"""Backgrounds (sets) for the Lucia video. Each set draws a full 1920x1080 frame and is cached."""
import math
import random

import skia

from g6fx import (W, H, C, P, xf, rrect, poly, line, linear, radial, fill_shader, glow, mixhex, clamp, lerp,
                  shape, oval, box, rect, grad_rect, T, tw, palm, palm_green, car, bars, cached, MARKER, SERIF,
                  SCRIPT, LUCKY, BANG, OUT, sparkle, money_bag)

FLOOR = 830


# ---------------------------------------------------------------- shared pieces
def sky(c, top, mid, bot, y1=H, sun=None, sun_r=110, sun_col="#ffd27a"):
    grad_rect(c, 0, 0, W, y1, [top, mid, bot], [0, 0.55, 1])
    if sun:
        glow(c, sun[0], sun[1], sun_r * 3.2, sun_col, 0.5)
        c.drawCircle(sun[0], sun[1], sun_r, P(sun_col))
        for k in range(5):
            yy = sun[1] + sun_r * 0.15 + k * sun_r * 0.17
            rect(c, sun[0] - sun_r, yy, sun_r * 2, 5 + k * 2, mid, 0.9)


def stars(c, n=120, seed=3, ymax=600, a=1.0):
    rnd = random.Random(seed)
    for _ in range(n):
        c.drawCircle(rnd.uniform(0, W), rnd.uniform(0, ymax), rnd.uniform(0.8, 2.6), P("#ffffff", a=rnd.uniform(.3, .9) * a))


def skyline(c, base, col, seed=1, hmin=120, hmax=420, wmin=60, wmax=150, lit=None, lit_a=0.8, x0=-20, x1=W + 20,
            antenna=True):
    rnd = random.Random(seed)
    x = x0
    while x < x1:
        w = rnd.uniform(wmin, wmax)
        h = rnd.uniform(hmin, hmax)
        rect(c, x, base - h, w, h + 2, col)
        if rnd.random() < 0.3:
            pth = poly([(x, base - h), (x + w / 2, base - h - rnd.uniform(30, 90)), (x + w, base - h)])
            c.drawPath(pth, P(col))
        if antenna and rnd.random() < 0.25:
            line(c, x + w / 2, base - h, x + w / 2, base - h - 50, col, 4)
        if lit:
            for wy in range(int(base - h + 18), int(base - 10), 26):
                for wx in range(int(x + 10), int(x + w - 14), 22):
                    if rnd.random() < 0.45:
                        rect(c, wx, wy, 10, 12, rnd.choice(lit), lit_a * rnd.uniform(0.5, 1))
        x += w + rnd.uniform(-10, 14)


def wallpaper(c, y0, y1, base, pat, kind="diamond"):
    rect(c, 0, y0, W, y1 - y0, base)
    if kind == "diamond":
        for yy in range(int(y0), int(y1), 70):
            for xx in range(0, W + 70, 70):
                o = 35 if (yy // 70) % 2 else 0
                pth = poly([(xx + o, yy + 12), (xx + o + 10, yy + 24), (xx + o, yy + 36), (xx + o - 10, yy + 24)])
                c.drawPath(pth, P(pat))
    elif kind == "stripe":
        for xx in range(0, W, 60):
            rect(c, xx, y0, 22, y1 - y0, pat)
    elif kind == "brick":
        for i, yy in enumerate(range(int(y0), int(y1), 44)):
            for xx in range(-60 if i % 2 else 0, W, 120):
                rrect(c, xx + 3, yy + 3, 114, 38, 4, pat)
    elif kind == "block":
        for i, yy in enumerate(range(int(y0), int(y1), 70)):
            for xx in range(-90 if i % 2 else 0, W, 180):
                c.drawRect(skia.Rect.MakeXYWH(xx + 2, yy + 2, 176, 66), P(pat, 3))
    elif kind == "panel":
        for xx in range(0, W, 160):
            line(c, xx, y0, xx, y1, pat, 4)


def floor_planks(c, y0, col, col2, kind="wood"):
    rect(c, 0, y0, W, H - y0, col)
    if kind == "wood":
        for i, yy in enumerate(range(int(y0), H, 36)):
            line(c, 0, yy, W, yy, col2, 3)
            for xx in range((i * 137) % 260 - 260, W, 260):
                line(c, xx, yy, xx, yy + 36, col2, 3)
    elif kind == "tile":
        for yy in range(int(y0), H, 60):
            line(c, 0, yy, W, yy, col2, 3)
        for xx in range(0, W, 120):
            line(c, xx, y0, xx, H, col2, 3)
    elif kind == "concrete":
        rnd = random.Random(4)
        for _ in range(60):
            c.drawCircle(rnd.uniform(0, W), rnd.uniform(y0, H), rnd.uniform(2, 6), P(col2, a=0.5))
    line(c, 0, y0, W, y0, OUT, 5)


def baseboard(c, y, col="#f2eadb"):
    box(c, -10, y - 26, W + 20, 30, col, ow=4)


def window(c, x, y, w, h, scene="day", curtains=None, frame="#f4efe6", bars_=False, t=0.0):
    box(c, x - 14, y - 14, w + 28, h + 28, frame)
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y, w, h))
    if scene == "day":
        grad_rect(c, x, y, w, h, ["#7cc7ec", "#cdeaf5"])
        for k in range(3):
            palm_green(c, x + 40 + k * w / 2.5, y + h + 60, 0.5)
    elif scene == "sunset":
        grad_rect(c, x, y, w, h, ["#4a2d7a", "#e05d8c", "#ffb36b"])
        skyline(c, y + h, "#2b1b3e", seed=int(x), hmin=30, hmax=h * 0.5, wmin=20, wmax=50)
        palm(c, x + w * 0.75, y + h + 20, 0.4, col="#24132e")
    elif scene == "night":
        grad_rect(c, x, y, w, h, ["#0d1030", "#2a1f5a"])
        rnd = random.Random(int(x))
        for _ in range(20):
            c.drawCircle(rnd.uniform(x, x + w), rnd.uniform(y, y + h * 0.6), 1.5, P("#ffffff", a=0.8))
        skyline(c, y + h, "#141030", seed=int(x) + 1, hmin=30, hmax=h * 0.55, wmin=20, wmax=50,
                lit=["#ffd36b", "#ff5fa2", "#5fe3ff"], lit_a=0.9)
    elif scene == "liberty":
        grad_rect(c, x, y, w, h, ["#8b9bb0", "#c9d2dc"])
        skyline(c, y + h, "#5b6678", seed=5, hmin=h * 0.3, hmax=h * 0.85, wmin=20, wmax=45)
    elif scene == "gray":
        grad_rect(c, x, y, w, h, ["#9eb4c6", "#d8e2ea"])
    c.restore()
    line(c, x + w / 2, y, x + w / 2, y + h, frame, 10)
    line(c, x, y + h / 2, x + w, y + h / 2, frame, 10)
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), P(OUT, 5))
    if bars_:
        for k in range(1, 5):
            line(c, x + k * w / 5, y, x + k * w / 5, y + h, "#5b6470", 9)
    if curtains:
        for sx in (0, 1):
            cx = x - 40 if sx == 0 else x + w - 50
            pth = skia.Path()
            pth.moveTo(cx, y - 40)
            pth.lineTo(cx + 90, y - 40)
            pth.cubicTo(cx + 70, y + h * 0.4, cx + 100, y + h * 0.8, cx + 80, y + h + 40)
            pth.lineTo(cx, y + h + 40)
            pth.close()
            shape(c, pth, curtains)
        box(c, x - 60, y - 52, w + 120, 16, "#6b4a33", r=8, ow=4)


def frame_pic(c, x, y, w, h, inner="#c9b48a", border="#6b4a33", draw=None):
    box(c, x, y, w, h, border, ow=4)
    box(c, x + 10, y + 10, w - 20, h - 20, inner, ow=3)
    if draw:
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(x + 10, y + 10, w - 20, h - 20))
        draw(c, x + 10, y + 10, w - 20, h - 20)
        c.restore()


def couch(c, x, y, w=560, col="#c9a66b"):
    dk = mixhex(col, "#000000", 0.25)
    box(c, x, y - 220, w, 120, col, r=26)
    box(c, x - 40, y - 150, 80, 150, dk, r=24)
    box(c, x + w - 40, y - 150, 80, 150, dk, r=24)
    box(c, x + 20, y - 120, w - 40, 90, col, r=18)
    line(c, x + w / 2, y - 118, x + w / 2, y - 32, OUT, 4)
    box(c, x + 10, y - 40, 20, 40, "#4a3222", ow=3)
    box(c, x + w - 30, y - 40, 20, 40, "#4a3222", ow=3)


def lamp(c, x, y, h=300, shade="#f2d28a", on=True):
    line(c, x, y, x, y - h, OUT, 10)
    line(c, x, y, x, y - h, "#8a6a4a", 5)
    box(c, x - 50, y - 8, 100, 14, "#5a3d2a", r=6, ow=3)
    pth = poly([(x - 55, y - h), (x + 55, y - h), (x + 35, y - h - 80), (x - 35, y - h - 80)])
    shape(c, pth, shade)
    if on:
        glow(c, x, y - h - 30, 200, "#ffd98a", 0.35)


def tv(c, x, y, s=1.0, screen="#202830", glowc=None):
    with xf(c, x, y, s=s):
        box(c, -130, -40, 260, 40, "#6b4a33", r=4)
        box(c, -110, -200, 220, 160, "#2a2a2e", r=14)
        box(c, -92, -184, 184, 128, screen, r=10)
        if glowc:
            glow(c, 0, -120, 160, glowc, 0.3)


def door(c, x, y, w=150, h=290, col="#7a4e30", knob=True, num=None):
    box(c, x - 12, y - h - 12, w + 24, h + 12, "#f2eadb")
    box(c, x, y - h, w, h, col)
    box(c, x + 20, y - h + 24, w - 40, h * 0.38, mixhex(col, "#000000", 0.15), r=4, ow=3)
    box(c, x + 20, y - h * 0.5, w - 40, h * 0.38, mixhex(col, "#000000", 0.15), r=4, ow=3)
    if knob:
        oval(c, x + w - 24, y - h * 0.48, 9, 9, "#e8c25a", ow=3)
    if num:
        T(c, num, x + w / 2, y - h - 30, 30, "#2a1a12", "inter")


def plant(c, x, y, s=1.0):
    with xf(c, x, y, s=s):
        for k in range(7):
            ang = -math.pi / 2 + (k - 3) * 0.32
            pth = skia.Path()
            pth.moveTo(0, -60)
            ex, ey = math.cos(ang) * 120, -60 + math.sin(ang) * 140
            pth.quadTo(ex * 0.4 - 30, ey * 0.6, ex, ey)
            pth.quadTo(ex * 0.4 + 30, ey * 0.6, 0, -60)
            shape(c, pth, "#4f9a56" if k % 2 else "#3d8446", ow=4)
        pth = poly([(-45, -70), (45, -70), (35, 0), (-35, 0)])
        shape(c, pth, "#c96a3a")


def neon(c, s, x, y, size, col, fam=SCRIPT, a=1.0, flick=1.0, rot=0.0):
    with xf(c, x, y, rot=rot, alpha=a):
        f_w = tw(s, size, fam)
        glow(c, 0, -size * 0.3, max(f_w, size) * 0.75, col, 0.35 * flick)
        T(c, s, 0, 0, size, col, fam, outline=col, ow=8 * flick)
        T(c, s, 0, 0, size, "#ffffff", fam, a=0.9 * flick)


def fence_wood(c, y, col="#e8dcc4", h=170):
    for xx in range(-20, W + 40, 64):
        pth = poly([(xx, y), (xx, y - h), (xx + 27, y - h - 22), (xx + 54, y - h), (xx + 54, y)])
        shape(c, pth, col, ow=4)
    box(c, -20, y - h + 30, W + 40, 18, mixhex(col, "#000000", 0.1), ow=3)
    box(c, -20, y - 50, W + 40, 18, mixhex(col, "#000000", 0.1), ow=3)


def house_front(c, x, y, w=520, h=300, col="#f2dcc0", roof="#7a4e3a", door_col="#3f7a8a", porch=True):
    pth = poly([(x - 40, y - h), (x + w / 2, y - h - 150), (x + w + 40, y - h)])
    shape(c, pth, roof)
    box(c, x, y - h, w, h, col)
    for yy in range(int(y - h + 24), int(y), 28):
        line(c, x + 4, yy, x + w - 4, yy, mixhex(col, "#000000", 0.12), 3)
    door(c, x + w / 2 - 60, y, 120, 210, door_col)
    window(c, x + 40, y - h + 70, 130, 110, "gray", frame="#f7f3ea")
    window(c, x + w - 170, y - h + 70, 130, 110, "gray", frame="#f7f3ea")
    if porch:
        box(c, x - 20, y - 14, w + 40, 20, "#c9b89a", ow=4)


# ---------------------------------------------------------------- sets
def set_vice_sunset(c):
    sky(c, "#3b1f63", "#e0568a", "#ffb067", y1=820, sun=(1250, 600), sun_r=150, sun_col="#ffe08a")
    skyline(c, 820, "#3a2150", seed=7, hmin=120, hmax=430, wmin=50, wmax=130, lit=["#ffd36b"], lit_a=0.35)
    skyline(c, 840, "#24132e", seed=9, hmin=60, hmax=240, wmin=70, wmax=160)
    grad_rect(c, 0, 820, W, 260, ["#2a1838", "#150b1e"])
    for xx in range(0, W, 220):
        rect(c, xx + 40, 940, 120, 10, "#ffcf6a", 0.6)
    for k, (x, s) in enumerate([(120, 1.2), (330, 0.9), (1550, 1.1), (1800, 1.35), (1680, 0.8)]):
        palm(c, x, 900, s, col="#170a1d")


def set_vice_night(c):
    sky(c, "#060716", "#1b1446", "#4a1f5e", y1=820)
    stars(c, 120, ymax=420)
    c.drawCircle(1600, 170, 60, P("#f4efe0"))
    c.drawCircle(1625, 155, 58, P("#0e0c2a"))
    skyline(c, 820, "#1a1236", seed=17, hmin=150, hmax=520, wmin=50, wmax=120,
            lit=["#ffd36b", "#ff5fa2", "#5fe3ff", "#ffffff"], lit_a=0.8)
    skyline(c, 840, "#0d0920", seed=19, hmin=60, hmax=260, wmin=70, wmax=160,
            lit=["#ff5fa2", "#5fe3ff"], lit_a=0.7)
    grad_rect(c, 0, 820, W, 260, ["#1a1036", "#07051a"])
    for xx in range(0, W, 60):
        rect(c, xx, 830 + (xx * 7) % 60, 30, 4, "#ff5fa2", 0.35)
        rect(c, xx + 20, 860 + (xx * 13) % 80, 22, 4, "#5fe3ff", 0.3)
    for x, s in [(90, 1.2), (300, 0.9), (1620, 1.0), (1840, 1.3)]:
        palm(c, x, 920, s, col="#05030c")


def set_map(c):
    rect(c, 0, 0, W, H, "#2a1d16")
    for yy in range(0, H, 40):
        line(c, 0, yy, W, yy + 10, "#24180f", 6)
    with xf(c, 960, 540, rot=-2):
        box(c, -820, -480, 1640, 960, "#efe2c4", r=6, ow=0)
        for k in (-410, 0, 410):
            line(c, k, -480, k, 480, "#d8c8a6", 4)
        line(c, -820, 0, 820, 0, "#d8c8a6", 4)
        # ocean
        rect(c, -820, -480, 1640, 960, "#a9cfd8")
        # Leonida (Florida-like) land mass
        pth = skia.Path()
        pts = [(-700, -420), (420, -420), (430, -300), (360, -200), (320, -40), (380, 120), (420, 260), (380, 380),
               (300, 430), (220, 330), (140, 200), (60, 80), (-40, 0), (-120, -60), (-260, -120), (-420, -150),
               (-560, -170), (-700, -180)]
        pth.moveTo(*pts[0])
        for p_ in pts[1:]:
            pth.lineTo(*p_)
        pth.close()
        c.drawPath(pth, P("#efe2c4"))
        c.drawPath(pth, P("#6a8a8f", 4))
        # keys
        for k in range(9):
            oval(c, 250 - k * 50, 450 - k * 8, 22 - k, 9, "#efe2c4", ow=3, oc="#6a8a8f")
        # lake
        oval(c, 220, 130, 70, 50, "#a9cfd8", ow=3, oc="#6a8a8f")
        # roads
        for pts_, col in (([(-650, -300), (-200, -260), (100, -200), (300, -60), (330, 200)], "#c0392b"),
                          ([(-400, -380), (-100, -330), (200, -380), (380, -380)], "#d6a243"),
                          ([(100, -200), (60, 60), (200, 300), (300, 420)], "#d6a243")):
            pth = skia.Path()
            pth.moveTo(*pts_[0])
            for p_ in pts_[1:]:
                pth.lineTo(*p_)
            c.drawPath(pth, P(col, 5))
        # legend box
        box(c, 470, -440, 320, 380, "#f6eedb", r=4, ow=3, oc="#6a5a40")
        T(c, "STATE OF", 630, -390, 26, "#8a2a22", SERIF)
        T(c, "LEONIDA", 630, -320, 64, "#a3261e", LUCKY)
        T(c, "HIGHWAY & ROAD MAP", 630, -280, 18, "#3a2a1a", "interb")
        for i, (lab, col) in enumerate((("Highway", "#c0392b"), ("Road", "#d6a243"), ("City", "#cbb48a"))):
            line(c, 500, -230 + i * 40, 560, -230 + i * 40, col, 6)
            T(c, lab, 580, -222 + i * 40, 22, "#3a2a1a", SERIF, align="left")
        # compass
        c.drawCircle(-640, 330, 80, P("#6a5a40", 3))
        pth = poly([(-640, 240), (-625, 330), (-640, 420), (-655, 330)])
        shape(c, pth, "#c0392b", ow=3)
        T(c, "N", -640, 230, 28, "#3a2a1a", SERIF)
        # city labels
        for lab, x, y in (("VICE CITY", 300, 120), ("Port Gellhorn", -470, -210), ("Leonida Keys", 120, 420),
                          ("Grassrivers", 150, 20), ("Kelly County", -150, -290), ("Ambrosia", -20, -160)):
            c.drawCircle(x, y, 9, P("#2a1a12"))
            T(c, lab, x + 18, y - 14, 28 if lab != "VICE CITY" else 38, "#2a1a12", SERIF if lab != "VICE CITY" else LUCKY,
              align="left")


def set_dark_desk(c):
    rect(c, 0, 0, W, H, "#140d0a")
    glow(c, 960, 520, 900, "#4a2e1c", 0.55)
    for yy in range(0, H, 46):
        line(c, 0, yy, W, yy + 6, "#1d130e", 5)


def set_cork(c):
    rect(c, 0, 0, W, H, "#5a3a24")
    box(c, 60, 40, W - 120, H - 80, "#b98a58", r=6, ow=8, oc="#3a2414")
    rnd = random.Random(2)
    for _ in range(1600):
        c.drawCircle(rnd.uniform(70, W - 70), rnd.uniform(50, H - 50), rnd.uniform(1, 3),
                     P(rnd.choice(["#a77a48", "#c99a66", "#8f6a3e"]), a=0.8))


def set_living(c, mood="day"):
    wallpaper(c, 0, FLOOR, "#7f9a6a", "#6f8a5c")
    floor_planks(c, FLOOR, "#b5835a", "#8f6340")
    baseboard(c, FLOOR)
    window(c, 1260, 200, 330, 300, "day" if mood == "day" else "night", curtains="#d9a441")
    frame_pic(c, 300, 170, 160, 200, "#c9b48a")
    frame_pic(c, 500, 140, 220, 160, "#d9c9a6")
    frame_pic(c, 760, 190, 150, 190, "#c9b48a")
    # liberty city postcard
    box(c, 520, 330, 180, 120, "#f7f3ea", ow=3)
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(530, 340, 160, 80))
    grad_rect(c, 530, 340, 160, 80, ["#8b9bb0", "#c9d2dc"])
    skyline(c, 420, "#5b6678", seed=5, hmin=20, hmax=70, wmin=10, wmax=22)
    c.restore()
    T(c, "Liberty City", 610, 440, 18, "#2a1a12", SERIF)
    couch(c, 380, FLOOR + 20, 640, "#c9a66b")
    lamp(c, 1120, FLOOR, 300, on=(mood != "day"))
    tv(c, 1650, FLOOR + 10, 1.0)
    plant(c, 230, FLOOR + 10, 0.9)
    box(c, 560, FLOOR + 60, 300, 26, "#7a5236", r=6)
    if mood == "night":
        tint(c, "#0a0830", 0.45)


def tint(c, col, a):
    c.drawRect(skia.Rect(0, 0, W, H), P(col, a=a))


def set_yard(c):
    sky(c, "#6cb9e6", "#a8d8f0", "#e8f4f6", y1=700)
    for x, s in ((150, 1.0), (1700, 1.1), (1450, 0.8)):
        palm_green(c, x, 640, s * 0.8)
    house_front(c, 560, 640, 760, 330, "#e9cfa9", "#8a4e3a", "#2f7a8a")
    fence_wood(c, 700, "#ecdcbf", 150)
    rect(c, 0, 700, W, 380, "#7cbf5a")
    for k in range(70):
        rnd = random.Random(k)
        x, y = rnd.uniform(0, W), rnd.uniform(720, H)
        line(c, x, y, x + 6, y - 14, "#5e9e44", 3)
    # tire + clothesline
    oval(c, 1600, 860, 70, 30, "#2a2a2e")
    oval(c, 1600, 852, 34, 12, "#7cbf5a", ow=3)
    line(c, 80, 460, 520, 480, "#ffffff", 3, 0.7)


def set_street(c, tod="day"):
    if tod == "day":
        sky(c, "#58ade3", "#9fd3f0", "#f4e6c8", y1=720)
    else:
        sky(c, "#3b1f63", "#e0568a", "#ffb067", y1=720, sun=(960, 690), sun_r=120)
    cols = ["#f4c6c6", "#bfe3d8", "#f6e3a8", "#c9d6f2", "#f2cfa8"]
    for i in range(5):
        x = -60 + i * 410
        house_front(c, x, 700, 330, 240, cols[i], ["#8a4e3a", "#4a6a8a", "#a35a3a", "#5a5a7a", "#7a4e3a"][i],
                    ["#3f7a8a", "#c0392b", "#2f5a8a", "#8a3f6a", "#3f8a5a"][i])
    for x in (180, 600, 1010, 1420, 1830):
        palm_green(c, x, 720, 0.85)
    rect(c, 0, 700, W, 70, "#d8d2c4")
    line(c, 0, 700, W, 700, OUT, 4)
    rect(c, 0, 770, W, 310, "#4a4a55")
    line(c, 0, 770, W, 770, OUT, 5)
    for xx in range(0, W, 200):
        rect(c, xx + 30, 920, 110, 12, "#f2e6b8")
    if tod != "day":
        tint(c, "#3a1050", 0.15)


def set_store_night(c):
    sky(c, "#05061a", "#141a40", "#2a1f5a", y1=860)
    stars(c, 60, ymax=200)
    box(c, -20, 120, W + 40, 740, "#3a3550", ow=5)
    wallpaper(c, 125, 300, "#2f2a44", "#3a3550", "brick")
    # sign
    box(c, 360, 160, 1200, 130, "#1a1830", r=10)
    neon(c, "PAYDAY LOANS", 960, 260, 100, "#5fe3ff", LUCKY)
    # windows / door
    box(c, 220, 380, 560, 420, "#ffe9a8", ow=6)
    box(c, 1140, 380, 560, 420, "#ffe9a8", ow=6)
    for x0 in (220, 1140):
        neon(c, "CASH NOW", x0 + 280, 500, 64, "#ff5fa2", LUCKY)
        neon(c, "$$$", x0 + 280, 620, 70, "#7dff8a", LUCKY)
        for k in range(1, 3):
            line(c, x0 + k * 186, 380, x0 + k * 186, 800, OUT, 5)
    box(c, 840, 380, 240, 420, "#2a2840", ow=6)
    box(c, 860, 400, 200, 380, "#ffe9a8", ow=4)
    rect(c, 0, 800, W, 280, "#24223a")
    line(c, 0, 800, W, 800, OUT, 5)
    for xx in range(0, W, 240):
        rect(c, xx + 40, 940, 6, 140, "#f2e6b8", 0.6)
    glow(c, 960, 600, 700, "#ffe9a8", 0.12)


def set_cafe(c):
    sky(c, "#58ade3", "#9fd3f0", "#f4e6c8", y1=760)
    box(c, 240, 150, 1440, 650, "#f2e2c4")
    pth = skia.Path()
    for k in range(9):
        x = 240 + k * 160
        pth = poly([(x, 280), (x + 160, 280), (x + 160, 350), (x + 80, 380), (x, 350)])
        shape(c, pth, "#c0392b" if k % 2 == 0 else "#f7f3ea", ow=4)
    box(c, 240, 230, 1440, 60, "#c0392b")
    T(c, "SUNSHINE COFFEE", 960, 278, 50, "#fff3d8", LUCKY)
    box(c, 330, 420, 520, 330, "#bfe3f2", ow=5)
    box(c, 1070, 420, 520, 330, "#bfe3f2", ow=5)
    for x0 in (330, 1070):
        line(c, x0 + 260, 420, x0 + 260, 750, OUT, 5)
        line(c, x0 + 40, 440, x0 + 120, 520, "#ffffff", 8, 0.5)
    door(c, 880, 800, 160, 330, "#5a3d2a")
    rect(c, 0, 790, W, 290, "#d8d2c4")
    line(c, 0, 790, W, 790, OUT, 5)
    for x in (120, 1800):
        palm_green(c, x, 800, 0.9)
    # little outdoor table
    oval(c, 1300, 820, 110, 22, "#f2f2f2")
    line(c, 1300, 840, 1300, 960, OUT, 10)
    line(c, 1300, 840, 1300, 960, "#9a9a9a", 5)
    box(c, 1240, 950, 120, 14, "#9a9a9a", r=6, ow=3)


def set_doorway(c):
    wallpaper(c, 0, FLOOR, "#e8d6b8", "#d9c3a0", "panel")
    floor_planks(c, FLOOR, "#9a9a9a", "#7a7a7a", "tile")
    door(c, 860, FLOOR, 220, 470, "#8a5a3a", num="4B")
    lamp(c, 600, FLOOR - 300, 0, on=True)
    box(c, 1300, 300, 120, 160, "#f7f3ea", ow=4)
    T(c, "4B", 1360, 400, 50, "#2a1a12", "inter")


def set_cell(c, light=1.0):
    wallpaper(c, 0, FLOOR, "#8d9298", "#7a7f86", "block")
    floor_planks(c, FLOOR, "#6a6e74", "#575b60", "concrete")
    # high small window with bars
    box(c, 1250, 140, 260, 150, "#c9dbe6", ow=6)
    for k in range(1, 4):
        line(c, 1250 + k * 65, 140, 1250 + k * 65, 290, "#4a4f56", 10)
    fill_shader(c, skia.Rect(1100, 290, 1700, FLOOR),
                linear(1300, 290, 1300, FLOOR, [("#ffffff", 0.18 * light), ("#ffffff", 0)]))
    # bunk
    box(c, 140, 560, 620, 60, "#9a8a6a", r=8)
    box(c, 140, 520, 620, 50, "#e8e2d4", r=14)
    box(c, 170, 490, 160, 50, "#f2efe8", r=20)
    for x in (160, 730):
        box(c, x - 10, 600, 24, FLOOR - 600, "#5a5f66", ow=4)
    # toilet + sink
    box(c, 1550, 600, 170, 230, "#d8dde2", r=20)
    oval(c, 1635, 640, 70, 26, "#b0b8c0")
    # tally marks
    for k in range(4):
        for j in range(5):
            if j < 4:
                line(c, 900 + k * 70 + j * 12, 380, 900 + k * 70 + j * 12, 440, "#4a4f56", 4)
            else:
                line(c, 895 + k * 70, 420, 950 + k * 70, 395, "#4a4f56", 4)


def set_bars_overlay(c):
    bars(c, 0, W, -40, H + 40, n=14, col="#6c7784")


def set_office(c):
    wallpaper(c, 0, FLOOR, "#c8c2b2", "#b9b3a2", "block")
    floor_planks(c, FLOOR, "#7a7f86", "#666b72", "tile")
    window(c, 760, 150, 400, 260, "gray", frame="#d8d8d8", bars_=True)
    box(c, 200, 160, 260, 340, "#c9b48a", ow=4)
    T(c, "LEONIDA", 330, 230, 30, "#2a1a12", LUCKY)
    T(c, "DEPT. OF", 330, 270, 24, "#2a1a12", "interb")
    T(c, "CORRECTIONS", 330, 300, 24, "#2a1a12", "interb")
    oval(c, 330, 400, 60, 60, "#e8c25a")
    # clock
    c.drawCircle(1500, 260, 80, P("#f7f3ea"))
    c.drawCircle(1500, 260, 80, P(OUT, 6))
    line(c, 1500, 260, 1500, 205, OUT, 6)
    line(c, 1500, 260, 1540, 270, OUT, 6)
    # table in front
    box(c, 300, 760, 1320, 60, "#8a6a4a", r=6)
    box(c, 340, 820, 40, 200, "#5a3d2a", ow=4)
    box(c, 1540, 820, 40, 200, "#5a3d2a", ow=4)
    box(c, 860, 720, 220, 40, "#f2efe6", ow=3)


def set_keys(c, tod="sunset"):
    if tod == "sunset":
        sky(c, "#4a2d7a", "#f07a6a", "#ffcf80", y1=600, sun=(1400, 560), sun_r=110, sun_col="#fff0b0")
    else:
        sky(c, "#060716", "#141a40", "#2a2f6a", y1=600)
        stars(c, 120, ymax=500)
        c.drawCircle(1500, 160, 55, P("#f4efe0"))
    grad_rect(c, 0, 600, W, 480, ["#2fb3b8" if tod == "sunset" else "#102a4a",
                                   "#0f6f8a" if tod == "sunset" else "#081a30"])
    for k in range(40):
        rnd = random.Random(k)
        x, y = rnd.uniform(0, W), rnd.uniform(620, H)
        line(c, x, y, x + rnd.uniform(30, 90), y, "#ffffff", 3, 0.25)
    # mangrove islands
    for x, w in ((200, 400), (1000, 300), (1600, 500)):
        oval(c, x, 610, w / 2, 30, "#2c5a3a" if tod == "sunset" else "#0d2218", ow=0)
    # dock
    box(c, -40, 760, 900, 40, "#8a6a4a", ow=5)
    for x in range(0, 860, 120):
        box(c, x, 760, 22, 260, "#6a4a32", ow=4)
    # boat
    with xf(c, 1250, 820):
        pth = poly([(-330, -60), (330, -60), (260, 40), (-280, 40)])
        shape(c, pth, "#f2f2f2")
        rect(c, -320, -40, 640, 14, "#2fb3b8")
        box(c, -120, -170, 220, 110, "#e8e8e8", r=10)
        box(c, -100, -150, 80, 50, "#9fd3ef", r=6, ow=3)
        box(c, 0, -150, 80, 50, "#9fd3ef", r=6, ow=3)
        for k in range(3):
            box(c, 150 + k * 50, -110, 46, 46, "#b98a58", r=4, ow=3)


def set_gate(c):
    sky(c, "#7cc4e8", "#bfe3f0", "#ffeccc", y1=760)
    box(c, 0, 360, W, 400, "#a9a9a0", ow=0)
    for xx in range(0, W, 60):
        line(c, xx, 360, xx, 760, "#6a6a66", 4)
    for xx in range(0, W, 120):
        line(c, xx, 360, xx + 60, 760, "#8a8a84", 2)
        line(c, xx + 60, 360, xx, 760, "#8a8a84", 2)
    for xx in range(0, W, 46):
        c.drawCircle(xx, 340, 22, P("#8a8a84", 4))
    box(c, 700, 300, 520, 460, "#6a6e74", ow=6)
    T(c, "LEONIDA STATE", 960, 360, 40, "#f2f2f2", LUCKY)
    T(c, "PENITENTIARY", 960, 410, 40, "#f2f2f2", LUCKY)
    rect(c, 0, 760, W, 320, "#bdb6a6")
    line(c, 0, 760, W, 760, OUT, 5)
    for xx in range(0, W, 260):
        rect(c, xx + 40, 900, 140, 10, "#f2f2f2", 0.8)


def set_gate_open(c, k):
    box(c, 760, 450, 400 * (1 - k), 310, "#4a4e54", ow=5)
    for i in range(8):
        x = 760 + i * 50 * (1 - k)
        line(c, x, 450, x, 760, "#2a2e34", 6)


def set_bar(c):
    wallpaper(c, 0, FLOOR, "#3a2418", "#2f1c12", "panel")
    # shelves with bottles
    for row, yy in enumerate((260, 420)):
        box(c, 300, yy, 1320, 20, "#7a5236", ow=4)
        rnd = random.Random(row)
        for k in range(22):
            x = 330 + k * 58
            col = rnd.choice(["#2e8b57", "#8b2e2e", "#d9a441", "#4a7ab4", "#c9c2b0"])
            h = rnd.uniform(70, 110)
            box(c, x, yy - h, 34, h, col, r=8, ow=3)
            box(c, x + 10, yy - h - 24, 14, 26, col, r=4, ow=3)
    neon(c, "Rusty Anchor", 960, 150, 90, "#ff8a3d", SCRIPT)
    # anchor icon
    with xf(c, 1580, 110, s=0.8):
        c.drawCircle(0, -30, 16, P("#ff8a3d", 7))
        line(c, 0, -14, 0, 60, "#ff8a3d", 8)
        pth = skia.Path()
        pth.moveTo(-50, 30)
        pth.quadTo(0, 90, 50, 30)
        c.drawPath(pth, P("#ff8a3d", 8))
    floor_planks(c, FLOOR, "#4a3020", "#3a2418")
    box(c, 0, 680, W, 70, "#8a5a3a", r=10, ow=6)
    box(c, 0, 750, W, 120, "#5a3a24", ow=5)
    glow(c, 960, 300, 800, "#ff9a4a", 0.12)


def set_house_night(c):
    sky(c, "#060716", "#141a40", "#2a2f6a", y1=700)
    stars(c, 150, ymax=560)
    c.drawCircle(1450, 180, 70, P("#f4efe0"))
    glow(c, 1450, 180, 220, "#f4efe0", 0.2)
    grad_rect(c, 0, 700, W, 380, ["#0d2a3a", "#061420"])
    # stilt house
    with xf(c, 960, 700):
        for x in (-300, -100, 100, 300):
            box(c, x - 14, -40, 28, 160, "#3a2a20", ow=4)
        box(c, -380, -60, 760, 30, "#4a3424", ow=4)
        box(c, -340, -330, 680, 270, "#5a7a7a")
        for yy in range(-320, -60, 26):
            line(c, -336, yy, 336, yy, "#4a6a6a", 3)
        pth = poly([(-400, -330), (0, -480), (400, -330)])
        shape(c, pth, "#3a3a4a")
        for x in (-250, 130):
            box(c, x, -270, 120, 100, "#ffd98a", ow=5)
            glow(c, x + 60, -220, 160, "#ffd98a", 0.35)
        door(c, -40, -60, 90, 170, "#3a2a20")
    for x, s in ((200, 1.0), (1700, 1.2)):
        palm(c, x, 760, s, col="#03050c")


def set_motel(c, tod="day"):
    if tod == "day":
        sky(c, "#9ec7d8", "#d6e6ea", "#f2e6cc", y1=780)
    else:
        sky(c, "#060716", "#141a40", "#2a1f5a", y1=780)
        stars(c, 80, ymax=300)
    box(c, 120, 360, 1680, 420, "#d9b98a" if tod == "day" else "#5a4a3a")
    box(c, 100, 330, 1720, 50, "#a85a3a" if tod == "day" else "#4a2a1e")
    for k in range(7):
        x = 190 + k * 230
        door(c, x, 780, 110, 230, ["#3f7a8a", "#a85a3a"][k % 2])
        box(c, x + 130, 470, 80, 90, "#bfe3f2" if tod == "day" else "#ffd98a", ow=4)
        T(c, str(10 + k), x + 55, 535, 26, "#f2f2f2", "inter")
    # sign
    line(c, 1700, 780, 1700, 200, OUT, 18)
    line(c, 1700, 780, 1700, 200, "#7a7a7a", 10)
    box(c, 1560, 90, 280, 160, "#2a6a5a", r=12)
    neon(c, "MOTEL", 1700, 170, 60, "#ff5f6a", LUCKY, flick=0.9 if tod != "day" else 0.4)
    T(c, "VACANCY", 1700, 225, 30, "#ffd36b", "inter")
    rect(c, 0, 780, W, 300, "#8a8070" if tod == "day" else "#2a2630")
    line(c, 0, 780, W, 780, OUT, 5)
    for xx in range(0, W, 200):
        rect(c, xx + 20, 900, 8, 120, "#f2f2f2", 0.6)
    T(c, "PORT GELLHORN", 400, 300, 40, "#3a2a1a" if tod == "day" else "#cfc6b8", LUCKY)
    if tod != "day":
        tint(c, "#0a0830", 0.25)


def set_club(c):
    rect(c, 0, 0, W, H, "#120822")
    for k in range(8):
        ang = -0.9 + k * 0.25
        pth = poly([(960, -50), (960 + math.sin(ang) * 2200, 1100), (960 + math.sin(ang + 0.08) * 2200, 1100)])
        c.drawPath(pth, P(["#ff5fa2", "#5fe3ff", "#b05fff"][k % 3], a=0.18))
    box(c, 560, 110, 800, 240, "#1e0f36", r=20)
    neon(c, "Club Neon", 960, 260, 120, "#ff5fa2", SCRIPT)
    # dance floor
    for i in range(10):
        for j in range(4):
            col = ["#ff5fa2", "#5fe3ff", "#b05fff", "#ffd36b"][(i + j) % 4]
            pth = poly([(i * 192 - (j * 60), 780 + j * 75), ((i + 1) * 192 - (j * 60), 780 + j * 75),
                        ((i + 1) * 192 - ((j + 1) * 60), 855 + j * 75), (i * 192 - ((j + 1) * 60), 855 + j * 75)])
            c.drawPath(pth, P(col, a=0.55))
            c.drawPath(pth, P("#0a0414", 4))
    # disco ball
    c.drawCircle(960, 60, 70, P("#c9c9d9"))
    for k in range(-3, 4):
        line(c, 890, 60 + k * 18, 1030, 60 + k * 18, "#8a8aa0", 2)
    glow(c, 960, 60, 200, "#ffffff", 0.2)


def set_bank(c):
    sky(c, "#58ade3", "#9fd3f0", "#f4e6c8", y1=820)
    skyline(c, 820, "#a6c4d8", seed=33, hmin=200, hmax=500, wmin=60, wmax=130)
    pth = poly([(420, 270), (960, 110), (1500, 270)])
    shape(c, pth, "#e8e2d4")
    box(c, 440, 270, 1040, 60, "#f2ede2")
    T(c, "NATIONAL BANK", 960, 318, 50, "#3a3a3a", "inter")
    box(c, 440, 330, 1040, 450, "#e8e2d4")
    for k in range(6):
        x = 500 + k * 180
        box(c, x, 340, 60, 430, "#f7f3ea", r=6)
        for j in range(3):
            line(c, x + 15 + j * 15, 350, x + 15 + j * 15, 760, "#d8d2c4", 3)
    door(c, 880, 780, 160, 300, "#c9a86a")
    box(c, 380, 770, 1160, 30, "#d8d2c4")
    box(c, 340, 800, 1240, 30, "#c9c2b0")
    rect(c, 0, 830, W, 250, "#7a7a84")
    line(c, 0, 830, W, 830, OUT, 5)
    for x in (200, 1720):
        palm_green(c, x, 840, 0.95)


def set_vault(c):
    rect(c, 0, 0, W, H, "#3a3f48")
    wallpaper(c, 0, FLOOR, "#4a505a", "#3f444c", "panel")
    c.drawCircle(1400, 450, 330, P("#8a9098"))
    c.drawCircle(1400, 450, 330, P(OUT, 8))
    c.drawCircle(1400, 450, 260, P("#a8aeb6"))
    c.drawCircle(1400, 450, 260, P(OUT, 5))
    for k in range(6):
        ang = k * math.pi / 3
        line(c, 1400, 450, 1400 + math.cos(ang) * 120, 450 + math.sin(ang) * 120, "#5a6068", 18)
    c.drawCircle(1400, 450, 50, P("#5a6068"))
    for row in range(4):
        for col in range(5):
            box(c, 120 + col * 150, 160 + row * 140, 130, 120, "#b8a070", r=6, ow=4)
            oval(c, 185 + col * 150, 220 + row * 140, 12, 12, "#6a5a3a", ow=3)
    floor_planks(c, FLOOR, "#2a2e34", "#22262c", "tile")


def set_penthouse(c):
    rect(c, 0, 0, W, FLOOR, "#0e0c24")
    # glass walls with city view
    c.save()
    c.clipRect(skia.Rect(0, 60, W, FLOOR - 40))
    sky(c, "#060716", "#1b1446", "#4a1f5e", y1=FLOOR)
    skyline(c, FLOOR, "#1a1236", seed=41, hmin=120, hmax=500, wmin=40, wmax=110,
            lit=["#ffd36b", "#ff5fa2", "#5fe3ff"], lit_a=0.8)
    c.restore()
    for xx in range(0, W + 1, 320):
        line(c, xx, 60, xx, FLOOR, "#d8d2c4", 12)
    rect(c, 0, 0, W, 60, "#e8e2d4")
    floor_planks(c, FLOOR, "#e8e2d4", "#cfc8b8", "tile")
    # white sofa + statue
    couch(c, 640, FLOOR + 40, 640, "#f2efe6")
    box(c, 1500, FLOOR - 220, 90, 220, "#d8c9a0", r=10)
    oval(c, 1545, FLOOR - 270, 50, 60, "#e8c25a")


def set_lawyer(c):
    wallpaper(c, 0, FLOOR, "#5a3a2a", "#4a2e20", "panel")
    for k in range(4):
        box(c, 140, 140 + k * 120, 420, 16, "#7a5236", ow=3)
        rnd = random.Random(k)
        for j in range(12):
            col = rnd.choice(["#8b2e2e", "#2e4b8b", "#2e6b4b", "#8b6b2e"])
            h = rnd.uniform(70, 100)
            box(c, 150 + j * 33, 140 + k * 120 - h, 28, h, col, r=2, ow=2)
    window(c, 1200, 150, 420, 330, "sunset", curtains="#7a1e2e")
    frame_pic(c, 700, 180, 320, 230, "#f2efe6")
    T(c, "LAW DEGREE", 860, 300, 30, "#2a1a12", SERIF)
    floor_planks(c, FLOOR, "#6a2e2e", "#5a2424", "concrete")
    box(c, 360, 760, 1200, 70, "#6a4428", r=6)
    box(c, 400, 830, 1120, 220, "#5a3a22", ow=5)


def set_gym(c):
    wallpaper(c, 0, FLOOR, "#3a4048", "#323840", "brick")
    neon(c, "IRON GYM", 960, 190, 100, "#ffd36b", LUCKY)
    box(c, 200, 300, 300, 400, "#c8382e", ow=5)
    T(c, "NO", 350, 420, 60, "#ffffff", LUCKY)
    T(c, "PAIN", 350, 500, 60, "#ffffff", LUCKY)
    # weights rack
    box(c, 1300, 520, 480, 30, "#5a5f66", ow=4)
    for k in range(6):
        oval(c, 1340 + k * 80, 500, 30, 30, "#202024")
    # bag
    line(c, 640, 0, 640, 300, OUT, 6)
    box(c, 580, 300, 120, 320, "#a8282c", r=50)
    floor_planks(c, FLOOR, "#2a2e34", "#22262c", "tile")
    rrect(c, 0, FLOOR, W, 20, 0, "#ffd36b", 0.6)


def set_airport(c):
    sky(c, "#ff9a6a", "#ffcf9a", "#fff0d0", y1=760, sun=(400, 640), sun_r=100)
    box(c, 0, 520, W, 240, "#c9d6e2", ow=5)
    for xx in range(0, W, 120):
        box(c, xx + 10, 560, 100, 140, "#7aa6c8", ow=3)
    T(c, "VICE CITY INTERNATIONAL", 960, 500, 56, "#2a2a3a", LUCKY)
    rect(c, 0, 760, W, 320, "#6a6e74")
    line(c, 0, 760, W, 760, OUT, 5)
    for xx in range(0, W, 240):
        rect(c, xx + 30, 900, 150, 14, "#f2e6b8")
    # plane
    with xf(c, 1250, 760):
        box(c, -460, -230, 920, 160, "#f2f2f2", r=80)
        pth = poly([(-120, -160), (120, -160), (-40, 20), (-200, 20)])
        shape(c, pth, "#d8d8d8")
        pth = poly([(-440, -220), (-480, -380), (-380, -380), (-320, -220)])
        shape(c, pth, "#2fb3b8")
        for k in range(10):
            oval(c, -300 + k * 70, -180, 14, 14, "#7aa6c8", ow=3)
        oval(c, -200, -40, 30, 30, "#2a2a2a")
        oval(c, 260, -40, 30, 30, "#2a2a2a")


def set_bridge(c, lights=True):
    sky(c, "#05061a", "#141a40", "#2a1f5a", y1=700)
    stars(c, 100, ymax=420)
    skyline(c, 700, "#1a1236", seed=17, hmin=100, hmax=380, wmin=40, wmax=110,
            lit=["#ffd36b", "#ff5fa2", "#5fe3ff"], lit_a=0.7)
    grad_rect(c, 0, 700, W, 380, ["#0d1a3a", "#050a18"])
    for k in range(30):
        rnd = random.Random(k)
        x, y = rnd.uniform(0, W), rnd.uniform(720, H)
        line(c, x, y, x + rnd.uniform(40, 120), y, rnd.choice(["#ff5fa2", "#5fe3ff", "#ffd36b"]), 3, 0.3)
    # bridge deck
    box(c, -40, 600, W + 80, 70, "#3a3f58", ow=6)
    for xx in range(0, W, 140):
        box(c, xx, 520, 18, 80, "#5a6080", ow=3)
    box(c, -40, 512, W + 80, 18, "#6a7090", ow=4)
    # towers + cables
    for tx in (360, 1560):
        box(c, tx - 30, 160, 60, 520, "#4a5070", ow=5)
        for k in range(8):
            line(c, tx, 180, tx - 60 - k * 55, 600, "#8a90b0", 3)
            line(c, tx, 180, tx + 60 + k * 55, 600, "#8a90b0", 3)
    for xx in range(0, W, 180):
        box(c, xx, 670, 30, 410, "#252a40", ow=4)


def set_interrog(c):
    wallpaper(c, 0, FLOOR, "#5a6068", "#50565e", "block")
    floor_planks(c, FLOOR, "#3a3e44", "#2f3338", "tile")
    box(c, 1250, 180, 520, 300, "#1a1e26", ow=6)
    fill_shader(c, skia.Rect(1260, 190, 1760, 470), linear(1260, 190, 1760, 470, [("#ffffff", 0.12), ("#ffffff", 0)]))
    # hanging lamp
    line(c, 760, 0, 760, 160, OUT, 5)
    pth = poly([(690, 210), (830, 210), (790, 160), (730, 160)])
    shape(c, pth, "#3a3e44")
    pth = poly([(690, 210), (830, 210), (1100, FLOOR + 100), (420, FLOOR + 100)])
    c.drawPath(pth, P("#fff2c0", a=0.12))
    box(c, 360, 740, 800, 50, "#6a6e74", r=4)
    box(c, 400, 790, 30, 240, "#4a4e54", ow=4)
    box(c, 1090, 790, 30, 240, "#4a4e54", ow=4)


def set_visit(c):
    wallpaper(c, 0, FLOOR, "#b9c2b0", "#a9b2a0", "block")
    floor_planks(c, FLOOR, "#8a9080", "#7a8070", "tile")
    for k in range(3):
        x = 260 + k * 520
        box(c, x, 260, 440, 420, "#d8ecf2", a=0.35, ow=6)
        line(c, x + 60, 300, x + 160, 400, "#ffffff", 8, 0.4)
        box(c, x + 380, 400, 40, 80, "#2a2a2a", r=8, ow=3)
    box(c, 0, 680, W, 50, "#8a8a80", ow=5)
    box(c, 0, 730, W, 300, "#6a6a62", ow=5)


def set_home_happy(c):
    wallpaper(c, 0, FLOOR, "#f2d6a8", "#ebc994", "stripe")
    floor_planks(c, FLOOR, "#c9925a", "#a87440")
    baseboard(c, FLOOR)
    window(c, 1260, 180, 360, 320, "day", curtains="#e8735a")
    frame_pic(c, 300, 170, 200, 160, "#c9e2f2")
    frame_pic(c, 540, 150, 160, 200, "#f2c9d8")
    frame_pic(c, 740, 190, 220, 160, "#d8f2c9")
    couch(c, 420, FLOOR + 20, 700, "#3f8a8a")
    plant(c, 1180, FLOOR + 10, 1.0)
    lamp(c, 260, FLOOR, 320, shade="#ffe3a8", on=True)
    glow(c, 1440, 340, 500, "#fff2c0", 0.25)


def set_water(c):
    grad_rect(c, 0, 0, W, H, ["#1a6a9a", "#0a2a4a", "#04101e"])
    for k in range(9):
        x = 200 + k * 200
        pth = poly([(x, 0), (x + 80, 0), (x + 260, H), (x + 160, H)])
        c.drawPath(pth, P("#9fe3ff", a=0.06))


def set_backroom(c):
    wallpaper(c, 0, FLOOR, "#3a3026", "#30281f", "panel")
    floor_planks(c, FLOOR, "#2a221a", "#221b14", "concrete")
    for k in range(4):
        box(c, 180 + k * 140, FLOOR - 120 - (k % 2) * 120, 130, 120, "#b98a58", r=4, ow=4)
    box(c, 1300, FLOOR - 160, 400, 160, "#6a4a32", ow=4)
    line(c, 960, 0, 960, 120, OUT, 5)
    c.drawCircle(960, 140, 26, P("#fff2c0"))
    glow(c, 960, 160, 500, "#fff2c0", 0.2)


def set_fire(c, t=0.0):
    set_house_night(c)


def set_road_night(c):
    sky(c, "#05061a", "#141a40", "#2a2f6a", y1=640)
    stars(c, 90, ymax=480)
    grad_rect(c, 0, 640, W, 440, ["#0d2a3a", "#061420"])


SETS = {
    "vice_sunset": set_vice_sunset, "vice_night": set_vice_night, "map": set_map, "dark": set_dark_desk,
    "cork": set_cork, "living": set_living, "living_night": lambda c: set_living(c, "night"), "yard": set_yard,
    "street": set_street, "street_sunset": lambda c: set_street(c, "sunset"), "store": set_store_night,
    "cafe": set_cafe, "doorway": set_doorway, "cell": set_cell, "office": set_office, "keys": set_keys,
    "keys_night": lambda c: set_keys(c, "night"), "gate": set_gate, "bar": set_bar, "house_night": set_house_night,
    "motel": set_motel, "motel_night": lambda c: set_motel(c, "night"), "club": set_club, "bank": set_bank,
    "vault": set_vault, "penthouse": set_penthouse, "lawyer": set_lawyer, "gym": set_gym, "airport": set_airport,
    "bridge": set_bridge, "interrog": set_interrog, "visit": set_visit, "home_happy": set_home_happy,
    "water": set_water, "backroom": set_backroom, "road_night": set_road_night,
}


def bg(name, blur=0.0):
    return cached(("set", name, blur), SETS[name], blur=blur)
