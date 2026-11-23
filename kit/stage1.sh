#!/bin/bash
# Stage 1: voice -> cleaned + de-"dot"ted voice.wav, transcript, levels.
# usage (inside a new work folder):  bash ../kit/stage1.sh /path/to/voice.mp3
set -e
K=$(cd "$(dirname "$0")" && pwd)/scripts
cp "$1" voice_raw.mp3
python3 $K/clean_voice.py voice_raw.mp3 voice_clean.wav 2>&1 | grep -v INFO | tail -1      # echo/noise removal
ffmpeg -v error -y -i voice_clean.wav -ar 16000 -ac 1 clean16k.wav
python3 $K/transcribe.py clean16k.wav transcript.json > transcribe.log 2>&1                  # ~15-20 min
for k in 0 1 2 3; do python3 $K/dotscan2.py $k 4 > dscan_$k.log 2>&1 & done; wait            # spoken "dot" hunt
python3 $K/build_dots.py | tail -1
python3 -c "
import json
T=json.load(open('transcript.json')); b={}
for s in T['segments']: b.setdefault(int(s['start']//45),[]).append(s['text'].strip())
open('transcript.txt','w').write('\n'.join(f'[{k*45}s] '+' '.join(v) for k,v in sorted(b.items())))"
echo "STAGE1 DONE -> review dot_list.json + transcript.txt (repeats / wrong order), then run fix_voice.py"
