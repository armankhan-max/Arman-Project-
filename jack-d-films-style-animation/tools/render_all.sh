#!/bin/bash
# Render every shot's frames (resumable: existing frames are skipped).
cd "$(dirname "$0")/.."
for s in ${@:-A B C D E1 E2 F G1 G2 H I J K1 K2 L M1 M2}; do
  /opt/bpyenv/bin/python blender/coinstory/shots.py $s > work/render_$s.log 2>&1
  echo "$s $(ls work/frames/$s 2>/dev/null | wc -l) $(date +%H:%M:%S)" >> work/render_progress.txt
done
echo ALL_DONE >> work/render_progress.txt
