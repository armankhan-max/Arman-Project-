# How this explainer was made

**Video:** *Why Mercury Is the Coldest Planet*, 7:21, 1920×1080, 30 fps.
Every frame is drawn in **JavaScript** (Node + `@napi-rs/canvas`), and the music and SFX are synthesized in JS.
There is no stock footage, so it's 100% original.

| File | What it is |
|---|---|
| `why_mercury_is_the_coldest_planet.mp4` | The finished video |
| `captions_en.srt` | Subtitles for YouTube |
| `YOUTUBE_UPLOAD.md` | Titles, description, chapters, tags |
| `src/` | The project: timing, B-roll kit, scenes, sound, render |

## 1. Voice first

1. **Transcribe with word timestamps** (Whisper). `src/timing.js` gives `at('melt lead')`,
   the exact second that phrase is spoken. **Every cut, number, chart and sound effect is placed on a
   word.** When the narrator says "seven times", 7 suns pop in, one by one.
2. **Proofread the transcript.** "hand standing" was really "and standing", and the spacecraft is
   spelled MESSENGER. Wrong captions look careless.
3. **Beat sheet:** 58 scenes in 7:21. That's a new picture every ~7.5 s, with text or a number
   changing inside each scene every 2–3 s. That's the pace YouTube explainers need to hold retention.

## 2. What "B-roll" means in a 2D explainer

In live action, B-roll is footage that *shows* what the narrator *says*. Here every line has a picture:

| Narration | B-roll |
|---|---|
| "150 million km… only 58 million" | Distance arrows that grow while the numbers count up |
| "seven times stronger" | 1 sun over Earth vs 7 suns over Mercury |
| "melt lead" | A grey lead bar slumping into a puddle, plus a "LEAD MELTS AT 327°C" fact chip |
| "colder than a freezer… Antarctica" | A bar chart: −18°C → −89°C → −180°C |
| "works like a blanket" | A literal quilt wrapping Earth; heat dots bouncing back |
| "charged particles strip away gas" | Solar-wind streaks; gas dots blown off; the blanket flies away |
| "176 Earth days" | A day/night timeline bar (88 + 88) and 3 dark calendar pages |
| "the Sun rises, stops, goes backward" | The Sun actually does that, word by word, with labels |
| "wrinkles like a drying apple" | The crust wobbles while an apple shrivels in an inset |
| "light never reaches the floor" | A crater cross-section with a low sun and a shadow wedge |
| "delivered by comets" | A comet hits the crater; ice appears on the floor |

**Rule:** if the narrator says a number, show the number. If they compare two things, show both side by side.

## 3. Text animation toolkit (`src/space.js`)

- **kinetic():** slam-in words (scale 1.8 → 1 with a punch). Used for big beats: *BURNING*, *NO MERCY*.
- **typeOn():** typewriter text for questions and calmer lines.
- **counter():** numbers that count up (150 MILLION KM, 610°, 176 EARTH DAYS). Numbers feel *earned*.
- **factChip():** small coloured pills ("EXOSPHERE", "RADAR FROM EARTH"). Cyan means fact, orange means heat.
- **strike():** a red line through a wrong idea ("CLOSEST = HOTTEST", "COLDEST PLANET?").
- **stamp():** rubber-stamp words ("NOT PEACEFUL", "NOT EVEN CLOSE").
- **Karaoke captions** in the bottom bar, with the spoken word in gold, plus a **section tag** in the top bar
  (REASON #1: NO AIR…). The viewer always knows where they are in the argument.

## 4. Story tricks in the script (and how the edit supports them)

- **Open loop:** "something frozen that should not exist". We show a dark crater with a "?" and a
  "REVEALED AT THE END" chip, then pay it off at 5:24 by unlocking the padlock on the same crater.
- **Numbered reasons** (#1 air, #2 time, #3 soil). Each one gets its own colour mood and section tag.
- **The honest twist** (Uranus holds the record). The title card comes back with an asterisk,
  and the verdict crosses out "COLDEST". Admitting it builds trust.
- **Recap montage** (4 tiles: heat, freezing, cracking, backward Sun) right before the big reveal.
- **Teaser ending** (a hidden "?" planet). It drives the next click.

## 5. Sound

- The voice is polished (EQ, de-esser, gentle compression), and the music **auto-ducks** to 40% under it.
- Each section has its own cue: tense pulse (hook), curious arpeggio (facts), cold bells (night side),
  clock ticks (reason #2), wonder pad (sunrise), radar pings and a big shimmer for "MERCURY HAS WATER ICE".
- Whooshes on every cut, booms on kinetic words, tape-stops when the Sun "stops".
- Final loudness is −14 LUFS (YouTube's target).

## 6. Re-render

```bash
cd mercury
npm install
node src/audio.js                 # → out/mix.wav
node src/render.js --still 50,354 # preview stills → out/stills
node src/render.js                # full video → why_mercury_is_the_coldest_planet.mp4
node src/srt.js                   # → captions_en.srt
```
