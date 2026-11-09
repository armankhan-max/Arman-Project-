# "Why Attackers Never Touch a Woman Who Does This (Yakuza Secret)"

Sab kuch code se bana hai: voice (offline Kokoro TTS), avatar lip-sync (photo warp, no AI model),
B-roll motion graphics (skia), music + SFX (numpy synth).

| File | Kya hai |
|---|---|
| `script.txt` | Voiceover script (`#` = paragraph pause). Avatar female hai, isliye narrator "Reiko Kuroda" + "husband Michio". |
| `tts.py` | script -> `build/voice.wav` + `timeline.json` (sentence/word timings) |
| `avatar.py` | Lip-sync: voice energy/spectrum -> jaw open, lip width, blinks, head nods; `assets/avatar.jpg` warp |
| `kit.py` | Drawing kit: silhouettes, anatomy, X-ray hand (27 bones), skull, titles, stamps, kickers |
| `scenes.py` / `scenes2.py` | ~45 B-roll scenes + `SHOTS` list (A = avatar, S = split, P = scene + PiP avatar, B = full B-roll) |
| `render.py` | Frames render (4 parallel workers) |
| `audio.py` | Music (drone + koto + taiko) + SFX on scene cues, ducked under voice |

## Re-build
```
pip install skia-python opencv-python-headless kokoro-onnx soundfile
# models: kokoro-v1.0.onnx + voices-v1.0.bin (github.com/thewh1teagle/kokoro-onnx releases)
python3 tts.py MODELS_DIR
python3 render.py events && python3 render.py all 4 && python3 audio.py
ffmpeg -i build/video_noaudio.mp4 -i build/mix.wav -c:v copy -c:a aac -b:a 192k -shortest self_defense_final.mp4
```
Naya script: `script.txt` badlo -> `tts.py` -> `scenes.SHOTS` me sentence numbers adjust karo -> render.
