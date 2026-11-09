"""Style kit for "The Loop": cinematic rim-lit 2D stickwoman, moody practical-lamp sets, kinetic type.

Why it looks "real" instead of flat:
  * Every character gets a RIM pass (offset silhouette in the light colour) + a LIGHT-WRAP gradient
    clipped to the body (lit side warm, far side falls off into shadow) + a soft contact shadow.
  * Sets are painted once, blurred (depth of field) and cached; characters stay sharp.
  * Practical lights (lamp, phone, window) are additive glows that also tint the character.
  * Grain + vignette + gentle colour grade on every frame.
"""
import math
import os
import random
import sys

import skia

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video"))
from gfx import (W, H, C, P, xf, rrect, poly, line, linear, radial, fill_shader, glow, clamp, lerp,  # noqa: E402,F401
                 smooth, ease_out, back_out, at, window, mixhex)

INK = "#09080b"
OUT = "#111016"
EYE = "#f3ece0"
HAIR = "#120c0c"

# ------------------------------------------------------------------ fonts
_TF = {}
FONTS = {
    "bebas": "/usr/share/fonts/opentype/bebas-neue/BebasNeue-Bold.otf",
    "serif": "/usr/share/fonts/opentype/ebgaramond/EBGaramond12-Regular.otf",
    "serifi": "/usr/share/fonts/opentype/ebgaramond/EBGaramond12-Italic.otf",
    "serifb": "/usr/share/fonts/opentype/ebgaramond/EBGaramond12-Bold.otf",
    "sans": "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
    "sansl": "/usr/share/fonts/opentype/inter/Inter-Light.otf",
    "sansm": "/usr/share/fonts/opentype/inter/Inter-Medium.otf",
    "spartan": "/usr/share/fonts/opentype/league-spartan/LeagueSpartan-Black.otf",
}


def fnt(fam, size):
    key = (fam, round(size, 1))
    if key not in _TF:
        if fam not in _TF:
            _TF[fam] = skia.Typeface.MakeFromFile(FONTS[fam])
        f = skia.Font(_TF[fam], size)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        f.setSubpixel(True)
        _TF[key] = f
    return _TF[key]


def tw(s, size, fam="bebas", track=0.0):
    f = fnt(fam, size)
    return f.measureText(s) + track * size * max(0, len(s) - 1)


def txt(c, s, x, y, size, fam="bebas", color="#ffffff", align="center", a=1.0, track=0.0, blur=0.0,
        glow_col=None, glow_a=0.0, shadow=0.0):
    if a <= 0.003:
        return 0
    f = fnt(fam, size)
    w = tw(s, size, fam, track)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w

    def draw(paint):
        if track == 0:
            c.drawString(s, x, y, f, paint)
        else:
            xx = x
            for ch in s:
                c.drawString(ch, xx, y, f, paint)
                xx += f.measureText(ch) + track * size

    if shadow:
        sp = P("#000000", a=shadow * a)
        sp.setImageFilter(skia.ImageFilters.Blur(size * 0.08, size * 0.08))
        c.save(); c.translate(0, size * 0.05); draw(sp); c.restore()
    if glow_col and glow_a > 0:
        gp = P(glow_col, a=glow_a * a)
        gp.setImageFilter(skia.ImageFilters.Blur(size * 0.18, size * 0.18))
        draw(gp)
    p = P(color, a=a)
    if blur > 0.2:
        p.setImageFilter(skia.ImageFilters.Blur(blur, blur))
    draw(p)
    return w


# ------------------------------------------------------------------ caching / post
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


def blit(c, img, x=0, y=0, a=1.0, s=1.0, cx=W / 2, cy=H / 2):
    p = skia.Paint(AntiAlias=True)
    p.setAlphaf(clamp(a))
    c.save()
    if s != 1.0:
        c.translate(cx, cy); c.scale(s, s); c.translate(-cx, -cy)
    c.drawImage(img, x, y, skia.SamplingOptions(skia.FilterMode.kLinear), p)
    c.restore()


_grain = []


def grain(c, t, a=0.07):
    if not _grain:
        rnd = random.Random(7)
        for _ in range(6):
            s = skia.Surface(640, 360)
            cc = s.getCanvas()
            cc.clear(skia.ColorTRANSPARENT)
            for _ in range(9000):
                v = rnd.choice(("#ffffff", "#000000"))
                cc.drawRect(skia.Rect.MakeXYWH(rnd.uniform(0, 640), rnd.uniform(0, 360), 1, 1), P(v, a=0.9))
            _grain.append(s.makeImageSnapshot())
    p = skia.Paint()
    p.setAlphaf(a)
    c.drawImageRect(_grain[int(t * 24) % 6], skia.Rect(0, 0, W, H), skia.SamplingOptions(), p)


def vignette(c, a=0.65):
    fill_shader(c, skia.Rect(0, 0, W, H),
                radial(W / 2, H / 2, W * 0.75, [("#000000", 0), ("#000000", 0.08), ("#000000", a)], [0, 0.45, 1]))


def tint(c, color, a, mode=None):
    if a > 0.002:
        p = P(color, a=a)
        if mode:
            p.setBlendMode(mode)
        c.drawRect(skia.Rect(0, 0, W, H), p)


def add_glow(c, x, y, r, color, a=0.5):
    """Additive (screen) light bloom."""
    p = skia.Paint(Shader=radial(x, y, r, [(color, a), (color, a * 0.35), (color, 0)], [0, 0.35, 1]))
    p.setBlendMode(skia.BlendMode.kScreen)
    c.drawRect(skia.Rect(x - r, y - r, x + r, y + r), p)


def light_cone(c, x, y, ang, spread, length, color, a=0.25):
    r = math.radians(ang)
    pts = [(x, y)]
    for k in (-1, 1):
        rr = r + k * math.radians(spread)
        pts.append((x + math.sin(rr) * length, y + math.cos(rr) * length))
    pth = poly([pts[0], pts[1], pts[2]])
    p = skia.Paint(AntiAlias=True, Shader=radial(x, y, length, [(color, a), (color, 0)]))
    p.setBlendMode(skia.BlendMode.kScreen)
    p.setImageFilter(skia.ImageFilters.Blur(30, 30))
    c.drawPath(pth, p)


def shake(t, amt, freq=24.0, seed=0):
    if amt <= 0:
        return 0.0, 0.0
    return (amt * math.sin(t * freq + seed) * math.sin(t * freq * 0.37 + 1.3),
            amt * math.cos(t * freq * 1.13 + seed) * math.sin(t * freq * 0.29 + 0.4))


# ------------------------------------------------------------------ character: "Maya"
SWEATER = "#c9b28f"
SWEATER2 = "#9d8462"
PANTS = "#232a38"
PANTS2 = "#171c27"
SHOE = "#e8e2d6"

POSES = {
    #        torso lean, head tilt, l-arm(sh, el), r-arm(sh, el), l-leg(hip, knee), r-leg(hip, knee)
    "stand": dict(lean=0, tilt=0, la=(-8, 4), ra=(8, -4), ll=(-4, 2), rl=(4, -2)),
    "slump": dict(lean=8, tilt=14, la=(-2, 8), ra=(4, 6), ll=(-4, 2), rl=(4, -2)),
    "phone": dict(lean=10, tilt=20, la=(-6, 4), ra=(20, 120), ll=(-4, 2), rl=(4, -2)),
    "think": dict(lean=0, tilt=-6, la=(16, 125), ra=(28, 140), ll=(-4, 2), rl=(4, -2)),
    "point": dict(lean=0, tilt=0, la=(-8, 4), ra=(95, 5), ll=(-4, 2), rl=(4, -2)),
    "reach": dict(lean=6, tilt=6, la=(-8, 4), ra=(70, 15), ll=(-4, 2), rl=(4, -2)),
    "headhold": dict(lean=6, tilt=10, la=(150, 30), ra=(150, 30), ll=(-4, 2), rl=(4, -2)),
    "sit": dict(lean=4, tilt=6, la=(30, 55), ra=(38, 50), ll=(84, -84), rl=(78, -80)),
    "sitphone": dict(lean=12, tilt=24, la=(30, 70), ra=(22, 128), ll=(84, -84), rl=(78, -80)),
    "sitslump": dict(lean=18, tilt=26, la=(42, 40), ra=(46, 34), ll=(84, -84), rl=(78, -80)),
    "sitchin": dict(lean=16, tilt=8, la=(40, 52), ra=(28, 150), ll=(84, -84), rl=(78, -80)),
    "lie": dict(lean=0, tilt=-6, la=(160, 20), ra=(12, 40), ll=(2, 0), rl=(-4, 6)),
    "open": dict(lean=-4, tilt=-8, la=(-40, 10), ra=(40, -10), ll=(-6, 2), rl=(6, -2)),
    "stepf": dict(lean=4, tilt=-4, la=(-24, 8), ra=(22, -12), ll=(-16, 6), rl=(26, -18)),
}


def walk_pose(t, speed=1.6, amp=24):
    ph = t * speed * 2 * math.pi
    s = math.sin(ph)
    return dict(lean=4, tilt=2, la=(-amp * s * 0.8, 10 + 10 * max(0, -s)), ra=(amp * s * 0.8, -10 - 10 * max(0, s)),
                ll=(amp * s, -max(0, -math.cos(ph)) * 30), rl=(-amp * s, -max(0, math.cos(ph)) * 30),
                bob=abs(math.cos(ph)) * 6)


def mix_pose(a, b, k):
    a = POSES[a] if isinstance(a, str) else a
    b = POSES[b] if isinstance(b, str) else b
    out = {}
    for key in ("lean", "tilt"):
        out[key] = lerp(a.get(key, 0), b.get(key, 0), k)
    for key in ("la", "ra", "ll", "rl"):
        out[key] = (lerp(a[key][0], b[key][0], k), lerp(a[key][1], b[key][1], k))
    out["bob"] = lerp(a.get("bob", 0), b.get("bob", 0), k)
    return out


def _seg(x, y, ang, L):
    r = math.radians(ang)
    return x + math.sin(r) * L, y + math.cos(r) * L


def _taper(c, pts, w0, w1, col, out=True):
    """Tapered limb through 3 points (round joints)."""
    (x1, y1), (x2, y2), (x3, y3) = pts
    for (ax, ay, bx, by, wa, wb) in ((x1, y1, x2, y2, w0, (w0 + w1) / 2), (x2, y2, x3, y3, (w0 + w1) / 2, w1)):
        ang = math.atan2(by - ay, bx - ax)
        nx, ny = -math.sin(ang), math.cos(ang)
        pth = poly([(ax + nx * wa / 2, ay + ny * wa / 2), (bx + nx * wb / 2, by + ny * wb / 2),
                    (bx - nx * wb / 2, by - ny * wb / 2), (ax - nx * wa / 2, ay - ny * wa / 2)])
        if out:
            c.drawPath(pth, P(OUT, 6))
        c.drawPath(pth, P(col))
        c.drawCircle(ax, ay, wa / 2, P(col))
        c.drawCircle(bx, by, wb / 2, P(col))


def _arm(c, sx, sy, a1, a2, col):
    x2, y2 = _seg(sx, sy, a1, 72)
    x3, y3 = _seg(x2, y2, a1 + a2, 66)
    _taper(c, [(sx, sy), (x2, y2), (x3, y3)], 25, 19, col)
    # cuff + hand
    cx, cy = _seg(x2, y2, a1 + a2, 58)
    c.drawCircle(cx, cy, 9, P(SWEATER2))
    hx, hy = _seg(x2, y2, a1 + a2, 76)
    c.drawOval(skia.Rect(hx - 9.5, hy - 11, hx + 9.5, hy + 11), P(OUT))
    c.drawOval(skia.Rect(hx - 8, hy - 9.5, hx + 8, hy + 9.5), P(INK))
    return hx, hy


def _leg(c, hx, hy, a1, a2, col):
    x2, y2 = _seg(hx, hy, a1, 92)
    x3, y3 = _seg(x2, y2, a1 + a2, 90)
    _taper(c, [(hx, hy), (x2, y2), (x3, y3)], 30, 21, col)
    ang = a1 + a2
    with xf(c, x3, y3, rot=-ang):
        rrect(c, -12, -6, 40, 17, 8, OUT)
        rrect(c, -10, -4, 36, 13, 6.5, SHOE)
        c.drawRect(skia.Rect(-10, 6, 26, 9), P("#b9b2a6"))


def draw_eyes(c, r, expr, t, look, blink_seed=0.0):
    lx, ly = look
    ey = -r * 0.02
    ex0 = r * 0.2
    blink = (t * 0.27 + blink_seed) % 1.0 < 0.035 and expr not in ("wide",)
    for side in (-1, 1):
        cx = ex0 + side * r * 0.3
        if expr in ("closed", "smile_closed") or blink:
            p = skia.Path()
            if expr == "smile_closed":
                p.moveTo(cx - r * 0.13, ey + r * 0.04); p.quadTo(cx, ey - r * 0.1, cx + r * 0.13, ey + r * 0.04)
            else:
                p.moveTo(cx - r * 0.14, ey + r * 0.01); p.quadTo(cx, ey + r * 0.09, cx + r * 0.14, ey + r * 0.01)
            c.drawPath(p, P(EYE, r * 0.06))
            # lash
            line(c, cx + side * r * 0.13, ey + r * 0.02, cx + side * r * 0.2, ey - r * 0.03, EYE, r * 0.035)
            continue
        big = 1.22 if expr == "wide" else 1.0
        rx, ry = r * 0.15 * big, r * 0.14 * big
        c.drawOval(skia.Rect(cx - rx, ey - ry, cx + rx, ey + ry), P(EYE))
        c.drawCircle(cx + rx * 0.45 * (lx + 0.35), ey + ry * 0.35 * ly, r * 0.07, P(INK))
        c.drawCircle(cx + rx * 0.45 * (lx + 0.35) - r * 0.025, ey + ry * 0.35 * ly - r * 0.03, r * 0.02,
                     P("#ffffff", a=0.9))
        lid = {"neutral": 0.3, "tired": 0.58, "bored": 0.55, "sad": 0.42, "worried": 0.25, "wide": 0.0,
               "focus": 0.42, "smile": 0.32, "soft": 0.4, "frustrated": 0.45}.get(expr, 0.3)
        top = ey - ry - 3
        yl = ey - ry + 2 * ry * lid
        if expr in ("sad", "worried"):
            inner = yl - ry * 0.5
            pts = [(cx - rx - 3, top), (cx + rx + 3, top)]
            pts += [(cx + rx + 3, inner), (cx - rx - 3, yl)] if side == -1 else [(cx + rx + 3, yl), (cx - rx - 3, inner)]
            c.drawPath(poly(pts), P(INK))
        elif expr == "frustrated":
            inner = yl + ry * 0.45
            pts = [(cx - rx - 3, top), (cx + rx + 3, top)]
            pts += [(cx + rx + 3, inner), (cx - rx - 3, yl - ry * 0.2)] if side == -1 else \
                [(cx + rx + 3, yl - ry * 0.2), (cx - rx - 3, inner)]
            c.drawPath(poly(pts), P(INK))
        elif lid > 0:
            c.drawRect(skia.Rect(cx - rx - 3, top, cx + rx + 3, yl), P(INK))
        # upper lid line + lash flick (feminine read)
        lp = skia.Path()
        lp.moveTo(cx - rx, max(yl, ey - ry) + 1)
        lp.quadTo(cx, max(yl, ey - ry) - r * 0.03, cx + rx, max(yl, ey - ry) + 1)
        c.drawPath(lp, P(INK, r * 0.04))
        ox = cx + side * rx
        line(c, ox - side * 2, max(yl, ey - ry) + 2, ox + side * r * 0.08, max(yl, ey - ry) - r * 0.05, EYE, r * 0.03)
        # brows
        by = ey - ry - r * 0.13
        if expr in ("sad", "worried"):
            line(c, cx - r * 0.12, by + side * r * 0.045, cx + r * 0.12, by - side * r * 0.045, EYE, r * 0.045)
        elif expr == "frustrated":
            line(c, cx - r * 0.12, by - side * r * 0.05, cx + r * 0.12, by + side * r * 0.05, EYE, r * 0.05)
        elif expr == "wide":
            line(c, cx - r * 0.12, by - r * 0.07, cx + r * 0.12, by - r * 0.07, EYE, r * 0.045)
        else:
            p = skia.Path()
            p.moveTo(cx - r * 0.12, by + r * 0.01); p.quadTo(cx, by - r * 0.03, cx + r * 0.12, by + r * 0.01)
            c.drawPath(p, P(EYE, r * 0.045))


def draw_mouth(c, r, expr, t, talk):
    mx, my = r * 0.2, r * 0.45
    if talk > 0:
        op = 0.25 + 0.75 * abs(math.sin(t * 13) * math.sin(t * 5.3 + 1))
        c.drawOval(skia.Rect(mx - r * 0.1, my - r * 0.04 * op, mx + r * 0.1, my + r * 0.1 * op), P(EYE))
    elif expr in ("smile", "smile_closed", "soft"):
        p = skia.Path()
        k = 0.1 if expr != "soft" else 0.05
        p.moveTo(mx - r * 0.13, my - r * 0.01); p.quadTo(mx, my + r * k, mx + r * 0.13, my - r * 0.01)
        c.drawPath(p, P(EYE, r * 0.05))
    elif expr in ("sad", "worried", "tired", "frustrated"):
        p = skia.Path()
        p.moveTo(mx - r * 0.11, my + r * 0.05); p.quadTo(mx, my - r * 0.03, mx + r * 0.11, my + r * 0.05)
        c.drawPath(p, P(EYE, r * 0.045))
    elif expr == "wide":
        c.drawOval(skia.Rect(mx - r * 0.06, my - r * 0.05, mx + r * 0.06, my + r * 0.09), P(EYE))
    elif expr == "yawn":
        c.drawOval(skia.Rect(mx - r * 0.1, my - r * 0.1, mx + r * 0.1, my + r * 0.18), P(EYE))
        c.drawOval(skia.Rect(mx - r * 0.06, my - r * 0.04, mx + r * 0.06, my + r * 0.12), P("#3a1d22"))
    else:
        line(c, mx - r * 0.09, my, mx + r * 0.09, my, EYE, r * 0.045)


def draw_head(c, r, expr, t, look=(0, 0), talk=0.0, hair_swing=0.0, back=True, front=True):
    """Head centred at 0,0, facing +x (3/4). Long wavy hair, side part."""
    sw = math.sin(t * 1.3) * 3 + hair_swing
    if back:
        # back hair mass (falls behind shoulders)
        hp = skia.Path()
        hp.moveTo(-r * 0.2, -r * 1.02)
        hp.cubicTo(-r * 1.25, -r * 0.95, -r * 1.25, r * 0.4, -r * 1.05 + sw * 0.3, r * 1.55)
        hp.cubicTo(-r * 0.9 + sw, r * 2.05, -r * 0.35 + sw, r * 2.1, -r * 0.1 + sw * 0.6, r * 1.75)
        hp.cubicTo(r * 0.2, r * 1.35, r * 0.15, r * 0.9, r * 0.3, r * 0.6)
        hp.lineTo(r * 0.6, -r * 0.6)
        hp.close()
        c.drawPath(hp, P(OUT, 7))
        c.drawPath(hp, P(HAIR))
        for k in range(3):  # strand highlights
            sp = skia.Path()
            sp.moveTo(-r * (0.95 - k * 0.18), -r * 0.2 + k * r * 0.1)
            sp.cubicTo(-r * (1.05 - k * 0.15), r * 0.5, -r * (0.9 - k * 0.2) + sw, r * 1.1,
                       -r * (0.7 - k * 0.2) + sw, r * (1.6 - k * 0.15))
            c.drawPath(sp, P("#3b2a26", r * 0.035, 0.7))
    if not front:
        return
    # head shape (slightly tall oval, soft jaw)
    hd = skia.Path()
    hd.addOval(skia.Rect(-r * 0.92, -r * 1.0, r * 0.98, r * 0.98))
    c.drawPath(hd, P(OUT, 7))
    c.drawPath(hd, P(INK))
    # ear + earring
    draw_eyes(c, r, expr, t, look)
    draw_mouth(c, r, expr, t, talk)
    # fringe / side-swept bangs over the top
    fp = skia.Path()
    fp.moveTo(-r * 0.98, r * 0.15)
    fp.cubicTo(-r * 1.08, -r * 0.9, -r * 0.2, -r * 1.25, r * 0.6, -r * 0.95)
    fp.cubicTo(r * 1.0, -r * 0.75, r * 1.05, -r * 0.4, r * 0.98, -r * 0.18)
    fp.cubicTo(r * 0.7, -r * 0.62, r * 0.25, -r * 0.62, -r * 0.05, -r * 0.48)
    fp.cubicTo(-r * 0.4, -r * 0.42, -r * 0.6, -r * 0.2, -r * 0.62, r * 0.25)
    fp.close()
    c.drawPath(fp, P(HAIR))
    hl = skia.Path()
    hl.moveTo(-r * 0.55, -r * 0.8); hl.cubicTo(-r * 0.1, -r * 1.05, r * 0.4, -r * 0.98, r * 0.75, -r * 0.7)
    c.drawPath(hl, P("#4a3530", r * 0.05, 0.75))


def _body(c, pose, expr, t, look, talk, hair_swing, hold_back=None):
    p = POSES[pose] if isinstance(pose, str) else pose
    bob = p.get("bob", 0)
    lean = p.get("lean", 0)
    tl = 150
    # legs from hip (0,0)
    for key, xo, col in (("ll", -10, PANTS2), ("rl", 10, PANTS)):
        a1, a2 = p[key]
        _leg(c, xo, -bob, a1, a2, col)
    with xf(c, 0, -bob, rot=lean * 0.6):
        # back arm
        a1, a2 = p["la"]
        if hold_back:
            hold_back(c)
        _arm(c, -22, -tl + 26, a1, a2, SWEATER2)
        # back hair behind torso
        hy = -tl - 66
        with xf(c, 6, hy, rot=p.get("tilt", 0) * 0.6):
            draw_head(c, 54, expr, t, look, talk, hair_swing, back=True, front=False)
        # torso (sweater) shoulders -> waist -> hip
        tp = skia.Path()
        tp.moveTo(-36, -tl + 6)
        tp.cubicTo(-44, -tl + 10, -42, -tl + 40, -34, -tl + 80)
        tp.cubicTo(-30, -tl + 105, -36, -tl + 135, -38, -4)
        tp.lineTo(38, -4)
        tp.cubicTo(36, -tl + 135, 32, -tl + 105, 36, -tl + 80)
        tp.cubicTo(44, -tl + 40, 46, -tl + 10, 36, -tl + 6)
        tp.cubicTo(18, -tl - 4, -18, -tl - 4, -36, -tl + 6)
        tp.close()
        c.drawPath(tp, P(OUT, 7))
        c.drawPath(tp, P(SWEATER))
        # knit ribbing + hem + neckline
        for k in range(6):
            line(c, -30 + k * 12, -16, -30 + k * 12, -4, SWEATER2, 2.2, 0.8)
        c.drawRect(skia.Rect(-38, -18, 38, -14), P(SWEATER2, a=0.7))
        nk = skia.Path()
        nk.moveTo(-16, -tl + 2); nk.quadTo(0, -tl + 16, 16, -tl + 2)
        c.drawPath(nk, P(SWEATER2, 5))
        # waist fold shadow
        line(c, -30, -tl + 92, -6, -tl + 98, SWEATER2, 2.5, 0.6)
        # neck
        rrect(c, -9, -tl - 22, 20, 28, 8, INK)
        # head
        with xf(c, 6, hy, rot=p.get("tilt", 0) * 0.6):
            draw_head(c, 54, expr, t, look, talk, hair_swing, back=False, front=True)
        # front arm
        a1, a2 = p["ra"]
        hand = _arm(c, 24, -tl + 26, a1, a2, SWEATER)
        # rotate hand into parent space
        r = math.radians(lean * 0.6)
        hx, hyy = hand
        hand = (hx * math.cos(r) - hyy * math.sin(r), hx * math.sin(r) + hyy * math.cos(r) - bob)
    return hand


def woman(c, x, y, s=1.0, pose="stand", expr="neutral", t=0.0, look=(0, 0), face=1, talk=0.0, rot=0.0,
          rim="#ffb36b", rim_off=(5, -4), light=None, shade=0.55, alpha=1.0, hold=None, hold_back=None,
          hair_swing=0.0, shadow=True, ghost=None):
    """Draw Maya with hip at (x, y). light=(lx, ly, colour) for light-wrap direction. Returns hand pos."""
    bounds = skia.Rect(x - 520 * s, y - 520 * s, x + 520 * s, y + 360 * s)
    if shadow and abs(rot) < 20:
        sp = P("#000000", a=0.45 * alpha)
        sp.setImageFilter(skia.ImageFilters.Blur(14 * s, 6 * s))
        c.drawOval(skia.Rect(x - 95 * s, y + 160 * s, x + 95 * s, y + 196 * s), sp) if "sit" not in str(pose) \
            else None
    hand_holder = {}

    def body(cc):
        with xf(cc, x, y, s, rot, sx=s * face, sy=s):
            hand_holder["h"] = _body(cc, pose, expr, t, look, talk, hair_swing, hold_back)
            if hold:
                hold(cc, *hand_holder["h"])

    if alpha < 0.999:
        c.saveLayerAlpha(bounds, int(clamp(alpha) * 255))
    if rim:
        rp = skia.Paint(ColorFilter=skia.ColorFilters.Blend(C(rim), skia.BlendMode.kSrcIn))
        c.saveLayer(bounds, rp)
        c.save(); c.translate(rim_off[0] * s, rim_off[1] * s); body(c); c.restore()
        c.restore()
    c.saveLayer(bounds, None)
    body(c)
    # light wrap: lit side warm, far side into shadow (SrcATop keeps it inside the silhouette)
    lx = light[0] if light else x + 600 * face
    ly = light[1] if light else y - 500
    lc = light[2] if light else "#ffb36b"
    gp = skia.Paint(Shader=linear(lx, ly, lx + (x - lx) * 2.2, ly + (y - 80 * s - ly) * 2.2,
                                  [(lc, 0.28), ("#000000", 0.0), ("#000000", shade)], [0, 0.45, 1]))
    gp.setBlendMode(skia.BlendMode.kSrcATop)
    c.drawRect(bounds, gp)
    if ghost:
        gp2 = P(ghost, a=0.65)
        gp2.setBlendMode(skia.BlendMode.kSrcATop)
        c.drawRect(bounds, gp2)
    c.restore()
    if alpha < 0.999:
        c.restore()
    hx, hy = hand_holder["h"]
    hx *= face
    r = math.radians(rot)
    return (x + s * (hx * math.cos(r) - hy * math.sin(r)), y + s * (hx * math.sin(r) + hy * math.cos(r)))


def big_head(c, x, y, r, expr, t, look=(0, 0), talk=0.0, face=1, rim="#ffb36b", light=None, tilt=0.0,
             shoulders=True, sweater=SWEATER, alpha=1.0):
    """Close-up: head + shoulders, used for emotional beats."""
    s = r / 60.0
    bounds = skia.Rect(x - r * 4, y - r * 3, x + r * 4, y + r * 6)

    def body(cc):
        with xf(cc, x, y, rot=tilt, sx=s * face, sy=s):
            draw_head(cc, 60, expr, t, look, talk, back=True, front=False)
            if shoulders:
                sp = skia.Path()
                sp.moveTo(-10, 58); sp.cubicTo(-46, 64, -84, 78, -92, 230)
                sp.lineTo(104, 230); sp.cubicTo(96, 78, 58, 64, 22, 58); sp.close()
                cc.drawPath(sp, P(OUT, 8)); cc.drawPath(sp, P(sweater))
                nk = skia.Path(); nk.moveTo(-28, 58); nk.quadTo(4, 92, 36, 58)
                cc.drawPath(nk, P(SWEATER2, 7))
                rrect(cc, -8, 30, 24, 40, 10, INK)
            draw_head(cc, 60, expr, t, look, talk, back=False, front=True)

    if alpha < 0.999:
        c.saveLayerAlpha(bounds, int(alpha * 255))
    if rim:
        rp = skia.Paint(ColorFilter=skia.ColorFilters.Blend(C(rim), skia.BlendMode.kSrcIn))
        c.saveLayer(bounds, rp); c.save(); c.translate(4 * s * face, -4 * s); body(c); c.restore(); c.restore()
    c.saveLayer(bounds, None)
    body(c)
    lx, ly, lc = light if light else (x + 500 * face, y - 300, "#ffb36b")
    gp = skia.Paint(Shader=linear(lx, ly, lx + (x - lx) * 2.2, ly + (y - ly) * 2.2,
                                  [(lc, 0.3), ("#000000", 0.0), ("#000000", 0.6)], [0, 0.45, 1]))
    gp.setBlendMode(skia.BlendMode.kSrcATop)
    c.drawRect(bounds, gp)
    c.restore()
    if alpha < 0.999:
        c.restore()


# ------------------------------------------------------------------ props
def phone(c, x, y, s=1.0, rot=0.0, on=1.0, t=0.0, feed=True):
    with xf(c, x, y, s, rot):
        rrect(c, -22, -40, 44, 80, 8, "#0c0c10")
        rrect(c, -19, -36, 38, 72, 6, mixhex("#141820", "#6fb6ff", on * 0.85))
        if on > 0 and feed:
            off = (t * 40) % 24
            for k in range(4):
                yy = -34 + k * 24 - off
                if -36 < yy < 30:
                    rrect(c, -15, yy, 30, 16, 3, "#ffffff", a=0.35 * on)
    if on > 0:
        add_glow(c, x, y, 220 * s, "#6fb6ff", 0.35 * on)


def mug(c, x, y, s=1.0, t=0.0, steam=True, col="#e9e4da"):
    with xf(c, x, y, s):
        c.drawCircle(30, -30, 16, P(col, 7))
        rrect(c, -28, -62, 56, 62, 9, col)
        rrect(c, -28, -62, 18, 62, 9, "#ffffff", a=0.35)
        c.drawOval(skia.Rect(-28, -68, 28, -56), P("#3a2416"))
        if steam:
            for k in range(3):
                ph = (t * 0.6 + k * 0.33) % 1.0
                sp = skia.Path()
                sx = -12 + k * 12
                sp.moveTo(sx, -72)
                sp.cubicTo(sx - 14, -95 - 40 * ph, sx + 14, -110 - 40 * ph, sx, -140 - 60 * ph)
                c.drawPath(sp, P("#ffffff", 4, 0.22 * (1 - ph)))


def book(c, x, y, s=1.0, rot=0.0, col="#7a2f2a", title=True, open_=0.0):
    with xf(c, x, y, s, rot):
        rrect(c, -70, -95, 140, 190, 6, "#1a1416")
        rrect(c, -66, -92, 132, 184, 5, col)
        rrect(c, -66, -92, 14, 184, 3, "#000000", a=0.25)
        if title:
            for k in range(3):
                rrect(c, -36, -60 + k * 16, 80 - k * 18, 6, 3, "#e8d9b0", a=0.85)


def laptop(c, x, y, s=1.0, on=1.0):
    with xf(c, x, y, s):
        rrect(c, -110, -150, 220, 140, 8, "#1b1d24")
        rrect(c, -100, -140, 200, 120, 4, mixhex("#0f1115", "#2d3d55", on))
        if on:
            for k in range(5):
                rrect(c, -86, -126 + k * 18, 120 - (k * 37) % 70, 7, 3, "#9cc7ff", a=0.5 * on)
        c.drawPath(poly([(-130, -10), (130, -10), (148, 6), (-148, 6)]), P("#2b2e37"))


def alarm_clock(c, x, y, s=1.0, t=0.0, ring=0.0, hhmm=(7, 0)):
    jx = math.sin(t * 70) * 5 * ring
    with xf(c, x + jx, y, s, rot=math.sin(t * 60) * 6 * ring):
        for side in (-1, 1):
            c.drawCircle(side * 42, -78, 22, P("#c9c2b4"))
        c.drawCircle(0, 0, 80, P("#1d1a1e"))
        c.drawCircle(0, 0, 70, P("#f1ead9"))
        for k in range(12):
            a = k * math.pi / 6
            line(c, math.sin(a) * 58, -math.cos(a) * 58, math.sin(a) * 64, -math.cos(a) * 64, "#3a3436", 4)
        h, m = hhmm
        ah = (h % 12 + m / 60) * math.pi / 6
        am = m * math.pi / 30
        line(c, 0, 0, math.sin(ah) * 34, -math.cos(ah) * 34, "#1d1a1e", 7)
        line(c, 0, 0, math.sin(am) * 52, -math.cos(am) * 52, "#1d1a1e", 4.5)
        c.drawCircle(0, 0, 6, P("#c0392b"))
        for side in (-1, 1):
            line(c, side * 50, 62, side * 64, 86, "#1d1a1e", 8)
    if ring > 0:
        for k in range(3):
            ph = (t * 3 + k / 3) % 1
            c.drawCircle(x, y, (90 + ph * 90) * s, P("#ffffff", 4, 0.3 * (1 - ph) * ring))


def pan_egg(c, x, y, s=1.0, t=0.0, cooked=1.0):
    with xf(c, x, y, s):
        sp = P("#000000", a=0.5); sp.setImageFilter(skia.ImageFilters.Blur(18, 18))
        c.drawCircle(14, 18, 210, sp)
        rrect(c, 180, -24, 260, 48, 20, "#1b1718")
        c.drawCircle(0, 0, 210, P("#1c1a1c"))
        c.drawCircle(0, 0, 186, P("#2c2829"))
        fill_shader(c, skia.Rect(-186, -186, 186, 186), radial(-50, -60, 220, [("#4a4446", 0.6), ("#2c2829", 0)]))
        ep = skia.Path()
        for k in range(20):
            a = k / 20 * 2 * math.pi
            rr = 100 + 14 * math.sin(a * 3 + 1) + 9 * math.sin(a * 5)
            (ep.moveTo if k == 0 else ep.lineTo)(math.cos(a) * rr, math.sin(a) * rr)
        ep.close()
        c.drawPath(ep, P("#f5f1e6", a=0.55 + 0.45 * cooked))
        c.drawPath(ep, P("#c9a46b", 4, 0.5 * cooked))
        c.drawCircle(18, -10, 42, P("#f0a51c"))
        c.drawCircle(4, -24, 12, P("#ffffff", a=0.6))
        for k in range(6):  # sizzle bubbles
            ph = (t * 1.7 + k * 0.17) % 1
            a = k * 1.1
            c.drawCircle(math.cos(a) * (110 + 20 * ph), math.sin(a) * (110 + 20 * ph), 4 * (1 - ph),
                         P("#ffffff", a=0.6 * (1 - ph)))


def calendar_page(c, x, y, s=1.0, rot=0.0, top="TOMORROW", big="", col="#c0392b", a=1.0):
    with xf(c, x, y, s, rot, alpha=a):
        sp = P("#000000", a=0.4); sp.setImageFilter(skia.ImageFilters.Blur(14, 14))
        c.drawRect(skia.Rect(-150, -170, 170, 200), sp)
        rrect(c, -160, -190, 320, 380, 10, "#f1ece2")
        rrect(c, -160, -190, 320, 90, 10, col)
        c.drawRect(skia.Rect(-160, -120, 160, -100), P(col))
        for k in range(5):
            c.drawCircle(-110 + k * 55, -190, 10, P("#2b2626"))
        txt(c, top, 0, -125, 58, "bebas", "#ffffff", track=0.04)
        if big:
            txt(c, big, 0, 120, 230, "bebas", "#1d1a1e")


def lamp(c, x, y, s=1.0, on=1.0):
    """Mushroom lamp like a warm practical."""
    with xf(c, x, y, s):
        rrect(c, -14, -120, 28, 120, 8, mixhex("#3a2a1a", "#f6a531", on))
        c.drawOval(skia.Rect(-60, -10, 60, 12), P(mixhex("#3a2a1a", "#d8841c", on)))
        cp = skia.Path()
        cp.moveTo(-110, -110); cp.cubicTo(-110, -230, 110, -230, 110, -110); cp.close()
        c.drawPath(cp, P(mixhex("#4a3520", "#ffb43a", on)))
        c.save(); c.clipPath(cp, doAntiAlias=True)
        fill_shader(c, skia.Rect(-110, -200, 110, -110), radial(-20, -170, 120, [("#fff1c2", 0.8 * on), ("#ffb43a", 0)]))
        c.restore()
    if on > 0:
        add_glow(c, x, y - 140 * s, 520 * s, "#ff9a2e", 0.45 * on)


def thought_bubble(c, x, y, w, h, a=1.0, col="#f3ece0", tail=(-1, 1), s=1.0):
    with xf(c, x, y, s, alpha=a):
        rr = skia.RRect.MakeRectXY(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), h / 2, h / 2)
        c.drawRRect(rr, P(col))
        for k, r in enumerate((16, 10, 6)):
            c.drawCircle(tail[0] * (w * 0.3 + k * 26), h / 2 + 22 + k * 22, r, P(col))


def arrow_curve(c, x1, y1, x2, y2, bend, color, w=8, a=1.0, prog=1.0):
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1
    cx, cy = mx - dy / L * bend, my + dx / L * bend
    pts = []
    n = 30
    for i in range(int(n * prog) + 1):
        u = i / n
        pts.append(((1 - u) ** 2 * x1 + 2 * (1 - u) * u * cx + u * u * x2,
                    (1 - u) ** 2 * y1 + 2 * (1 - u) * u * cy + u * u * y2))
    if len(pts) < 2:
        return
    p = skia.Path(); p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    c.drawPath(p, P(color, w, a))
    (ax, ay), (bx, by) = pts[-2], pts[-1]
    ang = math.atan2(by - ay, bx - ax)
    hl = w * 2.6
    c.drawPath(poly([(bx + math.cos(ang) * hl * 0.5, by + math.sin(ang) * hl * 0.5),
                     (bx + math.cos(ang + 2.5) * hl, by + math.sin(ang + 2.5) * hl),
                     (bx + math.cos(ang - 2.5) * hl, by + math.sin(ang - 2.5) * hl)]), P(color, a=a))


# ------------------------------------------------------------------ sets (painted once, blurred, cached)
def _wall_texture(c, rect, base, seed=1, n=500, a=0.05):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = rect
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        r = rnd.uniform(20, 90)
        c.drawCircle(x, y, r, P(rnd.choice(("#000000", "#ffffff")), a=a * rnd.uniform(0.2, 1)))


def set_room(c):
    """Her room at night: deep red-brown walls, desk, poster wall, bookshelf, window (blue)."""
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#2a1512", "#3d1d17", "#1a0d0b"], [0, 0.6, 1]))
    _wall_texture(c, (0, 0, W, 760), "#3d1d17", 3)
    # floor
    fill_shader(c, skia.Rect(0, 760, W, H), linear(0, 760, 0, H, ["#20120e", "#0c0706"]))
    c.drawRect(skia.Rect(0, 752, W, 764), P("#140a08"))
    # window (cool moonlight)
    rrect(c, 1380, 140, 360, 420, 6, "#0d0f16")
    fill_shader(c, skia.Rect(1395, 155, 1725, 545), linear(1395, 155, 1725, 545, ["#1c2c4a", "#0b1426"]))
    line(c, 1560, 155, 1560, 545, "#0d0f16", 14)
    line(c, 1395, 350, 1725, 350, "#0d0f16", 14)
    c.drawCircle(1650, 230, 34, P("#dfe8ff", a=0.85))
    # poster wall
    rnd = random.Random(11)
    for i in range(9):
        px, py = 220 + (i % 3) * 120 + rnd.uniform(-15, 15), 170 + (i // 3) * 140 + rnd.uniform(-10, 10)
        with xf(c, px, py, rot=rnd.uniform(-5, 5)):
            rrect(c, -48, -60, 96, 120, 2, rnd.choice(("#c9b99b", "#a8957a", "#d8ccb3")), a=0.55)
            rrect(c, -36, -44, 72, 60, 2, "#000000", a=0.25)
    # framed portrait
    rrect(c, 640, 120, 170, 210, 4, "#120a08")
    rrect(c, 656, 136, 138, 178, 2, "#c2b49a", a=0.6)
    c.drawCircle(725, 200, 34, P("#2a1e18", a=0.8))
    # bookshelf right
    rrect(c, 1780, 120, 200, 640, 4, "#160b09")
    for r_ in range(5):
        y = 150 + r_ * 120
        c.drawRect(skia.Rect(1790, y + 96, 1980, y + 106), P("#2a1712"))
        xx = 1795
        while xx < 1960:
            bw = rnd.uniform(14, 30)
            rrect(c, xx, y + 20 + rnd.uniform(0, 20), bw - 3, 76, 2,
                  rnd.choice(("#5c2a22", "#2f3d4a", "#6b5a3a", "#3d2b2b", "#7a6a55")), a=0.9)
            xx += bw


def set_bedroom(c):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#1a0e10", "#2c1515", "#120809"], [0, 0.55, 1]))
    _wall_texture(c, (0, 0, W, 700), "#2c1515", 5)
    # window with moon, cool light spill
    rrect(c, 1220, 120, 420, 380, 6, "#0a0c13")
    fill_shader(c, skia.Rect(1236, 136, 1624, 484), linear(1236, 136, 1624, 484, ["#24365c", "#0c1528"]))
    line(c, 1430, 136, 1430, 484, "#0a0c13", 14)
    c.drawCircle(1540, 220, 40, P("#e6eeff", a=0.9))
    for k in range(25):
        rnd = random.Random(k)
        c.drawCircle(rnd.uniform(1240, 1620), rnd.uniform(140, 480), rnd.uniform(1, 2.4), P("#ffffff", a=0.6))
    # headboard + bed
    rrect(c, 120, 420, 1000, 260, 30, "#24130f")
    rrect(c, 80, 620, 1240, 200, 30, "#3b3536")
    fill_shader(c, skia.Rect(80, 620, 1320, 820), linear(0, 620, 0, 820, ["#5a5253", "#2a2526"]))
    rrect(c, 160, 560, 330, 110, 50, "#cfc6b8")
    rrect(c, 160, 560, 330, 110, 50, "#000000", a=0.25)
    # nightstand
    rrect(c, 1180, 640, 260, 190, 8, "#1c100c")
    c.drawRect(skia.Rect(1180, 820, 1440, H), P("#120807"))
    fill_shader(c, skia.Rect(0, 820, W, H), linear(0, 820, 0, H, ["#140a08", "#060303"]))


def set_desk_close(c):
    """Desk surface seen from the front (for sitting shots)."""
    set_room(c)


def set_studio(c, col="#101015"):
    fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H * 0.45, W * 0.7, [col, "#050506"]))
    fill_shader(c, skia.Rect(0, 760, W, H), radial(W / 2, 800, 800, [("#2a2a33", 0.7), ("#000000", 0)]))


def set_mat(c):
    """Top-down green cutting mat on a wooden desk (for the cycle diagram)."""
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, W, H, ["#5a3a22", "#3b2414"]))
    rnd = random.Random(2)
    for _ in range(140):
        y = rnd.uniform(0, H)
        line(c, 0, y, W, y + rnd.uniform(-30, 30), rnd.choice(("#2a170b", "#6b4a2e")), rnd.uniform(1, 4),
             rnd.uniform(0.15, 0.4))
    rrect(c, 260, 60, 1400, 960, 18, "#0f3a2e")
    rrect(c, 270, 70, 1380, 940, 14, "#1d5a45")
    for k in range(0, 1380, 46):
        line(c, 270 + k, 70, 270 + k, 1010, "#2f7a5f", 1.5 if k % 230 else 3, 0.55)
    for k in range(0, 940, 46):
        line(c, 270, 70 + k, 1650, 70 + k, "#2f7a5f", 1.5 if k % 230 else 3, 0.55)
    line(c, 270, 70, 1650, 1010, "#2f7a5f", 2, 0.35)
    line(c, 1650, 70, 270, 1010, "#2f7a5f", 2, 0.35)
    c.drawCircle(960, 540, 300, P("#2f7a5f", 2, 0.45))


def set_hall(c):
    """Narrow warm hallway, one-point perspective, door at the end, stairs on the right."""
    vx, vy = 900, 470
    c.drawRect(skia.Rect(0, 0, W, H), P("#2a1c0e"))
    # far wall + door
    fill_shader(c, skia.Rect(700, 260, 1100, 760), linear(0, 260, 0, 760, ["#c99a3a", "#8a6420"]))
    rrect(c, 800, 330, 190, 430, 4, "#5a3b16")
    rrect(c, 812, 342, 166, 418, 3, "#b98a32")
    c.drawCircle(950, 560, 9, P("#3a2408"))
    # left wall
    c.drawPath(poly([(0, -60), (700, 260), (700, 760), (0, H + 60)]), P("#a87a2a"))
    fill_shader(c, skia.Rect(0, 0, 700, H), linear(0, 0, 700, 0, [("#000000", 0.55), ("#000000", 0)]))
    for i, (x0, w0) in enumerate(((120, 120), (380, 80), (560, 50))):
        y0 = 180 + i * 60
        c.drawPath(poly([(x0, y0 + 40 * (1 - i * 0.3)), (x0 + w0, y0 + 50), (x0 + w0, y0 + 50 + w0 * 1.1),
                         (x0, y0 + 40 + w0 * 1.4)]), P("#2a1a0a", a=0.85))
    # right wall + stairs
    c.drawPath(poly([(W, -60), (1100, 260), (1100, 760), (W, H + 60)]), P("#7a5418"))
    for s_ in range(9):
        y = 760 + s_ * 40
        x = 1100 + s_ * 95
        c.drawRect(skia.Rect(x, 200 + s_ * 20, x + 95, y), P("#5a3810", a=0.6))
        line(c, x, y - 40, x + 95, y - 40, "#e0a040", 5, 0.8)
    # floor + ceiling light
    c.drawPath(poly([(0, H + 60), (700, 760), (1100, 760), (W, H + 60)]), P("#3a2410"))
    fill_shader(c, skia.Rect(0, 760, W, H), linear(0, 760, 0, H, [("#ffcc66", 0.15), ("#000000", 0.4)]))
    c.drawPath(poly([(0, -60), (700, 260), (1100, 260), (W, -60)]), P("#1a1006"))
    fill_shader(c, skia.Rect(0, 0, W, H), radial(vx, 300, 700, [("#ffd27a", 0.35), ("#ffd27a", 0)]))


SETS = {"hall": set_hall, "room": set_room, "bedroom": set_bedroom, "studio": set_studio, "mat": set_mat}


def draw_set(c, name, blur=6.0, a=1.0, s=1.0, cx=W / 2, cy=H / 2, dx=0.0, dy=0.0):
    img = cached((name, blur), SETS[name], blur)
    blit(c, img, dx, dy, a, s, cx, cy)


def desk_front(c, y=780, x0=200, x1=1500, col="#3a2618"):
    rrect(c, x0, y, x1 - x0, 34, 6, "#4a3220")
    fill_shader(c, skia.Rect(x0, y, x1, y + 34), linear(0, y, 0, y + 34, ["#6b4a2e", "#3a2618"]))
    c.drawRect(skia.Rect(x0 + 30, y + 34, x0 + 60, H), P("#1d130c"))
    c.drawRect(skia.Rect(x1 - 60, y + 34, x1 - 30, H), P("#1d130c"))
    fill_shader(c, skia.Rect(x0, y + 34, x1, y + 140), linear(0, y + 34, 0, y + 140, [("#000000", 0.6), ("#000000", 0)]))


def chair(c, x, y, s=1.0):
    with xf(c, x, y, s):
        rrect(c, -90, -10, 150, 22, 8, "#1c1414")
        rrect(c, -100, -230, 26, 240, 10, "#1c1414")
        line(c, -70, 12, -90, 230, "#141010", 12)
        line(c, 40, 12, 60, 230, "#141010", 12)
