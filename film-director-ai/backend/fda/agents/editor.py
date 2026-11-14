"""Editor Agent: builds the editable multi-track timeline and subtitles from the storyboard and the narration timing.
Rebuilding keeps owner edits on clips (camera, filter, transition overrides) and owner-added overlays."""
import random

from fda import catalog
from fda.database import models as m

from .common import scenes, style, transcript

USER_KEYS = ("motion", "filter", "transition", "tdur", "speed", "focus", "scale", "x", "y", "opacity", "crop", "user_edited")


def caption_groups(words, max_chars=64):
    caps, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        gap = (words[i + 1]["s"] - w["e"]) if i + 1 < len(words) else 9
        chars = sum(len(x["w"]) + 1 for x in cur)
        if chars >= max_chars or (len(cur) >= 4 and w["w"][-1:] in ".,!?;:।") or gap > 0.6 or len(cur) >= 12:
            caps.append(cur)
            cur = []
    if cur:
        caps.append(cur)
    return caps


def snapshot(db, project_id):
    def rows(model, order):
        return [{c.name: (str(v) if hasattr(v, "hex") else v) for c in model.__table__.columns for v in [getattr(r, c.name)] if c.name not in ("created_at", "updated_at")}
                for r in db.query(model).filter_by(project_id=project_id).order_by(order).all()]
    return {"scenes": rows(m.Scene, m.Scene.idx), "timeline": rows(m.TimelineItem, m.TimelineItem.start_s), "audio": rows(m.AudioTrack, m.AudioTrack.role),
            "subtitles": rows(m.Subtitle, m.Subtitle.idx)}


def save_version(db, project, reason):
    project.current_version = (project.current_version or 0) + 1
    db.add(m.ProjectVersion(project_id=project.id, version=project.current_version, reason=reason, snapshot=snapshot(db, project.id)))
    db.flush()
    return project.current_version


def build(db, project, resync_subtitles=True):
    ps, st = style(db, project)
    scs = scenes(db, project.id)
    vo, tr = transcript(db, project.id)
    rnd = random.Random(project.id.int)
    old = {str(it.scene_id): it for it in db.query(m.TimelineItem).filter_by(project_id=project.id, track="V1").all() if it.scene_id}
    keep_overlays = [it for it in db.query(m.TimelineItem).filter_by(project_id=project.id).filter(m.TimelineItem.track != "V1").all() if (it.props or {}).get("user")]
    dq = db.query(m.TimelineItem).filter_by(project_id=project.id)
    if keep_overlays:
        dq = dq.filter(m.TimelineItem.id.notin_([o.id for o in keep_overlays]))
    dq.delete(synchronize_session=False)
    missing, last_motion = 0, None
    for i, sc in enumerate(scs):
        pl = sc.plan or {}
        a = db.get(m.Asset, sc.asset_id) if sc.asset_id else None
        if sc.visual_type == "motion_graphic":
            kind = "motion_graphic"
        elif a is None:
            kind = "placeholder"
            missing += 1
        elif sc.visual_type == "avatar" and not (pl.get("substitution")) and a.kind == "video":
            kind = "video"  # lip-synced talking-head video: play the part that matches this narration
        elif sc.visual_type == "avatar" and not (pl.get("substitution")):
            kind = "avatar"
        elif sc.visual_type == "blender" and not pl.get("substitution"):
            kind = "blender"
        else:
            kind = "video" if a.kind == "video" else "image"
        mv = catalog.MOVE_TO_ENGINE.get(pl.get("movement") or "push_in", "push_in")
        if mv == last_motion and kind == "image":
            mv = rnd.choice([x for x in ("push_in", "pull_out", "pan_left", "pan_right", "drift") if x != mv])
        last_motion = mv
        props = {"motion": mv, "focus": [round(rnd.uniform(0.42, 0.58), 2), round(rnd.uniform(0.38, 0.5), 2)], "transition": "cut" if i == 0 else pl.get("transition", "cut"),
                 "tdur": 0.5, "filter": "none", "speed": 1.0, "v": rnd.randint(0, 9999), "label": (pl.get("subject") or "")[:40]}
        if kind in ("motion_graphic", "placeholder"):
            props["mg"] = pl.get("motion_graphic") if kind == "motion_graphic" else {"type": "keywords", "words": ["MISSING VISUAL"]}
            props["missing"] = kind == "placeholder"
        prev = old.get(str(sc.id))
        if prev:
            for k in USER_KEYS:
                if (prev.props or {}).get("user_edited") and k in (prev.props or {}):
                    props[k] = prev.props[k]
        in_s = 0.0
        if a is not None and a.kind == "video" and (a.meta or {}).get("lipsync"):
            in_s = round(sc.start_s, 3)
            props["motion"], props["lipsync"] = "static", True
        elif a is not None and a.kind == "video" and a.duration_s:
            slack = a.duration_s - (sc.end_s - sc.start_s) - 0.3
            in_s = round(prev.in_s if prev and (prev.props or {}).get("user_edited") else (rnd.uniform(0, min(slack, 6)) if slack > 0.5 else 0.0), 2)
        db.add(m.TimelineItem(project_id=project.id, scene_id=sc.id, asset_id=a.id if a else None, track="V1", kind=kind, start_s=sc.start_s,
                              duration_s=round(sc.end_s - sc.start_s, 3), in_s=in_s, props=props))
    has_subs = db.query(m.Subtitle).filter_by(project_id=project.id).count() > 0
    if resync_subtitles or not has_subs:
        db.query(m.Subtitle).filter_by(project_id=project.id).delete()
    if tr and tr.words and (resync_subtitles or not has_subs):
        for k, g in enumerate(caption_groups(tr.words)):
            db.add(m.Subtitle(project_id=project.id, idx=k, start_s=g[0]["s"], end_s=g[-1]["e"], text=" ".join(w["w"] for w in g), words=[{"w": w["w"], "s": w["s"], "e": w["e"]} for w in g]))
    db.flush()
    return len(scs), missing


def run(ctx):
    n, missing = build(ctx.db, ctx.project, bool(ctx.params.get("resync_subtitles", True)))
    v = save_version(ctx.db, ctx.project, ctx.params.get("reason", "Timeline assembled"))
    return {"summary": "Timeline v%d: %d clips, subtitles synced to narration%s" % (v, n, (", %d placeholders for missing visuals" % missing) if missing else ""),
            "state": {"timeline_version": v}}
