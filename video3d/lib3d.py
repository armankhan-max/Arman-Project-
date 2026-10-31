"""Shared Blender helpers: scene setup, materials, procedural props, germs, hands, animation."""
import math
import os
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
RES = (int(os.environ.get("RES_X", 720)), int(os.environ.get("RES_Y", 1280)))
SAMPLES = int(os.environ.get("SAMPLES", 24))


# ------------------------------------------------------------------ scene
def reset(world_color=(0.6, 0.65, 0.75), world_strength=0.6):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.03
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 1
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 3
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.render.use_persistent_data = True
    sc.render.threads_mode = "FIXED" if os.environ.get("THREADS") else "AUTO"
    if os.environ.get("THREADS"):
        sc.render.threads = int(os.environ["THREADS"])
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        try:
            sc.view_settings.look = "Medium High Contrast"
        except Exception:
            pass
    w = bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*world_color, 1)
    bg.inputs[1].default_value = world_strength
    return sc


def set_range(n_frames):
    sc = bpy.context.scene
    sc.frame_start = 0
    sc.frame_end = n_frames - 1


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def camera(loc, target, lens=50, dof_dist=None, fstop=2.8):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.data.lens = lens
    cam.data.sensor_width = 36
    cam.data.clip_start = 0.01
    look_at(cam, target)
    if dof_dist is not None:
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = fstop
        if isinstance(dof_dist, (int, float)):
            cam.data.dof.focus_distance = dof_dist
        else:
            cam.data.dof.focus_object = dof_dist
    bpy.context.scene.camera = cam
    return cam


def cam_track(cam, target_obj):
    c = cam.constraints.new("TRACK_TO")
    c.target = target_obj
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return c


def empty(loc=(0, 0, 0), name="Empty"):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.location = loc
    return o


def area_light(loc, target, energy=500, size=3, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=loc)
    l = bpy.context.object
    l.data.energy = energy
    l.data.size = size
    l.data.color = color
    look_at(l, target)
    return l


def point_light(loc, energy=100, radius=0.3, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="POINT", location=loc)
    l = bpy.context.object
    l.data.energy = energy
    l.data.shadow_soft_size = radius
    l.data.color = color
    return l


def studio_lights(target=(0, 0, 0), key=800, fill=250, rim=600, scale=1.0, warm=True):
    t = Vector(target)
    kc = (1.0, 0.93, 0.85) if warm else (1, 1, 1)
    area_light(t + Vector((-4, -4, 5)) * scale, t, key * scale * scale, 4 * scale, kc)
    area_light(t + Vector((5, -3, 2)) * scale, t, fill * scale * scale, 5 * scale, (0.85, 0.9, 1.0))
    area_light(t + Vector((1, 6, 4)) * scale, t, rim * scale * scale, 3 * scale, (0.9, 0.95, 1.0))


# ------------------------------------------------------------------ materials
def bsdf_mat(name, color=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, sss=0.0, sss_radius=(1, 0.4, 0.2),
             sss_scale=0.05, coat=0.0, emit=None, emit_strength=0.0, transmission=0.0, ior=1.45,
             specular=0.5, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    inp = b.inputs
    inp["Base Color"].default_value = (*color, 1)
    inp["Roughness"].default_value = rough
    inp["Metallic"].default_value = metal
    inp["IOR"].default_value = ior
    if "Specular IOR Level" in inp:
        inp["Specular IOR Level"].default_value = specular
    if sss:
        inp["Subsurface Weight"].default_value = sss
        inp["Subsurface Radius"].default_value = sss_radius
        inp["Subsurface Scale"].default_value = sss_scale
    if coat:
        inp["Coat Weight"].default_value = coat
        inp["Coat Roughness"].default_value = 0.05
    if emit is not None:
        inp["Emission Color"].default_value = (*emit, 1)
        inp["Emission Strength"].default_value = emit_strength
    if transmission:
        inp["Transmission Weight"].default_value = transmission
    if alpha < 1:
        inp["Alpha"].default_value = alpha
    return m


def node_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    return m, nt, nt.nodes, nt.links, nt.nodes["Principled BSDF"]


def emission_mat(name, color, strength=5.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*color, 1)
    em.inputs[1].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def image_mat(name, path, emit_strength=0.0, rough=0.3, coat=0.0):
    m, nt, N, L, b = node_mat(name)
    tex = N.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    tex.extension = "CLIP"
    L.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    if emit_strength:
        L.new(tex.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emit_strength
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.03
    return m, b, tex


def skin_mat(name="Skin", tone=(0.78, 0.52, 0.40)):
    m, nt, N, L, b = node_mat(name)
    b.inputs["Base Color"].default_value = (*tone, 1)
    b.inputs["Subsurface Weight"].default_value = 0.35
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    b.inputs["Subsurface Scale"].default_value = 0.08
    b.inputs["Roughness"].default_value = 0.45
    # fine pore bump
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 180
    nz.inputs["Detail"].default_value = 6
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    L.new(nz.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    # subtle color variation (redder areas)
    nz2 = N.new("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = 4
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*tone, 1)
    mix.inputs["B"].default_value = (tone[0] * 1.02, tone[1] * 0.8, tone[2] * 0.78, 1)
    L.new(tc.outputs["Object"], nz2.inputs["Vector"])
    L.new(nz2.outputs["Fac"], mix.inputs["Factor"])
    L.new(mix.outputs["Result"], b.inputs["Base Color"])
    return m


def wood_mat(name="Wood", c1=(0.30, 0.16, 0.07), c2=(0.58, 0.36, 0.17), scale=1.0, rough=0.3):
    m, nt, N, L, b = node_mat(name)
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.5 * scale, 9 * scale, 1.0)
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 10
    nz.inputs["Roughness"].default_value = 0.6
    nz.inputs["Distortion"].default_value = 0.4
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.65
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.04
    L.new(nz.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = 0.35
    return m


def tile_mat(name="Tiles", color=(0.85, 0.88, 0.9), grout=(0.45, 0.47, 0.5), scale=4.0, rough=0.08):
    m, nt, N, L, b = node_mat(name)
    tc = N.new("ShaderNodeTexCoord")
    br = N.new("ShaderNodeTexBrick")
    br.offset = 0.0
    br.inputs["Color1"].default_value = (*color, 1)
    br.inputs["Color2"].default_value = (color[0] * 0.96, color[1] * 0.96, color[2] * 0.97, 1)
    br.inputs["Mortar"].default_value = (*grout, 1)
    br.inputs["Scale"].default_value = scale
    br.inputs["Mortar Size"].default_value = 0.012
    br.inputs["Brick Width"].default_value = 0.5
    br.inputs["Row Height"].default_value = 0.5
    L.new(tc.outputs["Object"], br.inputs["Vector"])
    L.new(br.outputs["Color"], b.inputs["Base Color"])
    inv = N.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    L.new(br.outputs["Fac"], inv.inputs[1])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.4
    L.new(inv.outputs[0], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    rmap = N.new("ShaderNodeMapRange")
    rmap.inputs["To Min"].default_value = rough
    rmap.inputs["To Max"].default_value = 0.7
    L.new(br.outputs["Fac"], rmap.inputs["Value"])
    L.new(rmap.outputs["Result"], b.inputs["Roughness"])
    return m


def assign(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


# ------------------------------------------------------------------ geometry
def smooth(obj, subsurf=0, bevel=None, segments=4):
    if bevel:
        mb = obj.modifiers.new("Bevel", "BEVEL")
        mb.width = bevel
        mb.segments = segments
        mb.limit_method = "ANGLE"
    if subsurf:
        ms = obj.modifiers.new("Sub", "SUBSURF")
        ms.levels = subsurf
        ms.render_levels = subsurf
    try:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shade_smooth()
    except Exception:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def box(size, loc=(0, 0, 0), bevel=0.05, mat=None, name="Box", segments=5):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        smooth(o, bevel=bevel, segments=segments)
    if mat:
        assign(o, mat)
    return o


def plane(size, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, name="Plane"):
    bpy.ops.mesh.primitive_plane_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, 1)
    bpy.ops.object.transform_apply(scale=True)
    if mat:
        assign(o, mat)
    return o


def sphere(r, loc=(0, 0, 0), scale=(1, 1, 1), mat=None, name="Sphere", seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    smooth(o)
    if mat:
        assign(o, mat)
    return o


def cylinder(r, depth, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, name="Cyl", bevel=0.0, verts=64):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object
    o.name = name
    smooth(o, bevel=bevel if bevel else None, segments=4)
    if mat:
        assign(o, mat)
    return o


def torus(R, r, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), mat=None, name="Torus"):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot,
                                     major_segments=96, minor_segments=24)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    smooth(o)
    if mat:
        assign(o, mat)
    return o


def lathe(profile, loc=(0, 0, 0), scale=(1, 1, 1), mat=None, name="Lathe", steps=96, thickness=0.0):
    """profile: list of (r, z) points; revolved around Z."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    verts = [bm.verts.new((r, 0, z)) for r, z in profile]
    for a, b in zip(verts, verts[1:]):
        bm.edges.new((a, b))
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.scale = scale
    sc = o.modifiers.new("Screw", "SCREW")
    sc.steps = steps
    sc.render_steps = steps
    sc.use_merge_vertices = True
    sc.use_normal_calculate = True
    if thickness:
        so = o.modifiers.new("Solid", "SOLIDIFY")
        so.thickness = thickness
    sub = o.modifiers.new("Sub", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 2
    for p in me.polygons:
        p.use_smooth = True
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.shade_smooth()
    if mat:
        o.data.materials.append(mat)
    return o


def star_mesh(name="Star", points=4, r_out=1.0, r_in=0.22):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    c = bm.verts.new((0, 0, 0))
    ring = []
    for i in range(points * 2):
        a = math.pi * i / points + math.pi / 2
        r = r_out if i % 2 == 0 else r_in
        ring.append(bm.verts.new((math.cos(a) * r, math.sin(a) * r, 0)))
    for i in range(len(ring)):
        bm.faces.new((c, ring[i], ring[(i + 1) % len(ring)]))
    bm.to_mesh(me)
    bm.free()
    return me


# ------------------------------------------------------------------ animation
def key(obj, frame, loc=None, rot=None, scale=None, interp=None):
    if loc is not None:
        obj.location = loc
        obj.keyframe_insert("location", frame=frame)
    if rot is not None:
        obj.rotation_euler = rot
        obj.keyframe_insert("rotation_euler", frame=frame)
    if scale is not None:
        if isinstance(scale, (int, float)):
            scale = (scale, scale, scale)
        obj.scale = scale
        obj.keyframe_insert("scale", frame=frame)


def fcurves_of(idblock):
    ad = idblock.animation_data
    if ad is None or ad.action is None:
        return []
    act = ad.action
    try:
        return list(act.fcurves)
    except AttributeError:
        pass
    try:
        from bpy_extras import anim_utils
        cb = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
        return list(cb.fcurves) if cb else []
    except Exception:
        out = []
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out.extend(cb.fcurves)
        return out


def set_interp(idblock, mode="BEZIER", easing=None):
    for fc in fcurves_of(idblock):
        for kp in fc.keyframe_points:
            kp.interpolation = mode
            if easing:
                kp.easing = easing


def add_noise(idblock, path, strength=0.1, scale=10.0, index=-1, phase=None):
    """Add a NOISE modifier on fcurves matching data path (needs at least one keyframe)."""
    for fc in fcurves_of(idblock):
        if fc.data_path == path and (index < 0 or fc.array_index == index):
            m = fc.modifiers.new("NOISE")
            m.strength = strength
            m.scale = scale
            m.phase = phase if phase is not None else random.uniform(0, 100)


def wobble(obj, amount=0.08, speed=6.0, rot_amount=0.25):
    """Organic idle wobble via fcurve noise on scale and rotation."""
    if not fcurves_of(obj) or not any(fc.data_path == "scale" for fc in fcurves_of(obj)):
        obj.keyframe_insert("scale", frame=0)
    if not any(fc.data_path == "rotation_euler" for fc in fcurves_of(obj)):
        obj.keyframe_insert("rotation_euler", frame=0)
    add_noise(obj, "scale", amount, speed)
    add_noise(obj, "rotation_euler", rot_amount, speed * 2)


def pop_in(obj, f, size=1.0, dur=6, overshoot=1.25):
    if isinstance(size, (int, float)):
        size = (size, size, size)
    key(obj, f - 1, scale=(0, 0, 0))
    key(obj, f, scale=(0.0001, 0.0001, 0.0001))
    key(obj, f + dur * 0.6, scale=tuple(s * overshoot for s in size))
    key(obj, f + dur, scale=size)


def pop_out(obj, f, size=1.0, dur=5):
    if isinstance(size, (int, float)):
        size = (size, size, size)
    key(obj, f, scale=size)
    key(obj, f + dur * 0.4, scale=tuple(s * 1.2 for s in size))
    key(obj, f + dur, scale=(0, 0, 0))


def key_value(socket, frame, value):
    socket.default_value = value
    socket.keyframe_insert("default_value", frame=frame)


# ------------------------------------------------------------------ props
_SCREEN_IMG = os.path.join(HERE, "assets", "screen.png")


def phone(loc=(0, 0, 0), rot=(0, 0, 0), color=(0.08, 0.12, 0.25), screen_strength=1.6, name="Phone",
          screen_img=None):
    """Phone lying flat: screen faces +Z. Size 0.75 x 1.55 x 0.08. Returns (root, screen_obj, screen_bsdf)."""
    root = empty(loc, name)
    root.rotation_euler = rot
    body_m = bsdf_mat(name + "Body", color, rough=0.25, metal=0.85, coat=0.5)
    body = box((0.75, 1.55, 0.08), (0, 0, 0), bevel=0.06, mat=body_m, name=name + "Body", segments=6)
    body.parent = root
    # black glass front
    glass_m = bsdf_mat(name + "Glass", (0.005, 0.005, 0.008), rough=0.02, coat=1.0, specular=0.8)
    front = box((0.73, 1.53, 0.012), (0, 0, 0.037), bevel=0.055, mat=glass_m, name=name + "Front", segments=6)
    front.parent = root
    # screen
    m, b, tex = image_mat(name + "ScreenMat", screen_img or _SCREEN_IMG, emit_strength=screen_strength,
                          rough=0.05, coat=1.0)
    scr = plane((0.68, 1.46), (0, 0, 0.0445), mat=m, name=name + "Screen")
    # rounded mask via UV already in image (image has rounded corners alpha -> we drew black corners)
    scr.parent = root
    # camera bump on back
    cam_m = bsdf_mat(name + "CamM", (0.02, 0.02, 0.025), rough=0.1, coat=1)
    bump = box((0.28, 0.28, 0.03), (-0.17, 0.52, -0.05), bevel=0.06, mat=body_m, name=name + "Bump")
    bump.parent = root
    for dx, dy in ((-0.06, 0.06), (0.06, -0.06), (-0.06, -0.06)):
        lens = cylinder(0.045, 0.03, (-0.17 + dx, 0.52 + dy, -0.07), mat=cam_m, name=name + "Lens")
        lens.parent = root
    # side buttons
    for y, l in ((0.35, 0.18), (0.1, 0.12)):
        btn = box((0.02, l, 0.03), (0.38, y, 0), bevel=0.008, mat=body_m, name=name + "Btn")
        btn.parent = root
    return root, scr, b


def germ_material(color, name):
    m, nt, N, L, b = node_mat(name)
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nz.inputs["Detail"].default_value = 4
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (color[0] * 0.12, color[1] * 0.12, color[2] * 0.12, 1)
    ramp.color_ramp.elements[1].color = (color[0] * 0.7, color[1] * 0.7, color[2] * 0.7, 1)
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[1].position = 0.7
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Subsurface Weight"].default_value = 0.15
    b.inputs["Subsurface Radius"].default_value = (color[0] + 0.1, color[1] + 0.1, color[2] + 0.1)
    b.inputs["Subsurface Scale"].default_value = 0.05
    b.inputs["Roughness"].default_value = 0.25
    b.inputs["Coat Weight"].default_value = 0.5
    b.inputs["Coat Roughness"].default_value = 0.15
    # fresnel rim glow
    lw = N.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 0.5
    L.new(lw.outputs["Facing"], mul.inputs[0])
    b.inputs["Emission Color"].default_value = (*color, 1)
    L.new(mul.outputs[0], b.inputs["Emission Strength"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.3
    nz2 = N.new("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = 12
    L.new(tc.outputs["Object"], nz2.inputs["Vector"])
    L.new(nz2.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


GERM_COLORS = [(0.35, 0.95, 0.15), (0.6, 0.25, 1.0), (0.1, 0.85, 0.75), (1.0, 0.55, 0.1), (0.95, 0.2, 0.5)]
_germ_mats = {}
_germ_meshes = {}


def _germ_mesh(kind, seed):
    """Lumpy germ body with cilia/spikes modelled as geometry (much faster to render than hair)."""
    from mathutils import Matrix
    keyname = (kind, seed % 4)
    if keyname in _germ_meshes:
        return _germ_meshes[keyname]
    bpy.ops.mesh.primitive_ico_sphere_add(radius=1, subdivisions=3)
    o = bpy.context.object
    if kind == "rod":
        o.scale = (2.0, 1, 1)
        bpy.ops.object.transform_apply(scale=True)
    tex = bpy.data.textures.new(f"GermTex{seed}", "CLOUDS")
    tex.noise_scale = 0.6
    d = o.modifiers.new("Disp", "DISPLACE")
    d.texture = tex
    d.strength = 0.2
    d.texture_coords = "LOCAL"
    s = o.modifiers.new("Sub", "SUBSURF")
    s.levels = 1
    bpy.ops.object.convert(target="MESH")
    me = o.data
    bm = bmesh.new()
    bm.from_mesh(me)
    rnd = random.Random(seed)
    if kind == "spiky":
        prob, length, taper = 0.05, 0.5, 0.2
    else:
        prob, length, taper = 0.07, 0.3, 0.12
    faces = [f for f in bm.faces if rnd.random() < prob]
    for f in faces:
        n = f.normal.copy()
        r = bmesh.ops.extrude_discrete_faces(bm, faces=[f])
        nf = r["faces"][0]
        c = nf.calc_center_median()
        L_ = length * rnd.uniform(0.6, 1.3)
        bend = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * 0.15
        bmesh.ops.translate(bm, verts=nf.verts, vec=n * L_ + bend)
        c2 = nf.calc_center_median()
        bmesh.ops.scale(bm, verts=nf.verts, vec=(taper, taper, taper),
                        space=Matrix.Translation(-c2))
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    bpy.data.objects.remove(o)
    _germ_meshes[keyname] = me
    return me


def germ(loc, size=0.1, kind=None, color_idx=None, seed=0, hair=False, parent=None, rot=None, name="Germ"):
    rnd = random.Random(seed)
    kind = kind or rnd.choice(["blob", "rod", "spiky", "blob", "rod"])
    ci = color_idx if color_idx is not None else rnd.randrange(len(GERM_COLORS))
    me = _germ_mesh(kind, seed)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    if ci not in _germ_mats:
        _germ_mats[ci] = germ_material(GERM_COLORS[ci], f"GermMat{ci}")
    if len(me.materials) == 0:
        me.materials.append(_germ_mats[ci])
    # per-object material via object link so meshes can be shared
    o.material_slots[0].link = "OBJECT"
    o.material_slots[0].material = _germ_mats[ci]
    o.location = loc
    o.rotation_euler = rot if rot else (rnd.uniform(0, 6.28), rnd.uniform(0, 6.28), rnd.uniform(0, 6.28))
    o.scale = (size, size, size)
    if parent:
        o.parent = parent
    if hair and kind != "spiky":  # optional particle hair (slow in Cycles)
        ps = o.modifiers.new("Hair", "PARTICLE_SYSTEM").particle_system
        st = ps.settings
        st.type = "HAIR"
        st.count = 160 if kind == "rod" else 120
        st.hair_length = 0.45
        st.use_advanced_hair = True
        st.render_step = 3
        st.display_step = 2
        st.child_type = "NONE"
        st.root_radius = 1.0
        st.tip_radius = 0.0
        st.radius_scale = 0.03
        ps.seed = seed
        st.use_hair_bspline = True
        st.factor_random = 0.3
        st.normal_factor = 1.0
        st.brownian_factor = 0.15
        st.use_rotations = False
        st.kink = "CURL"
        st.kink_amplitude = 0.05
        st.kink_frequency = 3
    return o


def germ_cluster(center, radius, n, size=(0.06, 0.12), seed=0, parent=None, flat_z=None, hair=False,
                 normal_offset=0.0, region=None):
    """Scatter n germs. region: (xmin,xmax,ymin,ymax) on plane z=flat_z if given."""
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        s = rnd.uniform(*size)
        if region is not None:
            x = rnd.uniform(region[0], region[1])
            y = rnd.uniform(region[2], region[3])
            p = (x, y, (flat_z or 0) + s * 0.6 + normal_offset)
        else:
            v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized() * radius * rnd.random() ** 0.33
            p = Vector(center) + v
        g = germ(p, s, seed=seed * 100 + i, parent=parent, hair=hair)
        out.append(g)
    return out


def sparkle(loc, size=0.15, color=(1, 1, 0.9), strength=12, cam=None, name="Sparkle"):
    me = star_mesh(name)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.scale = (size, size, size)
    o.data.materials.append(emission_mat(name + "M", color, strength))
    if cam is not None:
        c = o.constraints.new("TRACK_TO")
        c.target = cam
        c.track_axis = "TRACK_Z"
        c.up_axis = "UP_Y"
    return o


def sparkle_burst(cam, points, f, size=0.12, seed=0, hold=10):
    rnd = random.Random(seed)
    out = []
    for i, p in enumerate(points):
        s = sparkle(p, size * rnd.uniform(0.6, 1.3), cam=cam, name=f"Spk{seed}_{i}")
        ff = f + rnd.randint(0, 6)
        sz = size * rnd.uniform(0.6, 1.3)
        key(s, ff - 1, scale=0)
        key(s, ff + 3, scale=sz * 1.3)
        key(s, ff + 3 + hold, scale=sz)
        key(s, ff + 3 + hold + 6, scale=0)
        s.rotation_euler = (0, 0, 0)
        out.append(s)
    return out


# ------------------------------------------------------------------ hand (metaballs)
def _mb_capsule(mb, a, b, r):
    a, b = Vector(a), Vector(b)
    el = mb.elements.new()
    el.type = "CAPSULE"
    el.co = (a + b) / 2
    el.radius = r
    d = b - a
    el.size_x = max(d.length / 2, 0.001)
    el.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized())
    el.stiffness = 2.0
    return el


def _mb_ellipsoid(mb, co, size, r=1.0, rot=None, stiff=2.0):
    el = mb.elements.new()
    el.type = "ELLIPSOID"
    el.co = co
    el.radius = r
    el.size_x, el.size_y, el.size_z = size
    if rot is not None:
        el.rotation = rot
    el.stiffness = stiff
    return el


def hand(name="Hand", curl=(0.2, 0.2, 0.2, 0.2), thumb=0.3, spread=0.08, mat=None, loc=(0, 0, 0),
         rot=(0, 0, 0), scale=1.0, resolution=None, sleeve=(0.15, 0.25, 0.45)):
    """Right hand built with a Skin modifier. Local space: wrist at origin, fingers point +Y,
    palm faces -Z, thumb towards -X. curl per finger (index..pinky): 0 straight, 1 fist."""
    verts, edges, radii, roots = [], [], [], []

    def chain(points, rads):
        start = len(verts)
        roots.append(start)
        for i, (p, r) in enumerate(zip(points, rads)):
            verts.append(tuple(p))
            radii.append(r)
            if i:
                edges.append((start + i - 1, start + i))

    # forearm + wrist + palm (one chain); radius x = width, y = thickness
    chain([(0, -1.5, 0), (0, -0.55, 0), (0, -0.05, 0.0), (0, 0.3, 0.0), (0, 0.66, 0.0)],
          [(0.25, 0.21), (0.24, 0.19), (0.26, 0.14), (0.38, 0.15), (0.37, 0.13)])
    nails = []
    for i, pts in enumerate(fingertip_points(curl, spread)):
        rr = [0.085, 0.09, 0.085, 0.075][i]
        p0 = pts[0] + Vector((0, -0.2, 0))
        chain([p0] + pts, [(rr * 1.05, rr * 0.95)] * 2 + [(rr, rr * 0.92), (rr * 0.95, rr * 0.85), (rr * 0.85, rr * 0.75)])
        nails.append((pts[2], pts[3], rr))
    tp = thumb_points(thumb)
    chain(tp, [(0.13, 0.12), (0.12, 0.11), (0.105, 0.095), (0.095, 0.085)])
    nails.append((tp[2], tp[3], 0.095))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, edges, [])
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    sk = o.modifiers.new("Skin", "SKIN")
    sk.use_smooth_shade = True
    sk.branch_smoothing = 0.6
    for i, sv in enumerate(me.skin_vertices[0].data):
        sv.radius = radii[i]
        sv.use_root = i in roots
    sub = o.modifiers.new("Sub", "SUBSURF")
    sub.levels = 2
    sub.render_levels = 2
    if mat is None:
        mat = skin_mat()
    me.materials.append(mat)
    nail_m = bsdf_mat("Nail", (0.85, 0.62, 0.55), rough=0.15, coat=0.8, sss=0.3)
    for a, b, rr in nails:
        d = (b - a).normalized()
        up = Vector((0, 0, 1))
        up = (up - d * up.dot(d)).normalized()
        c = a.lerp(b, 0.62) + up * rr * 0.62
        n = sphere(1, c, scale=(rr * 0.75, rr * 1.0, rr * 0.25), mat=nail_m, name=name + "Nail", seg=16)
        q = Matrix((d.cross(up), d, up)).transposed().to_quaternion()
        n.rotation_mode = "QUATERNION"
        n.rotation_quaternion = q
        n.parent = o
    if sleeve:
        sm = bsdf_mat(name + "Sleeve", sleeve, rough=0.85)
        s = cylinder(0.3, 1.6, (0, -1.45, 0), rot=(math.pi / 2, 0, 0), mat=sm, name=name + "Sleeve")
        s.scale = (1.0, 0.85, 1)
        cuff = torus(0.3, 0.05, (0, -0.65, 0), rot=(math.pi / 2, 0, 0), scale=(1, 0.85, 1), mat=sm, name=name + "Cuff")
        s.parent = o
        cuff.parent = o
    o.location = loc
    o.rotation_euler = rot
    o.scale = (scale, scale, scale)
    return o


def thumb_points(thumb=0.3):
    p = Vector((-0.18, 0.12, -0.04))
    pts = [p.copy()]
    tdir = Vector((-0.75, 0.55, -0.15 - thumb * 0.5)).normalized()
    for L_ in (0.3, 0.26, 0.22):
        tdir = (tdir + Vector((0.32 * thumb + 0.12, 0.12, -0.12 * thumb))).normalized()
        p = p + tdir * L_
        pts.append(p.copy())
    return pts


def fingertip_points(curl=(0.2, 0.2, 0.2, 0.2), spread=0.08):
    """Local positions of fingertips (index..pinky), matching hand()."""
    lens = [(0.42, 0.26, 0.2), (0.46, 0.29, 0.21), (0.43, 0.27, 0.2), (0.34, 0.21, 0.17)]
    xs = [-0.27, -0.09, 0.09, 0.26]
    base_y = [0.88, 0.92, 0.9, 0.82]
    out = []
    for i in range(4):
        p = Vector((xs[i], base_y[i], 0))
        ang = 0
        dirx = (i - 1.5) * spread
        pts = [p.copy()]
        for seg in range(3):
            ang += curl[i] * (1.25 if seg == 0 else 1.45)
            d = Vector((dirx, math.cos(ang), -math.sin(ang)))
            p = p + d.normalized() * lens[i][seg]
            pts.append(p.copy())
        out.append(pts)
    return out


def render_frames(out_dir, start, end, prefix="f"):
    sc = bpy.context.scene
    os.makedirs(out_dir, exist_ok=True)
    for f in range(start, end):
        path = os.path.join(out_dir, f"{prefix}{f:04d}.png")
        if os.path.exists(path):
            continue
        sc.frame_set(f)
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
