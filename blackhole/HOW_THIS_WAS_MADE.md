# How this video was made: a professional breakdown

**Video:** *What If a Black Hole Stretched You?*, 7:03, 1920×1080, 30 fps.

Files:
- `what_if_black_hole_stretched_you.mp4`: the finished video, ready to upload
- `captions_en.srt`: subtitles to upload in YouTube Studio
- `thumbnail_1280x720.png`: the thumbnail
- `YOUTUBE_UPLOAD.md`: title, description with chapters, and tags

This guide explains **why** each choice was made, so you can reuse the thinking
in your own videos.

---

## 1. Pre-production: script → beats → shot list

1. **Transcribe the voiceover with word timestamps.** Every cut, text pop and
   sound effect is placed on the exact word it belongs to. That's why
   "SNAP!" appears and cracks at the same instant the narrator says it.
2. **Split the script into beats.** A beat is one idea, such as "boots
   heavier than helmet" or "coffee floats with you". Each beat gets one clear
   picture. This video has about 32 scenes and 60+ shots.
3. **Choose a shot type for each beat:**
   - **Story beats** use characters in a set, like the bridge, corridor,
     lab, or Mira's room.
   - **Science beats** use a clean diagram on a dark grid board.
   - **Emotional beats** use close-ups, like Kai's face in the helmet.
   - **Comparisons** use a split screen with a jagged divider (seconds vs
     forever, keep the fuel vs spend it).

## 2. The hook (0:00–0:25)

The first 25 seconds decide whether people keep watching. The structure:

| Time | Technique |
|---|---|
| 0:00 | **Start in the middle of the danger.** No intro or logo. Kai is already falling. |
| 0:04–0:12 | **Show, then label.** Big arrows plus short tags ("LONGER", "THINNER"), so the eye gets it instantly. |
| 0:13–0:19 | **Cut to the witnesses.** The crew watching makes the fall feel real. Slow → RED → FROZEN tags build the mystery. |
| 0:19–0:23 | **Split screen: SECONDS vs FOREVER.** The big question of the video becomes one picture. |
| 0:23 | **Rewind to "3 hours earlier".** An open loop: the viewer now *has* to find out how Kai got there. |

The ending replays the hook (5:53–6:10) with the same shots. The second time
it hurts, because now you know Kai. This is called a **callback**, or
book-ending.

## 3. Visual style

- **Rim light.** Every black character is drawn twice: first as a light-blue
  silhouette shifted toward the light, then the real character on top. That
  thin glowing edge separates a dark figure from a dark background. It's the
  signature of this style.
- **Depth of field.** Sets (rooms) are drawn once, Gaussian-blurred, and
  reused. Sharp characters over a soft background tell the eye exactly where
  to look.
- **Color = meaning:**
  - **Orange/red:** danger, the black hole, the stretch.
  - **Cyan/blue:** calm, safety, the ship, "what you see".
  - **Gold:** Mira and love (her hologram, her message).
  - Each character has one outfit color: Kai orange, Tomas green, Yuki
    white/purple, Lena navy/gold, Mira yellow.
- **Outfits:** space-crew jumpsuits replace the hoodie from the references.
  On the spacewalk, everyone wears white suits with a stripe in their own
  color, so you can still tell who is who.
- **Finish:** a soft vignette and light film grain on every frame make flat
  vector art feel like film.

## 4. Motion and camera

- **Never fully still.** Every shot slowly pushes in, and a tiny "handheld"
  drift is added. Static frames feel like slides.
- **Camera shake only for impact:** the fall, the SNAP, the push.
- **Easing.** Text and objects pop in with ease-out or slight overshoot
  ("back-out") instead of linear movement. This is the biggest difference
  between amateur and professional motion.
- **Quick black dips between scenes** (about 0.3 s) give the eye a reset.
- **Lower thirds** introduce each character once: KAI, DR. YUKI, TOMAS,
  COMMANDER LENA, MIRA.

## 5. Sound design

- **Low background music**, about 20 dB under the voice. It also **ducks**
  automatically whenever the narrator speaks.
- **Music follows emotion, not the clock:**
  - dread drone for the hook
  - curious ostinato for the science
  - wonder pads for the 2019 and 2022 history
  - a warm theme for Mira
  - a building ostinato for the spacewalk
  - the warm theme again for the last message
- **Silence is a sound effect.** The music cuts out for the rewind, for the
  **SNAP**, and for the final freeze, so those moments hit harder.
- **About 150 sound effects, each placed on a word or action:**
  - a rimshot on "Professional Joker", a boing on "noodle"
  - a slide whistle when Tomas whistles
  - crickets on "Nobody laughs"
  - helmet breathing during the spacewalk, radio static on comms
  - slowing clock ticks as the probe freezes, and a freeze chime
- **Loudness** is normalized to −14 LUFS, YouTube's standard, so the video
  isn't turned down or sound quiet next to other videos.

## 6. Captions

Captions come as a separate `captions_en.srt` file instead of being burned in:
- the cinematic frame stays clean,
- YouTube indexes the text, which helps search,
- viewers can turn them on or off, and YouTube can auto-translate them.

To burn them in instead, render with `BURN_CAPTIONS=1`.

## 7. Re-render or change things

```bash
python render.py --audio voice.mp3 --out video_voice.mp4 --jobs 4
python audio_bh.py --voice voice.mp3 --out mix.wav
ffmpeg -i video_voice.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy \
       -af loudnorm=I=-14:TP=-1 -c:a aac -b:a 192k final.mp4
```

What each file controls:
- `sgfx.py`: the style kit (characters, outfits, poses, expressions, sets,
  black hole, props).
- `scenes_bh.py`: the timeline. Each scene is a function with absolute
  timestamps.
- `audio_bh.py`: the music cues and sound-effect timeline.
- `thumbnail_bh.py`: the thumbnail.
