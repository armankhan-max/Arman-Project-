"""Synthesize the sound-design track (music bed, transition whooshes, coin, fire, water, digging) -> public/audio/sfx.wav"""
import json
import os
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100
tl = json.load(open(os.path.join(ROOT, "src", "data", "shots.json")))
FPS = tl["fps"]
start = {s["id"]: s["start"] / FPS for s in tl["shots"]}
end = {s["id"]: (s["start"] + s["n"]) / FPS for s in tl["shots"]}
DUR = tl["total"] / FPS
N = int(DUR * SR)
L = np.zeros(N)
Rr = np.zeros(N)
rng = np.random.default_rng(7)


def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i + len(sig) <= 0:
        return
    sig = sig[: max(0, N - i)]
    L[i:i + len(sig)] += sig * gain * (1 - max(0, pan))
    Rr[i:i + len(sig)] += sig * gain * (1 + min(0, pan))


def env(n, a=0.01, r=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / r)




def smooth(x, win):
    return np.convolve(x, np.ones(win) / win, mode="same")


def ting(f=2900.0, dur=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.55 * np.sin(2 * np.pi * f * 1.52 * t) + 0.3 * np.sin(2 * np.pi * f * 2.31 * t)
    return s * env(n, 0.001, 0.11)


def whoosh(dur=0.55):
    n = int(dur * SR)
    x = smooth(rng.standard_normal(n), 40) * 6
    t = np.arange(n) / n
    return x * np.sin(np.pi * t) ** 2


def thump(f=70.0, dur=0.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * (f + 40 * np.exp(-t * 25)) * t) * env(n, 0.003, 0.09)


def noise_bed(dur, win):
    n = int(dur * SR)
    x = smooth(rng.standard_normal(n), win)
    return x / (np.abs(x).max() + 1e-9)


def fade(x, d=0.4):
    n = min(len(x) // 2, int(d * SR))
    r = np.linspace(0, 1, n)
    x[:n] *= r
    x[-n:] *= r[::-1]
    return x


# music bed: slow minor drone with a gentle pulse
t = np.arange(N) / SR
bed = np.zeros(N)
for f, g in ((55.0, 0.5), (82.41, 0.3), (110.0, 0.22), (130.81, 0.16), (164.81, 0.1)):
    bed += g * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * t + f))
bed *= 0.085 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.5 * t))
L += bed
Rr += bed

# coins: shower into the grave (A), placed in mouth (E1), dropped in palm (E2), loot (G2, T)
for i in range(22):
    add(ting(rng.uniform(2500, 3600), 0.4), start["A"] + (25 + 4 * i) / FPS, 0.045, pan=rng.uniform(-0.5, 0.5))
add(ting(3100, 0.6), start["E1"] + 41 / FPS, 0.1)
add(ting(2800, 0.6), start["E2"] + 25 / FPS, 0.1)
for i in range(9):
    add(ting(rng.uniform(2500, 3600), 0.4), start["G2"] + 0.5 + i * 0.27, 0.05, pan=rng.uniform(-0.6, 0.6))
for i in range(18):
    add(ting(rng.uniform(2400, 3800), 0.4), start["T"] + 2.7 + i * 0.11, 0.05, pan=rng.uniform(-0.6, 0.6))

# digging thuds (G1, G2)
for sid in ("G1", "G2"):
    tt = start[sid] + 0.1
    while tt < end[sid]:
        add(thump(), tt, 0.22)
        tt += 16 / FPS

# water ambience on the Styx shots
for sid in ("C", "D", "E2", "F"):
    add(fade(noise_bed(end[sid] - start[sid], 500)), start[sid], 0.07)

# fire crackle + roar while the fires are on screen (inside the long continuous shot)
for t0, t1, g in ((start["S"] + 3.0, start["S"] + 5.8, 0.4), (start["S"] + 8.0, start["S"] + 11.4, 1.0), (start["S"] + 14.9, end["S"], 1.3)):
    d = t1 - t0
    add(fade(noise_bed(d, 220)), t0, 0.05 * g)
    for _ in range(int(d * 14)):
        n = int(rng.uniform(0.004, 0.02) * SR)
        add(rng.standard_normal(n) * np.exp(-np.arange(n) / (n / 3)), t0 + rng.uniform(0, d), 0.05 * g, pan=rng.uniform(-0.5, 0.5))

# ghost shimmer (shot B and "the dead still got paid") and the final hit
for t0, t1 in ((start["B"], end["B"]), (start["S"] + 11.2, start["S"] + 12.9)):
    n = int((t1 - t0) * SR)
    tt = np.arange(n) / SR
    sh = (np.sin(2 * np.pi * 880 * tt) + np.sin(2 * np.pi * 1318.5 * tt) + np.sin(2 * np.pi * 1760 * tt)) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * tt))
    add(fade(sh, 0.6), t0, 0.012)
add(thump(45, 0.8), start["T"] + 2.05, 0.3)

out = np.stack([L, Rr], axis=1)
edge = int(0.6 * SR)
out[:edge] *= np.linspace(0, 1, edge)[:, None]
out[-edge:] *= np.linspace(1, 0, edge)[:, None]
out = np.clip(out, -0.95, 0.95)
path = os.path.join(ROOT, "public", "audio", "sfx.wav")
with wave.open(path, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((out * 32767).astype("<i2").tobytes())
print("sfx", path, round(DUR, 2), "s")
