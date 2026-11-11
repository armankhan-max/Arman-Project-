"""Setup check: build a skinned, dressed, rigged MPFB human and render it with Cycles."""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mpfb import enable_mpfb

enable_mpfb()
from bl_ext.user_default.mpfb.services import LocationService

data = LocationService.get_user_data()
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)

bpy.ops.mpfb.create_human()
human = bpy.context.active_object


def asset(kind, name, ext):
    return os.path.join(data, kind, name, name + ext)


def step(label, fn):
    bpy.context.view_layer.objects.active = human
    human.select_set(True)
    try:
        print("STEP", label, fn())
    except Exception as e:  # keep going so one missing asset doesn't hide the rest
        print("STEP_FAIL", label, e)


step("skin", lambda: bpy.ops.mpfb.load_library_skin(filepath=asset("skins", "young_caucasian_male", ".mhmat")))
step("rig", lambda: bpy.ops.mpfb.add_standard_rig())
for kind, name, ext in [("clothes", "male_casualsuit01", ".mhclo"), ("clothes", "shoes01", ".mhclo"),
                        ("hair", "short02", ".mhclo"), ("eyes", "high-poly", ".mhclo"),
                        ("eyebrows", "eyebrow001", ".mhclo"), ("eyelashes", "eyelashes01", ".mhclo")]:
    step(name, lambda k=kind, n=name, e=ext: bpy.ops.mpfb.load_library_clothes(filepath=asset(k, n, e)))

print("OBJS", [(o.name, o.type) for o in bpy.data.objects])

s = bpy.context.scene
world = bpy.data.worlds.new("W"); s.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.25, 0.6, 0.85, 1)
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), 0, math.radians(30)))
bpy.context.object.data.energy = 4
bpy.ops.object.camera_add(location=(0, -3.2, 1.25), rotation=(math.radians(88), 0, 0))
s.camera = bpy.context.object
s.render.engine = "CYCLES"
s.cycles.samples = 48
s.cycles.use_denoising = True
s.render.resolution_x, s.render.resolution_y = 540, 960
s.render.filepath = sys.argv[-1]
bpy.ops.render.render(write_still=True)
print("RENDERED")
