"""Load extra MakeHuman asset packs into MPFB: install_packs.py <pack.zip> [...]"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mpfb import enable_mpfb

enable_mpfb()
for z in sys.argv[1:]:
    if z.endswith(".zip"):
        try:
            print("PACK", os.path.basename(z), bpy.ops.mpfb.load_pack(filepath=z))
        except Exception as e:
            print("PACK_FAIL", z, e)
bpy.ops.wm.save_userpref()
