#!/usr/bin/env python3
"""60 s nostalgic music (original), built from the reference's measured traits:
10 s loop repeated, dense soft plucks every ~0.31 s, G-centred major7 colour with
borrowed minor (Cm6), band-limited (3.8 kHz), constant quiet level, tape wobble, reverb."""
import subprocess, wave, os, sys
import numpy as np
from scipy import signal

SR, DUR, LOOP = 44100, 60, 10.0
N = SR * DUR
rng = np.random.default_rng(1975)


def n2f(s):
    semi = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    acc, i = 0, 1
    if s[1] in "b#":
        acc = -1 if s[1] == "b" else 1; i = 2
    return 440 * 2 ** ((semi[s[0]] + acc + 12 * (int(s[i:]) - 4) - 9) / 12)


CH = [["G3", "B3", "D4", "F#4"],      # Gmaj7
      ["E3", "G3", "B3", "D4"],       # Em7
      ["C3", "E3", "G3", "B3"],       # Cmaj7
      ["C3", "Eb3", "G3", "A3"]]      # Cm6 (borrowed minor = bittersweet)
MEL = ["B4", "G5", "E5", "Eb5"]
PAT = [0, 2, 1, 3, 2, 1, 3, 2]
bus = np.zeros((2, N)); snd = np.zeros((2, N))


def put(sig, t0, pan, g, send=0.0):
    i = max(int(t0 * SR), 0); n = min(len(sig), N - i)
    if n <= 0: return
    th = pan * np.pi / 2
    for c, w in enumerate((np.cos(th), np.sin(th))):
        bus[c, i:i + n] += sig[:n] * g * w
        snd[c, i:i + n] += sig[:n] * g * w * send


def pluck(f, d=2.0):
    f *= 2 ** (rng.uniform(-15, 15) / 1200)  # slightly out of tune
    t = np.arange(int(d * SR)) / SR
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.7) + 0.3 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t / 0.25)
         + 0.1 * np.sin(2 * np.pi * f * 4.1 * t) * np.exp(-t / 0.06))
    return s * (1 - np.exp(-t / 0.003))


def keys(f, d=5.0):
    f *= 2 ** (rng.uniform(-20, 20) / 1200)
    t = np.arange(int(d * SR)) / SR
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / 2.4) + 0.3 * np.sin(2 * np.pi * f * 2.003 * t) * np.exp(-t / 1.1)
    return np.tanh(1.5 * s * (1 - np.exp(-t / 0.01))) / 1.5


def pad(freqs, d=7.0):
    t = np.arange(int(d * SR)) / SR
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return sum(np.sin(2 * np.pi * f * (1 + k) * t) for f in freqs for k in (-0.002, 0.002)) * env


step = LOOP / 32
for li in range(int(DUR / LOOP)):
    t0 = li * LOOP
    for ci, ch in enumerate(CH):
        tc = t0 + ci * LOOP / 4
        fr = [n2f(x) for x in ch]
        for k, ix in enumerate(PAT):
            f = fr[ix] * (2 if k % 2 else 1)
            put(pluck(f), tc + k * step, 0.3 + 0.4 * (k % 2), 0.05 * rng.uniform(0.75, 1), 0.7)
        put(pad(fr), tc - 1.0, 0.5, 0.012 * min(1, li / 2), 0.4)
        if li >= 2:
            put(keys(n2f(MEL[ci])), tc + 0.05, 0.55, 0.07 * min(1, (li - 1) / 3), 1.2)

# reverb
n_ir = int(3.5 * SR); t = np.arange(n_ir) / SR
wet = np.zeros_like(bus)
for c in range(2):
    ir = np.random.default_rng(5 + c).standard_normal(n_ir) * np.exp(-6.9 * t / 3.5)
    ir = signal.sosfilt(signal.butter(2, 4500, "low", fs=SR, output="sos"), ir); ir[:int(.02 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum())
    wet[c] = signal.oaconvolve(snd[c], ir)[:N]
mix = bus + wet * 1.3
# band-limit + tape wobble
tt = np.arange(N) / SR
pos = np.arange(N) + (0.0035 / (2 * np.pi * .45) * np.sin(2 * np.pi * .45 * tt) + 0.0008 / (2 * np.pi * 7) * np.sin(2 * np.pi * 7 * tt)) * SR
sos = signal.butter(2, 3800, "low", fs=SR, output="sos")
for c in range(2):
    mix[c] = np.interp(pos, np.arange(N), signal.sosfilt(sos, mix[c]))
    mix[c] += signal.sosfilt(signal.butter(2, 5500, "low", fs=SR, output="sos"), rng.standard_normal(N)) * 0.0015  # tape hiss
mix *= 10 ** (-22 / 20) / mix.std()
mix = np.tanh(mix * 1.3) / 1.3
fi, fo = 3 * SR, 6 * SR
mix[:, :fi] *= np.linspace(0, 1, fi) ** 2; mix[:, -fo:] *= np.linspace(1, 0, fo) ** 2
mix *= min(1, 0.85 / abs(mix).max())
out = sys.argv[1] if len(sys.argv) > 1 else "Nostalgic_Music_1min.mp3"
wav = out.replace(".mp3", ".wav")
with wave.open(wav, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix.T * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libmp3lame", "-b:a", "192k",
                "-metadata", "title=Nostalgic Music", out], check=True)
os.remove(wav)
