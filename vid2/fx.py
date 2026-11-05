"""Fire, embers, smoke, glow and burning-paper helpers."""
import math
import random
import numpy as np
import skia
from engine3d import v3, col, clamp, INK


def _flame_path(x, h, w, sway):
    p = skia.Path()
    p.moveTo(x - w, 0)
    p.cubicTo(x - w * 1.1, -h * 0.45, x + sway - w * 0.4, -h * 0.7, x + sway, -h)
    p.cubicTo(x + sway + w * 0.4, -h * 0.7, x + w * 1.1, -h * 0.45, x + w, 0)
    p.close()
    return p


def draw_fire(c, t, k=1.0, seed=0):
    """local units: base at y=0, width ~[-50,50], height up to ~100*k."""
    rnd = random.Random(seed)
    # glow
    g = skia.GradientShader.MakeRadial((0, -30 * k), 95 * k, [skia.Color(255, 150, 40, 70), skia.Color(255, 120, 30, 0)])
    c.drawCircle(0, -30 * k, 95 * k, skia.Paint(AntiAlias=True, Shader=g, BlendMode=skia.BlendMode.kPlus))
    layers = [((255, 70, 20), (255, 150, 30), 1.0, 7), ((255, 140, 30), (255, 210, 80), 0.75, 6),
              ((255, 220, 110), (255, 250, 210), 0.45, 4)]
    for li, (c0, c1, hk, n) in enumerate(layers):
        for i in range(n):
            ph = rnd.uniform(0, 6.28)
            fr = rnd.uniform(5, 9)
            x = (i - (n - 1) / 2) * 13 * hk + math.sin(t * 3 + ph) * 3
            h = (55 + 45 * (0.5 + 0.5 * math.sin(t * fr + ph))) * hk * k
            w = (13 + rnd.uniform(-3, 4)) * (0.7 + 0.3 * hk)
            sway = math.sin(t * fr * 0.7 + ph) * 10 * hk
            sh = skia.GradientShader.MakeLinear([(0, 0), (0, -h)], [col(c1 + (255,)), col(c0 + (0,))])
            c.drawPath(_flame_path(x, h, w, sway), skia.Paint(AntiAlias=True, Shader=sh, Alphaf=0.92 if li < 2 else 0.75))


def fire(sc, pos, size, t, k=1.0, seed=0, depth_bias=-0.05):
    if k <= 0.01:
        return
    sc.billboard(v3(*pos), size, lambda c, t=t, k=k, seed=seed: draw_fire(c, t, k, seed), depth_bias=depth_bias)
    glow(sc, (pos[0], pos[1] + size * 0.3 * k, pos[2]), size * 1.6 * k, (255, 140, 50), 45)


def glow(sc, pos, radius, color=(255, 150, 60), alpha=80):
    cam = sc.cam
    p = cam.project(pos)
    if p is None:
        return
    x, y, z = p
    r = cam.f * radius / z

    def draw(c):
        g = skia.GradientShader.MakeRadial((x, y), r, [skia.Color(*color, alpha), skia.Color(*color, 0)])
        c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Shader=g, BlendMode=skia.BlendMode.kPlus))
    sc.items.append((5, 0.0, draw))


def embers(sc, base, t, n=24, spread=0.4, height=2.5, speed=0.5, seed=1, size=0.035):
    rnd = random.Random(seed)
    bx, by, bz = base
    for i in range(n):
        ph = rnd.random()
        age = (t * speed + ph) % 1.0
        x = bx + rnd.uniform(-spread, spread) + math.sin(t * 2 + i) * 0.15 * age
        z = bz + rnd.uniform(-spread, spread)
        y = by + age * height
        a = int(255 * (1 - age) * (0.6 + 0.4 * math.sin(t * 20 + i)))
        if a <= 5:
            continue
        sc.billboard(v3(x, y, z), size, lambda c, a=a: c.drawCircle(0, -50, 50, skia.Paint(
            AntiAlias=True, Color=skia.Color(255, 190, 80, a), BlendMode=skia.BlendMode.kPlus)), depth_bias=-0.1, layer=1)


def smoke(sc, base, t, n=8, height=4.0, speed=0.25, seed=2, size=0.6, alpha=110, color=(200, 200, 205)):
    rnd = random.Random(seed)
    bx, by, bz = base
    for i in range(n):
        ph = i / n
        age = (t * speed + ph) % 1.0
        x = bx + math.sin(age * 4 + i) * 0.3 * age
        y = by + age * height
        s = size * (0.5 + 1.5 * age)
        a = int(alpha * math.sin(math.pi * age))
        sc.billboard(v3(x, y, bz + rnd.uniform(-0.1, 0.1)), s, lambda c, a=a: c.drawCircle(0, -50, 50, skia.Paint(
            AntiAlias=True, Color=skia.Color(*color, a))), depth_bias=0.05)


def burnt(tex, w, h, p, seed=0):
    """wrap a texture: burning from the top edge down. p in 0..1 (0 = intact)."""
    if p <= 0:
        return tex
    rnd = random.Random(seed)
    pts = [(x, rnd.uniform(-0.06, 0.06)) for x in np.linspace(0, 1, 14)]

    def f(c):
        yb = -0.1 * h + p * h * 1.2
        edge = skia.Path()
        edge.moveTo(0, h)
        edge.lineTo(0, yb)
        for x, d in pts:
            edge.lineTo(x * w, yb + d * h)
        edge.lineTo(w, h)
        edge.close()
        c.save()
        c.clipPath(edge, doAntiAlias=True)
        tex(c)
        # charred band
        sh = skia.GradientShader.MakeLinear([(0, yb - 0.02 * h), (0, yb + 0.12 * h)],
                                            [skia.Color(20, 10, 5, 255), skia.Color(20, 10, 5, 0)])
        c.drawRect(skia.Rect(0, 0, w, h), skia.Paint(Shader=sh))
        c.restore()
        # glowing edge
        gl = skia.Path()
        for i, (x, d) in enumerate(pts):
            (gl.moveTo if i == 0 else gl.lineTo)(x * w, yb + d * h)
        c.drawPath(gl, skia.Paint(AntiAlias=True, Color=skia.Color(255, 160, 40), Style=skia.Paint.kStroke_Style,
                                  StrokeWidth=h * 0.03, BlendMode=skia.BlendMode.kPlus))
    return f


def warp(t, segs):
    """time remap for slow motion: segs = [(t0, t1, speed)] -> animation time."""
    a = t
    for t0, t1, s in segs:
        if t > t0:
            a -= (min(t, t1) - t0) * (1 - s)
    return a
