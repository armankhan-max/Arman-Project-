"""Thumbnail "20 BUSINESSES THAT WORK WITHOUT YOU" redrawn in the house 2D style (same pose/gestures/layout)."""
import math, random, sys
import skia
from kit import (W, H, C, P, xf, rrect, poly, line, text, text_width, linear, radial, fill_shader, glow,
                 mixhex, blurpaint)

NAVY, NAVY2 = "#26396b", "#1b2a52"
SKIN = "#f1c9a5"


def bill(c, x, y, rot, s=1.0):
    with xf(c, x, y, rot=rot, s=s):
        rrect(c, -17, -9, 34, 18, 3, "#3e8a4a")
        rrect(c, -15, -7, 30, 14, 2, "#74c27a")
        c.drawCircle(0, 0, 4.5, P("#3e8a4a"))


def coin(c, x, y, r=6):
    c.drawCircle(x, y, r, P("#b8860b"))
    c.drawCircle(x, y, r * 0.78, P("#f2c230"))
    c.drawCircle(x - r * 0.2, y - r * 0.2, r * 0.3, P("#fff0a0", a=0.8))


def pile(c, x, y, w, h, seed):
    rnd = random.Random(seed)
    for i in range(70):
        u = rnd.random()
        px = x + (rnd.random() * 2 - 1) * w * 0.5 * (1 - u * 0.75)
        py = y - u * h
        bill(c, px, py, rnd.uniform(-60, 60), 0.9)
    for i in range(14):
        coin(c, x + rnd.uniform(-w * 0.55, w * 0.55), y + rnd.uniform(-8, 6), 6)
    for k in range(3):                       # coin stacks
        for j in range(4 + k):
            coin(c, x + w * 0.55 - k * 14, y + 4 - j * 5, 6.5)


def falling(c, x0, y0, x1, y1, n, seed):
    rnd = random.Random(seed)
    for i in range(n):
        u = (i + 0.5) / n
        bill(c, lerp(x0, x1, u) + rnd.uniform(-9, 9), lerp(y0, y1, u), rnd.uniform(-70, 70), 0.9)


def lerp(a, b, t):
    return a + (b - a) * t


def atm(c, x, y):
    rrect(c, x, y, 130, 210, 8, "#8793a0")
    rrect(c, x, y, 130, 210, 8, "#4b5563", stroke=4)
    rrect(c, x + 14, y + 12, 102, 22, 5, "#3f7fa6")
    text(c, "ATM", x + 65, y + 30, 20, "#ffffff")
    rrect(c, x + 16, y + 44, 98, 64, 6, "#1f2937")
    rrect(c, x + 22, y + 50, 86, 52, 4, "#52b4c9")
    for i in range(3):
        line(c, x + 32, y + 66 + i * 12, x + 90 - i * 10, y + 66 + i * 12, "#d9f3f8", 3)
    for r in range(3):
        for k in range(4):
            rrect(c, x + 22 + k * 22, y + 118 + r * 14, 18, 10, 2, "#c3cbd4")
    rrect(c, x + 14, y + 168, 102, 18, 3, "#111827")
    rrect(c, x + 22, y + 174, 86, 6, 2, "#374151")


def washers(c, x, y):
    for i in range(3):
        mx = x + i * 80
        rrect(c, mx, y, 76, 118, 6, "#c9d1da")
        rrect(c, mx, y, 76, 118, 6, "#6b7686", stroke=3)
        rrect(c, mx, y, 76, 20, 6, "#aeb8c4")
        c.drawCircle(mx + 14, y + 10, 3, P("#4b5563"))
        c.drawCircle(mx + 26, y + 10, 3, P("#4b5563"))
        c.drawCircle(mx + 38, y + 62, 29, P("#7c8796"))
        if i == 1:
            c.drawOval(skia.Rect(mx + 14, y + 36, mx + 72, y + 96), P("#e6ebf1"))
            c.drawOval(skia.Rect(mx + 24, y + 44, mx + 64, y + 90), P("#4a5568"))
        else:
            c.drawCircle(mx + 38, y + 62, 24, P("#3b4a63"))
            c.drawCircle(mx + 30, y + 54, 8, P("#ffffff", a=0.3))


def vending(c, x, y):
    rrect(c, x, y, 132, 214, 8, "#7b8794")
    rrect(c, x, y, 132, 214, 8, "#323a46", stroke=4)
    rrect(c, x + 8, y + 12, 86, 160, 4, "#1c222c")
    cols = ["#f97316", "#facc15", "#ef4444", "#22c55e", "#3b82f6", "#a855f7"]
    rnd = random.Random(3)
    for r in range(5):
        line(c, x + 10, y + 40 + r * 31, x + 92, y + 40 + r * 31, "#7b8794", 3)
        for k in range(5):
            rrect(c, x + 14 + k * 16, y + 20 + r * 31, 12, 18, 2, rnd.choice(cols))
    rrect(c, x + 100, y + 14, 24, 60, 3, "#10151c")
    rrect(c, x + 104, y + 20, 16, 12, 2, "#38bdf8")
    for r in range(4):
        for k in range(2):
            c.drawCircle(x + 106 + k * 11, y + 90 + r * 14, 3.5, P("#cbd5e1"))
    rrect(c, x + 10, y + 180, 84, 22, 3, "#0b0f14")


def thought_bubble(c):
    parts = [(830, 140, 330, 105), (630, 130, 200, 95), (1030, 150, 160, 100), (560, 250, 110, 120),
             (1100, 270, 100, 130), (700, 340, 210, 100), (900, 345, 230, 95), (1030, 320, 150, 100),
             (830, 235, 360, 160)]
    c.drawOval(skia.Rect(0, 0, 0, 0), P("#000000"))
    for dx, dy, col in ((8, 10, "#101a33"),):
        for cx, cy, rx, ry in parts:
            c.drawOval(skia.Rect(cx - rx + dx, cy - ry + dy, cx + rx + dx, cy + ry + dy), P(col, a=0.5))
    for cx, cy, rx, ry in parts:
        c.drawOval(skia.Rect(cx - rx - 4, cy - ry - 4, cx + rx + 4, cy + ry + 4), P("#0f1b3a"))
    for cx, cy, rx, ry in parts:
        c.drawOval(skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry), P("#fbfcff"))
    for cx, cy, r in ((440, 410, 15), (408, 440, 10), (405, 298, 6)):
        c.drawCircle(cx, cy, r + 3, P("#0f1b3a"))
        c.drawCircle(cx, cy, r, P("#fbfcff"))


def background(c):
    fill_shader(c, skia.Rect(0, 0, 1280, 720), linear(0, 0, 0, 720, ["#2a3a5e", "#1c2744"]))
    # headboard
    rrect(c, -40, 190, 520, 420, 40, "#1d2a4a")
    rrect(c, -40, 190, 520, 420, 40, "#141d36", stroke=4)
    # window + curtain
    rrect(c, 1020, 0, 280, 345, 8, "#0f1b3a")
    rrect(c, 1034, 14, 252, 320, 4, "#18264e")
    fill_shader(c, skia.Rect(1034, 14, 1286, 334), linear(0, 14, 0, 334, ["#1a2c5c", "#0f1a3c"]))
    line(c, 1160, 14, 1160, 334, "#0f1b3a", 7)
    line(c, 1034, 170, 1286, 170, "#0f1b3a", 7)
    for sx, sy, r in ((1075, 70, 9), (1190, 55, 7), (1245, 235, 8), (1090, 250, 6), (1210, 190, 5)):
        pth = skia.Path()
        pth.moveTo(sx, sy - r); pth.quadTo(sx + 1, sy - 1, sx + r, sy); pth.quadTo(sx + 1, sy + 1, sx, sy + r)
        pth.quadTo(sx - 1, sy + 1, sx - r, sy); pth.quadTo(sx - 1, sy - 1, sx, sy - r)
        c.drawPath(pth, P("#ffe27a"))
    c.drawCircle(1222, 124, 42, P("#ffd84a"))
    c.drawCircle(1244, 108, 40, P("#18264e"))
    # curtain
    cp = skia.Path()
    cp.moveTo(1030, 0); cp.lineTo(1115, 0); cp.cubicTo(1130, 90, 1085, 170, 1105, 330); cp.lineTo(1030, 330); cp.close()
    c.drawPath(cp, P("#27407a"))
    for k in range(3):
        line(c, 1050 + k * 22, 8, 1046 + k * 26, 320, "#1c2f60", 5)
    line(c, 1020, 6, 1300, 6, "#0f1b3a", 8)
    # nightstand + lamp
    rrect(c, 1150, 455, 170, 280, 6, "#222f52")
    rrect(c, 1150, 455, 170, 280, 6, "#131b33", stroke=4)
    rrect(c, 1168, 492, 140, 82, 5, "#2b3a63")
    rrect(c, 1168, 492, 140, 82, 5, "#131b33", stroke=3)
    c.drawCircle(1238, 533, 6, P("#9aa7c4"))
    rrect(c, 1215, 430, 32, 28, 5, "#27407a")
    rrect(c, 1228, 372, 8, 62, 3, "#2e4a85")
    c.drawPath(poly([(1195, 368), (1275, 368), (1295, 300), (1180, 300)]), P("#4668b3"))
    c.drawPath(poly([(1275, 368), (1295, 300), (1280, 300), (1262, 368)]), P("#34528f"))


def bed(c):
    # base + sheet
    rrect(c, -30, 640, 1330, 120, 10, "#1b2547")
    sh = skia.Path()
    sh.moveTo(-20, 560); sh.cubicTo(300, 520, 700, 575, 1020, 540)
    sh.cubicTo(1130, 530, 1200, 560, 1300, 590); sh.lineTo(1300, 720); sh.lineTo(-20, 720); sh.close()
    c.drawPath(sh, P("#f3f6fb"))
    sh2 = skia.Path()
    sh2.moveTo(-20, 650); sh2.cubicTo(400, 600, 800, 640, 1300, 640); sh2.lineTo(1300, 720); sh2.lineTo(-20, 720); sh2.close()
    c.drawPath(sh2, P("#dde5f2"))
    for yy in (610, 665):
        pth = skia.Path(); pth.moveTo(40, yy); pth.cubicTo(380, yy - 30, 760, yy + 20, 1200, yy - 10)
        c.drawPath(pth, P("#c9d4e8", 4, 0.8))
    # pillow
    with xf(c, 240, 505, rot=-5):
        rrect(c, -250, -118, 500, 236, 90, "#c4d2ea")
        rrect(c, -250, -128, 500, 236, 90, "#f7f9fd")
        pth = skia.Path(); pth.moveTo(-170, 40); pth.cubicTo(-60, 70, 90, 70, 200, 30)
        c.drawPath(pth, P("#c4d2ea", 5, 0.9))


def face(c, cx, cy, r):
    # ears
    for sx in (-1, 1):
        c.drawCircle(cx + sx * r * 0.98, cy + 6, r * 0.2, P(mixhex(SKIN, "#000000", 0.08)))
        c.drawCircle(cx + sx * r * 0.98, cy + 6, r * 0.09, P(mixhex(SKIN, "#000000", 0.2)))
    c.drawCircle(cx, cy, r, P(SKIN))
    c.save()
    pc = skia.Path(); pc.addCircle(cx, cy, r)
    c.clipPath(pc, doAntiAlias=True)
    c.drawCircle(cx + r * 1.25, cy, r * 0.8, P(mixhex(SKIN, "#a85a3a", 0.13)))
    c.restore()
    # hair: thick grey with side tufts
    hair = skia.Path()
    hair.addArc(skia.Rect(cx - r - 4, cy - r - 8, cx + r + 4, cy + r * 0.7), 180, 180)
    hair.close()
    c.save()
    c.clipRect(skia.Rect(cx - r - 20, cy - r - 30, cx + r + 20, cy - r * 0.5))
    c.drawPath(hair, P("#cfd3da"))
    c.restore()
    for sx in (-1, 1):
        rrect(c, cx + sx * (r - 4) - 11, cy - r * 0.55, 22, r * 0.72, 10, "#cfd3da")
    # forehead wrinkles
    for k in range(2):
        pth = skia.Path(); pth.moveTo(cx - r * 0.3, cy - r * 0.42 + k * 9); pth.quadTo(cx, cy - r * 0.5 + k * 9, cx + r * 0.3, cy - r * 0.42 + k * 9)
        c.drawPath(pth, P("#c99772", 2.5, 0.8))
    # brows (thick, grey)
    for sx in (-1, 1):
        line(c, cx + sx * r * 0.52, cy - r * 0.18, cx + sx * r * 0.14, cy - r * 0.22, "#a9afba", r * 0.13)
    # closed eyes (peaceful arcs) + lashes crease
    for sx in (-1, 1):
        ex = cx + sx * r * 0.34
        pth = skia.Path(); pth.moveTo(ex - r * 0.2, cy + r * 0.04); pth.quadTo(ex, cy + r * 0.22, ex + r * 0.2, cy + r * 0.04)
        c.drawPath(pth, P("#2a1a14", r * 0.07))
        line(c, ex + sx * r * 0.22, cy + r * 0.06, ex + sx * r * 0.32, cy + r * 0.1, "#c99772", 2.5)
    # nose
    pth = skia.Path(); pth.moveTo(cx + 2, cy + r * 0.08); pth.quadTo(cx + r * 0.16, cy + r * 0.36, cx - r * 0.04, cy + r * 0.4)
    c.drawPath(pth, P("#c18a64", r * 0.07))
    # cheeks + smile
    for sx in (-1, 1):
        c.drawOval(skia.Rect(cx + sx * r * 0.52 - r * 0.16, cy + r * 0.36, cx + sx * r * 0.52 + r * 0.16, cy + r * 0.52),
                   P("#ff7a7a", a=0.3))
        pth = skia.Path(); pth.moveTo(cx + sx * r * 0.36, cy + r * 0.42); pth.quadTo(cx + sx * r * 0.5, cy + r * 0.62, cx + sx * r * 0.34, cy + r * 0.78)
        c.drawPath(pth, P("#c99772", 2.5, 0.8))
    pth = skia.Path(); pth.moveTo(cx - r * 0.3, cy + r * 0.58); pth.quadTo(cx, cy + r * 0.86, cx + r * 0.3, cy + r * 0.58)
    c.drawPath(pth, P("#9a3f38", r * 0.075))


def man(c):
    # trousers + shoe
    tr = skia.Path()
    tr.moveTo(760, 540); tr.cubicTo(860, 560, 960, 600, 1040, 640); tr.lineTo(1060, 700)
    tr.lineTo(990, 706); tr.cubicTo(900, 690, 820, 680, 740, 665); tr.close()
    c.drawPath(tr, P("#1f2f5e"))
    c.drawPath(poly([(780, 600), (1040, 665), (1010, 700), (770, 660)]), P("#18244b"))
    rrect(c, 1020, 640, 78, 68, 24, "#10131c")
    c.drawOval(skia.Rect(1030, 652, 1070, 668), P("#ffffff", a=0.18))
    # jacket body
    jk = skia.Path()
    jk.moveTo(420, 455); jk.cubicTo(560, 420, 720, 450, 830, 540)
    jk.cubicTo(860, 600, 840, 650, 780, 670)
    jk.cubicTo(640, 690, 520, 670, 430, 625); jk.close()
    c.drawPath(jk, P(NAVY))
    sh = skia.Path()
    sh.moveTo(520, 640); sh.cubicTo(640, 680, 760, 680, 830, 640); sh.cubicTo(850, 610, 840, 580, 826, 552)
    sh.cubicTo(790, 600, 650, 640, 520, 640); sh.close()
    c.drawPath(sh, P(NAVY2))
    pth = skia.Path(); pth.moveTo(470, 470); pth.cubicTo(600, 440, 740, 470, 810, 540)
    c.drawPath(pth, P("#3d548e", 5, 0.9))
    # shirt collar + tie
    c.drawPath(poly([(402, 470), (468, 452), (520, 520), (462, 560)]), P("#ffffff"))
    c.drawPath(poly([(402, 470), (440, 480), (470, 540), (440, 560)]), P("#dfe5ee"))
    c.drawPath(poly([(455, 520), (496, 500), (700, 590), (688, 622), (610, 612)]), P("#c8202f"))
    c.drawPath(poly([(455, 520), (480, 540), (496, 500)]), P("#8f1420"))
    c.drawPath(poly([(496, 500), (700, 590), (690, 560), (505, 492)]), P("#e04050", a=0.5))
    # lapel + pocket
    pth = skia.Path(); pth.moveTo(520, 520); pth.cubicTo(560, 560, 600, 600, 640, 640)
    c.drawPath(pth, P(NAVY2, 7))
    line(c, 660, 570, 740, 590, NAVY2, 5)
    c.drawPath(poly([(662, 566), (700, 560), (704, 576), (666, 580)]), P("#ffffff"))
    # head (tilted on pillow)
    with xf(c, 292, 452, rot=-68):
        face(c, 0, 0, 84)
    # sleeve + hands under cheek
    sl = skia.Path()
    sl.moveTo(440, 560); sl.cubicTo(420, 590, 390, 600, 350, 600); sl.lineTo(340, 548); sl.cubicTo(380, 548, 410, 530, 420, 500); sl.close()
    c.drawPath(sl, P(NAVY2))
    c.drawPath(poly([(352, 548), (372, 546), (378, 604), (358, 606)]), P("#ffffff"))
    for ox, oy, rot in ((0, 0, -20), (26, 14, -8)):
        with xf(c, 312 + ox, 560 + oy, rot=rot):
            rrect(c, -34, -20, 68, 40, 20, SKIN)
            rrect(c, -34, -20, 68, 40, 20, "#d49f78", stroke=2.5)
            for k in range(3):
                line(c, -22 + k * 14, -16, -22 + k * 14, 4, "#d49f78", 2.5)


def title(c):
    def fit(s, w, size0=100):
        return size0 * w / text_width(s, size0)
    s1 = fit("20 BUSINESSES", 540)
    for s, cx, by, size, col in (("20 BUSINESSES", 290, 90, s1, "#ffffff"), ("THAT WORK", 262, 192, s1, "#ffffff"),
                                 ("WITHOUT YOU", 290, 292, fit("WITHOUT YOU", 450), "#ffe600")):
        text(c, s, cx + 6, by + 8, size, "#000000", a=0.45, outline="#000000", ow=size * 0.22)
        text(c, s, cx, by, size, col, outline="#000000", ow=size * 0.2)
        text(c, s, cx, by, size, col)


def render(path, w, h):
    s = skia.Surface(w, h)
    c = s.getCanvas()
    c.scale(w / 1280, h / 720)
    background(c)
    bed(c)
    thought_bubble(c)
    atm(c, 560, 98)
    falling(c, 605, 330, 640, 380, 3, 1)
    pile(c, 625, 392, 150, 70, 11)
    washers(c, 725, 128)
    falling(c, 805, 260, 842, 340, 5, 2)
    pile(c, 848, 395, 190, 80, 12)
    vending(c, 1000, 98)
    falling(c, 1048, 318, 1052, 350, 3, 3)
    pile(c, 1060, 392, 150, 70, 13)
    man(c)
    title(c)
    s.makeImageSnapshot().save(path, skia.kPNG)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    render(f"{out}/thumbnail_20_businesses_1920x1080.png", 1920, 1080)
    render(f"{out}/thumbnail_20_businesses_1280x720.png", 1280, 720)
