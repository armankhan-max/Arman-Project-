"""Scene timeline for the voiceover. All times are absolute seconds in the audio."""
import json
import math
import os

import skia

from gfx import *  # noqa: F401,F403

HERE = os.path.dirname(os.path.abspath(__file__))
ROAD = 820
CAR_Y = 822


# ---------------------------------------------------------------- helpers
def cam(c, zoom=1.0, cx=W / 2, cy=H / 2, dx=0.0, dy=0.0):
    c.translate(W / 2 + dx, H / 2 + dy)
    c.scale(zoom, zoom)
    c.translate(-cx, -cy)


def awning(c, t):
    c.drawRect(skia.Rect(0, 0, W, 300), P("#2f4a1c"))
    for i in range(0, 13):
        x = i * 160
        c.drawRect(skia.Rect(x, 0, x + 80, 300), P("#5b7d3a"))
        c.drawRect(skia.Rect(x + 80, 0, x + 160, 300), P("#eef2e2"))
        col = "#5b7d3a" if True else "#eef2e2"
        c.drawCircle(x + 40, 300, 40, P("#5b7d3a"))
        c.drawCircle(x + 120, 300, 40, P("#eef2e2"))
    c.drawRect(skia.Rect(0, 340, W, H), P("#000000", a=0.16))
    rrect(c, 60, 300, 24, 700, 10, "#6b6b6b")
    rrect(c, W - 84, 300, 24, 700, 10, "#6b6b6b")


def car_shadow(c, x, y, s=1.0, a=0.28):
    c.drawPath(poly([(x - 280 * s, y + 10), (x + 260 * s, y + 10), (x + 40 * s, y + 120 * s),
                     (x - 640 * s, y + 120 * s)]), P("#3a1f10", a=a))


def headline(c, t, start, lines, y=330, size=96, color="#ffffff", accent=None, stagger=0.18):
    for i, ln in enumerate(lines):
        k = back_out(at(t, start + i * stagger, 0.5))
        col = accent if (accent and i == len(lines) - 1) else color
        with xf(c, W / 2, y + i * size * 1.15, s=0.6 + 0.4 * k, alpha=clamp(k)):
            text(c, ln, 0, size * 0.35, size, col, shadow=True)


def pop(t, start, dur=0.45):
    return back_out(at(t, start, dur)), clamp(at(t, start, dur * 0.6))


def counter(t, start, dur, a, b):
    return lerp(a, b, ease_out(at(t, start, dur)))


# ---------------------------------------------------------------- scenes
def s_open_wide(c, t):
    cam(c, 1.0 + 0.012 * t, 960, 620)
    scene_bg(c, "hot", t, scroll=0, shimmer=1.0)
    birds(c, t, 760, 230)
    car_shadow(c, 1100, CAR_Y)
    draw_vehicle(c, 1100, CAR_Y, 1.0, hood=1.0, t=t, smoke=0.25)
    # empty road arrow / emphasis at 2.6
    k = window(t, 2.8, 5.8)
    if k > 0:
        pill(c, 420, 470, "NO CARS. NO PEOPLE.", 40, "#1b1b2f", "#ffffff", a=k, s=0.9 + 0.1 * k)


def s_open_shade(c, t):
    lt = t - 6.0
    z = 1.0 + 0.01 * lt
    focus = lerp(1200, 900, smooth((t - 9.4) / 1.5))
    cam(c, 1.35 * z, focus, 700)
    scene_bg(c, "hot", t, shimmer=0.8)
    car_shadow(c, 1320, CAR_Y, 1.0, 0.33)
    draw_vehicle(c, 1320, CAR_Y, 1.0, hood=1.0, t=t)
    throb = 1.0 + (0.06 * abs(math.sin(t * 5)) if t > 8.0 else 0)
    # Noor asleep hugging the bottle
    draw_char(c, 830, 905, "noor", "hug", "sleep", t, s=1.0, htilt=-12, bob=2 * math.sin(t * 1.5))
    draw_bottle(c, 830, 865, 0.55, fill=0.55, rot=-10)
    gl = window(t, 12.3, 14.4, 0.25)
    if gl:
        sparkle(c, 845, 840, 30 * gl, "#ffffff", gl, rot=t * 60)
    for i in range(3):
        ph = (t * 0.4 + i / 3) % 1
        text(c, "z", 900 + ph * 60 + i * 6, 740 - ph * 90, 30 + ph * 20, "#ffffff", a=1 - ph)
    # You, exhausted
    draw_char(c, 1130, 905, "you", "head_hold" if t > 7.8 else "sit", "dry", t, s=1.0, sweat=1.0, htilt=6)
    if t > 7.8:
        for i in range(4):
            ang = math.radians(-150 + i * 40)
            r0 = 92 * throb
            hx, hy = 1130 + 5, 905 - 118 - 47
            line(c, hx + math.cos(ang) * r0, hy + math.sin(ang) * r0, hx + math.cos(ang) * (r0 + 22),
                 hy + math.sin(ang) * (r0 + 22), "#ff4d4d", 6, 0.8)


def s_zero_sips(c, t):
    cam(c, 1.0 + 0.01 * (t - 14.6), 960, 540)
    draw_sky(c, "hot", t)
    fill_shader(c, skia.Rect(0, 560, W, H), linear(0, 560, 0, H, ["#f3b867", "#d98d45"]))
    with xf(c, 760, 560, 3.2):
        draw_head(c, 0, 0, "you", "dry", t, look=(-0.3, 0.4), sweat=1.0)
    k, a = pop(t, 15.0)
    with xf(c, 1420, 420, k, alpha=a):
        card(c, -250, -170, 500, 340, "#ffffff")
        text(c, "SIPS TODAY", 0, -80, 44, "#7a7a8c", "ExtraBold")
        text(c, "0", 0, 120, 210, "#ff3b3b")
    k2 = at(t, 16.4, 0.3)
    if k2 > 0:
        draw_bottle(c, 1420, 760, 0.8, fill=0)
        cross_mark(c, 1420, 760, 140 * back_out(k2), "#ff3b3b", 0.9)


def s_mirror(c, t):
    lt = t - 18.1
    cam(c, 1.0 + 0.015 * lt, 960, 540)
    draw_sky(c, "hot", t, sun_pos=(1650, 160))
    fill_shader(c, skia.Rect(0, 600, W, H), linear(0, 600, 0, H, ["#f3b867", "#d98d45"]))
    vignette(c, 0.35)
    shake = 3.5 * math.sin(t * 37) + 2.5 * math.sin(t * 23)
    rise = ease_out(at(t, 18.1, 0.9))
    with xf(c, 960 + shake, lerp(1300, 720, rise), 1.6, rot=shake * 0.6):
        draw_hand_big(c, 0, 80, 1.0)
        draw_mirror(c, 0, -30, 2.0, rot=-8, glint=0.15 * (1 + math.sin(t * 9)), t=t)
    k = window(t, 19.4, 22.6)
    if k:
        pill(c, 960, 160, "TINY PINK MIRROR", 44, "#ff5c9a", "#ffffff", a=k)


def s_how(c, t):
    # rewind effect
    sp = (t - 22.6) * 3000
    scene_bg(c, "flash", t, scroll=-sp, shimmer=0, props=True)
    draw_vehicle(c, 960, CAR_Y, 1.0, wheel_rot=-sp * 0.5, t=t, riders=[("noor", "happy"), ("you", "laugh")])
    c.drawRect(skia.Rect(0, 0, W, H), P("#1b1b2f", a=0.45))
    for i in range(6):
        y = (i * 190 + t * 900) % H
        c.drawRect(skia.Rect(0, y, W, y + 6), P("#ffffff", a=0.18))
    k, a = pop(t, 22.7)
    with xf(c, 960, 470, k, alpha=a):
        for i in range(2):
            c.drawPath(poly([(-40 + i * 90 - 60, 0), (40 + i * 90 - 60, -55), (40 + i * 90 - 60, 55)]),
                       P("#ffffff"))
    headline(c, t, 23.0, ["HOW DID YOU", "END UP HERE?"], y=700, size=92, accent="#ffd34d")


def sepia_layer(c):
    m = [0.39, 0.77, 0.19, 0, 0,
         0.35, 0.69, 0.17, 0, 0,
         0.27, 0.53, 0.13, 0, 0,
         0, 0, 0, 1, 0]
    # blend sepia 50% with identity for a warm "memory" look
    ident = [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0]
    mm = [lerp(a, b, 0.45) for a, b in zip(ident, m)]
    p = skia.Paint(ColorFilter=skia.ColorFilters.Matrix(mm))
    c.saveLayer(None, p)


def s_flashback(c, t):
    sepia_layer(c)
    lt = t - 25.0
    sp = lt * 900
    zoom = 1.0
    inset = window(t, 30.3, 37.6, 0.35)
    cam(c, zoom, 960, 600)
    scene_bg(c, "flash", t, scroll=sp)
    bounce = 4 * abs(math.sin(t * 9))
    laugh = "laugh" if (t < 33.0 or t > 35.6) else "happy"
    draw_vehicle(c, 820, CAR_Y, 1.0, wheel_rot=sp * 0.9, bounce=bounce, t=t,
                 riders=[("noor", laugh), ("you", laugh if t < 33 else "happy")])
    for i in range(4):
        ph = (t * 0.5 + i / 4) % 1
        text(c, "♪", 700 + i * 70 + 30 * math.sin(t * 2 + i), 520 - ph * 220, 60, "#ffffff", "Bold", a=1 - ph)
    if inset:
        with xf(c, 1450, 400, back_out(clamp(inset * 1.4)), alpha=inset):
            c.drawCircle(0, 0, 250, P("#ffffff"))
            c.save()
            c.clipPath(skia.Path().addCircle(0, 0, 236), skia.ClipOp.kIntersect, True)
            c.drawRect(skia.Rect(-250, -250, 250, 250), P("#6d4c41"))
            rrect(c, -250, 40, 500, 210, 40, "#8d6e63")
            rrect(c, -250, -250, 500, 160, 0, "#bfe6f2")
            roll = 70 * math.sin(t * 3.2)
            draw_bottle(c, roll, 60, 1.1, fill=0.95, rot=90 + roll * 1.2)
            c.restore()
            c.drawCircle(0, 0, 243, P("#ffd34d", 14))
            pill(c, 0, 250, "½ LITER", 40, "#ffd34d", "#1b1b2f")
    c.restore()
    k = window(t, 33.2, 35.9, 0.2)
    if k:
        bubble(c, 420, 330, "ENOUGH?", 50, a=k, s=back_out(at(t, 33.2, 0.3)))
    k = window(t, 34.0, 37.6, 0.2)
    if k:
        bubble(c, 540, 470, "SURE. I'M FINE.", 46, a=k, s=back_out(at(t, 34.0, 0.3)), bg="#ffd34d")


def s_daily_loss(c, t):
    info_bg(c, t)
    headline(c, t, 37.7, ["MOST ADULTS LOSE"], y=170, size=70)
    for i in range(3):
        k, a = pop(t, 38.0 + i * 0.25)
        drain = clamp((t - 39.2 - i * 0.5) / 1.6) * (0.9 if i < 2 else 0.45)
        with xf(c, 560 + i * 260, 540, k * 1.35, alpha=a):
            draw_bottle(c, 0, 0, 1.0, fill=1 - drain)
            text(c, "1 L", 0, 140, 40, "#ffffff")
    k, a = pop(t, 39.4)
    with xf(c, 820, 830, k, alpha=a):
        text(c, "2–3 LITERS / DAY", 0, 30, 84, "#4cc3ff", shadow=True)
    k, a = pop(t, 41.2)
    with xf(c, 1520, 540, k, alpha=a):
        card(c, -210, -260, 420, 520, "#ffffff")
        draw_head(c, 0, -110, "you", "worried", t, r=80)
        text(c, "YOU PUT BACK", 0, 50, 34, "#7a7a8c", "ExtraBold")
        text(c, "0 L", 0, 185, 140, "#ff3b3b")


def s_question(c, t):
    info_bg(c, t, "#0f3d5e", "#1e6091")
    if t < 47.6:
        headline(c, t, 44.1, ["WHAT HAPPENS IF YOU", "DIDN'T DRINK WATER?"], y=470, size=100, accent="#ffd34d")
        for i in range(10):
            ph = (t * 0.35 + i / 10) % 1
            drop(c, 120 + i * 190, 100 + ph * 900, 18, "#4cc3ff", a=0.25 * (1 - ph))
        return
    k, a = pop(t, 47.7)
    with xf(c, 960, 140, k, alpha=a):
        text(c, "HERE'S THE CATCH", 0, 25, 70, "#ffd34d", shadow=True)
    water_body(c, 700, 640, 1.05, 0.62 - 0.03 * clamp((t - 48.3) / 4), t, leak=at(t, 48.3, 0.6))
    for i, (lab, val, col, st) in enumerate((("SPENDING WATER", "ALWAYS", "#4cc3ff", 48.5),
                                              ("PAYING IT BACK", "STOPPED", "#ff5c5c", 50.6))):
        k, a = pop(t, st)
        with xf(c, 1400, 470 + i * 260, k, alpha=a):
            card(c, -300, -100, 600, 200, "#ffffff")
            text(c, lab, 0, -25, 40, "#7a7a8c", "ExtraBold")
            text(c, val, 0, 60, 74, col)


def s_hour1(c, t):
    # car driving, coughs, stops
    stop_t = 55.1
    if t < stop_t:
        speed = lerp(900, 120, smooth((t - 52.8) / 2.3))
        scroll = (t - 52.8) * 700 - 200 * smooth((t - 52.8) / 2.3) ** 2
    else:
        speed = 0
        scroll = 2.3 * 700 - 200
    jerk = 10 * math.sin(t * 40) * window(t, 53.5, 55.1, 0.1)
    cam(c, 1.0 + 0.01 * (t - 52.8), 960, 600, dx=jerk * 0.5)
    scene_bg(c, "noon", t, scroll=scroll, shimmer=0.4)
    smoke = clamp((t - 53.4) / 0.5) * (1.0 if t < 58 else max(0.25, 1 - (t - 58) / 2))
    riders = [("noor", "worried" if t > 53.6 else "happy"), ("you", "shock" if t > 53.6 else "happy")]
    if t < 60.3:
        draw_vehicle(c, 960, CAR_Y, 1.0, wheel_rot=scroll * 0.9, bounce=abs(jerk) * 0.6, t=t, riders=riders,
                     smoke=smoke, hood=at(t, 57.0, 0.6))
    else:
        car_shadow(c, 1180, CAR_Y)
        draw_vehicle(c, 1180, CAR_Y, 1.0, hood=1.0, t=t, smoke=0.3)
    for i, st in enumerate((53.6, 54.3)):
        k = window(t, st, st + 1.0, 0.15)
        if k:
            bubble(c, 1350 + i * 140, 420 - i * 90, "COUGH!", 48, a=k, s=back_out(at(t, st, 0.25)), spiky=True,
                   bg="#ffd34d", t=t)
    k = window(t, 55.3, 57.4, 0.3)
    if k:
        text(c, ". . .", 960, 380, 120, "#ffffff", a=k, shadow=True)
        pill(c, 960, 470, "SILENCE", 40, "#1b1b2f", "#ffffff", a=k)
    k = window(t, 57.6, 60.4, 0.25)
    if k:
        with xf(c, 0, 0, alpha=k):
            c.drawRect(skia.Rect(0, 0, W, H), P("#000000", a=0.35))
            draw_phone(c, 960, 520 + 40 * (1 - ease_out(at(t, 57.6, 0.4))), 1.6, t)
    if t >= 60.3:
        g = smooth((t - 60.8) / 1.0)
        bx = lerp(905, 740, g)
        draw_char(c, 900, 830, "you", "give_l", "happy", t, s=1.0)
        draw_char(c, 680, 870, "noor", "give", "happy" if g > 0.5 else "neutral", t, s=1.0)
        draw_bottle(c, bx - 60, 760 + 10 * math.sin(g * math.pi), 0.5, 0.9)
        k = window(t, 61.2, 63.2, 0.2)
        if k:
            bubble(c, 560, 560, "OBVIOUSLY.", 44, a=k, s=back_out(at(t, 61.2, 0.3)))


def s_hour4(c, t):
    if t < 70.4:
        cam(c, 1.5 + 0.01 * (t - 63.2), 1050, 700)
        scene_bg(c, "noon", t, shimmer=0.6)
        car_shadow(c, 1320, CAR_Y, 1.0, 0.33)
        draw_vehicle(c, 1320, CAR_Y, 1.0, hood=1.0, t=t)
        draw_char(c, 1040, 905, "you", "sit", "tired", t, s=1.0, sweat=0.6, bob=3 * math.sin(t * 1.6))
        draw_char(c, 820, 905, "noor", "hug", "sleep", t, s=1.0, htilt=-10)
        draw_bottle(c, 820, 865, 0.55, fill=0.5, rot=-10)
        # breath vapor
        hx, hy = 1040, 905 - 118 - 47 + 25
        v = at(t, 66.0, 0.6)
        for i in range(10):
            ph = ((t * 0.6) + i / 10) % 1
            x = hx + 40 + ph * 220 + 20 * math.sin(t * 2 + i)
            y = hy - ph * 160
            c.drawCircle(x, y, 10 + ph * 30, P("#ffffff", a=0.35 * (1 - ph) * (0.25 + v)))
            if v > 0 and i % 3 == 0:
                drop(c, x, y - 10, 5 + ph * 6, "#4cc3ff", a=0.5 * v * (1 - ph))
        k = window(t, 66.4, 70.4, 0.3)
        if k:
            pill(c, 1260, 470, "INVISIBLE WATER VAPOR", 34, "#ffffff", "#1d7fd1", a=k)
        return
    info_bg(c, t, "#0b2545", "#13315c")
    level = 0.6 - 0.04 * clamp((t - 73.2) / 2.5)
    water_body(c, 760, 650, 1.1, ease_out(at(t, 70.4, 1.4)) * level, t, leak=at(t, 73.2, 0.5))
    k, a = pop(t, 71.0)
    with xf(c, 1380, 470, k, alpha=a):
        text(c, "≈60%", 0, 60, 210, "#4cc3ff", shadow=True)
        text(c, "OF YOUR BODY IS WATER", 0, 140, 44, "#ffffff", "ExtraBold")
    k, a = pop(t, 73.4)
    with xf(c, 1380, 790, k, alpha=a):
        pill(c, 0, 0, "AND IT'S LEAKING", 52, "#ff5c5c", "#ffffff")


def s_hour8(c, t):
    if t < 82.2:
        cam(c, 1.0, 960, 540)
        draw_sky(c, "noon", t)
        fill_shader(c, skia.Rect(0, 560, W, H), linear(0, 560, 0, H, ["#f2c27b", "#e2a45c"]))
        with xf(c, 700, 560, 3.0 + 0.05 * (t - 75.8)):
            draw_head(c, 0, 0, "you", "dry", t, sweat=0.4, look=(0.2, 0.2))
        k, a = pop(t, 79.4)
        with xf(c, 1400, 380, k, alpha=a):
            ring = 1 + 0.08 * math.sin(t * 14)
            c.drawCircle(0, 0, 140 * ring, P("#ff3b3b", a=0.2))
            c.drawCircle(0, 0, 110, P("#ff3b3b"))
            text(c, "!", 0, 50, 150, "#ffffff")
            text(c, "THIRST", 0, 230, 72, "#ffffff", shadow=True)
        k = window(t, 80.5, 82.2, 0.2)
        if k:
            pill(c, 1400, 760, "EARLY ALARM?", 52, "#ffffff", "#1b1b2f", a=k, s=back_out(at(t, 80.5, 0.3)))
        return
    info_bg(c, t, "#3d0c11", "#6a040f")
    if t < 83.0:
        k = back_out(at(t, 82.2, 0.35))
        with xf(c, 960, 540, 2.5 - 1.5 * k, rot=-8, alpha=clamp(k)):
            rrect(c, -330, -110, 660, 220, 30, "#ffffff", 0.0, stroke=None)
            rrect(c, -330, -110, 660, 220, 30, "#ff3b3b", stroke=16)
            text(c, "WRONG", 0, 60, 170, "#ff3b3b")
        return
    # thirst meter
    headline(c, t, 83.1, ["THIRST SHOWS UP AFTER YOU'VE LOST"], y=200, size=58)
    x0, x1, y = 260, 1660, 470
    rrect(c, x0, y - 40, x1 - x0, 80, 40, "#ffffff", 0.15)
    fillp = ease_out(at(t, 83.6, 4.0)) * 0.72
    rrect(c, x0, y - 40, (x1 - x0) * fillp + 1, 80, 40, "#ff7b54")
    for i in range(6):
        xx = lerp(x0, x1, i / 5)
        line(c, xx, y + 55, xx, y + 80, "#ffffff", 5, 0.7)
        text(c, f"{i * 0.5:.1f}%".replace(".0%", "%"), xx, y + 130, 36, "#ffffff", "ExtraBold", a=0.85)
    # 1-2% zone
    za, zb = lerp(x0, x1, 1 / 2.5), lerp(x0, x1, 2 / 2.5)
    k = at(t, 85.9, 0.5)
    if k:
        rrect(c, za, y - 70, zb - za, 140, 20, "#ffd34d", 0.35 * k)
        with xf(c, (za + zb) / 2, y - 140, back_out(k), alpha=k):
            pill(c, 0, 0, "1–2% OF BODY WEIGHT", 44, "#ffd34d", "#1b1b2f")
    k, a = pop(t, 88.7)
    with xf(c, 960, 760, k, alpha=a):
        text(c, "THIRST ISN'T THE FIRST WARNING.", 0, 0, 62, "#ffffff", shadow=True)
    k, a = pop(t, 90.9)
    with xf(c, 960, 860, k, alpha=a):
        text(c, "IT'S THE LATE ONE.", 0, 20, 78, "#ffd34d", shadow=True)


def s_night(c, t):
    if t < 96.0:
        cam(c, 1.05 + 0.01 * (t - 92.5), 900, 640)
        scene_bg(c, "night", t, sun_pos=(1450, 180))
        draw_vehicle(c, 1150, CAR_Y, 1.0, hood=1.0, t=t)
        draw_char(c, 760, 905, "noor", "hug", "sleep", t, s=1.0, htilt=-14)
        draw_char(c, 900, 905, "you", "sit", "tired", t, s=1.0, htilt=-8)
        c.drawRect(skia.Rect(0, 0, W, H), P("#0a1438", a=0.25))
        return
    info_bg(c, t, "#1b0f2e", "#3c1f5b")
    sq = 0.0
    if t > 102.7:
        sq = 0.5 + 0.5 * math.sin((t - 102.7) * 5)
        sq *= clamp((110.9 - t) / 0.4) if t < 110.9 else 0.3
    k, a = pop(t, 96.0)
    with xf(c, 520, 560, 1.0 * k, alpha=a):
        draw_kidney(c, -150, 0, 1.0, flip=True, squeeze=sq)
        draw_kidney(c, 150, 0, 1.0, squeeze=sq)
    # flow drops down the ureters
    if t > 106.9:
        for i in range(3):
            ph = ((t - 106.9) * 0.6 + i / 3) % 1
            drop(c, 520 + 150 - 42, 650 + ph * 200, 12, "#f0c27b", a=1 - ph)
    k, a = pop(t, 96.6)
    with xf(c, 1340, 300, k, alpha=a):
        val = counter(t, 96.6, 2.8, 0, 180)
        text(c, f"{val:.0f} L", 0, 50, 150, "#ffd34d", shadow=True)
        text(c, "OF PLASMA FILTERED / DAY", 0, 120, 40, "#ffffff", "ExtraBold")
    k, a = pop(t, 99.7)
    with xf(c, 1340, 640, k, alpha=a):
        pr = counter(t, 99.9, 1.6, 0, 0.99)
        c.drawCircle(0, 0, 120, P("#ffffff", 26, 0.15))
        arc = skia.Path()
        arc.addArc(skia.Rect(-120, -120, 120, 120), -90, 360 * pr)
        c.drawPath(arc, P("#4cc3ff", 26))
        text(c, f"{pr * 100:.0f}%", 0, 26, 72, "#ffffff")
        text(c, "PULLED BACK IN", 0, 190, 40, "#ffffff", "ExtraBold")
    k = window(t, 102.8, 106.9, 0.25)
    if k:
        pill(c, 520, 200, "SQUEEZING HARDER", 46, "#ff7b54", "#ffffff", a=k)
    k, a = pop(t, 106.9)
    if t > 106.9:
        with xf(c, 1340, 870, k, alpha=a):
            pill(c, 0, 0, "STILL NEED ~0.5 L / DAY TO FLUSH WASTE", 36, "#ffffff", "#3c1f5b")
    k = window(t, 110.9, 113.5, 0.25)
    if k:
        c.drawRect(skia.Rect(0, 0, W, H), P("#000000", a=0.55 * k))
        with xf(c, 960, 540, 0.9 + 0.1 * back_out(at(t, 110.9, 0.4)), alpha=k):
            text(c, "THE LEAK NEVER CLOSES.", 0, 30, 96, "#ffffff", shadow=True)


def s_crackers(c, t):
    if t < 116.0:
        cam(c, 1.4, 1000, 680)
        scene_bg(c, "night", t, sun_pos=(1500, 200))
        draw_vehicle(c, 1250, CAR_Y, 1.0, hood=1.0, t=t)
        draw_char(c, 980, 905, "you", "give", "happy" if t < 114.6 else "worried", t, s=1.0,
                  hold=lambda c_, hx, hy: draw_cracker(c_, hx + 15, hy - 20, 0.4, rot=10))
        c.drawRect(skia.Rect(0, 0, W, H), P("#0a1438", a=0.2))
        k = window(t, 114.6, 116.0, 0.2)
        if k:
            bubble(c, 1250, 450, "DRY ONES.", 46, a=k)
        return
    info_bg(c, t, "#3e2723", "#5d4037")
    cx, cy, r = 620, 560, 260
    k, a = pop(t, 116.0, 0.5)
    with xf(c, cx, cy, k, alpha=a):
        c.drawCircle(0, 0, r, P("#4cc3ff"))
        sweep = 72 * ease_out(at(t, 116.6, 0.8))
        wedge = skia.Path()
        wedge.moveTo(0, 0)
        wedge.arcTo(skia.Rect(-r - 20, -r - 20, r + 20, r + 20), -90, sweep, False)
        wedge.close()
        c.drawPath(wedge, P("#ffb74d"))
        text(c, "DRINKS", -40, 90, 50, "#ffffff")
        if sweep > 30:
            text(c, "FOOD", 150, -120, 40, "#3e2723")
    k, a = pop(t, 116.8)
    with xf(c, 1340, 380, k, alpha=a):
        text(c, "≈ 1/5", 0, 40, 150, "#ffb74d", shadow=True)
        text(c, "OF YOUR WATER COMES FROM FOOD", 0, 110, 36, "#ffffff", "ExtraBold")
    k, a = pop(t, 119.0)
    with xf(c, 1340, 760, k, alpha=a):
        draw_cracker(c, -140, 0, 1.2, rot=-8, face=t > 122.0, t=t)
        text(c, "+0 L", 120, 40, 110, "#ff5c5c", shadow=True)
    k, a = pop(t, 122.0)
    if t > 122.0:
        with xf(c, 1340, 560, k, alpha=a):
            pill(c, 0, 0, "THANK YOU, CRACKERS.", 40, "#ffffff", "#3e2723")


def s_sunrise(c, t):
    lt = t - 123.7
    rise = ease_out(lt / 4.0)
    sun = (lerp(380, 520, rise), lerp(640, 330, rise))
    tod = "sunrise" if lt < 3.5 else "hot"
    cam(c, 1.05, 960, 600)
    scene_bg(c, tod, t, sun_pos=sun, shimmer=clamp((lt - 2) / 3))
    car_shadow(c, 1120, CAR_Y, 1.0, 0.3)
    draw_vehicle(c, 1120, CAR_Y, 1.0, hood=1.0, t=t)
    draw_char(c, 760, 905, "noor", "sit", "tired", t, s=1.0)
    draw_char(c, 920, 905, "you", "sit", "dry", t, s=1.0, sweat=at(t, 127.8, 0.5))
    k, a = pop(t, 125.9)
    with xf(c, 1640, 520, k * 0.9, alpha=a):
        thermometer(c, 0, 0, 1.0, 0.25 + 0.7 * ease_out(at(t, 126.0, 5.0)), t)
    if t > 127.8:
        for i in range(8):
            ph = ((t - 127.8) * 0.7 + i / 8) % 1
            drop(c, 860 + i * 18, 690 + ph * 140, 9, "#8fd8ff", a=0.8 * (1 - ph))
    k, a = pop(t, 130.5)
    if t > 130.5:
        with xf(c, 900, 420, k, alpha=a):
            pill(c, 0, 0, "MORE WATER, GONE", 46, "#ff7b54", "#ffffff")


def s_brain(c, t):
    if t < 146.1:
        info_bg(c, t, "#240046", "#3c096c")
        if t < 134.8:
            headline(c, t, 132.7, ["HERE'S WHAT", "NOBODY MENTIONS"], y=460, size=110, accent="#ffd34d")
            return
        fog = ease_out(at(t, 138.9, 1.5))
        k, a = pop(t, 134.8)
        with xf(c, 620, 540, 1.5 * k, alpha=a):
            draw_brain(c, 0, 0, 1.0, fog=fog, t=t)
        k = window(t, 135.4, 138.9, 0.25)
        if k:
            with xf(c, 1360, 360, alpha=k):
                text(c, "NOT YOUR LEGS", 0, 0, 64, "#ffffff", shadow=True)
                line(c, -260, -20, 260, -20, "#ff3b3b", 10)
            with xf(c, 1360, 520, back_out(at(t, 136.9, 0.4)), alpha=at(t, 136.9, 0.3)):
                text(c, "YOUR JUDGMENT", 0, 0, 80, "#ffd34d", shadow=True)
        if t >= 138.9:
            k, a = pop(t, 138.9)
            with xf(c, 1360, 260, k, alpha=a):
                text(c, "~2% WATER LOSS", 0, 0, 80, "#ffd34d", shadow=True)
            for i, (lab, st) in enumerate((("FOCUS", 140.5), ("MOOD", 141.8))):
                k, a = pop(t, st)
                with xf(c, 1360, 430 + i * 150, k, alpha=a):
                    card(c, -260, -60, 520, 120, "#ffffff")
                    text(c, lab, -60, 22, 58, "#3c096c")
                    c.drawPath(poly([(150, -30), (200, -30), (200, 0), (225, 0), (175, 45), (125, 0), (150, 0)]),
                               P("#ff3b3b"))
            if t > 143.8:
                k, a = pop(t, 143.8)
                with xf(c, 1360, 800, k, alpha=a):
                    draw_cracker(c, -150, 0, 0.5 + 0.7 * ease_out(at(t, 144.0, 1.5)), rot=10)
                    text(c, "LITTLE THINGS", 110, -10, 46, "#ffffff")
                    text(c, "FEEL HUGE", 110, 50, 46, "#ffd34d")
        return
    if t < 150.4:
        cam(c, 1.45, 1000, 700)
        scene_bg(c, "hot", t, shimmer=0.7)
        car_shadow(c, 1320, CAR_Y)
        draw_vehicle(c, 1320, CAR_Y, 1.0, hood=1.0, t=t)
        quiet = t > 148.9
        draw_char(c, 1050, 870, "you", "angry", "angry" if not quiet else "worried", t, s=1.0,
                  look=(-1, 0), sweat=0.6, tilt=-4 if not quiet else 0)
        draw_char(c, 780, 905, "noor", "hug" if quiet else "sit", "sad", t, s=1.0, look=(1, 0),
                  htilt=-10 if quiet else 0)
        if not quiet:
            bubble(c, 1150, 470, "THAT'S MY CRACKER!", 40, s=back_out(at(t, 146.2, 0.3)), spiky=True,
                   bg="#ff5c5c", fg="#ffffff", t=t)
        else:
            text(c, ". . .", 780, 640, 70, "#ffffff", a=at(t, 148.9, 0.4), shadow=True)
        return
    # terrible idea
    info_bg(c, t, "#1a0505", "#3d0c0c")
    with xf(c, 700, 680, 3.0):
        draw_head(c, 0, 0, "you", "worried", t, look=(0.5, -0.8), sweat=0.6)
    flick = 0.65 + 0.35 * (1 if int(t * 7) % 3 else 0)
    k, a = pop(t, 152.0)
    with xf(c, 1250, 400, 1.6 * k, alpha=a):
        lightbulb(c, 0, 0, 1.0, "#ff5c3b", flick * at(t, 152.3, 0.5), t)
    k = at(t, 152.6, 0.5)
    if k:
        with xf(c, 1250, 720, back_out(k), alpha=k):
            text(c, "A TERRIBLE IDEA...", 0, 0, 64, "#ffb3a7", shadow=True)
            text(c, "THAT SOUNDS SMART", 0, 80, 54, "#ffffff", "ExtraBold")


def s_mirror_play(c, t):
    cam(c, 1.3, 1080, 640)
    scene_bg(c, "noon", t, shimmer=0.5)
    car_shadow(c, 1200, CAR_Y)
    draw_vehicle(c, 1200, CAR_Y, 1.0, hood=0.0, t=t)
    # Noor climbs onto the hood
    climb = smooth((t - 155.1) / 1.4)
    nx = lerp(1500, 1340, climb)
    ny = lerp(905, 700, climb) - 30 * math.sin(climb * math.pi)
    if t < 157.0:
        pose = walk_pose(t, 8, 20) if climb < 1 else "stand"
        draw_char(c, nx, ny, "noor", pose, "happy", t)
    elif t < 165.3:
        pose = "mirror_selfie" if t < 160.2 else "mirror_up"
        expr = "laugh" if 159.2 < t < 160.2 else "happy"
        draw_char(c, 1340, 700, "noor", pose, expr, t, look=(1, -0.3),
                  hold=lambda c_, hx, hy: draw_mirror(c_, hx, hy - 10, 0.5, rot=20, glint=0.3, t=t))
        if 159.2 < t < 160.2:
            for i in range(5):
                sparkle(c, 1400 + 50 * math.cos(i * 1.3 + t * 3), 520 + 40 * math.sin(i * 2.1 + t * 3), 18,
                        "#ffffff", 0.9)
    else:
        draw_char(c, 1340, 700, "noor", "give", "happy", t, look=(1, 0.3), flip=True,
                  hold=lambda c_, hx, hy: draw_mirror(c_, hx, hy - 10, 0.5, rot=-30, glint=0.6, t=t))
    # you sitting in shade
    if t < 165.3:
        expr = "roll" if 160.2 < t < 162.9 else ("worried" if t < 160.2 else "tired")
    elif t < 167.8:
        expr = "squint"
    else:
        expr = "laugh"
    draw_char(c, 900, 905, "you", "sit", expr, t, s=1.0, look=(1, -0.4) if expr != "roll" else (0, 0))
    if t > 165.3:
        b = at(t, 165.3, 0.3)
        hx, hy = 1340 - 60, 700 - 150
        tx, ty = 900, 905 - 165
        beam = poly([(hx, hy - 12), (hx, hy + 12), (tx + 60, ty + 60), (tx - 60, ty - 60)])
        c.drawPath(beam, P("#fff5b0", a=0.55 * b))
        glow(c, tx, ty, 160 * b, "#fff5b0", 0.7 * b)
    k = window(t, 159.2, 160.3, 0.15)
    if k:
        bubble(c, 1560, 470, "SELFIE TIME!", 44, a=k, bg="#ff5c9a", fg="#ffffff")
    k = window(t, 162.9, 165.2, 0.2)
    if k:
        bubble(c, 900, 520, "WHO PACKS A MIRROR?", 40, a=k)


def s_your_turn(c, t):
    if t < 176.7:
        cam(c, 1.6, 1000, 700)
        scene_bg(c, "noon", t, shimmer=0.5)
        car_shadow(c, 1350, CAR_Y)
        draw_vehicle(c, 1350, CAR_Y, 1.0, hood=1.0, t=t)
        shake = 14 * math.sin((t - 174.2) * 14) if 174.2 < t < 175.4 else 0
        draw_char(c, 1100, 905, "you", "sit", "tired", t, s=1.0, htilt=shake, talk=1.0 if 175.4 < t < 176.1 else 0)
        draw_char(c, 880, 905, "noor", "give", "worried", t, s=1.0, look=(1, 0), talk=1.0 if 173.3 < t < 173.8 else 0,
                  hold=lambda c_, hx, hy: draw_bottle(c_, hx + 10, hy - 40, 0.45, 0.4))
        k = window(t, 173.2, 175.0, 0.2)
        if k:
            bubble(c, 820, 520, "YOUR TURN.", 44, a=k, bg="#ffc93c")
        k = window(t, 175.3, 176.7, 0.15)
        if k:
            bubble(c, 1180, 520, "I'M FINE.", 44, a=k)
        return
    # Grandma Layla memory
    info_bg(c, t, "#4a3426", "#6d4c41")
    sepia_layer(c)
    k, a = pop(t, 176.8, 0.6)
    with xf(c, 760, 540, k, rot=-4, alpha=a):
        card(c, -330, -380, 660, 760, "#f6ead7", r=20)
        rrect(c, -290, -340, 580, 560, 10, "#bfe3f0")
        fill_shader(c, skia.Rect(-290, 80, 290, 220), linear(0, 80, 0, 220, ["#efc98c", "#dcaa68"]))
        draw_char(c, 0, 60, "gran", "stand", "happy", t, s=1.0)
        text(c, "GRANDMA LAYLA", 0, 300, 44, "#6d4c41")
    c.restore()
    k, a = pop(t, 177.6)
    with xf(c, 1400, 460, k, rot=3, alpha=a):
        bubble(c, 0, 0, "SMALL SIPS, OFTEN.", 52, bg="#ffffff")
    k, a = pop(t, 180.3)
    with xf(c, 1400, 700, k, alpha=a):
        text(c, "(YOU DIDN'T LISTEN THEN EITHER)", 0, 0, 34, "#ffd9b0", "ExtraBold")


def s_walk_idea(c, t):
    if t < 188.6:
        cam(c, 1.1, 960, 620)
        scene_bg(c, "hot", t, shimmer=1.6)
        car_shadow(c, 1100, CAR_Y)
        draw_vehicle(c, 1100, CAR_Y, 1.0, hood=1.0, t=t)
        draw_char(c, 760, 905, "noor", "sit", "tired", t)
        draw_char(c, 900, 870, "you", "stand", "worried", t, look=(-1, 0), sweat=1.0)
        if t > 184.7:
            k, a = pop(t, 184.7)
            flick = 0.7 + 0.3 * (1 if int(t * 7) % 3 else 0)
            with xf(c, 900, 470, k, alpha=a):
                lightbulb(c, 0, 0, 0.9, "#ff5c3b", flick, t)
        k, a = pop(t, 187.3)
        if t > 187.3:
            with xf(c, 520, 380, k, alpha=a):
                pill(c, 0, 0, "WALK FOR HELP?", 60, "#ff5c3b", "#ffffff")
        return
    if t < 200.5:
        info_bg(c, t, "#7a3412", "#b45309")
        # map
        k, a = pop(t, 188.6)
        with xf(c, 960, 360, k, alpha=a):
            card(c, -800, -220, 1600, 380, "#f6d7a7")
            p = skia.Path()
            p.moveTo(-650, 40)
            p.cubicTo(-300, -120, 100, 160, 620, 0)
            dash = skia.Paint(AntiAlias=True, Color=C("#8a4b1d"), Style=skia.Paint.kStroke_Style, StrokeWidth=10,
                              PathEffect=skia.DashPathEffect.Make([30, 22], -t * 40))
            c.drawPath(p, dash)
            # town
            for i in range(3):
                rrect(c, -720 + i * 40, -30 - i * 20, 34, 70 + i * 20, 4, "#8a4b1d")
            text(c, "LAST TOWN", -650, 120, 34, "#8a4b1d", "ExtraBold")
            draw_vehicle(c, 640, 30, 0.22, hood=1.0)
            text(c, "YOU", 640, 120, 34, "#8a4b1d", "ExtraBold")
            pill(c, -60, -150, "HOURS AWAY", 40, "#8a4b1d", "#ffffff")
        if t > 191.3:
            # walking figure sweating
            draw_char(c, 520, 860, "you", walk_pose(t, 7), "tired", t, s=0.9, sweat=1.0)
            k, a = pop(t, 192.0)
            with xf(c, 1250, 800, k, alpha=a):
                text(c, "> 1 LITER", 0, 0, 110, "#ffffff", shadow=True)
                text(c, "OF SWEAT EVERY HOUR", 0, 75, 44, "#ffe0b2", "ExtraBold")
        return
    if t < 207.1:
        info_bg(c, t, "#3d0c11", "#6a040f")
        k, a = pop(t, 200.6)
        with xf(c, 960, 380, k, alpha=a):
            text(c, "THE RULE", 0, 0, 60, "#ffd34d", shadow=True)
        headline(c, t, 201.7, ["YOU CAN'T", "OUTWALK THE HEAT"], y=530, size=110, accent="#ffffff")
        k, a = pop(t, 203.6)
        with xf(c, 960, 860, k, alpha=a):
            text(c, "EVERY STEP SPENDS WATER YOU DON'T HAVE", 0, 0, 44, "#ffb3a7", "ExtraBold")
        return
    cam(c, 1.5, 950, 700)
    scene_bg(c, "hot", t, shimmer=1.2)
    car_shadow(c, 1300, CAR_Y)
    draw_vehicle(c, 1300, CAR_Y, 1.0, hood=1.0, t=t)
    throb = 1.0 + 0.08 * abs(math.sin(t * 6))
    draw_char(c, 1000, 870, "you", "stand", "worried", t, sweat=1.0, look=(-0.6, 0.4))
    hx, hy = 1000, 870 - 118 - 47
    for i in range(5):
        ang = math.radians(-160 + i * 35)
        r0 = 80 * throb
        line(c, hx + math.cos(ang) * r0, hy + math.sin(ang) * r0, hx + math.cos(ang) * (r0 + 24),
             hy + math.sin(ang) * (r0 + 24), "#ff4d4d", 6, 0.8)
    tug = 6 * math.sin(t * 10) if t > 208.9 else 0
    draw_char(c, 860 + tug, 905, "noor", "tug", "sad", t, look=(1, -0.5), talk=1.0 if 210.7 < t < 211.2 else 0)
    k = window(t, 210.6, 212.0, 0.15)
    if k:
        bubble(c, 760, 560, "DON'T GO.", 46, a=k, bg="#ffc93c")


def s_choice(c, t):
    pick = smooth((t - 218.7) / 0.6)
    look = at(t, 217.4, 0.4)
    for side in (0, 1):
        x0 = side * W / 2
        c.save()
        c.clipRect(skia.Rect(x0, 0, x0 + W / 2, H))
        if side == 0:
            draw_sky(c, "hot", t, sun_pos=(500, 200), sun_r=120)
            draw_ground(c, "hot", scroll=0, props=False)
            heat_shimmer(c, t, 1.6)
            walk_x = 560 - ((t - 212) * 20)
            draw_char(c, walk_x, 760, "you", walk_pose(t, 6), "tired", t, s=0.6, sweat=1.0)
        else:
            draw_sky(c, "noon", t, sun_pos=(1700, 150))
            draw_ground(c, "noon", scroll=0, props=False)
            car_shadow(c, 1560, CAR_Y)
            draw_vehicle(c, 1560, CAR_Y, 0.8, hood=1.0, t=t)
            draw_char(c, 1250, 905, "noor", "sit", "happy" if pick > 0.5 else "worried", t, look=(1, 0))
            draw_char(c, 1390, 905, "you", "sit", "happy" if pick > 0.5 else "tired", t,
                      look=(-1, 0) if look > 0.5 else (0, 0))
        dim = (pick if side == 0 else 0)
        c.drawRect(skia.Rect(x0, 0, x0 + W / 2, H), P("#000000", a=0.55 * dim))
        c.restore()
    line(c, W / 2, 0, W / 2, H, "#ffffff", 12)
    k, a = pop(t, 213.2)
    with xf(c, W / 4, 170, k, alpha=a):
        pill(c, 0, 0, "WALK ALONE INTO THE HEAT", 40, "#ff5c3b", "#ffffff")
    k, a = pop(t, 214.8)
    with xf(c, 3 * W / 4, 170, k, alpha=a):
        pill(c, 0, 0, "STAY IN THE SHADE WITH NOOR", 40, "#1f9e9a", "#ffffff")
    with xf(c, W / 2, 540, 1.0 + 0.05 * math.sin(t * 4), alpha=1 - pick):
        c.drawCircle(0, 0, 80, P("#ffffff"))
        text(c, "OR", 0, 20, 56, "#1b1b2f")
    if pick > 0:
        with xf(c, 3 * W / 4, 420, back_out(pick), alpha=pick):
            c.drawCircle(0, 0, 90, P("#2ecc71"))
            check_mark(c, 0, 0, 110, "#ffffff", prog=pick)
            text(c, "YOU STAY.", 0, 160, 64, "#ffffff", shadow=True)


def s_signal(c, t):
    flash_times = (230.9, 231.6, 232.4)
    cam(c, 1.25, 1000, 640)
    scene_bg(c, "noon", t, shimmer=0.8)
    car_shadow(c, 1250, CAR_Y, 1.0, 0.45)
    draw_vehicle(c, 1250, CAR_Y, 1.0, hood=1.0, t=t)
    # you lying down in the shade
    crawl = smooth((t - 219.9) / 2.0)
    yx = lerp(560, 780, crawl)
    draw_char(c, yx, 930, "you", "stand", "tired", t, s=0.95, tilt=-85, look=(0, -1),
              bob=0)
    if t < 226.5:
        draw_char(c, 1000, 905, "noor", "sit", "worried", t, look=(-1, 0.3))
    else:
        tilt_up = t > 229.1
        draw_char(c, 1000, 870, "noor", "mirror_up" if tilt_up else "give", "happy", t, look=(0.5, -1),
                  hold=lambda c_, hx, hy: draw_mirror(c_, hx, hy - 10, 0.45, rot=-40 if tilt_up else 0,
                                                      glint=max([window(t, ft, ft + 0.35, 0.08) for ft in flash_times]
                                                                + [0.2]), t=t))
    k = window(t, 222.1, 224.4, 0.25)
    if k:
        pill(c, 760, 560, "MOVE AS LITTLE AS YOU CAN", 40, "#ffffff", "#1b1b2f", a=k)
    k = window(t, 224.4, 226.5, 0.25)
    if k:
        with xf(c, 760, 560, alpha=k):
            pill(c, 0, 0, "EVERY DROP COUNTS", 44, "#4cc3ff", "#ffffff")
    for i, ft in enumerate(flash_times):
        f = window(t, ft, ft + 0.35, 0.08)
        if f:
            beam = poly([(1060, 640), (1080, 650), (1500 + i * 90, -50), (1350 + i * 90, -50)])
            c.drawPath(beam, P("#fffbe0", a=0.6 * f))
            text(c, "FLASH!", 1260 + i * 160, 380 - i * 60, 64, "#ffffff", a=f, outline="#ff5c9a", ow=10)
    c.restore()
    c.save()
    fl = max(window(t, ft, ft + 0.2, 0.05) for ft in flash_times)
    if fl:
        c.drawRect(skia.Rect(0, 0, W, H), P("#ffffff", a=0.35 * fl))


def s_ranger(c, t):
    if t < 239.9:
        # far away: Ines at a lookout
        cam(c, 1.0, 960, 540)
        scene_bg(c, "noon", t, road=False, shimmer=0.6)
        ridge(c, 780, 120, [(0.003, 1.0, 4.0)], "#c58b55")
        rrect(c, 1250, 420, 30, 400, 6, "#6b4f2a")
        rrect(c, 1450, 420, 30, 400, 6, "#6b4f2a")
        rrect(c, 1210, 400, 310, 40, 8, "#8a6a3a")
        draw_char(c, 1365, 280, "ines", "bino", "neutral", t, s=0.95, look=(-1, 0))
        # binoculars
        rrect(c, 1290, 140, 70, 34, 14, "#2b2b30")
        k = at(t, 236.0, 0.3)
        # tiny spark far away
        sp = 0.5 + 0.5 * math.sin(t * 12)
        sparkle(c, 330, 640, 16 + 30 * sp * k, "#ffffff", 0.5 + 0.5 * k, rot=t * 50)
        glow(c, 330, 640, 60 * (0.5 + k), "#ffffff", 0.5 * k)
        k2 = window(t, 233.9, 239.9, 0.3)
        if k2:
            pill(c, 1365, 80, "RANGER INES", 42, "#5b7d3a", "#ffffff", a=k2)
        if k:
            with xf(c, 330, 520, back_out(k), alpha=k):
                pill(c, 0, 0, "A SPARK WHERE NOTHING SHOULD SPARKLE", 30, "#ffffff", "#1b1b2f")
        return
    if t < 243.5:
        arrive = ease_out((t - 239.9) / 2.6)
        cam(c, 1.0, 960, 600)
        scene_bg(c, "noon", t, shimmer=0.4)
        car_shadow(c, 700, CAR_Y)
        draw_vehicle(c, 700, CAR_Y, 1.0, hood=1.0, t=t)
        tx = lerp(2400, 1420, arrive)
        draw_vehicle(c, tx, CAR_Y, 1.05, wheel_rot=-tx * 0.6, kind="truck", t=t, flip=True,
                     riders=[("ines", "happy")])
        draw_char(c, 420, 870, "noor", "wave" if int(t * 3) % 2 else "stand", "laugh", t, look=(1, 0))
        k = window(t, 242.9, 243.6, 0.15)
        if k:
            pill(c, 1420, 400, "REAL SHADE", 46, "#ffffff", "#5b7d3a", a=k)
        return
    cam(c, 1.0, 960, 540)
    draw_sky(c, "noon", t)
    fill_shader(c, skia.Rect(0, 600, W, H), linear(0, 600, 0, H, ["#f2c27b", "#e2a45c"]))
    awning(c, t)
    sip_phase = (t - 243.5) % 1.6
    sipping = sip_phase < 0.8
    draw_char(c, 900, 905, "you", "drink" if sipping else "sit", "happy_closed" if sipping else "happy", t, s=1.25,
              hold=lambda c_, hx, hy: draw_bottle(c_, hx, hy - 50, 0.5, 0.85, rot=-120 if sipping else -20))
    draw_char(c, 1300, 905, "noor", "sit", "happy", t, s=1.25, look=(-1, 0))
    for i, st in enumerate((244.4, 245.6, 246.8)):
        k, a = pop(t, st)
        if t > st:
            with xf(c, 520 + i * 0 - 40, 380 + i * 110, k, alpha=a):
                pill(c, 0, 0, "SIP", 44, "#4cc3ff", "#ffffff")
    k, a = pop(t, 244.2)
    with xf(c, 1450, 420, k, alpha=a):
        pill(c, 0, 0, "SIPS, NOT GULPS", 48, "#ffffff", "#1b1b2f")


def s_not_fine(c, t):
    if t < 254.1:
        cam(c, 1.45, 960, 650)
        draw_sky(c, "noon", t)
        fill_shader(c, skia.Rect(0, 600, W, H), linear(0, 600, 0, H, ["#f2c27b", "#e2a45c"]))
        awning(c, t)
        draw_char(c, 1150, 870, "ines", "stand", "worried" if t > 252.6 else "happy", t, look=(-1, 0.2),
                  talk=1.0 if 248.9 < t < 250.3 else 0)
        draw_char(c, 800, 905, "you", "sit", "sad" if t > 252.6 else "tired", t, look=(1, -0.3),
                  talk=1.0 if 252.6 < t < 253.5 else 0,
                  hold=lambda c_, hx, hy: draw_bottle(c_, hx, hy - 40, 0.4, 0.6))
        k = window(t, 249.0, 250.6, 0.2)
        if k:
            bubble(c, 1250, 470, "HOW ARE YOU DOING?", 38, a=k)
        k = window(t, 252.5, 254.2, 0.2)
        if k:
            bubble(c, 760, 520, "I'M NOT FINE.", 48, a=k, s=back_out(at(t, 252.5, 0.3)), bg="#ffd34d")
        return
    info_bg(c, t, "#0b2545", "#13315c")
    water_body(c, 330, 640, 0.85, 0.5, t, leak=1.0)
    headline(c, t, 254.2, ["YOUR BODY NEVER", "STOPS SPENDING WATER"], y=420, size=74)
    k, a = pop(t, 257.0)
    with xf(c, 1060, 700, k, alpha=a):
        text(c, "EVEN WHEN YOU STOP PAYING.", 0, 0, 56, "#4cc3ff", shadow=True)
    c.translate(0, 0)


def s_fact_check(c, t):
    info_bg(c, t, "#102a43", "#243b53")
    if t < 266.2:
        headline(c, t, 258.9, ["SO WHAT'S REAL?"], y=170, size=96, accent="#ffd34d")
        k, a = pop(t, 260.9)
        with xf(c, 960, 320, k, alpha=a):
            text(c, "ALMOST EVERYTHING.", 0, 0, 56, "#ffffff", "ExtraBold")
        for i, (lab, st) in enumerate((("THE LEAK", 262.6), ("THE KIDNEYS", 263.6), ("THE LATE WARNING OF THIRST",
                                                                                       264.6))):
            k, a = pop(t, st)
            with xf(c, 960, 470 + i * 170, k, alpha=a):
                card(c, -560, -65, 1120, 130, "#ffffff")
                text(c, lab, -470, 20, 52, "#102a43", align="left")
                c.drawCircle(470, 0, 46, P("#2ecc71"))
                check_mark(c, 470, 0, 58, "#ffffff", prog=at(t, st + 0.2, 0.4))
        return
    if t < 278.2:
        headline(c, t, 266.2, ["\"3 DAYS WITHOUT WATER\""], y=170, size=80)
        k, a = pop(t, 269.6)
        with xf(c, 960, 280, k, alpha=a):
            text(c, "EXPERTS GIVE RANGES, NOT ONE NUMBER", 0, 0, 44, "#ffd34d", "ExtraBold")
        x0, x1, y = 260, 1660, 600
        line(c, x0, y, x1, y, "#ffffff", 8, 0.6)
        for d in range(8):
            xx = lerp(x0, x1, d / 7)
            line(c, xx, y - 20, xx, y + 20, "#ffffff", 6, 0.8)
            text(c, f"{d}", xx, y + 80, 44, "#ffffff", "ExtraBold")
        text(c, "DAYS", (x0 + x1) / 2, y + 150, 36, "#bcccdc", "ExtraBold")
        x3 = lerp(x0, x1, 3 / 7)
        k, a = pop(t, 266.8)
        with xf(c, x3, y - 90, k, alpha=a):
            pill(c, 0, 0, "~3", 50, "#ffffff", "#102a43")
        # heat shortens / shade stretches
        hk = ease_out(at(t, 272.8, 1.2))
        if hk > 0:
            xa = lerp(x3, lerp(x0, x1, 1.2 / 7), hk)
            rrect(c, xa, y - 20, x3 - xa, 40, 20, "#ff5c3b")
            text(c, "HEAT + EFFORT", (xa + x3) / 2, y - 140, 40, "#ff8a65", a=hk)
        sk = ease_out(at(t, 275.1, 1.5))
        if sk > 0:
            xb = lerp(x3, lerp(x0, x1, 7 / 7), sk)
            rrect(c, x3, y - 20, xb - x3, 40, 20, "#4cc3ff")
            text(c, "COOL SHADE + REST", (x3 + xb) / 2 + 60, y - 140, 40, "#81d4fa", a=sk)
        return
    headline(c, t, 278.2, ["LOSE MORE THAN ~10%", "OF BODY WEIGHT IN WATER"], y=170, size=66)
    cx, cy, R = 960, 800, 360
    arcbg = skia.Path()
    arcbg.addArc(skia.Rect(cx - R, cy - R, cx + R, cy + R), 180, 180)
    c.drawPath(arcbg, P("#ffffff", 50, 0.15))
    for i, (col, a0, a1) in enumerate((("#2ecc71", 180, 36), ("#ffd34d", 216, 54), ("#ff3b3b", 270, 90))):
        ap = skia.Path()
        ap.addArc(skia.Rect(cx - R, cy - R, cx + R, cy + R), a0, a1)
        c.drawPath(ap, P(col, 50, 0.85))
    val = ease_out(at(t, 278.6, 2.6))
    ang = math.radians(180 + 180 * lerp(0.05, 0.92, val))
    line(c, cx, cy, cx + math.cos(ang) * (R - 60), cy + math.sin(ang) * (R - 60), "#ffffff", 16)
    c.drawCircle(cx, cy, 30, P("#ffffff"))
    k, a = pop(t, 281.0)
    with xf(c, cx, cy - 120, k, alpha=a):
        pill(c, 0, 0, "MEDICAL EMERGENCY", 50, "#ff3b3b", "#ffffff")


def s_lessons(c, t):
    if t < 288.5:
        info_bg(c, t, "#1d3557", "#457b9d")
        headline(c, t, 283.5, ["SO HOW LONG", "COULD YOU LAST?"], y=330, size=110, accent="#ffd34d")
        k, a = pop(t, 285.6)
        with xf(c, 960, 760, k, alpha=a):
            text(c, "IT DEPENDS WHERE YOU'RE STANDING.", 0, 0, 56, "#ffffff", "ExtraBold")
            # map pin
            with xf(c, 0, 130):
                c.drawCircle(0, -40, 40, P("#ff5c3b"))
                c.drawPath(poly([(-34, -20), (34, -20), (0, 40)]), P("#ff5c3b"))
                c.drawCircle(0, -40, 15, P("#ffffff"))
        return
    info_bg(c, t, "#0b3d2e", "#14532d")
    headline(c, t, 288.5, ["THE REAL LESSON"], y=150, size=84, accent="#ffd34d")
    items = (("DRINK BEFORE YOU'RE THIRSTY", 289.8, "drop"),
             ("STAY WITH YOUR CAR, IN THE SHADE", 292.7, "car"),
             ("ALWAYS TELL SOMEONE YOUR ROUTE", 294.5, "pin"))
    for i, (lab, st, icon) in enumerate(items):
        k, a = pop(t, st)
        with xf(c, 960, 360 + i * 230, k, alpha=a):
            card(c, -720, -90, 1440, 180, "#ffffff")
            c.drawCircle(-610, 0, 64, P("#14532d"))
            if icon == "drop":
                drop(c, -610, 12, 28, "#4cc3ff")
            elif icon == "car":
                draw_vehicle(c, -610, 30, 0.18, t=t)
            else:
                c.drawCircle(-610, -12, 24, P("#ff5c3b"))
                c.drawPath(poly([(-630, 0), (-590, 0), (-610, 34)]), P("#ff5c3b"))
            text(c, f"{i + 1}. {lab}", -500, 22, 56, "#14532d", align="left")


def s_twist(c, t):
    if t < 305.1:
        info_bg(c, t, "#03045e", "#0077b6")
        if t < 301.1:
            headline(c, t, 297.3, ["BUT HERE'S THE TWIST..."], y=200, size=84, accent="#ffd34d")
            k, a = pop(t, 298.8)
            with xf(c, 960, 640, k, alpha=a):
                # overflowing glass
                c.drawPath(poly([(-130, -200), (130, -200), (100, 200), (-100, 200)]), P("#ffffff", a=0.25))
                c.drawPath(poly([(-125, -180), (125, -180), (98, 190), (-98, 190)]), P("#4cc3ff", a=0.85))
                c.drawPath(poly([(-130, -200), (130, -200), (100, 200), (-100, 200)]), P("#ffffff", 8))
                for i in range(8):
                    ph = (t * 0.9 + i / 8) % 1
                    sgn = -1 if i % 2 else 1
                    drop(c, sgn * (140 + ph * 60), -190 + ph * 380, 16, "#4cc3ff", a=1 - ph)
            k, a = pop(t, 299.4)
            with xf(c, 960, 890, k, alpha=a):
                text(c, "WATER CAN HURT YOU THE OTHER WAY TOO", 0, 0, 52, "#ffffff", "ExtraBold")
            return
        headline(c, t, 301.1, ["WHAT IF YOU DRANK", "TOO MUCH WATER?"], y=420, size=120, accent="#4cc3ff")
        k, a = pop(t, 303.9)
        with xf(c, 960, 820, k, alpha=a):
            pill(c, 0, 0, "WHAT DO YOU THINK?", 52, "#ffd34d", "#03045e")
        return
    info_bg(c, t, "#111827", "#1f2937")
    k, a = pop(t, 305.1)
    with xf(c, 960, 300, k, alpha=a):
        card(c, -560, -130, 1120, 260, "#ffffff")
        c.drawCircle(-430, 0, 70, P("#1f9e9a"))
        draw_head(c, -430, 10, "noor", "happy", t, r=46)
        rrect(c, -320, -60, 720, 36, 18, "#e5e7eb")
        rrect(c, -320, 10, 520, 36, 18, "#e5e7eb")
        text(c, "TELL US IN THE COMMENTS", -320, 110, 36, "#6b7280", "ExtraBold", align="left")
    k, a = pop(t, 306.6)
    with xf(c, 960, 520, k, alpha=a):
        text(c, "WHICH BODY LIMIT SHOULD WE TEST NEXT?", 0, 0, 52, "#ffd34d", shadow=True)
    k, a = pop(t, 308.7)
    press = window(t, 309.4, 309.8, 0.1)
    with xf(c, 760, 760, k * (1 - 0.08 * press), alpha=a):
        rrect(c, -200, -70, 400, 140, 70, "#374151")
        thumbs_up(c, -90, 0, 0.7, "#ffffff")
        text(c, "LIKE", 50, 22, 56, "#ffffff")
    k2, a2 = pop(t, 309.2)
    subbed = t > 309.9
    with xf(c, 1220, 760, k2, alpha=a2):
        rrect(c, -250, -70, 500, 140, 70, "#374151" if subbed else "#ff0000")
        text(c, "SUBSCRIBED" if subbed else "SUBSCRIBE", 0, 22, 54, "#ffffff")
    if subbed:
        with xf(c, 1530, 760, back_out(at(t, 310.0, 0.3)), rot=15 * math.sin(t * 20)):
            bell(c, 0, 0, 0.7)
    # cursor
    cx = lerp(1600, 1200, ease_out(at(t, 309.0, 0.6)))
    cy = lerp(1000, 780, ease_out(at(t, 309.0, 0.6)))
    if t > 308.9:
        c.drawPath(poly([(cx, cy), (cx, cy + 60), (cx + 16, cy + 46), (cx + 28, cy + 72), (cx + 38, cy + 66),
                         (cx + 27, cy + 41), (cx + 46, cy + 40)]), P("#ffffff"))


SCENES = [
    (0.0, 6.0, s_open_wide),
    (6.0, 14.6, s_open_shade),
    (14.6, 18.1, s_zero_sips),
    (18.1, 22.6, s_mirror),
    (22.6, 25.0, s_how),
    (25.0, 37.6, s_flashback),
    (37.6, 44.0, s_daily_loss),
    (44.0, 52.8, s_question),
    (52.8, 63.2, s_hour1),
    (63.2, 75.8, s_hour4),
    (75.8, 92.5, s_hour8),
    (92.5, 113.4, s_night),
    (113.4, 123.7, s_crackers),
    (123.7, 132.6, s_sunrise),
    (132.6, 155.1, s_brain),
    (155.1, 171.3, s_mirror_play),
    (171.3, 182.0, s_your_turn),
    (182.0, 211.9, s_walk_idea),
    (211.9, 219.9, s_choice),
    (219.9, 233.8, s_signal),
    (233.8, 248.9, s_ranger),
    (248.9, 258.9, s_not_fine),
    (258.9, 283.5, s_fact_check),
    (283.5, 297.2, s_lessons),
    (297.2, 1e9, s_twist),
]

# Cuts inside scenes that also get a quick dip
EXTRA_CUTS = [70.4, 82.2, 96.0, 116.0, 146.1, 150.4, 176.7, 188.6, 200.5, 207.1, 239.9, 243.5, 254.1, 266.2,
              278.2, 288.5, 305.1]
CUTS = [s for s, _, _ in SCENES[1:]] + EXTRA_CUTS

STAMPS = [
    (0.2, 6.0, "DAY 2 · HIGH NOON"),
    (25.0, 37.6, "TWO DAYS EARLIER"),
    (52.8, 63.2, "HOUR 1"),
    (63.2, 70.4, "HOUR 4"),
    (75.8, 82.2, "HOUR 8"),
    (92.5, 96.0, "NIGHT 1"),
    (123.7, 132.6, "DAY 2 · SUNRISE"),
    (182.0, 188.6, "DAY 2 · NOON"),
    (239.9, 243.5, "AN HOUR LATER"),
]


def draw_stamp(c, t):
    for a, b, label in STAMPS:
        if a <= t < b:
            k = ease_out(at(t, a, 0.5))
            out = clamp((b - t) / 0.3)
            w = text_width(label, 40) + 110
            with xf(c, lerp(-w, 60, k), 60, alpha=out):
                rrect(c, 4, 8, w, 76, 38, "#000000", 0.25)
                rrect(c, 0, 0, w, 76, 38, "#ffd34d")
                c.drawCircle(42, 38, 20, P("#1b1b2f", 5))
                ang = t * 3
                line(c, 42, 38, 42 + 12 * math.cos(ang), 38 + 12 * math.sin(ang), "#1b1b2f", 4)
                line(c, 42, 38, 42, 26, "#1b1b2f", 4)
                text(c, label, 76, 52, 40, "#1b1b2f", align="left")


# ---------------------------------------------------------------- captions
FIXES = {"flesh": "flush"}


def load_captions(path):
    segs = json.load(open(path))
    chunks = []
    for seg in segs:
        words = []
        for w in seg["words"]:
            txt = w["w"].strip()
            core = txt.strip(".,?!").lower()
            if core in FIXES:
                txt = txt.lower().replace(core, FIXES[core])
            if core == "and" and 279.0 < w["s"] < 281.0:
                txt = "in"
            words.append(dict(w=txt, s=w["s"], e=w["e"]))
        cur = []
        for w in words:
            cur.append(w)
            if len(cur) >= 6 or (len(cur) >= 3 and w["w"][-1:] in ".,?!"):
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
    out = []
    for i, ch in enumerate(chunks):
        start = ch[0]["s"] - 0.08
        end = ch[-1]["e"] + 0.5
        if i + 1 < len(chunks):
            end = min(end, chunks[i + 1][0]["s"] - 0.08)
        out.append((start, end, ch))
    return out


CAPTIONS = load_captions(os.path.join(HERE, "transcript.json"))


def draw_captions(c, t):
    for start, end, ch in CAPTIONS:
        if start <= t < end:
            size = 60
            words = [w["w"].upper() for w in ch]
            sp = size * 0.42
            widths = [text_width(w, size) for w in words]
            total = sum(widths) + sp * (len(words) - 1)
            if total > 1700:
                size = size * 1700 / total
                sp *= 1700 / total
                widths = [x * 1700 / total for x in widths]
                total = 1700
            x = W / 2 - total / 2
            y = H - 80
            appear = ease_out(at(t, start, 0.15))
            for w, wd, wi in zip(words, widths, ch):
                active = wi["s"] - 0.05 <= t < max(wi["e"], wi["s"] + 0.15)
                spoken = t >= wi["s"] - 0.05
                col = "#ffd34d" if active else "#ffffff"
                sc = 1.12 if active else 1.0
                with xf(c, x + wd / 2, y - size * 0.35, sc, alpha=appear * (1.0 if spoken else 0.75)):
                    text(c, w, 0, size * 0.35, size, col, outline="#111111", ow=size * 0.2)
                x += wd + sp
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
    draw_stamp(c, t)
    dip = 0.0
    for ct in CUTS:
        d = abs(t - ct)
        if d < 0.16:
            dip = max(dip, 1 - d / 0.16)
    if t < 0.4:
        dip = max(dip, 1 - t / 0.4)
    if dip > 0:
        c.drawRect(skia.Rect(0, 0, W, H), P("#000000", a=dip * 0.9))
    draw_captions(c, t)
