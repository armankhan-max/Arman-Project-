# Who Can Actually Afford a $500,000 House? (2D explainer)

`who_can_afford_500k_house_2d.mp4`: 6:13, 1920×1080, 30 fps, −14 LUFS. Captions: `captions_en.srt`.

## Style
The style is based on the flat explainer reference. It switches between two kinds of shots:
- **Infographic boards** with line-art, caps titles and one accent colour.
- **Illustrated sets** with black-head characters.

The colours and outfits are new:
- Boards are deep teal, with amber, mint and rose accents.
- Outdoor sets use a golden-hour palette.
- Outfits: teal hoodie, lilac cardigan, wine suit, slate suit, navy blazer, beige trench and olive overalls.

The human "photos" (agent, lender, couple, high earner) are painted entirely in code in `kit.py` (`_paint_portrait`). No stock images are used.

## Files
- `transcribe.py`: word timestamps for the voiceover (sherpa-onnx zipformer).
- `kit.py`: palette, boards, sets, characters, painted portraits and props.
- `scenes.py`: about 50 shots. Every pop, number and SFX cue is timed to the word that says it.
- `audio.py`: the voice, plus about 290 real recorded SFX cues, a real-piano score and ambience. The music and ambience duck under the voice.
- `render.py`: parallel frame renderer (skia → ffmpeg).

## Rebuild
```bash
pip install skia-python numpy sherpa-onnx   # + libegl1
python render.py --audio voice.mp3 --out video.mp4 --jobs 4
python audio.py --voice voice.mp3 --piano <Meta-open-sound>/systems/instruments/meta-piano/ogg --out mix.wav
ffmpeg -i video.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -af loudnorm=I=-14:TP=-1.5 -c:a aac -b:a 192k out.mp4
```

## Audio credits (put this in the YouTube description)
- "Oculus Audio Pack 01" by Oculus VR, LLC (https://developers.meta.com/vr/downloads/package/oculus-audio-pack-1/), licensed under CC BY 4.0. Files renamed and transcoded.
- Meta Piano samples (Meta Open Sound), CC0.
- Cash register, coins, ding, applause and receipt sounds from github.com/apexnorthca/free-sale-sounds, CC0.
