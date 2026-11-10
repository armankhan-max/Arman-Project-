"""Thumbnail: Moon / Mars / mystery world (Enceladus)."""
import os
import sys

import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jgfx import (W, H, C, P, text, world_bg, person, POSE_AIR, POSE_FLOAT, line, planet_icon,  # noqa: E402
                  vignette, glow)


def label(c, s, x, y, size, col, outline="#0d1220"):
    text(c, s, x, y, size, col, outline=outline, ow=size * 0.2)
    text(c, s, x, y, size, col)


def draw(c):
    c.clear(C("#000000"))
    pw = W / 3
    panels = [("moon", 0.8, 330, "tired", "MOON", "10 FT"), ("mars", 0.8, 240, "squint", "MARS", "4 FT"),
              ("enceladus", 0.26, 420, "shock", "???", "40 METERS")]
    for i, (key, s, lift, expr, top, bot) in enumerate(panels):
        c.save()
        c.clipRect(skia.Rect(i * pw, 0, (i + 1) * pw, H))
        c.translate(i * pw - (W - pw) / 2, 0)
        world_bg(c, key, 2.0, gy=900)
        if key == "moon":
            glow(c, W / 2 + 180, 190, 200, "#5fb0ff", 0.35)
            planet_icon(c, W / 2 + 180, 190, 70, "earth", 0.0)
        person(c, W / 2, 900, POSE_AIR if i < 2 else POSE_FLOAT, "astro", expr, 0.0, s, lift=lift, shadow_h=lift)
        if key == "enceladus":
            glow(c, W / 2, 600, 420, "#8fd0ff", 0.35)
            for gx in (W / 2 - 200, W / 2 + 190, W / 2 + 60):
                for k in range(24):
                    ph = k / 24
                    c.drawCircle(gx + 25 * ph * (1 if gx > W / 2 else -1), 900 - ph * 760, 8 + 26 * ph,
                                 P("#dff0ff", a=0.5 * (1 - ph)))
        c.restore()
        cx = i * pw + pw / 2
        if i < 2:
            label(c, top, cx, 140, 120, "#ffffff")
        else:
            glow(c, cx, 110, 260, "#ff2a2a", 0.55)
            label(c, top, cx, 175, 190, "#ff3030", "#3a0000")
        label(c, bot, cx, 1020, 110 if i < 2 else 96, "#ffd34d")
    for k in (1, 2):
        line(c, k * pw, 0, k * pw, H, "#ffffff", 6)
    vignette(c, 0.45)


if __name__ == "__main__":
    s = skia.Surface(W, H)
    draw(s.getCanvas())
    img = s.makeImageSnapshot()
    img.save(os.path.join(HERE, "thumbnail_1920x1080.png"), skia.kPNG)
    s2 = skia.Surface(1280, 720)
    s2.getCanvas().drawImageRect(img, skia.Rect(0, 0, 1280, 720), skia.SamplingOptions(skia.FilterMode.kLinear))
    s2.makeImageSnapshot().save(os.path.join(HERE, "thumbnail_1280x720.png"), skia.kPNG)
