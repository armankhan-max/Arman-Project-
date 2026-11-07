"""Soundtrack for "Is This Still Worth It?": the voice stays front and centre.

Deliberately restrained (as requested): no cartoon sound effects. Just
  * a soft, original music bed (warm pads + a gentle plucked pattern) that changes chords with the
    chapters and ducks under the narrator,
  * one quiet "air" swoosh on each of the 12 numbered title cards so the viewer feels the chapter turn,
  * loudness normalised afterwards to -14 LUFS with ffmpeg.

Usage: python audio_wi.py --voice voice.mp3 --out mix.wav
"""
import argparse
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from audio import SR, Track, lp, hp, midi, nm, pad, pluck, whoosh  # noqa: E402
from scipy.io import wavfile  # noqa: E402

from scenes_a import CARD_START  # noqa: E402
from scenes_wi import to_new  # noqa: E402

PROG_A = [["A2", "E3", "A3", "C4", "E4"], ["F2", "C3", "F3", "A3", "C4"],
          ["C3", "G3", "C4", "E4"], ["G2", "D3", "G3", "B3", "D4"]]      # Am F C G: curious, steady
PROG_B = [["D3", "A3", "D4", "F4"], ["A#2", "F3", "A#3", "D4"], ["F2", "C3", "F3", "A3"], ["C3", "G3", "C4", "E4"]]
PROG_END = [["F2", "C3", "F3", "A3", "C4"], ["C3", "G3", "C4", "E4"], ["G2", "D3", "G3", "B3", "D4"],
            ["A2", "E3", "A3", "C4", "E4"]]


def fz(names):
    return [midi(nm(n)) for n in names]


def bed(tr, a, b, prog, bpm=84, gain=1.0, pluck_gain=0.22):
    beat = 60.0 / bpm
    bar = beat * 4
    t = a
    i = 0
    while t < b:
        ch = prog[i % len(prog)]
        d = min(bar * 2, b - t)
        tr.add(pad(fz(ch), d + 1.2, 0.8, 1.2, 0.35), t, 0.22 * gain)
        # gentle 8th-note pluck pattern on the upper chord tones
        notes = fz(ch[1:])
        for k in range(int(d / (beat / 2))):
            f = notes[(k * 2 + (k // 4)) % len(notes)] * 2
            tr.add(pluck(f, 0.9, 0.55, 4.0), t + k * beat / 2, pluck_gain * gain * (1.0 if k % 2 == 0 else 0.6),
                   pan=0.25 if k % 2 else -0.25)
        t += bar * 2
        i += 1


def fade_region(x, a, b, floor=0.0, ramp=0.4):
    n = len(x)
    tt = np.arange(n) / SR
    g = np.ones(n)
    inside = (tt > a) & (tt < b)
    g[inside] = floor
    for s, e, up in ((a - ramp, a, False), (b, b + ramp, True)):
        m = (tt >= s) & (tt <= e)
        r = (tt[m] - s) / ramp
        g[m] = floor + (1 - floor) * (r if up else 1 - r)
    return x * g[:, None]


def build_music(dur):
    m = Track(dur)
    T = to_new
    bed(m, 0.0, T(30.0), PROG_A, gain=0.8)
    bed(m, T(30.0), T(163.1), PROG_A, gain=1.0)
    bed(m, T(163.1), T(279.8), PROG_B, gain=1.0)
    bed(m, T(279.8), T(369.8), PROG_A, gain=1.0)
    bed(m, T(369.8), dur + 2, PROG_END, bpm=76, gain=0.9)
    x = m.stereo(int(dur * SR))
    x = fade_region(x, T(395.8), T(401.9), floor=0.35, ramp=0.8)   # quieter under the disclaimer
    tt = np.arange(len(x)) / SR
    x *= np.clip((dur - tt) / 2.5, 0, 1)[:, None]          # fade out at the very end
    return x


def build_fx(dur):
    s = Track(dur)
    for st in CARD_START.values():
        s.add(lp(whoosh(0.7, True, 1.0), 2500), to_new(st) - 0.25, 0.18)
    return s.stereo(int(dur * SR))


def load_audio(path):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le",
                                   "-"])
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def envelope(v, win=0.25):
    k = int(win * SR)
    cs = np.concatenate([[0.0], np.cumsum(v ** 2)])
    m = (cs[k:] - cs[:-k]) / k
    m = np.concatenate([np.full(k // 2, m[0]), m, np.full(len(v) - len(m) - k // 2, m[-1])])
    return np.sqrt(np.maximum(m, 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    voice = load_audio(a.voice)
    dur = len(voice) / SR
    music = build_music(dur)
    fx = build_fx(dur)
    n = min(len(voice), len(music), len(fx))
    voice, music, fx = voice[:n], music[:n], fx[:n]
    music = music / (np.max(np.abs(music)) or 1.0)
    env = envelope(voice)
    env = env / (np.percentile(env, 95) + 1e-9)
    duck = lp(1.0 - 0.55 * np.clip(env * 1.5, 0, 1), 4, 1)
    music = hp(music, 90) * (0.16 * duck)[:, None]    # low bed, well under the voice
    fx = fx / (np.max(np.abs(fx)) or 1.0) * 0.12
    v = voice / (np.max(np.abs(voice)) or 1.0) * 0.92
    mix = np.stack([v, v], axis=1) + music + fx
    mix = np.clip(mix, -1, 1)
    wavfile.write(a.out, SR, (mix * 32767).astype(np.int16))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
