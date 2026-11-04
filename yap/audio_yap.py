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


def soft_pad(freqs, dur, bright=0.35):
    t = tt(dur)
    x = np.zeros_like(t)
    for f in freqs:
        for det in (-0.003, 0.0, 0.003):
            ph = rng.uniform(0, 6.28)
            x += np.sin(2 * np.pi * f * (1 + det) * t + ph) + bright * 0.4 * np.sin(2 * np.pi * 2 * f * (1 + det) * t + ph)
    x = lp(x / (len(freqs) * 3), 1800)
    return x * (0.75 + 0.25 * np.sin(2 * np.pi * 0.09 * t + rng.uniform(0, 6)))


def music_bed(dur):
    """Soft cinematic ambient bed: slow evolving pads, low drone, sparse felt-piano notes; mood follows the narration."""
    tr = Track(dur)
    # (start, end, chords, piano notes per bar, brightness)
    sections = [
        (0.0, 9.5, [[57, 64, 69, 72], [53, 60, 65, 69], [55, 62, 67, 71]], 2, 0.4),      # wonder: island + sea floor
        (9.5, 16.9, [[57, 64, 69, 76], [60, 67, 72, 76], [55, 62, 67, 74]], 3, 0.55),    # journey: voyage + quarry
        (16.9, 28.5, [[53, 60, 65, 72], [55, 62, 67, 74], [57, 64, 69, 76]], 3, 0.5),    # light / playful
        (28.5, 34.5, [[50, 57, 62, 65], [53, 60, 65, 69]], 2, 0.35),                     # calm agreement
        (34.5, 38.6, [[45, 52, 57, 60], [44, 51, 56, 60]], 0, 0.2),                      # storm: dark, low
        (38.6, 46.1, [[50, 57, 62, 65], [46, 53, 58, 62], [48, 55, 60, 64], [45, 52, 57, 64]], 1, 0.3),  # reflective ending
    ]
    bar = 3.2
    for s0, s1, chords, notes, br in sections:
        t = s0; k = 0
        while t < s1:
            d = min(bar, s1 - t)
            ch = chords[k % len(chords)]
            p = soft_pad([midi(m) for m in ch], d + 1.6, br)
            tr.add(p * edge_env(len(p), 0.9), t, 0.5)
            dr = np.sin(2 * np.pi * midi(ch[0] - 12) * tt(d + 1.6)) * 0.5 + 0.2 * lp(noise(d + 1.6), 90)
            tr.add(dr * edge_env(len(dr), 1.0), t, 0.32)
            for j in range(notes):
                m = ch[(j * 2 + k) % len(ch)] + 12
                pn = bell_tone(midi(m), 2.6) * 0.8 + pluck(midi(m), 2.6, 0.3, 1.8) * 0.5
                tr.add(lp(pn, 3500), t + j * bar / max(1, notes) + 0.2, 0.18, pan=0.3 if j % 2 else -0.3)
            t += bar; k += 1
    # gentle swell into the ending, low rumble under the storm
    sw = lp(noise(4.0), 140) * np.sin(np.pi * np.arange(int(4.0 * SR)) / (4.0 * SR))
    tr.add(sw, 34.5, 0.25)
    x = tr.stereo(int(dur * SR))
    return x * edge_env(len(x), 0.6)[:, None]


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
    music = music / mr * 10 ** (-35 / 20) * duck[:, None]
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
