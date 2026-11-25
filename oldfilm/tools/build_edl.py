"""shots.txt + pools.py -> edl.json (edited-audio timeline)."""
import sys, os, json, random, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plan"))
from timemap import o2e
import pools
import subprocess

FALLBACK = {}
MIN_SHOT = 1.7
total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", "voice_edit.wav"]))

rows = []
for line in open("plan/shots.txt"):
    if not line.strip() or line.startswith("#"): continue
    t, pool, note = (line.rstrip("\n").split("|") + [""])[:3]
    rows.append([o2e(float(t)), pool.strip(), note.strip()])
# times -> intervals
shots = []
for i, (t, pool, note) in enumerate(rows):
    if pool == "END": break
    end = rows[i + 1][0] if i + 1 < len(rows) else total
    if rows[i + 1][1] == "END": end = total
    shots.append({"start": t, "end": end, "pool": pool, "note": note})
shots[0]["start"] = 0.0
# merge too-short shots into the previous one (never into black)
merged = []
for s in shots:
    if merged and (s["end"] - s["start"]) < MIN_SHOT and s["pool"] != "black" and merged[-1]["pool"] != "black":
        merged[-1]["end"] = s["end"]; continue
    merged.append(s)
shots = merged
# split very long shots so no still sits > 9 s
out = []
for s in shots:
    d = s["end"] - s["start"]
    if d > 9.5 and s["pool"] != "black":
        n = int(d // 6.5) + 1
        for k in range(n):
            out.append(dict(s, start=s["start"] + d * k / n, end=s["start"] + d * (k + 1) / n))
    else:
        out.append(s)
shots = out

rng = random.Random(42)
order = {}
recent = collections.deque(maxlen=10)
missing = collections.Counter()
for s in shots:
    lst = pools.P.get(s["pool"]) or []
    lst = [x for x in lst if ("img" not in x) or os.path.exists(x["img"])]
    if not lst:
        missing[s["pool"]] += 1
        lst = [x for x in pools.P["sea_dawn"] if ("img" not in x) or os.path.exists(x["img"])]
    key = s["pool"] if pools.P.get(s["pool"]) else "sea_dawn"
    if key not in order:
        o = list(range(len(lst))); rng.shuffle(o); order[key] = [o, 0]
    o, k = order[key]
    # pick next not recently used
    pick = None
    for j in range(len(o)):
        cand = lst[o[(k + j) % len(o)]]
        sig = json.dumps(cand, sort_keys=True)
        if sig not in recent:
            pick = cand; order[key][1] = (k + j + 1) % len(o); break
    if pick is None:
        pick = lst[o[k % len(o)]]; order[key][1] = (k + 1) % len(o)
    recent.append(json.dumps(pick, sort_keys=True))
    src = dict(pick)
    if "vid" in src:
        d = s["end"] - s["start"]
        span = src["t1"] - src["t"]
        if span > d + 0.5:
            off = rng.uniform(0, span - d)
            src["t"] = round(src["t"] + off, 2)
    s["src"] = src
# chapter breaks
for i, s in enumerate(shots):
    if s["pool"] == "black":
        s["cut"] = True
        if i > 0: shots[i - 1]["fade_out"] = 12
        if i + 1 < len(shots):
            shots[i + 1]["cut"] = True; shots[i + 1]["fade_in"] = 15
shots[0]["fade_in"] = 20; shots[0]["cut"] = True
shots[-1]["fade_out"] = 40
# extra hard-cut split points for parallel rendering (every ~70 shots)
for i in range(60, len(shots), 70):
    shots[i]["cut"] = True
json.dump(shots, open("plan/edl.json", "w"), indent=0)
print("shots", len(shots), "missing pools:", dict(missing))
durs = [s["end"] - s["start"] for s in shots]
print("avg %.2f min %.2f max %.2f" % (sum(durs) / len(durs), min(durs), max(durs)))
