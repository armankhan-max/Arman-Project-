"""Enable the MPFB human generator inside the bpy module (run with /opt/bpyenv/bin/python)."""
import addon_utils
import bpy

MODULE = "bl_ext.user_default.mpfb"


def enable_mpfb():
    # MPFB reads its preferences during register(), so the entry must exist first.
    if MODULE not in bpy.context.preferences.addons:
        bpy.context.preferences.addons.new().module = MODULE
    addon_utils.enable(MODULE, handle_error=None)
