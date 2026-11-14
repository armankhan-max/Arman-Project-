"""Film Director / Storyboard Agent: turns timed narration into a shot-by-shot storyboard."""
import random
import shutil

from fda import catalog
from fda.config import get_settings
from fda.database import models as m
from fda.database.session import SessionLocal
from fda.providers import registry
from fda.providers.base import ProviderError
from fda.schemas.agents import Continuity, ScenePlan, StoryboardBatch
from fda.memory.store import as_context as mem_ctx, recall
from fda.services.llm import LLM, external

from . import blender as blender_agent
from .common import keywords, style, transcript

MG_DOC = """Motion-graphic types (for visual_type motion_graphic, put them in motion_graphic) and their data; use ONLY facts stated in the narration:
title {text, sub} · stat {value:number, prefix, suffix, label} · timeline {events:[{t, label}]} · bar_chart {title, unit, items:[{label, value}]}
compare {a:{label,value}, b:{label,value}, unit} · line_chart {title, unit, points:[{x, y}]} · ring {value:0-100, label} · world_map {place, lat, lon, label}
route_map {label, points:[{name, lat, lon}]} · quote {text, by} · list {title, items:[...]} · clock {time, date, place} · keywords {words:[...]}
icon_grid {items:[...]} · document {title, lines:[...], stamp} · diagram {center, parts:[...]} · counter {value, label}"""


def segment(words, pace, end_time):
    """Scene boundaries from real word timings: break at sentence ends and pauses, split long sentences, merge short ones."""
    if not words:
        return []
    lo, hi = max(1.8, pace * 0.5), max(pace * 1.6, 5.5)
    scenes, cur = [], [0, 0]

    def dur(a, b):
        return words[b]["e"] - words[a]["s"]
    for i in range(len(words)):
        cur[1] = i
        w = words[i]["w"]
        gap = (words[i + 1]["s"] - words[i]["e"]) if i + 1 < len(words) else 9
        d = dur(cur[0], i)
        sentence_end = w[-1:] in ".!?।" or gap > 0.7
        clause_end = w[-1:] in ",;:" or gap > 0.35
        if (sentence_end and d >= lo) or (clause_end and d >= pace) or d >= hi:
            scenes.append(tuple(cur))
            cur = [i + 1, i + 1]
    if cur[0] < len(words):
        if scenes and dur(cur[0], len(words) - 1) < lo:
            scenes[-1] = (scenes[-1][0], len(words) - 1)
        else:
            scenes.append((cur[0], len(words) - 1))
    out = []
    for k, (a, b) in enumerate(scenes):
        start = 0.0 if k == 0 else round(words[a]["s"] - 0.08, 3)
        out.append({"a": a, "b": b, "start": start})
    for k in range(len(out)):
        out[k]["end"] = out[k + 1]["start"] if k + 1 < len(out) else round(max(end_time, words[-1]["e"]) + 1.2, 3)
    return out


def allowed_types(db, project, st):
    src = st.get("sources") or {}
    ok = []
    if src.get("stock_video", True) and (registry.for_cap(db, "stock_video")):
        ok.append("stock_video")
    if src.get("stock_image", True) and registry.for_cap(db, "stock_image"):
        ok.append("stock_image")
    if src.get("archive", True) and registry.for_cap(db, "archive_image"):
        ok.append("archive")
    if src.get("ai_image", True) and registry.for_cap(db, "text_to_image"):
        ok.append("ai_image")
    if src.get("ai_video") and (registry.for_cap(db, "image_to_video") or registry.for_cap(db, "text_to_video")):
        ok.append("ai_video")
    if src.get("blender", True) and shutil.which(get_settings().blender_bin):
        ok.append("blender")
    if project.mode == "avatar" or src.get("avatar"):
        ok.append("avatar")
    ok.append("motion_graphic")
    return ok


def heuristic(n, text, allowed, rnd, prefer):
    kw = keywords(text)
    vt = next((t for t in prefer if t in allowed and t not in ("motion_graphic", "avatar", "blender")), "ai_image")
    if any(ch.isdigit() for ch in text) and "motion_graphic" in allowed and rnd.random() < 0.5:
        return ScenePlan(n=n, purpose="Show the key number", visual_type="motion_graphic", description="Animated keyword card", subject=" ".join(kw[:2]),
                         environment="graphic", shot="medium", angle="eye level", movement="static", lens="", lighting="", color="", prompt=text,
                         search_query=" ".join(kw[:3]), motion_graphic={"type": "keywords", "words": [w.upper() for w in kw[:3]] or ["?"]})
    return ScenePlan(n=n, purpose="Illustrate the narration", visual_type=vt, description=text[:200], subject=" ".join(kw[:2]), environment="",
                     shot=rnd.choice(["wide", "medium", "close_up"]), angle="eye level", movement=rnd.choice(["push_in", "pull_out", "pan_left", "pan_right", "tracking"]),
                     lens="35mm", lighting="natural", color="cinematic", prompt="Cinematic documentary photograph of %s. %s" % (", ".join(kw[:3]) or text[:80], text[:200]),
                     search_query=" ".join(kw[:3]) or text[:40], transition=rnd.choice(["cut", "fade", "cut"]))


def plan_batch(project_id, title, mode, lang, allowed, prefer, continuity, batch, prev_types, prefs=""):
    db = SessionLocal()
    try:
        llm = LLM(db, project_id, "storyboard")
        lines = "\n".join("%d. [%.1fs] %s" % (s["n"], s["end"] - s["start"], s["text"]) for s in batch)
        sys = ("You are a film director planning shots for a %s. Every shot must communicate what its line says; never pick a visual only because it is pretty. "
               "Vary shot sizes and camera moves; use movement only when it serves the scene; avoid repeating the previous shot type. "
               "Keep recurring characters, places and objects consistent with the continuity bible.") % catalog.MODES.get(mode, {}).get("name", mode)
        prompt = """VIDEO: %s
ALLOWED visual_type values: %s (preference for this mode, best first: %s)
Use ai_video only for scenes that truly need motion that no stock footage could show. Use archive only for real historical people, places and events.
Use motion_graphic when a number, date, place, comparison, list or quote is the point, but for no more than about one scene in four. Use blender for scientific/3D explanations: %s
%s
OWNER'S SAVED PREFERENCES (follow them unless the narration needs otherwise):
%s
CONTINUITY BIBLE:
%s
Previous scene types: %s
NARRATION LINES (scene number, duration, text):
%s
Return one ScenePlan per line, same numbers.""" % (title, ", ".join(allowed), ", ".join(p for p in prefer if p in allowed), blender_agent.template_doc() if "blender" in allowed else "(unavailable)",
                                                  MG_DOC, prefs or "(none)", external(continuity, "continuity"), ", ".join(prev_types[-4:]) or "none", external(lines, "narration"))
        out = llm.structured(sys, prompt, StoryboardBatch, max_tokens=min(9000, 700 + 520 * len(batch)), temperature=0.6)
        db.commit()
        return {s.n: s for s in out.scenes}
    finally:
        db.close()


def run(ctx):
    db, p = ctx.db, ctx.project
    ps, st = style(db, p)
    vo, tr = transcript(db, p.id)
    if not tr or not tr.words:
        raise ProviderError("No timed narration to storyboard", retryable=False)
    old = db.query(m.Storyboard).filter_by(project_id=p.id).order_by(m.Storyboard.version.desc()).first()
    if old and not ctx.params.get("redo") and db.query(m.Scene).filter_by(storyboard_id=old.id).count():
        n = db.query(m.Scene).filter_by(storyboard_id=old.id).count()
        return {"skipped": True, "summary": "Storyboard exists (%d scenes)" % n, "spawn": visual_tasks(db, old)}
    ws = tr.words
    segs = segment(ws, float(st.get("pace", 4.5)), vo.duration_s or ws[-1]["e"])
    for k, s in enumerate(segs):
        s["n"] = k + 1
        s["text"] = " ".join(w["w"] for w in ws[s["a"]:s["b"] + 1])
    allowed = allowed_types(db, p, st)
    prefer = catalog.MODES.get(p.mode, catalog.MODES["documentary"])["prefer"]
    llm = LLM(db, p.id, "storyboard")
    ctx.progress(0.05, "Building the continuity bible")
    try:
        cont = llm.structured("You keep visual continuity for a film.", "Narration:\n%s\n\nList recurring characters (name, look, clothing), places, objects, one palette and one look." %
                              external(tr.text[:9000], "narration"), Continuity, max_tokens=1500).model_dump()
    except ProviderError as e:
        cont = {}
        ctx.log("Continuity bible unavailable: %s" % e, "warn")
    rnd0 = random.Random(str(p.id) + "a")
    prefs = mem_ctx(recall(db, p.user_id, "camera movement transitions editing pace visual style", "preference", k=8))
    plans, prev = {}, []
    B = 10
    batches = [segs[i:i + B] for i in range(0, len(segs), B)]
    for bi, b in enumerate(batches):
        try:
            plans.update(plan_batch(p.id, p.title, p.mode, p.language, allowed, prefer, str(cont)[:2500], b, prev, prefs))
        except ProviderError as e:
            ctx.log("Storyboard batch %d used heuristic planning: %s" % (bi + 1, str(e)[:200]), "warn")
        prev += [plans[s["n"]].visual_type for s in b if s["n"] in plans]
        ctx.progress(0.1 + 0.8 * (bi + 1) / len(batches), "Planned %d/%d scenes" % (min(len(segs), (bi + 1) * B), len(segs)))
    rnd = random.Random(str(p.id))
    if p.mode == "avatar":
        # talking-head channel: host on camera for the hook and regularly after, AI phone-style B-roll in between
        run_b = 0
        for s_ in segs:
            n = s_["n"]
            pl = plans.get(n) or heuristic(n, s_["text"], allowed, rnd0, prefer)
            plans[n] = pl
            want = n <= 2 or n >= len(segs) or run_b >= 2 + (n % 2)
            if want:
                pl.visual_type, pl.motion_graphic, run_b = "avatar", None, 0
            else:
                run_b += 1
                if pl.visual_type not in ("motion_graphic",) or not any(ch.isdigit() for ch in s_["text"]):
                    pl.visual_type, pl.motion_graphic = "ai_image", None
            pl.transition = "cut"
    # keep graphics from crowding out pictures: at most ~30% motion graphics unless the mode is graphics-led
    if p.mode not in ("motion_graphics", "educational"):
        mgs = [n for n, pl in sorted(plans.items()) if pl.visual_type == "motion_graphic"]
        cap = max(1, int(len(segs) * 0.3))
        if len(mgs) > cap:
            alt = next((t for t in prefer if t in allowed and t not in ("motion_graphic", "avatar", "blender")), "ai_image")
            keep = set(sorted(mgs, key=lambda n: -sum(ch.isdigit() for ch in segs[n - 1]["text"]))[:cap])
            for n in mgs:
                if n not in keep:
                    pl = plans[n]
                    pl.visual_type, pl.motion_graphic = alt, None
                    pl.search_query = pl.search_query or " ".join(keywords(segs[n - 1]["text"], 3))
            ctx.log("Converted %d of %d motion-graphic scenes to %s to keep the edit picture-led" % (len(mgs) - cap, len(mgs), alt))
    sb = m.Storyboard(project_id=p.id, version=(old.version + 1) if old else 1, continuity=cont)
    db.add(sb)
    db.flush()
    heur = 0
    for s in segs:
        pl = plans.get(s["n"])
        if pl is None:
            pl = heuristic(s["n"], s["text"], allowed, rnd, prefer)
            heur += 1
        if pl.visual_type not in allowed:
            pl.visual_type = next((t for t in prefer if t in allowed and t not in ("avatar",)), "ai_image")
        if pl.visual_type == "motion_graphic" and not (pl.motion_graphic or {}).get("type") in catalog.MG_TYPES:
            pl.motion_graphic = {"type": "keywords", "words": [w.upper() for w in keywords(s["text"], 3)] or ["…"]}
        if pl.visual_type == "blender" and pl.blender_template not in blender_agent.TEMPLATES:
            pl.visual_type = next((t for t in prefer if t in allowed and t not in ("blender", "avatar", "motion_graphic")), "ai_image")
        plan = pl.model_dump()
        plan["planned_by"] = "heuristic" if s["n"] not in plans else "llm"
        db.add(m.Scene(storyboard_id=sb.id, project_id=p.id, idx=s["n"], start_s=s["start"], end_s=s["end"], narration=s["text"], word_start=s["a"], word_end=s["b"],
                       purpose=pl.purpose, visual_type=pl.visual_type, plan=plan, asset_status="pending"))
    db.flush()
    if heur:
        ctx.log("%d of %d scenes were planned heuristically because the reasoning model failed for them" % (heur, len(segs)), "warn")
    return {"summary": "Storyboard v%d: %d scenes (%s)" % (sb.version, len(segs), ", ".join("%s %d" % (t, sum(1 for x in plans.values() if x.visual_type == t)) for t in allowed if any(x.visual_type == t for x in plans.values()))),
            "spawn": visual_tasks(db, sb), "state": {"storyboard_id": str(sb.id)}}


def visual_tasks(db, sb):
    out = []
    for sc in db.query(m.Scene).filter_by(storyboard_id=sb.id).order_by(m.Scene.idx).all():
        out.append({"key": "visual:%04d" % sc.idx, "agent": "visual", "queue": "blender" if sc.visual_type == "blender" else "visual",
                    "depends_on": ["storyboard"], "params": {"scene_id": str(sc.id)}, "timeout_s": 2400})
    return out
