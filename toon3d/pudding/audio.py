"""Final mix for the Pudding Guy short: voice + BGM + SFX. python3 audio.py OUT.wav
Cue times are derived from vo.json exactly like src/pudding.js, so sound lands on the picture."""
import sys, json, os
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
VO = json.load(open(HERE + '/vo.json')); voice, SR = sf.read(HERE + '/voice.wav')
DUR = VO['dur']; N = int(SR * DUR); voice = np.pad(voice, (0, max(0, N - len(voice))))[:N]
A = lambda i: VO['sents'][i][0]
B = lambda i: VO['sents'][i][1]
CT = lambda s: next(c[0] for c in VO['chunks'] if c[2].startswith(s))
rng = np.random.default_rng(7)
T_STAMP = CT('tax write-off') + 0.38


class Bus:
    def __init__(s): s.L = np.zeros(N); s.R = np.zeros(N)
    def add(s, x, t, g=1.0, pan=0.0):
        i = int(t * SR)
        if i < 0 or i >= N: return
        x = x[:N - i] * g; s.L[i:i + len(x)] += x * min(1, 1 - pan); s.R[i:i + len(x)] += x * min(1, 1 + pan)


def tt(d): return np.arange(int(d * SR)) / SR
def noise(d): return rng.standard_normal(int(d * SR))
def filt(x, lo=0, hi=1e9):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (lo / np.maximum(f, 1)) ** 6) / (1 + (f / hi) ** 6), len(x))
hz = lambda m: 440 * 2 ** ((m - 69) / 12)


def pluck(f, d=0.6, bright=0.4):
    n = int(SR / f); buf = rng.uniform(-1, 1, n); out = np.empty(int(d * SR)); k = 0.5 + 0.49 * bright
    for i in range(len(out)):
        j = i % n; out[i] = buf[j]; buf[j] = 0.996 * (k * buf[j] + (1 - k) * buf[(j + 1) % n])
    return out * np.exp(-tt(d) * 3.0)
def mallet(f, d=0.7): t = tt(d); return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 20)) * np.exp(-t * 6) * (1 - np.exp(-t * 500))
def keys(f, d=1.0): t = tt(d); return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t) * np.exp(-t * 4) + 0.12 * np.sin(6 * np.pi * f * t) * np.exp(-t * 7)) * np.exp(-t * 2.4) * (1 - np.exp(-t * 90))
def bell(d=0.8, f0=1700): t = tt(d); return sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t * dc) for r, a, dc in [(1, 1, 6), (2.0, .5, 8), (2.76, .35, 11), (5.4, .15, 16)]) * (1 - np.exp(-t * 700)) * 0.4
def whoosh(d, up=True, lo=250, hi=2600):
    t = tt(d); k = t / d; n = noise(d); out = np.zeros_like(n)
    for b in range(8):
        kk = (b + .5) / 8; fc = lo * (hi / lo) ** (kk if up else 1 - kk); out += filt(n, fc * .65, fc * 1.5) * np.exp(-((k - kk) * 3.4) ** 2)
    return out * np.sin(np.pi * k) ** 2 * 0.45
def thud(f=80, d=0.25): t = tt(d); return np.sin(2 * np.pi * f * t * (1 + .5 * np.exp(-t * 30))) * np.exp(-t * 15) + filt(noise(d), 200, 1800) * np.exp(-t * 50) * .3
def blip(f1, f2, d=0.1): t = tt(d); return np.sin(2 * np.pi * np.cumsum(np.linspace(f1, f2, len(t))) / SR) * np.exp(-t * 13) * (1 - np.exp(-t * 350))
def tick(f=2500, d=0.03): t = tt(d); return filt(noise(d), f * .6, f * 1.6) * np.exp(-t * 130)
def beep(f=1900, d=0.05): t = tt(d); return np.sin(2 * np.pi * f * t) * np.sin(np.pi * t / d) ** 0.5 * 0.5
def chaching(): x = np.zeros(int(.7 * SR)); a = bell(.6, 2100); b = bell(.6, 2800); x[:len(a)] += a; o = int(.07 * SR); x[o:o + len(b)] += b[:len(x) - o]; c = tick(4000, .04); x[:len(c)] += c * .8; return x
def jet(d): t = tt(d); k = t / d; return filt(noise(d), 120, 1400) * np.sin(np.pi * k) ** 1.5 * (0.6 + 0.4 * np.sin(2 * np.pi * (90 - 30 * k) * t)) * 0.5


# ---------------- music: light funky pizzicato in F, 108 bpm ----------------
M = Bus(); beat = 60 / 108; bar = beat * 4
MAJ = [(41, [65, 69, 72]), (38, [62, 65, 69]), (34, [58, 62, 65]), (36, [60, 64, 67])]   # F Dm Bb C
MIN = [(38, [62, 65, 69]), (38, [62, 65, 69]), (31, [58, 62, 67]), (33, [57, 61, 64])]   # Dm Dm Gm A
cache = {}
def P(m, d=0.6, b=0.35):
    if (m, d, b) not in cache: cache[(m, d, b)] = pluck(hz(m), d, b)
    return cache[(m, d, b)]
t_end = A(23) + 0.05; nb = 0; t = 0.0
while t < t_end:
    sec = 'hook' if t < A(2) else 'light' if t < A(10) else 'build' if t < A(13) else 'big' if t < A(15) else 'problem' if t < A(17) else 'hope' if t < A(20) else 'full'
    root, ch = (MIN if sec == 'problem' else MAJ)[nb % 4]
    for b8 in range(8):
        tb = t + b8 * beat / 2
        if tb >= t_end: break
        pat = [1, 0, 0, 1, 0, 1, 1, 0] if sec != 'problem' else [1, 0, 0, 0, 1, 0, 0, 0]
        if pat[b8]: M.add(P(root + (12 if b8 in (3, 6) else 0), 0.7, 0.3), tb, 0.6)
        if sec in ('hook', 'big', 'hope', 'full', 'build') and b8 in (2, 6):
            for k, n in enumerate(ch): M.add(keys(hz(n), 0.9), tb, 0.085, (k - 1) * 0.35)
        if sec in ('light', 'problem') and b8 == 4: M.add(keys(hz(ch[1]), 1.0), tb, 0.07, 0.2)
        if sec in ('hook', 'build', 'big', 'full') or (sec in ('light', 'hope') and b8 % 2): M.add(tick(7000, 0.035), tb, 0.10 if b8 % 2 else 0.06, 0.4)
        if sec in ('hook', 'build', 'big', 'hope', 'full') and b8 in (0, 4): M.add(thud(58, 0.18), tb, 0.3)
        if sec in ('full', 'hook', 'big') and b8 in (1, 3, 5): M.add(mallet(hz(ch[(b8 + nb) % 3] + 12), 0.5), tb, 0.085, -0.35)
        if sec == 'build': M.add(P(ch[b8 % 3] + 0, 0.3, 0.7), tb, 0.12, -0.3)
    t += bar; nb += 1
for k, n in enumerate([53, 65, 69, 72, 77]): M.add(keys(hz(n), 1.9), T_STAMP + 0.28, 0.13, (k - 2) * 0.25)   # final button chord
M.add(P(41, 1.2, 0.3), T_STAMP + 0.28, 0.6)

# ---------------- SFX ----------------
X = Bus()
def W(t, d, up=True, g=0.22, pan=0.0): X.add(whoosh(d, up), t, g, pan)
X.add(bell(0.5, 2600), 0.05, 0.12)
for bt in np.arange(0.2, 1.0, 0.42): X.add(blip(420, 300, 0.07), bt, 0.12)
W(0.9, 0.9, False, 0.26); [X.add(tick(3000 + rng.uniform(-800, 800), 0.03), 1.2 + i * 0.05, 0.08, rng.uniform(-.5, .5)) for i in range(12)]
W(2.3, 0.85, True, 0.22); X.add(jet(2.2), 2.5, 0.42, 0.2); W(4.2, 0.9, False, 0.28)
X.add(thud(140, 0.12), 5.05, 0.25)
W(A(3), 0.5, True, 0.14); X.add(blip(600, 900, 0.09), CT('10 barcodes'), 0.25); X.add(blip(800, 1250, 0.09), CT('500'), 0.25)
W(A(4), 0.5, False, 0.16); [X.add(thud(110, 0.08), A(4) - 0.3 + i * 0.26, 0.1, -0.4 + i * 0.2) for i in range(5)]
W(A(5), 0.38, True, 0.26); X.add(bell(0.7, 2300), A(5) + 0.22, 0.22)
W(A(6), 0.55, True, 0.14)
for bt in np.arange(A(6) + 0.5, 15.1, 0.13): X.add(beep(1200 + rng.integers(0, 5) * 150, 0.04), bt, 0.07, 0.2)
for i, bt in enumerate([13.25, 13.95, 14.7]): X.add(blip(500 + i * 120, 800 + i * 150, 0.09), bt, 0.22, -0.2)
X.add(bell(0.9, 1900), 15.25, 0.3); X.add(bell(0.9, 2850), 15.33, 0.2)
W(A(7), 0.65, True, 0.28, 0.3); X.add(blip(700, 500, 0.12), A(7) + 0.75, 0.1)
W(A(8), 0.5, True, 0.16); X.add(bell(0.4, 2500), A(8) + 0.5, 0.12)
W(CT('25 cents') - 0.1, 0.45, False, 0.14); X.add(chaching(), CT('25 cents') + 0.25, 0.3)
W(A(9), 0.5, True, 0.16); W(A(9) + 1.15, 0.5, False, 0.16)
for bt in np.arange(A(9) + 1.45, B(9) + 0.05, 0.062): X.add(beep(1900, 0.04), bt, 0.13, -0.3 + 0.6 * (bt - A(9) - 1.45) / 0.65)
W(A(10), 0.55, False, 0.2)
for i in range(80): X.add(tick(1800 + rng.uniform(-500, 900), 0.035), A(10) + 0.25 + i * 0.021 + 0.3, 0.11, rng.uniform(-.4, .4))
for i in range(10): X.add(beep(900 + i * 60, 0.035), A(10) + 0.5 + i * (B(10) - A(10) - 0.7) / 10, 0.07, 0.3)
W(B(10) - 0.4, 0.8, True, 0.3, 0.3)
X.add(beep(1500, 0.07), A(11) + 0.55, 0.14, 0.3)
W(A(12), 0.4, True, 0.2)
zz = filt(noise(1.1), 900, 4500) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 38 * tt(1.1)))) * np.sin(np.pi * tt(1.1) / 1.1) ** 0.6
X.add(zz, A(12) + 0.1, 0.07, 0.35); X.add(mallet(hz(46), 0.5), B(12) - 0.1, 0.3)
W(A(13) - 0.15, 0.85, False, 0.34, -0.3); X.add(filt(noise(2.2), 40, 220) * np.sin(np.pi * tt(2.2) / 2.2), A(13) + 0.3, 0.3)
for i in range(190): X.add(tick(1500 + rng.uniform(-500, 1500), 0.04), A(13) + 0.55 + rng.uniform(0, 1.75), 0.09, rng.uniform(-.7, .7))
X.add(blip(300, 900, 0.14), B(13) - 0.75, 0.3); X.add(bell(0.6, 2200), B(13) - 0.45, 0.16)
W(A(14) - 0.05, 0.6, False, 0.2); X.add(filt(noise(0.6), 1500, 6000) * np.sin(np.pi * tt(0.6) / 0.6) ** 2, A(14) - 0.1, 0.06); X.add(chaching(), CT('$3,000') + 0.05, 0.3)
W(A(15), 0.4, True, 0.22); X.add(thud(52, 0.5), A(15) + 0.4, 0.55); X.add(mallet(hz(38), 0.9), A(15) + 0.4, 0.3)
W(A(16), 0.5, False, 0.2, -0.3)
for i, bt in enumerate(np.arange(A(16) + 0.4, CT('12,000 labels') + 0.6, 0.25)): X.add(tick(2600 if i % 2 else 2000, 0.03), bt, 0.16, -0.2)
W(CT('and nobody'), 0.55, True, 0.2, 0.3)
for bt in np.arange(CT('and nobody') + 0.6, CT('12,000 labels'), 0.2): X.add(blip(700, 1500, 0.07), bt, 0.07, 0.2)
W(CT('12,000 labels') + 0.05, 0.6, True, 0.22); X.add(blip(520, 260, 0.35), B(16) - 0.4, 0.14)
W(A(17), 0.5, False, 0.2)
for i, f in enumerate([941, 1209, 852, 1336]): X.add(beep(f, 0.07), A(17) + 0.5 + i * 0.11, 0.1, 0.3)
W(A(18) - 0.05, 0.6, True, 0.32, -0.4)
for bt in np.arange(A(18) + 0.5, CT('they keep'), 0.11): X.add(filt(noise(0.07), 2000, 7000) * np.linspace(0.2, 1, int(0.07 * SR)) ** 2, bt, 0.06, rng.uniform(-.5, .5))
for bt in np.arange(CT('they keep') + 0.1, B(18), 0.2): X.add(bell(0.25, 3200 + rng.uniform(-300, 300)), bt, 0.07, rng.uniform(-.5, .5))
W(A(19), 0.55, True, 0.24, 0.4)
tm = CT('the barcodes,') + 0.35
X.add(whoosh(0.22, True, 800, 4000), tm, 0.2, 0.3); X.add(blip(260, 120, 0.2), tm + 0.2, 0.4, 0.3); X.add(bell(0.5, 2400), tm + 0.52, 0.2, 0.3)
for bt in (A(19) + 0.2, A(19) + 1.0, A(19) + 1.6): X.add(blip(3200, 4200, 0.06), bt, 0.04, -0.6); X.add(blip(3600, 4400, 0.05), bt + 0.09, 0.04, -0.6)
W(CT('and gets') + 0.1, 0.8, True, 0.26); X.add(jet(1.6), CT('and gets') + 0.2, 0.36, -0.3)
for i, f in enumerate([1600, 2000, 2400, 3200]): X.add(bell(0.7, f), CT('1.25 million') + i * 0.07, 0.13, (i - 1.5) * 0.3)
W(A(20), 0.6, True, 0.24); X.add(chaching(), CT('$150,000') + 0.08, 0.3)
W(A(21), 0.5, True, 0.16)
for i in range(5): X.add(thud(150, 0.1), A(21) + 0.35 + i * 0.3, 0.3, (i % 2 - .5) * 0.6); X.add(tick(2200, 0.03), A(21) + 0.35 + i * 0.3, 0.12)
W(A(22), 0.5, True, 0.14); X.add(blip(500, 900, 0.1), A(22) + 0.5, 0.2, 0.3)
W(A(23), 0.35, True, 0.14)
X.add(thud(62, 0.45), T_STAMP, 0.95); X.add(tick(1500, 0.06), T_STAMP, 0.35); X.add(bell(1.0, 2500), T_STAMP + 0.3, 0.2); X.add(bell(1.0, 3150), T_STAMP + 0.36, 0.14)
cab = filt(noise(DUR), 80, 420) * np.clip((np.arange(N) / SR - A(20)) / 0.8, 0, 1) * 0.016; X.L += cab; X.R += cab   # cabin air

# ---------------- mix ----------------
env = np.abs(voice); k = int(0.08 * SR); env = np.convolve(env, np.ones(k) / k, 'same'); env = np.clip(env / 0.12, 0, 1)
duck = 1 - 0.3 * env
fade = np.clip((DUR - np.arange(N) / SR) / 0.5, 0, 1)
mus = np.stack([filt(M.L, 35, 9000), filt(M.R, 35, 9000)], 1) * 0.048 * duck[:, None]
sfx = np.stack([filt(X.L, 35, 9500), filt(X.R, 35, 9500)], 1) * 0.85
v = np.stack([voice, voice], 1) * 0.95
mix = np.tanh((v + mus + sfx) * 1.55) * 0.95 * fade[:, None]
r = lambda x: 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
print('rms dB  voice %.1f  music %.1f  sfx %.1f  mix %.1f  | peak sfx %.2f music %.2f mix %.2f' % (r(v), r(mus), r(sfx), r(mix), np.abs(sfx).max(), np.abs(mus).max(), np.abs(mix).max()))
sf.write(sys.argv[1] if len(sys.argv) > 1 else 'mix.wav', mix, SR)
