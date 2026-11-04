"""Synthesise original BGM + SFX for the Eiffel Tower short and mix with the voiceover.

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
DUR = 81.12
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
    if i >= len(buf):
        return
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


# ------------------------------------------------------------------ BGM
BPM = 112
BEAT = 60 / BPM
# D minor: Dm Gm A7 Dm | Dm Bb A7 Dm
PROG = [(50, [62, 65, 69]), (55, [62, 67, 70]), (57, [61, 64, 67]), (50, [62, 65, 69]),
        (50, [62, 65, 69]), (58, [62, 65, 70]), (57, [61, 64, 67]), (50, [62, 65, 69])]
WALK = [0, 3, 5, 7]
MELODY = [74, 72, 70, 69, 70, 69, 67, 65, 69, 67, 65, 64, 65, None, 62, None]  # sneaky accordion line


def sections(t):
    """layer gains for time t -> dict"""
    g = dict(bass=1.0, pizz=1.0, drums=1.0, acc=0.0, pad=0.0, level=1.0)
    if t < 4.04:
        g.update(acc=0.8)
    elif t < 14.6:
        g.update(drums=0.6)
    elif t < 34.1:
        pass
    elif t < 35.5:
        g.update(drums=1.4, level=1.15)
    elif t < 45.77:  # suspicious: thinner
        g.update(drums=0.25, pizz=0.8)
    elif t < 47.6:
        g.update(level=0.0)
    elif t < 55.55:
        g.update(drums=0.8)
    elif t < 59.6:
        g.update(acc=1.0, drums=1.2, level=1.1)
    elif t < 62.28:
        g.update(drums=0.4, pizz=0.7)
    elif t < 63.4:
        g.update(level=0.0)
    elif t < 64.22:
        g.update(drums=0.0, bass=0.6)
    elif t < 69.55:
        g.update(drums=0.0, pizz=0.35, bass=0.5, pad=1.0, level=0.9)
    elif t < 78.12:
        g.update(drums=0.9)
    else:
        g.update(acc=1.0, drums=1.1, level=1.05)
    return g


def make_bgm():
    out = np.zeros(N)
    nbeats = int(DUR / BEAT) + 2
    for b in range(nbeats):
        tb = b * BEAT
        bar = b // 4
        bi = b % 4
        root, chord = PROG[bar % len(PROG)]
        g = sections(tb)
        if g['level'] <= 0:
            continue
        L = g['level']
        # walking bass
        place(out, bass(midi(root - 12 + WALK[bi]), BEAT * 0.95), tb, 0.55 * g['bass'] * L)
        # pizzicato off-beat stabs
        for n in chord:
            place(out, pluck(midi(n), 0.3), tb + BEAT / 2, 0.11 * g['pizz'] * L)
        if bi in (0, 2):
            place(out, pluck(midi(chord[0] + 12), 0.25, 0.8), tb, 0.06 * g['pizz'] * L)
        # drums
        if g['drums'] > 0:
            if bi in (0, 2):
                place(out, kick(), tb, 0.45 * g['drums'] * L)
            if bi in (1, 3):
                place(out, brush(), tb, 0.35 * g['drums'] * L)
            place(out, hat(), tb, 0.25 * g['drums'] * L)
            place(out, hat(), tb + BEAT / 2, 0.15 * g['drums'] * L)
        # accordion melody (8th notes)
        if g['acc'] > 0:
            for k in range(2):
                n = MELODY[(b * 2 + k) % len(MELODY)]
                if n is not None:
                    place(out, accordion(midi(n), BEAT / 2 * 0.95), tb + k * BEAT / 2, 0.14 * g['acc'] * L)
        if g['pad'] > 0 and bi == 0:
            place(out, pad([midi(x - 12) for x in chord], BEAT * 4.2), tb, 0.35 * g['pad'] * L)
    # hard gates for the silence beats (quick fades)
    for a, b in ((45.77, 47.6), (62.28, 63.4)):
        i, j = int(a * SR), int(b * SR)
        f = int(0.03 * SR)
        out[i - f:i] *= np.linspace(1, 0, f)
        out[i:j] = 0
        out[j:j + f] *= np.linspace(0, 1, f)
    # tail fade
    e = int((DUR - 0.25) * SR)
    out[e:] *= np.linspace(1, 0, len(out) - e)
    return out


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


# ------------------------------------------------------------------ cue sheet
def build_sfx():
    s = np.zeros(N)
    P = lambda sig, at, g=1.0: place(s, sig, at, g)
    P(boom(), 0.02, 0.5)
    P(whoosh(0.25, False), 1.06, 0.35)
    P(stamp(), 1.28, 0.8)
    P(whoosh(0.35, True), 1.95, 0.4)
    P(stamp(), 2.99, 1.0)
    P(bell(1568, 0.8), 3.03, 0.25)
    # transitions
    sys.path.insert(0, HERE)
    import scenes as SCN
    for start, _e, _f, _d, kind in SCN.TIMELINE[1:]:
        if kind == 'whip':
            P(whoosh(0.4, True, 1.2), start - 0.22, 0.55)
        elif kind == 'dissolve':
            P(whoosh(0.6, False, 0.7), start - 0.3, 0.25)
    P(pop(700), 4.58, 0.45)
    P(creak(0.8, 160), 6.9, 0.35)
    P(boing(), 7.37, 0.35)
    P(creak(0.9, 120), 8.55, 0.5)
    P(ping(), 9.05, 0.4)
    P(paper(0.9), 9.95, 0.45)
    for k in (11.58, 11.77, 12.0, 12.36, 12.6, 12.91):
        P(paper(0.18), k - 0.05, 0.6)
    P(rip(0.35), 13.8, 0.55)
    P(paper(0.5), 14.95, 0.4)
    P(pop(900), 15.55, 0.4)
    P(bell(1760, 0.6), 15.6, 0.15)
    for k in (17.83, 18.09, 18.58):
        P(paper(0.15), k - 0.25, 0.3)
        P(stamp(), k, 0.9)
    P(sparkle(), 20.6, 0.35)
    P(bell(988, 1.0), 20.95, 0.25)
    for i in range(6):
        P(pop(500 + i * 70), 23.25 + i * 0.2, 0.35)
    P(whoosh(0.6, False, 0.6), 24.7, 0.4)
    P(dundun(), 25.1, 0.3)
    P(fft_filter(noise(0.5), lo=3000, hi=9000) * np.sin(np.pi * t_(0.5) / 0.5) * 0.4, 26.8)
    P(creak(0.35, 900), 27.38, 0.35)
    P(paper(0.25), 28.62, 0.5)
    P(kaching(), 29.78, 0.45)
    P(paper(0.25), 30.38, 0.5)
    P(gavel(), 31.1, 1.0)
    P(fft_filter(noise(0.7), lo=3500, hi=9000) * np.sin(np.pi * t_(0.7) / 0.7) * 0.5, 33.15)
    P(murmur(1.45), 34.1, 0.35)
    P(boom(), 34.8, 0.35)
    P(pop(900), 36.6, 0.4)
    P(reel(0.45), 37.6, 0.5)
    P(pop(1200), 38.44, 0.4)
    P(dundun(), 39.35, 0.4)
    k = 40.8
    while k < 42.9:
        P(tick(), k, 0.6)
        k += 0.25
    P(gulp(), 42.4, 0.5)
    P(steps(4, 0.22), 43.2, 0.5)
    P(fft_filter(noise(0.45), lo=3000, hi=9000) * np.sin(np.pi * t_(0.45) / 0.45) * 0.35, 45.15)
    P(scratch(), 45.98, 0.6)
    P(boing(), 46.95, 0.3)
    P(sparkle(), 48.36, 0.4)
    P(stamp(), 50.28, 0.7)
    P(bell(1568, 0.9), 50.3, 0.25)
    P(thud(90, 0.3), 53.4, 0.6)
    P(paper(0.3), 54.6, 0.5)
    P(kaching(), 55.0, 0.45)
    P(whistle_train(1.0), 55.6, 0.5)
    P(chug(4.0), 55.55, 0.35)
    P(pop(500), 58.0, 0.5)
    P(paper(1.0), 58.1, 0.5)
    for i in range(7):
        P(paper(0.12), 60.96 + i * 0.22, 0.35)
    P(crickets(1.0), 62.4, 2.0)
    P(bell(1318, 0.8), 63.9, 0.2)
    P(rain(5.2), 64.2, 1.0)
    P(thunder(), 66.15, 0.6)
    P(murmur(2.2, False), 67.35, 0.2)
    P(sad_trombone(), 68.0, 0.55)
    P(bell(988, 0.9), 70.6, 0.25)
    for i in range(6):
        P(pop(600 + i * 60), 71.95 + i * 0.12, 0.3)
    P(ff_whir(1.6), 73.55, 0.6)
    P(gavel(), 74.79, 1.0)
    P(door_slam(), 75.66, 0.6)
    P(steps(3, 0.15), 75.7, 0.4)
    P(police_whistle(0.6), 77.42, 0.5)
    P(door_slam(), 78.15, 0.7)
    P(ship_horn(1.4), 79.25, 0.5)
    P(waves(1.9), 79.2, 0.6)
    P(stinger(), 80.75, 0.5)
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
    g = np.array(duck_env(voice))
    bgm = bgm / (np.abs(bgm).max() + 1e-9)
    sfx = sfx / (np.abs(sfx).max() + 1e-9)
    vpk = np.abs(voice).max()
    mix = voice / vpk * 0.9 + bgm * g * 0.21 + sfx * 0.42
    mix = np.tanh(mix * 1.1) / 1.1
    st = np.stack([mix, mix], 1).astype(np.float32)
    tmp = out + '.raw.wav'
    import wave
    with wave.open(tmp, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.0:LRA=11",
                           "-ar", str(SR), "-t", f"{DUR:.2f}", out])
    os.remove(tmp)
    print('wrote', out)


if __name__ == '__main__':
    main()
