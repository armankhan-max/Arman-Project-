---
name: mark-tilbury-video
description: Turn a voiceover (mp3) into a finished faceless-finance YouTube video in the "Mark Tilbury" avatar style — cleaned voice, matching stock footage with a dark filter, the background-removed avatar photo pasted bottom-left with a live waveform, word-highlight captions, chapter cards, key-point cards and number pops. Use when the user sends a voiceover and asks for "Mark Tilbury wala video", "same style video", "voice se video bana do", or anything like the earlier avatar videos in this repo.
---

# Mark Tilbury avatar video (from a voiceover)

Everything lives in `kit/` (repo root). Work in a new folder per video, e.g. `videos/<topic>/`.
The two earlier videos (`avatar_video/`, `video2/`) were made this way; `video2/` is the reference.

## How the user wants it (important)
- Talks in Hindi/Hinglish. Reply in short Hinglish. **Very little chat text** — no long explanations,
  no frames/screenshots unless asked. Start with "OK boss, kaam start kar raha hoon" and just work.
- Wants it fast. Don't stop to ask questions; sensible defaults.
- English videos (the voiceover is English).
- Before sending, cross-check like a viewer: "would I click and keep watching?" Look at a grid of
  6-8 frames yourself (don't send them). Fix anything off.
- **Delivery: ONE merged file under ~95 MB** (`Final_Video.mp4`, 480p). Bigger files (150 MB+) failed
  to download on the user's phone ("another file is still downloading"). Verify it decodes end to end.
  Also commit + push it.

## Steps
```bash
bash kit/setup.sh                                  # once per session (~4 min): whisper, DeepFilterNet, rembg
mkdir -p videos/<topic> && cd videos/<topic>
bash ../../kit/stage1.sh /root/.claude/uploads/.../voice.mp3     # ~25 min for a 35-min voice
```
Stage 1 = DeepFilterNet echo/noise removal + EQ/compression/-14 LUFS (`clean_voice.py`), Whisper
word timestamps, a 4-process scan for the word **"dot"** (the user's TTS reads full stops as "dot" —
happened in both videos, 10-25 times), `dot_list.json`, and `transcript.txt` (45 s blocks).

Then, by hand (needs judgment):
1. **Read `transcript.txt`.** Check for repeated paragraphs (video 1 had a 64 s block twice) or parts
   in the wrong order. If found, add the cut to `fix_voice.py` (see the "duplicated block" code in
   `avatar_video/fix_voice.py`).
2. **Review `dot_list.json`** — `[time, prev_word, next_word]`. Drop false hits, fix prev/next words
   (look at `transcript.json` words around the time). Then `python3 ../../kit/scripts/fix_voice.py`.
   It tests candidate cuts with Whisper and keeps the first clean one; cuts it can't solve print `!!`.
   For those, look at the energy envelope and put a manual `[a, b]` in `dot_cuts.json`, rerun.
3. **Write `video.json`** (see `kit/example_video.json`): `chapters` (big centre cards: intro + each
   "Number one/two…" item + summary + final thought), ~25 `titles` (top-left key-point cards, one every
   ~60-90 s), 3-5 `pops` (numbers like "-50%", "$200 → $100"), `caption_fixes` for Whisper mistakes,
   `extra_concepts` ([regex, "mixkit search words"]) for topic-specific b-roll.
   `phrase` = the exact spoken words (lowercase) where the card should appear.
   If the topic needs new footage keywords: `python3 ../../kit/scripts/mixkit_index.py "keyword" ...`

```bash
bash ../../kit/stage2.sh        # plan -> download clips -> bg.mp4 -> render (4 jobs) -> Final_Video.mp4  (~40 min)
```
Before the long render, check a few stills:
`python3 ../../kit/scripts/render.py --bg bg.mp4 --still 75 /tmp/f.png` (also chapter times, an avatar switch).
Check the b-roll picks: print `plan.json` scene clip names vs text; add bad words to `BAD` in `plan.py`.

## Look (already built into render.py)
- Background: Mixkit stock clips (free, no key; `assets.mixkit.co/videos/<id>/<id>-720.mp4`), darkened
  (×0.55) + vignette, ~6 s per scene, 1 in 4 scenes nature, 1 in 6 business/city. Clips used in earlier
  videos are avoided (`kit/data/used_clips.txt`, updated by stage2).
- Avatar: 3 background-removed photos (`kit/avatar/sticker1-3.png`, white sticker border), bottom-left,
  big (~700 px), switches photo every ~20 s with a pop, yellow glow when speaking.
- Big waveform pill with mic icon next to the avatar; captions bottom-right, 2-4 words, yellow word highlight.
- Chapter cards (centre, 01/02/…), key-point cards (top-left, wipe in), yellow number pops (top-right),
  thin yellow progress bar on top, soft dip at cuts.

## Gotchas
- Pexels/Pixabay need keys (user declined); Coverr API was blocked. Use Mixkit.
- `github.com/.../raw/...` is blocked; use `raw.githubusercontent.com` (setup.sh does).
- DeepFilterNet needs torch CPU + a patched `df/io.py` (setup.sh does it) and numpy>=2.1.
- Keep big files out of git (`.gitignore`): clips, bgseg, parts, bg.mp4, HD render, wavs.
- Disk is limited (~20 GB free): delete `bgseg/`, `parts/`, `bg.mp4` of old videos if needed.
