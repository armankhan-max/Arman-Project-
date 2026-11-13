import os
from datetime import datetime, timedelta, timezone

from fda.database import models as m
from fda.services.assets import register
from fda.services.retention import cleanup
from fda.storage.store import scratch_dir, store


def test_purges_old_deleted_projects_only(db, project, tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hello")
    a = register(db, str(f), project.id, "scene", "x", "a.txt", kind="document")
    key = a.storage_key
    scratch_dir(project.id, "tmp")
    project.deleted_at = datetime.now(timezone.utc) - timedelta(days=10)
    keep = m.Project(user_id=project.user_id, title="keep", deleted_at=datetime.now(timezone.utc))
    db.add(keep)
    db.commit()
    pid, kid = project.id, keep.id
    r = cleanup(7, 24)
    assert r["projects_purged"] == 1 and not store().exists(key)
    db.expunge_all()
    assert db.get(m.Project, pid) is None and db.get(m.Project, kid) is not None
