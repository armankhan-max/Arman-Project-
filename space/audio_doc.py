"""Soundtrack for the space documentary.

Brief: voice-over loud and clear; background music very low and minimal (soft ambient pads only);
no fancy sound effects -- just a barely-there air swell on topic changes.

Usage: python audio_doc.py --voice voice.mp3 --out final_mix.wav
"""
import argparse
import os
import re
import subprocess
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
rng = np.random.default_rng(11)

MUSIC_DB_UNDER_VOICE = 21.0   # music level below the voice (minimal)
DUCK_DB = 4.0                 # extra dip while the narrator talks
SWELL_DB_UNDER_VOICE = 26.0   # topic-change air swells (very soft)


def load(path, filt=None):
    cmd = ["ffmpeg", "-v", "error", "-i", path]
    if filt:
        cmd += ["-af", filt]
    cmd += ["-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).astype(np.float64)


def lp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def bp(x, f1, f2, order=2):
    b, a = signal.butter(order, [f1 / (SR / 2), f2 / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# soft, slow chord cycle (A minor colour, spacious voicings)
CHORDS = [
    [45, 52, 57, 60, 64],   # Am(add9-ish)
    [41, 48, 53, 57, 64],   # Fmaj7
    [48, 55, 60, 64, 67],   # C
    [43, 50, 55, 59, 62],   # G
    [45, 52, 57, 59, 64],   # Asus2
    [38, 45, 50, 57, 60],   # Dm9
    [41, 48, 53, 60, 64],   # F
    [40, 47, 52, 55, 59],   # Em
]


def pad_layer(dur, chord_len=12.0, xfade=4.0):
    n = int(dur * SR)
    L, R = np.zeros(n), np.zeros(n)
    t_all = np.arange(n) / SR
    k = 0
    start = 0.0
    while start < dur:
        notes = CHORDS[k % len(CHORDS)]
        seg = chord_len + xfade
        a, b = int(start * SR), min(n, int((start + seg) * SR))
        t = t_all[a:b] - start
        env = np.minimum(1, t / xfade) * np.minimum(1, np.maximum(0, (seg - t) / xfade))
        env = np.sin(env * np.pi / 2) ** 2
        for j, m in enumerate(notes):
            f = midi(m)
            amp = 1.0 / (1 + 0.35 * j)
            for side, det in ((0, -0.0025), (1, 0.0025)):
                ph = rng.uniform(0, 6.28)
                lfo = 1 + 0.0015 * np.sin(2 * np.pi * (0.11 + 0.03 * j) * t + ph)
                x = np.sin(2 * np.pi * f * (1 + det) * lfo * t + ph) + 0.18 * np.sin(4 * np.pi * f * (1 + det) * t + ph)
                breathe = 0.75 + 0.25 * np.sin(2 * np.pi * 0.05 * t + j + ph)
                (L if side == 0 else R)[a:b] += x * amp * env * breathe
        start += chord_len
        k += 1
    # gentle low sub drone on A
    sub = 0.35 * np.sin(2 * np.pi * midi(33) * t_all) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.03 * t_all))
    L += sub
    R += sub
    # faint high shimmer (filtered noise), very soft
    sh = bp(rng.standard_normal(n), 5000, 9000) * 0.04 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.02 * t_all))
    L += sh
    R += np.roll(sh, 800)
    L, R = lp(L, 2400), lp(R, 2400)
    return np.stack([L, R], 1)


def swell(d=1.4):
    t = np.arange(int(d * SR)) / SR
    x = lp(rng.standard_normal(len(t)), 1800) - lp(rng.standard_normal(len(t)), 200) * 0.3
    env = np.sin(np.pi * t / d) ** 3
    return x * env


def voice_env(v, hop=441):
    """0..1 'narrator is talking' envelope (fast attack, slow release)."""
    fr = np.sqrt(np.convolve(v ** 2, np.ones(hop) / hop, "same")[::hop])
    thr = 0.25 * np.percentile(fr, 90)
    g = (fr > thr).astype(float)
    y = np.zeros_like(g)
    s = 0.0
    for i, x in enumerate(g):
        s += (x - s) * (0.5 if x > s else 0.04)
        y[i] = s
    return np.interp(np.arange(len(v)), np.arange(len(y)) * hop, y)


def rms(x):
    return float(np.sqrt(np.mean(x ** 2)) + 1e-12)


def scene_starts():
    src = open(os.path.join(HERE, "doc_scenes.py")).read()
    block = src[src.index("SCENES = ["):src.index("INNER_CUTS")]
    return sorted({float(m) for m in re.findall(r"\(\s*([0-9]+\.[0-9]+),", block)} - {0.0})


def integrated_lufs(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", out)[-1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--target", type=float, default=-13.0)
    a = ap.parse_args()

    # 1) voice: clean low rumble, gentle compression so every word is loud and even
    v = load(a.voice, "highpass=f=70,acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=3,"
                      "equalizer=f=3000:t=q:w=1.2:g=2")
    n = len(v) + int(1.0 * SR)
    v = np.concatenate([v, np.zeros(n - len(v))])
    dur = n / SR
    env = voice_env(v)
    v_rms = rms(v[env > 0.5]) if np.any(env > 0.5) else rms(v)

    # 2) music: minimal ambient pad, far under the voice, ducked further while speaking
    mus = pad_layer(dur)
    mus *= (v_rms * 10 ** (-MUSIC_DB_UNDER_VOICE / 20)) / rms(mus)
    duck = 10 ** (-DUCK_DB * env / 20)
    mus *= duck[:, None]
    fade = np.minimum(1, np.arange(n) / (3 * SR)) * np.minimum(1, (n - np.arange(n)) / (4 * SR))
    mus *= fade[:, None]

    # 3) the only "SFX": a barely-audible air swell at each topic change
    sfx = np.zeros(n)
    sw = swell()
    sw *= (v_rms * 10 ** (-SWELL_DB_UNDER_VOICE / 20)) / rms(sw[len(sw) // 4: 3 * len(sw) // 4])
    for st in scene_starts():
        i = int((st - 0.7) * SR)
        if 0 <= i < n - len(sw):
            sfx[i:i + len(sw)] += sw

    mix = np.stack([v, v], 1) + mus + np.stack([sfx, sfx], 1)
    tmp = os.path.splitext(a.out)[0] + "_pre.wav"
    wavfile.write(tmp, SR, (mix / max(1e-9, np.abs(mix).max()) * 0.5).astype(np.float32))
    cur = integrated_lufs(tmp)
    gain = a.target - cur
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af",
                    f"volume={gain:.2f}dB,alimiter=limit=0.89:attack=3:release=60:level=disabled",
                    "-ar", str(SR), "-c:a", "pcm_s16le", a.out], check=True)
    os.remove(tmp)
    print(f"voice-relative: music -{MUSIC_DB_UNDER_VOICE} dB (+{DUCK_DB} dB duck), swells -{SWELL_DB_UNDER_VOICE} dB; "
          f"pre {cur:.1f} LUFS -> target {a.target} LUFS; final {integrated_lufs(a.out):.1f} LUFS")


if __name__ == "__main__":
    main()
