"""Fix the voiceover: drop the duplicated real-estate block and the spoken "dot"s
(cut points chosen by testing candidate cuts with Whisper), then remap the
transcript word times to the new timeline (-> words_fixed.json, voice.wav)."""
import json, re, subprocess, wave, os
import numpy as np

with wave.open("voice_clean.wav") as w:
    sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)

T = json.load(open("transcript.json"))
W = [dict(w) for s in T["segments"] for w in s["words"]]
win = int(sr * 0.01)
env = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, "same"))
SIL = 0.22
FADE = int(0.012 * sr)

# approximate "dot" times (from the prompted scans) and the words around them
DOTS = json.load(open("dot_list.json"))   # [[t, prev_word, next_word], ...]


def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())


def minima(a, b, step=0.01):
    hop = int(0.005 * sr)
    ia, ib = int(a * sr), int(b * sr)
    e = env[ia:ib:hop]
    pts = []
    for j in range(2, len(e) - 2):
        if e[j] <= e[j - 2:j + 3].min():
            pts.append(((ia + j * hop) / sr, e[j]))
    pts.sort(key=lambda p: p[1])
    keep = []
    for t_, _ in pts:   # deepest minima, at least 40 ms apart
        if all(abs(t_ - k) > 0.04 for k in keep): keep.append(t_)
    return keep[:8]


def splice(a, b, ctx=2.2):
    L = x[int((a - ctx) * sr):int(a * sr)].copy(); L[-FADE:] *= np.linspace(1, 0, FADE)
    R = x[int(b * sr):int((b + ctx) * sr)].copy(); R[:FADE] *= np.linspace(0, 1, FADE)
    return np.concatenate([L, np.zeros(int(SIL * sr), np.float32), R])


model = None


def asr(y):
    global model
    if model is None:
        from faster_whisper import WhisperModel
        model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
    y16 = y[::3] / 32768
    segs, _ = model.transcribe(y16, beam_size=5, language="en",
                               initial_prompt="The narrator sometimes says the word dot.")
    return " ".join(s.text for s in segs)


cuts = []
CACHE = json.load(open("dot_cuts.json")) if os.path.exists("dot_cuts.json") else {}
for t, prev, nxt in DOTS:
    key = f"{t:.2f}"
    if key in CACHE:
        cuts.append(tuple(CACHE[key])); continue
    A = minima(t - 0.35, t + 0.3)
    B = minima(t + 0.1, t + 0.8)
    def depth(p): return env[int(p[0] * sr)] + env[int(p[1] * sr)]
    cands = sorted({(a, b) for a in A for b in B if 0.1 <= b - a <= 0.6}, key=depth)
    best = None
    for a, b in cands:
        txt = asr(splice(a, b))
        toks = [norm(w) for w in txt.split()]
        ok = norm(prev) in toks and norm(nxt) in toks and "dot" not in toks
        # the word right after `prev` must be `nxt` (no leftover syllables like "that")
        if ok:
            ip = len(toks) - 1 - toks[::-1].index(norm(prev)) if False else toks.index(norm(prev))
            ok = ip + 1 < len(toks) and toks[ip + 1] == norm(nxt)
        print(f"  {t:.2f} cut {a:.3f}-{b:.3f} ok={ok} :: {txt.strip()[:110]}", flush=True)
        if ok:
            best = (a, b); break
    if best is None:
        print("!! no clean cut for", t, prev, nxt); continue
    CACHE[key] = best
    json.dump(CACHE, open("dot_cuts.json", "w"))
    cuts.append(best)

cuts = [(a, b, SIL) for a, b in cuts]

cuts.sort()

pieces, pos, tmap, newt = [], 0.0, [], 0.0
for a, b, sil in cuts:
    seg = x[int(pos * sr):int(a * sr)].copy()
    seg[-FADE:] *= np.linspace(1, 0, FADE)
    if pos > 0: seg[:FADE] *= np.linspace(0, 1, FADE)
    pieces.append(seg); tmap.append((pos, a, newt)); newt += len(seg) / sr
    if sil:
        pieces.append(np.zeros(int(sil * sr), np.float32)); newt += sil
    pos = b
seg = x[int(pos * sr):].copy(); seg[:FADE] *= np.linspace(0, 1, FADE)
pieces.append(seg); tmap.append((pos, len(x) / sr, newt))
y = np.concatenate(pieces)
with wave.open("voice.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes(np.clip(y, -32768, 32767).astype(np.int16).tobytes())


def remap(t):
    for o0, o1, n0 in tmap:
        if o0 - 0.02 <= t <= o1 + 0.02:
            return n0 + (min(max(t, o0), o1) - o0)
    return None


out = []
for i, w in enumerate(W):
    if norm(w["w"]) == "dot" and (i + 1 >= len(W) or norm(W[i + 1]["w"]) != "gov"):
        continue
    if 0 < i and any(a <= (w["s"] + w["e"]) / 2 <= b for a, b, s in cuts):
        continue
    s, e = remap(w["s"]), remap(w["e"])
    if s is None or e is None: continue
    out.append({"w": w["w"].strip(), "s": round(s, 3), "e": round(e, 3)})
json.dump(out, open("words_fixed.json", "w"))
print("cuts:", [(round(a, 2), round(b, 2)) for a, b, _ in cuts])
print("new duration", round(len(y) / sr, 2), "words", len(out))
