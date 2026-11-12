"""Write src/data/shots.json (timeline of shots + handle size) from shots.py TIMES and the frames on disk."""
import ast
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = int(sys.argv[1]) if len(sys.argv) > 1 else 6
FPS = 24
src = open(os.path.join(ROOT, "blender", "coinstory", "shots.py")).read()
times = ast.literal_eval(re.search(r"TIMES = (\{.*?\n\})", src, re.S).group(1))
shots = []
for sid, (a, b) in times.items():
    n = round(b * FPS) - round(a * FPS)
    d = os.path.join(ROOT, "work", "frames", sid)
    have = len(os.listdir(d)) if os.path.isdir(d) else 0
    if have != n:
        print("FRAME_COUNT_MISMATCH", sid, "expected", n, "have", have)
    shots.append({"id": sid, "start": round(a * FPS), "n": n})
cont = ast.literal_eval(re.search(r"CONTINUOUS = (\[.*?\])", src).group(1))
diss = ast.literal_eval(re.search(r"DISSOLVE = (\[.*?\])", src).group(1))
ids = [x["id"] for x in shots]
trans = ["none" if (a, b) in cont else "dissolve" if (a, b) in diss else "push" for a, b in zip(ids, ids[1:])]
total = shots[-1]["start"] + shots[-1]["n"]
json.dump({"fps": FPS, "H": H, "total": total, "shots": shots, "trans": trans}, open(os.path.join(ROOT, "src", "data", "shots.json"), "w"), indent=1)
print("shots.json", len(shots), "shots", total, "frames")
