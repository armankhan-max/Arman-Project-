#!/bin/bash
# Render 3 preview frames per shot and stitch them: tools/preview_all.sh A B C ...
cd "$(dirname "$0")/.."
for s in "$@"; do
  rm -f work/prev/${s}_*.jpg
  /opt/bpyenv/bin/python blender/coinstory/shots.py $s --preview > work/prev_$s.log 2>&1
  if ls work/prev/${s}_*.jpg >/dev/null 2>&1; then
    ffmpeg -v error -y -pattern_type glob -i "work/prev/${s}_*.jpg" -filter_complex "tile=3x1" -frames:v 1 work/prev/sheet_$s.jpg
    echo "$s ok"
  else
    echo "$s FAIL: $(grep -E 'Error|error:' work/prev_$s.log | tail -3)"; grep -B2 -A12 Traceback work/prev_$s.log | tail -16
  fi
done
