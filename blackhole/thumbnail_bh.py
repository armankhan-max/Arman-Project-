"""YouTube thumbnail for the black-hole video (split screen, curiosity hook). Usage: python thumbnail_bh.py OUTDIR"""
import os
import sys

import skia

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sgfx import *  # noqa: F401,F403


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
    for side in (0, 1):
        c.save()
        clip_half(c, side, x=1010, seed=4, amp=18)
        if side == 0:
            starfield(c, t, drift=(0, 0), streak=0.5)
            black_hole(c, 560, 1180, 430, t)
            glow(c, 560, 600, 600, "#ff6a1a", 0.25)
            figure(c, 540, 640, "kai", "fall", "scared", t, s=1.0, space=True, stretch=0.45, red=0.2)
        else:
            draw_set(c, "bridge", 10)
            tint(c, "#000000", 0.35)
            head_only(c, 1420, 640, "tomas", "wide", t, r=170, face=-1, look=(-1, -0.4))
            head_only(c, 1760, 760, "yuki", "scared", t, r=120, face=-1, look=(-1, -0.4))
        c.restore()
    jagged_split(c, x=1010, seed=4, amp=18, w=22)
    big(c, "SECONDS", 500, 170, 150, "#ff8a3a")
    big(c, "FOREVER", 1460, 170, 150, "#bfe8ff")
    with xf(c, 1010, 520, rot=-8):
        c.drawCircle(0, 0, 105, P("#05060a"))
        c.drawCircle(0, 0, 92, P("#ffd37a"))
        text(c, "?", 0, 50, 140, "#05060a", "Black")
    vignette(c, 0.45)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    s = skia.Surface(W, H)
    c = s.getCanvas()
    thumb(c)
    img = s.makeImageSnapshot()
    img.save(os.path.join(out, "thumbnail_1920x1080.png"), skia.kPNG)
    img.resize(1280, 720, skia.SamplingOptions(skia.CubicResampler.Mitchell())).save(
        os.path.join(out, "thumbnail_1280x720.png"), skia.kPNG)
    print("ok")
