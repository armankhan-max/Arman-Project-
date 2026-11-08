"""Build the Voyager 1 "one light-day" news short as a Blender scene.

One shot per script line. Every camera cut sits on the first word of its
line, and everything that happens inside a shot (labels popping, the beam
drawing, the light pulse leaving/arriving, instruments switching off) is
keyed to individual word timings from transcript.json.

Output: voyager_news.blend with two scenes
  * "Shots" - the 3D world, ten cameras, timeline markers bound to cameras
              (the camera cuts), EEVEE render settings.
  * "Edit"  - the Video Sequencer: the Shots scene as a strip, one text strip
              per caption chunk, and the voiceover. Rendering this scene gives
              the finished MP4.

Run (Blender 5.x):
  blender -b -P build_scene.py            # or: python3 build_scene.py with `pip install bpy`
Then render with render.py (or open the .blend, switch to "Edit", Render Animation).
"""
import json
import math
import os
import re
import sys

import bpy
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
RES = (1920, 1080)        # final video (Edit scene, captions)
SHOT_RES = (1280, 720)    # EEVEE 3D render, scaled to fit in the edit (software GL budget)
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FONT_BLACK = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
SET_SPACING = 2000.0  # every shot set lives at its own X so sets never see each other

# ------------------------------------------------------------------ timing
TRANSCRIPT = json.load(open(os.path.join(HERE, "transcript.json")))
AUDIO_END = TRANSCRIPT[-1]["end"] + 0.8


def F(t):
    """seconds -> frame (scene starts at frame 1)."""
    return 1 + int(round(t * FPS))


def norm(w):
    return re.sub(r"[^a-z0-9\-]", "", w.lower())


class Line:
    def __init__(self, i):
        self.i = i
        self.seg = TRANSCRIPT[i]
        self.words = self.seg["words"]
        self.f0 = 1 if i == 0 else F(self.words[0]["s"])  # the camera cut: first word onset
        self.f1 = (F(TRANSCRIPT[i + 1]["words"][0]["s"]) - 1) if i + 1 < len(TRANSCRIPT) else F(AUDIO_END)

    def w(self, word, nth=0, end=False):
        """Frame of the nth occurrence of `word` in this line (start, or end with end=True)."""
        hits = [x for x in self.words if norm(x["w"]) == norm(word)]
        if len(hits) <= nth:
            raise KeyError(f"line {self.i}: no {word!r} (#{nth}) in {self.seg['text']!r}")
        return F(hits[nth]["e" if end else "s"])

    @property
    def last(self):
        return F(self.words[-1]["e"])


LINES = [Line(i) for i in range(len(TRANSCRIPT))]
assert len(LINES) == 10, "build_scene.py has one shot written per script line (10)"

# ------------------------------------------------------------------ reset
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.edit.keyframe_new_interpolation_type = "BEZIER"
SC = bpy.context.scene
SC.name = "Shots"
SC.render.fps = FPS
SC.frame_start = 1
SC.frame_end = F(AUDIO_END)
SC.render.resolution_x, SC.render.resolution_y = SHOT_RES
SC.render.resolution_percentage = 100

FONT = bpy.data.fonts.load(FONT_BLACK)
FONT.pack()


# ------------------------------------------------------------------ helpers
def key(obj, path, frame, value, interp=None):
    setattr_path(obj, path, value)
    obj.keyframe_insert(data_path=path, frame=frame)


def setattr_path(obj, path, value):
    if "[" in path:  # e.g. inputs[1].default_value handled by caller
        raise ValueError(path)
    cur = getattr(obj, path)
    if hasattr(cur, "__len__") and not isinstance(value, (int, float)):
        for i, v in enumerate(value):
            cur[i] = v
    else:
        setattr(obj, path, value)


def linear(fn):
    """Run fn with linear keyframe interpolation (for constant-speed motion)."""
    prefs = bpy.context.preferences.edit
    old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "LINEAR"
    try:
        fn()
    finally:
        prefs.keyframe_new_interpolation_type = old


def show_only(obj, f0, f1):
    """Render obj only on frames f0..f1 (hide_render keys are constant)."""
    obj.hide_render = True
    obj.keyframe_insert("hide_render", frame=1)
    if f0 > 1:
        obj.keyframe_insert("hide_render", frame=f0 - 1)
    obj.hide_render = False
    obj.keyframe_insert("hide_render", frame=f0)
    obj.keyframe_insert("hide_render", frame=f1)
    obj.hide_render = True
    obj.keyframe_insert("hide_render", frame=f1 + 1)
    obj.hide_viewport = False


def link(obj, coll=None):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    (coll or SC.collection).objects.link(obj)
    return obj


def new_coll(name, in_scene=True):
    c = bpy.data.collections.new(name)
    if in_scene:
        SC.collection.children.link(c)
    return c


def smooth(obj):
    me = obj.data
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.update()


def mesh_obj(name, verts, faces, coll=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    (coll or SC.collection).objects.link(ob)
    return ob


def lathe(name, profile, segs=64, coll=None):
    """Revolve a (radius, z) profile around Z."""
    verts, faces = [], []
    for r, z in profile:
        for j in range(segs):
            a = 2 * math.pi * j / segs
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for i in range(len(profile) - 1):
        for j in range(segs):
            a, b = i * segs + j, i * segs + (j + 1) % segs
            faces.append((a, b, b + segs, a + segs))
    ob = mesh_obj(name, verts, faces, coll)
    smooth(ob)
    return ob


def prim(kind, name, coll=None, **kw):
    getattr(bpy.ops.mesh, f"primitive_{kind}_add")(**kw)
    ob = bpy.context.active_object
    ob.name = name
    link(ob, coll)
    return ob


def sphere(name, r, loc=(0, 0, 0), coll=None, segs=96, rings=48):
    ob = prim("uv_sphere", name, coll, radius=r, location=loc, segments=segs, ring_count=rings)
    smooth(ob)
    return ob


def cyl(name, r, depth, loc=(0, 0, 0), rot=(0, 0, 0), verts=32, coll=None):
    return prim("cylinder", name, coll, radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)


def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), coll=None):
    ob = prim("cube", name, coll, size=1, location=loc, rotation=rot)
    ob.scale = size
    return ob


def empty(name, loc=(0, 0, 0), coll=None):
    ob = bpy.data.objects.new(name, None)
    ob.location = loc
    (coll or SC.collection).objects.link(ob)
    return ob


def instance(coll, name, loc, scale=1.0, rot=(0, 0, 0)):
    ob = empty(name, loc)
    ob.instance_type = "COLLECTION"
    ob.instance_collection = coll
    ob.scale = (scale,) * 3
    ob.rotation_euler = rot
    return ob


def assign(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


# ------------------------------------------------------------------ materials
def new_mat(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    return m, nt, out


def principled(name, color, metallic=0.0, rough=0.5, emit=None, emit_strength=0.0, coat=0.0):
    m, nt, out = new_mat(name)
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = rough
    p.inputs["Coat Weight"].default_value = coat
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = emit_strength
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    m.diffuse_color = (*color, 1)
    return m


def glow(name, color, strength, fresnel=None):
    """Additive glow: emission + fully transparent (no occlusion). fresnel=power for rim-only glow."""
    m, nt, out = new_mat(name)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    if fresnel:
        lw = nt.nodes.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.5
        pw = nt.nodes.new("ShaderNodeMath")
        pw.operation = "POWER"
        pw.inputs[1].default_value = fresnel
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = strength
        nt.links.new(lw.outputs["Facing"], pw.inputs[0])
        nt.links.new(pw.outputs[0], mul.inputs[0])
        nt.links.new(mul.outputs[0], em.inputs["Strength"])
    nt.links.new(em.outputs[0], add.inputs[0])
    nt.links.new(tr.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "BLENDED"
    m.use_backface_culling = True
    return m


def ramp(nt, stops, interp="LINEAR"):
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.interpolation = interp
    els = cr.color_ramp.elements
    while len(els) > len(stops):
        els.remove(els[-1])
    while len(els) < len(stops):
        els.new(0.5)
    for el, (pos, col) in zip(els, stops):
        el.position = pos
        el.color = (*col[:3], col[3] if len(col) > 3 else 1)
    return cr


def earth_mats():
    m, nt, out = new_mat("Earth")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.6
    nz.inputs["Detail"].default_value = 10
    nz.inputs["Roughness"].default_value = 0.62
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    land = ramp(nt, [(0.0, (0.004, 0.02, 0.09)), (0.5, (0.01, 0.06, 0.2)), (0.53, (0.08, 0.16, 0.05)),
                     (0.6, (0.2, 0.17, 0.07)), (0.72, (0.32, 0.27, 0.2))])
    nt.links.new(nz.outputs["Fac"], land.inputs[0])
    # polar ice
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Normal"], sep.inputs[0])
    ab = nt.nodes.new("ShaderNodeMath")
    ab.operation = "ABSOLUTE"
    nt.links.new(sep.outputs["Z"], ab.inputs[0])
    ice = ramp(nt, [(0.82, (0, 0, 0)), (0.86, (1, 1, 1))])
    nt.links.new(ab.outputs[0], ice.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(ice.outputs[0], mix.inputs["Factor"])
    nt.links.new(land.outputs[0], mix.inputs["A"])
    mix.inputs["B"].default_value = (0.85, 0.9, 0.95, 1)
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = 0.55
    p.inputs["Specular IOR Level"].default_value = 0.6
    nt.links.new(mix.outputs["Result"], p.inputs["Base Color"])
    # oceans shinier
    rr = ramp(nt, [(0.5, (0.25, 0.25, 0.25)), (0.53, (0.85, 0.85, 0.85))])
    nt.links.new(nz.outputs["Fac"], rr.inputs[0])
    nt.links.new(rr.outputs[0], p.inputs["Roughness"])
    nt.links.new(p.outputs[0], out.inputs["Surface"])

    c, nt, out = new_mat("Clouds")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.2
    nz.inputs["Detail"].default_value = 12
    nz.inputs["Distortion"].default_value = 0.6
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    a = ramp(nt, [(0.5, (0, 0, 0)), (0.68, (1, 1, 1))])
    nt.links.new(nz.outputs["Fac"], a.inputs[0])
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (1, 1, 1, 1)
    p.inputs["Roughness"].default_value = 0.9
    nt.links.new(a.outputs[0], p.inputs["Alpha"])
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    c.surface_render_method = "DITHERED"
    return m, c, glow("Atmosphere", (0.25, 0.55, 1.0), 6.0, fresnel=3.0)


def banded(name, stops, scale=1.2, distortion=6.0):
    m, nt, out = new_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.bands_direction = "Z"
    wv.inputs["Scale"].default_value = scale
    wv.inputs["Distortion"].default_value = distortion
    wv.inputs["Detail"].default_value = 4
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    cr = ramp(nt, stops)
    nt.links.new(wv.outputs["Fac"], cr.inputs[0])
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = 0.8
    nt.links.new(cr.outputs[0], p.inputs["Base Color"])
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def ring_mat():
    m, nt, out = new_mat("SaturnRing")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    nt.links.new(tc.outputs["Object"], ln.inputs[0])
    col = ramp(nt, [(0.0, (0.6, 0.5, 0.36, 0)), (0.62, (0.55, 0.47, 0.34, 0.6)), (0.72, (0.8, 0.7, 0.52, 0.95)),
                    (0.8, (0.3, 0.26, 0.2, 0.15)), (0.84, (0.85, 0.76, 0.6, 0.9)), (1.0, (0.6, 0.53, 0.4, 0.3))])
    rs = nt.nodes.new("ShaderNodeMapRange")
    rs.inputs["From Min"].default_value = 1.0
    rs.inputs["From Max"].default_value = 2.3
    nt.links.new(ln.outputs["Value"], rs.inputs["Value"])
    nt.links.new(rs.outputs[0], col.inputs[0])
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Roughness"].default_value = 0.9
    nt.links.new(col.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(col.outputs["Alpha"], p.inputs["Alpha"])
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "DITHERED"
    return m


def record_mat():
    m, nt, out = new_mat("GoldenRecord")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "RINGS"
    wv.rings_direction = "Z"
    wv.inputs["Scale"].default_value = 22
    wv.inputs["Distortion"].default_value = 0.4
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    bump.inputs["Distance"].default_value = 0.002
    nt.links.new(wv.outputs["Fac"], bump.inputs["Height"])
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (0.9, 0.55, 0.18, 1)
    p.inputs["Metallic"].default_value = 1.0
    p.inputs["Roughness"].default_value = 0.3
    p.inputs["Anisotropic"].default_value = 0.8
    nt.links.new(bump.outputs[0], p.inputs["Normal"])
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def heliopause_mat():
    m, nt, out = new_mat("Heliopause")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.025
    nz.inputs["Detail"].default_value = 6
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = ramp(nt, [(0.35, (0.0, 0.0, 0.0)), (0.6, (0.9, 0.35, 1.0)), (0.8, (0.3, 0.6, 1.0))])
    nt.links.new(nz.outputs["Fac"], cr.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 0.22
    nt.links.new(cr.outputs[0], em.inputs["Color"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(em.outputs[0], add.inputs[0])
    nt.links.new(tr.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "BLENDED"
    return m


def keyable_emission(name, color, strength):
    """Emissive material whose strength socket we keyframe (status lights, RTG glow)."""
    m, nt, out = new_mat(name)
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1)
    p.inputs["Roughness"].default_value = 0.3
    p.inputs["Emission Color"].default_value = (*color, 1)
    p.inputs["Emission Strength"].default_value = strength
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m, p.inputs["Emission Strength"]


def key_socket(sock, frame, value):
    sock.default_value = value
    sock.keyframe_insert("default_value", frame=frame)


MAT = {
    "white": principled("PaintWhite", (0.8, 0.8, 0.78), rough=0.45),
    "gold": principled("GoldFoil", (1.0, 0.66, 0.22), metallic=1.0, rough=0.32),
    "dark": principled("DarkMetal", (0.05, 0.05, 0.055), metallic=0.8, rough=0.4),
    "grey": principled("GreyMetal", (0.45, 0.45, 0.47), metallic=1.0, rough=0.35),
    "label": principled("RecordLabel", (0.25, 0.12, 0.04), metallic=0.6, rough=0.45),
    "panel": principled("Panel", (0.03, 0.035, 0.045), metallic=0.5, rough=0.35),
    "hud": glow("HUD", (1.0, 1.0, 1.0), 4.0),
    "hud_gold": glow("HUDGold", (1.0, 0.75, 0.25), 5.0),
    "beam": glow("Beam", (0.3, 0.75, 1.0), 6.0),
    "pulse_light": glow("PulseLight", (1.0, 0.95, 0.75), 60.0),
    "pulse_cmd": glow("PulseCommand", (0.25, 0.8, 1.0), 60.0),
    "pulse_reply": glow("PulseReply", (0.35, 1.0, 0.5), 60.0),
    "halo_blue": glow("HaloBlue", (0.3, 0.6, 1.0), 1.2, fresnel=4.0),
    "halo_gold": glow("HaloGold", (1.0, 0.7, 0.3), 1.2, fresnel=4.0),
    "dot": glow("PaleBlueDot", (0.5, 0.75, 1.0), 40.0),
}
EARTH_MAT, CLOUD_MAT, ATMO_MAT = earth_mats()
JUPITER_MAT = banded("Jupiter", [(0.0, (0.55, 0.38, 0.25)), (0.3, (0.85, 0.75, 0.6)), (0.5, (0.6, 0.35, 0.2)),
                                 (0.7, (0.92, 0.86, 0.75)), (1.0, (0.5, 0.33, 0.22))], scale=1.4)
SATURN_MAT = banded("Saturn", [(0.0, (0.75, 0.62, 0.4)), (0.4, (0.88, 0.8, 0.6)), (0.7, (0.7, 0.58, 0.38)),
                               (1.0, (0.85, 0.75, 0.55))], scale=1.0, distortion=3.0)

# ------------------------------------------------------------------ world: stars + faint nebula
world = bpy.data.worlds.new("Space")
SC.world = world
try:
    world.use_nodes = True
except Exception:
    pass
wt = world.node_tree
for n in list(wt.nodes):
    if n.type != "OUTPUT_WORLD":
        wt.nodes.remove(n)
wout = next(n for n in wt.nodes if n.type == "OUTPUT_WORLD")
tc = wt.nodes.new("ShaderNodeTexCoord")
vor = wt.nodes.new("ShaderNodeTexVoronoi")
vor.inputs["Scale"].default_value = 260
nt_ = wt
nt_.links.new(tc.outputs["Generated"], vor.inputs["Vector"])
star = ramp(wt, [(0.0, (1, 1, 1)), (0.06, (0, 0, 0))])
wt.links.new(vor.outputs["Distance"], star.inputs[0])
# vary brightness per star using voronoi cell colour
sepc = wt.nodes.new("ShaderNodeSeparateColor")
wt.links.new(vor.outputs["Color"], sepc.inputs[0])
pw = wt.nodes.new("ShaderNodeMath")
pw.operation = "POWER"
pw.inputs[1].default_value = 6.0
wt.links.new(sepc.outputs[0], pw.inputs[0])
mul = wt.nodes.new("ShaderNodeMix")
mul.data_type = "RGBA"
mul.blend_type = "MULTIPLY"
mul.inputs["Factor"].default_value = 1.0
wt.links.new(star.outputs[0], mul.inputs["A"])
wt.links.new(pw.outputs[0], mul.inputs["B"])
# second, denser and fainter star layer
vor2 = wt.nodes.new("ShaderNodeTexVoronoi")
vor2.inputs["Scale"].default_value = 700
wt.links.new(tc.outputs["Generated"], vor2.inputs["Vector"])
star2 = ramp(wt, [(0.0, (0.35, 0.38, 0.45)), (0.05, (0, 0, 0))])
wt.links.new(vor2.outputs["Distance"], star2.inputs[0])
neb_n = wt.nodes.new("ShaderNodeTexNoise")
neb_n.inputs["Scale"].default_value = 1.4
neb_n.inputs["Detail"].default_value = 8
wt.links.new(tc.outputs["Generated"], neb_n.inputs["Vector"])
neb = ramp(wt, [(0.45, (0.0, 0.0, 0.0)), (0.62, (0.012, 0.008, 0.03)), (0.75, (0.004, 0.015, 0.035))])
wt.links.new(neb_n.outputs["Fac"], neb.inputs[0])
a1 = wt.nodes.new("ShaderNodeMix")
a1.data_type = "RGBA"
a1.blend_type = "ADD"
a1.inputs["Factor"].default_value = 1.0
wt.links.new(mul.outputs["Result"], a1.inputs["A"])
wt.links.new(star2.outputs[0], a1.inputs["B"])
a2 = wt.nodes.new("ShaderNodeMix")
a2.data_type = "RGBA"
a2.blend_type = "ADD"
a2.inputs["Factor"].default_value = 1.0
wt.links.new(a1.outputs["Result"], a2.inputs["A"])
wt.links.new(neb.outputs[0], a2.inputs["B"])
bg = wt.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 3.0
wt.links.new(a2.outputs["Result"], bg.inputs["Color"])
wt.links.new(bg.outputs[0], wout.inputs["Surface"])

# ------------------------------------------------------------------ the Sun (shared by every set)
sun_d = bpy.data.lights.new("Sun", "SUN")
sun_d.energy = 4.5
sun_d.angle = math.radians(0.6)
sun = bpy.data.objects.new("Sun", sun_d)
SC.collection.objects.link(sun)
sun.rotation_euler = Vector((-1.0, 0.35, -0.25)).normalized().to_track_quat("-Z", "Y").to_euler()

# ------------------------------------------------------------------ reusable models (instanced)
MODELS = new_coll("Models (instanced)", in_scene=False)


def build_earth():
    col = new_coll("EarthModel", in_scene=False)
    e = assign(sphere("Earth.surface", 1.0, coll=col), EARTH_MAT)
    c = assign(sphere("Earth.clouds", 1.012, coll=col), CLOUD_MAT)
    a = assign(sphere("Earth.atmosphere", 1.06, coll=col), ATMO_MAT)
    # slow spin over the whole video (linear)
    def spin():
        for ob, rate in ((e, 1.0), (c, 1.25)):
            ob.rotation_euler = (0, 0, 0)
            ob.keyframe_insert("rotation_euler", index=2, frame=1)
            ob.rotation_euler = (0, 0, math.radians(40 * rate))
            ob.keyframe_insert("rotation_euler", index=2, frame=SC.frame_end)
    linear(spin)
    return col


def build_voyager():
    """Voyager-style probe from primitives. Dish faces +Z, ~3.7 units across."""
    col = new_coll("VoyagerModel", in_scene=False)
    # high-gain antenna: paraboloid bowl
    prof = [(r, r * r / (4 * 1.6)) for r in [i * 1.85 / 24 for i in range(25)]]
    dish = lathe("V.dish", prof, coll=col)
    sol = dish.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.04
    assign(dish, MAT["white"])
    rim = lathe("V.dishRim", [(1.85, prof[-1][1]), (1.87, prof[-1][1] - 0.04), (1.85, prof[-1][1] - 0.08)], coll=col)
    assign(rim, MAT["grey"])
    # feed + sub-reflector on struts
    assign(cyl("V.feed", 0.09, 0.5, loc=(0, 0, 0.35), coll=col), MAT["grey"])
    assign(cyl("V.subreflector", 0.28, 0.03, loc=(0, 0, 1.15), coll=col), MAT["white"])
    for k in range(3):
        a = 2 * math.pi * k / 3
        p0 = Vector((1.3 * math.cos(a), 1.3 * math.sin(a), 0.27))
        p1 = Vector((0.2 * math.cos(a), 0.2 * math.sin(a), 1.14))
        mid, d = (p0 + p1) / 2, p1 - p0
        s = cyl(f"V.strut{k}", 0.015, d.length, loc=mid, coll=col, verts=8)
        s.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        assign(s, MAT["grey"])
    # 10-sided bus wrapped in gold foil
    bus = cyl("V.bus", 0.95, 0.47, loc=(0, 0, -0.32), verts=10, coll=col)
    assign(bus, MAT["gold"])
    assign(cyl("V.busTop", 0.97, 0.04, loc=(0, 0, -0.07), verts=10, coll=col), MAT["dark"])
    # magnetometer boom (long, thin)
    assign(cyl("V.magBoom", 0.025, 9.0, loc=(-4.9, 0.6, -0.4), rot=(0, math.pi / 2, 0), verts=8, coll=col), MAT["grey"])
    assign(box("V.magSensor", (0.18, 0.12, 0.12), loc=(-9.4, 0.6, -0.4), coll=col), MAT["dark"])
    # RTG boom with three stacked generators + fins
    assign(cyl("V.rtgBoom", 0.04, 2.6, loc=(1.9, -1.0, -0.45), rot=(0, math.pi / 2, math.radians(-28)), verts=8, coll=col), MAT["grey"])
    for k in range(3):
        c = Vector((2.3 + 0.55 * k, -1.2 - 0.29 * k, -0.45))
        assign(cyl(f"V.rtg{k}", 0.2, 0.48, loc=c, rot=(0, math.pi / 2, math.radians(-28)), verts=16, coll=col), MAT["dark"])
        for j in range(6):
            a = j * math.pi / 3
            fin = box(f"V.rtg{k}.fin{j}", (0.44, 0.02, 0.18), coll=col)
            off = Euler((0, math.pi / 2, math.radians(-28))).to_matrix() @ Vector((0.28 * math.cos(a), 0.28 * math.sin(a), 0))
            fin.location = c + off
            fin.rotation_euler = (Euler((0, 0, math.radians(-28))).to_matrix() @ Euler((a, 0, 0)).to_matrix()).to_euler()
            assign(fin, MAT["dark"])
    # science boom + scan platform
    assign(cyl("V.sciBoom", 0.05, 2.4, loc=(0.4, 1.9, -0.5), rot=(math.pi / 2, 0, math.radians(15)), verts=8, coll=col), MAT["grey"])
    assign(box("V.scanPlatform", (0.6, 0.45, 0.4), loc=(0.75, 3.2, -0.5), coll=col), MAT["gold"])
    for k, dx in enumerate((-0.12, 0.14)):
        assign(cyl(f"V.camera{k}", 0.09, 0.5, loc=(0.75 + dx, 3.2, -0.15), coll=col, verts=16), MAT["dark"])
    # golden record on the bus side
    assign(cyl("V.record", 0.3, 0.02, loc=(0.97, 0, -0.32), rot=(0, math.pi / 2, 0), coll=col), MAT["gold"])
    return col


EARTH = build_earth()
VOYAGER = build_voyager()


# ------------------------------------------------------------------ cameras, cuts, labels
def camera(name, lens=35):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.05
    cd.clip_end = 6000
    cam = bpy.data.objects.new(name, cd)
    SC.collection.objects.link(cam)
    tgt = empty(name + ".target")
    con = cam.constraints.new("TRACK_TO")
    con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    return cam, tgt


def cut(line, cam):
    m = SC.timeline_markers.new(f"L{line.i + 1:02d}", frame=line.f0)
    m.camera = cam


def hud(cam, text, frame, f_end, y=0.35, size=0.075, mat="hud", x=0.0):
    """3D text pinned in front of a camera; pops in (scale overshoot) on `frame`."""
    cu = bpy.data.curves.new("HUD:" + text, "FONT")
    cu.body = text
    cu.font = FONT
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.size = size
    cu.extrude = 0.0
    cu.space_character = 1.08
    ob = bpy.data.objects.new("HUD:" + text, cu)
    SC.collection.objects.link(ob)
    ob.parent = cam
    ob.location = (x, y, -2.0)
    ob.data.materials.append(MAT[mat])
    ob.scale = (0, 0, 0)
    ob.keyframe_insert("scale", frame=frame - 1)
    ob.scale = (1.15,) * 3
    ob.keyframe_insert("scale", frame=frame + 3)
    ob.scale = (1,) * 3
    ob.keyframe_insert("scale", frame=frame + 6)
    show_only(ob, frame - 1, f_end)
    return ob


def sets_visible(objs, f0, f1):
    for ob in objs:
        show_only(ob, f0, f1)


def at(set_index, x=0, y=0, z=0):
    return Vector((set_index * SET_SPACING + x, y, z))


L = LINES

# ================================================================== L1  Earth, the date
# "On November eighteenth, a spacecraft launched in 1977 crosses a line ..."
l = L[0]
O = at(0)
e0 = instance(EARTH, "Earth.L1", O, scale=6.0)
cam, tgt = camera("CAM_L01_Earth", lens=40)
key(cam, "location", l.f0, O + Vector((13, -21, 5)))
key(cam, "location", l.f1, O + Vector((8.5, -15.5, 2.2)))
key(tgt, "location", l.f0, O + Vector((0, 0, 1.2)))
key(tgt, "location", l.f1, O + Vector((2.5, 0, 0)))
hud(cam, "NOV 18, 2026", l.w("November"), l.f1, y=0.42)
hud(cam, "LAUNCHED 1977", l.w("1977"), l.f1, y=0.3, size=0.05, mat="hud_gold")
hud(cam, "A LINE NO PROBE HAS CROSSED", l.w("crosses"), l.f1, y=-0.28, size=0.045)
sets_visible([e0], l.f0, l.f1)
cut(l, cam)

# ================================================================== L2  Voyager hero orbit
# "Voyager 1 will be one light-day from Earth."
l = L[1]
O = at(1)
v1 = instance(VOYAGER, "Voyager.L2", O, rot=(math.radians(-70), 0, math.radians(20)))
key(v1, "rotation_euler", l.f0, (math.radians(-70), 0, math.radians(20)))
key(v1, "rotation_euler", l.f1, (math.radians(-70), 0, math.radians(32)))
cam, tgt = camera("CAM_L02_Voyager", lens=32)
for k, frac in enumerate((0.0, 0.5, 1.0)):
    a = math.radians(-120 + 55 * frac)
    key(cam, "location", int(l.f0 + frac * (l.f1 - l.f0)), O + Vector((13 * math.cos(a), 13 * math.sin(a), 3.5 - 2 * frac)))
key(tgt, "location", l.f0, O + Vector((-1.5, 0, 0)))
key(tgt, "location", l.f1, O + Vector((-0.5, 0.5, 0)))
hud(cam, "VOYAGER 1", l.w("Voyager"), l.f1, y=0.42, size=0.06)
hud(cam, "1 LIGHT-DAY", l.w("light-day"), l.f1, y=0.3, size=0.1, mat="hud_gold")
sets_visible([v1], l.f0, l.f1)
cut(l, cam)

# ================================================================== the light-day line set (L3-L6)
O = at(2)
EARTH_P = O
VOY_P = O + Vector((100, 0, 0))
BEAM_SET = []
e_b = instance(EARTH, "Earth.beam", EARTH_P, scale=4.0)
v_b = instance(VOYAGER, "Voyager.beam", VOY_P, scale=1.2, rot=(0, math.radians(-90), 0))
halo_e = assign(sphere("Halo.Earth", 5.2, loc=EARTH_P, segs=48, rings=24), MAT["halo_blue"])
halo_v = assign(sphere("Halo.Voyager", 3.0, loc=VOY_P, segs=48, rings=24), MAT["halo_gold"])
beam = cyl("Beam", 0.06, 1.0, verts=16)
beam.data.transform(Matrix.Translation((0, 0, 0.5)))  # origin at the Earth end
beam.location = EARTH_P
beam.rotation_euler = (0, math.pi / 2, 0)
assign(beam, MAT["beam"])
BEAM_SET += [e_b, v_b, halo_e, halo_v, beam]
BEAM_LEN = (VOY_P - EARTH_P).length


def pulse(name, mat):
    p = sphere(name, 0.55, segs=32, rings=16)
    assign(p, MAT[mat])
    p.scale = (2.2, 1, 1)  # stretched along travel
    return p


# --- L3 "That's about twenty-six billion kilometers."  beam draws Earth -> Voyager
l = L[2]
key(beam, "scale", 1, (1, 1, 0.0001))
key(beam, "scale", l.w("twenty-six"), (1, 1, 0.0001))
key(beam, "scale", l.last, (1, 1, BEAM_LEN))
cam, tgt = camera("CAM_L03_Distance", lens=30)
mid = (EARTH_P + VOY_P) / 2
key(cam, "location", l.f0, mid + Vector((-6, -98, 22)))
key(cam, "location", l.f1, mid + Vector((4, -90, 16)))
key(tgt, "location", l.f0, mid + Vector((-4, 0, 0)))
key(tgt, "location", l.f1, mid + Vector((2, 0, 0)))
hud(cam, "EARTH", l.f0 + 4, l.f1, y=-0.12, x=-0.72, size=0.045)
hud(cam, "VOYAGER 1", l.f0 + 8, l.f1, y=-0.12, x=0.72, size=0.045, mat="hud_gold")
hud(cam, "≈ 25.9 BILLION KM", l.w("billion"), l.f1, y=0.36, size=0.09, mat="hud_gold")
cut(l, cam)
F_BEAM0 = l.f0

# --- L4 "Light, the fastest thing in the universe, needs a full day to get there."
l = L[3]
p_light = pulse("Pulse.light", "pulse_light")
cam, tgt = camera("CAM_L04_Light", lens=28)


def l4():
    for f, s in ((l.f0, 0.0), (l.last, 1.0)):
        pos = EARTH_P + Vector((4 + (BEAM_LEN - 8) * s, 0, 0))
        key(p_light, "location", f, pos)
        key(cam, "location", f, pos + Vector((-9, -7, 2.5)))
        key(tgt, "location", f, pos + Vector((3, 0, 0)))
    key(p_light, "location", l.f1, VOY_P + Vector((-4, 0, 0)))


linear(l4)
show_only(p_light, l.f0, l.f1)
hud(cam, "SPEED OF LIGHT", l.w("fastest"), l.f1, y=0.4, size=0.06)
hud(cam, "24 HOURS", l.w("day"), l.f1, y=0.28, size=0.1, mat="hud_gold")
cut(l, cam)

# --- L5 "So when engineers send a command, it takes a day to arrive..."
l = L[4]
p_cmd = pulse("Pulse.command", "pulse_cmd")
cam, tgt = camera("CAM_L05_Command", lens=30)
key(cam, "location", l.f0, EARTH_P + Vector((9, -22, 5)))
key(cam, "location", l.f1, EARTH_P + Vector((5, -19, 3)))
key(tgt, "location", l.f0, EARTH_P + Vector((2, 0, 0)))


def l5():
    key(p_cmd, "location", l.w("send"), EARTH_P + Vector((4.5, 0, 0)))
    key(p_cmd, "location", l.last, EARTH_P + Vector((60, 0, 0)))
    key(tgt, "location", l.w("send"), EARTH_P + Vector((4, 0, 0)))
    key(tgt, "location", l.f1, EARTH_P + Vector((40, 0, 0)))


linear(l5)
show_only(p_cmd, l.w("send"), l.f1)
hud(cam, "COMMAND SENT", l.w("command"), l.f1, y=0.4, size=0.06)
hud(cam, "+1 DAY", l.w("arrive"), l.f1, y=0.28, size=0.1, mat="hud_gold")
cut(l, cam)

# --- L6 "...and another day to hear back."   reply flies Voyager -> Earth
l = L[5]
p_rep = pulse("Pulse.reply", "pulse_reply")
cam, tgt = camera("CAM_L06_Reply", lens=30)
key(cam, "location", l.f0, VOY_P + Vector((9, -8, 3)))
key(cam, "location", l.f1, VOY_P + Vector((12, -6, 2)))


def l6():
    key(p_rep, "location", l.f0, VOY_P + Vector((-3, 0, 0)))
    key(p_rep, "location", l.f1, VOY_P + Vector((-70, 0, 0)))
    key(tgt, "location", l.f0, VOY_P + Vector((-3, 0, 0)))
    key(tgt, "location", l.f1, VOY_P + Vector((-40, 0, 0)))


linear(l6)
show_only(p_rep, l.f0, l.f1)
hud(cam, "REPLY", l.w("another"), l.f1, y=0.4, size=0.06)
hud(cam, "+2 DAYS", l.w("back"), l.f1, y=0.28, size=0.1, mat="hud_gold")
cut(l, cam)
sets_visible(BEAM_SET, F_BEAM0, L[5].f1)

# ================================================================== L7  Jupiter -> Saturn -> interstellar
# "Voyager flew past Jupiter and Saturn, then crossed into interstellar space in 2012."
l = L[6]
O = at(3)
v7 = instance(VOYAGER, "Voyager.flyby", O, scale=1.0, rot=(math.radians(-90), 0, 0))
jup = assign(sphere("Jupiter", 26, loc=O + Vector((-40, 60, -8))), JUPITER_MAT)
sat = assign(sphere("Saturn", 20, loc=O + Vector((36, 160, 6))), SATURN_MAT)
sat.rotation_euler = (math.radians(18), math.radians(-10), 0)
ring = lathe("Saturn.ring", [(26, 0), (47, 0)], segs=128)
ring.location = sat.location
ring.rotation_euler = sat.rotation_euler
assign(ring, ring_mat())
ring.scale = (1, 1, 1)
helio = sphere("Heliopause", 400, loc=O + Vector((0, 255 + 400, 0)), segs=128, rings=64)
assign(helio, heliopause_mat())
cam, tgt = camera("CAM_L07_Flyby", lens=26)
path = [(l.f0, 0), (l.w("Jupiter"), 60), (l.w("Saturn"), 160), (l.w("interstellar"), 245), (l.f1, 290)]


def l7():
    for f, y in path:
        key(v7, "location", f, O + Vector((0, y, 0)))
        key(cam, "location", f, O + Vector((7 - 0.02 * y, y - 15, 4.5)))
        key(tgt, "location", f, O + Vector((0, y + 4, 0)))


linear(l7)
hud(cam, "JUPITER · 1979", l.w("Jupiter"), l.w("Saturn") - 1, y=0.4, size=0.06)
hud(cam, "SATURN · 1980", l.w("Saturn"), l.w("crossed") - 1, y=0.4, size=0.06)
hud(cam, "INTERSTELLAR SPACE · 2012", l.w("crossed"), l.f1, y=0.4, size=0.06, mat="hud_gold")
sets_visible([v7, jup, sat, ring, helio], l.f0, l.f1)
cut(l, cam)

# ================================================================== L8  power fading, instruments off
# "Its nuclear power is fading, so instruments are being switched off, one by one."
l = L[7]
O = at(4)
rtg_glow_m, rtg_sock = keyable_emission("RTGGlow", (1.0, 0.25, 0.05), 3.0)
rtg = []
for k in range(3):
    c = O + Vector((-2.6, 0.2, -0.6 + 0.62 * k))
    body = assign(cyl(f"RTG{k}", 0.24, 0.55, loc=c, verts=24), MAT["dark"])
    core = assign(cyl(f"RTG{k}.core", 0.12, 0.57, loc=c, verts=16), rtg_glow_m)
    rtg += [body, core]
    for j in range(8):
        a = j * math.pi / 4
        fin = box(f"RTG{k}.fin{j}", (0.3, 0.025, 0.5), loc=c + Vector((0.36 * math.cos(a), 0.36 * math.sin(a), 0)), rot=(0, 0, a))
        rtg.append(assign(fin, MAT["dark"]))
panel = assign(box("InstrumentPanel", (3.6, 0.2, 1.0), loc=O + Vector((0.9, 0, 0))), MAT["panel"])
lights, socks = [], []
for k in range(5):
    m, s = keyable_emission(f"Status{k}", (0.2, 1.0, 0.45), 18.0)
    b = assign(box(f"Status{k}", (0.42, 0.12, 0.42), loc=O + Vector((-0.5 + 0.7 * k, -0.12, 0))), m)
    lights.append(b)
    socks.append(s)
key_socket(rtg_sock, l.f0, 6.0)
key_socket(rtg_sock, l.w("fading"), 2.0)
key_socket(rtg_sock, l.f1, 1.2)
off_words = [("switched", 0), ("off", 0), ("one", 0), ("by", 0)]  # the fifth light stays on
for s, (wd, n) in zip(socks, off_words):
    f = l.w(wd, n)
    key_socket(s, f, 18.0)
    key_socket(s, f + 2, 0.0)
area = bpy.data.lights.new("RTGKey", "AREA")
area.energy = 600
area.size = 4
area_ob = bpy.data.objects.new("RTGKey", area)
SC.collection.objects.link(area_ob)
area_ob.location = O + Vector((-3, -5, 4))
area_ob.rotation_euler = (Vector((0, 0, 0)) - Vector((-3, -5, 4))).to_track_quat("-Z", "Y").to_euler()
cam, tgt = camera("CAM_L08_Power", lens=40)
key(cam, "location", l.f0, O + Vector((-4.5, -6.5, 1.6)))
key(cam, "location", l.w("so"), O + Vector((-2.2, -7.5, 1.2)))
key(cam, "location", l.f1, O + Vector((0.4, -6.6, 0.8)))
key(tgt, "location", l.f0, O + Vector((-2.6, 0, 0)))
key(tgt, "location", l.w("so"), O + Vector((-0.6, 0, 0)))
key(tgt, "location", l.f1, O + Vector((1.0, 0, 0)))
hud(cam, "PLUTONIUM POWER ↓", l.w("power"), l.f1, y=0.42, size=0.06, mat="hud_gold")
hud(cam, "INSTRUMENTS", l.w("instruments"), l.f1, y=0.3, size=0.05)
sets_visible(rtg + [panel, area_ob] + lights, l.f0, l.f1)
cut(l, cam)

# ================================================================== L9  the Golden Record
# "It still carries a golden record of sounds and music from Earth."
l = L[8]
O = at(5)
rec = assign(cyl("GoldenRecord", 1.6, 0.03, loc=O, verts=128), record_mat())
lab = assign(cyl("GoldenRecord.label", 0.45, 0.034, loc=O, verts=64), MAT["label"])
hole = assign(cyl("GoldenRecord.hole", 0.04, 0.04, loc=O, verts=16), MAT["dark"])
for ob in (rec, lab, hole):
    ob.rotation_euler = (math.radians(70), 0, 0)
spin = empty("GoldenRecord.spin", O)
for ob in (rec, lab, hole):
    ob.parent = spin
    ob.location = (0, 0, 0)
linear(lambda: (key(spin, "rotation_euler", l.f0, (0, math.radians(-12), 0)),
                key(spin, "rotation_euler", l.f1, (0, math.radians(14), 0))))
sweep_d = bpy.data.lights.new("RecordSweep", "AREA")
sweep_d.energy = 120
sweep_d.size = 1.5
sweep = bpy.data.objects.new("RecordSweep", sweep_d)
SC.collection.objects.link(sweep)
for f, x in ((l.f0, -5), (l.w("music"), 0.5), (l.f1, 5)):
    key(sweep, "location", f, O + Vector((x, -4, 3)))
    sweep.rotation_euler = (O - sweep.location).to_track_quat("-Z", "Y").to_euler()
    sweep.keyframe_insert("rotation_euler", frame=f)
cam, tgt = camera("CAM_L09_Record", lens=50)
key(cam, "location", l.f0, O + Vector((1.8, -6.5, 0.9)))
key(cam, "location", l.f1, O + Vector((-0.6, -4.6, 0.3)))
key(tgt, "location", l.f0, O + Vector((0.2, 0, 0)))
key(tgt, "location", l.f1, O + Vector((-0.1, 0, 0)))
hud(cam, "THE GOLDEN RECORD", l.w("golden"), l.f1, y=0.42, size=0.06, mat="hud_gold")
hud(cam, "SOUNDS · MUSIC · GREETINGS", l.w("sounds"), l.f1, y=0.32, size=0.04)
sets_visible([rec, lab, hole, sweep], l.f0, l.f1)
cut(l, cam)

# ================================================================== L10  pull back: still talking
# "Forty-nine years, one light-day, and it's still talking to us."
l = L[9]
O = at(6)
v10 = instance(VOYAGER, "Voyager.final", O, rot=(0, math.radians(-90), 0))
dot = assign(sphere("PaleBlueDot", 0.35, loc=O + Vector((-160, 30, 8)), segs=16, rings=8), MAT["dot"])
cam, tgt = camera("CAM_L10_Pullback", lens=35)
key(cam, "location", l.f0, O + Vector((7, -3, 1.5)))
key(cam, "location", l.w("still"), O + Vector((24, -14, 6)))
key(cam, "location", l.f1, O + Vector((40, -20, 9)))
key(tgt, "location", l.f0, O + Vector((-3, 2, 0)))
key(tgt, "location", l.f1, O + Vector((-60, 12, 3)))
hud(cam, "49 YEARS", l.w("Forty-nine"), l.f1, y=0.42, size=0.06)
hud(cam, "1 LIGHT-DAY FROM HOME", l.w("light-day"), l.f1, y=0.3, size=0.08, mat="hud_gold")
sets_visible([v10, dot], l.f0, l.f1)
cut(l, cam)

SC.camera = bpy.data.objects["CAM_L01_Earth"]

# ------------------------------------------------------------------ EEVEE render settings
SC.render.engine = "BLENDER_EEVEE"
SC.eevee.taa_render_samples = 8
SC.eevee.shadow_resolution_scale = 0.25
SC.eevee.shadow_ray_count = 1
SC.eevee.shadow_step_count = 1
SC.eevee.use_shadows = True
SC.eevee.use_raytracing = False
SC.render.film_transparent = False
SC.view_settings.view_transform = "AgX"
try:
    SC.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
SC.render.use_motion_blur = False
SC.render.motion_blur_shutter = 0.5

# bloom-style glow in the compositor (Glare node, Fog Glow)
try:
    ng = bpy.data.node_groups.new("Glow", "CompositorNodeTree")
    SC.compositing_node_group = ng
    rl = ng.nodes.new("CompositorNodeRLayers")
    gl = ng.nodes.new("CompositorNodeGlare")
    for attr, val in (("glare_type", "FOG_GLOW"), ("quality", "MEDIUM")):
        if hasattr(gl, attr):
            setattr(gl, attr, val)
    for name, val in (("Type", "Fog Glow"), ("Quality", "Medium"), ("Threshold", 1.0),
                      ("Strength", 0.6), ("Size", 0.6)):
        if name in gl.inputs:
            try:
                gl.inputs[name].default_value = val
            except Exception:
                pass
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    go = ng.nodes.new("NodeGroupOutput")
    ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
    ng.links.new(gl.outputs["Image"], go.inputs[0])
    SC.render.use_compositing = True
except Exception as ex:  # glow is a nicety; never block the build on API drift
    print("compositor glow skipped:", ex)


# ------------------------------------------------------------------ captions + edit scene
def caption_chunks(max_words=3):
    """Group words into short caption chunks; break on punctuation and at max_words."""
    out = []
    for seg in TRANSCRIPT:
        cur = []
        for w in seg["words"]:
            cur.append(w)
            if len(cur) >= max_words or re.search(r"[,.!?]$", w["w"].strip()):
                out.append(cur)
                cur = []
        if cur:
            out.append(cur)
    return out


KEY_TERMS = re.compile(r"\d|light-day|billion|golden|interstellar", re.I)


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


chunks = caption_chunks()
with open(os.path.join(HERE, "captions_en.srt"), "w") as fh:
    for i, ch in enumerate(chunks):
        t0 = ch[0]["s"]
        t1 = chunks[i + 1][0]["s"] if i + 1 < len(chunks) else ch[-1]["e"] + 0.6
        t1 = min(t1, ch[-1]["e"] + 0.6)
        fh.write(f"{i + 1}\n{srt_time(t0)} --> {srt_time(t1)}\n"
                 + " ".join(w["w"].strip() for w in ch) + "\n\n")

ED = bpy.data.scenes.new("Edit")
ED.render.fps = FPS
ED.frame_start, ED.frame_end = 1, SC.frame_end
ED.render.resolution_x, ED.render.resolution_y = RES
ED.render.resolution_percentage = 100
ED.view_settings.view_transform = "Standard"
seq = ED.sequence_editor_create()
shots = seq.strips.new_scene("Shots", SC, channel=1, frame_start=1)
voice = seq.strips.new_sound("Voiceover", os.path.join(HERE, "voice.wav"), channel=2, frame_start=1)
cap_font = bpy.data.fonts.load(FONT_BOLD)
cap_font.pack()
for i, ch in enumerate(chunks):
    f0 = F(ch[0]["s"])
    nxt = F(chunks[i + 1][0]["s"]) if i + 1 < len(chunks) else F(ch[-1]["e"] + 0.6)
    f1 = min(nxt, F(ch[-1]["e"] + 0.6))
    text = " ".join(w["w"].strip() for w in ch).upper()
    st = seq.strips.new_effect(name=f"CAP{i:03d}", type="TEXT", channel=3 + (i % 2),
                               frame_start=f0, length=max(2, f1 - f0))
    st.text = text
    st.font = cap_font
    st.font_size = 74
    st.color = (1.0, 0.82, 0.3, 1) if KEY_TERMS.search(text) else (1, 1, 1, 1)
    st.use_outline = True
    st.outline_color = (0, 0, 0, 1)
    st.outline_width = 0.25
    st.use_shadow = True
    st.shadow_color = (0, 0, 0, 0.7)
    st.shadow_blur = 0.4
    st.location = (0.5, 0.11)
    st.alignment_x = "CENTER"
    st.anchor_x = "CENTER"
    st.anchor_y = "BOTTOM"
    st.wrap_width = 0.9

if hasattr(ED.render.image_settings, "media_type"):
    ED.render.image_settings.media_type = "VIDEO"
ED.render.image_settings.file_format = "FFMPEG"
ED.render.ffmpeg.format = "MPEG4"
ED.render.ffmpeg.codec = "H264"
ED.render.ffmpeg.constant_rate_factor = "HIGH"
ED.render.ffmpeg.audio_codec = "AAC"
ED.render.ffmpeg.audio_bitrate = 192
ED.render.filepath = os.path.join(HERE, "voyager_news.mp4")
for win in bpy.context.window_manager.windows:
    win.scene = ED

out = os.path.join(HERE, "voyager_news.blend")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print(f"saved {out}: {SC.frame_end} frames, {len(SC.timeline_markers)} camera cuts, {len(chunks)} captions")
