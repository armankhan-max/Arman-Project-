"""Original synthesized soundtrack for "What If You Jumped on Every World?".

Re-uses the synth instruments, music cues and mixer from ../video/audio.py; only the score
(which cue plays where) and the sound-effect timeline are specific to this video.

Usage:
  python audio_jump.py --voice voice.mp3 --out mix.wav
"""
import argparse
import os
import sys

import numpy as np
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
import audio as A  # noqa: E402
from audio import (SR, Track, cue_tense, cue_curious, cue_night, cue_warm, cue_tension, cue_hope,  # noqa: E402
                   cue_roadtrip, final_chord, fade_region, whoosh, pop, ding, chime_sparkle, buzzer, tick, hit,
                   riser, kick, squish, wind, edge_env, engine_hum, click, load_audio, envelope, lp)

sys.path.insert(0, HERE)


def build_music(dur):
    m = Track(dur)
    cue_tense(m, 0.0, 11.2, 0.7)
    cue_curious(m, 11.2, 28.4, bpm=96, gain=0.9)
    cue_curious(m, 28.4, 49.3, bpm=100, gain=0.9)
    cue_hope(m, 55.7, 96.3, build=0.0)
    cue_roadtrip(m, 96.3, 123.8, bpm=108, gain=0.7)
    cue_tense(m, 123.8, 141.9, 0.6, bpm=66)
    cue_tense(m, 141.9, 178.2, 0.9, bpm=72)
    cue_tension(m, 178.2, 205.7, bpm=92, gain=0.9)
    cue_curious(m, 205.7, 237.6, bpm=92, gain=0.85)
    cue_night(m, 237.6, 286.8)
    cue_tense(m, 286.8, 338.5, 0.7, bpm=60)
    cue_tension(m, 338.5, 389.3, bpm=100, gain=0.9)
    cue_hope(m, 389.3, 429.4, build=0.3)
    cue_warm(m, 429.4, 446.0)
    final_chord(m, 447.4, ["D3", "F#3", "A3", "D4"], 0.45, 3.0)
    x = m.stereo(int(dur * SR))
    # moments of silence make the big beats land harder
    x = fade_region(x, 49.6, 55.5, 0.6)
    x = fade_region(x, 290.2, 291.6, 0.2)
    x = fade_region(x, 319.4, 322.0, 0.4)
    x = fade_region(x, 361.6, 363.0, 0.2)
    return x


JUMPS = [  # (take-off time, air time) for the thump/landing sounds
    (1.3, 4.2), (9.3, 0.45), (33.4, 0.62), (48.2, 0.62), (64.5, 3.7), (73.0, 0.62), (74.9, 3.7), (104.2, 1.6),
    (107.9, 1.6), (116.8, 1.6), (132.9, 1.1), (147.0, 0.68), (165.0, 0.68), (199.6, 0.24), (214.4, 0.57),
    (218.4, 0.57), (227.0, 0.69), (231.3, 0.54), (249.3, 9.7), (269.4, 99), (280.2, 5.0), (319.6, 99),
    (357.6, 0.05), (413.5, 0.62)
]
for k in range(4):
    JUMPS.append((12.6 + k * 2.4, 0.62))
JUMPS += [(199.6 + 1.6, 0.24)]


def build_sfx(dur, cuts):
    s = Track(dur)

    def add(at, x, g=1.0, pan=0.0):
        if 0 <= at < dur:
            s.add(x, at, g, pan)

    for ct in cuts:
        add(ct - 0.25, whoosh(0.5, True, 0.35), 0.6)
    for t0, T in JUMPS:
        add(t0 - 0.05, whoosh(0.35, True, 0.3), 0.5)
        add(t0, pop(220, 0.4), 0.5)
        if T < 50:
            add(t0 + T, kick(0.25, 90, 40), 0.55)
    for t0 in (55.8, 99.9, 142.0, 179.7, 205.8, 245.9, 262.6, 277.4, 316.0, 346.7, 367.2):
        add(t0, chime_sparkle(0.35), 0.7)
    for t0 in (4.9, 12.9, 37.2, 65.2, 68.5, 105.0, 118.6, 147.4, 192.9, 215.8, 219.0, 227.9, 232.5, 250.2, 270.5,
               280.9, 355.0, 393.2, 394.5, 395.8, 397.4, 398.8, 401.0, 403.1, 414.9):
        add(t0, ding(1318.5, 0.35), 0.6)
    for t0 in (0.9, 7.0, 9.6, 15.7, 16.9, 25.9, 26.4, 27.6, 44.3, 46.6, 48.1, 51.5, 83.6, 88.4, 91.6, 95.3, 98.7,
               110.9, 120.6, 121.4, 128.3, 129.6, 134.0, 136.8, 139.9, 141.6, 152.0, 164.9, 169.4, 173.4, 182.3,
               197.4, 203.4, 209.7, 233.4, 237.9, 264.9, 272.3, 274.9, 287.4, 297.4, 314.0, 319.0, 322.5, 335.1,
               335.6, 336.7, 340.2, 342.6, 370.6, 375.2, 379.5, 387.8, 406.0, 407.9, 410.0, 417.4, 423.1, 423.6,
               424.3, 425.3, 426.4, 427.3, 433.1, 438.4, 440.8, 441.4, 442.2, 444.0):
        add(t0, pop(700, 0.35), 0.5)
    for t0 in (18.4, 126.6, 337.3):
        add(t0, buzzer(0.3), 0.45)
    for t0 in (290.4, 361.8, 447.6, 9.6):
        add(t0, hit(0.6), 0.8)
    add(386.9, squish(0.5), 0.9)
    add(52.0, riser(3.6, 0.35), 0.7)
    add(176.2, riser(1.8, 0.3), 0.5)
    # stopwatch ticks
    for a, b in ((71.5, 78.6), (108.6, 110.6), (259.0, 261.0)):
        x = a
        while x < b:
            add(x, tick(0.3), 0.6)
            x += 0.25
    # counters
    for a, b in ((158.4, 159.4), (375.2, 376.6)):
        x = a
        while x < b:
            add(x, click(0.3), 0.4)
            x += 0.07
    return s.stereo(int(dur * SR))


def build_ambience(dur):
    a = Track(dur)
    for k, (s0, s1, g) in enumerate(((99.6, 141.9, 0.10), (223.3, 237.6, 0.14), (141.9, 155.4, 0.06),
                                     (183.7, 205.7, 0.07))):
        w = wind(s1 - s0 + 1.0, 1.0, seed=k)
        a.add(w * edge_env(len(w), 0.8), s0, g, pan=0.15 if k % 2 else -0.15)
    a.add(engine_hum(14.0, 38, 0.06, 1.5), 346.6, 1.0)  # solar rumble
    a.add(engine_hum(13.5, 30, 0.05, 1.5), 141.9, 1.0)  # venus rumble
    return a.stereo(int(dur * SR))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import importlib.util
    spec = importlib.util.spec_from_file_location("scenes_jump", os.path.join(HERE, "scenes_jump.py"))
    sj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sj)

    voice = load_audio(a.voice)
    dur = len(voice) / SR
    music = build_music(dur)
    fx = build_sfx(dur, sj.CUTS)
    amb = build_ambience(dur)

    def norm(x, peak):
        m = np.max(np.abs(x)) or 1.0
        return x / m * peak

    n = min(len(voice), len(music), len(fx), len(amb))
    voice, music, fx, amb = voice[:n], music[:n], fx[:n], amb[:n]
    music = norm(music, 1.0)
    env = envelope(voice)
    env = env / (np.percentile(env, 95) + 1e-9)
    duck = lp(1.0 - 0.55 * np.clip(env, 0, 1), 6, 1)
    music *= (0.30 * duck)[:, None]
    fx = norm(fx, 0.5)
    amb = norm(amb, 0.2)
    v = voice / (np.max(np.abs(voice)) or 1.0) * 0.92
    mix = np.stack([v, v], axis=1) + music + fx + amb
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    wavfile.write(a.out, SR, (np.clip(mix, -1, 1) * 32767).astype(np.int16))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
