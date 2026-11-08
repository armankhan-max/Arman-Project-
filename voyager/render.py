"""Render voyager_news.blend headless.

  python render.py stills [--pct 50]        one frame from the middle of each shot -> render/stills/
  python render.py frames [--jobs 2]        EEVEE-render the "Shots" scene to render/frames/####.png
                                            (resumable: frames already on disk are skipped)
  python render.py edit                     "Edit" scene (frames + captions + voice) -> voyager_news.mp4

Works with `pip install bpy` (Blender 5.x as a module) or `blender -b -P render.py -- <args>`.
"""
import argparse
import os
import subprocess
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "voyager_news.blend")
FRAMES = os.path.join(HERE, "render", "frames")


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["stills", "frames", "edit", "_chunk"])
    ap.add_argument("--pct", type=int, default=100)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--frames", default="")  # _chunk: comma list
    return ap.parse_args(argv)


def open_blend():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    return bpy.data.scenes["Shots"], bpy.data.scenes["Edit"]


def render_frame(sc, f, path):
    sc.frame_set(f)
    sc.render.filepath = path
    sc.render.image_settings.file_format = "PNG"
    with bpy.context.temp_override(scene=sc):
        bpy.ops.render.render(write_still=True, scene=sc.name)


def main():
    a = args()
    if a.mode == "stills":
        sc, _ = open_blend()
        sc.render.resolution_percentage = a.pct
        ms = sorted(sc.timeline_markers, key=lambda m: m.frame)
        out = os.path.join(HERE, "render", "stills")
        os.makedirs(out, exist_ok=True)
        for i, m in enumerate(ms):
            end = ms[i + 1].frame if i + 1 < len(ms) else sc.frame_end
            f = (m.frame + end) // 2
            render_frame(sc, f, os.path.join(out, f"{m.name}_f{f:04d}.png"))
    elif a.mode == "_chunk":
        sc, _ = open_blend()
        sc.render.resolution_percentage = a.pct
        for f in map(int, a.frames.split(",")):
            render_frame(sc, f, os.path.join(FRAMES, f"{f:04d}.png"))
    elif a.mode == "frames":
        sc, _ = open_blend()
        os.makedirs(FRAMES, exist_ok=True)
        todo = [f for f in range(sc.frame_start, sc.frame_end + 1)
                if not os.path.exists(os.path.join(FRAMES, f"{f:04d}.png"))]
        print(f"{len(todo)} frames to render with {a.jobs} jobs")
        procs = []
        for j in range(a.jobs):
            part = todo[j::a.jobs]  # interleaved so every job finishes at about the same time
            if part:
                procs.append(subprocess.Popen([sys.executable, __file__, "_chunk", "--pct", str(a.pct),
                                               "--frames", ",".join(map(str, part))]))
        sys.exit(max((p.wait() for p in procs), default=0))
    elif a.mode == "edit":
        sc, ed = open_blend()
        seq = ed.sequence_editor
        old = seq.strips.get("Shots")
        files = sorted(os.listdir(FRAMES))
        assert len(files) == sc.frame_end - sc.frame_start + 1, f"missing frames: {len(files)}"
        img = seq.strips.new_image("ShotsRendered", os.path.join(FRAMES, files[0]), channel=1, frame_start=1)
        for fn in files[1:]:
            img.elements.append(fn)
        img.transform.scale_x = ed.render.resolution_x / sc.render.resolution_x  # 720p shots -> 1080p edit
        img.transform.scale_y = ed.render.resolution_y / sc.render.resolution_y
        if old:
            seq.strips.remove(old)
        ed.render.filepath = os.path.join(HERE, "voyager_news.mp4")
        with bpy.context.temp_override(scene=ed):
            bpy.ops.render.render(animation=True, scene=ed.name)


if __name__ == "__main__":
    main()
