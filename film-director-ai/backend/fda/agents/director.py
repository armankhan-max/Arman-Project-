"""Film Director Agent: understands requests, decides the workflow, delegates to specialists, and handles chat edits."""
import re

from fda import catalog
from fda.database import models as m
from fda.knowledge.retrieval import as_context as kctx, search
from fda.memory.store import as_context as mctx, recall, remember
from fda.orchestration import workflow
from fda.providers.base import ProviderError
from fda.schemas.agents import DirectorIntent, EditOp, EditPlan, InputAnalysis
from fda.services.llm import LLM, external

from .common import latest_script, scenes, style, uploads


# ------------------------------------------------------------------ input analysis (deterministic, no guessing)
def analyze_inputs(db, project):
    ps, st = style(db, project)
    ups = uploads(db, project.id)
    has_vo = any(a.kind == "audio" for a in ups)
    sc, sv = latest_script(db, project.id)
    has_script = bool(sv and sc.origin == "user")
    refs = [a for a in ups if a.kind in ("image", "video")]
    brief = (project.brief or "").strip()
    notes = []
    if has_vo:
        notes.append("Uploaded narration will be %s." % ("preserved exactly" if project.preserve_narration else "used"))
    if has_vo and has_script:
        notes.append("Script supplied too: used for alignment and research, not re-voiced.")
    if refs:
        notes.append("%d reference/footage files will be offered to the storyboard." % len(refs))
    needs_research = st.get("research", "auto") != "off" and (not has_script or st.get("research") == "on") and project.mode not in ("short",)
    return InputAnalysis(has_title=bool(project.title), has_brief=bool(brief and brief != project.title), has_script=has_script, has_voiceover=has_vo,
                         has_reference_media=bool(refs), needs_research=bool(needs_research), needs_script=not has_script and not has_vo,
                         needs_transcription=has_vo, preserve_narration=project.preserve_narration, mode=project.mode, language=project.language,
                         target_minutes=ps.target_minutes, notes=notes)


def analyze_run(ctx):
    a = analyze_inputs(ctx.db, ctx.project)
    ctx.project.status = "producing"
    steps = ["research" if a.needs_research else None, "script" if a.needs_script else None, "transcription" if a.needs_transcription else "narration synthesis",
             "storyboard", "visuals", "sound", "edit", "render", "QC"]
    return {"summary": "Plan: " + " → ".join(s for s in steps if s) + (". " + " ".join(a.notes) if a.notes else ""), "state": {"analysis": a.model_dump()}}


def production_tasks():
    return [
        {"key": "analyze", "agent": "analyze"},
        {"key": "research", "agent": "research", "queue": "research", "depends_on": ["analyze"]},
        {"key": "script", "agent": "script", "queue": "research", "depends_on": ["research"]},
        {"key": "voiceover", "agent": "voiceover", "queue": "transcription", "depends_on": ["script"], "timeout_s": 5400},
        {"key": "storyboard", "agent": "storyboard", "depends_on": ["voiceover"]},
        {"key": "audio", "agent": "audio", "queue": "audio", "depends_on": ["storyboard"]},
        {"key": "edit", "agent": "editor", "depends_on": ["storyboard", "visual:*", "audio"]},
        {"key": "render", "agent": "render", "queue": "render", "depends_on": ["edit"], "params": {"kind": "final"}, "timeout_s": 14400},
        {"key": "qc", "agent": "qc", "queue": "qc", "depends_on": ["render"]},
        {"key": "finalize", "agent": "finalize", "depends_on": ["*qc"]},
        {"key": "pack", "agent": "pack", "depends_on": ["finalize"], "max_attempts": 1},
    ]


def start_production(db, project, user_id):
    active = db.query(m.WorkflowRun).filter(m.WorkflowRun.project_id == project.id, m.WorkflowRun.status.in_(["pending", "running"])).first()
    if active:
        return active
    project.status = "producing"
    run = workflow.create_run(db, project.id, "produce", production_tasks(), plan={"requested_by": "owner"})
    db.commit()
    workflow.dispatch(run.id)
    return run


def finalize_run(ctx):
    db, p = ctx.db, ctx.project
    rep = db.get(m.QualityReport, ctx.state.get("qc_report_id")) if ctx.state.get("qc_report_id") else None
    p.status = "ready" if (rep is None or rep.passed) else "needs_attention"
    used = sorted({s.provider for s in scenes(db, p.id) if s.provider})
    try:
        remember(db, p.user_id, "production", "providers:%s" % p.mode, "Visual providers used for a %s video: %s" % (p.mode, ", ".join(used)), {"providers": used},
                 status="inferred", source="director", project_id=p.id)
        if rep and rep.issues:
            remember(db, p.user_id, "production", "qc:%s" % p.id, "QC on '%s': %s" % (p.title, "; ".join(i["description"] for i in rep.issues[:6])), {}, "inferred", "qc", p.id)
    except Exception:
        pass
    return {"summary": "Project %s (version %d)" % ("ready" if p.status == "ready" else "finished with open QC issues", p.current_version)}


# ------------------------------------------------------------------ chat editing
MOVES_SEQ = ["push_in", "pull_out", "pan_left", "pan_right", "orbit", "tracking", "handheld", "tilt_up", "drone"]


def heuristic_edit(text, n_scenes):
    t = text.lower()
    nums = [int(x) for x in re.findall(r"scene\s*(\d+)", t)]
    rng = re.findall(r"scene\s*(\d+)\s*(?:-|to|aur|and|se)\s*(\d+)", t)
    for a, b in rng:
        nums += list(range(int(a), int(b) + 1))
    nums = sorted({n for n in nums if 1 <= n <= n_scenes})
    ops = []
    if re.search(r"camera|movement|angle|shot", t) and nums:
        mv = next((mv for mv in catalog.MOVEMENTS if mv.replace("_", " ") in t or mv in t), None)
        ops.append(EditOp(op="change_camera", scenes=nums, value=mv, reason="camera"))
    if re.search(r"realistic|real|asli", t) and nums:
        ops.append(EditOp(op="change_visual_type", scenes=nums, value="realistic"))
    if re.search(r"\b3d\b|blender|animation", t):
        ops.append(EditOp(op="change_visual_type", scenes=nums, value="blender"))
    if re.search(r"regenerat|redo|dobara|replace|badal", t) and nums and not ops:
        ops.append(EditOp(op="regenerate_scene", scenes=nums))
    if re.search(r"music|bgm", t):
        lower = re.search(r"lower|kam|down|soft|thoda", t) and not re.search(r"louder|zyada|up|badha", t)
        ops.append(EditOp(op="music_volume", number=0.6 if lower else 1.4))
    if re.search(r"sfx|sound effect", t):
        ops.append(EditOp(op="sfx_volume", number=0.6 if re.search(r"lower|kam|less", t) else 1.4))
    if re.search(r"voice|voiceover|narration", t) and re.search(r"clear|saaf|clean", t):
        ops.append(EditOp(op="voice_enhance"))
    if re.search(r"subtitle|caption", t) and re.search(r"sync", t):
        ops.append(EditOp(op="resync_subtitles"))
    if re.search(r"transition", t):
        ops.append(EditOp(op="change_transition", scenes=nums, value="fade" if re.search(r"smooth|soft", t) else None))
    if re.search(r"opening|intro|first \d+ sec|shuru", t) and re.search(r"engag|interesting|better|strong|dhamak", t):
        ops.append(EditOp(op="more_engaging_opening"))
    if re.search(r"render|export", t) and not ops:
        ops.append(EditOp(op="render"))
    return EditPlan(understood="(rule-based) " + text[:200], ops=ops or [EditOp(op="note", reason="Could not map the request to an edit")])


def plan_edit(db, project, text):
    scs = scenes(db, project.id)
    summary = "\n".join("%d. [%.1f–%.1fs] %s | %s | move %s | %s" % (s.idx, s.start_s, s.end_s, s.visual_type, (s.narration or "")[:90], (s.plan or {}).get("movement"),
                                                                     (s.plan or {}).get("transition")) for s in scs[:150])
    try:
        return LLM(db, project.id, "edit").structured(
            "You are the film director translating the owner's editing request (English, Hindi or Hinglish) into the smallest set of edit operations. "
            "Only touch scenes the owner refers to. For change_camera put the new movement in value (one of %s). For change_visual_type value is one of "
            "stock_video, ai_video, ai_image, archive, blender, motion_graphic, realistic. Volumes use number as a multiplier (0.6 = lower)." % ", ".join(catalog.MOVEMENTS),
            "SCENES:\n%s\n\nREQUEST: %s" % (external(summary, "storyboard"), external(text, "owner request")), EditPlan, max_tokens=1500, temperature=0.2)
    except ProviderError:
        return heuristic_edit(text, len(scs))


def apply_edit_run(ctx):
    """Applies an EditPlan to project data and spawns only the work that is needed."""
    db, p = ctx.db, ctx.project
    plan = EditPlan.model_validate(ctx.params["plan"])
    ps, st = style(db, p)
    scs = {s.idx: s for s in scenes(db, p.id)}
    from .storyboard import allowed_types
    allowed = allowed_types(db, p, st)
    redo, audio, done = set(), False, []
    newst = dict(ps.style or {})
    for op in plan.ops:
        targets = [scs[i] for i in op.scenes if i in scs]
        if op.op == "regenerate_scene":
            redo |= {s.idx for s in targets}
        elif op.op == "change_camera":
            for s in targets:
                cur = (s.plan or {}).get("movement")
                mv = op.value if op.value in catalog.MOVEMENTS else MOVES_SEQ[(MOVES_SEQ.index(cur) + 1) % len(MOVES_SEQ) if cur in MOVES_SEQ else 0]
                s.plan = dict(s.plan or {}, movement=mv)
                if s.visual_type in ("blender", "ai_video"):
                    redo.add(s.idx)
                _override(db, s, motion=catalog.MOVE_TO_ENGINE.get(mv, "push_in"))
                done.append("scene %d camera → %s" % (s.idx, mv))
        elif op.op == "change_visual_type":
            want = op.value or "stock_video"
            if want == "realistic":
                want = "ai_video" if "ai_video" in allowed else "stock_video" if "stock_video" in allowed else "ai_image"
            if want not in allowed:
                done.append("%s is not available (configure its provider); kept current visuals" % want)
                continue
            for s in targets or [x for x in scs.values() if x.visual_type in ("motion_graphic", "ai_image") and want == "blender"][:6]:
                s.visual_type = want
                if want == "blender" and not (s.plan or {}).get("blender_template"):
                    s.plan = dict(s.plan or {}, blender_template="planet")
                redo.add(s.idx)
                done.append("scene %d → %s" % (s.idx, want))
        elif op.op == "change_prompt":
            for s in targets:
                s.plan = dict(s.plan or {}, prompt=op.value or (s.plan or {}).get("prompt"))
                redo.add(s.idx)
        elif op.op == "change_transition":
            for s in targets or list(scs.values()):
                s.plan = dict(s.plan or {}, transition=op.value or "fade")
                _override(db, s, transition=op.value or "fade", tdur=0.7)
            audio = True
            done.append("transitions smoothed")
        elif op.op == "music_volume":
            newst["music_volume"] = round(max(0.0, min(1.5, float(st.get("music_volume", 0.5)) * float(op.number or 0.7))), 3)
            audio = True
            done.append("music volume → %.2f" % newst["music_volume"])
        elif op.op == "sfx_volume":
            newst["sfx_volume"] = round(max(0.0, min(1.5, float(st.get("sfx_volume", 0.7)) * float(op.number or 0.7))), 3)
            audio = True
        elif op.op == "voice_enhance":
            newst["voice_enhance"] = True
            audio = True
            done.append("voice clean-up on")
        elif op.op == "resync_subtitles":
            done.append("subtitles rebuilt from word timings")
        elif op.op == "more_engaging_opening":
            for s in [x for x in scs.values() if x.start_s < 10]:
                s.plan = dict(s.plan or {}, movement="dolly_zoom" if s.idx == 1 else "handheld", prompt=((s.plan or {}).get("prompt") or s.narration) + ". Dramatic, high-contrast, striking composition.")
                _override(db, s, motion="ramp_push" if s.idx == 1 else "handheld", transition="flash" if s.idx > 1 else "cut")
                redo.add(s.idx)
            audio = True
            done.append("opening re-shot with stronger moves and punchier cuts")
        elif op.op == "change_caption_style" and op.value in catalog.CAPTION_STYLES:
            newst["captions"] = op.value
        elif op.op == "change_look" and op.value in catalog.LOOKS:
            newst["look"] = op.value
    ps.style = newst
    spawn = [{"key": "edit_visual:%04d" % i, "agent": "visual", "queue": "visual", "depends_on": ["apply_edit"],
              "params": {"scene_id": str(scs[i].id), "redo": True, "reason": "chat edit"}} for i in sorted(redo)]
    if audio:
        spawn.append({"key": "audio", "agent": "audio", "queue": "audio", "depends_on": ["apply_edit"]})
    return {"summary": "Edit applied: %s; regenerating %d scene(s)%s" % ("; ".join(done) or plan.understood[:200], len(redo), ", remixing audio" if audio else ""), "spawn": spawn}


def _override(db, scene, **props):
    it = db.query(m.TimelineItem).filter_by(scene_id=scene.id, track="V1").first()
    if it:
        it.props = dict(it.props or {}, user_edited=True, **props)


def start_edit(db, project, text, plan=None):
    plan = plan or plan_edit(db, project, text)
    only_render = all(o.op in ("render", "note") for o in plan.ops)
    if all(o.op == "note" for o in plan.ops):
        return None, plan
    tasks = [] if only_render else [{"key": "apply_edit", "agent": "apply_edit", "params": {"plan": plan.model_dump(), "request": text}},
                                    {"key": "edit", "agent": "editor", "depends_on": ["apply_edit", "edit_visual:*", "audio*"],
                                     "params": {"reason": "Chat edit: " + text[:200], "resync_subtitles": any(o.op == "resync_subtitles" for o in plan.ops)}}]
    tasks += [{"key": "render", "agent": "render", "queue": "render", "depends_on": [] if only_render else ["edit"], "params": {"kind": "final"}, "timeout_s": 14400},
              {"key": "qc", "agent": "qc", "queue": "qc", "depends_on": ["render"], "params": {"skip_creative": True}},
              {"key": "finalize", "agent": "finalize", "depends_on": ["*qc"]}]
    project.status = "producing"
    run = workflow.create_run(db, project.id, "edit", tasks, plan={"request": text, "edit_plan": plan.model_dump()})
    db.commit()
    workflow.dispatch(run.id)
    return run, plan


# ------------------------------------------------------------------ conversation
def classify(db, user_id, text, project):
    mems = mctx(recall(db, user_id, text, k=6))
    ctx = ""
    if project:
        ctx = "Current project: '%s' (%s, status %s, %d scenes)." % (project.title, project.mode, project.status, len(scenes(db, project.id)))
    try:
        return LLM(db, project.id if project else None, "director").structured(
            "You are Film Director AI, the owner's autonomous film director. Classify the owner's message (English/Hindi/Hinglish). "
            "produce = make a new video; edit = change an existing project; research = topic research; youtube_research = YouTube niche/competitor research; "
            "question = answer; remember = owner states a lasting preference (put it in remember as {category, key, content}); render = re-export; status = progress. "
            "Modes: %s." % ", ".join(catalog.MODES),
            "%s\nKnown preferences:\n%s\n\nMESSAGE:\n%s" % (ctx, mems or "(none)", external(text, "owner message")), DirectorIntent, max_tokens=900, temperature=0.2)
    except ProviderError:
        t = text.lower()
        intent = "edit" if project and re.search(r"scene\s*\d+|music|subtitle|transition|voice|camera|regenerat|opening", t) else (
            "produce" if re.search(r"create|make|banao|bana|video", t) else "question")
        title = re.search(r"titled?\s+[\"“]?(.+?)[\"”]?(?:\.|$)", text, re.I)
        return DirectorIntent(intent=intent, title=title.group(1)[:200] if title else "", brief=text)


def answer(db, user_id, text, project):
    know = kctx(search(db, text, 6, project.id if project else None))
    mems = mctx(recall(db, user_id, text, k=6))
    return LLM(db, project.id if project else None, "director").complete(
        "You are Film Director AI. Answer briefly and concretely. Cite bracketed source numbers when you use retrieved knowledge and say clearly when something is not verified.",
        "Owner preferences:\n%s\n\nRetrieved knowledge:\n%s\n\nQuestion: %s" % (mems or "(none)", external(know or "(nothing relevant)", "knowledge base"), external(text, "owner message")),
        max_tokens=900, temperature=0.4)
