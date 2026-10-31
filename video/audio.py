"""Procedural soundtrack: background music cues, SFX and ambience, mixed under the voiceover.

Everything is synthesized here (no samples), so the soundtrack is original and royalty-free.

Usage:
  python audio.py --voice voice.mp3 --out mix.wav [--stems DIR]
"""
import argparse
import os
import subprocess

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100
rng = np.random.default_rng(11)


# ------------------------------------------------------------------ basics
def tt(dur):
    return np.arange(int(dur * SR)) / SR


def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.2):
    e = np.ones(n) * s
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    A = min(A, n)
    e[:A] = np.linspace(0, 1, A, endpoint=False)
    D2 = min(D, n - A)
    e[A:A + D2] = np.linspace(1, s, D2, endpoint=False)
    if R > 0 and n > R:
        e[-R:] *= np.linspace(1, 0, R)
    return e


def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc / (SR / 2), 0.99), "low")
    return signal.lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = signal.butter(order, min(fc / (SR / 2), 0.99), "high")
    return signal.lfilter(b, a, x)


def bp(x, f1, f2, order=2):
    b, a = signal.butter(order, [f1 / (SR / 2), min(f2 / (SR / 2), 0.99)], "band")
    return signal.lfilter(b, a, x)


def noise(dur):
    return rng.standard_normal(int(dur * SR))


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def nm(name):
    """'A3' -> midi number."""
    return NOTE[name[:-1]] + 12 * (int(name[-1]) + 1)


class Track:
    def __init__(self, dur):
        self.L = np.zeros(int(dur * SR) + SR * 4)
        self.R = np.zeros_like(self.L)

    def add(self, x, at, gain=1.0, pan=0.0):
        i = int(at * SR)
        if i < 0:
            x = x[-i:]
            i = 0
        j = min(i + len(x), len(self.L))
        x = x[: j - i] * gain
        self.L[i:j] += x * np.sqrt(0.5 * (1 - pan))
        self.R[i:j] += x * np.sqrt(0.5 * (1 + pan))

    def stereo(self, n):
        return np.stack([self.L[:n], self.R[:n]], axis=1)


# ------------------------------------------------------------------ instruments
def pluck(f, dur=1.2, bright=1.0, decay=3.0):
    t = tt(dur)
    x = np.zeros_like(t)
    for k in range(1, 9):
        if f * k > 12000:
            break
        x += (bright ** (k - 1)) / k * np.sin(2 * np.pi * f * k * t + k) * np.exp(-t * (decay + k * 1.6))
    x *= env_adsr(len(t), 0.003, 0.05, 1.0, 0.05)
    return x * 0.5


def marimba(f, dur=0.8):
    t = tt(dur)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 6) + 0.35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 18)
    x *= env_adsr(len(t), 0.002, 0.02, 1.0, 0.05)
    return x * 0.55


def bell_tone(f, dur=2.0):
    t = tt(dur)
    x = (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.5) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 4)
         + 0.25 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 7))
    return x * env_adsr(len(t), 0.002, 0.01, 1.0, 0.1) * 0.4


def pad(freqs, dur, attack=1.5, release=1.5, bright=0.5, vib=0.0):
    t = tt(dur)
    x = np.zeros_like(t)
    for f in freqs:
        for det in (-0.004, 0.0, 0.004):
            ph = rng.uniform(0, 6.28)
            ff = f * (1 + det) * (1 + vib * 0.003 * np.sin(2 * np.pi * 5 * t))
            for k, amp in ((1, 1.0), (2, 0.5 * bright), (3, 0.25 * bright), (4, 0.12 * bright)):
                x += amp * np.sin(2 * np.pi * ff * k * t + ph * k)
    x /= max(1, len(freqs) * 3)
    return x * env_adsr(len(t), attack, 0.1, 1.0, release) * 0.6


def bass(f, dur, a=0.01, r=0.15):
    t = tt(dur)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) + 0.1 * np.sin(2 * np.pi * 3 * f * t)
    return x * env_adsr(len(t), a, 0.1, 0.8, r) * 0.6


def kick(dur=0.35, f0=110, f1=42, gain=1.0):
    t = tt(dur)
    f = f1 + (f0 - f1) * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * gain


def hat(dur=0.06, gain=0.25):
    x = hp(noise(dur), 7000) * np.exp(-tt(dur) * 70)
    return x * gain


def shaker(dur=0.09, gain=0.2):
    x = bp(noise(dur), 4000, 10000) * np.sin(np.linspace(0, np.pi, int(dur * SR))) ** 2
    return x * gain


def clap(gain=0.3):
    d = 0.18
    x = bp(noise(d), 900, 4000) * np.exp(-tt(d) * 25)
    return x * gain


def heartbeat(gain=1.0):
    a = lp(kick(0.25, 70, 38), 180)
    out = np.zeros(int(0.6 * SR))
    out[: len(a)] += a
    i = int(0.22 * SR)
    out[i:i + len(a)] += a * 0.7
    return out * gain


# ------------------------------------------------------------------ SFX
def whoosh(dur=0.6, up=True, gain=0.5):
    n = noise(dur)
    t = tt(dur)
    out = np.zeros_like(n)
    seg = 512
    for i in range(0, len(n), seg):
        p = i / len(n)
        fc = 300 + 5000 * (p if up else 1 - p)
        out[i:i + seg] = bp(n[max(0, i - 2048):i + seg], fc * 0.7, fc * 1.4)[-len(n[i:i + seg]):]
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return out * e * gain * 1.8


def pop(f=600, gain=0.5):
    d = 0.12
    t = tt(d)
    f = f * (1 + 1.5 * np.exp(-t * 40))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30) * gain


def click(gain=0.4):
    d = 0.03
    return bp(noise(d), 2000, 8000) * np.exp(-tt(d) * 200) * gain


def ding(f=1318.5, gain=0.4):
    a = bell_tone(f, 1.5) * gain
    b = bell_tone(f * 1.5, 1.2) * gain * 0.4
    a[: len(b)] += b
    return a


def chime_sparkle(gain=0.35):
    out = np.zeros(int(1.4 * SR))
    for i, m in enumerate((84, 88, 91, 96)):
        b = bell_tone(midi(m), 1.0) * (0.9 ** i)
        j = int(i * 0.06 * SR)
        out[j:j + len(b)] += b[: len(out) - j]
    return out * gain


def buzzer(gain=0.35):
    d = 0.7
    t = tt(d)
    x = signal.sawtooth(2 * np.pi * 110 * t) + signal.sawtooth(2 * np.pi * 116 * t)
    return lp(x, 1800) * env_adsr(len(t), 0.01, 0.05, 0.9, 0.08) * gain


def error_beep(gain=0.3):
    out = np.zeros(int(0.7 * SR))
    for k, f in enumerate((660, 440)):
        t = tt(0.22)
        b = signal.square(2 * np.pi * f * t) * env_adsr(len(t), 0.005, 0.02, 0.8, 0.03)
        j = int(k * 0.28 * SR)
        out[j:j + len(b)] += lp(b, 3000)
    return out * gain


def engine_cough(gain=0.6):
    d = 0.75
    t = tt(d)
    puffs = np.zeros_like(t)
    for k in range(4):
        c = 0.06 + k * 0.13
        puffs += np.exp(-((t - c) ** 2) / 0.0012) * (1 - k * 0.15)
    rumble = lp(noise(d), 300) * 2 + 0.6 * signal.sawtooth(2 * np.pi * 38 * t)
    bang = lp(noise(d), 1200) * np.exp(-((t - 0.5) ** 2) / 0.0004) * 1.5
    return lp(rumble * puffs + bang, 2500) * gain


def engine_hum(dur, f=45, gain=0.15, fade=0.5):
    t = tt(dur)
    x = signal.sawtooth(2 * np.pi * f * t * (1 + 0.01 * np.sin(2 * np.pi * 3 * t))) + lp(noise(dur), 200) * 1.5
    x = lp(x, 400)
    e = np.minimum(1, np.minimum(t / fade, (dur - t) / fade))
    return x * e * gain


def engine_die(gain=0.5):
    d = 1.6
    t = tt(d)
    f = 50 * np.exp(-t * 1.4) + 8
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) + lp(noise(d), 200)
    return lp(x, 500) * np.exp(-t * 1.8) * gain


def tape_rewind(dur=2.3, gain=0.35):
    t = tt(dur)
    f = 900 + 1800 * np.abs(np.sin(2 * np.pi * 1.3 * t))
    chirp = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3
    hiss = bp(noise(dur), 2000, 9000) * 0.8
    flutter = 0.6 + 0.4 * np.sin(2 * np.pi * 22 * t)
    e = np.minimum(1, np.minimum(t / 0.1, (dur - t) / 0.15))
    return (chirp + hiss) * flutter * e * gain


def tape_stop(gain=0.4):
    d = 0.8
    t = tt(d)
    f = 220 * np.exp(-t * 4)
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) + signal.sawtooth(2 * np.pi * np.cumsum(f * 1.5) / SR)
    return lp(x, 1500) * np.exp(-t * 2) * gain


def shutter(gain=0.5):
    out = np.zeros(int(0.25 * SR))
    for k in (0.0, 0.08):
        c = click(1.0)
        j = int(k * SR)
        out[j:j + len(c)] += c
    out += lp(noise(0.25), 1500) * np.exp(-tt(0.25) * 30) * 0.3
    return out * gain


def gulp(gain=0.5):
    d = 0.25
    t = tt(d)
    f = 180 + 500 * np.exp(-t * 18)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)
    return lp(x + 0.2 * lp(noise(d), 800) * np.exp(-t * 20), 2000) * gain


def crunch(gain=0.5):
    d = 0.35
    out = np.zeros(int(d * SR))
    for k in range(9):
        c = bp(noise(0.03), 1500, 7000) * np.exp(-tt(0.03) * 120)
        j = int(rng.uniform(0, d - 0.04) * SR)
        out[j:j + len(c)] += c * rng.uniform(0.4, 1)
    return out * gain


def squish(gain=0.4):
    d = 0.4
    t = tt(d)
    f = 300 + 250 * np.sin(np.pi * t / d)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * bp(noise(d), 300, 1500)
    return lp(x, 1500) * np.sin(np.pi * t / d) * gain


def tick(gain=0.25):
    return marimba(2000, 0.06) * gain


def hit(gain=0.6):
    d = 1.2
    t = tt(d)
    x = kick(d, 90, 35) * 1.2 + lp(noise(d), 600) * np.exp(-t * 6) * 0.6
    return x * gain


def riser(dur=2.0, gain=0.3):
    t = tt(dur)
    f = 200 * 2 ** (t / dur * 2.5)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4 + whoosh(dur, True, 0.6)[: len(t)]
    return x * (t / dur) ** 2 * gain


def bulb_buzz(dur, gain=0.12):
    t = tt(dur)
    x = signal.sawtooth(2 * np.pi * 120 * t) * (0.6 + 0.4 * (np.sin(2 * np.pi * 7 * t) > 0))
    e = np.minimum(1, np.minimum(t / 0.2, (dur - t) / 0.3))
    return lp(x, 2500) * e * gain


def thermo_rise(dur=4.0, gain=0.12):
    t = tt(dur)
    f = 300 + 600 * t / dur
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t))
    e = np.minimum(1, np.minimum(t / 0.3, (dur - t) / 0.4))
    return x * e * gain


def siren_chirp(gain=0.2):
    d = 0.9
    t = tt(d)
    f = 700 + 500 * np.sin(np.pi * t / d * 2) ** 2
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return x * env_adsr(len(t), 0.02, 0.05, 1, 0.2) * gain


def drop_plink(gain=0.25):
    d = 0.25
    t = tt(d)
    f = 900 + 900 * (1 - np.exp(-t * 25))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18) * gain


def wind(dur, gain=0.08, seed=0):
    r = np.random.default_rng(seed)
    n = r.standard_normal(int(dur * SR))
    x = lp(n, 500) + 0.3 * bp(n, 800, 2000)
    t = tt(dur)
    mod = 0.55 + 0.45 * np.sin(2 * np.pi * 0.07 * t + 1) * np.sin(2 * np.pi * 0.023 * t)
    return x * mod * gain


def crickets(dur, gain=0.05):
    t = tt(dur)
    chirp = np.sin(2 * np.pi * 4300 * t) * (np.sin(2 * np.pi * 30 * t) > 0.3)
    gate = (np.sin(2 * np.pi * 1.6 * t) > 0.55).astype(float)
    gate = lp(gate, 40)
    chirp2 = np.sin(2 * np.pi * 3900 * t) * (np.sin(2 * np.pi * 26 * t) > 0.3) * lp(
        (np.sin(2 * np.pi * 1.1 * t + 2) > 0.6).astype(float), 40)
    return (chirp * gate + 0.7 * chirp2) * gain


def car_drive(dur, gain=0.12):
    return engine_hum(dur, 52, 1.0, fade=0.6) * gain + lp(noise(dur), 900) * 0.04 * gain / 0.12


# ------------------------------------------------------------------ music
CHORDS = {
    "Am": ["A2", "C3", "E3", "A3", "C4", "E4"], "F": ["F2", "A2", "C3", "F3", "A3", "C4"],
    "C": ["C3", "E3", "G3", "C4", "E4", "G4"], "G": ["G2", "B2", "D3", "G3", "B3", "D4"],
    "Dm": ["D3", "F3", "A3", "D4", "F4", "A4"], "Em": ["E3", "G3", "B3", "E4", "G4", "B4"],
    "D": ["D3", "F#3", "A3", "D4", "F#4", "A4"], "A": ["A2", "C#3", "E3", "A3", "C#4", "E4"],
    "Bm": ["B2", "D3", "F#3", "B3", "D4", "F#4"], "Bb": ["A#2", "D3", "F3", "A#3", "D4", "F4"],
    "Cm": ["C3", "D#3", "G3", "C4", "D#4", "G4"], "Ab": ["G#2", "C3", "D#3", "G#3", "C4", "D#4"],
    "Eb": ["D#3", "G3", "A#3", "D#4", "G4", "A#4"], "Gm": ["G2", "A#2", "D3", "G3", "A#3", "D4"],
}


def fz(names):
    return [midi(nm(n)) for n in names]


def cue_tense(tr, a, b, intensity=1.0, heart=None, bpm=60):
    """Low drone + pulse, A minor. Used for the survival scenes."""
    prog = ["Am", "F", "Am", "Dm"]
    bar = 4 * 60 / bpm
    i = 0
    t = a
    while t < b:
        ch = prog[i % len(prog)]
        d = min(bar * 2, b - t) + 1.5
        tr.add(pad(fz(CHORDS[ch][:4]), d, 1.8, 1.8, 0.35), t, 0.55 * intensity)
        root = midi(nm(CHORDS[ch][0]) - 12)
        for k in range(8):
            bt = t + k * bar / 4
            if bt < b:
                tr.add(lp(bass(root, 0.5, 0.02, 0.3), 300), bt, 0.35 * intensity * (1.0 if k % 2 == 0 else 0.6))
        if i % 2 == 1:
            m = nm(CHORDS[ch][-1]) + 12
            tr.add(bell_tone(midi(m), 2.5), t + bar * 0.5, 0.12 * intensity, pan=0.4)
        t += bar * 2
        i += 1
    if heart:
        h0, h1 = heart
        x = h0
        while x < h1:
            tr.add(heartbeat(), x, 0.5)
            x += 0.85


def cue_roadtrip(tr, a, b, key_shift=0, bpm=112, gain=1.0):
    prog = ["C", "G", "Am", "F"]
    beat = 60 / bpm
    bar = beat * 4
    t, i = a, 0
    while t < b - 0.05:
        ch = prog[i % 4]
        notes = [nm(n) + key_shift for n in CHORDS[ch]]
        pattern = [0, 2, 3, 4, 5, 4, 3, 2]
        for k, idx in enumerate(pattern):
            nt = t + k * beat / 2
            if nt < b:
                tr.add(pluck(midi(notes[idx] + 12), 0.9, 0.7), nt, 0.22 * gain, pan=0.25 if k % 2 else -0.25)
        for k in range(4):
            bt = t + k * beat
            if bt >= b:
                continue
            if k in (0, 2):
                tr.add(kick(), bt, 0.35 * gain)
                tr.add(bass(midi(notes[0] - 12), beat * 0.9), bt, 0.35 * gain)
            else:
                tr.add(clap(), bt, 0.35 * gain)
                tr.add(bass(midi(notes[0] - 12 + 7), beat * 0.6), bt + beat / 2, 0.2 * gain)
            tr.add(shaker(), bt + beat / 2, 0.5 * gain, pan=0.5)
            tr.add(hat(), bt, 0.4 * gain, pan=-0.4)
        t += bar
        i += 1


def cue_curious(tr, a, b, bpm=96, gain=1.0):
    prog = ["F", "Dm", "Bb", "C"]
    beat = 60 / bpm
    bar = beat * 4
    t, i = a, 0
    motif = [0, None, 2, 3, None, 2, 4, None]
    while t < b - 0.05:
        ch = prog[i % 4]
        notes = [nm(n) for n in CHORDS[ch]]
        for k, idx in enumerate(motif):
            nt = t + k * beat / 2
            if idx is not None and nt < b:
                tr.add(marimba(midi(notes[idx] + 12)), nt, 0.3 * gain, pan=-0.2)
        tr.add(pad(fz(CHORDS[ch][1:4]), min(bar, b - t) + 1.0, 0.6, 1.0, 0.2), t, 0.25 * gain)
        for k in range(4):
            bt = t + k * beat
            if bt < b:
                tr.add(bass(midi(notes[0] - 12), beat * 0.7), bt, 0.25 * gain if k % 2 == 0 else 0.15 * gain)
                tr.add(tick(), bt + beat / 2, 0.6 * gain, pan=0.4)
        t += bar
        i += 1


def cue_night(tr, a, b):
    prog = ["Dm", "Bb", "F", "C"]
    bar = 4.0
    t, i = a, 0
    while t < b:
        ch = prog[i % 4]
        tr.add(pad(fz(CHORDS[ch][:4]), min(bar, b - t) + 2.0, 2.0, 2.0, 0.2), t, 0.45)
        for k, idx in enumerate((3, 5, 4)):
            nt = t + 0.5 + k * 1.2
            if nt < b:
                tr.add(bell_tone(midi(nm(CHORDS[ch][idx]) + 12), 2.0), nt, 0.12, pan=-0.3 + 0.3 * k)
        t += bar
        i += 1


def cue_warm(tr, a, b, bpm=84):
    prog = ["G", "D", "Em", "C"]
    beat = 60 / bpm
    bar = beat * 4
    t, i = a, 0
    while t < b - 0.05:
        ch = prog[i % 4]
        notes = [nm(n) for n in CHORDS[ch]]
        for k, idx in enumerate([0, 3, 4, 5, 3, 4]):
            nt = t + k * bar / 6
            if nt < b:
                tr.add(pluck(midi(notes[idx] + 12), 1.4, 0.6, 2.2), nt, 0.22, pan=-0.3 + 0.12 * k)
        tr.add(pad(fz(CHORDS[ch][:4]), min(bar, b - t) + 1.5, 1.0, 1.5, 0.3), t, 0.28)
        tr.add(bass(midi(notes[0] - 12), bar * 0.9, 0.05, 0.5), t, 0.3)
        t += bar
        i += 1


def cue_tension(tr, a, b, bpm=100, gain=1.0):
    """C minor ostinato that builds toward the decision."""
    prog = ["Cm", "Ab", "Eb", "Bb"]
    beat = 60 / bpm
    bar = beat * 4
    t, i = a, 0
    while t < b - 0.05:
        grow = (t - a) / max(1, b - a)
        ch = prog[i % 4]
        notes = [nm(n) for n in CHORDS[ch]]
        for k in range(8):
            nt = t + k * beat / 2
            if nt < b:
                tr.add(lp(bass(midi(notes[0] - 12), beat * 0.45, 0.005, 0.08), 600 + 1500 * grow), nt,
                       (0.25 + 0.2 * grow) * gain)
        tr.add(pad(fz(CHORDS[ch][1:5]), min(bar, b - t) + 1.0, 0.8, 1.0, 0.5 + grow), t, (0.25 + 0.25 * grow) * gain)
        if i % 2 == 0:
            tr.add(hit(0.4), t, (0.4 + 0.4 * grow) * gain)
        t += bar
        i += 1


def cue_hope(tr, a, b, bpm=76, build=0.0):
    prog = ["D", "A", "Bm", "G"]
    beat = 60 / bpm
    bar = beat * 4
    t, i = a, 0
    while t < b - 0.05:
        g = build + (1 - build) * (t - a) / max(1, b - a)
        ch = prog[i % 4]
        notes = [nm(n) for n in CHORDS[ch]]
        tr.add(pad(fz(CHORDS[ch][:5]), min(bar, b - t) + 2.0, 1.5, 2.0, 0.4 + 0.4 * g, vib=1.0), t, 0.35 + 0.15 * g)
        if g > 0.3:
            for k, idx in enumerate([0, 2, 4, 5, 4, 2, 3, 4]):
                nt = t + k * beat / 2
                if nt < b:
                    tr.add(pluck(midi(notes[idx] + 12), 1.0, 0.6), nt, 0.16 * g, pan=-0.3 if k % 2 else 0.3)
        tr.add(bass(midi(notes[0] - 12), bar * 0.95, 0.1, 0.5), t, 0.3 * g + 0.1)
        if g > 0.6:
            for k in range(4):
                tr.add(kick(0.3, 90, 40), t + k * beat, 0.22 * g if k % 2 == 0 else 0.0)
        t += bar
        i += 1


def final_chord(tr, at, names, gain=0.5, dur=4.0):
    tr.add(pad(fz(names), dur, 0.05, dur * 0.8, 0.6), at, gain)
    for k, n in enumerate(names):
        tr.add(pluck(midi(nm(n) + 12), 2.5, 0.7, 1.5), at + k * 0.03, 0.18)


def fade_region(x, a, b, fade=0.6):
    """Multiply stereo buffer x by a gain that is 0 in [a, b] with soft edges."""
    n = len(x)
    t = np.arange(n) / SR
    g = np.ones(n)
    g = np.where((t > a) & (t < b), 0.0, g)
    ramp_in = (t > a - fade) & (t <= a)
    g[ramp_in] = (a - t[ramp_in]) / fade
    ramp_out = (t >= b) & (t < b + fade)
    g[ramp_out] = (t[ramp_out] - b) / fade
    return x * g[:, None]


# ------------------------------------------------------------------ score
def build_music(dur):
    m = Track(dur)
    cue_tense(m, 0.0, 22.6, 0.9, heart=(7.8, 14.4))
    cue_roadtrip(m, 25.0, 37.6)
    cue_curious(m, 37.6, 52.8)
    cue_roadtrip(m, 52.8, 53.9, gain=0.9)
    cue_tense(m, 57.6, 92.5, 0.8)
    cue_night(m, 92.5, 123.7)
    cue_tense(m, 123.7, 146.1, 1.0, bpm=72)
    cue_tension(m, 146.1, 155.1, bpm=92, gain=0.8)
    cue_warm(m, 155.1, 182.0)
    cue_tension(m, 182.0, 218.6, bpm=100)
    final_chord(m, 218.7, ["D3", "F#3", "A3", "D4"], 0.45, 3.0)
    cue_hope(m, 220.5, 239.9, build=0.0)
    cue_hope(m, 239.9, 258.9, build=0.6)
    cue_curious(m, 258.9, 297.2, bpm=100, gain=0.9)
    cue_roadtrip(m, 297.2, 309.4, key_shift=5, bpm=118)
    final_chord(m, 309.4, ["F3", "A3", "C4", "F4"], 0.5, 3.5)
    x = m.stereo(int(dur * SR))
    # hard music gaps: rewind gap and the engine "silence"
    x = fade_region(x, 22.6, 25.0, 0.3)
    x = fade_region(x, 54.0, 57.6, 0.35)
    x = fade_region(x, 218.5, 218.6, 0.2) if False else x
    return x


SFX_EVENTS = []


def sfx(at, fn, gain=1.0, pan=0.0):
    SFX_EVENTS.append((at, fn, gain, pan))


def build_sfx(dur, cuts):
    s = Track(dur)
    # transitions
    for ct in cuts:
        s.add(whoosh(0.5, True, 0.25), ct - 0.3, 1.0, pan=0.0)
    # --- cold open
    sfx(0.0, lambda: hit(0.9))
    sfx(2.8, lambda: pop(500, 0.4))
    sfx(12.3, lambda: chime_sparkle(0.25), pan=-0.3)
    sfx(15.0, lambda: pop(700, 0.45))
    sfx(16.4, lambda: buzzer(0.18))
    sfx(18.1, lambda: whoosh(0.8, True, 0.35))
    sfx(19.4, lambda: chime_sparkle(0.3))
    # --- rewind
    sfx(22.6, lambda: tape_rewind(2.3, 0.35))
    sfx(23.0, lambda: pop(600, 0.35))
    # --- flashback
    sfx(30.3, lambda: pop(500, 0.4), pan=0.5)
    for k in range(5):
        sfx(30.8 + k * 0.95, lambda: drop_plink(0.12), pan=0.5)
    sfx(33.2, lambda: pop(800, 0.35), pan=-0.5)
    sfx(34.0, lambda: pop(650, 0.35), pan=-0.4)
    # --- daily loss infographic
    for k in range(3):
        sfx(38.0 + k * 0.25, lambda k=k: pop(600 + 120 * k, 0.35))
    sfx(39.2, lambda: whoosh(1.8, False, 0.2))
    sfx(41.2, lambda: pop(500, 0.45))
    sfx(41.8, lambda: buzzer(0.15))
    # --- the question
    sfx(44.1, lambda: hit(0.6))
    sfx(47.7, lambda: pop(700, 0.4))
    for k in range(6):
        sfx(48.6 + k * 0.7, lambda: drop_plink(0.15), pan=-0.5 + 0.2 * k)
    sfx(48.5, lambda: pop(600, 0.35))
    sfx(50.6, lambda: pop(450, 0.4))
    # --- hour 1: engine dies
    sfx(53.6, lambda: tape_stop(0.3))
    sfx(53.6, lambda: engine_cough(0.6), pan=0.3)
    sfx(54.3, lambda: engine_cough(0.55), pan=0.3)
    sfx(54.6, lambda: engine_die(0.45), pan=0.3)
    sfx(57.0, lambda: click(0.5), pan=0.3)
    sfx(57.6, lambda: whoosh(0.4, True, 0.25))
    sfx(58.2, lambda: error_beep(0.25))
    sfx(61.2, lambda: pop(650, 0.3))
    # --- hour 4 / body water
    sfx(70.4, lambda: riser(1.2, 0.18))
    sfx(71.0, lambda: pop(500, 0.45))
    sfx(73.4, lambda: pop(400, 0.45))
    for k in range(6):
        sfx(73.6 + k * 0.35, lambda: drop_plink(0.14), pan=-0.4 + 0.15 * k)
    # --- hour 8 / thirst
    sfx(79.4, lambda: buzzer(0.12))
    sfx(79.4, lambda: ding(1760, 0.2))
    sfx(80.5, lambda: pop(800, 0.35))
    sfx(82.2, lambda: hit(0.5))
    sfx(82.2, lambda: buzzer(0.3))
    sfx(83.6, lambda: riser(3.5, 0.12))
    sfx(85.9, lambda: pop(700, 0.4))
    sfx(88.7, lambda: pop(500, 0.35))
    sfx(90.9, lambda: hit(0.45))
    # --- night / kidneys
    sfx(96.0, lambda: pop(400, 0.4))
    for k in range(14):
        sfx(96.6 + k * 0.2, lambda: tick(0.4))
    sfx(99.7, lambda: pop(600, 0.4))
    sfx(101.5, lambda: ding(1318.5, 0.25))
    for k in range(8):
        sfx(102.8 + k * 1.25, lambda: squish(0.18))
    sfx(106.9, lambda: pop(550, 0.35))
    for k in range(4):
        sfx(107.2 + k * 1.6, lambda: drop_plink(0.12))
    sfx(110.9, lambda: hit(0.6))
    # --- crackers
    sfx(113.5, lambda: crunch(0.45), pan=0.2)
    sfx(114.6, lambda: pop(600, 0.3))
    sfx(116.0, lambda: pop(450, 0.4))
    sfx(116.8, lambda: pop(650, 0.35))
    sfx(119.0, lambda: pop(500, 0.35))
    sfx(119.6, lambda: buzzer(0.12))
    sfx(122.0, lambda: crunch(0.5))
    # --- sunrise
    sfx(123.7, lambda: riser(2.0, 0.15))
    sfx(126.0, lambda: thermo_rise(4.5, 0.08), pan=0.6)
    for k in range(6):
        sfx(127.9 + k * 0.45, lambda: drop_plink(0.1), pan=-0.2)
    sfx(130.5, lambda: pop(500, 0.4))
    # --- brain
    sfx(132.7, lambda: hit(0.5))
    sfx(134.8, lambda: pop(500, 0.4))
    sfx(135.4, lambda: whoosh(0.4, False, 0.25))
    sfx(136.9, lambda: pop(700, 0.4))
    sfx(138.9, lambda: pop(600, 0.4))
    sfx(140.5, lambda: pop(500, 0.35))
    sfx(140.7, lambda: whoosh(0.5, False, 0.2))
    sfx(141.8, lambda: pop(450, 0.35))
    sfx(142.0, lambda: whoosh(0.5, False, 0.2))
    sfx(143.8, lambda: riser(1.5, 0.15))
    sfx(146.1, lambda: hit(0.55))
    sfx(146.3, lambda: crunch(0.4))
    sfx(152.0, lambda: bulb_buzz(3.0, 0.08))
    sfx(152.3, lambda: ding(587.3, 0.2))
    # --- mirror play
    for k in range(3):
        sfx(155.3 + k * 0.4, lambda k=k: pop(300 + 60 * k, 0.25), pan=0.5)
    sfx(157.0, lambda: chime_sparkle(0.25), pan=0.4)
    sfx(159.2, lambda: shutter(0.45), pan=0.4)
    sfx(160.2, lambda: whoosh(0.3, True, 0.15))
    sfx(162.9, lambda: pop(650, 0.3))
    sfx(165.3, lambda: chime_sparkle(0.35))
    sfx(165.3, lambda: riser(0.6, 0.15))
    # --- your turn / grandma
    sfx(173.2, lambda: pop(700, 0.35))
    sfx(175.3, lambda: pop(550, 0.35))
    sfx(176.7, lambda: chime_sparkle(0.2))
    sfx(177.6, lambda: pop(600, 0.35))
    # --- walk idea
    sfx(184.7, lambda: bulb_buzz(3.9, 0.08))
    sfx(187.3, lambda: hit(0.45))
    sfx(188.6, lambda: whoosh(0.6, True, 0.3))
    for k in range(8):
        sfx(191.4 + k * 0.5, lambda: kick(0.12, 200, 90, 0.12), pan=-0.3 + 0.08 * k)
    sfx(192.0, lambda: pop(500, 0.4))
    sfx(196.2, lambda: pop(700, 0.35))
    sfx(199.1, lambda: buzzer(0.12))
    sfx(200.6, lambda: hit(0.5))
    sfx(201.7, lambda: pop(500, 0.35))
    x = 207.1
    while x < 210.6:
        sfx(x, lambda: heartbeat(0.55))
        x += 0.75
    sfx(210.6, lambda: pop(600, 0.35))
    # --- choice
    sfx(211.9, lambda: whoosh(0.6, True, 0.35))
    sfx(213.2, lambda: pop(450, 0.4), pan=-0.5)
    sfx(214.8, lambda: pop(650, 0.4), pan=0.5)
    sfx(218.7, lambda: ding(1318.5, 0.35), pan=0.4)
    # --- shade / signal
    sfx(220.0, lambda: lp(noise(1.6), 900) * np.exp(-tt(1.6) * 1.5) * 0.12, pan=-0.3)
    sfx(222.1, lambda: pop(500, 0.3))
    for k in range(3):
        sfx(224.6 + k * 0.5, lambda: drop_plink(0.15))
    sfx(227.4, lambda: chime_sparkle(0.2), pan=0.2)
    for ft in (230.9, 231.6, 232.4):
        sfx(ft, lambda: chime_sparkle(0.4), pan=0.3)
        sfx(ft, lambda: whoosh(0.3, True, 0.2), pan=0.4)
    # --- ranger
    sfx(236.0, lambda: chime_sparkle(0.3), pan=-0.6)
    sfx(236.2, lambda: pop(600, 0.3))
    sfx(239.9, lambda: engine_hum(2.8, 60, 0.2, 0.6), pan=0.6)
    sfx(240.3, lambda: siren_chirp(0.15), pan=0.6)
    sfx(241.3, lambda: siren_chirp(0.12), pan=0.4)
    sfx(242.9, lambda: pop(500, 0.3))
    for st in (244.4, 245.6, 246.8):
        sfx(st, lambda: gulp(0.35))
        sfx(st, lambda: pop(800, 0.2))
    sfx(244.2, lambda: pop(500, 0.3))
    # --- not fine
    sfx(249.0, lambda: pop(600, 0.3))
    sfx(252.5, lambda: pop(450, 0.35))
    for k in range(4):
        sfx(254.8 + k * 0.8, lambda: drop_plink(0.12))
    sfx(257.0, lambda: pop(600, 0.35))
    # --- fact check
    sfx(258.9, lambda: hit(0.45))
    sfx(260.9, lambda: pop(500, 0.35))
    for st in (262.6, 263.6, 264.6):
        sfx(st, lambda: pop(600, 0.3))
        sfx(st + 0.25, lambda: ding(1568, 0.25))
    sfx(266.8, lambda: pop(500, 0.35))
    sfx(269.6, lambda: pop(650, 0.3))
    sfx(272.8, lambda: whoosh(1.0, False, 0.3), pan=-0.5)
    sfx(275.1, lambda: whoosh(1.4, True, 0.3), pan=0.5)
    sfx(278.6, lambda: riser(2.4, 0.16))
    sfx(281.0, lambda: buzzer(0.25))
    sfx(281.0, lambda: hit(0.45))
    # --- lessons
    sfx(283.6, lambda: pop(500, 0.35))
    sfx(285.6, lambda: pop(650, 0.3))
    for st in (289.8, 292.7, 294.5):
        sfx(st, lambda: pop(550, 0.35))
        sfx(st + 0.15, lambda: ding(1318.5, 0.18))
    # --- twist / outro
    sfx(297.3, lambda: riser(1.4, 0.18))
    sfx(298.8, lambda: hit(0.45))
    for k in range(6):
        sfx(299.0 + k * 0.33, lambda: drop_plink(0.13), pan=-0.4 + 0.16 * k)
    sfx(301.1, lambda: hit(0.5))
    sfx(303.9, lambda: pop(650, 0.35))
    sfx(305.1, lambda: pop(500, 0.35))
    sfx(306.6, lambda: pop(650, 0.3))
    sfx(308.7, lambda: pop(500, 0.35))
    sfx(309.2, lambda: pop(650, 0.35))
    sfx(309.4, lambda: click(0.5))
    sfx(309.9, lambda: click(0.6))
    sfx(310.0, lambda: ding(1760, 0.35))
    sfx(310.1, lambda: ding(2637, 0.2))
    for at, fn, gain, pan in SFX_EVENTS:
        s.add(fn(), at, gain, pan)
    return s.stereo(int(dur * SR))


def edge_env(n, fade):
    t = np.arange(n) / SR
    return np.clip(np.minimum(t / fade, (n / SR - t) / fade), 0, 1)


def build_ambience(dur):
    a = Track(dur)
    desert = [(0, 22.6), (52.8, 92.5), (123.7, 155.1), (155.1, 182.0), (182.0, 188.6), (207.1, 248.9),
              (248.9, 254.1)]
    for k, (s0, s1) in enumerate(desert):
        w = wind(s1 - s0 + 1.0, 1.0, seed=k)
        e = edge_env(len(w), 0.8)
        a.add(w * e, s0, 0.10, pan=0.15 if k % 2 else -0.15)
    for s0, s1 in [(92.5, 96.0), (113.4, 116.0)]:
        cr = crickets(s1 - s0)
        e = edge_env(len(cr), 0.5)
        a.add(cr * e, s0, 0.06, pan=0.3)
        w = wind(s1 - s0, 1.0, seed=99)
        a.add(w * edge_env(len(w), 0.5), s0, 0.05)
    # car driving under the flashback and start of hour 1
    a.add(car_drive(12.6), 25.0, 1.0)
    a.add(car_drive(1.6), 52.8, 1.0)
    # rescue truck idles nearby while sipping
    a.add(engine_hum(5.0, 40, 0.06, 1.0), 243.5, 1.0, pan=0.5)
    return a.stereo(int(dur * SR))


# ------------------------------------------------------------------ mix
def load_audio(path):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def envelope(x, attack=0.02, release=0.35):
    rect = np.abs(x)
    rms = np.sqrt(lp(rect ** 2, 25, 1).clip(0))
    out = np.zeros_like(rms)
    aa = np.exp(-1 / (attack * SR))
    rr = np.exp(-1 / (release * SR))
    # vectorize via downsampled processing for speed
    step = 64
    small = rms[::step]
    env = np.zeros_like(small)
    a2, r2 = aa ** step, rr ** step
    prev = 0.0
    for i, v in enumerate(small):
        c = a2 if v > prev else r2
        prev = c * prev + (1 - c) * v
        env[i] = prev
    out = np.repeat(env, step)[: len(x)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stems")
    a = ap.parse_args()

    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from scenes import CUTS

    voice = load_audio(a.voice)
    dur = len(voice) / SR
    print("building music…", flush=True)
    music = build_music(dur)
    print("building sfx…", flush=True)
    fx = build_sfx(dur, CUTS)
    print("building ambience…", flush=True)
    amb = build_ambience(dur)

    # normalize stems to reference peaks
    def norm(x, peak):
        m = np.max(np.abs(x)) or 1.0
        return x / m * peak

    n = min(len(voice), len(music), len(fx), len(amb))
    voice, music, fx, amb = voice[:n], music[:n], fx[:n], amb[:n]
    music = norm(music, 1.0)
    # ducking: music drops when the narrator speaks
    env = envelope(voice)
    env = env / (np.percentile(env, 95) + 1e-9)
    duck = 1.0 - 0.55 * np.clip(env, 0, 1)
    duck = lp(duck, 6, 1)
    music *= (0.32 * duck)[:, None]
    fx = norm(fx, 0.55)
    amb = norm(amb, 0.22)
    vpk = np.max(np.abs(voice)) or 1.0
    v = voice / vpk * 0.92
    mix = np.stack([v, v], axis=1) + music + fx + amb
    # gentle soft clip / limiter
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    if a.stems:
        os.makedirs(a.stems, exist_ok=True)
        for name, x in (("music", music), ("sfx", fx), ("ambience", amb)):
            wavfile.write(os.path.join(a.stems, f"{name}.wav"), SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
    wavfile.write(a.out, SR, (np.clip(mix, -1, 1) * 32767).astype(np.int16))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
