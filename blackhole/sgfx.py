"""Cinematic dark-stickman style kit: rim-lit black-head characters, blurred sets, space, black holes.

Technique notes (why things look "pro"):
  * RIM LIGHT: every character is drawn twice. First as a flat light-blue silhouette nudged
    toward the light source, then the real character on top. That thin glowing edge separates a
    dark figure from a dark background, which is the core trick of this style.
  * DEPTH OF FIELD: sets are rendered once, Gaussian-blurred and cached. Sharp characters
    over a soft background point the viewer's eye exactly where we want it.
  * LIMITED PALETTE: navy sets, black characters, one saturated outfit color per character, and
    orange/cyan accents for the black hole and UI. Few colors = cinematic.
"""
import math
import os
import random
import sys

import skia

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video"))
from gfx import (W, H, C, P, xf, rrect, poly, line, text, text_width, linear, radial, fill_shader,  # noqa: E402,F401
                 glow, sparkle, check_mark, cross_mark, mixhex, font, clamp, lerp, smooth, ease_out,
                 back_out, at, window, drop)

INK = "#0a0a10"
OUT = "#14141c"
EYE = "#f2ead6"
RIM = "#8ec8ff"
NAVY = "#0f1826"

# ---------------------------------------------------------------- caching + post
_cache = {}


def cached(key, draw, blur=0.0, w=W, h=H):
    if key not in _cache:
        s = skia.Surface(w, h)
        cc = s.getCanvas()
        cc.clear(C("#000000"))
        draw(cc)
        img = s.makeImageSnapshot()
        if blur:
            s2 = skia.Surface(w, h)
            p = skia.Paint(ImageFilter=skia.ImageFilters.Blur(blur, blur, skia.TileMode.kClamp))
            s2.getCanvas().drawImage(img, 0, 0, skia.SamplingOptions(), p)
            img = s2.makeImageSnapshot()
        _cache[key] = img
    return _cache[key]


def blit(c, img, x=0, y=0, a=1.0):
    p = skia.Paint(AntiAlias=True)
    p.setAlphaf(clamp(a))
    c.drawImage(img, x, y, skia.SamplingOptions(skia.FilterMode.kLinear), p)


_grain = []


def grain(c, t, a=0.06):
    if not _grain:
        rnd = random.Random(5)
        for k in range(4):
            s = skia.Surface(480, 270)
            cc = s.getCanvas()
            cc.clear(skia.ColorTRANSPARENT)
            for _ in range(5000):
                v = rnd.choice(("#ffffff", "#000000"))
                cc.drawRect(skia.Rect.MakeXYWH(rnd.uniform(0, 480), rnd.uniform(0, 270), 1, 1), P(v, a=0.9))
            _grain.append(s.makeImageSnapshot())
    img = _grain[int(t * 24) % 4]
    p = skia.Paint()
    p.setAlphaf(a)
    c.drawImageRect(img, skia.Rect(0, 0, W, H), skia.SamplingOptions(), p)


def vignette(c, a=0.6):
    fill_shader(c, skia.Rect(0, 0, W, H),
                radial(W / 2, H / 2, W * 0.72, [("#000000", 0), ("#000000", 0.05), ("#000000", a)], [0, 0.5, 1]))


def tint(c, color, a):
    if a > 0:
        c.drawRect(skia.Rect(0, 0, W, H), P(color, a=a))


# ---------------------------------------------------------------- characters
OUTFITS = {
    "kai": dict(suit="#e8742a", suit2="#a94e17", trim="#f3eee3"),
    "tomas": dict(suit="#4f9a64", suit2="#336843", trim="#e6e0cc", mustache=True),
    "yuki": dict(suit="#e9edf3", suit2="#9aa3b3", trim="#7d5cc8", glasses=True, bob=True),
    "lena": dict(suit="#2c4a86", suit2="#1b2f58", trim="#e8c25a", bun=True),
    "mira": dict(suit="#f2c14e", suit2="#b88a22", trim="#ffffff", pigtails=True, small=True),
}

POSES = {
    "stand": dict(la=(-6, 0), ra=(6, 0), ll=(-3, 0), rl=(3, 0)),
    "float": dict(la=(-40, 30), ra=(45, -25), ll=(-14, 25), rl=(18, 30)),
    "float2": dict(la=(-70, -20), ra=(70, 20), ll=(-20, 10), rl=(20, 10)),
    "mug": dict(la=(30, 75), ra=(40, 60), ll=(-3, 0), rl=(3, 0)),
    "phone": dict(la=(-6, 0), ra=(120, 100), ll=(-3, 0), rl=(3, 0)),
    "point": dict(la=(-6, 0), ra=(95, -5), ll=(-3, 0), rl=(3, 0)),
    "tap": dict(la=(-6, 0), ra=(70, 30), ll=(-3, 0), rl=(3, 0)),
    "shrug": dict(la=(-60, -70), ra=(60, 70), ll=(-3, 0), rl=(3, 0)),
    "laugh": dict(la=(30, 80), ra=(-30, -80), ll=(-6, 0), rl=(6, 0)),
    "fall": dict(la=(-150, 10), ra=(150, -10), ll=(-4, 0), rl=(4, 0)),
    "reach": dict(la=(-6, 0), ra=(120, -20), ll=(-3, 0), rl=(3, 0)),
    "push": dict(la=(100, -5), ra=(80, 5), ll=(-30, 40), rl=(-10, 30)),
    "sit": dict(la=(25, 60), ra=(35, 50), ll=(80, -85), rl=(75, -80)),
    "fingerguns": dict(la=(-80, -20), ra=(80, 20), ll=(-3, 0), rl=(3, 0)),
    "headhold": dict(la=(-140, -80), ra=(140, 80), ll=(-3, 0), rl=(3, 0)),
    "sing": dict(la=(-110, -30), ra=(110, 30), ll=(-6, 0), rl=(6, 0)),
}


def _seg(x, y, ang, L):
    r = math.radians(ang)
    return x + math.sin(r) * L, y + math.cos(r) * L


def _limb(c, x, y, a1, a2, l1, l2, w, col, end="hand", endc=INK):
    x2, y2 = _seg(x, y, a1, l1)
    x3, y3 = _seg(x2, y2, a1 + a2, l2)
    pth = skia.Path()
    pth.moveTo(x, y)
    pth.lineTo(x2, y2)
    pth.lineTo(x3, y3)
    c.drawPath(pth, P(OUT, w + 7))
    c.drawPath(pth, P(col, w))
    if end == "hand":
        c.drawCircle(x3, y3, w * 0.62, P(OUT))
        c.drawCircle(x3, y3, w * 0.55, P(endc))
    elif end == "boot":
        ang = math.radians(a1 + a2)
        with xf(c, x3, y3, rot=-math.degrees(ang)):
            rrect(c, -w * 0.75, -w * 0.3, w * 1.5 + w * 0.35, w * 0.95, w * 0.4, OUT)
            rrect(c, -w * 0.68, -w * 0.24, w * 1.36 + w * 0.35, w * 0.8, w * 0.36, endc)
    return x3, y3


def draw_face(c, who, r, expr, t, look=(0, 0), face=1, talk=0.0, blink_off=0.0):
    o = OUTFITS[who]
    ex0 = face * r * 0.22
    ey = -r * 0.06
    lx, ly = look
    blink = ((t + blink_off) * 0.29 + (hash(who) % 5) * 0.17) % 1.0 < 0.04 and expr not in ("wide", "scared")
    for side in (-1, 1):
        cx = ex0 + side * r * 0.29
        if expr in ("happy", "laugh") or blink or expr == "closed":
            p = skia.Path()
            if expr in ("happy", "laugh"):
                p.moveTo(cx - r * 0.13, ey + r * 0.04)
                p.quadTo(cx, ey - r * 0.12, cx + r * 0.13, ey + r * 0.04)
            else:
                p.moveTo(cx - r * 0.13, ey)
                p.quadTo(cx, ey + r * 0.07, cx + r * 0.13, ey)
            c.drawPath(p, P(EYE, r * 0.07))
            continue
        big = 1.25 if expr in ("wide", "scared") else 1.0
        rx, ry = r * 0.16 * big, r * 0.13 * big
        c.drawOval(skia.Rect(cx - rx, ey - ry, cx + rx, ey + ry), P(EYE))
        pr = r * (0.045 if expr == "scared" else 0.065)
        c.drawCircle(cx + rx * 0.45 * (lx + face * 0.4), ey + ry * 0.35 * ly, pr, P(INK))
        lid = {"neutral": 0.38, "bored": 0.55, "sad": 0.45, "angry": 0.5, "wide": 0.0, "scared": 0.0,
               "smile": 0.35, "worried": 0.3, "deadpan": 0.6, "focus": 0.45}.get(expr, 0.38)
        if lid > 0:
            top = ey - ry - 2
            yl = ey - ry + 2 * ry * lid
            if expr in ("sad", "worried"):
                pts = [(cx - rx - 3, top), (cx + rx + 3, top), (cx + rx + 3, yl - side * face * ry * 0.4 * 0),
                       (cx - rx - 3, yl)]
                inner = yl - ry * 0.45
                pts = [(cx - rx - 3, top), (cx + rx + 3, top)]
                if side == -1:
                    pts += [(cx + rx + 3, inner), (cx - rx - 3, yl)]
                else:
                    pts += [(cx + rx + 3, yl), (cx - rx - 3, inner)]
                c.drawPath(poly(pts), P(INK))
            elif expr == "angry":
                inner = yl + ry * 0.5
                pts = [(cx - rx - 3, top), (cx + rx + 3, top)]
                if side == -1:
                    pts += [(cx + rx + 3, inner), (cx - rx - 3, yl - ry * 0.2)]
                else:
                    pts += [(cx + rx + 3, yl - ry * 0.2), (cx - rx - 3, inner)]
                c.drawPath(poly(pts), P(INK))
            else:
                c.drawRect(skia.Rect(cx - rx - 3, top, cx + rx + 3, yl), P(INK))
        # brows
        by = ey - ry - r * 0.12
        if expr in ("sad", "worried", "scared"):
            line(c, cx - r * 0.12, by + side * r * 0.04, cx + r * 0.12, by - side * r * 0.04, EYE, r * 0.06)
        elif expr == "angry":
            line(c, cx - r * 0.12, by - side * r * 0.05, cx + r * 0.12, by + side * r * 0.05, EYE, r * 0.07)
        elif expr in ("wide",):
            line(c, cx - r * 0.12, by - r * 0.06, cx + r * 0.12, by - r * 0.06, EYE, r * 0.06)
        else:
            line(c, cx - r * 0.12, by, cx + r * 0.12, by, EYE, r * 0.06)
    if o.get("glasses"):
        for side in (-1, 1):
            cx = ex0 + side * r * 0.29
            c.drawCircle(cx, ey, r * 0.23, P(EYE, r * 0.04, 0.8))
        line(c, ex0 - r * 0.06, ey, ex0 + r * 0.06, ey, EYE, r * 0.04, 0.8)
    # mouth
    mx, my = ex0, r * 0.42
    if o.get("mustache"):
        mp = skia.Path()
        mp.moveTo(mx - r * 0.34, my + r * 0.02)
        mp.quadTo(mx - r * 0.3, my - r * 0.24, mx, my - r * 0.14)
        mp.quadTo(mx + r * 0.3, my - r * 0.24, mx + r * 0.34, my + r * 0.02)
        mp.quadTo(mx, my - r * 0.02, mx - r * 0.34, my + r * 0.02)
        c.drawPath(mp, P("#c9a37e"))
        for k in range(3):
            line(c, mx - r * 0.22, my - r * 0.11 + k * r * 0.045, mx + r * 0.22, my - r * 0.11 + k * r * 0.045,
                 "#5a3d2a", r * 0.018)
        my += r * 0.08
    if talk > 0:
        op = 0.3 + 0.7 * abs(math.sin(t * 14))
        c.drawOval(skia.Rect(mx - r * 0.12, my - r * 0.06 * op, mx + r * 0.12, my + r * 0.12 * op), P(EYE))
    elif expr == "laugh":
        p = skia.Path()
        p.moveTo(mx - r * 0.2, my - r * 0.04)
        p.lineTo(mx + r * 0.2, my - r * 0.04)
        p.quadTo(mx + r * 0.16, my + r * 0.26, mx, my + r * 0.26)
        p.quadTo(mx - r * 0.16, my + r * 0.26, mx - r * 0.2, my - r * 0.04)
        c.drawPath(p, P(EYE))
    elif expr in ("smile", "happy"):
        p = skia.Path()
        p.moveTo(mx - r * 0.16, my - r * 0.02)
        p.quadTo(mx, my + r * 0.12, mx + r * 0.16, my - r * 0.02)
        c.drawPath(p, P(EYE, r * 0.06))
    elif expr in ("sad", "worried", "scared"):
        p = skia.Path()
        p.moveTo(mx - r * 0.14, my + r * 0.06)
        if expr == "scared":
            for k in range(1, 5):
                p.lineTo(mx - r * 0.14 + k * r * 0.07, my + (r * 0.02 if k % 2 else r * 0.07))
        else:
            p.quadTo(mx, my - r * 0.05, mx + r * 0.14, my + r * 0.06)
        c.drawPath(p, P(EYE, r * 0.055))
    elif expr == "wide":
        c.drawOval(skia.Rect(mx - r * 0.07, my - r * 0.06, mx + r * 0.07, my + r * 0.1), P(EYE))
    else:
        line(c, mx - r * 0.12, my, mx + r * 0.12, my, EYE, r * 0.055)


def _figure(c, who, pose, expr, t, look, face, talk, space, stretch, helmet):
    o = OUTFITS[who]
    small = o.get("small")
    p = POSES[pose] if isinstance(pose, str) else pose
    suit = "#dfe4ec" if space else o["suit"]
    suit2 = "#aab3c2" if space else o["suit2"]
    accent = o["suit"] if space else o["trim"]
    k = stretch
    wm = 1 / (1 + 0.8 * k)
    tl = 160 * (1 + 0.6 * k) * (0.75 if small else 1)
    hw = 48 * wm
    al1, al2 = (75, 70) if not small else (55, 50)
    ll1, ll2 = (85 * (1 + 2.6 * k), 80 * (1 + 3.2 * k)) if not small else (60, 55)
    aw, lw = 26 * wm, 30 * wm
    hr = 62 * (1.0 if not small else 0.95) * (1 / (1 + 0.25 * k))
    # legs
    for side, key in ((-1, "ll"), (1, "rl")):
        a1, a2 = p[key]
        _limb(c, side * hw * 0.42, -6, a1, a2, ll1, ll2, lw, suit2 if not space else suit, "boot", "#23232c")
    # back arm
    a1, a2 = p["la"] if face > 0 else p["ra"]
    sx = (-1 if face > 0 else 1) * hw * 0.8
    _limb(c, sx, -tl + 22, a1, a2, al1, al2, aw, suit2, "hand")
    # jetpack
    if space:
        rrect(c, -face * hw - face * 34 - 30, -tl + 10, 60, tl * 0.7, 14, OUT)
        rrect(c, -face * hw - face * 34 - 26, -tl + 14, 52, tl * 0.7 - 8, 12, "#8d96a6")
    # torso
    rrect(c, -hw - 4, -tl - 4, hw * 2 + 8, tl + 18, 30 * wm + 4, OUT)
    rrect(c, -hw, -tl, hw * 2, tl + 10, 30 * wm, suit)
    # outfit details
    if space:
        rrect(c, -hw * 0.6, -tl * 0.7, hw * 1.2, tl * 0.28, 8, "#c4ccd8")
        for i, col in enumerate((accent, "#ff5050", "#5bd6ff")):
            c.drawCircle(-hw * 0.35 + i * hw * 0.35, -tl * 0.56, 5, P(col))
        c.drawRect(skia.Rect(-hw, -tl * 0.18, hw, -tl * 0.1), P(accent))
    elif who == "yuki":
        c.drawPath(poly([(-hw * 0.5, -tl), (hw * 0.5, -tl), (0, -tl * 0.45)]), P(o["trim"]))
        line(c, 0, -tl * 0.45, 0, 0, OUT, 3)
    elif who == "lena":
        for side in (-1, 1):
            rrect(c, side * hw - (14 if side > 0 else 0) - (0 if side > 0 else 0), -tl, 14, 8, 3, o["trim"])
        c.drawRect(skia.Rect(-hw, -tl * 0.5, hw, -tl * 0.44), P(o["trim"]))
        c.drawCircle(hw * 0.45 * face, -tl * 0.72, 7, P(o["trim"]))
    elif who == "mira":
        c.drawPath(poly([(-hw * 0.35, -tl), (hw * 0.35, -tl), (hw * 0.15, -tl * 0.8), (-hw * 0.15, -tl * 0.8)]),
                   P(o["suit2"]))
        line(c, -6, -tl * 0.8, -6, -tl * 0.55, "#ffffff", 3)
        line(c, 6, -tl * 0.8, 6, -tl * 0.55, "#ffffff", 3)
        rrect(c, -hw * 0.6, -tl * 0.4, hw * 1.2, tl * 0.25, 10, o["suit2"])
    else:
        # jumpsuit: zipper, belt, chest patch
        line(c, 0, -tl + 6, 0, -tl * 0.15, o["suit2"], 4)
        c.drawRect(skia.Rect(-hw, -tl * 0.18, hw, -tl * 0.1), P(o["suit2"]))
        rrect(c, face * hw * 0.25 - 14, -tl * 0.8, 28, 20, 5, o["trim"])
        rrect(c, -hw * 0.95, -tl * 0.95, hw * 0.35, tl * 0.2, 6, o["suit2"])
    # head
    hy = -tl - hr * 0.78
    with xf(c, 0, hy):
        if o.get("bun"):
            c.drawCircle(-face * hr * 0.72, -hr * 0.62, hr * 0.38, P(OUT))
            c.drawCircle(-face * hr * 0.72, -hr * 0.62, hr * 0.34, P(INK))
        if o.get("pigtails"):
            for side in (-1, 1):
                c.drawCircle(side * hr * 0.95, -hr * 0.45, hr * 0.36, P(INK))
                c.drawCircle(side * hr * 0.75, -hr * 0.62, hr * 0.12, P("#ff6f9c"))
        if o.get("bob"):
            c.drawPath(poly([(-hr * 1.08, -hr * 0.2), (hr * 1.08, -hr * 0.2), (hr * 1.0, hr * 0.62),
                             (-hr * 1.0, hr * 0.62)]), P(INK))
        c.drawCircle(0, 0, hr + 3.5, P(OUT))
        c.drawCircle(0, 0, hr, P(INK))
        draw_face(c, who, hr, expr, t, look, face, talk)
        if helmet:
            c.drawCircle(0, hr * 0.05, hr * 1.42, P("#bfe3ff", a=0.12))
            c.drawCircle(0, hr * 0.05, hr * 1.42, P("#bfe3ff", 5, 0.75))
            c.drawCircle(-hr * 0.7, -hr * 0.85, hr * 0.17, P("#ffffff", a=0.65))
            c.drawCircle(-hr * 0.98, -hr * 0.4, hr * 0.06, P("#ffffff", a=0.5))
    # front arm
    a1, a2 = p["ra"] if face > 0 else p["la"]
    sx = (1 if face > 0 else -1) * hw * 0.8
    hand = _limb(c, sx, -tl + 22, a1, a2, al1, al2, aw, suit, "hand")
    return hand, hy, hr


def figure(c, x, y, who="kai", pose="stand", expr="neutral", t=0.0, s=1.0, look=(0, 0), face=1, talk=0.0,
           space=False, helmet=None, stretch=0.0, rot=0.0, rim=RIM, rim_off=(9, -8), red=0.0, alpha=1.0, hold=None):
    """Character with hip center at (x, y). Returns world position of the front hand."""
    helmet = space if helmet is None else helmet
    bounds = skia.Rect(x - 700 * s, y - 1100 * s, x + 700 * s, y + 900 * s)
    if alpha < 0.999:
        c.saveLayerAlpha(bounds, int(alpha * 255))
    # rim pass
    if rim:
        rp = skia.Paint(ColorFilter=skia.ColorFilters.Blend(C(rim), skia.BlendMode.kSrcIn))
        c.saveLayer(bounds, rp)
        with xf(c, x + rim_off[0] * s, y + rim_off[1] * s, s, rot):
            _figure(c, who, pose, expr, t, look, face, talk, space, stretch, helmet)
        c.restore()
    with xf(c, x, y, s, rot):
        if red > 0:
            rp = skia.Paint(ColorFilter=skia.ColorFilters.Blend(C("#ff3b1f", 0.75 * red), skia.BlendMode.kSrcATop))
            c.saveLayer(bounds.makeOffset(-x, -y) if False else None, rp)
        hand, hy, hr = _figure(c, who, pose, expr, t, look, face, talk, space, stretch, helmet)
        if hold:
            hold(c, *hand)
        if red > 0:
            c.restore()
    if alpha < 0.999:
        c.restore()
    r = math.radians(rot)
    hx, hyy = hand[0] * s, hand[1] * s
    return (x + hx * math.cos(r) - hyy * math.sin(r), y + hx * math.sin(r) + hyy * math.cos(r))


def head_only(c, x, y, who, expr, t, r=62, look=(0, 0), face=1, talk=0.0, rim=RIM, helmet=False):
    o = OUTFITS[who]
    with xf(c, x + 9, y - 8):
        c.drawCircle(0, 0, r + 4, P(rim))
    with xf(c, x, y):
        if o.get("bun"):
            c.drawCircle(-face * r * 0.72, -r * 0.62, r * 0.36, P(INK))
        if o.get("pigtails"):
            for side in (-1, 1):
                c.drawCircle(side * r * 0.95, -r * 0.45, r * 0.36, P(INK))
        c.drawCircle(0, 0, r + 3, P(OUT))
        c.drawCircle(0, 0, r, P(INK))
        draw_face(c, who, r, expr, t, look, face, talk)
        if helmet:
            c.drawCircle(0, r * 0.05, r * 1.42, P("#bfe3ff", a=0.1))
            c.drawCircle(0, r * 0.05, r * 1.42, P("#bfe3ff", 5, 0.75))
            c.drawCircle(-r * 0.7, -r * 0.85, r * 0.17, P("#ffffff", a=0.65))


# ---------------------------------------------------------------- props
def mug(c, x, y, s=1.0, t=0.0, face=False, steam=True, rot=0.0):
    with xf(c, x, y, s, rot):
        rrect(c, 22, -30, 34, 40, 16, OUT, stroke=10)
        rrect(c, -34, -46, 64, 78, 12, OUT)
        rrect(c, -30, -42, 56, 70, 10, "#3a3f4c")
        rrect(c, -22, -20, 40, 18, 4, "#141820")
        text(c, "COFFEE", -2, -6, 11, "#ffb347", "ExtraBold")
        if face:
            c.drawCircle(-12, 10, 3.5, P(EYE))
            c.drawCircle(8, 10, 3.5, P(EYE))
            pp = skia.Path()
            pp.moveTo(-10, 18)
            pp.quadTo(-2, 25, 6, 18)
            c.drawPath(pp, P(EYE, 3))
        if steam:
            for i in range(2):
                pp = skia.Path()
                bx = -12 + i * 18
                pp.moveTo(bx, -50)
                for k in range(1, 6):
                    pp.lineTo(bx + 6 * math.sin(t * 3 + k + i), -50 - k * 14)
                c.drawPath(pp, P("#9aa3b3", 4, 0.5))


def phone(c, x, y, s=1.0, rot=0.0, screen="#2b3a55", glow_a=0.0):
    with xf(c, x, y, s, rot):
        if glow_a:
            glow(c, 0, 0, 120, "#9fd0ff", glow_a)
        rrect(c, -28, -52, 56, 104, 10, OUT)
        rrect(c, -24, -48, 48, 96, 8, screen)


def probe(c, x, y, s=1.0, t=0.0, red=0.0, a=1.0):
    with xf(c, x, y, s, rot=t * 40, alpha=a):
        col = mixhex("#d7dde6", "#ff2a10", red)
        line(c, 0, -40, 0, -70, col, 4)
        c.drawCircle(0, -72, 6, P(mixhex("#ff5050", "#ff2a10", red)))
        c.drawCircle(0, 0, 36, P(OUT))
        c.drawCircle(0, 0, 32, P(col))
        rrect(c, -46, -8, 92, 16, 4, mixhex("#3a5ba8", "#7a1a10", red))
        c.drawCircle(-10, -10, 8, P("#ffffff", a=0.5 * (1 - red)))


def stopwatch(c, x, y, s, frac, col="#5bd6ff", label=None, frozen=False, t=0.0):
    with xf(c, x, y, s):
        rrect(c, -14, -132, 28, 24, 6, "#c9ced8")
        c.drawCircle(0, 0, 112, P("#c9ced8"))
        c.drawCircle(0, 0, 100, P("#121820"))
        arc = skia.Path()
        arc.addArc(skia.Rect(-88, -88, 88, 88), -90, 360 * (frac % 1.0))
        c.drawPath(arc, P(col, 14))
        ang = math.radians(frac * 360)
        line(c, 0, 0, math.sin(ang) * 80, -math.cos(ang) * 80, "#ffffff", 7)
        c.drawCircle(0, 0, 10, P("#ffffff"))
        if frozen:
            for i in range(6):
                a = i * 60 + 15
                line(c, math.cos(math.radians(a)) * 60, math.sin(math.radians(a)) * 60,
                     math.cos(math.radians(a)) * 100, math.sin(math.radians(a)) * 100, "#bfe8ff", 4, 0.7)
    if label:
        text(c, label, x, y + 170 * s, 56 * s, col, "Black")


def tether(c, x1, y1, x2, y2, sag=60, color="#e6e0cc", w=6, a=1.0):
    p = skia.Path()
    p.moveTo(x1, y1)
    p.quadTo((x1 + x2) / 2, (y1 + y2) / 2 + sag, x2, y2)
    c.drawPath(p, P(OUT, w + 4, a))
    c.drawPath(p, P(color, w, a))


def screen_panel(c, x, y, w, h, t, kind="graph", col="#5bd6ff", alert=False):
    rrect(c, x - 6, y - 6, w + 12, h + 12, 14, OUT)
    rrect(c, x, y, w, h, 10, "#0d1a2a")
    glow(c, x + w / 2, y + h / 2, max(w, h) * 0.7, "#ff3b3b" if alert else col, 0.12)
    if kind == "graph":
        pth = skia.Path()
        pth.moveTo(x + 14, y + h - 20)
        for i in range(1, 21):
            xx = x + 14 + i * (w - 28) / 20
            yy = y + h - 20 - (h - 50) * (0.5 + 0.4 * math.sin(i * 0.7 + t * 2)) * (i / 20)
            pth.lineTo(xx, yy)
        c.drawPath(pth, P(col, 3))
    elif kind == "bars":
        for i in range(6):
            bh = (h - 40) * (0.3 + 0.6 * abs(math.sin(i * 1.3 + t)))
            rrect(c, x + 16 + i * (w - 32) / 6, y + h - 16 - bh, (w - 32) / 6 - 10, bh, 4, col, 0.8)
    elif kind == "text":
        for i in range(5):
            rrect(c, x + 16, y + 18 + i * (h - 30) / 5, (w - 40) * (0.4 + 0.5 * ((i * 37) % 10) / 10), 8, 4, col, 0.7)
    if alert and int(t * 3) % 2 == 0:
        rrect(c, x, y, w, h, 10, "#ff3b3b", stroke=4)


# ---------------------------------------------------------------- space
_rs = random.Random(42)
STARS = [(_rs.uniform(0, 1), _rs.uniform(0, 1), _rs.uniform(0.6, 2.6), _rs.uniform(0, 6.28)) for _ in range(420)]


def starfield(c, t, rect=None, drift=(0.0, 0.0), streak=0.0, a=1.0, center=None, lens=0.0):
    x0, y0, x1, y1 = rect or (0, 0, W, H)
    w, h = x1 - x0, y1 - y0
    fill_shader(c, skia.Rect(x0, y0, x1, y1), linear(0, y0, 0, y1, ["#03040a", "#070a18"]))
    for (u, v, r, ph) in STARS:
        x = x0 + ((u * w + drift[0] * t) % w)
        y = y0 + ((v * h + drift[1] * t) % h)
        if center and lens:
            cx, cy, R = center
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy) + 1e-6
            if d < R * 1.02:
                continue
            push = lens * R * R / d
            x, y = x + dx / d * push * 0.15, y + dy / d * push * 0.15
        tw = 0.6 + 0.4 * math.sin(t * 2 + ph * 5)
        if streak > 0:
            line(c, x, y, x, y - streak * r * 18, "#dfe9ff", r * 0.8, a * tw * 0.8)
        else:
            c.drawCircle(x, y, r, P("#dfe9ff", a=a * tw))


def black_hole(c, x, y, r, t, disk=1.0, tilt=0.28):
    """Black hole with glowing accretion disk and lensed ring. r = shadow radius."""
    glow(c, x, y, r * 4.2, "#ff8a2a", 0.22 * disk)
    glow(c, x, y, r * 2.4, "#ffc46b", 0.25 * disk)
    if disk > 0:
        # back half of disk (behind the hole)
        for k, (col, wmul, aa) in enumerate((("#ff6a1a", 1.0, 0.55), ("#ffb347", 0.6, 0.75), ("#fff1c9", 0.25, 0.9))):
            c.save()
            c.clipRect(skia.Rect(x - r * 5, y - r * 5, x + r * 5, y))
            c.drawOval(skia.Rect(x - r * 3.0, y - r * 3.0 * tilt, x + r * 3.0, y + r * 3.0 * tilt),
                       P(col, r * 0.55 * wmul, aa * disk))
            c.restore()
        # lensed ring over the top
        for col, wmul, aa in (("#ff7a22", 0.32, 0.5), ("#ffd27a", 0.14, 0.8)):
            c.drawCircle(x, y, r * 1.28, P(col, r * wmul, aa * disk))
    c.drawCircle(x, y, r * 1.06, P("#fff3d6", r * 0.05, 0.9 * disk))
    c.drawCircle(x, y, r, P("#000000"))
    if disk > 0:
        c.save()
        c.clipRect(skia.Rect(x - r * 5, y, x + r * 5, y + r * 5))
        for k, (col, wmul, aa) in enumerate((("#ff6a1a", 1.0, 0.6), ("#ffb347", 0.6, 0.8), ("#fff1c9", 0.25, 0.95))):
            c.drawOval(skia.Rect(x - r * 3.0, y - r * 3.0 * tilt, x + r * 3.0, y + r * 3.0 * tilt),
                       P(col, r * 0.55 * wmul, aa * disk))
        c.restore()
        # orbiting hot spots
        for i in range(10):
            ang = t * (0.9 + 0.05 * i) + i * 0.63
            px = x + math.cos(ang) * r * (2.2 + 0.5 * math.sin(i))
            py = y + math.sin(ang) * r * (2.2 + 0.5 * math.sin(i)) * tilt
            if math.sin(ang) > 0 or abs(px - x) > r * 1.1:
                c.drawCircle(px, py, r * 0.05, P("#fff6e0", a=0.8 * disk))


def ship(c, x, y, s=1.0, t=0.0, face=1, lights=True):
    with xf(c, x, y, sx=s * face, sy=s):
        rrect(c, -260, -60, 420, 120, 50, OUT)
        rrect(c, -256, -56, 412, 112, 46, "#c9d0dc")
        c.drawPath(poly([(150, -56), (290, -10), (290, 10), (150, 56)]), P("#c9d0dc"))
        c.drawPath(poly([(150, -56), (290, -10), (290, 10), (150, 56)]), P(OUT, 4))
        rrect(c, 160, -28, 90, 40, 16, "#5bd6ff")
        for i in range(5):
            c.drawCircle(-170 + i * 60, -10, 11, P("#ffd37a" if lights else "#33404f"))
        c.drawRect(skia.Rect(-256, 22, 156, 34), P("#e8742a"))
        rrect(c, -330, -40, 80, 80, 20, "#7a8494")
        glow(c, -340, 0, 90, "#5bd6ff", 0.5 + 0.2 * math.sin(t * 20))
        # solar wings
        for sgn in (-1, 1):
            rrect(c, -150, sgn * 60 + (0 if sgn > 0 else -90), 180, 90, 6, "#1f3d6e")
            for k in range(4):
                line(c, -150 + k * 45, sgn * 60 + (0 if sgn > 0 else -90), -150 + k * 45,
                     sgn * 60 + (90 if sgn > 0 else 0), "#5c86c9", 2)


# ---------------------------------------------------------------- sets (drawn once, then blurred)
def _shelf(c, x, y, w, h):
    rrect(c, x, y, w, h, 4, "#1d2738")
    for k in range(3):
        yy = y + 20 + k * (h - 30) / 3
        c.drawRect(skia.Rect(x + 8, yy + (h - 30) / 3 - 8, x + w - 8, yy + (h - 30) / 3), P("#2b3a52"))
        rnd = random.Random(int(x + yy))
        xx = x + 16
        while xx < x + w - 40:
            bw = rnd.uniform(24, 60)
            bh = rnd.uniform(20, (h - 30) / 3 - 14)
            col = rnd.choice(["#3d6f6a", "#8a4b3a", "#4b4f8a", "#7a6a3a", "#5a6478", "#2f5b8a"])
            rrect(c, xx, yy + (h - 30) / 3 - 8 - bh, bw, bh, 3, col)
            xx += bw + rnd.uniform(6, 18)


def set_bridge(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#141e2e", "#0c121c"]))
    # big window
    rrect(c, 360, 120, 1200, 560, 40, "#070a14")
    starfield(c, 0.0, (380, 140, 1540, 660))
    black_hole(c, 1180, 420, 95, 0.0)
    rrect(c, 360, 120, 1200, 560, 40, "#2a3850", stroke=26)
    for xx in (760, 1160):
        c.drawRect(skia.Rect(xx - 8, 120, xx + 8, 680), P("#2a3850"))
    # side walls
    c.drawRect(skia.Rect(0, 0, 330, H), P("#172234"))
    c.drawRect(skia.Rect(W - 330, 0, W, H), P("#172234"))
    _shelf(c, 40, 250, 260, 420)
    for i in range(4):
        rrect(c, W - 300, 200 + i * 110, 240, 80, 8, "#20304a")
        rrect(c, W - 286, 214 + i * 110, 120, 12, 4, ["#5bd6ff", "#ffb347", "#7de08a", "#ff6b6b"][i], 0.7)
    # console
    c.drawPath(poly([(200, 760), (1720, 760), (1820, H), (100, H)]), P("#1a2436"))
    c.drawRect(skia.Rect(200, 740, 1720, 770), P("#26344c"))
    for i in range(7):
        rrect(c, 270 + i * 210, 790, 160, 90, 10, "#0f2236")
        rrect(c, 285 + i * 210, 810, 90, 10, 4, ["#5bd6ff", "#ffb347", "#7de08a"][i % 3], 0.6)


def set_corridor(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#18222f", "#0d131c"]))
    for i in range(6):
        x = i * 380 - 60
        rrect(c, x, 140, 300, 640, 20, "#1e2a3c")
        rrect(c, x + 20, 160, 260, 600, 16, "#223249")
        c.drawRect(skia.Rect(x + 30, 440, x + 270, 452), P("#2f4466"))
    rrect(c, 820, 180, 300, 520, 18, "#33231f")
    rrect(c, 840, 200, 120, 480, 8, "#3d2a24")
    rrect(c, 980, 200, 120, 480, 8, "#3d2a24")
    for i in range(8):
        c.drawRect(skia.Rect(0, 70 + i * 2, W, 72 + i * 2), P("#2a3a52"))
    for i in range(5):
        x = 150 + i * 420
        rrect(c, x, 40, 200, 26, 12, "#9fd0ff", 0.7)
    c.drawRect(skia.Rect(0, 800, W, H), P("#101722"))
    _shelf(c, 1300, 260, 280, 380)
    rrect(c, 380, 230, 260, 160, 10, "#1b3a6a")
    c.drawCircle(470, 310, 50, P("#3a6ab0", 6))
    line(c, 400, 360, 620, 250, "#3a6ab0", 5)


def set_quarters(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#1a2333", "#0e141f"]))
    rrect(c, 120, 300, 300, 560, 14, "#3a2420")
    line(c, 270, 320, 270, 840, "#2a1a17", 6)
    _shelf(c, 520, 280, 420, 520)
    c.drawCircle(1350, 360, 150, P("#070a14"))
    starfield(c, 0.0, (1200, 210, 1500, 510))
    c.drawCircle(1350, 360, 150, P("#2a3850", 24))
    rrect(c, 1150, 640, 500, 40, 8, "#2a3850")
    rrect(c, 1180, 680, 30, 220, 6, "#2a3850")
    rrect(c, 1590, 680, 30, 220, 6, "#2a3850")
    rrect(c, 1000, 180, 160, 110, 6, "#1f3d6e")
    c.drawCircle(1080, 235, 32, P("#5b8fd6"))


def set_mira_room(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#2a2238", "#151020"]))
    # window with night city + moon
    rrect(c, 1100, 160, 560, 420, 16, "#0d1430")
    for i in range(30):
        rnd = random.Random(i)
        bx = 1110 + i * 19
        bh = rnd.uniform(60, 200)
        c.drawRect(skia.Rect(bx, 580 - bh, bx + 17, 580), P("#1b2142"))
        for k in range(int(bh / 26)):
            if rnd.random() > 0.5:
                c.drawRect(skia.Rect(bx + 5, 580 - bh + 10 + k * 26, bx + 11, 580 - bh + 18 + k * 26), P("#ffd37a", a=0.7))
    c.drawCircle(1540, 260, 46, P("#f3efe0"))
    rrect(c, 1100, 160, 560, 420, 16, "#3a2f4a", stroke=22)
    line(c, 1380, 160, 1380, 580, "#3a2f4a", 14)
    # bed, lamp, posters
    rrect(c, 120, 640, 760, 260, 30, "#4a3a6a")
    rrect(c, 140, 600, 260, 90, 30, "#e8e0f0")
    glow(c, 960, 520, 300, "#ffb86b", 0.35)
    rrect(c, 930, 520, 60, 260, 8, "#3a2f4a")
    c.drawPath(poly([(900, 520), (1020, 520), (990, 440), (930, 440)]), P("#ffcf8a"))
    rrect(c, 300, 200, 220, 300, 8, "#5a3a7a")
    c.drawCircle(410, 320, 70, P("#ff8a6b"))
    rrect(c, 580, 240, 180, 140, 8, "#2f5b8a")
    sparkle(c, 670, 310, 40, "#ffe08a")


def set_lab(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#121c2b", "#0a1018"]))
    rrect(c, 60, 160, 520, 320, 14, "#16263a")
    # world-map style chart
    rnd = random.Random(9)
    for i in range(90):
        c.drawCircle(90 + rnd.uniform(0, 460), 190 + rnd.uniform(0, 260), rnd.uniform(4, 12), P("#c9a55a", a=0.5))
    for j in range(2):
        for i in range(3):
            screen_panel(c, 700 + i * 300, 170 + j * 230, 260, 190, 1.0 + i + j, ["graph", "bars", "text"][(i + j) % 3])
    c.drawRect(skia.Rect(0, 760, W, H), P("#0f1722"))
    rrect(c, 640, 640, 900, 40, 10, "#1e2b40")


SETS = {"bridge": set_bridge, "corridor": set_corridor, "quarters": set_quarters, "mira": set_mira_room,
        "lab": set_lab}


def draw_set(c, name, blur=7.0, a=1.0):
    img = cached(("set", name, blur), SETS[name], blur)
    blit(c, img, 0, 0, a)


# ---------------------------------------------------------------- titles / UI
def lower_third(c, t, start, name, role, color, x=110, y=860, dur=4.0):
    k = ease_out(at(t, start, 0.5))
    out = clamp((start + dur - t) / 0.4)
    if k <= 0 or out <= 0:
        return
    w = max(text_width(name, 64, "Black"), text_width(role, 30, "SemiBold")) + 70
    with xf(c, x - (1 - k) * 60, y, alpha=k * out):
        rrect(c, 0, 0, 12, 120, 6, color)
        rrect(c, 22, 0, w, 120, 12, "#0b1018", 0.85)
        text(c, name, 46, 62, 64, "#ffffff", "Black", align="left")
        text(c, role.upper(), 48, 100, 28, color, "SemiBold", align="left")


def kicker(c, t, start, s, y=170, size=64, color="#ffffff", end=None, accent=None):
    k = ease_out(at(t, start, 0.45))
    out = 1.0 if end is None else clamp((end - t) / 0.35)
    if k <= 0 or out <= 0:
        return
    with xf(c, W / 2, y + (1 - k) * 30, alpha=k * out):
        text(c, s, 0, 0, size, color, "Black", shadow=True)
        if accent:
            w = text_width(s, size)
            rrect(c, -w / 2, size * 0.25, w * k, 8, 4, accent)


def tag(c, x, y, s, color="#5bd6ff", size=36, a=1.0, sc=1.0, fg="#0b1018"):
    w = text_width(s, size, "Black") + 44
    with xf(c, x, y, sc, alpha=a):
        rrect(c, -w / 2, -size * 0.78, w, size * 1.56, 12, color)
        text(c, s, 0, size * 0.36, size, fg, "Black")


def info_board(c, t, top="#0d1624", bottom="#070b12"):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, [top, bottom]))
    for i in range(0, W, 80):
        c.drawRect(skia.Rect(i, 0, i + 1, H), P("#ffffff", a=0.03))
    for j in range(0, H, 80):
        c.drawRect(skia.Rect(0, j, W, j + 1), P("#ffffff", a=0.03))


def arrow(c, x1, y1, x2, y2, color, w=14, a=1.0, head=2.6):
    ang = math.atan2(y2 - y1, x2 - x1)
    L = math.hypot(x2 - x1, y2 - y1)
    if L < 2:
        return
    with xf(c, x1, y1, rot=math.degrees(ang), alpha=a):
        hl = min(L * 0.45, w * head)
        line(c, 0, 0, L - hl * 0.8, 0, color, w)
        c.drawPath(poly([(L, 0), (L - hl, -hl * 0.6), (L - hl, hl * 0.6)]), P(color))


def jagged_split(c, x=W / 2, amp=10, color="#05060a", w=12, seed=1):
    pts = []
    rnd = random.Random(seed)
    for y in range(-10, H + 30, 26):
        pts.append((x + rnd.uniform(-amp, amp), y))
    pth = poly(pts, close=False)
    c.drawPath(pth, P(color, w))
    return pts


def clip_half(c, side, x=W / 2, seed=1, amp=10):
    rnd = random.Random(seed)
    pts = [(x + rnd.uniform(-amp, amp), y) for y in range(-10, H + 30, 26)]
    if side == 0:
        path = poly([(-10, -10)] + pts + [(-10, H + 30)])
    else:
        path = poly([(W + 10, -10)] + pts + [(W + 10, H + 30)])
    c.clipPath(path, skia.ClipOp.kIntersect, True)
