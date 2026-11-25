# Grandma stock-footage video kit

This kit turns AI images and a voiceover into a fully edited YouTube video. Everything is built by code: shots, stock footage, text animations, SFX, music and the final render. The reference video is `projects/cart_90day` ("90-day grocery cart without power", 11:09, approved v2).

## Workflow (how the user works)

1. The user sends images in batches. Reply only **"ओके ओके"**. Do not start work.
2. The user sends the voiceover (mp3). Still wait.
3. When the user says **"अभी जनरेट कर दे" / "बना के दे"**, build the full video and send it. Keep chat replies very short: the user wants work, not text.
4. Only send the 2–3 preview frames you choose yourself. Send other frames only when the user asks for them.

## Build a new video

```bash
pip install faster-whisper
python3 tools/transcribe.py <voice.mp3> projects/<new>     # word-level times
python3 tools/mixkit_search.py grocery snow fireplace ...  # find matching stock clips
cp projects/cart_90day/{project.py,text_cues.py} projects/<new>/   # then edit both
python3 make.py projects/<new> --work <scratchpad>/<new> --frames 20 120 300   # preview
python3 make.py projects/<new> --work <scratchpad>/<new>                       # full render (~20 min)
```

`project.py` holds the voice path, image folder, `VO_DURATION`, `SPD`, the shot list, flash cuts, ambience and music.
`text_cues.py` holds the text animations. All times in both files are **original voiceover seconds**. `make.py` rescales them for the slowed voice.

Send the file with SendUserFile. The upload limit is 400 MB, and the encode settings (crf 21, maxrate 4.8M) keep an 11-minute video around 330 MB. Never commit rendered mp4s, because GitHub's limit is 100 MB.

## The style (user-approved)

**Voice:** `atempo=0.93` (7% slower, same pitch), a light room reverb (`aecho 45/90/140 ms`), gentle compression and -16 LUFS. The user asked for "slightly slow, slightly old-sounding, don't overdo it."

**SFX:** kept low (the user said they were too loud in v1). A cinematic impact plus thunder plays at 0 s as the hook. A soft whoosh plays on every cut (-29 dB), louder on flash cuts (-21 dB). Pops, hits, dings and ticks follow the text, with every text SFX trimmed by -6 dB. A subscribe button with a cursor click and bell appears twice: right after the intro and at the end.

**Music:** calm ambient from Mixkit (616 "What it Takes" → 584 "Rest Now"), ducked under the voice.

**Ambience:** winter wind (1157) in snow scenes and fire crackle (1330) in stove scenes.

**Picture:**
- Every image gets a smooth push in/out or a pan, with cosine easing, rendered from a 4K upscale to avoid jitter.
- Stock clips get an 8% push-in.
- Every shot gets a warm grade with vignette and light grain.
- Shots change every 2–8 s and follow the narration closely: the visual must match what is being said.
- Grandma A-roll goes on the intro, rules, recaps, safety and outro. B-roll (product images and stock) goes on each item.
- Transitions are 0.4 s dissolves, with every 4th one a smoothleft. A white flash marks a new section or a new item.

**Text (for a senior audience, large and readable):**
- Fonts: Anton for headlines, Montserrat ExtraBold for info. Text is white, with key words in warm yellow `[like this]`.
- `big` is a centre pop with overshoot. `words` reveals word by word. `lower` is a lower-third box that slides in.
- `item` is the "ITEM #n" yellow tag, plus the big name and the amount.
- `count` animates a number counting up (calories, days). `panel` is a dark box with checklist rows that appear on cue.
- `warn` is a red safety banner. `subscribe` is the animated button. A "PART 1/2" badge sits top-right.

**People talking:** there is no lip-sync. The Higgsfield account had 0 credits, so grandma images use Ken Burns motion. If credits exist, image-to-video talking clips could replace those shots.

## Stock footage sources

- **Mixkit** (free, no key, reachable through the proxy): videos `assets.mixkit.co/videos/<id>/<id>-1080.mp4` (falls back to `-720`), SFX `assets.mixkit.co/active_storage/sfx/<id>/<id>-preview.mp3`, music `assets.mixkit.co/music/<id>/<id>.mp3`.
- **Blocked through the proxy:** Pexels, Pixabay and freesound return 403. jsdelivr works for fonts.
- Never use branded store footage (for example Dollar Tree). Use generic grocery aisles and shelves instead.
- `tools/mixkit_catalog.json` has about 500 clip ids with titles. Clips that worked well in this style:

| Topic | Clip ids |
|---|---|
| Storm / power out | 9681 (lightning countryside), 4422, 9704, 25181 (power lines) |
| Snow / winter | 3358 (snowy pines), 3350, 25106, 31942 |
| Candle / dark | 6925 (candle flame), 3458, 21114 (oil lantern) |
| Grocery store | 6204 (woman pushing cart), 6102 (shelves), 14991 (adding food to cart), 22676 (small store), 31969 (price tags), 40174/40176 (groceries from car) |
| Family | 45977 (family dinner), 6472 (three generations walking), 4554 (doctor visit) |
| Rice / beans | 46354 (falling rice slow-mo), 3816 (rice grains), 12579, 12580, 12581 (rice & beans) |
| Cooking | 32608 (pot boiling on campfire), 26344 (boiling pasta), 47624 (raw spaghetti), 48053 (sifting flour), 22022 (serving soup), 24703 |
| Oil / sugar / tea | 13935 (oil bubbles), 47785 (oil pour), 13198 (stirring sugar in tea), 14218 |
| Fire / stove | 30252 (firewood burning), 1242, 17158 |
| Math / time | 28897 (clock on black) |

Avoid vertical clips such as 3352 and 39767, which are 1080x1920.

## SFX ids (in `sfx/`)

| Sound | Id |
|---|---|
| pop | 2358 |
| swoosh | 1485 |
| whoosh | 1491 |
| soft whoosh | 1489 |
| hit / alert | 490 |
| ding | 3116 |
| tick | 1133 |
| click | 1109 |
| bell | 933 |
| impact (hook) | 2908 |
| thunder | 2390 |
| wind | 1157 |
| fire | 1330 |
