"""Teddy Bear vs 1000 Cuts: satisfying ASMR slicing animation (Blender 4.x Python).

One script builds the whole scene from an empty file: a plush teddy bear with
a red bow tie on a wooden garden table, a steel chef's knife, warm golden-hour
light and depth of field. It then animates 1 -> 4 -> 10 -> 100 -> 1000 cuts:

  * cut 1      slow vertical cut through the centre, the halves part to show cotton stuffing
  * cuts 2-4   three deliberate slices
  * cuts 5-10  faster slices
  * cuts 11-100  rapid machine-gun slicing (thin slabs, white seams)
  * cuts 101-1000  dicing pass: the bear turns into cubes that tumble onto the table

Design rules (taken from the ASMR cutting-studio workflow):
  * ONE impact list drives the knife, the cut counter and the sound effects.
  * The pieces are pre-cut once (identical geometry every frame) and each seam only
    opens when the blade reaches it, so the bear's proportions never change.
  * The table is a passive rigid-body collider; cubes are active rigid bodies.

Usage (Blender 4.0+; works with --factory-startup):
  blender -b --factory-startup -P teddy_slice.py -- --out OUTDIR [--preview]
  # builds the scene, bakes physics, saves OUTDIR/scene.blend and OUTDIR/timeline.json
  blender -b OUTDIR/scene.blend -o OUTDIR/frames/f_#### -s 1 -e 480 -a
  # renders numbered PNGs (re-run with -s N to resume)

Low-RAM (3.7 GB) notes: EEVEE is the default engine. The fur is geometry-nodes
curves, not particles. Frames go to disk one at a time. No textures are loaded
from disk. --preview renders at 540x960 with fewer samples.
"""
import bpy  # noqa: I001  (bpy first: needed when run as the pip `bpy` module)
import bmesh
import json
import math
import os
import random
import sys
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

# ----------------------------------------------------------------------------- config
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[argv.index("--out") + 1]) if "--out" in argv else os.path.abspath("teddy_out")
PREVIEW = "--preview" in argv
ENGINE = "BLENDER_EEVEE" if "--eevee" in argv else "CYCLES"
os.makedirs(OUT, exist_ok=True)

FPS = 24
DURATION_S = 55
FRAMES = FPS * DURATION_S          # 480
RES = (540, 960) if PREVIEW else (1080, 1920)
SAMPLES = 24 if PREVIEW else 96
FUR_DENSITY = 160000 if PREVIEW else 230000   # strands per m^2
CUBE = 0.0175                                 # dice size (m)
N_SLICE_CUTS = 100                            # cuts 1..100 are parallel slices
TOTAL_CUTS = 1000
SEED = 7
rng = random.Random(SEED)

# Timeline (frames, 24 fps)
F_KNIFE_IN = 40        # knife starts entering from top-right
F_CUT1_TOP = 96        # blade touches the top of the head
F_CUT1_END = 210       # blade reaches the table -> counter = 1 (slow, ~5 s)
F_SPLIT = (222, 292)   # halves glide apart, then a close-up hold
F_STAGE2 = 360         # cuts 2..4   (2 s each)
S2, S2_HIT = 48, 27
F_STAGE3 = 512         # cuts 5..10  (1.25 s each)
S3, S3_HIT = 30, 16
F_STAGE4 = (705, 950)  # cuts 11..100
F_DICE = (965, 1195)   # cuts 101..1000, cubes released
F_END = FRAMES

# ----------------------------------------------------------------------------- helpers

def sock(coll, name, typ):
    for x in coll:
        if x.name == name and x.type == typ and getattr(x, "enabled", True):
            return x
    for x in coll:
        if x.name == name and x.type == typ:
            return x
    raise KeyError(name + "/" + typ)



def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease_in_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def lerp(a, b, t):
    return a + (b - a) * t


def new_obj(name, mesh, coll=None):
    ob = bpy.data.objects.new(name, mesh)
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def shade_smooth(mesh):
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    if hasattr(mesh, "use_auto_smooth"):          # Blender < 4.1
        mesh.use_auto_smooth = True
        mesh.auto_smooth_angle = math.radians(50)


def mesh_from_eval(ob, name):
    dg = bpy.context.evaluated_depsgraph_get()
    m = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    m.name = name
    return m


def add_ellipsoid(bm, center, radii, rot=None, segs=40, rings=24):
    r = bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    M = Matrix.Translation(center)
    if rot is not None:
        M = M @ rot.to_4x4()
    M = M @ Matrix.Diagonal((*radii, 1.0))
    bmesh.ops.transform(bm, matrix=M, verts=r["verts"])


def capsule_rot(a, b):
    d = (Vector(b) - Vector(a)).normalized()
    return Vector((0, 0, 1)).rotation_difference(d).to_matrix()


# ----------------------------------------------------------------------------- reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, FRAMES
scene.unit_settings.system = "METRIC"

# ----------------------------------------------------------------------------- materials

def principled(name, color, rough=0.5, metal=0.0, sheen=0.0, sub=0.0, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    for key in ("Sheen Weight", "Sheen"):
        if key in b.inputs:
            b.inputs[key].default_value = sheen
            break
    for key in ("Subsurface Weight", "Subsurface"):
        if key in b.inputs:
            b.inputs[key].default_value = sub
            break
    for key in ("Specular IOR Level", "Specular"):
        if key in b.inputs:
            b.inputs[key].default_value = spec
            break
    return m


def add_bump(mat, scale=120.0, strength=0.35, detail=8.0, stretch=None, wave=False):
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    if stretch:
        mp.inputs["Scale"].default_value = stretch
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    if wave:
        tx = nt.nodes.new("ShaderNodeTexWave")
        tx.inputs["Scale"].default_value = scale
        tx.inputs["Distortion"].default_value = 14.0
        tx.inputs["Detail"].default_value = detail
    else:
        tx = nt.nodes.new("ShaderNodeTexNoise")
        tx.inputs["Scale"].default_value = scale
        tx.inputs["Detail"].default_value = detail
    nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = strength
    nt.links.new(tx.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return tx


def fabric(name, c_dark, c_light, scale=260.0, rough=0.85):
    """Plush base colour under the fur: noise-mottled two-tone with a soft sheen."""
    m = principled(name, c_dark, rough=rough, sheen=1.0, spec=0.25)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tx = add_bump(m, scale=scale, strength=0.45)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c_dark, 1)
    ramp.color_ramp.elements[1].color = (*c_light, 1)
    nt.links.new(tx.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


def strand(name, root, tip):
    """Fur strand shader: darker roots, lighter sun-kissed tips, per-strand variation."""
    m = principled(name, tip, rough=0.55, sheen=0.6, spec=0.35)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    hi = nt.nodes.new("ShaderNodeHairInfo")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*root, 1)
    ramp.color_ramp.elements[1].color = (*tip, 1)
    nt.links.new(hi.outputs["Intercept"], ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 0.35
    nt.links.new(ramp.outputs["Color"], sock(mix.inputs, "A", "RGBA"))
    rr = nt.nodes.new("ShaderNodeValToRGB")
    rr.color_ramp.elements[0].color = (0.75, 0.72, 0.68, 1)
    rr.color_ramp.elements[1].color = (1.1, 1.05, 1.0, 1)
    nt.links.new(hi.outputs["Random"], rr.inputs["Fac"])
    nt.links.new(rr.outputs["Color"], sock(mix.inputs, "B", "RGBA"))
    nt.links.new(sock(mix.outputs, "Result", "RGBA"), b.inputs["Base Color"])
    return m


BROWN_D, BROWN_L = (0.10, 0.036, 0.010), (0.28, 0.115, 0.032)
BEIGE_D, BEIGE_L = (0.40, 0.28, 0.16), (0.62, 0.47, 0.30)
M_FUR = fabric("PlushBrown", BROWN_D, BROWN_L)
M_BEIGE = fabric("PlushBeige", BEIGE_D, BEIGE_L)
M_STUFF = fabric("CottonStuffing", (0.80, 0.78, 0.74), (0.97, 0.96, 0.93), scale=90.0, rough=0.95)
for nd in M_STUFF.node_tree.nodes:
    if nd.type == "BUMP":
        nd.inputs["Strength"].default_value = 1.0
        nd.inputs["Distance"].default_value = 0.004
    if nd.type == "TEX_NOISE":
        nd.inputs["Scale"].default_value = 38.0
        nd.inputs["Detail"].default_value = 12.0
        nd.inputs["Roughness"].default_value = 0.72
M_STRAND = strand("FurStrand", (0.05, 0.016, 0.005), (0.40, 0.17, 0.05))
M_STRAND_BEIGE = strand("FurStrandBeige", (0.30, 0.20, 0.11), (0.72, 0.57, 0.40))
M_FIBER = strand("CottonFiber", (0.86, 0.85, 0.82), (1.0, 1.0, 0.98))
M_EYE = principled("EyeGloss", (0.006, 0.005, 0.005), rough=0.04, spec=0.9)
M_NOSE = fabric("NoseFelt", (0.07, 0.025, 0.015), (0.16, 0.07, 0.04), scale=400.0, rough=0.6)
M_THREAD = principled("Thread", (0.04, 0.02, 0.015), rough=0.7)
M_BOW = fabric("RedSatin", (0.22, 0.002, 0.005), (0.55, 0.008, 0.015), scale=40.0, rough=0.3)
for _k in ("Sheen Weight", "Sheen"):
    if _k in M_BOW.node_tree.nodes["Principled BSDF"].inputs:
        M_BOW.node_tree.nodes["Principled BSDF"].inputs[_k].default_value = 0.25
M_STEEL = principled("BrushedSteel", (0.58, 0.59, 0.61), rough=0.24, metal=1.0)
for _k, _v in (("Anisotropic", 0.7), ("Anisotropic Rotation", 0.25)):
    if _k in M_STEEL.node_tree.nodes["Principled BSDF"].inputs:
        M_STEEL.node_tree.nodes["Principled BSDF"].inputs[_k].default_value = _v
add_bump(M_STEEL, scale=700.0, strength=0.08, stretch=(1, 0.02, 1))
M_HANDLE = principled("KnifeHandle", (0.012, 0.012, 0.014), rough=0.32, spec=0.6)
M_RIVET = principled("Rivet", (0.85, 0.85, 0.85), rough=0.15, metal=1.0)


def wood_mat(name, c1, c2, scale=3.0, plank=True):
    m = principled(name, c1, rough=0.55)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.25, 4.0, 1.0)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.inputs["Scale"].default_value = scale
    wv.inputs["Distortion"].default_value = 6.0
    wv.inputs["Detail"].default_value = 6.0
    wv.inputs["Detail Roughness"].default_value = 0.7
    nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 30.0
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "MULTIPLY"
    nt.links.new(wv.outputs["Fac"], mx.inputs[0])
    nt.links.new(nz.outputs["Fac"], mx.inputs[1])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(wv.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.12
    nt.links.new(mx.outputs["Value"], bp.inputs["Height"])
    if plank:
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Mortar Size"].default_value = 0.004
        br.inputs["Brick Width"].default_value = 1.4
        br.inputs["Row Height"].default_value = 0.16
        br.inputs["Color1"].default_value = (1, 1, 1, 1)
        br.inputs["Color2"].default_value = (1, 1, 1, 1)
        br.inputs["Mortar"].default_value = (0, 0, 0, 1)
        mp2 = nt.nodes.new("ShaderNodeMapping")
        mp2.inputs["Rotation"].default_value = (0, 0, math.pi / 2)
        nt.links.new(tc.outputs["Object"], mp2.inputs["Vector"])
        nt.links.new(mp2.outputs["Vector"], br.inputs["Vector"])
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs[0].default_value = 0.85
        nt.links.new(ramp.outputs["Color"], sock(mul.inputs, "A", "RGBA"))
        nt.links.new(br.outputs["Color"], sock(mul.inputs, "B", "RGBA"))
        nt.links.new(sock(mul.outputs, "Result", "RGBA"), b.inputs["Base Color"])
        add = nt.nodes.new("ShaderNodeMath")
        add.operation = "ADD"
        nt.links.new(mx.outputs["Value"], add.inputs[0])
        nt.links.new(br.outputs["Fac"], add.inputs[1])
        nt.links.new(add.outputs["Value"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


M_TABLE = wood_mat("TableWood", (0.12, 0.045, 0.016), (0.32, 0.14, 0.05))
M_FENCE = wood_mat("FenceWood", (0.42, 0.26, 0.14), (0.62, 0.42, 0.25), plank=False)
M_POT = fabric("Terracotta", (0.45, 0.17, 0.07), (0.62, 0.28, 0.13), scale=30.0, rough=0.8)
M_LEAF = fabric("Leaves", (0.04, 0.12, 0.02), (0.18, 0.32, 0.05), scale=8.0, rough=0.6)
M_LEAF2 = fabric("Leaves2", (0.10, 0.20, 0.03), (0.35, 0.45, 0.10), scale=12.0, rough=0.6)


def emissive(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m


M_GLOW = emissive("LanternGlow", (1.0, 0.55, 0.2), 5.0)
M_BOKEH = emissive("Bokeh", (1.0, 0.78, 0.45), 6.0)
FLOWER_MATS = [principled("FlowerPink", (0.85, 0.25, 0.55), 0.5, sheen=0.5),
               principled("FlowerPurple", (0.45, 0.25, 0.75), 0.5, sheen=0.5),
               principled("FlowerWhite", (0.9, 0.85, 0.9), 0.5, sheen=0.5)]

# ----------------------------------------------------------------------------- the bear
print("[teddy] building bear")
LEGS = [((s * 0.058, -0.010, 0.052), (s * 0.088, -0.135, 0.047), 0.046) for s in (-1, 1)]
ARMS = [((s * 0.088, -0.004, 0.205), (s * 0.128, -0.072, 0.092), 0.034) for s in (-1, 1)]
EARS = [(s * 0.074, 0.006, 0.383) for s in (-1, 1)]
HEAD_C, HEAD_R = Vector((0, -0.004, 0.302)), (0.100, 0.090, 0.090)
MUZZLE_C, MUZZLE_R = Vector((0, -0.079, 0.283)), (0.043, 0.033, 0.031)

bm = bmesh.new()
add_ellipsoid(bm, (0, 0.012, 0.135), (0.104, 0.090, 0.125))          # body
add_ellipsoid(bm, (0, -0.030, 0.120), (0.088, 0.070, 0.090))         # tummy
add_ellipsoid(bm, HEAD_C, HEAD_R)                                    # head
add_ellipsoid(bm, MUZZLE_C, MUZZLE_R)                                # muzzle
for c in EARS:
    add_ellipsoid(bm, c, (0.034, 0.017, 0.032))
for a, b, r in ARMS + LEGS:
    a, b = Vector(a), Vector(b)
    add_ellipsoid(bm, (a + b) / 2, (r, r, (b - a).length / 2 + r), capsule_rot(a, b))
for a, b, r in LEGS:                                                 # foot pads bulge forward
    add_ellipsoid(bm, Vector(b) + Vector((0, -0.012, 0.002)), (0.038, 0.020, 0.040))
raw = bpy.data.meshes.new("bear_raw")
bm.to_mesh(raw)
bm.free()
tmp = new_obj("bear_tmp", raw)
rm = tmp.modifiers.new("remesh", "REMESH")
rm.mode = "VOXEL"
rm.voxel_size = 0.0030 if PREVIEW else 0.0024
sm = tmp.modifiers.new("smooth", "LAPLACIANSMOOTH")
sm.iterations = 6
sm.lambda_factor = 1.2
body_mesh = mesh_from_eval(tmp, "bear_body")
bpy.data.objects.remove(tmp)

# flatten the bottom so it sits on the table and paint the beige regions
bm = bmesh.new()
bm.from_mesh(body_mesh)
for v in bm.verts:
    if v.co.z < 0.003:
        v.co.z = 0.003 + (v.co.z - 0.003) * 0.15


def in_ell(p, c, r, k=1.0):
    q = Vector(((p.x - c[0]) / r[0], (p.y - c[1]) / r[1], (p.z - c[2]) / r[2]))
    return q.length < k


bm.normal_update()
for f in bm.faces:
    p, n = f.calc_center_median(), f.normal
    beige = False
    if in_ell(p, MUZZLE_C, MUZZLE_R, 1.18) and n.y < -0.15:
        beige = True
    for c in EARS:
        if in_ell(p, c, (0.024, 0.03, 0.022), 1.0) and n.y < -0.35:
            beige = True
    for a, b, r in LEGS:
        if (p - Vector(b)).length < 0.05 and n.y < -0.55 and p.y < Vector(b).y - 0.02:
            beige = True
    f.material_index = 1 if beige else 0
bm.to_mesh(body_mesh)
bm.free()
for m in (M_FUR, M_BEIGE, M_STUFF):
    body_mesh.materials.append(m)


def part_mesh(name, build, mats, remesh=None):
    bm = bmesh.new()
    build(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if remesh:
        ob = new_obj(name + "_tmp", me)
        r = ob.modifiers.new("r", "REMESH")
        r.mode = "VOXEL"
        r.voxel_size = remesh
        s = ob.modifiers.new("s", "SMOOTH")
        s.iterations = 4
        me2 = mesh_from_eval(ob, name)
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)
        me = me2
    for m in mats:
        me.materials.append(m)
    return me


def head_surface_y(x, z, c, r):
    k = 1 - (x - c[0]) ** 2 / r[0] ** 2 - (z - c[2]) ** 2 / r[2] ** 2
    return c[1] - r[1] * math.sqrt(max(k, 0.0))


def build_eyes(bm):
    for s in (-1, 1):
        x, z = s * 0.036, 0.322
        y = head_surface_y(x, z, HEAD_C, HEAD_R) + 0.004
        add_ellipsoid(bm, (x, y, z), (0.0135, 0.0105, 0.0135), segs=32, rings=16)


def build_nose(bm):
    add_ellipsoid(bm, (0, MUZZLE_C.y - MUZZLE_R[1] + 0.004, 0.296), (0.0175, 0.0115, 0.012), segs=32, rings=16)


def build_mouth(bm):
    path_c = [(0, 0.287), (0, 0.276)]
    smile = [(-0.018, 0.279), (-0.011, 0.2715), (0, 0.270), (0.011, 0.2715), (0.018, 0.279)]

    def tube(pts2d):
        pts = []
        for x, z in pts2d:
            y = head_surface_y(x, z, MUZZLE_C, MUZZLE_R) - 0.0006
            pts.append(Vector((x, y, z)))
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            add_ellipsoid(bm, (a + b) / 2, (0.0013, 0.0013, (b - a).length / 2 + 0.0012),
                          capsule_rot(a, b), segs=10, rings=8)
    tube(path_c)
    tube(smile)


def build_bow(bm):
    cy, cz = -0.088, 0.212
    add_ellipsoid(bm, (0, cy - 0.006, cz), (0.013, 0.010, 0.0125), segs=24, rings=12)
    for s in (-1, 1):
        r = bmesh.ops.create_cube(bm, size=2.0)
        for v in r["verts"]:
            t = (v.co.x + 1) / 2
            h = lerp(0.006, 0.026, t ** 0.75)
            d = lerp(0.004, 0.0085, t)
            x = s * lerp(0.004, 0.056, t)
            pinch = 1.0 - 0.18 * math.sin(math.pi * t)
            v.co = Vector((x, cy + v.co.y * d, cz + v.co.z * h * pinch - 0.004 * t * t))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


PARTS = [
    ("body", body_mesh, 2),
    ("eyes", part_mesh("eyes", build_eyes, [M_EYE]), 0),
    ("nose", part_mesh("nose", build_nose, [M_NOSE]), 0),
    ("mouth", part_mesh("mouth", build_mouth, [M_THREAD], remesh=0.0005), 0),
    ("bow", part_mesh("bow", build_bow, [M_BOW], remesh=0.0013), 0),
]

# turn the bear to face the camera; the cut planes stay world-aligned (x = const), so the
# blade face and the opened seams are seen at a good angle while the bear still looks at us
BEAR_YAW = math.radians(22)
_rot = Matrix.Rotation(BEAR_YAW, 4, "Z")
for _, _me, _ in PARTS:
    _me.transform(_rot)
    _me.update()

# ----------------------------------------------------------------------------- cut plan (the impact list)
# 97 vertical planes (x = const) + 3 horizontal planes (z = const) = 100 cuts, then 900 dicing cuts.
xs = [v.co.x for v in body_mesh.vertices]
XMIN, XMAX = min(xs), max(xs)
D = (XMAX - XMIN) / 99
slice_ks = list(range(-48, 49))                       # 97 vertical planes, one through the centre
SLICE_X = [k * D for k in slice_ks]
CENTER = slice_ks.index(0)
k_of = {k: i for i, k in enumerate(slice_ks)}
H_PLANES = [0.12, 0.215, 0.33]                        # belly, neck, through the head
h_of = {z: j for j, z in enumerate(H_PLANES)}

order_stage2 = [("x", -25), ("x", 26), ("z", 0.215)]                                 # cuts 2..4
order_stage3 = [("x", 40), ("z", 0.12), ("x", -40), ("x", 13), ("z", 0.33), ("x", -12)]  # cuts 5..10
used = {0} | {k for a_, k in order_stage2 + order_stage3 if a_ == "x"}
order_stage4 = [k for k in slice_ks if k not in used]   # cuts 11..100, sweep left -> right


def mk(axis, k, **kw):
    return dict(axis=axis, b=k_of[k] if axis == "x" else h_of[k], **kw)


cuts = []   # axis, b(plane index), frame(contact = counter +1), gap, open(frames), kind
cuts.append(mk("x", 0, frame=F_CUT1_END, gap=0.055, open=(F_SPLIT[0], F_SPLIT[1]), kind="slow"))
f = F_STAGE2
for ax, k in order_stage2:
    cuts.append(mk(ax, k, frame=f + S2_HIT, gap=0.010 if ax == "x" else 0.014, open=(f + S2_HIT + 3, f + S2_HIT + 14), kind="slice", start=f))
    f += S2
f = F_STAGE3
for ax, k in order_stage3:
    cuts.append(mk(ax, k, frame=f + S3_HIT, gap=0.007 if ax == "x" else 0.009, open=(f + S3_HIT + 2, f + S3_HIT + 9), kind="chop", start=f))
    f += S3
n4 = len(order_stage4)
for i, k in enumerate(order_stage4):
    fr = F_STAGE4[0] + (F_STAGE4[1] - F_STAGE4[0]) * (i + 0.5) / n4
    cuts.append(mk("x", k, frame=fr, gap=0.0016, open=(fr + 0.3, fr + 2.5), kind="rapid"))
assert len(cuts) == N_SLICE_CUTS, len(cuts)

# cell (i, j): x-slab i between SLICE_X[i-1] and SLICE_X[i], z-layer j between H_PLANES[j-1] and H_PLANES[j]
N_SLABS = len(SLICE_X) + 1
slab_lo = [-1.0] + SLICE_X
slab_hi = SLICE_X + [1.0]
slab_cx = [((max(lo, XMIN) + min(hi, XMAX)) / 2) for lo, hi in zip(slab_lo, slab_hi)]
N_LAYERS = len(H_PLANES) + 1
lay_lo = [-1.0] + H_PLANES
lay_hi = H_PLANES + [2.0]


def cut_t(c, frame):
    a, b = c["open"]
    return ease_in_out_cubic((frame - a) / max(b - a, 1e-6))


def slab_offset(i, frame):
    """x shift of slab i: each opened vertical seam pushes its two sides apart."""
    off = 0.0
    for c in cuts:
        if c["axis"] != "x":
            continue
        t = cut_t(c, frame)
        if t > 0:
            off += c["gap"] * t * (0.5 if i >= c["b"] + 1 else -0.5)
    return off


def layer_offset(j, frame):
    """y shift of layer j: after a horizontal cut the part above slides forward, showing the stuffing."""
    off = 0.0
    for c in cuts:
        if c["axis"] != "z":
            continue
        t = cut_t(c, frame)
        if t > 0 and j >= c["b"] + 1:
            off -= c["gap"] * t
    return off

# ----------------------------------------------------------------------------- slicing


def slice_bm(src, planes, cap_mat, nudge):
    """planes: [(axis 0|2, value, keep_positive_side)]; cut + fill every plane, caps get cap_mat."""
    bm = src.copy()
    for axis, val, keep_pos in planes:
        if abs(val) >= 1.0:
            continue
        no = [0, 0, 0]
        no[axis] = 1
        co = [0, 0, 0]
        co[axis] = val
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        if not geom:
            break
        res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=co, plane_no=no,
                                     clear_inner=keep_pos, clear_outer=not keep_pos)
        edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if not edges:
            continue
        fn = [-v for v in no] if keep_pos else no
        fill = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges, normal=fn)
        cap_verts = set()
        for fc in fill["geom"]:
            if isinstance(fc, bmesh.types.BMFace):
                fc.material_index = cap_mat
                fc.smooth = False
                cap_verts.update(fc.verts)
        if nudge:     # small parts' caps sit a hair in front of the body's cap (no z-fighting)
            d = -nudge if keep_pos else nudge
            for v in cap_verts:
                v.co[axis] += d
    if not bm.faces:
        bm.free()
        return None
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


print("[teddy] slicing into %d x %d cells" % (N_SLABS, N_LAYERS))
src_bms = []
for name, me, capm in PARTS:
    b = bmesh.new()
    b.from_mesh(me)
    src_bms.append((name, b, capm, me.materials[:]))

_bb = bmesh.new()
_bb.from_mesh(body_mesh)
BODY_BVH = BVHTree.FromBMesh(_bb)
_bb.free()


def add_tufts(bm, side, zlo, zhi):
    """Lumpy cotton tufts bulging out of the centre cut (side=-1: left half's cap faces +x)."""
    rr = random.Random(int(99 + side + zlo * 1000))
    placed = 0
    for _ in range(4000):
        if placed >= 14:
            break
        y, z = rr.uniform(-0.2, 0.15), rr.uniform(max(zlo, 0.0) + 0.012, min(zhi, 0.45) - 0.012)
        p = Vector((0.0, y, z))
        loc, nrm, idx, dist = BODY_BVH.find_nearest(p)
        if loc is None or (p - loc).dot(nrm) > 0 or dist < 0.013:
            continue
        r = rr.uniform(0.006, min(0.012, dist - 0.004))
        res = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        ph = [rr.uniform(0, 6.3) for _ in range(4)]
        for v in res["verts"]:
            n = v.co.normalized()
            d = 1 + 0.18 * math.sin(n.y * 9 + ph[0]) * math.sin(n.z * 8 + ph[1]) + 0.08 * math.sin(n.x * 21 + ph[2])
            v.co = Vector((-side * 0.0015 + n.x * r * 0.55 * d, y + n.y * r * d, z + n.z * r * 0.9 * d))
        faces = {f for v in res["verts"] for f in v.link_faces}
        for f in faces:
            f.material_index = 2
            f.smooth = True
        placed += 1


col_bear = bpy.data.collections.new("Bear")
scene.collection.children.link(col_bear)
ALL_MATS = [M_FUR, M_BEIGE, M_STUFF, M_EYE, M_NOSE, M_THREAD, M_BOW]
slabs = []        # (i, j, object)
for i in range(N_SLABS):
    xparts = []
    for name, b, capm, mats in src_bms:
        sx = slice_bm(b, [(0, slab_lo[i], True), (0, slab_hi[i], False)], capm, 0.0 if name == "body" else 0.00025)
        if sx is not None:
            xparts.append((name, sx, capm, mats))
    for j in range(N_LAYERS):
        out = bmesh.new()
        for name, sx, capm, mats in xparts:
            s_ = slice_bm(sx, [(2, lay_lo[j], True), (2, lay_hi[j], False)], capm, 0.0 if name == "body" else 0.00025)
            if s_ is None:
                continue
            remap = [ALL_MATS.index(m) for m in mats]     # local -> shared material slots
            for fc in s_.faces:
                fc.material_index = remap[fc.material_index]
            tmpm = bpy.data.meshes.new("t")
            s_.to_mesh(tmpm)
            s_.free()
            out.from_mesh(tmpm)
            bpy.data.meshes.remove(tmpm)
        if not out.faces:
            out.free()
            continue
        if i in (CENTER, CENTER + 1):
            add_tufts(out, -1 if i == CENTER else 1, lay_lo[j], lay_hi[j])
        me = bpy.data.meshes.new("cell_%03d_%d" % (i, j))
        out.to_mesh(me)
        out.free()
        for m in ALL_MATS:
            me.materials.append(m)
        shade_smooth(me)
        for p in me.polygons:      # flat caps flat, everything else (incl. cotton tufts) smooth
            if p.material_index == 2 and (abs(p.normal.x) > 0.995 or abs(p.normal.z) > 0.995):
                p.use_smooth = False
        ob = new_obj("cell_%03d_%d" % (i, j), me, col_bear)
        slabs.append((i, j, ob))
    for _, sx, _, _ in xparts:
        sx.free()
for _, b, _, _ in src_bms:
    b.free()
print("[teddy] %d cells" % len(slabs))

# ----------------------------------------------------------------------------- fur (geometry nodes)


def new_node(N, *types):
    for t in types:
        try:
            return N.new(t)
        except RuntimeError:
            continue
    raise RuntimeError("no node type among %s" % (types,))


def make_fur_group(name="TeddyFur", cube=False):
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    join = N.new("GeometryNodeJoinGeometry")
    L.new(gi.outputs[0], join.inputs[0])
    L.new(join.outputs[0], go.inputs[0])
    mi = N.new("GeometryNodeInputMaterialIndex")

    # (material index, density, length, root radius, tilt, curl, strand material, seed)
    specs = [
        (0, FUR_DENSITY, 0.0125, 0.00036, 1.0, 0.0045, M_STRAND, 1),
        (1, FUR_DENSITY * 0.9, 0.0040, 0.00024, 0.7, 0.0012, M_STRAND_BEIGE, 2),
        (2, FUR_DENSITY * 0.30, 0.0050, 0.00018, 1.20, 0.0035, M_FIBER, 3),
    ]
    if cube:
        specs = [(0, FUR_DENSITY * 0.8, 0.0075, 0.00032, 0.9, 0.003, M_STRAND, 4),
                 (1, FUR_DENSITY * 0.8, 0.0035, 0.00024, 0.7, 0.001, M_STRAND_BEIGE, 5),
                 (2, FUR_DENSITY * 0.10, 0.0035, 0.00018, 1.2, 0.003, M_FIBER, 6)]
    for idx, dens, length, rad, tilt, curl, mat, seed in specs:
        cmp = N.new("ShaderNodeMath")
        cmp.operation = "COMPARE"
        cmp.inputs[1].default_value = idx
        cmp.inputs[2].default_value = 0.5
        L.new(mi.outputs[0], cmp.inputs[0])
        dist = N.new("GeometryNodeDistributePointsOnFaces")
        dist.distribute_method = "RANDOM"
        dist.inputs["Density"].default_value = dens
        dist.inputs["Seed"].default_value = seed
        L.new(gi.outputs[0], dist.inputs["Mesh"])
        L.new(cmp.outputs[0], dist.inputs["Selection"])

        line = N.new("GeometryNodeCurvePrimitiveLine")
        line.inputs["End"].default_value = (0, 0, length)
        rs = N.new("GeometryNodeResampleCurve")
        rs.inputs["Count"].default_value = 4
        L.new(line.outputs[0], rs.inputs["Curve"])

        # direction = surface normal + random tilt, then aligned (works on Blender 4.0 .. 5.x)
        rv = N.new("FunctionNodeRandomValue")
        rv.data_type = "FLOAT_VECTOR"
        sock(rv.inputs, "Min", "VECTOR").default_value = (-tilt, -tilt, -tilt)
        sock(rv.inputs, "Max", "VECTOR").default_value = (tilt, tilt, tilt)
        rv.inputs["Seed"].default_value = seed + 10
        dirv = N.new("ShaderNodeVectorMath")
        dirv.operation = "ADD"
        L.new(dist.outputs["Normal"], dirv.inputs[0])
        L.new(sock(rv.outputs, "Value", "VECTOR"), dirv.inputs[1])
        al = new_node(N, "FunctionNodeAlignRotationToVector", "FunctionNodeAlignEulerToVector")
        al.axis = "Z"
        L.new(dirv.outputs[0], al.inputs["Vector"])
        rot = al
        rs_ = N.new("FunctionNodeRandomValue")
        rs_.data_type = "FLOAT"
        sock(rs_.inputs, "Min", "VALUE").default_value = 0.55
        sock(rs_.inputs, "Max", "VALUE").default_value = 1.15
        rs_.inputs["Seed"].default_value = seed + 20

        inst = N.new("GeometryNodeInstanceOnPoints")
        L.new(dist.outputs["Points"], inst.inputs["Points"])
        L.new(rs.outputs[0], inst.inputs["Instance"])
        L.new(rot.outputs[0], inst.inputs["Rotation"])
        L.new(sock(rs_.outputs, "Value", "VALUE"), inst.inputs["Scale"])
        real = N.new("GeometryNodeRealizeInstances")
        L.new(inst.outputs[0], real.inputs[0])

        # curl / clumping: noise offset that grows towards the tip
        sp = N.new("GeometryNodeSetPosition")
        nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 160.0
        sub = N.new("ShaderNodeVectorMath")
        sub.operation = "SUBTRACT"
        sub.inputs[1].default_value = (0.5, 0.5, 0.5)
        L.new(nz.outputs["Color"], sub.inputs[0])
        par = N.new("GeometryNodeSplineParameter")
        mul = N.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = curl
        L.new(par.outputs["Factor"], mul.inputs[0])
        sc = N.new("ShaderNodeVectorMath")
        sc.operation = "SCALE"
        L.new(sub.outputs[0], sc.inputs[0])
        L.new(mul.outputs[0], sc.inputs["Scale"])
        L.new(real.outputs[0], sp.inputs["Geometry"])
        L.new(sc.outputs[0], sp.inputs["Offset"])

        # tapered radius
        taper = N.new("ShaderNodeMapRange")
        taper.inputs["To Min"].default_value = rad
        taper.inputs["To Max"].default_value = rad * 0.25
        L.new(par.outputs["Factor"], taper.inputs["Value"])
        cr = N.new("GeometryNodeSetCurveRadius")
        L.new(sp.outputs[0], cr.inputs["Curve"])
        L.new(taper.outputs["Result"], cr.inputs["Radius"])
        sm_ = N.new("GeometryNodeSetMaterial")
        sm_.inputs["Material"].default_value = mat
        L.new(cr.outputs[0], sm_.inputs["Geometry"])
        L.new(sm_.outputs[0], join.inputs[0])
    return ng


FUR = make_fur_group()
for _, _, ob in slabs:
    md = ob.modifiers.new("fur", "NODES")
    md.node_group = FUR

# ----------------------------------------------------------------------------- knife
print("[teddy] knife")
# Oversized hero knife: the blade is taller than the bear, so it stays visible through the whole cut
BL, BH = 0.64, 0.50          # blade length (local Y) and height (local Z)
TIP_Y, HEEL_Y = -0.38, 0.26


def build_knife():
    bm = bmesh.new()
    nseg = 48
    verts = []
    for i in range(nseg + 1):
        t = i / nseg
        y = lerp(HEEL_Y, TIP_Y, t)
        # chef's-knife profile: straight spine, belly curving up to the tip
        spine = BH * (1.0 - 0.08 * t) - BH * 0.85 * max(0.0, (t - 0.72) / 0.28) ** 1.6
        edge = BH * 0.95 * max(0.0, (t - 0.55) / 0.45) ** 2.2
        edge = min(edge, spine - 0.0006)
        thick = 0.0035 * (1 - 0.6 * t) + 0.0004
        col = []
        hgt = spine - edge
        for z, w in ((edge, 0.0001), (edge + min(hgt * 0.1, 0.02), thick * 0.55), (edge + hgt * 0.95, thick), (spine, thick * 0.8)):
            col.append((bm.verts.new((-w, y, z)), bm.verts.new((w, y, z))))
        verts.append(col)
    for i in range(nseg):
        a, b = verts[i], verts[i + 1]
        for j in range(3):
            for side in (0, 1):
                q = [a[j][side], b[j][side], b[j + 1][side], a[j + 1][side]]
                bm.faces.new(q if side else q[::-1])
        bm.faces.new([a[3][0], a[3][1], b[3][1], b[3][0]])          # spine
        bm.faces.new([a[0][1], a[0][0], b[0][0], b[0][1]])          # edge
    bm.faces.new([p[0] for p in verts[0]] + [p[1] for p in verts[0]][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("blade")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M_STEEL)
    shade_smooth(me)

    hb = bmesh.new()
    r = bmesh.ops.create_cube(hb, size=1.0)
    bmesh.ops.transform(hb, matrix=Matrix.Translation((0, HEEL_Y + 0.15, BH * 0.80)) @
                        Matrix.Diagonal((0.04, 0.30, 0.065, 1)), verts=r["verts"])
    hm = bpy.data.meshes.new("handle_raw")
    hb.to_mesh(hm)
    hb.free()
    hob = new_obj("handle_tmp", hm)
    bv = hob.modifiers.new("b", "BEVEL")
    bv.width = 0.015
    bv.segments = 4
    ss = hob.modifiers.new("s", "SUBSURF")
    ss.levels = 2
    handle = mesh_from_eval(hob, "handle")
    bpy.data.objects.remove(hob)
    handle.materials.append(M_HANDLE)
    shade_smooth(handle)

    rb = bmesh.new()
    for y in (HEEL_Y + 0.06, HEEL_Y + 0.15, HEEL_Y + 0.24):
        r = bmesh.ops.create_cone(rb, cap_ends=True, segments=16, radius1=0.008, radius2=0.008, depth=0.043)
        bmesh.ops.transform(rb, matrix=Matrix.Translation((0, y, BH * 0.80)) @ Matrix.Rotation(math.pi / 2, 4, "Y"),
                            verts=r["verts"])
    r = bmesh.ops.create_cube(rb, size=1.0)       # bolster
    bmesh.ops.transform(rb, matrix=Matrix.Translation((0, HEEL_Y + 0.008, BH * 0.62)) @
                        Matrix.Diagonal((0.03, 0.025, BH * 0.76, 1)), verts=r["verts"])
    rme = bpy.data.meshes.new("rivets")
    rb.to_mesh(rme)
    rb.free()
    rme.materials.append(M_RIVET)

    knife = bpy.data.objects.new("Knife", None)
    scene.collection.objects.link(knife)
    for nm, m in (("Blade", me), ("Handle", handle), ("Rivets", rme)):
        o = new_obj(nm, m)
        o.parent = knife
    return knife


KNIFE = build_knife()
KNIFE_Y = 0.10

# ----------------------------------------------------------------------------- environment
print("[teddy] garden")
col_env = bpy.data.collections.new("Garden")
scene.collection.children.link(col_env)


def box(name, size, loc, mat, coll=col_env, bevel=0.0):
    bm = bmesh.new()
    r = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(loc) @ Matrix.Diagonal((*size, 1)), verts=r["verts"])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = new_obj(name, me, coll)
    if bevel:
        b = ob.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = 3
    return ob


TABLE = box("TableTop", (1.8, 1.3, 0.05), (0, 0.22, -0.025), M_TABLE, bevel=0.006)
box("TableApron", (1.7, 1.2, 0.06), (0, 0.22, -0.08), M_TABLE)

for i in range(-16, 17):                         # picket fence
    x = i * 0.14
    h = 0.95 + 0.04 * math.sin(i * 1.7)
    box("picket", (0.10, 0.025, h), (x, 1.55, -0.6 + h / 2), M_FENCE, bevel=0.01)
for z in (-0.35, 0.15):
    box("rail", (4.8, 0.03, 0.07), (0, 1.58, z), M_FENCE)


def blob(name, loc, rad, mat, seed, disp=0.35):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    rr = random.Random(seed)
    ph = [rr.uniform(0, 10) for _ in range(6)]
    for v in bm.verts:
        n = v.co.normalized()
        d = (math.sin(n.x * 7 + ph[0]) * math.sin(n.y * 6 + ph[1]) * math.sin(n.z * 8 + ph[2]) +
             0.5 * math.sin(n.x * 17 + ph[3]) * math.sin(n.z * 15 + ph[4]))
        v.co = Vector((n.x * rad[0], n.y * rad[1], n.z * rad[2])) * (1 + disp * 0.3 * d)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    shade_smooth(me)
    return new_obj(name, me, col_env)


for i in range(14):                               # hedge / bushes behind the fence
    x = -2.4 + i * 0.37
    blob("bush", (x, 2.3 + rng.uniform(-0.2, 0.3), 0.1 + rng.uniform(0, 0.4)),
         (0.45, 0.35, 0.55 + rng.uniform(0, 0.3)), M_LEAF if i % 2 else M_LEAF2, i)


def flower_cluster(cx, cy, cz, n, seed):
    rr = random.Random(seed)
    for _ in range(n):
        p = (cx + rr.gauss(0, 0.09), cy + rr.gauss(0, 0.06), cz + rr.uniform(0, 0.28))
        blob("flower", p, (0.025, 0.025, 0.018), rr.choice(FLOWER_MATS), rr.randint(0, 999), 0.6)


for sx, sy in ((-0.62, 0.72), (0.70, 0.62), (-1.05, 1.05), (1.15, 1.0)):   # pots with plants
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=0.10, radius2=0.14, depth=0.2)
    bmesh.ops.translate(bm, vec=(sx, sy, 0.1), verts=bm.verts)
    me = bpy.data.meshes.new("pot")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M_POT)
    new_obj("pot", me, col_env)
    blob("plant", (sx, sy, 0.3), (0.18, 0.16, 0.16), M_LEAF2, int(sx * 100), 0.5)
    flower_cluster(sx, sy - 0.04, 0.33, 9, int(sy * 100))

# lantern (left), glowing
box("lantern_post", (0.03, 0.03, 0.6), (-0.95, 0.9, 0.3), M_HANDLE)
box("lantern_glass", (0.11, 0.11, 0.16), (-0.95, 0.9, 0.68), M_GLOW)
box("lantern_cap", (0.15, 0.15, 0.03), (-0.95, 0.9, 0.775), M_HANDLE)
lamp = bpy.data.lights.new("LanternLight", "POINT")
lamp.energy = 25
lamp.color = (1.0, 0.6, 0.28)
lamp.shadow_soft_size = 0.05
lo = bpy.data.objects.new("LanternLight", lamp)
lo.location = (-0.95, 0.82, 0.68)
col_env.objects.link(lo)

for i in range(40):                                # far bokeh sparkles (sun through leaves)
    p = (rng.uniform(-3, 3), rng.uniform(3.5, 6), rng.uniform(0.2, 2.5))
    blob("bokeh", p, (0.03, 0.03, 0.03), M_BOKEH, i, 0)

# world: warm golden-hour gradient
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
wn = world.node_tree
bg = wn.nodes["Background"]
bg.inputs["Strength"].default_value = 0.7
tc = wn.nodes.new("ShaderNodeTexCoord")
sep = wn.nodes.new("ShaderNodeSeparateXYZ")
wn.links.new(tc.outputs["Generated"], sep.inputs[0])
ramp = wn.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.45
ramp.color_ramp.elements[0].color = (0.55, 0.32, 0.14, 1)
ramp.color_ramp.elements[1].position = 0.75
ramp.color_ramp.elements[1].color = (0.45, 0.55, 0.65, 1)
wn.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
wn.links.new(ramp.outputs["Color"], bg.inputs["Color"])

# lights
def light(name, kind, loc, rot, energy, color, size=0.5):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind == "AREA":
        ld.size = size
    elif kind == "SUN":
        ld.angle = math.radians(2.5)
    else:
        ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    ob.rotation_euler = rot
    scene.collection.objects.link(ob)
    return ob


light("SunBacklight", "SUN", (2, 3, 3), (math.radians(-62), math.radians(28), math.radians(150)), 3.2, (1.0, 0.70, 0.42))
light("Key", "AREA", (-0.55, -0.85, 0.75), (math.radians(58), 0, math.radians(-33)), 30, (1.0, 0.86, 0.70), 0.9)
light("Fill", "AREA", (0.9, -0.6, 0.35), (math.radians(75), 0, math.radians(55)), 14, (0.85, 0.88, 1.0), 1.2)
light("Rim", "AREA", (0.15, 0.7, 0.7), (math.radians(-55), 0, math.radians(175)), 40, (1.0, 0.72, 0.45), 0.6)
light("KnifeGlint", "AREA", (0.6, -0.5, 0.95), (math.radians(40), math.radians(20), math.radians(50)), 20, (1, 0.95, 0.9), 0.3)
light("ReflectionCard", "AREA", (0.9, -1.1, 1.3), (math.radians(50), 0, math.radians(40)), 25, (1.0, 0.93, 0.85), 1.6)   # bright streak in the blade

# ----------------------------------------------------------------------------- dice (1000-cut stage)
print("[teddy] dicing")
dg = bpy.context.evaluated_depsgraph_get()
bvh_parts = {}
for name, me, _ in PARTS:
    b = bmesh.new()
    b.from_mesh(me)
    b.faces.ensure_lookup_table()
    mats = [ALL_MATS.index(me.materials[f.material_index]) for f in b.faces]
    bvh_parts[name] = (BVHTree.FromBMesh(b), mats)
    b.free()


def inside(tree, p):
    loc, nrm, idx, dist = tree.find_nearest(p)
    if loc is None:
        return False, None, None, None
    return (p - loc).dot(nrm) < 0, dist, idx, nrm


cube_mesh_cache = {}


def cube_mesh(face_mats):
    """Rounded cube whose 6 faces carry their own material (fur outside, cotton inside)."""
    key = tuple(face_mats)
    if key in cube_mesh_cache:
        return cube_mesh_cache[key]
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=CUBE * 0.9)
    dirs = [Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((0, 0, -1))]
    for f in bm.faces:
        n = f.normal
        k = max(range(6), key=lambda j: n.dot(dirs[j]))
        f.material_index = face_mats[k]
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=CUBE * 0.08, segments=2, affect="EDGES")
    me = bpy.data.meshes.new("cube")
    bm.to_mesh(me)
    bm.free()
    for m in ALL_MATS:
        me.materials.append(m)
    shade_smooth(me)
    cube_mesh_cache[key] = me
    return me


DIRS = [Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((0, 0, -1))]
col_cubes = bpy.data.collections.new("Cubes")
scene.collection.children.link(col_cubes)
cubes = []
nx = int((XMAX - XMIN) / CUBE) + 2
for ix in range(nx):
    x = XMIN + (ix + 0.5) * CUBE
    for iy in range(int(0.34 / CUBE) + 2):
        y = -0.20 + (iy + 0.5) * CUBE
        for iz in range(int(0.45 / CUBE) + 2):
            z = (iz + 0.5) * CUBE + 0.0005
            p = Vector((x, y, z))
            mat = None
            for name in ("eyes", "nose", "bow"):
                ins, _, idx, _ = inside(bvh_parts[name][0], p)
                if ins:
                    mat = [ALL_MATS.index({"eyes": M_EYE, "nose": M_NOSE, "bow": M_BOW}[name])] * 6
                    break
            if mat is None:
                ins, dist, idx, nrm = inside(bvh_parts["body"][0], p)
                if not ins:
                    continue
                if dist < CUBE * 0.8:
                    skin = bvh_parts["body"][1][idx]
                    mat = [skin if nrm.dot(d) > 0.05 else 2 for d in DIRS]
                else:
                    mat = [2] * 6
            cubes.append((p, mat))
print("[teddy] %d cubes" % len(cubes))


def layer_index(z):
    for j in range(N_LAYERS):
        if lay_lo[j] <= z < lay_hi[j]:
            return j
    return N_LAYERS - 1


def slab_index(x):
    for i in range(N_SLABS):
        if slab_lo[i] <= x < slab_hi[i]:
            return i
    return N_SLABS - 1


def wave_frame(x):
    """The dicing knife sweeps right -> left across the bear."""
    t = (XMAX - x) / (XMAX - XMIN)
    return F_DICE[0] + (F_DICE[1] - F_DICE[0]) * max(0.0, min(1.0, t))


CUBE_FUR = make_fur_group("CubeFur", cube=True)
cube_objs = []
for n, (p, mat) in enumerate(cubes):
    si = slab_index(p.x)
    wf = wave_frame(p.x)
    ob = new_obj("cube_%04d" % n, cube_mesh(mat), col_cubes)
    ob.location = (p.x + slab_offset(si, F_DICE[0]), p.y + layer_offset(layer_index(p.z), F_DICE[0]), p.z)
    ob.rotation_euler = (rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04))
    ob["release"] = int(math.ceil(wf))
    md = ob.modifiers.new("fur", "NODES")
    md.node_group = CUBE_FUR
    cube_objs.append(ob)

# ----------------------------------------------------------------------------- rigid bodies
print("[teddy] rigid bodies")
bpy.ops.rigidbody.world_add()
rw = scene.rigidbody_world
rw.collection = bpy.data.collections.new("RigidBodyWorld")
rw.substeps_per_frame = 20
rw.solver_iterations = 20
rw.point_cache.frame_start = F_DICE[0] - 2
rw.point_cache.frame_end = F_END


for o in [TABLE] + cube_objs:
    rw.collection.objects.link(o)
TABLE.rigid_body.type = "PASSIVE"
TABLE.rigid_body.collision_shape = "BOX"
TABLE.rigid_body.friction = 0.8
TABLE.rigid_body.collision_margin = 0.0005
for ob in cube_objs:
    rb = ob.rigid_body
    rb.type = "ACTIVE"
    rb.collision_shape = "BOX"
    rb.mass = 0.004
    rb.friction = 0.9
    rb.restitution = 0.05
    rb.collision_margin = 0.0004
    rb.linear_damping = 0.3
    rb.angular_damping = 0.5
    rel = ob["release"]
    rb.kinematic = True
    rb.keyframe_insert("kinematic", frame=rel - 1)
    rb.kinematic = False
    rb.keyframe_insert("kinematic", frame=rel)
    ob.hide_render = True
    ob.keyframe_insert("hide_render", frame=rel - 1)
    ob.hide_render = False
    ob.keyframe_insert("hide_render", frame=rel)
    ob.hide_viewport = False

# ----------------------------------------------------------------------------- animate slabs
print("[teddy] animating slabs")
for i, j, ob in slabs:
    hide_f = int(math.ceil(wave_frame(slab_cx[i])))
    last = None
    for fr in range(1, F_DICE[1] + 2):
        off = (slab_offset(i, fr), layer_offset(j, fr))
        if last is None or abs(off[0] - last[0]) + abs(off[1] - last[1]) > 1e-7 or fr in (1, hide_f):
            ob.location.x, ob.location.y = off
            ob.keyframe_insert("location", index=0, frame=fr)
            ob.keyframe_insert("location", index=1, frame=fr)
            last = off
    ob.hide_render = False
    ob.keyframe_insert("hide_render", frame=hide_f - 1)
    ob.hide_render = True
    ob.keyframe_insert("hide_render", frame=hide_f)

# ----------------------------------------------------------------------------- animate knife (from the impact list)
print("[teddy] animating knife")
Z_TOP = 0.50      # blade edge height when hovering over the bear
Z_HOME = (0.75, 1.05)


def boundary_x(c, frame):
    """World x of a cut plane at a given frame (moves as earlier seams open)."""
    return SLICE_X[c["b"]] + slab_offset(c["b"], frame)


def kf_knife(fr, x, z, tilt=0.0, roll=0.0, y=None):
    KNIFE.location = (x, KNIFE_Y if y is None else y, z)
    KNIFE.rotation_euler = (tilt, roll, 0)
    KNIFE.keyframe_insert("location", frame=fr)
    KNIFE.keyframe_insert("rotation_euler", frame=fr)


TILT = math.radians(-6)   # tip slightly down, rocking chop
home = (Z_HOME[0], Z_HOME[1])
kf_knife(1, *home, TILT * 2, math.radians(8))
kf_knife(F_KNIFE_IN, *home, TILT * 2, math.radians(8))
c1 = cuts[0]
x1 = boundary_x(c1, F_CUT1_TOP)
kf_knife(F_CUT1_TOP - 6, x1, Z_TOP + 0.02, TILT, 0)
kf_knife(F_CUT1_TOP, x1, Z_TOP - 0.05, TILT, 0)
for k in range(1, 9):     # slow, steady pass through the bear with a gentle rocking motion
    t = k / 8
    fr = lerp(F_CUT1_TOP, F_CUT1_END, t)
    z = lerp(Z_TOP - 0.05, 0.0015, ease_in_out_cubic(t) * 0.7 + t * 0.3)
    kf_knife(fr, x1, z, TILT * (1 - t) + math.radians(1.5) * math.sin(t * 6), 0)
kf_knife(F_CUT1_END + 4, x1, 0.0015, 0, 0)
kf_knife(F_SPLIT[0] + 2, x1 + 0.01, 0.12, TILT, 0)
kf_knife(F_SPLIT[1], *home, TILT * 2, math.radians(8))
kf_knife(F_STAGE2 - 6, *home, TILT * 2, math.radians(8))

HROLL = math.pi / 2     # blade lying flat, edge pointing to -x: a horizontal cut slides right -> left
for c in cuts[1:10]:
    s, hit = c["start"], c["frame"]
    slow = c["kind"] == "slice"
    if c["axis"] == "x":
        x = boundary_x(c, hit)
        kf_knife(s + (3 if slow else 2), x, 0.47 if slow else 0.46, TILT, 0)
        kf_knife(hit, x, 0.0015, 0, 0)
        kf_knife(hit + 1, x, 0.0015, 0, 0)
    else:
        z = H_PLANES[c["b"]]
        y = KNIFE_Y + layer_offset(c["b"], hit)
        kf_knife(s + (4 if slow else 2), XMAX + 0.07 + slab_offset(N_SLABS - 1, hit), z, 0, HROLL, y)
        kf_knife(hit, XMIN - 0.035 + slab_offset(0, hit), z, 0, HROLL, y)
        kf_knife(hit + 1, XMIN - 0.04 + slab_offset(0, hit), z, 0, HROLL, y)

# rapid: subframe keys so motion blur shows a ghosted, blurred blade
f4 = [c for c in cuts if c["kind"] == "rapid"]
for c in f4:
    x = boundary_x(c, c["frame"])
    kf_knife(c["frame"] - 0.33, x, 0.45, TILT, 0)
    kf_knife(c["frame"], x, 0.0015, 0, 0)

# dicing: the blade blurs right -> left; 900 cuts, counter driven by wave progress
n_dice = TOTAL_CUTS - N_SLICE_CUTS
dice_hits = [F_DICE[0] + (F_DICE[1] - F_DICE[0]) * (i + 0.5) / n_dice for i in range(n_dice)]
for j in range(0, n_dice, 12):       # alternating vertical chops and horizontal swipes at the dicing front
    fr = dice_hits[j]
    x = XMAX - (XMAX - XMIN) * (fr - F_DICE[0]) / (F_DICE[1] - F_DICE[0]) + 0.01
    phase = (j // 12) % 4
    if phase == 0:
        kf_knife(fr, x, 0.44, TILT, math.radians(rng.uniform(-4, 4)))
    elif phase == 1:
        kf_knife(fr, x, 0.002, TILT, 0)
    elif phase == 2:
        kf_knife(fr, x + 0.05, rng.uniform(0.05, 0.38), 0, HROLL)
    else:
        kf_knife(fr, x - 0.06, rng.uniform(0.05, 0.38), 0, HROLL)
kf_knife(F_DICE[1] + 10, *home, TILT * 2, math.radians(8))
kf_knife(F_END, home[0] + 0.1, home[1] + 0.2, TILT * 2, math.radians(8))

# ----------------------------------------------------------------------------- cotton fluff bits
print("[teddy] fluff")
fluff_me = None
bmf = bmesh.new()
bmesh.ops.create_icosphere(bmf, subdivisions=2, radius=1.0)
for v in bmf.verts:
    v.co *= 1 + rng.uniform(-0.35, 0.35)
fluff_me = bpy.data.meshes.new("fluff")
bmf.to_mesh(fluff_me)
bmf.free()
fluff_me.materials.append(M_STUFF)
shade_smooth(fluff_me)


def spawn_fluff(f0, pos, vel, size):
    ob = new_obj("fluff", fluff_me, col_bear)
    ob.scale = (size, size, size * 0.8)
    ob.hide_render = True
    ob.keyframe_insert("hide_render", frame=1)
    ob.hide_render = False
    ob.keyframe_insert("hide_render", frame=int(f0))
    p, v = Vector(pos), Vector(vel)
    fr = f0
    while fr < F_DICE[0] + 5:
        ob.location = p
        ob.rotation_euler = (fr * 0.05 * vel[0] * 40, fr * 0.04, 0)
        ob.keyframe_insert("location", frame=fr)
        ob.keyframe_insert("rotation_euler", frame=fr)
        if p.z <= size * 0.8 + 0.0005 and v.length < 0.01:
            break
        dt = 1.0 / FPS
        v.z -= 9.81 * dt * 0.35        # cotton: light and floaty
        v *= 0.93
        p = p + v * dt
        if p.z < size * 0.8:
            p.z = size * 0.8
            v = Vector((v.x * 0.3, v.y * 0.3, 0))
        fr += 1
    ob.hide_render = True
    ob.keyframe_insert("hide_render", frame=F_DICE[0] + 6)


for k in range(26):                     # puffs while the first cut goes through
    t = rng.uniform(0.15, 1.0)
    fr = int(lerp(F_CUT1_TOP, F_CUT1_END, t))
    z = lerp(0.40, 0.03, t)
    spawn_fluff(fr, (rng.uniform(-0.006, 0.006), rng.uniform(-0.13, -0.06), z),
                (rng.uniform(-0.12, 0.12), rng.uniform(-0.18, -0.05), rng.uniform(0.0, 0.12)),
                rng.uniform(0.0018, 0.0042))
for c in cuts[1:10]:
    for _ in range(3):
        if c["axis"] == "x":
            x, z = boundary_x(c, c["frame"]), rng.uniform(0.05, 0.3)
        else:
            x, z = rng.uniform(-0.08, 0.08), H_PLANES[c["b"]]
        spawn_fluff(int(c["frame"]) - rng.randint(0, 4), (x, rng.uniform(-0.12, -0.05), z),
                    (rng.uniform(-0.08, 0.08), rng.uniform(-0.12, -0.03), rng.uniform(0.0, 0.08)),
                    rng.uniform(0.0016, 0.003))

# ----------------------------------------------------------------------------- camera
print("[teddy] camera")
cam_d = bpy.data.cameras.new("Cam")
cam_d.lens = 50
cam_d.sensor_fit = "VERTICAL"
cam_d.sensor_height = 36
cam_d.clip_start = 0.02
cam_d.dof.use_dof = True
cam_d.dof.aperture_fstop = 2.4
cam_d.dof.aperture_blades = 7
cam = bpy.data.objects.new("Camera", cam_d)
scene.collection.objects.link(cam)
scene.camera = cam
target = bpy.data.objects.new("CamTarget", None)
scene.collection.objects.link(target)
tr = cam.constraints.new("TRACK_TO")
tr.target = target
tr.track_axis = "TRACK_NEGATIVE_Z"
tr.up_axis = "UP_Y"
cam_d.dof.focus_object = target

# (frame, distance, yaw deg, height, target xyz): slow push-in, no cuts, slight orbit
CAM_KEYS = [
    (1, 1.30, 38, 0.44, (0, -0.02, 0.23)),
    (F_CUT1_TOP, 1.10, 40, 0.42, (0, -0.02, 0.22)),
    (F_CUT1_END, 1.02, 42, 0.40, (0, -0.02, 0.21)),
    (F_SPLIT[1] + 10, 0.80, 46, 0.36, (0, -0.03, 0.21)),      # close-up on the two halves
    (F_STAGE2 + 4, 0.86, 45, 0.37, (0, -0.03, 0.21)),
    (F_STAGE3, 0.98, 43, 0.40, (0, -0.02, 0.21)),
    (F_STAGE4[1], 1.04, 41, 0.42, (0, -0.02, 0.21)),
    (F_DICE[1], 1.00, 43, 0.46, (0, -0.04, 0.12)),
    (F_END, 0.80, 47, 0.36, (0, -0.05, 0.06)),               # final close-up on the cube pile
]


def cam_at(fr):
    for (f0, *a), (f1, *b) in zip(CAM_KEYS, CAM_KEYS[1:]):
        if f0 <= fr <= f1:
            t = ease((fr - f0) / (f1 - f0))
            d, yaw, h = (lerp(a[i], b[i], t) for i in range(3))
            tg = Vector(a[3]).lerp(Vector(b[3]), t)
            return d, yaw, h, tg
    d, yaw, h, tg = CAM_KEYS[-1][1:]
    return d, yaw, h, Vector(tg)


for fr in range(1, F_END + 1):
    d, yaw, h, tg = cam_at(fr)
    sway = 0.004 * math.sin(fr / 37.0)                 # handheld-smooth drift
    a = math.radians(yaw)
    cam.location = (tg.x + d * math.sin(a) + sway, tg.y - d * math.cos(a), h + sway * 0.5)
    target.location = tg
    cam.keyframe_insert("location", frame=fr)
    target.keyframe_insert("location", frame=fr)

# ----------------------------------------------------------------------------- render settings


def tryset(obj, attr, val):
    try:
        setattr(obj, attr, val)
    except (AttributeError, TypeError, ValueError):
        pass


r = scene.render
r.engine = ENGINE
r.resolution_x, r.resolution_y = RES
r.resolution_percentage = 100
r.image_settings.file_format = "PNG"
r.image_settings.color_mode = "RGB"
r.image_settings.compression = 30
r.use_persistent_data = False
r.use_motion_blur = True
r.motion_blur_shutter = 0.5
tryset(r, "hair_type", "STRIP")
tryset(r, "hair_subdiv", 1)
vt = [v.identifier for v in bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items]
scene.view_settings.view_transform = "AgX" if "AgX" in vt else "Filmic"
for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
    tryset(scene.view_settings, "look", look)
scene.view_settings.exposure = -0.1
if ENGINE != "CYCLES":
    e = scene.eevee
    for k, v in dict(taa_render_samples=SAMPLES, use_gtao=True, gtao_distance=0.08, use_bloom=True,
                     bloom_threshold=1.2, bloom_intensity=0.04, use_ssr=True, ssr_quality=0.5,
                     use_soft_shadows=True, shadow_cube_size="1024", shadow_cascade_size="2048",
                     use_motion_blur=True, motion_blur_shutter=0.5, motion_blur_steps=1 if PREVIEW else 2,
                     bokeh_max_size=60, use_raytracing=True, use_shadows=True).items():
        tryset(e, k, v)
    for kind in ("SPHERE", "CUBE"):
        try:
            probe = bpy.data.lightprobes.new("Reflections", kind)
        except TypeError:
            continue
        po = bpy.data.objects.new("ReflectionProbe", probe)
        po.location = (0, -0.05, 0.3)
        tryset(probe, "influence_distance", 3.0)
        scene.collection.objects.link(po)
        break
else:
    c = scene.cycles
    c.device = "CPU"
    c.samples = SAMPLES
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.03
    c.use_denoising = True
    tryset(c, "denoiser", "OPENIMAGEDENOISE")
    tryset(c, "denoising_input_passes", "RGB_ALBEDO_NORMAL")
    tryset(c, "denoising_prefilter", "ACCURATE")
    c.max_bounces = 6
    c.diffuse_bounces = 2
    c.glossy_bounces = 3
    c.transmission_bounces = 2
    c.transparent_max_bounces = 4
    tryset(c, "use_light_tree", True)
    tryset(c, "blur_glossy", 1.0)
    tryset(c, "sample_clamp_indirect", 6.0)
    tryset(c, "tile_size", 512)          # low RAM: render in 512px tiles
    tryset(scene.cycles_curves, "shape", "RIBBONS")
    tryset(scene.cycles_curves, "subdivisions", 2)

# ----------------------------------------------------------------------------- bake + save + timeline
print("[teddy] baking rigid bodies")
scene.frame_set(1)
with bpy.context.temp_override(scene=scene, point_cache=rw.point_cache):
    bpy.ops.ptcache.bake(bake=True)
if ENGINE != "CYCLES" and bpy.app.version < (4, 2, 0):
    try:
        bpy.ops.scene.light_cache_bake()
    except Exception as ex:          # not fatal: SSR + world still give reflections
        print("[teddy] light cache bake skipped:", ex)

# per-frame counters + impact events for the overlay and sound (same impact list as the knife)
release = sorted(ob["release"] for ob in cube_objs)
frames = []
for fr in range(1, F_END + 1):
    n_cuts = sum(1 for c in cuts if c["frame"] <= fr) + sum(1 for h in dice_hits if h <= fr)
    n_cubes = sum(1 for rf in release if rf <= fr)
    frames.append(dict(frame=fr, cuts=n_cuts, cubes=n_cubes))
events = []
events.append(dict(type="knife_in", frame=F_KNIFE_IN))
events.append(dict(type="slow_slice", frame=F_CUT1_TOP, end=F_CUT1_END))
for n, c in enumerate(cuts):
    events.append(dict(type=c["kind"], frame=c["frame"], axis=c["axis"], n=n + 1))
events.append(dict(type="split", frame=F_SPLIT[0], end=F_SPLIT[1]))
for h in dice_hits:
    events.append(dict(type="dice", frame=h))
for rf in release:
    events.append(dict(type="cube_fall", frame=rf + 4 + rng.uniform(0, 8)))
events.append(dict(type="knife_out", frame=F_DICE[1] + 4))
meta = dict(fps=FPS, frames=F_END, width=RES[0], height=RES[1], total_cuts=TOTAL_CUTS,
            n_cubes=len(cube_objs), per_frame=frames, events=events)
with open(os.path.join(OUT, "timeline.json"), "w") as fh:
    json.dump(meta, fh)

r.filepath = os.path.join(OUT, "frames", "f_")
scene["motion_blur_frames"] = [F_CUT1_TOP - 8, F_CUT1_END + 2, F_STAGE2, F_END]   # [a,b, c,d] ranges
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "scene.blend"))
print("[teddy] saved", os.path.join(OUT, "scene.blend"), "cubes:", len(cube_objs))
