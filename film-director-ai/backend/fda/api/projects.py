import io
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from PIL import Image

from fda import catalog
from fda.agents import director
from fda.agents.common import latest_script, scenes as get_scenes, style, transcript
from fda.agents.editor import save_version
from fda.config import get_settings
from fda.database import models as m
from fda.database.session import get_db
from fda.knowledge.ingestion import extract_text, ingest
from fda.orchestration import workflow
from fda.services import assets, media
from fda.services.audit import audit
from fda.storage.store import store

from .deps import current_user, project_or_404
from .serialize import asset as asset_view, row

router = APIRouter(tags=["projects"])
PURPOSES = {"voiceover": ("audio",), "script": ("document",), "reference": ("image", "video"), "footage": ("video", "image"), "document": ("document",),
            "avatar": ("image",)}


def ser_project(db, p):
    d = row(p)
    ps = db.query(m.ProjectSettings).filter_by(project_id=p.id).one_or_none()
    d["settings"] = row(ps)
    if ps:
        d["settings"]["style"] = style(db, p)[1]
    return d


@router.get("/projects")
def list_projects(db=Depends(get_db), u=Depends(current_user)):
    out = []
    for p in db.query(m.Project).filter_by(user_id=u.id, deleted_at=None).order_by(m.Project.updated_at.desc()).all():
        d = row(p)
        r = db.query(m.Render).filter_by(project_id=p.id, status="succeeded", kind="final").order_by(m.Render.created_at.desc()).first()
        d["last_render"] = row(r)
        run = db.query(m.WorkflowRun).filter_by(project_id=p.id).order_by(m.WorkflowRun.created_at.desc()).first()
        d["last_run"] = row(run, ("state", "plan"))
        d["scenes"] = db.query(m.Scene).filter_by(project_id=p.id).count()
        out.append(d)
    return out


@router.post("/projects")
def create_project(body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    title = str(body.get("title") or "").strip()[:300] or "Untitled"
    mode = body.get("mode") if body.get("mode") in catalog.MODES else "documentary"
    lang = body.get("language") if body.get("language") in catalog.LANGUAGES else "en"
    p = m.Project(user_id=u.id, title=title, brief=str(body.get("brief") or "")[:20000], mode=mode, language=lang, preserve_narration=bool(body.get("preserve_narration", True)))
    db.add(p)
    db.flush()
    st = catalog.default_style(mode, lang)
    st.update({k: v for k, v in (body.get("style") or {}).items() if k in st or k in ("persona", "research", "ambience", "tts_provider", "avatar_pip")})
    if body.get("character_id"):
        from fda.services.characters import apply_to_style
        ch = db.get(m.Character, body["character_id"])
        if ch and ch.user_id == u.id:
            st = apply_to_style(ch, st)
    aspect = body.get("aspect") or st["aspect"]
    w, h = catalog.RESOLUTIONS.get(aspect, catalog.RESOLUTIONS["16:9"])[0]
    st["aspect"] = aspect
    db.add(m.ProjectSettings(project_id=p.id, width=int(body.get("width") or w), height=int(body.get("height") or h), fps=int(body.get("fps") or 30),
                             target_minutes=max(0.25, min(120.0, float(body.get("target_minutes") or 3))), style=st))
    if body.get("script"):
        _save_script(db, p, body["script"], "Pasted by owner")
    audit(db, "owner", "project_create", p.id)
    db.commit()
    return ser_project(db, p)


def _save_script(db, p, text, note):
    sc = db.query(m.Script).filter_by(project_id=p.id, origin="user").first()
    if not sc:
        sc = m.Script(project_id=p.id, origin="user", current_version=0)
        db.add(sc)
        db.flush()
    sc.current_version += 1
    db.add(m.ScriptVersion(script_id=sc.id, version=sc.current_version, text=str(text)[:200000], note=note))
    ingest(db, str(text), "Script: " + p.title, "script", p.id, "user_provided")


@router.get("/projects/{pid}")
def get_project(pid: str, db=Depends(get_db), u=Depends(current_user)):
    p = project_or_404(db, pid, u)
    d = ser_project(db, p)
    sc, sv = latest_script(db, p.id)
    d["script"] = {"origin": sc.origin, "version": sv.version, "text": sv.text, "outline": sv.outline, "versions": db.query(m.ScriptVersion).filter_by(script_id=sc.id).count()} if sv else None
    vo, tr = transcript(db, p.id)
    d["voiceover"] = row(vo) if vo else None
    if vo:
        d["voiceover"]["original"] = asset_view(db, db.get(m.Asset, vo.original_asset_id)) if vo.original_asset_id else None
        d["voiceover"]["processed"] = asset_view(db, db.get(m.Asset, vo.processed_asset_id)) if vo.processed_asset_id else None
    d["transcript"] = {"text": tr.text, "language": tr.language, "word_level": tr.word_level, "provider": tr.provider, "words": len(tr.words or [])} if tr else None
    sb = db.query(m.Storyboard).filter_by(project_id=p.id).order_by(m.Storyboard.version.desc()).first()
    d["storyboard"] = row(sb) if sb else None
    d["scenes"] = [dict(row(s), asset=asset_view(db, db.get(m.Asset, s.asset_id)) if s.asset_id else None) for s in get_scenes(db, p.id)]
    d["uploads"] = [asset_view(db, a) for a in db.query(m.Asset).filter_by(project_id=p.id, role="upload_original").all()]
    d["renders"] = [dict(row(r), asset=asset_view(db, db.get(m.Asset, r.asset_id)) if r.asset_id else None)
                    for r in db.query(m.Render).filter_by(project_id=p.id).order_by(m.Render.created_at.desc()).limit(20).all()]
    d["versions"] = [{"version": v.version, "reason": v.reason, "created_at": v.created_at.isoformat()} for v in
                     db.query(m.ProjectVersion).filter_by(project_id=p.id).order_by(m.ProjectVersion.version.desc()).all()]
    d["runs"] = [row(r, ("state", "plan")) for r in db.query(m.WorkflowRun).filter_by(project_id=p.id).order_by(m.WorkflowRun.created_at.desc()).limit(15).all()]
    q = db.query(m.QualityReport).filter_by(project_id=p.id).order_by(m.QualityReport.created_at.desc()).first()
    d["quality"] = row(q)
    pk = db.query(m.ResearchReport).filter_by(project_id=p.id, kind="upload_pack").order_by(m.ResearchReport.created_at.desc()).first()
    d["pack"] = dict(pk.data, thumbnails=[dict(t, url="/api/v1/assets/%s/file" % t["asset_id"]) for t in pk.data.get("thumbnails", [])]) if pk else None
    d["research"] = [dict(row(r), sources=[row(s) for s in db.query(m.ResearchSource).filter_by(report_id=r.id).all()])
                     for r in db.query(m.ResearchReport).filter(m.ResearchReport.project_id == p.id, m.ResearchReport.kind != "upload_pack").order_by(m.ResearchReport.created_at.desc()).limit(5).all()]
    return d


@router.patch("/projects/{pid}")
def patch_project(pid: str, body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    p = project_or_404(db, pid, u)
    for k in ("title", "brief"):
        if k in body:
            setattr(p, k, str(body[k])[:20000 if k == "brief" else 300])
    if body.get("mode") in catalog.MODES:
        p.mode = body["mode"]
    if body.get("language") in catalog.LANGUAGES:
        p.language = body["language"]
    if "preserve_narration" in body:
        p.preserve_narration = bool(body["preserve_narration"])
    ps = db.query(m.ProjectSettings).filter_by(project_id=p.id).one()
    for k in ("width", "height", "fps"):
        if k in body:
            setattr(ps, k, int(body[k]))
    if "target_minutes" in body:
        ps.target_minutes = max(0.25, min(120.0, float(body["target_minutes"])))
    if isinstance(body.get("style"), dict):
        ps.style = {**(ps.style or {}), **body["style"]}
    db.commit()
    return ser_project(db, p)


@router.delete("/projects/{pid}")
def delete_project(pid: str, body: dict = Body(default={}), db=Depends(get_db), u=Depends(current_user)):
    p = project_or_404(db, pid, u)
    if body.get("confirm") != p.title:
        raise HTTPException(400, "Type the exact project title to confirm deletion")
    for r in db.query(m.WorkflowRun).filter(m.WorkflowRun.project_id == p.id, m.WorkflowRun.status.in_(["pending", "running"])).all():
        r.cancel_requested = True
    p.deleted_at = datetime.now(timezone.utc)
    audit(db, "owner", "project_delete", p.id, title=p.title)
    db.commit()
    return {"ok": True, "note": "Project hidden; files are kept until storage cleanup runs"}


@router.post("/projects/{pid}/uploads")
async def upload(pid: str, purpose: str = Form("reference"), file: UploadFile = File(...), db=Depends(get_db), u=Depends(current_user)):
    p = project_or_404(db, pid, u)
    if purpose not in PURPOSES:
        raise HTTPException(400, "purpose must be one of %s" % ", ".join(PURPOSES))
    kind = assets.kind_of(file.filename or "")
    if kind not in PURPOSES[purpose]:
        raise HTTPException(400, "A %s upload must be %s; got %s" % (purpose, "/".join(PURPOSES[purpose]), kind or "an unsupported type"))
    s = get_settings()
    tmpd = tempfile.mkdtemp(prefix="fda_up_")
    tmp = os.path.join(tmpd, "upload" + os.path.splitext(file.filename)[1].lower())
    size = 0
    with open(tmp, "wb") as f:
        while True:
            chunk = await file.read(1 << 20)
            if not chunk:
                break
            size += len(chunk)
            if size > s.max_upload_mb << 20:
                shutil.rmtree(tmpd, ignore_errors=True)
                raise HTTPException(413, "File exceeds %d MB" % s.max_upload_mb)
            f.write(chunk)
    try:
        if kind in ("audio", "video"):
            info = media.probe(tmp)
            if kind == "audio" and not info.get("audio"):
                raise media.MediaError("no audio stream")
            if kind == "video" and not info.get("video"):
                raise media.MediaError("no video stream")
        elif kind == "image":
            with Image.open(tmp) as im:
                im.verify()
        text = extract_text(tmp) if kind == "document" else None
    except Exception as e:
        shutil.rmtree(tmpd, ignore_errors=True)
        raise HTTPException(400, "The file could not be read (corrupted or wrong format): %s" % str(e)[:200])
    a = assets.register(db, tmp, p.id, "upload_original", "uploads", file.filename, origin="upload", license="Owner upload", commercial_use="unknown", meta={"purpose": purpose}, move=True)
    shutil.rmtree(tmpd, ignore_errors=True)
    if purpose == "script" and text:
        _save_script(db, p, text, "Uploaded file " + file.filename)
    elif purpose == "document" and text:
        ingest(db, text, file.filename, "upload", p.id, "user_provided", meta={"asset_id": str(a.id)})
    elif purpose == "avatar":
        ps = db.query(m.ProjectSettings).filter_by(project_id=p.id).one()
        ps.style = {**(ps.style or {}), "avatar_image_asset": str(a.id)}
    audit(db, "owner", "upload", a.id, purpose=purpose, size=size)
    db.commit()
    return asset_view(db, a)


@router.put("/projects/{pid}/script")
def put_script(pid: str, body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    p = project_or_404(db, pid, u)
    _save_script(db, p, str(body.get("text", "")), body.get("note") or "Edited by owner")
    db.commit()
    return {"ok": True}


@router.post("/projects/{pid}/produce")
def produce(pid: str, db=Depends(get_db), u=Depends(current_user)):
    p = project_or_404(db, pid, u)
    run = director.start_production(db, p, u.id)
    return row(run, ("state",))


@router.post("/projects/{pid}/apply")
def apply_changes(pid: str, body: dict = Body(default={}), db=Depends(get_db), u=Depends(current_user)):
    """Rebuild timeline (and remix if asked) from manual edits, then render + QC."""
    p = project_or_404(db, pid, u)
    if db.query(m.WorkflowRun).filter(m.WorkflowRun.project_id == p.id, m.WorkflowRun.status.in_(["pending", "running"])).first():
        raise HTTPException(409, "A job is already running for this project")
    tasks = []
    if body.get("remix"):
        tasks.append({"key": "audio", "agent": "audio", "queue": "audio"})
    if body.get("rebuild", True):
        tasks.append({"key": "edit", "agent": "editor", "depends_on": ["audio"] if body.get("remix") else [],
                      "params": {"reason": body.get("reason") or "Manual edits applied", "resync_subtitles": bool(body.get("resync_subtitles"))}})
    exp = {k: body[k] for k in ("width", "height", "fps", "crf") if body.get(k)}
    tasks += [{"key": "render", "agent": "render", "queue": "render", "depends_on": ["edit"] if body.get("rebuild", True) else (["audio"] if body.get("remix") else []),
               "params": {"kind": body.get("kind", "final"), "export": exp}, "timeout_s": 14400},
              {"key": "qc", "agent": "qc", "queue": "qc", "depends_on": ["render"], "params": {"skip_creative": True}},
              {"key": "finalize", "agent": "finalize", "depends_on": ["*qc"]}]
    p.status = "producing"
    run = workflow.create_run(db, p.id, "render", tasks)
    db.commit()
    workflow.dispatch(run.id)
    return row(run, ("state",))


@router.post("/projects/{pid}/pack")
def make_pack(pid: str, db=Depends(get_db), u=Depends(current_user)):
    p = project_or_404(db, pid, u)
    run = workflow.create_run(db, p.id, "pack", [{"key": "pack", "agent": "pack", "max_attempts": 1}])
    db.commit()
    workflow.dispatch(run.id)
    return row(run, ("state",))


# ------------------------------------------------------------------ scenes
@router.patch("/scenes/{sid}")
def patch_scene(sid: str, body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    sc = db.get(m.Scene, sid)
    if not sc:
        raise HTTPException(404, "Scene not found")
    project_or_404(db, sc.project_id, u)
    if body.get("visual_type"):
        sc.visual_type = body["visual_type"]
    if isinstance(body.get("plan"), dict):
        sc.plan = {**(sc.plan or {}), **body["plan"]}
    if body.get("user_asset_id"):
        sc.visual_type = "user"
        sc.plan = {**(sc.plan or {}), "user_asset_id": body["user_asset_id"]}
    db.commit()
    return row(sc)


@router.post("/scenes/{sid}/regenerate")
def regenerate_scene(sid: str, db=Depends(get_db), u=Depends(current_user)):
    sc = db.get(m.Scene, sid)
    if not sc:
        raise HTTPException(404, "Scene not found")
    p = project_or_404(db, sc.project_id, u)
    plan = director.EditPlan(understood="Regenerate scene %d" % sc.idx, ops=[director.EditOp(op="regenerate_scene", scenes=[sc.idx])])
    run, _ = director.start_edit(db, p, "Regenerate scene %d" % sc.idx, plan)
    return row(run, ("state",))


# ------------------------------------------------------------------ timeline
@router.get("/projects/{pid}/timeline")
def get_timeline(pid: str, db=Depends(get_db), u=Depends(current_user)):
    p = project_or_404(db, pid, u)
    items = db.query(m.TimelineItem).filter_by(project_id=p.id).order_by(m.TimelineItem.track, m.TimelineItem.start_s).all()
    scs = {s.id: s.idx for s in get_scenes(db, p.id)}
    out = []
    for it in items:
        d = row(it)
        d["scene_idx"] = scs.get(it.scene_id)
        a = db.get(m.Asset, it.asset_id) if it.asset_id else None
        d["asset"] = {"id": str(a.id), "kind": a.kind, "url": "/api/v1/assets/%s/file" % a.id, "duration_s": a.duration_s, "filename": a.filename} if a else None
        out.append(d)
    audio = []
    for t in db.query(m.AudioTrack).filter_by(project_id=p.id).all():
        d = row(t)
        a = db.get(m.Asset, t.asset_id) if t.asset_id else None
        d["url"] = "/api/v1/assets/%s/file" % a.id if a else None
        d["duration_s"] = a.duration_s if a else None
        audio.append(d)
    subs = [row(s) for s in db.query(m.Subtitle).filter_by(project_id=p.id).order_by(m.Subtitle.idx).all()]
    dur = max([i["start_s"] + i["duration_s"] for i in out] + [0])
    return {"items": out, "audio": audio, "subtitles": subs, "duration": dur, "version": p.current_version}


EDITABLE = {"motion", "filter", "transition", "tdur", "speed", "focus", "scale", "x", "y", "opacity", "crop", "label", "mg", "text", "size", "color", "anim", "font", "type", "align"}


@router.patch("/timeline/{iid}")
def patch_item(iid: str, body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    it = db.get(m.TimelineItem, iid)
    if not it:
        raise HTTPException(404, "Clip not found")
    project_or_404(db, it.project_id, u)
    props = dict(it.props or {})
    for k, v in (body.get("props") or {}).items():
        if k in EDITABLE:
            props[k] = v
    props["user_edited"] = True
    it.props = props
    if "in_s" in body:
        it.in_s = max(0.0, float(body["in_s"]))
    if it.track != "V1":  # overlays move freely; main-track clips stay locked to narration timing
        if "start_s" in body:
            it.start_s = max(0.0, float(body["start_s"]))
        if "duration_s" in body:
            it.duration_s = max(0.2, float(body["duration_s"]))
    if body.get("asset_id"):
        a = db.get(m.Asset, body["asset_id"])
        if not a or a.project_id != it.project_id or a.kind not in ("video", "image"):
            raise HTTPException(400, "Asset must be an image or video of this project")
        it.asset_id, it.kind = a.id, a.kind
        props.pop("missing", None)
        it.props = props
        if it.scene_id:
            sc = db.get(m.Scene, it.scene_id)
            sc.asset_id, sc.asset_status, sc.visual_type = a.id, "ready", "user"
    db.commit()
    return row(it)


@router.post("/projects/{pid}/timeline")
def add_item(pid: str, body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    p = project_or_404(db, pid, u)
    kind = body.get("kind", "text")
    if kind not in ("text", "motion_graphic"):
        raise HTTPException(400, "Only text and motion-graphic overlays can be added; main clips follow the storyboard")
    props = {k: v for k, v in (body.get("props") or {}).items() if k in EDITABLE}
    props["user"] = True
    if kind == "motion_graphic" and (props.get("mg") or {}).get("type") not in catalog.MG_TYPES:
        raise HTTPException(400, "Unknown motion graphic type")
    if kind == "motion_graphic":
        props = dict(props["mg"], user=True)
    it = m.TimelineItem(project_id=p.id, track="V2" if kind == "motion_graphic" else "T1", kind=kind, start_s=max(0.0, float(body.get("start_s", 0))),
                        duration_s=max(0.3, float(body.get("duration_s", 3))), props=props)
    db.add(it)
    db.commit()
    return row(it)


@router.delete("/timeline/{iid}")
def delete_item(iid: str, db=Depends(get_db), u=Depends(current_user)):
    it = db.get(m.TimelineItem, iid)
    if not it:
        raise HTTPException(404, "Clip not found")
    project_or_404(db, it.project_id, u)
    if it.track == "V1":
        raise HTTPException(400, "Main-track clips are tied to narration; replace the visual instead")
    db.delete(it)
    db.commit()
    return {"ok": True}


@router.patch("/audio/{tid}")
def patch_audio(tid: str, body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    t = db.get(m.AudioTrack, tid)
    if not t:
        raise HTTPException(404, "Track not found")
    p = project_or_404(db, t.project_id, u)
    ps = db.query(m.ProjectSettings).filter_by(project_id=p.id).one()
    stl = dict(ps.style or {})
    if "volume" in body and t.role in ("music", "sfx"):
        t.volume = max(0.0, min(1.5, float(body["volume"])))
        stl["%s_volume" % t.role] = t.volume
    if "muted" in body and t.role in ("music", "sfx"):
        t.muted = bool(body["muted"])
        if t.role == "music":
            stl["music"] = "none" if t.muted else (t.props or {}).get("mood", "cinematic")
        else:
            stl["sfx"] = not t.muted
    if "enhance" in body and t.role == "voice":
        stl["voice_enhance"] = bool(body["enhance"])
    ps.style = stl
    db.commit()
    return {"ok": True, "needs_remix": True}


@router.patch("/subtitles/{sid}")
def patch_subtitle(sid: str, body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    s = db.get(m.Subtitle, sid)
    if not s:
        raise HTTPException(404, "Subtitle not found")
    project_or_404(db, s.project_id, u)
    if "text" in body:
        s.text = str(body["text"])[:500]
        ws = s.text.split()
        span = (s.end_s - s.start_s) / max(1, len(ws))
        s.words = [{"w": w, "s": round(s.start_s + i * span, 3), "e": round(s.start_s + (i + 1) * span, 3)} for i, w in enumerate(ws)]
    db.commit()
    return row(s)


# ------------------------------------------------------------------ versions
@router.post("/projects/{pid}/versions/{ver}/restore")
def restore(pid: str, ver: int, db=Depends(get_db), u=Depends(current_user)):
    p = project_or_404(db, pid, u)
    v = db.query(m.ProjectVersion).filter_by(project_id=p.id, version=ver).one_or_none()
    if not v:
        raise HTTPException(404, "Version not found")
    snap = v.snapshot or {}
    for s in snap.get("scenes", []):
        sc = db.get(m.Scene, s["id"])
        if sc:
            sc.plan, sc.visual_type, sc.asset_id = s["plan"], s["visual_type"], s["asset_id"]
            sc.asset_status = "ready" if s["asset_id"] or s["visual_type"] == "motion_graphic" else sc.asset_status
    db.query(m.TimelineItem).filter_by(project_id=p.id).delete()
    db.query(m.Subtitle).filter_by(project_id=p.id).delete()
    db.flush()
    for it in snap.get("timeline", []):
        db.add(m.TimelineItem(**{k: v for k, v in it.items() if k in ("id", "project_id", "scene_id", "asset_id", "track", "kind", "start_s", "duration_s", "in_s", "props")}))
    for s in snap.get("subtitles", []):
        db.add(m.Subtitle(**{k: v for k, v in s.items() if k in ("id", "project_id", "idx", "start_s", "end_s", "text", "words")}))
    db.flush()
    nv = save_version(db, p, "Restored version %d" % ver)
    db.commit()
    return {"ok": True, "version": nv}


# ------------------------------------------------------------------ files & export
@router.get("/assets/{aid}/file")
def asset_file(aid: str, download: int = 0, db=Depends(get_db), u=Depends(current_user)):
    a = db.get(m.Asset, aid)
    if not a:
        raise HTTPException(404, "Asset not found")
    if a.project_id:
        project_or_404(db, a.project_id, u)
    path = assets.local(a)
    if not os.path.isfile(path):
        raise HTTPException(410, "File is missing from storage")
    return FileResponse(path, media_type=a.content_type or None, filename=a.filename if download else None)


@router.get("/projects/{pid}/export")
def export_bundle(pid: str, include_media: int = 0, db=Depends(get_db), u=Depends(current_user)):
    """Editable project package: project JSON, script, transcript, storyboard, captions, research, licences, render settings (+ final MP4)."""
    p = project_or_404(db, pid, u)
    full = get_project(pid, db, u)
    tl = get_timeline(pid, db, u)
    vo, tr = transcript(db, p.id)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("project.json", json.dumps({"project": full, "timeline": tl}, indent=1, default=str))
        if full.get("script"):
            z.writestr("script.txt", full["script"]["text"])
        if tr:
            z.writestr("transcript.json", json.dumps({"language": tr.language, "word_level": tr.word_level, "words": tr.words}, indent=1))

        def ts(t):
            return "%02d:%02d:%02d,%03d" % (t // 3600, t % 3600 // 60, t % 60, int(t * 1000) % 1000)
        z.writestr("captions.srt", "\n".join("%d\n%s --> %s\n%s\n" % (i + 1, ts(s["start_s"]), ts(s["end_s"]), s["text"]) for i, s in enumerate(tl["subtitles"])))
        z.writestr("storyboard.json", json.dumps(full["scenes"], indent=1, default=str))
        lic = []
        for a in db.query(m.Asset).filter_by(project_id=p.id).all():
            l = db.query(m.AssetLicense).filter_by(asset_id=a.id).first()
            src = db.query(m.AssetSource).filter_by(asset_id=a.id).first()
            lic.append({"asset": a.filename, "kind": a.kind, "role": a.role, "license": l.license if l else None, "attribution": l.attribution if l else None,
                        "commercial_use": l.commercial_use if l else "unknown", "source": src.source_url if src else None, "provider": src.provider if src else None,
                        "prompt": src.prompt if src else None})
        z.writestr("sources_and_licenses.json", json.dumps(lic, indent=1))
        z.writestr("research.json", json.dumps(full["research"], indent=1, default=str))
        if include_media:
            r = next((r for r in full["renders"] if r["status"] == "succeeded" and r["kind"] == "final"), None)
            if r and r.get("asset_id"):
                z.write(assets.local(db.get(m.Asset, r["asset_id"])), "final.mp4")
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip", headers={"Content-Disposition": 'attachment; filename="%s.zip"' % (p.title[:60].replace('"', "") or "project")})
