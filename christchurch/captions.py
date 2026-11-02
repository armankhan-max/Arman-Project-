"""Build captions_en.srt from timeline.json (sentence timings + per-word estimates), max 2 lines x 42 chars."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def ts(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


def chunks(words, maxc=80):
    cur, out = [], []
    for w, t in words:
        if cur and len(" ".join(x for x, _ in cur + [(w, t)])) > maxc:
            out.append(cur)
            cur = []
        cur.append((w, t))
    if cur:
        out.append(cur)
    return out


def wrap(text, width=42):
    if len(text) <= width:
        return text
    words = text.split()
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        score = max(len(a), len(b))
        if best is None or score < best[0]:
            best = (score, a + "\n" + b)
    return best[1]


tl = json.load(open(os.path.join(HERE, "timeline.json")))
n = 1
lines = []
for s in tl:
    cs = chunks(s["words"])
    for i, c in enumerate(cs):
        a = c[0][1]
        b = cs[i + 1][0][1] if i + 1 < len(cs) else s["end"] + 0.25
        lines.append(f"{n}\n{ts(a)} --> {ts(b)}\n{wrap(' '.join(w for w, _ in c))}\n")
        n += 1
open(os.path.join(HERE, "captions_en.srt"), "w").write("\n".join(lines))
print(n - 1, "cues")
