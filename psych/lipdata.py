"""Build per-frame lip-sync data (mouth open + roundness) from the voiceover. Output: lips.npy (N x 2) at 30 fps."""
import sys
import numpy as np
from scipy.io import wavfile

sr, x = wavfile.read(sys.argv[1])
x = x.astype(np.float32) / 32768
fps = 30
hop = sr // fps
n = len(x) // hop
rms = np.zeros(n)
cent = np.zeros(n)
win = np.hanning(hop * 2)
freqs = np.fft.rfftfreq(hop * 2, 1 / sr)
for i in range(n):
    seg = x[max(0, i * hop - hop // 2): i * hop + hop + hop // 2]
    if len(seg) < hop * 2:
        seg = np.pad(seg, (0, hop * 2 - len(seg)))
    rms[i] = np.sqrt(np.mean(seg ** 2))
    sp = np.abs(np.fft.rfft(seg * win))
    band = (freqs > 150) & (freqs < 4000)
    cent[i] = np.sum(freqs[band] * sp[band]) / (np.sum(sp[band]) + 1e-9)
ref = np.percentile(rms[rms > 1e-4], 92)
o = np.clip((rms / ref - 0.12) / 0.88, 0, 1) ** 0.8
# attack fast, release medium so the mouth closes between words
sm = np.zeros(n)
for i in range(n):
    prev = sm[i - 1] if i else 0
    k = 0.75 if o[i] > prev else 0.45
    sm[i] = prev + (o[i] - prev) * k
rnd = np.clip((1800 - cent) / 1200, 0, 1)
np.save(sys.argv[2], np.stack([sm, rnd], 1).astype(np.float32))
print(n, "frames", sm.mean())
