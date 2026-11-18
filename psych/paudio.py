"""Soundtrack for 'The Dream Tax': emotional score + ~170 timed SFX, ducked under the narrator, -14 LUFS.

Music follows the story: hospital drone -> warm dream theme -> cold reality -> curious science
ostinato -> warm 'salary of satisfaction' -> fear tension -> hopeful build for the fix -> warm close.

Usage: python paudio.py --voice voice.mp3 --out mix.wav
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "blackhole"))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from audio import (SR, Track, tt, lp, hp, bp, noise, pad, bell_tone, kick, heartbeat, whoosh, pop, click,  # noqa
                   ding, chime_sparkle, buzzer, tape_stop, hit, riser, tick, crunch, squish, shutter, fz,
                   cue_tense, cue_curious, cue_night, cue_warm, cue_tension, cue_hope, final_chord, fade_region,
                   load_audio, envelope, edge_env, env_adsr, midi, gulp)
from audio_bh import (sub_boom, rumble, thud, bloop, beep, scribble, phone_buzz, freeze_chime, ticks,  # noqa
                      drone)
from scipy.io import wavfile  # noqa: E402

rng = np.random.default_rng(7)


def page_flip(gain=0.25):
    d = 0.35
    return bp(noise(d), 1200, 7000) * np.exp(-tt(d) * 9) * np.sin(np.pi * tt(d) / d) * gain


def stamp_sfx(gain=0.6):
    out = thud(1.0) * 0.9
    s = hp(noise(0.12), 2000) * np.exp(-tt(0.12) * 40)
    out[: len(s)] += s * 0.6
    return out * gain


def water(dur, gain=0.12):
    x = bp(noise(dur), 500, 6000) * (0.8 + 0.2 * np.sin(2 * np.pi * 7 * tt(dur)))
    return x * edge_env(len(x), 0.2) * gain


def applause(dur=2.0, gain=0.25):
    out = np.zeros(int(dur * SR))
    for k in range(int(dur * 22)):
        c_ = bp(noise(0.05), 800, 5000) * np.exp(-tt(0.05) * 60)
        j = int(rng.uniform(0, dur - 0.06) * SR)
        out[j:j + len(c_)] += c_ * rng.uniform(0.4, 1.0)
    return out * edge_env(len(out), 0.3) * gain


def typing(dur, gain=0.18):
    out = np.zeros(int(dur * SR))
    k = 0.0
    while k < dur - 0.05:
        c_ = click(1.0) * rng.uniform(0.5, 1.0)
        j = int(k * SR)
        out[j:j + len(c_)] += c_[: len(out) - j]
        k += rng.uniform(0.06, 0.16)
    return out * gain


def growl(gain=0.3):
    d = 1.2
    t = tt(d)
    f = 70 + 25 * np.sin(2 * np.pi * 3 * t)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 11 * t)) + lp(noise(d), 200) * 0.8
    return x * np.sin(np.pi * t / d) * gain


def downsweep(gain=0.3, d=1.4):
    t = tt(d)
    f = 900 * np.exp(-t * 2.2) + 80
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.2) * gain


def coin_sfx(gain=0.25):
    return (bell_tone(2637, 0.4) + bell_tone(3520, 0.4) * 0.6) * gain


def cash(gain=0.3):
    out = np.zeros(int(1.2 * SR))
    for i in range(5):
        c_ = coin_sfx(1.0)
        j = int(i * 0.09 * SR)
        out[j:j + len(c_)] += c_[: len(out) - j]
    return out * gain


def build_music(dur):
    m = Track(dur)
    drone(m, 0.0, 4.2, root="D2", gain=0.5)
    cue_warm(m, 3.9, 14.3, bpm=80)
    drone(m, 14.3, 22.3, root="D2", gain=0.55)
    cue_night(m, 22.2, 31.0)
    final_chord(m, 31.0, ["D3", "A3", "D4", "F#4"], 0.5, 3.0)
    cue_curious(m, 33.6, 83.2, bpm=92, gain=0.7)
    m.add(pad(fz(["D3", "F3", "A3", "C4"]), 8.0, 1.5, 2.0, 0.3), 83.2, 0.5)
    cue_curious(m, 90.9, 118.0, bpm=98, gain=0.65)
    cue_warm(m, 118.0, 136.3, bpm=76)
    cue_curious(m, 136.3, 183.5, bpm=90, gain=0.6)
    cue_night(m, 183.5, 205.6)
    cue_warm(m, 205.6, 228.6, bpm=82)
    final_chord(m, 230.9, ["C3", "G3", "C4", "E4"], 0.45, 2.5)
    cue_curious(m, 232.5, 289.7, bpm=96, gain=0.6)
    final_chord(m, 289.75, ["A2", "E3", "A3", "C4"], 0.45, 2.0)
    cue_tension(m, 291.2, 302.9, bpm=96, gain=0.9)
    cue_curious(m, 302.9, 356.0, bpm=88, gain=0.55)
    cue_tense(m, 356.0, 365.1, 0.6, bpm=66)
    final_chord(m, 365.1, ["D3", "A3", "D4", "F#4"], 0.45, 2.0)
    cue_hope(m, 367.0, 410.0, build=0.3)
    cue_curious(m, 410.0, 436.9, bpm=92, gain=0.5)
    cue_warm(m, 436.9, 467.6, bpm=72)
    final_chord(m, 467.6, ["D3", "F#3", "A3", "D4"], 0.55, 5.0)
    x = m.stereo(int(dur * SR))
    x = fade_region(x, 14.25, 14.6, 0.08)    # dream shatters into reality
    x = fade_region(x, 29.3, 29.9, 0.1)      # "LAZY?" stamp lands in silence
    x = fade_region(x, 298.2, 298.9, 0.1)    # silence before the fear hits
    return x


def build_sfx(dur, cuts):
    s = Track(dur)
    E = []

    def ev(at_, fn, g=1.0, pan=0.0):
        E.append((at_, fn, g, pan))

    for ct in cuts:
        ev(ct - 0.25, lambda: whoosh(0.45, True, 0.14))
    # HOOK: hospital
    for k in np.arange(0.2, 6.5, 0.86):
        ev(k, lambda: beep(1250, 0.1, 0.12), pan=0.5)
    ev(4.6, lambda: chime_sparkle(0.3))
    ev(6.9, lambda: freeze_chime(0.25))
    for k in np.arange(7.0, 11.6, 0.56):
        ev(k, lambda: kick(0.12, 140, 70, 0.12))
    ev(10.82, lambda: whoosh(0.5, True, 0.35))
    ev(10.95, lambda: pop(500, 0.3))
    ev(11.66, lambda: pop(700, 0.3))
    ev(12.86, lambda: chime_sparkle(0.4))
    ev(14.3, lambda: tape_stop(0.45))
    ev(14.32, lambda: hit(0.45))
    ev(16.5, lambda: chime_sparkle(0.2))
    ev(21.5, lambda: downsweep(0.3))
    ev(22.3, lambda: ticks(1.0, 13, 0.25))
    for k in (24.9, 25.5, 26.1):
        ev(k, lambda: page_flip(0.3))
    for i in range(6):
        ev(26.1 + i * 0.07, lambda: pop(380, 0.12))
    ev(29.42, lambda: stamp_sfx(0.7))
    ev(30.4, lambda: scribble(0.3, 0.3))
    ev(30.0, lambda: riser(1.0, 0.2))
    ev(31.0, lambda: hit(0.6))
    ev(31.0, lambda: sub_boom(0.5))
    ev(31.8, lambda: coin_sfx(0.35))
    # CHAPTER 1
    ev(33.9, lambda: whoosh(0.4, True, 0.2))
    ev(35.5, lambda: pop(600, 0.22))
    ev(36.7, lambda: pop(650, 0.22))
    ev(39.2, lambda: ticks(0.7, 20, 0.18))
    ev(41.6, lambda: whoosh(0.9, True, 0.3))
    ev(44.32, lambda: pop(500, 0.25), pan=-0.5)
    ev(45.28, lambda: chime_sparkle(0.25), pan=0.5)
    ev(48.0, lambda: pop(600, 0.2))
    for k in (51.4, 52.16, 53.0):
        ev(k, lambda: thud(0.35))
    ev(54.56, lambda: shutter(0.4))
    ev(54.6, lambda: hit(0.3))
    ev(56.2, lambda: chime_sparkle(0.15))
    ev(61.6, lambda: whoosh(0.6, False, 0.2))
    ev(62.7, lambda: water(1.1, 0.12))
    ev(63.8, lambda: rumble(1.1, 0.15))
    ev(64.9, lambda: rumble(2.5, 0.05, 120))
    ev(67.4, lambda: chime_sparkle(0.3))
    ev(68.2, lambda: pop(500, 0.25))
    ev(70.2, lambda: whoosh(0.8, True, 0.3))
    ev(70.9, lambda: ding(1568, 0.3))
    ev(72.3, lambda: downsweep(0.2, 0.8))
    ev(74.32, lambda: typing(1.0, 0.15))
    for k in (77.8, 78.4):
        ev(k, lambda: bloop(0.25))
    for k in (82.0, 82.6):
        ev(k, lambda: downsweep(0.2, 0.6))
    ev(82.04, lambda: buzzer(0.2))
    ev(89.1, lambda: downsweep(0.35, 1.4))
    for i in range(3):
        ev(92.2 + i * 0.3, lambda: pop(520 + i * 80, 0.25))
    ev(95.2, lambda: chime_sparkle(0.2))
    ev(98.0, lambda: hit(0.35))
    ev(103.76, lambda: stamp_sfx(0.55))
    ev(103.8, lambda: buzzer(0.15))
    ev(106.42, lambda: pop(600, 0.2))
    ev(108.32, lambda: stamp_sfx(0.4))
    ev(108.4, lambda: ding(1318.5, 0.3))
    ev(109.4, lambda: whoosh(0.7, True, 0.3))
    ev(110.3, lambda: chime_sparkle(0.2))
    ev(113.72, lambda: ticks(0.6, 15, 0.2))
    ev(115.4, lambda: bloop(0.2))
    ev(115.94, lambda: downsweep(0.3, 0.9))
    # DREAMING ISN'T BAD
    ev(120.0, lambda: pop(600, 0.2))
    ev(127.28, lambda: growl(0.35))
    ev(128.24, lambda: pop(700, 0.2))
    for i in range(6):
        ev(127.2 + i * 0.35, lambda: bloop(0.12))
    ev(132.6, lambda: crunch(0.15))
    ev(133.12, lambda: buzzer(0.15))
    ev(134.0, lambda: growl(0.25))
    ev(137.2, lambda: whoosh(0.5, True, 0.25))
    ev(137.3, lambda: ding(880, 0.2))
    # BLOOD PRESSURE
    for k in np.arange(140.4, 142.2, 0.45):
        ev(k, lambda: squish(0.18))
    ev(142.78, lambda: ticks(0.7, 20, 0.18))
    for i in range(4):
        ev(143.98 + i * 0.15, lambda: pop(500 + i * 90, 0.2))
    ev(148.84, lambda: stamp_sfx(0.45))
    for k in (153.1, 155.42, 156.14, 156.68):
        ev(k - 0.3, lambda: pop(600, 0.22))
    ev(158.2, lambda: riser(1.2, 0.15))
    ev(161.96, lambda: chime_sparkle(0.2), pan=-0.5)
    ev(165.0, lambda: downsweep(0.2, 0.9), pan=-0.5)
    ev(166.6, lambda: bloop(0.2), pan=0.5)
    for i in range(4):
        ev(170.4 + i * 0.25, lambda: bloop(0.18))
    ev(172.6, lambda: buzzer(0.12))
    ev(177.2, lambda: riser(1.4, 0.15))
    ev(180.1, lambda: downsweep(0.25, 2.0))
    ev(181.3, lambda: hit(0.3))
    # JOB SEEKER / LOVESICK
    ev(187.6, lambda: thud(0.25))
    ev(188.6, lambda: thud(0.3))
    ev(191.6, lambda: whoosh(0.4, True, 0.15))
    # MIND MOVES IN EARLY
    ev(196.3, lambda: whoosh(1.4, True, 0.35))
    ev(197.9, lambda: chime_sparkle(0.35))
    ev(200.0, lambda: pad(fz(["F3", "A3", "C4"]), 2.5, 0.5, 1.5, 0.4) * 0.3)
    ev(203.7, lambda: bloop(0.15))
    # SALARY
    for k in (210.56, 211.62, 212.7):
        ev(k - 0.2, lambda: pop(650, 0.22))
    ev(213.0, lambda: whoosh(0.8, False, 0.3))
    ev(213.6, lambda: cash(0.35))
    ev(215.52, lambda: stamp_sfx(0.4))
    ev(218.0, lambda: ding(1318.5, 0.3))
    ev(219.82, lambda: buzzer(0.15))
    ev(223.5, lambda: pop(600, 0.25))
    ev(224.34, lambda: pop(500, 0.25))
    ev(225.54, lambda: pop(700, 0.2))
    ev(226.54, lambda: pop(400, 0.2))
    ev(229.34, lambda: pop(650, 0.25))
    ev(230.95, lambda: hit(0.5))
    ev(230.95, lambda: sub_boom(0.4))
    # CHAPTER 2
    ev(233.08, lambda: ticks(0.7, 20, 0.18))
    for i in range(4):
        ev(236.16 + i * 0.12, lambda: page_flip(0.2))
    ev(239.8, lambda: whoosh(0.5, True, 0.2))
    ev(240.1, lambda: bloop(0.2))
    ev(246.36, lambda: chime_sparkle(0.25))
    for i in range(4):
        ev(249.22 + i * 0.15, lambda: thud(0.15))
    ev(252.26, lambda: applause(2.0, 0.25))
    ev(254.1, lambda: pop(600, 0.2))
    ev(256.56, lambda: pop(500, 0.2))
    for i in (0, 3, 1, 3, 4, 5):
        pass
    for i in range(7):
        ev(258.6 + i * 0.25, lambda: tick(0.3))
    ev(263.1, lambda: downsweep(0.2, 0.8))
    ev(266.8, lambda: hit(0.3))
    ev(268.8, lambda: bloop(0.15))
    ev(272.4, lambda: freeze_chime(0.3))
    ev(272.96, lambda: stamp_sfx(0.4))
    for i in range(10):
        ev(277.2 + i * 0.18, lambda: pop(800 + rng.uniform(-100, 300), 0.12))
    ev(282.6, lambda: beep(660, 0.25, 0.15))
    ev(283.5, lambda: pop(600, 0.25))
    ev(285.4, lambda: typing(2.0, 0.06))
    ev(288.4, lambda: downsweep(0.25, 1.0))
    ev(288.9, lambda: stamp_sfx(0.35))
    ev(289.75, lambda: hit(0.5))
    ev(289.75, lambda: sub_boom(0.5))
    # FEAR
    ev(294.72, lambda: chime_sparkle(0.25))
    for i in range(10):
        ev(296.22 + i * 0.07, lambda: thud(0.12))
    ev(297.6, lambda: rumble(5.0, 0.3))
    ev(298.34, lambda: sub_boom(0.9))
    ev(298.34, lambda: hit(0.6))
    ev(299.18, lambda: heartbeat(0.5))
    ev(300.44, lambda: heartbeat(0.5))
    ev(301.76, lambda: hit(0.4))
    # SIROIS & PYCHYL
    ev(303.4, lambda: whoosh(0.4, True, 0.2))
    ev(308.44, lambda: ticks(1.0, 4, 0.25))
    ev(309.34, lambda: buzzer(0.15))
    ev(310.2, lambda: ding(1318.5, 0.3))
    ev(312.9, lambda: chime_sparkle(0.15))
    ev(318.54, lambda: ticks(0.7, 20, 0.18))
    ev(321.62, lambda: thud(0.4))
    ev(323.5, lambda: pop(500, 0.2))
    ev(326.1, lambda: scribble(0.8, 0.25))
    ev(327.14, lambda: phone_buzz(1.0, 0.18))
    for k in np.arange(329.6, 331.4, 0.3):
        ev(k, lambda: click(0.2))
    for i in range(5):
        ev(330.44 + i * 0.12, lambda: pop(900, 0.12))
    for i in range(4):
        ev(331.6 + i * 0.4, lambda: page_flip(0.2))
    ev(335.3, lambda: chime_sparkle(0.25))
    ev(338.6, lambda: hit(0.25))
    ev(341.96, lambda: beep(440, 0.15, 0.08))
    ev(343.96, lambda: pad(fz(["D3", "F#3", "A3", "D4"]), 2.0, 0.1, 1.5, 0.5) * 0.35)
    ev(346.12, lambda: whoosh(0.8, False, 0.3))
    ev(346.9, lambda: thud(0.3))
    ev(348.1, lambda: typing(0.8, 0.12))
    ev(354.68, lambda: water(2.0, 0.08))
    for k in (358.6, 360.28, 362.2):
        ev(k, lambda: pop(600, 0.25))
    ev(362.3, lambda: downsweep(0.2, 0.6))
    ev(364.28, lambda: hit(0.3))
    ev(364.5, lambda: buzzer(0.12))
    ev(365.1, lambda: hit(0.5))
    ev(365.1, lambda: chime_sparkle(0.3))
    # THE FIX
    ev(368.1, lambda: scribble(0.35, 0.3))
    ev(370.26, lambda: stamp_sfx(0.5))
    ev(370.3, lambda: chime_sparkle(0.3))
    ev(372.18, lambda: whoosh(0.5, True, 0.2))
    ev(374.34, lambda: chime_sparkle(0.3))
    ev(376.6, lambda: whoosh(0.6, False, 0.4))
    ev(376.6, lambda: hit(0.4))
    for k in (381.26, 383.18, 384.7):
        ev(k, lambda: pop(500, 0.25))
    ev(384.7, lambda: phone_buzz(1.0, 0.12))
    ev(388.02, lambda: stamp_sfx(0.4))
    ev(388.4, lambda: stamp_sfx(0.4))
    ev(389.9, lambda: ticks(0.8, 12, 0.25))
    ev(390.6, lambda: ding(1046.5, 0.3))
    ev(391.8, lambda: typing(2.6, 0.18))
    ev(393.1, lambda: beep(1500, 0.1, 0.15))
    ev(395.0, lambda: click(0.6))
    ev(395.05, lambda: thud(0.3))
    ev(402.6, lambda: ding(1318.5, 0.25))
    ev(405.92, lambda: stamp_sfx(0.6))
    ev(405.92, lambda: hit(0.4))
    for k in (407.14, 407.52, 408.3, 408.98):
        ev(k, lambda: pop(650, 0.3))
    ev(408.98, lambda: chime_sparkle(0.3))
    ev(410.1, lambda: typing(1.4, 0.1))
    for k in (412.26, 418.78, 424.08):
        ev(k, lambda: bloop(0.25))
    ev(420.5, lambda: downsweep(0.2, 1.6))
    ev(432.04, lambda: pop(500, 0.3))
    ev(433.58, lambda: coin_sfx(0.35))
    ev(434.5, lambda: whoosh(0.8, True, 0.3))
    ev(435.3, lambda: thud(0.4))
    ev(435.3, lambda: ding(1568, 0.25))
    # BACK TO THE PATIENT
    for k in np.arange(437.2, 447.4, 0.86):
        ev(k, lambda: beep(1250, 0.1, 0.1), pan=0.5)
    ev(451.8, lambda: whoosh(1.0, True, 0.3))
    ev(452.6, lambda: freeze_chime(0.2))
    for k in np.arange(452.9, 453.9, 0.5):
        ev(k, lambda: thud(0.12))
    ev(455.26, lambda: ding(1318.5, 0.35))
    ev(456.6, lambda: ticks(3.0, 2, 0.25))
    for k in (459.72, 461.2, 462.74):
        ev(k, lambda: pop(600, 0.3))
    for k in (465.4, 466.0, 466.6):
        ev(k, lambda: scribble(0.3, 0.25))
    ev(467.6, lambda: hit(0.4))
    ev(467.6, lambda: chime_sparkle(0.35))
    for at_, fn, g, pan in E:
        s.add(fn(), at_, g, pan)
    return s.stereo(int(dur * SR))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sys.path.insert(0, HERE)
    from ptimeline import CUTS, END

    voice = load_audio(a.voice)
    dur = END
    n = int(dur * SR)
    voice = np.pad(voice, (0, max(0, n - len(voice))))[:n]
    music = build_music(dur)[:n]
    fx = build_sfx(dur, CUTS)[:n]

    def norm(x, peak):
        m = np.max(np.abs(x)) or 1.0
        return x / m * peak

    music = norm(music, 1.0)
    env = envelope(voice)
    env = env / (np.percentile(env, 95) + 1e-9)
    duck = lp(1.0 - 0.55 * np.clip(env, 0, 1), 6, 1)
    music *= (0.22 * duck)[:, None]
    fx = norm(fx, 0.5)
    v = voice / (np.max(np.abs(voice)) or 1.0) * 0.92
    mix = np.stack([v, v], axis=1) + music + fx
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    wavfile.write(a.out, SR, (np.clip(mix, -1, 1) * 32767).astype(np.int16))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
