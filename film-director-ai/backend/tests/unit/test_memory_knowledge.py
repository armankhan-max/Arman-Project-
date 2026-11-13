import pytest

from fda.knowledge.ingestion import chunk, ingest
from fda.knowledge.retrieval import search
from fda.memory.store import MemoryError_, recall, remember


def test_confirmed_memory_is_superseded_not_overwritten(db, owner):
    a = remember(db, owner.id, "preference", "camera", "Slow push-ins")
    b = remember(db, owner.id, "preference", "camera", "Handheld energy")
    db.flush()
    db.refresh(a)
    assert a.status == "superseded" and b.supersedes_id == a.id
    assert [x.content for x in recall(db, owner.id, category="preference")] == ["Handheld energy"]


def test_inference_cannot_replace_confirmed(db, owner):
    a = remember(db, owner.id, "preference", "pace", "Fast cuts")
    b = remember(db, owner.id, "preference", "pace", "Slow cuts", status="inferred")
    assert b.id == a.id and a.content == "Fast cuts"


def test_secrets_are_refused(db, owner):
    with pytest.raises(MemoryError_):
        remember(db, owner.id, "preference", "key", "my key is sk-abcdefghijklmnopqrstuvwx")


def test_chunk_and_search(db):
    text = "Jupiter is the largest planet. " * 40 + "\n\nSaturn has rings made of ice and rock. " * 20
    assert len(chunk(text)) >= 2
    doc, new = ingest(db, text, "Planets", "upload", None, "user_provided")
    assert new
    again, new2 = ingest(db, text, "Planets", "upload", None, "user_provided")
    assert not new2 and again.id == doc.id  # duplicate detection
    res = search(db, "rings of ice", 3)
    assert res and "Saturn" in res[0]["text"] and res[0]["trust"] == "user_provided"
