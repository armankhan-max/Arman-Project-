---
name: stock-media
description: Finds and downloads free stock footage (video clips) and stock images WITHOUT watermarks (Openverse, Wikimedia Commons, Internet Archive, plus Pexels and Pixabay when an API key is set) for any video topic, and saves them with credits. Use whenever the user needs b-roll, stock video, stock photos, images or background clips for a video, on any topic, or says "stock footage", "stock images", "without watermark", "b-roll" or "download clips for this topic".
---

# Stock footage and images (no watermark)

Run: `python3 .claude/skills/stock-media/stock.py <video|image> "<topic>" [--n 6] [--out DIR] [--min-height 720]`

- Saves files to `DIR` (default `stock/<topic>/`) and writes `credits.txt` (title, author, license, link). Always keep and show the credits; licenses are free-to-use ones (CC0, public domain, CC-BY and similar). The script prints each license, so tell the user when attribution is required.
- Sources without any key: Openverse (images), Wikimedia Commons (video and images), Internet Archive (video). If env var `PEXELS_API_KEY` or `PIXABAY_API_KEY` is set, those are searched too (best quality stock clips). If the user wants Pexels/Pixabay and no key is set, ask them for a free key (pexels.com/api, pixabay.com/api/docs) and use `request_credential` or an env var.
- Try several short English search words for one topic (for example "miami beach", "police car night", "city skyline aerial"). Look at the files (extract a frame with ffmpeg) before using them: skip any with a visible watermark, logo or text.
- Never download from sites that need a login or bypass bot checks. Never use pirated or leaked footage.
- Convert for editing when needed: `ffmpeg -i in.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30" -an out.mp4`
