"""Timeline for the space documentary. All times are absolute seconds in the voiceover."""
import math
import random

import skia

from cosmos import *  # noqa: F401,F403
import cosmos

# ---- no on-screen text anywhere (titles, facts, labels)
def _no_text(*_a, **_k):
    return 0


text = fact = doc_title = _no_text
cosmos.text = _no_text

# ---- presenter only where he adds meaning (reaction / human scale / interaction)
GUIDE_WINDOWS = [(74.6, 77.4), (93.3, 98.1), (190.0, 198.5), (215.2, 219.2), (317.4, 321.0), (331.7, 335.5),
                 (484.9, 487.6), (641.1, 1e9)]
_guide = guide


def guide(c, x, y, t, *args, **kw):
    if any(w0 <= t < w1 for w0, w1 in GUIDE_WINDOWS):
        _guide(c, x, y, t, *args, **kw)


# ======================================================================= shared helpers
def bg(c, t, drift=(-5, 0), tint_col=None):
    deep_sky(c, t, drift, tint_col)


def orbit(c, x, y, R, tilt=0.35, col="#8ec8ff", a=0.5, w=2.5, prog=1.0, rot=0.0):
    if prog <= 0:
        return
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    pth = skia.Path()
    pth.addArc(skia.Rect(-R, -R * tilt, R, R * tilt), 90, 360 * clamp(prog))
    c.drawPath(pth, P(col, w, a))
    c.restore()


def on_orbit(x, y, R, ang, tilt=0.35):
    return x + math.cos(ang) * R, y + math.sin(ang) * R * tilt


def earths_fill(c, x, y, R, k, er=9.0, seed=0):
    """Fill a disc with tiny Earths, sweeping in from the centre outward (k = 0..1)."""
    if k <= 0:
        return
    c.save()
    pth = skia.Path()
    pth.addCircle(x, y, R)
    c.clipPath(pth, skia.ClipOp.kIntersect, True)
    step = er * 2.15
    n = int(R / step) + 1
    pts = []
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            px, py = x + i * step + (j % 2) * step / 2, y + j * step * 0.9
            d = math.hypot(px - x, py - y)
            if d < R - er * 0.6:
                pts.append((d, px, py))
    pts.sort()
    m = int(len(pts) * k)
    for d, px, py in pts[:m]:
        with xf(c, px, py, alpha=0.8):
            earth_icon(c, 0, 0, er)
    c.restore()


def balance(c, x, y, k, left, right, s=1.0, t=0.0):
    """Balance scale. k>0 tips left pan down. left/right draw(c, px, py) at the pan."""
    ang = math.radians(16 * clamp(k, -1, 1))
    with xf(c, x, y, s):
        rrect(c, -16, 0, 32, 330, 8, "#5a6478")
        rrect(c, -120, 320, 240, 26, 12, "#5a6478")
        c.drawPath(poly([(-34, 6), (34, 6), (0, -36)]), P("#9aa3b3"))
        lx, ly = -330 * math.cos(ang), 330 * math.sin(ang)
        rx, ry = 330 * math.cos(ang), -330 * math.sin(ang)
        line(c, lx, ly - 30, rx, ry - 30, "#c9ced8", 14)
        c.drawCircle(0, -30, 14, P("#e3e7ee"))
        for (px, py, draw) in ((lx, ly - 30, left), (rx, ry - 30, right)):
            line(c, px, py, px - 120, py + 180, "#9aa3b3", 3)
            line(c, px, py, px + 120, py + 180, "#9aa3b3", 3)
            pth = skia.Path()
            pth.moveTo(px - 140, py + 180)
            pth.quadTo(px, py + 240, px + 140, py + 180)
            pth.close()
            c.drawPath(pth, P("#8a94a8"))
            draw(c, px, py + 178)


def ring_label(c, x, y, r, s, col="#8ec8ff", a=1.0, size=30):
    text(c, s, x, y - r - 22, size, col, "Bold", a=a, shadow=True)


def bar(c, x, y, w, h, col, k=1.0, a=1.0):
    if k <= 0:
        return
    rrect(c, x, y, max(h, w * k), h, h / 2, col, a)


def flash(c, x, y, k, col="#ffffff", r=300):
    if 0 < k < 1:
        glow(c, x, y, r * (0.4 + k), col, 0.9 * (1 - k))


def light_ray(c, pts, col="#ffe9a8", w=4, a=0.9, prog=1.0):
    pth = skia.Path()
    n = max(2, int(len(pts) * clamp(prog)))
    pth.moveTo(*pts[0])
    for p_ in pts[1:n]:
        pth.lineTo(*p_)
    c.drawPath(pth, P(col, w * 3, a * 0.18))
    c.drawPath(pth, P(col, w, a))


def ice_chunk(c, x, y, r, rot, col="#dfefff"):
    with xf(c, x, y, 1, rot):
        pth = skia.Path()
        for i in range(7):
            ang = i / 7 * TAU
            rr = r * (0.75 + 0.25 * math.sin(i * 2.3 + r))
            (pth.moveTo if i == 0 else pth.lineTo)(math.cos(ang) * rr, math.sin(ang) * rr)
        pth.close()
        c.drawPath(pth, P(col))
        c.drawPath(pth, P("#8fb6d8", max(1.5, r * 0.08)))
        c.drawCircle(-r * 0.25, -r * 0.25, r * 0.18, P("#ffffff", a=0.7))


def house(c, x, y, s, col="#c96a4a"):
    with xf(c, x, y, s):
        rrect(c, -60, -70, 120, 70, 4, "#e8dcc8")
        c.drawPath(poly([(-75, -70), (0, -130), (75, -70)]), P(col))
        rrect(c, -15, -40, 30, 40, 3, "#6a4a3a")
        rrect(c, 25, -55, 22, 20, 2, "#8ec8ff")


def city(c, x, y, w, s=1.0, col="#26344c", lights=True):
    rnd = random.Random(8)
    xx = x
    while xx < x + w:
        bw = rnd.uniform(30, 70) * s
        bh = rnd.uniform(60, 240) * s
        c.drawRect(skia.Rect(xx, y - bh, xx + bw - 4 * s, y), P(col))
        if lights:
            for k in range(int(bh / (22 * s))):
                if rnd.random() > 0.5:
                    c.drawRect(skia.Rect(xx + 8 * s, y - bh + 10 * s + k * 22 * s, xx + 14 * s,
                                         y - bh + 16 * s + k * 22 * s), P("#ffd37a", a=0.7))
        xx += bw


def lighthouse(c, x, y, s, t, beam=True):
    with xf(c, x, y, s):
        if beam:
            ang = math.sin(t * 1.4) * 0.8
            for sgn in (-1, 1):
                a0 = ang + (0 if sgn > 0 else math.pi)
                pth = skia.Path()
                pth.moveTo(0, -330)
                pth.lineTo(math.cos(a0 - 0.1) * 1400, -330 + math.sin(a0 - 0.1) * 200)
                pth.lineTo(math.cos(a0 + 0.1) * 1400, -330 + math.sin(a0 + 0.1) * 200)
                pth.close()
                c.drawPath(pth, P("#fff2b0", a=0.25 * max(0, math.cos(a0) * sgn) + 0.08))
        c.drawPath(poly([(-60, 0), (60, 0), (36, -300), (-36, -300)]), P("#e8e0d0"))
        for k in range(3):
            c.drawPath(poly([(-58 + k * 8, -40 - k * 90), (58 - k * 8, -40 - k * 90), (55 - k * 8, -80 - k * 90),
                             (-55 + k * 8, -80 - k * 90)]), P("#c0392b"))
        rrect(c, -44, -360, 88, 60, 8, "#2a3346")
        glow(c, 0, -330, 80, "#fff2b0", 0.8)
        c.drawPath(poly([(-50, -360), (50, -360), (0, -400)]), P("#c0392b"))
        rrect(c, -140, 0, 280, 40, 10, "#3a4558")


def fork(c, x, y, s, rot=0):
    with xf(c, x, y, s, rot):
        rrect(c, -5, 0, 10, 90, 5, "#c9ced8")
        rrect(c, -18, -40, 36, 44, 8, "#c9ced8")
        for k in range(4):
            rrect(c, -16 + k * 10, -80, 5, 46, 2, "#c9ced8")


def magnet(c, x, y, s, rot=0):
    with xf(c, x, y, s, rot):
        pth = skia.Path()
        pth.addArc(skia.Rect(-50, -50, 50, 50), 180, -180)
        c.drawPath(pth, P("#d0352b", 30))
        rrect(c, -65, -60, 30, 60, 4, "#d0352b")
        rrect(c, 35, -60, 30, 60, 4, "#d0352b")
        rrect(c, -65, -80, 30, 22, 3, "#e3e7ee")
        rrect(c, 35, -80, 30, 22, 3, "#e3e7ee")


def thermometer(c, x, y, s, k, col="#ff5a2a"):
    with xf(c, x, y, s):
        rrect(c, -22, -260, 44, 280, 22, "#e3e7ee")
        c.drawCircle(0, 30, 40, P("#e3e7ee"))
        c.drawCircle(0, 30, 30, P(col))
        rrect(c, -10, -240 + 240 * (1 - k), 20, 240 * k + 30, 10, col)


def dish(c, x, y, s, rot=-30):
    with xf(c, x, y, s):
        rrect(c, -10, -60, 20, 60, 5, "#9aa3b3")
        with xf(c, 0, -60, 1, rot):
            pth = skia.Path()
            pth.addArc(skia.Rect(-70, -40, 70, 40), 0, 180)
            pth.close()
            c.drawPath(pth, P("#e3e7ee"))
            line(c, 0, 0, 0, -50, "#9aa3b3", 4)


def thumbs_up(c, x, y, s, col="#ffffff"):
    with xf(c, x, y, s):
        rrect(c, -70, -10, 34, 90, 8, col)
        rrect(c, -30, -10, 100, 90, 22, col)
        pth = skia.Path()
        pth.moveTo(-28, -6)
        pth.lineTo(0, -80)
        pth.quadTo(24, -86, 22, -60)
        pth.lineTo(14, -10)
        pth.close()
        c.drawPath(pth, P(col))


def share_icon(c, x, y, s, col="#ffffff"):
    with xf(c, x, y, s):
        pts = [(-50, 0), (40, -50), (40, 50)]
        for (a, b) in ((0, 1), (0, 2)):
            line(c, pts[a][0], pts[a][1], pts[b][0], pts[b][1], col, 10)
        for (px, py) in pts:
            c.drawCircle(px, py, 24, P(col))


# ======================================================================= 1. JUPITER (0 - 8.7)
def s_jupiter(c, t):
    if t < 5.0:
        cam(c, push(t, 0, 5, 1.0, 1.1), 960, 540, t)
        bg(c, t)
        planet(c, 1250, 540, 360, "jupiter", t, spin=0.08, grs=True)
        earths_fill(c, 1250, 540, 360, ease_out(at(t, 2.4, 2.2)), er=8.5)
        guide(c, 430, 560, t, keys(t, [(0, "float"), (0.9, "float_point"), (2.6, "float_wow")]), s=0.95,
              expr="smile" if t < 2.6 else "wide", look=(1, 0))
        doc_title(c, t, 0.3, "JUPITER", "Largest planet in our solar system", dur=4.2)
        fact(c, t, 3.0, "1,300+ EARTHS", 1250, 980, 48, "#ffd36b")
        return
    cam(c, push(t, 5, 8.8, 1.02, 1.08), 960, 560, t)
    bg(c, t)
    k = ease_out(at(t, 5.3, 1.4))
    others = [("saturn", 46), ("neptune", 26), ("neptune", 25), ("earth", 14), ("earth", 13), ("mars", 9),
              ("mercury", 7)]

    def left(cc, px, py):
        planet(cc, px, py - 110, 110, "jupiter", t, spin=0.08, grs=True)

    def right(cc, px, py):
        xx = px - 120
        for kind, r in others:
            planet(cc, xx + r, py - r, r, kind, t, spin=0.1)
            xx += 2 * r + 4

    balance(c, 1050, 470, 0.8 * k, left, right, s=0.95, t=t)
    guide(c, 300, 690, t, keys(t, [(5.0, "present"), (6.3, "point")]), s=0.9, space=False, look=(1, 0))
    fact(c, t, 6.2, "2.5 × MASS OF ALL OTHER PLANETS", 1050, 110, 44, "#ffd36b")


# ======================================================================= 2. SOMETHING BIGGER (8.7 - 16.2)
def s_bigger(c, t):
    if t < 13.2:
        cam(c, push(t, 8.7, 13.2, 1.0, 0.92), 960, 540, t)
        bg(c, t)
        k = smooth(at(t, 10.4, 2.4))
        glow(c, 1300, 520, 900 * k + 1, "#ff6a8a", 0.15 * k)
        if k > 0:
            planet(c, 1350, 560, 120 + 380 * k, "proto", t, spin=0.04, dark=0.9)
        planet(c, lerp(1050, 820, k), lerp(560, 640, k), lerp(260, 120, k), "jupiter", t, spin=0.08, grs=True)
        guide(c, 330, 600, t, keys(t, [(8.7, "float"), (9.3, "float_point"), (11.0, "float_wow")]), s=0.9,
              expr="smile" if t < 11 else "wide", look=(1, -0.2))
        return
    # Subaru + Hubble split
    for side in (0, 1):
        c.save()
        clip_half(c, side, seed=5)
        if side == 0:
            fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#05081a", "#1a2440"]))
            for (u, v, r, ph) in FAR[:300]:
                c.drawCircle(u * 960, v * 700, r, P("#dfe9ff", a=0.7))
            mountain(c, 0, [(0, 820), (200, 700), (420, 560), (560, 600), (760, 760), (960, 840)], "#0d1220",
                     "#3a4a6a")
            observatory(c, 420, 575, 0.75, t, open_=ease_out(at(t, 13.5, 1.0)))
            k = at(t, 14.0, 0.8)
            pth = skia.Path()
            pth.moveTo(410, 400)
            pth.lineTo(250, -40)
            pth.lineTo(330, -40)
            pth.close()
            c.drawPath(pth, P("#9fd0ff", a=0.12 * k))
            guide(c, 680, 700, t, "point_up", s=0.55, who="yuki", space=False, talk=0, expr="focus", face=-1,
                  look=(-0.5, -1))
            doc_title(c, t, 13.6, "SUBARU TELESCOPE", "Mauna Kea, Hawaii", dur=3, x=60, y=990)
        else:
            bg(c, t)
            planet(c, 1440, 1500, 640, "earth", t, spin=0.03)
            hubble(c, 1440, 400, 0.9, t)
            doc_title(c, t, 14.6, "HUBBLE", "Space telescope", dur=2, x=1020, y=990)
        c.restore()
    jagged_split(c, seed=5)


# ======================================================================= 3. AB AURIGAE (16.2 - 33.5)
def s_ab_aur(c, t):
    if t < 24.6:
        cam(c, push(t, 16.2, 24.6, 1.12, 1.0), 960, 540, t)
        bg(c, t, tint_col="#6a3a5a")
        proto_disk(c, 960, 540, 620, t, front=False)
        star(c, 960, 540, 46, "#bfe0ff", t)
        proto_disk(c, 960, 540, 620, t, front=True)
        ang = 0.9 + t * 0.12
        px, py = 960 + math.cos(ang) * 470 * 0.98, 540 + math.sin(ang) * 470 * 0.38
        c.save()
        c.translate(960, 540)
        c.rotate(-14)
        px, py = math.cos(ang) * 460, math.sin(ang) * 460 * 0.38
        glow(c, px, py, 120, "#ff6a8a", 0.4)
        planet(c, px, py, 30, "proto", t, light=(-math.cos(ang) * 0.5, -math.sin(ang) * 0.5))
        c.restore()
        doc_title(c, t, 16.8, "AB AURIGAE", "A very young star", dur=6)
        fact(c, t, 21.6, "< 5 MILLION YEARS OLD", 960, 140, 46, "#bfe0ff", dur=3.0)
        return
    if t < 28.2:
        cam(c, push(t, 24.6, 28.2, 1.0, 1.04), 960, 540, t)
        bg(c, t)
        sun(c, 330, 380, 120, t)
        star(c, 330, 720, 34, "#bfe0ff", t)
        k = ease_out(at(t, 25.0, 1.6))
        bar(c, 520, 360, 1200, 44, "#ffb52e", k)
        bar(c, 520, 700, 1200 * 5 / 4600 + 14, 44, "#8ec8ff", ease_out(at(t, 25.6, 0.6)))
        fact(c, t, 25.4, "4.6 BILLION YEARS", 1120, 330, 40, "#ffd36b")
        fact(c, t, 26.0, "5 MILLION YEARS", 760, 680, 40, "#8ec8ff")
        guide(c, 1500, 790, t, "shrug" if t > 26.4 else "present", s=0.62, space=False, face=-1, look=(-1, 0))
        return
    cam(c, push(t, 28.2, 33.5, 1.0, 1.08), 960, 540, t)
    bg(c, t)
    # Auriga pattern
    pts = [(1180, 260), (1420, 330), (1460, 600), (1250, 760), (1060, 560)]
    k = ease_out(at(t, 29.6, 1.4))
    for i in range(5):
        a_, b_ = pts[i], pts[(i + 1) % 5]
        line(c, a_[0], a_[1], lerp(a_[0], b_[0], k), lerp(a_[1], b_[1], k), "#8ec8ff", 2.5, 0.6)
    for (x, y) in pts:
        star(c, x, y, 8, "#ffffff", t, flare=0.8)
    tx, ty = 1300, 470
    star(c, tx, ty, 12, "#bfe0ff", t)
    you_are_here(c, tx, ty, t, "AB AURIGAE", "#bfe0ff", a=at(t, 28.6, 0.5))
    earth_icon(c, 260, 820, 40)
    kd = ease_out(at(t, 28.8, 1.6))
    pth = skia.Path()
    pth.moveTo(300, 800)
    pth.lineTo(lerp(300, tx - 20, kd), lerp(800, ty + 10, kd))
    c.drawPath(pth, skia.Paint(AntiAlias=True, Color=C("#ffd36b", 0.8), Style=skia.Paint.kStroke_Style,
                               StrokeWidth=4, PathEffect=skia.DashPathEffect.Make([16, 12], -t * 40)))
    fact(c, t, 29.2, "531 LIGHT-YEARS", 700, 600, 46, "#ffd36b")
    fact(c, t, 30.6, "CONSTELLATION AURIGA", 1260, 880, 34, "#8ec8ff")
    guide(c, 330, 600, t, keys(t, [(28.2, "point"), (30.4, "point_up")]), s=0.6, space=False, look=(1, -0.5))


# ======================================================================= 4. THE DISC (33.5 - 46.1)
def s_disc(c, t):
    cam(c, push(t, 33.5, 46.1, 1.0, 1.15), 900, 560, t)
    bg(c, t, tint_col="#6a3a5a")
    feed = at(t, 36.6, 0.6)
    clump = smooth(at(t, 39.5, 5.0))
    proto_disk(c, 1060, 560, 700, t, front=False, a=1 - 0.4 * clump)
    star(c, 1060, 560, 50 + 8 * feed * math.sin(t * 3), "#bfe0ff", t)
    proto_disk(c, 1060, 560, 700, t, front=True, a=1 - 0.4 * clump)
    if feed:
        c.save()
        c.translate(1060, 560)
        c.rotate(-14)
        for i in range(14):
            u = ((t * 0.35 + i / 14) % 1)
            ang = i * 1.7 + u * 5
            rr = 520 * (1 - u)
            c.drawCircle(math.cos(ang) * rr, math.sin(ang) * rr * 0.38, 4, P("#ffe2a8", a=feed * (0.3 + 0.7 * u)))
        c.restore()
    if clump > 0:
        bodies = [(0.35, 22, "mars"), (0.55, 34, "proto"), (0.72, 16, "mercury"), (0.88, 12, "ganymede"),
                  (0.95, 8, "mercury")]
        c.save()
        c.translate(1060, 560)
        c.rotate(-14)
        for i, (u, r, kind) in enumerate(bodies):
            ang = i * 1.3 + t * 0.35 / (u ** 1.5)
            px, py = math.cos(ang) * 620 * u, math.sin(ang) * 620 * u * 0.38
            planet(c, px, py, r * clump, kind, t, atm=False)
        for i in range(14):
            ang = i * 0.9 + t * 0.2
            px, py = math.cos(ang) * 660, math.sin(ang) * 660 * 0.38
            c.drawCircle(px, py, 4 * clump, P("#b0a090", a=clump))
        c.restore()
    guide(c, 240, 640, t, keys(t, [(33.5, "float"), (36.6, "float_point"), (40.0, "float_wow"), (42.5, "float")]),
          s=0.8, expr="smile" if t < 40 else "happy", look=(1, 0))
    k = window(t, 41.0, 46.0, 0.4)
    if k:
        labs = ["PLANETS", "DWARF PLANETS", "COMETS", "ASTEROIDS"]
        for i, lab in enumerate(labs):
            kk = ease_out(at(t, 41.0 + i * 0.75, 0.4))
            text(c, lab, 1620, 760 + i * 52, 34, "#ffd9a8", "Bold", a=k * kk, shadow=True)


# ======================================================================= 5. AB AUR b (46.1 - 61.1)
def s_ab_b(c, t):
    if t < 50.0:
        cam(c, push(t, 46.1, 50.0, 1.0, 1.05), 960, 560, t)
        bg(c, t)
        k = ease_out(at(t, 47.4, 1.2))

        def left(cc, px, py):
            glow(cc, px, py - 90, 160, "#ff6a8a", 0.3)
            planet(cc, px, py - 90, 90, "proto", t)

        def right(cc, px, py):
            for i in range(9):
                planet(cc, px - 100 + (i % 3) * 100, py - 40 - (i // 3) * 70, 34, "jupiter", t, atm=False)

        balance(c, 960, 430, 0.0, left, right, s=0.95)
        doc_title(c, t, 46.4, "AB AURIGAE b", "Gas giant", dur=3.4)
        fact(c, t, 47.8, "9 × JUPITER'S MASS", 960, 120, 48, "#ffd36b")
        guide(c, 1680, 700, t, "present", s=0.75, space=False, face=-1, look=(-1, 0))
        return
    cam(c, push(t, 50.0, 61.1, 1.0, 1.06), 960, 540, t)
    bg(c, t)
    cx, cy = 760, 560
    if t < 54.3:
        star(c, cx, cy, 30, "#bfe0ff", t)
        orbit(c, cx, cy, 560, 0.45, "#ff8aa8", 0.5, 3, prog=ease_out(at(t, 50.2, 1.2)))
        orb = ((t - 50.0) / 4.3)
        ang = math.pi * 0.2 + orb * TAU
        px, py = on_orbit(cx, cy, 560, ang, 0.45)
        planet(c, px, py, 26, "proto", t)
        clock(c, 1620, 360, 0.8, (t - 50.0) / 4.3, "#ff8aa8")
        n = round(count(t, 50.2, 3.4, 0, 588))
        fact(c, t, 50.2, f"{n} EARTH-YEARS PER ORBIT", 1620, 560, 34, "#ff8aa8")
        return
    # 94 AU
    star(c, 220, 560, 34, "#ffd36b", t)
    k1 = ease_out(at(t, 54.4, 0.6))
    earth_icon(c, 220 + 17, 640, 6)
    dim_line(c, 220, 680, 237, 680, "#8ec8ff", prog=k1)
    text(c, "1 AU", 228, 730, 26, "#8ec8ff", "Bold", a=k1)
    k2 = ease_out(at(t, 55.2, 2.6))
    dim_line(c, 220, 480, 220 + 1600 * k2, 480, "#ff8aa8", w=4, prog=1.0)
    planet(c, 220 + 1600 * k2, 480, 24, "proto", t)
    fact(c, t, 56.0, "94 AU", 1120, 420, 56, "#ff8aa8")
    fact(c, t, 58.3, "94 × EARTH–SUN DISTANCE", 1120, 860, 40, "#ffffff")
    guide(c, 980, 690, t, keys(t, [(54.3, "point"), (58.3, "wow")]), s=0.55, space=False, look=(1, 0),
          expr="smile")


# ======================================================================= 6. HOW IT FORMS (61.1 - 81.1)
_SWIRL = [(random.Random(i).uniform(0, TAU), random.Random(i + 5).uniform(0.2, 1)) for i in range(220)]


def s_forming(c, t):
    if t < 74.6:
        cam(c, push(t, 61.1, 74.6, 1.0, 1.04), 960, 540, t)
        bg(c, t)
        # left: core accretion
        lk = 1 if t < 68.6 else 0.45
        with xf(c, 0, 0, alpha=lk):
            cx, cy = 480, 480
            core = 20 + 60 * smooth(at(t, 63.8, 5.0))
            for i, (ang, u) in enumerate(_SWIRL[:120]):
                ph = (t * 0.25 + u) % 1
                rr = 330 * (1 - ph) + core
                a_ = ang + ph * 4
                c.drawCircle(cx + math.cos(a_) * rr, cy + math.sin(a_) * rr * 0.9, 3.5,
                             P("#c8a27a", a=0.3 + 0.6 * ph))
            planet(c, cx, cy, core, "mars", t, atm=False)
            text(c, "SLOW: CORE FIRST", cx, 920, 38, "#ffd9a8", "Bold", a=at(t, 64.4, 0.6), shadow=True)
        # right: gravitational collapse
        rk = at(t, 68.6, 0.6)
        if rk:
            cx, cy = 1440, 480
            col = smooth(at(t, 71.7, 2.8))
            R = lerp(420, 70, col)
            glow(c, cx, cy, R * 1.4, "#ff6a8a", 0.25 * rk)
            for i, (ang, u) in enumerate(_SWIRL):
                a_ = ang + t * (0.3 + 1.6 * col) / (0.3 + u)
                rr = R * u
                c.drawCircle(cx + math.cos(a_) * rr, cy + math.sin(a_) * rr, 3 + 2 * u,
                             P("#ff9ab8", a=rk * (0.25 + 0.5 * (1 - u))))
            if col > 0.6:
                planet(c, cx, cy, 70 * (col - 0.6) / 0.4 + 1, "proto", t)
            text(c, "FAST: GAS COLLAPSES", cx, 920, 38, "#ff9ab8", "Bold", a=rk, shadow=True)
        guide(c, 960, 690, t, keys(t, [(61.1, "talk"), (63.8, "point"), (68.6, "think"), (69.3, "point")]),
              s=0.62, space=False, face=1 if t > 68.6 else -1, look=(1 if t > 68.6 else -1, 0),
              expr="focus" if t > 68.6 else "smile")
        return
    if t < 77.4:
        cam(c, push(t, 74.6, 77.4, 1.0, 1.05), 960, 540, t)
        bg(c, t)
        planet(c, 520, 420, 80, "mars", t)
        planet(c, 1400, 420, 110, "proto", t)
        guide(c, 960, 640, t, "open", s=0.9, space=False, expr="happy", look=(0, -0.3))
        fact(c, t, 75.0, "MORE THAN ONE WAY", 960, 950, 48, "#ffffff")
        return
    cam(c, push(t, 77.4, 81.1, 1.2, 1.0), 960, 540, t)
    bg(c, t)
    galaxy(c, 960, 540, 520, t, "milkyway", tilt=0.55, rot=-12, spin=3)
    rnd = random.Random(3)
    for i in range(22):
        k = back_out(at(t, 77.8 + i * 0.12, 0.3))
        if k <= 0:
            continue
        ang = rnd.uniform(0, TAU)
        rr = rnd.uniform(120, 480)
        x, y = 960 + math.cos(ang) * rr, 540 + math.sin(ang) * rr * 0.55
        with xf(c, x, y, k):
            c.drawCircle(0, 0, 5, P("#ffe08a"))
            for j in range(rnd.randint(1, 3)):
                rr2 = 14 + j * 9
                c.drawOval(skia.Rect(-rr2, -rr2 * 0.5, rr2, rr2 * 0.5), P("#8ec8ff", 1.5, 0.7))


# ======================================================================= 7. GQ LUPI b (81.1 - 104.1)
def s_gq(c, t):
    if t < 89.4:
        cam(c, push(t, 81.1, 89.4, 1.0, 1.08), 960, 540, t)
        bg(c, t, tint_col="#5a3a2a")
        star(c, 760, 520, 40, "#ffcf8a", t)
        ang = 0.4 + t * 0.06
        px, py = on_orbit(760, 520, 600, ang, 0.32)
        orbit(c, 760, 520, 600, 0.32, "#ff8a6a", 0.35)
        glow(c, px, py, 90, "#ff6a4a", 0.35)
        planet(c, px, py, 40, "brown", t)
        doc_title(c, t, 84.6, "GQ LUPI b", "Found in 2005", dur=4.6)
        guide(c, 260, 640, t, keys(t, [(81.1, "float"), (85.0, "float_point")]), s=0.7, look=(1, 0))
        return
    if t < 93.3:
        cam(c, push(t, 89.4, 93.3, 1.0, 1.04), 960, 540, t)
        bg(c, t)
        sun(c, 300, 540, 34, t)
        k1 = ease_out(at(t, 89.8, 0.8))
        orbit(c, 300, 540, 560, 1.0, "#9aa3b3", 0.4, 2, rot=-90, prog=k1) if False else None
        dim_line(c, 300, 640, 300 + 560 * k1, 640, "#9aa3b3", prog=1)
        planet(c, 300 + 560 * k1, 640, 10, "mercury", t, atm=False)
        text(c, "SUN → PLUTO", 580, 700, 28, "#9aa3b3", "Bold", a=k1)
        k2 = ease_out(at(t, 90.8, 1.6))
        dim_line(c, 300, 440, 300 + 1400 * k2, 440, "#ff8a6a", w=4, prog=1)
        planet(c, 300 + 1400 * k2, 440, 22, "brown", t)
        fact(c, t, 91.2, "× 2.5", 1000, 400, 54, "#ff8a6a")
        return
    if t < 98.1:
        cam(c, push(t, 93.3, 98.1, 1.0, 1.05), 960, 540, t)
        bg(c, t)
        planet(c, 480, 470, 120, "jupiter", t)
        text(c, "PLANET", 480, 680, 36, "#ffd9a8", "Bold")
        star(c, 1440, 470, 70, "#c8583a", t, core="#ff9a6a")
        text(c, "BROWN DWARF", 1440, 680, 36, "#ff9a6a", "Bold")
        sw = math.sin((t - 93.3) * 2.2)
        planet(c, 960 + 200 * sw, 330, 50, "brown", t)
        text(c, "?", 960 + 200 * sw, 240, 64, "#ffffff", "Black", a=at(t, 93.6, 0.4))
        guide(c, 960, 720, t, keys(t, [(93.3, "think"), (95.2, "shrug")]), s=0.7, space=False, expr="focus",
              look=(sw, -0.4))
        fact(c, t, 96.6, "A FAILED STAR", 1440, 760, 32, "#ffffff")
        return
    cam(c, push(t, 98.1, 104.1, 1.0, 1.05), 960, 560, t)
    bg(c, t)
    k = ease_out(at(t, 99.6, 1.4))
    planet(c, 480, 600, 100, "jupiter", t)
    planet(c, 1260, 600, 100 + 250 * k, "brown", t)
    fact(c, t, 100.2, "LARGEST EVER FOUND?", 1260, 140, 44, "#ff8a6a")
    fact(c, t, 102.0, "3.5 × JUPITER'S RADIUS", 960, 1000, 44, "#ffd36b")
    guide(c, 480, 860, t, "wow" if t > 100 else "point", s=0.42, space=False, expr="wide", face=1, look=(1, -0.6))


# ======================================================================= 8. UY SCUTI (104.1 - 118.7)
def s_uy(c, t):
    if t < 110.6:
        cam(c, push(t, 104.1, 110.6, 1.0, 0.94), 960, 540, t)
        bg(c, t)
        cx, cy = 960, 540
        for i, (R, kind) in enumerate(((60, "mercury"), (95, "mars"), (130, "earth"), (200, "mars"),
                                       (420, "jupiter"))):
            orbit(c, cx, cy, R, 0.85, "#8ec8ff", 0.45, 2)
            ang = 1.2 + i * 1.1 + t * 0.3 / (R / 100)
            px, py = on_orbit(cx, cy, R, ang, 0.85)
            planet(c, px, py, 8 if kind != "jupiter" else 18, kind, t, atm=False)
        sun(c, cx, cy, 14, t)
        k = smooth(at(t, 106.5, 3.2))
        if k > 0:
            supergiant(c, cx, cy, 20 + 450 * k, t)
            orbit(c, cx, cy, 420, 0.85, "#ffffff", 0.6 * k, 3)
            text(c, "JUPITER'S ORBIT", cx + 300, cy - 400, 30, "#ffffff", "Bold", a=k, shadow=True)
        doc_title(c, t, 104.4, "UY SCUTI", "Biggest known star", dur=5)
        return
    cam(c, push(t, 110.6, 118.7, 1.0, 0.75), 960, 540, t)
    bg(c, t)
    cx, cy = 960, 540
    for i in range(70):
        rnd = random.Random(i)
        ang = rnd.uniform(0, TAU)
        rr = 180 + ((t * 30 + rnd.uniform(0, 600)) % 640)
        glow(c, cx + math.cos(ang) * rr, cy + math.sin(ang) * rr * 0.9, rnd.uniform(30, 80), "#ff6a3a", 0.12)
    supergiant(c, cx, cy, 170, t)
    orbit(c, cx, cy, 560, 0.85, "#bfe0ff", 0.55, 3, prog=ease_out(at(t, 111.6, 1.4)))
    text(c, "PLUTO'S ORBIT", cx, cy - 500, 32, "#bfe0ff", "Bold", a=at(t, 112.0, 0.6), shadow=True)
    fact(c, t, 114.0, "≈ 400 × EARTH–SUN DISTANCE", 960, 1000, 42, "#ffd36b")
    guide(c, 220, 850, t, "float_wow", s=0.35, expr="wide", look=(1, -0.5))


# ======================================================================= 9. BLACK HOLES (118.7 - 138.7)
def s_bh(c, t):
    if t < 126.0:
        cam(c, push(t, 118.7, 126.0, 1.0, 1.1), 960, 540, t)
        bg(c, t)
        if t < 122.9:
            black_hole(c, 1200, 540, 150, t, disk=0.9)
            for i in range(6):
                y0 = 250 + i * 70
                prog = clamp((t - 119.2 - i * 0.25) / 1.6)
                pts = []
                x, y, vx, vy = 300.0, float(y0), 1.0, 0.0
                for _ in range(80):
                    dx, dy = 1200 - x, 540 - y
                    d = math.hypot(dx, dy)
                    if d < 150:
                        break
                    vx += dx / d ** 3 * 2600
                    vy += dy / d ** 3 * 2600
                    n = math.hypot(vx, vy)
                    vx, vy = vx / n, vy / n
                    x, y = x + vx * 16, y + vy * 16
                    pts.append((x, y))
                if len(pts) > 2:
                    light_ray(c, pts, prog=prog, w=3)
            guide(c, 230, 640, t, "float_point", s=0.7, look=(1, 0), expr="focus")
            doc_title(c, t, 119.0, "BLACK HOLES", "Not even light escapes", dur=3.6)
            return
        k = smooth(at(t, 123.2, 2.2))
        R = lerp(300, 8, k)
        star(c, 960, 540, R, "#ffd36b", t)
        for i in range(16):
            ang = i * TAU / 16
            arrow(c, 960 + math.cos(ang) * (R + 120), 540 + math.sin(ang) * (R + 120),
                  960 + math.cos(ang) * (R + 40), 540 + math.sin(ang) * (R + 40), "#ff8a3a", 6, a=0.7 * (1 - k * 0.5))
        if k > 0.9:
            black_hole(c, 960, 540, 50 * (k - 0.9) * 10, t, disk=0.6)
        return
    if t < 132.0:
        cam(c, push(t, 126.0, 132.0, 0.8, 1.6), 960, 540, t)
        bg(c, t)
        galaxy(c, 960, 540, 520, t, "spiral", tilt=0.6, rot=-15, spin=5)
        k = at(t, 128.0, 1.0)
        black_hole(c, 960, 540, 18 * k + 0.1, t, disk=k)
        fact(c, t, 126.6, "MILLIONS – BILLIONS OF SUNS", 960, 960, 42, "#ffd36b")
        return
    cam(c, push(t, 132.0, 138.7, 1.0, 1.08), 960, 500, t)
    bg(c, t)
    black_hole(c, 960, 470, 230, t, disk=1.0)
    doc_title(c, t, 132.2, "TON 618", "Heaviest black hole found", dur=6)
    n = count(t, 134.0, 2.4, 0, 66)
    fact(c, t, 133.8, f"{round(n)} BILLION SUNS", 960, 960, 54, "#ffd36b")
    guide(c, 1500, 800, t, "float_wow", s=0.4, expr="wide", face=-1, look=(-1, -0.5))


# ======================================================================= 10. FERMI BUBBLES (138.7 - 154.7)
def s_fermi(c, t):
    cam(c, push(t, 138.7, 154.7, 1.0, 1.1), 960, 540, t)
    bg(c, t)
    galaxy(c, 960, 540, 560, t, "milkyway", tilt=0.1, rot=0, spin=0)
    reveal = smooth(at(t, 143.2, 2.0))
    if t < 143.2:
        hubble(c, 1500, 220, 0.5, t, rot=-150)
        doc_title(c, t, 138.9, "FERMI TELESCOPE", "NASA, 2010", dur=4)
        guide(c, 1500, 760, t, "float_point", s=0.5, face=-1, look=(-1, -0.3))
        return
    # scanner lens reveals the bubbles
    sx = lerp(300, 1620, smooth(at(t, 143.2, 2.6)))
    nebula(c, 960, 540, 0.95, "fermi", t, a=reveal, breathe=0.01)
    if t < 146.2:
        c.drawRect(skia.Rect(sx - 4, 0, sx + 4, H), P("#e08aff", a=0.6))
        glow(c, sx, 540, 300, "#e08aff", 0.15)
    k = ease_out(at(t, 147.0, 1.2))
    dim_line(c, 1340, 290, 1340, 540, "#e08aff", prog=k)
    fact(c, t, 147.2, "25,000 LIGHT-YEARS", 1560, 430, 34, "#e08aff")
    if t > 150.0:
        doc_title(c, t, 150.0, "FERMI BUBBLES", "Blown out by our galaxy's black hole", dur=4.7)
        kb = at(t, 151.6, 0.5)
        black_hole(c, 960, 540, 16 * kb + 0.1, t, disk=kb)
        for side in (-1, 1):
            for i in range(4):
                u = (t * 0.6 + i / 4) % 1
                c.drawCircle(960, 540 + side * 260 * u, 8 * (1 - u), P("#f0b0ff", a=kb * (1 - u)))


# ======================================================================= 11. ERIDANUS SUPERVOID (154.7 - 170.5)
def s_void_eri(c, t):
    cam(c, push(t, 154.7, 170.5, 1.15, 1.0), 960, 540, t)
    screen_fill(c, ["#02030a", "#060816"])
    k = smooth(at(t, 158.5, 3.0))
    hk = 0.92 * k
    galaxy_field(c, t, (-60, -60, W + 60, H + 60), hole=(960, 540, 380, hk), drift=(-3, 0))
    if k > 0:
        c.drawCircle(960, 540, 380, P("#8ec8ff", 2, 0.35 * k))
    if t < 158.4:
        guide(c, 960, 560, t, keys(t, [(154.7, "float"), (156.4, "float_point")]), s=0.75, look=(0.5, 0))
    else:
        guide(c, 960, 560, t, keys(t, [(158.4, "float"), (163.0, "float_wow"), (166.0, "float")]), s=0.45,
              expr="wide" if t < 166 else "worried", look=(math.sin(t * 0.7), 0))
    doc_title(c, t, 158.6, "ERIDANUS SUPERVOID", "Found in 2004", dur=4.4)
    fact(c, t, 163.4, "1.8 BILLION LIGHT-YEARS ACROSS", 960, 1000, 42, "#8ec8ff")


# ======================================================================= 12. NEBULAE + TARANTULA (170.5 - 198.5)
def s_nebulae(c, t):
    if t < 179.4:
        cam(c, push(t, 170.5, 179.4, 1.0, 1.08), 960, 540, t)
        bg(c, t)
        if t < 177.0:
            nebula(c, 960, 540, 1.15, "ring" if t > 174.1 else "generic", t, a=at(t, 170.6, 0.8))
            if t > 174.1:
                k = (t - 174.1)
                star(c, 960, 540, 14, "#bfe8ff", t)
                for i in range(3):
                    u = ((k * 0.35 + i / 3) % 1)
                    c.drawCircle(960, 540, 60 + 340 * u, P("#ffb07a", 6, 0.5 * (1 - u)))
            guide(c, 260, 700, t, "float_point" if t > 171 else "float", s=0.55, look=(1, -0.3))
            return
        nebula(c, 960, 540, 1.15, "pillars", t)
        rnd = random.Random(5)
        for i in range(10):
            k = at(t, 177.2 + i * 0.18, 0.4)
            flash(c, 600 + rnd.uniform(0, 700), 300 + rnd.uniform(0, 500), k, "#fff2c0", 90)
        return
    cam(c, push(t, 179.4, 198.5, 1.0, 1.25), 960, 540, t)
    bg(c, t)
    nebula(c, 960, 540, 1.3, "tarantula", t, a=at(t, 179.5, 0.8))
    doc_title(c, t, 179.8, "TARANTULA NEBULA", "Also called 30 Doradus", dur=4.8)
    fact(c, t, 184.0, "1,800+ LIGHT-YEARS WIDE", 960, 140, 40, "#ff9ac8", dur=6.0)
    fact(c, t, 187.0, "170,000 LIGHT-YEARS AWAY", 960, 200, 34, "#ffffff", dur=3.2)
    if t > 190.0:
        guide(c, 300, 760, t, keys(t, [(190.0, "duck"), (192.0, "float_wow")]), s=0.5,
              expr="scared" if t < 191.9 else "happy", look=(1, -0.3))
        fact(c, t, 191.9, "STELLAR NURSERY", 960, 1000, 44, "#ffd36b")
        rnd = random.Random(9)
        for i in range(18):
            st = 193.2 + rnd.uniform(0, 5)
            k = at(t, st, 0.6)
            px, py = 960 + rnd.gauss(0, 240), 540 + rnd.gauss(0, 170)
            flash(c, px, py, k, "#fff2c0", 70)
            if k >= 1:
                c.drawCircle(px, py, 4, P("#ffffff"))


# ======================================================================= 13. COMET (198.5 - 227.1)
def s_comet(c, t):
    if t < 206.2:
        cam(c, push(t, 198.5, 206.2, 1.0, 1.06), 960, 540, t)
        bg(c, t, drift=(-20, 0))
        comet(c, lerp(1300, 900, (t - 198.5) / 7.7), lerp(420, 520, (t - 198.5) / 7.7), 0.9, t, ang=-15)
        doc_title(c, t, 198.8, "BERNARDINELLI–BERNSTEIN", "Comet C/2014 UN271 · largest comet found", dur=7)
        return
    if t < 215.2:
        cam(c, push(t, 206.2, 215.2, 1.0, 1.04), 960, 540, t)
        bg(c, t)
        glow(c, 1150, 520, 380, "#bfe8ff", 0.18)
        nucleus(c, 1150, 520, 230, t)
        nucleus(c, 520, 600, 22, t)
        text(c, "TYPICAL COMET", 520, 690, 28, "#9aa3b3", "Bold", a=at(t, 209.0, 0.5))
        fact(c, t, 206.4, "~85 MILES ACROSS", 1150, 880, 42, "#bfe8ff")
        fact(c, t, 209.2, "50 × BIGGER", 520, 470, 40, "#ffd36b", dur=2.8)
        fact(c, t, 212.1, "100,000 × THE MASS", 520, 470, 40, "#ffd36b")
        guide(c, 300, 820, t, keys(t, [(206.2, "point"), (209.2, "point"), (212.0, "wow")]), s=0.45,
              space=False, look=(1, -0.3), expr="wide" if t > 212 else "smile")
        return
    if t < 219.2:
        cam(c, push(t, 215.2, 219.2, 1.0, 1.06), 960, 540, t)
        bg(c, t)
        nucleus(c, 1200, 480, 150, t)
        text(c, "PLANET?", 1200, 260, 48, "#ffffff", "Bold", a=window(t, 215.4, 218.0, 0.3), shadow=True)
        guide(c, 540, 640, t, keys(t, [(215.2, "think"), (218.1, "idle")]), s=0.85, space=False,
              expr="focus" if t < 218 else "smile", look=(1, -0.3))
        return
    cam(c, push(t, 219.2, 227.1, 1.0, 0.9), 960, 540, t)
    bg(c, t)
    cx, cy = 760, 560
    sun(c, cx, cy, 30, t)
    for i, (R, kind, r) in enumerate(((70, "mercury", 5), (110, "earth", 7), (160, "mars", 6), (300, "jupiter", 16),
                                      (430, "saturn", 13))):
        orbit(c, cx, cy, R, 0.5, "#8ec8ff", 0.4, 2)
        ang = 2.0 + i * 1.3 + t * 0.25 / (R / 100)
        px, py = on_orbit(cx, cy, R, ang, 0.5)
        if kind == "saturn":
            rings(c, px, py, r, t, False)
        planet(c, px, py, r, kind, t, atm=False)
        if kind == "saturn":
            rings(c, px, py, r, t, True)
    text(c, "SATURN", cx + 430, cy - 240, 28, "#ffe6a8", "Bold", a=at(t, 222.6, 0.5), shadow=True)
    pth = skia.Path()
    pth.moveTo(1920, 0)
    pth.quadTo(cx + 760, cy - 60, 1920, 1080)
    c.drawPath(pth, skia.Paint(AntiAlias=True, Color=C("#bfe8ff", 0.5), Style=skia.Paint.kStroke_Style,
                               StrokeWidth=3, PathEffect=skia.DashPathEffect.Make([14, 12], 0)))
    u = clamp((t - 219.2) / 7.9)
    qx = (1 - u) ** 2 * 1920 + 2 * (1 - u) * u * (cx + 760) + u * u * 1920
    qy = (1 - u) ** 2 * 0 + 2 * (1 - u) * u * (cy - 60) + u * u * 1080
    comet(c, qx, qy, 0.25, t, ang=math.degrees(math.atan2(qy - cy, qx - cx)))
    fact(c, t, 219.8, "CLOSEST APPROACH: 2031", 960, 110, 42, "#bfe8ff")
    fact(c, t, 222.6, "1+ BILLION MILES AWAY", 960, 1000, 40, "#ffd36b")
    guide(c, 230, 850, t, "hips", s=0.4, space=False, expr="smile", look=(1, 0))


# ======================================================================= 14. NUCLEAR PASTA (227.1 - 246.0)
def s_pasta(c, t):
    if t < 235.6:
        cam(c, push(t, 227.1, 235.6, 1.0, 1.08), 960, 540, t)
        bg(c, t)
        if t < 232.9:
            neutron_star(c, 1150, 540, 60, t, beams=0.0)
            doc_title(c, t, 227.4, "NUCLEAR PASTA", "Inside neutron stars", dur=5)
            guide(c, 420, 640, t, keys(t, [(227.1, "float"), (229.8, "float_point")]), s=0.8, look=(1, 0))
            return
        k = at(t, 233.0, 1.6)
        if k < 0.5:
            star(c, 960, 540, 200 * (1 - k), "#ffb36b", t)
        flash(c, 960, 540, k, "#ffffff", 700)
        for i in range(30):
            ang = i * TAU / 30
            rr = 900 * ease_out(k)
            c.drawCircle(960 + math.cos(ang) * rr, 540 + math.sin(ang) * rr, 6, P("#ffb36b", a=1 - k))
        neutron_star(c, 960, 540, 30 * clamp(k * 2 - 0.5), t, beams=0)
        return
    if t < 242.6:
        cam(c, push(t, 235.6, 242.6, 1.0, 1.06), 960, 540, t)
        bg(c, t)
        cx, cy, R = 760, 560, 380
        c.drawCircle(cx, cy, R, P("#2a3a5a"))
        c.save()
        pth = skia.Path()
        pth.addCircle(cx, cy, R)
        c.clipPath(pth, skia.ClipOp.kIntersect, True)
        fill_shader(c, skia.Rect(cx - R, cy - R, cx + R, cy + R), radial(cx, cy, R, ["#ffe6c0", "#ff9a5a", "#7a3a8a"]))
        k = smooth(at(t, 236.0, 2.0))
        rnd = random.Random(4)
        for i in range(16):
            y = cy - R + i * 48
            wob = 6 * math.sin(t * 2 + i)
            line(c, cx - R, y + wob, cx - R + 2 * R * k, y - wob, "#ffd27a", 14)
        for i in range(5):
            rrect(c, cx - R * 0.6, cy - R * 0.7 + i * 110, 2 * R * 0.6 * k, 40, 10, "#ff7a4a", 0.85)
        c.restore()
        c.drawCircle(cx, cy, R, P("#bfe4ff", 6, 0.8))
        text(c, "SPAGHETTI", 1450, 400, 40, "#ffd27a", "Bold", a=at(t, 237.0, 0.5), shadow=True)
        text(c, "LASAGNA", 1450, 480, 40, "#ff7a4a", "Bold", a=at(t, 237.8, 0.5), shadow=True)
        guide(c, 1450, 780, t, "point", s=0.5, space=False, face=-1, look=(-1, 0))
        fork(c, 1300, 640, 0.6, -30)
        fact(c, t, 239.2, "STRONGEST MATERIAL IN THE UNIVERSE?", 960, 1020, 40, "#ffffff")
        return
    cam(c, push(t, 242.6, 246.0, 1.0, 1.04), 960, 540, t)
    bg(c, t)
    rrect(c, 300, 480, 500, 60, 6, "#8a94a8")
    text(c, "STEEL", 550, 600, 34, "#9aa3b3", "Bold")
    for i in range(6):
        line(c, 1150, 470 + i * 14, 1650, 470 + i * 14, "#ffd27a", 10)
    fact(c, t, 243.0, "10 BILLION × STRONGER", 1400, 640, 40, "#ffd36b")
    guide(c, 960, 690, t, "wow", s=0.6, space=False, expr="wide", look=(0, -0.3))


# ======================================================================= 15. PULSARS (246.0 - 262.0)
def s_pulsar(c, t):
    if t < 250.8:
        cam(c, push(t, 246.0, 250.8, 1.0, 1.05), 960, 540, t)
        bg(c, t)
        neutron_star(c, 960, 420, 40, t, beams=0.0)
        c.save()
        c.translate(960, 420)
        c.rotate(t * 200)
        line(c, 0, -60, 0, -80, "#bfe4ff", 3, 0.6)
        c.restore()
        k = at(t, 247.7, 0.6)
        city(c, 560, 900, 800, 1.0)
        dim_line(c, 920, 500, 1000, 500, "#8ec8ff", a=k) if False else None
        fact(c, t, 247.7, "SIZE OF A CITY", 960, 1000, 40, "#8ec8ff", dur=1.6)
        fact(c, t, 249.1, "MORE MASS THAN THE SUN", 960, 1000, 40, "#ffd36b")
        doc_title(c, t, 246.2, "PULSARS", "Spinning neutron stars", dur=3)
        return
    if t < 254.2:
        for side in (0, 1):
            c.save()
            clip_half(c, side, seed=7)
            if side == 0:
                bg(c, t)
                neutron_star(c, 480, 540, 24, t, beams=1.0, spin=1.4, beam_len=800)
            else:
                fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#0a1028", "#1a2a48"]))
                c.drawRect(skia.Rect(960, 900, W, H), P("#0d1a2a"))
                lighthouse(c, 1440, 900, 1.0, t)
            c.restore()
        jagged_split(c, seed=7)
        return
    cam(c, push(t, 254.2, 262.0, 1.0, 1.08), 960, 540, t)
    bg(c, t)
    k = smooth(at(t, 258.4, 3.0))
    star(c, 1350, 540, lerp(110, 70, k), "#ff9a5a", t)
    for i in range(30):
        u = ((t * 0.4 + i / 30) % 1)
        c.drawCircle(1350 + 120 + 500 * u, 540 + 80 * math.sin(i * 2.1) * u, 6 * (1 - u),
                     P("#ffb07a", a=k * (1 - u)))
    neutron_star(c, 560, 540, 26, t, beams=1.0, spin=0.8, beam_len=900)
    glow(c, 1350, 540, 260, "#bfe8ff", 0.2 * k * (0.5 + 0.5 * math.sin(t * 4)))
    doc_title(c, t, 254.4, "BLACK WIDOW PULSAR", "Destroying its partner star", dur=6)


# ======================================================================= 16. HAUMEA (262.0 - 285.3)
def haumea(c, x, y, s, t, spin=1.0, ring=True, moons=True):
    sq = 0.55 + 0.45 * abs(math.cos(t * spin))
    if ring:
        c.drawOval(skia.Rect(x - 260 * s, y - 60 * s, x + 260 * s, y + 60 * s), P("#c8d4e8", 6 * s, 0.6))
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.drawOval(skia.Rect(-170 * sq - 20, -90, 170 * sq + 20, 90), P("#d8dde6"))
    fill_shader(c, skia.Rect(-200, -100, 200, 100),
                radial(-60, -40, 260, [("#000000", 0), ("#000000", 0.05), ("#000000", 0.6)], [0, 0.4, 1])) if False else None
    c.drawOval(skia.Rect(-170 * sq - 20, -90, 170 * sq + 20, 90), skia.Paint(
        AntiAlias=True, Shader=radial(-60, -40, 260, [("#000000", 0), ("#000000", 0.05), ("#000000", 0.65)], [0, 0.4, 1])))
    c.drawOval(skia.Rect(-60 * sq, -30, 20 * sq, 10), P("#a4475a", a=0.5))
    c.restore()
    if ring:
        c.save()
        c.clipRect(skia.Rect(x - 400 * s, y, x + 400 * s, y + 200 * s))
        c.drawOval(skia.Rect(x - 260 * s, y - 60 * s, x + 260 * s, y + 60 * s), P("#c8d4e8", 6 * s, 0.85))
        c.restore()
    if moons:
        for i, (R, sp, r) in enumerate(((380, 0.5, 18), (520, 0.3, 11))):
            ang = t * sp + i * 2
            planet(c, x + math.cos(ang) * R * s, y + math.sin(ang) * R * s * 0.3, r * s, "mercury", t, atm=False)


def s_haumea(c, t):
    if t < 267.7:
        cam(c, push(t, 262.0, 267.7, 1.0, 1.05), 960, 540, t)
        bg(c, t)
        cx, cy = 760, 560
        sun(c, cx, cy, 18, t)
        orbit(c, cx, cy, 620, 0.42, "#6a8aff", 0.5, 2)
        planet(c, *on_orbit(cx, cy, 620, 1.2 + t * 0.03, 0.42), 16, "neptune", t)
        rnd = random.Random(6)
        for i in range(260):
            ang = rnd.uniform(0, TAU) + t * 0.01
            rr = rnd.uniform(760, 1000)
            px, py = on_orbit(cx, cy, rr, ang, 0.42)
            c.drawCircle(px, py, rnd.uniform(1.5, 3.5), P("#b8c8e8", a=0.6))
        ang = 0.3 + t * 0.02
        hx, hy = on_orbit(cx, cy, 880, ang, 0.42)
        you_are_here(c, hx, hy, t, "HAUMEA", "#ffd36b", a=at(t, 262.4, 0.5))
        fact(c, t, 264.0, "KUIPER BELT · BEYOND NEPTUNE", 960, 110, 40, "#8ec8ff")
        return
    if t < 277.5:
        cam(c, push(t, 267.7, 277.5, 1.0, 1.06), 960, 540, t)
        bg(c, t)
        spin_rate = 1.0 if t < 270.7 else 3.2
        haumea(c, 1000, 520, 1.25, t, spin_rate, ring=False, moons=True)
        doc_title(c, t, 268.0, "HAUMEA", "Egg-shaped dwarf planet · 2 moons", dur=3)
        if t > 270.7:
            clock(c, 1620, 300, 0.85, (t - 270.7) / 1.2, "#ffd36b")
            fact(c, t, 270.9, "1 DAY = 4 HOURS", 1620, 500, 38, "#ffd36b")
            guide(c, 300, 760, t, "float_wow", s=0.5, expr="wide", look=(1, -0.3))
        else:
            guide(c, 300, 760, t, "float_point", s=0.5, look=(1, -0.3))
        return
    cam(c, push(t, 277.5, 285.3, 1.0, 1.08), 960, 540, t)
    bg(c, t)
    if t < 280.7:
        haumea(c, 960, 540, 1.3, t, 1.0, ring=True, moons=False)
        fact(c, t, 277.8, "THIN RING · ~40 MILES WIDE", 960, 1000, 40, "#c8d4e8")
        return
    k = smooth(at(t, 281.0, 1.4))
    planet(c, lerp(300, 880, k), 540, 110, "mercury", t, atm=False)
    planet(c, lerp(1620, 1040, k), 540, 90, "ganymede", t, atm=False)
    flash(c, 960, 540, at(t, 282.3, 1.0), "#fff2c0", 500)
    if t > 282.4:
        for i in range(40):
            ang = i * TAU / 40
            rr = 700 * ease_out(at(t, 282.4, 2.5))
            c.drawCircle(960 + math.cos(ang) * rr, 540 + math.sin(ang) * rr * 0.4, 5, P("#c8d4e8", a=0.8))
    guide(c, 220, 880, t, "shrug", s=0.38, space=True, expr="focus", look=(1, -0.3))
    fact(c, t, 283.2, "AN ANCIENT COLLISION?", 960, 140, 42, "#ffffff")


# ======================================================================= 17. THE SUN (285.3 - 300.9)
def s_sun(c, t):
    if t < 291.8:
        cam(c, push(t, 285.3, 291.8, 1.0, 1.05), 960, 540, t)
        bg(c, t)
        k = ease_out(at(t, 287.0, 1.6))
        sun(c, 700, 540, 300, t)
        rnd = random.Random(1)
        xx = 1260
        for i, (kind, r) in enumerate((("jupiter", 34), ("saturn", 28), ("neptune", 14), ("neptune", 14),
                                       ("earth", 6), ("earth", 6), ("mars", 4), ("mercury", 3))):
            planet(c, xx + r, 540 + 30 * math.sin(i), r, kind, t, atm=False)
            xx += 2 * r + 12
        fact(c, t, 287.0, "99.8% OF ALL THE MASS", 700, 960, 46, "#ffd36b")
        fact(c, t, 289.0, "THE REST", 1440, 680, 32, "#9aa3b3")
        doc_title(c, t, 285.5, "THE SUN", "Our home star", dur=3)
        return
    if t < 296.5:
        cam(c, push(t, 291.8, 296.5, 1.0, 1.04), 960, 540, t)
        bg(c, t)
        sun(c, 960, 1720, 1300, t)
        k = ease_out(at(t, 292.2, 1.8))
        n = int(109 * k)
        for i in range(n):
            earth_icon(c, 960 - 109 * 8.2 + i * 16.4 + 8, 330, 7.5)
        fact(c, t, 292.4, "109 EARTHS WIDE", 960, 250, 44, "#ffffff")
        fact(c, t, 294.3, "1,000,000+ EARTHS FIT INSIDE", 960, 140, 40, "#ffd36b")
        return
    cam(c, push(t, 296.5, 300.9, 1.0, 0.9), 960, 540, t)
    bg(c, t)
    supergiant(c, 1320, 540, 520, t)
    sun(c, 360, 540, 16, t)
    text(c, "OUR SUN", 360, 610, 30, "#ffd36b", "Bold", shadow=True)
    fact(c, t, 297.0, "JUST AN AVERAGE STAR", 360, 460, 36, "#ffffff")
    guide(c, 360, 900, t, "shrug", s=0.36, space=True, expr="smile", look=(1, -0.3))


# ======================================================================= 18. OLYMPUS MONS (300.9 - 321.0)
def mars_sky(c, t):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#3a1a1a", "#b8704a", "#d8955a"], [0, 0.6, 1]))
    sun(c, 1600, 180, 34, t)


def s_olympus(c, t):
    if t < 305.6:
        cam(c, push(t, 300.9, 305.6, 1.0, 1.05), 960, 540, t)
        bg(c, t)
        planet(c, 960, 560, 360, "mars", t, spin=0.05)
        ang = 1.2 + t * 0.05
        glow(c, 860, 470, 70, "#ffd9b0", 0.5 * at(t, 301.6, 0.5))
        you_are_here(c, 860, 470, t, "", "#ffd36b", a=at(t, 301.6, 0.5))
        doc_title(c, t, 301.2, "OLYMPUS MONS", "Tallest volcano in the solar system", dur=4.2)
        return
    if t < 317.4:
        cam(c, push(t, 305.6, 317.4, 1.0, 1.03), 960, 540, t)
        mars_sky(c, t)
        k = ease_out(at(t, 305.8, 2.0))
        pth = skia.Path()
        pth.moveTo(-50, 980)
        pth.cubicTo(500, 980 - 50 * k, 650, 980 - 520 * k, 900, 980 - 560 * k)
        pth.lineTo(1100, 980 - 560 * k)
        pth.cubicTo(1350, 980 - 520 * k, 1450, 980 - 50 * k, 1970, 980)
        pth.lineTo(1970, H)
        pth.lineTo(-50, H)
        pth.close()
        c.drawPath(pth, P("#8a3a22"))
        c.drawPath(pth, P("#d8804a", 4, 0.6))
        # Everest
        ke = ease_out(at(t, 308.6, 1.0))
        c.drawPath(poly([(1500, 980), (1600, 980 - 190 * ke), (1700, 980)]), P("#5a6478"))
        c.drawPath(poly([(1572, 980 - 140 * ke), (1600, 980 - 190 * ke), (1628, 980 - 140 * ke)]), P("#ffffff"))
        text(c, "EVEREST", 1600, 1040, 28, "#ffffff", "Bold", a=ke, shadow=True)
        c.drawRect(skia.Rect(0, 980, W, H), P("#5a2414"))
        dim_line(c, 1180, 980, 1180, 420, "#ffffff", prog=ease_out(at(t, 306.0, 1.0)))
        fact(c, t, 306.0, "~16 MILES HIGH", 1340, 560, 40, "#ffffff", dur=5.2)
        fact(c, t, 308.8, "≈ 3 × EVEREST", 1340, 620, 34, "#ffd36b", dur=2.5)
        kw = ease_out(at(t, 311.6, 1.2))
        dim_line(c, 100, 1010, 1820, 1010, "#ffd36b", prog=kw)
        fact(c, t, 312.0, "~370 MILES ACROSS · ABOUT THE SIZE OF ARIZONA", 960, 1060, 32, "#ffd36b")
        return
    # gentle slope walk
    cam(c, push(t, 317.4, 321.0, 1.0, 1.0), 960, 540, t)
    mars_sky(c, t)
    scroll = (t - 317.4) * 160
    surface(c, 860, "#9a4a2a", "#5a2414", t, rocks=True, seed=4, scroll=scroll,
            hills=[(80, 640, "#7a3a22", 0.3), (50, 760, "#8a4026", 0.6)])
    ph = scroll / (STRIDE * 0.9) * TAU
    guide(c, 900, hip_on(860, 0.9), t, s=0.9, walk=ph, expr="smile", look=(1, 0), rot=-2)
    fact(c, t, 318.0, "YOU WOULDN'T EVEN NOTICE THE CLIMB", 960, 140, 40, "#ffffff")


# ======================================================================= 19. VALLES MARINERIS (321.0 - 343.4)
def s_valles(c, t):
    if t < 331.7:
        cam(c, push(t, 321.0, 331.7, 1.0, 1.06), 960, 540, t)
        bg(c, t)
        planet(c, 760, 560, 380, "mars", t, spin=0.0)
        k = ease_out(at(t, 322.6, 2.0))
        pth = skia.Path()
        pth.moveTo(480, 560)
        pth.cubicTo(560, 600, 700, 560, 480 + 520 * k, 600 - 40 * k)
        c.drawPath(pth, P("#e09a6a", 30, 0.5))
        c.drawPath(pth, P("#5a1a0e", 20))
        c.drawPath(pth, P("#2a0a06", 8))
        doc_title(c, t, 322.6, "VALLES MARINERIS", "Largest canyon system known", dur=3.6)
        kb = ease_out(at(t, 326.4, 1.6))
        bar(c, 1250, 420, 560, 30, "#ff8a5a", kb)
        fact(c, t, 326.5, "~2,500 MILES LONG", 1530, 390, 38, "#ff8a5a")
        fact(c, t, 328.3, "≈ ACROSS THE UNITED STATES", 1530, 520, 32, "#ffffff")
        return
    if t < 335.5:
        cam(c, push(t, 331.7, 335.5, 1.0, 1.08), 960, 600, t)
        mars_sky(c, t)
        c.drawPath(poly([(-20, 520), (600, 520), (760, 1000), (1160, 1000), (1320, 520), (1940, 520), (1940, H),
                         (-20, H)]), P("#8a3a22"))
        c.drawPath(poly([(600, 520), (760, 1000), (1160, 1000), (1320, 520)]), P("#3a140a"))
        for i in range(5):
            line(c, 600 + i * 30, 520 + i * 96, 1320 - i * 30, 520 + i * 96, "#5a2414", 3, 0.6)
        guide(c, 520, hip_on(520, 0.35), t, "point_down", s=0.35, expr="wide", look=(1, 1))
        dim_line(c, 1380, 520, 1380, 1000, "#ffffff", prog=ease_out(at(t, 333.9, 0.8)))
        fact(c, t, 331.9, "120 MILES WIDE", 960, 470, 40, "#ffffff")
        fact(c, t, 334.0, "4+ MILES DEEP", 1600, 780, 36, "#ffd36b")
        return
    cam(c, push(t, 335.5, 343.4, 1.0, 1.04), 960, 540, t)
    info_board(c, t)
    k1 = ease_out(at(t, 335.7, 1.6))
    bar(c, 200, 360, 1500, 60, "#ff8a5a", 1.0)
    text(c, "VALLES MARINERIS · 2,500 MI", 200, 330, 34, "#ff8a5a", "Bold", align="left")
    bar(c, 200, 620, 1500 * 277 / 2500, 60, "#5bd6ff", k1)
    text(c, "GRAND CANYON · 277 MI", 200, 590, 34, "#5bd6ff", "Bold", align="left", a=k1)
    guide(c, 1400, 730, t, keys(t, [(335.5, "point"), (340.9, "shrug")]), s=0.6, space=False, face=-1,
          look=(-1, 0), expr="smile" if t < 340.9 else "deadpan")


# ======================================================================= 20. GANYMEDE (343.4 - 362.0)
def s_ganymede(c, t):
    if t < 349.5:
        cam(c, push(t, 343.4, 349.5, 1.0, 1.08), 1000, 540, t)
        bg(c, t)
        planet(c, 500, 540, 300, "jupiter", t, grs=True)
        for i, (R, sp, r, kind) in enumerate(((440, 0.6, 12, "mercury"), (560, 0.45, 14, "ganymede"),
                                              (760, 0.3, 26, "ganymede"), (900, 0.2, 20, "mercury"))):
            orbit(c, 500, 540, R, 0.3, "#8ec8ff", 0.25, 2)
            ang = 0.4 + i + t * sp * 0.2
            px, py = on_orbit(500, 540, R, ang, 0.3)
            planet(c, px, py, r, kind, t, atm=False)
            if i == 2:
                you_are_here(c, px, py, t, "GANYMEDE", "#ffd36b", a=at(t, 346.0, 0.5))
        doc_title(c, t, 346.2, "GANYMEDE", "Largest moon in the solar system", dur=3.2)
        return
    if t < 357.4:
        cam(c, push(t, 349.5, 357.4, 1.0, 1.04), 960, 540, t)
        bg(c, t)
        fld = at(t, 354.2, 1.0)
        if fld:
            c.save()
            c.translate(1200, 520)
            for k in range(1, 5):
                rr = 260 + k * 60
                for side in (-1, 1):
                    c.drawOval(skia.Rect(-rr if side < 0 else 0, -rr * 0.95, 0 if side < 0 else rr, rr * 0.95),
                               P("#8a7aff", 3, fld * (0.6 - k * 0.1)))
            c.restore()
        planet(c, 1200, 520, 260, "ganymede", t)
        planet(c, 480, 600, 190, "mercury", t, atm=False)
        text(c, "MERCURY", 480, 860, 34, "#9aa3b3", "Bold", shadow=True)
        fact(c, t, 349.8, "~3,270 MILES WIDE", 1200, 880, 40, "#ffffff")
        fact(c, t, 352.4, "BIGGER THAN MERCURY", 960, 120, 42, "#ffd36b", dur=1.8)
        fact(c, t, 354.3, "ITS OWN MAGNETIC FIELD", 960, 120, 42, "#8a7aff")
        return
    cam(c, push(t, 357.4, 362.0, 1.0, 1.1), 960, 540, t)
    bg(c, t)
    cx, cy, R = 960, 560, 380
    planet(c, cx, cy, R, "ganymede", t)
    k = ease_out(at(t, 357.8, 1.0))
    c.save()
    c.drawPath(poly([(cx, cy), (cx + R * 1.1, cy - R * 0.2), (cx + R * 1.1, cy + R * 1.1), (cx, cy + R * 1.1)]),
               P("#000000", a=0)) if False else None
    pth = skia.Path()
    pth.moveTo(cx, cy)
    pth.arcTo(skia.Rect(cx - R, cy - R, cx + R, cy + R), -20, 110 * k, False)
    pth.close()
    c.drawPath(pth, P("#d8dde6"))
    pth2 = skia.Path()
    pth2.moveTo(cx, cy)
    pth2.arcTo(skia.Rect(cx - R * 0.9, cy - R * 0.9, cx + R * 0.9, cy + R * 0.9), -20, 110 * k, False)
    pth2.close()
    c.drawPath(pth2, P("#1f62b5"))
    pth3 = skia.Path()
    pth3.moveTo(cx, cy)
    pth3.arcTo(skia.Rect(cx - R * 0.7, cy - R * 0.7, cx + R * 0.7, cy + R * 0.7), -20, 110 * k, False)
    pth3.close()
    c.drawPath(pth3, P("#6a5a4a"))
    c.drawCircle(cx, cy, R * 0.3, P("#a85a3a", a=k))
    c.restore()
    fact(c, t, 358.4, "HIDDEN SALTY OCEAN", 1600, 640, 40, "#5bd6ff")
    guide(c, 260, 700, t, "float_point", s=0.55, look=(1, 0))


# ======================================================================= 21. GREAT RED SPOT (362.0 - 380.3)
def jupiter_close(c, t, shrink=0.0):
    screen_fill(c, ["#d8b890", "#b8875a"])
    for i in range(-2, 15):
        y = i * 95 + 20 * math.sin(t * 0.3 + i)
        col = ["#e9d7b6", "#c99a6b", "#f1e3c6", "#b9784a"][i % 4]
        pth = skia.Path()
        pth.moveTo(-300, y)
        for x in range(-300, W + 380, 80):
            pth.lineTo(x, y + 18 * math.sin(x * 0.006 + t * 0.4 + i))
        pth.lineTo(W + 300, y + 95)
        pth.lineTo(-300, y + 95)
        pth.close()
        c.drawPath(pth, P(col, a=0.8))
    sx = 1 - 0.35 * shrink
    with xf(c, 960, 560, 1, sx=sx, sy=sx):
        for k, col in enumerate(("#a83a22", "#b5442a", "#c85a3a", "#d4683f", "#e07a4a", "#e89a6a")):
            rx, ry = 560 - k * 80, 300 - k * 44
            c.drawOval(skia.Rect(-rx, -ry, rx, ry), P(col))
        for i in range(40):
            rr = 0.2 + 0.8 * ((i * 37) % 40) / 40
            ph = i * 0.9 + t * (1.4 / (0.3 + rr))
            pth = skia.Path()
            pth.addArc(skia.Rect(-560 * rr, -300 * rr, 560 * rr, 300 * rr), math.degrees(ph) % 360, 50)
            c.drawPath(pth, P("#f6c8a0" if i % 2 else "#8a2a1a", 6, 0.45))
        c.drawOval(skia.Rect(-560, -300, 560, 300), P("#f3d6b0", 10, 0.5))


def s_grs(c, t):
    if t < 367.3:
        cam(c, push(t, 362.0, 367.3, 1.0, 1.06), 960, 560, t)
        jupiter_close(c, t)
        k = ease_out(at(t, 365.2, 0.8))
        if k:
            planet(c, 960, 560, 230 * k, "earth", t)
        doc_title(c, t, 362.3, "GREAT RED SPOT", "A storm on Jupiter", dur=3)
        fact(c, t, 365.4, "WIDER THAN EARTH", 960, 140, 44, "#ffffff")
        return
    if t < 373.8:
        cam(c, push(t, 367.3, 373.8, 1.0, 1.08), 960, 560, t)
        jupiter_close(c, t * (1 if t < 370.8 else 3))
        if t < 370.8:
            fact(c, t, 367.5, "WATCHED FOR 150+ YEARS", 960, 140, 44, "#ffffff")
        else:
            for i in range(8):
                ang = t * 3 + i * TAU / 8
                arrow(c, 960 + math.cos(ang) * 420, 560 + math.sin(ang) * 230,
                      960 + math.cos(ang + 0.35) * 420, 560 + math.sin(ang + 0.35) * 230, "#ffffff", 8, a=0.8)
            fact(c, t, 370.9, "WINDS: ~270 MPH", 960, 140, 44, "#ffd36b")
        return
    cam(c, push(t, 373.8, 380.3, 1.0, 0.95), 960, 560, t)
    jupiter_close(c, t, shrink=smooth(at(t, 374.0, 4.0)))
    guide(c, 260, 800, t, keys(t, [(373.8, "float"), (376.4, "shrug")]), s=0.5, expr="sad", look=(1, -0.2))
    fact(c, t, 374.0, "SLOWLY SHRINKING", 960, 140, 44, "#ffffff")


# ======================================================================= 22. SATURN'S RINGS (380.3 - 399.2)
def s_saturn(c, t):
    if t < 388.7:
        cam(c, push(t, 380.3, 388.7, 1.0, 1.06), 960, 540, t)
        bg(c, t)
        rings(c, 960, 520, 200, t, False, tilt=0.26, rot=-8)
        planet(c, 960, 520, 200, "saturn", t)
        rings(c, 960, 520, 200, t, True, tilt=0.26, rot=-8)
        doc_title(c, t, 380.5, "SATURN'S RINGS", None, dur=3)
        k = ease_out(at(t, 382.2, 1.4))
        dim_line(c, 960 - 450, 860, 960 + 450, 860, "#ffe6a8", prog=k)
        fact(c, t, 382.4, "~170,000 MILES", 960, 930, 40, "#ffe6a8")
        k2 = ease_out(at(t, 384.8, 1.4))
        earth_icon(c, 960 - 450, 990, 12)
        planet(c, 960 - 450 + 1200 * k2 * 0.75, 990, 5, "mercury", t, atm=False)
        line(c, 960 - 450, 990, 960 - 450 + 900 * k2, 990, "#8ec8ff", 2, 0.6)
        fact(c, t, 385.0, "≈ 3/4 OF THE WAY TO THE MOON", 1500, 1010, 30, "#8ec8ff")
        return
    if t < 393.8:
        k = smooth(at(t, 388.7, 2.0))
        cam(c, push(t, 388.7, 393.8, 1.0, 1.1), 960, 540, t)
        bg(c, t)
        tilt = lerp(0.26, 0.012, k)
        rings(c, 960, 540, 200, t, False, tilt=tilt, rot=0)
        planet(c, 960, 540, 200, "saturn", t)
        rings(c, 960, 540, 200, t, True, tilt=tilt, rot=0)
        if t > 390.3:
            fact(c, t, 390.4, "INCREDIBLY THIN", 960, 160, 44, "#ffffff")
            fact(c, t, 391.8, "OFTEN ONLY ~30 FEET THICK", 960, 940, 40, "#ffd36b")
        guide(c, 1650, 620, t, "float_wow" if t > 390.3 else "float", s=0.4, face=-1, look=(-1, 0),
              expr="wide" if t > 390.3 else "smile")
        return
    cam(c, push(t, 393.8, 399.2, 1.0, 1.06), 960, 540, t)
    bg(c, t, drift=(-30, 0))
    rnd = random.Random(12)
    for i in range(90):
        x = (rnd.uniform(0, W + 200) - (t - 393.8) * rnd.uniform(20, 60)) % (W + 200) - 100
        y = 540 + rnd.gauss(0, 200)
        ice_chunk(c, x, y, rnd.uniform(3, 18), t * 20 + i * 30)
    ice_chunk(c, 1320, 520, 160, t * 4)
    house(c, 1320, 780, 0.9)
    fact(c, t, 395.9, "FROM TINY GRAINS TO HOUSE-SIZED CHUNKS", 960, 140, 40, "#dfefff")
    guide(c, 520, 560, t, "float_point", s=0.6, look=(1, 0))


# ======================================================================= 23. PILLARS OF CREATION (399.2 - 413.9)
def s_pillars(c, t):
    cam(c, push(t, 399.2, 413.9, 1.0, 1.3), 960, 560, t)
    bg(c, t)
    nebula(c, 960, 560, 1.4, "pillars", t, a=at(t, 399.3, 1.0), breathe=0.0)
    doc_title(c, t, 399.4, "PILLARS OF CREATION", "Eagle Nebula", dur=4)
    fact(c, t, 403.5, "6,500 LIGHT-YEARS AWAY", 960, 140, 40, "#ffd9a8", dur=2.4)
    fact(c, t, 406.0, "SEVERAL LIGHT-YEARS TALL", 960, 140, 40, "#ffd9a8", dur=2.2)
    rnd = random.Random(14)
    for i in range(10):
        st = 408.2 + rnd.uniform(0, 2)
        k = at(t, st, 0.6)
        px, py = 960 + rnd.uniform(-500, 300), 560 + rnd.uniform(-100, 400)
        flash(c, px, py, k, "#fff2c0", 50)
        if k >= 1:
            c.drawCircle(px, py, 3, P("#ffffff"))
    if t > 410.4:
        k = at(t, 410.4, 0.6)
        for i in range(12):
            u = ((t * 0.4 + i / 12) % 1)
            arrow(c, 1800 - 600 * u, 100 + i * 40 + 300 * u, 1760 - 600 * u, 120 + i * 40 + 300 * u, "#fff2c0", 3,
                  a=k * (1 - u) * 0.6)


# ======================================================================= 24. LANIAKEA (413.9 - 428.1)
def s_laniakea(c, t):
    if t < 415.9:
        z = math.exp(lerp(math.log(1.0), math.log(0.12), smooth((t - 413.9) / 2.0)))
        bg(c, t)
        galaxy(c, 960, 540, 520 * z, t, "milkyway", tilt=0.6, rot=-10, spin=3)
        you_are_here(c, 960, 540, t, "", "#ffd36b") if z < 0.2 else None
        return
    cam(c, push(t, 415.9, 428.1, 1.0, 1.08), 960, 540, t)
    screen_fill(c, ["#02030a", "#070a1a"])
    galaxy_field(c, t, (-40, -40, W + 40, H + 40), n=1400, size=1.1)
    k = ease_out(at(t, 416.2, 1.2))
    rnd = random.Random(31)
    for i in range(46):
        x0, y0 = rnd.uniform(0, W), rnd.uniform(0, H)
        pts = [(x0, y0)]
        x, y = x0, y0
        for j in range(30):
            dx, dy = 1100 - x, 520 - y
            d = math.hypot(dx, dy) + 1
            x += dx / d * 18 + math.sin(y * 0.01) * 6
            y += dy / d * 18 + math.cos(x * 0.01) * 6
            pts.append((x, y))
            if d < 60:
                break
        light_ray(c, pts, "#8ec8ff", 2, 0.35 * k, prog=k)
    glow(c, 1100, 520, 160, "#8ec8ff", 0.3 * k)
    you_are_here(c, 760, 640, t, "MILKY WAY", "#ffd36b", a=k)
    doc_title(c, t, 417.0, "LANIAKEA SUPERCLUSTER", None, dur=11)
    fact(c, t, 420.0, "~520 MILLION LIGHT-YEARS ACROSS", 960, 110, 40, "#ffffff", dur=3.4)
    fact(c, t, 422.8, "~100,000 GALAXIES", 960, 110, 40, "#ffffff", dur=1.9)
    fact(c, t, 424.7, "\"IMMENSE HEAVEN\"", 960, 110, 46, "#ffd36b")
    if t > 424.6:
        guide(c, 1650, 820, t, "float_wow", s=0.45, face=-1, expr="happy", look=(-1, -0.5))


# ======================================================================= 25. HERCULES–CORONA BOREALIS (428.1 - 448.9)
_GRB = [(random.Random(i).gauss(960, 360), random.Random(i + 50).gauss(520, 160), random.Random(i + 90).uniform(0, 6))
        for i in range(26)]


def s_wall(c, t):
    cam(c, push(t, 428.1, 448.9, 1.0, 1.1), 960, 540, t)
    screen_fill(c, ["#02030a", "#070a1a"])
    galaxy_field(c, t, (-40, -40, W + 40, H + 40), n=1100, a=0.8)
    if t < 430.0:
        guide(c, 960, 560, t, "float", s=0.7, expr="neutral", look=(0, -0.3))
        return
    for (x, y, off) in _GRB:
        st = 430.3 + off
        k = at(t, st, 0.9)
        if 0 < k < 1:
            glow(c, x, y, 140 * (1 - k) + 20, "#d8a0ff", 0.9 * (1 - k))
            line(c, x - 60 * (1 - k), y, x + 60 * (1 - k), y, "#ffffff", 3, 1 - k)
        if k >= 1:
            c.drawCircle(x, y, 4, P("#d8a0ff", a=0.8))
    if t > 435.0:
        k = ease_out(at(t, 435.2, 2.0))
        pth = skia.Path()
        pth.addOval(skia.Rect(960 - 700 * k, 520 - 300 * k, 960 + 700 * k, 520 + 300 * k))
        dash = skia.DashPathEffect.Make([22, 14], t * 20) if t > 445.5 else None
        p = skia.Paint(AntiAlias=True, Color=C("#d8a0ff", 0.6 * (0.6 + 0.4 * math.sin(t * 5) if t > 445.5 else 1)),
                       Style=skia.Paint.kStroke_Style, StrokeWidth=4)
        if dash:
            p.setPathEffect(dash)
        c.drawPath(pth, p)
        doc_title(c, t, 435.4, "HERCULES–CORONA BOREALIS", "Great Wall", dur=4)
        fact(c, t, 439.4, "~10 BILLION LIGHT-YEARS ACROSS", 960, 110, 40, "#ffffff", dur=2.4)
        fact(c, t, 442.0, "LARGEST KNOWN STRUCTURE", 960, 110, 44, "#d8a0ff", dur=3.4)
        if t > 445.5:
            guide(c, 260, 820, t, keys(t, [(445.5, "think"), (447.0, "shrug")]), s=0.45, space=True,
                  expr="focus", look=(1, -0.4))
            fact(c, t, 445.7, "ONE STRUCTURE?", 960, 110, 44, "#ffffff")


# ======================================================================= 26. IC 1101 (448.9 - 466.7)
def s_ic1101(c, t):
    cam(c, push(t, 448.9, 466.7, 1.0, 1.06), 960, 540, t)
    bg(c, t)
    k = ease_out(at(t, 449.2, 1.4))
    galaxy(c, 1120, 540, 760 * k + 1, t, "elliptical", tilt=0.7, rot=-15, spin=0, blur=2)
    km = ease_out(at(t, 458.3, 1.0))
    if km:
        galaxy(c, 330, 760, 60 * km + 1, t, "milkyway", tilt=0.7, rot=-10, spin=4)
        text(c, "MILKY WAY", 330, 870, 28, "#8ec8ff", "Bold", a=km, shadow=True)
    doc_title(c, t, 450.7, "IC 1101", "One of the largest galaxies known", dur=4)
    fact(c, t, 453.3, "~4 MILLION LIGHT-YEARS ACROSS", 1120, 110, 40, "#ffe6c0", dur=2.4)
    fact(c, t, 455.9, "~100 TRILLION STARS", 1120, 110, 44, "#ffe6c0", dur=2.4)
    fact(c, t, 458.4, "MILKY WAY: ~100,000 LIGHT-YEARS", 1120, 110, 40, "#8ec8ff", dur=5.0)
    fact(c, t, 463.7, "~1 BILLION LIGHT-YEARS AWAY", 1120, 110, 40, "#ffffff")
    guide(c, 330, 380, t, keys(t, [(448.9, "float"), (452.0, "float_point"), (461.4, "float_wow")]), s=0.45,
          look=(1, 0), expr="wide" if t > 461.4 else "smile")


# ======================================================================= 27. BOÖTES VOID (466.7 - 478.3)
def s_bootes(c, t):
    cam(c, push(t, 466.7, 478.3, 1.0, 1.12), 960, 540, t)
    screen_fill(c, ["#02030a", "#060816"])
    expect = window(t, 473.0, 476.2, 0.4)
    k = smooth(at(t, 467.0, 2.0))
    galaxy_field(c, t, (-40, -40, W + 40, H + 40), hole=(960, 540, 420, 0.98 * k * (1 - expect)))
    if k:
        c.drawCircle(960, 540, 420, P("#8ec8ff", 2, 0.35 * k))
    doc_title(c, t, 466.9, "BOÖTES VOID", "One of the biggest empty spaces", dur=4)
    fact(c, t, 470.3, "~330 MILLION LIGHT-YEARS ACROSS", 960, 1010, 40, "#8ec8ff", dur=2.6)
    fact(c, t, 473.1, "EXPECTED: THOUSANDS OF GALAXIES", 960, 1010, 40, "#ffffff", dur=3.1)
    fact(c, t, 476.3, "FOUND: ~60", 960, 1010, 46, "#ffd36b")
    guide(c, 960, 560, t, keys(t, [(466.7, "float"), (473.0, "float_point"), (476.3, "float_wow")]), s=0.4,
          expr="wide" if t > 476.3 else "focus", look=(math.sin(t), 0))


# ======================================================================= 28. MAGNETAR (478.3 - 493.9)
def s_magnetar(c, t):
    cam(c, push(t, 478.3, 493.9, 1.0, 1.08), 960, 540, t)
    bg(c, t, tint_col="#3a2a6a")
    quake = at(t, 489.8, 0.6)
    shake = 8 * window(t, 489.8, 492.0, 0.2) * math.sin(t * 50)
    neutron_star(c, 1100 + shake, 520, 90, t, beams=0.0, field=at(t, 481.2, 1.0), col="#c8b8ff", tilt=10)
    if t > 487.5:
        kc = ease_out(at(t, 487.5, 1.2))
        rnd = random.Random(3)
        for i in range(6):
            ang = rnd.uniform(0, TAU)
            x1, y1 = 1100 + math.cos(ang) * 20, 520 + math.sin(ang) * 20
            x2, y2 = 1100 + math.cos(ang + 0.3) * 85 * kc, 520 + math.sin(ang + 0.3) * 85 * kc
            line(c, x1, y1, x2, y2, "#ffffff", 3, kc)
    if quake:
        for i in range(3):
            u = ((t - 489.8) * 0.6 + i / 3) % 1
            c.drawCircle(1100, 520, 100 + 900 * u, P("#e0d0ff", 8 * (1 - u), 0.7 * (1 - u)))
    doc_title(c, t, 478.6, "MAGNETAR", "Strongest magnetic field known", dur=5.8)
    if 484.9 < t < 487.6:
        guide(c, 360, 640, t, "hold_up", s=0.6, expr="wide", space=True, look=(1, -0.5))
        magnet(c, 360, 380, 0.7)
        fact(c, t, 485.0, "TRILLIONS × A FRIDGE MAGNET", 1100, 940, 40, "#ffd36b", dur=2.6)
    else:
        guide(c, 360, 640, t, keys(t, [(478.3, "float"), (480.0, "float_point"), (489.8, "duck")]), s=0.6,
              expr="scared" if t > 489.8 else "focus", look=(1, 0))
    fact(c, t, 490.0, "STARQUAKES", 1100, 940, 46, "#e0d0ff")


# ======================================================================= 29. SAGITTARIUS A* (493.9 - 515.7)
def s_sgr(c, t):
    if t < 501.0:
        z = math.exp(lerp(0, math.log(3.2), smooth((t - 493.9) / 4.0)))
        cam(c, z, 960, 540, t, drift=0.4)
        bg(c, t)
        galaxy(c, 960, 540, 520, t, "milkyway", tilt=0.6, rot=-10, spin=3)
        k = at(t, 496.0, 1.0)
        black_hole(c, 960, 540, 14 * k + 0.1, t, disk=k)
        c.resetMatrix()
        doc_title(c, t, 496.2, "SAGITTARIUS A*", "Our galaxy's central black hole", dur=4.4)
        fact(c, t, 498.9, "~4 MILLION × THE SUN'S MASS", 960, 1010, 40, "#ffd36b")
        return
    if t < 504.9:
        cam(c, push(t, 501.0, 504.9, 1.0, 1.05), 960, 540, t)
        bg(c, t)
        galaxy(c, 960, 540, 480, t, "milkyway", tilt=1.0, rot=0, spin=2)
        black_hole(c, 960, 540, 10, t, disk=0.7)
        ex, ey = 960 + 300 * math.cos(2.4), 540 + 300 * math.sin(2.4)
        you_are_here(c, ex, ey, t, "EARTH", "#8ec8ff")
        k = ease_out(at(t, 501.6, 1.2))
        line(c, ex, ey, lerp(ex, 960, k), lerp(ey, 540, k), "#ffd36b", 3, 0.8)
        fact(c, t, 501.6, "~27,000 LIGHT-YEARS", 960, 1010, 42, "#ffd36b")
        return
    if t < 510.0:
        cam(c, push(t, 504.9, 510.0, 1.0, 1.06), 960, 540, t)
        bg(c, t)
        planet(c, 960, 1500, 700, "earth", t, spin=0.04)
        for i, x in enumerate((420, 700, 1220, 1500)):
            dish(c, x, 860 - 40 * math.sin((x - 960) / 700 * 1.4) * 0 - abs(x - 960) * 0.12, 0.8, -40 + i * 10)
        k = ease_out(at(t, 506.2, 1.0))
        rrect(c, 760, 170, 400, 400, 16, "#0a0a10", a=k)
        if k:
            glow(c, 960, 370, 160, "#ff8a2a", 0.6 * k)
            c.drawCircle(960, 370, 95, P("#ff9a3a", 46, 0.8 * k))
            c.drawCircle(960, 370, 95, P("#ffd27a", 14, 0.6 * k))
            c.drawCircle(960, 370, 60, P("#0a0a10", a=k))
        rrect(c, 760, 170, 400, 400, 16, "#e3e7ee", a=k, stroke=8)
        fact(c, t, 506.3, "FIRST IMAGE · 2022", 960, 640, 38, "#ffffff")
        fact(c, t, 508.3, "EVENT HORIZON TELESCOPE", 960, 690, 30, "#8ec8ff")
        return
    cam(c, push(t, 510.0, 515.7, 1.0, 0.95), 960, 540, t)
    bg(c, t)
    if t < 512.6:
        black_hole(c, 1300, 540, 260, t)
        black_hole(c, 420, 540, 12, t, disk=0.8)
        text(c, "TON 618", 1300, 960, 36, "#ffd36b", "Bold", shadow=True)
        text(c, "SGR A*", 420, 640, 30, "#8ec8ff", "Bold", shadow=True)
        return
    galaxy(c, 960, 540, 520, t, "milkyway", tilt=0.6, rot=-10, spin=14)
    black_hole(c, 960, 540, 14, t, disk=0.8)
    guide(c, 260, 820, t, "float_wow", s=0.45, expr="happy", look=(1, -0.4))


# ======================================================================= 30. OBSERVABLE UNIVERSE (515.7 - 528.0)
def s_universe(c, t):
    z = 1.0 if t < 525.5 else lerp(1.0, 0.35, smooth((t - 525.5) / 2.5))
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#010208", "#04050e"]))
    c.save()
    c.translate(960, 540)
    c.scale(z, z)
    c.translate(-960, -540)
    R = 470
    glow(c, 960, 540, R * 1.25, "#ff9a5a", 0.25)
    c.drawCircle(960, 540, R, P("#05060f"))
    c.save()
    pth = skia.Path()
    pth.addCircle(960, 540, R)
    c.clipPath(pth, skia.ClipOp.kIntersect, True)
    cosmic_web(c, t * 0.2, zoom=0.55, a=0.9)
    c.restore()
    c.drawCircle(960, 540, R, P("#ff9a5a", 6, 0.6))
    you_are_here(c, 960, 540, t, "US", "#ffd36b")
    dim_line(c, 960 - R, 540 + R + 40, 960 + R, 540 + R + 40, "#8ec8ff", prog=ease_out(at(t, 517.8, 1.2)))
    c.restore()
    doc_title(c, t, 515.9, "THE OBSERVABLE UNIVERSE", None, dur=2)
    fact(c, t, 517.9, "~93 BILLION LIGHT-YEARS ACROSS", 960, 1050, 38, "#8ec8ff", dur=2.6)
    fact(c, t, 520.5, "HUNDREDS OF BILLIONS OF GALAXIES", 960, 1050, 38, "#ffffff", dur=2.6)
    fact(c, t, 523.3, "ONLY THE PART WE CAN SEE", 960, 1050, 40, "#ffd36b", dur=2.2)
    if t > 525.6:
        k = at(t, 525.8, 1.4)
        for i in range(120):
            rnd = random.Random(i)
            x, y = rnd.uniform(0, W), rnd.uniform(0, H)
            if math.hypot(x - 960, y - 540) > 470 * z + 20:
                c.drawCircle(x, y, rnd.uniform(1, 2.5), P("#8a8aa8", a=0.5 * k))
        fact(c, t, 525.7, "THE UNIVERSE MAY BE FAR BIGGER", 960, 120, 42, "#ffffff")


# ======================================================================= 31/37. FOMALHAUT
def fomalhaut(c, x, y, s, t, a=1.0):
    nebula(c, x, y, 0.95 * s, "ring", t, a=a, breathe=0.0)
    with xf(c, x, y, s, -12, alpha=a):
        for k, (col, wdt, aa) in enumerate((("#ff7a3a", 60, 0.25), ("#ffb05a", 26, 0.5), ("#ffe0a0", 8, 0.7))):
            c.drawOval(skia.Rect(-420, -230, 420, 230), P(col, wdt, aa))
    star(c, x, y, 26 * s, "#ffffff", t)


def s_fomalhaut(c, t, t0, t1, second=False):
    k_end = t1 - t0
    cam(c, push(t, t0, t1, 1.0 if not second else 1.25, 1.1 if not second else 1.0), 960, 540, t)
    bg(c, t)
    fomalhaut(c, 960, 520, 1.0, t)
    doc_title(c, t, t0 + 0.3, "FOMALHAUT", "One of the brightest stars in the night sky", dur=4.5)
    fact(c, t, t0 + 3.0, "\"THE EYE OF SAURON\"", 960, 110, 46, "#ffb05a", dur=4.6)
    fact(c, t, t0 + 9.8, "~2 × THE SUN'S MASS", 960, 1000, 40, "#ffffff", dur=2.6)
    fact(c, t, t0 + 12.4, "ONLY 25 LIGHT-YEARS AWAY", 960, 1000, 40, "#ffd36b")
    if second:
        guide(c, 1650, 840, t, "float_point", s=0.4, face=-1, look=(-1, -0.4))
    else:
        guide(c, 260, 820, t, keys(t, [(t0, "float"), (t0 + 3.0, "float_wow"), (t0 + 6.0, "float_point")]), s=0.45,
              look=(1, -0.4), expr="wide" if t0 + 3 < t < t0 + 6 else "smile")


# ======================================================================= 32/38. BUTTERFLY NEBULA
def s_butterfly(c, t, t0, t1, second=False):
    cam(c, push(t, t0, t1, 1.0, 1.15), 960, 540, t)
    bg(c, t)
    nebula(c, 960, 540, 1.35, "butterfly", t, a=at(t, t0, 0.8))
    doc_title(c, t, t0 + 0.2, "BUTTERFLY NEBULA", None, dur=3)
    k = ease_out(at(t, t0 + 1.8, 1.2))
    dim_line(c, 960 - 820, 940, 960 + 820, 940, "#9ad0ff", prog=k)
    fact(c, t, t0 + 1.9, "WINGS: 3+ LIGHT-YEARS ACROSS", 960, 1010, 36, "#9ad0ff", dur=3.0)
    fact(c, t, t0 + 4.8, "ONE OF THE MOST COMPLEX EVER SEEN", 960, 110, 40, "#ffffff", dur=3.4)
    if t > t0 + 8.4:
        thermometer(c, 1640, 460, 0.8, ease_out(at(t, t0 + 8.6, 1.4)))
        fact(c, t, t0 + 8.6, "~450,000 °F", 1640, 660, 40, "#ff7a4a", dur=4.0)
        glow(c, 960, 540, 120, "#ffffff", 0.6)
    if t > t0 + 12.4 and t0 + 12.4 < t1:
        fact(c, t, t0 + 12.5, "FROM A STAR ~5 × THE SUN'S MASS", 960, 110, 40, "#ffd36b")
    if second and t > 633.3:
        kb = ease_out(at(t, 633.4, 1.0))
        c.drawOval(skia.Rect(960 - 160, 540 - 40, 960 + 160, 540 + 40), P("#3a2020", 30, 0.9 * kb))
        for sgn in (-1, 1):
            ka = at(t, 635.2, 1.0)
            arrow(c, 960 + sgn * 140, 540, 960 + sgn * (140 + 420 * ease_out(ka)), 540, "#ffd36b", 12, a=ka)
        fact(c, t, 633.5, "A THICK BELT OF DUST", 960, 1010, 38, "#ffd9a8", dur=4.0)
        fact(c, t, 637.9, "HOURGLASS · BUTTERFLY SHAPE", 960, 1010, 40, "#ffd36b")
    guide(c, 240, 860, t, "float_wow" if t < t0 + 4 else "float_point", s=0.36, look=(1, -0.4),
          expr="wide" if t < t0 + 4 else "smile")


# ======================================================================= 33. TRILLION SUNS (558.1 - 563.6)
def s_trillion(c, t):
    cam(c, push(t, 558.1, 563.6, 1.0, 1.15), 960, 540, t)
    bg(c, t)
    galaxy(c, 960, 540, 620, t, "elliptical", tilt=0.8, rot=10, spin=0, blur=2)
    black_hole(c, 960, 540, 26, t, disk=1.0)
    fact(c, t, 558.3, "A TRILLION SUNS", 960, 120, 46, "#ffe6c0", dur=2.2)
    if t > 560.4:
        u = clamp((t - 560.4) / 2.6)
        ang = 1 + u * 5
        rr = 380 * (1 - u)
        sx, sy = 960 + math.cos(ang) * rr, 540 + math.sin(ang) * rr * 0.6
        sun(c, sx, sy, 26 * (1 - u * 0.8), t)
        fact(c, t, 560.5, "EATS ~1 SUN EVERY DAY", 960, 120, 46, "#ffd36b")


# ======================================================================= 34. GREAT ATTRACTOR (563.6 - 581.2)
def s_attractor(c, t):
    cam(c, push(t, 563.6, 581.2, 1.0, 1.1), 960, 540, t)
    screen_fill(c, ["#02030a", "#070a1a"])
    ax, ay = 1450, 520
    galaxy_field(c, t, (-40, -40, W + 40, H + 40), n=700, a=0.5)
    rnd = random.Random(17)
    k = ease_out(at(t, 571.9, 1.0))
    for i in range(380):
        x0, y0 = rnd.uniform(-100, W + 100), rnd.uniform(-100, H + 100)
        dx, dy = ax - x0, ay - y0
        d = math.hypot(dx, dy) + 1
        pull = k * ((t - 571.9) * 18 % 200) if k else 0
        x, y = x0 + dx / d * pull * 0.5, y0 + dy / d * pull * 0.5
        c.drawCircle(x, y, rnd.uniform(1, 3), P(rnd.choice(["#cfe0ff", "#ffe2b8"]), a=0.7))
        if k and i % 6 == 0:
            arrow(c, x, y, x + dx / d * 40, y + dy / d * 40, "#8ec8ff", 2.5, a=0.5 * k)
    glow(c, ax, ay, 300, "#ffb07a", 0.18 * (0.7 + 0.3 * math.sin(t)))
    mw = (760, 640)
    galaxy(c, mw[0] + 30 * k * math.sin(0) + 20 * k, mw[1], 40, t, "milkyway", tilt=0.6, rot=-10, spin=4)
    text(c, "MILKY WAY", mw[0], mw[1] + 70, 26, "#8ec8ff", "Bold", shadow=True)
    if t > 576.7:
        kb = smooth(at(t, 576.7, 1.2))
        with xf(c, 1450, 520, 1, -60, alpha=kb):
            for i in range(30):
                glow(c, random.Random(i).uniform(-700, 700), random.Random(i + 3).gauss(0, 60),
                     random.Random(i + 6).uniform(80, 160), "#c8b080", 0.28)
        guide(c, 300, 820, t, "think", s=0.45, space=True, expr="focus", look=(1, -0.3))
    doc_title(c, t, 565.9, "THE GREAT ATTRACTOR", None, dur=2)
    fact(c, t, 567.9, "150–250 MILLION LIGHT-YEARS AWAY", 960, 1010, 40, "#ffb07a", dur=3.8)
    fact(c, t, 572.0, "PULLING THOUSANDS OF GALAXIES", 960, 1010, 40, "#ffffff", dur=4.5)
    fact(c, t, 576.8, "HIDDEN BEHIND OUR GALAXY'S CENTRE", 960, 1010, 40, "#c8b080")


# ======================================================================= 35. COSMIC WEB (581.2 - 593.2)
def s_web(c, t):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#010208", "#05060f"]))
    z = push(t, 581.2, 593.2, 1.6, 0.85)
    cosmic_web(c, t, zoom=z)
    doc_title(c, t, 584.6, "THE COSMIC WEB", "Threads and walls of galaxies", dur=4.6)
    fact(c, t, 586.9, "ENORMOUS EMPTY VOIDS", 960, 120, 40, "#ffffff", dur=2.6)
    fact(c, t, 589.7, "LIKE A SPONGE — OR A SPIDER WEB", 960, 120, 40, "#d0b0ff")


# ======================================================================= 36. SUN'S JOURNEY (593.2 - 602.9)
def s_journey(c, t):
    cam(c, push(t, 593.2, 602.9, 1.0, 1.06), 960, 540, t)
    bg(c, t)
    galaxy(c, 960, 540, 500, t, "milkyway", tilt=1.0, rot=0, spin=2)
    ang = 2.4 + (t - 593.2) * 0.25
    orbit(c, 960, 540, 300, 1.0, "#ffd36b", 0.5, 2, prog=1.0)
    sx, sy = 960 + 300 * math.cos(ang), 540 + 300 * math.sin(ang)
    glow(c, sx, sy, 30, "#ffd36b", 0.8)
    c.drawCircle(sx, sy, 7, P("#fff2c0"))
    text(c, "SUN", sx, sy - 24, 26, "#ffd36b", "Bold", shadow=True)
    fact(c, t, 596.7, "~450,000 MPH", 960, 110, 44, "#ffd36b", dur=2.5)
    fact(c, t, 599.2, "ONE LAP: ~230 MILLION YEARS", 960, 110, 44, "#ffffff")
    guide(c, 1650, 840, t, "float_wow" if t > 599 else "float", s=0.4, face=-1, look=(-1, -0.4),
          expr="wide" if t > 599 else "smile")


# ======================================================================= 39. OUTRO (641.2 - end)
def s_outro(c, t):
    cam(c, push(t, 641.0, 647, 1.0, 1.04), 960, 540, t)
    bg(c, t)
    planet(c, 1500, 1200, 500, "earth", t, spin=0.04)
    guide(c, 760, 600, t, keys(t, [(641.0, "wave"), (643.6, "point"), (645.0, "open")]), s=1.0, expr="happy",
          look=(0.3, 0))
    k1 = back_out(at(t, 643.9, 0.4))
    k2 = back_out(at(t, 645.0, 0.4))
    if k1 > 0:
        with xf(c, 1240, 400, k1):
            c.drawCircle(0, 0, 100, P("#ffffff", a=0.12))
            thumbs_up(c, 0, 10, 0.8)
    if k2 > 0:
        with xf(c, 1500, 400, k2):
            c.drawCircle(0, 0, 100, P("#ffffff", a=0.12))
            share_icon(c, 0, 0, 0.8)


# ======================================================================= timeline
SCENES = [
    (0.0, 8.7, s_jupiter), (8.7, 16.2, s_bigger), (16.2, 33.5, s_ab_aur), (33.5, 46.1, s_disc),
    (46.1, 61.1, s_ab_b), (61.1, 81.1, s_forming), (81.1, 104.1, s_gq), (104.1, 118.7, s_uy),
    (118.7, 138.7, s_bh), (138.7, 154.7, s_fermi), (154.7, 170.5, s_void_eri), (170.5, 198.5, s_nebulae),
    (198.5, 227.1, s_comet), (227.1, 246.0, s_pasta), (246.0, 262.0, s_pulsar), (262.0, 285.3, s_haumea),
    (285.3, 300.9, s_sun), (300.9, 321.0, s_olympus), (321.0, 343.4, s_valles), (343.4, 362.0, s_ganymede),
    (362.0, 380.3, s_grs), (380.3, 399.2, s_saturn), (399.2, 413.9, s_pillars), (413.9, 428.1, s_laniakea),
    (428.1, 448.9, s_wall), (448.9, 466.7, s_ic1101), (466.7, 478.3, s_bootes), (478.3, 493.9, s_magnetar),
    (493.9, 515.7, s_sgr), (515.7, 528.0, s_universe),
    (528.0, 542.5, lambda c, t: s_fomalhaut(c, t, 528.0, 542.5)),
    (542.5, 558.1, lambda c, t: s_butterfly(c, t, 542.5, 558.1)),
    (558.1, 563.6, s_trillion), (563.6, 581.2, s_attractor), (581.2, 593.2, s_web), (593.2, 602.9, s_journey),
    (602.9, 617.7, lambda c, t: s_fomalhaut(c, t, 602.9, 617.7, True)),
    (617.7, 641.1, lambda c, t: s_butterfly(c, t, 617.7, 641.1, True)),
    (641.1, 1e9, s_outro),
]
INNER_CUTS = [5.0, 13.2, 24.6, 28.2, 50.0, 54.3, 74.6, 77.4, 89.4, 93.3, 98.1, 110.6, 122.9, 126.0, 132.0,
              177.0, 179.4, 206.2, 215.2, 219.2, 232.9, 235.6, 242.6, 250.8, 254.2, 267.7, 277.5, 280.7, 291.8,
              296.5, 305.6, 317.4, 331.7, 335.5, 349.5, 357.4, 367.3, 373.8, 388.7, 393.8, 415.9, 501.0, 504.9,
              510.0, 512.6]
CUTS = [s for s, _, _ in SCENES[1:]] + INNER_CUTS


CUTS = sorted(set(CUTS + [190.0, 484.9, 487.6]))
XFADE = 0.55


def _scene(t):
    for start, end, fn in SCENES:
        if start <= t < end:
            return fn
    return SCENES[-1][2]


def _draw(c, t):
    n = c.getSaveCount()
    c.save()
    _scene(t)(c, t)
    c.restoreToCount(n)


def render_frame(c, t):
    """Every cut is a soft cross-dissolve with a gentle settle-in zoom (no hard black dips)."""
    c.clear(C("#000000"))
    cut = None
    for ct in CUTS:
        if 0 <= t - ct < XFADE:
            cut = ct
    if cut is None:
        _draw(c, t)
    else:
        k = smooth((t - cut) / XFADE)
        _draw(c, cut - 0.001)
        c.saveLayerAlpha(None, int(255 * k))
        z = 1.035 - 0.035 * ease_out((t - cut) / XFADE)
        c.translate(W / 2, H / 2)
        c.scale(z, z)
        c.translate(-W / 2, -H / 2)
        _draw(c, t)
        c.restore()
    vignette(c, 0.4)
    grain(c, t, 0.04)
    if t < 0.8:
        tint(c, "#000000", 1 - smooth(t / 0.8))
    if t > 644.5:
        tint(c, "#000000", smooth((t - 644.5) / 2.0))
