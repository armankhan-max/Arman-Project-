# "7 Smart Things to Buy in Your 60s" — stock-footage edit with pasted avatar

1920×1080, 30 fps. Voiceover + matching stock footage, the narrator's photo pasted
as a white-bordered cut-out (bottom-left) with a live voice waveform next to it,
word-highlighted captions and simple title text animations.

## Pipeline

1. `transcribe.py` — Whisper (`small`, faster-whisper) word timestamps → `transcript.json`.
2. `fix_voice.py` — fixes the voiceover:
   - removes a ~64 s block that was repeated (the real-estate "Whether you choose direct
     property ownership…" paragraph appeared twice),
   - removes the word "dot" that the TTS read out in place of full stops (10 places;
     each cut point is picked from the audio's quiet points and checked with Whisper),
   - writes `voice.wav` and `words_fixed.json` (word times on the new timeline).
3. `assets.py` — background-removed avatar stickers (rembg: BiRefNet-portrait / ISNet)
   and per-frame voice levels for the waveform (`levels.npz`).
4. `mixkit_index.py` + `plan.py` — free Mixkit stock clips (Mixkit License) are indexed by
   keyword; every 4–9 s scene of narration gets the best-matching clip (no repeats),
   plus the title cards, avatar photo per section and caption groups
   (`plan.json`, `captions.json`). `download.py` fetches the clips.
5. `bg.py` — cuts/crops every clip to its scene → continuous `bg.mp4`.
6. `render.py` — composites avatar, waveform, captions and titles over `bg.mp4`
   in parallel parts and muxes `voice.wav` → `final_video.mp4`.

```bash
python render.py --still 99.5 frame.png          # preview one frame
python render.py --bg bg.mp4 --voice voice.wav --out final_video.mp4 --jobs 3
```
