"""Soundtrack for the octopus video: low underwater score, ambience and word-timed SFX, ducked under the voice.

Usage: python audio_octo.py --voice voiceover_merged.mp3 --out mix.wav
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
sys.path.insert(0, os.path.join(HERE, "..", "blackhole"))
sys.path.insert(0, HERE)
from audio import (SR, Track, tt, lp, hp, bp, noise, pad, bell_tone, heartbeat, whoosh, pop, click, ding,  # noqa
                   chime_sparkle, error_beep, hit, riser, tick, drop_plink, fz, cue_tense, cue_curious, cue_night,
                   cue_warm, cue_tension, cue_hope, final_chord, fade_region, load_audio, envelope, edge_env, squish,
                   shutter)
from audio_bh import sub_boom, rumble, creak, thud, scribble, radar, static_burst, snap, breathing  # noqa: E402
from scipy import signal  # noqa: E402
from scipy.io import wavfile  # noqa: E402
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("octo_scenes", os.path.join(HERE, "scenes.py"))
_sc = importlib.util.module_from_spec(_spec)
sys.path.insert(0, HERE)
_spec.loader.exec_module(_sc)
S, WT, E = _sc.S, _sc.WT, _sc.E

rng = np.random.default_rng(7)


def drone(tr, a, b, roots=("D2", "A2"), gain=0.5, cluster=True):
    d = b - a
    tr.add(pad(fz(list(roots)), d + 1.5, 2.5, 2.0, 0.2), a, gain)
    if cluster:
        tr.add(pad(fz(["D4", "D#4", "A4"]), d + 1.5, 4.0, 2.0, 0.1), a, gain * 0.3)


def bubble_blip(gain=0.25):
    d = 0.12
    t = tt(d)
    f = 400 + 1600 * t / d
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30) * gain


def bubble_burst(n=8, gain=0.3):
    out = np.zeros(int(1.2 * SR))
    for k in range(n):
        st = int(rng.uniform(0, 0.9) * SR)
        b = bubble_blip(rng.uniform(0.3, 1.0))
        out[st:st + len(b)] += b[: len(out) - st]
    return out * gain


def buzz(dur=2.0, gain=0.12):
    t = tt(dur)
    f = 210 + 25 * np.sin(2 * np.pi * 3 * t)
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
    return bp(x, 300, 3000) * edge_env(len(x), 0.1) * gain


def printer(dur=1.6, gain=0.18):
    out = np.zeros(int(dur * SR))
    for k in range(int(dur * 18)):
        c = click(1.0)
        st = int(k / 18 * SR)
        out[st:st + len(c)] += c[: len(out) - st]
    return lp(out, 3000) * gain


def underwater_bed(dur):
    x = lp(noise(dur), 220) * 2.5 + 0.5 * lp(noise(dur), 60)
    return x * edge_env(len(x), 2.0)


def build_music(dur):
    m = Track(dur)
    cue_night(m, 0.0, 15.8)
    drone(m, 17.6, 32.0, gain=0.6)
    cue_curious(m, 32.0, 53.6, bpm=88, gain=0.6)
    drone(m, 53.7, 57.9, gain=0.5)
    cue_curious(m, 57.9, 115.0, bpm=92, gain=0.55)
    cue_tense(m, 117.2, 145.6, 0.55, bpm=64)
    cue_night(m, 145.8, 176.0)
    drone(m, 176.0, 213.0, roots=("C2", "G2"), gain=0.5)
    cue_curious(m, 213.1, 259.4, bpm=96, gain=0.55)
    final_chord(m, 263.7, ["D2", "A2", "D3", "F3"], 0.5, 3.0)
    cue_night(m, 266.6, 293.6)
    cue_tension(m, 293.8, 359.0, bpm=96, gain=0.8)
    drone(m, 359.2, 372.2, gain=0.55)
    cue_hope(m, 374.9, 405.2, build=0.2)
    cue_night(m, 405.3, 437.2)
    cue_tense(m, 437.3, 447.3, 0.5, bpm=64)
    cue_warm(m, 447.4, 471.3, bpm=72)
    drone(m, 471.5, 483.0, roots=("A1", "E2"), gain=0.55)
    cue_warm(m, 483.2, 492.6, bpm=72)
    final_chord(m, 490.4, ["G2", "D3", "G3", "B3"], 0.45, 3.0)
    x = m.stereo(int(dur * SR))
    x = fade_region(x, 15.8, 17.6, 0.2)
    x = fade_region(x, 115.0, 117.2, 0.1)
    x = fade_region(x, 259.4, 263.6, 0.1)
    x = fade_region(x, 372.2, 374.8, 0.4)
    return x


def build_sfx(dur):
    s = Track(dur)
    ev = []

    def at_(t, fn, g=1.0, pan=0.0):
        ev.append((t, fn, g, pan))

    # hook
    for t in (2.0, 7.0, 12.0):
        at_(t, lambda: bubble_burst(6, 0.4), 0.6, 0.3)
    at_(WT(2, "sharks"), lambda: pop(700, 0.4), 0.5)
    at_(WT(3, "seals"), lambda: pop(760, 0.4), 0.5)
    at_(WT(4, "nothing"), lambda: pop(820, 0.4), 0.5)
    at_(S(5) + 0.15, lambda: thud(0.7), 0.8)
    at_(S(6) - 0.15, lambda: breathing(10.5, 0.08), 1.0)
    at_(WT(6, "feel"), lambda: heartbeat(1.0), 0.9)
    at_(WT(6, "feel") + 0.85, lambda: heartbeat(1.0), 0.8)
    at_(WT(7, "slides"), lambda: squish(0.4), 0.7, -0.3)
    at_(WT(7, "kelp") - 0.15, lambda: hit(0.6), 0.6)
    at_(WT(8, "pulls"), lambda: squish(0.4), 0.7)
    at_(WT(8, "testing"), lambda: squish(0.4), 0.6)
    at_(S(9), lambda: sub_boom(0.8), 0.9)
    at_(WT(9, "giant"), lambda: whoosh(0.6, True, 0.4), 0.6)
    at_(WT(10, "great"), lambda: whoosh(0.8, True, 0.4), 0.5, -0.4)
    at_(WT(10, "orca"), lambda: whoosh(0.8, True, 0.4), 0.5, 0.4)
    for w in ("bones", "shell", "fins"):
        at_(WT(12, w) + 0.25, lambda: error_beep(0.25), 0.5)
    at_(WT(13, "largest"), lambda: hit(0.6), 0.7)
    at_(WT(13, "hunts"), lambda: thud(0.6), 0.8)
    at_(WT(13, "disappear"), lambda: whoosh(1.2, False, 0.4), 0.6)
    at_(S(14), lambda: sub_boom(0.7), 0.8)
    # chapters
    for i in (15, 25, 34, 43, 52):
        at_(S(i), lambda: whoosh(0.7, True, 0.45), 0.6)
        at_(S(i) + 0.2, lambda: ding(880, 0.3), 0.4)
    at_(WT(16, "weigh"), lambda: pop(600, 0.4), 0.6)
    at_(WT(16, "arms"), lambda: riser(1.4, 0.25), 0.5)
    at_(WT(18, "dog"), lambda: pop(500, 0.5), 0.6)
    for k in range(4):
        at_(S(19) + 0.2 + k * 0.45, lambda: squish(0.3), 0.4)
    at_(S(20), lambda: radar(2.5, 0.12), 0.7)
    at_(WT(20, "single"), lambda: error_beep(0.25), 0.5)
    at_(S(21) + 0.6, lambda: chime_sparkle(0.3), 0.5)
    at_(WT(23, "coin"), lambda: ding(1568, 0.4), 0.6)
    at_(WT(24, "pour"), lambda: squish(0.4), 0.6)
    at_(WT(24, "pour") + 0.6, lambda: squish(0.4), 0.5)
    for w, f in (("crabs", 600), ("clams", 680), ("snails", 760), ("lobsters", 840)):
        at_(WT(26, w) - 0.1, lambda f=f: pop(f, 0.4), 0.6)
    at_(WT(27, "fish") - 0.1, lambda: pop(920, 0.4), 0.6)
    at_(WT(28, "sharks"), lambda: sub_boom(0.9), 1.0)
    at_(WT(28, "sharks"), lambda: hit(0.8), 0.8)
    at_(WT(29, "catching"), lambda: whoosh(0.4, True, 0.4), 0.6)
    at_(WT(29, "wrapping"), lambda: squish(0.5), 0.7)
    at_(WT(29, "pulling"), lambda: squish(0.5), 0.7)
    for i, w in enumerate(("octopus", "shark", "remains", "dens")):
        at_(WT(30, w), lambda: pop(700 + i * 60, 0.35), 0.5)
    at_(WT(32, "receipt"), lambda: printer(1.6, 0.2), 0.8, 0.4)
    at_(WT(33, "receipt"), lambda: error_beep(0.3), 0.6)
    at_(S(36), lambda: radar(3.4, 0.14), 0.7)
    at_(WT(36, "sound"), lambda: error_beep(0.3), 0.5)
    for k in range(16):
        at_(WT(37, "2") + k * 0.1, lambda: tick(0.25), 0.5)
    at_(WT(38, "plain"), lambda: error_beep(0.25), 0.5)
    at_(WT(39, "taste"), lambda: chime_sparkle(0.3), 0.5)
    at_(S(40), lambda: squish(0.4), 0.5)
    at_(WT(42, "long"), lambda: ding(1318, 0.4), 0.6)
    at_(WT(44, "disappear"), lambda: whoosh(1.2, False, 0.4), 0.6)
    at_(WT(45, "millions"), lambda: chime_sparkle(0.3), 0.4)
    for w in ("sand", "seaweed", "stone"):
        at_(WT(46, w), lambda: whoosh(0.35, True, 0.3), 0.5)
    for k in range(3):
        at_(S(46) + k * 0.33, lambda: tick(0.3), 0.6)
    at_(WT(46, "bumps"), lambda: pop(900, 0.3), 0.5)
    at_(WT(50, "blinking"), lambda: pop(300, 0.5), 0.7)
    at_(WT(56, "nine"), lambda: hit(0.7), 0.8)
    for i in range(3):
        at_(WT(57, "three") + i * 0.12, lambda: heartbeat(0.8), 0.5)
    at_(WT(57, "blue"), lambda: drop_plink(0.4), 0.6)
    at_(WT(57, "iron") + 0.25, lambda: error_beep(0.25), 0.5)
    at_(WT(60, "open"), lambda: creak(1.4, 0.3), 0.6)
    at_(WT(60, "individual"), lambda: ding(1318, 0.35), 0.5)
    for k in range(6):
        at_(WT(61, "squirting") + k * 0.6, lambda: drop_plink(0.3), 0.5, 0.3)
    at_(WT(61, "short"), lambda: static_burst(0.5, 0.3), 0.9)
    at_(WT(61, "short") + 0.3, lambda: snap(0.5), 0.6)
    at_(WT(61, "lights"), lambda: click(0.8), 1.0)
    at_(WT(63, "plan"), lambda: sub_boom(0.8), 0.9)
    # part 2
    at_(S(64), lambda: whoosh(0.8, True, 0.4), 0.5)
    at_(S(67), lambda: creak(2.0, 0.3), 0.6)
    at_(WT(67, "dragging"), lambda: rumble(3.0, 0.25), 0.8)
    at_(WT(68, "imagination"), lambda: chime_sparkle(0.3), 0.5)
    at_(S(70), lambda: sub_boom(0.7), 0.8)
    at_(WT(71, "problem"), lambda: hit(0.6), 0.6)
    for i in range(4):
        at_(WT(73, "down") + 0.2 + i * 0.3, lambda: pop(600 + i * 80, 0.4), 0.5)
    for t in (E(77) - 0.6, E(81) - 0.5, E(84) - 0.4, E(86) - 0.4):
        at_(t, lambda: scribble(0.3, 0.25), 0.7)
    at_(WT(75, "jet"), lambda: whoosh(0.9, True, 0.6), 0.9)
    at_(S(78), lambda: rumble(5.0, 0.15), 0.6)
    at_(WT(81, "kitchen"), lambda: hit(0.5), 0.6)
    for k in range(4):
        at_(WT(84, "feel") + k * 0.4, lambda: radar(0.6, 0.08), 0.4)
    for t in (S(85) + 0.1, WT(86, "more", 0), WT(86, "more", 1), WT(86, "arms"), WT(86, "join"), WT(86, "in")):
        at_(t, lambda: squish(0.4), 0.6)
    at_(WT(87, "cloud") - 0.3, lambda: whoosh(1.4, False, 0.6), 0.9)
    at_(WT(87, "cloud") - 0.3, lambda: rumble(2.0, 0.25), 0.7)
    at_(S(90), lambda: breathing(5.0, 0.09), 1.0)
    at_(WT(93, "not"), lambda: hit(0.7), 0.8)
    at_(WT(95, "never"), lambda: chime_sparkle(0.35), 0.6)
    for i in range(16):
        at_(WT(97, "meet") + i * 0.1, lambda: pop(800 + (i % 4) * 60, 0.25), 0.4)
    at_(WT(98, "backs"), lambda: whoosh(0.8, False, 0.3), 0.5)
    at_(S(101), lambda: bubble_burst(10, 0.4), 0.7)
    at_(S(101) + 1.2, lambda: bubble_burst(10, 0.4), 0.6)
    at_(S(102), lambda: buzz(3.3, 0.1), 0.8, 0.4)
    at_(WT(103, "other"), lambda: whoosh(0.6, True, 0.4), 0.6)
    at_(WT(105, "weakens"), lambda: whoosh(1.8, False, 0.3), 0.5)
    at_(WT(106, "tens"), lambda: riser(1.4, 0.2), 0.5)
    at_(WT(110, "hatch"), lambda: chime_sparkle(0.35), 0.7)
    at_(WT(110, "hatch") + 0.6, lambda: chime_sparkle(0.3), 0.5)
    for w in ("fishing", "crab", "heat"):
        at_(WT(113, w) - 0.1, lambda: thud(0.5), 0.6)
    at_(WT(114, "monster"), lambda: hit(0.6), 0.7)
    at_(WT(114, "this"), lambda: scribble(0.3, 0.25), 0.6)
    for w in ("crabs", "shrimp", "otters", "seals", "sharks"):
        at_(WT(115, w) - 0.1, lambda: pop(700, 0.35), 0.5)
    at_(S(119), lambda: rumble(4.0, 0.15), 0.6)
    for w in ("nine", "three", "two"):
        at_(WT(120, w), lambda: tick(0.4), 0.8)
    at_(WT(120, "watching"), lambda: sub_boom(0.7), 0.8)
    at_(S(122), lambda: ding(1046, 0.4), 0.6)
    for k in range(18):
        at_(WT(123, "sea") + k * 0.1, lambda: click(0.3), 0.3)
    for t, fn, g, pan in ev:
        s.add(fn(), t, g, pan)
    return s.stereo(int(dur * SR))


def build_ambience(dur):
    a = Track(dur)
    bed = underwater_bed(dur)
    a.add(bed, 0.0, 0.05)
    t = 0.0
    while t < dur - 2:
        a.add(bubble_blip(0.3), t, 0.25, pan=float(rng.uniform(-0.6, 0.6)))
        t += float(rng.uniform(1.5, 5.0))
    return a.stereo(int(dur * SR))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    voice = load_audio(a.voice)
    tail = int(1.5 * SR)
    voice = np.concatenate([voice, np.zeros(tail)])
    dur = len(voice) / SR
    music = build_music(dur)
    fx = build_sfx(dur)
    amb = build_ambience(dur)
    n = min(len(voice), len(music), len(fx), len(amb))
    voice, music, fx, amb = voice[:n], music[:n], fx[:n], amb[:n]

    def norm(x, peak):
        m = np.max(np.abs(x)) or 1.0
        return x / m * peak

    music = norm(music, 1.0)
    env = envelope(voice)
    env = env / (np.percentile(env, 95) + 1e-9)
    duck = lp(1.0 - 0.55 * np.clip(env, 0, 1), 6, 1)
    music *= (0.17 * duck)[:, None]
    fx = norm(fx, 0.42)
    amb = norm(amb, 0.10)
    v = voice / (np.max(np.abs(voice)) or 1.0) * 0.92
    mix = np.stack([v, v], axis=1) + music + fx + amb
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    wavfile.write(a.out, SR, (np.clip(mix, -1, 1) * 32767).astype(np.int16))
    print("wrote", a.out, n / SR)


if __name__ == "__main__":
    main()
