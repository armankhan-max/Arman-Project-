"""Shot definitions + renderer for the 'coins for the dead' short.

  /opt/bpyenv/bin/python blender/coinstory/shots.py A --preview
  /opt/bpyenv/bin/python blender/coinstory/shots.py A [--start 1 --end 50 --threads 2]
"""
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chars as C
import props as P
from props import mat

ROOT = os.path.dirname(os.path.dirname(HERE))
FPS = 24
R = math.radians

# shot -> (start, end) seconds in the voiceover
TIMES = {
    "A": (0.00, 4.25), "B": (4.25, 7.40), "C": (7.40, 11.90), "D": (11.90, 14.60), "E1": (14.60, 17.30),
    "E2": (17.30, 20.35), "F": (20.35, 23.50), "G1": (23.50, 26.45), "G2": (26.45, 29.35),
    "S": (29.35, 48.58), "T": (48.58, 53.30),
}
# cuts that are not cuts at all (same scene + camera pose on both sides) / slow match dissolves
CONTINUOUS = [("C", "D"), ("G1", "G2")]
DISSOLVE = [("A", "B")]


def nframes(shot):
    a, b = TIMES[shot]
    return round(b * FPS) - round(a * FPS)


# ---------------- scene helpers ----------------

def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)


def world(horizon, zenith, ground=None, strength=1.0):
    w = bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    bg.inputs["Strength"].default_value = strength
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position = 0.0; e[0].color = (*(ground or horizon), 1)
    e[1].position = 0.65; e[1].color = (*zenith, 1)
    h = e.new(0.02); h.color = (*horizon, 1)
    madd = nt.nodes.new("ShaderNodeMath")
    madd.operation = "MULTIPLY_ADD"
    madd.inputs[1].default_value = 1.0
    madd.inputs[2].default_value = 0.0
    nt.links.new(sep.outputs["Z"], madd.inputs[0])
    nt.links.new(madd.outputs[0], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])


def world_hdri(slot, strength=1.0, rot=0.0, sat=1.0):
    w = bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    bg.inputs["Strength"].default_value = strength
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, rot)
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(P.ASSETS, "hdri", slot + ".hdr"), check_existing=True)
    hs = nt.nodes.new("ShaderNodeHueSaturation")
    hs.inputs["Saturation"].default_value = sat
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], hs.inputs["Color"])
    nt.links.new(hs.outputs["Color"], bg.inputs["Color"])


def sun(rot, energy, color=(1, 1, 1), angle=3.0):
    li = bpy.data.lights.new("sun", "SUN")
    li.energy = energy
    li.color = color
    li.angle = R(angle)
    o = P.link(bpy.data.objects.new("sun", li))
    o.rotation_euler = tuple(R(a) for a in rot)
    return o


def area(loc, target, size, watts, color=(1, 1, 1)):
    li = bpy.data.lights.new("area", "AREA")
    li.energy = watts
    li.color = color
    li.size = size
    o = P.link(bpy.data.objects.new("area", li))
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    o.visible_camera = False
    o.visible_glossy = False
    return o


def point(loc, watts, color=(1, 1, 1), radius=0.1):
    li = bpy.data.lights.new("pt", "POINT")
    li.energy = watts
    li.color = color
    li.shadow_soft_size = radius
    o = P.link(bpy.data.objects.new("pt", li))
    o.location = loc
    return o


def camera(keys, lens=20, fstop=None):
    """keys: [(frame, cam_loc, target_loc[, lens])]"""
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.clip_start = 0.02
    cd.clip_end = 500
    cam = P.link(bpy.data.objects.new("cam", cd))
    tgt = P.empty("cam_target")
    con = cam.constraints.new("TRACK_TO")
    con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    for k in keys:
        f, loc, t = k[0], k[1], k[2]
        cam.location = loc
        cam.keyframe_insert("location", frame=f)
        tgt.location = t
        tgt.keyframe_insert("location", frame=f)
        if len(k) > 3:
            cd.lens = k[3]
            cd.keyframe_insert("lens", frame=f)
    if fstop:
        cd.dof.use_dof = True
        cd.dof.focus_object = tgt
        cd.dof.aperture_fstop = fstop
    bpy.context.scene.camera = cam
    return cam


def key_loc(o, frame, loc):
    o.location = loc
    o.keyframe_insert("location", frame=frame)


def key_vis(o, frame, visible):
    for c in [o] + list(o.children_recursive):
        c.hide_render = not visible
        c.keyframe_insert("hide_render", frame=frame)


def ballistic(o, f0, p0, v0, floor=None, g=9.8, frames=60, spin=(9, 5, 0), rest_rot=(0, 0, 0), bounce=0.3):
    """Keyframe a thrown object with gravity; it bounces once or twice on `floor` (z) and comes to rest."""
    p = Vector(p0); v = Vector(v0); rot = Vector((0, 0, 0)); dt = 1.0 / FPS
    o.location = p
    o.keyframe_insert("location", frame=f0 - 1)
    resting = False
    for i in range(frames + 1):
        o.location = p
        o.rotation_euler = rest_rot if resting else tuple(rot)
        o.keyframe_insert("location", frame=f0 + i)
        o.keyframe_insert("rotation_euler", frame=f0 + i)
        if resting:
            break
        v.z -= g * dt
        p = p + v * dt
        rot += Vector(spin) * dt
        if floor is not None and p.z <= floor and v.z < 0:
            p.z = floor
            if bounce and abs(v.z) > 1.3:
                v.z = -v.z * bounce; v.x *= 0.45; v.y *= 0.45
                spin = tuple(c * 0.4 for c in spin)
            else:
                resting = True


def ghostify(rig):
    """Translucent blue-glowing version of a character (keeps its textures)."""
    seen = set()
    for o in rig.children_recursive:
        if o.type != "MESH":
            continue
        o.visible_shadow = False
        for sl in o.material_slots:
            m = sl.material
            if not m or not m.node_tree:
                continue
            if m.users > 1 or m.name in seen:
                m = m.copy(); sl.material = m
            seen.add(m.name)
            for nd in m.node_tree.nodes:
                if nd.type == "BSDF_PRINCIPLED":
                    al = nd.inputs["Alpha"]
                    if al.links:
                        mul = m.node_tree.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
                        mul.inputs[1].default_value = 0.5
                        src = al.links[0].from_socket
                        m.node_tree.links.new(src, mul.inputs[0]); m.node_tree.links.new(mul.outputs[0], al)
                    else:
                        al.default_value = 0.5
                    lw = m.node_tree.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.3
                    ramp = m.node_tree.nodes.new("ShaderNodeValToRGB")
                    ramp.color_ramp.elements[0].color = (0.0, 0.08, 0.3, 1)
                    ramp.color_ramp.elements[1].color = (0.25, 0.85, 1.0, 1)
                    m.node_tree.links.new(lw.outputs["Facing"], ramp.inputs["Fac"])
                    m.node_tree.links.new(ramp.outputs["Color"], nd.inputs["Emission Color"])
                    nd.inputs["Emission Strength"].default_value = 0.3


# ---------------- characters ----------------

def robe_mat(color, rough=0.75):
    return P.add_noise(P.M("robe", color, rough=rough), scale=90, bump=0.25)


def recolor(rig, key, sat=1.0, val=1.0, mul=None):
    """Re-tint textured clothing whose object name contains `key` (keeps fabric detail)."""
    for o in rig.children_recursive:
        if o.type != "MESH" or key not in o.name:
            continue
        for sl in o.material_slots:
            m = sl.material.copy()
            sl.material = m
            nt = m.node_tree
            for nd in nt.nodes:
                if nd.type != "BSDF_PRINCIPLED" or not nd.inputs["Base Color"].links:
                    continue
                src = nd.inputs["Base Color"].links[0].from_socket
                hs = nt.nodes.new("ShaderNodeHueSaturation")
                hs.inputs["Saturation"].default_value = sat
                hs.inputs["Value"].default_value = val
                nt.links.new(src, hs.inputs["Color"])
                out = hs.outputs["Color"]
                if mul:
                    mx = nt.nodes.new("ShaderNodeMix")
                    mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1.0
                    nt.links.new(out, mx.inputs[6]); mx.inputs[7].default_value = (*mul, 1)
                    out = mx.outputs[2]
                nt.links.new(out, nd.inputs["Base Color"])


def make_dead(name="dead"):
    rig, body, parts = C.make_human(name, skin="young_caucasian_male", hair="short02", clothes=["donitz_monk_robe"])
    recolor(rig, "monk_robe", sat=0.0, val=5.0, mul=(1.0, 0.97, 0.9))
    return rig


def make_kin(name="kin", color=(0.85, 0.08, 0.06), skin="middleage_caucasian_male"):
    rig, body, parts = C.make_human(name, skin=skin, hair="short04",
                                    clothes=["donitz_monk_robe", "donitz_monk_robe_hood_down", "toigo_mj_cloth_shoes"])
    recolor(rig, "monk_robe", sat=0.0, val=4.5, mul=color)
    return rig


PEOPLE = [
    ("young_asian_female", "toigo_blunt_bob_with_bangs", (0.1, 0.45, 0.95)), ("middleage_asian_male", "short03", (0.95, 0.6, 0.05)),
    ("old_asian_male", "short04", (0.55, 0.15, 0.8)),
]
GREEKS = [
    ("young_caucasian_female", "long01", (0.15, 0.4, 0.9)), ("middleage_caucasian_male", "short04", (0.85, 0.2, 0.15)),
]


def mourner(i, spec, loc, face_deg, mode="clasp"):
    skin, hair, color = spec
    if "female" in skin:
        rig, body, parts = C.make_human(f"p{i}", skin=skin, hair=hair,
                                        clothes=["toigo_long_full_skirt", "toigo_turtleneck_halter_top", "toigo_ballet_flats"])
    else:
        rig, body, parts = C.make_human(f"p{i}", skin=skin, hair=hair,
                                        clothes=["donitz_monk_robe", "donitz_monk_robe_hood_down", "toigo_mj_cloth_shoes"])
        recolor(rig, "monk_robe", sat=0.0, val=4.5, mul=color)
    C.legs_together(rig)
    if mode == "clasp":
        C.reach(rig, "L", (0.04, -0.2, 1.0), pole=(1, 0.3, -0.4)); C.reach(rig, "R", (-0.04, -0.21, 1.0), pole=(-1, 0.3, -0.4))
        C.aim(rig, "head", (0, -0.5, 1))
    elif mode == "up":
        C.pose(rig, {"upperarm01.L": (0.7, -0.2, 0.9), "lowerarm01.L": (0.2, -0.3, 1),
                     "upperarm01.R": (-0.7, -0.2, 0.9), "lowerarm01.R": (-0.2, -0.3, 1)})
        C.aim(rig, "head", (0, 0.2, 1))
    else:
        stand_relaxed(rig)
    rig.location = loc
    rig.rotation_euler = (0, 0, R(face_deg))
    return rig


def make_charon():
    rig, body, parts = C.make_human("charon", skin="old_caucasian_male", hair=None,
                                    clothes=["donitz_monk_robe", "donitz_monk_robe_hood"])
    recolor(rig, "monk_robe", sat=0.4, val=0.3, mul=(0.7, 0.75, 1.0))
    eye_m = P.M("ceye", (0.6, 1, 0.7), emit=(0.5, 1.0, 0.6), es=5)
    for sd in "LR":
        e = P.sphere("ceye", 0.012, C.bone_world(rig, f"eye.{sd}") + Vector((0, -0.028, 0)), eye_m, subdiv=2)
        C.attach(e, rig, "head")
    rig.scale = (1.14, 1.14, 1.14)
    return rig


def stripe_mat():
    m = P.M("stripes", (0.02, 0.02, 0.02), rough=0.8)
    nt = m.node_tree
    b = P.bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    fr = nt.nodes.new("ShaderNodeMath"); fr.operation = "MULTIPLY"; fr.inputs[1].default_value = 13.0
    nt.links.new(sep.outputs["Z"], fr.inputs[0])
    fc = nt.nodes.new("ShaderNodeMath"); fc.operation = "FRACT"
    nt.links.new(fr.outputs[0], fc.inputs[0])
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 0.5
    nt.links.new(fc.outputs[0], gt.inputs[0])
    top = nt.nodes.new("ShaderNodeMath"); top.operation = "GREATER_THAN"; top.inputs[1].default_value = 0.55
    nt.links.new(sep.outputs["Z"], top.inputs[0])
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    nt.links.new(gt.outputs[0], mul.inputs[0]); nt.links.new(top.outputs[0], mul.inputs[1])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.015, 0.015, 0.02, 1)
    ramp.color_ramp.elements[1].color = (0.9, 0.9, 0.88, 1)
    nt.links.new(mul.outputs[0], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


def make_thief(name="thief"):
    rig, body, parts = C.make_human(name, skin="young_caucasian_male2", hair=None,
                                    clothes=["male_casualsuit04", "culturalibre_hero_mask_1", "jujube_newsboy_cap", "shoes02"])
    recolor(rig, "casualsuit", sat=0.5, val=0.45)
    recolor(rig, "newsboy", sat=0.0, val=0.12)
    return rig


def stand_relaxed(rig):
    C.legs_together(rig)
    C.pose(rig, {"upperarm01.L": (0.2, 0.02, -1), "lowerarm01.L": (0.12, -0.3, -1),
                 "upperarm01.R": (-0.2, 0.02, -1), "lowerarm01.R": (-0.12, -0.3, -1)})
    for s in "LR":
        C.curl_fingers(rig, s, 0.35)


def lie_crossed(rig):
    C.reach(rig, "L", (-0.06, -0.19, 1.22), pole=(1, -0.2, -0.6))
    C.reach(rig, "R", (0.06, -0.2, 1.14), pole=(-1, -0.2, -0.6))
    C.close_eyes(rig)


def lay_down(rig, feet, floor_z):
    """Lie on back, head toward +Y."""
    rig.rotation_euler = (R(-90), 0, 0)
    rig.location = (feet[0], feet[1], floor_z + 0.125)


# ---------------- environments ----------------

def graveyard(night=False, pits=((0, 0),), closed=(), greek=True, seed=2):
    rnd = random.Random(seed)
    gm = P.ground_mat((0.06, 0.42, 0.04), (0.2, 0.33, 0.13)) if not night else P.ground_mat((0.03, 0.3, 0.12), (0.16, 0.3, 0.2))
    ground = P.box("ground", (160, 160, 4), (0, 0, -2), gm)
    for i, (px, py) in enumerate(pits):
        cut = P.box(f"cut{i}", (1.1, 2.3, 1.5), (px, py + 0.8, 0), None)
        cut.hide_render = True
        cut.display_type = "WIRE"
        b = ground.modifiers.new(f"pit{i}", "BOOLEAN")
        b.object = cut
        b.operation = "DIFFERENCE"
        P.mound((px + 1.2, py + 0.9, -0.05), (0.5, 0.95, 0.3))
        P.tombstone(f"ts{i}", (px, py + 2.25, 0), material="marble" if greek else "stone")
    for i, (cx, cy) in enumerate(closed):
        P.mound((cx, cy + 0.8, -0.05), (0.55, 1.1, 0.25))
        P.tombstone(f"tc{i}", (cx, cy + 2.25, 0), h=rnd.uniform(0.8, 1.3), rot_z=rnd.uniform(-0.08, 0.08))
    blocked = list(pits) + list(closed)

    def free(x, y):
        return not any(abs(x - bx) < 1.05 and -0.75 < y - by < 2.75 for bx, by in blocked)

    for i in range(7):
        x = rnd.uniform(-17, 17); y = rnd.uniform(9, 24)
        if abs(x) > 2.5:
            P.place("island_tree_02", (x, y, 0), rnd.uniform(1.7, 2.5), rnd.uniform(0, 6.28))
    for i in range(10):
        x = rnd.uniform(-14, 14); y = rnd.uniform(5, 16)
        if abs(x) > 2.5:
            P.tombstone(f"bg{i}", (x, y, 0), h=rnd.uniform(0.7, 1.4), rot_z=rnd.uniform(-0.15, 0.15))
    for x, y, sc in ((-30, 60, 22), (10, 75, 30), (45, 58, 20)):
        P.sphere("hill", sc, (x, y, -sc * 0.55), mat("leaf") if not night else P.M("hilln", (0.03, 0.12, 0.3), rough=1), subdiv=4)
    x0 = min(px for px, _ in blocked) - 5 if blocked else -6
    x1 = max(px for px, _ in blocked) + 5 if blocked else 6
    P.scatter("grass_medium_01", 150, (x0, x1), (-4.5, 8), seed=seed, keep=free, scale=(0.5, 0.9))
    P.scatter("grass_medium_02", 240, (x0, x1), (-4.5, 8), seed=seed + 1, keep=free, scale=(0.8, 1.4))
    P.scatter("fern_02", 9, (x0, x1), (-3, 8), seed=seed + 2, keep=free, scale=(0.5, 0.8))
    P.scatter("flower_gazania", 8, (x0, x1), (-4, 7), seed=seed + 3, keep=free, scale=(0.7, 1.0))
    P.scatter("dandelion_01", 8, (x0, x1), (-4, 7), seed=seed + 4, keep=free, scale=(0.8, 1.2))
    P.scatter("rock_07", 16, (x0, x1), (-4, 8), seed=seed + 5, keep=free, scale=(1.0, 2.5))
    P.scatter("boulder_01", 3, (x0 - 1, x1 + 1), (4, 9), seed=seed + 6, keep=free, scale=(0.5, 0.9))
    if greek:
        P.temple((-6.5, 13, 0))
        P.column("ruin1", (4.6, 7.5, 0), broken=True)
        P.column("ruin2", (6.2, 9, 0))
    if night:
        world((0.25, 0.12, 0.55), (0.01, 0.03, 0.3), ground=(0.02, 0.08, 0.2), strength=1.0)
        sun((55, 0, -150), 3.4, (0.5, 0.75, 1.0), angle=6)
        sun((62, 0, 40), 1.8, (0.85, 0.5, 1.0), angle=20)
        moon = P.sphere("moon", 3.2, (-14, 80, 34), P.M("moon", (1, 1, 0.9), emit=(0.9, 0.95, 1.0), es=1.6), subdiv=3)
        moon.visible_shadow = False
    else:
        world_hdri("day", strength=1.0, sat=1.25)
        sun((22, 0, 25), 2.6, (1.0, 0.93, 0.8))
    return ground


def styx(taxi=False, taxi_rot=0.0):
    """Underworld river. Returns (boat_root, boat, charon)."""
    P.box("water", (400, 400, 0.1), (0, 0, -0.05), P.water_mat())
    P.box("riverbed", (400, 400, 0.1), (0, 0, -3), mat("black"))
    rockm = P.tex_mat("rock", 0.25, tint=(1.4, 0.7, 2.2), normal=1.5)
    P.bsdf(rockm).inputs["Emission Color"].default_value = (0.35, 0.05, 0.8, 1)
    P.bsdf(rockm).inputs["Emission Strength"].default_value = 0.12
    dock = P.box("dock", (5.2, 6.0, 0.6), (0, -3.3, -0.15), P.tex_mat("paving", 0.5, tint=(0.7, 0.75, 1.0), name="dockm"), bevel=0.03)
    for x in (-2.2, 2.2):
        P.column("dc", (x, -1.0, 0.15), h=3.0, r=0.22, broken=(x > 0))
        P.column("dc2", (x, -4.2, 0.15), h=3.0, r=0.22)
    rnd = random.Random(7)
    for i in range(26):
        side = -1 if i % 2 else 1
        x = side * rnd.uniform(6, 26); y = rnd.uniform(-8, 60)
        h = rnd.uniform(4, 16)
        r = P.cyl("spire", rnd.uniform(1.4, 3.4), h, (x, y, h / 2 - 0.5), rockm, segs=7, r2=rnd.uniform(0.3, 0.9), smooth=False)
        r.rotation_euler = (rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12), rnd.uniform(0, 3))
    # far gate of the dead
    gm = P.M("gateglow", (0.3, 1, 0.6), emit=(0.2, 1.0, 0.5), es=1.0)
    for x in (-3.2, 3.2):
        P.cyl("fg", 0.6, 11, (x, 62, 5.5), gm, segs=12)
    P.box("fgt", (8.6, 1.2, 1.2), (0, 62, 11.4), gm)
    area((0, 55, 8), (0, 0, 2), 14, 22000, (0.3, 1.0, 0.6))
    area((9, 6, 6), (0, 2, 1), 6, 900, (0.6, 0.4, 1.0))
    world((0.05, 0.55, 0.5), (0.12, 0.0, 0.3), ground=(0.0, 0.1, 0.12), strength=1.0)
    sun((50, 0, 160), 1.8, (0.3, 1.0, 0.8), angle=10)
    sun((60, 0, -40), 1.2, (1.0, 0.3, 0.9), angle=15)
    area((0, -2, 9), (0, 0, 0), 9, 450, (0.45, 0.6, 1.0))
    area((-6, -7, 3), (0, 0, 1.2), 4, 250, (0.9, 0.5, 1.0))
    # boat group, bow toward -Y
    root = P.empty("boat_root", (0, 2.6, 0))
    hull = P.boat()
    hull.rotation_euler = (0, 0, R(90))
    hull.location = (0, 2.6, 0.3)
    P.parent(hull, root)
    lan = P.lantern((-0.5, 1.0, 0.0), pole=2.0, watts=260)
    P.parent(lan, root)
    pole = P.cyl("punt", 0.022, 4.2, (0.66, 1.45, 1.2), mat("wood"), segs=8, rot=(R(8), R(-6), 0))
    P.parent(pole, root)
    charon = make_charon()
    charon.location = (0.12, 1.25, -0.12)
    if taxi:
        ym = P.M("taxi", (1.0, 0.75, 0.0), emit=(1.0, 0.7, 0.0), es=1.2, rough=0.3)
        post = P.cyl("tx_post", 0.03, 2.3, (0, 3.3, 1.2), mat("wood"), segs=8)
        sign = P.box("tx_sign", (0.95, 0.12, 0.36), (0, 3.3, 2.5), ym, bevel=0.03)
        t1 = P.text("tx_t", "TAXI", 0.27, (0, 3.23, 2.5), (R(90), 0, 0), mat("black"), extrude=0.01)
        piv = P.empty("tx_piv", (0, 3.3, 2.5))
        P.parent(sign, piv); P.parent(t1, piv)
        piv.rotation_euler = (0, 0, taxi_rot)
        for o in (post, piv):
            P.parent(o, root)
    return root, hull, charon


def bob(root, amp=0.025):
    P.drive(root, "location", 2, f"{amp}*sin(frame/9.0)")
    P.drive(root, "rotation_euler", 1, "0.02*sin(frame/12.0)")


def china(pits=()):
    fm = P.tex_mat("paving", 0.45, tint=(1.25, 1.1, 0.95))
    floor = P.box("floor", (120, 120, 4), (0, 0, -2), fm)
    for i, (cx, cy) in enumerate(pits):
        cut = P.box(f"cut{i}", (1.3, 1.5, 1.3), (cx, cy, 0), None)
        cut.hide_render = True
        bm = floor.modifiers.new(f"pit{i}", "BOOLEAN"); bm.object = cut; bm.operation = "DIFFERENCE"
        for sz, lc in (((1.3, 1.5, 0.02), (0, 0, -0.64)), ((0.02, 1.5, 0.65), (-0.64, 0, -0.33)), ((0.02, 1.5, 0.65), (0.64, 0, -0.33)),
                       ((1.3, 0.02, 0.65), (0, -0.74, -0.33)), ((1.3, 0.02, 0.65), (0, 0.74, -0.33))):
            P.box("liner", sz, (cx + lc[0], cy + lc[1], lc[2]), mat("soil"))
        P.mound((cx + (1.2 if cx > 0 else -1.2), cy, -0.05), (0.45, 0.7, 0.26))
    P.paifang((0, 0, 0))
    for i, x in enumerate((-1.5, -0.5, 0.5, 1.5)):
        P.red_lantern((x, -0.1, 3.05), hang=0.35 + 0.15 * (i % 2), ph=i * 1.3, light=160 if i in (0, 3) else 0)
    wallm = P.tex_mat("marble", 0.5, tint=(1.0, 0.1, 0.07), name="wall")
    capm = P.M("wallcap", (0.04, 0.16, 0.15), rough=0.4)
    for x in (-7.5, 7.5):
        P.box("wall", (0.5, 60, 2.6), (x, 10, 1.3), wallm)
        P.box("wallcap", (0.9, 60, 0.25), (x, 10, 2.7), capm, bevel=0.05)
    P.box("backwall", (15.5, 0.5, 2.6), (0, 11, 1.3), wallm)
    P.box("backcap", (15.9, 0.9, 0.25), (0, 11, 2.7), capm, bevel=0.05)
    # tomb: mound + stele + offering table
    tomb = P.sphere("tomb", 1.7, (0, 6.6, -0.25), mat("stone"), scale=(1.25, 1, 0.85), subdiv=4)
    P.tombstone("stele", (0, 4.75, 0), w=0.8, h=1.25, t=0.2, material="stone")
    P.box("stele_red", (0.5, 0.02, 0.85), (0, 4.63, 0.72), mat("red"))
    for x, y, sc in ((-5.6, 8.0, 0.3), (5.7, 8.4, 0.34), (5.9, -6.0, 0.28), (-6.0, -7.0, 0.3)):
        P.place("jacaranda_tree", (x, y, 0), sc, x * 1.3)
    for x, y, sc, rz in ((-2.9, 5.3, 0.8, 0.4), (2.6, 5.6, 0.9, 2.0), (6.3, 1.5, 1.0, 1.0), (-6.4, 0.8, 0.9, 3.0)):
        P.place("boulder_01", (x, y, 0), sc, rz)
    for x in (-0.75, 0.75):
        P.place("brass_vase_01", (x, 4.45, 0), 1.4)
    for x, y in ((-1.6, -2.5), (1.6, -2.5), (-1.6, -6.5), (1.6, -6.5)):
        P.place("wooden_lantern_01", (x, y, 0), 1.5)
        point((x, y, 0.45), 30, (1.0, 0.6, 0.25), radius=0.1)
    mm = P.M("mnt", (0.2, 0.3, 0.75), rough=1)
    mm2 = P.M("mnt2", (0.45, 0.3, 0.7), rough=1)
    rnd = random.Random(5)
    for i in range(9):
        x = -80 + i * 20 + rnd.uniform(-5, 5)
        h = rnd.uniform(18, 38)
        m = P.cyl("mnt", rnd.uniform(16, 26), h, (x, 85 + rnd.uniform(-8, 20), h / 2 - 1), mm if i % 2 else mm2, segs=10, r2=1.0)
        P.displace(m, 4.0, 8.0)
    world_hdri("sunset", strength=1.1, rot=R(40), sat=1.3)
    sun((58, 0, 125), 2.1, (1.0, 0.7, 0.4), angle=4)
    sun((50, 0, -60), 0.6, (0.5, 0.65, 1.0), angle=20)
    return floor


def note_pile(center, n=120, radius=0.8, height=0.5, seed=4):
    rnd = random.Random(seed)
    base = P.note("pile_note")
    base.location = (center[0], center[1], center[2] + 0.01)
    for i in range(n):
        a = rnd.uniform(0, 6.28); r = radius * math.sqrt(rnd.random())
        d = P.dup(base)
        d.location = (center[0] + math.cos(a) * r, center[1] + math.sin(a) * r,
                      center[2] + 0.02 + height * (1 - r / radius) * rnd.uniform(0.6, 1.0))
        d.rotation_euler = (rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(0, 6.28))
    return base


def flying_notes(center, n, frames, seed=5, rise=0.09, radius=0.6, spread=0.012, glow=False, start_z=0.3, top=9.0, big=1.0):
    rnd = random.Random(seed)
    base = P.note("fly_note", 0.17 * big, 0.075 * big)
    if glow:
        gm = P.M("gnote", (0.6, 1, 0.9), emit=(0.5, 1.0, 0.85), es=3)
        base.data.materials[0] = gm
    base.location = (0, 0, -50)
    for i in range(n):
        d = P.dup(base)
        ph = rnd.uniform(0, top)
        a0 = rnd.uniform(0, 6.28); r0 = rnd.uniform(0.1, radius); w = rnd.uniform(0.04, 0.09) * rnd.choice((-1, 1))
        sp = rise * rnd.uniform(0.7, 1.4)
        sx, sy, sz = rnd.uniform(0.2, 0.5), rnd.uniform(0.2, 0.5), rnd.uniform(0.1, 0.3)
        for f in range(1, frames + 1, 2):
            z = (ph + f * sp) % top
            r = r0 + z * spread * 10
            a = a0 + f * w
            d.location = (center[0] + math.cos(a) * r, center[1] + math.sin(a) * r, center[2] + start_z + z)
            d.rotation_euler = (f * sx, f * sy, f * sz)
            d.keyframe_insert("location", frame=f)
            d.keyframe_insert("rotation_euler", frame=f)


def falling_notes(center, n, frames, seed=6, radius=1.0, top=3.2, glow=True):
    rnd = random.Random(seed)
    base = P.note("fall_note")
    if glow:
        base.data.materials[0] = P.M("gnote", (0.6, 1, 0.9), emit=(0.5, 1.0, 0.85), es=3)
        base.data.materials[1] = P.M("gnote2", (0.2, 0.9, 1), emit=(0.2, 0.8, 1.0), es=3)
    base.location = (0, 0, -50)
    for i in range(n):
        d = P.dup(base)
        ph = rnd.uniform(0, top)
        a = rnd.uniform(0, 6.28); r = rnd.uniform(0.25, radius)
        sp = rnd.uniform(0.03, 0.055)
        sx, sy = rnd.uniform(0.15, 0.4), rnd.uniform(0.15, 0.4)
        for f in range(1, frames + 1, 2):
            z = top - ((ph + f * sp) % top)
            d.location = (center[0] + math.cos(a) * r + 0.08 * math.sin(f * 0.2 + i), center[1] + math.sin(a) * r, center[2] + z)
            d.rotation_euler = (f * sx, f * sy, i)
            d.keyframe_insert("location", frame=f)
            d.keyframe_insert("rotation_euler", frame=f)


# ---------------- shots ----------------

def grave_body(coin_in_mouth=False):
    dead = make_dead()
    lie_crossed(dead)
    if coin_in_mouth:
        C.open_jaw(dead, 9)
    lay_down(dead, (0, -0.15), -0.75)
    return dead


def mouth_pos(dead):
    bpy.context.view_layer.update()
    teeth = next(o for o in dead.children_recursive if "teeth" in o.name.lower())
    c = sum((Vector(v) for v in teeth.bound_box), Vector()) / 8
    out = (dead.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()
    return teeth.matrix_world @ c + out * 0.04


def shot_A(n):
    graveyard(night=False)
    dead = grave_body()
    rnd = random.Random(1)
    base = P.coin(r=0.045)
    base.location = (0, 0, -50)
    for i in range(22):
        c = P.dup(base)
        tx = rnd.uniform(-0.38, 0.38); ty = rnd.uniform(0.2, 1.5)
        on_body = abs(tx) < 0.17 and 0.75 < ty < 1.35
        floor = -0.75 + (0.275 if on_body else 0.012)
        f0 = 8 + i * 4
        ballistic(c, f0, (tx + rnd.uniform(-0.3, 0.3), ty - 0.5, 2.6), (rnd.uniform(-0.1, 0.1), 0.6, -1.0), floor=floor,
                  rest_rot=(rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), rnd.uniform(0, 3)))
    sh = P.shovel()
    sh.location = (1.3, 0.6, 1.25); sh.rotation_euler = (R(8), R(-12), 0)
    for i, (loc, face) in enumerate((((-1.15, 0.3, 0), 90), ((-1.2, 1.3, 0), 90))):
        mourner(i, GREEKS[i], loc, face)
    camera([(1, (1.3, -2.9, 3.3), (0, 0.7, -0.3)), (55, (0.45, -0.9, 2.3), (0, 0.85, -0.5)),
            (n, (0.1, 0.62, 0.6), (0, 1.12, -0.55))], lens=19)


def ghost_at_grave(n, rise=True):
    graveyard(night=True)
    P.lantern((1.1, -0.2, 0), watts=90, pole=0.5)
    ghost = make_dead("ghost")
    ghostify(ghost)
    ghost.location = (0, 0.6, 0.3)
    if rise:
        key_loc(ghost, 1, (0, 0.6, -0.9)); key_loc(ghost, 30, (0, 0.6, 0.32)); key_loc(ghost, 50, (0, 0.6, 0.25))
        key_loc(ghost, n, (0, 0.6, 0.33))
    else:
        P.drive(ghost, "location", 2, "0.3+0.04*sin(frame/7.0)")
    point((0, 0.2, 1.0), 60, (0.4, 0.8, 1.0), radius=0.5)
    return ghost


def shot_B(n):
    ghost = ghost_at_grave(n)
    C.reach(ghost, "L", (0.13, -0.33, 1.12), pole=(1, 0.3, -0.6))
    C.reach(ghost, "R", (-0.13, -0.33, 1.12), pole=(-1, 0.3, -0.6))
    C.aim(ghost, "head", (0, -0.45, 1))
    pm = P.M("bill", (1, 1, 1), emit=(1, 1, 1), es=0.9, rough=0.6)
    paper = P.box("bill", (0.27, 0.36, 0.003), (0, 0, 0), pm)
    paper.location = ghost.matrix_world @ Vector((0, -0.37, 1.16))
    paper.rotation_euler = (R(62), 0, 0)
    P.parent(paper, ghost)
    bm = mat("black")
    t = P.text("bt", "BILL", 0.085, (0, 0.105, 0.003), (0, 0, 0), bm, extrude=0.001); t.parent = paper
    t2 = P.text("bt2", "PAST DUE", 0.043, (0, -0.105, 0.003), (0, 0, R(8)), P.M("stamp", (0.9, 0, 0), emit=(1, 0, 0), es=1.5),
                extrude=0.001); t2.parent = paper
    for i in range(4):
        ln = P.box("bl", (0.19, 0.008, 0.001), (0, 0.035 - i * 0.028, 0.003), bm); ln.parent = paper
    camera([(1, (0.5, -3.4, 0.35), (0, 0.6, 0.6)), (40, (0.2, -1.9, 1.3), (0, 0.5, 1.35)),
            (n, (-0.28, -0.62, 1.78), (0, 0.32, 1.42))], lens=21)


def shot_C(n):
    root, hull, charon = styx()
    stand_relaxed(charon)
    C.reach(charon, "L", (0.46, 0.12, 1.12), pole=(1, 0.5, -0.5))
    P.parent(charon, root)
    ghost = make_dead("ghost"); ghostify(ghost)
    stand_relaxed(ghost)
    ghost.rotation_euler = (0, 0, R(180)); ghost.location = (0.8, -1.2, 0.15)
    P.drive(ghost, "location", 2, "0.2+0.03*sin(frame/7.0)")
    key_loc(root, 1, (0, 17.5, 0)); key_loc(root, n, (0, 3.4, 0))
    P.drive(hull, "rotation_euler", 1, "0.025*sin(frame/10.0)")
    camera([(1, (-2.2, -9.5, 3.4), (0, 4, 0.8)), (60, (-1.4, -5.5, 1.5), (0, 3, 1.1)),
            (n, (-0.7, -3.3, 1.05), (0.3, 1.6, 1.3))], lens=20)


def charon_hand_out(charon, amount=1.0):
    C.reach(charon, "R", (-0.06, -0.52 * amount - 0.05, 1.02 + 0.12 * amount), pole=(-1, 0.6, -0.8))
    C.twist(charon, "lowerarm02.R", -80 * amount, "Y")
    C.twist(charon, "wrist.R", -40 * amount, "Y")


def shot_D(n):
    """Continues shot C without a cut: same scene state and camera pose as C's last frame."""
    off = nframes("C")
    root, hull, charon = styx()
    stand_relaxed(charon)
    C.reach(charon, "L", (0.46, 0.12, 1.12), pole=(1, 0.5, -0.5))
    C.key_pose(charon, 1); C.key_pose(charon, 8)
    charon_hand_out(charon)
    C.aim(charon, "head", (0, -0.25, 1))
    C.key_pose(charon, 30); C.key_pose(charon, n)
    P.parent(charon, root)
    root.location = (0, 3.4, 0)
    P.drive(hull, "rotation_euler", 1, f"0.025*sin((frame+{off})/10.0)")
    ghost = make_dead("ghost"); ghostify(ghost)
    stand_relaxed(ghost)
    ghost.rotation_euler = (0, 0, R(180)); ghost.location = (0.8, -1.2, 0.15)
    P.drive(ghost, "location", 2, f"0.2+0.03*sin((frame+{off})/7.0)")
    camera([(1, (-0.7, -3.3, 1.05), (0.3, 1.6, 1.3)), (36, (0.3, -0.9, 1.0), (0.1, 2.0, 1.45)),
            (n, (0.25, 0.75, 1.5), (0.12, 2.05, 1.82))], lens=20)


def shot_E1(n):
    graveyard(night=False, pits=(), closed=((3.2, 1.5), (-3.4, 2.5)))
    P.box("bier", (1.0, 2.3, 0.7), (0, 0.85, 0.35), mat("marble"), bevel=0.03)
    P.box("bier2", (1.25, 2.6, 0.12), (0, 0.85, 0.06), mat("marble"), bevel=0.02)
    dead = make_dead()
    lie_crossed(dead)
    C.open_jaw(dead, 11)
    lay_down(dead, (0, -0.15), 0.7)
    mp = mouth_pos(dead)
    kin = make_kin(color=(0.2, 0.3, 0.75))
    kin.rotation_euler = (0, 0, R(90)); kin.location = (-0.78, 1.2, 0)
    stand_relaxed(kin)
    C.aim(kin, "spine03", (0, -0.25, 1)); C.aim(kin, "head", (0, -0.6, 1))
    C.reach(kin, "R", mp + Vector((-0.25, -0.05, 0.42)), pole=(-0.3, 0.6, -1), world=True)
    C.curl_fingers(kin, "R", 0.75, 0.8)
    C.key_pose(kin, 1)
    C.reach(kin, "R", mp + Vector((-0.085, 0.0, 0.07)), pole=(-0.3, 0.6, -1), world=True)
    C.key_pose(kin, 36); C.key_pose(kin, 42)
    held = P.coin(r=0.026)
    wt = C.bone_world(kin, "finger2-3.R", tail=True)
    held.location = (wt + C.bone_world(kin, "finger1-3.R", tail=True)) / 2
    held.rotation_euler = (R(70), 0, R(20))
    C.attach(held, kin, "wrist.R")
    C.reach(kin, "R", mp + Vector((-0.3, -0.1, 0.38)), pole=(-0.3, 0.6, -1), world=True)
    C.key_pose(kin, n)
    placed = P.coin(r=0.026)
    placed.location = mp; placed.rotation_euler = (R(-14), 0, 0)
    key_vis(held, 1, True); key_vis(held, 41, False)
    key_vis(placed, 1, False); key_vis(placed, 41, True)
    camera([(1, (0.75, 0.55, 1.75), mp + Vector((-0.05, 0, 0.1))), (36, (0.34, 1.0, 1.28), mp),
            (n, (0.16, 1.18, 1.12), mp)], lens=24, fstop=2.0)


def shot_E2(n):
    root, hull, charon = styx(taxi=True)
    root.location = (0, 2.6, 0)
    stand_relaxed(charon)
    C.reach(charon, "L", (0.46, 0.12, 1.12), pole=(1, 0.5, -0.5))
    charon_hand_out(charon)
    charon.location = (0.0, 0.95, -0.12)
    P.parent(charon, root)
    palm = C.bone_world(charon, "wrist.R", tail=True) + Vector((0, 0, 0.05))
    ghost = make_dead("ghost"); ghostify(ghost)
    ghost.rotation_euler = (0, 0, R(180)); ghost.location = (-0.12, -0.55, 0.15)
    stand_relaxed(ghost)
    C.reach(ghost, "R", palm + Vector((0, -0.3, 0.25)), pole=(-1, 0.4, -0.7), world=True)
    C.curl_fingers(ghost, "R", 0.7, 0.8)
    C.key_pose(ghost, 1)
    C.reach(ghost, "R", palm + Vector((0, -0.06, 0.09)), pole=(-1, 0.4, -0.7), world=True)
    C.key_pose(ghost, 20); C.key_pose(ghost, 26)
    held = P.coin(r=0.03)
    held.location = (C.bone_world(ghost, "finger2-3.R", tail=True) + C.bone_world(ghost, "finger1-3.R", tail=True)) / 2
    C.attach(held, ghost, "wrist.R")
    stand_relaxed(ghost)
    C.key_pose(ghost, 44)
    placed = P.coin(r=0.03); placed.location = palm
    C.attach(placed, charon, "wrist.R")
    key_vis(held, 1, True); key_vis(held, 25, False)
    key_vis(placed, 1, False); key_vis(placed, 25, True)
    camera([(1, (0.7, -0.35, 1.5), palm), (24, (0.75, -0.55, 1.5), palm),
            (n, (1.15, -5.9, 2.2), (0, 1.9, 1.5))], lens=20)


def shot_F(n):
    root, hull, charon = styx(taxi=True, taxi_rot=R(-90))
    stand_relaxed(charon)
    C.reach(charon, "L", (0.46, 0.12, 1.12), pole=(1, 0.5, -0.5))
    P.parent(charon, root)
    ghost = make_dead("ghost"); ghostify(ghost)
    ghost.location = (0, 2.5, -0.1)
    C.pose(ghost, {"upperarm01.L": (0.75, 0, 1), "lowerarm01.L": (0.25, -0.2, 1),
                   "upperarm01.R": (-0.75, 0, 1), "lowerarm01.R": (-0.25, -0.2, 1)})
    P.parent(ghost, root)
    for o in list(bpy.data.objects):
        if o.name.startswith(("dock", "dc")):
            for c in [o] + list(o.children_recursive):
                c.hide_render = True
    root.rotation_euler = (0, 0, R(90))
    key_loc(root, 1, (-3.5, 9, 0)); key_loc(root, n, (3.0, 9, 0))
    P.drive(hull, "rotation_euler", 1, "0.03*sin(frame/9.0)")
    camera([(1, (-5.5, 2.5, 0.45), (-2.5, 9, 1.1)), (n, (5.2, 4.6, 1.9), (3.4, 9, 1.2))], lens=22)


def dig_setup(thief, phase=0, n=80, period=16):
    def down():
        C.reset_pose(thief)
        C.pose(thief, {"spine05": (0, -0.25, 1), "spine03": (0, -0.6, 1), "spine01": (0, -0.75, 1)})
        C.aim(thief, "head", (0, -0.9, 0.5))
        C.reach(thief, "R", (-0.12, -0.5, 0.95), pole=(-1, 0.5, 0))
        C.reach(thief, "L", (0.1, -0.78, 0.62), pole=(1, 0.5, 0))
        for s in "LR":
            C.curl_fingers(thief, s, 0.9, 0.6)

    def up():
        C.reset_pose(thief)
        C.pose(thief, {"spine05": (0, -0.05, 1), "spine03": (0, -0.12, 1)})
        C.aim(thief, "head", (0, -0.5, 1))
        C.reach(thief, "R", (-0.2, -0.32, 1.22), pole=(-1, 0.5, 0))
        C.reach(thief, "L", (0.14, -0.55, 0.98), pole=(1, 0.5, 0))
        for s in "LR":
            C.curl_fingers(thief, s, 0.9, 0.6)

    down()
    hr = C.bone_world(thief, "wrist.R", tail=True); hl = C.bone_world(thief, "wrist.L", tail=True)
    sh = P.shovel()
    d = (hl - hr).normalized()
    sh.location = hr - d * 0.12
    sh.rotation_euler = (-d).to_track_quat("Z", "Y").to_euler()
    C.attach(sh, thief, "wrist.R")
    f = 1 - phase
    i = 0
    while f <= n + period:
        (down if i % 2 == 0 else up)()
        C.key_pose(thief, max(f, -40))
        f += period // 2
        i += 1
    return sh


G_PITS = [(0, 0), (4.8, 0), (9.6, 0)]
G_CLOSED = [(-3.2, 0), (-6.4, 0), (-3.2, 4.5), (0, 4.5), (3.2, 4.5), (-6.4, 4.5), (6.4, 4.5), (9.6, 4.5), (12.8, 0)]


def thieves_yard(n, frame_off=0):
    """Night graveyard: glowing markers show where the coins are; each thief digs inside a marked grave."""
    graveyard(night=True, pits=G_PITS, closed=G_CLOSED, greek=False, seed=4)
    gm = P.M("mark", (1, 0.8, 0.2), emit=(1.0, 0.7, 0.1), es=2.5, metal=1, rough=0.2)
    for i, (x, y) in enumerate(G_CLOSED + G_PITS):
        c = P.cyl("marker", 0.22, 0.04, (x, y + 0.8, 1.9), gm, segs=32, rot=(R(90), 0, 0))
        P.drive(c, "rotation_euler", 2, f"(frame+{frame_off})*0.12+{i}")
        P.drive(c, "location", 2, f"2.0+0.08*sin((frame+{frame_off})/6.0+{i})")
        point((x, y + 0.8, 1.5), 25, (1.0, 0.75, 0.3), radius=0.2)
    rnd = random.Random(11)
    clod = P.sphere("clod", 0.06, (0, 0, -50), mat("soil"), subdiv=1)
    P.displace(clod, 0.02, 0.05)
    total = frame_off + n
    for i, (px, py) in enumerate(G_PITS):
        if i != 1:
            t = make_thief(f"thief{i}")
            t.rotation_euler = (0, 0, R(180)); t.location = (px, 0.05, -0.75)
            dig_setup(t, phase=(i * 5 + frame_off) % 16, n=n, period=16)
            # soil thrown out of the grave on every upswing
            f = 9 - (i * 5) % 16
            while f < total + 16:
                for k in range(4):
                    d = P.dup(clod)
                    d.scale = (rnd.uniform(0.6, 1.4),) * 3
                    ballistic(d, f - frame_off + k, (px + 0.1, 0.75, -0.25), (rnd.uniform(1.3, 1.9), rnd.uniform(-0.3, 0.3), rnd.uniform(3.6, 4.6)),
                              floor=0.28, frames=30, bounce=0)
                    key_vis(d, f - frame_off + k - 2, False); key_vis(d, f - frame_off + k - 1, True)
                f += 16
        P.sack((px - 1.35, 1.6, 0), 0.8)
        P.place("wooden_lantern_01", (px - 0.95, -0.6, 0), 1.6)
        point((px - 0.95, -0.6, 0.5), 110, (1.0, 0.6, 0.25), radius=0.12)
    bx = 11.5
    P.box("bank", (7, 4, 4.2), (bx, 13, 2.1), mat("marble"))
    for k in range(4):
        P.column("bcol", (bx - 2.4 + k * 1.6, 10.6, 0), h=3.4, r=0.26)
    P.box("bank_top", (7.4, 1.4, 0.7), (bx, 10.8, 4.2), mat("marble"), bevel=0.03)
    P.text("bank_t", "BANK", 0.5, (bx, 10.05, 4.2), (R(90), 0, 0), P.M("bankt", (1, 0.8, 0.2), emit=(1.0, 0.75, 0.2), es=2), extrude=0.03)
    point((bx, 9.3, 2.2), 900, (1.0, 0.8, 0.5), radius=0.6)


G1_END = ((1.7, -1.9, 1.5), (0.0, 0.7, 0.35))


def shot_G1(n):
    thieves_yard(n)
    camera([(1, (0, -8.5, 8.5), (0, 3, 0)), (34, (0.6, -5.0, 4.2), (0, 1.5, 0.6)), (n, *G1_END)], lens=20)


def shot_G2(n):
    """Continues G1 without a cut: the camera tracks along the row of robbed graves, coins flying into the sacks."""
    thieves_yard(n, frame_off=nframes("G1"))
    rnd = random.Random(9)
    base = P.coin(r=0.035); base.location = (0, 0, -50)
    for i, (px, py) in enumerate(G_PITS):
        for k in range(7):
            c = P.dup(base)
            f0 = 4 + i * 14 + k * 5 + rnd.randint(0, 3)
            ballistic(c, f0, (px + rnd.uniform(-0.2, 0.2), 1.1, -0.5),
                      (rnd.uniform(-1.3, -0.9), rnd.uniform(0.2, 0.5), rnd.uniform(4.6, 5.4)), floor=0.02, frames=44)
    camera([(1, *G1_END), (32, (4.9, -3.6, 1.6), (4.8, 0.8, 0.6)), (n, (9.9, -2.1, 1.5), (9.6, 0.6, 0.45))], lens=20)


def fire_pit(loc, scale=1.0, watts=260, notes=0, seed=1, frames=0, top=7.0, hero=True, big=2.4):
    """Stone fire pit with flames (volumetric for the hero fire, light mesh flames for distant ones);
    optionally a column of burning paper notes rising from it."""
    P.place("stone_fire_pit", (loc[0], loc[1], 0.12), 0.8 * scale, seed)
    if hero:
        P.fire_volume((loc[0], loc[1], 0.1), scale=scale, watts=watts)
        P.embers((loc[0], loc[1], 0.5), n=14, radius=0.25 * scale, height=3.0, seed=seed)
    else:
        P.fire((loc[0], loc[1], 0.15), scale=1.5 * scale, n=4, watts=watts, seed=seed)
    if notes:
        flying_notes((loc[0], loc[1], 0), notes, frames, seed=seed, radius=0.5 * scale, top=top, rise=0.075, big=big, start_z=0.6)


def shot_S(n):
    """One continuous camera move: through the gate -> buried gold and a lurking thief -> family burning
    paper money -> the ghost receiving it -> the thief finding only ash -> fires everywhere, notes filling the sky."""
    GOLD, ASH, FIRE = (-3.6, 3.0), (3.6, 3.0), (0.0, 2.6)
    china(pits=(GOLD, ASH))
    rnd = random.Random(3)
    # --- the old way: gold in the grave
    P.place("treasure_chest", (GOLD[0], GOLD[1] + 0.25, -0.63), 0.9, 0.3)
    for i in range(10):
        ig = P.ingot((GOLD[0] + rnd.uniform(-0.45, 0.45), GOLD[1] - 0.35 + rnd.uniform(-0.25, 0.25), -0.62 + 0.06 * (i // 5)), s=rnd.uniform(1.3, 1.8))
        ig.rotation_euler = (0, 0, rnd.uniform(0, 3))
    base = P.coin(r=0.04); base.location = (0, 0, -50)
    for i in range(34):
        c = P.dup(base)
        c.location = (GOLD[0] + rnd.uniform(-0.55, 0.55), GOLD[1] + rnd.uniform(-0.65, 0.65), -0.615 + rnd.uniform(0, 0.03))
        c.rotation_euler = (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0)
    point((GOLD[0], GOLD[1], -0.1), 70, (1.0, 0.8, 0.4), radius=0.3)
    P.place("boulder_01", (-4.9, 4.5, 0), 1.25, 1.2)
    thief = make_thief("thief")
    C.pose(thief, {"spine03": (0, -0.3, 1)})
    C.aim(thief, "head", (0.25, -0.5, 1))
    C.reach(thief, "R", (-0.25, -0.35, 1.25), pole=(-1, 0.5, -0.5)); C.reach(thief, "L", (0.2, -0.3, 1.0), pole=(1, 0.5, -0.5))
    thief.rotation_euler = (0, 0, R(-35))
    key_loc(thief, 1, (-6.3, 5.3, -0.35)); key_loc(thief, 168, (-6.3, 5.3, -0.35))
    key_loc(thief, 190, (-5.75, 5.05, -0.12)); key_loc(thief, 215, (-5.7, 5.0, -0.1)); key_loc(thief, 240, (-6.3, 5.3, -0.35))
    # --- the new way: the family burns paper money
    fire_pit(FIRE, 1.0, watts=200, notes=26, seed=2, frames=n, top=6.0, big=1.2)
    kin = make_kin(skin="middleage_asian_male")
    kin.rotation_euler = (0, 0, R(90)); kin.location = (FIRE[0] - 1.0, FIRE[1], 0)
    C.pose(kin, {"spine03": (0, -0.2, 1)})
    C.legs_together(kin)
    C.aim(kin, "head", (0, -0.6, 1))
    C.reach(kin, "L", Vector((FIRE[0] - 0.42, FIRE[1] + 0.12, 1.3)), pole=(0.6, 0.5, -1), world=True)
    C.reach(kin, "R", Vector((FIRE[0] - 0.42, FIRE[1] - 0.12, 1.3)), pole=(-0.6, 0.5, -1), world=True)
    for sd in "LR":
        C.curl_fingers(kin, sd, 0.5, 0.5)
    nb = P.note("jn", 0.19, 0.085); nb.location = (0, 0, -50)
    for i in range(6):
        st = P.dup(nb); st.location = (FIRE[0] - 0.43, FIRE[1], 1.24 + i * 0.006); st.rotation_euler = (0, 0, R(90) + rnd.uniform(-0.2, 0.2))
    for i in range(14):
        d = P.dup(nb)
        f0 = 196 + i * 5
        ballistic(d, f0, (FIRE[0] - 0.4, FIRE[1] + rnd.uniform(-0.08, 0.08), 1.27), (rnd.uniform(0.3, 0.6), rnd.uniform(-0.12, 0.12), 0.7),
                  floor=0.45, g=3.2, frames=40, spin=(4, 3, 2), bounce=0)
        key_vis(d, 1, False); key_vis(d, f0 - 1, True); key_vis(d, f0 + 24, True); key_vis(d, f0 + 28, False)
    mourner(0, PEOPLE[0], (1.15, 3.7, 0), 20)
    mourner(1, PEOPLE[2], (-0.7, 4.0, 0), -15)
    # --- the dead still got paid: the ghost above the flames
    ghost = make_dead("ghost"); ghostify(ghost)
    C.legs_together(ghost)
    C.pose(ghost, {"upperarm01.L": (0.8, -0.3, 0.6), "lowerarm01.L": (0.2, -0.6, 0.8),
                   "upperarm01.R": (-0.8, -0.3, 0.6), "lowerarm01.R": (-0.2, -0.6, 0.8)})
    C.aim(ghost, "head", (0, -0.5, 1))
    ghost.location = (0.5, 3.0, 3.1)
    P.drive(ghost, "location", 2, "3.1+0.06*sin(frame/8.0)")
    for c in ghost.children_recursive:
        c.hide_render = True; c.keyframe_insert("hide_render", frame=1); c.keyframe_insert("hide_render", frame=255)
        c.hide_render = False; c.keyframe_insert("hide_render", frame=256)
    falling_notes((0.5, 2.9, 2.6), 40, n, radius=0.9, top=2.6)
    point((0.5, 2.6, 3.6), 80, (0.4, 0.8, 1.0), radius=0.5)
    # --- the thieves got nothing but ash
    ash = P.sphere("ashpile", 0.4, (ASH[0], ASH[1] - 0.25, -0.62), mat("ash"), scale=(1, 1.2, 0.3), subdiv=4)
    P.displace(ash, 0.1, 0.2)
    t2 = make_thief("thief2")
    t2.location = (ASH[0], ASH[1] + 0.4, -0.63)
    C.pose(t2, {"spine03": (0, -0.3, 1)})
    C.aim(t2, "head", (0, -0.7, 0.8))
    C.reach(t2, "L", (0.16, -0.42, 1.02), pole=(1, 0.5, -0.5)); C.reach(t2, "R", (-0.16, -0.42, 1.02), pole=(-1, 0.5, -0.5))
    C.twist(t2, "lowerarm02.L", 80, "Y"); C.twist(t2, "lowerarm02.R", -80, "Y")
    for c in t2.children_recursive:
        c.hide_render = True; c.keyframe_insert("hide_render", frame=1); c.keyframe_insert("hide_render", frame=285)
        c.hide_render = False; c.keyframe_insert("hide_render", frame=286)
    for i in range(46):
        ab = P.sphere("ashbit", rnd.uniform(0.008, 0.02), (0, 0, -50), mat("ash"), subdiv=1)
        f0 = 300 + rnd.randint(0, 70)
        ballistic(ab, f0, (ASH[0] + rnd.uniform(-0.2, 0.2), ASH[1] - 0.03 + rnd.uniform(-0.05, 0.05), 0.38), (rnd.uniform(-0.1, 0.1), -0.1, 0),
                  floor=-0.5, g=5.0, frames=22, spin=(0, 0, 0), bounce=0)
    sh = P.shovel(); sh.location = (ASH[0] + 0.9, ASH[1] + 0.5, 1.2); sh.rotation_euler = (R(6), R(-10), 0)
    # --- today: fires everywhere, notes filling the sky
    for i, (x, y, sc) in enumerate(((-4.6, -3.2, 1.2), (4.6, -3.6, 1.3), (-5.2, 8.6, 1.1), (5.0, 9.0, 1.2),
                                    (-13, 4, 2.2), (13, 6, 2.4), (0, 17, 2.6), (-12, -9, 2.2), (12, -10, 2.2))):
        fire_pit((x, y, 0), sc, watts=160 * sc, notes=34, seed=10 + i, frames=n, top=13.0, hero=False)
    flying_notes((0, -1.0, 0), 130, n, seed=77, radius=6.0, top=17.0, rise=0.07, big=3.2, start_z=3.0, spread=0.004)
    camera([
        (1, (0.6, -15, 0.9), (0, 0, 3.4)),
        (70, (0.3, -6.5, 1.5), (0, 0.5, 2.6)),
        (125, (0.2, -1.2, 1.7), (0, 3.5, 1.2)),
        (165, (-1.9, 0.6, 1.9), (GOLD[0], GOLD[1], -0.3)),
        (198, (-2.4, 1.3, 1.5), (-5.2, 4.8, 1.25)),
        (232, (-0.4, 0.5, 1.5), (FIRE[0], FIRE[1], 0.9)),
        (264, (0.55, 1.2, 1.2), (0.1, 2.6, 1.0)),
        (292, (0.9, 0.5, 1.5), (0.5, 3.0, 3.9)),
        (306, (1.0, 0.4, 1.8), (0.5, 3.0, 4.0)),
        (336, (2.4, 0.7, 2.0), (ASH[0], ASH[1] + 0.2, -0.1)),
        (358, (2.8, 1.5, 1.3), (ASH[0], ASH[1] + 0.4, 0.75)),
        (384, (1.2, 0.2, 1.6), (0.4, 3.0, 1.6)),
        (410, (0.9, -3.8, 2.6), (0, 2.6, 3.0)),
        (n, (0.7, -8.5, 5.4), (0, 3, 12.0)),
    ], lens=19)


def shot_T(n):
    """Continuous: the coin still in the dead man's mouth -> pull back and up to the thief on his pile of gold."""
    graveyard(night=False)
    dead = grave_body(coin_in_mouth=True)
    mp = mouth_pos(dead)
    c = P.coin(r=0.024); c.location = mp; c.rotation_euler = (R(12), 0, 0)
    rnd = random.Random(1)
    base = P.coin(r=0.045); base.location = (0, 0, -50)
    for i in range(18):
        d = P.dup(base)
        tx = rnd.uniform(-0.38, 0.38); ty = rnd.uniform(0.2, 1.5)
        on_body = abs(tx) < 0.17 and 0.75 < ty < 1.3
        d.location = (tx, ty, -0.75 + (0.275 if on_body else 0.012))
        d.rotation_euler = (rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), 0)
    G = (0.0, 4.4)
    pile = P.sphere("goldpile", 1.0, (G[0], G[1], -0.1), mat("gold"), scale=(1.5, 1.5, 0.55), subdiv=4)
    P.displace(pile, 0.12, 0.12)
    big = P.coin(r=0.05); big.location = (0, 0, -50)
    for i in range(150):
        a = rnd.uniform(0, 6.28); r = 1.65 * math.sqrt(rnd.random())
        d = P.dup(big)
        d.location = (G[0] + math.cos(a) * r, G[1] + math.sin(a) * r, max(0.02, 0.46 * (1 - (r / 1.5) ** 2)) + 0.02)
        d.rotation_euler = (rnd.uniform(-0.7, 0.7), rnd.uniform(-0.7, 0.7), 0)
    P.place("treasure_chest", (G[0] + 1.5, G[1] - 0.3, 0), 1.1, -0.5)
    P.place("treasure_chest", (G[0] - 1.6, G[1] + 0.1, 0), 1.0, 0.6)
    P.sack((G[0] + 1.0, G[1] + 1.0, 0.1), 1.2)
    thief = make_thief()
    thief.location = (G[0], G[1] + 0.1, 0.42)
    up = {"upperarm01.L": (0.7, -0.1, 1), "lowerarm01.L": (0.2, -0.2, 1), "upperarm01.R": (-0.7, -0.1, 1), "lowerarm01.R": (-0.2, -0.2, 1)}
    down = {"upperarm01.L": (0.9, -0.3, 0.5), "lowerarm01.L": (0.4, -0.5, 1), "upperarm01.R": (-0.9, -0.3, 0.5), "lowerarm01.R": (-0.4, -0.5, 1)}
    C.legs_together(thief, 0.08)
    C.aim(thief, "head", (0, 0.15, 1))
    for f, pz in ((1, down), (52, down), (62, up), (76, down), (86, up), (100, down), (n, up)):
        C.pose(thief, pz); C.key_pose(thief, f)
    for i in range(40):
        d = P.dup(big)
        sx = rnd.choice((-1, 1))
        f0 = rnd.choice((60, 62, 84, 86, 108)) + rnd.randint(0, 5)
        ballistic(d, f0, (G[0] + sx * 0.45, G[1], 2.25), (sx * rnd.uniform(0.2, 1.3), rnd.uniform(-1.0, 0.6), rnd.uniform(2.5, 4.6)),
                  floor=0.1, frames=50)
    camera([(1, (0.1, 1.02, -0.02), mp), (40, (0.3, 0.5, 1.2), mp + Vector((0, 0.1, 0))),
            (74, (0.6, -0.2, 1.9), (G[0], G[1] - 0.5, 1.2)), (n, (0.9, -0.9, 2.15), (G[0], G[1], 1.55))], lens=20)


SHOTS = {k: globals()["shot_" + k] for k in TIMES}


def setup_render(preview, threads):
    s = bpy.context.scene
    if os.environ.get("NOSSS", "0") == "1":
        for m in bpy.data.materials:
            if m.node_tree:
                for nd in m.node_tree.nodes:
                    if nd.type == "BSDF_PRINCIPLED":
                        nd.inputs["Subsurface Weight"].default_value = 0.0
                        for l in list(nd.inputs["Subsurface Weight"].links):
                            m.node_tree.links.remove(l)
    eevee = os.environ.get("ENGINE", "CYCLES") == "EEVEE"
    s.render.engine = "BLENDER_EEVEE" if eevee else "CYCLES"
    s.render.fps = FPS
    if eevee:
        ee = s.eevee
        for k, v in (("taa_render_samples", int(os.environ.get("SPP", 16))), ("use_raytracing", os.environ.get("RT", "0") == "1"),
                     ("use_shadows", True), ("shadow_ray_count", 1), ("shadow_step_count", 4), ("use_gtao", True)):
            try:
                setattr(ee, k, v)
            except Exception as e:
                print("EEVEE_SET_FAIL", k, e)
        for m in bpy.data.materials:
            if m.node_tree and any(nd.type in ("BSDF_TRANSPARENT",) or (nd.type == "BSDF_PRINCIPLED" and (nd.inputs["Alpha"].links or nd.inputs["Alpha"].default_value < 1)) for nd in m.node_tree.nodes):
                try:
                    m.surface_render_method = "BLENDED" if any(nd.type == "BSDF_TRANSPARENT" for nd in m.node_tree.nodes) else "DITHERED"
                except Exception as e:
                    print("MAT_FAIL", e)
    c = s.cycles
    c.samples = 10 if preview or eevee else int(os.environ.get("SPP", 10))
    c.use_adaptive_sampling = True
    c.adaptive_threshold = float(os.environ.get("AT", 0.08))
    c.use_denoising = os.environ.get("DN", "1") == "1"
    try:
        c.denoising_quality = os.environ.get("DNQ", "FAST")
        c.denoising_input_passes = "RGB_ALBEDO"
    except Exception as e:
        print("DNQ_FAIL", e)
    c.adaptive_min_samples = 4
    c.max_bounces = 3
    c.diffuse_bounces = 1
    c.glossy_bounces = 2
    c.transmission_bounces = 2
    c.transparent_max_bounces = 8
    c.volume_step_rate = 2.0
    c.volume_max_steps = 64
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.sample_clamp_indirect = 6
    s.render.use_persistent_data = True
    s.render.resolution_x, s.render.resolution_y = (360, 640) if preview else tuple(int(v) for v in os.environ.get("RES", "630x1120").split("x"))
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = "JPEG"
    s.render.image_settings.quality = 93
    try:
        s.view_settings.view_transform = "Khronos PBR Neutral"
        s.view_settings.look = "None"
    except Exception as e:
        print("LOOK_FAIL", e)
    s.view_settings.exposure = float(os.environ.get("EXPO", 0.0))
    if threads:
        s.render.threads_mode = "FIXED"
        s.render.threads = threads


def main():
    a = sys.argv[1:]
    shot = a[0]
    preview = "--preview" in a
    get = lambda k, d: int(a[a.index(k) + 1]) if k in a else d
    n = nframes(shot)
    clear()
    s = bpy.context.scene
    s.frame_start = 1
    s.frame_end = n
    SHOTS[shot](n)
    setup_render(preview, get("--threads", 0))
    if preview:
        frames = [int(x) for x in a[a.index("--frames") + 1].split(",")] if "--frames" in a else [1, n // 2, n]
        for f in frames:
            s.frame_set(f)
            s.render.filepath = os.path.join(ROOT, "work", "prev", f"{shot}_{f:04d}.jpg")
            bpy.ops.render.render(write_still=True)
    elif "--handles" in a:
        # extra real frames before frame 1 and after frame n, so transitions have footage to blend
        h = get("--handles", 6)
        out = os.path.join(ROOT, "work", "handles", shot)
        os.makedirs(out, exist_ok=True)
        jobs = [(1 - h + i, f"pre_{i + 1:02d}.jpg") for i in range(h)] + [(n + 1 + i, f"post_{i + 1:02d}.jpg") for i in range(h)]
        for f, name in jobs:
            path = os.path.join(out, name)
            if os.path.exists(path):
                continue
            s.frame_set(f)
            s.render.filepath = path
            bpy.ops.render.render(write_still=True)
    else:
        out = os.path.join(ROOT, "work", "frames", shot)
        os.makedirs(out, exist_ok=True)
        for f in range(get("--start", 1), get("--end", n) + 1):
            path = os.path.join(out, f"{f:04d}.jpg")
            if os.path.exists(path):
                continue
            s.frame_set(f)
            s.render.filepath = path
            bpy.ops.render.render(write_still=True)
    print("SHOT_DONE", shot, n)


if __name__ == "__main__":
    main()
