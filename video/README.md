# "What if you didn't drink water?" — 2D animated video

A 1920×1080, 30 fps flat-vector 2D animation, timed to the ElevenLabs voiceover
(`Jessa – Easygoing and Effortless`, 5:11).

Output: `what_if_no_water_2d_music_sfx.mp4` (voiceover + background music + SFX, −14 LUFS)

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

4. **Soundtrack:** `audio.py` synthesizes everything, so the audio is original
   and royalty-free:
   - **Music cues** follow the story: a tense desert drone with a heartbeat,
     an upbeat road-trip groove for the flashback, curious marimba under the
     facts, a soft night pad, a warm theme for the mirror scene, a building
     ostinato as you weigh walking for help (resolving on "You stay"), a
     hopeful swell for the rescue, and a bright outro.
   - **Music cuts out completely** for the rewind and for "Then, silence."
   - **~80 timed sound effects:** engine coughs and dying, phone error beep,
     tape rewind, whooshes on cuts, pops on text, "WRONG" buzzer, kidney
     squishes, cracker crunch, camera shutter, mirror flash chimes, heartbeat,
     ranger siren chirp, sips, check-mark dings, like/subscribe clicks and a
     bell.
   - **Ambience:** desert wind, and crickets at night.
   - **Mix:** the music ducks automatically under the narrator. The final mix
     is loudness-normalized to −14 LUFS.

## Re-render

```bash
pip install skia-python numpy          # needs libegl1 on Linux
python render.py --still 158 frame.png # preview one frame at t=158s
python render.py --audio voice.mp3 --out video_voice_only.mp4 --jobs 4
pip install scipy
python audio.py --voice voice.mp3 --out mix.wav --stems stems/
ffmpeg -i video_voice_only.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy \
       -af loudnorm=I=-14:TP=-1 -c:a aac -b:a 192k what_if_no_water_2d_music_sfx.mp4
```

To move a sound effect, change its time in `build_sfx()` in `audio.py`. To
change the music, edit `build_music()`.

To change what appears when, edit the times in `SCENES` / `STAMPS` in
`scenes.py`. They are absolute seconds in the audio.
