from unittest import mock

from fda.database import models as m


def test_bulk_duplicate_captions_runs_stats(client, db, monkeypatch):
    from fda.orchestration import workflow
    monkeypatch.setattr(workflow, "submit", lambda *a, **k: None)  # do not actually run productions in this test
    r = client.post("/api/v1/projects/bulk", json={"titles": "What If the Moon Vanished?\n\nWhy Bees Dance\n", "mode": "science", "target_minutes": 1, "start": False})
    assert r.status_code == 200, r.text
    made = r.json()["created"]
    assert [x["title"] for x in made] == ["What If the Moon Vanished?", "Why Bees Dance"]
    pid = made[0]["id"]
    assert client.put("/api/v1/projects/%s/script" % pid, json={"text": "The Moon keeps our tides steady."}).status_code == 200
    d = client.post("/api/v1/projects/%s/duplicate" % pid, json={}).json()
    assert d["title"].endswith("(copy)") and d["mode"] == "science"
    assert client.get("/api/v1/projects/%s" % d["id"]).json()["script"]["text"] == "The Moon keeps our tides steady."
    p = db.get(m.Project, __import__("uuid").UUID(pid))
    db.add(m.Subtitle(project_id=p.id, idx=0, start_s=0.5, end_s=2.25, text="Hello there", words=[]))
    db.commit()
    srt = client.get("/api/v1/projects/%s/captions.srt" % pid).text
    assert "00:00:00,500 --> 00:00:02,300" in srt and "Hello there" in srt
    assert client.get("/api/v1/projects/%s/captions.vtt" % pid).text.startswith("WEBVTT")
    assert client.get("/api/v1/runs").status_code == 200
    st = client.get("/api/v1/stats").json()
    assert st["projects"] == 3
    assert client.post("/api/v1/projects/%s/short" % pid, json={}).status_code == 400  # nothing produced yet
    assert client.post("/api/v1/projects/%s/rebuild" % pid).status_code == 200


def test_stock_search_and_use(client, db, monkeypatch):
    from fda.providers import visual
    cand = {"kind": "image", "url": "https://example.org/a.jpg", "thumb": "https://example.org/t.jpg", "provider": "openverse", "license": "CC0", "attribution": "x",
            "source_page": "https://example.org", "width": 1600, "height": 900, "duration": 0, "title": "moon surface", "id": "openverse-1", "commercial_use": "yes", "terms_url": None}
    monkeypatch.setattr(visual.Openverse, "search", lambda self, q, kind="image", n=8, portrait=False: [dict(cand)])
    res = client.get("/api/v1/media/search", params={"q": "moon", "kind": "image"}).json()
    hit = [r for r in res["results"] if r["provider"] == "openverse"][0]
    pid = client.post("/api/v1/projects", json={"title": "Moon"}).json()["id"]
    p = db.get(m.Project, __import__("uuid").UUID(pid))
    sb = m.Storyboard(project_id=p.id, version=1)
    db.add(sb)
    db.flush()
    sc = m.Scene(storyboard_id=sb.id, project_id=p.id, idx=1, start_s=0, end_s=4, narration="The moon", visual_type="ai_image", plan={})
    db.add(sc)
    db.commit()

    def fake_download(url, dest, **kw):
        from PIL import Image
        Image.new("RGB", (1600, 900), "#334455").save(dest, "PNG")
        return dest
    with mock.patch("fda.api.features.download", fake_download):
        r = client.post("/api/v1/scenes/%s/use-stock" % sc.id, json={"key": hit["key"]})
    assert r.status_code == 200, r.text
    db.expire_all()
    sc2 = db.get(m.Scene, sc.id)
    assert sc2.visual_type == "stock_image" and sc2.asset_status == "ready"
    lic = db.query(m.AssetLicense).filter_by(asset_id=sc2.asset_id).one()
    assert lic.license == "CC0"
    assert client.post("/api/v1/scenes/%s/use-stock" % sc.id, json={"key": "nope"}).status_code == 400
