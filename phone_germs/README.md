# Your Phone Is Dirtier Than A Toilet Seat — *Not The Hero* (YouTube Short)

**Final video:** `phone_dirtier_than_toilet_seat.mp4` — 1080×1920, 60 fps, H.264 + AAC 48 kHz, length = voiceover + 0.5 s (40.32 s).

All art is code-drawn SVG in **Remotion (React + TypeScript)**. There are no stock or AI images. Every scene, camera move, caption and SFX is
anchored to a **word** in `assets/words.json`. Nothing is timed with hard-coded seconds.

## Pipeline

1. **Transcribe → `assets/words.json`.** HuggingFace is blocked in this environment, so Whisper (base.en, ONNX via sherpa-onnx, fetched from
   GitHub releases) supplies the exact text (`assets/script.txt`). A zipformer transducer supplies the per-token timestamps. The two
   word lists line up 1:1 (131 words), and the Whisper spelling is kept.
2. **Timeline:** `src/timeline.ts` builds scene boundaries from the scene-plan anchor phrases (`W("so every door handle")` and so on).
   `L(scene, phrase)` gives a scene-local frame.
3. **Components** (`src/components`): `Hero` (rig with IK arms, walk cycle, expressions, blink, breathing, hair/drawstring secondary
   motion), `Germ` (blobby body, 15 cilia wiggling at 7 Hz, 7 expressions, sunglasses, wave), `Phone` (scrolling feed, lock screen,
   glow, shine), `Toilet`, `Props`, `Fx` (skull, stink lines, CLEAN_SPARKLE, ARROW, pop bursts, glows), `Caption`, `Room`.
4. **Camera** (`src/lib/stage.tsx`): a virtual 2D camera (x, y, zoom, rotation, orbit) applied to 4 parallax layers:
   BG ×0.3 with 3 px blur, MID ×0.6, SUBJECT ×1.0, FG ×1.6 with 6 px blur. WHIP_PAN is built in (1.5 screen widths in 8 frames,
   easeInExpo out / easeOutExpo in). Automatic directional motion blur comes from camera velocity, up to 40 px.
   SHAKE, SNAP_ZOOM (easeOutExpo + 2% overshoot), PULL_BACK_REVEAL, DOLLY_TRACK (spring k=120, d=20) and ORBIT_FAKE are recipes in `src/lib/ease.ts` and the scenes.
5. **Audio** (`audio_mix.py`): `src/cues.ts` builds the cue sheet from the same anchors and `dump_cues.ts` exports it to `assets/cues.json`.
   Python synthesizes every SFX (or uses `./sfx/<name>.wav` if you add one) plus an original D-minor "curious/suspense" loop:
   - The voice sits at -14 LUFS.
   - Music sits at -30 LUFS and ducks another 6 dB under speech. Music hits land on "But" and "So the dirtiest".
   - The SFX stem sits at about -18.5 LUFS.
   - Room tone runs under everything, so there is no silence.

## Scene / cut map

| Scene | Anchor | Moves | Cut out |
|---|---|---|---|
| S1 Hook | "Your phone is probably dirtier" | PULL_BACK_REVEAL from zoom 3 on a waving germ; FG toilet roll; SNAP_ZOOM + DANGER on "toilet seat" | cut on action |
| S2 Expectation | "You'd think the toilet" | SLOW_PUSH_IN, SNAP_ZOOM on "dirtiest", dolly to the poke on "touch", ORBIT_FAKE + lid rattle on "waste" | WHIP_PAN |
| S3 Twist | "But toilet seats get scrubbed" | whip in, spray + 5 germ pops, SNAP_ZOOM "disinfectant", CLEAN_SPARKLE; cut on action → phone on sink, SNAP_ZOOM on the laughing sunglasses germ | WHIP_PAN |
| S4 Montage | "every door handle" | side-view DOLLY_TRACK on the hand: door handle → dollar bill → snack (each pops in on its word, GERM_GLOW, germs leap with squash & stretch); FG plant/lamp; taps + SNAP_ZOOMs on "right" / "screen" | MATCH_CUT (phone) |
| S5 Escalation 1 | "your phone stays warm" | pull back into hoodie-pocket cross-section, WARM_GLOW, thermometer, beach germs multiplying, SNAP_ZOOM "germs" | WHIP_PAN |
| S6 Escalation 2 | "carry it into the bathroom" | dolly walk-in, phone on the tank, flush, 60-droplet slow-mo cloud, ORBIT_FAKE, SNAP_ZOOM "land on it" | cut on action |
| S7 Escalation 3 | "press that same screen" | POV from inside the phone; giant face approaches; SHAKE + squish on "face"; green tint; germs squashed, pop back laughing | WHIP_PAN |
| S8 Payoff | "So the dirtiest thing" | clean toilet → PULL_BACK + pan to the phone in hand, ARROW + GERM_GLOW; "a quick wipe": germs fly off with smears, sparkle, ding, lock screen "NOT THE HERO", thumbs up; final push-in matches frame 0 (loop) | loop |

Branding lives inside the world: the hoodie chest, the spray bottle label, the wipes packet and the lock screen.

## Rebuild

```bash
npm install
npx tsx dump_cues.ts                 # cue sheet from word anchors
python3 audio_mix.py                 # -> out/mix_48k.wav
node stills.mjs review 0 120 ...     # review stills
npx remotion render src/index.ts Main out/video_noaudio.mp4 --codec=h264 --crf=16
ffmpeg -i out/video_noaudio.mp4 -i out/mix_48k.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -ar 48000 -shortest phone_dirtier_than_toilet_seat.mp4
```
`remotion.config.ts` points Remotion at the preinstalled Chromium headless shell.

## Notes / deviations
- The spec asks for a "jeans pocket". Because the style lock gives the Hero white tube legs and a hoodie, the cutaway uses the hoodie's kangaroo
  pocket, so the character design stays identical.
- Whisper models could not be downloaded from HuggingFace (blocked by the network policy). The same Whisper weights came from the
  sherpa-onnx GitHub release instead, and a zipformer model supplied the word timestamps.
