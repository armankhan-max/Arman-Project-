"""Documentary compositor: plates + 2D graphics + text animations + shakes -> video frames.

Usage:
  python3 comp.py --events                     # resolve EDL -> build/events.json (for the sound mix)
  python3 comp.py --part 0 --parts 4           # render a quarter of the frames to build/part0.mp4
  python3 comp.py --still 123.4                # render one frame to build/still.png
"""
import argparse
import json
import math
import os
import subprocess
import sys
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import edl  # noqa: E402
import gfx2d  # noqa: E402

W, H, FPS = 1920, 1080, 30
BUILD = os.path.join(HERE, "build")
PLATES = os.path.join(BUILD, "plates")
FONTS = os.path.join(HERE, "assets", "fonts")
RED = (214, 40, 40)
WHITE = (240, 235, 225)
GREEN = (60, 200, 110)


# ================================================================== timeline resolution
def load_timeline():
    tl = json.load(open(os.path.join(HERE, "timeline.json")))
    paras = {}
    for s in tl:
        paras.setdefault(s["p"], []).append(s)
    return tl, paras


def clean(w):
    return w.strip(".,;:!?\"'“”").lower()


def word_time(para, word, occ=1):
    target = clean(word)
    n = 0
    for s in para:
        for w, t in s["words"]:
            if clean(w) == target or (len(target) > 3 and clean(w).startswith(target)):
                n += 1
                if n == occ:
                    return t
    raise KeyError(f"word {word!r} not in paragraph: {para[0]['text'][:50]}")


def resolve():
    tl, paras = load_timeline()
    total = tl[-1]["end"] + 4.0
    keys = sorted(paras)
    starts = {p: (0.0 if p == keys[0] else paras[p][0]["start"] - 0.25) for p in keys}
    shots, texts, quakes, sfx = [], [], [], []
    for i, p in enumerate(keys):
        a = starts[p]
        b = starts[keys[i + 1]] if i + 1 < len(keys) else total
        ent = edl.E.get(p)
        if not ent:
            raise SystemExit(f"paragraph {p} has no EDL entry")
        sl = ent["shots"]
        ts = []
        for k, s in enumerate(sl):
            if k == 0:
                ts.append(a)
            elif s.get("at"):
                ts.append(word_time(paras[p], s["at"]) - 0.12)
            else:
                ts.append(None)
        # interpolate unanchored
        for k in range(len(ts)):
            if ts[k] is None:
                nxt = next((ts[j] for j in range(k + 1, len(ts)) if ts[j] is not None), b)
                prv = ts[k - 1]
                cnt = next((j for j in range(k + 1, len(ts)) if ts[j] is not None), len(ts)) - k + 1
                ts[k] = prv + (nxt - prv) / cnt
        for k, s in enumerate(sl):
            e = ts[k + 1] if k + 1 < len(sl) else b
            shots.append(dict(s, start=ts[k], end=e, para=p))
        for x in ent["extra"]:
            t = word_time(paras[x["p"] or p] if x.get("p") is not None else paras[p], x["at"]) if x.get("at") else a + 0.2
            x = dict(x, t=t, para=p)
            if x["kind"] == "quake":
                quakes.append(x)
            elif x["kind"] == "sfx":
                sfx.append(x)
            else:
                texts.append(x)
    return dict(total=total, shots=shots, texts=texts, quakes=quakes, sfx=sfx, paras={p: (starts[p]) for p in keys})


# ================================================================== look: sky, grade, overlays
def fbm(h, w, seed, octaves=6, base=4, persistence=0.55):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = base * 2 ** o
        small = rng.random((max(2, int(n * h / w)) + 1, n + 1)).astype(np.float32)
        out += cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC) * amp
        tot += amp
        amp *= persistence
    return out / tot


SKY = {
    "day": ((0.24, 0.42, 0.66), (0.72, 0.8, 0.86), 0.55),
    "disaster": ((0.42, 0.42, 0.42), (0.78, 0.72, 0.62), 0.75),
    "dark": ((0.12, 0.14, 0.18), (0.4, 0.42, 0.45), 0.8),
    "memory": ((0.3, 0.38, 0.5), (0.75, 0.72, 0.68), 0.6),
    "dawn": ((0.25, 0.32, 0.5), (0.98, 0.72, 0.5), 0.45),
    "hope": ((0.28, 0.45, 0.68), (0.9, 0.85, 0.75), 0.5),
    "dusk": ((0.18, 0.2, 0.36), (1.0, 0.55, 0.3), 0.55),
    "mourn": ((0.3, 0.32, 0.36), (0.7, 0.7, 0.7), 0.8),
    "night": ((0.01, 0.015, 0.03), (0.04, 0.05, 0.08), 0.3),
}


@lru_cache(maxsize=12)
def sky_image(kind, w, h, seed=3):
    top, hor, cover = SKY.get(kind, SKY["day"])
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None] ** 0.8
    grad = np.array(top, np.float32)[None, None] * (1 - y) + np.array(hor, np.float32)[None, None] * y
    grad = np.repeat(grad, w, axis=1)
    n = fbm(h, w, seed, 7, 3)
    # stretch clouds horizontally, perspective-ish: smaller near horizon
    c = np.clip((n - (1 - cover * 0.75)) * 3.0, 0, 1)
    c = c * np.clip(1.2 - y[:, :, 0] * 0.9, 0, 1)
    shade = fbm(h, w, seed + 5, 5, 6)
    cloud_col = np.stack([0.92 - 0.25 * shade, 0.92 - 0.25 * shade, 0.95 - 0.22 * shade], -1)
    if kind in ("dusk", "dawn"):
        cloud_col = cloud_col * np.array([1.0, 0.75, 0.6], np.float32) + np.array([0.08, 0.02, 0.0], np.float32)
    if kind in ("disaster", "mourn", "dark"):
        cloud_col = cloud_col * 0.75
    out = grad * (1 - c[..., None]) + cloud_col * c[..., None]
    return out.astype(np.float32)


GRADES = {  # sat, contrast, gain rgb, lift, gamma, shadow tint
    "day": (0.82, 1.12, (1.03, 1.0, 0.95), 0.015, 1.0, (0.0, 0.01, 0.02)),
    "disaster": (0.5, 1.18, (1.06, 0.98, 0.86), 0.03, 1.05, (0.02, 0.015, 0.0)),
    "dark": (0.45, 1.22, (0.72, 0.74, 0.8), 0.01, 1.15, (0.0, 0.0, 0.015)),
    "night": (0.75, 1.15, (0.82, 0.9, 1.12), 0.0, 1.05, (0.0, 0.005, 0.02)),
    "memory": (0.42, 1.06, (0.96, 1.0, 1.05), 0.045, 1.0, (0.0, 0.01, 0.02)),
    "dawn": (0.78, 1.08, (1.1, 0.98, 0.86), 0.02, 0.98, (0.01, 0.0, 0.02)),
    "hope": (0.92, 1.06, (1.06, 1.01, 0.92), 0.02, 0.95, (0.0, 0.01, 0.0)),
    "dusk": (0.9, 1.1, (1.16, 0.93, 0.78), 0.015, 1.0, (0.02, 0.0, 0.03)),
    "mourn": (0.15, 1.12, (0.9, 0.9, 0.92), 0.02, 1.1, (0.0, 0.0, 0.0)),
}


def grade(img, kind):
    sat, con, gain, lift, gam, sh = GRADES.get(kind, GRADES["day"])
    x = img
    lum = (x * np.array([0.299, 0.587, 0.114], np.float32)).sum(-1, keepdims=True)
    x = lum + (x - lum) * sat
    x = np.clip(x, 0, 1)
    x = 0.5 + (x - 0.5) * con
    x = np.clip(x, 0, 1)
    x = x * x * (3 - 2 * x) * 0.35 + x * 0.65  # gentle S
    x = x * np.array(gain, np.float32)
    x = lift + x * (1 - lift)
    x = x + np.array(sh, np.float32) * (1 - lum)
    x = np.clip(x, 0, 1) ** gam
    return np.clip(x, 0, 1)


@lru_cache(maxsize=6)
def plate_base(name, grade_kind, dim=1.0):
    path = os.path.join(PLATES, name + ".png")
    if not os.path.exists(path):
        alt = os.path.join(PLATES, name + "_prev.png")
        if os.path.exists(alt):
            path = alt
        else:
            img = np.full((1080, 1920, 3), 50, np.uint8)
            cv2.putText(img, "MISSING " + name, (100, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 4)
            return img
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im.shape[1] != 1920:
        im = cv2.resize(im, (1920, int(im.shape[0] * 1920 / im.shape[1])),
                        interpolation=cv2.INTER_AREA if im.shape[1] > 1920 else cv2.INTER_LANCZOS4)
    rgb = im[..., :3][..., ::-1].astype(np.float32) / 255.0
    if im.shape[2] == 4:
        a = im[..., 3].astype(np.float32)[..., None] / 255.0
        sky = sky_image(grade_kind if grade_kind in SKY else "day", rgb.shape[1], rgb.shape[0], seed=hash(name) % 97)
        rgb = rgb * a + sky * (1 - a)
    out = grade(rgb, grade_kind) * dim
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)


# vignette + grain
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2)
VIGNETTE = np.clip(1.0 - 0.55 * np.clip(_r - 0.45, 0, None) ** 1.6, 0.25, 1).astype(np.float32)[..., None]
_rng = np.random.default_rng(5)
GRAIN = [cv2.GaussianBlur(_rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.7) for _ in range(6)]
del _yy, _xx, _r


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def back_out(x, s=1.7):
    x = min(1.0, max(0.0, x)) - 1
    return x * x * ((s + 1) * x + s) + 1


# ================================================================== camera move on plates
MOVES = {
    "in": ((0.5, 0.5, 1.02), (0.5, 0.48, 1.12)),
    "out": ((0.5, 0.48, 1.13), (0.5, 0.5, 1.02)),
    "left": ((0.56, 0.5, 1.09), (0.44, 0.5, 1.09)),
    "right": ((0.44, 0.5, 1.09), (0.56, 0.5, 1.09)),
    "up": ((0.5, 0.6, 1.1), (0.5, 0.4, 1.1)),
    "down": ((0.5, 0.4, 1.1), (0.5, 0.6, 1.1)),
    "static": ((0.5, 0.5, 1.04), (0.5, 0.5, 1.05)),
}


def render_plate(shot, u, d, t):
    img = plate_base(shot["name"], shot["grade"], shot.get("dim", 1.0))
    ph, pw = img.shape[:2]
    (x0, y0, z0), (x1, y1, z1) = MOVES[shot["move"]]
    # documentary moves are almost linear (gentle ease at the ends)
    k = u / max(d, 0.01)
    k = 0.15 * ease(k) + 0.85 * k
    cx, cy, z = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, z0 + (z1 - z0) * k
    # handheld drift
    hx = 2.5 * math.sin(t * 0.7 + 1.3) + 1.5 * math.sin(t * 1.9)
    hy = 2.0 * math.sin(t * 0.9) + 1.2 * math.sin(t * 2.3 + 0.4)
    s = max(W / pw, H / ph) * z
    # keep the crop inside the plate
    half_w, half_h = W / (2 * s), H / (2 * s)
    px = min(max(cx * pw, half_w), pw - half_w)
    py = min(max(cy * ph, half_h), ph - half_h)
    M = np.float32([[s, 0, W / 2 - s * px + hx], [0, s, H / 2 - s * py + hy]])
    out = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if shot.get("blackout"):
        f = 1 - 0.85 * ease((k - 0.35) / 0.1)
        flick = 1.0 if k < 0.3 or k > 0.46 else (0.4 if int(t * 20) % 3 == 0 else 1.0)
        out = (out.astype(np.float32) * f * flick).astype(np.uint8)
    return out


# ================================================================== particles
def dust_layer(frame, t, seed, amount=1.0, fall=False):
    rng = np.random.default_rng(seed)
    n = int(70 * amount)
    xs = rng.random(n) * W
    ys = rng.random(n) * H
    sp = rng.random(n) * 0.6 + 0.2
    sz = rng.random(n) ** 3 * 4 + 1
    ph = rng.random(n) * 6.28
    layer = np.zeros((H // 2, W // 2), np.float32)
    for i in range(n):
        x = (xs[i] + t * 25 * sp[i] + 20 * math.sin(t * 0.5 + ph[i])) % W
        y = (ys[i] + t * (120 if fall else -8) * sp[i] + 10 * math.sin(t * 0.7 + ph[i] * 2)) % H
        cv2.circle(layer, (int(x / 2), int(y / 2)), int(sz[i]), 0.35 + 0.4 * sp[i], -1, cv2.LINE_AA)
    layer = cv2.GaussianBlur(layer, (0, 0), 1.2)
    layer = cv2.resize(layer, (W, H))
    f = frame.astype(np.float32)
    f += layer[..., None] * np.array([200, 190, 170], np.float32) * 0.5
    return np.clip(f, 0, 255).astype(np.uint8)


@lru_cache(maxsize=1)
def leak_img():
    n = fbm(270, 480, 9, 3, 2)
    col = np.stack([n * 1.0, n * 0.55, n * 0.2], -1)
    return cv2.resize(col.astype(np.float32), (W * 2, H))


def light_leak(frame, t, amount=0.25):
    li = leak_img()
    off = int((t * 40) % W)
    l = li[:, off:off + W]
    f = frame.astype(np.float32) / 255
    l = l * amount
    f = 1 - (1 - f) * (1 - l)
    return (f * 255).astype(np.uint8)


# ================================================================== text rendering
@lru_cache(maxsize=64)
def font(name, size, var=None):
    path = {"oswald": "Oswald.ttf", "playfair": "Playfair.ttf", "bebas": "BebasNeue.ttf", "type": "SpecialElite.ttf",
            "courier": "CourierPrimeBold.ttf", "cinzel": "Cinzel.ttf"}[name]
    f = ImageFont.truetype(os.path.join(FONTS, path), size)
    if var:
        try:
            f.set_variation_by_name(var)
        except Exception:
            pass
    return f


def tracked(draw, xy, text, fnt, fill, tracking=0, anchor="l"):
    """draw text with letter spacing; anchor l/m on x; y is the top."""
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    tw = sum(widths) + tracking * (len(text) - 1)
    x, y = xy
    if anchor == "m":
        x -= tw / 2
    elif anchor == "r":
        x -= tw
    for ch, w_ in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += w_ + tracking
    return tw


def text_size(draw, text, fnt, tracking=0):
    return sum(draw.textlength(ch, font=fnt) for ch in text) + tracking * (len(text) - 1)


def draw_texts(frame, t, texts):
    active = [x for x in texts if x["t"] <= t < x["t"] + x["dur"]]
    if not active:
        return frame
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dim = 1.0
    for x in active:
        u = t - x["t"]
        d = x["dur"]
        out_a = 1 - ease((u - (d - 0.4)) / 0.4)
        k = x["kind"]
        if k in ("chapter", "title"):
            dim = min(dim, 1 - 0.45 * min(ease(u / 0.5), out_a))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dr = ImageDraw.Draw(layer)
        glow = False
        if k == "lower":
            a = out_a
            fx = 110
            fy = 830
            ft = font("playfair", 58, "Bold")
            fs = font("playfair", 30, "Italic") if False else font("oswald", 28, "Light")
            lw = ease_out(u / 0.5)
            tw = max(text_size(dr, x["text"], ft, 4), text_size(dr, x["sub"].upper(), fs, 5))
            dr.rectangle([fx, fy - 18, fx + (tw + 20) * lw, fy - 14], fill=RED + (int(255 * a),))
            ta = ease((u - 0.2) / 0.5) * a
            oy = 18 * (1 - ease_out((u - 0.2) / 0.6))
            tracked(dr, (fx, fy + oy - 4), x["text"], ft, WHITE + (int(255 * ta),), 4)
            sa = ease((u - 0.5) / 0.5) * a
            tracked(dr, (fx + 2, fy + 76 + oy * 0.5), x["sub"].upper(), fs, (200, 195, 185, int(230 * sa)), 5)
            glow = True
        elif k == "date":
            ft = font("type", 84)
            fs = font("type", 46)
            n = int(len(x["text"]) * min(1, u / 0.9))
            fl = 1.0 if u > 1.2 else (0.75 + 0.25 * ((int(u * 30) % 3) > 0))
            a = out_a * fl
            dr.text((120, 120), x["text"][:n] + ("_" if u < 1.0 and int(u * 6) % 2 == 0 else ""), font=ft,
                    fill=RED + (int(255 * a),))
            if x.get("sub"):
                ns = int(len(x["sub"]) * min(1, max(0, (u - 1.0) / 0.6)))
                dr.text((124, 220), x["sub"][:ns], font=fs, fill=WHITE + (int(235 * a),))
            glow = True
        elif k == "pop":
            col = {"red": (225, 38, 38), "white": WHITE, "green": GREEN}[x["color"]]
            ft = font("oswald", x["size"], "Bold")
            lines = x["text"].split("\n")
            sc = 1 + 0.35 * (1 - back_out(u / 0.28))
            a = min(1, u / 0.12) * out_a
            lh = x["size"] * 1.18
            tot_h = lh * len(lines)
            sub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(sub)
            for i, ln in enumerate(lines):
                y = H / 2 - tot_h / 2 + i * lh
                tracked(sd, (W / 2 + 6, y + 6), ln, ft, (0, 0, 0, int(160 * a)), 3, "m")
                tracked(sd, (W / 2, y), ln, ft, col + (int(255 * a),), 3, "m")
            if abs(sc - 1) > 0.002:
                sub = sub.resize((int(W * sc), int(H * sc)), Image.BILINEAR)
                ox, oy = (sub.width - W) // 2, (sub.height - H) // 2
                sub = sub.crop((ox, oy, ox + W, oy + H))
            jx = int(6 * math.sin(u * 60) * max(0, 1 - u / 0.3))
            layer.alpha_composite(sub, (jx, 0))
            glow = x["color"] == "red"
        elif k == "chapter":
            a = min(ease(u / 0.6), out_a)
            fc = font("oswald", 30, "Regular")
            ft = font("playfair", 80, "Bold")
            tr = 14 + 8 * ease_out(u / 2.0)
            tracked(dr, (W / 2, H / 2 - 90), f"CHAPTER {x['n']}", fc, RED + (int(255 * a),), int(tr), "m")
            tw = text_size(dr, x["text"], ft, 3)
            tracked(dr, (W / 2, H / 2 - 40), x["text"], ft, WHITE + (int(255 * a),), 3, "m")
            lw = (tw / 2 + 40) * ease_out(u / 0.8)
            dr.rectangle([W / 2 - lw, H / 2 + 75, W / 2 + lw, H / 2 + 77], fill=WHITE + (int(160 * a),))
        elif k == "title":
            a = min(ease(u / 0.9), out_a)
            ft = font("playfair", 120, "Black")
            fs = font("oswald", 34, "Regular")
            lines = x["text"].split("\n")
            for i, ln in enumerate(lines):
                tr = 2 + 10 * (1 - ease_out(u / 3.0))
                tracked(dr, (W / 2 + 5, H / 2 - 170 + i * 140 + 5), ln, ft, (0, 0, 0, int(140 * a)), int(tr), "m")
                tracked(dr, (W / 2, H / 2 - 170 + i * 140), ln, ft, WHITE + (int(255 * a),), int(tr), "m")
            sa = min(ease((u - 0.8) / 0.8), out_a)
            tracked(dr, (W / 2, H / 2 + 135), x["sub"], fs, RED + (int(255 * sa),), 16, "m")
            dr.rectangle([W / 2 - 300 * sa, H / 2 + 120, W / 2 + 300 * sa, H / 2 + 122], fill=WHITE + (int(150 * sa),))
        elif k == "callout":
            a = out_a
            px, py = x["x"] * W, x["y"] * H
            tx, ty = (x["tx"] or x["x"] + 0.12) * W, (x["ty"] or x["y"] - 0.15) * H
            r = 26 + 6 * math.sin(u * 5)
            ra = ease(u / 0.3) * a
            dr.ellipse([px - r, py - r, px + r, py + r], outline=RED + (int(255 * ra),), width=4)
            lk = ease_out((u - 0.2) / 0.5)
            lx, ly = px + (tx - px) * lk, py + (ty - py) * lk
            dr.line([px, py, lx, ly], fill=RED + (int(255 * ra),), width=3)
            if u > 0.6:
                ft = font("oswald", 40, "Medium")
                ba = ease((u - 0.6) / 0.3) * a
                tw = text_size(dr, x["text"], ft, 3)
                dr.rectangle([tx, ty - 34, tx + tw + 30, ty + 30], fill=(15, 15, 15, int(200 * ba)))
                dr.rectangle([tx, ty - 34, tx + 6, ty + 30], fill=RED + (int(255 * ba),))
                tracked(dr, (tx + 18, ty - 30), x["text"], ft, WHITE + (int(255 * ba),), 3)
        if glow:
            g = layer.filter(ImageFilter.GaussianBlur(10))
            canvas.alpha_composite(g)
        canvas.alpha_composite(layer)
    f = frame.astype(np.float32) * dim
    arr = np.asarray(canvas).astype(np.float32)
    a = arr[..., 3:4] / 255.0
    f = f * (1 - a) + arr[..., :3] * a
    return np.clip(f, 0, 255).astype(np.uint8)


# ================================================================== shake
def shake_at(t, quakes):
    amp = 0.0
    for q in quakes:
        u = t - q["t"]
        if 0 <= u < q["dur"]:
            att = min(1.0, u / 0.12)
            amp += q["amp"] * att * math.exp(-u * q["decay"] / max(q["dur"], 0.1) * 2.5)
    return amp


def apply_shake(frame, t, amp, seed=0):
    if amp < 0.02:
        return frame
    ox = amp * (24 * math.sin(t * 47) + 14 * math.sin(t * 83 + 1.1))
    oy = amp * (34 * math.sin(t * 61 + 0.3) + 20 * math.sin(t * 97 + 2.0))  # vertical dominates (Feb 2011)
    rot = amp * 0.6 * math.sin(t * 29)
    sc = 1.04 + 0.03 * min(amp, 1.5)
    M = cv2.getRotationMatrix2D((W / 2, H / 2), rot, sc)
    M[0, 2] += ox
    M[1, 2] += oy
    a = cv2.warpAffine(frame, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    M2 = M.copy()
    M2[0, 2] -= ox * 0.35
    M2[1, 2] -= oy * 0.35
    b = cv2.warpAffine(frame, M2, (W, H), borderMode=cv2.BORDER_REFLECT)
    out = cv2.addWeighted(a, 0.55, b, 0.45, 0)
    if amp > 0.5:  # chromatic aberration on violent shakes
        sh = int(min(10, amp * 6))
        out[..., 0] = np.roll(out[..., 0], sh, axis=1)
        out[..., 2] = np.roll(out[..., 2], -sh, axis=1)
    return out


# ================================================================== frame
class Renderer:
    def __init__(self, ev):
        self.ev = ev
        self.shots = ev["shots"]
        self.texts = ev["texts"]
        self.quakes = ev["quakes"]

    def shot_at(self, t):
        for i, s in enumerate(self.shots):
            if s["start"] <= t < s["end"]:
                return i, s
        return len(self.shots) - 1, self.shots[-1]

    def render_shot(self, s, t):
        u, d = t - s["start"], s["end"] - s["start"]
        if s["kind"] == "plate":
            f = render_plate(s, u, d, t)
            if s["grade"] in ("disaster",):
                f = dust_layer(f, t, hash(s["name"]) % 1000, 1.0, fall=shake_at(t, self.quakes) > 0.3)
            if s["grade"] in ("dawn", "hope", "dusk"):
                f = light_leak(f, t, 0.18)
            return f
        return gfx2d.render(s, u, d, t)

    def frame(self, t):
        i, s = self.shot_at(t)
        f = self.render_shot(s, t)
        # soft dissolves into calm grades
        if s["kind"] == "plate" and s["grade"] in ("hope", "dusk", "mourn", "dawn") and i > 0:
            u = t - s["start"]
            if u < 0.5:
                p = self.shots[i - 1]
                g = self.render_shot(p, t)
                f = cv2.addWeighted(f, ease(u / 0.5), g, 1 - ease(u / 0.5), 0)
        u = t - s["start"]
        if s.get("flash") and u < 0.35:
            k = 1 - u / 0.35
            f = cv2.addWeighted(f, 1 - k * 0.9, np.full_like(f, 255), k * 0.9, 0)
        amp = shake_at(t, self.quakes)
        f = apply_shake(f, t, amp)
        f = draw_texts(f, t, self.texts)
        # finishing: vignette, grain, global fades
        ff = f.astype(np.float32) * VIGNETTE
        g = GRAIN[int(t * FPS) % len(GRAIN)]
        ff += g[..., None] * (7.0 if s.get("grade") != "memory" else 11.0)
        fade = min(1.0, t / 0.8) * min(1.0, (self.ev["total"] - t) / 3.0)
        if s.get("fade_out"):
            fade *= 1 - 0.85 * ease((u - (s["end"] - s["start"] - 3.0)) / 3.0)
        ff *= fade
        return np.clip(ff, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", action="store_true")
    ap.add_argument("--part", type=int, default=None)
    ap.add_argument("--parts", type=int, default=4)
    ap.add_argument("--still", type=float, nargs="*")
    ap.add_argument("--range", type=float, nargs=2)
    ap.add_argument("--fps", type=int, default=FPS)
    args = ap.parse_args()
    ev = resolve()
    os.makedirs(BUILD, exist_ok=True)
    if args.events:
        json.dump(ev, open(os.path.join(BUILD, "events.json"), "w"), indent=1)
        print("shots", len(ev["shots"]), "texts", len(ev["texts"]), "total", ev["total"])
        return
    R = Renderer(ev)
    if args.still:
        for t in args.still:
            Image.fromarray(R.frame(t)).save(os.path.join(BUILD, f"still_{t:.1f}.jpg"), quality=88)
        return
    fps = args.fps
    nframes = int(ev["total"] * fps)
    if args.range:
        a, b = int(args.range[0] * fps), int(args.range[1] * fps)
        out = os.path.join(BUILD, "range.mp4")
    else:
        per = math.ceil(nframes / args.parts)
        a, b = args.part * per, min(nframes, (args.part + 1) * per)
        out = os.path.join(BUILD, f"part{args.part}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    import time
    t0 = time.time()
    for fi in range(a, b):
        p.stdin.write(R.frame(fi / fps).tobytes())
        if (fi - a) % 300 == 0:
            print(f"[part {args.part}] {fi - a}/{b - a} {time.time() - t0:.0f}s", flush=True)
    p.stdin.close()
    p.wait()
    print("done", out)


if __name__ == "__main__":
    main()
