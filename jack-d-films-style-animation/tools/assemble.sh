#!/bin/bash
# Render transition handles, build per-shot clips, sound track and the final video.
cd "$(dirname "$0")/.."
SHOTS="A B C D E1 E2 F G1 G2 H I J K1 K2 L M1 M2"
H=6
for s in $SHOTS; do
  /opt/bpyenv/bin/python blender/coinstory/shots.py $s --handles $H > work/handles_$s.log 2>&1
done
mkdir -p public/shots out
for s in $SHOTS; do
  list=work/list_$s.txt
  for f in work/handles/$s/pre_*.jpg work/frames/$s/*.jpg work/handles/$s/post_*.jpg; do
    echo "file '$PWD/$f'"; echo "duration 0.0416667"
  done > $list
  ffmpeg -v error -y -f concat -safe 0 -r 24 -i $list -r 24 -c:v libx264 -crf 14 -g 12 -pix_fmt yuv420p public/shots/$s.mp4
done
python3 tools/make_shots_json.py $H
/opt/bpyenv/bin/python tools/make_sfx.py
[ "$1" = "noremotion" ] || npx remotion render CoinStory out/coins-for-the-dead.mp4 --crf 17
