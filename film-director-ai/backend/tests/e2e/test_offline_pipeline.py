"""End-to-end through storyboard → timeline → audio → render → QC → chat edit → re-render, with no network:
narration is synthesised locally, visuals are local images, motion graphics and a Blender-free path."""
import os
import wave

import numpy as np
import pytest
from PIL import Image, ImageDraw

from fda.agents import audio, director, editor, quality
from fda.agents.common import scenes
from fda.agents.storyboard import segment
from fda.database import models as m
from fda.rendering import renderer
from fda.services import assets, media
from fda.storage.store import scratch_dir


class Ctx:
    def __init__(self, db, project, params=None):
        self.db, self.project, self.params, self.state = db, project, params or {}, {}
        self.run = type("R", (), {"id": None, "cancel_requested": False})()
        self.task = type("T", (), {"key": "t", "attempts": 1, "message": ""})()

    def progress(self, f, msg=""):
        pass

    def log(self, msg, level="info", **k):
        pass


def make_voice(path, words=36, sr=44100):
    rng = np.random.default_rng(1)
    chunks, t, out = [], 0.3, []
    chunks.append(np.zeros(int(0.3 * sr)))
    for i in range(words):
        d = 0.28
        x = rng.standard_normal(int(d * sr)) * 0.15 * np.hanning(int(d * sr))
        chunks.append(x)
        out.append({"w": ("word%d" % i) + ("." if i % 9 == 8 else ""), "s": round(t, 3), "e": round(t + d, 3)})
        gap = 0.45 if i % 9 == 8 else 0.1
        chunks.append(np.zeros(int(gap * sr)))
        t += d + gap
    x = np.concatenate(chunks)
    with wave.open(path, "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(sr)
        w.writeframes((x * 32767).astype("<i2").tobytes())
    return out, t


def make_image(path, color):
    im = Image.new("RGB", (1280, 720), color)
    d = ImageDraw.Draw(im)
    for i in range(0, 1280, 80):
        d.line([(i, 0), (i + 300, 720)], fill=(255, 255, 255), width=6)
    im.save(path)


@pytest.mark.timeout(900)
def test_full_offline_pipeline(db, project):
    work = scratch_dir(project.id, "test")
    wav = os.path.join(work, "voice.wav")
    words, dur = make_voice(wav)
    a = assets.register(db, wav, project.id, "processed", "audio", "voice.wav", origin="tts", provider="test")
    vo = m.Voiceover(project_id=project.id, origin="tts", processed_asset_id=a.id, duration_s=dur)
    db.add(vo)
    db.flush()
    db.add(m.Transcript(voiceover_id=vo.id, text=" ".join(w["w"] for w in words), word_level=True, provider="test", words=words))
    sb = m.Storyboard(project_id=project.id, version=1)
    db.add(sb)
    db.flush()
    imgs = []
    for k, col in enumerate(["#204060", "#603020", "#206040"]):
        p = os.path.join(work, "img%d.png" % k)
        make_image(p, col)
        imgs.append(assets.register(db, p, project.id, "scene", "scenes", "img%d.png" % k, origin="generated", provider="test", license="test", meta={"source_id": "i%d" % k}))
    segs = segment(words, 4.0, dur)
    for k, s in enumerate(segs):
        mg = k % 3 == 1
        db.add(m.Scene(storyboard_id=sb.id, project_id=project.id, idx=k + 1, start_s=s["start"], end_s=s["end"], narration="scene %d" % (k + 1),
                       visual_type="motion_graphic" if mg else "ai_image", asset_id=None if mg else imgs[k % 3].id, asset_status="ready",
                       plan={"movement": "push_in", "transition": "fade" if k else "cut", "sfx": ["whoosh"] if k == 2 else [],
                             "motion_graphic": {"type": "stat", "value": 42, "label": "test"} if mg else None}))
    db.commit()
    ctx = Ctx(db, project)
    audio.run(ctx)
    editor.run(ctx)
    db.commit()
    assert db.query(m.Subtitle).filter_by(project_id=project.id).count() > 0
    items = db.query(m.TimelineItem).filter_by(project_id=project.id, track="V1").order_by(m.TimelineItem.start_s).all()
    assert len(items) == len(segs) and items[0].start_s == 0.0
    rnd, probe, desc = renderer.render(db, project, "final")
    db.commit()
    assert probe["video"]["codec"] == "h264" and probe["audio"]["codec"] == "aac"
    assert (probe["video"]["width"], probe["video"]["height"]) == (640, 360)
    assert abs(probe["duration"] - desc["duration"]) < 1.0
    det = media.detect(assets.local(rnd), True, True, probe["duration"])
    assert not [b for b in det["black"] if b[0] > 0.6 and b[1] < probe["duration"] - 1.6]
    r = m.Render(project_id=project.id, project_version=project.current_version, kind="final", status="succeeded", asset_id=rnd.id, verified=True, probe=probe)
    db.add(r)
    db.commit()
    out = quality.qc_run(Ctx(db, project, {"render_id": str(r.id), "skip_creative": True}))
    rep = db.query(m.QualityReport).filter_by(project_id=project.id).one()
    assert not [i for i in rep.issues if i["severity"] == "critical"], rep.issues
    # chat edit touches only scene 1; everything else keeps its asset
    before = {s.idx: s.asset_id for s in scenes(db, project.id)}
    plan = director.heuristic_edit("Scene 1 ka camera movement change kar aur background music thoda lower kar", len(segs))
    ops = {o.op for o in plan.ops}
    assert {"change_camera", "music_volume"} <= ops
    res = director.apply_edit_run(Ctx(db, project, {"plan": plan.model_dump()}))
    db.commit()
    after = {s.idx: s.asset_id for s in scenes(db, project.id)}
    assert before == after
    assert any(t["key"] == "audio" for t in res["spawn"]) and not any(t["key"].startswith("edit_visual") for t in res["spawn"])
    st = db.query(m.ProjectSettings).filter_by(project_id=project.id).one().style
    assert st["music_volume"] < 0.5
    v1 = db.query(m.TimelineItem).filter_by(project_id=project.id, track="V1").order_by(m.TimelineItem.start_s).first()
    assert v1.props["user_edited"] and v1.props["motion"] != "push_in"
    editor.run(Ctx(db, project, {"resync_subtitles": False}))
    db.commit()
    v1 = db.query(m.TimelineItem).filter_by(project_id=project.id, track="V1").order_by(m.TimelineItem.start_s).first()
    assert v1.props["motion"] != "push_in"  # owner edit survives a rebuild
    assert db.query(m.ProjectVersion).filter_by(project_id=project.id).count() == 2
