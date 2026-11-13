import uuid

from fastapi import Depends, HTTPException, Request

from fda.auth.security import SESSION_COOKIE, read_session
from fda.database import models as m
from fda.database.session import get_db


def current_user(request: Request, db=Depends(get_db)) -> m.User:
    uid = read_session(request.cookies.get(SESSION_COOKIE))
    if not uid:
        raise HTTPException(401, "Not signed in")
    u = db.get(m.User, uuid.UUID(uid))
    if not u:
        raise HTTPException(401, "Not signed in")
    return u


def project_or_404(db, pid, user) -> m.Project:
    try:
        p = db.get(m.Project, uuid.UUID(str(pid)))
    except ValueError:
        p = None
    if not p or p.user_id != user.id or p.deleted_at:
        raise HTTPException(404, "Project not found")
    return p
