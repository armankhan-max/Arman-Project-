"""ASMR soundtrack + MP4 export for the teddy slicing render.

Reads timeline.json (the same impact list that drove the knife), synthesises a
48 kHz stereo WAV with one sound per blade contact, then muxes it with the PNG frames.

  python post.py OUTDIR [--name teddy_bear_slicing.mp4]

Sounds (all generated, nothing downloaded):
  slow_slice  long fabric-tearing "shhhrrk" of the blade going through plush + cotton
  slice/chop  short plush slice + soft wooden tap on the table
  rapid/dice  tight crisp chops; the dice pass becomes a fast rattling run
  cube_fall   soft little cube taps landing on wood
  knife_in/out  a quiet metallic "shing"
  ting        glassy bell 'ting' on every counted cut (rising pitch), bigger chime at 1/4/10/100/1000
  ambience    very low garden air with the odd distant bird
Overlay: big cut counter at the top (+ VERTICAL / HORIZONTAL CUT tag), cube counter at the bottom.
"""
import json
import os
import subprocess
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
rng = np.random.default_rng(11)

out_dir = os.path.abspath(sys.argv[1])
name = sys.argv[sys.argv.index("--name") + 1] if "--name" in sys.argv else "teddy_bear_slicing.mp4"
meta = json.load(open(os.path.join(out_dir, "timeline.json")))
fps, n_frames = meta["fps"], meta["frames"]
dur = n_frames / fps
N = int(dur * SR)
L = np.zeros(N)
R = np.zeros(N)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="high", fs=SR, output="sos"), x)


def place(snd, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    snd = snd[: N - i] * gain
    L[i:i + len(snd)] += snd * np.sqrt(0.5 * (1 - pan))
    R[i:i + len(snd)] += snd * np.sqrt(0.5 * (1 + pan))


def t_of(frame):            # PDF rule: frame 1 is t = 0
    return (frame - 1) / fps


def env(n, a, d):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d)
    return e


def plush_cut(length, bright=1.0):
    """Blade through fabric + stuffing: granular crackle on band-limited noise."""
    n = int(length * SR)
    base = bp(rng.standard_normal(n), 900, 7000 * bright) * 0.5
    grains = np.zeros(n)
    k = int(length * 900)
    idx = rng.integers(0, n - 200, k)
    for i in idx:
        g = rng.standard_normal(60) * np.hanning(60) * rng.uniform(0.3, 1.0)
        grains[i:i + 60] += g
    grains = bp(grains, 1500, 11000)
    tex = base + grains * 0.9
    shape = np.sin(np.linspace(0, np.pi, n)) ** 0.6
    wobble = 0.75 + 0.25 * np.sin(np.linspace(0, length * 2 * np.pi * 3.1, n))
    return tex * shape * wobble


def wood_tap(gain=1.0, pitch=1.0):
    n = int(0.18 * SR)
    t = np.arange(n) / SR
    body = (np.sin(2 * np.pi * 180 * pitch * t) * np.exp(-t / 0.035) +
            0.5 * np.sin(2 * np.pi * 410 * pitch * t) * np.exp(-t / 0.02))
    click = hp(rng.standard_normal(n), 2500) * np.exp(-t / 0.004) * 0.6
    return (body + click) * gain


def crisp_chop(gain=1.0):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    s = bp(rng.standard_normal(n), 1800, 9000) * np.exp(-t / 0.018)
    return (s + wood_tap(0.55, rng.uniform(0.9, 1.15))[:n]) * gain


def shing(length=0.8):
    n = int(length * SR)
    t = np.arange(n) / SR
    f = np.array([2900, 4370, 6120, 7900])
    s = sum(np.sin(2 * np.pi * fi * t + rng.uniform(0, 6)) / (k + 1) for k, fi in enumerate(f))
    sweep = bp(rng.standard_normal(n), 3000, 12000) * np.exp(-t / 0.08) * 0.4
    return (s * 0.25 * np.exp(-t / 0.25) + sweep) * np.minimum(1, t / 0.02)


def soft_whoosh(length=0.5):
    n = int(length * SR)
    w = lp(rng.standard_normal(n), 900) * np.sin(np.linspace(0, np.pi, n)) ** 2
    return w * 0.6


def ting(freq=2093.0, length=1.6, bright=1.0):
    """Clear glassy 'ting' (inharmonic bell partials) - the satisfying ear-tickle on each counted cut."""
    n = int(length * SR)
    t = np.arange(n) / SR
    parts = [(1.0, 1.0, 1.0), (2.756, 0.45, 0.55), (5.404, 0.25 * bright, 0.30), (8.933, 0.12 * bright, 0.18)]
    out = np.zeros(n)
    for ratio, amp, dec in parts:
        out += amp * np.sin(2 * np.pi * freq * ratio * t + rng.uniform(0, 6)) * np.exp(-t / (dec * length * 0.5))
    out *= np.minimum(1, t / 0.002)
    return out


def tiring(length=1.2):
    """Shimmering metallic 'tiriiing' as the blade glides: a rising cluster of tiny tings."""
    n = int(length * SR)
    out = np.zeros(n)
    notes = [2349, 2637, 2960, 3136, 3520, 3951]
    for k in range(10):
        f = notes[k % len(notes)] * (1 + 0.5 * (k // len(notes)))
        snd = ting(f, 0.6, 0.6) * (0.5 + 0.5 * k / 10)
        i = int(k * (n - len(snd)) / 10)
        out[i:i + len(snd)] += snd[: n - i]
    return out


def cube_tap():
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    f = rng.uniform(500, 900)
    return (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.012) +
            bp(rng.standard_normal(n), 1500, 6000) * np.exp(-t / 0.006) * 0.5)


SCALE = [1047, 1175, 1319, 1568, 1760, 2093, 2349, 2637, 3136, 3520]    # C6 pentatonic-ish climb
MILESTONES = {1, 4, 10, 100}
ev = meta["events"]
for e in ev:
    t0 = t_of(e["frame"])
    k = e["type"]
    if k == "knife_in":
        place(soft_whoosh(0.7), t0, 0.35, 0.5)
        place(shing(1.0), t0 + 0.6, 0.18, 0.4)
    elif k == "slow_slice":
        length = (e["end"] - e["frame"]) / fps
        place(plush_cut(length), t0, 0.55, 0.0)
    elif k == "slow":
        place(wood_tap(1.0, 0.95), t0, 0.7)
        place(tiring(1.0), t0 - 1.0, 0.10, 0.3)
    elif k == "split":
        place(plush_cut((e["end"] - e["frame"]) / fps, 0.5), t0, 0.22)
    elif k == "slice":
        place(plush_cut(0.38), t0 - 0.36, 0.5, rng.uniform(-0.2, 0.2))
        place(wood_tap(0.85), t0, 0.6)
    elif k == "chop":
        place(plush_cut(0.2), t0 - 0.18, 0.45, rng.uniform(-0.25, 0.25))
        place(wood_tap(0.7, 1.05), t0, 0.55)
    if k in ("slow", "slice", "chop"):
        place(ting(SCALE[min(e.get("n", 1) - 1, 9)], 1.8), t0 + 0.02, 0.16, rng.uniform(-0.3, 0.3))
    if e.get("n") in MILESTONES:
        place(ting(2637, 2.4) + ting(3951, 2.4) * 0.6, t0 + 0.05, 0.14)
    if k == "rapid" and e.get("n", 0) % 9 == 0:
        place(ting(rng.choice(SCALE[4:]), 0.5, 0.5), t0, 0.05, rng.uniform(-0.6, 0.6))
    if k == "rapid":
        place(crisp_chop(), t0, 0.32, rng.uniform(-0.3, 0.3))
    elif k == "dice":
        place(crisp_chop(), t0, 0.10, rng.uniform(-0.5, 0.5))
    elif k == "cube_fall":
        place(cube_tap(), t0, 0.07, rng.uniform(-0.6, 0.6))
        if rng.random() < 0.12:
            place(ting(rng.uniform(3000, 5200), 0.35, 0.4), t0, 0.025, rng.uniform(-0.8, 0.8))
    elif k == "knife_out":
        place(soft_whoosh(0.6), t0, 0.3, 0.5)
        place(ting(2093, 3.0) + ting(3136, 3.0) * 0.7 + ting(4186, 3.0) * 0.4, t0 + 0.2, 0.18)   # 1000 reached

# garden ambience: soft air + a few distant birds
air = lp(rng.standard_normal(N), 600) * 0.012
L += air
R += lp(rng.standard_normal(N), 600) * 0.012
for tb in np.arange(1.5, dur - 1, 3.7):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f0 = rng.uniform(3200, 4200)
    chirp = np.sin(2 * np.pi * (f0 + 900 * np.sin(2 * np.pi * 14 * t)) * t) * np.hanning(n)
    place(chirp, tb + rng.uniform(0, 1.2), 0.012, rng.uniform(-0.8, 0.8))

mix = np.stack([L, R], 1)
mix = hp(mix.T, 30).T
fade = int(0.4 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
peak = np.max(np.abs(mix))
mix = mix / peak * 0.89 if peak > 0 else mix          # about -1 dBFS, no clipping
wav = os.path.join(out_dir, "soundtrack.wav")
wavfile.write(wav, SR, (mix * 32767).astype(np.int16))
print("wrote", wav)

# ---------------------------------------------------------------- counter overlay (top: CUTS, bottom: CUBES)
from PIL import Image, ImageDraw, ImageFont, ImageFilter  # noqa: E402

FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W, H = meta["width"], meta["height"]
k = W / 1080.0
f_num = ImageFont.truetype(FONT, int(150 * k))
f_lab = ImageFont.truetype(FONT, int(64 * k))
f_num2 = ImageFont.truetype(FONT, int(96 * k))
f_tag = ImageFont.truetype(FONT, int(40 * k))
WHITE, GOLD = (250, 246, 240), (236, 170, 70)
per = {d["frame"]: d for d in meta["per_frame"]}
change = {}
prev = None
for fr in range(1, n_frames + 1):
    c = per[fr]["cuts"]
    if c != prev:
        change[fr] = c
        prev = c
last_change = 0
cut_ev = [e for e in ev if e["type"] in ("slow", "slice", "chop")]


RAPID = [e["frame"] for e in ev if e["type"] == "rapid"]
DICE = [e["frame"] for e in ev if e["type"] == "dice"]


def tag_for(fr):
    if RAPID and RAPID[0] - 2 <= fr <= RAPID[-1] + 4:
        return "RAPID SLICING"
    if DICE and DICE[0] - 2 <= fr <= DICE[-1] + 6:
        return "DICING  |  VERTICAL + HORIZONTAL"
    for e in cut_ev:
        if 0 <= fr - e["frame"] < fps * 0.9:
            return "VERTICAL CUT" if e["axis"] == "x" else "HORIZONTAL CUT"
    return None


def text_c(d, y, txt, font, fill, shadow=True):
    w = d.textlength(txt, font=font)
    x = (W - w) / 2
    d.text((x, y), txt, font=font, fill=fill)
    return x, w


def overlay(img, fr):
    global last_change
    if fr in change:
        last_change = fr
    cuts, cubes = per[fr]["cuts"], per[fr]["cubes"]
    pop = max(0.0, 1 - (fr - last_change) / 5.0) if cuts < 101 else 0.0
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    num = "{:,}".format(cuts)
    fn = ImageFont.truetype(FONT, int(150 * k * (1 + 0.18 * pop)))
    text_c(d, int(120 * k - 24 * k * pop), num, fn, WHITE)
    text_c(d, int(335 * k), "CUT" if cuts == 1 else "CUTS", f_lab, GOLD)
    tag = tag_for(fr)
    if tag:
        tw = d.textlength(tag, font=f_tag)
        pad = 18 * k
        x0, y0 = (W - tw) / 2 - pad, 425 * k
        d.rounded_rectangle((x0, y0, x0 + tw + 2 * pad, y0 + 62 * k), radius=31 * k, fill=(20, 14, 10, 150))
        d.text(((W - tw) / 2, y0 + 8 * k), tag, font=f_tag, fill=WHITE)
    text_c(d, int(H - 330 * k), "{:,}".format(cubes), f_num2, WHITE)
    text_c(d, int(H - 215 * k), "CUBES", f_lab, GOLD)
    sh = layer.split()[3].filter(ImageFilter.GaussianBlur(10 * k))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow.putalpha(sh.point(lambda a: int(a * 0.55)))
    base = img.convert("RGBA")
    base.alpha_composite(shadow)
    base.alpha_composite(layer)
    return base.convert("RGB")


final_dir = os.path.join(out_dir, "frames_text")
os.makedirs(final_dir, exist_ok=True)
for fr in range(1, n_frames + 1):
    src = os.path.join(out_dir, "frames", "f_%04d.png" % fr)
    overlay(Image.open(src), fr).save(os.path.join(final_dir, "f_%04d.png" % fr), compress_level=1)
print("overlay done")

mp4 = os.path.join(out_dir, name)
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-start_number", "1",
       "-i", os.path.join(final_dir, "f_%04d.png"), "-i", wav,
       "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
       "-vf", "scale=%d:%d:flags=lanczos" % (meta["width"], meta["height"]),
       "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", mp4]
subprocess.run(cmd, check=True)
print("wrote", mp4)
