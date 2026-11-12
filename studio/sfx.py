"""Sound design generated in code (no licensing needed): whooshes, risers, cinematic hits,
soft pops for text, and a low ambient bed. Placed on the timeline by the pipeline."""
import numpy as np

SR = 48000
_rng = np.random.default_rng(11)


def _band_noise(n, f_lo, f_hi, width=0.35, block=2048):
    """Noise whose band centre sweeps from f_lo to f_hi (overlap-add FFT filtering)."""
    hop = block // 2
    win = np.hanning(block).astype(np.float32)
    out = np.zeros(n + block, dtype=np.float32)
    freqs = np.fft.rfftfreq(block, 1 / SR)
    for a in range(0, n, hop):
        p = a / max(1, n)
        fc = f_lo * (f_hi / f_lo) ** p
        spec = np.fft.rfft(_rng.standard_normal(block).astype(np.float32) * win)
        g = np.exp(-0.5 * (np.log(np.maximum(freqs, 1) / fc) / width) ** 2)
        out[a:a + block] += np.fft.irfft(spec * g, block).astype(np.float32) * win
    out = out[:n]
    return out / (np.abs(out).max() + 1e-9)


def whoosh(dur=0.9, up=True):
    n = int(dur * SR)
    x = _band_noise(n, 250, 4500) if up else _band_noise(n, 4000, 300)
    t = np.linspace(0, 1, n)
    env = np.where(t < 0.62, (t / 0.62) ** 2.2, np.exp(-(t - 0.62) * 9))
    return (x * env * 0.8).astype(np.float32)


def riser(dur=2.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = t / dur
    noise = _band_noise(n, 200, 7000, 0.5) * p ** 2.5
    f = 110 * 2 ** (3 * p)                       # tone climbing three octaves
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * p ** 2 * 0.35
    x = noise * 0.7 + tone
    x[-int(0.04 * SR):] *= np.linspace(1, 0, int(0.04 * SR))
    return (x / (np.abs(x).max() + 1e-9) * 0.75).astype(np.float32)


def hit(dur=2.2, big=True):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 38 + 70 * np.exp(-t * 9)                 # pitch-dropping sub
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (2.2 if big else 4))
    burst = _band_noise(n, 900, 120, 0.6) * np.exp(-t * 14)
    tail = _band_noise(n, 300, 120, 0.5) * np.exp(-t * 2.5) * 0.25
    x = sub * 1.0 + burst * 0.55 + tail
    return (x / (np.abs(x).max() + 1e-9) * (0.9 if big else 0.55)).astype(np.float32)


def pop(dur=0.12):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 820 * t * (1 - t * 2)) * np.exp(-t * 45) + _band_noise(n, 3000, 2000) * np.exp(-t * 90) * 0.3
    return (x * 0.5).astype(np.float32)


def tick(dur=0.03):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 200) * 0.25).astype(np.float32)


def ambience(seconds, kind="room"):
    """Very quiet bed so there is never dead digital silence: room tone, wind or night."""
    n = int(seconds * SR)
    lo, hi = {"wind": (180, 700), "night": (2500, 4200), "room": (120, 400)}.get(kind, (120, 400))
    chunks, step = [], 20 * SR
    for a in range(0, n, step):
        m = min(step, n - a)
        c = _band_noise(m, lo, hi * 1.0001, 0.7, 4096)
        chunks.append(c)
    x = np.concatenate(chunks) if chunks else np.zeros(0, np.float32)
    t = np.arange(n) / SR
    x *= 0.6 + 0.4 * np.sin(2 * np.pi * t / 9.0) ** 2   # slow gusts / breathing
    return (x * 0.5).astype(np.float32)


def place(track, clip, at, gain=1.0):
    a = int(max(0, at) * SR)
    if a >= len(track):
        return
    b = min(len(track), a + len(clip))
    track[a:b] += clip[:b - a] * gain


def design(scenes, total, boundaries, outro_at, ambience_kind="room", level=1.0):
    """Builds the whole SFX track. boundaries: scene-change times that got a visual transition."""
    tr = np.zeros(int(total * SR) + SR, dtype=np.float32)
    if ambience_kind and ambience_kind != "none":
        tr[:int(total * SR)] += ambience(total, ambience_kind) * 0.05
    # opening: a hit under the title so the first second lands hard
    place(tr, hit(2.4, True), 0.05, 0.55)
    place(tr, whoosh(0.7, False), 0.0, 0.25)
    # whoosh on scene transitions, but not on every one (room to breathe)
    for k, b in enumerate(boundaries):
        if k % 2 == 0:
            place(tr, whoosh(0.85, k % 4 == 0), b - 0.55, 0.32)
    # on-screen text gets a pop, numbers/stat cards get a soft hit + counter ticks
    for s in scenes:
        if s.get("text"):
            t0 = s["start"] + 0.25
            if any(ch.isdigit() for ch in s["text"]):
                place(tr, hit(1.4, False), t0, 0.45)
                for i in range(10):
                    place(tr, tick(), t0 + i * 0.07, 0.6)
            else:
                place(tr, pop(), t0, 0.7)
    # a riser into the two-thirds "twist" and into the ending
    if len(scenes) > 4:
        twist = scenes[int(len(scenes) * 0.66)]["start"]
        place(tr, riser(2.4), twist - 2.4, 0.28)
        place(tr, hit(2.0, True), twist, 0.35)
    place(tr, riser(2.8), outro_at - 2.8, 0.22)
    place(tr, hit(2.6, True), outro_at, 0.45)
    tr = tr[:int(total * SR)] * level
    peak = np.abs(tr).max()
    return tr / peak * 0.9 if peak > 0.9 else tr
