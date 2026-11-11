# Jack D Films style animation

Toolkit for 9:16 3D explainer shorts in the style of the reference videos.

## Tools
- **Blender 5.3 (`/opt/bpyenv/bin/python`, `import bpy`)** – modelling, rigging, Cycles renders (denoiser on).
- **Blender 4.0 CLI (`blender -b`)** – fallback; Cycles works only with denoising off.
- **MPFB** – realistic rigged humans (skins, clothes, hair). `from mpfb import enable_mpfb` first. See `blender/human_test.py`.
- **Remotion + Three.js** (`@remotion/three`, r3f, drei, postprocessing) – compositing, captions, audio, final mp4.
- **edge-tts** – voiceover: `SSL_CERT_FILE=/root/.ccr/ca-bundle.crt /opt/bpyenv/bin/edge-tts --proxy "$HTTPS_PROXY" ...`
- **Poly Haven** (api.polyhaven.com / dl.polyhaven.org) – HDRIs, textures.
- Fresh machine: `bash tools/setup.sh`.

## Pipeline
1. Blender script builds scene → renders frames with Cycles (or exports GLB to `public/models/`).
2. Remotion composition plays the frames/GLB, adds captions + audio.
3. `npx remotion render <Id> out/<name>.mp4`

## Style (from 4 reference shorts)
- 1080x1920, 30 fps, ~26–31 s, one idea per video.
- Almost no hard cuts: one continuous camera that flies, orbits, pushes in and whips between subjects; wide-angle lens, close to the subject, POV and low/overhead angles, light motion blur.
- Realistic 3D humans / detailed macro objects, glossy materials, strong saturated colours, clean simple backgrounds (flat sky gradient or lit environment), soft shadows.
- Cutaway/inside views for explanations (skin layers, eye, brain), exaggerated scale.
- Captions: white bold rounded sans (Montserrat/Poppins-like), lowercase-ish, 2–3 words at a time synced to voice, thin dark outline + soft shadow, centred at ~78% height.
- Channel name appears inside the scene (on a shirt / object), not as an overlay.
- Ends on a clear payoff shot.
