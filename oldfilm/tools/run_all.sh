set -e
cd /home/user/Arman-Project-/oldfilm
python3 tools/build_edl.py
rm -rf render_parts && python3 tools/render.py plan/edl.json render_parts --jobs 4
cd render_parts && ffmpeg -loglevel error -y -f concat -safe 0 -i list.txt -c copy video_only.mp4 && cd ..
ffmpeg -loglevel error -y -i render_parts/video_only.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart the_giant_of_the_skerry_1951_FULL.mp4
python3 tools/credits.py
ffprobe -v error -show_entries format=duration -of csv=p=0 the_giant_of_the_skerry_1951_FULL.mp4
