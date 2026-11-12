#!/bin/bash
# Render transition handles, build per-shot clips, sound track and the final video.
cd "$(dirname "$0")/.."
SHOTS="A B C D E1 E2 F G1 G2 S T"
H=6
for s in $SHOTS; do
  /opt/bpyenv/bin/python blender/coinstory/shots.py $s --handles $H > work/handles_$s.log 2>&1
done
mkdir -p public/shots out final
rm -f public/shots/*.mp4
for s in $SHOTS; do
  list=work/list_$s.txt
  for f in work/handles/$s/pre_*.jpg work/frames/$s/*.jpg work/handles/$s/post_*.jpg; do
    echo "file '$PWD/$f'"; echo "duration 0.0416667"
  done > $list
  ffmpeg -v error -y -f concat -safe 0 -r 24 -i $list -vf "scale=720:1280:flags=lanczos" -r 24 -c:v libx264 -crf 14 -g 12 -pix_fmt yuv420p public/shots/$s.mp4
done
python3 tools/make_shots_json.py $H
/opt/bpyenv/bin/python tools/make_sfx.py
[ -f public/audio/vo_loud.m4a ] || ffmpeg -v error -y -i public/audio/vo.mp3 -af "loudnorm=I=-12:TP=-1.0:LRA=9" -ar 44100 -c:a aac -b:a 192k public/audio/vo_loud.m4a
[ "$1" = "noremotion" ] && exit 0
npx remotion render CoinStory out/coins-for-the-dead.mp4 --crf 17
ffmpeg -v error -y -i out/coins-for-the-dead.mp4 -c:v libx264 -crf 20 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart final/coins-for-the-dead.mp4
echo ASSEMBLE_DONE
