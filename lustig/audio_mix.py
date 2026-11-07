"""Soundtrack for the Lustig test video: enhanced voice + synthesized SFX + original noir score.

Every SFX is placed from events.json (exported by the renderer), so sounds land on the
same frame as the visuals. Music is ducked under the voice.

  python3 audio_mix.py   ->  build/mix.wav
"""
import json
import os
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "video"))
import audio as A  # reuse the synth helpers from the earlier project

SR = 48000
A.SR = SR
from audio import (tt, env_adsr, lp, hp, bp, noise, midi, pluck, pad, bass, kick, hat, shaker,
                   whoosh, pop, click, bell_tone, tape_rewind, tape_stop, hit, riser, heartbeat, gulp, crunch)

DUR = 81.12
N = int(DUR * SR)
rng = np.random.default_rng(5)


def place(buf, x, t, gain=1.0):
    i = int(t * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    if i < 0:
        x, i = x[-i:], 0
    x = x[: len(buf) - i]
    buf[i:i + len(x)] += x * gain


# ---------------------------------------------------------------- SFX
def smooth_env(n, a, r):
    e = np.ones(n)
    A, R = int(a * SR), int(r * SR)
    e[:A] = np.sin(np.linspace(0, np.pi / 2, A)) ** 2
    e[-R:] *= np.cos(np.linspace(0, np.pi / 2, R)) ** 2
    return e


def paper_drop(size=1.0):
    """Soft paper sliding down, then a muted landing on a table."""
    d = .75
    n = int(d * SR)
    t = tt(d)
    slide = bp(noise(d), 700, 3800)
    slide *= smooth_env(n, .12, .35) * (.6 + .4 * np.abs(np.sin(2 * np.pi * 11 * t + 1))) * (t < .42)
    slide *= .22
    j = int(.43 * SR)
    lt = tt(.3)
    land = lp(noise(.3), 1400) * np.exp(-lt * 38) * .6
    thud = np.sin(2 * np.pi * (78 + 30 * np.exp(-lt * 40)) * lt) * np.exp(-lt * 22) * .55 * size
    tap = bp(noise(.3), 2500, 6000) * np.exp(-lt * 120) * .12
    out = slide.copy()
    out[j:j + len(lt)] += land + thud + tap
    return out * (.55 + .3 * size)


def stamp():
    d = .6
    t = tt(d)
    thud = np.sin(2 * np.pi * (62 + 90 * np.exp(-t * 55)) * t) * np.exp(-t * 14)
    body = lp(noise(d), 900) * np.exp(-t * 32) * .7
    snap = bp(noise(d), 1800, 5500) * np.exp(-t * 90) * .22
    return (thud * .9 + body + snap) * .85


def key():
    d = .07
    t = tt(d)
    th = np.sin(2 * np.pi * rng.uniform(170, 230) * t) * np.exp(-t * 90) * .5
    c = lp(bp(noise(d), 1200, 4200), 4200) * np.exp(-t * 150)
    return (th + c * .5) * rng.uniform(.10, .16)


def scribble(dur):
    t = tt(dur + .05)
    n = bp(noise(dur + .05), 2200, 5500)
    am = (.55 + .45 * np.abs(np.sin(2 * np.pi * rng.uniform(5, 7) * t))) * smooth_env(len(t), .04, .08)
    return n * am * .12


def line_zip(dur):
    return np.zeros(int(.01 * SR))


def pin():
    d = .35
    t = tt(d)
    tick = bp(noise(d), 1800, 5000) * np.exp(-t * 110) * .35
    thud = np.sin(2 * np.pi * (95 + 40 * np.exp(-t * 40)) * t) * np.exp(-t * 24) * .6
    return tick + thud


def swell(dur, amt):
    """Soft low air-swell for big camera moves (replaces the noisy whoosh)."""
    n = int(dur * SR)
    t = tt(dur)
    x = bp(noise(dur), 180, 1400)
    x = lp(x, 1500)
    return x * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2 * (.14 + .22 * amt)


def rust_creak(dur):
    t = tt(dur)
    f = 70 + 25 * np.sin(2 * np.pi * .9 * t) + 10 * np.sin(2 * np.pi * 3.1 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = signal.sawtooth(ph) * (.6 + .4 * np.abs(np.sin(2 * np.pi * 7 * t)))
    x = bp(x, 200, 1400) + bp(noise(dur), 300, 900) * .3
    return x * np.minimum(1, np.minimum(t / .1, (dur - t) / .3)) * .35


def counter(dur):
    out = np.zeros(int((dur + .2) * SR))
    k = 0.0
    while k < dur:
        c = click(.5) + np.sin(2 * np.pi * 1800 * tt(.03)) * np.exp(-tt(.03) * 200) * .2
        i = int(k * SR)
        out[i:i + len(c)] += c
        k += .03 + .1 * (k / dur) ** 2
    return out * .7


def msum(*xs):
    n = max(len(x) for x in xs)
    return sum(np.pad(x, (0, n - len(x))) for x in xs)


def seal_sfx():
    return msum(gulp(.4), kick(.3, 90, 40, .6), crunch(.15))


def crowd(dur):
    t = tt(dur)
    x = np.zeros_like(t)
    for f1, f2 in ((300, 700), (600, 1300), (1000, 2400)):
        x += bp(noise(dur), f1, f2) * (.6 + .4 * np.sin(2 * np.pi * rng.uniform(2, 5) * t + rng.uniform(0, 6)))
    e = np.minimum(1, np.minimum(t / .08, (dur - t) / .5))
    return x * e * .45


def watch(dur):
    out = np.zeros(int((dur + .1) * SR))
    for k in np.arange(0, dur, 1 / 8):
        c = np.sin(2 * np.pi * 3200 * tt(.02)) * np.exp(-tt(.02) * 300) + click(.6)[: int(.02 * SR)]
        i = int(k * SR)
        out[i:i + len(c)] += c * (.35 if int(k * 8) % 2 else .25)
    return out * .8


def train(dur, back=False):
    t = tt(dur)
    rate = 3 + 4 * (t / dur if not back else 1 - t / dur)
    ph = np.cumsum(rate) / SR
    chug = bp(noise(dur), 200, 2500) * (np.mod(ph, 1) < .25) * np.exp(-np.mod(ph, 1) * 6)
    e = np.minimum(1, np.minimum(t / .2, (dur - t) / .5))
    out = chug * e * .6
    if not back:
        wd = .8
        wt = tt(wd)
        vib = 1 + .006 * np.sin(2 * np.pi * 6 * wt)
        w = (np.sin(2 * np.pi * 523 * vib * wt) + .7 * np.sin(2 * np.pi * 659 * vib * wt) + .3 * np.sin(2 * np.pi * 784 * vib * wt))
        w *= env_adsr(len(wt), .05, .1, .8, .3) * .18
        out[: len(w)] += w
    return out


def ship(dur):
    hd = 1.6
    t = tt(hd)
    x = signal.sawtooth(2 * np.pi * 98 * t) + .7 * signal.sawtooth(2 * np.pi * 147 * t)
    x = lp(x, 700) * env_adsr(len(t), .2, .2, .85, .6) * .4
    wash = lp(noise(dur), 900) * np.sin(np.pi * np.clip(tt(dur) / dur, 0, 1)) * .15
    out = wash.copy()
    out[: len(x)] += x
    return out


def sink(dur):
    t = tt(dur)
    f = 80 * np.exp(-t / dur * .5)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + .4 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    return lp(x, 400) * np.sin(np.pi * t / dur) ** 2 * .35


def impact():
    d = 2.5
    t = tt(d)
    h = hit(1.0)
    h = np.pad(h, (0, max(0, len(t) - len(h))))[: len(t)]
    return h + lp(noise(d), 3000) * np.exp(-t * 3) * .35 + np.sin(2 * np.pi * 45 * t) * np.exp(-t * 2) * .5


def build_sfx(events):
    sfx = np.zeros(N + SR * 3)
    for e in events:
        t, ty = e["t"], e["type"]
        if ty == "drop":
            place(sfx, paper_drop(e.get("size", 1)), t - .43)
        elif ty == "stamp":
            place(sfx, stamp(), t - .01)
        elif ty == "key":
            place(sfx, key(), t)
        elif ty == "scribble":
            place(sfx, scribble(e["dur"]), t)
        elif ty == "line":
            place(sfx, line_zip(e["dur"]), t)
        elif ty == "pin":
            place(sfx, pin(), t)
        elif ty == "whoosh":
            place(sfx, swell(max(.8, e["dur"]), e["amt"]), t - .1)
        elif ty == "rewind":
            place(sfx, swell(1.2, .5), t - .2)
        elif ty == "rust":
            place(sfx, rust_creak(e["dur"] + .4), t)
        elif ty == "counter":
            place(sfx, counter(e["dur"]), t)
        elif ty == "seal":
            place(sfx, seal_sfx(), t - .02)
        elif ty == "riser":
            place(sfx, riser(e["dur"], .45), t)
        elif ty == "impact":
            place(sfx, impact(), t - .01, 1.1)
        elif ty == "crowd":
            place(sfx, crowd(e["dur"]), t)
        elif ty == "hook":
                        place(sfx, bell_tone(2400, .9) * .45, t + .15)
        elif ty == "watch":
            place(sfx, watch(e["dur"]), t)
        elif ty == "envelope":
            place(sfx, crunch(.35), t)
            place(sfx, paper_drop(.6), t - .43)
        elif ty == "freeze":
            place(sfx, tape_stop(.45), t - .05)
            place(sfx, hit(.8), t)
            place(sfx, heartbeat(.9), t + .25)
            place(sfx, heartbeat(.8), t + 1.05)
        elif ty == "train":
            place(sfx, train(e["dur"], e.get("back", 0)), t)
        elif ty == "case":
            place(sfx, kick(.3, 110, 50, .5), t)
            place(sfx, click(.5), t + .12)
        elif ty == "nothing":
            place(sfx, hit(.7), t)
        elif ty == "sink":
            place(sfx, sink(e["dur"]), t)
        elif ty == "ship":
            place(sfx, ship(e["dur"]), t)
        elif ty == "final":
            place(sfx, hit(.9), t)
            place(sfx, bell_tone(146.8, 3.0) * .6, t)
    return sfx[:N]


# ---------------------------------------------------------------- music (D minor noir heist, 90 bpm)
BEAT = 60 / 90
GRID0 = 4.0
CHORDS = [  # (bass midi, arpeggio, pad)
    (38, [50, 57, 53, 57, 62, 57, 53, 57], [62, 65, 69]),
    (34, [46, 53, 50, 53, 58, 53, 50, 53], [58, 62, 65]),
    (31, [43, 50, 46, 50, 55, 50, 46, 50], [55, 58, 62]),
    (33, [45, 52, 49, 52, 57, 52, 49, 52], [57, 61, 64]),
]
# section flags over time: pizz, bass, kick, hats, pad gain
SECTIONS = [
    (4.0, 14.7, dict(pizz=.8, bass=.7, kick=0, hat=0, pad=.35)),
    (14.7, 22.3, dict(pizz=1, bass=.9, kick=0, hat=.8, pad=.4)),
    (22.3, 31.8, dict(pizz=1, bass=1, kick=.8, hat=1, pad=.45)),
    (35.6, 45.9, dict(pizz=.45, bass=.8, kick=.5, hat=0, pad=.5)),
    (47.6, 52.4, dict(pizz=.7, bass=.7, kick=0, hat=.6, pad=.35)),
    (52.4, 59.4, dict(pizz=1, bass=1, kick=1, hat=1.2, pad=.45)),
    (69.6, 77.4, dict(pizz=1, bass=1, kick=.9, hat=1, pad=.45)),
]


def sec_at(t):
    for a, b, f in SECTIONS:
        if a <= t < b:
            return f
    return None


def build_music():
    L = np.zeros(N + SR * 4)
    R = np.zeros(N + SR * 4)

    def put(x, t, g=1.0, pan=0.0):
        place(L, x, t, g * (1 - max(0, pan)))
        place(R, x, t + .011, g * (1 + min(0, pan)))

    # low drone under everything (Dm), swells at dark moments
    d = DUR + 2
    tt_ = tt(d)
    drone = (np.sin(2 * np.pi * midi(26) * tt_) + .5 * np.sin(2 * np.pi * midi(33) * tt_ + 1) + .25 * np.sin(2 * np.pi * midi(38) * tt_))
    lvl = np.interp(tt_, [0, 3.5, 4, 31, 33, 35, 36, 45.5, 46, 47.6, 59, 60, 66, 69, 70, 78, 80, 82],
                    [.5, .6, .25, .2, .5, .7, .45, .55, .8, .3, .3, .6, .8, .6, .25, .4, .7, .4])
    drone *= lvl * .09
    put(lp(drone, 500), 0)
    # cold open: pulse
    for k in range(5):
        put(lp(kick(.4, 70, 38), 200), .52 + k * BEAT, .45)

    nbeats = int((DUR - GRID0) / BEAT) + 1
    for b in range(nbeats):
        t0 = GRID0 + b * BEAT
        f = sec_at(t0)
        if f is None:
            continue
        bar = b // 4
        ch = CHORDS[bar % 4]
        beat_in_bar = b % 4
        # pizzicato eighths
        for h in range(2):
            tn = t0 + h * BEAT / 2
            if sec_at(tn) is None:
                continue
            if f["pizz"] < .6 and (beat_in_bar * 2 + h) % 2:
                continue
            note = ch[1][beat_in_bar * 2 + h]
            put(pluck(midi(note), .5, .55, 9) * f["pizz"], tn, .5, pan=-.3 if h else .3)
        # bass on beats 1 and 3
        if beat_in_bar in (0, 2) and f["bass"] > 0:
            put(lp(bass(midi(ch[0]), BEAT * 1.6, .01, .2), 900) * f["bass"], t0, .55)
        if f["kick"] > 0 and beat_in_bar in (0, 2):
            put(kick(.35, 95, 42, 1.0) * f["kick"], t0, .5)
        if f["hat"] > 0:
            put(hat(.05, .2) * f["hat"], t0 + BEAT / 2, .6, pan=.4)
            if beat_in_bar == 3:
                put(shaker(.08, .2) * f["hat"], t0 + BEAT * .75, .6, pan=-.4)
        if beat_in_bar == 0 and f["pad"] > 0:
            put(pad([midi(n) for n in ch[2]], BEAT * 4.2, .4, .6, .35) * f["pad"], t0, .32)
    # somber section 59.6 - 69.2: sparse low piano-ish notes (clock of days)
    for i, (tn, n) in enumerate([(59.7, 62), (61.0, 60), (62.35, 57), (64.0, 58), (65.6, 57), (67.2, 53), (68.6, 50)]):
        put(pluck(midi(n), 2.2, .35, 2.2), tn, .45)
        put(pluck(midi(n - 12), 2.2, .25, 2.0), tn, .3)
    put(pad([midi(50), midi(53), midi(56)], 9.5, 2.0, 2.0, .3), 59.6, .35)
    # finale: wide Dm(add9) swell + low D
    put(pad([midi(50), midi(57), midi(62), midi(64), midi(65)], 4.5, 1.2, 1.5, .5), 78.2, .5)
    put(lp(bass(midi(26), 3.5, .3, 1.2), 300), 80.25, .7)
    return np.stack([L[:N], R[:N]], 1)


def reverb(x, secs=1.4, wet=.2, seed=3):
    r = np.random.default_rng(seed)
    n = int(secs * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR * 4.5)
    ir = lp(ir, 5000)
    ir /= np.sqrt((ir ** 2).sum())
    return x + wet * signal.fftconvolve(x, ir)[: len(x)]


def main():
    os.makedirs("build", exist_ok=True)
    events = json.load(open("events.json"))
    sr, v = wavfile.read("assets/voice_hq.wav")
    assert sr == SR
    v = v.astype(np.float64)
    if v.dtype != np.float64 or np.abs(v).max() > 2:
        v = v / 32768.0
    if v.ndim > 1:
        v = v.mean(1)
    voice = np.zeros(N)
    voice[: min(N, len(v))] = v[:N]

    sfx = reverb(build_sfx(events), 1.0, .12, 4)
    mus = build_music()
    mus = np.stack([reverb(mus[:, 0], 1.8, .25, 5), reverb(mus[:, 1], 1.8, .25, 6)], 1)

    # sidechain duck: music dips under speech
    env = np.abs(voice)
    win = int(.05 * SR)
    env = np.convolve(env, np.ones(win) / win, mode="same")
    env = env / (np.percentile(env, 99) + 1e-9)
    sm = np.zeros_like(env)
    a_att, a_rel = np.exp(-1 / (.03 * SR)), np.exp(-1 / (.35 * SR))
    s = 0.0
    for i in range(0, len(env), 32):  # block-wise follower (fast enough)
        e = min(1.0, env[i] * 1.6)
        a = a_att if e > s else a_rel
        s = a ** 32 * s + (1 - a ** 32) * e
        sm[i:i + 32] = s
    duck = 1 - .6 * sm

    def rms(x):
        return np.sqrt(np.mean(x ** 2) + 1e-12)
    vr = rms(voice[voice != 0])
    mus *= (vr * .27 / rms(mus)) * duck[:, None]
    sfx *= (vr * .34 / rms(sfx))
    sfx = .42 * np.tanh(sfx / .42)  # keep transients under the voice
    mix = np.stack([voice, voice], 1) * 1.0 + mus + np.stack([sfx, sfx], 1)
    # soft clip safety
    peak = np.abs(mix).max()
    mix = np.tanh(mix / peak * 1.2) / np.tanh(1.2) * .9
    fade = int(.4 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    wavfile.write("build/mix_pre.wav", SR, (mix * 32767).astype(np.int16))
    wavfile.write("build/stem_music.wav", SR, (np.clip(mus / max(1e-9, np.abs(mus).max()), -1, 1) * 32767 * .9).astype(np.int16))
    wavfile.write("build/stem_sfx.wav", SR, (np.clip(sfx / max(1e-9, np.abs(sfx).max()), -1, 1) * 32767 * .9).astype(np.int16))
    print("ok", mix.shape[0] / SR)


if __name__ == "__main__":
    main()
