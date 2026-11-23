"""Style kit for the GTA VI 'born as Lucia' 2D video.

Look: flat-vector cartoon with thick dark-brown outlines, chibi characters (big heads, small
bodies), detailed hand-drawn-feeling sets, Vice City sunset palette (purple, pink, orange,
teal), paper maps, polaroids, white name tags and speech bubbles, a soft vignette and film grain.
Everything is drawn in code so every frame is deterministic.
"""
import math
import os
import random
import sys

import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from gfx import (W, H, C, P, xf, rrect, poly, line, linear, radial, fill_shader,  # noqa: E402,F401
                 glow, sparkle, mixhex, clamp, lerp, smooth, ease_out, back_out, at, window, font)

OUT = "#2a1a12"          # outline ink
OW = 5.0                 # outline width
FONTS = os.path.join(HERE, "fonts")
_tf = {}


def tface(name):
    if name not in _tf:
        if name == "inter":
            _tf[name] = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-Black.otf")
        elif name == "interb":
            _tf[name] = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-Bold.otf")
        else:
            _tf[name] = skia.Typeface.MakeFromFile(os.path.join(FONTS, name))
    return _tf[name]


MARKER = "PermanentMarker-Regular.ttf"
BANG = "Bangers-Regular.ttf"
SERIF = "Alegreya-Italic.ttf"
SCRIPT = "Pacifico-Regular.ttf"
LUCKY = "LuckiestGuy-Regular.ttf"
BRUSH = "CaveatBrush-Regular.ttf"
_fc = {}


def F(name, size):
    k = (name, round(size, 1))
    if k not in _fc:
        f = skia.Font(tface(name), size)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        _fc[k] = f
    return _fc[k]


def tw(s, size, fam="inter"):
    return F(fam, size).measureText(s)


def T(c, s, x, y, size, color="#ffffff", fam="inter", align="center", a=1.0, outline=None, ow=0, shadow=0.0,
      rot=0.0):
    f = F(fam, size)
    w = f.measureText(s)
    dx = -w / 2 if align == "center" else (-w if align == "right" else 0)
    with xf(c, x, y, rot=rot):
        if shadow:
            c.drawString(s, dx + size * 0.04, size * 0.06, f, P("#000000", a=shadow * a))
        if outline:
            c.drawString(s, dx, 0, f, P(outline, ow, a))
        c.drawString(s, dx, 0, f, P(color, a=a))
    return w


def shape(c, path, fill, a=1.0, ow=OW, oc=OUT):
    c.drawPath(path, P(fill, a=a))
    if ow:
        c.drawPath(path, P(oc, ow, a))


def oval(c, x, y, rx, ry, fill, a=1.0, ow=OW, oc=OUT):
    pth = skia.Path()
    pth.addOval(skia.Rect(x - rx, y - ry, x + rx, y + ry))
    shape(c, pth, fill, a, ow, oc)


def box(c, x, y, w, h, fill, r=0, a=1.0, ow=OW, oc=OUT):
    pth = skia.Path()
    pth.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r))
    shape(c, pth, fill, a, ow, oc)


def rect(c, x, y, w, h, color, a=1.0):
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), P(color, a=a))


def grad_rect(c, x, y, w, h, cols, pos=None, vertical=True):
    sh = linear(x, y, x, y + h, cols, pos) if vertical else linear(x, y, x + w, y, cols, pos)
    fill_shader(c, skia.Rect.MakeXYWH(x, y, w, h), sh)


def blend(t):
    return smooth(t)


# ---------------------------------------------------------------- caching + post
_cache = {}


def cached(key, draw, blur=0.0, w=W, h=H):
    if key not in _cache:
        s = skia.Surface(w, h)
        cc = s.getCanvas()
        cc.clear(skia.ColorTRANSPARENT)
        draw(cc)
        img = s.makeImageSnapshot()
        if blur:
            s2 = skia.Surface(w, h)
            s2.getCanvas().clear(skia.ColorTRANSPARENT)
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


def grain(c, t, a=0.05):
    if not _grain:
        rnd = random.Random(5)
        for _ in range(4):
            s = skia.Surface(480, 270)
            cc = s.getCanvas()
            cc.clear(skia.ColorTRANSPARENT)
            for _ in range(4500):
                v = rnd.choice(("#ffffff", "#000000"))
                cc.drawRect(skia.Rect.MakeXYWH(rnd.uniform(0, 480), rnd.uniform(0, 270), 1, 1), P(v, a=0.9))
            _grain.append(s.makeImageSnapshot())
    img = _grain[int(t * 24) % 4]
    p = skia.Paint()
    p.setAlphaf(a)
    c.drawImageRect(img, skia.Rect(0, 0, W, H), skia.SamplingOptions(), p)


def vignette(c, a=0.5):
    fill_shader(c, skia.Rect(0, 0, W, H),
                radial(W / 2, H / 2, W * 0.75, [("#000000", 0), ("#000000", 0.0), ("#120614", a)], [0, 0.55, 1]))


def tint(c, color, a):
    if a > 0:
        c.drawRect(skia.Rect(0, 0, W, H), P(color, a=clamp(a)))


def hsh(s):
    return sum(ord(ch) * (i + 1) for i, ch in enumerate(s))


# ---------------------------------------------------------------- characters
SKIN = {"raul": "#c48e64", "abe": "#e0b48e", "valentina": "#d8a27c", "cordell": "#6e442b", "mendes": "#c08a60",
        "giorgio": "#e9c4a2", "camila": "#d6a07a", "danica": "#f0cdb0", "vinny": "#e2b08a", "liz": "#f0c8a8",
        "mattia": "#d0986c", "arnold": "#e6b892", "aunt": "#b87a50", "counselor": "#e8c0a0", "masked": "#c98a5e",
        "lucia": "#c98a5e", "mom": "#b87a50", "jason": "#e7b48c", "tommy": "#cf9466", "guard": "#a8704a",
        "cop": "#e2ad86", "cop2": "#8a5a3a", "boss": "#d9a07a", "inmate": "#9c6a45", "coach": "#7d4f33",
        "judge": "#e8c0a0", "lawyer": "#d6a27c", "kid": "#c98a5e", "man": "#b07850", "woman": "#e0aa80",
        "dad": "#b07a52", "friend": "#8d5b3b", "dealer": "#d9a684", "cal": "#efc5a0", "boobie": "#7a4c30",
        "brian": "#f0c6a4", "dre": "#6e442b"
}

LOOKS = {
    # who: hair style, hair color, top, top2, bottom, shoes, extras
    "lucia":   dict(fem=True, tank=True, hair="pony", hc="#2b1a14", top="#f4efe6", bottom="#3c6fb4", shoes="#f2f2f2", ear="hoop"),
    "lucia_p": dict(fem=True, hair="pony", hc="#2b1a14", top="#f08a2c", bottom="#f08a2c", shoes="#e9e9e9", ear=None,
                    jump=True),
    "lucia_box": dict(fem=True, tank=True, hair="pony", hc="#2b1a14", top="#d9383a", bottom="#1f1f2b", shoes="#e8e8e8", ear=None,
                      wraps=True),
    "lucia_kid": dict(fem=True, hair="puffs", hc="#2b1a14", top="#f6c544", bottom="#4b7fc4", shoes="#ffffff", ear=None,
                      small=True),
    "lucia_teen": dict(fem=True, hair="pony", hc="#2b1a14", top="#7ac4c2", bottom="#33476b", shoes="#ffffff", ear="stud",
                       small=False),
    "lucia_baby": dict(hair="babycurl", hc="#2b1a14", top="#f4a7c0", bottom="#f4a7c0", shoes="#f4a7c0",
                       baby=True),
    "mom":     dict(fem=True, hair="curly", hc="#1f1410", top="#2f8f83", bottom="#2f8f83", shoes="#6b3a2a", dress=True,
                    ear="hoop"),
    "dad":     dict(hair="short", hc="#1d130e", top="#e9e0cf", bottom="#4c5a73", shoes="#3b2a22", mustache=True),
    "jason":   dict(hair="jason", hc="#5b3a24", top="#8a8f96", bottom="#3d4f6d", shoes="#6b4a33", stubble=True),
    "tommy":   dict(hair="babycurl", hc="#2b1a14", top="#8fc6ef", bottom="#8fc6ef", shoes="#8fc6ef", baby=True),
    "tommy_kid": dict(hair="short", hc="#2b1a14", top="#e84b3c", bottom="#4b7fc4", shoes="#ffffff", small=True),
    "guard":   dict(long=True, hair="cap", hc="#1d2a44", top="#3a4f78", bottom="#25324d", shoes="#151515", badge=True),
    "cop":     dict(long=True, hair="cap", hc="#141a2a", top="#24324f", bottom="#1a2236", shoes="#111111", badge=True),
    "cop2":    dict(long=True, hair="cap", hc="#141a2a", top="#24324f", bottom="#1a2236", shoes="#111111", badge=True),
    "inmate":  dict(hair="buzz", hc="#1d130e", top="#f08a2c", bottom="#f08a2c", shoes="#e9e9e9", jump=True),
    "coach":   dict(hair="bald", hc="#1d130e", top="#2b2b33", bottom="#55555f", shoes="#e9e9e9", mustache=True,
                    whistle=True),
    "boss":    dict(long=True, hair="slick", hc="#14100e", top="#202024", bottom="#202024", shoes="#0d0d0d", suit=True,
                    shades=True),
    "judge":   dict(long=True, fem=True, hair="gray", hc="#d8d4cc", top="#15151a", bottom="#15151a", shoes="#0d0d0d", dress=True),
    "lawyer":  dict(long=True, hair="short", hc="#3a2a1e", top="#3b4256", bottom="#3b4256", shoes="#1a1a1a", suit=True),
    "man":     dict(hair="short", hc="#1d130e", top="#c9603f", bottom="#38404f", shoes="#2a2a2a"),
    "woman":   dict(fem=True, hair="long", hc="#c58b3c", top="#e05d8c", bottom="#2f3b55", shoes="#f2f2f2"),
    "friend":  dict(hair="braids", hc="#1d130e", top="#9b59b6", bottom="#2f3b55", shoes="#ffffff", ear="hoop"),
    "dealer":  dict(long=True, hair="slick", hc="#2a1d14", top="#f2f2f2", bottom="#c9c2b0", shoes="#c9a27a", suit=True,
                    shades=True),
    "cal":     dict(hair="cal", hc="#8a6b4a", top="#6d7d5b", bottom="#4a4f5c", shoes="#3b2a22", glasses=True),
    "boobie":  dict(hair="bald", hc="#1d130e", top="#f2f2f2", bottom="#20242e", shoes="#111111", chain=True,
                    shades=False),
    "dre":     dict(hair="buzz", hc="#1d130e", top="#121216", bottom="#121216", shoes="#d8d8d8", chain=True),
    "brian":   dict(hair="gray", hc="#e3ddd3", top="#c9ad79", bottom="#4b5563", shoes="#3b2a22", mustache=True),
"raul":    dict(long=True, hair="slick", hc="#2a1d14", top="#5a3d2b", bottom="#2a2a30", shoes="#1a1a1a", stubble=True),
    "abe":     dict(long=True, hair="gray", hc="#bfb8ae", top="#56607a", bottom="#56607a", shoes="#1a1a1a", suit=True,
                    glasses=True),
    "valentina": dict(long=True, fem=True, hair="long", hc="#1a1210", top="#8e1f3c", bottom="#1a1a22", shoes="#1a1a1a",
                      ear="hoop"),
    "cordell": dict(hair="buzz", hc="#1d130e", top="#2c7a4b", bottom="#2a2a30", shoes="#ffffff", chain=True),
    "mendes":  dict(long=True, hair="slick", hc="#1d130e", top="#3a3226", bottom="#2a2a30", shoes="#1a1a1a", badge=True,
                    mustache=True),
    "giorgio": dict(long=True, hair="gray", hc="#9a948a", top="#f2efe6", bottom="#f2efe6", shoes="#c9a27a", suit=True),
    "camila":  dict(long=True, fem=True, hair="long", hc="#4a2e1c", top="#2f4c8a", bottom="#2f4c8a", shoes="#1a1a1a",
                    suit=True),
    "danica":  dict(long=True, fem=True, hair="long", hc="#e0c07a", top="#3c3f48", bottom="#3c3f48", shoes="#1a1a1a",
                    suit=True, glasses=True),
    "vinny":   dict(hair="short", hc="#2a1d14", top="#e6c34a", bottom="#38404f", shoes="#2a2a2a"),
    "liz":     dict(fem=True, hair="long", hc="#d8573c", top="#34a3a0", bottom="#2f3b55", shoes="#f2f2f2"),
    "mattia":  dict(hair="slick", hc="#14100e", top="#6a2a8a", bottom="#22222a", shoes="#1a1a1a", chain=True,
                    shades=True),
    "arnold":  dict(hair="short", hc="#7a5a3a", top="#9aa86a", bottom="#5a4a3a", shoes="#3b2a22", stubble=True),
    "aunt":    dict(fem=True, hair="curly", hc="#2a1a14", top="#e3893a", bottom="#e3893a", shoes="#6b3a2a",
                    dress=True, ear="hoop"),
    "counselor": dict(long=True, fem=True, hair="long", hc="#3a2a1e", top="#c8d2dc", bottom="#3b4256", shoes="#1a1a1a",
                      glasses=True),
    "masked":  dict(long=True, hair="mask", hc="#151518", top="#1d1d22", bottom="#1d1d22", shoes="#111111"),
}

# arm poses: (upper_angle, lower_angle) in degrees, 0 = straight down, + = outward, 180 = straight up
POSES = {
    "stand": dict(r=(12, 6), l=(12, 6)),
    "hips": dict(r=(48, -55), l=(48, -55)),
    "cross": dict(r=(22, -95), l=(22, -95), cross=True),
    "hold": dict(r=(18, -80), l=(18, -80)),
    "wave": dict(r=(135, 168), l=(12, 6)),
    "point": dict(r=(88, 92), l=(12, 6)),
    "pointl": dict(r=(12, 6), l=(88, 92)),
    "guard": dict(r=(28, 205), l=(28, 205)),
    "punch": dict(r=(92, 92), l=(28, 205)),
    "punchl": dict(r=(28, 205), l=(92, 92)),
    "raise": dict(r=(150, 172), l=(150, 172)),
    "shrug": dict(r=(62, 140), l=(62, 140)),
    "cry": dict(r=(30, 212), l=(30, 212)),
    "phone": dict(r=(26, 208), l=(12, 6)),
    "cuffed": dict(r=(-8, -20), l=(-8, -20), behind=True),
    "bag": dict(r=(14, 4), l=(12, 6)),
    "reach": dict(r=(70, 70), l=(70, 70)),
    "think": dict(r=(26, 200), l=(30, -80)),
    "fist": dict(r=(140, 175), l=(12, 6)),
    "walk": dict(r=(12, 6), l=(12, 6)),
    "sit": dict(r=(25, -60), l=(25, -60), sit=True),
    "sitcry": dict(r=(30, 212), l=(30, 212), sit=True),
    "drive": dict(r=(45, -70), l=(45, -70), sit=True),
    "hug": dict(r=(80, -30), l=(80, -30)),
    "gavel": dict(r=(120, 60), l=(30, -80)),
}


def _arm(c, sx, sy, a1, a2, side, L1, L2, w, col, skin, hand=True, wraps=False):
    def d(a):
        r = math.radians(a)
        return math.sin(r) * side, math.cos(r)
    dx, dy = d(a1)
    ex, ey = sx + dx * L1, sy + dy * L1
    dx2, dy2 = d(a2)
    hx, hy = ex + dx2 * L2, ey + dy2 * L2
    pth = skia.Path()
    pth.moveTo(sx, sy)
    pth.lineTo(ex, ey)
    pth.lineTo(hx, hy)
    c.drawPath(pth, P(OUT, w + OW * 2))
    sl = skia.Path()
    sl.moveTo(sx, sy)
    sl.lineTo(ex, ey)
    c.drawPath(pth, P(skin, w))
    c.drawPath(sl, P(col, w + 1))
    if hand:
        oval(c, hx, hy, w * 0.62, w * 0.62, "#e8e8e8" if wraps else skin, ow=OW * 0.8)
    return hx, hy


def _hair_back(c, style, hc, r, t):
    if style == "pony":
        sw = math.sin(t * 2.2) * 4
        pth = skia.Path()
        pth.moveTo(r * 0.55, -r * 0.55)
        pth.cubicTo(r * 1.25 + sw, -r * 0.4, r * 1.15 + sw, r * 0.6, r * 0.95 + sw, r * 1.05)
        pth.cubicTo(r * 0.75 + sw, r * 0.7, r * 0.75, r * 0.1, r * 0.45, -r * 0.2)
        pth.close()
        shape(c, pth, hc)
        oval(c, 0, -r * 0.05, r * 1.04, r * 1.02, hc)
    elif style in ("long", "braids"):
        pth = skia.Path()
        pth.moveTo(-r * 1.02, -r * 0.1)
        pth.lineTo(-r * 1.08, r * 1.35)
        pth.quadTo(0, r * 1.55, r * 1.08, r * 1.35)
        pth.lineTo(r * 1.02, -r * 0.1)
        pth.close()
        shape(c, pth, hc)
        if style == "braids":
            for k in range(-3, 4):
                line(c, k * r * 0.28, r * 0.6, k * r * 0.3, r * 1.4, mixhex(hc, "#000000", 0.4), 3)
    elif style == "curly":
        for i in range(14):
            a = i / 14 * math.tau
            oval(c, math.cos(a) * r * 0.98, math.sin(a) * r * 0.9 - r * 0.15, r * 0.38, r * 0.38, hc)
        oval(c, 0, -r * 0.1, r * 1.08, r * 1.0, hc, ow=0)
    elif style == "puffs":
        oval(c, -r * 0.95, -r * 0.75, r * 0.42, r * 0.42, hc)
        oval(c, r * 0.95, -r * 0.75, r * 0.42, r * 0.42, hc)
    elif style == "cal":
        oval(c, 0, -r * 0.05, r * 1.06, r * 1.0, hc)


def _hair_front(c, style, hc, r, t):
    def cap(top=-1.08, part=None):
        pth = skia.Path()
        pth.moveTo(-r * 1.0, -r * 0.05)
        pth.cubicTo(-r * 1.08, r * top, r * 1.08, r * top, r * 1.0, -r * 0.05)
        if part == "mid":
            pth.cubicTo(r * 0.9, -r * 0.55, r * 0.3, -r * 0.75, 0, -r * 0.62)
            pth.cubicTo(-r * 0.3, -r * 0.75, -r * 0.9, -r * 0.55, -r * 1.0, -r * 0.05)
        elif part == "side":
            pth.cubicTo(r * 0.85, -r * 0.5, r * 0.2, -r * 0.45, -r * 0.35, -r * 0.62)
            pth.cubicTo(-r * 0.7, -r * 0.5, -r * 0.95, -r * 0.4, -r * 1.0, -r * 0.05)
        else:
            pth.cubicTo(r * 0.7, -r * 0.62, -r * 0.7, -r * 0.62, -r * 1.0, -r * 0.05)
        pth.close()
        shape(c, pth, hc)

    if style in ("pony", "long", "braids"):
        cap(part="mid")
        if style == "pony":
            oval(c, r * 0.62, -r * 0.62, r * 0.16, r * 0.12, "#c0392b", ow=3)
    elif style == "puffs":
        cap(part="mid")
    elif style == "curly":
        for i in range(7):
            a = math.pi + i / 6 * math.pi
            oval(c, math.cos(a) * r * 0.78, math.sin(a) * r * 0.78 - r * 0.05, r * 0.3, r * 0.26, hc, ow=0)
    elif style in ("short", "jason"):
        cap(top=-1.15, part="side")
        if style == "jason":
            pth = skia.Path()
            pth.moveTo(-r * 0.4, -r * 0.92)
            pth.quadTo(r * 0.1, -r * 1.25, r * 0.55, -r * 0.88)
            pth.quadTo(r * 0.1, -r * 0.95, -r * 0.4, -r * 0.92)
            shape(c, pth, hc, ow=3)
    elif style == "buzz":
        pth = skia.Path()
        pth.moveTo(-r * 0.98, -r * 0.2)
        pth.cubicTo(-r * 1.0, -r * 1.12, r * 1.0, -r * 1.12, r * 0.98, -r * 0.2)
        pth.cubicTo(r * 0.7, -r * 0.6, -r * 0.7, -r * 0.6, -r * 0.98, -r * 0.2)
        shape(c, pth, hc, ow=3)
    elif style == "slick":
        cap(top=-1.2, part="side")
        line(c, -r * 0.3, -r * 0.8, r * 0.5, -r * 0.75, "#ffffff", 3, 0.35)
    elif style == "gray":
        cap(top=-1.05, part="side")
    elif style == "cal":
        cap(top=-1.1, part="side")
    elif style == "babycurl":
        pth = skia.Path()
        pth.moveTo(-r * 0.1, -r * 0.95)
        pth.cubicTo(-r * 0.05, -r * 1.35, r * 0.4, -r * 1.25, r * 0.25, -r * 1.0)
        c.drawPath(pth, P(OUT, 6))
        c.drawPath(pth, P(hc, 3))
    elif style == "cap":
        pth = skia.Path()
        pth.moveTo(-r * 1.02, -r * 0.3)
        pth.cubicTo(-r * 1.0, -r * 1.25, r * 1.0, -r * 1.25, r * 1.02, -r * 0.3)
        pth.close()
        shape(c, pth, hc)
        box(c, -r * 1.1, -r * 0.42, r * 2.2, r * 0.22, mixhex(hc, "#000000", 0.4), r=6)
        oval(c, 0, -r * 0.8, r * 0.16, r * 0.18, "#e8c25a", ow=3)
    elif style == "mask":
        pth = skia.Path()
        pth.addOval(skia.Rect(-r * 1.02, -r * 1.0, r * 1.02, r * 1.0))
        hole = skia.Path()
        hole.addRRect(skia.RRect.MakeRectXY(skia.Rect(-r * 0.62, -r * 0.25, r * 0.62, r * 0.18), r * 0.2, r * 0.2))
        m = skia.Op(pth, hole, skia.PathOp.kDifference_PathOp)
        shape(c, m, hc)
    elif style == "bald":
        line(c, -r * 0.35, -r * 0.65, -r * 0.1, -r * 0.8, "#ffffff", 4, 0.25)


LASH = [False]


def _eyes(c, r, expr, t, blink, look):
    lx, ly = look[0] * r * 0.06, look[1] * r * 0.05
    ey = -r * 0.02
    sep = r * 0.36
    for sx in (-1, 1):
        x = sx * sep + lx
        if blink or expr in ("happy", "laugh"):
            pth = skia.Path()
            if expr in ("happy", "laugh"):
                pth.moveTo(x - r * 0.13, ey + r * 0.04)
                pth.quadTo(x, ey - r * 0.12, x + r * 0.13, ey + r * 0.04)
            else:
                pth.moveTo(x - r * 0.12, ey)
                pth.lineTo(x + r * 0.12, ey)
            c.drawPath(pth, P(OUT, 5))
            continue
        ry = r * (0.17 if expr in ("shock", "scared") else 0.14)
        if LASH[0]:
            c.drawLine(x + sx * r * 0.08, ey + ly - ry * 0.7, x + sx * r * 0.17, ey + ly - ry * 1.0, P(OUT, 4))
        oval(c, x, ey + ly, r * 0.105, ry, "#1a110c", ow=0)
        c.drawCircle(x - r * 0.035 + lx * 0.2, ey + ly - ry * 0.45, r * 0.04, P("#ffffff"))
        c.drawCircle(x + r * 0.04, ey + ly + ry * 0.35, r * 0.018, P("#ffffff", a=0.8))
        if expr in ("cry", "sad") and expr == "cry":
            k = (t * 1.4 + (0.5 if sx > 0 else 0)) % 1
            pth = skia.Path()
            pth.addOval(skia.Rect.MakeXYWH(x - r * 0.05, ey + r * 0.15 + k * r * 0.45, r * 0.1, r * 0.14))
            c.drawPath(pth, P("#7fc8ff", a=1 - k))


def _brows(c, r, expr):
    by = -r * 0.27
    for sx in (-1, 1):
        x = sx * r * 0.36
        if expr in ("angry", "determined", "punch"):
            a, b = by - r * 0.02, by + r * 0.08
            c.drawLine(x - sx * r * 0.15, a, x + sx * r * 0.1, b, P(OUT, 7))
        elif expr in ("sad", "cry", "worried", "scared"):
            c.drawLine(x - sx * r * 0.14, by + r * 0.06, x + sx * r * 0.1, by - r * 0.04, P(OUT, 6))
        elif expr in ("shock",):
            c.drawLine(x - r * 0.12, by - r * 0.1, x + r * 0.12, by - r * 0.12, P(OUT, 6))
        elif expr in ("smirk",):
            yy = by - (r * 0.07 if sx > 0 else 0)
            c.drawLine(x - r * 0.12, yy, x + r * 0.12, yy, P(OUT, 6))
        else:
            c.drawLine(x - r * 0.12, by, x + r * 0.12, by - r * 0.02, P(OUT, 6))


def _mouth(c, r, expr, talk, t):
    my = r * 0.42
    op = 0.0
    if talk > 0:
        op = (0.5 + 0.5 * math.sin(t * 19)) * (0.6 + 0.4 * math.sin(t * 7.3)) * talk
    if expr in ("shock", "scared"):
        oval(c, 0, my, r * 0.1, r * 0.14 + op * r * 0.04, "#5a1e1e", ow=4)
        return
    if expr in ("happy", "laugh", "smile") or op > 0.15:
        o = max(op, 0.55 if expr == "laugh" else (0.35 if expr == "happy" else 0))
        if o > 0.1:
            pth = skia.Path()
            pth.moveTo(-r * 0.2, my - r * 0.04)
            pth.quadTo(0, my + r * (0.05 + 0.32 * o), r * 0.2, my - r * 0.04)
            pth.close()
            shape(c, pth, "#6a2222", ow=4)
            c.save()
            c.clipPath(pth)
            oval(c, 0, my + r * 0.22 * o + r * 0.05, r * 0.1, r * 0.06, "#e07070", ow=0)
            c.restore()
            return
        pth = skia.Path()
        pth.moveTo(-r * 0.17, my - r * 0.03)
        pth.quadTo(0, my + r * 0.12, r * 0.17, my - r * 0.03)
        c.drawPath(pth, P(OUT, 5))
        return
    pth = skia.Path()
    if expr in ("sad", "cry", "worried"):
        pth.moveTo(-r * 0.14, my + r * 0.05)
        pth.quadTo(0, my - r * 0.07, r * 0.14, my + r * 0.05)
    elif expr in ("angry", "determined", "punch"):
        pth.moveTo(-r * 0.14, my + r * 0.02)
        pth.lineTo(r * 0.14, my)
    elif expr == "smirk":
        pth.moveTo(-r * 0.12, my + r * 0.02)
        pth.quadTo(r * 0.08, my + r * 0.04, r * 0.18, my - r * 0.06)
    else:
        pth.moveTo(-r * 0.11, my)
        pth.quadTo(0, my + r * 0.05, r * 0.11, my)
    c.drawPath(pth, P(OUT, 5))


def head(c, who, look_key, r, expr="neutral", t=0.0, look=(0, 0), talk=0.0, blink_ok=True):
    L = LOOKS[look_key]
    if is_adult(look_key):
        from adult import a_head
        a_head(c, who, look_key, L, SKIN.get(who, "#c98a5e"), expr, t, look, talk, blink_ok, scale=r / 34)
        return
    skin = SKIN.get(who, SKIN.get(look_key.split("_")[0], "#c98a5e"))
    hc = L["hair"]
    _hair_back(c, hc, L["hc"], r, t)
    # ears
    for sx in (-1, 1):
        oval(c, sx * r * 0.98, r * 0.08, r * 0.17, r * 0.22, skin, ow=4)
        if L.get("ear") == "hoop":
            c.drawCircle(sx * r * 1.0, r * 0.42, r * 0.16, P("#e8b93a", 4))
        elif L.get("ear") == "stud":
            c.drawCircle(sx * r * 1.0, r * 0.28, r * 0.05, P("#e8e8e8"))
    oval(c, 0, 0, r, r * 0.97, skin)
    # cheeks
    c.drawCircle(-r * 0.55, r * 0.3, r * 0.13, P("#e0705a", a=0.22))
    c.drawCircle(r * 0.55, r * 0.3, r * 0.13, P("#e0705a", a=0.22))
    if L.get("stubble"):
        pth = skia.Path()
        pth.moveTo(-r * 0.75, r * 0.25)
        pth.quadTo(0, r * 1.15, r * 0.75, r * 0.25)
        pth.quadTo(0, r * 0.75, -r * 0.75, r * 0.25)
        c.drawPath(pth, P("#5b3a24", a=0.3))
    LASH[0] = L.get("fem", False)
    blink = blink_ok and ((t + (hsh(who) % 37) * 0.13) % 3.7) < 0.12
    if L.get("shades"):
        for sx in (-1, 1):
            box(c, sx * r * 0.36 - r * 0.24, -r * 0.16, r * 0.48, r * 0.3, "#101014", r=8, ow=3)
        line(c, -r * 0.12, -r * 0.05, r * 0.12, -r * 0.05, "#101014", 4)
    else:
        _eyes(c, r, expr, t, blink, look)
        if L.get("glasses"):
            for sx in (-1, 1):
                c.drawCircle(sx * r * 0.36, -r * 0.02, r * 0.2, P(OUT, 4))
            line(c, -r * 0.16, -r * 0.04, r * 0.16, -r * 0.04, OUT, 4)
    _brows(c, r, expr)
    # nose
    pth = skia.Path()
    pth.moveTo(-r * 0.05, r * 0.2)
    pth.quadTo(0, r * 0.26, r * 0.06, r * 0.2)
    c.drawPath(pth, P(mixhex(skin, "#000000", 0.45), 4))
    if L.get("mustache"):
        pth = skia.Path()
        pth.moveTo(-r * 0.26, r * 0.36)
        pth.quadTo(0, r * 0.2, r * 0.26, r * 0.36)
        pth.quadTo(0, r * 0.3, -r * 0.26, r * 0.36)
        shape(c, pth, L["hc"], ow=3)
    _mouth(c, r, expr, talk, t)
    _hair_front(c, hc, L["hc"], r, t)
    if hc not in ("bald", "cap", "babycurl"):
        pth = skia.Path()
        pth.moveTo(-r * 0.62, -r * 0.62)
        pth.quadTo(-r * 0.35, -r * 0.88, r * 0.0, -r * 0.9)
        c.drawPath(pth, P("#ffffff", 5, 0.22))


def is_adult(lk):
    L = LOOKS[lk]
    return not (L.get("baby") or L.get("small"))


def person(c, x, y, who="lucia", look_key=None, pose="stand", expr="neutral", t=0.0, s=1.0, look=(0, 0),
           talk=0.0, walk=0.0, flip=False, bob=True, a=1.0, label=None, label_a=1.0, prop=None):
    """Character with feet at (x, y). Kids/babies are chibi (~360 px at s=1); adults are realistic (~465 px)."""
    lk = look_key or who
    L = LOOKS[lk]
    skin = SKIN.get(who, "#c98a5e")
    if is_adult(lk):
        from adult import person_adult
        ps = POSES.get(pose, POSES["stand"])
        s *= 0.82
        if lk == "lucia_teen":
            s *= 0.93
        person_adult(c, x, y, who, lk, L, skin, ps, pose, expr, t, s, look, talk, walk, flip, bob, a, prop)
        if label:
            tag(c, x, y - 470 * s - 40, label, a=label_a * a)
        return
    if L.get("baby"):
        s *= 0.55
    elif L.get("small"):
        s *= 0.8
    ps = POSES.get(pose, POSES["stand"])
    sit = ps.get("sit")
    with xf(c, x, y, s=s, alpha=a, sx=-s if flip else None, sy=s if flip else None):
        breathe = math.sin(t * 2.4 + hsh(who)) * 2.5 if bob else 0
        wk = math.sin(walk * 9.0) if walk else 0
        hop = abs(math.sin(walk * 9.0)) * 8 if walk else 0
        c.translate(0, -hop)
        top_col = L["top"]
        bot = L["bottom"]
        # shadow
        c.drawOval(skia.Rect(-70, -10, 70, 12), P("#000000", a=0.18))
        # legs
        if sit:
            for sx in (-1, 1):
                box(c, sx * 26 - 15, -110, 30, 60, bot, r=12)
                box(c, sx * 26 - 15, -62, 30, 52, bot, r=12)
                oval(c, sx * 26, -8, 22, 12, L["shoes"], ow=4)
        elif L.get("baby"):
            for sx in (-1, 1):
                oval(c, sx * 26, -22, 26, 24, bot)
        else:
            for sx in (-1, 1):
                sw = wk * 14 * sx
                lx = sx * 24
                pth = skia.Path()
                pth.moveTo(lx, -100)
                pth.lineTo(lx + sw, -14)
                c.drawPath(pth, P(OUT, 30 + OW * 2))
                c.drawPath(pth, P(bot, 30))
                oval(c, lx + sw + sx * 6, -10, 25, 13, L["shoes"], ow=4)
        if L.get("dress"):
            pth = skia.Path()
            pth.moveTo(-52, -190)
            pth.lineTo(52, -190)
            pth.lineTo(74, -50)
            pth.quadTo(0, -38, -74, -50)
            pth.close()
            shape(c, pth, top_col)
            for k in range(5):
                c.drawCircle(-40 + k * 20, -70 - (k % 2) * 30, 6, P("#ffffff", a=0.35))
        # arms behind
        sh_y = -178 + breathe * 0.4
        sit_dy = 0
        L1, L2, aw = 52, 48, 24
        if ps.get("behind"):
            for side in (-1, 1):
                _arm(c, side * 44, sh_y, ps["r"][0], ps["r"][1], side, L1, L2, aw, top_col, skin)
        # torso
        if not L.get("dress"):
            pth = skia.Path()
            pth.moveTo(-50, -192 + breathe)
            pth.lineTo(50, -192 + breathe)
            pth.lineTo(56, -92)
            pth.quadTo(0, -84, -56, -92)
            pth.close()
            shape(c, pth, top_col)
            if L.get("baby"):
                pass
            elif L.get("jump"):
                line(c, 0, -180, 0, -95, mixhex(top_col, "#000000", 0.3), 3)
                box(c, 16, -165, 22, 16, mixhex(top_col, "#ffffff", 0.25), r=3, ow=3)
                T(c, "DOC", 27, -152, 9, OUT, "interb")
            else:
                box(c, -57, -100, 114, 14, bot, r=6, ow=4)
            if L.get("suit"):
                pth = skia.Path()
                pth.moveTo(-14, -192)
                pth.lineTo(0, -140)
                pth.lineTo(14, -192)
                pth.close()
                shape(c, pth, "#f2f2f2", ow=3)
                pth = skia.Path()
                pth.moveTo(-4, -180)
                pth.lineTo(4, -180)
                pth.lineTo(6, -130)
                pth.lineTo(0, -120)
                pth.lineTo(-6, -130)
                pth.close()
                shape(c, pth, "#a8282c" if lk != "dealer" else "#e3b13b", ow=2)
            if L.get("badge"):
                pth = skia.Path()
                for i in range(10):
                    rr = 12 if i % 2 == 0 else 6
                    ang = -math.pi / 2 + i * math.pi / 5
                    pt = (-26 + math.cos(ang) * rr, -160 + math.sin(ang) * rr)
                    pth.lineTo(*pt) if i else pth.moveTo(*pt)
                pth.close()
                shape(c, pth, "#e8c25a", ow=2)
            if L.get("chain"):
                pth = skia.Path()
                pth.moveTo(-26, -190)
                pth.quadTo(0, -140, 26, -190)
                c.drawPath(pth, P("#e8c25a", 5))
            if L.get("whistle"):
                line(c, -10, -190, 6, -150, "#d9d9d9", 2)
                box(c, 0, -155, 16, 10, "#c0c0c0", r=4, ow=2)
            # collar / neckline
            pth = skia.Path()
            pth.moveTo(-18, -192 + breathe)
            pth.quadTo(0, -170 + breathe, 18, -192 + breathe)
            c.drawPath(pth, P(skin))
            c.drawPath(pth, P(OUT, 3))
        # prop held in front (drawn between torso and arms)
        if prop:
            prop(c)
        # front arms
        if not ps.get("behind"):
            hands = []
            for side, key in ((1, "r"), (-1, "l")):
                a1, a2 = ps[key]
                if pose == "walk":
                    a1 += wk * 18 * side
                    a2 += wk * 18 * side
                if pose == "wave" and key == "r":
                    a2 += math.sin(t * 10) * 18
                if pose in ("punch", "punchl") and key == ("r" if pose == "punch" else "l"):
                    k = abs(math.sin(t * 5.5))
                    a1 = lerp(30, 92, k)
                    a2 = lerp(200, 92, k)
                hands.append(_arm(c, side * 46, sh_y, a1, a2, side, L1, L2, aw, top_col, skin,
                                  wraps=L.get("wraps")))
        # neck + head
        hr = 82
        with xf(c, 0, -262 + breathe):
            head(c, who, lk, hr, expr, t, look, talk)
    if label:
        tag(c, x, y - 380 * s - 40, label, a=label_a * a)


# ---------------------------------------------------------------- UI pieces
def tag(c, x, y, label, size=30, a=1.0, s=1.0, rot=0.0, bg="#ffffff", fg="#1a1a1a"):
    """White name tag with dark outline (like the reference)."""
    if a <= 0:
        return
    w = tw(label, size) + 34
    h = size * 1.45
    rot = rot + (1.0 - clamp(a)) * -16 + (s - 1.0) * 30
    with xf(c, x, y, s=s, rot=rot, alpha=a):
        box(c, -w / 2 + 4, -h / 2 + 5, w, h, "#000000", r=10, a=0.25, ow=0)
        box(c, -w / 2, -h / 2, w, h, bg, r=10, ow=4, oc="#141414")
        T(c, label, 0, size * 0.36, size, fg)


def speech(c, x, y, lines, size=30, a=1.0, s=1.0, tail=(-60, 90), bg="#ffffff", fg="#141414", hot=None):
    if a <= 0:
        return
    if isinstance(lines, str):
        lines = [lines]
    w = max(tw(l, size) for l in lines) + 60
    h = size * 1.25 * len(lines) + 40
    with xf(c, x, y, s=s, alpha=a):
        pth = skia.Path()
        pth.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), h * 0.32, h * 0.32))
        tp = poly([(-16, h / 2 - 6), (tail[0], h / 2 + tail[1] * 0.6), (18, h / 2 - 6)])
        pth2 = skia.Path()
        pth2.addPath(pth)
        u = skia.Op(pth, tp, skia.PathOp.kUnion_PathOp)
        box(c, -w / 2 + 6, -h / 2 + 8, w, h, "#000000", r=h * 0.32, a=0.22, ow=0)
        shape(c, u, bg, ow=5, oc="#141414")
        for i, l in enumerate(lines):
            col = hot if (hot and i == len(lines) - 1) else fg
            T(c, l, 0, -h / 2 + 20 + size * 0.95 + i * size * 1.25, size, col)


def stamp(c, x, y, label, size=70, a=1.0, s=1.0, rot=-10, color="#d8262e"):
    if a <= 0:
        return
    w = tw(label, size, LUCKY) + 50
    h = size * 1.35
    with xf(c, x, y, s=s, rot=rot, alpha=a * 0.92):
        rrect(c, -w / 2, -h / 2, w, h, 10, color, stroke=7)
        rrect(c, -w / 2 + 10, -h / 2 + 10, w - 20, h - 20, 6, color, stroke=3)
        T(c, label, 0, size * 0.38, size, color, LUCKY)


def marker_text(c, s, x, y, size=60, color="#e8282e", a=1.0, rot=-4, fam=MARKER, align="center"):
    """Hand-written marker text that writes on from left to right as `a` goes 0 -> 1."""
    if a <= 0:
        return
    w = tw(s, size, fam)
    x0 = x - w / 2 if align == "center" else (x - w if align == "right" else x)
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.clipRect(skia.Rect(x0 - x - 10, -size * 1.4, x0 - x + (w + 20) * clamp(a * 1.15), size * 0.6))
    c.drawString(s, x0 - x + size * 0.03, size * 0.05, F(fam, size), P("#000000", a=0.35))
    c.drawString(s, x0 - x, 0, F(fam, size), P(color))
    c.restore()


def marker_circle(c, x, y, rx, ry, prog=1.0, color="#e8282e", w=7, rot=-6):
    """Hand-drawn red marker ellipse that draws itself (overshoots its start like a real pen)."""
    if prog <= 0:
        return
    pth = skia.Path()
    n = 60
    end = int(n * 1.12 * clamp(prog)) + 1
    for i in range(end):
        a = -2.2 + i / n * math.tau
        wob = 1 + 0.04 * math.sin(i * 0.7) + 0.06 * (i / n)
        px = x + math.cos(a) * rx * wob
        py = y + math.sin(a) * ry * wob
        pth.lineTo(px, py) if i else pth.moveTo(px, py)
    with xf(c, x, y, rot=rot):
        c.translate(-x, -y)
        c.drawPath(pth, P(color, w))


def caption_serif(c, s, x, y, size=40, color="#f3e3c3", a=1.0):
    T(c, s, x, y, size, color, SERIF, a=a, shadow=0.5)


def polaroid(c, x, y, w, h, draw_inner, label="", a=1.0, rot=0.0, s=1.0, pin=True, label_col="#1d1d1d"):
    if a <= 0:
        return
    with xf(c, x, y, s=s, rot=rot, alpha=a):
        pad = 22
        rrect(c, -w / 2 + 10, -h / 2 + 14, w, h, 6, "#000000", 0.35)
        rrect(c, -w / 2, -h / 2, w, h, 6, "#f7f3ea")
        iw, ih = w - pad * 2, h - pad - 120
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(-w / 2 + pad, -h / 2 + pad, iw, ih))
        with xf(c, -w / 2 + pad, -h / 2 + pad):
            draw_inner(c, iw, ih)
        c.restore()
        c.drawRect(skia.Rect.MakeXYWH(-w / 2 + pad, -h / 2 + pad, iw, ih), P("#000000", 2, 0.4))
        if label:
            T(c, label, 0, h / 2 - 48, 48, label_col, MARKER, rot=-2)
        if pin:
            oval(c, 0, -h / 2 + 8, 16, 16, "#d8262e", ow=3)
            c.drawCircle(-5, -h / 2 + 3, 5, P("#ffffff", a=0.6))


def corner_tag(c, label, a=1.0):
    """Top-right chapter tag, e.g. 'GTA VI · LEONIDA'."""
    if a <= 0:
        return
    w = tw(label, 22) + 30
    with xf(c, W - 50 - w, 40, alpha=a):
        box(c, 0, 0, w, 40, "#101014", r=4, ow=3, oc="#f2f2f2")
        T(c, label, w / 2, 28, 22, "#f2f2f2")


# ---------------------------------------------------------------- props
def palm(c, x, y, s=1.0, t=0.0, col="#1e1530", trunk=None, a=1.0, sway=1.0):
    trunk = trunk or col
    with xf(c, x, y, s=s, alpha=a):
        sw = math.sin(t * 0.9 + x * 0.01) * 8 * sway
        pth = skia.Path()
        pth.moveTo(-9, 0)
        pth.cubicTo(-6, -200, 10 + sw * 0.5, -380, 18 + sw, -520)
        pth.lineTo(30 + sw, -520)
        pth.cubicTo(20 + sw * 0.5, -380, 8, -200, 9, 0)
        pth.close()
        c.drawPath(pth, P(trunk))
        cx, cy = 24 + sw, -522
        for i in range(9):
            ang = -math.pi + i / 8 * math.pi + math.sin(t * 1.3 + i) * 0.04 * sway
            L = 150 + (i % 3) * 22
            ex, ey = cx + math.cos(ang) * L, cy + math.sin(ang) * L * 0.45 + 60
            mx, my = cx + math.cos(ang) * L * 0.5, cy - 40 + math.sin(ang) * 30
            pth = skia.Path()
            pth.moveTo(cx, cy)
            pth.quadTo(mx, my - 18, ex, ey)
            pth.quadTo(mx, my + 14, cx, cy)
            c.drawPath(pth, P(col))


def palm_green(c, x, y, s=1.0, t=0.0):
    with xf(c, x, y, s=s):
        sw = math.sin(t * 0.9 + x * 0.01) * 6
        pth = skia.Path()
        pth.moveTo(-12, 0)
        pth.cubicTo(-8, -180, 6 + sw * 0.5, -330, 14 + sw, -460)
        pth.lineTo(30 + sw, -460)
        pth.cubicTo(20, -330, 10, -180, 12, 0)
        pth.close()
        shape(c, pth, "#9a6b45", ow=4)
        for k in range(10):
            yy = -40 - k * 42
            line(c, -8 + k * 1.5, yy, 10 + k * 1.8, yy - 6, "#6e4a2e", 3)
        cx, cy = 22 + sw, -462
        for i in range(8):
            ang = -math.pi + 0.15 + i / 7 * (math.pi - 0.3) + math.sin(t * 1.3 + i) * 0.04
            L = 170 + (i % 2) * 30
            ex, ey = cx + math.cos(ang) * L, cy + math.sin(ang) * L * 0.4 + 80
            mx, my = cx + math.cos(ang) * L * 0.55, cy - 45 + math.sin(ang) * 25
            pth = skia.Path()
            pth.moveTo(cx, cy)
            pth.quadTo(mx, my - 22, ex, ey)
            pth.quadTo(mx, my + 10, cx, cy)
            shape(c, pth, "#3f9b4f" if i % 2 else "#358645", ow=4)
        oval(c, cx - 8, cy + 8, 12, 12, "#6e4a2e", ow=3)
        oval(c, cx + 10, cy + 10, 12, 12, "#6e4a2e", ow=3)


def car(c, x, y, s=1.0, body="#d8262e", t=0.0, moving=0.0, kind="conv", flip=False, people=None, lights=0.0,
        a=1.0):
    """Side-view car, wheels on y. kind: conv (convertible), cop, sedan, van."""
    with xf(c, x, y, s=s, alpha=a, sx=-s if flip else None, sy=s if flip else None):
        bounce = math.sin(t * 22) * 2 * moving
        c.drawOval(skia.Rect(-270, -14, 270, 14), P("#000000", a=0.28))
        c.translate(0, bounce)
        if kind == "cop":
            body2 = "#f4f4f4"
        if people and kind == "conv":
            c.save()
            c.clipRect(skia.Rect(-400, -400, 400, -60))
            for px, who, lk, ex in people:
                with xf(c, px, -168):
                    head(c, who, lk, 52, ex, t)
            c.restore()
        pth = skia.Path()
        if kind == "conv":
            pth.moveTo(-260, -40)
            pth.lineTo(-255, -100)
            pth.quadTo(-200, -118, -90, -118)
            pth.lineTo(70, -118)
            pth.lineTo(120, -150)
            pth.lineTo(132, -150)
            pth.lineTo(110, -116)
            pth.quadTo(220, -112, 262, -86)
            pth.lineTo(268, -40)
            pth.close()
        else:
            pth.moveTo(-262, -40)
            pth.lineTo(-258, -100)
            pth.quadTo(-230, -112, -170, -114)
            pth.lineTo(-120, -178)
            pth.lineTo(80, -178)
            pth.lineTo(140, -114)
            pth.quadTo(230, -110, 262, -90)
            pth.lineTo(268, -40)
            pth.close()
        shape(c, pth, body if kind != "cop" else "#16161c")
        if kind == "cop":
            c.save()
            c.clipPath(pth)
            rect(c, -120, -180, 200, 140, "#f4f4f4")
            c.restore()
            c.drawPath(pth, P(OUT, OW))
            T(c, "POLICE", -20, -64, 30, "#16161c", "inter")
            box(c, -40, -196, 80, 18, "#16161c", r=4, ow=3)
            fl = (t * 6) % 2 < 1
            box(c, -40, -196, 38, 18, "#ff2a3a" if fl else "#5a1218", r=4, ow=3)
            box(c, 2, -196, 38, 18, "#2a6aff" if not fl else "#122050", r=4, ow=3)
            if moving or lights:
                glow(c, -20 if fl else 20, -188, 90, "#ff2a3a" if fl else "#2a6aff", 0.5)
        if kind != "conv":
            for wx0, wx1 in ((-112, -18), (-6, 74)):
                pw = poly([(wx0 + (6 if wx0 < -50 else 0), -168), (wx1, -168), (wx1 + (40 if wx1 > 50 else 0), -120),
                           (wx0 - (36 if wx0 < -50 else 0), -120)])
                shape(c, pw, "#9fd3ef", ow=4)
        else:
            line(c, -60, -118, -60, -60, mixhex(body, "#000000", 0.35), 4)
            line(c, 120, -118, 120, -60, mixhex(body, "#000000", 0.35), 4)
            box(c, -250, -78, 500, 8, mixhex(body, "#ffffff", 0.35), r=4, ow=0)
        box(c, 240, -78, 24, 14, "#fff2b0", r=4, ow=3)
        box(c, -268, -80, 18, 14, "#e23a3a", r=4, ow=3)
        if lights:
            cone = poly([(262, -76), (720, -150), (720, 10)])
            c.drawPath(cone, skia.Paint(AntiAlias=True, Shader=linear(260, 0, 720, 0, [("#fff6c8", 0.5 * lights),
                                                                                     ("#fff6c8", 0)])))
        box(c, 230, -52, 50, 14, "#c9c9c9", r=6, ow=3)
        box(c, -280, -52, 50, 14, "#c9c9c9", r=6, ow=3)
        for wx in (-165, 165):
            oval(c, wx, -38, 46, 46, "#1a1a1a")
            oval(c, wx, -38, 24, 24, "#c9c9c9", ow=3)
            ang = t * 30 * moving
            for k in range(5):
                aa = ang + k * math.tau / 5
                line(c, wx, -38, wx + math.cos(aa) * 20, -38 + math.sin(aa) * 20, "#8a8a8a", 3)
        if moving > 0.5:
            for k in range(5):
                yy = -150 + k * 28
                line(c, -330 - k * 30, yy, -440 - k * 50, yy, "#ffffff", 4, 0.5)


def baby_bundle(c, x, y, s=1.0, t=0.0, who="lucia", lk="lucia_baby", blanket="#f4a7c0", expr="smile"):
    with xf(c, x, y, s=s):
        oval(c, 0, 10, 60, 42, blanket)
        with xf(c, 0, -32):
            head(c, who, lk, 38, expr, t)


def cash(c, x, y, s=1.0, rot=0.0):
    with xf(c, x, y, s=s, rot=rot):
        box(c, -40, -20, 80, 40, "#6dbb63", r=4, ow=3)
        oval(c, 0, 0, 12, 12, "#8fd085", ow=2)
        T(c, "$", 0, 8, 22, "#2e6b2a", "inter")


def money_bag(c, x, y, s=1.0):
    with xf(c, x, y, s=s):
        pth = skia.Path()
        pth.moveTo(-18, -70)
        pth.lineTo(18, -70)
        pth.lineTo(10, -52)
        pth.cubicTo(70, -30, 70, 30, 0, 32)
        pth.cubicTo(-70, 30, -70, -30, -10, -52)
        pth.close()
        shape(c, pth, "#c9a86a")
        T(c, "$", 0, 14, 48, "#3b6b2a", "inter")


def bars(c, x0, x1, y0, y1, a=1.0, n=None, col="#7c8794"):
    n = n or int((x1 - x0) / 70)
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        box(c, x - 8, y0, 16, y1 - y0, col, r=6, a=a, ow=4)
        line(c, x - 3, y0 + 10, x - 3, y1 - 10, "#ffffff", 3, 0.3 * a)
    box(c, x0 - 20, y0 + 40, x1 - x0 + 40, 22, col, r=6, a=a, ow=4)
    box(c, x0 - 20, y1 - 80, x1 - x0 + 40, 22, col, r=6, a=a, ow=4)


def phone_prop(c, x, y, s=1.0, rot=0.0, screen="#1c2a4a", txt=None):
    with xf(c, x, y, s=s, rot=rot):
        box(c, -60, -110, 120, 220, "#151518", r=18)
        box(c, -50, -96, 100, 190, screen, r=8, ow=0)
        if txt:
            txt(c)


def speedlines(c, t, a=0.4, col="#ffffff"):
    rnd = random.Random(int(t * 12))
    for _ in range(26):
        ang = rnd.uniform(0, math.tau)
        r0 = rnd.uniform(420, 560)
        r1 = r0 + rnd.uniform(200, 500)
        line(c, W / 2 + math.cos(ang) * r0, H / 2 + math.sin(ang) * r0,
             W / 2 + math.cos(ang) * r1, H / 2 + math.sin(ang) * r1, col, rnd.uniform(3, 9), a)


def burst(c, x, y, r, col="#ffd23f", t=0.0, a=1.0, n=14):
    pts = []
    for i in range(n * 2):
        ang = i / (n * 2) * math.tau + t
        rr = r if i % 2 == 0 else r * 0.62
        pts.append((x + math.cos(ang) * rr, y + math.sin(ang) * rr))
    shape(c, poly(pts), col, a=a, ow=5)


def heart(c, x, y, s, col="#e8283a", a=1.0):
    with xf(c, x, y, s=s, alpha=a):
        pth = skia.Path()
        pth.moveTo(0, 30)
        pth.cubicTo(-60, -10, -30, -60, 0, -28)
        pth.cubicTo(30, -60, 60, -10, 0, 30)
        pth.close()
        shape(c, pth, col)
