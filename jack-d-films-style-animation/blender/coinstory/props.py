"""Procedural materials and props."""
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector


def link(o):
    bpy.context.scene.collection.objects.link(o)
    return o


def bsdf(m):
    return m.node_tree.nodes["Principled BSDF"]


def M(name, color, rough=0.5, metal=0.0, emit=None, es=0.0, alpha=1.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = bsdf(m)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = es
    return m


def add_noise(m, scale=8.0, bump=0.3, color2=None, detail=6.0, anim=0.0, coords="Object", stretch=None):
    nt = m.node_tree
    b = bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    src = tc.outputs[coords]
    if stretch:
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = stretch
        nt.links.new(src, mp.inputs["Vector"])
        src = mp.outputs["Vector"]
    nt.links.new(src, n.inputs["Vector"])
    if anim:
        n.noise_dimensions = "4D"
        fc = n.inputs["W"].driver_add("default_value")
        fc.driver.expression = f"frame*{anim}"
    if bump:
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump
        nt.links.new(n.outputs["Fac"], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    if color2:
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[1].position = 0.65
        ramp.color_ramp.elements[0].color = tuple(b.inputs["Base Color"].default_value)
        ramp.color_ramp.elements[1].color = (*color2, 1)
        nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


def from_bm(name, bm, mat=None, smooth=False, loc=(0, 0, 0), rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    if mat:
        me.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    o.location = loc
    o.rotation_euler = rot
    return o


def box(name, size, loc, mat, rot=(0, 0, 0), bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    o = from_bm(name, bm, mat, loc=loc, rot=rot)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL")
        b.width = bevel
        b.segments = 2
    return o


def cyl(name, r, h, loc, mat, segs=32, r2=None, rot=(0, 0, 0), smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h)
    o = from_bm(name, bm, mat, loc=loc, rot=rot)
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = abs(p.normal.z) < 0.9
    return o


def sphere(name, r, loc, mat, scale=(1, 1, 1), subdiv=3, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    o = from_bm(name, bm, mat, smooth=smooth, loc=loc)
    o.scale = scale
    return o


def displace(o, strength, size, seed=0):
    tex = bpy.data.textures.new(o.name + "_t", "CLOUDS")
    tex.noise_scale = size
    tex.noise_depth = 3
    mod = o.modifiers.new("disp", "DISPLACE")
    mod.texture = tex
    mod.strength = strength
    mod.texture_coords = "GLOBAL" if seed else "LOCAL"
    return mod


def text(name, body, size, loc, rot, mat, extrude=0.004):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    o = link(bpy.data.objects.new(name, cu))
    cu.materials.append(mat)
    o.location = loc
    o.rotation_euler = rot
    return o


def parent(child, par):
    bpy.context.view_layer.update()
    child.parent = par
    child.matrix_parent_inverse = par.matrix_world.inverted()


def empty(name, loc=(0, 0, 0)):
    e = link(bpy.data.objects.new(name, None))
    e.location = loc
    return e


def drive(o, path, idx, expr):
    fc = o.driver_add(path, idx) if idx is not None else o.driver_add(path)
    fc.driver.expression = expr


# ---------- materials ----------
_cache = {}
ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")


def tex_nodes(m, slot, scale=1.0, tint=None, normal=1.0):
    """Wire Poly Haven diffuse/rough/normal maps (box projected) into material m. Returns the colour socket."""
    nt = m.node_tree
    b = bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

    def img(suffix, cs):
        path = os.path.join(ASSETS, "tex", f"{slot}_{suffix}.jpg")
        if not os.path.exists(path):
            return None
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(path, check_existing=True)
        n.image.colorspace_settings.name = cs
        n.projection = "BOX"
        n.projection_blend = 0.25
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
        return n

    d = img("diff", "sRGB")
    col = d.outputs["Color"]
    if tint:
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.blend_type = "MULTIPLY"
        mx.inputs[0].default_value = 1.0
        nt.links.new(col, mx.inputs[6])
        mx.inputs[7].default_value = (*tint, 1)
        col = mx.outputs[2]
    nt.links.new(col, b.inputs["Base Color"])
    r = img("rough", "Non-Color")
    if r:
        nt.links.new(r.outputs["Color"], b.inputs["Roughness"])
    nr = img("nor", "Non-Color")
    if nr:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = normal
        nt.links.new(nr.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return col


def tex_mat(slot, scale=1.0, tint=None, normal=1.0, name=None):
    m = M(name or ("tx_" + slot), (0.5, 0.5, 0.5))
    tex_nodes(m, slot, scale, tint, normal)
    return m


def mat(key):
    if key in _cache:
        return _cache[key]
    if key == "gold":
        m = M("gold", (1.0, 0.6, 0.1), rough=0.3, metal=1.0, emit=(1.0, 0.55, 0.05), es=0.25)
    elif key == "stone":
        m = tex_mat("stone", 1.2, tint=(1.15, 1.15, 1.2))
    elif key == "marble":
        m = tex_mat("marble", 0.6, tint=(1.0, 0.98, 0.94), normal=0.5)
    elif key == "soil":
        m = tex_mat("soil", 1.0, tint=(1.3, 1.1, 0.9))
    elif key == "wood":
        m = tex_mat("wood", 1.2, tint=(1.2, 0.95, 0.75))
    elif key == "black":
        m = M("black", (0.02, 0.02, 0.025), rough=0.7)
    elif key == "white":
        m = M("white", (0.92, 0.92, 0.9), rough=0.6)
    elif key == "red":
        m = M("red", (0.75, 0.05, 0.04), rough=0.35, coat=0.6)
    elif key == "bronze":
        m = add_noise(M("bronze", (0.5, 0.3, 0.12), rough=0.35, metal=1.0), scale=30, bump=0.15)
    elif key == "ash":
        m = add_noise(M("ash", (0.42, 0.42, 0.42), rough=1.0), scale=40, bump=0.9, color2=(0.2, 0.2, 0.2))
    elif key == "paper":
        m = M("paper", (0.98, 0.8, 0.25), rough=0.6)
    elif key == "paper_red":
        m = M("paper_red", (0.85, 0.08, 0.05), rough=0.5)
    elif key == "sack":
        m = add_noise(M("sack", (0.62, 0.48, 0.3), rough=0.9), scale=80, bump=0.4)
    elif key == "leaf":
        m = add_noise(M("leaf", (0.04, 0.42, 0.1), rough=0.8), scale=10, bump=0.6, color2=(0.02, 0.22, 0.06))
    elif key == "blossom":
        m = add_noise(M("blossom", (1.0, 0.55, 0.7), rough=0.7), scale=12, bump=0.5, color2=(1.0, 0.8, 0.88))
    elif key == "flame":
        m = flame_mat()
    elif key == "ember":
        m = M("ember", (1, 0.4, 0.05), emit=(1.0, 0.45, 0.05), es=3)
    else:
        raise KeyError(key)
    _cache[key] = m
    return m


def flame_mat():
    m = bpy.data.materials.new("flame")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(bsdf(m))
    out = nt.nodes["Material Output"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    col = nt.nodes.new("ShaderNodeValToRGB")
    e = col.color_ramp.elements
    e[0].position = 0.0; e[0].color = (1.0, 0.7, 0.08, 1)
    e[1].position = 0.85; e[1].color = (0.7, 0.03, 0.0, 1)
    mid = e.new(0.4); mid.color = (1.0, 0.25, 0.0, 1)
    nt.links.new(sep.outputs["Z"], col.inputs["Fac"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(col.outputs["Color"], em.inputs["Color"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    fade = nt.nodes.new("ShaderNodeValToRGB")
    fade.color_ramp.elements[0].position = 0.45; fade.color_ramp.elements[0].color = (1, 1, 1, 1)
    fade.color_ramp.elements[1].position = 1.0; fade.color_ramp.elements[1].color = (0, 0, 0, 1)
    nt.links.new(sep.outputs["Z"], fade.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fade.outputs["Color"], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def ghost_mat():
    m = bpy.data.materials.new("ghost")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(bsdf(m))
    out = nt.nodes["Material Output"]
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    col = nt.nodes.new("ShaderNodeValToRGB")
    col.color_ramp.elements[0].color = (0.12, 0.5, 0.9, 1)
    col.color_ramp.elements[1].color = (0.75, 1.0, 1.0, 1)
    nt.links.new(lw.outputs["Facing"], col.inputs["Fac"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(col.outputs["Color"], em.inputs["Color"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    fac = nt.nodes.new("ShaderNodeMath")
    fac.operation = "MULTIPLY_ADD"
    fac.inputs[1].default_value = 0.6
    fac.inputs[2].default_value = 0.38
    nt.links.new(lw.outputs["Facing"], fac.inputs[0])
    nt.links.new(fac.outputs[0], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def ground_mat(top, top2, scale=3.0):
    """Grass on top, soil below ground level (pit walls). `top` tints the grass."""
    m = M("ground", top, rough=0.95)
    nt = m.node_tree
    b = bsdf(m)
    grass = tex_nodes(m, "grass", 0.55, tint=tuple(min(2.0, c * 3.2) for c in top2), normal=1.0)
    stc = nt.nodes.new("ShaderNodeTexCoord")
    smp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(stc.outputs["Object"], smp.inputs["Vector"])
    simg = nt.nodes.new("ShaderNodeTexImage")
    simg.image = bpy.data.images.load(os.path.join(ASSETS, "tex", "soil_diff.jpg"), check_existing=True)
    simg.projection = "BOX"
    simg.projection_blend = 0.25
    nt.links.new(smp.outputs["Vector"], simg.inputs["Vector"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    lt.inputs[1].default_value = -0.03
    nt.links.new(sep.outputs["Z"], lt.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(lt.outputs[0], mix.inputs[0])
    nt.links.new(grass, mix.inputs[6])
    nt.links.new(simg.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    return m


def water_mat():
    m = M("water", (0.0, 0.16, 0.2), rough=0.04, coat=1.0)
    add_noise(m, scale=1.6, bump=0.35, detail=3, anim=0.02)
    return m


# ---------- props ----------

def coin(name="coin", r=0.02):
    o = cyl(name, r, r * 0.16, (0, 0, 0), mat("gold"), segs=36)
    b = o.modifiers.new("bev", "BEVEL")
    b.width = r * 0.04
    return o


def dup(o, name=None):
    d = o.copy()
    if name:
        d.name = name
    return link(d)


def note(name="note", w=0.17, h=0.075):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=8, y_segments=4, size=0.5)
    for v in bm.verts:
        v.co.x *= w; v.co.y *= h
        v.co.z = math.sin(v.co.x / w * 5.0) * 0.006
    o = from_bm(name, bm, mat("paper"), smooth=True)
    o.data.materials.append(mat("paper_red"))
    for p in o.data.polygons:
        c = p.center
        if abs(c.x) < w * 0.26 and abs(c.y) < h * 0.26:
            p.material_index = 1
    return o


def tombstone(name, loc, w=0.7, h=1.1, t=0.16, rot_z=0.0, material="stone"):
    root = empty(name, loc)
    root.rotation_euler = (0, 0, rot_z)
    a = box(name + "_s", (w, t, h), (0, 0, h / 2), mat(material), bevel=0.02)
    b = cyl(name + "_c", w / 2, t * 0.9, (0, 0, h), mat(material), segs=32, rot=(math.radians(90), 0, 0))
    c = box(name + "_b", (w * 1.3, t * 2.2, 0.14), (0, 0, 0.07), mat(material), bevel=0.02)
    for o in (a, b, c):
        o.parent = root
    return root


def column(name, loc, h=4.0, r=0.3, broken=False):
    root = empty(name, loc)
    hh = h * (0.55 if broken else 1.0)
    parts = [cyl(name + "_shaft", r, hh, (0, 0, hh / 2 + 0.25), mat("marble"), segs=18, r2=r * 0.85, smooth=False),
             box(name + "_base", (r * 2.8, r * 2.8, 0.25), (0, 0, 0.125), mat("marble"), bevel=0.02)]
    if not broken:
        parts.append(box(name + "_cap", (r * 2.8, r * 2.8, 0.22), (0, 0, hh + 0.36), mat("marble"), bevel=0.03))
    for o in parts:
        o.parent = root
    return root


def temple(loc, n=4, spacing=1.6, h=4.2):
    root = empty("temple", loc)
    w = spacing * (n - 1)
    for i in range(n):
        column(f"tc{i}", (-w / 2 + i * spacing, 0, 0.3), h=h).parent = root
    box("t_ent", (w + 1.4, 1.2, 0.6), (0, 0, h + 1.05), mat("marble"), bevel=0.03).parent = root
    box("t_step", (w + 2.2, 2.4, 0.3), (0, 0, 0.15), mat("marble"), bevel=0.02).parent = root
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=3, radius1=(w + 1.6) / 1.732, radius2=(w + 1.6) / 1.732, depth=1.2)
    ped = from_bm("t_ped", bm, mat("marble"), loc=(0, 0, h + 1.35), rot=(math.radians(90), math.radians(-30), 0))
    ped.scale = (1, 0.42, 1)
    ped.rotation_euler = (math.radians(90), 0, 0)
    ped.parent = root
    return root


def cypress(loc, h=4.5):
    o = cyl("cypress", 0.55, h, (loc[0], loc[1], loc[2] + h / 2 + 0.4), mat("leaf"), segs=14, r2=0.03)
    cyl("trunk", 0.09, 0.6, (loc[0], loc[1], loc[2] + 0.3), mat("wood"), segs=8)
    return o


def mound(loc, size=(0.9, 0.6, 0.3), material="soil"):
    o = sphere("mound", 1.0, loc, mat(material), scale=size, subdiv=4)
    displace(o, 0.15, 0.35)
    return o


def boat():
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=1.0)
    for v in bm.verts:
        v.co.x *= 2.4; v.co.y *= 0.72; v.co.z *= 0.55
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 0, 1),
                           clear_outer=True)
    for v in bm.verts:
        k = max(0.0, abs(v.co.x) - 1.1)
        v.co.z += k * k * 0.22
        if abs(v.co.x) > 1.9:
            v.co.y *= 0.8
    hull = from_bm("boat", bm, mat("wood"), smooth=True)
    s = hull.modifiers.new("sol", "SOLIDIFY")
    s.thickness = 0.06
    s.offset = 1
    floor = box("boat_floor", (3.2, 1.05, 0.05), (0, 0, -0.42), mat("wood"))
    floor.parent = hull
    for x in (-1.2, 1.2):
        box("seat", (0.18, 1.3, 0.05), (x, 0, -0.1), mat("wood")).parent = hull
    return hull


def lantern(loc, color=(1.0, 0.6, 0.2), watts=120, pole=1.5):
    root = empty("lantern", loc)
    cyl("lpole", 0.02, pole, (0, 0, pole / 2), mat("wood"), segs=8).parent = root
    glow = sphere("lglow", 0.1, (0, 0, pole + 0.08), M("lglow", color, emit=color, es=2.5), scale=(1, 1, 1.25))
    glow.parent = root
    cyl("lcap", 0.08, 0.03, (0, 0, pole + 0.22), mat("bronze"), segs=12).parent = root
    li = bpy.data.lights.new("lanternL", "POINT")
    li.energy = watts
    li.color = color
    li.shadow_soft_size = 0.12
    lo = link(bpy.data.objects.new("lanternL", li))
    lo.location = (0, 0, pole + 0.08)
    lo.parent = root
    return root


def fire(loc, scale=1.0, n=5, watts=300, seed=1):
    rnd = random.Random(seed)
    root = empty("fire", loc)
    drv = empty("fire_drv")
    drive(drv, "location", 2, "-frame*0.09")
    for i in range(n):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        for v in bm.verts:
            t = (v.co.z + 1) / 2
            k = (1 - t) ** 0.8 * 0.95 + 0.05
            v.co.x *= k * 0.22; v.co.y *= k * 0.22
            v.co.z = t * 1.0
        f = from_bm(f"flame{i}", bm, mat("flame"), smooth=True)
        a = rnd.uniform(0, 6.28)
        rr = 0.0 if i == 0 else rnd.uniform(0.08, 0.2)
        f.location = (math.cos(a) * rr, math.sin(a) * rr, 0)
        sc = rnd.uniform(0.6, 1.0) if i else 1.15
        f.scale = (sc, sc, sc * rnd.uniform(0.9, 1.3))
        f.parent = root
        tex = bpy.data.textures.new(f"flame_t{i}", "CLOUDS")
        tex.noise_scale = 0.35
        d = f.modifiers.new("d", "DISPLACE")
        d.texture = tex
        d.strength = 0.28
        d.texture_coords = "OBJECT"
        d.texture_coords_object = drv
        drive(f, "scale", 2, f"{f.scale[2]:.3f}*(1+0.18*sin(frame*0.9+{i * 1.7:.2f}))")
        f.visible_shadow = False
    li = bpy.data.lights.new("fireL", "POINT")
    li.energy = watts
    li.color = (1.0, 0.5, 0.15)
    li.shadow_soft_size = 0.25
    lo = link(bpy.data.objects.new("fireL", li))
    lo.location = (0, 0, 0.45)
    lo.parent = root
    drive(li, "energy", None, f"{watts}*(1+0.25*sin(frame*1.3)+0.12*sin(frame*2.9))")
    root.scale = (scale, scale, scale)
    return root


def embers(loc, n=30, radius=0.4, height=3.0, seed=3, size=0.012):
    rnd = random.Random(seed)
    for i in range(n):
        e = sphere("ember", size, loc, mat("ember"), subdiv=1)
        ph = rnd.uniform(0, 100)
        sp = rnd.uniform(0.03, 0.07)
        a = rnd.uniform(0, 6.28)
        r = rnd.uniform(0.05, radius)
        drive(e, "location", 2, f"{loc[2]:.3f}+((frame*{sp:.3f}+{ph:.2f})%{height:.2f})")
        drive(e, "location", 0, f"{loc[0]:.3f}+{r:.3f}*cos({a:.2f}+frame*0.05)*(1+((frame*{sp:.3f}+{ph:.2f})%{height:.2f})*0.4)")
        drive(e, "location", 1, f"{loc[1]:.3f}+{r:.3f}*sin({a:.2f}+frame*0.05)*(1+((frame*{sp:.3f}+{ph:.2f})%{height:.2f})*0.4)")
        e.visible_shadow = False


def brazier(loc, r=0.38):
    root = empty("brazier", loc)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=r)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 0, 1),
                           clear_outer=True)
    bowl = from_bm("bowl", bm, mat("bronze"), smooth=True, loc=(0, 0, 0.75))
    s = bowl.modifiers.new("sol", "SOLIDIFY")
    s.thickness = 0.03
    bowl.parent = root
    cyl("coals", r * 0.9, 0.04, (0, 0, 0.66), M("coals", (0.9, 0.25, 0.03), emit=(1.0, 0.3, 0.03), es=1.2), segs=24).parent = root
    for i in range(3):
        a = i * 2.094
        leg = cyl("leg", 0.025, 0.72, (math.cos(a) * r * 0.75, math.sin(a) * r * 0.75, 0.33), mat("bronze"), segs=8)
        leg.parent = root
    return root


def ingot(loc, s=1.0):
    root = empty("ingot", loc)
    a = sphere("ing_a", 0.07 * s, (0, 0, 0.03 * s), mat("gold"), scale=(1.5, 0.95, 0.55))
    b = sphere("ing_b", 0.045 * s, (0, 0, 0.06 * s), mat("gold"), scale=(1, 1, 0.8))
    a.parent = root; b.parent = root
    return root


def sack(loc, s=1.0):
    o = sphere("sack", 0.3 * s, (loc[0], loc[1], loc[2] + 0.26 * s), mat("sack"), scale=(1, 1, 1.05), subdiv=4)
    displace(o, 0.08, 0.3)
    cyl("sack_neck", 0.09 * s, 0.14 * s, (loc[0], loc[1], loc[2] + 0.6 * s), mat("sack"), segs=12, r2=0.14 * s)
    return o


def shovel():
    root = empty("shovel")
    cyl("sh_handle", 0.018, 1.15, (0, 0, -0.575), mat("wood"), segs=10).parent = root
    bl = box("sh_blade", (0.2, 0.02, 0.28), (0, 0, -1.27), M("steel", (0.6, 0.62, 0.65), rough=0.3, metal=1.0), bevel=0.008)
    bl.parent = root
    return root


def paifang(loc=(0, 0, 0)):
    root = empty("gate", loc)
    red = mat("red")
    roofm = add_noise(M("roof", (0.03, 0.22, 0.2), rough=0.35, coat=0.5), scale=1, bump=0.0)
    goldm = mat("gold")
    for x in (-2.3, 2.3):
        cyl("g_pil", 0.24, 4.4, (x, 0, 2.2), red, segs=24).parent = root
        box("g_base", (0.75, 0.75, 0.5), (x, 0, 0.25), mat("stone"), bevel=0.04).parent = root
    box("g_beam1", (5.6, 0.34, 0.4), (0, 0, 4.0), red, bevel=0.02).parent = root
    box("g_beam2", (5.0, 0.3, 0.55), (0, 0, 3.35), M("panel", (0.05, 0.2, 0.55), rough=0.4, coat=0.5), bevel=0.02).parent = root
    box("g_trim", (5.05, 0.33, 0.06), (0, 0, 3.66), goldm).parent = root
    box("g_plq", (1.3, 0.38, 0.42), (0, 0, 3.35), goldm, bevel=0.02).parent = root
    for (w, d, z, cx) in ((7.2, 1.7, 4.45, 0), (3.6, 1.5, 5.25, 0)):
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=24, y_segments=8, size=0.5)
        for v in bm.verts:
            xx = v.co.x * 2; yy = v.co.y * 2
            v.co.x *= w; v.co.y *= d
            v.co.z = 0.38 * xx ** 4 + 0.32 * (1 - abs(yy)) + 0.12 * abs(xx) ** 2
        r = from_bm("g_roof", bm, roofm, smooth=True, loc=(cx, 0, z))
        s = r.modifiers.new("sol", "SOLIDIFY")
        s.thickness = 0.1
        r.parent = root
        box("g_ridge", (w * 0.8, 0.14, 0.14), (cx, 0, z + 0.38), goldm, bevel=0.03).parent = root
    box("g_mid", (2.9, 0.3, 0.6), (0, 0, 4.75), red).parent = root
    return root


def red_lantern(loc, hang=0.5, ph=0.0, light=0):
    root = empty("rl", loc)
    cyl("rl_str", 0.006, hang, (0, 0, -hang / 2), mat("black"), segs=6).parent = root
    body = sphere("rl_body", 0.2, (0, 0, -hang - 0.17), M("rl", (0.9, 0.05, 0.03), emit=(1.0, 0.12, 0.04), es=1.3),
                  scale=(1, 1, 0.85))
    body.parent = root
    for z in (-hang - 0.01, -hang - 0.34):
        cyl("rl_cap", 0.09, 0.04, (0, 0, z), mat("gold"), segs=16).parent = root
    cyl("rl_tas", 0.02, 0.25, (0, 0, -hang - 0.48), mat("gold"), segs=8, r2=0.035).parent = root
    drive(root, "rotation_euler", 0, f"0.07*sin(frame/13+{ph:.2f})")
    drive(root, "rotation_euler", 1, f"0.05*sin(frame/17+{ph * 2:.2f})")
    if light:
        li = bpy.data.lights.new("rlL", "POINT")
        li.energy = light
        li.color = (1.0, 0.35, 0.15)
        li.shadow_soft_size = 0.2
        lo = link(bpy.data.objects.new("rlL", li))
        lo.location = (0, -0.35, -hang - 0.17)
        lo.parent = root
    return root


def blossom_tree(loc, seed=1, s=1.0):
    rnd = random.Random(seed)
    root = empty("tree", loc)
    tr = cyl("tr_trunk", 0.16 * s, 2.4 * s, (0, 0, 1.2 * s), mat("wood"), segs=10, r2=0.08 * s)
    tr.rotation_euler = (0.08, 0.1, 0)
    tr.parent = root
    for i in range(11):
        a = rnd.uniform(0, 6.28)
        r = rnd.uniform(0, 1.2) * s
        c = sphere("tr_c", rnd.uniform(0.55, 0.9) * s, (math.cos(a) * r, math.sin(a) * r, (2.5 + rnd.uniform(0, 1.0)) * s),
                   mat("blossom"), scale=(1, 1, 0.75))
        displace(c, 0.25 * s, 0.3)
        c.parent = root
    return root
