# "The Deadliest Gadgets Ever Sold": clean 2D explainer video

A 1920×1080, 30 fps kinetic-typography explainer, synced word by word to the
voiceover `Joanne_Merged_Clear_Hall.mp3` (12:55).

**Output:** `deadliest_gadgets_explainer.mp4` (voiceover only, normalized to −14 LUFS)
and `captions_en.srt` (corrected subtitles to upload to YouTube).

## Style: no distractions

- **One plain dark background** with a soft vignette. No grain, particles or busy textures.
- **Three colours only:** white text, **red** for the key word in each line, and
  **amber** for money and heat. Blue is used only for "safety" (the shield).
- **Text is the main visual.** Each line slides up word by word as the narrator
  says it. One idea is on screen at a time.
- **Big count-up numbers** for every statistic: 2.5M phones, $5 billion,
  500,000 hoverboards, 99 fires, 78 people burned, and so on.
- **Simple flat icons** for each gadget: phone, hoverboard, laptop, watch,
  washer, treadmill, magnets, Segway and power bank.
- **Diagrams only where they explain something:**
  - the inside of a lithium-ion cell (two layers and a thin separator)
  - the thermal-runaway loop
  - batch 1's squeezed corner
  - Sony's metal specks piercing the separator
  - magnets clamping through the intestine walls
  - the lithium-ion "hub" that links the Note 7, hoverboard, laptop and Fitbit
- **Calm motion:** short ease-out entrances, a very slow push-in on every
  beat, and a quick fade between beats. Nothing loops for attention.
- **Small chapter tag** in the top-left corner (`01 SAMSUNG GALAXY NOTE 7` … `09 THE POWER BANK`).
- **No music and no sound effects.** Only the voice. Captions come as a separate
  file, so they don't cover the picture.

## Chapters

| # | Gadget | Starts |
|---|---|---|
| intro | cold open + title | 0:00 |
| 01 | Samsung Galaxy Note 7 | 0:18 |
| 02 | Hoverboard | 2:38 |
| 03 | Exploding laptop batteries (Sony) | 4:20 |
| 04 | Fitbit Ionic | 5:26 |
| 05 | Samsung top-loading washer | 6:43 |
| 06 | Peloton Tread+ | 7:52 |
| 07 | Buckyballs | 9:20 |
| 08 | Segway | 10:43 |
| 09 | Power bank + recap | 11:26 |

## How it was made

1. `transcribe.py`: an offline speech-to-text model (sherpa-onnx Zipformer,
   with Silero VAD and a punctuation model) produces word-level timestamps in
   `transcript.json`.
2. `kit.py`: the style kit. It holds the palette, fonts (Inter), easing,
   word-by-word text reveal, icons, flames and smoke.
3. `engine.py`: the beat engine. Each beat is a list of elements: `T`
   headline, `S` supporting line, `K` kicker, `N` count-up number, `I` icon,
   `LIST`, and `G` custom graphic. Elements are laid out automatically, and
   each one appears at its own time. `tw("word", t)` returns the exact
   moment a word is spoken.
4. `timeline.py`: the whole video, about 150 beats plus the diagrams.
5. `render.py`: renders frames in parallel with skia-python and encodes them with ffmpeg/x264.
6. `make_captions.py`: builds `captions_en.srt` and fixes misheard words
   (for example "samson" → Samsung, "saguay" → Segway, "pellaton" → Peloton).

## Re-render

```bash
pip install skia-python numpy sherpa-onnx soundfile   # skia needs libegl1 on Linux
python render.py --still 105 frame.png                 # preview one frame at t=105 s
python render.py --audio voice.mp3 --out raw.mp4 --jobs 4
ffmpeg -i raw.mp4 -i voice.mp3 -map 0:v -map 1:a -c:v copy \
       -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 -c:a aac -b:a 192k final.mp4
```

To change what appears and when, edit `timeline.py`. Times are in absolute
seconds of the voiceover.
