---
name: grandma-stock-video
description: Build a fully edited YouTube video (grandma/pantry/prepping style) from the user's AI images + voiceover - Ken Burns shots, matching free Mixkit stock footage, animated text, SFX, music, slowed voice with light reverb. Use when the user sends images/voice and asks for a "fully edited video", "वैसा ही वीडियो", stock footage + text animation + SFX.
---

# Grandma stock-footage video

Everything lives in `grandma_stock/`. Read `grandma_stock/README.md` first: it covers the workflow, the approved style, the stock and SFX ids, and the commands.

The rules the user cares about:

1. While images or voice are arriving, reply only "ओके ओके". Build only when they say generate.
2. Keep chat replies tiny. Do the work, then send the video with SendUserFile (under 400 MB).
3. Stock footage is compulsory and must match the narration. Search Mixkit with `tools/mixkit_search.py`.
4. Voice goes 7% slower (`SPD = 0.93`) with a light reverb. Keep SFX low. Start with the hook impact.
5. Copy `projects/cart_90day/` as the template. Write `project.py` (shots) and `text_cues.py` (text) from the transcript times, preview 2–3 frames, then run the full render.
6. Render into the scratchpad (`--work`). Never commit mp4s.
