"""Space-documentary kit: animated stickman presenter (walk cycle, gestures, lip flap) + cosmic objects.

Builds on the rim-lit black-head stickman style in ../blackhole/sgfx.py.
Angle convention for limbs (from sgfx): 0 = hanging straight down, +90 = pointing forward (+x),
180 = straight up, negative = toward the back. a2 is the elbow/knee bend relative to a1.
"""
import json
import math
import os
import random
import sys

import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "blackhole"))
from sgfx import *  # noqa: E402,F401,F403
import sgfx  # noqa: E402

TAU = math.tau

# ======================================================================= presenter animation
MP = {
    "idle": dict(la=(-8, 12), ra=(8, -6), ll=(-4, 0), rl=(4, 0)),
    "talk": dict(la=(-10, 14), ra=(38, 62), ll=(-4, 0), rl=(4, 0)),
    "present": dict(la=(-10, 14), ra=(70, 40), ll=(-5, 0), rl=(5, 0)),
    "point": dict(la=(-10, 14), ra=(96, -4), ll=(-5, 0), rl=(5, 0)),
    "point_up": dict(la=(-10, 14), ra=(140, 6), ll=(-5, 0), rl=(5, 0)),
    "point_down": dict(la=(-10, 14), ra=(58, 4), ll=(-5, 0), rl=(5, 0)),
    "wow": dict(la=(-130, -25), ra=(130, 25), ll=(-9, 0), rl=(9, 0)),
    "open": dict(la=(-62, -28), ra=(62, 28), ll=(-6, 0), rl=(6, 0)),
    "think": dict(la=(-30, 95), ra=(30, 132), ll=(-4, 0), rl=(4, 0)),
    "hips": dict(la=(-42, 92), ra=(42, -92), ll=(-8, 0), rl=(8, 0)),
    "shrug": dict(la=(-58, -78), ra=(58, 78), ll=(-4, 0), rl=(4, 0)),
    "wave": dict(la=(-10, 14), ra=(130, 40), ll=(-4, 0), rl=(4, 0)),
    "look_scope": dict(la=(60, 70), ra=(75, 60), ll=(-10, 0), rl=(12, 0)),
    "float": dict(la=(-55, 30), ra=(60, -25), ll=(-14, 22), rl=(18, 28)),
    "float_point": dict(la=(-55, 30), ra=(100, -6), ll=(-14, 22), rl=(18, 28)),
    "float_wow": dict(la=(-125, -20), ra=(125, 20), ll=(-20, 18), rl=(20, 18)),
    "hold_up": dict(la=(-150, -10), ra=(150, 10), ll=(-6, 0), rl=(6, 0)),
    "duck": dict(la=(-150, -60), ra=(150, 60), ll=(-22, 30), rl=(22, -10)),
    "sit": dict(la=(25, 60), ra=(35, 50), ll=(80, -85), rl=(75, -80)),
    "lean_point": dict(la=(-20, 20), ra=(110, -10), ll=(-14, 0), rl=(10, 0)),
    "climb": dict(la=(-20, 30), ra=(30, 40), ll=(18, -40), rl=(-12, 10)),
}

_TALK = None


def _load_talk():
    global _TALK
    segs = json.load(open(os.path.join(HERE, "transcript.json")))
    on = bytearray(int(700 * 50))
    for s in segs:
        for w in s["words"]:
            a, b = int(w["s"] * 50), int((w["e"] + 0.04) * 50)
            for i in range(max(0, a), min(len(on), b)):
                on[i] = 1
    _TALK = on


def talking(t):
    if _TALK is None:
        _load_talk()
    i = int(t * 50)
    return 1.0 if 0 <= i < len(_TALK) and _TALK[i] else 0.0


def mix(a, b, k):
    a = MP[a] if isinstance(a, str) else a
    b = MP[b] if isinstance(b, str) else b
    return {key: (lerp(a[key][0], b[key][0], k), lerp(a[key][1], b[key][1], k)) for key in a}


def keys(t, seq, blend=0.45):
    """seq = [(time, pose), ...]; holds each pose, blends smoothly into the next around its key time."""
    if t <= seq[0][0]:
        return MP[seq[0][1]] if isinstance(seq[0][1], str) else seq[0][1]
    for i in range(len(seq) - 1):
        t1, p1 = seq[i + 1]
        if t < t1 + blend * 0.5:
            k = smooth((t - (t1 - blend * 0.5)) / blend)
            return mix(seq[i][1], p1, k) if k > 0 else (MP[seq[i][1]] if isinstance(seq[i][1], str) else seq[i][1])
    p = seq[-1][1]
    return MP[p] if isinstance(p, str) else p


def alive(p, t, amt=1.0, talk=0.0, seed=0.0):
    """Breathing + small natural arm drift, and conversational hand motion while talking."""
    q = dict(p)
    b = math.sin(t * 2.1 + seed)
    la, ra = q["la"], q["ra"]
    g = talk * amt
    q["la"] = (la[0] - 3 * amt * b, la[1] + 4 * amt * math.sin(t * 1.7 + seed))
    q["ra"] = (ra[0] + 3 * amt * b + g * 9 * math.sin(t * 3.1 + seed), ra[1] + g * 14 * math.sin(t * 4.3 + 1 + seed))
    return q


def walk_pose(ph, amp=1.0, arms=True):
    s, co = math.sin(ph), math.cos(ph)
    s2, co2 = math.sin(ph + math.pi), math.cos(ph + math.pi)
    p = {
        "ll": (26 * amp * s, -38 * amp * max(0.0, co) - 6 * amp),
        "rl": (26 * amp * s2, -38 * amp * max(0.0, co2) - 6 * amp),
        "la": (-24 * amp * s - 4, 18 + 10 * amp * max(0.0, -s)),
        "ra": (-24 * amp * s2 + 4, 18 + 10 * amp * max(0.0, -s2)),
    }
    if not arms:
        p["la"], p["ra"] = MP["idle"]["la"], MP["idle"]["ra"]
    return p


STRIDE = 285.0  # px per full walk cycle at scale 1


def walker(t, t0, t1, x0, x1, s=1.0):
    """Returns (x, phase, walking) for a walk from x0 at t0 to x1 at t1 with stride-matched cadence."""
    if t <= t0:
        return x0, 0.0, False
    if t >= t1:
        return x1, 0.0, False
    k = (t - t0) / (t1 - t0)
    x = lerp(x0, x1, k)
    ph = abs(x - x0) / (STRIDE * s) * TAU
    return x, ph, True


def guide(c, x, y, t, pose="idle", s=1.0, face=1, expr="smile", look=(0, 0), space=True, helmet=None,
          talk=None, who="kai", rot=0.0, alpha=1.0, walk=None, life=1.0, rim=RIM, red=0.0):
    """Presenter with hip centre at (x, y). walk = phase (radians) when walking."""
    talk = talking(t) if talk is None else talk
    p = MP[pose] if isinstance(pose, str) else pose
    bob = 0.0
    if walk is not None:
        p = walk_pose(walk)
        bob = -7 * abs(math.cos(walk)) + 3
        p = alive(p, t, 0.3, 0.0)
    else:
        p = alive(p, t, life, talk, seed=hash(who) % 7)
    if "float" in (pose if isinstance(pose, str) else ""):
        bob += 10 * math.sin(t * 1.3)
        rot += 3 * math.sin(t * 0.9)
    c.save()
    c.translate(x, y + bob * s)
    if face < 0:
        c.scale(-1, 1)
    sgfx.figure(c, 0, 0, who, p, expr, t, s=s, look=look, face=1, talk=talk, space=space, helmet=helmet,
                rot=rot * face, rim=rim, rim_off=(9, -8) if face > 0 else (-9, -8), alpha=alpha, red=red)
    c.restore()


def foot_y(y, s=1.0):
    """Ground level under a standing guide whose hip is at y."""
    return y + 178 * s


def hip_on(ground, s=1.0):
    return ground - 178 * s


# ======================================================================= captions-free labels
def doc_title(c, t, start, name, sub=None, dur=5.0, x=90, y=930, col="#8ec8ff"):
    """Quiet documentary-style title (bottom-left). Only object names / key facts, no clutter."""
    k = ease_out(at(t, start, 0.7))
    out = clamp((start + dur - t) / 0.6)
    a = k * out
    if a <= 0:
        return
    c.save()
    c.resetMatrix()
    with xf(c, x + (1 - k) * -30, y, alpha=a):
        wmax = max(text_width(name, 50, "Bold"), text_width(sub, 26, "SemiBold") if sub else 0)
        with xf(c, wmax * 0.45, -12, 1, sx=1.0, sy=0.32):
            glow(c, 0, 0, wmax * 0.85 + 80, "#000000", 0.55)
        c.drawRect(skia.Rect(0, -54, 4, sub and 34 or 4), P(col))
        text(c, name, 22, -6, 50, "#ffffff", "Bold", align="left", shadow=True)
        if sub:
            text(c, sub, 24, 30, 26, col, "SemiBold", align="left", shadow=True)
    c.restore()


def fact(c, t, start, s, x, y, size=46, col="#ffffff", dur=None, a=1.0):
    k = ease_out(at(t, start, 0.5))
    out = 1.0 if dur is None else clamp((start + dur - t) / 0.4)
    if k * out <= 0:
        return
    ui = y < 220 or y > 880
    if ui:
        c.save()
        c.resetMatrix()
    text(c, s, x, y + (1 - k) * 16, size, col, "Bold", a=k * out * a, shadow=True)
    if ui:
        c.restore()


def dim_line(c, x1, y1, x2, y2, col="#8ec8ff", a=1.0, w=3, prog=1.0):
    """Measurement line with end ticks (draws on with prog)."""
    if prog <= 0 or a <= 0:
        return
    xm, ym = lerp(x1, x2, 0.5), lerp(y1, y2, 0.5)
    ax, ay = lerp(xm, x1, prog), lerp(ym, y1, prog)
    bx, by = lerp(xm, x2, prog), lerp(ym, y2, prog)
    line(c, ax, ay, bx, by, col, w, a)
    ang = math.atan2(y2 - y1, x2 - x1) + math.pi / 2
    for (px, py) in ((ax, ay), (bx, by)):
        line(c, px - math.cos(ang) * 12, py - math.sin(ang) * 12, px + math.cos(ang) * 12, py + math.sin(ang) * 12,
             col, w, a)


def count(t, start, dur, v0, v1):
    return lerp(v0, v1, ease_out(at(t, start, dur)))


# ======================================================================= backgrounds
_rs = random.Random(7)
FAR = [(_rs.uniform(0, 1), _rs.uniform(0, 1), _rs.uniform(0.4, 1.4), _rs.uniform(0, 6.28)) for _ in range(900)]


def _milky_band(c):
    for i in range(60):
        rnd = random.Random(i)
        x = rnd.uniform(-200, W + 200)
        y = 700 - x * 0.35 + rnd.gauss(0, 60)
        glow(c, x, y, rnd.uniform(120, 300), rnd.choice(["#3a4a7a", "#4a3a6a", "#2f4f6f"]), 0.12)


def deep_sky(c, t, drift=(-4, 0), tint_col=None, band=True, a=1.0):
    """Starfield with faint Milky Way band (band baked + blurred once). Drawn in screen space (far away)."""
    c.save()
    c.resetMatrix()
    if band:
        img = cached(("deepsky", tint_col), lambda cc: (fill_shader(cc, skia.Rect(0, 0, W, H),
                                                                    linear(0, 0, 0, H, ["#02030a", "#060816"])),
                                                        _milky_band(cc),
                                                        glow(cc, 1500, 200, 700, tint_col, 0.10) if tint_col else None),
                     blur=30)
        blit(c, img)
    else:
        fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#02030a", "#060816"]))
    for (u, v, r, ph) in FAR:
        x = (u * W + drift[0] * t) % W
        y = (v * H + drift[1] * t) % H
        tw = 0.55 + 0.45 * math.sin(t * 1.6 + ph * 7)
        c.drawCircle(x, y, r, P("#dfe9ff", a=a * tw * 0.8))
    for (u, v, r, ph) in sgfx.STARS[:160]:
        x = (u * W + drift[0] * 2 * t) % W
        y = (v * H + drift[1] * 2 * t) % H
        tw = 0.6 + 0.4 * math.sin(t * 2 + ph * 5)
        c.drawCircle(x, y, r * 0.9, P("#ffffff", a=a * tw))
    c.restore()


def cam(c, zoom=1.0, cx=W / 2, cy=H / 2, t=0.0, drift=1.0, rot=0.0):
    dx = drift * (6 * math.sin(t * 0.37) + 3 * math.sin(t * 0.91))
    dy = drift * (4 * math.sin(t * 0.29 + 1) + 2 * math.sin(t * 1.13))
    c.translate(W / 2 + dx, H / 2 + dy)
    if rot:
        c.rotate(rot)
    zoom *= 1.02
    c.scale(zoom, zoom)
    c.translate(-cx, -cy)


def push(t, a, b, z0, z1):
    return lerp(z0, z1, smooth((t - a) / max(0.01, b - a)))


# ======================================================================= planets
PLANETS = {
    "jupiter": dict(bands=["#e9d7b6", "#c99a6b", "#f1e3c6", "#b9784a", "#ecdcbf", "#a8693f", "#e7cfaa", "#c58e5d",
                           "#efe0c4", "#b27a52", "#e4d0ad"], atm="#ffd9a0"),
    "saturn": dict(bands=["#efe0b8", "#e2c98f", "#f3e6c3", "#d6b77a", "#ecdcae", "#cfae70", "#efe2bd"], atm="#ffe6a8"),
    "earth": dict(base="#1f62b5", atm="#7fc3ff"),
    "mars": dict(base="#c1572f", atm="#ff9c70"),
    "mercury": dict(base="#8d8a86", atm=None),
    "ganymede": dict(base="#8f8577", atm=None),
    "proto": dict(bands=["#c0486a", "#8e2f55", "#d86a6a", "#7a2a4e", "#c45a70", "#93365c"], atm="#ff7aa8"),
    "brown": dict(bands=["#8a4a3a", "#6e3427", "#9c5a44", "#5e2c22", "#8f4e3c"], atm="#ff6a4a"),
    "neptune": dict(base="#3d6fe0", atm="#8fb6ff"),
}


def disc(c, x, y, r, shader):
    c.drawCircle(x, y, r, skia.Paint(Shader=shader, AntiAlias=True))


def _shade(c, x, y, r, light=(-0.45, -0.4), dark=0.82):
    disc(c, x, y, r,
                radial(x + light[0] * r, y + light[1] * r, r * 2.1,
                       [("#000000", 0), ("#000000", 0), ("#000000", dark * 0.45), ("#000000", dark)],
                       [0, 0.3, 0.62, 1]))


def planet(c, x, y, r, kind, t=0.0, spin=0.05, light=(-0.45, -0.4), grs=False, atm=True, dark=0.82, tilt=0.0):
    d = PLANETS[kind]
    if atm and d.get("atm"):
        glow(c, x, y, r * 1.35, d["atm"], 0.22)
    c.save()
    pth = skia.Path()
    pth.addCircle(x, y, r)
    c.clipPath(pth, skia.ClipOp.kIntersect, True)
    if tilt:
        c.translate(x, y)
        c.rotate(tilt)
        c.translate(-x, -y)
    if "bands" in d:
        bands = d["bands"]
        n = len(bands)
        for i, col in enumerate(bands):
            y0 = y - r + 2 * r * i / n
            c.drawRect(skia.Rect(x - r - 2, y0, x + r + 2, y0 + 2 * r / n + 2), P(col))
        rnd = random.Random(hash(kind) % 100)
        for i in range(26):
            lat = rnd.uniform(-0.85, 0.85)
            lon = rnd.uniform(0, TAU) + t * spin * (1 + 0.3 * abs(lat))
            if math.cos(lon) < 0.05:
                continue
            px = x + r * math.sin(lon) * math.sqrt(1 - lat * lat)
            py = y + r * lat
            ww = r * rnd.uniform(0.12, 0.35) * math.cos(lon)
            c.drawOval(skia.Rect(px - ww, py - r * 0.025, px + ww, py + r * 0.025),
                       P(rnd.choice(bands), a=0.85))
        if grs:
            lon = 0.5 + t * spin
            if math.cos(lon) > 0:
                px = x + r * math.sin(lon) * 0.89
                ww = r * 0.2 * math.cos(lon)
                c.drawOval(skia.Rect(px - ww, y + r * 0.27, px + ww, y + r * 0.42), P("#b5442a"))
                c.drawOval(skia.Rect(px - ww * 0.6, y + r * 0.3, px + ww * 0.6, y + r * 0.39), P("#d4683f"))
    else:
        c.drawCircle(x, y, r, P(d["base"]))
        rnd = random.Random(hash(kind) % 1000)
        if kind == "earth":
            for i in range(9):
                lat = rnd.uniform(-0.7, 0.7)
                lon = rnd.uniform(0, TAU) + t * spin
                if math.cos(lon) < 0:
                    continue
                px, py = x + r * math.sin(lon) * math.sqrt(1 - lat * lat), y + r * lat
                ww = r * rnd.uniform(0.15, 0.32) * (0.3 + 0.7 * math.cos(lon))
                c.drawOval(skia.Rect(px - ww, py - r * 0.16, px + ww, py + r * 0.18), P("#3f8f4a"))
            for i in range(10):
                lat = rnd.uniform(-0.8, 0.8)
                lon = rnd.uniform(0, TAU) + t * spin * 1.3
                if math.cos(lon) < 0:
                    continue
                px, py = x + r * math.sin(lon) * math.sqrt(1 - lat * lat), y + r * lat
                ww = r * rnd.uniform(0.12, 0.3) * math.cos(lon)
                c.drawOval(skia.Rect(px - ww, py - r * 0.03, px + ww, py + r * 0.04), P("#ffffff", a=0.75))
            c.drawOval(skia.Rect(x - r * 0.6, y - r * 1.02, x + r * 0.6, y - r * 0.82), P("#f4f8ff"))
        else:
            spots = {"mars": ("#8e3a1f", "#d9774a"), "mercury": ("#6e6b68", "#a8a5a0"),
                     "ganymede": ("#5f574c", "#c2b9a8"), "neptune": ("#2a50b0", "#6f9bff")}[kind]
            for i in range(22):
                lat = rnd.uniform(-0.85, 0.85)
                lon = rnd.uniform(0, TAU) + t * spin
                if math.cos(lon) < 0:
                    continue
                px, py = x + r * math.sin(lon) * math.sqrt(1 - lat * lat), y + r * lat
                rr = r * rnd.uniform(0.05, 0.2)
                c.drawOval(skia.Rect(px - rr * math.cos(lon), py - rr * 0.7, px + rr * math.cos(lon), py + rr * 0.7),
                           P(spots[i % 2], a=0.8))
            if kind == "mars":
                c.drawOval(skia.Rect(x - r * 0.4, y - r * 1.02, x + r * 0.4, y - r * 0.88), P("#f6ebe4"))
    c.restore()
    _shade(c, x, y, r, light, dark)
    if atm and d.get("atm"):
        c.drawCircle(x, y, r, P(d["atm"], max(2, r * 0.025), 0.35))


def rings(c, x, y, r, t, front, tilt=0.22, rot=-12, a=1.0, inner=1.25, outer=2.25):
    """Saturn rings; front=True draws only the half in front of the planet."""
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    if front:
        c.clipRect(skia.Rect(-r * 3, 0, r * 3, r * 3))
    else:
        c.clipRect(skia.Rect(-r * 3, -r * 3, r * 3, 0))
    cols = [("#cdb88a", 1.25, 1.5), ("#e8d7ad", 1.52, 1.86), ("#00000000", 1.86, 1.93), ("#d6c294", 1.93, 2.25)]
    for col, a0, a1 in cols:
        if col.startswith("#000"):
            continue
        rm = r * (a0 + a1) / 2 * (outer / 2.25)
        wdt = r * (a1 - a0) * (outer / 2.25)
        c.drawOval(skia.Rect(-rm, -rm * tilt, rm, rm * tilt), P(col, wdt * 0.98, 0.85 * a))
    c.restore()


def star(c, x, y, r, col="#ffd36b", t=0.0, core="#fffaf0", flare=1.0):
    glow(c, x, y, r * 6, col, 0.18 * flare)
    glow(c, x, y, r * 2.8, col, 0.45 * flare)
    for i in range(4):
        ang = i * 45 + 10 * math.sin(t * 0.5)
        L = r * (3.2 + 0.4 * math.sin(t * 2 + i))
        with xf(c, x, y, rot=ang):
            line(c, -L, 0, L, 0, col, max(1.5, r * 0.06), 0.35 * flare)
    disc(c, x, y, r, radial(x, y, r, [core, core, col], [0, 0.55, 1]))


def sun(c, x, y, r, t, col="#ffb52e"):
    glow(c, x, y, r * 2.2, "#ff9a1f", 0.35)
    glow(c, x, y, r * 1.35, "#ffd36b", 0.5)
    disc(c, x, y, r,
                radial(x, y, r, ["#fff6d8", "#ffd45a", "#ff9f1c", "#f07a12"], [0, 0.5, 0.85, 1]))
    rnd = random.Random(3)
    c.save()
    pth = skia.Path()
    pth.addCircle(x, y, r)
    c.clipPath(pth, skia.ClipOp.kIntersect, True)
    for i in range(70):
        ang = rnd.uniform(0, TAU) + t * 0.02
        d = r * math.sqrt(rnd.uniform(0, 1))
        rr = r * rnd.uniform(0.03, 0.08) * (0.7 + 0.3 * math.sin(t * 1.5 + i))
        c.drawCircle(x + math.cos(ang) * d, y + math.sin(ang) * d, rr, P("#fff2b0", a=0.18))
    c.restore()
    # prominences
    for i in range(3):
        ang = i * 2.2 + 0.6
        px, py = x + math.cos(ang) * r, y + math.sin(ang) * r
        hh = r * (0.12 + 0.05 * math.sin(t * 0.8 + i))
        pth = skia.Path()
        pth.moveTo(px - math.sin(ang) * r * 0.08, py + math.cos(ang) * r * 0.08)
        pth.quadTo(px + math.cos(ang) * hh * 2, py + math.sin(ang) * hh * 2,
                   px + math.sin(ang) * r * 0.08, py - math.cos(ang) * r * 0.08)
        c.drawPath(pth, P("#ff7a1a", r * 0.02, 0.7))


def supergiant(c, x, y, r, t):
    """UY Scuti: huge, red-orange, mottled, with gas streaming off."""
    rnd = random.Random(11)
    for i in range(40):
        ang = rnd.uniform(0, TAU) + t * 0.01
        d = r * rnd.uniform(1.05, 1.9) + 20 * math.sin(t * 0.3 + i)
        glow(c, x + math.cos(ang) * d, y + math.sin(ang) * d, r * rnd.uniform(0.15, 0.4), "#ff5a2a", 0.10)
    glow(c, x, y, r * 1.6, "#ff4a1a", 0.35)
    disc(c, x, y, r,
                radial(x, y, r, ["#ffd9a0", "#ff9a4a", "#e2502a", "#b02a18"], [0, 0.45, 0.8, 1]))
    c.save()
    pth = skia.Path()
    pth.addCircle(x, y, r)
    c.clipPath(pth, skia.ClipOp.kIntersect, True)
    for i in range(36):
        ang = rnd.uniform(0, TAU) + t * 0.015
        d = r * math.sqrt(rnd.uniform(0, 1))
        rr = r * rnd.uniform(0.08, 0.2) * (0.8 + 0.2 * math.sin(t * 0.7 + i))
        c.drawCircle(x + math.cos(ang) * d, y + math.sin(ang) * d, rr,
                     P(rnd.choice(["#ffb36b", "#c23a1f"]), a=0.22))
    c.restore()


# ======================================================================= discs, nebulae, galaxies
_DISK = [(random.Random(i).uniform(0.15, 1.0) ** 0.7, random.Random(i * 7 + 1).uniform(0, TAU),
          random.Random(i * 3 + 2).uniform(1, 3.2), random.Random(i * 5 + 3).random()) for i in range(900)]


def proto_disk(c, x, y, R, t, tilt=0.38, rot=-14, front=None, gap=None, a=1.0):
    """Swirling disc of gas and dust. front: None=all, True=near half, False=far half. gap=(r0,r1) cleared ring."""
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    if front is True:
        c.clipRect(skia.Rect(-R * 1.2, 0, R * 1.2, R * 1.2))
    elif front is False:
        c.clipRect(skia.Rect(-R * 1.2, -R * 1.2, R * 1.2, 0))
    for k, (col, rr, aa) in enumerate((("#7a3a1e", 1.0, 0.25), ("#b85a26", 0.75, 0.25), ("#f0a050", 0.45, 0.3))):
        c.drawOval(skia.Rect(-R * rr, -R * rr * tilt, R * rr, R * rr * tilt), P(col, R * 0.22 * rr, aa * a))
    for (u, ph, sz, h) in _DISK:
        rr = 0.12 + 0.88 * u
        if gap and gap[0] < rr < gap[1]:
            continue
        ang = ph + t * 0.35 / (rr ** 1.5)
        px, py = math.cos(ang) * R * rr, math.sin(ang) * R * rr * tilt
        col = "#ffe2a8" if rr < 0.35 else ("#f0954a" if rr < 0.7 else "#a8552a")
        c.drawCircle(px, py, sz * (0.6 + 0.6 * h), P(col, a=a * (0.35 + 0.5 * h)))
    c.restore()


def _neb_draw(kind):
    def d(cc):
        cc.clear(skia.ColorTRANSPARENT)
        rnd = random.Random(hash(kind) % 997)
        if kind == "tarantula":
            for i in range(160):
                ang = rnd.uniform(0, TAU)
                rr = abs(rnd.gauss(0, 260))
                x, y = 700 + math.cos(ang) * rr * 1.3, 500 + math.sin(ang) * rr
                glow(cc, x, y, rnd.uniform(60, 180), rnd.choice(["#ff5aa0", "#ff7a6a", "#c04ad0", "#4ad0c8", "#ffb070"]),
                     0.18)
            for i in range(26):
                pth = skia.Path()
                ang = rnd.uniform(0, TAU)
                pth.moveTo(700, 500)
                pth.quadTo(700 + math.cos(ang + 0.6) * 300, 500 + math.sin(ang + 0.6) * 260,
                           700 + math.cos(ang) * 520, 500 + math.sin(ang) * 420)
                cc.drawPath(pth, P("#ff9ac8", rnd.uniform(8, 26), 0.22))
        elif kind == "pillars":
            glow(cc, 700, 450, 700, "#2a6a6a", 0.5)
            glow(cc, 900, 300, 500, "#c8a04a", 0.35)
            for i in range(120):
                glow(cc, rnd.uniform(0, 1400), rnd.uniform(0, 1000), rnd.uniform(60, 160),
                     rnd.choice(["#3a8a8a", "#c89a4a", "#6aa0a0"]), 0.14)
            for (bx, top, wdt) in ((400, 220, 150), (760, 360, 110), (1040, 480, 90)):
                pth = skia.Path()
                pth.moveTo(bx - wdt, 1000)
                pth.cubicTo(bx - wdt * 0.9, 700, bx - wdt * 0.6, top + 120, bx - wdt * 0.5, top + 40)
                pth.quadTo(bx, top - 40, bx + wdt * 0.5, top + 40)
                pth.cubicTo(bx + wdt * 0.6, top + 140, bx + wdt * 0.8, 700, bx + wdt, 1000)
                pth.close()
                cc.drawPath(pth, P("#5a3a26"))
                cc.drawPath(pth, P("#ffcf7a", 10, 0.6))
                for k in range(14):
                    glow(cc, bx + rnd.uniform(-wdt, wdt) * 0.6, rnd.uniform(top + 60, 1000), rnd.uniform(30, 70),
                         "#2a1a12", 0.5)
        elif kind == "butterfly":
            glow(cc, 700, 500, 600, "#3a4a9a", 0.25)
            for side in (-1, 1):
                pth = skia.Path()
                pth.moveTo(700, 500)
                pth.cubicTo(700 + side * 180, 400, 700 + side * 420, 110, 700 + side * 600, 200)
                pth.cubicTo(700 + side * 700, 260, 700 + side * 690, 740, 700 + side * 600, 800)
                pth.cubicTo(700 + side * 420, 890, 700 + side * 180, 600, 700, 500)
                pth.close()
                cc.save()
                cc.clipPath(pth, skia.ClipOp.kIntersect, True)
                fill_shader(cc, skia.Rect(0, 0, 1400, 1000), radial(700, 500, 700, [
                    ("#ffffff", 0.95), ("#9ad0ff", 0.85), ("#7a6aff", 0.7), ("#ff6a5a", 0.75), ("#ff9a5a", 0.5)],
                    [0, 0.12, 0.4, 0.75, 1]))
                for i in range(70):
                    u = rnd.uniform(0.1, 0.95)
                    glow(cc, 700 + side * u * 620, 500 + rnd.gauss(0, 60 + 220 * u), rnd.uniform(30, 90),
                         rnd.choice(["#ffffff", "#5ab0ff", "#c070ff", "#ff7a5a"]), 0.25)
                for i in range(18):
                    y0 = rnd.uniform(-1, 1)
                    p2 = skia.Path()
                    p2.moveTo(700, 500)
                    p2.quadTo(700 + side * 300, 500 + y0 * 200, 700 + side * 650, 500 + y0 * 330)
                    cc.drawPath(p2, P("#ffffff", rnd.uniform(2, 6), 0.18))
                cc.restore()
                cc.drawPath(pth, P("#ffb07a", 10, 0.5))
            glow(cc, 700, 500, 120, "#ffffff", 0.8)
            cc.drawOval(skia.Rect(660, 420, 740, 580), P("#2a1a20", a=0.85))
        elif kind == "eagle":
            for i in range(150):
                glow(cc, rnd.uniform(100, 1300), rnd.uniform(100, 900), rnd.uniform(80, 200),
                     rnd.choice(["#3a7a8a", "#c8904a", "#8a5a9a"]), 0.15)
        elif kind == "generic":
            for i in range(140):
                ang = rnd.uniform(0, TAU)
                rr = abs(rnd.gauss(0, 240))
                glow(cc, 700 + math.cos(ang) * rr * 1.4, 500 + math.sin(ang) * rr, rnd.uniform(60, 170),
                     rnd.choice(["#4a8aff", "#c04ad0", "#4ad0c8", "#ff7a9a"]), 0.15)
        elif kind == "ring":
            for i in range(120):
                ang = rnd.uniform(0, TAU)
                rr = rnd.gauss(300, 40)
                glow(cc, 700 + math.cos(ang) * rr, 500 + math.sin(ang) * rr * 0.8, rnd.uniform(40, 110),
                     rnd.choice(["#ff7a4a", "#ffb05a", "#4ad0c8"]), 0.18)
            glow(cc, 700, 500, 200, "#4ad0ff", 0.25)
        elif kind == "fermi":
            for side in (-1, 1):
                for i in range(70):
                    ang = rnd.uniform(0, TAU)
                    rr = rnd.uniform(0, 1) ** 0.6 * 250
                    glow(cc, 700 + math.cos(ang) * rr * 0.85, 500 + side * 260 + math.sin(ang) * rr,
                         rnd.uniform(50, 120), rnd.choice(["#c05aff", "#ff5ad0", "#8a5aff"]), 0.15)
                pth = skia.Path()
                pth.addOval(skia.Rect(480, 500 + side * 260 - 250, 920, 500 + side * 260 + 250))
                cc.drawPath(pth, P("#e08aff", 6, 0.35))
    return d


_mcache = {}


def masked(key, draw, w, h, blur=0.0, feather=0.42):
    """Offscreen sprite with transparent background, decal blur, and a soft radial edge fade (no hard edges)."""
    if key not in _mcache:
        sf = skia.Surface(w, h)
        cc = sf.getCanvas()
        cc.clear(skia.ColorTRANSPARENT)
        draw(cc)
        img = sf.makeImageSnapshot()
        s2 = skia.Surface(w, h)
        c2 = s2.getCanvas()
        c2.clear(skia.ColorTRANSPARENT)
        p = skia.Paint()
        if blur:
            p.setImageFilter(skia.ImageFilters.Blur(blur, blur, skia.TileMode.kDecal))
        c2.drawImage(img, 0, 0, skia.SamplingOptions(), p)
        m = skia.Paint(Shader=skia.GradientShader.MakeRadial(
            skia.Point(w / 2, h / 2), max(w, h) / 2, [C("#000000"), C("#000000"), C("#000000", 0)],
            [0, 1 - feather, 1], skia.TileMode.kClamp, 0, skia.Matrix.Scale(1, h / max(w, h)) if False else None))
        m.setBlendMode(skia.BlendMode.kDstIn)
        c2.save()
        c2.scale(1, h / max(w, h)) if w >= h else c2.scale(w / max(w, h), 1)
        c2.drawRect(skia.Rect(0, 0, max(w, h), max(w, h)), m)
        c2.restore()
        _mcache[key] = s2.makeImageSnapshot()
    return _mcache[key]


def nebula(c, x, y, s, kind, t=0.0, a=1.0, rot=0.0, breathe=0.02):
    img = masked(("neb", kind), _neb_draw(kind), 1400, 1000, blur={"pillars": 5, "butterfly": 4}.get(kind, 14),
                 feather=0.38)
    sc = s * (1 + breathe * math.sin(t * 0.4))
    with xf(c, x, y, sc, rot, alpha=a):
        p = skia.Paint(AntiAlias=True)
        p.setBlendMode(skia.BlendMode.kScreen)
        c.drawImage(img, -700, -500, skia.SamplingOptions(skia.FilterMode.kLinear), p)
    rnd = random.Random(hash(kind) % 31)
    for i in range(24):
        px, py = x + rnd.uniform(-560, 560) * s, y + rnd.uniform(-400, 400) * s
        star(c, px, py, rnd.uniform(1.5, 4) * max(0.6, s), rnd.choice(["#bfe0ff", "#ffffff", "#ffd8a0"]), t,
             flare=0.5 * a)


def _gal_draw(kind):
    def d(cc):
        cc.clear(skia.ColorTRANSPARENT)
        rnd = random.Random(hash(kind) % 51)
        cx, cy = 600, 600
        if kind == "elliptical":
            for i in range(10):
                glow(cc, cx, cy, 560 - i * 50, "#ffe6c0", 0.12)
            for i in range(2500):
                rr = abs(rnd.gauss(0, 200))
                ang = rnd.uniform(0, TAU)
                cc.drawCircle(cx + math.cos(ang) * rr * 1.3, cy + math.sin(ang) * rr, rnd.uniform(0.6, 1.8),
                              P("#fff0d8", a=0.5))
            glow(cc, cx, cy, 120, "#ffffff", 0.7)
            return
        glow(cc, cx, cy, 540, "#2a3a70", 0.35)
        arms = 2 if kind == "milkyway" else 3
        for i in range(900):
            arm = i % arms
            u = rnd.uniform(0.06, 1)
            th = arm * TAU / arms + 3.2 * math.log(1 + 6 * u) + rnd.gauss(0, 0.18)
            rr = u * 500
            glow(cc, cx + math.cos(th) * rr, cy + math.sin(th) * rr, rnd.uniform(25, 60),
                 rnd.choice(["#5a7ad8", "#7a9aff", "#6a5ac8"]), 0.10)
        for i in range(14000):
            arm = i % arms
            u = rnd.uniform(0.03, 1) ** 0.9
            th = arm * TAU / arms + 3.2 * math.log(1 + 6 * u) + rnd.gauss(0, 0.30 * (1.15 - u))
            rr = u * 510 + rnd.gauss(0, 8)
            col = rnd.choice(["#cfe0ff", "#e8f0ff", "#aac8ff", "#ffffff"]) if u > 0.22 else "#ffe8c0"
            cc.drawCircle(cx + math.cos(th) * rr, cy + math.sin(th) * rr, rnd.uniform(0.6, 1.9),
                          P(col, a=rnd.uniform(0.3, 0.85)))
            if rnd.random() < 0.012:
                glow(cc, cx + math.cos(th) * rr, cy + math.sin(th) * rr, rnd.uniform(6, 16), "#ff6aa8", 0.5)
        for i in range(1500):
            ang = rnd.uniform(0, TAU)
            rr = abs(rnd.gauss(0, 60))
            cc.drawCircle(cx + math.cos(ang) * rr, cy + math.sin(ang) * rr, rnd.uniform(0.6, 1.6), P("#fff0d0", a=0.6))
        for i in range(6):
            glow(cc, cx, cy, 200 - i * 28, "#ffe6b8", 0.22)
        if kind == "milkyway":
            cc.save()
            cc.translate(cx, cy)
            cc.rotate(25)
            for k in range(-4, 5):
                glow(cc, k * 26, 0, 46, "#ffe6b8", 0.18)
            cc.restore()
    return d


def galaxy(c, x, y, R, t, kind="spiral", tilt=1.0, rot=0.0, spin=4.0, a=1.0, blur=1.2):
    img = masked(("gal", kind, blur), _gal_draw(kind), 1200, 1200, blur=blur, feather=0.12)
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(R / 520, R / 520 * tilt)
    c.rotate(t * spin)
    p = skia.Paint(AntiAlias=True)
    p.setAlphaf(clamp(a))
    p.setBlendMode(skia.BlendMode.kScreen)
    c.drawImage(img, -600, -600, skia.SamplingOptions(skia.FilterMode.kLinear), p)
    c.restore()


_GDOTS = [(random.Random(i).uniform(0, 1), random.Random(i + 99).uniform(0, 1), random.Random(i + 199).random())
          for i in range(1400)]


def galaxy_field(c, t, rect=(0, 0, W, H), hole=None, a=1.0, n=1400, drift=(0, 0), size=1.0, cols=None):
    """Thousands of tiny galaxies. hole=(x,y,r,k) empties a void (k = how empty, 0..1)."""
    x0, y0, x1, y1 = rect
    cols = cols or ("#cfe0ff", "#ffe2b8", "#ffc0e0")
    for i, (u, v, h) in enumerate(_GDOTS[:n]):
        x = x0 + ((u * (x1 - x0) + drift[0] * t) % (x1 - x0))
        y = y0 + ((v * (y1 - y0) + drift[1] * t) % (y1 - y0))
        aa = a
        if hole:
            hx, hy, hr, hk = hole
            d = math.hypot(x - hx, y - hy)
            if d < hr and h < 0.97:
                aa *= (1 - hk) + hk * smooth((d - hr * 0.85) / (hr * 0.15))
        if aa <= 0.01:
            continue
        r = (0.8 + 2.2 * h) * size
        col = cols[i % len(cols)]
        if h > 0.85:
            c.drawOval(skia.Rect(x - r * 2, y - r * 0.8, x + r * 2, y + r * 0.8), P(col, a=aa * 0.8))
        else:
            c.drawCircle(x, y, r, P(col, a=aa * (0.4 + 0.5 * h)))


_web_nodes = None


def _web():
    global _web_nodes
    if _web_nodes is None:
        rnd = random.Random(21)
        nodes = [(rnd.uniform(-200, W + 200), rnd.uniform(-200, H + 200)) for _ in range(70)]
        edges = []
        for i, (x, y) in enumerate(nodes):
            ds = sorted(((math.hypot(x - X, y - Y), j) for j, (X, Y) in enumerate(nodes) if j != i))
            for d, j in ds[:3]:
                if i < j:
                    edges.append((i, j))
        _web_nodes = (nodes, edges)
    return _web_nodes


def _web_draw(cc):
    cc.clear(C("#000000"))
    nodes, edges = _web()
    rnd = random.Random(4)
    for i, j in edges:
        (x1, y1), (x2, y2) = nodes[i], nodes[j]
        mx, my = (x1 + x2) / 2 + rnd.uniform(-40, 40), (y1 + y2) / 2 + rnd.uniform(-40, 40)
        pth = skia.Path()
        pth.moveTo(x1, y1)
        pth.quadTo(mx, my, x2, y2)
        cc.drawPath(pth, P("#5a6aff", 16, 0.12))
        cc.drawPath(pth, P("#b08aff", 5, 0.25))
        for k in range(26):
            u = k / 26
            px = (1 - u) ** 2 * x1 + 2 * (1 - u) * u * mx + u * u * x2 + rnd.gauss(0, 7)
            py = (1 - u) ** 2 * y1 + 2 * (1 - u) * u * my + u * u * y2 + rnd.gauss(0, 7)
            cc.drawCircle(px, py, rnd.uniform(0.8, 2.4), P("#e0d8ff", a=0.7))
    for (x, y) in nodes:
        glow(cc, x, y, 60, "#d0b0ff", 0.4)
        glow(cc, x, y, 18, "#ffffff", 0.7)


def cosmic_web(c, t, zoom=1.0, a=1.0):
    img = cached(("web",), _web_draw, blur=1.0)
    with xf(c, W / 2, H / 2, zoom, t * 0.6):
        p = skia.Paint(AntiAlias=True)
        p.setAlphaf(a)
        p.setBlendMode(skia.BlendMode.kScreen)
        c.drawImage(img, -W / 2, -H / 2, skia.SamplingOptions(skia.FilterMode.kLinear), p)


# ======================================================================= compact objects
def neutron_star(c, x, y, r, t, beams=1.0, spin=1.2, field=0.0, col="#bfe4ff", beam_len=900, tilt=25):
    if field > 0:
        c.save()
        c.translate(x, y)
        c.rotate(tilt + 6 * math.sin(t * 0.5))
        for k in range(1, 6):
            rr = r * (1.6 + k * 1.1)
            for side in (-1, 1):
                c.drawOval(skia.Rect(-rr if side < 0 else 0, -rr * 0.95, 0 if side < 0 else rr, rr * 0.95),
                           P("#8a7aff", 3, field * (0.55 - k * 0.07)))
        c.restore()
    if beams > 0:
        ang = math.radians(tilt) + math.sin(t * spin * TAU) * 0.0
        sweep = math.sin(t * spin) * 0.9
        for sgn in (-1, 1):
            a0 = -math.pi / 2 + sgn * 0.0 + sweep + (0 if sgn > 0 else math.pi)
            pth = skia.Path()
            pth.moveTo(x, y)
            pth.lineTo(x + math.cos(a0 - 0.08) * beam_len, y + math.sin(a0 - 0.08) * beam_len)
            pth.lineTo(x + math.cos(a0 + 0.08) * beam_len, y + math.sin(a0 + 0.08) * beam_len)
            pth.close()
            p = P("#bfe8ff", a=0.35 * beams)
            c.drawPath(pth, p)
            line(c, x, y, x + math.cos(a0) * beam_len, y + math.sin(a0) * beam_len, "#ffffff", 4, 0.6 * beams)
    glow(c, x, y, r * 5, col, 0.4)
    glow(c, x, y, r * 2, "#ffffff", 0.6)
    disc(c, x, y, r, radial(x - r * 0.3, y - r * 0.3, r * 1.4,
                                                                 ["#ffffff", col, "#6a9ad0"], [0, 0.5, 1]))


def comet(c, x, y, s, t, ang=200, a=1.0, tail=1.0):
    with xf(c, x, y, s, ang, alpha=a):
        for k, (col, wd, L, aa) in enumerate((("#7ad0ff", 90, 900, 0.22), ("#bfe8ff", 40, 700, 0.4),
                                              ("#ffffff", 12, 500, 0.6))):
            pth = skia.Path()
            pth.moveTo(0, -wd * 0.2)
            pth.quadTo(L * 0.5 * tail, -wd * 0.8, L * tail, -wd * (1 + 0.1 * math.sin(t * 2 + k)))
            pth.lineTo(L * tail, wd * (1 + 0.1 * math.sin(t * 2.3 + k)))
            pth.quadTo(L * 0.5 * tail, wd * 0.8, 0, wd * 0.2)
            pth.close()
            c.drawPath(pth, P(col, a=aa))
        pth = skia.Path()
        pth.moveTo(0, 0)
        pth.quadTo(300 * tail, 90, 620 * tail, 220)
        c.drawPath(pth, P("#ffe0a0", 26, 0.22))
        glow(c, 0, 0, 90, "#cfefff", 0.7)
        c.drawCircle(0, 0, 16, P("#e8f6ff"))


def nucleus(c, x, y, r, t, rot=0.0):
    """Icy comet core (lumpy potato)."""
    with xf(c, x, y, 1, rot + t * 6):
        pth = skia.Path()
        for i in range(24):
            ang = i / 24 * TAU
            rr = r * (1 + 0.12 * math.sin(ang * 3) + 0.06 * math.sin(ang * 7 + 1))
            px, py = math.cos(ang) * rr * 1.25, math.sin(ang) * rr
            (pth.moveTo if i == 0 else pth.lineTo)(px, py)
        pth.close()
        c.drawPath(pth, P("#4a5868"))
        c.drawPath(pth, P("#bfe8ff", 4, 0.6))
        rnd = random.Random(2)
        for i in range(10):
            c.drawCircle(rnd.uniform(-r, r), rnd.uniform(-r * 0.6, r * 0.6), r * rnd.uniform(0.06, 0.14),
                         P("#33404e"))
        for i in range(6):
            c.drawCircle(rnd.uniform(-r, r), rnd.uniform(-r * 0.6, r * 0.6), r * 0.05, P("#e8f6ff", a=0.8))


def hubble(c, x, y, s, t, rot=0.0):
    with xf(c, x, y, s, rot + 3 * math.sin(t * 0.4)):
        for sgn in (-1, 1):
            rrect(c, -60, sgn * 70 + (0 if sgn > 0 else -150), 120, 150, 6, "#1f3d6e")
            for k in range(4):
                line(c, -60 + k * 30, sgn * 70 + (0 if sgn > 0 else -150), -60 + k * 30,
                     sgn * 70 + (150 if sgn > 0 else 0), "#5c86c9", 2)
            line(c, 0, sgn * 40, 0, sgn * 70, "#9aa3b3", 6)
        rrect(c, -230, -50, 300, 100, 14, OUT)
        rrect(c, -226, -46, 292, 92, 12, "#c9ced8")
        for k in range(6):
            line(c, -200 + k * 45, -46, -200 + k * 45, 46, "#aeb5c2", 2)
        rrect(c, 60, -58, 150, 116, 14, OUT)
        rrect(c, 64, -54, 142, 108, 12, "#dfe4ec")
        c.drawOval(skia.Rect(196, -50, 224, 50), P("#2a3346"))


def observatory(c, x, y, s, t, open_=1.0):
    """Subaru-style dome on a mountain top (y = ground under dome)."""
    with xf(c, x, y, s):
        rrect(c, -160, -140, 320, 150, 10, "#c9ced8")
        rrect(c, -160, -140, 320, 150, 10, OUT, stroke=6)
        pth = skia.Path()
        pth.addArc(skia.Rect(-170, -310, 170, 30), 180, 180)
        pth.close()
        c.drawPath(pth, P("#e3e7ee"))
        c.drawPath(pth, P(OUT, 6))
        slit = 30 * open_
        c.drawRect(skia.Rect(-slit, -305, slit, -140), P("#0a1020"))
        glow(c, 0, -240, 60, "#9fd0ff", 0.25 * open_)


def mountain(c, base, peaks, col="#1a2233", rim_col=None):
    pth = skia.Path()
    pth.moveTo(-100, H + 50)
    for (x, y) in peaks:
        pth.lineTo(x, y)
    pth.lineTo(W + 100, H + 50)
    pth.close()
    c.drawPath(pth, P(col))
    if rim_col:
        pth2 = skia.Path()
        pth2.moveTo(*peaks[0])
        for (x, y) in peaks[1:]:
            pth2.lineTo(x, y)
        c.drawPath(pth2, P(rim_col, 4, 0.6))


def screen_fill(c, colors, pos=None):
    c.save()
    c.resetMatrix()
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, colors, pos))
    c.restore()


def surface(c, ground, col_top, col_bot, t=0.0, rocks=True, seed=1, scroll=0.0, hills=None):
    if hills:
        for (amp, base, col, sp) in hills:
            pth = skia.Path()
            pth.moveTo(-10, H)
            for i in range(0, W + 40, 40):
                yy = base - amp * (0.5 + 0.5 * math.sin((i + scroll * sp) * 0.004 + seed)) \
                     - amp * 0.3 * math.sin((i + scroll * sp) * 0.011 + seed * 2)
                pth.lineTo(i, yy)
            pth.lineTo(W + 40, H)
            pth.close()
            c.drawPath(pth, P(col))
    fill_shader(c, skia.Rect(0, ground, W, H), linear(0, ground, 0, H, [col_top, col_bot]))
    c.drawRect(skia.Rect(0, ground - 2, W, ground + 3), P(mixhex(col_top, "#ffffff", 0.25), a=0.6))
    if rocks:
        rnd = random.Random(seed)
        for i in range(26):
            x = (rnd.uniform(0, W + 400) - scroll) % (W + 400) - 200
            yy = ground + rnd.uniform(10, H - ground)
            r = rnd.uniform(6, 26) * (0.5 + (yy - ground) / (H - ground))
            c.drawOval(skia.Rect(x - r * 1.4, yy - r * 0.7, x + r * 1.4, yy + r * 0.3), P(mixhex(col_bot, "#000000", 0.35)))
            c.drawOval(skia.Rect(x - r * 1.2, yy - r * 0.75, x + r * 0.9, yy), P(mixhex(col_top, "#000000", 0.1)))


def clock(c, x, y, s, frac, col="#8ec8ff", label=None):
    with xf(c, x, y, s):
        c.drawCircle(0, 0, 100, P("#0d1624", a=0.85))
        c.drawCircle(0, 0, 100, P(col, 6))
        for i in range(12):
            a = i * TAU / 12
            line(c, math.sin(a) * 82, -math.cos(a) * 82, math.sin(a) * 92, -math.cos(a) * 92, col, 4)
        arc = skia.Path()
        arc.addArc(skia.Rect(-70, -70, 70, 70), -90, 360 * (frac % 1.0))
        c.drawPath(arc, P(col, 10, 0.4))
        ang = frac * TAU
        line(c, 0, 0, math.sin(ang) * 72, -math.cos(ang) * 72, "#ffffff", 6)
        c.drawCircle(0, 0, 9, P("#ffffff"))
    if label:
        text(c, label, x, y + 150 * s, 44 * s, col, "Bold", shadow=True)


def earth_icon(c, x, y, r, t=0.0):
    c.drawCircle(x, y, r, P("#2a6fd0"))
    c.drawOval(skia.Rect(x - r * 0.6, y - r * 0.5, x + r * 0.1, y + r * 0.2), P("#3f9a4a"))
    c.drawOval(skia.Rect(x + r * 0.1, y, x + r * 0.7, y + r * 0.6), P("#3f9a4a"))


def you_are_here(c, x, y, t, label="YOU ARE HERE", col="#ffd36b", a=1.0):
    pulse = (t * 0.8) % 1
    c.drawCircle(x, y, 10 + 40 * pulse, P(col, 3, a * (1 - pulse)))
    c.drawCircle(x, y, 8, P(col, a=a))
    if label:
        text(c, label, x, y - 30, 28, col, "Bold", a=a, shadow=True)
