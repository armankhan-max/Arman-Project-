"""Soundtrack for "The Loop": original synthesized score + timed SFX, ducked under the voice, -14 LUFS.

Score (A minor, emotional documentary style):
  hook      : sub drone + clock ticks counting down, BRAAM on "loop", silence + low piano under the title
  the loop  : felt-piano ostinato Am-F-C-G (the same four chords forever = the loop itself)
  cycle     : piano + pulsing pluck + heartbeat, accelerating riser as the cycle spins
  break free: escalating impacts on DAY / MONTH / YEAR
  slow down : tape-stop into silence, then airy pads + bells for metacognition
  split sec : everything drops out, heartbeat + shimmer freeze
  ending    : piano returns, lifts to F major / C major, glass-break shimmer on "breaking", final chord
Usage: python audio_loop.py --voice voice.wav --out mix.wav
"""
import argparse
import os
import subprocess
import sys

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "..", "video"))
from audio import (SR, Track, tt, lp, hp, bp, noise, midi, nm, pad, pluck, bell_tone, kick, whoosh, pop, click,  # noqa
                   ding, tick, hit, riser, heartbeat, tape_stop, env_adsr, envelope, load_audio, marimba)
sys.path.insert(0, HERE)
import loop_scenes as S  # noqa: E402

rng = np.random.default_rng(5)


# ------------------------------------------------------------------ instruments
def piano(f, dur=3.0, vel=0.7):
    t = tt(dur)
    x = np.zeros_like(t)
    B = 0.0004
    for k in range(1, 10):
        fk = f * k * np.sqrt(1 + B * k * k)
        if fk > 9000:
            break
        amp = (0.6 ** (k - 1)) * (1 + 0.3 * vel)
        x += amp * np.sin(2 * np.pi * fk * t + k * 0.7) * np.exp(-t * (0.9 + k * 0.55 + f / 900))
    ham = lp(noise(0.03), 2500) * np.exp(-tt(0.03) * 120) * 0.15
    x[: len(ham)] += ham
    x *= env_adsr(len(t), 0.004, 0.05, 1.0, 0.3)
    return lp(x, 2600 + 2000 * vel) * 0.35 * vel


def braam(dur=3.0, root="A1", gain=0.8):
    t = tt(dur)
    x = np.zeros_like(t)
    for m in (nm(root), nm(root) + 12, nm(root) + 19):
        for det in (-0.006, 0, 0.007):
            x += signal.sawtooth(2 * np.pi * midi(m) * (1 + det) * t)
    sweep = 300 + 1600 * np.exp(-t * 1.4)
    out = np.zeros_like(x)
    seg = 2048
    for i in range(0, len(x), seg):
        out[i:i + seg] = lp(x[max(0, i - 4096):i + seg], sweep[i])[-len(x[i:i + seg]):]
    e = np.minimum(1, t / 0.05) * np.exp(-t * 0.9)
    return out * e * gain * 0.12 + sub_boom(gain * 0.9, dur)


def sub_boom(gain=0.8, dur=2.5):
    t = tt(dur)
    f = 30 + 45 * np.exp(-t * 4)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.5)
    return lp(x + 0.25 * lp(noise(dur), 150) * np.exp(-t * 3), 220) * gain


def drone(dur, root="A1", gain=0.5):
    t = tt(dur)
    f = midi(nm(root))
    x = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t + 1) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
         + 0.15 * lp(noise(dur), 200))
    x *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * t)
    e = np.minimum(1, np.minimum(t / 2.0, (dur - t) / 1.5)).clip(0)
    return x * e * gain * 0.4


def shimmer(dur=3.0, gain=0.3):
    out = np.zeros(int(dur * SR))
    for i, m in enumerate((81, 84, 88, 93, 96, 100)):
        b = bell_tone(midi(m), dur - i * 0.12) * (0.85 ** i)
        j = int(i * 0.07 * SR)
        out[j:j + len(b)] += b[: len(out) - j]
    return out * gain


def exhale(gain=0.3):
    d = 1.6
    t = tt(d)
    return bp(noise(d), 400, 2500) * np.sin(np.pi * t / d) ** 2 * gain


def paper(gain=0.35):
    d = 0.25
    t = tt(d)
    return (bp(noise(d), 1500, 7000) * np.exp(-t * 25) + kick(d, 160, 70) * 0.4 * np.exp(-t * 20)) * gain


def marker(gain=0.2, dur=0.5):
    t = tt(dur)
    x = bp(noise(dur), 2500, 6000) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t))
    return x * np.sin(np.pi * t / dur) * gain


def sizzle(dur, gain=0.12):
    x = hp(noise(dur), 3000) * (0.5 + 0.5 * (rng.random(int(dur * SR)) > 0.997).astype(float).cumsum() % 2)
    return x * np.minimum(1, np.minimum(tt(dur) / 0.1, (dur - tt(dur)) / 0.1)) * gain


def pour(dur=0.9, gain=0.2):
    t = tt(dur)
    return bp(noise(dur), 300, 1600) * (0.7 + 0.3 * np.sin(2 * np.pi * 9 * t)) * np.sin(np.pi * t / dur) * gain


def alarm(dur=1.6, gain=0.35):
    t = tt(dur)
    gate = (np.sin(2 * np.pi * 8 * t) > 0) * ((t % 0.5) < 0.35)
    x = (np.sin(2 * np.pi * 2093 * t) + 0.5 * np.sin(2 * np.pi * 2637 * t)) * gate
    return lp(x, 6000) * gain * np.minimum(1, (dur - t) / 0.1)


def notif(gain=0.3):
    a = bell_tone(1568, 0.6)
    b = bell_tone(2093, 0.6)
    out = np.zeros(int(0.8 * SR))
    out[: len(a)] += a
    out[int(0.09 * SR):int(0.09 * SR) + len(b)] += b
    return out * gain


def glass(gain=0.4):
    d = 2.0
    t = tt(d)
    x = hp(noise(d), 3000) * np.exp(-t * 8) * 0.6
    for f in (2900, 3700, 4500, 5300, 6100):
        x += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t * rng.uniform(3, 7)) * 0.2
    return x * gain


def reverse_swell(dur=1.5, gain=0.3):
    t = tt(dur)
    x = hp(noise(dur), 2000) * (t / dur) ** 3
    return x * gain


def beep(gain=0.2):
    t = tt(0.12)
    return np.sin(2 * np.pi * 1200 * t) * gain * np.minimum(1, (0.12 - t) / 0.02)


# ------------------------------------------------------------------ score
CH = {"Am": ["A2", "E3", "A3", "C4", "E4"], "F": ["F2", "C3", "F3", "A3", "C4"], "C": ["C3", "G3", "C4", "E4", "G4"],
      "G": ["G2", "D3", "G3", "B3", "D4"], "Fmaj7": ["F2", "C3", "E3", "A3", "C4"], "Csus": ["C3", "G3", "C4", "D4", "G4"]}


def piano_loop(m, a, b, bpm=72, prog=("Am", "F", "C", "G"), vel=0.55, arp=True, gain=1.0):
    beat = 60 / bpm
    t = a
    i = 0
    while t < b - 0.2:
        ch = CH[prog[(i // 4) % len(prog)]]
        if i % 4 == 0:
            m.add(piano(midi(nm(ch[0])), 4 * beat + 1.5, vel * 0.9), t, gain)
            m.add(piano(midi(nm(ch[1])), 4 * beat + 1.5, vel * 0.6), t, gain * 0.7)
        if arp:
            seq = [2, 3, 4, 3]
            n = ch[seq[i % 4]]
            m.add(piano(midi(nm(n)), 2.2, vel * (0.75 if i % 4 else 0.9)), t + 0.01 * (i % 3), gain * 0.55,
                  pan=0.25 * np.sin(i))
        t += beat
        i += 1


def fade(x, a, b, f=0.6):
    """Silence x between a and b with fades."""
    n = len(x)
    g = np.ones(n)
    ia, ib = int(a * SR), int(b * SR)
    fa = int(f * SR)
    g[max(0, ia):min(n, ib)] = 0
    if ia - fa > 0:
        g[ia - fa:ia] = np.linspace(1, 0, fa)
    if ib + fa < n:
        g[ib:ib + fa] = np.linspace(0, 1, fa)
    return x * g[:, None]


def build_music(dur):
    T, E, wt = S.T, S.E, S.wt
    m = Track(dur)
    # hook
    m.add(drone(T(2) + 0.5, "A1", 0.6), 0.0)
    m.add(pad([midi(nm("E5")), midi(nm("A5"))], T(2), 2.0, 1.0, 0.2), 0.0, 0.25)
    # title card: low piano A + Am chord
    ttl = E(2) + 0.25
    m.add(piano(midi(nm("A1")), 5.0, 0.8), ttl + 0.4, 1.0)
    m.add(piano(midi(nm("A2")), 5.0, 0.6), ttl + 0.4, 0.8)
    m.add(pad([midi(nm(n)) for n in ("A2", "E3", "C4")], T(3) - ttl + 0.5, 1.5, 1.5, 0.3), ttl, 0.5)
    # the loop: piano ostinato through night + morning + droste
    piano_loop(m, T(3) - 0.2, T(9) - 0.3, 72, vel=0.5)
    m.add(drone(T(9) - T(8) + 0.5, "A1", 0.35), T(8) - 0.2)
    # cycle: piano + pulse
    piano_loop(m, T(9), T(18), 80, vel=0.5, gain=0.85)
    beat = 60 / 80
    t = T(9)
    while t < T(18):
        m.add(pluck(midi(nm("A2")), 0.4, 0.4, 8), t, 0.35)
        m.add(pluck(midi(nm("A3")), 0.3, 0.3, 10), t + beat / 2, 0.18)
        t += beat
    m.add(drone(T(14) - T(13), "D2", 0.5), T(13))
    # spin: riser
    sp = wt(17, "trapping")
    m.add(riser(T(18) - sp, 0.7), sp)
    # break free: tension drone + building pulse
    m.add(drone(T(22) - T(18) + 0.5, "A1", 0.7), T(18))
    t, step = T(18), 0.75
    while t < T(22):
        m.add(kick(0.4, 70, 40, 0.5), t)
        t += step
        step = max(0.32, step * 0.97)
    # slow down -> metacognition: airy pads + bells
    m.add(pad([midi(nm(n)) for n in ("F3", "A3", "C4", "E4")], T(25) - T(22) + 2, 2.5, 2.5, 0.25, 0.5),
          wt(22, "slow") + 0.8, 0.5)
    for k, n in enumerate(("E5", "A5", "C6", "E6", "A5", "G5", "E5", "C6")):
        m.add(bell_tone(midi(nm(n)), 2.5), T(23) + 0.4 + k * 1.1, 0.16, pan=0.4 * np.sin(k))
    # examine + decisions: curious marimba
    t = T(25)
    seq = ("A4", "C5", "E5", "D5", "C5", "E5", "G5", "E5")
    k = 0
    while t < T(29):
        m.add(marimba(midi(nm(seq[k % 8])), 0.6), t, 0.3, pan=0.3 if k % 2 else -0.3)
        if k % 4 == 0:
            m.add(pluck(midi(nm("A2")), 0.8, 0.4, 5), t, 0.3)
        t += 0.42
        k += 1
    m.add(pad([midi(nm(n)) for n in ("A2", "E3", "A3")], T(29) - T(25), 1.5, 1.5, 0.3), T(25), 0.3)
    # autopilot: mechanical loop
    t = T(29)
    while t < T(31):
        m.add(tick(0.6), t)
        m.add(pluck(midi(nm("A2")), 0.4, 0.3, 9), t, 0.28)
        t += 0.5
    m.add(drone(T(31) - T(29), "A1", 0.5), T(29))
    # attention / split second: thin pad, then nothing but heartbeat
    m.add(pad([midi(nm(n)) for n in ("E4", "A4", "B4")], T(32) - T(31) + 1, 1.5, 1.0, 0.2, 0.3), T(31), 0.4)
    # the choice + ending: piano returns, then lifts
    piano_loop(m, T(33), T(35), 70, prog=("Am", "F", "C", "G"), vel=0.55)
    piano_loop(m, T(35), E(36) + 2.0, 70, prog=("F", "C", "G", "Am"), vel=0.6)
    m.add(pad([midi(nm(n)) for n in ("F3", "A3", "C4", "E4", "G4")], 6, 1.5, 3.0, 0.4), wt(36, "breaking"), 0.6)
    fin = E(36) + 0.6
    for n in ("C2", "C3", "G3", "C4", "E4", "G4"):
        m.add(piano(midi(nm(n)), 6.0, 0.7), fin, 0.8)
    m.add(pad([midi(nm(n)) for n in ("C3", "G3", "C4", "E4")], 5.0, 0.8, 3.0, 0.3), fin, 0.5)
    x = m.stereo(int(dur * SR))
    # silences (silence is a sound effect)
    x = fade(x, ttl - 0.05, ttl + 0.35, 0.05)
    x = fade(x, wt(32, "split") - 0.25, T(33) - 0.3, 0.2)
    sd = wt(22, "slow")
    x = fade(x, sd + 0.35, sd + 0.8, 0.3)
    return x


def build_sfx(dur):
    T, E, wt = S.T, S.E, S.wt
    s = Track(dur)

    def add(at, x, g=1.0, pan=0.0):
        s.add(x, at, g, pan)

    # hook: countdown ticks + whooshes on words
    for k in range(int(T(1) - wt(0, "three")) + 1):
        add(wt(0, "three") + k, tick(0.5), 1.0, 0.2)
    add(wt(0, "you") - 0.05, whoosh(0.35, True, 0.35))
    add(wt(0, "never"), hit(0.7))
    add(wt(0, "never"), braam(2.5, "A1", 0.5))
    add(T(1), reverse_swell(0.6, 0.15))
    # INFINITE LOOP
    add(wt(2, "infinite") - 0.05, whoosh(0.4, True, 0.35))
    add(wt(2, "loop"), braam(4.0, "A1", 1.0))
    add(E(2) + 0.25, sub_boom(0.6, 3.0))
    add(E(2) + 0.6, shimmer(3.0, 0.15))
    # night: promises
    for i in range(3):
        add(wt(3, "promises") + 0.25 + i * 0.45, pop(700 + i * 120, 0.25))
    add(wt(4, "tomorrow") - 0.1, whoosh(0.4, False, 0.3))
    add(wt(4, "tomorrow") + 0.3, kick(0.4, 140, 60, 0.6))  # stamp
    add(wt(4, "tomorrow") + 0.3, paper(0.4))
    # morning
    add(wt(5, "comes") - 0.1, alarm(1.6, 0.35))
    seg = 0.95
    i = 0
    tcur = T(6)
    while tcur < T(8) - 0.2:
        add(tcur, whoosh(0.22, True, 0.18))
        kind = i % 3
        if kind == 0:
            add(tcur, sizzle(seg, 0.1))
        elif kind == 1:
            add(tcur, pour(0.9, 0.18))
        else:
            add(tcur + 0.2, click(0.25))
        tcur += seg
        i += 1
    # droste
    add(wt(8, "trap") - 0.05, hit(0.45))
    add(T(8), reverse_swell(1.5, 0.15))
    # cycle cards
    for (st, g) in ((wt(9, "difficult") - 0.1, 0.5), (wt(12, "discomfort") - 0.1, 0.5)):
        add(st + 0.35, paper(g))
    add(wt(10, "book"), paper(0.35))
    add(wt(11, "project"), paper(0.35))
    add(T(12) + 0.1, marker(0.18))
    add(wt(13, "boredom"), whoosh(0.3, True, 0.2))
    add(wt(13, "frustration"), hit(0.35))
    add(wt(13, "fear"), sub_boom(0.6, 2.5))
    add(wt(14, "picking") - 0.05, click(0.35))
    add(wt(14, "picking") + 0.3, notif(0.25))
    add(wt(14, "avoid") + 0.3, paper(0.35))
    add(wt(15, "relief"), exhale(0.25))
    add(wt(15, "relief") + 0.3, paper(0.3))
    add(wt(16, "teaches") - 0.2, marker(0.2))
    add(wt(16, "brain") - 0.1, pop(500, 0.3))
    sp = wt(17, "trapping")
    tk, step = sp, 0.5
    while tk < T(18) - 0.2:
        add(tk, tick(0.45))
        tk += step
        step = max(0.06, step * 0.9)
    # break free
    add(wt(18, "break"), whoosh(0.5, True, 0.25))
    for i, k in enumerate((19, 20, 21)):
        add(T(k), hit(0.5 + 0.15 * i))
        add(T(k), sub_boom(0.4 + 0.25 * i, 2.0))
        add(T(k) - 0.15, whoosh(0.25, True, 0.25))
    # slow down: tape stop
    add(wt(22, "slow") + 0.2, tape_stop(0.4))
    add(wt(22, "recognize"), shimmer(2.5, 0.12))
    # metacognition: letters + whoosh
    add(wt(23, "metacognition") - 0.3, reverse_swell(0.35, 0.2))
    add(wt(23, "metacognition"), shimmer(3.0, 0.18))
    add(T(24), whoosh(0.8, True, 0.18))
    add(wt(24, "your", 1), pop(800, 0.2))
    # examine
    for i in range(3):
        add(T(26) + 0.1 + i * 0.5, pop(600 + i * 90, 0.18))
    add(wt(26, "examine") - 0.3, whoosh(0.5, False, 0.2))
    # decisions: icon pops (thinned), counter
    for i in range(0, 160, 6):
        add(wt(27, "hundreds") + i * 0.022, pop(900 + (i * 37) % 600, 0.07), 1.0, ((i % 16) - 8) / 10)
    add(wt(28, "breakfast") - 0.1, sizzle(1.4, 0.1))
    add(wt(28, "work") - 0.25, click(0.3))
    # autopilot
    for k in range(3):
        add(wt(29, "automatic") + k * 0.18, beep(0.12))
    for i in range(4):
        add(T(30) + i * 0.25 + 0.2, click(0.25))
    # split second
    add(wt(31, "attention"), shimmer(2.0, 0.12))
    tf = wt(32, "split")
    add(T(32), whoosh(1.2, True, 0.2))
    add(tf - 0.6, reverse_swell(0.4, 0.3))
    add(tf - 0.2, hit(0.5))
    add(tf - 0.2, shimmer(3.0, 0.2))
    for k in range(4):
        add(tf + 0.2 + k * 0.95, heartbeat(0.5))
    # choice
    add(wt(33, "choice") - 0.1, whoosh(0.5, True, 0.3))
    add(wt(33, "choice"), kick(0.6, 90, 40, 0.5))
    # step + break
    add(wt(35, "step"), kick(0.3, 120, 60, 0.35))
    add(wt(36, "breaking"), glass(0.5))
    add(wt(36, "breaking"), shimmer(3.5, 0.25))
    add(wt(36, "breaking"), sub_boom(0.5, 3.0))
    add(E(36) + 0.6, whoosh(1.0, True, 0.2))
    return s.stereo(int(dur * SR))


def room_tone(dur):
    x = lp(noise(dur), 400) * 0.6 + hp(lp(noise(dur), 3000), 800) * 0.05
    return np.stack([x, np.roll(x, 2000)], axis=1)


def reverb(x, secs=2.2, wet=0.25):
    n = int(secs * SR)
    t = np.arange(n) / SR
    out = x.copy()
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-t * 3.2)
        ir = lp(ir, 5000)
        ir[0] = 0
        out[:, ch] = x[:, ch] + wet * signal.fftconvolve(x[:, ch], ir)[: len(x)] / np.sqrt(np.sum(ir ** 2)) * 0.3
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    voice = load_audio(a.voice)
    dur = S.END
    n = int(dur * SR)
    voice = np.pad(voice, (0, max(0, n - len(voice))))[:n]
    music = reverb(build_music(dur), 2.6, 0.45)
    fx = reverb(build_sfx(dur), 1.4, 0.15)
    amb = room_tone(dur)

    def norm(x, peak):
        return x / (np.max(np.abs(x)) or 1.0) * peak

    music = norm(music, 1.0)
    env = envelope(voice)
    env = env / (np.percentile(env, 95) + 1e-9)
    duck = lp(1.0 - 0.5 * np.clip(env, 0, 1), 6, 1)
    music *= (0.30 * duck)[:, None]
    fx = norm(fx, 0.6)
    amb = norm(amb, 0.015)
    # voice: gentle presence EQ + warmth
    v = voice / (np.max(np.abs(voice)) or 1.0)
    v = v + 0.25 * bp(v, 2500, 5000) - 0.15 * lp(v, 120)
    v = v / np.max(np.abs(v)) * 0.9
    mix = np.stack([v, v], axis=1) + music + fx + amb
    end_fade = np.clip((dur - np.arange(n) / SR) / 1.5, 0, 1)
    mix *= end_fade[:, None]
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    raw = (mix.astype(np.float32)).tobytes()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", a.out], input=raw, check=True)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
