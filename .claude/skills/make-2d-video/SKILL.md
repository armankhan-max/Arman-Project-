---
name: make-2d-video
description: Build a professional 2D animated explainer video from a voiceover (mp3), in the saved house style (flat vector, teal infographic boards + golden-hour illustrated sets, cartoon characters with skin-tone faces, code-painted human portraits, animated text, real recorded SFX, real-piano score). Use whenever the user asks for a 2D animation, explainer video, or /make-2d-video.
---

# make-2d-video: house style (approved by the user, reuse every time)

The user loved the result of `andrew/` ("Who can afford a $500K house?"). Any new
2D / explainer request must look and feel like it. Do not ask style questions; just build it.
The user writes Hinglish and wants **minimal chat text, just working code and the video**.

## Start from the template
Copy `andrew/` to a new folder (e.g. `<topic>/`) and keep: `kit.py` (palette, boards, sets, characters,
portraits, props), `scenes.py` (shot list pattern), `audio.py`, `render.py`, `transcribe.py`, `sfx/`.
Rewrite `scenes.py` for the new script; extend `kit.py` with new props. Reuse everything else.

## Visual rules
- Two worlds, cut between them: **infographic boards** (deep teal gradient, dot grid, thin line-art,
  CAPS titles, amber/mint/rose accents) and **illustrated sets** (golden-hour sky, blurred sage hills,
  flat houses/trees/clouds, interiors). Change the palette per project only if asked; never copy a
  reference's exact colours/outfits.
- **Characters: flat cartoon people with skin-tone faces, hair styles, eyebrows, blinking, expressions,
  mouths. NEVER black-head stickmen** (user rejected that). Different outfit + hair + skin per person.
- **Human "photos"**: painted fully in code (`_paint_portrait`, polaroid cards with tape + callout label).
  Use them for key real-world people (agent, lender, couple...). No stock images needed.
- **Stock footage**: allowed only in a few chosen spots; the rest stays animation. (Network is
  restricted, so default to animation.)
- **Text animation is a core feature**: titles slide/fade in, pill tags pop with overshoot (`back_out`),
  numbers count up (`money()`), stamps slam in, strike-through/underline draws, callout lines,
  calendar flips, donut/gauge/bar fills, shake on shock. Every item lands on the exact spoken word.
- Every shot slowly pushes in + tiny drift; ~0.06 s dip at cuts; vignette + film grain on top.
- Visual metaphors per beat (stack of monthly costs, jar emptying, house squishing under pressure...).
  Hook in first 15 s, callbacks at the end, "next video" teaser + like/subscribe at the end if relevant.
- Check stills in 12-up contact sheets before the full render; fix overlapping/clipped text
  (min text size ~26 px at 1080p; keep >= 60 px from edges).

## Audio rules (the user complained SFX was too loud; keep it low)
- **SFX must be real recordings**, ~250-300 cues, each timed to a word/action via `S(t, name, gain)` placed
  next to the visual in `scenes.py`. Global level `BASE = 0.22` in `audio.py`; SFX stem ~ -33 LUFS.
  Voice stays dominant. Never raise SFX above the voice.
- Music: real sampled piano (Meta Piano CC0) score per section, ducked ~-6 dB under speech, drops out on
  panic/impact beats. Ambience loops (city/room/night/birds) very low.
- Final: loudnorm -14 LUFS, TP -1.5, AAC 192k.

## Pipeline (all in code)
1. `transcribe.py` -> `transcript.json` word timestamps (sherpa-onnx zipformer; HuggingFace/Azure are
   blocked in this sandbox, GitHub release `k2-fsa/sherpa-onnx` `asr-models/sherpa-onnx-zipformer-en-2023-06-26.tar.bz2`
   works). Transcription may mishear; fix wording in scenes by listening to timestamps.
2. Write `scenes.py` with absolute-second scene windows from the word times.
3. SFX/music sources reachable via GitHub only: `facebookincubator/Meta-open-sound` (Oculus Audio Pack,
   CC BY 4.0 -> must credit; Meta Piano CC0) and `apexnorthca/free-sale-sounds` (CC0). Convert chosen
   files into the project `sfx/*.ogg`.
4. `python render.py --audio voice.mp3 --out video.mp4 --jobs 4` (needs `pip install skia-python numpy scipy`
   and `apt-get install libegl1`; ~5 min for 6 min video on 4 cores).
5. `python audio.py --voice voice.mp3 --piano <meta-piano/ogg> --out mix.wav`, then mux with ffmpeg + loudnorm.
6. Deliver with SendUserFile: mp4 + `captions_en.srt`; put licence credits in README (Oculus credit line).
7. Commit + push to the session branch. Mp4 is ~70 MB (GitHub warns, still works).

## Gotchas
- `kit.py` appends (not inserts) `../video` to `sys.path`, otherwise the wrong `scenes.py` imports.
- Use 6-digit hex colours only.
- Do not recreate a specific existing show/game/film; original characters and layouts only.
