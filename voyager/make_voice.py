"""Scratch voiceover + word timings for the Voyager script.

Synthesizes each script line with espeak-ng and measures word timings by
synthesizing growing prefixes of the line (end of word k = trimmed length of
the audio for words 1..k). Writes voice.wav and transcript.json in the same
format as the other projects ({start, end, text, words:[{w, s, e}]}).

Replace voice.wav with a real voiceover later: re-time transcript.json
(e.g. with Whisper word timestamps) and rebuild; everything downstream
reads only transcript.json.

Usage: python make_voice.py [--speed 165] [--gap 0.35]
"""
import argparse
import json
import os
import re
import subprocess
import tempfile

import numpy as np
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 22050
VOICE = "en-us+m3"


def synth(text, speed, pitch=42):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
    subprocess.run(["espeak-ng", "-v", VOICE, "-s", str(speed), "-p", str(pitch),
                    "-g", "2", "-w", path, text], check=True)
    sr, a = wavfile.read(path)
    os.unlink(path)
    assert sr == SR, sr
    return a.astype(np.float32) / 32768.0


def trim(a, thr=0.01):
    idx = np.nonzero(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a[:0], 0
    return a[idx[0]: idx[-1] + 1], idx[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--speed", type=int, default=165)
    ap.add_argument("--gap", type=float, default=0.35)
    args = ap.parse_args()

    lines = [l.strip() for l in open(os.path.join(HERE, "script.txt")) if l.strip()]
    out, t, segs = [], 0.25, []
    out.append(np.zeros(int(0.25 * SR), np.float32))
    for line in lines:
        spoken = line.strip(".").replace("...", "")
        words = line.replace("...", "").split()
        full, _ = trim(synth(spoken, args.speed))
        total = len(full) / SR
        # word end times from prefix synthesis, kept monotonic and inside the line
        ends = []
        for k in range(1, len(words) + 1):
            pre = " ".join(words[:k]).rstrip(",.")
            p, _ = trim(synth(pre, args.speed))
            ends.append(min(len(p) / SR, total))
        ends[-1] = total
        for k in range(1, len(ends)):
            ends[k] = max(ends[k], ends[k - 1] + 0.08)
        scale = total / ends[-1]
        ends = [e * scale for e in ends]
        starts = [0.0] + ends[:-1]
        wl = [{"w": " " + w, "s": round(t + s, 3), "e": round(t + e, 3)}
              for w, s, e in zip(words, starts, ends)]
        segs.append({"start": round(t, 3), "end": round(t + total, 3),
                     "text": line.replace("...", ""), "words": wl})
        out.append(full)
        out.append(np.zeros(int(args.gap * SR), np.float32))
        t += total + args.gap
    audio = np.concatenate(out + [np.zeros(int(0.8 * SR), np.float32)])
    audio = audio / max(1e-6, np.abs(audio).max()) * 0.89
    wavfile.write(os.path.join(HERE, "voice.wav"), SR, (audio * 32767).astype(np.int16))
    json.dump(segs, open(os.path.join(HERE, "transcript.json"), "w"), indent=1)
    print(f"{len(segs)} lines, {len(audio) / SR:.2f}s total")


if __name__ == "__main__":
    main()
