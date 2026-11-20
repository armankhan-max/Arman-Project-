import numpy as np, subprocess, sys, os
sys.path.insert(0, os.getcwd())
from data3 import *
SR = 48000
A = "/root/.claude/uploads/30c4e146-8864-5bf9-8426-9f627abc5b68/8bf75415-Carson_Ridge_Voiceover_room_slow.mp3"
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", A, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
v = np.frombuffer(raw, np.float32).copy()
c1, c2 = int(1518.60 * SR), int(1940.80 * SR); xf = int(0.04 * SR)
a = v[:c1].copy(); b = v[c2:].copy()
ramp = np.linspace(0, 1, xf, dtype=np.float32)
a[-xf:] *= 1 - ramp; b[:xf] *= ramp
voice = np.concatenate([a, b])
n = int(DUR * SR) + SR
voice = np.pad(voice, (0, max(0, n - len(voice))))[:n]
rng = np.random.default_rng(1)
t = np.arange(n) / SR
def lp(x, k):  # simple moving-average lowpass, k samples
    c = np.cumsum(np.insert(x, 0, 0)); y = (c[k:] - c[:-k]) / k
    return np.pad(y, (k // 2, n - len(y) - k // 2))[:n] if len(x) == n else y
# --- drone bed: low tones + brown noise, slow swell
brown = np.cumsum(rng.normal(0, 1, n)).astype(np.float32); brown -= lp(brown, 4801); brown /= np.abs(brown).max() + 1e-6
drone = 0.5 * np.sin(2 * np.pi * 55 * t) + 0.3 * np.sin(2 * np.pi * 82.4 * t + 1) + 0.15 * np.sin(2 * np.pi * 110.3 * t)
lfo = 0.6 + 0.4 * np.sin(2 * np.pi * t / 23.0)
susp = np.zeros(n, np.float32)
for s0, s1 in SUSPENSE:
    i0, i1 = int(s0 * SR), int(s1 * SR); susp[i0:i1] = 1
susp = lp(susp, SR * 3)
bed = (drone * lfo * 0.6 + brown * 0.5) * (0.010 + 0.014 * susp)
mix = voice + bed.astype(np.float32)
def add(at, sig, g):
    i = int(at * SR); j = min(n, i + len(sig))
    if 0 <= i < n: mix[i:j] += sig[:j - i] * g
def whoosh(d=0.9):
    m = int(d * SR); x = rng.normal(0, 1, m).astype(np.float32)
    env = np.sin(np.linspace(0, np.pi, m)) ** 2
    k = np.linspace(60, 6, m).astype(int); out = np.zeros(m, np.float32); c = np.cumsum(np.insert(x, 0, 0))
    idx = np.arange(m); lo = np.clip(idx - k, 0, m); out = (c[idx + 1] - c[lo]) / (idx + 1 - lo)
    out = out / (np.abs(out).max() + 1e-6); return out * env
def boom(d=2.2):
    m = int(d * SR); tt = np.arange(m) / SR
    f = 52 * np.exp(-tt * 0.6); ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-tt * 2.2) + 0.15 * rng.normal(0, 1, m) * np.exp(-tt * 30)).astype(np.float32)
def click():
    m = int(0.03 * SR); x = rng.normal(0, 1, m) * np.exp(-np.arange(m) / (0.004 * SR))
    return (x + 0.5 * np.sin(2 * np.pi * 1800 * np.arange(m) / SR) * np.exp(-np.arange(m) / (0.003 * SR))).astype(np.float32)
def pulse():
    m = int(0.5 * SR); tt = np.arange(m) / SR
    return (np.sin(2 * np.pi * 48 * tt) * np.exp(-tt * 9)).astype(np.float32)
W_, B_ = whoosh(), boom()
for g in GFX: add(g[0] - 0.35, W_, 0.035)
for o in OV:
    s, e, kind, dat = o
    if kind in ("chapter", "loc"): add(s - 0.35, W_, 0.035)
    if kind in ("cold", "big"): add(s, B_, 0.11); add(s - 0.3, W_, 0.025)
    if kind == "lower": add(s - 0.2, whoosh(0.6), 0.02)
    if kind == "type":
        nch = len(dat["t"]); 
        for i in range(0, nch, 1):
            if dat["t"][i] != " ": add(s + i / 20, click(), 0.012 * rng.uniform(0.6, 1.1))
for g in GFX:
    if g[2] == "ledger":
        for ts, txt, st in g[3]["lines"]:
            for i, ch in enumerate(txt):
                if ch != " ": add(g[0] + ts + i / 22, click(), 0.014 * rng.uniform(0.6, 1.1))
# slow heartbeat-like pulses in suspense windows
for s0, s1 in SUSPENSE:
    x = s0 + 1
    while x < s1 - 1:
        add(x, pulse(), 0.05); add(x + 0.28, pulse(), 0.03); x += 1.25
# fade out end
fo = int(1.5 * SR); end = int(DUR * SR)
mix[end - fo:end] *= np.linspace(1, 0, fo); mix[end:] = 0
pk = np.abs(mix).max(); mix = mix / max(pk, 1.0) * 0.97 if pk > 0.97 else mix
mix[:end].astype(np.float32).tofile("mix.f32")
print("voice peak", np.abs(voice).max(), "mix peak", pk, "dur", end / SR)
