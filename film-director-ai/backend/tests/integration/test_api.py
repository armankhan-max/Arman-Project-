import io
import wave

from fda.database import models as m


def test_auth_required_and_csrf(client):
    from fastapi.testclient import TestClient
    from fda.main import app
    anon = TestClient(app)
    assert anon.get("/api/v1/projects").status_code == 401
    r = client.post("/api/v1/projects", json={"title": "x"}, headers={"x-fda-request": ""})
    assert r.status_code == 403  # missing CSRF header


def test_wrong_password(owner):
    from fastapi.testclient import TestClient
    from fda.main import app
    c = TestClient(app)
    c.headers["x-fda-request"] = "1"
    assert c.post("/api/v1/auth/login", json={"email": "owner@localhost", "password": "nope"}).status_code == 401


def test_project_lifecycle(client):
    r = client.post("/api/v1/projects", json={"title": "What If Jupiter Disappeared?", "mode": "science", "target_minutes": 2, "script": "Jupiter is huge."})
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    d = client.get("/api/v1/projects/%s" % pid).json()
    assert d["script"]["origin"] == "user" and d["settings"]["style"]["look"] == "neon"
    assert client.patch("/api/v1/projects/%s" % pid, json={"style": {"music": "epic"}}).json()["settings"]["style"]["music"] == "epic"
    assert client.request("DELETE", "/api/v1/projects/%s" % pid, json={"confirm": "wrong"}).status_code == 400
    assert client.request("DELETE", "/api/v1/projects/%s" % pid, json={"confirm": "What If Jupiter Disappeared?"}).status_code == 200
    assert client.get("/api/v1/projects/%s" % pid).status_code == 404


def _wav(seconds=1.0):
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(16000)
        w.writeframes(b"\x00\x10" * int(16000 * seconds))
    return b.getvalue()


def test_uploads_validated(client, db):
    pid = client.post("/api/v1/projects", json={"title": "Upload test"}).json()["id"]
    bad = client.post("/api/v1/projects/%s/uploads" % pid, data={"purpose": "voiceover"}, files={"file": ("narration.mp3", b"not really audio", "audio/mpeg")})
    assert bad.status_code == 400 and "corrupted" in bad.json()["detail"]
    wrong = client.post("/api/v1/projects/%s/uploads" % pid, data={"purpose": "voiceover"}, files={"file": ("x.png", b"123", "image/png")})
    assert wrong.status_code == 400
    ok = client.post("/api/v1/projects/%s/uploads" % pid, data={"purpose": "voiceover"}, files={"file": ("narration.wav", _wav(), "audio/wav")})
    assert ok.status_code == 200, ok.text
    a = db.query(m.Asset).filter_by(role="upload_original").one()
    assert a.kind == "audio" and abs(a.duration_s - 1.0) < 0.05 and a.sha256
    assert client.get(ok.json()["url"]).status_code == 200


def test_providers_and_budget_endpoints(client):
    pv = client.get("/api/v1/providers").json()
    assert any(p["name"] == "anthropic" and p["paid"] for p in pv)
    assert client.put("/api/v1/providers/pexels", json={"credentials": {"api_key": "k" * 20}}).json()["configured"]
    assert client.put("/api/v1/budget", json={"scope": "daily", "limit_usd": 3}).json()["daily"]["limit"] == 3
    assert client.get("/api/health").json()["database"] == "ok"


def test_memory_api_refuses_secrets(client):
    assert client.post("/api/v1/memory", json={"category": "preference", "key": "k", "content": "token ghp_abcdefghijklmnopqrstuvwxyz"}).status_code == 400
    assert client.post("/api/v1/memory", json={"category": "preference", "key": "subs", "content": "Yellow captions"}).status_code == 200
    assert client.get("/api/v1/memory?category=preference").json()[0]["content"] == "Yellow captions"
