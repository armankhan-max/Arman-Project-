"""Remove the stray spoken word "Asterisk" (a TTS artifact) from the voiceover.

Writes audio/voice_clean.wav and transcript.json with times shifted to the cleaned audio.
"""
import json, subprocess, sys, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1]
SR = 44100
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True).stdout
x = np.frombuffer(raw, np.float32).copy()
hop = SR // 100
n = len(x) // hop
rms = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
db = 20 * np.log10(rms)
thr = np.percentile(db, 95) - 38
silent = db < thr

T = json.load(open(os.path.join(HERE, "transcript_raw.json")))
words = [w for s in T for w in s["words"]]


def fr(t):
    return min(max(int(t * 100), 0), n - 1)


cuts = []
# hand-checked against the energy envelope where whisper's word timing drifted
OVERRIDE = [(660.80, 661.58, 662.05), (899.92, 899.20, 900.82), (196.38, 196.37, 196.95), (301.62, 301.63, 302.25)]
for i, w in enumerate(words):
    if "asterisk" not in w["w"].lower():
        continue
    s, e = w["s"], w["e"]
    nxt = words[i + 1]["s"] if i + 1 < len(words) else e + 0.3
    # onset: walk back from inside the word to the first silent frame
    k = fr((s + e) / 2)
    lo = fr(s - 0.35)
    while k > lo and not silent[k]:
        k -= 1
    a = k / 100 + 0.01
    # end: the next silent run after the word, but never past the next word's start
    k = fr((s + e) / 2)
    hi = fr(min(e + 0.25, nxt))
    while k < hi and not silent[k]:
        k += 1
    word_end = k / 100
    if not silent[k]:
        # no pause before the next word: cut at the deepest energy dip near whisper's word end
        w0, w1 = fr(e - 0.06), fr(e + 0.10)
        word_end = (w0 + int(np.argmin(db[w0:w1 + 1]))) / 100 + 0.01
        k = fr(word_end)
    # swallow the pause after the word up to just before the next word's sound
    k2 = fr(word_end)
    hi2 = fr(nxt + 0.2)
    while k2 < hi2 and silent[k2]:
        k2 += 1
    b = max(word_end, k2 / 100 - 0.06) if silent[fr(word_end)] else word_end
    for (ms, ma, mb) in OVERRIDE:
        if abs(ms - s) < 0.05:
            a, b = ma, mb
    cuts.append((a, b))
    print(f"{w['w']!r:14} whisper {s:7.2f}-{e:7.2f}  cut {a:7.2f}-{b:7.2f} ({b - a:.2f}s)")

# build output with 8 ms fades at each join
fade = int(SR * 0.008)
pieces, pos = [], 0.0
keep = []
for a, b in cuts:
    keep.append((pos, a))
    pos = b
keep.append((pos, len(x) / SR))
for a, b in keep:
    seg = x[int(a * SR):int(b * SR)].copy()
    if len(seg) > 2 * fade:
        seg[:fade] *= np.linspace(0, 1, fade)
        seg[-fade:] *= np.linspace(1, 0, fade)
    pieces.append(seg)
y = np.concatenate(pieces)
os.makedirs(os.path.join(HERE, "audio"), exist_ok=True)
out = os.path.join(HERE, "audio", "voice_clean.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s16le", out],
               input=y.tobytes(), check=True)


def remap(t):
    shift = 0.0
    for a, b in cuts:
        if t >= b:
            shift += b - a
        elif t > a:
            return a - shift
    return t - shift


segs = []
for s in T:
    ws = [dict(w="" + w["w"], s=round(remap(w["s"]), 3), e=round(remap(w["e"]), 3))
          for w in s["words"] if "asterisk" not in w["w"].lower()]
    if not ws:
        continue
    segs.append(dict(start=ws[0]["s"], end=ws[-1]["e"], words=ws, text="".join(w["w"] for w in ws).strip()))
json.dump(segs, open(os.path.join(HERE, "transcript.json"), "w"), indent=0)
json.dump([[a,b] for a,b in cuts], open(os.path.join(HERE,"audio","cuts.json"),"w"))
print("removed", len(cuts), "cuts,", round(sum(b - a for a, b in cuts), 2), "s; new length", round(len(y) / SR, 2))
