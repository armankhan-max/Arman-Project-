"""Character builders (MPFB) and direction-based posing helpers."""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mpfb import enable_mpfb


def _data_dir():
    from bl_ext.user_default.mpfb.services import LocationService
    return LocationService.get_user_data()


def _asset(kind, name, ext):
    return os.path.join(_data_dir(), kind, name, name + ext)


def _activate(obj):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def make_human(name, skin="young_caucasian_male", hair="short02", clothes=(), brows="eyebrow001"):
    """Create a skinned, rigged human. Returns (rig, body, parts)."""
    enable_mpfb()
    before = set(bpy.data.objects)
    bpy.ops.mpfb.create_human()
    body = bpy.context.active_object
    bpy.ops.mpfb.load_library_skin(filepath=_asset("skins", skin, ".mhmat"))
    _activate(body)
    bpy.ops.mpfb.add_standard_rig()
    items = [("eyes", "high-poly"), ("eyebrows", brows), ("eyelashes", "eyelashes01"), ("teeth", "teeth_base"),
             ("tongue", "tongue01")]
    if hair:
        items.append(("hair", hair))
    items += [("clothes", c) for c in clothes]
    for kind, n in items:
        _activate(body)
        path = _asset(kind, n, ".mhclo")
        if not os.path.exists(path):
            print("MISSING_ASSET", path)
            continue
        bpy.ops.mpfb.load_library_clothes(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    rig = next(o for o in new if o.type == "ARMATURE")
    for o in new:
        low = o.name.lower()
        if "teeth" in low or "tongue" in low:
            m = bpy.data.materials.new(low)
            m.use_nodes = True
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Base Color"].default_value = (0.9, 0.88, 0.8, 1) if "teeth" in low else (0.7, 0.25, 0.25, 1)
            b.inputs["Roughness"].default_value = 0.3
            o.data.materials.clear()
            o.data.materials.append(m)
    rig.name = name
    for o in new:
        if o is not rig:
            o.name = name + "." + o.name.split(".", 1)[-1] if "." in o.name else name + ".body"
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return rig, body, [o for o in new if o is not rig and o is not body]


def garment_from_helpers(body, rig, name, mat, sleeves="short", offset=0.022, skirt=True, legs=False):
    """Build a robe/tunic from the base mesh's hidden helper geometry (skirt tube + upper tights)."""
    g = body.copy()
    g.data = body.data.copy()
    g.name = name
    bpy.context.collection.objects.link(g)
    for m in list(g.modifiers):
        if m.type == "MASK":
            g.modifiers.remove(m)
    vg = {v.name: v.index for v in g.vertex_groups}
    arm_groups = {i for n, i in vg.items() if n.startswith(("wrist", "finger", "metacarpal"))}
    if sleeves == "short":
        arm_groups |= {i for n, i in vg.items() if n.startswith(("upperarm02", "lowerarm"))}
    low_names = ("foot", "toe") if legs else ("upperleg", "lowerleg", "foot", "toe", "pelvis")
    low_groups = {i for n, i in vg.items() if n.startswith(low_names)}
    head_groups = {i for n, i in vg.items() if n.startswith(("head", "neck", "jaw"))}
    keep = set()
    for v in g.data.vertices:
        gs = {e.group: e.weight for e in v.groups}
        in_skirt = vg["helper-skirt"] in gs
        in_tights = vg["helper-tights"] in gs
        if skirt and in_skirt:
            keep.add(v.index)
        elif in_tights:
            dom = max(((w, i) for i, w in gs.items() if g.vertex_groups[i].name not in
                       ("helper-tights", "HelperGeometry", "body", "Left", "Right", "Mid")), default=(0, -1))[1]
            if dom in arm_groups or dom in low_groups or dom in head_groups:
                continue
            keep.add(v.index)
    bm = bmesh.new()
    bm.from_mesh(g.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context="VERTS")
    bm.to_mesh(g.data)
    bm.free()
    if g.data.shape_keys:
        _activate(g)
        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    g.data.materials.clear()
    g.data.materials.append(mat)
    disp = g.modifiers.new("Puff", "DISPLACE")
    disp.strength = offset
    disp.mid_level = 0
    sub = g.modifiers.new("Sub", "SUBSURF")
    sub.levels = sub.render_levels = 1
    # keep armature last-but-before subdivision ordering sane: armature already copied from body
    for p in g.data.polygons:
        p.use_smooth = True
    return g


# ---------- posing ----------

def _update():
    bpy.context.view_layer.update()


def aim(rig, bone, direction):
    """Rotate pose bone so it points along `direction` (rig space), minimal rotation."""
    pb = rig.pose.bones[bone]
    _update()
    m = pb.matrix.copy()
    cur = (m.to_3x3() @ Vector((0, 1, 0))).normalized()
    q = cur.rotation_difference(Vector(direction).normalized())
    rot = (q.to_matrix() @ m.to_3x3()).to_4x4()
    rot.translation = m.translation
    pb.matrix = rot
    _update()


def twist(rig, bone, deg, axis="Y"):
    pb = rig.pose.bones[bone]
    pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion({"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}[axis],
                                                                 math.radians(deg))
    _update()


def pose(rig, spec):
    """spec: ordered {bone: direction | ('twist', axis, deg)}; parents must come before children."""
    for bone, val in spec.items():
        if isinstance(val, tuple) and val and val[0] == "twist":
            twist(rig, bone, val[2], val[1])
        else:
            aim(rig, bone, val)


def reset_pose(rig):
    for pb in rig.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    _update()


def key_pose(rig, frame, bones=None):
    for pb in rig.pose.bones:
        if bones is None or pb.name in bones:
            pb.keyframe_insert("rotation_quaternion", frame=frame)


def curl_fingers(rig, side, amount=0.6, thumb=0.3):
    for f in range(2, 6):
        for j in range(1, 4):
            twist(rig, f"finger{f}-{j}.{side}", amount * 55, "X")
    for j in range(1, 4):
        twist(rig, f"finger1-{j}.{side}", thumb * 30, "X")


def close_eyes(rig, amount=1.0):
    for s in "LR":
        twist(rig, f"orbicularis03.{s}", -30 * amount, "X")
        twist(rig, f"orbicularis04.{s}", -8 * amount, "X")


def open_jaw(rig, deg=18):
    twist(rig, "jaw", deg, "X")


def reach(rig, side, target, pole=(0, 0.6, -1), world=False):
    """Two-bone IK: put the palm of `side` arm at target (rig space unless world=True)."""
    _update()
    P = rig.matrix_world.inverted() @ Vector(target) if world else Vector(target)
    ua = rig.pose.bones[f"upperarm01.{side}"]
    la = rig.pose.bones[f"lowerarm01.{side}"]
    wr = rig.pose.bones[f"wrist.{side}"]
    S = ua.head.copy()
    L1 = (la.bone.head_local - ua.bone.head_local).length
    L2 = (wr.bone.head_local - la.bone.head_local).length + 0.08
    v = P - S
    d = min(v.length, (L1 + L2) * 0.999)
    n = v.normalized()
    a = (L1 * L1 - L2 * L2 + d * d) / (2 * d)
    h = math.sqrt(max(L1 * L1 - a * a, 0))
    pv = Vector(pole)
    perp = pv - n * pv.dot(n)
    perp = perp.normalized() if perp.length > 1e-5 else Vector((0, 0, -1))
    E = S + n * a + perp * h
    aim(rig, ua.name, E - S)
    aim(rig, la.name, (S + n * d) - E)


def bone_world(rig, bone, tail=False):
    _update()
    pb = rig.pose.bones[bone]
    return rig.matrix_world @ (pb.tail if tail else pb.head)


def attach(obj, rig, bone):
    """Parent obj to a bone, keeping its current world transform."""
    _update()
    mw = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    _update()
    obj.matrix_world = mw
    _update()


def head_center(rig):
    b = rig.data.bones["head"]
    return rig.matrix_world @ (b.head_local + (b.tail_local - b.head_local) * 0.5 + Vector((0, -0.02, 0)))


def legs_together(rig, gap=0.035):
    for s, sx in (("L", 1), ("R", -1)):
        aim(rig, f"upperleg01.{s}", (sx * gap, 0, -1))
        aim(rig, f"lowerleg01.{s}", (sx * gap * 0.5, 0, -1))
