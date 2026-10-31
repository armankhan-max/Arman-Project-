# "What if you didn't drink water?" — 2D animated video

A 1920×1080, 30 fps flat-vector 2D animation, timed to the ElevenLabs voiceover
(`Jessa – Easygoing and Effortless`, 5:11).

Output: `what_if_no_water_2d.mp4`

## How it was made

1. **Transcription:** the voiceover was transcribed with Whisper (`small`,
   faster-whisper), which gave word-level timestamps → `transcript.json`.
2. **Animation:** every frame is drawn in code with [skia-python](https://github.com/kyamagu/skia-python):
   - `gfx.py`: characters (You, Noor, Ranger Ines, Grandma Layla) with poses,
     expressions and blinking, plus the car and ranger truck, the desert
     (sky changes from noon to night to sunrise), and props and infographic
     pieces (water body, kidneys, brain, thermometer, mirror, bottle…).
   - `scenes.py`: 25 scenes keyed to the narration's timestamps, the time
     stamps (`HOUR 1`, `NIGHT 1`…), and word-by-word highlighted captions.
3. **Render:** `render.py` splits the frames across worker processes. Each
   worker pipes raw frames to ffmpeg (x264), then the parts are joined and the
   voiceover is muxed in.

## Re-render

```bash
pip install skia-python numpy          # needs libegl1 on Linux
python render.py --still 158 frame.png # preview one frame at t=158s
python render.py --audio voice.mp3 --out what_if_no_water_2d.mp4 --jobs 4
```

To change what appears when, edit the times in `SCENES` / `STAMPS` in
`scenes.py`. They are absolute seconds in the audio.
