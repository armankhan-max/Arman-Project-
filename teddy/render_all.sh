#!/bin/bash
# Full pipeline: build -> render all frames (resume-safe) -> sound + overlay + MP4.
# usage: render_all.sh OUTDIR [WxH] [samples]
set -e
OUT=$1; RES=${2:-720x1280}; SPP=${3:-14}
PY=${BPY_PYTHON:-/opt/bpyenv/bin/python}
cd "$(dirname "$0")"
[ -f "$OUT/scene.blend" ] || BPY_PYTHON=$PY ./run_build.sh "$OUT" > "$OUT.build.log" 2>&1
for try in 1 2 3; do
  $PY -u render_frames.py "$OUT" --res "$RES" --samples "$SPP" 2>&1 | grep --line-buffered "\[render\]" >> "$OUT.render.log" || true
  [ "$(ls "$OUT"/frames/*.png 2>/dev/null | wc -l)" -ge "$(python3 -c "import json;print(json.load(open('$OUT/timeline.json'))['frames'])")" ] && break
done
python3 post.py "$OUT" >> "$OUT.render.log" 2>&1
echo DONE >> "$OUT.render.log"
