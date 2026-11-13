import os

from fda.permissions import budget_manager as budget
from fda.providers import registry
from fda.storage.store import DBStore


def test_db_store_survives_cache_loss(tmp_path, monkeypatch):
    st = DBStore(str(tmp_path / "cache"))
    src = tmp_path / "v.mp4"
    src.write_bytes(b"video-bytes" * 100)
    st.put_file(str(src), "projects/p/renders/v.mp4")
    os.remove(st.path("projects/p/renders/v.mp4"))  # simulate a restart with an empty disk
    assert st.exists("projects/p/renders/v.mp4")
    assert open(st.local_path("projects/p/renders/v.mp4"), "rb").read() == b"video-bytes" * 100
    st.delete_prefix("projects/p")
    assert not st.exists("projects/p/renders/v.mp4")


def test_owner_override_allows_paid_without_limits(db):
    p = registry.get(db, "anthropic")
    try:
        budget.reserve(db, p, "llm", 1, "1k tokens")
        raise AssertionError("should be blocked")
    except budget.BudgetError:
        pass
    budget.set_override(db, True)
    db.flush()
    rec = budget.reserve(db, p, "llm", 1, "1k tokens")
    assert rec.status == "reserved" and budget.status(db)["owner_override"]
    budget.set_override(db, False)
    db.flush()
    assert not budget.status(db)["owner_override"]
