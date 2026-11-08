"""Neon open-world style kit: sunset/night coast city, palms, sports cars, game-store props, HUD.

All art is original and drawn procedurally with skia (no logos, no real game assets).
The look is a generic "sun-soaked crime-city" game aesthetic: pink/orange sunsets, teal neon,
palm silhouettes, wet reflective roads, bold slanted titles, a money counter and a minimap.
"""
import math
import os
import random
import sys

import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "blackhole"))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from gfx import (W, H, C, P, xf, rrect, poly, line, linear, radial, fill_shader, clamp, lerp,  # noqa: E402,F401
                 smooth, ease_out, back_out, at, window, mixhex)
import sgfx  # noqa: E402
from sgfx import cached, blit, grain, tint, figure, head_only, arrow, OUTFITS, POSES  # noqa: E402,F401

FD = "/usr/share/fonts/opentype/inter/"
_tf = {}
_fo = {}


def tf(name):
    if name not in _tf:
        _tf[name] = skia.Typeface.MakeFromFile(FD + name + ".otf")
    return _tf[name]


def fnt(size, face="InterDisplay-BlackItalic"):
    k = (face, round(size, 1))
    if k not in _fo:
        f = skia.Font(tf(face), size)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        _fo[k] = f
    return _fo[k]


# palette
PINK = "#ff3d8b"
HOT = "#ff2e63"
ORANGE = "#ff8c32"
GOLD = "#ffd23f"
TEAL = "#21e6d2"
CYAN = "#3ad7ff"
PURPLE = "#7a2cff"
NIGHT = "#0c0620"
GREEN = "#3dff8a"
CASH = "#7ee08a"
RED = "#ff3030"

OUTFITS.update({
    "hero": dict(suit="#16b8a6", suit2="#0d7c70", trim="#ffd23f"),
    "buyer": dict(suit="#ff4f8b", suit2="#b8325f", trim="#ffffff"),
    "buyer2": dict(suit="#ff9a3c", suit2="#b8641f", trim="#ffffff"),
    "buyer3": dict(suit="#7a6cff", suit2="#4f43b8", trim="#ffffff"),
    "parent": dict(suit="#6c5ce7", suit2="#463ba6", trim="#ffd23f", bun=True),
    "teen": dict(suit="#ff7a3c", suit2="#b8521f", trim="#ffffff", small=True),
    "ceo": dict(suit="#262a36", suit2="#151821", trim="#e9e3d2"),
    "gamer": dict(suit="#3a7bff", suit2="#2552b0", trim="#ffffff", glasses=True),
})
POSES.update({
    "run": dict(la=(-60, 40), ra=(60, 50), ll=(-45, 40), rl=(40, 10)),
    "run2": dict(la=(60, 50), ra=(-60, 40), ll=(40, 10), rl=(-45, 40)),
    "cheer": dict(la=(-150, -10), ra=(150, 10), ll=(-6, 0), rl=(6, 0)),
    "hold": dict(la=(40, 70), ra=(-40, -70), ll=(-3, 0), rl=(3, 0)),
    "think": dict(la=(-6, 0), ra=(150, 120), ll=(-3, 0), rl=(3, 0)),
    "stop": dict(la=(-6, 0), ra=(120, 40), ll=(-3, 0), rl=(3, 0)),
    "game": dict(la=(40, 85), ra=(-40, -85), ll=(80, -85), rl=(75, -80)),
})


def ftext(c, s, x, y, size, color="#ffffff", face="InterDisplay-BlackItalic", align="center", a=1.0,
          stroke=None, sw=0, shadow=0.0, glow_c=None, glow_r=0):
    f = fnt(size, face)
    w = f.measureText(s)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    if glow_c:
        p = P(glow_c, a=a * 0.9)
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, glow_r))
        c.drawString(s, x, y, f, p)
    if shadow:
        c.drawString(s, x + size * 0.06, y + size * 0.08, f, P("#000000", a=a * shadow))
    if stroke:
        c.drawString(s, x, y, f, P(stroke, sw, a))
    c.drawString(s, x, y, f, P(color, a=a))
    return w


def tw(s, size, face="InterDisplay-BlackItalic"):
    return fnt(size, face).measureText(s)


def blurp(color, r, a=1.0, stroke=None):
    p = P(color, stroke, a)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r))
    return p


def glow(c, x, y, r, color, a=0.6):
    fill_shader(c, skia.Rect(x - r, y - r, x + r, y + r), radial(x, y, r, [(color, a), (color, 0)]))


def neon_rect(c, x, y, w, h, r, color, sw=6, a=1.0, flicker=1.0):
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)
    c.drawRRect(rr, blurp(color, 14, 0.8 * a * flicker, sw * 2.5))
    c.drawRRect(rr, P(color, sw, a * flicker))
    c.drawRRect(rr, P("#ffffff", sw * 0.35, 0.8 * a * flicker))


def neon_text(c, s, x, y, size, color, a=1.0, flicker=1.0, face="InterDisplay-BlackItalic"):
    ftext(c, s, x, y, size, color, face, a=a * flicker, glow_c=color, glow_r=size * 0.25)
    ftext(c, s, x, y, size, "#ffffff", face, a=0.55 * a * flicker)


# ----------------------------------------------------------------- environment
SKIES = {
    "dusk": (["#1a0b3b", "#5a1a6e", "#c2306f", "#ff6b4a", "#ffb15c"], [0, 0.35, 0.62, 0.85, 1.0]),
    "night": (["#05030f", "#0d0a2e", "#2a1452", "#5b1f6b"], [0, 0.45, 0.8, 1.0]),
    "day": (["#2a7fd4", "#5fb8ea", "#9fdcf0", "#ffd9a8"], [0, 0.45, 0.8, 1.0]),
    "dawn": (["#1b2a5e", "#5a4b8f", "#e07a8f", "#ffc890"], [0, 0.4, 0.75, 1.0]),
}
_r = random.Random(3)
STARS = [(_r.uniform(0, W), _r.uniform(0, 560), _r.uniform(0.8, 2.4), _r.uniform(0, 6.28)) for _ in range(260)]


def sky(c, kind="dusk", horizon=700, t=0.0, stars=None):
    cols, pos = SKIES[kind]
    fill_shader(c, skia.Rect(0, 0, W, horizon + 4), linear(0, 0, 0, horizon, cols, pos))
    if stars is None:
        stars = kind in ("night", "dusk")
    if stars:
        k = 1.0 if kind == "night" else 0.45
        for x, y, r, ph in STARS:
            if y < horizon * 0.7:
                a = k * (0.35 + 0.35 * math.sin(t * 1.3 + ph)) * (1 - y / (horizon * 0.7))
                c.drawCircle(x, y, r, P("#ffffff", a=a))


def retro_sun(c, x, y, r, top=GOLD, bottom=HOT, stripes=True, a=1.0):
    glow(c, x, y, r * 2.6, ORANGE, 0.35 * a)
    glow(c, x, y, r * 1.5, GOLD, 0.35 * a)
    c.save()
    c.clipRect(skia.Rect(x - r - 2, y - r - 2, x + r + 2, y + r * 0.62))
    if stripes:
        for i in range(6):
            yy = y + r * (0.05 + i * 0.11)
            h = 3 + i * 3.2
            c.clipRect(skia.Rect(x - r - 2, yy, x + r + 2, yy + h), skia.ClipOp.kDifference)
    p = skia.Paint(AntiAlias=True, Shader=linear(0, y - r, 0, y + r, [top, bottom]))
    p.setAlphaf(a)
    c.drawCircle(x, y, r, p)
    c.restore()


def clouds(c, t, y=260, color="#ff8fb0", a=0.35, seed=4, speed=6):
    rnd = random.Random(seed)
    for i in range(7):
        cx = (rnd.uniform(0, W + 600) + t * speed * rnd.uniform(0.6, 1.4)) % (W + 600) - 300
        cy = y + rnd.uniform(-120, 120)
        w = rnd.uniform(260, 520)
        for j in range(5):
            c.drawOval(skia.Rect.MakeXYWH(cx + j * w * 0.18 - w * 0.3, cy - rnd.uniform(10, 40), w * 0.5, 34 + j % 2 * 12),
                       blurp(color, 18, a))


def _tower_layer(cc, base, seed, color, win_col, hmin, hmax, wmin, wmax, win_a=0.85, spires=True, lit=0.35):
    rnd = random.Random(seed)
    x = -40
    while x < W + 60:
        w = rnd.uniform(wmin, wmax)
        h = rnd.uniform(hmin, hmax)
        top = base - h
        cc.drawRect(skia.Rect(x, top, x + w, base + 400), P(color))
        kind = rnd.random()
        if spires and kind < 0.18:
            cc.drawRect(skia.Rect(x + w * 0.45, top - h * 0.25, x + w * 0.55, top), P(color))
            cc.drawCircle(x + w * 0.5, top - h * 0.25, 4, P(RED))
        elif kind < 0.35:
            cc.drawPath(poly([(x, top), (x + w, top), (x + w * 0.5, top - w * 0.4)]), P(color))
        elif kind < 0.5:
            cc.drawRect(skia.Rect(x + w * 0.15, top - 30, x + w * 0.85, top), P(color))
        # windows
        if win_col:
            cols = max(2, int(w / 16))
            rows = int(h / 22)
            for i in range(cols):
                for j in range(rows):
                    if rnd.random() < lit:
                        wx = x + 6 + i * (w - 12) / cols
                        wy = top + 10 + j * 22
                        cc.drawRect(skia.Rect.MakeXYWH(wx, wy, max(3, (w - 12) / cols - 5), 9),
                                    P(rnd.choice(win_col), a=win_a * rnd.uniform(0.5, 1)))
        # rooftop neon strip on some
        if rnd.random() < 0.12:
            cc.drawRect(skia.Rect(x + 4, top + 4, x + w - 4, top + 9), P(rnd.choice((PINK, TEAL, CYAN))))
        x += w + rnd.uniform(-6, 10)


def city_layers(kind="dusk", base=700):
    """Returns cached (far, mid, near) skyline images for a time of day."""
    if kind == "night":
        cfar, cmid, cnear = "#2a1a4e", "#160d33", "#0a0619"
        wins = ("#ffd27a", "#7af0ff", "#ff7ac8", "#fff3c4")
        lit = 0.42
    elif kind == "day":
        cfar, cmid, cnear = "#7fa9cf", "#4f7ba6", "#2c4a6e"
        wins = ("#cfe8ff", "#a8d4f5")
        lit = 0.2
    elif kind == "dawn":
        cfar, cmid, cnear = "#6d5a97", "#3e3470", "#1f1a44"
        wins = ("#ffd9a0", "#ffe9c7")
        lit = 0.25
    else:
        cfar, cmid, cnear = "#7a2f78", "#43195a", "#1c0a2e"
        wins = ("#ffd27a", "#ffb0d8", "#9ef6ff")
        lit = 0.32

    def mk(seed, col, hmin, hmax, wmin, wmax, wa, blur):
        def d(cc):
            cc.clear(skia.ColorTRANSPARENT)
            _tower_layer(cc, base, seed, col, wins, hmin, hmax, wmin, wmax, wa, lit=lit)
        return cached(("city", kind, seed, base), d, blur=blur)

    far = mk(11, cfar, 120, 300, 50, 110, 0.35, 1.5)
    mid = mk(12, cmid, 160, 420, 70, 150, 0.6, 0.6)
    near = mk(13, cnear, 80, 230, 90, 190, 0.9, 0)
    return far, mid, near


def _cached_t(key, draw):
    """Cached transparent full-frame layer (cached() clears to black; this keeps alpha)."""
    if key not in sgfx._cache:
        s = skia.Surface(W, H)
        cc = s.getCanvas()
        cc.clear(skia.ColorTRANSPARENT)
        draw(cc)
        sgfx._cache[key] = s.makeImageSnapshot()
    return sgfx._cache[key]


def city_layers_t(kind="dusk", base=700):
    if kind == "night":
        cols = ("#2a1a4e", "#160d33", "#0a0619")
        wins, lit = ("#ffd27a", "#7af0ff", "#ff7ac8", "#fff3c4"), 0.42
    elif kind == "day":
        cols = ("#86aed3", "#5482ad", "#2e4d72")
        wins, lit = ("#e4f3ff", "#b8ddf7"), 0.18
    elif kind == "dawn":
        cols = ("#6d5a97", "#3e3470", "#1f1a44")
        wins, lit = ("#ffd9a0", "#ffe9c7"), 0.25
    else:
        cols = ("#86347f", "#4a1b60", "#1f0b32")
        wins, lit = ("#ffd27a", "#ffb0d8", "#9ef6ff"), 0.32
    specs = [(11, cols[0], 140, 330, 50, 110, 0.35), (12, cols[1], 170, 440, 70, 150, 0.6),
             (13, cols[2], 80, 230, 90, 190, 0.9)]
    out = []
    for seed, col, a, b, w1, w2, wa in specs:
        out.append(_cached_t(("cityT", kind, seed, base),
                             lambda cc, seed=seed, col=col, a=a, b=b, w1=w1, w2=w2, wa=wa:
                             _tower_layer(cc, base, seed, col, wins, a, b, w1, w2, wa, lit=lit)))
    return out


def palm(c, x, y, s=1.0, color="#12061f", t=0.0, sway=1.0, lean=6):
    """Palm tree silhouette rooted at (x, y)."""
    with xf(c, x, y, s):
        trunk = skia.Path()
        h = 520
        bend = lean * 6
        trunk.moveTo(-16, 0)
        trunk.cubicTo(-14, -h * 0.4, -10 + bend * 0.5, -h * 0.75, bend - 7, -h)
        trunk.lineTo(bend + 7, -h)
        trunk.cubicTo(10 + bend * 0.5, -h * 0.75, 14, -h * 0.4, 16, 0)
        trunk.close()
        c.drawPath(trunk, P(color))
        tx, ty = bend, -h
        sw = math.sin(t * 1.4 + x * 0.01) * 4 * sway
        for i, ang in enumerate((-160, -125, -95, -60, -25, 10, 40, 75)):
            a = math.radians(ang + sw * (1 if i % 2 else -1))
            L = 230 + (i % 3) * 30
            ex, ey = tx + math.cos(a) * L, ty + math.sin(a) * L * 0.55 + L * 0.28
            mx, my = tx + math.cos(a) * L * 0.5, ty + math.sin(a) * L * 0.5 - 40
            fr = skia.Path()
            fr.moveTo(tx, ty)
            fr.quadTo(mx, my - 14, ex, ey)
            fr.quadTo(mx, my + 22, tx, ty + 8)
            fr.close()
            c.drawPath(fr, P(color))
        c.drawCircle(tx, ty + 4, 22, P(color))


def palms_row(c, t, y, color="#12061f", xs=(80, 330, 1620, 1860), scale=1.0, sway=1.0):
    for i, x in enumerate(xs):
        palm(c, x, y, scale * (0.9 + 0.15 * (i % 2)), color, t, sway, lean=(6 if x < W / 2 else -6))


def ocean(c, y0, t, sun_x=W / 2, kind="dusk", y1=H):
    if kind == "night":
        top, bot, ref = "#2a1452", "#05030f", PINK
    elif kind == "day":
        top, bot, ref = "#5fc2d8", "#1d5f8a", "#ffffff"
    else:
        top, bot, ref = "#d24c7a", "#2a0f3e", GOLD
    fill_shader(c, skia.Rect(0, y0, W, y1), linear(0, y0, 0, y1, [top, bot]))
    rnd = random.Random(9)
    for i in range(70):
        yy = y0 + (i / 70) ** 1.6 * (y1 - y0)
        wdt = 30 + 260 * (1 - (i / 70)) * rnd.uniform(0.4, 1)
        xx = sun_x + math.sin(t * 1.2 + i * 1.7) * 30 + rnd.uniform(-60, 60) * (1 + i / 30)
        c.drawRect(skia.Rect(xx - wdt / 2, yy, xx + wdt / 2, yy + 2 + i * 0.06), P(ref, a=0.55 * (1 - i / 90)))


def road(c, y0, t, speed=1.0, kind="dusk", wet=True):
    fill_shader(c, skia.Rect(0, y0, W, H), linear(0, y0, 0, H, ["#1a1028", "#07050d"]))
    if wet:
        # neon reflections streak
        for x, col in ((260, PINK), (700, CYAN), (1150, ORANGE), (1600, TEAL)):
            c.drawRect(skia.Rect(x - 30, y0, x + 30, H), blurp(col, 22, 0.18))
    # dashes
    off = (t * 900 * speed) % 240
    for i in range(-1, 10):
        x = i * 240 - off
        rrect(c, x, y0 + (H - y0) * 0.5, 120, 10, 4, "#ffe9a8", 0.7)
    c.drawRect(skia.Rect(0, y0, W, y0 + 6), P("#3a2a55"))


def car(c, x, y, s=1.0, body=HOT, t=0.0, face=1, glow_c=None, wheel_spin=0.0, lights=True, a=1.0):
    """Original low sports coupe, side view. (x, y) = ground under car center."""
    with xf(c, x, y, s, alpha=a, sx=s * face, sy=s):
        if glow_c:
            c.drawOval(skia.Rect(-260, -20, 260, 22), blurp(glow_c, 26, 0.75))
        c.drawOval(skia.Rect(-250, -10, 250, 14), P("#000000", a=0.5))
        bodyp = skia.Path()
        bodyp.moveTo(-250, -30)
        bodyp.lineTo(-245, -78)
        bodyp.cubicTo(-200, -96, -120, -100, -80, -104)
        bodyp.cubicTo(-40, -150, 40, -158, 90, -150)
        bodyp.cubicTo(130, -136, 160, -112, 175, -104)
        bodyp.cubicTo(220, -98, 252, -86, 258, -60)
        bodyp.lineTo(262, -30)
        bodyp.close()
        c.drawPath(bodyp, skia.Paint(AntiAlias=True, Shader=linear(0, -160, 0, -30, [mixhex(body, "#ffffff", 0.25),
                                                                                       body, mixhex(body, "#000000",
                                                                                                    0.55)])))
        # side character line + highlights
        line(c, -230, -66, 240, -70, mixhex(body, "#ffffff", 0.5), 3, 0.7)
        # windows
        win = skia.Path()
        win.moveTo(-60, -104)
        win.cubicTo(-30, -140, 30, -146, 80, -140)
        win.cubicTo(115, -128, 140, -112, 150, -104)
        win.close()
        c.drawPath(win, skia.Paint(AntiAlias=True, Shader=linear(-60, -146, 150, -104, ["#1b2340", "#4a5c8a",
                                                                                          "#141a30"])))
        line(c, 40, -142, 34, -104, mixhex(body, "#000000", 0.5), 6)
        c.drawPath(poly([(-30, -128), (10, -138), (-20, -108), (-45, -108)]), P("#ffffff", a=0.18))
        # lights
        if lights:
            rrect(c, 236, -78, 22, 10, 4, "#fff6d0")
            glow(c, 258, -73, 60, "#fff1b0", 0.5)
            rrect(c, -252, -74, 16, 10, 4, "#ff2a2a")
            glow(c, -252, -69, 40, "#ff2a2a", 0.5)
        # wheels
        for wx in (-150, 160):
            c.drawCircle(wx, -26, 44, P("#08060c"))
            c.drawCircle(wx, -26, 28, P("#565a66"))
            for k in range(5):
                ang = wheel_spin + k * 2 * math.pi / 5
                line(c, wx, -26, wx + math.cos(ang) * 24, -26 + math.sin(ang) * 24, "#2a2d36", 6)
            c.drawCircle(wx, -26, 8, P("#c9ccd6"))


def scene_coast(c, t, kind="dusk", cam=0.0, sun=True, zoom=1.0, horizon=640, car_x=None, car_c=HOT):
    """Big cinematic coastal city establishing shot."""
    with xf(c, W / 2, H / 2, zoom):
        c.translate(-W / 2, -H / 2)
        sky(c, kind, horizon, t)
        if sun and kind in ("dusk", "dawn"):
            retro_sun(c, W * 0.5 + cam * 0.05, horizon - 40, 230)
        clouds(c, t, 230, "#ff9cc0" if kind == "dusk" else "#9fa0ff", 0.28)
        far, mid, near = city_layers_t(kind, horizon + 10)
        # distant skyline across the bay: squashed so the sun still shows
        with xf(c, 0, horizon + 10, sx=1.0, sy=0.42):
            blit(c, far, -cam * 0.15 - 300, -(horizon + 10))
        with xf(c, 0, horizon + 10, sx=1.0, sy=0.3):
            blit(c, mid, -cam * 0.3 + 700, -(horizon + 10))
        fill_shader(c, skia.Rect(0, horizon - 160, W, horizon + 12),
                    linear(0, horizon - 160, 0, horizon + 12, [(ORANGE, 0), (PINK, 0.35)]))
        ocean(c, horizon + 10, t, W / 2, kind)
        # coastal road + palms foreground
        c.drawRect(skia.Rect(0, 905, W, H), P("#0b0614"))
        c.drawRect(skia.Rect(0, 900, W, 908), P(PINK, a=0.5))
        if car_x is not None:
            car(c, car_x, 960, 0.85, car_c, t, glow_c=CYAN, wheel_spin=t * 20)
        for i, x in enumerate((-60, 240, 1700, 1990)):
            palm(c, x - cam * 0.9, 1000, 1.25 + 0.1 * (i % 2), "#0b0614", t, 1.0, lean=(7 if x < W / 2 else -7))


def scene_street(c, t, kind="night", cam=0.0, horizon=620):
    """Neon downtown street at night with wet road."""
    sky(c, kind, horizon + 40, t)
    far, mid, near = city_layers_t(kind, horizon)
    blit(c, far, -cam * 0.1, 0)
    blit(c, mid, -cam * 0.25, 0)
    blit(c, near, -cam * 0.45, 0)
    fill_shader(c, skia.Rect(0, horizon - 200, W, horizon + 10), linear(0, horizon - 200, 0, horizon,
                                                                          [(PURPLE, 0), (PINK, 0.25)]))
    road(c, horizon, t, 0.0, kind)
    # reflections of the skyline
    c.save()
    c.translate(0, horizon * 2)
    c.scale(1, -1)
    p = skia.Paint()
    p.setAlphaf(0.18)
    c.drawImage(near, -cam * 0.45, 0, skia.SamplingOptions(), p)
    c.restore()


# ----------------------------------------------------------------- post / camera
def shake(t, start, dur=0.4, amp=18):
    k = clamp(1 - (t - start) / dur) if t >= start else 0
    if k <= 0:
        return 0, 0
    return (math.sin(t * 91) * amp * k, math.cos(t * 77) * amp * k)


def grade(c, warm=0.0, cool=0.0):
    if warm:
        p = P(ORANGE, a=warm)
        p.setBlendMode(skia.BlendMode.kOverlay)
        c.drawRect(skia.Rect(0, 0, W, H), p)
    if cool:
        p = P(PURPLE, a=cool)
        p.setBlendMode(skia.BlendMode.kOverlay)
        c.drawRect(skia.Rect(0, 0, W, H), p)


def vignette(c, a=0.55):
    fill_shader(c, skia.Rect(0, 0, W, H),
                radial(W / 2, H / 2, W * 0.72, [("#000000", 0), ("#000000", 0.0), ("#000000", a)], [0, 0.55, 1]))


def letterbox(c, k=1.0, h=96):
    if k > 0:
        c.drawRect(skia.Rect(0, 0, W, h * k), P("#000000"))
        c.drawRect(skia.Rect(0, H - h * k, W, H), P("#000000"))


def flash(c, t, start, dur=0.25, color="#ffffff", a=0.8):
    if start <= t < start + dur:
        tint(c, color, a * (1 - (t - start) / dur))


def light_leak(c, t, a=0.25):
    x = W * (0.2 + 0.6 * (0.5 + 0.5 * math.sin(t * 0.21)))
    glow(c, x, -100, 900, ORANGE, a)
    glow(c, W - x * 0.4, H + 200, 800, PINK, a * 0.6)


# ----------------------------------------------------------------- titles / HUD
def slam_title(c, t, start, s, x=W / 2, y=H / 2, size=170, color="#ffffff", stroke="#000000", end=None,
               sub=None, sub_color=GOLD, rot=-4, tilt=True):
    """Big slanted game title that slams in (scale from 1.6 → 1 with a punch)."""
    if t < start:
        return
    k = clamp((t - start) / 0.22)
    out = 1.0 if end is None else clamp((end - t) / 0.25)
    if out <= 0:
        return
    sc = lerp(1.7, 1.0, ease_out(k))
    with xf(c, x, y, sc, rot=rot if tilt else 0, alpha=k * out):
        ftext(c, s, 0, size * 0.35, size, color, stroke=stroke, sw=size * 0.14, shadow=0.6)
        if sub:
            ftext(c, sub, 0, size * 0.35 + size * 0.55, size * 0.36, sub_color, "InterDisplay-ExtraBoldItalic",
                  stroke="#000000", sw=size * 0.06)


def stamp(c, t, start, s, x, y, color=RED, size=90, rot=-12, end=None):
    if t < start:
        return
    k = clamp((t - start) / 0.16)
    out = 1.0 if end is None else clamp((end - t) / 0.25)
    sc = lerp(2.4, 1.0, k)
    w = tw(s, size) + 70
    with xf(c, x, y, sc, rot=rot, alpha=min(1.0, k * 1.5) * out):
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -size * 0.8, w, size * 1.4), 18, 18)
        c.drawRRect(rr, P(color, 12))
        ftext(c, s, 0, size * 0.33, size, color)


def chip(c, x, y, s, bg=GOLD, fg="#0b0614", size=44, a=1.0, sc=1.0, face="InterDisplay-BlackItalic"):
    w = tw(s, size, face) + 50
    with xf(c, x, y, sc, alpha=a):
        c.drawPath(poly([(-w / 2 + 12, -size * 0.8), (w / 2 + 12, -size * 0.8), (w / 2 - 12, size * 0.75),
                         (-w / 2 - 12, size * 0.75)]), P("#000000", a=0.6))
        c.drawPath(poly([(-w / 2 + 6, -size * 0.85), (w / 2 + 6, -size * 0.85), (w / 2 - 18, size * 0.7),
                         (-w / 2 - 18, size * 0.7)]), P(bg))
        ftext(c, s, -6, size * 0.33, size, fg, face)


def pop_in(t, start, dur=0.35):
    return back_out(at(t, start, dur)) if t >= start else 0.0


def money_hud(c, value, t=0.0, color=CASH, x=W - 70, y=110, size=72, flash_t=None):
    s = "$" + f"{int(value):,}"
    a = 1.0
    col = color
    if flash_t is not None and 0 <= t - flash_t < 0.3:
        col = "#ffffff"
    ftext(c, s, x, y, size, col, "InterDisplay-Black", align="right", stroke="#000000", sw=10, a=a)


def minimap(c, t, x=150, y=H - 150, r=95, heading=0.0, blip=None):
    c.save()
    pth = skia.Path()
    pth.addCircle(x, y, r)
    c.clipPath(pth, skia.ClipOp.kIntersect, True)
    c.drawCircle(x, y, r, P("#2d3a2e", a=0.88))
    with xf(c, x, y, rot=heading):
        rnd = random.Random(2)
        for i in range(-4, 5):
            line(c, i * 46 - (t * 20) % 46, -r, i * 46 - (t * 20) % 46, r, "#566457", 10)
            line(c, -r, i * 52, r, i * 52, "#566457", 8)
        for _ in range(8):
            rrect(c, rnd.uniform(-r, r), rnd.uniform(-r, r), rnd.uniform(14, 30), rnd.uniform(14, 30), 3, "#43514a")
        c.drawRect(skia.Rect(-r, r * 0.45, r, r), P("#2a6e8f"))
    if blip:
        bx, by, col = blip
        c.drawCircle(x + bx, y + by, 11 + 2 * math.sin(t * 8), P(col))
    c.restore()
    c.drawCircle(x, y, r, P("#000000", 6))
    c.drawPath(poly([(x, y - 16), (x + 11, y + 12), (x, y + 6), (x - 11, y + 12)]), P("#ffffff"))


def banner(c, t, start, title, sub=None, color=GOLD, end=None, y=H / 2):
    """Wide horizontal 'objective complete' style banner (original wording)."""
    if t < start:
        return
    k = ease_out(at(t, start, 0.3))
    out = 1.0 if end is None else clamp((end - t) / 0.3)
    if out <= 0:
        return
    hh = 190 * k
    c.drawRect(skia.Rect(0, y - hh / 2, W, y + hh / 2), P("#000000", a=0.62 * out))
    with xf(c, W / 2, y, alpha=k * out):
        ftext(c, title, 0, 30 if sub else 40, 120, color, stroke="#000000", sw=12)
        if sub:
            ftext(c, sub, 0, 85, 40, "#ffffff", "InterDisplay-SemiBoldItalic")


# ----------------------------------------------------------------- props
def console_tall(c, x, y, s=1.0, a=1.0, glow_c=CYAN, t=0.0):
    """Generic tall white console with curved side plates (no branding)."""
    with xf(c, x, y, s, alpha=a):
        if glow_c:
            glow(c, 0, -230, 300, glow_c, 0.35)
        body = skia.Path()
        body.moveTo(-70, 0)
        body.cubicTo(-110, -150, -110, -320, -60, -470)
        body.lineTo(60, -470)
        body.cubicTo(110, -320, 110, -150, 70, 0)
        body.close()
        c.drawPath(body, skia.Paint(AntiAlias=True, Shader=linear(-110, 0, 110, 0, ["#cfd5e0", "#ffffff",
                                                                                    "#b9c0cf"])))
        rrect(c, -34, -470, 68, 470, 10, "#16161e")
        line(c, -32, -380, 32, -380, glow_c or CYAN, 4, 0.9)
        c.drawCircle(0, -440, 6, P(glow_c or CYAN))
        c.drawOval(skia.Rect(-95, -6, 95, 10), P("#000000", a=0.4))


def console_box(c, x, y, s=1.0, a=1.0, glow_c=GREEN, t=0.0):
    """Generic matte black tower console with vent top (no branding)."""
    with xf(c, x, y, s, alpha=a):
        if glow_c:
            glow(c, 0, -200, 280, glow_c, 0.3)
        c.drawOval(skia.Rect(-110, -8, 110, 12), P("#000000", a=0.4))
        rrect(c, -95, -400, 190, 400, 14, "#15171c")
        rrect(c, -95, -400, 190, 400, 14, "#2c3038", 3)
        c.drawOval(skia.Rect(-78, -418, 78, -380), P("#0a0b0e"))
        for i in range(10):
            c.drawCircle(-60 + i * 13.3, -398, 4, P(glow_c or GREEN, a=0.85))
        c.drawCircle(-62, -350, 7, P("#ffffff", a=0.9))
        rrect(c, -75, -300, 10, 70, 4, "#24272e")


def console_old(c, x, y, s=1.0, a=1.0, crack=0.0, kind=0):
    """Generic flat last-generation console slab."""
    with xf(c, x, y, s, alpha=a):
        c.drawOval(skia.Rect(-200, -8, 200, 12), P("#000000", a=0.4))
        if kind == 0:
            c.drawPath(poly([(-190, 0), (190, 0), (175, -60), (-175, -60)]), P("#1d1f26"))
            c.drawPath(poly([(-175, -60), (175, -60), (160, -110), (-160, -110)]), P("#2b2e37"))
            line(c, -170, -62, 170, -62, "#4a8cff", 3, 0.8)
        else:
            rrect(c, -200, -100, 400, 100, 16, "#202228")
            rrect(c, -200, -100, 160, 100, 16, "#2c2f37")
            c.drawCircle(150, -50, 10, P("#9fd36b"))
        if crack > 0:
            rnd = random.Random(7)
            px, py = -20, -100
            for i in range(int(8 * crack)):
                nx, ny = px + rnd.uniform(-40, 40), py + rnd.uniform(8, 18)
                line(c, px, py, nx, ny, "#ff4040", 4)
                px, py = nx, ny


def pc_tower(c, x, y, s=1.0, a=1.0, t=0.0):
    with xf(c, x, y, s, alpha=a):
        # monitor
        rrect(c, -260, -420, 360, 230, 16, "#0d0f16")
        fill_shader(c, skia.Rect(-248, -408, 88, -202), linear(-248, -408, 88, -202, ["#2a1b5e", "#0e2c4a"]))
        rrect(c, -110, -190, 60, 60, 6, "#1b1d25")
        rrect(c, -170, -134, 180, 16, 6, "#1b1d25")
        # tower with rgb
        rrect(c, 140, -380, 150, 380, 12, "#14161d")
        for i, col in enumerate((PINK, PURPLE, CYAN)):
            c.drawCircle(215, -320 + i * 90, 34, P(col, 6, 0.9))
            c.drawCircle(215, -320 + i * 90, 34, blurp(col, 10, 0.5, 8))


def game_case(c, x, y, s=1.0, a=1.0, rot=0.0, open_k=0.0, t=0.0, art=True, inside=None):
    """Original game case with sunset key-art (no title/logo). open_k 0..1 swings the cover."""
    w, h = 300, 400
    with xf(c, x, y, s, rot=rot, alpha=a):
        c.drawRect(skia.Rect(-w / 2 + 14, -h / 2 + 18, w / 2 + 14, h / 2 + 18), blurp("#000000", 16, 0.5))
        # inner tray
        rrect(c, -w / 2, -h / 2, w, h, 10, "#1a1a22")
        rrect(c, -w / 2 + 12, -h / 2 + 12, w - 24, h - 24, 8, "#26262f")
        if inside:
            inside(c)
        # cover
        cw = w * math.cos(open_k * math.pi * 0.5 * 0.98)
        if cw > 2:
            c.save()
            c.clipRect(skia.Rect(-w / 2, -h / 2, -w / 2 + cw, h / 2))
            c.translate(-w / 2, -h / 2)
            c.scale(cw / w, 1)
            rrect(c, 0, 0, w, h, 10, "#0e0a18")
            if art:
                fill_shader(c, skia.Rect(8, 8, w - 8, h - 8),
                            linear(0, 8, 0, h - 8, ["#2a0c45", "#b8306c", "#ff8a3c", "#ffcf6a"]))
                c.save()
                c.clipRect(skia.Rect(8, 8, w - 8, h - 8))
                retro_sun(c, w / 2, h * 0.62, 70, a=1.0)
                c.drawRect(skia.Rect(8, h * 0.66, w - 8, h - 8), P("#1c0a2e"))
                with xf(c, 40, h * 0.68, 0.28):
                    palm(c, 0, 0, 1, "#12061f", t, 0.5, 6)
                with xf(c, w - 50, h * 0.7, 0.24):
                    palm(c, 0, 0, 1, "#12061f", t, 0.5, -6)
                # stylized number 6 badge (generic)
                ftext(c, "VI", w / 2, 120, 110, "#ffffff", stroke="#000000", sw=10) if False else None
                c.restore()
            rrect(c, 0, 0, w, 38, 8, "#ffffff", 0.95)
            rrect(c, 18, 10, 90, 18, 4, "#0e0a18")
            c.restore()


def disc(c, x, y, r=120, a=1.0, rot=0.0, t=0.0):
    with xf(c, x, y, rot=rot, alpha=a):
        sh = skia.GradientShader.MakeSweep(0, 0, [C("#d8e0ff"), C("#ffb3e6"), C("#b3fff4"), C("#fff1b3"),
                                                  C("#d8e0ff")])
        c.drawCircle(0, 0, r, skia.Paint(AntiAlias=True, Shader=sh))
        c.drawCircle(0, 0, r, P("#9aa0b5", 3))
        c.drawCircle(0, 0, r * 0.3, P("#e8ecf5"))
        c.drawCircle(0, 0, r * 0.12, P("#0b0614"))


def code_card(c, x, y, s=1.0, a=1.0, rot=0.0, reveal=1.0):
    with xf(c, x, y, s, rot=rot, alpha=a):
        rrect(c, -150, -90, 300, 180, 14, "#f4f1ea")
        rrect(c, -150, -90, 300, 44, 14, "#0e0a18")
        c.drawRect(skia.Rect(-150, -60, 150, -46), P("#0e0a18"))
        rrect(c, -125, -10, 250, 56, 8, "#d8d2c4")
        code = "X7K2-9QF4-LM3P"
        n = int(len(code) * clamp(reveal))
        ftext(c, code[:n], 0, 30, 30, "#0e0a18", "InterDisplay-Bold")
        for i in range(24):
            c.drawRect(skia.Rect(-120 + i * 10, 56, -120 + i * 10 + (3 if i % 3 else 6), 80), P("#0e0a18"))


def price_tag(c, x, y, s, label, color=GOLD, a=1.0, rot=-8, fg="#0b0614"):
    w = tw(label, 84) + 90
    with xf(c, x, y, s, rot=rot, alpha=a):
        pth = poly([(-w / 2, -60), (w / 2 - 40, -60), (w / 2, 0), (w / 2 - 40, 60), (-w / 2, 60)])
        c.drawPath(pth, blurp("#000000", 12, 0.5))
        c.drawPath(pth, P(color))
        c.drawPath(pth, P("#000000", 5))
        c.drawCircle(w / 2 - 42, 0, 10, P("#000000"))
        ftext(c, label, -20, 30, 84, fg)


def bill(c, x, y, s=1.0, rot=0.0, a=1.0):
    with xf(c, x, y, s, rot=rot, alpha=a):
        rrect(c, -80, -38, 160, 76, 6, "#7ccf7a")
        rrect(c, -70, -28, 140, 56, 4, "#5aa85a", stroke=3)
        c.drawCircle(0, 0, 20, P("#5aa85a"))
        ftext(c, "$", 0, 12, 34, "#e9ffe6", "InterDisplay-Black")


def coin(c, x, y, r=36, a=1.0, spin=0.0):
    sx = abs(math.cos(spin)) * 0.85 + 0.15
    with xf(c, x, y, sx=sx, sy=1.0, alpha=a):
        c.drawCircle(0, 0, r, P("#e0a516"))
        c.drawCircle(0, 0, r * 0.8, P("#ffd23f"))
        ftext(c, "$", 0, r * 0.35, r, "#b8820f", "InterDisplay-Black")


def wallet(c, x, y, s=1.0, a=1.0, open_k=0.0, empty=False, burn=0.0, t=0.0):
    with xf(c, x, y, s, alpha=a):
        if not empty:
            for i in range(3):
                with xf(c, -20 + i * 18, -80 - open_k * 60 - i * 10, rot=-8 + i * 8):
                    bill(c, 0, 0, 1.0)
        rrect(c, -150, -90, 300, 180, 26, "#6b3d22")
        rrect(c, -150, -90, 300, 180, 26, "#3b2010", 5)
        line(c, -130, -70, 130, -70, "#a46b3e", 3, 0.7)
        rrect(c, 60, -30, 110, 60, 20, "#57301a")
        c.drawCircle(130, 0, 10, P("#d9b36a"))
        if burn > 0:
            for i in range(9):
                fx = -130 + i * 32
                fh = (60 + 50 * math.sin(t * 9 + i * 1.7)) * burn
                c.drawPath(poly([(fx - 22, -88), (fx + 22, -88), (fx + math.sin(t * 7 + i) * 8, -88 - fh)]),
                           blurp(ORANGE, 3, 0.9))
                c.drawPath(poly([(fx - 12, -88), (fx + 12, -88), (fx, -88 - fh * 0.6)]), P(GOLD, a=0.9))


def controller(c, x, y, s=1.0, a=1.0, rot=0.0, color="#1d2029", accent=CYAN):
    with xf(c, x, y, s, rot=rot, alpha=a):
        pth = skia.Path()
        pth.moveTo(-150, -50)
        pth.cubicTo(-60, -80, 60, -80, 150, -50)
        pth.cubicTo(200, -20, 230, 90, 190, 110)
        pth.cubicTo(150, 130, 120, 60, 80, 40)
        pth.lineTo(-80, 40)
        pth.cubicTo(-120, 60, -150, 130, -190, 110)
        pth.cubicTo(-230, 90, -200, -20, -150, -50)
        pth.close()
        c.drawPath(pth, blurp("#000000", 12, 0.45))
        c.drawPath(pth, P(color))
        c.drawPath(pth, P(mixhex(color, "#ffffff", 0.25), 3))
        # dpad
        rrect(c, -132, -22, 64, 20, 4, "#0c0d12")
        rrect(c, -110, -44, 20, 64, 4, "#0c0d12")
        for i, (bx, by) in enumerate(((110, -36), (140, -12), (80, -12), (110, 12))):
            c.drawCircle(bx, by, 13, P((PINK, TEAL, GOLD, CYAN)[i]))
        c.drawCircle(-50, 30, 24, P("#0c0d12"))
        c.drawCircle(50, 30, 24, P("#0c0d12"))
        line(c, -30, -40, 30, -40, accent, 5, 0.9)


def ssd(c, x, y, s=1.0, a=1.0, rot=0.0, fill=0.0):
    with xf(c, x, y, s, rot=rot, alpha=a):
        rrect(c, -170, -60, 340, 120, 14, "#1d2230")
        rrect(c, -150, -40, 220, 80, 8, "#2b3246")
        for i in range(6):
            c.drawRect(skia.Rect(100 + i * 10, -40, 104 + i * 10, 40), P(GOLD))
        ftext(c, "4TB", -40, 18, 46, "#ffffff", "InterDisplay-BlackItalic")


def calendar(c, x, y, s, month, day, a=1.0, circle=0.0, color=HOT, t=0.0):
    with xf(c, x, y, s, alpha=a):
        c.drawRect(skia.Rect(-150 + 12, -170 + 16, 150 + 12, 170 + 16), blurp("#000000", 14, 0.5))
        rrect(c, -150, -170, 300, 340, 22, "#fbf6ee")
        rrect(c, -150, -170, 300, 100, 22, color)
        c.drawRect(skia.Rect(-150, -100, 150, -70), P(color))
        for i in (-80, 80):
            rrect(c, i - 10, -190, 20, 50, 8, "#2a2a35")
        ftext(c, month, 0, -100, 56, "#ffffff")
        ftext(c, str(day), 0, 95, 170, "#1a1426")
        if circle > 0:
            pth = skia.Path()
            pth.addArc(skia.Rect(-120, -60, 120, 140), -90, 360 * clamp(circle))
            c.drawPath(pth, P(RED, 10, 0.9))


def progress_bar(c, x, y, w, frac, color=TEAL, a=1.0, h=46, label=None):
    with xf(c, x, y, alpha=a):
        rrect(c, -w / 2, -h / 2, w, h, h / 2, "#000000", 0.6)
        rrect(c, -w / 2, -h / 2, w, h, h / 2, "#ffffff", 0.9, stroke=4)
        if frac > 0:
            c.save()
            c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 6, -h / 2 + 6, w - 12, h - 12),
                                              h / 2 - 6, h / 2 - 6), skia.ClipOp.kIntersect, True)
            fill_shader(c, skia.Rect(-w / 2, -h / 2, -w / 2 + (w) * clamp(frac), h / 2),
                        linear(-w / 2, 0, w / 2, 0, [color, mixhex(color, "#ffffff", 0.4)]))
            c.restore()
        if label:
            ftext(c, label, 0, -h, 40, "#ffffff", "InterDisplay-Black", stroke="#000000", sw=6)


def wifi(c, x, y, s=1.0, bars=3, a=1.0, color="#ffffff"):
    with xf(c, x, y, s, alpha=a):
        for i in range(3):
            r = 40 + i * 42
            pth = skia.Path()
            pth.addArc(skia.Rect(-r, -r, r, r), -135, 90)
            c.drawPath(pth, P(color if i < bars else "#ffffff", 20, 1.0 if i < bars else 0.18))
        c.drawCircle(0, 0, 14, P(color))


def padlock(c, x, y, s=1.0, a=1.0, closed=1.0, color=GOLD):
    with xf(c, x, y, s, alpha=a):
        pth = skia.Path()
        lift = (1 - closed) * 50
        pth.addArc(skia.Rect(-60, -150 - lift, 60, -30 - lift), 180, 180)
        c.drawPath(pth, P("#c9ccd6", 22))
        line(c, -60, -90 - lift, -60, -40 - lift * 0.0 if closed > 0.5 else -90, "#c9ccd6", 22)
        line(c, 60, -90 - lift, 60, -40, "#c9ccd6", 22)
        rrect(c, -95, -50, 190, 150, 22, color)
        c.drawCircle(0, 15, 18, P("#2a1c05"))
        rrect(c, -7, 15, 14, 45, 5, "#2a1c05")


def shield_badge(c, x, y, s, label, color=RED, a=1.0):
    with xf(c, x, y, s, alpha=a):
        pth = poly([(0, -140), (120, -100), (110, 40), (0, 140), (-110, 40), (-120, -100)])
        c.drawPath(pth, blurp("#000000", 14, 0.5))
        c.drawPath(pth, P(color))
        c.drawPath(pth, P("#ffffff", 8))
        ftext(c, label, 0, 30, 90, "#ffffff")


def storefront(c, x, y, s=1.0, t=0.0, sign="GAMES", lit=1.0, crowd=0):
    """Neon game-store facade with ground at y."""
    with xf(c, x, y, s):
        rrect(c, -480, -560, 960, 560, 6, "#1a1030")
        c.drawRect(skia.Rect(-480, -560, 480, -520), P("#2b1a4a"))
        # window
        fill_shader(c, skia.Rect(-420, -330, 420, -20), linear(0, -330, 0, -20, ["#3a2a6a", "#ff9a6a"]))
        for i in range(5):
            rrect(c, -380 + i * 160, -200, 120, 170, 6, ("#21e6d2", "#ff3d8b", "#ffd23f", "#7a2cff",
                                                          "#3ad7ff")[i], 0.55)
        line(c, -420, -330, 420, -330, "#0a0612", 10)
        line(c, 0, -330, 0, -20, "#0a0612", 8)
        fl = 1.0 if (math.sin(t * 23) > -0.92) else 0.35
        neon_rect(c, -360, -500, 720, 130, 30, PINK, 7, lit, fl)
        neon_text(c, sign, 0, -405, 92, TEAL, lit, fl)


def game_box_pedestal(c, x, y, t, lid=0.0, spot=1.0, rattle=0.0, inside=None):
    """Mystery boxed copy on a pedestal under a spotlight."""
    fill_shader(c, skia.Rect(x - 420, 0, x + 420, y), linear(x, 0, x, y, [("#fff3c4", 0.0), ("#fff3c4", 0.16 * spot)]))
    c.drawPath(poly([(x - 90, 0), (x + 90, 0), (x + 380, y + 20), (x - 380, y + 20)]),
               P("#fff3c4", a=0.10 * spot))
    c.drawOval(skia.Rect(x - 380, y - 40, x + 380, y + 60), P("#fff3c4", a=0.12 * spot))
    rrect(c, x - 260, y - 40, 520, 340, 12, "#1c1430")
    rrect(c, x - 280, y - 70, 560, 50, 10, "#2a1f48")
    rx = math.sin(t * 60) * 8 * rattle
    game_case(c, x + rx, y - 280, 1.0, rot=math.sin(t * 47) * 3 * rattle, open_k=lid, t=t, inside=inside)


def iceberg(c, x, y, s=1.0, t=0.0, reveal=1.0):
    with xf(c, x, y, s):
        tip = poly([(-160, 0), (-60, -180), (0, -230), (80, -150), (170, 0)])
        c.drawPath(tip, P("#eaf6ff"))
        c.drawPath(poly([(0, -230), (80, -150), (170, 0), (40, 0)]), P("#bfdcf2"))
        under = poly([(-160, 0), (170, 0), (360, 160), (300, 420), (0, 560), (-320, 400), (-380, 150)])
        p = P("#7fb6de", a=0.75 * reveal)
        c.drawPath(under, p)
        line(c, -700, 0, 700, 0, "#ffffff", 4, 0.7)


def hourglass(c, x, y, s=1.0, frac=0.5, rot=0.0, a=1.0):
    with xf(c, x, y, s, rot=rot, alpha=a):
        rrect(c, -110, -170, 220, 26, 8, GOLD)
        rrect(c, -110, 144, 220, 26, 8, GOLD)
        glass = poly([(-90, -144), (90, -144), (14, 0), (90, 144), (-90, 144), (-14, 0)])
        c.drawPath(glass, P("#cfe8ff", a=0.25))
        c.drawPath(glass, P("#cfe8ff", 5, 0.8))
        top = 1 - frac
        if top > 0:
            yy = -144 + 144 * (1 - top)
            wv = 14 + 76 * (1 - (yy + 144) / 144)
            c.drawPath(poly([(-wv, yy), (wv, yy), (14, 0), (-14, 0)]), P(ORANGE))
        if frac > 0:
            hh = 144 * frac
            c.drawPath(poly([(-90, 144), (90, 144), (90 - 76 * frac, 144 - hh), (-90 + 76 * frac, 144 - hh)]),
                       P(ORANGE))
        line(c, 0, 0, 0, 140, ORANGE, 4, 0.8)


def qmark(c, x, y, size=260, color=GOLD, a=1.0, t=0.0):
    ftext(c, "?", x, y + size * 0.35 + math.sin(t * 3) * 8, size, color, a=a, stroke="#000000", sw=size * 0.08,
          glow_c=color, glow_r=size * 0.12)


def receipt(c, x, y, lines, k=1.0, total=None, a=1.0):
    n = len(lines)
    hh = 120 + 80 * n * k + (110 if total and k >= 1 else 0)
    with xf(c, x, y, alpha=a):
        c.drawRect(skia.Rect(-230 + 14, 16, 230 + 14, hh + 16), blurp("#000000", 14, 0.5))
        c.drawRect(skia.Rect(-230, 0, 230, hh), P("#f7f3ea"))
        for i in range(24):
            c.drawPath(poly([(-230 + i * 19.2, hh), (-230 + i * 19.2 + 9.6, hh + 14), (-230 + (i + 1) * 19.2, hh)]),
                       P("#f7f3ea"))
        ftext(c, "RECEIPT", 0, 70, 44, "#1a1426", "InterDisplay-Black")
        for i, (name, price) in enumerate(lines):
            if i + 1 > n * k + 0.01:
                break
            yy = 150 + i * 80
            ftext(c, name, -190, yy, 38, "#1a1426", "InterDisplay-SemiBold", align="left")
            ftext(c, price, 190, yy, 38, "#1a1426", "InterDisplay-Bold", align="right")
        if total and k >= 1:
            line(c, -190, 120 + 80 * n, 190, 120 + 80 * n, "#1a1426", 3)
            ftext(c, total, 0, 200 + 80 * n, 72, HOT, "InterDisplay-Black")


def gear(c, x, y, r, rot=0.0, color="#c9ccd6", a=1.0):
    with xf(c, x, y, rot=rot, alpha=a):
        for i in range(8):
            with xf(c, 0, 0, rot=i * 45):
                rrect(c, -r * 0.18, -r * 1.25, r * 0.36, r * 0.5, 4, color)
        c.drawCircle(0, 0, r, P(color))
        c.drawCircle(0, 0, r * 0.4, P("#0b0614"))


def gift(c, x, y, s=1.0, a=1.0, lid=0.0, color=PINK, rib=GOLD):
    with xf(c, x, y, s, alpha=a):
        rrect(c, -150, -220, 300, 220, 10, color)
        c.drawRect(skia.Rect(-22, -220, 22, 0), P(rib))
        with xf(c, 0, -220 - lid * 120, rot=-lid * 20):
            rrect(c, -170, -50, 340, 60, 10, mixhex(color, "#ffffff", 0.15))
            c.drawRect(skia.Rect(-22, -50, 22, 10), P(rib))
            c.drawOval(skia.Rect(-80, -100, 0, -45), P(rib, 14))
            c.drawOval(skia.Rect(0, -100, 80, -45), P(rib, 14))


def cart_icon(c, x, y, s=1.0, color="#ffffff"):
    with xf(c, x, y, s):
        c.drawPath(poly([(-90, -60), (-60, -60), (-30, 40), (70, 40), (90, -30), (-50, -30)], close=False),
                   P(color, 14))
        c.drawCircle(-20, 70, 14, P(color))
        c.drawCircle(60, 70, 14, P(color))


def tv(c, x, y, s=1.0, screen=None, a=1.0, t=0.0):
    with xf(c, x, y, s, alpha=a):
        rrect(c, -330, -210, 660, 380, 18, "#0a0a10")
        c.save()
        c.clipRect(skia.Rect(-312, -192, 312, 152))
        if screen:
            screen(c)
        else:
            fill_shader(c, skia.Rect(-312, -192, 312, 152), linear(0, -192, 0, 152, ["#1c1240", "#ff7a5a"]))
        c.restore()
        c.drawPath(poly([(-312, -192), (-60, -192), (-200, 152), (-312, 152)]), P("#ffffff", a=0.05))
        rrect(c, -60, 170, 120, 20, 6, "#0a0a10")
        rrect(c, -140, 188, 280, 14, 6, "#0a0a10")


def couch(c, x, y, s=1.0, color="#3b2d6a"):
    with xf(c, x, y, s):
        rrect(c, -330, -230, 660, 170, 40, mixhex(color, "#000000", 0.2))
        rrect(c, -360, -110, 720, 120, 30, color)
        rrect(c, -400, -170, 90, 190, 30, mixhex(color, "#ffffff", 0.08))
        rrect(c, 310, -170, 90, 190, 30, mixhex(color, "#ffffff", 0.08))
        rrect(c, -330, 0, 30, 40, 6, "#151020")
        rrect(c, 300, 0, 30, 40, 6, "#151020")


def room_bg(c, t, wall="#24163f", floor="#150d26", lamp=True, window_kind="night"):
    fill_shader(c, skia.Rect(0, 0, W, 780), linear(0, 0, 0, 780, [mixhex(wall, "#000000", 0.4), wall]))
    fill_shader(c, skia.Rect(0, 780, W, H), linear(0, 780, 0, H, [floor, "#07040e"]))
    # window with city
    wx, wy, ww, wh = 1250, 140, 520, 400
    c.save()
    c.clipRect(skia.Rect(wx, wy, wx + ww, wy + wh))
    c.translate(wx, wy)
    c.scale(ww / W, wh / H)
    sky(c, window_kind, 760, t)
    for img in city_layers_t(window_kind, 760):
        blit(c, img, 0, 0)
    c.restore()
    rrect(c, wx - 14, wy - 14, ww + 28, wh + 28, 6, "#0c0818", stroke=18)
    line(c, wx + ww / 2, wy, wx + ww / 2, wy + wh, "#0c0818", 10)
    if lamp:
        glow(c, 260, 380, 420, ORANGE, 0.22)
    # neon strip
    c.drawRect(skia.Rect(0, 770, W, 776), blurp(PINK, 6, 0.6))


def grid_board(c, t, top="#170a33", bottom="#06030f", col=PINK):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, [top, bottom]))
    # synth perspective grid floor
    hy = 640
    for i in range(-20, 21):
        x2 = W / 2 + i * 260
        line(c, W / 2 + i * 22, hy, x2, H + 200, col, 2, 0.28)
    off = (t * 0.6) % 1.0
    for j in range(14):
        k = (j + off) / 14
        yy = hy + (H - hy) * k ** 2.2
        line(c, 0, yy, W, yy, col, 2, 0.3 * k + 0.05)
    fill_shader(c, skia.Rect(0, hy - 120, W, hy + 40), linear(0, hy - 120, 0, hy + 40, [(col, 0), (col, 0.18),
                                                                                         (col, 0)]))
