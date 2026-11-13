"""Timeline → finished video.

The editable timeline in PostgreSQL is converted to a render description, frames are drawn in parallel worker
processes by the compositor (camera moves, transitions, motion graphics, captions, grade), encoded with FFmpeg,
muxed with the final audio mix, and the output is verified with ffprobe before it is recorded as a render."""
import json
import os
import shutil
import subprocess
import sys
import time

import numpy as np

from fda.config import BACKEND_DIR, get_settings
from fda.database import models as m
from fda.services import assets, media
from fda.storage.store import scratch_dir

from .engine import sound

KIND_TO_ENGINE = {"video": "visual", "image": "visual", "blender": "visual", "motion_graphic": "mg", "avatar": "avatar", "placeholder": "mg"}


def describe(db, project, width, height, fps):
    ps = db.query(m.ProjectSettings).filter_by(project_id=project.id).one()
    from fda import catalog
    st = catalog.default_style(project.mode, project.language)
    st.update(ps.style or {})
    items = db.query(m.TimelineItem).filter_by(project_id=project.id).order_by(m.TimelineItem.start_s).all()
    shots, overlays = [], []
    avatar_img = None
    for it in items:
        pr = dict(it.props or {})
        a = db.get(m.Asset, it.asset_id) if it.asset_id else None
        if it.track == "V1":
            kind = KIND_TO_ENGINE.get(it.kind, "visual")
            shot = {"id": str(it.id), "start": it.start_s, "dur": it.duration_s, "kind": kind, "motion": pr.get("motion", "push_in"), "focus": pr.get("focus", [0.5, 0.45]),
                    "transition": pr.get("transition", "cut"), "tdur": pr.get("tdur", 0.5), "filter": pr.get("filter", "none"), "speed": pr.get("speed", 1.0),
                    "offset": it.in_s or 0.0, "v": pr.get("v", 0), "key": pr.get("label", "")}
            if kind == "mg":
                shot["mg"] = pr.get("mg") or {"type": "keywords", "words": [pr.get("label") or "…"]}
            if a and kind in ("visual", "mg"):
                shot["asset"] = {"kind": "video" if a.kind == "video" else "image", "path": assets.local(a), "id": str(a.id)}
            if kind == "avatar" and a:
                avatar_img = assets.local(a)
            shots.append(shot)
        else:
            ov = dict(pr, id=str(it.id), start=it.start_s, dur=it.duration_s)
            ov.setdefault("type", "text" if it.kind == "text" else pr.get("type", "text"))
            overlays.append(ov)
    subs = db.query(m.Subtitle).filter_by(project_id=project.id).order_by(m.Subtitle.start_s).all()
    caps = [{"start": s.start_s, "end": s.end_s, "words": s.words or [{"w": w, "s": s.start_s, "e": s.end_s} for w in s.text.split()]} for s in subs]
    dur = max([s["start"] + s["dur"] for s in shots] + [1.0])
    info = None
    if avatar_img:
        from .engine import avatar as av
        info = av.detect(avatar_img)
    return {"title": project.title, "seed": project.id.int % 10 ** 6, "shots": shots, "overlays": overlays, "captions": caps, "duration": dur,
            "avatar": {"image": avatar_img, "info": info} if avatar_img else {},
            "settings": {"aspect": st.get("aspect", "16:9"), "width": width, "height": height, "theme": st.get("look", "abyss"),
                         "captions": st.get("captions", "clean"), "avatar_pip": bool(st.get("avatar_pip"))}}


def render(db, project, kind="final", width=None, height=None, fps=None, crf=None, progress=lambda f, msg: None, cancelled=lambda: False):
    s = get_settings()
    ps = db.query(m.ProjectSettings).filter_by(project_id=project.id).one()
    width, height, fps = int(width or ps.width), int(height or ps.height), int(fps or ps.fps)
    if kind == "preview":
        sc = 480.0 / min(width, height)
        width, height, fps = int(width * sc) // 2 * 2, int(height * sc) // 2 * 2, min(fps, 24)
    mix = db.query(m.AudioTrack).filter_by(project_id=project.id, role="mix").one_or_none()
    if not mix or not mix.asset_id:
        raise RuntimeError("No final audio mix; run the Audio Agent first")
    work = scratch_dir(project.id, "render", "%s_%d" % (kind, int(time.time())))
    desc = describe(db, project, width, height, fps)
    desc["dir"] = work
    voice = db.query(m.AudioTrack).filter_by(project_id=project.id, role="voice").one_or_none()
    if voice and voice.asset_id:
        vw = os.path.join(work, "voice.wav")
        media.run([s.ffmpeg_bin, "-y", "-v", "error", "-i", assets.local(db.get(m.Asset, voice.asset_id)), "-ac", "1", "-ar", str(sound.SR), vw])
        np.save(os.path.join(work, "voice_env_30.npy"), sound.envelope(vw, 30))
    snap = os.path.join(work, "render.json")
    json.dump(desc, open(snap, "w"))
    total = int(desc["duration"] * fps)
    jobs = max(1, min(s.render_workers, 8, total // (fps * 3) or 1))
    step = -(-total // jobs)
    procs, parts = [], []
    for j in range(jobs):
        f0, f1 = j * step, min(total, (j + 1) * step)
        if f0 >= f1:
            break
        out = os.path.join(work, "part%03d.mp4" % j)
        parts.append((out, f1 - f0))
        procs.append(subprocess.Popen([sys.executable, "-m", "fda.rendering.engine.compose", snap, str(f0), str(f1), out, str(fps), str(width), str(height),
                                       str(crf or (19 if kind == "final" else 27)), "veryfast" if kind == "final" else "ultrafast"],
                                      cwd=BACKEND_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE))
    t0 = time.time()
    while any(p.poll() is None for p in procs):
        done = 0
        for out, n in parts:
            try:
                done += int(open(out + ".prog").read() or 0)
            except (OSError, ValueError):
                pass
        el = time.time() - t0
        progress(done / max(1, total), "Rendering %s %d%% (%d/%d frames, ~%ds left)" % (kind, 100 * done // max(1, total), done, total, int(el / max(1, done) * (total - done))))
        if cancelled():
            for p in procs:
                p.kill()
            raise RuntimeError("Render cancelled")
        time.sleep(2)
    for p in procs:
        if p.returncode != 0:
            raise RuntimeError("Frame worker failed: %s" % p.stderr.read().decode("utf-8", "ignore")[-900:])
    lst = os.path.join(work, "list.txt")
    open(lst, "w").write("".join("file '%s'\n" % o for o, _ in parts))
    out = os.path.join(work, "%s.mp4" % kind)
    media.run([s.ffmpeg_bin, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", assets.local(db.get(m.Asset, mix.asset_id)), "-map", "0:v", "-map", "1:a",
               "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", "%.3f" % desc["duration"], "-movflags", "+faststart", out], timeout=3600)
    pr = verify(out, width, height, fps, desc["duration"])
    a = assets.register(db, out, project.id, "render", "renders", "%s_v%d.mp4" % ("preview" if kind == "preview" else "final", project.current_version), origin="procedural",
                        provider="fda-renderer", settings={"width": width, "height": height, "fps": fps, "kind": kind}, license="Rendered project output", commercial_use="unknown")
    shutil.rmtree(work, ignore_errors=True)
    return a, pr, desc


def verify(path, width, height, fps, expected):
    if not os.path.exists(path) or os.path.getsize(path) < 1000:
        raise RuntimeError("Render produced no file")
    pr = media.probe(path)
    v, au = pr.get("video") or {}, pr.get("audio") or {}
    problems = []
    if v.get("codec") != "h264":
        problems.append("video codec %s" % v.get("codec"))
    if au.get("codec") != "aac":
        problems.append("audio codec %s" % au.get("codec"))
    if (v.get("width"), v.get("height")) != (width, height):
        problems.append("resolution %sx%s" % (v.get("width"), v.get("height")))
    if abs((v.get("fps") or 0) - fps) > 0.6:
        problems.append("fps %s" % v.get("fps"))
    if abs(pr["duration"] - expected) > 1.0:
        problems.append("duration %.2fs vs %.2fs" % (pr["duration"], expected))
    pr["problems"] = problems
    if problems:
        raise RuntimeError("Render verification failed: " + ", ".join(problems))
    return pr
