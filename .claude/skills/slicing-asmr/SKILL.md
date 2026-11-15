---
name: slicing-asmr
description: Make a satisfying "X vs N cuts" ASMR slicing video (single cut, 5, 15, 40, 100, 300, 1000, 10,000 cuts) of any object or product X as a 9:16 720p MP4 with counters and chopping sound, using Blender Python (pip bpy) in the cloud container. Use whenever the user asks for a slicing / cutting / "1 cut vs 1000 cuts" / ASMR cutting animation of some object (fruit, toy, product, anything).
---

# Slicing ASMR video ("1 cut -> 1000 cuts")

The user (Hinglish speaker) wants a video like the reference reels: one object on a board, a knife chops it
more and more, a big cut counter at the top, a cube counter at the bottom, satisfying chop/ting sounds.
They give you only the object **X** (and sometimes the max cut count). Everything else is below, so do not
re-ask or re-derive it.

## User rules (strict, repeated many times)
- **Talk as little as possible.** Their credits run out. No recaps, no long messages. One-word / one-line
  answers when they ask something ("kitna time?" -> "Five (about 4.5 hours)").
- Work in the background and keep going. Do not stop to ask permission for routine steps.
- **One single video only.** No extra variants, no preview videos sent to the user.
- When it is finished send **only the MP4** (SendUserFile, status proactive), no explanation.
- The only question you may ask (once, via AskUserQuestion, short options): **"Kitne cuts?"** if they gave
  no maximum (e.g. 100 / 1000 / 10,000). Object X is given by them; if missing ask "Kaunsa object?".
- If a limit/credit break happens they may say "resume at 14:50": schedule it with `send_later`.

## Output spec
- 9:16 vertical, **1280x720 -> 720x1280** (720p, NEVER 1080p), 24 fps, H.264 yuv420p + AAC 48 kHz.
- **Length 60-65 seconds** (the teddy v2 came out at 56 s: add ~5-8 s via longer holds/intros).
- File name `<object>_slicing.mp4` (teddy one is `teddy_bear_slicing.mp4`).
- **Hook first (2 s):** mid-chop clip of the 100-cut round with a red pill label "1 CUT  vs  100 CUTS";
  then the video starts from cut 0. Never show 1000 in the hook, never the full 100 round.
- Overlay text: huge white number at top + gold "CUTS" label; bottom white cube count + gold "CUBES".
  Cube count shows "≈ 294,000" style approximations for huge numbers. **No other labels / tags / fancy text.**
- Rounds with increasing cuts, each starting from a fresh whole object: 5, 15, 40, 100, 300, 1000
  (add 3000 / 10,000 if the user asks for more). Cuts get faster each round: slow weighty single chops,
  then fast chopping, then machine-gun. After the cuts the object crumbles into the cubes the cuts made
  and settles into a pile (instanced cubes, procedural collapse). Final round ends on a pile close-up.
- Cuts are **vertical (x and y planes) AND horizontal (z planes)**. On the object the cut only shows as a thin
  dark seam line (shader based), the object stays whole until the collapse.
- Style: cute / satisfying, **not scary** (the first teddy video looked creepy: doubled ghost faces from sliding
  slabs, giant knife, garden background. Fixed in v2). Dark brick studio wall, wood cutting board, normal chef
  knife, soft key + rim light, shallow depth of field, AgX tone mapping.
- Sound (all synthesised in `post_v2.py`, nothing downloaded): plush/fruit cut swish, wood tap, crisp chop,
  rising "ting" on counted slow cuts, thinned machine-gun chops, sandy cube-rush + little cube taps on collapse,
  reward chime. Hit time = (frame - 1) / fps, driven by the same event list as the knife and the counter.

## References (this folder)
`references/videos/ref_{onion,chocolate,pomegranate,avocado}.mp4` (360p copies), plus
`references/*_contact_sheet.jpg` frame grids and `references/asmr_cutting_studio_guide.pdf`
(Hinglish "ASMR cutting studio" guide: ONE impact list drives knife + counter + audio, pre-cut pieces whose
seams reveal on blade contact, counter increments on the contact frame, passive board collider, resume-safe
PNG frames, ffmpeg). Look at the contact sheets first; open a video only if needed.
What the references show:
- Onion / avocado / chocolate: counter top ("7 CUTS"), cube counter bottom ("2,149 CUBES", "≈ 127,000"),
  brick wall + light wood board, big knife chopping fast with motion blur, seam lines appear on the object,
  then it collapses into a pile of tiny cubes; each round restarts with a whole object and a bigger count
  (5/7 -> 100 -> 250 -> 1000 ...). Chocolate bar ends with 1,000 cuts / ≈ 24,150,000 cubes = flat powder.
- Pomegranate (Slizzy): title "1 Cut / 3 Cuts / 7 / 13 / 40 / BONUS 100 Cuts", fruit flies apart into
  shards; ends with "What should we cut next? Comment below".
Do NOT copy any brand/logo/name from the references, only the structure and feel.

## Pipeline (code already in the repo, folder `teddy/`)
| File | Role |
|---|---|
| `teddy/teddy_v2.py` | Builds the whole Blender scene (`/opt/bpyenv/bin/python teddy_v2.py --out OUT`): object, studio, knife, per-round timeline (`ROUNDS` list at the top), seam shader, rigid-body pieces for small rounds (5, 15 cuts), instanced-cube collapse for big rounds, bakes, saves `OUT/scene.blend` + `OUT/timeline.json` (per-frame cuts/cubes + event list). |
| `teddy/render_frames.py` | Resume-safe PNG renderer (`--res 720x1280 --samples 12`), skips valid frames. |
| `teddy/post_v2.py` | Synth audio from `timeline.json`, adds hook, PIL overlay, ffmpeg -> `OUT/teddy_bear_slicing.mp4`. |
| `teddy/render_v2.sh` | `render_v2.sh OUT [720x1280] [spp]`: build if missing -> render (3 tries) -> post -> appends `DONE` to `OUT.render.log`. |
| `teddy/teddy_slice.py`, `post.py`, `render_all.sh` | Old v1 (garden, slabs). Reference only, do not reuse the look. |

## How to make a new object X
1. Copy `teddy/teddy_v2.py` to `<x>/x_v2.py`; copy `post_v2.py`, `render_v2.sh`, `render_frames.py` along.
   Change file/output names (`teddy_bear_slicing.mp4` -> `<x>_slicing.mp4`) and the hook text only if the
   user asks.
2. Replace only the **object section** ("the bear": `PARTS`, `classify`, materials `M_FUR/M_BEIGE/...`,
   `MAT_COL`, bounds `XMIN..ZMAX`). Requirements for the new object: parts as meshes with material indices;
   `classify(p, s)` returns a material index (surface colour) or 2 (inner/cut colour) so cubes get the right colours;
   `MAT_COL[i]` = flat colour for cube i; `add_seams` works on any material that has a Principled BSDF.
   Build X procedurally (ellipsoids, curves, bmesh, remesh + displacement for organic things) or import a GLB.
   Make the **inside** realistic (apple = pale flesh, onion rings, chocolate = brown, product = plain grey/white
   foam or whatever fits). Keep the object ~0.4 m tall, sitting on z = 0, centred near the origin.
3. Set the rounds: edit `ROUNDS` (n cuts, frames per cut, intro/gap/after/collapse/hold). Rounds with
   `cap > 0` use coarser instanced cubes and show "≈" counts (needed above ~300 cuts to keep it renderable;
   `cap` is the minimum cube edge in metres). For 10,000 cuts add a round with `n=10000, per≈0.1, cap≈0.0030`.
   Tune the total so frames come to 60-65 s x 24 = 1440-1560 frames.
4. Build, then render 10-12 stills at 360x640 (`render_frames.py OUT --frames ... --res 360x640 --samples 6`),
   tile them with ffmpeg and look: whole object, knife angle, seam lines, collapse, pile. Fix before the full render.
5. Full render: `nohup setsid ./render_v2.sh OUT > OUT.nohup 2>&1 < /dev/null &`. ~15-20 s/frame at 12 spp
   on 4 CPUs (1300 frames ~ 6-7 h). Cycles CPU + OpenImageDenoise via pip `bpy` 5.3 at `/opt/bpyenv/bin/python`
   (system blender 4.0 has no OIDN; download.blender.org is blocked).
6. Keep a keep-alive watcher running (run_in_background, timeout 7200000, loop `until grep -q DONE log ...`)
   and a `send_later` check-in every ~110 min. **The container restarts every few hours and kills the render**:
   after a restart just relaunch the same `render_v2.sh` with the same OUT (frames on disk are kept, it resumes).
   Re-arm the watcher each time (max timeout 2 h).
7. When `DONE`: `ffprobe` (720x1280, audio present, 60-65 s), copy MP4 into the repo folder, commit + push to the
   session branch, SendUserFile the MP4 only.

## Known pitfalls (already solved in the code)
- pip `bpy` must be imported before `bmesh`; Blender 5.x API differences (no RotateEuler, use
  AlignRotationToVector; geometry-node `Value` node keyed instead of group inputs; force fields via
  `bpy.ops.object.effector_add`; `sock(coll, name, type)` to pick sockets by name).
- Knife poses: vertical chops use `ROT_X` / `ROT_Y`, horizontal slices use `ROT_Z` and slide across,
  lifting and returning over the top for slow rounds. Check a 12-frame strip of knife motion before rendering.
- Pile must not look like the original object (looked like a bear): targets are a slumped, spread, window-shuffled
  heap; keep that.
- Do not use slab-sliding cuts, giant knives, or garden scenes (scary / busy).
- Overlay size comes from the real frame size; hook label is a red pill, not plain text.
- Monitor/grep: the "CUEW initialization failed" warning is harmless.
