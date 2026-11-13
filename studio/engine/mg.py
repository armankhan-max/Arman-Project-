"""Motion graphics drawn in code. Every graphic takes (canvas, spec, t, dur, theme, VW, VH, variant)
and animates itself in, holds, and out. `variant` changes layout so two videos never look the same."""
import json
import math
import os
import random

import skia

from . import core
from .core import clamp, ease_out, ease_io, back_out, ramp, lerp
from .gfx import (C, text, text_w, wrap, fit_size, text_block, rect, line, circle, arc, poly, arrow, linear, radial, fill, glow,
                  draw_cover, AA)

FULLSCREEN = {"title", "timeline", "bar_chart", "compare", "line_chart", "ring", "world_map", "route_map", "quote", "list", "clock",
              "icon_grid", "character_card", "document", "diagram", "credits", "stat", "counter", "keywords"}
OVERLAY = {"lower_third", "callout"}


def num(x, default=0.0):
    try:
        if isinstance(x, str):
            x = x.replace(",", "").replace("$", "").replace("%", "").strip().split()[0]
        return float(x)
    except Exception:
        return default


def fmt_num(v):
    if abs(v) >= 100 or abs(v - round(v)) < 1e-6:
        return "{:,}".format(int(round(v)))
    return "%.1f" % v


def S(x, default=""):
    return str(x if x is not None else default).strip()


def up(T, s):
    return s.upper() if T["display"] not in ("PatrickHand-Regular", "PlayfairDisplay") else s


# ------------------------------------------------------------------ backdrops
def backdrop(c, T, t, v, VW, VH, img=None, dim=0.72):
    """Designed background. With an image: blurred, tinted picture so the graphic sits in the story's world."""
    if img is not None:
        from .gfx import blurred
        b = blurred(img, 26, 0.2)
        draw_cover(c, b, 0, 0, VW, VH, 1.08 + 0.03 * math.sin(t * 0.3), 0.5, 0.5)
        rect(c, 0, 0, VW, VH, T["bg"], dim)
    else:
        ang = (v % 4) * math.pi / 4
        fill(c, linear(VW / 2 - math.cos(ang) * VW / 2, VH / 2 - math.sin(ang) * VH / 2, VW / 2 + math.cos(ang) * VW / 2, VH / 2 + math.sin(ang) * VH / 2,
                       [C(T["bg"]), C(T["bg2"])]), 0, 0, VW, VH)
    k = v % 5
    ink = T["ink"]
    if T["key"] == "paper" or k == 0:
        st = 60
        off = (t * 6) % st if T["key"] != "paper" else 0
        for x in range(-st, VW + st, st):
            line(c, x + off, 0, x + off, VH, ink, 1, 0.07 if T["key"] != "paper" else 0.13, cap=False)
        for y in range(0, VH + st, st):
            line(c, 0, y, VW, y, ink, 1, 0.07 if T["key"] != "paper" else 0.13, cap=False)
    elif k == 1:
        for x in range(40, VW, 80):
            for y in range(40, VH, 80):
                circle(c, x, y, 2.2, ink, 0.1)
    elif k == 2:
        off = (t * 14) % 120
        for x in range(-VH, VW + 120, 120):
            line(c, x + off, VH, x + off + VH * 0.6, 0, ink, 2, 0.05, cap=False)
    elif k == 3:
        for i in range(1, 7):
            circle(c, VW * 0.78, VH * 0.3, i * 150 + (t * 10) % 150, ink, 0.05, stroke=2)
    else:
        glow(c, VW * (0.2 + 0.1 * math.sin(t * 0.2)), VH * 0.25, VH * 0.9, T["accent"], 0.12)
        glow(c, VW * 0.85, VH * 0.85, VH * 0.7, T["accent2"], 0.08)
    if T.get("hud"):
        hud(c, T, t, VW, VH, 0.5)


def hud(c, T, t, VW, VH, a=0.6, label=None):
    m, L, col = 46, 34, T["dim"]
    for (x, y, sx, sy) in ((m, m, 1, 1), (VW - m, m, -1, 1), (m, VH - m, 1, -1), (VW - m, VH - m, -1, -1)):
        line(c, x, y, x + L * sx, y, col, 2, a, cap=False)
        line(c, x, y, x, y + L * sy, col, 2, a, cap=False)
    for i in range(9):
        y = VH * 0.25 + i * VH * 0.06
        line(c, VW - m - (14 if i % 4 == 0 else 7), y, VW - m, y, col, 2, a * 0.7, cap=False)
    if label:
        text(c, label, m + 8, VH - m - 12, 17, col, T["mono"], a=a, tracking=2)


def kicker(c, T, s, x, y, a=1.0, align="left", size=22):
    """Small tracked mono label with an accent tick."""
    if not s:
        return
    s = s.upper()
    w = text_w(s, T["mono"], size, 3)
    ox = x - (w / 2 if align == "center" else w if align == "right" else 0)
    rect(c, ox - 22, y - size * 0.72, 10, size * 0.8, T["accent"], a)
    text(c, s, ox, y, size, T["dim"], T["mono"], a=a, tracking=3)


def reveal_text(c, s, x, y, size, color, name, t, delay=0.0, d=0.55, align="left", a=1.0, **kw):
    """Line slides up out of a mask."""
    p = ease_out(ramp(t, delay, delay + d), 4)
    if p <= 0:
        return 0
    w = text_w(s, name, size)
    ox = x - (w / 2 if align == "center" else w if align == "right" else 0)
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(ox - 30, y - size * 1.1, ox + w + 30, y + size * 0.32))
    text(c, s, x, y + (1 - p) * size * 1.1, size, color, name, align, a, **kw)
    c.restore()
    return w


# ------------------------------------------------------------------ graphics
def g_title(c, sp, t, dur, T, VW, VH, v):
    s = up(T, S(sp.get("text"), "CHAPTER"))
    sub = S(sp.get("sub"))
    k = v % 3
    maxw = VW * 0.78
    size = fit_size(max(wrap(s, T["display"], VH * 0.13, maxw), key=len), T["display"], maxw, VH * 0.13, 40)
    lines = wrap(s, T["display"], size, maxw)[:3]
    lh = size * 1.08
    if k == 0:  # centered, accent rule grows
        y0 = VH / 2 - (len(lines) - 1) * lh / 2 + size * 0.3
        for i, ln in enumerate(lines):
            reveal_text(c, ln, VW / 2, y0 + i * lh, size, T["ink"], T["display"], t, 0.15 + i * 0.12, align="center", shadow=10)
        w = ease_out(ramp(t, 0.05, 0.9), 4) * min(maxw, 520)
        rect(c, VW / 2 - w / 2, y0 + (len(lines) - 1) * lh + size * 0.38, w, 6, T["accent"])
        if sub:
            text(c, sub.upper(), VW / 2, y0 + (len(lines) - 1) * lh + size * 0.38 + 58, 26, T["dim"], T["mono"], "center", ramp(t, 0.6, 1.1), tracking=4)
    elif k == 1:  # left, big ghost numeral
        n = S(sp.get("n"), "")
        if n:
            text(c, n.zfill(2), VW * 0.07, VH * 0.72, VH * 0.6, T["ink"], T["display"], a=0.07 * ramp(t, 0, 0.6))
        x = VW * 0.1
        y0 = VH * 0.5 - (len(lines) - 1) * lh / 2
        rect(c, x - 34, y0 - size * 0.8, 10, ease_out(ramp(t, 0, 0.7)) * (len(lines) * lh), T["accent"])
        for i, ln in enumerate(lines):
            reveal_text(c, ln, x, y0 + i * lh, size, T["ink"], T["display"], t, 0.12 + i * 0.12, shadow=10)
        if sub:
            text(c, sub.upper(), x, y0 + len(lines) * lh - size * 0.2 + 20, 26, T["accent"], T["mono"], a=ramp(t, 0.6, 1.1), tracking=4)
    else:  # text on a wiping accent block
        y0 = VH / 2 - (len(lines) - 1) * lh / 2 + size * 0.3
        for i, ln in enumerate(lines):
            w = text_w(ln, T["display"], size)
            p = ease_io(ramp(t, 0.05 + i * 0.1, 0.6 + i * 0.1))
            rect(c, VW / 2 - w / 2 - 28, y0 + i * lh - size * 0.9, (w + 56) * p, size * 1.12, T["accent"])
            c.save()
            c.clipRect(skia.Rect.MakeXYWH(VW / 2 - w / 2 - 28, y0 + i * lh - size, (w + 56) * p, size * 1.4))
            text(c, ln, VW / 2, y0 + i * lh, size, T["bg"], T["display"], "center")
            c.restore()
        if sub:
            text(c, sub.upper(), VW / 2, y0 + len(lines) * lh + 20, 26, T["ink"], T["mono"], "center", ramp(t, 0.7, 1.2), tracking=4)


def g_lower_third(c, sp, t, dur, T, VW, VH, v):
    name, role = S(sp.get("name") or sp.get("text")), S(sp.get("role") or sp.get("sub"))
    p = ease_out(ramp(t, 0.1, 0.7), 4) * (1 - ease_out(ramp(t, dur - 0.4, dur)))
    if p <= 0:
        return
    x, y = VW * 0.055, VH * (0.8 if VW > VH else 0.7)
    size = 46
    w = max(text_w(name.upper(), T["display"], size), text_w(role.upper(), T["mono"], 22, 2)) + 60
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y - 70, (w + 20) * p, 140))
    rect(c, x, y - 58, 8, 96, T["accent"])
    rect(c, x + 8, y - 58, w, 96, T["bg"], 0.82)
    text(c, name.upper() if T["display"] != "PlayfairDisplay" else name, x + 34, y - 6, size, T["ink"], T["display"])
    if role:
        text(c, role.upper(), x + 34, y + 24, 22, T["accent"], T["mono"], tracking=2)
    c.restore()


def g_stat(c, sp, t, dur, T, VW, VH, v):
    val = num(sp.get("value"))
    p = ease_out(ramp(t, 0.2, min(1.8, dur * 0.55)), 3)
    s = S(sp.get("prefix")) + fmt_num(val * p if val else 0) + S(sp.get("suffix"))
    if not val:
        s = S(sp.get("value"), "?")
    size = fit_size(s, T["display"], VW * 0.8, VH * 0.3, 60)
    k = v % 2
    cx = VW / 2 if k == 0 else VW * 0.1
    al = "center" if k == 0 else "left"
    a = ramp(t, 0.05, 0.4)
    text(c, s, cx, VH * 0.55, size, T["accent"], T["display"], al, a, shadow=14)
    w = ease_out(ramp(t, 0.3, 1.1), 4) * min(VW * 0.5, text_w(s, T["display"], size))
    rect(c, cx - (w / 2 if k == 0 else 0), VH * 0.55 + 30, w, 6, T["ink"], 0.9)
    lab = S(sp.get("label"))
    if lab:
        text_block(c, lab.upper(), cx, VH * 0.55 + 96, 34, T["ink"], T["mono"], VW * 0.7, al, ramp(t, 0.6, 1.1), max_lines=2, tracking=0)


def g_counter(c, sp, t, dur, T, VW, VH, v):
    p = back_out(ramp(t, 0.1, 0.6))
    r = VH * 0.26 * p
    x, y = VW / 2, VH * 0.46
    circle(c, x, y, r * 1.08, T["ink"], 0.15)
    circle(c, x, y, r, T["accent"])
    circle(c, x, y, r * 0.88, T["bg"], 0.25, stroke=6)
    s = S(sp.get("value"), "1")
    size = fit_size(s, T["display"], r * 1.5, r * 0.9, 30)
    if p > 0.5:
        text(c, s, x, y + size * 0.35, size, T["bg"], T["display"], "center")
    text_block(c, S(sp.get("label")).upper(), x, y + VH * 0.26 + 90, 38, T["ink"], T["mono"], VW * 0.7, "center", ramp(t, 0.5, 1.0), max_lines=2)


def g_timeline(c, sp, t, dur, T, VW, VH, v):
    ev = [e for e in (sp.get("events") or []) if isinstance(e, dict)][:6]
    if not ev:
        return g_title(c, {"text": S(sp.get("title"), "Timeline")}, t, dur, T, VW, VH, v)
    x0, x1, y = VW * 0.1, VW * 0.9, VH * 0.55
    grow = ease_io(ramp(t, 0.1, min(dur * 0.8, 0.6 + 0.7 * len(ev))))
    line(c, x0, y, x0 + (x1 - x0), y, T["dim"], 2, 0.35, cap=False)
    line(c, x0, y, x0 + (x1 - x0) * grow, y, T["accent2"], 4)
    for i in range(41):
        xx = x0 + (x1 - x0) * i / 40
        line(c, xx, y + 8, xx, y + (20 if i % 5 == 0 else 13), T["dim"], 2, 0.4, cap=False)
    kicker(c, T, S(sp.get("title"), "timeline"), x0 + 22, VH * 0.16, ramp(t, 0, 0.4))
    n = len(ev)
    for i, e in enumerate(ev):
        fx = (i + 0.5) / n
        x = x0 + (x1 - x0) * fx
        a = ease_out(ramp(grow, fx - 0.08, fx + 0.04))
        if a <= 0:
            continue
        up_ = i % 2 == 0
        yy = y - 150 if up_ else y + 120
        line(c, x, y, x, y + (-110 if up_ else 84) * a, T["dim"], 2, 0.7, cap=False)
        circle(c, x, y, 10 * back_out(a), T["accent"])
        circle(c, x, y, 20 * a, T["accent"], 0.25 * (1 - a) + 0.12, stroke=2)
        text(c, S(e.get("t")), x, yy, 44, T["accent"], T["mono"], "center", a)
        text_block(c, S(e.get("label")).upper(), x, yy + 38, 21, T["ink"], T["mono"], (x1 - x0) / n - 20, "center", a, max_lines=3, lh=1.3)


def g_bar_chart(c, sp, t, dur, T, VW, VH, v):
    items = [i for i in (sp.get("items") or []) if isinstance(i, dict)][:6]
    if not items:
        return g_title(c, {"text": S(sp.get("title"), "Data")}, t, dur, T, VW, VH, v)
    vals = [abs(num(i.get("value"))) for i in items]
    mx = max(vals) or 1
    x0, top = VW * 0.1, VH * 0.26
    text(c, up(T, S(sp.get("title"))), x0, VH * 0.17, 58, T["ink"], T["display"], a=ramp(t, 0, 0.4))
    rh = min(110, (VH * 0.62) / len(items))
    labw = max(text_w(S(i.get("label")).upper(), T["mono"], 26) for i in items) + 30
    labw = min(labw, VW * 0.3)
    bw = VW * 0.8 - labw - 160
    unit = S(sp.get("unit"))
    for k, (it, val) in enumerate(zip(items, vals)):
        y = top + k * rh
        p = ease_out(ramp(t, 0.3 + k * 0.18, 1.2 + k * 0.18), 4)
        a = ramp(t, 0.2 + k * 0.18, 0.5 + k * 0.18)
        col = T["accent"] if val == mx else T["accent2"]
        text(c, S(it.get("label")).upper()[:26], x0, y + rh * 0.55, 26, T["ink"], T["mono"], a=a)
        rect(c, x0 + labw, y + rh * 0.2, bw, rh * 0.5, T["ink"], 0.07 * a, r=6)
        rect(c, x0 + labw, y + rh * 0.2, max(4, bw * val / mx * p), rh * 0.5, col, a, r=6)
        text(c, fmt_num(val * p) + (" " + unit if unit else ""), x0 + labw + bw * val / mx * p + 18, y + rh * 0.56, 30, T["ink"], T["display"], a=a)


def g_compare(c, sp, t, dur, T, VW, VH, v):
    A, B = sp.get("a") or {}, sp.get("b") or {}
    va, vb = abs(num(A.get("value"))), abs(num(B.get("value")))
    mx = max(va, vb) or 1
    unit = S(sp.get("unit"))
    base, hmax = VH * 0.78, VH * 0.5
    for k, (d, val, col, cx) in enumerate(((A, va, T["accent2"], VW * 0.32), (B, vb, T["accent"], VW * 0.68))):
        p = ease_out(ramp(t, 0.25 + k * 0.25, 1.3 + k * 0.25), 4)
        hh = max(6, hmax * val / mx * p)
        bw = VW * 0.16
        rect(c, cx - bw / 2, base - hh, bw, hh, col, r=10)
        s = fmt_num(val * p) if val else S(d.get("value"))
        text(c, s, cx, base - hh - 26, 76, T["ink"], T["display"], "center", ramp(t, 0.3 + k * 0.25, 0.6 + k * 0.25))
        text_block(c, S(d.get("label")).upper(), cx, base + 54, 28, T["ink"], T["mono"], VW * 0.3, "center", ramp(t, 0.2, 0.6), max_lines=2)
    line(c, VW * 0.14, base, VW * 0.86, base, T["dim"], 3, 0.6)
    pv = back_out(ramp(t, 0.5, 0.9))
    circle(c, VW / 2, VH * 0.5, 44 * pv, T["bg"], 1)
    circle(c, VW / 2, VH * 0.5, 44 * pv, T["ink"], 0.8, stroke=3)
    if pv > 0.6:
        text(c, "VS", VW / 2, VH * 0.5 + 13, 36, T["ink"], T["display"], "center")
    if unit:
        kicker(c, T, unit, VW / 2, VH * 0.14, ramp(t, 0.1, 0.5), "center")


def g_line_chart(c, sp, t, dur, T, VW, VH, v):
    pts = [p for p in (sp.get("points") or []) if isinstance(p, dict)][:14]
    if len(pts) < 2:
        return g_stat(c, {"value": (pts[0].get("y") if pts else 0), "label": S(sp.get("title"))}, t, dur, T, VW, VH, v)
    ys = [num(p.get("y")) for p in pts]
    lo, hi = min(ys), max(ys)
    if hi - lo < 1e-9:
        hi = lo + 1
    x0, x1, y0, y1 = VW * 0.12, VW * 0.88, VH * 0.8, VH * 0.28
    text(c, up(T, S(sp.get("title"))), x0, VH * 0.17, 56, T["ink"], T["display"], a=ramp(t, 0, 0.4))
    for i in range(5):
        yy = lerp(y0, y1, i / 4)
        line(c, x0, yy, x1, yy, T["ink"], 1, 0.12, cap=False)
        text(c, fmt_num(lerp(lo, hi, i / 4)), x0 - 16, yy + 8, 22, T["dim"], T["mono"], "right")
    P = [(lerp(x0, x1, i / (len(pts) - 1)), lerp(y0, y1, (y - lo) / (hi - lo))) for i, y in enumerate(ys)]
    prog = ease_io(ramp(t, 0.3, min(dur * 0.75, 2.6))) * (len(P) - 1)
    k = int(prog)
    cur = P[:k + 1]
    if k < len(P) - 1:
        f = prog - k
        cur.append((lerp(P[k][0], P[k + 1][0], f), lerp(P[k][1], P[k + 1][1], f)))
    if len(cur) > 1:
        area = skia.Path()
        area.moveTo(cur[0][0], y0)
        for q in cur:
            area.lineTo(*q)
        area.lineTo(cur[-1][0], y0)
        area.close()
        c.drawPath(area, skia.Paint(Shader=linear(0, y1, 0, y0, [C(T["accent"], 0.35), C(T["accent"], 0.0)]), **AA))
        poly(c, cur, T["accent"], 1, stroke=6, close=False)
    circle(c, cur[-1][0], cur[-1][1], 11, T["ink"])
    circle(c, cur[-1][0], cur[-1][1], 22, T["accent"], 0.35, stroke=3)
    for i, p in enumerate(pts):
        if i % max(1, len(pts) // 6) == 0 or i == len(pts) - 1:
            text(c, S(p.get("x")), P[i][0], y0 + 40, 22, T["dim"], T["mono"], "center", ramp(prog, i - 0.5, i))
    unit = S(sp.get("unit"))
    text(c, fmt_num(lerp(ys[min(k, len(ys) - 1)], ys[min(k + 1, len(ys) - 1)], prog - k)) + (" " + unit if unit else ""),
         cur[-1][0] + 26, cur[-1][1] - 18, 36, T["ink"], T["display"])


def g_ring(c, sp, t, dur, T, VW, VH, v):
    val = clamp(num(sp.get("value")) / 100.0)
    p = ease_out(ramp(t, 0.2, 1.6), 4)
    x, y, r = VW / 2, VH * 0.46, VH * 0.27
    arc(c, x, y, r, 0, 360, T["ink"], 26, 0.1)
    arc(c, x, y, r, -90, 360 * val * p, T["accent"], 26)
    text(c, "%d%%" % round(val * 100 * p), x, y + 46, 150, T["ink"], T["display"], "center")
    text_block(c, S(sp.get("label")).upper(), x, y + r + 96, 34, T["ink"], T["mono"], VW * 0.7, "center", ramp(t, 0.5, 1.0), max_lines=2)


def g_quote(c, sp, t, dur, T, VW, VH, v):
    s = S(sp.get("text"))
    size = 62 if len(s) < 120 else 48
    maxw = VW * 0.7
    lines = wrap(s, T["display"] if T["display"] == "PlayfairDisplay" else T["body"], size, maxw)[:7]
    fnt = T["display"] if T["display"] == "PlayfairDisplay" else T["body"]
    y0 = VH * 0.5 - len(lines) * size * 0.65
    text(c, "“", VW * 0.15 - 20, y0 + 40, 260, T["accent"], "PlayfairDisplay", a=ramp(t, 0, 0.4))
    total = sum(len(ln) for ln in lines)
    shown = int(total * ramp(t, 0.3, min(dur * 0.7, 0.3 + total * 0.035)))
    for i, ln in enumerate(lines):
        if shown <= 0:
            break
        text(c, ln[:shown], VW * 0.15 + 70, y0 + 70 + i * size * 1.32, size, T["ink"], fnt)
        shown -= len(ln)
    by = S(sp.get("by"))
    if by:
        yb = y0 + 70 + len(lines) * size * 1.32 + 30
        a = ramp(t, dur * 0.55, dur * 0.7)
        rect(c, VW * 0.15 + 70, yb - 16, 60 * a, 4, T["accent"])
        text(c, by.upper(), VW * 0.15 + 150, yb - 4, 26, T["dim"], T["mono"], a=a, tracking=3)


def g_list(c, sp, t, dur, T, VW, VH, v):
    items = [S(i if not isinstance(i, dict) else i.get("label") or i.get("text")) for i in (sp.get("items") or [])][:6]
    title = S(sp.get("title"))
    x0 = VW * 0.1
    text(c, up(T, title), x0, VH * 0.18, 60, T["ink"], T["display"], a=ramp(t, 0, 0.4))
    rect(c, x0, VH * 0.18 + 22, ease_out(ramp(t, 0.1, 0.8)) * 160, 6, T["accent"])
    n = max(1, len(items))
    grid = v % 2 == 1 and n >= 4 and VW > VH
    rh = min(128, VH * 0.62 / (math.ceil(n / 2) if grid else n))
    step = max(0.25, min(0.7, (dur * 0.6) / n))
    for i, it in enumerate(items):
        p = ease_out(ramp(t, 0.4 + i * step, 0.9 + i * step), 4)
        if p <= 0:
            continue
        col, row = (i % 2, i // 2) if grid else (0, i)
        w = VW * 0.39 if grid else VW * 0.8
        x = x0 + col * (w + VW * 0.02) + (1 - p) * 60
        y = VH * 0.28 + row * rh
        rect(c, x, y, w, rh - 18, T["ink"], 0.07 * p, r=12)
        rect(c, x, y, 8, rh - 18, T["accent"], p, r=3)
        text(c, "%02d" % (i + 1), x + 34, y + (rh - 18) / 2 + 16, 44, T["accent"], T["display"], a=p)
        sz = fit_size(it, T["body"], w - 150, 36, 22)
        text(c, wrap(it, T["body"], sz, w - 150)[0] if it else "", x + 118, y + (rh - 18) / 2 + sz * 0.35, sz, T["ink"], T["body"], a=p)


def g_clock(c, sp, t, dur, T, VW, VH, v):
    tm = S(sp.get("time"), "00:00")
    flick = 1.0 if t > 0.5 else (0.3 + 0.7 * ((int(t * 30) % 3) > 0))
    k = v % 2
    x = VW * 0.12 if k == 0 else VW / 2
    al = "left" if k == 0 else "center"
    size = fit_size(tm, T["mono"], VW * 0.7, VH * 0.2, 60)
    text(c, tm, x, VH * 0.5, size, T["ink"], T["mono"] if T["key"] != "home" else T["display"], al, flick * ramp(t, 0, 0.15), tracking=4)
    w = text_w(tm, T["mono"], size, 4)
    px = x - (w / 2 if k else 0)
    rect(c, px, VH * 0.5 + 34, w * ease_out(ramp(t, 0.1, dur * 0.9), 2), 4, T["accent"])
    d = " · ".join(s for s in (S(sp.get("date")), S(sp.get("place"))) if s)
    text(c, d.upper(), x, VH * 0.5 + 86, 26, T["accent2"], T["mono"], al, ramp(t, 0.35, 0.8), tracking=3)


def g_keywords(c, sp, t, dur, T, VW, VH, v):
    ws = [up(T, S(w)) for w in (sp.get("words") or []) if S(w)][:4] or [up(T, S(sp.get("text"), ""))]
    n = len(ws)
    step = min(0.6, dur * 0.7 / n)
    size = min(VH * 0.2, VH * 0.62 / n)
    y0 = VH / 2 - (n - 1) * size * 0.56 + size * 0.34
    for i, w in enumerate(ws):
        p = ramp(t, 0.1 + i * step, 0.34 + i * step)
        if p <= 0:
            continue
        sz = fit_size(w, T["display"], VW * 0.84, size, 40) * (1 + 0.5 * (1 - back_out(p)))
        col = T["accent"] if i == n - 1 else T["ink"]
        text(c, w, VW / 2, y0 + i * size * 1.12, sz, col, T["display"], "center", min(1, p * 2), stroke=T["bg"], stroke_w=sz * 0.09, shadow=12)


def g_icon_grid(c, sp, t, dur, T, VW, VH, v):
    items = [S(i if not isinstance(i, dict) else i.get("label")) for i in (sp.get("items") or [])][:6]
    n = max(1, len(items))
    cols = n if n <= 3 or VW < VH * 1.2 and n <= 3 else math.ceil(n / 2)
    if VW < VH:
        cols = 2
    rows = math.ceil(n / cols)
    r = min(VW * 0.8 / cols, VH * 0.62 / rows) * 0.3
    cols_c = [T["accent"], T["accent2"], T["ink"]]
    for i, it in enumerate(items):
        cx = VW * 0.1 + (i % cols + 0.5) * VW * 0.8 / cols
        cy = VH * 0.2 + (i // cols + 0.42) * VH * 0.64 / rows
        p = back_out(ramp(t, 0.2 + i * 0.22, 0.65 + i * 0.22))
        if p <= 0:
            continue
        col = cols_c[i % 3]
        circle(c, cx, cy, r * p, col, 0.16)
        circle(c, cx, cy, r * p, col, 1, stroke=5)
        arc(c, cx, cy, r * 1.18 * p, t * 40 + i * 60, 80, col, 3, 0.6)
        text(c, (it[:1] or "?").upper(), cx, cy + r * 0.3, r * 0.9, col, T["display"], "center", min(1, p))
        text_block(c, it.upper(), cx, cy + r + 46, 24, T["ink"], T["mono"], VW * 0.8 / cols - 30, "center", ramp(t, 0.5 + i * 0.22, 0.9 + i * 0.22), max_lines=2, lh=1.25)


def g_character_card(c, sp, t, dur, T, VW, VH, v, img=None):
    p = ease_out(ramp(t, 0.1, 0.7), 4)
    w, hh = VW * 0.74, VH * 0.6
    x, y = VW * 0.13, VH * 0.2 + (1 - p) * 40
    rect(c, x, y, w, hh, T["bg2"], 0.92 * p, r=14)
    rect(c, x, y, w, hh, T["dim"], 0.5 * p, r=14, stroke=2)
    pw = hh * 0.74
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x + 30, y + 30, pw, hh - 60))
    if img is not None:
        draw_cover(c, img, x + 30, y + 30, pw, hh - 60, 1.0 + 0.04 * ramp(t, 0, dur), 0.5, 0.35, p,
                   paint=skia.Paint(ColorFilter=skia.ColorFilters.Matrix([0.33, 0.6, 0.07, 0, 0] * 3 + [0, 0, 0, 1, 0])))
    else:
        rect(c, x + 30, y + 30, pw, hh - 60, T["bg"], p)
        circle(c, x + 30 + pw / 2, y + hh * 0.4, pw * 0.2, T["dim"], 0.5 * p)
        circle(c, x + 30 + pw / 2, y + hh * 0.95, pw * 0.42, T["dim"], 0.5 * p)
    c.restore()
    tx = x + pw + 80
    kicker(c, T, S(sp.get("role"), "profile"), tx + 22, y + 80, p)
    nm = up(T, S(sp.get("name"), "Unknown"))
    text(c, nm, tx, y + 160, fit_size(nm, T["display"], w - pw - 130, 72, 30), T["ink"], T["display"], a=p)
    for i, f in enumerate([S(f) for f in (sp.get("facts") or [])][:4]):
        a = ramp(t, 0.6 + i * 0.3, 0.9 + i * 0.3)
        yy = y + 240 + i * 62
        rect(c, tx, yy - 20, 12, 12, T["accent"], a)
        text(c, wrap(f, T["body"], 28, w - pw - 170)[0] if f else "", tx + 32, yy - 6, 28, T["ink"], T["body"], a=a)


def g_document(c, sp, t, dur, T, VW, VH, v):
    p = ease_out(ramp(t, 0.05, 0.6), 4)
    w, hh = min(VW * 0.5, VH * 0.75), VH * 0.82
    c.save()
    c.translate(VW / 2, VH / 2 + (1 - p) * VH * 0.6)
    c.rotate(-3 + (v % 5) * 1.4)
    rect(c, -w / 2 + 14, -hh / 2 + 18, w, hh, "#000000", 0.35)
    rect(c, -w / 2, -hh / 2, w, hh, "#efe9da")
    text(c, S(sp.get("title"), "REPORT").upper()[:30], -w / 2 + 50, -hh / 2 + 90, 36, "#1a1a1a", "SpecialElite-Regular")
    line(c, -w / 2 + 50, -hh / 2 + 112, w / 2 - 50, -hh / 2 + 112, "#1a1a1a", 2, 0.8, cap=False)
    yy = -hh / 2 + 170
    lines = [S(l) for l in (sp.get("lines") or [])][:7]
    chars = int(ramp(t, 0.5, max(1.2, dur * 0.75)) * sum(len(l) for l in lines))
    rnd = random.Random(v)
    for ln in lines:
        for wl in wrap(ln, "SpecialElite-Regular", 25, w - 100)[:3]:
            if chars > 0:
                text(c, wl[:chars], -w / 2 + 50, yy, 25, "#22201c", "SpecialElite-Regular")
            chars -= len(wl)
            yy += 38
        yy += 14
    for i in range(3):
        rect(c, -w / 2 + 50 + rnd.random() * w * 0.3, yy + 20 + i * 38, w * (0.25 + rnd.random() * 0.3), 24, "#111111", 0.9 * ramp(t, 0.8, 1.2))
    st = S(sp.get("stamp"))
    if st:
        ps = ramp(t, dur * 0.45, dur * 0.45 + 0.18)
        if ps > 0:
            c.save()
            c.translate(w * 0.16, hh * 0.22)
            c.rotate(-14)
            sc = 1 + (1 - ps) * 1.4
            c.scale(sc, sc)
            tw = text_w(st.upper(), "ArchivoBlack-Regular", 54) + 50
            rect(c, -tw / 2, -50, tw, 78, "#b3122a", ps * 0.85, r=6, stroke=6)
            text(c, st.upper(), 0, 8, 54, "#b3122a", "ArchivoBlack-Regular", "center", ps * 0.85)
            c.restore()
    c.restore()


def g_diagram(c, sp, t, dur, T, VW, VH, v):
    parts = [S(p if not isinstance(p, dict) else p.get("label")) for p in (sp.get("parts") or [])][:6]
    cx, cy = VW / 2, VH * 0.52
    R = min(VW, VH) * 0.33
    p0 = back_out(ramp(t, 0.1, 0.6))
    n = max(1, len(parts))
    for i, pt in enumerate(parts):
        ang = -math.pi / 2 + i * math.tau / n + (v % 3) * 0.2
        p = ease_out(ramp(t, 0.45 + i * 0.25, 0.95 + i * 0.25), 4)
        if p <= 0:
            continue
        ex = cx + math.cos(ang) * R * (1.25 if VW > VH else 0.9) * p
        ey = cy + math.sin(ang) * R * 0.86 * p
        line(c, cx, cy, ex, ey, T["dim"], 3, 0.8, dash=(10, 10))
        w = min(VW * 0.26, text_w(pt.upper(), T["mono"], 24) + 44)
        rect(c, ex - w / 2, ey - 30, w, 60, T["bg2"], p, r=30)
        rect(c, ex - w / 2, ey - 30, w, 60, T["accent2"], p, r=30, stroke=3)
        sz = fit_size(pt.upper(), T["mono"], w - 30, 24, 14)
        text(c, pt.upper(), ex, ey + sz * 0.36, sz, T["ink"], T["mono"], "center", p)
    circle(c, cx, cy, R * 0.36 * p0, T["accent"])
    circle(c, cx, cy, R * 0.44 * p0, T["accent"], 0.35, stroke=3)
    ctr = up(T, S(sp.get("center"), ""))
    if p0 > 0.5:
        ls = wrap(ctr, T["display"], 34, R * 0.62)[:3]
        for i, ln in enumerate(ls):
            text(c, ln, cx, cy + 12 + (i - (len(ls) - 1) / 2) * 38, 34, T["bg"], T["display"], "center")


def g_credits(c, sp, t, dur, T, VW, VH, v):
    lines = [S(l) for l in (sp.get("lines") or [])][:60]
    text(c, up(T, S(sp.get("title"), "Sources & Credits")), VW / 2, VH * 0.2, 56, T["ink"], T["display"], "center", ramp(t, 0, 0.5))
    rect(c, VW / 2 - 60, VH * 0.2 + 24, 120, 5, T["accent"], ramp(t, 0.2, 0.6))
    total = len(lines) * 40
    view = VH * 0.6
    scroll = max(0, total - view) * ramp(t, 1.0, max(1.5, dur - 0.8))
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(0, VH * 0.27, VW, view))
    for i, ln in enumerate(lines):
        y = VH * 0.32 + i * 40 - scroll
        if VH * 0.25 < y < VH * 0.9:
            sz = fit_size(ln, T["mono"], VW * 0.84, 22, 12)
            text(c, ln, VW / 2, y, sz, T["dim"], T["mono"], "center", ramp(t, 0.3 + i * 0.03, 0.7 + i * 0.03))
    c.restore()


def g_callout(c, sp, t, dur, T, VW, VH, v):
    rnd = random.Random(v)
    fx, fy = num(sp.get("x"), rnd.uniform(0.38, 0.62)), num(sp.get("y"), rnd.uniform(0.4, 0.6))
    x, y, r = VW * fx, VH * fy, VH * num(sp.get("r"), 0.13)
    out = 1 - ramp(t, dur - 0.3, dur)
    p = ease_io(ramp(t, 0.3, 0.95))
    col = T["accent"] if T["key"] != "clean" else T["accent2"]
    arc(c, x, y, r, -100, 372 * p, col, 9, out)
    lab = S(sp.get("label"))
    side = -1 if fx > 0.5 else 1
    lx, ly = x + side * VW * 0.2, y - VH * 0.22
    arrow(c, lx, ly + 20, x + side * r * 0.8, y - r * 0.75, col, 8, out, ease_out(ramp(t, 0.8, 1.3)), curve=-side * 60)
    if lab:
        a = ramp(t, 0.7, 1.0) * out
        sz = 40
        w = text_w(lab.upper(), T["display"], sz) + 44
        rect(c, lx - w / 2, ly - 54, w, 66, T["bg"], 0.9 * a, r=8)
        text(c, lab.upper(), lx, ly - 8, sz, T["ink"], T["display"], "center", a)


# ------------------------------------------------------------------ maps
_geo = {}


def _load_geo():
    if _geo:
        return _geo
    topo = json.load(open(os.path.join(core.ASSETS, "geo", "countries-110m.json")))
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    arcs = []
    for a in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in a:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)

    def ring(idx):
        out = []
        for i in idx:
            pts = arcs[i] if i >= 0 else arcs[~i][::-1]
            out += pts if not out else pts[1:]
        return out
    countries = []
    for g in topo["objects"]["countries"]["geometries"]:
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        rings = [ring(p[0]) for p in polys if p]
        path = skia.Path()
        for rg in rings:
            prev = None
            for (lo, la) in rg:
                if prev is None or abs(lo - prev) > 180:
                    path.moveTo(lo, -la)
                else:
                    path.lineTo(lo, -la)
                prev = lo
        countries.append({"name": (g.get("properties") or {}).get("name", ""), "rings": rings, "path": path})
    _geo["countries"] = countries
    return _geo


def _country_at(lat, lon, name=""):
    geo = _load_geo()
    nm = name.lower().strip()
    if nm:
        for ct in geo["countries"]:
            if ct["name"].lower() == nm or (len(nm) > 4 and nm in ct["name"].lower()):
                return ct
    for ct in geo["countries"]:
        for rg in ct["rings"]:
            inside = False
            j = len(rg) - 1
            for i in range(len(rg)):
                xi, yi = rg[i]
                xj, yj = rg[j]
                if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-9) + xi:
                    inside = not inside
                j = i
            if inside:
                return ct
    return None


def _draw_world(c, T, VW, VH, cx, cy, z, hi=None, a=1.0):
    geo = _load_geo()
    k = VW / 360.0 * z
    c.save()
    c.translate(VW / 2, VH / 2)
    c.scale(k, k)
    c.translate(-cx, cy)
    land = skia.Paint(Color=C(core.mix_hex(T["bg2"], T["ink"], 0.16), a), **AA)
    edge = skia.Paint(Color=C(T["dim"], 0.55 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=1.3 / k, **AA)
    for ct in geo["countries"]:
        c.drawPath(ct["path"], land)
        c.drawPath(ct["path"], edge)
    if hi is not None:
        c.drawPath(hi["path"], skia.Paint(Color=C(T["accent"], 0.55 * a), **AA))
        c.drawPath(hi["path"], skia.Paint(Color=C(T["accent"], a), Style=skia.Paint.kStroke_Style, StrokeWidth=2.6 / k, **AA))
    gp = skia.Paint(Color=C(T["ink"], 0.07 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=1.0 / k, **AA)
    for lo in range(-180, 181, 30):
        c.drawLine(lo, -90, lo, 90, gp)
    for la in range(-60, 61, 30):
        c.drawLine(-180, la, 180, la, gp)
    c.restore()
    return lambda lon, lat: (VW / 2 + (lon - cx) * k, VH / 2 + (cy - lat) * k)


def _marker(c, T, x, y, t, label, sub="", a=1.0, side=1):
    for i in range(2):
        ph = (t * 0.8 + i * 0.5) % 1
        circle(c, x, y, 14 + ph * 46, T["accent"], (1 - ph) * 0.7 * a, stroke=3)
    circle(c, x, y, 11, T["bg"], a)
    circle(c, x, y, 8, T["accent"], a)
    if label:
        lab = label.upper()
        w = max(text_w(lab, "Inter-Bold", 30), text_w(sub, "SpaceMono-Regular", 18, 1)) + 36
        lx = x + 40 * side - (w if side < 0 else 0)
        line(c, x + 12 * side, y - 8, x + 40 * side, y - 40, T["ink"], 2, 0.8 * a)
        rect(c, lx, y - 84, w, 70 if sub else 50, T["bg"], 0.88 * a, r=6)
        rect(c, lx, y - 84, 5, 70 if sub else 50, T["accent"], a)
        text(c, lab, lx + 20, y - 50, 30, T["ink"], "Inter-Bold", a=a)
        if sub:
            text(c, sub, lx + 20, y - 26, 18, T["dim"], "SpaceMono-Regular", a=a, tracking=1)


def g_world_map(c, sp, t, dur, T, VW, VH, v):
    lat, lon = clamp(num(sp.get("lat")), -80, 80), clamp(num(sp.get("lon")), -179, 179)
    hi = _country_at(lat, lon, S(sp.get("country")))
    z1 = 3.2 + (v % 3) * 0.9
    p = ease_io(ramp(t, 0.25, min(dur * 0.7, 2.6)))
    z = lerp(1.0 if VW > VH else 2.0, z1, p)
    cx, cy = lerp(lon * 0.35, lon, p), lerp(lat * 0.3 + 10, lat, p)
    proj = _draw_world(c, T, VW, VH, cx, cy, z, hi if p > 0.5 else None)
    fill(c, radial(VW / 2, VH / 2, VW * 0.75, [C(T["bg"], 0), C(T["bg"], 0.75)]), 0, 0, VW, VH)
    x, y = proj(lon, lat)
    a = ramp(t, min(dur * 0.5, 1.6), min(dur * 0.5, 1.6) + 0.4)
    coord = "%.2f°%s  %.2f°%s" % (abs(lat), "N" if lat >= 0 else "S", abs(lon), "E" if lon >= 0 else "W")
    _marker(c, T, x, y, t, S(sp.get("label") or sp.get("place")), coord, a, -1 if x > VW * 0.6 else 1)
    kicker(c, T, S(sp.get("place"), "location"), VW * 0.06 + 22, VH * 0.12, ramp(t, 0.1, 0.5))


def g_route_map(c, sp, t, dur, T, VW, VH, v):
    pts = [(clamp(num(p.get("lat")), -80, 80), clamp(num(p.get("lon")), -179, 179), S(p.get("name"))) for p in (sp.get("points") or []) if isinstance(p, dict)][:5]
    if len(pts) < 2:
        if pts:
            return g_world_map(c, {"lat": pts[0][0], "lon": pts[0][1], "place": pts[0][2], "label": pts[0][2]}, t, dur, T, VW, VH, v)
        return g_title(c, {"text": S(sp.get("label"), "Route")}, t, dur, T, VW, VH, v)
    las, los = [p[0] for p in pts], [p[1] for p in pts]
    cx, cy = (min(los) + max(los)) / 2, (min(las) + max(las)) / 2
    span = max(max(los) - min(los), (max(las) - min(las)) * VW / VH, 4)
    z1 = clamp(360.0 / span * 0.55, 1.2, 40)
    p = ease_io(ramp(t, 0.1, 1.2))
    proj = _draw_world(c, T, VW, VH, lerp(cx * 0.4, cx, p), lerp(cy * 0.4, cy, p), lerp(1.0, z1, p))
    fill(c, radial(VW / 2, VH / 2, VW * 0.75, [C(T["bg"], 0), C(T["bg"], 0.75)]), 0, 0, VW, VH)
    P = [proj(lo, la) for la, lo, _ in pts]
    prog = ease_io(ramp(t, 1.0, max(2.0, dur * 0.8))) * (len(P) - 1)
    for i in range(len(P) - 1):
        f = clamp(prog - i)
        if f <= 0:
            break
        (x1, y1), (x2, y2) = P[i], P[i + 1]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - math.hypot(x2 - x1, y2 - y1) * 0.18
        seg = [((1 - u) ** 2 * x1 + 2 * (1 - u) * u * mx + u * u * x2, (1 - u) ** 2 * y1 + 2 * (1 - u) * u * my + u * u * y2)
               for u in [k / 30 * f for k in range(31)]]
        poly(c, seg, T["accent"], 1, stroke=6, close=False)
        circle(c, seg[-1][0], seg[-1][1], 9, T["ink"])
    for i, ((x, y), (_, _, nm)) in enumerate(zip(P, pts)):
        a = ramp(prog, i - 0.15, i + 0.05) if i else ramp(t, 0.8, 1.1)
        if a > 0:
            _marker(c, T, x, y, t + i * 0.3, nm, "", a, -1 if x > VW * 0.6 else 1)
    kicker(c, T, S(sp.get("label"), "route"), VW * 0.06 + 22, VH * 0.12, ramp(t, 0.1, 0.5))


DRAW = {"title": g_title, "lower_third": g_lower_third, "stat": g_stat, "timeline": g_timeline, "bar_chart": g_bar_chart,
        "compare": g_compare, "line_chart": g_line_chart, "ring": g_ring, "world_map": g_world_map, "route_map": g_route_map,
        "quote": g_quote, "list": g_list, "callout": g_callout, "clock": g_clock, "keywords": g_keywords, "icon_grid": g_icon_grid,
        "character_card": g_character_card, "document": g_document, "counter": g_counter, "diagram": g_diagram, "credits": g_credits}


def draw(c, spec, t, dur, T, VW, VH, v=0, img=None, with_backdrop=True):
    ty = spec.get("type")
    fn = DRAW.get(ty)
    if not fn:
        return
    if with_backdrop and ty in FULLSCREEN:
        solid = ty in ("world_map", "route_map", "document")
        backdrop(c, T, t, v, VW, VH, None if solid else img, 0.78 if T["key"] not in ("clean", "paper", "comic") else 0.86)
    try:
        if ty == "character_card":
            fn(c, spec, t, dur, T, VW, VH, v, img)
        else:
            fn(c, spec, t, dur, T, VW, VH, v)
    except Exception:
        text(c, S(spec.get("text") or spec.get("title") or spec.get("label")), VW / 2, VH / 2, 60, T["ink"], T["display"], "center")
