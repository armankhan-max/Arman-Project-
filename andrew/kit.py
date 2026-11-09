"""Flat 2D explainer kit for "Who can actually afford a $500,000 house?".

Style analysed from the reference (flat vector explainer):
  * two worlds: clean INFOGRAPHIC BOARDS (one dark colour, thin line-art, caps titles, one hot accent)
    and warm ILLUSTRATED SETS (flat houses, trees, soft sky) with black-head characters;
  * black round heads with simple white eyes, one strong outfit colour per character;
  * "real person" photo cards pinned on the board with a callout line + caps label.

This version keeps the grammar but changes the look:
  * boards are deep TEAL (not navy), accents are AMBER + MINT, danger is ROSE (not coral);
  * sets are GOLDEN-HOUR (peach sky, sage hills, terracotta / teal houses) instead of blue sky;
  * outfits: teal hoodie, lilac cardigan, wine-red suit, slate suit, navy blazer, beige trench,
    olive overalls; nothing re-uses the reference's orange puffer / yellow / teal jackets.
  * the human photos are painted entirely in code (gradients + blurred shading), no stock images.
"""
import math
import os
import random
import sys

import skia

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video"))
from gfx import (W, H, C, P, xf, rrect, poly, line, text, text_width, linear, radial,  # noqa: E402,F401
                 fill_shader, glow, sparkle, check_mark, cross_mark, mixhex, font, clamp, lerp, smooth,
                 ease_out, back_out, at, window)

# ---------------------------------------------------------------- palette
BOARD1 = "#0f3d45"
BOARD2 = "#07242a"
CREAM = "#f6efe2"
LINEC = "#dcebe6"
AMBER = "#ffb547"
MINT = "#46d9a8"
ROSE = "#ff5a76"
MUTED = "#7fa6a8"
INK = "#14161b"
HEAD = "#16181d"

# ---------------------------------------------------------------- caching / post
_cache = {}


def cached(key, draw, blur=0.0, w=W, h=H, clear="#000000"):
    if key not in _cache:
        s = skia.Surface(w, h)
        cc = s.getCanvas()
        if clear:
            cc.clear(C(clear))
        else:
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


def blit(c, img, x=0, y=0, a=1.0, s=1.0):
    p = skia.Paint(AntiAlias=True)
    p.setAlphaf(clamp(a))
    if s == 1.0:
        c.drawImage(img, x, y, skia.SamplingOptions(skia.FilterMode.kLinear), p)
    else:
        c.drawImageRect(img, skia.Rect.MakeXYWH(x, y, img.width() * s, img.height() * s),
                        skia.SamplingOptions(skia.FilterMode.kLinear), p)


def blurpaint(color, sigma, a=1.0):
    p = P(color, a=a)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma))
    return p


_grain = []


def grain(c, t, a=0.05):
    if not _grain:
        rnd = random.Random(7)
        for _ in range(4):
            s = skia.Surface(480, 270)
            cc = s.getCanvas()
            cc.clear(skia.ColorTRANSPARENT)
            for _ in range(4200):
                v = rnd.choice(("#ffffff", "#000000"))
                cc.drawRect(skia.Rect.MakeXYWH(rnd.uniform(0, 480), rnd.uniform(0, 270), 1, 1), P(v, a=0.9))
            _grain.append(s.makeImageSnapshot())
    p = skia.Paint()
    p.setAlphaf(a)
    c.drawImageRect(_grain[int(t * 24) % 4], skia.Rect(0, 0, W, H), skia.SamplingOptions(), p)


def vignette(c, a=0.45):
    img = cached(("vig", round(a, 2)), lambda cc: fill_shader(
        cc, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, W * 0.75, [("#000000", 0), ("#000000", 0), ("#000000", a)],
                                          [0, 0.55, 1])), clear=None)
    blit(c, img)


# ---------------------------------------------------------------- boards (infographic world)
def _board(cc, tint=BOARD1):
    fill_shader(cc, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, [tint, BOARD2]))
    fill_shader(cc, skia.Rect(0, 0, W, H), radial(W / 2, H * 0.42, W * 0.55, [("#ffffff", 0.07), ("#ffffff", 0)]))
    for x in range(0, W + 1, 60):
        for y in range(0, H + 1, 60):
            cc.drawCircle(x, y, 1.6, P("#ffffff", a=0.05))


def board(c, tint=BOARD1):
    blit(c, cached(("board", tint), lambda cc: _board(cc, tint)))


def title(c, s, t, t0, y=110, size=58, color=CREAM, accent=None, acc_color=AMBER):
    """Caps title that slides down + fades in. `accent` = leading part drawn in accent colour."""
    k = ease_out(at(t, t0, 0.45))
    if k <= 0:
        return
    yy = y - 24 * (1 - k)
    if accent:
        w1 = text_width(accent + " ", size)
        w2 = text_width(s, size)
        x0 = W / 2 - (w1 + w2) / 2
        text(c, accent + " ", x0, yy, size, acc_color, align="left", a=k)
        text(c, s, x0 + w1, yy, size, color, align="left", a=k)
    else:
        text(c, s, W / 2, yy, size, color, a=k)


def pop(t, t0, d=0.4):
    return back_out(at(t, t0, d))


def tag(c, x, y, label, t, t0, bg=CREAM, fg=INK, size=34, rot=0.0):
    k = pop(t, t0)
    if k <= 0:
        return
    w = text_width(label, size) + 48
    h = size * 1.6
    with xf(c, x, y, s=k, rot=rot):
        rrect(c, -w / 2 + 4, -h / 2 + 6, w, h, h / 2, "#000000", 0.25)
        rrect(c, -w / 2, -h / 2, w, h, h / 2, bg)
        text(c, label, 0, size * 0.36, size, fg)


def money(c, x, y, value, size, t, t0, t1, color=CREAM, prefix="$", suffix="", align="center", a=1.0,
          fmt=None):
    """Count-up number from 0 to value between t0..t1."""
    if t < t0:
        return
    k = smooth((t - t0) / max(0.01, t1 - t0))
    v = value * k
    s = fmt(v) if fmt else f"{prefix}{int(round(v)):,}{suffix}"
    pk = pop(t, t0, 0.35)
    with xf(c, x, y, s=0.6 + 0.4 * pk):
        text(c, s, 0, 0, size, color, align=align, a=a)


def callout(c, x, y, x2, y2, small, big, t, t0, small_c=ROSE, big_c=CREAM, size=72):
    """Reference-style callout: dot + elbow line + caps label."""
    k = ease_out(at(t, t0, 0.5))
    if k <= 0:
        return
    mx = lerp(x, x2 - 60, k)
    c.drawCircle(x, y, 7, P(CREAM, 3))
    pth = skia.Path()
    pth.moveTo(x, y)
    pth.lineTo(lerp(x, x2 - 60, min(1, k * 2)), lerp(y, y2, min(1, k * 2)))
    if k > 0.5:
        pth.lineTo(mx + (x2 - 60 - mx) * 0, y2)
        pth.lineTo(x2 - 60 + 50 * (k - 0.5) * 2, y2)
    c.drawPath(pth, P(CREAM, 3))
    ka = clamp((k - 0.5) * 2)
    text(c, small, x2, y2 - size * 0.9, size * 0.42, small_c, "Black", "left", a=ka)
    text(c, big, x2, y2 + size * 0.35, size, big_c, "Black", "left", a=ka)


def underline(c, x, y, w, t, t0, color=ROSE, wid=8):
    k = ease_out(at(t, t0, 0.35))
    if k > 0:
        line(c, x - w / 2, y, x - w / 2 + w * k, y, color, wid)


def strike(c, x, y, w, t, t0, color=ROSE, wid=10):
    k = ease_out(at(t, t0, 0.3))
    if k > 0:
        line(c, x - w / 2, y + 8, x - w / 2 + w * k, y - 8, color, wid)


# ---------------------------------------------------------------- outdoor (golden hour) sets
def _hill(cc, base, amp, freqs, color, seed=0):
    p = skia.Path()
    p.moveTo(0, H)
    for x in range(0, W + 41, 40):
        y = base + sum(amp * a * math.sin(x * f + seed * (i + 1)) for i, (a, f) in enumerate(freqs))
        p.lineTo(x, y)
    p.lineTo(W, H)
    p.close()
    cc.drawPath(p, P(color))


def tree(c, x, y, s=1.0, col="#6f9a5a", col2="#5b844a", kind="round"):
    with xf(c, x, y, s=s):
        rrect(c, -9, -110, 18, 112, 8, "#7a5a44")
        if kind == "round":
            c.drawCircle(0, -150, 70, P(col2))
            c.drawCircle(-30, -125, 50, P(col))
            c.drawCircle(25, -175, 48, P(col))
            c.drawCircle(18, -128, 42, P(col2))
        else:
            for i in range(3):
                w = 80 - i * 18
                c.drawPath(poly([(-w, -60 - i * 55), (w, -60 - i * 55), (0, -170 - i * 55)]),
                           P(col if i % 2 == 0 else col2))


def cloud(c, x, y, s=1.0, a=1.0, col="#fffaf1"):
    with xf(c, x, y, s=s, alpha=a):
        rrect(c, -90, -10, 180, 44, 22, col)
        c.drawCircle(-30, -10, 38, P(col))
        c.drawCircle(25, -22, 46, P(col))


def house(c, x, y, s=1.0, body="#2f8f83", roof="#7a3b3b", trim=CREAM, door="#ffb547", lights=0.0, big=False):
    """Two-storey suburban house; (x, y) = centre of ground line."""
    with xf(c, x, y, s=s):
        w, hgt = (420, 300) if not big else (520, 340)
        # chimney
        rrect(c, w * 0.22, -hgt - 150, 46, 120, 4, mixhex(roof, "#000000", 0.2))
        # body
        rrect(c, -w / 2 + 8, -hgt + 8, w, hgt, 4, "#000000", 0.12)
        c.drawRect(skia.Rect(-w / 2, -hgt, w / 2, 0), P(body))
        c.drawRect(skia.Rect(-w / 2, -hgt, w / 2, -hgt + 18), P(mixhex(body, "#000000", 0.18)))
        # siding lines
        for yy in range(-hgt + 40, 0, 26):
            line(c, -w / 2, yy, w / 2, yy, mixhex(body, "#000000", 0.08), 2)
        # roof
        c.drawPath(poly([(-w / 2 - 40, -hgt + 4), (w / 2 + 40, -hgt + 4), (0, -hgt - 190)]), P(roof))
        c.drawPath(poly([(-w / 2 - 40, -hgt + 4), (w / 2 + 40, -hgt + 4), (w / 2 + 28, -hgt + 20),
                         (-w / 2 - 28, -hgt + 20)]), P(mixhex(roof, "#000000", 0.25)))
        # attic window
        c.drawCircle(0, -hgt - 70, 34, P(trim))
        c.drawCircle(0, -hgt - 70, 26, P(mixhex("#2b4a5a", AMBER, lights)))
        # windows
        def win(wx, wy, ww=78, wh=92):
            rrect(c, wx - ww / 2 - 7, wy - 7, ww + 14, wh + 14, 4, trim)
            c.drawRect(skia.Rect(wx - ww / 2, wy, wx + ww / 2, wy + wh), P(mixhex("#3d6b7a", "#ffd27a", lights)))
            line(c, wx, wy, wx, wy + wh, trim, 5)
            line(c, wx - ww / 2, wy + wh / 2, wx + ww / 2, wy + wh / 2, trim, 5)
            c.drawPath(poly([(wx - ww / 2, wy), (wx - ww / 2 + 26, wy), (wx - ww / 2, wy + 34)]),
                       P("#ffffff", a=0.18))
        win(-w * 0.3, -hgt + 50)
        win(w * 0.3, -hgt + 50)
        win(-w * 0.3, -hgt * 0.42)
        win(w * 0.3, -hgt * 0.42)
        # door + steps
        rrect(c, -40, -140, 80, 140, 6, trim)
        rrect(c, -32, -132, 64, 132, 4, door)
        c.drawCircle(18, -66, 5, P(CREAM))
        rrect(c, -62, -10, 124, 16, 3, mixhex(trim, "#000000", 0.15))


def _street(cc, lights=0.0, sky=("#ffcf9f", "#fff0d9")):
    fill_shader(cc, skia.Rect(0, 0, W, 760), linear(0, 0, 0, 760, list(sky)))
    glow(cc, 1500, 300, 260, "#fff6d8", 0.75)
    cc.drawCircle(1500, 300, 70, P("#fff3cf"))
    _hill(cc, 610, 30, [(1.0, 0.004), (0.5, 0.011)], "#c7cfa4", seed=1)
    _hill(cc, 660, 26, [(1.0, 0.006), (0.4, 0.015)], "#a9bd8a", seed=2)
    cc.drawRect(skia.Rect(0, 760, W, H), P("#8fb072"))
    cc.drawRect(skia.Rect(0, 905, W, H), P("#c9bfae"))
    cc.drawRect(skia.Rect(0, 900, W, 912), P("#b3a894"))
    for x in range(0, W, 120):
        line(cc, x, 905, x, H, "#b8ad9a", 3)


def street(c, t, blur=6.0):
    blit(c, cached(("street", blur), _street, blur=blur))
    for i, (cx, cy, s) in enumerate([(300, 170, 1.0), (980, 120, 0.8), (1720, 210, 0.9)]):
        cloud(c, (cx + t * 12 * (1 + i * 0.3)) % (W + 400) - 200, cy, s, 0.9)


def interior(c, wall="#f2e4cf", floor="#c99a6e", window=True, night=False):
    key = ("interior", wall, floor, window, night)

    def draw(cc):
        cc.drawRect(skia.Rect(0, 0, W, 820), P(wall))
        for x in range(0, W, 90):
            line(cc, x, 0, x, 820, mixhex(wall, "#000000", 0.04), 3)
        cc.drawRect(skia.Rect(0, 820, W, H), P(floor))
        for x in range(-200, W + 200, 160):
            line(cc, x, 820, x - 140, H, mixhex(floor, "#000000", 0.12), 3)
        cc.drawRect(skia.Rect(0, 806, W, 830), P(mixhex(wall, "#000000", 0.2)))
        if window:
            sky = ("#1d2a4a", "#33406b") if night else ("#ffd6a6", "#fff1dc")
            rrect(cc, 1290, 150, 430, 470, 8, CREAM)
            fill_shader(cc, skia.Rect(1310, 170, 1700, 600), linear(0, 170, 0, 600, list(sky)))
            if night:
                cc.drawCircle(1600, 270, 40, P("#f6efe2"))
                cc.drawCircle(1585, 260, 38, P(sky[0]))
            else:
                _hill_clip = skia.Path()
                cc.save()
                cc.clipRect(skia.Rect(1310, 170, 1700, 600))
                cc.drawCircle(1440, 520, 160, P("#a9bd8a"))
                cc.drawCircle(1640, 560, 140, P("#8fb072"))
                cc.restore()
                del _hill_clip
            line(cc, 1505, 170, 1505, 600, CREAM, 12)
            line(cc, 1310, 385, 1700, 385, CREAM, 12)
        if night:
            cc.drawRect(skia.Rect(0, 0, W, H), P("#0a1030", a=0.55))
    blit(c, cached(key, draw, blur=4.0))


# ---------------------------------------------------------------- characters (black-head style)
OUTFITS = {
    # name: top, top shade, inner shirt, pants, shoes, extras
    "buyer": dict(top="#2aa58f", top2="#1f7f6e", shirt=CREAM, pants="#2c3242", shoe="#f6efe2", hood=True),
    "partner": dict(top="#a98bea", top2="#8467c6", shirt="#fff1cc", pants="#3c3552", shoe="#3a2a22",
                    pony="#4a2e22", band=AMBER),
    "agent": dict(top="#9e2f48", top2="#76223a", shirt="#ffffff", pants="#9e2f48", shoe="#1b1b1b", tie=AMBER,
                  lapel=True),
    "banker": dict(top="#4d5869", top2="#38404d", shirt="#ffffff", pants="#38404d", shoe="#1b1b1b", tie=MINT,
                   lapel=True, glasses=True),
    "earner": dict(top="#22407a", top2="#172d58", shirt="#ffffff", pants="#172d58", shoe="#2b1d14", tie=AMBER,
                   lapel=True),
    "saver": dict(top="#d9b98a", top2="#b8976a", shirt="#3d5a5a", pants="#3d5a5a", shoe="#5a3a2a", lapel=True,
                  belt=True),
    "lean": dict(top="#6f8c3f", top2="#56702f", shirt="#f3e3c6", pants="#6f8c3f", shoe="#f6efe2", overalls=True,
                 beanie=ROSE),
    "avg": dict(top="#e3a73b", top2="#b9862b", shirt="#ffffff", pants="#4a5a6a", shoe="#2b2b2b", cap="#3b6fd1"),
    "crowd1": dict(top="#5f7fa8", top2="#4b6688", shirt=CREAM, pants="#2c3242", shoe="#222222"),
    "crowd2": dict(top="#c96f5a", top2="#a65846", shirt=CREAM, pants="#3a3a3a", shoe="#222222"),
    "crowd3": dict(top="#8aa66b", top2="#6e8754", shirt=CREAM, pants="#2c3242", shoe="#222222"),
    "crowd4": dict(top="#c9a0c8", top2="#a582a4", shirt=CREAM, pants="#3a3550", shoe="#222222"),
    "crowd5": dict(top="#e0c35a", top2="#b89e44", shirt=CREAM, pants="#3a3a3a", shoe="#222222"),
}

POSES = {
    #        left arm (a1, a2)     right arm         left leg   right leg
    "stand": ((-8, 4), (8, -4), (-3, 0), (3, 0)),
    "wave": ((-8, 4), (150, 25), (-3, 0), (3, 0)),
    "point": ((-8, 4), (92, -4), (-3, 0), (3, 0)),
    "pointL": ((-92, 4), (8, -4), (-3, 0), (3, 0)),
    "shrug": ((-55, -75), (55, 75), (-3, 0), (3, 0)),
    "cheer": ((-155, 10), (155, -10), (-6, 0), (6, 0)),
    "hold": ((-30, 75), (30, -75), (-3, 0), (3, 0)),
    "present": ((-8, 4), (35, 70), (-3, 0), (3, 0)),
    "headhold": ((-150, -80), (150, 80), (-4, 0), (4, 0)),
    "hips": ((-40, 70), (40, -70), (-6, 0), (6, 0)),
    "phone": ((-8, 4), (25, 150), (-3, 0), (3, 0)),
    "sit": ((20, 40), (-10, -40), (88, -88), (85, -85)),
    "thumbs": ((-8, 4), (35, 95), (-3, 0), (3, 0)),
    "slump": ((-4, 2), (4, -2), (-2, 0), (2, 0)),
}


def _seg(x, y, ang, L):
    r = math.radians(ang)
    return x + math.sin(r) * L, y + math.cos(r) * L


def _limb(c, x, y, a1, a2, l1, l2, w, col, end="hand", endc=HEAD):
    x2, y2 = _seg(x, y, a1, l1)
    x3, y3 = _seg(x2, y2, a1 + a2, l2)
    pth = skia.Path()
    pth.moveTo(x, y)
    pth.lineTo(x2, y2)
    pth.lineTo(x3, y3)
    c.drawPath(pth, P(col, w))
    if end == "hand":
        c.drawCircle(x3, y3, w * 0.62, P(endc))
    elif end == "shoe":
        rrect(c, x3 - w * 0.55, y3 - w * 0.35, w * 1.55, w * 0.8, w * 0.4, endc)
    return x3, y3


def face(c, cx, cy, r, expr="smile", t=0.0, look=(0, 0), talk=0.0, blink_seed=0.0):
    lx, ly = look
    # blink every ~3.7 s
    bt = (t + blink_seed) % 3.7
    blink = 0.12 if bt < 0.12 else 1.0
    ey = cy - r * 0.08 + ly * 4
    for sx in (-1, 1):
        ex = cx + sx * r * 0.36 + lx * 6
        if expr in ("happy", "grin") and blink > 0.5:
            pth = skia.Path()
            pth.moveTo(ex - r * 0.16, ey + 3)
            pth.quadTo(ex, ey - r * 0.22, ex + r * 0.16, ey + 3)
            c.drawPath(pth, P(CREAM, r * 0.09))
            continue
        c.drawOval(skia.Rect(ex - r * 0.17, ey - r * 0.23 * blink, ex + r * 0.17, ey + r * 0.23 * blink), P(CREAM))
        if blink > 0.5:
            c.drawCircle(ex + lx * 3, ey + 2 + ly * 3, r * 0.085, P(HEAD))
        if expr in ("worried", "sad", "panic"):
            line(c, ex - sx * r * 0.18, ey - r * 0.36, ex + sx * r * 0.14, ey - r * 0.28 - (6 if expr == "panic" else 0),
                 CREAM, r * 0.07)
        if expr == "angry":
            line(c, ex - sx * r * 0.2, ey - r * 0.38, ex + sx * r * 0.14, ey - r * 0.26, CREAM, r * 0.07)
    my = cy + r * 0.42
    if talk > 0:
        o = 0.25 + 0.75 * abs(math.sin(t * 13.0 + blink_seed))
        c.drawOval(skia.Rect(cx - r * 0.16, my - r * 0.1 * o, cx + r * 0.16, my + r * 0.12 * o), P(CREAM))
        return
    pth = skia.Path()
    if expr in ("smile", "happy"):
        pth.moveTo(cx - r * 0.24, my - 4)
        pth.quadTo(cx, my + r * 0.2, cx + r * 0.24, my - 4)
        c.drawPath(pth, P(CREAM, r * 0.08))
    elif expr == "grin":
        pth.moveTo(cx - r * 0.3, my - 6)
        pth.quadTo(cx, my + r * 0.42, cx + r * 0.3, my - 6)
        pth.close()
        c.drawPath(pth, P(CREAM))
    elif expr in ("sad",):
        pth.moveTo(cx - r * 0.2, my + 8)
        pth.quadTo(cx, my - r * 0.14, cx + r * 0.2, my + 8)
        c.drawPath(pth, P(CREAM, r * 0.08))
    elif expr in ("worried",):
        pth.moveTo(cx - r * 0.22, my + 2)
        for i in range(1, 5):
            pth.lineTo(cx - r * 0.22 + i * r * 0.11, my + (5 if i % 2 else -3))
        c.drawPath(pth, P(CREAM, r * 0.07))
    elif expr in ("shock", "panic"):
        c.drawOval(skia.Rect(cx - r * 0.13, my - r * 0.12, cx + r * 0.13, my + r * 0.2), P(CREAM))
    else:
        line(c, cx - r * 0.15, my + 2, cx + r * 0.15, my + 2, CREAM, r * 0.08)


LOOKS = {
    # skin, hair colour, hair style, extras
    "buyer": dict(skin="#c98b62", hair="#2b1d16", style="quiff"),
    "partner": dict(skin="#f1c8a6", hair="#6a3b22", style="pony", lashes=True),
    "agent": dict(skin="#f3cfae", hair="#3a2418", style="bun", lashes=True, lips="#c25a5f"),
    "banker": dict(skin="#efc9a8", hair="#c9c6c0", style="side", glasses=True, mustache=True),
    "earner": dict(skin="#8d5a3c", hair="#141010", style="crop"),
    "saver": dict(skin="#e3ac85", hair="#5a3a24", style="side", beard=True),
    "lean": dict(skin="#f0c39c", hair="#b5652e", style="none", freckles=True),
    "avg": dict(skin="#b5774f", hair="#2a1d14", style="none", beard=True),
    "crowd1": dict(skin="#f0c8a4", hair="#e0b35a", style="quiff"),
    "crowd2": dict(skin="#7a4a30", hair="#111111", style="afro"),
    "crowd3": dict(skin="#d9a27a", hair="#3a2a20", style="crop"),
    "crowd4": dict(skin="#f4d2b8", hair="#2a1a14", style="long", lashes=True),
    "crowd5": dict(skin="#c48a64", hair="#4a2c1a", style="bun", lashes=True),
}


def skin_face(c, cx, cy, r, lk, expr="smile", t=0.0, look=(0, 0), talk=0.0, blink_seed=0.0):
    """Flat cartoon face on a skin-tone head: white eyes + dark pupils, brows, nose, mouth, blush."""
    FEAT = "#2a1a14"
    lx, ly = look
    bt = (t + blink_seed) % 3.7
    blink = 0.1 if bt < 0.12 else 1.0
    ey = cy - r * 0.06 + ly * 4
    for sx in (-1, 1):
        ex = cx + sx * r * 0.34 + lx * 7
        # brows
        tilt = {"worried": 0.14, "sad": 0.14, "panic": 0.2, "angry": -0.14}.get(expr, 0.0)
        by = ey - r * 0.36 - (r * 0.06 if expr in ("shock", "panic", "grin") else 0)
        bc = lk["hair"] if lk["style"] != "none" else FEAT
        line(c, ex - sx * r * 0.15, by - tilt * r, ex + sx * r * 0.15, by + tilt * r * 0.4, bc, r * 0.09)
        if expr in ("happy", "grin") and blink > 0.5:
            pth = skia.Path()
            pth.moveTo(ex - r * 0.15, ey + 4)
            pth.quadTo(ex, ey - r * 0.2, ex + r * 0.15, ey + 4)
            c.drawPath(pth, P(FEAT, r * 0.08))
            continue
        ew, eh = r * 0.16, r * 0.2 * blink
        c.drawOval(skia.Rect(ex - ew, ey - eh, ex + ew, ey + eh), P("#ffffff"))
        if blink > 0.5:
            pr = r * (0.06 if expr in ("shock", "panic") else 0.095)
            c.drawCircle(ex + lx * 4, ey + 2 + ly * 4, pr, P(FEAT))
            c.drawCircle(ex + lx * 4 + pr * 0.35, ey - pr * 0.3 + ly * 4, pr * 0.35, P("#ffffff"))
        c.drawOval(skia.Rect(ex - ew, ey - eh, ex + ew, ey + eh), P(FEAT, 2.2))
        if lk.get("lashes") and blink > 0.5:
            line(c, ex + sx * ew * 0.7, ey - eh * 0.7, ex + sx * ew * 1.25, ey - eh * 1.05, FEAT, 2.5)
    # blush + freckles
    for sx in (-1, 1):
        c.drawOval(skia.Rect(cx + sx * r * 0.5 - r * 0.14, cy + r * 0.2, cx + sx * r * 0.5 + r * 0.14, cy + r * 0.34),
                   P("#ff7a7a", a=0.28))
        if lk.get("freckles"):
            for k in range(3):
                c.drawCircle(cx + sx * (r * 0.42 + k * 5), cy + r * 0.2 + (k % 2) * 5, 1.8, P("#9a5a3a"))
    # nose
    pth = skia.Path()
    pth.moveTo(cx + lx * 5, cy + r * 0.02)
    pth.quadTo(cx + r * 0.12 + lx * 5, cy + r * 0.2, cx - r * 0.02 + lx * 5, cy + r * 0.22)
    c.drawPath(pth, P(mixhex(lk["skin"], "#000000", 0.3), r * 0.06))
    if lk.get("mustache"):
        c.drawPath(poly([(cx - r * 0.24, cy + r * 0.36), (cx, cy + r * 0.28), (cx + r * 0.24, cy + r * 0.36),
                         (cx, cy + r * 0.33)]), P(lk["hair"]))
    my = cy + r * 0.45
    lipc = lk.get("lips", "#8a3a34")
    if talk > 0:
        o = 0.25 + 0.75 * abs(math.sin(t * 13.0 + blink_seed))
        c.drawOval(skia.Rect(cx - r * 0.15, my - r * 0.09 * o, cx + r * 0.15, my + r * 0.12 * o), P("#5a1f1c"))
        return
    pth = skia.Path()
    if expr in ("smile", "happy"):
        pth.moveTo(cx - r * 0.22, my - 4)
        pth.quadTo(cx, my + r * 0.2, cx + r * 0.22, my - 4)
        c.drawPath(pth, P(lipc, r * 0.07))
    elif expr == "grin":
        pth.moveTo(cx - r * 0.27, my - 6)
        pth.quadTo(cx, my + r * 0.4, cx + r * 0.27, my - 6)
        pth.close()
        c.drawPath(pth, P("#5a1f1c"))
        c.save()
        c.clipPath(pth, doAntiAlias=True)
        c.drawRect(skia.Rect(cx - r * 0.3, my - 8, cx + r * 0.3, my + r * 0.06), P("#ffffff"))
        c.drawCircle(cx, my + r * 0.3, r * 0.14, P("#e0605a"))
        c.restore()
    elif expr == "sad":
        pth.moveTo(cx - r * 0.18, my + 8)
        pth.quadTo(cx, my - r * 0.12, cx + r * 0.18, my + 8)
        c.drawPath(pth, P(lipc, r * 0.07))
    elif expr == "worried":
        pth.moveTo(cx - r * 0.2, my + 2)
        for i in range(1, 5):
            pth.lineTo(cx - r * 0.2 + i * r * 0.1, my + (5 if i % 2 else -3))
        c.drawPath(pth, P(lipc, r * 0.06))
    elif expr in ("shock", "panic"):
        c.drawOval(skia.Rect(cx - r * 0.12, my - r * 0.1, cx + r * 0.12, my + r * 0.22), P("#5a1f1c"))
    else:
        line(c, cx - r * 0.14, my + 2, cx + r * 0.14, my + 2, lipc, r * 0.07)


def skin_head(c, hx, hy, hr, lk, o, expr, t, look, talk, seed, back=False):
    skin, hair, st = lk["skin"], lk["hair"], lk["style"]
    if back:
        if st == "pony":
            c.drawOval(skia.Rect(hx - 84, hy - 10, hx - 34, hy + 74), P(hair))
        if st == "long":
            rrect(c, hx - hr - 10, hy - 20, hr * 2 + 20, hr * 1.9, 26, hair)
        if st == "bun":
            c.drawCircle(hx, hy - hr - 8, hr * 0.42, P(hair))
        if st == "afro":
            c.drawCircle(hx, hy - 10, hr * 1.28, P(hair))
        return
    # ears
    for sx in (-1, 1):
        c.drawCircle(hx + sx * hr * 0.98, hy + 6, hr * 0.2, P(mixhex(skin, "#000000", 0.08)))
    c.drawCircle(hx, hy, hr, P(skin))
    # soft shade on the right
    c.save()
    c.clipPath(_circle_path(hx, hy, hr), doAntiAlias=True)
    c.drawCircle(hx - hr * 0.35, hy - hr * 0.2, hr * 1.1, P(mixhex(skin, "#000000", 0.0)))
    c.drawCircle(hx + hr * 1.25, hy + hr * 0.2, hr * 0.75, P(mixhex(skin, "#000000", 0.1)))
    if lk.get("beard"):
        c.drawPath(poly([(hx - hr, hy + 2), (hx + hr, hy + 2), (hx + hr, hy + hr), (hx - hr, hy + hr)]), P(hair))
        c.drawOval(skia.Rect(hx - hr * 0.42, hy + hr * 0.12, hx + hr * 0.42, hy + hr * 0.62), P(skin))
    c.restore()
    # hair on top
    pth = skia.Path()
    if st in ("quiff", "crop", "side", "pony", "bun", "long"):
        pth.addArc(skia.Rect(hx - hr - 3, hy - hr - (12 if st == "quiff" else 5), hx + hr + 3, hy + hr * 0.9),
                   180, 180)
        pth.close()
        c.save()
        c.clipRect(skia.Rect(hx - hr - 10, hy - hr - 30, hx + hr + 10, hy - hr * (0.5 if st != "crop" else 0.6)))
        c.drawPath(pth, P(hair))
        c.restore()
        if st == "quiff":
            c.drawPath(poly([(hx - hr * 0.6, hy - hr * 0.75), (hx + hr * 0.2, hy - hr * 1.3),
                             (hx + hr * 0.9, hy - hr * 0.6)]), P(hair))
        if st == "side":
            c.drawPath(poly([(hx - hr * 0.95, hy - hr * 0.3), (hx - hr * 0.2, hy - hr * 0.62),
                             (hx + hr * 0.95, hy - hr * 0.3), (hx + hr, hy - hr * 0.7), (hx - hr, hy - hr * 0.7)]),
                       P(hair))
        if st in ("pony", "long", "bun"):
            # side locks framing the face
            rrect(c, hx - hr - 4, hy - hr * 0.6, 16, hr * (1.25 if st == "long" else 0.7), 8, hair)
            rrect(c, hx + hr - 12, hy - hr * 0.6, 16, hr * (1.25 if st == "long" else 0.7), 8, hair)
        if st == "pony":
            line(c, hx - hr * 0.9, hy - hr * 0.1, hx - hr * 0.75, hy - hr * 0.55, o.get("band", AMBER), 9)
    elif st == "afro":
        c.save()
        c.clipRect(skia.Rect(hx - hr * 1.4, hy - hr * 1.5, hx + hr * 1.4, hy - hr * 0.52))
        c.drawCircle(hx, hy - 10, hr * 1.28, P(hair))
        c.restore()
    skin_face(c, hx, hy + 6, hr, lk, expr, t, look, talk, seed * 1.3)
    if lk.get("glasses"):
        for sx in (-1, 1):
            c.drawCircle(hx + sx * 17 + look[0] * 7, hy + 4, 15, P("#2a2a2a", 3.5))
        line(c, hx - 3, hy + 2, hx + 3, hy + 2, "#2a2a2a", 3)


def _circle_path(x, y, r):
    p = skia.Path()
    p.addCircle(x, y, r)
    return p


def person(c, x, y, who="buyer", pose="stand", expr="smile", t=0.0, s=1.0, look=(0, 0), talk=0.0,
           walk=0.0, flip=False, sweat=0.0, breathe=True, prop=None, seed=0.0):
    """Flat cartoon character with a skin-tone face. (x, y) = point between the feet."""
    o = OUTFITS[who]
    la, ra, ll, rl = POSES[pose]
    if walk:
        sw = math.sin(walk * math.tau)
        ll = (-3 + 24 * sw, -6 * max(0, sw))
        rl = (3 - 24 * sw, -6 * max(0, -sw))
        la = (-8 - 20 * sw, 6)
        ra = (8 + 20 * sw, -6)
    bob = (math.sin(t * 2.1 + seed) * 2.5 if breathe else 0) + (abs(math.sin(walk * math.tau)) * -6 if walk else 0)
    with xf(c, x, y, sx=-s if flip else s, sy=s):
        c.drawOval(skia.Rect(-60, -8, 60, 10), P("#000000", a=0.16))
        hip = -150 + bob
        sh = -282 + bob
        sit = pose == "sit"
        # legs
        for side, (a1, a2) in ((-1, ll), (1, rl)):
            _limb(c, side * 18, hip, a1, a2, 76, 74, 24, o["pants"], end="shoe", endc=o["shoe"])
        # back arm first when flipped looks fine since symmetric
        top, top2 = o["top"], o["top2"]
        # torso
        tp = skia.Path()
        tp.moveTo(-54, sh)
        tp.quadTo(0, sh - 12, 54, sh)
        tp.lineTo(46, hip + 6)
        tp.quadTo(0, hip + 16, -46, hip + 6)
        tp.close()
        if o.get("hood"):
            c.drawOval(skia.Rect(-46, sh - 26, 46, sh + 20), P(top2))
        c.drawPath(tp, P(top))
        c.save()
        c.clipPath(tp, doAntiAlias=True)
        c.drawRect(skia.Rect(24, sh - 20, 60, hip + 20), P(top2))
        if o.get("overalls"):
            c.drawRect(skia.Rect(-60, sh - 20, 60, hip + 20), P(o["shirt"]))
            rrect(c, -34, sh + 50, 68, 140, 10, top)
            line(c, -28, sh + 54, -40, sh, top, 12)
            line(c, 28, sh + 54, 40, sh, top, 12)
            c.drawCircle(-24, sh + 64, 5, P(AMBER))
            c.drawCircle(24, sh + 64, 5, P(AMBER))
            rrect(c, -16, sh + 90, 32, 26, 4, top2)
        else:
            c.drawPath(poly([(-20, sh - 8), (20, sh - 8), (0, sh + 52)]), P(o["shirt"]))
            if o.get("tie"):
                c.drawPath(poly([(-6, sh + 2), (6, sh + 2), (10, sh + 70), (0, sh + 82), (-10, sh + 70)]),
                           P(o["tie"]))
            if o.get("lapel"):
                line(c, -20, sh - 6, -6, sh + 70, top2, 6)
                line(c, 20, sh - 6, 6, sh + 70, top2, 6)
                c.drawCircle(0, sh + 96, 4, P(top2))
                c.drawCircle(0, sh + 118, 4, P(top2))
            if o.get("hood"):
                line(c, -10, sh + 4, -12, sh + 52, CREAM, 4)
                line(c, 10, sh + 4, 12, sh + 52, CREAM, 4)
                rrect(c, -34, hip - 52, 68, 34, 8, top2)
            if o.get("belt"):
                c.drawRect(skia.Rect(-60, hip - 34, 60, hip - 20), P(top2))
        c.restore()
        # neck + head
        lk = LOOKS[who]
        c.drawRect(skia.Rect(-11, sh - 34, 11, sh + 2), P(mixhex(lk["skin"], "#000000", 0.12)))
        hx, hy, hr = 0, sh - 72, 50
        skin_head(c, hx, hy, hr, lk, o, expr, t, look, talk, seed, back=True)
        skin_head(c, hx, hy, hr, lk, o, expr, t, look, talk, seed)
        if o.get("cap"):
            c.drawPath(_cap_path(hx, hy - 22, hr), P(o["cap"]))
            rrect(c, hx + 10, hy - hr * 0.9, 70, 14, 7, mixhex(o["cap"], "#000000", 0.25))
        if o.get("beanie"):
            pth = skia.Path()
            pth.addArc(skia.Rect(hx - hr - 2, hy - hr - 22, hx + hr + 2, hy + hr - 22), 180, 180)
            pth.close()
            c.drawPath(pth, P(o["beanie"]))
            rrect(c, hx - hr - 4, hy - 42, hr * 2 + 8, 20, 8, mixhex(o["beanie"], "#000000", 0.2))
            c.drawCircle(hx, hy - hr - 22, 12, P(o["beanie"]))
        if sweat > 0:
            d = (t * 1.4) % 1.0
            c.drawCircle(hx + 52, hy - 20 + d * 40, 7, P("#9fe3ff", a=sweat * (1 - d)))
        # arms (on top of torso)
        for side, (a1, a2) in ((-1, la), (1, ra)):
            hx3, hy3 = _limb(c, side * 50, sh + 8, a1, a2, 74, 70, 24, top, endc=lk["skin"])
            if prop and side == 1:
                prop(c, hx3, hy3)
        if pose == "thumbs":
            hx3, hy3 = _seg(*_seg(50, sh + 8, ra[0], 74), ra[0] + ra[1], 70)
            rrect(c, hx3 - 6, hy3 - 34, 12, 28, 6, lk["skin"])


def _cap_path(hx, hy, hr):
    pth = skia.Path()
    pth.addArc(skia.Rect(hx - hr - 2, hy - hr - 4, hx + hr + 2, hy + hr), 180, 180)
    pth.close()
    return pth


# ---------------------------------------------------------------- painted human portraits (code-generated)
PORTRAITS = {
    "agent": dict(skin=("#f3cfae", "#d9a47f", "#b47b5a"), hair=("#3a2418", "#5b3a26"), style="bun",
                  suit=("#a3344c", "#6e1f33"), shirt="#fbf6ef", bg=("#e9d8c0", "#9c8670"), iris="#5a3b22",
                  lip=("#c25a5f", "#9b3f47"), smile=1.0, female=True),
    "lender": dict(skin=("#efc9a8", "#cf9a77", "#a6714f"), hair=("#bfbcb6", "#8d8a84"), style="side",
                   suit=("#3b4a63", "#1f2a3c"), shirt="#ffffff", tie="#2fae86", bg=("#cfd8db", "#6f7f86"),
                   iris="#4b6a7c", lip=("#b9746b", "#8f5047"), glasses=True, smile=0.25, female=False, age=1.0),
    "husband": dict(skin=("#c99372", "#a46f50", "#7c4e34"), hair=("#1e1612", "#3a2a20"), style="short",
                    suit=("#2aa58f", "#1b6f60"), shirt="#f6efe2", bg=("#f0dcc0", "#b49270"), iris="#3a2616",
                    lip=("#a8605a", "#7e4440"), beard=True, smile=0.6, female=False, hoodie=True),
    "wife": dict(skin=("#f1d2b6", "#d8a988", "#b98463"), hair=("#6a3b22", "#8f5530"), style="long",
                 suit=("#a98bea", "#7a5fc0"), shirt="#fff1cc", bg=("#efe0cf", "#a99079"), iris="#3f5e3a",
                 lip=("#c96a6a", "#a14c50"), smile=0.7, female=True),
    "earner": dict(skin=("#8d5a3c", "#6e4229", "#4e2d1a"), hair=("#141010", "#2a201a"), style="crop",
                   suit=("#244782", "#14284d"), shirt="#ffffff", tie=AMBER, bg=("#d5dce6", "#7c8aa0"),
                   iris="#2a1a10", lip=("#7e4a40", "#5e3328"), smile=0.8, female=False),
}


def _egg(cx, cy, w, h, chin=0.55):
    p = skia.Path()
    p.moveTo(cx, cy - h / 2)
    p.cubicTo(cx + w * 0.56, cy - h / 2, cx + w * 0.54, cy + h * 0.05, cx + w * 0.42, cy + h * 0.24)
    p.cubicTo(cx + w * 0.3, cy + h * 0.44, cx + w * 0.16 * chin, cy + h / 2, cx, cy + h / 2)
    p.cubicTo(cx - w * 0.16 * chin, cy + h / 2, cx - w * 0.3, cy + h * 0.44, cx - w * 0.42, cy + h * 0.24)
    p.cubicTo(cx - w * 0.54, cy + h * 0.05, cx - w * 0.56, cy - h / 2, cx, cy - h / 2)
    p.close()
    return p


def _paint_portrait(cc, spec, PW, PH):
    rnd = random.Random(hash(spec["skin"]) & 0xffff)
    sk1, sk2, sk3 = spec["skin"]
    h1, h2 = spec["hair"]
    cx, cy = PW / 2, PH * 0.43
    fw, fh = PW * 0.47, PH * 0.45
    # backdrop
    fill_shader(cc, skia.Rect(0, 0, PW, PH), radial(PW * 0.4, PH * 0.3, PW * 0.95, [spec["bg"][0], spec["bg"][1]]))
    for _ in range(14):
        cc.drawCircle(rnd.uniform(0, PW), rnd.uniform(0, PH * 0.6), rnd.uniform(20, 60),
                      blurpaint("#ffffff", 18, a=rnd.uniform(0.04, 0.12)))
    # long hair behind
    if spec["style"] in ("long",):
        hp = skia.Path()
        hp.moveTo(cx - fw * 0.62, cy - fh * 0.2)
        hp.cubicTo(cx - fw * 0.85, cy + fh * 0.5, cx - fw * 0.9, cy + fh * 0.95, cx - fw * 0.55, cy + fh * 1.05)
        hp.lineTo(cx + fw * 0.55, cy + fh * 1.05)
        hp.cubicTo(cx + fw * 0.9, cy + fh * 0.95, cx + fw * 0.85, cy + fh * 0.5, cx + fw * 0.62, cy - fh * 0.2)
        hp.close()
        cc.drawPath(hp, skia.Paint(AntiAlias=True, Shader=linear(0, cy - fh, 0, cy + fh, [h2, h1])))
    if spec["style"] == "bun":
        cc.drawCircle(cx + fw * 0.05, cy - fh * 0.7, fw * 0.26, skia.Paint(
            AntiAlias=True, Shader=radial(cx - fw * 0.05, cy - fh * 0.7, fw * 0.35, [h2, h1])))
    # shoulders / suit
    sp = skia.Path()
    sy = cy + fh * 0.62
    sp.moveTo(-20, PH + 10)
    sp.cubicTo(PW * 0.02, sy + PH * 0.12, PW * 0.18, sy + PH * 0.02, cx - fw * 0.3, sy - 6)
    sp.lineTo(cx + fw * 0.3, sy - 6)
    sp.cubicTo(PW * 0.82, sy + PH * 0.02, PW * 0.98, sy + PH * 0.12, PW + 20, PH + 10)
    sp.close()
    cc.drawPath(sp, skia.Paint(AntiAlias=True, Shader=linear(0, 0, PW, 0, [spec["suit"][0], spec["suit"][1]])))
    # neck
    nw = fw * 0.5
    neck = skia.Path()
    neck.moveTo(cx - nw / 2, cy + fh * 0.25)
    neck.lineTo(cx + nw / 2, cy + fh * 0.25)
    neck.lineTo(cx + nw * 0.62, sy + 10)
    neck.lineTo(cx - nw * 0.62, sy + 10)
    neck.close()
    cc.drawPath(neck, skia.Paint(AntiAlias=True, Shader=linear(cx - nw, 0, cx + nw, 0, [sk2, sk1, sk3])))
    cc.drawOval(skia.Rect(cx - nw * 0.7, cy + fh * 0.3, cx + nw * 0.7, cy + fh * 0.62), blurpaint(sk3, 10, 0.75))
    # shirt + collar
    if spec.get("hoodie"):
        cc.drawPath(poly([(cx - nw * 0.9, sy - 4), (cx + nw * 0.9, sy - 4), (cx + nw * 1.5, sy + 40),
                          (cx - nw * 1.5, sy + 40)]), P(spec["suit"][1]))
        line(cc, cx - 22, sy + 30, cx - 26, PH, spec["shirt"], 6)
        line(cc, cx + 22, sy + 30, cx + 26, PH, spec["shirt"], 6)
    else:
        cc.drawPath(poly([(cx - nw * 0.75, sy - 8), (cx + nw * 0.75, sy - 8), (cx, PH * 0.98)]), P(spec["shirt"]))
        cc.drawPath(poly([(cx - nw * 0.75, sy - 8), (cx - 4, sy + 40), (cx - nw * 0.55, sy + 48)]),
                    P(mixhex(spec["shirt"], "#000000", 0.12)))
        cc.drawPath(poly([(cx + nw * 0.75, sy - 8), (cx + 4, sy + 40), (cx + nw * 0.55, sy + 48)]),
                    P(mixhex(spec["shirt"], "#000000", 0.12)))
        if spec.get("tie"):
            cc.drawPath(poly([(cx - 12, sy + 34), (cx + 12, sy + 34), (cx + 20, PH), (cx - 20, PH)]), P(spec["tie"]))
            cc.drawPath(poly([(cx - 14, sy + 14), (cx + 14, sy + 14), (cx + 10, sy + 36), (cx - 10, sy + 36)]),
                        P(mixhex(spec["tie"], "#000000", 0.2)))
        # lapels
        dk = spec["suit"][1]
        cc.drawPath(poly([(cx - nw * 0.85, sy - 4), (cx - 18, PH * 0.98), (cx - nw * 1.8, PH)]), P(dk, a=0.55))
        cc.drawPath(poly([(cx + nw * 0.85, sy - 4), (cx + 18, PH * 0.98), (cx + nw * 1.8, PH)]), P(dk, a=0.55))
    # ears
    for sx in (-1, 1):
        ex = cx + sx * fw * 0.5
        cc.drawOval(skia.Rect(ex - fw * 0.09, cy - fh * 0.06, ex + fw * 0.09, cy + fh * 0.16), P(sk2))
        cc.drawOval(skia.Rect(ex - fw * 0.04, cy - fh * 0.02, ex + fw * 0.04, cy + fh * 0.12), blurpaint(sk3, 3, 0.6))
    # face
    fp = _egg(cx, cy, fw, fh, chin=0.7 if spec.get("female") else 0.95)
    cc.drawPath(fp, skia.Paint(AntiAlias=True, Shader=radial(cx - fw * 0.12, cy - fh * 0.08, fw * 0.8,
                                                              [sk1, sk1, sk2, sk3], [0, 0.35, 0.75, 1])))
    cc.save()
    cc.clipPath(fp, doAntiAlias=True)
    # soft modelling
    cc.drawOval(skia.Rect(cx + fw * 0.18, cy - fh * 0.5, cx + fw * 0.7, cy + fh * 0.5), blurpaint(sk3, 24, 0.45))
    for sx in (-1, 1):
        cc.drawOval(skia.Rect(cx + sx * fw * 0.22 - fw * 0.13, cy + fh * 0.08, cx + sx * fw * 0.22 + fw * 0.13,
                              cy + fh * 0.2), blurpaint("#e0756a", 12, 0.22 if spec.get("female") else 0.12))
        cc.drawOval(skia.Rect(cx + sx * fw * 0.2 - fw * 0.16, cy - fh * 0.16, cx + sx * fw * 0.2 + fw * 0.16,
                              cy - fh * 0.0), blurpaint(sk3, 9, 0.35))
    if spec.get("beard"):
        bp = skia.Path()
        bp.moveTo(cx - fw * 0.5, cy + fh * 0.05)
        bp.cubicTo(cx - fw * 0.45, cy + fh * 0.5, cx + fw * 0.45, cy + fh * 0.5, cx + fw * 0.5, cy + fh * 0.05)
        bp.lineTo(cx + fw * 0.5, cy + fh * 0.6)
        bp.lineTo(cx - fw * 0.5, cy + fh * 0.6)
        bp.close()
        cc.drawPath(bp, blurpaint(h1, 6, 0.85))
        for _ in range(420):
            a_ = rnd.uniform(0, math.pi)
            rr = rnd.uniform(0.25, 0.5)
            px = cx + math.cos(a_) * fw * rr
            py = cy + fh * 0.18 + math.sin(a_) * fh * 0.3
            line(cc, px, py, px + rnd.uniform(-2, 2), py + rnd.uniform(3, 7), h2, 1.4, 0.6)
    cc.restore()
    # eyes
    ey = cy - fh * 0.06
    for sx in (-1, 1):
        ex = cx + sx * fw * 0.2
        ew, eh = fw * 0.16, fh * 0.055
        if spec.get("smile", 0) > 0.7:
            eh *= 0.8
        al = skia.Path()
        al.moveTo(ex - ew, ey)
        al.cubicTo(ex - ew * 0.5, ey - eh * 1.4, ex + ew * 0.5, ey - eh * 1.4, ex + ew, ey - eh * 0.1)
        al.cubicTo(ex + ew * 0.5, ey + eh * 0.9, ex - ew * 0.5, ey + eh * 0.9, ex - ew, ey)
        al.close()
        cc.drawPath(al, P("#f6f1ea"))
        cc.save()
        cc.clipPath(al, doAntiAlias=True)
        ir = eh * 1.05
        cc.drawCircle(ex + sx * -1, ey - eh * 0.15, ir, skia.Paint(
            AntiAlias=True, Shader=radial(ex, ey - eh * 0.15, ir, [mixhex(spec["iris"], "#ffffff", 0.25),
                                                                   spec["iris"], "#000000"], [0, 0.7, 1])))
        cc.drawCircle(ex + sx * -1, ey - eh * 0.15, ir * 0.45, P("#0b0806"))
        cc.drawOval(skia.Rect(ex - ew, ey - eh * 1.6, ex + ew, ey - eh * 0.5), blurpaint("#000000", 3, 0.25))
        cc.restore()
        cc.drawCircle(ex + ir * 0.3, ey - eh * 0.45, ir * 0.22, P("#ffffff", a=0.9))
        up = skia.Path()
        up.moveTo(ex - ew * 1.05, ey + 1)
        up.cubicTo(ex - ew * 0.5, ey - eh * 1.45, ex + ew * 0.5, ey - eh * 1.45, ex + ew * 1.05, ey - eh * 0.15)
        cc.drawPath(up, P("#1d120c", 4.2 if spec.get("female") else 3.2))
        cr = skia.Path()
        cr.moveTo(ex - ew * 0.8, ey - eh * 1.4)
        cr.quadTo(ex, ey - eh * 2.3, ex + ew * 0.85, ey - eh * 1.2)
        cc.drawPath(cr, P(sk3, 2.2, 0.55))
        # brow
        bw = ew * 1.15
        by = ey - eh * 3.1 - (2 if spec.get("smile", 0) > 0.5 else 0)
        brow = skia.Path()
        brow.moveTo(ex - sx * bw * 0.9, by + 4)
        brow.quadTo(ex, by - 7, ex + sx * bw, by + 3)
        cc.drawPath(brow, P(h1, 7 if not spec.get("female") else 5))
    # nose
    ny = cy + fh * 0.13
    cc.drawOval(skia.Rect(cx - fw * 0.1, ny - fh * 0.03, cx + fw * 0.1, ny + fh * 0.04), blurpaint(sk3, 5, 0.5))
    line(cc, cx - fw * 0.03, cy - fh * 0.05, cx - fw * 0.05, ny - 6, sk3, 3, 0.35)
    cc.drawCircle(cx - fw * 0.01, ny - fh * 0.02, fw * 0.035, blurpaint("#ffffff", 3, 0.35))
    for sx in (-1, 1):
        cc.drawOval(skia.Rect(cx + sx * fw * 0.055 - 6, ny + 2, cx + sx * fw * 0.055 + 6, ny + 8),
                    blurpaint("#4a2a1c", 1.5, 0.75))
    # mouth
    my = cy + fh * 0.27
    mw = fw * (0.2 + 0.05 * spec.get("smile", 0))
    sm = spec.get("smile", 0)
    lp = skia.Path()
    lp.moveTo(cx - mw, my - sm * 6)
    lp.cubicTo(cx - mw * 0.4, my - 9, cx + mw * 0.4, my - 9, cx + mw, my - sm * 6)
    lp.cubicTo(cx + mw * 0.5, my + 14 + sm * 8, cx - mw * 0.5, my + 14 + sm * 8, cx - mw, my - sm * 6)
    lp.close()
    cc.drawPath(lp, skia.Paint(AntiAlias=True, Shader=linear(0, my - 10, 0, my + 16, [spec["lip"][1], spec["lip"][0]])))
    if sm > 0.55:
        tp = skia.Path()
        tp.moveTo(cx - mw * 0.82, my - sm * 5)
        tp.quadTo(cx, my + 1 + sm * 8, cx + mw * 0.82, my - sm * 5)
        tp.quadTo(cx, my - 2, cx - mw * 0.82, my - sm * 5)
        tp.close()
        cc.drawPath(tp, P("#fbf7f0"))
    mid = skia.Path()
    mid.moveTo(cx - mw, my - sm * 6)
    mid.quadTo(cx, my + sm * 9, cx + mw, my - sm * 6)
    cc.drawPath(mid, P("#5a2a24", 2.4, 0.8))
    cc.drawOval(skia.Rect(cx - mw * 0.5, my + 12, cx + mw * 0.5, my + 22), blurpaint(sk3, 4, 0.4))
    # hair front
    hp = skia.Path()
    st = spec["style"]
    top = cy - fh * 0.5
    if st in ("short", "crop", "side"):
        hp.moveTo(cx - fw * 0.53, cy - fh * 0.02)
        hp.cubicTo(cx - fw * 0.7, top - fh * 0.3, cx + fw * 0.7, top - fh * 0.34, cx + fw * 0.53, cy - fh * 0.02)
        thick = 0.22 if st == "short" else (0.16 if st == "crop" else 0.24)
        hp.cubicTo(cx + fw * 0.46, top + fh * 0.12, cx + fw * 0.1, top + fh * thick, cx - fw * 0.2, top + fh * 0.1)
        hp.cubicTo(cx - fw * 0.4, top + fh * 0.14, cx - fw * 0.48, top + fh * 0.25, cx - fw * 0.53, cy - fh * 0.02)
    else:
        hp.moveTo(cx - fw * 0.56, cy + fh * 0.15)
        hp.cubicTo(cx - fw * 0.72, top - fh * 0.3, cx + fw * 0.72, top - fh * 0.3, cx + fw * 0.56, cy + fh * 0.15)
        hp.cubicTo(cx + fw * 0.48, top + fh * 0.25, cx + fw * 0.2, top + fh * 0.08, cx, top + fh * 0.1)
        hp.cubicTo(cx - fw * 0.2, top + fh * 0.12, cx - fw * 0.5, top + fh * 0.22, cx - fw * 0.56, cy + fh * 0.15)
    hp.close()
    cc.drawPath(hp, skia.Paint(AntiAlias=True, Shader=linear(cx - fw, top, cx + fw, top + fh * 0.4, [h2, h1])))
    cc.save()
    cc.clipPath(hp, doAntiAlias=True)
    for _ in range(160):
        x0 = rnd.uniform(cx - fw * 0.6, cx + fw * 0.6)
        y0 = rnd.uniform(top - fh * 0.25, top + fh * 0.25)
        line(cc, x0, y0, x0 + rnd.uniform(-18, 18), y0 + rnd.uniform(10, 30), mixhex(h2, "#ffffff", 0.25), 1.3, 0.35)
    cc.restore()
    if spec.get("glasses"):
        for sx in (-1, 1):
            ex = cx + sx * fw * 0.2
            r = skia.Rect(ex - fw * 0.17, ey - fh * 0.075, ex + fw * 0.17, ey + fh * 0.065)
            cc.drawRoundRect(r, 12, 12, P("#ffffff", a=0.08))
            cc.drawRoundRect(r, 12, 12, P("#2a2a2a", 4))
        line(cc, cx - fw * 0.03, ey - 4, cx + fw * 0.03, ey - 4, "#2a2a2a", 4)
    # unify: light from left, film grain
    fill_shader(cc, skia.Rect(0, 0, PW, PH), linear(0, 0, PW, 0, [("#fff3e0", 0.08), ("#000000", 0.12)]))
    for _ in range(2600):
        cc.drawRect(skia.Rect.MakeXYWH(rnd.uniform(0, PW), rnd.uniform(0, PH), 1.2, 1.2),
                    P(rnd.choice(("#ffffff", "#000000")), a=0.07))


def portrait_img(kind, PW=420, PH=520):
    return cached(("portrait", kind), lambda cc: _paint_portrait(cc, PORTRAITS[kind], PW, PH), w=PW, h=PH)


def photo(c, x, y, kind, t, t0, s=1.0, rot=-3.0, label=None, sub=None, side="right"):
    """Polaroid-style code-painted photo pinned on board. (x, y) = centre."""
    k = pop(t, t0, 0.5)
    if k <= 0:
        return
    img = portrait_img(kind)
    PW, PH = img.width(), img.height()
    drift = math.sin((t - t0) * 0.6) * 0.8
    with xf(c, x, y, s=s * (0.7 + 0.3 * k), rot=rot + drift, alpha=clamp(k * 1.5)):
        rrect(c, -PW / 2 - 22 + 10, -PH / 2 - 22 + 16, PW + 44, PH + 90, 6, "#000000", 0.3)
        rrect(c, -PW / 2 - 22, -PH / 2 - 22, PW + 44, PH + 90, 6, "#fbf7ef")
        # slow ken burns inside frame
        kb = 1.0 + 0.04 * clamp((t - t0) / 6)
        c.save()
        c.clipRect(skia.Rect(-PW / 2, -PH / 2, PW / 2, PH / 2))
        blit(c, img, -PW / 2 * kb, -PH / 2 * kb, s=kb)
        c.restore()
        c.drawRect(skia.Rect(-PW / 2, -PH / 2, PW / 2, PH / 2), P("#000000", 2, 0.2))
        rrect(c, -50, -PH / 2 - 40, 100, 36, 3, "#f3e6b8", 0.85)  # tape
    if label:
        if side == "right":
            callout(c, x + (PW / 2 + 22) * s, y - 40 * s, x + (PW / 2 + 140) * s, y - 60 * s, sub or "", label,
                    t, t0 + 0.4)
        else:
            callout(c, x - (PW / 2 + 22) * s, y - 40 * s, x - (PW / 2 + 140) * s - text_width(label, 46), y - 60 * s,
                    sub or "", label, t, t0 + 0.4)


# ---------------------------------------------------------------- props & icons
def bill(c, x, y, s=1.0, rot=0.0, a=1.0):
    with xf(c, x, y, s=s, rot=rot, alpha=a):
        rrect(c, -70, -34, 140, 68, 6, "#5fae7a")
        rrect(c, -62, -26, 124, 52, 4, "#7cc794")
        c.drawCircle(0, 0, 18, P("#5fae7a"))
        text(c, "$", 0, 9, 26, "#e9f7ea")


def cash_stack(c, x, y, n, s=1.0, t=0.0):
    with xf(c, x, y, s=s):
        for i in range(n):
            yy = -i * 14
            rrect(c, -80, yy - 20, 160, 22, 4, "#4e9a67")
            rrect(c, -80, yy - 22, 160, 8, 3, "#6dbf86")
            rrect(c, -14, yy - 22, 28, 22, 2, "#e9e2c8")


def price_tag(c, x, y, label, s=1.0, rot=-8, col=AMBER, fg=INK, a=1.0):
    w = text_width(label, 64) + 90
    with xf(c, x, y, s=s, rot=rot, alpha=a):
        pth = poly([(-w / 2 + 40, -54), (w / 2, -54), (w / 2, 54), (-w / 2 + 40, 54), (-w / 2, 0)])
        c.save()
        c.translate(6, 10)
        c.drawPath(pth, P("#000000", a=0.25))
        c.restore()
        c.drawPath(pth, P(col))
        c.drawCircle(-w / 2 + 34, 0, 10, P(mixhex(col, "#000000", 0.35)))
        text(c, label, 26, 22, 64, fg)


def contract(c, x, y, s=1.0, sign=0.0, t=0.0, title_="HOME PURCHASE AGREEMENT", price="$500,000"):
    with xf(c, x, y, s=s):
        rrect(c, -330 + 10, -420 + 14, 660, 840, 8, "#000000", 0.2)
        rrect(c, -330, -420, 660, 840, 8, "#fbf6ea")
        text(c, title_, 0, -340, 30, INK)
        for i in range(9):
            yy = -280 + i * 42
            ww = 520 if i % 3 != 2 else 380
            line(c, -260, yy, -260 + ww, yy, "#cfc6b4", 8)
        text(c, "PRICE", -260, 140, 26, "#8a8274", "Bold", "left")
        text(c, price, -260, 210, 70, INK, "Black", "left")
        line(c, -260, 330, 260, 330, "#8a8274", 3)
        text(c, "BUYER SIGNATURE", -260, 362, 20, "#8a8274", "Bold", "left")
        if sign > 0:
            pth = skia.Path()
            n = int(60 * sign)
            for i in range(n + 1):
                u = i / 60
                px = -250 + u * 380
                py = 300 + math.sin(u * 22) * 16 * (1 - u * 0.3) - u * 10
                pth.moveTo(px, py) if i == 0 else pth.lineTo(px, py)
            c.drawPath(pth, P("#1d3f8a", 6))
            return -250 + sign * 380, 300 + math.sin(sign * 22) * 16 * (1 - sign * 0.3) - sign * 10
    return None


def pen(c, x, y, s=1.0, rot=-30):
    with xf(c, x, y, s=s, rot=rot):
        rrect(c, -10, -190, 20, 170, 8, "#1c1c22")
        rrect(c, -10, -190, 20, 40, 8, AMBER)
        c.drawPath(poly([(-10, -22), (10, -22), (0, 4)]), P("#d8d0c0"))


def stamp(c, x, y, label, k, col=MINT, rot=-12, size=80):
    if k <= 0:
        return
    sc = lerp(2.4, 1.0, ease_out(k))
    w = text_width(label, size) + 70
    with xf(c, x, y, s=sc, rot=rot, alpha=clamp(k * 3)):
        rrect(c, -w / 2, -size * 0.85, w, size * 1.6, 14, col, stroke=10)
        text(c, label, 0, size * 0.35, size, col)


def water_heater(c, x, y, s=1.0, t=0.0, burst=0.0):
    with xf(c, x, y, s=s):
        sh = math.sin(t * 60) * 6 * burst
        with xf(c, sh, 0):
            rrect(c, -110, -420, 220, 420, 40, "#cfd6d8")
            rrect(c, -110, -420, 70, 420, 30, "#e6ecee")
            rrect(c, -110, -420, 220, 60, 30, "#b4bec2")
            rrect(c, -40, -170, 80, 60, 8, "#8d999e")
            c.drawCircle(0, -140, 16, P(ROSE if burst > 0 else MINT))
            line(c, -50, -420, -50, -520, "#b07a3e", 22)
            line(c, 50, -420, 50, -520, "#b07a3e", 22)
            rrect(c, -110, -10, 220, 14, 6, "#9aa4a8")
        if burst > 0:
            for i in range(14):
                ph = (t * 1.8 + i / 14) % 1
                ang = math.radians(-60 + i * 9)
                d = 40 + ph * 280
                c.drawCircle(60 + math.sin(ang) * d * 0.6 + 40, -480 - math.cos(ang) * d * 0.3 + ph * ph * 220,
                             10 * (1 - ph) + 3, P("#7fd3ff", a=burst * (1 - ph)))
            for i in range(5):
                ph = (t * 1.1 + i / 5) % 1
                c.drawCircle(-70 + i * 40, -520 - ph * 120, 18 + ph * 30, P("#ffffff", a=0.35 * burst * (1 - ph)))


def calendar(c, x, y, s, top, big, small="", col=ROSE, a=1.0, flip=0.0):
    with xf(c, x, y, s=s, alpha=a):
        rrect(c, -110 + 8, -120 + 12, 220, 240, 18, "#000000", 0.25)
        rrect(c, -110, -120, 220, 240, 18, "#fbf6ea")
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-110, -120, 110, -50), 18, 18), P(col))
        c.drawRect(skia.Rect(-110, -70, 110, -50), P(col))
        text(c, top, 0, -72, 30, "#ffffff")
        text(c, big, 0, 50, 92, INK)
        if small:
            text(c, small, 0, 96, 22, "#8a8274", "Bold")
        for sx in (-55, 55):
            rrect(c, sx - 7, -138, 14, 36, 7, "#58606a")
        if flip > 0:
            with xf(c, 0, -50, sy=1 - flip, sx=1):
                c.drawRect(skia.Rect(-110, 0, 110, 170), P("#efe8da"))


def shield(c, x, y, s=1.0, col=MINT, check=True, a=1.0, label=None):
    with xf(c, x, y, s=s, alpha=a):
        pth = skia.Path()
        pth.moveTo(0, -110)
        pth.cubicTo(50, -80, 80, -85, 95, -85)
        pth.cubicTo(95, 10, 70, 80, 0, 115)
        pth.cubicTo(-70, 80, -95, 10, -95, -85)
        pth.cubicTo(-80, -85, -50, -80, 0, -110)
        pth.close()
        c.drawPath(pth, P(col))
        c.drawPath(pth, P(mixhex(col, "#000000", 0.25), 8))
        if check:
            check_mark(c, 0, 0, 90, "#ffffff")
        if label:
            text(c, label, 0, 20, 40, "#ffffff")


def jar(c, x, y, s=1.0, fill=0.5, col="#5fae7a", label=None):
    with xf(c, x, y, s=s):
        rrect(c, -90, -230, 180, 230, 34, "#ffffff", 0.12)
        hh = 210 * clamp(fill)
        c.save()
        c.clipRRect(skia.RRect.MakeRectXY(skia.Rect(-90, -230, 90, 0), 34, 34), doAntiAlias=True)
        c.drawRect(skia.Rect(-90, -hh, 90, 0), P(col))
        for i in range(int(hh // 22)):
            line(c, -80, -i * 22 - 6, 80, -i * 22 - 6, mixhex(col, "#000000", 0.15), 3)
        c.restore()
        rrect(c, -90, -230, 180, 230, 34, CREAM, stroke=6)
        rrect(c, -70, -262, 140, 34, 8, CREAM)
        if label:
            text(c, label, 0, 50, 30, CREAM)


def car(c, x, y, s=1.0, col="#d9534f", smoke=0.0, t=0.0, wheel=0.0):
    with xf(c, x, y, s=s):
        c.drawOval(skia.Rect(-210, -10, 210, 12), P("#000000", a=0.2))
        rrect(c, -210, -130, 420, 100, 40, col)
        c.drawPath(poly([(-120, -128), (-70, -210), (90, -210), (140, -128)]), P(col))
        c.drawPath(poly([(-100, -132), (-60, -196), (0, -196), (0, -132)]), P("#bfe3f0"))
        c.drawPath(poly([(14, -132), (14, -196), (82, -196), (118, -132)]), P("#bfe3f0"))
        rrect(c, 180, -100, 30, 22, 8, "#fff3c4")
        rrect(c, -210, -100, 24, 22, 8, ROSE)
        for wx in (-120, 120):
            c.drawCircle(wx, -26, 44, P("#24262b"))
            c.drawCircle(wx, -26, 20, P("#c8ccd2"))
            with xf(c, wx, -26, rot=wheel):
                line(c, -18, 0, 18, 0, "#8a9098", 5)
        if smoke > 0:
            for i in range(7):
                ph = (t * 0.7 + i / 7) % 1
                c.drawCircle(150 + ph * 60 + math.sin(ph * 9 + i) * 20, -150 - ph * 260, 30 + ph * 60,
                             P("#5b5f66", a=smoke * 0.55 * (1 - ph)))


def ac_unit(c, x, y, s=1.0, t=0.0, dead=0.0):
    with xf(c, x, y, s=s):
        rrect(c, -170, -150, 340, 150, 14, "#dfe5e6")
        c.drawCircle(-50, -75, 58, P("#9aa6aa"))
        with xf(c, -50, -75, rot=(t * 900 * (1 - dead)) % 360):
            for k in range(3):
                with xf(c, 0, 0, rot=k * 120):
                    c.drawOval(skia.Rect(-12, -50, 12, 0), P("#5f6b70"))
        for i in range(6):
            line(c, 40, -125 + i * 20, 140, -125 + i * 20, "#b4bec2", 5)
        if dead > 0:
            for i in range(5):
                ph = (t * 0.8 + i / 5) % 1
                c.drawCircle(100 + math.sin(i * 3 + ph * 6) * 30, -160 - ph * 160, 18 + ph * 26,
                             P("#555b62", a=0.5 * dead * (1 - ph)))


def credit_card(c, x, y, s=1.0, rot=-8, col="#3b2f6b"):
    with xf(c, x, y, s=s, rot=rot):
        rrect(c, -160 + 8, -100 + 10, 320, 200, 20, "#000000", 0.25)
        rrect(c, -160, -100, 320, 200, 20, col)
        rrect(c, -120, -50, 60, 44, 8, AMBER)
        text(c, "•••• 4821", -120, 50, 30, "#ffffff", "Bold", "left")
        c.drawCircle(100, 60, 22, P(ROSE, a=0.9))
        c.drawCircle(124, 60, 22, P(AMBER, a=0.9))


def bed_scene(c, x, y, s=1.0, t=0.0, eyes_open=True):
    with xf(c, x, y, s=s):
        rrect(c, -380, -90, 760, 120, 16, "#6a4e3a")
        rrect(c, -400, -260, 40, 300, 12, "#6a4e3a")
        rrect(c, -360, -140, 720, 70, 20, "#eef0f6")
        rrect(c, -340, -200, 170, 70, 30, "#ffffff")
        skin_head(c, -250, -205, 52, LOOKS["buyer"], OUTFITS["buyer"], "worried" if eyes_open else "happy", t,
                  (0.6, -0.6), 0, 0)
        pth = skia.Path()
        pth.moveTo(-200, -150)
        pth.cubicTo(-50, -200, 200, -190, 370, -150)
        pth.lineTo(370, -70)
        pth.lineTo(-200, -70)
        pth.close()
        c.drawPath(pth, P("#2aa58f"))
        c.drawPath(pth, P("#1f7f6e", 4))


def clock(c, x, y, r, h, m, col="#fbf6ea", a=1.0):
    with xf(c, x, y, alpha=a):
        c.drawCircle(0, 0, r + 10, P("#3d4650"))
        c.drawCircle(0, 0, r, P(col))
        for i in range(12):
            ang = math.radians(i * 30)
            line(c, math.sin(ang) * r * 0.82, -math.cos(ang) * r * 0.82, math.sin(ang) * r * 0.92,
                 -math.cos(ang) * r * 0.92, INK, 4)
        ha = math.radians((h % 12 + m / 60) * 30)
        ma = math.radians(m * 6)
        line(c, 0, 0, math.sin(ha) * r * 0.5, -math.cos(ha) * r * 0.5, INK, 9)
        line(c, 0, 0, math.sin(ma) * r * 0.75, -math.cos(ma) * r * 0.75, INK, 6)
        c.drawCircle(0, 0, 8, P(ROSE))


def people_icon(c, x, y, s, col, a=1.0):
    with xf(c, x, y, s=s, alpha=a):
        c.drawCircle(0, -34, 16, P(col))
        pth = skia.Path()
        pth.moveTo(-26, 20)
        pth.lineTo(-26, 0)
        pth.quadTo(-26, -14, -10, -14)
        pth.lineTo(10, -14)
        pth.quadTo(26, -14, 26, 0)
        pth.lineTo(26, 20)
        pth.close()
        c.drawPath(pth, P(col))


def house_icon(c, x, y, s, col=CREAM, stroke=6, a=1.0, fillc=None):
    with xf(c, x, y, s=s, alpha=a):
        pth = poly([(-60, -10), (0, -66), (60, -10), (60, 60), (-60, 60)])
        if fillc:
            c.drawPath(pth, P(fillc))
        c.drawPath(pth, P(col, stroke))
        c.drawRect(skia.Rect(-16, 20, 16, 60), P(col, stroke))


def storm_icons(c, x, y, t, t0, gap=200):
    # flood
    k = pop(t, t0)
    if k > 0:
        with xf(c, x - gap, y, s=k):
            for i in range(3):
                pth = skia.Path()
                yy = -20 + i * 26
                pth.moveTo(-60, yy)
                for j in range(1, 7):
                    pth.quadTo(-60 + j * 20 - 10, yy + (-12 if j % 2 else 12), -60 + j * 20, yy)
                c.drawPath(pth, P("#6cc6ff", 8))
            text(c, "FLOOD", 0, 90, 26, CREAM)
    k = pop(t, t0 + 0.5)
    if k > 0:
        with xf(c, x, y, s=k):
            fl = 1 + 0.08 * math.sin(t * 18)
            with xf(c, 0, 20, sy=fl, sx=1):
                pth = skia.Path()
                pth.moveTo(0, -80)
                pth.cubicTo(50, -20, 55, 30, 0, 40)
                pth.cubicTo(-55, 30, -50, -20, 0, -80)
                c.drawPath(pth, P(ROSE))
                pth2 = skia.Path()
                pth2.moveTo(0, -30)
                pth2.cubicTo(26, 0, 26, 30, 0, 36)
                pth2.cubicTo(-26, 30, -26, 0, 0, -30)
                c.drawPath(pth2, P(AMBER))
            text(c, "FIRE", 0, 90, 26, CREAM)
    k = pop(t, t0 + 0.9)
    if k > 0:
        with xf(c, x + gap, y, s=k):
            cloud(c, 0, -20, 0.6, col="#c7d0d6")
            fl = 1.0 if int(t * 6) % 3 else 0.4
            c.drawPath(poly([(-6, 0), (18, 0), (2, 30), (20, 30), (-14, 76), (-2, 40), (-18, 40)]), P(AMBER, a=fl))
            text(c, "STORM", 0, 90, 26, CREAM)


def warning(c, x, y, s=1.0, a=1.0):
    with xf(c, x, y, s=s, alpha=a):
        pth = poly([(0, -90), (95, 75), (-95, 75)])
        c.drawPath(pth, P(AMBER))
        c.drawPath(pth, P(mixhex(AMBER, "#000000", 0.3), 8))
        text(c, "!", 0, 55, 110, INK)


def donut(c, x, y, r, frac, col, bg="#ffffff", wid=60, a=1.0, start=-90):
    with xf(c, x, y, alpha=a):
        rect = skia.Rect(-r, -r, r, r)
        p = P(bg, wid, 0.12)
        p.setStrokeCap(skia.Paint.kButt_Cap)
        c.drawArc(rect, 0, 360, False, p)
        p2 = P(col, wid)
        p2.setStrokeCap(skia.Paint.kButt_Cap)
        c.drawArc(rect, start, 360 * clamp(frac), False, p2)


def gauge(c, x, y, r, v, a=1.0):
    with xf(c, x, y, alpha=a):
        for i in range(30):
            u = i / 29
            col = mixhex(MINT, ROSE, u)
            ang = math.radians(180 + u * 180)
            line(c, math.cos(ang) * r * 0.8, math.sin(ang) * r * 0.8, math.cos(ang) * r, math.sin(ang) * r, col, 10)
        ang = math.radians(180 + clamp(v) * 180)
        line(c, 0, 0, math.cos(ang) * r * 0.75, math.sin(ang) * r * 0.75, CREAM, 10)
        c.drawCircle(0, 0, 18, P(CREAM))


def bike(c, x, y, s=1.0, wheel=0.0, col=MINT):
    with xf(c, x, y, s=s):
        for wx in (-110, 110):
            c.drawCircle(wx, -60, 60, P(INK, 10))
            with xf(c, wx, -60, rot=wheel):
                for k in range(4):
                    with xf(c, 0, 0, rot=k * 45):
                        line(c, -56, 0, 56, 0, "#8a9098", 2)
        pth = poly([(-110, -60), (-20, -60), (60, -150), (-50, -150)], close=True)
        c.drawPath(pth, P(col, 10))
        line(c, -20, -60, -60, -170, col, 10)
        line(c, 60, -150, 110, -60, col, 10)
        line(c, 60, -150, 50, -190, col, 10)
        rrect(c, -90, -182, 60, 16, 8, INK)
        line(c, 30, -195, 80, -195, INK, 8)


def briefcase(c, x, y, s=1.0, col="#6b4a2f"):
    with xf(c, x, y, s=s):
        rrect(c, -30, -24, 60, 20, 8, col, stroke=8)
        rrect(c, -60, -8, 120, 84, 10, col)
        c.drawRect(skia.Rect(-60, 20, 60, 28), P(mixhex(col, "#000000", 0.25)))
        rrect(c, -8, 14, 16, 18, 3, AMBER)


def vault(c, x, y, s=1.0, t=0.0, lock=1.0):
    with xf(c, x, y, s=s):
        rrect(c, -170, -170, 340, 340, 26, "#5d6b72")
        rrect(c, -150, -150, 300, 300, 20, "#7d8b92")
        c.drawCircle(0, 0, 90, P("#5d6b72"))
        with xf(c, 0, 0, rot=t * 20):
            for k in range(6):
                with xf(c, 0, 0, rot=k * 60):
                    line(c, 0, 0, 0, -78, "#c8d0d4", 10)
        c.drawCircle(0, 0, 26, P("#c8d0d4"))
        if lock:
            with xf(c, 120, -120, s=0.8):
                rrect(c, -40, -10, 80, 64, 10, AMBER)
                pth = skia.Path()
                pth.addArc(skia.Rect(-28, -50, 28, 10), 180, 180)
                c.drawPath(pth, P(AMBER, 12))


def clipboard(c, x, y, s=1.0):
    with xf(c, x, y, s=s):
        rrect(c, -330 + 10, -380 + 14, 660, 780, 22, "#000000", 0.25)
        rrect(c, -330, -380, 660, 780, 22, "#a7774f")
        rrect(c, -300, -340, 600, 720, 10, "#fbf6ea")
        rrect(c, -90, -410, 180, 70, 16, "#6f7f86")


def roof_fix(c, x, y, s=1.0, t=0.0):
    house(c, x, y, s, body="#2f8f83", roof="#7a3b3b")


def sun_moon(c, x, y, r, night):
    if night:
        c.drawCircle(x, y, r, P("#f6efe2"))
        c.drawCircle(x - r * 0.35, y - r * 0.2, r * 0.9, P(BOARD1))
    else:
        c.drawCircle(x, y, r, P(AMBER))


def zzz(c, x, y, t, a=1.0):
    for i in range(3):
        ph = (t * 0.6 + i / 3) % 1
        text(c, "z", x + ph * 60, y - ph * 120, 30 + ph * 30, CREAM, a=a * (1 - ph))


def money_rain(c, t, t0, n=14, seed=3):
    rnd = random.Random(seed)
    for i in range(n):
        x0 = rnd.uniform(100, W - 100)
        sp = rnd.uniform(380, 620)
        d = rnd.uniform(0, 0.8)
        tt = t - t0 - d
        if tt < 0:
            continue
        yy = -100 + tt * sp
        if yy > H + 100:
            continue
        bill(c, x0 + math.sin(tt * 3 + i) * 40, yy, 0.8, rot=math.sin(tt * 4 + i) * 30)
