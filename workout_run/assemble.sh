#!/bin/sh
# Concatenate rendered chunks, add the soundtrack (loudness-normalised) and write the final video.
set -e
cd "$(dirname "$0")/out"
ls chunks/c*.mp4 | sort | sed "s#^#file '#; s#\$#'#" > chunks.txt
ffmpeg -v error -y -f concat -safe 0 -i chunks.txt -i soundtrack.wav \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -tune animation \
  -c:a aac -b:a 256k -af "loudnorm=I=-14:TP=-1.0:LRA=11" -movflags +faststart -shortest pov_cardio_run_16min.mp4
ls -la pov_cardio_run_16min.mp4
