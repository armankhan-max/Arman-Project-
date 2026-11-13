"""FastAPI application: API v1, security middleware, owner bootstrap and job recovery."""
import logging
import os
import secrets
import threading

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from fda.api import auth_routes, other, projects
from fda.auth.security import CSRF_HEADER, hash_password
from fda.config import get_settings
from fda.database import models as m
from fda.database.session import session_scope

log = logging.getLogger("fda")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
s = get_settings()
app = FastAPI(title="Film Director AI", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in s.cors_origins.split(",") if o.strip()], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def security(request: Request, call_next):
    # CSRF: state-changing requests must carry a custom header, which browsers never add cross-site without CORS approval
    if request.method in ("POST", "PUT", "PATCH", "DELETE") and request.url.path.startswith("/api/") and request.headers.get(CSRF_HEADER) != "1":
        return JSONResponse({"detail": "Missing %s header" % CSRF_HEADER}, status_code=403)
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "same-origin"
    return resp


for r in (auth_routes.router, projects.router, other.router):
    app.include_router(r, prefix="/api/v1")


@app.get("/api/health")
def health():
    out = {"api": "ok"}
    try:
        with session_scope() as db:
            db.execute(text("select 1"))
        out["database"] = "ok"
    except Exception as e:
        out["database"] = "error: %s" % str(e)[:120]
    try:
        import redis
        redis.Redis.from_url(s.redis_url, socket_connect_timeout=1).ping()
        out["redis"] = "ok"
    except Exception:
        out["redis"] = "unavailable (jobs run in-process)"
    import shutil
    out["ffmpeg"] = "ok" if shutil.which(s.ffmpeg_bin) else "missing"
    out["blender"] = "ok" if shutil.which(s.blender_bin) else "missing"
    return out


def bootstrap_owner():
    with session_scope() as db:
        if db.query(m.User).count():
            return
        pw = s.owner_password
        generated = False
        if not pw:
            pw = secrets.token_urlsafe(14)
            generated = True
        db.add(m.User(email=s.owner_email.lower(), password_hash=hash_password(pw), is_owner=True))
    if generated:
        os.makedirs(s.storage_dir, exist_ok=True)
        path = os.path.join(s.storage_dir, "OWNER_CREDENTIALS.txt")
        with open(path, "w") as f:
            f.write("email: %s\npassword: %s\n(change it with FDA_OWNER_PASSWORD on a fresh database, or from Settings → Security)\n" % (s.owner_email, pw))
        os.chmod(path, 0o600)
        log.warning("Owner account created. Credentials written to %s", path)


@app.on_event("startup")
def startup():
    bootstrap_owner()
    from fda.orchestration import workflow
    # without Celery, any task marked running belonged to a previous API process that is gone
    threading.Thread(target=lambda: workflow.recover_stale(0 if not workflow.use_celery() else None), daemon=True).start()
    threading.Thread(target=check_free_providers, daemon=True).start()


def check_free_providers():
    """Keyless providers get a real reachability check at start-up so the UI never shows an untested 'ok'."""
    from fda.providers import registry
    for name in registry.all_names():
        try:
            with session_scope() as db:
                p = registry.get(db, name)
                if not p.fields:
                    registry.check(db, name)
        except Exception as e:  # never block start-up
            log.warning("provider check %s failed: %s", name, e)


# Serve the built website (static export) from the same origin when it is present (production container).
_web = os.environ.get("FDA_WEB_DIR") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
if os.path.isdir(_web):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=_web, html=True), name="web")
