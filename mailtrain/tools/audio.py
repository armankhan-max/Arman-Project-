"""Original synthesized soundtrack (royalty-free): sombre string-like pad, soft sea
wash and faint film-projector crackle, ducked under the narration.
usage: python audio.py voice_edit.wav out_mix.wav"""
import sys, numpy as np, subprocess
from scipy import signal

SR = 24000
voice_path, out = sys.argv[1], sys.argv[2]
v = subprocess.check_output(["ffmpeg", "-loglevel", "error", "-i", voice_path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"])
voice = np.frombuffer(v, np.float32).copy()
N = len(voice); T = N / SR
rng = np.random.default_rng(7)
t = np.arange(N, dtype=np.float32) / np.float32(SR)

def note(m):  # midi -> Hz
    return 440.0 * 2 ** ((m - 69) / 12)

# --- pad: slow minor progression, each chord 14 s with 5 s crossfades
prog = [[45, 57, 60, 64], [41, 53, 57, 60], [48, 55, 60, 64], [43, 55, 59, 62],
        [45, 57, 60, 64], [38, 50, 57, 62], [40, 52, 56, 59], [45, 52, 57, 60]]
CH = 14.0
padL = np.zeros(N, np.float32); padR = np.zeros(N, np.float32)
nchords = int(T / CH) + 2
for c in range(nchords):
    ch = prog[c % len(prog)]
    s0 = c * CH - 5; s1 = (c + 1) * CH + 5
    a, b = max(0, int(s0 * SR)), min(N, int(s1 * SR))
    if a >= b: continue
    tt = np.arange(b - a, dtype=np.float64) / SR + (a / SR - s0)
    L = s1 - s0
    env = np.clip(np.minimum(tt / 5.0, (L - tt) / 5.0), 0, 1)
    env = (np.sin(env * np.pi / 2) ** 2).astype(np.float32)
    for k, m in enumerate(ch):
        f = note(m)
        amp = 0.16 if k == 0 else 0.10
        for det, side in ((-0.12, 0), (0.12, 1)):
            ph = rng.uniform(0, 6.28)
            vib = 0.0025 * np.sin(2 * np.pi * (0.13 + 0.05 * k) * tt + ph)
            w = 2 * np.pi * (f + det) * tt * (1 + vib)
            sig = np.sin(w + ph) + 0.35 * np.sin(2 * w + ph) + 0.12 * np.sin(3 * w)
            (padL if side == 0 else padR)[a:b] += (amp * env * sig).astype(np.float32)
# soft low-pass and slow swell
sos = signal.butter(2, 1400, "low", fs=SR, output="sos")
padL = signal.sosfilt(sos, padL).astype(np.float32); padR = signal.sosfilt(sos, padR).astype(np.float32)
swell = (0.75 + 0.25 * np.sin(2 * np.pi * t / 47.0)).astype(np.float32)
padL *= swell; padR *= swell

# reverb (exponential noise IR), overlap-add
ir_len = int(3.2 * SR)
irt = np.arange(ir_len) / SR
def ir():
    x = rng.normal(0, 1, ir_len) * np.exp(-irt / 0.9)
    x = signal.sosfilt(signal.butter(2, 3000, "low", fs=SR, output="sos"), x)
    return (x / np.sqrt(np.sum(x ** 2))).astype(np.float32)
padL = 0.55 * padL + 0.8 * signal.oaconvolve(padL, ir())[:N].astype(np.float32)
padR = 0.55 * padR + 0.8 * signal.oaconvolve(padR, ir())[:N].astype(np.float32)

# --- sea wash: brown-ish noise, band-passed, slow swells
def sea():
    n = rng.normal(0, 1, N).astype(np.float32)
    n = signal.sosfilt(signal.butter(2, [120, 1800], "band", fs=SR, output="sos"), n).astype(np.float32)
    phase = rng.uniform(0, 6.28)
    env = 0.45 + 0.55 * (0.5 + 0.5 * np.sin(2 * np.pi * t / 9.5 + phase)) ** 2.5
    env *= 0.8 + 0.2 * np.sin(2 * np.pi * t / 31.0)
    return n * env.astype(np.float32)
seaL, seaR = sea(), sea()

# --- projector crackle: sparse clicks
crk = np.zeros(N, np.float32)
idx = rng.integers(0, N, int(T * 3))
crk[idx] = rng.normal(0, 1, len(idx)).astype(np.float32)
crk = signal.sosfilt(signal.butter(2, 2500, "high", fs=SR, output="sos"), crk).astype(np.float32)

def rms(x): return float(np.sqrt(np.mean(x[::50].astype(np.float64) ** 2)) + 1e-9)
vr = rms(voice)
padL *= (vr * 10 ** (-20 / 20)) / rms(padL); padR *= (vr * 10 ** (-20 / 20)) / rms(padR)
seaL *= (vr * 10 ** (-29 / 20)) / rms(seaL); seaR *= (vr * 10 ** (-29 / 20)) / rms(seaR)
crk *= (vr * 10 ** (-40 / 20)) / rms(crk)

# --- ducking: music sits lower while the narrator speaks
env = np.abs(voice)
env = signal.sosfilt(signal.butter(1, 3, "low", fs=SR, output="sos"), env)
env = np.clip(env / (np.percentile(env, 90) + 1e-9), 0, 1)
duck = (1.0 - 0.45 * env).astype(np.float32)
# fade in/out of the whole bed
fade = np.clip(np.minimum(t / 4.0, (T - t) / 6.0), 0, 1).astype(np.float32)
mL = (padL * duck + seaL * duck * 0.9 + crk) * fade
mR = (padR * duck + seaR * duck * 0.9 + crk) * fade
st = np.stack([mL, mR], 1)
p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                      "-ar", "48000", "-c:a", "pcm_f32le", out], stdin=subprocess.PIPE)
p.stdin.write(st.astype(np.float32).tobytes()); p.stdin.close(); p.wait()
print("bed ok", T)
