# "Is This Still Worth It? 12 Things for 2027": 2D stickman video

1920×1080, 30 fps, 6:55, made for the voiceover `Andrew_Clear_Open_Hall.mp3`.

Output: `is_this_still_worth_it_2d.mp4` (voice + soft music bed, −14 LUFS)

## Style
- **Stickman scenes** reuse the dark rim-lit kit from `../blackhole/sgfx.py`. The main character, Sam (teal),
  stands in for "you". There's also a cashier, a chef, a banker and a courier.
- **Code-made "photos"**: whenever the voiceover names a real object (car, phone, receipt, coffee cup, shirt,
  pill bottle, bank card, statement, TV, jar of coins…), the video cuts to a product shot drawn in code.
  These shots use a studio backdrop, gradient shading, highlights and soft shadows (`pgfx.py`). No stock images
  or real brand logos are used.
- **No burned-in captions.** On-screen text is limited to the numbers and key amounts.
- **Sound kept clean:** the voice comes first, under it is a quiet original music bed that ducks while
  the narrator speaks, and the only effect is a soft swoosh on each of the 12 title cards.

## Files
- `transcript.json`: Whisper (small) word timestamps
- `pgfx.py`: photo props, sets, cast, charts and title cards
- `scenes_a.py` (hook → #5), `scenes_b.py` (#6 → end screen): timeline with absolute timestamps
- `scenes_wi.py`: joins both parts and adds the finish (vignette, grain, cut dips)
- `audio_wi.py`: music bed and mix
- `render.py`, `sheet.py`: renderer, plus a contact sheet for previews

## Re-render
```bash
pip install skia-python numpy scipy        # Linux needs libegl1
python sheet.py preview.png 12 45 150      # quick stills
python render.py --audio voice.mp3 --out video_voice.mp4 --jobs 4
python audio_wi.py --voice voice.mp3 --out mix.wav
ffmpeg -i video_voice.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy \
       -af loudnorm=I=-14:TP=-1 -c:a aac -b:a 192k is_this_still_worth_it_2d.mp4
```
