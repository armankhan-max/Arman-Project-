"""Soundtrack for the Christchurch documentary.

  * Narration: Kokoro TTS (am_michael) -> EQ (warmth + presence), compression, short room reverb.
  * Score: synthesized documentary cues that follow the story (dark drone, sparse piano, pulses,
    taiko-style impacts, strings for grief, a warm build for the recovery). Ducked under the voice.
  * SFX: placed from build/events.json — every text pop, date stamp, quake, flash and explicit sfx cue
    in edl.py gets its sound (rumbles, debris, glass, sirens, alarms, fire, typewriter, clock ticks...).
  * Ambience beds per scene mood (city, night crickets, wind, dust, sirens).
  * Master: limiter + loudness normalised to -14 LUFS (YouTube).

Usage: python3 sound.py  ->  build/mix.wav
"""
import json
import math
from functools import lru_cache
import os
import subprocess
import sys

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from audio import (SR, tt, lp, hp, bp, noise, midi, env_adsr, heartbeat, whoosh, tick, riser, tape_rewind,  # noqa: E402
                   crickets, wind, kick)

BUILD = os.path.join(HERE, "build")
rng = np.random.default_rng(42)


class Track:
    def __init__(self, dur):
        self.x = np.zeros((int(dur * SR) + SR, 2), np.float32)

    def add(self, clip, at, gain=1.0, pan=0.0):
        if clip is None or at < 0:
            return
        c = np.asarray(clip, np.float32)
        if c.ndim == 1:
            l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
            c = np.stack([c * l * 1.414, c * r * 1.414], 1)
        i = int(at * SR)
        j = min(len(self.x), i + len(c))
        if j > i:
            self.x[i:j] += c[: j - i] * gain


# ------------------------------------------------------------------ helpers
def ir(dur=2.2, decay=3.0, bright=4000):
    t = tt(dur)
    n = rng.normal(0, 1, len(t)) * np.exp(-t * decay)
    n = lp(n, bright)
    n[: int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))
    return (n / np.sqrt((n ** 2).sum())).astype(np.float32)


IR_HALL = ir(2.6, 2.6, 3500)
IR_ROOM = ir(0.5, 9.0, 6000)


def verb(x, wet=0.3, kind="hall"):
    h = IR_HALL if kind == "hall" else IR_ROOM
    y = signal.fftconvolve(x, h)
    xx = np.concatenate([x, np.zeros(len(y) - len(x))])
    return (xx * (1 - wet) + y * wet * 3).astype(np.float32)


def fade(x, a=0.01, r=0.1):
    x = x.copy()
    A, Rr = int(a * SR), int(r * SR)
    if A:
        x[:A] *= np.linspace(0, 1, A)
    if Rr:
        x[-Rr:] *= np.linspace(1, 0, Rr)
    return x


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


# ------------------------------------------------------------------ SFX library
def s_boom(dur=4.0):
    t = tt(dur)
    f = 30 + 70 * np.exp(-t * 6)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.3)
    body = lp(noise(dur), 300) * np.exp(-t * 3.5) * 1.5
    crack = hp(noise(dur), 2000) * np.exp(-t * 25) * 0.4
    return verb(norm(sub + body + crack), 0.25)


def s_sub(dur=3.0):
    t = tt(dur)
    f = 26 + 40 * np.exp(-t * 3)
    return verb(norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.2)) * 0.8, 0.2)


def s_hit_soft():
    t = tt(2.0)
    return verb(norm(lp(kick(0.6, 80, 35), 400)) * 0.6 + 0.0 * t[: len(kick(0.6))].sum(), 0.35) if False else \
        verb(norm(np.concatenate([lp(kick(0.6, 80, 35), 400), np.zeros(SR)])) * 0.6, 0.35)


def s_rumble(dur=6.0, amp=1.0, rattle=True):
    t = tt(dur)
    env = np.minimum(1, t / 0.25) * np.exp(-np.maximum(0, t - dur * 0.3) * 1.2)
    lo = lp(noise(dur), 90) * 6
    lo *= 0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 2.3 * t + np.sin(2 * np.pi * 0.7 * t) * 2))
    mid = bp(noise(dur), 120, 500) * 1.2
    x = (lo + mid) * env
    if rattle:
        r = np.zeros_like(t)
        for k in range(int(dur * 40)):
            p = rng.uniform(0, dur * 0.8)
            i = int(p * SR)
            b = bp(noise(0.04), rng.uniform(1500, 5000), 9000) * np.exp(-tt(0.04) * 90)
            r[i:i + len(b)] += b * rng.uniform(0.2, 0.8)
        x += r * env * 0.6
    return norm(x) * amp


def s_debris(dur=3.0):
    x = np.zeros(int(dur * SR) + SR)
    for k in range(int(dur * 25)):
        p = rng.uniform(0, dur) ** 1.3 / dur ** 0.3
        i = int(p * SR)
        d = rng.uniform(0.04, 0.25)
        f = rng.uniform(150, 2500)
        b = bp(noise(d), f * 0.5, f * 2) * np.exp(-tt(d) * rng.uniform(15, 50))
        x[i:i + len(b)] += b * rng.uniform(0.3, 1.0)
    x += lp(noise(len(x) / SR), 200) * np.exp(-np.arange(len(x)) / SR * 1.5) * 1.5
    x += hp(noise(len(x) / SR), 3000) * np.exp(-np.arange(len(x)) / SR * 1.2) * 0.25  # dust hiss
    return verb(norm(x), 0.25)


def s_bricks(dur=2.0):
    x = np.zeros(int(dur * SR) + SR // 2)
    for k in range(int(dur * 60)):
        i = int(rng.uniform(0, dur) ** 1.5 / dur ** 0.5 * SR)
        d = 0.05
        b = bp(noise(d), 600, 4000) * np.exp(-tt(d) * 70) + 0.5 * np.sin(2 * np.pi * rng.uniform(300, 900) * tt(d)) * np.exp(-tt(d) * 60)
        x[i:i + len(b)] += b * rng.uniform(0.2, 1)
    return verb(norm(x), 0.2)


def s_glass(dur=2.5):
    x = np.zeros(int(dur * SR))
    x[: int(0.3 * SR)] += hp(noise(0.3), 3000) * np.exp(-tt(0.3) * 12) * 1.5
    for k in range(70):
        i = int(rng.uniform(0, dur - 0.3) ** 1.6 / (dur - 0.3) ** 0.6 * SR)
        f = rng.uniform(2500, 8000)
        d = 0.2
        b = np.sin(2 * np.pi * f * tt(d)) * np.exp(-tt(d) * rng.uniform(20, 50))
        x[i:i + len(b)] += b * rng.uniform(0.1, 0.5)
    return verb(norm(x) * 0.8, 0.25)


def s_crack():
    d = 1.5
    t = tt(d)
    x = noise(d) * np.exp(-t * 40) + lp(noise(d), 200) * np.exp(-t * 6) * 2
    return verb(norm(x), 0.25)


def s_creak(dur=2.0, f0=180, f1=90):
    t = tt(dur)
    f = f0 + (f1 - f0) * t / dur + 8 * np.sin(2 * np.pi * 6 * t)
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 17 * t))
    return verb(lp(x, 1000) * np.sin(np.pi * t / dur) * 0.5, 0.3)


def s_metal():
    return s_creak(2.5, 120, 60) + 0.5 * s_creak(2.5, 340, 260)


def s_stone():
    return norm(s_boom(3.0)[: 3 * SR] * 0.7 + s_debris(3.0)[: 3 * SR])


def s_collapse(dur=6.0):
    x = s_rumble(dur, 1.0)
    out = np.zeros(int(dur * SR) + 6 * SR)
    out[: len(x)] += x * 0.8
    for k in range(5):
        b = s_boom(3.0) * (0.9 - k * 0.12)
        i = int((k * 0.55 + rng.uniform(0, 0.2)) * SR)
        out[i:i + len(b)] += b[: len(out) - i]
    dbr = s_debris(dur - 1)
    j = int(0.8 * SR)
    out[j:j + len(dbr)] += dbr[: len(out) - j] * 0.8
    return norm(out)


def s_water(dur=4.0):
    t = tt(dur)
    x = lp(noise(dur), 700) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.8 * t)) * 0.8
    for k in range(int(dur * 18)):
        i = int(rng.uniform(0, dur - 0.1) * SR)
        d = 0.06
        f0 = rng.uniform(300, 900)
        b = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 2 * tt(d) / d)) / SR) * np.exp(-tt(d) * 40)
        x[i:i + len(b)] += b * 0.4
    return fade(norm(x) * 0.7, 0.4, 1.0)


def s_alarm(dur=6.0):
    out = np.zeros(int(dur * SR))
    t = tt(dur)
    for k, (f1, f2, rate, pan) in enumerate(((1000, 750, 2.5, 0), (1300, 900, 6, 0), (850, 1250, 1.2, 0))):
        f = np.where(np.sin(2 * np.pi * rate * t + k) > 0, f1, f2)
        x = signal.square(2 * np.pi * np.cumsum(f) / SR) * 0.3
        out += lp(x, 2500 - k * 600) * (0.6 - 0.15 * k)
    return verb(fade(out, 0.05, 1.0), 0.35)


def s_sirens(dur=7.0):
    t = tt(dur)
    f = 750 + 400 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.22 * t))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(2 * np.pi * 2 * np.cumsum(f) / SR)
    x = lp(x, 1800) * np.minimum(1, t / 1.5) * np.minimum(1, (dur - t) / 2)
    return verb(x * 0.35, 0.5)


def s_fire(dur=6.0):
    t = tt(dur)
    roar = lp(noise(dur), 250) * 1.5 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * t))
    x = roar
    for k in range(int(dur * 50)):
        i = int(rng.uniform(0, dur - 0.05) * SR)
        b = hp(noise(0.01), 2000) * np.exp(-tt(0.01) * 400)
        x[i:i + len(b)] += b * rng.uniform(0.3, 1.5)
    return fade(norm(x) * 0.8, 1.0, 1.5)


def s_tap():
    out = np.zeros(3 * SR)
    for k, at in enumerate((0.0, 0.45, 0.9, 1.9, 2.35)):
        d = 0.12
        b = bp(noise(d), 300, 2000) * np.exp(-tt(d) * 50) + np.sin(2 * np.pi * 220 * tt(d)) * np.exp(-tt(d) * 40)
        i = int(at * SR)
        out[i:i + len(b)] += b
    return verb(norm(out) * 0.7, 0.35, "room")


def s_saw(dur=3.5):
    t = tt(dur)
    f = 190 + 20 * np.sin(2 * np.pi * 0.5 * t)
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * 0.4 + bp(noise(dur), 2000, 7000) * 0.6
    return verb(fade(lp(x, 5000), 0.3, 0.5) * 0.6, 0.3)


def s_rockfall(dur=4.0):
    out = s_rumble(dur, 0.7, rattle=False)
    out = np.concatenate([out, np.zeros(2 * SR)])
    for k in range(10):
        i = int((k * 0.35 + rng.uniform(0, 0.15)) * SR)
        b = lp(kick(0.4, 90, 40), 500) * rng.uniform(0.4, 0.9)
        out[i:i + len(b)] += b
    return verb(norm(out), 0.3)


def s_power_down():
    d = 2.5
    t = tt(d)
    f = 60 * np.exp(-t * 0.9)
    hum = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 3) / SR)
    x = hum * np.exp(-t * 1.0) * 0.5
    x[:2000] += hp(noise(2000 / SR), 1000) * 0.8
    return x


def s_shovels(dur=6.0):
    out = np.zeros(int(dur * SR))
    for k in range(int(dur * 2.2)):
        i = int(rng.uniform(0, dur - 0.6) * SR)
        d = 0.45
        b = bp(noise(d), 800, 4000) * np.sin(np.pi * tt(d) / d) ** 2
        out[i:i + len(b)] += b * rng.uniform(0.3, 0.8)
        c = np.sin(2 * np.pi * rng.uniform(1800, 2600) * tt(0.15)) * np.exp(-tt(0.15) * 40)
        out[i:i + len(c)] += c * 0.2
    return fade(out, 0.5, 1.0)


def s_demolish(dur=5.0):
    t = tt(dur)
    eng = lp(signal.sawtooth(2 * np.pi * 42 * t) + 0.5 * noise(dur), 400) * 0.6
    out = eng + s_debris(dur)[: len(t)] * 0.8
    return fade(norm(out), 0.5, 1.0)


def s_birds(dur=4.0):
    out = np.zeros(int(dur * SR))
    for k in range(14):
        i = int(rng.uniform(0, dur - 0.3) * SR)
        d = rng.uniform(0.06, 0.15)
        f0 = rng.uniform(2500, 4500)
        f = f0 + 1500 * np.sin(np.pi * tt(d) / d)
        b = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt(d) / d)
        out[i:i + len(b)] += b * 0.25
    return verb(out, 0.3)


def s_drone_swell(dur=4.0):
    t = tt(dur)
    x = (np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 82.4 * t) + 0.3 * np.sin(2 * np.pi * 110.5 * t))
    x += lp(noise(dur), 300) * 0.5
    env = (t / dur) ** 2 * np.minimum(1, (dur - t) / 0.3)
    return x * env * 0.5


def s_final():
    out = np.concatenate([s_drone_swell(3.0), np.zeros(5 * SR)])
    b = s_boom(5.0)
    out[3 * SR: 3 * SR + len(b)] += b[: len(out) - 3 * SR]
    return norm(out)


def s_typekey():
    d = 0.06
    b = bp(noise(d), 1500, 6000) * np.exp(-tt(d) * 90) + 0.4 * lp(noise(d), 400) * np.exp(-tt(d) * 60)
    return b * 0.6


def s_tick():
    d = 0.05
    return (np.sin(2 * np.pi * 3200 * tt(d)) * np.exp(-tt(d) * 120) + hp(noise(d), 4000) * np.exp(-tt(d) * 200) * 0.5) * 0.5


def s_pop_hit():
    d = 1.5
    t = tt(d)
    x = lp(kick(0.5, 120, 40), 600)
    out = np.zeros(int(d * SR))
    out[: len(x)] += x
    out += hp(noise(d), 1500) * np.exp(-t * 18) * 0.25
    return verb(norm(out) * 0.7, 0.3)


def s_whoosh(up=True):
    return whoosh(0.7, up, 0.6)


SFX = {"boom": s_boom, "sub": s_sub, "hit_soft": s_hit_soft, "rumble_s": lambda: s_rumble(2.5, 0.6),
       "rumble_l": lambda: s_rumble(8.0, 1.0), "debris": s_debris, "bricks": s_bricks, "glass": s_glass,
       "crack": s_crack, "creak": s_creak, "metal": s_metal, "stone": s_stone, "collapse": s_collapse,
       "water": s_water, "alarms": s_alarm, "sirens": s_sirens, "fire": s_fire, "tap": s_tap, "saw": s_saw,
       "rockfall": s_rockfall, "power_down": s_power_down, "shovels": s_shovels, "demolish": s_demolish,
       "birds": s_birds, "crickets": lambda: crickets(6.0, 0.6), "city": lambda: s_city(6.0) * 0.8,
       "drone_swell": s_drone_swell, "riser": lambda: riser(2.0, 0.8), "rewind": lambda: tape_rewind(2.3, 0.8),
       "heartbeat": lambda: np.concatenate([heartbeat(1.0), np.zeros(int(0.1 * SR)), heartbeat(1.0)]),
       "final": s_final}
SFX_GAIN = {"boom": 0.9, "sub": 0.8, "rumble_l": 0.8, "rumble_s": 0.6, "debris": 0.55, "bricks": 0.5, "glass": 0.45,
            "crack": 0.6, "collapse": 0.9, "alarms": 0.18, "sirens": 0.25, "fire": 0.35, "water": 0.3, "birds": 0.25,
            "crickets": 0.25, "city": 0.3, "tap": 0.5, "saw": 0.25, "shovels": 0.35, "creak": 0.35, "metal": 0.3,
            "rockfall": 0.6, "stone": 0.7, "heartbeat": 0.7, "drone_swell": 0.35, "riser": 0.4, "rewind": 0.45,
            "hit_soft": 0.5, "power_down": 0.4, "demolish": 0.4, "final": 0.9}


def s_city(dur):
    t = tt(dur)
    x = lp(noise(dur), 500) * 0.6 + bp(noise(dur), 500, 2000) * 0.15
    return x * (0.8 + 0.2 * np.sin(2 * np.pi * 0.1 * t))


# ------------------------------------------------------------------ music
NOTE = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def m(name, octave):
    return midi(12 * (octave + 1) + NOTE[name])


@lru_cache(maxsize=512)
def piano(f, dur=4.0, vel=1.0):
    t = tt(dur)
    x = np.zeros_like(t)
    for k in range(1, 10):
        fk = f * k * math.sqrt(1 + 0.0004 * k * k)
        if fk > 10000:
            break
        x += (0.7 ** (k - 1)) * np.sin(2 * np.pi * fk * t) * np.exp(-t * (0.9 + k * 0.55) * (1 + f / 800))
    x += lp(noise(0.02), 3000)[: len(t)].sum() * 0
    x *= env_adsr(len(t), 0.004, 0.05, 1.0, 0.3)
    return x * 0.35 * vel


def strings(freqs, dur, att=2.5, rel=2.5, bright=0.35):
    t = tt(dur)
    x = np.zeros_like(t)
    for f in freqs:
        for det in (-0.006, -0.002, 0.003, 0.007):
            vib = 1 + 0.004 * np.sin(2 * np.pi * (5 + det * 100) * t + rng.uniform(0, 6))
            ph = 2 * np.pi * np.cumsum(f * (1 + det) * vib) / SR
            x += signal.sawtooth(ph) * 0.25
    x = lp(x, 900 + 2500 * bright)
    return x / max(1, len(freqs) * 4) * env_adsr(len(t), att, 0.1, 1.0, rel) * 1.2


def drone(dur, root=m("D", 1), dark=1.0):
    t = tt(dur)
    x = (np.sin(2 * np.pi * root * t) + 0.5 * np.sin(2 * np.pi * root * 1.5 * t + 1) + 0.35 * np.sin(2 * np.pi * root * 2.01 * t))
    x += lp(noise(dur), 200) * 0.6 * dark
    sweep = 0.7 + 0.3 * np.sin(2 * np.pi * t / 11)
    return x * sweep * env_adsr(len(t), 3.0, 0.1, 1.0, 3.0) * 0.4


@lru_cache(maxsize=4)
def taiko():
    d = 2.0
    t = tt(d)
    f = 50 + 60 * np.exp(-t * 12)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4) + bp(noise(d), 100, 900) * np.exp(-t * 18) * 0.6
    return verb(x * 0.8, 0.3)


def pulse_tick(bpm, dur):
    out = np.zeros(int(dur * SR))
    beat = 60 / bpm
    k = 0
    while k * beat < dur - 0.1:
        c = s_tick() * (1.0 if k % 4 == 0 else 0.55)
        i = int(k * beat * SR)
        out[i:i + len(c)] += c
        k += 1
    return out


CH = {  # chord tones (name, octave)
    "Dm": [("D", 3), ("F", 3), ("A", 3)], "Bb": [("Bb", 2), ("D", 3), ("F", 3)], "F": [("F", 3), ("A", 3), ("C", 4)],
    "C": [("C", 3), ("E", 3), ("G", 3)], "Gm": [("G", 2), ("Bb", 2), ("D", 3)], "A": [("A", 2), ("C#", 3), ("E", 3)],
    "Am": [("A", 2), ("C", 3), ("E", 3)], "G": [("G", 2), ("B", 2), ("D", 3)], "Em": [("E", 3), ("G", 3), ("B", 3)],
    "D": [("D", 3), ("F#", 3), ("A", 3)],
}


def cue_dark(tr, a, b, piano_on=True, gain=1.0, prog=("Dm", "Bb", "Gm", "A")):
    tr.add(drone(b - a + 3), a, 0.5 * gain)
    bar = 6.0
    t, i = a, 0
    while t < b - 1:
        ch = CH[prog[i % len(prog)]]
        tr.add(strings([m(n, o) for n, o in ch], min(bar, b - t) + 2.5, 2.5, 2.5, 0.2), t, 0.45 * gain)
        if piano_on:
            for k, (n, o) in enumerate([ch[0], ch[2], ch[1]]):
                nt = t + 0.5 + k * 1.8
                if nt < b:
                    tr.add(piano(m(n, o + 1), 4.0, 0.8), nt, 0.55 * gain, pan=-0.2 + 0.2 * k)
        t += bar
        i += 1


def cue_pulse(tr, a, b, bpm=84, gain=1.0, prog=("Dm", "Bb", "F", "C")):
    beat = 60 / bpm
    tr.add(pulse_tick(bpm, b - a), a, 0.35 * gain, pan=0.3)
    t, i = a, 0
    while t < b - 0.5:
        ch = CH[prog[i % len(prog)]]
        bar = beat * 8
        tr.add(strings([m(n, o) for n, o in ch], min(bar, b - t) + 1.5, 1.0, 1.5, 0.3), t, 0.35 * gain)
        for k in range(8):
            nt = t + k * beat
            if nt < b:
                n, o = ch[0]
                tr.add(lp(piano(m(n, o - 1), 1.2, 0.8), 600), nt, 0.4 * gain)
        for k, (n, o) in enumerate(ch):
            nt = t + beat * (2 + k * 2)
            if nt < b:
                tr.add(piano(m(n, o + 1), 2.5, 0.6), nt, 0.35 * gain, pan=0.3 - 0.3 * k)
        t += bar
        i += 1


def cue_chaos(tr, a, b, gain=1.0):
    tr.add(drone(b - a + 3, m("D", 1), 1.5), a, 0.6 * gain)
    t = a
    k = 0
    while t < b:
        tr.add(taiko(), t, (0.7 if k % 4 == 0 else 0.4) * gain)
        t += 1.5 if k % 4 != 3 else 0.75
        k += 1
    t = a
    while t < b - 1:
        tr.add(strings([m("D", 3), m("Eb", 3), m("A", 3)], min(8.0, b - t) + 2, 1.0, 2.0, 0.6), t, 0.35 * gain)
        t += 8


def cue_grief(tr, a, b, gain=1.0, prog=("Dm", "Bb", "F", "A")):
    bar = 6.5
    t, i = a, 0
    while t < b - 1:
        ch = CH[prog[i % len(prog)]]
        tr.add(strings([m(n, o) for n, o in ch] + [m(ch[0][0], ch[0][1] - 1)], min(bar, b - t) + 3, 3.0, 3.0, 0.25), t, 0.6 * gain)
        mel = [ch[2], ch[1], ch[0], ch[1]]
        for k, (n, o) in enumerate(mel):
            nt = t + 0.3 + k * 1.5
            if nt < b:
                tr.add(piano(m(n, o + 1), 4.5, 0.7), nt, 0.5 * gain)
        t += bar
        i += 1


def cue_hope(tr, a, b, gain=1.0, prog=("D", "A", "Bm", "G")):
    CH["Bm"] = [("B", 2), ("D", 3), ("F#", 3)]
    bar = 5.0
    t, i = a, 0
    while t < b - 1:
        g = 0.5 + 0.5 * (t - a) / max(1, b - a)
        ch = CH[prog[i % len(prog)]]
        tr.add(strings([m(n, o) for n, o in ch], min(bar, b - t) + 2.5, 1.8, 2.5, 0.3 + 0.3 * g), t, 0.45 * gain)
        for k, idx in enumerate([0, 1, 2, 1, 2, 0, 1, 2]):
            nt = t + k * bar / 8
            if nt < b:
                n, o = ch[idx]
                tr.add(piano(m(n, o + 1), 2.0, 0.55), nt, 0.4 * gain * g, pan=-0.3 if k % 2 else 0.3)
        tr.add(lp(piano(m(ch[0][0], ch[0][1] - 1), 4.0), 500), t, 0.5 * gain)
        t += bar
        i += 1


def build_music(ev, dur):
    tr = Track(dur)
    P = {int(k): v for k, v in ev["paras"].items()}

    def p(i):
        return P[i] if i in P else dur

    cues = [
        ("chaos", 0, 3, 0.8), ("dark", 3, 7, 0.9), ("dark_np", 7, 11, 0.8), ("hope", 11, 14, 0.5), ("dark", 14, 19, 0.8),
        ("pulse", 20, 27, 0.8), ("dark", 27, 33, 0.85), ("hope", 33, 40, 0.55), ("pulse_fast", 40, 41, 0.6),
        ("chaos", 42, 43, 0.7), ("pulse", 43, 51, 0.7), ("chaos", 51, 67, 0.75), ("grief", 68, 80, 0.75),
        ("dark", 80, 93, 0.8), ("grief", 93, 98, 0.7), ("hope", 98, 103, 0.75), ("grief", 103, 104, 0.8),
        ("pulse", 104, 113, 0.7), ("grief", 113, 121, 0.7), ("hope", 121, 129, 0.8), ("grief", 129, 132, 0.8),
    ]
    for kind, i0, i1, g in cues:
        a, b = p(i0), p(i1) if i1 in P else dur - 2
        if kind == "chaos":
            cue_chaos(tr, a, b, g)
        elif kind == "dark":
            cue_dark(tr, a, b, True, g)
        elif kind == "dark_np":
            cue_dark(tr, a, b, False, g)
        elif kind == "pulse":
            cue_pulse(tr, a, b, 84, g)
        elif kind == "pulse_fast":
            cue_pulse(tr, a, b, 120, g)
        elif kind == "grief":
            cue_grief(tr, a, b, g)
        elif kind == "hope":
            cue_hope(tr, a, b, g)
    x = tr.x
    # silences that make moments hit: "It wasn't.", "12:51 PM.", "It falls.", "Smoke."
    for pi in (19, 41, 61, 67):
        if pi in P:
            a = P[pi]
            b = P.get(pi + 1, a + 2)
            gate = np.ones(len(x), np.float32)
            i0, i1 = int((a - 0.2) * SR), int(b * SR)
            gate[i0:i1] = 0
            gate = lp(gate.astype(np.float64), 8, 1).astype(np.float32)
            x *= gate[:, None]
    # end fade
    n = len(x)
    e = int((dur - 1.0) * SR)
    x[e:] *= np.linspace(1, 0, n - e)[:, None]
    return x


# ------------------------------------------------------------------ SFX timeline
def build_sfx(ev, dur):
    tr = Track(dur)
    cache = {}

    def get(name):
        if name not in cache:
            cache[name] = np.asarray(SFX[name](), np.float32)
        return cache[name]

    count = 0
    for s in ev["sfx"]:
        tr.add(get(s["name"]), s["t"] + s.get("off", 0) - (0.05 if s["name"] in ("boom", "collapse") else 0),
               SFX_GAIN.get(s["name"], 0.5) * s.get("gain", 1.0), pan=rng.uniform(-0.2, 0.2))
        count += 1
    for q in ev["quakes"]:
        r = s_rumble(q["dur"] + 1.5, 1.0)
        tr.add(r, q["t"], 0.45 * min(1.4, q["amp"]))
        count += 1
    for x in ev["texts"]:
        k = x["kind"]
        if k == "pop":
            tr.add(s_pop_hit(), x["t"], 0.55)
            tr.add(s_whoosh(True), x["t"] - 0.35, 0.35)
        elif k == "date":
            n = len(x["text"])
            for i in range(n):
                tr.add(s_typekey(), x["t"] + 0.9 * i / n, 0.5, pan=rng.uniform(-0.2, 0.2))
            for i in range(len(x.get("sub", ""))):
                tr.add(s_typekey(), x["t"] + 1.0 + 0.6 * i / max(1, len(x["sub"])), 0.4)
            tr.add(s_typekey() * 1.5, x["t"] + 1.65, 0.5)
        elif k in ("lower", "callout"):
            tr.add(s_whoosh(True), x["t"] - 0.1, 0.25, pan=-0.4)
        elif k in ("chapter", "title"):
            tr.add(s_boom(), x["t"], 0.45)
            tr.add(s_whoosh(False), x["t"] - 0.4, 0.3)
        count += 1
    prev_kind = None
    for s in ev["shots"]:
        if s.get("flash"):
            tr.add(s_whoosh(True), s["start"] - 0.5, 0.35)
        if s["kind"] == "gfx":
            nm_ = s["name"]
            if nm_ == "map":
                tr.add(s_whoosh(False), s["start"] - 0.2, 0.3)
            if nm_ == "clock":
                d = s["end"] - s["start"]
                tk = 0.0
                while tk < d:
                    tr.add(s_tick(), s["start"] + tk, 0.5)
                    tk += 1.0 if not s.get("fast") else max(0.12, 1.0 - tk / d * 0.9)
            if nm_ in ("counter", "quote"):
                tr.add(s_sub(), s["start"], 0.35)
            if nm_ in ("seismo",):
                tr.add(s_rumble(4.0, 0.6), s["start"] + (s["end"] - s["start"]) * 0.3, 0.4)
            if nm_ in ("reasons", "compare", "sway", "depth", "soil", "timeline", "world", "doc", "gforce"):
                if prev_kind != nm_:
                    tr.add(s_whoosh(True), s["start"] - 0.25, 0.25)
            count += 1
        prev_kind = s["name"] if s["kind"] == "gfx" else None
    print("sfx events", count)
    return tr.x


def build_ambience(ev, dur):
    tr = Track(dur)
    for s in ev["shots"]:
        a, b = s["start"], s["end"]
        d = b - a + 0.6
        if d <= 0.3:
            continue
        g = s.get("grade") if s["kind"] == "plate" else None
        if g == "night":
            tr.add(fade(crickets(d, 1.0) * 0.35 + wind(d, 0.5, int(a)) * 0.4, 0.3, 0.3), a, 0.35)
        elif g in ("day", "hope"):
            tr.add(fade(s_city(d) * 0.5, 0.3, 0.3), a, 0.25)
        elif g == "disaster":
            tr.add(fade(wind(d, 0.6, int(a)) + hp(noise(d), 3000) * 0.05, 0.3, 0.3), a, 0.35)
        elif g in ("dark", "mourn", "memory", "dusk", "dawn"):
            tr.add(fade(wind(d, 0.5, int(a)), 0.3, 0.3), a, 0.25)
    return tr.x


# ------------------------------------------------------------------ voice
def load(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def peq(x, f0, gain_db, q=0.8, kind="peak"):
    A = 10 ** (gain_db / 40)
    w0 = 2 * math.pi * f0 / SR
    al = math.sin(w0) / (2 * q)
    cs = math.cos(w0)
    if kind == "peak":
        b = [1 + al * A, -2 * cs, 1 - al * A]
        a = [1 + al / A, -2 * cs, 1 - al / A]
    else:  # low shelf
        sq = 2 * math.sqrt(A) * al
        b = [A * ((A + 1) - (A - 1) * cs + sq), 2 * A * ((A - 1) - (A + 1) * cs), A * ((A + 1) - (A - 1) * cs - sq)]
        a = [(A + 1) + (A - 1) * cs + sq, -2 * ((A - 1) + (A + 1) * cs), (A + 1) + (A - 1) * cs - sq]
    return signal.lfilter(b, a, x)


def compress(x, thr_db=-20, ratio=3.0):
    env = np.sqrt(lp(x ** 2, 15, 1).clip(1e-12))
    db = 20 * np.log10(env + 1e-9)
    over = np.maximum(0, db - thr_db)
    gain = 10 ** (-over * (1 - 1 / ratio) / 20)
    return x * gain


def process_voice(v):
    v = hp(v, 70)
    v = peq(v, 140, 2.5, kind="shelf")
    v = peq(v, 3200, 2.0, 1.0)
    v = peq(v, 7500, -2.0, 1.5)
    v = compress(v / (np.max(np.abs(v)) + 1e-9), -18, 2.5)
    v = v / (np.max(np.abs(v)) + 1e-9)
    wet = signal.fftconvolve(v, IR_ROOM)[: len(v)]
    v = v + wet * 0.12
    return v / (np.max(np.abs(v)) + 1e-9)


def envelope(x):
    e = np.sqrt(lp(x ** 2, 8, 1).clip(0))
    return e


def main():
    ev = json.load(open(os.path.join(BUILD, "events.json")))
    dur = ev["total"]
    voice = process_voice(load(os.path.join(HERE, "voice_raw.wav")))
    n = int(dur * SR)
    voice = np.pad(voice, (0, max(0, n - len(voice))))[:n]
    print("music...", flush=True)
    music = build_music(ev, dur)[:n].astype(np.float64)
    print("sfx...", flush=True)
    fx = build_sfx(ev, dur)[:n].astype(np.float64)
    print("ambience...", flush=True)
    amb = build_ambience(ev, dur)[:n].astype(np.float64)
    music = music / (np.percentile(np.abs(music), 99.9) + 1e-9)
    env = envelope(voice)
    env = env / (np.percentile(env, 95) + 1e-9)
    duck = 1.0 - 0.6 * np.clip(env, 0, 1)
    duck = lp(duck, 3, 1)
    music *= (0.22 * duck)[:, None]
    fx = fx / (np.percentile(np.abs(fx), 99.95) + 1e-9) * 0.6
    fx *= (1.0 - 0.35 * np.clip(env, 0, 1))[:, None]
    amb = amb / (np.percentile(np.abs(amb), 99.9) + 1e-9) * 0.09
    v = voice * 0.85
    mix = np.stack([v, v], 1) + music + fx + amb
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)
    os.makedirs(BUILD, exist_ok=True)
    raw = os.path.join(BUILD, "mix_raw.wav")
    from scipy.io import wavfile
    wavfile.write(raw, SR, (mix * 32000).astype(np.int16))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000",
                    os.path.join(BUILD, "mix.wav")], check=True)
    print("wrote build/mix.wav")


if __name__ == "__main__":
    main()
