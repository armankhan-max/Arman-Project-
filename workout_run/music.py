"""Procedural soundtrack + SFX for the POV cardio run, locked to web/timeline.json.

Everything is synthesized here with numpy (no samples): a 128 BPM EDM score with a different
key, groove and lead for each level, chill lo-fi rests, a triumphant finish, and sound effects
for every cue tick, jump, duck, side step, turn, coin, passing train, sprint and firework.

  python music.py  ->  out/soundtrack.wav
"""
import json
import os

import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, "web", "timeline.json")))
SR = 44100
BEAT = TL["beat"]
BAR = TL["bar"]
DUR = TL["duration"] + 2.0
N = int(DUR * SR)
rng = np.random.default_rng(7)

music = np.zeros((2, N), np.float32)
send = np.zeros((2, N), np.float32)   # reverb send
sfx = np.zeros((2, N), np.float32)
duck_env = np.ones(N, np.float32)     # sidechain from the kick


# ----------------------------------------------------------------------------- basics
def tt(d):
    return np.arange(int(d * SR)) / SR


def midi(m):
    return 440.0 * 2 ** ((np.asarray(m) - 69) / 12)


def adsr(n, a=0.005, d=0.1, s=0.6, r=0.1):
    e = np.full(n, s, np.float32)
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    A = max(1, min(A, n))
    e[:A] = np.linspace(0, 1, A)
    D = min(D, n - A)
    if D > 0:
        e[A:A + D] = np.linspace(1, s, D)
    R = min(R, n)
    if R > 0:
        e[-R:] *= np.linspace(1, 0, R)
    return e


def lp(x, fc, order=2):
    b, a = signal.butter(order, min(max(fc, 20) / (SR / 2), 0.99), "low")
    return signal.lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = signal.butter(order, min(fc / (SR / 2), 0.99), "high")
    return signal.lfilter(b, a, x)


def bp(x, f1, f2, order=2):
    b, a = signal.butter(order, [f1 / (SR / 2), min(f2 / (SR / 2), 0.99)], "band")
    return signal.lfilter(b, a, x)


def saw(f, t, phase=0.0):
    return 2 * ((f * t + phase) % 1.0) - 1


def place(buf, x, t0, gain=1.0, pan=0.0, rev=0.0):
    i = int(round(t0 * SR))
    if i >= N or i + len(x) <= 0:
        return
    j0 = max(0, -i)
    x = x[j0:]
    i = max(i, 0)
    n = min(len(x), N - i)
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[0, i:i + n] += (x[:n] * gain * l * 1.414).astype(np.float32)
    buf[1, i:i + n] += (x[:n] * gain * r * 1.414).astype(np.float32)
    if rev > 0 and buf is not sfx:
        send[0, i:i + n] += (x[:n] * gain * rev * l).astype(np.float32)
        send[1, i:i + n] += (x[:n] * gain * rev * r).astype(np.float32)


def place_sfx(x, t0, gain=1.0, pan=0.0, rev=0.0):
    place(sfx, x, t0, gain, pan)
    if rev:
        i = int(round(t0 * SR))
        if 0 <= i < N:
            n = min(len(x), N - i)
            send[:, i:i + n] += (x[:n] * gain * rev).astype(np.float32)


# ----------------------------------------------------------------------------- drums
def kick(hard=1.0):
    t = tt(0.42)
    f = 46 + 110 * np.exp(-t * 28) * hard
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t * 7.5)
    x += 0.35 * np.exp(-t * 300) * rng.standard_normal(len(t)) * hard
    return np.tanh(x * 1.6) * 0.9


def clap():
    t = tt(0.3)
    n = rng.standard_normal(len(t))
    env = np.exp(-t * 18)
    for d in (0.0, 0.011, 0.022):
        k = int(d * SR)
        env[k:] += 0.6 * np.exp(-(t[: len(t) - k]) * 90)
    return bp(n, 900, 5000) * env * 0.55


def snare():
    t = tt(0.25)
    x = bp(rng.standard_normal(len(t)), 1200, 8000) * np.exp(-t * 20) * 0.6
    x += np.sin(2 * np.pi * 185 * t) * np.exp(-t * 30) * 0.5
    return x


def hat(open_=False):
    d = 0.28 if open_ else 0.05
    t = tt(d)
    x = hp(rng.standard_normal(len(t)), 7500, 2) * np.exp(-t * (9 if open_ else 70))
    return x * (0.32 if open_ else 0.24)


def tom(f=140):
    t = tt(0.45)
    fr = f * (1 + 0.6 * np.exp(-t * 20))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 7) * 0.7


def shaker():
    t = tt(0.07)
    return bp(rng.standard_normal(len(t)), 5000, 12000) * np.sin(np.pi * t / 0.07) * 0.18


def crash():
    t = tt(2.2)
    return hp(rng.standard_normal(len(t)), 4000) * np.exp(-t * 2.0) * 0.35


KICK, KICK_SOFT, CLAP, SNARE, HAT, OHAT, SHAKER, CRASH = kick(), kick(0.5), clap(), snare(), hat(), hat(True), shaker(), crash()
TOMS = [tom(f) for f in (110, 150, 200)]


def kick_at(t0, g=1.0, soft=False):
    place(music, KICK_SOFT if soft else KICK, t0, g * (0.8 if soft else 1.0))
    i = int(t0 * SR)
    n = int(0.3 * SR)
    if 0 <= i < N:
        m = min(n, N - i)
        env = 1 - 0.72 * np.exp(-np.arange(m) / SR * 9) * (0.5 if soft else 1)
        duck_env[i:i + m] = np.minimum(duck_env[i:i + m], env)


# ----------------------------------------------------------------------------- synths
def supersaw(f, d, cutoff=3000, voices=5, detune=0.012, a=0.01, r=0.15, s=0.8):
    t = tt(d + r)
    x = np.zeros(len(t))
    for k in range(voices):
        dt_ = (k - (voices - 1) / 2) / ((voices - 1) / 2 or 1) * detune
        x += saw(f * (1 + dt_), t, rng.random())
    x /= voices
    x = lp(x, cutoff, 2)
    return x * adsr(len(t), a, 0.2, s, r)


def pluck(f, d, bright=4000, decay=6.0):
    t = tt(d)
    x = saw(f, t) * 0.6 + np.sign(np.sin(2 * np.pi * f * t)) * 0.2
    x = lp(x, bright, 2) * np.exp(-t * decay)
    return x * adsr(len(t), 0.002, 0.05, 1.0, 0.03)


def bass(f, d, cutoff=700, drive=1.5):
    t = tt(d)
    x = saw(f, t) * 0.7 + np.sin(2 * np.pi * f / 2 * t) * 0.6
    env_f = cutoff * (1 + 2.5 * np.exp(-t * 18))
    # time-varying cutoff via short blocks
    y = np.zeros_like(x)
    blk = 256
    zi = None
    for i in range(0, len(x), blk):
        b, a = signal.butter(2, min(env_f[i] / (SR / 2), 0.99), "low")
        if zi is None:
            zi = signal.lfilter_zi(b, a) * 0
        y[i:i + blk], zi = signal.lfilter(b, a, x[i:i + blk], zi=zi)
    return np.tanh(y * drive) * adsr(len(t), 0.003, 0.08, 0.8, 0.04) * 0.55


def lead(f, d, vib=0.004, cutoff=5000, kind="saw"):
    t = tt(d + 0.08)
    fm = f * (1 + vib * np.sin(2 * np.pi * 5.5 * t) * np.clip(t * 4, 0, 1))
    ph = np.cumsum(fm) / SR
    if kind == "saw":
        x = (2 * (ph % 1) - 1) * 0.5 + (2 * ((ph * 1.004) % 1) - 1) * 0.5
    elif kind == "square":
        x = np.sign(np.sin(2 * np.pi * ph)) * 0.6 + np.sin(2 * np.pi * ph) * 0.4
    else:  # flute-ish / marimba
        x = np.sin(2 * np.pi * ph) + 0.3 * np.sin(4 * np.pi * ph) + 0.1 * np.sin(6 * np.pi * ph)
    x = lp(x, cutoff, 2)
    return x * adsr(len(t), 0.01, 0.1, 0.75, 0.08)


def marimba(f, d=0.5):
    t = tt(d)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 7) + 0.4 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 22)
    return x * 0.7


def keys(f, d):
    # soft electric-piano-ish tone
    t = tt(d + 0.6)
    x = np.sin(2 * np.pi * f * t + 0.8 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 4))
    x *= np.exp(-t * 1.6)
    return x * adsr(len(t), 0.004, 0.2, 1.0, 0.5) * 0.5


def pad(f, d, cutoff=1800):
    t = tt(d + 0.6)
    x = sum(saw(f * (1 + k * 0.006), t, rng.random()) for k in (-2, -1, 0, 1, 2)) / 5
    x = lp(x, cutoff, 2)
    return x * adsr(len(t), 0.35, 0.3, 0.8, 0.6)


def noise_riser(d, f0=400, f1=9000):
    t = tt(d)
    n = rng.standard_normal(len(t))
    y = np.zeros_like(n)
    blk = 512
    zi = None
    for i in range(0, len(n), blk):
        fc = f0 * (f1 / f0) ** (i / len(n))
        b, a = signal.butter(2, [max(fc * 0.6, 30) / (SR / 2), min(fc * 1.4, 20000) / (SR / 2)], "band")
        if zi is None:
            zi = np.zeros(max(len(a), len(b)) - 1)
        y[i:i + blk], zi = signal.lfilter(b, a, n[i:i + blk], zi=zi)
    return y * (t / d) ** 2 * 0.5


def impact():
    t = tt(2.5)
    sub = np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-t * 6)) / SR) * np.exp(-t * 2.2)
    n = lp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 4) * 0.5
    return np.tanh((sub + n) * 1.3) * 0.8


# ----------------------------------------------------------------------------- harmony per level
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def chord(root, kind="min", octave=4):
    r = NOTE[root] + 12 * (octave + 1)
    iv = {"min": [0, 3, 7], "maj": [0, 4, 7], "sus": [0, 5, 7]}[kind]
    return [r + i for i in iv]


LEVEL_MUSIC = [
    dict(prog=[("A", "min"), ("F", "maj"), ("C", "maj"), ("G", "maj")], scale=[0, 2, 3, 5, 7, 8, 10], tonic="A",
         lead="square", cutoff=2600, bright=3500),
    dict(prog=[("D", "min"), ("A#", "maj"), ("F", "maj"), ("C", "maj")], scale=[0, 2, 3, 5, 7, 8, 10], tonic="D",
         lead="saw", cutoff=2200, bright=3000, acid=True),
    dict(prog=[("E", "maj"), ("B", "maj"), ("C#", "min"), ("A", "maj")], scale=[0, 2, 4, 5, 7, 9, 11], tonic="E",
         lead="saw", cutoff=4200, bright=5000),
    dict(prog=[("F#", "min"), ("D", "maj"), ("E", "maj"), ("F#", "min")], scale=[0, 3, 5, 7, 10], tonic="F#",
         lead="flute", cutoff=3000, bright=3500, tribal=True),
    dict(prog=[("G", "min"), ("D#", "maj"), ("A#", "maj"), ("F", "maj")], scale=[0, 2, 3, 5, 7, 8, 10], tonic="G",
         lead="saw", cutoff=5200, bright=6000),
]


def make_motif(cfg, seed):
    """A catchy two-bar motif: rhythm in 16ths, scale degrees."""
    r = np.random.default_rng(seed)
    rhythms = [
        [0, 3, 6, 8, 10, 12, 14, 16, 19, 22, 24, 28],
        [0, 2, 4, 6, 8, 11, 14, 16, 18, 20, 24, 27, 30],
        [0, 3, 6, 10, 12, 16, 19, 22, 26, 28],
    ]
    rh = rhythms[r.integers(len(rhythms))]
    deg = 0
    notes = []
    for k, p in enumerate(rh):
        deg = int(np.clip(deg + r.choice([-2, -1, 1, 1, 2, 0, 3]), -2, 7))
        nxt = rh[k + 1] if k + 1 < len(rh) else 32
        notes.append((p, max(1, min(nxt - p, 4)), deg))
    return notes


def degree_to_midi(cfg, deg, octave=5):
    sc = cfg["scale"]
    base = NOTE[cfg["tonic"]] + 12 * (octave + 1)
    o, i = divmod(deg, len(sc))
    return base + 12 * o + sc[i]


# ----------------------------------------------------------------------------- arrangement
SECS = TL["sections"]
LVLS = TL["levels"]


def level_bar_roles(li):
    """Role of each bar in an 80-bar level: groove / drop / build / sprint / outro."""
    lv = LVLS[li]
    roles = []
    sprints = [(e["t"], e["t_end"]) for e in lv["events"] if e["move"] == "sprint"]
    nb = int(round(80))
    for b in range(nb):
        t = b * BAR
        role = "drop" if (b // 8) % 2 == 1 else "groove"
        if b < 2:
            role = "groove"
        for a, e in sprints:
            if a - 2 * BAR <= t < a:
                role = "build"
            elif a <= t < e:
                role = "sprint"
        if b >= nb - 1:
            role = "outro"
        roles.append(role)
    return roles


def render_level(li, sec):
    cfg = LEVEL_MUSIC[li]
    t0 = sec["t0"]
    roles = level_bar_roles(li)
    motif = make_motif(cfg, 40 + li)
    motif2 = make_motif(cfg, 90 + li)
    for b, role in enumerate(roles):
        tb = t0 + b * BAR
        root, kind = cfg["prog"][b % 4]
        ch = chord(root, kind, 4)
        energy = {"groove": 0.8, "drop": 1.0, "build": 0.9, "sprint": 1.15, "outro": 0.7}[role]
        # drums
        for q in range(4):
            tq = tb + q * BEAT
            if role == "build" and b % 2 == 1 and q == 3:
                continue
            if not (role == "outro" and q >= 2):
                kick_at(tq, 0.95)
            if q in (1, 3):
                place(music, CLAP, tq, 0.55 * energy, 0.0, rev=0.25)
            place(music, OHAT, tq + BEAT / 2, 0.45 * energy, 0.25)
            n16 = 4 if role in ("drop", "sprint") else 2
            for k in range(n16):
                place(music, HAT, tq + k * BEAT / n16, 0.5 * (1.0 if k % 2 == 0 else 0.6), -0.3)
            if cfg.get("tribal"):
                for k, tom_i in ((0.75, 0), (1.5, 1), (2.75, 2)):
                    if q % 2 == 0:
                        place(music, TOMS[tom_i], tq + k * BEAT / 2, 0.35 * energy, (tom_i - 1) * 0.5, rev=0.15)
                place(music, SHAKER, tq + BEAT * 0.25, 0.6, 0.4)
                place(music, SHAKER, tq + BEAT * 0.75, 0.6, 0.4)
        if role == "build":
            # snare roll accelerating over the two build bars
            k = 1 if b > 0 and roles[b - 1] == "build" else 0
            steps = 8 if k == 0 else 16
            for i in range(steps):
                place(music, SNARE, tb + i * BAR / steps, (0.25 + 0.5 * (k * steps + i) / (2 * steps)) * 0.8, 0.0, rev=0.2)
            if k == 0:
                place(music, noise_riser(2 * BAR), tb, 0.55, 0.0, rev=0.3)
        if b % 8 == 0 or (role == "sprint" and roles[b - 1] != "sprint"):
            place(music, CRASH, tb, 0.6, 0.2, rev=0.3)
        # bass: offbeat 8ths on the chord root (sidechained)
        rootm = NOTE[root] + 12 * 2
        for q in range(8):
            if q % 2 == 0 and not cfg.get("acid"):
                continue
            f = midi(rootm + (12 if (cfg.get("acid") and q in (3, 7)) else 0))
            place(music, bass(f, BEAT / 2 * 0.9, cutoff=(500 if role == "groove" else 900)), tb + q * BEAT / 2, 0.75)
        # chords: stabs in drops, held supersaw pad otherwise
        if role in ("drop", "sprint"):
            for q in [0, 1.5, 3, 4.5, 6]:
                for m in ch:
                    place(music, supersaw(midi(m), BEAT * 0.45, cutoff=cfg["cutoff"], a=0.003, r=0.08), tb + q * BEAT / 2,
                          0.09, (m % 3 - 1) * 0.3, rev=0.3)
        else:
            for m in ch:
                place(music, pad(midi(m), BAR, cutoff=1500 if role != "build" else 2500), tb, 0.07, (m % 3 - 1) * 0.4, rev=0.35)
        # arp in 16ths
        if role in ("groove", "drop", "sprint", "build"):
            arp = ch + [ch[0] + 12, ch[1] + 12]
            for i in range(16):
                m = arp[(i * 3 + (i // 4)) % len(arp)] + 12
                g = 0.07 if role != "sprint" else 0.09
                fn = marimba if cfg.get("tribal") else pluck
                x = fn(midi(m), 0.22) if cfg.get("tribal") else pluck(midi(m), 0.2, bright=cfg["bright"])
                place(music, x, tb + i * BEAT / 4, g, 0.5 * np.sin(i), rev=0.25)
        # lead melody on drops and sprints (two-bar motif, answered by a variation)
        if role in ("drop", "sprint"):
            mot = motif if (b // 2) % 2 == 0 else motif2
            half = b % 2
            oct_ = 6 if role == "sprint" else 5
            for p, d, deg in mot:
                if (p >= 16) != bool(half):
                    continue
                tp = tb + (p - 16 * half) * BEAT / 4
                m = degree_to_midi(cfg, deg + (b // 4) % 2, oct_)
                place(music, lead(midi(m), d * BEAT / 4 * 0.95, kind=cfg["lead"], cutoff=cfg["cutoff"] * 1.4), tp, 0.13, 0.1, rev=0.35)
    # level start impact
    place(music, impact(), t0, 0.7, 0.0, rev=0.3)


REST_PROG = [("C", "maj"), ("A", "min"), ("F", "maj"), ("G", "sus")]


def render_rest(sec, cooldown=False):
    t0, t1 = sec["t0"], sec["t1"]
    nb = int(round((t1 - t0) / BAR))
    for b in range(nb):
        tb = t0 + b * BAR
        root, kind = REST_PROG[b % 4]
        ch = chord(root, kind, 4) if kind != "sus" else chord(root, "sus", 4)
        if not cooldown or b < nb - 2:
            # lazy half-time groove
            if b >= 1:
                kick_at(tb, 0.55, soft=True)
                kick_at(tb + 2.5 * BEAT, 0.4, soft=True)
                place(music, SNARE, tb + 2 * BEAT, 0.22, 0.0, rev=0.4)
                for k in range(8):
                    sw = 0.06 * BEAT if k % 2 else 0.0
                    place(music, HAT, tb + k * BEAT / 2 + sw, 0.22 if k % 2 else 0.3, 0.3)
        for m in ch:
            place(music, keys(midi(m), BAR * 0.95), tb, 0.16, (m % 3 - 1) * 0.4, rev=0.5)
        place(music, keys(midi(NOTE[root] + 36), BAR), tb, 0.22, 0.0, rev=0.2)
        for m in ch:
            place(music, pad(midi(m + 12), BAR, cutoff=1100), tb, 0.04, (m % 3 - 1) * 0.6, rev=0.6)
        # gentle melody bell every other bar
        if b % 2 == 1:
            for i, k in enumerate([0, 2, 1, 4]):
                m = ch[k % 3] + 24 + (12 if k == 4 else 0)
                place(music, marimba(midi(m), 0.9), tb + i * BEAT * 0.75, 0.08, 0.3 * np.sin(i * 2), rev=0.6)
    # vinyl-ish air
    t = tt(t1 - t0)
    hiss = hp(rng.standard_normal(len(t)), 3000) * 0.006
    place(music, hiss, t0, 1.0, 0.0)


def render_intro(sec):
    t0 = sec["t0"]
    for b in range(6):
        tb = t0 + b * BAR
        root, kind = LEVEL_MUSIC[0]["prog"][b % 4]
        for m in chord(root, kind, 4):
            place(music, pad(midi(m), BAR, cutoff=600 + b * 450), tb, 0.08, (m % 3 - 1) * 0.4, rev=0.5)
        if b >= 2:
            for q in range(4):
                kick_at(tb + q * BEAT, 0.6 + 0.08 * b)
                if b >= 4:
                    place(music, HAT, tb + q * BEAT + BEAT / 2, 0.4, 0.3)
        # heartbeat in the first bars (the ECG on screen)
        if b < 2:
            for q in range(4):
                place(music, KICK_SOFT, tb + q * BEAT, 0.5)
                place(music, KICK_SOFT, tb + q * BEAT + 0.16, 0.3)
    place(music, noise_riser(2 * BAR), t0 + 4 * BAR, 0.5, 0.0, rev=0.3)


def render_card(sec):
    t0 = sec["t0"]
    li = sec["world"]
    cfg = LEVEL_MUSIC[li]
    root, kind = cfg["prog"][0]
    place(music, impact(), t0, 0.55, 0.0, rev=0.3)
    for b in range(2):
        tb = t0 + b * BAR
        for m in chord(root, kind, 4):
            place(music, pad(midi(m), BAR, cutoff=900 + 900 * b), tb, 0.07, 0.0, rev=0.4)
        for q in range(4):
            kick_at(tb + q * BEAT, 0.7)
    for i in range(16):
        place(music, SNARE, t0 + BAR + i * BAR / 16, 0.2 + 0.5 * i / 16, 0.0, rev=0.2)
    place(music, noise_riser(2 * BAR), t0, 0.45, 0.0, rev=0.3)


def render_finish(sec):
    t0 = sec["t0"]
    place(music, impact(), TL["finish_cross"], 0.9, 0.0, rev=0.4)
    place(music, CRASH, TL["finish_cross"], 0.8, 0.0, rev=0.4)
    fan = [("G", "maj"), ("C", "maj"), ("D", "maj"), ("G", "maj")]
    for b, (root, kind) in enumerate(fan):
        tb = t0 + b * BAR
        ch = chord(root, kind, 4)
        for q in range(4):
            kick_at(tb + q * BEAT, 0.8)
            if q in (1, 3):
                place(music, CLAP, tb + q * BEAT, 0.5, 0.0, rev=0.3)
        for m in ch + [ch[0] + 12]:
            place(music, supersaw(midi(m), BAR * 0.95, cutoff=4500, a=0.02, r=0.4), tb, 0.08, (m % 3 - 1) * 0.4, rev=0.4)
        mel = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[0] + 24]
        for i, m in enumerate(mel):
            place(music, lead(midi(m), BEAT * 0.9, kind="square", cutoff=6000), tb + i * BEAT, 0.12, 0.0, rev=0.4)


def render_outro(sec):
    t0 = sec["t0"]
    for m in chord("C", "maj", 4) + [72]:
        place(music, pad(midi(m), 3 * BAR - 0.5, cutoff=2500), t0, 0.1, (m % 3 - 1) * 0.5, rev=0.7)
        place(music, keys(midi(m), 2.0), t0, 0.15, 0.0, rev=0.6)
    place(music, impact(), t0, 0.5, 0.0, rev=0.5)
    for i, m in enumerate([72, 76, 79, 84]):
        place(music, marimba(midi(m), 1.2), t0 + 0.2 + i * BEAT * 0.5, 0.12, 0.0, rev=0.6)


for s in SECS:
    if s["kind"] == "level":
        render_level(s["world"], s)
    elif s["kind"] == "rest":
        render_rest(s, cooldown=bool(s.get("cooldown")))
    elif s["kind"] == "intro":
        render_intro(s)
    elif s["kind"] == "card":
        render_card(s)
    elif s["kind"] == "finish":
        render_finish(s)
    elif s["kind"] == "outro":
        render_outro(s)


# ----------------------------------------------------------------------------- SFX
def tick(f=1800):
    t = tt(0.06)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 70) * 0.6 + bp(rng.standard_normal(len(t)), 2000, 6000) * np.exp(-t * 120) * 0.2


def whoosh(d=0.45, f0=300, f1=3000):
    x = noise_riser(d, f0, f1)
    t = tt(d)
    return x / (np.abs(x).max() + 1e-6) * np.sin(np.pi * t / d) ** 1.5 * 0.6


def swish(d=0.35):
    t = tt(d)
    x = bp(rng.standard_normal(len(t)), 1500, 7000) * np.sin(np.pi * t / d) ** 2
    return x * 0.5


def thud():
    t = tt(0.25)
    return np.sin(2 * np.pi * np.cumsum(60 + 50 * np.exp(-t * 30)) / SR) * np.exp(-t * 16) * 0.8 + lp(rng.standard_normal(len(t)), 900) * np.exp(-t * 25) * 0.3


def coin_chime(step):
    t = tt(0.32)
    f1 = midi(84 + [0, 2, 4, 7, 9, 12][step % 6])
    x = (np.sin(2 * np.pi * f1 * t) + 0.5 * np.sin(2 * np.pi * f1 * 2.01 * t)) * np.exp(-t * 12)
    f2 = f1 * 1.5
    x2 = np.sin(2 * np.pi * f2 * t) * np.exp(-(t - 0.05).clip(0) * 14) * (t > 0.05)
    return (x + 0.6 * x2) * 0.22


def train_pass(d=2.6):
    t = tt(d)
    n = lp(rng.standard_normal(len(t)), 1800)
    rumble = lp(rng.standard_normal(len(t)), 150) * 2
    clack = np.zeros(len(t))
    for k in np.arange(0, d, 0.11):
        i = int(k * SR)
        m = min(int(0.03 * SR), len(t) - i)
        clack[i:i + m] += np.exp(-np.arange(m) / SR * 200) * 0.7
    env = np.exp(-((t - d * 0.45) / (d * 0.22)) ** 2)
    return (n * 0.6 + rumble * 0.5 + bp(clack * rng.standard_normal(len(t)), 800, 4000)) * env * 0.5


def horn(d=0.9):
    t = tt(d)
    x = sum(np.sign(np.sin(2 * np.pi * f * t)) for f in (311, 370, 466)) / 3
    return lp(x, 2500) * adsr(len(t), 0.03, 0.1, 0.9, 0.2) * 0.25


def sizzle(d=0.5):
    t = tt(d)
    return bp(rng.standard_normal(len(t)), 3000, 11000) * np.exp(-t * 4) * 0.3 * (1 + 0.5 * np.sin(2 * np.pi * 37 * t))


def firework():
    t = tt(1.6)
    boom = lp(rng.standard_normal(len(t)), 700) * np.exp(-t * 6) * 1.2
    crackle = np.zeros(len(t))
    for k in range(40):
        i = int((0.15 + rng.random() * 1.2) * SR)
        m = min(300, len(t) - i)
        crackle[i:i + m] += rng.standard_normal(m) * np.exp(-np.arange(m) / 40) * 0.5
    return boom + hp(crackle, 2000)


def cheer(d=4.0):
    t = tt(d)
    x = np.zeros(len(t))
    for f in (700, 1100, 1700, 2500):
        x += bp(rng.standard_normal(len(t)), f * 0.8, f * 1.25) * (1 + 0.3 * np.sin(2 * np.pi * rng.random() * 3 * t))
    return x * np.clip(t / 0.3, 0, 1) * np.exp(-t * 0.6) * 0.35


def bell(f=1046):
    t = tt(1.5)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3)) * np.exp(-t * 2.5) * 0.35


def pop():
    t = tt(0.12)
    return np.sin(2 * np.pi * np.cumsum(900 * np.exp(-t * 20) + 300) / SR) * np.exp(-t * 30) * 0.5


TICK_LO, TICK_HI = tick(1500), tick(2200)
WH_UP, WH_DN = whoosh(0.5, 300, 4000), whoosh(0.5, 4000, 300)
SWISH, THUD = swish(), thud()
COINS = [coin_chime(i) for i in range(6)]

for lv in LVLS:
    li = lv["index"]
    lead_beats = 3 if li == 4 else 4
    for e in lv["events"]:
        te = e["t_abs"]
        m = e["move"]
        # countdown ticks on the beats before the move, then the action sound
        for k in range(1, lead_beats):
            place_sfx(TICK_LO, te - k * BEAT, 0.5)
        place_sfx(TICK_HI, te - lead_beats * BEAT, 0.35)
        if m == "sprint":
            place_sfx(whoosh(1.0, 200, 6000), te - 0.3, 0.7, rev=0.2)
            place_sfx(impact(), te, 0.5)
            place_sfx(sizzle(2.0), te, 0.35)
            continue
        if m in ("jump", "jump2"):
            for k in ([0] if m == "jump" else [0, 2 * BEAT]):
                place_sfx(WH_UP, te + k - 0.05, 0.8)
                place_sfx(THUD, te + k + 0.74, 0.9)
        elif m == "duck":
            place_sfx(WH_DN, te - 0.05, 0.8)
        elif m in ("left", "right", "turnL", "turnR"):
            pan = -0.7 if m in ("left", "turnL") else 0.7
            place_sfx(SWISH, te - 0.05, 0.9, pan)
            if lv["kind"] == "skyrail":
                place_sfx(THUD, te + 0.38, 0.6)
            if e.get("oncoming"):
                place_sfx(horn(), te - 1.6, 0.8, -pan * 0.3)
                place_sfx(train_pass(), te + 0.72 - 1.2, 1.0, -pan * 0.6)
    for tp in lv["passes"]:
        place_sfx(train_pass(), tp - 1.2, 0.7, 0.0)
    # hazards that hum: electric fences and saws (short sizzles when passing)
    # coins: pitch rises along a run of coins
    prev = -9
    step = 0
    for c in lv["coins"]:
        tc = c["t"] - 0.24
        step = step + 1 if tc - prev < 0.5 else 0
        place_sfx(COINS[step % 6], tc, 0.55, 0.15 * np.sin(step), rev=0.1)
        prev = tc

for s in SECS:
    if s["kind"] == "card":
        lv = LVLS[s["world"]]
        n = 2 + len(set(e["move"] for e in lv["events"]))
        for i in range(n):
            place_sfx(pop(), s["t0"] + BEAT * (1 + i * 0.5), 0.6)
    if s["kind"] == "rest":
        place_sfx(whoosh(0.7, 200, 3000), s["t0"] - 0.1, 0.6)
        b = BAR
        starts = [s["t0"], s["t0"] + 8 * b] if s.get("cooldown") else [s["t0"], s["t0"] + 4 * b, s["t0"] + 12 * b]
        for st in starts:
            place_sfx(bell(1046), st, 0.6, rev=0.5)
        # side switch chimes in the middle of each stretch
        segs = list(zip(starts, starts[1:] + [s["t1"]]))
        for a, z in segs[(0 if s.get("cooldown") else 1):]:
            place_sfx(bell(1318), (a + z) / 2, 0.5, rev=0.5)

place_sfx(cheer(5.0), TL["finish_cross"], 0.8, rev=0.3)
for i, tf in enumerate(TL["fireworks"]):
    place_sfx(whoosh(0.55, 500, 5000), tf - 0.55, 0.35, (i % 3 - 1) * 0.5)
    place_sfx(firework(), tf, 0.6, (i % 3 - 1) * 0.5, rev=0.4)
for ts in TL["stars"]:
    place_sfx(bell(1568), ts, 0.6, rev=0.4)
outro = [s for s in SECS if s["kind"] == "outro"][0]
for i in range(3):
    place_sfx(bell(1568 * [1, 1.25, 1.5][i]), outro["t0"] + 0.3 + i * BEAT * 0.5, 0.5, rev=0.5)

# ----------------------------------------------------------------------------- mix
print("reverb...")
ir_t = tt(2.4)
ir = rng.standard_normal((2, len(ir_t))) * np.exp(-ir_t * 2.6)
ir[:, : int(0.012 * SR)] = 0
ir = np.stack([lp(ir[0], 6000), lp(ir[1], 6000)])
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.stack([signal.oaconvolve(send[c], ir[c].astype(np.float32))[:N] for c in range(2)]).astype(np.float32)

music *= duck_env[None, :]
mix = music + wet * 0.55 + sfx * 0.9
# gentle bus compression / limiting
peak = np.abs(mix).max()
mix = mix / max(peak, 1e-6) * 1.4
mix = np.tanh(mix) * 0.89
fade = int(1.2 * SR)
end = int(TL["duration"] * SR)
mix[:, end - fade:end] *= np.linspace(1, 0, fade)
mix[:, end:] = 0
mix = mix[:, :end]
mix[:, : int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))
os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
out = os.path.join(HERE, "out", "soundtrack.wav")
wavfile.write(out, SR, (mix.T * 32767).astype(np.int16))
print("wrote", out, f"{mix.shape[1] / SR:.1f}s")
