#!/bin/bash
# Render all shots with two parallel workers (540x960, upscaled at encode time).
cd "$(dirname "$0")"
export RES_X=${RES_X:-540} RES_Y=${RES_Y:-960} SAMPLES=${SAMPLES:-10} THREADS=${THREADS:-2}
w(){ for s in "$@"; do python3 run_shot.py $s > logs/$s.log 2>&1; echo "done $s"; done; }
mkdir -p logs
w s10 s01 s04 s06 s03 &
w s02 s09 s07 s08 s05 &
wait
echo ALL DONE
