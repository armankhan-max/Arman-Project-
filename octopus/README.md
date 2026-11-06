# Giant Pacific Octopus: 2D animated video

**Video:** *Why You'd Never Want To Meet A Giant Pacific Octopus*, 8:13, 1920×1080, 30 fps.

| File | What it is |
|---|---|
| `giant_pacific_octopus_2d.mp4` | Final video: both voiceovers merged, with music and SFX (compressed to 87 MB to fit GitHub's 100 MB limit; the full-quality 125 MB render was delivered separately) |
| `voiceover_merged.mp3` | The two voiceover parts joined into one track (0.9 s gap) |
| `thumbnail_1280x720.png`, `thumbnail_1920x1080.png` | Thumbnail: "IT TASTES YOU.." with an engraved octopus |
| `captions_en.srt` | English subtitles |
| `YOUTUBE_UPLOAD.md` | Title, description with chapters, and tags |

## Style (matched to the reference videos)
- Dark teal ocean gradient, swaying god-rays and drifting "marine snow".
- Flat vector animals without outlines: octopus with suckers, papillae spots and slit pupils;
  a small black-suited diver with a torch who stands in for "you".
- Letter-spaced all-caps labels: white for facts, red for danger, amber for numbers.
- Infographic shots like the references: chapter cards with progress dots, X-ray/blueprint diagrams,
  a "YOUR OPTIONS" list that gets crossed out, a map card, REC camera brackets, and a parchment "Here be Monsters" page.
- Vignette and light film grain on every frame.

## How it was made
1. Both voiceovers were transcribed with word timestamps (Parakeet ASR + Silero VAD) → `transcript.json`.
2. `scenes.py` has about 85 shots. Each starts on its sentence, and labels pop in on the exact spoken word.
3. `audio_octo.py` builds the low background score (it changes with the mood), underwater ambience and
   about 150 sound effects placed on words. The music ducks under the voice, and the final mix is normalized to −14 LUFS.
4. `thumbnail_octo.py` renders the octopus as a grey shading map, then converts it to engraving-style hatch lines.

## Re-render
```bash
python audio_octo.py --voice voiceover_merged.mp3 --out mix.wav
python render.py --audio mix.wav --out octo_raw.mp4 --jobs 4
ffmpeg -i octo_raw.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -af loudnorm=I=-14:TP=-1 -c:a aac -b:a 192k giant_pacific_octopus_2d_FULL.mp4
python thumbnail_octo.py
```
Requires `skia-python`, `numpy`, `scipy`, `Pillow` and `ffmpeg`. Shared helpers come from `../video/gfx.py`, `../video/audio.py` and `../blackhole/audio_bh.py`.
