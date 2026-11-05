"""Synthesise original BGM + SFX for the Hell Bank Notes short and mix with the voiceover.

python audio.py voiceover.mp3 out.wav
Everything is generated here (royalty-free). Cues are keyed to words.json timings.
"""
import json
import math
import os
import subprocess
import sys
import numpy as np

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
DUR = 57.05
N = int(DUR * SR) + SR
rng = np.random.default_rng(7)


def t_(d):
    return np.arange(int(d * SR)) / SR


def env_ad(n, a=0.005, d=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
    return e


def place(buf, sig, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf) or len(sig) == 0:
        return
    sig = np.array(sig, dtype=float)
    f = min(len(sig) // 4, int(0.004 * SR))  # 4 ms fades on every event: no clicks
    if f > 1:
        sig[:f] *= np.linspace(0, 1, f)
        sig[-f:] *= np.linspace(1, 0, f)
    if i < 0:
        sig = sig[-i:]
        i = 0
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[:j - i] * gain


def lp(x, cutoff):
    # one-pole low-pass (vectorised via cumulative filter approximation)
    a = math.exp(-2 * math.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    # chunked python loop is ok for short sfx only
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        m *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * m, len(x))


def noise(d):
    return rng.standard_normal(int(d * SR))


def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


# ------------------------------------------------------------------ instruments
def pluck(freq, d=0.45, bright=1.0):
    t = t_(d)
    s = np.zeros_like(t)
    for h in range(1, 7):
        s += np.sin(2 * np.pi * freq * h * t) * (bright ** (h - 1)) / h * np.exp(-t * (6 + h * 4))
    s += noise(d) * np.exp(-t * 120) * 0.15
    return s * env_ad(len(t), 0.002, 0.35)


def bass(freq, d=0.5):
    t = t_(d)
    s = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) + 0.12 * np.sin(6 * np.pi * freq * t)
    return s * env_ad(len(t), 0.004, 0.32)


def accordion(freq, d=0.5, vib=6.0):
    t = t_(d)
    trem = 1 + 0.18 * np.sin(2 * np.pi * vib * t)
    s = np.zeros_like(t)
    for det in (0.997, 1.0, 1.004):
        for h in range(1, 9):
            s += np.sin(2 * np.pi * freq * det * h * t) * (0.8 ** h) / (h ** 0.6)
    a = np.minimum(1, t / 0.03) * np.minimum(1, (d - t) / 0.06)
    return s * trem * np.clip(a, 0, 1) * 0.25


def kick(d=0.35):
    t = t_(d)
    f = 50 + 90 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 12)


def brush(d=0.18):
    return fft_filter(noise(d), lo=1500, hi=9000) * np.exp(-t_(d) * 25) * 0.5


def hat(d=0.06):
    return fft_filter(noise(d), lo=7000) * np.exp(-t_(d) * 70) * 0.35


def pad(freqs, d):
    t = t_(d)
    s = np.zeros_like(t)
    for f in freqs:
        for det in (0.995, 1.005):
            s += np.sin(2 * np.pi * f * det * t) + 0.3 * np.sin(4 * np.pi * f * det * t)
    a = np.clip(np.minimum(t / 0.6, (d - t) / 0.8), 0, 1)
    return s * a / len(freqs) * 0.4


# ------------------------------------------------------------------ SFX
def whoosh(d=0.45, up=True, bright=1.0):
    n = noise(d)
    t = t_(d)
    sh = np.sin(np.pi * t / d) ** 2
    # sweep band by mixing two filtered versions
    a = fft_filter(n, lo=300, hi=1500 * bright)
    b = fft_filter(n, lo=1500, hi=7000 * bright)
    k = t / d if up else 1 - t / d
    return (a * (1 - k) + b * k) * sh * 0.9


def pop(f=600):
    t = t_(0.12)
    fr = f * (1 + 2 * np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 40)


def thud(f=70, d=0.4):
    t = t_(d)
    fr = f * (1 + 1.5 * np.exp(-t * 25))
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 9)
    s += fft_filter(noise(d), hi=1200) * np.exp(-t * 40) * 0.6
    return s


def mx(*xs):
    n = max(len(x) for x in xs)
    o = np.zeros(n)
    for x in xs:
        o[:len(x)] += x
    return o


def stamp():
    return mx(thud(90, 0.3), fft_filter(noise(0.06), lo=800, hi=5000) * np.exp(-t_(0.06) * 60) * 0.6)


def bell(f=1320, d=1.0):
    t = t_(d)
    s = sum(np.sin(2 * np.pi * f * r * t) * a * np.exp(-t * dcy) for r, a, dcy in
            ((1, 1, 3), (2.76, 0.5, 6), (5.4, 0.25, 10), (8.9, 0.1, 14)))
    return s * 0.5


def sparkle():
    s = np.zeros(int(0.9 * SR))
    for i, f in enumerate((2093, 2637, 3136, 3951, 4186)):
        place(s, bell(f, 0.5) * 0.5, i * 0.06)
    return s


def kaching():
    s = np.zeros(int(1.0 * SR))
    place(s, fft_filter(noise(0.08), lo=2000) * np.exp(-t_(0.08) * 50), 0, 0.7)
    place(s, bell(1760, 0.9) + bell(2217, 0.9) * 0.7, 0.07, 0.9)
    return s


def paper(d=0.25):
    n = fft_filter(noise(d), lo=1500, hi=8000)
    t = t_(d)
    return n * np.abs(np.sin(t * 90)) * np.exp(-t * 8) * 0.8


def rip(d=0.4):
    n = fft_filter(noise(d), lo=1200, hi=6000)
    t = t_(d)
    return n * (0.6 + 0.4 * np.sign(np.sin(t * 320))) * np.minimum(1, (d - t) * 10)


def creak(d=0.7, f0=180):
    t = t_(d)
    f = f0 + 60 * np.sin(t * 7)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * (0.6 + 0.4 * np.sin(t * 40))
    return fft_filter(s, lo=300, hi=2500) * np.sin(np.pi * t / d) * 0.4


def ping():
    return bell(2400, 0.6) * 0.6


def knock(d=0.15, f=300):
    t = t_(d)
    return (np.sin(2 * np.pi * f * t) + fft_filter(noise(d), lo=400, hi=3000) * 0.8) * np.exp(-t * 35)


def gavel():
    s = np.zeros(int(0.6 * SR))
    place(s, knock(0.2, 220), 0, 1.0)
    place(s, thud(60, 0.5), 0, 0.8)
    return s


def murmur(d, angry=True):
    n = noise(d)
    t = t_(d)
    s = np.zeros_like(t)
    for k in range(8):
        f = 300 + k * 90
        band = fft_filter(n * (0.5 + 0.5 * np.sin(2 * np.pi * (3 + k * 0.7) * t + k)), lo=f, hi=f * 2.2)
        s += band
    a = np.clip(np.minimum(t / 0.2, (d - t) / 0.3), 0, 1)
    return s * a * (1.0 if angry else 0.6)


def tick():
    return knock(0.04, 2500) * 0.5


def gulp():
    t = t_(0.25)
    f = 400 - 900 * t
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.25) * 0.7


def dundun():
    s = np.zeros(int(1.4 * SR))
    for i, n in enumerate((38, 37)):
        t = t_(0.7)
        x = sum(np.sin(2 * np.pi * midi(n) * h * t) / h for h in range(1, 6)) * np.exp(-t * 3)
        place(s, x, i * 0.45, 0.6)
    return s


def scratch():
    d = 0.45
    t = t_(d)
    f = 300 + 1200 * np.abs(np.sin(np.pi * t / d * 2))
    s = fft_filter(noise(d), lo=200, hi=4000) * 0.5
    s += np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4
    return s * np.minimum(1, (d - t) * 8)


def boing():
    t = t_(0.5)
    f = 220 * (1 + 0.5 * np.sin(2 * np.pi * 14 * t) * np.exp(-t * 6))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5) * 0.6


def reel(d=0.6):
    s = np.zeros(int(d * SR))
    k = 0.0
    while k < d - 0.03:
        place(s, tick(), k, 0.8)
        k += 0.035
    return s


def steps(n=4, gap=0.22):
    s = np.zeros(int((n * gap + 0.2) * SR))
    for i in range(n):
        place(s, knock(0.08, 140 + 20 * (i % 2)), i * gap, 0.8)
    return s


def chug(d):
    s = np.zeros(int(d * SR))
    k = 0.0
    i = 0
    while k < d:
        place(s, fft_filter(noise(0.12), lo=200, hi=1800) * np.exp(-t_(0.12) * 25), k, 0.9 if i % 2 == 0 else 0.6)
        k += 0.16
        i += 1
    return s


def whistle_train(d=0.9):
    t = t_(d)
    a = np.clip(np.minimum(t / 0.05, (d - t) / 0.2), 0, 1)
    return (np.sin(2 * np.pi * 740 * t) + np.sin(2 * np.pi * 932 * t) + 0.5 * np.sin(2 * np.pi * 1110 * t)) * a * 0.3


def crickets(d):
    s = np.zeros(int(d * SR))
    k = 0.05
    while k < d - 0.1:
        for j in range(3):
            t = t_(0.03)
            place(s, np.sin(2 * np.pi * 4300 * t) * np.sin(np.pi * t / 0.03), k + j * 0.045, 0.25)
        k += 0.33
    return s


def rain(d):
    n = fft_filter(noise(d), lo=2000, hi=9000)
    t = t_(d)
    return n * np.clip(np.minimum(t / 0.4, (d - t) / 0.4), 0, 1) * 0.25


def thunder(d=1.6):
    t = t_(d)
    return fft_filter(noise(d), hi=180) * np.exp(-t * 2) * np.minimum(1, t / 0.05) * 2.5


def sad_trombone():
    s = np.zeros(int(2.0 * SR))
    for i, (n, d) in enumerate(((58, 0.32), (57, 0.32), (56, 0.32), (55, 0.9))):
        t = t_(d)
        f = midi(n) * (1 + 0.012 * np.sin(2 * np.pi * 5.5 * t * (1 if i < 3 else 1.6)))
        ph = 2 * np.pi * np.cumsum(f) / SR
        x = sum(np.sin(ph * h) * (0.7 ** h) for h in range(1, 8))
        a = np.clip(np.minimum(t / 0.03, (d - t) / 0.08), 0, 1)
        place(s, x * a * 0.35, i * 0.34)
    return s


def ff_whir(d):
    t = t_(d)
    f = 600 + 300 * np.sin(2 * np.pi * 8 * t)
    return np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.08 * np.clip(np.minimum(t / 0.1, (d - t) / 0.1), 0, 1)


def police_whistle(d=0.55):
    t = t_(d)
    f = 2800 * (1 + 0.03 * np.sign(np.sin(2 * np.pi * 28 * t)))
    a = np.clip(np.minimum(t / 0.02, (d - t) / 0.05), 0, 1)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * a * 0.35


def ship_horn(d=1.3):
    t = t_(d)
    s = sum(np.sin(2 * np.pi * f * t) / (i + 1) for i, f in enumerate((98, 196, 294, 392)))
    s += sum(np.sin(2 * np.pi * f * 1.26 * t) / (i + 1) * 0.6 for i, f in enumerate((98, 196, 294)))
    a = np.clip(np.minimum(t / 0.08, (d - t) / 0.25), 0, 1)
    return s * a * 0.35


def waves(d):
    n = fft_filter(noise(d), lo=150, hi=1800)
    t = t_(d)
    return n * (0.5 + 0.5 * np.sin(2 * np.pi * 0.4 * t)) * np.clip(np.minimum(t / 0.3, (d - t) / 0.3), 0, 1) * 0.4


def stinger():
    s = np.zeros(int(2.0 * SR))
    for n in (50, 57, 62, 65, 69):
        place(s, accordion(midi(n), 1.2, 7) * 1.4, 0)
        place(s, pluck(midi(n + 12), 0.8), 0, 0.3)
    place(s, kick(0.5), 0, 0.8)
    return s


def boom():
    return thud(45, 1.2) * 1.2


def door_slam():
    return mx(thud(80, 0.5), knock(0.1, 180))



# ------------------------------------------------------------------ extra SFX
def fire_burst(d=1.2):
    t = t_(d)
    n = fft_filter(noise(d), lo=60, hi=2500)
    e = np.minimum(1, t / 0.08) * np.exp(-t * 2.2)
    return n * e * 1.4


def crackle(d, dens=18):
    s = np.zeros(int(d * SR))
    k = rng.exponential(1 / dens)
    while k < d - 0.02:
        place(s, fft_filter(noise(0.012), lo=1500, hi=9000) * np.exp(-t_(0.012) * 300), k, rng.uniform(0.2, 1.0))
        k += rng.exponential(1 / dens)
    roar = fft_filter(noise(d), lo=80, hi=500) * 0.25
    return s + roar


def slowmo_in(d=1.2):
    t = t_(d)
    f = 220 * np.exp(-t * 1.8) + 40
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5
    air = fft_filter(noise(d), lo=100, hi=900) * 0.6
    return (tone + air) * np.sin(np.pi * t / d) ** 1.5


def riser(d=1.0):
    t = t_(d)
    f = 200 + 1400 * (t / d) ** 2
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25 + fft_filter(noise(d), lo=800, hi=6000) * (t / d) * 0.5
    return s * np.minimum(1, (d - t) / 0.05)


def gong(f=110, d=3.0):
    t = t_(d)
    s = sum(np.sin(2 * np.pi * f * r * t + 0.3 * np.sin(2 * np.pi * 3 * t)) * a * np.exp(-t * dc)
            for r, a, dc in ((1, 1, 0.9), (1.48, 0.6, 1.3), (2.03, 0.45, 1.6), (2.74, 0.3, 2.2), (3.9, 0.2, 3)))
    return s * np.minimum(1, t / 0.01) * 0.45


def coin():
    return mx(bell(3200, 0.35) * 0.6, bell(4100, 0.3) * 0.3)


def honk():
    s = np.zeros(int(0.5 * SR))
    for i in range(2):
        t = t_(0.15)
        x = np.sign(np.sin(2 * np.pi * 420 * t)) * 0.3 + np.sign(np.sin(2 * np.pi * 530 * t)) * 0.3
        place(s, fft_filter(x, hi=2500), i * 0.2)
    return s


def blip_tune():
    s = np.zeros(int(0.8 * SR))
    for i, n in enumerate((76, 81, 84, 88)):
        place(s, np.sin(2 * np.pi * midi(n) * t_(0.12)) * np.exp(-t_(0.12) * 12) * 0.5, i * 0.11)
    return s


def success():
    s = np.zeros(int(1.2 * SR))
    for i, n in enumerate((72, 76, 79, 84)):
        place(s, bell(midi(n), 0.7) * 0.5, i * 0.08)
    return s


def flutter(d=0.8):
    t = t_(d)
    return fft_filter(noise(d), lo=200, hi=1500) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 16 * t))) * 0.35


def harp():
    s = np.zeros(int(1.4 * SR))
    for i, n in enumerate((62, 65, 67, 69, 72, 74, 77, 79, 81, 84)):
        place(s, pluck(midi(n), 0.9, 0.9), i * 0.05, 0.5)
    return s


def wah():
    s = np.zeros(int(1.0 * SR))
    for i, (n, d) in enumerate(((55, 0.3), (54, 0.55))):
        t = t_(d)
        f = midi(n) * (1 + 0.015 * np.sin(2 * np.pi * 6 * t))
        ph = 2 * np.pi * np.cumsum(f) / SR
        x = sum(np.sin(ph * h) * (0.7 ** h) for h in range(1, 7))
        place(s, x * np.clip(np.minimum(t / 0.03, (d - t) / 0.08), 0, 1) * 0.35, i * 0.32)
    return s


def heaven():
    s = np.zeros(int(2.0 * SR))
    place(s, pad([midi(n) for n in (74, 77, 81, 84)], 1.9), 0, 0.9)
    place(s, sparkle(), 0.1, 0.6)
    return s


# ------------------------------------------------------------------ BGM (pentatonic, guzheng + erhu + drums)
BPM = 96
BEAT = 60 / BPM
PENTA = [50, 53, 55, 57, 60, 62, 65, 67, 69, 72, 74]  # D minor pentatonic
ROOTS = [38, 38, 43, 45, 38, 41, 43, 45]
MEL = [69, 67, 65, 62, None, 65, 67, 69, 72, 69, 67, None, 65, 62, 60, 62]


def guzheng(f, d=0.6):
    t = t_(d)
    bend = f * (1 + 0.02 * np.exp(-t * 18))
    ph = 2 * np.pi * np.cumsum(bend) / SR
    s = sum(np.sin(ph * h) * (0.75 ** h) * np.exp(-t * (4 + h * 2.5)) for h in range(1, 8))
    return s * np.minimum(1, t / 0.002) * 0.6


def erhu(f, d):
    t = t_(d)
    vib = 1 + 0.012 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / 0.25)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    s = sum(np.sin(ph * h) * (0.62 ** h) for h in range(1, 10))
    a = np.clip(np.minimum(t / 0.09, (d - t) / 0.12), 0, 1)
    return fft_filter(s * a, hi=3500) * 0.3


def woodblock():
    return knock(0.06, 900) * 0.6


def taiko(d=0.6):
    t = t_(d)
    f = 70 + 60 * np.exp(-t * 25)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) + fft_filter(noise(d), hi=600) * np.exp(-t * 30) * 0.3


def mood(t):
    g = dict(zh=1.0, erhu=0.0, drums=1.0, pad=0.0, level=1.0, bells=0.0)
    slow = [(0.0, 1.25), (16.35, 17.55), (33.55, 34.5), (49.45, 53.2)]
    if any(a <= t < b for a, b in slow):
        g.update(drums=0.0, zh=0.35, pad=1.0, level=0.7)
    if 1.25 <= t < 4.4:
        g.update(drums=1.3)
    if 5.95 <= t < 9.6:
        g.update(erhu=0.8, drums=0.4, pad=0.8)
    if 20.9 <= t < 24.55:
        g.update(drums=0.5, erhu=0.6)
    if 25.55 <= t < 28.85:
        g.update(bells=1.0, pad=0.8)
    if 28.85 <= t < 30.05 or 40.85 <= t < 42.35:
        g.update(drums=0.0, zh=0.2, erhu=1.0, level=0.8)
    if 35.3 <= t < 40.85:
        g.update(drums=1.2 + (t - 35.3) / 6, level=1.0 + (t - 35.3) / 20)
    if 42.35 <= t < 49.45:
        g.update(drums=1.3, erhu=0.7)
    if 53.2 <= t:
        g.update(drums=0.0, zh=0.8, erhu=0.8, pad=1.0, level=0.85)
    return g


def make_bgm():
    out = np.zeros(N)
    nb = int(DUR / (BEAT / 2)) + 2
    for e in range(nb):  # eighth notes
        te = e * BEAT / 2
        if te > DUR:
            break
        b = e // 2
        bar = b // 4
        g = mood(te)
        L = g['level']
        root = ROOTS[bar % len(ROOTS)]
        if e % 2 == 0 and b % 4 in (0, 2):
            place(out, bass(midi(root), BEAT * 1.6), te, 0.5 * L)
        # guzheng arpeggio on eighths
        n = PENTA[(e * 3 + bar * 2) % len(PENTA)]
        place(out, guzheng(midi(n), 0.7), te, 0.11 * g['zh'] * L)
        if g['drums'] > 0:
            if e % 8 == 0:
                place(out, taiko(), te, 0.55 * g['drums'] * L)
            if e % 8 == 5:
                place(out, taiko(0.4), te, 0.3 * g['drums'] * L)
            if e % 2 == 1:
                place(out, woodblock(), te, 0.18 * g['drums'] * L)
            place(out, hat(), te, 0.12 * g['drums'] * L)
        if g['erhu'] > 0 and e % 2 == 0:
            m = MEL[(b) % len(MEL)]
            if m is not None:
                place(out, erhu(midi(m), BEAT * 0.98), te, 0.16 * g['erhu'] * L)
        if g['pad'] > 0 and e % 8 == 0:
            place(out, pad([midi(root + 12), midi(root + 19), midi(root + 24)], BEAT * 4.3), te, 0.28 * g['pad'] * L)
        if g['bells'] > 0 and e % 2 == 0:
            place(out, bell(midi(PENTA[(e + 4) % len(PENTA)] + 24), 0.5), te, 0.05 * g['bells'])
    # slow-mo sections: muffle the bed (low-pass) for that underwater feel
    for a, b in [(0.0, 1.25), (16.35, 17.55), (33.55, 34.5), (49.45, 53.2)]:
        i, j = int(a * SR), int(b * SR)
        seg = out[i:j].copy()
        out[i:j] = fft_filter(seg, hi=700) * 1.3
    e_ = int((DUR - 0.6) * SR)
    out[e_:] *= np.linspace(1, 0, len(out) - e_)
    return out


# ------------------------------------------------------------------ cue sheet
def build_sfx():
    s = np.zeros(N)
    P = lambda sig, at, g=1.0: place(s, sig, at, g)
    # fire crackle beds
    for a, b in [(0.0, 5.95), (9.6, 13.05), (16.35, 17.55), (24.55, 25.55), (42.35, 47.5), (49.45, 57.0)]:
        P(crackle(b - a), a, 0.35)
    P(slowmo_in(1.3), 0.0, 0.6)
    P(boom(), 0.02, 0.4)
    sys.path.insert(0, HERE)
    import scenes as SCN
    for start, _e, _f, _d, kind in SCN.TIMELINE[1:]:
        if kind in ('up', 'pushin', 'right', 'left'):
            P(whoosh(0.55, True, 1.15), start - 0.3, 0.45)
        elif kind in ('down', 'pullback'):
            P(whoosh(0.55, False, 1.0), start - 0.3, 0.45)
        else:
            P(whoosh(0.7, False, 0.7), start - 0.35, 0.2)
    P(whoosh(0.5, True, 1.1), 1.2, 0.55)
    P(whoosh(0.6, False, 1.0), 2.55, 0.5)
    P(riser(0.6), 3.05, 0.35)
    P(whoosh(0.4, False, 0.6)[::-1].copy(), 3.24, 0.4)  # fire inhales (anticipation)
    P(thud(70, 0.3), 3.08, 0.5)                          # stack lands on "dollars"
    P(fire_burst(1.3), 3.6, 0.9)
    P(boom(), 3.64, 0.5)
    P(boing(), 4.65, 0.3)
    P(whoosh(0.3, True, 1.3), 5.15, 0.4)
    P(paper(0.3), 5.35, 0.35)
    P(riser(0.9), 6.0, 0.3)
    for i in range(4):
        P(pop(650 + i * 90), 6.12 + i * 0.08, 0.25)       # lanterns pop on "Chinese tradition"
    P(heaven(), 6.95, 0.4)
    P(sparkle(), 7.45, 0.35)                             # grandpa appears on "the dead" 
    for k, f in ((8.23, 700), (8.45, 800), (8.68, 900)):
        P(pop(f), k, 0.4)
    P(whoosh(0.6, False, 1.0), 9.65, 0.5)
    P(paper(0.3), 10.3, 0.4)
    P(fire_burst(0.6), 10.9, 0.35)
    P(gong(196, 1.8), 12.36, 0.35)
    P(pop(800), 12.32, 0.3)
    P(paper(0.4), 15.0, 0.3)
    P(paper(0.8) * 0.5, 14.95, 0.25)                    # card rattles at the slot
    P(whoosh(0.3, True, 1.4), 15.83, 0.55)               # sucked in on "except" 
    P(slowmo_in(1.3), 16.3, 0.55)
    P(fire_burst(0.9), 16.4, 0.6)
    for k in (17.5, 18.71, 19.75):
        P(paper(0.18), k, 0.55)
    P(kaching(), 19.95, 0.35)
    P(gong(98, 2.6), 21.48, 0.55)
    P(dundun(), 23.45, 0.4)
    P(whoosh(0.3, True, 1.2), 23.85, 0.4)
    P(boom(), 23.92, 0.35)
    P(boing(), 24.77, 0.35)
    P(harp(), 25.6, 0.4)
    P(sparkle(), 27.82, 0.3)
    P(scratch(), 28.8, 0.45)
    P(bell(1760, 0.6), 30.11, 0.3)
    for i in range(3):
        P(coin(), 31.6 + i * 0.12, 0.45)
    P(paper(0.5), 32.6, 0.4)
    P(slowmo_in(1.0), 33.5, 0.5)
    P(kaching(), 33.61, 0.45)
    P(sparkle(), 33.7, 0.35)
    P(wah(), 35.33, 0.45)
    P(pop(900), 36.4, 0.3)
    P(kaching(), 37.91, 0.35)
    P(dundun(), 38.0, 0.35)
    for i in range(4):
        P(paper(0.15), 39.1 + i * 0.4, 0.45)
        P(pop(500 + i * 120), 39.12 + i * 0.4, 0.25)
    P(crackle(0.34, 60) * 0.6, 40.0, 0.35)               # note trembles
    P(boom(), 40.34, 0.65)
    P(flutter(1.0), 41.2, 0.35)
    P(riser(0.4), 43.3, 0.2)                              # house lifted
    P(fire_burst(0.9), 43.75, 0.55)
    P(honk(), 45.05, 0.4)
    P(fire_burst(0.7), 45.2, 0.4)
    P(blip_tune(), 46.6, 0.35)
    P(fire_burst(0.7), 46.8, 0.4)
    P(riser(0.7), 47.3, 0.3)
    P(sparkle(), 56.4, 0.35)                             # "richer" 
    P(whoosh(0.5, False, 1.3), 47.6, 0.4)
    P(pop(600), 48.5, 0.3)
    P(pop(750), 48.6, 0.3)
    P(success(), 48.78, 0.5)
    P(slowmo_in(1.4), 49.45, 0.5)
    P(whoosh(0.8, False, 0.7), 51.9, 0.3)
    P(slowmo_in(1.6), 53.2, 0.45)
    P(riser(1.5), 53.3, 0.2)
    P(heaven(), 55.2, 0.3)
    P(gong(147, 2.4), 56.3, 0.3)
    return s


def load_voice(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    v = np.frombuffer(raw, np.float32).astype(np.float64)
    out = np.zeros(N)
    out[:min(N, len(v))] = v[:N]
    return out


def duck_env(voice):
    hop = 441
    n = len(voice) // hop
    e = np.sqrt((voice[:n * hop].reshape(n, hop) ** 2).mean(1))
    e = e / (e.max() + 1e-9)
    act = (e > 0.06).astype(float)
    # smooth (attack 30ms, release 250ms)
    sm = np.zeros_like(act)
    acc = 0.0
    for i, a in enumerate(act):
        k = 0.5 if a > acc else 0.04
        acc += (a - acc) * k
        sm[i] = acc
    g = 1 - 0.45 * sm  # ~ -5 dB under voice
    out = np.ones(len(voice))
    out[:n * hop] = np.repeat(g, hop)
    return out


def main():
    vpath, out = sys.argv[1], sys.argv[2]
    voice = load_voice(vpath)
    bgm = make_bgm()
    sfx = build_sfx()
    g = duck_env(voice)
    bgm = bgm / (np.abs(bgm).max() + 1e-9)
    sfx = sfx / (np.abs(sfx).max() + 1e-9)
    voice = voice / (np.abs(voice).max() + 1e-9)
    gs = 1 - (1 - g) * 0.5  # SFX duck lightly under the voice so words stay clear
    mix = voice * 0.85 + bgm * g * 0.2 + sfx * gs * 0.38
    pk = np.abs(mix).max()
    if pk > 0.97:  # clean gain, no clipping or saturation
        mix = mix * 0.97 / pk
    st = np.stack([mix, mix], 1)
    tmp = out + '.raw.wav'
    import wave
    with wave.open(tmp, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
    # two-pass linear loudness normalisation + true-peak limiter (transparent, no distortion)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f",
                        "null", "-"], capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:"
          "measured_thresh={input_thresh}:offset={target_offset},alimiter=limit=0.85:attack=3:release=60:level=false").format(**js)
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af", af, "-ar", str(SR), "-t", f"{DUR:.2f}", out])
    os.remove(tmp)
    print('wrote', out)


if __name__ == '__main__':
    main()
