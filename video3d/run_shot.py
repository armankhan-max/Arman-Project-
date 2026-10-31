"""Build and render one shot.  python run_shot.py <shot-prefix> [--still F] [--range A B] [--out DIR]"""
import argparse, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa
import shots

ap = argparse.ArgumentParser()
ap.add_argument("shot")
ap.add_argument("--still", type=int)
ap.add_argument("--range", nargs=2, type=int)
ap.add_argument("--out", default=os.path.join(HERE, "frames"))
ap.add_argument("--blend")
a = ap.parse_args()
name, n, fn = next(s for s in shots.SHOTS if s[0].startswith(a.shot))
t = time.time()
fn(n)
import lib3d as L
L.set_range(n)
if a.blend:
    bpy.ops.wm.save_as_mainfile(filepath=a.blend)
print(f"built {name} in {time.time()-t:.1f}s", flush=True)
sc = bpy.context.scene
if a.still is not None:
    sc.frame_set(a.still)
    sc.render.filepath = os.path.join(a.out, f"{name}_still{a.still:03d}.png")
    os.makedirs(a.out, exist_ok=True)
    t = time.time(); bpy.ops.render.render(write_still=True); print(f"rendered in {time.time()-t:.1f}s")
else:
    # Animation is keyed at 30 fps; output at FPS_OUT by sampling sub-frames so timing stays in sync.
    fps_out = int(os.environ.get("FPS_OUT", 30))
    idx = [s[0] for s in shots.SHOTS].index(name)
    start30 = sum(s[1] for s in shots.SHOTS[:idx])
    r = fps_out / 30.0
    s_out, e_out = round(start30 * r), round((start30 + n) * r)
    out_dir = os.path.join(a.out, name)
    os.makedirs(out_dir, exist_ok=True)
    sc.render.fps = fps_out
    for k in range(s_out, e_out):
        path = os.path.join(out_dir, f"f{k - s_out:04d}.png")
        if os.path.exists(path):
            continue
        t30 = min(max(k / r - start30, 0.0), n - 1)
        sc.frame_set(int(t30), subframe=t30 - int(t30))
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
