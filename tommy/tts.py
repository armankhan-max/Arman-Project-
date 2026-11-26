import re, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
d = sys.argv[1]
k = Kokoro(f"{d}/kokoro-v1.0.onnx", f"{d}/voices-v1.0.bin")
text = open("script.txt").read().strip()
paras = [p.strip() for p in text.split("\n\n") if p.strip()]
out = []
sr = 24000
for p in paras:
    sents = re.split(r'(?<=[.?!])\s+', p)
    for s in sents:
        a, sr = k.create(s, voice=sys.argv[2], speed=float(sys.argv[3]), lang="en-us")
        out.append(a)
        out.append(np.zeros(int(sr * 0.22)))
    out.append(np.zeros(int(sr * 0.35)))
x = np.concatenate(out)
sf.write("voice.wav", x, sr)
print(len(x) / sr)
