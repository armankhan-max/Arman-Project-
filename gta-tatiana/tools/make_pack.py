#!/usr/bin/env python3
"""make_pack.py <part number>
Builds voice-video/parts/partNN/footage/ for a run: every clip of the footage library (hard links, no copies),
contact sheets per source (one labelled middle frame per clip), README.md (how to mix, the clip list, facts,
clips already used in earlier parts), then the owner's images (add_images.py)."""
import json, os, subprocess, sys
from pathlib import Path

T = Path(__file__).resolve().parent; J = T.parent / "voice-video"
n = int(sys.argv[1]); lib = J / "footage" / "library"
dest = J / "parts" / f"part{n:02d}" / "footage"
subprocess.run(["rm", "-rf", str(dest)]); (dest / "clips").mkdir(parents=True); (dest / "sheets").mkdir()
book = json.loads((lib / "library.json").read_text())
names = sorted(k for k in book if (lib / f"{k}.mp4").exists())
for k in names:
    os.link(lib / f"{k}.mp4", dest / "clips" / f"{k}.mp4")
TITLES = {"L": "Launch Trailer", "T1": "Trailer 1", "T2": "Trailer 2", "X": "An Extended Look (gameplay showcase)"}
for tag in TITLES:
    grp_all = [k for k in names if k.split("-")[0] == tag]
    for p in range(0, len(grp_all), 30):
        grp = grp_all[p:p + 30]; ins = []
        for k in grp:
            ins += ["-i", str(lib / "sheets" / f"_{k}.jpg")]
        lay = "|".join(f"{(j % 6) * 384}_{(j // 6) * 216}" for j in range(len(grp)))
        fc = f"xstack=inputs={len(grp)}:layout={lay}:fill=black" if len(grp) > 1 else "null"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc,
                        str(dest / "sheets" / f"{tag}-p{p // 30 + 1}.jpg")], check=True)
used = []
for m in range(1, n):
    for u in (J / "parts" / f"part{m:02d}" / "used-clips.txt", J / "parts" / f"part{m:02d}" / "run" / "used-clips.txt"):
        if u.exists():
            used += u.read_text().split()
guide = subprocess.run(["python3", "-c", "import sys;sys.path.insert(0,sys.argv[1]);import pack;print(pack.GUIDE)",
                        str(Path.home() / ".claude/skills/gta/scripts/footage")], capture_output=True, text=True).stdout
facts = json.loads((J / "footage" / f"part{n:02d}.json").read_text()).get("facts", [])
txt = guide + f"""
## The footage library for this part

`clips/` holds {len(names)} real clips cut at measured shot changes from Rockstar's official videos
({', '.join(f'`{k}-`: {v}' for k, v in TITLES.items() if any(x.startswith(k + '-') for x in names))}).
`sheets/` shows one labelled middle frame of every clip (name and length). **Look at the sheets first**, then pick
the clips that fit the words of THIS part (often 30 to 50 picks for a 70 to 90 s part; footage cuts every 1 to 2.5 s).
Clips are 0.7 to 8.5 s; use only the part you need. Before using a clip, look at its first and last frame:
skip any frame with a title card, a logo card, a rating card, a date card other than NOVEMBER 19, 2026, or a
watermark. Some Trailer 1 shots are framed like social media posts with their own captions: use those only
where that look fits, never for reading text.

**When you are done, write `used-clips.txt` in the run folder: the names of the clips you used, one per line.**

### Do not reuse these clips (used in earlier parts)
{' '.join(used) if used else '(none yet: this is the first part)'}

## Facts to keep right on screen
""" + "\n".join(f"- {f}" for f in facts) + """

## Sources to credit
Rockstar Games: Grand Theft Auto VI Trailer 1, Trailer 2, Launch Trailer, An Extended Look (official videos).
"""
(dest / "README.md").write_text(txt)
subprocess.run(["python3", str(T / "add_images.py"), str(n)], check=True)
print("pack", n, len(names), "clips,", len(used), "used before")
