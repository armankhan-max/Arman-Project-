"""Write captions_en.srt from transcript.json (sentence-ish chunks, max ~7 words)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
words = json.load(open(os.path.join(HERE, "transcript.json")))


def ts(x):
    h, r = divmod(x, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


chunks, cur = [], []
for w in words:
    if cur and (len(cur) >= 7 or w["s"] - cur[-1]["e"] > 0.35):
        chunks.append(cur)
        cur = []
    cur.append(w)
chunks.append(cur)
with open(os.path.join(HERE, "captions_en.srt"), "w") as f:
    for i, ch in enumerate(chunks):
        end = ch[-1]["e"] + 0.2
        if i + 1 < len(chunks):
            end = min(end, chunks[i + 1][0]["s"])
        line = " ".join(w["w"] for w in ch).capitalize()
        f.write(f"{i + 1}\n{ts(ch[0]['s'])} --> {ts(end)}\n{line}\n\n")
print("wrote captions_en.srt", len(chunks))
