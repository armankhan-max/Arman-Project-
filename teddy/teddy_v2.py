"""Teddy Bear vs 1000 Cuts, v2 (reference style: studio board, seam lines, crumble into cubes).

Each round starts with a fresh teddy bear on a cutting board in a dark brick studio:
  the knife makes N fast cuts (vertical x, vertical y, horizontal z). Each cut shows on the
  plush only as a thin seam line. Then the bear crumbles into the cells those cuts made.
Rounds: 5, 15, 40, 100, 300, 1000 cuts. Rounds 1-2 use real sliced pieces (rigid bodies);
later rounds use instanced cubes with a procedural collapse.

  python teddy_v2.py --out OUTDIR [--preview]     (pip bpy module)
"""
import bpy  # noqa: I001
import bmesh
import json
import math
import os
import random
import sys
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OUT = os.path.abspath(argv[argv.index("--out") + 1]) if "--out" in argv else os.path.abspath("v2_out")
PREVIEW = "--preview" in argv
os.makedirs(OUT, exist_ok=True)
FPS = 24
RES = (720, 1280)
SAMPLES = 16
rng = np.random.default_rng(5)
random.seed(5)

ROUNDS = [  # n cuts, frames per cut, intro, gap between axis groups, hold after cuts, collapse, hold after
    dict(n=5, per=13.0, intro=22, gap=10, after=10, collapse=46, hold=20, mode="pieces"),
    dict(n=15, per=5.5, intro=12, gap=8, after=8, collapse=48, hold=16, mode="pieces"),
    dict(n=40, per=2.5, intro=10, gap=6, after=6, collapse=44, hold=14, mode="cubes", cap=0.0),
    dict(n=100, per=1.25, intro=10, gap=6, after=6, collapse=44, hold=14, mode="cubes", cap=0.0),
    dict(n=300, per=0.5, intro=10, gap=6, after=6, collapse=46, hold=14, mode="cubes", cap=0.0045),
    dict(n=1000, per=0.17, intro=10, gap=6, after=8, collapse=52, hold=36, mode="cubes", cap=0.0036),
]


# ----------------------------------------------------------------------------- helpers
def sock(coll, name, typ):
    for x in coll:
        if x.name == name and x.type == typ and getattr(x, "enabled", True):
            return x
    for x in coll:
        if x.name == name and x.type == typ:
            return x
    raise KeyError(name + "/" + typ)


def new_node(N, *types):
    for t in types:
        try:
            return N.new(t)
        except RuntimeError:
            continue
    raise RuntimeError("no node type among %s" % (types,))


def tryset(obj, attr, val):
    try:
        setattr(obj, attr, val)
    except (AttributeError, TypeError, ValueError):
        pass


def lerp(a, b, t):
    return a + (b - a) * t


def new_obj(name, data, coll=None):
    ob = bpy.data.objects.new(name, data)
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def shade_smooth(mesh):
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))


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


def set_interp(kind):
    bpy.context.preferences.edit.keyframe_new_interpolation_type = kind


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS

# ----------------------------------------------------------------------------- materials


def principled(name, color, rough=0.5, metal=0.0, sheen=0.0, spec=0.5):
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
    for key in ("Specular IOR Level", "Specular"):
        if key in b.inputs:
            b.inputs[key].default_value = spec
            break
    return m


def add_bump(mat, scale=120.0, strength=0.35, detail=8.0, stretch=None):
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    if stretch:
        mp.inputs["Scale"].default_value = stretch
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
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
    m = principled(name, c_dark, rough=rough, sheen=1.0, spec=0.25)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tx = add_bump(m, scale=scale, strength=0.5)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c_dark, 1)
    ramp.color_ramp.elements[1].color = (*c_light, 1)
    nt.links.new(tx.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    for key in ("Sheen Tint",):
        if key in b.inputs and b.inputs[key].type == "RGBA":
            b.inputs[key].default_value = (*c_light, 1)
    return m


BROWN_D, BROWN_L = (0.075, 0.03, 0.011), (0.20, 0.09, 0.035)
BEIGE_D, BEIGE_L = (0.42, 0.29, 0.17), (0.64, 0.49, 0.32)
STUFF_C = (0.86, 0.85, 0.81)
M_FUR = fabric("PlushBrown", BROWN_D, BROWN_L, scale=700.0)
M_BEIGE = fabric("PlushBeige", BEIGE_D, BEIGE_L, scale=700.0)
M_STUFF = fabric("CottonStuffing", (0.78, 0.77, 0.73), (0.97, 0.96, 0.93), scale=40.0, rough=0.95)
for nd in M_STUFF.node_tree.nodes:
    if nd.type == "BUMP":
        nd.inputs["Strength"].default_value = 1.0
        nd.inputs["Distance"].default_value = 0.003
    if nd.type == "TEX_NOISE":
        nd.inputs["Detail"].default_value = 12.0
        nd.inputs["Roughness"].default_value = 0.72
M_EYE = principled("EyeGloss", (0.006, 0.005, 0.005), rough=0.04, spec=0.9)
M_NOSE = fabric("NoseFelt", (0.05, 0.02, 0.012), (0.13, 0.06, 0.035), scale=400.0, rough=0.6)
M_THREAD = principled("Thread", (0.04, 0.02, 0.015), rough=0.7)
M_BOW = fabric("RedSatin", (0.25, 0.004, 0.008), (0.60, 0.012, 0.02), scale=60.0, rough=0.35)
M_STEEL = principled("BrushedSteel", (0.62, 0.63, 0.65), rough=0.22, metal=1.0)
add_bump(M_STEEL, scale=700.0, strength=0.06, stretch=(0.02, 1, 1))
M_HANDLE = principled("HandleWood", (0.06, 0.025, 0.012), rough=0.45, spec=0.5)
add_bump(M_HANDLE, scale=60.0, strength=0.1, stretch=(0.1, 1, 1))
M_RIVET = principled("Rivet", (0.85, 0.85, 0.85), rough=0.15, metal=1.0)
ALL_MATS = [M_FUR, M_BEIGE, M_STUFF, M_EYE, M_NOSE, M_THREAD, M_BOW]
MAT_COL = [(0.14, 0.06, 0.022), (0.55, 0.40, 0.25), STUFF_C, (0.01, 0.01, 0.01), (0.07, 0.03, 0.02),
           (0.04, 0.02, 0.015), (0.45, 0.008, 0.015)]


def wood_board(name, c1, c2):
    m = principled(name, c1, rough=0.5)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.4, 7.0, 1.0)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.inputs["Scale"].default_value = 2.5
    wv.inputs["Distortion"].default_value = 5.0
    wv.inputs["Detail"].default_value = 5.0
    nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 40.0
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "MULTIPLY"
    nt.links.new(wv.outputs["Fac"], mx.inputs[0])
    nt.links.new(nz.outputs["Fac"], mx.inputs[1])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(mx.outputs["Value"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.05
    nt.links.new(mx.outputs["Value"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


M_BOARD = wood_board("BoardMaple", (0.42, 0.25, 0.12), (0.66, 0.46, 0.27))


def brick_wall(name):
    m = principled(name, (0.05, 0.055, 0.05), rough=0.9, spec=0.2)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = 4.5
    br.inputs["Mortar Size"].default_value = 0.012
    br.inputs["Brick Width"].default_value = 0.5
    br.inputs["Row Height"].default_value = 0.2
    br.inputs["Color1"].default_value = (0.022, 0.026, 0.024, 1)
    br.inputs["Color2"].default_value = (0.032, 0.038, 0.035, 1)
    br.inputs["Mortar"].default_value = (0.012, 0.013, 0.012, 1)
    mpw = nt.nodes.new("ShaderNodeMapping")
    mpw.inputs["Rotation"].default_value = (math.pi / 2, 0, 0)
    nt.links.new(tc.outputs["Object"], mpw.inputs["Vector"])
    nt.links.new(mpw.outputs["Vector"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.4
    bp.invert = True
    nt.links.new(br.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


M_WALL = brick_wall("BrickWall")
M_COUNTER = principled("Counter", (0.025, 0.024, 0.023), rough=0.6, spec=0.3)
add_bump(M_COUNTER, scale=30.0, strength=0.05)


def add_seams(mat):
    """Darken thin lines where the cut planes meet the surface. Plane counts/spacing are object props."""
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])

    def attr(name):
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_type = "OBJECT"
        a.attribute_name = name
        return a.outputs["Fac"]

    def math(op, a, b=None, clamp=False):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs[0]

    w = attr("sw")
    lines = None
    for ax, key in ((0, "x"), (1, "y"), (2, "z")):
        u = math("DIVIDE", math("SUBTRACT", sep.outputs[ax], attr(key + "0")), attr("s" + key))
        k = math("ROUND", u)
        d = math("MULTIPLY", math("ABSOLUTE", math("SUBTRACT", u, k)), attr("s" + key))
        line = math("SUBTRACT", 1.0, math("DIVIDE", d, w), clamp=True)
        valid = math("MULTIPLY", math("GREATER_THAN", k, 0.5), math("LESS_THAN", k, math("ADD", attr("n" + key), 0.5)))
        la = math("MULTIPLY", line, valid)
        lines = la if lines is None else math("MAXIMUM", lines, la)
    src = None
    for l in b.inputs["Base Color"].links:
        src = l.from_socket
    if src is None:
        rgb = nt.nodes.new("ShaderNodeRGB")
        rgb.outputs[0].default_value = b.inputs["Base Color"].default_value
        src = rgb.outputs[0]
    dark = nt.nodes.new("ShaderNodeMix")
    dark.data_type = "RGBA"
    dark.blend_type = "MULTIPLY"
    sock(dark.inputs, "Factor", "VALUE").default_value = 1.0
    nt.links.new(src, sock(dark.inputs, "A", "RGBA"))
    sock(dark.inputs, "B", "RGBA").default_value = (0.28, 0.26, 0.25, 1)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(lines, sock(mix.inputs, "Factor", "VALUE"))
    nt.links.new(src, sock(mix.inputs, "A", "RGBA"))
    nt.links.new(sock(dark.outputs, "Result", "RGBA"), sock(mix.inputs, "B", "RGBA"))
    nt.links.new(sock(mix.outputs, "Result", "RGBA"), b.inputs["Base Color"])


SEAM_MATS = []
for m in (M_FUR, M_BEIGE, M_EYE, M_NOSE, M_THREAD, M_BOW):
    c = m.copy()
    c.name = m.name + "_Seam"
    add_seams(c)
    SEAM_MATS.append(c)
BEAR_MATS = [SEAM_MATS[0], SEAM_MATS[1], M_STUFF, SEAM_MATS[2], SEAM_MATS[3], SEAM_MATS[4], SEAM_MATS[5]]

# ----------------------------------------------------------------------------- the bear
print("[v2] bear", flush=True)
LEGS = [((s * 0.058, -0.010, 0.052), (s * 0.088, -0.135, 0.047), 0.046) for s in (-1, 1)]
ARMS = [((s * 0.088, -0.004, 0.205), (s * 0.128, -0.072, 0.092), 0.034) for s in (-1, 1)]
EARS = [(s * 0.074, 0.006, 0.383) for s in (-1, 1)]
HEAD_C, HEAD_R = Vector((0, -0.004, 0.302)), (0.100, 0.090, 0.090)
MUZZLE_C, MUZZLE_R = Vector((0, -0.079, 0.283)), (0.043, 0.033, 0.031)

bm = bmesh.new()
add_ellipsoid(bm, (0, 0.012, 0.135), (0.104, 0.090, 0.125))
add_ellipsoid(bm, (0, -0.030, 0.120), (0.088, 0.070, 0.090))
add_ellipsoid(bm, HEAD_C, HEAD_R)
add_ellipsoid(bm, MUZZLE_C, MUZZLE_R)
for c in EARS:
    add_ellipsoid(bm, c, (0.034, 0.017, 0.032))
for a, b, r in ARMS + LEGS:
    a, b = Vector(a), Vector(b)
    add_ellipsoid(bm, (a + b) / 2, (r, r, (b - a).length / 2 + r), capsule_rot(a, b))
for a, b, r in LEGS:
    add_ellipsoid(bm, Vector(b) + Vector((0, -0.012, 0.002)), (0.038, 0.020, 0.040))
raw = bpy.data.meshes.new("bear_raw")
bm.to_mesh(raw)
bm.free()
tmp = new_obj("bear_tmp", raw)
rm = tmp.modifiers.new("remesh", "REMESH")
rm.mode = "VOXEL"
rm.voxel_size = 0.0032
sm = tmp.modifiers.new("smooth", "LAPLACIANSMOOTH")
sm.iterations = 6
sm.lambda_factor = 1.2
body_mesh = mesh_from_eval(tmp, "bear_body")
bpy.data.objects.remove(tmp)

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
AZ = math.radians(28)          # camera azimuth (front-right); the bear turns to face it
_rot = Matrix.Rotation(AZ, 4, "Z")
for _, _me, _ in PARTS:
    _me.transform(_rot)
    _me.update()

# joined, intact bear (with seam shader)
jb = bmesh.new()
for name, me, _ in PARTS:
    tm = me.copy()
    remap = [ALL_MATS.index(m) for m in me.materials]
    for p in tm.polygons:
        p.material_index = remap[p.material_index]
    jb.from_mesh(tm)
    bpy.data.meshes.remove(tm)
bear_me = bpy.data.meshes.new("bear")
jb.to_mesh(bear_me)
jb.free()
for m in BEAR_MATS:
    bear_me.materials.append(m)
shade_smooth(bear_me)
BEAR = new_obj("Bear", bear_me)

co = np.array([v.co[:] for v in bear_me.vertices])
XMIN, YMIN, ZMIN = co.min(0)
XMAX, YMAX, ZMAX = co.max(0)
ZMIN = 0.0
print("[v2] bounds", XMIN, XMAX, YMIN, YMAX, ZMAX, flush=True)

bvh = {}
for name, me, _ in PARTS:
    b = bmesh.new()
    b.from_mesh(me)
    b.faces.ensure_lookup_table()
    mats = [ALL_MATS.index(me.materials[f.material_index]) for f in b.faces]
    bvh[name] = (BVHTree.FromBMesh(b), mats)
    b.free()


def classify(p, s):
    """material index for a cell centred at p (or None if outside)."""
    for name in ("eyes", "nose", "bow"):
        loc, nrm, idx, dist = bvh[name][0].find_nearest(p)
        if loc is not None and (p - loc).dot(nrm) < 0:
            return bvh[name][1][idx]
    loc, nrm, idx, dist = bvh["body"][0].find_nearest(p)
    if loc is None or (p - loc).dot(nrm) > 0:
        return None
    return bvh["body"][1][idx] if dist < max(0.7 * s, 0.011) else 2


# ----------------------------------------------------------------------------- studio
print("[v2] studio", flush=True)


def box(name, size, loc, mat, rotz=0.0, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = new_obj(name, me)
    ob.location = loc
    ob.rotation_euler = (0, 0, rotz)
    if bevel:
        bv = ob.modifiers.new("b", "BEVEL")
        bv.width = bevel
        bv.segments = 3
    return ob


BOARD = box("Board", (0.80, 0.52, 0.03), (0.02, 0.02, -0.015), M_BOARD, rotz=AZ - math.radians(18), bevel=0.006)
COUNTER = box("Counter", (4.0, 3.0, 0.1), (0, 0.6, -0.08), M_COUNTER)
WALL = box("Wall", (5.0, 0.1, 3.0), (0, 0, 1.2), M_WALL)
WALL.location = Vector((-math.sin(AZ) * 1.1, math.cos(AZ) * 1.1, 1.2))
WALL.rotation_euler = (0, 0, AZ)

TARGET = Vector((0.0, 0.0, 0.165))
CAM_D, CAM_EL = 1.62, math.radians(27)
cam_d = bpy.data.cameras.new("Cam")
cam_d.lens = 50
cam_d.sensor_width = 36
cam_d.dof.use_dof = True
cam_d.dof.aperture_fstop = 5.6
CAM = new_obj("Camera", cam_d)
CAM.location = TARGET + CAM_D * Vector((math.sin(AZ) * math.cos(CAM_EL), -math.cos(AZ) * math.cos(CAM_EL), math.sin(CAM_EL)))
CAM.rotation_euler = (TARGET - CAM.location).to_track_quat("-Z", "Y").to_euler()
cam_d.dof.focus_distance = (TARGET - CAM.location).length
scene.camera = CAM


def light(name, kind, loc, energy, color, size=0.5):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind == "AREA":
        ld.size = size
    ob = new_obj(name, ld)
    ob.location = loc
    ob.rotation_euler = (TARGET - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


light("Key", "AREA", (-0.55, -0.95, 1.25), 70, (1.0, 0.93, 0.84), 1.3)
light("Fill", "AREA", (1.1, -0.7, 0.55), 12, (0.88, 0.92, 1.0), 1.2)
light("Rim", "AREA", (0.5, 0.75, 0.95), 45, (1.0, 0.88, 0.75), 0.8)
light("Top", "AREA", (0.0, 0.0, 1.4), 18, (1.0, 0.97, 0.92), 1.0)
world = bpy.data.worlds.new("W")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.004, 0.004, 1)
scene.world = world

# ----------------------------------------------------------------------------- knife
print("[v2] knife", flush=True)
KL, BH = 0.46, 0.075        # blade length along local +X (0 = heel, KL = tip), height along local +Z


def build_knife():
    bm = bmesh.new()
    nseg = 40
    cols = []
    for i in range(nseg + 1):
        t = i / nseg
        x = KL * t
        spine = BH * (1.0 - 0.1 * t) - BH * 0.85 * max(0.0, (t - 0.78) / 0.22) ** 1.5
        edge = BH * 0.9 * max(0.0, (t - 0.62) / 0.38) ** 2.3
        edge = min(edge, spine - 0.0006)
        th = 0.0022 * (1 - 0.5 * t) + 0.0003
        hgt = spine - edge
        col = []
        for z, w in ((edge, 0.00005), (edge + min(hgt * 0.12, 0.008), th * 0.5), (edge + hgt * 0.95, th), (spine, th * 0.8)):
            col.append((bm.verts.new((x, -w, z)), bm.verts.new((x, w, z))))
        cols.append(col)
    for i in range(nseg):
        a, b = cols[i], cols[i + 1]
        for j in range(3):
            bm.faces.new([a[j][0], b[j][0], b[j + 1][0], a[j + 1][0]])
            bm.faces.new([a[j][1], a[j + 1][1], b[j + 1][1], b[j][1]])
        bm.faces.new([a[3][0], b[3][0], b[3][1], a[3][1]])
        bm.faces.new([a[0][0], a[0][1], b[0][1], b[0][0]])
    bm.faces.new([p[0] for p in cols[0]] + [p[1] for p in cols[0]][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("blade")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M_STEEL)
    shade_smooth(me)

    hb = bmesh.new()
    r = bmesh.ops.create_cube(hb, size=1.0)
    bmesh.ops.transform(hb, matrix=Matrix.Translation((-0.075, 0, BH * 0.62)) @ Matrix.Diagonal((0.14, 0.022, 0.032, 1)),
                        verts=r["verts"])
    hm = bpy.data.meshes.new("handle_raw")
    hb.to_mesh(hm)
    hb.free()
    hob = new_obj("handle_tmp", hm)
    bv = hob.modifiers.new("b", "BEVEL")
    bv.width = 0.008
    bv.segments = 3
    ss = hob.modifiers.new("s", "SUBSURF")
    ss.levels = 2
    handle = mesh_from_eval(hob, "handle")
    bpy.data.objects.remove(hob)
    handle.materials.append(M_HANDLE)
    shade_smooth(handle)
    rb = bmesh.new()
    for x in (-0.03, -0.075, -0.12):
        r = bmesh.ops.create_cone(rb, cap_ends=True, segments=12, radius1=0.0045, radius2=0.0045, depth=0.0235)
        bmesh.ops.transform(rb, matrix=Matrix.Translation((x, 0, BH * 0.62)) @ Matrix.Rotation(math.pi / 2, 4, "X"),
                            verts=r["verts"])
    r = bmesh.ops.create_cube(rb, size=1.0)
    bmesh.ops.transform(rb, matrix=Matrix.Translation((-0.004, 0, BH * 0.55)) @ Matrix.Diagonal((0.01, 0.012, BH * 0.85, 1)),
                        verts=r["verts"])
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
ROT_X = Matrix.Rotation(math.pi / 2, 3, "Z")             # blade along +y, vertical: cuts planes x = c
ROT_Y = Matrix.Rotation(math.pi, 3, "Z")                 # blade along -x, vertical: cuts planes y = c
ROT_Z = Matrix(((-1, 0, 0), (0, 0, -1), (0, -1, 0)))     # blade along -x, flat, edge facing +y: planes z = c
Y_HEEL = YMIN - 0.07
X_HEEL = XMAX + 0.07
Z_TOP = ZMAX + 0.05


def pose(axis, c, h):
    """knife pose for a cut at plane coordinate c; h = edge height (x/y chops) or edge x (z slide)"""
    if axis == "x":
        return Vector((c, Y_HEEL, h)), ROT_X
    if axis == "y":
        return Vector((X_HEEL, c, h)), ROT_Y
    return Vector((X_HEEL, h, c)), ROT_Z


HOME = (Vector((0.55, -0.55, 0.85)), ROT_X)
set_interp("LINEAR")
_prev_eul = [None]


def key_knife(fr, p):
    loc, rot = p
    KNIFE.location = loc
    e = rot.to_euler("XYZ", _prev_eul[0]) if _prev_eul[0] is not None else rot.to_euler("XYZ")
    _prev_eul[0] = e
    KNIFE.rotation_euler = e
    KNIFE.keyframe_insert("location", frame=fr)
    KNIFE.keyframe_insert("rotation_euler", frame=fr)


# ----------------------------------------------------------------------------- timeline
print("[v2] timeline", flush=True)
EXT = {"x": (XMIN, XMAX), "y": (YMIN, YMAX), "z": (0.0, ZMAX)}
for k in ("x", "y", "z"):
    BEAR[k + "0"] = 0.0
    BEAR["s" + k] = 1.0
    BEAR["n" + k] = 0.0
BEAR["sw"] = 0.0007
f = 1.0
rounds = []
events = []
per_frame_cuts = {}
for ri, R in enumerate(ROUNDS):
    n = R["n"]
    nx = int(round(n * 0.4))
    nz = int(round(n * 0.3))
    ny = n - nx - nz
    counts = {"x": nx, "y": ny, "z": nz}
    sp = {k: (EXT[k][1] - EXT[k][0]) / (counts[k] + 1) for k in counts}
    start = int(f)
    R.update(start=start, counts=counts, sp=sp)
    set_interp("CONSTANT")
    for k in ("x", "y", "z"):
        BEAR[k + "0"] = EXT[k][0]
        BEAR["s" + k] = sp[k]
        BEAR["n" + k] = 0.0
        for prop in (k + "0", "s" + k, "n" + k):
            BEAR.keyframe_insert('["%s"]' % prop, frame=start)
    BEAR["sw"] = min(0.0007, 0.22 * min(sp.values()))
    BEAR.keyframe_insert('["sw"]', frame=start)
    BEAR.hide_render = False
    BEAR.keyframe_insert("hide_render", frame=start)
    set_interp("LINEAR")
    key_knife(start, HOME)
    t = start + R["intro"]
    impacts = []
    per = R["per"]
    slow = per >= 5
    first = True
    for axis in ("x", "y", "z"):
        m = counts[axis]
        if m == 0:
            continue
        if not first:
            # lift out of the bear and reorient
            lp, lr = _last
            key_knife(t, (Vector((lp.x, lp.y, Z_TOP + 0.12)) if axis != "z" else lp + Vector((0, 0, 0.12)), lr))
            t += R["gap"]
        first = False
        lo = EXT[axis][0]
        for j in range(1, m + 1):
            c = lo + j * sp[axis]
            if axis in ("x", "y"):
                key_knife(t, pose(axis, c, Z_TOP))
                hit = t + per * 0.55
                key_knife(hit, pose(axis, c, 0.002))
                _last = pose(axis, c, Z_TOP)
            else:
                xr, xl = YMIN - 0.03, YMAX + BH + 0.03
                a, b_ = (xr, xl) if (j % 2 == 1 or slow) else (xl, xr)
                key_knife(t, pose("z", c, a))
                hit = t + per * 0.45
                if slow:   # slice right -> left, lift, come back over the top for the next slice
                    key_knife(t + per * 0.62, pose("z", c, b_))
                    key_knife(t + per * 0.74, pose("z", ZMAX + 0.1, b_))
                    key_knife(t + per * 0.92, pose("z", ZMAX + 0.1, a))
                    _last = pose("z", ZMAX + 0.1, a)
                else:
                    key_knife(t + per * 0.98, pose("z", c, b_))
                    _last = pose("z", c, b_)
            impacts.append((hit, axis))
            t += per
        if axis in ("x", "y"):
            key_knife(t, _last)
    key_knife(t + R["after"] * 0.5, (Vector((_last[0].x, _last[0].y, Z_TOP + 0.3)), _last[1]))
    key_knife(t + R["after"] + 6, HOME)
    # seam reveal keys
    set_interp("CONSTANT")
    cnt = {"x": 0, "y": 0, "z": 0}
    for hit, axis in impacts:
        cnt[axis] += 1
        BEAR["n" + axis] = float(cnt[axis])
        BEAR.keyframe_insert('["n%s"]' % axis, frame=hit)
    set_interp("LINEAR")
    col_f = int(math.ceil(t + R["after"]))
    end = col_f + R["collapse"] + R["hold"]
    R.update(impacts=impacts, collapse_f=col_f, end=end, cut_end=t)
    for i, (hit, axis) in enumerate(impacts):
        events.append(dict(type="cut", frame=hit, round=ri, n=i + 1, axis=axis, slow=slow, per=per))
    events.append(dict(type="collapse", frame=col_f, round=ri, end=col_f + R["collapse"]))
    events.append(dict(type="knife_in", frame=start + 2, round=ri))
    set_interp("CONSTANT")
    BEAR.hide_render = True
    BEAR.keyframe_insert("hide_render", frame=col_f)
    set_interp("LINEAR")
    rounds.append(R)
    f = end + 1
FRAMES = int(f - 1)
scene.frame_start, scene.frame_end = 1, FRAMES
print("[v2] frames", FRAMES, flush=True)

# ----------------------------------------------------------------------------- pieces (rounds with real sliced cells)


def slice_bm(src, planes, cap_mat, nudge):
    bm = src.copy()
    for axis, val, keep_pos in planes:
        no = [0, 0, 0]
        no[axis] = 1
        co_ = [0, 0, 0]
        co_[axis] = val
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        if not geom:
            break
        res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=co_, plane_no=no,
                                     clear_inner=keep_pos, clear_outer=not keep_pos)
        edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if not edges:
            continue
        fn = [-v for v in no] if keep_pos else no
        fill = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges, normal=fn)
        cv = set()
        for fc in fill["geom"]:
            if isinstance(fc, bmesh.types.BMFace):
                fc.material_index = cap_mat
                fc.smooth = False
                cv.update(fc.verts)
        if nudge:
            d = -nudge if keep_pos else nudge
            for v in cv:
                v.co[axis] += d
    if not bm.faces:
        bm.free()
        return None
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


src_bms = []
for name, me, capm in PARTS:
    b = bmesh.new()
    b.from_mesh(me)
    src_bms.append((name, b, capm, me.materials[:]))

PARK = Vector((0, 0, -20))
piece_objs = []
any_pieces = False
for ri, R in enumerate(rounds):
    if R["mode"] != "pieces":
        continue
    any_pieces = True
    coll = bpy.data.collections.new("Pieces_%d" % ri)
    scene.collection.children.link(coll)
    edges = {}
    for k, ax in (("x", 0), ("y", 1), ("z", 2)):
        cuts = [EXT[k][0] + j * R["sp"][k] for j in range(1, R["counts"][k] + 1)]
        edges[ax] = [-1e3] + cuts + [1e3]
    objs = []

    def cut_range(b, ax, i, capm, nm):
        pl = []
        if edges[ax][i] > -1e2:
            pl.append((ax, edges[ax][i], True))
        if edges[ax][i + 1] < 1e2:
            pl.append((ax, edges[ax][i + 1], False))
        return slice_bm(b, pl, capm, 0.0 if nm == "body" else 0.00025)

    for i in range(len(edges[0]) - 1):
        xs = [(nm, cut_range(b, 0, i, capm, nm), capm, mats) for nm, b, capm, mats in src_bms]
        xs = [x for x in xs if x[1] is not None]
        for j in range(len(edges[1]) - 1):
            ys = [(nm, cut_range(b, 1, j, capm, nm), capm, mats) for nm, b, capm, mats in xs]
            ys = [y for y in ys if y[1] is not None]
            for k in range(len(edges[2]) - 1):
                out = bmesh.new()
                for nm, b, capm, mats in ys:
                    s_ = cut_range(b, 2, k, capm, nm)
                    if s_ is None:
                        continue
                    remap = [ALL_MATS.index(m) for m in mats]
                    for fc in s_.faces:
                        fc.material_index = remap[fc.material_index]
                    tm = bpy.data.meshes.new("t")
                    s_.to_mesh(tm)
                    s_.free()
                    out.from_mesh(tm)
                    bpy.data.meshes.remove(tm)
                if len(out.faces) < 20:
                    out.free()
                    continue
                cen = sum((v.co for v in out.verts), Vector()) / len(out.verts)
                bmesh.ops.translate(out, vec=-cen, verts=out.verts)
                me = bpy.data.meshes.new("piece")
                out.to_mesh(me)
                out.free()
                for m in ALL_MATS:
                    me.materials.append(m)
                shade_smooth(me)
                for p in me.polygons:
                    if p.material_index == 2:
                        p.use_smooth = False
                ob = new_obj("piece_%d_%03d" % (ri, len(objs)), me, coll)
                ob["home"] = cen[:]
                objs.append(ob)
            for _, b, _, _ in ys:
                b.free()
        for _, b, _, _ in xs:
            b.free()
    R["n_cubes"] = len(objs)
    R["pieces"] = objs
    print("[v2] round %d pieces: %d" % (ri, len(objs)), flush=True)

if any_pieces:
    bpy.ops.rigidbody.world_add()
    rw = scene.rigidbody_world
    rw.collection = bpy.data.collections.new("RBW")
    rw.substeps_per_frame = 15
    rw.solver_iterations = 20
    last_piece_end = max(R["end"] for R in rounds if R["mode"] == "pieces")
    rw.point_cache.frame_start = 1
    rw.point_cache.frame_end = last_piece_end + 2
    rw.collection.objects.link(BOARD)
    BOARD.rigid_body.type = "PASSIVE"
    BOARD.rigid_body.collision_shape = "BOX"
    BOARD.rigid_body.friction = 0.9
    BOARD.rigid_body.collision_margin = 0.001
    rw.collection.objects.link(COUNTER)
    COUNTER.rigid_body.type = "PASSIVE"
    COUNTER.rigid_body.collision_shape = "BOX"
    bpy.ops.object.effector_add(type="FORCE", location=(0.03, -0.05, 0.18))
    burst = bpy.context.object
    burst.field.falloff_type = "SPHERE"
    burst.field.shape = "POINT"
    burst.field.strength = 0.0
    set_interp("CONSTANT")
    burst.keyframe_insert("field.strength", frame=1)
    for R in rounds:
        if R["mode"] != "pieces":
            continue
        cf, end = R["collapse_f"], R["end"]
        burst.field.strength = 0.035
        burst.keyframe_insert("field.strength", frame=cf)
        burst.field.strength = 0.0
        burst.keyframe_insert("field.strength", frame=cf + 3)
        for ob in R["pieces"]:
            rw.collection.objects.link(ob)
            rb = ob.rigid_body
            rb.type = "ACTIVE"
            rb.collision_shape = "CONVEX_HULL"
            rb.mass = 0.05
            rb.friction = 0.85
            rb.restitution = 0.05
            rb.collision_margin = 0.0008
            rb.linear_damping = 0.25
            rb.angular_damping = 0.4
            home = Vector(ob["home"])
            ob.location = home + PARK
            rb.kinematic = True
            ob.hide_render = True
            ob.keyframe_insert("location", frame=1)
            rb.keyframe_insert("kinematic", frame=1)
            ob.keyframe_insert("hide_render", frame=1)
            ob.location = home
            ob.keyframe_insert("location", frame=cf - 1)
            ob.hide_render = False
            ob.keyframe_insert("hide_render", frame=cf)
            rb.kinematic = False
            rb.keyframe_insert("kinematic", frame=cf)
            rb.kinematic = True
            rb.keyframe_insert("kinematic", frame=end + 1)
            ob.location = home + PARK
            ob.keyframe_insert("location", frame=end + 1)
            ob.hide_render = True
            ob.keyframe_insert("hide_render", frame=end + 1)
    set_interp("LINEAR")

# ----------------------------------------------------------------------------- instanced cubes (procedural collapse)
proto_me = bpy.data.meshes.new("cube_proto")
pb = bmesh.new()
bmesh.ops.create_cube(pb, size=0.96)
bmesh.ops.bevel(pb, geom=pb.edges[:], offset=0.08, segments=2, affect="EDGES")
pb.to_mesh(proto_me)
pb.free()
shade_smooth(proto_me)
M_CUBE = principled("CubeMat", (0.5, 0.5, 0.5), rough=0.8, sheen=0.8, spec=0.3)
_nt = M_CUBE.node_tree
_at = _nt.nodes.new("ShaderNodeAttribute")
_at.attribute_type = "INSTANCER"
_at.attribute_name = "ccol"
_nt.links.new(_at.outputs["Color"], _nt.nodes["Principled BSDF"].inputs["Base Color"])
add_bump(M_CUBE, scale=900.0, strength=0.25)
proto_me.materials.append(M_CUBE)
PROTO = new_obj("CubeProto", proto_me)
PROTO.location = (0, 0, -30)
PROTO.hide_render = True


def collapse_group():
    ng = bpy.data.node_groups.new("Collapse", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")

    def named(name, dt):
        a = N.new("GeometryNodeInputNamedAttribute")
        a.data_type = dt
        a.inputs["Name"].default_value = name
        return sock(a.outputs, "Attribute", "VECTOR" if dt == "FLOAT_VECTOR" else "VALUE")

    pos = N.new("GeometryNodeInputPosition")
    tv = N.new("ShaderNodeValue")
    tv.name = "Tval"
    tv.outputs[0].default_value = 0.0
    sub = N.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    L.new(tv.outputs[0], sub.inputs[0])
    L.new(named("del", "FLOAT"), sub.inputs[1])
    div = N.new("ShaderNodeMath")
    div.operation = "DIVIDE"
    div.use_clamp = True
    L.new(sub.outputs[0], div.inputs[0])
    div.inputs[1].default_value = 0.55
    sq = N.new("ShaderNodeMath")
    sq.operation = "POWER"
    L.new(div.outputs[0], sq.inputs[0])
    sq.inputs[1].default_value = 1.7
    mix = N.new("ShaderNodeMix")
    mix.data_type = "VECTOR"
    L.new(sq.outputs[0], sock(mix.inputs, "Factor", "VALUE"))
    L.new(pos.outputs[0], sock(mix.inputs, "A", "VECTOR"))
    L.new(named("tgt", "FLOAT_VECTOR"), sock(mix.inputs, "B", "VECTOR"))
    sp_ = N.new("GeometryNodeSetPosition")
    L.new(gi.outputs[0], sp_.inputs["Geometry"])
    L.new(sock(mix.outputs, "Result", "VECTOR"), sp_.inputs["Position"])
    rsc = N.new("ShaderNodeVectorMath")
    rsc.operation = "SCALE"
    L.new(named("rot", "FLOAT_VECTOR"), rsc.inputs[0])
    L.new(div.outputs[0], rsc.inputs["Scale"])
    oi = N.new("GeometryNodeObjectInfo")
    oi.inputs["Object"].default_value = PROTO
    oi.transform_space = "ORIGINAL"
    inst = N.new("GeometryNodeInstanceOnPoints")
    L.new(sp_.outputs[0], inst.inputs["Points"])
    L.new(oi.outputs["Geometry"], inst.inputs["Instance"])
    try:
        e2r = new_node(N, "FunctionNodeEulerToRotation")
        L.new(rsc.outputs[0], e2r.inputs[0])
        L.new(e2r.outputs[0], inst.inputs["Rotation"])
    except RuntimeError:
        L.new(rsc.outputs[0], inst.inputs["Rotation"])
    L.new(named("scl", "FLOAT_VECTOR"), inst.inputs["Scale"])
    L.new(inst.outputs[0], go.inputs[0])
    return ng


CGROUP = collapse_group()
VOLUME = None
for ri, R in enumerate(rounds):
    if R["mode"] != "cubes":
        continue
    cap = R.get("cap", 0.0)
    sp = R["sp"]
    g = {k: max(sp[k], cap) for k in sp}
    xs = np.arange(XMIN + g["x"] / 2, XMAX, g["x"])
    ys = np.arange(YMIN + g["y"] / 2, YMAX, g["y"])
    zs = np.arange(g["z"] / 2, ZMAX, g["z"])
    pts, cols = [], []
    smin = min(g.values())
    for x in xs:
        for y in ys:
            for z in zs:
                p = Vector((x, y, z))
                mi = classify(p, smin)
                if mi is None:
                    continue
                pts.append((x, y, z))
                cols.append(mi)
    P = np.array(pts)
    n_pts = len(P)
    cell_vol = g["x"] * g["y"] * g["z"]
    true_cells = n_pts * cell_vol / (sp["x"] * sp["y"] * sp["z"])
    R["n_cubes"] = int(round(true_cells)) if cap == 0.0 else int(round(true_cells, -3))
    R["approx"] = cap > 0.0
    # heap targets: a dome of the same number of slots
    # slump: the bear sinks to ~45% height and spreads out at the base (keeps its silhouette)
    cx, cy = P[:, 0].mean(), P[:, 1].mean()
    zr = P[:, 2] / ZMAX
    zn = P[:, 2] * 0.44 + rng.uniform(-0.3, 0.3, n_pts) * g["z"]
    spread = 1.0 + 0.55 * (1 - zn / (ZMAX * 0.44)) ** 1.5 + rng.uniform(0, 0.12, n_pts)
    T = np.stack([cx + (P[:, 0] - cx) * spread, cy + (P[:, 1] - cy) * spread,
                  np.maximum(zn, g["z"] * 0.5)], 1)
    T[:, :2] += rng.uniform(-0.4, 0.4, (n_pts, 2)) * np.array([g["x"], g["y"]])
    # break up the face/shell pattern: shuffle targets inside local windows (height band, then angle)
    key_band = np.floor((T[:, 2] + rng.uniform(-0.03, 0.03, n_pts)) / 0.03)
    ang = np.arctan2(T[:, 1] - cy, T[:, 0] - cx)
    order = np.lexsort((ang, key_band))
    W = max(6, n_pts // 40)
    T2 = T.copy()
    for b0 in range(0, n_pts, W):
        idx = order[b0:b0 + W]
        T2[idx] = T[rng.permutation(idx)]
    T = T2
    dl = 0.30 * (1 - P[:, 2] / ZMAX) * 0.0 + rng.uniform(0, 0.35, n_pts) + 0.12 * (1 - P[:, 2] / ZMAX)
    rot = rng.uniform(-1.4, 1.4, (n_pts, 3))
    colv = np.array([MAT_COL[c] for c in cols])
    inner = np.array(cols) == 2
    colv[inner] = colv[inner] * rng.uniform(0.9, 1.05, (inner.sum(), 1))
    colv[~inner] = colv[~inner] * rng.uniform(0.85, 1.15, ((~inner).sum(), 1))
    me = bpy.data.meshes.new("cubes_%d" % ri)
    me.vertices.add(n_pts)
    me.vertices.foreach_set("co", P.ravel())
    for nm, dt, data, key in (("tgt", "FLOAT_VECTOR", T, "vector"), ("rot", "FLOAT_VECTOR", rot, "vector"),
                              ("del", "FLOAT", dl, "value")):
        a = me.attributes.new(nm, dt, "POINT")
        a.data.foreach_set(key, np.asarray(data, dtype=np.float32).ravel())
    a = me.attributes.new("scl", "FLOAT_VECTOR", "POINT")
    a.data.foreach_set("vector", np.tile(np.array([g["x"], g["y"], g["z"]], np.float32) * 0.97, n_pts))
    a = me.attributes.new("ccol", "FLOAT_COLOR", "POINT")
    a.data.foreach_set("color", np.concatenate([colv, np.ones((n_pts, 1))], 1).astype(np.float32).ravel())
    ob = new_obj("Cubes_%d" % ri, me)
    md = ob.modifiers.new("collapse", "NODES")
    md.node_group = CGROUP.copy()
    cf, end = R["collapse_f"], R["end"]
    set_interp("CONSTANT")
    ob.hide_render = True
    ob.keyframe_insert("hide_render", frame=1)
    ob.hide_render = False
    ob.keyframe_insert("hide_render", frame=cf)
    ob.hide_render = True
    ob.keyframe_insert("hide_render", frame=end + 1)
    ob.hide_viewport = False
    set_interp("LINEAR")
    tsock = md.node_group.nodes["Tval"].outputs[0]
    tsock.default_value = 0.0
    tsock.keyframe_insert("default_value", frame=cf)
    tsock.default_value = 1.0
    tsock.keyframe_insert("default_value", frame=cf + R["collapse"] - 6)
    R["cube_obj"] = ob
    print("[v2] round %d cubes: %d instances, shown %d" % (ri, n_pts, R["n_cubes"]), flush=True)

# ----------------------------------------------------------------------------- render settings
r = scene.render
r.engine = "CYCLES"
r.resolution_x, r.resolution_y = RES if not PREVIEW else (360, 640)
r.resolution_percentage = 100
r.image_settings.file_format = "PNG"
r.image_settings.color_mode = "RGB"
r.image_settings.compression = 30
r.use_motion_blur = True
r.motion_blur_shutter = 0.5
vt = [v.identifier for v in bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items]
scene.view_settings.view_transform = "AgX" if "AgX" in vt else "Filmic"
for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
    tryset(scene.view_settings, "look", look)
c = scene.cycles
c.device = "CPU"
c.samples = SAMPLES
c.use_adaptive_sampling = True
c.adaptive_threshold = 0.04
c.use_denoising = True
tryset(c, "denoiser", "OPENIMAGEDENOISE")
tryset(c, "denoising_input_passes", "RGB_ALBEDO_NORMAL")
c.max_bounces = 4
c.diffuse_bounces = 2
c.glossy_bounces = 2
c.transmission_bounces = 1
c.transparent_max_bounces = 2
tryset(c, "use_light_tree", True)
tryset(c, "blur_glossy", 1.0)
tryset(c, "sample_clamp_indirect", 5.0)
tryset(c, "tile_size", 512)

# ----------------------------------------------------------------------------- bake + timeline + save
if any_pieces:
    print("[v2] baking rigid bodies", flush=True)
    scene.frame_set(1)
    with bpy.context.temp_override(scene=scene, point_cache=scene.rigidbody_world.point_cache):
        bpy.ops.ptcache.bake(bake=True)

mb = []
for R in rounds:
    if R["per"] < 6:
        mb += [R["start"] + R["intro"] - 2, int(R["cut_end"]) + R["after"] + 6]
scene["motion_blur_frames"] = mb
frames = []
for fr in range(1, FRAMES + 1):
    R = [x for x in rounds if x["start"] <= fr <= x["end"]][0]
    cuts = sum(1 for h, _ in R["impacts"] if h <= fr + 0.5)
    cubes = R["n_cubes"] if fr >= R["collapse_f"] + 2 else 0
    frames.append(dict(frame=fr, cuts=cuts, cubes=cubes, approx=bool(R.get("approx")) and cubes > 0, round=rounds.index(R)))
meta = dict(fps=FPS, frames=FRAMES, per_frame=frames, events=events,
            rounds=[dict(n=R["n"], start=R["start"], end=R["end"], collapse_f=R["collapse_f"], cut_end=R["cut_end"],
                         n_cubes=R["n_cubes"]) for R in rounds])
with open(os.path.join(OUT, "timeline.json"), "w") as fh:
    json.dump(meta, fh)
r.filepath = os.path.join(OUT, "frames", "f_")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "scene.blend"))
print("[v2] saved", OUT, flush=True)
