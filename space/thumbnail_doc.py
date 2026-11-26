"""Thumbnail in black & white engraved style: giant planet vs tiny Jupiter.
Usage: python thumbnail_doc.py OUTDIR"""
import math
import os
import random
import sys

import skia

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cosmos import W, H, P, C, font  # noqa: E402

L = (-0.72, -0.5, 0.48)  # light dir (upper-left, toward viewer)
_n = math.sqrt(sum(v * v for v in L))
L = tuple(v / _n for v in L)


def engraved_planet(c, cx, cy, r, seed=1, step=5.0, bands=True, storm=None, wscale=1.0):
    rnd = random.Random(seed)
    c.save()
    clip = skia.Path()
    clip.addCircle(cx, cy, r)
    c.clipPath(clip, skia.ClipOp.kIntersect, True)
    c.drawCircle(cx, cy, r, P("#000000"))
    band_ph = [rnd.uniform(0, 6.28) for _ in range(6)]

    def bright(u, v):
        z2 = 1 - u * u - v * v
        if z2 <= 0:
            return 0.0, 0.0
        z = math.sqrt(z2)
        lam = max(0.0, u * L[0] + v * L[1] + z * L[2])
        b = 0.04 + 1.05 * lam ** 1.35
        if bands:
            b *= 0.62 + 0.38 * (0.5 + 0.5 * math.sin(v * 13 + band_ph[0] + 0.6 * math.sin(v * 31 + band_ph[1])))
        if storm:
            su, sv, sr = storm
            d = math.hypot((u - su) / 1.7, v - sv) / sr
            if d < 1:
                b *= 0.55 + 0.45 * abs(math.sin(d * 14))
        return min(1.0, b), z

    y = -r
    while y < r:
        v = y / r
        pts = []
        nseg = max(12, int(2 * r * math.sqrt(max(0, 1 - v * v)) / 7))
        half = math.sqrt(max(0.0, 1 - v * v))
        for k in range(nseg + 1):
            u = -half + 2 * half * k / nseg
            wav = 0.012 * math.sin(u * 9 + band_ph[2] + v * 20) + 0.006 * math.sin(u * 23 + band_ph[3])
            pts.append((u, v + wav))
        for k in range(nseg):
            (u1, v1), (u2, v2) = pts[k], pts[k + 1]
            b, z = bright((u1 + u2) / 2, v)
            if b < 0.06:
                continue
            w = (0.35 + 2.6 * b) * wscale
            c.drawLine(cx + u1 * r, cy + v1 * r, cx + u2 * r, cy + v2 * r, P("#ffffff", w, 0.35 + 0.6 * b))
        y += step
    # stipple + pits
    for i in range(int(r * r / 90)):
        u, v = rnd.uniform(-1, 1), rnd.uniform(-1, 1)
        b, z = bright(u, v)
        if z <= 0:
            continue
        if rnd.random() < b * 0.8:
            c.drawCircle(cx + u * r, cy + v * r, rnd.uniform(0.6, 1.6) * wscale, P("#ffffff", a=0.7))
        elif rnd.random() < 0.25:
            c.drawCircle(cx + u * r, cy + v * r, rnd.uniform(0.8, 2.2) * wscale, P("#000000", a=0.9))
    if storm:
        su, sv, sr = storm
        for k in range(1, 8):
            rx, ry = r * sr * 1.7 * k / 7, r * sr * k / 7
            c.drawOval(skia.Rect(cx + su * r - rx, cy + sv * r - ry, cx + su * r + rx, cy + sv * r + ry),
                       P("#000000" if k % 2 else "#ffffff", 2.2 * wscale, 0.55))
    c.restore()
    c.drawCircle(cx, cy, r, P("#ffffff", 2.5 * wscale, 0.5))


def stars(c):
    rnd = random.Random(3)
    for _ in range(700):
        c.drawCircle(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(0.5, 1.8), P("#ffffff", a=rnd.uniform(0.2, 0.8)))


def bold(c, s, x, y, size, color):
    f = font(size, "Black")
    c.drawString(s, x + 5, y + 7, f, P("#000000", a=0.8))
    c.drawString(s, x, y, f, P(color))
    return f.measureText(s)


def thumb(c):
    c.clear(C("#000000"))
    stars(c)
    # giant planet on the right
    engraved_planet(c, 1560, 720, 660, seed=7, step=4.6, storm=(-0.35, 0.28, 0.13))
    # sound-wave-like rings between them
    for k in range(6):
        R = 230 + k * 55
        pth = skia.Path()
        pth.addArc(skia.Rect(900 - R, 720 - R, 900 + R, 720 + R), 150, 60)
        p = P("#ffffff", 3.0 - k * 0.35, 0.75 - k * 0.1)
        if k >= 4:
            p.setPathEffect(skia.DashPathEffect.Make([6, 8], 0))
        c.drawPath(pth, p)
    # tiny Jupiter on the left
    engraved_planet(c, 300, 760, 58, seed=2, step=2.6, storm=(0.2, 0.3, 0.16), wscale=0.55)
    # red hand-drawn arrow toward tiny Jupiter
    pth = skia.Path()
    pth.moveTo(640, 250)
    pth.cubicTo(520, 330, 340, 450, 315, 640)
    c.drawPath(pth, P("#ff1a1a", 15))
    ang = math.atan2(640 - 450, 315 - 340)
    hx, hy = 313, 675
    head = skia.Path()
    for i, (dx, dy) in enumerate(((0, 0), (-math.cos(ang - 0.5) * 70, -math.sin(ang - 0.5) * 70),
                                  (-math.cos(ang + 0.5) * 70, -math.sin(ang + 0.5) * 70))):
        (head.moveTo if i == 0 else head.lineTo)(hx + dx, hy + dy)
    head.close()
    c.drawPath(head, P("#ff1a1a"))
    # headline
    x = 50
    w = bold(c, "JUPITER IS ", x, 190, 160, "#ffffff")
    bold(c, "TINY..", x + w, 190, 160, "#ff1a1a")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    s = skia.Surface(W, H)
    thumb(s.getCanvas())
    img = s.makeImageSnapshot()
    img.save(os.path.join(out, "thumbnail_1920x1080.png"), skia.kPNG)
    img.resize(1280, 720, skia.SamplingOptions(skia.CubicResampler.Mitchell())).save(
        os.path.join(out, "thumbnail_1280x720.png"), skia.kPNG)
