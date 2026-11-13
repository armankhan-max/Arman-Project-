"""Render Agent and Quality Control Agent (with bounded automatic repair)."""
from collections import Counter
from typing import Literal

from pydantic import BaseModel

from fda.database import models as m
from fda.providers.base import ProviderError
from fda.rendering import renderer
from fda.services import assets, media
from fda.services.llm import LLM, external

from .common import scenes, transcript

MAX_REPAIR_ROUNDS = 2


def render_run(ctx):
    db, p = ctx.db, ctx.project
    kind = ctx.params.get("kind", "final")
    ps = db.query(m.ProjectSettings).filter_by(project_id=p.id).one()
    exp = ctx.params.get("export") or {}
    r = m.Render(project_id=p.id, project_version=p.current_version, kind=kind, status="running",
                 settings={"width": exp.get("width", ps.width), "height": exp.get("height", ps.height), "fps": exp.get("fps", ps.fps), "crf": exp.get("crf")})
    db.add(r)
    db.commit()
    try:
        a, probe, desc = renderer.render(db, p, kind, r.settings["width"], r.settings["height"], r.settings["fps"], r.settings.get("crf"),
                                         progress=lambda f, msg: ctx.progress(f, msg), cancelled=lambda: (db.refresh(ctx.run, ["cancel_requested"]) or ctx.run.cancel_requested))
    except Exception as e:
        r.status, r.error = "failed", str(e)[:2000]
        db.commit()
        raise
    r.status, r.asset_id, r.probe, r.verified = "succeeded", a.id, probe, True
    return {"summary": "Rendered and verified %s: %dx%d @ %sfps, %.1fs" % (kind, probe["video"]["width"], probe["video"]["height"], probe["video"]["fps"], probe["duration"]),
            "state": {"render_id": str(r.id)}, "render_id": str(r.id)}


class SceneReview(BaseModel):
    n: int
    matches: bool
    severity: Literal["info", "minor", "major"] = "minor"
    problem: str = ""
    better_prompt: str = ""
    better_query: str = ""


class CreativeReview(BaseModel):
    scenes: list[SceneReview]
    pacing: str = ""
    style_consistency: str = ""


def scene_at(scs, t):
    for sc in scs:
        if sc.start_s <= t < sc.end_s:
            return sc.idx
    return None


def issue(check, severity, description, scene=None, repair="", auto=False, kind="technical"):
    return {"check": check, "category": kind, "severity": severity, "scene_idx": scene, "description": description, "repair": repair, "auto_repairable": auto, "repaired": False}


def qc_run(ctx):
    db, p = ctx.db, ctx.project
    rid = ctx.params.get("render_id") or ctx.state.get("render_id")
    rend = db.get(m.Render, rid) if rid else None
    if rend is None or not rend.asset_id:
        raise ProviderError("No render to check", retryable=False)
    path = assets.local(db.get(m.Asset, rend.asset_id))
    scs = scenes(db, p.id)
    items = db.query(m.TimelineItem).filter_by(project_id=p.id, track="V1").order_by(m.TimelineItem.start_s).all()
    vo, tr = transcript(db, p.id)
    issues = []
    ctx.progress(0.1, "Technical checks")
    pr = media.probe(path)
    total = pr["duration"]
    if not pr.get("video") or not pr.get("audio"):
        issues.append(issue("streams", "critical", "Missing %s stream" % ("video" if not pr.get("video") else "audio"), repair="re-render", auto=True))
    det = media.detect(path, True, True, total)
    for a, b in det["black"]:
        if a < 0.6 or b > total - 1.6 or b - a < 0.5:
            continue  # intentional fade in/out and dip transitions
        sc = scene_at(scs, (a + b) / 2)
        issues.append(issue("black_frames", "major", "Black frames %.1f–%.1fs" % (a, b), sc, "regenerate scene visual", sc is not None))
    for a, b in det["freeze"]:
        if b - a < 4.5:
            continue
        sc = scene_at(scs, (a + b) / 2)
        it = next((x for x in items if x.scene_id and sc and x.start_s <= a + 0.1 < x.start_s + x.duration_s), None)
        if it and it.kind in ("motion_graphic", "placeholder"):
            continue
        issues.append(issue("frozen_frames", "minor", "Picture barely changes for %.1fs (%.1f–%.1fs)" % (b - a, a, b), sc, "regenerate scene visual", sc is not None and b - a > 6))
    for a, b in det["silence"]:
        if a < 1 or b > total - 2 or b - a < 2.5:
            continue
        issues.append(issue("silence", "minor", "Silence %.1f–%.1fs" % (a, b), scene_at(scs, a), "check narration pause (original narration is preserved)", False, "editing"))
    if det["peak_db"] is not None and det["peak_db"] > -0.3:
        issues.append(issue("clipping", "major", "Audio peaks at %.2f dBFS" % det["peak_db"], repair="remix with limiter", auto=True))
    if det["integrated_lufs"] is not None and not -17 <= det["integrated_lufs"] <= -11:
        issues.append(issue("loudness", "minor", "Integrated loudness %.1f LUFS (target -14)" % det["integrated_lufs"], repair="remix", auto=True))
    ctx.progress(0.5, "Editing checks")
    for i, it in enumerate(items):
        if (it.props or {}).get("missing"):
            sc = next((s.idx for s in scs if s.id == it.scene_id), None)
            issues.append(issue("missing_media", "major", "Scene %s has no visual (placeholder shown)" % sc, sc, "regenerate scene visual", True, "editing"))
        if it.asset_id:
            a = db.get(m.Asset, it.asset_id)
            if a is None or not assets.store().exists(a.storage_key):
                sc = next((s.idx for s in scs if s.id == it.scene_id), None)
                issues.append(issue("broken_path", "critical", "Asset file missing for scene %s" % sc, sc, "regenerate scene visual", True, "editing"))
        if i:
            prev = items[i - 1]
            gap = it.start_s - (prev.start_s + prev.duration_s)
            if abs(gap) > 0.05:
                issues.append(issue("timeline_gap", "major", "%s of %.2fs at %.1fs" % ("Gap" if gap > 0 else "Overlap", abs(gap), it.start_s), None, "rebuild timeline", True, "editing"))
    ps = db.query(m.ProjectSettings).filter_by(project_id=p.id).one()
    low = []
    for it in items:
        a = db.get(m.Asset, it.asset_id) if it.asset_id else None
        if a and a.kind in ("image", "video"):
            w, h = a.width or 0, a.height or 0
            if not w and a.kind == "image":
                try:
                    from PIL import Image
                    with Image.open(assets.local(a)) as im:
                        w, h = im.size
                except Exception:
                    pass
            if w and h and max(ps.width / w, ps.height / h) > 1.4:
                low.append("%s (%dx%d)" % (next((s.idx for s in scs if s.id == it.scene_id), "?"), w, h))
    if low:
        issues.append(issue("upscaled_sources", "info", "Upscaled to %dx%d from lower-resolution sources in scenes %s" % (ps.width, ps.height, ", ".join(low[:12])),
                            repair="replace with higher-resolution footage if quality matters", kind="technical"))
    order = [s.idx for s in sorted(scs, key=lambda s: s.start_s)]
    if order != sorted(order):
        issues.append(issue("scene_order", "major", "Scene order does not follow narration time", repair="rebuild timeline", auto=True, kind="editing"))
    use = Counter(it.asset_id for it in items if it.asset_id)
    for aid, n in use.items():
        if n > 1:
            dup = [s.idx for s in scs if s.asset_id == aid][1:]
            for d in dup:
                issues.append(issue("visual_repetition", "minor", "Scene %d reuses the same visual as an earlier scene" % d, d, "regenerate scene visual", True, "editing"))
    subs = db.query(m.Subtitle).filter_by(project_id=p.id).order_by(m.Subtitle.start_s).all()
    for a, b in zip(subs, subs[1:]):
        if b.start_s < a.start_s or a.end_s > b.end_s + 0.01:
            issues.append(issue("subtitle_sync", "major", "Subtitles out of order near %.1fs" % a.start_s, repair="rebuild subtitles from word timings", auto=True, kind="editing"))
            break
    if subs and subs[-1].end_s > total + 0.3:
        issues.append(issue("subtitle_sync", "major", "Subtitles run past the end of the video", repair="rebuild subtitles", auto=True, kind="editing"))
    if tr and tr.words and scs:
        if abs(scs[-1].end_s - (tr.words[-1]["e"] + 1.2)) > 2.5:
            issues.append(issue("narration_alignment", "major", "Last scene ends %.1fs away from the end of narration" % (scs[-1].end_s - tr.words[-1]["e"]), repair="re-storyboard", kind="editing"))
        if not tr.word_level:
            issues.append(issue("narration_alignment", "info", "Word timing is approximate (no speech recogniser was available)", repair="configure Whisper for exact timing", kind="editing"))
    non_cut = sum(1 for it in items if (it.props or {}).get("transition") not in (None, "cut"))
    if items and non_cut / len(items) > 0.6:
        issues.append(issue("transitions", "minor", "%d%% of cuts use effects; consider more straight cuts" % (100 * non_cut / len(items)), kind="editing"))
    subs_missing = [s.idx for s in scs if (s.plan or {}).get("substitution")]
    if subs_missing:
        issues.append(issue("substitutions", "info", "Scenes %s used a fallback visual type (see each scene)" % ", ".join(map(str, subs_missing[:20])), kind="creative"))
    ctx.progress(0.7, "Creative review")
    if scs and not ctx.params.get("skip_creative"):
        try:
            lines = "\n".join("%d. NARRATION: %s | PLAN: %s | ASSET: %s %s" % (s.idx, s.narration[:220], (s.plan or {}).get("description", "")[:160],
                                                                             s.visual_type, ((db.get(m.Asset, s.asset_id).meta or {}).get("title", "") if s.asset_id else "none")[:80]) for s in scs[:80])
            rv = LLM(db, p.id, "qc").structured("You are a strict documentary film editor reviewing whether each shot communicates its narration line. Flag only real mismatches.",
                                                "Review these scenes:\n" + external(lines, "storyboard"), CreativeReview, max_tokens=4000, temperature=0.2)
            for s in rv.scenes:
                if not s.matches and s.severity in ("minor", "major"):
                    issues.append(dict(issue("visual_relevance", s.severity, "Scene %d: %s" % (s.n, s.problem), s.n, "regenerate with revised prompt",
                                             s.severity == "major", "creative"), better_prompt=s.better_prompt, better_query=s.better_query))
            if rv.pacing:
                issues.append(issue("pacing", "info", rv.pacing, kind="creative"))
        except ProviderError as e:
            issues.append(issue("creative_review", "info", "Creative review skipped: %s" % str(e)[:200], kind="creative"))
    passed = not any(i["severity"] in ("critical", "major") for i in issues)
    rep = m.QualityReport(project_id=p.id, render_id=rend.id, passed=passed, issues=issues,
                          stats={"duration": total, "peak_db": det["peak_db"], "lufs": det["integrated_lufs"], "black": det["black"], "freeze": det["freeze"], "silence": det["silence"]})
    db.add(rep)
    db.flush()
    rnd = int(ctx.params.get("round", 0))
    repairs = [i for i in issues if i["auto_repairable"]]
    spawn = []
    if repairs and rnd < MAX_REPAIR_ROUNDS:
        spawn = repair_tasks(db, p, ctx.run, repairs, rnd + 1)
        for i in repairs:
            i["repaired"] = "scheduled"
        rep.issues = issues
    elif repairs:
        ctx.log("Auto-repair limit reached; %d issues left for the owner" % len(repairs), "warn")
    for s in scs:
        bad = [i for i in issues if i.get("scene_idx") == s.idx and i["severity"] in ("major", "critical")]
        s.quality_status = "failed" if bad else "passed"
    sev = Counter(i["severity"] for i in issues)
    return {"summary": "QC %s: %s%s" % ("passed" if passed else "found problems", ", ".join("%d %s" % (n, k) for k, n in sev.items()) or "no issues",
                                        ("; repair round %d scheduled (%d fixes)" % (rnd + 1, len(repairs))) if spawn else ""),
            "spawn": spawn, "state": {"qc_report_id": str(rep.id)}}


def repair_tasks(db, p, run, repairs, rnd):
    pre = "repair%d:" % rnd
    sc_by_idx = {s.idx: s for s in scenes(db, p.id)}
    redo, need_audio = set(), False
    for i in repairs:
        if i.get("scene_idx") and i["repair"].startswith("regenerate"):
            redo.add(i["scene_idx"])
            sc = sc_by_idx.get(i["scene_idx"])
            if sc and (i.get("better_prompt") or i.get("better_query")):
                pl = dict(sc.plan or {})
                if i.get("better_prompt"):
                    pl["prompt"] = i["better_prompt"]
                if i.get("better_query"):
                    pl["search_query"] = i["better_query"]
                sc.plan = pl
        if i["check"] in ("clipping", "loudness"):
            need_audio = True
    tasks = []
    for idx in sorted(redo):
        sc = sc_by_idx.get(idx)
        if sc:
            tasks.append({"key": pre + "visual:%04d" % idx, "agent": "visual", "queue": "visual", "params": {"scene_id": str(sc.id), "redo": True, "reason": "QC repair"}})
    if need_audio:
        tasks.append({"key": pre + "audio", "agent": "audio", "queue": "audio"})
    deps = [t["key"] for t in tasks]
    tasks.append({"key": pre + "edit", "agent": "editor", "depends_on": deps, "params": {"reason": "QC repair round %d" % rnd}})
    tasks.append({"key": pre + "render", "agent": "render", "queue": "render", "depends_on": [pre + "edit"], "params": {"kind": "final"}, "timeout_s": 14400})
    tasks.append({"key": pre + "qc", "agent": "qc", "queue": "qc", "depends_on": [pre + "render"], "params": {"round": rnd, "skip_creative": True}})
    return tasks
