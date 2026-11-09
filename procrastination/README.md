# The Loop: how to never procrastinate again (2D remake, female voiceover)

`The_Loop_never_procrastinate_again.mp4`: 1920×1080 (16:9), 30 fps, 2:44, -14 LUFS, no captions.

- `voice.py`: female voiceover (Kokoro TTS, voice `af_heart`), same script → `voice.wav`, `timing.json`
- `kit.py`: style kit (rim-lit stickwoman, light-wrap shading, sets, props, kinetic type)
- `loop_scenes.py`: timeline locked to `timing.json`
- `audio_loop.py`: original score + SFX, ducked under the voice, -14 LUFS

```bash
python audio_loop.py --voice voice.wav --out mix.wav
python render.py --audio mix.wav --out v.mp4 --jobs 4
ffmpeg -i v.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k final.mp4
```
