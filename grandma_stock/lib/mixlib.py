"""Audio mix for the grandma stock-footage style.

Voice: slowed by SPD (pitch kept), light room reverb, gentle compression, -16 LUFS.
Music: Mixkit tracks back to back, ducked under the voice.
SFX: cinematic hook at 0s, soft whoosh on every cut, text-driven pops/hits/dings.
Ambience: wind / fire beds where the project lists them.
Levels below are the user-approved ones (v2: SFX already turned down).
"""
import json, os, subprocess
import numpy as np

SR = 48000
VOICE_FX = ("atempo={spd},highpass=f=70,aecho=0.8:0.7:45|90|140:0.14|0.09|0.05,"
            "acompressor=threshold=-20dB:ratio=2.5:attack=10:release=150:makeup=2,loudnorm=I=-16:TP=-1.5:LRA=9")
SFX_LIB = {
    "pop": "2358", "swoosh": "1485", "whoosh": "1491", "hit": "490", "ding": "3116",
    "tick": "1133", "alert": "490", "click": "1109", "bell": "933", "whoosh2": "1489",
    "impact": "2908", "thunder": "2390",
}


def db(x): return 10 ** (x / 20)


def load(path, start=None, dur=None):
    cmd = ["ffmpeg", "-v", "error"]
    if start is not None: cmd += ["-ss", str(start)]
    if dur is not None: cmd += ["-t", str(dur)]
    cmd += ["-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.check_output(cmd), dtype=np.float32).reshape(-1, 2).copy()


def movavg(x, w):
    c = np.cumsum(np.concatenate([[0.0], x]))
    y = (c[w:] - c[:-w]) / w
    pad = len(x) - len(y)
    return np.pad(y, (pad // 2, pad - pad // 2), mode="edge")


def mix(p, work, kit):
    spd, total = p.SPD, p.TOTAL
    N = int(total * SR) + SR
    out = np.zeros((N, 2), np.float32)

    # voice
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p.VO, "-af", VOICE_FX.format(spd=spd),
                    "-ar", str(SR), "-ac", "2", f"{work}/vo_proc.wav"], check=True)
    vo = load(f"{work}/vo_proc.wav")[:N]
    out[:len(vo)] += vo

    # duck curve from voice activity
    active = (movavg(np.abs(vo).mean(1), int(0.05 * SR)) > 0.01).astype(np.float32)
    duck = np.clip(movavg(active, int(0.4 * SR)), 0, 1)
    duck = np.pad(duck, (0, max(0, N - len(duck))))[:N]

    # music
    tracks = [load(f"{work}/music/{m}.mp3") for m in p.MUSIC]
    xf = 4 * SR; fade = np.linspace(0, 1, xf)[:, None]
    mus = tracks[0]
    for tr in tracks[1:]:
        mus = np.concatenate([mus[:-xf], mus[-xf:] * (1 - fade) + tr[:xf] * fade, tr[xf:]])
    while len(mus) < N:
        mus = np.concatenate([mus, mus])
    mus = mus[:N] / (np.sqrt((mus[:N] ** 2).mean()) + 1e-9) * db(-21)
    mus *= (db(-9) * (1 - duck) + db(-17) * duck)[:, None].astype(np.float32)
    t = np.arange(N) / SR
    env = np.clip((t - 1.0) / 2.5, 0.15, 1) * np.clip((total - t) / 3.0, 0, 1)
    out += mus * env[:, None].astype(np.float32)

    cache = {}

    def sfx(name, t0, gdb, dur=None):
        key = (name, dur)
        if key not in cache:
            a = load(f"{kit}/sfx/{SFX_LIB[name]}.mp3", dur=dur)
            a = a / (np.abs(a).max() + 1e-9) * 0.9
            if dur:
                f = min(len(a), int(0.5 * SR)); a[-f:] *= np.linspace(1, 0, f)[:, None]
            cache[key] = a
        a = cache[key] * db(gdb)
        i = int(t0 * SR); j = min(N, i + len(a))
        if i < N:
            out[i:j] += a[:j - i]

    # hook (attention grabber) + first-cut hit
    sfx("impact", 0.0, -11)
    sfx("thunder", 0.0, -15, dur=4.0)
    sfx("hit", p.SHOTS_S[1][0], -15)
    # soft whoosh on every cut, louder on flash cuts
    for st, _, _ in p.SHOTS_S[1:]:
        flash = st in p.FLASH_S
        sfx("whoosh" if flash else "whoosh2", max(0, st - 0.35), -21 if flash else -29)
    # text-driven sfx (already time-scaled + trimmed by vtext.save)
    for t0, name, g in json.load(open(f"{work}/sfx_text.json")):
        sfx(name, t0, g)

    # ambience
    for sid, t0, t1, gdb, off in p.AMBIENCE:
        t0, t1, gdb = t0 / spd, t1 / spd, gdb - 4
        a = load(f"{kit}/sfx/{sid}.mp3", start=off, dur=t1 - t0 + 0.1)
        a = a / (np.sqrt((a ** 2).mean()) + 1e-9) * db(gdb)
        a *= min(1.0, 0.12 / (np.abs(a).max() + 1e-9))      # cap crackle transients
        n = len(a); f = min(n // 3, int(1.0 * SR))
        e = np.ones(n, np.float32); e[:f] = np.linspace(0, 1, f); e[-f:] = np.linspace(1, 0, f)
        i = int(t0 * SR); j = min(N, i + n)
        out[i:j] += (a * e[:, None])[:j - i]

    out = out[:int(total * SR)]
    pcm = f"{work}/mix.pcm"
    (out.clip(-1, 1) * 32767).astype("<i2").tofile(pcm)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", pcm,
                    "-af", "alimiter=limit=0.95", f"{work}/mix.wav"], check=True)
    os.remove(pcm)
    print("mix ok, peak", float(np.abs(out).max()))
