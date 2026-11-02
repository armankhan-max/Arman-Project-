"""Procedural Blender kit for photoreal-ish documentary B-roll plates (Cycles, CPU).

Everything is built from code: buildings with real window geometry, streets, cars, buses, trees,
terrain, rubble piles, collapsed floors, dust / smoke / fire volumes, liquefaction silt, people
silhouettes. Plates are rendered as stills and animated later (Ken Burns, parallax, particles).
"""
import math
import random

import bpy  # noqa: I001  (bpy must be imported before bmesh)
import bmesh
from mathutils import Euler, Vector

R = random.Random(1)
_MAT = {}
_MESH = {}


# ------------------------------------------------------------------ scene
def reset(seed=1):
    global R
    R = random.Random(seed)
    _MAT.clear()
    _MESH.clear()
    FONTS.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 64
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.05
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 4
    sc.cycles.volume_bounces = 1
    sc.cycles.transparent_max_bounces = 6
    sc.cycles.volume_step_rate = 8.0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.resolution_x = 2112
    sc.render.resolution_y = 1188
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 93
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
        sc.view_settings.exposure = -1.1
    except Exception:
        pass
    sc.render.threads_mode = "AUTO"
    return sc


def render(path, samples=None, res=None):
    sc = bpy.context.scene
    if samples:
        sc.cycles.samples = samples
    if res:
        sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def camera(loc, look, lens=35, dof=None, fstop=4.0, shift=(0, 0)):
    cam = bpy.data.cameras.new("cam")
    cam.lens = lens
    cam.clip_end = 20000
    cam.shift_x, cam.shift_y = shift
    ob = bpy.data.objects.new("cam", cam)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector(look) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if dof:
        cam.dof.use_dof = True
        cam.dof.focus_distance = dof if dof > 0 else d.length
        cam.dof.aperture_fstop = fstop
    bpy.context.scene.camera = ob
    return ob


def sky(elev=35, rot=120, strength=0.35, haze=1.0, sun=4.0, sun_color=(1, 0.95, 0.88), air=1.0, ozone=1.0, sun_angle=0.6):
    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    st = nt.nodes.new("ShaderNodeTexSky")
    for t in ("NISHITA", "MULTIPLE_SCATTERING", "SINGLE_SCATTERING"):
        try:
            st.sky_type = t
            break
        except Exception:
            continue
    try:
        st.sun_disc = False
    except Exception:
        pass
    st.sun_elevation = math.radians(elev)
    st.sun_rotation = math.radians(rot)
    for k, v in (("air_density", air), ("aerosol_density", haze), ("dust_density", haze), ("ozone_density", ozone)):
        if hasattr(st, k):
            setattr(st, k, v)
    bg.inputs["Strength"].default_value = strength
    nt.links.new(st.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])
    if sun > 0:
        L = bpy.data.lights.new("sun", "SUN")
        L.energy = sun
        L.color = sun_color
        L.angle = math.radians(sun_angle)
        ob = bpy.data.objects.new("sun", L)
        bpy.context.scene.collection.objects.link(ob)
        # Nishita: rotation measured from +Y? align lamp to the sky sun direction
        e, r = math.radians(elev), math.radians(rot)
        dvec = Vector((math.sin(r) * math.cos(e), -math.cos(r) * math.cos(e), math.sin(e)))
        ob.rotation_euler = (-dvec).to_track_quat("-Z", "Y").to_euler()
    return w


def flat_world(color=(0.02, 0.03, 0.05), strength=1.0):
    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength
    return w


def light_point(loc, energy=500, color=(1, 0.8, 0.55), radius=0.15, kind="POINT"):
    L = bpy.data.lights.new("l", kind)
    L.energy = energy
    L.color = color
    if kind in ("POINT", "SPOT"):
        L.shadow_soft_size = radius
    ob = bpy.data.objects.new("l", L)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    return ob


def light_area(loc, look, energy=1000, size=4, color=(1, 1, 1)):
    L = bpy.data.lights.new("a", "AREA")
    L.energy = energy
    L.size = size
    L.color = color
    ob = bpy.data.objects.new("a", L)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


def spot(loc, look, energy=2000, angle=40, color=(1, 1, 1), blend=0.3, radius=0.2):
    L = bpy.data.lights.new("s", "SPOT")
    L.energy = energy
    L.spot_size = math.radians(angle)
    L.spot_blend = blend
    L.color = color
    L.shadow_soft_size = radius
    ob = bpy.data.objects.new("s", L)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


# ------------------------------------------------------------------ materials
def _nodes(m):
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(p.outputs[0], out.inputs[0])
    return nt, p, out


def _set(p, name, v):
    if name in p.inputs:
        p.inputs[name].default_value = v


def mat(name, color, rough=0.7, metal=0.0, var=0.25, scale=3.0, bump=0.15, bump_scale=40.0, spec=0.5,
        emit=None, emit_str=0.0, alpha=1.0, coat=0.0, transmission=0.0, ior=1.45, grime=0.0, coords="World"):
    key = (name, tuple(color), rough, metal, var, scale, bump, emit, emit_str, grime)
    if key in _MAT:
        return _MAT[key]
    m = bpy.data.materials.new(name)
    nt, p, out = _nodes(m)
    L = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    if coords == "World":
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        co = geo.outputs["Position"]
        scale, bump_scale, gscale = scale * 0.15, bump_scale * 0.25, 0.18
    else:
        co = tc.outputs[coords]
        gscale = 1.2
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = scale
    n1.inputs["Detail"].default_value = 8
    L(co, n1.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    c = color
    ramp.color_ramp.elements[0].color = (c[0] * (1 - var), c[1] * (1 - var), c[2] * (1 - var), 1)
    ramp.color_ramp.elements[1].color = (min(1, c[0] * (1 + var)), min(1, c[1] * (1 + var)), min(1, c[2] * (1 + var)), 1)
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[1].position = 0.7
    L(n1.outputs["Fac"], ramp.inputs[0])
    col = ramp.outputs[0]
    if grime > 0:
        n3 = nt.nodes.new("ShaderNodeTexNoise")
        n3.inputs["Scale"].default_value = gscale
        n3.inputs["Detail"].default_value = 4
        L(co, n3.inputs["Vector"])
        gr = nt.nodes.new("ShaderNodeValToRGB")
        gr.color_ramp.elements[0].position = 0.45
        gr.color_ramp.elements[1].position = 0.75
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        L(n3.outputs["Fac"], gr.inputs[0])
        mix.inputs["Factor"].default_value = grime
        L(col, mix.inputs[6])
        gm = nt.nodes.new("ShaderNodeMix")
        gm.data_type = "RGBA"
        gm.inputs[6].default_value = (0.25, 0.22, 0.2, 1)
        gm.inputs[7].default_value = (1, 1, 1, 1)
        L(gr.outputs[0], gm.inputs["Factor"])
        L(gm.outputs[2], mix.inputs[7])
        col = mix.outputs[2]
    L(col, p.inputs["Base Color"])
    _set(p, "Roughness", rough)
    _set(p, "Metallic", metal)
    _set(p, "Specular IOR Level", spec)
    _set(p, "Coat Weight", coat)
    _set(p, "Transmission Weight", transmission)
    _set(p, "IOR", ior)
    if alpha < 1:
        _set(p, "Alpha", alpha)
    if emit is not None:
        _set(p, "Emission Color", (*emit, 1))
        _set(p, "Emission Strength", emit_str)
    if bump > 0:
        n2 = nt.nodes.new("ShaderNodeTexNoise")
        n2.inputs["Scale"].default_value = bump_scale
        n2.inputs["Detail"].default_value = 10
        L(co, n2.inputs["Vector"])
        b = nt.nodes.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = bump
        L(n2.outputs["Fac"], b.inputs["Height"])
        L(b.outputs[0], p.inputs["Normal"])
    _MAT[key] = m
    return m


def mat_brick(name="brick", c1=(0.33, 0.12, 0.07), c2=(0.42, 0.18, 0.1), mortar=(0.55, 0.52, 0.47), scale=6.0, grime=0.5):
    key = ("brick", name, c1, c2)
    if key in _MAT:
        return _MAT[key]
    m = bpy.data.materials.new(name)
    nt, p, out = _nodes(m)
    L = nt.links.new
    tc = nt.nodes.new("ShaderNodeNewGeometry")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1, 1, 1)
    L(tc.outputs["Position"], mp.inputs[0])
    # project: use x+y for horizontal so walls on both axes get bricks
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(mp.outputs[0], sep.inputs[0])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    L(sep.outputs[0], add.inputs[0])
    L(sep.outputs[1], add.inputs[1])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    L(add.outputs[0], comb.inputs[0])
    L(sep.outputs[2], comb.inputs[1])
    bt = nt.nodes.new("ShaderNodeTexBrick")
    bt.inputs["Scale"].default_value = 1.0
    bt.inputs["Color1"].default_value = (*c1, 1)
    bt.inputs["Color2"].default_value = (*c2, 1)
    bt.inputs["Mortar"].default_value = (*mortar, 1)
    bt.inputs["Mortar Size"].default_value = 0.008
    bt.inputs["Brick Width"].default_value = 0.23
    bt.inputs["Row Height"].default_value = 0.077
    L(comb.outputs[0], bt.inputs["Vector"])
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 0.25
    n.inputs["Detail"].default_value = 5
    L(tc.outputs["Position"], n.inputs["Vector"])
    gr = nt.nodes.new("ShaderNodeValToRGB")
    gr.color_ramp.elements[0].position = 0.4
    gr.color_ramp.elements[0].color = (1 - grime, 1 - grime, 1 - grime * 0.95, 1)
    gr.color_ramp.elements[1].position = 0.7
    L(n.outputs["Fac"], gr.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    L(bt.outputs["Color"], mix.inputs[6])
    L(gr.outputs[0], mix.inputs[7])
    L(mix.outputs[2], p.inputs["Base Color"])
    _set(p, "Roughness", 0.88)
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = 0.35
    b.invert = True
    L(bt.outputs["Fac"], b.inputs["Height"])
    L(b.outputs[0], p.inputs["Normal"])
    _MAT[key] = m
    return m


def mat_glass(dark=0.02, rough=0.04, tint=(0.6, 0.7, 0.75), lit=0.0, lit_col=(1.0, 0.75, 0.45)):
    key = ("glass", dark, rough, tint, lit)
    if key in _MAT:
        return _MAT[key]
    m = bpy.data.materials.new("glass")
    nt, p, out = _nodes(m)
    _set(p, "Base Color", (dark, dark * 1.1, dark * 1.2, 1))
    _set(p, "Roughness", rough)
    _set(p, "Metallic", 0.0)
    _set(p, "Specular IOR Level", 1.0)
    _set(p, "IOR", 1.52)
    _set(p, "Coat Weight", 1.0)
    _set(p, "Coat Roughness", 0.02)
    _set(p, "Coat Tint", (*tint, 1))
    if lit > 0:
        _set(p, "Emission Color", (*lit_col, 1))
        _set(p, "Emission Strength", lit)
    _MAT[key] = m
    return m


def mat_volume(density=0.05, color=(0.6, 0.55, 0.5), noise_scale=0.6, aniso=0.3, contrast=1.0, emit=0.0, falloff_z=None,
               blackbody=None, absorb=(0.4, 0.4, 0.4)):
    m = bpy.data.materials.new("vol")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    L = nt.links.new
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = (*color, 1)
    pv.inputs["Anisotropy"].default_value = aniso
    pv.inputs["Absorption Color"].default_value = (*absorb, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = noise_scale
    n.inputs["Detail"].default_value = 6
    n.inputs["Roughness"].default_value = 0.6
    L(tc.outputs["Object"], n.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeMapRange")
    cr.inputs["From Min"].default_value = 0.5 - 0.25 / contrast
    cr.inputs["From Max"].default_value = 0.5 + 0.25 / contrast
    cr.inputs["To Min"].default_value = 0.0
    cr.inputs["To Max"].default_value = density
    L(n.outputs["Fac"], cr.inputs["Value"])
    dens = cr.outputs["Result"]
    if falloff_z is not None:
        # density fades with generated z (0 bottom -> 1 top)
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        L(tc.outputs["Generated"], sep.inputs[0])
        fr = nt.nodes.new("ShaderNodeMapRange")
        fr.inputs["From Min"].default_value = 0.0
        fr.inputs["From Max"].default_value = falloff_z
        fr.inputs["To Min"].default_value = 1.0
        fr.inputs["To Max"].default_value = 0.0
        L(sep.outputs[2], fr.inputs["Value"])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        L(dens, mul.inputs[0])
        L(fr.outputs["Result"], mul.inputs[1])
        dens = mul.outputs[0]
    L(dens, pv.inputs["Density"])
    if blackbody:
        pv.inputs["Blackbody Intensity"].default_value = blackbody
        pv.inputs["Temperature"].default_value = 1400
    if emit > 0:
        pv.inputs["Emission Strength"].default_value = emit
        pv.inputs["Emission Color"].default_value = (1.0, 0.45, 0.12, 1)
    L(pv.outputs[0], out.inputs["Volume"])
    return m


def mat_fire(strength=30):
    m = bpy.data.materials.new("fire")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    L = nt.links.new
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 2.5
    n.inputs["Detail"].default_value = 8
    L(tc.outputs["Object"], n.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(tc.outputs["Generated"], sep.inputs[0])
    sub = nt.nodes.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    L(n.outputs["Fac"], sub.inputs[0])
    L(sep.outputs[2], sub.inputs[1])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 0.35
    L(sub.outputs[0], mr.inputs["Value"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].color = (0, 0, 0, 1)
    e[1].color = (1, 0.85, 0.5, 1)
    e.new(0.4).color = (1, 0.25, 0.03, 1)
    L(mr.outputs["Result"], ramp.inputs[0])
    L(ramp.outputs[0], em.inputs["Color"])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = strength
    L(mr.outputs["Result"], mul.inputs[0])
    L(mul.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    L(mr.outputs["Result"], mix.inputs[0])
    L(tr.outputs[0], mix.inputs[1])
    L(em.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs[0])
    return m


# ------------------------------------------------------------------ geometry helpers
def link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _box_mesh(key, bevel=0.0):
    if key in _MESH:
        return _MESH[key]
    me = bpy.data.meshes.new(key)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:] + bm.verts[:], offset=bevel, segments=2, affect="EDGES")
    bm.to_mesh(me)
    bm.free()
    for f in me.polygons:
        f.use_smooth = bevel > 0
    _MESH[key] = me
    return me


def box(loc, size, material, rot=(0, 0, 0), bevel=0.0, name="box"):
    """Axis box centered at loc with full dimensions size. Bevel is in object units of the unit cube."""
    me = _box_mesh(f"cube_b{bevel:.3f}", bevel)
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.scale = size
    ob.rotation_euler = rot
    if material is not None:
        ob.data = me
        ob.active_material = material  # object-linked slot below
        if not me.materials:
            me.materials.append(material)
        ob.material_slots[0].link = "OBJECT"
        ob.material_slots[0].material = material
    return link(ob)


def mesh_from(name, verts, faces, material=None, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    if material:
        me.materials.append(material)
    return link(ob)


def cylinder(loc, r, h, material, rot=(0, 0, 0), verts=16, name="cyl"):
    key = f"cyl{verts}"
    if key not in _MESH:
        me = bpy.data.meshes.new(key)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=1, radius2=1, depth=1)
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = len(p.vertices) == 4
        _MESH[key] = me
    ob = bpy.data.objects.new(name, _MESH[key])
    ob.location = loc
    ob.scale = (r, r, h)
    ob.rotation_euler = rot
    _objmat(ob, material)
    return link(ob)


def sphere(loc, r, material, subdiv=3, name="sph", scale=None):
    key = f"ico{subdiv}"
    if key not in _MESH:
        me = bpy.data.meshes.new(key)
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1)
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        _MESH[key] = me
    ob = bpy.data.objects.new(name, _MESH[key])
    ob.location = loc
    ob.scale = scale or (r, r, r)
    _objmat(ob, material)
    return link(ob)


def _objmat(ob, material):
    if material is None:
        return
    if not ob.data.materials:
        ob.data.materials.append(material)
    ob.material_slots[0].link = "OBJECT"
    ob.material_slots[0].material = material


def rock_mesh(seed, sub=2, jag=0.35):
    key = f"rock{seed}_{sub}_{jag}"
    if key in _MESH:
        return _MESH[key]
    rr = random.Random(seed)
    me = bpy.data.meshes.new(key)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1)
    # random planar cuts -> chunky fractured look
    for _ in range(6):
        n = Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(-1, 1))).normalized()
        d = rr.uniform(0.35, 0.8)
        for v in bm.verts:
            k = v.co.dot(n)
            if k > d:
                v.co -= n * (k - d)
    for v in bm.verts:
        v.co *= 1 + rr.uniform(-jag, jag) * 0.3
    bm.to_mesh(me)
    bm.free()
    _MESH[key] = me
    return me


def rock(loc, size, material, seed=None, rot=None):
    me = rock_mesh(seed if seed is not None else R.randrange(12))
    ob = bpy.data.objects.new("rock", me)
    ob.location = loc
    ob.scale = size if isinstance(size, (tuple, list)) else (size, size * R.uniform(0.6, 1), size * R.uniform(0.5, 0.9))
    ob.rotation_euler = rot or (R.uniform(0, 6.3), R.uniform(0, 6.3), R.uniform(0, 6.3))
    _objmat(ob, material)
    return link(ob)


def grid_terrain(name, size_x, size_y, nx, ny, height_fn, material, origin=(0, 0, 0)):
    verts, faces = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = -size_x / 2 + size_x * i / nx
            y = -size_y / 2 + size_y * j / ny
            verts.append((x + origin[0], y + origin[1], height_fn(x + origin[0], y + origin[1]) + origin[2]))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    return mesh_from(name, verts, faces, material, smooth=True)


def noise2(x, y, seed=0, octaves=4, base=0.01):
    """cheap value-noise fbm (pure python, used for terrain heights)"""
    tot, amp, f = 0.0, 1.0, base
    for o in range(octaves):
        tot += amp * _vnoise(x * f, y * f, seed + o * 17)
        amp *= 0.5
        f *= 2.03
    return tot


def _h(i, j, s):
    n = (i * 374761393 + j * 668265263 + s * 2147483647) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0 * 2 - 1


def _vnoise(x, y, s):
    i, j = math.floor(x), math.floor(y)
    fx, fy = x - i, y - j
    ux, uy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = _h(i, j, s), _h(i + 1, j, s), _h(i, j + 1, s), _h(i + 1, j + 1, s)
    return a + (b - a) * ux + (c - a) * uy + (a - b - c + d) * ux * uy


def volume_box(loc, size, material, name="vol"):
    ob = box(loc, size, None, name=name)
    ob.data = _box_mesh("volcube").copy() if "volcube" in _MESH else _box_mesh("volcube")
    ob.data.materials.clear()
    ob.data.materials.append(material)
    ob.visible_shadow = True
    return ob


# ------------------------------------------------------------------ palettes
def M():
    """Common material set."""
    return dict(
        asphalt=mat("asphalt", (0.07, 0.07, 0.075), rough=0.85, var=0.3, scale=8, bump=0.25, bump_scale=120, grime=0.3),
        asphalt_wet=mat("asphaltwet", (0.04, 0.04, 0.045), rough=0.25, var=0.3, scale=8, bump=0.1, bump_scale=120),
        concrete=mat("concrete", (0.5, 0.49, 0.46), rough=0.85, var=0.18, scale=2, bump=0.12, grime=0.45),
        concrete_dark=mat("concrete_d", (0.32, 0.31, 0.3), rough=0.9, var=0.2, scale=2, bump=0.15, grime=0.5),
        curb=mat("curb", (0.55, 0.54, 0.5), rough=0.8, var=0.15, scale=3, bump=0.1),
        footpath=mat("footpath", (0.38, 0.37, 0.35), rough=0.85, var=0.2, scale=4, bump=0.15, bump_scale=60, grime=0.3),
        stone=mat("stone", (0.48, 0.46, 0.41), rough=0.85, var=0.25, scale=1.5, bump=0.3, bump_scale=18, grime=0.55),
        stone_dark=mat("stone_d", (0.3, 0.29, 0.27), rough=0.9, var=0.25, scale=1.5, bump=0.3, bump_scale=18, grime=0.55),
        plaster_cream=mat("pl_cream", (0.72, 0.66, 0.53), rough=0.8, var=0.12, grime=0.45),
        plaster_white=mat("pl_white", (0.78, 0.77, 0.73), rough=0.8, var=0.1, grime=0.4),
        plaster_blue=mat("pl_blue", (0.35, 0.45, 0.5), rough=0.8, var=0.1, grime=0.4),
        plaster_green=mat("pl_green", (0.3, 0.4, 0.32), rough=0.8, var=0.1, grime=0.4),
        plaster_red=mat("pl_red", (0.5, 0.2, 0.15), rough=0.8, var=0.1, grime=0.4),
        trim=mat("trim", (0.85, 0.84, 0.8), rough=0.6, var=0.05, bump=0.02),
        metal=mat("metal", (0.55, 0.56, 0.58), rough=0.35, metal=1.0, var=0.1, bump=0.02),
        metal_dark=mat("metal_d", (0.12, 0.12, 0.13), rough=0.4, metal=0.8, var=0.1, bump=0.02),
        rust=mat("rust", (0.3, 0.13, 0.06), rough=0.8, metal=0.4, var=0.4, bump=0.2),
        roof_iron=mat("roof_iron", (0.25, 0.27, 0.28), rough=0.45, metal=0.7, var=0.2, bump=0.05),
        roof_red=mat("roof_red", (0.35, 0.1, 0.07), rough=0.55, metal=0.4, var=0.2, bump=0.05),
        roof_tile=mat("roof_tile", (0.28, 0.12, 0.08), rough=0.7, var=0.25, bump=0.2),
        wood=mat("wood", (0.35, 0.22, 0.13), rough=0.7, var=0.3, scale=6, bump=0.1),
        weatherboard_white=mat("wb_white", (0.8, 0.79, 0.74), rough=0.65, var=0.08, grime=0.35),
        weatherboard_yellow=mat("wb_yel", (0.75, 0.66, 0.42), rough=0.65, var=0.08, grime=0.35),
        weatherboard_blue=mat("wb_blue", (0.42, 0.52, 0.6), rough=0.65, var=0.08, grime=0.35),
        weatherboard_green=mat("wb_grn", (0.45, 0.55, 0.45), rough=0.65, var=0.08, grime=0.35),
        grass=mat("grass", (0.13, 0.2, 0.06), rough=0.9, var=0.45, scale=0.8, bump=0.4, bump_scale=200),
        grass_dry=mat("grass_dry", (0.3, 0.28, 0.13), rough=0.95, var=0.4, scale=0.6, bump=0.4, bump_scale=200),
        dirt=mat("dirt", (0.22, 0.17, 0.12), rough=0.95, var=0.35, scale=2, bump=0.4, bump_scale=30),
        silt=mat("silt", (0.32, 0.31, 0.29), rough=0.6, var=0.2, scale=1.5, bump=0.25, bump_scale=15),
        silt_wet=mat("silt_wet", (0.17, 0.17, 0.165), rough=0.12, var=0.18, scale=1.2, bump=0.08, bump_scale=8, coat=0.6),
        water=mat("water", (0.03, 0.04, 0.045), rough=0.04, var=0.1, bump=0.04, bump_scale=3, coat=1.0),
        rubble=mat("rubble", (0.45, 0.43, 0.4), rough=0.9, var=0.3, scale=3, bump=0.4, bump_scale=25, grime=0.5),
        rubble_dust=mat("rubble_dust", (0.6, 0.58, 0.54), rough=0.95, var=0.2, scale=3, bump=0.4, bump_scale=25, grime=0.3),
        leaves=mat("leaves", (0.07, 0.13, 0.04), rough=0.8, var=0.5, scale=4, bump=0.6, bump_scale=60),
        bark=mat("bark", (0.12, 0.09, 0.07), rough=0.95, var=0.3, bump=0.5, bump_scale=30),
        tyre=mat("tyre", (0.02, 0.02, 0.02), rough=0.7, var=0.05, bump=0.05),
        brick=mat_brick(),
        brick_light=mat_brick("brick_l", (0.45, 0.25, 0.15), (0.52, 0.32, 0.2)),
        glass=mat_glass(),
        rock=mat("rock", (0.28, 0.25, 0.22), rough=0.9, var=0.35, scale=1, bump=0.6, bump_scale=8, grime=0.4),
        hivis=mat("hivis", (0.9, 0.55, 0.02), rough=0.6, var=0.05, bump=0.05),
        hivis_y=mat("hivis_y", (0.75, 0.85, 0.05), rough=0.6, var=0.05, bump=0.05),
        cloth_dark=mat("cloth_d", (0.04, 0.045, 0.06), rough=0.9, var=0.2, bump=0.1),
        cloth_blue=mat("cloth_b", (0.08, 0.12, 0.2), rough=0.9, var=0.2, bump=0.1),
        skin=mat("skin", (0.55, 0.38, 0.28), rough=0.6, var=0.05, bump=0.02),
        helmet=mat("helmet", (0.8, 0.78, 0.7), rough=0.35, var=0.05, bump=0.01),
        cardboard=mat("cardboard", (0.55, 0.42, 0.27), rough=0.85, var=0.15, scale=4, bump=0.1, bump_scale=200),
    )


# ------------------------------------------------------------------ architecture
def window_unit(w, h, frame_mat, glass_mat, depth=0.25, frame=0.08, mullion=True, sill_mat=None):
    """Return list of (local offset, size, material) boxes making one window, origin at center of the opening face."""
    parts = []
    rev = _reveal_mat()
    parts.append(((0, -0.012, 0), (w + 0.16, 0.03, h + 0.16), rev))  # dark reveal ring
    parts.append(((0, -0.03, 0), (w - 0.04, 0.02, h - 0.04), glass_mat))
    parts.append(((0, -0.07, h / 2 - frame / 2), (w, 0.1, frame), frame_mat))
    parts.append(((0, -0.07, -h / 2 + frame / 2), (w, 0.1, frame), frame_mat))
    parts.append(((-w / 2 + frame / 2, -0.07, 0), (frame, 0.1, h), frame_mat))
    parts.append(((w / 2 - frame / 2, -0.07, 0), (frame, 0.1, h), frame_mat))
    if mullion:
        parts.append(((0, -0.06, 0), (frame * 0.6, 0.07, h), frame_mat))
        parts.append(((0, -0.06, h * 0.18), (w, 0.07, frame * 0.6), frame_mat))
    if sill_mat:
        parts.append(((0, -0.14, -h / 2 - 0.05), (w + 0.25, 0.28, 0.1), sill_mat))
        parts.append(((0, -0.1, h / 2 + 0.12), (w + 0.35, 0.2, 0.22), sill_mat))  # hood
    return parts


def _reveal_mat():
    return mat("reveal", (0.03, 0.028, 0.025), rough=0.9, var=0.1, bump=0.05)


def facade_box(x0, y0, w, d, h, wall, floors, win_w=1.2, win_h=1.6, bay=3.0, frame=None, glass=None, sill=None,
               parapet=0.0, cornice=None, shop=False, shop_glass=None, awning=None, sides=("front",), rot=0.0,
               ground_h=None, lit_frac=0.0, lit_glass=None):
    """Building with true recessed windows on the given sides. (x0,y0) = front-left corner, front faces -Y."""
    frame = frame or wall
    glass = glass or mat_glass()
    objs = []
    fh = h / floors
    ground_h = ground_h or fh
    objs.append(box((x0 + w / 2, y0 + d / 2, h / 2), (w, d, h), wall, name="bld"))
    if parapet > 0:
        objs.append(box((x0 + w / 2, y0 + 0.15, h + parapet / 2), (w, 0.3, parapet), wall))
    if cornice:
        objs.append(box((x0 + w / 2, y0 - 0.12, h - 0.25), (w + 0.3, 0.45, 0.35), cornice))
        objs.append(box((x0 + w / 2, y0 - 0.08, ground_h + 0.15), (w + 0.1, 0.3, 0.25), cornice))
    nb = max(1, int(w / bay))
    bw = w / nb
    for side in sides:
        for f in range(floors):
            zc = ground_h + (f - 1) * fh + fh * 0.55 if f > 0 else ground_h * 0.5
            for b in range(nb):
                xc = x0 + bw * (b + 0.5)
                if f == 0 and shop:
                    sg = shop_glass or glass
                    objs.append(box((xc, y0 + 0.12, ground_h * 0.48), (bw * 0.86, 0.06, ground_h * 0.72), sg))
                    objs.append(box((xc, y0 - 0.02, ground_h * 0.86), (bw * 0.9, 0.12, 0.12), frame))
                    objs.append(box((xc, y0 - 0.02, 0.1), (bw * 0.9, 0.12, 0.2), frame))
                    continue
                if f == 0:
                    continue
                g = lit_glass if (lit_glass is not None and R.random() < lit_frac) else glass
                for (o, s, m) in window_unit(win_w, win_h, frame, g, sill_mat=sill):
                    objs.append(box((xc + o[0], y0 + o[1] - 0.001, zc + o[2]), s, m))
        if awning and R.random() < 0.6:
            objs.append(box((x0 + w / 2, y0 - 1.5, ground_h - 0.4), (w, 3.0, 0.1), awning))
            objs.append(box((x0 + w / 2, y0 - 3.0, ground_h - 0.55), (w, 0.06, 0.35), awning))
            for px in (x0 + 0.3, x0 + w - 0.3):
                objs.append(box((px, y0 - 2.95, (ground_h - 0.4) / 2), (0.1, 0.1, ground_h - 0.4), awning))
    if rot:
        for o in objs:
            o.rotation_euler.z += rot
    return objs


def heritage_building(x0, y0, w, h, floors, wall=None, d=14, trim=None, shop=True, mats=None, **kw):
    mats = mats or M()
    wall = wall or mats["brick"]
    trim = trim or mats["trim"]
    return facade_box(x0, y0, w, d, h, wall, floors, win_w=1.1, win_h=2.0, bay=3.2, frame=trim, glass=mats["glass"],
                      sill=trim, parapet=1.2, cornice=trim, shop=shop, awning=kw.pop("awning", mats["metal_dark"]), **kw)


def office_building(x0, y0, w, d, floors, fh=3.4, mats=None, band=None, glass=None, rot=0.0, lit_frac=0.0):
    """Modern concrete frame office: horizontal spandrel bands + ribbon glazing (CTV/PGC style)."""
    mats = mats or M()
    band = band or mats["concrete"]
    glass = glass or mats["glass"]
    objs = []
    h = floors * fh
    objs.append(box((x0 + w / 2, y0 + d / 2 + 0.6, h / 2), (w - 1.2, d - 1.2, h), mats["concrete_dark"]))
    for f in range(floors + 1):
        z = f * fh
        objs.append(box((x0 + w / 2, y0 + d / 2, z + 0.45), (w, d, 0.9), band))
        if f < floors:
            objs.append(box((x0 + w / 2, y0 + 0.65, z + 0.9 + (fh - 0.9) / 2), (w - 0.4, 0.05, fh - 0.9), glass))
            objs.append(box((x0 + 0.65, y0 + d / 2, z + 0.9 + (fh - 0.9) / 2), (0.05, d - 0.4, fh - 0.9), glass))
            objs.append(box((x0 + w - 0.65, y0 + d / 2, z + 0.9 + (fh - 0.9) / 2), (0.05, d - 0.4, fh - 0.9), glass))
            # mullions
            n = int(w / 1.6)
            for i in range(n + 1):
                objs.append(box((x0 + 0.3 + (w - 0.6) * i / n, y0 + 0.6, z + 0.9 + (fh - 0.9) / 2), (0.08, 0.12, fh - 0.9), mats["metal_dark"]))
    # columns
    for i in range(5):
        objs.append(box((x0 + 0.3 + (w - 0.6) * i / 4, y0 + 0.4, h / 2), (0.6, 0.6, h), band))
    if rot:
        for o in objs:
            o.rotation_euler.z += rot
    return objs


def house(x, y, w=9, d=11, h=3.0, wall=None, roof=None, rot=0.0, tilt=(0, 0), sink=0.0, mats=None, chimney=True):
    """Single-storey NZ weatherboard bungalow with gabled roof. Returns objects (parented to an empty)."""
    mats = mats or M()
    wall = wall or mats["weatherboard_white"]
    roof = roof or mats["roof_iron"]
    root = bpy.data.objects.new("house", None)
    link(root)
    objs = [box((0, 0, h / 2 + 0.4), (w, d, h), wall), box((0, 0, 0.2), (w + 0.1, d + 0.1, 0.5), mats["concrete"])]
    # gable roof
    rh = w * 0.32
    v = [(-w / 2 - 0.5, -d / 2 - 0.5, h + 0.4), (w / 2 + 0.5, -d / 2 - 0.5, h + 0.4), (0, -d / 2 - 0.5, h + 0.4 + rh),
         (-w / 2 - 0.5, d / 2 + 0.5, h + 0.4), (w / 2 + 0.5, d / 2 + 0.5, h + 0.4), (0, d / 2 + 0.5, h + 0.4 + rh)]
    objs.append(mesh_from("roof", v, [(0, 2, 5, 3), (2, 1, 4, 5)], roof))
    sol = objs[-1].modifiers.new("s", "SOLIDIFY")
    sol.thickness = 0.12
    gv = [(-w / 2, -d / 2 - 0.01, h + 0.4), (w / 2, -d / 2 - 0.01, h + 0.4), (0, -d / 2 - 0.01, h + 0.4 + rh - 0.2)]
    objs.append(mesh_from("gable", gv, [(0, 1, 2)], wall))
    gv2 = [(x_, d / 2 + 0.01, z_) for (x_, _, z_) in gv]
    objs.append(mesh_from("gable2", gv2, [(0, 2, 1)], wall))
    for wx in (-w / 4, w / 4):
        for (o, s, m) in window_unit(1.6, 1.3, mats["trim"], mats["glass"], sill_mat=mats["trim"]):
            objs.append(box((wx + o[0], -d / 2 + o[1] - 0.12, 2.0 + o[2]), s, m))
    objs.append(box((0, -d / 2 - 0.05, 1.45), (0.95, 0.1, 2.1), mats["wood"]))
    if chimney:
        objs.append(box((w / 4, d / 5, h + rh + 0.2), (0.7, 0.7, 2.2), mats["brick"]))
    for o in objs:
        o.parent = root
    root.location = (x, y, -sink)
    root.rotation_euler = (tilt[0], tilt[1], rot)
    return root


def _extrude_profile(name, prof, width, material, bevel=0.06, sub=True):
    """prof: list of (x,z) in a closed loop (counter-clockwise, side view); extruded along Y by width."""
    n = len(prof)
    v = [(x, -width / 2, z) for x, z in prof] + [(x, width / 2, z) for x, z in prof]
    f = [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    ob = mesh_from(name, v, f, material)
    if bevel:
        b = ob.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = 3
        b.limit_method = "ANGLE"
    if sub:
        ob.modifiers.new("w", "WEIGHTED_NORMAL")
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


CAR_BODY = [(-2.25, 0.32), (2.25, 0.32), (2.3, 0.62), (2.2, 0.82), (1.0, 0.95), (-1.6, 0.98), (-2.2, 0.92), (-2.32, 0.65)]
CAR_CABIN = [(-1.55, 0.95), (0.95, 0.95), (0.25, 1.42), (-1.25, 1.44), (-1.75, 1.0)]


def car(x, y, rot=0.0, color=None, sink=0.0, tilt=(0, 0), mats=None, scale=1.0, dusty=0.0):
    mats = mats or M()
    color = color or R.choice([(0.5, 0.52, 0.55), (0.05, 0.05, 0.06), (0.6, 0.6, 0.62), (0.25, 0.05, 0.05),
                               (0.08, 0.15, 0.3), (0.75, 0.75, 0.74), (0.3, 0.32, 0.3), (0.55, 0.45, 0.3)])
    if dusty:
        color = tuple(c * (1 - dusty) + 0.55 * dusty for c in color)
    paint = mat("paint", color, rough=0.25 + dusty * 0.6, var=0.03 + dusty * 0.2, bump=0.0, coat=1.0 - dusty)
    root = bpy.data.objects.new("car", None)
    link(root)
    objs = [_extrude_profile("body", CAR_BODY, 1.78, paint, 0.08),
            _extrude_profile("cabin", CAR_CABIN, 1.5, mats["glass"], 0.05),
            box((-0.42, 0, 1.445), (1.45, 1.42, 0.05), paint, bevel=0.2)]
    objs[1].location.z = -0.01
    for (dx, dy) in ((1.4, 0.8), (-1.45, 0.8), (1.4, -0.8), (-1.45, -0.8)):
        objs.append(cylinder((dx, dy, 0.33), 0.33, 0.22, mats["tyre"], rot=(math.pi / 2, 0, 0)))
        objs.append(cylinder((dx, dy * 1.07, 0.33), 0.2, 0.02, mats["metal"], rot=(math.pi / 2, 0, 0)))
    hl = mat("hl", (1, 1, 0.95), rough=0.1, bump=0)
    tl = mat("tl", (0.5, 0.02, 0.02), rough=0.2, bump=0)
    for s_ in (1, -1):
        objs.append(box((2.24, s_ * 0.6, 0.68), (0.08, 0.32, 0.1), hl, bevel=0.2))
        objs.append(box((-2.3, s_ * 0.62, 0.78), (0.06, 0.28, 0.1), tl, bevel=0.2))
    objs.append(box((2.3, 0, 0.42), (0.1, 1.7, 0.16), mats["metal_dark"], bevel=0.2))
    objs.append(box((-2.32, 0, 0.42), (0.1, 1.7, 0.16), mats["metal_dark"], bevel=0.2))
    for o in objs:
        o.parent = root
    root.location = (x, y, -sink)
    root.rotation_euler = (tilt[0], tilt[1], rot)
    root.scale = (scale, scale, scale)
    return root


def bus(x, y, rot=0.0, color=(0.75, 0.62, 0.1), mats=None):
    mats = mats or M()
    paint = mat("buspaint", color, rough=0.3, var=0.04, bump=0, coat=0.6)
    root = bpy.data.objects.new("bus", None)
    link(root)
    L, W, H = 11.5, 2.5, 3.0
    objs = [box((0, 0, 0.35 + H / 2), (L, W, H), paint, bevel=0.06),
            box((0, -W / 2 - 0.01, 0.35 + H * 0.68), (L - 1.2, 0.04, H * 0.42), mats["glass"]),
            box((0, W / 2 + 0.01, 0.35 + H * 0.68), (L - 1.2, 0.04, H * 0.42), mats["glass"]),
            box((L / 2 + 0.01, 0, 0.35 + H * 0.6), (0.04, W - 0.3, H * 0.55), mats["glass"])]
    for dx in (L / 2 - 2.2, -L / 2 + 2.6):
        for dy in (W / 2 - 0.15, -W / 2 + 0.15):
            objs.append(cylinder((dx, dy, 0.5), 0.5, 0.3, mats["tyre"], rot=(math.pi / 2, 0, 0)))
    for o in objs:
        o.parent = root
    root.location = (x, y, 0)
    root.rotation_euler = (0, 0, rot)
    return root


def tree(x, y, h=8.0, r=3.0, mats=None, seed=None, leaves=None, bare=False):
    mats = mats or M()
    rr = random.Random(seed if seed is not None else R.random())
    objs = [cylinder((x, y, h * 0.3), 0.18 * h / 8, h * 0.6, mats["bark"])]
    if bare:
        for i in range(7):
            a = rr.uniform(0, 6.28)
            el = rr.uniform(0.5, 1.1)
            L = rr.uniform(1.5, 3.2) * h / 8
            c = cylinder((x + math.cos(a) * L * 0.4, y + math.sin(a) * L * 0.4, h * 0.55 + L * 0.3), 0.06, L,
                         mats["bark"], rot=(math.cos(a) * el, -math.sin(a) * el, 0))
            c.rotation_euler = (Vector((math.cos(a), math.sin(a), 1.2))).to_track_quat("Z", "Y").to_euler()
            objs.append(c)
        return objs
    lm = leaves or mats["leaves"]
    for i in range(rr.randint(10, 14)):
        rx, ry = rr.uniform(-r * 0.6, r * 0.6), rr.uniform(-r * 0.6, r * 0.6)
        rz = h * rr.uniform(0.55, 0.98)
        s = rr.uniform(0.35, 0.55) * r
        ob = sphere((x + rx, y + ry, rz), s, lm, subdiv=3, scale=(s, s * rr.uniform(0.8, 1.1), s * rr.uniform(0.7, 0.9)))
        dm = ob.modifiers.new("d", "DISPLACE")
        tx = bpy.data.textures.new("t", "CLOUDS")
        tx.noise_scale = 0.12
        tx.noise_depth = 4
        dm.texture = tx
        dm.strength = 0.45
        dm.texture_coords = "GLOBAL"
        objs.append(ob)
    return objs


def lamp_post(x, y, h=7.5, arm_dir=1, mats=None, lit=0.0, color=(1, 0.65, 0.3)):
    mats = mats or M()
    objs = [cylinder((x, y, h / 2), 0.08, h, mats["metal_dark"]),
            box((x, y + arm_dir * 0.8, h), (0.1, 1.6, 0.1), mats["metal_dark"]),
            box((x, y + arm_dir * 1.6, h - 0.05), (0.35, 0.6, 0.15), mats["metal_dark"])]
    if lit > 0:
        objs.append(box((x, y + arm_dir * 1.6, h - 0.14), (0.3, 0.5, 0.03), mat("lampglow", color, emit=color, emit_str=lit, bump=0)))
        light_point((x, y + arm_dir * 1.6, h - 0.4), energy=lit * 25, color=color, radius=0.2)
    return objs


def street(length=200, width=12, foot=4.0, mats=None, wet=False, center=(0, 0), along="x", lines=True):
    mats = mats or M()
    cx, cy = center
    o = []
    asp = mats["asphalt_wet"] if wet else mats["asphalt"]
    if along == "x":
        o.append(box((cx, cy, -0.05), (length, width, 0.1), asp))
        for s in (-1, 1):
            o.append(box((cx, cy + s * (width / 2 + foot / 2), 0.08), (length, foot, 0.16), mats["footpath"]))
            o.append(box((cx, cy + s * (width / 2 + 0.1), 0.08), (length, 0.25, 0.17), mats["curb"]))
        if lines:
            paint = mat("roadpaint", (0.75, 0.75, 0.7), rough=0.6, var=0.2, bump=0.05)
            for i in range(int(length / 9)):
                o.append(box((cx - length / 2 + i * 9 + 2, cy, 0.002), (3.0, 0.15, 0.01), paint))
    else:
        o.append(box((cx, cy, -0.05), (width, length, 0.1), asp))
        for s in (-1, 1):
            o.append(box((cx + s * (width / 2 + foot / 2), cy, 0.08), (foot, length, 0.16), mats["footpath"]))
            o.append(box((cx + s * (width / 2 + 0.1), cy, 0.08), (0.25, length, 0.17), mats["curb"]))
        if lines:
            paint = mat("roadpaint", (0.75, 0.75, 0.7), rough=0.6, var=0.2, bump=0.05)
            for i in range(int(length / 9)):
                o.append(box((cx, cy - length / 2 + i * 9 + 2, 0.002), (0.15, 3.0, 0.01), paint))
    return o


def ground(size=4000, material=None, z=-0.11):
    material = material or M()["grass"]
    return box((0, 0, z - 0.05), (size, size, 0.1), material)


def rubble_pile(cx, cy, rx, ry, h, n=300, mats=None, dusty=True, slabs=0, rebar=0, bricks=0, seed=0, brick_mat=None):
    """Mound of rocks/concrete chunks + optional tilted slabs, rebar, loose bricks."""
    mats = mats or M()
    rr = random.Random(seed)
    m1 = mats["rubble_dust"] if dusty else mats["rubble"]
    m2 = mats["concrete"] if dusty else mats["concrete_dark"]
    objs = []
    mound = box((cx, cy, h * 0.25), (rx * 1.6, ry * 1.6, h * 0.5), m1)
    sub = mound.modifiers.new("sub", "SUBSURF")
    sub.levels = 3
    sub.render_levels = 3
    dm = mound.modifiers.new("d", "DISPLACE")
    tx = bpy.data.textures.new("rt", "CLOUDS")
    tx.noise_scale = 0.8
    dm.texture = tx
    dm.strength = 0.8
    objs.append(mound)

    def surf(x, y):
        k = 1 - ((x - cx) / rx) ** 2 - ((y - cy) / ry) ** 2
        return max(0.0, k) ** 0.7 * h

    for i in range(n):
        a = rr.uniform(0, 6.283)
        d = rr.random() ** 0.6
        x, y = cx + math.cos(a) * d * rx, cy + math.sin(a) * d * ry
        s = rr.uniform(0.15, 0.9) * (1.3 - d * 0.6)
        objs.append(rock((x, y, surf(x, y) * rr.uniform(0.6, 1.0)), (s * rr.uniform(0.8, 1.6), s, s * rr.uniform(0.4, 0.8)),
                         rr.choice([m1, m1, m2]), seed=rr.randrange(12)))
    for i in range(slabs):
        a = rr.uniform(0, 6.283)
        d = rr.random() ** 0.8 * 0.8
        x, y = cx + math.cos(a) * d * rx, cy + math.sin(a) * d * ry
        objs.append(box((x, y, surf(x, y) * 0.8 + 0.3), (rr.uniform(3, 7), rr.uniform(2, 4), 0.3), m2,
                        rot=(rr.uniform(-0.6, 0.6), rr.uniform(-0.6, 0.6), rr.uniform(0, 6.3)), bevel=0.02))
    for i in range(rebar):
        a = rr.uniform(0, 6.283)
        d = rr.random() * 0.8
        x, y = cx + math.cos(a) * d * rx, cy + math.sin(a) * d * ry
        objs.append(cylinder((x, y, surf(x, y) + 0.6), 0.025, rr.uniform(1.5, 3.5), mats["rust"], verts=6,
                             rot=(rr.uniform(-0.9, 0.9), rr.uniform(-0.9, 0.9), 0)))
    bm_ = brick_mat or mats["brick_light"]
    for i in range(bricks):
        a = rr.uniform(0, 6.283)
        d = rr.random() ** 0.5 * 1.15
        x, y = cx + math.cos(a) * d * rx, cy + math.sin(a) * d * ry
        objs.append(box((x, y, surf(x, y) + 0.06), (0.23, 0.11, 0.075), bm_,
                        rot=(rr.uniform(-0.5, 0.5), rr.uniform(-0.5, 0.5), rr.uniform(0, 6.3)), bevel=0.05))
    return objs


def person(x, y, rot=0.0, scale=1.0, top=None, legs=None, hivis=False, helmet=False, pose="stand", mats=None):
    """Very simple human figure (reads well small, in haze, or backlit)."""
    mats = mats or M()
    top = top or mats["cloth_dark"]
    legs = legs or mats["cloth_blue"]
    root = bpy.data.objects.new("person", None)
    link(root)
    o = []
    lean = 0.35 if pose == "dig" else 0.0
    o.append(cylinder((0.11, 0, 0.45), 0.075, 0.9, legs))
    o.append(cylinder((-0.11, 0, 0.45), 0.075, 0.9, legs))
    t = box((0, 0 + lean * 0.3, 1.22), (0.42, 0.25, 0.65), mats["hivis"] if hivis else top, bevel=0.3)
    t.rotation_euler = (lean, 0, 0)
    o.append(t)
    o.append(sphere((0, 0.05 + lean * 0.6, 1.68), 0.11, mats["skin"], subdiv=2, scale=(0.1, 0.11, 0.125)))
    if helmet:
        o.append(sphere((0, 0.05 + lean * 0.6, 1.74), 0.13, mats["helmet"], subdiv=2, scale=(0.13, 0.14, 0.09)))
    for s in (-1, 1):
        a = cylinder((s * 0.26, -0.05 if pose == "dig" else 0, 1.2), 0.05, 0.62, top)
        a.rotation_euler = (0.7 if pose == "dig" else 0.05, s * 0.1, 0)
        o.append(a)
    for ob in o:
        ob.parent = root
    root.location = (x, y, 0)
    root.rotation_euler = (0, 0, rot)
    root.scale = (scale, scale, scale)
    return root


def fence(x0, y0, x1, y1, n=None, post_mat=None, wire=True, mats=None, offset_fn=None):
    """Farm fence of posts + wires. offset_fn(t)->lateral shift (for fault-offset fences)."""
    mats = mats or M()
    post_mat = post_mat or mats["wood"]
    L = math.hypot(x1 - x0, y1 - y0)
    n = n or int(L / 3)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    px, py = -uy, ux
    pts = []
    objs = []
    for i in range(n + 1):
        t = i / n
        off = offset_fn(t) if offset_fn else 0
        x, y = x0 + (x1 - x0) * t + px * off, y0 + (y1 - y0) * t + py * off
        pts.append((x, y))
        objs.append(cylinder((x, y, 0.6), 0.06, 1.25, post_mat, verts=8, rot=(R.uniform(-0.04, 0.04), R.uniform(-0.04, 0.04), 0)))
    if wire:
        wm = mat("wire", (0.45, 0.45, 0.45), rough=0.4, metal=1, bump=0)
        for z in (0.45, 0.8, 1.1):
            for i in range(n):
                (ax, ay), (bx, by) = pts[i], pts[i + 1]
                ln = math.hypot(bx - ax, by - ay)
                c = cylinder(((ax + bx) / 2, (ay + by) / 2, z), 0.006, ln, wm, verts=4)
                c.rotation_euler = Vector((bx - ax, by - ay, 0)).to_track_quat("Z", "Y").to_euler()
                objs.append(c)
    return objs


def mountains(dist=4000, width=12000, height=1800, seed=3, snow=True, z0=0.0, y=None, depth=3000):
    """Distant mountain range as a displaced strip (Southern Alps backdrop)."""
    snowm = mat("snow", (0.85, 0.86, 0.9), rough=0.5, var=0.08, scale=0.01, bump=0.2, bump_scale=0.05)
    rockm = mat("mrock", (0.2, 0.2, 0.22), rough=0.9, var=0.3, scale=0.003, bump=0.3, bump_scale=0.02)
    y = y if y is not None else dist

    def hf(x, yy):
        ridge = max(0.0, 1 - abs(yy - y) / (depth / 2))
        n = noise2(x, yy, seed, 6, 0.0012) * 0.6 + 0.6
        return (ridge ** 0.8) * height * max(0.05, n) + z0

    ob = grid_terrain("mtn", width, depth, 300, 60, hf, None, origin=(0, y, 0))
    ob.location.y = 0
    # material: mix snow above altitude
    m = bpy.data.materials.new("mtnmat")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    L = nt.links.new
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ms = nt.nodes.new("ShaderNodeMixShader")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs[0])
    nz = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(geo.outputs["Normal"], nz.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = height * 0.5 + z0
    mr.inputs["From Max"].default_value = height * 0.62 + z0
    L(sep.outputs[2], mr.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    L(mr.outputs["Result"], mul.inputs[0])
    sm = nt.nodes.new("ShaderNodeMapRange")
    sm.inputs["From Min"].default_value = 0.55
    sm.inputs["From Max"].default_value = 0.75
    L(nz.outputs[2], sm.inputs["Value"])
    L(sm.outputs["Result"], mul.inputs[1])
    L(mul.outputs[0], ms.inputs[0])
    a = nt.nodes.new("ShaderNodeBsdfPrincipled")
    a.inputs["Base Color"].default_value = (0.13, 0.13, 0.13, 1)
    a.inputs["Roughness"].default_value = 0.9
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.85, 0.87, 0.92, 1) if snow else (0.13, 0.13, 0.13, 1)
    b.inputs["Roughness"].default_value = 0.5
    L(a.outputs[0], ms.inputs[1])
    L(b.outputs[0], ms.inputs[2])
    L(ms.outputs[0], out.inputs[0])
    ob.data.materials.append(m)
    return ob


def atmosphere(size=(6000, 6000, 600), center=(0, 0, 300), density=0.0006, color=(0.75, 0.8, 0.9)):
    """Uniform aerial-perspective haze (cheap version: principled volume, no noise)."""
    m = bpy.data.materials.new("haze")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = density
    pv.inputs["Color"].default_value = (*color, 1)
    pv.inputs["Anisotropy"].default_value = 0.5
    nt.links.new(pv.outputs[0], out.inputs["Volume"])
    ob = box(center, size, None, name="haze")
    ob.data = ob.data.copy()
    ob.data.materials.clear()
    ob.data.materials.append(m)
    return ob


def dust(center, size, density=0.08, color=(0.62, 0.58, 0.52), scale=0.35, falloff=0.9, contrast=1.3):
    return volume_box(center, size, mat_volume(density, color, scale, 0.35, contrast, falloff_z=falloff))


def smoke(center, size, density=0.6, color=(0.08, 0.08, 0.08), scale=0.6, emit=0.0):
    return volume_box(center, size, mat_volume(density, color, scale, 0.2, 1.6, emit=emit, falloff_z=1.0,
                                               absorb=(0.2, 0.2, 0.2)))


def fire(center, size, strength=40):
    ob = box(center, size, None, name="fire")
    ob.data = ob.data.copy()
    ob.data.materials.clear()
    ob.data.materials.append(mat_fire(strength))
    sub = ob.modifiers.new("s", "SUBSURF")
    sub.levels = 2
    sub.render_levels = 2
    ob.visible_shadow = False
    return ob


# ------------------------------------------------------------------ extra builders
def mat_facade(wall=(0.6, 0.58, 0.54), glass=(0.03, 0.035, 0.045), bay=3.2, floor=3.6, frac=0.35, lit=0.0,
               lit_col=(1.0, 0.72, 0.4), name="facade", rough=0.8):
    """Cheap window-grid facade for aerial/distant buildings (Brick texture: bricks = windows, mortar = wall)."""
    key = ("facade", wall, glass, bay, floor, frac, lit)
    if key in _MAT:
        return _MAT[key]
    m = bpy.data.materials.new(name)
    nt, p, out = _nodes(m)
    L = nt.links.new
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs[0])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    L(sep.outputs[0], add.inputs[0])
    L(sep.outputs[1], add.inputs[1])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    L(add.outputs[0], comb.inputs[0])
    L(sep.outputs[2], comb.inputs[1])
    bt = nt.nodes.new("ShaderNodeTexBrick")
    bt.offset = 0.0
    bt.inputs["Scale"].default_value = 1.0
    bt.inputs["Brick Width"].default_value = bay
    bt.inputs["Row Height"].default_value = floor
    bt.inputs["Mortar Size"].default_value = min(bay, floor) * frac
    bt.inputs["Mortar Smooth"].default_value = 0.0
    bt.inputs["Color1"].default_value = (*glass, 1)
    bt.inputs["Color2"].default_value = (glass[0] * 2.5, glass[1] * 2.5, glass[2] * 2.5, 1)
    bt.inputs["Mortar"].default_value = (*wall, 1)
    L(comb.outputs[0], bt.inputs["Vector"])
    L(bt.outputs["Color"], p.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.05
    rr.inputs["To Max"].default_value = rough
    L(bt.outputs["Fac"], rr.inputs["Value"])
    L(rr.outputs["Result"], p.inputs["Roughness"])
    if lit > 0:
        # random lit windows: brick colour noise -> threshold
        wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
        sn = nt.nodes.new("ShaderNodeMath")
        sn.operation = "SNAP"
        sn.inputs[1].default_value = 1.0
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1 / bay, 1 / floor, 1)
        L(comb.outputs[0], mp.inputs[0])
        L(mp.outputs[0], wn.inputs["Vector"])
        th = nt.nodes.new("ShaderNodeMath")
        th.operation = "GREATER_THAN"
        th.inputs[1].default_value = 0.55
        L(wn.outputs["Value"], th.inputs[0])
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        L(bt.outputs["Fac"], inv.inputs[1])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        L(th.outputs[0], mul.inputs[0])
        L(inv.outputs[0], mul.inputs[1])
        mul2 = nt.nodes.new("ShaderNodeMath")
        mul2.operation = "MULTIPLY"
        mul2.inputs[1].default_value = lit
        L(mul.outputs[0], mul2.inputs[0])
        _set(p, "Emission Color", (*lit_col, 1))
        L(mul2.outputs[0], p.inputs["Emission Strength"])
    _MAT[key] = m
    return m


FONTS = {}


def text_obj(text, loc, size=0.5, material=None, rot=(math.pi / 2, 0, 0), font=None, extrude=0.01, align="CENTER"):
    cu = bpy.data.curves.new("txt", "FONT")
    cu.body = text
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = "CENTER"
    if font:
        if font not in FONTS:
            FONTS[font] = bpy.data.fonts.load(font)
        cu.font = FONTS[font]
    ob = bpy.data.objects.new("txt", cu)
    ob.location = loc
    ob.rotation_euler = rot
    if material:
        cu.materials.append(material)
    return link(ob)


def sign(text, loc, w, h, bg, fg, rot_z=0.0, size=None, font=None):
    """Flat sign board facing -Y (rotated by rot_z)."""
    root = bpy.data.objects.new("sign", None)
    link(root)
    b = box((0, 0, 0), (w, 0.06, h), bg)
    t = text_obj(text, (0, -0.04, 0), size or h * 0.55, fg, font=font)
    b.parent = root
    t.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root


def city_grid(cx, cy, ex, ey, block=60, street_w=14, seed=0, hmin=6, hmax=22, tall=None, lit=0.0, mats=None,
              skip=None, roof_mats=None, low=False, damaged=0.0):
    """Aerial city: blocks filled with box buildings using facade shader. Returns list of objects."""
    mats = mats or M()
    rr = random.Random(seed)
    walls = [(0.62, 0.58, 0.52), (0.55, 0.53, 0.5), (0.45, 0.3, 0.24), (0.7, 0.68, 0.64), (0.5, 0.5, 0.52),
             (0.6, 0.5, 0.4), (0.35, 0.36, 0.38)]
    facs = [mat_facade(w, lit=lit, bay=rr.choice([2.8, 3.2, 3.6])) for w in walls]
    roofs = roof_mats or [mat("roofg", (0.3, 0.3, 0.3), rough=0.9, var=0.3, bump=0.2),
                          mat("roofg2", (0.42, 0.41, 0.38), rough=0.9, var=0.3, bump=0.2), mats["roof_iron"],
                          mats["roof_red"]]
    objs = []
    nx, ny = int(ex / block), int(ey / block)
    for i in range(-nx // 2, nx // 2 + 1):
        for j in range(-ny // 2, ny // 2 + 1):
            bx, by = cx + i * block, cy + j * block
            if skip and skip(bx, by):
                continue
            inner = block - street_w
            # subdivide block into lots
            x = bx - inner / 2
            while x < bx + inner / 2 - 4:
                lw = min(rr.uniform(8, 22), bx + inner / 2 - x)
                y = by - inner / 2
                while y < by + inner / 2 - 4:
                    ld = min(rr.uniform(10, 25), by + inner / 2 - y)
                    if rr.random() < 0.88:
                        dist = math.hypot(bx - cx, by - cy)
                        hh = rr.uniform(hmin, hmax) * (1.0 if dist < 250 else 0.6)
                        if tall and rr.random() < tall and dist < 300:
                            hh = rr.uniform(30, 60)
                        if low:
                            hh = rr.uniform(4, 7)
                        f = rr.choice(facs)
                        o = box((x + lw / 2, y + ld / 2, hh / 2), (lw - 1.0, ld - 1.0, hh), f)
                        objs.append(o)
                        objs.append(box((x + lw / 2, y + ld / 2, hh + 0.1), (lw - 1.0, ld - 1.0, 0.2), rr.choice(roofs)))
                        if damaged and rr.random() < damaged:
                            objs.append(rock((x + lw / 2, y + ld / 2, 0.5), (lw * 0.4, ld * 0.4, 1.5), mats["rubble_dust"]))
                    y += ld
                x += lw
    return objs


def city_trees(cx, cy, ex, ey, n, mats=None, seed=0, avoid=None):
    mats = mats or M()
    rr = random.Random(seed)
    objs = []
    for i in range(n):
        x, y = cx + rr.uniform(-ex / 2, ex / 2), cy + rr.uniform(-ey / 2, ey / 2)
        if avoid and avoid(x, y):
            continue
        s = rr.uniform(3, 6)
        ob = sphere((x, y, s * 1.2), s, mats["leaves"], subdiv=2, scale=(s, s, s * 0.8))
        objs.append(ob)
    return objs


def cathedral(x, y, rot=0.0, mats=None, broken=0.0, seed=0):
    """Gothic revival stone cathedral with west tower + spire. broken: 0 intact, 1 spire/tower collapsed."""
    mats = mats or M()
    st = mats["stone"]
    sd = mats["stone_dark"]
    roof = mat("slate", (0.13, 0.14, 0.15), rough=0.6, var=0.2, bump=0.2, bump_scale=60)
    gl = mat_glass(dark=0.01, rough=0.15, tint=(0.4, 0.45, 0.6))
    root = bpy.data.objects.new("cath", None)
    link(root)
    o = []
    NL, NW, NH = 50, 14, 15
    # nave + aisles (extend +Y, tower at y=0 side)
    o.append(box((0, 12 + NL / 2, NH / 2), (NW, NL, NH), st))
    for s_ in (-1, 1):
        o.append(box((s_ * (NW / 2 + 3.5), 12 + NL / 2, 4.5), (7, NL - 4, 9), st))
    # pitched roof
    rh = 9
    v = [(-NW / 2 - 0.6, 12, NH), (NW / 2 + 0.6, 12, NH), (0, 12, NH + rh), (-NW / 2 - 0.6, 12 + NL, NH),
         (NW / 2 + 0.6, 12 + NL, NH), (0, 12 + NL, NH + rh)]
    r_ = mesh_from("roof", v, [(0, 2, 5, 3), (2, 1, 4, 5)], roof)
    r_.modifiers.new("s", "SOLIDIFY").thickness = 0.3
    o.append(r_)
    o.append(mesh_from("gab", [(-NW / 2, 12.01, NH), (NW / 2, 12.01, NH), (0, 12.01, NH + rh)], [(0, 1, 2)], st))
    # buttresses + lancet windows on both sides
    for k in range(9):
        yy = 16 + k * 5.4
        for s_ in (-1, 1):
            o.append(box((s_ * (NW / 2 + 7.3), yy, 4.2), (1.2, 1.4, 8.4), sd))
            o.append(box((s_ * (NW / 2 + 0.05), yy + 2.7, NH * 0.72), (0.2, 1.3, 4.5), gl))
            o.append(mesh_from("arch", [(s_ * (NW / 2 + 0.06), yy + 2.05, NH * 0.72 + 2.25), (s_ * (NW / 2 + 0.06), yy + 3.35, NH * 0.72 + 2.25),
                                        (s_ * (NW / 2 + 0.06), yy + 2.7, NH * 0.72 + 3.3)], [(0, 1, 2)], gl))
            o.append(box((s_ * (NW / 2 + 7.05), yy + 2.7, 4.6), (0.2, 1.4, 3.6), gl))
    # tower
    TW, TH = 9.5, 32
    if broken < 0.5:
        o.append(box((0, 6.5, TH / 2), (TW, TW, TH), st))
        for s_x in (-1, 1):
            for s_y in (-1, 1):
                o.append(box((s_x * TW / 2, 6.5 + s_y * TW / 2, TH / 2 - 2), (1.6, 1.6, TH - 4), sd))
                o.append(cylinder((s_x * TW / 2, 6.5 + s_y * TW / 2, TH + 2.2), 0.55, 4.4, sd, verts=8))
        for zc in (TH * 0.55, TH * 0.82):
            for s_ in (-1, 1):
                o.append(box((s_ * (TW / 2 + 0.05), 6.5, zc), (0.2, 1.6, 5.0), gl))
            o.append(box((0, 6.5 - TW / 2 - 0.05, zc), (1.6, 0.2, 5.0), gl))
        o.append(box((0, 6.5, TH + 0.5), (TW + 0.6, TW + 0.6, 1.0), sd))
        # spire: 8-sided cone
        sp = bpy.data.meshes.new("spire")
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=3.6, radius2=0.05, depth=31)
        bm.to_mesh(sp)
        bm.free()
        so = bpy.data.objects.new("spire", sp)
        so.location = (0, 6.5, TH + 1 + 15.5)
        sp.materials.append(sd)
        link(so)
        o.append(so)
        o.append(cylinder((0, 6.5, TH + 33.5), 0.08, 3, mats["metal"], verts=6))
        o.append(box((0, 6.5, TH + 34.2), (1.0, 0.1, 0.12), mats["metal"]))
    else:
        # stump of tower, jagged top
        o.append(box((0, 6.5, 7), (TW, TW, 14), st))
        for k in range(8):
            o.append(box((rnd(-3, 3), 6.5 + rnd(-3, 3), 14 + rnd(0, 4)), (rnd(1.5, 3.5), rnd(1.5, 3), rnd(2, 6)), st,
                         rot=(rnd(-.3, .3), rnd(-.3, .3), rnd(0, 1))))
        o += rubble_pile(0, -6, 16, 12, 6, n=420, mats=mats, slabs=6, bricks=0, seed=seed)
        o.append(box((0, 12.01, NH * 0.6), (6, 0.5, 7), _reveal_mat()))  # gaping hole into nave
    # west door + rose window
    o.append(box((0, 6.5 - TW / 2 - 0.06, 3.2), (2.6, 0.2, 5.2), mats["wood"]))
    for ob in o:
        if ob.parent is None:
            ob.parent = root
    root.location = (x, y, 0)
    root.rotation_euler = (0, 0, rot)
    return root


def rnd(a, b):
    return R.uniform(a, b)


def pancake(x0, y0, w, d, floors_crushed=3, floors_intact=2, fh=3.4, tilt=0.03, mats=None, seed=0):
    """PGC-style collapse: lower floors pancaked into a thin stack, upper floors sitting on top."""
    mats = mats or M()
    rr = random.Random(seed)
    o = []
    z = 0.0
    for k in range(floors_crushed):
        th = 0.45
        o.append(box((x0 + w / 2 + rr.uniform(-0.6, 0.6), y0 + d / 2 + rr.uniform(-0.4, 0.4), z + th / 2),
                     (w + rr.uniform(-0.5, 1.2), d + rr.uniform(-0.5, 1.0), th), mats["concrete"],
                     rot=(rr.uniform(-tilt, tilt), rr.uniform(-tilt, tilt), rr.uniform(-0.02, 0.02))))
        # crushed layer between slabs
        o.append(box((x0 + w / 2, y0 + d / 2, z + th + 0.25), (w - 0.5, d - 0.5, 0.5), _reveal_mat()))
        for i in range(int(w / 1.5)):
            o.append(rock((x0 + rr.uniform(0, w), y0 - 0.3, z + th + 0.2), (rr.uniform(0.2, 0.6),) * 3, mats["rubble_dust"]))
        z += th + 0.5
    base = z
    root = bpy.data.objects.new("upper", None)
    link(root)
    up = office_building(0, 0, w, d, floors_intact, fh=fh, mats=mats)
    for ob in up:
        ob.parent = root
    root.location = (x0 + 0.4, y0 - 0.3, base)
    root.rotation_euler = (rr.uniform(-0.04, 0.04), 0.05, 0.02)
    o += rubble_pile(x0 + w / 2, y0 - 2, w * 0.6, 4, 1.2, n=150, mats=mats, seed=seed + 1)
    return o


def excavator(x, y, rot=0.0, mats=None, boom_up=0.6):
    mats = mats or M()
    yel = mat("cat", (0.75, 0.5, 0.03), rough=0.45, var=0.15, bump=0.05, grime=0.4)
    root = bpy.data.objects.new("exc", None)
    link(root)
    o = [box((0, 1.4, 0.5), (4.6, 0.6, 1.0), mats["metal_dark"], bevel=0.3),
         box((0, -1.4, 0.5), (4.6, 0.6, 1.0), mats["metal_dark"], bevel=0.3),
         box((0, 0, 1.5), (3.6, 2.9, 1.1), yel, bevel=0.05),
         box((0.6, 0.8, 2.6), (1.3, 1.0, 1.4), mats["glass"], bevel=0.05),
         box((-1.4, 0, 1.9), (1.0, 2.8, 1.3), yel, bevel=0.1)]
    b1 = box((2.6, -0.2, 2.6 + boom_up * 1.5), (4.2, 0.5, 0.6), yel)
    b1.rotation_euler = (0, -boom_up, 0)
    b2 = box((4.6, -0.2, 2.4), (0.45, 0.45, 3.4), yel)
    b2.rotation_euler = (0, 0.35, 0)
    bk = box((5.0, -0.2, 0.7), (1.1, 1.1, 0.8), mats["metal_dark"], bevel=0.2)
    o += [b1, b2, bk]
    for ob in o:
        ob.parent = root
    root.location = (x, y, 0)
    root.rotation_euler = (0, 0, rot)
    return root


def mesh_fence(x0, y0, x1, y1, h=2.0, mats=None):
    """Temporary construction fence panels (wire mesh via wireframe modifier) with concrete feet."""
    mats = mats or M()
    L = math.hypot(x1 - x0, y1 - y0)
    n = max(1, int(L / 3.4))
    ang = math.atan2(y1 - y0, x1 - x0)
    o = []
    for i in range(n):
        t = (i + 0.5) / n
        cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        me = bpy.data.meshes.new("pan")
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=30, y_segments=18, size=0.5)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new("panel", me)
        ob.location = (cx, cy, h / 2 + 0.15)
        ob.scale = (3.3, h, 1)
        ob.rotation_euler = (math.pi / 2, 0, ang)
        wf = ob.modifiers.new("w", "WIREFRAME")
        wf.thickness = 0.008
        me.materials.append(mats["metal"])
        link(ob)
        o.append(ob)
        o.append(box((cx, cy, h + 0.15), (3.3, 0.05, 0.05), mats["metal"], rot=(0, 0, ang)))
        o.append(box((cx, cy, 0.15), (3.3, 0.05, 0.05), mats["metal"], rot=(0, 0, ang)))
        fx, fy = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
        o.append(box((fx, fy, 0.08), (0.6, 0.25, 0.16), mats["concrete"], rot=(0, 0, ang)))
        o.append(cylinder((fx, fy, h / 2 + 0.15), 0.025, h, mats["metal"], verts=6))
    return o


def container(x, y, rot=0.0, color=(0.7, 0.2, 0.1), z=0.0, open_side=False, mats=None, length=6.06):
    mats = mats or M()
    m = mat(f"ctr{color}", color, rough=0.5, var=0.1, bump=0.3, bump_scale=5, grime=0.25)
    root = bpy.data.objects.new("ctr", None)
    link(root)
    o = [box((0, 0, 1.3), (length, 2.44, 2.59), m, bevel=0.01)]
    for k in range(int(length / 0.35)):
        o.append(box((-length / 2 + 0.2 + k * 0.35, -1.23, 1.3), (0.12, 0.04, 2.4), m))
    if open_side:
        o.append(box((0, -1.27, 1.25), (length * 0.6, 0.05, 1.9), mat_glass(lit=1.5)))
        o.append(box((0, -1.6, 2.6), (length * 0.7, 0.7, 0.08), mats["trim"]))
    for ob in o:
        ob.parent = root
    root.location = (x, y, z)
    root.rotation_euler = (0, 0, rot)
    return root


def tape(x0, y0, x1, y1, z=1.0, mats=None):
    L = math.hypot(x1 - x0, y1 - y0)
    n = max(1, int(L / 0.6))
    a = math.atan2(y1 - y0, x1 - x0)
    red = mat("tred", (0.6, 0.02, 0.02), rough=0.4, bump=0)
    wht = mat("twht", (0.85, 0.85, 0.85), rough=0.4, bump=0)
    o = []
    for i in range(n):
        t = (i + 0.5) / n
        o.append(box((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z - 0.05 * math.sin(math.pi * t)), (L / n, 0.005, 0.07),
                     red if i % 2 else wht, rot=(0, 0, a)))
    return o


def floodlight(x, y, h, look, energy=40000, mats=None):
    mats = mats or M()
    o = [cylinder((x, y, h / 2), 0.07, h, mats["metal_dark"], verts=8),
         box((x, y, h), (0.8, 0.4, 0.5), mats["metal_dark"])]
    g = box((x, y - 0.21, h), (0.7, 0.02, 0.4), mat("flglow", (1, 1, 0.95), emit=(1, 0.97, 0.9), emit_str=60, bump=0))
    o.append(g)
    spot((x, y - 0.4, h), look, energy=energy, angle=55, color=(1, 0.95, 0.85), radius=0.4)
    return o
