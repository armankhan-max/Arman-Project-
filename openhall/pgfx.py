"""Photo-real props drawn in code + the stickman cast for "Is This Still Worth It?".

The style mixes two looks on purpose:
  * STICKMAN SCENES reuse the dark rim-lit kit from ../blackhole/sgfx.py (black heads, one outfit
    colour each, blurred sets behind sharp characters).
  * PRODUCT SHOTS are "photos" made entirely in code: a seamless studio sweep with a key light,
    objects shaded with multi-stop gradients, specular highlights, blurred contact shadows and a
    faint floor reflection. Whenever the narrator names a real object (a car, a phone, a receipt,
    a coffee cup...) we cut to one of these so the viewer sees the actual thing.
"""
import math
import os
import random
import sys

import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "blackhole"))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from sgfx import *  # noqa: E402,F401,F403
from sgfx import OUTFITS, POSES  # noqa: E402

# ------------------------------------------------------------------ cast
OUTFITS["sam"] = dict(suit="#2fa58f", suit2="#1d6e5f", trim="#f3eee3")      # the viewer ("you")
OUTFITS["clerk"] = dict(suit="#c0392b", suit2="#7f241b", trim="#f5d76e")    # cashier / salesperson
OUTFITS["chef"] = dict(suit="#e9edf3", suit2="#9aa3b3", trim="#e8742a")     # restaurant owner
OUTFITS["banker"] = dict(suit="#2c4a86", suit2="#1b2f58", trim="#e8c25a", glasses=True)
OUTFITS["courier"] = dict(suit="#f39c12", suit2="#b06f08", trim="#222222")

POSES.update({
    "think": dict(la=(-6, 0), ra=(150, 110), ll=(-3, 0), rl=(3, 0)),
    "hold2": dict(la=(60, 70), ra=(60, 70), ll=(-3, 0), rl=(3, 0)),
    "present": dict(la=(-6, 0), ra=(70, -40), ll=(-3, 0), rl=(3, 0)),
    "walk1": dict(la=(-25, 10), ra=(25, 10), ll=(-22, 15), rl=(22, 5)),
    "walk2": dict(la=(25, 10), ra=(-25, 10), ll=(22, 5), rl=(-22, 15)),
    "cheer": dict(la=(-150, -10), ra=(150, 10), ll=(-6, 0), rl=(6, 0)),
    "pushup": dict(la=(-6, 0), ra=(6, 0), ll=(-3, 0), rl=(3, 0)),
    "slump": dict(la=(20, 10), ra=(-20, -10), ll=(80, -85), rl=(75, -80)),
    "pay": dict(la=(-6, 0), ra=(85, 20), ll=(-3, 0), rl=(3, 0)),
    "wallet": dict(la=(40, 70), ra=(50, 60), ll=(-3, 0), rl=(3, 0)),
})


def walk(t, speed=7.0, amp=24):
    s = math.sin(t * speed)
    return dict(la=(-amp * s, 10), ra=(amp * s, 10), ll=(amp * s * 0.9, max(0, -s) * 25),
                rl=(-amp * s * 0.9, max(0, s) * 25))


# ------------------------------------------------------------------ photo primitives
def blur_paint(color, sigma, a=1.0):
    p = P(color, a=a)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma))
    return p


def soft_shadow(c, x, y, w, h, a=0.45, sigma=18):
    """Blurred elliptical contact shadow centred at (x, y)."""
    c.drawOval(skia.Rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2), blur_paint("#000000", sigma, a))


def studio(c, t, key="#e9e4da", rim="#b9b1a3", floor_y=760, light=(960, 380), warm=0.0):
    """Seamless photo-studio sweep: lit wall, curved floor, key-light falloff."""
    wall_hi = mixhex(key, "#ffe6c4", warm)
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, [rim, wall_hi, key, rim], [0, 0.45, 0.7, 1]))
    fill_shader(c, skia.Rect(0, 0, W, H),
                radial(light[0], light[1], 1100, [("#ffffff", 0.35), ("#ffffff", 0.0)]))
    # floor sweep
    fill_shader(c, skia.Rect(0, floor_y - 120, W, H),
                linear(0, floor_y - 120, 0, H, [(rim, 0.0), (rim, 0.35), ("#000000", 0.18)], [0, 0.45, 1]))
    fill_shader(c, skia.Rect(0, 0, W, H),
                radial(W / 2, H / 2, W * 0.8, [("#000000", 0), ("#000000", 0), ("#000000", 0.35)], [0, 0.55, 1]))


def dark_studio(c, t, tone="#1a2233", light=(960, 420)):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#07090e", tone, "#0a0d14"], [0, 0.6, 1]))
    fill_shader(c, skia.Rect(0, 0, W, H), radial(light[0], light[1], 900, [("#ffffff", 0.12), ("#ffffff", 0)]))


def reflect(c, draw, floor_y, a=0.18):
    """Draw `draw(c)` mirrored under floor_y with fading alpha (glossy floor reflection)."""
    c.save()
    c.clipRect(skia.Rect(0, floor_y, W, floor_y + 260))
    c.saveLayerAlpha(skia.Rect(0, floor_y, W, floor_y + 260), int(a * 255))
    c.translate(0, floor_y * 2)
    c.scale(1, -1)
    draw(c)
    c.restore()
    # fade
    fill_shader(c, skia.Rect(0, floor_y, W, floor_y + 260),
                linear(0, floor_y, 0, floor_y + 260, [("#000000", 0.0), ("#000000", 0.0)]))
    c.restore()


def spec(c, x, y, w, h, a=0.55, rot=0):
    with xf(c, x, y, rot=rot):
        fill_shader(c, skia.Rect(-w / 2, -h / 2, w / 2, h / 2),
                    linear(-w / 2, 0, w / 2, 0, [("#ffffff", 0), ("#ffffff", a), ("#ffffff", 0)]))


# ------------------------------------------------------------------ photo props
def photo_phone(c, x, y, s=1.0, rot=0.0, screen=None, t=0.0, color="#1c1d22", shadow=True):
    """Modern smartphone, 300x620 at s=1. `screen(c, w, h, t)` paints the display (origin top-left)."""
    w, h = 300, 620
    with xf(c, x, y, s, rot):
        if shadow:
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-w / 2 + 16, -h / 2 + 30, w / 2 + 16, h / 2 + 30), 52, 52),
                        blur_paint("#000000", 26, 0.45))
        body = skia.RRect.MakeRectXY(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), 50, 50)
        c.drawRRect(body, skia.Paint(AntiAlias=True, Shader=linear(-w / 2, 0, w / 2, 0,
                    [mixhex(color, "#ffffff", 0.35), color, mixhex(color, "#000000", 0.4), color,
                     mixhex(color, "#ffffff", 0.25)], [0, 0.08, 0.5, 0.92, 1])))
        inner = skia.RRect.MakeRectXY(skia.Rect(-w / 2 + 12, -h / 2 + 12, w / 2 - 12, h / 2 - 12), 40, 40)
        c.drawRRect(inner, P("#050507"))
        sc = skia.Rect(-w / 2 + 18, -h / 2 + 18, w / 2 - 18, h / 2 - 18)
        c.save()
        c.clipRRect(skia.RRect.MakeRectXY(sc, 34, 34), skia.ClipOp.kIntersect, True)
        c.translate(sc.left(), sc.top())
        if screen:
            screen(c, sc.width(), sc.height(), t)
        else:
            fill_shader(c, skia.Rect(0, 0, sc.width(), sc.height()),
                        linear(0, 0, sc.width(), sc.height(), ["#1d3b6b", "#5a2d7a", "#d9566b"]))
        c.restore()
        # island + glass reflection
        rrect(c, -48, -h / 2 + 30, 96, 26, 13, "#000000")
        c.save()
        c.clipRRect(inner, skia.ClipOp.kIntersect, True)
        c.drawPath(poly([(-w / 2, -h / 2), (w * 0.05, -h / 2), (-w / 2, h * 0.15)]), P("#ffffff", a=0.07))
        c.restore()
        # side buttons
        rrect(c, w / 2 - 2, -h * 0.22, 6, 70, 3, mixhex(color, "#ffffff", 0.2))
        rrect(c, -w / 2 - 4, -h * 0.28, 6, 40, 3, mixhex(color, "#ffffff", 0.2))
        rrect(c, -w / 2 - 4, -h * 0.18, 6, 60, 3, mixhex(color, "#ffffff", 0.2))


def app_screen_delivery(c, w, h, t):
    c.drawRect(skia.Rect(0, 0, w, h), P("#f6f3ee"))
    c.drawRect(skia.Rect(0, 0, w, 120), P("#ff5a3c"))
    text(c, "Order food", 24, 80, 30, "#ffffff", "Black", align="left")
    for i, (nm, col, pr) in enumerate((("Burger", "#c97a2c", "$19.80"), ("Pizza", "#d64933", "$24.10"),
                                       ("Noodles", "#e0a83a", "$17.60"))):
        y = 150 + i * 135
        rrect(c, 16, y, w - 32, 118, 16, "#ffffff")
        rrect(c, 28, y + 12, 94, 94, 12, col)
        c.drawCircle(75, y + 59, 30, P("#ffffff", a=0.25))
        text(c, nm, 138, y + 50, 26, "#222222", "Bold", align="left")
        text(c, pr, 138, y + 88, 24, "#ff5a3c", "Black", align="left")
    rrect(c, 24, h - 100, w - 48, 70, 35, "#ff5a3c")
    text(c, "Checkout", w / 2, h - 54, 28, "#ffffff", "Black")


def app_screen_home(c, w, h, t, icons=None):
    fill_shader(c, skia.Rect(0, 0, w, h), linear(0, 0, w, h, ["#203a6b", "#4b2f7a", "#c2506a"]))
    text(c, "9:41", w / 2, 70, 30, "#ffffff", "SemiBold")
    cols = icons or ["#ff5a3c", "#2ecc71", "#3498db", "#f1c40f", "#9b59b6", "#e74c3c", "#1abc9c", "#e67e22",
                     "#34495e", "#ff7aa8", "#16a085", "#c0392b"]
    for i, col in enumerate(cols):
        gx, gy = i % 4, i // 4
        x, y = 22 + gx * ((w - 44) / 4), 120 + gy * 110
        rrect(c, x + 6, y, 56, 56, 15, col)
        rrect(c, x + 6, y, 56, 28, 15, "#ffffff", 0.12)


def photo_car(c, x, y, s=1.0, color="#c4161c", t=0.0, wheel_rot=0.0, shine=1.0, old=False, shadow=True):
    """Side-view sedan, ~900 px long at s=1, (x, y) = ground contact centre."""
    body_hi = mixhex(color, "#ffffff", 0.45)
    body_lo = mixhex(color, "#000000", 0.55)
    with xf(c, x, y, s):
        if shadow:
            soft_shadow(c, 0, 0, 900, 60, 0.6, 16)
        # lower body
        b = skia.Path()
        b.moveTo(-440, -60)
        b.cubicTo(-450, -120, -430, -170, -380, -180)
        b.lineTo(-210, -200)
        b.cubicTo(-150, -290, -90, -305, 30, -305)
        b.cubicTo(140, -305, 200, -280, 270, -205)
        b.lineTo(390, -185)
        b.cubicTo(445, -175, 455, -130, 450, -70)
        b.lineTo(445, -45)
        b.lineTo(-435, -45)
        b.close()
        c.drawPath(b, skia.Paint(AntiAlias=True, Shader=linear(0, -305, 0, -45,
                   [body_hi, color, color, body_lo], [0, 0.35, 0.62, 1])))
        # windows
        wpath = skia.Path()
        wpath.moveTo(-180, -205)
        wpath.cubicTo(-130, -280, -80, -290, 20, -290)
        wpath.lineTo(25, -205)
        wpath.close()
        wpath2 = skia.Path()
        wpath2.moveTo(45, -205)
        wpath2.lineTo(40, -290)
        wpath2.cubicTo(130, -290, 180, -270, 240, -205)
        wpath2.close()
        for wp in (wpath, wpath2):
            c.drawPath(wp, skia.Paint(AntiAlias=True, Shader=linear(0, -290, 0, -205,
                       ["#2a3442", "#0e1218"])))
        c.drawPath(poly([(-120, -205), (-60, -285), (-20, -285), (-80, -205)]), P("#ffffff", a=0.10 * shine))
        c.drawPath(poly([(90, -205), (130, -285), (150, -285), (110, -205)]), P("#ffffff", a=0.08 * shine))
        line(c, 32, -290, 32, -205, body_lo, 12)
        # body line + specular streak along the shoulder
        line(c, -420, -150, 430, -140, mixhex(color, "#000000", 0.3), 3)
        spec(c, 0, -178, 760, 10, 0.55 * shine)
        line(c, 30, -200, 30, -55, mixhex(color, "#000000", 0.35), 3)
        rrect(c, -40, -150, 40, 8, 4, "#d8d8d8")
        rrect(c, 170, -150, 40, 8, 4, "#d8d8d8")
        # lights
        c.drawPath(poly([(420, -165), (452, -150), (450, -120), (418, -128)]), P("#fff3c4"))
        glow(c, 440, -140, 40, "#fff3c4", 0.4)
        c.drawPath(poly([(-440, -150), (-412, -165), (-410, -128), (-442, -120)]), P("#d32f2f"))
        # bumpers
        rrect(c, -445, -85, 70, 30, 12, mixhex(color, "#000000", 0.45))
        rrect(c, 380, -85, 72, 30, 12, mixhex(color, "#000000", 0.45))
        # wheels
        for wx in (-265, 280):
            c.drawCircle(wx, -55, 92, P(mixhex(color, "#000000", 0.75)))
            c.drawCircle(wx, -55, 78, P("#121214"))
            c.drawCircle(wx, -55, 76, skia.Paint(AntiAlias=True, Shader=radial(wx - 10, -70, 80,
                         ["#2b2b30", "#0b0b0d"])))
            c.drawCircle(wx, -55, 50, skia.Paint(AntiAlias=True, Shader=radial(wx - 12, -70, 55,
                         ["#f2f2f4", "#a6a9b0", "#5c6068"])))
            with xf(c, wx, -55, rot=wheel_rot):
                for k in range(5):
                    with xf(c, 0, 0, rot=k * 72):
                        rrect(c, -7, -46, 14, 38, 6, "#3a3d44", 0.85)
            c.drawCircle(wx, -55, 11, P("#c8cbd2"))
        if old:
            # a few honest scuffs: a little less gloss
            spec(c, 0, -178, 760, 10, 0.15)


def photo_cup(c, x, y, s=1.0, t=0.0, steam=True, sleeve="#8b5a2b", cup="#f4f1ea", label=None):
    """Paper coffee cup with lid and sleeve, ~360 px tall at s=1. (x, y) = base centre."""
    with xf(c, x, y, s):
        soft_shadow(c, 20, 0, 260, 40, 0.5, 14)
        body = poly([(-105, -330), (105, -330), (80, 0), (-80, 0)])
        c.drawPath(body, skia.Paint(AntiAlias=True, Shader=linear(-105, 0, 105, 0,
                   [mixhex(cup, "#000000", 0.25), cup, "#ffffff", cup, mixhex(cup, "#000000", 0.35)],
                   [0, 0.25, 0.4, 0.7, 1])))
        sl = poly([(-98, -230), (98, -230), (88, -95), (-88, -95)])
        c.drawPath(sl, skia.Paint(AntiAlias=True, Shader=linear(-100, 0, 100, 0,
                   [mixhex(sleeve, "#000000", 0.35), sleeve, mixhex(sleeve, "#ffffff", 0.25), sleeve,
                    mixhex(sleeve, "#000000", 0.4)], [0, 0.25, 0.42, 0.7, 1])))
        if label:
            text(c, label, 0, -150, 30, "#f4e9d8", "Black")
        # lid
        rrect(c, -120, -365, 240, 40, 14, "#2a2a2e")
        fill_shader(c, skia.Rect(-120, -365, 120, -325), linear(-120, 0, 120, 0,
                    [("#ffffff", 0.0), ("#ffffff", 0.25), ("#ffffff", 0.0)]))
        c.drawPath(poly([(-95, -365), (95, -365), (80, -392), (-80, -392)]), P("#333338"))
        rrect(c, 10, -392, 36, 10, 5, "#111114")
        if steam:
            for i in range(3):
                pp = skia.Path()
                bx = -40 + i * 40
                pp.moveTo(bx, -400)
                for k in range(1, 9):
                    pp.lineTo(bx + 12 * math.sin(t * 2.2 + k * 0.8 + i * 2), -400 - k * 22)
                c.drawPath(pp, blur_paint("#ffffff", 4, 0.28))


def photo_mug(c, x, y, s=1.0, t=0.0, color="#f5f5f2"):
    with xf(c, x, y, s):
        soft_shadow(c, 10, 0, 260, 40, 0.5, 14)
        rrect(c, 70, -210, 90, 140, 50, mixhex(color, "#000000", 0.25), stroke=26)
        body = skia.RRect.MakeRectXY(skia.Rect(-110, -260, 110, 0), 26, 26)
        c.drawRRect(body, skia.Paint(AntiAlias=True, Shader=linear(-110, 0, 110, 0,
                    [mixhex(color, "#000000", 0.3), color, "#ffffff", color, mixhex(color, "#000000", 0.35)],
                    [0, 0.25, 0.42, 0.7, 1])))
        c.drawOval(skia.Rect(-110, -278, 110, -244), P(mixhex(color, "#000000", 0.15)))
        c.drawOval(skia.Rect(-96, -272, 96, -250), P("#3b2314"))
        for i in range(2):
            pp = skia.Path()
            bx = -25 + i * 50
            pp.moveTo(bx, -285)
            for k in range(1, 8):
                pp.lineTo(bx + 10 * math.sin(t * 2 + k + i * 2), -285 - k * 20)
            c.drawPath(pp, blur_paint("#ffffff", 4, 0.25))


def photo_receipt(c, x, y, s=1.0, lines=(), total=None, rot=0.0, reveal=1.0, title="RECEIPT"):
    """Thermal paper receipt. lines = [(label, amount, alpha, highlight)]."""
    w, h = 460, 150 + 70 * len(lines) + (110 if total else 0)
    with xf(c, x, y, s, rot):
        c.drawRect(skia.Rect(-w / 2 + 18, -h / 2 + 26, w / 2 + 18, h / 2 + 26), blur_paint("#000000", 20, 0.4))
        p = skia.Path()
        p.moveTo(-w / 2, -h / 2)
        p.lineTo(w / 2, -h / 2)
        n = 18
        for i in range(n + 1):
            xx = w / 2 - i * w / n
            p.lineTo(xx, h / 2 + (10 if i % 2 else 0))
        p.close()
        c.drawPath(p, skia.Paint(AntiAlias=True, Shader=linear(0, -h / 2, 0, h / 2,
                   ["#fbfaf6", "#f1eee6", "#e8e3d8"])))
        fill_shader(c, skia.Rect(-w / 2, -h / 2, w / 2, h / 2),
                    linear(-w / 2, 0, w / 2, 0, [("#000000", 0.06), ("#000000", 0), ("#000000", 0.08)]))
        text(c, title, 0, -h / 2 + 70, 40, "#2b2b2b", "Black")
        for k in range(-w // 2 + 30, w // 2 - 30, 18):
            line(c, k, -h / 2 + 100, k + 9, -h / 2 + 100, "#9b968c", 3)
        for i, ln in enumerate(lines):
            lab, amt, a, hi = (list(ln) + [1.0, False])[:4]
            if a <= 0:
                continue
            yy = -h / 2 + 160 + i * 70
            if hi:
                rrect(c, -w / 2 + 18, yy - 42, (w - 36) * clamp(a), 58, 6, "#ffe14d", 0.75)
            text(c, lab, -w / 2 + 34, yy, 32, "#2b2b2b", "Bold", align="left", a=clamp(a * 2))
            text(c, amt, w / 2 - 34, yy, 32, "#2b2b2b", "Bold", align="right", a=clamp(a * 2))
        if total:
            yy = h / 2 - 50
            for k in range(-w // 2 + 30, w // 2 - 30, 18):
                line(c, k, yy - 60, k + 9, yy - 60, "#9b968c", 3)
            text(c, "TOTAL", -w / 2 + 34, yy, 40, "#111111", "Black", align="left", a=total[1])
            text(c, total[0], w / 2 - 34, yy, 40, "#d0021b", "Black", align="right", a=total[1])


def photo_card(c, x, y, s=1.0, rot=0.0, color=("#1d2b53", "#3a5ba8"), name="DEBIT", chip=True):
    """Bank card, 540x340 at s=1."""
    w, h = 540, 340
    with xf(c, x, y, s, rot):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-w / 2 + 14, -h / 2 + 24, w / 2 + 14, h / 2 + 24), 28, 28),
                    blur_paint("#000000", 20, 0.45))
        r = skia.RRect.MakeRectXY(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), 26, 26)
        c.drawRRect(r, skia.Paint(AntiAlias=True, Shader=linear(-w / 2, -h / 2, w / 2, h / 2, list(color))))
        c.save()
        c.clipRRect(r, skia.ClipOp.kIntersect, True)
        c.drawCircle(w * 0.35, -h * 0.6, 300, P("#ffffff", a=0.07))
        c.drawCircle(w * 0.5, h * 0.4, 220, P("#ffffff", a=0.05))
        c.drawPath(poly([(-w / 2, -h / 2), (-w * 0.1, -h / 2), (-w / 2, h * 0.2)]), P("#ffffff", a=0.08))
        c.restore()
        if chip:
            rrect(c, -w / 2 + 50, -40, 80, 62, 10, "#d9b45a")
            fill_shader(c, skia.Rect(-w / 2 + 50, -40, -w / 2 + 130, 22),
                        linear(-w / 2 + 50, -40, -w / 2 + 130, 22, ["#f3dc8c", "#b48a2c"]))
            for k in (-20, 0):
                line(c, -w / 2 + 50, k, -w / 2 + 130, k, "#8f6d22", 2)
            line(c, -w / 2 + 90, -40, -w / 2 + 90, 22, "#8f6d22", 2)
        text(c, "4821  0193  5527  0846", -w / 2 + 50, 80, 32, "#ffffff", "SemiBold", align="left", a=0.9)
        text(c, name, -w / 2 + 50, h / 2 - 34, 26, "#ffffff", "Bold", align="left", a=0.75)
        c.drawCircle(w / 2 - 95, h / 2 - 50, 30, P("#ff5f00", a=0.9))
        c.drawCircle(w / 2 - 60, h / 2 - 50, 30, P("#f9a01b", a=0.85))


def photo_tshirt(c, x, y, s=1.0, color="#3d6ec9", worn=0.0, rot=0.0, tag=None):
    """Folded-flat t-shirt product shot, ~520 wide at s=1. worn 0..1 fades + adds pills/holes."""
    col = mixhex(color, "#9a9a9a", worn * 0.6)
    with xf(c, x, y, s, rot):
        soft_shadow(c, 14, 300, 520, 50, 0.45, 18)
        p = skia.Path()
        p.moveTo(-90, -280)
        p.quadTo(0, -230, 90, -280)
        p.lineTo(250, -210)
        p.lineTo(300, -60)
        p.lineTo(195, -25)
        p.lineTo(190, 290)
        p.lineTo(-190, 290)
        p.lineTo(-195, -25)
        p.lineTo(-300, -60)
        p.lineTo(-250, -210)
        p.close()
        c.drawPath(p, skia.Paint(AntiAlias=True, Shader=linear(-300, -280, 300, 290,
                   [mixhex(col, "#ffffff", 0.25), col, mixhex(col, "#000000", 0.3)])))
        c.save()
        c.clipPath(p, skia.ClipOp.kIntersect, True)
        for k, (fx, fy, fw) in enumerate(((-120, 60, 140), (60, 160, 120), (20, -40, 90))):
            spec(c, fx, fy, fw, 18, 0.18, rot=-20 + k * 15)
        line(c, -195, -25, -150, 280, mixhex(col, "#000000", 0.25), 4, 0.6)
        if worn > 0:
            r = random.Random(4)
            for _ in range(int(60 * worn)):
                c.drawCircle(r.uniform(-180, 180), r.uniform(-200, 280), r.uniform(2, 5), P("#ffffff", a=0.25))
            c.drawOval(skia.Rect(60, 180, 100, 205), P("#151515", a=worn))
            line(c, -175, 240, -120, 250, "#151515", 3, worn)
        c.restore()
        neck = skia.Path()
        neck.moveTo(-90, -280)
        neck.quadTo(0, -210, 90, -280)
        c.drawPath(neck, P(mixhex(col, "#000000", 0.35), 14))
        if tag:
            with xf(c, 150, -150, rot=12):
                line(c, -30, -50, 0, 0, "#555555", 2)
                rrect(c, -10, 0, 120, 70, 8, "#fdfbf5")
                c.drawCircle(4, 14, 6, P("#555555"))
                text(c, tag, 50, 48, 32, "#c0392b", "Black")


def photo_box(c, x, y, s=1.0, color="#c9a46c", label="", rot=0.0, printcol="#3a2a1a"):
    """Cardboard product box (3/4 view). (x, y) = bottom front centre. 420x320 front."""
    with xf(c, x, y, s, rot):
        soft_shadow(c, 40, 0, 560, 50, 0.5, 16)
        fw, fh, d = 420, 320, 110
        front = poly([(-fw / 2, 0), (fw / 2, 0), (fw / 2, -fh), (-fw / 2, -fh)])
        side = poly([(fw / 2, 0), (fw / 2 + d, -d * 0.6), (fw / 2 + d, -fh - d * 0.6), (fw / 2, -fh)])
        top = poly([(-fw / 2, -fh), (fw / 2, -fh), (fw / 2 + d, -fh - d * 0.6), (-fw / 2 + d, -fh - d * 0.6)])
        c.drawPath(front, skia.Paint(AntiAlias=True, Shader=linear(0, -fh, 0, 0, [mixhex(color, "#ffffff", 0.15),
                   color])))
        c.drawPath(side, P(mixhex(color, "#000000", 0.32)))
        c.drawPath(top, P(mixhex(color, "#ffffff", 0.3)))
        c.drawRect(skia.Rect(-20, -fh - 1, 20, -fh * 0.55), P("#d8c49a", a=0.8))
        if label:
            text(c, label, 0, -fh * 0.42, 44, printcol, "Black")


def photo_tv(c, x, y, s=1.0, screen=None, t=0.0):
    """Flat TV on a stand, 900x520 screen. (x, y) = centre of screen."""
    w, h = 900, 520
    with xf(c, x, y, s):
        soft_shadow(c, 0, h / 2 + 120, 520, 40, 0.5, 14)
        c.drawPath(poly([(-60, h / 2), (60, h / 2), (110, h / 2 + 115), (-110, h / 2 + 115)]), P("#24262b"))
        rrect(c, -180, h / 2 + 105, 360, 16, 8, "#1a1b1f")
        rrect(c, -w / 2 - 14, -h / 2 - 14, w + 28, h + 28, 14, "#101114")
        sc = skia.Rect(-w / 2, -h / 2, w / 2, h / 2)
        c.save()
        c.clipRect(sc)
        c.translate(-w / 2, -h / 2)
        if screen:
            screen(c, w, h, t)
        else:
            c.drawRect(skia.Rect(0, 0, w, h), P("#05070b"))
        c.restore()
        c.drawPath(poly([(-w / 2, -h / 2), (-w * 0.05, -h / 2), (-w / 2, h * 0.3)]), P("#ffffff", a=0.05))


def photo_jar(c, x, y, s=1.0, fill=0.5, t=0.0, label="EMERGENCY FUND"):
    """Glass jar with coins + notes. (x, y) = base centre, ~420 tall."""
    with xf(c, x, y, s):
        soft_shadow(c, 0, 0, 340, 46, 0.5, 14)
        jar = skia.RRect.MakeRectXY(skia.Rect(-150, -380, 150, 0), 50, 50)
        c.save()
        c.clipRRect(jar, skia.ClipOp.kIntersect, True)
        c.drawRect(skia.Rect(-150, -380, 150, 0), P("#cfe3ea", a=0.18))
        top = lerp(0, -340, fill)
        r = random.Random(11)
        coins = []
        for i in range(160):
            cx, cy = r.uniform(-140, 140), r.uniform(-340, 0)
            coins.append((cy, cx, r.uniform(26, 36), r.choice(("#d4a838", "#c9c9cf", "#b5803a"))))
        for cy, cx, cr, col in sorted(coins):
            if cy < top:
                continue
            c.drawOval(skia.Rect(cx - cr, cy - cr * 0.45, cx + cr, cy + cr * 0.45),
                       skia.Paint(AntiAlias=True, Shader=linear(cx - cr, cy, cx + cr, cy,
                                  [mixhex(col, "#ffffff", 0.4), col, mixhex(col, "#000000", 0.4)])))
        c.restore()
        c.drawRRect(jar, P("#ffffff", 5, 0.45))
        spec(c, -95, -190, 34, 300, 0.45)
        spec(c, 110, -190, 14, 260, 0.25)
        rrect(c, -130, -420, 260, 52, 12, "#8a8f98")
        fill_shader(c, skia.Rect(-130, -420, 130, -368), linear(0, -420, 0, -368, ["#d5d9df", "#6c717a"]))
        rrect(c, -120, -250, 240, 90, 6, "#f4ecd8")
        text(c, label, 0, -195, 26 if len(label) > 10 else 34, "#3a2a1a", "Black")


def photo_bill(c, x, y, s=1.0, rot=0.0, amount="100", a=1.0):
    """Generic banknote (not a real currency design), 520x230."""
    with xf(c, x, y, s, rot, alpha=a):
        c.drawRect(skia.Rect(-250, -100, 270, 130), blur_paint("#000000", 12, 0.35))
        r = skia.Rect(-260, -115, 260, 115)
        c.drawRect(r, skia.Paint(AntiAlias=True, Shader=linear(-260, -115, 260, 115,
                   ["#cfe3c8", "#a9cfa0", "#d8ead1"])))
        c.drawRect(skia.Rect(-245, -100, 245, 100), P("#4f7f4a", 3, 0.7))
        c.drawCircle(0, 0, 70, P("#7fae78", a=0.5))
        c.drawCircle(0, 0, 70, P("#4f7f4a", 3, 0.7))
        text(c, amount, -190, -55, 46, "#2f5a2b", "Black")
        text(c, amount, 190, 92, 46, "#2f5a2b", "Black")
        text(c, "$", 0, 26, 76, "#2f5a2b", "Black")


def photo_coin(c, x, y, r=40, col="#d4a838", a=1.0):
    with xf(c, x, y, alpha=a):
        c.drawCircle(4, 6, r, blur_paint("#000000", 6, 0.35))
        c.drawCircle(0, 0, r, skia.Paint(AntiAlias=True, Shader=radial(-r * 0.3, -r * 0.3, r * 1.4,
                     [mixhex(col, "#ffffff", 0.55), col, mixhex(col, "#000000", 0.45)], [0, 0.5, 1])))
        c.drawCircle(0, 0, r * 0.78, P(mixhex(col, "#000000", 0.25), 3))
        text(c, "$", 0, r * 0.32, r * 0.9, mixhex(col, "#000000", 0.35), "Black")


def photo_dumbbell(c, x, y, s=1.0, rot=0.0, dust=0.0):
    with xf(c, x, y, s, rot):
        soft_shadow(c, 0, 90, 700, 40, 0.5, 14)
        rrect(c, -260, -16, 520, 32, 14, "#b7bcc4")
        fill_shader(c, skia.Rect(-260, -16, 260, 16), linear(0, -16, 0, 16, ["#f4f6f8", "#9aa0a8", "#55595f"]))
        for sx in (-1, 1):
            for k, (ww, hh) in enumerate(((60, 200), (50, 170))):
                xx = sx * (140 + k * 62)
                rrect(c, xx - ww / 2, -hh / 2, ww, hh, 14, "#1c1d21")
                fill_shader(c, skia.Rect(xx - ww / 2, -hh / 2, xx + ww / 2, hh / 2),
                            linear(xx - ww / 2, 0, xx + ww / 2, 0,
                                   [("#ffffff", 0.0), ("#ffffff", 0.18), ("#ffffff", 0.0)]))
            rrect(c, sx * 262 - 14, -30, 28, 60, 6, "#8c9199")
        if dust:
            r = random.Random(2)
            for _ in range(120):
                c.drawCircle(r.uniform(-300, 300), r.uniform(-100, -5), r.uniform(1, 3), P("#d9d2c2", a=0.5 * dust))
            c.drawRect(skia.Rect(-300, -105, 300, 0), P("#cfc6b4", a=0.12 * dust))


def photo_bottle(c, x, y, s=1.0, cap="#ffffff", body="#ffffff", label_col="#c0392b", name="BRAND", sub="",
                 plain=False, rot=0.0):
    """Pill bottle, 220x380. (x, y) = base centre."""
    with xf(c, x, y, s, rot):
        soft_shadow(c, 10, 0, 260, 34, 0.5, 12)
        bd = skia.RRect.MakeRectXY(skia.Rect(-110, -320, 110, 0), 28, 28)
        c.drawRRect(bd, skia.Paint(AntiAlias=True, Shader=linear(-110, 0, 110, 0,
                    [mixhex(body, "#000000", 0.3), body, "#ffffff", body, mixhex(body, "#000000", 0.35)],
                    [0, 0.22, 0.38, 0.7, 1])))
        rrect(c, -100, -380, 200, 70, 14, cap)
        fill_shader(c, skia.Rect(-100, -380, 100, -310), linear(-100, 0, 100, 0,
                    [("#000000", 0.25), ("#ffffff", 0.2), ("#000000", 0.3)]))
        for k in range(-90, 100, 14):
            line(c, k, -375, k, -315, "#000000", 2, 0.12)
        rrect(c, -105, -260, 210, 190, 6, "#f7f7f7" if plain else label_col)
        if plain:
            rrect(c, -105, -260, 210, 34, 6, label_col)
        text(c, name, 0, -190 if not plain else -170, 40 if len(name) < 7 else 30,
             "#ffffff" if not plain else "#333333", "Black")
        if sub:
            text(c, sub, 0, -120, 26, "#ffffff" if not plain else "#333333", "Bold")
        spec(c, -60, -160, 30, 290, 0.35)


def photo_pack(c, x, y, s=1.0, color="#e74c3c", name="", plain=False, kind="box", rot=0.0):
    """Supermarket product: cereal box ('box') or detergent jug ('jug'). (x, y) = base centre."""
    with xf(c, x, y, s, rot):
        soft_shadow(c, 10, 0, 300, 30, 0.5, 12)
        if kind == "box":
            r = skia.Rect(-120, -420, 120, 0)
            c.drawRect(r, skia.Paint(AntiAlias=True, Shader=linear(-120, 0, 120, 0,
                       [mixhex(color, "#000000", 0.25), color, mixhex(color, "#ffffff", 0.2),
                        mixhex(color, "#000000", 0.3)], [0, 0.3, 0.55, 1])))
            if plain:
                c.drawRect(skia.Rect(-120, -300, 120, -150), P("#ffffff", a=0.9))
                text(c, name, 0, -210, 34, "#333333", "Black")
                c.drawCircle(0, -80, 46, P("#ffffff", a=0.5))
            else:
                c.drawCircle(0, -300, 85, P("#ffd23f"))
                c.drawCircle(0, -300, 70, P(mixhex(color, "#000000", 0.2)))
                text(c, name, 0, -282, 40, "#ffffff", "Black")
                for i in range(5):
                    c.drawCircle(-60 + i * 30, -110 + (i % 2) * 20, 22, P("#f5c26b"))
                c.drawPath(poly([(60, -200), (110, -230), (100, -170)]), P("#ffffff"))
                text(c, "NEW!", 70, -160, 22, "#ffd23f", "Black")
            spec(c, -40, -210, 40, 400, 0.18)
        else:
            p = skia.Path()
            p.moveTo(-110, 0)
            p.lineTo(-110, -260)
            p.quadTo(-110, -320, -40, -330)
            p.lineTo(-40, -380)
            p.lineTo(20, -380)
            p.lineTo(20, -330)
            p.quadTo(110, -320, 110, -260)
            p.lineTo(110, 0)
            p.close()
            c.drawPath(p, skia.Paint(AntiAlias=True, Shader=linear(-110, 0, 110, 0,
                       [mixhex(color, "#000000", 0.3), color, mixhex(color, "#ffffff", 0.35), color,
                        mixhex(color, "#000000", 0.35)], [0, 0.25, 0.4, 0.7, 1])))
            rrect(c, -50, -410, 80, 36, 8, "#ffffff" if plain else "#ffd23f")
            rrect(c, -85, -230, 170, 170, 14, "#ffffff", 0.92 if plain else 0.15)
            text(c, name, 0, -140, 34 if len(name) < 7 else 26, "#333333" if plain else "#ffffff", "Black")
            if not plain:
                for i in range(6):
                    c.drawCircle(-60 + i * 25, -90, 12, P("#ffffff", a=0.6))


def photo_statement(c, x, y, s=1.0, rows=(), rot=0.0, title="ACCOUNT STATEMENT", mark=None, t=0.0):
    """Paper bank statement. rows = [(date, desc, amount)]. mark = {row_index: (progress, color)}."""
    w = 760
    h = 220 + 62 * len(rows)
    mark = mark or {}
    with xf(c, x, y, s, rot):
        c.drawRect(skia.Rect(-w / 2 + 20, -h / 2 + 30, w / 2 + 20, h / 2 + 30), blur_paint("#000000", 22, 0.4))
        c.drawRect(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), skia.Paint(AntiAlias=True,
                   Shader=linear(0, -h / 2, 0, h / 2, ["#ffffff", "#f3f1ec"])))
        c.drawRect(skia.Rect(-w / 2, -h / 2, w / 2, -h / 2 + 90), P("#1d2b53"))
        text(c, title, -w / 2 + 36, -h / 2 + 58, 34, "#ffffff", "Black", align="left")
        text(c, "DATE", -w / 2 + 36, -h / 2 + 140, 22, "#7a7f8c", "Bold", align="left")
        text(c, "DESCRIPTION", -w / 2 + 170, -h / 2 + 140, 22, "#7a7f8c", "Bold", align="left")
        text(c, "AMOUNT", w / 2 - 36, -h / 2 + 140, 22, "#7a7f8c", "Bold", align="right")
        for i, (d, desc, amt) in enumerate(rows):
            yy = -h / 2 + 200 + i * 62
            if i in mark:
                pr, col = mark[i]
                if pr > 0:
                    rrect(c, -w / 2 + 20, yy - 40, (w - 40) * clamp(pr), 54, 6, col, 0.55)
            line(c, -w / 2 + 30, yy + 18, w / 2 - 30, yy + 18, "#e2dfd8", 2)
            text(c, d, -w / 2 + 36, yy, 26, "#333333", "SemiBold", align="left")
            text(c, desc, -w / 2 + 170, yy, 26, "#222222", "SemiBold", align="left")
            text(c, amt, w / 2 - 36, yy, 26, "#c0392b" if amt.startswith("-") else "#222222", "Bold", align="right")


def photo_burger(c, x, y, s=1.0):
    with xf(c, x, y, s):
        soft_shadow(c, 0, 10, 420, 46, 0.5, 14)
        c.drawOval(skia.Rect(-200, -60, 200, 10), skia.Paint(AntiAlias=True,
                   Shader=linear(0, -60, 0, 10, ["#d9a05b", "#9c5f25"])))
        c.drawRect(skia.Rect(-205, -110, 205, -60), skia.Paint(AntiAlias=True,
                   Shader=linear(0, -110, 0, -60, ["#5a2e16", "#3a1c0c"])))
        c.drawPath(poly([(-210, -110), (210, -110), (180, -88), (120, -100), (60, -82), (0, -100),
                         (-60, -84), (-130, -100), (-185, -86)]), P("#f4b41a"))
        p = skia.Path()
        p.moveTo(-215, -118)
        for i in range(13):
            xx = -215 + i * 36
            p.quadTo(xx + 18, -150 + (i % 2) * 18, xx + 36, -122)
        p.close()
        c.drawPath(p, P("#4caf50"))
        c.drawRect(skia.Rect(-190, -140, 190, -120), P("#d63b2f"))
        dome = skia.Path()
        dome.moveTo(-205, -140)
        dome.cubicTo(-200, -300, 200, -300, 205, -140)
        dome.close()
        c.drawPath(dome, skia.Paint(AntiAlias=True, Shader=radial(-60, -240, 300,
                   ["#f0be74", "#d48a3a", "#9c5a1d"], [0, 0.55, 1])))
        r = random.Random(9)
        for _ in range(26):
            sx, sy = r.uniform(-150, 150), r.uniform(-250, -170)
            with xf(c, sx, sy, rot=r.uniform(-40, 40)):
                c.drawOval(skia.Rect(-7, -3.5, 7, 3.5), P("#fbf1d5"))
        spec(c, -70, -230, 120, 30, 0.35, rot=-18)


def photo_bag(c, x, y, s=1.0, color="#ff5a3c", label="DELIVERY"):
    """Paper takeaway bag. (x, y) = base centre."""
    with xf(c, x, y, s):
        soft_shadow(c, 20, 0, 380, 40, 0.5, 14)
        c.drawPath(poly([(-150, 0), (150, 0), (140, -380), (-140, -380)]), skia.Paint(AntiAlias=True,
                   Shader=linear(-150, 0, 150, 0, ["#9c7b55", "#c9a678", "#dcbd92", "#a9865c"],
                                 [0, 0.3, 0.55, 1])))
        c.drawPath(poly([(-140, -380), (140, -380), (128, -410), (-128, -410)]), P("#b8956a"))
        rrect(c, -95, -260, 190, 120, 14, color)
        text(c, label, 0, -186, 30, "#ffffff", "Black")
        pp = skia.Path()
        pp.moveTo(-60, -405)
        pp.quadTo(0, -490, 60, -405)
        c.drawPath(pp, P("#7d5e3c", 10))


def photo_door(c, x, y, s=1.0, open_=0.0):
    with xf(c, x, y, s):
        c.drawRect(skia.Rect(-210, -700, 210, 0), P("#2a1d14"))
        c.drawRect(skia.Rect(-190, -680, 190, 0), P("#0d0a08"))
        fill_shader(c, skia.Rect(-190, -680, 190, 0), radial(0, -300, 400, [("#ffe9b8", 0.6 * open_),
                                                                              ("#ffe9b8", 0)]))
        w = 380 * (1 - 0.75 * open_)
        c.drawRect(skia.Rect(-190, -680, -190 + w, 0), skia.Paint(AntiAlias=True,
                   Shader=linear(-190, 0, -190 + w, 0, ["#7b4a2a", "#9a6238", "#6a3f22"])))
        for yy in (-620, -360):
            c.drawRect(skia.Rect(-170, yy, -190 + w - 20, yy + 220), P("#000000", 3, 0.25))
        c.drawCircle(-190 + w - 40, -340, 14, P("#d8b45a"))


# ------------------------------------------------------------------ dark-stickman sets (blurred, cached)
def _floor(c, y=800, col="#141b26"):
    c.drawRect(skia.Rect(0, y, W, H), P(col))
    c.drawRect(skia.Rect(0, y, W, y + 4), P("#ffffff", a=0.05))


def set_home(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#1a2333", "#141b28"]))
    # window with city night
    rrect(c, 1180, 160, 520, 420, 10, "#0b1220")
    for i in range(40):
        r = random.Random(i)
        bx, bh = 1200 + r.uniform(0, 470), r.uniform(80, 300)
        c.drawRect(skia.Rect(bx, 580 - bh, bx + 40, 580), P("#1a2740"))
        for k in range(4):
            c.drawRect(skia.Rect(bx + 8, 590 - bh + k * 40, bx + 16, 598 - bh + k * 40), P("#f3c86b", a=0.6))
    c.drawRect(skia.Rect(1435, 160, 1445, 580), P("#2b3446"))
    c.drawRect(skia.Rect(1180, 365, 1700, 375), P("#2b3446"))
    # lamp + shelf + frame
    glow(c, 260, 380, 300, "#ffcf8a", 0.25)
    rrect(c, 200, 300, 120, 90, 20, "#e9c98a")
    c.drawRect(skia.Rect(256, 390, 264, 800), P("#2b3446"))
    rrect(c, 520, 220, 220, 160, 8, "#2b3446")
    rrect(c, 535, 235, 190, 130, 4, "#3d5a80")
    _floor(c, 800, "#121925")
    # couch
    rrect(c, 560, 600, 800, 120, 40, "#3a3f5c")
    rrect(c, 520, 660, 880, 150, 40, "#454b6b")
    rrect(c, 500, 640, 90, 170, 40, "#3a3f5c")
    rrect(c, 1330, 640, 90, 170, 40, "#3a3f5c")


def set_street(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#20304a", "#3a4d6b"]))
    for i, (x, w, h, col) in enumerate(((0, 380, 600, "#1c2638"), (400, 300, 520, "#232f45"),
                                        (720, 460, 650, "#1b2536"), (1200, 320, 560, "#26324a"),
                                        (1540, 380, 620, "#1c2638"))):
        c.drawRect(skia.Rect(x, 800 - h, x + w, 800), P(col))
        r = random.Random(i)
        for k in range(16):
            wx, wy = x + 30 + (k % 4) * (w - 60) / 4, 800 - h + 40 + (k // 4) * 110
            c.drawRect(skia.Rect(wx, wy, wx + 40, wy + 60), P("#f3c86b", a=0.5 if r.random() > 0.4 else 0.08))
    _floor(c, 800, "#2b2f38")
    c.drawRect(skia.Rect(0, 800, W, 830), P("#4a4f5a"))


def set_store(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#e8edf2", "#c9d2db"]))
    for k in range(4):
        y = 140 + k * 150
        c.drawRect(skia.Rect(0, y + 110, W, y + 124), P("#8a96a3"))
        r = random.Random(k)
        x = 20
        while x < W:
            w = r.uniform(50, 110)
            h = r.uniform(60, 108)
            c.drawRect(skia.Rect(x, y + 110 - h, x + w - 8, y + 110), P(r.choice(
                ("#e74c3c", "#3498db", "#f1c40f", "#2ecc71", "#9b59b6", "#e67e22", "#ecf0f1"))))
            x += w
    _floor(c, 800, "#b3bcc6")


def set_gym(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#1d2230", "#262c3c"]))
    for i in range(5):
        x = 120 + i * 360
        c.drawRect(skia.Rect(x, 100, x + 260, 520), P("#2f3648"))
        c.drawRect(skia.Rect(x + 10, 110, x + 250, 510), P("#3f4a63", a=0.6))
    _floor(c, 800, "#171b25")
    for i in range(4):
        x = 200 + i * 440
        rrect(c, x, 620, 260, 30, 10, "#3b4252")
        c.drawRect(skia.Rect(x + 30, 650, x + 50, 800), P("#3b4252"))
        c.drawRect(skia.Rect(x + 210, 650, x + 230, 800), P("#3b4252"))
        rrect(c, x - 30, 560, 40, 160, 10, "#11141b")
        rrect(c, x + 250, 560, 40, 160, 10, "#11141b")


def set_cafe(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#3b2a20", "#2a1d16"]))
    for i in range(6):
        x = 150 + i * 300
        glow(c, x, 180, 160, "#ffcf8a", 0.35)
        c.drawCircle(x, 180, 26, P("#ffdca0"))
        line(c, x, 0, x, 160, "#1a120d", 4)
    rrect(c, 1100, 260, 640, 280, 10, "#1e1611")
    for k in range(3):
        text(c, ("LATTE", "MOCHA", "FLAT WHITE")[k], 1160, 340 + k * 70, 40, "#f4e9d8", "Bold", align="left",
             a=0.7)
        text(c, "$5.40", 1680, 340 + k * 70, 40, "#f4e9d8", "Bold", align="right", a=0.7)
    _floor(c, 800, "#21170f")
    rrect(c, 0, 640, 760, 170, 10, "#5a3e2b")


def set_bank(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#1b2638", "#121a28"]))
    for i in range(7):
        x = 80 + i * 270
        c.drawRect(skia.Rect(x, 120, x + 60, 800), P("#26344d"))
        c.drawRect(skia.Rect(x - 10, 110, x + 70, 140), P("#2f3f5c"))
    c.drawPath(poly([(0, 110), (W, 110), (W / 2, 10)]), P("#22304a"))
    _floor(c, 800, "#0f1520")
    rrect(c, 900, 620, 1020, 190, 8, "#3b2a1d")
    c.drawRect(skia.Rect(900, 620, 1920, 640), P("#5a4130"))


def set_park(c, t=0.0):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#4b7bb5", "#a8c9e6", "#e8d9b0"], [0, 0.6, 1]))
    for i in range(7):
        x = 80 + i * 300
        c.drawCircle(x, 520, 180, P("#2f6b3a"))
        c.drawCircle(x + 90, 470, 150, P("#3d8048"))
        c.drawRect(skia.Rect(x - 12, 560, x + 12, 800), P("#4a3424"))
    c.drawRect(skia.Rect(0, 760, W, H), P("#5c9b4a"))
    c.drawRect(skia.Rect(0, 820, W, 880), P("#cdb98f"))


SETS = dict(home=set_home, street=set_street, store=set_store, gym=set_gym, cafe=set_cafe, bank=set_bank,
            park=set_park)


def bg(c, name, blur=8.0, a=1.0, dim=0.0):
    img = cached(("wiset", name, blur), SETS[name], blur)
    blit(c, img, 0, 0, a)
    if dim:
        tint(c, "#000000", dim)


# ------------------------------------------------------------------ titles, charts and UI
ACC = "#ffcf3f"   # gold accent = money
RED = "#ff4d4d"
GRN = "#2ecc71"
CYN = "#5bd6ff"


def number_card(c, t, start, num, title, sub=None, accent=ACC):
    """Chapter card: huge outlined number + title, slides in. Returns progress."""
    k = ease_out(at(t, start, 0.55))
    k2 = ease_out(at(t, start + 0.15, 0.55))
    with xf(c, 0, 0, alpha=k):
        f = font(420, "Black")
        s = f"{num:02d}"
        wv = f.measureText(s)
        x0 = 330 - (1 - k) * 120
        c.drawString(s, x0 - wv / 2, 690, f, P(accent, 10, 0.95))
        c.drawString(s, x0 - wv / 2 + 14, 704, f, P(accent, a=0.18))
    with xf(c, (1 - k2) * 80, 0, alpha=k2):
        text(c, f"NUMBER {num}", 640, 430, 40, accent, "Black", align="left")
        lines = title if isinstance(title, (list, tuple)) else [title]
        fs = min(92.0, 92.0 * 640 / max(text_width(ln, 92) for ln in lines))
        for i, ln in enumerate(lines):
            text(c, ln, 636, 530 + i * 96, fs, "#ffffff", "Black", align="left", shadow=True)
        rrect(c, 640, 560 + (len(lines) - 1) * 96 + 20, 300 * k2, 10, 5, accent)
        if sub:
            text(c, sub, 640, 560 + (len(lines) - 1) * 96 + 90, 38, "#c9d3e3", "SemiBold", align="left")
    return k


def money(x, dec=0):
    if dec:
        return f"${x:,.{dec}f}"
    return f"${int(round(x)):,}"


def big_number(c, x, y, s, size=160, color=ACC, a=1.0, sc=1.0, sub=None, subcol="#c9d3e3"):
    with xf(c, x, y, sc, alpha=a):
        text(c, s, 0, size * 0.35, size, color, "Black", shadow=True)
        if sub:
            text(c, sub, 0, size * 0.35 + 70, 40, subcol, "Bold")


def bar(c, x, y, w, h, color, a=1.0, label=None, value=None, lcol="#c9d3e3"):
    """Bar growing upward from baseline y."""
    if h > 1:
        rrect(c, x - w / 2, y - h, w, h, min(14, w / 4), color, a)
        fill_shader(c, skia.Rect(x - w / 2, y - h, x + w / 2, y), linear(x - w / 2, 0, x + w / 2, 0,
                    [("#ffffff", 0.16 * a), ("#ffffff", 0.0)]))
    if label:
        text(c, label, x, y + 50, 34, lcol, "Bold", a=a)
    if value:
        text(c, value, x, y - h - 22, 46, "#ffffff", "Black", a=a)


def chart_frame(c, x0, y0, x1, y1, a=1.0):
    line(c, x0, y1, x1, y1, "#ffffff", 3, 0.35 * a)
    line(c, x0, y0, x0, y1, "#ffffff", 3, 0.35 * a)
    for k in range(1, 4):
        yy = lerp(y1, y0, k / 4)
        line(c, x0, yy, x1, yy, "#ffffff", 1, 0.08 * a)


def plot_line(c, pts, prog, color, w=10, a=1.0, dot=True):
    """pts in screen coords; draw first `prog` fraction."""
    if prog <= 0 or len(pts) < 2:
        return None
    n = len(pts) - 1
    upto = prog * n
    p = skia.Path()
    p.moveTo(*pts[0])
    last = pts[0]
    for i in range(1, len(pts)):
        if i <= upto:
            p.lineTo(*pts[i])
            last = pts[i]
        else:
            f = upto - (i - 1)
            if f > 0:
                last = (lerp(pts[i - 1][0], pts[i][0], f), lerp(pts[i - 1][1], pts[i][1], f))
                p.lineTo(*last)
            break
    c.drawPath(p, P(color, w + 10, 0.15 * a))
    c.drawPath(p, P(color, w, a))
    if dot:
        c.drawCircle(last[0], last[1], w * 1.3, P(color, a=a))
        c.drawCircle(last[0], last[1], w * 0.6, P("#ffffff", a=a))
    return last


def stamp(c, x, y, s, label, color=RED, k=1.0, rot=-12):
    if k <= 0:
        return
    sc = lerp(2.2, 1.0, ease_out(k))
    with xf(c, x, y, sc, rot, alpha=clamp(k * 2)):
        w = text_width(label, 84 * s) + 70
        h = 140 * s
        rrect(c, -w / 2, -h / 2, w, h, 16, color, stroke=10)
        text(c, label, 0, 30 * s, 84 * s, color, "Black")


def icon_tile(c, x, y, size, color, glyph, a=1.0, s=1.0):
    """App-style rounded tile with a simple glyph."""
    with xf(c, x, y, s, alpha=a):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-size / 2 + 6, -size / 2 + 12, size / 2 + 6, size / 2 + 12),
                    size * 0.24, size * 0.24), blur_paint("#000000", 10, 0.35))
        r = skia.RRect.MakeRectXY(skia.Rect(-size / 2, -size / 2, size / 2, size / 2), size * 0.24, size * 0.24)
        c.drawRRect(r, skia.Paint(AntiAlias=True, Shader=linear(0, -size / 2, 0, size / 2,
                    [mixhex(color, "#ffffff", 0.25), color, mixhex(color, "#000000", 0.25)])))
        glyph_draw(c, glyph, size)


def glyph_draw(c, g, size):
    u = size / 100
    wcol = "#ffffff"
    if g == "play":
        c.drawPath(poly([(-16 * u, -24 * u), (28 * u, 0), (-16 * u, 24 * u)]), P(wcol))
    elif g == "music":
        c.drawCircle(-12 * u, 18 * u, 11 * u, P(wcol))
        c.drawCircle(18 * u, 12 * u, 11 * u, P(wcol))
        line(c, -2 * u, 18 * u, -2 * u, -24 * u, wcol, 6 * u)
        line(c, 28 * u, 12 * u, 28 * u, -30 * u, wcol, 6 * u)
        line(c, -2 * u, -24 * u, 28 * u, -30 * u, wcol, 8 * u)
    elif g == "cloud":
        for cx, cy, r in ((-14, 4, 18), (6, -6, 22), (24, 6, 15)):
            c.drawCircle(cx * u, cy * u, r * u, P(wcol))
        c.drawRect(skia.Rect(-30 * u, 4 * u, 38 * u, 20 * u), P(wcol))
    elif g == "box":
        c.drawPath(poly([(-26 * u, -10 * u), (0, -24 * u), (26 * u, -10 * u), (26 * u, 20 * u), (0, 32 * u),
                         (-26 * u, 20 * u)]), P(wcol))
        line(c, -26 * u, -10 * u, 0, 4 * u, "#000000", 3 * u, 0.3)
        line(c, 26 * u, -10 * u, 0, 4 * u, "#000000", 3 * u, 0.3)
        line(c, 0, 4 * u, 0, 32 * u, "#000000", 3 * u, 0.3)
    elif g == "news":
        rrect(c, -26 * u, -28 * u, 52 * u, 56 * u, 6 * u, wcol)
        for k in range(4):
            line(c, -16 * u, (-14 + k * 12) * u, 16 * u, (-14 + k * 12) * u, "#000000", 4 * u, 0.35)
    elif g == "game":
        rrect(c, -32 * u, -16 * u, 64 * u, 34 * u, 16 * u, wcol)
        c.drawCircle(16 * u, 0, 5 * u, P("#000000", a=0.4))
        line(c, -20 * u, 0, -6 * u, 0, "#000000", 5 * u, 0.4)
        line(c, -13 * u, -7 * u, -13 * u, 7 * u, "#000000", 5 * u, 0.4)
    elif g == "fit":
        line(c, -24 * u, 0, 24 * u, 0, wcol, 7 * u)
        for sx in (-1, 1):
            rrect(c, sx * 22 * u - 6 * u, -16 * u, 12 * u, 32 * u, 4 * u, wcol)
    elif g == "lock":
        rrect(c, -22 * u, -4 * u, 44 * u, 34 * u, 6 * u, wcol)
        rrect(c, -14 * u, -28 * u, 28 * u, 36 * u, 14 * u, wcol, stroke=7 * u)
    elif g == "star":
        pts = []
        for i in range(10):
            r = (28 if i % 2 == 0 else 12) * u
            ang = -math.pi / 2 + i * math.pi / 5
            pts.append((math.cos(ang) * r, math.sin(ang) * r))
        c.drawPath(poly(pts), P(wcol))
    elif g == "car":
        rrect(c, -30 * u, -4 * u, 60 * u, 20 * u, 8 * u, wcol)
        c.drawPath(poly([(-18 * u, -4 * u), (-10 * u, -20 * u), (12 * u, -20 * u), (20 * u, -4 * u)]), P(wcol))
        c.drawCircle(-16 * u, 18 * u, 7 * u, P("#000000", a=0.5))
        c.drawCircle(16 * u, 18 * u, 7 * u, P("#000000", a=0.5))
    elif g == "cup":
        c.drawPath(poly([(-18 * u, -20 * u), (18 * u, -20 * u), (13 * u, 26 * u), (-13 * u, 26 * u)]), P(wcol))
        rrect(c, -22 * u, -28 * u, 44 * u, 10 * u, 4 * u, wcol)
    elif g == "phone":
        rrect(c, -16 * u, -28 * u, 32 * u, 56 * u, 7 * u, wcol)
        rrect(c, -11 * u, -21 * u, 22 * u, 38 * u, 3 * u, "#000000", 0.35)
    elif g == "shirt":
        c.drawPath(poly([(-12 * u, -24 * u), (12 * u, -24 * u), (30 * u, -12 * u), (22 * u, 0), (14 * u, -4 * u),
                         (14 * u, 26 * u), (-14 * u, 26 * u), (-14 * u, -4 * u), (-22 * u, 0),
                         (-30 * u, -12 * u)]), P(wcol))
    elif g == "bag":
        rrect(c, -22 * u, -12 * u, 44 * u, 40 * u, 6 * u, wcol)
        rrect(c, -12 * u, -28 * u, 24 * u, 26 * u, 10 * u, wcol, stroke=5 * u)
    elif g == "shield":
        c.drawPath(poly([(0, -28 * u), (24 * u, -18 * u), (20 * u, 10 * u), (0, 28 * u), (-20 * u, 10 * u),
                         (-24 * u, -18 * u)]), P(wcol))
    elif g == "bank":
        c.drawPath(poly([(-30 * u, -12 * u), (0, -30 * u), (30 * u, -12 * u)]), P(wcol))
        for k in range(4):
            c.drawRect(skia.Rect((-24 + k * 15) * u, -8 * u, (-17 + k * 15) * u, 18 * u), P(wcol))
        c.drawRect(skia.Rect(-30 * u, 20 * u, 30 * u, 28 * u), P(wcol))
    elif g == "split":
        for k in range(4):
            rrect(c, (-30 + k * 16) * u, -14 * u, 12 * u, 28 * u, 3 * u, wcol)
    elif g == "tv":
        rrect(c, -30 * u, -22 * u, 60 * u, 38 * u, 5 * u, wcol)
        line(c, -10 * u, 26 * u, 10 * u, 26 * u, wcol, 5 * u)
    elif g == "fork":
        for k in (-8, 0, 8):
            line(c, k * u, -28 * u, k * u, -8 * u, wcol, 4 * u)
        line(c, 0, -8 * u, 0, 28 * u, wcol, 6 * u)
        line(c, -8 * u, -8 * u, 8 * u, -8 * u, wcol, 4 * u)
    elif g == "pill":
        with xf(c, 0, 0, rot=-35):
            rrect(c, -30 * u, -12 * u, 60 * u, 24 * u, 12 * u, wcol)
            c.drawRect(skia.Rect(0, -12 * u, 30 * u, 12 * u), P("#000000", a=0.25))
    elif g == "q":
        text(c, "?", 0, 20 * u, 64 * u, wcol, "Black")
    elif g == "dollar":
        text(c, "$", 0, 22 * u, 64 * u, wcol, "Black")


def thought(c, x, y, w, h, a=1.0, s=1.0, tail=(-1, 1)):
    with xf(c, x, y, s, alpha=a):
        rrect(c, -w / 2, -h / 2, w, h, h / 2.2, "#ffffff")
        for i, rr in enumerate((22, 14, 9)):
            c.drawCircle(tail[0] * (w * 0.25 + i * 28), h / 2 + 20 + i * 30, rr, P("#ffffff"))


def label(c, x, y, s, size=40, color="#ffffff", bgc="#0b1018", a=1.0, sc=1.0):
    w = text_width(s, size, "Black") + 48
    with xf(c, x, y, sc, alpha=a):
        rrect(c, -w / 2, -size * 0.8, w, size * 1.6, 14, bgc, 0.85)
        text(c, s, 0, size * 0.36, size, color, "Black")


