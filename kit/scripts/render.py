"""Video 2 compositor: stock b-roll (bg.mp4) + big pasted avatar that switches photos with a
pop transition and glows while speaking + large live waveform + word-highlight captions
with pop-in + chapter cards, key-point cards and number pops + top progress bar.

python render.py --still 123.4 frame.png
python render.py --bg bg.mp4 --voice voice.wav --out final.mp4 --jobs 4
"""
import os as _os
KIT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import argparse, json, math, os, subprocess, sys, time
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
FB = f"{KIT}/fonts/Inter-Black.otf"
FXB = f"{KIT}/fonts/Inter-ExtraBold.otf"
FSB = f"{KIT}/fonts/Inter-Bold.otf"
YELLOW = (255, 214, 10)
ACCENT = (255, 196, 0)

PLAN = json.load(open("plan.json"))
CAP = json.load(open("captions.json"))
LV = np.load("levels.npz"); SPEC, RMS = LV["spec"], LV["rms"]
NF = len(RMS)
# smoothed loudness for the glow
RMS_S = np.convolve(RMS, np.ones(5) / 5, "same")
CUTS = sorted({round(s["s"] * FPS) for s in PLAN["scenes"][1:]})

AV_X = 18


def blend(frame, rgba, x, y, alpha=1.0):
    h, w = rgba.shape[:2]
    x0, y0 = max(x, 0), max(y, 0); x1, y1 = min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1 or alpha <= 0.003: return
    p = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = p[..., 3:4] * (alpha / 255.0)
    dst = frame[y0:y1, x0:x1].astype(np.float32)
    frame[y0:y1, x0:x1] = (dst + (p[..., :3] - dst) * a).astype(np.uint8)


def clamp(v, a=0.0, b=1.0): return min(max(v, a), b)
def ease_out(t): return 1 - (1 - clamp(t)) ** 3
def ease_back(t):
    t = clamp(t); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def rgba_np(im): return np.asarray(im, dtype=np.float32)


def scaled(arr_img, s):
    """arr_img: PIL RGBA. returns float array scaled by s."""
    if abs(s - 1) < 0.01: return rgba_np(arr_img)
    w, h = arr_img.size
    return rgba_np(arr_img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.BILINEAR))


# ---------------- bottom gradient ----------------
GRAD_H = 460
_g = np.linspace(0, 1, GRAD_H) ** 1.5 * 0.75
GRAD = (1 - _g)[:, None, None].astype(np.float32)

# ---------------- avatar ----------------
AV_IMG = {k: Image.open(f"{KIT}/avatar/sticker{k}.png") for k in (1, 2, 3)}
AV_ARR = {k: rgba_np(v) for k, v in AV_IMG.items()}
POP_STEPS = [0.82, 0.88, 0.93, 0.97, 1.0]
AV_POP = {k: [scaled(AV_IMG[k], s) for s in POP_STEPS] for k in AV_IMG}


def make_glow(im):
    a = im.split()[3]
    pad = 40
    big = Image.new("L", (im.width + 2 * pad, im.height + 2 * pad), 0)
    big.paste(a, (pad, pad))
    g = big.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(22))
    col = Image.new("RGBA", big.size, YELLOW + (0,)); col.putalpha(g.point(lambda v: int(v * 0.85)))
    return rgba_np(col), pad


GLOW = {k: make_glow(AV_IMG[k]) for k in AV_IMG}


def avatar_state(t):
    segs = PLAN["avatar"]
    for i, sc in enumerate(segs):
        if sc["s"] <= t < sc["e"]:
            return sc["id"], t - sc["s"], (segs[i - 1]["id"] if i else None)
    return segs[-1]["id"], 99, None


def draw_avatar(frame, t, f):
    k, since, prev = avatar_state(t)
    r = float(RMS_S[min(f, NF - 1)])
    bob = int(round(3 * math.sin(t * 2.0)))
    # outgoing avatar fades/shrinks quickly
    if prev is not None and since < 0.22:
        po = AV_ARR[prev]; a = 1 - since / 0.22
        blend(frame, po, AV_X, H - po.shape[0] + 30 + bob, alpha=a)
    if since < 0.4:
        idx = min(int(since / 0.4 * len(POP_STEPS)), len(POP_STEPS) - 1)
        img = AV_POP[k][idx]; alpha = clamp(since / 0.18)
    else:
        img = AV_ARR[k]; alpha = 1.0
    full = AV_ARR[k]
    x = AV_X + (full.shape[1] - img.shape[1]) // 2
    y = H - img.shape[0] + 30 + bob
    # speaking glow behind the sticker
    g, pad = GLOW[k]
    ga = clamp((r - 0.08) * 1.4) * alpha
    if ga > 0.02 and img is full:
        blend(frame, g, x - pad, y - pad, alpha=ga)
    blend(frame, img, x, y, alpha=alpha)
    return AV_X + full.shape[1]


# ---------------- waveform (big) ----------------
WF_BARS, WF_W, WF_H = 38, 600, 128


@lru_cache(maxsize=1)
def wf_bg():
    im = Image.new("RGBA", (WF_W + 40, WF_H + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((20, 26, WF_W + 20, WF_H + 26), WF_H // 2, fill=(0, 0, 0, 150))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(im).rounded_rectangle((20, 20, WF_W + 20, WF_H + 20), WF_H // 2, fill=(12, 16, 26, 225),
                                         outline=(255, 214, 10, 150), width=3)
    return rgba_np(im)


@lru_cache(maxsize=2)
def mic_icon(on):
    s = 76
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((2, 2, s - 2, s - 2), fill=(255, 60, 60, 255) if on else (90, 96, 110, 255))
    d.rounded_rectangle((29, 14, 47, 44), 9, fill=(255, 255, 255, 255))
    d.arc((21, 26, 55, 54), 0, 180, fill=(255, 255, 255, 255), width=4)
    d.line((38, 54, 38, 62), fill=(255, 255, 255, 255), width=4)
    d.line((29, 62, 47, 62), fill=(255, 255, 255, 255), width=4)
    return rgba_np(im)


def draw_wave(frame, f, x, y):
    blend(frame, wf_bg(), x - 20, y - 20)
    f = min(f, NF - 1)
    sp = SPEC[f]; r = float(RMS[f])
    on = r > 0.1
    cy = y + WF_H // 2
    # pulsing ring behind the mic while talking
    if on:
        rad = int(40 + 10 * r)
        yy, xx = np.ogrid[-rad:rad + 1, -rad:rad + 1]
        ring = ((xx ** 2 + yy ** 2) <= rad ** 2) & ((xx ** 2 + yy ** 2) >= (rad - 5) ** 2)
        cx = x + 64
        reg = frame[cy - rad:cy + rad + 1, cx - rad:cx + rad + 1]
        if reg.shape[:2] == ring.shape:
            reg[ring] = (reg[ring] * 0.4 + np.array([255, 90, 90]) * 0.6).astype(np.uint8)
    blend(frame, mic_icon(on), x + 64 - 38, cy - 38)
    half = WF_BARS // 2
    vals = np.concatenate([sp[:half][::-1], sp[:half]])
    bw = 8; x0 = x + 120; span = WF_W - 150
    gap = (span - WF_BARS * bw) / (WF_BARS - 1)
    for i in range(WF_BARS):
        v = 0.07 + 0.93 * float(vals[i]) * (0.3 + 0.7 * r)
        bh = max(8, int(v * (WF_H - 26)))
        bx = int(x0 + i * (bw + gap))
        c = np.array(YELLOW if v > 0.5 else (255, 255, 255), np.uint8)
        frame[cy - bh // 2:cy + bh // 2, bx:bx + bw] = c


# ---------------- captions ----------------
CAP_FONT = ImageFont.truetype(FB, 60)
CAP_Y = 975
CAP_MAXW = 1080


@lru_cache(maxsize=48)
def caption_pil(key, hi):
    words = key.split("\x00")
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    sp = d.textlength(" ", font=CAP_FONT) + 14
    ws = [d.textlength(w, font=CAP_FONT) for w in words]
    lines, cur, cw = [], [], 0
    for i, w in enumerate(ws):
        if cur and cw + sp + w > CAP_MAXW:
            lines.append(cur); cur, cw = [], 0
        cw += (sp if cur else 0) + w; cur.append(i)
    lines.append(cur)
    lh = 78
    img = Image.new("RGBA", (CAP_MAXW + 60, lh * len(lines) + 40), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    for li, line in enumerate(lines):
        tw = sum(ws[i] for i in line) + sp * (len(line) - 1)
        x = (img.width - tw) / 2; y = 16 + li * lh
        for i in line:
            if i == hi:
                dr.rounded_rectangle((x - 11, y - 4, x + ws[i] + 11, y + 72), 14, fill=YELLOW + (255,))
                dr.text((x, y), words[i], font=CAP_FONT, fill=(12, 12, 12))
            else:
                dr.text((x, y), words[i], font=CAP_FONT, fill=(255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0))
            x += ws[i] + sp
    return img


@lru_cache(maxsize=48)
def caption_arr(key, hi): return rgba_np(caption_pil(key, hi))


_cap_i = [0]


def draw_caption(frame, t, cx):
    i = _cap_i[0]
    if i >= len(CAP) or CAP[i]["s"] - 0.05 > t:
        i = 0
    while i < len(CAP) and CAP[i]["e"] + 0.15 <= t: i += 1
    _cap_i[0] = i
    if i >= len(CAP) or CAP[i]["s"] - 0.05 > t: return
    c = CAP[i]
    hi = -1
    for j, w in enumerate(c["words"]):
        if t >= w["s"] - 0.02: hi = j
    key = "\x00".join(w["w"] for w in c["words"])
    since = t - c["s"] + 0.05
    if since < 0.16:
        s = 0.86 + 0.14 * ease_back(since / 0.16)
        img = scaled(caption_pil(key, hi), s)
    else:
        img = caption_arr(key, hi)
    y = CAP_Y - img.shape[0] // 2
    blend(frame, img, cx - img.shape[1] // 2, y, alpha=clamp(since / 0.1))


# ---------------- chapter card (big, centre) ----------------
CH_NUM = ImageFont.truetype(FB, 150)
CH_T = ImageFont.truetype(FB, 78)
CH_S = ImageFont.truetype(FSB, 38)


@lru_cache(maxsize=4)
def chapter_pil(num, text, sub):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = max(d.textlength(text, font=CH_T), d.textlength(sub, font=CH_S) if sub else 0)
    nw = d.textlength(num, font=CH_NUM) if num else 0
    w = int(tw + nw + (90 if num else 0) + 120); h = 230
    im = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((30, 40, w + 30, h + 40), 28, fill=(0, 0, 0, 170))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((30, 30, w + 30, h + 30), 28, fill=(14, 18, 28, 238), outline=YELLOW + (255,), width=4)
    x = 90
    if num:
        dr.text((x, 30 + (h - 170) // 2 - 6), num, font=CH_NUM, fill=YELLOW)
        x += nw + 40
        dr.rectangle((x, 75, x + 6, h - 15), fill=(255, 255, 255, 90))
        x += 50
    ty = 80 if sub else 115
    dr.text((x, ty), text, font=CH_T, fill=(255, 255, 255))
    if sub: dr.text((x + 2, ty + 98), sub, font=CH_S, fill=(200, 205, 215))
    return im


def draw_chapter(frame, t):
    for c in PLAN.get("chapters", []):
        if c["s"] <= t < c["e"]:
            im = chapter_pil(c.get("num", ""), c["text"], c.get("sub", ""))
            since, left = t - c["s"], c["e"] - t
            if since < 0.45:
                s = 0.6 + 0.4 * ease_back(since / 0.45); arr = scaled(im, s); a = clamp(since / 0.2)
            elif left < 0.35:
                s = 1 - 0.1 * (1 - left / 0.35); arr = scaled(im, s); a = clamp(left / 0.35)
            else:
                arr = chapter_arr(c.get("num", ""), c["text"], c.get("sub", "")); a = 1
            blend(frame, arr, (W - arr.shape[1]) // 2, 250 - arr.shape[0] // 2, alpha=a)
            return True
    return False


@lru_cache(maxsize=4)
def chapter_arr(num, text, sub): return rgba_np(chapter_pil(num, text, sub))


# ---------------- key-point card (top-left, slides in) ----------------
TITLE_FONT = ImageFont.truetype(FB, 62)
SUB_FONT = ImageFont.truetype(FSB, 34)


@lru_cache(maxsize=8)
def title_arr(text, sub):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = d.textlength(text, font=TITLE_FONT)
    sw = d.textlength(sub, font=SUB_FONT) if sub else 0
    w = int(max(tw, sw) + 80); h = 108 + (50 if sub else 0)
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((20, 26, w + 20, h + 26), 18, fill=(0, 0, 0, 140))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((20, 20, w + 20, h + 20), 18, fill=(255, 255, 255, 246))
    dr.rounded_rectangle((20, 20, 36, h + 20), 6, fill=ACCENT + (255,))
    dr.text((60, 34), text, font=TITLE_FONT, fill=(16, 18, 28))
    if sub: dr.text((62, 110), sub, font=SUB_FONT, fill=(90, 96, 110))
    return rgba_np(im)


def draw_title(frame, t):
    for ti in PLAN["titles"]:
        if ti["s"] <= t < ti["e"]:
            img = title_arr(ti["text"], ti.get("sub", ""))
            k = min(ease_out((t - ti["s"]) / 0.35), ease_out((ti["e"] - t) / 0.3))
            # text reveal: a wipe from left on entry
            if t - ti["s"] < 0.5:
                wv = int(img.shape[1] * ease_out((t - ti["s"]) / 0.5))
                img = img[:, :max(wv, 1)]
            blend(frame, img, 60 - int((1 - k) * 60), 56, alpha=k)
            return True
    return False


# ---------------- number / keyword pop (top-right) ----------------
POP_FONT = ImageFont.truetype(FB, 96)


@lru_cache(maxsize=8)
def pop_pil(text):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = d.textlength(text, font=POP_FONT)
    w, h = int(tw + 80), 150
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((20, 28, w + 20, h + 28), 26, fill=(0, 0, 0, 160))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((20, 20, w + 20, h + 20), 26, fill=YELLOW + (255,))
    dr.text((60, 30), text, font=POP_FONT, fill=(14, 14, 14))
    return im


def draw_pop(frame, t):
    for p in PLAN.get("pops", []):
        if p["s"] <= t < p["e"]:
            im = pop_pil(p["text"]); since, left = t - p["s"], p["e"] - t
            if since < 0.35:
                arr = scaled(im, 0.5 + 0.5 * ease_back(since / 0.35)); a = clamp(since / 0.12)
            else:
                arr = rgba_np(im) if left > 0.25 else scaled(im, 0.9 + 0.1 * left / 0.25)
                a = clamp(left / 0.25)
            ang = 0
            blend(frame, arr, W - 70 - arr.shape[1] + (rgba_np(im).shape[1] - arr.shape[1]) // 2,
                  300 - arr.shape[0] // 2, alpha=a)
            return


# ---------------- progress bar ----------------
def draw_progress(frame, f):
    p = f / (PLAN["duration"] * FPS)
    frame[0:7, :] = (frame[0:7, :] * 0.35).astype(np.uint8)
    frame[0:7, :int(W * p)] = YELLOW


# ---------------- frame ----------------
def compose(frame, f):
    t = f / FPS
    # quick dip at cuts (soft transition)
    for c in CUTS:
        d = f - c
        if -3 <= d <= 3:
            frame[:] = (frame * (0.55 + 0.15 * abs(d))).astype(np.uint8); break
        if d < -3: break
    frame[H - GRAD_H:] = (frame[H - GRAD_H:].astype(np.float32) * GRAD).astype(np.uint8)
    right = draw_avatar(frame, t, f)
    draw_wave(frame, f, right - 10, 640)
    cap_cx = (right + W) // 2 - 10
    draw_caption(frame, t, cap_cx)
    if not draw_chapter(frame, t):
        draw_title(frame, t)
        draw_pop(frame, t)
    draw_progress(frame, f)
    return frame


def render_part(bg, start, n, out):
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{start / FPS:.4f}", "-i", bg, "-frames:v", str(n),
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                            "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    sz = W * H * 3; last = None
    for i in range(n):
        buf = dec.stdout.read(sz)
        if len(buf) < sz:
            frame = last.copy() if last is not None else np.zeros((H, W, 3), np.uint8)
        else:
            frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy(); last = frame.copy()
        enc.stdin.write(compose(frame, start + i).tobytes())
        if i % 1500 == 0: print(f"{out}: {i}/{n}", flush=True)
    enc.stdin.close(); enc.wait(); dec.wait()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg", default="bg.mp4")
    ap.add_argument("--voice", default="voice.wav")
    ap.add_argument("--out", default="final.mp4")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--part", type=int, nargs=3)
    ap.add_argument("--still", nargs=2)
    a = ap.parse_args()
    total = int(PLAN["duration"] * FPS)
    if a.still:
        f = int(float(a.still[0]) * FPS)
        fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{f / FPS:.3f}", "-i", a.bg, "-frames:v", "1",
                             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        frame = np.frombuffer(fr, np.uint8).reshape(H, W, 3).copy()
        Image.fromarray(compose(frame, f)).save(a.still[1]); sys.exit()
    if a.part:
        render_part(a.bg, a.part[0], a.part[1], f"parts/part{a.part[2]:02d}.mp4"); sys.exit()
    os.makedirs("parts", exist_ok=True)
    nparts = a.jobs * 4
    step = math.ceil(total / nparts)
    todo = [(i * step, min(step, total - i * step), i) for i in range(nparts) if i * step < total]
    running = []
    for s, n, i in todo:
        if os.path.exists(f"parts/part{i:02d}.done"): continue
        while len(running) >= a.jobs:
            for p in running:
                if p.poll() is not None: running.remove(p); break
            else: time.sleep(2)
        running.append(subprocess.Popen(f"python3 {_os.path.abspath(__file__)} --bg {a.bg} --part {s} {n} {i} && touch parts/part{i:02d}.done", shell=True))
    for p in running: p.wait()
    with open("parts/list.txt", "w") as fl:
        for _, _, i in todo: fl.write(f"file 'part{i:02d}.mp4'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "parts/list.txt", "-i", a.voice,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
                    "-movflags", "+faststart", a.out], check=True)
    print("done", a.out)
