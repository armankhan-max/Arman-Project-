"""Soundtrack for "Why Perfect Banks Didn't Work" (synthesized, royalty-free).

* whooshes are driven by the real camera path (camtrack.json): every camera move gets air, peaks get a whoosh
* low booms only on reveals/impacts, risers into every slow-mo, foley (coins, footsteps, vault door, crowd)
* flat music bed ~13 dB under the voice; voice placeholder track is silent unless --voice is given

Usage: python audio_banks.py --out mix.wav [--voice voiceover.wav] [--sfx-dir DIR]
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from audio import SR, Track, tt, lp, hp, bp, noise, midi, pluck, pad, bass, kick, whoosh, riser, bell_tone, load_audio, envelope, edge_env  # noqa: E402

rng = np.random.default_rng(1609)
TL = json.load(open(os.path.join(HERE, "timeline.json")))
DUR = TL["duration"] + 1 / TL["fps"]
AUD_N = None


def boom(gain=0.9, dur=2.2):
    t = tt(dur)
    f = 32 + 48 * np.exp(-t * 4)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.9)
    return lp(x + 0.35 * lp(noise(dur), 140) * np.exp(-t * 3), 220) * gain


def clink(f=None, gain=0.3):
    f = f or rng.uniform(2600, 4200)
    d = 0.5
    t = tt(d)
    x = sum(a * np.sin(2 * np.pi * f * k * t + rng.uniform(0, 6)) * np.exp(-t * (9 + 6 * k)) for k, a in ((1, 1), (1.53, .6), (2.41, .4), (3.7, .25)))
    return (x + 0.3 * hp(noise(d), 5000) * np.exp(-t * 120)) * gain


def coin_flip_ting(gain=0.5):
    d = 1.6
    t = tt(d)
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * dk) * a for f, dk, a in ((3150, 2.5, 1), (4890, 4, .5), (7100, 7, .3)))
    return x * (1 + 0.6 * np.sin(2 * np.pi * 9 * t)) * gain


def step(gain=0.25):
    d = 0.14
    t = tt(d)
    return (lp(noise(d), 900) * np.exp(-t * 45) + 0.5 * np.sin(2 * np.pi * 80 * t) * np.exp(-t * 40)) * gain


def creak(dur, gain=0.25):
    t = tt(dur)
    f = 95 + 40 * np.sin(2 * np.pi * 0.7 * t) + 20 * np.sin(2 * np.pi * 3.1 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sign(np.sin(ph)) * (0.5 + 0.5 * np.sin(2 * np.pi * 23 * t) ** 2)
    return bp(x, 150, 1800) * edge_env(len(t), 0.15) * gain


def clunk(gain=0.6):
    d = 0.5
    t = tt(d)
    return (kick(d, 160, 60) * 0.8 + bp(noise(d), 300, 3000) * np.exp(-t * 60) * 0.6 + clink(1800, 0.25)[:len(t)]) * gain


def shh(gain=0.3):
    d = 0.9
    t = tt(d)
    return bp(noise(d), 2500, 7000) * np.sin(np.pi * t / d) ** 0.7 * gain


def babble(dur, gain=0.2):
    t = tt(dur)
    x = np.zeros_like(t)
    for k in range(10):
        f0 = rng.uniform(110, 240)
        syl = (np.sin(2 * np.pi * rng.uniform(3, 6) * t + rng.uniform(0, 6)) > 0.2).astype(float)
        syl = lp(syl, 18)
        v = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.08 * np.sin(2 * np.pi * 2.3 * t + k))) / SR)
        x += bp(np.sign(v) * 0.5 + v, 300, 2500) * syl
    return x / 10 * edge_env(len(t), 0.3) * gain


def crumble(dur, gain=0.25):
    t = tt(dur)
    n = np.zeros_like(t)
    for _ in range(int(dur * 90)):
        i = rng.integers(0, len(t) - 2000)
        n[i:i + 2000] += clink(rng.uniform(3000, 9000), rng.uniform(0.02, 0.08))[:2000] * np.exp(-np.arange(2000) / 300)
    return (n + 0.5 * bp(noise(dur), 3000, 9000) * 0.15) * edge_env(len(t), 0.2) * gain


def poof(gain=0.3):
    d = 0.6
    t = tt(d)
    return lp(noise(d), 1500) * np.exp(-t * 7) * (1 - np.exp(-t * 80)) * gain


def music_bed(dur):
    """Flat baroque-ish bed: D-minor drone + slow harpsichord ostinato, constant level."""
    tr = Track(dur)
    prog = [("D", [50, 57, 62, 65]), ("Bb", [46, 53, 58, 62]), ("F", [41, 53, 57, 60]), ("A", [45, 52, 57, 61])]
    bar = 2.5
    n = int(np.ceil(dur / bar)) + 1
    for i in range(n):
        name, notes = prog[i % 4]
        at = i * bar
        tr.add(pad([midi(m) for m in notes[1:]], bar + 1.0, 0.6, 0.8, 0.4), at, 0.55)
        tr.add(bass(midi(notes[0] - 12), bar, 0.05, 0.6), at, 0.35)
        arp = notes[1:] + [notes[2] + 12]
        for k in range(8):
            m = arp[k % len(arp)] + 12
            tr.add(pluck(midi(m), 0.6, 0.8, 5.0), at + k * bar / 8, 0.16, pan=0.3 if k % 2 else -0.3)
    x = tr.stereo(int(dur * SR))
    return x * edge_env(len(x), 0.05)[:, None]


def camera_air(dur):
    """Air/whoosh layer following camera speed + discrete whooshes on speed peaks."""
    tr = Track(dur)
    ct = np.array(json.load(open(os.path.join(HERE, "camtrack.json"))))
    t, p, yaw, pit = ct[:, 0], ct[:, 1:4], np.unwrap(ct[:, 4]), ct[:, 5]
    fr = np.arange(len(ct)) / TL["fps"]
    dt = 1 / TL["fps"]
    lin = np.r_[0, np.linalg.norm(np.diff(p, axis=0), axis=1)] / dt
    ang = np.r_[0, np.hypot(np.diff(yaw), np.diff(pit))] / dt
    sp = lin / 12 + ang / 4.0
    sp = np.convolve(sp, np.ones(5) / 5, "same")
    # continuous air
    n = int(dur * SR)
    env = np.interp(np.arange(n) / SR, fr, np.clip(sp, 0, 2.5))
    base = bp(noise(dur), 250, 3500)[:n]
    bright = hp(noise(dur), 3000)[:n]
    air = (base * 0.6 + bright * 0.25 * np.clip(env - 0.5, 0, 2)) * env * 0.18
    tr.add(air, 0, 1.0)
    # discrete whooshes on local speed peaks
    peaks = []
    for i in range(3, len(sp) - 3):
        if sp[i] > 0.55 and sp[i] == sp[max(0, i - 20):i + 20].max():
            peaks.append(i)
    for i in peaks:
        d = 0.55 if sp[i] < 1.5 else 0.8
        tr.add(whoosh(d, True, 0.5 * min(1.6, sp[i])), fr[i] - d * 0.55, 0.9, pan=float(np.clip(np.sin(yaw[i]) * 0.4, -0.5, 0.5)))
    return tr.stereo(n), [round(fr[i], 2) for i in peaks]


def build(voice_path=None):
    n = int(DUR * SR)
    sfx = Track(DUR)
    fo = TL["foley"]
    for b in TL["booms"]:
        sfx.add(boom(0.9 if b not in (5.3,) else 0.45), b, 1.0)
    for r in TL["risers"]:
        sfx.add(riser(1.0, 0.3), r - 1.0, 1.0)
    for a in fo["door_unlock"]:
        sfx.add(clunk(0.5), a, 1.0, pan=-0.2)
    a, b = fo["door_open"]
    sfx.add(creak(b - a, 0.22), a, 1.0, pan=-0.3)
    a, b = fo["door_close"]
    sfx.add(creak(b - a, 0.2), a, 1.0, pan=-0.3)
    sfx.add(clunk(0.9), b, 1.0)
    sfx.add(coin_flip_ting(0.35), fo["coin_flip"], 1.0, pan=0.2)
    sfx.add(clink(3400, 0.5), fo["coin_catch"], 1.0)
    for c in fo["coin_clinks"]:
        for k in range(3):
            sfx.add(clink(gain=0.18), c + k * rng.uniform(0.05, 0.12), 1.0, pan=rng.uniform(-0.6, 0.6))
    for a, b, people in fo["walk"]:
        rate = 0.36 if people < 5 else 0.18
        for k in range(people):
            t = a + rng.uniform(0, rate)
            while t < b:
                sfx.add(step(0.22 if people < 5 else 0.14), t, 1.0, pan=rng.uniform(-0.5, 0.5))
                t += rate * rng.uniform(0.9, 1.1)
    a, b = fo["bag_jingle"]
    t = a
    while t < b:
        sfx.add(clink(gain=0.07), t, 1.0, pan=rng.uniform(-0.3, 0.3))
        t += rng.uniform(0.15, 0.35)
    sfx.add(shh(0.35), fo["shh"], 1.0)
    a, b = fo["ship"]
    sfx.add(creak(b - a, 0.25), a, 1.0, pan=0.6)
    gl = bp(noise(b - a + 1), 200, 900) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * tt(b - a + 1)) ** 8)
    sfx.add(gl * edge_env(len(gl), 0.4) * 0.25, a, 1.0, pan=0.6)
    a, b = fo["cheer"]
    sfx.add(babble(b - a, 0.22), a, 1.0, pan=-0.2)
    a, b = fo["crowd"]
    sfx.add(babble(b - a, 0.5), a, 1.0)
    a, b = fo["dust"]
    sfx.add(crumble(b - a + 0.6, 0.6), a, 1.0)
    a, b = fo["poof"]
    for k in range(8):
        sfx.add(poof(0.25), a + k * 0.07, 1.0, pan=(k - 3.5) / 5)
    # room tone: low vault rumble
    rt = lp(noise(DUR), 120) * 0.035
    sfx.add(rt, 0, 1.0)
    air, peaks = camera_air(DUR)
    print("camera whooshes at:", peaks)

    music = music_bed(DUR)
    voice = np.zeros((n, 2))
    vref = 0.1
    if voice_path:
        v = load_audio(voice_path)[:n]
        v = v / (np.sqrt(np.mean(v[np.abs(v) > 1e-3] ** 2)) + 1e-9) * vref   # ~ -20 dBFS RMS while speaking
        vp = np.zeros(n); vp[:len(v)] = v
        voice[:, 0] = vp; voice[:, 1] = vp
        duck = 1 - 0.45 * np.clip(envelope(vp) / 0.05, 0, 1)
    else:
        duck = np.ones(n)
    # bed level: voice placeholder reference -20 dBFS RMS -> bed ~ -33 dBFS RMS (13 dB under)
    mr = np.sqrt(np.mean(music ** 2)) + 1e-9
    music = music / mr * 10 ** (-33 / 20)
    music = music * duck[:, None]
    mix = voice + music + (sfx.stereo(n) + air * 0.9) * 0.8
    # loop: tiny fades so the seam is click-free
    f = int(0.02 * SR)
    mix[:f] *= np.linspace(0, 1, f)[:, None]
    mix[-f:] *= np.linspace(1, 0, f)[:, None]
    peak = np.abs(mix).max()
    if peak > 0.95:
        mix *= 0.95 / peak
    return mix


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice")
    a = ap.parse_args()
    m = build(a.voice)
    wavfile.write(a.out, SR, (m * 32767).astype(np.int16))
    print("wrote", a.out, m.shape[0] / SR, "s")
