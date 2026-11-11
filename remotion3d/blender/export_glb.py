"""Shared helpers for building models in Blender and exporting them to Remotion.

Run any build script headless:
    blender -b --python blender/<script>.py
or export an existing .blend:
    blender -b file.blend --python blender/export_glb.py -- public/models/name.glb
"""
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "public", "models")


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name, rgb, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def export_glb(path):
    """Export the whole scene (meshes, materials, armatures, animations) as GLB."""
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        export_apply=True,
        export_animations=True,
        export_yup=True,
    )
    print("EXPORTED", path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    export_glb(args[0] if args else os.path.join(MODELS, "export.glb"))
