"""Visual Generation Agent: produces or retrieves the asset for one storyboard scene.

Every substitution (e.g. stock footage was unavailable so an AI still with a camera move was used) is written to the
scene plan and the event log; nothing is swapped silently, and a still is never labelled as video."""
import base64
import os
import random

from PIL import Image

from fda.database import models as m
from fda.permissions import budget_manager as budget
from fda.providers import registry
from fda.providers.base import NotConfigured, ProviderError, download
from fda.services import assets
from fda.storage.store import scratch_dir

from . import blender as blender_agent
from .common import style

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


def from_search(ctx, scene, vtype, work, used, blocked):
    cap, kind = SEARCH_CAP[vtype]
    portrait = style(ctx.db, ctx.project)[1].get("aspect") == "9:16"
    plan = scene.plan or {}
    queries = [q for q in [plan.get("search_query"), plan.get("subject"), " ".join((scene.narration or "").split()[:6])] if q]
    errors = []
    for prov in registry.for_cap(ctx.db, cap):
        for q in queries[:2]:
            try:
                cands = prov.search(q, kind=kind, n=10, portrait=portrait)
            except ProviderError as e:
                errors.append("%s: %s" % (prov.label, e))
                break
            need = scene.end_s - scene.start_s
            cands.sort(key=lambda c: (c["kind"] == "video" and c.get("duration", 0) < need))  # long-enough clips first
            for c in cands:
                if c["id"] in used or any(b in (c.get("title") or "").lower() for b in blocked):
                    continue
                if c.get("commercial_use") == "no":
                    continue
                ext = ".webm" if ".webm" in c["url"] else ".mp4" if kind == "video" else ".jpg"
                raw = os.path.join(work, "%s%s" % (c["id"].replace("/", "_"), ext if kind == "video" else ".raw"))
                try:
                    download(c["url"], raw, timeout=240, max_mb=250 if kind == "video" else 40)
                    path = raw if kind == "video" else normalise_image(raw, raw[:-4] + ".jpg")
                    a = assets.register(ctx.db, path, ctx.project.id, "scene", "scenes", os.path.basename(path), origin="archive" if vtype == "archive" else "stock",
                                        provider=prov.name, source_url=c.get("source_page") or c["url"], settings={"query": q}, license=c["license"],
                                        attribution=c.get("attribution", ""), commercial_use=c.get("commercial_use", "unknown"), terms_url=c.get("terms_url"),
                                        meta={"source_id": c["id"], "title": c.get("title", "")})
                    return a, prov.name
                except Exception as e:
                    errors.append("%s download: %s" % (prov.label, str(e)[:120]))
                    continue
    raise ProviderError("No usable %s result (%s)" % (vtype, "; ".join(errors[-3:]) or "no matches"), retryable=True)


def ai_image(ctx, scene, work, seed):
    plan = scene.plan or {}
    _, st = style(ctx.db, ctx.project)
    portrait = st.get("aspect") == "9:16"
    w, h = (720, 1280) if portrait else (1280, 720)
    prompt = plan.get("prompt") or scene.narration
    extras = ", ".join(x for x in [plan.get("shot", "").replace("_", " ") + " shot" if plan.get("shot") else "", plan.get("lens"), plan.get("lighting"), plan.get("color")] if x)
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
    look = persona.get("look") or "a friendly middle-aged presenter with short grey hair, round glasses and a navy sweater"
    prompt = ("Medium close-up, chest up, of an original fictional character: %s. Looking straight into the camera, mouth gently closed, slight warm smile, "
              "face centred in the upper middle of the frame, both eyes visible, in %s. Natural window light, filmed on a smartphone at eye level, photorealistic.") % (
        look, persona.get("set", "a tidy home studio with soft background blur"))
    fake = type("S", (), {"plan": {"prompt": prompt}, "narration": prompt, "idx": 0, "id": "avatar"})()
    a, _ = ai_image(ctx, fake, work, 7)
    st["avatar_image_asset"] = str(a.id)
    ps.style = dict(ps.style or {}, avatar_image_asset=str(a.id))
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
        return avatar_portrait(ctx, work), "talking_photo"
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
            plan["avatar_engine"] = "talking_photo"
        scene.plan = plan
        if ctx.params.get("redo"):
            scene.version = (scene.version or 1) + 1
        return {"summary": "Scene %d: %s from %s%s" % (scene.idx, vt.replace("_", " "), prov, " (substituted)" if vt != requested else "")}
    scene.asset_status, scene.last_error = "failed", "; ".join(errors)[:2000]
    ctx.log("Scene %d has no visual: %s" % (scene.idx, scene.last_error[:400]), "error")
    return {"summary": "Scene %d failed to get a visual; QC will retry it" % scene.idx, "scene_failed": True}
