"""Drawing primitives, characters, props and backgrounds for the 2D video.

Everything is flat vector art drawn with skia so the renderer is fully
deterministic: frame N always looks the same.
"""
import math
import random
from contextlib import contextmanager

import skia

W, H = 1920, 1080
HORIZON = 600
FONT_DIR = "/usr/share/fonts/opentype/inter/"

_tf_cache = {}
_font_cache = {}


def typeface(name):
    if name not in _tf_cache:
        _tf_cache[name] = skia.Typeface.MakeFromFile(FONT_DIR + name)
    return _tf_cache[name]


def font(size, weight="Black"):
    key = (weight, round(size, 1))
    if key not in _font_cache:
        f = skia.Font(typeface(f"Inter-{weight}.otf"), size)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        _font_cache[key] = f
    return _font_cache[key]


# ---------------------------------------------------------------- utilities
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def back_out(t):
    t = clamp(t)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def at(t, start, dur=0.45):
    """0..1 progress of an animation that starts at absolute time `start`."""
    return clamp((t - start) / dur)


def window(t, a, b, fade=0.3):
    """1 inside [a, b], fading in/out over `fade` seconds."""
    return clamp((t - a) / fade) * clamp((b - t) / fade)


def hexrgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def C(h, a=1.0):
    r, g, b = hexrgb(h)
    return skia.ColorSetARGB(int(clamp(a) * 255), r, g, b)


def mixhex(h1, h2, t):
    a, b = hexrgb(h1), hexrgb(h2)
    t = clamp(t)
    return "#%02x%02x%02x" % tuple(int(lerp(x, y, t)) for x, y in zip(a, b))


def P(color, stroke=None, a=1.0):
    if isinstance(color, str):
        color = C(color, a)
    p = skia.Paint(AntiAlias=True, Color=color)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


@contextmanager
def xf(c, x=0, y=0, s=1.0, rot=0.0, alpha=1.0, sx=None, sy=None):
    c.save()
    c.translate(x, y)
    if rot:
        c.rotate(rot)
    if sx is not None or sy is not None:
        c.scale(sx if sx is not None else s, sy if sy is not None else s)
    elif s != 1:
        c.scale(s, s)
    layered = alpha < 0.999
    if layered:
        c.saveLayerAlpha(None, int(clamp(alpha) * 255))
    try:
        yield
    finally:
        if layered:
            c.restore()
        c.restore()


def rrect(c, x, y, w, h, r, color, a=1.0, stroke=None):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), P(color, stroke, a))


def poly(points, close=True):
    p = skia.Path()
    p.moveTo(*points[0])
    for pt in points[1:]:
        p.lineTo(*pt)
    if close:
        p.close()
    return p


def line(c, x1, y1, x2, y2, color, w, a=1.0):
    c.drawLine(x1, y1, x2, y2, P(color, w, a))


def text(c, s, x, y, size, color="#ffffff", weight="Black", align="center",
         a=1.0, outline=None, ow=0, shadow=False):
    f = font(size, weight)
    w = f.measureText(s)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    if shadow:
        c.drawString(s, x + size * 0.05, y + size * 0.07, f, P("#000000", a=0.35 * a))
    if outline:
        c.drawString(s, x, y, f, P(outline, ow, a))
    c.drawString(s, x, y, f, P(color, a=a))
    return w


def text_width(s, size, weight="Black"):
    return font(size, weight).measureText(s)


def linear(x1, y1, x2, y2, colors, pos=None):
    return skia.GradientShader.MakeLinear(
        [skia.Point(x1, y1), skia.Point(x2, y2)], [C(*c) if isinstance(c, tuple) else C(c) for c in colors], pos)


def radial(x, y, r, colors, pos=None):
    return skia.GradientShader.MakeRadial(
        skia.Point(x, y), r, [C(*c) if isinstance(c, tuple) else C(c) for c in colors], pos)


def fill_shader(c, rect, shader):
    c.drawRect(rect, skia.Paint(Shader=shader, AntiAlias=True))


def glow(c, x, y, r, color, a=0.6):
    fill_shader(c, skia.Rect(x - r, y - r, x + r, y + r), radial(x, y, r, [(color, a), (color, 0)]))


def drop_path(x, y, r):
    p = skia.Path()
    p.moveTo(x, y - r * 1.9)
    p.cubicTo(x + r * 0.35, y - r * 1.2, x + r, y - r * 0.6, x + r, y)
    p.cubicTo(x + r, y + r * 0.6, x + r * 0.55, y + r, x, y + r)
    p.cubicTo(x - r * 0.55, y + r, x - r, y + r * 0.6, x - r, y)
    p.cubicTo(x - r, y - r * 0.6, x - r * 0.35, y - r * 1.2, x, y - r * 1.9)
    p.close()
    return p


def drop(c, x, y, r, color="#4cc3ff", a=1.0, shine=True):
    c.drawPath(drop_path(x, y, r), P(color, a=a))
    if shine:
        c.drawCircle(x - r * 0.35, y - r * 0.1, r * 0.22, P("#ffffff", a=0.6 * a))


def sparkle(c, x, y, r, color="#ffffff", a=1.0, rot=0):
    with xf(c, x, y, rot=rot):
        p = skia.Path()
        k = r * 0.22
        p.moveTo(0, -r)
        p.quadTo(k, -k, r, 0)
        p.quadTo(k, k, 0, r)
        p.quadTo(-k, k, -r, 0)
        p.quadTo(-k, -k, 0, -r)
        p.close()
        c.drawPath(p, P(color, a=a))


def check_mark(c, x, y, s, color="#2ecc71", a=1.0, prog=1.0):
    pts = [(-0.5, 0.0), (-0.15, 0.35), (0.55, -0.4)]
    pts = [(x + px * s, y + py * s) for px, py in pts]
    if prog <= 0:
        return
    p = skia.Path()
    p.moveTo(*pts[0])
    seg = prog * 2
    if seg <= 1:
        p.lineTo(lerp(pts[0][0], pts[1][0], seg), lerp(pts[0][1], pts[1][1], seg))
    else:
        p.lineTo(*pts[1])
        p.lineTo(lerp(pts[1][0], pts[2][0], seg - 1), lerp(pts[1][1], pts[2][1], seg - 1))
    c.drawPath(p, P(color, s * 0.18, a))


def cross_mark(c, x, y, s, color="#ff3b3b", a=1.0):
    line(c, x - s / 2, y - s / 2, x + s / 2, y + s / 2, color, s * 0.18, a)
    line(c, x + s / 2, y - s / 2, x - s / 2, y + s / 2, color, s * 0.18, a)


def pill(c, x, y, label, size=42, bg="#ffffff", fg="#1b1b2f", a=1.0, s=1.0, weight="Black", pad=28):
    """Centered pill label."""
    w = text_width(label, size, weight) + pad * 2
    h = size * 1.55
    with xf(c, x, y, s=s, alpha=a):
        rrect(c, -w / 2 + 4, -h / 2 + 7, w, h, h / 2, "#000000", 0.25)
        rrect(c, -w / 2, -h / 2, w, h, h / 2, bg)
        text(c, label, 0, size * 0.36, size, fg, weight)
    return w


def card(c, x, y, w, h, bg="#ffffff", a=1.0, r=34):
    rrect(c, x + 6, y + 10, w, h, r, "#000000", 0.22 * a)
    rrect(c, x, y, w, h, r, bg, a)


def bubble(c, x, y, label, size=46, a=1.0, s=1.0, tail=(-1, 1), bg="#ffffff", fg="#1b1b2f", spiky=False, t=0):
    """Speech bubble centered at (x, y) with tail pointing toward `tail` direction."""
    w = text_width(label, size) + 70
    h = size * 1.9
    with xf(c, x, y, s=s, alpha=a):
        if spiky:
            n = 18
            pts = []
            for i in range(n * 2):
                ang = i / (n * 2) * math.tau
                rr = (1.0 if i % 2 == 0 else 0.8) + 0.04 * math.sin(t * 20 + i)
                pts.append((math.cos(ang) * (w * 0.62) * rr, math.sin(ang) * (h * 0.85) * rr))
            c.drawPath(poly(pts), P(bg))
        else:
            tx, ty = tail
            tp = poly([(tx * w * 0.18, h * 0.3), (tx * w * 0.42, h * 0.95 * ty), (tx * w * 0.02, h * 0.38)])
            c.drawPath(tp, P(bg))
            rrect(c, -w / 2, -h / 2, w, h, h / 2, bg)
        text(c, label, 0, size * 0.36, size, fg)


# ---------------------------------------------------------------- scenery
SKIES = {
    "noon": ("#3d9be0", "#9fd3f2", "#fbe7bd"),
    "hot": ("#f0a04b", "#f8c77e", "#fff0c8"),
    "night": ("#050a1f", "#101c45", "#24356b"),
    "sunrise": ("#4b5bb5", "#ee8f6f", "#ffd49a"),
    "flash": ("#7cc4e8", "#bfe3f0", "#ffeccc"),
}
GROUND = {
    "noon": ("#f2c27b", "#e2a45c"),
    "hot": ("#f3b867", "#d98d45"),
    "night": ("#3b3a5e", "#2a2947"),
    "sunrise": ("#e6a46a", "#c97f4b"),
    "flash": ("#efc98c", "#dcaa68"),
}

_rng = random.Random(7)
STARS = [(_rng.uniform(0, W), _rng.uniform(0, HORIZON - 40), _rng.uniform(1.2, 3.2), _rng.uniform(0, 6.28))
         for _ in range(170)]


def ridge(c, base, amp, freqs, color, scroll=0.0, a=1.0, step=24):
    p = skia.Path()
    p.moveTo(-10, H)
    for x in range(-10, W + step + 10, step):
        X = x + scroll
        y = base - amp * sum(w * math.sin(X * f + ph) for f, w, ph in freqs)
        p.lineTo(x, y)
    p.lineTo(W + 10, H)
    p.close()
    c.drawPath(p, P(color, a=a))


def cactus(c, x, y, s, color="#4f8a4b"):
    with xf(c, x, y, s):
        rrect(c, -16, -170, 32, 175, 16, color)
        rrect(c, -58, -120, 24, 70, 12, color)
        rrect(c, -58, -70, 50, 22, 11, color)
        rrect(c, 34, -140, 24, 80, 12, color)
        rrect(c, 8, -82, 50, 22, 11, color)
        line(c, 0, -160, 0, 0, "#3d6f3a", 4, 0.5)


def rock(c, x, y, s, color="#b9875a"):
    with xf(c, x, y, s):
        c.drawPath(poly([(-60, 0), (-45, -38), (-10, -55), (30, -42), (60, 0)]), P(color))
        c.drawPath(poly([(-10, -55), (30, -42), (60, 0), (15, 0)]), P("#000000", a=0.12))


def draw_sky(c, tod, t, sun_pos=None, sun_r=90):
    top, mid, hor = SKIES[tod]
    fill_shader(c, skia.Rect(0, 0, W, HORIZON + 4), linear(0, 0, 0, HORIZON, [top, mid, hor], [0, 0.62, 1]))
    if tod == "night":
        for (x, y, r, ph) in STARS:
            a = 0.55 + 0.45 * math.sin(t * 2.2 + ph * 3)
            c.drawCircle(x, y, r, P("#ffffff", a=a))
        mx, my = sun_pos or (1500, 170)
        glow(c, mx, my, 260, "#c9d8ff", 0.35)
        c.drawCircle(mx, my, 70, P("#f3f1e4"))
        c.drawCircle(mx - 22, my - 14, 13, P("#d9d6c4"))
        c.drawCircle(mx + 18, my + 20, 9, P("#d9d6c4"))
        c.drawCircle(mx + 26, my - 22, 6, P("#d9d6c4"))
        return
    sx, sy = sun_pos or {"noon": (1520, 150), "hot": (1500, 140), "sunrise": (420, 470), "flash": (1550, 160)}[tod]
    pulse = 1 + 0.03 * math.sin(t * 2.5)
    glow(c, sx, sy, sun_r * 4.2 * pulse, "#fff3c4", 0.75 if tod == "hot" else 0.55)
    # rays
    with xf(c, sx, sy, rot=t * 6):
        for i in range(12):
            with xf(c, 0, 0, rot=i * 30):
                c.drawPath(poly([(-9, -sun_r * 1.25), (9, -sun_r * 1.25), (0, -sun_r * 1.75 * pulse)]),
                           P("#fff6d0", a=0.5))
    c.drawCircle(sx, sy, sun_r, P("#fff6cf"))
    c.drawCircle(sx, sy, sun_r * 0.82, P("#ffe47a"))


def draw_ground(c, tod, scroll=0.0, road=True, road_y=820, props=True, t=0.0):
    g1, g2 = GROUND[tod]
    night = tod == "night"
    # mountains
    far = mixhex("#c98f74", "#4a4f88", 0.85 if night else 0.0)
    if tod == "sunrise":
        far = "#b77678"
    near = mixhex("#d9a06a", "#33335a", 0.9 if night else 0.0)
    if tod == "sunrise":
        near = "#c8875f"
    ridge(c, HORIZON - 30, 70, [(0.0021, 1.0, 0.3), (0.0057, 0.45, 1.3), (0.013, 0.12, 2.2)], far, scroll * 0.08)
    ridge(c, HORIZON + 10, 38, [(0.0034, 1.0, 2.0), (0.009, 0.3, 0.4)], near, scroll * 0.2)
    fill_shader(c, skia.Rect(0, HORIZON + 10, W, H), linear(0, HORIZON, 0, H, [g1, g2]))
    # dune bands
    ridge(c, 700, 22, [(0.004, 1.0, 0.9), (0.011, 0.3, 0.1)], mixhex(g1, "#ffffff", 0.12), scroll * 0.45, a=0.6)
    if props:
        sp = scroll * 0.5
        for i in range(-1, 6):
            base = i * 520 - (sp % 520)
            rock(c, base + 140, 735, 0.5, mixhex("#b9875a", "#2a2947", 0.7 if night else 0))
        sp2 = scroll * 0.75
        for i in range(-1, 4):
            base = i * 860 - (sp2 % 860)
            cactus(c, base + 300, 770, 0.75, mixhex("#4f8a4b", "#1f3340", 0.7 if night else 0))
    if road:
        asphalt = mixhex("#5a5560", "#25243a", 0.75 if night else 0)
        c.drawRect(skia.Rect(0, road_y - 70, W, road_y + 70), P(asphalt))
        c.drawRect(skia.Rect(0, road_y - 70, W, road_y - 62), P("#ffffff", a=0.25))
        c.drawRect(skia.Rect(0, road_y + 62, W, road_y + 70), P("#ffffff", a=0.25))
        off = scroll % 240
        for i in range(-1, 10):
            x = i * 240 - off
            rrect(c, x, road_y - 6, 130, 12, 6, "#ffd34d", 0.85 if not night else 0.4)
        # foreground sand lip
        ridge(c, road_y + 110, 8, [(0.01, 1.0, 0.0)], g2, scroll, a=1.0)
        if props:
            off3 = scroll * 1.2 % 700
            for i in range(-1, 4):
                rock(c, i * 700 - off3 + 500, road_y + 200, 0.9, mixhex("#a8774d", "#22213a", 0.7 if night else 0))


def heat_shimmer(c, t, strength=1.0, y0=HORIZON - 40, y1=HORIZON + 120):
    if strength <= 0:
        return
    for i in range(7):
        y = lerp(y0, y1, i / 6) + 6 * math.sin(t * 3 + i)
        p = skia.Path()
        p.moveTo(0, y)
        for x in range(0, W + 40, 40):
            p.lineTo(x, y + 5 * math.sin(x * 0.02 + t * 6 + i * 1.7))
        c.drawPath(p, P("#ffffff", 3, 0.10 * strength))


def scene_bg(c, tod, t, scroll=0.0, road=True, sun_pos=None, shimmer=0.0, props=True):
    draw_sky(c, tod, t, sun_pos)
    draw_ground(c, tod, scroll, road, props=props, t=t)
    heat_shimmer(c, t, shimmer)


def vignette(c, a=0.45):
    fill_shader(c, skia.Rect(0, 0, W, H),
                radial(W / 2, H / 2, W * 0.75, [("#000000", 0), ("#000000", 0), ("#000000", a)], [0, 0.55, 1]))


def info_bg(c, t, top="#14213d", bottom="#1d3557", dots="#ffffff"):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, [top, bottom]))
    r = random.Random(3)
    for i in range(40):
        x = (r.uniform(0, W) + t * r.uniform(5, 20)) % W
        y = (r.uniform(0, H) - t * r.uniform(8, 25)) % H
        c.drawCircle(x, y, r.uniform(2, 6), P(dots, a=0.07))


def birds(c, t, cx=900, cy=220, n=2):
    for i in range(n):
        ang = t * 0.5 + i * math.pi
        x = cx + math.cos(ang) * 160
        y = cy + math.sin(ang) * 40
        flap = 12 * math.sin(t * 8 + i)
        p = skia.Path()
        p.moveTo(x - 26, y - flap)
        p.quadTo(x - 12, y - 10, x, y)
        p.quadTo(x + 12, y - 10, x + 26, y - flap)
        c.drawPath(p, P("#3b2a2a", 5, 0.7))


# ---------------------------------------------------------------- characters
CHARS = {
    "you": dict(skin="#b97a50", hair="#2a1b14", shirt="#1f9e9a", pants="#2f3e5c", shoe="#f1f1f1",
                cap="#e4572e", head=50, torso=118, arm=(60, 56), leg=(70, 68), width=40),
    "noor": dict(skin="#d39a6c", hair="#3a2418", shirt="#ffc93c", pants="#ff7aa8", shoe="#ff4f86",
                 cap=None, head=48, torso=78, arm=(42, 40), leg=(46, 44), width=31),
    "ines": dict(skin="#8d5a3b", hair="#1c120e", shirt="#5b7d3a", pants="#3c4a2a", shoe="#4a3426",
                 cap="#c9a26a", head=48, torso=118, arm=(60, 56), leg=(70, 68), width=42),
    "gran": dict(skin="#c48c64", hair="#d9d9d9", shirt="#8e5ea2", pants="#5c3a6e", shoe="#3a2a2a",
                 cap=None, head=50, torso=110, arm=(58, 54), leg=(66, 64), width=42),
}

POSES = {
    "stand": dict(la=(-8, 0), ra=(8, 0), ll=(4, 0), rl=(-4, 0)),
    "sit": dict(la=(18, -20), ra=(-18, 20), ll=(-78, 95), rl=(78, -95)),
    "hug": dict(la=(40, 80), ra=(-40, -80), ll=(-78, 95), rl=(78, -95)),
    "wave": dict(la=(-8, 0), ra=(150, 20), ll=(4, 0), rl=(-4, 0)),
    "give": dict(la=(-8, 0), ra=(80, 0), ll=(4, 0), rl=(-4, 0)),
    "give_l": dict(la=(-80, 0), ra=(8, 0), ll=(4, 0), rl=(-4, 0)),
    "hold": dict(la=(30, 70), ra=(-30, -70), ll=(4, 0), rl=(-4, 0)),
    "mirror_up": dict(la=(-8, 0), ra=(160, -10), ll=(4, 0), rl=(-4, 0)),
    "mirror_selfie": dict(la=(-8, 0), ra=(130, 60), ll=(4, 0), rl=(-4, 0)),
    "sit_mirror": dict(la=(18, -20), ra=(150, 0), ll=(-78, 95), rl=(78, -95)),
    "bino": dict(la=(150, 40), ra=(-150, -40), ll=(4, 0), rl=(-4, 0)),
    "drink": dict(la=(18, -20), ra=(-20, -150), ll=(-78, 95), rl=(78, -95)),
    "angry": dict(la=(40, 20), ra=(-60, -60), ll=(10, 0), rl=(-10, 0)),
    "head_hold": dict(la=(-130, -85), ra=(130, 85), ll=(-78, 95), rl=(78, -95)),
    "tug": dict(la=(-8, 0), ra=(60, 10), ll=(4, 0), rl=(-4, 0)),
}


def walk_pose(t, speed=6.0, amp=28):
    s = math.sin(t * speed)
    return dict(la=(-amp * s * 0.8, -15), ra=(amp * s * 0.8, 15), ll=(amp * s, max(0, -s) * 30),
                rl=(-amp * s, max(0, s) * 30))


def _limb(c, x, y, a1, a2, l1, l2, w, col1, col2, end=None, endcol=None, endr=0):
    r1 = math.radians(a1)
    x2, y2 = x + math.sin(r1) * l1, y + math.cos(r1) * l1
    r2 = math.radians(a1 + a2)
    x3, y3 = x2 + math.sin(r2) * l2, y2 + math.cos(r2) * l2
    line(c, x2, y2, x3, y3, col2, w * 0.9)
    line(c, x, y, x2, y2, col1, w)
    if end == "hand":
        c.drawCircle(x3, y3, endr, P(endcol))
    elif end == "shoe":
        c.drawOval(skia.Rect(x3 - endr * 1.3, y3 - endr * 0.6, x3 + endr * 1.3, y3 + endr * 0.75), P(endcol))
    return x3, y3


def draw_head(c, x, y, who, expr="neutral", t=0.0, look=(0, 0), talk=0.0, sweat=0.0, r=None, hat=True):
    d = CHARS[who]
    r = r or d["head"]
    skin, hair = d["skin"], d["hair"]
    lx, ly = look
    # back hair
    if who == "noor":
        for sgn in (-1, 1):
            c.drawCircle(x + sgn * r * 1.02, y + r * 0.1, r * 0.42, P(hair))
            c.drawCircle(x + sgn * r * 0.82, y - r * 0.15, r * 0.14, P("#ff4f86"))
        c.drawCircle(x, y - r * 0.08, r * 1.04, P(hair))
    elif who == "gran":
        c.drawCircle(x, y - r * 1.0, r * 0.45, P(hair))
        c.drawCircle(x, y - r * 0.05, r * 1.05, P(hair))
    else:
        c.drawCircle(x, y - r * 0.05, r * 1.02, P(hair))
    # ears + face
    for sgn in (-1, 1):
        c.drawCircle(x + sgn * r * 0.95, y + r * 0.12, r * 0.2, P(skin))
    c.drawCircle(x, y + r * 0.06, r * 0.95, P(skin))
    # front hair / hats
    if who == "noor":
        p = skia.Path()
        p.moveTo(x - r * 0.95, y - r * 0.05)
        p.quadTo(x - r * 0.9, y - r * 1.05, x, y - r * 1.02)
        p.quadTo(x + r * 0.9, y - r * 1.05, x + r * 0.95, y - r * 0.05)
        p.quadTo(x + r * 0.5, y - r * 0.55, x + r * 0.1, y - r * 0.45)
        p.quadTo(x - r * 0.4, y - r * 0.6, x - r * 0.95, y - r * 0.05)
        c.drawPath(p, P(hair))
    elif who == "gran":
        p = skia.Path()
        p.moveTo(x - r * 0.95, y)
        p.quadTo(x, y - r * 1.4, x + r * 0.95, y)
        p.quadTo(x, y - r * 0.6, x - r * 0.95, y)
        c.drawPath(p, P(hair))
    elif d["cap"] and hat:
        if who == "ines":
            c.drawOval(skia.Rect(x - r * 1.45, y - r * 0.72, x + r * 1.45, y - r * 0.38), P("#a9834f"))
            p = skia.Path()
            p.moveTo(x - r * 0.75, y - r * 0.55)
            p.quadTo(x - r * 0.7, y - r * 1.45, x, y - r * 1.4)
            p.quadTo(x + r * 0.7, y - r * 1.45, x + r * 0.75, y - r * 0.55)
            p.close()
            c.drawPath(p, P(d["cap"]))
            c.drawRect(skia.Rect(x - r * 0.75, y - r * 0.72, x + r * 0.75, y - r * 0.58), P("#6b4f2a"))
        else:
            p = skia.Path()
            p.moveTo(x - r * 0.98, y - r * 0.25)
            p.quadTo(x - r * 0.95, y - r * 1.12, x, y - r * 1.1)
            p.quadTo(x + r * 0.95, y - r * 1.12, x + r * 0.98, y - r * 0.25)
            p.close()
            c.drawPath(p, P(d["cap"]))
            c.drawOval(skia.Rect(x - r * 0.3, y - r * 0.5, x + r * 1.45, y - r * 0.18), P("#c2401f"))
            c.drawCircle(x, y - r * 1.08, r * 0.1, P("#c2401f"))
    # cheeks
    if expr not in ("angry",):
        for sgn in (-1, 1):
            c.drawCircle(x + sgn * r * 0.55, y + r * 0.38, r * 0.16, P("#ff6f6f", a=0.25 if expr != "dry" else 0.1))
    # eyes
    ex, ey = r * 0.36, y + r * 0.05
    blink = (t * 0.27 + hash(who) % 7 * 0.13) % 1.0 < 0.035
    ink = "#1d1414"
    for sgn in (-1, 1):
        cx = x + sgn * ex + lx * r * 0.12
        cy = ey + ly * r * 0.12
        if expr in ("sleep",) or (blink and expr not in ("shock", "roll")):
            p = skia.Path()
            p.moveTo(cx - r * 0.14, cy)
            p.quadTo(cx, cy + r * 0.1, cx + r * 0.14, cy)
            c.drawPath(p, P(ink, r * 0.06))
        elif expr in ("laugh", "happy_closed"):
            p = skia.Path()
            p.moveTo(cx - r * 0.14, cy + r * 0.03)
            p.quadTo(cx, cy - r * 0.14, cx + r * 0.14, cy + r * 0.03)
            c.drawPath(p, P(ink, r * 0.07))
        elif expr == "squint":
            line(c, cx - r * 0.14, cy, cx + r * 0.14, cy, ink, r * 0.07)
        else:
            er = r * (0.15 if expr == "shock" else 0.115)
            c.drawCircle(cx, cy, er, P(ink))
            hl_y = -er * 0.35
            if expr == "roll":
                c.drawCircle(cx, cy, er * 1.3, P("#ffffff"))
                c.drawCircle(cx, cy - er * 0.7, er * 0.6, P(ink))
            else:
                c.drawCircle(cx + er * 0.35, cy + hl_y, er * 0.35, P("#ffffff"))
            if expr in ("tired", "dry"):
                # heavy eyelid
                c.drawRect(skia.Rect(cx - er * 1.4, cy - er * 1.6, cx + er * 1.4, cy - er * 0.15), P(skin))
                line(c, cx - er * 1.2, cy - er * 0.15, cx + er * 1.2, cy - er * 0.15, ink, r * 0.045)
    # brows
    bw = r * 0.05
    for sgn in (-1, 1):
        bx = x + sgn * ex
        by = ey - r * 0.3
        if expr == "angry":
            line(c, bx - sgn * r * 0.16, by - r * 0.06, bx + sgn * r * 0.14, by + r * 0.08, ink, bw * 1.3)
        elif expr in ("sad", "tired", "dry", "worried"):
            line(c, bx - sgn * r * 0.15, by + r * 0.06, bx + sgn * r * 0.14, by - r * 0.04, ink, bw)
        elif expr in ("shock",):
            line(c, bx - r * 0.13, by - r * 0.1, bx + r * 0.13, by - r * 0.1, ink, bw)
        else:
            line(c, bx - r * 0.13, by - r * 0.02, bx + r * 0.13, by - r * 0.02, ink, bw)
    # mouth
    my = y + r * 0.5
    mouth = "#7a2630"
    if talk > 0:
        o = 0.25 + 0.75 * abs(math.sin(t * 15))
        c.drawOval(skia.Rect(x - r * 0.17, my - r * 0.08 * o, x + r * 0.17, my + r * 0.16 * o), P(mouth))
    elif expr in ("laugh",):
        p = skia.Path()
        p.moveTo(x - r * 0.3, my - r * 0.05)
        p.quadTo(x, my - r * 0.02, x + r * 0.3, my - r * 0.05)
        p.quadTo(x, my + r * 0.5, x - r * 0.3, my - r * 0.05)
        c.drawPath(p, P(mouth))
        c.drawCircle(x, my + r * 0.18, r * 0.09, P("#ff7c87"))
    elif expr in ("happy", "happy_closed"):
        p = skia.Path()
        p.moveTo(x - r * 0.24, my - r * 0.04)
        p.quadTo(x, my + r * 0.22, x + r * 0.24, my - r * 0.04)
        c.drawPath(p, P(ink, r * 0.06))
    elif expr in ("sad", "worried", "angry"):
        p = skia.Path()
        p.moveTo(x - r * 0.2, my + r * 0.08)
        p.quadTo(x, my - r * 0.12, x + r * 0.2, my + r * 0.08)
        c.drawPath(p, P(ink, r * 0.06))
        if expr == "angry":
            c.drawOval(skia.Rect(x - r * 0.2, my - r * 0.07, x + r * 0.2, my + r * 0.12), P(mouth))
    elif expr in ("dry", "tired"):
        p = skia.Path()
        p.moveTo(x - r * 0.22, my)
        for i in range(1, 7):
            p.lineTo(x - r * 0.22 + i * r * 0.0733, my + (r * 0.035 if i % 2 else -r * 0.035))
        c.drawPath(p, P("#8a4a40", r * 0.055))
        if expr == "dry":
            for dx in (-0.12, 0.02, 0.14):
                line(c, x + dx * r, my - r * 0.06, x + dx * r + r * 0.02, my + r * 0.06, "#e8c3a6", r * 0.025)
    elif expr == "shock":
        c.drawOval(skia.Rect(x - r * 0.12, my - r * 0.1, x + r * 0.12, my + r * 0.18), P(mouth))
    elif expr == "sleep":
        c.drawCircle(x, my + r * 0.02, r * 0.07, P(mouth))
    else:
        line(c, x - r * 0.14, my + r * 0.02, x + r * 0.14, my + r * 0.02, ink, r * 0.055)
    if who == "gran":
        for sgn in (-1, 1):
            c.drawCircle(x + sgn * ex, ey, r * 0.24, P("#6b5a4a", r * 0.05))
        line(c, x - ex + r * 0.24, ey, x + ex - r * 0.24, ey, "#6b5a4a", r * 0.05)
    if sweat > 0:
        for i in range(2):
            ph = (t * 0.8 + i * 0.5) % 1.0
            sx = x + (r * 0.95 if i == 0 else -r * 0.9)
            sy = y - r * 0.4 + ph * r * 0.9
            drop(c, sx, sy, r * 0.11, "#8fd8ff", a=sweat * (1 - ph * 0.6))


def draw_char(c, x, y, who="you", pose="stand", expr="neutral", t=0.0, s=1.0, look=(0, 0), talk=0.0,
              sweat=0.0, tilt=0.0, htilt=0.0, hold=None, hold_r=None, bob=0.0, flip=False):
    """Character with hip center at (x, y). `hold` is a callable(c, hx, hy) drawn at the right hand."""
    d = CHARS[who]
    p = POSES[pose] if isinstance(pose, str) else pose
    with xf(c, x, y + bob, s, rot=tilt, sx=(-s if flip else None), sy=(s if flip else None)):
        wdt = d["width"]
        tor = d["torso"]
        a1, a2 = d["arm"]
        l1, l2 = d["leg"]
        lw = wdt * 0.58
        # legs
        for side, key in ((-1, "ll"), (1, "rl")):
            aa, bb = p[key]
            _limb(c, side * wdt * 0.45, -4, aa, bb, l1, l2, lw, d["pants"], d["pants"], "shoe", d["shoe"], lw * 0.62)
        # torso
        if who == "noor":
            c.drawPath(poly([(-wdt * 0.9, -tor * 0.98), (wdt * 0.9, -tor * 0.98), (wdt * 1.35, 6), (-wdt * 1.35, 6)]),
                       P(d["shirt"]))
            rrect(c, -wdt * 0.9, -tor - 6, wdt * 1.8, tor * 0.5, wdt * 0.5, d["shirt"])
        else:
            rrect(c, -wdt, -tor - 8, wdt * 2, tor + 16, wdt * 0.75, d["shirt"])
            if who == "ines":
                c.drawRect(skia.Rect(-wdt, -14, wdt, 0), P("#3c2a1a"))
                c.drawPath(poly([(wdt * 0.25, -tor * 0.75), (wdt * 0.6, -tor * 0.75), (wdt * 0.6, -tor * 0.5),
                                 (wdt * 0.42, -tor * 0.42), (wdt * 0.25, -tor * 0.5)]), P("#e8c547"))
            else:
                rrect(c, -wdt * 0.55, -tor * 0.62, wdt * 1.1, tor * 0.08, 4, "#ffffff", 0.25)
        # neck + head
        hx, hy = 0, -tor - d["head"] * 0.95
        c.drawRect(skia.Rect(-wdt * 0.25, -tor - 26, wdt * 0.25, -tor), P(d["skin"]))
        with xf(c, hx, hy, rot=htilt):
            draw_head(c, 0, 0, who, expr, t, look, talk, sweat)
        # arms (in front)
        hands = []
        for side, key in ((-1, "la"), (1, "ra")):
            aa, bb = p[key]
            hands.append(_limb(c, side * wdt * 0.82, -tor + 10, aa, bb, a1, a2, lw * 0.85, d["shirt"], d["skin"],
                               "hand", d["skin"], lw * 0.5))
        if hold:
            hold(c, *hands[1])
        return hands


# ---------------------------------------------------------------- props
def draw_bottle(c, x, y, s=1.0, fill=0.8, rot=0.0, a=1.0):
    """Bottle centered at (x, y), 160 px tall at s=1."""
    with xf(c, x, y, s, rot, alpha=a):
        body = skia.RRect.MakeRectXY(skia.Rect(-32, -55, 32, 80), 18, 18)
        c.drawRRect(body, P("#dff4ff", a=0.85))
        if fill > 0:
            c.save()
            c.clipRRect(body, skia.ClipOp.kIntersect, True)
            top = lerp(80, -55, fill)
            c.drawRect(skia.Rect(-40, top, 40, 90), P("#3fb4f0"))
            c.drawRect(skia.Rect(-40, top, 40, top + 6), P("#a8e3ff"))
            c.restore()
        c.drawPath(poly([(-32, -45), (-14, -72), (14, -72), (32, -45)]), P("#dff4ff", a=0.85))
        rrect(c, -15, -92, 30, 22, 6, "#2a7de1")
        rrect(c, -32, -5, 64, 34, 4, "#ffffff", 0.9)
        drop(c, 0, 15, 8, "#2a7de1", shine=False)
        c.drawRRect(body, P("#9cc9e0", 3))
        line(c, -20, -40, -20, 60, "#ffffff", 5, 0.6)


def draw_mirror(c, x, y, s=1.0, rot=0.0, glint=0.0, t=0.0):
    with xf(c, x, y, s, rot):
        rrect(c, -10, 30, 20, 60, 10, "#ff5c9a")
        c.drawCircle(0, 0, 46, P("#ff5c9a"))
        c.drawCircle(0, 0, 46, P("#d63a77", 4))
        c.save()
        c.clipPath(skia.Path().addCircle(0, 0, 36), skia.ClipOp.kIntersect, True)
        fill_shader(c, skia.Rect(-36, -36, 36, 36), linear(-36, -36, 36, 36, ["#e9fbff", "#9fd6ef", "#e0f6ff"]))
        c.drawPath(poly([(-40, 10), (10, -40), (24, -40), (-26, 10)]), P("#ffffff", a=0.7))
        c.restore()
        for i in range(6):
            ang = i / 6 * math.tau
            c.drawCircle(math.cos(ang) * 46, math.sin(ang) * 46, 4, P("#ffd1e3"))
    if glint > 0:
        glow(c, x, y, 120 * s * (0.6 + glint), "#ffffff", 0.8 * glint)
        sparkle(c, x, y, 80 * s * glint, "#ffffff", glint, rot=t * 90)


def draw_phone(c, x, y, s=1.0, t=0.0, bars=0):
    with xf(c, x, y, s):
        rrect(c, -95, -180, 190, 360, 30, "#1c1c24")
        rrect(c, -82, -160, 164, 320, 18, "#2b3a55")
        rrect(c, -30, -172, 60, 8, 4, "#3a3a46")
        # signal bars
        for i in range(4):
            h = 18 + i * 14
            rrect(c, -50 + i * 26, 0 - h, 18, h, 4, "#ffffff", 0.25)
        cross_mark(c, 50, -30, 40, "#ff4d4d")
        text(c, "NO SIGNAL", 0, 60, 26, "#ffffff", "ExtraBold")
        text(c, "SOS unavailable", 0, 100, 18, "#ffffff", "Medium", a=0.6)


def draw_cracker(c, x, y, s=1.0, rot=0.0, face=False, t=0.0):
    with xf(c, x, y, s, rot):
        rrect(c, -60, -60, 120, 120, 16, "#e6b15c")
        rrect(c, -60, -60, 120, 120, 16, "#c48a36", 5)
        for i in range(3):
            for j in range(3):
                c.drawCircle(-34 + i * 34, -34 + j * 34, 5, P("#b07a2c"))
        if face:
            c.drawCircle(-20, -8, 7, P("#3a2414"))
            c.drawCircle(20, -8, 7, P("#3a2414"))
            pp = skia.Path()
            pp.moveTo(-20, 22)
            pp.quadTo(0, 36, 20, 22)
            c.drawPath(pp, P("#3a2414", 5))


def draw_hand_big(c, x, y, s=1.0, skin="#b97a50", rot=0.0):
    """A big forearm coming from below, palm up; returns nothing."""
    with xf(c, x, y, s, rot):
        rrect(c, -55, 0, 110, 400, 50, "#1f9e9a")
        rrect(c, -48, -40, 96, 120, 44, skin)
        for i, (fx, fl) in enumerate(((-36, 60), (-12, 75), (12, 72), (36, 58))):
            rrect(c, fx - 11, -40 - fl, 22, fl + 20, 11, skin)
        rrect(c, 40, -30, 60, 24, 12, skin)


def draw_kidney(c, x, y, s=1.0, flip=False, squeeze=0.0, t=0.0):
    with xf(c, x, y, sx=(-s if flip else s) * (1 - 0.12 * squeeze), sy=s * (1 + 0.06 * squeeze)):
        p = skia.Path()
        p.moveTo(30, -150)
        p.cubicTo(130, -170, 150, -30, 120, 40)
        p.cubicTo(95, 120, 20, 175, -20, 150)
        p.cubicTo(-55, 128, -30, 70, -10, 40)
        p.cubicTo(10, 10, 10, -10, -10, -40)
        p.cubicTo(-35, -80, -25, -140, 30, -150)
        p.close()
        c.drawPath(p, P("#d9534f"))
        c.drawPath(p, P("#a83a37", 6))
        with xf(c, 6, 4, 0.8):
            c.drawPath(p, P("#e8736f", a=0.6))
        # ureter
        pp = skia.Path()
        pp.moveTo(0, 20)
        pp.quadTo(-50, 60, -40, 260)
        c.drawPath(pp, P("#f0c27b", 12))


def draw_brain(c, x, y, s=1.0, fog=0.0, t=0.0):
    with xf(c, x, y, s):
        pts = [(-110, -20, 70), (-60, -70, 75), (10, -85, 78), (80, -55, 72), (115, 5, 62), (60, 40, 68),
               (-20, 40, 70), (-90, 35, 58)]
        for (px, py, r) in pts:
            c.drawCircle(px, py, r, P("#f4a3b8"))
        for (px, py, r) in pts:
            p = skia.Path()
            p.addArc(skia.Rect(px - r * 0.6, py - r * 0.6, px + r * 0.6, py + r * 0.6), 200, 140)
            c.drawPath(p, P("#d9708f", 7))
        rrect(c, 20, 80, 40, 80, 20, "#e98aa6")
        if fog > 0:
            for i in range(9):
                fx = -130 + i * 32 + 20 * math.sin(t * 1.3 + i)
                fy = -20 + 30 * math.sin(i * 1.7 + t)
                c.drawCircle(fx, fy, 60, P("#d8dde6", a=0.45 * fog))


def body_path(s=1.0):
    p = skia.Path()
    p.addCircle(0, -300 * s, 58 * s)
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect(-80 * s, -235 * s, 80 * s, 40 * s), 50 * s, 50 * s))
    for sgn in (-1, 1):
        p.addRRect(skia.RRect.MakeRectXY(skia.Rect(sgn * 82 * s - 24 * s, -225 * s, sgn * 82 * s + 24 * s, 20 * s),
                                         24 * s, 24 * s))
        p.addRRect(skia.RRect.MakeRectXY(skia.Rect(sgn * 38 * s - 30 * s, 0, sgn * 38 * s + 30 * s, 260 * s),
                                         30 * s, 30 * s))
    return p


def water_body(c, x, y, s, level, t, leak=0.0, outline="#ffffff"):
    """Body silhouette filled to `level` (0..1) with animated waves. Origin = hips."""
    with xf(c, x, y):
        bp = body_path(s)
        c.drawPath(bp, P("#ffffff", a=0.12))
        c.save()
        c.clipPath(bp, skia.ClipOp.kIntersect, True)
        top = lerp(260 * s, -360 * s, level)
        for k, (col, amp, sp) in enumerate((("#1d7fd1", 10, 2.0), ("#3fb4f0", 14, 2.8))):
            wp = skia.Path()
            wp.moveTo(-200 * s, 300 * s)
            for xx in range(-200, 201, 10):
                X = xx * s
                wp.lineTo(X, top + k * 10 + amp * math.sin(xx * 0.04 + t * sp + k))
            wp.lineTo(200 * s, 300 * s)
            wp.close()
            c.drawPath(wp, P(col, a=0.95))
        c.restore()
        c.drawPath(bp, P(outline, 5, 0.9))
        if leak > 0:
            for i in range(10):
                ph = (t * 0.7 + i * 0.137) % 1.0
                ang = i * 2.4
                rx = math.cos(ang) * (110 + ph * 260) * s
                ry = -120 * s + math.sin(ang) * (130 + ph * 200) * s
                drop(c, rx, ry, 12 * s, "#4cc3ff", a=leak * (1 - ph))


def thermometer(c, x, y, s, level, t):
    with xf(c, x, y, s):
        rrect(c, -28, -260, 56, 300, 28, "#ffffff")
        c.drawCircle(0, 60, 52, P("#ffffff"))
        c.drawCircle(0, 60, 40, P("#ff3b3b"))
        h = lerp(10, 250, level)
        rrect(c, -14, 40 - h, 28, h + 10, 14, "#ff3b3b")
        for i in range(6):
            line(c, 14, -220 + i * 44, 26, -220 + i * 44, "#999999", 4)


def draw_vehicle(c, x, y, s=1.0, wheel_rot=0.0, bounce=0.0, hood=0.0, kind="car", t=0.0,
                 riders=None, smoke=0.0, flip=False):
    """Side-view vehicle facing right, origin at ground level under the middle."""
    body = "#e4572e" if kind == "car" else "#f2f2ee"
    trim = "#b8401f" if kind == "car" else "#5b7d3a"
    with xf(c, x, y, sx=(-s if flip else s), sy=s):
        c.drawOval(skia.Rect(-300, -16, 300, 16), P("#000000", a=0.2))
        with xf(c, 0, -bounce):
            if kind == "car":
                cab = skia.Path()
                cab.moveTo(-200, -150)
                cab.lineTo(-150, -255)
                cab.quadTo(-140, -265, -120, -265)
                cab.lineTo(90, -265)
                cab.quadTo(110, -265, 125, -250)
                cab.lineTo(200, -150)
                cab.close()
                c.drawPath(cab, P(body))
                rrect(c, -275, -165, 550, 125, 46, body)
                win1 = poly([(-172, -158), (-132, -240), (-25, -240), (-25, -158)])
                win2 = poly([(-5, -158), (-5, -240), (92, -240), (160, -158)])
                wins = [win1, win2]
            else:
                rrect(c, -40, -275, 200, 140, 26, body)
                rrect(c, -300, -175, 600, 135, 30, body)
                rrect(c, -300, -195, 250, 30, 10, "#dcdcd4")
                rrect(c, 80, -300, 70, 22, 8, "#ff3b3b" if int(t * 4) % 2 else "#3b7bff")
                win2 = poly([(-20, -170), (-20, -255), (100, -255), (145, -170)])
                wins = [win2]
                c.drawRect(skia.Rect(-300, -125, 300, -98), P(trim))
                with xf(c, -150, -55, sx=(-1 if flip else 1), sy=1):
                    text(c, "RANGER", 0, 0, 34, "#5b7d3a")
            for wp in wins:
                c.drawPath(wp, P("#bfe6f2"))
            if riders:
                for i, (who, expr) in enumerate(riders):
                    if who is None or i >= len(wins):
                        continue
                    c.save()
                    c.clipPath(wins[i], skia.ClipOp.kIntersect, True)
                    b = wins[i].getBounds()
                    cx = (b.left() + b.right()) / 2 + 5
                    draw_head(c, cx, -195 + 3 * math.sin(t * 7 + i), who, expr, t, look=(1, 0),
                              r=CHARS[who]["head"] * 0.85)
                    rrect(c, cx - 40, -150, 80, 60, 20, CHARS[who]["shirt"])
                    c.restore()
            for wp in wins:
                c.drawPath(wp, P("#ffffff", 4, 0.6))
            line(c, -15, -155, -15, -60, trim, 4) if kind == "car" else None
            if kind == "car":
                c.drawRect(skia.Rect(-275, -118, 275, -102), P("#ffffff", a=0.75))
                rrect(c, 10, -138, 34, 9, 4, trim)
                rrect(c, -150, -138, 34, 9, 4, trim)
            rrect(c, 248, -135, 24, 26, 8, "#ffe27a")
            rrect(c, -282, -135, 18, 26, 6, "#ff4040")
            rrect(c, -290, -62, 580, 22, 11, "#3a3a44")
            if hood > 0 and kind == "car":
                with xf(c, 140, -158, rot=-55 * hood):
                    rrect(c, 0, -10, 135, 18, 8, body)
                    rrect(c, 0, -10, 135, 18, 8, trim, stroke=3)
        for wx in (-170, 170):
            c.drawCircle(wx, -42, 70, P("#2d2228"))
            c.drawCircle(wx, -42, 54, P("#25252b"))
            c.drawCircle(wx, -42, 30, P("#c9ccd1"))
            for k in range(5):
                ang = math.radians(wheel_rot + k * 72)
                line(c, wx, -42, wx + math.cos(ang) * 26, -42 + math.sin(ang) * 26, "#8a8f98", 6)
            c.drawCircle(wx, -42, 9, P("#555555"))
    if smoke > 0:
        for i in range(8):
            ph = (t * 0.6 + i / 8) % 1.0
            sx = x + (210 + 40 * math.sin(i * 3.1) + ph * 80) * s * (-1 if flip else 1)
            sy = y - (170 + ph * 260) * s
            c.drawCircle(sx, sy, (30 + ph * 60) * s, P("#8d8d95", a=smoke * 0.55 * (1 - ph)))


def lightbulb(c, x, y, s, color="#ffd34d", on=1.0, t=0.0):
    with xf(c, x, y, s):
        if on > 0:
            glow(c, 0, -10, 170, color, 0.6 * on)
        c.drawCircle(0, -20, 62, P(mixhex("#e8e8e8", color, on)))
        rrect(c, -30, 30, 60, 46, 10, "#9aa0a6")
        for i in range(3):
            line(c, -30, 40 + i * 12, 30, 40 + i * 12, "#6f747a", 4)
        pp = skia.Path()
        pp.moveTo(-18, 22)
        pp.lineTo(-10, -20)
        pp.lineTo(0, 0)
        pp.lineTo(10, -20)
        pp.lineTo(18, 22)
        c.drawPath(pp, P("#8a6d1d", 4))


def thumbs_up(c, x, y, s, color="#ffffff"):
    with xf(c, x, y, s):
        rrect(c, -60, -10, 36, 80, 8, color)
        rrect(c, -18, -10, 80, 80, 18, color)
        p = skia.Path()
        p.moveTo(-14, -6)
        p.lineTo(6, -70)
        p.quadTo(30, -80, 28, -50)
        p.lineTo(20, -10)
        p.close()
        c.drawPath(p, P(color))


def bell(c, x, y, s, color="#ffffff"):
    with xf(c, x, y, s):
        p = skia.Path()
        p.moveTo(-50, 40)
        p.quadTo(-40, 25, -40, -10)
        p.quadTo(-40, -60, 0, -62)
        p.quadTo(40, -60, 40, -10)
        p.quadTo(40, 25, 50, 40)
        p.close()
        c.drawPath(p, P(color))
        c.drawCircle(0, 52, 14, P(color))
        c.drawCircle(0, -66, 9, P(color))
