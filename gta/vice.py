"""Neon beach-city kit: pastel Art Deco hotels, Ocean Drive strip, cop car, helicopter, boat, explainer callouts.
All original, procedurally drawn."""
import math
import random

import skia

from gfx import W, H, C, P, xf, rrect, poly, line, linear, radial, fill_shader, clamp, lerp, smooth, ease_out, \
    back_out, at, mixhex
import sgfx
from ggfx import (glow, blurp, ftext, tw, neon_text, sky, retro_sun, clouds, ocean, palm, car, _cached_t, PINK, HOT,
                  ORANGE, GOLD, TEAL, CYAN, PURPLE, GREEN, RED, city_layers_t)

PASTELS = ["#f7c6d9", "#bfe9e3", "#fbe3b0", "#d9c9f5", "#ffd1b8", "#c9e4ff", "#f3f0e6"]
NEONS = [PINK, TEAL, CYAN, GOLD, PURPLE, "#ff7a3c"]
SIGNS = ["HOTEL", "MOTEL", "PALMS", "CLUB", "BAR", "SURF", "DINER", "TACOS"]


def deco_hotel(c, x, base, w, h, col, neon, sign, night=1.0, seed=0, t=0.0):
    rnd = random.Random(seed)
    dark = mixhex(col, "#1a0b2e", 0.55 * night)
    face = mixhex(col, "#2a1446", 0.42 * night)
    # main block
    c.drawRect(skia.Rect(x, base - h, x + w, base), P(face))
    # stepped deco crown
    cw = w * 0.42
    cx = x + w * 0.5
    for i in range(3):
        ww = cw * (1 - i * 0.28)
        hh = 26 + i * 4
        yy = base - h - (i + 1) * hh
        c.drawRect(skia.Rect(cx - ww / 2, yy, cx + ww / 2, yy + hh + 1), P(face))
    # center fin
    c.drawRect(skia.Rect(cx - 9, base - h - 150, cx + 9, base - h), P(dark))
    # rounded corner tower
    rrect(c, x - 18, base - h * 0.82, 60, h * 0.82, 30, mixhex(face, "#ffffff", 0.08))
    # horizontal "eyebrow" ledges and windows
    rows = int(h / 70)
    for j in range(rows):
        yy = base - h + 40 + j * 70
        c.drawRect(skia.Rect(x - 6, yy - 8, x + w + 6, yy - 2), P(dark))
        for i in range(int(w / 46)):
            wx = x + 18 + i * 46
            lit = rnd.random() < (0.55 * night + 0.1)
            colw = rnd.choice(("#ffd98a", "#ffe9c4", "#9ef6ff", "#ffb0d8")) if lit else mixhex(dark, "#000000", 0.3)
            c.drawRect(skia.Rect(wx, yy + 6, wx + 26, yy + 38), P(colw, a=0.95 if lit else 0.8))
    # neon outline on the crown + vertical sign
    if night > 0.2:
        fl = 1.0 if math.sin(t * 17 + seed) > -0.95 else 0.4
        pth = skia.Path()
        pth.moveTo(x, base - h)
        pth.lineTo(x + w, base - h)
        c.drawPath(pth, blurp(neon, 10, 0.9 * night * fl, 8))
        c.drawPath(pth, P(neon, 4, night * fl))
        sx = x + w - 34
        sh = len(sign) * 46 + 30
        sy = base - h + 30
        rrect(c, sx - 26, sy, 52, sh, 10, "#140a24")
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(sx - 26, sy, 52, sh), 10, 10), blurp(neon, 10, 0.8 * fl, 6))
        for k, ch in enumerate(sign):
            ftext(c, ch, sx, sy + 52 + k * 46, 40, mixhex(neon, "#ffffff", 0.5), "InterDisplay-Black", a=fl * night,
                  glow_c=neon, glow_r=10)
    # awning + entrance
    rrect(c, cx - 70, base - 90, 140, 90, 6, "#1a0f28")
    c.drawPath(poly([(cx - 90, base - 100), (cx + 90, base - 100), (cx + 76, base - 74), (cx - 76, base - 74)]),
               P(neon if night > 0.2 else mixhex(col, "#000000", 0.2)))
    glow(c, cx, base - 40, 120, "#ffd98a", 0.35 * night)


def ocean_drive_layer(night=1.0, base=860, seed=21):
    """Cached transparent strip of deco hotels (full width plus overscan)."""
    key = ("odrive", round(night, 2), base, seed)

    def draw(cc):
        rnd = random.Random(seed)
        x = -80
        i = 0
        while x < W + 200:
            w = rnd.uniform(260, 420)
            h = rnd.uniform(300, 520)
            deco_hotel(cc, x, base, w, h, rnd.choice(PASTELS), rnd.choice(NEONS), rnd.choice(SIGNS), night,
                       seed=seed * 10 + i)
            x += w + rnd.uniform(40, 90)
            i += 1
    return _cached_t(key, draw)


def street_lamp(c, x, base, night=1.0, h=360):
    line(c, x, base, x, base - h, "#1a1226", 10)
    line(c, x, base - h, x + 60, base - h - 10, "#1a1226", 8)
    c.drawCircle(x + 64, base - h - 6, 12, P("#fff3c4"))
    glow(c, x + 64, base - h, 160, "#ffd98a", 0.4 * night)
    c.drawPath(poly([(x + 52, base - h), (x + 76, base - h), (x + 200, base), (x - 70, base)]),
               P("#ffd98a", a=0.05 * night))


def cop_car(c, x, y, s=1.0, t=0.0, face=1, lights=True, a=1.0):
    """Original police cruiser: black/white sedan with roof light bar."""
    with xf(c, x, y, s, alpha=a, sx=s * face, sy=s):
        c.drawOval(skia.Rect(-250, -10, 250, 14), P("#000000", a=0.5))
        body = skia.Path()
        body.moveTo(-250, -32)
        body.lineTo(-248, -90)
        body.lineTo(-120, -100)
        body.lineTo(-70, -160)
        body.lineTo(110, -160)
        body.lineTo(170, -102)
        body.lineTo(250, -92)
        body.lineTo(256, -32)
        body.close()
        c.drawPath(body, P("#101218"))
        c.save()
        c.clipPath(body, skia.ClipOp.kIntersect, True)
        c.drawRect(skia.Rect(-110, -160, 160, -32), P("#f2f2f2"))
        c.restore()
        win = poly([(-60, -150), (100, -150), (150, -104), (-100, -104)])
        c.drawPath(win, P("#1b2340"))
        line(c, 30, -150, 26, -104, "#101218", 7)
        line(c, -246, -70, 252, -70, "#2a2d36", 3)
        rrect(c, -10, -90, 70, 22, 4, "#d6b84a")
        # light bar
        rrect(c, -40, -178, 120, 18, 6, "#20232c")
        if lights:
            ph = int(t * 8) % 2
            rc, bc = ("#ff2a2a", "#2a6bff") if ph == 0 else ("#5a1010", "#102a6a")
            rrect(c, -36, -176, 54, 14, 4, rc)
            rrect(c, 22, -176, 54, 14, 4, bc)
            glow(c, -10, -170, 220, "#ff2a2a", 0.55 if ph == 0 else 0.15)
            glow(c, 50, -170, 220, "#2a6bff", 0.55 if ph == 1 else 0.15)
        rrect(c, 236, -82, 20, 10, 4, "#fff6d0")
        for wx in (-150, 160):
            c.drawCircle(wx, -26, 44, P("#08060c"))
            c.drawCircle(wx, -26, 26, P("#9aa0ad"))
            c.drawCircle(wx, -26, 8, P("#2a2d36"))


def helicopter(c, x, y, s=1.0, t=0.0, beam=0.0, beam_to=None):
    with xf(c, x, y, s):
        if beam > 0 and beam_to:
            bx, by = (beam_to[0] - x) / s, (beam_to[1] - y) / s
            c.drawPath(poly([(-10, 30), (10, 30), (bx + 160, by), (bx - 160, by)]), P("#fff6d0", a=0.12 * beam))
            c.drawOval(skia.Rect(bx - 160, by - 30, bx + 160, by + 30), P("#fff6d0", a=0.18 * beam))
        rrect(c, -90, -30, 160, 70, 34, "#121522")
        c.drawPath(poly([(60, -10), (220, -4), (230, -30), (240, -30), (236, 10), (60, 18)]), P("#121522"))
        c.drawPath(poly([(-80, -20), (-30, -24), (-30, 20), (-70, 20)]), P("#3a5a8a", a=0.9))
        line(c, -80, 50, 60, 50, "#121522", 6)
        line(c, -60, 40, -60, 50, "#121522", 5)
        line(c, 40, 40, 40, 50, "#121522", 5)
        line(c, -10, -30, -10, -46, "#121522", 6)
        sw = math.cos(t * 40)
        line(c, -10 - 200 * sw, -48, -10 + 200 * sw, -48, "#121522", 6)
        c.drawCircle(-90, 10, 6, P(RED if int(t * 3) % 2 else "#440000"))


def boat(c, x, y, s=1.0, t=0.0, wake=True):
    with xf(c, x, y + math.sin(t * 2) * 4, s):
        if wake:
            for i in range(6):
                line(c, -200 - i * 60, 12 + i * 3, -150 - i * 60, 12 + i * 3, "#ffffff", 4, 0.5 - i * 0.07)
        c.drawPath(poly([(-180, 0), (200, 0), (150, 40), (-160, 40)]), P("#f4f1ea"))
        c.drawPath(poly([(-180, 0), (200, 0), (195, 10), (-178, 10)]), P(HOT))
        c.drawPath(poly([(-60, 0), (60, -50), (110, -50), (90, 0)]), P("#1b2340"))


def convertible(c, x, y, s=1.0, body="#ff3d8b", t=0.0, face=1, glow_c=None, riders=None, spin=0.0):
    """Open-top cruiser; riders(c) draws people inside (in car space)."""
    with xf(c, x, y, s, sx=s * face, sy=s):
        if glow_c:
            c.drawOval(skia.Rect(-270, -20, 270, 22), blurp(glow_c, 26, 0.75))
        c.drawOval(skia.Rect(-260, -10, 260, 14), P("#000000", a=0.5))
        if riders:
            riders(c)
        b = skia.Path()
        b.moveTo(-262, -32)
        b.lineTo(-258, -92)
        b.lineTo(-60, -100)
        b.lineTo(20, -128)
        b.lineTo(40, -100)
        b.lineTo(250, -92)
        b.lineTo(266, -40)
        b.lineTo(262, -32)
        b.close()
        c.drawPath(b, skia.Paint(AntiAlias=True, Shader=linear(0, -130, 0, -30, [mixhex(body, "#ffffff", 0.3), body,
                                                                                  mixhex(body, "#000000", 0.5)])))
        line(c, -250, -72, 250, -74, "#ffffff", 4, 0.6)
        line(c, 20, -128, 40, -100, "#bfe3ff", 6, 0.9)
        rrect(c, 240, -84, 22, 10, 4, "#fff6d0")
        glow(c, 262, -79, 60, "#fff1b0", 0.5)
        for wx in (-160, 165):
            c.drawCircle(wx, -26, 42, P("#08060c"))
            c.drawCircle(wx, -26, 26, P("#e6e6ea"))
            for k in range(6):
                ang = spin + k * math.pi / 3
                line(c, wx, -26, wx + math.cos(ang) * 22, -26 + math.sin(ang) * 22, "#9aa0ad", 5)


def beach_scene(c, t, night=0.0, cam=0.0, horizon=560):
    """Sunset beach + deco hotels on the left, ocean on the right — the postcard shot."""
    kind = "dusk" if night < 0.5 else "night"
    sky(c, kind, horizon + 40, t)
    if night < 0.5:
        retro_sun(c, W * 0.72 - cam * 0.05, horizon - 30, 190)
    clouds(c, t, 220, "#ff9cc0", 0.25)
    ocean(c, horizon, t, W * 0.72, kind)
    boat(c, 1500 - (t * 30) % 2400 + 600, horizon + 60, 0.4, t)
    # sand
    sand = skia.Path()
    sand.moveTo(0, 760)
    sand.cubicTo(500, 720, 1200, 860, W, 820)
    sand.lineTo(W, H)
    sand.lineTo(0, H)
    sand.close()
    c.drawPath(sand, skia.Paint(AntiAlias=True, Shader=linear(0, 720, 0, H, ["#e8b98a", "#b07a5a"])))
    c.drawPath(sand, P("#ffffff", 4, 0.35))


def ocean_drive(c, t, night=1.0, cam=0.0, base=860):
    """Street-level boulevard: deco hotels, palms, lamps, road."""
    kind = "night" if night > 0.5 else "dusk"
    sky(c, kind, base, t)
    if kind == "dusk":
        retro_sun(c, W * 0.5, base - 200, 200, a=0.8)
    for img in city_layers_t(kind, base - 120)[:2]:
        sgfx.blit(c, img, -cam * 0.1, 0)
    od = ocean_drive_layer(night if night > 0.5 else 0.35, base)
    sgfx.blit(c, od, -(cam * 0.6) % 400 - 100 if False else -cam * 0.6, 0)
    # sidewalk + road
    c.drawRect(skia.Rect(0, base, W, base + 40), P("#3a2f4a"))
    fill_shader(c, skia.Rect(0, base + 40, W, H), linear(0, base + 40, 0, H, ["#1a1028", "#07050d"]))
    for x, col in ((260, PINK), (760, CYAN), (1250, GOLD), (1700, TEAL)):
        c.drawRect(skia.Rect(x - 30, base + 40, x + 30, H), blurp(col, 22, 0.16 * night + 0.04))
    off = (cam * 1.0) % 240
    for i in range(-1, 10):
        rrect(c, i * 240 - off, base + 130, 120, 10, 4, "#ffe9a8", 0.6)
    for i, x in enumerate((-100, 520, 1140, 1760)):
        xx = (x - cam * 0.9) % (W + 600) - 300
        palm(c, xx, base + 30, 1.0, "#120a1e", t, 0.8, lean=6 if i % 2 else -6)
        street_lamp(c, xx + 300, base + 30, night)


# ------------------------------------------------------------------ explainer helpers
def callout(c, t, start, px, py, lx, ly, label, color=GOLD, size=40, dot=True, end=None, fg="#0b0614"):
    """Animated leader line from a point (px,py) to a label box at (lx,ly)."""
    if t < start:
        return
    out = 1.0 if end is None else clamp((end - t) / 0.25)
    k = ease_out(at(t, start, 0.45))
    if dot:
        c.drawCircle(px, py, 12 * min(1, k * 3), P(color, a=out))
        c.drawCircle(px, py, 22 * min(1, k * 3), P(color, 3, 0.6 * out))
    # elbow line: diagonal then horizontal
    mx, my = lerp(px, lx, 0.55), ly
    seg1 = math.hypot(mx - px, my - py)
    seg2 = abs(lx - mx)
    tot = seg1 + seg2
    d = tot * k
    pth = skia.Path()
    pth.moveTo(px, py)
    if d <= seg1:
        f = d / max(1, seg1)
        pth.lineTo(lerp(px, mx, f), lerp(py, my, f))
    else:
        pth.lineTo(mx, my)
        f = (d - seg1) / max(1, seg2)
        pth.lineTo(lerp(mx, lx, f), my)
    c.drawPath(pth, P("#000000", 9, 0.5 * out))
    c.drawPath(pth, P(color, 4, out))
    if k >= 0.95:
        kk = back_out(at(t, start + 0.4, 0.3))
        w = tw(label, size) + 40
        left = lx if lx >= px else lx - w
        with xf(c, left + w / 2, ly, kk, alpha=out):
            rrect(c, -w / 2, -size * 0.75, w, size * 1.5, 10, color)
            ftext(c, label, 0, size * 0.35, size, fg)


def draw_line_anim(c, pts, k, color, w=8, glow_on=True, dash=False, t=0.0, a=1.0):
    """Polyline revealed by fraction k."""
    L = [0.0]
    for i in range(1, len(pts)):
        L.append(L[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    tot = L[-1] or 1
    d = tot * clamp(k)
    pth = skia.Path()
    pth.moveTo(*pts[0])
    head = pts[0]
    for i in range(1, len(pts)):
        if L[i] <= d:
            pth.lineTo(*pts[i])
            head = pts[i]
        else:
            f = (d - L[i - 1]) / max(1e-6, L[i] - L[i - 1])
            head = (lerp(pts[i - 1][0], pts[i][0], f), lerp(pts[i - 1][1], pts[i][1], f))
            pth.lineTo(*head)
            break
    if glow_on:
        c.drawPath(pth, blurp(color, w, 0.7 * a, w * 2.2))
    p = P(color, w, a)
    if dash:
        p.setPathEffect(skia.DashPathEffect.Make([w * 2.4, w * 1.6], -t * 60))
    c.drawPath(pth, p)
    return head


def flow_diagram(c, t, start, items, total_xy, color=GOLD, total_label="TOTAL", total_val=None):
    """Lines from several item boxes merging into one total box. items: [(x, y, label)]."""
    tx, ty = total_xy
    for i, (x, y, lab) in enumerate(items):
        st = start + i * 0.15
        if t < st:
            continue
        k = ease_out(at(t, st, 0.6))
        mid = (lerp(x, tx, 0.5), y)
        mid2 = (lerp(x, tx, 0.5), ty)
        draw_line_anim(c, [(x, y), mid, mid2, (tx - 160, ty)], k, color, 6, t=t, dash=True)
        w = tw(lab, 40) + 40
        with xf(c, x, y, back_out(at(t, st, 0.3))):
            rrect(c, -w / 2, -34, w, 68, 12, "#140a2a")
            rrect(c, -w / 2, -34, w, 68, 12, color, stroke=4)
            ftext(c, lab, 0, 14, 40, "#ffffff")
    st = start + len(items) * 0.15 + 0.2
    if t > st:
        k = back_out(at(t, st, 0.35))
        with xf(c, tx, ty, k):
            rrect(c, -170, -90, 340, 180, 22, color)
            ftext(c, total_label, 0, -20, 40, "#0b0614")
            if total_val:
                ftext(c, total_val, 0, 58, 76, "#0b0614")
