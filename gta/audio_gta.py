"""Soundtrack for the GTA 6 buying-guide video: original synthwave BGM + ~260 synced SFX + voice.

Everything is synthesized (no samples), so it is original and royalty-free.
SFX cue times come from scenes_gta.SFX, which is built from the voice's word timestamps.

Usage:
  python audio_gta.py --voice voice.mp3 --out mix.wav
"""
import argparse
import os
import subprocess
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "video"))
import audio as A  # noqa: E402
from audio import SR, tt, lp, hp, bp, env_adsr, Track, midi  # noqa: E402
import scenes_gta as S  # noqa: E402

rng = np.random.default_rng(23)


def noise(d):
    return rng.standard_normal(int(d * SR))


def saw(f, d):
    t = tt(d)
    ph = np.cumsum(np.full(len(t), f) if np.isscalar(f) else f) / SR
    return 2 * (ph % 1.0) - 1


def sq(f, d, duty=0.5):
    t = tt(d)
    ph = (np.cumsum(np.full(len(t), f)) / SR) % 1.0
    return np.where(ph < duty, 1.0, -1.0)


def fade(x, a=0.005, r=0.05):
    n = len(x)
    e = np.ones(n)
    A_ = min(n, int(a * SR))
    R_ = min(n, int(r * SR))
    if A_:
        e[:A_] = np.linspace(0, 1, A_)
    if R_:
        e[-R_:] *= np.linspace(1, 0, R_)
    return x * e


def sweep(f0, f1, d, kind="sin"):
    t = tt(d)
    f = f0 * (f1 / f0) ** (t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) if kind == "sin" else signal.sawtooth(ph)


def ov(*parts):
    """Mix (array, offset_seconds) pairs into one buffer long enough for all."""
    n = max(int(o * SR) + len(x) for x, o in parts)
    out = np.zeros(n)
    for x, o in parts:
        i = int(o * SR)
        out[i:i + len(x)] += x
    return out


# ------------------------------------------------------------------ SFX library
def sfx_boom(d=2.5):
    t = tt(d)
    x = A.kick(d, 70, 28, 1.4) + lp(noise(d), 200) * np.exp(-t * 2.5) * 0.9
    x += lp(noise(d), 3000) * np.exp(-t * 18) * 0.3
    return x


def sfx_slam():
    d = 0.9
    t = tt(d)
    x = A.kick(d, 120, 40, 1.2) + bp(noise(d), 200, 3000) * np.exp(-t * 14) * 0.8
    x += sweep(900, 120, d) * np.exp(-t * 9) * 0.25
    return x


def sfx_hit_low():
    return A.hit(1.0) + sweep(120, 40, 1.2) * np.exp(-tt(1.2) * 3) * 0.4


def sfx_riser(dur=1.5):
    return A.riser(dur, 1.0)


def sfx_riser_rev(dur=1.2):
    x = A.riser(dur, 1.0)
    return x[::-1] * 0.8


def sfx_whoosh():
    return A.whoosh(0.5, True, 1.0)


def sfx_swoosh_big():
    return np.concatenate([A.whoosh(0.6, True, 1.2), A.whoosh(0.6, False, 1.0)])


def sfx_drop_whoosh():
    return A.whoosh(0.5, False, 1.0)


def sfx_crowd(dur=2.5, angry=False):
    t = tt(dur)
    x = np.zeros_like(t)
    for k in range(10):
        f0 = rng.uniform(140, 320) * (1.3 if angry else 1.0)
        vib = 1 + 0.08 * np.sin(2 * np.pi * rng.uniform(2, 6) * t + rng.uniform(0, 6))
        ph = 2 * np.pi * np.cumsum(f0 * vib) / SR
        v = signal.sawtooth(ph) * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(1.5, 4) * t + k)) ** 2
        x += bp(v, 300, 2500)
    x += bp(noise(dur), 300, 3000) * 0.4
    return fade(x / 8, 0.3, 0.6)


def sfx_crowd_angry(dur=2.2):
    return sfx_crowd(dur, True) * 1.3


def sfx_car_pass():
    d = 2.2
    t = tt(d)
    f = 70 + 50 * np.exp(-((t - 0.9) / 0.5) ** 2) - 10 * (t > 0.9)
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) + 0.5 * signal.sawtooth(2 * np.pi * np.cumsum(f * 2.02) / SR)
    x = lp(x, 900) + lp(noise(d), 1500) * 0.4
    env = np.exp(-((t - 0.9) / 0.45) ** 2)
    return x * env * 0.8


def sfx_footsteps(dur=3.5):
    out = np.zeros(int(dur * SR))
    k = 0.0
    while k < dur - 0.1:
        s = lp(noise(0.07), 900) * np.exp(-tt(0.07) * 60)
        i = int(k * SR)
        out[i:i + len(s)] += s * rng.uniform(0.5, 1)
        k += rng.uniform(0.07, 0.14)
    return fade(out, 0.3, 0.4)


def sfx_cash_flutter():
    d = 1.4
    out = np.zeros(int(d * SR))
    for _ in range(26):
        s = bp(noise(0.05), 2000, 8000) * np.exp(-tt(0.05) * 70)
        i = int(rng.uniform(0, d - 0.06) * SR)
        out[i:i + len(s)] += s * rng.uniform(0.3, 1)
    return out


def sfx_register():
    d = 1.4
    out = np.zeros(int(d * SR))
    c = bp(noise(0.08), 800, 4000) * np.exp(-tt(0.08) * 50)
    out[: len(c)] += c
    return ov((out, 0), (A.bell_tone(2093, 1.2) * 1.4, 0.1), (A.bell_tone(2637, 1.0) * 0.8, 0.1))


def sfx_coin_out():
    return A.bell_tone(1568 * rng.uniform(0.95, 1.1), 0.5) * 1.2


def sfx_coin_in():
    a = A.bell_tone(1975, 0.6)
    b = A.bell_tone(2637, 0.8)
    out = np.zeros(int(0.9 * SR))
    out[: len(a)] += a
    out[int(0.09 * SR):int(0.09 * SR) + len(b)] += b
    return out * 1.3


def sfx_pop():
    return A.pop(rng.uniform(500, 800), 1.0)


def sfx_pop_big():
    p = A.pop(420, 1.0)
    k = A.kick(0.12, 160, 60, 0.5)
    n = min(len(p), len(k))
    return p[:n] + k[:n]


def sfx_box_drop():
    return ov((lp(A.kick(0.3, 90, 50, 1.0), 400), 0), (bp(noise(0.12), 300, 2000) * np.exp(-tt(0.12) * 30) * 0.5, 0))


def sfx_buzzer():
    return A.buzzer(1.0)


def sfx_buzzer_short():
    d = 0.25
    x = signal.square(2 * np.pi * 110 * tt(d)) + signal.square(2 * np.pi * 116 * tt(d))
    return lp(fade(x, 0.005, 0.04), 1800) * 0.4


def sfx_error():
    return A.error_beep(1.0)


def sfx_glass_crack():
    d = 0.6
    out = hp(noise(d), 3000) * np.exp(-tt(d) * 12)
    for _ in range(12):
        s = A.bell_tone(rng.uniform(3000, 6000), 0.2)
        i = int(rng.uniform(0, 0.3) * SR)
        out[i:i + len(s)] += s * 0.4
    return out * 0.7


def sfx_ding():
    return A.ding(1318.5, 1.0)


def sfx_fire(dur=1.2):
    t = tt(dur)
    x = lp(noise(dur), 1200) * 0.6 + lp(noise(dur), 300) * 0.8
    for _ in range(int(dur * 25)):
        s = hp(noise(0.01), 3000) * np.exp(-tt(0.01) * 300)
        i = int(rng.uniform(0, dur - 0.02) * SR)
        x[i:i + len(s)] += s * 1.5
    return fade(x, 0.15, 0.4) * 0.6


def sfx_tick_ui():
    return A.click(1.0)


def sfx_select():
    a = A.bell_tone(880, 0.8)
    b = A.bell_tone(1318.5, 0.8)
    out = np.zeros(int(1.0 * SR))
    out[: len(a)] += a
    out[int(0.07 * SR):int(0.07 * SR) + len(b)] += b
    return ov((out * 1.5, 0), (A.kick(0.3, 120, 50, 0.6), 0))


def sfx_spotlight():
    d = 1.5
    t = tt(d)
    x = A.kick(0.3, 60, 35, 1.0)
    x = np.pad(x, (0, len(t) - len(x)))
    x += lp(noise(d), 400) * np.exp(-t * 3) * 0.6 + sweep(50, 45, d) * np.exp(-t * 1.5) * 0.4
    return x


def sfx_drone(dur=5.0):
    t = tt(dur)
    x = signal.sawtooth(2 * np.pi * 55 * t) + signal.sawtooth(2 * np.pi * 55.4 * t) + 0.6 * np.sin(2 * np.pi * 82.4 * t)
    x = lp(x, 400) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * t))
    return fade(x, 1.0, 1.2) * 0.35


def sfx_rattle(dur=2.4):
    out = np.zeros(int(dur * SR))
    k = 0.0
    while k < dur - 0.05:
        s = bp(noise(0.04), 600, 3000) * np.exp(-tt(0.04) * 90)
        i = int(k * SR)
        out[i:i + len(s)] += s * rng.uniform(0.4, 1)
        k += rng.uniform(0.04, 0.09)
    t = tt(dur)
    return out * (t / dur) * 1.2


def sfx_shimmer():
    out = np.zeros(int(1.8 * SR))
    for i, m in enumerate((84, 88, 91, 95, 96, 100)):
        b = A.bell_tone(midi(m), 1.2) * 0.6
        j = int(i * 0.07 * SR)
        out[j:j + len(b)] += b
    return out


def sfx_lock():
    a = bp(noise(0.05), 1500, 6000) * np.exp(-tt(0.05) * 80)
    b = bp(noise(0.06), 800, 4000) * np.exp(-tt(0.06) * 60)
    out = np.zeros(int(0.3 * SR))
    out[: len(a)] += a
    out[int(0.09 * SR):int(0.09 * SR) + len(b)] += b * 1.3
    return out * 1.5


def sfx_unlock():
    return sfx_lock()[::-1].copy() * 0.6 + sfx_lock()


def sfx_camera():
    return A.shutter(1.0)


def sfx_stamp():
    d = 0.6
    t = tt(d)
    return A.kick(d, 140, 50, 1.2) + bp(noise(d), 200, 2500) * np.exp(-t * 25) * 0.9


def sfx_phone_ring():
    d = 1.6
    t = tt(d)
    x = (np.sin(2 * np.pi * 1300 * t) + np.sin(2 * np.pi * 1600 * t)) * (np.sin(2 * np.pi * 20 * t) > 0)
    gate = ((t % 0.8) < 0.5).astype(float)
    return fade(x * gate * 0.25, 0.01, 0.05)


def sfx_cough():
    out = np.zeros(int(0.7 * SR))
    for k, st in enumerate((0.0, 0.22)):
        d = 0.18
        t = tt(d)
        x = bp(noise(d), 250, 2500) * np.exp(-t * 18) + np.sin(2 * np.pi * 180 * t) * np.exp(-t * 25) * 0.3
        i = int(st * SR)
        out[i:i + len(x)] += x * (1 - 0.3 * k)
    return out * 1.2


def sfx_game_start():
    out = np.zeros(int(1.0 * SR))
    for i, m in enumerate((72, 76, 79, 84)):
        b = fade(sq(midi(m), 0.12, 0.25), 0.002, 0.03) * 0.25
        j = int(i * 0.09 * SR)
        out[j:j + len(b)] += b
    return lp(out, 6000)


def sfx_rimshot():
    out = np.zeros(int(1.0 * SR))
    for st, g in ((0.0, 0.8), (0.15, 0.8)):
        s = bp(noise(0.1), 1500, 6000) * np.exp(-tt(0.1) * 40) + np.sin(2 * np.pi * 330 * tt(0.1)) * np.exp(-tt(0.1) * 40)
        i = int(st * SR)
        out[i:i + len(s)] += s * g
    cy = hp(noise(0.8), 5000) * np.exp(-tt(0.8) * 4) * 0.5
    i = int(0.35 * SR)
    out[i:i + len(cy)] += cy[: len(out) - i]
    out[i:i + int(0.12 * SR)] += A.kick(0.12, 100, 50, 0.6)[: int(0.12 * SR)]
    return out


def sfx_scratch():
    d = 0.45
    t = tt(d)
    f = 600 + 900 * np.sin(2 * np.pi * 4 * t)
    x = bp(noise(d), 500, 4000) * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR / 40))
    return x * np.exp(-t * 3) * 1.4


def sfx_scratch_line():
    return bp(noise(0.3), 1500, 5000) * np.linspace(1, 0.2, int(0.3 * SR)) * 0.8


def sfx_heartbeat_fast(dur=2.0):
    out = np.zeros(int(dur * SR))
    k = 0.0
    while k < dur - 0.5:
        h = A.heartbeat(1.0)
        i = int(k * SR)
        n = min(len(h), len(out) - i)
        out[i:i + n] += h[:n]
        k += 0.42
    return out


def sfx_tape_slow():
    return A.tape_stop(1.2)


def sfx_power_on():
    d = 1.2
    t = tt(d)
    x = sweep(80, 600, d) * np.exp(-t * 2) * 0.5
    b = A.bell_tone(659, 1.0) * 0.8
    out = x.copy()
    i = int(0.35 * SR)
    out[i:i + len(b)] += b[: len(out) - i]
    return out


def sfx_power_down():
    d = 0.9
    return sweep(600, 60, d) * np.exp(-tt(d) * 2) * 0.6


def sfx_thud_crack():
    x = np.pad(A.kick(0.6, 100, 40, 1.3), (0, int(0.2 * SR)))
    g = sfx_glass_crack()
    x[int(0.05 * SR):int(0.05 * SR) + len(g)] += g[: len(x) - int(0.05 * SR)] * 0.7
    return x


def sfx_thud():
    return A.kick(0.5, 90, 40, 1.2) + lp(noise(0.5), 500) * np.exp(-tt(0.5) * 15) * 0.5


def sfx_hum_old(dur=2.0):
    t = tt(dur)
    return fade((np.sin(2 * np.pi * 60 * t) + 0.4 * np.sin(2 * np.pi * 120 * t)) * 0.3 + hp(noise(dur), 4000) * 0.05,
                0.2, 0.3)


def sfx_map_open():
    w = A.whoosh(0.4, True, 0.8)
    return w + sfx_select()[: len(w)] * 0.5


def sfx_sigh_pad():
    return A.pad([midi(69), midi(72), midi(76)], 2.5, 0.3, 1.2, 0.4) * 1.0


def sfx_click():
    return A.click(1.0) * 1.5


def sfx_dun():
    d = 1.8
    t = tt(d)
    x = signal.sawtooth(2 * np.pi * 55 * t) + signal.sawtooth(2 * np.pi * 58.3 * t) + signal.sawtooth(2 * np.pi * 41.2 * t)
    return lp(x, 500) * np.exp(-t * 1.6) * 0.5 + A.kick(d, 80, 35, 0.8)


def sfx_underwater():
    d = 1.6
    t = tt(d)
    x = lp(noise(d), 300) * 0.8
    for _ in range(14):
        f = rng.uniform(300, 900)
        bl = np.sin(2 * np.pi * np.cumsum(f * (1 + 2 * tt(0.08))) / SR) * np.exp(-tt(0.08) * 30)
        i = int(rng.uniform(0, d - 0.1) * SR)
        x[i:i + len(bl)] += bl * 0.4
    return fade(x, 0.1, 0.4)


def sfx_spin():
    d = 1.0
    t = tt(d)
    x = bp(noise(d), 1000, 5000) * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(20 * np.exp(-t * 2.5)) / SR))
    return x * np.exp(-t * 2) * 0.8


def sfx_notify():
    a = A.bell_tone(1568, 0.5)
    b = A.bell_tone(2093, 0.7)
    out = np.zeros(int(0.8 * SR))
    out[: len(a)] += a
    out[int(0.1 * SR):int(0.1 * SR) + len(b)] += b
    return out * 1.3


def sfx_printer(dur=1.0):
    t = tt(dur)
    x = bp(noise(dur), 500, 3000) * (0.6 + 0.4 * (np.sin(2 * np.pi * 30 * t) > 0))
    return fade(x, 0.02, 0.1) * 0.5


def sfx_kids_yay():
    d = 0.9
    t = tt(d)
    x = np.zeros_like(t)
    for f in (520, 610, 700):
        ff = f * (1 + 0.25 * np.sin(np.pi * t / d))
        x += signal.sawtooth(2 * np.pi * np.cumsum(ff) / SR)
    return bp(x, 400, 3000) * np.sin(np.pi * t / d) * 0.25


def sfx_download_blips(dur=1.4):
    out = np.zeros(int(dur * SR))
    k = 0.0
    i0 = 0
    while k < dur - 0.06:
        b = fade(sq(midi(84 + (i0 % 4) * 2), 0.05, 0.25), 0.002, 0.02) * 0.2
        j = int(k * SR)
        out[j:j + len(b)] += b
        k += 0.11
        i0 += 1
    return lp(out, 5000)


def sfx_connect():
    return sfx_game_start() * 0.8


def sfx_creak():
    d = 0.9
    t = tt(d)
    f = 180 + 60 * np.sin(2 * np.pi * 1.3 * t)
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 37 * t))
    return bp(x, 300, 2500) * np.sin(np.pi * t / d) * 0.5


def sfx_slide():
    return bp(noise(0.5), 1000, 5000) * np.sin(np.pi * tt(0.5) / 0.5) * 0.6


def sfx_type():
    return A.click(1.0) * 1.2


def sfx_clock_slow(dur=1.2):
    out = np.zeros(int(dur * SR))
    for k in range(int(dur / 0.4) + 1):
        c = A.click(1.0)
        i = int(k * 0.4 * SR)
        if i < len(out):
            out[i:i + len(c)] += c[: len(out) - i]
    return out


def sfx_clock_fast(dur=1.6):
    out = np.zeros(int(dur * SR))
    for k in range(int(dur / 0.08)):
        c = A.click(0.7)
        i = int(k * 0.08 * SR)
        out[i:i + len(c)] += c[: len(out) - i]
    return out


def sfx_tick_slow(dur=1.4):
    return sfx_clock_slow(dur)


def sfx_cards():
    out = np.zeros(int(0.6 * SR))
    for k in range(3):
        s = A.whoosh(0.18, True, 0.8)
        i = int(k * 0.15 * SR)
        out[i:i + len(s)] += s
    return out


def sfx_trash():
    return np.concatenate([A.whoosh(0.2, False, 0.6), sfx_box_drop() * 0.7])


def sfx_page_flip():
    return bp(noise(0.12), 1500, 7000) * np.sin(np.pi * tt(0.12) / 0.12) * 0.7


def sfx_marker():
    d = 0.6
    return bp(noise(d), 2000, 6000) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * tt(d))) * 0.4


def sfx_success():
    out = np.zeros(int(2.0 * SR))
    for i, m in enumerate((72, 76, 79, 84)):
        b = ov((A.bell_tone(midi(m), 1.4) * 0.8, 0), (fade(sq(midi(m), 0.16, 0.3), 0.002, 0.05) * 0.12, 0))
        j = int(i * 0.08 * SR)
        out[j:j + len(b)] += b[: len(out) - j]
    return out * 1.2


def sfx_banner():
    sl = sfx_slam() * 0.7
    w = A.whoosh(0.5, True, 0.6)
    sl[: len(w)] += w[: len(sl)]
    return sl


def sfx_wheel():
    return np.concatenate([A.whoosh(0.3, True, 0.7), sfx_clock_fast(0.6) * 0.6])


def sfx_pause():
    return A.tape_stop(0.6)[: int(0.4 * SR)]


def sfx_tick_check():
    return A.pop(900, 0.6) + A.ding(1760, 0.3)[: int(0.12 * SR)]


def sfx_dust():
    d = 1.0
    return fade(hp(noise(d), 3000) * 0.15 + lp(noise(d), 600) * 0.2, 0.2, 0.5)


def sfx_slide_down():
    return sweep(900, 200, 0.8) * np.exp(-tt(0.8) * 1.5) * 0.5 + A.whoosh(0.8, False, 0.5)


def sfx_wrench():
    out = np.zeros(int(0.6 * SR))
    for k in range(3):
        s = bp(noise(0.06), 1200, 6000) * np.exp(-tt(0.06) * 60) + A.bell_tone(2400, 0.06) * 0.3
        i = int(k * 0.15 * SR)
        out[i:i + len(s)] += s
    return out


def sfx_squish():
    return A.squish(1.0)


def sfx_up():
    return sweep(300, 1200, 0.4) * np.exp(-tt(0.4) * 4) * 0.5


def sfx_hourglass_flip():
    w = A.whoosh(0.5, True, 0.6)
    c = A.click(1.0)
    w[: len(c)] += c
    return w


def sfx_sand(dur=2.0):
    return fade(hp(noise(dur), 2500) * 0.12, 0.2, 0.5)


def sfx_siren(dur=2.4):
    t = tt(dur)
    f = 750 + 350 * np.sin(2 * np.pi * 1.6 * t)
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * 0.5 + np.sin(2 * np.pi * np.cumsum(f) / SR)
    x = lp(x, 3000)
    dop = np.interp(t, [0, dur * 0.45, dur], [0.2, 1.0, 0.15])
    return fade(x * dop * 0.4, 0.05, 0.3)


def sfx_heli(dur=4.0):
    t = tt(dur)
    chop = (0.5 + 0.5 * np.sin(2 * np.pi * 14 * t)) ** 4
    x = lp(noise(dur), 300) * chop * 1.6 + lp(noise(dur), 1200) * 0.15
    return fade(x, 0.6, 0.8) * 0.8


LIB = {k[4:]: v for k, v in globals().items() if k.startswith("sfx_")}


# ------------------------------------------------------------------ music (synthwave, 100 BPM, A minor)
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
N = A.nm

PROGS = {
    "main": [("A", "min"), ("F", "maj"), ("C", "maj"), ("G", "maj")],
    "tense": [("A", "min"), ("A", "min"), ("F", "maj"), ("E", "maj")],
    "warm": [("F", "maj"), ("C", "maj"), ("G", "maj"), ("A", "min")],
}
ROOT = {"A": 57, "F": 53, "C": 48, "G": 55, "E": 52, "D": 50}


def chord_notes(root, q):
    r = ROOT[root]
    return [r, r + (3 if q == "min" else 4), r + 7]


def synth_bass(f, d):
    x = signal.sawtooth(2 * np.pi * f * tt(d)) + 0.5 * signal.square(2 * np.pi * f * 0.5 * tt(d))
    x = lp(x, 600)
    return x * env_adsr(len(x), 0.005, 0.08, 0.7, 0.04) * 0.5


def synth_pad(notes, d):
    t = tt(d)
    x = np.zeros_like(t)
    for m in notes:
        for det in (-0.006, 0.0, 0.006):
            x += signal.sawtooth(2 * np.pi * midi(m + 12) * (1 + det) * t + rng.uniform(0, 6))
    x = lp(x / (len(notes) * 3), 1800)
    return x * env_adsr(len(t), 0.4, 0.1, 1.0, 0.5) * 0.5


def synth_arp(m, d):
    x = sq(midi(m), d, 0.3) * 0.5 + signal.sawtooth(2 * np.pi * midi(m) * 1.003 * tt(d)) * 0.5
    x = lp(x, 3500)
    return x * env_adsr(len(x), 0.002, 0.08, 0.2, 0.03) * 0.25


def snare():
    d = 0.5
    t = tt(d)
    x = bp(noise(d), 1200, 8000) * np.exp(-t * 9) * 0.8 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * 0.5
    # gated "80s" reverb tail
    tail = lp(noise(d), 5000) * 0.25 * (t < 0.28)
    return x + tail * np.exp(-t * 3)


SNARE = snare()
KICK = A.kick(0.4, 120, 45, 1.0)
HAT = A.hat(0.05, 0.35)
OHAT = hp(noise(0.25), 7000) * np.exp(-tt(0.25) * 12) * 0.25

_cache = {}


def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


def music_section(m, a, b, style, prog="main", gain=1.0):
    """Lay bars on the global grid from a to b. style: drone|pulse|light|groove|full|build"""
    first = int(np.floor(a / BAR))
    last = int(np.ceil(b / BAR))
    chords = PROGS[prog]
    for bi in range(first, last):
        t0 = bi * BAR
        root, q = chords[bi % 4]
        notes = chord_notes(root, q)
        rootf = midi(ROOT[root] - 24)

        def put(x, at, g=1.0):
            if a - 0.01 <= at < b:
                m.add(x * gain * g, at)

        if style in ("drone", "pulse", "light", "groove", "full", "build", "warm"):
            pd = cached(("pad", root, q), lambda: synth_pad(notes, BAR + 0.5))
            put(pd, t0, 0.55 if style != "drone" else 0.8)
        if style in ("pulse", "groove", "full", "build", "light", "warm"):
            bs = cached(("bass", root), lambda: synth_bass(rootf, BEAT / 2 * 0.9))
            for k in range(8):
                put(bs, t0 + k * BEAT / 2, 0.9 if style != "light" else 0.6)
        if style in ("groove", "full", "light", "warm"):
            seq = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[1] + 24]
            for k in range(16 if style != "light" else 8):
                st = (BEAT / 4) if style != "light" else (BEAT / 2)
                nn = seq[k % 4]
                ar = cached(("arp", nn, st), lambda: synth_arp(nn, st * 0.9))
                put(ar, t0 + k * st, 0.8 if style == "full" else 0.55)
        if style in ("pulse", "groove", "full", "build", "warm"):
            for k in range(4):
                put(KICK, t0 + k * BEAT, 0.9 if style != "pulse" else 0.6)
        if style in ("groove", "full", "warm"):
            for k in (1, 3):
                put(SNARE, t0 + k * BEAT, 0.7)
            for k in range(8):
                put(HAT, t0 + k * BEAT / 2 + BEAT / 4 * 0, 0.7)
            if style == "full":
                for k in range(4):
                    put(OHAT, t0 + k * BEAT + BEAT / 2, 0.8)
        if style == "build":
            for k in range(16):
                put(SNARE, t0 + k * BEAT / 4, 0.25 + 0.5 * k / 16)
        if style == "light":
            for k in range(8):
                put(HAT, t0 + k * BEAT / 2, 0.5)


def build_music(dur):
    m = Track(dur)
    T = S.T
    sec = [
        (0.0, T("and", 17.1), "pulse", "tense"),
        (T("and", 17.1), T("on", 23.6), "drone", "tense"),
        (T("on", 23.6), T("launches", 27.8), "build", "main"),
        (T("launches", 27.8), T("problem", 40.2) - 0.15, "full", "main"),
        (T("when", 41.2), T("so", 47.5), "build", "tense"),
        (T("first", 51.5) - 0.2, T("but", 84.1), "groove", "main"),
        (T("but", 84.1), T("let's", 90.1), "drone", "tense"),
        (T("let's", 90.1), T("and", 142.8), "groove", "main"),
        (T("and", 142.8), T("that", 161.0), "drone", "tense"),
        (T("that", 161.0), T("the", 184.5), "light", "tense"),
        (T("the", 184.5), T("so", 202.1), "groove", "main"),
        (T("so", 202.1), T("now", 242.8), "warm", "warm"),
        (T("now", 242.8), T("you're", 267.5), "groove", "main"),
        (T("you're", 267.5), T("one", 274.9), "full", "main"),
        (T("one", 274.9), T("either", 294.7), "drone", "tense"),
        (T("either", 294.7), S.END - 1.2, "full", "main"),
    ]
    for a, b, st, pr in sec:
        music_section(m, a, b, st, pr)
    # slow-down moment ("let's slow down"): pitched-down pad only
    m.add(synth_pad(chord_notes("A", "min"), 4.0) * 0.6, T("so", 47.5))
    # final chord ring-out
    fin = synth_pad(chord_notes("A", "min"), 4.0) * 0.9
    m.add(fin, S.END - 1.4)
    return m


# ------------------------------------------------------------------ mix
def envelope(x, win=0.05):
    n = int(win * SR)
    e = np.sqrt(np.convolve(x ** 2, np.ones(n) / n, mode="same"))
    return e


def load_voice(path):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"])
    v = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    end = int(S.VOICE_END * SR)
    v = v[:end].copy()
    f = int(0.12 * SR)
    v[-f:] *= np.linspace(1, 0, f)
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    dur = S.END
    n = int(dur * SR)
    voice = np.zeros(n)
    v = load_voice(a.voice)
    voice[: len(v)] = v
    print("music...", flush=True)
    m = build_music(dur)
    music = m.stereo(n)
    print("sfx...", flush=True)
    fx = Track(dur)
    for (at, name, gain, pan, kw) in S.SFX:
        x = LIB[name](**kw) if kw else LIB[name]()
        fx.add(np.asarray(x, dtype=np.float64), at, gain, pan)
    # cut whooshes
    for ct in S.CUTS:
        fx.add(A.whoosh(0.45, True, 0.35), ct - 0.3, 1.0)
    fxs = fx.stereo(n)
    # ducking
    env = envelope(voice)
    env = env / (np.percentile(env, 95) + 1e-9)
    duck = 1.0 - 0.55 * np.clip(env, 0, 1)
    duck = lp(duck, 4, 1)
    music = music / (np.max(np.abs(music)) + 1e-9)
    music *= (0.30 * duck)[:, None]
    fxs = fxs / (np.percentile(np.abs(fxs), 99.95) + 1e-9) * 0.55
    fxs *= (0.65 + 0.35 * duck)[:, None]
    vpk = np.max(np.abs(voice)) or 1.0
    vo = voice / vpk * 0.9
    for name, x in (("music", music), ("sfx", fxs), ("voice", vo)):
        sel = env > 0.3
        r = np.sqrt(np.mean((x if x.ndim == 1 else x.mean(1))[sel] ** 2))
        print(f"  {name:6s} rms while speaking: {20 * np.log10(r + 1e-12):6.1f} dB")
    mix = music + fxs + vo[:, None]
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    wavfile.write(a.out, SR, (mix * 32767 * 0.95).astype(np.int16))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
