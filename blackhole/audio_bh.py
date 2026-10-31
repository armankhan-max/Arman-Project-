"""Soundtrack for the black-hole video: low BGM, ~150 timed SFX, ship/space ambience, ducked under the narrator.

Sound-design notes:
  * BGM sits LOW (about 14-18 dB under the voice) and also ducks when the narrator speaks.
  * Music follows the emotion: dread drone (hook), curious ostinato (science), wonder pads (history),
    a warm theme for Mira, a building ostinato for the spacewalk, then silence on the fade.
  * Silence is a tool: music drops out for the rewind, the SNAP, and the final freeze.

Usage: python audio_bh.py --voice voice.mp3 --out mix.wav [--stems DIR]
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from audio import (SR, Track, tt, lp, hp, bp, noise, midi, nm, pad, pluck, bell_tone, bass, kick, hat, heartbeat,  # noqa
                   whoosh, pop, click, ding, chime_sparkle, buzzer, error_beep, tape_rewind, tape_stop, hit,
                   riser, tick, drop_plink, crickets, fz, CHORDS, cue_tense, cue_curious, cue_night, cue_warm,
                   cue_tension, cue_hope, final_chord, fade_region, load_audio, envelope, edge_env, env_adsr,
                   marimba, gulp, squish)
from scipy import signal  # noqa: E402
from scipy.io import wavfile  # noqa: E402

rng = np.random.default_rng(3)


# ------------------------------------------------------------------ extra SFX
def sub_boom(gain=0.8, dur=2.5):
    t = tt(dur)
    f = 28 + 40 * np.exp(-t * 3)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    return lp(x + 0.3 * lp(noise(dur), 120) * np.exp(-t * 2), 200) * gain


def rumble(dur, gain=0.2, f=60):
    x = lp(noise(dur), f) * 3 + 0.4 * np.sin(2 * np.pi * 31 * tt(dur))
    return x * edge_env(len(x), 0.8) * gain


def creak(dur=1.4, gain=0.3, f0=140, f1=70):
    t = tt(dur)
    f = f0 + (f1 - f0) * t / dur + 6 * np.sin(2 * np.pi * 7 * t)
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t))
    return lp(x, 900) * np.sin(np.pi * t / dur) * gain


def thud(gain=0.6):
    return lp(kick(0.5, 80, 30), 300) * gain


def lower_swoosh(gain=0.25):
    return whoosh(0.45, True, gain)


def rimshot(gain=0.5):
    out = np.zeros(int(1.6 * SR))
    for i, at_ in enumerate((0.0, 0.18)):
        sn = bp(noise(0.2), 900, 5000) * np.exp(-tt(0.2) * 22) + 0.4 * np.sin(2 * np.pi * 190 * tt(0.2)) * np.exp(-tt(0.2) * 30)
        j = int(at_ * SR)
        out[j:j + len(sn)] += sn * 0.8
    k = kick(0.3)
    out[int(0.09 * SR):int(0.09 * SR) + len(k)] += k * 0.6
    cr = hp(noise(1.2), 5000) * np.exp(-tt(1.2) * 3.5)
    j = int(0.36 * SR)
    out[j:j + len(cr)] += cr * 0.5
    return out * gain


def boing(gain=0.35):
    d = 0.8
    t = tt(d)
    f = 220 + 160 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3) * gain


def bloop(gain=0.3):
    d = 0.18
    t = tt(d)
    f = 300 + 900 * t / d
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) * gain


def beep(f=1200, d=0.12, gain=0.2):
    t = tt(d)
    return np.sin(2 * np.pi * f * t) * env_adsr(len(t), 0.005, 0.02, 0.8, 0.03) * gain


def alarm(dur, gain=0.08):
    out = np.zeros(int(dur * SR))
    k = 0.0
    while k < dur - 0.3:
        b = beep(880, 0.18, 1.0)
        j = int(k * SR)
        out[j:j + len(b)] += b
        k += 0.5
    return out * gain


def scribble(dur=0.25, gain=0.2):
    return bp(noise(dur), 1500, 6000) * (0.5 + 0.5 * np.sin(2 * np.pi * 18 * tt(dur))) * edge_env(int(dur * SR), 0.03) * gain


def radar(dur=2.0, gain=0.12):
    out = np.zeros(int(dur * SR))
    for k in np.arange(0, dur - 0.5, 1.0):
        b = beep(1500, 0.4, 1.0) * np.exp(-tt(0.4) * 6)
        j = int(k * SR)
        out[j:j + len(b)] += b
    return out * gain


def thrust(dur=1.2, gain=0.35):
    x = bp(noise(dur), 200, 3000) + lp(noise(dur), 150) * 2
    return x * edge_env(len(x), 0.15) * gain


def slide_whistle(gain=0.25):
    d = 1.3
    t = tt(d)
    f = np.where(t < 0.6, 600 + 900 * t / 0.6, 1500 - 1100 * (t - 0.6) / 0.7)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_adsr(len(t), 0.05, 0.1, 0.9, 0.2) * gain


def freeze_chime(gain=0.3):
    out = np.zeros(int(2.4 * SR))
    for i, m in enumerate((88, 95, 100)):
        b = bell_tone(midi(m), 2.0)
        j = int(i * 0.09 * SR)
        out[j:j + len(b)] += b
    return lp(out, 6000) * gain


def phone_buzz(dur=3.0, gain=0.2):
    t = tt(dur)
    on = ((t % 1.0) < 0.45).astype(float)
    x = signal.square(2 * np.pi * 160 * t) * lp(on, 30)
    return lp(x, 900) * gain


def bad_singing(dur=4.4, gain=0.18):
    notes = [64, 67, 66, 69, 62, 71, 60, 65]
    out = np.zeros(int(dur * SR))
    step = dur / len(notes)
    for i, m in enumerate(notes):
        t = tt(step)
        f = midi(m) * (1 + 0.03 * np.sin(2 * np.pi * 6.5 * t) + 0.02 * rng.uniform(-1, 1))
        x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) + 0.5 * signal.sawtooth(2 * np.pi * np.cumsum(f * 1.01) / SR)
        x = bp(x, 300, 2500) * env_adsr(len(t), 0.03, 0.05, 0.8, 0.08)
        j = int(i * step * SR)
        out[j:j + len(x)] += x
    return out * gain


def breathing(dur, gain=0.06):
    t = tt(dur)
    x = bp(noise(dur), 300, 1800)
    env = np.clip(np.sin(2 * np.pi * t / 3.6), 0, 1) ** 2 + 0.6 * np.clip(np.sin(2 * np.pi * t / 3.6 + np.pi), 0, 1) ** 2
    return x * env * edge_env(len(t), 0.8) * gain


def static_burst(dur=0.35, gain=0.18):
    return bp(noise(dur), 800, 5000) * edge_env(int(dur * SR), 0.02) * gain


def comms_in(gain=0.25):
    out = np.zeros(int(0.6 * SR))
    s = static_burst(0.25, 1.0)
    out[: len(s)] += s * 0.6
    b = beep(1800, 0.08, 1.0)
    out[int(0.25 * SR):int(0.25 * SR) + len(b)] += b
    return out * gain


def snap(gain=0.8):
    d = 0.5
    x = hp(noise(d), 1500) * np.exp(-tt(d) * 35) * 1.5 + lp(kick(d, 300, 80), 2000) * 0.6
    return x * gain


def hatch(gain=0.5):
    x = lp(kick(0.4, 160, 50), 800) * gain
    c_ = click(0.6) * 0.5 * gain
    x[: len(c_)] += c_
    return x


def holo(dur=1.2, gain=0.15):
    t = tt(dur)
    x = np.sin(2 * np.pi * (600 + 400 * t / dur) * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 30 * t))
    return x * edge_env(len(t), 0.2) * gain


def ship_hum(dur, gain=0.05):
    t = tt(dur)
    x = 0.6 * np.sin(2 * np.pi * 55 * t) + 0.3 * np.sin(2 * np.pi * 110 * t) + lp(noise(dur), 250) * 1.5
    return x * edge_env(len(t), 0.6) * gain


def ticks(dur, rate, gain=0.25, slow=False):
    out = np.zeros(int(dur * SR))
    k, step = 0.0, 1.0 / rate
    while k < dur - 0.05:
        b = tick(1.0)
        j = int(k * SR)
        out[j:j + len(b)] += b
        k += step
        if slow:
            step *= 1.18
    return out * gain


# ------------------------------------------------------------------ music cues
def drone(tr, a, b, root="A1", gain=0.5, cluster=True):
    d = b - a
    tr.add(pad(fz([root, "E2"]), d + 1.5, 2.5, 2.0, 0.2), a, gain)
    if cluster:
        tr.add(pad(fz(["A3", "A#3", "E4"]), d + 1.5, 4.0, 2.0, 0.1), a, gain * 0.35)


def space_pad(tr, a, b, gain=0.6):
    cue_night(tr, a, b)


def build_music(dur):
    m = Track(dur)
    drone(m, 0.0, 23.6, gain=0.6)
    cue_curious(m, 26.9, 58.0, bpm=88, gain=0.75)
    space_pad(m, 60.8, 110.7)
    cue_curious(m, 110.9, 120.1, bpm=96, gain=0.6)
    drone(m, 120.1, 131.1, root="D2", gain=0.5)
    cue_curious(m, 131.1, 141.9, bpm=96, gain=0.55)
    cue_hope(m, 141.9, 160.6, build=0.3)
    cue_tense(m, 160.6, 209.3, 0.75, bpm=60)
    cue_warm(m, 209.3, 245.6, bpm=76)
    cue_tense(m, 245.6, 253.2, 0.6, bpm=66)
    cue_tension(m, 257.0, 308.2, bpm=96, gain=0.9)
    m.add(pad(fz(["D3", "F3", "A3", "D4"]), 8.0, 2.0, 3.0, 0.3), 310.6, 0.45)
    final_chord(m, 322.4, ["D3", "F#3", "A3", "D4"], 0.4, 2.5)
    cue_warm(m, 323.4, 352.9, bpm=64)
    drone(m, 352.9, 369.0, gain=0.55)
    cue_curious(m, 370.1, 409.0, bpm=96, gain=0.6)
    cue_hope(m, 409.0, 420.6, build=0.5)
    final_chord(m, 420.6, ["D3", "F#3", "A3", "D4"], 0.45, 2.2)
    x = m.stereo(int(dur * SR))
    x = fade_region(x, 23.6, 26.7, 0.3)
    x = fade_region(x, 253.4, 256.6, 0.15)
    x = fade_region(x, 369.0, 370.1, 1.2)
    return x


# ------------------------------------------------------------------ SFX timeline
def build_sfx(dur, cuts):
    s = Track(dur)
    E = []

    def ev(at_, fn, g=1.0, pan=0.0):
        E.append((at_, fn, g, pan))

    for ct in cuts:
        ev(ct - 0.3, lambda: whoosh(0.5, True, 0.18))
    # HOOK
    ev(0.0, lambda: sub_boom(0.9))
    ev(0.0, lambda: hit(0.6))
    ev(0.0, lambda: rumble(13.0, 0.35))
    ev(4.3, lambda: thud(0.6), pan=-0.2)
    ev(4.55, lambda: thud(0.6), pan=0.2)
    ev(7.7, lambda: creak(2.4, 0.22))
    ev(10.3, lambda: creak(2.2, 0.22, 200, 110))
    ev(13.0, lambda: ship_hum(6.2, 1.0))
    for st in (15.9, 17.5):
        ev(st, lambda: pop(500, 0.25))
    ev(18.2, lambda: freeze_chime(0.35))
    ev(19.3, lambda: ticks(4.3, 6, 0.3), pan=-0.5)
    ev(19.3, lambda: heartbeat(0.4), pan=0.4)
    ev(21.2, lambda: freeze_chime(0.2), pan=0.5)
    ev(23.6, lambda: tape_rewind(2.6, 0.35))
    ev(25.2, lambda: pop(700, 0.3))
    # MEET KAI
    ev(26.7, lambda: ship_hum(3.9, 1.0))
    ev(27.0, lambda: lower_swoosh())
    ev(29.3, lambda: rimshot(0.45))
    ev(31.4, lambda: pop(600, 0.25))
    # TIDAL
    ev(34.6, lambda: pop(500, 0.3))
    ev(35.0, lambda: pop(650, 0.25))
    ev(41.0, lambda: pop(500, 0.25))
    ev(41.9, lambda: riser(1.0, 0.18))
    ev(42.6, lambda: hit(0.55))
    ev(42.6, lambda: sub_boom(0.5))
    ev(48.6, lambda: pop(700, 0.3))
    # HORIZON
    ev(50.6, lambda: riser(0.9, 0.12))
    for st in (54.3, 55.2, 56.6):
        ev(st, lambda: whoosh(1.2, False, 0.2))
        ev(st + 1.2, lambda: buzzer(0.12))
    ev(53.1, lambda: hit(0.4))
    ev(58.4, lambda: sub_boom(0.9))
    ev(58.4, lambda: hit(0.6))
    # WINDOW
    ev(60.8, lambda: ship_hum(1.6, 1.0))
    ev(62.3, lambda: whoosh(0.7, True, 0.25))
    ev(63.4, lambda: rumble(6.0, 0.2, 45))
    ev(67.6, lambda: pop(450, 0.25))
    # SCALE
    for i in range(10):
        ev(69.6 + i * 0.1, lambda i=i: pop(500 + 60 * i, 0.18))
    ev(72.4, lambda: riser(0.8, 0.12))
    ev(74.9, lambda: whoosh(0.8, False, 0.3))
    ev(76.5, lambda: ticks(2.6, 4, 0.2))
    # YUKI
    ev(79.4, lambda: ship_hum(7.7, 1.0))
    ev(79.6, lambda: lower_swoosh())
    for i in range(3):
        ev(80.0 + i * 0.35, lambda: click(0.35))
    ev(81.6, lambda: alarm(5.4, 0.07))
    for i in range(4):
        ev(83.0 + i * 0.25, lambda: scribble(0.18, 0.2))
    ev(84.0, lambda: scribble(0.3, 0.2))
    for i in range(4):
        ev(85.2 + i * 0.3, lambda: click(0.3))
    # DANGER MAP
    ev(87.4, lambda: radar(4.0, 0.12))
    ev(90.7, lambda: thrust(2.0, 0.2), pan=0.5)
    ev(95.2, lambda: pop(600, 0.25))
    # ROPE
    ev(99.8, lambda: creak(1.6, 0.2))
    ev(101.6, lambda: creak(1.6, 0.2, 180, 90))
    ev(102.3, lambda: pop(500, 0.25))
    ev(107.6, lambda: hit(0.55))
    ev(109.0, lambda: boing(0.35))
    # COFFEE / PROBE
    ev(110.7, lambda: ship_hum(31.2, 1.0))
    ev(110.9, lambda: lower_swoosh())
    ev(112.1, lambda: pop(400, 0.25))
    ev(113.4, lambda: whoosh(1.2, True, 0.12))
    ev(115.9, lambda: bloop(0.3))
    ev(116.4, lambda: bloop(0.25))
    ev(118.6, lambda: beep(1000, 0.15, 0.3))
    ev(120.1, lambda: thud(0.5))
    ev(120.1, lambda: whoosh(1.0, False, 0.3))
    ev(121.0, lambda: ticks(9.0, 5, 0.22, slow=True))
    ev(125.2, lambda: rumble(3.0, 0.12, 40))
    ev(129.5, lambda: freeze_chime(0.35))
    ev(131.1, lambda: pop(650, 0.25))
    ev(138.5, lambda: slide_whistle(0.22))
    ev(140.2, lambda: pop(500, 0.2))
    # HISTORY
    ev(142.3, lambda: hit(0.45))
    ev(142.3, lambda: chime_sparkle(0.2))
    ev(149.5, lambda: hit(0.45))
    ev(149.5, lambda: chime_sparkle(0.2))
    ev(154.3, lambda: pop(500, 0.25))
    ev(158.1, lambda: whoosh(0.8, True, 0.25))
    # LENA
    ev(160.6, lambda: ship_hum(6.9, 1.0))
    ev(162.7, lambda: lower_swoosh())
    for st in (167.5, 169.2, 170.6):
        ev(st, lambda: sub_boom(0.6, 2.0))
    for i in range(6):
        ev(171.8 + i * 0.6, lambda: whoosh(1.5, False, 0.1), pan=-0.4 + 0.16 * i)
    ev(171.9, lambda: rumble(8.0, 0.18, 50))
    # BODY LIES
    ev(180.5, lambda: hit(0.4))
    for st in (186.8, 187.9, 188.9):
        ev(st, lambda: pop(500, 0.25))
        ev(st + 0.15, lambda: buzzer(0.07))
    ev(193.1, lambda: creak(3.0, 0.18))
    ev(195.6, lambda: hit(0.35))
    ev(198.9, lambda: bloop(0.3))
    for i in range(3):
        ev(199.6 + i * 0.7, lambda i=i: pop(600 + 100 * i, 0.22))
    ev(202.7, lambda: ship_hum(6.6, 1.0))
    ev(204.4, lambda: pop(500, 0.2))
    ev(207.0, lambda: rimshot(0.25))
    ev(208.1, lambda: crickets(1.6, 0.06))
    # MIRA
    ev(209.4, lambda: hit(0.3))
    ev(212.0, lambda: phone_buzz(3.6, 0.15))
    for i in range(9):
        ev(216.0 + i * 0.3, lambda: tick(0.3))
    ev(220.8, lambda: pop(500, 0.22))
    ev(222.8, lambda: ding(1318.5, 0.18))
    ev(225.4, lambda: pop(400, 0.22))
    ev(231.3, lambda: pop(500, 0.18))
    ev(234.0, lambda: bad_singing(4.4, 0.16))
    ev(238.5, lambda: pop(600, 0.2))
    ev(243.7, lambda: hit(0.3))
    # SPACEWALK
    ev(245.6, lambda: breathing(21.0, 0.07))
    ev(246.0, lambda: comms_in(0.15))
    for i in range(4):
        ev(248.6 + i * 0.6, lambda: click(0.3), pan=0.3)
    ev(254.0, lambda: snap(0.85))
    ev(254.2, lambda: whoosh(0.4, True, 0.3))
    x = 255.0
    while x < 266.0:
        ev(x, lambda: heartbeat(0.35))
        x += 0.95
    ev(266.7, lambda: comms_in(0.3))
    ev(268.4, lambda: static_burst(0.2, 0.1))
    ev(270.4, lambda: comms_in(0.3))
    ev(272.7, lambda: alarm(4.4, 0.06))
    ev(277.2, lambda: hit(0.5))
    ev(279.0, lambda: beep(700, 0.25, 0.2))
    ev(281.1, lambda: pop(500, 0.2))
    ev(283.6, lambda: hit(0.5))
    ev(283.6, lambda: sub_boom(0.5))
    # RESCUE
    ev(284.8, lambda: thrust(2.0, 0.35))
    ev(286.2, lambda: thud(0.5))
    ev(291.3, lambda: whoosh(0.8, True, 0.25), pan=0.5)
    ev(291.3, lambda: whoosh(0.8, True, 0.25), pan=-0.5)
    ev(294.9, lambda: pop(500, 0.25))
    ev(297.3, lambda: whoosh(0.6, True, 0.25))
    ev(302.0, lambda: pop(500, 0.25), pan=-0.5)
    ev(304.5, lambda: pop(650, 0.25), pan=0.5)
    ev(308.2, lambda: hit(0.45))
    ev(312.2, lambda: comms_in(0.15))
    ev(317.0, lambda: thrust(1.4, 0.5))
    ev(317.0, lambda: sub_boom(0.8))
    ev(317.0, lambda: hit(0.5))
    ev(317.4, lambda: whoosh(2.0, False, 0.25), pan=-0.5)
    ev(320.7, lambda: hatch(0.45), pan=-0.6)
    ev(322.4, lambda: ding(1568, 0.25))
    # LAST MESSAGE
    ev(323.4, lambda: rumble(29.5, 0.22, 45))
    ev(326.6, lambda: riser(1.6, 0.12))
    ev(332.5, lambda: holo(1.4, 0.15))
    ev(332.8, lambda: beep(1400, 0.1, 0.15))
    ev(344.3, lambda: beep(900, 0.18, 0.2))
    ev(349.0, lambda: whoosh(1.2, True, 0.25))
    for i in range(3):
        ev(349.3 + i * 0.25, lambda: beep(1600, 0.07, 0.15))
    ev(351.1, lambda: chime_sparkle(0.18))
    # FINALE
    ev(352.9, lambda: rumble(4.5, 0.4))
    ev(353.2, lambda: creak(3.5, 0.22))
    ev(357.4, lambda: ship_hum(8.0, 1.0))
    ev(360.6, lambda: rumble(2.0, 0.15, 40))
    ev(362.4, lambda: freeze_chime(0.35))
    ev(365.4, lambda: ticks(3.6, 6, 0.25), pan=-0.5)
    x = 365.4
    while x < 368.6:
        ev(x, lambda: heartbeat(0.3), pan=0.3)
        x += 1.0 + (x - 365.4) * 0.3
    # FACTS + OUTRO
    ev(370.1, lambda: hit(0.4))
    for st in (372.4, 376.3):
        ev(st, lambda: pop(500, 0.25))
        ev(st + 0.3, lambda: ding(1568, 0.18))
    ev(384.2, lambda: pop(500, 0.2))
    ev(387.1, lambda: buzzer(0.2))
    ev(387.1, lambda: hit(0.4))
    ev(388.4, lambda: pop(500, 0.2))
    ev(390.8, lambda: hit(0.3))
    for st in (393.7, 395.8, 400.6, 405.8):
        ev(st, lambda: pop(550, 0.22))
    ev(409.2, lambda: riser(1.4, 0.15))
    ev(410.7, lambda: sub_boom(0.6))
    ev(416.4, lambda: pop(500, 0.25))
    for i in range(3):
        ev(418.0 + i * 0.35, lambda i=i: pop(550 + 80 * i, 0.22))
    ev(420.5, lambda: pop(500, 0.25))
    ev(421.0, lambda: click(0.5))
    ev(421.6, lambda: click(0.6))
    ev(421.7, lambda: ding(1760, 0.25))
    for at_, fn, g, pan in E:
        s.add(fn(), at_, g, pan)
    return s.stereo(int(dur * SR))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stems")
    a = ap.parse_args()
    sys.path.insert(0, HERE)
    from scenes_bh import CUTS

    voice = load_audio(a.voice)
    dur = len(voice) / SR
    music = build_music(dur)
    fx = build_sfx(dur, CUTS)
    n = min(len(voice), len(music), len(fx))
    voice, music, fx = voice[:n], music[:n], fx[:n]

    def norm(x, peak):
        m = np.max(np.abs(x)) or 1.0
        return x / m * peak

    music = norm(music, 1.0)
    env = envelope(voice)
    env = env / (np.percentile(env, 95) + 1e-9)
    duck = lp(1.0 - 0.6 * np.clip(env, 0, 1), 6, 1)
    music *= (0.2 * duck)[:, None]          # LOW background music, as requested
    fx = norm(fx, 0.5)
    v = voice / (np.max(np.abs(voice)) or 1.0) * 0.92
    mix = np.stack([v, v], axis=1) + music + fx
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    if a.stems:
        os.makedirs(a.stems, exist_ok=True)
        for name, x in (("music", music), ("sfx", fx)):
            wavfile.write(os.path.join(a.stems, f"{name}.wav"), SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
    wavfile.write(a.out, SR, (np.clip(mix, -1, 1) * 32767).astype(np.int16))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
