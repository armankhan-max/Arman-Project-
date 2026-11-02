# How this video was made

**Video:** *The Day the Ground Came Back: Christchurch 2011*, about 21 minutes, 1920×1080, 30 fps.
Realistic documentary style, built from your script and the two reference videos.

## 1. What I took from your references

**Reference 1 (Picher tornado). This set the main editing style.**
- Fast documentary cutting: a new shot every 3–6 seconds, cut on the narrator's words.
- Dark, desaturated satellite maps with **red markers, red rings, dashed distance lines and
  label boxes** (zone outlines, "200 ft" measurement callouts).
- **Red typewriter date and time stamps** ("May 10 2008", "5:38 PM CDT") → here: *12:51 PM*,
  *4 SEPTEMBER 2010 / 04:35 AM*, *22 FEBRUARY 2011*.
- Big red keyword slams ("DECADES", "Toxic Waste Site") → here: *UPWARD*, *IT WASN'T.*, *SMOKE.*,
  *IT FALLS.*, *RED ZONE*.
- A heavy vignette, film grain, and a moody, desaturated grade.

**Reference 2 (Gault site). This set the text and animation style.**
- Serif **lower thirds** with a thin line wipe (*HENRY GAULT / Landowner, c. 1900*) → here:
  *COLOMBO STREET*, *CTV BUILDING / Madras Street*, *TIMEBALL STATION*, and others.
- Map pins with angled label lines (*Gault Site*) → the map markers here.
- A big serif title card (*50 Years Beneath the Surface*) → *THE DAY THE GROUND CAME BACK*.
- Slow Ken Burns moves on every still, plus document close-ups → the Royal Commission report shot.

## 2. B-roll

The cloud machine that made this video could not reach stock-footage or image sites. So every
B-roll shot is a **3D CG reconstruction**, built in code with Blender (Cycles path tracer):
- 74 camera shots across 41 scenes: Colombo Street before and after, the cathedral intact and
  collapsed, the CTV and PGC buildings standing, collapsed, on fire, and under night rescue,
  liquefaction streets, the Port Hills, Lyttelton harbour, the Timeball Station, the Sumner cliffs, a
  boulder through a house, the Grand Chancellor leaning, the Student Volunteer Army, red-zone
  cordons, the container mall, the Cardboard Cathedral, the memorial wall, and more.
- Physical sky lighting, volumetric dust, smoke and fire, and depth of field.
- The sky is rendered transparent and replaced in the compositor with cloudy skies that match each
  shot's mood.

**To use real archival footage:** `edl.py` lists every shot by paragraph. Replace any
`pl("plate_name", ...)` with your own clip, or drop a same-named PNG into `build/plates/` and
re-render.

## 3. Motion and grade

- Every plate gets a slow push in, push out, pan or tilt, plus a subtle handheld drift.
- **Earthquake shakes** are tied to words ("moved upward", "tears open", "gives way", "hammer
  blow"). The motion is mostly vertical, because the February quake hit upward. Strong hits add
  motion blur, chromatic aberration, a white flash, and falling debris particles.
- Each scene has a grade that carries meaning:
  - *memory*: cool and washed out, for September 2010
  - *disaster*: dusty and desaturated
  - *night*: blue
  - *mourn*: almost black and white
  - *hope* and *dusk*: warm, with light leaks

## 4. Text animations

There are 56 on-screen text events:
- typewriter date stamps, with a key click for each letter
- red and white keyword slams, with a hit and a whoosh
- serif lower thirds
- five chapter cards
- the main title card
- callouts with leader lines ("6 FLOORS", "STAIRWELL TOWER", "LEANING")

## 5. Explainer graphics

- Maps: New Zealand zooming to Christchurch, Darfield at 40 km, aftershocks month by month, the
  hidden Port Hills fault, the February epicentre 10 km away, the two buildings, the liquefaction
  zone, and the red zones.
- Seismograph traces.
- Gravity vs. 2.2 g bars.
- 7.1 vs. 6.2 comparison (about 20× less energy).
- Depth cross-section and building sway diagram.
- Liquefaction animation: grains, water, a sinking house.
- A ticking clock up to 12:51.
- Memorial counters (115, 18, 185) and the NZ$40 billion cost.
- A world map of the international rescue teams.
- The John Key quote card, the "four reasons" board, and the report document.

## 6. Sound

- **Voice:** Kokoro TTS, male voice `am_michael`, at speed 0.93. The narration is processed with
  EQ for warmth and presence, compression, and a light room reverb.
- **Music:** an original synthesized score. It moves through:
  - a dark drone and sparse piano for the night of September 2010
  - a ticking pulse for the science
  - taiko impacts for 12:51
  - strings and piano for the grief
  - a warm build for the recovery

  The music ducks under the voice and drops to silence for "It wasn't.", "12:51 PM", "It falls."
  and "Smoke."
- **SFX:** about 200 placed sounds, all synthesized: earthquake rumbles, debris, bricks, glass,
  cracks, car alarms, sirens, fire, tapping, cutting saws, rockfall, shovels, typewriter keys,
  clock ticks, booms and whooshes.
- **Ambience** is set per scene: city, night crickets, wind and dust.
- **Master:** loudness is normalized to −14 LUFS, YouTube's standard.

## 7. Re-render

```bash
./render.sh            # full pipeline (about 1–2 h on 4 CPU cores)
```

| File | What it does |
|---|---|
| `script.txt` | the narration |
| `tts.py` | the voice |
| `bl_kit.py`, `plates.py` | the 3D B-roll |
| `edl.py` | the edit: shots, text, shakes and SFX, per paragraph |
| `comp.py` | the compositor (grade, moves, shakes, text) |
| `gfx2d.py` | the maps and diagrams |
| `sound.py` | the music, SFX and mix |
| `captions.py` | the captions |
