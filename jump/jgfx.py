"""Style kit for "What If You Jumped on Every World?".

Re-uses the flat-vector primitives and the "you" character from ../video/gfx.py and adds:
  * a jump engine (crouch -> real ballistic arc -> landing squash) driven by real physics,
  * a world painter (sky, stars, sky-objects, curved ground, craters, haze) for 15 worlds,
  * measuring props (ruler, height tag, hoop, table, house, tower, stair step),
  * infographic widgets (gravity badge, stopwatch, planet icons, title cards).
"""
import math
import os
import random
import sys

import skia

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video"))
from gfx import (W, H, C, P, xf, rrect, poly, line, text, text_width, linear, radial, fill_shader,  # noqa: E402,F401
                 glow, sparkle, check_mark, cross_mark, mixhex, font, clamp, lerp, smooth, ease_out, back_out,
                 at, window, pill, card, bubble, draw_char, draw_head, CHARS, POSES, drop, thumbs_up, bell)

V0 = 3.0  # launch speed, m/s
G_EARTH = 9.81

CHARS["astro"] = dict(CHARS["you"], shirt="#eef1f5", pants="#d5dbe4", shoe="#7d8796", cap=None)
CHARS["kid"] = dict(CHARS["noor"])

# ---------------------------------------------------------------- worlds
# g = surface gravity as a fraction of Earth's.
WORLDS = {
    "earth": dict(name="EARTH", g=1.0, sky=("#3d8fe0", "#bfe4ff"), ground="#5aa64a", ground2="#3f8a37",
                  stars=0, icon=("#2f7fd8", "#4caf50"), haze="#ffffff", clouds=True),
    "moon": dict(name="THE MOON", g=0.165, sky=("#05060c", "#11131d"), ground="#a3a3ab", ground2="#7d7d86",
                 stars=1, icon=("#c9c9cf", "#8f8f98"), craters=True, skyobj=("earth", 1500, 210, 70)),
    "mars": dict(name="MARS", g=0.38, sky=("#c9774a", "#f0c79c"), ground="#c1592e", ground2="#9c4422",
                 stars=0, icon=("#d0623a", "#a3431f"), rocks=True, dust="#f3c393", skyobj=("sun_small", 1550, 200, 26)),
    "mercury": dict(name="MERCURY", g=0.38, sky=("#06060a", "#1d1410"), ground="#8f8379", ground2="#6c625a",
                    stars=1, icon=("#a39a92", "#7a716a"), craters=True, skyobj=("sun_big", 1500, 230, 150)),
    "venus": dict(name="VENUS", g=0.90, sky=("#b8742a", "#f3c66a"), ground="#7d4419", ground2="#5c2f10",
                  stars=0, icon=("#e8c06a", "#c99a45"), lava=True, haze="#ffcf70"),
    "jupiter": dict(name="JUPITER", g=2.53, sky=("#7a4a2a", "#e8c9a0"), ground="#d9b38a", ground2="#b88d62",
                    stars=0, icon=("#d9a676", "#a8673e"), cloudtop=True, bands=True),
    "saturn": dict(name="SATURN", g=1.07, sky=("#8a7650", "#f2e1b4"), ground="#e9d6a6", ground2="#cdb57f",
                   stars=0, icon=("#e8d39a", "#c4a866"), cloudtop=True, skyrings=True),
    "uranus": dict(name="URANUS", g=0.89, sky=("#3f9fae", "#b8f0f2"), ground="#9fe0e4", ground2="#79c7cd",
                   stars=0, icon=("#8fdde3", "#5fb9c2"), cloudtop=True),
    "neptune": dict(name="NEPTUNE", g=1.14, sky=("#16307e", "#4a78e0"), ground="#3e64c9", ground2="#2b4ba3",
                    stars=0, icon=("#3e6ee0", "#2446a8"), cloudtop=True, wind=True),
    "pluto": dict(name="PLUTO", g=0.063, sky=("#04050a", "#141826"), ground="#e9dccb", ground2="#c9b49e",
                  stars=1, icon=("#e3cdb3", "#b48a6a"), ice=True, skyobj=("charon", 1450, 230, 80)),
    "enceladus": dict(name="ENCELADUS", g=0.0115, sky=("#03050c", "#0e1426"), ground="#eef6ff", ground2="#c7dcf2",
                      stars=1, icon=("#f2f8ff", "#bcd3ee"), ice=True, geysers=True, skyobj=("saturn", 1460, 250, 150)),
    "ceres": dict(name="CERES", g=0.029, sky=("#040408", "#121218"), ground="#6d6a66", ground2="#55524f",
                  stars=1, icon=("#86827d", "#5d5a56"), craters=True, brightspots=True),
    "bennu": dict(name="BENNU", g=0.0000006, sky=("#020205", "#0a0a12"), ground="#4a4642", ground2="#36332f",
                  stars=1, icon=("#5a5550", "#3a3632"), rubble=True, curve=1.0),
    "sun": dict(name="THE SUN", g=28.0, sky=("#ff9a1f", "#ffe07a"), ground="#ff7a12", ground2="#e04e0a",
                stars=0, icon=("#ffcf3a", "#ff8a1a"), plasma=True),
    "neutron": dict(name="NEUTRON STAR", g=1.4e11, sky=("#05031a", "#1d1450"), ground="#b9c4ff", ground2="#8a93e6",
                    stars=1, icon=("#d6dcff", "#7d86ff"), neutron=True),
}


def jump_height(g):
    return V0 * V0 / (2 * g * G_EARTH)


def air_time(g):
    return 2 * V0 / (g * G_EARTH)


_rng = random.Random(42)
STARS = [(_rng.uniform(0, W), _rng.uniform(-900, 900), _rng.uniform(1.0, 3.2), _rng.uniform(0, 6.28))
         for _ in range(260)]


def planet_icon(c, x, y, r, key, t=0.0, a=1.0):
    """Little planet/world icon used on badges, maps and the recap chart."""
    w = WORLDS[key]
    c1, c2 = w["icon"]
    with xf(c, x, y, alpha=a):
        if key == "sun":
            glow(c, 0, 0, r * 2.2, "#ffb300", 0.55)
        if key == "neutron":
            glow(c, 0, 0, r * 2.6, "#8fa0ff", 0.6)
            for k in range(2):
                ang = t * 0.8 + k * math.pi
                line(c, math.cos(ang) * r * 0.2, -r * 2.4, -math.cos(ang) * r * 0.2, r * 2.4, "#cfd6ff", r * 0.12, 0.5)
        if key == "saturn":
            c.drawOval(skia.Rect(-r * 2.1, -r * 0.5, r * 2.1, r * 0.5), P("#d9c48e", r * 0.22, 0.9))
        c.save()
        clip = skia.Path()
        clip.addCircle(0, 0, r)
        c.clipPath(clip, doAntiAlias=True)
        fill_shader(c, skia.Rect(-r, -r, r, r), radial(-r * 0.35, -r * 0.4, r * 1.6, [c1, c2]))
        if key in ("jupiter", "saturn"):
            for k in range(-4, 5):
                yy = k * r * 0.24
                c.drawRect(skia.Rect(-r, yy, r, yy + r * 0.1), P(c2 if k % 2 else "#f4e3c4", a=0.55))
            if key == "jupiter":
                c.drawOval(skia.Rect(r * 0.1, r * 0.25, r * 0.6, r * 0.5), P("#c0502c", a=0.85))
        if key == "earth":
            for (dx, dy, rr) in ((-0.3, -0.2, 0.42), (0.35, 0.3, 0.3), (0.2, -0.5, 0.2)):
                c.drawCircle(dx * r, dy * r, rr * r, P("#4caf50"))
            c.drawOval(skia.Rect(-r * 0.6, -r * 0.95, r * 0.3, -r * 0.75), P("#ffffff", a=0.8))
        if key in ("moon", "mercury", "ceres", "pluto", "bennu"):
            rr = random.Random(hash(key) % 100)
            for _ in range(6):
                c.drawCircle(rr.uniform(-0.6, 0.6) * r, rr.uniform(-0.6, 0.6) * r, rr.uniform(0.08, 0.2) * r,
                             P(c2, a=0.8))
        if key == "pluto":
            c.drawCircle(r * 0.2, r * 0.25, r * 0.4, P("#f6efe4", a=0.9))
        if key == "mars":
            c.drawOval(skia.Rect(-r * 0.4, -r * 1.02, r * 0.4, -r * 0.8), P("#ffffff", a=0.8))
        if key == "neptune":
            c.drawOval(skia.Rect(-r * 0.4, -r * 0.1, r * 0.1, r * 0.2), P("#1a2a7a", a=0.8))
        if key == "enceladus":
            for k in range(4):
                line(c, -r * 0.5 + k * r * 0.2, r * 0.4, -r * 0.2 + k * r * 0.2, r * 0.8, "#6fb6ff", r * 0.06)
        # terminator shading
        fill_shader(c, skia.Rect(-r, -r, r, r),
                    radial(-r * 0.5, -r * 0.5, r * 2.2, [("#000000", 0), ("#000000", 0), ("#000000", 0.45)],
                           [0, 0.5, 1]))
        c.restore()
        if key == "saturn":
            p = skia.Path()
            p.addArc(skia.Rect(-r * 2.1, -r * 0.5, r * 2.1, r * 0.5), 0, 180)
            c.drawPath(p, P("#e9d6a6", r * 0.22, 0.95))


def draw_skyobj(c, spec, t):
    kind, x, y, r = spec
    if kind == "earth":
        glow(c, x, y, r * 1.8, "#5fb0ff", 0.3)
        planet_icon(c, x, y, r, "earth", t)
    elif kind == "sun_big":
        glow(c, x, y, r * 3.2, "#fff3c0", 0.7)
        c.drawCircle(x, y, r, P("#fffbe8"))
    elif kind == "sun_small":
        glow(c, x, y, r * 4, "#fff6dc", 0.6)
        c.drawCircle(x, y, r, P("#fffaf0"))
    elif kind == "charon":
        planet_icon(c, x, y, r, "moon", t)
    elif kind == "saturn":
        planet_icon(c, x, y, r * 0.55, "saturn", t)


def ground_y_at(x, gy, curve):
    if not curve:
        return gy
    R = 2600 / curve
    dx = x - W / 2
    return gy + (R - math.sqrt(max(R * R - dx * dx, 0)))


def world_bg(c, key, t, gy=860, sky_shift=0.0, shake=0.0):
    """Paint a whole world. `sky_shift` > 0 moves the view up (camera rising) by that many px."""
    w = WORLDS[key]
    top, bot = w["sky"]
    fill_shader(c, skia.Rect(0, -3000, W, H + 400), linear(0, -600 + sky_shift * 0.2, 0, gy + sky_shift, [top, bot]))
    if w.get("stars"):
        for (sx, sy, sr, ph) in STARS:
            yy = sy + sky_shift * 0.15
            a = 0.45 + 0.4 * math.sin(t * 1.6 + ph)
            c.drawCircle(sx, yy, sr, P("#ffffff", a=a))
    if w.get("skyobj"):
        kind, x, y, r = w["skyobj"]
        draw_skyobj(c, (kind, x, y + sky_shift * 0.3, r), t)
    if w.get("skyrings"):
        with xf(c, W * 0.5, 160 + sky_shift * 0.3, rot=-8):
            for k in range(5):
                c.drawOval(skia.Rect(-1500 - k * 60, -90 - k * 12, 1500 + k * 60, 90 + k * 12),
                           P("#fff1c8", 14, 0.25 - k * 0.04))
    if w.get("bands"):
        for k in range(6):
            yy = 120 + k * 95 + sky_shift * 0.25 + 8 * math.sin(t * 0.4 + k)
            c.drawRect(skia.Rect(0, yy, W, yy + 42), P("#f4dcb5" if k % 2 else "#a8673e", a=0.18))
    if w.get("wind"):
        for k in range(14):
            yy = 120 + k * 50 + sky_shift * 0.2
            xx = ((t * 900 + k * 377) % (W + 800)) - 400
            line(c, xx, yy, xx + 280, yy, "#cfe0ff", 4, 0.25)
    if w.get("plasma"):
        for k in range(10):
            ang = t * 0.5 + k
            x = (k * 211 + 80) % W
            hgt = 120 + 60 * math.sin(ang)
            p = skia.Path()
            p.moveTo(x - 60, gy)
            p.cubicTo(x - 50, gy - hgt * 1.4, x + 50, gy - hgt * 1.4, x + 60, gy)
            c.drawPath(p, P("#ffd04a", 10, 0.5))
    if w.get("neutron"):
        for k in range(5):
            glow(c, (k * 470 + t * 40) % W, 300 + 80 * math.sin(t + k), 260, "#6b5bff", 0.25)
    # ground
    curve = w.get("curve", 0.0)
    gyy = gy + sky_shift
    if curve:
        R = 2600 / curve
        c.drawCircle(W / 2, gyy + R, R, P(w["ground"]))
        c.drawCircle(W / 2, gyy + R + 30, R - 10, P(w["ground2"], a=0.4))
    elif w.get("cloudtop"):
        fill_shader(c, skia.Rect(0, gyy - 20, W, H + 600), linear(0, gyy, 0, H + 200, [w["ground"], w["ground2"]]))
        for k in range(16):
            xx = (k * 150 + t * 25) % (W + 300) - 150
            c.drawCircle(xx, gyy + 10 + 14 * math.sin(k), 90, P(w["ground"]))
            c.drawCircle(xx + 60, gyy + 50, 70, P(w["ground2"], a=0.5))
    else:
        fill_shader(c, skia.Rect(0, gyy, W, H + 600), linear(0, gyy, 0, H + 100, [w["ground"], w["ground2"]]))
        c.drawRect(skia.Rect(0, gyy, W, gyy + 8), P("#ffffff", a=0.12))
    rr = random.Random(hash(key) % 1000)
    if w.get("craters"):
        for _ in range(9):
            x = rr.uniform(0, W)
            y = gyy + rr.uniform(40, 220)
            s = rr.uniform(40, 120) * (0.5 + (y - gyy) / 300)
            c.drawOval(skia.Rect(x - s, y - s * 0.22, x + s, y + s * 0.22), P(w["ground2"]))
            c.drawOval(skia.Rect(x - s * 0.85, y - s * 0.16, x + s * 0.85, y + s * 0.2), P("#000000", a=0.18))
    if w.get("rocks") or w.get("rubble"):
        n = 30 if w.get("rubble") else 12
        for _ in range(n):
            x = rr.uniform(0, W)
            y = ground_y_at(x, gyy, curve) + rr.uniform(4, 200)
            s = rr.uniform(10, 40)
            c.drawOval(skia.Rect(x - s, y - s * 0.6, x + s, y + s * 0.4), P(w["ground2"]))
            c.drawOval(skia.Rect(x - s * 0.6, y - s * 0.55, x + s * 0.2, y - s * 0.2), P("#ffffff", a=0.12))
    if w.get("ice"):
        for _ in range(8):
            x = rr.uniform(0, W)
            y = gyy + rr.uniform(20, 200)
            p = skia.Path()
            p.moveTo(x, y)
            for k in range(4):
                x += rr.uniform(40, 120)
                y += rr.uniform(-10, 14)
                p.lineTo(x, y)
            c.drawPath(p, P("#5aa7ff" if key == "enceladus" else "#b09b84", 4, 0.6))
    if w.get("lava"):
        for _ in range(8):
            x = rr.uniform(0, W)
            y = gyy + rr.uniform(30, 200)
            p = skia.Path()
            p.moveTo(x, y)
            for k in range(3):
                x += rr.uniform(50, 140)
                y += rr.uniform(-16, 16)
                p.lineTo(x, y)
            c.drawPath(p, P("#ff8a2a", 6, 0.55 + 0.25 * math.sin(t * 3 + x)))
    if w.get("brightspots"):
        for x in (520, 1420):
            glow(c, x, gyy + 120, 60, "#ffffff", 0.5)
            c.drawOval(skia.Rect(x - 30, gyy + 112, x + 30, gyy + 128), P("#f4f4ff"))
    if w.get("plasma"):
        for k in range(30):
            x = (k * 97) % W
            y = gyy + 30 + (k * 53) % 200
            c.drawCircle(x, y, 26 + 6 * math.sin(t * 2 + k), P("#ffb43a", a=0.5))
    if w.get("neutron"):
        for k in range(12):
            x = (k * 173) % W
            line(c, x, gyy + 10, x + 160, gyy + 10, "#ffffff", 3, 0.3)
    if w.get("geysers"):
        for gx in (380, 1600):
            for k in range(26):
                ph = (t * 0.6 + k / 26) % 1.0
                yy = gyy - ph * 900
                xx = gx + math.sin(k * 1.7) * 40 * ph
                c.drawCircle(xx, yy, 6 + 30 * ph, P("#dff0ff", a=0.35 * (1 - ph)))
    if w.get("dust"):
        for k in range(30):
            x = (k * 131 + t * 60) % W
            y = gyy - 40 - (k * 37) % 400
            c.drawCircle(x, y, 3, P(w["dust"], a=0.35))
    if w.get("haze"):
        fill_shader(c, skia.Rect(0, gyy - 300, W, gyy + 100),
                    linear(0, gyy - 300, 0, gyy + 60, [(w["haze"], 0), (w["haze"], 0.25)]))


# ---------------------------------------------------------------- jumper
POSE_STAND = dict(la=(-8, 0), ra=(8, 0), ll=(4, 0), rl=(-4, 0))
POSE_CROUCH = dict(la=(-30, -15), ra=(30, 15), ll=(-42, 84), rl=(42, -84))
POSE_AIR = dict(la=(-165, 10), ra=(165, -10), ll=(-14, 30), rl=(14, -30))
POSE_FLOAT = dict(la=(-110, 40), ra=(110, -40), ll=(-22, 34), rl=(22, -34))
POSE_TPOSE = dict(la=(-90, 0), ra=(90, 0), ll=(10, 0), rl=(-10, 0))
POSE_STRAIN = dict(la=(-25, 40), ra=(25, -40), ll=(-48, 92), rl=(48, -92))
POSE_WALK = None


def mix_pose(p1, p2, k):
    k = clamp(k)
    return {key: (lerp(p1[key][0], p2[key][0], k), lerp(p1[key][1], p2[key][1], k)) for key in p1}


def leg_drop(pose, who="you"):
    d = CHARS[who]
    l1, l2 = d["leg"]
    best = 0
    for key in ("ll", "rl"):
        a1, a2 = pose[key]
        dy = l1 * math.cos(math.radians(a1)) + l2 * math.cos(math.radians(a1 + a2))
        best = max(best, dy)
    return best + 10


def person(c, x, gy, pose, who="you", expr="happy", t=0.0, s=1.0, tilt=0.0, look=(0, 0), helmet=None,
           shadow_h=0.0, lift=0.0, sweat=0.0, rim=None, squash=1.0):
    """Draw a person whose feet touch `gy` (+ lift px off the ground)."""
    if shadow_h is not None:
        k = 1 / (1 + shadow_h / 300)
        c.drawOval(skia.Rect(x - 70 * s * k, gy - 9 * s * k, x + 70 * s * k, gy + 9 * s * k), P("#000000", a=0.3 * k))
    hip = gy - lift - leg_drop(pose, who) * s * squash
    with xf(c, x, hip, sx=1.0, sy=squash):
        draw_char(c, 0, 0, who, pose, expr, t, s=s, tilt=tilt, look=look, sweat=sweat)
    if helmet:
        d = CHARS[who]
        hy = hip + (-d["torso"] - d["head"] * 0.95) * s * squash
        r = d["head"] * 1.45 * s
        c.drawCircle(x, hy, r, P("#bfe6ff", a=0.18))
        c.drawCircle(x, hy, r, P("#ffffff", 5 * s, 0.85))
        p = skia.Path()
        p.addArc(skia.Rect(x - r * 0.75, hy - r * 0.8, x + r * 0.75, hy + r * 0.6), 200, 60)
        c.drawPath(p, P("#ffffff", 6 * s, 0.6))
        if helmet == "pack":
            pass
    return hip


def head_y(gy, pose, who, s, lift=0.0):
    d = CHARS[who]
    return gy - lift - leg_drop(pose, who) * s - (d["torso"] + d["head"] * 1.95) * s


def jump_state(t, t0, T, crouch=0.35, land=0.3):
    """Return (pose, height_fraction 0..1, squash) for a jump that leaves the ground at t0 and lasts T."""
    if t < t0 - crouch:
        return POSE_STAND, 0.0, 1.0
    if t < t0:
        k = smooth((t - (t0 - crouch)) / crouch)
        return mix_pose(POSE_STAND, POSE_CROUCH, k), 0.0, 1.0
    if t < t0 + T:
        u = (t - t0) / T
        hf = 4 * u * (1 - u)
        k = clamp(u * 6)
        pose = mix_pose(POSE_CROUCH, POSE_AIR, k) if u < 0.5 else mix_pose(POSE_AIR, POSE_FLOAT, (u - 0.5) * 2)
        if u > 0.85:
            pose = mix_pose(pose, POSE_STAND, (u - 0.85) / 0.15)
        return pose, hf, 1.0 + 0.06 * (1 - abs(1 - 2 * u))
    if t < t0 + T + land:
        k = (t - t0 - T) / land
        return mix_pose(POSE_CROUCH, POSE_STAND, smooth(k)), 0.0, 1.0 - 0.06 * math.sin(k * math.pi)
    return POSE_STAND, 0.0, 1.0


def jumper(c, x, gy, t, t0, height_px, T, who="you", expr="happy", s=1.0, helmet=None, repeat=None,
           expr_air=None):
    """Person doing a real ballistic jump. If `repeat` is set, jumps again every `repeat` seconds."""
    tt = t
    if repeat and t > t0:
        n = int((t - t0) // repeat)
        tt = t - n * repeat
    pose, hf, sq = jump_state(tt, t0, T)
    lift = hf * height_px
    e = expr_air if (expr_air and hf > 0.05) else expr
    person(c, x, gy, pose, who, e, t, s, helmet=helmet, shadow_h=lift, lift=lift, squash=sq)
    return x, gy - lift, lift


# ---------------------------------------------------------------- measuring props
def height_tag(c, x, y_bottom, y_top, label, sub=None, color="#ffd34d", a=1.0, side=1):
    """Vertical dimension line with arrow heads and a label."""
    if a <= 0:
        return
    with xf(c, alpha=a):
        line(c, x, y_bottom, x, y_top, color, 6)
        for yy, d in ((y_bottom, 1), (y_top, -1)):
            c.drawPath(poly([(x - 16, yy + d * 20), (x + 16, yy + d * 20), (x, yy)]), P(color))
            line(c, x - 26, yy, x + 26, yy, color, 4)
        my = (y_bottom + y_top) / 2
        lx = x + side * 40
        al = "left" if side > 0 else "right"
        w = max(text_width(label, 64), text_width(sub, 40, "Bold") if sub else 0)
        bx = lx if side > 0 else lx - w - 40
        rrect(c, bx - 10, my - 58, w + 40, 84 + (52 if sub else 0), 20, "#0d1220", 0.75)
        text(c, label, bx + 10 + (0 if side > 0 else 0), my + 4, 64, color, align="left")
        if sub:
            text(c, sub, bx + 10, my + 56, 40, "#ffffff", weight="Bold", align="left")


def ruler(c, x, gy, ppm, max_m, step=1.0, a=1.0, label_every=1, unit="m"):
    with xf(c, alpha=a):
        top = gy - max_m * ppm
        rrect(c, x - 14, top - 10, 28, gy - top + 10, 8, "#ffffff", 0.85)
        m = 0.0
        i = 0
        while m <= max_m + 1e-6:
            y = gy - m * ppm
            big = i % label_every == 0
            line(c, x - 14, y, x + (14 if big else 2), y, "#1b1b2f", 4 if big else 2)
            if big:
                lab = f"{m:g} {unit}"
                text(c, lab, x - 26, y + 12, 32, "#ffffff", "Bold", align="right", shadow=True)
            m += step
            i += 1


def hoop(c, x, gy, ppm, a=1.0):
    rim = gy - 3.05 * ppm
    with xf(c, alpha=a):
        rrect(c, x + 60, rim - 1.1 * ppm, 16, 1.1 * ppm + (gy - rim), 6, "#5a6170")
        rrect(c, x - 10, rim - 1.05 * ppm, 1.8 * ppm * 0.5, 1.05 * ppm, 10, "#ffffff")
        rrect(c, x - 10, rim - 1.05 * ppm, 1.8 * ppm * 0.5, 1.05 * ppm, 10, "#c9ced8", stroke=6)
        c.drawOval(skia.Rect(x - 0.45 * ppm - 10, rim - 10, x - 10, rim + 10), P("#ff5a1f", 8))
        for k in range(5):
            xx = x - 0.45 * ppm - 4 + k * 0.1 * ppm
            line(c, xx, rim + 6, xx + 6, rim + 0.4 * ppm, "#ffffff", 3, 0.8)


def table_prop(c, x, gy, ppm, w_m=1.6, h_m=0.9, a=1.0):
    with xf(c, alpha=a):
        top = gy - h_m * ppm
        rrect(c, x - w_m * ppm / 2, top - 18, w_m * ppm, 26, 8, "#a8693c")
        for sx in (-1, 1):
            rrect(c, x + sx * (w_m * ppm / 2 - 30) - 9, top, 18, h_m * ppm, 5, "#7a4a28")
        # a mug and a plate for "kitchen"
        rrect(c, x - 40, top - 58, 40, 40, 8, "#ffffff")
        c.drawOval(skia.Rect(x + 30, top - 30, x + 130, top - 16), P("#e8eef5"))


def house(c, x, gy, ppm, stories=2, a=1.0, color="#e9b872"):
    h = stories * 2.6 * ppm
    w = 7 * ppm
    with xf(c, alpha=a):
        rrect(c, x - w / 2, gy - h, w, h, 6, color)
        c.drawPath(poly([(x - w / 2 - 20, gy - h), (x + w / 2 + 20, gy - h), (x, gy - h - 1.8 * ppm)]), P("#b5483a"))
        for st in range(stories):
            for k in (-1, 1):
                wx = x + k * w * 0.25
                wy = gy - (st + 0.6) * 2.6 * ppm
                rrect(c, wx - 0.6 * ppm, wy - 0.6 * ppm, 1.2 * ppm, 1.2 * ppm, 4, "#bfe6ff")
        rrect(c, x - 0.5 * ppm, gy - 2.1 * ppm, 1.0 * ppm, 2.1 * ppm, 4, "#7a4a28")


def tower(c, x, gy, ppm, stories, a=1.0, color="#7f8fa6", lit=0.0, w_m=12):
    sh = 3.0 * ppm
    w = w_m * ppm
    with xf(c, alpha=a):
        rrect(c, x - w / 2, gy - stories * sh, w, stories * sh, 6, color)
        for st in range(stories):
            for k in range(4):
                wx = x - w / 2 + w * (0.12 + k * 0.22)
                wy = gy - (st + 0.75) * sh
                on = ((st * 7 + k * 3) % 5) < 2
                col = "#ffe7a3" if (on and lit) else "#cfe3ff"
                c.drawRect(skia.Rect(wx, wy, wx + w * 0.12, wy + sh * 0.5), P(col, a=0.85))
        if stories >= 3:
            for st in range(1, stories + 1, max(1, stories // 5)):
                text(c, str(st), x + w / 2 + 22, gy - (st - 0.4) * sh, max(18, min(36, sh * 0.6)), "#ffffff",
                     "Bold", align="left", a=0.7)


def stair(c, x, gy, ppm, n=3, a=1.0):
    step_h = 0.2 * ppm
    step_w = 0.6 * ppm
    with xf(c, alpha=a):
        for k in range(n):
            rrect(c, x + k * step_w, gy - (k + 1) * step_h, step_w * (n - k), step_h + 2, 4,
                  mixhex("#cfc6b8", "#a89d8c", k / n))


# ---------------------------------------------------------------- UI widgets
def gravity_badge(c, key, t, start, x=60, y=60, a=1.0):
    w = WORLDS[key]
    k = back_out(at(t, start, 0.5))
    if k <= 0:
        return
    g = w["g"]
    if g >= 1000:
        gl = "×100,000,000,000"
    elif g >= 2:
        gl = f"{g:.1f}× EARTH"
    elif g >= 0.05:
        gl = f"{int(round(g * 100))}% OF EARTH"
    elif g >= 0.005:
        gl = f"{g * 100:.1f}% OF EARTH"
    else:
        gl = "≈ 0"
    with xf(c, x, y, s=0.7 + 0.3 * k, alpha=clamp(k) * a):
        card(c, 0, 0, 600, 150, "#0d1220", a=0.82, r=28)
        planet_icon(c, 80, 75, 46, key, t)
        text(c, w["name"], 150, 66, 46, "#ffffff", align="left")
        text(c, "GRAVITY: " + gl, 150, 116, 30, "#ffd34d", "Bold", align="left")


def title_card(c, t, start, key, sub=None, y=380):
    """Big world-name reveal with an icon pop."""
    k = back_out(at(t, start, 0.55))
    a = clamp(at(t, start, 0.3)) * clamp((start + 2.6 - t) / 0.4)
    if a <= 0:
        return
    w = WORLDS[key]
    with xf(c, W / 2, y, s=0.6 + 0.4 * k, alpha=a):
        planet_icon(c, 0, -110, 80, key, t)
        text(c, w["name"], 0, 60, 120, "#ffffff", outline="#0d1220", ow=18)
        text(c, w["name"], 0, 60, 120, "#ffffff")
        if sub:
            text(c, sub, 0, 130, 46, "#ffd34d", "Bold", outline="#0d1220", ow=10)
            text(c, sub, 0, 130, 46, "#ffd34d", "Bold")


def stopwatch(c, x, y, r, secs, label=None, color="#ffd34d", a=1.0, running=True):
    with xf(c, x, y, alpha=a):
        rrect(c, -r * 0.18, -r * 1.32, r * 0.36, r * 0.25, 6, "#d9dee6")
        c.drawCircle(0, 0, r + 10, P("#0d1220", a=0.85))
        c.drawCircle(0, 0, r, P("#ffffff"))
        frac = (secs % 1.0) if running else 0
        sweep = (secs / 4.0) * 360
        p = skia.Path()
        p.moveTo(0, 0)
        p.arcTo(skia.Rect(-r * 0.9, -r * 0.9, r * 0.9, r * 0.9), -90, min(sweep, 359.9), False)
        p.close()
        c.drawPath(p, P(color, a=0.55))
        for k in range(12):
            ang = math.radians(k * 30)
            line(c, math.sin(ang) * r * 0.8, -math.cos(ang) * r * 0.8, math.sin(ang) * r * 0.92,
                 -math.cos(ang) * r * 0.92, "#1b1b2f", 4)
        ang = math.radians(secs / 4.0 * 360)
        line(c, 0, 0, math.sin(ang) * r * 0.78, -math.cos(ang) * r * 0.78, "#e4572e", 7)
        c.drawCircle(0, 0, 9, P("#1b1b2f"))
        text(c, f"{secs:.1f} s", 0, r + 70, 54, "#ffffff", shadow=True)
        if label:
            text(c, label, 0, -r - 60, 40, color, "Bold", shadow=True)
        _ = frac


def arrow(c, x1, y1, x2, y2, color, w=14, a=1.0, head=34):
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - math.cos(ang) * head * 0.8, y2 - math.sin(ang) * head * 0.8
    line(c, x1, y1, bx, by, color, w, a)
    pts = [(x2, y2), (x2 - math.cos(ang - 0.45) * head, y2 - math.sin(ang - 0.45) * head),
           (x2 - math.cos(ang + 0.45) * head, y2 - math.sin(ang + 0.45) * head)]
    c.drawPath(poly(pts), P(color, a=a))


def grid_board(c, t, top="#0f1a2e", bottom="#16264a"):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, [top, bottom]))
    off = (t * 12) % 80
    for x in range(-80, W + 80, 80):
        line(c, x + off, 0, x + off, H, "#ffffff", 1.5, 0.05)
    for y in range(0, H + 80, 80):
        line(c, 0, y, W, y, "#ffffff", 1.5, 0.05)


def vignette(c, a=0.5):
    fill_shader(c, skia.Rect(0, 0, W, H),
                radial(W / 2, H / 2, W * 0.75, [("#000000", 0), ("#000000", 0), ("#000000", a)], [0, 0.55, 1]))


_grain = []


def grain(c, t, a=0.05):
    if not _grain:
        rnd = random.Random(5)
        for _k in range(4):
            s = skia.Surface(480, 270)
            cc = s.getCanvas()
            cc.clear(skia.ColorTRANSPARENT)
            for _ in range(4000):
                v = rnd.choice(("#ffffff", "#000000"))
                cc.drawRect(skia.Rect.MakeXYWH(rnd.uniform(0, 480), rnd.uniform(0, 270), 1, 1), P(v, a=0.9))
            _grain.append(s.makeImageSnapshot())
    img = _grain[int(t * 24) % 4]
    p = skia.Paint()
    p.setAlphaf(a)
    c.drawImageRect(img, skia.Rect(0, 0, W, H), skia.SamplingOptions(), p)
