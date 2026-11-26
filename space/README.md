# Space documentary — 2D stickman explainer

Rim-lit black-head stickman presenter (same style as `../blackhole`) explaining ~40 space facts,
synced to the voice-over (`voice.mp3`, 10:46).

- `cosmos.py` – presenter animation (pose keyframes, walk cycle, gestures, lip flap from word timings) + space objects
- `doc_scenes.py` – scene timeline (absolute voice-over timestamps)
- `audio_doc.py` – mix: voice compressed and loud (-13 LUFS), ambient pad ~21 dB under voice (+4 dB duck), only faint air swells on topic changes
- `render_doc.py` – renderer (`--still t out.png`, `--sheet out.png t1 t2…`, `--audio voice.mp3 --out video.mp4`)

```bash
python render_doc.py --audio voice.mp3 --out video_noaudio.mp4 --jobs 4
python audio_doc.py --voice voice.mp3 --out mix.wav
ffmpeg -i video_noaudio.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest space_documentary.mp4
```
