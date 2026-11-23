"""Procedural soundtrack for the Lucia video: synthwave/drama music cues, ~200 SFX on word times, ambience.

Everything is synthesized (no samples), so the soundtrack is original and royalty-free.

Usage:
  python audio_g6.py --voice voice.mp3 --out mix.wav
"""
import argparse
import os
import sys

import numpy as np
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
sys.path.insert(0, HERE)
import audio as A  # noqa: E402
from audio import (SR, Track, tt, env_adsr, lp, hp, bp, noise, midi, nm, CHORDS, fz, pluck, marimba, bell_tone,  # noqa
                   pad, bass, kick, hat, shaker, clap, heartbeat, whoosh, pop, click, ding, chime_sparkle, buzzer,
                   error_beep, tick, hit, riser, crickets, wind, car_drive, shutter, cue_tense, cue_curious, cue_night,
                   cue_warm, cue_tension, cue_hope, final_chord, fade_region, load_audio, envelope)

rng = np.random.default_rng(7)


# ------------------------------------------------------------------ extra instruments / sfx
def saw(f, dur, bright=1.0):
    t = tt(dur)
    x = np.zeros_like(t)
    for k in range(1, 12):
        x += ((-1) ** (k + 1)) * np.sin(2 * np.pi * f * k * t) / k * (bright ** (k - 1))
    return x


def synth_arp(f, dur=0.25):
    x = saw(f, dur, 0.8) * env_adsr(int(dur * SR), 0.005, 0.08, 0.3, 0.08)
    return lp(x, 2600)


def gated_snare(gain=0.5):
    n = noise(0.28) * env_adsr(int(0.28 * SR), 0.001, 0.05, 0.6, 0.05)
    x = bp(n, 300, 6000) + 0.4 * np.sin(2 * np.pi * 190 * tt(0.28)) * env_adsr(int(0.28 * SR), 0.001, 0.06, 0.0, 0.0)
    return x * gain


def siren(dur=2.0, gain=0.25):
    t = tt(dur)
    f = 700 + 350 * np.sin(2 * np.pi * 0.9 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.3 * np.sin(2 * ph)
    return lp(x, 3000) * gain * env_adsr(len(t), 0.2, 0.1, 1.0, 0.4)


def alarm_bell(dur=2.0, gain=0.25):
    t = tt(dur)
    x = np.sign(np.sin(2 * np.pi * 18 * t)) * np.sin(2 * np.pi * 1450 * t)
    return lp(x, 4000) * gain * env_adsr(len(t), 0.01, 0.1, 1.0, 0.2)


def fire_crackle(dur=3.0, gain=0.3):
    base = lp(noise(dur), 900) * 0.4
    n = len(base)
    cr = np.zeros(n)
    for _ in range(int(dur * 25)):
        i = rng.integers(0, n - 400)
        cr[i:i + 400] += hp(noise(400 / SR), 2000) * np.exp(-np.arange(400) / 60) * rng.uniform(0.3, 1)
    return (base + cr) * gain * A.edge_env(n, 0.5)


def boom(gain=0.8):
    k = kick(0.9, 80, 30, 1.0)
    n = lp(noise(1.2), 500) * env_adsr(int(1.2 * SR), 0.005, 0.2, 0.3, 0.8)
    out = np.zeros(int(1.2 * SR))
    out[:len(k)] += k
    out += n * 0.8
    return out * gain


def pew(gain=0.35):
    """Cartoon blaster pop (kept non-realistic on purpose)."""
    t = tt(0.18)
    f = 1800 * np.exp(-t * 18) + 200
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)
    return x * gain


def splash(gain=0.6):
    n = noise(1.4)
    x = lp(n, 2500) * env_adsr(len(n), 0.01, 0.3, 0.3, 1.0)
    return x * gain


def bubbles(dur=2.0, gain=0.25):
    out = np.zeros(int(dur * SR))
    for _ in range(int(dur * 8)):
        i = rng.integers(0, len(out) - 3000)
        f0 = rng.uniform(400, 900)
        t = tt(3000 / SR)
        out[i:i + 3000] += np.sin(2 * np.pi * (f0 + 3000 * t) * t) * np.exp(-t * 40)
    return out * gain


def waves(dur, gain=0.1, seed=0):
    w = wind(dur, 1.0, seed=seed)
    t = tt(dur)
    mod = 0.55 + 0.45 * np.sin(2 * np.pi * 0.12 * t + seed)
    return lp(w, 900)[:len(t)] * mod * gain


def crowd(dur, gain=0.08):
    return bp(noise(dur), 300, 2500) * gain


def coin(gain=0.3):
    return (bell_tone(midi(nm("E6")), 0.4) + bell_tone(midi(nm("B6")), 0.4)) * gain


def kiss_chime(gain=0.35):
    return chime_sparkle(gain)


def metal_slam(gain=0.7):
    t = tt(1.2)
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in ((180, 4), (437, 6), (911, 8), (1460, 10)))
    out = x * 0.25
    h = hit(0.6)
    out[:len(h)] += h
    return out * gain


def cue_synth(tr, a, b, bpm=104, gain=1.0, minor=True):
    """Vice City synthwave: four-on-floor-ish kick, gated snare, saw arps, warm pad."""
    prog = ["Am", "F", "C", "G"] if minor else ["F", "C", "G", "Am"]
    beat = 60 / bpm
    bar = beat * 4
    t, i = a, 0
    while t < b - 0.05:
        ch = prog[i % 4]
        notes = [nm(n) for n in CHORDS[ch]]
        tr.add(pad(fz(CHORDS[ch][:4]), min(bar, b - t) + 1.0, 0.4, 1.0, 0.5), t, 0.22 * gain)
        for k in range(16):
            nt = t + k * beat / 4
            if nt >= b:
                break
            idx = [0, 2, 4, 3][k % 4] + (1 if k >= 8 else 0)
            tr.add(synth_arp(midi(notes[min(idx, 5)] + 12), beat / 4 * 0.9), nt, 0.12 * gain,
                   pan=-0.35 if k % 2 else 0.35)
        for k in range(4):
            bt = t + k * beat
            if bt >= b:
                continue
            tr.add(kick(0.35, 100, 40), bt, 0.32 * gain)
            if k in (1, 3):
                tr.add(gated_snare(), bt, 0.3 * gain)
            tr.add(lp(saw(midi(notes[0] - 12), beat * 0.45, 0.6), 500) * env_adsr(int(beat * 0.45 * SR), 0.005,
                                                                                    0.1, 0.6, 0.05),
                   bt + beat / 2, 0.22 * gain)
            tr.add(hat(), bt + beat / 2, 0.35 * gain, pan=0.3)
        t += bar
        i += 1


# ------------------------------------------------------------------ score (licensed tracks)
# Music: Kevin MacLeod (incompetech.com), licensed under Creative Commons: By Attribution 4.0.
MUSIC_DIR = os.environ.get("MUSIC_DIR", os.path.join(HERE, "music"))
CUES = [  # (start, end, track, offset_in_track, gain)
    (0.0, 34.7, "Investigations", 0.0, 1.0),
    (34.7, 69.7, "Sneaky_Snitch", 0.0, 0.9),
    (69.7, 94.3, "Volatile_Reaction", 0.0, 1.0),
    (94.3, 136.4, "Dark_Fog", 0.0, 1.1),
    (136.4, 158.1, "Night_on_the_Docks_-_Sax", 0.0, 1.0),
    (158.1, 191.6, "Hitman", 0.0, 0.9),
    (191.6, 212.4, "Volatile_Reaction", 60.0, 1.0),
    (212.4, 252.9, "Mining_by_Moonlight", 0.0, 1.0),
    (252.9, 283.3, "Crypto", 0.0, 1.0),
    (283.3, 314.3, "Funkorama", 0.0, 0.9),
    (314.3, 350.9, "Rollin_at_5", 0.0, 0.9),
    (350.9, 372.3, "Crypto", 70.0, 1.0),
    (372.3, 402.4, "Sad_Trio", 0.0, 1.1),
    (402.4, 437.8, "Hitman", 70.0, 0.9),
    (437.8, 479.6, "Volatile_Reaction", 100.0, 1.0),
    (479.6, 501.9, "Heartwarming", 0.0, 1.1),
    (501.9, 521.5, "Sad_Trio", 80.0, 1.1),
    (521.5, 572.4, "Investigations", 20.0, 1.0),
    (572.4, 613.6, "Bass_Walker", 0.0, 0.9),
    (613.6, 645.2, "Lightless_Dawn", 0.0, 1.2),
    (645.2, 666.9, "Heartwarming", 10.0, 1.1),
    (666.9, 709.5, "Lightless_Dawn", 120.0, 1.2),
    (709.5, 734.6, "Funkorama", 60.0, 0.9),
    (734.6, 761.0, "Night_on_the_Docks_-_Sax", 40.0, 1.0),
]
_trk = {}


def track(name):
    if name not in _trk:
        path = os.path.join(MUSIC_DIR, name + ".mp3")
        raw = A.subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                               capture_output=True, check=True).stdout
        x = np.frombuffer(raw, np.float32).astype(np.float64).reshape(-1, 2)
        _trk[name] = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * 0.2     # loudness-match every track
    return _trk[name]


def build_music(dur):
    n = int(dur * SR) + SR
    out = np.zeros((n, 2))
    fade = 1.2
    for a, b, name, off, g in CUES:
        x = track(name)
        need = int((b - a + fade) * SR)
        i0 = int(off * SR)
        seg = x[i0:i0 + need]
        while len(seg) < need:   # loop if the cue is longer than the track
            seg = np.concatenate([seg, x[:need - len(seg)]])
        L = len(seg)
        env = np.ones(L)
        fi = int((0.6 if a > 0 else 0.05) * SR)
        fo = int(fade * SR)
        env[:fi] = np.linspace(0, 1, fi)
        env[-fo:] = np.linspace(1, 0, fo)
        i = int(a * SR)
        j = min(n, i + L)
        out[i:j] += seg[: j - i] * env[: j - i, None] * g
    out = out[: int(dur * SR)]
    for a, b in ((384.2, 385.6), (700.6, 703.0), (276.6, 279.4)):
        out = fade_region(out, a, b, 0.25)
    return out


def build_music_synth(dur):
    m = Track(dur)
    cue_tension(m, 0.0, 13.4, bpm=96, gain=0.9)
    cue_warm(m, 13.4, 34.7, bpm=84)
    cue_curious(m, 34.7, 46.8, bpm=100)
    cue_tense(m, 46.8, 57.2, 0.8)
    cue_hope(m, 57.2, 69.7, build=0.3)
    cue_tension(m, 69.7, 94.3, bpm=112, gain=1.0)
    cue_night(m, 94.3, 117.0)
    cue_warm(m, 117.0, 136.4, bpm=80)
    cue_hope(m, 136.4, 152.4, build=0.5)
    cue_curious(m, 152.4, 158.1, bpm=104, gain=0.8)
    cue_synth(m, 158.1, 174.4, bpm=100, gain=0.9)
    cue_tension(m, 174.4, 191.6, bpm=96)
    cue_tense(m, 191.6, 212.4, 1.0, heart=(203.0, 212.0), bpm=70)
    cue_night(m, 212.4, 240.2)
    cue_synth(m, 240.2, 252.9, bpm=108, gain=0.9)
    cue_tense(m, 252.9, 276.6, 0.9)
    final_chord(m, 280.0, ["A2", "E3", "A3", "C4"], 0.5, 3.5)
    cue_synth(m, 283.3, 314.3, bpm=112, gain=1.0)
    cue_warm(m, 314.3, 324.6, bpm=84)
    cue_curious(m, 324.6, 350.9, bpm=100, gain=0.9)
    cue_tension(m, 350.9, 372.3, bpm=100)
    cue_night(m, 372.3, 402.4)
    cue_tension(m, 402.4, 437.8, bpm=104)
    cue_tense(m, 437.8, 459.4, 1.0, bpm=80)
    cue_tension(m, 459.4, 479.6, bpm=90)
    cue_hope(m, 479.6, 501.9, build=0.2)
    cue_night(m, 501.9, 521.5)
    cue_warm(m, 521.5, 538.7, bpm=80)
    cue_curious(m, 538.7, 572.4, bpm=96, gain=0.85)
    cue_hope(m, 572.4, 613.6, build=0.3)
    cue_tense(m, 613.6, 623.9, 0.9)
    cue_night(m, 623.9, 645.2)
    cue_hope(m, 645.2, 666.9, build=0.5)
    cue_tense(m, 666.9, 682.9, 0.9)
    cue_tense(m, 682.9, 709.5, 1.1, heart=(691.6, 700.6), bpm=66)
    cue_synth(m, 709.5, 734.6, bpm=104, gain=0.9)
    cue_warm(m, 734.6, 756.0, bpm=80)
    final_chord(m, 756.2, ["C3", "G3", "C4", "E4"], 0.5, 5.0)
    x = m.stereo(int(dur * SR))
    for a, b in ((276.6, 279.6), (384.2, 385.6), (700.6, 703.0), (283.3, 283.9)):
        x = fade_region(x, a, b, 0.25)
    return x


SFX = []


def sfx(at, fn, gain=1.0, pan=0.0):
    SFX.append((at, fn, gain, pan))


def build_sfx(dur, cuts, wt):
    s = Track(dur)
    # hook
    sfx(wt("punch", 3.3), lambda: hit(0.7), 1.0)
    sfx(wt("punch", 3.3), lambda: pop(300, 0.5), 0.8)
    sfx(5.2, lambda: metal_slam(0.8), 0.9)
    sfx(wt("trust", 8.0), shutter, 0.6)
    sfx(wt("way", 11.4), lambda: pop(700, 0.5), 0.6)
    sfx(wt("end", 12.4), lambda: pop(500, 0.5), 0.6)
    sfx(wt("wants", 16.0), lambda: coin(0.3), 0.8)
    sfx(wt("dream", 22.0), chime_sparkle, 0.6)
    for w_, n_ in (("money", 26.7), ("safety", 27.5), ("door", 28.9)):
        sfx(wt(w_, n_) + 0.1, lambda: ding(1318.5, 0.4), 0.7)
    sfx(wt("locks", 29.9), click, 1.0)
    sfx(wt("locks", 29.9) + 0.12, click, 0.8)
    sfx(wt("decides", 32.5), lambda: hit(0.6), 0.7)
    sfx(wt("gift", 36.4), lambda: pop(800, 0.5), 0.6)
    for w_, n_ in (("fists", 40.7), ("chin", 41.4), ("hit", 42.2)):
        sfx(wt(w_, n_), lambda: hit(0.5), 0.8)
    for k in range(5):
        sfx(42.3 + k * 0.6, lambda: pop(250, 0.4), 0.5)
    sfx(wt("love", 46.3), chime_sparkle, 0.6)
    sfx(wt("rigged", 50.0), lambda: hit(0.7), 0.9)
    for k in range(18):
        sfx(53.8 + k * 2.6 / 18, lambda: tick(0.3), 0.5)
    sfx(wt("gone", 55.9), lambda: buzzer(0.25), 0.5)
    for w_, n_ in (("sharp", 57.6), ("stubborn", 58.1), ("loyal", 58.6)):
        sfx(wt(w_, n_), lambda: pop(650, 0.5), 0.7)
    for k in range(4):
        sfx(62.1 + k * 0.57, lambda: hit(0.5), 0.6)
    sfx(wt("tommy", 65.6), chime_sparkle, 0.7)
    sfx(wt("worst", 70.7), lambda: hit(0.8), 0.9)
    sfx(wt("wrong", 74.5), lambda: hit(0.7), 0.9)
    sfx(wt("alarms", 75.4), lambda: alarm_bell(2.6, 0.22), 0.8)
    sfx(wt("sirens", 76.3), lambda: siren(3.2, 0.2), 0.8)
    sfx(77.4, lambda: car_drive(1.8), 1.2)
    for k in range(10):
        sfx(81.1 + k * 0.32, lambda: tick(0.3), 0.6)
    sfx(wt("reported", 85.5), lambda: error_beep(0.3), 0.6)
    sfx(84.4, lambda: siren(4.0, 0.12), 0.6)
    sfx(wt("handcuffs", 89.4), click, 1.0)
    sfx(wt("handcuffs", 89.4) + 0.15, click, 1.0)
    sfx(94.4, lambda: metal_slam(0.8), 1.0)
    sfx(wt("orange", 95.4), lambda: pop(600, 0.4), 0.6)
    sfx(103.8, lambda: pop(500, 0.4), 0.6)
    sfx(104.4, lambda: pop(700, 0.4), 0.6)
    sfx(wt("early", 108.8), lambda: pop(700, 0.4), 0.6)
    sfx(117.0, shutter, 0.8)
    sfx(117.05, lambda: hit(0.6), 0.6)
    sfx(wt("partner", 119.0), lambda: pop(800, 0.4), 0.6)
    sfx(wt("while", 119.9), lambda: metal_slam(0.4), 0.5)
    for w_, n_ in (("rich", 127.0), ("safe", 128.4)):
        sfx(wt(w_, n_), lambda: hit(0.5), 0.7)
    sfx(wt("possible", 131.6), chime_sparkle, 0.6)
    sfx(wt("luck", 138.0), chime_sparkle, 0.7)
    sfx(wt("released", 139.5), lambda: metal_slam(0.5), 0.5)
    sfx(wt("released", 139.5) + 0.2, lambda: hit(0.6), 0.7)
    sfx(143.4, lambda: ding(2637, 0.35), 0.7)
    sfx(143.45, lambda: ding(3136, 0.3), 0.6)
    sfx(wt("subscribe", 152.8) + 0.8, click, 1.0)
    sfx(wt("subscribe", 152.8) + 1.0, lambda: ding(1568, 0.4), 0.8)
    sfx(wt("comments", 155.0), lambda: pop(700, 0.4), 0.6)
    for k in range(16):
        sfx(158.2 + k * 0.33, lambda: tick(0.3), 0.6)
    sfx(wt("money", 160.6), lambda: coin(0.4), 0.8)
    sfx(wt("costs", 163.6), lambda: pop(500, 0.4), 0.6)
    
    sfx(wt("natural", 172.9), lambda: hit(0.5), 0.6)
    sfx(wt("pays", 177.9), lambda: coin(0.4), 0.7)
    sfx(wt("trap", 179.9), lambda: pop(400, 0.4), 0.6)
    sfx(wt("yes", 189.0), lambda: hit(0.6), 0.8)
    for k in range(6):
        sfx(wt("domino", 190.7) + k * 0.12, lambda: click(0.5), 0.8)
    sfx(191.7, lambda: hit(0.8), 1.0)
    sfx(191.7, lambda: siren(5.0, 0.2), 0.8)
    sfx(wt("burn", 200.2) - 0.3, lambda: boom(0.7), 0.8)
    sfx(wt("burn", 200.2), lambda: fire_crackle(3.5, 0.35), 0.8)
    for w_, n_ in (("money", 213.9), ("friends", 214.6), ("plan", 215.4)):
        sfx(wt(w_, n_) + 0.1, lambda: buzzer(0.2), 0.5)
    for w_, n_ in (("supplies", 222.0), ("painkillers", 223.4), ("local", 224.4)):
        sfx(wt(w_, n_), lambda: pop(600, 0.4), 0.6)
    sfx(wt("kidnapping", 228.5), lambda: hit(0.7), 0.8)
    sfx(wt("dead", 231.6), lambda: hit(0.7), 0.8)
    sfx(wt("worth", 235.0), lambda: pop(400, 0.4), 0.6)
    for k in range(5):
        sfx(wt("small", 240.6) + k * 0.7, lambda: ding(1760, 0.35), 0.6)
    sfx(wt("scarily", 244.5), lambda: hit(0.5), 0.6)
    sfx(wt("huge", 251.6), lambda: hit(0.7), 0.8)
    sfx(wt("vice", 257.0), chime_sparkle, 0.8)
    sfx(wt("hunters", 258.4), lambda: hit(0.7), 0.8)
    sfx(wt("bag", 267.6), lambda: hit(0.5), 0.6)
    
    sfx(wt("close", 273.5), lambda: hit(0.6), 0.8)
    for w_, n_ in (("bank", 281.2), ("betrayal", 281.8), ("bridge", 282.7)):
        sfx(wt(w_, n_), lambda: hit(0.5), 0.6)
    sfx(wt("slap", 283.6), lambda: clap(0.9), 1.0)
    sfx(wt("slap", 283.6), lambda: hit(0.6), 0.8)
    for k in range(10):
        sfx(288.6 + k * 0.18, lambda: coin(0.25), 0.4)
    sfx(wt("dollar", 291.5), lambda: buzzer(0.25), 0.5)
    sfx(wt("nightclub", 298.0) - 0.2, shutter, 0.7)
    sfx(wt("raul", 300.0) - 0.2, shutter, 0.7)
    sfx(wt("plan", 304.5), lambda: pop(500, 0.4), 0.6)
    for k in range(14):
        sfx(309.0 + k * 0.2, lambda: coin(0.25), 0.4)
    for w_, n_ in (("rich", 314.3), ("free", 315.3)):
        sfx(wt(w_, n_), lambda: ding(1568, 0.35), 0.6)
    sfx(wt("almost", 321.0), lambda: hit(0.8), 1.0)
    sfx(wt("fake", 328.0), shutter, 0.6)
    sfx(wt("fake", 328.0) + 0.4, shutter, 0.6)
    sfx(wt("double", 350.6), lambda: hit(0.7), 0.9)
    sfx(wt("sells", 358.6), lambda: coin(0.4), 0.7)
    sfx(wt("blood", 363.0), lambda: hit(0.6), 0.7)
    sfx(wt("price", 371.2), lambda: pop(500, 0.4), 0.6)
    sfx(wt("no", 384.3), lambda: hit(0.9), 1.1)
    sfx(402.6, lambda: ding(1975, 0.35), 0.7)
    sfx(403.2, lambda: ding(1975, 0.35), 0.7)
    sfx(wt("giorgio", 406.0), lambda: hit(0.6), 0.7)
    sfx(wt("blackmail", 412.4), lambda: hit(0.7), 0.8)
    sfx(wt("hires", 418.3), lambda: hit(0.6), 0.8)
    for w_, n_ in (("cocaine", 419.6), ("war", 420.8), ("helicopter", 423.3), ("sniffer", 424.4)):
        sfx(max(wt(w_, n_) - 0.2, 421.4), shutter, 0.6)
    sfx(wt("blow", 425.4), lambda: boom(0.8), 0.9)
    for d_ in (0.0, 0.3):
        sfx(wt("killed", 430.2) + d_, lambda: hit(0.5), 0.6)
    sfx(wt("betrays", 436.6), lambda: hit(0.8), 0.9)
    sfx(437.9, lambda: metal_slam(0.6), 0.7)
    for k in range(3):
        sfx(449.0 + k * 1.2, lambda: hit(0.7), 0.9)
        sfx(449.0 + k * 1.2, lambda: pop(250, 0.5), 0.6)
    sfx(454.7, lambda: hit(0.7), 0.8)
    sfx(wt("drive", 458.6), chime_sparkle, 0.7)
    sfx(460.6, lambda: siren(4.5, 0.2), 0.8)
    sfx(wt("refuse", 472.6) + 0.1, lambda: hit(0.7), 0.8)
    sfx(wt("water", 489.3), splash, 1.0)
    sfx(wt("water", 489.3) + 0.2, lambda: bubbles(2.5, 0.25), 0.7)
    sfx(wt("escape", 490.4), lambda: ding(1318, 0.35), 0.6)
    sfx(492.3, chime_sparkle, 0.6)
    for k in range(6):
        sfx(507.7 + k * 0.17, lambda: pew(0.3), 0.6, pan=-0.3 if k % 2 else 0.3)
    sfx(wt("fall", 510.9), lambda: hit(0.5), 0.6)
    for w_, n_ in (("freedom", 523.6), ("home", 524.3), ("son", 525.6)):
        sfx(wt(w_, n_) - 0.1, shutter, 0.6)
    sfx(533.3, lambda: hit(0.5), 0.6)
    for k in range(40):
        sfx(wt("hundred", 543.3) + k * 0.06, lambda: click(0.25), 0.5)
    for k in range(10):
        sfx(wt("heart", 553.3) + k * 0.35, lambda: pop(500 + k * 40, 0.35), 0.5)
    for w_, n_ in (("$5", 579.0), ("$15", 580.7), ("$100", 582.3)):
        sfx(wt(w_, n_), lambda: coin(0.4), 0.8)
    for k in range(5):
        sfx(587.5 + k * 0.25, lambda: coin(0.25), 0.5)
    for k in range(3):
        sfx(wt("close", 595.5) + k * 0.3, lambda: metal_slam(0.4), 0.5)
    sfx(wt("spares", 601.5), lambda: ding(1318, 0.35), 0.6)
    sfx(607.6, lambda: coin(0.45), 0.8)
    sfx(613.7, lambda: siren(4.0, 0.15), 0.6)
    sfx(wt("two", 617.6), lambda: hit(0.5), 0.6)
    sfx(wt("talks", 649.3), lambda: coin(0.45), 0.8)
    sfx(wt("cash", 658.3), lambda: coin(0.4), 0.7)
    sfx(wt("opens", 661.6), lambda: metal_slam(0.5), 0.6)
    sfx(wt("happiest", 664.6), chime_sparkle, 0.8)
    for k in range(8):
        sfx(671.5 + k * 0.4, lambda: pew(0.25), 0.5, pan=-0.3 if k % 2 else 0.3)
    sfx(wt("psychopath", 689.8), lambda: hit(0.8), 0.9)
    sfx(wt("kiss", 694.0), kiss_chime, 0.7)
    sfx(wt("shoot", 700.7), lambda: pew(0.5), 0.9)
    sfx(wt("shoot", 700.7), lambda: hit(0.9), 1.0)
    for k in range(4):
        sfx(709.7 + k * 0.25, lambda: pop(500 + k * 100, 0.4), 0.6)
    sfx(wt("ready", 722.3), lambda: pop(700, 0.4), 0.6)
    sfx(wt("yet", 724.4), lambda: pop(500, 0.4), 0.6)
    sfx(wt("drive", 726.8), lambda: car_drive(2.5), 1.0)
    for w_, n_ in (("finish", 728.8), ("chase", 729.9), ("return", 731.0)):
        sfx(wt(w_, n_) + 0.1, lambda: ding(1318, 0.35), 0.6)
    for tm in (735.0, wt("mother", 740.0), wt("robbery", 741.0), wt("prison", 741.7), wt("son", 743.0)):
        sfx(tm - 0.2, shutter, 0.6)
    sfx(756.2, lambda: hit(0.6), 0.7)
    for at_, fn, g, pn in SFX:
        x = fn()
        s.add(x, at_, g, pn)
    return s.stereo(int(dur * SR))


def build_ambience(dur):
    a = Track(dur)
    for s0, s1 in [(147.4, 152.4), (212.4, 240.2), (258.4, 265.0)]:
        cr = crickets(s1 - s0)
        a.add(cr * A.edge_env(len(cr), 0.5), s0, 0.6)
    for s0, s1 in [(143.0, 147.4), (283.3, 290.5)]:
        x = crowd(s1 - s0)
        a.add(x * A.edge_env(len(x), 0.5), s0, 1.0)
    return a.stereo(int(dur * SR))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from common import wt
    from scenes_g6 import SHOTS
    cuts = [s[0] for s in SHOTS]
    voice = load_audio(a.voice)
    dur = len(voice) / SR
    print("music…", flush=True)
    music = build_music(dur)
    print("sfx…", flush=True)
    fx = build_sfx(dur, cuts, wt)
    print("ambience…", flush=True)
    amb = build_ambience(dur)

    def norm(x, peak):
        m = np.max(np.abs(x)) or 1.0
        return x / m * peak

    n = min(len(voice), len(music), len(fx), len(amb))
    voice, music, fx, amb = voice[:n], music[:n], fx[:n], amb[:n]
    music = norm(music, 1.0)
    env = envelope(voice)
    env = env / (np.percentile(env, 95) + 1e-9)
    duck = 1.0 - 0.5 * np.clip(env, 0, 1)
    duck = lp(duck, 6, 1)
    music *= (0.42 * duck)[:, None]
    fx = norm(fx, 0.4)
    amb = norm(amb, 0.18)
    v = voice / (np.max(np.abs(voice)) or 1.0) * 0.92
    mix = np.stack([v, v], axis=1) + music + fx + amb
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    wavfile.write(a.out, SR, (np.clip(mix, -1, 1) * 32767).astype(np.int16))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
