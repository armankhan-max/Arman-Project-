"""AI Video Studio web server. Run:  python app.py   then open http://localhost:8000"""
import hashlib
import json
import os
import re
import secrets
import shutil
import time

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

import llm
import media
import pipeline
import store
import thumb
import tts

app = FastAPI(title="AI Video Studio")
STATIC = os.path.join(store.BASE, "static")
SECRET_KEYS = ("anthropic_key", "openai_key", "pollinations_key", "pexels_key", "pixabay_key", "did_key")


# ---------------- owner login ----------------
def _hash(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex()


def _authed(request):
    a = store.get_auth()
    sid = request.cookies.get("sid")
    return bool(sid) and sid in a.get("sessions", {}) and a["sessions"][sid] > time.time()


@app.middleware("http")
async def guard(request: Request, call_next):
    path = request.url.path
    if (path.startswith("/api/") or path.startswith("/media/")) and path not in ("/api/me", "/api/login", "/api/setup"):
        if not _authed(request):
            return JSONResponse({"detail": "Please log in."}, status_code=401)
    return await call_next(request)


def _login_response(a):
    sid = secrets.token_urlsafe(32)
    a.setdefault("sessions", {})
    a["sessions"] = {k: v for k, v in a["sessions"].items() if v > time.time()}
    a["sessions"][sid] = time.time() + 30 * 86400
    store.save_auth(a)
    r = JSONResponse({"ok": True})
    r.set_cookie("sid", sid, max_age=30 * 86400, httponly=True, samesite="lax")
    return r


@app.get("/api/me")
def me(request: Request):
    return {"setup": bool(store.get_auth().get("hash")), "authed": _authed(request)}


@app.post("/api/setup")
async def setup(request: Request):
    a = store.get_auth()
    if a.get("hash"):
        raise HTTPException(400, "Owner password is already set.")
    pw = (await request.json()).get("password", "")
    if len(pw) < 6:
        raise HTTPException(400, "Use at least 6 characters.")
    a["salt"] = secrets.token_hex(16)
    a["hash"] = _hash(pw, a["salt"])
    return _login_response(a)


@app.post("/api/login")
async def login(request: Request):
    a = store.get_auth()
    pw = (await request.json()).get("password", "")
    time.sleep(0.4)
    if not a.get("hash") or not secrets.compare_digest(_hash(pw, a["salt"]), a["hash"]):
        raise HTTPException(401, "Wrong password.")
    return _login_response(a)


@app.post("/api/logout")
def logout(request: Request):
    a = store.get_auth()
    a.get("sessions", {}).pop(request.cookies.get("sid", ""), None)
    store.save_auth(a)
    return {"ok": True}


@app.post("/api/password")
async def change_password(request: Request):
    pw = (await request.json()).get("password", "")
    if len(pw) < 6:
        raise HTTPException(400, "Use at least 6 characters.")
    a = store.get_auth()
    a["salt"] = secrets.token_hex(16)
    a["hash"] = _hash(pw, a["salt"])
    store.save_auth(a)
    return {"ok": True}


# ---------------- settings (owner panel) ----------------
def _mask(s):
    s = dict(s)
    for k in SECRET_KEYS:
        s[k] = ("••••" + s[k][-4:]) if s.get(k) else ""
    return s


@app.get("/api/settings")
def get_settings():
    s = store.get_settings()
    out = _mask(s)
    out["defaults"] = {"styles": store.DEFAULT_STYLES, "script_rules": store.SCRIPT_RULES}
    out["llm_active"] = llm.provider(s)
    out["music_library"] = sorted(os.listdir(store.MUSIC))
    return out


@app.put("/api/settings")
async def put_settings(request: Request):
    patch = await request.json()
    patch = {k: v for k, v in patch.items() if k in store.DEFAULT_SETTINGS}
    for k in SECRET_KEYS:  # masked value coming back unchanged = keep the stored key
        if k in patch and str(patch[k]).startswith("••••"):
            del patch[k]
    if "styles" in patch and not isinstance(patch["styles"], dict):
        raise HTTPException(400, "Styles must be a JSON object.")
    return _mask(store.save_settings(patch))


@app.post("/api/music")
async def upload_music(file: UploadFile = File(...)):
    name = re.sub(r"[^\w.\-]", "_", os.path.basename(file.filename or "track.mp3"))
    with open(os.path.join(store.MUSIC, name), "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"name": name}


@app.get("/api/voices")
def voices():
    return tts.voices()


@app.post("/api/voice-preview")
async def voice_preview(request: Request):
    b = await request.json()
    out = os.path.join(store.DATA, "preview.mp3")
    try:
        await run_in_threadpool(tts.synth, (b.get("text") or "Hello! This is how your video will sound with this voice.")[:300], b["voice"], out, int(b.get("rate", 0)))
    except Exception as e:
        raise HTTPException(502, str(e))
    return FileResponse(out, media_type="audio/mpeg", headers={"Cache-Control": "no-store"})


# ---------------- projects ----------------
def _save_upload(up, pid, stem):
    ext = os.path.splitext(up.filename or "")[1].lower()[:6] or ".bin"
    name = stem + ext
    with open(os.path.join(store.pdir(pid), name), "wb") as f:
        shutil.copyfileobj(up.file, f)
    return name


@app.get("/api/projects")
def projects():
    return store.list_projects()


@app.post("/api/projects")
async def create_project(data: str = Form(...), voiceover: UploadFile = File(None), avatar: UploadFile = File(None),
                         avatar_video: UploadFile = File(None)):
    b = json.loads(data)
    title = (b.get("title") or "").strip()
    if not title:
        raise HTTPException(400, "Give the video a title.")
    cfg = store.get_settings()
    if not (b.get("script") or "").strip() and llm.provider(cfg) == "none":
        raise HTTPException(400, "AI script writing is off. Paste a script or turn on an AI provider in Settings.")
    if (voiceover is not None or avatar_video is not None) and not (b.get("script") or "").strip():
        raise HTTPException(400, "When you upload your own voiceover, also paste the script it reads, so scenes can be matched.")
    fields = ("style", "language", "voice", "rate", "aspect", "source", "captions", "music", "script", "notes", "persona", "show_title", "sfx", "style_prompt")
    p = store.new_project({"title": title, "minutes": max(0.3, min(33, float(b.get("minutes") or 1))),
                           **{k: b[k] for k in fields if k in b}})
    if voiceover is not None:
        p["voiceover"] = _save_upload(voiceover, p["id"], "voiceover")
        p["voice_mode"] = "upload"
    if avatar is not None:
        p["avatar"] = _save_upload(avatar, p["id"], "avatar")
    if avatar_video is not None:
        p["avatar_video"] = _save_upload(avatar_video, p["id"], "avatar_video")
    store.save_project(p)
    pipeline.start(p["id"], bool(b.get("preview")))
    return p


def _project(pid):
    p = store.get_project(pid)
    if not p:
        raise HTTPException(404, "Project not found.")
    return p


@app.get("/api/projects/{pid}")
def get_project(pid: str):
    return _project(pid)


@app.put("/api/projects/{pid}")
async def edit_project(pid: str, request: Request):
    p = _project(pid)
    if p["status"] in ("queued", "working"):
        raise HTTPException(409, "This video is rendering right now.")
    b = await request.json()
    for k in ("title", "style", "voice", "rate", "aspect", "source", "captions", "music", "show_title", "meta", "sfx"):
        if k in b:
            p[k] = b[k]
    if "scenes" in b:
        old = p["scenes"]
        new = []
        for s in b["scenes"]:
            o = old[s["_i"]] if isinstance(s.get("_i"), int) and 0 <= s["_i"] < len(old) else {}
            n = {**o, "narration": str(s.get("narration", "")).strip(), "text": str(s.get("text", ""))[:60],
                 "queries": [q.strip() for q in s.get("queries", []) if q.strip()], "kind": s.get("kind", "broll"),
                 "graphic": str(s.get("graphic", "")).strip()[:200],
                 "image_prompt": s.get("image_prompt") or o.get("image_prompt", "")}
            if not n["narration"]:
                continue
            if not o.get("custom") and (n["queries"] != o.get("queries") or s.get("refresh")):
                n["assets"] = []
            new.append(n)
        p["scenes"] = new
        p["script"] = "\n\n".join(s["narration"] for s in new)
    store.save_project(p)
    if b.get("render"):
        pipeline.start(pid, bool(b.get("preview")))
    return store.get_project(pid)


@app.post("/api/projects/{pid}/scenes/{i}/asset")
async def scene_asset(pid: str, i: int, file: UploadFile = File(...)):
    p = _project(pid)
    if not 0 <= i < len(p["scenes"]):
        raise HTTPException(404, "Scene not found.")
    os.makedirs(os.path.join(store.pdir(pid), "visuals"), exist_ok=True)
    name = _save_upload(file, pid, f"visuals/custom_{i}_{int(time.time())}")
    is_video = name.lower().endswith((".mp4", ".mov", ".webm", ".mkv", ".m4v"))
    p["scenes"][i]["assets"] = [{"path": name, "type": "video" if is_video else "image", "source": "your upload", "credit": ""}]
    p["scenes"][i]["custom"] = True
    store.save_project(p)
    return p["scenes"][i]


@app.post("/api/projects/{pid}/thumb")
async def project_thumb(pid: str, request: Request):
    p = _project(pid)
    b = await request.json()
    pipeline.make_thumb(p, b.get("text"), b.get("layout", "left"))
    p["version"] = int(time.time())
    store.save_project(p)
    return p


@app.delete("/api/projects/{pid}")
def delete_project(pid: str):
    _project(pid)
    shutil.rmtree(store.pdir(pid), ignore_errors=True)
    return {"ok": True}


@app.get("/media/{pid}/{path:path}")
def project_file(pid: str, path: str, download: int = 0):
    root = os.path.realpath(store.pdir(pid) if pid != "_thumbs" else store.THUMBS)
    full = os.path.realpath(os.path.join(root, path))
    if not full.startswith(root + os.sep) or not os.path.isfile(full) or full.endswith(".json"):
        raise HTTPException(404)
    return FileResponse(full, filename=os.path.basename(full) if download else None)


# ---------------- tools ----------------
@app.post("/api/titles")
async def gen_titles(request: Request):
    b = await request.json()
    if not (b.get("topic") or "").strip():
        raise HTTPException(400, "Type a topic first.")
    out, how = await run_in_threadpool(llm.titles, store.get_settings(), b["topic"], int(b.get("count", 10)), b.get("language", "English"), b.get("notes", ""))
    return {"titles": out, "source": how}


@app.post("/api/thumbnail")
async def gen_thumb(text: str = Form(...), layout: str = Form("left"), accent: str = Form("#FFD400"), arrow: str = Form("1"),
                    bg_prompt: str = Form(""), bg: UploadFile = File(None), subject: UploadFile = File(None)):
    tid = secrets.token_hex(5)
    paths = {}
    for key, up in (("bg", bg), ("subject", subject)):
        if up is not None and up.filename:
            paths[key] = os.path.join(store.THUMBS, f"{tid}_{key}{os.path.splitext(up.filename)[1].lower()[:6]}")
            with open(paths[key], "wb") as f:
                shutil.copyfileobj(up.file, f)
    note = ""
    if "bg" not in paths and bg_prompt.strip():
        try:
            paths["bg"] = await run_in_threadpool(media.ai_image, bg_prompt + ", no text, no watermark", os.path.join(store.THUMBS, f"{tid}_bg.jpg"), 1280, 720, int(tid, 16) % 99999)
        except Exception as e:
            note = f"AI background could not be generated ({str(e)[:80]}), used a plain backdrop."
    out = os.path.join(store.THUMBS, f"{tid}.jpg")
    thumb.make(out, text, paths.get("bg"), paths.get("subject"), layout, accent, arrow == "1")
    return {"url": f"/media/_thumbs/{tid}.jpg", "note": note}


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC, "index.html"), headers={"Cache-Control": "no-store"})


app.mount("/static", StaticFiles(directory=STATIC), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")))
