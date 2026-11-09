"""Music + SFX, all synthesized with numpy, mixed under the voice.

Music: low drone + koto-like Karplus-Strong plucks in the Japanese "In" scale
+ soft taiko pulse. SFX are placed on the cue times collected from the scenes
(build/events.json): cut whoosh, kicker pop, stamp thud, impact, X buzz,
counter ticks, title taiko+gong. The music ducks under the voice."""
import json, math, os
import numpy as np, soundfile as sf

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(3)


def load_voice():
    v, sr = sf.read(os.path.join(HERE, "build", "voice.wav"), dtype="float32")
    n = int(len(v) * SR / sr)
    return np.interp(np.linspace(0, len(v) - 1, n), np.arange(len(v)), v).astype(np.float32)


def env(n, a=0.005, r=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)


def lowpass(x, k):
    """one-pole lowpass, k in (0,1): smaller = darker"""
    y = np.zeros_like(x); s = 0.0
    for i in range(len(x)):
        s += k * (x[i] - s); y[i] = s
    return y


def lp_fast(x, cutoff):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x)).astype(np.float32)


def pluck(freq, dur=2.5, bright=0.5):
    n = int(SR * dur); N = int(SR / freq)
    buf = rng.uniform(-1, 1, N).astype(np.float32)
    buf = lp_fast(np.tile(buf, 4), 2000 + 6000 * bright)[:N]
    out = np.zeros(n, np.float32)
    for i in range(n):
        j = i % N
        out[i] = buf[j]
        buf[j] = 0.996 * 0.5 * (buf[j] + buf[(j + 1) % N])
    return out * env(n, 0.002, dur * 0.4)


def taiko(dur=1.2, f=62):
    n = int(SR * dur); t = np.arange(n) / SR
    pitch = f * (1 + 0.6 * np.exp(-t * 18))
    body = np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-t * 4.5)
    slap = lp_fast(rng.normal(0, 1, n).astype(np.float32), 900) * np.exp(-t * 40) * 0.6
    return (body + slap).astype(np.float32)


def gong(dur=4.0):
    n = int(SR * dur); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t + p) * a for f, a, p in [(110, 1, 0), (163.7, .6, 1), (231, .5, 2), (297, .35, .3), (415, .2, 1.4)])
    return (x * np.exp(-t * 1.1) * np.minimum(1, t / 0.02) * 0.4).astype(np.float32)


def whoosh(dur=0.45, up=True):
    n = int(SR * dur); t = np.linspace(0, 1, n)
    x = rng.normal(0, 1, n).astype(np.float32)
    e = np.sin(np.pi * t) ** 2
    # sweep a bandpass by mixing two lowpasses
    lo = lp_fast(x, 600); hi = lp_fast(x, 3500)
    mix = (t if up else 1 - t)
    return ((lo * (1 - mix) + hi * mix) * e * 0.5).astype(np.float32)


def thud(f=80, dur=0.4):
    n = int(SR * dur); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t * (1 + np.exp(-t * 30))) * np.exp(-t * 12)).astype(np.float32)


def crack(dur=0.25):
    n = int(SR * dur); t = np.arange(n) / SR
    x = rng.normal(0, 1, n).astype(np.float32) * np.exp(-t * 35)
    clicks = np.zeros(n, np.float32)
    for k in range(6):
        i = int(rng.uniform(0, 0.06) * SR); clicks[i:i + 60] += rng.uniform(0.5, 1)
    return (x * 0.6 + lp_fast(clicks, 5000) * 3).astype(np.float32)


def tick(f=1800, dur=0.05):
    n = int(SR * dur); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) * np.exp(-t * 90)).astype(np.float32)


def buzz(dur=0.3):
    n = int(SR * dur); t = np.arange(n) / SR
    return (np.sign(np.sin(2 * np.pi * 110 * t)) * 0.3 * np.exp(-t * 8)).astype(np.float32)


def add(buf, x, t, g):
    i = int(t * SR)
    if i >= len(buf): return
    x = x[: len(buf) - i]
    buf[i:i + len(x)] += x * g


def music(n):
    out = np.zeros(n, np.float32); t = np.arange(n) / SR
    # drone on D with slow swell
    for f, a in [(73.4, 0.5), (110, 0.25), (146.8, 0.12)]:
        out += (np.sin(2 * np.pi * f * t) * a * (0.6 + 0.4 * np.sin(2 * np.pi * t / 23 + f))).astype(np.float32)
    out = lp_fast(out, 400) * 0.35
    # koto phrases, In scale on D: D Eb G A Bb
    scale = [293.7, 311.1, 392.0, 440.0, 466.2, 587.3, 622.3, 784.0]
    cache = {}
    tt = 2.0
    while tt < n / SR - 3:
        phrase = rng.integers(2, 5)
        base = rng.integers(0, 4)
        for k in range(phrase):
            idx = int(np.clip(base + rng.integers(-1, 3), 0, len(scale) - 1))
            if idx not in cache: cache[idx] = pluck(scale[idx], 2.6, 0.4)
            add(out, cache[idx], tt, 0.16)
            tt += float(rng.choice([0.35, 0.5, 0.7]))
        tt += float(rng.uniform(2.5, 5.0))
    # soft taiko heartbeat every 2 bars (70 bpm)
    tk = taiko(1.0, 55); beat = 60 / 70
    tt = 4.0
    while tt < n / SR - 2:
        add(out, tk, tt, 0.22); add(out, tk, tt + beat * 0.5, 0.12)
        tt += beat * 8
    return out


def main():
    voice = load_voice(); n = len(voice)
    mus = music(n)
    # duck under voice
    e = np.abs(voice); win = int(SR * 0.3)
    cs = np.concatenate([[0], np.cumsum(e, dtype=np.float64)])
    idx = np.arange(n); lo = np.clip(idx - win // 2, 0, n); hi = np.clip(idx + win // 2, 0, n)
    e = ((cs[hi] - cs[lo]) / np.maximum(hi - lo, 1)).astype(np.float32)
    duck = 1 - 0.55 * np.clip(e / 0.03, 0, 1)
    mus *= duck.astype(np.float32)
    sfx = np.zeros(n, np.float32)
    W_IN, W_OUT, TK, TH, CR, BZ, G = whoosh(0.4, True), whoosh(0.5, False), tick(), thud(), crack(), buzz(), gong()
    TA = taiko(1.4, 50)
    evs = json.load(open(os.path.join(HERE, "build", "events.json")))
    last = {}
    for kind, t in evs:
        if t - last.get(kind, -9) < 0.25: continue
        last[kind] = t
        if kind == "cut": add(sfx, W_IN, max(0, t - 0.25), 0.18)
        elif kind == "title": add(sfx, TA, t, 0.7); add(sfx, G, t + 0.05, 0.35); add(sfx, W_OUT, max(0, t - 0.3), 0.25)
        elif kind == "kick": add(sfx, W_OUT, max(0, t - 0.05), 0.14); add(sfx, TH, t, 0.12)
        elif kind == "stamp": add(sfx, TH, t + 0.15, 0.5); add(sfx, CR, t + 0.15, 0.08)
        elif kind == "impact": add(sfx, TH, t, 0.55); add(sfx, CR, t, 0.25)
        elif kind == "x": add(sfx, BZ, t, 0.18)
        elif kind == "tick": add(sfx, TK, t, 0.2)
        elif kind == "count":
            for k in range(8): add(sfx, TK, t + k * 0.09, 0.08)
    mix = voice * 1.0 + mus * 0.55 + sfx * 0.8
    # end: let music swell after voice
    peak = np.abs(mix).max()
    mix = np.tanh(mix / peak * 1.1) * 0.92
    sf.write(os.path.join(HERE, "build", "mix.wav"), np.stack([mix, mix], 1), SR, subtype="PCM_16")
    print("mix ok", n / SR)


if __name__ == "__main__":
    main()
