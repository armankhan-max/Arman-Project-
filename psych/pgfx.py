"""Psych-documentary style kit: rim-lit 2D characters with real lip-sync, walk/run cycles, kinetic type.

Builds on the black-hole video kit (../blackhole/sgfx.py) so the look stays consistent:
black rim-lit heads, one outfit colour per character, blurred sets, film grain and vignette.

New here:
  * Full cast with identities (hair, outfits, glasses, beard, gown...).
  * Poses in "facing space": positive angles always point the way the character faces.
  * walk()/run() cycles whose ground speed is computed from the stride, so feet don't slide.
  * lip(t): mouth opening + roundness measured from the voiceover itself (lips.npy).
  * Display fonts (Bebas Neue for titles, Playfair Display for quotes) and word-synced quote reveals.
"""
import json
import math
import os
import random
import sys

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "blackhole"))
from sgfx import *  # noqa: F401,F403,E402
from sgfx import _seg  # noqa: E402
from gfx import typeface  # noqa: E402

GOLD = "#ffc56b"
DREAM = "#ffd98f"
COOL = "#7fb7d9"
RED = "#ff5a4f"
GREEN = "#5fd39a"
CREAM = "#f2ead6"

# ---------------------------------------------------------------- fonts
_tfx = {}
_fx = {}


def _typeface(kind):
    if kind not in _tfx:
        if kind == "bebas":
            _tfx[kind] = skia.Typeface.MakeFromFile(os.path.join(HERE, "fonts", "BebasNeue-Regular.ttf"))
        elif kind.startswith("play"):
            base = skia.Typeface.MakeFromFile(os.path.join(HERE, "fonts", "PlayfairDisplay.ttf"))
            wght = {"play": 500, "playb": 800}[kind]
            try:
                tag = skia.FourByteTag(*"wght") if hasattr(skia, "FourByteTag") else None
                coord = skia.FontArguments.VariationPosition.Coordinate(
                    tag if tag is not None else 0x77676874, wght)
                pos = skia.FontArguments.VariationPosition(
                    skia.FontArguments.VariationPosition.Coordinates([coord]))
                args = skia.FontArguments()
                args.setVariationDesignPosition(pos)
                _tfx[kind] = base.makeClone(args)
            except Exception:
                _tfx[kind] = base
        else:
            _tfx[kind] = typeface(f"Inter-{kind}.otf")
    return _tfx[kind]


def dfont(size, kind="bebas"):
    key = (kind, round(size, 1))
    if key not in _fx:
        f = skia.Font(_typeface(kind), size)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        f.setSubpixel(True)
        _fx[key] = f
    return _fx[key]


def dwidth(s, size, kind="bebas", track=0.0):
    return dfont(size, kind).measureText(s) + track * size * max(0, len(s) - 1)


def dtext(c, s, x, y, size, color="#ffffff", kind="bebas", align="center", a=1.0, track=0.0, shadow=0.0):
    f = dfont(size, kind)
    w = dwidth(s, size, kind, track)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    if a <= 0:
        return w
    if shadow:
        sp = P("#000000", a=shadow * a)
        sp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.08))
    if track == 0:
        if shadow:
            c.drawString(s, x + size * 0.03, y + size * 0.05, f, sp)
        c.drawString(s, x, y, f, P(color, a=a))
    else:
        xx = x
        for ch in s:
            if shadow:
                c.drawString(ch, xx + size * 0.03, y + size * 0.05, f, sp)
            c.drawString(ch, xx, y, f, P(color, a=a))
            xx += f.measureText(ch) + track * size
    return w


def soft(c, x, y, r, color, a=0.5, blur=None):
    p = P(color, a=a)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur or r * 0.5))
    c.drawCircle(x, y, r, p)


def soft_rect(c, x, y, w, h, color, a=0.5, blur=20, r=20):
    p = P(color, a=a)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), p)


def soft_stroke(c, path, color, w, a=0.6, blur=10):
    p = P(color, w, a)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    c.drawPath(path, p)


# ---------------------------------------------------------------- lip-sync + transcript
_LIPS = np.load(os.path.join(HERE, "lips.npy"))
TRANSCRIPT = json.load(open(os.path.join(HERE, "transcript.json")))
WORDS = [(w["w"].strip(), w["s"], w["e"]) for seg in TRANSCRIPT for w in seg["words"]]


def lip(t):
    """(open 0..1, round 0..1) for the narrator at time t, linearly interpolated between frames."""
    f = t * 30
    i = int(f)
    if i < 0 or i + 1 >= len(_LIPS):
        return 0.0, 0.0
    k = f - i
    a = _LIPS[i] * (1 - k) + _LIPS[i + 1] * k
    return float(a[0]), float(a[1])


def wt(word, near, end=False, span=4.0):
    """Exact timestamp of `word` spoken closest to `near` seconds."""
    best = None
    key = word.lower().strip(".,?!'\"")
    for w, s, e in WORDS:
        if w.lower().strip(".,?!'\"-") .startswith(key) and abs(s - near) <= span:
            if best is None or abs(s - near) < abs(best[0] - near):
                best = (s, e)
    if best is None:
        return near
    return best[1] if end else best[0]


def words_between(a, b):
    return [(w, s, e) for (w, s, e) in WORDS if s >= a - 0.05 and s < b]


# ---------------------------------------------------------------- cast
# top/top2 = outfit colours, legs, shoe, hair style, extras
CAST = {
    "leo": dict(skin="#c68a5e", hairc="#2a1d17", top="#2f8f86", top2="#226a63", legs="#3a4254", shoe="#ece8e0",
                hair="messy", kind="hoodie"),
    "hari": dict(skin="#b37a50", hairc="#d6d2cc", top="#a8cde0", top2="#86aec4", legs="#b37a50", shoe="#6b5442",
                 hair="gray_sides", mustache=True, kind="gown", old=True, grayhair=True),
    "nina": dict(skin="#e3b08a", hairc="#3a2418", top="#3fb58e", top2="#2f8f6e", legs="#3fb58e", shoe="#f0f0f0",
                 hair="ponytail", kind="scrubs"),
    "host": dict(skin="#d29a70", hairc="#b9b4ad", top="#8b5a3a", top2="#6e452b", legs="#3a3530", shoe="#3a2618",
                 hair="gray_sides", glasses=True, beard=True, kind="cardigan", collar="#e8e2d0", grayhair=True),
    "oet": dict(skin="#f0c9a8", hairc="#8a5a3a", top="#3d4a7a", top2="#2d3860", legs="#2d3860", shoe="#1d1d26",
                hair="bob", glasses=True, kind="blazer", collar="#f0ece2"),
    "gol": dict(skin="#efc3a0", hairc="#c9c4bb", top="#5d6470", top2="#464c57", legs="#2e3238", shoe="#1d1d26",
                hair="gray_sides", mustache=True, kind="blazer", collar="#dfe6ee", tie="#a83a3a", grayhair=True),
    "kap": dict(skin="#e9b996", hairc="#5a3420", top="#c0567a", top2="#9a4062", legs="#2b2b3a", shoe="#1d1d26",
                hair="ponytail", kind="blazer", collar="#f3e8ee"),
    "maya": dict(skin="#a8704a", hairc="#1e1412", top="#e0675a", top2="#b84f44", legs="#30334a", shoe="#e0675a",
                 hair="long", kind="tee"),
    "boss": dict(skin="#8a5a3a", hairc="#1a1412", top="#2f3542", top2="#232833", legs="#232833", shoe="#151515",
                 hair="short", tie="#e0b84a", kind="blazer", collar="#f0f0f0"),
    "ana": dict(skin="#d49a72", hairc="#3a2016", top="#8e5bd6", top2="#7045ae", legs="#d49a72", shoe="#ff4f7b",
                hair="long", kind="dress", heels=True),
    "sam": dict(skin="#7a4e30", hairc="#1a1210", top="#e0a23a", top2="#b88228", legs="#3a3f55", shoe="#f3f3f3",
                hair="curly", kind="tee"),
    "zed": dict(skin="#e8c09a", hairc="#6a4a2a", top="#4f7fd1", top2="#3d66ad", legs="#2c2f3d", shoe="#f3f3f3",
                hair="short", kind="tee"),
    "job": dict(skin="#c49070", hairc="#2a1d17", top="#7d8a99", top2="#646f7d", legs="#2c2f3d", shoe="#3a2c22",
                hair="short", kind="tee", stubble=True),
    "sir": dict(skin="#e8bc98", hairc="#2a1a14", top="#5a7a5a", top2="#465f46", legs="#2b2b3a", shoe="#1d1d26",
                hair="long", glasses=True, kind="blazer", collar="#f3efe6"),
    "pyc": dict(skin="#f0c8a4", hairc="#7a5a40", top="#4a5a7a", top2="#3a4762", legs="#2e3238", shoe="#1d1d26",
                hair="short", beard=True, kind="cardigan", collar="#e8e2d0"),
    "stud": dict(skin="#f0c8a0", hairc="#c9a050", top="#c9b458", top2="#a8953f", legs="#2c2f3d", shoe="#f3f3f3",
                 hair="messy", kind="tee"),
}

# poses in FACING space: (upper angle, elbow/knee relative angle); positive = toward where the character faces
POSES = {
    "stand": dict(fa=(8, 6), ba=(-8, 6), fl=(3, 0), bl=(-3, 0)),
    "point": dict(fa=(95, -5), ba=(-8, 6), fl=(3, 0), bl=(-3, 0)),
    "point_up": dict(fa=(150, 10), ba=(-8, 6), fl=(3, 0), bl=(-3, 0)),
    "present": dict(fa=(55, 55), ba=(-8, 6), fl=(3, 0), bl=(-3, 0)),
    "explain": dict(fa=(35, 75), ba=(-15, 40), fl=(3, 0), bl=(-3, 0)),
    "open": dict(fa=(60, 30), ba=(-60, -30), fl=(5, 0), bl=(-5, 0)),
    "think": dict(fa=(5, 160), ba=(15, 95), fl=(3, 0), bl=(-3, 0)),
    "write": dict(fa=(60, 30), ba=(45, 45), fl=(3, 0), bl=(-3, 0)),
    "cheer": dict(fa=(165, 10), ba=(-165, -10), fl=(6, 0), bl=(-6, 0)),
    "shrug": dict(fa=(60, 70), ba=(-60, -70), fl=(3, 0), bl=(-3, 0)),
    "headhold": dict(fa=(150, 70), ba=(-150, -70), fl=(3, 0), bl=(-3, 0)),
    "slump": dict(fa=(4, 0), ba=(-4, 0), fl=(3, 0), bl=(-3, 0)),
    "phone": dict(fa=(30, 105), ba=(-6, 8), fl=(3, 0), bl=(-3, 0)),
    "phone2": dict(fa=(30, 105), ba=(25, 95), fl=(3, 0), bl=(-3, 0)),
    "reach": dict(fa=(90, 0), ba=(-10, 8), fl=(3, 0), bl=(-3, 0)),
    "wave": dict(fa=(150, 30), ba=(-8, 6), fl=(3, 0), bl=(-3, 0)),
    "hold": dict(fa=(40, 60), ba=(-8, 6), fl=(3, 0), bl=(-3, 0)),
    "clip": dict(fa=(35, 75), ba=(-8, 6), fl=(3, 0), bl=(-3, 0)),
    "shake": dict(fa=(75, -5), ba=(-8, 6), fl=(3, 0), bl=(-3, 0)),
    "cross": dict(fa=(28, 105), ba=(22, 115), fl=(3, 0), bl=(-3, 0)),
    "sit": dict(fa=(40, 40), ba=(25, 40), fl=(85, -85), bl=(80, -80)),
    "sitdesk": dict(fa=(65, 25), ba=(55, 30), fl=(85, -85), bl=(80, -80)),
    "sitthink": dict(fa=(5, 160), ba=(40, 40), fl=(85, -85), bl=(80, -80)),
    "sitphone": dict(fa=(35, 100), ba=(25, 95), fl=(85, -85), bl=(80, -80)),
    "sitslump": dict(fa=(25, 20), ba=(15, 20), fl=(80, -70), bl=(75, -65)),
    "sittalk": dict(fa=(45, 70), ba=(25, 40), fl=(85, -85), bl=(80, -80)),
    "sithead": dict(fa=(150, 70), ba=(-150, -70), fl=(85, -85), bl=(80, -80)),
    "lie": dict(fa=(10, 0), ba=(-6, 0), fl=(2, 0), bl=(-2, 0)),
    "walker": dict(fa=(55, 15), ba=(50, 15), fl=(3, 0), bl=(-8, 0)),
}


def mix_pose(p1, p2, k):
    a = POSES[p1] if isinstance(p1, str) else p1
    b = POSES[p2] if isinstance(p2, str) else p2
    k = smooth(k)
    out = {key: (lerp(a[key][0], b[key][0], k), lerp(a[key][1], b[key][1], k)) for key in ("fa", "ba", "fl", "bl")}
    n1 = p1 if isinstance(p1, str) else p1.get("_name", "")
    n2 = p2 if isinstance(p2, str) else p2.get("_name", "")
    out["_name"] = n2 if k > 0.5 else n1
    return out


LEG1, LEG2 = 88, 82


def walk(t, freq=0.9, run=False):
    """Walk/run cycle. Returns (pose, bob, lean, ground_speed_px_per_s at s=1)."""
    p = t * freq * 2 * math.pi
    if run:
        A, K, Ar, El, lean, bobA = 38, 95, 55, 85, 10, 16
    else:
        A, K, Ar, El, lean, bobA = 24, 45, 26, 25, 2, 7
    pose = {}
    for key, ph in (("fl", p), ("bl", p + math.pi)):
        a1 = A * math.sin(ph)
        a2 = -(6 + K * max(0.0, math.cos(ph)) ** 1.3)
        pose[key] = (a1, a2)
    pose["fa"] = (-Ar * math.sin(p) + lean, El + (20 if run else 0))
    pose["ba"] = (-Ar * math.sin(p + math.pi) + lean, El + (20 if run else 0))
    bob = -bobA * abs(math.cos(p))
    L = LEG1 + LEG2 * 0.9
    speed = 4 * L * math.sin(math.radians(A)) * freq * (1.25 if run else 1.0)
    return pose, bob, lean, speed


# ---------------------------------------------------------------- drawing helpers
# Detailed 2D style: skin-toned faces, thick dark outlines, flat cel shading, five-finger hands.
OL = "#231c1f"


def shade(col, k=0.22):
    return mixhex(col, "#2a1830", k)


def hilite(col, k=0.18):
    return mixhex(col, "#fff4e0", k)


HANDS = {
    "point": ("point", "relax"), "point_up": ("point", "relax"), "present": ("open", "relax"),
    "explain": ("open", "relax"), "open": ("open", "open"), "cheer": ("fist", "fist"), "shrug": ("open", "open"),
    "wave": ("open", "relax"), "phone": ("grip", "relax"), "phone2": ("grip", "grip"), "sitphone": ("grip", "grip"),
    "hold": ("grip", "relax"), "clip": ("grip", "relax"), "write": ("grip", "relax"), "sitdesk": ("relax", "relax"),
    "shake": ("open", "relax"), "reach": ("open", "relax"), "think": ("fist", "relax"), "sitthink": ("fist", "relax"),
    "sittalk": ("open", "relax"), "walker": ("grip", "grip"), "headhold": ("open", "open"), "sithead": ("open", "open"),
}


def _capsule(c, x1, y1, x2, y2, w, col):
    c.drawLine(x1, y1, x2, y2, P(col, w))


def draw_hand(c, x, y, ang, s, skin, shape="relax", sgn=1, ow=3.0):
    """Hand at wrist (x, y); fingers point along `ang` (degrees from straight down, same as limbs)."""
    sk2 = shade(skin, 0.18)
    caps = []   # (x1, y1, x2, y2, w)
    blobs = []  # (rrect or circle) as ("rr", x, y, w, h, r) / ("c", x, y, r)
    lines = []
    if shape in ("fist", "grip"):
        blobs.append(("c", 0.0, s * 0.55, s * 0.62))
        for i in range(4):
            fx = -s * 0.42 + i * s * 0.28
            blobs.append(("c", fx, s * 1.0, s * 0.2))
        caps.append((s * 0.5, s * 0.25, s * 0.05, s * 0.75, s * 0.32))
    elif shape == "point":
        blobs.append(("c", 0.0, s * 0.55, s * 0.6))
        caps.append((s * 0.28, s * 0.7, s * 0.34, s * 1.85, s * 0.27))
        for i in range(3):
            fx = -s * 0.42 + i * s * 0.24
            blobs.append(("c", fx, s * 0.98, s * 0.19))
        caps.append((s * 0.5, s * 0.3, s * 0.2, s * 0.85, s * 0.3))
    else:
        spread = 14 if shape == "open" else 4
        blobs.append(("rr", -s * 0.55, -s * 0.1, s * 1.1, s * 1.0, s * 0.42))
        for i in range(4):
            a = math.radians((i - 1.5) * spread)
            fx = -s * 0.39 + i * s * 0.26
            L = s * (0.72 + (0.12 if i in (1, 2) else 0.0))
            caps.append((fx, s * 0.75, fx + math.sin(a) * L, s * 0.75 + math.cos(a) * L, s * 0.25))
        ta = math.radians(55 if shape == "open" else 30)
        caps.append((s * 0.45, s * 0.25, s * 0.45 + math.sin(ta) * s * 0.6, s * 0.25 + math.cos(ta) * s * 0.6,
                     s * 0.3))
    with xf(c, x, y, rot=-ang):
        c.scale(sgn, 1)
        for pass_ in (0, 1):
            col = OL if pass_ == 0 else skin
            add = ow * 2 if pass_ == 0 else 0
            for b in blobs:
                if b[0] == "c":
                    c.drawCircle(b[1], b[2], b[3] + add / 2, P(col))
                else:
                    _, bx, by, bw, bh, br = b
                    rrect(c, bx - add / 2, by - add / 2, bw + add, bh + add, br + add / 2, col)
            for (x1, y1, x2, y2, w) in caps:
                _capsule(c, x1, y1, x2, y2, w + add, col)
        # shading on the palm edge
        c.drawCircle(-s * 0.3, s * 0.45, s * 0.25, P(sk2, a=0.5))
        if shape in ("fist", "grip", "point"):
            for i in range(3 if shape != "point" else 2):
                fx = -s * 0.28 + i * s * 0.28
                c.drawLine(fx, s * 0.85, fx, s * 1.12, P(OL, max(1.2, ow * 0.5)))


def limb(c, x, y, a1, a2, l1, l2, w, col, face=1, end="hand", endc=INK, outline=OL, skin="#c68a5e",
         hand="relax", cuff=None, ow=4.5):
    x2, y2 = _seg(x, y, a1, l1)
    x3, y3 = _seg(x2, y2, a1 + a2, l2)
    pth = skia.Path()
    pth.moveTo(x, y)
    pth.lineTo(x2, y2)
    pth.lineTo(x3, y3)
    c.drawPath(pth, P(outline, w + ow * 2))
    c.drawPath(pth, P(col, w))
    # cel-shade stripe along one side
    ang = math.radians(a1 + a2)
    nx, ny = math.cos(ang), -math.sin(ang)
    off = w * 0.28 * -face
    sp = skia.Path()
    sp.moveTo(x2 + nx * off, y2 + ny * off)
    sp.lineTo(x3 + nx * off, y3 + ny * off)
    c.drawPath(sp, P(shade(col, 0.25), w * 0.3, 0.7))
    if cuff:
        cx_, cy_ = _seg(x2, y2, a1 + a2, l2 * 0.86)
        c.drawLine(cx_, cy_, x3, y3, P(cuff, w))
    if end == "hand":
        draw_hand(c, x3, y3, a1 + a2, w * 0.78, skin, hand, face, ow * 0.7)
    elif end in ("shoe", "heel"):
        with xf(c, x3, y3, rot=-math.degrees(ang)):
            c.scale(face, 1)
            if end == "heel":
                pp = poly([(-w * 0.5, -w * 0.3), (w * 1.2, w * 0.1), (w * 1.3, w * 0.5), (-w * 0.2, w * 0.55)])
                c.drawPath(pp, P(outline, ow * 1.6))
                c.drawPath(pp, P(endc))
                line(c, -w * 0.3, w * 0.4, -w * 0.35, w * 1.05, outline, 7)
                line(c, -w * 0.3, w * 0.4, -w * 0.35, w * 1.0, endc, 4)
            else:
                rrect(c, -w * 0.62 - ow, -w * 0.3 - ow, w * 1.95 + ow * 2, w * 0.95 + ow * 2, w * 0.42 + ow, outline)
                rrect(c, -w * 0.62, -w * 0.3, w * 1.95, w * 0.95, w * 0.42, endc)
                c.drawRect(skia.Rect(-w * 0.62, w * 0.42, w * 1.33, w * 0.65), P(shade(endc, 0.35)))
                line(c, w * 0.2, -w * 0.1, w * 0.75, -w * 0.05, shade(endc, 0.3), 3)
    return x3, y3


EXPR = {  # lid (0 open .. 1 shut), brow raise, brow angle, mouth
    "neutral": (0.25, 0.0, 0, "line"), "smile": (0.25, 0.05, 0, "smile"), "happy": (0.0, 0.1, 0, "grin"),
    "bliss": (1.0, 0.12, 0, "grin"), "laugh": (1.0, 0.15, 0, "laugh"), "dreamy": (0.5, 0.12, 0, "smile"),
    "proud": (0.35, 0.08, 0, "smirk"), "sad": (0.35, 0.05, 1, "frown"), "worried": (0.15, 0.1, 1, "worry"),
    "scared": (0.0, 0.22, 1, "o"), "wide": (0.0, 0.25, 0, "o"), "bored": (0.55, -0.02, 0, "flat"),
    "deadpan": (0.6, -0.04, 0, "flat"), "focus": (0.3, -0.03, 0, "line"), "angry": (0.3, -0.06, -1, "frown"),
    "tired": (0.6, 0.0, 1, "flat"), "closed": (1.0, 0.0, 0, "line"), "talk": (0.2, 0.06, 0, "line"),
}


def _eye(c, cx, cy, rx, ry, r, lid, look, face, skin, expr, angle_side, blink, hair_dark):
    lx, ly = look
    if lid >= 0.99 or blink:
        p = skia.Path()
        if expr in ("bliss", "laugh"):
            p.moveTo(cx - rx, cy + ry * 0.2)
            p.quadTo(cx, cy - ry * 0.9, cx + rx, cy + ry * 0.2)
        else:
            p.moveTo(cx - rx, cy)
            p.quadTo(cx, cy + ry * 0.6, cx + rx, cy)
        c.drawPath(p, P(OL, r * 0.055))
        return
    oval = skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry)
    c.drawOval(oval.makeOutset(r * 0.03, r * 0.03), P(OL))
    c.drawOval(oval, P("#fbf8f2"))
    c.save()
    c.clipRect(oval)
    ir = rx * (0.62 if expr not in ("scared", "wide") else 0.45)
    px = cx + clamp(lx + face * 0.25, -1, 1) * rx * 0.42
    py = cy + ly * ry * 0.35
    c.drawCircle(px, py, ir, P("#5b3a26"))
    c.drawCircle(px, py, ir * 0.58, P("#1b1210"))
    c.drawCircle(px + ir * 0.35, py - ir * 0.4, ir * 0.28, P("#ffffff"))
    if lid > 0:
        yl = cy - ry + 2 * ry * lid
        tilt_ = angle_side * ry * 0.5
        c.drawPath(poly([(cx - rx - 4, cy - ry - 4), (cx + rx + 4, cy - ry - 4), (cx + rx + 4, yl + tilt_),
                         (cx - rx - 4, yl - tilt_)]), P(skin))
        c.drawLine(cx - rx, yl - tilt_, cx + rx, yl + tilt_, P(OL, r * 0.045))
    c.restore()
    if lid <= 0:
        p = skia.Path()
        p.addArc(oval, 200, 140)
        c.drawPath(p, P(OL, r * 0.05))


def face_features(c, who, r, expr, t, look=(0, 0), face=1.0, talk=None, blink_seed=0.0):
    o = CAST[who]
    skin = o["skin"]
    hairc = o["hairc"]
    browc = mixhex(hairc, "#1a1010", 0.45 if o.get("grayhair") or hairc in ("#d6d2cc", "#b9b4ad", "#c9c4bb") else 0.1)
    lid, braise, bang, mouth = EXPR.get(expr, EXPR["neutral"])
    talking = talk is not None and talk[0] > 0.04
    if talking:
        braise += 0.06 * talk[0]
    ex0 = face * r * 0.2
    ey = r * 0.02
    bl_phase = (t * 0.27 + (sum(map(ord, who)) % 7) * 0.13 + blink_seed) % 1.0
    blink = bl_phase < 0.03 and expr not in ("wide", "scared")
    far = 1.0 - 0.18 * abs(face)
    for side in (-1, 1):
        k = far if side * face < 0 else 1.0
        cx = ex0 + side * r * 0.33 * (0.82 + 0.18 * (1 - abs(face))) * (1.0 if side * face > 0 else 0.92)
        rx, ry = r * 0.15 * k, r * 0.18
        if expr in ("scared", "wide"):
            rx, ry = rx * 1.12, ry * 1.12
        # lids slant: sad -> outer corners down (inner up); angry -> inner down
        angle_side = side * bang * 0.5
        _eye(c, cx, ey, rx, ry, r, lid, look, face, skin, expr, angle_side, blink, browc)
        # brows
        by = ey - ry - r * 0.12 - braise * r
        inner = cx - side * r * 0.12
        outer = cx + side * r * 0.14
        iy = by + bang * r * 0.07 * (-1 if bang > 0 else -1) * (1 if bang > 0 else -1)
        if bang > 0:      # worried: inner end up
            iy = by - r * 0.07
            oy = by + r * 0.03
        elif bang < 0:    # angry/focus: inner end down
            iy = by + r * 0.07
            oy = by - r * 0.02
        else:
            iy = oy = by
        bp = skia.Path()
        bp.moveTo(inner, iy)
        bp.quadTo((inner + outer) / 2, min(iy, oy) - r * 0.05, outer, oy)
        c.drawPath(bp, P(browc, r * 0.085))
    # nose
    nx = ex0 + face * r * 0.1
    np_ = skia.Path()
    np_.moveTo(nx - face * r * 0.02, ey + r * 0.06)
    np_.quadTo(nx + face * r * 0.2, ey + r * 0.3, nx - face * r * 0.04, ey + r * 0.34)
    c.drawPath(np_, P(OL, r * 0.045))
    c.drawCircle(nx + face * r * 0.02, ey + r * 0.3, r * 0.05, P(shade(skin, 0.25), a=0.6))
    # cheeks
    if expr in ("happy", "bliss", "laugh", "dreamy", "smile", "proud"):
        for side in (-1, 1):
            soft(c, ex0 + side * r * 0.42, ey + r * 0.32, r * 0.13, "#ff7a7a", 0.35, r * 0.06)
    if expr == "tired":
        for side in (-1, 1):
            p = skia.Path()
            cx = ex0 + side * r * 0.33
            p.addArc(skia.Rect(cx - r * 0.13, ey + r * 0.08, cx + r * 0.13, ey + r * 0.26), 20, 140)
            c.drawPath(p, P(shade(skin, 0.4), r * 0.03))
    # facial hair
    mx, my = ex0, ey + r * 0.56
    if o.get("beard"):
        bp = skia.Path()
        bp.moveTo(-r * 0.86, r * 0.0)
        bp.cubicTo(-r * 0.8, r * 0.75, -r * 0.4, r * 1.12, ex0 * 0.5, r * 1.1)
        bp.cubicTo(r * 0.4, r * 1.12, r * 0.8, r * 0.75, r * 0.86, r * 0.0)
        bp.cubicTo(r * 0.6, r * 0.45, ex0 + r * 0.3, r * 0.45, mx, my - r * 0.08)
        bp.cubicTo(ex0 - r * 0.3, r * 0.45, -r * 0.6, r * 0.45, -r * 0.86, r * 0.0)
        c.drawPath(bp, P(OL, r * 0.05))
        c.drawPath(bp, P(hairc))
    if o.get("stubble"):
        rnd = random.Random(7)
        for i in range(40):
            a = rnd.uniform(0.2, 2.9)
            rr = rnd.uniform(0.6, 0.9) * r
            c.drawCircle(math.cos(a) * rr * 0.85, r * 0.15 + math.sin(a) * rr * 0.9, r * 0.018,
                         P(shade(skin, 0.5), a=0.6))
    # mouth
    mw = r * 0.3
    if talking:
        op, rnd_ = talk
        w_ = r * (0.3 - 0.1 * rnd_) * (0.85 + 0.25 * op)
        h_ = r * (0.05 + 0.3 * op)
        rect = skia.Rect(mx - w_ / 2, my - h_ * 0.3, mx + w_ / 2, my + h_ * 0.7)
        rr_ = skia.RRect.MakeRectXY(rect, w_ * 0.45, h_ * 0.5)
        c.drawRRect(rr_, P(OL, r * 0.05))
        c.drawRRect(rr_, P("#5a1d24"))
        if op > 0.2:
            c.save()
            c.clipRRect(rr_, skia.ClipOp.kIntersect, True)
            c.drawRect(skia.Rect(rect.left(), rect.top(), rect.right(), rect.top() + h_ * 0.22), P("#fbf6ee"))
            c.drawOval(skia.Rect(mx - w_ * 0.32, rect.bottom() - h_ * 0.38, mx + w_ * 0.32, rect.bottom() + h_ * 0.2),
                       P("#d8646e"))
            c.restore()
    elif mouth in ("grin", "laugh"):
        h_ = r * (0.22 if mouth == "grin" else 0.32)
        p = skia.Path()
        p.moveTo(mx - mw * 0.75, my - r * 0.04)
        p.quadTo(mx, my + r * 0.02, mx + mw * 0.75, my - r * 0.04)
        p.quadTo(mx + mw * 0.6, my + h_, mx, my + h_)
        p.quadTo(mx - mw * 0.6, my + h_, mx - mw * 0.75, my - r * 0.04)
        p.close()
        c.drawPath(p, P(OL, r * 0.05))
        c.drawPath(p, P("#5a1d24"))
        c.save()
        c.clipPath(p, skia.ClipOp.kIntersect, True)
        c.drawRect(skia.Rect(mx - mw, my - r * 0.06, mx + mw, my + h_ * 0.3), P("#fbf6ee"))
        c.drawOval(skia.Rect(mx - mw * 0.4, my + h_ * 0.6, mx + mw * 0.4, my + h_ * 1.3), P("#d8646e"))
        c.restore()
    elif mouth in ("smile", "smirk"):
        p = skia.Path()
        if mouth == "smile":
            p.moveTo(mx - mw * 0.6, my - r * 0.02)
            p.quadTo(mx, my + r * 0.14, mx + mw * 0.6, my - r * 0.02)
        else:
            p.moveTo(mx - mw * 0.5, my + r * 0.02)
            p.quadTo(mx + mw * 0.1, my + r * 0.1, mx + face * mw * 0.65, my - r * 0.06)
        c.drawPath(p, P(OL, r * 0.055))
    elif mouth in ("frown", "worry"):
        p = skia.Path()
        p.moveTo(mx - mw * 0.5, my + r * 0.06)
        p.quadTo(mx, my - r * (0.06 if mouth == "frown" else 0.02), mx + mw * 0.5, my + r * 0.06)
        c.drawPath(p, P(OL, r * 0.05))
    elif mouth == "o":
        rect = skia.Rect(mx - r * 0.08, my - r * 0.06, mx + r * 0.08, my + r * 0.14)
        c.drawOval(rect.makeOutset(r * 0.025, r * 0.025), P(OL))
        c.drawOval(rect, P("#5a1d24"))
    elif mouth == "flat":
        line(c, mx - mw * 0.45, my + r * 0.02, mx + mw * 0.45, my + r * 0.02, OL, r * 0.05)
    else:
        p = skia.Path()
        p.moveTo(mx - mw * 0.45, my)
        p.quadTo(mx, my + r * 0.04, mx + mw * 0.45, my)
        c.drawPath(p, P(OL, r * 0.05))
    if o.get("mustache"):
        mp = skia.Path()
        mp.moveTo(mx - r * 0.32, my + r * 0.02)
        mp.quadTo(mx - r * 0.28, my - r * 0.2, mx, my - r * 0.13)
        mp.quadTo(mx + r * 0.28, my - r * 0.2, mx + r * 0.32, my + r * 0.02)
        mp.quadTo(mx, my - r * 0.05, mx - r * 0.32, my + r * 0.02)
        c.drawPath(mp, P(OL, r * 0.04))
        c.drawPath(mp, P(hairc))
    if o.get("glasses"):
        for side in (-1, 1):
            cx = ex0 + side * r * 0.33 * (0.82 + 0.18 * (1 - abs(face)))
            rr_ = skia.RRect.MakeRectXY(skia.Rect(cx - r * 0.24, ey - r * 0.22, cx + r * 0.24, ey + r * 0.2),
                                        r * 0.1, r * 0.1)
            c.drawRRect(rr_, P("#ffffff", a=0.12))
            c.drawRRect(rr_, P("#2b2324", r * 0.055))
            line(c, cx - r * 0.12, ey - r * 0.12, cx - r * 0.02, ey - r * 0.2, "#ffffff", r * 0.03, 0.5)
        line(c, ex0 - r * 0.09, ey - r * 0.05, ex0 + r * 0.09, ey - r * 0.05, "#2b2324", r * 0.05)
    if expr in ("worried", "scared"):
        ph = (t * 0.5) % 1.0
        drop(c, -face * r * 0.75, -r * 0.35 + ph * r * 0.3, r * 0.09, "#9fdcff", a=0.9)


def _face_path(r):
    p = skia.Path()
    p.moveTo(-r * 0.9, -r * 0.1)
    p.cubicTo(-r * 0.95, -r * 1.25, r * 0.95, -r * 1.25, r * 0.9, -r * 0.1)
    p.cubicTo(r * 0.88, r * 0.55, r * 0.45, r * 1.0, 0, r * 1.0)
    p.cubicTo(-r * 0.45, r * 1.0, -r * 0.88, r * 0.55, -r * 0.9, -r * 0.1)
    p.close()
    return p


def _outlined(c, path, col, ow):
    c.drawPath(path, P(OL, ow * 2))
    c.drawPath(path, P(col))


def draw_head(c, who, r, expr, t, look=(0, 0), face=1.0, talk=None, back_only=False):
    o = CAST[who]
    hs = o.get("hair")
    sgn = 1 if face >= 0 else -1
    skin, hairc = o["skin"], o["hairc"]
    ow = r * 0.065
    # back hair
    if hs == "long":
        p = skia.Path()
        p.moveTo(-r * 1.0, -r * 0.4)
        p.cubicTo(-r * 1.2, r * 0.6, -r * 1.2, r * 1.3, -r * 0.7, r * 1.45)
        p.lineTo(r * 0.7, r * 1.45)
        p.cubicTo(r * 1.2, r * 1.3, r * 1.2, r * 0.6, r * 1.0, -r * 0.4)
        p.close()
        _outlined(c, p, shade(hairc, 0.15), ow)
    elif hs == "bob":
        p = skia.Path()
        p.addRRect(skia.RRect.MakeRectXY(skia.Rect(-r * 1.12, -r * 1.12, r * 1.12, r * 0.85), r * 0.7, r * 0.7))
        _outlined(c, p, shade(hairc, 0.15), ow)
    elif hs == "ponytail":
        p = skia.Path()
        bx = -sgn * r * 0.95
        p.moveTo(bx, -r * 0.55)
        p.cubicTo(bx - sgn * r * 0.7, -r * 0.4, bx - sgn * r * 0.55, r * 0.7, bx - sgn * r * 0.2, r * 1.0)
        p.cubicTo(bx + sgn * r * 0.05, r * 0.5, bx + sgn * r * 0.1, -r * 0.1, bx, -r * 0.55)
        p.close()
        _outlined(c, p, hairc, ow)
        c.drawCircle(bx, -r * 0.45, r * 0.13, P(OL))
        c.drawCircle(bx, -r * 0.45, r * 0.09, P("#e05a6a"))
    if hs == "gray_sides":
        for side in (-1, 1):
            p = skia.Path()
            p.moveTo(side * r * 0.55, -r * 0.82)
            p.cubicTo(side * r * 1.15, -r * 0.7, side * r * 1.12, r * 0.1, side * r * 0.85, r * 0.42)
            p.lineTo(side * r * 0.6, r * 0.1)
            p.close()
            _outlined(c, p, hairc, ow)
            for k in range(3):
                line(c, side * r * (0.95 + 0.02 * k), -r * 0.45 + k * r * 0.2, side * r * 1.03, -r * 0.35 + k * r * 0.2,
                     shade(hairc, 0.25), r * 0.03)
    # ears
    for side in (-1, 1):
        ex = side * r * 0.88
        rect = skia.Rect(ex - r * 0.16, -r * 0.12, ex + r * 0.16, r * 0.3)
        c.drawOval(rect.makeOutset(ow, ow), P(OL))
        c.drawOval(rect, P(skin))
        c.drawArc(rect.makeInset(r * 0.06, r * 0.08), 90 - side * 60, 120, False, P(shade(skin, 0.3), r * 0.03))
    fp = _face_path(r)
    _outlined(c, fp, skin, ow)
    # cel shade on the side turned away from the light
    c.save()
    c.clipPath(fp, skia.ClipOp.kIntersect, True)
    c.drawOval(skia.Rect(-sgn * r * 1.55 - r * 0.6, -r * 1.3, -sgn * r * 1.55 + r * 0.6 + sgn * r * 0.25, r * 1.3),
               P(shade(skin, 0.2)))
    c.drawOval(skia.Rect(-r * 0.6, r * 0.75, r * 0.6, r * 1.2), P(shade(skin, 0.12), a=0.6))
    c.restore()
    # wrinkles for the older patient
    if o.get("old"):
        for i in range(2):
            p = skia.Path()
            p.moveTo(-r * 0.35, -r * 0.55 + i * r * 0.1)
            p.quadTo(0, -r * 0.62 + i * r * 0.1, r * 0.35, -r * 0.55 + i * r * 0.1)
            c.drawPath(p, P(shade(skin, 0.35), r * 0.025))
    # front hair
    if hs == "messy":
        pts = [(-r * 0.98, r * 0.05), (-r * 1.08, -r * 0.55), (-r * 0.8, -r * 1.05), (-r * 0.35, -r * 1.25),
               (r * 0.1, -r * 1.22), (r * 0.55, -r * 1.15), (r * 0.95, -r * 0.8), (r * 1.02, -r * 0.2),
               (r * 0.88, -r * 0.3), (r * 0.75, -r * 0.6), (r * 0.5, -r * 0.48), (r * 0.35, -r * 0.7),
               (r * 0.1, -r * 0.5), (-r * 0.15, -r * 0.72), (-r * 0.4, -r * 0.5), (-r * 0.6, -r * 0.7),
               (-r * 0.8, -r * 0.4), (-r * 0.86, -r * 0.05)]
        if sgn < 0:
            pts = [(-x, y) for x, y in pts]
        p = poly(pts)
        _outlined(c, p, hairc, ow)
        for i in range(3):
            line(c, sgn * (-r * 0.5 + i * r * 0.35), -r * 1.0, sgn * (-r * 0.35 + i * r * 0.35), -r * 0.75,
                 hilite(hairc, 0.25), r * 0.05)
    elif hs == "short":
        p = skia.Path()
        p.moveTo(-r * 0.95, -r * 0.05)
        p.cubicTo(-r * 1.05, -r * 1.3, r * 1.05, -r * 1.3, r * 0.95, -r * 0.05)
        p.lineTo(r * 0.85, -r * 0.35)
        p.cubicTo(r * 0.5, -r * 0.65, -sgn * r * 0.1, -r * 0.75, -r * 0.85, -r * 0.4)
        p.close()
        _outlined(c, p, hairc, ow)
        line(c, -sgn * r * 0.2, -r * 1.0, sgn * r * 0.3, -r * 0.85, hilite(hairc, 0.2), r * 0.05)
    elif hs == "curly":
        rnd = random.Random(3)
        cs = []
        for i in range(11):
            a = math.radians(-185 + i * 19)
            cs.append((math.cos(a) * r * 0.92, math.sin(a) * r * 0.92 - r * 0.05, r * rnd.uniform(0.24, 0.3)))
        for (x_, y_, rr) in cs:
            c.drawCircle(x_, y_, rr + ow, P(OL))
        for (x_, y_, rr) in cs:
            c.drawCircle(x_, y_, rr, P(hairc))
            c.drawArc(skia.Rect(x_ - rr * 0.6, y_ - rr * 0.6, x_ + rr * 0.6, y_ + rr * 0.6), 200, 120, False,
                      P(hilite(hairc, 0.3), r * 0.03))
    elif hs == "gray_sides":
        soft(c, sgn * r * 0.3, -r * 0.8, r * 0.18, "#ffffff", 0.25, r * 0.08)
    elif hs == "bob":
        p = skia.Path()
        p.moveTo(-r * 1.0, r * 0.1)
        p.cubicTo(-r * 1.15, -r * 1.25, r * 1.15, -r * 1.25, r * 1.0, r * 0.1)
        p.cubicTo(r * 0.9, -r * 0.3, r * 0.5, -r * 0.55, sgn * r * 0.2, -r * 0.62)
        p.cubicTo(-r * 0.3, -r * 0.45, -r * 0.8, -r * 0.4, -r * 1.0, r * 0.1)
        p.close()
        _outlined(c, p, hairc, ow)
    elif hs in ("ponytail", "long"):
        p = skia.Path()
        p.moveTo(-r * 0.98, r * 0.0)
        p.cubicTo(-r * 1.08, -r * 1.3, r * 1.08, -r * 1.3, r * 0.98, r * 0.0)
        p.cubicTo(r * 0.85, -r * 0.45, r * 0.35, -r * 0.7, sgn * r * 0.05, -r * 0.72)
        p.cubicTo(-r * 0.35, -r * 0.7, -r * 0.85, -r * 0.45, -r * 0.98, r * 0.0)
        p.close()
        _outlined(c, p, hairc, ow)
        line(c, -sgn * r * 0.1, -r * 1.0, sgn * r * 0.4, -r * 0.85, hilite(hairc, 0.25), r * 0.05)
    if not back_only:
        face_features(c, who, r, expr, t, look, face, talk)


def _torso(c, o, who, hw, tl, face, wm=1.0):
    kind = o.get("kind", "tee")
    sgn = 1 if face >= 0 else -1
    top, top2 = o["top"], o["top2"]
    ow = 4.5
    if kind == "hoodie":
        hp = skia.Path()
        hp.addRRect(skia.RRect.MakeRectXY(skia.Rect(-hw * 0.8, -tl - 22, hw * 0.8, -tl + 24), 24, 24))
        _outlined(c, hp, top2, ow)
    body = skia.Path()
    body.moveTo(-hw, -tl + 26)
    body.quadTo(-hw, -tl, -hw + 26, -tl)
    body.lineTo(hw - 26, -tl)
    body.quadTo(hw, -tl, hw, -tl + 26)
    body.lineTo(hw * 0.92, 2)
    body.quadTo(hw * 0.92, 10, hw * 0.92 - 10, 10)
    body.lineTo(-hw * 0.92 + 10, 10)
    body.quadTo(-hw * 0.92, 10, -hw * 0.92, 2)
    body.close()
    _outlined(c, body, top, ow)
    c.save()
    c.clipPath(body, skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect(-sgn * hw * 1.2, -tl, -sgn * hw * 0.55, 20) if sgn > 0 else
               skia.Rect(hw * 0.55, -tl, hw * 1.2, 20), P(shade(top, 0.22)))
    c.drawRect(skia.Rect(-hw, -8, hw, 12), P(shade(top, 0.15)))
    c.restore()
    if kind == "hoodie":
        pk = skia.Path()
        pk.addRRect(skia.RRect.MakeRectXY(skia.Rect(-hw * 0.6 + sgn * 6, -tl * 0.4, hw * 0.6 + sgn * 6, -tl * 0.1),
                                          14, 14))
        c.drawPath(pk, P(top2))
        c.drawPath(pk, P(OL, 3))
        for dx in (-10, 10):
            line(c, sgn * 8 + dx, -tl + 4, sgn * 8 + dx * 1.2, -tl * 0.7, OL, 6)
            line(c, sgn * 8 + dx, -tl + 4, sgn * 8 + dx * 1.2, -tl * 0.7, "#f0ece4", 3)
        c.drawRect(skia.Rect(-hw * 0.92, -2, hw * 0.92, 10), P(top2))
    elif kind == "gown":
        rnd = random.Random(2)
        for i in range(12):
            c.drawCircle(rnd.uniform(-hw * 0.8, hw * 0.8), rnd.uniform(-tl * 0.9, -tl * 0.1), 3.5, P(top2))
        p = skia.Path()
        p.addArc(skia.Rect(-hw * 0.4, -tl - 14, hw * 0.4, -tl + 22), 10, 160)
        c.drawPath(p, P(OL, 4))
    elif kind == "scrubs":
        c.drawPath(poly([(-hw * 0.35, -tl), (hw * 0.35, -tl), (0, -tl * 0.68)]), P(o["skin"]))
        c.drawPath(poly([(-hw * 0.35, -tl), (0, -tl * 0.68), (hw * 0.35, -tl)], False), P(OL, 4))
        rrect(c, sgn * hw * 0.3 - 15, -tl * 0.62, 30, 34, 5, top2)
        rrect(c, sgn * hw * 0.3 - 15, -tl * 0.62, 30, 34, 5, OL, stroke=3)
        line(c, sgn * hw * 0.3 - 4, -tl * 0.7, sgn * hw * 0.3 - 4, -tl * 0.56, "#2a6acf", 4)
    elif kind == "cardigan":
        c.drawPath(poly([(-hw * 0.42, -tl), (hw * 0.42, -tl), (0, -tl * 0.5)]), P(o["collar"]))
        c.drawPath(poly([(-hw * 0.42, -tl), (0, -tl * 0.5), (hw * 0.42, -tl)], False), P(OL, 4))
        c.drawPath(poly([(-hw * 0.42, -tl), (-hw * 0.1, -tl), (-hw * 0.2, -tl * 0.86)]), P("#ffffff"))
        c.drawPath(poly([(hw * 0.42, -tl), (hw * 0.1, -tl), (hw * 0.2, -tl * 0.86)]), P("#ffffff"))
        for k in range(3):
            c.drawCircle(0, -tl * 0.42 + k * tl * 0.14, 6, P(OL))
            c.drawCircle(0, -tl * 0.42 + k * tl * 0.14, 4, P("#d8b48a"))
        rrect(c, sgn * hw * 0.25 - 18, -tl * 0.32, 36, 26, 6, top2)
        rrect(c, sgn * hw * 0.25 - 18, -tl * 0.32, 36, 26, 6, OL, stroke=3)
    elif kind == "blazer":
        c.drawPath(poly([(-hw * 0.4, -tl), (hw * 0.4, -tl), (0, -tl * 0.45)]), P(o["collar"]))
        if o.get("tie"):
            tp = poly([(-7, -tl + 6), (7, -tl + 6), (11, -tl * 0.5), (0, -tl * 0.4), (-11, -tl * 0.5)])
            c.drawPath(tp, P(OL, 4))
            c.drawPath(tp, P(o["tie"]))
        for sd in (-1, 1):
            lp_ = poly([(sd * hw * 0.45, -tl), (sd * hw * 0.04, -tl * 0.45), (sd * hw * 0.3, -tl * 0.62)])
            c.drawPath(lp_, P(top2))
            c.drawPath(lp_, P(OL, 3.5))
        for k in range(2):
            c.drawCircle(sgn * 4, -tl * 0.34 + k * 34, 5.5, P(OL))
            c.drawCircle(sgn * 4, -tl * 0.34 + k * 34, 3.5, P("#c9a86a"))
        line(c, sgn * hw * 0.5, -tl * 0.72, sgn * hw * 0.75, -tl * 0.72, OL, 3)
    elif kind == "dress":
        c.drawRect(skia.Rect(-hw * 0.92, -tl * 0.32, hw * 0.92, -tl * 0.24), P(top2))
        p = skia.Path()
        p.addArc(skia.Rect(-hw * 0.45, -tl - 18, hw * 0.45, -tl + 26), 10, 160)
        c.drawPath(p, P(o["skin"]))
        c.drawPath(p, P(OL, 3.5))
    else:  # tee
        p = skia.Path()
        p.addArc(skia.Rect(-hw * 0.38, -tl - 16, hw * 0.38, -tl + 18), 10, 160)
        c.drawPath(p, P(o["skin"]))
        c.drawPath(p, P(OL, 4))
        line(c, -hw * 0.5, -tl * 0.55, -hw * 0.2, -tl * 0.5, shade(top, 0.25), 3)


def _figure(c, who, pose, expr, t, look, face, talk, tilt=0.0, lean=0.0, hold=None, back_hold=None):
    o = CAST[who]
    pname = pose if isinstance(pose, str) else pose.get("_name", "")
    p = POSES[pose] if isinstance(pose, str) else pose
    hf, hb = HANDS.get(pname, HANDS.get(pname.replace("sit_", ""), ("relax", "relax")))
    sgn = 1 if face >= 0 else -1
    tl, hw = 160, 48
    al1, al2 = 75, 70
    aw, lw = 25, 29
    hr = 58
    kind = o.get("kind")
    skin = o["skin"]
    legc = o["legs"]
    legc2 = shade(legc, 0.2)
    shoe = "heel" if o.get("heels") else "shoe"
    a1, a2 = p["bl"]
    limb(c, -sgn * hw * 0.38, -6, a1 * sgn, a2 * sgn, LEG1, LEG2, lw, legc2, sgn, shoe, o["shoe"])
    if kind not in ("gown",):
        a1, a2 = p["fl"]
        limb(c, sgn * hw * 0.38, -6, a1 * sgn, a2 * sgn, LEG1, LEG2, lw, legc, sgn, shoe, o["shoe"])
    with xf(c, 0, 0, rot=lean * sgn):
        a1, a2 = p["ba"]
        bh = limb(c, -sgn * hw * 0.78, -tl + 24, a1 * sgn, a2 * sgn, al1, al2, aw, shade(o["top"], 0.15), sgn,
                  "hand", skin=shade(skin, 0.1), hand=hb, cuff=shade(o["top2"], 0.15))
        if back_hold:
            back_hold(c, *bh)
        if kind in ("gown", "dress"):
            wid = 12 if kind == "gown" else 30
            bot = 104 if kind == "gown" else 84
            sk = poly([(-hw * 0.92, -20), (hw * 0.92, -20), (hw + wid, bot), (-hw - wid, bot)])
            _outlined(c, sk, o["top"], 4.5)
            c.save()
            c.clipPath(sk, skia.ClipOp.kIntersect, True)
            c.drawRect(skia.Rect(-sgn * 200, -20, -sgn * hw * 0.3, bot + 10) if sgn > 0 else
                       skia.Rect(hw * 0.3, -20, 200, bot + 10), P(shade(o["top"], 0.2)))
            c.restore()
            if kind == "gown":
                rnd = random.Random(40)
                for i in range(7):
                    c.drawCircle(rnd.uniform(-hw * 0.8, hw * 0.8), rnd.uniform(0, 90), 3.5, P(o["top2"]))
        # neck
        nk = skia.Path()
        nk.addRect(skia.Rect(-13, -tl - 26, 13, -tl + 6))
        _outlined(c, nk, shade(skin, 0.15), 4)
        _torso(c, o, who, hw, tl, face)
        hy = -tl - hr * 0.92
        with xf(c, 0, hy + 40, rot=tilt * sgn):
            with xf(c, 0, -40):
                draw_head(c, who, hr, expr, t, look, face, talk)
        a1, a2 = p["fa"]
        fh = limb(c, sgn * hw * 0.78, -tl + 24, a1 * sgn, a2 * sgn, al1, al2, aw, o["top"], sgn, "hand", skin=skin,
                  hand=hf, cuff=o["top2"])
        if hold:
            hold(c, *fh)
    if kind == "gown":
        a1, a2 = p["fl"]
        limb(c, sgn * hw * 0.38, -6, a1 * sgn, a2 * sgn, LEG1, LEG2, lw, legc, sgn, shoe, o["shoe"])
    return fh, hy, hr


def person(c, x, y, who="leo", pose="stand", expr="neutral", t=0.0, s=1.0, look=(0, 0), face=1.0, talk=None,
           rot=0.0, rim=None, rim_off=(-4, -4), alpha=1.0, tilt=0.0, lean=0.0, hold=None, back_hold=None,
           tint_col=None, tint_a=0.0, shadow=True, chair=True):
    """Character with hip centre at (x, y). Feet rest ~170*s below y. talk = (open, round) or None."""
    if rim is None:
        rim = RIM_DEFAULT
    pname = pose if isinstance(pose, str) else pose.get("_name", "")
    if chair and pname.startswith("sit") and abs(rot) < 20:
        draw_chair(c, x, y, s, 1 if face >= 0 else -1, alpha)
    if shadow and abs(rot) < 30:
        c.drawOval(skia.Rect(x - 90 * s, y + 158 * s, x + 90 * s, y + 184 * s), P("#000000", a=0.3 * alpha))
    bounds = skia.Rect(x - 700 * s, y - 1100 * s, x + 700 * s, y + 900 * s)
    if alpha < 0.999:
        c.saveLayerAlpha(bounds, int(clamp(alpha) * 255))
    group = tint_a > 0 or bool(rim)
    if group:
        c.saveLayer(bounds, None)
    with xf(c, x, y, s, rot):
        res = _figure(c, who, pose, expr, t, look, face, talk, tilt, lean, hold, back_hold)
    if rim:
        # painted rim light INSIDE the figure: (silhouette - silhouette shifted away from the light),
        # composited onto the figure only (SrcATop) - the lit edge glows like the reference art.
        dx, dy = rim_off[0] * s * 2.8, rim_off[1] * s * 2.8
        ix, iy = rim_off[0] * s * 1.15, rim_off[1] * s * 1.15
        c.saveLayer(bounds, skia.Paint(BlendMode=skia.BlendMode.kSrcATop))
        c.saveLayer(bounds, skia.Paint(ColorFilter=skia.ColorFilters.Blend(C(rim, 0.8), skia.BlendMode.kSrcIn)))
        with xf(c, x - ix, y - iy, s, rot):
            _figure(c, who, pose, expr, t, look, face, None, tilt, lean)
        c.restore()
        c.saveLayer(bounds, skia.Paint(BlendMode=skia.BlendMode.kDstOut))
        with xf(c, x - dx, y - dy, s, rot):
            _figure(c, who, pose, expr, t, look, face, None, tilt, lean)
        c.restore()
        c.restore()
    if tint_a > 0:
        tp = skia.Paint(BlendMode=skia.BlendMode.kSrcATop)
        tp.setColor(C(tint_col, tint_a))
        c.drawRect(bounds, tp)
    if group:
        c.restore()
    if alpha < 0.999:
        c.restore()
    return res


RIM_DEFAULT = "#ffc887"


def draw_chair(c, x, y, s, sgn, alpha=1.0, col="#6a4630"):
    with xf(c, x, y, s, alpha=alpha):
        bx = -sgn * 62
        for pass_, cc_, add in ((0, OL, 8), (1, col, 0)):
            c.drawLine(bx, -170, bx, 170, P(cc_, 16 + add))
            c.drawLine(sgn * 70, 20, sgn * 70, 170, P(cc_, 14 + add))
            c.drawLine(bx * 0.5, 20, bx * 0.6, 170, P(cc_, 12 + add))
        rrect(c, -sgn * 75 - (0 if sgn > 0 else 0) - 4, 4, 0, 0, 0, col)
        seat = skia.Rect(min(bx, sgn * 90) - 6, 6, max(bx, sgn * 90) + 6, 30)
        c.drawRRect(skia.RRect.MakeRectXY(seat.makeOutset(4, 4), 8, 8), P(OL))
        c.drawRRect(skia.RRect.MakeRectXY(seat, 6, 6), P(hilite(col, 0.1)))
        back = skia.Rect(bx - 14, -175, bx + 14, -60)
        c.drawRRect(skia.RRect.MakeRectXY(back.makeOutset(4, 4), 8, 8), P(OL))
        c.drawRRect(skia.RRect.MakeRectXY(back, 6, 6), P(col))


def bust(c, x, y, who, expr, t, s=1.0, look=(0, 0), face=1.0, talk=None, rim=None, tilt=0.0, pose="stand",
         hold=None):
    person(c, x, y, who, pose, expr, t, s, look, face, talk, rim=rim, tilt=tilt, hold=hold, shadow=False)


# ---------------------------------------------------------------- kinetic type
def kword(c, t, start, s, x, y, size, color="#ffffff", kind="bebas", end=None, style="rise", track=0.04,
          shadow=0.6, a=1.0):
    """Animated word/phrase. styles: rise, pop, slam, type, wipe."""
    if t < start:
        return 0
    out = 1.0 if end is None else clamp((end - t) / 0.3)
    if out <= 0:
        return 0
    k = at(t, start, 0.5)
    if style == "rise":
        e = ease_out(k)
        dtext(c, s, x, y + (1 - e) * size * 0.5, size, color, kind, a=a * clamp(k * 2) * out, track=track,
              shadow=shadow)
    elif style == "pop":
        e = back_out(at(t, start, 0.35))
        with xf(c, x, y - size * 0.35, max(0.01, e)):
            dtext(c, s, 0, size * 0.35, size, color, kind, a=a * out * clamp(k * 3), track=track, shadow=shadow)
    elif style == "slam":
        kk = at(t, start, 0.22)
        sc = lerp(2.4, 1.0, ease_out(kk))
        with xf(c, x, y - size * 0.35, sc):
            dtext(c, s, 0, size * 0.35, size, color, kind, a=a * out * clamp(kk * 2), track=track, shadow=shadow)
    elif style == "type":
        n = int(len(s) * clamp((t - start) / max(0.3, len(s) * 0.045)))
        w = dtext(c, s[:n], x - dwidth(s, size, kind, track) / 2, y, size, color, kind, "left", a * out, track,
                  shadow)
        if n < len(s) and int(t * 3) % 2 == 0:
            xx = x - dwidth(s, size, kind, track) / 2 + w + 6
            c.drawRect(skia.Rect(xx, y - size * 0.75, xx + size * 0.06, y + size * 0.05), P(color, a=a * out))
    elif style == "wipe":
        e = ease_out(at(t, start, 0.6))
        w = dwidth(s, size, kind, track)
        c.save()
        c.clipRect(skia.Rect(x - w / 2 - 20, y - size * 1.2, x - w / 2 - 20 + (w + 40) * e, y + size * 0.4))
        dtext(c, s, x, y, size, color, kind, a=a * out, track=track, shadow=shadow)
        c.restore()
    return 1


def underline(c, t, start, x, y, w, color=GOLD, th=8, dur=0.5, a=1.0):
    e = ease_out(at(t, start, dur))
    if e > 0:
        rrect(c, x - w / 2, y, w * e, th, th / 2, color, a)


def strike(c, t, start, x, y, w, color=RED, th=12, dur=0.35):
    e = ease_out(at(t, start, dur))
    if e > 0:
        line(c, x - w / 2, y + 6, x - w / 2 + w * e, y - 6, color, th)


def stamp(c, t, start, s, x, y, color=RED, size=120, rot=-8, end=None):
    if t < start:
        return
    out = 1.0 if end is None else clamp((end - t) / 0.25)
    k = at(t, start, 0.18)
    sc = lerp(2.2, 1.0, ease_out(k))
    w = dwidth(s, size, "bebas", 0.06) + 70
    with xf(c, x, y, sc, rot, alpha=clamp(k * 2) * out):
        rrect(c, -w / 2, -size * 0.72, w, size * 1.2, 16, color, stroke=10)
        rrect(c, -w / 2 + 14, -size * 0.72 + 14, w - 28, size * 1.2 - 28, 10, color, 0.75, 3)
        dtext(c, s, 0, size * 0.33, size, color, "bebas", track=0.06)


def chapter(c, t, start, num, title, end, color=GOLD):
    """Netflix-style chapter card: thin rule, chapter number, big tracked title."""
    k = at(t, start, 0.8)
    out = clamp((end - t) / 0.5)
    a = clamp(k * 1.5) * out
    if a <= 0:
        return
    fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, W * 0.7, ["#14100c", "#050505"]))
    for i in range(18):
        rnd = random.Random(i * 7)
        bx = rnd.uniform(0, W)
        by = rnd.uniform(0, H)
        soft(c, bx + math.sin(t * 0.3 + i) * 20, by - (t - start) * rnd.uniform(5, 20), rnd.uniform(20, 70),
             color, 0.05 * a, rnd.uniform(15, 30))
    e = ease_out(k)
    dtext(c, f"CHAPTER {num}", W / 2, H / 2 - 90, 40, color, "SemiBold", a=a, track=0.5)
    rrect(c, W / 2 - 220 * e, H / 2 - 55, 440 * e, 3, 1.5, color, a)
    dtext(c, title, W / 2, H / 2 + 80 + (1 - e) * 20, 150, "#f6efe2", "bebas", a=a, track=0.08, shadow=0.6)


def lower(c, t, start, name, role, color=GOLD, x=110, y=850, dur=4.5):
    k = ease_out(at(t, start, 0.6))
    out = clamp((start + dur - t) / 0.4)
    if k <= 0 or out <= 0:
        return
    w = max(dwidth(name, 70, "bebas", 0.04), dwidth(role.upper(), 26, "SemiBold", 0.12)) + 60
    with xf(c, x, y, alpha=k * out):
        soft_rect(c, -20, -20, w + 60, 170, "#000000", 0.45, 30)
        rrect(c, 0, 0, 6, 120 * k, 3, color)
        c.save()
        c.clipRect(skia.Rect(0, -20, 30 + w * k, 160))
        dtext(c, name, 30, 70, 70, "#ffffff", "bebas", "left", track=0.04)
        dtext(c, role.upper(), 32, 108, 26, color, "SemiBold", "left", track=0.12)
        c.restore()


def year_badge(c, t, start, year, x, y, color=GOLD, size=110, end=None):
    if t < start:
        return
    out = 1.0 if end is None else clamp((end - t) / 0.3)
    k = at(t, start, 0.7)
    y0 = int(year) - 40
    v = int(lerp(y0, int(year), ease_out(k)))
    with xf(c, x, y, alpha=clamp(k * 3) * out):
        dtext(c, str(v), 0, 0, size, color, "bebas", track=0.05, shadow=0.5)
        rrect(c, -size * 0.9 * ease_out(k), size * 0.18, size * 1.8 * ease_out(k), 4, 2, color)


FIX = {"Urtingen": "Oettingen", "Urtingen's": "Oettingen's", "Dreading": "Oettingen's", "in's": "",
       "Siroas": "Sirois", "Feigl": "Pychyl", "Seigl": "Pychyl", "whoop,": "WOOP:", "Goal": "Gollwitzer",
       "witzer": ""}


def quote(c, t, a, b, x, y, maxw, size=64, color="#f6efe2", hi=GOLD, kind="play", end=None, lead=None,
          fixes=None, line_h=1.32, align="center"):
    """Reveal the spoken words between a and b, word-synced, wrapped to maxw. Current word glows gold."""
    ws = words_between(a, b)
    fx = dict(FIX)
    if fixes:
        fx.update(fixes)
    toks = []
    for w, s, e in ws:
        w2 = fx.get(w, w)
        if w2:
            toks.append((w2, s, e))
    if lead:
        toks = [(lead, a, a)] + toks
    f = dfont(size, kind)
    sp = f.measureText(" ")
    lines, cur, cw = [], [], 0
    for tok in toks:
        ww = f.measureText(tok[0])
        if cur and cw + sp + ww > maxw:
            lines.append((cur, cw))
            cur, cw = [], 0
        cur.append((tok, ww))
        cw += (sp if cw else 0) + ww
    if cur:
        lines.append((cur, cw))
    out = 1.0 if end is None else clamp((end - t) / 0.4)
    y0 = y - (len(lines) - 1) * size * line_h / 2
    for li, (ln, lw) in enumerate(lines):
        xx = x - lw / 2 if align == "center" else x
        yy = y0 + li * size * line_h
        for (w, s, e), ww in ln:
            k = clamp((t - s + 0.08) / 0.25)
            if k > 0:
                speaking = s - 0.05 <= t <= e + 0.25
                col = hi if speaking else color
                with xf(c, 0, (1 - ease_out(k)) * 14):
                    if speaking:
                        soft(c, xx + ww / 2, yy - size * 0.3, ww * 0.6, hi, 0.12 * out, 20)
                    c.drawString(w, xx, yy, f, P(col, a=k * out))
            xx += ww + sp


# ---------------------------------------------------------------- scene-wide looks
def grade(c, kind, a=1.0):
    """Colour grade overlay: dream = warm golden bloom; cold = blue reality; fear = red."""
    if kind == "dream":
        p = skia.Paint(BlendMode=skia.BlendMode.kScreen)
        p.setShader(radial(W / 2, H * 0.35, W * 0.8, [("#ffcf7a", 0.28 * a), ("#ff9f5a", 0.08 * a), ("#000000", 0)]))
        c.drawRect(skia.Rect(0, 0, W, H), p)
    elif kind == "cold":
        p = skia.Paint(BlendMode=skia.BlendMode.kMultiply)
        p.setColor(C("#9cc3ff", 0.25 * a))
        c.drawRect(skia.Rect(0, 0, W, H), p)
    elif kind == "fear":
        p = skia.Paint(BlendMode=skia.BlendMode.kMultiply)
        p.setColor(C("#ff6a5a", 0.3 * a))
        c.drawRect(skia.Rect(0, 0, W, H), p)


def bokeh(c, t, color=GOLD, n=26, seed=1, a=0.25, speed=12, rmin=10, rmax=60):
    rnd = random.Random(seed)
    for i in range(n):
        bx = rnd.uniform(0, W)
        by = rnd.uniform(0, H)
        r = rnd.uniform(rmin, rmax)
        sp = rnd.uniform(0.4, 1.2) * speed
        yy = (by - t * sp) % (H + 200) - 100
        xx = bx + math.sin(t * 0.4 + i) * 30
        tw = 0.6 + 0.4 * math.sin(t * 1.3 + i * 2.1)
        soft(c, xx, yy, r, color, a * tw, r * 0.35)


def thought_bubbles(c, x0, y0, x1, y1, t, a=1.0, color="#fff2d6"):
    for i, k in enumerate((0.15, 0.4, 0.68)):
        x = lerp(x0, x1, k)
        y = lerp(y0, y1, k) + math.sin(t * 2 + i) * 4
        r = 10 + i * 9
        soft(c, x, y, r + 10, GOLD, 0.25 * a, 12)
        c.drawCircle(x, y, r, P(color, a=a))


def dream_frame(c, cx, cy, rx, ry, t, draw_fn, k=1.0):
    """Cloud-edged golden 'dream window'. k animates it open."""
    if k <= 0:
        return
    e = back_out(k) if k < 1 else 1.0
    path = skia.Path()
    path.addOval(skia.Rect(cx - rx * e, cy - ry * e, cx + rx * e, cy + ry * e))
    for i in range(14):
        ang = i / 14 * 2 * math.pi + t * 0.05
        bx = cx + math.cos(ang) * rx * e * 0.95
        by = cy + math.sin(ang) * ry * e * 0.95
        rr = (0.16 + 0.05 * math.sin(i * 2.3 + t)) * min(rx, ry) * e
        path.addCircle(bx, by, rr)
    soft_stroke(c, path, GOLD, 30, 0.5 * clamp(k * 2), 30)
    c.save()
    c.clipPath(path, skia.ClipOp.kIntersect, True)
    draw_fn(c)
    grade(c, "dream", 1.0)
    c.restore()
    c.drawPath(path, P("#fff2d6", 6, 0.9 * clamp(k * 2)))


def flash(c, t, at_, color="#fff4dc", dur=0.5, a=0.9):
    d = t - at_
    if -0.08 < d < dur:
        k = clamp(1 - d / dur) if d >= 0 else clamp(1 + d / 0.08)
        c.drawRect(skia.Rect(0, 0, W, H), P(color, a=a * k * k))


def letterbox(c, k=1.0, h=90):
    if k > 0:
        c.drawRect(skia.Rect(0, 0, W, h * k), P("#000000"))
        c.drawRect(skia.Rect(0, H - h * k, W, H), P("#000000"))


# marks sized in "units" (1.0 ~ 90 px) instead of raw pixels
from gfx import check_mark as _ck, cross_mark as _cx  # noqa: E402


def check_mark(c, x, y, s, color="#5fd39a", a=1.0, prog=1.0):
    _ck(c, x, y, s * 90, color, a, prog)


def cross_mark(c, x, y, s, color="#ff5a4f", a=1.0):
    _cx(c, x, y, s * 90, color, a)
