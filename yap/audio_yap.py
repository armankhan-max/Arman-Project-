"""Soundtrack for "The Island That Paid With Stones" (synthesized, royalty-free) + the voiceover.

* camera-driven air/whooshes from camtrack.json, big whooshes on every whip seam
* environment beds follow the camera: surf on the island, muffled rumble + bubbles underwater, rain/wind in the storm
* low booms only on reveals/impacts, risers into each slow-mo, foley (hammer on limestone, paddles, steps,
  thud, coconut knock, bus crash + honk, splash, sparkle on the name change, thunder)
* flat tropical music bed (marimba + plucks), ~13 dB under the voice and ducked while it speaks

Usage: python audio_yap.py --out mix.wav [--voice voiceover.mp3]
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
sys.path.insert(0, os.path.join(HERE, "..", "banks"))
from audio import SR, Track, tt, lp, hp, bp, noise, midi, pluck, marimba, pad, bass, kick, whoosh, riser, bell_tone, load_audio, envelope, edge_env  # noqa: E402
from audio_banks import boom, clink, step, creak, babble, poof  # noqa: E402

rng = np.random.default_rng(1871)
_add = Track.add
def _safe_add(self, x, at, gain=1.0, pan=0.0):
    if at * SR >= len(self.L) - 1:
        return
    return _add(self, x, at, gain, pan)
Track.add = _safe_add
TL = json.load(open(os.path.join(HERE, "timeline.json")))
DUR = TL["duration"] + 1 / TL["fps"]
SEAMS = [3.75, 7.15, 9.55, 12.85, 16.85, 24.45, 28.5, 38.55]
HITS = [13.02, 13.36, 13.74, 14.31]


def surf(dur, gain=0.2, seed=0):
    r = np.random.default_rng(seed)
    t = tt(dur)
    n = r.standard_normal(len(t))
    x = lp(n, 900) * 0.8 + bp(n, 1500, 5000) * 0.25
    mod = 0.35 + 0.65 * (0.5 + 0.5 * np.sin(2 * np.pi * t / 5.3 + 1.2)) ** 3
    return x * mod * gain


def underwater(dur, gain=0.3):
    t = tt(dur)
    x = lp(noise(dur), 220) * 2.5 + 0.3 * np.sin(2 * np.pi * 42 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * t))
    out = x * gain
    for _ in range(int(dur * 7)):           # bubbles
        i = rng.integers(0, max(1, len(t) - 4000))
        f0 = rng.uniform(500, 1500)
        tb = np.arange(3000) / SR
        out[i:i + 3000] += np.sin(2 * np.pi * np.cumsum(f0 * (1 + 4 * tb)) / SR) * np.exp(-tb * 40) * 0.05
    return out


def rain(dur, gain=0.25):
    x = hp(noise(dur), 1500) * 0.6 + bp(noise(dur), 300, 1200) * 0.5
    return x * edge_env(len(x), 0.3) * gain


def thunder(gain=0.8, dur=3.0):
    t = tt(dur)
    crack = hp(noise(dur), 2000) * np.exp(-t * 18) * 0.6
    roll = lp(noise(dur), 160) * 3 * (np.exp(-t * 1.2) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t) ** 2))
    return (crack + roll) * gain


def stone_hit(gain=0.5):
    d = 0.4
    t = tt(d)
    x = bp(noise(d), 700, 4000) * np.exp(-t * 45) + np.sin(2 * np.pi * 180 * t) * np.exp(-t * 30) * 0.6 + clink(2200, 0.25)[:len(t)]
    return x * gain


def splash(gain=0.5, dur=1.2):
    t = tt(dur)
    x = bp(noise(dur), 400, 6000) * (np.exp(-t * 5) * (1 - np.exp(-t * 60))) + lp(noise(dur), 300) * np.exp(-t * 3) * 0.8
    return x * gain


def paddle(gain=0.15):
    return splash(gain, 0.45)


def thud(gain=0.7):
    d = 0.6
    t = tt(d)
    return (kick(d, 120, 45) + lp(noise(d), 500) * np.exp(-t * 14) * 0.6) * gain


def knock(gain=0.35):
    d = 0.2
    t = tt(d)
    return (np.sin(2 * np.pi * 420 * t) * np.exp(-t * 40) + bp(noise(d), 800, 3000) * np.exp(-t * 80) * 0.4) * gain


def fall_whistle(dur, gain=0.2):
    t = tt(dur)
    f = 1800 - 1300 * t / dur
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / dur) * gain


def crash(gain=0.8):
    d = 1.4
    t = tt(d)
    metal = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t * k) for f, k in ((310, 5), (523, 6), (877, 8), (1312, 9))) * 0.25
    return (thud(1.0)[:len(t)] if len(t) <= len(thud(1.0)) else np.pad(thud(1.0), (0, len(t) - len(thud(1.0))))) * gain + (metal + bp(noise(d), 1500, 7000) * np.exp(-t * 9) * 0.5) * gain


def honk(gain=0.3):
    d = 0.5
    t = tt(d)
    x = np.sign(np.sin(2 * np.pi * 330 * t)) + np.sign(np.sin(2 * np.pi * 415 * t))
    return lp(x, 2500) * edge_env(len(t), 0.03) * gain


def sparkle(gain=0.3):
    out = np.zeros(int(1.4 * SR))
    for i, m in enumerate((84, 88, 91, 96, 100)):
        b = bell_tone(midi(m), 1.0) * (0.85 ** i)
        j = int(i * 0.06 * SR)
        out[j:j + len(b)] += b[:len(out) - j]
    return out * gain


def music_bed(dur):
    """Flat tropical bed: marimba ostinato in C major pentatonic + soft pad + bass, constant level."""
    tr = Track(dur)
    prog = [[48, 60, 64, 67], [45, 57, 60, 64], [41, 57, 60, 65], [43, 55, 59, 62]]
    bar = 2.4
    for i in range(int(np.ceil(dur / bar)) + 1):
        notes = prog[i % 4]
        at = i * bar
        tr.add(pad([midi(m) for m in notes[1:]], bar + 0.8, 0.5, 0.7, 0.3), at, 0.35)
        tr.add(bass(midi(notes[0] - 12), bar * 0.5, 0.02, 0.3), at, 0.3)
        tr.add(bass(midi(notes[0] - 5), bar * 0.45, 0.02, 0.3), at + bar * 0.5, 0.22)
        pent = [notes[1], notes[2], notes[3], notes[1] + 12, notes[3] - 5 + 12]
        for k in range(12):
            if k % 4 == 3 and i % 2:
                continue
            m = pent[(k * 2 + i) % len(pent)] + 12
            tr.add(marimba(midi(m), 0.5), at + k * bar / 12, 0.22, pan=0.25 if k % 2 else -0.25)
        for k in (2, 6, 10):
            tr.add(pluck(midi(notes[2] + 12), 0.5, 0.6, 6.0), at + k * bar / 12, 0.08, pan=0.4)
    x = tr.stereo(int(dur * SR))
    return x * edge_env(len(x), 0.05)[:, None]


def build(voice_path=None):
    n = int(DUR * SR)
    ct = np.array(json.load(open(os.path.join(HERE, "camtrack.json"))))
    fr = np.arange(len(ct)) / TL["fps"]
    under = ct[:, 8] > 0.5
    shot = ct[:, 7]
    storm = shot == 8
    env_t = np.arange(n) / SR
    m_under = lp(np.interp(env_t, fr, under.astype(float)), 8, 1)
    m_storm = lp(np.interp(env_t, fr, (storm & ~under).astype(float)), 8, 1)
    m_day = np.clip(1 - m_under - m_storm, 0, 1)

    sfx = Track(DUR)
    # beds
    bed = surf(DUR, 0.16, 1)[:n] * m_day + underwater(DUR, 0.22)[:n] * m_under + (rain(DUR, 0.22)[:n] + surf(DUR, 0.25, 2)[:n]) * m_storm
    sfx.add(bed, 0, 1.0)
    # whips + air from the camera path
    p, yaw, pit = ct[:, 1:4], np.unwrap(ct[:, 4]), ct[:, 5]
    dt = 1 / TL["fps"]
    lin = np.r_[0, np.linalg.norm(np.diff(p, axis=0), axis=1)] / dt
    ang = np.r_[0, np.hypot(np.diff(yaw), np.diff(pit))] / dt
    lin[lin > 60] = 0  # seam teleports
    ang[ang > 40] = 0
    sp = np.convolve(lin / 12 + ang / 4.0, np.ones(5) / 5, "same")
    env = np.interp(env_t, fr, np.clip(sp, 0, 2.5))
    sfx.add((bp(noise(DUR), 250, 3500)[:n] * 0.6) * env * 0.16, 0, 1.0)
    for i in range(3, len(sp) - 3):
        if sp[i] > 0.6 and sp[i] == sp[max(0, i - 20):i + 20].max():
            sfx.add(whoosh(0.55, True, 0.4 * min(1.5, sp[i])), fr[i] - 0.3, 0.8)
    for s in SEAMS:
        sfx.add(whoosh(0.7, True, 0.9), s - 0.42, 1.0, pan=0.2)
    # entering / leaving the water
    for i in range(1, len(under)):
        if under[i] != under[i - 1]:
            sfx.add(splash(0.6 if under[i] else 0.35), fr[i] - 0.05, 1.0)
    # booms + risers
    for b in [2.9, 4.95, 15.65, 21.09, 27.41, 33.1, 35.62, 45.6]:
        sfx.add(boom(0.85), b, 1.0)
    for a, b, f in TL["slowmo"]:
        sfx.add(riser(0.9, 0.28), a - 0.9, 1.0)
    # foley
    for h in HITS:
        sfx.add(stone_hit(0.6), h, 1.0, pan=0.3)
        sfx.add(stone_hit(0.35), h + 0.17, 1.0, pan=-0.3)
    t = 9.6
    while t < 12.85:
        sfx.add(paddle(0.14), t, 1.0, pan=rng.uniform(-0.4, 0.4)); t += 0.6
    t = 14.4
    while t < 16.85:
        sfx.add(paddle(0.16), t, 1.0, pan=rng.uniform(-0.4, 0.4)); t += 0.55
    for a, b, rate, g in [(16.85, 18.35, 0.42, 0.12), (21.2, 22.2, 0.34, 0.16)]:
        t = a
        while t < b:
            sfx.add(step(g), t, 1.0, pan=0.2); t += rate
    sfx.add(creak(2.0, 0.12), 18.9, 1.0)          # straining stone
    sfx.add(thud(0.8), 21.09, 1.0)
    sfx.add(creak(1.6, 0.1), 22.3, 1.0)
    sfx.add(thud(0.6), 23.95, 1.0)
    sfx.add(knock(0.4), 24.97, 1.0); sfx.add(knock(0.3), 25.12, 1.0)
    sfx.add(fall_whistle(0.46, 0.18), 26.95, 1.0)
    sfx.add(crash(0.8), 27.41, 1.0)
    sfx.add(honk(0.25), 27.75, 1.0)
    sfx.add(babble(2.8, 0.25), 28.5, 1.0)
    sfx.add(step(0.25), 29.33, 1.0)             # handshake pat
    sfx.add(sparkle(0.35), 33.1, 1.0)
    for th in [34.62, 36.25, 37.6]:
        sfx.add(thunder(0.7 if th < 36 else 0.45), th, 1.0)
    sfx.add(creak(1.0, 0.2), 35.0, 1.0, pan=0.4)
    sfx.add(splash(0.9, 1.6), 35.62, 1.0)
    sfx.add(babble(2.0, 0.18), 38.6, 1.0, pan=-0.2)
    for k in range(6):
        sfx.add(clink(rng.uniform(1800, 2600), 0.05), 42.72 + k * 0.12, 1.0)   # chalk-ish tally ticks

    music = music_bed(DUR)
    voice = np.zeros((n, 2))
    duck = np.ones(n)
    if voice_path:
        v = load_audio(voice_path)[:n]
        v = v / (np.sqrt(np.mean(v[np.abs(v) > 1e-3] ** 2)) + 1e-9) * 0.1
        vp = np.zeros(n); vp[:len(v)] = v
        voice[:, 0] = vp; voice[:, 1] = vp
        duck = 1 - 0.45 * np.clip(envelope(vp) / 0.05, 0, 1)
    mr = np.sqrt(np.mean(music ** 2)) + 1e-9
    music = music / mr * 10 ** (-33 / 20) * duck[:, None]
    mix = voice + music + sfx.stereo(n) * 0.8
    f = int(0.02 * SR)
    mix[:f] *= np.linspace(0, 1, f)[:, None]
    mix[-int(0.5 * SR):] *= np.linspace(1, 0, int(0.5 * SR))[:, None]
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
