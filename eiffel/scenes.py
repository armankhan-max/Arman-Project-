"""Shot list for 'The Man Who Sold the Eiffel Tower Twice'.

Every shot is a function (t) -> Scene where t is GLOBAL time in seconds, so the
camera moves can be keyed straight to the word timings in words.json.
"""
import json
import math
import random
import numpy as np
import skia
from engine3d import (Camera, Scene, v3, rgb, clamp, ease, ease_out, ease_in, ease_back, lerp, W, H, INK, col, norm)
from chars import draw_char
import props2d as PR
import sets as S
import tex as T

WORDS = json.load(open(__file__.replace('scenes.py', 'words.json')))
DUR = 81.12

# ------------------------------------------------------------------ looks
LUSTIG = dict(body=rgb('#232a42'), suit=True, tie=rgb('#c0283a'), hat='fedora', hat_col=(28, 28, 36),
              stache='curl')
POISSON = dict(body=rgb('#8c5a34'), suit=True, bowtie=rgb('#2f74c0'), hair='combover', hair_col=(90, 60, 40),
               glasses=True, belly=1.25)
DEALERS = [
    dict(body=rgb('#5f7d4a'), hat='cap', hat_col=rgb('#3d4a30'), stache='walrus'),
    dict(body=rgb('#7d7f86'), hat='cap', hat_col=rgb('#45464c')),
    dict(body=rgb('#8a2f3a'), hair='side', hair_col=(40, 30, 25), stache='thin'),
    dict(body=rgb('#2f7f86'), hat='cap', hat_col=rgb('#1f4f55')),
    dict(body=rgb('#c49a2c'), hair='curly', hair_col=(120, 60, 30)),
]
NEW_DEALERS = [
    dict(body=rgb('#6a4c9c'), hat='beret', hat_col=rgb('#2a2a40'), stache='thin'),
    dict(body=rgb('#3f8a5a'), hat='beret', hat_col=rgb('#a83030')),
    dict(body=rgb('#b8643a'), hair='curly', hair_col=(40, 30, 25)),
    dict(body=rgb('#4a6aa8'), hat='tophat', hat_col=rgb('#2a2a30'), stache='walrus'),
    dict(body=rgb('#9a9a40'), hat='cap', hat_col=rgb('#5a5a20')),
    dict(body=rgb('#a83a6a'), hair='side', hair_col=(70, 40, 30), belly=1.2),
]
BUYER2 = dict(body=rgb('#3f6aa8'), hat='beret', hat_col=rgb('#a83030'), stache='thin', belly=1.1)
DOORMAN = dict(body=rgb('#a8262f'), suit=True, tie=rgb('#e8c060'), hat='tophat', hat_col=rgb('#a8262f'))
POLICE = dict(body=rgb('#1f3470'), hat='kepi', hat_col=rgb('#1f3470'), badge=True, belt=(30, 30, 30), stache='walrus',
              stache_col=(60, 40, 30))
PAINTER = dict(body=rgb('#e8e2d0'), hat='beret', hat_col=rgb('#2a2a40'), stache='thin')
CROWD = [dict(body=rgb(h), hat=hh, hat_col=rgb('#333333'), hair=hr) for h, hh, hr in [
    ('#a83a3a', 'cap', None), ('#3a7aa8', None, 'side'), ('#7aa83a', 'beret', None), ('#a8843a', None, 'curly'),
    ('#6a3aa8', 'cap', None), ('#3aa88a', None, 'side'), ('#c05a8a', 'beret', None), ('#5a5a5a', 'cap', None)]]


def blink(t, seed=0, eyes='dot'):
    ph = (t + seed * 1.37) % 3.3
    return 'shut' if ph < 0.09 else eyes


def bob(t, seed=0, amt=0.012):
    return 1 + amt * math.sin(t * 4.2 + seed)


def char(sc, look, pos, pose, h=1.75, shadow=True, depth_bias=0.0, layer=1):
    pos = v3(*pos)
    if shadow:
        sc.shadow((pos[0], pos[1], pos[2]), rx=0.32 * h / 1.75, rz=0.2 * h / 1.75)
    sc.billboard(pos, h, lambda c, look=look, pose=pose: draw_char(c, look, pose), depth_bias=depth_bias, layer=layer)


# ------------------------------------------------------------------ camera helpers
def catmull(p0, p1, p2, p3, u):
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


def path(keys, t):
    """keys: [(time, pos, target, fov, roll)] -> Camera params (smooth, never fully stops)."""
    ts = [k[0] for k in keys]
    if t <= ts[0]:
        i, u = 0, 0.0
    elif t >= ts[-1]:
        i, u = len(keys) - 2, 1.0
    else:
        i = max(j for j in range(len(ts) - 1) if ts[j] <= t)
        u = (t - ts[i]) / (ts[i + 1] - ts[i])
    k0, k1, k2, k3 = keys[max(i - 1, 0)], keys[i], keys[i + 1], keys[min(i + 2, len(keys) - 1)]
    out = []
    for j in range(1, 5):
        a = [np.array(k[j], float) if j < 3 else np.array([k[j] if len(k) > j else 0.0]) for k in (k0, k1, k2, k3)]
        out.append(catmull(*a, u))
    return out[0], out[1], float(out[2][0]), float(out[3][0])


def punch(t, at, amt=0.22, attack=0.06, hold=0.35, release=0.6):
    if t < at:
        return 0.0
    d = t - at
    if d < attack:
        return amt * ease_out(d / attack)
    if d < attack + hold:
        return amt
    return amt * (1 - ease(min(1, (d - attack - hold) / release)))


def shake(t, at, amp=18, dur=0.35, freq=38):
    if t < at or t > at + dur:
        return (0, 0)
    k = (1 - (t - at) / dur) ** 2 * amp
    return (k * math.sin((t - at) * freq * 6.28), k * math.cos((t - at) * freq * 5.1))


def drift(t, amp=0.04):
    return v3(amp * math.sin(t * 0.9), amp * math.sin(t * 1.3 + 1), 0)


def mkcam(keys, t, punches=(), shakes=(), handheld=0.03):
    pos, tgt, fov, roll = path(keys, t)
    f = 1.0
    for p in punches:
        f += punch(t, *p) if isinstance(p, tuple) else punch(t, p)
    sx, sy = 0, 0
    for s in shakes:
        dx, dy = shake(t, *s) if isinstance(s, tuple) else shake(t, s)
        sx += dx
        sy += dy
    tgt = tgt + drift(t, handheld)
    return Camera(pos, tgt, fov=fov / f, roll=roll, shake=(sx, sy))


def W_(word_index):
    return WORDS[word_index]['start']


def at(word):
    """time of first word whose text starts with `word` (after optional index hint)."""
    for w in WORDS:
        if w['w'].strip('.,?!').lower() == word.lower():
            return w['start']
    raise KeyError(word)


def at_n(word, n):
    k = 0
    for w in WORDS:
        if w['w'].strip('.,?!').lower() == word.lower():
            if k == n:
                return w['start']
            k += 1
    raise KeyError((word, n))


SKY_DAY = (rgb('#6fa8e0'), rgb('#f6dcb4'))
SKY_DUSK = (rgb('#3a2f6a'), rgb('#f08a4a'))
SKY_NIGHT = (rgb('#0f1838'), rgb('#3a3f7a'))
FOG_DAY = (rgb('#e6e6ea'), 30, 150)


# ================================================================== SHOTS
def sh_hook(t):
    keys = [(0.0, (0.5, 1.2, -4.3), (0.0, 4.2, 20), 62), (2.0, (0.2, 1.25, -3.8), (0.0, 4.3, 20), 60),
            (4.1, (-0.3, 1.35, -3.3), (0.0, 4.4, 20), 58)]
    cam = mkcam(keys, t, punches=[(1.31, 0.12, 0.05, 0.2, 0.5), (3.01, 0.24)], shakes=[(1.36, 14), (3.05, 22)])
    sc = Scene(cam, bg=SKY_DAY, fog=FOG_DAY)
    S.paris(sc)
    S.lamp_post(sc, (-4.5, 0, 6))
    S.lamp_post(sc, (4.5, 0, 6))
    # sign post with SOLD sign that drops in on "Tower."
    tdrop = 1.12
    dy = 0 if t >= tdrop + 0.18 else (6 * (1 - ease_in((t - tdrop) / 0.18)) if t >= tdrop else 99)
    sc.box((0, 0.9, 1.6), (0.12, 1.8, 0.12), rgb('#5a3a22'))
    if dy < 50:
        sc.quad_tex(v3(-0.95, 2.75 + dy, 1.5), v3(1.9, 0, 0), v3(0, -1.14, 0), T.sold_sign(False), 600, 360, lw=4,
                    shade=False)
    if t >= 3.0:
        k = ease_back(min(1, (t - 3.0) / 0.16), 2.2)
        sc.quad_tex(v3(-1.15 * k, 2.2 + 0.4 * k, 1.42), v3(2.3 * k, 0, 0), v3(0, -1.2 * k, 0), T.stamp_again(), 700, 360,
                    outline=False, shade=False, depth_bias=-0.3)
    # Lustig (left) and buyer (right): handshake; buyer swaps at "came back"
    lp = dict(eyes=blink(t, 1, 'half'), brows='sly', mouth='smirk', arms=(20, -100), sq=bob(t))
    if t > 2.05:
        lp = dict(eyes='wink' if 2.3 < t < 2.9 else 'half', brows='sly', mouth='smirk', arms=(20, -100), sq=bob(t))
    char(sc, LUSTIG, (-0.62, 0, 0.0), lp)
    if t < 2.0:
        pp = dict(eyes=blink(t, 2, 'closed' if t > 1.35 else 'dot'), mouth='grin' if t > 1.35 else 'smile',
                  arms=(100, -20), sq=bob(t, 2), hold_l=lambda c: PR.money_bag(c, '₣'))
        char(sc, POISSON, (0.62, 0, 0.1), pp)
    else:
        k = ease_out((t - 2.05) / 0.35)
        x = lerp(3.0, 0.62, k)
        bp = dict(eyes='money' if t > 3.05 else 'dot', mouth='grin' if t > 3.05 else 'smile', arms=(100, -20),
                  walk=(t * 3) if k < 1 else None, sq=bob(t, 3), hold_l=lambda c: PR.money_bag(c, '₣'))
        char(sc, BUYER2, (x, 0, 0.1), bp)
    return sc


def sh_1925(t):
    keys = [(4.0, (-6.5, 1.6, -2.0), (-1.0, 2.2, 6.0), 52), (5.9, (-2.6, 1.8, -1.0), (-1.2, 2.4, 8.0), 50),
            (7.2, (1.6, 5.6, 17.0), (2.0, 7.0, 31.0), 54), (8.3, (1.9, 6.6, 21.5), (2.0, 7.0, 31.0), 50)]
    cam = mkcam(keys, t, punches=[(4.58, 0.12), (7.37, 0.22)], shakes=[(7.4, 10)])
    sc = Scene(cam, bg=SKY_DAY, fog=FOG_DAY)
    S.paris(sc)
    S.morris_column(sc, (-1.6, 0, 4.0))
    # people strolling
    for i, (x, z, lk) in enumerate([(3.0, 6, CROWD[1]), (-4.0, 12, CROWD[2]), (5.0, 15, CROWD[4])]):
        char(sc, lk, (x + math.sin(t * 0.5 + i) * 0.6, 0, z), dict(eyes=blink(t, i), walk=t * 1.6 + i, arms=(25, -25)))
    # big TEMPORARY tag swinging on a string from the first platform
    sw = math.sin(t * 2.4) * 0.12
    top = v3(2.0, 10.6, 31.0)
    cx, sx_ = math.cos(sw), math.sin(sw)
    U = v3(4.2 * cx, 4.2 * sx_, 0)
    V = v3(2.6 * sx_, -2.6 * cx, 0)
    O = top + v3(-2.1 * cx, -1.2, 0) - U * 0.0
    sc.poly([top, top + v3(0.02, 0, 0), O + U * 0.12 + V * 0.5], rgb('#3a2a20'), outline=False, normal=None)
    sc.quad_tex(O, U, V, T.temp_tag(), 420, 260, lw=3, shade=False, depth_bias=-0.5)
    return sc


def sh_rust(t):
    keys = [(8.1, (-19.0, 3.0, 12.0), (-7.0, 6.5, 31.0), 50), (9.5, (-17.5, 3.6, 14.5), (-8.2, 5.5, 29.0), 48),
            (11.5, (-15.0, 4.2, 18.0), (-8.6, 5.2, 28.6), 44)]
    cam = mkcam(keys, t, punches=[(8.63, 0.14), (10.02, 0.16)])
    sc = Scene(cam, bg=SKY_DAY, fog=FOG_DAY)
    rust = round(clamp((t - 8.3) / 0.9) * 4) / 4
    S.ground(sc, T.cobble(), size=120, rep=30, center=(0, 30))
    S.tower(sc, (0, 0, 40), 1.0, rust)
    # painter hanging from a rope with a tiny brush; the bill unrolls (2D overlay)
    if t > 9.4:
        k = ease_out((t - 9.4) / 0.5)
        yy = lerp(11, 4.1, k) + math.sin(t * 3) * 0.05
        rope_top = v3(-8.6, 11, 28.6)
        sc.poly([rope_top, rope_top + v3(0.03, 0, 0), v3(-8.57, yy + 1.7, 28.6)], rgb('#e8e0c8'), outline=False,
                normal=None)
        char(sc, PAINTER, (-8.6, yy, 28.6), dict(eyes='worried' if False else 'dot', brows='worried', mouth='frown',
                                                  sit=True, arms=(80, -150), hold=PR.brush, hold_l=PR.bucket,
                                                  sweat=True), h=1.5, shadow=False)
    return sc


def sh_news(t):
    keys = [(11.3, (0.0, 7.5, -0.6), (0.0, 0.0, 0.25), 55), (13.0, (0.0, 4.6, -0.3), (0.0, 0.0, 0.2), 52),
            (14.75, (0.0, 2.6, -0.15), (0.0, 0.0, 0.1), 50)]
    cam = mkcam(keys, t, punches=[(13.83, 0.25)], shakes=[(13.86, 16)])
    cam.roll = 0
    sc = Scene(cam, bg=(150, 140, 130))
    S.ground(sc, T.cobble(), size=24, rep=12, center=(0, 0))
    rnd = random.Random(7)
    land = [11.58, 11.77, 12.0, 12.36, 12.6, 12.91]
    for i, tl in enumerate(land):
        if t < tl - 0.5:
            continue
        k = ease_out(clamp((t - (tl - 0.5)) / 0.5))
        x, z = rnd.uniform(-1.6, 1.6), rnd.uniform(-1.2, 2.2)
        rot = rnd.uniform(-0.9, 0.9) + (1 - k) * 3
        if i == len(land) - 1:
            x, z, rot = 0.0, 0.0, -0.06 + (1 - k) * 2.5
        y = 0.02 + i * 0.004 + (1 - k) * 5
        w, h = 1.6, 2.08
        U = v3(w * math.cos(rot), 0, w * math.sin(rot))
        V = v3(-h * math.sin(rot), 0, h * math.cos(rot))
        O = v3(x, y, z) - U / 2 + V / 2
        sc.quad_tex(O, U, -V, T.newspaper(0 if i == len(land) - 1 else 1 + i % 4), 1000, 1300, lw=2, shade=False,
                    depth_bias=-i * 0.01)
    return sc


def sh_intro(t):
    # newspaper lowers to reveal Lustig on a bench, tower behind
    keys = [(14.6, (0.0, 1.45, -2.2), (0.0, 1.45, 4.0), 46), (17.6, (0.15, 1.35, -1.75), (0.0, 1.5, 4.0), 44)]
    cam = mkcam(keys, t, punches=[(16.40, 0.12)])
    sc = Scene(cam, bg=SKY_DAY, fog=(rgb('#e6e6ea'), 20, 120))
    S.ground(sc, T.grass(), size=160, rep=40, center=(0, 40))
    S.tower(sc, (6, 0, 90), 1.0)
    for x in (-3.5, 3.0):
        sc.cyl((x, 0, 6), 0.18, 2.4, rgb('#6b4a2a'), seg=8)
        for k in range(4):
            sc.cyl((x + math.sin(k) * 0.4, 2.2 + k * 0.25, 6 + math.cos(k) * 0.3), 1.1 - k * 0.15, 0.9, rgb('#5f9a4a'), seg=10, r2=0.5)
    # bench
    sc.box((0, 0.48, 0.25), (2.2, 0.08, 0.5), rgb('#7a4b2a'))
    sc.box((0, 0.85, 0.5), (2.2, 0.5, 0.06), rgb('#7a4b2a'))
    for x in (-1.0, 1.0):
        sc.box((x, 0.24, 0.25), (0.08, 0.48, 0.45), rgb('#2a2a30'))
    k = ease(clamp((t - 14.95) / 0.55))
    ny = lerp(1.0, -0.42, k)
    lp = dict(eyes='half' if t > 15.4 else 'dot', brows='sly' if t > 15.4 else 'flat', mouth='smirk' if t > 15.5 else 'flat',
              sit=True, arms=((60, 140), (-60, -140)), sq=bob(t))
    char(sc, LUSTIG, (0, 0.0, 0.2), lp, h=1.6, shadow=False)
    sc.quad_tex(v3(-0.62, ny + 1.25, -0.05), v3(1.24, 0, 0), v3(0, -lerp(1.0, 0.5, k), 0), T.newspaper(0), 1000, 1300, lw=2,
                shade=False, depth_bias=-0.5)
    return sc


def sh_letter(t):
    keys = [(17.4, (0.9, 2.3, -1.2), (0.0, 0.8, 0.4), 44), (19.8, (0.35, 1.9, -0.75), (0.0, 0.8, 0.45), 42)]
    beats = [17.83, 18.09, 18.58]
    cam = mkcam(keys, t, punches=[(b, 0.06, 0.03, 0.05, 0.25) for b in beats], shakes=[(b + 0.03, 10, 0.2) for b in beats])
    sc = Scene(cam, bg=(20, 18, 28), ambient=0.75)
    S.room(sc, w=6, d=6, h=3, z0=-3, wall=T.wallpaper((40, 46, 70), (48, 54, 82)), floor=T.planks((90, 60, 40)))
    S.table(sc, (0, 0, 0.4), w=2.4, d=1.4)
    # lamp
    sc.cyl((0.85, 0.82, 0.8), 0.12, 0.04, rgb('#2a2a30'), seg=10)
    sc.box((0.85, 1.05, 0.8), (0.03, 0.45, 0.03), rgb('#2a2a30'))
    sc.cyl((0.85, 1.25, 0.8), 0.22, 0.18, rgb('#2f6a4a'), seg=12, r2=0.08)
    for i, b in enumerate(beats):
        if t < b - 0.25:
            continue
        k = ease_out(clamp((t - (b - 0.25)) / 0.22))
        x = lerp(-1.6, -0.45 + i * 0.32, k)
        rot = -0.15 + i * 0.12
        U = v3(0.5 * math.cos(rot), 0, 0.5 * math.sin(rot))
        V = v3(-0.64 * math.sin(rot), 0, 0.64 * math.cos(rot))
        O = v3(x, 0.83 + i * 0.002, 0.25) - U / 2 + V / 2
        sc.quad_tex(O, U, -V, T.letterhead(t > b), 700, 900, lw=1.5, shade=False)
    # stamp moving to current sheet then slamming
    cur = max([i for i, b in enumerate(beats) if t >= b - 0.25] or [0])
    b = beats[cur]
    lift = 0.06 if t >= b else 0.06 + 0.5 * ease_out(clamp((b - t) / 0.25))
    if t > b + 0.08:
        lift = 0.06 + 0.4 * ease_out(clamp((t - b - 0.08) / 0.2))
    sx = -0.45 + cur * 0.32 + 0.05
    sc.box((sx, 0.83 + lift, 0.3), (0.26, 0.08, 0.2), rgb('#3a2a20'))
    sc.cyl((sx, 0.87 + lift, 0.3), 0.04, 0.2, rgb('#8a5a30'), seg=8)
    sc.cyl((sx, 1.07 + lift, 0.3), 0.07, 0.07, rgb('#a83030'), seg=10)
    return sc


def hotel_set(sc, t):
    S.ground(sc, T.cobble(), size=120, rep=30, center=(0, 20))
    S.tower(sc, (-30, 0, 120), 1.0)
    # facade
    sc.quad_tex4([v3(-9, 15, 6), v3(9, 15, 6), v3(9, 0, 6), v3(-9, 0, 6)], T.haussmann(1, True), 512, 640, lw=4)
    sc.quad_tex4([v3(-27, 15, 6), v3(-9, 15, 6), v3(-9, 0, 6), v3(-27, 0, 6)], T.haussmann(2, False), 512, 640, lw=4)
    sc.quad_tex4([v3(9, 15, 6), v3(27, 15, 6), v3(27, 0, 6), v3(9, 0, 6)], T.haussmann(0, False), 512, 640, lw=4)
    sc.quad_tex(v3(-2.6, 4.3, 5.9), v3(5.2, 0, 0), v3(0, -1.22, 0), T.hotel_sign(), 1100, 260, lw=3, shade=False)
    # door & awning & carpet
    sc.poly([v3(-1.1, 0, 5.95), v3(1.1, 0, 5.95), v3(1.1, 2.8, 5.95), v3(-1.1, 2.8, 5.95)], rgb('#2a1a14'), normal=(0, 0, -1),
            depth_bias=-0.1)
    sc.poly([v3(-1.0, 0.0, 5.93), v3(1.0, 0, 5.93), v3(1.0, 2.7, 5.93), v3(-1.0, 2.7, 5.93)], rgb('#ffd98a'), normal=None,
            depth_bias=-0.12, outline=False)
    sc.box((0, 2.95, 4.9), (3.2, 0.15, 2.2), rgb('#a8262f'), top=rgb('#c0303a'))
    sc.poly([v3(-0.9, 0.01, -6), v3(0.9, 0.01, -6), v3(0.9, 0.01, 5.9), v3(-0.9, 0.01, 5.9)], rgb('#b0222c'), layer=0,
            normal=(0, 1, 0))
    for x in (-1.6, 1.6):
        sc.cyl((x, 0, 5.4), 0.25, 0.6, rgb('#d9b24a'), seg=10, r2=0.3)
        sc.cyl((x, 0.6, 5.4), 0.35, 0.7, rgb('#4a8a3a'), seg=10, r2=0.1)


def sh_hotel(t, back=False):
    t0 = 19.7 if not back else 69.55
    lt = t - t0
    keys = [(0.0, (0.0, 1.4, -7.5), (0.0, 2.8, 6), 56), (1.6, (0.0, 1.8, -6.0), (0.0, 3.4, 6), 54),
            (2.9, (0.0, 4.6, -2.4), (0.0, 7.3, 6), 46)]
    if back:
        keys = [(0.0, (0.0, 1.4, -7.5), (0.0, 2.8, 6), 56), (1.9, (0.0, 1.8, -5.6), (0.0, 3.2, 6), 52)]
    cam = mkcam(keys, lt, punches=[(0.95 if not back else 1.0, 0.1)])
    sc = Scene(cam, bg=SKY_DAY, fog=FOG_DAY)
    hotel_set(sc, t)
    # Lustig walks to the door
    k = clamp(lt / 1.5)
    x = lerp(-4.2, -0.2, ease(k))
    z = lerp(-2.0, 4.6, ease(k))
    sc_ = 1.0 if lt < 1.6 else max(0.0, 1 - (lt - 1.6) / 0.25)
    if sc_ > 0:
        char(sc, LUSTIG, (x, 0, z), dict(eyes='wink' if back and lt > 0.9 else 'half', brows='sly', mouth='smirk',
                                          walk=lt * 2.4 if k < 1 else None, arms=(10, -30),
                                          hold=lambda c: PR.suitcase(c)))
    bow = clamp((lt - 1.0) / 0.3)
    char(sc, DOORMAN, (1.5, 0, 5.0), dict(eyes='closed' if bow > 0 else 'dot', mouth='smile', tilt=-18 * bow,
                                          arms=(30, -100 * bow - 10)))
    return sc


def sh_hotel_back(t):
    return sh_hotel(t, back=True)


# ---------------------------------------------------------------- the suite
# long table along z; dealers on both sides, Lustig stands at the far end
SEATS = [(-0.85, -0.4), (-0.85, 0.6), (-0.85, 1.6), (0.85, -0.4), (0.85, 0.6), (0.85, 1.6)]
HEAD = (0.0, 0, 3.0)
POI = SEATS[1]


def suite_set(sc, t, dealers, curtains=0.0, dim=0.0, easel=0, lustig_pose=None, lustig_pos=HEAD,
              hook=None, show_lustig=True, show_dealers=True, note=False):
    S.room(sc, w=9, d=9, h=4.2, z0=-5, wall=T.wallpaper(), floor=T.carpet())
    S.wall_window(sc, -3.4, 1.0, 3.98, 1.9, 2.6, curtains=curtains)
    S.wall_window(sc, 1.5, 1.0, 3.98, 1.9, 2.6, curtains=curtains)
    S.frame_pic(sc, -0.75, 2.2, 3.98, 1.5, 1.1)
    S.chandelier(sc, (0, 3.4, 0.6))
    S.table(sc, (0, 0, 0.6), w=1.0, d=3.4, cloth=rgb('#e8e0cc'))
    ex, ez = 1.25, 3.45
    sc.box((ex - 0.45, 0.9, ez), (0.05, 1.8, 0.05), rgb('#6b4a2a'))
    sc.box((ex + 0.45, 0.9, ez), (0.05, 1.8, 0.05), rgb('#6b4a2a'))
    sc.quad_tex(v3(ex - 0.6, 2.25, ez - 0.05), v3(1.2, 0, 0), v3(0, -1.5, 0), T.easel(easel), 800, 1000, lw=3, shade=False)
    for i, (x, z) in enumerate(SEATS):
        S.chair(sc, (x, 0, z), back=(-1 if x < 0 else 1, 0))
    if show_dealers:
        for i, d in enumerate(dealers):
            if d is None:
                continue
            look, pose = d
            x, z = SEATS[i]
            char(sc, look, (x, 0, z), pose, h=1.6, shadow=False, depth_bias=-0.05)
    if show_lustig and lustig_pose is not None:
        char(sc, LUSTIG, lustig_pos, lustig_pose)
    if hook is not None:
        sc.billboard(v3(*hook), 1.6, PR.contract_hook, depth_bias=-1)
    if note:
        sc.quad_tex(v3(-0.4, 0.84, 1.8), v3(0.8, 0, 0), v3(0, 0, -0.5), T.au_revoir(), 800, 500, lw=2, shade=False, depth_bias=-0.6)
    if dim > 0:
        sc.ambient = lerp(0.62, 0.45, dim)


def dealer_poses(t, look_list, appear=None, eyes=None, lean=0.0, mouth=None):
    out = []
    for i, lk in enumerate(look_list):
        if appear is not None and t < appear[i]:
            out.append(None)
            continue
        pop = 1.0 if appear is None else ease_back(clamp((t - appear[i]) / 0.18))
        e = eyes(i) if callable(eyes) else (eyes or blink(t, i + 3))
        out.append((lk, dict(eyes=e, mouth=mouth or 'flat', sit=True, arms=(60, -60), sq=max(0.05, pop) * bob(t, i),
                             tilt=lean * (-1 if SEATS[i][0] < 0 else 1) * 12, brows='flat')))
    return out


def meeting_dealers(t, poisson_pose=None, appear=None, eyes=None, lean=0.0, mouth=None, hide=()):
    looks = [DEALERS[0], POISSON] + DEALERS[1:5]
    d = dealer_poses(t, looks, appear, eyes, lean, mouth)
    for h in hide:
        d[h] = None
    if poisson_pose is not None and d[1] is not None:
        pp = dict(sit=True, arms=(60, -60))
        pp.update(poisson_pose)
        d[1] = (POISSON, pp)
    return d


def sh_meet(t):
    # 22.55 - 25.65: high corner wide shot, dealers pop into chairs, curtains close
    keys = [(22.4, (2.8, 3.4, -4.4), (0.0, 0.9, 1.4), 58), (24.0, (1.6, 2.8, -4.2), (0.0, 1.0, 1.6), 56),
            (25.8, (0.4, 2.0, -3.9), (0.0, 1.2, 2.0), 52)]
    cam = mkcam(keys, t, punches=[(25.09, 0.1)])
    sc = Scene(cam, bg=(30, 20, 20))
    appear = [23.25 + i * 0.2 for i in range(6)]
    cur = ease(clamp((t - 24.7) / 0.6))
    lp = dict(eyes=blink(t, 1, 'half'), brows='sly', mouth='smirk', arms=(20, -160 if t > 24.6 else -30), sq=bob(t))
    suite_set(sc, t, meeting_dealers(t, appear=appear), curtains=cur, dim=cur, lustig_pose=lp,
              lustig_pos=(lerp(-2.4, 0.0, ease(clamp((t - 22.8) / 1.2))), 0, 3.0))
    return sc


def sh_whisper(t):
    keys = [(25.6, (0.0, 2.0, -3.4), (0.0, 1.2, 2.0), 56), (28.7, (0.1, 1.7, -2.2), (0.1, 1.35, 2.4), 50)]
    cam = mkcam(keys, t, punches=[(27.42, 0.16)], shakes=[(27.45, 12)])
    sc = Scene(cam, bg=(30, 20, 20), ambient=0.48)
    stage = 1 if t > 27.42 else 0
    lean = ease(clamp((t - 26.8) / 0.4))
    lp = dict(eyes='half', brows='sly', mouth='smirk', arms=(20, (-120, -170)) if t < 27.3 else (20, (-150, -110)),
              tilt=-8 * lean, sq=bob(t))
    suite_set(sc, t, meeting_dealers(t, eyes=lambda i: 'wide' if t > 27.5 else blink(t, i + 3), lean=lean * 1.5),
              curtains=1, dim=1, easel=stage, lustig_pose=lp)
    return sc


def sh_tons(t):
    keys = [(28.6, (-0.5, 1.5, -1.6), (0.6, 1.6, 3.2), 50), (31.9, (-0.2, 1.4, -0.2), (0.7, 1.55, 3.2), 44)]
    cam = mkcam(keys, t, punches=[(28.7, 0.1), (29.8, 0.12), (31.12, 0.28)], shakes=[(31.15, 24)])
    sc = Scene(cam, bg=(30, 20, 20), ambient=0.48)
    stage = 3 if t > 30.4 else 2
    g = -60 if t < 30.95 else (-60 + 120 * ease_out(clamp((t - 30.95) / 0.12)))
    lp = dict(eyes='half', brows='sly', mouth='smirk' if t < 31.1 else 'grin',
              arms=(20, (-150 + (g + 60) * 0.6, -150 + (g + 60))), hold=lambda c: PR.gavel(c, 90), sq=bob(t))
    money = t > 29.8
    suite_set(sc, t, meeting_dealers(t, eyes=lambda i: 'money' if money else blink(t, i + 3),
                                     mouth='grin' if money else 'flat'),
              curtains=1, dim=1, easel=stage, lustig_pose=lp, lustig_pos=(-0.15, 0, 3.0))
    return sc


def sh_shh(t):
    keys = [(31.8, (0.05, 1.45, 1.0), (0.0, 1.42, 3.0), 44), (34.2, (0.0, 1.45, 1.45), (0.0, 1.42, 3.0), 40)]
    cam = mkcam(keys, t, punches=[(33.19, 0.12)])
    sc = Scene(cam, bg=(30, 20, 20), ambient=0.45)
    lp = dict(eyes='half' if t < 33.1 else 'squint', brows='sly', mouth='flat',
              arms=(20, (-160, -175)) if t > 32.0 else (20, -40), sq=bob(t), tilt=4)
    suite_set(sc, t, meeting_dealers(t), curtains=1, dim=1, easel=3, lustig_pose=lp, show_dealers=False)
    return sc


def sh_riot(t):
    keys = [(34.1, (0.0, 2.4, -2.0), (0.0, 7.0, 30), 60), (35.6, (0.0, 1.9, -0.8), (0.0, 7.5, 30), 56)]
    cam = mkcam(keys, t, punches=[(34.81, 0.2)], shakes=[(34.2, 10, 1.4, 9), (34.85, 26)])
    sc = Scene(cam, bg=SKY_DUSK, fog=(rgb('#a05a5a'), 25, 140), ambient=0.5)
    S.paris(sc)
    rnd = random.Random(11)
    for i in range(16):
        x = rnd.uniform(-4.5, 4.5)
        z = rnd.uniform(3, 14)
        lk = CROWD[i % len(CROWD)]
        jump = abs(math.sin(t * 9 + i)) * 0.25
        prop = (lambda c, t=t: PR.torch(c, t)) if i % 2 == 0 else PR.pitchfork
        char(sc, lk, (x, jump, z), dict(eyes='squint', brows='angry', mouth='shout', arms=(30, -165 + 15 * math.sin(t * 12 + i)),
                                         hold=prop, red=0.35), h=1.6)
    return sc


PX, PZ = POI
PHEAD = v3(PX, 1.3, PZ)


def sh_poisson(t):
    # 35.52 - 40.72 dolly to Poisson; name card; takes the bait; suspicious
    keys = [(35.5, (1.2, 1.8, -2.8), (-0.5, 1.2, 1.0), 52), (36.7, (0.95, 1.45, -1.0), (PX, 1.3, PZ), 46),
            (38.5, (0.85, 1.4, -0.6), (PX, 1.3, PZ), 44), (40.8, (0.75, 1.38, -0.4), (PX, 1.32, PZ), 42, 7)]
    cam = mkcam(keys, t, punches=[(38.44, 0.12), (39.84, 0.14)])
    sc = Scene(cam, bg=(30, 20, 20), ambient=0.48)
    hook = None
    if 37.6 < t < 39.3:
        hy = lerp(4.2, 1.95, ease_out(clamp((t - 37.6) / 0.45)))
        if t > 38.45:
            hy = lerp(1.95, 4.5, ease_in(clamp((t - 38.6) / 0.6)))
        hook = (PX + 0.32, hy, PZ - 0.1)
    bait = t > 38.44
    greedy = 38.0 < t < 39.3
    pp = dict(eyes='money' if greedy else blink(t, 5), mouth='grin' if greedy else 'flat',
              arms=(60, -150 if 38.3 < t < 38.6 else -60), hold=PR.paper if bait else None)
    if t > 39.35:
        pp.update(eyes='squint', brows='angry', mouth='flat', tilt=6, hold=PR.paper)
    suite_set(sc, t, meeting_dealers(t, poisson_pose=pp, hide=(3, 4)), curtains=1, dim=1, easel=3,
              lustig_pose=dict(eyes='half', brows='sly', mouth='smirk', arms=(20, -30)), hook=hook)
    return sc


def sh_hurry(t):
    # 40.72 - 43.0 Lustig glances at his watch, sweating
    keys = [(40.7, (-0.3, 1.45, 0.9), (0.0, 1.4, 3.0), 46), (43.1, (-0.2, 1.42, 1.3), (0.0, 1.42, 3.0), 42)]
    cam = mkcam(keys, t, punches=[(42.39, 0.14)])
    sc = Scene(cam, bg=(30, 20, 20), ambient=0.48)
    lp = dict(eyes='wide' if t > 41.6 else 'dot', brows='worried', mouth='flat', arms=(20, (-120, -170)), hold=PR.watch,
              sweat=t > 41.6, py=2, sq=bob(t))
    suite_set(sc, t, meeting_dealers(t, poisson_pose=dict(eyes='squint', brows='angry', mouth='flat')), curtains=1, dim=1,
              easel=3, lustig_pose=lp, show_dealers=False)
    return sc


LEAN_POS = (PX - 0.15, 0, PZ + 0.75)


def sh_lean(t):
    # 43.0 - 45.84 Lustig walks over and leans in behind Poisson
    keys = [(43.0, (1.0, 1.5, -1.6), (-0.6, 1.3, 1.6), 48), (45.9, (0.95, 1.45, -0.7), (PX, 1.35, PZ + 0.35), 44)]
    cam = mkcam(keys, t, punches=[(45.23, 0.12)])
    sc = Scene(cam, bg=(30, 20, 20), ambient=0.48)
    k = ease(clamp((t - 43.2) / 0.9))
    lx = lerp(HEAD[0], LEAN_POS[0], k)
    lz = lerp(HEAD[2], LEAN_POS[2], k)
    rub = t > 44.9
    lp = dict(eyes='half', brows='sly', mouth='smirk', tilt=14 * k,
              arms=(20, (-110, -150 + (8 * math.sin(t * 30) if rub else 0))),
              walk=t * 2.5 if 0 < k < 1 else None, sq=bob(t))
    pp = dict(eyes='squint' if t < 45.3 else 'wide', brows='angry' if t < 45.3 else 'up', mouth='flat' if t < 45.3 else 'o')
    suite_set(sc, t, meeting_dealers(t, poisson_pose=pp, hide=(3, 4)), curtains=1, dim=1, easel=3, lustig_pose=lp,
              lustig_pos=(lx, 0, lz))
    return sc


def sh_wait(t):
    # 45.84 - 49.56 snap zoom on Poisson: Wait, a bribe? Well... that's what convinced him.
    keys = [(45.8, (0.8, 1.38, -0.3), (PX, 1.32, PZ), 42), (49.7, (0.7, 1.38, -0.15), (PX, 1.32, PZ), 40)]
    cam = mkcam(keys, t, punches=[(46.02, 0.35, 0.04, 0.6, 0.4), (46.95, 0.12), (48.36, 0.1)], shakes=[(46.05, 16)])
    sc = Scene(cam, bg=(30, 20, 20), ambient=0.5)
    if t < 47.6:
        pp = dict(eyes='wide', brows='up', mouth='o', sq=1.0 + 0.03 * math.sin(t * 20))
    elif t < 48.3:
        pp = dict(eyes='roll', brows='flat', mouth='flat', tilt=8)
    else:
        pp = dict(eyes='closed', brows='up', mouth='grin', arms=(60, -170), blush=0.8)
    suite_set(sc, t, meeting_dealers(t, poisson_pose=pp, hide=(3, 4)), curtains=1, dim=1, easel=3,
              lustig_pose=dict(eyes='half', brows='sly', mouth='smirk', tilt=14), lustig_pos=LEAN_POS)
    return sc


def sh_corrupt(t):
    # 49.56 - 52.45 orbit, Poisson nodding, Lustig grinning behind him
    keys = [(49.5, (0.95, 1.5, -0.9), (PX, 1.4, PZ + 0.4), 50), (52.6, (0.7, 1.6, 2.5), (PX, 1.4, PZ + 0.4), 48)]
    cam = mkcam(keys, t, punches=[(51.64, 0.16)])
    sc = Scene(cam, bg=(30, 20, 20), ambient=0.5)
    pp = dict(eyes='closed', brows='flat', mouth='smile', tilt=8 * math.sin(t * 7))
    lp = dict(eyes='half', brows='sly', mouth='grin' if t > 51.6 else 'smirk', tilt=10, arms=(20, -120))
    suite_set(sc, t, meeting_dealers(t, poisson_pose=pp, hide=(3, 4)), curtains=1, dim=1, easel=3, lustig_pose=lp,
              lustig_pos=LEAN_POS)
    return sc


def sh_pay(t):
    # 52.45 - 55.55 table macro: money bag + bribe bills slide down the table to Lustig
    keys = [(52.4, (0.35, 1.15, -0.9), (0.0, 0.9, 2.2), 46), (55.7, (0.25, 1.05, -0.3), (0.0, 0.95, 2.4), 42)]
    cam = mkcam(keys, t, punches=[(53.43, 0.12), (54.76, 0.14)], shakes=[(53.5, 10), (54.8, 10)])
    sc = Scene(cam, bg=(30, 20, 20), ambient=0.55)
    suite_set(sc, t, meeting_dealers(t), curtains=1, dim=1, easel=3, show_dealers=False,
              lustig_pose=dict(eyes='money', brows='sly', mouth='grin', arms=(20, -150)), lustig_pos=HEAD)
    k1 = ease_out(clamp((t - 52.9) / 0.5))
    k2 = ease_out(clamp((t - 54.4) / 0.4))
    sc.billboard(v3(-0.15, 0.82, lerp(0.3, 2.0, k1)), 0.8,
                 lambda c: (c.save(), c.translate(0, -26), PR.money_bag(c, '₣'), c.restore()))
    if t > 54.3:
        z = lerp(0.2, 1.7, k2)
        sc.quad_tex(v3(0.05, 0.835, z + 0.2), v3(0.4, 0, 0), v3(0, 0, -0.3), T.bill(), 400, 300, lw=1.5, shade=False)
    return sc


def _wheel(c):
    c.drawCircle(0, -50, 48, skia.Paint(AntiAlias=True, Color=skia.Color(170, 40, 40)))
    c.drawCircle(0, -50, 48, skia.Paint(AntiAlias=True, Color=INK, Style=skia.Paint.kStroke_Style, StrokeWidth=8))
    c.drawCircle(0, -50, 10, skia.Paint(AntiAlias=True, Color=INK))


def sh_train(t):
    lt = t - 55.55
    keys = [(0.0, (-6.5, 2.4, -9.5), (0.2, 1.6, 0.0), 50), (2.0, (-2.8, 2.2, -7.6), (0.2, 1.7, 0.0), 46),
            (4.1, (-0.6, 2.2, -5.6), (-0.2, 1.8, 0.0), 42)]
    cam = mkcam(keys, lt, punches=[(2.47, 0.16)], shakes=[(0, 3, 4.5, 6)])
    sc = Scene(cam, bg=SKY_DAY, fog=(rgb('#e8ece8'), 20, 120))
    v = 14.0
    off = (lt * v) % 40
    S.ground(sc, T.grass(), size=200, rep=50, center=(-off, 40))
    for zz in (-0.55, 0.55):
        sc.box((0, 0.05, zz), (120, 0.1, 0.08), rgb('#8a8a90'))
    for i in range(-30, 30):
        x = i * 1.2 - (lt * v) % 1.2
        sc.box((x, 0.02, 0), (0.25, 0.04, 1.6), rgb('#5a3a22'))
    for i in range(12):
        x = ((i * 9.0 - lt * v) % 108) - 40
        z = 7 + (i % 3) * 5
        sc.cyl((x, 0, z), 0.25, 1.8, rgb('#6b4a2a'), seg=6)
        sc.cyl((x, 1.6, z), 1.4, 2.2, rgb('#4f8a3a'), seg=8, r2=0.1)
    sx = 30 - lt * v + 2
    sc.box((sx, 1.1, -2.5), (0.15, 2.2, 0.15), rgb('#5a3a22'))
    sc.quad_tex(v3(sx - 1.4, 2.8, -2.6), v3(2.8, 0, 0), v3(0, -1.0, 0),
                lambda c: (c.drawRect(skia.Rect(0, 0, 560, 200), skia.Paint(Color=skia.Color(250, 245, 230))),
                           T.text_c(c, 'FRANCE  →  AUSTRIA', 280, 130, T.font('black', 58), (40, 40, 60))), 560, 200, lw=3,
                shade=False)
    bounce = 0.02 * math.sin(lt * 26)
    # locomotive
    sc.box((4.4, 1.25 + bounce, 0), (3.4, 1.5, 1.5), rgb('#2a2a34'), top=rgb('#3a3a46'))
    sc.box((2.9, 2.2 + bounce, 0), (1.3, 1.2, 1.5), rgb('#33333f'), top=rgb('#a83030'))
    sc.cyl((5.5, 2.0 + bounce, 0), 0.25, 0.9, rgb('#22222a'), seg=8)
    sc.box((6.2, 0.7, 0), (0.3, 0.6, 1.6), rgb('#a83030'))
    # carriage
    G = rgb('#3f8a5e')
    sc.box((-0.2, 1.45 + bounce, 0), (4.8, 1.9, 1.6), G, top=rgb('#4a4a52'), sides=('top', 'back', 'left', 'right'))
    b_ = bounce
    zf = -0.8
    def panel(x0, x1, y0, y1):
        sc.poly([v3(x0, y0 + b_, zf), v3(x1, y0 + b_, zf), v3(x1, y1 + b_, zf), v3(x0, y1 + b_, zf)], G, normal=(0, 0, -1))
    panel(-2.6, 2.2, 0.5, 1.35)
    panel(-2.6, 2.2, 2.25, 2.4)
    panel(-2.6, -1.4, 1.35, 2.25)
    panel(0.6, 1.0, 1.35, 2.25)
    panel(2.0, 2.2, 1.35, 2.25)
    sc.poly([v3(-2.6, 0.5 + b_, 0.75), v3(2.2, 0.5 + b_, 0.75), v3(2.2, 2.4 + b_, 0.75), v3(-2.6, 2.4 + b_, 0.75)],
            rgb('#ffe9b8'), normal=(0, 0, -1), outline=False)
    sc.box((-0.2, 0.55, 0), (4.6, 0.12, 1.5), rgb('#2a2a30'))
    for wx in (-1.8, 1.4, 3.4, 4.6, 5.6):
        sc.billboard(v3(wx, 0.05, -0.85), 0.9, lambda c, r=lt * 400: (c.rotate(0), _wheel(c)), depth_bias=-0.4)
    op = ease_out(clamp((t - 58.0) / 0.5))
    char(sc, LUSTIG, (-0.4, 0.55 + bounce, -0.2), dict(eyes='closed' if t > 58.0 else 'half', brows='sly', mouth='grin',
                                                        arms=(20, -150 + 10 * math.sin(t * 14)),
                                                        hold_l=lambda c, op=op: PR.suitcase(c, op)), h=1.55, shadow=False)
    for i in range(6):
        age = (lt * 1.5 + i / 6) % 1.0
        px = 5.5 - age * 7
        sc.billboard(v3(px, 2.9 + age * 1.8, 0), 0.6 + age * 1.4,
                     lambda c, a=age: c.drawCircle(0, -50, 50, skia.Paint(AntiAlias=True, Color=skia.Color(245, 245, 245, int(230 * (1 - a))))),
                     depth_bias=-0.2)
    if t > 58.2:
        rnd = random.Random(3)
        for i in range(12):
            a = clamp((t - 58.2 - i * 0.05) / 1.2)
            if a <= 0:
                continue
            x = -0.6 - a * 5 + rnd.uniform(-0.4, 0.4)
            y = 2.2 + a * 1.4 + math.sin(t * 9 + i) * 0.2
            sc.billboard(v3(x, y, -1.0 - rnd.uniform(0, 1)), 0.3,
                         lambda c, i=i, t=t: (c.rotate(t * 300 + i * 40),
                                              c.drawRect(skia.Rect(-60, -40, 60, 40), skia.Paint(Color=skia.Color(150, 200, 140))),
                                              c.drawRect(skia.Rect(-60, -40, 60, 40), skia.Paint(Color=skia.Color(60, 110, 60), Style=skia.Paint.kStroke_Style, StrokeWidth=6))))
    return sc


def sh_papers(t):
    keys = [(59.5, (-1.2, 1.6, -1.8), (0.0, 1.3, 1.2), 50), (62.2, (-0.6, 1.5, -1.2), (0.0, 1.3, 1.2), 44),
            (62.3, (0.0, 1.32, 0.15), (0.0, 1.32, 1.2), 40), (64.4, (0.0, 1.35, -0.6), (0.0, 1.35, 1.2), 44)]
    cam = mkcam(keys, t, punches=[(62.28, 0.25, 0.04, 0.5, 0.3), (63.9, 0.12)])
    sc = Scene(cam, bg=(30, 30, 50), ambient=0.6)
    S.room(sc, w=7, d=7, h=3.5, z0=-4, wall=T.wallpaper((52, 74, 110), (60, 84, 122)), floor=T.planks())
    S.wall_window(sc, -2.8, 1.0, 2.98, 1.4, 1.8)
    S.table(sc, (0, 0, 1.0), w=2.0, d=1.2)
    # calendar flipping every day
    day = int(clamp((t - 60.96) / 0.22, 0, 6))
    sc.quad_tex(v3(1.2, 2.6, 2.97), v3(1.0, 0, 0), v3(0, -0.72, 0), T.calendar(day), 700, 500, lw=2, shade=False)
    # stack of newspapers grows
    n = int(clamp((t - 59.8) / 0.3, 0, 8))
    for i in range(n):
        sc.box((-0.6, 0.84 + i * 0.03, 1.0), (0.6, 0.03, 0.75), rgb('#eae4d2'))
    # Lustig reading, newspaper up in front of face
    up = t < 63.4
    lp = dict(eyes='half', brows='sly' if t > 63.4 else 'flat', mouth='grin' if t > 63.7 else ('smirk' if t > 63.4 else 'flat'),
              sit=True, arms=((60, 140), (-60, -140)))
    char(sc, LUSTIG, (0.0, 0, 1.6), lp, h=1.6, shadow=False)
    if up:
        flip = (t * 3) % 1.0 < 0.15 and t < 62.0
        kind = 1 + int(t * 3) % 4 if t < 62.2 else 1
        sc.quad_tex(v3(-0.55, 1.75, 1.35), v3(1.1, 0, 0), v3(0, -0.9 * (0.6 if flip else 1), 0), T.newspaper(kind), 1000, 1300,
                    lw=2, shade=False, depth_bias=-0.4)
    else:
        sc.quad_tex(v3(-0.55, 0.95, 1.3), v3(1.1, 0, 0), v3(0, -0.12, -0.6), T.newspaper(1), 1000, 1300, lw=2, shade=False,
                    depth_bias=-0.4)
    return sc


def sh_shame(t):
    # 64.3 - 67.35 Poisson at night with the certificate, going red
    keys = [(64.2, (-0.8, 1.5, -1.8), (0.0, 1.1, 1.0), 48), (67.4, (-0.3, 1.3, -0.8), (0.0, 1.15, 1.0), 40)]
    cam = mkcam(keys, t, punches=[(66.18, 0.12)])
    sc = Scene(cam, bg=(14, 16, 34), ambient=0.38, fog=None)
    S.room(sc, w=6, d=6, h=3.2, z0=-3, wall=T.wallpaper((40, 44, 70), (46, 50, 80)), floor=T.planks((80, 56, 40)))
    S.wall_window(sc, -0.9, 1.1, 2.98, 1.8, 1.6, night=True, rain=True, curtain_col=rgb('#3a3a60'))
    sc.box((0.3, 0.3, 1.5), (2.2, 0.5, 1.6), rgb('#4a3a6a'), top=rgb('#e0d8f0'))
    red = clamp((t - 64.8) / 1.5)
    pp = dict(eyes='shut' if t > 66.2 else 'dot', brows='worried', mouth='frown', sit=True, red=red * 0.8, sweat=t > 65.5,
              arms=((70, 150), (-70, -150)), sq=bob(t))
    char(sc, POISSON, (0.0, 0.3, 1.4), pp, h=1.5, shadow=False)
    sc.quad_tex(v3(-0.38, 1.05, 1.0), v3(0.76, 0, 0), v3(0, -0.95, 0), T.certificate(), 800, 1000, lw=2, shade=False,
                depth_bias=-0.4)
    return sc


def sh_laugh(t):
    # 67.35 - 69.6 imagined Paris laughing at him
    keys = [(67.3, (0.0, 1.5, -3.0), (0.0, 4.5, 30), 58), (69.7, (0.0, 1.3, -1.6), (0.0, 4.8, 30), 52)]
    cam = mkcam(keys, t, punches=[(68.66, 0.18)], shakes=[(68.7, 12)])
    sc = Scene(cam, bg=SKY_NIGHT, fog=(rgb('#2a2f5a'), 25, 140), ambient=0.5)
    S.paris(sc, lit=True)
    rnd = random.Random(2)
    for i in range(12):
        x = rnd.uniform(-3.5, 3.5)
        z = rnd.uniform(1.5, 9)
        bounce = abs(math.sin(t * 10 + i)) * 0.12
        char(sc, CROWD[i % len(CROWD)], (x, bounce, z), dict(eyes='closed', brows='up', mouth='open', arms=(40, -100),
                                                              tilt=math.sin(t * 12 + i) * 10), h=1.6)
    return sc


def sh_same(t):
    # 71.4 - 75.6 same speech, new dealers (callback of sh_tons framing)
    keys = [(71.3, (1.6, 2.8, -4.2), (0.0, 1.0, 1.6), 56), (73.4, (-0.5, 1.5, -1.6), (0.6, 1.6, 3.2), 50),
            (75.7, (-0.2, 1.4, -0.2), (0.7, 1.55, 3.2), 44)]
    cam = mkcam(keys, t, punches=[(74.81, 0.26)], shakes=[(74.84, 22)])
    sc = Scene(cam, bg=(30, 20, 20), ambient=0.48)
    appear = [71.95 + i * 0.12 for i in range(6)]
    stage = [0, 1, 2, 3][int(clamp((t - 73.6) / 0.35, 0, 3))]
    g = -60 if t < 74.65 else (-60 + 120 * ease_out(clamp((t - 74.65) / 0.12)))
    lp = dict(eyes='half', brows='sly', mouth='smirk', arms=(20, (-150 + (g + 60) * 0.6, -150 + (g + 60))),
              hold=lambda c: PR.gavel(c, 90), sq=bob(t))
    d = dealer_poses(t, NEW_DEALERS, appear, eyes=lambda i: 'money' if t > 74.0 else blink(t, i))
    suite_set(sc, t, d, curtains=1, dim=1, easel=stage, lustig_pose=lp, lustig_pos=(-0.15, 0, 3.0))
    return sc


def sh_police(t):
    keys = [(75.5, (0.0, 1.6, -3.4), (0.0, 1.4, 1.5), 52), (78.3, (0.2, 1.4, -2.2), (0.0, 1.4, 1.5), 46)]
    cam = mkcam(keys, t, punches=[(77.45, 0.2)], shakes=[(77.48, 18)])
    sc = Scene(cam, bg=(30, 40, 70), ambient=0.62)
    S.room(sc, w=8, d=7, h=3.6, z0=-4, wall=T.wallpaper((120, 140, 170), (130, 150, 180)), floor=T.planks((110, 100, 90)))
    sc.quad_tex(v3(-0.9, 3.2, 2.97), v3(1.8, 0, 0), v3(0, -1.2, 0), T.police_sign(), 600, 400, lw=3, shade=False)
    sc.box((0.6, 0.55, 1.6), (2.4, 1.1, 0.8), rgb('#5a3a22'), top=rgb('#6b4a2a'))
    whistle = t > 77.4
    char(sc, POLICE, (0.8, 0, 2.3), dict(eyes='wide' if whistle else 'dot', brows='angry' if whistle else 'flat',
                                         mouth='o' if whistle else 'flat', arms=(20, (-150, -175)) if whistle else (20, -20),
                                         hold=PR.whistle if whistle else None, red=0.3 if whistle else 0))
    if t > 77.6:
        for i, x in enumerate((-2.4, 2.6)):
            k = ease_back(clamp((t - 77.6 - i * 0.1) / 0.2))
            char(sc, POLICE, (x, 0, 1.0), dict(eyes='wide', brows='angry', mouth='shout', arms=(160, -160), sq=k))
    k = ease_out(clamp((t - 75.66) / 0.4))
    char(sc, BUYER2, (lerp(-4.5, -0.9, k), 0, 0.6), dict(eyes='squint', brows='angry', mouth='shout', red=0.5,
                                                          arms=(30, (-60, -95)), walk=t * 3 if k < 1 else None))
    return sc


def sh_empty(t):
    keys = [(78.15, (0.0, 1.8, -6.0), (0.0, 1.0, 1.5), 54), (79.25, (0.0, 1.6, 0.4), (0.0, 0.84, 1.6), 46)]
    cam = mkcam(keys, t, punches=[(78.4, 0.14)], shakes=[(78.2, 18)])
    sc = Scene(cam, bg=(30, 20, 20), ambient=0.55)
    suite_set(sc, t, [], curtains=0.0, easel=3, show_lustig=False, note=True)
    for i, x in enumerate((-0.45, 0.45)):
        char(sc, POLICE, (x, 0, -2.0), dict(eyes='wide', brows='up', mouth='o', arms=(40, -40)))
    return sc


def sh_boat(t):
    lt = t - 79.2
    keys = [(0.0, (-5.6, 2.9, -4.6), (-3.0, 2.3, 0.0), 46), (2.0, (-8.5, 5.0, -10.0), (-1.5, 2.6, 2.0), 52)]
    cam = mkcam(keys, lt)
    sc = Scene(cam, bg=SKY_DUSK, fog=(rgb('#e09a7a'), 30, 160), ambient=0.6)
    # sea
    waves = lambda c: (c.drawRect(skia.Rect(0, 0, 256, 256), skia.Paint(Color=skia.Color(40, 90, 150))),
                       [c.drawLine(x, y, x + 30, y, skia.Paint(AntiAlias=True, Color=skia.Color(120, 180, 220), StrokeWidth=4,
                                                               Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap))
                        for x in range(0, 256, 64) for y in range(16, 256, 48)])
    S.ground(sc, waves, size=300, rep=60, center=(-(lt * 3) % 5, 60), tw=256, th=256)
    # statue of liberty on the horizon
    sc.billboard(v3(14, 0, 90), 22, _liberty, depth_bias=0)
    # liner
    sc.quad_tex(v3(-6, 1.6, -1.2), v3(12, 0, 0), v3(0, -1.6, 0), T.ship_hull(), 512, 256, lw=3, shade=False)
    sc.box((0, 0.8, 0.6), (12, 1.6, 3.6), rgb('#1e1e28'), top=rgb('#c9a27a'), sides=('top', 'right', 'back', 'left'))
    sc.box((1.2, 2.3, 0.8), (6, 1.4, 2.4), rgb('#f2f2f2'))
    for x in (0.0, 2.6):
        sc.cyl((x, 3.0, 0.8), 0.5, 1.8, rgb('#c0303a'), seg=12, top=rgb('#1e1e28'))
    char(sc, LUSTIG, (-3.2, 1.6, -0.4), dict(eyes='closed', brows='sly', mouth='grin', shades=True, sit=True,
                                              arms=(20, -150 + 18 * math.sin(t * 9)), hold_l=lambda c: PR.suitcase(c, 0.4)),
         h=1.5)
    sc.box((-3.2, 1.75, -0.4), (0.7, 0.12, 1.1), rgb('#e8d8b0'))
    return sc


def _liberty(c):
    g = skia.Paint(AntiAlias=True, Color=skia.Color(80, 140, 120))
    p = skia.Path()
    p.addRect(skia.Rect(-14, -30, 14, 0))
    p.addRect(skia.Rect(-7, -70, 7, -30))
    p.addCircle(0, -76, 6)
    c.drawPath(p, g)
    c.drawLine(5, -72, 12, -96, skia.Paint(AntiAlias=True, Color=skia.Color(80, 140, 120), StrokeWidth=4,
                                           Style=skia.Paint.kStroke_Style))
    c.drawCircle(12, -98, 3.5, skia.Paint(AntiAlias=True, Color=skia.Color(255, 220, 120)))


# ------------------------------------------------------------------ timeline
# (start, end, shot, transition-in seconds (dissolve) or 0 for cut, kind)
TIMELINE = [
    (0.0, 4.04, sh_hook, 0, 'cut'),
    (4.04, 8.22, sh_1925, 0.22, 'whip'),
    (8.22, 11.42, sh_rust, 0.25, 'dissolve'),
    (11.42, 14.62, sh_news, 0.22, 'whip'),
    (14.62, 17.42, sh_intro, 0.18, 'dissolve'),
    (17.42, 19.66, sh_letter, 0.18, 'whip'),
    (19.66, 22.55, sh_hotel, 0.22, 'dissolve'),
    (22.55, 25.65, sh_meet, 0.35, 'dissolve'),
    (25.65, 28.62, sh_whisper, 0.2, 'whip'),
    (28.62, 31.8, sh_tons, 0.18, 'dissolve'),
    (31.8, 34.12, sh_shh, 0.16, 'whip'),
    (34.12, 35.52, sh_riot, 0.12, 'whip'),
    (35.52, 40.72, sh_poisson, 0.16, 'whip'),
    (40.72, 43.0, sh_hurry, 0.2, 'dissolve'),
    (43.0, 45.84, sh_lean, 0.2, 'dissolve'),
    (45.84, 49.56, sh_wait, 0.0, 'cut'),
    (49.56, 52.45, sh_corrupt, 0.22, 'dissolve'),
    (52.45, 55.55, sh_pay, 0.2, 'whip'),
    (55.55, 59.55, sh_train, 0.22, 'whip'),
    (59.55, 64.22, sh_papers, 0.25, 'dissolve'),
    (64.22, 67.3, sh_shame, 0.3, 'dissolve'),
    (67.3, 69.55, sh_laugh, 0.15, 'whip'),
    (69.55, 71.4, sh_hotel_back, 0.2, 'whip'),
    (71.4, 75.6, sh_same, 0.25, 'dissolve'),
    (75.6, 78.12, sh_police, 0.18, 'whip'),
    (78.12, 79.18, sh_empty, 0.12, 'whip'),
    (79.18, 81.2, sh_boat, 0.2, 'dissolve'),
]


# ------------------------------------------------------------------ 2D overlays
def captions_chunks():
    chunks = []
    cur = []
    for w in WORDS:
        txt = w['w']
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
            sh = skia.Paint(AntiAlias=True, Color=skia.Color(0, 0, 0, 120),
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
            c.drawString(txt, x + 3, 30 + 6, CAP_FONT, sh)
            c.drawString(txt, x, 30, CAP_FONT, skia.Paint(AntiAlias=True, Color=INK, Style=skia.Paint.kStroke_Style,
                                                         StrokeWidth=16, StrokeJoin=skia.Paint.kRound_Join))
            c.drawString(txt, x, 30, CAP_FONT, skia.Paint(AntiAlias=True, Color=skia.Color(255, 255, 255)))
            c.restore()
            break


def card_overlay(c, t, t0, t1, name, sub, accent=(210, 40, 50), y=0.2):
    if not (t0 <= t < t1):
        return
    k_in = ease_back(clamp((t - t0) / 0.22), 1.8)
    k_out = 1 - ease_in(clamp((t - (t1 - 0.2)) / 0.2))
    k = min(k_in, k_out)
    c.save()
    c.translate(W / 2, H * y)
    c.rotate(-4 + 4 * (1 - k))
    c.scale(0.95 * k, 0.95 * k)
    c.translate(-450, -150)
    T.name_card(name, sub, accent)(c)
    c.restore()


def sparkles(c, t, pts, t0, dur=0.8, color=(255, 230, 120)):
    if not (t0 <= t < t0 + dur):
        return
    a = (t - t0) / dur
    for i, (x, y) in enumerate(pts):
        s = math.sin(min(1, a * 1.3) * math.pi) * (22 + 8 * (i % 3))
        p = skia.Path()
        for j in range(8):
            r = s if j % 2 == 0 else s * 0.3
            ang = j * math.pi / 4 + t * 2
            (p.moveTo if j == 0 else p.lineTo)(x + r * math.cos(ang), y + r * math.sin(ang))
        p.close()
        c.drawPath(p, skia.Paint(AntiAlias=True, Color=col(color)))


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


def vignette(c, strength=150, color=(0, 0, 0)):
    sh = skia.GradientShader.MakeRadial((W / 2, H / 2), H * 0.72,
                                        [skia.Color(*color, 0), skia.Color(*color, 0), skia.Color(*color, strength)],
                                        [0.0, 0.55, 1.0])
    c.drawPaint(skia.Paint(Shader=sh))


def lamp_glow(c, x, y, r, color=(255, 200, 120), a=90):
    sh = skia.GradientShader.MakeRadial((x, y), r, [skia.Color(*color, a), skia.Color(*color, 0)])
    c.drawPaint(skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kPlus))


def bill_receipt(c, t, t0):
    """long paint bill unrolling down the frame ('cost a fortune to repaint')"""
    if t < t0:
        return
    k = ease_out(clamp((t - t0) / 0.9))
    hgt = 80 + k * 900
    x0, y0 = W * 0.05, H * 0.1
    c.save()
    c.rotate(4, x0, y0)
    c.drawRect(skia.Rect(x0, y0, x0 + 360, y0 + hgt), skia.Paint(AntiAlias=True, Color=skia.Color(252, 250, 242)))
    c.drawRect(skia.Rect(x0, y0, x0 + 360, y0 + hgt), skia.Paint(AntiAlias=True, Color=INK, Style=skia.Paint.kStroke_Style,
                                                                 StrokeWidth=5))
    c.clipRect(skia.Rect(x0, y0, x0 + 360, y0 + hgt))
    T.text_c(c, 'PAINT BILL', x0 + 180, y0 + 62, T.font('black', 44), (40, 40, 50))
    lines = ['60 tons paint', '25 painters', '1,500 brushes', '7 years', 'scaffolding', 'more paint', 'even more paint']
    for i, ln in enumerate(lines):
        y = y0 + 130 + i * 92
        c.drawString(ln, x0 + 24, y, T.font('semi', 34), skia.Paint(AntiAlias=True, Color=skia.Color(70, 70, 80)))
        c.drawString('₣₣₣', x0 + 270, y, T.font('bold', 30), skia.Paint(AntiAlias=True, Color=skia.Color(200, 40, 50)))
    c.drawString('TOTAL: ₣₣₣₣₣₣₣', x0 + 24, y0 + 820, T.font('black', 38), skia.Paint(AntiAlias=True, Color=skia.Color(200, 40, 50)))
    c.restore()


def overlays(c, t):
    # warm lamp glow on the night desk
    if 17.42 <= t < 19.66:
        lamp_glow(c, W * 0.72, H * 0.42, 900, a=70)
    if 22.55 <= t < 55.55 and t >= 25.0:
        lamp_glow(c, W * 0.5, H * 0.1, 1100, (255, 210, 140), 40)
    if 9.55 <= t < 11.42:
        bill_receipt(c, t, 9.95)
    impact_lines(c, t, 1.31, 0.28)
    impact_lines(c, t, 3.01, 0.3, color=(255, 220, 120))
    impact_lines(c, t, 31.12, 0.3)
    impact_lines(c, t, 46.02, 0.3, cy=H * 0.4)
    impact_lines(c, t, 74.81, 0.3)
    sparkles(c, t, [(W * 0.25, H * 0.33), (W * 0.78, H * 0.3), (W * 0.62, H * 0.2)], 20.6, 0.9)
    sparkles(c, t, [(W * 0.3, H * 0.4), (W * 0.72, H * 0.36), (W * 0.5, H * 0.26)], 48.36, 1.0)
    sparkles(c, t, [(W * 0.3, H * 0.42), (W * 0.7, H * 0.38)], 29.8, 0.7, (120, 230, 140))
    card_overlay(c, t, 15.55, 17.35, 'VICTOR LUSTIG', 'professional con man')
    card_overlay(c, t, 36.6, 38.0, 'ANDRÉ POISSON', 'scrap metal dealer', accent=(47, 116, 192))
    if 49.9 <= t < 52.4:
        k = ease_back(clamp((t - 50.28) / 0.2), 2)
        if t >= 50.28:
            c.save()
            c.translate(W * 0.5, H * 0.2)
            c.rotate(-10)
            c.scale(k, k)
            T.rrect(c, -330, -90, 330, 90, 26, (255, 255, 255, 235), (40, 150, 70), 12)
            T.text_c(c, '✓ REAL OFFICIAL', 0, 30, T.font('black', 74), (40, 150, 70))
            c.restore()
    if 33.19 <= t < 34.1:
        a = clamp((t - 33.19) / 0.12)
        T.text_c(c, 'shhh...', W * 0.73, H * 0.3, T.font('black', 70), (255, 255, 255, int(255 * a)), stroke=10)
    if 34.12 <= t < 35.52:
        vignette(c, 160, (160, 20, 20))
    if 64.22 <= t < 69.55:
        vignette(c, 200, (10, 10, 40))
    if 73.55 <= t < 75.2:
        a = 0.6 + 0.4 * math.sin(t * 12)
        T.text_c(c, '▶▶  SAME SPEECH', W * 0.5, H * 0.12, T.font('black', 64), (255, 255, 255, int(255 * a)), stroke=10)
    if 62.8 <= t < 63.4:  # dead air beat
        T.text_c(c, '. . .', W * 0.5, H * 0.3, T.font('black', 90), (255, 255, 255), stroke=10)
    vignette(c, 120)
    draw_caption(c, t)
