"""Storage retention: purge projects soft-deleted more than N days ago and stale scratch folders."""
import os
import shutil
import time
from datetime import datetime, timedelta, timezone

from fda.config import get_settings
from fda.database import models as m
from fda.database.session import session_scope
from fda.storage.store import store


def cleanup(deleted_days=7, scratch_hours=24):
    out = {"projects_purged": 0, "scratch_removed": 0}
    cutoff = datetime.now(timezone.utc) - timedelta(days=deleted_days)
    with session_scope() as db:
        busy = {r.project_id for r in db.query(m.WorkflowRun).filter(m.WorkflowRun.status.in_(["pending", "running"])).all()}
        for p in db.query(m.Project).filter(m.Project.deleted_at.isnot(None), m.Project.deleted_at < cutoff).all():
            if p.id in busy:
                continue
            store().delete_prefix("projects/%s" % p.id)
            shutil.rmtree(os.path.join(get_settings().storage_dir, ".work", str(p.id)), ignore_errors=True)
            db.delete(p)
            out["projects_purged"] += 1
        busy_ids = {str(x) for x in busy}
    work = os.path.join(get_settings().storage_dir, ".work")
    if os.path.isdir(work):
        for d in os.listdir(work):
            path = os.path.join(work, d)
            if d in busy_ids or not os.path.isdir(path):
                continue
            if time.time() - os.path.getmtime(path) > scratch_hours * 3600:
                shutil.rmtree(path, ignore_errors=True)
                out["scratch_removed"] += 1
    return out
