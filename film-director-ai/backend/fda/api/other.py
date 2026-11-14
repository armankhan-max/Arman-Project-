"""Runs & live events, Director chat, YouTube, knowledge, memory, providers, budget, dashboard."""
import asyncio
import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy import func

from fda import catalog
from fda.agents import director, research as research_agent
from fda.agents.common import scenes as get_scenes
from fda.database import models as m
from fda.database.session import SessionLocal, get_db
from fda.knowledge.ingestion import extract_text, ingest, reindex
from fda.knowledge.retrieval import search
from fda.memory.store import CATEGORIES, MemoryError_, remember
from fda.orchestration import workflow
from fda.permissions import budget_manager as budget
from fda.providers import registry
from fda.providers.base import NotConfigured, ProviderError
from fda.services.audit import audit
from fda.youtube import intelligence as yt

from .deps import current_user, project_or_404
from .serialize import row

router = APIRouter()


# ------------------------------------------------------------------ runs
def run_view(db, run):
    d = row(run, ("plan",))
    d["tasks"] = [row(t, ("params",)) for t in db.query(m.WorkflowTask).filter_by(run_id=run.id).order_by(m.WorkflowTask.created_at).all()]
    return d


@router.get("/runs/{rid}")
def get_run(rid: str, after: int = -1, db=Depends(get_db), u=Depends(current_user)):
    run = db.get(m.WorkflowRun, rid)
    if not run:
        raise HTTPException(404, "Run not found")
    project_or_404(db, run.project_id, u)
    d = run_view(db, run)
    if after >= 0:
        evs = db.query(m.WorkflowEvent).filter(m.WorkflowEvent.run_id == run.id, m.WorkflowEvent.id > after).order_by(m.WorkflowEvent.id).limit(300).all()
        d["events"] = [{"id": e.id, "task": e.task_key, "level": e.level, "message": e.message, "at": e.created_at.isoformat()} for e in evs]
    return d


@router.get("/runs/{rid}/events")
async def run_events(rid: str, request: Request, after: int = 0, u=Depends(current_user)):
    """Server-Sent Events: every workflow event and task progress, read from the database (works with any number of workers)."""
    async def gen():
        last = after
        snap = None
        while True:
            if await request.is_disconnected():
                break
            db = SessionLocal()
            try:
                evs = db.query(m.WorkflowEvent).filter(m.WorkflowEvent.run_id == rid, m.WorkflowEvent.id > last).order_by(m.WorkflowEvent.id).limit(200).all()
                for e in evs:
                    last = e.id
                    yield "event: log\ndata: %s\n\n" % json.dumps({"id": e.id, "task": e.task_key, "level": e.level, "message": e.message, "at": e.created_at.isoformat()})
                run = db.get(m.WorkflowRun, rid)
                tasks = db.query(m.WorkflowTask).filter_by(run_id=rid).all()
                cur = json.dumps({"status": run.status if run else "gone", "tasks": [{"key": t.key, "status": t.status, "progress": round(t.progress, 3), "message": t.message} for t in tasks]})
                if cur != snap:
                    snap = cur
                    yield "event: state\ndata: %s\n\n" % cur
                if not run or run.status in ("succeeded", "failed", "cancelled"):
                    yield "event: end\ndata: {}\n\n"
                    break
            finally:
                db.close()
            await asyncio.sleep(1.0)
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/runs/{rid}/cancel")
def cancel_run(rid: str, db=Depends(get_db), u=Depends(current_user)):
    run = db.get(m.WorkflowRun, rid)
    if not run:
        raise HTTPException(404, "Run not found")
    project_or_404(db, run.project_id, u)
    workflow.cancel(db, run.id)
    return {"ok": True}


@router.post("/runs/{rid}/resume")
def resume_run(rid: str, db=Depends(get_db), u=Depends(current_user)):
    run = db.get(m.WorkflowRun, rid)
    if not run:
        raise HTTPException(404, "Run not found")
    project_or_404(db, run.project_id, u)
    workflow.resume(db, run.id)
    return {"ok": True}


# ------------------------------------------------------------------ Director chat
def say(db, project_id, role, content, **data):
    msg = m.ChatMessage(project_id=project_id, role=role, content=content, data=data)
    db.add(msg)
    db.flush()
    return row(msg)


@router.get("/chat")
def chat_history(project_id: str | None = None, db=Depends(get_db), u=Depends(current_user)):
    q = db.query(m.ChatMessage)
    if project_id:
        project_or_404(db, project_id, u)
        q = q.filter_by(project_id=project_id)
    else:
        q = q.filter(m.ChatMessage.project_id.is_(None))
    return [row(x) for x in q.order_by(m.ChatMessage.created_at).limit(300).all()]


@router.post("/chat")
def chat(body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    text = str(body.get("text", "")).strip()
    if not text:
        raise HTTPException(400, "Empty message")
    project = project_or_404(db, body["project_id"], u) if body.get("project_id") else None
    say(db, project.id if project else None, "user", text, attachments=body.get("attachments") or [])
    db.commit()
    intent = director.classify(db, u.id, text, project)
    actions = []
    reply = intent.reply or ""
    for mem in intent.remember or []:
        try:
            if mem.get("content"):
                remember(db, u.id, mem.get("category") if mem.get("category") in CATEGORIES else "preference", str(mem.get("key") or mem["content"][:60]),
                         str(mem["content"]), {}, "confirmed", "owner chat")
                actions.append({"type": "remembered", "content": mem["content"]})
        except MemoryError_ as e:
            actions.append({"type": "not_remembered", "reason": str(e)})
    try:
        if intent.intent == "produce":
            if project is None or project.status not in ("draft",):
                mode = intent.mode if intent.mode in catalog.MODES else "documentary"
                lang = intent.language if intent.language in catalog.LANGUAGES else "en"
                project = m.Project(user_id=u.id, title=(intent.title or text[:80])[:300], brief=intent.brief or text, mode=mode, language=lang,
                                    preserve_narration=intent.preserve_narration if intent.preserve_narration is not None else True)
                db.add(project)
                db.flush()
                st = catalog.default_style(mode, lang)
                w, h = catalog.RESOLUTIONS[st["aspect"]][0]
                db.add(m.ProjectSettings(project_id=project.id, width=w, height=h, fps=30, target_minutes=intent.target_minutes or 3, style=st))
                for att in body.get("attachments") or []:
                    a = db.get(m.Asset, att)
                    if a and a.project_id is None:
                        a.project_id = project.id
                db.flush()
                say(db, project.id, "user", text)
            run = director.start_production(db, project, u.id)
            actions.append({"type": "production_started", "project_id": str(project.id), "run_id": str(run.id)})
            reply = reply or "On it. I'm producing \"%s\" as a %s. Follow the live progress in the project workspace." % (project.title, catalog.MODES[project.mode]["name"].lower())
        elif intent.intent == "edit":
            if project is None:
                reply = "Open the project you want to change, then send the edit from its chat."
            else:
                run, plan = director.start_edit(db, project, text)
                if run:
                    actions.append({"type": "edit_started", "run_id": str(run.id), "plan": plan.model_dump()})
                    reply = "Understood: %s. Only the affected parts will be redone; the previous version stays saved." % plan.understood
                else:
                    reply = "I couldn't map that to a concrete edit. Try naming the scene number and what to change."
        elif intent.intent == "render" and project:
            run, _ = director.start_edit(db, project, text, director.EditPlan(understood="re-render", ops=[director.EditOp(op="render")]))
            actions.append({"type": "render_started", "run_id": str(run.id)})
            reply = reply or "Rendering a new version now."
        elif intent.intent == "research":
            rep = research_agent.research(db, intent.brief or text, project.id if project else None)
            actions.append({"type": "research_report", "report_id": str(rep.id)})
            reply = rep.summary
        elif intent.intent == "youtube_research":
            rep = yt.public_report(db, intent.title or intent.brief or text, 30, None, project.id if project else None)
            actions.append({"type": "youtube_report", "report_id": str(rep.id)})
            reply = rep.summary
        elif intent.intent == "status" and project:
            run = db.query(m.WorkflowRun).filter_by(project_id=project.id).order_by(m.WorkflowRun.created_at.desc()).first()
            reply = "Project status: %s. Latest job: %s (%s)." % (project.status, run.kind if run else "none", run.status if run else "-")
        elif not reply or intent.intent == "question":
            reply = director.answer(db, u.id, text, project)
    except (NotConfigured, budget.BudgetError) as e:
        reply = "I can't do that yet: %s" % e
    except ProviderError as e:
        reply = "A provider failed: %s" % e
    msg = say(db, project.id if project else None, "director", reply or "Done.", intent=intent.intent, actions=actions)
    audit(db, "director", "chat_" + intent.intent, project.id if project else "")
    db.commit()
    return {"message": msg, "project_id": str(project.id) if project else None, "actions": actions}


@router.post("/uploads")
async def loose_upload(file: UploadFile = File(...), db=Depends(get_db), u=Depends(current_user)):
    """Attach a file in the global chat before a project exists."""
    from fda.services import assets
    kind = assets.kind_of(file.filename or "")
    if not kind:
        raise HTTPException(400, "Unsupported file type")
    tmpd = tempfile.mkdtemp()
    tmp = os.path.join(tmpd, "u" + os.path.splitext(file.filename)[1].lower())
    with open(tmp, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        a = assets.register(db, tmp, None, "upload_original", "uploads", file.filename, origin="upload", license="Owner upload", move=True, meta={"purpose": "chat"})
    except Exception as e:
        raise HTTPException(400, "Unreadable file: %s" % str(e)[:200])
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
    db.commit()
    return {"id": str(a.id), "filename": a.filename, "kind": a.kind}


# ------------------------------------------------------------------ saved characters (AI hosts)
def char_view(db, c):
    d = row(c)
    d["image_url"] = "/api/v1/assets/%s/file" % c.image_asset_id if c.image_asset_id else None
    d["lipsync_ready"] = bool((c.external or {}).get("heygen_talking_photo_id"))
    return d


@router.get("/characters")
def characters(db=Depends(get_db), u=Depends(current_user)):
    return [char_view(db, c) for c in db.query(m.Character).filter_by(user_id=u.id).order_by(m.Character.updated_at.desc()).all()]


@router.post("/characters/design")
def character_design(body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    from fda.services import characters as cs
    try:
        persona = cs.design(db, str(body.get("topic", "")), str(body.get("bible", "")))
    except (ProviderError, budget.BudgetError) as e:
        raise HTTPException(502, str(e))
    db.commit()
    return persona


@router.post("/characters")
def character_save(body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    from fda.services import characters as cs
    c = db.get(m.Character, body["id"]) if body.get("id") else None
    if c is None:
        c = m.Character(user_id=u.id, name=str(body.get("name") or (body.get("persona") or {}).get("name") or "Host")[:200])
        db.add(c)
    elif c.user_id != u.id:
        raise HTTPException(404, "Not found")
    for k in ("name", "voice", "tts_provider"):
        if k in body:
            setattr(c, k, str(body[k])[:200])
    for k in ("voice_rate", "voice_pitch"):
        if k in body:
            setattr(c, k, int(body[k] or 0))
    if isinstance(body.get("persona"), dict):
        c.persona = body["persona"]
    if body.get("image_asset_id"):
        c.image_asset_id = body["image_asset_id"]
        c.external = {}
    db.flush()
    if body.get("generate_portrait") or (not c.image_asset_id and body.get("auto_portrait", True)):
        try:
            cs.make_portrait(db, c, body.get("seed"))
        except ProviderError as e:
            db.commit()
            raise HTTPException(502, str(e))
    audit(db, "owner", "character_save", c.id)
    db.commit()
    return char_view(db, c)


@router.post("/characters/{cid}/image")
async def character_image(cid: str, file: UploadFile = File(...), db=Depends(get_db), u=Depends(current_user)):
    from fda.services import assets
    from fda.agents.visual import normalise_image
    c = db.get(m.Character, cid)
    if not c or c.user_id != u.id:
        raise HTTPException(404, "Not found")
    tmpd = tempfile.mkdtemp()
    raw = os.path.join(tmpd, "u" + os.path.splitext(file.filename or ".jpg")[1].lower())
    with open(raw, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        jpg = normalise_image(raw, os.path.join(tmpd, "face.jpg"))
        a = assets.register(db, jpg, None, "character", "characters", "%s.jpg" % c.name[:40], origin="upload", license="Owner upload", kind="image", meta={"character_id": str(c.id)})
    except Exception as e:
        raise HTTPException(400, "Unreadable image: %s" % str(e)[:160])
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
    c.image_asset_id, c.external = a.id, {}
    db.commit()
    return char_view(db, c)


@router.delete("/characters/{cid}")
def character_delete(cid: str, db=Depends(get_db), u=Depends(current_user)):
    c = db.get(m.Character, cid)
    if c and c.user_id == u.id:
        db.delete(c)
        db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ YouTube
def _yt_err(e):
    raise HTTPException(400 if isinstance(e, NotConfigured) else 502, str(e))


@router.get("/youtube/status")
def yt_status(db=Depends(get_db), u=Depends(current_user)):
    conn = db.query(m.ChannelConnection).filter_by(user_id=u.id).first()
    own = db.get(m.Channel, conn.channel_id) if conn and conn.channel_id else None
    data_api = registry.get(db, "youtube_data")
    oauth = registry.get(db, "google_oauth")
    from fda.config import get_settings
    s = get_settings()
    return {"public_api": {"configured": data_api.configured()}, "oauth": {"configured": bool(oauth.creds.get("client_id") or s.google_client_id), "redirect_uri": yt.redirect_uri()},
            "connection": row(conn, ("token_encrypted",)) if conn else None, "channel": row(own) if own else None}


@router.get("/youtube/oauth/start")
def yt_start(db=Depends(get_db), u=Depends(current_user)):
    try:
        return {"url": yt.auth_url(db, u.id)}
    except NotConfigured as e:
        _yt_err(e)


@router.get("/youtube/oauth/callback")
def yt_callback(code: str = "", state: str = "", error: str = "", db=Depends(get_db)):
    if error:
        return HTMLResponse("<p>Authorisation was not granted: %s</p><a href='/youtube'>Back</a>" % error.replace("<", ""), status_code=400)
    try:
        conn = yt.callback(db, code, state)
        audit(db, "owner", "youtube_connected", conn.channel_id)
        db.commit()
    except (ProviderError, NotConfigured) as e:
        return HTMLResponse("<p>Could not connect: %s</p><a href='/youtube'>Back</a>" % str(e).replace("<", ""), status_code=400)
    return RedirectResponse("/youtube?connected=1")


@router.post("/youtube/disconnect")
def yt_disconnect(db=Depends(get_db), u=Depends(current_user)):
    for c in db.query(m.ChannelConnection).filter_by(user_id=u.id).all():
        c.token_encrypted, c.status = None, "disconnected"
    db.commit()
    return {"ok": True}


@router.post("/youtube/sync")
def yt_sync(body: dict = Body(default={}), db=Depends(get_db), u=Depends(current_user)):
    try:
        r = yt.sync_analytics(db, u.id, int(body.get("days", 90)))
        db.commit()
        return r
    except (ProviderError, NotConfigured) as e:
        db.commit()
        _yt_err(e)


@router.post("/youtube/analyze-own")
def yt_analyze_own(db=Depends(get_db), u=Depends(current_user)):
    try:
        rep = yt.own_analysis(db, u.id)
        db.commit()
        return row(rep)
    except (ProviderError, NotConfigured) as e:
        _yt_err(e)


@router.get("/youtube/channel-metrics")
def yt_metrics(days: int = 90, db=Depends(get_db), u=Depends(current_user)):
    ch = db.query(m.Channel).filter_by(is_own=True).first()
    if not ch:
        return {"channel": None, "daily": [], "videos": [], "traffic": []}
    since = datetime.now(timezone.utc) - timedelta(days=days + 2)
    rows = db.query(m.ChannelMetric).filter(m.ChannelMetric.channel_id == ch.id, m.ChannelMetric.scope == "authorized", m.ChannelMetric.period_start >= since).all()
    daily, vids, traffic = {}, {}, {}
    for r in rows:
        if r.video_id is None and r.dimension is None and r.period_start == r.period_end:
            daily.setdefault(r.period_start.date().isoformat(), {})[r.metric] = r.value
        elif r.video_id and r.dimension is None:
            vids.setdefault(r.video_id, {})[r.metric] = r.value
        elif (r.dimension or "").startswith("traffic:") and r.metric == "views":
            traffic[r.dimension[8:]] = r.value
    titles = {v.youtube_video_id: v.title for v in db.query(m.Video).filter(m.Video.youtube_video_id.in_(list(vids))).all()}
    return {"channel": row(ch), "daily": [dict(v, day=k) for k, v in sorted(daily.items())],
            "videos": sorted([dict(v, id=k, title=titles.get(k, k)) for k, v in vids.items()], key=lambda x: -(x.get("views") or 0)),
            "traffic": sorted(traffic.items(), key=lambda x: -x[1]), "retrieved_at": ch.last_synced_at.isoformat() if ch.last_synced_at else None,
            "unavailable": (ch.meta or {}).get("unavailable", [])}


@router.post("/youtube/research")
def yt_research(body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    try:
        rep = yt.public_report(db, str(body.get("query", ""))[:200], int(body.get("n", 30)), body.get("days"), body.get("project_id"))
        db.commit()
        return row(rep)
    except (ProviderError, NotConfigured) as e:
        _yt_err(e)


@router.post("/youtube/channel")
def yt_channel(body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    try:
        ch = yt.channel(db, str(body.get("ref", "")))
        vids = yt.channel_videos(db, ch, int(body.get("n", 30)))
        db.commit()
        return {"channel": row(ch), "videos": [yt.features(v) for v in vids]}
    except (ProviderError, NotConfigured) as e:
        _yt_err(e)


@router.get("/youtube/history")
def yt_history(video_id: str = "", channel_id: str = "", db=Depends(get_db), u=Depends(current_user)):
    q = db.query(m.ChannelMetric).filter(m.ChannelMetric.scope == "public")
    if video_id:
        q = q.filter_by(video_id=video_id)
    if channel_id:
        ch = db.query(m.Channel).filter_by(youtube_channel_id=channel_id).first()
        q = q.filter_by(channel_id=ch.id if ch else None, video_id=None)
    return [{"metric": r.metric, "value": r.value, "retrieved_at": r.retrieved_at.isoformat(), "video_id": r.video_id} for r in q.order_by(m.ChannelMetric.retrieved_at).limit(2000).all()]


@router.get("/reports")
def reports(kind: str | None = None, db=Depends(get_db), u=Depends(current_user)):
    q = db.query(m.ResearchReport)
    if kind:
        q = q.filter_by(kind=kind)
    out = []
    for r in q.order_by(m.ResearchReport.created_at.desc()).limit(50).all():
        d = row(r)
        d["sources"] = [row(s) for s in db.query(m.ResearchSource).filter_by(report_id=r.id).all()]
        out.append(d)
    return out


@router.post("/research")
def do_research(body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    try:
        rep = research_agent.research(db, str(body.get("query", ""))[:500], body.get("project_id"))
        db.commit()
        return row(rep)
    except (ProviderError, NotConfigured, budget.BudgetError) as e:
        raise HTTPException(502, str(e))


# ------------------------------------------------------------------ knowledge & memory
@router.post("/knowledge")
async def add_doc(file: UploadFile = File(None), text: str = Form(""), title: str = Form(""), trust: str = Form("user_provided"), project_id: str = Form(""),
                  db=Depends(get_db), u=Depends(current_user)):
    if file is not None:
        tmpd = tempfile.mkdtemp()
        p = os.path.join(tmpd, "d" + os.path.splitext(file.filename)[1].lower())
        with open(p, "wb") as f:
            shutil.copyfileobj(file.file, f)
        try:
            text = extract_text(p)
        except Exception as e:
            raise HTTPException(400, str(e))
        finally:
            shutil.rmtree(tmpd, ignore_errors=True)
        title = title or file.filename
    if not text.strip():
        raise HTTPException(400, "Nothing to ingest")
    doc, new = ingest(db, text, title or text[:60], "upload", uuid.UUID(project_id) if project_id else None, trust if trust in ("user_provided", "verified", "unverified") else "user_provided")
    db.commit()
    return {"document": row(doc), "new": new, "chunks": db.query(m.KnowledgeChunk).filter_by(document_id=doc.id).count()}


@router.get("/knowledge")
def list_docs(db=Depends(get_db), u=Depends(current_user)):
    out = []
    for d in db.query(m.KnowledgeDocument).order_by(m.KnowledgeDocument.created_at.desc()).limit(200).all():
        x = row(d)
        x["chunks"] = db.query(m.KnowledgeChunk).filter_by(document_id=d.id).count()
        out.append(x)
    return out


@router.get("/knowledge/search")
def kn_search(q: str, project_id: str | None = None, db=Depends(get_db), u=Depends(current_user)):
    return search(db, q, 10, uuid.UUID(project_id) if project_id else None)


@router.delete("/knowledge/{did}")
def kn_delete(did: str, db=Depends(get_db), u=Depends(current_user)):
    d = db.get(m.KnowledgeDocument, did)
    if d:
        db.delete(d)
        db.commit()
    return {"ok": True}


@router.post("/knowledge/reindex")
def kn_reindex(db=Depends(get_db), u=Depends(current_user)):
    n = reindex(db)
    db.commit()
    return {"chunks": n}


@router.get("/memory")
def list_memory(category: str | None = None, include_superseded: int = 0, db=Depends(get_db), u=Depends(current_user)):
    q = db.query(m.Memory).filter_by(user_id=u.id)
    if category:
        q = q.filter_by(category=category)
    if not include_superseded:
        q = q.filter(m.Memory.status != "superseded")
    return [row(x, ("embedding",)) for x in q.order_by(m.Memory.updated_at.desc()).limit(500).all()]


@router.post("/memory")
def add_memory(body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    try:
        mem = remember(db, u.id, body.get("category", "preference"), str(body.get("key", ""))[:200] or str(body.get("content", ""))[:60], str(body.get("content", "")),
                       body.get("data") or {}, "confirmed", "owner")
    except MemoryError_ as e:
        raise HTTPException(400, str(e))
    db.commit()
    return row(mem, ("embedding",))


@router.post("/memory/{mid}/confirm")
def confirm_memory(mid: str, db=Depends(get_db), u=Depends(current_user)):
    mem = db.get(m.Memory, mid)
    if not mem or mem.user_id != u.id:
        raise HTTPException(404, "Not found")
    mem.status, mem.source = "confirmed", mem.source + " (confirmed by owner)"
    db.commit()
    return row(mem, ("embedding",))


@router.delete("/memory/{mid}")
def del_memory(mid: str, db=Depends(get_db), u=Depends(current_user)):
    mem = db.get(m.Memory, mid)
    if mem and mem.user_id == u.id:
        db.delete(mem)
        db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ providers, budget, usage
@router.get("/providers")
def providers(db=Depends(get_db), u=Depends(current_user)):
    return registry.public_view(db)


@router.put("/providers/{name}")
def save_provider(name: str, body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    try:
        cfg = body.get("config")
        if "usd_per_unit" in body:
            cfg = dict(cfg or {}, usd_per_unit=body["usd_per_unit"])
        registry.save(db, name, body.get("credentials"), cfg, body.get("enabled"))
    except KeyError as e:
        raise HTTPException(404, str(e))
    audit(db, "owner", "provider_update", name, fields=list((body.get("credentials") or {}).keys()))
    db.commit()
    return [p for p in registry.public_view(db) if p["name"] == name][0]


@router.post("/providers/{name}/check")
def check_provider(name: str, db=Depends(get_db), u=Depends(current_user)):
    try:
        r = registry.check(db, name)
    except KeyError as e:
        raise HTTPException(404, str(e))
    db.commit()
    return {"status": r.status, "detail": r.status_detail}


@router.get("/budget")
def get_budget(project_id: str | None = None, db=Depends(get_db), u=Depends(current_user)):
    return budget.status(db, uuid.UUID(project_id) if project_id else None)


@router.put("/budget")
def set_budget(body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    scope = body.get("scope")
    if scope not in ("daily", "monthly", "project", "provider"):
        raise HTTPException(400, "scope must be daily, monthly, project or provider")
    val = body.get("limit_usd")
    budget.set_limit(db, scope, body.get("ref") or "", None if val in (None, "") else max(0.0, float(val)))
    audit(db, "owner", "budget_set", scope, ref=body.get("ref"), limit=val)
    db.commit()
    return budget.status(db)


@router.put("/budget/override")
def budget_override(body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    from fda.auth.security import verify_password
    if not verify_password(str(body.get("password", "")), u.password_hash):
        raise HTTPException(403, "Wrong owner password")
    budget.set_override(db, bool(body.get("on")))
    audit(db, "owner", "budget_override", "", on=bool(body.get("on")))
    db.commit()
    return budget.status(db)


@router.get("/usage")
def usage(days: int = 30, db=Depends(get_db), u=Depends(current_user)):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    recs = db.query(m.UsageRecord).filter(m.UsageRecord.created_at >= since).order_by(m.UsageRecord.created_at.desc()).limit(500).all()
    by = db.query(m.UsageRecord.provider, func.count(), func.sum(m.UsageRecord.estimated_usd), func.sum(m.UsageRecord.actual_usd)).filter(
        m.UsageRecord.created_at >= since, m.UsageRecord.status != "released").group_by(m.UsageRecord.provider).all()
    runs = db.query(m.ModelRun.provider, func.count(), func.sum(m.ModelRun.input_tokens), func.sum(m.ModelRun.output_tokens)).filter(m.ModelRun.created_at >= since).group_by(m.ModelRun.provider).all()
    return {"records": [row(r) for r in recs], "by_provider": [{"provider": p, "operations": n, "estimated_usd": float(e or 0), "actual_usd": None if a is None else float(a)} for p, n, e, a in by],
            "llm": [{"provider": p, "calls": n, "input_tokens": int(i or 0), "output_tokens": int(o or 0)} for p, n, i, o in runs]}


@router.get("/catalog")
def get_catalog(u=Depends(current_user)):
    from fda.agents.blender import TEMPLATES, available
    return {"modes": catalog.MODES, "looks": catalog.LOOKS, "movements": catalog.MOVEMENTS, "transitions": catalog.TRANSITIONS, "captions": catalog.CAPTION_STYLES,
            "music": catalog.MUSIC_MOODS, "motion_graphics": catalog.MG_TYPES, "languages": catalog.LANGUAGES, "resolutions": catalog.RESOLUTIONS,
            "blender": {"available": available(), "templates": list(TEMPLATES)}, "fps": [24, 25, 30, 60]}


@router.get("/voices")
def voices(provider: str = "edge_tts", lang: str = "en", db=Depends(get_db), u=Depends(current_user)):
    try:
        p = registry.get(db, provider)
        vs = p.voices()
    except (KeyError, ProviderError, NotConfigured) as e:
        raise HTTPException(400, str(e))
    pre = {"en": "en-", "hi": "hi-", "hinglish": "hi-"}.get(lang, "")
    return [v for v in vs if not pre or provider != "edge_tts" or v["locale"].lower().startswith(pre) or "Multilingual" in v["id"]]


@router.post("/maintenance/cleanup")
def maintenance_cleanup(body: dict = Body(default={}), db=Depends(get_db), u=Depends(current_user)):
    from fda.services.retention import cleanup
    r = cleanup(int(body.get("deleted_days", 7)), int(body.get("scratch_hours", 24)))
    audit(db, "owner", "storage_cleanup", "", **r)
    db.commit()
    return r


@router.get("/dashboard")
def dashboard(db=Depends(get_db), u=Depends(current_user)):
    projects = db.query(m.Project).filter_by(user_id=u.id, deleted_at=None).order_by(m.Project.updated_at.desc()).limit(8).all()
    active = db.query(m.WorkflowRun).filter(m.WorkflowRun.status.in_(["pending", "running"])).order_by(m.WorkflowRun.created_at.desc()).all()
    failed = db.query(m.WorkflowTask).filter(m.WorkflowTask.status == "failed").order_by(m.WorkflowTask.updated_at.desc()).limit(8).all()
    renders = db.query(m.Render).filter_by(status="succeeded").order_by(m.Render.created_at.desc()).limit(6).all()
    pv = registry.public_view(db)
    conn = db.query(m.ChannelConnection).filter_by(user_id=u.id).first()
    titles = {p.id: p.title for p in db.query(m.Project).all()}
    return {"projects": [row(p) for p in projects],
            "active": [dict(run_view(db, r), project_title=titles.get(r.project_id)) for r in active],
            "failed_tasks": [dict(row(t, ("params", "output")), project_title=titles.get(db.get(m.WorkflowRun, t.run_id).project_id)) for t in failed],
            "renders": [dict(row(r), project_title=titles.get(r.project_id)) for r in renders],
            "providers": [{"name": p["name"], "label": p["label"], "status": p["status"], "configured": p["configured"], "caps": p["caps"]} for p in pv],
            "budget": budget.status(db), "youtube": {"connected": bool(conn and conn.status == "connected")}, "workers": {"celery": workflow.use_celery()}}
