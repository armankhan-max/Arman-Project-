"""YouTube thumbnails (1280x720) in the video's art style. Three curiosity-hook variants for A/B testing.

Usage: python thumbnail.py OUTDIR
"""
import math
import os
import sys

import skia

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *  # noqa: F401,F403

TW, TH = 1920, 1080  # drawn at 1080p, saved at both 1080p and 1280x720


def big_text(c, s, x, y, size, color, align="left", rot=0, ow=None):
    with xf(c, x, y, rot=rot):
        f = font(size, "Black")
        w = f.measureText(s)
        ox = {"left": 0, "center": -w / 2, "right": -w}[align]
        c.drawString(s, ox + size * 0.06, size * 0.09, f, P("#000000", a=0.45))
        c.drawString(s, ox, 0, f, P("#111111", ow or size * 0.16))
        c.drawString(s, ox, 0, f, P(color))


def red_arrow(c, x1, y1, x2, y2, w=34):
    ang = math.atan2(y2 - y1, x2 - x1)
    L = math.hypot(x2 - x1, y2 - y1)
    with xf(c, x1, y1, rot=math.degrees(ang)):
        body = skia.Path()
        body.moveTo(0, 0)
        body.quadTo(L * 0.5, -L * 0.18, L - w * 2.2, 0)
        c.drawPath(body, P("#ffffff", w + 16))
        c.drawPath(body, P("#ff1e1e", w))
        head = poly([(L, 0), (L - w * 3.2, -w * 1.9), (L - w * 2.4, 0), (L - w * 3.2, w * 1.9)])
        c.drawPath(head, P("#ffffff", 16))
        c.drawPath(head, P("#ff1e1e"))


def red_circle(c, x, y, rx, ry, w=18):
    r = skia.Rect(x - rx, y - ry, x + rx, y + ry)
    c.drawOval(r, P("#ffffff", w + 14))
    c.drawOval(r, P("#ff1e1e", w))


def hot_bg(c, t=1.3):
    draw_sky(c, "hot", t, sun_pos=(1650, 170), sun_r=120)
    draw_ground(c, "hot", scroll=0, props=False)
    heat_shimmer(c, t, 1.4)
    vignette(c, 0.55)


# ---------------------------------------------------------------- variant A: "HOW LONG?" face + empty bottle
def thumb_a(c):
    t = 1.3
    hot_bg(c, t)
    glow(c, 560, 560, 650, "#ff3b1f", 0.35)
    with xf(c, 540, 620, 6.2, rot=-4):
        draw_head(c, 0, 0, "you", "shock", t + 0.5, look=(0.6, -0.2), sweat=1.0)
    # cracked lips detail + extra sweat
    for i, (dx, dy) in enumerate(((-260, -60), (290, -10), (250, 130))):
        drop(c, 540 + dx, 560 + dy, 26, "#8fd8ff")
    red_circle(c, 548, 790, 120, 95)
    # empty bottle with a single last drop
    with xf(c, 1480, 760, 2.6, rot=12):
        draw_bottle(c, 0, 0, 1.0, fill=0.04)
    drop(c, 1530, 1000, 34, "#4cc3ff")
    big_text(c, "HOW LONG", 1870, 230, 175, "#ffd400", align="right")
    big_text(c, "WITHOUT WATER?", 1870, 360, 100, "#ffffff", align="right")
    # timer badge
    with xf(c, 1290, 540, rot=-6):
        rrect(c, -170, -70, 340, 140, 30, "#111111")
        rrect(c, -170, -70, 340, 140, 30, "#ff1e1e", stroke=8)
        text(c, "??:??", 0, 38, 100, "#ff3b3b")


# ---------------------------------------------------------------- variant B: "THIS SAVED US" pink mirror
def thumb_b(c):
    t = 2.0
    hot_bg(c, t)
    car_y = 900
    draw_vehicle(c, 1050, car_y, 1.35, hood=1.0, t=t)
    # kid lying exhausted in front
    draw_char(c, 520, 990, "you", "stand", "dry", t, s=1.3, tilt=-84, sweat=1.0)
    # Noor flashing mirror at the sky
    ns, nx, ny = 1.5, 1500, 900
    hands = draw_char(c, nx, ny, "noor", "mirror_up", "happy", t, s=ns, look=(0.5, -1))
    mx, my = nx + hands[1][0] * ns + 20, ny + hands[1][1] * ns - 150
    rrect(c, mx - 12, my + 40, 24, 110, 12, "#ff5c9a")
    beam = poly([(mx - 20, my), (mx + 20, my), (1900, -40), (1700, -40)])
    c.drawPath(beam, P("#fffbe0", a=0.75))
    draw_mirror(c, mx, my, 1.25, rot=-40, glint=1.0, t=t)
    red_circle(c, mx, my, 150, 150)
    red_arrow(c, 980, 380, mx - 175, my - 10)
    big_text(c, "THIS", 70, 230, 210, "#ffffff", rot=-3)
    big_text(c, "SAVED US", 70, 430, 210, "#ffd400", rot=-3)
    big_text(c, "(NOT WATER)", 90, 560, 80, "#ff4d4d", rot=-3, ow=14)


# ---------------------------------------------------------------- variant C: body water draining "DAY 3"
def thumb_c(c):
    t = 3.0
    fill_shader(c, skia.Rect(0, 0, TW, TH), linear(0, 0, 0, TH, ["#3a0006", "#8a0a12"]))
    glow(c, 620, 560, 700, "#ff2a2a", 0.35)
    # warning stripes bottom
    for i in range(-2, 30):
        x = i * 90
        c.drawPath(poly([(x, TH - 60), (x + 45, TH - 60), (x - 15, TH), (x - 60, TH)]), P("#ffd400", a=0.9))
    c.drawRect(skia.Rect(0, TH - 60, TW, TH - 52), P("#111111"))
    water_body(c, 600, 640, 1.45, 0.16, t, leak=1.0)
    red_circle(c, 600, 920, 230, 70)
    pill(c, 600, 120, "WATER LOST: 10%", 56, "#ff1e1e", "#ffffff")
    big_text(c, "DAY 3", 1080, 330, 260, "#ffd400")
    big_text(c, "WITHOUT", 1090, 500, 140, "#ffffff")
    big_text(c, "WATER", 1090, 650, 140, "#ffffff")
    with xf(c, 1640, 850, rot=8):
        c.drawCircle(0, 0, 120, P("#111111"))
        c.drawCircle(0, 0, 120, P("#ffd400", 12))
        text(c, "?", 0, 62, 180, "#ffd400")


# ---------------------------------------------------------------- variant D: split screen DAY 1 vs DAY 3
def thumb_d(c):
    t = 1.0
    mid = TW / 2
    # jagged divider shape
    zig = [(mid + 40, -10)]
    for i in range(1, 9):
        zig.append((mid + (40 if i % 2 == 0 else -40), i * TH / 8))
    zig.append((mid + 40, TH + 10))
    left = poly([(-10, -10)] + zig + [(-10, TH + 10)])
    right = poly([(TW + 10, -10)] + zig + [(TW + 10, TH + 10)])

    # LEFT: day 1, happy and hydrated (cool blue)
    c.save()
    c.clipPath(left, skia.ClipOp.kIntersect, True)
    fill_shader(c, skia.Rect(0, 0, TW, TH), linear(0, 0, 0, TH, ["#36b3ff", "#0a5fc4"]))
    for i in range(14):
        drop(c, 80 + (i * 137) % 860, 120 + (i * 241) % 900, 22, "#ffffff", a=0.18)
    glow(c, 470, 600, 520, "#9be3ff", 0.5)
    with xf(c, 470, 640, 5.2, rot=-3):
        draw_head(c, 0, 0, "you", "laugh", t, look=(0.3, -0.2))
    with xf(c, 830, 820, 2.0, rot=-12):
        draw_bottle(c, 0, 0, 1.0, fill=0.95)
    for k, (sx, sy) in enumerate(((800, 560), (870, 640), (760, 700))):
        sparkle(c, sx, sy, 26 - k * 5, "#ffffff", 0.9, rot=20 * k)
    c.restore()

    # RIGHT: day 3, dehydrated (hot red/orange)
    c.save()
    c.clipPath(right, skia.ClipOp.kIntersect, True)
    fill_shader(c, skia.Rect(0, 0, TW, TH), linear(0, 0, 0, TH, ["#ff9a1f", "#b3170d"]))
    glow(c, 1760, 150, 420, "#fff3c4", 0.8)
    c.drawCircle(1760, 150, 110, P("#fff6cf"))
    c.drawCircle(1760, 150, 90, P("#ffe47a"))
    heat_shimmer(c, t, 2.0, 500, 900)
    glow(c, 1450, 600, 520, "#ff2a00", 0.45)
    with xf(c, 1450, 640, 5.2, rot=4):
        draw_head(c, 0, 0, "you", "dry", t + 0.4, look=(-0.2, 0.4), sweat=1.0)
    # cracks on lips emphasis
    red_circle(c, 1462, 775, 115, 80, 14)
    with xf(c, 1800, 820, 1.6, rot=75):
        draw_bottle(c, 0, 0, 1.0, fill=0.0)
    c.restore()

    # divider
    zp = poly(zig, close=False)
    c.drawPath(zp, P("#111111", 34))
    c.drawPath(zp, P("#ffffff", 16))

    # labels
    pill(c, 470, 110, "DAY 1", 92, "#ffffff", "#0a5fc4", s=1.0)
    pill(c, 1450, 110, "DAY 3", 92, "#111111", "#ffd400", s=1.0)
    # body water meters
    for x, lvl, col, lab in ((470, 0.95, "#4cc3ff", "WATER 100%"), (1450, 0.18, "#ff3b3b", "WATER ???")):
        rrect(c, x - 260, 960, 520, 64, 32, "#111111")
        rrect(c, x - 252, 968, 504 * lvl, 48, 24, col)
        text(c, lab, x, 1008, 40, "#ffffff", outline="#111111", ow=8)
    # VS badge
    with xf(c, mid, 520, rot=-8):
        c.drawCircle(0, 0, 118, P("#111111"))
        c.drawCircle(0, 0, 104, P("#ffd400"))
        text(c, "VS", 0, 34, 96, "#111111")
    # bottom-center hook
    big_text(c, "NO WATER", mid, 320, 120, "#ffffff", align="center", rot=-4)


def save(fn, outdir, name):
    s = skia.Surface(TW, TH)
    c = s.getCanvas()
    c.clear(C("#000000"))
    fn(c)
    img = s.makeImageSnapshot()
    big = os.path.join(outdir, f"{name}_1920x1080.png")
    img.save(big, skia.kPNG)
    small = img.resize(1280, 720, skia.SamplingOptions(skia.CubicResampler.Mitchell()))
    small.save(os.path.join(outdir, f"{name}_1280x720.png"), skia.kPNG)
    return big


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "thumbnails"
    os.makedirs(out, exist_ok=True)
    for fn, name in ((thumb_a, "thumb_A_how_long"), (thumb_b, "thumb_B_this_saved_us"), (thumb_c, "thumb_C_day3"),
                     (thumb_d, "thumb_D_split_day1_vs_day3")):
        print(save(fn, out, name))
