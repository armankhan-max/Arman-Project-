"""Sets (blurred, cached backgrounds) and props for the psych documentary."""
import math
import random

import skia

from pgfx import *  # noqa: F401,F403
from sgfx import _shelf  # noqa: E402


# ================================================================= SETS
# Painted-look sets: textured walls/floors, outlined furniture, then a lighting pass
# (multiply darkness + screen-blended light pools + haze), like a lit illustration.
SOL = "#1f191c"


def _p_ol(c, path, col, w=4):
    c.drawPath(path, P(col))
    c.drawPath(path, P(SOL, w))


def box(c, x, y, w, h, col, r=6, ow=4, shade_k=0.0):
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)
    c.drawRRect(rr, P(col))
    if shade_k:
        c.save()
        c.clipRRect(rr, skia.ClipOp.kIntersect, True)
        c.drawRect(skia.Rect(x, y + h * 0.65, x + w, y + h), P(shade(col, shade_k)))
        c.drawRect(skia.Rect(x, y, x + w, y + 5), P(hilite(col, 0.2)))
        c.restore()
    if ow:
        c.drawRRect(rr, P(SOL, ow))


def bricks(c, rect, base, bw=120, bh=52, seed=1, mortar=None, var=0.12, stone=False):
    x0, y0, x1, y1 = rect
    rnd = random.Random(seed)
    mortar = mortar or shade(base, 0.45)
    c.save()
    c.clipRect(skia.Rect(x0, y0, x1, y1))
    c.drawRect(skia.Rect(x0, y0, x1, y1), P(mortar))
    row = 0
    y = y0
    while y < y1:
        h = bh * (rnd.uniform(0.8, 1.2) if stone else 1)
        off = (bw / 2 if row % 2 else 0) if not stone else rnd.uniform(0, bw)
        x = x0 - off
        while x < x1:
            w = bw * (rnd.uniform(0.7, 1.4) if stone else 1)
            col = mixhex(base, rnd.choice(["#000000", "#ffffff", "#5a3020"]), rnd.uniform(0, var))
            rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x + 3, y + 3, w - 6, h - 6), 6 if stone else 3, 6 if stone else 3)
            c.drawRRect(rr, P(col))
            c.drawLine(x + 6, y + 5, x + w - 8, y + 5, P(hilite(col, 0.18), 3))
            c.drawLine(x + 6, y + h - 6, x + w - 8, y + h - 6, P(shade(col, 0.25), 3))
            x += w
        y += h
        row += 1
    c.restore()


def plaster(c, rect, base, seed=1, stripes=False):
    x0, y0, x1, y1 = rect
    fill_shader(c, skia.Rect(x0, y0, x1, y1), linear(0, y0, 0, y1, [hilite(base, 0.06), shade(base, 0.12)]))
    rnd = random.Random(seed)
    c.save()
    c.clipRect(skia.Rect(x0, y0, x1, y1))
    for i in range(40):
        soft(c, rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(40, 140), shade(base, 0.3), 0.08, 40)
    if stripes:
        for x in range(int(x0), int(x1), 64):
            c.drawRect(skia.Rect(x, y0, x + 26, y1), P(shade(base, 0.06)))
    c.restore()


def wood_floor(c, y0, base="#6b4a32", seed=2, vx=W / 2, plank=120):
    rnd = random.Random(seed)
    c.drawRect(skia.Rect(0, y0, W, H), P(base))
    n = 22
    vy = y0 - 900
    for i in range(-n, n + 1):
        xb = vx + i * plank
        xt = vx + (xb - vx) * (y0 - vy) / (H - vy)
        pts = [(xt, y0), (vx + (xb + plank - vx) * (y0 - vy) / (H - vy), y0), (xb + plank, H), (xb, H)]
        col = mixhex(base, rnd.choice(["#000000", "#ffffff"]), rnd.uniform(0, 0.1))
        c.drawPath(poly(pts), P(col))
        c.drawLine(xt, y0, xb, H, P(shade(base, 0.35), 3))
    for k in range(6):
        yy = y0 + (H - y0) * (k / 6) ** 1.6
        c.drawLine(0, yy, W, yy, P(shade(base, 0.25), 2, 0.5))
    fill_shader(c, skia.Rect(0, y0, W, y0 + 60), linear(0, y0, 0, y0 + 60, [("#000000", 0.35), ("#000000", 0)]))


def tile_floor(c, y0, a="#cfd8d8", b="#b4c0c0", vx=W / 2, n=14, rows=8):
    vy = y0 - 900
    c.drawRect(skia.Rect(0, y0, W, H), P(a))
    ys = [y0 + (H - y0) * (k / rows) ** 1.5 for k in range(rows + 1)]
    for r_ in range(rows):
        for i in range(-n, n):
            xb0 = vx + i * 160
            xb1 = xb0 + 160

            def X(xb, yy):
                return vx + (xb - vx) * (yy - vy) / (H - vy)
            pts = [(X(xb0, ys[r_]), ys[r_]), (X(xb1, ys[r_]), ys[r_]), (X(xb1, ys[r_ + 1]), ys[r_ + 1]),
                   (X(xb0, ys[r_ + 1]), ys[r_ + 1])]
            c.drawPath(poly(pts), P(a if (i + r_) % 2 else b))
    fill_shader(c, skia.Rect(0, y0, W, y0 + 60), linear(0, y0, 0, y0 + 60, [("#000000", 0.3), ("#000000", 0)]))


def skirting(c, y, col="#3a2c26", h=26):
    c.drawRect(skia.Rect(0, y - h, W, y), P(col))
    c.drawLine(0, y - h, W, y - h, P(SOL, 4))
    c.drawLine(0, y - h + 5, W, y - h + 5, P(hilite(col, 0.2), 2))


def win_frame(c, x, y, w, h, frame="#e8e2d6", sky=("#9cc8e8", "#dff0ff"), panes=(2, 2), blinds=0, draw=None):
    box(c, x - 14, y - 14, w + 28, h + 28, frame, 6, 4)
    fill_shader(c, skia.Rect(x, y, x + w, y + h), linear(0, y, 0, y + h, list(sky)))
    if draw:
        c.save()
        c.clipRect(skia.Rect(x, y, x + w, y + h))
        draw(c, x, y, w, h)
        c.restore()
    for i in range(1, panes[0]):
        c.drawRect(skia.Rect(x + w * i / panes[0] - 6, y, x + w * i / panes[0] + 6, y + h), P(frame))
    for j in range(1, panes[1]):
        c.drawRect(skia.Rect(x, y + h * j / panes[1] - 6, x + w, y + h * j / panes[1] + 6), P(frame))
    if blinds:
        for i in range(blinds):
            yy = y + i * h / blinds
            c.drawRect(skia.Rect(x, yy, x + w, yy + h / blinds * 0.55), P("#e9e4d8", a=0.85))
            c.drawLine(x, yy + h / blinds * 0.55, x + w, yy + h / blinds * 0.55, P(shade("#e9e4d8", 0.3), 2))
    c.drawRect(skia.Rect(x, y, x + w, y + h), P(SOL, 4))
    box(c, x - 30, y + h + 10, w + 60, 22, frame, 4, 4)


def skyline(c, x, y, w, h, seed=3, night=True):
    rnd = random.Random(seed)
    xx = x
    while xx < x + w:
        bw = rnd.uniform(40, 90)
        bh = rnd.uniform(0.25, 0.8) * h
        col = "#1d2340" if night else "#8a9ab8"
        c.drawRect(skia.Rect(xx, y + h - bh, xx + bw - 4, y + h), P(col))
        for r_ in range(int(bh / 22)):
            for q in range(int(bw / 18)):
                if rnd.random() > 0.55:
                    c.drawRect(skia.Rect(xx + 6 + q * 16, y + h - bh + 8 + r_ * 22, xx + 14 + q * 16,
                                         y + h - bh + 18 + r_ * 22), P("#ffd98a" if night else "#dfe8f5", a=0.75))
        xx += bw


def books_shelf(c, x, y, w, h, wood="#5a3a26", seed=4, rows=3):
    box(c, x, y, w, h, wood, 4, 4)
    rnd = random.Random(seed)
    sh = (h - 20) / rows
    for k in range(rows):
        yy = y + 10 + k * sh
        c.drawRect(skia.Rect(x + 10, yy, x + w - 10, yy + sh - 12), P(shade(wood, 0.45)))
        xx = x + 14
        while xx < x + w - 30:
            bw = rnd.uniform(14, 30)
            bh = rnd.uniform(sh * 0.55, sh * 0.85)
            col = rnd.choice(["#8a3a2e", "#2f5b7a", "#c9a24a", "#3d6b4a", "#6a4a7a", "#d8cfbf", "#a0522d"])
            lean = 0 if rnd.random() > 0.15 else 8
            pp = poly([(xx, yy + sh - 12), (xx + bw, yy + sh - 12), (xx + bw + lean, yy + sh - 12 - bh),
                       (xx + lean, yy + sh - 12 - bh)])
            c.drawPath(pp, P(col))
            c.drawPath(pp, P(SOL, 2.5))
            c.drawLine(xx + 4, yy + sh - 12 - bh * 0.8, xx + bw - 4, yy + sh - 12 - bh * 0.8, P(hilite(col, 0.4), 2))
            xx += bw + lean + rnd.uniform(1, 4)
        box(c, x + 6, yy + sh - 14, w - 12, 12, hilite(wood, 0.1), 2, 3)


def plant(c, x, y, s=1.0, pot="#b5653a"):
    with xf(c, x, y, s):
        for i in range(9):
            a = -2.7 + i * 0.3
            lx, ly = math.cos(a) * 110, math.sin(a) * 130 - 60
            pth = skia.Path()
            pth.moveTo(0, -20)
            pth.quadTo(lx * 0.4 - 20, ly * 0.6, lx, ly)
            pth.quadTo(lx * 0.6 + 20, ly * 0.4, 0, -20)
            _p_ol(c, pth, "#4f8a4a" if i % 2 else "#3d7040", 3)
        pp = poly([(-60, -20), (60, -20), (45, 80), (-45, 80)])
        _p_ol(c, pp, pot, 4)
        c.drawRect(skia.Rect(-62, -24, 62, -6), P(shade(pot, 0.2)))


def lamp_floor(c, x, y, s=1.0):
    with xf(c, x, y, s):
        c.drawLine(0, 0, 0, -380, P(SOL, 12))
        c.drawLine(0, 0, 0, -380, P("#3a2c26", 6))
        box(c, -50, -6, 100, 16, "#3a2c26", 6, 3)
        pp = poly([(-80, -360), (80, -360), (55, -470), (-55, -470)])
        _p_ol(c, pp, "#f2d49a", 4)


def light(c, x, y, r, col="#ffc46b", a=0.6):
    p = skia.Paint(BlendMode=skia.BlendMode.kScreen)
    p.setShader(radial(x, y, r, [(col, a), (col, a * 0.35), (col, 0)], [0, 0.4, 1]))
    c.drawRect(skia.Rect(x - r, y - r, x + r, y + r), p)


def beam(c, pts, col="#fff2d0", a=0.18):
    p = skia.Paint(BlendMode=skia.BlendMode.kScreen, AntiAlias=True)
    p.setColor(C(col, a))
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18))
    c.drawPath(poly(pts), p)


def darkness(c, col="#0a0814", a=0.5, cx=W / 2, cy=H / 2, r=None):
    """Multiply-darken the edges (a painted vignette tinted with the ambient colour)."""
    a = min(0.9, a * 1.3)
    p = skia.Paint(BlendMode=skia.BlendMode.kMultiply)
    p.setShader(radial(cx, cy, r or W * 0.75, [("#ffffff", 1.0), (mixhex("#ffffff", col, a), 1.0)], [0.25, 1]))
    c.drawRect(skia.Rect(0, 0, W, H), p)


def haze(c, y, h, col="#c8d4e0", a=0.18, seed=1):
    rnd = random.Random(seed)
    for i in range(14):
        soft(c, rnd.uniform(0, W), y + rnd.uniform(0, h), rnd.uniform(160, 320), col, a, 90)


_paper = []


def paper_texture(c, a=0.06):
    if not _paper:
        s = skia.Surface(W // 2, H // 2)
        cc = s.getCanvas()
        cc.clear(skia.ColorTRANSPARENT)
        rnd = random.Random(11)
        for _ in range(1400):
            x, y = rnd.uniform(0, W / 2), rnd.uniform(0, H / 2)
            cc.drawCircle(x, y, rnd.uniform(2, 14), P(rnd.choice(["#000000", "#ffffff"]), a=rnd.uniform(0.05, 0.25)))
        _paper.append(s.makeImageSnapshot())
    p = skia.Paint()
    p.setAlphaf(a)
    c.drawImageRect(_paper[0], skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.FilterMode.kLinear), p)


def set_hospital(c, t=0.0):
    plaster(c, (0, 0, W, 760), "#a9c8c4", 1)
    c.drawRect(skia.Rect(0, 470, W, 760), P("#8fb3ae"))
    c.drawLine(0, 470, W, 470, P(SOL, 4))
    c.drawLine(0, 476, W, 476, P("#c6dcd8", 3))
    tile_floor(c, 760, "#c9d3d0", "#b3c0bd")
    skirting(c, 760, "#6f8f8a")

    def outside(cc, x, y, w, h):
        skyline(cc, x, y + h * 0.35, w, h * 0.65, 5, night=False)
    win_frame(c, 1160, 130, 560, 420, "#e8ece8", ("#a8d0ec", "#f2f8ff"), (2, 1), blinds=9, draw=outside)
    beam(c, [(1160, 150), (1720, 150), (1350, H), (560, H)], "#fff4dc", 0.22)
    # curtain rail + pleated curtain
    box(c, 60, 60, 680, 16, "#9aa8a6", 6, 3)
    for i in range(10):
        col = "#5f9f97" if i % 2 else "#6fb0a8"
        pp = poly([(80 + i * 34, 76), (116 + i * 34, 76), (122 + i * 34, 740), (74 + i * 34, 740)])
        c.drawPath(pp, P(col))
    c.drawRect(skia.Rect(74, 76, 462, 740), P(SOL, 4))
    # wall details: socket panel, sign, hand sanitiser
    box(c, 780, 300, 260, 110, "#dfe8e6", 8, 4)
    for i in range(3):
        box(c, 800 + i * 80, 330, 50, 50, "#ffffff", 6, 3)
    box(c, 1830, 300, 60, 120, "#e8ecef", 10, 3)
    box(c, 560, 150, 160, 110, "#f4f1e8", 4, 4)
    c.drawLine(590, 190, 690, 190, P("#3a7a74", 6))
    c.drawLine(590, 220, 660, 220, P("#9aa8a6", 4))
    light(c, 1450, 300, 700, "#fff1d6", 0.35)
    haze(c, 300, 500, "#e8f4f0", 0.1, 4)
    darkness(c, "#183a3a", 0.5)
    paper_texture(c)


def set_physio(c, t=0.0):
    plaster(c, (0, 0, W, 720), "#c8d6e0", 2)
    for i in range(3):
        win_frame(c, 160 + i * 580, 110, 420, 380, "#f0f2f4", ("#9ec8ea", "#eaf4ff"), (2, 2), blinds=0,
               draw=lambda cc, x, y, w, h: (skyline(cc, x, y + h * 0.5, w, h * 0.5, 9 + int(x), night=False)))
        beam(c, [(160 + i * 580, 120), (580 + i * 580, 120), (700 + i * 580, H), (40 + i * 580, H)], "#fff6e0", 0.12)
    wood_floor(c, 720, "#b88a5a", 4)
    skirting(c, 720, "#8a6a4a")
    # wall bars on the right
    for i in range(6):
        c.drawLine(1760 + (i % 2) * 0, 170, 1760, 700, P(SOL, 1))
    for k in range(9):
        box(c, 1700, 180 + k * 58, 180, 14, "#c9a06a", 6, 3)
    box(c, 1700, 160, 14, 560, "#a07a4a", 4, 3)
    box(c, 1866, 160, 14, 560, "#a07a4a", 4, 3)
    # exercise ball + mat
    c.drawCircle(260, 760, 95, P(SOL))
    c.drawCircle(260, 760, 90, P("#4a8ad9"))
    soft(c, 230, 720, 30, "#ffffff", 0.4, 12)
    box(c, 520, 900, 700, 50, "#3a7a9a", 12, 4)
    light(c, 960, 300, 900, "#fff6e0", 0.3)
    darkness(c, "#1a2a3a", 0.45)
    paper_texture(c)


def set_bedroom(c, t=0.0):
    plaster(c, (0, 0, W, 780), "#4a4468", 3, stripes=True)

    def night(cc, x, y, w, h):
        fill_shader(cc, skia.Rect(x, y, x + w, y + h), linear(0, y, 0, y + h, ["#0c1430", "#2a3460"]))
        for i in range(40):
            rnd = random.Random(i)
            cc.drawCircle(x + rnd.uniform(0, w), y + rnd.uniform(0, h * 0.5), rnd.uniform(1, 2.5), P("#ffffff", a=0.7))
        cc.drawCircle(x + w * 0.78, y + h * 0.25, 42, P("#f6f1de"))
        soft(cc, x + w * 0.78, y + h * 0.25, 90, "#f6f1de", 0.3, 40)
        skyline(cc, x, y + h * 0.4, w, h * 0.6, 7, night=True)
    win_frame(c, 1180, 120, 540, 420, "#5a4a6a", ("#0c1430", "#2a3460"), (2, 2), draw=night)
    # curtains
    for sd, x in ((-1, 1130), (1, 1770)):
        pp = poly([(x - 50, 90), (x + 50, 90), (x + 40 + sd * 20, 640), (x - 40 + sd * 20, 640)])
        _p_ol(c, pp, "#7a3a4a", 4)
    box(c, 1080, 80, 740, 16, "#2a2030", 6, 3)
    # corkboard with plans
    box(c, 150, 160, 520, 340, "#a8774a", 8, 5)
    rnd = random.Random(3)
    for i in range(10):
        col = rnd.choice(["#ffd166", "#ff9f80", "#9be3c3", "#a8c8ff"])
        x = 175 + (i % 5) * 98
        y = 190 + (i // 5) * 150 + rnd.uniform(-10, 10)
        with xf(c, x + 40, y + 50, rot=rnd.uniform(-8, 8)):
            box(c, -40, -50, 84, 90, col, 2, 3)
            c.drawCircle(0, -42, 7, P("#d14a3a"))
            for k in range(3):
                c.drawLine(-28, -20 + k * 18, 24, -20 + k * 18, P("#5a4a3a", 3, 0.5))
    books_shelf(c, 760, 200, 300, 300, "#5a3a2e", 6, 2)
    # poster
    box(c, 760, 560, 200, 150, "#2f5b8a", 4, 4)
    c.drawCircle(860, 635, 40, P("#ffcf6b"))
    wood_floor(c, 780, "#5a3e30", 6)
    skirting(c, 780, "#3a2a24")
    # desk + lamp
    box(c, 300, 690, 1100, 44, "#7a5238", 8, 5, 0.3)
    box(c, 340, 734, 34, 230, "#5a3a2a", 4, 4)
    box(c, 1326, 734, 34, 230, "#5a3a2a", 4, 4)
    box(c, 1100, 734, 220, 160, "#6a4630", 6, 4)
    box(c, 1180, 790, 60, 12, "#c9a86a", 4, 2)
    c.drawLine(1250, 690, 1210, 560, P(SOL, 14))
    c.drawLine(1250, 690, 1210, 560, P("#2a2030", 8))
    _p_ol(c, poly([(1150, 560), (1290, 540), (1270, 490), (1170, 500)]), "#ffcf8a", 4)
    light(c, 1230, 620, 520, "#ffb35c", 0.55)
    light(c, 1450, 320, 520, "#7a9aff", 0.18)
    haze(c, 200, 500, "#8a8ad0", 0.08, 5)
    darkness(c, "#0c0a1a", 0.65, 1150, 560)
    paper_texture(c)


def set_shower(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#6a9ab4", "#2e5068"]))
    for j in range(0, H, 110):
        for i in range(0, W, 110):
            rnd = random.Random(i * 7 + j)
            col = mixhex("#7fb2cc", "#ffffff", rnd.uniform(0, 0.12))
            box(c, i + 4, j + 4, 102, 102, col, 6, 0)
            c.drawLine(i + 10, j + 10, i + 60, j + 10, P("#ffffff", 3, 0.35))
    c.drawLine(1500, 0, 1500, 140, P(SOL, 22))
    c.drawLine(1500, 0, 1500, 140, P("#d8e0e6", 14))
    _p_ol(c, poly([(1420, 140), (1580, 140), (1550, 190), (1450, 190)]), "#d8e0e6", 4)
    light(c, 1500, 200, 600, "#ffffff", 0.3)
    darkness(c, "#0a1a28", 0.5)
    paper_texture(c)


def set_bus(c, t=0.0):
    c.drawRect(skia.Rect(0, 0, W, 120), P("#5a6270"))
    c.drawLine(0, 118, W, 118, P(SOL, 6))
    for i in range(6):
        c.drawLine(160 + i * 320, 120, 160 + i * 320, 150, P(SOL, 10))
        c.drawLine(160 + i * 320, 120, 160 + i * 320, 150, P("#c9ced8", 6))
        c.drawCircle(160 + i * 320, 172, 24, P(SOL, 10))
        c.drawCircle(160 + i * 320, 172, 24, P("#e8b04a", 6))
    c.drawRect(skia.Rect(0, 740, W, H), P("#3a3f4a"))
    c.drawLine(0, 740, W, 740, P(SOL, 6))


def set_ceiling(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, W, H, ["#5a5478", "#2a2640"]))
    rnd = random.Random(2)
    for i in range(0, W, 140):
        c.drawLine(i, 0, i, H, P("#4a4468", 3))
    light(c, 600, 300, 700, "#ffcf8a", 0.25)
    paper_texture(c)


def set_office(c, t=0.0):
    plaster(c, (0, 0, W, 760), "#c9a27a", 5)

    def sunset(cc, x, y, w, h):
        fill_shader(cc, skia.Rect(x, y, x + w, y + h), linear(0, y, 0, y + h, ["#ff9f6a", "#ffd9a0", "#ffe8c8"]))
        cc.drawCircle(x + w * 0.7, y + h * 0.55, 90, P("#fff2d0"))
        skyline(cc, x, y + h * 0.45, w, h * 0.55, 12, night=False)
    win_frame(c, 180, 100, 1560, 520, "#4a3428", ("#ff9f6a", "#ffe8c8"), (4, 1), draw=sunset)
    beam(c, [(180, 120), (1740, 120), (1900, H), (0, H)], "#ffd9a0", 0.12)
    wood_floor(c, 760, "#7a5238", 8)
    skirting(c, 760, "#4a3428")
    plant(c, 1760, 680, 1.3)
    light(c, 1300, 360, 900, "#ffb36b", 0.4)
    darkness(c, "#2a1408", 0.4)
    paper_texture(c)


def set_exam(c, t=0.0):
    plaster(c, (0, 0, W, 760), "#b8b088", 6)
    box(c, 360, 100, 1200, 420, "#8a6a42", 10, 5)
    fill_shader(c, skia.Rect(380, 120, 1540, 500), linear(0, 120, 0, 500, ["#2f5a44", "#244a38"]))
    for i in range(4):
        c.drawLine(440, 200 + i * 70, 440 + (760 - i * 140), 200 + i * 70, P("#e9efe8", 5, 0.6))
    dtext(c, "FINAL EXAM", 960, 170, 50, "#f2f2e8", "bebas", a=0.8, track=0.2)
    box(c, 360, 520, 1200, 18, "#6a4a2a", 4, 4)
    c.drawCircle(1710, 220, 78, P(SOL))
    c.drawCircle(1710, 220, 72, P("#f4efe2"))
    c.drawLine(1710, 220, 1710, 170, P(SOL, 7))
    c.drawLine(1710, 220, 1745, 230, P(SOL, 7))
    win_frame(c, 60, 140, 220, 420, "#e8e2d6", ("#9ec8ea", "#eaf4ff"), (1, 2))
    wood_floor(c, 760, "#8a6a48", 9)
    skirting(c, 760, "#5a4a32")
    light(c, 200, 300, 700, "#fff2d0", 0.3)
    darkness(c, "#1a1a10", 0.45)
    paper_texture(c)


def set_cafe(c, t=0.0):
    bricks(c, (0, 0, W, 770), "#9a5a3e", 130, 54, 3)

    def street(cc, x, y, w, h):
        fill_shader(cc, skia.Rect(x, y, x + w, y + h), linear(0, y, 0, y + h, ["#f4c88a", "#c98a5a"]))
        skyline(cc, x, y + h * 0.3, w, h * 0.7, 21, night=False)
    win_frame(c, 100, 120, 720, 470, "#2e2420", ("#f4c88a", "#c98a5a"), (2, 1), draw=street)
    # chalk menu
    box(c, 1000, 120, 420, 300, "#2a2a28", 8, 6)
    dtext(c, "MENU", 1210, 190, 54, "#f2efe6", "bebas", track=0.3)
    for i in range(4):
        c.drawLine(1050, 240 + i * 42, 1300 - (i * 37) % 80, 240 + i * 42, P("#e8e2d6", 4, 0.6))
    # pendant lamps
    for xx in (1530, 1760):
        c.drawLine(xx, 0, xx, 210, P(SOL, 4))
        _p_ol(c, poly([(xx - 70, 260), (xx + 70, 260), (xx + 40, 210), (xx - 40, 210)]), "#2f4a3a", 4)
        light(c, xx, 300, 360, "#ffb35c", 0.55)
    # counter
    box(c, 960, 520, 960, 250, "#6a4630", 8, 5, 0.25)
    box(c, 940, 500, 1000, 30, "#c9a27a", 6, 4)
    box(c, 1600, 400, 160, 100, "#b8bcc4", 10, 4)
    wood_floor(c, 770, "#6a4a34", 10)
    light(c, 460, 360, 700, "#ffcf8a", 0.3)
    darkness(c, "#1a0c06", 0.5)
    paper_texture(c)


def set_living(c, t=0.0):
    plaster(c, (0, 0, W, 780), "#6a7088", 7, stripes=True)
    win_frame(c, 230, 140, 440, 340, "#e0dcd2", ("#2a3a5a", "#5a6a8a"), (2, 2), blinds=7)
    # front door
    box(c, 1440, 160, 320, 620, "#6a4630", 8, 5)
    box(c, 1470, 190, 260, 260, "#7a5238", 6, 3)
    box(c, 1470, 480, 260, 270, "#7a5238", 6, 3)
    c.drawCircle(1712, 470, 14, P(SOL))
    c.drawCircle(1712, 470, 10, P("#e0b84a"))
    # TV glow on the wall
    box(c, 760, 290, 480, 280, "#121418", 12, 5)
    fill_shader(c, skia.Rect(780, 310, 1220, 550), linear(0, 310, 0, 550, ["#3a6ab0", "#1a2a5a"]))
    lamp_floor(c, 130, 780, 1.0)
    wood_floor(c, 780, "#4e3a30", 12)
    skirting(c, 780, "#2e2420")
    # rug
    c.drawOval(skia.Rect(420, 880, 1500, 1060), P("#8a3a3a"))
    c.drawOval(skia.Rect(470, 900, 1450, 1040), P("#c9a26a", 4))
    light(c, 130, 380, 420, "#ffcf8a", 0.5)
    light(c, 1000, 430, 500, "#6fa8ff", 0.3)
    darkness(c, "#0a0c18", 0.55)
    paper_texture(c)


def set_study(c, t=0.0):
    # wood panelling + full bookshelves: the interview set
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#5a3a28", "#3a2418"]))
    for i in range(0, W, 160):
        box(c, i + 10, 520, 140, 330, "#6a4630", 6, 3, 0.15)
    books_shelf(c, 40, 80, 520, 780, "#4a2e1e", 3, 5)
    books_shelf(c, 1380, 80, 500, 780, "#4a2e1e", 8, 5)

    def rain(cc, x, y, w, h):
        fill_shader(cc, skia.Rect(x, y, x + w, y + h), linear(0, y, 0, y + h, ["#1d2a3e", "#3a4a64"]))
        skyline(cc, x, y + h * 0.45, w, h * 0.55, 31, night=True)
        for i in range(60):
            rnd = random.Random(i)
            xx, yy = x + rnd.uniform(0, w), y + rnd.uniform(0, h)
            cc.drawLine(xx, yy, xx - 6, yy + 30, P("#9fc0e0", 2, 0.5))
    win_frame(c, 700, 120, 520, 400, "#4a2e1e", ("#1d2a3e", "#3a4a64"), (2, 2), draw=rain)
    for xx in (600, 1250):
        box(c, xx, 600, 120, 150, "#c9a35a", 4, 4)
        box(c, xx + 12, 612, 96, 126, "#efe6d2", 2, 2)
    lamp_floor(c, 1250, 880, 1.1)
    plant(c, 330, 820, 1.0)
    c.drawRect(skia.Rect(0, 860, W, H), P("#2e1c12"))
    c.drawLine(0, 860, W, 860, P(SOL, 5))
    light(c, 1250, 380, 650, "#ffb35c", 0.55)
    haze(c, 300, 500, "#ffcf9a", 0.06, 6)
    darkness(c, "#120804", 0.6, 1000, 500)
    paper_texture(c)


def set_dream(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#ffd59a", "#ffb58a", "#c98aa8"], [0, 0.55, 1]))
    light(c, 1400, 300, 700, "#fff4d0", 0.8)
    rnd = random.Random(7)
    for i in range(10):
        x, y = rnd.uniform(0, W), rnd.uniform(560, H)
        r = rnd.uniform(140, 320)
        c.drawCircle(x, y, r, P("#fff0d8", a=0.35))
    for i in range(5):
        x, y = rnd.uniform(0, W), rnd.uniform(80, 360)
        for k in range(4):
            c.drawCircle(x + k * 60, y + (k % 2) * 16, 55 + (k % 2) * 15, P("#fff6e8", a=0.55))
    c.drawRect(skia.Rect(0, 770, W, H), P("#f0b48a", a=0.6))
    paper_texture(c, 0.05)


def set_void(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H * 0.55, W * 0.6, ["#3a1414", "#120606", "#000000"],
                                                     [0, 0.6, 1]))
    haze(c, 600, 400, "#5a1a1a", 0.2, 3)
    paper_texture(c, 0.05)


def set_lab_room(c, t=0.0):
    plaster(c, (0, 0, W, 740), "#c8d4dc", 8)
    for j in range(2):
        for i in range(3):
            box(c, 160 + i * 340 - 10, 150 + j * 230 - 10, 300, 200, "#2a3038", 12, 4)
            screen_panel(c, 160 + i * 340, 150 + j * 230, 280, 180, 1.0 + i + j, ["graph", "bars", "text"][(i + j) % 3],
                         "#7fd3ff")
    books_shelf(c, 1300, 140, 460, 440, "#8a8f9a", 12, 3)
    box(c, 0, 690, W, 60, "#e8ecef", 0, 4)
    tile_floor(c, 750, "#d8dee2", "#c4ccd2")
    light(c, 600, 300, 800, "#e8f4ff", 0.35)
    darkness(c, "#1a2a3a", 0.4)
    paper_texture(c)


def set_street(c, t=0.0):
    """Night street with cobblestones, lamps and fog (like a moody illustrated alley)."""
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#2a3448", "#4a5468"]))
    c.drawCircle(1500, 160, 60, P("#e8e8f0", a=0.8))
    soft(c, 1500, 160, 140, "#e8e8f0", 0.2, 60)
    rnd = random.Random(5)
    for layer, (col, base) in enumerate((("#3a4256", 560), ("#2a3044", 640))):
        x = -40
        while x < W:
            w = rnd.uniform(160, 300)
            h = rnd.uniform(220, 420)
            c.drawRect(skia.Rect(x, base - h, x + w - 10, base + 200), P(col))
            c.drawPath(poly([(x - 10, base - h), (x + w / 2, base - h - 80), (x + w, base - h)]), P(col))
            for r_ in range(3):
                for q in range(2):
                    if rnd.random() > 0.4:
                        c.drawRect(skia.Rect(x + 30 + q * 80, base - h + 40 + r_ * 90, x + 60 + q * 80,
                                             base - h + 90 + r_ * 90), P("#ffb35c", a=0.7 if layer else 0.5))
            x += w
    haze(c, 400, 400, "#9aa8c0", 0.18, 2)
    # cobblestones in perspective
    c.drawRect(skia.Rect(0, 760, W, H), P("#3a3f4c"))
    for r_ in range(10):
        yy = 760 + (H - 760) * (r_ / 10) ** 1.4
        hh = 8 + r_ * 4
        x = -rnd.uniform(0, 60)
        while x < W:
            w = 30 + r_ * 12 + rnd.uniform(-6, 6)
            col = mixhex("#5a6070", "#000000", rnd.uniform(0, 0.25))
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, yy, w - 4, hh), hh / 2, hh / 2), P(col))
            x += w
    light(c, 300, 300, 500, "#ffb35c", 0.5)
    darkness(c, "#0a0c18", 0.55)
    paper_texture(c)


SETS = {"hospital": set_hospital, "physio": set_physio, "bedroom": set_bedroom, "shower": set_shower,
        "bus": set_bus, "ceiling": set_ceiling, "office": set_office, "exam": set_exam, "cafe": set_cafe,
        "living": set_living, "study": set_study, "dream": set_dream, "void": set_void, "labroom": set_lab_room,
        "street": set_street}


def bg(c, name, blur=7.0, a=1.0):
    """Painted set. Only a whisper of blur now: the reference style keeps backgrounds crisp but softly lit."""
    b = round(min(2.5, blur * 0.25), 1)
    img = cached(("pset", name, b), SETS[name], b)
    blit(c, img, 0, 0, a)


# ================================================================= scrolling worlds (sharp, parallax)
def dream_park(c, t, scroll, sun=True):
    """Golden dream world for walking/running. scroll = ground distance in px."""
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, 760, ["#ffcf8a", "#ffe3b0", "#ffd6a0"], [0, 0.6, 1]))
    if sun:
        glow(c, 1450, 330, 520, "#fff3c4", 0.8)
        c.drawCircle(1450, 330, 110, P("#fff6dc"))
    for layer, (col, base, amp, par) in enumerate((("#f2b98a", 640, 70, 0.15), ("#e39a72", 700, 50, 0.35))):
        pth = skia.Path()
        pth.moveTo(0, H)
        off = scroll * par
        for x in range(0, W + 41, 40):
            u = (x + off) * 0.004
            pth.lineTo(x, base - amp * (0.5 + 0.3 * math.sin(u * 1.3 + layer) + 0.2 * math.sin(u * 3.1)))
        pth.lineTo(W, H)
        c.drawPath(pth, P(col))
    # trees mid layer
    off = scroll * 0.6
    for i in range(-1, 8):
        x = i * 300 - (off % 300)
        k = int((off // 300) + i)
        rnd = random.Random(k)
        h = rnd.uniform(140, 220)
        line(c, x, 760, x, 760 - h, "#8a5a44", 16)
        c.drawCircle(x, 760 - h - 40, rnd.uniform(70, 95), P("#c9785c"))
        c.drawCircle(x - 40, 760 - h, 60, P("#d98a66"))
    c.drawRect(skia.Rect(0, 750, W, H), P("#e8a679"))
    c.drawRect(skia.Rect(0, 820, W, 900), P("#f6d2a6"))
    for i in range(-1, 12):
        x = i * 180 - (scroll % 180)
        rrect(c, x, 855, 90, 8, 4, "#ffffff", 0.5)
    # flowers foreground
    for i in range(-1, 14):
        x = i * 150 - ((scroll * 1.3) % 150)
        rnd = random.Random(int((scroll * 1.3) // 150) + i)
        c.drawCircle(x, 960 + rnd.uniform(0, 80), 10, P(rnd.choice(["#ffffff", "#ffe08a", "#ff9fb0"])))


def city_scroll(c, t, rect, speed=420, night=False):
    x0, y0, x1, y1 = rect
    c.save()
    c.clipRect(skia.Rect(x0, y0, x1, y1))
    sky = ["#2a3a5a", "#7a6a8a"] if not night else ["#0a0f24", "#1a1f3a"]
    fill_shader(c, skia.Rect(x0, y0, x1, y1), linear(0, y0, 0, y1, sky))
    for layer, (col, par, hmin, hmax, wdt) in enumerate((("#3a4466", 0.3, 0.3, 0.6, 140),
                                                         ("#252c44", 1.0, 0.25, 0.75, 110))):
        off = t * speed * par
        n0 = int(off // wdt)
        for i in range(-1, int((x1 - x0) / wdt) + 2):
            k = n0 + i
            rnd = random.Random(k * 31 + layer)
            bh = (y1 - y0) * rnd.uniform(hmin, hmax)
            bx = x0 + i * wdt - (off % wdt)
            c.drawRect(skia.Rect(bx, y1 - bh, bx + wdt - 8, y1), P(col))
            for r in range(int(bh / 34)):
                for q in range(3):
                    if rnd.random() > 0.5:
                        c.drawRect(skia.Rect(bx + 12 + q * 30, y1 - bh + 14 + r * 34, bx + 26 + q * 30,
                                             y1 - bh + 26 + r * 34), P("#ffd98a", a=0.55))
    c.restore()


# ================================================================= PROPS
def hosp_bed(c, x, y, s=1.0, front=False):
    """Bed (mattress top at y). Draw back part first, call again with front=True after the patient."""
    with xf(c, x, y, s):
        if not front:
            rrect(c, -480, -150, 30, 260, 10, "#9fb1b0")
            rrect(c, -500, 60, 1000, 40, 12, "#5f7472")
            rrect(c, -470, -10, 940, 80, 30, "#e8f0f0")
            rrect(c, -460, -60, 220, 70, 30, "#ffffff")
            line(c, -440, 100, -440, 230, "#5f7472", 12)
            line(c, 440, 100, 440, 230, "#5f7472", 12)
            c.drawCircle(-440, 236, 16, P("#2a3534"))
            c.drawCircle(440, 236, 16, P("#2a3534"))
        else:
            p = skia.Path()
            p.moveTo(-250, 10)
            p.quadTo(-120, -110, 120, -95)
            p.quadTo(330, -90, 450, -40)
            p.lineTo(470, 60)
            p.lineTo(-250, 60)
            p.close()
            c.drawPath(p, P(OUT, 8))
            c.drawPath(p, P("#7fb7c9"))
            line(c, -240, 20, 460, 20, "#a8d3e0", 6)
            rrect(c, 450, -110, 30, 220, 10, "#9fb1b0")


def monitor(c, x, y, s, t, bpm=70, col="#5fe0a0"):
    with xf(c, x, y, s):
        rrect(c, -130, -90, 260, 180, 16, OUT)
        rrect(c, -120, -80, 240, 160, 10, "#07211b")
        pth = skia.Path()
        ph = t * bpm / 60.0
        for i in range(60):
            xx = -110 + i * 220 / 60
            u = (i / 60 * 2 + ph) % 1.0
            yy = 10 - (60 if 0.4 < u < 0.43 else (-20 if 0.43 <= u < 0.46 else 6 * math.sin(u * 6.28)))
            if i == 0:
                pth.moveTo(xx, yy)
            else:
                pth.lineTo(xx, yy)
        c.drawPath(pth, P(col, 4))
        text(c, str(bpm), 85, -45, 30, col, "Bold")


def cane(c, x, y, s=1.0, rot=0.0):
    with xf(c, x, y, s, rot):
        line(c, 0, 0, 0, 260, OUT, 18)
        line(c, 0, 0, 0, 260, "#8a5a3a", 12)
        p = skia.Path()
        p.moveTo(0, 0)
        p.quadTo(0, -40, -40, -40)
        p.quadTo(-70, -40, -70, -10)
        c.drawPath(p, P(OUT, 18))
        c.drawPath(p, P("#8a5a3a", 12))


def walker_frame(c, x, y, s=1.0, h=170):
    with xf(c, x, y, s):
        for pass_, col, add in ((0, OL, 6), (1, "#c8d0d6", 0)):
            for xx in (-60, 60):
                line(c, xx, 0, xx - 10, h, col, 10 + add)
            line(c, -60, 0, 60, 0, col, 12 + add)
            line(c, -65, h * 0.4, 55, h * 0.4, col, 8 + add)
        for xx in (-70, 50):
            c.drawCircle(xx, h + 2, 14, P(OL))
            c.drawCircle(xx, h + 2, 10, P("#3a3a3a"))


def clipboard(c, x, y, s=1.0, rot=0.0, marks=0, t=0.0):
    with xf(c, x, y, s, rot):
        rrect(c, -50, -66, 100, 132, 8, "#7a5634")
        rrect(c, -42, -54, 84, 112, 4, "#f5f2ea")
        rrect(c, -18, -72, 36, 18, 5, "#b8c2c8")
        for i in range(4):
            line(c, -30, -34 + i * 24, 26, -34 + i * 24, "#9aa3ad", 4)
        if marks:
            line(c, -30, 40, -30 + 56 * clamp(marks), 40, RED, 6)


def notebook(c, x, y, s=1.0, t=0.0, flip=0.0, items=None, checks=None, rot=0.0, dust=0.0):
    """Open notebook. flip animates a page turning (0..1)."""
    items = items or []
    with xf(c, x, y, s, rot):
        rrect(c, -330, -210, 660, 420, 18, "#2a2030")
        for side in (-1, 1):
            rrect(c, -315 if side < 0 else 5, -195, 310, 390, 8, "#f4ecd8")
        line(c, 0, -200, 0, 200, "#cdbf9f", 4)
        for i, it in enumerate(items[:6]):
            col = 0 if i < 3 else 1
            yy = -130 + (i % 3) * 110
            xx = -290 if col == 0 else 30
            rrect(c, xx, yy - 30, 36, 36, 6, "#6b5a4a", stroke=4)
            text(c, it, xx + 52, yy, 34, "#3a2f28", "Bold", align="left")
            if checks and i < len(checks) and checks[i]:
                check_mark(c, xx + 18, yy - 12, 0.6, "#2e9d5a", prog=checks[i])
        if flip > 0:
            ang = flip * 180
            wv = 310 * math.cos(math.radians(ang))
            p = poly([(0, -195), (wv, -195 - 20 * math.sin(math.radians(ang))),
                      (wv, 195 - 20 * math.sin(math.radians(ang))), (0, 195)])
            c.drawPath(p, P("#ece2c8"))
            c.drawPath(p, P("#cdbf9f", 3))
        if dust > 0:
            rnd = random.Random(4)
            for i in range(40):
                c.drawCircle(rnd.uniform(-320, 320), rnd.uniform(-200, 200) + math.sin(t + i) * 4,
                             rnd.uniform(2, 5), P("#d8cdb0", a=0.5 * dust))


def phone_feed(c, x, y, s, t, scroll=0.0, rot=0.0, likes=0):
    with xf(c, x, y, s, rot):
        glow(c, 0, 0, 260, "#9fd0ff", 0.25)
        rrect(c, -95, -180, 190, 360, 26, OUT)
        rrect(c, -86, -170, 172, 340, 20, "#f4f6fa")
        c.save()
        c.clipRect(skia.Rect(-86, -150, 86, 170))
        for i in range(-1, 6):
            yy = -150 + i * 130 - (scroll % 130)
            k = int(scroll // 130) + i
            col = ["#ffb4a2", "#9bd0ff", "#c7f0b0", "#ffd98a", "#d8b4ff"][k % 5]
            rrect(c, -76, yy + 8, 152, 84, 10, col)
            c.drawCircle(-62, yy + 108, 10, P("#c0c6d0"))
            rrect(c, -46, yy + 102, 80, 10, 5, "#d0d5de")
        c.restore()
        rrect(c, -86, -170, 172, 22, 10, "#e3e7ee")
        if likes:
            for i in range(likes):
                kk = (t * 0.8 + i * 0.37) % 1.0
                heart(c, 60 + math.sin(i * 3 + t * 3) * 30, 120 - kk * 300, 18 * (1 - kk * 0.5), RED, a=1 - kk)


def heart(c, x, y, r, color=RED, a=1.0):
    p = skia.Path()
    p.moveTo(x, y + r * 0.9)
    p.cubicTo(x - r * 1.6, y - r * 0.1, x - r * 0.9, y - r * 1.4, x, y - r * 0.5)
    p.cubicTo(x + r * 0.9, y - r * 1.4, x + r * 1.6, y - r * 0.1, x, y + r * 0.9)
    c.drawPath(p, P(color, a=a))


def battery(c, x, y, s, level, t=0.0, label=None):
    col = GREEN if level > 0.5 else (GOLD if level > 0.25 else RED)
    with xf(c, x, y, s):
        rrect(c, -90, -160, 180, 320, 26, "#e8e2d6", stroke=12)
        rrect(c, -36, -186, 72, 26, 8, "#e8e2d6")
        hh = 284 * clamp(level)
        if hh > 2:
            rrect(c, -72, 142 - hh, 144, hh, 14, col)
            glow(c, 0, 142 - hh / 2, 180, col, 0.15)
        if label:
            dtext(c, label, 0, 230, 50, "#e8e2d6", "bebas", track=0.06)


def gauge(c, x, y, s, value, t=0.0, col=COOL, label=None):
    """Blood-pressure dial. value 0..1."""
    with xf(c, x, y, s):
        c.drawCircle(0, 0, 160, P("#e8e2d6"))
        c.drawCircle(0, 0, 146, P("#14181e"))
        for i in range(11):
            a = math.radians(-220 + i * 26)
            line(c, math.cos(a) * 118, math.sin(a) * 118, math.cos(a) * 138, math.sin(a) * 138, "#e8e2d6", 6)
        arc = skia.Path()
        arc.addArc(skia.Rect(-128, -128, 128, 128), -220, 260 * clamp(value))
        c.drawPath(arc, P(col, 14, 0.8))
        a = math.radians(-220 + 260 * clamp(value) + 1.5 * math.sin(t * 9))
        line(c, 0, 0, math.cos(a) * 110, math.sin(a) * 110, "#ff6a5a", 8)
        c.drawCircle(0, 0, 14, P("#e8e2d6"))
        if label:
            dtext(c, label, 0, 240, 54, col, "bebas", track=0.06)


def bp_cuff(c, x, y, s=1.0, t=0.0, pump=0.0):
    with xf(c, x, y, s):
        rrect(c, -60, -40, 120, 80, 16, "#2c3e5a")
        rrect(c, -60, -40, 120, 80, 16, "#16202e", stroke=5)
        line(c, 60, 0, 150, 60, "#16202e", 8)
        c.drawOval(skia.Rect(140, 50, 190 + 8 * pump, 110 + 8 * pump), P("#2c2c34"))


def high_heel(c, x, y, s=1.0, col="#ff4f7b", rot=0.0):
    with xf(c, x, y, s, rot):
        p = skia.Path()
        p.moveTo(-90, 10)
        p.quadTo(-80, -40, -20, -30)
        p.quadTo(30, -20, 60, 20)
        p.lineTo(100, 20)
        p.lineTo(100, 34)
        p.lineTo(-80, 34)
        p.close()
        c.drawPath(p, P(col))
        line(c, -76, 30, -84, 110, col, 10)
        c.drawPath(p, P("#000000", 4, 0.3))


def envelope(c, x, y, s=1.0, rot=0.0, open_=0.0, glow_a=0.0):
    with xf(c, x, y, s, rot):
        if glow_a:
            glow(c, 0, 0, 220, GOLD, glow_a)
        rrect(c, -110, -70, 220, 140, 10, "#fff4dc")
        c.drawPath(poly([(-110, -70), (0, 10 - open_ * 140), (110, -70)]), P("#f0dcb0"))
        c.drawPath(poly([(-110, -70), (0, 10 - open_ * 140), (110, -70)]), P("#c9a86a", 3))
        c.drawCircle(0, 10 - open_ * 140, 16, P("#d14a3a"))


def trophy(c, x, y, s=1.0, a=1.0, ghost=False):
    col = GOLD
    with xf(c, x, y, s, alpha=a):
        if ghost:
            glow(c, 0, -40, 220, GOLD, 0.35)
        p = skia.Path()
        p.moveTo(-80, -140)
        p.lineTo(80, -140)
        p.quadTo(80, -20, 0, 0)
        p.quadTo(-80, -20, -80, -140)
        c.drawPath(p, P(col))
        for sd in (-1, 1):
            pp = skia.Path()
            pp.addArc(skia.Rect(sd * 70 - 40, -130, sd * 70 + 40, -50), -90 if sd > 0 else 90, 180)
            c.drawPath(pp, P(col, 14))
        rrect(c, -14, 0, 28, 50, 4, col)
        rrect(c, -60, 50, 120, 30, 6, "#b88a2a")
        c.drawPath(poly([(-50, -120), (-30, -120), (-50, -50)]), P("#ffffff", a=0.4))


def scale_balance(c, x, y, s, tiltv, t=0.0, left=None, right=None):
    with xf(c, x, y, s):
        line(c, 0, -200, 0, 160, "#d8cfbf", 14)
        rrect(c, -120, 150, 240, 30, 10, "#d8cfbf")
        with xf(c, 0, -200, rot=tiltv):
            line(c, -300, 0, 300, 0, "#d8cfbf", 12)
            for sd, fn in ((-1, left), (1, right)):
                with xf(c, sd * 300, 0, rot=-tiltv):
                    line(c, 0, 0, -70, 150, "#d8cfbf", 3)
                    line(c, 0, 0, 70, 150, "#d8cfbf", 3)
                    p = skia.Path()
                    p.addArc(skia.Rect(-90, 110, 90, 190), 0, 180)
                    c.drawPath(p, P("#d8cfbf"))
                    if fn:
                        fn(c, 0, 120)
        c.drawCircle(0, -200, 16, P(GOLD))


def film_frame(c, x, y, w, h, t, draw_fn=None, a=1.0):
    with xf(c, x, y, alpha=a):
        rrect(c, -w / 2 - 40, -h / 2 - 50, w + 80, h + 100, 10, "#121212")
        for i in range(int(w / 50) + 1):
            xx = -w / 2 - 20 + i * 50 - (t * 120 % 50)
            rrect(c, xx, -h / 2 - 38, 26, 22, 4, "#d8d0c0")
            rrect(c, xx, h / 2 + 16, 26, 22, 4, "#d8d0c0")
        c.save()
        c.clipRect(skia.Rect(-w / 2, -h / 2, w / 2, h / 2))
        if draw_fn:
            draw_fn(c)
        c.restore()


def calendar(c, x, y, s, label, sub="", flip=0.0, col=RED):
    with xf(c, x, y, s):
        rrect(c, -130, -150, 260, 300, 18, "#f4f1ea")
        rrect(c, -130, -150, 260, 80, 18, col)
        c.drawRect(skia.Rect(-130, -100, 130, -70), P(col))
        for xx in (-70, 70):
            rrect(c, xx - 10, -170, 20, 50, 8, "#3a3a3a")
        dtext(c, label, 0, 60, 150, "#2a2a2a", "bebas")
        if sub:
            dtext(c, sub, 0, -95, 46, "#ffffff", "bebas", track=0.1)
        if flip > 0:
            hgt = 220 * (1 - flip)
            rrect(c, -130, -70, 260, max(1, hgt), 10, "#e6e1d6")


def clock_face(c, x, y, s, hours, minutes, col="#f4f1ea", glow_a=0.0):
    with xf(c, x, y, s):
        if glow_a:
            glow(c, 0, 0, 260, GOLD, glow_a)
        c.drawCircle(0, 0, 150, P(col))
        c.drawCircle(0, 0, 150, P("#2a2a2a", 12))
        for i in range(12):
            a = math.radians(i * 30)
            line(c, math.sin(a) * 118, -math.cos(a) * 118, math.sin(a) * 135, -math.cos(a) * 135, "#2a2a2a", 8)
        ha = math.radians((hours % 12 + minutes / 60) * 30)
        ma = math.radians(minutes * 6)
        line(c, 0, 0, math.sin(ha) * 70, -math.cos(ha) * 70, "#2a2a2a", 14)
        line(c, 0, 0, math.sin(ma) * 110, -math.cos(ma) * 110, "#2a2a2a", 9)
        c.drawCircle(0, 0, 12, P(RED))


def laptop(c, x, y, s, t, typing=0.0, blank=False, words=0.0):
    with xf(c, x, y, s):
        c.drawPath(poly([(-230, 0), (230, 0), (260, 30), (-260, 30)]), P("#9aa3b3"))
        rrect(c, -210, -290, 420, 290, 14, "#2a2f3a")
        rrect(c, -196, -276, 392, 262, 8, "#f6f6f2" if not blank else "#fbfbf8")
        if not blank:
            n = int(words * 9)
            for i in range(n):
                ww = 330 * (0.5 + 0.5 * ((i * 37) % 10) / 10)
                rrect(c, -170, -250 + i * 26, ww, 10, 5, "#b9bec8")
        if typing or blank:
            yy = -250 + int(words * 9) * 26
            if int(t * 2.5) % 2 == 0:
                c.drawRect(skia.Rect(-170 + (0 if blank else 0), yy - 10, -166, yy + 16), P("#2a2f3a"))


def burger(c, x, y, s=1.0, a=1.0, ghost=False):
    with xf(c, x, y, s, alpha=a):
        if ghost:
            glow(c, 0, 0, 180, GOLD, 0.4)
        p = skia.Path()
        p.addArc(skia.Rect(-110, -100, 110, 40), 180, 180)
        c.drawPath(p, P("#e0a050"))
        rrect(c, -115, -36, 230, 20, 10, "#5fbf4a")
        rrect(c, -110, -18, 220, 28, 12, "#6b3a20")
        rrect(c, -115, 6, 230, 14, 7, "#ffcc3a")
        rrect(c, -105, 18, 210, 34, 16, "#e0a050")
        for i in range(5):
            c.drawOval(skia.Rect(-60 + i * 28, -80, -50 + i * 28, -72), P("#fff2d0"))


def megaphone(c, x, y, s=1.0, rot=0.0, t=0.0, waves=0.0):
    with xf(c, x, y, s, rot):
        c.drawPath(poly([(-60, -30), (60, -80), (60, 80), (-60, 30)]), P("#e8e2d6"))
        rrect(c, -90, -34, 40, 68, 10, RED)
        rrect(c, 52, -84, 22, 168, 8, "#cfc7b6")
        for i in range(3):
            if waves > 0:
                k = (t * 1.5 + i / 3) % 1.0
                p = skia.Path()
                p.addArc(skia.Rect(60 - 40 - k * 150, -60 - k * 150, 60 + 40 + k * 150, 60 + k * 150), -40, 80)
                c.drawPath(p, P(GOLD, 8, (1 - k) * waves))


def law_book(c, x, y, s=1.0, rot=0.0, col="#7a2a2a", open_=0.0, label="LAW"):
    with xf(c, x, y, s, rot):
        rrect(c, -70, -95, 140, 190, 8, col)
        rrect(c, -58, -95, 10, 190, 3, "#00000055")
        rrect(c, -40, -40, 100, 50, 4, GOLD, stroke=4)
        dtext(c, label, 10, -2, 36, GOLD, "bebas", track=0.1)


def coin(c, x, y, r, a=1.0):
    c.drawCircle(x, y, r, P("#b8862a", a=a))
    c.drawCircle(x, y, r * 0.82, P(GOLD, a=a))
    dtext(c, "$", x, y + r * 0.35, r * 1.0, "#b8862a", "bebas", a=a)


def payslip(c, x, y, s=1.0, rot=0.0, amount="+ SATISFACTION", a=1.0):
    with xf(c, x, y, s, rot, alpha=a):
        rrect(c, -170, -100, 340, 200, 12, "#f6f1e4")
        rrect(c, -170, -100, 340, 50, 12, "#2e7d5a")
        c.drawRect(skia.Rect(-170, -70, 170, -50), P("#2e7d5a"))
        dtext(c, "PAYSLIP", 0, -62, 34, "#ffffff", "bebas", track=0.2)
        for i in range(2):
            rrect(c, -140, -20 + i * 30, 160, 10, 5, "#c8c0ae")
        dtext(c, amount, 0, 80, 40, "#2e7d5a", "bebas", track=0.05)


def invoice(c, x, y, s=1.0, rot=0.0, a=1.0):
    with xf(c, x, y, s, rot, alpha=a):
        rrect(c, -150, -190, 300, 380, 10, "#f6f1e4")
        rrect(c, -150, -190, 300, 70, 10, RED)
        c.drawRect(skia.Rect(-150, -150, 150, -120), P(RED))
        dtext(c, "BILL", 0, -138, 50, "#ffffff", "bebas", track=0.2)
        for i in range(5):
            rrect(c, -120, -90 + i * 40, 150 + (i * 23) % 60, 12, 6, "#c8c0ae")
        dtext(c, "DUE: LATER", 0, 160, 44, RED, "bebas", track=0.06)


def ceiling_fan(c, x, y, s, t):
    with xf(c, x, y, s, rot=t * 60):
        for i in range(4):
            with xf(c, 0, 0, rot=i * 90):
                rrect(c, 20, -26, 260, 52, 26, "#4a4560")
        c.drawCircle(0, 0, 40, P("#6a6580"))


def steam(c, t, a=0.4, n=10, seed=2):
    rnd = random.Random(seed)
    for i in range(n):
        x = rnd.uniform(0, W)
        y = (rnd.uniform(0, H) - t * rnd.uniform(30, 70)) % (H + 300) - 150
        soft(c, x + math.sin(t * 0.5 + i) * 40, y, rnd.uniform(120, 240), "#ffffff", a * 0.35, 80)


def rain_drops(c, t, rect, a=0.6, n=40, seed=1, col="#cfe8ff", speed=900):
    x0, y0, x1, y1 = rect
    rnd = random.Random(seed)
    for i in range(n):
        x = rnd.uniform(x0, x1)
        y = y0 + (rnd.uniform(0, y1 - y0) + t * speed * rnd.uniform(0.8, 1.2)) % (y1 - y0)
        line(c, x, y, x - 4, y + 34, col, 3, a)


def shadow_monster(c, x, y, s, t, a=1.0, eyes=1.0):
    with xf(c, x, y, s, alpha=a):
        p = skia.Path()
        p.moveTo(-320, 400)
        for i in range(13):
            ang = math.pi + i / 12 * math.pi
            rr = 330 + 40 * math.sin(i * 1.7 + t * 1.5)
            p.lineTo(math.cos(ang) * rr, -40 + math.sin(ang) * rr * 1.4)
        p.lineTo(320, 400)
        p.close()
        soft_stroke(c, p, "#ff3a2a", 30, 0.25, 40)
        c.drawPath(p, P("#050203"))
        for sd in (-1, 1):
            glow(c, sd * 110, -200, 90, "#ff3a2a", 0.6 * eyes)
            c.drawOval(skia.Rect(sd * 110 - 50, -220, sd * 110 + 50, -180), P("#ff6a4a", a=eyes))


def bar_chart(c, x, y, bars, t, start, maxh=420, bw=180, gap=90, labels=True, vals=None):
    """bars = [(label, frac, color)]; animated growth from `start`."""
    n = len(bars)
    total = n * bw + (n - 1) * gap
    line(c, x - total / 2 - 40, y, x + total / 2 + 40, y, "#d8cfbf", 4, 0.6)
    for i, (lab, frac, col) in enumerate(bars):
        k = ease_out(at(t, start + i * 0.25, 0.9))
        bx = x - total / 2 + i * (bw + gap)
        hh = maxh * frac * k
        if hh > 1:
            rrect(c, bx, y - hh, bw, hh, 10, col)
            c.drawRect(skia.Rect(bx, y - min(hh, 10), bx + bw, y), P(col))
            glow(c, bx + bw / 2, y - hh, 120, col, 0.12)
        if labels:
            dtext(c, lab, bx + bw / 2, y + 60, 44, "#e8e2d6", "bebas", a=clamp(k * 2), track=0.05)
        if vals and k > 0:
            dtext(c, vals[i], bx + bw / 2, y - hh - 24, 54, col, "bebas", a=clamp(k * 2))


def line_chart(c, x, y, w, h, pts, t, start, dur, col, width=10, label=None, dot=True):
    k = clamp((t - start) / dur)
    if k <= 0:
        return
    pth = skia.Path()
    n = len(pts)
    last = None
    for i in range(n):
        u = i / (n - 1)
        if u > k + 1e-6:
            break
        px, py = x + u * w, y - pts[i] * h
        if i == 0:
            pth.moveTo(px, py)
        else:
            pth.lineTo(px, py)
        last = (px, py)
    c.drawPath(pth, P(col, width))
    if dot and last:
        glow(c, last[0], last[1], 60, col, 0.4)
        c.drawCircle(last[0], last[1], width * 1.3, P(col))
    if label and k >= 1:
        dtext(c, label, last[0] + 20, last[1] + 16, 48, col, "bebas", "left", a=clamp((t - start - dur) / 0.4))


def axes(c, x, y, w, h, xl="", yl="", a=1.0):
    line(c, x, y, x + w, y, "#d8cfbf", 4, a)
    line(c, x, y, x, y - h, "#d8cfbf", 4, a)
    dtext(c, xl, x + w / 2, y + 60, 40, "#a9a092", "bebas", a=a, track=0.1)
    with xf(c, x - 40, y - h / 2, rot=-90):
        dtext(c, yl, 0, 0, 40, "#a9a092", "bebas", a=a, track=0.1)


def icon_circle(c, x, y, r, col, a=1.0, ring=True):
    soft(c, x, y, r * 1.2, col, 0.18 * a, r * 0.4)
    c.drawCircle(x, y, r, P("#10141a", a=a))
    if ring:
        c.drawCircle(x, y, r, P(col, 6, a))


def info_board(c, t, top="#14100c", bottom="#070504"):
    """Motion-graphics board: dark grid with warm ember glows (keeps the tint of `top`)."""
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, [mixhex(top, "#16121a", 0.6), "#0b090c"]))
    for i in range(0, W + 1, 96):
        c.drawRect(skia.Rect(i, 0, i + 1.5, H), P("#ffffff", a=0.045))
    for j in range(0, H + 1, 96):
        c.drawRect(skia.Rect(0, j, W, j + 1.5), P("#ffffff", a=0.045))
    soft(c, 120 + 40 * math.sin(t * 0.3), H - 60, 420, "#ff5a2a", 0.22, 200)
    soft(c, W - 120, 80 + 30 * math.sin(t * 0.25), 380, mixhex(top, "#ff8a4a", 0.5), 0.14, 200)
    rnd = random.Random(2)
    for i in range(24):
        x = rnd.uniform(0, W)
        y = (rnd.uniform(0, H) - t * rnd.uniform(6, 18)) % H
        c.drawCircle(x, y, rnd.uniform(1, 2.4), P("#ffd9a0", a=0.25))
