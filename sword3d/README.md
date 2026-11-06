# The Indestructible Sword — 2D characters in a 3D world

Vertical 1080×1920, 30 fps short. A flat 2D stick-figure hero (canvas-drawn, billboarded) lives inside a
toon-shaded 3D world (three.js, outlines via OutlineEffect), timed word-by-word to `voiceover.mp3`.

Output: `indestructible_sword_2d3d.mp4`

## Pipeline
1. `words.json` — script read from the reference video's captions, force-aligned to the voiceover (pocketsphinx).
2. `main.js` — the whole film as a function of time: 3D road world, car, sword, hero tree, shockwave,
   mushroom cloud, reality-void; 2D character with expressions (happy, determined, shock, strain, smug, scared);
   overlay FX (captions, reticle, force arrows, rewind, lightning, glitch, cracks).
3. `render.js` — headless Chromium (SwiftShader WebGL) renders every frame to JPEG.
4. `audio.py` — synthesized BGM cues + SFX (reuses `../video/audio.py`), ducked under the voice.

## Re-render
```
npm i
node render.js --out frames --workers 4 --dur 40.4
python audio.py --voice voiceover.mp3 --out mix.wav
ffmpeg -framerate 30 -i frames/f%05d.jpg -i mix.wav -af loudnorm=I=-14:TP=-1.5 -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest indestructible_sword_2d3d.mp4
```
