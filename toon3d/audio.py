"""BGM + SFX bed for the bell-grave style test (numpy only). python3 audio.py out.wav
Every cue sits on the same times the picture uses (see CAM / RINGS in src/main.js)."""
import sys, wave
import numpy as np

SR, DUR = 44100, 20.5
N = int(SR * DUR)
rng = np.random.default_rng(4)
L = np.zeros(N); R = np.zeros(N)


def add(x, t, gain=1.0, pan=0.0, bus=None):
    i = int(t * SR)
    if i >= N or i < 0: return
    x = x[: N - i] * gain
    a, b = (bus if bus is not None else (L, R))
    a[i:i + len(x)] += x * (1 - max(0, pan)); b[i:i + len(x)] += x * (1 + min(0, pan))


def tt(d): return np.arange(int(d * SR)) / SR
def noise(d): return rng.standard_normal(int(d * SR))


def filt(x, lo=0, hi=1e9):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = 1 / (1 + (lo / np.maximum(f, 1)) ** 6) / (1 + (f / hi) ** 6)
    return np.fft.irfft(X * m, len(x))


def pluck(freq, d=0.7, bright=0.5):  # Karplus-Strong pizzicato
    n = int(SR / freq); buf = rng.uniform(-1, 1, n); out = np.empty(int(d * SR))
    k = 0.5 + 0.49 * bright
    for i in range(len(out)):
        out[i] = buf[i % n]; buf[i % n] = 0.996 * (k * buf[i % n] + (1 - k) * buf[(i + 1) % n])
    return out * np.exp(-tt(d) * 3.2)


def mallet(freq, d=0.6):
    t = tt(d); return (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 4 * t) * np.exp(-t * 18)) * np.exp(-t * 7)


def bell(d=0.9, f0=1650):
    t = tt(d); x = sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t * dec) for r, a, dec in [(1, 1, 5), (2.0, .6, 7), (2.76, .45, 9), (5.4, .25, 14), (8.9, .12, 22)])
    return x * (1 - np.exp(-t * 900)) * 0.4


def whoosh(d, f1=500, f2=3000, up=True):
    t = tt(d); k = t / d; env = np.sin(np.pi * k) ** 1.6
    n = noise(d); out = np.zeros_like(n); bands = 10
    for b in range(bands):  # swept band-pass
        kk = (b + 0.5) / bands; fc = f1 * (f2 / f1) ** (kk if up else 1 - kk)
        w = np.exp(-((k - kk) * bands / 2.2) ** 2); out += filt(n, fc * 0.6, fc * 1.6) * w
    return out * env * 0.5


def thud(f=85, d=0.25): t = tt(d); return np.sin(2 * np.pi * f * t * (1 + 0.6 * np.exp(-t * 30))) * np.exp(-t * 16) + filt(noise(d), 200, 2500) * np.exp(-t * 45) * 0.4
def blip(f1, f2, d=0.12): t = tt(d); return np.sin(2 * np.pi * np.cumsum(np.linspace(f1, f2, len(t))) / SR) * np.exp(-t * 14) * (1 - np.exp(-t * 400))
def rumble(d=0.7): t = tt(d); return filt(noise(d), 30, 260) * np.sin(np.pi * t / d) ** 1.3


# ---------- music: sneaky pizzicato, D minor, 104 bpm ----------
mL = np.zeros(N); mR = np.zeros(N); MB = (mL, mR)
beat = 60 / 104
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
bass = [38, None, 41, 45, 38, None, 34, 33, 38, None, 41, 45, 43, 41, 40, 37]
mel = {2: 74, 3.5: 77, 6: 76, 7: 74, 10: 69, 11.5: 72, 14: 73, 15: 70}
PL = {m: pluck(hz(m), 0.8, 0.35) for m in set(b for b in bass if b)}
PH = {m: pluck(hz(m + 12), 0.45, 0.7) for m in set(b for b in bass if b)}
i = 0; t = 0.0
while t < DUR:
    b = bass[i % 16]; hot = t > 14.8
    if b:
        add(PL[b], t, 0.55, 0, MB)
        if hot: add(PH[b], t + beat / 2, 0.22, 0.3, MB)
    k = i % 16
    for off, m in mel.items():
        if int(off) == k and t > 2.5: add(mallet(hz(m)), t + (off - k) * beat, 0.16, -0.3, MB)
    add(filt(noise(0.05), 5000, 12000) * np.exp(-tt(0.05) * 80), t + beat / 2, 0.10 if not hot else 0.2, 0.4, MB)
    if hot: add(filt(noise(0.05), 5000, 12000) * np.exp(-tt(0.05) * 80), t + beat / 4, 0.12, -0.4, MB)
    t += beat; i += 1
# muffle the music while the camera is underground, like the picture
env_under = np.zeros(N)
for a, b in [(3.0, 6.05), (8.35, 10.35)]:
    s = np.clip((np.arange(N) / SR - a) / 0.25, 0, 1) * np.clip((b - np.arange(N) / SR) / 0.25, 0, 1); env_under = np.maximum(env_under, s)
for ch, dst in ((mL, L), (mR, R)): dst += (ch * (1 - env_under) + filt(ch, 0, 420) * env_under * 1.5) * 0.8

# ---------- ambience: crickets + night air (above ground only) ----------
t = tt(DUR)
crk = np.sin(2 * np.pi * 4300 * t) * (np.sin(2 * np.pi * 31 * t) > 0.3) * (np.sin(2 * np.pi * 1.35 * t) > 0.1) * 0.02
air = filt(noise(DUR), 150, 900) * 0.012
L += (crk + air) * (1 - env_under); R += (np.roll(crk, 900) + air) * (1 - env_under)
low = filt(noise(DUR), 30, 140) * 0.05 * env_under; L += low; R += low

# ---------- SFX ----------
add(bell(0.7, 2400), 0.12, 0.28)                                            # glint on the bell
for a, d, up, g in [(0.8, 0.95, False, .5), (2.55, 0.8, False, .7), (3.88, 0.4, True, .5), (5.55, 0.95, True, .7), (7.95, 0.8, False, .65),
                    (9.95, 0.8, True, .7), (12.25, 0.7, True, .8), (14.45, 0.6, False, .8), (16.15, 1.8, True, .6)]:
    add(whoosh(d, 350, 3800, up), a, g, 0.25 if up else -0.25)            # every camera move gets air
for a in (1.25, 1.65, 2.05): add(thud(95), a, 0.7, -0.3)                   # shovel pats
for a in (2.92, 6.02, 8.3, 10.32): add(rumble(0.6), a, 0.9)               # passing through the soil
add(blip(300, 1400, 0.16), 3.9, 0.45); add(thud(60, 0.3), 3.9, 0.5)       # eyes snap open
for a in np.arange(4.0, 5.6, 0.42):                                        # heartbeat in the coffin
    add(thud(55, 0.18), a, 0.75); add(thud(48, 0.18), a + 0.14, 0.5)
add(bell(1.2), 6.55, 0.4)                                                  # bell reveal
for a in (8.95, 9.24, 9.53): add(pluck(520, 0.3, 0.8) * (1 + 0.0 * tt(0.3)), a, 0.4, 0.3)  # finger wiggles the string
rings = [10.1, 10.5, 10.9, 11.35, 12.0] + [round(x, 2) for x in np.arange(14.9, 16.6, 0.15)] + [round(x, 2) for x in np.arange(16.6, 20.4, 0.19)]
for r in rings:
    far = 0.33 if 12.6 < r < 14.6 else (0.85 if r < 16.4 else max(0.3, 0.85 - (r - 16.4) * 0.3))
    add(bell(1.3 if r in (11.35, 12.0) else 0.7, 1650 * (1 + rng.uniform(-.01, .01))), r, 0.5 * far, 0.15)
    if r < 12.3: add(pluck(300, 0.15, 0.9), r - 0.1, 0.25)                 # the yank on the string
add(blip(900, 1300, 0.06), 12.55, 0.4, 0.3)                                # lamp click
add(blip(250, 700, 0.14), 12.78, 0.4, 0.3)                                 # neighbor pops up
for k, a in enumerate(np.arange(13.18, 14.0, 0.115)):                      # sleepy mumble
    f = 150 + 45 * np.sin(k * 2.1); tm = tt(0.085)
    v = (np.sign(np.sin(2 * np.pi * f * tm)) * 0.3 + np.sin(2 * np.pi * f * tm)) * np.sin(np.pi * tm / 0.085)
    add(filt(np.pad(v, 2000), 300, 1400), a - 2000 / SR, 0.3, 0.3)
add(thud(120, 0.2), 14.24, 0.9, 0.3); add(filt(noise(0.06), 800, 5000) * np.exp(-tt(0.06) * 60), 14.24, 0.6, 0.3)  # shutters slam
for k, d in enumerate(sorted([0.0, 0.75, 0.35, 1.1, 0.55, 1.4])):          # the street lights up, one pop each
    add(blip(500 + k * 110, 900 + k * 160, 0.1), 16.9 + d, 0.4, (k % 3 - 1) * 0.5)
    add(blip(700 + k * 90, 380, 0.16), 16.9 + d + 0.45, 0.28, (k % 3 - 1) * 0.5)
add(mallet(hz(50), 1.4) + mallet(hz(62), 1.4) + mallet(hz(69), 1.4), 19.3, 0.3)

mix = np.stack([L, R], 1); mix = np.tanh(mix * 1.5) * 0.9
fade = np.clip((DUR - np.arange(N) / SR) / 0.35, 0, 1); mix *= fade[:, None]
w = wave.open(sys.argv[1] if len(sys.argv) > 1 else 'mix.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mix * 32767).astype(np.int16).tobytes()); w.close()
print('peak', np.abs(mix).max().round(3), 'rms', np.sqrt((mix ** 2).mean()).round(3))
