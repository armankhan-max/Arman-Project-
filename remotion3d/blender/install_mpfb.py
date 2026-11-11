"""Install the MPFB extension zip and an asset pack: install_mpfb.py <mpfb.zip> <pack.zip>"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mpfb import enable_mpfb

addon_zip, pack_zip = sys.argv[-2], sys.argv[-1]
bpy.ops.extensions.package_install_files(filepath=addon_zip, repo="user_default", enable_on_install=False)
enable_mpfb()
bpy.ops.mpfb.load_pack(filepath=pack_zip)
bpy.ops.wm.save_userpref()
print("MPFB_READY")
