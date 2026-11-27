import sys, os, json, random, collections
sys.path.insert(0, "plan")
import pools
rows = json.load(open("plan/timeline.json"))
rng = random.Random(7)
SHOT = 5.2
shots = []
for i, r in enumerate(rows):
    a = r["start"]; b = rows[i + 1]["start"] if i + 1 < len(rows) else r["end"] + 2.5
    d = b - a
    if r["pool"] == "black" or not r["text"]:
        shots.append({"start": a, "end": b, "pool": "black", "cut": True}); continue
    n = max(1, round(d / SHOT))
    for k in range(n):
        shots.append({"start": a + d * k / n, "end": a + d * (k + 1) / n, "pool": r["pool"], "row": i})
    ov = r.get("ov", "")
    if ov:
        if ov.startswith("tag:"):
            l1, l2 = ov[4:].split("/", 1); o = {"kind": "tag", "a": l1, "b": l2}
        else:
            n_ = int(ov.split(":")[1]); o = {"kind": "depth", "n": n_, "a": "Boxcar red" if n_ == 61 else "Depth"}
        nb = next((rows[j]["start"] for j in range(i + 1, len(rows)) if not rows[j]["text"]), a + 99)
        o["t0"] = a + 0.5; o["t1"] = min(nb - 0.3, a + 6.5)
        shots[-n]["ovs"] = [o]
# assign sources, avoiding repeats
order = {}; recent = collections.deque(maxlen=14); missing = collections.Counter()
for s in shots:
    lst = [x for x in pools.P.get(s["pool"], []) if "img" not in x or os.path.exists(x["img"])]
    if not lst:
        missing[s["pool"]] += 1; lst = pools.P["plains"]
    key = s["pool"] if pools.P.get(s["pool"]) else "plains"
    if key not in order:
        o = list(range(len(lst))); rng.shuffle(o); order[key] = [o, 0]
    o, k = order[key]; pick = None
    for j in range(len(o)):
        c = lst[o[(k + j) % len(o)]]
        if json.dumps(c, sort_keys=True) not in recent:
            pick = c; order[key][1] = (k + j + 1) % len(o); break
    if pick is None: pick = lst[o[k % len(o)]]; order[key][1] = (k + 1) % len(o)
    recent.append(json.dumps(pick, sort_keys=True))
    src = dict(pick)
    if "vid" in src:
        d = s["end"] - s["start"]; span = src["t1"] - src["t"]
        if span > d + 0.5: src["t"] = round(src["t"] + rng.uniform(0, span - d), 2)
    s["src"] = src
for i, s in enumerate(shots):
    if s["pool"] == "black":
        if i > 0: shots[i - 1]["fade_out"] = 12
        if i + 1 < len(shots): shots[i + 1]["cut"] = True; shots[i + 1]["fade_in"] = 15
shots[0]["cut"] = True; shots[0]["fade_in"] = 20; shots[-1]["fade_out"] = 40
for i in range(60, len(shots), 70): shots[i]["cut"] = True
json.dump(shots, open("plan/edl.json", "w"), indent=0)
print("shots", len(shots), "missing", dict(missing), "dur", round(shots[-1]["end"] / 60, 2))
