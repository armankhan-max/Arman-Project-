"""Render frames from scene.blend, skipping frames that are already valid PNGs (resume-safe).

  python render_frames.py OUTDIR [--frames 1,100,175 | --range 1-480] [--res 540x960] [--samples N]
  (or: blender -b OUTDIR/scene.blend -P render_frames.py -- OUTDIR ...)
"""
import os
import sys
import time

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
out = os.path.abspath(argv[0])
if not bpy.data.filepath:
    bpy.ops.wm.open_mainfile(filepath=os.path.join(out, "scene.blend"))
sc = bpy.context.scene
frames = list(range(sc.frame_start, sc.frame_end + 1))
sub = "frames"
if "--frames" in argv:
    frames = [int(x) for x in argv[argv.index("--frames") + 1].split(",")]
    sub = "stills"
if "--range" in argv:
    a, b = argv[argv.index("--range") + 1].split("-")
    frames = list(range(int(a), int(b) + 1))
if "--res" in argv:
    w, h = argv[argv.index("--res") + 1].split("x")
    sc.render.resolution_x, sc.render.resolution_y = int(w), int(h)
if "--samples" in argv:
    n = int(argv[argv.index("--samples") + 1])
    sc.cycles.samples = n
    try:
        sc.eevee.taa_render_samples = n
    except AttributeError:
        pass
os.makedirs(os.path.join(out, sub), exist_ok=True)
sc.render.use_persistent_data = len(frames) > 3      # keep BVH/fur between frames when rendering a sequence


def valid_png(p):
    try:
        with open(p, "rb") as fh:
            fh.seek(-12, 2)
            return os.path.getsize(p) > 10000 and fh.read()[-8:-4] == b"IEND"
    except OSError:
        return False


for f in frames:
    path = os.path.join(out, sub, "f_%04d.png" % f)
    if valid_png(path):
        continue
    t = time.time()
    sc.frame_set(f)
    mb = list(sc.get("motion_blur_frames", []))     # motion blur only where the knife moves fast
    sc.render.use_motion_blur = any(mb[i] <= f <= mb[i + 1] for i in range(0, len(mb), 2))
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("[render] frame %d  %.1fs" % (f, time.time() - t), flush=True)
