"""Extra sets for the Tommy Vercetti video (Liberty City, Harwood, courtroom, junkyard, mansion...)."""
import math
import random

import skia

import sets as S
from sets import (W, H, C, P, xf, rrect, poly, line, linear, glow, mixhex, shape, oval, box, rect, grad_rect, T,
                  tw, palm, palm_green, sky, stars, skyline, wallpaper, floor_planks, baseboard, window, door, lamp,
                  neon, FLOOR, LUCKY, SERIF, SCRIPT, MARKER, OUT)


def brownstone(c, x, y, w, h, col, seed=0):
    rnd = random.Random(seed)
    box(c, x, y - h, w, h, col)
    for yy in range(int(y - h + 10), int(y), 26):
        line(c, x + 3, yy, x + w - 3, yy, mixhex(col, "#000000", 0.15), 2)
    box(c, x - 8, y - h - 18, w + 16, 22, mixhex(col, "#000000", 0.3))
    rows = int((h - 120) // 110)
    for r in range(rows):
        for k in range(3):
            wx = x + 24 + k * (w - 48) / 3
            wy = y - h + 40 + r * 110
            lit = rnd.random() < 0.35
            box(c, wx, wy, (w - 48) / 3 - 18, 70, "#ffd98a" if lit else "#3a4656", ow=3)
            line(c, wx + ((w - 48) / 3 - 18) / 2, wy, wx + ((w - 48) / 3 - 18) / 2, wy + 70, OUT, 3)
        # fire escape
        fy = y - h + 118 + r * 110
        line(c, x + w * 0.55, fy, x + w - 10, fy, "#20242a", 6)
        for k in range(6):
            line(c, x + w * 0.55 + k * (w * 0.45 - 10) / 5, fy, x + w * 0.55 + k * (w * 0.45 - 10) / 5, fy - 26,
                 "#20242a", 3)
    door(c, x + w / 2 - 50, y, 100, 170, "#4a2e1e")


def set_liberty_street(c):
    sky(c, "#6f7b8a", "#a9b3bf", "#d5d9de", y1=760)
    skyline(c, 600, "#8a94a3", seed=5, hmin=200, hmax=480, wmin=40, wmax=90)
    cols = ["#7a4a3a", "#8a5a46", "#6a3e32", "#7e5644", "#5e3a30"]
    for i in range(5):
        brownstone(c, -40 + i * 400, 790, 380, 560 + (i % 2) * 60, cols[i], seed=i)
    rect(c, 0, 790, W, 60, "#a8a49a")
    line(c, 0, 790, W, 790, OUT, 4)
    rect(c, 0, 850, W, 230, "#4a4a50")
    line(c, 0, 850, W, 850, OUT, 5)
    for xx in range(0, W, 260):
        rect(c, xx + 40, 960, 140, 10, "#e8e2c8", 0.8)
    for x in (300, 1300):
        line(c, x, 850, x, 520, OUT, 12)
        line(c, x, 850, x, 520, "#3a3e44", 7)
        box(c, x - 30, 500, 60, 30, "#3a3e44", r=6, ow=4)
        S.glow(c, x, 520, 120, "#ffe9a8", 0.25)
    for k in range(40):
        rnd = random.Random(k)
        c.drawCircle(rnd.uniform(0, W), rnd.uniform(0, 760), rnd.uniform(1.5, 3), P("#ffffff", a=0.7))


def set_liberty_night(c):
    set_liberty_street(c)
    S.tint(c, "#0a1030", 0.55)


def set_harwood(c):
    S.sky(c, "#05060f", "#10142a", "#1c2238", y1=700)
    S.stars(c, 60, ymax=300)
    box(c, 200, 180, 1520, 640, "#3a3a40")
    for yy in range(200, 820, 40):
        line(c, 210, yy, 1710, yy, "#33333a", 3)
    box(c, 640, 120, 640, 110, "#22222a", r=6)
    T(c, "HARWOOD", 960, 205, 80, "#c9c2b0", LUCKY)
    T(c, "AUTO PARTS & STORAGE", 960, 250, 26, "#8a8a8a", "interb")
    box(c, 760, 420, 400, 400, "#2a2a30", ow=6)
    for yy in range(430, 820, 26):
        line(c, 765, yy, 1155, yy, "#3a3a42", 3)
    lamp_x = 960
    line(c, lamp_x, 330, lamp_x, 380, OUT, 5)
    pth = poly([(lamp_x - 40, 400), (lamp_x + 40, 400), (lamp_x + 20, 380), (lamp_x - 20, 380)])
    shape(c, pth, "#5a5a60")
    c.drawPath(poly([(lamp_x - 40, 400), (lamp_x + 40, 400), (lamp_x + 260, 1080), (lamp_x - 260, 1080)]),
               P("#fff2c0", a=0.12))
    rect(c, 0, 820, W, 260, "#1c1c22")
    line(c, 0, 820, W, 820, OUT, 5)
    for x in (360, 1560):
        box(c, x - 60, 700, 120, 120, "#4a3a2a", r=4, ow=4)
        box(c, x - 40, 620, 80, 80, "#5a4a3a", r=4, ow=4)


def set_court(c):
    wallpaper(c, 0, FLOOR, "#6a4428", "#5a3820", "panel")
    floor_planks(c, FLOOR, "#7a5236", "#5a3d2a")
    box(c, 560, 300, 800, 380, "#5a3820", r=6, ow=6)
    box(c, 520, 280, 880, 40, "#7a5236", r=6, ow=5)
    oval(c, 960, 170, 90, 90, "#c9a24a", ow=6)
    T(c, "LIBERTY CITY", 960, 160, 22, "#3a2a1a", "interb")
    T(c, "COURT", 960, 190, 22, "#3a2a1a", "interb")
    for x in (300, 1620):
        box(c, x - 18, 120, 36, 700, "#7a5236", ow=4)
    box(c, 200, 760, 1520, 30, "#7a5236", ow=5)


def set_junkyard(c):
    sky(c, "#7a3a2a", "#e08a4a", "#ffd08a", y1=760, sun=(1500, 640), sun_r=90)
    rnd = random.Random(9)
    for k in range(9):
        x = -80 + k * 240
        h = rnd.uniform(160, 320)
        for j in range(4):
            col = rnd.choice(["#6a4a3a", "#5a5a64", "#7a3a2a", "#4a5a4a"])
            box(c, x + rnd.uniform(-20, 20), 760 - h + j * h / 4, 220, h / 4 - 6, col, r=10, ow=4)
    rect(c, 0, 760, W, 320, "#6a5a48")
    line(c, 0, 760, W, 760, OUT, 5)
    with xf(c, 1450, 560):
        line(c, 0, 0, 0, 200, OUT, 18)
        line(c, 0, 0, -260, -180, "#d8a23a", 20)
        line(c, -260, -180, -260, -40, OUT, 6)
        oval(c, -260, -20, 60, 30, "#5a5a64")


def set_mansion(c):
    sky(c, "#58ade3", "#9fd3f0", "#f4e6c8", y1=760)
    box(c, 360, 280, 1200, 480, "#f4efe6")
    pth = poly([(320, 290), (960, 120), (1600, 290)])
    shape(c, pth, "#c96a4a")
    for k in range(8):
        x = 420 + k * 150
        box(c, x, 300, 46, 460, "#ffffff", r=6)
    box(c, 840, 520, 240, 240, "#8a5a3a", ow=6)
    T(c, "V", 960, 470, 90, "#c9a24a", SERIF)
    for x in (520, 1340):
        for y in (360, 560):
            box(c, x - 60, y, 120, 120, "#9fd3ef", ow=4)
    rect(c, 0, 760, W, 320, "#7cbf5a")
    line(c, 0, 760, W, 760, OUT, 5)
    oval(c, 960, 900, 220, 50, "#bfe3f2")
    oval(c, 960, 880, 50, 60, "#e8e2d4")
    for x in (180, 1740, 380, 1540):
        palm_green(c, x, 780, 1.0 if x in (180, 1740) else 0.8)


def set_roof(c):
    S.set_vice_night(c)
    box(c, -20, 760, W + 40, 340, "#5a5a64", ow=6)
    for xx in range(0, W, 120):
        box(c, xx, 720, 30, 60, "#6a6a74", ow=4)
    box(c, -20, 700, W + 40, 30, "#7a7a84", ow=5)


def set_balcony(c):
    S.set_vice_sunset(c)
    box(c, -20, 840, W + 40, 260, "#e8e2d4", ow=6)
    for xx in range(0, W, 90):
        box(c, xx + 20, 720, 40, 120, "#f4efe6", r=14, ow=4)
    box(c, -20, 700, W + 40, 30, "#f4efe6", ow=5)


def set_office_m(c):
    S.set_penthouse(c)
    box(c, 560, 700, 800, 70, "#6a4428", r=6)
    box(c, 600, 770, 720, 300, "#5a3a22", ow=5)
    box(c, 860, 600, 200, 100, "#3a3a44", r=8, ow=4)


def set_club_malibu(c):
    S.set_club(c)
    box(c, 560, 110, 800, 240, "#1e0f36", r=20)
    neon(c, "Malibu", 960, 270, 140, "#5fe3ff", SCRIPT)


def set_bank_vc(c):
    S.set_bank(c)
    box(c, 440, 270, 1040, 60, "#f2ede2")
    T(c, "EL BANCO CORRUPTO GRANDE", 960, 316, 44, "#3a3a3a", "inter")


def set_airport_vc(c):
    S.set_airport(c)


S.SETS.update({
    "liberty_street": set_liberty_street, "liberty_night": set_liberty_night, "harwood": set_harwood,
    "court": set_court, "junkyard": set_junkyard, "mansion": set_mansion, "roof": set_roof, "balcony": set_balcony,
    "office_m": set_office_m, "club_malibu": set_club_malibu, "bank_vc": set_bank_vc,
})
