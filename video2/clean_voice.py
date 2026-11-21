"""Clean the voiceover: DeepFilterNet3 (noise + room/echo suppression) in chunks,
then ffmpeg polish (high-pass, de-mud EQ, presence, light expander for reverb tails,
compression, loudness -14 LUFS).  in.mp3 -> voice_clean.wav (48 kHz mono)"""
import subprocess, sys, wave
import numpy as np, torch
from df.enhance import enhance, init_df

src, out = sys.argv[1], sys.argv[2]
SR = 48000
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.float32).copy()
model, st, _ = init_df()

CH, OV = SR * 30, SR * 1
y = np.zeros_like(x)
w = np.zeros_like(x)
pos = 0
while pos < len(x):
    a, b = max(0, pos - OV), min(len(x), pos + CH + OV)
    seg = torch.from_numpy(x[a:b]).unsqueeze(0)
    e = enhance(model, st, seg, atten_lim_db=28).squeeze(0).numpy()
    win = np.ones(b - a, np.float32)
    r = min(OV, b - a)
    if a > 0: win[:r] = np.linspace(0, 1, r)
    if b < len(x): win[-r:] = np.linspace(1, 0, r)
    y[a:b] += e * win; w[a:b] += win
    pos += CH
    print(f"{pos / SR:.0f}s / {len(x) / SR:.0f}s", flush=True)
y /= np.maximum(w, 1e-6)

af = ("highpass=f=75,lowpass=f=15000,"
      "equalizer=f=250:t=q:w=1.2:g=-2.5,equalizer=f=3800:t=q:w=1.5:g=2.5,equalizer=f=9000:t=q:w=1:g=1,"
      "agate=threshold=0.012:ratio=2.2:attack=5:release=180:range=0.25,"
      "acompressor=threshold=0.09:ratio=3:attack=8:release=120:makeup=1.6,"
      "loudnorm=I=-14:TP=-1.2:LRA=9")
p = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-af", af, "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", out],
                   input=y.astype(np.float32).tobytes(), check=True)
print("done", out)
