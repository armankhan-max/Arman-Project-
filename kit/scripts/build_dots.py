"""Merge the spoken-"dot" scans (dots_*.json from dotscan2.py + unprompted transcript hits)
into dot_list.json: [[time, prev_word, next_word], ...] for fix_voice.py.
Review dot_list.json by eye before running fix_voice.py (drop false hits)."""
import json, glob, re
T = json.load(open("transcript.json"))
W = [w for s in T["segments"] for w in s["words"]]
def n(s): return re.sub(r"[^a-z0-9$%]", "", s.lower())
hits = []
for f in glob.glob("dots_*.json"):
    hits += [[x[0], n(x[2]), n(x[3])] for x in json.load(open(f))]
for i, w in enumerate(W):
    if n(w["w"]) in ("dot", ""):
        hits.append([w["s"], None, None])
hits.sort(key=lambda x: x[0])
out = []
for t, p, q in hits:
    if out and abs(t - out[-1][0]) < 1.0:
        if p and not out[-1][1]: out[-1][1], out[-1][2] = p, q
        continue
    if not p:
        prev = [w for w in W if w["e"] <= t + 0.08 and n(w["w"]) not in ("", "dot")]
        nxt = [w for w in W if w["s"] >= t + 0.12 and n(w["w"]) not in ("", "dot")]
        if not prev or not nxt: continue
        p, q = n(prev[-1]["w"]), n(nxt[0]["w"])
    out.append([round(t, 2), p, q])
json.dump(out, open("dot_list.json", "w"))
for x in out: print(x)
print(len(out), "candidates -> dot_list.json")
