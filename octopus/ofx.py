"""Underwater flat-vector style kit for the giant Pacific octopus video.

Style (matched to the reference whale explainers):
  * Deep teal ocean gradient, soft god-rays from the surface, drifting "marine snow".
  * Flat vector animals with one soft gradient each and a few texture spots, no outlines.
  * A small black-suited diver with a torch, used for scale and as "you".
  * All-caps, letter-spaced labels; white for facts, red for danger, amber for numbers.
  * Finish: vignette + light film grain on every frame.
"""
import math
import os
import random
import sys

import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from gfx import (W, H, C, P, xf, rrect, poly, line, text, text_width, linear, radial, fill_shader,  # noqa: E402,F401
                 glow, sparkle, check_mark, cross_mark, mixhex, font, clamp, lerp, smooth, ease_out,
                 back_out, at, window)

# ---------------------------------------------------------------- palette
SEA_TOP = "#1f5670"
SEA_MID = "#123b50"
SEA_BOT = "#071822"
DARK_TOP = "#0c2430"
DARK_BOT = "#02070a"
GREEN_TOP = "#123a35"
GREEN_BOT = "#020a08"
ROCK = "#163644"
ROCK2 = "#0f2833"
ROCK_HI = "#21495a"
OCTO = "#c4492f"
OCTO_DK = "#8b2a1d"
OCTO_LT = "#e8835c"
SUCKER = "#f3d0b0"
RED = "#ee3f36"
AMBER = "#f2a93b"
CYAN = "#7fd8ea"
WHITE = "#ffffff"
MUTED = "#9db7c4"


# ---------------------------------------------------------------- caching + post
_cache = {}


def cached(key, draw, blur=0.0, w=W, h=H, clear="#000000"):
    if key not in _cache:
        s = skia.Surface(w, h)
        cc = s.getCanvas()
        if clear:
            cc.clear(C(clear))
        else:
            cc.clear(skia.ColorTRANSPARENT)
        draw(cc)
        img = s.makeImageSnapshot()
        if blur:
            s2 = skia.Surface(w, h)
            s2.getCanvas().clear(skia.ColorTRANSPARENT)
            p = skia.Paint(ImageFilter=skia.ImageFilters.Blur(blur, blur, skia.TileMode.kClamp))
            s2.getCanvas().drawImage(img, 0, 0, skia.SamplingOptions(), p)
            img = s2.makeImageSnapshot()
        _cache[key] = img
    return _cache[key]


def blit(c, img, x=0, y=0, a=1.0):
    p = skia.Paint(AntiAlias=True)
    p.setAlphaf(clamp(a))
    c.drawImage(img, x, y, skia.SamplingOptions(skia.FilterMode.kLinear), p)


_grain = []


def grain(c, t, a=0.05):
    if not _grain:
        rnd = random.Random(5)
        for _ in range(4):
            s = skia.Surface(480, 270)
            cc = s.getCanvas()
            cc.clear(skia.ColorTRANSPARENT)
            for _ in range(4000):
                v = rnd.choice(("#ffffff", "#000000"))
                cc.drawRect(skia.Rect.MakeXYWH(rnd.uniform(0, 480), rnd.uniform(0, 270), 1, 1), P(v, a=0.9))
            _grain.append(s.makeImageSnapshot())
    p = skia.Paint()
    p.setAlphaf(a)
    c.drawImageRect(_grain[int(t * 24) % 4], skia.Rect(0, 0, W, H), skia.SamplingOptions(), p)


def vignette(c, a=0.55):
    img = cached(("vig", round(a, 2)), lambda cc: fill_shader(
        cc, skia.Rect(0, 0, W, H),
        radial(W / 2, H / 2, W * 0.75, [("#000000", 0), ("#000000", 0.0), ("#000000", a)], [0, 0.45, 1])),
        clear=None)
    blit(c, img)


def tint(c, color, a):
    if a > 0.001:
        c.drawRect(skia.Rect(0, 0, W, H), P(color, a=a))


# ---------------------------------------------------------------- text
def spaced(c, s, x, y, size, color=WHITE, weight="Black", align="center", a=1.0, sp=0.06, shadow=True):
    """Letter-spaced caps text (the reference's label look)."""
    f = font(size, weight)
    gap = size * sp
    widths = [f.measureText(ch) for ch in s]
    total = sum(widths) + gap * (len(s) - 1)
    if align == "center":
        x -= total / 2
    elif align == "right":
        x -= total
    if shadow:
        xx = x
        for ch, wd in zip(s, widths):
            c.drawString(ch, xx + size * 0.03, y + size * 0.05, f, P("#000000", a=0.45 * a))
            xx += wd + gap
    for ch, wd in zip(s, widths):
        c.drawString(ch, x, y, f, P(color, a=a))
        x += wd + gap
    return total


def spaced_w(s, size, weight="Black", sp=0.06):
    f = font(size, weight)
    return sum(f.measureText(ch) for ch in s) + size * sp * (len(s) - 1)


def pop_text(c, t, start, s, x, y, size, color=WHITE, dur=0.35, end=None, align="center", sp=0.05, weight="Black"):
    """Text that pops in with a small overshoot (and optionally fades out at `end`)."""
    if t < start:
        return
    k = back_out(at(t, start, dur))
    a = clamp((t - start) / 0.12)
    if end is not None:
        a *= clamp((end - t) / 0.25)
    if a <= 0:
        return
    with xf(c, x, y, s=lerp(0.85, 1.0, k)):
        spaced(c, s, 0, 0, size, color, weight, align, a, sp)


def label_box(c, x, y, s, size=30, fg="#0b1a22", bg=WHITE, a=1.0, pad=16):
    w = spaced_w(s, size, "ExtraBold", 0.05)
    rrect(c, x - w / 2 - pad, y - size * 0.95, w + 2 * pad, size * 1.35, 6, bg, a=a)
    spaced(c, s, x, y, size, fg, "ExtraBold", "center", a, 0.05, shadow=False)


def strike(c, x1, y, x2, prog, color=RED, w=6, a=1.0):
    if prog > 0:
        line(c, x1, y, lerp(x1, x2, clamp(prog)), y, color, w, a)


def corners(c, a=0.6, m=40, L=40, color=WHITE):
    """Camera viewfinder brackets (reference look)."""
    for (x, y, dx, dy) in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
        line(c, x, y, x + dx * L, y, color, 3, a)
        line(c, x, y, x, y + dy * L, color, 3, a)


def rec_overlay(c, t, label="REC", a=1.0):
    corners(c, 0.7 * a)
    if int(t * 2) % 2 == 0:
        c.drawCircle(84, 92, 9, P(RED, a=a))
    spaced(c, label, 104, 102, 26, WHITE, "Bold", "left", a, 0.08)
    ss = int(t * 30)
    tc = "00:%02d:%02d:%02d" % ((ss // 1800) % 60, (ss // 30) % 60, ss % 30)
    spaced(c, tc, W - 84, 102, 26, WHITE, "Bold", "right", a, 0.06)


def leader(c, x1, y1, x2, y2, s, prog=1.0, color=WHITE, size=26, a=1.0, align=None):
    """Label with a thin leader line and a dot (diagram callout)."""
    if prog <= 0:
        return
    k = ease_out(prog)
    c.drawCircle(x1, y1, 7 * k, P(color, a=a))
    line(c, x1, y1, lerp(x1, x2, k), lerp(y1, y2, k), color, 2.5, a)
    if prog > 0.5:
        al = align or ("left" if x2 >= x1 else "right")
        off = 14 if al == "left" else -14
        spaced(c, s, x2 + off, y2 + size * 0.35, size, color, "ExtraBold", al, a * clamp((prog - 0.5) * 2), 0.05)


def chapter(c, t, start, num, total, title, sub=None):
    """Chapter card: progress dots + big title (reference 'ESCAPE 6/6' look)."""
    k = ease_out(at(t, start, 0.5))
    a = clamp((t - start) / 0.2)
    x0, y0 = 150, 700
    spaced(c, title, x0, y0 + (1 - k) * 30, 110, WHITE, "Black", "left", a, 0.04)
    if sub:
        spaced(c, sub, x0 + 4, y0 + 56, 26, MUTED, "Bold", "left", a * clamp((t - start - 0.3) / 0.3), 0.12)
    for i in range(total):
        cx = x0 + 18 + i * 44
        cy = y0 + 112
        if i < num - 1:
            c.drawCircle(cx, cy, 13, P(MUTED, 2.5, a * 0.8))
            c.drawCircle(cx, cy, 5, P(MUTED, a=a * 0.8))
        elif i == num - 1:
            c.drawCircle(cx, cy, 15 * back_out(at(t, start + 0.2, 0.4)), P(AMBER, a=a))
        else:
            c.drawCircle(cx, cy, 13, P(MUTED, 2.5, a * 0.5))
    spaced(c, f"{num} / {total}", x0 + 18 + total * 44 + 10, y0 + 122, 28, WHITE, "ExtraBold", "left", a, 0.05)


# ---------------------------------------------------------------- environment
def blob_path(x, y, w, h, seed, n=11, rough=0.22, flat_bottom=False):
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1 + rnd.uniform(-rough, rough)
        px, py = x + math.cos(a) * w / 2 * r, y + math.sin(a) * h / 2 * r
        if flat_bottom and py > y:
            py = y + h * 0.5
        pts.append((px, py))
    p = skia.Path()
    mx = [((pts[i][0] + pts[(i + 1) % n][0]) / 2, (pts[i][1] + pts[(i + 1) % n][1]) / 2) for i in range(n)]
    p.moveTo(*mx[-1])
    for i in range(n):
        p.quadTo(pts[i][0], pts[i][1], mx[i][0], mx[i][1])
    p.close()
    return p


def rock(c, x, y, w, h, seed, col=ROCK, hi=ROCK_HI, a=1.0):
    path = blob_path(x, y, w, h, seed, flat_bottom=True)
    c.drawPath(path, skia.Paint(AntiAlias=True, Shader=linear(x, y - h / 2, x, y + h / 2, [hi, col]),
                                Alphaf=a))
    rnd = random.Random(seed + 99)
    c.save()
    c.clipPath(path, doAntiAlias=True)
    for _ in range(int(w * h / 9000) + 3):
        px, py = x + rnd.uniform(-w / 2, w / 2), y + rnd.uniform(-h / 2, h / 2)
        c.drawCircle(px, py, rnd.uniform(3, 12), P("#000000", a=0.12 * a))
    c.restore()


def ocean(c, t, top=SEA_TOP, bot=SEA_BOT, rays=1.0, snow=1.0, sway=1.0):
    img = cached(("sea", top, bot), lambda cc: fill_shader(
        cc, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, [top, mixhex(top, bot, 0.55), bot], [0, 0.45, 1])))
    blit(c, img)
    if rays > 0:
        god_rays(c, t, rays, sway)
    if snow > 0:
        marine_snow(c, t, snow)


_RAYS = [(random.Random(i).uniform(-200, W + 200), random.Random(i + 50).uniform(60, 200),
          random.Random(i + 9).uniform(0, 6.28)) for i in range(7)]


def god_rays(c, t, a=1.0, sway=1.0):
    for x0, wd, ph in _RAYS:
        dx = math.sin(t * 0.25 + ph) * 60 * sway
        k = 0.5 + 0.5 * math.sin(t * 0.4 + ph * 2)
        p = poly([(x0 + dx - wd / 2, -10), (x0 + dx + wd / 2, -10), (x0 + dx + 380 + wd * 1.3, H * 0.95),
                  (x0 + dx + 380 - wd * 1.3, H * 0.95)])
        c.drawPath(p, skia.Paint(AntiAlias=True, Shader=linear(0, 0, 0, H * 0.95, [("#bfeaf5", 0.10 * a * (0.5 + k)),
                                                                                   ("#bfeaf5", 0)])))


_SNOW = [(random.Random(i).uniform(0, W), random.Random(i + 1000).uniform(0, H), random.Random(i + 2000).uniform(1, 3.2),
          random.Random(i + 3000).uniform(0, 6.28)) for i in range(140)]


def marine_snow(c, t, a=1.0):
    for x0, y0, r, ph in _SNOW:
        x = (x0 + math.sin(t * 0.3 + ph) * 18 + t * 6) % W
        y = (y0 - t * (6 + r * 3)) % H
        c.drawCircle(x, y, r, P("#d8f1f7", a=0.22 * a * (r / 3.2)))


def bubbles(c, x, y, t, n=6, spread=14, rise=120, size=6, a=1.0, seed=0):
    for i in range(n):
        ph = (t * 0.9 + i / n + seed * 0.13) % 1.0
        bx = x + math.sin((ph * 6 + i) * 2.0) * spread * ph
        by = y - ph * rise
        r = size * (0.5 + 0.7 * ((i * 37) % 10) / 10) * (0.6 + ph * 0.6)
        c.drawCircle(bx, by, r, P("#e9fbff", 2, a * (1 - ph) * 0.9))


def kelp(c, x, y, h, t, seed=0, col="#1d4a3c", a=1.0, w=16):
    rnd = random.Random(seed)
    ph = rnd.uniform(0, 6.28)
    n = 18
    pts = []
    for i in range(n + 1):
        u = i / n
        dx = math.sin(t * 0.8 + ph + u * 3) * 40 * u ** 1.4
        pts.append((x + dx, y - h * u))
    p = skia.Path()
    p.moveTo(*pts[0])
    for px, py in pts[1:]:
        p.lineTo(px, py)
    c.drawPath(p, P(col, w, a))
    for i in range(2, n, 2):
        px, py = pts[i]
        s = 1 if i % 4 == 0 else -1
        leaf = skia.Path()
        leaf.moveTo(px, py)
        leaf.quadTo(px + s * 40, py - 30, px + s * 70 + math.sin(t + i) * 6, py - 10)
        leaf.quadTo(px + s * 30, py + 6, px, py)
        c.drawPath(leaf, P(col, a=a))


def reef(c, t, seed=1, y=H, a=1.0, back=True):
    """Rocky reef floor (cached) + swaying kelp."""
    def draw(cc):
        rnd = random.Random(seed)
        if back:
            for i in range(9):
                x = i * 240 + rnd.uniform(-60, 60)
                rock(cc, x, y - 120, rnd.uniform(300, 420), rnd.uniform(200, 280), seed * 100 + i, ROCK2, "#173c4b")
        for i in range(8):
            x = i * 280 + rnd.uniform(-60, 60)
            rock(cc, x, y - 40, rnd.uniform(320, 460), rnd.uniform(160, 240), seed * 200 + i)
    blit(c, cached(("reef", seed, y, back), draw, clear=None), a=a)
    for i, kx in enumerate((150, 610, 1180, 1700)):
        kelp(c, kx + seed * 37 % 90, y - 60, 330 + (i * 71) % 160, t, seed=i + seed, a=0.85 * a)


def ink_cloud(c, x, y, r, t, a=1.0, seed=3):
    rnd = random.Random(seed)
    for i in range(16):
        ang = rnd.uniform(0, 6.28)
        d = rnd.uniform(0, 0.75) * r
        rr = r * rnd.uniform(0.35, 0.65)
        px = x + math.cos(ang) * d + math.sin(t * 0.7 + i) * 10
        py = y + math.sin(ang) * d + math.cos(t * 0.6 + i) * 10
        fill_shader(c, skia.Rect(px - rr, py - rr, px + rr, py + rr),
                    radial(px, py, rr, [("#040608", 0.75 * a), ("#040608", 0.5 * a), ("#040608", 0)], [0, 0.5, 1]))


# ---------------------------------------------------------------- octopus
def _arm_center(x0, y0, a0, L, curl, tip, t, ph, amp, freq, n=46):
    pts = []
    x, y = x0, y0
    ds = L / n
    for i in range(n + 1):
        u = i / n
        ang = a0 + curl * u * u + tip * u ** 5 + amp * u * math.sin(2 * math.pi * (0.9 * u - freq * t) + ph)
        pts.append((x, y, ang))
        x += math.cos(ang) * ds
        y += math.sin(ang) * ds
    return pts


def draw_arm(c, x0, y0, a0, L, curl=0.0, tip=0.0, t=0.0, ph=0.0, amp=0.18, freq=0.25, w0=34, col=OCTO,
             under=1, suckers=True, a=1.0, ucol=None, scol=SUCKER, n=46):
    if L < 2:
        return [(x0, y0, a0)] * (n + 1)
    pts = _arm_center(x0, y0, a0, L, curl, tip, t, ph, amp, freq, n)
    left, right, mid = [], [], []
    for i, (x, y, ang) in enumerate(pts):
        u = i / n
        wd = w0 * (1 - u) ** 1.05 + 1.4
        nx, ny = -math.sin(ang), math.cos(ang)
        left.append((x + nx * wd, y + ny * wd))
        right.append((x - nx * wd, y - ny * wd))
        mid.append((x + nx * wd * 0.15 * under, y + ny * wd * 0.15 * under, wd, nx, ny))
    body = skia.Path()
    body.moveTo(*left[0])
    for p in left[1:]:
        body.lineTo(*p)
    tx, ty, _ = pts[-1]
    body.quadTo(tx + math.cos(pts[-1][2]) * 3, ty + math.sin(pts[-1][2]) * 3, *right[-1])
    for p in reversed(right[:-1]):
        body.lineTo(*p)
    body.close()
    c.drawPath(body, P(col, a=a))
    if ucol is None:
        ucol = mixhex(col, "#f6c3a0", 0.45)
    # underside strip
    side = left if under > 0 else right
    strip = skia.Path()
    strip.moveTo(mid[0][0], mid[0][1])
    for m in mid[1:]:
        strip.lineTo(m[0], m[1])
    for p in reversed(side):
        strip.lineTo(*p)
    strip.close()
    c.drawPath(strip, P(ucol, a=a))
    if suckers:
        u = 0.06
        while u < 0.93:
            i = int(u * n)
            x, y, ang = pts[i]
            wd = mid[i][2]
            nx, ny = mid[i][3], mid[i][4]
            r = wd * 0.36
            if r < 1.6:
                break
            sx, sy = x + nx * wd * 0.62 * under, y + ny * wd * 0.62 * under
            c.drawCircle(sx, sy, r, P(scol, a=a))
            c.drawCircle(sx, sy, r * 0.45, P(mixhex(scol, col, 0.55), a=a))
            u += max(0.012, (2.3 * r) / L)
    return pts


# arm presets: (base angle deg, length factor, curl, tip curl, under side, phase)
REST = [
    (205, 1.00, -0.9, -2.6, -1, 0.0), (180, 1.10, -0.4, -2.2, -1, 1.1), (150, 1.00, 0.2, -2.4, -1, 2.3),
    (118, 0.95, 0.5, -2.5, -1, 3.0), (80, 0.95, -0.4, 2.6, 1, 0.6), (50, 1.00, -0.2, 2.4, 1, 1.9),
    (20, 1.08, 0.3, 2.2, 1, 2.8), (-8, 1.00, 0.9, 2.6, 1, 4.0),
]
SPREAD = [(200 + i * 0, 1.0, 0, 0, 1, i) for i in range(8)]


def octopus(c, x, y, s=1.0, t=0.0, face=1, col=OCTO, a=1.0, arms=None, L=420, blink=0.0, look=(0, 0),
            mtilt=-32, eye_glow=0.0, amp=0.16, freq=0.22, camo=0.0, camo_col="#3d5a63", suckers=True,
            pupil=1.0, breathe=1.0, squash=1.0, hide_body=False, armw=34):
    """Giant Pacific octopus, side 3/4 view, facing right when face=1. (x, y) = head centre."""
    col = mixhex(col, camo_col, camo)
    dk = mixhex(mixhex(OCTO_DK, camo_col, camo), "#000000", 0.05)
    lt = mixhex(OCTO_LT, mixhex(camo_col, "#ffffff", 0.2), camo)
    arms = REST if arms is None else arms
    br = 1 + 0.035 * math.sin(t * 1.6) * breathe
    with xf(c, x, y, sx=s * face, sy=s * squash, alpha=a):
        base_y = 40
        # back arms (darker)
        order = sorted(range(len(arms)), key=lambda i: -abs(math.cos(math.radians(arms[i][0]))))
        back = [i for i in range(len(arms)) if i in (0, 2, 5, 7)]
        front = [i for i in range(len(arms)) if i not in back]
        _ = order

        def one(i, shade):
            spec = arms[i]
            ad, lf, cu, tp, und, ph = spec[:6]
            ang = math.radians(ad)
            bx, by = math.cos(ang) * 46, base_y + math.sin(ang) * 22
            draw_arm(c, bx, by, ang, L * lf, cu, tp, t, ph, amp, freq, armw, shade, und, suckers, 1.0,
                     scol=mixhex(SUCKER, camo_col, camo * 0.7))
        for i in back:
            one(i, mixhex(col, "#000000", 0.25))
        # skirt / web
        c.drawOval(skia.Rect(-95, base_y - 40, 95, base_y + 45), P(mixhex(col, "#000000", 0.12)))
        if not hide_body:
            # mantle
            with xf(c, -70, -70, rot=mtilt):
                mp = skia.Rect(-175 * br, -112 * br, 120, 112 * br)
                c.drawOval(mp, skia.Paint(AntiAlias=True, Shader=radial(-40, -60, 230, [lt, col, dk], [0, 0.45, 1])))
                rnd = random.Random(7)
                for _ in range(26):
                    px, py = rnd.uniform(-150, 90), rnd.uniform(-90, 90)
                    if (px / 165) ** 2 + (py / 105) ** 2 < 0.8:
                        c.drawCircle(px, py, rnd.uniform(4, 11), P(dk, a=0.55))
                for _ in range(14):
                    px, py = rnd.uniform(-140, 80), rnd.uniform(-85, 20)
                    if (px / 165) ** 2 + (py / 105) ** 2 < 0.75:
                        c.drawCircle(px, py, rnd.uniform(2, 5), P(lt, a=0.7))
                # wrinkle lines
                for k in range(3):
                    pth = skia.Path()
                    pth.moveTo(60 - k * 30, -80 + k * 10)
                    pth.quadTo(90 - k * 30, 0, 50 - k * 30, 80 - k * 10)
                    c.drawPath(pth, P(dk, 3, 0.35))
            # head
            c.drawOval(skia.Rect(-92, -78, 98, 72), skia.Paint(AntiAlias=True, Shader=radial(10, -40, 140, [lt, col, dk],
                                                                                            [0, 0.5, 1])))
            rnd = random.Random(3)
            for _ in range(10):
                px, py = rnd.uniform(-70, 70), rnd.uniform(-55, 50)
                c.drawCircle(px, py, rnd.uniform(3, 7), P(dk, a=0.45))
            # eyes
            for ex, ey, er, main in ((-38, -54, 17, False), (36, -38, 27, True)):
                c.drawCircle(ex, ey - 4, er * 1.45, P(lt, a=0.85))
                c.drawCircle(ex, ey, er, P("#efd9a0"))
                if eye_glow:
                    glow(c, ex, ey, er * 3.5, "#ffe9a8", 0.5 * eye_glow)
                lx, ly = look
                ph_ = er * 0.30 * pupil
                rrect(c, ex - er * 0.62 + lx * er * 0.25, ey - ph_ / 2 + ly * er * 0.2, er * 1.24, ph_, ph_ / 2,
                      "#0c0d10")
                c.drawCircle(ex - er * 0.35, ey - er * 0.42, er * 0.17, P(WHITE, a=0.8))
                if blink > 0:
                    lid = skia.Path()
                    lid.addOval(skia.Rect(ex - er * 1.1, ey - er * 1.1, ex + er * 1.1, ey - er * 1.1 + er * 2.2 * blink))
                    c.drawPath(lid, P(col))
                    c.drawCircle(ex, ey - 4, er * 1.45, P(dk, 2.5, 0.6))
                if main:
                    # horn-like papilla above eye
                    pth = poly([(ex - 10, ey - er * 1.3), (ex + 2, ey - er * 2.1), (ex + 12, ey - er * 1.25)])
                    c.drawPath(pth, P(lt))
        # front arms
        for i in front:
            one(i, col)


def octopus_spread(c, x, y, s=1.0, t=0.0, col=OCTO, a=1.0, L=430, amp=0.12, reach=1.0):
    """Top-down 'star' pose used for size measurements."""
    with xf(c, x, y, s=s, alpha=a):
        for i in range(8):
            ang = math.radians(-90 + 22.5 + i * 45)
            draw_arm(c, math.cos(ang) * 50, math.sin(ang) * 50, ang, L * reach, 0.0, 2.2 * (1 if i % 2 else -1), t, i,
                     amp, 0.2, 36, col, 1 if i % 2 else -1, True)
        c.drawCircle(0, 0, 80, P(mixhex(col, "#000000", 0.1)))
        c.drawOval(skia.Rect(-70, -170, 70, 40), skia.Paint(AntiAlias=True, Shader=radial(-10, -90, 150,
                                                                                         [OCTO_LT, col, OCTO_DK])))
        for ex in (-48, 48):
            c.drawCircle(ex, 10, 20, P(OCTO_LT))
            c.drawCircle(ex, 10, 14, P("#efd9a0"))
            rrect(c, ex - 9, 7, 18, 5, 2.5, "#0c0d10")


def lone_arm(c, x0, y0, a0, L, t, curl=0.0, tip=2.4, w0=40, col=OCTO, under=1, a=1.0, amp=0.15, freq=0.3, ph=0.0):
    with xf(c, 0, 0, alpha=a):
        return draw_arm(c, x0, y0, a0, L, curl, tip, t, ph, amp, freq, w0, col, under, True)


def reach_arm(c, x0, y0, x1, y1, t, w0=40, col=OCTO, prog=1.0, under=1, curl_tip=2.6, a=1.0, ph=0.0, amp=0.08):
    """An arm from (x0,y0) toward (x1,y1); prog 0..1 extends it."""
    d = math.hypot(x1 - x0, y1 - y0)
    ang = math.atan2(y1 - y0, x1 - x0)
    L = max(10, d * 1.08 * ease_out(prog))
    return lone_arm(c, x0, y0, ang + 0.35 * under * -1, L, t, curl=0.7 * under, tip=curl_tip * under, w0=w0,
                    col=col, under=under, a=a, amp=amp, ph=ph)


def eye_closeup(c, x, y, r, t, blink=0.0, look=(0, 0), col=OCTO, pupil=1.0, a=1.0):
    """Huge octopus eye filling part of the frame."""
    with xf(c, x, y, alpha=a):
        c.drawCircle(0, 0, r * 1.6, skia.Paint(AntiAlias=True, Shader=radial(-r * 0.4, -r * 0.6, r * 2.2,
                                                                          [OCTO_LT, col, OCTO_DK])))
        rnd = random.Random(2)
        for _ in range(30):
            ang, d = rnd.uniform(0, 6.28), rnd.uniform(r * 1.15, r * 1.6)
            c.drawCircle(math.cos(ang) * d, math.sin(ang) * d, rnd.uniform(r * 0.03, r * 0.08), P(OCTO_DK, a=0.6))
        c.drawCircle(0, 0, r, skia.Paint(AntiAlias=True, Shader=radial(0, 0, r, ["#f6e6b5", "#d9b46a"])))
        for i in range(36):
            ang = i * 10 * math.pi / 180
            line(c, math.cos(ang) * r * 0.5, math.sin(ang) * r * 0.5, math.cos(ang) * r * 0.95,
                 math.sin(ang) * r * 0.95, "#b98d4b", 2, 0.5)
        ph = r * 0.32 * pupil
        lx, ly = look
        rrect(c, -r * 0.72 + lx * r * 0.2, -ph / 2 + ly * r * 0.15, r * 1.44, ph, ph / 2, "#08090b")
        c.drawCircle(-r * 0.4, -r * 0.45, r * 0.12, P(WHITE, a=0.85))
        if blink > 0:
            c.save()
            cp = skia.Path()
            cp.addCircle(0, 0, r * 1.05)
            c.clipPath(cp, doAntiAlias=True)
            c.drawRect(skia.Rect(-r * 1.2, -r * 1.2, r * 1.2, -r * 1.2 + r * 2.4 * blink), P(col))
            c.restore()


# ---------------------------------------------------------------- diver
def diver(c, x, y, s=1.0, t=0.0, face=1, a=1.0, torch=True, beam=1.0, kick=1.0, accent="#e8513a", rot=0.0,
          bubbles_on=True, fin="#f2b632", tired=0.0, arm_up=0.0, pose="swim", suit="#16191d", tank="#cdd5da",
          mask="#5fc6dc"):
    """Side-view scuba diver, horizontal, facing right when face=1. (x,y) = torso centre."""
    with xf(c, x, y, rot=rot, sx=s * face, sy=s, alpha=a):
        k = math.sin(t * (5 - 3 * tired)) * kick
        # far leg
        _leg(c, -78, 6, 186 + 12 * k, 180 - 10 * k, suit, mixhex(fin, "#000000", 0.25))
        # tank
        rrect(c, -70, -58, 132, 36, 18, tank)
        rrect(c, -70, -58, 132, 12, 6, WHITE, a=0.35)
        rrect(c, 58, -50, 14, 20, 4, "#6c7378")
        # torso
        rrect(c, -86, -28, 160, 54, 26, suit)
        rrect(c, -70, -6, 120, 8, 4, accent)
        # near leg
        _leg(c, -78, 10, 174 - 12 * k, 182 + 10 * k, suit, fin)
        # head
        c.drawCircle(92, -6, 26, P(suit))
        rrect(c, 98, -20, 26, 20, 7, mask)
        rrect(c, 104, -17, 9, 7, 3, WHITE, a=0.6)
        line(c, 80, -14, 100, -14, "#2b3036", 5)
        c.drawCircle(114, 12, 7, P("#2b3036"))
        # arm with torch
        if pose == "swim":
            sx_, sy_ = 56, 0
            hx, hy = 128, 18 - arm_up * 60
            line(c, sx_, sy_, hx, hy, suit, 18)
            ta = math.atan2(hy - sy_, hx - sx_)
            if torch:
                with xf(c, hx, hy, rot=math.degrees(ta)):
                    rrect(c, -6, -9, 40, 18, 5, "#3a4147")
                    rrect(c, 32, -11, 8, 22, 3, "#9aa3a8")
                    if beam > 0:
                        bp_ = poly([(40, -9), (40, 9), (520, 150), (520, -150)])
                        c.drawPath(bp_, skia.Paint(AntiAlias=True, Shader=linear(40, 0, 520, 0, [("#fff7d6", 0.42 * beam),
                                                                                                ("#fff7d6", 0)])))
                        glow(c, 42, 0, 40, "#fff7d6", 0.7 * beam)
        elif pose == "still":
            line(c, 56, 0, 70, 40, suit, 18)
    if bubbles_on:
        bx = x + face * 116 * s * math.cos(math.radians(rot))
        by = y - 6 * s
        bubbles(c, bx, by, t, n=7, spread=10 * s, rise=150 * s, size=7 * s, a=a)


def _leg(c, hx, hy, a1, a2, suit, fin):
    l1, l2 = 70, 64
    r1, r2 = math.radians(a1), math.radians(a2)
    kx, ky = hx + math.cos(r1) * l1, hy + math.sin(r1) * l1
    ax, ay = kx + math.cos(r2) * l2, ky + math.sin(r2) * l2
    line(c, hx, hy, kx, ky, suit, 24)
    line(c, kx, ky, ax, ay, suit, 20)
    with xf(c, ax, ay, rot=math.degrees(r2)):
        p = poly([(-6, -10), (90, -22), (96, 18), (-6, 10)])
        c.drawPath(p, P(fin))


# ---------------------------------------------------------------- other animals / props
def fish(c, x, y, s=1.0, t=0.0, face=1, col="#9fb7c0", a=1.0):
    with xf(c, x, y, sx=s * face, sy=s, alpha=a):
        w = math.sin(t * 8) * 8
        c.drawPath(poly([(-50, 0), (-80, -22 + w), (-80, 22 + w)]), P(col))
        c.drawOval(skia.Rect(-60, -24, 60, 24), P(col))
        c.drawOval(skia.Rect(-40, -2, 50, 22), P(mixhex(col, WHITE, 0.4), a=0.6))
        c.drawCircle(36, -6, 6, P("#0b1014"))


def shark(c, x, y, s=1.0, t=0.0, face=1, col="#7f96a3", belly="#dfe6ea", a=1.0, kind="white"):
    """Flat side-view shark. kind='white' (great white) or 'dogfish' (slim, spotted)."""
    with xf(c, x, y, sx=s * face, sy=s, alpha=a):
        w = math.sin(t * 3) * 10
        slim = 0.6 if kind == "dogfish" else 1.0
        body = skia.Path()
        body.moveTo(230, 10)
        body.cubicTo(200, -60 * slim, 40, -75 * slim, -120, -30 * slim)
        body.cubicTo(-180, -15, -230, -8 + w * 0.3, -250, 0 + w * 0.5)
        body.cubicTo(-230, 10, -180, 25, -120, 35 * slim)
        body.cubicTo(20, 70 * slim, 190, 55 * slim, 230, 10)
        body.close()
        c.drawPath(poly([(-235, w * 0.5), (-320, -80 + w), (-290, w * 0.6), (-310, 60 + w)]), P(col))
        c.drawPath(poly([(10, -55 * slim), (-30, -150 * slim), (-70, -48 * slim)]), P(col))
        c.drawPath(poly([(40, 45 * slim), (-20, 110 * slim), (-50, 40 * slim)]), P(mixhex(col, "#000000", 0.2)))
        c.drawPath(body, P(col))
        c.save()
        c.clipPath(body, doAntiAlias=True)
        c.drawRect(skia.Rect(-260, 18 * slim, 240, 100), P(belly))
        if kind == "dogfish":
            rnd = random.Random(1)
            for _ in range(14):
                c.drawCircle(rnd.uniform(-200, 180), rnd.uniform(-40, 10), rnd.uniform(3, 6), P(WHITE, a=0.7))
        c.restore()
        c.drawCircle(160, -8 * slim, 7, P("#0b0d10"))
        for i in range(4):
            line(c, 95 - i * 12, -14 * slim, 90 - i * 12, 14 * slim, "#000000", 3, 0.35)


def orca(c, x, y, s=1.0, t=0.0, face=1, a=1.0):
    with xf(c, x, y, sx=s * face, sy=s, alpha=a):
        w = math.sin(t * 2.5) * 10
        body = skia.Path()
        body.moveTo(240, 20)
        body.cubicTo(220, -70, 40, -85, -140, -30)
        body.cubicTo(-200, -12, -240, 0, -255, w * 0.5)
        body.cubicTo(-220, 22, -150, 40, -100, 45)
        body.cubicTo(40, 80, 200, 70, 240, 20)
        body.close()
        c.drawPath(poly([(-240, w * 0.5), (-330, -50 + w), (-300, w * 0.6), (-330, 55 + w)]), P("#101316"))
        c.drawPath(poly([(10, -62), (-25, -210), (-70, -48)]), P("#101316"))
        c.drawPath(body, P("#101316"))
        c.save()
        c.clipPath(body, doAntiAlias=True)
        c.drawOval(skia.Rect(-60, 25, 260, 120), P("#f0f3f5"))
        c.drawOval(skia.Rect(120, -45, 190, -15), P("#f0f3f5"))
        c.restore()
        c.drawPath(poly([(60, 50), (20, 130), (-20, 45)]), P("#101316"))


def crab(c, x, y, s=1.0, t=0.0, col="#d0623a", a=1.0, wiggle=1.0):
    with xf(c, x, y, s=s, alpha=a):
        for sd in (-1, 1):
            for i in range(3):
                k = math.sin(t * 6 + i + sd) * 6 * wiggle
                line(c, sd * 30, 8 + i * 10, sd * (70 + i * 6), 30 + i * 12 + k, col, 7)
            line(c, sd * 34, -6, sd * 66, -40, col, 9)
            c.drawOval(skia.Rect(sd * 66 - 20, -66, sd * 66 + 20, -34), P(col))
            c.drawPath(poly([(sd * 66, -58), (sd * 90, -78), (sd * 76, -46)]), P(col))
        c.drawOval(skia.Rect(-52, -26, 52, 32), P(col))
        c.drawOval(skia.Rect(-40, -24, 40, 4), P(WHITE, a=0.15))
        for sd in (-1, 1):
            line(c, sd * 14, -22, sd * 18, -42, col, 4)
            c.drawCircle(sd * 18, -44, 6, P("#101214"))


def clam(c, x, y, s=1.0, a=1.0, col="#d9cbb2", open_=0.0):
    with xf(c, x, y, s=s, alpha=a):
        p = skia.Path()
        p.moveTo(-50, 0)
        p.cubicTo(-50, -60, 50, -60, 50, 0)
        p.close()
        with xf(c, -50, 0, rot=-25 * open_):
            with xf(c, 50, 0):
                c.drawPath(p, P(col))
                for i in range(-3, 4):
                    line(c, 0, 0, i * 13, -40, mixhex(col, "#000000", 0.25), 2.5)
        p2 = skia.Path()
        p2.moveTo(-50, 0)
        p2.cubicTo(-50, 30, 50, 30, 50, 0)
        p2.close()
        c.drawPath(p2, P(mixhex(col, "#000000", 0.15)))


def snail(c, x, y, s=1.0, a=1.0, col="#b98a5a"):
    with xf(c, x, y, s=s, alpha=a):
        rrect(c, -55, 10, 110, 22, 11, "#c9b29a")
        c.drawCircle(-4, -14, 40, P(col))
        p = skia.Path()
        for i in range(60):
            ang = i * 0.28
            r = 36 * (1 - i / 64)
            px, py = -4 + math.cos(ang) * r, -14 + math.sin(ang) * r
            p.moveTo(px, py) if i == 0 else p.lineTo(px, py)
        c.drawPath(p, P(mixhex(col, "#000000", 0.35), 4))
        line(c, 46, 12, 60, -14, "#c9b29a", 5)


def lobster(c, x, y, s=1.0, a=1.0, col="#b9442e", t=0.0):
    with xf(c, x, y, s=s, alpha=a):
        for i in range(5):
            c.drawOval(skia.Rect(-60 - i * 26, -18 + i * 2, -14 - i * 26, 18 - i * 2), P(mixhex(col, "#000000", i * 0.04)))
        c.drawPath(poly([(-180, 0), (-215, -26), (-222, 26)]), P(col))
        c.drawOval(skia.Rect(-30, -26, 70, 26), P(col))
        for sd in (-1, 1):
            line(c, 50, sd * 14, 110, sd * 50, col, 10)
            c.drawOval(skia.Rect(100, sd * 50 - 18, 170, sd * 50 + 18), P(col))
            line(c, 64, sd * 6, 200, sd * 70 + math.sin(t * 2 + sd) * 10, col, 3)
        c.drawCircle(62, -10, 5, P("#101214"))


def shell_pile(c, x, y, n, s=1.0, seed=4, a=1.0):
    rnd = random.Random(seed)
    for i in range(n):
        px = x + rnd.gauss(0, 120) * s
        py = y - abs(rnd.gauss(0, 30)) * s - (i / max(n, 1)) * 40 * s
        kind = rnd.random()
        sc = s * rnd.uniform(0.35, 0.55)
        if kind < 0.45:
            clam(c, px, py, sc, a, col=rnd.choice(("#d9cbb2", "#cdbf9f", "#e5dccb")), open_=rnd.uniform(0.6, 1.0))
        elif kind < 0.8:
            with xf(c, px, py, rot=rnd.uniform(-40, 40)):
                crab_claw(c, 0, 0, sc * 1.2, a)
        else:
            snail(c, px, py, sc, a)


def crab_claw(c, x, y, s=1.0, a=1.0, col="#d0623a"):
    with xf(c, x, y, s=s, alpha=a):
        c.drawOval(skia.Rect(-40, -22, 40, 22), P(col))
        c.drawPath(poly([(30, -14), (80, -30), (60, -2)]), P(col))
        c.drawPath(poly([(30, 10), (76, 22), (50, 0)]), P(mixhex(col, "#000000", 0.2)))
        line(c, -40, 0, -80, 6, col, 10)


def coin(c, x, y, r, a=1.0):
    c.drawCircle(x, y, r, P("#d9a441", a=a))
    c.drawCircle(x, y, r * 0.82, P("#f1c35a", a=a))
    c.drawCircle(x, y, r * 0.82, P("#b4832c", 3, a))
    text(c, "1", x, y + r * 0.35, r, "#b4832c", a=a)


def beak(c, x, y, s=1.0, a=1.0, col="#1d1712"):
    with xf(c, x, y, s=s, alpha=a):
        p = skia.Path()
        p.moveTo(-40, -30)
        p.cubicTo(10, -60, 60, -30, 50, 20)
        p.quadTo(30, -5, 0, 0)
        p.quadTo(-30, 0, -40, -30)
        c.drawPath(p, P(col))
        p2 = skia.Path()
        p2.moveTo(-40, 10)
        p2.cubicTo(0, 50, 50, 50, 46, 30)
        p2.quadTo(20, 18, -40, 10)
        c.drawPath(p2, P(mixhex(col, "#ffffff", 0.12)))
        c.drawCircle(-20, -30, 6, P(WHITE, a=0.25))


def heart(c, x, y, r, col=RED, a=1.0):
    p = skia.Path()
    p.moveTo(x, y + r * 0.9)
    p.cubicTo(x - r * 1.6, y - r * 0.2, x - r * 0.7, y - r * 1.4, x, y - r * 0.5)
    p.cubicTo(x + r * 0.7, y - r * 1.4, x + r * 1.6, y - r * 0.2, x, y + r * 0.9)
    c.drawPath(p, P(col, a=a))


def blood_drop(c, x, y, r, col="#3a7bff", a=1.0):
    from gfx import drop
    drop(c, x, y, r, col, a)


def thermometer(c, x, y, h, level, col="#5bc6ff", a=1.0):
    rrect(c, x - 16, y - h, 32, h, 16, "#e8eef1", a=a)
    rrect(c, x - 8, y - h * level, 16, h * level, 8, col, a=a)
    c.drawCircle(x, y + 10, 28, P("#e8eef1", a=a))
    c.drawCircle(x, y + 10, 20, P(col, a=a))


def lamp(c, x, y, s=1.0, on=1.0, t=0.0, a=1.0):
    with xf(c, x, y, s=s, alpha=a):
        line(c, 0, -400, 0, -60, "#2a2f33", 6)
        c.drawPath(poly([(-90, 0), (90, 0), (40, -70), (-40, -70)]), P("#3a4248"))
        if on > 0:
            c.drawPath(poly([(-90, 0), (90, 0), (300, 600), (-300, 600)]),
                       skia.Paint(AntiAlias=True, Shader=linear(0, 0, 0, 600, [("#fff3c4", 0.35 * on), ("#fff3c4", 0)])))
            glow(c, 0, 6, 130, "#fff3c4", 0.8 * on)
        c.drawOval(skia.Rect(-40, -14, 40, 18), P("#fff3c4" if on > 0.5 else "#6b6550"))


def jar(c, x, y, s=1.0, a=1.0, lid_rot=0.0, lid_off=0.0):
    with xf(c, x, y, s=s, alpha=a):
        rrect(c, -110, -150, 220, 290, 40, "#bfe6ee", a=0.18)
        rrect(c, -110, -150, 220, 290, 40, "#d9f3f8", a=0.6) if False else None
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-110, -150, 110, 140), 40, 40), P("#d9f3f8", 4, 0.8))
        line(c, -80, -110, -80, 90, WHITE, 8, 0.35)
        with xf(c, 0, -165 - lid_off, rot=lid_rot):
            rrect(c, -95, -22, 190, 40, 8, "#c94a3a")
            for i in range(9):
                line(c, -85 + i * 21, -18, -85 + i * 21, 14, "#9b3327", 3)


def person_icon(c, x, y, s=1.0, col=WHITE, a=1.0):
    with xf(c, x, y, s=s, alpha=a):
        c.drawCircle(0, -60, 30, P(col))
        p = skia.Path()
        p.moveTo(-55, 40)
        p.cubicTo(-55, -30, 55, -30, 55, 40)
        p.close()
        c.drawPath(p, P(col))


def dog_icon(c, x, y, s=1.0, col=WHITE, a=1.0):
    with xf(c, x, y, s=s, alpha=a):
        rrect(c, -110, -50, 200, 80, 38, col)
        for lx in (-90, -55, 40, 72):
            rrect(c, lx, 10, 22, 80, 10, col)
        c.drawCircle(110, -70, 46, P(col))
        rrect(c, 130, -78, 60, 36, 16, col)
        c.drawPath(poly([(84, -110), (96, -150), (118, -112)]), P(col))
        line(c, -110, -30, -160, -80, col, 16)


def ship(c, x, y, s=1.0, rot=0.0, a=1.0, col="#5a3d2a"):
    with xf(c, x, y, s=s, rot=rot, alpha=a):
        hull = skia.Path()
        hull.moveTo(-220, -20)
        hull.lineTo(230, -20)
        hull.lineTo(180, 60)
        hull.lineTo(-180, 60)
        hull.close()
        c.drawPath(hull, P(col))
        line(c, -200, 0, 210, 0, "#e9d8b0", 4)
        for mx, mh in ((-90, 300), (30, 360), (140, 260)):
            line(c, mx, -20, mx, -20 - mh, "#3a2a1e", 8)
            for k in range(3):
                yy = -40 - mh + 40 + k * mh * 0.3
                ww = 70 - k * 4
                p = skia.Path()
                p.moveTo(mx - ww, yy)
                p.quadTo(mx, yy - 14, mx + ww, yy)
                p.lineTo(mx + ww - 6, yy + mh * 0.24)
                p.quadTo(mx, yy + mh * 0.24 + 16, mx - ww + 6, yy + mh * 0.24)
                p.close()
                c.drawPath(p, P("#efe6cf"))


def squid(c, x, y, s=1.0, t=0.0, a=1.0, col="#d88a6a"):
    with xf(c, x, y, s=s, alpha=a):
        for i in range(8):
            ang = math.radians(180 + (i - 3.5) * 6)
            draw_arm(c, -90, (i - 3.5) * 6, ang, 260 + (i % 3) * 30, 0, 0.6 * (1 if i % 2 else -1), t, i, 0.2, 0.3, 14,
                     mixhex(col, "#000000", 0.15), 1, False)
        for sd in (-1, 1):
            draw_arm(c, -90, 0, math.radians(180 + sd * 4), 520, 0, sd * 1.5, t, sd, 0.15, 0.25, 8, col, 1, False)
        body = skia.Path()
        body.moveTo(-90, -40)
        body.cubicTo(60, -60, 260, -30, 330, 0)
        body.cubicTo(260, 30, 60, 60, -90, 40)
        body.close()
        c.drawPath(body, P(col))
        c.drawPath(poly([(250, 0), (340, -70), (360, 0), (340, 70)]), P(col))
        c.drawCircle(-60, 0, 26, P("#f1e6c8"))
        c.drawCircle(-60, 0, 14, P("#0c0d10"))


def egg_strands(c, x, y, n=7, L=180, t=0.0, a=1.0, hatch=0.0, seed=1):
    rnd = random.Random(seed)
    for i in range(n):
        sx = x + (i - n / 2) * 34
        sway = math.sin(t * 0.8 + i) * 6
        line(c, sx, y, sx + sway, y + L, "#e9e0c6", 3, a * 0.8)
        for k in range(14):
            u = k / 14
            px = sx + sway * u + rnd.uniform(-9, 9)
            py = y + 10 + u * L
            if hatch > 0 and rnd.random() < hatch:
                continue
            c.drawOval(skia.Rect(px - 6, py - 9, px + 6, py + 9), P("#f3ecd6", a=a))
            c.drawCircle(px, py + 2, 2.2, P("#3b3326", a=a * 0.7))


def paralarva(c, x, y, s=1.0, t=0.0, a=1.0):
    with xf(c, x, y, s=s, alpha=a):
        for i in range(8):
            ang = math.radians(60 + i * 8)
            k = math.sin(t * 5 + i) * 6
            line(c, 0, 8, math.cos(ang) * 22 + k, 8 + math.sin(ang) * 26, "#f0b49a", 2.5, 0.9)
        c.drawOval(skia.Rect(-9, -14, 9, 12), P("#f6c4ad", a=0.9))
        c.drawCircle(-4, 4, 2.5, P("#111111"))
        c.drawCircle(4, 4, 2.5, P("#111111"))


def otter(c, x, y, s=1.0, a=1.0, col="#6b4a32"):
    with xf(c, x, y, s=s, alpha=a):
        rrect(c, -140, -32, 240, 64, 32, col)
        c.drawCircle(110, -10, 44, P(col))
        c.drawCircle(124, -4, 30, P("#c9ab8a"))
        c.drawCircle(136, -18, 5, P("#111111"))
        c.drawCircle(150, -6, 6, P("#111111"))
        c.drawCircle(84, -46, 10, P(col))
        line(c, -140, 0, -200, 10, col, 18)


def seal(c, x, y, s=1.0, a=1.0, col="#7d8a91", t=0.0):
    with xf(c, x, y, s=s, alpha=a):
        body = skia.Path()
        body.moveTo(200, -10)
        body.cubicTo(180, -70, 0, -70, -140, -20)
        body.lineTo(-200, -30 + math.sin(t * 3) * 8)
        body.lineTo(-190, 10)
        body.cubicTo(0, 60, 180, 40, 200, -10)
        body.close()
        c.drawPath(body, P(col))
        c.drawCircle(150, -36, 6, P("#101214"))
        c.drawPath(poly([(40, 20), (0, 70), (-20, 20)]), P(mixhex(col, "#000000", 0.2)))


def shrimp(c, x, y, s=1.0, a=1.0, col="#f08a6a"):
    with xf(c, x, y, s=s, alpha=a):
        for i in range(6):
            c.drawCircle(-i * 14, math.sin(i * 0.6) * 10 - i * 2, 16 - i * 1.6, P(mixhex(col, "#000000", i * 0.03)))
        line(c, 10, -6, 70, -40, col, 2)
        line(c, 10, -2, 70, -20, col, 2)
        c.drawCircle(10, -8, 3, P("#111111"))


def fly(c, x, y, s=1.0, t=0.0, a=1.0):
    with xf(c, x, y, s=s, alpha=a):
        flap = abs(math.sin(t * 40))
        c.drawOval(skia.Rect(-30, -50 * flap - 10, 10, 0), P("#d8eef5", a=0.6))
        c.drawOval(skia.Rect(-10, -50 * flap - 10, 30, 0), P("#d8eef5", a=0.6))
        c.drawOval(skia.Rect(-26, -10, 26, 16), P("#24282b"))
        c.drawCircle(24, 0, 12, P("#3a1f1f"))


def trap(c, x, y, s=1.0, a=1.0):
    with xf(c, x, y, s=s, alpha=a):
        rrect(c, -120, -90, 240, 180, 14, "#c9b057", stroke=6)
        for i in range(1, 8):
            line(c, -120 + i * 30, -90, -120 + i * 30, 90, "#c9b057", 2.5, 0.8)
        for i in range(1, 6):
            line(c, -120, -90 + i * 30, 120, -90 + i * 30, "#c9b057", 2.5, 0.8)
        line(c, 0, -90, 0, -400, "#e2d7b8", 3)


def net(c, x, y, w, h, a=1.0, col="#d8cfae"):
    for i in range(int(w / 26) + 1):
        line(c, x + i * 26, y, x + i * 26 + 20, y + h, col, 2, a * 0.7)
        line(c, x + i * 26 + 20, y, x + i * 26, y + h, col, 2, a * 0.7)


def stopwatch(c, x, y, r, frac, col=AMBER, a=1.0, label=None):
    c.drawCircle(x, y, r, P("#0b1a22", a=a * 0.8))
    c.drawCircle(x, y, r, P("#5b7480", 6, a))
    rect = skia.Rect(x - r, y - r, x + r, y + r)
    pth = skia.Path()
    pth.addArc(rect, -90, 360 * clamp(frac))
    c.drawPath(pth, P(col, 8, a))
    rrect(c, x - 14, y - r - 26, 28, 18, 4, "#5b7480", a=a)
    ang = math.radians(-90 + 360 * frac)
    line(c, x, y, x + math.cos(ang) * r * 0.7, y + math.sin(ang) * r * 0.7, WHITE, 5, a)
    if label:
        spaced(c, label, x, y + r + 50, 30, WHITE, "ExtraBold", "center", a)


def receipt(c, x, y, rows, prog, t, a=1.0, title="RECEIPT"):
    """Paper receipt that prints downward (prog 0..1)."""
    w = 380
    full = 110 + len(rows) * 46 + 90
    h = full * ease_out(prog)
    with xf(c, x, y, alpha=a):
        c.save()
        c.clipRect(skia.Rect(-w / 2 - 10, 0, w / 2 + 10, h + 4))
        p = skia.Path()
        p.moveTo(-w / 2, 0)
        p.lineTo(w / 2, 0)
        p.lineTo(w / 2, full)
        for i in range(19):
            p.lineTo(w / 2 - (i + 0.5) * w / 19, full + (12 if i % 2 == 0 else 0))
        p.lineTo(-w / 2, full)
        p.close()
        c.drawPath(p, P("#f3efe4"))
        text(c, title, 0, 60, 36, "#1c1c1c", "Black")
        line(c, -w / 2 + 24, 84, w / 2 - 24, 84, "#1c1c1c", 2, 0.5)
        for i, (k, v) in enumerate(rows):
            yy = 128 + i * 46
            text(c, k, -w / 2 + 28, yy, 26, "#2a2a2a", "Bold", "left")
            text(c, v, w / 2 - 28, yy, 26, "#2a2a2a", "Bold", "right")
        yy = 128 + len(rows) * 46
        line(c, -w / 2 + 24, yy - 16, w / 2 - 24, yy - 16, "#1c1c1c", 2, 0.5)
        text(c, "THANK YOU, COME AGAIN", 0, yy + 30, 22, "#2a2a2a", "ExtraBold")
        c.restore()


def card_frame(c, x, y, w, h, rot=0.0, a=1.0, paper="#efe6cf"):
    """Photo/postcard frame with drop shadow, returns nothing; draw content inside afterwards (local coords)."""
    with xf(c, x, y, rot=rot, alpha=a):
        rrect(c, -w / 2 + 10, -h / 2 + 14, w, h, 6, "#000000", a=0.35)
        rrect(c, -w / 2, -h / 2, w, h, 6, paper)


def comment_box(c, x, y, w, s, prog, a=1.0):
    with xf(c, x, y, alpha=a):
        rrect(c, -w / 2, -60, w, 120, 18, "#0e2632", a=0.95)
        rrect(c, -w / 2, -60, w, 120, 18, "#7fd8ea", a=0.6, stroke=3)
        c.drawCircle(-w / 2 + 60, 0, 30, P(AMBER))
        n = int(len(s) * clamp(prog))
        text(c, s[:n] + ("|" if prog < 1 else ""), -w / 2 + 112, 14, 40, WHITE, "SemiBold", "left")
