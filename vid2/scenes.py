"""Shot list: 'Hell Bank Notes' (THINK ODD). Global-time shots keyed to words.json."""
import json
import math
import random
import numpy as np
import skia
from engine3d import (Camera, Scene, v3, rgb, clamp, ease, ease_out, ease_in, ease_back, lerp, W, H, INK, col)
from chars import draw_char
import sets as S
import tex as T
import tex2 as T2
import fx

WORDS = json.load(open(__file__.replace('scenes.py', 'words.json')))
DUR = 57.05

DAD = dict(body=rgb('#2c4470'), hair='side', hair_col=(28, 26, 32), pants=(48, 48, 58))
MOM = dict(body=rgb('#2e8b6a'), hair='bun', hair_col=(28, 26, 32), pants=(40, 40, 50))
KID = dict(body=rgb('#f2b632'), hair='side', hair_col=(28, 26, 32))
GRANDPA = dict(body=rgb('#c9a227'), suit=True, tie=rgb('#a01c1c'), hair='combover', hair_col=(235, 235, 235),
               stache='walrus', stache_col=(240, 240, 240), beard=True)
SHOPKEEP = dict(body=rgb('#7a3b6b'), hair='bun', hair_col=(205, 205, 210), glasses=True)
FAMS = [dict(body=rgb(h), hair=hr, hair_col=(28, 26, 32)) for h, hr in
        [('#a8443a', 'side'), ('#3a6aa8', 'bun'), ('#6a8a3a', 'side'), ('#8a3a8a', 'bun'), ('#c07a2a', 'side'),
         ('#3a8a8a', 'bun')]]


# ------------------------------------------------------------------ helpers
def blink(t, seed=0, eyes='dot'):
    return 'shut' if (t + seed * 1.37) % 3.1 < 0.09 else eyes


def bob(t, seed=0, amt=0.012):
    return 1 + amt * math.sin(t * 4.2 + seed)


def char(sc, look, pos, pose, h=1.75, shadow=True, depth_bias=0.0, layer=1):
    pos = v3(*pos)
    if shadow:
        sc.shadow((pos[0], pos[1], pos[2]), rx=0.3 * h / 1.75, rz=0.19 * h / 1.75)
    sc.billboard(pos, h, lambda c, look=look, pose=pose: draw_char(c, look, pose), depth_bias=depth_bias, layer=layer)


def catmull(p0, p1, p2, p3, u):
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


def _vals(k):
    return np.concatenate([np.array(k[1], float), np.array(k[2], float),
                           [k[3]], [k[4] if len(k) > 4 and not isinstance(k[4], str) else 0.0]])


def path(keys, t, eased=False):
    """monotone (no-overshoot) time-aware cubic through camera keys."""
    ts = [k[0] for k in keys]
    P = [_vals(k) for k in keys]
    n = len(keys)
    if t <= ts[0]:
        v = P[0]
    elif t >= ts[-1]:
        v = P[-1]
    else:
        i = max(j for j in range(n - 1) if ts[j] <= t)
        h = ts[i + 1] - ts[i]
        u = (t - ts[i]) / h
        mode = keys[i + 1][5] if len(keys[i + 1]) > 5 else None
        if mode == 'ease':
            u = ease(u)
        elif mode == 'fast':
            u = ease_out(u, 4)
        d = [(P[j + 1] - P[j]) / (ts[j + 1] - ts[j]) for j in range(n - 1)]

        def tang(j):
            if j == 0:
                return d[0] * 0.5
            if j == n - 1:
                return d[-1] * 0.5
            m = (d[j - 1] + d[j]) / 2
            m = np.where(d[j - 1] * d[j] <= 0, 0.0, m)
            lim = 3 * np.minimum(np.abs(d[j - 1]), np.abs(d[j]))
            return np.clip(m, -lim, lim)
        m0, m1 = tang(i) * h, tang(i + 1) * h
        if mode in ('ease', 'fast'):
            m0 = m1 = (P[i + 1] - P[i])
        h00 = 2 * u ** 3 - 3 * u ** 2 + 1
        h10 = u ** 3 - 2 * u ** 2 + u
        h01 = -2 * u ** 3 + 3 * u ** 2
        h11 = u ** 3 - u ** 2
        v = h00 * P[i] + h10 * m0 + h01 * P[i + 1] + h11 * m1
    return v[0:3], v[3:6], float(v[6]), float(v[7])


def punch(t, at, amt=0.2, attack=0.06, hold=0.3, release=0.55):
    if t < at:
        return 0.0
    d = t - at
    if d < attack:
        return amt * ease_out(d / attack)
    if d < attack + hold:
        return amt
    return amt * (1 - ease(min(1, (d - attack - hold) / release)))


def shake(t, at, amp=16, dur=0.35, freq=36):
    if t < at or t > at + dur:
        return (0, 0)
    k = (1 - (t - at) / dur) ** 2 * amp
    return (k * math.sin((t - at) * freq * 6.28), k * math.cos((t - at) * freq * 5.1))


def mkcam(keys, t, punches=(), shakes=(), handheld=0.03):
    pos, tgt, fov, roll = path(keys, t)
    f = 1.0
    for p in punches:
        f += punch(t, *p) if isinstance(p, tuple) else punch(t, p)
    sx = sy = 0
    for s in shakes:
        dx, dy = shake(t, *s) if isinstance(s, tuple) else shake(t, s)
        sx += dx
        sy += dy
    tgt = tgt + v3(handheld * math.sin(t * 0.9), handheld * math.sin(t * 1.3 + 1), 0)
    return Camera(pos, tgt, fov=fov / f, roll=roll, shake=(sx, sy))


SKY_GOLD = (rgb('#7fa6d8'), rgb('#ffcf96'))
SKY_DUSK = (rgb('#4a3f7a'), rgb('#ff9a5a'))
SKY_HEAVEN = (rgb('#8f7ad8'), rgb('#ffe3b8'))
FOG_GOLD = (rgb('#ffd9b0'), 18, 90)


# ------------------------------------------------------------------ sets
def cherry(sc, x, z, s=1.0):
    sc.cyl((x, 0, z), 0.16 * s, 1.6 * s, rgb('#5a3a2a'), seg=7)
    for k, (dx, dy, dz, r) in enumerate([(0, 2.0, 0, 1.0), (0.6, 1.7, 0.2, 0.7), (-0.6, 1.8, -0.1, 0.75), (0.1, 2.5, 0.1, 0.65)]):
        sc.cyl((x + dx * s, dy * s - 0.4 * s, z + dz * s), r * s, 0.9 * s, rgb('#f4a6c0') if k % 2 else rgb('#f7bcd0'),
               seg=10, r2=r * s * 0.4)


def tomb(sc, x, z, s=1.0, face=True):
    sc.box((x, 0.12 * s, z), (1.5 * s, 0.24 * s, 1.0 * s), rgb('#8f8f98'))
    sc.box((x, 0.9 * s, z + 0.2 * s), (0.9 * s, 1.35 * s, 0.25 * s), rgb('#9a9aa4'), top=rgb('#a6a6b0'))
    if face:
        sc.quad_tex(v3(x - 0.38 * s, 1.5 * s, z + 0.07 * s), v3(0.76 * s, 0, 0), v3(0, -1.2 * s, 0), T2.tomb_face(), 500, 800,
                    lw=2, shade=False, depth_bias=-0.05)


def bin_(sc, x, z, t, k=1.0, seed=0, emb=True, smk=True):
    sc.cyl((x, 0, z), 0.32, 0.62, rgb('#4a4a52'), seg=14, top=rgb('#1a1a1e'))
    sc.cyl((x, 0.62, z), 0.34, 0.04, rgb('#6a6a72'), seg=14, top=rgb('#2a1a10'))
    fx.fire(sc, (x, 0.6, z), 0.9, t, k, seed)
    if emb:
        fx.embers(sc, (x, 0.8, z), t, n=14, spread=0.25, height=2.2, speed=0.45, seed=seed)
    if smk:
        fx.smoke(sc, (x, 1.3, z), t, n=6, height=3.5, speed=0.18, seed=seed, size=0.55, alpha=70)


def cemetery(sc, t, many=False, ground=True):
    if ground:
        S.ground(sc, T.grass(), size=200, rep=50, center=(0, 40))
        sc.poly([v3(-0.7, 0.01, -20), v3(0.7, 0.01, -20), v3(0.7, 0.01, 30), v3(-0.7, 0.01, 30)], rgb('#cbbca8'),
                layer=0, normal=(0, 1, 0), outline=False)
    # distant hills
    for i, (x, z, r, h) in enumerate([(-30, 70, 26, 10), (10, 85, 32, 14), (45, 70, 24, 9)]):
        sc.cyl((x, -1, z), r, h, rgb('#7fb072'), seg=18, r2=r * 0.25, outline=False)
    for i, (x, z, s) in enumerate([(-4.5, 6, 1.1), (4.0, 8, 1.2), (-6, 16, 1.4), (7, 18, 1.3), (-3, 26, 1.5), (5, 30, 1.4)]):
        cherry(sc, x, z, s)
    rnd = random.Random(4)
    for i in range(14):
        x = rnd.choice([-1, 1]) * rnd.uniform(2.2, 9)
        z = rnd.uniform(4, 34)
        tomb(sc, x, z, 0.9, face=False)
    if many:
        for i in range(16):
            x = rnd.choice([-1, 1]) * rnd.uniform(2.2, 9)
            z = rnd.uniform(4, 34)
            sc.cyl((x + 1.0, 0, z - 0.6), 0.25, 0.5, rgb('#4a4a52'), seg=10)
            fx.fire(sc, (x + 1.0, 0.5, z - 0.6), 0.7, t + i, 1.0, i)
            fx.smoke(sc, (x + 1.0, 1.1, z - 0.6), t, n=4, height=3, speed=0.2, seed=i, size=0.5, alpha=55)
            char(sc, FAMS[i % len(FAMS)], (x + 0.3, 0, z - 1.0), dict(eyes=blink(t, i), arms=(20, -60)), h=1.5)


def afterlife(sc, t):
    S.ground(sc, T2.cloud_floor(), size=160, rep=40, center=(0, 30))
    rnd = random.Random(9)
    for i in range(18):
        x = rnd.uniform(-14, 14)
        z = rnd.uniform(4, 40)
        r = rnd.uniform(1.0, 2.6)
        sc.billboard(v3(x + math.sin(t * 0.3 + i) * 0.3, -0.3, z), r * 1.6,
                     lambda c: [c.drawCircle(dx, -45 + dy, rr, skia.Paint(AntiAlias=True, Color=skia.Color(255, 250, 255, 235)))
                                for dx, dy, rr in ((-30, 10, 30), (0, -5, 40), (32, 12, 28))])
    for i in range(7):  # floating lanterns
        x = rnd.uniform(-6, 6)
        z = rnd.uniform(4, 22)
        y = 2.5 + rnd.uniform(0, 3) + math.sin(t * 1.2 + i) * 0.2
        sc.billboard(v3(x, y, z), 0.6, lambda c: (
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-28, -100, 28, -20), 18, 18), skia.Paint(AntiAlias=True, Color=skia.Color(220, 50, 40))),
            c.drawRect(skia.Rect(-14, -108, 14, -98), skia.Paint(Color=skia.Color(230, 190, 70))),
            c.drawRect(skia.Rect(-14, -22, 14, -12), skia.Paint(Color=skia.Color(230, 190, 70)))))
        fx.glow(sc, (x, y + 0.3, z), 0.9, (255, 120, 60), 60)


def aura(sc, pos, h=1.75, a=35):
    fx.glow(sc, (pos[0], pos[1] + h * 0.6, pos[2]), h * 0.9, (255, 230, 150), a)


def note_quad(sc, O, U, V, value='1,000,000,000', look=0, tint=0, burn=0.0, seed=0, **kw):
    t = T2.note(value, look, tint)
    if burn > 0:
        t = fx.burnt(t, 1000, 480, burn, seed)
    sc.quad_tex(v3(*O), v3(*U), v3(*V), t, 1000, 480, lw=2, shade=False, **kw)


# ================================================================== SHOTS
def sh_hook(t):
    # 0 - 4.4: slow-mo macro of notes in the fire, rocket up to the hillside, dive back, FWOOSH
    a = fx.warp(t, [(0.0, 1.25, 0.3)])
    keys = [(0.0, (0.3, 1.45, -1.45), (0.0, 0.85, 0.0), 44), (1.2, (0.25, 1.4, -1.3), (0.0, 0.85, 0.0), 42),
            (1.95, (2.5, 9.0, -12.0), (0.0, 1.0, 10.0), 58, 0, 'fast'), (2.55, (2.0, 7.6, -10.5), (0.0, 1.0, 10.0), 58),
            (3.5, (0.5, 1.4, -2.2), (0.0, 0.95, 0.0), 48, 0, 'fast'), (4.45, (0.4, 1.35, -2.0), (0.0, 1.0, 0.0), 46)]
    cam = mkcam(keys, t, punches=[(3.64, 0.18)], shakes=[(3.66, 22)])
    sc = Scene(cam, bg=SKY_DUSK, fog=(rgb('#ffb08a'), 20, 90), ambient=0.6)
    cemetery(sc, a, many=True)
    tomb(sc, 0.0, 1.6)
    burst = (0.55 if t < 1.3 else 0.85) + 0.6 * math.exp(-max(0, t - 3.64) * 3) * (t > 3.64)
    bin_(sc, 0, 0, a, k=burst, seed=1)
    # hero note held over the fire, burning in slow motion
    if t < 1.35:
        note_quad(sc, (-0.26, 1.18, -0.55), (0.52, 0.0, 0.05), (0, -0.25, 0.04), tint=0, burn=clamp(a * 1.9), seed=1,
                  depth_bias=-0.6)
    # notes falling into the fire in slow motion
    for i in range(4):
        st = 0.15 + i * 0.28
        p = clamp((a - st) / 0.6)
        if p <= 0 or p >= 1:
            continue
        y = lerp(1.6, 0.68, p)
        rot = i * 0.7 + p * 1.2
        U = (0.42 * math.cos(rot), 0.05, 0.42 * math.sin(rot))
        V = (-0.2 * math.sin(rot), -0.02, 0.2 * math.cos(rot))
        note_quad(sc, (-0.2 + i * 0.08, y, -0.3 + 0.03 * i), U, V, tint=i % 3, burn=max(0, p - 0.4) * 1.6, seed=i,
                  depth_bias=-0.3)
    # dad drops a huge stack on "billions"
    if t > 2.2:
        char(sc, DAD, (-0.75, 0, -0.35), dict(eyes='closed' if t > 3.7 else 'dot', brows='up', mouth='o' if t > 3.7 else 'smile',
                                               arms=(20, -110), red=0.0), h=1.75)
        p = clamp((t - 2.9) / 0.7)
        if p < 1:
            sc.box((lerp(-0.35, 0, p), lerp(1.2, 0.72, ease_in(p)), lerp(-0.25, 0, p)), (0.42, 0.18, 0.2), rgb('#e8d6a0'),
                   top=rgb('#d08a3a'))
    return sc


def sh_notforthem(t):
    keys = [(4.35, (0.3, 1.25, -2.8), (0.05, 1.0, 0.3), 46), (5.95, (0.2, 1.2, -2.3), (0.05, 1.0, 0.3), 44)]
    cam = mkcam(keys, t, punches=[(5.25, 0.12)])
    sc = Scene(cam, bg=SKY_DUSK, fog=(rgb('#ffb08a'), 20, 90), ambient=0.6)
    cemetery(sc, t)
    bin_(sc, 0.1, 0.4, t, seed=2)
    grab = 4.6 < t < 5.2
    char(sc, KID, (-0.45, 0, 0.25), dict(eyes='money' if t < 5.25 else 'wide', mouth='grin' if t < 5.25 else 'frown',
                                         brows='up' if t < 5.25 else 'worried', arms=(20, -120 if grab else -30)), h=1.25)
    away = ease(clamp((t - 5.15) / 0.3))
    char(sc, DAD, (0.65, 0, 0.2), dict(eyes='half' if t > 5.2 else 'dot', brows='flat', mouth='flat',
                                       arms=(20, lerp(-100, -170, away)), sq=bob(t)))
    hx = lerp(0.35, 0.75, away)
    hy = lerp(1.15, 1.85, away)
    note_quad(sc, (hx - 0.2, hy + 0.1, 0.0), (0.4, 0, 0), (0, -0.19, 0), tint=0, depth_bias=-0.4)
    return sc


def sh_rise(t):
    # 5.95 - 9.6: follow the smoke up into the sky -> afterlife; grandpa with needs
    if t < 6.95:
        keys = [(5.9, (0.0, 1.2, -1.8), (0.0, 2.0, 0.4), 48), (6.95, (0.0, 6.5, -1.4), (0.0, 12.0, 1.0), 56, 0, 'fast')]
        cam = mkcam(keys, t)
        sc = Scene(cam, bg=SKY_DUSK, fog=(rgb('#ffb08a'), 20, 90), ambient=0.6)
        cemetery(sc, t)
        bin_(sc, 0, 0.4, t, seed=3)
        fx.smoke(sc, (0, 1.4, 0.4), t, n=12, height=10, speed=0.35, seed=5, size=1.0, alpha=120)
        return sc
    keys = [(6.95, (0.0, 4.5, -3.6), (0.0, 1.2, 2.0), 56), (7.6, (0.2, 1.7, -2.6), (0.0, 1.2, 2.0), 50, 0, 'fast'),
            (9.65, (0.1, 1.5, -1.6), (0.0, 1.2, 2.0), 44)]
    cam = mkcam(keys, t, punches=[(8.23, 0.12)])
    sc = Scene(cam, bg=SKY_HEAVEN, fog=(rgb('#f0e2ff'), 15, 70), ambient=0.75)
    afterlife(sc, t)
    gp = (0, 0, 2.0)
    aura(sc, gp)
    pose = dict(eyes=blink(t, 1), brows='worried' if t > 8.0 else 'flat', mouth='frown' if t > 8.0 else 'smile',
                arms=(20, -150 + 15 * math.sin(t * 10)) if 7.5 < t < 8.1 else (20, -20), sq=bob(t))
    char(sc, GRANDPA, gp, pose)
    # "needs": icons pop up around him
    icons = [('r', (-0.75, 1.75, 1.9), 8.23), ('h', (0.0, 2.15, 1.9), 8.45), ('p', (0.75, 1.75, 1.9), 8.68)]
    for i, (_, p, t0) in enumerate(icons):
        if t < t0:
            continue
        k = ease_back(clamp((t - t0) / 0.2), 2)
        sc.billboard(v3(*p), 0.55 * k, lambda c, i=i: _need_icon(c, i), depth_bias=-1)
    return sc


def _need_icon(c, i):
    c.drawCircle(0, -50, 48, skia.Paint(AntiAlias=True, Color=skia.Color(255, 255, 255)))
    c.drawCircle(0, -50, 48, skia.Paint(AntiAlias=True, Color=INK, Style=skia.Paint.kStroke_Style, StrokeWidth=5))
    p = lambda cc: skia.Paint(AntiAlias=True, Color=skia.Color(*cc))
    if i == 0:  # rice bowl
        c.drawCircle(0, -58, 22, p((250, 250, 250)))
        c.drawCircle(0, -58, 22, skia.Paint(AntiAlias=True, Color=INK, Style=skia.Paint.kStroke_Style, StrokeWidth=3))
        c.drawRect(skia.Rect(-30, -56, 30, -50), p((250, 250, 250)))
        pa = skia.Path()
        pa.moveTo(-30, -52)
        pa.quadTo(0, -10, 30, -52)
        pa.close()
        c.drawPath(pa, p((60, 120, 200)))
    elif i == 1:  # house
        pa = skia.Path()
        pa.moveTo(-28, -50)
        pa.lineTo(0, -78)
        pa.lineTo(28, -50)
        pa.close()
        c.drawPath(pa, p((200, 50, 50)))
        c.drawRect(skia.Rect(-22, -50, 22, -22), p((240, 200, 120)))
        c.drawRect(skia.Rect(-6, -40, 6, -22), p((120, 70, 40)))
    else:  # phone
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-16, -80, 16, -20), 6, 6), p((30, 30, 36)))
        c.drawRect(skia.Rect(-12, -74, 12, -28), p((90, 170, 240)))


def sh_qingming(t):
    keys = [(9.6, (0.0, 9.0, -3.0), (0.0, 1.0, 2.0), 56), (10.4, (-1.6, 1.8, -2.6), (0.0, 0.9, 1.0), 50, 0, 'fast'),
            (13.1, (-0.4, 1.6, -2.4), (0.2, 1.0, 1.0), 46)]
    cam = mkcam(keys, t, punches=[(10.32, 0.1), (12.36, 0.12)])
    sc = Scene(cam, bg=SKY_GOLD, fog=FOG_GOLD, ambient=0.66)
    cemetery(sc, t)
    tomb(sc, 0.2, 2.2)
    for i, (x, col_) in enumerate([(-0.2, (240, 140, 40)), (0.0, (240, 160, 40)), (0.2, (230, 120, 40))]):
        sc.cyl((x + 0.2, 0.25, 1.6), 0.08, 0.06, rgb('#d8d8d0'), seg=8)
        sc.billboard(v3(x + 0.2, 0.32, 1.6), 0.14, lambda c, cc=col_: c.drawCircle(0, -50, 50, skia.Paint(AntiAlias=True, Color=skia.Color(*cc))))
    for i in range(3):  # incense sticks
        sc.box((0.05 + i * 0.07, 0.55, 1.75), (0.015, 0.6, 0.015), rgb('#a03020'))
        fx.smoke(sc, (0.05 + i * 0.07, 0.86, 1.75), t, n=4, height=1.5, speed=0.3, seed=i + 10, size=0.12, alpha=90)
    bin_(sc, 1.0, 1.1, t, seed=4)
    char(sc, MOM, (-0.7, 0, 0.9), dict(eyes='closed', mouth='flat', arms=((60, 160), (-60, -160)), sq=bob(t)))
    char(sc, KID, (-0.1, 0, 0.6), dict(eyes=blink(t, 2), mouth='smile', arms=(20, -20)), h=1.25)
    throw = 10.25 < t < 10.9
    char(sc, DAD, (1.55, 0, 0.7), dict(eyes=blink(t, 3), mouth='flat', arms=(20, -120 if throw else -40)))
    if 10.2 < t < 11.4:
        p = clamp((t - 10.3) / 0.8)
        note_quad(sc, (lerp(1.2, 0.85, p), lerp(1.3, 0.75, p), lerp(0.6, 1.0, p)), (0.36, 0, 0.0), (0, -0.17, 0.05),
                  tint=1, burn=max(0, p - 0.5) * 2, seed=3, depth_bias=-0.2)
    return sc


def sh_mail(t):
    # 13.05 - 17.55: mailing grandpa a gift card... into fire (slow-mo at the end)
    a = fx.warp(t, [(16.35, 17.6, 0.35)])
    keys = [(13.0, (1.6, 1.6, -3.4), (0.0, 1.2, 0.0), 50), (15.0, (0.8, 1.4, -2.2), (0.0, 1.2, 0.0), 46),
            (15.95, (0.05, 1.32, -0.75), (0.0, 1.28, 0.0), 42, 0, 'fast'), (16.35, (0.0, 1.28, -0.15), (0.0, 1.0, 0.4), 50, 0, 'fast'),
            (17.6, (0.0, 1.22, -0.05), (0.0, 0.95, 0.35), 46)]
    cam = mkcam(keys, t, punches=[(16.93, 0.1)])
    inside = t > 16.3
    sc = Scene(cam, bg=SKY_GOLD if not inside else (30, 14, 8), fog=None if inside else FOG_GOLD, ambient=0.66)
    if not inside:
        S.ground(sc, T2.stone_tiles(), size=60, rep=20, center=(0, 10))
        sc.quad_tex(v3(-6, 4, 1.2), v3(12, 0, 0), v3(0, -4, 0), T2.red_wall(), 256, 256, lw=2)
        # mailbox
        sc.box((0, 0.55, 0.3), (0.2, 1.1, 0.2), rgb('#1f5a3a'))
        sc.box((0, 1.25, 0.3), (0.8, 0.6, 0.6), rgb('#2f8a5a'), top=rgb('#3a9a6a'))
        sc.poly([v3(-0.25, 1.38, -0.005), v3(0.25, 1.38, -0.005), v3(0.25, 1.44, -0.005), v3(-0.25, 1.44, -0.005)],
                rgb('#2a0a00'), normal=None, depth_bias=-0.05)
        fx.glow(sc, (0, 1.41, 0.0), 0.25, (255, 140, 40), 90)
        sc.quad_tex(v3(-0.3, 1.32, -0.005), v3(0.6, 0, 0), v3(0, -0.22, 0), T2.mailbox_label(), 700, 260, lw=1.5, shade=False,
                    depth_bias=-0.06)
        char(sc, DAD, (0.75, 0, -0.35), dict(eyes=blink(t, 1), mouth='smile', arms=(20, -105 if t < 15.9 else -40), sq=bob(t)))
        if t < 15.95:
            p = ease(clamp((t - 15.0) / 0.9))
            sc.quad_tex(v3(lerp(0.45, -0.17, p), lerp(1.55, 1.48, p), lerp(-0.3, -0.02, p)), v3(0.34, 0, 0), v3(0, -0.21, 0),
                        T2.gift_card(), 860, 540, lw=2, shade=False, depth_bias=-0.3)
    else:
        # inside the mailbox: it's a furnace
        sc.box((0, 0.5, 0.5), (1.4, 1.4, 1.4), rgb('#3a2a20'), sides=('back', 'left', 'right', 'bottom'))
        fx.fire(sc, (0, 0.2, 0.5), 0.9, a * 1.0, 1.2, 5)
        fx.embers(sc, (0, 0.5, 0.45), a, n=26, spread=0.3, height=0.9, speed=0.6, seed=6, size=0.018)
        p = clamp((a - 16.3) / 0.6)
        burn = clamp((a - 16.42) / 0.45)
        tex_ = fx.burnt(T2.gift_card(), 860, 540, burn, 2)
        sc.quad_tex(v3(-0.17, lerp(1.3, 0.95, ease_out(p)), 0.3), v3(0.34, 0, 0), v3(0, -0.06, 0.2), tex_, 860, 540, lw=2,
                    shade=False, depth_bias=-0.3)
    return sc


def sh_values(t):
    keys = [(17.5, (-0.5, 1.4, -0.9), (0.0, 0.78, 0.2), 44), (19.9, (0.2, 1.25, -0.55), (0.1, 0.78, 0.25), 42),
            (20.95, (0.25, 1.15, -0.35), (0.15, 0.78, 0.3), 38)]
    cam = mkcam(keys, t, punches=[(18.91, 0.12), (19.95, 0.28)], shakes=[(19.98, 18)])
    sc = Scene(cam, bg=(28, 18, 14), ambient=0.75)
    S.room(sc, w=6, d=6, h=3, z0=-3, wall=T2.red_wall(), floor=T.planks((90, 60, 40)), sides=False)
    S.table(sc, (0, 0, 0.4), w=2.2, d=1.4, top=rgb('#6b3f22'))
    vals = [('1,000', 17.7, 0), ('1,000,000', 18.91, 1), ('1,000,000,000', 19.95, 2)]
    for i, (v, t0, tint) in enumerate(vals):
        if t < t0 - 0.2:
            continue
        p = ease_out(clamp((t - (t0 - 0.2)) / 0.22))
        rot = -0.35 + i * 0.3
        x = lerp(-1.2, -0.25 + i * 0.2, p)
        U = (0.5 * math.cos(rot), 0, 0.5 * math.sin(rot))
        V = (-0.24 * math.sin(rot), 0, 0.24 * math.cos(rot))
        note_quad(sc, (x, 0.83 + i * 0.003 + (1 - p) * 0.3, 0.25), U, (-V[0], 0, -V[2]), value=v, tint=tint)
    fx.glow(sc, (0.2, 0.9, 0.4), 1.2, (255, 190, 110), 50)
    return sc


def sh_bank(t):
    # 20.9 - 24.55: slow macro over the giant note, then the ruler's eyes shift to camera
    keys = [(20.85, (-0.55, 1.45, -1.2), (-0.55, 0.0, -0.25), 40), (22.3, (-0.5, 1.3, -1.08), (-0.55, 0.0, -0.28), 38),
            (23.1, (0.0, 1.1, -0.75), (0.0, 0.0, -0.1), 44, 0, 'ease'), (24.6, (0.0, 0.8, -0.5), (0.0, 0.0, -0.12), 40)]
    cam = mkcam(keys, t, punches=[(21.48, 0.12), (23.92, 0.3)], shakes=[(23.95, 14)], handheld=0.01)
    sc = Scene(cam, bg=(28, 18, 14), ambient=0.85)
    S.ground(sc, T.planks((80, 50, 32)), size=12, rep=8, center=(0, 0))
    look = 1 if t > 23.5 else 0
    note_quad(sc, (-1.0, 0.01, 0.48), (2.0, 0, 0), (0, 0, -0.96), look=look, tint=0)
    fx.glow(sc, (0.0, 0.3, 0.0), 2.0, (255, 200, 140), 40)
    return sc


def sh_why(t):
    keys = [(24.5, (0.9, 1.3, -2.4), (-0.2, 0.9, 0.6), 50), (25.6, (0.1, 1.1, -1.3), (-0.2, 0.85, 0.6), 42, 0, 'fast')]
    cam = mkcam(keys, t, punches=[(24.77, 0.16)])
    sc = Scene(cam, bg=SKY_DUSK, fog=(rgb('#ffb08a'), 20, 90), ambient=0.6)
    cemetery(sc, t)
    bin_(sc, 0.6, 0.9, t, seed=7)
    char(sc, KID, (-0.2, 0, 0.6), dict(eyes='dot', brows='one', mouth='flat', tilt=10, arms=(20, (-150, -175))), h=1.25)
    return sc


def sh_comfy(t):
    # 25.55 - 28.85 luxury afterlife; 28.85 - 30.05 the shabby alternative
    shabby = t > 28.85
    if not shabby:
        keys = [(25.5, (-1.8, 1.6, -2.6), (0.0, 1.0, 1.2), 50), (28.9, (1.4, 1.5, -2.0), (0.0, 1.0, 1.2), 46)]
        cam = mkcam(keys, t, punches=[(27.82, 0.1)])
        sc = Scene(cam, bg=(40, 30, 20), ambient=0.75)
        S.room(sc, w=8, d=8, h=4, z0=-4, wall=T2.gold_wall(), floor=T2.stone_tiles())
        S.chandelier(sc, (0, 3.2, 1.0)) if hasattr(S, 'chandelier') else None
        sc.box((0, 0.3, 1.4), (1.8, 0.35, 0.8), rgb('#a01c1c'), top=rgb('#c02a2a'))
        sc.box((0.7, 0.6, 1.4), (0.4, 0.5, 0.8), rgb('#a01c1c'))
        for i, cc in enumerate(('#ff8a2a', '#ffcc33', '#d33a3a')):
            sc.cyl((-1.3 + i * 0.12, 0.62, 0.9), 0.07, 0.1, rgb(cc), seg=8)
        sc.box((-1.3, 0.3, 0.9), (0.6, 0.6, 0.5), rgb('#6b3f22'), top=rgb('#d9b24a'))
        char(sc, GRANDPA, (-0.1, 0.35, 1.4), dict(eyes='closed', brows='flat', mouth='grin', shades=True, sit=True,
                                                   arms=(20, (-140 + 10 * math.sin(t * 6), -150))), shadow=False)
        aura(sc, (-0.1, 0.35, 1.4), a=55)
        for i in range(10):
            ph = (t * 0.25 + i / 10) % 1.0
            sc.billboard(v3(-3 + i * 0.7, 3.5 - ph * 3.5, 2.5), 0.15, lambda c: c.drawCircle(0, -50, 40, skia.Paint(
                AntiAlias=True, Color=skia.Color(255, 220, 90, 200))))
        return sc
    keys = [(28.8, (0.5, 1.5, -2.4), (0.0, 1.0, 1.2), 48), (30.1, (0.3, 1.4, -2.0), (0.0, 1.0, 1.2), 46)]
    cam = mkcam(keys, t)
    sc = Scene(cam, bg=(30, 26, 22), ambient=0.55)
    S.room(sc, w=5, d=5, h=3, z0=-3, wall=T2.shack_wall(), floor=T.planks((100, 80, 60)))
    sc.box((0, 0.25, 1.2), (0.6, 0.5, 0.5), rgb('#7a5a3a'))
    char(sc, GRANDPA, (0, 0.5, 1.2), dict(eyes='dot', brows='worried', mouth='frown', sit=True, arms=(20, (-110, -150)),
                                           hold=lambda c: (c.drawCircle(0, -4, 5, skia.Paint(AntiAlias=True, Color=skia.Color(240, 240, 240))))),
         shadow=False)
    return sc


def sh_shop(t):
    a = fx.warp(t, [(33.55, 34.5, 0.4)])
    keys = [(30.0, (1.8, 1.7, -3.2), (0.0, 1.1, 1.2), 52), (31.9, (0.7, 1.3, -2.0), (-0.2, 1.0, 1.0), 46),
            (33.6, (-0.1, 0.95, -1.4), (-0.35, 0.9, 0.6), 46, 0, 'fast'), (35.35, (-0.2, 0.95, -1.15), (-0.35, 0.9, 0.6), 42)]
    cam = mkcam(keys, t, punches=[(31.85, 0.1), (33.61, 0.18)], shakes=[(33.62, 12)])
    sc = Scene(cam, bg=(40, 20, 18), ambient=0.72)
    S.room(sc, w=7, d=6, h=3.4, z0=-3, wall=T2.red_wall(), floor=T.planks((110, 80, 50)))
    sc.quad_tex(v3(-1.6, 3.2, 2.95), v3(3.2, 0, 0), v3(0, -1.28, 0), T2.shop_sign(), 900, 360, lw=3, shade=False)
    # shelves with paper goods
    for sx in (-2.6, 2.6):
        for k in range(3):
            sc.box((sx, 0.5 + k * 0.8, 2.6), (1.4, 0.06, 0.6), rgb('#6b3f22'))
            for j in range(3):
                cc = ['#e8c060', '#d84a3a', '#f0e0c0'][(j + k) % 3]
                sc.box((sx - 0.45 + j * 0.45, 0.68 + k * 0.8, 2.6), (0.3, 0.3, 0.3), rgb(cc), top=rgb('#c03030'))
    sc.box((0.5, 0.5, 1.4), (2.0, 1.0, 0.7), rgb('#8a2a2a'), top=rgb('#d9b24a'))
    char(sc, SHOPKEEP, (0.6, 0, 2.0), dict(eyes='closed' if t > 32.2 else blink(t, 2), mouth='smile',
                                           arms=(20, -100 if 32.0 < t < 33.3 else -20)))
    sc.quad_tex(v3(-0.1, 1.45, 1.04), v3(0.42, 0, 0), v3(0, -0.25, 0), T2.price_tag('¥0.10'), 400, 240, lw=2, shade=False,
                depth_bias=-0.2)
    rich = t > 33.55
    char(sc, KID, (-0.35, 0, 0.6), dict(eyes='closed' if rich else 'dot', mouth='grin' if rich else 'smile', shades=rich,
                                        brows='up', arms=(20, -150) if rich else (20, -100 if t < 32.0 else -30)), h=1.25)
    # stack of billions slides to the kid
    if t > 32.6:
        p = ease_out(clamp((t - 32.6) / 0.5))
        sc.box((lerp(0.6, 0.0, p), 1.12, 1.3), (0.5, 0.22 + (0.3 if rich else 0), 0.26), rgb('#e8d6a0'), top=rgb('#d08a3a'))
    if rich:  # money rain (slow-mo)
        rnd = random.Random(3)
        for i in range(26):
            ph = rnd.random()
            fall = ((a - 33.55) * 0.7 + ph) % 1.0
            x = rnd.uniform(-1.4, 0.8)
            z = rnd.uniform(0.0, 1.6)
            y = 3.0 - fall * 3.2
            rot = a * 3 + i
            U = (0.22 * math.cos(rot), 0.05 * math.sin(rot * 1.3), 0.22 * math.sin(rot))
            V = (0, -0.1, 0.02)
            note_quad(sc, (x, y, z), U, V, tint=i % 3, depth_bias=-0.1)
    return sc


def sh_inflation(t):
    keys = [(35.3, (-1.2, 1.6, -2.6), (0.2, 1.3, 1.2), 50), (37.9, (-0.6, 1.4, -2.0), (0.3, 1.4, 1.2), 46),
            (39.1, (0.4, 1.3, -2.2), (0.0, 1.3, 1.0), 48, 0, 'fast'), (40.9, (0.2, 1.4, -2.6), (0.0, 1.6, 1.0), 54)]
    cam = mkcam(keys, t, punches=[(37.91, 0.14), (40.34, 0.2)], shakes=[(40.36, 26)])
    sc = Scene(cam, bg=SKY_HEAVEN, fog=(rgb('#f0e2ff'), 15, 70), ambient=0.75)
    afterlife(sc, t)
    # bakery stall
    sc.box((0.8, 0.5, 2.0), (1.8, 1.0, 0.7), rgb('#a01c1c'), top=rgb('#d9b24a'))
    for x in (-0.05, 1.65):
        sc.box((x, 1.4, 2.0), (0.08, 2.8, 0.08), rgb('#6b3f22'))
    sc.box((0.8, 2.85, 2.0), (2.0, 0.12, 0.9), rgb('#c03030'))
    sc.cyl((0.8, 1.0, 1.85), 0.16, 0.14, rgb('#f6efe0'), seg=12, r2=0.06)  # bun
    from tex2 import RULER
    char(sc, RULER, (0.9, 0, 2.6), dict(eyes='squint', brows='angry', mouth='flat', arms=(20, -20)))
    price = '1,000,000' if t < 37.9 else ('1 BILLION' if t < 39.1 else ['2 BILLION', '50 BILLION', '1 TRILLION'][min(2, int((t - 39.1) / 0.4))])
    sc.quad_tex(v3(0.55, 1.45, 1.6), v3(0.55, 0, 0), v3(0, -0.33, 0), T2.price_tag(price), 400, 240, lw=2, shade=False,
                depth_bias=-0.2)
    gp = (-0.45, 0, 1.0)
    aura(sc, gp, a=50)
    shock = t > 37.9
    char(sc, GRANDPA, gp, dict(eyes='wide' if shock else 'dot', brows='up' if shock else 'flat',
                               mouth='o' if shock else 'smile', arms=(20, (-120, -170)), sweat=t > 39.1, sq=bob(t)))
    # the note he holds grows every year
    g = 1.0
    if t > 39.1:
        g = 1 + min(3, int((t - 39.1) / 0.4)) * 0.7
    if t > 40.34:
        g = 3.6 + 1.5 * ease_back(clamp((t - 40.34) / 0.25))
    w_, h_ = 0.45 * g, 0.216 * g
    note_quad(sc, (-0.2 - w_ / 2 + 0.15, 1.35 + h_, 0.85), (w_, 0, 0), (0, -h_, 0), value='1,000,000,000', tint=2,
              depth_bias=-0.4)
    if t > 39.1:
        yr = 2024 + min(3, int((t - 39.1) / 0.4))
        sc.quad_tex(v3(-2.2, 3.1, 2.4), v3(1.0, 0, 0), v3(0, -0.66, 0), T2.year_card(yr), 700, 460, lw=2, shade=False)
    return sc


def sh_notenough(t):
    keys = [(40.85, (0.3, 1.5, -1.9), (0.0, 1.3, 1.0), 46), (42.4, (0.15, 1.45, -1.3), (0.0, 1.35, 1.0), 40)]
    cam = mkcam(keys, t, punches=[(41.82, 0.1)])
    sc = Scene(cam, bg=SKY_HEAVEN, fog=(rgb('#f0e2ff'), 15, 70), ambient=0.7)
    afterlife(sc, t)
    gp = (0, 0, 1.0)
    aura(sc, gp, a=40)
    char(sc, GRANDPA, gp, dict(eyes='dot', brows='worried', mouth='frown', arms=(90, -90), sq=bob(t)))
    # empty pockets (white flaps) + a moth
    mx = math.sin(t * 6) * 0.25
    sc.billboard(v3(mx, 1.0 + (t - 40.85) * 0.5, 0.95), 0.12, lambda c: (
        c.drawOval(skia.Rect(-40, -80, 0, -40), skia.Paint(AntiAlias=True, Color=skia.Color(200, 190, 170))),
        c.drawOval(skia.Rect(0, -80, 40, -40), skia.Paint(AntiAlias=True, Color=skia.Color(200, 190, 170)))), depth_bias=-1)
    return sc


def _paper_house(sc, x, z, s, burn_k, t):
    sc.box((x, 0.65 + 0.35 * s, z), (0.9 * s, 0.7 * s, 0.7 * s), rgb('#f6ead2'))
    sc.quad_tex(v3(x - 0.45 * s, 0.65 + 0.7 * s, z - 0.351 * s), v3(0.9 * s, 0, 0), v3(0, -0.7 * s, 0), T2.paper_house_face(),
                600, 420, lw=2, shade=False, depth_bias=-0.02)
    roof = [v3(x - 0.55 * s, 0.65 + 0.7 * s, z - 0.45 * s), v3(x + 0.55 * s, 0.65 + 0.7 * s, z - 0.45 * s),
            v3(x, 0.65 + 1.1 * s, z)]
    sc.poly(roof, rgb('#c03030'))
    sc.poly([v3(x - 0.55 * s, 0.65 + 0.7 * s, z + 0.45 * s), v3(x + 0.55 * s, 0.65 + 0.7 * s, z + 0.45 * s), v3(x, 0.65 + 1.1 * s, z)],
            rgb('#a02828'))


def _paper_car(sc, x, z, s):
    sc.box((x, 0.85, z), (0.9 * s, 0.25 * s, 0.45 * s), rgb('#d83a3a'), top=rgb('#e85a4a'))
    sc.box((x - 0.05, 1.05, z), (0.5 * s, 0.2 * s, 0.42 * s), rgb('#f0e8d8'))
    for wx in (-0.3, 0.3):
        sc.billboard(v3(x + wx * s, 0.68, z - 0.24 * s), 0.18 * s, lambda c: (
            c.drawCircle(0, -50, 46, skia.Paint(AntiAlias=True, Color=INK)),
            c.drawCircle(0, -50, 18, skia.Paint(AntiAlias=True, Color=skia.Color(220, 220, 220)))), depth_bias=-0.2)


def sh_goods(t):
    # 42.35 - 47.5 paper house, car, phone into the fire (macro, fast whips between)
    keys = [(42.3, (-2.0, 2.0, -3.2), (0.0, 0.9, 0.3), 50), (43.6, (-0.8, 1.6, -2.3), (0.0, 0.95, 0.3), 46, 0, 'fast'),
            (44.65, (0.6, 1.5, -2.0), (0.0, 0.95, 0.3), 46), (45.0, (-0.5, 1.45, -1.8), (0.0, 0.95, 0.3), 44, 0, 'fast'),
            (45.9, (0.5, 1.4, -1.7), (0.0, 0.95, 0.3), 44), (46.3, (0.0, 1.45, -1.4), (0.0, 1.1, 0.3), 42, 0, 'fast'),
            (47.55, (0.0, 1.7, -1.3), (0.0, 1.7, 0.3), 46)]
    cam = mkcam(keys, t, punches=[(43.79, 0.12), (45.02, 0.12), (46.58, 0.14)], shakes=[(43.82, 12), (45.05, 12), (46.6, 12)])
    sc = Scene(cam, bg=SKY_DUSK, fog=(rgb('#ffb08a'), 20, 90), ambient=0.6)
    cemetery(sc, t)
    sc.box((0, 0.3, 0.3), (1.2, 0.6, 1.0), rgb('#4a4a52'), top=rgb('#1a1a1e'))  # big burner
    big = 0.9 + 0.35 * (t > 43.79)
    fx.fire(sc, (0, 0.6, 0.45), 0.8, t, big, 8, depth_bias=0.3)
    fx.embers(sc, (0, 0.9, 0.3), t, n=26, spread=0.4, height=2.6, speed=0.5, seed=8)
    fx.smoke(sc, (0, 1.8, 0.3), t, n=8, height=4, speed=0.2, seed=8, size=0.8, alpha=80)
    if t < 44.7:
        p = ease_out(clamp((t - 42.6) / 1.1))
        _paper_house(sc, lerp(-1.4, 0.0, p), 0.3, 0.5, 0, t)
        char(sc, DAD, (lerp(-2.2, -0.9, p), 0, -0.2), dict(eyes=blink(t), mouth='smile', arms=(20, -110), walk=t * 2.4 if p < 1 else None))
    elif t < 45.9:
        p = ease_out(clamp((t - 44.7) / 0.4))
        _paper_car(sc, lerp(1.3, 0.0, p), 0.2, 0.6)
        char(sc, KID, (1.0, 0, -0.1), dict(eyes='closed', mouth='grin', arms=(20, -150)), h=1.25)
    else:
        p = ease_out(clamp((t - 45.95) / 0.45))
        sc.quad_tex(v3(-0.15, lerp(1.6, 1.15, p), lerp(-0.1, 0.25, p)), v3(0.3, 0, 0), v3(0, -0.54, 0.05),
                    fx.burnt(T2.phone_screen(0), 500, 900, clamp((t - 46.6) / 0.9), 4), 500, 900, lw=2, shade=False,
                    depth_bias=-0.4)
        char(sc, MOM, (-0.9, 0, -0.1), dict(eyes=blink(t, 2), mouth='smile', arms=(20, -100)))
    return sc


def sh_upgrade(t):
    keys = [(47.5, (0.0, 4.0, -3.2), (0.0, 1.4, 1.0), 54), (48.2, (0.4, 1.6, -2.1), (0.0, 1.35, 1.0), 46, 0, 'fast'),
            (49.5, (0.25, 1.5, -1.7), (0.0, 1.35, 1.0), 42)]
    cam = mkcam(keys, t, punches=[(48.78, 0.16)], shakes=[(48.8, 10)])
    sc = Scene(cam, bg=SKY_HEAVEN, fog=(rgb('#f0e2ff'), 15, 70), ambient=0.78)
    afterlife(sc, t)
    if t > 48.5:  # paper mansion + car appear behind him
        k = ease_back(clamp((t - 48.5) / 0.3))
        _paper_house(sc, -1.5, 3.2, 1.8 * k + 0.01, 0, t)
        _paper_car(sc, 1.4, 2.4, 1.3 * k + 0.01)
    gp = (0, 0, 1.0)
    aura(sc, gp, a=55)
    done = t > 48.78
    char(sc, GRANDPA, gp, dict(eyes='closed' if done else 'wide', mouth='grin' if done else 'o', shades=done, brows='up',
                               arms=(20, (-120, -170))))
    py = lerp(3.0, 1.62, ease_out(clamp((t - 47.6) / 0.5)))
    sc.quad_tex(v3(0.12, py + 0.2, 0.92), v3(0.18, 0, 0), v3(0, -0.32, 0), T2.phone_screen(1 if done else 0), 500, 900, lw=2,
                shade=False, depth_bias=-0.5)
    return sc


def sh_still(t):
    # 49.45 - 53.2: quiet slow-mo: one note drifting into the fire, then everyone still paying
    a = fx.warp(t, [(49.45, 52.0, 0.35)])
    if t < 51.95:
        keys = [(49.4, (0.9, 1.6, -2.1), (0.2, 1.0, 0.3), 46), (52.0, (0.7, 1.5, -1.75), (0.2, 1.0, 0.3), 42)]
        cam = mkcam(keys, t, handheld=0.015)
        sc = Scene(cam, bg=SKY_DUSK, fog=(rgb('#ffb08a'), 20, 90), ambient=0.55)
        cemetery(sc, a)
        bin_(sc, 0, 0.3, a, seed=9)
        p = clamp((a - 49.45) / 0.9)
        rot = p * 2.0
        note_quad(sc, (-0.2 + math.sin(rot) * 0.1, lerp(1.6, 0.75, p), 0.2), (0.42 * math.cos(rot * 0.3), 0, 0.1),
                  (0, -0.2, 0.05), tint=0, burn=max(0, p - 0.65) * 3, seed=9, depth_bias=-0.3)
        char(sc, DAD, (0.6, 0, 0.6), dict(eyes='half', brows='flat', mouth='flat', arms=(20, -20)))
        return sc
    keys = [(51.9, (0.0, 3.0, -5.0), (0.0, 1.0, 3.0), 54), (53.25, (0.0, 3.6, -6.2), (0.0, 1.0, 3.0), 56)]
    cam = mkcam(keys, t)
    sc = Scene(cam, bg=SKY_DUSK, fog=(rgb('#ffb08a'), 20, 90), ambient=0.6)
    cemetery(sc, t, many=True)
    return sc


def sh_end(t):
    # 53.2 - 54.85 slow-mo rise of smoke & burning notes; 54.85 - end family walks away at sunset
    a = fx.warp(t, [(53.2, 54.85, 0.4)])
    if t < 54.85:
        keys = [(53.2, (0.0, 1.2, -1.6), (0.0, 1.8, 0.4), 46), (54.9, (0.0, 2.6, -1.4), (0.0, 4.5, 0.6), 50)]
        cam = mkcam(keys, t, handheld=0.01)
        sc = Scene(cam, bg=SKY_DUSK, fog=(rgb('#ffb08a'), 20, 90), ambient=0.6)
        cemetery(sc, a)
        bin_(sc, 0, 0.4, a, seed=11, smk=False)
        fx.smoke(sc, (0, 1.6, 0.6), a, n=8, height=6, speed=0.3, seed=12, size=0.5, alpha=60)
        fx.embers(sc, (0, 1.0, 0.4), a, n=40, spread=0.6, height=5, speed=0.3, seed=13, size=0.05)
        for i in range(5):
            ph = (a * 0.25 + i / 5) % 1.0
            note_quad(sc, (-0.3 + math.sin(i + a) * 0.4, 1.2 + ph * 3.5, 0.3 + i * 0.05),
                      (0.3 * math.cos(a + i), 0.05, 0.3 * math.sin(a + i)), (0, -0.14, 0.02), tint=i % 3, burn=ph * 0.9,
                      seed=i, depth_bias=-0.2)
        return sc
    keys = [(54.8, (0.0, 1.6, -3.6), (0.0, 1.2, 4.0), 50), (57.1, (0.0, 2.6, -5.0), (0.0, 2.4, 6.0), 54)]
    cam = mkcam(keys, t)
    sc = Scene(cam, bg=SKY_DUSK, fog=(rgb('#ffb08a'), 20, 90), ambient=0.6)
    cemetery(sc, t)
    bin_(sc, 1.6, 0.2, t, seed=14, k=0.6)
    walk = (t - 54.85) * 0.75
    for i, (lk, x, h) in enumerate([(DAD, 0.35, 1.75), (KID, 0.0, 1.25), (MOM, -0.35, 1.7)]):
        char(sc, lk, (x, 0, 1.6 + walk), dict(eyes='closed', mouth='smile', walk=t * 1.8 + i * 0.3,
                                              arms=(20, -40) if i != 1 else (40, -40), sq=1.0), h=h)
    # grandpa faint in the clouds, waving
    gp = (0, 4.2, 14)
    sc.billboard(v3(*gp), 3.0, lambda c, t=t: (c.saveLayerAlpha(None, 120), draw_char(c, GRANDPA, dict(
        eyes='closed', mouth='grin', shades=True, arms=(20, -150 + 20 * math.sin(t * 8)))), c.restore()), depth_bias=-30)
    fx.glow(sc, (0, 5.6, 14), 3.5, (255, 220, 160), 60)
    return sc


TIMELINE = [
    (0.0, 4.4, sh_hook, 0, 'cut'),
    (4.4, 5.95, sh_notforthem, 0.14, 'whip'),
    (5.95, 9.6, sh_rise, 0.2, 'dissolve'),
    (9.6, 13.05, sh_qingming, 0.2, 'whip'),
    (13.05, 17.55, sh_mail, 0.2, 'whip'),
    (17.55, 20.9, sh_values, 0.2, 'whip'),
    (20.9, 24.55, sh_bank, 0.25, 'dissolve'),
    (24.55, 25.55, sh_why, 0.14, 'whip'),
    (25.55, 30.05, sh_comfy, 0.25, 'dissolve'),
    (30.05, 35.3, sh_shop, 0.18, 'whip'),
    (35.3, 40.85, sh_inflation, 0.2, 'whip'),
    (40.85, 42.35, sh_notenough, 0.2, 'dissolve'),
    (42.35, 47.5, sh_goods, 0.18, 'whip'),
    (47.5, 49.45, sh_upgrade, 0.2, 'dissolve'),
    (49.45, 53.2, sh_still, 0.3, 'dissolve'),
    (53.2, 57.1, sh_end, 0.25, 'dissolve'),
]


# ------------------------------------------------------------------ overlays
def captions_chunks():
    chunks, cur = [], []
    for w in WORDS:
        if cur:
            joined = ' '.join(x['w'] for x in cur + [w])
            ends = cur[-1]['w'][-1] in '.,?!'
            gap = w['start'] - cur[-1]['end']
            if len(cur) >= 2 or len(joined) > 13 or ends or gap > 0.25:
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    out = []
    for i, ch in enumerate(chunks):
        s = ch[0]['start']
        e = chunks[i + 1][0]['start'] if i + 1 < len(chunks) else ch[-1]['end'] + 0.4
        e = min(e, ch[-1]['end'] + 0.45)
        out.append((s, e, ' '.join(x['w'] for x in ch)))
    return out


CAPS = captions_chunks()
CAP_FONT = T.font('black', 84)
KEYWORDS = {'billions', 'fire,', 'fire.', 'Hell', 'billionaire', 'inflation,', 'bigger.', 'smoke,', 'richer.', 'Qingming.',
            'billions?', 'billions,', 'upgrade.', 'millions'}


def draw_caption(c, t):
    for s, e, txt in CAPS:
        if s - 0.02 <= t < e:
            k = ease_back(clamp((t - s) / 0.1), 2.5)
            sc = 0.82 + 0.18 * k
            c.save()
            c.translate(W / 2, H * 0.655)
            c.scale(sc, sc)
            w = CAP_FONT.measureText(txt)
            if w > W * 0.86:
                f = W * 0.86 / w
                c.scale(f, f)
            x = -w / 2
            hot = any(word in KEYWORDS for word in txt.split())
            sh = skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, 120), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
            c.drawString(txt, x + 3, 36, CAP_FONT, sh)
            c.drawString(txt, x, 30, CAP_FONT, skia.Paint(AntiAlias=True, Color=INK, Style=skia.Paint.kStroke_Style,
                                                         StrokeWidth=16, StrokeJoin=skia.Paint.kRound_Join))
            c.drawString(txt, x, 30, CAP_FONT, skia.Paint(AntiAlias=True, Color=skia.Color(255, 214, 60) if hot else skia.Color(255, 255, 255)))
            c.restore()
            break


def vignette(c, strength=140, color=(0, 0, 0)):
    sh = skia.GradientShader.MakeRadial((W / 2, H / 2), H * 0.72, [skia.Color(*color, 0), skia.Color(*color, 0),
                                                                  skia.Color(*color, strength)], [0.0, 0.55, 1.0])
    c.drawPaint(skia.Paint(Shader=sh))


def flash(c, t, at, dur=0.18, color=(255, 230, 180)):
    if at <= t < at + dur:
        a = int(200 * (1 - (t - at) / dur))
        c.drawPaint(skia.Paint(Color=skia.Color(*color, a), BlendMode=skia.BlendMode.kPlus))


def impact_lines(c, t, t0, dur=0.3, cx=W / 2, cy=H * 0.45, color=(255, 255, 255)):
    if not (t0 <= t < t0 + dur):
        return
    a = (t - t0) / dur
    for i in range(18):
        ang = i * math.pi * 2 / 18 + 0.1
        r0 = 260 + a * 300
        r1 = r0 + 160 * (1 - a)
        c.drawLine(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang), cx + r1 * math.cos(ang), cy + r1 * math.sin(ang),
                   skia.Paint(AntiAlias=True, Color=col(color + (int(220 * (1 - a)),)), StrokeWidth=10,
                              StrokeCap=skia.Paint.kRound_Cap))


def sparkles(c, t, pts, t0, dur=0.8, color=(255, 230, 120)):
    if not (t0 <= t < t0 + dur):
        return
    a = (t - t0) / dur
    for i, (x, y) in enumerate(pts):
        s = math.sin(min(1, a * 1.3) * math.pi) * (24 + 8 * (i % 3))
        p = skia.Path()
        for j in range(8):
            r = s if j % 2 == 0 else s * 0.3
            ang = j * math.pi / 4 + t * 2
            (p.moveTo if j == 0 else p.lineTo)(x + r * math.cos(ang), y + r * math.sin(ang))
        p.close()
        c.drawPath(p, skia.Paint(AntiAlias=True, Color=col(color)))


def banner(c, t, t0, t1, fn, w, h, y=0.18, scale=0.8):
    if not (t0 <= t < t1):
        return
    k = min(ease_back(clamp((t - t0) / 0.22), 1.8), 1 - ease_in(clamp((t - (t1 - 0.2)) / 0.2)))
    c.save()
    c.translate(W / 2, H * y)
    c.rotate(-3 + 3 * (1 - k))
    c.scale(scale * k, scale * k)
    c.translate(-w / 2, -h / 2)
    fn(c)
    c.restore()


def letterbox_slowmo(c, t):
    for t0, t1 in ((0.0, 1.25), (16.35, 17.55), (33.55, 34.5), (49.45, 51.95), (53.2, 54.85)):
        if t0 <= t < t1:
            k = min(ease(clamp((t - t0) / 0.2)), ease(clamp((t1 - t) / 0.2)))
            bh = 90 * k
            c.drawRect(skia.Rect(0, 0, W, bh), skia.Paint(Color=skia.Color(0, 0, 0, 230)))
            c.drawRect(skia.Rect(0, H - bh, W, H), skia.Paint(Color=skia.Color(0, 0, 0, 230)))


def overlays(c, t):
    flash(c, t, 3.64, 0.14)
    flash(c, t, 43.79, 0.15)
    impact_lines(c, t, 3.64, 0.3, color=(255, 210, 120))
    impact_lines(c, t, 19.95, 0.3)
    impact_lines(c, t, 23.92, 0.3)
    impact_lines(c, t, 40.34, 0.3)
    sparkles(c, t, [(W * 0.25, H * 0.35), (W * 0.72, H * 0.3), (W * 0.55, H * 0.2)], 33.61, 0.9)
    sparkles(c, t, [(W * 0.3, H * 0.3), (W * 0.7, H * 0.28)], 48.78, 0.8, (150, 220, 255))
    banner(c, t, 12.3, 13.05, T2.qingming_banner(), 1200, 300, y=0.16)
    if 24.77 <= t < 25.55:
        k = ease_back(clamp((t - 24.77) / 0.2), 2)
        T.text_c(c, '?', W * 0.62, H * 0.3, T.font('black', int(220 * k) + 1), (255, 214, 60), stroke=14)
    if 30.11 <= t < 30.9:
        T.text_c(c, 'LUCKILY', W / 2, H * 0.14, T.font('black', 96), (120, 230, 140), stroke=12)
    if 35.33 <= t < 36.2:
        T.text_c(c, 'UNLUCKILY', W / 2, H * 0.14, T.font('black', 96), (255, 110, 100), stroke=12)
    if 41.0 <= t < 42.35:
        vignette(c, 160, (20, 20, 60))
    letterbox_slowmo(c, t)
    vignette(c, 120)
    draw_caption(c, t)
