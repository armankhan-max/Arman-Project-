"""Soundtrack: voice + real recorded SFX + real-piano score + ambience, ducked and loudness-normalised.

  * SFX are real recordings (see sfx/: Oculus Audio Pack 01, CC BY 4.0, and CC0 Freesound sale sounds).
    Their cue times come from scenes.py (each S(...) sits next to the visual it belongs to).
  * Music is played on real sampled piano (Meta Piano, CC0, multi-velocity) from a small score below:
    one chord progression per story section, so the music follows the emotion, not the clock.
  * The bed ducks under the narrator and drops out on the two "panic" beats.

Usage: python audio.py --voice voice.mp3 --piano /path/to/meta-piano/ogg --out mix.wav
"""
import argparse
import os
import subprocess

import numpy as np

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))


def load(path, mono=False):
    pcm = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le",
                          "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(pcm, np.float32).reshape(-1, 2).copy()
    return x


def fade(x, fi=0.005, fo=0.25):
    n = len(x)
    a, b = min(n, int(fi * SR)), min(n, int(fo * SR))
    if a:
        x[:a] *= np.linspace(0, 1, a)[:, None]
    if b:
        x[-b:] *= np.linspace(1, 0, b)[:, None]
    return x


def add(buf, x, t, g=1.0):
    i = int(t * SR)
    if i < 0:
        x = x[-i:]
        i = 0
    j = min(len(buf), i + len(x))
    if j > i:
        buf[i:j] += x[:j - i] * g


# ------------------------------------------------------------------ SFX
MAXLEN = {"water": 2.4, "water_short": 1.0, "breath": 2.6, "type": 0.55, "car_fail": 3.2, "rumble_low": 3.2,
          "clock": 2.6, "pressure": 2.0, "counter": 1.8, "scan": 1.0, "applause": 2.6, "steps": 2.4,
          "ac_off": 2.6, "rain": 2.0, "receipt": 1.4}
ALIAS = {"water_short": "water", "fire": "whoosh_s", "heart": "soft", "fly": None, "sigh": None}
BASE = 0.55   # global SFX level under the voice


def sfx_track(n, cues):
    buf = np.zeros((n, 2), np.float32)
    cache = {}
    for t, name, g in cues:
        src = ALIAS.get(name, name)
        if src is None:
            continue
        if name not in cache:
            p = os.path.join(HERE, "sfx", src + ".ogg")
            if not os.path.exists(p):
                print("missing sfx", name)
                cache[name] = None
                continue
            x = load(p)
            ml = MAXLEN.get(name)
            if ml:
                x = fade(x[:int(ml * SR)].copy(), fo=0.35)
            pk = np.abs(x).max() + 1e-9
            cache[name] = x / pk * 0.8
        x = cache[name]
        if x is not None:
            add(buf, x, t, g * BASE)
    return buf


def amb_track(n, ambs):
    buf = np.zeros((n, 2), np.float32)
    for t0, t1, name, g in ambs:
        x = load(os.path.join(HERE, "sfx", f"amb_{name}.ogg"))
        x = x / (np.abs(x).max() + 1e-9)
        L = int((t1 - t0 + 0.6) * SR)
        reps = int(np.ceil(L / len(x)))
        y = np.tile(x, (reps, 1))[:L].copy()
        add(buf, fade(y, 0.3, 0.4), t0 - 0.1, g * 0.35)
    return buf


# ------------------------------------------------------------------ real-piano score
NOTE = {"C": 0, "Cs": 1, "D": 2, "Ds": 3, "E": 4, "F": 5, "Fs": 6, "G": 7, "Gs": 8, "A": 9, "As": 10, "B": 11}
INV = {v: k for k, v in NOTE.items()}


class Piano:
    def __init__(self, folder):
        self.folder = folder
        self.cache = {}

    def note(self, midi, vel=2, dur=3.0):
        key = (midi, vel)
        if key not in self.cache:
            octv = midi // 12 - 1
            name = f"INSPiano_Vel{vel:02d}_{INV[midi % 12]}{octv}_01.ogg"
            x = load(os.path.join(self.folder, name))
            self.cache[key] = x / (np.abs(x).max() + 1e-9)
        x = self.cache[key][:int(dur * SR)].copy()
        return fade(x, 0.002, min(0.8, dur * 0.4))


def m(name):
    """'C4' / 'Fs3' -> midi"""
    o = int(name[-1])
    return 12 * (o + 1) + NOTE[name[:-1]]


# chord = (bass, [upper notes]); one bar each
SECTIONS = [
    # t0, t1, bpm, chords, pattern, vel, gain
    (0.0, 13.3, 76, [("A2", ["A3", "C4", "E4"]), ("F2", ["F3", "A3", "C4"]), ("C3", ["G3", "C4", "E4"]),
                     ("G2", ["G3", "B3", "D4"])], "arp", 2, 0.9),
    (14.9, 25.5, 76, [("A2", ["A3", "C4", "E4"]), ("F2", ["A3", "C4", "F4"]), ("D3", ["A3", "D4", "F4"]),
                      ("E2", ["Gs3", "B3", "E4"])], "pulse", 2, 0.85),
    (25.5, 98.7, 92, [("C3", ["E4", "G4", "C5"]), ("A2", ["E4", "A4", "C5"]), ("F2", ["F4", "A4", "C5"]),
                      ("G2", ["D4", "G4", "B4"])], "arp8", 1, 0.75),
    (98.7, 165.4, 92, [("F2", ["F4", "A4", "C5"]), ("G2", ["D4", "G4", "B4"]), ("E2", ["E4", "G4", "B4"]),
                       ("A2", ["E4", "A4", "C5"])], "arp8", 1, 0.75),
    (165.4, 208.9, 96, [("C3", ["E4", "G4", "C5"]), ("G2", ["D4", "G4", "B4"]), ("A2", ["E4", "A4", "C5"]),
                        ("F2", ["F4", "A4", "C5"])], "arp8", 1, 0.75),
    (208.9, 231.7, 84, [("D2", ["D4", "F4", "A4"]), ("As1", ["D4", "F4", "As4"]), ("F2", ["C4", "F4", "A4"]),
                        ("A1", ["Cs4", "E4", "A4"])], "pulse", 2, 0.9),
    (231.7, 294.9, 100, [("F2", ["F4", "A4", "C5"]), ("C3", ["E4", "G4", "C5"]), ("G2", ["D4", "G4", "B4"]),
                         ("A2", ["E4", "A4", "C5"])], "arp8", 2, 0.75),
    (294.9, 317.1, 80, [("A2", ["A3", "C4", "E4"]), ("F2", ["A3", "C4", "F4"]), ("C3", ["G3", "C4", "E4"]),
                        ("E2", ["Gs3", "B3", "E4"])], "pulse", 2, 0.85),
    (317.1, 361.8, 88, [("C3", ["E4", "G4", "C5"]), ("G2", ["D4", "G4", "B4"]), ("A2", ["E4", "A4", "C5"]),
                        ("F2", ["F4", "A4", "C5"])], "arp", 2, 0.8),
    (361.8, 373.1, 76, [("A2", ["A3", "C4", "E4"]), ("F2", ["A3", "C4", "F4"]), ("D3", ["A3", "D4", "F4"]),
                        ("E2", ["Gs3", "B3", "E4"])], "arp", 2, 0.85),
]


def music_track(n, piano):
    buf = np.zeros((n, 2), np.float32)
    for t0, t1, bpm, chords, pat, vel, gain in SECTIONS:
        beat = 60.0 / bpm
        bar = beat * 4
        t = t0
        i = 0
        while t < t1 - 0.5:
            bass, up = chords[i % len(chords)]
            add(buf, piano.note(m(bass), vel, bar * 1.2), t, 0.55 * gain)
            if pat == "arp":
                seq = [up[0], up[1], up[2], up[1]]
                for k, nn in enumerate(seq):
                    add(buf, piano.note(m(nn), vel, beat * 2.2), t + k * beat, 0.32 * gain)
            elif pat == "arp8":
                seq = [up[0], up[1], up[2], up[1], up[0], up[2], up[1], up[2]]
                for k, nn in enumerate(seq):
                    add(buf, piano.note(m(nn), vel, beat * 1.4), t + k * beat / 2, 0.24 * gain)
            else:  # pulse: repeated chord on every beat, a little tension
                for k in range(4):
                    for nn in up:
                        add(buf, piano.note(m(nn), vel, beat * 0.9), t + k * beat, 0.16 * gain)
            t += bar
            i += 1
        # section tail fade
    # silence beats: the heater panic and the burst pipe
    env = np.ones(n, np.float32)
    for a, b in ((13.3, 14.9), (112.85, 114.0)):
        ia, ib = int(a * SR), int(b * SR)
        env[ia:ib] = 0.0
        r = int(0.12 * SR)
        env[max(0, ia - r):ia] = np.minimum(env[max(0, ia - r):ia], np.linspace(1, 0, ia - max(0, ia - r)))
        env[ib:ib + int(0.6 * SR)] = np.linspace(0, 1, len(env[ib:ib + int(0.6 * SR)]))
    tail = int(1.5 * SR)
    env[-tail:] *= np.linspace(1, 0, tail)
    return buf * env[:, None]


def duck_env(voice):
    mono = np.abs(voice).mean(axis=1)
    win = int(0.05 * SR)
    k = np.ones(win) / win
    rms = np.sqrt(np.convolve(mono ** 2, k, mode="same"))
    act = (rms > 0.02).astype(np.float32)
    # smooth attack/release (~150 ms / 500 ms) by simple one-pole on decimated signal
    dec = act[::480]
    out = np.zeros_like(dec)
    v = 0.0
    for i, a in enumerate(dec):
        c = 0.25 if a > v else 0.04
        v += (a - v) * c
        out[i] = v
    env = np.repeat(out, 480)[:len(act)]
    if len(env) < len(act):
        env = np.pad(env, (0, len(act) - len(env)), mode="edge")
    return 1.0 - 0.5 * env   # -6 dB under speech


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--piano", required=True)
    ap.add_argument("--out", default="mix.wav")
    ap.add_argument("--stems", default=None)
    a = ap.parse_args()
    import scenes
    cues = scenes.build_cues()
    print(len(cues), "sfx cues")
    voice = load(a.voice)
    n = len(voice) + SR
    voice = np.pad(voice, ((0, n - len(voice)), (0, 0)))
    sfx = sfx_track(n, cues)
    amb = amb_track(n, scenes.AMB)
    mus = music_track(n, Piano(a.piano))
    mus = mus / (np.abs(mus).max() + 1e-9) * 0.13
    d = duck_env(voice)[:, None]
    mix = voice * 1.0 + mus * d + amb * d + sfx * (0.55 + 0.45 * d)
    mix = np.tanh(mix * 0.95) / 0.95
    if a.stems:
        os.makedirs(a.stems, exist_ok=True)
        for nm, x in (("music", mus), ("sfx", sfx), ("amb", amb)):
            write(os.path.join(a.stems, nm + ".wav"), x)
    write(a.out, mix)
    print("wrote", a.out)


def write(path, x):
    pcm = np.clip(x, -1, 1).astype(np.float32).tobytes()
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_s16le", path], input=pcm, check=True)


if __name__ == "__main__":
    main()
