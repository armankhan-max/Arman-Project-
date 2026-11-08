"""Original crime-game style human characters (2D, flat-shaded, rim-lit). Fully code-drawn.

Proportions are realistic-ish (small head, shoulders, real clothes) instead of stickmen.
The pose system reuses the (angle1, angle2) limb tables from sgfx.POSES, so every pose
name used by the scenes keeps working: angle 0 points straight down, positive swings forward.
"""
import math

import skia

from gfx import C, P, xf, rrect, poly, line, clamp, mixhex
import sgfx
from sgfx import POSES

OUT = "#0c0910"

# Each look: skin, hair (style, color), top (style, colors), pants, shoes, extras.
LOOKS = {
    # the lead: bleached crop, pink floral shirt, white pants, aviators
    "hero": dict(skin="#c68a5e", hair=("crop", "#e8d38a"), top=("floral", "#ff5d8f", "#ffd23f"),
                 pants="#ece6da", shoes="#f2f2f2", shades=True, chain=True, stubble=True),
    "buyer": dict(skin="#8d5a3b", hair=("curly", "#1b120d"), top=("tee", "#ff4f8b"), pants="#2c3a5a",
                  shoes="#ffffff"),
    "buyer2": dict(skin="#e0ac84", hair=("ponytail", "#6a3b1f"), top=("crop", "#ff9a3c"), pants="#3b2f5a",
                   shoes="#ff5d8f", female=True),
    "buyer3": dict(skin="#b77a52", hair=("cap", "#2a2140", "#7a6cff"), top=("hoodie", "#7a6cff"), pants="#1e2230",
                   shoes="#e8e8e8"),
    "gamer": dict(skin="#d39a72", hair=("messy", "#2b1a10"), top=("hoodie", "#3a7bff"), pants="#22262f",
                  shoes="#ff3d8b", glasses=True),
    "parent": dict(skin="#a8704c", hair=("bun", "#241510"), top=("blazer", "#6c5ce7", "#f2efe6"), pants="#2a2540",
                   shoes="#14121a", female=True),
    "teen": dict(skin="#e3b08a", hair=("messy", "#8a4b22"), top=("tee", "#ff7a3c"), pants="#3a4a6a",
                 shoes="#ffffff", small=True),
    "ceo": dict(skin="#e2b38e", hair=("slick", "#8f8f96"), top=("suit", "#262a36", "#e9e3d2", "#c8324a"),
                pants="#1e212b", shoes="#0e0e12", glasses=True),
    # extra original cast for street scenes
    "nova": dict(skin="#9c6644", hair=("bob", "#18d6c3"), top=("jacket", "#1b1b26", "#ff3d8b"), pants="#2a2140",
                 shoes="#ffffff", female=True, shades=True),
    "cop": dict(skin="#c48c64", hair=("cap", "#141a2e", "#141a2e"), top=("uniform", "#26345a", "#d6b84a"),
                pants="#1c2440", shoes="#0e0e12", shades=True),
}


def _seg(x, y, ang, L):
    r = math.radians(ang)
    return x + math.sin(r) * L, y + math.cos(r) * L


def _limb(c, x, y, a1, a2, l1, l2, w1, w2, col1, col2, end=None, endc="#000000", endw=None):
    x2, y2 = _seg(x, y, a1, l1)
    x3, y3 = _seg(x2, y2, a1 + a2, l2)
    p1 = skia.Path()
    p1.moveTo(x, y)
    p1.lineTo(x2, y2)
    p2 = skia.Path()
    p2.moveTo(x2, y2)
    p2.lineTo(x3, y3)
    c.drawPath(p2, P(OUT, w2 + 6))
    c.drawPath(p1, P(OUT, w1 + 6))
    c.drawPath(p2, P(col2, w2))
    c.drawPath(p1, P(col1, w1))
    if end == "hand":
        c.drawCircle(x3, y3, w2 * 0.72 + 3, P(OUT))
        c.drawCircle(x3, y3, w2 * 0.72, P(endc))
    elif end == "shoe":
        ang = math.radians(a1 + a2)
        with xf(c, x3, y3, rot=-math.degrees(ang)):
            ew = endw or w2
            rrect(c, -ew * 0.6 - 3, -ew * 0.35 - 3, ew * 1.9 + 6, ew * 0.85 + 6, ew * 0.4, OUT)
            rrect(c, -ew * 0.6, -ew * 0.35, ew * 1.9, ew * 0.85, ew * 0.38, endc)
            rrect(c, -ew * 0.6, ew * 0.25, ew * 1.9, ew * 0.22, ew * 0.1, "#ffffff", 0.6)
    return x3, y3


def _face(c, L, r, expr, t, face, talk, who):
    skin = L["skin"]
    f = face
    # ear
    c.drawOval(skia.Rect(-f * r * 0.98 - r * 0.18, -r * 0.1, -f * r * 0.98 + r * 0.18, r * 0.32), P(OUT))
    c.drawOval(skia.Rect(-f * r * 0.98 - r * 0.14, -r * 0.06, -f * r * 0.98 + r * 0.14, r * 0.28),
               P(mixhex(skin, "#000000", 0.12)))
    # head shape: slightly long oval with jaw
    head = skia.Path()
    head.addOval(skia.Rect(-r * 0.92, -r * 1.08, r * 0.92, r * 1.0))
    c.drawPath(head, P(OUT, 6))
    c.drawPath(head, P(skin))
    # shading on the back side
    c.save()
    c.clipPath(head, skia.ClipOp.kIntersect, True)
    c.drawOval(skia.Rect(-f * r * 1.6 - r, -r * 1.4, -f * r * 1.6 + r, r * 1.4), P(mixhex(skin, "#2a1030", 0.25),
                                                                                   a=0.6))
    if L.get("stubble"):
        c.drawOval(skia.Rect(-r * 0.7 + f * r * 0.12, r * 0.25, r * 0.7 + f * r * 0.12, r * 1.15),
                   P(mixhex(skin, "#2a1a10", 0.35), a=0.5))
    c.restore()
    cx = f * r * 0.22
    ey = -r * 0.12
    blink = ((t * 0.31 + (len(who) % 5) * 0.21) % 1.0) < 0.035 and expr not in ("wide", "scared")
    # brows
    bw = r * 0.26
    for side in (-1, 1):
        bx = cx + side * r * 0.32
        tilt = 0
        if expr == "angry":
            tilt = side * 0.35
        elif expr in ("sad", "worried", "scared"):
            tilt = -side * 0.3
        line(c, bx - bw / 2, ey - r * 0.28 - tilt * bw * 0.5, bx + bw / 2, ey - r * 0.28 + tilt * bw * 0.5,
             mixhex(L["hair"][1], "#000000", 0.3), r * 0.09)
    if L.get("shades"):
        sp = skia.Path()
        sp.moveTo(cx - r * 0.62, ey - r * 0.12)
        sp.lineTo(cx + r * 0.66, ey - r * 0.12)
        sp.lineTo(cx + r * 0.6, ey + r * 0.12)
        sp.quadTo(cx + r * 0.36, ey + r * 0.3, cx + r * 0.1, ey + r * 0.1)
        sp.lineTo(cx - r * 0.08, ey + r * 0.1)
        sp.quadTo(cx - r * 0.34, ey + r * 0.3, cx - r * 0.58, ey + r * 0.12)
        sp.close()
        c.drawPath(sp, P("#0d0d14"))
        line(c, cx - r * 0.45, ey - r * 0.04, cx - r * 0.25, ey - r * 0.04, "#ffffff", r * 0.05, 0.6)
        line(c, -f * r * 0.85, ey - r * 0.05, cx - f * r * 0.6, ey - r * 0.1, "#0d0d14", r * 0.06)
    else:
        for side in (-1, 1):
            ex = cx + side * r * 0.32
            if blink or expr in ("happy", "laugh"):
                pth = skia.Path()
                if expr in ("happy", "laugh") and not blink:
                    pth.moveTo(ex - r * 0.13, ey + r * 0.03)
                    pth.quadTo(ex, ey - r * 0.12, ex + r * 0.13, ey + r * 0.03)
                else:
                    pth.moveTo(ex - r * 0.13, ey)
                    pth.lineTo(ex + r * 0.13, ey)
                c.drawPath(pth, P(OUT, r * 0.07))
            else:
                big = 1.3 if expr in ("wide", "scared") else 1.0
                c.drawOval(skia.Rect(ex - r * 0.14 * big, ey - r * 0.1 * big, ex + r * 0.14 * big, ey + r * 0.1 * big),
                           P("#fbf7f0"))
                pr = r * (0.055 if expr == "scared" else 0.075)
                c.drawCircle(ex + f * r * 0.04, ey + r * 0.01, pr, P("#1a1210"))
        if L.get("glasses"):
            for side in (-1, 1):
                ex = cx + side * r * 0.32
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(ex - r * 0.22, ey - r * 0.16, ex + r * 0.22, ey + r * 0.16),
                                                  r * 0.06, r * 0.06), P("#15151c", r * 0.06))
            line(c, cx - r * 0.1, ey, cx + r * 0.1, ey, "#15151c", r * 0.05)
    # nose
    nx = cx + f * r * 0.2
    pth = skia.Path()
    pth.moveTo(nx - f * r * 0.02, ey + r * 0.02)
    pth.lineTo(nx + f * r * 0.12, ey + r * 0.32)
    pth.lineTo(nx - f * r * 0.04, ey + r * 0.36)
    c.drawPath(pth, P(mixhex(skin, "#000000", 0.35), r * 0.05))
    # mouth
    my = r * 0.55
    mx = cx + f * r * 0.04
    op = 0.0
    if talk > 0:
        op = abs(math.sin(t * 13)) * talk
    mp = skia.Path()
    lip = "#5a2a2a"
    if expr == "laugh" or op > 0.35:
        h = r * (0.26 if expr == "laugh" else 0.1 + 0.2 * op)
        mp.moveTo(mx - r * 0.24, my - r * 0.03)
        mp.quadTo(mx, my - r * 0.06, mx + r * 0.24, my - r * 0.03)
        mp.quadTo(mx, my + h * 1.6, mx - r * 0.24, my - r * 0.03)
        c.drawPath(mp, P("#3a0d14"))
        c.drawRect(skia.Rect(mx - r * 0.16, my - r * 0.04, mx + r * 0.16, my + r * 0.04), P("#ffffff", a=0.9))
    elif expr in ("happy", "smile"):
        mp.moveTo(mx - r * 0.24, my - r * 0.05)
        mp.quadTo(mx, my + r * 0.2, mx + r * 0.24, my - r * 0.05)
        c.drawPath(mp, P(lip, r * 0.07))
    elif expr in ("sad", "worried"):
        mp.moveTo(mx - r * 0.2, my + r * 0.08)
        mp.quadTo(mx, my - r * 0.1, mx + r * 0.2, my + r * 0.08)
        c.drawPath(mp, P(lip, r * 0.07))
    elif expr in ("wide", "scared"):
        c.drawOval(skia.Rect(mx - r * 0.1, my - r * 0.08, mx + r * 0.1, my + r * 0.16), P("#3a0d14"))
    elif expr == "angry":
        mp.moveTo(mx - r * 0.22, my + r * 0.06)
        mp.lineTo(mx + r * 0.22, my + r * 0.02)
        c.drawPath(mp, P(lip, r * 0.08))
    else:
        mp.moveTo(mx - r * 0.18, my)
        mp.quadTo(mx, my + r * 0.04, mx + r * 0.18, my)
        c.drawPath(mp, P(lip, r * 0.07))


def _hair_back(c, L, r, face):
    style, col = L["hair"][0], L["hair"][1]
    if style == "ponytail":
        pth = skia.Path()
        pth.moveTo(-face * r * 0.7, -r * 0.5)
        pth.cubicTo(-face * r * 1.7, -r * 0.4, -face * r * 1.6, r * 0.9, -face * r * 1.05, r * 1.4)
        pth.cubicTo(-face * r * 1.2, r * 0.6, -face * r * 1.0, 0, -face * r * 0.6, -r * 0.1)
        pth.close()
        c.drawPath(pth, P(OUT, 6))
        c.drawPath(pth, P(col))
    elif style == "bob":
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-r * 1.08, -r * 1.05, r * 1.08, r * 0.62), r * 0.5, r * 0.5),
                    P(OUT))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-r * 1.04, -r * 1.02, r * 1.04, r * 0.58), r * 0.48, r * 0.48),
                    P(col))
    elif style == "bun":
        c.drawCircle(-face * r * 0.55, -r * 1.05, r * 0.42, P(OUT))
        c.drawCircle(-face * r * 0.55, -r * 1.05, r * 0.38, P(col))
    elif style == "curly":
        for i in range(9):
            a = math.pi * (1.05 + i / 8 * 0.95)
            c.drawCircle(math.cos(a) * r * 0.85, math.sin(a) * r * 0.85 - r * 0.15, r * 0.36, P(OUT))
        for i in range(9):
            a = math.pi * (1.05 + i / 8 * 0.95)
            c.drawCircle(math.cos(a) * r * 0.85, math.sin(a) * r * 0.85 - r * 0.15, r * 0.32, P(col))


def _hair_front(c, L, r, face):
    style, col = L["hair"][0], L["hair"][1]
    pth = skia.Path()
    if style in ("crop", "slick", "messy", "ponytail", "bun", "bob"):
        pth.moveTo(-r * 0.95, -r * 0.15)
        pth.cubicTo(-r * 1.05, -r * 1.25, r * 1.05, -r * 1.35, r * 0.95, -r * 0.25)
        if style == "messy":
            for i in range(5):
                x = r * (0.8 - i * 0.38) * face
                pth.lineTo(x, -r * (0.55 + 0.12 * (i % 2)))
        elif style == "bob":
            pth.quadTo(face * r * 0.2, -r * 0.75, -face * r * 0.2 if face < 0 else -r * 0.4, -r * 0.55)
        else:
            pth.quadTo(face * r * 0.4, -r * 0.9 if style == "crop" else -r * 0.75, -face * r * 0.4, -r * 0.62)
        pth.lineTo(-face * r * 0.9, -r * 0.05 if style != "crop" else -r * 0.35)
        pth.close()
        if face < 0:
            m = skia.Matrix.Scale(-1, 1)
            pth.transform(m)
        c.drawPath(pth, P(OUT, 6))
        c.drawPath(pth, P(col))
        if style == "slick":
            for i in range(3):
                line(c, -r * 0.5 + i * r * 0.3, -r * 0.85, -r * 0.3 + i * r * 0.35, -r * 0.6, "#ffffff", 3, 0.25)
    elif style == "curly":
        for i in range(6):
            a = math.pi * (1.15 + i / 5 * 0.7)
            c.drawCircle(math.cos(a) * r * 0.7, math.sin(a) * r * 0.7 - r * 0.2, r * 0.3, P(col))
    elif style == "cap":
        capc = L["hair"][2]
        c.drawPath(poly([(-r * 0.98, -r * 0.3), (-r * 0.9, -r * 0.95), (0, -r * 1.22), (r * 0.9, -r * 0.95),
                         (r * 0.98, -r * 0.3)]), P(OUT, 6))
        c.drawPath(poly([(-r * 0.98, -r * 0.3), (-r * 0.9, -r * 0.95), (0, -r * 1.22), (r * 0.9, -r * 0.95),
                         (r * 0.98, -r * 0.3)]), P(capc))
        rrect(c, face * r * 0.2 - (r * 0.0 if face > 0 else r * 1.1), -r * 0.42, r * 0.9, r * 0.2, r * 0.1,
              mixhex(capc, "#000000", 0.35))


def _torso(c, L, tl, sh, wa, face, t):
    top = L["top"]
    style, col = top[0], top[1]
    body = skia.Path()
    body.moveTo(-sh, -tl)
    body.quadTo(-sh * 1.05, -tl * 0.5, -wa, 0)
    body.lineTo(wa, 0)
    body.quadTo(sh * 1.05, -tl * 0.5, sh, -tl)
    body.quadTo(0, -tl - 14, -sh, -tl)
    body.close()
    c.drawPath(body, P(OUT, 7))
    c.drawPath(body, P(col))
    c.save()
    c.clipPath(body, skia.ClipOp.kIntersect, True)
    # shading
    c.drawRect(skia.Rect(-face * sh * 2.2, -tl - 20, -face * sh * 0.45, 10), P("#1a0820", a=0.18))
    if style == "floral":
        acc = top[2]
        for i in range(14):
            fx = -sh + ((i * 37) % 100) / 100 * sh * 2
            fy = -tl + ((i * 53) % 100) / 100 * tl
            for k in range(5):
                a = k * 1.256 + t * 0.0
                c.drawCircle(fx + math.cos(a) * 7, fy + math.sin(a) * 7, 5, P(acc, a=0.9))
            c.drawCircle(fx, fy, 4, P("#ffffff"))
        # open collar + placket
        c.drawPath(poly([(-sh * 0.35, -tl - 4), (0, -tl * 0.62), (sh * 0.35, -tl - 4)]), P(L["skin"]))
        line(c, 0, -tl * 0.62, 0, 0, mixhex(col, "#000000", 0.3), 4)
    elif style == "tee":
        c.drawPath(poly([(-sh * 0.3, -tl - 4), (0, -tl * 0.86), (sh * 0.3, -tl - 4)]), P(L["skin"]))
        c.drawCircle(face * sh * 0.25, -tl * 0.55, sh * 0.22, P("#ffffff", a=0.25))
    elif style == "crop":
        c.drawRect(skia.Rect(-sh * 2, -tl * 0.32, sh * 2, 10), P(L["skin"]))
        c.drawRect(skia.Rect(-sh * 2, -tl * 0.22, sh * 2, 10), P(L["pants"]))
    elif style == "hoodie":
        c.drawPath(poly([(-sh * 0.5, -tl), (0, -tl * 0.7), (sh * 0.5, -tl)]), P(mixhex(col, "#000000", 0.3)))
        rrect(c, -sh * 0.55, -tl * 0.38, sh * 1.1, tl * 0.25, 10, mixhex(col, "#000000", 0.18))
        line(c, -sh * 0.12, -tl * 0.78, -sh * 0.15, -tl * 0.5, "#ffffff", 3)
        line(c, sh * 0.12, -tl * 0.78, sh * 0.15, -tl * 0.5, "#ffffff", 3)
    elif style in ("blazer", "suit", "jacket", "uniform"):
        inner = top[2]
        c.drawPath(poly([(-sh * 0.42, -tl - 4), (sh * 0.42, -tl - 4), (sh * 0.12, 0), (-sh * 0.12, 0)]), P(inner))
        if style == "suit":
            c.drawPath(poly([(-sh * 0.08, -tl * 0.9), (sh * 0.08, -tl * 0.9), (sh * 0.06, -tl * 0.3), (0, -tl * 0.22),
                             (-sh * 0.06, -tl * 0.3)]), P(top[3]))
        if style == "jacket":
            line(c, -sh * 0.5, -tl, -sh * 0.12, 0, top[2], 5)
            line(c, sh * 0.5, -tl, sh * 0.12, 0, top[2], 5)
        if style == "uniform":
            c.drawCircle(face * sh * 0.5, -tl * 0.7, 12, P(top[2]))
            line(c, -sh, -tl * 0.15, sh, -tl * 0.15, "#111111", 14)
        # lapels
        c.drawPath(poly([(-sh * 0.42, -tl - 4), (-sh * 0.12, -tl * 0.45), (-sh * 0.3, -tl * 0.62)]),
                   P(mixhex(col, "#ffffff", 0.12)))
        c.drawPath(poly([(sh * 0.42, -tl - 4), (sh * 0.12, -tl * 0.45), (sh * 0.3, -tl * 0.62)]),
                   P(mixhex(col, "#ffffff", 0.12)))
    c.restore()
    if L.get("chain"):
        pth = skia.Path()
        pth.moveTo(-sh * 0.32, -tl - 2)
        pth.quadTo(0, -tl * 0.62, sh * 0.32, -tl - 2)
        c.drawPath(pth, P("#ffd23f", 4))


def _human(c, who, pose, expr, t, look, face, talk):
    L = LOOKS[who]
    p = POSES[pose] if isinstance(pose, str) else pose
    k = 0.8 if L.get("small") else 1.0
    fem = L.get("female")
    tl = 170 * k
    sh = (52 if not fem else 46) * k
    wa = (40 if not fem else 36) * k
    ll1, ll2 = 92 * k, 88 * k
    al1, al2 = 78 * k, 74 * k
    hr = 46 * k
    skin = L["skin"]
    top = L["top"]
    sleeve = top[1]
    short = top[0] in ("floral", "tee", "crop")
    # back arm
    a1, a2 = p["la"] if face > 0 else p["ra"]
    _limb(c, -face * sh * 0.82, -tl + 16, a1, a2, al1, al2, 24 * k, 20 * k,
          mixhex(sleeve, "#000000", 0.25), mixhex(skin if short else sleeve, "#000000", 0.25), "hand",
          mixhex(skin, "#000000", 0.25))
    # legs
    for side, key in ((-1, "ll"), (1, "rl")):
        a1, a2 = p[key]
        pc = L["pants"] if side == face else mixhex(L["pants"], "#000000", 0.2)
        _limb(c, side * wa * 0.5, -8, a1, a2, ll1, ll2, 32 * k, 28 * k, pc, pc, "shoe", L["shoes"], endw=26 * k)
    # hips / belt
    rrect(c, -wa - 3, -16, wa * 2 + 6, 26, 10, OUT)
    rrect(c, -wa, -13, wa * 2, 20, 8, L["pants"])
    _torso(c, L, tl, sh, wa, face, t)
    # neck + head
    rrect(c, -hr * 0.32, -tl - hr * 0.55, hr * 0.64, hr * 0.7, 8, mixhex(skin, "#000000", 0.15))
    hy = -tl - hr * 1.05
    with xf(c, look[0] * 0.3, hy + look[1] * 0.3):
        _hair_back(c, L, hr, face)
        _face(c, L, hr, expr, t, face, talk, who)
        _hair_front(c, L, hr, face)
    # front arm
    a1, a2 = p["ra"] if face > 0 else p["la"]
    hand = _limb(c, face * sh * 0.82, -tl + 16, a1, a2, al1, al2, 24 * k, 20 * k, sleeve,
                 skin if short else sleeve, "hand", skin)
    return hand, hy, hr


def figure(c, x, y, who="hero", pose="stand", expr="neutral", t=0.0, s=1.0, look=(0, 0), face=1, talk=0.0,
           rim="#8ec8ff", rim_off=(8, -7), alpha=1.0, hold=None, rot=0.0, shadow=True, **kw):
    """Human character with hip center at (x, y). Returns world position of the front hand."""
    if who not in LOOKS:
        who = "hero"
    bounds = skia.Rect(x - 700 * s, y - 1100 * s, x + 700 * s, y + 900 * s)
    if alpha < 0.999:
        c.saveLayerAlpha(bounds, int(alpha * 255))
    if shadow:
        c.drawOval(skia.Rect(x - 110 * s, y + 160 * s, x + 110 * s, y + 190 * s), P("#000000", a=0.35))
    if rim:
        rp = skia.Paint(ColorFilter=skia.ColorFilters.Blend(C(rim), skia.BlendMode.kSrcIn))
        c.saveLayer(bounds, rp)
        with xf(c, x + rim_off[0] * s, y + rim_off[1] * s, s, rot):
            _human(c, who, pose, expr, t, look, face, talk)
        c.restore()
    with xf(c, x, y, s, rot):
        hand, hy, hr = _human(c, who, pose, expr, t, look, face, talk)
        if hold:
            hold(c, *hand)
    if alpha < 0.999:
        c.restore()
    r = math.radians(rot)
    hx, hyy = hand[0] * s, hand[1] * s
    return (x + hx * math.cos(r) - hyy * math.sin(r), y + hx * math.sin(r) + hyy * math.cos(r))


def head_only(c, x, y, who, expr, t, r=62, look=(0, 0), face=1, talk=0.0, rim="#8ec8ff", **kw):
    if who not in LOOKS:
        who = "hero"
    L = LOOKS[who]
    s = r / 46.0
    with xf(c, x, y + r * 0.2, s):
        # shoulders bust
        if rim:
            c.drawCircle(6, -6, 52, P(rim, a=0.9))
        _hair_back(c, L, 46, face)
        _face(c, L, 46, expr, t, face, talk, who)
        _hair_front(c, L, 46, face)
