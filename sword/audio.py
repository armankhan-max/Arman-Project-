"""Procedural SFX + BGM for the sword video (numpy only). Timing comes from timing.json (same clock as the 3D scene)."""
import json, wave, numpy as np
TM = json.load(open('timing.json')); T = TM['T']; DUR = TM['dur']
SR = 44100; N = int(DUR * SR); R = np.random.default_rng(7)
L = np.zeros(N); Rr = np.zeros(N)
def tt(d): return np.arange(int(d * SR)) / SR
def put(x, t, g=1.0, pan=0.0):
    i = int(t * SR); 
    if i >= N: return
    x = x[:N - i] if i >= 0 else x[-i:]; i = max(i, 0)
    L[i:i + len(x)] += x * g * (1 - max(0, pan)); Rr[i:i + len(x)] += x * g * (1 + min(0, pan))
def fil(x, lo=None, hi=None):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); H = np.ones_like(f)
    if hi: H *= 1 / (1 + (f / hi) ** 4)
    if lo: H *= 1 - 1 / (1 + (f / lo) ** 4)
    return np.fft.irfft(X * H, len(x))
def noise(d): return R.normal(0, 1, int(d * SR))
def env(d, a=.003, dec=8): t = tt(d); return np.minimum(1, t / a) * np.exp(-t * dec)
def sweep_tone(d, f0, f1, curve=1.0, harm=(1,)):
    t = tt(d); f = f0 + (f1 - f0) * (t / d) ** curve; ph = 2 * np.pi * np.cumsum(f) / SR
    return sum(np.sin(ph * h) / h for h in harm)
def thud(d=.55, f0=140, f1=38, g=1): t = tt(d); return (sweep_tone(d, f0, f1, .35) * env(d, .002, 6) + fil(noise(d), None, 600) * env(d, .001, 40) * .6) * g
def clang(d=.9, base=620, g=1):
    t = tt(d); x = sum(np.sin(2 * np.pi * base * r * t) * np.exp(-t * (5 + i * 3)) / (i + 1) for i, r in enumerate([1, 2.76, 5.4, 8.93, 13.3])); return x * g
def crack(d=.25, g=1): return (fil(noise(d), 900, None) * env(d, .0005, 28) + np.sin(2 * np.pi * 1700 * tt(d)) * env(d, .0005, 60) * .4) * g
def whoosh(d, f0, f1, g=1, q=.5):
    x = noise(d); out = np.zeros(len(x)); win = 2048; hop = 1024; w = np.hanning(win)
    for s in range(0, len(x) - win, hop):
        fc = f0 + (f1 - f0) * (s / len(x)); seg = x[s:s + win] * w; X = np.fft.rfft(seg); f = np.fft.rfftfreq(win, 1 / SR)
        X *= np.exp(-((np.log(f + 1) - np.log(fc)) / q) ** 2); out[s:s + win] += np.fft.irfft(X, win)
    e = np.sin(np.pi * np.linspace(0, 1, len(x))) ** 1.5; return out / (np.abs(out).max() + 1e-9) * e * g
def shimmer(d, f0=900, f1=3200, g=1):
    t = tt(d); x = sum(np.sin(2 * np.pi * (f0 + (f1 - f0) * (t / d)) * k * t + k) / k for k in (1, 1.5, 2, 3)) ; return x * np.sin(np.pi * t / d) ** 1.2 * g * .25
def screech(d, g=1):
    t = tt(d); f = 1250 + 500 * np.sin(2 * np.pi * 3 * t) * 0 + 700 * (1 - t / d) ** .7 + 60 * np.sin(2 * np.pi * 17 * t); ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + .5 * np.sin(2 * ph) + .3 * np.sin(3.01 * ph) + fil(noise(d), 1500, 7000) * .9
    return x * np.minimum(1, t / .03) * (1 - t / d) ** .6 * g * .5
def riser(d, f0, f1, g=1):
    t = tt(d); f = f0 * (f1 / f0) ** (t / d); ph = 2 * np.pi * np.cumsum(f) / SR
    x = (np.sin(ph) + .5 * np.sin(2 * ph) + .25 * np.sin(3 * ph)) + fil(noise(d), 300, 6000) * (t / d) * .6
    return x * (t / d) ** 1.6 * g
def boom(d=3.5, g=1): t = tt(d); return (sweep_tone(d, 75, 22, .3) * np.exp(-t * 1.1) + fil(noise(d), None, 900) * np.exp(-t * 2.2) * 1.3 + fil(noise(d), None, 120) * np.exp(-t * .9) * 1.5) * g
def engine(t0, t1, fn, g=1):
    d = t1 - t0; t = tt(d); f = np.array([fn(t0 + s) for s in t[::50]]); f = np.interp(np.arange(len(t)), np.arange(0, len(t), 50), f); ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + .6 * np.sin(2 * ph + .3) + .4 * np.sin(3 * ph) + .25 * np.sin(4 * ph); x = fil(x + fil(noise(d), None, 500) * .5, None, 700)
    e = np.minimum(1, t / .4) * np.minimum(1, (d - t) / .4); put(x * e * g, t0, 1, 0)
def ping(f, d=.35, g=1): t = tt(d); return np.sin(2 * np.pi * f * t) * np.exp(-t * 11) * g
def pad(t0, d, notes, g=1):
    t = tt(d); x = 0
    for n in notes:
        for det in (-.004, .004): x = x + 2 * ((t * n * (1 + det)) % 1) - 1
    x = fil(x, None, 900); put(x * np.minimum(1, t / 1.0) * np.minimum(1, (d - t) / 1.0) * g, t0)

# ---------------- BGM (A minor, tense then huge) ----------------
A2, E3, A3, C4, E4, F2, G2 = 110, 164.8, 220, 261.6, 329.6, 87.3, 98
pad(0, 7, [A2, E3, A3], .05); pad(7, 8.4, [A2, E3, C4], .06); pad(15.4, 8.6, [F2, C4 / 2 * 1.0, A3], .06); pad(24, 7.4, [A2, E3, A3, C4], .07)
beat = 60 / 128
for k in range(int(7 / beat), int(31.2 / beat)):   # driving bass pulse
    t0 = k * beat; lvl = .08 + .1 * min(1, max(0, (t0 - 7) / 24)); f = [A2, A2, G2, F2][(k // 8) % 4]
    x = fil(2 * ((tt(.28) * f) % 1) - 1, None, 400 + 600 * (t0 / 31)) * env(.28, .005, 9); put(x, t0, lvl)
    if k % 2 == 0: put(thud(.18, 170, 55) * .35, t0, 1)
for k in range(int(15 / beat * 2), int(31.2 / beat * 2)): put(fil(noise(.07), 6000, None) * env(.07, .001, 55), k * beat / 2, .07 + .04 * (k % 2))
for k in range(int(26.3 / beat), int(31.2 / beat)): put(clang(.15, 880 + 40 * (k % 4)) * .06, k * beat, 1)
# duck + riser into the explosion
put(riser(T['boom'] - 26.3 + 0.0, 70, 900, .06) , 26.3, 1) if False else put(riser(5.0, 90, 1400, .22), T['boom'] - 5.0)
put(boom(5.5, 1.0), T['boom']); put(whoosh(2.5, 300, 90, .5, .9), T['boom'] + .1)
for t0, g in [(33.2, .8)]: put(fil(noise(3), None, 200) * np.sin(np.pi * tt(3) / 3) * 1.3, t0)
pad(34.1, 5.2, [A2 / 2, E3 / 2, 233, 311], .09)
put(riser(2.6, 200, 3000, .18), 35.0); put(shimmer(2.2, 600, 2400, .6), 35.7); put(ping(1568, 1.0, .5), T['orb']); put(ping(2093, 1.2, .4), T['orb'] + .12)
put(riser(1.9, 80, 600, .25), T['dive0']); put(boom(2.4, .5), 37.9)

# ---------------- SFX synced to the animation ----------------
# approach
engine(0, 6.8, lambda t: 62 + 8 * np.sin(t * 2) if t < 4.7 else 62 - 22 * min(1, (t - 4.7) / .6), .13)
put(whoosh(1.4, 300, 900, .22), 2.6)
put(thud(.45, 180, 45, .9), T['contact1']); put(clang(1.0, 740, .55), T['contact1']); put(crack(.3, .6), T['contact1'] + .02)
put(crack(.35, 1.1), T['snap']); put(clang(1.2, 1180, .5), T['snap'] + .01); put(whoosh(.7, 2500, 500, .3), T['snap'])
put(whoosh(.9, 600, 2200, .5), T['rip']); put(crack(.15, .4), T['rip'])
for tb, g, f in [(6.0, .35, 1400), (6.45, .26, 1900), (6.85, .18, 2300)]: put(clang(.5, f, g), tb)
put(whoosh(.8, 500, 3000, .6), T['flyPast'] - .3)
# green / unbreakable
engine(7.0, 12.4, lambda t: 64, .12); put(shimmer(.9, 500, 2600, .8), T['unb'] - .6); put(ping(1318, .8, .5), T['unb']); put(thud(.6, 110, 40, .9), T['unb']); put(whoosh(.5, 3000, 600, .3), T['unb'])
put(thud(.5, 150, 40, .9), T['grip']); put(shimmer(.7, 800, 2800, .6), T['grip'] - .3); put(ping(1760, .7, .4), T['grip'] + .05)
put(boom(1.8, .6), T['body']); put(shimmer(1.0, 400, 1800, .7), T['body'] - .4)
# force transfer
engine(12.4, 15.4, lambda t: 64 - 24 * min(1, max(0, (t - 12.4) / 1.0)), .12)
for k in range(10): put(ping(520 + 70 * k, .4, .4), T['ripple0'] + k * .2)
put(riser(1.9, 120, 900, .22), T['impact2'] - 1.9)
put(thud(.8, 170, 36, 1.3), T['impact2']); put(clang(1.4, 480, .9), T['impact2']); put(crack(.3, .8), T['impact2'])
put(screech(1.3, .9), T['impact2'] + .1); put(whoosh(1.2, 2200, 300, .35), T['impact2'] + .1)
put(thud(.7, 120, 30, 1.0), T['halt']); put(fil(noise(1.2), 3000, None) * np.exp(-tt(1.2) * 2.5) * .3, T['halt'] - .1)
# pushing
put(whoosh(.7, 400, 1800, .4), T['push']); engine(T['push'], T['lunge'] + .6, lambda t: 70 + 55 * min(1, (t - T['push']) / 2.5) + 6 * np.sin(t * 40), .2)
put(screech(3.0, .35), T['push'] + .2); put(fil(noise(3), 2500, None) * .12 * np.minimum(1, tt(3) / .3), T['push'])
put(thud(.5, 110, 40, .8), T['lunge']); put(whoosh(.6, 300, 1600, .35), T['lunge'] - .1)
# cutting the tree
saw = fil(noise(.9), 700, 4500) * (.6 + .4 * np.sin(tt(.9) * 2 * np.pi * 38)); put(saw * .55, T['lunge'] + .3)
put(crack(.4, 1.1), 21.92); put(crack(.35, .7), 22.1); put(whoosh(.9, 250, 900, .3), 22.2)
t = tt(.9); put((np.sin(2 * np.pi * (180 + 70 * t / .9) * t) * .5 * (1 + np.sin(60 * t)) ) * np.sin(np.pi * t / .9) * .18, 22.1)
put(thud(.9, 100, 28, 1.4), T['crash']); put(boom(1.6, .45), T['crash']); put(fil(noise(1.6), None, 1500) * np.exp(-tt(1.6) * 2.5) * .8, T['crash'])
# indestructible tree + energy build
put(shimmer(1.0, 500, 2600, .8), T['greenBand'] - .3); put(ping(1568, .8, .5), T['greenBand'] + .2)
engine(24, T['boom'] - .25, lambda t: 70 + 50 * ((t - 24) / 7.4) ** 1.3 + 4 * np.sin(t * 45), .2)
t = 26.3
k = 0
while t < T['boom'] - .25:
    put(thud(.3, 90, 40, .55), t); put(thud(.25, 80, 38, .35), t + .13); t += .62 - .5 * ((t - 26.3) / 5.1) ** 1.2; k += 1
for kk in range(26): put(ping(500 + kk * 45, .3, .22 + kk * .01), 26.4 + kk * 0.19 * (1 - kk / 70))
# duck the whole mix right before the boom (classic silence-before-the-hit)
d0, d1 = int((T['boom'] - .3) * SR), int(T['boom'] * SR); L[d0:d1] *= np.linspace(1, .08, d1 - d0); Rr[d0:d1] *= np.linspace(1, .08, d1 - d0)
# final fade out
f0 = int(T['fadeOut'] * SR); fade = np.linspace(1, 0, N - f0); L[f0:] *= fade; Rr[f0:] *= fade
# ---------------- master: peak -1.5 dB (final loudness set with ffmpeg loudnorm) ----------------
out = np.stack([L, Rr]); out = np.tanh(out * .9) / np.tanh(.9)
out *= 10 ** (-1.5 / 20) / np.abs(out).max()
with wave.open('sword_raw.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out.T * 32767).astype('<i2').tobytes())
print('audio ok', N / SR)
