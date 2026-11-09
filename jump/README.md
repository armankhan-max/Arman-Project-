# What If You Jumped on Every World?: 2D animated video

A 1920×1080, 30 fps flat-vector 2D animation timed word-for-word to the voiceover
`voice.mp3` (7:30).

## Files

| File | What it is |
|---|---|
| `what_if_you_jumped_on_every_world.mp4` | Finished video: voice + music + SFX, −14 LUFS, captions burned in |
| `captions_en.srt` | Subtitles for YouTube Studio |
| `thumbnail_1280x720.png` / `thumbnail_1920x1080.png` | Thumbnail ("Same jump. Different world.") |
| `YOUTUBE_UPLOAD.md` | Title options, description with chapters, tags |
| `transcript.json` | Word-level timestamps of the narration |

## How it was made

1. **Transcription.** The narration was transcribed with a sherpa-onnx Zipformer model
   (GigaSpeech), which gave a timestamp for every word. A few misheard names were fixed by hand
   (Enceladus, Ceres, "one and a third", "missions", "falls").
2. **Physics, not guesses.** Every jump uses a launch speed of 3 m/s and each world's real surface
   gravity, so height = v²/2g and air time = 2v/g. That's why the Moon jump really hangs for
   about 3.7 s on screen, and the Pluto jump really takes about 10 s to come down. The Enceladus
   (≈ 53 s) and Bennu (never comes back) jumps are the only ones sped up or left open.
3. **Style kit (`jgfx.py`).** Re-uses the character and drawing primitives from `../video/gfx.py`
   and adds:
   - a world painter for 15 worlds (sky, stars, sky objects, craters, ice cracks, lava, cloud
     tops, geysers, plasma),
   - a jump engine (crouch → ballistic arc → landing squash),
   - measuring props (ruler, height tags, hoop, kitchen table, house, tower, stair step),
   - widgets (gravity badge, stopwatch, planet icons, title cards).
4. **Timeline (`scenes_jump.py`).** 48 scenes keyed to the narration's timestamps, with slow
   push-ins, black dips between cuts, vignette and grain, and word-by-word highlighted captions.
5. **Soundtrack (`audio_jump.py`).** Fully synthesized, so it's original and royalty-free:
   - music cues follow the story: mystery drone → curious marimba (the rule) → floaty hope pad
     (Moon) → light groove (Mars/Mercury) → dread (Venus) → heavy ostinato (Jupiter, Sun, neutron
     star) → night pads (small worlds) → warm ending,
   - the music drops out for "…until now", the Bennu push-off and "the heat wins first",
   - ~150 sound effects: a whoosh and thud on every jump, chimes on world titles, dings on every
     height, stopwatch ticks, counter clicks, and buzzers on "not fixed", "T-shirt" and "not
     footsteps",
   - wind on Mars and Neptune, and a low rumble on Venus and the Sun,
   - the music ducks under the voice, and the final mix is normalized to −14 LUFS.

## Re-render

```bash
pip install skia-python numpy scipy        # Linux also needs: apt-get install libegl1
python render.py --still 66.5 frame.png    # preview one frame at t = 66.5 s
python render.py --audio voice.mp3 --out video_voice.mp4 --jobs 4
python audio_jump.py --voice voice.mp3 --out mix.wav
ffmpeg -i video_voice.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy \
       -af loudnorm=I=-14:TP=-1 -c:a aac -b:a 192k what_if_you_jumped_on_every_world.mp4
python make_srt.py                         # rebuild captions_en.srt
python thumbnail_jump.py                   # rebuild thumbnails
```

Set `BURN_CAPTIONS=0` to render without on-screen captions.

To change when something appears, edit the times in `SCENES` (or inside a scene function) in
`scenes_jump.py`. All times are absolute seconds in the voiceover.
