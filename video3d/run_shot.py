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
    f0, f1 = a.range if a.range else (0, n)
    L.render_frames(os.path.join(a.out, name), f0, f1)
