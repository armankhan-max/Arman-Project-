"""Thumbnail: giant planet vs small Jupiter. Usage: python thumbnail_doc.py OUTDIR"""
import os
import sys

import skia

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cosmos import *  # noqa: F401,F403


def big(c, s, x, y, size, color, align="center", rot=0):
    with xf(c, x, y, rot=rot):
        f = font(size, "Black")
        w = f.measureText(s)
        ox = {"left": 0, "center": -w / 2, "right": -w}[align]
        c.drawString(s, ox + 6, 10, f, P("#000000", a=0.6))
        c.drawString(s, ox, 0, f, P("#05060a", size * 0.14))
        c.drawString(s, ox, 0, f, P(color))


def thumb(c):
    t = 2.0
    deep_sky(c, t, (0, 0))
    glow(c, 560, 620, 900, "#ff4a6a", 0.28)
    planet(c, 560, 640, 470, "proto", t, dark=0.65)
    glow(c, 1380, 640, 300, "#ffd9a0", 0.25)
    planet(c, 1380, 650, 120, "jupiter", t, grs=True, dark=0.6)
    arrow(c, 1210, 650, 1080, 650, "#ffd36b", 22)
    guide(c, 1760, 880, t, "wow", s=0.8, face=-1, expr="wide", look=(-1, -0.5), space=True, talk=0)
    big(c, "BIGGER THAN", 560, 170, 120, "#ffffff")
    big(c, "JUPITER?!", 1450, 330, 130, "#ffd36b", rot=-4)
    tag(c, 1380, 830, "JUPITER", "#ffd36b", 44)
    vignette(c, 0.4)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    s = skia.Surface(W, H)
    thumb(s.getCanvas())
    img = s.makeImageSnapshot()
    img.save(os.path.join(out, "thumbnail_1920x1080.png"), skia.kPNG)
    img.resize(1280, 720, skia.SamplingOptions(skia.CubicResampler.Mitchell())).save(
        os.path.join(out, "thumbnail_1280x720.png"), skia.kPNG)
