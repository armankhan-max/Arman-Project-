# The Dream Tax: how this 2D documentary was made

**Video:** `the_dream_tax_2d.mp4` (7:52, 1920×1080, 30 fps, voiceover + score + SFX, −14 LUFS)
**Captions:** `captions_en.srt` (names corrected: Oettingen, Mayer, Kappes, Gollwitzer, Sirois, Pychyl)

## 1. Script → beats → shots
1. **Word-level transcript.** Whisper gives every word a timestamp (`transcript.json`). Each cut, text pop and
   sound effect lands on the word it belongs to.
2. **One idea per beat, one picture per idea.** About 80 scenes. Story beats use characters in sets (hospital,
   bedroom, café, lab). Science beats use clean motion-graphics boards. Quotes get their own dark, quiet frames.
3. **Book-ending.** The film opens and closes on the same patient. On the second visit you understand him.

## 2. The art style (from the reference)
- **Characters:** skin-toned faces, big white eyes with pupils that *look* at things, eyebrows that carry the
  emotion, a nose, and a mouth. Thick dark outlines plus flat cel shading on the side away from the light.
- **Five-finger hands** that change shape with the pose: relaxed, open, fist, pointing, gripping a prop.
- **Painted rim light.** A warm band of light sits *inside* the outline on the side facing the light. It's made by
  taking the silhouette, subtracting a copy shifted away from the light, and painting the leftover edge. This is
  the single biggest "illustrated, not clip-art" trick.
- **Sets:** textured walls (brick, plaster, panelling), perspective floors, then a lighting pass: pools of lamp
  light (screen blend), coloured darkness at the edges (multiply), and a little haze and paper grain.
- **Colour = meaning:** gold/peach = fantasy, cool blue = reality, red = fear and cost, green = the fix.

## 3. Animation
- **Lip-sync:** the host's mouth opening and roundness are measured from the voiceover itself, frame by frame
  (`lips.npy`), so the mouth moves exactly when the voice does and closes in the pauses.
- **Walk/run cycles:** knees bend on the swing, arms counter-swing, the body bobs, and the background scrolls at
  the speed the stride covers the ground, so the feet never slide.
- **Never fully still:** slow camera push-ins, gentle handheld drift, eye blinks, gesture changes every ~1.5 s.
- **Easing:** everything enters with ease-out or a slight overshoot, never linear.

## 4. Text animation
Short kinetic words only (Bebas Neue), and quotes in Playfair Display that appear **word by word as they're
spoken**, with the current word glowing gold. Chapter cards: The Announcement, The Fear, The Fix.

## 5. Sound
Music follows the emotion (hospital drone → warm dream theme → cold reality → curious science → fear tension →
hopeful build → warm close), ducks under the narrator, and drops to silence for the hardest hits ("LAZY?",
the fear reveal). ~170 SFX are placed on words: monitor beeps, stamps, page flips, coin cash, applause, ticks.

## Re-render
```bash
python render.py --audio voice.mp3 --out video.mp4 --jobs 4     # frames → video
python paudio.py --voice voice.mp3 --out mix.wav                # score + SFX + voice
ffmpeg -i video.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -af loudnorm=I=-14:TP=-1 -c:a aac -b:a 192k final.mp4
python render.py --still 120 frame.png                          # preview one frame
```
Files: `pgfx.py` (characters, faces, hands, text), `psets.py` (sets and props), `pscenes_a.py` / `pscenes_b.py`
(the timeline), `ptimeline.py` (scene table), `paudio.py` (soundtrack).
