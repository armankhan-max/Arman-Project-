# Style bible: "2D character in a 3D world" shorts

Standing reference for every video in this style. Built from a frame-by-frame study
of four reference shorts (Pink Prison Cell, Winning Tickets, Job Nobody Wants in
Japan, Burglar Who Moved Furniture): 2 frames per second over the full length, plus
15 fps on the transitions and a loudness/onset pass on the audio.

**Trigger words:** "2D video in 3D world", "short in this style", "camera movement /
BGM / SFX like the references" all mean: follow this file.

## 1. Format

- 9:16, 1080x1920, 30 fps, 58 to 65 seconds.
- Starts on the first word. No logo, no title card, no fade in.
- Ends on the punchline word. No outro.

## 2. World (3D)

- Real 3D sets with perspective: rooms with floor, walls, ceiling, props you can
  fly around. Simple low-poly shapes.
- Flat cel colours, 2 or 3 tone steps, bold dark ink outline on every object.
- Saturated palette. One strong colour identity per location (pink cell, blue-green
  prison, yellow kitchen, navy office) so the viewer knows where they are instantly.
- Lighting carries mood: hard window light shafts and soft cast shadows on the
  floor by day; deep blue/purple with warm practical lights (lamp, lantern, window,
  flashlight pool) by night.
- Characters cast real shadows onto the 3D floor. This is what glues 2D into 3D.
- Every set carries readable gag props: labels, notes, signs ("DON'T MOVE!",
  "DESK STUFF", "CAREER DEVELOPMENT ROOM"). At least one joke per set that is never
  said out loud.

## 3. Characters (2D)

- Flat 2D drawings standing in the 3D set like cards, always facing camera.
- Big round head, small simple body, thin limbs, thick black outline.
- Face does all the acting: dot eyes, half-lid suspicion, wide panic eyes, closed
  happy arcs, gritted square teeth, small "o" mouth, sweat drops, thick brows.
- Expression changes are instant (1 to 2 frames), never slow morphs.
- Poses are held and snapped, with a small bounce on arrival. Limbs are rubbery.
- Each character has one colour and one identifying item (cap, tie, lanyard).
- **Main character (ours):** round brown head, dark bowl hair with a small tuft,
  thick short brows, round white eyes with black pupils and a highlight, small nose
  curl, teal hoodie with white inner tee and drawstrings, darker pocket, navy
  pants. Bold outline added so he sits in the 3D world. Rig: `src/char.js`.
- Supporting cast uses the same rig with other skin, hair, top colour, and a hat.

## 4. Camera (the most important part)

- **One continuous shot.** The camera never hard-cuts. It travels through the world.
- Rhythm is always **move, settle, move**: a fast eased move of 0.5 to 0.9 s, then
  a 1 to 2.5 s hold. A hold is never frozen: it keeps a slow push in or drift.
- About 22 to 28 camera moves per 60 s. One new picture every 2 to 3 seconds.
- Move types seen in the references:
  - Push in to a detail (label, face, button, clock) on the exact word naming it.
  - Pull out to reveal the wider situation or the joke.
  - Whip pan between two things in the same space, with motion blur.
  - Fly through: door, window, wall, floor, roof, to change location without a cut.
  - Top-down and steep high angles for layouts; low angles for threat or size.
  - Giant scale jumps: room, roof, aerial of the town, and back down.
  - Snap zoom on a shock beat (0.3 s).
- Moves ease in and out. Never linear, never constant speed.
- When a real location change is unavoidable, it is hidden: a 4 to 6 frame
  cross-dissolve inside a fast move, or a wipe by an object crossing the lens.
- Framing: subject sits in the upper-middle. The band around 68 to 72% height is
  kept clear for captions.
- Slight wide-lens feel up close: big foreground objects, strong perspective.

## 5. Visual scripting

- One sentence equals one or two pictures. The picture shows the noun at the
  moment it is spoken.
- Hook in the first 2 seconds: the strangest image of the story, already in motion.
- Show the mechanism, do not tell it: numbers light up, the string is followed
  from finger to bell, the stopwatch fills the frame.
- Exaggerate for comedy: literal visual metaphors, absurd scale, deadpan reactions.
- A reaction face follows each reveal, held about half a second.
- Dialogue lines are acted: mouth flaps on the syllables, with a shrug or point.
- The last shot is the twist, held 1 to 1.5 s, then stop.
- Per shot, decide: what moves in the background, what the character does with
  hands, what the eyes look at, what the one funny prop is.

## 6. Captions

- 1 to 2 words at a time (3 only for short words), in sync with the voice.
- Heavy rounded white sans, thick black outline, soft drop shadow.
- Centred at about 70% of frame height. Sentence case, punctuation kept.
- Each chunk pops in from about 86% to 100% scale in 3 frames. No colour changes,
  no emoji, no boxes.

## 7. Sound

Measured on the references: loudness stays almost constant (voice always present,
under 1% silence), with roughly 3 distinct sound hits per second.

- **Voice:** fast, dry, deadpan male narrator, around 190 to 200 words per minute.
  No pauses longer than about 0.3 s. Loudest element.
- **BGM:** light, sneaky or playful bed (pizzicato, mallets, soft percussion),
  well under the voice. It changes with the story: thins out for the mystery,
  tightens for the escalation, drops out for a beat before the twist.
- **SFX on everything.** Rule: if it moves, it makes a sound.
  - Whoosh on every camera move, pitched up for rises and down for dives.
  - Pop or blip when something appears, a light switches on, eyes snap open.
  - Foley for every action: footsteps, thuds, slams, pours, scratches, clicks.
  - Signature sound of the story object (bell, stopwatch tick, scratch).
  - Ambience per location (night crickets, office hum), muffled when the camera
    goes inside or underground.
- SFX land on the frame of the action, not near it.

## 8. Mistakes to avoid

- Hard cuts or fades to black between shots.
- A static camera, or constant-speed (linear) camera moves.
- A flat 2D background with no perspective, or characters with no floor shadow.
- Characters without outlines, or slow floaty expression changes.
- Full-sentence subtitles, or captions sitting on top of the subject's face.
- Silent moves. Any camera move or action without its sound.
- Empty sets with no gag props.
- Explaining with on-screen text what a picture could show.
- Long holds past 2.5 seconds with nothing new.

## 9. Workflow for a new video

1. Script with word timestamps (voiceover file or timed transcript).
2. Beat sheet: one row per sentence with picture, camera move, expression, prop
   gag, SFX.
3. Build the 3D sets in one connected world so the camera can travel between them.
4. Key the camera first (move, settle, move), then act the characters to the words.
5. Preview stills at every beat, send frames for review, then render.
6. Audio: voice, then SFX on every cue time used by the picture, then BGM under.
7. Push the video to the repo.

## 10. Engine in this folder

- `src/char.js`: the 2D character rig (canvas).
- `src/main.js`: 3D world, camera keys, acting, captions (three.js, toon shading,
  ink outlines, shadows, motion blur on fast moves).
- `render.mjs`: renders frames with headless Chromium.
- `audio.py`: synthesized BGM and SFX on the same cue times.
- Setup: `npm install`, then `node render.mjs --out frames` and
  `python3 audio.py mix.wav`, then join with ffmpeg.
