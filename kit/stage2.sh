#!/bin/bash
# Stage 2: (after fix_voice.py and writing video.json) -> plan, footage, render, phone file.
set -e
K=$(cd "$(dirname "$0")" && pwd)/scripts
python3 $K/assets.py voice.wav | tail -1                       # waveform levels
for i in 1 2 3; do python3 $K/plan.py | tail -1; python3 $K/download.py | grep -c FAILED || true; done
python3 $K/plan.py | tail -1
python3 $K/bg.py | tail -1                                      # ~12 min
python3 $K/render.py --bg bg.mp4 --voice voice.wav --out final_hd.mp4 --jobs 4 | tail -1   # ~25 min
# phone-friendly single file (<100 MB; big files failed to download on the user's phone)
ffmpeg -v error -y -i final_hd.mp4 -vf scale=854:480 -c:v libx264 -preset slow -profile:v main -level 3.1 \
  -pix_fmt yuv420p -b:v 260k -maxrate 420k -bufsize 800k -g 60 -c:a aac -b:a 64k -ac 1 -ar 44100 \
  -movflags +faststart Final_Video.mp4
ffmpeg -v error -i Final_Video.mp4 -f null - && echo DECODE_OK
python3 -c "
import json; u=set(open('$K/../data/used_clips.txt').read().split())
u|={str(s['clip']) for s in json.load(open('plan.json'))['scenes']}
open('$K/../data/used_clips.txt','w').write('\n'.join(sorted(u))+'\n')"
ls -la Final_Video.mp4
