# AI Video Studio

Type a title, then pick a style and a voice. The studio writes the script, records the voiceover, finds B-roll, edits everything together and gives you a finished MP4 with a thumbnail and an upload pack.

## Run it
```bash
# needs Python 3.10+ and ffmpeg (sudo apt install ffmpeg, or brew install ffmpeg)
pip install -r requirements.txt
python app.py            # then open http://localhost:8000
```
The first time you open it, you choose the **owner password**. Only the owner can log in, make videos and change settings.

## What it does
| Part | How |
|---|---|
| Script | Claude, any OpenAI-compatible API, or free Pollinations. You can also paste your own script. The script rules from the master prompt are editable in the Owner panel. |
| Voiceover | 300+ free neural voices (English, Hindi, Hinglish and more) with word-level timing, or upload your own recording |
| A-roll | **Best:** upload your avatar's talking video (from HeyGen, D-ID, Hedra or your own phone). Its voice becomes the voiceover, and the studio cuts between the host and B-roll with the lips always in sync. **Or** upload a host picture, which plays with a handheld phone-camera feel. A D-ID key turns a picture into a talking face. |
| B-roll | Pexels and Pixabay stock video and photos (free keys), Wikimedia Commons (historical photos, maps, satellite images), Openverse, and AI images from Pollinations. A generated backdrop is used if all of these fail. |
| Camera | Push in, pull out, pans, tilt, dolly diagonal, orbit, and parallax with depth-of-field blur. Stock clips run in slow motion. |
| Editing | Crossfades, dissolves, slides, zoom and circle transitions between scenes. Hard jump cuts between host shots. A cold open, and an end card with credits. |
| Animated maps, charts, timelines | Made in code with no keys needed: `map: Egypt` (zooms in, highlights the country, pin drop, label), `bars: Honey=3000, Milk=7 (days)`, `timeline: 1922=Tomb opened; 2026=Still edible`. The AI adds them where the script names a place, numbers or dates, and you can add or change them in the scene editor. |
| Motion graphics | Word-by-word captions, big pop text, numbers that count up with an accent bar, callout labels that slide in, and a title tag |
| Sound | Whooshes on transitions, a cinematic hit on the opening, the twist and the end card, risers, pops and ticks on text, and an ambient bed |
| Music | Generated moods (suspense, cinematic, emotional, calm, upbeat), or upload your own tracks. The music ducks under the voice automatically. |
| Voice processing | High-pass filter, de-esser, compressor, presence EQ, loudness normalised to -14 LUFS, and a limiter so nothing clips |
| Grading | A per-style colour grade, vignette and film grain |
| Extras | Title generator, thumbnail maker, an upload pack (titles, description, tags, hashtags, pinned comment), and a scene editor that lets you re-render only what changed |

## Free vs. keys
With no keys at all, the studio works like this. The script, scene plan and titles come from the free Pollinations writer, which allows one reply every 45 seconds, so a video takes a few minutes. Visuals come from AI images, Wikimedia Commons and Openverse, all with no watermark. **The free writer can make up facts, so always read the script before you upload.** For accurate scripts, add a Claude key.

## Keys (all optional, set them in the Owner panel)
- **Anthropic** or **OpenAI-compatible**: smarter scripts, scene planning and titles
- **Pexels** (pexels.com/api) and **Pixabay** (pixabay.com/api/docs): free, real stock video with no watermark. Signing up takes about 2 minutes.
- **Pollinations** (optional): removes the free 45-second wait
- **D-ID**: lip-sync for the avatar

Styles (look, transitions, camera moves, music, SFX and tone) are JSON in the Owner panel. You can edit them or add new ones.

Map shapes come from Natural Earth (public domain).
