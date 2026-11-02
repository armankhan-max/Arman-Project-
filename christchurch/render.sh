#!/usr/bin/env bash
# Full pipeline: narration -> plates -> edit events -> sound mix -> video parts -> final mux.
set -euo pipefail
cd "$(dirname "$0")"
PARTS=${PARTS:-4}
[ -f voice_raw.wav ] || python3 tts.py                      # Kokoro TTS, am_michael
python3 plates.py --all --skip-existing                     # Blender/Cycles B-roll plates
python3 comp.py --events                                    # resolve EDL against word timings
python3 sound.py                                            # score + SFX + ambience + voice -> build/mix.wav
python3 captions.py                                         # captions_en.srt
for i in $(seq 0 $((PARTS-1))); do python3 comp.py --part "$i" --parts "$PARTS" & done; wait
: > build/parts.txt
for i in $(seq 0 $((PARTS-1))); do echo "file 'part$i.mp4'" >> build/parts.txt; done
ffmpeg -y -v error -f concat -safe 0 -i build/parts.txt -i build/mix.wav -map 0:v -map 1:a -c:v copy \
       -c:a aac -b:a 256k -shortest -movflags +faststart build/christchurch_FULL.mp4
echo "done: build/christchurch_FULL.mp4"
