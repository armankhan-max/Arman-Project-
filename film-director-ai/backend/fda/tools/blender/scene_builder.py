"""Runs INSIDE Blender:  blender -b -P scene_builder.py -- params.json
Builds one parameterised scene template, animates the camera, renders an MP4 and saves the .blend.
This file is fixed code; the Director only supplies validated numbers, colours and choices."""
import json
import math
import random
import sys

import bpy

P = json.load(open(sys.argv[sys.argv.index("--") + 1]))
rnd = random.Random(P.get("seed", 1))
FPS, DUR = int(P.get("fps", 24)), float(P.get("duration", 5.0))
NF = max(2, int(round(FPS * DUR)))


def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255) ** 2.2, (int(h[2:4], 16) / 255) ** 2.2, (int(h[4:6], 16) / 255) ** 2.2, a


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    if P.get("engine", "EEVEE") == "EEVEE":
        sc.render.engine = "BLENDER_EEVEE"
        ee = sc.eevee
        ee.taa_render_samples = int(P.get("samples", 32))
        for k, v in (("use_bloom", True), ("bloom_intensity", 0.06), ("use_gtao", True), ("use_soft_shadows", True)):
            if hasattr(ee, k):
                setattr(ee, k, v)
    else:
        sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = int(P.get("samples", 32))
    sc.cycles.use_adaptive_sampling = True
    sc.render.film_transparent = False
    sc.cycles.use_denoising = False  # many distro builds lack OpenImageDenoise; more samples instead
    sc.render.resolution_x, sc.render.resolution_y = int(P.get("width", 1280)), int(P.get("height", 720))
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, NF
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.filepath = P["out"]
    sc.view_settings.view_transform = "Filmic" if "Filmic" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Standard"
    world = bpy.data.worlds.new("W")
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = hexc(P.get("background", "#020308"))
    world.node_tree.nodes["Background"].inputs[1].default_value = float(P.get("ambient", 0.3))
    return sc


def mat(name, color, emission=0.0, rough=0.5, metal=0.0, noise=0.0, color2=None, scale=4.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if noise > 0 and color2:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = scale
        tex.inputs["Detail"].default_value = 8
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = hexc(color)
        ramp.color_ramp.elements[1].color = hexc(color2)
        nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    else:
        b.inputs["Base Color"].default_value = hexc(color)
    if emission > 0:
        key = "Emission Color" if "Emission Color" in b.inputs else "Emission"
        b.inputs[key].default_value = hexc(color)
        b.inputs["Emission Strength"].default_value = emission
    return m


def sphere(name, r, loc, material, seg=64):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.active_object
    o.name = name
    bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    return o


def light_sun(energy=3.0, rot=(0.9, 0.2, 0.6), color="#ffffff"):
    bpy.ops.object.light_add(type="SUN", rotation=rot)
    l = bpy.context.active_object
    l.data.energy = energy
    l.data.color = hexc(color)[:3]
    return l


def stars(n=600, radius=60):
    m = mat("star", "#ffffff", emission=6)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.06, location=(0, 0, 0))
    base = bpy.context.active_object
    base.data.materials.append(m)
    for i in range(n):
        th, ph = rnd.uniform(0, math.tau), math.acos(rnd.uniform(-1, 1))
        o = base.copy()
        o.location = (radius * math.sin(ph) * math.cos(th), radius * math.sin(ph) * math.sin(th), radius * math.cos(ph))
        o.scale = [rnd.uniform(0.5, 1.6)] * 3
        bpy.context.collection.objects.link(o)
    bpy.data.objects.remove(base)


def camera(target=(0, 0, 0), move="orbit", dist=8.0, height=1.5, lens=35):
    bpy.ops.object.empty_add(location=target)
    tgt = bpy.context.active_object
    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    cam.data.lens = lens
    bpy.context.scene.camera = cam
    c = cam.constraints.new("TRACK_TO")
    c.target, c.track_axis, c.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
    for f in range(1, NF + 1, max(1, NF // 24)):
        u = (f - 1) / max(1, NF - 1)
        e = u * u * (3 - 2 * u)
        if move == "orbit":
            a = math.radians(-35 + 70 * e)
            d = dist
        elif move == "push_in":
            a, d = math.radians(15), dist * (1.25 - 0.45 * e)
        elif move == "pull_out":
            a, d = math.radians(-10), dist * (0.8 + 0.5 * e)
        else:  # flyby
            a, d = math.radians(-60 + 120 * e), dist * (1.1 - 0.3 * math.sin(math.pi * e))
        cam.location = (target[0] + d * math.sin(a), target[1] - d * math.cos(a), target[2] + height * (1 - 0.3 * e))
        cam.keyframe_insert("location", frame=f)
    return cam


def spin(o, turns=0.15, axis=2):
    o.rotation_euler[axis] = 0
    o.keyframe_insert("rotation_euler", frame=1)
    o.rotation_euler[axis] = math.tau * turns
    o.keyframe_insert("rotation_euler", frame=NF)
    for fc in (o.animation_data.action.fcurves if o.animation_data and o.animation_data.action else []):
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"


# ------------------------------------------------------------------ templates
def t_planet():
    p = sphere("Planet", 2.0, (0, 0, 0), mat("surface", P.get("color", "#c8894e"), noise=1, color2=P.get("color2", "#6b3e1f"), scale=float(P.get("bands", 6)), rough=0.8))
    p.scale[2] = 0.94
    spin(p, 0.08)
    if P.get("rings"):
        bpy.ops.mesh.primitive_torus_add(major_radius=3.4, minor_radius=0.9, major_segments=128, minor_segments=16)
        r = bpy.context.active_object
        r.scale[2] = 0.02
        r.data.materials.append(mat("rings", P.get("ring_color", "#d9c39a"), noise=1, color2="#8a7350", scale=30, rough=0.9))
        r.rotation_euler = (math.radians(14), math.radians(-8), 0)
    if P.get("atmosphere", False):
        a = sphere("Atmo", 2.08, (0, 0, 0), mat("atmo", P.get("atmo_color", "#7fb6ff"), emission=0.6, rough=1))
        a.active_material.blend_method = "BLEND"
        bsdf = a.active_material.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Alpha"].default_value = 0.12
    light_sun(float(P.get("sun", 4.0)))
    stars()
    camera(move=P.get("move", "orbit"), dist=12.5 if P.get("rings") else 8.5)


def t_solar_system():
    sun = sphere("Sun", 1.4, (0, 0, 0), mat("sun", "#ffb347", emission=12))
    bpy.ops.object.light_add(type="POINT", location=(0, 0, 0))
    bpy.context.active_object.data.energy = 6000
    n = max(2, min(8, int(P.get("planets", 5))))
    cols = ["#9a8f86", "#d9b37c", "#4a7fd1", "#c1502e", "#d4a373", "#e3cf9b", "#8fd3e8", "#3f63c6"]
    for i in range(n):
        r = 2.6 + i * 1.25
        pl = sphere("P%d" % i, 0.18 + 0.12 * (i % 4), (r, 0, 0), mat("p%d" % i, cols[i % 8], rough=0.7), seg=32)
        bpy.ops.object.empty_add(location=(0, 0, 0))
        piv = bpy.context.active_object
        pl.parent = piv
        piv.rotation_euler[2] = rnd.uniform(0, math.tau)
        spin(piv, 0.35 / (1 + i * 0.6))
    stars()
    camera(move=P.get("move", "orbit"), dist=7 + n * 1.6, height=4.5, lens=30)


def t_black_hole():
    sphere("Horizon", 1.0, (0, 0, 0), mat("void", "#000000", rough=1))
    bpy.ops.mesh.primitive_torus_add(major_radius=2.4, minor_radius=0.8, major_segments=128, minor_segments=24)
    d = bpy.context.active_object
    d.scale[2] = 0.08
    d.data.materials.append(mat("disk", P.get("color", "#ff8a2a"), emission=8, noise=1, color2="#ffe2a8", scale=10))
    spin(d, 0.2)
    stars(900)
    camera(move=P.get("move", "push_in"), dist=9, height=1.2)


def t_molecule():
    atoms = P.get("atoms") or [["O", 0, 0, 0], ["H", 0.96, 0.0, 0.0], ["H", -0.24, 0.93, 0.0]]
    cmap = {"H": "#f2f2f2", "C": "#333333", "O": "#e03b3b", "N": "#3b62e0", "S": "#e0c53b", "P": "#f08a24"}
    rad = {"H": 0.32, "C": 0.55, "O": 0.5, "N": 0.52, "S": 0.65, "P": 0.62}
    bpy.ops.object.empty_add()
    root = bpy.context.active_object
    pts = []
    for el, x, y, z in atoms[:60]:
        o = sphere(el, rad.get(el, 0.5), (x * 1.5, y * 1.5, z * 1.5), mat(el, cmap.get(el, "#aaaaaa"), rough=0.3, metal=0.1), seg=32)
        o.parent = root
        pts.append(o.location.copy())
    bm = mat("bond", "#bbbbbb", rough=0.4)
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            dv = pts[j] - pts[i]
            if dv.length < 2.6:
                bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=dv.length, location=(pts[i] + pts[j]) / 2)
                c = bpy.context.active_object
                c.rotation_mode = "QUATERNION"
                c.rotation_quaternion = dv.to_track_quat("Z", "Y")
                c.data.materials.append(bm)
                c.parent = root
    spin(root, 0.3)
    light_sun(3.5)
    bpy.context.scene.world.node_tree.nodes["Background"].inputs[0].default_value = hexc(P.get("background", "#0b1020"))
    camera(move=P.get("move", "push_in"), dist=7, height=1.0, lens=50)


def t_dna():
    bpy.ops.object.empty_add()
    root = bpy.context.active_object
    a, b, r = mat("a", P.get("color", "#4fc3f7"), emission=1.5), mat("b", P.get("color2", "#f06292"), emission=1.5), mat("rung", "#e0e0e0", rough=0.4)
    for i in range(40):
        t = i * 0.35
        z = i * 0.22 - 4.4
        for k, mm in ((0, a), (math.pi, b)):
            o = sphere("n", 0.16, (math.cos(t + k) * 1.1, math.sin(t + k) * 1.1, z), mm, seg=16)
            o.parent = root
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2.2, location=(0, 0, z), rotation=(0, math.pi / 2, t))
        c = bpy.context.active_object
        c.data.materials.append(r)
        c.parent = root
    spin(root, 0.25)
    light_sun(2.5)
    camera(move=P.get("move", "orbit"), dist=9, height=2.0)


def t_terrain():
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=200, y_subdivisions=200, size=40)
    g = bpy.context.active_object
    tex = bpy.data.textures.new("n", "CLOUDS")
    tex.noise_scale = 3.5
    md = g.modifiers.new("d", "DISPLACE")
    md.texture, md.strength = tex, float(P.get("height", 3.0))
    g.data.materials.append(mat("ground", P.get("color", "#5f7a3a"), noise=1, color2=P.get("color2", "#a68a5b"), scale=2, rough=0.95))
    bpy.ops.object.shade_smooth()
    light_sun(4.0, (0.7, 0.1, 2.2), P.get("sun_color", "#ffd9a8"))
    bpy.context.scene.world.node_tree.nodes["Background"].inputs[0].default_value = hexc(P.get("background", "#8fb3d9"))
    bpy.context.scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    camera(target=(0, 6, 0), move="flyby", dist=14, height=5.5, lens=28)


def t_title3d():
    bpy.ops.object.text_add()
    t = bpy.context.active_object
    t.data.body = str(P.get("text", "TITLE"))[:40]
    t.data.extrude, t.data.bevel_depth = 0.12, 0.02
    t.data.align_x, t.data.align_y = "CENTER", "CENTER"
    t.rotation_euler[0] = math.radians(90)
    t.data.materials.append(mat("txt", P.get("color", "#e0b450"), metal=0.9, rough=0.25))
    light_sun(3.0)
    bpy.ops.object.light_add(type="AREA", location=(0, -4, 3))
    bpy.context.active_object.data.energy = 400
    camera(move=P.get("move", "push_in"), dist=7, height=0.4, lens=50)


TEMPLATES = {"planet": t_planet, "solar_system": t_solar_system, "black_hole": t_black_hole, "molecule": t_molecule, "dna": t_dna, "terrain": t_terrain, "title3d": t_title3d}
reset()
TEMPLATES[P["template"]]()
bpy.ops.wm.save_as_mainfile(filepath=P["blend"])
bpy.ops.render.render(animation=True)
print("FDA_BLENDER_DONE", P["out"])
