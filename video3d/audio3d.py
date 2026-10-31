"""Soundtrack for the 3D phone-germs short: quirky low-volume music + timed SFX, mixed under the voice.

Reuses the synth instruments from ../video/audio.py, so everything is synthesized (royalty-free).
Usage: python audio3d.py --voice voice_energetic.wav --offset 0.25 --dur 19.0 --out mix.wav
"""
import argparse
import os
import sys

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video"))
import audio as A  # noqa: E402
from audio import SR, Track, bp, hp, lp, noise, tt, midi, nm  # noqa: E402

rng = np.random.default_rng(7)
CUTS = [2.6, 4.867, 6.6, 7.767, 9.0, 9.867, 11.567, 13.3, 15.4]


# ------------------------------------------------------------------ extra SFX
def spray(dur=0.32, gain=0.5):
    t = tt(dur)
    x = bp(noise(dur), 2500, 11000) * np.minimum(1, t / 0.01) * np.exp(-t * 6)
    return x * gain


def scrub(dur=1.1, rate=7.0, gain=0.4):
    t = tt(dur)
    x = bp(noise(dur), 900, 5000)
    e = (0.5 + 0.5 * np.sin(2 * np.pi * rate * t)) ** 2 * np.sin(np.pi * t / dur)
    return x * e * gain


def squelch(f=180, gain=0.35):
    d = 0.22
    t = tt(d)
    ff = f * (1 + 1.2 * np.sin(np.pi * t / d)) * (1 + 0.2 * np.sin(2 * np.pi * 30 * t))
    x = np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.sin(np.pi * t / d) ** 2
    x += 0.3 * lp(noise(d), 800) * np.sin(np.pi * t / d)
    return x * gain


def blip(f=900, gain=0.3):
    """Cartoon germ 'bloop' when a germ appears."""
    d = 0.1
    t = tt(d)
    ff = f * (0.6 + 0.8 * t / d)
    return np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-t * 25) * gain


def tap(gain=0.6):
    d = 0.06
    t = tt(d)
    x = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 120) + bp(noise(d), 1500, 6000) * np.exp(-t * 150)
    return x * gain


def ripple(gain=0.3):
    d = 0.5
    t = tt(d)
    ff = 500 + 900 * t / d
    return np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-t * 7) * (1 + 0.5 * np.sin(2 * np.pi * 18 * t)) * gain


def latch(gain=0.6):
    d = 0.25
    t = tt(d)
    a = bp(noise(d), 1500, 7000) * np.exp(-t * 90)
    b = np.sin(2 * np.pi * 220 * t) * np.exp(-t * 30) * 0.6
    out = np.zeros(int(0.35 * SR))
    out[: len(a)] += a + b
    i = int(0.09 * SR)
    out[i:i + len(a)] += (a * 0.8 + b * 0.5)
    return out * gain


def rustle(dur=0.4, gain=0.4):
    t = tt(dur)
    x = bp(noise(dur), 1500, 9000)
    e = np.abs(lp(rng.standard_normal(len(t)), 25, 1)) * 8 * np.sin(np.pi * t / dur)
    return x * np.clip(e, 0, 1.5) * gain


def swish(dur=1.2, gain=0.4):
    t = tt(dur)
    x = bp(noise(dur), 400, 3000)
    e = np.sin(np.pi * t / dur) ** 1.5 * (0.7 + 0.3 * np.sin(2 * np.pi * 3 * t))
    return x * e * gain


def thump(gain=0.6):
    return lp(A.kick(0.3, 90, 45), 300) * gain


# ------------------------------------------------------------------ music
CH = {"Am": ["A2", "C4", "E4", "A4"], "F": ["F2", "A3", "C4", "F4"], "C": ["C3", "E4", "G4", "C5"],
      "G": ["G2", "B3", "D4", "G4"], "E": ["E2", "G#3", "B3", "E4"]}


def music(dur, bpm=112):
    tr = Track(dur)
    beat = 60 / bpm
    bar = beat * 4
    prog = ["Am", "F", "C", "G", "Am", "F", "E", "E"]
    motif = [0, 2, 3, 2, None, 3, 1, 2]  # eighth notes over the chord tones
    t, i = 0.0, 0
    while t < dur:
        ch = CH[prog[i % len(prog)]]
        notes = [nm(n) for n in ch]
        for k, idx in enumerate(motif):
            nt = t + k * beat / 2
            if idx is not None:
                tr.add(A.pluck(midi(notes[idx] + 12), 0.4, 0.6, 9.0), nt, 0.22, pan=-0.25)
                if k % 4 == 0:
                    tr.add(A.marimba(midi(notes[(idx + 1) % 4] + 12)), nt, 0.12, pan=0.3)
        for k in range(4):
            bt = t + k * beat
            tr.add(A.bass(midi(notes[0]), beat * 0.45, r=0.05), bt, 0.32 if k % 2 == 0 else 0.22)
            tr.add(A.bass(midi(notes[0] + 12), beat * 0.25, r=0.05), bt + beat / 2, 0.12)
            if k % 2 == 0:
                tr.add(A.kick(0.3, 100, 45), bt, 0.45)
            else:
                tr.add(A.clap(), bt, 0.28)
            tr.add(A.hat(), bt + beat / 2, 0.35, pan=0.4)
            tr.add(A.shaker(), bt + beat * 0.75, 0.25, pan=-0.4)
        tr.add(A.pad([midi(x) for x in notes[1:]], bar + 0.6, 0.3, 0.5, 0.3), t, 0.18)
        t += bar
        i += 1
    n = int(dur * SR)
    x = tr.stereo(n)
    fade_out = np.ones(n)
    k = int(1.2 * SR)
    fade_out[-k:] = np.linspace(1, 0, k) ** 2
    fade_in = np.minimum(1, np.arange(n) / (0.15 * SR))
    return x * (fade_in * fade_out)[:, None]


# ------------------------------------------------------------------ SFX timeline (absolute seconds)
def sfx_track(dur):
    s = Track(dur)
    add = s.add
    add(A.riser(0.6, 0.25), 0.0)
    add(thump(0.5), 0.02)
    for ct in CUTS:
        add(A.whoosh(0.45, True, 0.3), ct - 0.28)
    # s01 phone vs toilet: wriggling germs
    for k, t0 in enumerate(np.arange(0.35, 2.5, 0.27)):
        add(squelch(150 + 40 * (k % 4), 0.18), t0, pan=rng.uniform(-0.5, 0.5))
    add(A.buzzer(0.12), 1.95)
    # s02 toilet cleaned
    add(spray(), 2.6 + 8 / 30)
    add(spray(), 2.6 + 15 / 30)
    add(scrub(1.1, 7, 0.35), 2.6 + 28 / 30)
    for f in range(30, 60, 4):
        add(A.pop(900 + 40 * f % 300, 0.15), 2.6 + f / 30)
    add(A.chime_sparkle(0.3), 2.6 + 50 / 30)
    # s03 phone never cleaned: creepier squelches
    for k, t0 in enumerate(np.arange(4.95, 6.5, 0.22)):
        add(squelch(110 + 30 * (k % 3), 0.2), t0, pan=rng.uniform(-0.6, 0.6))
    add(A.bass(midi(40), 0.8), 5.6, 0.25)
    # s04 door handle
    add(thump(0.35), 6.6 + 12 / 30)
    add(latch(0.55), 6.6 + 20 / 30)
    for i in range(7):
        add(blip(700 + 80 * i, 0.22), 6.6 + (14 + 2 * i) / 30, pan=0.2)
    # s05 bill
    add(rustle(0.45, 0.45), 7.767 + 14 / 30)
    for i in range(6):
        add(blip(650 + 90 * i, 0.22), 7.767 + (18 + 2 * i) / 30, pan=-0.2)
    # s06 snack
    add(A.crunch(0.5), 9.0 + 11 / 30)
    add(A.crunch(0.25), 9.0 + 15 / 30)
    for i in range(6):
        add(blip(800 + 70 * i, 0.2), 9.0 + (12 + 2 * i) / 30)
    # s07 fingers: cascade of germs
    for i in range(32):
        add(blip(500 + 25 * i, 0.16), 9.867 + (2 + int(i * 1.1)) / 30, pan=rng.uniform(-0.6, 0.6))
    add(A.riser(1.4, 0.15), 9.95)
    # s08 tap screen
    for f in (14, 31):
        t0 = 11.567 + f / 30
        add(tap(0.6), t0)
        add(ripple(0.25), t0 + 0.01)
        for k in range(6):
            add(blip(900 + 60 * k, 0.15), t0 + (1 + k) / 30)
    # s09 phone to face
    add(A.whoosh(0.6, False, 0.3), 13.35)
    add(squelch(120, 0.35), 13.3 + 24 / 30)
    add(thump(0.3), 13.3 + 25 / 30)
    for k in range(16):
        add(blip(600 + 40 * k, 0.15), 13.3 + (26 + k) / 30, pan=0.3)
    add(A.whoosh(0.5, True, 0.25), 13.3 + 42 / 30)
    # s10 wipe clean
    add(swish(1.3, 0.45), 15.4 + 12 / 30)
    for f in range(18, 52, 2):
        add(A.pop(1100 + (f * 37) % 400, 0.12), 15.4 + f / 30)
    add(A.chime_sparkle(0.4), 15.4 + 66 / 30)
    add(A.ding(1568, 0.25), 15.4 + 70 / 30)
    add(A.chime_sparkle(0.25), 15.4 + 88 / 30)
    n = int(dur * SR)
    return s.stereo(n)


def load(path):
    import subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--offset", type=float, default=0.25)
    ap.add_argument("--dur", type=float, default=19.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stems")
    a = ap.parse_args()
    n = int(a.dur * SR)
    v = np.zeros(n)
    vv = load(a.voice)
    i = int(a.offset * SR)
    v[i:i + len(vv)] = vv[: n - i]
    m = music(a.dur)
    fx = sfx_track(a.dur)
    m = m / (np.max(np.abs(m)) + 1e-9)
    fx = fx / (np.max(np.abs(fx)) + 1e-9)
    # duck the music under the voice
    env = np.abs(v)
    env = lp(env, 8, 1)
    env = env / (np.percentile(env, 95) + 1e-9)
    duck = lp(1.0 - 0.5 * np.clip(env, 0, 1), 4, 1)
    m *= (0.13 * duck)[:, None]      # background music: low volume
    fx *= 0.42
    vk = v / (np.max(np.abs(v)) + 1e-9) * 0.9
    mix = np.stack([vk, vk], axis=1) + m + fx
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)
    if a.stems:
        os.makedirs(a.stems, exist_ok=True)
        for name, x in (("music", m), ("sfx", fx)):
            wavfile.write(os.path.join(a.stems, name + ".wav"), SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
    wavfile.write(a.out, SR, (np.clip(mix, -1, 1) * 32767).astype(np.int16))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
