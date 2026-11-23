"""Shared scene helpers: word timing, shot registry, camera, reusable mini-compositions."""
import json
import math
import os

import skia

from g6fx import (W, H, C, P, xf, rrect, poly, line, linear, radial, fill_shader, glow, mixhex, clamp, lerp, smooth,
                  ease_out, back_out, at, window, shape, oval, box, rect, grad_rect, T, tw, person, head, tag, speech,
                  stamp, marker_text, caption_serif, polaroid, corner_tag, palm, palm_green, car, baby_bundle, cash,
                  money_bag, bars, phone_prop, speedlines, burst, heart, blit, cached, MARKER, SERIF, SCRIPT, LUCKY,
                  BANG, BRUSH, OUT, LOOKS, sparkle)
from sets import bg

HERE = os.path.dirname(os.path.abspath(__file__))
_tr = json.load(open(os.path.join(HERE, "transcript.json")))
WORDS = [(w["w"].strip().strip(",.?!").lower(), w["s"], w["e"]) for s in _tr for w in s["words"]]


def wt(word, near, end=False):
    """Start time of the occurrence of `word` closest to time `near`."""
    word = word.lower()
    best = None
    for w, s, e in WORDS:
        if w == word or w.startswith(word):
            if best is None or abs(s - near) < abs(best[0] - near):
                best = (s, e)
    if best is None or abs(best[0] - near) > 8:
        return near
    return best[1] if end else best[0]


SHOTS = []


def shot(a, b, chapter=None):
    def deco(fn):
        SHOTS.append((a, b, fn, chapter))
        return fn
    return deco


def pop(t, start, dur=0.35):
    """Back-out pop scale 0..1."""
    return back_out(at(t, start, dur))


def fade(t, start, dur=0.3):
    return smooth(at(t, start, dur))


def draw_bg(c, name, blur=0.0, a=1.0):
    blit(c, bg(name, blur), 0, 0, a)


def cam(c, lt, d, z0=1.0, z1=1.07, cx=960, cy=540, dx=0, dy=0, shake=0.0, t=0.0):
    k = smooth(lt / max(d, 0.01))
    z = lerp(z0, z1, k)
    zm = min(z0, z1)
    if zm >= 1.0:
        hw, hh = W / (2 * zm), H / (2 * zm)
        cx = min(max(cx, hw), W - hw)
        cy = min(max(cy, hh), H - hh)
    hx = math.sin(t * 0.7) * 4 + math.sin(t * 1.9) * 2
    hy = math.cos(t * 0.6) * 3
    if shake:
        hx += math.sin(t * 61) * 14 * shake
        hy += math.cos(t * 53) * 10 * shake
    c.translate(W / 2 + hx + dx * k, H / 2 + hy + dy * k)
    c.scale(z, z)
    c.translate(-cx, -cy)


def mug(c, x, y, who, lk=None, label="", expr="neutral", rot=0.0, a=1.0, s=1.0, bgcol="#e8dcc0", t=0.0, w=300,
        h=380, xmark=0.0, pin=True, pose="stand"):
    """Polaroid with a character's head and shoulders."""
    lk = lk or who

    def inner(cc, iw, ih):
        grad_rect(cc, 0, 0, iw, ih, [bgcol, mixhex(bgcol, "#000000", 0.25)])
        for k in range(5):
            line(cc, 0, 40 + k * 50, iw, 40 + k * 50, "#000000", 2, 0.08)
        sc = iw / 190
        L = LOOKS[lk]
        eff = sc * (0.55 if L.get("baby") else 0.8 if L.get("small") else 1.0)
        person(cc, iw / 2, ih * 0.5 + 262 * eff, who, lk, pose, expr, t, s=sc)

    polaroid(c, x, y, w, h, inner, label, a=a, rot=rot, s=s, pin=pin)
    if xmark > 0:
        with xf(c, x, y, s=s, rot=rot, alpha=a):
            k1 = clamp(xmark * 2)
            k2 = clamp(xmark * 2 - 1)
            line(c, -w * 0.4, -h * 0.4, lerp(-w * 0.4, w * 0.4, k1), lerp(-h * 0.4, h * 0.25, k1), "#d8262e", 18)
            if k2 > 0:
                line(c, w * 0.4, -h * 0.4, lerp(w * 0.4, -w * 0.4, k2), lerp(-h * 0.4, h * 0.25, k2), "#d8262e", 18)


def red_string(c, pts, prog=1.0, col="#c0262e", wdt=5):
    if prog <= 0 or len(pts) < 2:
        return
    total = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    left = total * clamp(prog)
    pth = skia.Path()
    pth.moveTo(*pts[0])
    for i in range(len(pts) - 1):
        d = math.dist(pts[i], pts[i + 1])
        if left >= d:
            pth.lineTo(*pts[i + 1])
            left -= d
        else:
            k = left / d
            pth.lineTo(lerp(pts[i][0], pts[i + 1][0], k), lerp(pts[i][1], pts[i + 1][1], k))
            break
    c.drawPath(pth, P(col, wdt))


def arrow(c, x1, y1, x2, y2, col="#e8282e", w=10, prog=1.0, dashed=False, head_=True):
    k = clamp(prog)
    if k <= 0:
        return
    ex, ey = lerp(x1, x2, k), lerp(y1, y2, k)
    p = P(col, w)
    if dashed:
        p.setPathEffect(skia.DashPathEffect.Make([30, 18], 0))
    c.drawLine(x1, y1, ex, ey, p)
    if head_ and k > 0.05:
        ang = math.atan2(y2 - y1, x2 - x1)
        L = w * 4
        for s in (-1, 1):
            c.drawLine(ex, ey, ex - math.cos(ang + s * 0.5) * L, ey - math.sin(ang + s * 0.5) * L, P(col, w))


def checklist(c, x, y, items, t, times, size=52, col="#f2f2f2", check_col="#3ccf6a", cross=False, fam=LUCKY):
    for i, (label, tm) in enumerate(zip(items, times)):
        k = fade(t, tm, 0.3)
        if k <= 0:
            continue
        yy = y + i * size * 1.6
        with xf(c, x - (1 - k) * 40, yy, alpha=k):
            box(c, 0, -size * 0.85, size, size, "#ffffff", r=8, ow=5, oc="#141414")
            if cross:
                ck = at(t, tm + 0.15, 0.25)
                line(c, 8, -size * 0.8 + 8, 8 + (size - 16) * ck, -size * 0.8 + 8 + (size - 16) * ck, "#e8282e", 9)
            else:
                ck = at(t, tm + 0.15, 0.25)
                if ck > 0:
                    pth = skia.Path()
                    pth.moveTo(8, -size * 0.35)
                    pth.lineTo(size * 0.4, -size * 0.1)
                    pth.lineTo(lerp(size * 0.4, size + 6, ck), lerp(-size * 0.1, -size - 6, ck))
                    c.drawPath(pth, P(check_col, 10))
            T(c, label, size + 26, 0, size, col, fam, align="left", outline="#141414", ow=8)


def big_title(c, s, x, y, size, t, start, col="#ffffff", fam=LUCKY, outline="#141414", ow=12, rot=0.0):
    k = pop(t, start, 0.4)
    if k <= 0:
        return
    with xf(c, x, y, s=k, rot=rot):
        T(c, s, 0, size * 0.35, size, col, fam, outline=outline, ow=ow, shadow=0.4)


def note(c, x, y, s=1.0, col="#ffd36b", a=1.0):
    with xf(c, x, y, s=s, alpha=a):
        oval(c, 0, 0, 18, 13, col, ow=3)
        line(c, 16, 0, 16, -60, OUT, 8)
        line(c, 16, 0, 16, -60, col, 4)
        pth = skia.Path()
        pth.moveTo(16, -60)
        pth.quadTo(40, -50, 36, -28)
        c.drawPath(pth, P(col, 6))


def flash(c, t, start, dur=0.25, col="#ffffff"):
    k = 1 - clamp((t - start) / dur) if t >= start else 0
    if k > 0:
        c.drawRect(skia.Rect(0, 0, W, H), P(col, a=k * 0.85))


def thought(c, x, y, w, h, a=1.0, s=1.0):
    with xf(c, x, y, s=s, alpha=a):
        for k in range(10):
            ang = k / 10 * math.tau
            oval(c, math.cos(ang) * w * 0.42, math.sin(ang) * h * 0.38, w * 0.22, h * 0.22, "#ffffff", ow=5)
        oval(c, 0, 0, w * 0.47, h * 0.42, "#ffffff", ow=0)
        oval(c, -w * 0.3, h * 0.62, 24, 18, "#ffffff")
        oval(c, -w * 0.4, h * 0.8, 14, 10, "#ffffff")


def dream_house(c, x, y, s=1.0, t=0.0, lock=0.0):
    with xf(c, x, y, s=s):
        pth = poly([(-170, -150), (0, -270), (170, -150)])
        shape(c, pth, "#c0392b")
        box(c, -150, -150, 300, 160, "#f7e3c0")
        box(c, -30, -90, 60, 100, "#3f7a8a")
        oval(c, 18, -40, 6, 6, "#e8c25a", ow=2)
        box(c, -125, -125, 70, 55, "#9fd3ef", ow=4)
        box(c, 55, -125, 70, 55, "#9fd3ef", ow=4)
        if lock > 0:
            with xf(c, 0, -40, s=back_out(lock) * 0.9):
                pth = skia.Path()
                pth.moveTo(-18, -10)
                pth.lineTo(-18, -30)
                pth.cubicTo(-18, -58, 18, -58, 18, -30 + 12 * (1 - clamp(lock * 2 - 1)))
                c.drawPath(pth, P(OUT, 12))
                c.drawPath(pth, P("#c9c9c9", 6))
                box(c, -28, -12, 56, 46, "#e8c25a", r=8, ow=4)
                oval(c, 0, 8, 6, 6, OUT, ow=0)


def phone_screen(c, x, y, s, draw, rot=0.0, a=1.0):
    with xf(c, x, y, s=s, rot=rot, alpha=a):
        box(c, -170, -330, 340, 660, "#141418", r=44, ow=6)
        c.save()
        c.clipRRect(skia.RRect.MakeRectXY(skia.Rect(-150, -300, 150, 300), 26, 26))
        draw(c)
        c.restore()
        box(c, -50, -318, 100, 14, "#2a2a30", r=7, ow=0)


def lucia_text_card(c, lines, x, y, size=46, a=1.0):
    for i, l in enumerate(lines):
        T(c, l, x, y + i * size * 1.25, size, "#f3e3c3", SERIF, a=a, shadow=0.5)


def doors(c, t, start, labels, cols=("#2f7ad8", "#d8262e"), x0=560, x1=1360, y=860, open_=(0.0, 0.0), glowa=1.0):
    for i, (x, lab, col) in enumerate(zip((x0, x1), labels, cols)):
        k = pop(t, start + i * 0.25, 0.4)
        if k <= 0:
            continue
        with xf(c, x, y, s=k):
            glow(c, 0, -230, 380, col, 0.35 * glowa)
            box(c, -150, -470, 300, 470, mixhex(col, "#000000", 0.55), r=8, ow=7)
            o = open_[i]
            box(c, -140, -460, 280 * (1 - o * 0.7), 460, col, r=6, ow=5)
            if o > 0:
                rect(c, -140 + 280 * (1 - o * 0.7), -460, 280 * o * 0.7, 460, "#fff6d8", 0.8)
            oval(c, 100 * (1 - o * 0.7), -230, 12, 12, "#e8c25a", ow=3)
            tag(c, 0, -520, lab, 34)
