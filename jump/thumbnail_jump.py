"""Thumbnail: one jump, three worlds."""
import os
import sys

import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jgfx import (W, H, C, P, xf, text, world_bg, person, POSE_AIR, POSE_STRAIN, height_tag, line,  # noqa: E402
                  planet_icon, vignette, rrect, arrow)


def draw(c):
    c.clear(C("#000000"))
    panels = [("jupiter", 0.0, POSE_STRAIN, 8, "worried", "8 in"), ("earth", 0.0, POSE_AIR, 60, "happy", "20 in"),
              ("moon", 0.0, POSE_AIR, 470, "laugh", "10 ft")]
    pw = W / 3
    for i, (key, _, pose, lift, expr, lab) in enumerate(panels):
        c.save()
        c.clipRect(skia.Rect(i * pw, 0, (i + 1) * pw, H))
        c.translate(i * pw - (W - pw) / 2, 0)
        world_bg(c, key, 2.0, gy=860)
        person(c, W / 2, 860, pose, "you", expr, 0.0, 0.78, lift=lift, shadow_h=lift, sweat=1.0 if i == 0 else 0)
        c.restore()
        planet_icon(c, i * pw + 90, 110, 55, key, 0.0)
        cx = i * pw + pw / 2
        text(c, lab, cx, (330, 260, 640)[i], 110, "#ffd34d", outline="#0d1220", ow=22)
        text(c, lab, cx, (330, 260, 640)[i], 110, "#ffd34d")
    for k in (1, 2):
        line(c, k * pw, 0, k * pw, H, "#ffffff", 10)
    vignette(c, 0.35)
    rrect(c, 0, H - 200, W, 200, 0, "#0d1220", 0.85)
    text(c, "SAME JUMP. DIFFERENT WORLD.", W / 2, H - 70, 104, "#ffffff")


if __name__ == "__main__":
    s = skia.Surface(W, H)
    draw(s.getCanvas())
    img = s.makeImageSnapshot()
    img.save(os.path.join(HERE, "thumbnail_1920x1080.png"), skia.kPNG)
    s2 = skia.Surface(1280, 720)
    s2.getCanvas().drawImageRect(img, skia.Rect(0, 0, 1280, 720), skia.SamplingOptions(skia.FilterMode.kLinear))
    s2.makeImageSnapshot().save(os.path.join(HERE, "thumbnail_1280x720.png"), skia.kPNG)
    print("wrote thumbnails")
