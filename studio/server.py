"""FrameForge Studio: web server. Run:  python server.py  (then open http://localhost:8000)"""
import hashlib
import os
import shutil
import time

from fastapi import Body, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from engine import catalog, core, llm, media, mg, pipeline, thumb, voice, writer

app = FastAPI(title="FrameForge Studio")
WEB = os.path.join(core.ROOT, "web")
BRANDS = os.path.join(core.DATA, "brands.json")
THUMBS = os.path.join(core.DATA, "thumbs")
os.makedirs(THUMBS, exist_ok=True)


def _token():
    pw = core.get_settings().get("owner_password") or ""
    return hashlib.sha256(("ff|" + pw).encode()).hexdigest()[:32] if pw else ""


@app.middleware("http")
async def auth(request: Request, call_next):
    tok = _token()
    path = request.url.path
    if tok and path.startswith("/api/") and path not in ("/api/login", "/api/health") and request.cookies.get("ff_owner") != tok:
        return JSONResponse({"detail": "login required"}, status_code=401)
    resp = await call_next(request)
    if path == "/" or path.startswith("/static/"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


@app.post("/api/login")
def login(body: dict = Body(...)):
    tok = _token()
    if tok and hashlib.sha256(("ff|" + str(body.get("password", ""))).encode()).hexdigest()[:32] != tok:
        raise HTTPException(403, "Wrong password")
    r = JSONResponse({"ok": True})
    r.set_cookie("ff_owner", tok, max_age=86400 * 30, httponly=True, samesite="lax")
    return r


@app.get("/api/health")
def health():
    return {"ok": True, "locked": bool(_token())}


def safe_path(path):
    full = os.path.realpath(path)
    if not full.startswith(os.path.realpath(core.DATA) + os.sep) or not os.path.isfile(full):
        raise HTTPException(404, "file not found")
    return full


@app.get("/api/file")
def get_file(path: str, download: str = ""):
    full = safe_path(path)
    return FileResponse(full, filename=download or None)


# ------------------------------------------------------------------ catalog / settings
def settings_public():
    s = core.get_settings()
    out = {}
    for k, v in s.items():
        if k.endswith("_key") or k == "owner_password":
            out[k] = ("•" * 6 + str(v)[-4:]) if v else ""
        else:
            out[k] = v
    out["llm_active"] = llm.provider()
    out["stock_video_ready"] = bool(s.get("pexels_key") or s.get("pixabay_key"))
    return out


@app.get("/api/catalog")
def get_catalog():
    return {
        "formats": [dict(v, id=k) for k, v in catalog.FORMATS.items()],
        "themes": [{"id": k, "name": v["name"], "desc": v["desc"], "bg": v["bg"], "bg2": v["bg2"], "ink": v["ink"], "accent": v["accent"], "accent2": v["accent2"]}
                   for k, v in catalog.THEMES.items()],
        "languages": catalog.LANGUAGES, "motion_graphics": catalog.MOTION_GRAPHICS, "motions": catalog.MOTIONS, "transitions": catalog.TRANSITIONS,
        "filters": catalog.FILTERS, "captions": catalog.CAPTION_STYLES, "music": catalog.MUSIC_MOODS, "durations": catalog.DURATIONS,
        "tips": catalog.TIPS, "ai_styles": list(media.AI_STYLES), "sfx": ["whoosh", "hit", "riser", "tick", "click", "pop", "rumble", "shutter", "typing", "heartbeat", "water", "wind", "glitch", "ding"],
        "mg_fullscreen": sorted(mg.FULLSCREEN), "settings": settings_public(), "title_formulas": writer.TITLE_FORMULAS,
    }


@app.get("/api/defaults")
def get_defaults(format: str = "documentary"):
    return pipeline.default_settings(format)


@app.get("/api/settings")
def get_settings():
    return settings_public()


@app.post("/api/settings")
def post_settings(body: dict = Body(...)):
    patch = {k: v for k, v in body.items() if not (isinstance(v, str) and v.startswith("•"))}
    core.update_settings(patch)
    r = JSONResponse(settings_public())
    if "owner_password" in patch:
        r.set_cookie("ff_owner", _token(), max_age=86400 * 30, httponly=True, samesite="lax")
    return r


@app.get("/api/voices")
def get_voices(lang: str = "en"):
    vs = voice.list_all(lang)
    loc = catalog.LANG_LOCALE.get(lang, "en-US")[:2]
    extra = voice.more_neural(loc) if loc != "en" else []
    return {"voices": vs, "more": extra}


@app.get("/api/voices/preview")
def voice_preview(id: str, lang: str = "en"):
    try:
        return FileResponse(voice.preview(id, lang), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(400, str(e))


# ------------------------------------------------------------------ tools
@app.post("/api/titles")
def post_titles(body: dict = Body(...)):
    try:
        return {"titles": writer.gen_titles(body.get("topic", ""), body.get("format", "documentary"), body.get("language", "en"), int(body.get("n", 10)), body.get("reference", ""))}
    except Exception as e:
        raise HTTPException(502, str(e))


@app.post("/api/reference")
def post_reference(body: dict = Body(...)):
    return writer.analyze_reference(body.get("url", ""))


@app.post("/api/estimate")
def post_estimate(body: dict = Body(...)):
    return pipeline.estimate(body)


@app.post("/api/persona")
def post_persona(body: dict = Body(...)):
    return writer.make_persona(body.get("topic", ""), body.get("bible", ""))


@app.post("/api/thumb/references")
def thumb_refs(body: dict = Body(...)):
    return {"refs": thumb.references(body.get("topic", ""), int(body.get("n", 12)))}


@app.post("/api/thumb/url")
def thumb_url(body: dict = Body(...)):
    info = thumb.from_url(body.get("url", ""))
    if not info.get("error"):
        info["analysis"] = {k: v for k, v in thumb.analyze(info).items() if k != "path"}
    return info


@app.post("/api/thumb/concepts")
def thumb_concepts(body: dict = Body(...)):
    return {"concepts": thumb.concepts(body.get("title", ""), body.get("format", "documentary"), body.get("ref_title", ""), body.get("persona"), int(body.get("n", 4)))}


@app.post("/api/thumb/generate")
def thumb_generate(body: dict = Body(...)):
    concept = body.get("concept") or {}
    if not concept.get("prompt"):
        raise HTTPException(400, "concept.prompt is required")
    accent = None
    if (body.get("ref") or {}).get("id"):
        accent = thumb.analyze(body["ref"]).get("accent")
    try:
        out = thumb.generate(concept, THUMBS, "t_" + core.uid(8), body.get("face"), body.get("accent") or accent, int(time.time()) % 99999, body.get("style") or "photo")
    except Exception as e:
        raise HTTPException(502, str(e))
    return {"path": out}


@app.get("/api/thumb/gallery")
def thumb_gallery():
    fs = sorted([os.path.join(THUMBS, f) for f in os.listdir(THUMBS) if f.endswith(".png")], key=os.path.getmtime, reverse=True)
    return {"items": fs[:60]}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".webm", ".mkv"):
        raise HTTPException(400, "Unsupported file type")
    dest = os.path.join(core.UPLOADS, core.uid(12) + ext)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"path": dest, "name": file.filename, "duration": core.media_duration(dest) if ext not in (".jpg", ".jpeg", ".png", ".webp") else 0}


# ------------------------------------------------------------------ brand profiles
@app.get("/api/brands")
def brands():
    return {"brands": core.load_json(BRANDS, []) or []}


@app.post("/api/brands")
def brand_save(body: dict = Body(...)):
    bs = core.load_json(BRANDS, []) or []
    if not body.get("id"):
        body["id"] = core.uid(8)
        bs.append(body)
    else:
        bs = [body if b["id"] == body["id"] else b for b in bs]
    core.save_json(BRANDS, bs)
    return body


@app.delete("/api/brands/{bid}")
def brand_delete(bid: str):
    core.save_json(BRANDS, [b for b in (core.load_json(BRANDS, []) or []) if b["id"] != bid])
    return {"ok": True}


# ------------------------------------------------------------------ projects
def need(pid):
    p = pipeline.load(pid)
    if not p:
        raise HTTPException(404, "project not found")
    return p


def editable(p):
    if p["status"] in ("queued", "processing", "rendering"):
        raise HTTPException(409, "This video is busy. Wait for the current job to finish.")


def done(p):
    pipeline.save(p)
    return pipeline.load(p["id"])


@app.get("/api/projects")
def projects():
    return {"projects": pipeline.list_projects(), "queue": pipeline._state}


@app.post("/api/projects")
def project_create(body: dict = Body(...)):
    p = pipeline.create(body)
    if body.get("start"):
        pipeline.enqueue(p["id"], "generate")
    return pipeline.load(p["id"])


@app.get("/api/projects/{pid}")
def project_get(pid: str, light: int = 0):
    p = need(pid)
    if light:
        return {"id": p["id"], "status": p["status"], "progress": p["progress"], "title": p["title"], "outputs": p.get("outputs"), "dirty": p.get("dirty")}
    return p


@app.patch("/api/projects/{pid}")
def project_patch(pid: str, body: dict = Body(...)):
    p = need(pid)
    editable(p)
    if "title" in body:
        p["title"] = str(body["title"])[:100]
    for k, v in (body.get("settings") or {}).items():
        if k in p["settings"] and k not in ("format", "duration_min", "language", "aspect"):
            p["settings"][k] = v
            p["dirty"] = True
            if k in ("music", "music_volume", "sfx", "sfx_volume", "voice_fx", "ambience", "voice_reverb"):
                p["audio_dirty"] = True
    if "user_sfx" in body:
        p["user_sfx"] = body["user_sfx"]
        p["dirty"] = p["audio_dirty"] = True
    return done(p)


@app.delete("/api/projects/{pid}")
def project_delete(pid: str):
    pipeline.cancel(pid)
    pipeline.delete(pid)
    return {"ok": True}


@app.post("/api/projects/{pid}/start")
def project_start(pid: str):
    p = need(pid)
    editable(p)
    pipeline.enqueue(pid, "generate")
    return pipeline.load(pid)


@app.post("/api/projects/{pid}/cancel")
def project_cancel(pid: str):
    pipeline.cancel(pid)
    return {"ok": True}


@app.post("/api/projects/{pid}/render")
def project_render(pid: str, body: dict = Body(default={})):
    p = need(pid)
    editable(p)
    if not p.get("shots"):
        raise HTTPException(400, "Nothing to render yet")
    pipeline.enqueue(pid, "final" if body.get("final") else "preview")
    return pipeline.load(pid)


@app.get("/api/projects/{pid}/frame")
def project_frame(pid: str, t: float = 0.0):
    p = need(pid)
    try:
        pipeline.apply_times(p)
        path = pipeline.preview_frame(p, t)
    except Exception as e:
        raise HTTPException(500, str(e))
    data = open(path, "rb").read()
    os.remove(path)
    return Response(data, media_type="image/jpeg")


@app.get("/api/projects/{pid}/thumb")
def project_thumb_img(pid: str):
    p = need(pid)
    t = (p.get("outputs") or {}).get("thumbnail")
    if not t or not os.path.exists(t):
        raise HTTPException(404, "no thumbnail")
    return FileResponse(t)


@app.post("/api/projects/{pid}/shots/{sid}")
def shot_edit(pid: str, sid: str, body: dict = Body(...)):
    p = need(pid)
    editable(p)
    try:
        op = body.get("op", "edit")
        if op == "split":
            pipeline.split_shot(p, sid, float(body["t"]))
        elif op == "delete":
            pipeline.delete_shot(p, sid)
        elif op == "replace":
            pipeline.replace_asset(p, sid, body["mode"], body.get("data") or {})
        else:
            pipeline.edit_shot(p, sid, body.get("patch") or {})
        pipeline.apply_times(p)
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e).strip("'"))
    except Exception as e:
        raise HTTPException(502, str(e))
    return done(p)


@app.post("/api/projects/{pid}/alternatives")
def shot_alternatives(pid: str, body: dict = Body(...)):
    p = need(pid)
    return {"items": media.alternatives(body.get("query", ""), "", p["settings"].get("aspect") == "9:16")}


@app.post("/api/projects/{pid}/beats/{bi}")
def beat_edit(pid: str, bi: int, body: dict = Body(...)):
    p = need(pid)
    editable(p)
    try:
        pipeline.revoice(p, bi, str(body.get("text", "")).strip())
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, str(e))
    return done(p)


@app.post("/api/projects/{pid}/overlays")
def overlay_add(pid: str, body: dict = Body(...)):
    p = need(pid)
    editable(p)
    pipeline.add_overlay(p, body)
    return done(p)


@app.post("/api/projects/{pid}/overlays/{oid}")
def overlay_edit(pid: str, oid: str, body: dict = Body(...)):
    p = need(pid)
    editable(p)
    try:
        pipeline.edit_overlay(p, oid, body)
    except KeyError:
        raise HTTPException(404, "overlay not found")
    return done(p)


@app.post("/api/projects/{pid}/thumbnail")
def project_thumb(pid: str, body: dict = Body(default={})):
    p = need(pid)
    if body.get("concept"):
        p["thumb_choice"] = dict(p.get("thumb_choice") or {}, concept=body["concept"])
    elif body.get("text"):
        p["thumb_choice"] = dict(p.get("thumb_choice") or {}, text=body["text"], concept=None)
    try:
        thumb.for_project(p)
    except Exception as e:
        raise HTTPException(502, str(e))
    return done(p)


@app.post("/api/projects/{pid}/pack")
def project_pack(pid: str):
    p = need(pid)
    p["pack"] = writer.gen_pack(p)
    return done(p)


app.mount("/static", StaticFiles(directory=WEB), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    return open(os.path.join(WEB, "index.html"), encoding="utf-8").read()


@app.on_event("startup")
def _startup():
    pipeline.recover()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), log_level="warning")
