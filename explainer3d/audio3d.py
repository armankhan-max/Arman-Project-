"""Soundtrack for '5,000 Steps': original synthesized music cues + timed SFX, ducked under the voice, -14 LUFS.
Usage: python audio3d.py --voice voice.mp3 --out mix.wav
"""
import argparse, os, re, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from audio import (SR, Track, tt, lp, hp, noise, midi, nm, pad, pluck, bell_tone, bass, kick, hat, heartbeat, whoosh, pop,
                   click, ding, chime_sparkle, hit, riser, tick, drop_plink, fz, CHORDS, cue_curious, cue_night, cue_warm,
                   cue_tension, cue_hope, cue_roadtrip, final_chord, fade_region, load_audio, envelope, edge_env, squish, gulp)

DUR = 251.0
def shots():
    src = open(os.path.join(HERE, "web/js/timeline.js")).read()
    out = []
    for m in re.finditer(r"^sh\(([\d.]+), ([\d.]+), '(\w+)'.*?^\}(?:, \{([^}]*)\})?\);", src, re.S | re.M):
        a, b, s, o = float(m.group(1)), float(m.group(2)), m.group(3), m.group(4) or ""
        tin = re.search(r"tin: '(\w+)'", o); tout = re.search(r"tout: '(\w+)'", o)
        out.append((a, b, s, tin.group(1) if tin else None, tout.group(1) if tout else None))
    return out

def footstep(gain=0.35):
    t = tt(0.12); x = lp(noise(0.12), 900) * np.exp(-t * 45) + 0.6 * lp(kick(0.12, 120, 60), 400)
    return x * gain
def thud(gain=0.8):
    k = lp(kick(0.6, 90, 30), 260); nn = lp(noise(0.6), 300) * np.exp(-tt(0.6) * 9); m = min(len(k), len(nn)); return (k[:m] + .6 * nn[:m]) * gain
def shimmer(dur=2.0, gain=0.3):
    out = np.zeros(int((dur + 2.5) * SR))
    for k in range(14):
        f = midi(84 + [0, 4, 7, 11, 12, 16, 19][k % 7]); s = bell_tone(f, 1.8); i = int(k * dur / 14 * SR)
        out[i:i + len(s)] += s * (0.6 + 0.4 * np.sin(k))
    return out * gain
def bubble(gain=0.25):
    t = tt(0.15); f = 300 + 900 * t / 0.15
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 25) * gain

def build_music():
    m = Track(DUR)
    cue_hope(m, 0.0, 10.3, build=0.35)
    cue_night(m, 10.3, 21.0)
    m.add(riser(2.2, 0.35), 21.2, 1.0)
    cue_roadtrip(m, 23.4, 47.0, bpm=112, gain=0.85)
    cue_warm(m, 47.0, 75.5)
    m.add(riser(1.6, 0.35), 75.5, 1.0)
    cue_curious(m, 77.1, 108.3, bpm=96)
    cue_night(m, 108.3, 131.0)
    cue_warm(m, 131.0, 141.0, bpm=90)
    cue_curious(m, 141.0, 157.7, bpm=104)
    cue_tension(m, 157.7, 168.4, bpm=84, gain=0.6)
    cue_hope(m, 168.4, 186.2, build=0.3)
    cue_tension(m, 186.2, 209.7, bpm=100, gain=0.8)
    cue_night(m, 209.7, 221.3)
    cue_hope(m, 221.3, 245.2, build=0.4)
    m.add(pad(fz(["D3", "A3", "D4", "F#4"]), 3.5, 1.0, 2.0, 0.3), 245.2, 0.4)
    final_chord(m, 248.3, ["D3", "F#3", "A3", "D4"], 0.55, 3.0)
    x = m.stereo(int(DUR * SR))
    x = fade_region(x, 247.4, 248.25, 0.25)   # silence on "first step?"
    x = fade_region(x, 22.6, 23.35, 0.2)      # breath before the city wakes
    return x

def build_sfx():
    s = Track(DUR)
    for a, b, set_, tin, tout in shots():
        if tin in ("whip",): s.add(whoosh(0.45, True, 0.5), a - 0.2, 1.0, pan=0.3)
        if tin == "zoom": s.add(whoosh(0.6, True, 0.6), a - 0.3, 1.0)
        if tin == "flash": s.add(hit(0.5), a, 0.8)
        if tin == "dip": s.add(whoosh(0.8, False, 0.2), a - 0.4, 1.0)
        if set_ == "heart":
            x = a + 0.1
            while x < b: s.add(heartbeat(), x, 0.45); x += 0.8 if a > 49 else 1.3
        if set_ == "town" and not (61 < a < 62.5 or 136 < a < 138.1 or 231 < a < 233.6 or 5 < a < 10.3):
            x = a + 0.1; step = 0.48 if not (157 < a < 160.5 or 180 < a < 182.6) else 1.4
            k = 0
            while x < b: s.add(footstep(0.3), x, 1.0, pan=0.15 if k % 2 else -0.15); x += step; k += 1
        if set_ == "vessel":
            n = noise(b - a + .5); s.add(lp(n, 250) * edge_env(len(n), .3) * 0.5, a, 1.0)
    # title slams
    for i, t in enumerate([0.02, 0.14, 0.26, 0.38, 0.5]): s.add(thud(0.9), t, 1.0, pan=(i - 2) * .15)
    s.add(whoosh(0.5, True, 0.4), 0.85, 1.0); s.add(chime_sparkle(0.35), 3.0, 1.0)
    for t in [3.3, 3.7, 4.1, 4.5]: s.add(ding(1318.5, 0.18), t, 1.0)
    s.add(tick(0.4), 5.85, 1.0)
    s.add(gulp(0.2), 11.6, 1.0)                       # yawn-ish
    s.add(thud(0.6), 23.2, 1.0); s.add(shimmer(2.0, 0.35), 23.45, 1.0)
    for t in [28.9, 30.4]: s.add(squish(0.35), t, 1.0)
    for t in [40.75, 41.7, 42.75, 43.55]: s.add(squish(0.45), t, 1.0); s.add(whoosh(0.35, True, 0.3), t + .05, 1.0)
    s.add(pop(700, 0.35), 45.95, 1.0)
    s.add(ding(1567.98, 0.25), 47.9, 1.0)
    s.add(chime_sparkle(0.3), 63.4, 1.0)
    s.add(hit(0.4), 65.0, 1.0)
    s.add(riser(1.5, 0.3), 75.6, 1.0)
    s.add(chime_sparkle(0.3), 85.5, 1.0); s.add(whoosh(1.2, False, 0.25), 88.1, 1.0)
    for t in np.arange(90.4, 93.4, 0.27): s.add(drop_plink(0.12), t, 1.0, pan=np.sin(t * 3) * .5)
    s.add(chime_sparkle(0.25), 95.3, 1.0); s.add(pop(900, 0.45), 98.4, 1.0); s.add(ding(2093, 0.3), 98.45, 1.0)
    s.add(chime_sparkle(0.25), 102.8, 1.0)
    for i in range(10): s.add(click(0.18), 117.9 + i * .25, 1.0, pan=(i % 3 - 1) * .4)
    for i in range(10): s.add(pop(1000 + i * 40, 0.12), 121.4 + i * .03, 1.0)
    for i in range(8): s.add(pop(500, 0.1), 122.25 + i * .04, 1.0)
    s.add(ding(1046.5, 0.25), 124.7, 1.0); s.add(ding(1174.7, 0.25), 128.6, 1.0)
    s.add(chime_sparkle(0.3), 134.4, 1.0)
    for t in np.arange(144.0, 147.4, 0.526): s.add(squish(0.2), t, 1.0)
    for i in range(12): s.add(bubble(0.2), 152.3 + i * .12, 1.0, pan=np.sin(i) * .5)
    s.add(chime_sparkle(0.3), 154.9, 1.0)
    for t in [169.0, 170.8, 171.7, 172.6, 173.5]: s.add(squish(0.35), t, 1.0)
    s.add(chime_sparkle(0.3), 176.6, 1.0); s.add(thud(0.5), 181.2, 1.0)
    for t in [182.7, 183.6, 184.5, 185.4]: s.add(thud(0.35), t, 1.0)
    s.add(riser(2.5, 0.2), 186.5, 1.0)
    for i, t in enumerate(np.linspace(199.9, 201.7, 18)): s.add(tick(0.25), t, 1.0)
    s.add(ding(1318.5, 0.35), 201.7, 1.0)
    for i in range(30): s.add(click(0.2), 205.0 + i * 4.4 / 30, 1.0, pan=np.sin(i) * .3)
    s.add(whoosh(1.5, True, 0.25), 211.4, 1.0); s.add(chime_sparkle(0.25), 215.6, 1.0)
    for t in np.arange(223.6, 224.9, 0.13): s.add(tick(0.2), t, 1.0)
    s.add(pop(800, 0.35), 224.4, 1.0)
    for t in [228.65, 228.85, 229.85, 230.95]: s.add(pop(400, 0.4), t, 1.0); s.add(whoosh(0.3, False, 0.2), t, 1.0)
    s.add(chime_sparkle(0.35), 240.1, 1.0)
    s.add(whoosh(1.0, True, 0.2), 245.4, 1.0)
    s.add(hit(0.5), 248.3, 1.0)
    return s.stereo(int(DUR * SR))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--voice", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
    v = load_audio(a.voice); n = int(DUR * SR); voice = np.zeros(n); voice[:min(n, len(v))] = v[:n]
    music = build_music(); fx = build_sfx()
    norm = lambda x, p: x / (np.max(np.abs(x)) or 1) * p
    music = norm(music, 1.0)
    env = envelope(voice); env = env / (np.percentile(env, 95) + 1e-9)
    duck = lp(1.0 - 0.6 * np.clip(env, 0, 1), 6, 1)
    music *= (0.28 * duck)[:, None]
    fx = norm(fx, 0.5)
    vv = voice / (np.max(np.abs(voice)) or 1) * 0.92
    mix = np.stack([vv, vv], 1) + music + fx
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    from scipy.io import wavfile
    wavfile.write(a.out, SR, (mix * 32767).astype(np.int16)); print("wrote", a.out)

if __name__ == "__main__":
    main()
