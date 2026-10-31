"""Scene timeline for 'What if a black hole stretched you?'. Times are absolute seconds in the voiceover."""
import json
import math
import os

import skia

from sgfx import *  # noqa: F401,F403

HERE = os.path.dirname(os.path.abspath(__file__))
BURN_CAPTIONS = os.environ.get("BURN_CAPTIONS", "0") == "1"


# ---------------------------------------------------------------- camera helpers
def cam(c, zoom=1.0, cx=W / 2, cy=H / 2, t=0.0, shake=0.0, drift=1.0):
    dx = drift * (6 * math.sin(t * 0.37) + 3 * math.sin(t * 0.91)) + shake * (math.sin(t * 53) * 9 + math.sin(t * 31) * 6)
    dy = drift * (4 * math.sin(t * 0.29 + 1) + 2 * math.sin(t * 1.13)) + shake * (math.cos(t * 47) * 9)
    c.translate(W / 2 + dx, H / 2 + dy)
    c.scale(zoom, zoom)
    c.translate(-cx, -cy)


def push(t, a, b, z0, z1):
    return lerp(z0, z1, smooth((t - a) / max(0.01, b - a)))


def space(c, t, bh=(1350, 760, 190), drift=(-6, 3), streak=0.0, disk=1.0, lens=0.6):
    starfield(c, t, drift=drift, streak=streak, center=bh, lens=lens)
    if bh:
        black_hole(c, bh[0], bh[1], bh[2], t, disk)


def bubble_line(c, x, y, s, t, start, end=None, color="#ffffff", fg="#0b1018", size=40):
    k = back_out(at(t, start, 0.3))
    out = 1.0 if end is None else clamp((end - t) / 0.25)
    if k <= 0 or out <= 0:
        return
    w = text_width(s, size) + 60
    h = size * 1.8
    with xf(c, x, y, k, alpha=clamp(k) * out):
        c.drawPath(poly([(-w * 0.15, h * 0.35), (-w * 0.32, h * 0.95), (w * 0.02, h * 0.4)]), P(color))
        rrect(c, -w / 2, -h / 2, w, h, h / 2, color)
        text(c, s, 0, size * 0.36, size, fg, "Black")


# ---------------------------------------------------------------- 1. HOOK
def s_hook_fall(c, t):
    # 0 - 3.4: falling feet first toward the hole
    z = push(t, 0, 3.6, 1.0, 1.25)
    cam(c, z, 960, 560, t, shake=0.25)
    space(c, t, bh=(1150, 1080, 330), drift=(0, -260), streak=0.6)
    sway = 6 * math.sin(t * 1.3)
    figure(c, 900, 560, "kai", "fall", "scared", t, s=1.0, space=True, stretch=0.08 + 0.04 * t, rot=sway,
           look=(0, 1))


def s_hook_boots(c, t):
    # 4.0 - 7.0: boots heavier than the helmet
    cam(c, push(t, 3.6, 7.3, 1.0, 1.08), 960, 540, t, shake=0.3)
    space(c, t, bh=(960, 1300, 420), drift=(0, -300), streak=0.8)
    figure(c, 960, 470, "kai", "fall", "worried", t, s=1.0, space=True, stretch=0.15, rot=0, look=(0, 1))
    k = at(t, 4.3, 0.4)
    if k:
        for i, (x, L, col) in enumerate(((900, 260, "#ff6a3a"), (1020, 260, "#ff6a3a"))):
            arrow(c, x, 600, x, 600 + L * ease_out(k), col, 26, a=k)
        arrow(c, 960, 40, 960, 40 + 60 * ease_out(k), "#5bd6ff", 14, a=k)
        tag(c, 1260, 820, "BOOTS: HEAVY", "#ff6a3a", 40, a=k)
        tag(c, 1260, 140, "HELMET: LIGHT", "#5bd6ff", 34, a=k)


def s_hook_stretch(c, t):
    # 7.6 - 12.5: legs pulled longer, shoulders squeezed thinner
    st = 0.15 + 0.55 * smooth((t - 7.4) / 5.0)
    cam(c, push(t, 7.3, 12.8, 1.0, 1.12), 960, 540, t, shake=0.35)
    space(c, t, bh=(960, 1250, 380), drift=(0, -380), streak=1.0)
    figure(c, 960, 430, "kai", "fall", "scared", t, s=0.9, space=True, stretch=st, rot=0, look=(0, 1))
    k1 = window(t, 7.7, 10.2, 0.25)
    if k1:
        arrow(c, 760, 500, 760, 820, "#ff6a3a", 18, a=k1)
        arrow(c, 1160, 500, 1160, 820, "#ff6a3a", 18, a=k1)
        tag(c, 760, 880, "LONGER", "#ff6a3a", 40, a=k1)
    k2 = window(t, 10.3, 12.9, 0.25)
    if k2:
        arrow(c, 700, 300, 880, 300, "#5bd6ff", 18, a=k2)
        arrow(c, 1220, 300, 1040, 300, "#5bd6ff", 18, a=k2)
        tag(c, 960, 160, "THINNER", "#5bd6ff", 40, a=k2)


def s_hook_crew(c, t):
    # 13.4 - 18.9: crew watching, figure slows, turns red, freezes
    cam(c, push(t, 13.0, 19.0, 1.0, 1.08), 960, 540, t)
    draw_set(c, "bridge", 8)
    # sharp window insert over the blurred set
    c.save()
    c.clipRRect(skia.RRect.MakeRectXY(skia.Rect(380, 140, 1540, 660), 30, 30), skia.ClipOp.kIntersect, True)
    starfield(c, t, (380, 140, 1540, 660))
    black_hole(c, 1180, 470, 110, t)
    prog = 1 - math.exp(-(t - 13.0) * 0.55)
    fx, fy = lerp(700, 1040, prog), lerp(300, 440, prog)
    red = clamp((t - 17.4) / 1.0)
    figure(c, fx, fy, "kai", "fall", "scared", t, s=0.18, space=True, rot=-35, red=red,
           alpha=1 - 0.4 * clamp((t - 18.2) / 0.8))
    c.restore()
    vignette(c, 0.5)
    for i, (who, x, face) in enumerate((("tomas", 560, 1), ("yuki", 960, 1), ("lena", 1360, -1))):
        figure(c, x, 1140, who, "stand", "worried" if t > 16 else "focus", t, s=1.35, face=face, look=(0.3, -1),
               rim_off=(-9, -8))
    k = window(t, 15.9, 19.0, 0.25)
    if k:
        tag(c, 960, 90, "SLOWER", "#ffb347", 34, a=window(t, 15.9, 17.4, 0.2))
        tag(c, 960, 90, "RED", "#ff4a2a", 34, a=window(t, 17.5, 18.2, 0.15))
        tag(c, 960, 90, "FROZEN", "#bfe8ff", 34, a=window(t, 18.2, 19.4, 0.15))


def s_hook_split(c, t):
    # 19.3 - 23.6: seconds vs forever
    for side in (0, 1):
        c.save()
        clip_half(c, side, seed=3)
        if side == 0:
            space(c, t, bh=(560, 1150, 360), drift=(0, -300), streak=0.8)
            figure(c, 480, 380, "kai", "fall", "scared", t, s=0.8, space=True, stretch=0.4, rot=0)
            stopwatch(c, 480, 820, 0.85, (t - 19.3) * 1.2, "#ff6a3a", "SECONDS")
        else:
            draw_set(c, "bridge", 8)
            tint(c, "#000000", 0.35)
            figure(c, 1300, 1050, "lena", "stand", "sad", t, s=1.1, face=-1, look=(-0.4, -1))
            figure(c, 1620, 1080, "tomas", "stand", "worried", t, s=1.1, face=-1, look=(-0.4, -1))
            stopwatch(c, 1440, 330, 0.85, 0.08, "#bfe8ff", "FOREVER", frozen=True)
        c.restore()
    jagged_split(c, seed=3)
    tag(c, 480, 110, "TO YOU", "#ff6a3a", 36, a=at(t, 19.4, 0.3))
    tag(c, 1440, 110, "TO EVERYONE WATCHING", "#bfe8ff", 36, a=at(t, 21.2, 0.3))


def s_rewind(c, t):
    # 23.6 - 26.8: how did you get here? three hours earlier
    space(c, t, bh=(1150, 900, 260), drift=(0, 900), streak=0.9)
    tint(c, "#0b1424", 0.55)
    for i in range(7):
        y = (i * 170 + t * 1400) % H
        c.drawRect(skia.Rect(0, y, W, y + 5), P("#ffffff", a=0.12))
    k = back_out(at(t, 23.9, 0.3))
    with xf(c, 960, 420, k, alpha=clamp(k)):
        for i in range(2):
            c.drawPath(poly([(-90 + i * 100, 0), (10 + i * 100, -60), (10 + i * 100, 60)]), P("#ffffff"))
    kicker(c, t, 24.0, "HOW DID YOU GET HERE?", 620, 72)
    kicker(c, t, 25.2, "3 HOURS EARLIER", 720, 44, "#ffb347", accent="#ffb347")


# ---------------------------------------------------------------- 2. MEET KAI
def s_meet_kai(c, t):
    # 26.8 - 30.6
    cam(c, push(t, 26.8, 30.6, 1.15, 1.25), 900, 560, t)
    draw_set(c, "corridor", 9)
    vignette(c, 0.45)
    if t < 29.1:
        figure(c, 900, 1060, "kai", "mug", "neutral", t, s=1.6, look=(0.6, 0),
               hold=lambda c_, x, y: mug(c_, x + 14, y - 14, 1.3, t))
    else:
        figure(c, 900, 1060, "kai", "fingerguns", "happy", t, s=1.6, look=(0.6, 0))
        for i in range(3):
            sparkle(c, 1180 + i * 60, 420 - i * 40, 20, "#ffd37a", 0.8 * at(t, 29.2 + i * 0.1, 0.2))
    lower_third(c, t, 27.0, "KAI", "Ship's engineer", "#e8742a", dur=3.5)
    k = window(t, 29.1, 30.7, 0.15)
    if k:
        tag(c, 1400, 420, "PROFESSIONAL JOKER", "#ffd37a", 40, a=k, sc=back_out(at(t, 29.1, 0.3)))


def s_closest(c, t):
    # 30.6 - 34.4
    cam(c, push(t, 30.6, 34.5, 1.0, 1.1), 960, 540, t)
    space(c, t, bh=(1350, 600, 220), drift=(-10, 0))
    ship(c, 520, 380, 0.9, t)
    kicker(c, t, 31.4, "CLOSER THAN ANY HUMAN IN HISTORY", 960, 54, accent="#ffb347")


# ---------------------------------------------------------------- 3. TIDAL FORCES
def s_tidal(c, t):
    # 34.4 - 50.2
    info_board(c, t)
    if t < 39.2:
        # Earth: equal pull
        k = ease_out(at(t, 34.6, 0.6))
        c.drawCircle(960, 1500, 760, P("#1d5fa8"))
        c.drawCircle(960, 1500, 760, P("#5bd6ff", 6, 0.6))
        figure(c, 960, 640, "kai", "stand", "neutral", t, s=1.1, look=(0, 0.3))
        for y, lab in ((330, "HEAD"), (720, "FEET")):
            arrow(c, 1170, y, 1170, y + 90 * k, "#5bd6ff", 14, a=k)
            text(c, lab, 1240, y + 60, 36, "#9fd0ff", "Black", align="left", a=k)
        kicker(c, t, 35.0, "ON EARTH: ALMOST THE SAME PULL", 150, 52)
        return
    # near the edge
    black_hole(c, 960, 1260, 300, t, 0.8)
    figure(c, 960, 640, "kai", "fall", "scared", t, s=1.0, space=True, rot=0, stretch=0.1 * at(t, 41.9, 2.0))
    kh = at(t, 41.0, 0.5)
    kf = ease_out(at(t, 41.9, 1.6))
    arrow(c, 1220, 260, 1220, 320, "#5bd6ff", 14, a=kh)
    text(c, "HEAD", 1270, 300, 36, "#9fd0ff", "Black", align="left", a=kh)
    arrow(c, 1220, 680, 1220, 680 + 330 * kf, "#ff6a3a", 30, a=kh)
    text(c, "FEET", 1270, 720, 36, "#ffb08a", "Black", align="left", a=kh)
    k, a2 = back_out(at(t, 42.6, 0.4)), at(t, 42.6, 0.3)
    with xf(c, 520, 560, k, alpha=a2):
        text(c, "20,000,000×", 0, 0, 110, "#ff8a4a", "Black", shadow=True)
        text(c, "YOUR WEIGHT", 0, 70, 40, "#ffffff", "Black")
    kicker(c, t, 39.3, "NEAR THE EDGE", 150, 56, "#ffb347")
    k3 = window(t, 48.6, 50.4, 0.2)
    if k3:
        tag(c, 520, 800, "ONE RULE", "#ffffff", 44, a=k3)


def s_horizon(c, t):
    # 50.2 - 58.2
    info_board(c, t)
    cx, cy = 1120, 560
    black_hole(c, cx, cy, 170, t, 0.7)
    k = ease_out(at(t, 50.6, 0.8))
    R = 260
    dash = skia.Paint(AntiAlias=True, Color=C("#ff5a3a"), Style=skia.Paint.kStroke_Style, StrokeWidth=6,
                      PathEffect=skia.DashPathEffect.Make([22, 16], t * 30))
    pth = skia.Path()
    pth.addArc(skia.Rect(cx - R, cy - R, cx + R, cy + R), -90, 360 * k)
    c.drawPath(pth, dash)
    tag(c, cx, cy - R - 50, "EVENT HORIZON", "#ff5a3a", 38, a=k)
    items = (("SHIP", 54.3), ("SIGNAL", 55.2), ("LIGHT", 56.6))
    for i, (lab, st) in enumerate(items):
        y = 300 + i * 220
        p = clamp((t - st) / 1.2)
        x = lerp(260, cx - R + 30, ease_out(p))
        a = at(t, st - 0.3, 0.3)
        if lab == "SHIP":
            ship(c, x, y, 0.22, t)
        elif lab == "SIGNAL":
            for k2 in range(3):
                c.drawCircle(x, y, 20 + k2 * 22, P("#5bd6ff", 5, a * (0.8 - k2 * 0.2)))
        else:
            line(c, x - 160, y, x, y, "#fff3c4", 8, a)
            glow(c, x, y, 50, "#fff3c4", 0.6 * a)
        text(c, lab, 260, y - 60, 34, "#ffffff", "Black", align="center", a=a)
        if p >= 1:
            cross_mark(c, 520, y, 50, "#ff4a4a", at(t, st + 1.2, 0.2))
    kicker(c, t, 53.1, "NOTHING COMES BACK", 980, 60, "#ffffff", accent="#ff5a3a")


def s_title(c, t):
    # 58.2 - 60.8 : episode title card
    space(c, t, bh=(960, 560, 200), drift=(-4, 0))
    tint(c, "#000000", 0.35)
    k = ease_out(at(t, 58.4, 0.6))
    with xf(c, 960, 860, 0.9 + 0.1 * k, alpha=k):
        text(c, "WHAT IF A BLACK HOLE", 0, 0, 76, "#ffffff", "Black", shadow=True)
        text(c, "STRETCHED YOU?", 0, 92, 96, "#ffb347", "Black", shadow=True)


# ---------------------------------------------------------------- 4. THE WINDOW
def s_window(c, t):
    # 60.8 - 69.3
    if t < 62.3:
        cam(c, 1.2, 1000, 560, t)
        draw_set(c, "quarters", 8)
        vignette(c, 0.45)
        figure(c, 1000, 1080, "kai", "stand", "neutral", t, s=1.5, face=1, look=(1, -0.3))
        return
    # POV out the window
    z = push(t, 62.3, 69.3, 1.0, 1.15)
    cam(c, z, 960, 540, t, drift=0.4)
    bh = (960, 540, 230)
    starfield(c, t, center=bh, lens=1.0)
    c.drawCircle(960, 540, 230, P("#000000"))
    if t > 67.6:
        glow(c, 960, 540, 330, "#1b2a44", 0.2)
    # porthole frame
    fr = skia.Path()
    fr.addRect(skia.Rect(-200, -200, W + 200, H + 200))
    fr.addCircle(960, 540, 470)
    fr.setFillType(skia.PathFillType.kEvenOdd)
    c.drawPath(fr, P("#141e2e"))
    c.drawCircle(960, 540, 470, P("#2a3850", 40))
    for i in range(8):
        a = math.radians(i * 45)
        c.drawCircle(960 + math.cos(a) * 470, 540 + math.sin(a) * 470, 12, P("#4a5a78"))
    kicker(c, t, 63.4, "NOTHING.", 140, 56, "#ffffff", end=64.3)
    k = window(t, 64.3, 69.4, 0.3)
    if k:
        tag(c, 960, 140, "A PERFECT BLACK CIRCLE", "#ffffff", 40, a=k)
    k = window(t, 67.6, 69.4, 0.2)
    if k:
        tag(c, 960, 950, "NO LIGHT AT ALL", "#ff6a3a", 36, a=k)


def s_scale(c, t):
    # 69.3 - 79.4
    info_board(c, t)
    if t < 74.9:
        # 10 suns
        for i in range(10):
            k = back_out(at(t, 69.6 + i * 0.1, 0.35))
            x = 260 + (i % 5) * 120
            y = 380 + (i // 5) * 130
            with xf(c, x, y, k):
                glow(c, 0, 0, 80, "#ffb347", 0.4)
                c.drawCircle(0, 0, 46, P("#ffd37a"))
        text(c, "10 SUNS", 500, 680, 64, "#ffd37a", "Black", a=at(t, 70.2, 0.3))
        k = ease_out(at(t, 72.4, 0.6))
        black_hole(c, 1350, 520, 130, t, 0.7)
        if k:
            line(c, 1350, 520, 1350 + 300 * k, 520, "#ffffff", 6)
            c.drawCircle(1350, 520, 300 * k, P("#ff5a3a", 4, 0.7))
            tag(c, 1500, 470, "30 KM", "#ffffff", 40, a=k)
        kicker(c, t, 72.6, "EDGE: JUST 30 KM FROM THE CENTER", 900, 50)
        return
    # squeezed: drive across in under an hour
    p = clamp((t - 76.5) / 2.6)
    cx, cy = 960, 560
    k = ease_out(at(t, 74.9, 0.6))
    c.drawCircle(cx, cy, 330 * k, P("#000000"))
    c.drawCircle(cx, cy, 330 * k, P("#ff8a3a", 6, 0.8))
    for i in range(10):
        a = i * 0.628 + t * 0.4
        glow(c, cx + math.cos(a) * 520 * (1 - k * 0.7), cy + math.sin(a) * 520 * (1 - k * 0.7), 60, "#ffb347", 0.5 * (1 - k))
    line(c, cx - 330, cy + 380, cx + 330, cy + 380, "#ffffff", 4, 0.5)
    car_x = lerp(cx - 330, cx + 330, p)
    with xf(c, car_x, cy + 360):
        rrect(c, -50, -34, 100, 30, 10, "#5bd6ff")
        rrect(c, -30, -54, 60, 26, 10, "#5bd6ff")
        c.drawCircle(-30, -2, 12, P("#ffffff"))
        c.drawCircle(30, -2, 12, P("#ffffff"))
    stopwatch(c, 1580, 520, 0.6, p * 0.9, "#5bd6ff", "< 1 HOUR")
    kicker(c, t, 75.0, "10 SUNS IN A BALL YOU COULD DRIVE ACROSS", 150, 50)


# ---------------------------------------------------------------- 5. YUKI
def s_yuki(c, t):
    # 79.4 - 87.1
    cam(c, push(t, 79.4, 87.1, 1.1, 1.2), 960, 560, t)
    draw_set(c, "lab", 8)
    vignette(c, 0.45)
    alert = t > 81.6
    screen_panel(c, 1120, 330, 460, 300, t, "graph", alert=alert)
    if alert:
        text(c, "TOO CLOSE", 1350, 500, 60, "#ff4a4a", "Black", a=0.7 + 0.3 * math.sin(t * 8))
    figure(c, 850, 1080, "yuki", "tap" if t < 81.7 else "point", "focus" if t < 81.6 else "worried", t, s=1.5,
           face=1, look=(1, -0.3), talk=1.0 if 81.7 < t < 82.4 else 0)
    lower_third(c, t, 79.6, "DR. YUKI", "Ship's scientist", "#9b7cf0", dur=2.4)
    k = window(t, 82.8, 85.0, 0.2)
    if k:
        with xf(c, 450, 300, alpha=k):
            text(c, "SAID IT", 0, 0, 40, "#ffffff", "Black")
            for i in range(4):
                if t > 83.0 + i * 0.25:
                    line(c, -60 + i * 30, 30, -60 + i * 30, 110, "#ffd37a", 10)
            if t > 84.0:
                line(c, -80, 100, 60, 40, "#ffd37a", 10)
    if t > 85.0:
        figure(c, 300, 1100, "kai", "mug", "focus", t, s=1.35, face=1, look=(1, 0.6),
               hold=lambda c_, x, y: phone(c_, x + 10, y - 30, 1.1, -70, glow_a=0.3))
        tag(c, 560, 360, "CHECKING HER NUMBERS", "#e8742a", 32, a=at(t, 85.1, 0.3))


def s_danger_map(c, t):
    # 87.1 - 99.5
    info_board(c, t)
    cx, cy = 560, 560
    black_hole(c, cx, cy, 70, t, 0.7)
    k = ease_out(at(t, 87.4, 0.8))
    for i in range(3):
        c.drawCircle(cx, cy, (160 + i * 120) * k, P("#ff4a2a", a=0.10))
    c.drawCircle(cx, cy, 520 * k, P("#ff4a2a", 4, 0.6))
    tag(c, cx, cy + 560 * k - 10, "DEADLY STRETCH ZONE", "#ff4a2a", 30, a=k)
    back = smooth((t - 90.7) / 2.5)
    sx = lerp(1180, 1600, back)
    ship(c, sx, 420, 0.35, t)
    if 90.7 < t < 94.6:
        arrow(c, sx + 80, 500, sx + 260, 500, "#5bd6ff", 12, a=window(t, 90.7, 94.6, 0.3))
    kicker(c, t, 87.4, "HUNDREDS OF KM OUT: ALREADY DEADLY", 150, 46)
    if t > 92.8:
        figure(c, 1420, 1090, "yuki", "point", "focus", t, s=1.0, face=-1, look=(-1, -0.4),
               talk=1.0 if 95.2 < t < 98.0 else 0)
        k = at(t, 95.2, 0.4)
        bubble_line(c, 1360, 560, "FEET PULLED HARDER THAN HEAD", t, 95.2, None, size=32)


def s_rope(c, t):
    # 99.5 - 110.7
    info_board(c, t, "#120d1c", "#07050c")
    if t < 107.4:
        k = ease_out(at(t, 99.7, 0.6))
        # rope body between two black holes (both teams are the black hole)
        black_hole(c, 220, 560, 90, t, 0.6)
        black_hole(c, 1700, 560, 90, t, 0.6)
        tug = 30 * math.sin(t * 3)
        line(c, 320, 560, 1600, 560, "#c9a55a", 18, k)
        figure(c, 960 + tug, 620, "kai", "fall", "scared", t, s=0.85, space=True, rot=-90, stretch=0.3)
        for x, d in ((360, -1), (1560, 1)):
            arrow(c, x + d * -120, 640, x, 640, "#ff6a3a", 16, a=at(t, 100.3, 0.4))
        k2 = at(t, 102.3, 0.4)
        if k2:
            tag(c, 220, 380, "BLACK HOLE", "#ff6a3a", 30, a=k2)
            tag(c, 1700, 380, "BLACK HOLE", "#ff6a3a", 30, a=k2)
        kicker(c, t, 99.8, "A TUG OF WAR", 160, 60)
        kicker(c, t, 104.8, "SCIENTISTS HAVE A REAL NAME FOR IT", 900, 44, "#c9b8ff")
        return
    # SPAGHETTIFICATION
    k = back_out(at(t, 107.6, 0.5))
    with xf(c, 960, 420, 0.7 + 0.3 * k, alpha=clamp(k)):
        text(c, "SPAGHETTIFICATION", 0, 0, 120, "#ffd37a", "Black", shadow=True)
    if t > 109.0:
        p = skia.Path()
        p.moveTo(600, 760)
        for i in range(1, 40):
            x = 600 + i * 18
            p.lineTo(x, 760 + 40 * math.sin(i * 0.5 + t * 4))
        c.drawPath(p, P(OUT, 46))
        c.drawPath(p, P("#e8742a", 36))
        head_only(c, 590, 740, "kai", "deadpan", t, r=56)
        tag(c, 1180, 920, "YOU BECOME A NOODLE", "#e8742a", 38, a=at(t, 109.0, 0.3))


def s_coffee(c, t):
    # 110.7 - 117.4
    cam(c, 1.1, 960, 560, t)
    draw_set(c, "bridge", 8)
    vignette(c, 0.45)
    if t < 113.3:
        figure(c, 640, 1080 + 6 * math.sin(t * 12), "tomas", "laugh", "laugh", t, s=1.4, face=1)
        figure(c, 1260, 1080, "kai", "stand", "deadpan", t, s=1.4, face=-1, look=(-1, 0))
        lower_third(c, t, 110.9, "TOMAS", "Pilot · best friend", "#4f9a64", dur=2.4)
        if t > 112.1:
            tag(c, 1260, 300, "YOU DON'T.", "#ffffff", 40, a=at(t, 112.1, 0.25))
        return
    fl = (t - 113.3)
    x = lerp(500, 1150, smooth(fl / 3.5))
    y = 760 + 18 * math.sin(t * 1.4)
    figure(c, x, y, "kai", "float", "neutral", t, s=1.3, face=1, look=(1, -0.2), rot=6 * math.sin(t * 0.8))
    mug(c, x + 250, y - 280 + 22 * math.sin(t * 1.7 + 1), 1.4, t, face=t > 115.9, rot=12 * math.sin(t * 1.1))
    # floating coffee blobs
    for i in range(4):
        bx = x + 330 + 30 * i + 10 * math.sin(t * 2 + i)
        by = y - 420 - 20 * i + 12 * math.cos(t * 1.6 + i)
        c.drawCircle(bx, by, 9 - i, P("#7a4a2a"))
    k = window(t, 115.9, 117.5, 0.2)
    if k:
        tag(c, 1460, 300, "IT FLOATS WITH YOU", "#ffb347", 34, a=k)


def s_probe(c, t):
    # 117.4 - 141.9
    if t < 120.1:
        cam(c, 1.15, 960, 560, t)
        draw_set(c, "bridge", 8)
        vignette(c, 0.45)
        figure(c, 820, 1080, "tomas", "tap", "smile", t, s=1.4, face=1, look=(1, 0))
        rrect(c, 1080, 760, 200, 60, 12, OUT)
        rrect(c, 1086, 766, 188, 48, 10, "#ff4a4a" if t > 118.6 else "#a02020")
        text(c, "LAUNCH", 1180, 802, 30, "#ffffff", "Black")
        return
    if t < 131.1:
        # window POV: probe falls fast then slower, red, dim, frozen
        cam(c, push(t, 120.1, 131.1, 1.0, 1.18), 1100, 520, t, drift=0.5)
        bh = (1150, 560, 150)
        starfield(c, t, center=bh, lens=1.0)
        black_hole(c, *bh, t)
        tt_ = t - 120.4
        prog = 1 - math.exp(-max(0, tt_) * 0.5)
        px, py = lerp(400, 1150 - 170, prog), lerp(260, 560 - 120, prog)
        red = clamp((t - 125.2) / 1.5)
        dim = clamp((t - 126.8) / 2.0)
        probe(c, px, py, lerp(0.9, 0.45, prog), t * (1 - prog), red, 1 - 0.65 * dim)
        for i, (lab, st, col) in enumerate((("FAST", 121.4, "#ffffff"), ("SLOWER", 122.6, "#ffd37a"),
                                            ("SLOWER", 123.7, "#ffb347"), ("RED", 125.2, "#ff4a2a"),
                                            ("DIM", 126.4, "#8a5050"), ("FROZEN", 129.5, "#bfe8ff"))):
            k = window(t, st, st + 1.2, 0.15) if lab != "FROZEN" else at(t, st, 0.2)
            if k:
                tag(c, 960, 120, lab, col, 40, a=k)
        return
    if t < 138.5:
        # explanation split: probe's view vs crew's view
        for side in (0, 1):
            c.save()
            clip_half(c, side, seed=8)
            if side == 0:
                space(c, t, bh=(520, 1080, 320), drift=(0, -400), streak=0.8)
                probe(c, 480, 420, 1.2, t * 3)
                stopwatch(c, 480, 780, 0.7, (t - 131) * 1.5, "#ff6a3a", "SECONDS")
            else:
                starfield(c, t)
                black_hole(c, 1450, 600, 160, t)
                probe(c, 1450 - 190, 470, 0.5, 0, 1.0, 0.35)
                tag(c, 1440, 940, "ITS LAST LIGHT, STRETCHED", "#bfe8ff", 32)
            c.restore()
        jagged_split(c, seed=8)
        tag(c, 480, 110, "FOR THE PROBE", "#ff6a3a", 36)
        tag(c, 1440, 110, "WHAT YOU SEE", "#bfe8ff", 36)
        kicker(c, t, 131.1, "DID IT STOP?", 540, 70, end=132.3)
        return
    cam(c, 1.2, 960, 560, t)
    draw_set(c, "bridge", 8)
    vignette(c, 0.45)
    figure(c, 900, 1080, "tomas", "stand", "wide", t, s=1.5, face=1, look=(1, -0.5),
           talk=1.0 if 140.2 < t < 141.5 else 0)
    if 138.5 < t < 140.0:
        for i in range(3):
            ph = ((t - 138.5) * 1.2 + i / 3) % 1
            text(c, "♪", 1100 + ph * 120, 520 - ph * 120, 60, "#ffffff", "Bold", a=1 - ph)
    bubble_line(c, 1300, 420, "OK, THAT'S CREEPY.", t, 140.2, 142.2, size=40)


# ---------------------------------------------------------------- 6. REAL HISTORY
def m87(c, x, y, r, t):
    glow(c, x, y, r * 2.2, "#ff7a1a", 0.35)
    for k in range(6):
        c.drawCircle(x, y, r, P("#ff9a3a", r * (0.5 - k * 0.06), 0.25))
    arc = skia.Path()
    arc.addArc(skia.Rect(x - r, y - r, x + r, y + r), 100, 160)
    c.drawPath(arc, P("#ffe08a", r * 0.35, 0.55))
    c.drawCircle(x, y, r * 0.62, P("#000000"))


def s_history(c, t):
    # 141.9 - 160.6
    info_board(c, t)
    k1, a1 = back_out(at(t, 142.3, 0.5)), at(t, 142.3, 0.3)
    with xf(c, 480, 460, k1, alpha=a1):
        m87(c, 0, 0, 170, t)
        text(c, "2019", 0, 280, 80, "#ffd37a", "Black")
        text(c, "FIRST IMAGE · M87*", 0, 330, 34, "#ffffff", "SemiBold")
        text(c, "ANOTHER GALAXY", 0, 372, 28, "#9fb3d0", "SemiBold")
    k2, a2 = back_out(at(t, 149.5, 0.5)), at(t, 149.5, 0.3)
    with xf(c, 1440, 460, k2, alpha=a2):
        m87(c, 0, 0, 150, t + 1)
        text(c, "2022", 0, 280, 80, "#ffd37a", "Black")
        text(c, "SAGITTARIUS A*", 0, 330, 34, "#ffffff", "SemiBold")
        text(c, "OUR OWN GALAXY", 0, 372, 28, "#9fb3d0", "SemiBold")
    k = window(t, 154.3, 158.1, 0.3)
    if k:
        tag(c, 1440, 120, "4 MILLION SUNS", "#ffb347", 44, a=k)
    if t > 158.0:
        c.drawRect(skia.Rect(0, 0, W, H), P("#000000", a=0.6 * at(t, 158.0, 0.4)))
        k = ease_out(at(t, 158.1, 0.6))
        c.drawCircle(300, 560, 70, P("#2f7bd6"))
        c.drawCircle(300, 560, 70, P("#7de08a", 10, 0.5))
        line(c, 400, 560, 400 + 1100 * k, 560, "#ffffff", 4, 0.6)
        if k > 0.9:
            black_hole(c, 1600, 560, 50, t, 0.6)
        text(c, "EARTH", 300, 680, 34, "#ffffff", "Black")
        tag(c, 960, 480, "CLOSEST KNOWN: ~1,500 LIGHT YEARS", "#5bd6ff", 40, a=k)


# ---------------------------------------------------------------- 7. LENA: the quiet monster
def s_lena(c, t):
    # 160.6 - 180.3
    if t < 167.5:
        cam(c, push(t, 160.6, 167.5, 1.1, 1.25), 960, 560, t)
        draw_set(c, "bridge", 8)
        vignette(c, 0.45)
        figure(c, 1100, 1080, "lena", "stand", "neutral", t, s=1.5, face=-1, look=(-1, -0.4),
               talk=1.0 if 163.0 < t < 167.0 else 0)
        lower_third(c, t, 162.7, "COMMANDER LENA", "Mission lead", "#e8c25a", dur=4.0)
        if t > 165.3:
            tag(c, 1100, 220, "THE QUIETEST MONSTER IN THE UNIVERSE", "#e8c25a", 34, a=at(t, 165.3, 0.3))
        return
    z = push(t, 167.5, 180.3, 1.0, 1.3)
    cam(c, z, 960, 560, t, drift=0.5)
    space(c, t, bh=(960, 560, 200), drift=(-3, 0))
    for i, (lab, st) in enumerate((("IT DOESN'T ROAR.", 167.5), ("IT DOESN'T CHASE.", 169.2), ("IT JUST WAITS.", 170.6))):
        k = window(t, st, 171.8 if i < 2 else 171.8, 0.25)
        if k:
            text(c, lab, 960, 180 + i * 70, 48 if i < 2 else 60, "#ffffff" if i < 2 else "#ffb347", "Black", a=k)
    if t > 171.8:
        for i in range(6):
            ph = clamp((t - 171.8 - i * 0.6) / 4.0)
            ang = i * 1.1
            r0 = lerp(700, 230, ease_out(ph))
            x = 960 + math.cos(ang + ph * 2) * r0
            y = 560 + math.sin(ang + ph * 2) * r0 * 0.6
            rrect(c, x - 14, y - 10, 28, 20, 4, mixhex("#9aa3b3", "#ff4a2a", ph), a=1 - 0.5 * ph)
        kicker(c, t, 171.9, "ANYTHING THAT DRIFTS TOO CLOSE... STAYS", 900, 46)
        kicker(c, t, 176.8, "NOBODY HAS EVER COME BACK TO SAY", 980, 36, "#9fb3d0")


# ---------------------------------------------------------------- 8. BODY LIES
def s_body_lies(c, t):
    # 180.3 - 209.3
    if t < 193.0:
        info_board(c, t, "#0d1624", "#06090f")
        kicker(c, t, 180.5, "HERE'S THE STRANGE PART", 150, 56, "#ffb347")
        y = 640 + 20 * math.sin(t * 1.2)
        figure(c, 600, y, "kai", "float2", "neutral", t, s=1.1, space=True, rot=8 * math.sin(t * 0.7))
        items = (("STOMACH DROP", 186.8), ("WIND", 187.9), ("ALARM", 188.9))
        for i, (lab, st) in enumerate(items):
            k, a = back_out(at(t, st, 0.35)), at(t, st, 0.25)
            with xf(c, 1300, 420 + i * 150, k, alpha=a):
                rrect(c, -260, -55, 520, 110, 20, "#16233a")
                text(c, lab, -30, 16, 44, "#ffffff", "Black")
                c.drawCircle(200, 0, 34, P("#ff4a4a"))
                cross_mark(c, 200, 0, 34, "#ffffff")
        k = window(t, 190.2, 193.2, 0.3)
        if k:
            tag(c, 960, 960, "NO SENSE FOR THIS DANGER", "#ff6a3a", 36, a=k)
        return
    if t < 202.7:
        info_board(c, t, "#1a0d0d", "#0a0505")
        st = 0.1 + 0.4 * smooth((t - 193.1) / 5)
        figure(c, 700, 520, "kai", "fall", "worried", t, s=0.85, space=True, stretch=st, rot=0)
        kicker(c, t, 193.1, "THE ONLY WARNING: THE STRETCH ITSELF", 150, 50)
        k = window(t, 195.6, 198.9, 0.3)
        if k:
            tag(c, 1350, 560, "BY THEN, IT'S ALREADY STRONG", "#ff4a2a", 36, a=k)
        if t > 198.9:
            mug(c, 1400, 600 + 20 * math.sin(t * 1.5), 2.6, t, face=True, rot=8 * math.sin(t))
            for i, lab in enumerate(("CALM", "HAPPY", "CLUELESS")):
                k = at(t, 199.6 + i * 0.7, 0.25)
                tag(c, 1400, 260 + i * 0 - 0, lab, ["#5bd6ff", "#7de08a", "#ffd37a"][i], 40,
                    a=k * (1 if i == 2 or t < 199.6 + (i + 1) * 0.7 else 0))
        return
    cam(c, 1.15, 960, 560, t)
    draw_set(c, "lab", 8)
    vignette(c, 0.45)
    figure(c, 760, 1080, "yuki", "stand", "focus", t, s=1.45, face=1, look=(1, 0),
           talk=1.0 if 204.4 < t < 206.4 else 0)
    if t < 206.9:
        bubble_line(c, 1150, 380, "OUT HERE, YOUR BODY LIES TO YOU.", t, 204.4, 206.9, size=36)
    figure(c, 1400, 1080, "kai", "fingerguns" if t > 206.9 else "stand", "happy" if t > 206.9 else "neutral", t,
           s=1.45, face=-1, look=(-1, 0))
    if t > 208.1:
        tag(c, 960, 200, "...", "#ffffff", 60, a=at(t, 208.1, 0.3))


# ---------------------------------------------------------------- 9. MIRA
def s_mira(c, t):
    # 209.3 - 243.6
    if t < 211.6:
        info_board(c, t)
        kicker(c, t, 209.4, "HOW DO YOU RUN FROM SOMETHING", 470, 60)
        kicker(c, t, 210.3, "YOU CAN'T FEEL?", 570, 70, "#ffb347")
        return
    if t < 222.7:
        cam(c, push(t, 211.6, 222.7, 1.1, 1.2), 900, 580, t)
        draw_set(c, "mira", 8)
        vignette(c, 0.45)
        calling = int(t * 1.6) % 2 == 0
        figure(c, 820, 1080, "mira", "phone", "sad" if t > 219 else "neutral", t, s=1.6, face=1, look=(0.5, 0),
               hold=lambda c_, x, y: phone(c_, x + 24, y, 1.0, 10, "#4a6aa8", glow_a=0.35 if calling else 0.1))
        lower_third(c, t, 212.4, "MIRA", "Kai's little sister · Earth", "#f2c14e", dur=3.2)
        if t > 215.8:
            k = at(t, 215.8, 0.3)
            n = min(9, 1 + int((t - 216.0) / 0.3)) if t > 216 else 1
            with xf(c, 1420, 420, back_out(k), alpha=k):
                rrect(c, -200, -110, 400, 220, 30, "#16233a")
                text(c, "MISSED CALLS", 0, -40, 34, "#9fb3d0", "Black")
                text(c, f"{n}", 0, 80, 130, "#ff4a4a", "Black")
        if t > 220.8:
            tag(c, 1420, 720, "BUSY. ALWAYS BUSY.", "#ffffff", 34, a=at(t, 220.8, 0.3))
        return
    if t < 234.0:
        cam(c, push(t, 222.7, 234, 1.1, 1.25), 960, 560, t)
        draw_set(c, "quarters", 8)
        vignette(c, 0.5)
        figure(c, 700, 1080, "kai", "phone", "worried" if t > 231.3 else "neutral", t, s=1.5, face=1, look=(1, 0.3),
               hold=lambda c_, x, y: phone(c_, x + 24, y, 1.0, 10, "#2b3a55", glow_a=0.3))
        k, a = back_out(at(t, 222.8, 0.4)), at(t, 222.8, 0.3)
        with xf(c, 1340, 440, k, alpha=a):
            rrect(c, -330, -120, 660, 240, 30, "#16233a")
            c.drawCircle(-230, 0, 60, P("#f2c14e"))
            c.drawPath(poly([(-250, -30), (-250, 30), (-195, 0)]), P("#16233a"))
            for i in range(14):
                hgt = 20 + 50 * abs(math.sin(i * 1.7))
                rrect(c, -140 + i * 22, -hgt / 2, 12, hgt, 6, "#9fb3d0")
            text(c, "MIRA · VOICE MESSAGE", 40, -70, 26, "#9fb3d0", "Black")
            text(c, "\"FOR THE WAY HOME\"", 40, 90, 36, "#f2c14e", "Black")
        if t > 225.0:
            tag(c, 1340, 720, "UNOPENED", "#ff4a4a", 36, a=at(t, 225.4, 0.3))
        if t > 231.3:
            tag(c, 700, 260, "SCARED SHE'S ANGRY", "#ffffff", 34, a=at(t, 231.3, 0.3))
        return
    cam(c, 1.15, 960, 560, t)
    draw_set(c, "bridge", 8)
    vignette(c, 0.45)
    singing = 234.0 < t < 238.5
    figure(c, 720, 1080 + (6 * math.sin(t * 10) if singing else 0), "tomas", "sing" if singing else "stand",
           "laugh" if singing else "smile", t, s=1.45, face=1, talk=1.0 if singing else 0)
    figure(c, 1300, 1080, "kai", "headhold" if singing else "stand", "bored" if singing else "smile", t, s=1.45,
           face=-1, look=(-1, 0))
    if singing:
        for i in range(5):
            ph = ((t - 234) * 0.8 + i / 5) % 1
            text(c, "♪" if i % 2 else "♫", 880 + ph * 220 + 40 * math.sin(i), 560 - ph * 260, 56,
                 "#ff8a8a" if i % 2 else "#ffd37a", "Bold", a=1 - ph)
        tag(c, 760, 230, "BADLY. VERY BADLY.", "#ffd37a", 34, a=at(t, 236.1, 0.3))
    if t > 238.5:
        tag(c, 1300, 230, "PLAY IT ON THE TRIP HOME", "#f2c14e", 34, a=at(t, 238.5, 0.3))


def s_question(c, t):
    # 243.6 - 245.6
    info_board(c, t, "#0b0f18", "#05070b")
    kicker(c, t, 243.7, "HAVE YOU EVER SAVED SOMETHING", 470, 62)
    kicker(c, t, 244.3, "FOR LATER?", 570, 80, "#f2c14e")


# ---------------------------------------------------------------- 10. SPACEWALK
def s_spacewalk(c, t):
    # 245.6 - 266.6
    if t < 257.0:
        z = push(t, 245.6, 255.0, 1.0, 1.15)
        sh = 1.0 if 253.2 < t < 254.0 else 0.0
        cam(c, z, 960, 560, t, shake=sh, drift=0.6)
        space(c, t, bh=(1650, 900, 170), drift=(-4, 0), lens=0.3)
        # hull
        rrect(c, -200, 760, 1600, 400, 40, OUT)
        rrect(c, -196, 764, 1592, 392, 38, "#9aa3b3")
        for i in range(8):
            c.drawRect(skia.Rect(i * 200, 764, i * 200 + 6, 1160), P("#7a8494"))
        line(c, 980, 770, 1040, 560, "#c9ced8", 10)
        c.drawCircle(1040, 560, 22, P("#ff4a4a" if int(t * 2) % 2 else "#802020"))
        snapped = t > 254.2
        kx, ky = 760, 700
        tx, ty = 1180, 680
        if snapped:
            dt = t - 254.2
            tx, ty = tx + dt * 40, ty - dt * 25
        tether(c, 300, 780, kx - 60, ky - 120, 40)
        if not snapped:
            tether(c, 300, 780, tx, ty - 120, 80)
        else:
            tether(c, 1180 - 120, 600, tx - 40, ty - 120, 30, a=0.9)
        figure(c, kx, ky, "kai", "reach", "focus" if not snapped else "wide", t, s=0.9, space=True, face=1,
               look=(1, 0))
        figure(c, tx, ty, "tomas", "reach", "smile" if not snapped else "scared", t, s=0.9, space=True, face=-1,
               look=(-1, 0), rot=(t - 254.2) * 6 if snapped else 0)
        k = window(t, 248.4, 250.6, 0.25)
        if k:
            tag(c, 1040, 470, "LOOSE ANTENNA · ROUTINE", "#5bd6ff", 30, a=k)
        if 253.2 < t < 255.0:
            k = back_out(at(t, 254.0, 0.2))
            with xf(c, 1080, 520, k, rot=-8):
                text(c, "SNAP!", 0, 0, 120, "#ff4a4a", "Black", shadow=True)
        if t > 255.6:
            tag(c, 960, 140, "HIS TETHER BREAKS", "#ff4a4a", 40, a=at(t, 255.6, 0.3))
        return
    # Tomas drifts toward the hole
    z = push(t, 257.0, 266.6, 1.0, 1.1)
    cam(c, z, 960, 560, t, drift=0.5)
    space(c, t, bh=(1500, 760, 220), drift=(-3, 0), lens=0.5)
    p = smooth((t - 257) / 10)
    figure(c, lerp(520, 980, p), lerp(420, 560, p), "tomas", "float", "worried", t, s=0.75, space=True, face=1,
           rot=(t - 257) * 8, look=(1, 0.3))
    if t > 261.4:
        tag(c, 960, 140, "HE DOESN'T FEEL LIKE HE'S FALLING", "#ffffff", 34, a=window(t, 261.4, 266.7, 0.3))
    if t > 263.5:
        mug(c, 300, 820 + 10 * math.sin(t * 1.5), 1.2, t, face=True, steam=False, rot=10 * math.sin(t))


def comms(c, x, y, who, label, t, col):
    rrect(c, x - 260, y - 90, 520, 180, 24, "#0b1220")
    rrect(c, x - 260, y - 90, 520, 180, 24, col, stroke=4)
    head_only(c, x - 170, y, who, "focus", t, r=52, face=1, talk=1.0)
    for i in range(16):
        hgt = 10 + 50 * abs(math.sin(t * 9 + i * 1.3))
        rrect(c, x - 90 + i * 20, y - hgt / 2, 10, hgt, 5, col)
    text(c, label, x + 60, y - 56, 24, "#9fb3d0", "Black")


def s_status(c, t):
    # 266.6 - 284.6
    if t < 277.1:
        space(c, t, bh=(1500, 760, 220), drift=(-3, 0), lens=0.5)
        figure(c, 420, 640, "kai", "float", "wide", t, s=0.9, space=True, look=(1, 0))
        if t < 270.4:
            comms(c, 1240, 260, "lena", "COMMANDER LENA", t, "#e8c25a")
            tag(c, 1240, 420, "\"KAI, STATUS.\"", "#e8c25a", 40, a=at(t, 268.4, 0.25))
        else:
            comms(c, 1240, 260, "yuki", "DR. YUKI", t, "#9b7cf0")
            k = at(t, 272.7, 0.3)
            tag(c, 1240, 440, "DRIFTING TOWARD THE STRETCH ZONE", "#ff6a3a", 30, a=k)
            if t > 274.8:
                kicker(c, t, 274.8, "HOW LONG UNTIL HE'S PAST SAVING?", 920, 46)
        return
    info_board(c, t, "#140a0a", "#070404")
    k, a = back_out(at(t, 277.2, 0.35)), at(t, 277.2, 0.25)
    with xf(c, 520, 420, k, alpha=a):
        text(c, "MINUTES.", 0, 0, 110, "#ff4a4a", "Black", shadow=True)
    if t > 279.0:
        # jetpack fuel gauge
        with xf(c, 1300, 560):
            rrect(c, -160, -300, 320, 600, 40, OUT)
            rrect(c, -150, -290, 300, 580, 36, "#1a2232")
            lvl = 0.22
            rrect(c, -130, 270 - 540 * lvl, 260, 540 * lvl, 26, "#ffb347")
            for i in range(5):
                line(c, -150, 270 - i * 135, -110, 270 - i * 135, "#5a6478", 4)
            text(c, "JETPACK FUEL", 0, -330, 34, "#ffffff", "Black")
        tag(c, 520, 620, "FUEL FOR ONE HARD PUSH", "#ffb347", 36, a=at(t, 281.1, 0.3))
        if t > 283.6:
            k = back_out(at(t, 283.6, 0.3))
            with xf(c, 520, 800, k):
                text(c, "ONE.", 0, 0, 120, "#ffffff", "Black", shadow=True)


def s_rescue(c, t):
    # 284.6 - 297.3
    if t < 287.6:
        cam(c, 1.0, 960, 560, t, drift=0.5)
        space(c, t, bh=(1600, 820, 200), drift=(-60, 0), lens=0.4)
        p = smooth((t - 284.8) / 2.4)
        kx = lerp(300, 980, p)
        figure(c, kx, 560, "kai", "reach", "focus", t, s=0.85, space=True, face=1, rot=70 * (1 - p) + 10, look=(1, 0))
        for i in range(8):
            c.drawCircle(kx - 120 - i * 26, 640 + 8 * math.sin(i + t * 20), 16 - i * 1.5,
                         P("#ffd37a", a=0.7 - i * 0.08))
        figure(c, 1240, 520, "tomas", "float", "scared", t, s=0.85, space=True, face=-1, rot=-20)
        if t > 286.2:
            tag(c, 960, 140, "YOU GRAB HIS BOOT", "#ffffff", 36, a=at(t, 286.2, 0.3))
        return
    info_board(c, t)
    kicker(c, t, 287.6, "EVERY PUSH IN SPACE WORKS BOTH WAYS", 160, 52)
    k = ease_out(at(t, 291.3, 0.8))
    ax = lerp(860, 520, k)
    bx = lerp(1060, 1400, k)
    figure(c, ax, 700, "kai", "push", "focus", t, s=0.8, space=True, face=1)
    figure(c, bx, 700, "tomas", "float", "worried", t, s=0.8, space=True, face=-1)
    if k > 0.1:
        arrow(c, 960, 520, 960 + 300 * k, 520, "#5bd6ff", 20, a=k)
        arrow(c, 960, 520, 960 - 300 * k, 520, "#ff6a3a", 20, a=k)
    if t > 294.9:
        tag(c, 960, 960, "EQUAL · OPPOSITE", "#ffffff", 44, a=at(t, 294.9, 0.3))


def s_choice(c, t):
    # 297.3 - 310.6
    pick = 0
    for side in (0, 1):
        c.save()
        clip_half(c, side, seed=21)
        if side == 0:
            space(c, t, bh=(820, 960, 160), drift=(-4, 0), lens=0.3)
            ship(c, 260, 300, 0.4, t)
            figure(c, 480, 640, "kai", "float", "sad", t, s=0.7, space=True, face=-1)
            figure(c, 760, 760, "tomas", "float", "scared", t, s=0.55, space=True, rot=t * 20, alpha=0.8)
            tint(c, "#ff4a2a", 0.08)
        else:
            space(c, t, bh=(1860, 960, 160), drift=(-4, 0), lens=0.3)
            ship(c, 1300, 300, 0.4, t)
            figure(c, 1420, 520, "tomas", "float", "wide", t, s=0.55, space=True, face=-1)
            figure(c, 1640, 760, "kai", "fall", "smile", t, s=0.7, space=True, rot=-30)
            tint(c, "#5bd6ff", 0.06)
        c.restore()
    jagged_split(c, seed=21)
    tag(c, 480, 110, "KEEP THE FUEL", "#ff6a3a", 38, a=at(t, 302.0, 0.3))
    text(c, "FLY HOME ALONE", 480, 190, 30, "#ffffff", "Black", a=at(t, 302.4, 0.3))
    tag(c, 1440, 110, "SPEND IT", "#5bd6ff", 38, a=at(t, 304.5, 0.3))
    text(c, "THROW TOMAS TO SAFETY", 1440, 190, 30, "#ffffff", "Black", a=at(t, 305.0, 0.3))
    if t > 308.2:
        k = back_out(at(t, 308.2, 0.35))
        with xf(c, 960, 560, k):
            rrect(c, -330, -80, 660, 160, 30, "#0b1018")
            text(c, "TWO CHOICES. ONE PUSH.", 0, 18, 50, "#ffffff", "Black")


def s_push(c, t):
    # 310.6 - 323.4
    if t < 317.0:
        cam(c, push(t, 310.6, 317, 1.15, 1.3), 960, 560, t)
        space(c, t, bh=(1700, 900, 180), drift=(-3, 0), lens=0.3)
        figure(c, 640, 620, "tomas", "float", "angry" if t < 314 else "worried", t, s=1.0, space=True, face=1,
               look=(1, 0), talk=1.0 if 312.2 < t < 313.5 else 0)
        figure(c, 1260, 620, "kai", "float", "smile", t, s=1.0, space=True, face=-1, look=(-1, 0),
               talk=1.0 if 315.1 < t < 316.5 else 0)
        bubble_line(c, 560, 220, "DON'T YOU DARE.", t, 312.2, 314.0, size=40)
        bubble_line(c, 1300, 220, "SINCE WHEN DO I LISTEN TO YOU?", t, 315.1, 317.1, size=34)
        return
    dt = t - 317.0
    cam(c, 1.0, 960, 560, t, shake=1.0 if dt < 0.5 else 0.0, drift=0.5)
    space(c, t, bh=(1700, 900, 200), drift=(-3, 0), lens=0.3)
    ship(c, 240, 260, 0.5, t)
    tx = 760 - 520 * ease_out(dt / 3.0)
    ty = 560 - 260 * ease_out(dt / 3.0)
    kx = 1000 + 220 * ease_out(dt / 4.0)
    ky = 600 + 160 * ease_out(dt / 4.0)
    if dt < 0.6:
        glow(c, 880, 580, 300, "#ffffff", 0.6 * (1 - dt / 0.6))
    if t < 321.0:
        figure(c, tx, ty, "tomas", "float", "wide", t, s=0.8 * (1 - 0.3 * clamp(dt / 3)), space=True, face=-1,
               rot=-dt * 30)
    figure(c, kx, ky, "kai", "push", "smile", t, s=0.85, space=True, face=-1, rot=dt * 10)
    if t > 320.7:
        tag(c, 380, 420, "LENA PULLS HIM INSIDE", "#e8c25a", 30, a=at(t, 320.7, 0.3))
    if t > 322.4:
        k = back_out(at(t, 322.4, 0.3))
        with xf(c, 380, 520, k):
            text(c, "SAFE.", 0, 0, 90, "#7de08a", "Black", shadow=True)


# ---------------------------------------------------------------- 11. LAST MESSAGE
def s_fall_message(c, t):
    # 323.4 - 352.9
    sp = 0.3 if t < 326.6 else 1.0
    cam(c, push(t, 323.4, 352.9, 1.0, 1.15), 960, 560, t, drift=0.6)
    space(c, t, bh=(960, 1350, 520), drift=(0, -60 - 300 * sp * clamp((t - 326.6) / 2)), streak=0.4 * sp)
    if t < 328.2:
        figure(c, 960, 460, "kai", "fall", "neutral", t, s=1.0, space=True, rot=0)
        if t > 326.6:
            tag(c, 960, 120, "THEN NOT SLOWLY", "#ff6a3a", 36, a=at(t, 326.6, 0.3))
        return
    # close up in helmet
    head_only(c, 760, 560, "kai", "sad" if t < 337.7 else ("smile" if t < 347.5 else "happy"), t, r=210,
              look=(0.2, 0.2), helmet=True, talk=1.0 if 344.3 < t < 349.0 else 0)
    if t < 332.4:
        kicker(c, t, 328.2, "\"FOR THE WAY HOME\"", 170, 54, "#f2c14e")
        k = window(t, 329.9, 332.6, 0.3)
        if k:
            text(c, "NEVER THE WAY HOME YOU PLANNED", 960, 250, 40, "#ffffff", "Black", a=k, shadow=True)
        return
    # Mira's message playing as a hologram
    k = ease_out(at(t, 332.5, 0.6))
    with xf(c, 1360, 520, alpha=k):
        glow(c, 0, 0, 380, "#f2c14e", 0.25)
        rrect(c, -280, -300, 560, 600, 40, "#f2c14e", 0.08)
        rrect(c, -280, -300, 560, 600, 40, "#f2c14e", stroke=3)
        if t < 344.3:
            figure(c, 0, 230, "mira", "stand", "smile" if t > 337.7 else "neutral", t, s=0.95,
                   talk=1.0 if 336.0 < t < 342.0 else 0, rim="#f2c14e")
            for i in range(18):
                hgt = 8 + 30 * abs(math.sin(t * 8 + i))
                rrect(c, -200 + i * 22, 260 - hgt / 2, 10, hgt, 5, "#f2c14e", 0.8)
        else:
            text(c, "RECORDING", 0, -220, 36, "#ff4a4a", "Black")
            c.drawCircle(-160, -232, 12, P("#ff4a4a", a=0.5 + 0.5 * math.sin(t * 6)))
    msgs = (("SHE ISN'T ANGRY.", 337.7, 340.4), ("SHE JUST MISSES YOU.", 338.6, 340.4),
            ("ONE CALL. JUST ONE.", 340.5, 344.2))
    for lab, st, en in msgs:
        k = window(t, st, en, 0.2)
        if k:
            text(c, lab, 760, 150 + (60 if lab.startswith("SHE JUST") else 0), 44, "#ffffff", "Black", a=k, shadow=True)
    lines_ = (("I'M SORRY.", 344.3), ("YOU WERE RIGHT.", 345.9), ("I LOVE YOU.", 347.5))
    for i, (lab, st) in enumerate(lines_):
        if 344.3 < t < 349.0:
            text(c, lab, 1360, -60 + 520 - 80 + i * 90, 48, "#f2c14e", "Black", a=at(t, st, 0.3))
    if t > 349.0:
        p = clamp((t - 349.2) / 2.5)
        for i in range(3):
            c.drawCircle(1360 + p * 400, 520 - p * 380, 30 + i * 30 + p * 40, P("#5bd6ff", 4, (1 - p) * (0.8 - i * 0.2)))
        tag(c, 1360, 880, "SENT TO THE SHIP", "#5bd6ff", 36, a=at(t, 349.0, 0.3))
        if t > 351.1:
            tag(c, 1360, 960, "TOMAS WILL CARRY IT HOME", "#7de08a", 30, a=at(t, 351.1, 0.3))


def s_finale(c, t):
    # 352.9 - 370.0 : the hook, replayed with meaning
    if t < 357.4:
        st = 0.1 + 0.6 * smooth((t - 353) / 4)
        cam(c, 1.2, 960, 540, t, shake=0.35)
        space(c, t, bh=(960, 1300, 420), drift=(0, -380), streak=1.0)
        figure(c, 960, 360, "kai", "fall", "closed", t, s=1.0, space=True, stretch=st, rot=0)
        return
    if t < 365.4:
        cam(c, 1.05, 960, 540, t)
        draw_set(c, "bridge", 8)
        c.save()
        c.clipRRect(skia.RRect.MakeRectXY(skia.Rect(380, 140, 1540, 660), 30, 30), skia.ClipOp.kIntersect, True)
        starfield(c, t, (380, 140, 1540, 660))
        black_hole(c, 1180, 470, 110, t)
        prog = 1 - math.exp(-(t - 357.0) * 0.5)
        red = clamp((t - 360.6) / 0.8)
        figure(c, lerp(760, 1040, prog), lerp(320, 440, prog), "kai", "fall", "closed", t, s=0.16, space=True,
               rot=-35, red=red, alpha=1 - 0.6 * clamp((t - 361.6) / 1.2))
        c.restore()
        vignette(c, 0.5)
        for who, x, face in (("tomas", 560, 1), ("yuki", 960, 1), ("lena", 1360, -1)):
            figure(c, x, 1140, who, "stand", "sad", t, s=1.35, face=face, look=(0.3, -1), rim_off=(-9, -8))
        for lab, st, en, col in (("SLOW", 357.6, 360.5, "#ffb347"), ("RED", 360.6, 361.5, "#ff4a2a"),
                                 ("FADE", 361.6, 362.3, "#8a5050"), ("FROZEN AT THE EDGE", 362.4, 365.4, "#bfe8ff")):
            k = window(t, st, en, 0.15)
            if k:
                tag(c, 960, 90, lab, col, 34, a=k)
        return
    for side in (0, 1):
        c.save()
        clip_half(c, side, seed=3)
        if side == 0:
            space(c, t, bh=(560, 1150, 360), drift=(0, -300), streak=0.8)
            figure(c, 480, 380, "kai", "fall", "closed", t, s=0.8, space=True, stretch=0.5, rot=0)
            stopwatch(c, 480, 820, 0.85, (t - 365.4) * 1.2, "#ff6a3a", "SECONDS")
        else:
            draw_set(c, "bridge", 8)
            tint(c, "#000000", 0.4)
            figure(c, 1300, 1050, "tomas", "stand", "sad", t, s=1.1, face=-1, look=(-0.4, -1))
            stopwatch(c, 1440, 330, 0.85, 0.08, "#bfe8ff", "FOREVER", frozen=True)
        c.restore()
    jagged_split(c, seed=3)
    fade = clamp((t - 368.8) / 1.2)
    tint(c, "#000000", fade)


# ---------------------------------------------------------------- 12. FACT CHECK + OUTRO
def s_facts(c, t):
    # 370.0 - 409.0
    info_board(c, t)
    if t < 384.2:
        kicker(c, t, 370.1, "SO HOW REAL IS ALL THIS?", 160, 64, "#ffb347")
        rows = (("SPAGHETTIFICATION", "REAL. SCIENTISTS REALLY CALL IT THAT.", 372.4),
                ("THE FREEZE AT THE EDGE", "REAL. FAR AWAY, A FALLER SLOWS, REDDENS, FADES.", 376.3))
        for i, (h, sub, st) in enumerate(rows):
            k, a = back_out(at(t, st, 0.4)), at(t, st, 0.3)
            with xf(c, 960, 400 + i * 230, k, alpha=a):
                rrect(c, -700, -90, 1400, 180, 26, "#13213a")
                c.drawCircle(-600, 0, 50, P("#2ecc71"))
                check_mark(c, -600, 0, 60, "#ffffff", prog=at(t, st + 0.2, 0.4))
                text(c, h, -520, -10, 52, "#ffffff", "Black", align="left")
                text(c, sub, -520, 50, 30, "#9fb3d0", "SemiBold", align="left")
        return
    if t < 393.7:
        kicker(c, t, 384.2, "SURVIVING IT NEAR A SMALL BLACK HOLE?", 220, 54)
        k, a = back_out(at(t, 387.1, 0.35)), at(t, 387.1, 0.25)
        with xf(c, 960, 470, k, alpha=a, rot=-4):
            rrect(c, -380, -100, 760, 200, 30, "#ff4a4a", stroke=12)
            text(c, "IMPOSSIBLE", 0, 40, 120, "#ff4a4a", "Black")
        if t > 388.4:
            tag(c, 960, 760, "THE STRETCH WINS LONG BEFORE THE EDGE", "#ffb347", 36, a=at(t, 388.4, 0.3))
        return
    if t < 409.1:
        kicker(c, t, 390.8, "WHAT'S INSIDE?", 160, 64, "#ffb347")
        black_hole(c, 330, 600, 100, t, 0.7)
        text(c, "?", 330, 640, 110, "#ffffff", "Black", a=0.6 + 0.4 * math.sin(t * 3))
        items = (("EINSTEIN'S THEORY BREAKS DOWN AT THE CENTER", 393.7),
                 ("WHAT HAPPENS TO INFORMATION? STILL DEBATED", 395.8),
                 ("HAWKING CHANGED HIS MIND ABOUT IT", 400.6),
                 ("MANY PHYSICISTS AGREE. NOBODY HAS PROVEN IT.", 405.8))
        for i, (lab, st) in enumerate(items):
            k, a = ease_out(at(t, st, 0.4)), at(t, st, 0.3)
            with xf(c, 760 + (1 - k) * 40, 380 + i * 140, alpha=a):
                rrect(c, 0, -50, 1060, 100, 20, "#13213a")
                text(c, lab, 40, 14, 34, "#ffffff", "Black", align="left")
        return


def s_outro(c, t):
    # 409.0 - end
    if t < 416.4:
        space(c, t, bh=(960, 600, 300), drift=(-3, 0))
        tint(c, "#000000", 0.3)
        kicker(c, t, 409.2, "AND HERE'S A TWIST...", 150, 60, "#ffb347")
        kicker(c, t, 410.7, "WHAT IF IT WAS A GIANT ONE", 930, 56)
        kicker(c, t, 413.1, "...AND YOU DIDN'T GET STRETCHED AT ALL?", 1010, 44, "#5bd6ff")
        return
    info_board(c, t, "#0b0f18", "#05070b")
    kicker(c, t, 416.4, "TELL US IN THE COMMENTS", 260, 60)
    kicker(c, t, 417.5, "WHICH SPACE MYSTERY SHOULD WE DO NEXT?", 350, 40, "#9fb3d0")
    for i, lab in enumerate(("WHITE HOLES?", "NEUTRON STARS?", "WORMHOLES?")):
        k, a = back_out(at(t, 418.0 + i * 0.35, 0.35)), at(t, 418.0 + i * 0.35, 0.25)
        with xf(c, 560 + i * 400, 560, k, alpha=a):
            rrect(c, -170, -60, 340, 120, 24, "#13213a")
            text(c, lab, 0, 14, 34, "#ffffff", "Black")
    k, a = back_out(at(t, 420.5, 0.35)), at(t, 420.5, 0.25)
    subbed = t > 421.6
    with xf(c, 680, 820, k, alpha=a):
        rrect(c, -180, -60, 360, 120, 60, "#2a3346")
        text(c, "LIKE", 0, 20, 50, "#ffffff", "Black")
    with xf(c, 1180, 820, k, alpha=a):
        rrect(c, -240, -60, 480, 120, 60, "#2a3346" if subbed else "#ff1e1e")
        text(c, "SUBSCRIBED" if subbed else "SUBSCRIBE", 0, 20, 48, "#ffffff", "Black")


SCENES = [
    (0.0, 3.8, s_hook_fall), (3.8, 7.4, s_hook_boots), (7.4, 13.0, s_hook_stretch), (13.0, 19.1, s_hook_crew),
    (19.1, 23.6, s_hook_split), (23.6, 26.7, s_rewind), (26.7, 30.6, s_meet_kai), (30.6, 34.4, s_closest),
    (34.4, 50.2, s_tidal), (50.2, 58.2, s_horizon), (58.2, 60.8, s_title), (60.8, 69.3, s_window),
    (69.3, 79.4, s_scale), (79.4, 87.1, s_yuki), (87.1, 99.5, s_danger_map), (99.5, 110.7, s_rope),
    (110.7, 117.4, s_coffee), (117.4, 141.9, s_probe), (141.9, 160.6, s_history), (160.6, 180.3, s_lena),
    (180.3, 209.3, s_body_lies), (209.3, 243.6, s_mira), (243.6, 245.6, s_question), (245.6, 266.6, s_spacewalk),
    (266.6, 284.6, s_status), (284.6, 297.3, s_rescue), (297.3, 310.6, s_choice), (310.6, 323.4, s_push),
    (323.4, 352.9, s_fall_message), (352.9, 370.0, s_finale), (370.0, 409.0, s_facts), (409.0, 1e9, s_outro),
]
INNER_CUTS = [39.2, 62.3, 74.9, 107.4, 113.3, 120.1, 131.1, 138.5, 158.0, 167.5, 193.0, 202.7, 211.6, 222.7,
              234.0, 257.0, 277.1, 287.6, 317.0, 328.2, 357.4, 365.4, 384.2, 393.7, 416.4]
CUTS = [s for s, _, _ in SCENES[1:]] + INNER_CUTS


# ---------------------------------------------------------------- captions (SRT + optional burn-in)
FIX = {"Thomas": "Tomas", "Your Kai": "You're Kai"}


def load_words():
    segs = json.load(open(os.path.join(HERE, "transcript.json")))
    words = []
    for s in segs:
        for w in s["words"]:
            words.append(dict(w=w["w"].strip(), s=w["s"], e=w["e"]))
    for i, w in enumerate(words):
        if w["w"].startswith("Thomas"):
            w["w"] = w["w"].replace("Thomas", "Tomas")
        if w["w"] == "Your" and i + 1 < len(words) and words[i + 1]["w"].startswith("Kai"):
            w["w"] = "You're"
    return words


def caption_chunks():
    words = load_words()
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 7 or (len(cur) >= 3 and w["w"][-1:] in ".,?!") or w["w"][-1:] in ".?!":
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    out = []
    for i, ch in enumerate(chunks):
        st, en = ch[0]["s"], ch[-1]["e"] + 0.35
        if i + 1 < len(chunks):
            en = min(en, chunks[i + 1][0]["s"] - 0.02)
        out.append((st, en, " ".join(w["w"] for w in ch)))
    return out


def write_srt(path):
    def ts(x):
        h, m = int(x // 3600), int(x % 3600 // 60)
        s = x % 60
        return f"{h:02d}:{m:02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    with open(path, "w") as f:
        for i, (st, en, tx) in enumerate(caption_chunks(), 1):
            f.write(f"{i}\n{ts(st)} --> {ts(en)}\n{tx}\n\n")


_CHUNKS = None


def burn_captions(c, t):
    global _CHUNKS
    if _CHUNKS is None:
        _CHUNKS = caption_chunks()
    for st, en, tx in _CHUNKS:
        if st <= t < en:
            w = text_width(tx, 44, "Bold") + 50
            rrect(c, W / 2 - w / 2, H - 120, w, 70, 14, "#000000", 0.55)
            text(c, tx, W / 2, H - 72, 44, "#ffffff", "Bold")
            return


# ---------------------------------------------------------------- frame
def render_frame(c, t):
    c.clear(C("#000000"))
    for start, end, fn in SCENES:
        if start <= t < end:
            c.save()
            fn(c, t)
            c.restoreToCount(1)
            break
    vignette(c, 0.35)
    grain(c, t, 0.05)
    dip = 0.0
    for ct in CUTS:
        d = abs(t - ct)
        if d < 0.14:
            dip = max(dip, 1 - d / 0.14)
    if t < 0.5:
        dip = max(dip, 1 - t / 0.5)
    if dip:
        tint(c, "#000000", dip * 0.85)
    if BURN_CAPTIONS:
        burn_captions(c, t)
