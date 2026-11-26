"""Thumbnail in black & white scratchboard-engraving style: giant planet vs tiny Jupiter.
The planets are rendered as real line engravings: a shaded, turbulent planet is computed per pixel
(numpy), then turned into flowing ink lines whose thickness follows the brightness.
Usage: python thumbnail_doc.py OUTDIR"""
import math
import os
import sys

import numpy as np
import skia

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cosmos import W, H, P, font  # noqa: E402

rng = np.random.default_rng(5)


def value_noise(shape, scale, seed):
    r = np.random.default_rng(seed)
    gh, gw = int(shape[0] / scale) + 3, int(shape[1] / scale) + 3
    g = r.random((gh, gw))
    y = np.arange(shape[0]) / scale
    x = np.arange(shape[1]) / scale
    y0, x0 = y.astype(int), x.astype(int)
    fy, fx = y - y0, x - x0
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0]
    b = g[y0][:, x0 + 1]
    c = g[y0 + 1][:, x0]
    d = g[y0 + 1][:, x0 + 1]
    top = a + (b - a) * fx[None, :]
    bot = c + (d - c) * fx[None, :]
    return top + (bot - top) * fy[:, None]


def fbm(shape, scale, seed, oct=5):
    out = np.zeros(shape)
    amp, tot = 1.0, 0.0
    for o in range(oct):
        out += amp * value_noise(shape, max(2, scale / 2 ** o), seed + o)
        tot += amp
        amp *= 0.5
    return out / tot


def engrave_planet(img, cx, cy, r, seed, line_px, storms, band_freq=11.0, light=(-0.8, -0.5, 0.35)):
    """Adds an engraved planet (white ink on black) into img (float HxW, 0..1)."""
    HH, WW = img.shape
    x0, x1 = max(0, int(cx - r - 2)), min(WW, int(cx + r + 2))
    y0, y1 = max(0, int(cy - r - 2)), min(HH, int(cy + r + 2))
    if x1 <= x0 or y1 <= y0:
        return
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(float)
    u, v = (xs - cx) / r, (ys - cy) / r
    rr = u * u + v * v
    inside = rr < 1
    z = np.sqrt(np.clip(1 - rr, 0, 1))
    lx, ly, lz = light
    n = math.sqrt(lx * lx + ly * ly + lz * lz)
    lam = np.clip((u * lx + v * ly + z * lz) / n, 0, 1)
    shp = u.shape
    sc = max(8.0, r / 6)
    turb = fbm(shp, sc, seed) - 0.5
    turb2 = fbm(shp, sc / 3, seed + 20) - 0.5
    # latitude with turbulence; storms swirl it
    lat = v + 0.06 * turb + 0.02 * turb2
    lon = u / np.maximum(z, 0.15)
    storm_dark = np.zeros(shp)
    for (su, sv, srad, spin) in storms:
        du, dv = (u - su) / 1.6, v - sv
        d = np.sqrt(du * du + dv * dv) / srad
        w = np.exp(-d * d * 1.6)
        ang = spin * w * 5.0
        lat = lat + w * (np.sin(np.arctan2(dv, du) + ang) * d * srad * 0.9 - dv * 0.9)
        storm_dark += w * (0.5 + 0.5 * np.sin(d * 18))
    bands = 0.5 + 0.5 * np.sin(lat * band_freq * math.pi + 1.3 * np.sin(lat * 23 + 1.0))
    bands = 0.55 + 0.45 * bands + 0.15 * turb2
    bright = (0.0 + 1.15 * lam ** 1.7) * bands * (1 - 0.35 * np.clip(storm_dark, 0, 1))
    bright = np.clip(bright, 0, 1)
    # engraving: lines follow the warped latitude; thickness ~ brightness
    phase = (lat * r / line_px + 0.8 * turb2) % 1.0
    tri = np.abs(phase - 0.5) * 2  # 0 at line centre .. 1 between lines
    ink = (tri < bright * 0.95).astype(float)
    # soften + fine stipple grain
    grain = rng.random(shp)
    ink = np.where(grain < 0.04 * bright, 1.0, ink)
    ink = np.where(grain > 1 - 0.05 * (1 - bright), 0.0, ink)
    ink *= np.clip(0.35 + 0.8 * bright, 0, 1)
    # rim highlight
    rim = np.clip((rr - 0.985) / 0.015, 0, 1) * (rr < 1) * np.clip(lam * 2 + 0.2, 0, 1)
    out = np.where(inside, np.maximum(ink, rim * 0.8), 0)
    reg = img[y0:y1, x0:x1]
    img[y0:y1, x0:x1] = np.where(inside, out, reg)


SS = 2


def build_art():
    img = np.zeros((H * SS, W * SS))
    # stars
    for _ in range(900):
        x, y = rng.integers(2, W * SS - 4), rng.integers(2, H * SS - 4)
        sz = 2 if rng.random() < 0.85 else 4
        img[y:y + sz, x:x + sz] = rng.uniform(0.4, 1.0)
    # giant planet (right), tiny Jupiter (left)
    engrave_planet(img, 1600 * SS, 790 * SS, 700 * SS, seed=3, line_px=4.0 * SS,
                   storms=[(-0.42, 0.22, 0.16, 1.0), (-0.1, -0.25, 0.07, -1.0), (-0.55, 0.55, 0.06, 1.0)],
                   band_freq=9.0)
    engrave_planet(img, 300 * SS, 770 * SS, 64 * SS, seed=9, line_px=1.9 * SS, storms=[(0.25, 0.32, 0.2, 1.0)],
                   band_freq=6.0)
    return img


def thumb(path_png):
    art = build_art()
    rgb = (np.clip(art, 0, 1) * 255).astype(np.uint8)
    rgba = np.dstack([rgb, rgb, rgb, np.full_like(rgb, 255)])
    s = skia.Surface(W, H)
    c = s.getCanvas()
    c.drawImageRect(skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType), skia.Rect(0, 0, W, H),
                    skia.SamplingOptions(skia.CubicResampler.Mitchell()))
    # concentric arcs radiating from the giant toward tiny Jupiter
    for k in range(7):
        R = 120 + k * 62
        pth = skia.Path()
        pth.addArc(skia.Rect(900 - R, 770 - R, 900 + R, 770 + R), 145, 70)
        p = P("#ffffff", max(1.2, 3.4 - k * 0.35), 0.85 - k * 0.09)
        if k >= 5:
            p.setPathEffect(skia.DashPathEffect.Make([5, 9], 0))
        c.drawPath(pth, p)
    # red hand-drawn arrow
    pth = skia.Path()
    pth.moveTo(660, 270)
    pth.cubicTo(520, 360, 360, 470, 318, 640)
    c.drawPath(pth, P("#ff1414", 15))
    ang = math.atan2(640 - 470, 318 - 360)
    hx, hy = 312, 684
    head = skia.Path()
    head.moveTo(hx, hy)
    head.lineTo(hx - math.cos(ang - 0.45) * 72, hy - math.sin(ang - 0.45) * 72)
    head.lineTo(hx - math.cos(ang + 0.45) * 72, hy - math.sin(ang + 0.45) * 72)
    head.close()
    c.drawPath(head, P("#ff1414"))
    # headline
    f = font(175, "Black")
    x, y = 46, 205
    for s_, col in (("THIS IS ", "#ffffff"), ("JUPITER..", "#ff1414")):
        c.drawString(s_, x + 5, y + 8, f, P("#000000", a=0.9))
        c.drawString(s_, x, y, f, P(col))
        x += f.measureText(s_)
    img = s.makeImageSnapshot()
    return img


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    img = thumb(None)
    img.save(os.path.join(out, "thumbnail_1920x1080.png"), skia.kPNG)
    img.resize(1280, 720, skia.SamplingOptions(skia.CubicResampler.Mitchell())).save(
        os.path.join(out, "thumbnail_1280x720.png"), skia.kPNG)
