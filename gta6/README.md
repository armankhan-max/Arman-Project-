# "If you were born as Lucia Caminos": 2D GTA VI lore video

1920×1080, 30 fps, 12:41. Flat-vector cartoon in the style of the reference
video: chibi characters with thick outlines, detailed sets, polaroids, paper
maps, name tags, speech bubbles, marker text and stamps, plus a Vice City
sunset and neon palette.

Everything is drawn in code. No game footage or copyrighted art is used, so
the video is safe to upload.

## Files
- `what_if_born_as_lucia_gta6.mp4`: the finished video (voice, music, SFX, −14 LUFS)
- `captions_en.srt`: subtitles to upload separately
- `frames/`: preview stills
- `g6fx.py`: style kit (characters, outfits, poses, expressions, cars, props, UI)
- `sets.py`: 36 backgrounds (Vice City, Leonida map, prison, Keys, bar, bank,
  penthouse, bridge…)
- `common.py`, `scenes_a.py`, `scenes_b.py`: the timeline (~110 shots). Every
  pop is keyed to a word timestamp with `wt("word", near_time)`.
- `scenes_g6.py`: crossfades, chapter tag, vignette and grain
- `audio_g6.py`: synthwave and drama music cues, ~200 sound effects on word
  times, ambience, and auto-ducking under the voice
- `transcript.json`: word timestamps from Whisper

## Re-render
```bash
pip install skia-python numpy scipy faster-whisper   # needs libegl1
python render.py --still 99 frame.png                 # preview one frame
python render.py --audio voice.mp3 --out video_voice.mp4 --jobs 4
python audio_g6.py --voice voice.mp3 --out mix.wav
ffmpeg -i video_voice.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy \
       -af loudnorm=I=-14:TP=-1 -c:a aac -b:a 192k what_if_born_as_lucia_gta6.mp4
```

## Music credits (put this in the YouTube description)
Music by Kevin MacLeod (incompetech.com), licensed under Creative Commons: By Attribution 4.0
(http://creativecommons.org/licenses/by/4.0/). Tracks: Investigations, Sneaky Snitch, Volatile Reaction,
Dark Fog, Night on the Docks - Sax, Hitman, Mining by Moonlight, Crypto, Funkorama, Rollin at 5, Sad Trio,
Heartwarming, Bass Walker, Lightless Dawn, Bossa Antigua, Scheming Weasel (faster version). Put the mp3s in `gta6/music/` to rebuild the mix.
