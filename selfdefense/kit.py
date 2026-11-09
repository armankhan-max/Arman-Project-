"""Visual kit for the self-defense video: palette, text, backgrounds, figures,
anatomy and props. Everything is vector art drawn with skia (no stock
footage, no images except the avatar photo)."""
import math, os, sys, random
import numpy as np
import skia

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video"))
from gfx import (C, P, xf, rrect, poly, line, linear, radial, fill_shader, clamp, lerp,  # noqa: E402,F401
                 smooth, ease_out, back_out, at, window, mixhex, check_mark, cross_mark)

W, H = 1920, 1080
INK = "#0b0a09"; PAPER = "#efe6d2"; GOLD = "#e0a83e"; RED = "#d1132f"; BONE = "#eadfc8"
STEEL = "#9fb4c2"; XRAY = "#7fd4ff"; SKIN = "#c48a62"; DIM = "#8a7f70"; GREEN = "#48c774"

FONTS = {
    "black": "/usr/share/fonts/opentype/inter/Inter-Black.otf",
    "bold": "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
    "semi": "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
    "serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "serifi": "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf",
    "jp": "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
}
_tf, _ft = {}, {}


def font(size, kind="black"):
    k = (kind, round(size, 1))
    if k not in _ft:
        if kind not in _tf:
            _tf[kind] = skia.Typeface.MakeFromFile(FONTS[kind])
        f = skia.Font(_tf[kind], size); f.setEdging(skia.Font.Edging.kAntiAlias)
        _ft[k] = f
    return _ft[k]


def tw(s, size, kind="black"):
    return font(size, kind).measureText(s)


def text(c, s, x, y, size, color="#ffffff", kind="black", align="center", a=1.0, shadow=0.0, stroke=None, sw=0, spacing=0):
    f = font(size, kind)
    w = f.measureText(s) + spacing * max(0, len(s) - 1)
    if align == "center": x -= w / 2
    elif align == "right": x -= w
    if a <= 0: return w
    def draw(dx, dy, p):
        if spacing:
            xx = x + dx
            for ch in s:
                c.drawString(ch, xx, y + dy, f, p); xx += f.measureText(ch) + spacing
        else:
            c.drawString(s, x + dx, y + dy, f, p)
    if shadow:
        draw(size * 0.04, size * 0.06, P("#000000", a=shadow * a))
    if stroke:
        draw(0, 0, P(stroke, sw, a))
    draw(0, 0, P(color, a=a))
    return w


def glow(c, x, y, r, color, a=0.6):
    if a <= 0: return
    fill_shader(c, skia.Rect(x - r, y - r, x + r, y + r), radial(x, y, r, [(color, a), (color, 0)]))


def rect(c, x, y, w, h, color, a=1.0):
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), P(color, a=a))


def blurred(radius):
    p = skia.Paint(AntiAlias=True)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, radius))
    return p


def soft_shape(c, path, color, a, radius):
    p = blurred(radius); p.setColor(C(color, a)); c.drawPath(path, p)


def rng(seed):
    return random.Random(seed)


# ------------------------------------------------------------------ backgrounds
def bg_dark(c, w, h, t, tone="#1a1410", light=(0.75, 0.15), a=1.0):
    """Moody dark room with a warm light shaft and floating dust."""
    fill_shader(c, skia.Rect(0, 0, w, h), linear(0, 0, 0, h, [mixhex(tone, "#000000", 0.2), mixhex(tone, "#000000", 0.75)]))
    lx, ly = w * light[0], h * light[1]
    glow(c, lx, ly, max(w, h) * 0.7, "#ffb35a", 0.16 * a)
    # light shaft
    p = poly([(lx - 60, -20), (lx + 90, -20), (lx - w * 0.2, h + 20), (lx - w * 0.45, h + 20)])
    soft_shape(c, p, "#ffd08a", 0.05 * a, 40)
    r = rng(3)
    for i in range(40):
        x0 = r.uniform(0, w); y0 = r.uniform(0, h); sp = r.uniform(4, 14)
        x = (x0 + math.sin(t * 0.3 + i) * 30) % w; y = (y0 - t * sp) % h
        c.drawCircle(x, y, r.uniform(1.0, 2.6), P("#ffe3b0", a=0.25 * a * (0.5 + 0.5 * math.sin(t + i))))


def bg_paper(c, w, h, t, a=1.0):
    fill_shader(c, skia.Rect(0, 0, w, h), radial(w / 2, h / 2, max(w, h) * 0.75, ["#efe4cc", "#c9b896"]))
    r = rng(11)
    for i in range(160):
        x = r.uniform(0, w); y = r.uniform(0, h)
        c.drawCircle(x, y, r.uniform(0.5, 2.2), P("#6b5a3e", a=r.uniform(0.03, 0.09)))
    for i in range(14):
        y = r.uniform(0, h)
        line(c, 0, y, w, y + r.uniform(-30, 30), "#8a7556", r.uniform(0.6, 1.4), 0.05)


def bg_xray(c, w, h, t):
    fill_shader(c, skia.Rect(0, 0, w, h), radial(w / 2, h * 0.45, max(w, h) * 0.7, ["#0e2a3d", "#04080d"]))
    for i in range(0, int(w) + 60, 60):
        line(c, i, 0, i, h, XRAY, 1, 0.05)
    for j in range(0, int(h) + 60, 60):
        line(c, 0, j, w, j, XRAY, 1, 0.05)
    y = (t * 260) % (h + 200) - 100
    fill_shader(c, skia.Rect(0, y - 60, w, y + 60), linear(0, y - 60, 0, y + 60, [(XRAY, 0), (XRAY, 0.08), (XRAY, 0)]))


def bg_night_street(c, w, h, t, sign="薬", sign_col="#3fe0a0", rain=True):
    fill_shader(c, skia.Rect(0, 0, w, h), linear(0, 0, 0, h, ["#05070c", "#0f1420", "#16110d"]))
    r = rng(5)
    # buildings
    x = -40
    while x < w + 40:
        bw = r.uniform(140, 260); bh = r.uniform(380, 760)
        rect(c, x, h * 0.78 - bh, bw - 8, bh, "#0c0f16")
        for wy in range(int(h * 0.78 - bh + 30), int(h * 0.74), 46):
            for wx in range(int(x + 18), int(x + bw - 30), 38):
                if r.random() < 0.28:
                    rect(c, wx, wy, 20, 26, r.choice(["#ffcf7a", "#ffb35a", "#9fd3ff"]), 0.35 + 0.25 * r.random())
        x += bw
    # wet ground
    fill_shader(c, skia.Rect(0, h * 0.78, w, h), linear(0, h * 0.78, 0, h, ["#1a1712", "#070605"]))
    # neon sign
    sx, sy = w * 0.68, h * 0.38
    fl = 0.85 + 0.15 * math.sin(t * 23) * (1 if int(t * 3) % 7 == 0 else 0)
    rrect(c, sx - 70, sy - 110, 140, 220, 10, "#0a0a0a")
    glow(c, sx, sy, 260, sign_col, 0.35 * fl)
    text(c, sign, sx, sy + 45, 120, sign_col, "jp", a=fl)
    glow(c, sx, h * 0.86, 220, sign_col, 0.18 * fl)  # reflection
    # door with light
    dx = w * 0.3
    rect(c, dx, h * 0.78 - 300, 150, 300, "#ffcf87", 0.85)
    glow(c, dx + 75, h * 0.78 - 150, 260, "#ffb35a", 0.3)
    fill_shader(c, skia.Rect(dx - 80, h * 0.78, dx + 230, h), linear(0, h * 0.78, 0, h, [("#ffcf87", 0.35), ("#ffcf87", 0)]))
    if rain:
        rr = rng(9)
        for i in range(140):
            x0 = rr.uniform(0, w); sp = rr.uniform(900, 1400); y = (rr.uniform(0, h) + t * sp) % h
            line(c, x0 - y * 0.08, y, x0 - y * 0.08 - 6, y + 34, "#9fb7d6", 1.2, 0.25)


def bg_dojo(c, w, h, t, a=1.0):
    fill_shader(c, skia.Rect(0, 0, w, h), linear(0, 0, 0, h, ["#2a1d12", "#120c07"]))
    # shoji wall
    for i in range(-1, int(w / 160) + 2):
        x = i * 160 + (w % 160) / 2
        rect(c, x, 80, 150, h * 0.55, "#e8d6b0", 0.22)
        for k in range(1, 4):
            line(c, x + k * 37.5, 80, x + k * 37.5, 80 + h * 0.55, "#2a1d12", 4, 0.8)
        for k in range(1, 6):
            line(c, x, 80 + k * h * 0.55 / 6, x + 150, 80 + k * h * 0.55 / 6, "#2a1d12", 4, 0.8)
        rect(c, x - 6, 60, 12, h * 0.6, "#1c120a")
    glow(c, w * 0.5, h * 0.35, w * 0.6, "#ffcf87", 0.18)
    # tatami floor
    fy = h * 0.66
    fill_shader(c, skia.Rect(0, fy, w, h), linear(0, fy, 0, h, ["#b59a5c", "#5d4a28"]))
    for i in range(-6, 7):
        line(c, w / 2 + i * 60, fy, w / 2 + i * 260, h, "#3b2e16", 3, 0.5)
    line(c, 0, fy, w, fy, "#1c120a", 10)


def grain_overlay(c, w, h, t, a=0.05):
    r = rng(int(t * 24))
    for i in range(60):
        c.drawCircle(r.uniform(0, w), r.uniform(0, h), r.uniform(0.6, 1.6), P("#ffffff" if i % 2 else "#000000", a=a))


def vignette(c, w, h, a=0.55):
    fill_shader(c, skia.Rect(0, 0, w, h), radial(w / 2, h / 2, max(w, h) * 0.72, [("#000000", 0), ("#000000", 0), ("#000000", a)], [0, 0.55, 1]))


# ------------------------------------------------------------------ type helpers
def brush_bar(c, x, y, w, h, color=RED, prog=1.0, a=1.0, seed=1):
    """Ink brush stroke bar that paints in from left."""
    if prog <= 0: return
    r = rng(seed); ww = w * clamp(prog)
    p = skia.Path(); p.moveTo(x, y + h * 0.15)
    n = 14
    for i in range(n + 1):
        p.lineTo(x + ww * i / n, y + r.uniform(-0.08, 0.12) * h)
    for i in range(n, -1, -1):
        p.lineTo(x + ww * i / n, y + h + r.uniform(-0.15, 0.06) * h)
    p.close()
    c.drawPath(p, P(color, a=a))
    for k in range(5):
        yy = y + h * (0.15 + 0.17 * k)
        line(c, x + ww - r.uniform(5, 60), yy, x + ww + r.uniform(0, 26), yy + r.uniform(-3, 3), color, r.uniform(2, 5), a * 0.7)


EVENTS = []          # filled during the sfx dry-run: (kind, local t0)
REC = {"on": False}


def ev(kind, t, t0):
    if REC["on"] and t >= t0:
        EVENTS.append((kind, round(t0, 2)))


def pop(t, start, dur=0.35):
    return back_out(at(t, start, dur))


def kicker(c, t, t0, t1, s, x, y, size=84, color="#ffffff", bar=RED, kind="black"):
    """Big caption that pops in with a brush bar behind it."""
    k = window(t, t0, t1, 0.18)
    ev("kick", t, t0)
    if k <= 0: return
    sc = 0.85 + 0.15 * pop(t, t0, 0.3)
    fw = tw(s, size, kind)
    if fw > 940: size = size * 940 / fw
    with xf(c, x, y, s=sc, alpha=k):
        w = tw(s, size, kind)
        if bar:
            brush_bar(c, -w / 2 - 34, -size * 0.92, w + 68, size * 1.22, bar, at(t, t0, 0.25), seed=len(s))
        text(c, s, 0, 0, size, color, kind, shadow=0.5 if not bar else 0)


def counter(c, t, t0, x, y, val, size=180, color=GOLD, dur=0.9, fmt="{:d}", suffix="", kind="black"):
    ev("count", t, t0)
    p = ease_out(at(t, t0, dur))
    v = fmt.format(int(round(val * p))) + suffix
    text(c, v, x, y, size, color, kind, a=clamp((t - t0) / 0.15), shadow=0.6)


def stamp(c, t, t0, x, y, s, color=RED, size=60, rot=-8):
    ev("stamp", t, t0)
    k = at(t, t0, 0.22)
    if k <= 0: return
    sc = 2.2 - 1.2 * ease_out(k)
    with xf(c, x, y, s=sc, rot=rot, alpha=clamp(k * 2)):
        w = tw(s, size, "black") + 50; h = size * 1.5
        rrect(c, -w / 2, -h / 2, w, h, 10, color, 1, stroke=7)
        text(c, s, 0, size * 0.36, size, color, "black")


def label_line(c, t, t0, x1, y1, x2, y2, s, color=GOLD, size=40, align="left"):
    k = ease_out(at(t, t0, 0.4))
    if k <= 0: return
    xm, ym = lerp(x1, x2, k), lerp(y1, y2, k)
    c.drawCircle(x1, y1, 9, P(color)); line(c, x1, y1, xm, ym, color, 4)
    if k > 0.7:
        a = (k - 0.7) / 0.3
        text(c, s, x2 + (14 if align == "left" else -14), y2 + size * 0.35, size, color, "black", align=align, a=a, shadow=0.6)


# ------------------------------------------------------------------ figures
def capsule(c, x1, y1, x2, y2, w, color, a=1.0):
    line(c, x1, y1, x2, y2, color, w, a)


def man(c, x, y, s=1.0, pose="stand", t=0.0, color="#121212", rim=None, big=1.0, legs=True, a=1.0, run=0.0):
    """Front-facing silhouette. (x, y) = feet centre. Height ~ 900*s.
    pose: stand | guard_high | guard_low | palm | charge | sit | kick"""
    with xf(c, x, y, s=s, alpha=a):
        bw = big
        hip_y, sh_y, head_y = -470, -760, -850
        breathe = math.sin(t * 2.2) * 4
        sh_y += breathe; head_y += breathe
        sw = 150 * bw  # half shoulder width
        def body(col, off=0.0):
            # legs
            if legs:
                ph = math.sin(run * 9) * 60 if run else 0
                if pose == "kick":
                    capsule(c, -50 * bw, hip_y, -70 * bw, -10, 95 * bw + off, col)
                    capsule(c, 50 * bw, hip_y, 260, -250, 90 * bw + off, col)
                elif pose == "sit":
                    capsule(c, -60 * bw, hip_y + 200, -160 * bw, -20, 95 * bw + off, col)
                    capsule(c, 60 * bw, hip_y + 200, 160 * bw, -20, 95 * bw + off, col)
                else:
                    capsule(c, -55 * bw, hip_y, -70 * bw - ph * 0.2, -10 + max(0, ph) * 0.5, 100 * bw + off, col)
                    capsule(c, 55 * bw, hip_y, 70 * bw - ph * 0.2, -10 + max(0, -ph) * 0.5, 100 * bw + off, col)
            # torso
            hy = hip_y + (200 if pose == "sit" else 0)
            o2 = off / 2
            tp = skia.Path(); tp.moveTo(-sw * 0.35 - o2, sh_y - 25 - o2)
            tp.lineTo(sw * 0.35 + o2, sh_y - 25 - o2)
            tp.quadTo(sw + o2, sh_y - 15 - o2, sw + 8 + o2, sh_y + 70)
            tp.lineTo(sw * 0.78 + o2, hy + 30); tp.lineTo(-sw * 0.78 - o2, hy + 30)
            tp.lineTo(-sw - 8 - o2, sh_y + 70)
            tp.quadTo(-sw - o2, sh_y - 15 - o2, -sw * 0.35 - o2, sh_y - 25 - o2); tp.close()
            c.drawPath(tp, P(col))
            # neck/head
            capsule(c, 0, sh_y, 0, head_y + 40, 80 * bw + off, col)
            c.drawOval(skia.Rect(-62 - off / 2, head_y - 75 - off / 2, 62 + off / 2, head_y + 75 + off / 2), P(col))
            # arms
            aw = 58 * bw + off
            if pose == "guard_high":
                for sgn in (-1, 1):
                    capsule(c, sgn * (sw - 20), sh_y + 30, sgn * 120, sh_y + 140, aw, col)
                    capsule(c, sgn * 120, sh_y + 140, sgn * 55, head_y + 10, aw * 0.9, col)
                    c.drawCircle(sgn * 50, head_y - 5, 42 + off / 2, P(col))
            elif pose == "palm":
                capsule(c, -(sw - 20), sh_y + 30, -sw - 60, hy + 40, aw, col)
                capsule(c, sw - 20, sh_y + 30, sw + 210, sh_y + 60, aw, col)
                c.drawCircle(sw + 230, sh_y + 55, 44 + off / 2, P(col))
            elif pose == "charge":
                for sgn in (-1, 1):
                    capsule(c, sgn * (sw - 20), sh_y + 30, sgn * (sw + 70), sh_y + 220, aw, col)
                    capsule(c, sgn * (sw + 70), sh_y + 220, sgn * (sw - 10), sh_y + 330 + sgn * math.sin(run * 9) * 40, aw * 0.9, col)
            else:  # stand / guard_low / sit / kick
                for sgn in (-1, 1):
                    capsule(c, sgn * (sw - 20), sh_y + 30, sgn * (sw + 30), hy + 30, aw, col)
                    capsule(c, sgn * (sw + 30), hy + 30, sgn * (sw + 10), hy + 230, aw * 0.9, col)
        if rim:
            body(rim, 10)
        body(color)


def torso_anatomy(c, x, y, s, t, show=("ribs",), hi=None, a=1.0):
    """Ribs / liver / solar plexus overlay for man() at the same x,y,s (big=1)."""
    with xf(c, x, y, s=s, alpha=a):
        sh = -760
        if "ribs" in show:
            line(c, 0, sh + 40, 0, sh + 210, BONE, 10, 0.55)  # sternum
            for i in range(7):
                yy = sh + 50 + i * 30; wdt = 110 - i * 2
                for sgn in (-1, 1):
                    p = skia.Path(); p.moveTo(sgn * 8, yy)
                    p.cubicTo(sgn * wdt * 0.6, yy - 10, sgn * wdt, yy + 10, sgn * (wdt - 5), yy + 40 + i * 4)
                    c.drawPath(p, P(BONE, 6, 0.45))
            # costal arch
            for sgn in (-1, 1):
                p = skia.Path(); p.moveTo(0, sh + 215); p.quadTo(sgn * 60, sh + 250, sgn * 112, sh + 300)
                c.drawPath(p, P(BONE, 7, 0.55))
        if "liver" in show:
            pul = 0.5 + 0.5 * math.sin(t * 6)
            p = skia.Path(); lx, ly = -60, sh + 255
            p.moveTo(lx - 75, ly - 20); p.cubicTo(lx - 20, ly - 55, lx + 60, ly - 45, lx + 80, ly - 10)
            p.cubicTo(lx + 40, ly + 10, lx - 10, ly + 45, lx - 70, ly + 40); p.close()
            glow(c, lx, ly, 160, RED, 0.35 + 0.25 * pul)
            c.drawPath(p, P("#8f2a22", a=0.95)); c.drawPath(p, P("#ff6b5a", 3, 0.8))
        if "plexus" in show:
            px, py = 0, sh + 245
            pul = 0.5 + 0.5 * math.sin(t * 7)
            glow(c, px, py, 120, GOLD, 0.35 + 0.3 * pul)
            r = rng(4)
            for i in range(12):
                ang = i / 12 * math.tau; L = 40 + r.uniform(0, 30)
                line(c, px, py, px + math.cos(ang) * L, py + math.sin(ang) * L, "#ffe08a", 3, 0.8)
            c.drawCircle(px, py, 12, P("#fff3c4"))


def reticle(c, x, y, r, t, color=RED, a=1.0, t0=0.0):
    k = ease_out(at(t, t0, 0.5))
    if k <= 0: return
    rr = r * (2.2 - 1.2 * k)
    with xf(c, x, y, rot=t * 40, alpha=a * k):
        c.drawCircle(0, 0, rr, P(color, 5))
        for i in range(4):
            with xf(c, 0, 0, rot=i * 90):
                line(c, 0, -rr - 22, 0, -rr + 14, color, 6)
    c.drawCircle(x, y, 7, P(color, a=a * k))


# ------------------------------------------------------------------ hands & bones
HAND_BONES = None


def hand_skeleton(c, x, y, s, t, color=BONE, crack=0.0, glowc=XRAY, fist=0.0, a=1.0):
    """27 bones: 8 carpals, 5 metacarpals, 14 phalanges. Fingers point up."""
    with xf(c, x, y, s=s, alpha=a):
        # carpals
        r = rng(2)
        for i in range(8):
            cx = -60 + (i % 4) * 40 + r.uniform(-4, 4); cy = 40 + (i // 4) * 38
            c.drawOval(skia.Rect(cx - 19, cy - 15, cx + 19, cy + 15), P(color, a=0.9))
        fingers = [(-95, -10, 0.55, -35), (-55, -40, 1.0, -8), (-10, -48, 1.08, 0), (35, -42, 1.0, 6), (75, -28, 0.82, 14)]
        for fi, (bx, by, L, ang) in enumerate(fingers):
            ang = math.radians(ang)
            segs = [120 * L, 70 * L, 46 * L, 34 * L] if fi else [100 * L, 80 * L, 60 * L]
            px, py = bx, by + 30
            a_ = ang
            for si, sl in enumerate(segs):
                bend = fist * (1.5 if si > 0 else 0.25)
                a_ = a_ + bend * (0.6 if fi == 0 else 1)
                nx = px + math.sin(a_) * sl; ny = py - math.cos(a_) * sl * (1 - 0.15 * fist)
                wdt = 26 - si * 3
                line(c, px, py, nx, ny, color, wdt, 0.95)
                c.drawCircle(nx, ny, wdt * 0.62, P(color))
                px, py = nx + math.sin(a_) * 6, ny - math.cos(a_) * 6
        if crack > 0:
            glow(c, -10, -140, 170, RED, 0.6 * crack)
            pts = [(-30, -200), (-12, -165), (-36, -140), (-6, -100), (-26, -70)]
            p = poly(pts, close=False)
            c.drawPath(p, P(RED, 7, crack))
            c.drawPath(p, P("#ffffff", 2, crack))


def skull_profile(c, x, y, s, color=BONE, a=1.0, helmet=0.0, t=0.0):
    with xf(c, x, y, s=s, alpha=a):
        p = skia.Path()
        p.moveTo(-150, 40); p.cubicTo(-170, -160, 60, -230, 150, -90)   # cranium
        p.cubicTo(175, -40, 170, 10, 150, 40)                           # forehead
        p.lineTo(168, 70); p.lineTo(150, 95); p.lineTo(170, 130)          # brow/nose
        p.lineTo(150, 150); p.lineTo(155, 185); p.cubicTo(120, 215, 60, 215, 30, 190)  # jaw
        p.cubicTo(10, 160, -30, 140, -60, 140); p.cubicTo(-110, 130, -140, 100, -150, 40); p.close()
        c.drawPath(p, P(color, a=0.95))
        c.drawOval(skia.Rect(70, 40, 128, 88), P("#0a0f14"))           # orbit
        c.drawOval(skia.Rect(-30, 60, 10, 110), P("#0a0f14", a=0.6))     # ear
        if helmet > 0:
            hp = skia.Path(); hp.moveTo(-165, 30); hp.cubicTo(-185, -185, 70, -255, 172, -95)
            hp.cubicTo(195, -40, 190, 10, 170, 48)
            c.drawPath(hp, P(STEEL, 14 * helmet, helmet))
            glow(c, 160, 0, 120, STEEL, 0.4 * helmet)


def fist_shape(c, x, y, s, color=SKIN, rot=0.0, a=1.0, outline="#2a1a10"):
    with xf(c, x, y, s=s, rot=rot, alpha=a):
        rrect(c, -90, -70, 180, 140, 46, color)
        for i in range(4):
            rrect(c, -90 + i * 45, -78, 44, 60, 20, mixhex(color, "#ffffff", 0.08))
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-90 + i * 45, -78, 44, 60), 20, 20), P(outline, 3, 0.6))
        rrect(c, -100, -10, 70, 50, 24, mixhex(color, "#000000", 0.1))  # thumb
        rrect(c, -70, 60, 140, 70, 20, color)                            # wrist
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-90, -70, 180, 140), 46, 46), P(outline, 4, 0.6))


def palm_shape(c, x, y, s, color=SKIN, rot=0.0, a=1.0, heel=0.0, t=0.0, outline="#2a1a10"):
    """Open hand, fingers bent back, heel of palm towards +x (strike side up)."""
    with xf(c, x, y, s=s, rot=rot, alpha=a):
        rrect(c, -80, -60, 160, 180, 60, color)                           # palm
        for i, (fx, L) in enumerate([(-62, 120), (-22, 140), (18, 135), (56, 110)]):
            rrect(c, fx - 18, -60 - L, 38, L + 30, 19, color)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(fx - 18, -60 - L, 38, L + 30), 19, 19), P(outline, 3, 0.5))
        with xf(c, -80, 40, rot=-40):
            rrect(c, -110, -22, 120, 46, 22, color)                       # thumb
        rrect(c, -60, 110, 120, 90, 20, color)                            # wrist
        if heel > 0:
            pul = 0.6 + 0.4 * math.sin(t * 8)
            glow(c, 0, 95, 110, GOLD, 0.6 * heel * pul)
            c.drawOval(skia.Rect(-60, 60, 60, 125), P(GOLD, 6, heel))


def x_over(c, x, y, s, t, t0, color=RED):
    ev("x", t, t0)
    k = at(t, t0, 0.25)
    if k <= 0: return
    L = s * ease_out(k)
    line(c, x - L / 2, y - L / 2, x + L / 2, y + L / 2, color, s * 0.13)
    if k > 0.5:
        k2 = (k - 0.5) * 2; L2 = s * ease_out(k2)
        line(c, x + L2 / 2, y - L2 / 2, x - L2 / 2, y + L2 / 2, color, s * 0.13)


def tick(c, x, y, s, t, t0, color=GREEN):
    ev("tick", t, t0)
    check_mark(c, x, y, s, color, prog=ease_out(at(t, t0, 0.35)))


def arrow(c, x1, y1, x2, y2, color, w=14, a=1.0, head=2.8, prog=1.0):
    if prog <= 0: return
    x2, y2 = lerp(x1, x2, prog), lerp(y1, y2, prog)
    ang = math.atan2(y2 - y1, x2 - x1); hl = w * head
    bx, by = x2 - math.cos(ang) * hl * 0.8, y2 - math.sin(ang) * hl * 0.8
    line(c, x1, y1, bx, by, color, w, a)
    p = poly([(x2, y2), (x2 - math.cos(ang - 0.5) * hl, y2 - math.sin(ang - 0.5) * hl),
              (x2 - math.cos(ang + 0.5) * hl, y2 - math.sin(ang + 0.5) * hl)])
    c.drawPath(p, P(color, a=a))


def speed_lines(c, w, h, t, cx, cy, a=0.5, n=50, color="#ffffff"):
    r = rng(int(t * 12))
    for i in range(n):
        ang = r.uniform(0, math.tau); r0 = r.uniform(0.35, 0.6) * max(w, h); L = r.uniform(80, 260)
        line(c, cx + math.cos(ang) * r0, cy + math.sin(ang) * r0, cx + math.cos(ang) * (r0 + L), cy + math.sin(ang) * (r0 + L), color, r.uniform(2, 5), a)


def impact(c, x, y, t, t0, color="#ffffff", r=160):
    ev("impact", t, t0)
    k = at(t, t0, 0.35)
    if k <= 0 or k >= 1: return
    rr = r * ease_out(k)
    c.drawCircle(x, y, rr, P(color, 10 * (1 - k), 1 - k))
    for i in range(10):
        ang = i / 10 * math.tau + 0.3
        line(c, x + math.cos(ang) * rr * 0.8, y + math.sin(ang) * rr * 0.8, x + math.cos(ang) * rr * 1.4,
             y + math.sin(ang) * rr * 1.4, color, 7 * (1 - k), 1 - k)
    glow(c, x, y, r * 1.2, color, 0.6 * (1 - k))


def lantern(c, x, y, s, t, col="#ff5a3c", txt=""):
    with xf(c, x, y + math.sin(t * 1.4 + x) * 4, s=s):
        glow(c, 0, 0, 140, col, 0.35)
        c.drawOval(skia.Rect(-40, -60, 40, 60), P(col))
        for k in range(-40, 50, 16):
            line(c, -38, k, 38, k, "#000000", 2, 0.25)
        rect(c, -26, -72, 52, 14, "#1a1a1a"); rect(c, -26, 58, 52, 14, "#1a1a1a")
        if txt: text(c, txt, 0, 16, 40, "#1a0a05", "jp")


def koi_wave(c, w, h, t, a=0.25, color=RED):
    """Irezumi-style wave bands."""
    for k in range(5):
        p = skia.Path(); y0 = h * (0.55 + k * 0.1)
        p.moveTo(0, h)
        for i in range(0, int(w) + 40, 40):
            p.lineTo(i, y0 + math.sin(i * 0.012 + t * 0.8 + k) * 30 + math.sin(i * 0.03 + k) * 10)
        p.lineTo(w, h); p.close()
        c.drawPath(p, P(mixhex(color, "#000000", 0.25 + k * 0.12), a=a))
        for i in range(0, int(w), 120):
            yy = y0 + math.sin(i * 0.012 + t * 0.8 + k) * 30
            c.drawCircle(i + 20, yy - 4, 14, P("#ffffff", 3, a * 0.5))


def sakura(c, w, h, t, n=26, a=0.8):
    r = rng(21)
    for i in range(n):
        x0 = r.uniform(0, w); y0 = r.uniform(0, h); sp = r.uniform(40, 90)
        x = (x0 + t * sp * 0.6 + math.sin(t + i) * 30) % w; y = (y0 + t * sp) % h
        with xf(c, x, y, rot=t * 60 + i * 30):
            c.drawOval(skia.Rect(-9, -5, 9, 5), P("#f7b6c8", a=a))
