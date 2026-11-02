"""Soundtrack for 'Your Phone Is Dirtier Than A Toilet Seat'.

Voice (-14 LUFS, on top) + original synthesized music loop (-30 LUFS, ducked another 6 dB under the voice)
+ every SFX from assets/cues.json (cues come from the same word anchors as the animation) + room tone.
If ./sfx/<name>.wav exists it is used instead of the synthesized version.

Usage: python3 audio_mix.py  -> out/mix_48k.wav
"""
import json, os, subprocess, sys
import numpy as np
import pyloudnorm as pyln
from scipy import signal
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'video'))
from audio import (SR, Track, tt, lp, hp, bp, noise, midi, nm, pad, pluck, bell_tone, bass, kick, hat, heartbeat,  # noqa
                   whoosh, pop, click, ding, chime_sparkle, tick, hit, riser, squish, marimba, env_adsr, edge_env, load_audio)

rng = np.random.default_rng(42)
cues = json.load(open(os.path.join(HERE, 'assets/cues.json')))
FPS, TOTAL = cues['fps'], cues['total']
DUR = TOTAL / FPS


# ------------------------------------------------------------------ SFX library (synthesized)
def norm(x):
    m = np.max(np.abs(x)) or 1.0
    return x / m

def boing(d=0.55):
    t = tt(d); f = 260 + 200 * np.sin(2 * np.pi * 11 * t) * np.exp(-t * 5) + 120 * t
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)

def squeaky_jump():
    d = 0.14; t = tt(d); f = 700 + 1100 * (t / d) ** 0.7
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 0.5

def snap_tick():
    x = np.zeros(int(0.25 * SR)); a = tick(1.0); x[:len(a)] += a
    c = click(1.0); x[:len(c)] += c * 0.8
    w = whoosh(0.18, True, 0.5); x[:len(w)] += w * 0.6
    return x

def danger_sting():
    d = 0.7; t = tt(d)
    x = signal.sawtooth(2 * np.pi * 110 * t) + signal.sawtooth(2 * np.pi * 116.5 * t) + 0.5 * signal.sawtooth(2 * np.pi * 220 * t)
    return lp(x, 1400) * env_adsr(len(t), 0.005, 0.1, 0.6, 0.35)

def stink():
    d = 0.8; t = tt(d); f = 260 * 2 ** (-t / d) * (1 + 0.04 * np.sin(2 * np.pi * 7 * t))
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
    return lp(x, 900) * env_adsr(len(t), 0.03, 0.1, 0.8, 0.3)

def tap():
    d = 0.12; t = tt(d)
    return bp(noise(d), 1500, 6000) * np.exp(-t * 90) * 0.7 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 40)

def porcelain_clack():
    d = 0.09; t = tt(d)
    return bp(noise(d), 1200, 5000) * np.exp(-t * 60) + 0.6 * np.sin(2 * np.pi * 900 * t) * np.exp(-t * 50)

def lid_rattle():
    out = np.zeros(int(0.5 * SR))
    for i, at in enumerate((0, 0.07, 0.13, 0.2)):
        c = porcelain_clack() * (1 - i * 0.2); j = int(at * SR); out[j:j + len(c)] += c
    return out

def spray_hiss():
    d = 0.5; t = tt(d)
    return bp(noise(d), 2500, 11000) * env_adsr(len(t), 0.01, 0.05, 0.85, 0.15)

def clack():
    x = np.zeros(int(0.2 * SR)); k = lp(kick(0.15, 160, 80), 900); x[:len(k)] += k * 0.8
    c = porcelain_clack(); x[:len(c)] += c * 0.6
    return x

def laugh_boing():
    out = np.zeros(int(0.9 * SR))
    for i in range(5):
        d = 0.11; t = tt(d); f0 = 520 - i * 40
        f = f0 * (1 + 0.25 * np.exp(-t * 30))
        v = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * signal.sawtooth(2 * np.pi * np.cumsum(f * 2) / SR)
        v = bp(v, 300, 3000) * np.sin(np.pi * t / d)
        j = int(i * 0.15 * SR); out[j:j + len(v)] += v
    return out

def step():
    d = 0.1; t = tt(d)
    return lp(noise(d), 500) * np.exp(-t * 45) * 2 + np.sin(2 * np.pi * 80 * t) * np.exp(-t * 50) * 0.5

def warm_swell():
    d = 1.6; t = tt(d)
    x = pad([midi(62), midi(66), midi(69)], d, 0.8, 0.6, 0.3) if True else 0
    x = x[:len(t)]
    return x * np.sin(np.pi * t / d) + 0.3 * bp(noise(d), 300, 1200) * np.sin(np.pi * t / d)

def flush():
    d = 2.4; t = tt(d)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * (2 + 3 * t) * t)
    x = bp(noise(d), 180, 2200) * (0.6 + 0.4 * lfo) + 0.6 * lp(noise(d), 300)
    env = np.clip(t / 0.15, 0, 1) * np.exp(-np.clip(t - 0.9, 0, None) * 1.6)
    g = np.zeros_like(t)
    for _ in range(40):
        at = rng.uniform(0.1, 2.0); bd = rng.uniform(0.03, 0.08); bt = tt(bd); f = rng.uniform(180, 500) * (1 + 2 * bt / bd)
        b = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * bt / bd); j = int(at * SR); g[j:j + len(b)] += b[:len(g) - j] * 0.35
    return x * env + g * env

def bubbly_whoosh():
    d = 1.8; x = whoosh(d, True, 0.8)[:int(d * SR)]
    for _ in range(45):
        at = rng.uniform(0, d - 0.1); bd = rng.uniform(0.04, 0.09); bt = tt(bd); f = rng.uniform(500, 1400) * (1 + 1.5 * bt / bd)
        b = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * bt / bd); j = int(at * SR); x[j:j + len(b)] += b[:len(x) - j] * 0.25
    return x

def patter():
    out = np.zeros(int(0.7 * SR))
    for _ in range(26):
        c = bp(noise(0.02), 2000, 8000) * np.exp(-tt(0.02) * 160) * rng.uniform(0.3, 1); j = int(rng.uniform(0, 0.6) * SR); out[j:j + len(c)] += c
    return out

def heartbeat_soft():
    return lp(heartbeat(1.0), 140)

def music_hit():
    d = 1.6; t = tt(d); x = kick(d, 100, 38) * 1.2
    x += hp(noise(d), 4000) * np.exp(-t * 3.5) * 0.35
    for m in (50, 57, 62, 65):
        x += signal.sawtooth(2 * np.pi * midi(m) * t) * np.exp(-t * 4) * 0.12
    return lp(x, 6000)

def wipe_swish():
    d = 0.4; t = tt(d)
    x = whoosh(d, True, 1.0)[:len(t)] + 0.25 * np.sin(2 * np.pi * np.cumsum(900 + 1600 * t / d) / SR) * np.sin(np.pi * t / d)
    return x

LIB = {
    'whoosh_whip': lambda: whoosh(0.36, True, 1.0), 'whoosh_reveal': lambda: whoosh(0.9, False, 1.0),
    'whoosh_soft': lambda: whoosh(0.5, True, 0.6), 'pop': lambda: pop(rng.uniform(480, 900), 1.0), 'snap_tick': snap_tick,
    'danger_sting': danger_sting, 'stink': stink, 'tap': tap, 'lid_rattle': lid_rattle, 'spray_hiss': spray_hiss,
    'sparkle_chime': lambda: chime_sparkle(1.0), 'clack': clack, 'laugh_boing': laugh_boing, 'step': step, 'boing': boing,
    'squeaky_jump': squeaky_jump, 'warm_swell': warm_swell, 'click': lambda: click(1.0), 'flush': flush,
    'bubbly_whoosh': bubbly_whoosh, 'patter': patter, 'heartbeat_soft': heartbeat_soft, 'riser': lambda: riser(1.4, 1.0),
    'squish': lambda: squish(1.0), 'impact': lambda: hit(1.0), 'music_hit': music_hit, 'wipe_swish': wipe_swish,
    'ding': lambda: ding(1318.5, 1.0),
}

def get_sfx(name):
    user = os.path.join(HERE, 'sfx', name + '.wav')
    if os.path.exists(user):
        return load_audio(user)
    return LIB[name]()


# ------------------------------------------------------------------ music: light curious / suspense loop (D minor, 100 bpm)
def build_music():
    tr = Track(DUR)
    bpm = 100; beat = 60 / bpm; bar = beat * 4
    prog = [('D3', [62, 65, 69]), ('A#2', [58, 62, 65]), ('G2', [55, 58, 62]), ('A2', [57, 61, 64])]
    motif = [0, 2, 1, 2, 0, 2, 1, None]
    t, i = 0.0, 0
    esc0 = cues['scenes'][4]['from'] / FPS  # escalation from S5
    esc1 = cues['scenes'][7]['from'] / FPS
    while t < DUR + bar:
        root, notes = prog[i % 4]
        esc = esc0 <= t < esc1
        for k, idx in enumerate(motif):
            nt = t + k * beat / 2
            if idx is not None:
                tr.add(marimba(midi(notes[idx] + 12)), nt, 0.32, pan=-0.25 if k % 2 else 0.25)
        tr.add(pad([midi(n) for n in notes], bar + 0.8, 0.5, 0.8, 0.25), t, 0.22)
        for k in range(4):
            bt = t + k * beat
            tr.add(bass(midi(nm(root) - 12 + 12), beat * 0.6), bt, 0.28 if k % 2 == 0 else 0.16)
            tr.add(hat(0.05, 1.0), bt + beat / 2, 0.10, pan=0.4)
            if esc:  # suspense: pulsing low strings + extra ticks
                tr.add(pluck(midi(nm(root)), beat * 0.9, 0.5, 4.0), bt, 0.22, pan=-0.3)
                tr.add(tick(1.0), bt + beat / 4, 0.12, pan=-0.4)
        t += bar; i += 1
    st = tr.stereo(int(DUR * SR))
    # gentle fade-in so frame 0 is not silent but not abrupt; no fade at the end (loop)
    st[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))[:, None]
    return st


def lufs(x):
    meter = pyln.Meter(SR)
    return meter.integrated_loudness(x if x.ndim == 1 else x)

def gain_to(x, target):
    return x * 10 ** ((target - lufs(x)) / 20)


def main():
    n = int(DUR * SR)
    voice = load_audio(os.path.join(HERE, 'assets/voiceover.mp3'))
    voice = np.pad(voice, (0, max(0, n - len(voice))))[:n]
    voice = gain_to(np.stack([voice, voice], axis=1), -14.0)[:, 0]  # -14 LUFS as played (dual-mono)
    vpk = np.max(np.abs(voice))
    va = np.abs(voice); v_rms = np.sqrt(np.mean(voice[va > 0.1 * va.max()] ** 2))
    # voice activity envelope -> ducking (extra -6 dB while speaking)
    env = np.sqrt(lp(voice ** 2, 8, 1).clip(0))
    act = (env > 0.02).astype(float)
    pass
    act = np.convolve(act, np.ones(int(0.15 * SR)) / int(0.15 * SR), mode='same').clip(0, 1)
    duck = 10 ** (-6 * act / 20)
    music = gain_to(build_music(), -30.0) * duck[:, None]
    # SFX
    sfx = Track(DUR)
    for c in cues['cues']:
        x = get_sfx(c['sfx'])
        # loudness-match each SFX to the voice (RMS over its loud part), then 50-70% of it
        a = np.abs(x); loud = x[a > 0.1 * a.max()]
        x = x / (np.sqrt(np.mean(loud ** 2)) + 1e-9) * v_rms
        level = 0.6 * c.get('gain', 1.0)
        if c['sfx'] == 'heartbeat_soft':
            level = 0.3 * c.get('gain', 1.0)
        if c['sfx'] == 'step':
            level = 0.22
        x = x * level
        pk = np.max(np.abs(x))
        if pk > 0.85 * vpk:
            x *= 0.85 * vpk / pk
        sfx.add(x, c['f'] / FPS, 1.0, pan=c.get('pan', 0.0))
    sfx_st = sfx.stereo(n)
    sfx_l = lufs(sfx_st)
    sfx_st = sfx_st * 10 ** ((-18.5 - sfx_l) / 20)  # SFX stem sits well under the -14 LUFS voice
    # room tone so there is never digital silence
    room = lp(rng.standard_normal(n), 400) * 0.0025
    mix = music + sfx_st + np.stack([voice + room, voice + room * 0.9], axis=1)
    # soft limiter at -1 dBFS
    lim = 10 ** (-1 / 20)
    mix = np.tanh(mix / lim) * lim
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    tmp = os.path.join(HERE, 'out/mix_44k.wav')
    wavfile.write(tmp, SR, (mix * 32767).astype(np.int16))
    out = os.path.join(HERE, 'out/mix_48k.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-ar', '48000', out], check=True)
    os.remove(tmp)
    print('voice LUFS %.1f | music -30 (pre-duck) | sfx stem %.1f -> -18.5 | mix LUFS %.1f | sfx cues %d' % (lufs(np.stack([voice, voice], axis=1)), sfx_l, lufs(mix), len(cues['cues'])))

if __name__ == '__main__':
    main()
