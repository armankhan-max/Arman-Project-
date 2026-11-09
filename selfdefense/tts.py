"""Voiceover: script.txt -> Kokoro TTS (offline ONNX) -> voice.wav + timeline.json.

Each sentence is synthesized separately so we know exactly when it starts and
ends; word times inside a sentence are spread by letter count (good enough for
captions and keyword pops)."""
import json, re, sys, os
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

MODELS = sys.argv[1] if len(sys.argv) > 1 else "models"
VOICE, SPEED, SR = "af_heart", 0.92, 24000
GAP_S, GAP_P = 0.20, 0.60

def sentences(par):
    out = re.split(r'(?<=[.?!])["”]?\s+(?=["“A-Z0-9])', par.strip())
    # re-attach a closing quote that the split may have left
    return [s.strip() for s in out if s.strip()]

def trim(a, thr=0.012):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0: return a
    return a[max(0, idx[0] - 240): idx[-1] + 1200]

def main():
    k = Kokoro(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
    pars = [p for p in open("script.txt").read().split("#") if p.strip()]
    audio, tl, t = [], [], 0.6
    audio.append(np.zeros(int(0.6 * SR), np.float32))
    for pi, par in enumerate(pars):
        for s in sentences(par):
            spoken = s.replace('"', '').replace('“', '').replace('”', '')
            a, sr = k.create(spoken, voice=VOICE, speed=SPEED, lang="en-us")
            a = trim(a.astype(np.float32))
            d = len(a) / SR
            ws = s.split()
            wl = np.array([max(2, len(re.sub(r"\W", "", w))) + 1.5 for w in ws], float)
            cum = np.concatenate([[0], np.cumsum(wl)]) / wl.sum() * d
            words = [{"w": w, "s": round(t + cum[i], 3), "e": round(t + cum[i + 1], 3)} for i, w in enumerate(ws)]
            tl.append({"i": len(tl), "par": pi, "start": round(t, 3), "end": round(t + d, 3), "text": s, "words": words})
            audio.append(a); t += d
            audio.append(np.zeros(int(GAP_S * SR), np.float32)); t += GAP_S
            print(f"{len(tl):3d} {t:7.2f} {s[:60]}", flush=True)
        audio.append(np.zeros(int(GAP_P * SR), np.float32)); t += GAP_P
    audio.append(np.zeros(int(1.5 * SR), np.float32))
    v = np.concatenate(audio)
    v = v / (np.abs(v).max() + 1e-6) * 0.89
    sf.write("build/voice.wav", v, SR)
    json.dump(tl, open("timeline.json", "w"), indent=1)
    print("total", len(v) / SR)

if __name__ == "__main__":
    os.makedirs("build", exist_ok=True); main()
