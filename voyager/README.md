# Voyager 1 hits one light-day: a 40-second news short in Blender

A 3D news explainer built entirely with Blender's Python API (Blender 5.2,
EEVEE). It has one shot per script line, a camera cut on the first word of
every line, in-shot animation keyed to individual words, and burned-in captions.

**The news:** NASA expects Voyager 1 to reach **one light-day from Earth on
November 18, 2026**, about 25.9 billion km (16.1 billion miles, ~173 AU). After
that, a radio signal takes more than 24 hours each way.
Sources: [EarthSky](https://earthsky.org/space/voyager-1-1-light-day-from-earth-november-17-18-2026/),
[IFLScience](https://iflscience.com/its-official-voyager-1-will-cross-the-1-light-day-threshold-on-november-18-2026-82733),
[Popular Science](https://popsci.com/science/voyager-one-light-day-earth).

## The script (40 s, 112 words)

> On November eighteenth, a spacecraft launched in 1977 crosses a line nothing built by humans has ever reached.
> Voyager 1 will be one light-day from Earth.
> That's about twenty-six billion kilometers.
> Light, the fastest thing in the universe, needs a full day to get there.
> So when engineers send a command, it takes a day to arrive...
> ...and another day to hear back.
> Voyager flew past Jupiter and Saturn, then crossed into interstellar space in 2012.
> Its nuclear power is fading, so instruments are being switched off, one by one.
> It still carries a golden record of sounds and music from Earth.
> Forty-nine years, one light-day, and it's still talking to us.

## Shot list (cut = first word of the line)

| Shot | Cut at (s) | Length (s) | Line | Picture | Word-timed beats |
|---|---|---|---|---|---|
| L01 | 0.00 | 7.54 | On November eighteenth… | Earth push-in | "NOV 18, 2026" on *November*, "LAUNCHED 1977" on *1977*, tagline on *crosses* |
| L02 | 7.54 | 2.43 | Voyager 1 will be one light-day… | Voyager hero orbit | "VOYAGER 1" on *Voyager*, "1 LIGHT-DAY" on *light-day* |
| L03 | 9.97 | 2.54 | That's about twenty-six billion… | Wide: Earth ↔ Voyager | beam starts drawing on *twenty-six*, finishes on *kilometers*; "≈ 25.9 BILLION KM" on *billion* |
| L04 | 12.51 | 4.01 | Light, the fastest thing… | Tracking a light pulse | pulse travels the whole line; "SPEED OF LIGHT" on *fastest*, "24 HOURS" on *day* |
| L05 | 16.52 | 3.56 | So when engineers send a command… | Earth, command pulse leaves | pulse launches on *send*; "COMMAND SENT" on *command*; "+1 DAY" on *arrive* |
| L06 | 20.07 | 1.68 | …and another day to hear back. | At Voyager, reply flies home | "REPLY" on *another*, "+2 DAYS" on *back* |
| L07 | 21.75 | 5.51 | Voyager flew past Jupiter and Saturn… | Chase cam flyby | passes Jupiter on *Jupiter*, Saturn on *Saturn*, heliopause on *interstellar* (labels 1979 / 1980 / 2012) |
| L08 | 27.26 | 4.76 | Its nuclear power is fading… | RTG + instrument panel | RTG glow dims on *fading*; status lights go dark on *switched*, *off*, *one*, *by* (the last stays on) |
| L09 | 32.02 | 3.68 | It still carries a golden record… | Golden Record close-up | light sweep peaks on *music*; labels on *golden* and *sounds* |
| L10 | 35.70 | 4.27 | Forty-nine years, one light-day… | Pull back to a pale blue dot | "49 YEARS" on *Forty-nine*, "1 LIGHT-DAY FROM HOME" on *light-day*; camera fastest until *still* |

The cuts are Blender **timeline markers bound to cameras** (`marker.camera`),
so you can see and drag them in the Timeline once you open the .blend.

## Files

| File | What it is |
|---|---|
| `script.txt` | The script, one line per shot |
| `make_voice.py` | Scratch voiceover (espeak-ng) plus word timings → `voice.wav`, `transcript.json` |
| `transcript.json` | Word-level timings, the single source of truth for every cut and beat |
| `build_scene.py` | Builds `voyager_news.blend`: models, materials, 10 cameras, camera-bound markers, word-keyed animation, EEVEE settings, VSE caption strips, and `captions_en.srt` |
| `render.py` | Headless render: `stills`, `frames` (parallel, resumable), and `edit` (final MP4) |
| `voyager_news.blend` | The scene. The **Shots** scene holds the 3D; the **Edit** scene holds the sequencer with captions and voice |
| `captions_en.srt` | Caption file for YouTube or other platforms |
| `voyager_news.mp4` | The finished 1080p video |

## Build and render

```bash
pip install bpy            # Blender 5.2 as a Python module (or use `blender -b -P <script> -- <args>`)
python make_voice.py       # optional: regenerate the scratch VO + timings
python build_scene.py      # -> voyager_news.blend + captions_en.srt
python render.py stills    # one frame per shot, to check the look
python render.py frames --jobs 2
python render.py edit      # -> voyager_news.mp4 (frames + captions + voice)
```

Or open `voyager_news.blend`, switch to the **Edit** scene and choose Render ▸
Render Animation. The scene strip renders the Shots scene through EEVEE.

### Swapping in a real voiceover

The included voice is a robotic espeak-ng placeholder. HuggingFace was blocked
in the build environment, so neural TTS models could not be downloaded. To use
a real VO:

1. Record or generate `voice.wav` reading `script.txt`.
2. Get word timestamps (for example faster-whisper with `word_timestamps=True`) and
   write them to `transcript.json` in the same format: `[{start, end, text, words:[{w, s, e}]}]`,
   one segment per script line.
3. Re-run `build_scene.py` and `render.py`. Every cut, label pop, beam, pulse
   and light switch-off moves to the new timings automatically.

## Render settings and why

- **EEVEE**, 8 TAA samples, shadow resolution 0.25, AgX (Medium High Contrast),
  plus a Fog Glow glare node in the compositor for the glowing beam and pulses.
- The 3D renders at **1280×720** and is scaled into the **1920×1080** edit, so
  captions stay crisp at full resolution. The build machine had no GPU (software
  OpenGL), where 1080p frames took ~37 s each and 720p takes ~7 s. On a real
  GPU, set `SHOT_RES = (1920, 1080)` and raise `taa_render_samples` in
  `build_scene.py`.
- Captions are VSE text strips in Inter Bold. Chunks are up to three words,
  broken at punctuation, each shown from its first word's onset. Chunks with
  numbers or key terms (light-day, billion, golden, interstellar) are gold.
- Every shot's set sits at its own X offset (2000 units apart), and objects are
  hidden from render outside their shot, so no set ever leaks into another
  shot.
