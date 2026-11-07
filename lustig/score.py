"""Suspense score (original, synthesized): drones, low string ostinato, tremolo, braams,
clock pulse, heartbeat, risers. Pace follows the voiceover: slow in backstory/suspicion,
driving in the scheme, the escape and round two."""
import numpy as np
from scipy import signal

import audio as A
from audio import tt, lp, hp, bp, noise, midi, pluck, kick, heartbeat

SR = A.SR
rng = np.random.default_rng(21)


def env(n, a, r):
    e = np.ones(n)
    A_, R = max(1, int(a * SR)), max(1, int(r * SR))
    A_, R = min(A_, n), min(R, n)
    e[:A_] = np.linspace(0, 1, A_)
    e[-R:] *= np.linspace(1, 0, R)
    return e


def saw_stack(f, dur, det=(-.006, 0, .007)):
    t = tt(dur)
    return sum(signal.sawtooth(2 * np.pi * f * (1 + d) * t + rng.uniform(0, 6)) for d in det) / len(det)


def stacc(f, dur=.2):                       # low string staccato
    x = saw_stack(f, dur)
    t = tt(dur)
    return lp(x, 1400) * np.exp(-t * 14) * env(len(t), .004, .03)


def braam(root, dur=3.0):                   # big low brass hit
    t = tt(dur)
    x = saw_stack(midi(root), dur) + .8 * saw_stack(midi(root + 12), dur) + .5 * saw_stack(midi(root + 7), dur)
    x = np.tanh(x * 1.6)
    out = np.zeros_like(x)
    seg = 1024
    for i in range(0, len(x), seg):                      # filter opens then closes
        p = i / len(x)
        fc = 250 + 1700 * np.exp(-((p - .08) ** 2) / .02)
        out[i:i + seg] = lp(x[max(0, i - 4096):i + seg], fc)[-len(x[i:i + seg]):]
    return out * env(len(t), .03, dur * .6) * .9


def tremolo(notes, dur, rate=11, bright=2600):  # high string tremolo cluster
    t = tt(dur)
    x = sum(saw_stack(midi(n), dur) for n in notes) / len(notes)
    x = lp(hp(x, 300), bright) * (.55 + .45 * np.sin(2 * np.pi * rate * t) ** 2)
    return x * env(len(t), dur * .35, dur * .3)


def drone(notes, dur, a=2.0, r=2.0):
    t = tt(dur)
    x = sum(np.sin(2 * np.pi * midi(n) * t + i) + .3 * np.sin(2 * np.pi * midi(n) * 2.003 * t) for i, n in enumerate(notes)) / len(notes)
    return lp(x, 600) * env(len(t), a, r)


def tick(hi=True):
    d = .05
    t = tt(d)
    return (bp(noise(d), 2500 if hi else 1200, 7000) * np.exp(-t * 180) + np.sin(2 * np.pi * (3100 if hi else 1700) * t) * np.exp(-t * 220) * .4) * .5


def taiko(g=1.0):
    d = .8
    t = tt(d)
    return (kick(d, 120, 40, 1.0) * 1.1 + lp(noise(d), 500) * np.exp(-t * 18) * .5) * g


def shepard(dur):                           # endless rising tension
    t = tt(dur)
    x = np.zeros_like(t)
    for k in range(6):
        oct_ = (k + t / dur * 1.5) % 6
        f = 55 * 2 ** oct_
        amp = np.exp(-((oct_ - 3) ** 2) / 2.5)
        x += amp * np.sin(2 * np.pi * np.cumsum(f) / SR)
    return x * env(len(t), dur * .6, .05) * .35


def reverse_swell(dur):
    t = tt(dur)
    return bp(noise(dur), 300, 4000) * (t / dur) ** 3 * .8


def piano(f, dur=2.5):
    return pluck(f, dur, .45, 2.0) + .4 * pluck(f * 2, dur, .3, 3.0)


# ostinato patterns (MIDI), one note per 16th
OST_A = [38, 38, 41, 38, 39, 38, 41, 38]          # D D F D Eb D F D  (phrygian bite)
OST_B = [36, 36, 39, 36, 37, 36, 39, 36]          # C ...  (step down every other bar)


def build(DUR):
    N = int(DUR * SR)
    L = np.zeros(N + SR * 6)
    R = np.zeros(N + SR * 6)

    def put(x, t, g=1.0, pan=0.0):
        i = int(t * SR)
        if i >= len(L):
            return
        x = x[: len(L) - i]
        L[i:i + len(x)] += x * g * (1 - max(0, pan) * .7)
        j = i + int(.013 * SR)
        x2 = x[: len(R) - j]
        R[j:j + len(x2)] += x2 * g * (1 + min(0, pan) * .7)

    # ---- bed: drone through the whole film, darker in slow parts
    put(drone([26, 33], 36), 0, .55)
    put(drone([26, 32, 38], 26), 34.5, .55)       # tritone colour in suspicion
    put(drone([26, 33, 41], 23), 58.5, .6)

    # ---- cold open: two braams on "sold" + tremolo bed + reverse swell into rewind
    put(tremolo([74, 75], 3.8), 0, .22, .3)
    put(braam(26, 2.6), .5, .55)
    put(braam(27, 2.6), 2.98, .6)
    put(reverse_swell(.9), 3.0, .35)

    # ---- slow backstory 4.0-14.6: clock pulse + sparse piano + low pulse
    for k, tk in enumerate(np.arange(4.1, 14.6, .75)):
        put(tick(k % 2 == 0), tk, .28, .4 if k % 2 else -.4)
    for tk, n in [(4.6, 62), (6.1, 65), (7.4, 63), (8.6, 62), (10.1, 58), (11.6, 57), (13.0, 62)]:
        put(piano(midi(n)), tk, .32)
    for tk in np.arange(4.1, 14.6, 1.5):
        put(lp(kick(.5, 60, 36), 160), tk, .5)
    put(shepard(1.8), 12.9, .4)

    # ---- fast: scheme 14.7-31.8 (ostinato 16ths @ 112 bpm, building)
    def ostinato(a, b, bpm=112, g=.42, perc=True, start_full=False):
        s16 = 60 / bpm / 4
        n = int((b - a) / s16)
        for i in range(n):
            t0 = a + i * s16
            bar = i // 16
            pat = OST_A if bar % 2 == 0 else OST_B
            note = pat[i % 8]
            prog = (i / max(1, n)) if not start_full else 1
            acc = 1.0 if i % 4 == 0 else .62
            put(stacc(midi(note), .18), t0, g * acc * (.7 + .3 * prog), -.25)
            if i % 8 == 4 and prog > .3:
                put(stacc(midi(note + 12), .14), t0, g * .35, .35)
            if perc:
                if i % 16 == 0:
                    put(taiko(), t0, .5 * (.6 + .4 * prog))
                if i % 16 == 10 and prog > .45:
                    put(taiko(.6), t0, .35)
                if i % 2 == 0:
                    put(tick(i % 4 == 2), t0, .12 * (.5 + .5 * prog), .5)
    ostinato(14.75, 31.8)
    put(tremolo([74, 75, 79], 9.0), 22.3, .14, -.3)
    put(braam(26, 2.4), 23.1, .35)                # "six" dealers
    put(braam(29, 2.4), 28.88, .38)               # "7,000"

    # ---- break: riot 31.8-35.6 (shepard rise -> braam -> silence)
    put(shepard(3.0), 31.8, .55)
    put(tremolo([86, 87], 3.0, 14), 31.8, .14)
    put(braam(26, 3.0), 34.78, .85)
    put(taiko(1.2), 34.78, .7)

    # ---- slow suspicion 35.6-45.9: heartbeat + ticking + dissonant tremolo
    for tk in np.arange(35.9, 45.7, 1.0):
        put(heartbeat(.8), tk, .45)
    put(tremolo([62, 63], 10.0, 7, 1800), 35.7, .13)
    for tk, n in [(36.6, 50), (38.48, 49), (39.8, 51)]:
        put(piano(midi(n)), tk, .28)
    for k, tk in enumerate(np.arange(41.8, 45.2, .25)):
        put(tick(k % 2 == 0), tk, .22)
    put(shepard(1.6), 43.8, .45)
    put(braam(27, 2.0), 45.3, .45)                # "bribe"

    # ---- freeze 45.9-47.6: near silence, high sine, heartbeat (sfx carries it)
    t = tt(1.8)
    put(np.sin(2 * np.pi * 1975 * t) * env(len(t), .3, .6) * .12, 46.0, 1)

    # ---- sly release 47.6-52.4: plucked low motif
    for k, tk in enumerate(np.arange(47.7, 52.3, .5)):
        put(pluck(midi([38, 41, 45, 44][k % 4]), .6, .5, 7), tk, .35, .3 if k % 2 else -.3)
    put(shepard(1.4), 51.0, .35)

    # ---- fast escape 52.4-59.4
    ostinato(52.45, 59.4, bpm=120, g=.45, start_full=True)
    put(braam(26, 2.4), 53.44, .5)                # SOLD
    put(tremolo([74, 77], 6.0), 53.5, .12)

    # ---- slow silence 59.6-69.2: clock of days, lonely piano, "nothing" hit
    for k, tk in enumerate(np.arange(59.7, 62.2, .5)):
        put(tick(True), tk, .3)
    put(braam(25, 3.5), 62.28, .5)
    for tk, n in [(63.4, 62), (64.9, 61), (66.4, 58), (67.8, 57)]:
        put(piano(midi(n), 3.0), tk, .3)
    put(tremolo([61, 62], 6.0, 6, 1500), 63.3, .1)
    put(shepard(1.6), 67.9, .4)

    # ---- fast round two 69.6-77.4, bigger
    ostinato(69.65, 77.4, bpm=120, g=.5, start_full=True)
    put(tremolo([74, 75, 81], 7.5), 69.7, .15, .3)
    put(braam(26, 2.0), 71.7, .4)
    put(braam(31, 2.4), 77.44, .8)                # police
    put(taiko(1.2), 77.44, .6)

    # ---- finale 78.2-81: wide resolve + last hit on "America"
    put(drone([26, 33, 38, 45], 4.0, .5, 1.5), 78.0, .7)
    put(tremolo([69, 74, 76], 3.0, 9), 78.2, .14)
    put(braam(26, 3.0), 80.28, .9)
    put(taiko(1.3), 80.28, .7)

    out = np.stack([L[:N], R[:N]], 1)
    return out
