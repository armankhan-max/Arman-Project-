# GTA 6 buying guide: neon open-world style video

`gta6_buying_guide.mp4`: 1920×1080, 30 fps, about 5:05. No burned-in captions.

## What's inside
- **Visuals:** an original "sun-soaked crime-city" game look, drawn in code with skia:
  - sunset and neon coast city, palms, wet reflective streets and sports cars
  - a money HUD, a minimap, a character-switch wheel, slanted slam titles and stamps
- **2D explainers:** rim-lit stickman characters with the console, price, storage, internet and preload props.
- **No real game assets:** no logos, key art, characters or fonts from any real game. Everything is original.
- **Timing:** the voice was transcribed with Whisper (word timestamps, saved as `transcript.json`). Every cut, title and SFX is keyed to a word with `T("word", approx_time)`.
- **Ending:** the recording continues after 5:01 with the script's production notes ("Hook open loop… Fact ledger…"). The video ends at the last narrated line, followed by a 3.6 s music outro.
- **Audio:**
  - original synthwave BGM at 100 BPM in A minor. Its sections follow the story: tense hook, a drop on "launches", groove, a drone for the disc reveal, a warm section, and a full finish.
  - the music sits about 17 dB under the voice and is auto-ducked.
  - about 260 synthesized SFX: cash register, coins, crowd, stamps, locks, download blips, car pass, record scratch and more.
  - the final mix is loudness-normalized to −14 LUFS.

## Files
- `ggfx.py`: style kit (environment, props, HUD, titles)
- `scenes_gta.py`: timeline (33 scenes) and SFX cue list
- `audio_gta.py`: music and SFX synthesis, plus the mix
- `render.py`: parallel frame renderer

## Re-render
```bash
export PYTHONHASHSEED=0
python audio_gta.py --voice voice.mp3 --out mix.wav
python render.py --audio mix.wav --out video_raw.mp4 --jobs 4
ffmpeg -i video_raw.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy \
       -af loudnorm=I=-14:TP=-1 -c:a aac -b:a 192k gta6_buying_guide.mp4
python render.py --still 27.9 frame.png   # preview one frame
```
Requires `skia-python`, `numpy`, `scipy` and `ffmpeg`, plus the shared helpers in `../video` and `../blackhole`.
