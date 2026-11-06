"""Clean explainer style kit: typography, easing, icons and diagrams (skia).

Design rules (kept on purpose, "no distractions"):
- one dark, plain background with a soft vignette
- white text, ONE accent colour (danger red) + one warm secondary (amber)
- every element enters with a short ease-out, nothing loops for attention
"""
import math
import random
from contextlib import contextmanager

import skia

W, H = 1920, 1080
FONT_DIR = "/usr/share/fonts/opentype/inter/"

BG = "#0F1217"
INK = "#F3F0EA"
MUTED = "#8A93A3"
DIM = "#2A3039"
ACC = "#FF4B33"   # danger / key words
AMB = "#FFB43A"   # heat / money / secondary
COOL = "#58B7FF"  # safe / calm (used sparingly)

_tf, _fc = {}, {}


def font(size, weight="Black"):
    key = (weight, round(size, 1))
    if key not in _fc:
        if weight not in _tf:
            _tf[weight] = skia.Typeface.MakeFromFile(FONT_DIR + f"Inter-{weight}.otf")
        f = skia.Font(_tf[weight], size)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        f.setSubpixel(True)
        _fc[key] = f
    return _fc[key]


# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_io(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def back_out(t, s=1.5):
    t = clamp(t)
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


def prog(t, start, dur=0.45):
    return clamp((t - start) / dur)


def hexrgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def C(h, a=1.0):
    r, g, b = hexrgb(h)
    return skia.ColorSetARGB(int(clamp(a) * 255), r, g, b)


def mix(h1, h2, t):
    a, b = hexrgb(h1), hexrgb(h2)
    t = clamp(t)
    return "#%02x%02x%02x" % tuple(int(lerp(x, y, t)) for x, y in zip(a, b))


def P(color, stroke=None, a=1.0):
    p = skia.Paint(AntiAlias=True, Color=C(color, a) if isinstance(color, str) else color)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


@contextmanager
def xf(c, x=0, y=0, s=1.0, rot=0.0, alpha=1.0):
    c.save()
    c.translate(x, y)
    if rot:
        c.rotate(rot)
    if s != 1:
        c.scale(s, s)
    lay = alpha < 0.999
    if lay:
        c.saveLayerAlpha(None, int(clamp(alpha) * 255))
    try:
        yield
    finally:
        if lay:
            c.restore()
        c.restore()


def rr(c, x, y, w, h, r, color, a=1.0, stroke=None):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), P(color, stroke, a))


def circ(c, x, y, r, color, a=1.0, stroke=None):
    c.drawCircle(x, y, r, P(color, stroke, a))


def line(c, x0, y0, x1, y1, color, w=6, a=1.0):
    c.drawLine(x0, y0, x1, y1, P(color, w, a))


def path(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


# ---------------------------------------------------------------- background
_bg_cache = {}


def background(c):
    if "img" not in _bg_cache:
        s = skia.Surface(W, H)
        k = s.getCanvas()
        k.clear(C(BG))
        sh = skia.GradientShader.MakeRadial((W / 2, H * 0.45), W * 0.75,
                                           [C("#1A1F27"), C(BG), C("#090B0E")], [0, 0.6, 1])
        k.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh))
        _bg_cache["img"] = s.makeImageSnapshot()
    c.drawImage(_bg_cache["img"], 0, 0)


# -------------------------------------------------------------------- text
def text_w(s, size, weight="Black"):
    return font(size, weight).measureText(s)


def draw_text(c, s, x, y, size, color=INK, weight="Black", a=1.0, align="left"):
    f = font(size, weight)
    w = f.measureText(s)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    c.drawString(s, x, y, f, P(color, a=a))
    return w


def parse_rich(s):
    """'Airlines *banned it* by name' -> [(word, accent_color_or_None)].
    *x* = red accent, ^x^ = amber accent."""
    out, mode = [], None
    for tok in s.split(" "):
        if not tok:
            continue
        col = mode
        if tok.startswith("*"):
            mode = ACC
            col = ACC
            tok = tok[1:]
        elif tok.startswith("^"):
            mode = AMB
            col = AMB
            tok = tok[1:]
        end = False
        if tok.endswith("*") or tok.endswith("^") or tok[:-1].endswith("*") or tok[:-1].endswith("^"):
            # allow trailing punctuation after marker: word*, -> word,
            if tok[-1] in "*^":
                tok = tok[:-1]
            else:
                tok = tok[:-2] + tok[-1]
            end = True
        out.append((tok, col))
        if end:
            mode = None
    return out


def rich_line(c, s, cx, y, size, t, t0, color=INK, weight="Black", align="center", stagger=0.045,
              max_w=1640, highlight=None):
    """Word-by-word slide-up reveal of one line. Returns used width."""
    words = parse_rich(s)
    f = font(size, weight)
    space = f.measureText(" ")
    widths = [f.measureText(w) for w, _ in words]
    total = sum(widths) + space * (len(words) - 1)
    if total > max_w:  # shrink to fit
        k = max_w / total
        return rich_line(c, s, cx, y, size * k, t, t0, color, weight, align, stagger, max_w * 10, highlight)
    x = cx - total / 2 if align == "center" else cx
    for i, ((w, col), ww) in enumerate(zip(words, widths)):
        p = ease_out(prog(t, t0 + i * stagger, 0.42))
        if p > 0:
            dy = (1 - p) * size * 0.45
            c.drawString(w, x, y + dy, f, P(col or color, a=p))
        x += ww + space
    return total


# --------------------------------------------------------------------- icons
# Each icon is drawn centred at (0,0) for a nominal size of ~300 px.

def ic_phone(c, t=0, a=1.0, col=INK):
    rr(c, -85, -150, 170, 300, 30, "#1C2129", a)
    rr(c, -85, -150, 170, 300, 30, col, a, stroke=9)
    rr(c, -66, -122, 132, 236, 12, "#2B3340", a)
    # curved edge glint + stylus
    line(c, 70, -110, 70, 105, MUTED, 4, a * 0.6)
    rr(c, 30, 118, 40, 8, 4, MUTED, a)
    circ(c, 0, -136, 5, MUTED, a)


def ic_flame(c, t=0, a=1.0, s=1.0):
    def fl(scale, col, ph):
        k = 1 + 0.06 * math.sin(t * 9 + ph)
        p = skia.Path()
        p.moveTo(0, 60 * scale)
        p.cubicTo(-70 * scale, 50 * scale, -70 * scale, -10 * scale, -30 * scale, -60 * scale * k)
        p.cubicTo(-28 * scale, -30 * scale, -10 * scale, -20 * scale, -5 * scale, -20 * scale)
        p.cubicTo(-10 * scale, -60 * scale, 10 * scale, -100 * scale * k, 25 * scale, -120 * scale * k)
        p.cubicTo(30 * scale, -70 * scale, 75 * scale, -40 * scale, 65 * scale, 10 * scale)
        p.cubicTo(60 * scale, 45 * scale, 30 * scale, 60 * scale, 0, 60 * scale)
        c.drawPath(p, P(col, a=a))
    with xf(c, s=s):
        fl(1.0, ACC, 0)
        fl(0.62, AMB, 1.3)
        with xf(c, 0, 18):
            fl(0.3, "#FFE7A8", 2.1)


def ic_battery(c, t=0, a=1.0, level=0.7, col=INK, fill=None):
    rr(c, -80, -140, 160, 280, 22, col, a, stroke=10)
    rr(c, -32, -165, 64, 25, 8, col, a)
    h = 236 * level
    rr(c, -58, 118 - h, 116, h, 10, fill or col, a * 0.9)
    # bolt
    p = path([(10, -70), (-30, 10), (0, 10), (-10, 70), (30, -10), (0, -10)])
    c.drawPath(p, P(BG, a=a))


def ic_hoverboard(c, t=0, a=1.0, col=INK):
    for sx in (-1, 1):
        circ(c, sx * 155, 40, 62, "#1C2129", a)
        circ(c, sx * 155, 40, 62, col, a, stroke=10)
        circ(c, sx * 155, 40, 18, col, a)
    p = skia.Path()
    p.moveTo(-150, -30)
    p.cubicTo(-90, -70, -40, -40, 0, -10)
    p.cubicTo(40, -40, 90, -70, 150, -30)
    p.lineTo(150, 10)
    p.cubicTo(80, -10, 40, 20, 0, 30)
    p.cubicTo(-40, 20, -80, -10, -150, 10)
    p.close()
    c.drawPath(p, P("#2B3340", a=a))
    c.drawPath(p, P(col, 9, a))
    rr(c, -120, -42, 70, 14, 7, MUTED, a)
    rr(c, 50, -42, 70, 14, 7, MUTED, a)


def ic_laptop(c, t=0, a=1.0, col=INK):
    rr(c, -150, -120, 300, 190, 16, "#1C2129", a)
    rr(c, -150, -120, 300, 190, 16, col, a, stroke=9)
    rr(c, -128, -98, 256, 146, 6, "#2B3340", a)
    p = path([(-185, 80), (185, 80), (205, 110), (-205, 110)])
    c.drawPath(p, P(col, a=a))
    rr(c, -40, 82, 80, 10, 5, BG, a)


def ic_watch(c, t=0, a=1.0, col=INK, screen=None):
    rr(c, -55, -175, 110, 90, 20, MUTED, a)
    rr(c, -55, 85, 110, 90, 20, MUTED, a)
    rr(c, -95, -105, 190, 210, 42, "#1C2129", a)
    rr(c, -95, -105, 190, 210, 42, col, a, stroke=10)
    rr(c, -72, -82, 144, 164, 26, screen or "#2B3340", a)
    # heart-rate trace
    pts = [(-55, 5), (-25, 5), (-12, -30), (2, 35), (16, -12), (26, 5), (55, 5)]
    c.drawPath(path(pts, False), P(ACC if screen is None else BG, 7, a))


def ic_washer(c, t=0, a=1.0, col=INK, lid=0.0, spin=0.0):
    rr(c, -130, -130, 260, 290, 22, "#1C2129", a)
    rr(c, -130, -130, 260, 290, 22, col, a, stroke=10)
    circ(c, 0, 30, 82, col, a, stroke=10)
    with xf(c, 0, 30, rot=spin):
        for k in range(3):
            ang = k * 2.094
            line(c, 0, 0, 55 * math.cos(ang), 55 * math.sin(ang), MUTED, 8, a)
    circ(c, 75, -100, 10, ACC, a)
    circ(c, 40, -100, 10, MUTED, a)
    # lid (top) – can fly off
    with xf(c, 0 + lid * 160, -150 - lid * 380, rot=-lid * 70):
        rr(c, -140, -20, 280, 26, 10, col, a)


def ic_treadmill(c, t=0, a=1.0, col=INK, gap=False):
    # belt deck (raised) + upright + screen
    p = path([(-220, 60), (170, 30), (190, 55), (-200, 95)])
    c.drawPath(p, P("#2B3340", a=a))
    c.drawPath(p, P(col, 9, a))
    line(c, 130, 35, 170, -170, col, 12, a)
    rr(c, 120, -250, 130, 85, 12, "#2B3340", a)
    rr(c, 120, -250, 130, 85, 12, col, a, stroke=8)
    line(c, 70, -110, 175, -125, col, 10, a)
    # legs / gap under back
    line(c, -200, 95, -205, 140, col, 10, a)
    line(c, 180, 55, 185, 140, col, 10, a)
    line(c, -240, 140, 230, 140, MUTED, 5, a)
    if gap:
        rr(c, -195, 102, 120, 32, 6, ACC, a * 0.35)
        rr(c, -195, 102, 120, 32, 6, ACC, a, stroke=4)


def ic_magnets(c, t=0, a=1.0, n=19):
    rnd = random.Random(4)
    pts = []
    for row in range(4):
        for k in range(5 - (row % 2)):
            pts.append((-120 + k * 60 + (row % 2) * 30, 60 - row * 52))
    for (x, y) in pts[:n]:
        sh = skia.GradientShader.MakeRadial((x - 9, y - 10), 34, [C("#FFFFFF", a), C("#B9C0CB", a), C("#5B6370", a)],
                                            [0, 0.45, 1])
        c.drawCircle(x, y, 27, skia.Paint(AntiAlias=True, Shader=sh))


def ic_segway(c, t=0, a=1.0, col=INK):
    circ(c, 0, 110, 70, "#1C2129", a)
    circ(c, 0, 110, 70, col, a, stroke=10)
    circ(c, 0, 110, 20, col, a)
    rr(c, -70, 60, 140, 26, 10, "#2B3340", a)
    rr(c, -70, 60, 140, 26, 10, col, a, stroke=7)
    line(c, 10, 62, 50, -160, col, 13, a)
    line(c, -20, -168, 110, -150, col, 13, a)


def ic_powerbank(c, t=0, a=1.0, col=INK):
    rr(c, -95, -160, 190, 320, 30, "#1C2129", a)
    rr(c, -95, -160, 190, 320, 30, col, a, stroke=10)
    for k in range(4):
        circ(c, -36 + k * 24, -110, 7, COOL if k < 3 else DIM, a)
    rr(c, -30, 135, 60, 14, 6, MUTED, a)
    p = path([(12, -50), (-28, 25), (0, 25), (-12, 90), (32, 10), (4, 10)])
    c.drawPath(p, P(col, a=a))


def ic_plane(c, t=0, a=1.0, col=INK):
    p = skia.Path()
    p.moveTo(-200, 0)
    p.cubicTo(-200, -22, -150, -26, -100, -26)
    p.lineTo(160, -26)
    p.cubicTo(200, -26, 215, -5, 215, 0)
    p.cubicTo(215, 5, 200, 26, 160, 26)
    p.lineTo(-100, 26)
    p.cubicTo(-150, 26, -200, 22, -200, 0)
    c.drawPath(p, P(col, a=a))
    c.drawPath(path([(-10, -20), (60, -20), (-40, -150), (-80, -150)]), P(col, a=a))
    c.drawPath(path([(-10, 20), (60, 20), (-40, 150), (-80, 150)]), P(col, a=a))
    c.drawPath(path([(140, -20), (185, -20), (200, -95), (175, -95)]), P(col, a=a))
    for k in range(6):
        circ(c, -150 + k * 45, -6, 6, BG, a)


def ic_car(c, t=0, a=1.0, col=INK):
    c.drawPath(path([(-210, 40), (-210, -20), (-150, -40), (-100, -110), (90, -110), (140, -40),
                     (210, -25), (210, 40)]), P(col, a=a))
    rr(c, -85, -95, 75, 50, 6, BG, a)
    rr(c, 5, -95, 75, 50, 6, BG, a)
    for sx in (-130, 130):
        circ(c, sx, 45, 45, BG, a)
        circ(c, sx, 45, 36, col, a, stroke=12)


def ic_warning(c, t=0, a=1.0, col=ACC):
    p = skia.Path()
    p.moveTo(0, -150)
    p.lineTo(165, 135)
    p.lineTo(-165, 135)
    p.close()
    pp = P(col, 22, a)
    c.drawPath(p, pp)
    rr(c, -11, -60, 22, 115, 11, col, a)
    circ(c, 0, 92, 14, col, a)


def ic_house(c, t=0, a=1.0, col=INK):
    c.drawPath(path([(-170, -10), (0, -160), (170, -10)], False), P(col, 16, a))
    rr(c, -125, -20, 250, 170, 8, col, a, stroke=14)
    rr(c, -30, 50, 60, 100, 6, col, a)


def ic_shield(c, t=0, a=1.0, col=COOL):
    p = skia.Path()
    p.moveTo(0, -160)
    p.cubicTo(60, -120, 110, -115, 140, -120)
    p.cubicTo(140, 20, 90, 110, 0, 160)
    p.cubicTo(-90, 110, -140, 20, -140, -120)
    p.cubicTo(-110, -115, -60, -120, 0, -160)
    c.drawPath(p, P(col, 14, a))
    c.drawPath(path([(-55, 0), (-12, 45), (65, -45)], False), P(col, 18, a))


def ic_gavel(c, t=0, a=1.0, col=AMB):
    with xf(c, 0, -20, rot=-35):
        rr(c, -95, -55, 190, 80, 14, col, a)
        rr(c, -18, 25, 36, 170, 14, col, a)
    rr(c, -170, 130, 230, 30, 10, MUTED, a)


def ic_tree(c, t=0, a=1.0, col="#3BB273"):
    for k, (w, y) in enumerate([(120, -80), (170, -10), (220, 70)]):
        c.drawPath(path([(0, y - 110), (w, y + 20), (-w, y + 20)]), P(col, a=a))
    rr(c, -22, 90, 44, 60, 6, "#8B5E3C", a)
    c.drawPath(path([(0, -215), (14, -185), (-14, -185)]), P(AMB, a=a))


def ic_factory(c, t=0, a=1.0, col=INK):
    c.drawPath(path([(-200, 140), (-200, -20), (-110, -80), (-110, -20), (-20, -80), (-20, -20), (70, -80),
                     (70, -20), (200, -20), (200, 140)]), P(col, a=a))
    rr(c, 120, -170, 40, 150, 4, col, a)
    for k in range(4):
        rr(c, -165 + k * 85, 30, 50, 40, 4, BG, a)
    for k in range(3):
        ph = (t * 0.6 + k / 3) % 1
        circ(c, 140 + ph * 30, -190 - ph * 110, 18 + ph * 22, MUTED, a * (1 - ph) * 0.7)


def ic_hospital(c, t=0, a=1.0, col=INK):
    rr(c, -150, -150, 300, 300, 40, col, a, stroke=14)
    rr(c, -28, -95, 56, 190, 8, ACC, a)
    rr(c, -95, -28, 190, 56, 8, ACC, a)


def ic_globe(c, t=0, a=1.0, col=INK):
    circ(c, 0, 0, 150, col, a, stroke=12)
    c.drawOval(skia.Rect.MakeLTRB(-70, -150, 70, 150), P(col, 9, a))
    line(c, 0, -150, 0, 150, col, 9, a)
    line(c, -150, 0, 150, 0, col, 9, a)
    c.drawPath(path([(-130, -70), (130, -70)], False), P(col, 7, a))
    c.drawPath(path([(-130, 70), (130, 70)], False), P(col, 7, a))


def ic_box(c, t=0, a=1.0, col=INK):
    rr(c, -150, -80, 300, 210, 12, col, a, stroke=13)
    line(c, -150, -20, 150, -20, col, 10, a)
    line(c, 0, -80, 0, 130, AMB, 14, a)
    rr(c, -100, -140, 200, 55, 10, AMB, a)


def ic_cash(c, t=0, a=1.0, col="#3BB273"):
    for k in range(3):
        with xf(c, -20 + k * 20, 30 - k * 30, rot=-6 + k * 4):
            rr(c, -170, -90, 340, 180, 16, "#163322", a)
            rr(c, -170, -90, 340, 180, 16, col, a, stroke=10)
            circ(c, 0, 0, 48, col, a, stroke=9)
            draw_text(c, "$", 0, 26, 72, col, a=a, align="center")


def ic_child(c, t=0, a=1.0, col=INK):
    circ(c, 0, -110, 50, col, a)
    rr(c, -55, -50, 110, 130, 40, col, a)
    line(c, -25, 80, -30, 150, col, 22, a)
    line(c, 25, 80, 30, 150, col, 22, a)


def ic_paw(c, t=0, a=1.0, col=INK):
    c.drawOval(skia.Rect.MakeLTRB(-70, -10, 70, 100), P(col, a=a))
    for (x, y, r) in [(-90, -50, 30), (-35, -100, 32), (35, -100, 32), (90, -50, 30)]:
        circ(c, x, y, r, col, a)


def ic_candy(c, t=0, a=1.0):
    ic_magnets(c, t, a, n=7)


ICONS = {k[3:]: v for k, v in globals().items() if k.startswith("ic_")}


def icon(c, name, x, y, size, t, t0, a=1.0, anim="pop", **kw):
    """Draw an icon at (x, y); size is the displayed height (nominal 300)."""
    p = prog(t, t0, 0.55)
    if p <= 0:
        return
    s = size / 300.0
    if anim == "pop":
        s *= lerp(0.6, 1.0, back_out(p))
    yy = y + (1 - ease_out(p)) * 30
    rot = 0
    if anim == "shake":
        rot = math.sin(t * 40) * 3 * clamp(1 - prog(t, t0 + 0.6, 1.2))
    with xf(c, x, yy, s=s, rot=rot, alpha=a * ease_out(p)):
        ICONS[name](c, t=t, a=1.0, **kw)


def burn(c, x, y, size, t, t0, a=1.0):
    """Flames rising behind/over an object (gentle, not flashy)."""
    p = ease_out(prog(t, t0, 0.6))
    if p <= 0:
        return
    for k, (dx, sc) in enumerate([(-0.25, 0.7), (0.0, 1.0), (0.26, 0.75)]):
        with xf(c, x + dx * size, y - size * 0.05, s=size / 300 * sc * p * 1.25, alpha=a * p):
            ic_flame(c, t + k * 0.7, 1.0)


def smoke(c, x, y, size, t, t0, a=1.0):
    p = prog(t, t0, 0.5)
    if p <= 0:
        return
    for k in range(6):
        ph = ((t - t0) * 0.45 + k / 6) % 1
        r = size * (0.08 + ph * 0.18)
        circ(c, x + math.sin(k * 2.3 + ph * 3) * size * 0.12, y - ph * size * 0.9, r, "#9AA3B0",
             a * p * (1 - ph) * 0.35)
