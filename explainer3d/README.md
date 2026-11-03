# 5,000 Steps — 3D explainer (2D-face toon characters in a 3D world)

- Output: `five_thousand_steps.mp4` — 1600×900, 30 fps, 4:11, voice + original music + SFX (−14 LUFS)
- `captions_en.srt` — optional subtitles (not burned in; on-screen text kept minimal on purpose)

## How it works
- `transcribe.py` — Whisper (small) word timestamps → `transcript.json`
- `web/js/core.js` — Three.js renderer + post: bloom, depth of field, camera motion blur, zoom/whip blur, ACES grade, grain
- `web/js/character.js` — toon character: 3D body, hand-drawn 2D face on a canvas texture, walk cycle
- `web/js/organs.js` — heart, brain, lungs (+bronchial tree), liver, pancreas, stomach, intestines, knee, cells
- `web/js/envs.js`, `web/js/sets.js` — town, living room, organ city, body interiors, infographic stage, x-ray character
- `web/js/timeline.js` — the edit: 76 shots on exact voiceover times (slow-mo / speed ramps / transitions)
- `web/render.js` — headless Chromium renders frames in parallel → ffmpeg
- `audio3d.py` — music cues + timed SFX, ducked under the voice

## Re-render
```bash
npm i && python3 -m http.server 8765 --bind 127.0.0.1 &
node web/stills.js out_dir 12.5 52 98.6            # preview single frames
node web/render.js video.mp4 4                       # full render (4 workers)
python3 audio3d.py --voice voice.mp3 --out mix.wav
ffmpeg -i video.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -af loudnorm=I=-14:TP=-1 -c:a aac -b:a 192k five_thousand_steps.mp4
```
