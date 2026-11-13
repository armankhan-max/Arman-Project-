"""Original, royalty-free soundtrack synthesised in code: music beds per mood, sound effects, ambience,
and the final mix (voice clean-up chain, automatic ducking, -14 LUFS loudness)."""
import os
import random
import wave

import numpy as np
from scipy import signal

from . import core

SR = 44100


# ------------------------------------------------------------------ dsp basics
def tt(d):
    return np.arange(int(d * SR)) / SR


def lp(x, fc, o=2):
    b, a = signal.butter(o, min(fc / (SR / 2), 0.99), "low")
    return signal.lfilter(b, a, x)


def hp(x, fc, o=2):
    b, a = signal.butter(o, min(fc / (SR / 2), 0.99), "high")
    return signal.lfilter(b, a, x)


def bp(x, f1, f2, o=2):
    b, a = signal.butter(o, [f1 / (SR / 2), min(f2 / (SR / 2), 0.99)], "band")
    return signal.lfilter(b, a, x)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def fade(x, a=0.01, r=0.05):
    n = len(x)
    A, R = min(n // 2, int(a * SR)), min(n // 2, int(r * SR))
    if A:
        x[:A] *= np.linspace(0, 1, A)
    if R:
        x[-R:] *= np.linspace(1, 0, R)
    return x


def add(buf, x, t, g=1.0, wrap=True):
    """Mix x into buf at time t. With wrap, the tail folds back to the start so loops are seamless."""
    i = int(t * SR)
    n = len(buf)
    if i >= n and not wrap:
        return
    i %= n
    m = min(len(x), n - i)
    buf[i:i + m] += x[:m] * g
    rest = x[m:]
    while wrap and len(rest):
        k = min(len(rest), n)
        buf[:k] += rest[:k] * g
        rest = rest[k:]


# ------------------------------------------------------------------ instruments
def pad(f, d, rng, bright=900, det=0.006):
    t = tt(d)
    x = sum(signal.sawtooth(2 * np.pi * f * (1 + det * k) * t + rng.uniform(0, 6)) for k in (-1, 0, 1))
    x = lp(x, bright) / 3
    return fade(x, min(1.2, d * 0.35), min(1.6, d * 0.4))


def piano(f, d=2.2, vel=1.0):
    t = tt(d)
    x = sum(np.sin(2 * np.pi * f * k * t) * a * np.exp(-t * (2.2 + k * 0.9)) for k, a in ((1, 1), (2, 0.42), (3, 0.2), (4, 0.09)))
    return fade(x * vel * 0.5, 0.004, 0.2)


def pluck(f, d=0.5, vel=1.0):
    t = tt(d)
    x = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 30)) * np.exp(-t * 9)
    return fade(x * vel * 0.5, 0.002, 0.05)


def bell(f, d=2.5, vel=1.0):
    t = tt(d)
    x = sum(np.sin(2 * np.pi * f * r * t) * a * np.exp(-t * dc) for r, a, dc in ((1, 1, 2.5), (2.76, 0.5, 4), (5.4, 0.25, 6)))
    return fade(x * vel * 0.3, 0.002, 0.3)


def bass(f, d, vel=1.0):
    t = tt(d)
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 2 * t)
    return fade(x * vel * 0.5, 0.01, min(0.2, d * 0.3))


def kick(vel=1.0, low=48):
    t = tt(0.4)
    x = np.sin(2 * np.pi * (low + 70 * np.exp(-t * 28)) * t) * np.exp(-t * 9)
    return x * vel * 0.9


def hat(rng, vel=1.0, d=0.06):
    x = hp(rng.standard_normal(int(d * SR)), 7000) * np.exp(-tt(d) * 70)
    return x * vel * 0.25


def strings(f, d, rng):
    t = tt(d)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t)
    x = signal.sawtooth(2 * np.pi * f * vib * t) + signal.sawtooth(2 * np.pi * f * 1.004 * t + 1)
    return fade(lp(x, 1800) * 0.25, min(0.5, d * 0.3), min(0.6, d * 0.3))


def reverb(x, rng, d=2.2, mix=0.3):
    n = int(d * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (SR * d / 5))
    ir = lp(ir, 5000)
    wet = signal.fftconvolve(x, ir)[:len(x) + n]
    wet /= (np.abs(wet).max() + 1e-9)
    out = x.copy()
    add(out, wet[:len(x)], 0, mix * np.abs(x).max(), wrap=False)
    add(out, wet[len(x):], 0, mix * np.abs(x).max(), wrap=True)  # tail folds into the loop start
    return out


SCALES = {"minor": [0, 2, 3, 5, 7, 8, 10], "major": [0, 2, 4, 5, 7, 9, 11], "dorian": [0, 2, 3, 5, 7, 9, 10], "phrygian": [0, 1, 3, 5, 7, 8, 10]}
PROGS = {"minor": [[0, 5, 2, 6], [0, 3, 5, 4], [0, 6, 5, 4], [0, 2, 5, 3]], "major": [[0, 4, 5, 3], [0, 5, 3, 4], [0, 3, 4, 3], [5, 3, 0, 4]],
         "dorian": [[0, 3, 0, 6], [0, 2, 3, 0]], "phrygian": [[0, 1, 0, 6], [0, 5, 1, 0]]}
MOODS = {  # bpm, scale, layers
    "cinematic": (60, "minor", ["pad", "piano_sparse", "sub_pulse"]),
    "suspense": (72, "phrygian", ["drone", "tick", "sub_pulse", "bell_sparse"]),
    "emotional": (66, "minor", ["pad", "piano_arp", "strings"]),
    "ambient": (56, "dorian", ["pad", "bell_sparse", "drone"]),
    "tension": (104, "minor", ["ostinato", "bass", "pad", "tick"]),
    "upbeat": (112, "major", ["marimba", "bass", "kick", "hat", "pad_soft"]),
    "curious": (96, "dorian", ["marimba", "pizz_bass", "hat_soft"]),
    "warm": (84, "major", ["epiano", "bass_soft", "pad_soft"]),
    "epic": (92, "minor", ["drums", "ostinato", "strings", "pad", "bass"]),
    "dark": (50, "phrygian", ["drone", "rumble", "bell_sparse"]),
    "playful": (120, "major", ["glock", "pizz_bass", "hat_soft", "kick_soft"]),
}


def chord_notes(root, scale, deg, octave=0):
    sc = SCALES[scale]
    return [root + 12 * octave + sc[(deg + k) % 7] + 12 * ((deg + k) // 7) for k in (0, 2, 4)]


def make_loop(mood, seed, full=True):
    """One seamless 8-bar section. `full` adds the busier layers (the B section)."""
    rng = np.random.default_rng(seed)
    r = random.Random(seed)
    bpm, scale, layers = MOODS.get(mood, MOODS["cinematic"])
    bpm = bpm + r.randint(-4, 4)
    beat = 60.0 / bpm
    bar = beat * 4
    root = 45 + r.randint(0, 7)  # A2..E3
    prog = r.choice(PROGS[scale])
    bars = 8
    L = np.zeros(int(bars * bar * SR))
    motif = [r.choice([0, 1, 2, 2, 4]) for _ in range(8)]
    for b in range(bars):
        deg = prog[(b // 2) % 4]
        t0 = b * bar
        ch = chord_notes(root, scale, deg, 1)
        sc = [root + 24 + SCALES[scale][k % 7] + 12 * (k // 7) for k in range(14)]
        if "pad" in layers or "pad_soft" in layers:
            g = 0.16 if "pad" in layers else 0.09
            for n in ch:
                add(L, pad(midi(n), bar * 1.15, rng), t0, g)
        if "drone" in layers and b % 4 == 0:
            add(L, lp(pad(midi(root - 12), bar * 4.3, rng, 300, 0.01), 260), t0, 0.5)
            add(L, pad(midi(root + 7), bar * 4.3, rng, 500), t0, 0.07)
        if "sub_pulse" in layers:
            for k in ((0, 2) if full else (0,)):
                add(L, kick(0.35, 38), t0 + k * beat, 0.6)
        if "piano_sparse" in layers and (full or b % 2 == 0):
            for k, st in enumerate((0, 1.5, 3) if full else (0, 2.5)):
                add(L, piano(midi(sc[(deg + motif[(b + k) % 8] * 2) % 14]), 3.0, 0.8 - 0.15 * k), t0 + st * beat, 0.5)
        if "piano_arp" in layers:
            pat = [0, 1, 2, 1, 0, 2, 1, 2] if full else [0, 1, 2, 1]
            step = bar / len(pat)
            for k, idx in enumerate(pat):
                add(L, piano(midi(ch[idx] + (12 if k % 4 == 3 else 0)), 2.4, 0.55 + 0.15 * (k == 0)), t0 + k * step, 0.55)
        if "strings" in layers and full:
            add(L, strings(midi(ch[0] + 12), bar * 1.05, rng), t0, 0.22)
            add(L, strings(midi(ch[2]), bar * 1.05, rng), t0, 0.16)
        if "bell_sparse" in layers and b % 2 == (0 if full else 1):
            add(L, bell(midi(sc[(deg + motif[b % 8]) % 14] + 12), 3.5), t0 + r.choice([0.5, 1, 2.5]) * beat, 0.28)
        if "tick" in layers:
            for k in range(8 if full else 4):
                add(L, hat(rng, 0.5 if k % 2 else 0.8, 0.03), t0 + k * bar / (8 if full else 4), 0.5)
        if "ostinato" in layers:
            pat = [0, 2, 1, 2, 0, 2, 1, 2]
            for k, idx in enumerate(pat):
                if full or k % 2 == 0:
                    add(L, pluck(midi(ch[idx]), 0.4, 0.8 if k % 4 == 0 else 0.55), t0 + k * beat / 2, 0.5)
        if "bass" in layers or "bass_soft" in layers:
            g = 0.5 if "bass" in layers else 0.32
            add(L, bass(midi(ch[0] - 24), beat * 1.8), t0, g)
            if full:
                add(L, bass(midi(ch[0] - 24), beat * 0.9), t0 + 2.5 * beat, g * 0.8)
        if "pizz_bass" in layers:
            for k in (0, 1.5, 2.5) if full else (0, 2):
                add(L, pluck(midi(ch[0] - 12), 0.35, 0.9), t0 + k * beat, 0.6)
        if "marimba" in layers or "glock" in layers:
            hi = 12 if "glock" in layers else 0
            steps = 8
            for k in range(steps):
                if r.random() < (0.75 if full else 0.45):
                    n = sc[(deg + motif[(k + b) % 8] + (k % 3)) % 14] + hi
                    x = bell(midi(n), 0.9, 0.7) if hi else pluck(midi(n), 0.45, 0.8)
                    add(L, x, t0 + k * beat / 2, 0.5)
        if "epiano" in layers:
            for st in ((0, 2.5) if full else (0,)):
                for n in ch:
                    add(L, piano(midi(n), 2.6, 0.5), t0 + st * beat + r.uniform(0, 0.012), 0.32)
        if "kick" in layers or "kick_soft" in layers or "drums" in layers:
            g = 0.3 if "kick_soft" in layers else 0.5
            hits = (0, 2.5) if "drums" in layers else (0, 2)
            if full or "drums" not in layers:
                for k in hits:
                    add(L, kick(1.0, 44 if "drums" in layers else 50), t0 + k * beat, g)
            if "drums" in layers and full:
                tom = lp(rng.standard_normal(int(0.3 * SR)), 500) * np.exp(-tt(0.3) * 12)
                for k in (1.5, 3, 3.5):
                    add(L, tom, t0 + k * beat, 0.5)
        if ("hat" in layers or "hat_soft" in layers) and full:
            for k in range(8):
                add(L, hat(rng, 0.9 if k % 2 == 0 else 0.5), t0 + k * beat / 2, 0.3 if "hat_soft" in layers else 0.45)
        if "rumble" in layers and b % 4 == 2:
            x = lp(rng.standard_normal(int(bar * 2 * SR)), 90) * np.hanning(int(bar * 2 * SR))
            add(L, x, t0, 1.2)
    L = reverb(L, rng, 2.4, 0.28 if mood not in ("upbeat", "playful", "curious") else 0.14)
    L = hp(L, 30)
    return (L / (np.abs(L).max() + 1e-9) * 0.7).astype(np.float32)


class Track:
    """Streams a long mono track to a WAV file from timed events, without holding it all in memory."""

    def __init__(self, path, dur):
        self.path, self.n = path, int(dur * SR) + SR
        self.events = []

    def put(self, t, x, g=1.0):
        if x is not None and len(x) and t < self.n / SR:
            self.events.append((max(0, int(t * SR)), x, g))

    def write(self):
        self.events.sort(key=lambda e: e[0])
        B = SR * 20
        carry = np.zeros(0, np.float32)
        ei = 0
        with wave.open(self.path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            pos = 0
            while pos < self.n:
                size = min(B, self.n - pos)
                longest = max([len(e[1]) for e in self.events[ei:ei + 4000] if e[0] < pos + size] + [0])
                blk = np.zeros(size + max(len(carry), longest) + 1, np.float32)
                blk[:len(carry)] += carry
                while ei < len(self.events) and self.events[ei][0] < pos + size:
                    s, x, g = self.events[ei]
                    o = s - pos
                    if o + len(x) > len(blk):
                        blk = np.concatenate([blk, np.zeros(o + len(x) - len(blk), np.float32)])
                    blk[o:o + len(x)] += x.astype(np.float32) * g
                    ei += 1
                out, carry = blk[:size], blk[size:]
                w.writeframes((np.clip(out, -1, 1) * 32767).astype("<i2").tobytes())
                pos += size
        self.events = []
        return self.path


def build_music(path, dur, mood, seed, sections=None):
    """sections: [(start, mood)] lets the music change with the story. Each section fades in/out."""
    tr = Track(path, dur)
    if mood == "none":
        tr.put(0, np.zeros(SR, np.float32))
        return tr.write()
    sections = sections or [(0.0, mood)]
    loops = {}
    for si, (st, md) in enumerate(sections):
        end = sections[si + 1][0] if si + 1 < len(sections) else dur
        key = md
        if key not in loops:
            s = seed + core.seed_of(md) % 1000
            loops[key] = (make_loop(md, s, False), make_loop(md, s, True))
        A, Bf = loops[key]
        t, k = st, 0
        ll = len(A) / SR
        order = [0, 1, 1, 0, 1, 1, 1, 0]
        while t < end:
            x = (A if order[k % len(order)] == 0 else Bf)
            seg_end = min(end + 2.5, t + ll)
            y = x[:int((seg_end - t) * SR)].copy()
            if k == 0:
                y = fade(y, 2.5 if st > 0 else 1.2, 0.0)
            if t + ll >= end:
                y = fade(y, 0.0, min(4.0, len(y) / SR))
            tr.put(t, y)
            t += ll
            k += 1
    return tr.write()


# ------------------------------------------------------------------ sound effects
def sfx(name, seed=0):
    rng = np.random.default_rng(seed + core.seed_of(name) % 9999)
    if name in ("whoosh", "push", "slide", "wipe", "zoom"):
        d = 0.55
        x = rng.standard_normal(int(d * SR))
        s = np.linspace(0, 1, len(x)) ** 1.4
        lo, hi = bp(x, 250, 1100), bp(x, 1400, 5200 if name != "zoom" else 2800)
        return (lo * (1 - s) * 1.6 + hi * s) * np.hanning(len(x)) * 0.5
    if name in ("hit", "dip", "title"):
        t = tt(1.8)
        x = np.sin(2 * np.pi * (42 + 30 * np.exp(-t * 14)) * t) * np.exp(-t * 2.6)
        x += lp(rng.standard_normal(len(t)), 700) * np.exp(-t * 7) * 0.5
        return fade(x * 0.9, 0.002, 0.4)
    if name == "riser":
        t = tt(2.4)
        x = bp(rng.standard_normal(len(t)), 300, 6000) * (t / 2.4) ** 2.2
        x += np.sin(2 * np.pi * (180 + 500 * (t / 2.4) ** 2) * t) * (t / 2.4) ** 2 * 0.3
        return fade(x * 0.45, 0.05, 0.03)
    if name in ("tick", "clock"):
        return hp(rng.standard_normal(int(0.03 * SR)), 2500) * np.exp(-tt(0.03) * 160) * 0.7
    if name == "click":
        t = tt(0.05)
        return np.sin(2 * np.pi * 1900 * t) * np.exp(-t * 110) * 0.5
    if name == "pop":
        t = tt(0.12)
        return np.sin(2 * np.pi * (520 + 500 * np.exp(-t * 50)) * t) * np.exp(-t * 34) * 0.5
    if name == "rumble":
        t = tt(3.0)
        return lp(rng.standard_normal(len(t)), 80) * np.hanning(len(t)) * 2.2
    if name == "shutter":
        a = hp(rng.standard_normal(int(0.05 * SR)), 1800) * np.exp(-tt(0.05) * 70)
        return np.concatenate([a, np.zeros(int(0.06 * SR)), a * 0.8]) * 0.6
    if name == "typing":
        out = np.zeros(int(1.1 * SR))
        r = random.Random(seed)
        tpos = 0.0
        while tpos < 1.0:
            add(out, hp(rng.standard_normal(int(0.02 * SR)), 1500) * np.exp(-tt(0.02) * 200), tpos, r.uniform(0.3, 0.6), wrap=False)
            tpos += r.uniform(0.05, 0.13)
        return out
    if name == "heartbeat":
        out = np.zeros(int(1.9 * SR))
        for k in (0.0, 0.28, 0.95, 1.23):
            add(out, kick(0.8, 36), k, 0.9, wrap=False)
        return lp(out, 160) * 1.4
    if name == "water":
        t = tt(2.6)
        return bp(rng.standard_normal(len(t)), 300, 2400) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * t)) * np.hanning(len(t)) * 0.3
    if name == "wind":
        t = tt(3.5)
        return bp(rng.standard_normal(len(t)), 150, 900) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * t + 1)) * np.hanning(len(t)) * 0.4
    if name in ("glitch",):
        out = np.zeros(int(0.35 * SR))
        r = random.Random(seed)
        for k in range(6):
            f = r.choice([220, 880, 1760, 3520])
            seg = signal.square(2 * np.pi * f * tt(0.03)) * 0.25
            add(out, seg, k * 0.05 + r.uniform(0, 0.02), 1, wrap=False)
        return out
    if name in ("flash", "burn"):
        t = tt(0.7)
        return hp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 6) * 0.35
    if name == "ding":
        return bell(1320, 1.4, 0.9)
    return None


AMBIENCE = {"wind": (150, 900), "water": (200, 1800), "room": (80, 400), "city": (100, 1200), "night": (2500, 6000), "space": (40, 180)}


def build_sfx(path, dur, cues, seed, ambience=None):
    """cues: [(time, name, gain)]"""
    tr = Track(path, dur)
    cache = {}
    last = {}
    for t, name, g in sorted(cues):
        if name in (None, "none", "cut") or t - last.get(name, -9) < 0.35:
            continue
        last[name] = t
        if name not in cache:
            x = sfx(name, seed)
            cache[name] = None if x is None else x.astype(np.float32)
        if cache[name] is not None:
            lead = 0.18 if name in ("whoosh", "push", "slide", "wipe", "zoom") else (2.3 if name == "riser" else 0.0)
            tr.put(max(0, t - lead), cache[name], g)
    if ambience in AMBIENCE:
        rng = np.random.default_rng(seed)
        lo, hi = AMBIENCE[ambience]
        d = 20.0
        x = bp(rng.standard_normal(int(d * SR)), lo, hi) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.11 * tt(d)))
        x = fade(x / (np.abs(x).max() + 1e-9) * 0.05, 2, 2).astype(np.float32)
        t = 0.0
        while t < dur:
            tr.put(t, x)
            t += d - 2
    tr.put(0, np.zeros(SR, np.float32))
    return tr.write()


def build_voice(path, dur, clips):
    """clips: [(start, file, clip_dur)] → one decoded mono voice track."""
    import subprocess
    tr = Track(path, dur)
    for st, f, cd in clips:
        p = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-t", "%.3f" % cd, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], stdout=subprocess.PIPE)
        x = np.frombuffer(p.stdout, np.float32).copy()
        if len(x):
            fade(x, 0.005, 0.04)
            tr.put(st, x)
    tr.put(0, np.zeros(SR, np.float32))
    return tr.write()


def envelope(wav_path, fps):
    """Speech loudness per video frame, 0..1 (drives avatar lip movement)."""
    with wave.open(wav_path, "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768
    x = np.abs(bp(x, 180, 3200))
    hop = SR // fps
    n = len(x) // hop
    e = x[:n * hop].reshape(n, hop).mean(1) if n else np.zeros(1)
    e = e / (np.percentile(e, 97) + 1e-6)
    e = np.clip(e, 0, 1) ** 0.6
    sm = np.copy(e)
    for i in range(1, len(sm)):  # fast attack, slower release, like a jaw
        sm[i] = e[i] if e[i] > sm[i - 1] else sm[i - 1] * 0.55 + e[i] * 0.45
    return sm.astype(np.float32)


def mix(voice, music, sfx_path, out, music_vol=0.5, sfx_vol=0.7, voice_fx=True, reverb=False):
    chain = "highpass=f=70"
    if voice_fx:
        chain += (",afftdn=nf=-30,equalizer=f=240:t=q:w=1.1:g=-2,equalizer=f=3600:t=q:w=1.3:g=2.5,equalizer=f=9500:t=q:w=1.5:g=1.5,"
                  "deesser=i=0.25,acompressor=threshold=-21dB:ratio=3:attack=8:release=150:makeup=3")
    if reverb:
        chain += ",aecho=0.8:0.5:60|110:0.18|0.1"
    mv = max(0.0, music_vol) * 0.5
    fc = ("[0:a]%s,asplit=2[v][vk];[1:a]volume=%.3f[m];[m][vk]sidechaincompress=threshold=0.02:ratio=9:attack=25:release=700[md];"
          "[2:a]volume=%.3f[s];[v][md][s]amix=inputs=3:normalize=0:dropout_transition=0,loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.95[o]") % (
        chain, mv, max(0.0, sfx_vol) * 0.8)
    core.run(["ffmpeg", "-y", "-v", "error", "-i", voice, "-i", music, "-i", sfx_path, "-filter_complex", fc, "-map", "[o]",
              "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", out])
    return out
