"""Thumbnail: 'DREAM BIG / NEVER ACT'. Black-white-red ink look; only the dream bubble is warm yellow.

  python thumbnail.py   ->  thumbnail_1920x1080.png, thumbnail_1280x720.png
"""
import math
import os
import random
import sys

import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pgfx import *  # noqa: F401,F403,E402
from psets import trophy  # noqa: E402

CAST["ink"] = dict(skin="#f4f1ea", hairc="#2e2e2e", top="#f4f1ea", top2="#d9d5cc", legs="#f4f1ea", shoe="#f4f1ea",
                   hair="messy", kind="tee")
CAST["doubt"] = dict(skin="#f4f1ea", hairc="#141414", top="#f4f1ea", top2="#d9d5cc", legs="#f4f1ea",
                     shoe="#f4f1ea", hair="gray_sides", kind="tee")

RED_BOX = "#a3070a"
GRAY = skia.ColorFilters.Matrix([
    0.30, 0.59, 0.11, 0, 0,
    0.30, 0.59, 0.11, 0, 0,
    0.30, 0.59, 0.11, 0, 0,
    0, 0, 0, 1, 0])


def swirl_cloud(c, cx, cy, t=0.0):
    """Black flowing 'thought smoke' behind the figure, with white ink strokes."""
    rnd = random.Random(4)
    p = skia.Path()
    n = 26
    pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        rx = 330 + 60 * math.sin(a * 3 + 1) + rnd.uniform(-25, 25)
        ry = 430 + 50 * math.sin(a * 2 + 2) + rnd.uniform(-25, 25)
        pts.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
    p.moveTo(*pts[0])
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = mx - cx, my - cy
        d = math.hypot(dx, dy)
        p.quadTo(x1 + dx / d * 40, y1 + dy / d * 40, mx, my)
        p.lineTo(x2, y2)
    p.close()
    c.drawPath(p, P("#0c0c0c"))
    # flowing white ink lines inside the smoke
    for k in range(34):
        a0 = rnd.uniform(0, 2 * math.pi)
        r0 = rnd.uniform(150, 360)
        q = skia.Path()
        x0, y0 = cx + math.cos(a0) * r0 * 0.9, cy + math.sin(a0) * r0 * 1.2
        q.moveTo(x0, y0)
        for j in range(1, 6):
            a = a0 + j * 0.18 * (1 if k % 2 else -1)
            r = r0 + j * 10
            q.lineTo(cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 1.2)
        c.drawPath(q, P("#f4f1ea", rnd.uniform(2, 5), rnd.uniform(0.35, 0.8)))


def doubter(c, x, y, s, rot, expr, face, look):
    with xf(c, x, y, s, rot):
        draw_head(c, "doubt", 54, expr, 0.37, look, face)
        # long pale neck trailing back into the smoke
        pass


def _ol_line(c, x1, y1, x2, y2, w, col="#f4f1ea"):
    c.drawLine(x1, y1, x2, y2, P(OL, w + 12))
    c.drawLine(x1, y1, x2, y2, P(col, w))


def seated_figure(c, x, y, s):
    """Front-facing, cross-legged, hands pressed over the face."""
    skin = "#f4f1ea"
    with xf(c, x, y, s):
        # crossed legs (behind first, then front)
        _ol_line(c, -150, 250, 95, 330, 62, "#e6e2da")
        _ol_line(c, 150, 250, -95, 330, 62)
        for sd in (-1, 1):
            fx = sd * 120
            c.drawOval(skia.Rect(fx - 46, 310, fx + 46, 350).makeOutset(6, 6), P(OL))
            c.drawOval(skia.Rect(fx - 46, 310, fx + 46, 350), P(skin))
        # torso
        body = skia.Path()
        body.moveTo(-115, 20)
        body.quadTo(-120, -10, -90, -18)
        body.lineTo(90, -18)
        body.quadTo(120, -10, 115, 20)
        body.lineTo(130, 250)
        body.lineTo(-130, 250)
        body.close()
        c.drawPath(body, P(OL, 12))
        c.drawPath(body, P(skin))
        c.save()
        c.clipPath(body, skia.ClipOp.kIntersect, True)
        c.drawRect(skia.Rect(60, -20, 140, 310), P("#d8d4cb"))
        c.restore()
        p = skia.Path()
        p.addArc(skia.Rect(-45, -40, 45, 30), 10, 160)
        c.drawPath(p, P(OL, 6))
        # neck + head
        rrect(c, -22, -70, 44, 60, 8, OL)
        rrect(c, -16, -66, 32, 56, 6, "#dcd8cf")
        halo = skia.Paint(ColorFilter=skia.ColorFilters.Blend(C("#f4f1ea"), skia.BlendMode.kSrcIn))
        c.saveLayer(skia.Rect(-300, -400, 300, 100), halo)
        for ox, oy in ((-7, 0), (7, 0), (0, -7), (0, 7), (-5, -5), (5, -5)):
            with xf(c, ox, -165 + oy, 1.8):
                draw_head(c, "ink", 54, "scared", 0.37, (0.3, 0.1), 0.0)
        c.restore()
        with xf(c, 0, -165, 1.8):
            draw_head(c, "ink", 54, "scared", 0.37, (0.3, 0.1), 0.0)
        # upper arms + forearms rising to the face
        for sd in (-1, 1):
            sh = (sd * 100, 10)
            el = (sd * 165, -35)
            wr = (sd * 60, -128)
            _ol_line(c, sh[0], sh[1], el[0], el[1], 50)
            _ol_line(c, el[0], el[1], wr[0], wr[1], 46)
        # hands over the face: left hand covers one eye, right hand slightly lower so the other eye peeks out
        draw_hand(c, -60, -128, 172, 50, skin, "relax", 1, 5)
        draw_hand(c, 64, -100, 198, 50, skin, "open", -1, 5)


def main():
    S = 1.5  # draw at 1920x1080
    surf = skia.Surface(1920, 1080)
    c = surf.getCanvas()
    c.clear(C("#fbfaf7"))

    # ---------------- text (about 15% larger than the reference, short + punchy)
    f = dfont(250, "bebas")
    tx = 70
    w1 = dwidth("DREAM BIG", 250, "bebas", 0.02)
    dtext(c, "DREAM BIG", tx, 520, 250, "#0d0d0d", "bebas", "left", track=0.02)
    w2 = dwidth("NEVER ACT", 230, "bebas", 0.02)
    bx, by, bw, bh = tx - 22, 570, w2 + 60, 230
    c.drawRect(skia.Rect(bx, by, bx + bw, by + bh), P(RED_BOX))
    dtext(c, "NEVER ACT", tx + 8, by + 198, 230, "#ffffff", "bebas", "left", track=0.02)

    # ---------------- artwork (slightly smaller than the reference)
    cx, cy = 1440, 560
    art = skia.Rect(980, 0, 1920, 1080)
    c.saveLayer(art, skia.Paint(ColorFilter=GRAY))
    swirl_cloud(c, cx, cy - 10)
    # doubting faces circling the head
    heads = [(-230, -290, -22, "angry", 0.6, (0.9, 0.4)), (-30, -390, 4, "deadpan", 0.2, (0, 1)),
             (190, -300, 20, "angry", -0.6, (-0.9, 0.4)), (-285, -95, -30, "sad", 0.7, (1, 0)),
             (260, -95, 28, "deadpan", -0.7, (-1, 0.2)), (-200, 120, -15, "worried", 0.6, (1, -0.6)),
             (220, 130, 18, "angry", -0.6, (-1, -0.6))]
    for dx, dy, r_, ex, fc, lk in heads:
        doubter(c, cx + dx, cy - 60 + dy, 1.05, r_, ex, fc, lk)
    # seated figure, cross-legged, hands over the face (one eye peeking through the fingers)
    seated_figure(c, cx, cy + 40, 1.0)
    c.restore()
    # thin ink outline around the art block edge of the smoke is already there; ground shadow
    c.drawOval(skia.Rect(cx - 220, cy + 440, cx + 220, cy + 480), P("#000000", a=0.12))

    # ---------------- the ONE colour: a warm glowing dream bubble above the head
    bxc, byc = cx + 175, 140
    soft(c, bxc, byc, 210, "#ffc94a", 0.55, 90)
    c.drawCircle(bxc, byc, 120, P("#ffd65a"))
    c.drawCircle(bxc, byc, 120, P("#141414", 7))
    c.drawCircle(bxc - 40, byc - 45, 26, P("#fff6cf", a=0.9))
    trophy(c, bxc, byc + 46, 0.48)
    for i, (ox, oy, rr) in enumerate(((-95, 150, 26), (-140, 200, 17))):
        c.drawCircle(bxc + ox, byc + oy, rr, P("#ffd65a"))
        c.drawCircle(bxc + ox, byc + oy, rr, P("#141414", 5))

    img = surf.makeImageSnapshot()
    img.save(os.path.join(HERE, "thumbnail_1920x1080.png"), skia.kPNG)
    img.resize(1280, 720, skia.SamplingOptions(skia.FilterMode.kLinear)).save(
        os.path.join(HERE, "thumbnail_1280x720.png"), skia.kPNG)
    print("ok")


if __name__ == "__main__":
    main()
