"""Rim-lit stick-figure characters for the 2D animation format: poses, expressions, walk cycles, speech bubbles."""
import math

import skia

from .core import clamp, ease_out, back_out, ramp
from .gfx import C, AA, text, text_w, rect, circle, poly, fit_size, draw_cover, fill, linear, wrap

INK = "#0b0b12"
EYE = "#f4eedc"

# front arm (upper, bend), back arm (upper, bend), front leg (hip, knee), back leg (hip, knee), lean, head tilt
POSES = {
    "stand": ((10, 14), (-10, -10), (5, 0), (-5, 0), 0, 0),
    "point": ((84, 4), (-12, -12), (6, 0), (-6, 0), 2, 0),
    "think": ((38, 128), (-8, -18), (5, 0), (-5, 0), -2, -6),
    "shock": ((150, -18), (-150, 18), (10, 0), (-12, 0), -7, -4),
    "sit": ((22, 44), (-6, -30), (84, -84), (74, -80), 2, 0),
    "cheer": ((166, 8), (-166, -8), (8, 0), (-8, 0), 0, -6),
    "sad": ((4, 6), (-4, -6), (3, 0), (-3, 0), 15, 20),
    "talk": ((46, 72), (-10, -12), (5, 0), (-5, 0), 1, 0),
    "carry": ((62, 58), (52, 70), (8, 4), (-8, 0), 5, 0),
    "look_up": ((10, 12), (-10, -12), (5, 0), (-5, 0), -9, -22),
    "fall": ((140, 30), (-120, -40), (40, 30), (-30, 50), 70, 10),
    "walk": None, "run": None,
}


def _pose(pose, t):
    if pose in ("walk", "run"):
        sp, amp = (7.0, 30) if pose == "walk" else (11.0, 46)
        s = math.sin(t * sp)
        return ((-amp * s, 20 + 10 * abs(s)), (amp * s, 20 + 10 * abs(s)), (amp * s, max(0, -40 * s) if pose == "run" else max(0, -22 * s)),
                (-amp * s, max(0, 40 * s) if pose == "run" else max(0, 22 * s)), 4 if pose == "walk" else 13, 0)
    return POSES.get(pose) or POSES["stand"]


def _limb(c, x, y, a1, a2, l1, l2, w, col, face):
    r1 = math.radians(a1)
    ex, ey = x + math.sin(r1) * l1 * face, y + math.cos(r1) * l1
    r2 = math.radians(a1 + a2)
    hx, hy = ex + math.sin(r2) * l2 * face, ey + math.cos(r2) * l2
    p = skia.Paint(Color=C(col), Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join, **AA)
    path = skia.Path()
    path.moveTo(x, y)
    path.lineTo(ex, ey)
    path.lineTo(hx, hy)
    c.drawPath(path, p)
    return hx, hy


def _body(c, pose, expr, t, color, face, talk, flat=None):
    """Draws at origin = feet. `flat` paints everything one color (used for the rim-light pass)."""
    fa, ba, fl, bl, lean, tilt = _pose(pose, t)
    bob = math.sin(t * 2.2) * 2.5 + (abs(math.sin(t * 7)) * -6 if pose == "walk" else 0) + (abs(math.sin(t * 9)) * -14 if pose == "cheer" else 0)
    leg, torso, arm, hr = 74, 128, 60, 48
    sit = pose == "sit"
    hip_y = -(leg * 2 - 8) + bob if not sit else -leg + bob
    ink = flat or INK
    c.save()
    if pose == "fall":
        c.translate(0, -70)
        c.rotate(lean * face)
        lean = 0
    lr = math.radians(lean)
    sx, sy = math.sin(lr) * torso * face, hip_y - math.cos(lr) * torso
    _limb(c, 0, hip_y, bl[0], bl[1], leg, leg, 21, ink, face)
    _limb(c, sx, sy + 16, ba[0], ba[1], arm, arm, 17, flat or color, face)
    _limb(c, 0, hip_y, fl[0], fl[1], leg, leg, 21, ink, face)
    body = skia.Path()
    body.moveTo(-26, hip_y + 6)
    body.lineTo(26, hip_y + 6)
    body.lineTo(sx + 34, sy + 8)
    body.lineTo(sx - 34, sy + 8)
    body.close()
    c.drawPath(body, skia.Paint(Color=C(flat or color), PathEffect=skia.CornerPathEffect.Make(18), **AA))
    hx, hy = sx + math.sin(lr) * 30 * face, sy - hr * 0.86
    c.drawCircle(hx, hy, hr, skia.Paint(Color=C(ink), **AA))
    if not flat:
        c.save()
        c.translate(hx, hy)
        c.rotate(tilt * face)
        blink = (t * 0.37 + hash(color) % 7 * 0.13) % 1 > 0.965
        ex = 10 * face
        eh = {"shock": 17, "fear": 16, "angry": 8, "sad": 10, "happy": 9, "think": 10}.get(expr, 12)
        for dx in (-16, 16):
            if blink:
                rect(c, ex + dx - 9, -6, 18, 4, EYE, r=2)
            else:
                c.drawOval(skia.Rect.MakeXYWH(ex + dx - 9, -8 - eh / 2, 18, eh), skia.Paint(Color=C(EYE), **AA))
                circle(c, ex + dx + 3 * face, -8 + (2 if expr == "sad" else -2 if expr == "think" else 0), 4.2, INK)
        if expr in ("angry", "sad", "fear"):
            s = 1 if expr == "angry" else -1
            for dx in (-16, 16):
                sign = 1 if dx > 0 else -1
                poly(c, [(ex + dx - 12, -22 + 5 * s * sign), (ex + dx + 12, -22 - 5 * s * sign)], EYE, 1, stroke=4, close=False)
        my = 18
        if talk > 0.08 or expr in ("shock", "fear"):
            oh = 6 + 16 * talk if talk > 0.08 else 16
            c.drawOval(skia.Rect.MakeXYWH(ex - 9, my - oh / 2, 18, oh), skia.Paint(Color=C(EYE), **AA))
        elif expr == "happy":
            p = skia.Path()
            p.addArc(skia.Rect.MakeXYWH(ex - 13, my - 12, 26, 18), 15, 150)
            c.drawPath(p, skia.Paint(Color=C(EYE), Style=skia.Paint.kStroke_Style, StrokeWidth=4.5, StrokeCap=skia.Paint.kRound_Cap, **AA))
        elif expr in ("sad", "angry"):
            p = skia.Path()
            p.addArc(skia.Rect.MakeXYWH(ex - 11, my, 22, 14), 200, 140)
            c.drawPath(p, skia.Paint(Color=C(EYE), Style=skia.Paint.kStroke_Style, StrokeWidth=4.5, StrokeCap=skia.Paint.kRound_Cap, **AA))
        else:
            rect(c, ex - 9, my - 2, 18, 4.5, EYE, r=2)
        c.restore()
    _limb(c, sx, sy + 16, fa[0], fa[1] + (math.sin(t * 6) * 9 if pose == "talk" else 0), arm, arm, 17, flat or color, face)
    c.restore()


def figure(c, x, y, s=1.0, pose="stand", expr="neutral", t=0.0, color="#ffb347", face=1, talk=0.0, rim="#8ec8ff", a=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    if a < 1:
        c.saveLayerAlpha(skia.Rect.MakeLTRB(-260, -460, 260, 40), int(clamp(a) * 255))
    c.drawOval(skia.Rect.MakeXYWH(-70, -10, 140, 22), skia.Paint(Color=C("#000000", 0.35), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8), **AA))
    c.save()
    c.translate(-5 * face, -4)
    _body(c, pose, expr, t, color, face, talk, flat=rim)
    c.restore()
    _body(c, pose, expr, t, color, face, talk)
    if a < 1:
        c.restore()
    c.restore()


def bubble(c, x, y, s, T, t, thought=False, side=1):
    p = back_out(ramp(t, 0, 0.35))
    if p <= 0 or not s:
        return
    size = 40
    lines = wrap(s, T["body"], size, 420)[:3]
    w = max(text_w(l, T["body"], size) for l in lines) + 60
    hh = len(lines) * size * 1.2 + 44
    c.save()
    c.translate(x, y)
    c.scale(p, p)
    bx = 0 if side > 0 else -w
    rect(c, bx, -hh, w, hh, "#ffffff", r=26)
    if thought:
        circle(c, bx + (30 if side > 0 else w - 30), 18, 12, "#ffffff")
        circle(c, bx + (10 if side > 0 else w - 10), 42, 7, "#ffffff")
    else:
        tx = bx + (40 if side > 0 else w - 40)
        poly(c, [(tx - 16, -4), (tx + 16, -4), (tx - 22 * side, 34)], "#ffffff")
    for i, ln in enumerate(lines):
        text(c, ln, bx + w / 2, -hh + 30 + size * 0.8 + i * size * 1.2, size, "#14141c", T["body"], "center")
    c.restore()


def draw_scene(c, shot, t, dur, T, VW, VH, bg=None, talk=0.0, paint=None):
    """One 2D shot: illustrated set (slow push), 1-2 characters acting, optional bubble."""
    from . import mg
    u = t / max(0.1, dur)
    if bg is not None:
        draw_cover(c, bg, 0, 0, VW, VH, 1.06 + 0.06 * u, 0.5, 0.5, paint=paint)
        rect(c, 0, 0, VW, VH, T["bg"], 0.28)
    else:
        mg.backdrop(c, T, t, shot.get("v", 0), VW, VH)
    gy = VH * 0.9
    fill(c, linear(0, gy - 150, 0, VH, [C(T["bg"], 0), C(T["bg"], 0.9)]), 0, gy - 150, VW, VH - gy + 150)
    cast = [x for x in (shot.get("cast") or []) if isinstance(x, dict)][:2] or [{"pose": "stand", "expr": "neutral"}]
    cols = [T["accent"], T["accent2"]]
    s = (VH / 1080.0) * (1.25 if len(cast) == 1 else 1.1)
    n = len(cast)
    for i, ch in enumerate(cast):
        fx = 0.36 if n == 1 and shot.get("bubble") else (0.5 if n == 1 else (0.3, 0.7)[i])
        face = 1 if (n == 1 or i == 0) else -1
        pose = ch.get("pose") if ch.get("pose") in POSES else "stand"
        enter = ease_out(ramp(t, 0.0 + i * 0.15, 0.5 + i * 0.15), 3)
        x = VW * fx - face * (1 - enter) * VW * 0.25
        if pose in ("walk", "run"):
            x += face * (u - 0.5) * VW * (0.22 if pose == "walk" else 0.4)
        figure(c, x, gy, s, pose if enter >= 1 or pose in ("walk", "run", "sit") else "walk", ch.get("expr", "neutral"), t + i * 1.7, cols[i % 2], face,
               talk if (i == 0 and pose in ("talk", "point", "stand")) else 0.0, a=min(1.0, enter * 2))
        if i == 0 and shot.get("bubble"):
            bubble(c, x + face * 70 * s, gy - 330 * s, shot["bubble"], T, t - 0.7, thought=pose == "think", side=face)
