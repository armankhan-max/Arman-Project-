"""Soundtrack for "The Indestructible Sword": synthesized BGM + SFX, ducked under the voiceover.

Reuses the instrument/SFX library from ../video/audio.py (everything synthesized, royalty-free).
Usage: python audio.py --voice vo.mp3 --out mix.wav --dur 40.4
"""
import argparse, os, subprocess, sys
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video"))
from audio import (SR, tt, env_adsr, lp, hp, bp, noise, midi, Track, pluck, bell_tone, pad, bass, kick, hat,
                   clap, whoosh, ding, chime_sparkle, tape_rewind, hit, riser)

rng = np.random.default_rng(5)


# ------------------------------------------------------------------ extra SFX
def metal_clang(gain=0.6, f0=820):
    d = 1.4; t = tt(d); x = np.zeros_like(t)
    for k, r in enumerate([1, 2.76, 5.4, 8.93, 13.3]):
        x += np.sin(2 * np.pi * f0 * r * t + k) * np.exp(-t * (4 + 3 * k)) / (1 + k * 0.6)
    x += hp(noise(d), 2500) * np.exp(-t * 40) * 0.8
    return x * gain


def snap(gain=0.7):
    d = 0.5; t = tt(d)
    x = hp(noise(d), 1500) * np.exp(-t * 25) + metal_clang(1, 1300)[: len(t)] * 0.6
    return x * gain


def boom(gain=1.0, dur=4.0):
    t = tt(dur)
    sub = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t * 1.5) + 28) / SR) * np.exp(-t * 1.1)
    rum = lp(noise(dur), 260) * np.exp(-t * 0.9) * 2.5
    crack = hp(noise(dur), 1200) * np.exp(-t * 12) * 0.8
    return np.tanh((sub * 1.4 + rum + crack) * 1.2) * gain


def screech(dur=1.2, gain=0.35):
    t = tt(dur); f = 2300 + 250 * np.sin(2 * np.pi * 7 * t) - 500 * t / dur
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    x = x * (0.7 + 0.3 * lp(noise(dur), 30) * 4) + bp(noise(dur), 1500, 5000) * 0.6
    return x * env_adsr(len(t), 0.02, 0.1, 0.9, 0.35) * gain


def whine(dur, gain=0.18):
    t = tt(dur); f = 180 + 520 * np.minimum(1, t / 1.2) + 15 * np.sin(2 * np.pi * 18 * t)
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.4 + np.sin(2 * np.pi * np.cumsum(f * 2) / SR)
    return lp(x, 3000) * env_adsr(len(t), 0.3, 0.1, 1, 0.3) * gain


def zap(gain=0.3, d=0.35):
    t = tt(d); x = bp(noise(d), 2000, 9000) * (rng.random(len(t)) < 0.25)
    x += np.sign(np.sin(2 * np.pi * 90 * t)) * 0.3
    return x * np.exp(-t * 9) * gain


def wood_crack(gain=0.7):
    d = 1.0; t = tt(d); x = np.zeros_like(t)
    for k in range(14):
        i = int(rng.random() * 0.35 * SR)
        L = int(0.03 * SR); x[i:i + L] += bp(noise(0.03), 600, 3500) * np.exp(-tt(0.03) * 120) * (1 - k / 16)
    x += lp(noise(d), 400) * np.exp(-t * 4) * 0.8
    return x * gain


def thud(gain=0.6):
    return kick(0.4, 140, 50) * gain + lp(noise(0.4), 900)[: int(0.4 * SR)] * np.exp(-tt(0.4) * 14) * gain * 0.6


def boing(gain=0.3):
    d = 0.6; t = tt(d); f = 220 + 120 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5) * gain


def glitch_sfx(d=0.4, gain=0.3):
    t = tt(d); x = np.zeros_like(t); seg = int(0.02 * SR)
    for i in range(0, len(t), seg):
        f = rng.choice([200, 400, 900, 1600, 3000]); x[i:i + seg] = np.sign(np.sin(2 * np.pi * f * t[i:i + seg])) * rng.random()
    return lp(x, 6000) * gain


def reverse_swell(dur=2.0, gain=0.4):
    x = bell_tone(midi(62), dur)[::-1] + bell_tone(midi(69), dur)[::-1]
    return x * gain


# ------------------------------------------------------------------ music
def groove(tr, a, b, bpm=124, gain=1.0, root=50):
    beat = 60 / bpm; t = a; i = 0
    prog = [0, 0, -2, -4]  # D, D, C, Bb
    while t < b:
        bar = int(i // 8); r = root + prog[bar % 4]
        if i % 2 == 0: tr.add(kick(0.35, 120, 45, 0.9), t, gain)
        if i % 4 == 2: tr.add(clap(0.35), t, gain * 0.9)
        tr.add(hat(0.05, 0.18), t + beat / 2, gain, pan=0.3)
        tr.add(bass(midi(r - 12), beat * 0.45), t, gain * 0.9)
        if i % 2 == 1: tr.add(pluck(midi(r + [12, 15, 19, 17][(i // 2) % 4]), 0.4, 0.8), t, gain * 0.35, pan=-0.3)
        t += beat; i += 1


def tense(tr, a, b, bpm=124, gain=1.0, rise=False):
    beat = 60 / bpm; t = a; i = 0
    tr.add(pad([midi(38), midi(45), midi(50), midi(53)], b - a + 0.5, 0.4, 0.6, 0.35), a, gain * 0.5)
    while t < b:
        k = (t - a) / max(0.01, b - a)
        if i % 2 == 0: tr.add(kick(0.4, 90, 38, 1.0), t, gain)
        tr.add(bass(midi(38 if (i // 8) % 2 == 0 else 41), beat * 0.4), t, gain * 0.8)
        step = 0.5 if (rise and k > 0.5) else 1
        tr.add(pluck(midi([62, 65, 69, 65][i % 4] + (12 if rise and k > 0.7 else 0)), 0.25, 1.2), t, gain * 0.25, pan=0.2)
        if step == 0.5: tr.add(hat(0.04, 0.2), t + beat / 2, gain)
        t += beat; i += 1


def heroic(tr, a, dur, gain=1.0):
    tr.add(pad([midi(50), midi(57), midi(62), midi(66)], dur, 0.2, 0.8, 0.6), a, gain * 0.6)
    for k, n in enumerate([74, 78, 81]):
        tr.add(bell_tone(midi(n), 2.0), a + 0.15 * k, gain * 0.5)


def eerie(tr, a, b, gain=1.0):
    d = b - a
    for f, p in [(midi(38) * 1.003, -0.4), (midi(44), 0.4), (midi(49) * 0.997, 0), (midi(56), -0.2)]:
        tr.add(pad([f], d, 0.3, 1.0, 0.4, vib=0.4), a, gain * 0.4, pan=p)
    t = a; i = 0
    while t < b:
        tr.add(bell_tone(midi([74, 73, 80, 77][i % 4]), 1.2), t, gain * 0.18, pan=(-1) ** i * 0.5)
        tr.add(kick(0.5, 70, 30, 0.9), t, gain * 0.8)
        t += 0.97; i += 1


def build(dur, voice):
    mus, sfx = Track(dur), Track(dur)
    # music cues
    groove(mus, 0.0, 6.9)
    heroic(mus, 7.35, 1.9)
    groove(mus, 9.1, 13.05, gain=0.85)
    tense(mus, 13.1, 21.9)
    heroic(mus, 24.0, 1.9, 0.9)
    tense(mus, 25.9, 30.75, bpm=132, rise=True)
    mus.add(riser(4.9, 0.5), 25.95)
    mus.add(pad([midi(26), midi(33)], 4.0, 0.2, 1.5, 0.3), 31.3, 0.7)
    eerie(mus, 35.3, 39.35)
    mus.add(reverse_swell(2.0, 0.35), 37.2)
    # sfx
    for t in [2.45, 3.85, 5.73, 9.08, 10.95, 13.1, 16.0, 17.75, 18.75, 20.4, 21.92, 25.9, 27.2, 27.85, 28.75]:
        sfx.add(whoosh(0.45, True, 0.35), t - 0.2)
    sfx.add(snap(0.9), 5.19); sfx.add(metal_clang(0.5, 1100), 5.19)
    sfx.add(whoosh(0.7, False, 0.5), 5.73)
    sfx.add(tape_rewind(0.45, 0.5), 6.93); sfx.add(tape_rewind(0.4, 0.5), 23.63)
    sfx.add(metal_clang(0.8), 8.12); sfx.add(chime_sparkle(0.4), 8.2); sfx.add(ding(1568, 0.3), 8.3)
    sfx.add(chime_sparkle(0.3), 9.65); sfx.add(clap(0.5), 10.42); sfx.add(ding(1318, 0.25), 10.45)
    sfx.add(whoosh(0.3, True, 0.4), 12.1); sfx.add(thud(0.9), 12.4); sfx.add(boing(0.4), 12.45)
    sfx.add(metal_clang(0.7, 600), 13.97); sfx.add(hit(0.6), 13.97)
    sfx.add(hit(0.8), 16.95); sfx.add(metal_clang(0.6, 650), 16.95); sfx.add(screech(1.0, 0.35), 16.9)
    sfx.add(metal_clang(0.5, 700), 18.02)
    sfx.add(whine(3.2, 0.2), 18.75); sfx.add(whine(1.0, 0.15), 27.85)
    for t in np.arange(19.3, 21.9, 0.8): sfx.add(zap(0.25), t)
    sfx.add(wood_crack(0.9), 22.6); sfx.add(hit(0.5), 22.6)
    sfx.add(chime_sparkle(0.45), 24.6); sfx.add(ding(1760, 0.3), 24.65)
    for t in np.arange(25.9, 30.8, 0.23): sfx.add(zap(0.12 + 0.2 * (t - 25.9) / 5), t, pan=rng.uniform(-0.6, 0.6))
    sfx.add(boom(1.1, 5.0), 31.27); sfx.add(boom(0.8, 4.0), 33.75); sfx.add(boom(0.6, 3.5), 34.28)
    sfx.add(glitch_sfx(0.35, 0.35), 35.15); sfx.add(glitch_sfx(0.25, 0.35), 36.55); sfx.add(glitch_sfx(0.15, 0.3), 37.06)
    sfx.add(riser(1.2, 0.5), 38.2); sfx.add(boom(0.7, 3.0), 39.35)

    n = int(dur * SR)
    M = mus.stereo(n); S = sfx.stereo(n)
    # sidechain duck music under voice
    env = np.abs(voice[:n]) if len(voice) >= n else np.pad(np.abs(voice), (0, n - len(voice)))
    k = int(0.05 * SR); env = np.convolve(env, np.ones(k) / k, mode="same")
    env = env / (env.max() + 1e-9)
    duck = 1 - 0.55 * np.clip(env * 4, 0, 1)
    duck = np.convolve(duck, np.ones(int(0.12 * SR)) / int(0.12 * SR), mode="same")
    M *= duck[:, None]
    # silence right before "unleash" for impact
    gap = np.ones(n); a, b = int(30.95 * SR), int(31.27 * SR); gap[a:b] = 0.15
    M *= gap[:, None]
    V = np.stack([voice[:n]] * 2, axis=1) if len(voice) >= n else np.pad(np.stack([voice] * 2, axis=1), ((0, n - len(voice)), (0, 0)))
    mix = V * 1.0 + M * 0.22 + S * 0.32
    fade = np.ones(n); fade[-int(0.6 * SR):] = np.linspace(1, 0, int(0.6 * SR))
    mix *= fade[:, None]
    return mix / (np.abs(mix).max() + 1e-9) * 0.95


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--voice"); ap.add_argument("--out"); ap.add_argument("--dur", type=float, default=40.4)
    a = ap.parse_args()
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.voice, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    voice = np.frombuffer(raw, np.float32).astype(np.float64)
    voice = voice / (np.abs(voice).max() + 1e-9) * 0.8
    mix = build(a.dur, voice)
    wavfile.write(a.out, SR, (mix * 32767).astype(np.int16))
    print("wrote", a.out)
