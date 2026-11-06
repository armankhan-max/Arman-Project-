"""Thumbnail: engraved white-on-black giant Pacific octopus, tiny diver, red arrow, 'IT TASTES YOU..'.

Matches the reference thumbnails ('IT CAN'T SEE YOU' / 'IT HEARS YOU..'): same layout and black
scratchboard/engraving look, with the main word changed to TASTES and the animal changed to an octopus.

Technique: the flat vector octopus is rendered in greys as a shading map, then converted to
engraving with curved hatch lines whose thickness follows brightness, plus stippling and a rim edge.

Usage: python thumbnail_octo.py  -> thumbnail_1280x720.png, thumbnail_1920x1080.png
"""
import math
import os
import sys

import numpy as np
import skia
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ofx  # noqa: E402
from ofx import C, P, xf, line, poly, font, glow, linear, radial, fill_shader, draw_arm  # noqa: E402

SC = 2                      # supersample: draw at 2560x1440
TW, TH = 1280 * SC, 720 * SC
RED = "#ff1a1a"
rng = np.random.default_rng(4)

OX, OY, OS = 1610, 900, 3.1  # octopus head position / scale (in 2x pixels)


def shading_map():
    """Grey render of the octopus (luminance) + alpha mask."""
    ofx.OCTO_DK, ofx.OCTO_LT, ofx.SUCKER = "#151515", "#f2f2f2", "#ffffff"
    s = skia.Surface(TW, TH)
    c = s.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    arms = [
        (205, 1.15, -1.1, -2.8, -1, 0.0), (182, 1.35, -0.2, -2.6, -1, 1.1), (160, 1.1, 0.3, -2.4, -1, 2.3),
        (125, 1.0, 0.5, -2.6, -1, 3.0), (85, 1.0, -0.3, 2.6, 1, 0.6), (55, 1.1, -0.2, 2.4, 1, 1.9),
        (25, 1.1, 0.3, 2.2, 1, 2.8), (-5, 1.0, 0.9, 2.6, 1, 4.0),
    ]
    ofx.octopus(c, OX, OY, OS, 2.0, face=-1, col="#8c8c8c", arms=arms, L=430, mtilt=-40, amp=0.12)
    # one long arm reaching toward the diver, suckers up
    with xf(c, 0, 0):
        draw_arm(c, OX - 120, OY + 210, math.radians(178), 1150, 0.25, -2.4, 0.0, 0.5, 0.06, 0.2, 60, "#8c8c8c", -1,
                 True, ucol="#d0d0d0", scol="#ffffff")
    img = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32) / 255.0
    lum = img[..., :3].mean(axis=2)
    alpha = img[..., 3]
    return lum, alpha


def engrave(lum, alpha):
    h, w = lum.shape
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    # curved hatch field: lines wrap around the body like the reference engravings
    dx, dy = x - OX, y - (OY - 150)
    r = np.sqrt(dx * dx + dy * dy)
    u = 0.55 * r + 0.45 * (y * 0.9 + x * 0.25) + 14 * np.sin(x / 85.0) + 9 * np.sin(y / 60.0 + x / 140.0)
    period = 11.0
    stripe = (u / period) % 1.0
    # 3D roundness: darken toward silhouette edges / overlaps (blurred-mask AO) and light from upper-left
    ao = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(38))) / 255.0
    ao = np.clip((ao - 0.35) / 0.6, 0, 1)
    light = np.clip(1.15 - 0.55 * ((x / w) * 0.35 + (y / h) * 0.9), 0.35, 1.2)
    tone = np.clip((lum - 0.06) / 0.85, 0, 1) * (0.25 + 0.85 * ao) * light
    tone = np.clip(tone, 0, 1) ** 1.25
    lines = (stripe < tone * 0.82).astype(np.float32)
    # cross-hatch in the darkest areas is left black; stipple dots add texture
    dots = (rng.random((h, w)) < 0.045 * tone ** 1.5).astype(np.float32)
    texture = np.clip(lines + dots, 0, 1)
    # small dark pits (skin papillae)
    pits = rng.random((h, w)) < 0.0009
    pits_img = Image.fromarray((pits * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))
    texture *= 1 - (np.asarray(pits_img) > 0) * (tone > 0.35)
    # rim/edge highlight from the mask
    m = Image.fromarray((alpha * 255).astype(np.uint8))
    er = np.asarray(m.filter(ImageFilter.MinFilter(5))).astype(np.float32) / 255
    edge = np.clip(alpha - er, 0, 1)
    # bright, clean suckers: keep near-white luminance as solid white
    solid = (lum > 0.93).astype(np.float32) * np.clip(light, 0, 1)
    out = np.clip(texture * 0.95 + edge + solid, 0, 1) * alpha
    return out


def background():
    s = skia.Surface(TW, TH)
    c = s.getCanvas()
    c.clear(C("#000000"))
    for _ in range(900):
        xx, yy = rng.uniform(0, TW), rng.uniform(0, TH)
        c.drawCircle(xx, yy, rng.uniform(0.6, 2.2), P("#ffffff", a=float(rng.uniform(0.05, 0.35))))
    return s


def overlay(c):
    # sense ripples: dashed arcs spreading from the octopus toward the diver
    for i in range(7):
        rr = 260 + i * 95
        pth = skia.Path()
        pth.addArc(skia.Rect(OX - 470 - rr, OY + 120 - rr, OX - 470 + rr, OY + 120 + rr), 150, 70)
        p = P("#ffffff", 3, 0.55 - i * 0.06)
        p.setPathEffect(skia.DashPathEffect.Make([14, 10], 0))
        c.drawPath(pth, p)
    # diver with torch (bottom-left), small like the references
    dx, dy = 250, 1150
    with xf(c, dx, dy, s=0.62, rot=-8):
        beam = poly([(150, 18), (150, 2), (620, -120), (620, 160)])
        c.drawPath(beam, skia.Paint(AntiAlias=True, Shader=linear(150, 0, 620, 0, [("#ffffff", 0.75), ("#ffffff", 0)])))
        glow(c, 150, 10, 60, "#ffffff", 0.9)
    ofx.diver(c, dx, dy, 0.62, 0.3, face=1, torch=True, beam=0.0, accent="#9a9a9a", fin="#f0f0f0",
              bubbles_on=False, rot=-8, suit="#e6e6e6", tank="#ffffff", mask="#ffffff")
    for i in range(6):
        c.drawCircle(dx + 60 + i * 6, dy - 40 - i * 34, 5 + i, P("#ffffff", 2.5, 0.8))
    # red arrow from the headline down to the diver
    arr = skia.Path()
    arr.moveTo(740, 320)
    arr.cubicTo(640, 520, 470, 760, 390, 1010)
    c.drawPath(arr, P(RED, 22))
    ang = math.atan2(1010 - 760, 390 - 470)
    tip = (380, 1050)
    c.drawPath(poly([tip, (tip[0] - 70 * math.cos(ang - 0.5), tip[1] - 70 * math.sin(ang - 0.5)),
                     (tip[0] - 70 * math.cos(ang + 0.5), tip[1] - 70 * math.sin(ang + 0.5))]), P(RED))
    c.drawPath(poly([tip, (tip[0] - 82 * math.cos(ang - 0.48), tip[1] - 82 * math.sin(ang - 0.48))], close=False),
               P(RED, 22))
    c.drawPath(poly([tip, (tip[0] - 82 * math.cos(ang + 0.48), tip[1] - 82 * math.sin(ang + 0.48))], close=False),
               P(RED, 22))
    # headline: 'IT TASTES' white + 'YOU..' red, heavy caps with a dark outline
    f = font(212, "Black")
    x, y = 70, 270
    for word, col in (("IT TASTES ", "#ffffff"), ("YOU..", RED)):
        c.drawString(word, x, y, f, P("#000000", 26))
        c.drawString(word, x, y, f, P(col))
        x += f.measureText(word)


def eye(c):
    ex, ey, r = OX + 36 * OS, OY - 38 * OS, 27 * OS     # face=-1 mirrors the local x
    ex = OX - 36 * OS
    c.drawCircle(ex, ey, r * 1.45, P("#000000"))
    c.drawCircle(ex, ey, r * 1.45, P("#ffffff", 5))
    c.drawCircle(ex, ey, r, P("#f4f4f4"))
    for i in range(48):
        a = i * 2 * math.pi / 48
        line(c, ex + math.cos(a) * r * 0.45, ey + math.sin(a) * r * 0.45, ex + math.cos(a) * r * 0.95,
             ey + math.sin(a) * r * 0.95, "#8a8a8a", 2.5)
    ph = r * 0.34
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(ex - r * 0.72, ey - ph / 2, ex + r * 0.72, ey + ph / 2), ph / 2, ph / 2),
                P("#050505"))
    c.drawCircle(ex - r * 0.35, ey - r * 0.4, r * 0.14, P("#ffffff"))


def main():
    lum, alpha = shading_map()
    eng = engrave(lum, alpha)
    bg = background()
    base = bg.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32) / 255.0
    rgb = base[..., :3] * (1 - alpha[..., None]) + eng[..., None] * np.array([0.97, 0.97, 0.95])
    canvas_img = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    rgba = np.dstack([canvas_img, np.full(canvas_img.shape[:2], 255, np.uint8)])
    s = skia.Surface(TW, TH)
    c = s.getCanvas()
    c.drawImage(skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType), 0, 0)
    eye(c)
    overlay(c)
    out = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    im = Image.fromarray(out[..., :3])
    im.resize((1920, 1080), Image.LANCZOS).save(os.path.join(HERE, "thumbnail_1920x1080.png"))
    im.resize((1280, 720), Image.LANCZOS).save(os.path.join(HERE, "thumbnail_1280x720.png"))
    print("wrote thumbnails")


if __name__ == "__main__":
    main()
