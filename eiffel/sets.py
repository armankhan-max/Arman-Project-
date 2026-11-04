"""3D set builders. Each takes a Scene and adds geometry."""
import math
import random
import numpy as np
import skia
from engine3d import v3, rgb, norm, clamp
import tex as T

# ------------------------------------------------------------------ Eiffel tower
TOWER_SEG = [  # (y, half-width)
    (0.0, 9.0), (11.0, 5.6), (22.0, 3.4), (34.0, 1.9), (46.0, 0.9), (54.0, 0.45)]


def tower(sc, base=(0, 0, 0), s=1.0, rust=0.0, tag=None):
    bx, by, bz = base
    for i in range(len(TOWER_SEG) - 1):
        (y0, w0), (y1, w1) = TOWER_SEG[i], TOWER_SEG[i + 1]
        y0, y1, w0, w1 = y0 * s, y1 * s, w0 * s, w1 * s
        for k in range(4):
            a0 = k * math.pi / 2 + math.pi / 4
            a1 = a0 + math.pi / 2
            r0, r1 = w0 * math.sqrt(2), w1 * math.sqrt(2)
            p = [v3(bx + r0 * math.cos(a0), by + y0, bz + r0 * math.sin(a0)),
                 v3(bx + r0 * math.cos(a1), by + y0, bz + r0 * math.sin(a1)),
                 v3(bx + r1 * math.cos(a1), by + y1, bz + r1 * math.sin(a1)),
                 v3(bx + r1 * math.cos(a0), by + y1, bz + r1 * math.sin(a0))]
            # texture: v=0 at top. pts order maps (0,0)->p3,(tw,0)->p2,(tw,th)->p1,(0,th)->p0
            if i == 0:
                t = T.arch_face(rust)
                sc.quad_tex4([p[3], p[2], p[1], p[0]], t, 512, 256, outline=False, shade=True)
            else:
                t = T.lattice(6, rust)
                sc.quad_tex4([p[3], p[2], p[1], p[0]], t, 256, 256, outline=False, shade=True)
    # platforms
    for y, w in (TOWER_SEG[1], TOWER_SEG[2]):
        sc.box((bx, by + y * s, bz), (w * 2.25 * s, 0.8 * s, w * 2.25 * s), rgb('#6e4a38'), top=rgb('#8a5e46'))
    sc.box((bx, by + 46 * s, bz), (2.2 * s, 1.4 * s, 2.2 * s), rgb('#6e4a38'))
    sc.poly([v3(bx - 0.08 * s, by + 54 * s, bz), v3(bx + 0.08 * s, by + 54 * s, bz),
             v3(bx, by + 60 * s, bz)], rgb('#5a3a2a'), outline=False, normal=None)


def ground(sc, tex_fn, size=200, rep=20.0, y=0.0, center=(0, 0), layer=0, tw=256, th=128):
    cx, cz = center
    # tile in a grid so texture repeats
    n = 6
    step = size / n
    for i in range(n):
        for j in range(n):
            x0, z0 = cx - size / 2 + i * step, cz - size / 2 + j * step
            O = v3(x0, y, z0)
            tile_tex = _repeat(tex_fn, tw, th, int(rep / n) or 1)
            sc.quad_tex(O, v3(step, 0, 0), v3(0, 0, step), tile_tex, tw * (int(rep / n) or 1), th * (int(rep / n) or 1),
                        layer=layer, outline=False, shade=False)


_rep_cache = {}


def _repeat(tex_fn, tw, th, k):
    key = (id(tex_fn), k)
    if key not in _rep_cache:
        from engine3d import picture
        def f(c):
            for i in range(k):
                for j in range(k):
                    c.save()
                    c.translate(i * tw, j * th)
                    tex_fn(c)
                    c.restore()
        pic = picture(tw * k, th * k, f)
        _rep_cache[key] = lambda canvas: canvas.drawPicture(pic)
    return _rep_cache[key]


def paris(sc, rust=0.0, lit=False, tower_at=(0, 0, 40), tower_s=1.0, buildings=True, ground_tex='cobble'):
    g = T.cobble() if ground_tex == 'cobble' else T.grass()
    ground(sc, g, size=240, rep=60, center=(0, 30))
    # grass lawn (Champ de Mars) in front of tower
    tower(sc, tower_at, tower_s, rust)
    if buildings:
        rnd = random.Random(4)
        for side in (-1, 1):
            for k in range(7):
                z = -10 + k * 14
                x = side * (24 + rnd.uniform(0, 4))
                h = rnd.uniform(14, 18)
                d = 12
                # facade facing the street (towards x=0)
                O = v3(x, 0, z - 6)
                fac = T.haussmann(k + (side > 0), lit)
                sc.quad_tex4([v3(x, h, z - 6), v3(x, h, z + 6), v3(x, 0, z + 6), v3(x, 0, z - 6)] if side < 0 else
                             [v3(x, h, z + 6), v3(x, h, z - 6), v3(x, 0, z - 6), v3(x, 0, z + 6)],
                             fac, 512, 640, outline=True, lw=2)
                sc.box((x + side * d / 2, h / 2, z), (d - 0.05, h - 0.05, 11.9), rgb('#d9c9a8'), sides=('top',))


def morris_column(sc, pos, poster=True):
    x, y, z = pos
    sc.cyl((x, y, z), 0.7, 3.2, rgb('#2f5a3a'), seg=16, top=rgb('#2f5a3a'))
    sc.cyl((x, y + 3.2, z), 0.85, 0.5, rgb('#2f5a3a'), seg=16, r2=0.2)
    if poster:
        sc.quad_tex(v3(x - 0.55, y + 0.6, z - 0.72), v3(1.1, 0, 0), v3(0, 2.2, 0), lambda c: (c.save(), c.scale(1, -1), c.translate(0, -720), T.morris_poster()(c), c.restore()), 520, 720, depth_bias=-0.2)


def lamp_post(sc, pos, h=4.2, on=False):
    x, y, z = pos
    sc.box((x, y + h / 2, z), (0.12, h, 0.12), rgb('#2a2a30'))
    sc.box((x, y + h + 0.25, z), (0.4, 0.5, 0.4), rgb('#f6dc8a') if on else rgb('#cfd8e0'), top=rgb('#2a2a30'))


# ------------------------------------------------------------------ rooms
def room(sc, w=10, d=10, h=4, floor=None, wall=None, wall2=None, z0=-4, cx=0, ceiling=False, back=True, sides=True,
         floor_col=rgb('#8a5a3a'), wall_col=rgb('#a83a3a')):
    x0, x1 = cx - w / 2, cx + w / 2
    z1 = z0 + d
    if floor:
        sc.quad_tex(v3(x0, 0, z0), v3(w, 0, 0), v3(0, 0, d), _repeat(floor, 256, 256, 4), 1024, 1024, layer=0,
                    outline=False, shade=False)
    else:
        sc.poly([v3(x0, 0, z0), v3(x1, 0, z0), v3(x1, 0, z1), v3(x0, 0, z1)], floor_col, layer=0, normal=(0, 1, 0), outline=False)
    wt = _repeat(wall, 256, 256, 3) if wall else None
    if back:
        if wt:
            sc.quad_tex(v3(x0, h, z1), v3(w, 0, 0), v3(0, -h, 0), wt, 768, 768 * h / w if False else 768, layer=0, outline=False)
        else:
            sc.poly([v3(x0, 0, z1), v3(x1, 0, z1), v3(x1, h, z1), v3(x0, h, z1)], wall_col, layer=0, normal=(0, 0, -1), outline=False)
    if sides:
        for xs, nx in ((x0, 1), (x1, -1)):
            if wt:
                sc.quad_tex(v3(xs, h, z0), v3(0, 0, d), v3(0, -h, 0), wt, 768, 768, layer=0, outline=False)
            else:
                sc.poly([v3(xs, 0, z0), v3(xs, 0, z1), v3(xs, h, z1), v3(xs, h, z0)], wall_col, layer=0, normal=(nx, 0, 0), outline=False)
    # baseboards
    sc.poly([v3(x0, 0, z1 - 0.02), v3(x1, 0, z1 - 0.02), v3(x1, 0.25, z1 - 0.02), v3(x0, 0.25, z1 - 0.02)], rgb('#3a2018'), layer=0, normal=(0, 0, -1), outline=False)
    if ceiling:
        sc.poly([v3(x0, h, z0), v3(x1, h, z0), v3(x1, h, z1), v3(x0, h, z1)], rgb('#efe6d4'), layer=0, normal=(0, -1, 0), outline=False)


def table(sc, center, w=4.0, d=1.6, h=0.78, color=rgb('#6b3f22'), top=rgb('#7d4b2a'), cloth=None):
    x, y, z = center
    sc.box((x, y + h, z), (w, 0.08, d), color, top=cloth or top)
    for sx in (-1, 1):
        for sz in (-1, 1):
            sc.box((x + sx * (w / 2 - 0.12), y + h / 2, z + sz * (d / 2 - 0.12)), (0.09, h, 0.09), rgb('#4a2a16'))


def chair(sc, pos, back=(0, 1), color=rgb('#7a2a32')):
    x, y, z = pos
    sc.box((x, y + 0.45, z), (0.5, 0.08, 0.5), rgb('#5a3418'), top=color)
    bx, bz = back
    sc.box((x + bx * 0.24, y + 0.9, z + bz * 0.24), (0.5 if bz else 0.07, 0.9, 0.07 if bz else 0.5), color)
    for sx in (-1, 1):
        for sz in (-1, 1):
            sc.box((x + sx * 0.2, y + 0.22, z + sz * 0.2), (0.05, 0.45, 0.05), rgb('#4a2a16'))


def wall_window(sc, x0, y0, z, w, h, night=False, rain=False, layer=0, curtains=0.0, curtain_col=rgb('#d4a64a')):
    sc.quad_tex(v3(x0, y0 + h, z - 0.03), v3(w, 0, 0), v3(0, -h, 0), T.window_tex(night, rain), 400, 600,
                layer=layer, depth_bias=-0.05, lw=4, shade=False)
    # curtains slide from sides (0 open .. 1 closed)
    cw = w * 0.25 + (w * 0.5 - w * 0.25) * curtains
    for side in (0, 1):
        xa = x0 - 0.3 if side == 0 else x0 + w + 0.3 - cw - 0.3
        sc.poly([v3(xa, y0 - 0.3, z - 0.08), v3(xa + cw + 0.3, y0 - 0.3, z - 0.08),
                 v3(xa + cw + 0.3, y0 + h + 0.35, z - 0.08), v3(xa, y0 + h + 0.35, z - 0.08)],
                curtain_col, layer=layer, normal=(0, 0, -1), depth_bias=-0.1)


def frame_pic(sc, x, y, z, w, h, color=rgb('#d9b24a')):
    sc.poly([v3(x, y, z - 0.03), v3(x + w, y, z - 0.03), v3(x + w, y + h, z - 0.03), v3(x, y + h, z - 0.03)],
            color, layer=0, normal=(0, 0, -1), depth_bias=-0.05)
    sc.poly([v3(x + 0.1, y + 0.1, z - 0.05), v3(x + w - 0.1, y + 0.1, z - 0.05), v3(x + w - 0.1, y + h - 0.1, z - 0.05),
             v3(x + 0.1, y + h - 0.1, z - 0.05)], rgb('#5f8a6a'), layer=0, normal=(0, 0, -1), depth_bias=-0.06)


def chandelier(sc, pos, glow=1.0):
    x, y, z = pos
    sc.box((x, y + 0.5, z), (0.04, 1.0, 0.04), rgb('#c9a24a'))
    sc.cyl((x, y - 0.1, z), 0.7, 0.2, rgb('#d9b24a'), seg=12, r2=0.3)
    for k in range(6):
        a = k * math.pi / 3
        px, pz = x + 0.65 * math.cos(a), z + 0.65 * math.sin(a)
        sc.box((px, y + 0.18, pz), (0.08, 0.2, 0.08), rgb('#fff6d0'))
