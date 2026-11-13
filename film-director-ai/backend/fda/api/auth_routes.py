from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response

from fda.auth.security import SESSION_COOKIE, RateLimiter, make_session, verify_password
from fda.config import get_settings
from fda.database import models as m
from fda.database.session import get_db
from fda.services.audit import audit

from .deps import current_user

router = APIRouter(prefix="/auth", tags=["auth"])
_limit = RateLimiter(8, 300)


@router.post("/login")
def login(request: Request, response: Response, body: dict = Body(...), db=Depends(get_db)):
    ip = request.client.host if request.client else "?"
    if not _limit.allow(ip):
        raise HTTPException(429, "Too many attempts; wait a few minutes")
    u = db.query(m.User).filter_by(email=str(body.get("email", "")).strip().lower()).one_or_none()
    if not u or not verify_password(str(body.get("password", "")), u.password_hash):
        audit(db, "anonymous", "login_failed", body.get("email", ""), ip)
        db.commit()
        raise HTTPException(401, "Wrong email or password")
    u.last_login_at = datetime.now(timezone.utc)
    audit(db, "owner", "login", u.email, ip)
    db.commit()
    s = get_settings()
    response.set_cookie(SESSION_COOKIE, make_session(str(u.id)), max_age=s.session_hours * 3600, httponly=True, samesite="strict", secure=s.env == "production")
    return {"ok": True, "email": u.email}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@router.get("/me")
def me(u=Depends(current_user)):
    return {"id": str(u.id), "email": u.email}


@router.post("/password")
def change_password(body: dict = Body(...), db=Depends(get_db), u=Depends(current_user)):
    from fda.auth.security import hash_password
    if not verify_password(str(body.get("current", "")), u.password_hash):
        raise HTTPException(400, "Current password is wrong")
    new = str(body.get("new", ""))
    if len(new) < 10:
        raise HTTPException(400, "Use at least 10 characters")
    u.password_hash = hash_password(new)
    audit(db, "owner", "password_changed", u.email)
    db.commit()
    return {"ok": True}
