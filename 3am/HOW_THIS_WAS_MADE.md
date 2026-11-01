# 3AM Thoughts: an editor's + psychologist's breakdown

**Film:** *3AM Thoughts | An Animated Short Film*, 3:56, 1920×1080, 30 fps, no voice-over.
Every frame is drawn in **JavaScript** (Node + `@napi-rs/canvas`), and the whole soundtrack
(piano, laughter, rain, heartbeat, fridge hum) is synthesized in JS. There are no stock assets,
so it is 100% original and royalty-free.

| File | What it is |
|---|---|
| `3am_thoughts.mp4` | The finished film |
| `YOUTUBE_UPLOAD.md` | Titles, description, chapters, tags |
| `src/` | The full project: characters, sets, phone UI, scenes, sound, render |

---

## 1. The core idea (why this film works)

> **Every mistake from the day comes back at night as a thought.**

That one rule is the whole film. The **day (1:25)** is fast and comic, and it plants 6 small
embarrassments. The **night (2:31)** is slow, and each one returns as a thought. Psychologists call
this *rumination*: the brain replays unfinished or embarrassing moments, and it is loudest when you
are tired and alone. Viewers don't need it explained, because they have **lived it**. That is the
strongest hook there is: *recognition* ("that's literally me").

| Day setup (plant) | Night payoff (callback) |
|---|---|
| Whole class laughs (0:41) | Grey memory bubble "The whole class laughed." (1:42) |
| She waved at the guy behind you (0:56) | "She waved at him, not you." (1:47) |
| Not in the "Squad" photo (0:49) | "They didn't even invite you." (1:52) |
| "Enjoy your coffee!" / "You too!" (1:03) | "You too!?" in the storm, then "Remember when you said 'you too'…" (3:40) |
| Declined Mom's call (1:11) | The callback: "Sorry I missed your call. Love you." (3:24) |
| Same classroom laughed at you | In Imagination Mode the **same classroom cheers for you** (2:07) |

**Editor rule: never show a payoff you didn't plant.** And when you do plant something, pay it off.
The audience feels a click every time a callback lands.

## 2. Structure and pacing

- **Cold open = an open loop (0:00–0:08).** A giant shadow with red eyes and the line *"How did today get this bad?"*
  The viewer now has a question, and the brain hates unfinished questions (the *Zeigarnik effect*).
  Then a **VHS rewind** takes us back to 7:42 AM. We promise an answer and make them wait for it.
- **Fast day, slow night.** Day shots last 4–8 s, with running, speed lines, quirky pizzicato at 150 BPM.
  Night shots last 6–15 s, with ticking clocks and single piano notes. *The edit rhythm itself tells
  you how time feels*: the day flies, the night drags.
- **The title arrives late (1:16),** over the lonely rain walk home, the first quiet moment. By then the viewer
  is invested, so the title feels like a chapter break instead of an intro to skip.
- **Gold time stamps in the top bar** (7:42 AM → 6:12 PM → 3:07 AM → 3:58 AM) work as a clock
  the viewer reads without thinking. The clock moves forward all night, so you *feel* sleep
  disappearing ("Sleep now = 3 hours 41 min").
- **Escalation then release.** Replay (3 bubbles) → Drift → Storm (bubbles every 0.12 s, shadow
  covers the ceiling) → **Phone dies: total darkness, only breathing.** Silence after chaos hits
  harder than any effect. That's the turning point.

## 3. The psychology inside the story (my additions)

These beats come from real coping tools, shown instead of lectured:

1. **The shadow = anxiety made visible.** It grows with every replayed thought, and it
   shrinks when he does something real (water, writing). An abstract feeling becomes something you can see.
2. **"You put it down." (2:35).** He resists the urge and the film rewards it. In therapy, *naming the win*
   reinforces the behaviour. The 3AM fact card explains why urges are strongest when you're
   tired (the brain's "brakes" are weakest).
3. **Grounding (3:04).** "Cold water. Cold floor. Fridge hum." Noticing 3 real things pulls the brain
   from *what if* back to *what is*. The stubbed toe is a comic beat, but it's also grounding:
   pain is very *present*.
4. **Cognitive offloading (3:07).** He writes the worries down, and each one shrinks to one line.
   Studies found that people who wrote a to-do list before bed fell asleep faster.
5. **The reframe: "One bad day. Not a bad life."** This is the thesis of the film, underlined in red.
6. **Connection beats rumination.** He replies to Mom, and she's awake too: *"Bad day? Me too."*
   The split screen shows two lonely rooms becoming one moment. Loneliness is a big driver of
   3 AM spirals, so the cure is shown as a person, not a tip.
7. **The ending isn't "fixed forever".** The next night the shadow climbs again and the thought comes back.
   This time he **smirks**, flips to the cold side and says *"Not tonight."* That's honest, and honesty is
   why people share films like this.

## 4. Visual language

- **White stick figure** (from your reference): cream pill body, big round head, heavy lids and
  **eye bags** that show tiredness without a single word. In the dream scenes the bags disappear,
  because the dream-self is the version he wishes he was.
- **Rim light:** blue from the phone at night, warm orange in the dream scenes and with Mom.
  It separates a white figure from a dark room and tells you where the light comes from.
- **Continuity props:** the coffee stain on his white shirt stays all day, and the rain soaks him from
  the bus scene on. Small details make the audience trust the world.
- **Colour = emotion:**
  - morning cream
  - grey rain
  - night navy
  - **warm red for temptation**, with edges blurring like tunnel vision
  - fridge-light amber for calm
  - warm lamp for Mom
- **POV phone shots** put the viewer's own hands on the phone. With no narrator, the phone is the
  narrator: battery 31% → 24% → 4% → dead is a countdown nobody needs explained.
- **Grey flashbacks inside thought bubbles:** the night *re-renders the actual day scenes*. They are
  literally the same frames, de-saturated. It's a real memory, not a new picture.

## 5. Sound design (the half people forget)

- **Silence is an instrument.** Phone dies → 5 s of black with 3 breaths. "Blank mind" in class →
  a thin tinnitus tone. The record skip that cuts Imagination Mode. All of these are *absence* of sound.
- **One main theme** (Am–F–C–G, a simple 8-note piano melody) appears 5 times:
  - the rain walk / title
  - "one song"
  - triumphant in Imagination Mode
  - tender during the callback
  - final on the end card

  Repetition makes a melody feel like *memory*.
- **Comedy timing:** music hard-stops for gags (bus doors "BONK", "You too!" record scratch,
  crickets after the wave). A gag lands in the silence after it.
- **Heartbeat speeds up** through the replay, the drift and the storm (from 1.1 s to 0.38 s per beat),
  so the viewer's body tenses before the brain notices.
- **Loudness:** two-pass *linear* normalisation to −16 LUFS. Quiet moments stay quiet and loud ones
  don't get squashed. For a quiet emotional film that matters more than being loud.

## 6. Re-render it yourself

```bash
cd 3am
npm install
node src/audio.js                       # → out/mix.wav (score + SFX)
node src/render.js --still 12,95,180    # PNG previews of any second → out/stills
node src/render.js --range 85,101       # preview clip of a time range
node src/render.js                      # full film (all cores) → 3am_thoughts.mp4
```

Code map:

- `src/tl.js`: the **master timeline**. Change one number here and picture *and* sound move together.
- `src/guy.js`: the white figure (15 moods, walk, blink, sit, fall), POV hands + phone
- `src/sets.js`, `src/sets2.js`: bedroom (day/night), bathroom, kitchen, street (morning/rain/night), bus, classroom, cafeteria, café, Mom's room, dream sets
- `src/screens.js`: phone UI (lock screen, music, call, group chat, feed, low battery, chat)
- `src/day.js`, `src/night.js`: every scene
- `src/audio.js`: the cue sheet; `src/audio_base.js`: the synth instruments

## 7. Seven rules to steal

1. **Plant in the day, pay off at night:** setups and callbacks.
2. **Open with the question, not the answer** (cold open + rewind).
3. **Edit rhythm = emotion:** fast cuts for chaos, long holds for loneliness.
4. **Make the invisible visible:** anxiety is a shadow, time is a battery.
5. **Use silence after chaos;** it is louder than any sound effect.
6. **Show coping, don't preach it:** water, a pen, one text message.
7. **End honest, not perfect:** the thought comes back, he just answers it differently.
