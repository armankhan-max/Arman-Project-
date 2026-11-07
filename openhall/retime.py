"""Tighten the voiceover: shorten unusually long pauses and gently adjust pace in a few spots.

Writes the edited voice (wav) and timemap.json. The renderer reads the map so every animation stays
locked to the word it belongs to.

Usage: python retime.py voice.mp3 voice_tight.wav
"""
import json
import os
import subprocess
import sys

import numpy as np
from scipy.io import wavfile

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
KEEP_PAUSE = 0.42        # a natural breath between sentences
MIN_GAP = 0.55           # only pauses longer than this are shortened
# (start, end, tempo) in original seconds: >1 = faster, <1 = slower. Subtle, pitch preserved.
PACE = [
    (24.54, 26.9, 0.94),     # "12 things that fail that test in 2027" - let it land
    (325.20, 327.40, 0.93),  # "Now, the one I promised..."
    (387.54, 392.90, 0.95),  # "the real skill is not earning more... it is noticing"
    (394.80, 395.70, 0.90),  # "is this still worth it?"
    (395.82, 401.00, 1.12),  # disclaimer: brisk
]


def decode(path):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le",
                                   "-"])
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def silences(x, thr_db=-30, min_len=MIN_GAP):
    hop = int(0.01 * SR)
    n = len(x) // hop
    rms = np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    quiet = 20 * np.log10(rms / (np.max(np.abs(x)) + 1e-9)) < thr_db
    out, i = [], 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            a, b = i * 0.01, j * 0.01
            if b - a >= min_len and a > 0.3:
                out.append((a, b))
            i = j
        else:
            i += 1
    return out


def atempo(chunk, rate):
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", f"atempo={rate}", "-f", "f32le", "-"], input=chunk.astype(np.float32).tobytes(),
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32).astype(np.float64)


def main():
    x = decode(sys.argv[1])
    dur = len(x) / SR
    cuts = []
    for a, b in silences(x):
        L = b - a
        if L > MIN_GAP:
            keep = min(L, KEEP_PAUSE)
            mid = (a + b) / 2
            cuts.append((mid - (L - keep) / 2, mid + (L - keep) / 2))
    # build segments of original time: (a, b, rate); cut regions are dropped
    bounds = sorted({0.0, dur} | {p for c in cuts for p in c} | {p for s, e, _ in PACE for p in (s, e)})
    segs = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        m = (a + b) / 2
        if any(c0 <= m <= c1 for c0, c1 in cuts):
            continue
        rate = next((r for s, e, r in PACE if s <= m <= e), 1.0)
        segs.append((a, b, rate))
    out, tmap, tn = [], [], 0.0
    fade = int(0.008 * SR)
    for a, b, rate in segs:
        ch = x[int(a * SR):int(b * SR)].copy()
        if rate != 1.0 and len(ch) > SR * 0.1:
            ch = atempo(ch, rate)
        if len(ch) > 2 * fade:
            ch[:fade] *= np.linspace(0, 1, fade)
            ch[-fade:] *= np.linspace(1, 0, fade)
        nl = len(ch) / SR
        tmap.append([round(tn, 4), round(a, 4), round(b, 4), round(nl, 4)])
        out.append(ch)
        tn += nl
    y = np.concatenate(out)
    wavfile.write(sys.argv[2], SR, (np.clip(y, -1, 1) * 32767).astype(np.int16))
    json.dump(dict(segments=tmap, new_duration=tn, old_duration=dur), open(os.path.join(HERE, "timemap.json"), "w"))
    print(f"{len(cuts)} pauses shortened, {dur:.1f}s -> {tn:.1f}s")


if __name__ == "__main__":
    main()
