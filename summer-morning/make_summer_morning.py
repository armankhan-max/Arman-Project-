#!/usr/bin/env python3
"""
1970s Summer Morning Outside - 10 minute calming ambience (fully synthesized).

Layers:
  * pre-dawn crickets that fade out as the sun comes up
  * soft breeze, rustling leaves, distant stream
  * dawn chorus that slowly builds: mourning dove, cuckoo, flute-thrush,
    robin, sparrows, warbler
  * warm evolving analog-style pad (the "sunrise" swell)
  * sparse, slow 70s Rhodes-style electric piano with auto-pan
  * distant wind chimes
Output: WAV -> MP3 via ffmpeg.
"""
import subprocess
import sys
import wave
import numpy as np
from scipy import signal

SR = 44100
DUR = 600  # seconds (10 minutes)
N = SR * DUR
rng = np.random.default_rng(1970)


# ---------------------------------------------------------------- helpers
def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def lp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def pink(seed):
    r = np.random.default_rng(seed)
    w = r.standard_normal(N)
    W = np.fft.rfft(w)
    f = np.fft.rfftfreq(N, 1 / SR)
    f[0] = f[1]
    W /= np.sqrt(f)
    x = np.fft.irfft(W, N)
    return (x / np.std(x)).astype(np.float64)


def slow(period, seed, lo=0.0, hi=1.0):
    """Smooth random control signal, one new random target every `period` s."""
    r = np.random.default_rng(seed)
    n = int(DUR / period) + 3
    pts = r.random(n)
    x = np.arange(N) / SR / period
    idx = np.minimum(x.astype(int), n - 2)
    f = (1 - np.cos(np.pi * (x - idx))) / 2
    v = pts[idx] * (1 - f) + pts[idx + 1] * f
    return lo + (hi - lo) * v


TIME = None  # lazily built


def tarr():
    global TIME
    if TIME is None:
        TIME = np.arange(N) / SR
    return TIME


def pan_gains(p):
    th = p * np.pi / 2
    return np.cos(th), np.sin(th)


def add(bus, sig, t0, p=0.5, gain=1.0):
    i = int(t0 * SR)
    if i >= N:
        return
    n = min(len(sig), N - i)
    l, r = pan_gains(p)
    bus[0, i:i + n] += sig[:n] * gain * l
    bus[1, i:i + n] += sig[:n] * gain * r


# ------------------------------------------------------------- bird voices
def note(f0, f1, dur, harm=(1.0, 0.2), vib=(0, 0), curve=1.0, env_pow=1.4, fm=(0, 0)):
    n = max(int(dur * SR), 8)
    t = np.arange(n) / SR
    u = t / dur
    f = f0 + (f1 - f0) * u ** curve
    if vib[0]:
        f = f * (1 + vib[1] * np.sin(2 * np.pi * vib[0] * t))
    if fm[0]:
        f = f * (1 + fm[1] * np.sin(2 * np.pi * fm[0] * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum(a * np.sin(k * ph) for k, a in enumerate(harm, 1))
    env = np.sin(np.pi * u) ** env_pow
    return s * env


def seq(parts, gaps):
    out = []
    for p, g in zip(parts, gaps):
        out.append(p)
        out.append(np.zeros(int(g * SR)))
    return np.concatenate(out)


def bird_dove(r):
    base = r.uniform(380, 470)
    a = note(base * 0.95, base * 1.12, 0.22, harm=(1, 0.12), env_pow=1.0)
    b = note(base * 1.1, base * 0.97, 0.75, harm=(1, 0.15), vib=(5, 0.01), env_pow=0.8)
    s1 = seq([a, b, b, b][: r.integers(3, 5)], [0.1, 0.18, 0.18, 0.3])
    return s1 * 0.9


def bird_cuckoo(r):
    f1 = r.uniform(640, 760)
    f2 = f1 * 0.79
    parts, gaps = [], []
    for _ in range(r.integers(3, 7)):
        parts += [note(f1, f1 * 0.98, 0.2, harm=(1, 0.1), env_pow=0.9),
                  note(f2, f2 * 0.99, 0.32, harm=(1, 0.08), env_pow=0.9)]
        gaps += [0.04, 0.85]
    return seq(parts, gaps) * 0.8


def bird_thrush(r):
    """slow, fluty, liquid phrases"""
    parts, gaps = [], []
    base = r.uniform(1800, 2600)
    for _ in range(r.integers(3, 6)):
        f0 = base * r.uniform(0.8, 1.5)
        f1 = f0 * r.uniform(0.7, 1.4)
        parts.append(note(f0, f1, r.uniform(0.15, 0.35), harm=(1, 0.18, 0.05),
                          vib=(r.uniform(18, 30), 0.012), env_pow=1.0))
        gaps.append(r.uniform(0.08, 0.35))
    return seq(parts, gaps) * 0.55


def bird_robin(r):
    parts, gaps = [], []
    for _ in range(r.integers(5, 10)):
        f0 = r.uniform(2600, 5200)
        f1 = f0 * r.choice([0.6, 0.75, 1.3, 1.6])
        parts.append(note(f0, f1, r.uniform(0.05, 0.14), harm=(1, 0.25, 0.06),
                          fm=(r.uniform(40, 90), 0.02), env_pow=1.2))
        gaps.append(r.uniform(0.03, 0.14))
    gaps[-1] = 0
    return seq(parts, gaps) * 0.4


def bird_sparrow(r):
    parts, gaps = [], []
    base = r.uniform(3200, 4200)
    for _ in range(r.integers(3, 9)):
        parts.append(note(base, base * r.uniform(1.15, 1.45), r.uniform(0.04, 0.07),
                          harm=(1, 0.3), env_pow=0.9))
        gaps.append(r.uniform(0.12, 0.3))
    return seq(parts, gaps) * 0.35


def bird_warbler(r):
    parts, gaps = [], []
    lo, hi = r.uniform(3200, 3900), r.uniform(4400, 5400)
    for k in range(r.integers(14, 30)):
        if k % 2 == 0:
            parts.append(note(lo, hi, 0.035, harm=(1, 0.2), env_pow=1.0))
        else:
            parts.append(note(hi, lo, 0.035, harm=(1, 0.2), env_pow=1.0))
        gaps.append(0.012)
    # swell envelope over the whole trill
    sig = seq(parts, gaps)
    sig *= np.sin(np.linspace(0.15, np.pi - 0.15, len(sig))) ** 0.8
    return sig * 0.3


SPECIES = [
    ("dove", bird_dove), ("cuckoo", bird_cuckoo), ("thrush", bird_thrush),
    ("robin", bird_robin), ("sparrow", bird_sparrow), ("warbler", bird_warbler),
]


def weights(d):
    return np.array([0.9, 0.45, 0.7, 0.15 + 1.3 * d, 0.1 + 1.1 * d, 0.1 + 0.9 * d])


# ------------------------------------------------------------- reverb
def make_ir(rt60=2.6, seed=7):
    r = np.random.default_rng(seed)
    n = int(rt60 * SR)
    t = np.arange(n) / SR
    ir = np.zeros((2, n))
    for c in range(2):
        x = r.standard_normal(n) * np.exp(-6.9 * t / rt60)
        x = lp(x, 5500)
        x[: int(0.02 * SR)] = 0  # pre-delay
        ir[c] = x
    ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
    return ir


def reverb(send, ir):
    out = np.zeros_like(send)
    for c in range(2):
        out[c] = signal.oaconvolve(send[c], ir[c])[:N]
    return out


# ------------------------------------------------------------- music
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def mf(name, octave):
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octave - 4) - 9) / 12)


CHORDS = [
    [("C", 3), ("G", 3), ("B", 3), ("D", 4), ("E", 4)],   # Cmaj9
    [("F", 3), ("A", 3), ("C", 4), ("E", 4), ("G", 4)],   # Fmaj9
    [("A", 2), ("E", 3), ("G", 3), ("B", 3), ("C", 4)],   # Am9
    [("F", 3), ("A", 3), ("C", 4), ("E", 4), ("D", 4)],   # Fmaj9 (add 13)
    [("G", 2), ("D", 3), ("G", 3), ("B", 3), ("E", 4)],   # G6
]
SEG = 30  # seconds per chord
XF = 8    # crossfade


def build_pad():
    pad = np.zeros((2, N), dtype=np.float32)
    nseg = DUR // SEG + 1
    for i in range(nseg):
        chord = CHORDS[i % len(CHORDS)]
        start = i * SEG - XF
        a = max(start, 0)
        b = min((i + 1) * SEG + XF, DUR)
        if b <= a:
            continue
        n = (b - a) * SR
        t = np.arange(n) / SR
        env = np.ones(n)
        fi = int(XF * SR)
        if start >= 0:
            env[:fi] = np.sin(np.linspace(0, np.pi / 2, fi)) ** 2
        if (i + 1) * SEG + XF <= DUR:
            env[-fi:] = np.cos(np.linspace(0, np.pi / 2, fi)) ** 2
        seg = np.zeros((2, n))
        for k, (nm, oc) in enumerate(chord):
            f = mf(nm, oc)
            for v, (det, p) in enumerate([(-0.0018, 0.2), (0.0, 0.5), (0.0018, 0.8)]):
                ff = f * (1 + det)
                ph = 2 * np.pi * ff * t + rng.uniform(0, 6.28)
                s = np.sin(ph) + 0.28 * np.sin(2 * ph) + 0.09 * np.sin(3 * ph)
                s *= 0.7 + 0.3 * np.sin(2 * np.pi * rng.uniform(0.04, 0.1) * t + rng.uniform(0, 6))
                l, r_ = pan_gains(p)
                seg[0] += s * l
                seg[1] += s * r_
        pad[:, a * SR:b * SR] += (seg * env * 0.018).astype(np.float32)
    # sunrise swell: pad slowly grows
    g = 0.3 + 0.7 * smooth(tarr() / 480.0)
    pad *= g.astype(np.float32)
    return pad


def rhodes_note(f, dur=5.0, vel=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    decay = 2.2 if f < 500 else 1.4
    env = np.exp(-t / decay) * (1 - np.exp(-t / 0.006))
    idx = vel * 1.6 * np.exp(-t / 0.5) + 0.12
    s = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t))
    tine = 0.07 * vel * np.sin(2 * np.pi * f * 7 * t) * np.exp(-t / 0.09)
    s = (s + tine) * env
    s += 0.25 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t / (decay * 0.5)) * env
    return s


def chime_note(f, dur=5.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t / 2.2)
         + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 1.1)
         + 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / 0.5))
    return s * (1 - np.exp(-t / 0.002))


# ------------------------------------------------------------- build
def main(out_mp3):
    print("beds...", flush=True)
    t = tarr()
    dry = np.zeros((2, N), dtype=np.float32)
    send = np.zeros((2, N), dtype=np.float32)

    # breeze
    for c in range(2):
        b = lp(pink(100 + c), 650)
        b *= (0.35 + 0.65 * slow(11, 200 + c)) * 0.16
        dry[c] += b.astype(np.float32)
        # higher airy gusts
        g = bp(pink(110 + c), 900, 2600) * (slow(17, 210 + c) ** 3) * 0.06
        dry[c] += g.astype(np.float32)

    # leaves rustle
    for c in range(2):
        w = np.random.default_rng(300 + c).standard_normal(N)
        w = bp(w, 2500, 7500) * (slow(5, 310 + c) ** 3) * 0.018
        dry[c] += w.astype(np.float32)

    # distant stream (left-ish)
    w = np.random.default_rng(400).standard_normal(N)
    s = bp(w, 500, 2400)
    mod = 0.65 + 0.35 * lp(np.random.default_rng(401).standard_normal(N), 25) * 8
    s = s * np.clip(mod, 0.2, 1.4) * 0.02
    dry[0] += (s * 1.0).astype(np.float32)
    dry[1] += (s * 0.4).astype(np.float32)

    # pre-dawn crickets
    print("crickets...", flush=True)
    cn = 280 * SR
    ct = np.arange(cn) / SR
    fade = 1 - smooth(ct / 270.0)
    for c, (fc, rate, grp) in enumerate([(4350, 41.0, 1.55), (4680, 38.0, 1.3)]):
        pulses = np.clip(np.sin(2 * np.pi * rate * ct) * 3, 0, 1)
        groups = np.clip(np.sin(2 * np.pi * grp * ct + c) * 4 - 1.5, 0, 1)
        amp = (0.5 + 0.5 * slow(7, 500 + c)[:cn])
        cr = np.sin(2 * np.pi * fc * ct) * pulses * lp(groups, 40) * amp * fade * 0.010
        dry[c, :cn] += cr.astype(np.float32)
        send[c, :cn] += (cr * 0.5).astype(np.float32)

    # birds
    print("birds...", flush=True)
    r = np.random.default_rng(1977)
    tt = 2.0
    nb = 0
    while tt < DUR - 6:
        d = 0.12 + 0.88 * smooth((tt - 20) / 360.0)
        w = weights(d)
        k = r.choice(len(SPECIES), p=w / w.sum())
        sig = SPECIES[k][1](r)
        dist = r.uniform(0.2, 1.0)
        # far birds are duller
        if dist < 0.5:
            sig = lp(sig, 3500)
        p = r.uniform(0.08, 0.92)
        add(dry, sig, tt, p, 0.9 * dist)
        add(send, sig, tt, p, 0.55 * (1.3 - dist))
        # occasional answering bird
        if r.random() < 0.35:
            k2 = r.choice(len(SPECIES), p=w / w.sum())
            sig2 = SPECIES[k2][1](r)
            t2 = tt + len(sig) / SR * r.uniform(0.6, 1.1) + r.uniform(0.3, 1.5)
            p2 = r.uniform(0.08, 0.92)
            d2 = r.uniform(0.2, 0.9)
            if t2 < DUR - 6:
                add(dry, sig2, t2, p2, 0.9 * d2)
                add(send, sig2, t2, p2, 0.55 * (1.3 - d2))
        tt += r.exponential(13.0 - 10.0 * d) + 1.0
        nb += 1
    print(f"  {nb} bird bouts", flush=True)

    # pad
    print("pad...", flush=True)
    pad = build_pad()
    dry += pad * 0.9
    send += pad * 0.45

    # rhodes
    print("rhodes...", flush=True)
    rh = np.zeros((2, N), dtype=np.float32)
    r2 = np.random.default_rng(1971)
    tt = 25.0
    while tt < DUR - 8:
        seg = int(tt // SEG)
        chord = CHORDS[seg % len(CHORDS)]
        pool = [mf(n_, o_ + (1 if r2.random() < 0.7 else 0)) for n_, o_ in chord]
        pool += [mf("G", 4), mf("E", 5), mf("D", 5)]
        f = r2.choice(pool)
        vel = r2.uniform(0.3, 0.6)
        sig = rhodes_note(f, 5.0, vel) * 0.07
        add(rh, sig, tt, r2.uniform(0.35, 0.65), 1.0)
        if r2.random() < 0.3:  # soft second note, like a gentle dyad
            f2 = r2.choice(pool)
            add(rh, rhodes_note(f2, 5.0, vel * 0.8) * 0.06, tt + r2.uniform(0.25, 0.6), 0.5, 1.0)
        tt += r2.uniform(3.5, 7.5)
    # tremolo auto-pan (Suitcase-Rhodes style)
    lfo = 0.5 * np.sin(2 * np.pi * 0.28 * t)
    rh[0] *= (1 + 0.3 * lfo).astype(np.float32)
    rh[1] *= (1 - 0.3 * lfo).astype(np.float32)
    rh *= (0.5 + 0.5 * smooth((t - 10) / 120.0)).astype(np.float32)
    dry += rh
    send += rh * 0.6

    # wind chimes, more present in the second half
    print("chimes...", flush=True)
    r3 = np.random.default_rng(1973)
    scale = [mf("C", 6), mf("D", 6), mf("E", 6), mf("G", 6), mf("A", 6), mf("C", 7)]
    tt = 150.0
    while tt < DUR - 8:
        cnt = r3.integers(2, 6)
        tc = tt
        for _ in range(cnt):
            add(dry, chime_note(r3.choice(scale), 4.5) * 0.012, tc, r3.uniform(0.15, 0.85), 1.0)
            add(send, chime_note(r3.choice(scale), 4.5) * 0.012, tc, r3.uniform(0.15, 0.85), 1.0)
            tc += r3.uniform(0.1, 0.5)
        tt += r3.uniform(20, 55)

    # "sunrise" airy shimmer swell centred around 4:30
    sw = bp(pink(900), 1200, 5000)
    swell = np.exp(-((t - 270) / 55.0) ** 2) * 0.020
    sw2 = bp(pink(901), 1200, 5000)
    dry[0] += (sw * swell).astype(np.float32)
    dry[1] += (sw2 * swell).astype(np.float32)

    print("reverb...", flush=True)
    wet = reverb(send, make_ir())
    mix = dry + wet * 0.8

    # master: gentle warmth + soft clip + fades
    print("master...", flush=True)
    for c in range(2):
        mix[c] = lp(mix[c].astype(np.float64), 13500, 2).astype(np.float32)
        mix[c] = hp(mix[c].astype(np.float64), 30, 2).astype(np.float32)
    mix = np.tanh(mix * 1.6) / 1.6
    fi, fo = 6 * SR, 14 * SR
    mix[:, :fi] *= np.linspace(0, 1, fi) ** 2
    mix[:, -fo:] *= np.linspace(1, 0, fo) ** 2
    mix *= 0.8 / np.abs(mix).max()

    wav_path = out_mp3.replace(".mp3", ".wav")
    pcm = (mix.T * 32767).astype(np.int16)
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())

    # per-minute RMS report
    for m in range(10):
        seg = mix[:, m * 60 * SR:(m + 1) * 60 * SR]
        print(f"  min {m}: rms {20*np.log10(np.sqrt((seg**2).mean())):.1f} dBFS", flush=True)

    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", wav_path,
        "-c:a", "libmp3lame", "-b:a", "192k",
        "-metadata", "title=1970s Summer Morning Outside",
        "-metadata", "artist=Calm Ambience",
        "-metadata", "genre=Ambient / Nature",
        out_mp3,
    ], check=True)
    import os
    os.remove(wav_path)
    print("done:", out_mp3)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "1970s_Summer_Morning.mp3")
