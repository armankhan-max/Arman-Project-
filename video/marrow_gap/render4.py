import json, math, sys, subprocess, random, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1280, 720, 24
D = os.path.dirname(os.path.abspath(__file__))
F_BEBAS = D + "/../work/fonts/7fb78b.ttf"; F_OSW = D + "/../work/fonts/092e85.ttf"
F_PLAY = D + "/../work/fonts/b8a6dc.ttf"; F_TYPE = D + "/../work/fonts/c33104.ttf"
GOLD = (212, 170, 92); CREAM = (236, 230, 216)
TR = json.load(open(D + "/transcript.json"))
SEGSTARTS = [s["s"] for s in TR]

_imgs = {}
VD = D + "/../stock/clips/"
VLEN = {}
def vk(sh, t):
    k = sh["k"]
    if not k.startswith("V:"): return k
    c = k[2:]
    if c not in VLEN: VLEN[c] = len(os.listdir(VD + c))
    n = VLEN[c]; i = int(max(0, t - sh["s"]) * FPS); per = 2 * n - 2
    i = i % per; i = i if i < n else per - i
    return f"V:{c}/{i + 1:04d}"
def IMG(k):
    if k.startswith("V:"): return Image.open(VD + k[2:] + ".jpg").convert("RGB")
    if k not in _imgs:
        p_ = f"{D}/img/{k}.jpg"
        if not os.path.exists(p_): p_ = f"{D}/../v3/img/{k}.jpg"
        if not os.path.exists(p_): p_ = f"{D}/../work/img/{k}.jpg"
        _imgs[k] = Image.open(p_).convert("RGB")
    return _imgs[k]
_fonts = {}
def FONT(p, s):
    if (p, s) not in _fonts: _fonts[(p, s)] = ImageFont.truetype(p, s)
    return _fonts[(p, s)]

def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)

import sys as _s; _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data4 import *
# ------------------------------------------------------------ shot list
def build_shots():
    rng = random.Random(7)
    bounds = [r[0] for r in R] + [DUR]
    shots = []; use = {}
    for i, (s, pool, steam, pace) in enumerate(R):
        e = bounds[i + 1]
        cuts = [s]
        t = s
        while e - t > pace * 1.5:
            cands = [x for x in SEGSTARTS if t + pace * 0.75 <= x <= t + pace * 1.3 and x < e - pace * 0.6]
            nt = min(cands, key=lambda x: abs(x - (t + pace))) if cands else t + pace
            cuts.append(nt); t = nt
        cuts.append(e)
        for j in range(len(cuts) - 1):
            k = pool[j % len(pool)]
            n = use.get(k, 0); use[k] = n + 1
            mv = rng.choice(["in", "out", "pl", "pr", "in", "out"])
            if k.startswith("V:") or k.startswith("c_g_"): z0, fx, fy = 1.0, 0.5, 0.5
            elif n == 0: z0, fx, fy = 1.0, 0.5, 0.5
            else: z0 = 1.12 + min(n, 5) * 0.05; fx, fy = rng.uniform(.3, .7), rng.uniform(.3, .65)
            shots.append(dict(s=cuts[j], e=cuts[j + 1], k=k, mv=mv, z=z0, fx=fx, fy=fy, steam=steam))
    return shots
SHOTS = build_shots()

def crop_rect(sh, t):
    d = sh["e"] - sh["s"]; p = (t - sh["s"]) / max(d, .01); p = min(max(p, 0), 1.2)
    z = sh["z"]; mv = sh["mv"]
    if mv == "in": zz = z * (1 + 0.14 * p); cx, cy = sh["fx"], sh["fy"]
    elif mv == "out": zz = z * (1.14 - 0.14 * p); cx, cy = sh["fx"], sh["fy"]
    else:
        zz = z * 1.12; a = 0.5 - 0.08 + 0.16 * p if mv == "pr" else 0.5 + 0.08 - 0.16 * p
        cx, cy = a + (sh["fx"] - .5), sh["fy"]
    cw, ch = 1600 / zz, 900 / zz
    x0 = min(max(cx * 1600 - cw / 2, 0), 1600 - cw); y0 = min(max(cy * 900 - ch / 2, 0), 900 - ch)
    return x0, y0, cw, ch

def render_img(k, rect, jx=0, jy=0):
    x0, y0, cw, ch = rect
    sx, sy = cw / W, ch / H
    im = IMG(k).transform((W, H), Image.AFFINE, (sx, 0, x0 + jx, 0, sy, y0 + jy), resample=Image.BILINEAR)
    return np.asarray(im).astype(np.float32)

# ------------------------------------------------------------ textures
rs = np.random.default_rng(1)
GRAIN = []
for i in range(24):
    g = rs.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    g = np.asarray(Image.fromarray((g * 30 + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) - 128
    GRAIN.append(g * 0.30)
def make_smoke():
    acc = np.zeros((H * 2, W), np.float32)
    for sc, wt in [(8, 1.0), (16, .6), (32, .35), (64, .2)]:
        n = rs.random((H * 2 // (256 // sc) + 2, W // (256 // sc) + 2)).astype(np.float32)
        im = Image.fromarray((n * 255).astype(np.uint8)).resize((W, H * 2), Image.BICUBIC)
        acc += np.asarray(im).astype(np.float32) / 255 * wt
    acc = acc / acc.max(); acc = np.clip((acc - 0.45) * 2.2, 0, 1)
    return np.asarray(Image.fromarray((acc * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18))).astype(np.float32) / 255
SMOKE = make_smoke()
yy, xx = np.mgrid[0:H, 0:W]
VIG = 1.12 * (1 - 0.26 * (((xx / W - .5) ** 2) * 1.2 + ((yy / H - .5) ** 2) * 1.8) * 2.2).clip(0.5, 1).astype(np.float32)[..., None]

_th = {}
def _thumb(k, w, h):
    if (k, w) not in _th: _th[(k, w)] = np.asarray(IMG(k).resize((w, h), Image.BILINEAR)).astype(np.float32)
    return _th[(k, w)]

def dark_bg(k, t, dim=0.35, blur=True):
    if blur and k + "_b" not in _imgs: _imgs[k + "_b"] = IMG(k).filter(ImageFilter.GaussianBlur(4))
    a = render_img(k + "_b" if blur else k, (100 + 30 * math.sin(t * .05), 60, 1400, 787.5))
    return a * dim

# ------------------------------------------------------------ text helpers
def tlayer(size=(W, H)): return Image.new("RGBA", size, (0, 0, 0, 0))
def comp(base, layer, alpha=1.0):
    bb = layer.getbbox()
    if not bb or alpha <= 0: return base
    x0, y0, x1, y1 = bb
    a = np.asarray(layer.crop(bb)).astype(np.float32)
    al = a[..., 3:4] * (alpha / 255)
    reg = base[y0:y1, x0:x1]
    base[y0:y1, x0:x1] = reg + (a[..., :3] - reg) * al
    return base
def shadow_text(d, xy, txt, font, fill, anchor="la", sh=3):
    d.text((xy[0] + sh, xy[1] + sh), txt, font=font, fill=(0, 0, 0, 170), anchor=anchor)
    d.text(xy, txt, font=font, fill=fill, anchor=anchor)

PAPER = (0.88 + 0.12 * np.asarray(Image.fromarray((np.random.default_rng(3).random((60, 100)) * 255).astype(np.uint8)).resize((940, 545), Image.BICUBIC)).astype(np.float32)[..., None] / 255)
_g = np.linspace(0, 1, H)[:, None, None].astype(np.float32)
GR1 = np.clip((_g - 0.62) * 2.6, 0, 1); GR2 = np.clip((_g - 0.55) * 2.2, 0, 1); GR3 = np.clip((_g - 0.7) * 3, 0, 1)
_cache = {}
def ov_layer(o):
    key = id(o)
    if key in _cache: return _cache[key]
    s, e, kind, dat = o
    L = tlayer(); d = ImageDraw.Draw(L); extra = {}
    if kind == "lower":
        fa = FONT(F_OSW, 44); fb = FONT(F_PLAY, 30)
        d.rectangle((90, 560, 118, 565), fill=GOLD + (255,))
        shadow_text(d, (134, 538), dat["a"], fa, CREAM + (255,))
        shadow_text(d, (136, 600), dat["b"], fb, (236, 228, 210, 255), sh=2)
        extra["w"] = 160 + max(fa.getlength(dat["a"]), fb.getlength(dat["b"]))
    elif kind == "chapter":
        fn = FONT(F_OSW, 24); ft = FONT(F_BEBAS, 96)
        shadow_text(d, (W / 2, 300), "·  " + dat["n"] + "  ·", fn, GOLD + (255,), "mm", 2)
        shadow_text(d, (W / 2, 372), dat["t"], ft, CREAM + (255,), "mm", 4)
        extra["uw"] = ft.getlength(dat["t"])
    elif kind == "loc":
        fa = FONT(F_BEBAS, 64); fb = FONT(F_OSW, 26)
        shadow_text(d, (90, 520), dat["a"], fa, CREAM + (255,))
        shadow_text(d, (92, 600), dat["b"], fb, GOLD + (255,), sh=2)
        extra["w"] = fa.getlength(dat["a"]) + 20
    elif kind == "big":
        ft = FONT(F_BEBAS, 120)
        shadow_text(d, (W / 2, H / 2), dat["t"], ft, CREAM + (255,), "mm", 5)
        extra["uw"] = ft.getlength(dat["t"])
    elif kind == "cold":
        ft = FONT(F_BEBAS, 150 if len(dat["t"]) < 10 else 96)
        shadow_text(d, (W / 2, H / 2), dat["t"], ft, CREAM + (255,), "mm", 5)
        extra["uw"] = ft.getlength(dat["t"])
    elif kind == "quote":
        fq = FONT(F_PLAY, 46); fb = FONT(F_OSW, 22)
        lines = dat["t"].split("\n"); y = H / 2 - (len(lines) - 1) * 32 - (14 if dat["b"] else 0)
        for ln in lines:
            shadow_text(d, (W / 2, y), ln, fq, CREAM + (255,), "mm", 3); y += 64
        if dat["b"]:
            d.rectangle((W / 2 - 20, y - 8, W / 2 + 20, y - 5), fill=GOLD + (255,))
            shadow_text(d, (W / 2, y + 22), dat["b"], fb, GOLD + (255,), "mm", 2)
    elif kind == "type":
        txt = dat["t"]; sz = 34 if len(txt) < 40 else 26
        f = FONT(F_TYPE, sz); extra["f"] = f
        if dat["pos"] == "c":
            # wrap
            words = txt.split(); lines = [""]
            for wd in words:
                if f.getlength(lines[-1] + " " + wd) > 980: lines.append(wd)
                else: lines[-1] = (lines[-1] + " " + wd).strip()
            extra["lines"] = lines
        else: extra["lines"] = [txt]
    _cache[key] = (L, extra)
    return _cache[key]

def apply_overlay(fr, o, t):
    s, e, kind, dat = o
    L, ex = ov_layer(o)
    p = t - s; rem = e - t
    fade = min(1, p / 0.5, rem / 0.5)
    if kind == "lower":
        a = ease(p / 0.7) * min(1, rem / 0.6)
        wv = int(ex["w"] * ease(p / 0.9)) + 90
        M = np.zeros((1, W, 1), np.float32); M[:, :min(W, wv)] = 1
        dx = int((1 - ease(p / 0.7)) * -30)
        Ls = L if dx == 0 else L.transform(L.size, Image.AFFINE, (1, 0, -dx, 0, 1, 0))
        arr = np.asarray(Ls).astype(np.float32); al = arr[..., 3:4] / 255 * a * M
        # dark gradient behind
        fr[440:] *= (1 - GR1[440:] * 0.55 * a)
        return fr * (1 - al) + arr[..., :3] * al
    if kind in ("chapter", "big", "cold"):
        dim = 0.55 if kind == "chapter" else 0.4
        fr = fr * (1 - dim * fade)
        sc = 1.0 + 0.03 * (p / (e - s))
        Ls = L.resize((int(W * sc), int(H * sc)), Image.BILINEAR).crop((int(W * (sc - 1) / 2), int(H * (sc - 1) / 2), int(W * (sc - 1) / 2) + W, int(H * (sc - 1) / 2) + H)) if kind != "chapter" else L
        fr = comp(fr, Ls, fade)
        uw = ex["uw"] * ease((p - 0.3) / 0.9)
        if uw > 2:
            y = 430 if kind == "chapter" else H // 2 + (95 if kind == "cold" and ex["uw"] < 700 else 70)
            x0 = int(W / 2 - ex["uw"] / 2)
            fr[y:y + 4, x0:x0 + int(uw)] = fr[y:y + 4, x0:x0 + int(uw)] * (1 - fade) + np.array(GOLD, np.float32) * fade
        return fr
    if kind == "loc":
        a = fade
        wv = int(ex["w"] * ease(p / 1.0)) + 90
        M = np.zeros((1, W, 1), np.float32); M[:, :wv] = 1
        arr = np.asarray(L).astype(np.float32); al = arr[..., 3:4] / 255 * a * M
        fr[390:] *= (1 - GR2[390:] * 0.6 * a)
        uw = int(ex["w"] * ease((p - .4) / 1.0))
        if uw > 2: fr[592:595, 90:90 + uw] = fr[592:595, 90:90 + uw] * (1 - a) + np.array(GOLD, np.float32) * a
        return fr * (1 - al) + arr[..., :3] * al
    if kind == "quote":
        fr = fr * (1 - 0.6 * fade)
        fq = FONT(F_PLAY, 46); fb = FONT(F_OSW, 22)
        lines = dat["t"].split("\n"); nw = sum(len(l.split()) for l in lines)
        rate = max(nw / 1.8, 6.0); shown = p * rate
        Lq = tlayer(); d = ImageDraw.Draw(Lq)
        y = H / 2 - (len(lines) - 1) * 32 - (14 if dat["b"] else 0); c = 0
        for ln in lines:
            ws = ln.split(); full = fq.getlength(ln); x = W / 2 - full / 2
            for w_ in ws:
                a_ = min(1, max(0, shown - c)); c += 1
                if a_ > 0:
                    yo = (1 - ease(a_)) * 10
                    shadow_text(d, (x, y + yo), w_, fq, CREAM + (int(255 * a_),), "lm", 3)
                x += fq.getlength(w_ + " ")
            y += 64
        if dat["b"]:
            ab = ease((shown - nw) / 6)
            if ab > 0:
                d.rectangle((W / 2 - 20, y - 8, W / 2 + 20, y - 5), fill=GOLD + (int(255 * ab),))
                shadow_text(d, (W / 2, y + 22), dat["b"], fb, GOLD + (int(255 * ab),), "mm", 2)
        return comp(fr, Lq, fade)
    if kind == "type":
        f = ex["f"]; lines = ex["lines"]
        n = int(p * 20)  # chars revealed
        Lt = tlayer(); d = ImageDraw.Draw(Lt)
        if dat["pos"] == "bl":
            fr[500:] *= (1 - GR3[500:] * 0.5 * fade)
            txt = lines[0][:n]
            shadow_text(d, (90, 630), txt, f, (232, 226, 210, 255), sh=2)
            if n < len(lines[0]) and int(t * 3) % 2 == 0:
                x = 90 + f.getlength(txt); d.rectangle((x + 3, 606, x + 15, 640), fill=GOLD + (255,))
        else:
            fr = fr * (1 - 0.5 * fade)
            y = H / 2 - (len(lines) - 1) * 26; c = n
            for ln in lines:
                shadow_text(d, (W / 2 - f.getlength(ln) / 2, y), ln[:max(0, c)], f, (232, 226, 210, 255), "lm", 2)
                c -= len(ln); y += 52
        return comp(fr, Lt, fade)
    return fr

# ------------------------------------------------------------ graphics scenes
def gfx_frame(g, t):
    s, e, kind, dat = g
    p = t - s
    if kind == "thermo":
        fr = dark_bg("dae0d14e", t, 0.3)
        L = tlayer(); d = ImageDraw.Draw(L)
        for i, (lab, val, x) in enumerate([("THE ROCK", 118, 420), ("THE AIR ON THE STAIR", 58, 860)]):
            d.rounded_rectangle((x - 22, 140, x + 22, 560), 22, outline=CREAM + (220,), width=3)
            d.ellipse((x - 38, 540, x + 38, 616), outline=CREAM + (220,), width=3)
            col = (165, 85, 62, 255) if i == 0 else (105, 135, 160, 255)
            d.ellipse((x - 30, 548, x + 30, 608), fill=col)
            prog = ease((p - 0.4 - i * 1.6) / 2.2); v = val * prog
            top = 548 - (v / 130) * 400
            d.rectangle((x - 10, top, x + 10, 560), fill=col)
            for tk in range(0, 131, 10):
                yy_ = 548 - tk / 130 * 400; d.line((x + 26, yy_, x + 40, yy_), fill=CREAM + (160,), width=2)
            shadow_text(d, (x, 100), lab, FONT(F_OSW, 28), GOLD + (255,), "mm", 2)
            shadow_text(d, (x + 70, top), f"{int(round(v))}°F", FONT(F_BEBAS, 72), CREAM + (255,), "lm", 3)
        if p > 5.5:
            a = min(1, (p - 5.5) / .6)
            shadow_text(d, (W / 2, 670), "THE HOTTEST MINE ON THE RIDGE · THE ONLY COLD STAIR", FONT(F_OSW, 26), (236, 230, 216, int(255 * a)), "mm", 2)
        return comp(fr, L)
    if kind == "title":
        fr = dark_bg(dat["bg"], t, 0.42, blur=False)
        L = tlayer(); d = ImageDraw.Draw(L)
        sc = 1 + 0.02 * p
        ft = FONT(F_BEBAS, int(118 * sc))
        a = ease(p / 1.2)
        shadow_text(d, (W / 2, H / 2 - 20), dat["t"], ft, (236, 230, 216, int(255 * a)), "mm", 5)
        shadow_text(d, (W / 2, H / 2 + 80), dat["s"], FONT(F_OSW, 24), GOLD + (int(255 * ease((p - 1.2) / 1)),), "mm", 2)
        fr = comp(fr, L)
        uw = int(ft.getlength(dat["t"]) * ease((p - 0.6) / 1.2)); x0 = int(W / 2 - ft.getlength(dat["t"]) / 2)
        if uw > 2: fr[H // 2 + 42:H // 2 + 46, x0:x0 + uw] = GOLD
        return fr
    if kind == "grid":
        fr = np.full((H, W, 3), 14, np.float32)
        for gx in range(0, W, 125): fr[:, gx:gx + 1] = 70
        for gy in range(0, H, 125): fr[gy:gy + 1, :] = 70
        names = dat["names"]; n = len(names)
        pw, ph = 264, 149; gap = 30
        total = n * pw + (n - 1) * gap
        off = 80 - p * 18
        for i, (k, a, b) in enumerate(names):
            ap = ease((p - i * 0.6) / 0.8)
            if ap <= 0: continue
            x = int(W / 2 - total / 2 + i * (pw + gap) + off * 0.5 * (i - 1.5) / 1.5)
            y = int(285 + (1 - ap) * 40)
            im = _thumb(k, pw, ph)
            reg = fr[y - 6:y + ph + 6, x - 6:x + pw + 6]
            if reg.shape[0] != ph + 12 or reg.shape[1] != pw + 12: continue
            gold = np.array([190, 140, 80], np.float32)
            reg[:] = reg * (1 - ap) + gold * ap
            reg[6:6 + ph, 6:6 + pw] = reg[6:6 + ph, 6:6 + pw] * (1 - ap) + im * ap
            L = tlayer(); d = ImageDraw.Draw(L)
            shadow_text(d, (x + pw / 2, y + ph + 40), a, FONT(F_BEBAS, 40), CREAM + (int(255 * ap),), "mm", 2)
            shadow_text(d, (x + pw / 2, y + ph + 74), b, FONT(F_PLAY, 22), GOLD + (int(255 * ap),), "mm", 2)
            fr = comp(fr, L)
        return fr
    if kind == "stats":
        fr = dark_bg("04b91edb", t, 0.32)
        L = tlayer(); d = ImageDraw.Draw(L)
        items = [(0, "52", "STEPS · COUNTED TWICE"), (3.5, "156 FT", "STRAIGHT DOWN · NO TURNS"), (18.0, "36 IN", "EVERY RISER"), (20.7, "60 IN", "EVERY TREAD"), (25.0, "0.5 IN", "MAX ERROR · NINE STEPS MEASURED")]
        y = 110
        for (ts, big, small) in items:
            a = ease((p - ts) / 0.8)
            if a > 0:
                shadow_text(d, (330 - (1 - a) * 30, y), big, FONT(F_BEBAS, 84), CREAM + (int(255 * a),), "ra", 4)
                shadow_text(d, (370, y + 30), small, FONT(F_OSW, 30), GOLD + (int(255 * a),), "la", 2)
            y += 112
        return comp(fr, L)
    if kind == "formula":
        fr = dark_bg("4252c9d9", t, 0.28)
        L = tlayer(); d = ImageDraw.Draw(L)
        rows = [(0, F_PLAY, 34, "A rule for stairs - written down 200 years ago", GOLD),
                (7.2, F_BEBAS, 76, "2 × RISER  +  TREAD  =  STRIDE", CREAM),
                (10.0, F_OSW, 30, "an ordinary man  =  about 25 inches", (210, 204, 190)),
                (14.7, F_BEBAS, 76, "2 × 36  +  60  =  132 IN", CREAM),
                (19.9, F_BEBAS, 76, "A STRIDE OF 11 FEET", CREAM),
                (23.6, F_BEBAS, 120, "= 30 FEET TALL", (240, 205, 140))]
        y = 95
        for ts, fp, sz, txt, col in rows:
            a = ease((p - ts) / 0.9)
            if a > 0:
                shadow_text(d, (W / 2, y + (1 - a) * 15), txt, FONT(fp, sz), col + (int(255 * a),), "mm", 3)
            y += 92 if sz < 100 else 0
        fr = comp(fr, L)
        if p > 31.6:  # box around it
            a = ease((p - 31.6) / 0.8); bw = FONT(F_BEBAS, 120).getlength("= 30 FEET TALL") / 2 + 30
            x0, x1, y0, y1 = int(W / 2 - bw), int(W / 2 + bw), 600, 720 - 6
            yc = 555 + 92 * 0
            y0, y1 = 95 + 92 * 5 - 70, 95 + 92 * 5 + 70
            g = np.array(GOLD, np.float32)
            fr[y0:y0 + 3, x0:x1] = fr[y0:y0 + 3, x0:x1] * (1 - a) + g * a; fr[y1:y1 + 3, x0:x1] = fr[y1:y1 + 3, x0:x1] * (1 - a) + g * a
            fr[y0:y1, x0:x0 + 3] = fr[y0:y1, x0:x0 + 3] * (1 - a) + g * a; fr[y0:y1, x1:x1 + 3] = fr[y0:y1, x1:x1 + 3] * (1 - a) + g * a
        return fr
    if kind == "sump":
        fr = dark_bg("5e4f424e", t, 0.4)
        L = tlayer(); d = ImageDraw.Draw(L)
        x0, x1, ytop, ybot = 470, 810, 120, 620
        d.rectangle((x0, ytop, x1, ybot), outline=CREAM + (200,), width=3)
        for ft in range(0, 41, 5):
            yv = ybot - ft / 40 * (ybot - ytop); d.line((x1, yv, x1 + 18, yv), fill=CREAM + (180,), width=2)
            d.text((x1 + 26, yv), f"{ft} FT", font=FONT(F_OSW, 20), fill=CREAM + (200,), anchor="lm")
        # level: start 34, drop 19 over seconds 3..8, recover 18..24
        lv = 34 - 19 * ease((p - 3) / 5) + 19 * ease((p - 18.5) / 6)
        yv = ybot - lv / 40 * (ybot - ytop)
        d.rectangle((x0 + 3, yv, x1 - 3, ybot - 3), fill=(80, 95, 110, 210))
        d.line((x0 + 3, yv, x1 - 3, yv), fill=(200, 220, 235, 255), width=3)
        shadow_text(d, (x0 - 30, 160), "LOWEST SUMP", FONT(F_OSW, 28), GOLD + (255,), "ra", 2)
        shadow_text(d, (x0 - 30, 200), "~2:00 A.M.", FONT(F_BEBAS, 56), CREAM + (255,), "ra", 3)
        shadow_text(d, (x0 - 30, 260), "ENGINES OFF", FONT(F_OSW, 24), (210, 204, 190, 255), "ra", 2)
        dropped = 34 - lv
        if p > 3: shadow_text(d, (x0 - 30, 420), f"-{dropped:0.0f} FT", FONT(F_BEBAS, 96), (240, 205, 140, 255), "ra", 4)
        if p > 8.5: shadow_text(d, (x0 - 30, 490), "IN ABOUT ONE HOUR", FONT(F_OSW, 24), CREAM + (255,), "ra", 2)
        return comp(fr, L)
    if kind == "ledger":
        fr = dark_bg(N["notebookwarm"], t, 0.30)
        px0, py0, px1, py1 = 170, 95, 1110, 640
        g = np.array([226, 216, 192], np.float32)
        fr[py0:py1, px0:px1] = fr[py0:py1, px0:px1] * 0.08 + g * 0.92 * PAPER
        for yl in range(py0 + 120, py1 - 20, 62): fr[yl:yl + 2, px0 + 20:px1 - 20] = fr[yl:yl + 2, px0 + 20:px1 - 20] * 0.55 + 90
        fr[py0:py1, px0 + 90:px0 + 92] = fr[py0:py1, px0 + 90:px0 + 92] * 0.5 + 70
        L = tlayer(); d = ImageDraw.Draw(L)
        d.text((px0 + 110, py0 + 45), dat["h"], font=FONT(F_OSW, 24), fill=(120, 95, 60, 255))
        y = py0 + 165
        for (ts, txt, st) in dat["lines"]:
            n = int(max(0, p - ts) * 22)
            if n > 0 and txt:
                sz = 38 if st else 32
                while FONT(F_TYPE, sz).getlength(txt) > 820: sz -= 2
                f = FONT(F_TYPE, sz)
                d.text((px0 + 110, y), txt[:n], font=f, fill=(25, 22, 20, 255), anchor="ls")
                if st == 2 and n >= len(txt):
                    uw = f.getlength(txt) * ease((p - ts - len(txt) / 22) / 0.6)
                    d.line((px0 + 110, y + 8, px0 + 110 + uw, y + 8), fill=(25, 22, 20, 255), width=3)
                    d.line((px0 + 110, y + 15, px0 + 110 + uw, y + 15), fill=(25, 22, 20, 255), width=2)
                if n < len(txt) and int(t * 3) % 2 == 0:
                    x = px0 + 110 + f.getlength(txt[:n]); d.rectangle((x + 3, y - 30, x + 14, y + 4), fill=(150, 110, 60, 255))
            y += 62 if st == 0 else 76
        z = 1 + 0.035 * p / (e - s)
        fr = comp(fr, L)
        if z > 1.001:
            im = Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8)); cw, ch = W / z, H / z
            fr = np.asarray(im.transform((W, H), Image.AFFINE, (cw / W, 0, (W - cw) / 2, 0, ch / H, (H - ch) / 2), resample=Image.BILINEAR)).astype(np.float32)
        return fr
    if kind == "list":
        fr = dark_bg(N["gloves"] if "GHOST" in dat["h"] else N["micro"], t, 0.26)
        L = tlayer(); d = ImageDraw.Draw(L)
        a0 = ease(p / 0.8)
        shadow_text(d, (130, 110), dat["h"], FONT(F_OSW, 30), GOLD + (int(255 * a0),), "la", 2)
        uw = int(700 * ease((p - 0.3) / 1.0))
        if uw > 2: d.rectangle((130, 158, 130 + uw, 161), fill=GOLD + (220,))
        y = 215
        for ts, txt in dat["items"]:
            a = ease((p - ts) / 0.7)
            if a > 0:
                last = (ts == dat["items"][-1][0]) and len(dat["items"]) == 5 and "7." in txt
                f = FONT(F_TYPE, 40 if last else 34)
                col = (240, 205, 140) if last else CREAM
                shadow_text(d, (160 - (1 - a) * 30, y), txt, f, col + (int(255 * a),), "la", 3)
            y += 82
        return comp(fr, L)
    if kind == "scale":
        fr = dark_bg(dat.get("bg", N["measure"]), t, 0.25)
        L = tlayer(); d = ImageDraw.Draw(L)
        base = 640; ppf = 38.0
        for ft in range(0, 14):
            yv = base - ft * ppf
            d.line((150, yv, 1130, yv), fill=(236, 230, 216, 40 if ft % 2 else 70), width=1)
            d.text((120, yv), f"{ft}", font=FONT(F_OSW, 20), fill=CREAM + (170,), anchor="rm")
        d.text((120, base - 13.5 * ppf), "FT", font=FONT(F_OSW, 20), fill=GOLD + (220,), anchor="rm")
        def fig(cx, hft, col):
            hp = hft * ppf; top = base - hp; hr = hp * 0.065
            d.ellipse((cx - hr, top, cx + hr, top + 2 * hr), fill=col)
            sw = hp * 0.13; hipw = hp * 0.09; sy = top + 2.2 * hr; hy = base - hp * 0.47
            d.polygon([(cx - sw, sy), (cx + sw, sy), (cx + hipw, hy), (cx - hipw, hy)], fill=col)
            d.polygon([(cx - hipw, hy), (cx - 3, hy), (cx - hp * 0.025, base), (cx - hipw - hp * 0.02, base)], fill=col)
            d.polygon([(cx + 3, hy), (cx + hipw, hy), (cx + hipw + hp * 0.02, base), (cx + hp * 0.025, base)], fill=col)
            d.polygon([(cx - sw, sy), (cx - sw - hp * 0.03, sy + hp * 0.36), (cx - sw + hp * 0.02, sy + hp * 0.36), (cx - sw + hp * 0.03, sy + hp * 0.05)], fill=col)
            d.polygon([(cx + sw, sy), (cx + sw + hp * 0.03, sy + hp * 0.36), (cx + sw - hp * 0.02, sy + hp * 0.36), (cx + sw - hp * 0.03, sy + hp * 0.05)], fill=col)
        a1 = ease(p / 0.8); fig(420, 5.67, (190, 182, 165, int(230 * a1)))
        shadow_text(d, (420, base + 40), dat.get("a", "AN ORDINARY MAN · 5 FT 8 IN"), FONT(F_OSW, 24), CREAM + (int(255 * a1),), "mm", 2)
        gh = dat.get("h", 12.08) * ease((p - 1.5) / 3.0)
        if gh > 0.3:
            fig(860, gh, (120, 112, 98, 235))
            shadow_text(d, (860, base + 40), dat.get("b", "THE REARDON REMAINS"), FONT(F_OSW, 24), GOLD + (255,), "mm", 2)
            ft_ = int(gh); inch = int(round((gh - ft_) * 12)) % 12
            shadow_text(d, (1000, base - gh * ppf), f"{ft_} FT {inch} IN", FONT(F_BEBAS, 64), (240, 205, 140, 255), "lm", 3)
        if p > 8.5 and dat.get("c"):
            a2 = ease((p - 8.5) / 0.8)
            shadow_text(d, (W / 2, 60), dat.get("c", ""), FONT(F_OSW, 24), CREAM + (int(255 * a2),), "mm", 2)
        return comp(fr, L)
    if kind == "still":
        a = render_img(dat["k"], crop_rect(dict(s=s, e=e, mv="in", z=1.0, fx=0.5, fy=0.5), t))
        return a
    if kind == "ring":
        fr = dark_bg(K("standing2_0"), t, 0.25)
        L = tlayer(); d = ImageDraw.Draw(L)
        cx, cy, r = 640, 380, 230; n = 24
        for i in range(n):
            a = ease((p - 0.3 - i * 0.12) / 0.5)
            if a <= 0: continue
            th = 2 * math.pi * i / n - math.pi / 2; x, y = cx + r * math.cos(th), cy + r * math.sin(th)
            d.rounded_rectangle((x - 9, y - 14, x + 9, y + 14), 4, fill=(200, 192, 175, int(255 * a)))
        ca = ease((p - 3.6) / 1.2)
        if ca > 0:
            th0, th1 = -math.pi / 2, -math.pi / 2 + 2 * math.pi / n
            p0 = (cx + r * math.cos(th0), cy + r * math.sin(th0)); p1 = (cx + r * math.cos(th1), cy + r * math.sin(th1))
            d.line((p0, p1), fill=GOLD + (int(255 * ca),), width=4)
            shadow_text(d, (cx + 150, cy - r - 40), "66 FT  =  ONE CHAIN", FONT(F_OSW, 30), GOLD + (int(255 * ca),), "la", 2)
        ra = ease((p - 7.0) / 1.0)
        if ra > 0:
            shadow_text(d, (cx, cy), "THE RING CLOSED", FONT(F_BEBAS, 54), CREAM + (int(255 * ra),), "mm", 3)
            shadow_text(d, (cx, cy + 50), "to within an inch", FONT(F_PLAY, 30), CREAM + (int(255 * ra),), "mm", 2)
        return comp(fr, L)
    if kind == "end":
        fr = dark_bg(N["tarp"], t, 0.3, blur=False)
        L = tlayer(); d = ImageDraw.Draw(L)
        a = ease((p - 0.2) / 1.0)
        shadow_text(d, (W / 2, 300), "THE GIANT LEDGER", FONT(F_BEBAS, 110), CREAM + (int(255 * a),), "mm", 5)
        shadow_text(d, (W / 2, 385), "stories built from ledgers, letters & tin boxes", FONT(F_PLAY, 32), GOLD + (int(255 * a),), "mm", 2)
        b = ease((p - 1.2) / 0.8)
        if b > 0:
            d.rounded_rectangle((W / 2 - 150, 450, W / 2 + 150, 510), 8, fill=(170, 40, 30, int(230 * b)))
            d.text((W / 2, 480), "SUBSCRIBE", font=FONT(F_OSW, 32), fill=(255, 255, 255, int(255 * b)), anchor="mm")
        fr = comp(fr, L)
        uw = int(560 * ease((p - 0.6) / 1.0))
        if uw > 2: fr[352:355, W // 2 - 280:W // 2 - 280 + uw] = GOLD
        if rem := (e - t) < 1.5: fr = fr * max(0, (e - t) / 1.5)
        return fr
    return np.zeros((H, W, 3), np.float32)

# ------------------------------------------------------------ frame
XF = 0.45  # crossfade
def shot_at(t):
    for i, sh in enumerate(SHOTS):
        if sh["s"] <= t < sh["e"]: return i
    return len(SHOTS) - 1

def frame(fi):
    t = fi / FPS
    rng = np.random.default_rng(fi)
    jx, jy = rng.normal(0, 0.35), rng.normal(0, 0.35)  # gate weave
    g = next((g for g in GFX if g[0] <= t < g[1]), None)
    if g is not None:
        fr = gfx_frame(g, t)
        p = t - g[0]
        if p < 0.4:  # fade from shot
            i = shot_at(g[0] - 0.01); sh = SHOTS[i]
            prev = render_img(vk(sh, g[0]), crop_rect(sh, g[0]), jx, jy)
            fr = prev * (1 - p / 0.4) + fr * (p / 0.4)
    else:
        i = shot_at(t); sh = SHOTS[i]
        fr = render_img(vk(sh, t), crop_rect(sh, t), jx, jy)
        if i > 0 and t - sh["s"] < XF:
            pv = SHOTS[i - 1]
            pg = next((g for g in GFX if g[0] <= sh["s"] - 0.01 < g[1]), None)
            prev = gfx_frame(pg, sh["s"] - 0.01) if pg else render_img(vk(pv, t), crop_rect(pv, t), jx, jy)
            a = (t - sh["s"]) / XF; a = a * a * (3 - 2 * a)
            fr = prev * (1 - a) + fr * a
        if sh["steam"]:
            off = int((t * 22) % H)
            sm = SMOKE[off:off + H, :, None]
            fr = fr + sm * 70 * (0.8 + 0.2 * math.sin(t * 0.7))
    for o in OV:
        if o[0] <= t < o[1]: fr = apply_overlay(fr, o, t)
    # opening fade
    if t < 1.2: fr = fr * (t / 1.2)
    # flicker + vignette + grain
    fl = 1 + 0.035 * math.sin(fi * 1.7) * rng.random() + rng.normal(0, 0.012)
    fr = fr * fl * VIG + GRAIN[(fi * 7) % 24][..., None]
    if rng.random() < 0.02:  # occasional scratch
        x = rng.integers(0, W); fr[:, x:x + 1] += rng.uniform(-25, 30)
    if rng.random() < 0.06:
        for _ in range(rng.integers(1, 4)):
            x, y = rng.integers(10, W - 10), rng.integers(10, H - 10); r = rng.integers(1, 4)
            fr[y - r:y + r, x - r:x + r] = rng.choice([15, 220])
    return np.clip(fr, 0, 255).astype(np.uint8)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        for ts in sys.argv[2:]:
            Image.fromarray(frame(int(float(ts) * FPS))).save(f"{D}/still_{ts}.jpg", quality=88)
    else:
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-b:v", "1200k", "-maxrate", "2200k", "-bufsize", "4000k", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for fi in range(a, b):
            p.stdin.write(frame(fi).tobytes())
            if fi % 1200 == 0: print(out, fi, flush=True)
        p.stdin.close(); p.wait()
