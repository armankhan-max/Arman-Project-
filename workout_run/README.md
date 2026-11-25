# POV Cardio Run — 16-minute warm-up (no text, everything procedural)

A first-person runner workout video: you jog in place the whole time and do each move
when its pictogram badge pops (countdown dots tick on the beat).

| Part | World | Moves |
|---|---|---|
| Level 1 | Sunny city rails (3 lanes) | jump, squat-duck, side step left/right, one high-knee sprint |
| Rest 1 | Breathe + water, side reach, arm circles | |
| Level 2 | Underground tunnel | + oncoming trains to dodge, double jumps, electric & saw barriers, 2 sprints |
| Rest 2 | Lunge twist, quad stretch | |
| Level 3 | Sky rail — running on train roofs above the city | gap jumps, step-up jumps, roof-to-roof hops, duck under bridges, 2 sprints |
| Rest 3 | Hamstring fold, side reach | |
| Level 4 | Jungle temple causeway | gaps, fire jets, spikes, spiked logs, spinning blades, low arches, sharp left/right turns, 2 sprints |
| Rest 4 | Arm circles, lunge twist | |
| Level 5 | Lava city (fastest) | everything + 3 HIIT sprints, finish line, fireworks |
| Cooldown | Quad stretch, hamstring fold | |

Everything is generated in code: the 3D worlds (three.js), the pictogram figures,
the music and sound effects (numpy synthesis). There is no on-screen text.

## Build
```
python3 timeline.py          # choreography on a 128 BPM grid -> web/timeline.json
python3 music.py             # soundtrack + SFX -> out/soundtrack.wav
xvfb-run -a -s "-screen 0 1920x1080x24" node render.js 3   # frames -> out/chunks/*.mp4 (resumable)
./assemble.sh                # concat + mux + loudness -> out/pov_cardio_run_16min.mp4
```
Preview single frames: `node snap.js <outdir> <seconds...>` (with a static server on :8765 serving `web/`).
