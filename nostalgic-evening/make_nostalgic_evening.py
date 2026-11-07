#!/usr/bin/env python3
"""
Nostalgic Evening - 10 min sleep ambience: crickets, birds, children playing
far away, sun fading, with an ORIGINAL slow nostalgic music bed.

WHY THE REFERENCE VIDEO FEELS NOSTALGIC (measured with FFT/autocorrelation):
  1. One short loop (~10.1 s) repeats unchanged for 2 minutes -> memory-like, static.
  2. Nothing above ~4 kHz, centroid ~700 Hz -> old cassette / TV / distance.
  3. Constant, very quiet level (-24 dBFS RMS), no dynamics -> background, not event.
  4. Pitch centre G with F#/B/A# -> major-7th colour with a major/minor third
     ambiguity = bittersweet.
  5. Dense soft plucked onsets every ~0.2-0.35 s smeared by reverb.
We do NOT copy its notes. We reuse the *reasons*, each as its own nostalgic
device, switched on in different sections:
  S1 (0-96s)    music-box + band-limit (3.8 kHz) + tape wow/flutter
  S2 (96-208s)  + warm detuned pad, Rhodes arpeggio, vinyl crackle/tape hiss (old recording)
  S3 (208-336s) borrowed minor-iv chord (Bbm6): the bittersweet "memory" chord
  S4 (336-480s) echo/ghost notes, octave sparkles, tape slows down (memory fading)
  S5 (480-600s) only a few lonely notes; music dissolves into crickets
"""
import os, sys, subprocess, wave
import numpy as np
from scipy import signal
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "summer-morning"))
from make_summer_morning import (SR, DUR, N, smooth, lp, hp, bp, pink, slow, tarr, add,
                                 SPECIES, weights, make_ir, reverb, rhodes_note)

T = tarr()


def n2f(s):
    semi = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    acc, i = 0, 1
    if s[1] in "b#":
        acc = -1 if s[1] == "b" else 1
        i = 2
    return 440 * 2 ** ((semi[s[0]] + acc + 12 * (int(s[i:]) - 4) - 9) / 12)


def ienv(pts, vals):
    return np.interp(T, pts, vals)


# ------------------------------------------------------------ children
VOW = {"a": (1000, 2900), "e": (700, 3100), "i": (450, 3300), "o": (600, 1100)}


def voice(f_contour, vowel, noise=0.12, rng=None):
    n = len(f_contour)
    ph = 2 * np.pi * np.cumsum(f_contour) / SR
    kmax = max(2, int(4500 / f_contour.max()))
    src = sum(np.sin(k * ph) / k for k in range(1, kmax + 1))
    src += noise * np.random.default_rng(int(f_contour[0])).standard_normal(n)
    f1, f2 = VOW[vowel]
    out = bp(src, f1 * 0.8, f1 * 1.25) + 0.55 * bp(src, f2 * 0.85, f2 * 1.2)
    return out


def contour(f0, f1, n, wob=0.015, r=None):
    f = np.linspace(f0, f1, n)
    t = np.arange(n) / SR
    return f * (1 + wob * np.sin(2 * np.pi * r.uniform(4, 7) * t))


def child_laugh(r):
    parts = []
    f0 = r.uniform(380, 520)
    for k in range(r.integers(3, 7)):
        n = int(r.uniform(0.08, 0.12) * SR)
        v = voice(contour(f0, f0 * 0.92, n, r=r), "a")
        v *= np.sin(np.pi * np.arange(n) / n) ** 0.8 * (0.85 ** k)
        parts += [v, np.zeros(int(0.07 * SR))]
        f0 *= 0.95
    return np.concatenate(parts)


def child_shout(r):
    n = int(r.uniform(0.35, 0.8) * SR)
    f0 = r.uniform(330, 450)
    u = np.linspace(0, 1, n)
    f = np.interp(u, [0, 0.3, 1], [f0, f0 * 1.35, f0 * 1.05]) * (1 + 0.012 * np.sin(2 * np.pi * 6 * u * n / SR))
    v = voice(f, r.choice(["a", "e", "o"]))
    return v * np.sin(np.pi * u) ** 0.7


def child_chatter(r):
    parts = []
    for _ in range(r.integers(4, 9)):
        n = int(r.uniform(0.07, 0.16) * SR)
        f0 = r.uniform(300, 450)
        v = voice(contour(f0, f0 * r.uniform(0.85, 1.2), n, r=r), r.choice(list(VOW)))
        parts += [v * np.sin(np.pi * np.arange(n) / n), np.zeros(int(r.uniform(0.03, 0.1) * SR))]
    return np.concatenate(parts) * 0.8


KIDS = [child_laugh, child_shout, child_chatter]


def ball(r):
    out = np.zeros(int(3 * SR))
    gap, amp, p = 0.5, 1.0, 0
    while gap > 0.08 and p < len(out) - 8000:
        n = int(0.12 * SR)
        t = np.arange(n) / SR
        thud = np.sin(2 * np.pi * (60 + 90 * np.exp(-t / 0.02)) * t) * np.exp(-t / 0.04)
        out[p:p + n] += thud * amp
        p += int(gap * SR)
        gap *= 0.76
        amp *= 0.72
    return out


def bell(r):
    out = np.zeros(int(1.6 * SR))
    for s in (0, int(0.28 * SR)):
        n = int(1.0 * SR)
        t = np.arange(n) / SR
        b = (np.sin(2 * np.pi * 2350 * t) + 0.5 * np.sin(2 * np.pi * 2350 * 2.76 * t)) * np.exp(-t / 0.25)
        out[s:s + n] += b[: len(out) - s]
    return out


# ------------------------------------------------------------ music
def musicbox(f, dur=5.0):
    """soft, slightly detuned felt piano (out-of-tune = old/imperfect)"""
    f = f * 2 ** (np.random.uniform(-22, 22) / 1200)
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t / 2.6)
         + 0.35 * np.sin(2 * np.pi * f * 2.003 * t) * np.exp(-t / 1.2)
         + 0.12 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t / 0.6))
    s *= (1 - np.exp(-t / 0.012))
    return np.tanh(s * 1.6) / 1.6  # soft distortion


def pad_chord(freqs, dur=9.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = smooth(t / 3.0) * smooth((dur - t) / 3.0)
    out = np.zeros((2, n))
    for f in freqs:
        for det, pan in ((-0.002, 0.25), (0.002, 0.75)):
            ph = 2 * np.pi * f * (1 + det) * t
            s = np.sin(ph) + 0.25 * np.sin(2 * ph)
            th = pan * np.pi / 2
            out[0] += s * np.cos(th)
            out[1] += s * np.sin(th)
    return out * env


CH = {
    "Fmaj7": ["F3", "C4", "E4", "A4"], "Am7": ["A2", "E3", "G3", "C4"],
    "Bbmaj7": ["Bb2", "F3", "A3", "D4"], "C69": ["C3", "G3", "A3", "D4", "E4"],
    "Dm7": ["D3", "A3", "C4", "F4"], "Bbm6": ["Bb2", "F3", "G3", "Db4"],
}
PROG_A = ["Fmaj7", "Am7", "Bbmaj7", "C69"]
PROG_B = ["Fmaj7", "Dm7", "Bbmaj7", "Bbm6"]  # minor iv = bittersweet
# simple, repeating, hanging melody: never resolves to the tonic (something is missing)
PH_A = [(0, "A4"), (2, "C5"), (4, "F5"), (8, "E5"), (10, "C5"), (12, "D5"), (14, "G5")]
PH_B = [(0, "A4"), (2, "C5"), (4, "F5"), (8, "F5"), (10, "D5"), (12, "Db5"), (14, "Bb4")]
PH_S5 = [(0, "A5"), (8, "F5"), (14, "C6")]
BEAT = 1.5  # slow: 40 bpm


def build_music():
    r = np.random.default_rng(1982)
    mus = np.zeros((2, N), np.float32)
    snd = np.zeros((2, N), np.float32)
    LOOP = int(16 * BEAT)
    for i in range(int(DUR / LOOP) + 1):
        t0 = i * LOOP
        sec = 1 if t0 < 96 else 2 if t0 < 208 else 3 if t0 < 336 else 4 if t0 < 480 else 5
        prog = PROG_A if sec <= 2 else PROG_B
        phrase = PH_A if sec <= 2 else PH_B if sec <= 4 else PH_S5
        for b, cname in enumerate(prog):
            tb = t0 + b * 4 * BEAT
            if tb >= DUR - 8:
                break
            freqs = [n2f(x) for x in CH[cname]]
            gp = np.interp(tb, [0, 90, 160, 440, 520, 600], [0, 0, 1, 1, .35, .1])
            if gp > 0.02:
                add(mus, pad_chord(freqs[:4]).T[0] * 0, tb, 0.5, 0)  # keep API simple (no-op)
                pc = pad_chord(freqs[:4])
                i0 = int(tb * SR)
                n = min(pc.shape[1], N - i0)
                mus[:, i0:i0 + n] += (pc[:, :n] * 0.012 * gp).astype(np.float32)
                snd[:, i0:i0 + n] += (pc[:, :n] * 0.006 * gp).astype(np.float32)
            gr = np.interp(tb, [0, 50, 110, 336, 480, 540, 600], [0, 0, .7, .8, .35, .15, 0])
            if gr > 0.03:
                order = [0, 2, 1]
                for k, bt in enumerate([0.0, 2.25, 3.75]):
                    f = freqs[order[k] % len(freqs)] * 2
                    sig = rhodes_note(f, 4.5, 0.35) * 0.045 * gr
                    ta = tb + bt + r.uniform(-0.03, 0.03)
                    add(mus, sig, ta, 0.4 + 0.2 * k / 2, 1.0)
                    add(snd, sig, ta, 0.5, 0.7)
        # melody
        for beat, nm in phrase:
            if sec == 5 and r.random() < 0.4:
                continue
            tm = t0 + beat * BEAT + r.uniform(-0.06, 0.06)
            if tm >= DUR - 8:
                continue
            f = n2f(nm)
            vel = r.uniform(0.7, 1.0)
            g = np.interp(tm, [0, 20, 480, 585, 600], [0.3, 1, 1, .25, 0])
            sig = musicbox(f) * 0.06 * vel * g
            p = 0.35 + 0.3 * (n2f(nm) / 1100)
            add(mus, sig, tm, p, 1.0)
            add(snd, sig, tm, p, 1.8)
            if sec == 4:  # memory echoes + octave sparkles
                add(mus, sig * 0.35, tm + 2.25, 0.75, 1.0)
                add(snd, sig * 0.35, tm + 2.25, 0.75, 1.3)
                add(snd, musicbox(f * 2, 3.0) * 0.05 * vel * g * 0.25, tm + 4.5, 0.3, 1.2)
    return mus, snd


def warp(x):
    """tape wow & flutter + slow drift (tape slows down late = memory fading)."""
    depth = 0.5 + 1.1 * smooth((T - 150) / 220)
    rate = 1 - 0.018 * smooth((T - 340) / 220)
    off = depth * (0.0035 / (2 * np.pi * 0.45) * np.sin(2 * np.pi * 0.45 * T)
                   + 0.0008 / (2 * np.pi * 7.0) * np.sin(2 * np.pi * 7.0 * T)) * SR
    pos = np.cumsum(rate) + off
    idx = np.arange(N)
    out = np.empty_like(x)
    for c in range(2):
        out[c] = np.interp(pos, idx, x[c])
    return out


def main(out_mp3):
    print("beds...", flush=True)
    dry = np.zeros((2, N), np.float32)
    snd = np.zeros((2, N), np.float32)
    for c in range(2):
        b = lp(pink(100 + c), 600) * (0.35 + 0.65 * slow(13, 200 + c)) * 0.10
        dry[c] += b.astype(np.float32)
        w = np.random.default_rng(300 + c).standard_normal(N)
        dry[c] += (bp(w, 2500, 7500) * slow(6, 310 + c) ** 3 * 0.010).astype(np.float32)

    print("crickets...", flush=True)
    g = (0.12 + 0.88 * smooth((T - 15) / 280)).astype(np.float32)
    for j, (fc, rate, grp, pan) in enumerate([(4350, 41.0, 1.55, 0.2), (4680, 38.0, 1.3, 0.5), (5050, 36.0, 1.05, 0.8)]):
        pulses = np.clip(np.sin(2 * np.pi * rate * T) * 3, 0, 1)
        groups = lp(np.clip(np.sin(2 * np.pi * grp * T + j) * 4 - 1.5, 0, 1), 40)
        amp = 0.5 + 0.5 * slow(7, 500 + j)
        cr = (np.sin(2 * np.pi * fc * T) * pulses * groups * amp * g * 0.012).astype(np.float32)
        th = pan * np.pi / 2
        dry[0] += cr * np.cos(th); dry[1] += cr * np.sin(th)
        snd[0] += cr * np.cos(th) * 0.4; snd[1] += cr * np.sin(th) * 0.4
        del pulses, groups, amp, cr

    print("birds (evening, thinning out)...", flush=True)
    r = np.random.default_rng(1983)
    tt = 2.0
    while tt < DUR - 30:
        d = 0.05 + 0.95 * (1 - smooth((tt - 40) / 360))
        w = weights(d)
        k = r.choice(len(SPECIES), p=w / w.sum())
        sig = SPECIES[k][1](r)
        dist = r.uniform(0.2, 1.0)
        if dist < 0.5:
            sig = lp(sig, 3500)
        p = r.uniform(0.08, 0.92)
        add(dry, sig, tt, p, 0.8 * dist)
        add(snd, sig, tt, p, 0.5 * (1.3 - dist))
        tt += r.exponential(13.0 - 10.0 * d) + 1.0

    print("children...", flush=True)
    r = np.random.default_rng(1984)
    tt, gp = 8.0, 0.5
    while tt < 470:
        k = float(smooth((tt - 10) / 60) * (1 - smooth((tt - 300) / 150)))
        if k < 0.05:
            tt += 5
            continue
        gp = float(np.clip(gp + r.normal(0, 0.12), 0.12, 0.88))
        for _ in range(r.choice([1, 1, 2, 3])):
            sig = KIDS[r.choice(3, p=[0.4, 0.2, 0.4])](r)
            sig = lp(sig, r.uniform(2300, 3400))
            sig /= (np.abs(sig).max() + 1e-9)
            dist = r.uniform(0.3, 1.0) * k
            tx = tt + r.uniform(0, 1.2)
            p = float(np.clip(gp + r.normal(0, 0.08), 0.05, 0.95))
            add(dry, sig, tx, p, 0.05 * dist)
            add(snd, sig, tx, p, 0.07 * dist)
        tt += r.exponential(4.2 / (0.3 + k))
    for tb in np.arange(25, 300, 38) + r.uniform(0, 10, 8):
        sig = lp(ball(r), 1100)
        add(dry, sig, tb, r.uniform(0.2, 0.8), 0.035); add(snd, sig, tb, 0.5, 0.05)
    for tb in (70, 150, 230):
        sig = lp(bell(r), 6000)
        add(dry, sig, tb + r.uniform(0, 8), r.uniform(0.2, 0.8), 0.012)
        add(snd, sig, tb, 0.5, 0.02)

    print("ambience reverb...", flush=True)
    amb = dry + reverb(snd, make_ir(2.4, 5)) * 0.8
    del dry, snd

    print("music...", flush=True)
    mus, msnd = build_music()
    music = mus + reverb(msnd, make_ir(6.0, 9)) * 1.7
    del mus, msnd
    for c in range(2):
        music[c] = lp(music[c].astype(np.float64), 3200, 2).astype(np.float32)  # reason #2: band-limited
    music = warp(music)                                                           # tape wow/flutter

    # old-recording texture: crackle + hiss (sections 2-4)
    rr = np.random.default_rng(77)
    old = np.zeros((2, N), np.float32)
    env_old = (smooth((T - 60) / 80) * (1 - smooth((T - 480) / 80))).astype(np.float32)
    for c in range(2):
        clicks = (rr.random(N) < 1.2e-4) * rr.exponential(1, N) * rr.choice([-1, 1], N)
        cl = bp(clicks.astype(np.float64), 1500, 7000)
        hiss = lp(rr.standard_normal(N), 5500) * 0.002
        old[c] = ((cl * 0.03 + hiss) * env_old).astype(np.float32)

    # auto-balance: music sits ~7 dB under the ambience
    ra, rm = amb.std(), music.std()
    mg = 10 ** (-7 / 20) * ra / rm
    print(f"  music gain {mg:.2f}", flush=True)
    mix = amb + music * mg + old
    del amb, music, old

    print("master (dusk darkening)...", flush=True)
    b = smooth((T - 120) / 420) * 0.7
    for c in range(2):
        x = mix[c].astype(np.float64)
        mix[c] = (x * (1 - b) + lp(x, 5200, 2) * b).astype(np.float32)
        mix[c] = hp(mix[c].astype(np.float64), 30, 2).astype(np.float32)
    mix *= 10 ** (-20 / 20) / mix.std()
    mix = np.tanh(mix * 1.4) / 1.4
    fi, fo = 8 * SR, 16 * SR
    mix[:, :fi] *= np.linspace(0, 1, fi) ** 2
    mix[:, -fo:] *= np.linspace(1, 0, fo) ** 2
    mix *= min(1.0, 0.85 / np.abs(mix).max())

    wav = out_mp3.replace(".mp3", ".wav")
    pcm = (mix.T * 32767).astype(np.int16)
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    for m in range(10):
        s = mix[:, m * 60 * SR:(m + 1) * 60 * SR]
        print(f"  min {m}: rms {20*np.log10(s.std()):.1f} dBFS peak {20*np.log10(np.abs(s).max()):.1f}", flush=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libmp3lame", "-b:a", "192k",
                    "-metadata", "title=Nostalgic Evening (Sleep)", "-metadata", "artist=Calm Ambience",
                    out_mp3], check=True)
    os.remove(wav)
    print("done", out_mp3)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Nostalgic_Evening_Sleep_v2.mp3")
