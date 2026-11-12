#!/bin/bash
# Build scene with either a Blender binary or the pip bpy module.
# usage: run_build.sh OUTDIR [--preview] [--eevee]
OUT=$1; shift
if [ -n "$BPY_PYTHON" ]; then "$BPY_PYTHON" -u "$(dirname "$0")/teddy_slice.py" -- --out "$OUT" "$@"
else blender -b --factory-startup -P "$(dirname "$0")/teddy_slice.py" -- --out "$OUT" "$@"; fi
