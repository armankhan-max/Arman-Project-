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
SECRET_KEYS = ("elevenlabs_key", "youtube_key", "anthropic_key", "openai_key", "pollinations_key", "pexels_key", "pixabay_key", "did_key")


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
    return {"voices": tts.voices(store.get_settings()), "ages": tts.AGES,
            "emotions": {k: v["label"] for k, v in tts.EMOTIONS.items() if v}}


@app.post("/api/voice-preview")
async def voice_preview(request: Request):
    b = await request.json()
    out = os.path.join(store.DATA, "preview.mp3")
    try:
        age = tts.AGES.get(b.get("age") or "", {})
        rate = int(b.get("rate", 0)) + (age.get("rate", 0) if not b["voice"].startswith("el:") else 0)
        text = (b.get("text") or "Have you ever wondered why some stories stay with you? Here is the truth. Nobody saw it coming.")[:300]
        if b.get("emotion") and b["emotion"] != "off" and not b["voice"].startswith("el:"):
            out = out.replace(".mp3", ".wav")
            await run_in_threadpool(tts.humanize_synth, text, b["voice"], out, rate, age.get("pitch", 0), b["emotion"])
        else:
            await run_in_threadpool(tts.synth, text, b["voice"], out, rate, age.get("pitch", 0))
    except Exception as e:
        raise HTTPException(502, str(e))
    return FileResponse(out, media_type="audio/wav" if out.endswith(".wav") else "audio/mpeg", headers={"Cache-Control": "no-store"})


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
    fields = ("style", "language", "voice", "rate", "aspect", "source", "captions", "music", "script", "notes", "persona", "show_title", "sfx", "style_prompt", "age", "graphics",
              "thumb_ref", "thumb_text", "profile_id", "emotion")
    p = store.new_project({"title": title, "minutes": max(0.3, min(60, float(b.get("minutes") or 1))),
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
    for k in ("title", "style", "voice", "rate", "aspect", "source", "captions", "music", "show_title", "meta", "sfx", "thumb", "age"):
        if k in b:
            p[k] = b[k]
    if isinstance(b.get("look"), dict):
        p["look"] = {**(p.get("look") or {}), **b["look"]}
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
            if isinstance(s.get("assets"), list):  # shot list edited in the timeline editor
                root = os.path.realpath(store.pdir(pid))
                keep = []
                for x in s["assets"]:
                    full = os.path.realpath(os.path.join(root, str(x.get("path", ""))))
                    if not full.startswith(root + os.sep) or not os.path.isfile(full):
                        continue
                    prev = next((y for y in o.get("assets", []) if y.get("path") == x["path"]), {})
                    item = {**prev, "path": x["path"], "type": x.get("type") or prev.get("type", "image"),
                            "source": x.get("source") or prev.get("source", "your pick"), "credit": x.get("credit", prev.get("credit", ""))}
                    for f in ("move", "filter"):
                        item[f] = str(x.get(f) or "")[:30]
                    item["speed"] = max(0.25, min(2.0, float(x.get("speed") or 1)))
                    item["weight"] = max(0.1, min(10.0, float(x.get("weight") or 1)))
                    keep.append(item)
                if keep:
                    n["assets"], n["locked"] = keep, True
                n["trans"] = str(s.get("trans") or "")[:20]
            elif not o.get("custom") and (n["queries"] != o.get("queries") or s.get("refresh")):
                n["assets"], n["locked"] = [], False
            if n.get("graphic", "") != o.get("graphic", ""):  # new or removed motion graphic: rebuild this scene's visuals
                n["assets"], n["locked"], n["custom"] = [], False, False
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


@app.get("/api/editor-options")
def editor_options():
    import look as looks
    return {"moves": looks.MOVES, "transitions": looks.TRANSITIONS, "filters": list(looks.FILTERS), "fonts": list(looks.FONTS),
            "caption_styles": looks.CAPTION_STYLES, "title_styles": looks.TITLE_STYLES, "palettes": looks.PALETTES,
            "graphics": __import__("graphics").TYPES, "atmospheres": __import__("atmos").KINDS}


@app.post("/api/projects/{pid}/candidates")
async def visual_candidates(pid: str, request: Request):
    p = _project(pid)
    b = await request.json()
    q = (b.get("query") or "").strip()
    if not q:
        raise HTTPException(400, "Type what you want to see.")
    items, errors = await run_in_threadpool(media.candidates, q, store.get_settings(), b.get("kind", "all"), p.get("aspect") == "9:16")
    return {"items": items[:40], "errors": errors}


@app.post("/api/projects/{pid}/pick")
async def visual_pick(pid: str, request: Request):
    _project(pid)
    b = await request.json()
    vdir = os.path.join(store.pdir(pid), "visuals")
    os.makedirs(vdir, exist_ok=True)
    try:
        if b.get("prompt"):
            import random as _r
            w, h = (1344, 768) if b.get("aspect", "16:9") != "9:16" else (768, 1344)
            path = os.path.join(vdir, f"ai_{secrets.token_hex(5)}.jpg")
            await run_in_threadpool(media.ai_image, b["prompt"] + ", no text, no watermark", path, w, h, _r.randint(1, 99999))
            typ, src, credit = "image", "AI image", "AI generated (Pollinations)"
        else:
            typ = "video" if b.get("type") == "video" else "image"
            path = await run_in_threadpool(media.download_pick, b["url"], typ, vdir)
            src, credit = b.get("kind") or "stock", b.get("credit", "")
    except Exception as e:
        raise HTTPException(502, f"Could not get that visual: {e}")
    return {"path": os.path.relpath(path, store.pdir(pid)), "type": typ, "source": src, "credit": credit}


@app.post("/api/projects/{pid}/upload")
async def visual_upload(pid: str, file: UploadFile = File(...)):
    _project(pid)
    os.makedirs(os.path.join(store.pdir(pid), "visuals"), exist_ok=True)
    name = _save_upload(file, pid, f"visuals/up_{secrets.token_hex(4)}")
    is_video = name.lower().endswith((".mp4", ".mov", ".webm", ".mkv", ".m4v"))
    return {"path": name, "type": "video" if is_video else "image", "source": "your upload", "credit": ""}


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


@app.get("/api/thumb-refs")
def thumb_refs(topic: str):
    import thumbref
    try:
        return {"items": thumbref.outliers(topic, store.get_settings().get("youtube_key"))}
    except Exception as e:
        return {"items": [], "error": str(e)}


@app.post("/api/thumb-ref-preview")
async def thumb_ref_preview(request: Request):
    import thumbref
    url = (await request.json()).get("url", "")
    name = secrets.token_hex(5) + ".jpg"
    try:
        await run_in_threadpool(thumbref.fetch_reference, url, os.path.join(store.THUMBS, name))
    except Exception as e:
        raise HTTPException(400, str(e))
    return {"url": f"/media/_thumbs/{name}"}


# ---------------- brand profiles ----------------
@app.get("/api/profiles")
def list_profiles():
    return [dict(store.PROFILE_DEFAULTS, **x) for x in store.get_profiles()]


@app.post("/api/profiles")
async def save_profile(request: Request):
    b = await request.json()
    b = {k: v for k, v in b.items() if k in store.PROFILE_DEFAULTS or k == "id"}
    if not (b.get("name") or "").strip() and not b.get("id"):
        raise HTTPException(400, "Give the profile a name.")
    return store.upsert_profile(b)


@app.delete("/api/profiles/{pid}")
def delete_profile(pid: str):
    store.save_profiles([x for x in store.get_profiles() if x.get("id") != pid])
    return {"ok": True}


@app.post("/api/profiles/{pid}/reference")
async def profile_reference(pid: str, file: UploadFile = File(None), url: str = Form(""), transcript: str = Form("")):
    """Study a reference video (file) and/or its transcript and save the editing + script style to the profile."""
    import refstyle
    prof = store.get_profile(pid)
    if not prof:
        raise HTTPException(404, "Profile not found.")
    cfg = store.get_settings()
    video = None
    meta = {}
    if file is not None and file.filename:
        path = os.path.join(store.DATA, f"ref_{pid}{os.path.splitext(file.filename)[1][:6] or '.mp4'}")
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        video = await run_in_threadpool(refstyle.analyse_video, path)
    if url:
        import thumbref
        vid = thumbref.video_id(url)
        meta["url"] = url
        if vid and cfg.get("youtube_key"):
            try:
                import requests as _rq
                j = _rq.get("https://www.googleapis.com/youtube/v3/videos", timeout=30,
                            params={"part": "snippet,contentDetails", "id": vid, "key": cfg["youtube_key"]}).json()
                sn = j["items"][0]["snippet"]
                meta.update(title=sn.get("title"), channel=sn.get("channelTitle"), description=(sn.get("description") or "")[:600])
            except Exception:
                pass
        if vid:
            meta["thumb"] = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    stats, style = (None, None)
    if transcript.strip():
        stats, style = await run_in_threadpool(refstyle.analyse_script, transcript, cfg, (video or {}).get("duration"))
    if not (video or stats or meta):
        raise HTTPException(400, "Upload the reference video, paste its transcript, or both.")
    ref = {"video": video, "script_stats": stats, "script_style": style, "meta": meta,
           "settings": refstyle.to_settings(video, stats, style), "analysed": time.time()}
    return store.upsert_profile({"id": pid, "reference": ref})


# ---------------- prompt -> plan ("quote statement") ----------------
@app.post("/api/plan")
async def plan(request: Request):
    """Read a free-text prompt (up to 10,000 characters) and work out the video settings."""
    b = await request.json()
    prompt = (b.get("prompt") or "").strip()[:10000]
    if not prompt:
        raise HTTPException(400, "Describe the video you want.")
    cfg = store.get_settings()
    prof = store.get_profile(b.get("profile_id") or "") or dict(store.PROFILE_DEFAULTS)
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(?:\d+\s*)?(min|minute|hour|hr)", prompt, re.I)
    minutes = float(m.group(1)) * (60 if m and m.group(2).lower().startswith("h") else 1) if m else 8
    first = re.sub(r"^(title|video prompt)\s*[:\-]\s*", "", prompt.splitlines()[0], flags=re.I).strip()
    out = {"title": first[:100], "minutes": max(0.5, min(60, minutes)), "format": store.THEMES.get(prof["theme"], "documentary"),
           "language": prof["language"], "notes": prompt if len(prompt) > len(first) + 20 else "", "tone": ""}
    if llm.provider(cfg) != "none":
        try:
            o = await run_in_threadpool(lambda: llm._json(llm.chat(cfg, "You turn video requests into production settings. Return ONLY one JSON object.",
                f"Formats available: {', '.join(cfg['styles'])}.\nDefault format from the brand profile: {out['format']}.\n"
                f"Request:\n{prompt[:8000]}\n\nReturn {{\"title\": \"best YouTube title under 70 characters (keep the user's title if they gave one)\", "
                '"minutes": number, "format": one of the formats, "language": "...", "tone": "short description", '
                '"notes": "the user\'s scene breakdown, facts and instructions, kept in full"}', 6000)))
            for k in ("title", "format", "language", "tone", "notes"):
                if o.get(k):
                    out[k] = str(o[k])
            if o.get("minutes"):
                out["minutes"] = max(0.5, min(60, float(o["minutes"])))
            if out["format"] not in cfg["styles"]:
                out["format"] = store.THEMES.get(prof["theme"], "documentary")
        except Exception:
            pass
    wpm = cfg.get("words_per_minute", 150)
    out["estimate"] = {"words": int(out["minutes"] * wpm), "scenes": int(out["minutes"] * wpm / 32),
                       "render_minutes": round(2 + out["minutes"] * (1.6 if prof.get("quality") != "draft" else 0.9))}
    return out


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC, "index.html"), headers={"Cache-Control": "no-store"})


app.mount("/static", StaticFiles(directory=STATIC), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")))
