# How this video was made: an editor's breakdown

**Video:** *What If Crows Had Human Intelligence Tomorrow?*, 6:12, 1920×1080, 30 fps

Everything was made in **JavaScript**. Every frame is drawn in code
(Node + `@napi-rs/canvas`), and the whole soundtrack is synthesized in JS.
No stock footage, stock music or templates were used, so the video is 100% original and
royalty-free.

| File | What it is |
|---|---|
| `what_if_crows_were_smart.mp4` | The finished video, ready to upload |
| `captions_en.srt` | Subtitles to upload in YouTube Studio |
| `src/` | The full "project file": characters, sets, scenes, sound, render |

---

## 1. Pre-production: the voiceover is the boss

1. **Transcribe with word timestamps.** Whisper gives the exact second of every
   word. `src/timing.js` has `at('crow lands')`, which returns the time that
   phrase is spoken. **Every cut, text pop and sound effect is placed on a word,
   not on a guessed second.** That's why "TAP" appears exactly when the narrator says
   "tap".
2. **Clean the transcript.** The speech-to-text made mistakes ("For minutes" was really
   "Four minutes", "530" was "5:30"). A professional editor always proofreads the
   captions. One wrong caption looks careless.
3. **Beat sheet.** Split the script into beats, where one beat is one idea and one picture.
   This video has **36 scenes** for 6 minutes. That's a new picture about every
   10 seconds, plus pop-ups inside each scene every 2–3 seconds. This rhythm keeps
   retention high.

## 2. The hook (0:00–0:54)

| Time | Technique |
|---|---|
| 0:00 | **Start in the story, not with an intro.** The bus pulls in and a crow lands. No logo, no "hey guys". |
| 0:06 | **Close-up for the surprise.** The crow speaks. A speech bubble makes it readable even with the sound off. |
| 0:14 | **Split screen** for the "blink / blink back" staring contest. Two shots side by side make a joke land faster than two cuts. |
| 0:23 | **Yesterday vs Today wipe.** The whole premise in one picture. |
| 0:29–0:50 | **Explain the rules on a clean "science board".** Viewers accept fantasy better once they know the limits (no hands, same body). |
| 0:50 | **Title card after the hook,** not before it. By now the viewer is curious, so the title answers "what am I watching?" |

## 3. Visual style (matched to your reference image)

- **Characters:** big round black heads, small cream eyes and brows, one bold
  outfit colour each. Lena wears **blue**, Dev **green with a cap** (straight from
  the reference), Rosa purple, Victor red, the crew orange. *Colour = identity:* you
  know who is on screen even in a wide shot.
- **Rim light:** each character is drawn twice. First comes a warm-orange copy shifted a
  few pixels toward the sun, then the real character on top. That glowing edge
  is the signature of the reference style, and it separates black figures from the background.
- **Cinematic letterbox:** black bars on top and bottom, with a **gold time stamp in
  the top bar** ("6:10 AM", "NOON", "5:30 AM"…), just like "DAY 3" in the reference.
  The time stamps also work as **chapter markers** for the viewer.
- **Captions inside the bottom bar.** The art stays clean, and the spoken word lights up
  gold (karaoke style). That helps the 70%+ of mobile viewers who watch muted.
- **Light tells the time of day:** dawn purple-peach → golden day → noon white →
  sunset pink → night blue → predawn violet → dawn gold for the ending. The light
  quietly tells the story.
- **God rays + floating dust + vignette + film grain** turn flat vector art into
  "film". Grain is only 5%: you feel it more than you see it.
- **Colour coding for information:**
  - Cyan chip **"REAL FACT"** = true science, gold = story beats, red = danger/no.
  - Separating fact from fiction builds trust, which matters for "what if" channels.

## 4. Motion and camera

- **Nothing is ever still.** Every scene slowly pushes in, with a tiny "handheld"
  drift added on top (smooth noise, not random jitter).
- **Punch-in on cuts:** each new shot starts 2.5% zoomed in and settles. This hides
  the cut and adds energy.
- **Easing:** text pops in with a slight overshoot ("back-out" easing), and objects move
  with ease-in-out. Linear motion is the #1 sign of amateur animation.
- **Camera shake only for impact:** "THAT'S THE RULE", "NO.", "NOT SIGNED",
  engines. If everything shakes, nothing feels important.
- **Time slows** (4:33): colours go cool and dark, Pip moves at 20% speed, and the music
  drops to a ticking clock and a heartbeat. You show "slow motion" with *sound* as
  much as with picture.
- **Callback ending:** "A crow never forgets a face" comes back at 5:22 with the
  same framing as before, now with a warm meaning. Book-ending makes a video feel complete.

## 5. Sound design (the half people forget)

Everything is in `src/audio.js`. Mixing order matters:

1. **Voice first.** The voice is polished to sound soft and warm: high-pass at 80 Hz
   (removes rumble), +2 dB at 180 Hz (warmth), −2 dB at 3.2 kHz and −2.5 dB at
   7 kHz (removes harshness), a de-esser (soft "s" sounds), gentle 2.5:1
   compression (even volume), and a very small room echo so it doesn't sound
   "dry in a box".
2. **Music follows the story.** There are 13 cues: a morning piano arpeggio, curious
   pizzicato for the science, a bouncy marimba for the day montage, a warm swell
   for the roost, a music box for the Seattle flashback, a tender piano for Pip's
   "thank you", a tense ostinato for the plan, **near silence + clock + heartbeat**
   for "time slows", a build to a big hit on "NOT SIGNED", a warm resolution, and a
   dark drone for the teaser.
3. **Auto-ducking.** The music drops to about 40% whenever the narrator speaks and
   comes back up in the pauses. That's why the music feels full, yet the voice is always
   clear.
4. **About 120 timed SFX:** whooshes on cuts, pops on text, dings on check-marks, crow
   caws (synthesized with a pitched buzz plus a formant filter), wing flaps, glass
   taps, the phone buzz, the truck rumble, footsteps, a ticking clock, stamp thuds,
   applause, and the like/subscribe clicks.
5. **Ambience beds:** morning wind, night crickets. Silence sounds "fake"; a quiet
   ambience sounds "real".
6. **Loudness:** the final mix is −14 LUFS, true peak −1.5 dB, which is YouTube's target.
   YouTube won't turn your video down, and it won't sound quieter than other channels.

## 6. Re-render it yourself

```bash
cd crows
npm install                 # @napi-rs/canvas
node src/audio.js voiceover.mp3     # → out/mix.wav (music + sfx + polished voice)
node src/render.js --still 12,95    # quick PNG previews of any second
node src/render.js --range 0,20     # preview clip of a time range
node src/render.js                  # full video (all CPU cores) → what_if_crows_were_smart.mp4
node src/srt.js                     # → captions_en.srt
```

Code map:

- `src/lib.js`: easing, text pops, speech bubbles, chips, rays, dust, grain, vignette
- `src/chars.js`: the people (poses, walk cycle, moods, blinking, lip-flap) and the crow (perch, fly, talk, tilt, items in beak, Pip's tail notch)
- `src/sets.js`: backgrounds (terminal, street, park, night bus stop, office, science board) and props (bus, bins, truck, plane tree, traffic light…)
- `src/scenes1.js`, `src/scenes2.js`: the 36 scenes, each keyed to spoken words
- `src/render.js`: the camera, captions, time stamps, finishing, and the parallel ffmpeg render
- `src/audio.js`: the score, SFX, ducking, voice polish and loudness

## 7. Five editor rules from this project

1. **Cut on the word, not on the second.**
2. **One idea = one picture.** If the narrator says a number, show that number.
3. **Show the rules before the fun.** Limits make a "what if" believable.
4. **Use sound to sell time.** Silence, a clock or a heartbeat is stronger than any visual effect.
5. **End with a callback + a question.** It closes the loop and drives comments ("which animal next?").
