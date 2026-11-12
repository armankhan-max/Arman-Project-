# Teddy Bear vs 1000 Cuts: ASMR slicing video (Blender Python)

**Final video:** `teddy_bear_slicing.mp4`. Vertical 9:16, 1080×1920, 24 fps, 20 seconds, ASMR sound, no on-screen text.

## What happens in the video
| Time | Cuts | Shot |
|---|---|---|
| 0–3 s | 0 | Full teddy in the garden, slow camera push-in, knife enters from the top right |
| 3–5.3 s | **1** | Slow vertical cut through the centre, cotton bits fly out |
| 5.5–8 s | 1 | The two halves glide apart and the cotton stuffing shows, close-up |
| 8–11 s | **4** | Three slow slices |
| 11–13.4 s | **10** | Faster slices |
| 13.4–15.8 s | **100** | Rapid chopping, thin slices with white seams |
| 16–18.6 s | **1000** | Dicing pass: the bear turns into plush cubes that tumble onto the table |
| 18.6–20 s | | Close-up of the cube pile |

## Files
- `teddy_slice.py`: builds the whole scene from an empty Blender file: the bear (fur, stuffing, bow tie, eyes, nose, stitched smile), the knife, the garden, the lights, the camera, the cuts, the cube physics and `timeline.json`
- `render_frames.py`: renders numbered PNGs. It skips frames that are already done, so you can stop and restart it.
- `post.py`: makes the ASMR soundtrack from the same impact list (48 kHz WAV), then exports the MP4 with FFmpeg
- `run_build.sh`: runs the builder with either a Blender binary or the pip `bpy` module

## Run it on your PC
```bash
# 1) build the scene, then do a low-res preview first (540x960)
blender -b --factory-startup -P teddy_slice.py -- --out out_prev --preview
blender -b out_prev/scene.blend -P render_frames.py -- out_prev --frames 1,110,180,300,420,470

# 2) final build and full render (1080x1920). Resume-safe: just run it again if it stops.
blender -b --factory-startup -P teddy_slice.py -- --out out_final
blender -b out_final/scene.blend -P render_frames.py -- out_final

# 3) sound + MP4
python post.py out_final        # -> out_final/teddy_bear_slicing.mp4
```

### Low-RAM PC (about 4 GB)
- Cycles CPU with OpenImageDenoise, 512 px tiles, and one frame in memory at a time.
- The fur is geometry-nodes curves, not particles. Lower `FUR_DENSITY` in the config if RAM runs out.
- The `--eevee` flag switches to EEVEE, which is much faster on a GPU.
- `--preview` renders at half resolution with lower fur density.

## How the cuts work
- **One impact list** (`cuts` in `teddy_slice.py`) drives the knife motion, the cut counter in `timeline.json` and every chop sound.
- The bear is **pre-cut once** into 101 slabs along 100 planes. Every seam stays closed until the blade reaches it, so the bear's shape is identical in every frame.
- Every cut surface is filled with cotton stuffing: a white fabric shader, cotton fibres, and fluffy tufts on the centre cut.
- At the 1000-cut stage the bear is rebuilt as about 2,000 cubes. Each face that was on the outside of the bear keeps its fur or face colour, and the inside faces show cotton. The cubes are active rigid bodies falling onto a passive table collider.
