"""Power features: bulk creation, duplicates and translations, script rewrite and rebuild, vertical shorts, stock-footage browser,
captions download, global job list, title and idea lab, voice previews."""
import hashlib
import os
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, wait

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

from fda import catalog
from fda.agents import director
from fda.agents.common import clean_narration, latest_script, scenes as get_scenes
from fda.agents.visual import normalise_image
from fda.config import get_settings
from fda.database import models as m
from fda.database.session import get_db
from fda.orchestration import workflow
from fda.permissions import budget_manager as budget
from fda.providers import registry
from fda.providers.base import NotConfigured, ProviderError, download
from fda.services import assets
from fda.services.audit import audit
from fda.services.llm import LLM, external
from fda.storage.store import scratch_dir

from .deps import current_user, project_or_404
from .projects import _save_script, create_project, ser_project
from .serialize import asset as asset_view, row

router = APIRouter(tags=["features"])

LANG_NAME = {"en": "English", "hi": "Hindi (Devanagari script)", "hinglish": "Hinglish (conversational Hindi written in Latin letters with natural English words)"}


def _busy(db, p):
    return db.query(m.WorkflowRun).filter(m.WorkflowRun.project_id == p.id, m.WorkflowRun.status.in_(["pending", "running"])).first()


# ------------------------------------------------------------------ bulk creation
@router.post("/projects/bulk")
def bulk_create(body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    """Create many videos at once from a list of titles. Production runs in the background; renders take turns."""
    titles = [t.strip() for t in re.split(r"[\r\n]+", str(body.get("titles") or "")) if t.strip()][:50]
    if not titles:
        raise HTTPException(400, "Write at least one title, one per line")
    base = {k: body.get(k) for k in ("mode", "language", "target_minutes", "aspect", "fps", "style", "character_id", "preserve_narration") if body.get(k) is not None}
    if base.get("aspect"):
        w, h = catalog.RESOLUTIONS.get(base["aspect"], catalog.RESOLUTIONS["16:9"])[0]
        base.setdefault("width", w)
        base.setdefault("height", h)
    out = []
    for t in titles:
        p = create_project(dict(base, title=t[:300], brief=str(body.get("brief") or "")), db, u)
        proj = db.get(m.Project, uuid.UUID(p["id"]))
        run_id = None
        if body.get("start", True):
            run_id = str(director.start_production(db, proj, u.id).id)
        out.append({"id": p["id"], "title": t, "run_id": run_id})
    audit(db, "owner", "bulk_create", "", count=len(out))
    db.commit()
    return {"created": out}


# ------------------------------------------------------------------ duplicate & translate
def _copy_project(db, u, src, title=None, language=None, script_text=None):
    ps = db.query(m.ProjectSettings).filter_by(project_id=src.id).one()
    style = dict(ps.style or {})
    for k in ("avatar_video",):
        style.pop(k, None)
    if language and language != src.language and not style.get("character_id"):
        style["voice"] = catalog.DEFAULT_VOICES.get(language, style.get("voice"))
    p = m.Project(user_id=u.id, title=(title or src.title)[:300], brief=src.brief, mode=src.mode, language=language or src.language, preserve_narration=src.preserve_narration)
    db.add(p)
    db.flush()
    db.add(m.ProjectSettings(project_id=p.id, width=ps.width, height=ps.height, fps=ps.fps, target_minutes=ps.target_minutes, style=style))
    if script_text:
        _save_script(db, p, script_text, "Copied from '%s'" % src.title[:80])
    return p


@router.post("/projects/{pid}/duplicate")
def duplicate(pid: str, body: dict = Body(default={}), db=Depends(get_db), u=Depends(current_user)):
    src = project_or_404(db, pid, u)
    _, sv = latest_script(db, src.id)
    p = _copy_project(db, u, src, body.get("title") or (src.title + " (copy)"), None, sv.text if (sv and body.get("keep_script", True)) else None)
    if body.get("start"):
        director.start_production(db, p, u.id)
    db.commit()
    return ser_project(db, p)


@router.post("/projects/{pid}/translate")
def translate(pid: str, body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    """Make a version of the video in another language: the script is translated, then the new project is produced."""
    src = project_or_404(db, pid, u)
    lang = body.get("language")
    if lang not in catalog.LANGUAGES:
        raise HTTPException(400, "language must be one of %s" % ", ".join(catalog.LANGUAGES))
    _, sv = latest_script(db, src.id)
    if not sv:
        raise HTTPException(400, "This project has no script yet; produce it first")
    llm = LLM(db, src.id, "translate")
    try:
        text = clean_narration(llm.complete(
            "You translate YouTube narration for a voice-over. Keep every fact, the order and the storytelling rhythm. Write natural spoken %s, not a literal translation. "
            "Write numbers as words. Output only the translated narration." % LANG_NAME[lang],
            external(sv.text[:20000], "script"), max_tokens=min(12000, int(len(sv.text) / 2) + 1500), temperature=0.4))
        title = llm.complete("Translate this YouTube title into %s. Keep it under 70 characters and keep the curiosity. Output only the title." % LANG_NAME[lang],
                             external(src.title, "title"), max_tokens=120, temperature=0.4).strip().strip('"')[:300]
    except (ProviderError, budget.BudgetError) as e:
        raise HTTPException(502, str(e))
    p = _copy_project(db, u, src, title or src.title, lang, text)
    run = director.start_production(db, p, u.id) if body.get("start", True) else None
    db.commit()
    return {"project": ser_project(db, p), "run_id": str(run.id) if run else None}


# ------------------------------------------------------------------ script tools
@router.post("/projects/{pid}/script/rewrite")
def rewrite_script(pid: str, body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    p = project_or_404(db, pid, u)
    _, sv = latest_script(db, p.id)
    if not sv:
        raise HTTPException(400, "No script to rewrite yet")
    how = str(body.get("instruction") or "Make it more engaging").strip()[:800]
    try:
        text = clean_narration(LLM(db, p.id, "rewrite").complete(
            "You are an elite YouTube scriptwriter. Rewrite the narration following the owner's instruction. Keep facts correct, write for the ear, "
            "flowing spoken sentences, no headings or stage directions, no em dashes, numbers as words. Output only the narration.",
            "INSTRUCTION: %s\n\nSCRIPT:\n%s" % (external(how, "owner instruction"), external(sv.text[:20000], "script")),
            max_tokens=min(12000, int(len(sv.text) / 2) + 2000), temperature=0.7))
    except (ProviderError, budget.BudgetError) as e:
        raise HTTPException(502, str(e))
    if len(text.split()) < 10:
        raise HTTPException(502, "The writer returned an empty script; try again")
    _save_script(db, p, text, "Rewritten: " + how[:120])
    db.commit()
    return {"text": text, "words": len(text.split())}


@router.post("/projects/{pid}/rebuild")
def rebuild(pid: str, db=Depends(get_db), u=Depends(current_user)):
    """Re-voice the current script and rebuild storyboard, visuals, sound, edit, render, QC and the upload pack."""
    p = project_or_404(db, pid, u)
    if _busy(db, p):
        raise HTTPException(409, "A job is already running for this project")
    if db.query(m.Asset).filter_by(project_id=p.id, role="upload_original", kind="audio").first():
        raise HTTPException(400, "This project uses your uploaded narration, which is preserved. Edit scenes instead, or duplicate the project without the upload.")
    tasks = director.production_tasks()
    for t in tasks:
        if t["key"] in ("voiceover", "storyboard"):
            t["params"] = dict(t.get("params") or {}, redo=True)
    p.status = "producing"
    run = workflow.create_run(db, p.id, "rebuild", tasks, plan={"requested_by": "owner", "reason": "rebuild from script"})
    db.commit()
    workflow.dispatch(run.id)
    return row(run, ("state",))


# ------------------------------------------------------------------ vertical shorts
@router.post("/projects/{pid}/short")
def make_short(pid: str, body: dict = Body(default={}), db=Depends(get_db), u=Depends(current_user)):
    """Render a vertical 9:16 Short from the same edit (first N seconds), with big pop captions."""
    p = project_or_404(db, pid, u)
    if _busy(db, p):
        raise HTTPException(409, "A job is already running for this project")
    if not db.query(m.TimelineItem).filter_by(project_id=p.id).first():
        raise HTTPException(400, "Produce the video first")
    secs = max(5.0, min(180.0, float(body.get("seconds") or 59)))
    w, h = (1080, 1920) if body.get("quality", "1080") == "1080" else (720, 1280)
    run = workflow.create_run(db, p.id, "short", [{"key": "render", "agent": "render", "queue": "render", "timeout_s": 7200,
                                                    "params": {"kind": "short", "aspect": "9:16", "max_seconds": secs, "captions": body.get("captions") or "pop",
                                                               "export": {"width": w, "height": h, "fps": 30}}}])
    db.commit()
    workflow.dispatch(run.id)
    return row(run, ("state",))


# ------------------------------------------------------------------ captions
def _subs(db, p):
    return db.query(m.Subtitle).filter_by(project_id=p.id).order_by(m.Subtitle.start_s).all()


def _ts(t, sep):
    t = max(0.0, t)
    return "%02d:%02d:%02d%s%03d" % (t // 3600, t % 3600 // 60, t % 60, sep, int(round(t * 1000)) % 1000)


@router.get("/projects/{pid}/captions.srt")
def captions_srt(pid: str, db=Depends(get_db), u=Depends(current_user)):
    p = project_or_404(db, pid, u)
    body = "\n".join("%d\n%s --> %s\n%s\n" % (i + 1, _ts(s.start_s, ","), _ts(s.end_s + 0.05, ","), s.text) for i, s in enumerate(_subs(db, p)))
    return PlainTextResponse(body, media_type="application/x-subrip", headers={"Content-Disposition": 'attachment; filename="captions.srt"'})


@router.get("/projects/{pid}/captions.vtt")
def captions_vtt(pid: str, db=Depends(get_db), u=Depends(current_user)):
    p = project_or_404(db, pid, u)
    body = "WEBVTT\n\n" + "\n".join("%s --> %s\n%s\n" % (_ts(s.start_s, "."), _ts(s.end_s + 0.05, "."), s.text) for s in _subs(db, p))
    return PlainTextResponse(body, media_type="text/vtt", headers={"Content-Disposition": 'attachment; filename="captions.vtt"'})


@router.get("/projects/{pid}/script.txt")
def script_txt(pid: str, db=Depends(get_db), u=Depends(current_user)):
    p = project_or_404(db, pid, u)
    _, sv = latest_script(db, p.id)
    return PlainTextResponse(sv.text if sv else "", headers={"Content-Disposition": 'attachment; filename="script.txt"'})


# ------------------------------------------------------------------ stock footage browser
_found = {}
_found_lock = threading.Lock()
SEARCH_GROUPS = {"video": ("stock_video", "video"), "image": ("stock_image", "image"), "archive": ("archive_image", "image")}


_search_cache = {}


def _search_one(prov, q, k, portrait):
    try:
        return [c for c in prov.search(q, kind=k, n=12, portrait=portrait) if c.get("commercial_use") != "no"], None
    except Exception as e:  # one broken source never breaks the whole search
        return [], "%s: %s" % (prov.label, str(e)[:120])


@router.get("/media/search")
def media_search(q: str, kind: str = "video", portrait: int = 0, db=Depends(get_db), u=Depends(current_user)):
    """Search every connected free/licensed source at once (in parallel). Results are remembered for an hour so they can be used in a scene."""
    if kind not in SEARCH_GROUPS or not q.strip():
        raise HTTPException(400, "kind must be video, image or archive, and q is required")
    cap, k = SEARCH_GROUPS[kind]
    query = q.strip()[:120]
    provs = registry.for_cap(db, cap)
    ck = (kind, query.lower(), bool(portrait), tuple(p.name for p in provs))
    hit = _search_cache.get(ck)
    if hit and time.time() - hit[0] < 600:
        groups, errors = hit[1], list(hit[2])
    else:
        ex = ThreadPoolExecutor(max_workers=max(1, len(provs)))
        futs = [ex.submit(_search_one, p, query, k, bool(portrait)) for p in provs]
        wait(futs, timeout=25)
        ex.shutdown(wait=False, cancel_futures=True)
        groups, errors = [], []
        for prov, f in zip(provs, futs):
            if not f.done():
                errors.append("%s: took too long" % prov.label)
                continue
            found, err = f.result()
            groups.append(found)
            if err:
                errors.append(err)
        _search_cache[ck] = (time.time(), groups, errors)
        for key in [k_ for k_, v in list(_search_cache.items()) if time.time() - v[0] > 600]:
            _search_cache.pop(key, None)
    results, seen = [], set()
    for i in range(max([len(g) for g in groups] or [0])):  # interleave sources so the grid shows variety
        for g in groups:
            if i >= len(g):
                continue
            c = g[i]
            cid = hashlib.sha1(c["id"].encode()).hexdigest()[:16]
            if cid in seen:
                continue
            seen.add(cid)
            with _found_lock:
                _found[cid] = (time.time(), c)
            results.append({"key": cid, "kind": c["kind"], "thumb": (c.get("thumb") or "").replace("http://", "https://", 1) or None, "title": (c.get("title") or "")[:160], "provider": c["provider"],
                            "license": c.get("license"), "attribution": c.get("attribution"), "source_page": c.get("source_page"),
                            "width": c.get("width"), "height": c.get("height"), "duration": c.get("duration")})
    with _found_lock:
        for key in [k_ for k_, (t, _) in _found.items() if time.time() - t > 3600]:
            _found.pop(key, None)
    unconfigured = [p.label for p in registry.for_cap(db, cap, usable_only=False) if p.fields and not p.configured()]
    return {"results": results, "errors": errors, "add_keys_for_more": unconfigured}


@router.post("/scenes/{sid}/use-stock")
def use_stock(sid: str, body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    """Put a search result into a scene: download, record licence and source, swap the clip on the timeline."""
    sc = db.get(m.Scene, sid)
    if not sc:
        raise HTTPException(404, "Scene not found")
    p = project_or_404(db, sc.project_id, u)
    with _found_lock:
        hit = _found.get(str(body.get("key", "")))
    if not hit:
        raise HTTPException(400, "That search result expired; search again")
    c = hit[1]
    work = scratch_dir(p.id, "picked")
    is_video = c["kind"] == "video"
    raw = os.path.join(work, "%s%s" % (hashlib.sha1(c["id"].encode()).hexdigest()[:12], ".mp4" if is_video and ".webm" not in c["url"] else ".webm" if is_video else ".raw"))
    try:
        download(c["url"], raw, timeout=300, max_mb=300 if is_video else 40)
        path = raw if is_video else normalise_image(raw, raw[:-4] + ".jpg")
        a = assets.register(db, path, p.id, "scene", "scenes", os.path.basename(path), origin="stock", provider=c["provider"], source_url=c.get("source_page") or c["url"],
                            settings={"picked_by": "owner"}, license=c.get("license") or "unknown", attribution=c.get("attribution", ""),
                            commercial_use=c.get("commercial_use", "unknown"), terms_url=c.get("terms_url"), meta={"source_id": c["id"], "title": (c.get("title") or "")[:300]})
    except Exception as e:
        raise HTTPException(502, "Could not download that result: %s" % str(e)[:200])
    db.add(m.SceneVersion(scene_id=sc.id, version=sc.version or 1, plan=sc.plan or {}, asset_id=sc.asset_id, reason="owner picked stock"))
    sc.asset_id, sc.asset_status, sc.provider, sc.last_error = a.id, "ready", c["provider"], None
    sc.visual_type = "stock_video" if is_video else "stock_image"
    sc.plan = {k: v for k, v in (sc.plan or {}).items() if k != "substitution"}
    sc.version = (sc.version or 1) + 1
    it = db.query(m.TimelineItem).filter_by(scene_id=sc.id, track="V1").first()
    if it:
        props = {k: v for k, v in (it.props or {}).items() if k not in ("missing", "mg", "lipsync")}
        if props.get("motion") == "static":
            props["motion"] = "push_in"
        it.asset_id, it.kind, it.in_s = a.id, "video" if is_video else "image", 0.0
        it.props = dict(props, user_edited=True)
    db.commit()
    return {"scene": row(sc), "asset": asset_view(db, a)}


# ------------------------------------------------------------------ jobs across all projects
@router.get("/runs")
def all_runs(limit: int = 60, db=Depends(get_db), u=Depends(current_user)):
    titles = {p.id: p.title for p in db.query(m.Project).filter_by(user_id=u.id).all()}
    out = []
    for r in db.query(m.WorkflowRun).filter(m.WorkflowRun.project_id.in_(list(titles) or [uuid.uuid4()])).order_by(m.WorkflowRun.created_at.desc()).limit(max(1, min(200, limit))).all():
        tasks = db.query(m.WorkflowTask).filter_by(run_id=r.id).all()
        done = sum(1 for t in tasks if t.status in ("succeeded", "skipped"))
        prog = (done + sum(t.progress for t in tasks if t.status == "running")) / max(1, len(tasks))
        cur = next((t for t in tasks if t.status == "running"), None)
        out.append(dict(row(r, ("state", "plan")), project_title=titles.get(r.project_id), progress=round(prog, 3), tasks=len(tasks), done=done,
                        current=("%s: %s" % (cur.key, cur.message)) if cur else ""))
    return out


# ------------------------------------------------------------------ title & idea lab
class TitleIdea(BaseModel):
    title: str
    angle: str = ""
    score: int = 70


class TitleSet(BaseModel):
    titles: list[TitleIdea]


class VideoIdea(BaseModel):
    title: str
    why: str
    hook: str
    format: str
    thumbnail_text: str = ""


class IdeaSet(BaseModel):
    ideas: list[VideoIdea]


FORMULAS = ["Most People Are [Doing X] Wrong", "Stop [Doing X]! Do This Instead", "What Actually Happens When You [Action]", "The $[Price] [Thing] That [Result]",
            "[Number] Things [Group] Never [Do]", "Why Your [Thing] [Problem] — Do This Instead", "The Untold Timeline of [Event]", "What If [Impossible Scenario]?",
            "They Found [Thing] in [Place]", "How [Small Thing] Destroyed [Big Thing]", "I Tried [X] for [Time] — Here's What Happened", "The Real Reason [Surprising Fact]"]


@router.post("/tools/titles")
def title_lab(body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    topic = str(body.get("topic") or "").strip()[:1500]
    if not topic:
        raise HTTPException(400, "Write a topic")
    lang = body.get("language") if body.get("language") in catalog.LANGUAGES else "en"
    try:
        out = LLM(db, None, "titles").structured(
            "You are a YouTube packaging specialist. Titles carry one honest curiosity gap the video can deliver, under 70 characters, at most one ALL-CAPS word, no emojis, no brand names.",
            "Topic: %s\nStyle: %s\nLanguage: %s\nProven formulas to adapt (never copy an existing title): %s\nWrite %d titles, each with the curiosity angle in 6 words and a 1-100 click score." % (
                external(topic, "topic"), body.get("mode") or "documentary", LANG_NAME[lang], " | ".join(FORMULAS), max(3, min(20, int(body.get("n") or 10)))),
            TitleSet, max_tokens=2000, temperature=0.95)
    except (ProviderError, budget.BudgetError) as e:
        raise HTTPException(502, str(e))
    return {"titles": sorted([t.model_dump() for t in out.titles], key=lambda t: -t["score"])}


@router.post("/tools/ideas")
def idea_lab(body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    niche = str(body.get("niche") or "").strip()[:1200]
    if not niche:
        raise HTTPException(400, "Describe your channel or niche")
    try:
        out = LLM(db, None, "ideas").structured(
            "You are a YouTube growth strategist. Suggest video ideas with real breakout potential for this channel: a problem or curiosity the audience has now, a surprising answer, "
            "a clear 'nobody told you' angle, a visual that works as a thumbnail. Never medical, legal or investment advice. Never copy an existing video.",
            "Channel / niche: %s\nToday: %s\nGive 10 ideas ranked best first; format is one of Countdown, Walkthrough, Myth-Buster, Story-Led, Documentary, Explainer." % (
                external(niche, "niche"), time.strftime("%B %d, %Y")), IdeaSet, max_tokens=3000, temperature=0.9)
    except (ProviderError, budget.BudgetError) as e:
        raise HTTPException(502, str(e))
    return {"ideas": [i.model_dump() for i in out.ideas]}


# ------------------------------------------------------------------ voice preview
SAMPLES = {"en": "At nine in the morning, nobody on the dock knew what was coming. By noon, everything had changed.",
           "hi": "उस सुबह किसी को अंदाज़ा नहीं था कि आगे क्या होने वाला है। दोपहर तक सब कुछ बदल चुका था।",
           "hinglish": "Us subah kisi ko pata nahi tha ki aage kya hone wala hai. Dopahar tak sab kuch badal chuka tha."}


@router.get("/voices/preview")
def voice_preview(voice: str, provider: str = "edge_tts", lang: str = "en", rate: int = 0, pitch: int = 0, db=Depends(get_db), u=Depends(current_user)):
    if not re.fullmatch(r"[\w.-]{2,80}", voice or ""):
        raise HTTPException(400, "Invalid voice id")
    try:
        prov = registry.get(db, provider)
    except KeyError:
        raise HTTPException(404, "Unknown provider")
    if "tts" not in prov.caps:
        raise HTTPException(400, "Not a voice provider")
    d = os.path.join(get_settings().storage_dir, ".cache", "voices")
    os.makedirs(d, exist_ok=True)
    rate, pitch = max(-50, min(50, int(rate))), max(-50, min(50, int(pitch)))
    path = os.path.join(d, "%s_%s_%s_%d_%d.mp3" % (provider, voice, lang if lang in SAMPLES else "en", rate, pitch))
    if not os.path.exists(path):
        try:
            if prov.paid:
                rec = budget.reserve(db, prov, "voice preview", len(SAMPLES.get(lang, SAMPLES["en"])), "characters")
            prov.speak(SAMPLES.get(lang, SAMPLES["en"]), voice, path, rate, pitch)
            if prov.paid:
                budget.commit(db, rec)
                db.commit()
        except (ProviderError, NotConfigured, budget.BudgetError) as e:
            raise HTTPException(502, str(e))
    return FileResponse(path, media_type="audio/mpeg")


# ------------------------------------------------------------------ studio totals
@router.get("/stats")
def stats(db=Depends(get_db), u=Depends(current_user)):
    pids = [p.id for p in db.query(m.Project).filter_by(user_id=u.id, deleted_at=None).all()]
    renders = db.query(m.Render).filter(m.Render.project_id.in_(pids or [uuid.uuid4()]), m.Render.status == "succeeded").all()
    secs = sum(float((r.probe or {}).get("duration") or 0) for r in renders if r.kind in ("final", "short"))
    return {"projects": len(pids), "renders": len(renders), "shorts": sum(1 for r in renders if r.kind == "short"), "minutes_rendered": round(secs / 60, 1),
            "characters": db.query(m.Character).filter_by(user_id=u.id).count(),
            "scenes": db.query(m.Scene).filter(m.Scene.project_id.in_(pids or [uuid.uuid4()])).count()}
