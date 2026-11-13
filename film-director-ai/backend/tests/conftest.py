import os
import shutil
import tempfile

import pytest

TMP = tempfile.mkdtemp(prefix="fda_test_")
os.environ.setdefault("FDA_DATABASE_URL", "postgresql+psycopg://postgres@/fda_test?host=/tmp")
os.environ["FDA_STORAGE_DIR"] = TMP
os.environ["FDA_USE_CELERY"] = "false"
os.environ["FDA_OWNER_PASSWORD"] = "test-password-123"
os.environ["FDA_SECRET_KEY"] = "test-secret-key-test-secret-key"
os.environ["STUDIO_DATA"] = os.path.join(TMP, ".engine")
for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "PEXELS_API_KEY", "PIXABAY_API_KEY", "YOUTUBE_API_KEY", "ELEVENLABS_API_KEY"):
    os.environ.pop(k, None)

from sqlalchemy import text  # noqa: E402

from fda.database import models as m  # noqa: E402
from fda.database.session import engine, SessionLocal  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def schema():
    eng = engine()
    with eng.begin() as c:
        c.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    from alembic import command
    from alembic.config import Config
    cfg = Config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(os.path.dirname(__file__)), "fda", "database", "migrations"))
    cfg.attributes["url"] = os.environ["FDA_DATABASE_URL"]
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    yield
    shutil.rmtree(TMP, ignore_errors=True)


@pytest.fixture(autouse=True)
def clean():
    eng = engine()
    names = ", ".join('"%s"' % t.name for t in reversed(m.Base.metadata.sorted_tables))
    with eng.begin() as c:
        c.execute(text("TRUNCATE %s RESTART IDENTITY CASCADE" % names))
    yield


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture
def owner(db):
    from fda.auth.security import hash_password
    u = m.User(email="owner@localhost", password_hash=hash_password("test-password-123"))
    db.add(u)
    db.commit()
    return u


@pytest.fixture
def project(db, owner):
    from fda import catalog
    p = m.Project(user_id=owner.id, title="Test film", brief="", mode="documentary", language="en")
    db.add(p)
    db.flush()
    st = catalog.default_style("documentary")
    db.add(m.ProjectSettings(project_id=p.id, width=640, height=360, fps=24, target_minutes=0.2, style=st))
    db.commit()
    return p


@pytest.fixture
def client(owner):
    from fastapi.testclient import TestClient
    from fda.main import app
    c = TestClient(app)
    c.headers["x-fda-request"] = "1"
    r = c.post("/api/v1/auth/login", json={"email": "owner@localhost", "password": "test-password-123"})
    assert r.status_code == 200, r.text
    return c
