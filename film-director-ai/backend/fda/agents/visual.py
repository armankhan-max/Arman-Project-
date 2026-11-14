"""Visual Generation Agent: produces or retrieves the asset for one storyboard scene.

Every substitution (e.g. stock footage was unavailable so an AI still with a camera move was used) is written to the
scene plan and the event log; nothing is swapped silently, and a still is never labelled as video."""
import base64
import os
import random
import re

from PIL import Image

from fda.database import models as m
from fda.permissions import budget_manager as budget
from fda.providers import registry
from fda.providers.base import NotConfigured, ProviderError, download
from fda.services import assets
from fda.storage.store import scratch_dir

from . import blender as blender_agent
from .common import STOP, keywords, style

FALLBACK = {"stock_video": ["stock_image", "archive", "ai_image"], "stock_image": ["archive", "ai_image", "stock_video"],
            "archive": ["stock_image", "ai_image"], "ai_image": ["stock_image", "archive", "stock_video"], "ai_video": ["stock_video", "ai_image"],
            "blender": ["ai_image", "stock_video"], "avatar": ["ai_image"], "user": ["stock_video", "ai_image"]}
SEARCH_CAP = {"stock_video": ("stock_video", "video"), "stock_image": ("stock_image", "image"), "archive": ("archive_image", "image")}


def normalise_image(src, dest, max_side=2560):
    Image.MAX_IMAGE_PIXELS = 300_000_000
    with Image.open(src) as im:
        im = im.convert("RGB")
        if max(im.size) > max_side:
            im.thumbnail((max_side, max_side), Image.LANCZOS)
        if min(im.size) < 300:
            raise ProviderError("Image too small", retryable=False)
        im.save(dest, "JPEG", quality=92)
    return dest


def used_sources(db, project_id, except_scene):
    ids = set()
    for sc in db.query(m.Scene).filter(m.Scene.project_id == project_id, m.Scene.asset_id.isnot(None), m.Scene.id != except_scene).all():
        a = db.get(m.Asset, sc.asset_id)
        if a and a.meta.get("source_id"):
            ids.add(a.meta["source_id"])
    return ids


def scene_queries(ctx, scene):
    """Search phrases for one scene: the storyboard's query, its subject, named things in the narration, and the project topic."""
    plan = scene.plan or {}
    names = re.findall(r"(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})", scene.narration or "")
    names = [n for n in names if n.lower() not in STOP and len(n) > 3][:3]
    qs = [plan.get("search_query"), plan.get("subject"), " ".join(names), " ".join(keywords(scene.narration, 3)),
          " ".join(keywords(ctx.project.title, 3))]
    out = []
    for q in qs:
        q = (q or "").strip()
        if q and q.lower() not in [x.lower() for x in out]:
            out.append(q)
    return out[:4]


BROAD = {"internet_archive", "nasa_video"}
GENERIC = {"nasa", "video", "image", "photo", "footage", "film", "shot", "close", "wide", "view", "scene", "cinematic", "stock"}


def relevance(c, terms, need):
    text = (c.get("title") or "").lower()
    hits = sum(1 for t in terms if t in text)
    s = hits * 2.0 + (1.5 if hits >= 2 else 0)
    if c["kind"] == "video":
        s += 1.0 if (c.get("duration") or 0) >= need or not c.get("duration") else -0.5
    w, h = c.get("width") or 0, c.get("height") or 0
    if w and h:
        s += 0.5 if w >= 1280 else -0.5 if w < 800 else 0
    return s


def from_search(ctx, scene, vtype, work, used, blocked):
    """Internet visual research for one scene: query every configured source with several phrasings,
    rank candidates by relevance to the narration, then download the best licence-cleared result."""
    cap, kind = SEARCH_CAP[vtype]
    portrait = style(ctx.db, ctx.project)[1].get("aspect") == "9:16"
    queries = scene_queries(ctx, scene)
    terms = set(keywords(" ".join([scene.narration or "", (scene.plan or {}).get("subject") or "", (scene.plan or {}).get("search_query") or ""]), 12)) - GENERIC
    need = scene.end_s - scene.start_s
    errors, pool, seen = [], [], set()
    for prov in registry.for_cap(ctx.db, cap):
        for q in queries[:3]:
            try:
                for c in prov.search(q, kind=kind, n=8, portrait=portrait):
                    if c["id"] in seen or c["id"] in used or c.get("commercial_use") == "no" or any(b in (c.get("title") or "").lower() for b in blocked):
                        continue
                    if kind == "image" and not portrait and c.get("width") and c.get("height") and c["width"] / float(c["height"]) < 1.25:
                        continue  # landscape projects use pictures that fill the frame
                    seen.add(c["id"])
                    c["_q"], c["_prov"] = q, prov.name
                    c["_score"] = relevance(c, terms, need) - 0.3 * queries.index(q)
                    if prov.name in BROAD and not any(t in (c.get("title") or "").lower() for t in terms):
                        continue  # full-text archives return loosely related films; demand a real match
                    pool.append(c)
            except ProviderError as e:
                errors.append("%s: %s" % (prov.label, str(e)[:120]))
                break
        if len([c for c in pool if c["_score"] >= 2]) >= 6:
            break  # enough relevant material; do not hammer every source
    pool.sort(key=lambda c: -c["_score"])
    # try the best results but spread across sources, so one rate-limited host cannot sink the scene
    order, per = [], {}
    for c in pool:
        if per.get(c["_prov"], 0) < 3:
            order.append(c)
            per[c["_prov"]] = per.get(c["_prov"], 0) + 1
    for c in order[:9]:
        ext = ".webm" if ".webm" in c["url"] else ".mp4" if kind == "video" else ".jpg"
        raw = os.path.join(work, "%s%s" % (re.sub(r"[^\w.-]", "_", c["id"])[:80], ext if kind == "video" else ".raw"))
        try:
            download(c["url"], raw, timeout=240, max_mb=250 if kind == "video" else 40)
            path = raw if kind == "video" else normalise_image(raw, raw[:-4] + ".jpg")
            a = assets.register(ctx.db, path, ctx.project.id, "scene", "scenes", os.path.basename(path), origin="archive" if vtype == "archive" else "stock",
                                provider=c["_prov"], source_url=c.get("source_page") or c["url"], settings={"query": c["_q"], "relevance": round(c["_score"], 2)},
                                license=c["license"], attribution=c.get("attribution", ""), commercial_use=c.get("commercial_use", "unknown"), terms_url=c.get("terms_url"),
                                meta={"source_id": c["id"], "title": c.get("title", "")[:300]})
            ctx.log("Scene %d: found '%s' on %s (query '%s')" % (scene.idx, (c.get("title") or "")[:70], c["_prov"], c["_q"]))
            return a, c["_prov"]
        except Exception as e:
            errors.append("%s download: %s" % (c["_prov"], str(e)[:120]))
    raise ProviderError("No usable %s result for %s (%s)" % (vtype, queries, "; ".join(errors[-3:]) or "no matches"), retryable=True)


def ai_image(ctx, scene, work, seed):
    plan = scene.plan or {}
    _, st = style(ctx.db, ctx.project)
    portrait = st.get("aspect") == "9:16"
    w, h = (720, 1280) if portrait else (1280, 720)
    prompt = plan.get("prompt") or scene.narration
    extras = ", ".join(x for x in [plan.get("shot", "").replace("_", " ") + " shot" if plan.get("shot") else "", plan.get("lens"), plan.get("lighting"), plan.get("color")] if x)
    if ctx.project.mode == "avatar":
        persona = st.get("persona") or {}
        full = ("%s. Candid photo taken on a smartphone by an ordinary person%s, natural daylight, true-to-life colors, slightly imperfect framing, real textures and small everyday clutter, "
                "sharp focus on the subject, wide 16:9 frame filled edge to edge. Show the objects and at most a pair of hands, no faces. Photorealistic, no studio lighting, no text, no watermark, no logo.") % (
            prompt.rstrip("."), (" in " + persona["set"].rstrip(".")) if persona.get("set") and scene.idx % 3 == 0 else " at home")
    else:
        full = "%s. %s. Photorealistic, natural skin and materials, no text, no watermark, no logo." % (prompt.rstrip("."), extras)
    neg = ", ".join(x for x in [plan.get("negative_prompt"), "text, watermark, logo, plastic skin, deformed hands, extra fingers", st.get("blocklist")] if x)
    errors = []
    for prov in registry.for_cap(ctx.db, "text_to_image"):
        rec = None
        try:
            rec = budget.reserve(ctx.db, prov, "image", 1, "images", ctx.project.id)
            dest = os.path.join(work, "ai_%s_%d.png" % (scene.idx, seed))
            info = prov.generate(full, dest, w, h, seed, neg)
            budget.commit(ctx.db, rec)
            jpg = normalise_image(dest, dest[:-4] + ".jpg")
            a = assets.register(ctx.db, jpg, ctx.project.id, "scene", "scenes", os.path.basename(jpg), origin="generated", provider=prov.name, prompt=full,
                                settings=dict(info, negative=neg, width=w, height=h), license="AI-generated (%s terms)" % prov.label, commercial_use="unknown",
                                meta={"source_id": "ai-%s-%d" % (scene.id, seed), "ai_generated": True})
            return a, prov.name
        except budget.BudgetError as e:
            errors.append(str(e))
        except ProviderError as e:
            budget.release(ctx.db, rec)
            errors.append("%s: %s" % (prov.label, e))
    raise ProviderError("AI image generation failed (%s)" % "; ".join(errors[-3:]), retryable=True)


def ai_video(ctx, scene, work, seed):
    plan = scene.plan or {}
    dur = scene.end_s - scene.start_s
    errors = []
    _, st = style(ctx.db, ctx.project)
    for cap in ("image_to_video", "text_to_video"):
        for prov in registry.for_cap(ctx.db, cap):
            rec = None
            try:
                rec = budget.reserve(ctx.db, prov, "video", 10 if dur > 7 else 5, "seconds", ctx.project.id)
                img_url = None
                if cap == "image_to_video":
                    still, _ = ai_image(ctx, scene, work, seed)
                    with open(assets.local(still), "rb") as f:
                        img_url = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
                prompt = "%s. Camera: %s, %s. %s" % (plan.get("prompt") or scene.narration, plan.get("movement", "").replace("_", " "), plan.get("shot", "").replace("_", " "),
                                                    plan.get("subject_motion", ""))
                job = prov.submit(prompt, img_url, dur, st.get("aspect", "16:9"), seed)
                ctx.log("Submitted to %s (job %s)" % (prov.label, job))
                dest = prov.wait(job, os.path.join(work, "gen_%s_%d.mp4" % (scene.idx, seed)))
                budget.commit(ctx.db, rec)
                a = assets.register(ctx.db, dest, ctx.project.id, "scene", "scenes", os.path.basename(dest), origin="generated", provider=prov.name, prompt=prompt,
                                    settings={"job": job, "seed": seed}, license="AI-generated (%s terms)" % prov.label, commercial_use="unknown",
                                    meta={"source_id": "gen-%s" % job, "ai_generated": True})
                return a, prov.name
            except budget.BudgetError as e:
                errors.append(str(e))
            except ProviderError as e:
                budget.release(ctx.db, rec)
                errors.append("%s: %s" % (prov.label, e))
    raise NotConfigured("AI video generation unavailable (%s)" % ("; ".join(errors[-3:]) or "no video provider configured"))


def avatar_portrait(ctx, work):
    db, p = ctx.db, ctx.project
    ps, st = style(db, p)
    aid = st.get("avatar_image_asset")
    if aid:
        a = db.get(m.Asset, aid)
        if a:
            return a
    persona = st.get("persona") or {}
    if st.get("character_id"):
        ch = db.get(m.Character, st["character_id"])
        if ch and ch.image_asset_id and db.get(m.Asset, ch.image_asset_id):
            return db.get(m.Asset, ch.image_asset_id)
    look = persona.get("look") or "a friendly middle-aged presenter with short grey hair, round glasses and a navy sweater"
    from fda.services.characters import portrait_prompt
    prompt = portrait_prompt(dict(persona, look=look, set=persona.get("set", "a tidy lived-in kitchen")))
    fake = type("S", (), {"plan": {"prompt": prompt}, "narration": prompt, "idx": 0, "id": "avatar"})()
    a, _ = ai_image(ctx, fake, work, 7)
    st["avatar_image_asset"] = str(a.id)
    ps.style = dict(ps.style or {}, avatar_image_asset=str(a.id))
    return a


def lipsync_video(ctx, portrait_asset, work):
    """One lip-synced talking-head video for the whole narration (made once per project, reused by every avatar scene).
    Returns None when no lip-sync provider is configured, so the built-in talking photo is used instead."""
    from sqlalchemy import text as sql
    db, p = ctx.db, ctx.project
    provs = [x for x in registry.for_cap(db, "lipsync")]
    if not provs:
        return None
    prov = provs[0]
    db.execute(sql("SELECT pg_advisory_xact_lock(:k)"), {"k": p.id.int % (2 ** 62)})  # scenes run in parallel; only one may generate
    ps = db.query(m.ProjectSettings).filter_by(project_id=p.id).one()
    db.refresh(ps)
    vo = db.query(m.Voiceover).filter_by(project_id=p.id).order_by(m.Voiceover.created_at.desc()).first()
    key = "%s:%s" % (portrait_asset.id, vo.id if vo else "")
    cur = (ps.style or {}).get("avatar_video")
    if cur and cur.get("key") == key and db.get(m.Asset, cur["asset_id"]):
        return db.get(m.Asset, cur["asset_id"])
    if not vo or not vo.processed_asset_id:
        return None
    from fda.services import media
    mp3 = os.path.join(work, "narration.mp3")
    media.run(["ffmpeg", "-y", "-v", "error", "-i", assets.local(db.get(m.Asset, vo.processed_asset_id)), "-b:a", "128k", mp3])
    rec = budget.reserve(db, prov, "lipsync", vo.duration_s or 0, "seconds", p.id)
    try:
        char = db.get(m.Character, (ps.style or {}).get("character_id")) if (ps.style or {}).get("character_id") else None
        tp = (char.external or {}).get("heygen_talking_photo_id") if char else None
        if not tp:
            tp = prov.upload_photo(assets.local(portrait_asset))
            if char:
                char.external = dict(char.external or {}, heygen_talking_photo_id=tp)
        ps_ = db.query(m.ProjectSettings).filter_by(project_id=p.id).one()
        job = prov.submit_talk(tp, prov.upload_audio(mp3), ps_.width, ps_.height)
        ctx.log("Lip-sync video submitted to %s (job %s)" % (prov.label, job))
        dest = prov.wait(job, os.path.join(work, "avatar_talk.mp4"), timeout=3600, every=15)
    except Exception:
        budget.release(db, rec)
        raise
    budget.commit(db, rec)
    a = assets.register(db, dest, p.id, "scene", "avatar", "avatar_lipsync.mp4", origin="generated", provider=prov.name, settings={"job": job},
                        license="AI-generated (%s terms)" % prov.label, commercial_use="unknown", meta={"ai_generated": True, "lipsync": True})
    ps.style = dict(ps.style or {}, avatar_video={"key": key, "asset_id": str(a.id)})
    db.commit()
    return a


def produce(ctx, scene, vtype, work, seed, used, blocked):
    if vtype in SEARCH_CAP:
        return from_search(ctx, scene, vtype, work, used, blocked)
    if vtype == "ai_image":
        return ai_image(ctx, scene, work, seed)
    if vtype == "ai_video":
        return ai_video(ctx, scene, work, seed)
    if vtype == "blender":
        plan = scene.plan or {}
        ps, st = style(ctx.db, ctx.project)
        w, h = (1280, 720) if st.get("aspect") != "9:16" else (720, 1280)
        params = dict(plan.get("blender_params") or {}, move=(plan.get("blender_params") or {}).get("move") or {"orbit": "orbit", "push_in": "push_in", "pull_out": "pull_out"}.get(plan.get("movement"), "orbit"))
        a, _ = blender_agent.render(ctx.db, ctx.project.id, plan.get("blender_template") or "planet", params, scene.end_s - scene.start_s + 0.8, w, h, 24, seed=seed,
                                   progress=lambda f, msg: ctx.progress(f, msg))
        return a, "blender"
    if vtype == "avatar":
        portrait_asset = avatar_portrait(ctx, work)
        talk = lipsync_video(ctx, portrait_asset, work)
        if talk is not None:
            return talk, "heygen"
        return portrait_asset, "talking_photo"
    if vtype == "user":
        aid = (scene.plan or {}).get("user_asset_id")
        a = ctx.db.get(m.Asset, aid) if aid else None
        if not a:
            raise ProviderError("No uploaded footage assigned to this scene", retryable=False)
        return a, "user"
    raise ProviderError("Unknown visual type %s" % vtype, retryable=False)


def run(ctx):
    db = ctx.db
    scene = db.get(m.Scene, ctx.params["scene_id"])
    if scene is None:
        return {"skipped": True, "summary": "Scene no longer exists"}
    if scene.asset_status == "ready" and not ctx.params.get("redo") and (scene.asset_id or scene.visual_type == "motion_graphic"):
        return {"skipped": True, "summary": "Scene %d already has its asset" % scene.idx}
    if scene.visual_type == "motion_graphic":
        scene.asset_status, scene.provider, scene.asset_id = "ready", "motion_graphics", None
        return {"summary": "Scene %d: motion graphic (%s)" % (scene.idx, (scene.plan.get("motion_graphic") or {}).get("type"))}
    _, st = style(db, ctx.project)
    blocked = [b.strip().lower() for b in (st.get("blocklist") or "").split(",") if b.strip()]
    work = scratch_dir(ctx.project.id, "scenes", scene.idx)
    seed = random.Random("%s-%s" % (scene.id, ctx.task.attempts + (scene.version or 1))).randint(1, 10 ** 6)
    used = used_sources(db, ctx.project.id, scene.id)
    if ctx.params.get("redo") and scene.asset_id:  # a regeneration must not hand back the same picture
        cur = db.get(m.Asset, scene.asset_id)
        if cur and cur.meta.get("source_id"):
            used.add(cur.meta["source_id"])
    requested = scene.visual_type
    chain = [requested] + [t for t in FALLBACK.get(requested, []) if (st.get("sources") or {}).get(t, True) or t == "ai_image"]
    scene.asset_status = "generating"
    db.commit()
    errors = []
    for i, vt in enumerate(chain):
        try:
            a, prov = produce(ctx, scene, vt, work, seed, used, blocked)
        except (ProviderError, budget.BudgetError) as e:
            errors.append("%s: %s" % (vt, str(e)[:240]))
            db.rollback()
            scene = db.get(m.Scene, ctx.params["scene_id"])
            continue
        old = scene.asset_id
        db.add(m.SceneVersion(scene_id=scene.id, version=scene.version, plan=scene.plan, asset_id=old, reason=ctx.params.get("reason", "generated")))
        scene.asset_id, scene.provider, scene.asset_status, scene.last_error = a.id, prov, "ready", None
        plan = dict(scene.plan or {})
        plan.pop("substitution", None)
        if vt != requested:
            plan["substitution"] = {"requested": requested, "used": vt, "reason": "; ".join(errors)[:600]}
            ctx.log("Scene %d: %s unavailable, used %s instead (%s)" % (scene.idx, requested, vt, errors[-1][:200] if errors else ""), "warn")
        if vt == "avatar":
            plan["avatar_engine"] = prov
        scene.plan = plan
        if ctx.params.get("redo"):
            scene.version = (scene.version or 1) + 1
        return {"summary": "Scene %d: %s from %s%s" % (scene.idx, vt.replace("_", " "), prov, " (substituted)" if vt != requested else "")}
    scene.asset_status, scene.last_error = "failed", "; ".join(errors)[:2000]
    ctx.log("Scene %d has no visual: %s" % (scene.idx, scene.last_error[:400]), "error")
    return {"summary": "Scene %d failed to get a visual; QC will retry it" % scene.idx, "scene_failed": True}
