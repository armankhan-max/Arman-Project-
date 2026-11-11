"""Connection test: build a model in Blender, export GLB for the Remotion scene."""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_glb import MODELS, export_glb, material, reset_scene

reset_scene()
bpy.ops.mesh.primitive_monkey_add(size=2)
head = bpy.context.active_object
head.name = "Suzanne"
mod = head.modifiers.new("Subdiv", "SUBSURF")
mod.levels = 2
bpy.ops.object.shade_smooth()
head.data.materials.append(material("Skin", (0.95, 0.35, 0.2), roughness=0.45))

export_glb(os.path.join(MODELS, "blender-test.glb"))
