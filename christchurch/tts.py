"""Narration: Kokoro TTS (am_michael), one clip per sentence, assembled with documentary pacing.
Writes voice.wav + timeline.json (paragraph/sentence/word-estimate timings)."""
import json, re, sys, os
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOICE, SPEED = "am_michael", 0.93
SR = 24000
FIX = [(r"\b12:51 PM\b", "twelve fifty-one P.M."), (r"\b12:51\b", "twelve fifty-one"), (r"\b4:35\b", "four thirty-five"),
       (r"\b7\.1\b", "seven point one"), (r"\b6\.2\b", "six point two"), (r"ChristChurch Cathedral", "Christchurch Cathedral"),
       (r"\b2010\b", "twenty ten"), (r"\b2011\b", "twenty eleven"), (r"\b2017\b", "twenty seventeen"), (r"1870s", "eighteen seventies"),
       (r"\b185\b", "one hundred and eighty-five"), (r"Lyttelton", "Littleton"), (r"\bCTV\b", "C.T.V."), (r"\bPGC\b", "P.G.C."),
       (r"cafés", "cafes"), (r"Pyne Gould", "Pine Gould")]

def speak_text(s):
    for a, b in FIX:
        s = re.sub(a, b, s)
    return s

def main():
    k = Kokoro("/opt/kokoro/kokoro-v1.0.onnx", "/opt/kokoro/voices-v1.0.bin")
    paras = [p.strip() for p in open("script.txt").read().split("\n\n") if p.strip()]
    out, tl, t = [np.zeros(int(0.6 * SR))], [], 0.6
    for pi, p in enumerate(paras):
        sents = re.split(r"(?<=[.?!])\s+(?=[A-Z0-9])", p)
        for si, s in enumerate(sents):
            a, sr = k.create(speak_text(s), voice=VOICE, speed=SPEED, lang="en-us")
            a = np.asarray(a, np.float32)
            # trim silence
            idx = np.where(np.abs(a) > 0.01)[0]
            a = a[max(0, idx[0] - 240): idx[-1] + 1200] if len(idx) else a
            d = len(a) / SR
            words = s.split(); n = sum(len(w) + 1 for w in words); acc = 0; wt = []
            for w in words:
                wt.append([w, round(t + d * acc / n, 3)]); acc += len(w) + 1
            tl.append(dict(p=pi, s=si, text=s, start=round(t, 3), end=round(t + d, 3), words=wt))
            out.append(a); t += d
            short = len(words) <= 4
            gap = 0.75 if si == len(sents) - 1 else (0.55 if short else 0.33)
            if si == len(sents) - 1 and len(sents) == 1 and short: gap = 1.0
            out.append(np.zeros(int(gap * SR))); t += gap
        print(pi, round(t, 1), flush=True)
    out.append(np.zeros(int(3 * SR)))
    v = np.concatenate(out)
    sf.write("voice_raw.wav", v, SR)
    json.dump(tl, open("timeline.json", "w"), indent=1)
    print("total", len(v) / SR)

main()
