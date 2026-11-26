# "If you were born as Tommy Vercetti": 2D video, 6:34

This video uses the same style kit, editing and director camera as `gta6/`.

## Files
- `script.txt`: the narration script.
- `voice.wav`: the narration (Kokoro TTS, voice `af_heart`).
- `scenes_t.py`: the timeline (~60 shots).
- `sets_t.py`: new sets: Liberty City, Harwood, courtroom, junkyard, Vercetti mansion, roof, balcony, Malibu
  Club and El Banco Corrupto Grande.
- `timeline.py`: the director camera and transitions.
- `audio_t.py`: background music for each scene, plus sound effects.

## Build
```bash
python render.py --audio voice.wav --out video.mp4 --jobs 4
python audio_t.py --voice voice.wav --out mix.wav
ffmpeg -i video.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -af loudnorm=I=-14:TP=-1 -c:a aac -b:a 192k final.mp4
```

Music by Kevin MacLeod (incompetech.com), CC BY 4.0. See `gta6/README.md` for the credit line.
