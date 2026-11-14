#!/bin/bash
# Joins parts 1-3 (animation runs) with the fast edit of the rest and puts the full voiceover on top.
set -e
G=/home/user/Arman-Project-/gta-tatiana; P=$G/voice-video/parts; F=$G/fast; O=$G/output
mkdir -p $O
ffmpeg -v error -y -i $P/part01/run/broll.mp4 -i $P/part02/run/broll.mp4 -i $P/part03/run/broll.mp4 -i $F/rest.mp4 \
  -f lavfi -t 900 -i anullsrc=r=48000:cl=stereo \
  -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a][3:v][4:a]concat=n=4:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset veryfast -crf 19 -pix_fmt yuv420p -c:a aac -b:a 192k $O/B-ROLL-no-voice.mp4
VD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $G/voice-video/voiceover.wav)
ffmpeg -v error -y -i $O/B-ROLL-no-voice.mp4 -i $G/voice-video/voiceover.wav \
  -filter_complex "[0:a]volume=0.6[s];[1:a]volume=1.0[vo];[vo][s]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" \
  -map 0:v -map "[a]" -t $VD -c:v copy -c:a aac -b:a 192k -movflags +faststart $O/FINAL-with-voice.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 $O/FINAL-with-voice.mp4
