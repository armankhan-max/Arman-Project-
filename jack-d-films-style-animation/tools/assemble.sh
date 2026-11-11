#!/bin/bash
# Join rendered shot frames into public/shots/base.mp4 (upscaled to 1080x1920), then render the final video.
cd "$(dirname "$0")/.."
rm -f work/list.txt
for s in A B C D E1 E2 F G1 G2 H I J K1 K2 L M1 M2; do
  for f in work/frames/$s/*.jpg; do echo "file '$PWD/$f'" >> work/list.txt; echo "duration 0.0416667" >> work/list.txt; done
done
ffmpeg -v error -y -f concat -safe 0 -r 24 -i work/list.txt -vf "scale=1080:1920:flags=lanczos,unsharp=5:5:0.7" -r 24 -c:v libx264 -crf 14 -pix_fmt yuv420p public/shots/base.mp4
[ "$1" = "base" ] || npx remotion render CoinStory out/coins-for-the-dead.mp4 --crf 18
