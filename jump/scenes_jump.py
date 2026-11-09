"""Timeline for "What If You Jumped on Every World?". All times are absolute seconds in the voiceover."""
import json
import math
import os

import skia

from jgfx import *  # noqa: F401,F403
from jgfx import (W, H, C, P, xf, rrect, poly, line, text, text_width, linear, radial, fill_shader, glow, sparkle,
                  check_mark, cross_mark, mixhex, clamp, lerp, smooth, ease_out, back_out, at, window, pill, card,
                  bubble, draw_char, CHARS, WORLDS, jump_height, air_time, planet_icon, world_bg, person, jumper,
                  jump_state, mix_pose, head_y, height_tag, ruler, hoop, table_prop, house, tower, stair,
                  gravity_badge, title_card, stopwatch, arrow, grid_board, vignette, grain, POSE_STAND, POSE_CROUCH,
                  POSE_AIR, POSE_FLOAT, POSE_TPOSE, POSE_STRAIN, ground_y_at)

HERE = os.path.dirname(os.path.abspath(__file__))
GY = 860
PPM_PER_S = 211.0  # pixels per meter for a person drawn at scale 1 (1.75 m tall)


def ppm_for(s):
    return PPM_PER_S * s


def cam(c, zoom=1.0, cx=W / 2, cy=H / 2, dx=0.0, dy=0.0):
    c.translate(W / 2 + dx, H / 2 + dy)
    c.scale(zoom, zoom)
    c.translate(-cx, -cy)


def push(c, t, a, b, z0=1.0, z1=1.08, cx=W / 2, cy=H / 2):
    k = smooth((t - a) / max(0.1, b - a))
    z = lerp(z0, z1, k)
    cy = H / 2 + (cy - H / 2) * 0.3
    dx = 6 * math.sin(t * 0.7)
    dy = 4 * math.sin(t * 0.9 + 1)
    cam(c, z, cx, cy, dx, dy)


def shake(c, t, start, dur=0.4, amp=14):
    if start <= t < start + dur:
        k = 1 - (t - start) / dur
        c.translate(amp * k * math.sin(t * 90), amp * k * math.cos(t * 77))


def pop_pill(c, t, start, x, y, label, size=46, bg="#ffd34d", fg="#1b1b2f", end=None):
    y = min(y, 880)
    k = back_out(at(t, start, 0.45))
    a = clamp(at(t, start, 0.25))
    if end is not None:
        a *= clamp((end - t) / 0.3)
    if a > 0:
        pill(c, x, y, label, size, bg, fg, a=a, s=0.5 + 0.5 * k)


def big_text(c, t, start, s, x, y, size=110, color="#ffffff", end=None, outline="#0d1220"):
    k = back_out(at(t, start, 0.45))
    a = clamp(at(t, start, 0.25))
    if end is not None:
        a *= clamp((end - t) / 0.3)
    if a <= 0:
        return
    with xf(c, x, y, s=0.6 + 0.4 * k, alpha=a):
        text(c, s, 0, size * 0.35, size, "#000000", outline=outline, ow=size * 0.16)
        text(c, s, 0, size * 0.35, size, color)


def counter(t, start, dur, a, b):
    return lerp(a, b, ease_out(at(t, start, dur)))


def earth_props(c, t, gy=GY):
    # clouds, trees and a fence so Earth reads instantly as "home"
    for k, (x, y, s) in enumerate(((300, 180, 1.0), (980, 120, 0.8), (1580, 210, 1.1))):
        xx = (x + t * 12 * (k + 1)) % (W + 400) - 200
        for dx, dy, r in ((0, 0, 50), (55, 10, 40), (-55, 12, 38), (25, -25, 42)):
            c.drawCircle(xx + dx * s, y + dy * s, r * s, P("#ffffff", a=0.9))
    for x in (140, 1700, 1820):
        rrect(c, x - 14, gy - 190, 28, 190, 8, "#7a4a28")
        c.drawCircle(x, gy - 230, 90, P("#3f8a37"))
        c.drawCircle(x - 40, gy - 190, 60, P("#4c9b40"))
    for x in range(0, W, 60):
        rrect(c, x, gy - 70, 14, 70, 4, "#f1e3c8", a=0.0)


# =============================================================== 1. HOOK
def s_hook_tall(c, t):
    s = 0.36
    ppm = ppm_for(s)
    push(c, t, 0, 6, 1.0, 1.06, cy=600)
    world_bg(c, "pluto", t)
    tower(c, 1260, GY, ppm, 3, color="#6c7a99")
    T = 4.2
    h = 9.3 * ppm
    jumper(c, 900, GY, t, 1.3, h, T, s=s, expr="happy", expr_air="laugh")
    if t > 4.6:
        height_tag(c, 760, GY, GY - 9.3 * ppm, "3 STORIES", a=clamp((t - 4.9) / 0.3), side=-1)
    pop_pill(c, t, 0.9, W / 2, 140, "ONE SINGLE JUMP", 54)


def s_hook_heavy(c, t):
    s = 0.85
    push(c, t, 6, 11.2, 1.0, 1.08, cy=650)
    world_bg(c, "jupiter", t)
    pose = POSE_STRAIN if t < 9.3 or t > 9.9 else POSE_STAND
    lift = 0.0
    if 9.3 <= t < 9.75:
        u = (t - 9.3) / 0.45
        lift = 18 * 4 * u * (1 - u)
        pose = POSE_AIR
    person(c, 960, GY, pose, "you", "worried" if lift == 0 else "shock", t, s, sweat=1.0, lift=lift, shadow_h=lift)
    for k in range(3):
        x = 760 + k * 200
        arrow(c, x, 220 + 20 * math.sin(t * 3 + k), x, 420 + 20 * math.sin(t * 3 + k), "#ff5a3c", 18, 0.8)
    pop_pill(c, t, 7.0, W / 2, 140, "SAME LEGS. SAME EFFORT.", 50)
    pop_pill(c, t, 9.6, W / 2, 980 - 60, "BARELY OFF THE GROUND", 46, "#ff5a3c", "#ffffff")


def s_earth(c, t):
    s = 0.95
    ppm = ppm_for(s)
    push(c, t, 11.2, 19.0, 1.0, 1.1, cx=900, cy=640)
    world_bg(c, "earth", t)
    earth_props(c, t)
    T = air_time(1.0)
    hpx = 0.5 * ppm
    jumper(c, 900, GY, t, 12.6, hpx, T, s=s, repeat=2.4, expr="happy")
    a = clamp((t - 12.7) / 0.3)
    ruler(c, 1180, GY, ppm, 2.0, 0.5, a=a, label_every=2)
    if t > 12.9:
        sub = "≈ 20 INCHES" if t > 14.2 else None
        height_tag(c, 1320, GY, GY - hpx, "0.5 m", sub, a=clamp((t - 12.9) / 0.3))
    # "fixed number" lock, then it cracks on "but it doesn't"
    if t > 15.7:
        k = back_out(at(t, 15.7, 0.45))
        with xf(c, 520, 330, s=0.6 + 0.4 * k):
            card(c, -230, -80, 460, 160, "#0d1220", a=0.85)
            text(c, "0.5 m", -60, 34, 86, "#ffd34d")
            # padlock
            c.translate(40, 0)
            rrect(c, 95, -20, 70, 60, 10, "#c9ced8")
            p = skia.Path()
            p.addArc(skia.Rect(105, -60, 155, -2), 180, 180)
            c.drawPath(p, P("#c9ced8", 10))
            if t > 18.4:
                ck = clamp((t - 18.4) / 0.25)
                line(c, 110, -18, 130, 5, "#1b1b2f", 5, ck)
                line(c, 130, 5, 120, 20, "#1b1b2f", 5, ck)
                line(c, 120, 20, 150, 38, "#1b1b2f", 5, ck)
        if t > 18.4:
            pop_pill(c, t, 18.5, 520, 470, "NOT FIXED!", 44, "#ff5a3c", "#ffffff")
    pop_pill(c, t, 16.9, 520, 470 if t < 18.4 else -500, "BELONGS TO YOUR BODY?", 40)


def s_half_story(c, t):
    grid_board(c, t)
    k1 = back_out(at(t, 19.0, 0.5))
    k2 = back_out(at(t, 20.8, 0.5))
    # left: body
    with xf(c, 520, 560, s=0.4 + 0.6 * k1, alpha=clamp(k1)):
        card(c, -300, -330, 600, 620, "#16264a", a=0.9)
        person(c, 0, 200, POSE_STAND, "you", "happy", t, 0.9, shadow_h=None)
        text(c, "YOUR BODY", 0, -250, 60, "#ffffff")
        text(c, "50%", 0, 270, 60, "#ffd34d")
    text(c, "+", W / 2, 600, 140, "#ffffff", a=clamp(k2))
    with xf(c, 1400, 560, s=0.4 + 0.6 * k2, alpha=clamp(k2)):
        card(c, -300, -330, 600, 620, "#16264a", a=0.9)
        planet_icon(c, 0, 20, 170, "earth", t)
        text(c, "THE PLANET", 0, -250, 60, "#ffffff")
        text(c, "50%", 0, 270, 60, "#ffd34d")
        # tiny person standing on top
        person(c, 0, -150, POSE_STAND, "you", "happy", t, 0.22, shadow_h=None)


def s_change(c, t):
    grid_board(c, t, "#120f2a", "#241b4a")
    # number rolling between worlds
    vals = ["0.5 m", "3 m", "1.3 m", "0.2 m", "8 m", "40 m", "∞"]
    k = int(max(0, (t - 24.4)) * 5) % len(vals)
    v = vals[k] if t > 24.4 else "0.5 m"
    planet_keys = ["earth", "moon", "mars", "jupiter", "pluto", "enceladus", "bennu"]
    with xf(c, W / 2, 420):
        planet_icon(c, -360, 0, 110, planet_keys[k] if t > 24.4 else "earth", t)
        text(c, v, 140, 50, 170, "#ffd34d", shadow=True)
    words = [("STRANGE", 25.9, "#7fd3ff"), ("FUNNY", 26.4, "#ffd34d"), ("TERRIFYING", 27.6, "#ff5a3c")]
    for i, (w, st, col) in enumerate(words):
        pop_pill(c, t, st, 460 + i * 500, 800, w, 56, col, "#1b1b2f" if i < 2 else "#ffffff")


# =============================================================== 2. THE RULE
def s_rule(c, t):
    grid_board(c, t)
    gy = 820
    s = 0.95
    ppm = ppm_for(s)
    rrect(c, 360, gy, 1200, 30, 10, "#3d5a8a")
    title_a = clamp(at(t, 28.6, 0.4))
    text(c, "THE JUMP RULE", W / 2, 130, 84, "#ffffff", a=title_a)
    # push at 32.6, take-off 33.4
    T = 0.62
    tt = t
    if t > 36.5:
        tt = 33.4 + ((t - 36.5) % 2.6)  # keep demonstrating
    pose, hf, sq = jump_state(tt, 33.4, T)
    lift = hf * 0.5 * ppm
    person(c, 960, gy, pose, "you", "happy", t, s, lift=lift, shadow_h=lift, squash=sq)
    if 32.4 < t < 33.6:
        a = window(t, 32.4, 33.6, 0.15)
        arrow(c, 960, gy - 20, 960, gy + 120, "#ff9a3c", 22, a)
        text(c, "PUSH", 1060, gy + 90, 48, "#ff9a3c", a=a, align="left")
    if t > 33.6:
        a = clamp((t - 33.6) / 0.3)
        arrow(c, 1250, 700, 1250, 330, "#4cd6ff", 26, a)
        text(c, "LAUNCH", 1290, 520, 52, "#4cd6ff", align="left", a=a)
        if t > 37.2:
            pop_pill(c, t, 37.2, 1400, 600, "3 m/s", 56, "#4cd6ff", "#0d1220")
    if t > 38.3:
        a = clamp((t - 38.3) / 0.3)
        arrow(c, 660, 330, 660, 700, "#ff5a3c", 26, a)
        text(c, "GRAVITY", 620, 520, 52, "#ff5a3c", align="right", a=a)
    if t > 44.3:
        k = back_out(at(t, 44.3, 0.5))
        with xf(c, W / 2, 260, s=0.5 + 0.5 * k, alpha=clamp(k)):
            card(c, -560, -70, 1120, 120, "#0d1220", a=0.85)
            text(c, "WEAKER GRAVITY  →  HIGHER JUMP", 0, 18, 58, "#ffd34d")


def s_three(c, t):
    grid_board(c, t)
    keys = [("earth", 46.9), ("moon", 47.3), ("pluto", 47.7)]
    for i, (key, st) in enumerate(keys):
        x0 = 120 + i * 580
        k = back_out(at(t, st, 0.45))
        if k <= 0:
            continue
        with xf(c, x0 + 270, 560, s=0.5 + 0.5 * k, alpha=clamp(k)):
            c.save()
            c.clipRect(skia.Rect(-270, -420, 270, 420))
            c.translate(-W / 2, -540)
            world_bg(c, key, t, gy=860)
            c.restore()
            rrect(c, -270, -420, 540, 840, 30, "#ffffff", stroke=8)
            g = WORLDS[key]["g"]
            s = 0.5
            ppm = ppm_for(s)
            hm = jump_height(g)
            T = min(air_time(g), 3.0)
            hpx = min(hm * ppm, 560)
            jumper(c, 0, 320, t, 48.2, hpx, T, s=s, repeat=3.4)
            text(c, WORLDS[key]["name"], 0, -350, 46, "#ffffff", shadow=True)
    pop_pill(c, t, 46.6, W / 2, 80, "SAME PUSH", 46)
    pop_pill(c, t, 48.1, W / 2, 1000 - 40, "COMPLETELY DIFFERENT RESULT", 44, "#ff5a3c", "#ffffff")


def s_fly(c, t):
    # warp through space toward the Moon
    c.drawRect(skia.Rect(0, 0, W, H), P("#03040a"))
    sp = 1 + 3 * smooth((t - 52.0) / 3)
    for i, (sx, sy, sr, ph) in enumerate(STARS_W):
        z = ((ph + t * 0.25 * sp) % 1.0)
        x = W / 2 + (sx - W / 2) / (1.2 - z)
        y = H / 2 + (sy - H / 2) / (1.2 - z)
        x2 = W / 2 + (sx - W / 2) / (1.2 - max(0, z - 0.03 * sp))
        y2 = H / 2 + (sy - H / 2) / (1.2 - max(0, z - 0.03 * sp))
        line(c, x2, y2, x, y, "#ffffff", sr, z)
    r = lerp(30, 300, smooth((t - 52.5) / 3.3))
    planet_icon(c, W / 2, H / 2, r, "moon", t)
    pop_pill(c, t, 51.5, W / 2, 140, "STOP #1", 50)
    big_text(c, t, 53.8, "ALMOST FLY?", W / 2, 900, 100, "#ffd34d")


import random as _r  # noqa: E402

_rs = _r.Random(9)
STARS_W = [(_rs.uniform(0, W), _rs.uniform(0, H), _rs.uniform(1.5, 3.5), _rs.uniform(0, 1)) for _ in range(220)]


# =============================================================== 3. MOON
def s_moon_intro(c, t):
    push(c, t, 55.6, 63.3, 1.0, 1.08, cy=640)
    world_bg(c, "moon", t)
    s = 0.8
    person(c, 960, GY, POSE_STAND, "you", "happy", t, s, look=(0.3, -0.4))
    title_card(c, t, 55.8, "moon", "1/6 OF EARTH'S GRAVITY", y=360)
    gravity_badge(c, "moon", t, 58.4)
    if t > 61.8:
        a = clamp((t - 61.8) / 0.3)
        arrow(c, 1250, 300, 1250, 360, "#ff5a3c", 12, a, head=22)
        text(c, "tiny pull", 1290, 345, 36, "#ff5a3c", "Bold", align="left", a=a)
        arrow(c, 1150, 700, 1150, 320, "#4cd6ff", 22, a)


def s_moon_hoop(c, t):
    s = 0.6
    ppm = ppm_for(s)
    push(c, t, 63.3, 70.7, 1.0, 1.05, cy=600)
    world_bg(c, "moon", t)
    hoop(c, 1150, GY, ppm)
    ruler(c, 600, GY, ppm, 3.5, 0.5, label_every=2, a=clamp((t - 63.6) / 0.3))
    T = air_time(0.165)
    hpx = 2.8 * ppm
    jumper(c, 930, GY, t, 64.5, hpx, T, s=s, expr="happy", expr_air="laugh")
    if t > 65.2:
        height_tag(c, 1450, GY, GY - 3.0 * ppm, "3 m", "≈ 10 FEET" if t > 66.6 else None,
                   a=clamp((t - 65.2) / 0.3))
    if t > 68.1:
        pop_pill(c, t, 68.5, 1100, 160, "TOUCH THE RIM!", 46)
        if 68.0 < t < 69.0:
            for k in range(6):
                sparkle(c, 1080 + 60 * math.cos(k), GY - 3.05 * ppm + 40 * math.sin(k * 2), 16, "#ffd34d")


def s_hang(c, t):
    c.drawRect(skia.Rect(0, 0, W, H), P("#000000"))
    for side, key, t0 in ((0, "earth", 73.0), (1, "moon", 74.9)):
        x0 = side * W / 2
        c.save()
        c.clipRect(skia.Rect(x0, 0, x0 + W / 2, H))
        c.translate(x0 - W / 4, 0)
        world_bg(c, key, t)
        if key == "earth":
            earth_props(c, t)
        s = 0.6
        ppm = ppm_for(s)
        g = WORLDS[key]["g"]
        T = air_time(g)
        hpx = jump_height(g) * ppm
        tt = t
        if key == "earth" and t > t0 + T + 0.6:
            tt = t0 + ((t - t0) % (T + 0.9))
        _, _, lift = jumper(c, W / 2, GY, tt, t0, hpx, T, s=s, expr="happy", expr_air="laugh")
        c.restore()
        # stopwatch
        if key == "earth":
            secs = clamp((t - t0) / T) * T if t > t0 else 0
            secs = min(secs, 0.6)
        else:
            secs = clamp((t - t0) / T) * T if t > t0 else 0
        stopwatch(c, x0 + W / 4 + 330, 300, 90, secs, WORLDS[key]["name"], a=clamp((t - 71.5) / 0.4))
    line(c, W / 2, 0, W / 2, H, "#ffffff", 8)
    if t > 77.6:
        big_text(c, t, 77.6, "4 FULL SECONDS", W * 0.75, 140, 76, "#ffd34d")


def s_float(c, t):
    s = 0.75
    push(c, t, 78.6, 83.0, 1.05, 1.15, cy=560)
    world_bg(c, "moon", t)
    lift = 300 + 18 * math.sin(t * 1.3)
    tilt = (t - 78.6) * 70 if t > 80.3 else 0
    tilt = min(tilt, 360) if t < 81.6 else 360
    person(c, 960, GY, POSE_FLOAT, "you", "shock" if t > 81.1 else "happy", t, s, lift=lift, shadow_h=lift,
           tilt=tilt % 360, look=(math.sin(t * 1.5), -0.3))
    if t > 81.2:
        bubble(c, 1260, 330, "WHY AM I STILL UP HERE?", 40, a=clamp((t - 81.2) / 0.3), tail=(-1, 1))


def s_apollo(c, t):
    s = 0.62
    push(c, t, 82.9, 90.6, 1.0, 1.06, cy=620)
    world_bg(c, "moon", t)
    # flag
    rrect(c, 1450, GY - 330, 8, 330, 3, "#d9dee6")
    for k in range(6):
        c.drawRect(skia.Rect(1458, GY - 330 + k * 22, 1640, GY - 319 + k * 22), P("#d94040" if k % 2 == 0 else "#ffffff"))
    c.drawRect(skia.Rect(1458, GY - 330, 1530, GY - 264), P("#2a4a9a"))
    # bunny-hopping astronaut
    period = 1.6
    ph = ((t - 83.0) % period) / period
    x = 300 + ((t - 83.0) * 140) % 1300
    lift = 4 * ph * (1 - ph) * 120
    pose = POSE_AIR if 0.1 < ph < 0.9 else POSE_CROUCH
    person(c, x, GY, mix_pose(POSE_FLOAT, pose, 0.4), "astro", "laugh", t, s, lift=lift, shadow_h=lift,
           helmet=True, tilt=8)
    # old-film overlay
    fa = 0.3
    c.drawRect(skia.Rect(0, 0, W, H), P("#c8b48a", a=0.12))
    for k in range(3):
        x = (k * 613 + int(t * 24) * 97) % W
        line(c, x, 0, x + 6, H, "#ffffff", 2, fa * 0.4)
    c.drawRect(skia.Rect(0, 0, W, 70), P("#000000"))
    c.drawRect(skia.Rect(0, H - 70, W, H), P("#000000"))
    pop_pill(c, t, 83.6, 330, 150, "APOLLO • 1969–1972", 40, "#ffffff", "#1b1b2f")
    if t > 88.4:
        pop_pill(c, t, 88.4, W / 2, 260, "…FIGHTING A PROBLEM", 44, "#ff5a3c", "#ffffff")


def s_teaser(c, t):
    c.drawRect(skia.Rect(0, 0, W, H), P("#03040a"))
    for (sx, sy, sr, ph) in STARS_W:
        c.drawCircle(sx, sy, sr * 0.7, P("#ffffff", a=0.5 + 0.3 * math.sin(t * 2 + ph * 6)))
    planet_icon(c, 520, 560, 260 * (1 - 0.25 * smooth((t - 90.7) / 3)), "moon", t)
    k = back_out(at(t, 93.1, 0.6))
    with xf(c, 1400, 560, s=k, rot=t * 10):
        planet_icon(c, 0, 0, 70, "bennu", t)
    if t > 94.4:
        a = clamp((t - 94.4) / 0.3)
        with xf(c, 1400, 360, s=0.8 + 0.2 * math.sin(t * 6), alpha=a):
            c.drawPath(poly([(0, -70), (75, 60), (-75, 60)]), P("#ffd34d"))
            text(c, "!", 0, 48, 100, "#1b1b2f")
    pop_pill(c, t, 91.6, 520, 900, "ONLY THE BEGINNING", 42)
    pop_pill(c, t, 95.3, 1400, 900, "MUCH MORE DANGEROUS", 42, "#ff5a3c", "#ffffff")


# =============================================================== 4. MARS / MERCURY
def s_closer(c, t):
    grid_board(c, t)
    keys = ["mercury", "venus", "earth", "mars"]
    for i, key in enumerate(keys):
        k = back_out(at(t, 97.3 + i * 0.25, 0.45))
        planet_icon(c, 330 + i * 420, 540, 100 * k, key, t)
        text(c, WORLDS[key]["name"], 330 + i * 420, 720, 44, "#ffffff", a=clamp(k))
    if t > 98.7:
        pop_pill(c, t, 98.7, W / 2, 200, "CLOSER TO HOME", 50)


def s_mars(c, t):
    s = 0.7
    ppm = ppm_for(s)
    push(c, t, 99.5, 112.6, 1.0, 1.07, cy=620)
    world_bg(c, "mars", t)
    title_card(c, t, 99.9, "mars", "38% OF EARTH'S GRAVITY", y=330)
    gravity_badge(c, "mars", t, 102.4)
    table_prop(c, 1000, GY, ppm, a=clamp((t - 107.4) / 0.3))
    T = air_time(0.38)
    hpx = 1.2 * ppm
    # jump forward over the table
    t0 = 104.2
    x = 760
    if t > t0:
        x = lerp(760, 1240, clamp((t - t0) / T))
    if t > 107.6:
        t0b = 107.9
        x = lerp(760, 1240, clamp((t - t0b) / T))
        _, _, lift = jumper(c, x, GY, t, t0b, hpx, T, s=s, expr="happy", expr_air="laugh")
    else:
        _, _, lift = jumper(c, x, GY, t, t0, hpx, T, s=s, expr="happy", expr_air="laugh")
    if t > 105.0:
        height_tag(c, 1500, GY, GY - 1.33 * ppm, "1.3 m", "≈ 4 FEET" if t > 106.2 else None,
                   a=clamp((t - 105.0) / 0.3))
    if t > 108.6:
        secs = clamp((t - 107.9) / T) * T
        stopwatch(c, 360, 430, 80, secs, "AIR TIME", a=clamp((t - 108.6) / 0.3))
    if t > 110.7:
        pop_pill(c, t, 110.9, 360, 680, "3× LONGER THAN EARTH", 36)


def s_mercury(c, t):
    c.drawRect(skia.Rect(0, 0, W, H), P("#000000"))
    for side, key in ((0, "mercury"), (1, "mars")):
        x0 = side * W / 2
        c.save()
        c.clipRect(skia.Rect(x0, 0, x0 + W / 2, H))
        c.translate(x0 - W / 4, 0)
        world_bg(c, key, t)
        s = 0.62
        ppm = ppm_for(s)
        T = air_time(0.38)
        jumper(c, W / 2, GY, t, 116.8 + side * 0.1, 1.2 * ppm, T, s=s, repeat=2.4, helmet=True, who="astro")
        c.restore()
        name = WORLDS[key]["name"]
        k = back_out(at(t, 112.7 if side == 0 else 116.0, 0.45))
        with xf(c, x0 + W / 4, 130, s=0.5 + 0.5 * k, alpha=clamp(k)):
            text(c, name, 0, 30, 80, "#ffffff", shadow=True)
        if t > 118.6:
            pop_pill(c, t, 118.6, x0 + W / 4, 260, "≈ 4 FEET", 46)
        lab, col, st = (("430 °C BURNING", "#ff7a2a", 120.6) if side == 0 else ("−60 °C FREEZING", "#7fd3ff", 121.4))
        pop_pill(c, t, st, x0 + W / 4, 980 - 40, lab, 42, col, "#0d1220")
    line(c, W / 2, 0, W / 2, H, "#ffffff", 8)
    if t > 122.9:
        big_text(c, t, 122.9, "SAME JUMP", W / 2, 540, 100, "#ffd34d")


def s_suit(c, t):
    s = 0.75
    ppm = ppm_for(s)
    push(c, t, 123.8, 138.0, 1.0, 1.08, cy=620)
    world_bg(c, "mars", t)
    tshirt = t < 127.6
    who = "you" if tshirt else "astro"
    hel = None if tshirt else True
    if t < 132.4:
        person(c, 960, GY, POSE_STAND, who, "happy" if tshirt else "worried", t, s, helmet=hel,
               sweat=0.0 if tshirt else 0.6)
        if tshirt and t > 126.5:
            cross_mark(c, 1200, 450, 90, a=clamp((t - 126.6) / 0.2))
            pop_pill(c, t, 126.9, 1200, 600, "T-SHIRT", 42, "#ffffff", "#1b1b2f")
        if not tshirt:
            pop_pill(c, t, 128.3, 1300, 360, "PRESSURIZED SUIT", 42)
            if t > 129.6:
                k = back_out(at(t, 129.6, 0.45))
                with xf(c, 560, 560, s=k):
                    card(c, -190, -110, 380, 220, "#0d1220", a=0.85)
                    text(c, "SUIT", -90, -30, 44, "#ffffff")
                    text(c, "YOU", 90, -30, 44, "#ffffff")
                    text(c, ">", 0, -30, 60, "#ffd34d")
                    text(c, "HEAVIER THAN YOU", 0, 60, 30, "#ffd34d", "Bold")
            if t > 131.0:
                for k in range(3):
                    a = window(t, 131.0 + k * 0.2, 132.4)
                    text(c, "✕", 800 + k * 160, 500 + 40 * k, 50, "#ff5a3c", a=a)
    else:
        T = air_time(0.38)
        ghost_h = 1.2 * ppm
        if t > 133.6:
            ka = clamp((t - 133.6) / 0.3)
            with xf(c, alpha=0.35 * ka):
                person(c, 720, GY, POSE_AIR, "astro", "happy", t, s, lift=ghost_h, shadow_h=None, helmet=True)
            pop_pill(c, t, 134.0, 720, 200, "THE MATH SAYS", 38, "#ffffff", "#1b1b2f")
        jumper(c, 1200, GY, t, 132.9, 0.55 * ppm, T * 0.7, who="astro", s=s, helmet=True, repeat=2.2,
               expr="worried")
        pop_pill(c, t, 132.4, 1200, 200, "REAL JUMP", 38, "#ff5a3c", "#ffffff")
        if t > 136.6:
            pop_pill(c, t, 136.8, W / 2, 940, "YOUR OWN SUIT IS STOPPING YOU", 42)


def s_gift(c, t):
    grid_board(c, t)
    for i, (key, st) in enumerate((("mars", 138.7), ("mercury", 139.1))):
        k = back_out(at(t, st, 0.45))
        x = 480 + i * 360
        planet_icon(c, x, 470, 110 * k, key, t)
        if t > 140.0:
            with xf(c, x, 690, s=back_out(at(t, 140.0 + i * 0.1, 0.4))):
                rrect(c, -60, -40, 120, 90, 8, "#4cd68a")
                c.drawRect(skia.Rect(-12, -40, 12, 50), P("#ffd34d"))
                rrect(c, -70, -60, 140, 30, 6, "#3ab874")
    if t > 140.4:
        k = back_out(at(t, 140.4, 0.5))
        planet_icon(c, 1440, 540, 170 * k, "venus", t)
        if t > 141.5:
            with xf(c, 1440, 300, s=back_out(at(t, 141.5, 0.4))):
                text(c, "?!", 0, 40, 120, "#ff5a3c", shadow=True)
        pop_pill(c, t, 141.6, 1440, 800, "A TRICK", 46, "#ff5a3c", "#ffffff")
    pop_pill(c, t, 139.9, 660, 840, "A GIFT", 46, "#4cd68a", "#0d1220")


# =============================================================== 5. VENUS
def s_venus(c, t):
    s = 0.85
    ppm = ppm_for(s)
    push(c, t, 141.8, 155.4, 1.0, 1.08, cy=640)
    world_bg(c, "venus", t)
    title_card(c, t, 142.0, "venus", "90% OF EARTH'S GRAVITY", y=330)
    gravity_badge(c, "venus", t, 144.6)
    T = air_time(0.9)
    expr = "happy" if t < 151.7 else "worried"
    jumper(c, 960, GY, t, 147.0, 0.55 * ppm, T, s=s, repeat=2.2, expr=expr, helmet=None)
    if t > 147.4:
        height_tag(c, 1300, GY, GY - 0.55 * ppm, "55 cm", "JUST A BIT HIGHER" if t > 148.5 else None,
                   a=clamp((t - 147.4) / 0.3))
    # heat shimmer + warning icons
    if t > 151.9:
        for k, (x, lab) in enumerate(((400, "🔥"), (1520, "⚠"))):
            pass
        pop_pill(c, t, 152.0, 450, 260, "GRAVITY = SMALLEST PROBLEM", 40, "#ff5a3c", "#ffffff")
        c.drawRect(skia.Rect(0, 0, W, H), P("#ff6a00", a=0.12 * clamp((t - 152) / 1.5)))


def s_venus_danger(c, t):
    grid_board(c, t, "#2a1408", "#4a220c")
    # panel 1: heat, melting lead
    k1 = back_out(at(t, 155.5, 0.5))
    with xf(c, 360, 520, s=0.5 + 0.5 * k1, alpha=clamp(k1)):
        card(c, -280, -330, 560, 660, "#1a0c05", a=0.85)
        # thermometer
        rrect(c, -40, -240, 80, 360, 40, "#ffffff")
        lvl = smooth((t - 156.2) / 1.2)
        rrect(c, -22, 100 - 300 * lvl, 44, 300 * lvl + 10, 22, "#ff3b1f")
        c.drawCircle(0, 160, 70, P("#ffffff"))
        c.drawCircle(0, 160, 54, P("#ff3b1f"))
        text(c, "465 °C", 0, 280, 64, "#ffd34d")
    # lead bar melting
    k2 = back_out(at(t, 156.8, 0.5))
    with xf(c, 360 + 330, 650, s=k2, alpha=clamp(k2)):
        m = smooth((t - 157.1) / 1.6)
        rrect(c, -80, -40 + 40 * m, 160, 80 - 40 * m, 10, "#9aa3b3")
        c.drawOval(skia.Rect(-80 - 60 * m, 30, 80 + 60 * m, 50), P("#9aa3b3"))
        text(c, "LEAD", 0, 110, 36, "#ffffff")
    # panel 2: pressure x90 + ocean
    k3 = back_out(at(t, 157.6, 0.5))
    with xf(c, 1340, 520, s=0.5 + 0.5 * k3, alpha=clamp(k3)):
        card(c, -440, -330, 880, 660, "#071a33", a=0.9)
        text(c, "PRESSURE", 0, -250, 52, "#ffffff")
        n = int(counter(t, 158.4, 1.0, 1, 90))
        text(c, f"{n}×", 0, -120, 130, "#ffd34d")
        if t > 160.1:
            dk = smooth((t - 160.1) / 2.0)
            fill_shader(c, skia.Rect(-420, -30, 420, 310), linear(0, -30, 0, 310, ["#2a7fd0", "#041029"]))
            yy = lerp(-10, 230, dk)
            c.save()
            c.translate(0, yy)
            c.drawCircle(0, 0, 26, P("#ffd34d"))
            rrect(c, -20, 20, 40, 50, 12, "#ffd34d")
            c.restore()
            line(c, 300, -20, 300, 300, "#ffffff", 4)
            text(c, "1 km", 330, 160, 40, "#ffffff", align="left")
            text(c, "DEEP IN THE OCEAN", 0, 290, 34, "#ffffff", "Bold", a=dk)


def s_thought(c, t):
    grid_board(c, t)
    s = 0.95
    person(c, 600, 900, POSE_STAND, "you", "worried" if t < 168 else "happy", t, s, look=(0.6, -0.6))
    for k, (dx, dy, r) in enumerate(((120, -420, 16), (170, -480, 24))):
        c.drawCircle(600 + dx, 900 + dy, r, P("#ffffff", a=clamp((t - 164.6 - k * 0.15) / 0.2)))
    k = back_out(at(t, 164.9, 0.5))
    with xf(c, 1150, 330, s=k, alpha=clamp(k)):
        c.drawOval(skia.Rect(-480, -220, 480, 220), P("#ffffff"))
        c.save()
        clip = skia.Path()
        clip.addOval(skia.Rect(-450, -195, 450, 195))
        c.clipPath(clip, doAntiAlias=True)
        c.translate(-W / 2 * 0.5, -540 * 0.5)
        c.scale(0.5, 0.5)
        world_bg(c, "venus", t)
        jumper(c, W / 2, GY, t, 165.0, 90, air_time(0.9), s=0.9, repeat=2.0)
        c.restore()
    pop_pill(c, t, 164.9, 1150, 640, "THOUGHT EXPERIMENT", 46)
    if t > 166.3:
        pop_pill(c, t, 166.4, 1150, 760, "YOU WOULDN'T SURVIVE", 40, "#ff5a3c", "#ffffff", end=168.6)
    if t > 169.4:
        pop_pill(c, t, 169.4, 1150, 760, "BUT IT TEACHES US…", 40, "#4cd68a", "#0d1220")


def s_mismatch(c, t):
    grid_board(c, t)
    text(c, "GRAVITY  vs  DANGER", W / 2, 150, 72, "#ffffff", a=clamp(at(t, 170.8, 0.4)))
    rows = [("mercury", 0.38, 0.75), ("mars", 0.38, 0.55), ("venus", 0.90, 1.0), ("earth", 1.0, 0.05)]
    for i, (key, g, d) in enumerate(rows):
        y = 300 + i * 165
        k = ease_out(at(t, 171.4 + i * 0.3, 0.8))
        planet_icon(c, 200, y + 30, 50, key, t, a=clamp(k * 3))
        text(c, WORLDS[key]["name"], 290, y + 46, 40, "#ffffff", align="left", a=clamp(k * 3))
        rrect(c, 640, y, 520 * g / 1.0 * k + 4, 36, 10, "#4cd6ff")
        rrect(c, 640, y + 46, 520 * d * k + 4, 36, 10, "#ff5a3c")
    text(c, "■ GRAVITY", 640, 990, 34, "#4cd6ff", align="left")
    text(c, "■ DANGER", 960, 990, 34, "#ff5a3c", align="left")
    if t > 173.3:
        pop_pill(c, t, 173.4, 1530, 450, "NO MATCH!", 50, "#ffd34d")
    if t > 176.2:
        big_text(c, t, 176.2, "GRAVITY = DANGER?", 1530, 700, 66, "#ff5a3c")


# =============================================================== 6. GIANTS
def s_jupiter_big(c, t):
    c.drawRect(skia.Rect(0, 0, W, H), P("#03040a"))
    for (sx, sy, sr, ph) in STARS_W:
        c.drawCircle(sx, sy, sr * 0.7, P("#ffffff", a=0.5))
    z = lerp(1.0, 1.25, smooth((t - 178.2) / 5))
    planet_icon(c, W / 2, 560, 330 * z, "jupiter", t)
    # tiny Earth for scale
    planet_icon(c, W / 2 + 470 * z, 260, 30, "earth", t)
    text(c, "EARTH", W / 2 + 470 * z, 330, 30, "#ffffff", "Bold")
    title_card(c, t, 179.7, "jupiter", "THE BIGGEST PLANET", y=180)
    if t > 182.3:
        pop_pill(c, t, 182.3, W / 2, 960, "NO SOLID GROUND", 50, "#ff5a3c", "#ffffff")


def s_jupiter(c, t):
    s = 0.95
    ppm = ppm_for(s)
    push(c, t, 183.7, 201.3, 1.0, 1.1, cy=660)
    world_bg(c, "jupiter", t)
    k = back_out(at(t, 184.8, 0.6))
    gy = GY + (1 - k) * 400
    stair(c, 1480, gy, ppm, 3, a=clamp((t - 196.8) / 0.3))
    expr = "worried"
    if t < 198.1:
        pose = POSE_STRAIN if t > 189.5 else POSE_STAND
        person(c, 860, gy, pose, "you", expr, t, s, sweat=clamp((t - 189.5) / 1.0))
    else:
        T = air_time(2.53)
        jumper(c, 860, gy, t, 199.6, 0.2 * ppm, T, s=s, repeat=1.6, expr="angry")
    gravity_badge(c, "jupiter", t, 189.4)
    if t > 189.5:
        for k2 in range(3):
            x = 700 + k2 * 160
            yy = 140 + 25 * ((t * 1.5 + k2 * 0.3) % 1.0)
            arrow(c, x, yy, x, yy + 140, "#ff5a3c", 16, clamp((t - 189.5) / 0.4))
    if t > 192.9:
        height_tag(c, 1150, gy, gy - 0.2 * ppm, "20 cm", "≈ 8 INCHES" if t > 194.6 else None,
                   a=clamp((t - 192.9) / 0.3), side=1)
    if t > 197.1:
        pop_pill(c, t, 197.4, 1460, 360, "ONE STAIR STEP", 44)


def s_bodies(c, t):
    s = 0.85
    push(c, t, 201.3, 205.7, 1.0, 1.1, cy=600)
    world_bg(c, "jupiter", t)
    hip = person(c, 960, GY, POSE_STRAIN, "you", "dry", t, s, sweat=1.0)
    # 1.5 extra bodies piled on the back
    for k in range(2):
        a = clamp((t - (203.3 + k * 0.45)) / 0.3)
        if a <= 0:
            continue
        sc = s * (1.0 if k == 0 else 0.6)
        with xf(c, alpha=0.55 * a):
            person(c, 960 + (k * 20), hip - 250 * s - k * 170 * s, POSE_FLOAT, "you", "sleep", t, sc,
                   shadow_h=None, tilt=90 - k * 20)
    pop_pill(c, t, 203.4, 1450, 300, "+1.5 BODIES", 54, "#ff5a3c", "#ffffff")


def s_saturn(c, t):
    s = 0.85
    ppm = ppm_for(s)
    push(c, t, 205.6, 217.3, 1.0, 1.06, cy=640)
    world_bg(c, "saturn", t)
    title_card(c, t, 205.8, "saturn", "MUCH GENTLER", y=330)
    if t > 209.5:
        pop_pill(c, t, 209.7, 450, 520, "VERY LIGHT FOR ITS SIZE", 38)
    gravity_badge(c, "saturn", t, 211.3)
    T = air_time(1.07)
    jumper(c, 1000, GY, t, 214.4, 0.47 * ppm, T, s=s, repeat=2.0)
    if t > 215.8:
        height_tag(c, 1300, GY, GY - 0.47 * ppm, "47 cm", a=clamp((t - 215.8) / 0.3))


def s_like_home(c, t):
    c.drawRect(skia.Rect(0, 0, W, H), P("#000000"))
    for side, key in ((0, "earth"), (1, "saturn")):
        x0 = side * W / 2
        c.save()
        c.clipRect(skia.Rect(x0, 0, x0 + W / 2, H))
        c.translate(x0 - W / 4, 0)
        world_bg(c, key, t)
        if key == "earth":
            earth_props(c, t)
        s = 0.8
        ppm = ppm_for(s)
        g = WORLDS[key]["g"]
        jumper(c, W / 2, GY, t, 218.4, jump_height(g) * ppm, air_time(g), s=s, repeat=1.5)
        c.restore()
        text(c, WORLDS[key]["name"], x0 + W / 4, 150, 80, "#ffffff", shadow=True)
        pop_pill(c, t, 219.0 + side * 0.2, x0 + W / 4, 260, "46 cm" if side == 0 else "47 cm", 46)
    line(c, W / 2, 0, W / 2, H, "#ffffff", 8)
    if t > 220.6:
        big_text(c, t, 220.6, "JUST LIKE HOME", W / 2, 560, 96, "#ffd34d")


def s_ice_giants(c, t):
    c.drawRect(skia.Rect(0, 0, W, H), P("#000000"))
    for side, key, hm, st in ((0, "uranus", 0.56, 226.1), (1, "neptune", 0.44, 230.4)):
        x0 = side * W / 2
        c.save()
        c.clipRect(skia.Rect(x0, 0, x0 + W / 2, H))
        c.translate(x0 - W / 4, 0)
        world_bg(c, key, t)
        s = 0.8
        ppm = ppm_for(s)
        g = WORLDS[key]["g"]
        jumper(c, W / 2, GY, t, st + 0.9, hm * ppm, air_time(g), s=s, repeat=2.0,
               expr="happy" if t < 233.4 else "worried")
        if t > 233.4:
            for k in range(6):
                sparkle(c, (k * 150 + t * 200) % W, 200 + k * 90, 10, "#ffffff", 0.7)
        c.restore()
        k = back_out(at(t, 223.4 if side == 0 else 224.1, 0.4))
        with xf(c, x0 + W / 4, 150, s=0.5 + 0.5 * k, alpha=clamp(k)):
            text(c, WORLDS[key]["name"], 0, 30, 80, "#ffffff", shadow=True)
        if t > st + 1.2:
            pop_pill(c, t, st + 1.2, x0 + W / 4, 270, f"{int(hm * 100)} cm", 50)
    line(c, W / 2, 0, W / 2, H, "#ffffff", 8)
    if t > 233.3:
        pop_pill(c, t, 233.4, W / 2, 960, "FREEZING • WINDY", 44, "#7fd3ff", "#0d1220")


def s_lineup(c, t):
    grid_board(c, t)
    big = [("jupiter", 120), ("saturn", 100), ("uranus", 70), ("neptune", 70)]
    small = [("pluto", 34), ("enceladus", 26), ("ceres", 22), ("bennu", 12)]
    for i, (key, r) in enumerate(big):
        x = 230 + i * 230
        a = 1.0 - 0.6 * clamp((t - 239.8) / 0.6)
        planet_icon(c, x, 470, r * 0.9, key, t, a=a)
    if t > 237.9:
        pop_pill(c, t, 237.9, 590, 720, "NOT THE EXTREMES", 40, "#ffffff", "#1b1b2f")
    for i, (key, r) in enumerate(small):
        k = back_out(at(t, 241.5 + i * 0.25, 0.45))
        x = 1180 + i * 200
        planet_icon(c, x, 470, r * 1.6 * k, key, t)
        text(c, WORLDS[key]["name"], x, 600, 28, "#ffffff", "Bold", a=clamp(k))
    if t > 239.9:
        arrow(c, 1000, 470, 1080, 470, "#ffd34d", 12, clamp((t - 239.9) / 0.3))
    if t > 244.1:
        big_text(c, t, 244.1, "NOT A GAME ANYMORE", 1480, 800, 62, "#ff5a3c")


# =============================================================== 7. SMALL WORLDS
def s_pluto(c, t):
    s = 0.36
    ppm = ppm_for(s)
    push(c, t, 245.6, 261.0, 1.0, 1.04, cy=560)
    world_bg(c, "pluto", t)
    house(c, 1320, GY, ppm, 2)
    ruler(c, 330, GY, ppm, 8, 1, label_every=2, a=clamp((t - 249.6) / 0.3))
    title_card(c, t, 245.9, "pluto", "6% OF EARTH'S GRAVITY", y=320)
    gravity_badge(c, "pluto", t, 247.0)
    T = air_time(0.063)  # ~9.7 s, real time
    t0 = 249.3
    hpx = 7.3 * ppm
    _, ytop, lift = jumper(c, 900, GY, t, t0, hpx, T, s=s, expr="happy", expr_air="laugh")
    if t > 250.2:
        height_tag(c, 720, GY, GY - 8 * ppm, "8 m", "HIGHER THAN A ROOF" if t > 251.8 else None,
                   a=clamp((t - 250.2) / 0.3), side=-1)
    if t > 257.6:
        # feather drifting beside the jumper
        fx = 1060 + 30 * math.sin(t * 2)
        fy = GY - lift - 60
        with xf(c, fx, fy, rot=20 * math.sin(t * 2)):
            c.drawOval(skia.Rect(-12, -50, 12, 50), P("#ffffff", a=0.9))
            line(c, 0, -55, 0, 60, "#c9ced8", 3)
    if t > 259.0:
        down_start = t0 + T / 2
        secs = max(0.0, t - down_start)
        stopwatch(c, 300, 300, 80, min(secs, T / 2), "FALL TIME", a=clamp((t - 259.0) / 0.3))


def s_enceladus(c, t):
    s = 0.3
    ppm = ppm_for(s)
    T_up = 4.0  # compressed rise (the real one would take ~26 s)
    t0 = 269.4
    hm = 40.0
    if t < t0:
        rise = 0.0
    else:
        u = clamp((t - t0) / T_up)
        rise = hm * (1 - (1 - u) ** 2)
    lift = rise * ppm
    cam_up = max(0.0, lift - 300)
    c.save()
    zz = 1.0
    c.translate(0, cam_up)
    world_bg(c, "enceladus", t, gy=GY)
    tower(c, 1400, GY, ppm, 15, lit=1.0, w_m=7)
    pose = POSE_STAND if t < t0 - 0.35 else (mix_pose(POSE_STAND, POSE_CROUCH, (t - t0 + 0.35) / 0.35) if t < t0 else
                                             mix_pose(POSE_AIR, POSE_FLOAT, clamp((t - t0 - 1) / 2)))
    person(c, 900, GY, pose, "astro", "laugh" if t > t0 else "happy", t, s, lift=lift, shadow_h=lift, helmet=True)
    c.restore()
    if t > 270.5:
        big_text(c, t, 270.5, "40+ METERS", 560, 300, 90, "#ffd34d")
    if t > 272.3:
        pop_pill(c, t, 272.3, 560, 420, "= A 15-STORY BUILDING", 42)
    _ = zz
    title_card(c, t, 262.6, "enceladus", "SATURN'S ICY MOON", y=330)
    gravity_badge(c, "enceladus", t, 267.0)
    if 264.7 < t < 268.8:
        pop_pill(c, t, 264.9, W / 2, 940, "WATER FOUNTAINS INTO SPACE", 42, "#7fd3ff", "#0d1220", end=268.8)


def s_cracks(c, t):
    # looking down from 40 m: icy plain with blue "tiger stripe" cracks
    k = smooth((t - 273.6) / 3.4)
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#0e1426", "#03050c"]))
    for (sx, sy, sr, ph) in STARS_W[:120]:
        c.drawCircle(sx, sy * 0.4, sr * 0.6, P("#ffffff", a=0.5))
    hz = 330
    fill_shader(c, skia.Rect(0, hz, W, H), linear(0, hz, 0, H, ["#c7dcf2", "#f2f8ff"]))
    for i in range(7):
        x = 200 + i * 260
        p = skia.Path()
        p.moveTo(W / 2 + (x - W / 2) * 0.08, hz)
        p.lineTo(x + 40 * math.sin(i), H)
        prog = clamp(k * 1.4 - i * 0.05)
        m = skia.PathMeasure(p, False)
        seg = skia.Path()
        m.getSegment(0, m.getLength() * prog, seg, True)
        c.drawPath(seg, P("#4aa3ff", 10 + i % 3 * 4, 0.9))
    planet_icon(c, 1500, 160, 70, "saturn", t)
    pop_pill(c, t, 274.9, W / 2, 120, "CRACKS TO THE HORIZON", 44, "#7fd3ff", "#0d1220")


def s_ceres(c, t):
    s = 0.36
    ppm = ppm_for(s)
    push(c, t, 277.0, 287.3, 1.0, 1.04, cy=580)
    world_bg(c, "ceres", t)
    title_card(c, t, 277.4, "ceres", "LARGEST IN THE ASTEROID BELT", y=320)
    gravity_badge(c, "ceres", t, 279.4)
    T = 5.0
    hpx = 16.5 * ppm * 0.6  # scaled to frame, ruler is scaled the same
    jumper(c, 900, GY, t, 280.2, hpx, T, who="astro", helmet=True, s=s, expr_air="laugh")
    ruler(c, 1560, GY, ppm * 0.6, 17, 1, label_every=5, a=clamp((t - 280.6) / 0.3))
    if t > 280.9:
        height_tag(c, 1250, GY, GY - 17 * ppm * 0.6, "17 m", a=clamp((t - 280.9) / 0.3))
    if t > 283.4:
        bubble(c, 1500, 260, "CERES WHO?", 44, a=clamp((t - 283.4) / 0.3))


def s_hold(c, t):
    c.drawRect(skia.Rect(0, 0, W, H), P("#000000"))
    keys = ["pluto", "enceladus", "ceres"]
    for i, key in enumerate(keys):
        x0 = i * W / 3
        c.save()
        c.clipRect(skia.Rect(x0, 0, x0 + W / 3, H))
        c.translate(x0 - W / 3, 0)
        world_bg(c, key, t)
        u = clamp((t - 286.8) / 2.2)
        lift = 420 * (1 - u)
        pose = POSE_FLOAT if u < 1 else POSE_STAND
        person(c, W / 2, GY, pose, "astro", "happy", t, 0.45, lift=lift, shadow_h=lift, helmet=True)
        c.restore()
        if t > 287.5:
            arrow(c, x0 + W / 6 + 160, 300, x0 + W / 6 + 160, 560, "#4cd68a", 16, clamp((t - 287.5) / 0.3))
    for i in (1, 2):
        line(c, i * W / 3, 0, i * W / 3, H, "#ffffff", 6)
    pop_pill(c, t, 287.4, W / 2, 140, "THEY ALWAYS BRING YOU BACK", 48, "#4cd68a", "#0d1220", end=290.2)
    if t > 290.2:
        c.drawRect(skia.Rect(0, 0, W, H), P("#000000", a=0.5 * clamp((t - 290.2) / 0.4)))
        big_text(c, t, 290.4, "…UNTIL NOW", W / 2, 540, 120, "#ff5a3c")


def s_escape(c, t):
    grid_board(c, t)
    text(c, "ESCAPE VELOCITY", W / 2, 140, 84, "#ffffff", a=clamp(at(t, 296.4, 0.4)))
    if t > 297.4:
        pop_pill(c, t, 297.4, W / 2, 230, "THE SPEED TO LEAVE… AND NEVER COME BACK", 34, "#ffffff", "#1b1b2f")
    rows = [("earth", "11 km/s", 300.9, 1.0), ("moon", "2.4 km/s", 305.1, 0.42), ("bennu", "0.2 m/s", 310.9, 0.0)]
    for i, (key, lab, st, frac) in enumerate(rows):
        y = 400 + i * 190
        k = back_out(at(t, st - 0.4, 0.45))
        if k <= 0:
            continue
        with xf(c, 0, 0, alpha=clamp(k)):
            planet_icon(c, 220, y + 40, 60, key, t)
            text(c, WORLDS[key]["name"], 320, y + 56, 44, "#ffffff", align="left")
            bw = ease_out(at(t, st, 0.9)) * max(frac * 900, 8)
            rrect(c, 760, y + 16, bw, 50, 14, "#ff5a3c" if frac > 0 else "#4cd68a")
            text(c, lab, 780 + bw, y + 58, 46, "#ffd34d", align="left")
    # human leg speed reference
    if t > 303.4:
        a = clamp((t - 303.4) / 0.3) * (1 - clamp((t - 309.0) / 0.4))
        with xf(c, alpha=a):
            line(c, 760, 330, 760, 960, "#4cd6ff", 4)
            text(c, "YOUR LEGS: 3 m/s", 780, 345, 34, "#4cd6ff", "Bold", align="left")
    if t > 314.0:
        pop_pill(c, t, 314.0, 1450, 920, "SLOWER THAN A WALK", 42, "#4cd68a", "#0d1220")


def s_bennu(c, t):
    s = 0.5
    t0 = 319.6
    if t < t0:
        d = 0.0
    else:
        d = (t - t0) * 70  # px per second drift, never slows
    # camera pulls away so the asteroid shrinks
    z = 1.0 / (1 + max(0.0, t - t0) * 0.12)
    c.drawRect(skia.Rect(0, 0, W, H), P("#020205"))
    for (sx, sy, sr, ph) in STARS_W:
        c.drawCircle(sx, sy, sr * 0.7, P("#ffffff", a=0.6))
    c.save()
    cam(c, z, W / 2, 700 - d * 0.5)
    # rubble-pile asteroid
    R = 900
    cx, cy = W / 2, 860 + R
    c.drawCircle(cx, cy, R, P("#4a4642"))
    rr = _r.Random(3)
    for _ in range(120):
        ang = rr.uniform(-1.2, 1.2) - math.pi / 2
        dist = rr.uniform(0.6, 1.0) * R
        x = cx + math.cos(ang) * dist
        y = cy + math.sin(ang) * dist
        r = rr.uniform(14, 50)
        c.drawCircle(x, y, r, P(rr.choice(("#5a5550", "#3a3632", "#6a645e"))))
    pose = POSE_STAND if t < t0 - 0.35 else (mix_pose(POSE_STAND, POSE_CROUCH, (t - t0 + 0.35) / 0.35)
                                             if t < t0 else POSE_FLOAT)
    tilt = 0 if t < t0 else (t - t0) * 12
    person(c, W / 2, 860, pose, "astro", "happy" if t < t0 + 1.5 else "shock", t, s, lift=d, shadow_h=d,
           helmet=True, tilt=tilt)
    c.restore()
    title_card(c, t, 316.0, "bennu", "ESCAPE SPEED: 0.2 m/s", y=260) if t < 319 else None
    if t > 318.9:
        pop_pill(c, t, 319.0, W / 2, 140, "IT SENDS YOU AWAY", 48, "#ff5a3c", "#ffffff", end=322.1)
    if t > 322.4:
        pop_pill(c, t, 322.5, W / 2, 140, "NO WAY BACK", 48, "#ff5a3c", "#ffffff")


def s_missions(c, t):
    grid_board(c, t)
    text(c, "HOW MISSIONS STAY PUT", W / 2, 150, 72, "#ffffff", a=clamp(at(t, 333.3, 0.4)))
    items = [("ANCHORS", 335.1), ("HARPOONS", 335.6), ("THRUSTERS", 336.7)]
    for i, (lab, st) in enumerate(items):
        k = back_out(at(t, st, 0.45))
        x = 420 + i * 540
        with xf(c, x, 520, s=0.4 + 0.6 * k, alpha=clamp(k)):
            card(c, -210, -200, 420, 400, "#16264a", a=0.95)
            if i == 0:  # anchor
                line(c, 0, -110, 0, 90, "#d9dee6", 18)
                c.drawCircle(0, -125, 26, P("#d9dee6", 12))
                line(c, -60, -70, 60, -70, "#d9dee6", 14)
                p = skia.Path()
                p.addArc(skia.Rect(-90, -20, 90, 120), 0, 180)
                c.drawPath(p, P("#d9dee6", 16))
            elif i == 1:  # harpoon
                line(c, -120, 80, 90, -80, "#d9dee6", 14)
                c.drawPath(poly([(110, -100), (60, -90), (100, -50)]), P("#ff5a3c"))
            else:  # thruster
                rrect(c, -50, -110, 100, 150, 20, "#d9dee6")
                c.drawPath(poly([(-40, 40), (40, 40), (0, 40 + 80 + 20 * math.sin(t * 30))]), P("#ff9a3c"))
            text(c, lab, 0, 160, 44, "#ffd34d")
    if t > 337.3:
        k = back_out(at(t, 337.3, 0.45))
        with xf(c, W / 2, 900, s=k):
            for dx in (-60, 60):
                c.drawOval(skia.Rect(dx - 22, -40, dx + 22, 40), P("#ffffff", a=0.8))
            cross_mark(c, 0, 0, 160)
            text(c, "NOT FOOTSTEPS", 260, 18, 46, "#ff5a3c", align="left")


def s_opposite(c, t):
    grid_board(c, t)
    k = smooth((t - 341.0) / 2.5)
    # see-saw: small worlds up, heavy world down
    with xf(c, W / 2, 620, rot=lerp(0, 14, k)):
        rrect(c, -700, -14, 1400, 28, 14, "#d9dee6")
        planet_icon(c, -560, -100, 70, "bennu", t)
        planet_icon(c, 560, -190, 170 * (0.3 + 0.7 * k), "sun", t)
    c.drawPath(poly([(W / 2, 640), (W / 2 - 70, 760), (W / 2 + 70, 760)]), P("#7f8fa6"))
    pop_pill(c, t, 340.2, 400, 200, "LEAP SO HIGH", 44, "#4cd68a", "#0d1220")
    if t > 342.6:
        pop_pill(c, t, 342.6, 1500, 200, "THE OPPOSITE?", 44, "#ff5a3c", "#ffffff")
    if t > 345.3:
        big_text(c, t, 345.3, "ALMOST IMPOSSIBLE", W / 2, 920, 80, "#ffd34d")


# =============================================================== 8. HEAVY WORLDS
def s_sun(c, t):
    s = 0.95
    ppm = ppm_for(s)
    push(c, t, 346.6, 361.6, 1.0, 1.08, cy=640)
    world_bg(c, "sun", t)
    title_card(c, t, 346.7, "sun", "28× EARTH'S GRAVITY", y=330)
    gravity_badge(c, "sun", t, 348.5)
    if t > 351.2:
        with xf(c, alpha=clamp((t - 351.2) / 0.3)):
            T = air_time(28.0)
            jumper(c, 900, GY, t, 357.6, 0.016 * ppm * 6, T * 2.5, s=s, repeat=1.4, expr="dry")
        if t > 352.6:
            pop_pill(c, t, 352.7, 1450, 330, "(YOU COULDN'T)", 38, "#ffffff", "#1b1b2f", end=355.0)
    # magnifier on the gap
    if 355.0 < t < 361.6:
        k = back_out(at(t, 355.0, 0.45))
        with xf(c, 1400, 600, s=k):
            c.drawCircle(0, 0, 190, P("#ffffff", a=0.9))
            c.drawCircle(0, 0, 190, P("#1b1b2f", 14))
            line(c, 130, 130, 260, 260, "#1b1b2f", 30)
            text(c, "< 2 cm", 0, -10, 76, "#e4572e")
            text(c, "< 1 INCH", 0, 70, 44, "#1b1b2f")
    if t > 361.6:
        c.drawRect(skia.Rect(0, 0, W, H), P("#ffffff", a=0.6 * clamp((t - 361.6) / 0.6)))
        big_text(c, t, 361.8, "THE HEAT WINS FIRST", W / 2, 540, 90, "#e4572e")


def s_neutron(c, t):
    c.drawRect(skia.Rect(0, 0, W, H), P("#05031a"))
    for (sx, sy, sr, ph) in STARS_W:
        c.drawCircle(sx, sy, sr * 0.7, P("#ffffff", a=0.6))
    k = back_out(at(t, 367.2, 0.6))
    planet_icon(c, 620, 520, 230 * k, "neutron", t)
    title_card(c, t, 367.2, "neutron", "A COLLAPSED STAR'S CORE", y=170) if t < 371 else None
    # city skyline the same width
    if t > 372.8:
        a = clamp((t - 372.8) / 0.4)
        with xf(c, alpha=a):
            rr = _r.Random(4)
            x = 1100
            while x < 1800:
                w = rr.uniform(40, 90)
                h = rr.uniform(120, 380)
                rrect(c, x, 760 - h, w, h, 4, "#3a3f6a")
                x += w + 6
            line(c, 1100, 790, 1800, 790, "#ffd34d", 6)
            text(c, "≈ ONE CITY WIDE", 1450, 850, 44, "#ffd34d")
    if t > 370.6:
        pop_pill(c, t, 370.6, 1450, 200, "MORE MASS THAN THE SUN", 40, "#ffd34d", "#0d1220", end=375.1)
    if t > 375.2:
        n = counter(t, 375.2, 1.4, 1, 200)
        pop_pill(c, t, 375.2, 1450, 200, f"{int(n)},000,000,000× GRAVITY", 40, "#ff5a3c", "#ffffff")


def s_atom(c, t):
    grid_board(c, t, "#05031a", "#1d1450")
    k = back_out(at(t, 378.6, 0.5))
    with xf(c, 560, 520, s=k):
        c.drawCircle(0, 0, 30, P("#ffd34d"))
        for ang in (0, 60, 120):
            with xf(c, 0, 0, rot=ang + t * 20):
                c.drawOval(skia.Rect(-200, -70, 200, 70), P("#7fd3ff", 6))
            e = math.radians(t * 200 + ang * 3)
            with xf(c, 0, 0, rot=ang + t * 20):
                c.drawCircle(200 * math.cos(e), 70 * math.sin(e), 14, P("#ffffff"))
        text(c, "ONE ATOM", 0, 300, 52, "#ffffff")
    if t > 379.5:
        pop_pill(c, t, 379.5, 560, 120, "YOUR JUMP < THIS", 46, "#ff5a3c", "#ffffff")
    # flattening person
    sq = 1.0
    if t > 386.6:
        sq = lerp(1.0, 0.04, smooth((t - 386.6) / 1.0))
    person(c, 1400, 900, POSE_STRAIN if t > 381.0 else POSE_STAND, "you", "dry", t, 0.9, squash=sq, sweat=1.0)
    if t > 381.2 and t < 386.6:
        for kk in range(3):
            x = 1260 + kk * 140
            arrow(c, x, 200, x, 380, "#ff5a3c", 20, 0.8)
    if t > 387.6:
        pop_pill(c, t, 387.8, 1400, 700, "THINNER THAN PAPER", 46)


# =============================================================== 9. RECAP + ENDING
RECAP = [("moon", "10 FEET", 393.2, 3.0), ("mars", "4 FEET", 394.5, 1.33), ("earth", "20 INCHES", 395.8, 0.5),
         ("jupiter", "8 INCHES", 397.4, 0.2), ("sun", "< 1 INCH", 398.8, 0.02), ("neutron", "NOTHING", 401.0, 0.0),
         ("bennu", "FOREVER", 403.1, 99)]


def s_recap(c, t):
    grid_board(c, t)
    text(c, "ONE JUMP. SEVEN WORLDS.", W / 2, 120, 70, "#ffffff", a=clamp(at(t, 389.6, 0.4)))
    base = 900
    for i, (key, lab, st, hm) in enumerate(RECAP):
        x = 200 + i * 255
        k = back_out(at(t, st - 0.3, 0.45))
        if k <= 0:
            continue
        with xf(c, x, 0, alpha=clamp(k)):
            planet_icon(c, 0, base + 70, 48, key, t)
            if hm >= 99:
                bh = ease_out(at(t, st, 0.8)) * 760
                fill_shader(c, skia.Rect(-50, base - bh, 50, base),
                            linear(0, base, 0, base - 760, ["#4cd68a", ("#4cd68a", 0)]))
                text(c, "∞", 0, base - bh + 40, 120, "#4cd68a")
            else:
                bh = ease_out(at(t, st, 0.6)) * max(4, hm / 3.0 * 600)
                rrect(c, -50, base - bh, 100, bh, 12, "#ffd34d")
            text(c, lab, 0, base - (bh if hm < 99 else 680) - 30, 32, "#ffffff")


def s_conversation(c, t):
    grid_board(c, t)
    k1 = back_out(at(t, 405.6, 0.5))
    with xf(c, 520, 560, s=k1, alpha=clamp(k1)):
        person(c, 0, 300, dict(la=(-150, -60), ra=(150, 60), ll=(6, 0), rl=(-6, 0)), "you", "happy", t, 1.0,
               shadow_h=None)
        text(c, "YOUR MUSCLES", 0, 400, 50, "#ffffff")
    k2 = back_out(at(t, 407.6, 0.5))
    with xf(c, 1400, 520, s=k2, alpha=clamp(k2)):
        planet_icon(c, 0, 0, 200, "earth", t)
        text(c, "THE PLANET", 0, 330, 50, "#ffffff")
    if t > 406.0:
        bubble(c, 820, 260, "I PUSH!", 46, a=clamp((t - 406.0) / 0.3), tail=(-1, 1))
    if t > 407.9:
        bubble(c, 1150, 200, "I PULL!", 46, a=clamp((t - 407.9) / 0.3), tail=(1, 1))
    if t > 408.8:
        k = (t - 408.8)
        keys = ["moon", "mars", "jupiter", "pluto"]
        if k > 0.0:
            idx = int(k * 3) % len(keys)
            if t > 409.8:
                with xf(c, 1400, 520, s=k2):
                    planet_icon(c, 0, 0, 200, keys[idx], t)
        pop_pill(c, t, 410.0, W / 2, 960, "CHANGE THE PLANET → CHANGE THE ANSWER", 42)


def s_only_here(c, t):
    s = 0.95
    ppm = ppm_for(s)
    push(c, t, 410.8, 423.0, 1.0, 1.08, cx=900, cy=640)
    world_bg(c, "earth", t)
    earth_props(c, t)
    jumper(c, 900, GY, t, 413.5, 0.46 * ppm, air_time(1.0), s=s, repeat=2.2)
    if t > 414.9:
        k = back_out(at(t, 414.9, 0.5))
        with xf(c, 1350, 360, s=k):
            card(c, -300, -110, 600, 220, "#0d1220", a=0.85)
            text(c, "0.5 m", 0, 0, 100, "#ffd34d")
            text(c, "EXISTS ONLY HERE", 0, 70, 40, "#ffffff", "Bold")
    if t > 417.4:
        pop_pill(c, t, 417.4, 1350, 580, "SET BY EARTH'S SIZE + WEIGHT", 36)


def s_body_diff(c, t):
    grid_board(c, t)
    items = [("TALLER", 423.1, "#7fd3ff"), ("STEPS", 423.6, "#ffd34d"), ("LONGER FALLS", 424.3, "#ff9a3c"),
             ("EASIER RUNNING", 425.3, "#4cd68a"), ("HARDER BREATHING", 426.4, "#ff5a3c")]
    for i, (lab, st, col) in enumerate(items):
        x = 420 + (i % 3) * 540
        y = 330 + (i // 3) * 250
        if i >= 3:
            x = 690 + (i - 3) * 540
        pop_pill(c, t, st, x, y, lab, 50, col, "#0d1220")
    if t > 427.3:
        k = back_out(at(t, 427.3, 0.5))
        with xf(c, W / 2, 860, s=k):
            card(c, -420, -100, 840, 200, "#0d1220", a=0.9)
            text(c, "WE EVOLVED FOR  1.00 g", 0, 22, 62, "#ffffff")


def s_future(c, t):
    s = 0.7
    push(c, t, 429.4, 442.6, 1.0, 1.06, cy=620)
    key = "moon" if t < 437.7 else "mars"
    world_bg(c, key, t)
    # habitat domes
    for x, r in ((1300, 220), (1620, 150), (1080, 120)):
        p = skia.Path()
        p.addArc(skia.Rect(x - r, GY - r, x + r, GY + r), 180, 180)
        c.drawPath(p, P("#dff3ff", a=0.35))
        c.drawPath(p, P("#ffffff", 6, 0.8))
    person(c, 700, GY, POSE_STAND, "astro", "happy", t, s, helmet=True)
    person(c, 860, GY, POSE_STAND, "astro", "happy", t, s * 0.65, helmet=True)
    if t > 433.1:
        pop_pill(c, t, 433.1, W / 2, 140, "ONE LAST QUESTION", 50)
    if t > 438.4:
        pop_pill(c, t, 438.4, 780, 300, "FOR GENERATIONS", 40, "#ffffff", "#1b1b2f")
    labels = [("BONES", 440.8), ("MUSCLES", 441.4), ("HEARTS", 442.2)]
    for i, (lab, st) in enumerate(labels):
        pop_pill(c, t, st, 1150 + i * 260, 430, lab, 38, "#ff5a3c", "#ffffff")


def s_home(c, t):
    s = 0.95
    push(c, t, 442.6, 450.0, 1.0, 1.12, cx=960, cy=620)
    world_bg(c, "earth", t)
    earth_props(c, t)
    # child born on Mars arrives on Earth and struggles to stand up straight
    k = smooth((t - 444.5) / 2.0)
    pose = mix_pose(POSE_STRAIN, POSE_STAND, k * 0.6)
    person(c, 960, GY, pose, "kid", "worried", t, s, sweat=1.0 - k * 0.5)
    if t > 444.0:
        pop_pill(c, t, 444.0, 960, 250, "STAND UP STRAIGHT?", 46, "#ffffff", "#1b1b2f", end=446.0)
    if t > 446.1:
        c.drawRect(skia.Rect(0, 0, W, H), P("#000000", a=0.55 * clamp((t - 446.1) / 1.2)))
        big_text(c, t, 447.6, "STILL HOME?", W / 2, 520, 130, "#ffd34d")


SCENES = [
    (0.0, 6.0, s_hook_tall),
    (6.0, 11.2, s_hook_heavy),
    (11.2, 19.0, s_earth),
    (19.0, 23.0, s_half_story),
    (23.0, 28.4, s_change),
    (28.4, 46.5, s_rule),
    (46.5, 49.3, s_three),
    (49.3, 55.7, s_fly),
    (55.7, 63.3, s_moon_intro),
    (63.3, 70.7, s_moon_hoop),
    (70.7, 78.6, s_hang),
    (78.6, 82.9, s_float),
    (82.9, 90.6, s_apollo),
    (90.6, 96.3, s_teaser),
    (96.3, 99.6, s_closer),
    (99.6, 112.6, s_mars),
    (112.6, 123.8, s_mercury),
    (123.8, 138.1, s_suit),
    (138.1, 141.9, s_gift),
    (141.9, 155.4, s_venus),
    (155.4, 162.7, s_venus_danger),
    (162.7, 170.8, s_thought),
    (170.8, 178.2, s_mismatch),
    (178.2, 183.7, s_jupiter_big),
    (183.7, 201.3, s_jupiter),
    (201.3, 205.7, s_bodies),
    (205.7, 217.4, s_saturn),
    (217.4, 223.3, s_like_home),
    (223.3, 237.6, s_ice_giants),
    (237.6, 245.6, s_lineup),
    (245.6, 261.0, s_pluto),
    (261.0, 273.6, s_enceladus),
    (273.6, 277.2, s_cracks),
    (277.2, 286.8, s_ceres),
    (286.8, 294.8, s_hold),
    (294.8, 315.8, s_escape),
    (315.8, 329.6, s_bennu),
    (329.6, 338.5, s_missions),
    (338.5, 346.6, s_opposite),
    (346.6, 366.9, s_sun),
    (366.9, 378.4, s_neutron),
    (378.4, 389.3, s_atom),
    (389.3, 405.5, s_recap),
    (405.5, 410.8, s_conversation),
    (410.8, 423.0, s_only_here),
    (423.0, 429.4, s_body_diff),
    (429.4, 442.6, s_future),
    (442.6, 9999, s_home),
]
CUTS = [s for s, _, _ in SCENES[1:]]


# =============================================================== captions
def load_captions(path):
    words = json.load(open(path))
    chunks = []
    cur = []
    for i, w in enumerate(words):
        if cur:
            gap = w["s"] - cur[-1]["e"]
            if len(cur) >= 6 or gap > 0.35:
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    out = []
    for ch in chunks:
        out.append((ch[0]["s"], ch[-1]["e"] + 0.25, ch))
    # make chunks hand off cleanly
    for i in range(len(out) - 1):
        s0, e0, ch = out[i]
        out[i] = (s0, min(e0, out[i + 1][0]), ch)
    return out


CAPS = load_captions(os.path.join(HERE, "transcript.json"))
BURN = os.environ.get("BURN_CAPTIONS", "1") == "1"


def draw_captions(c, t):
    if not BURN:
        return
    for s0, e0, ch in CAPS:
        if s0 - 0.05 <= t < e0:
            size = 50
            words = [w["w"] for w in ch]
            widths = [text_width(w, size) for w in words]
            gapw = size * 0.32
            total = sum(widths) + gapw * (len(words) - 1)
            x = W / 2 - total / 2
            y = 1012
            rrect(c, x - 26, y - 52, total + 52, 72, 22, "#000000", 0.55)
            for w, ww, wd in zip(ch, words, widths):
                on = w["s"] - 0.02 <= t
                cur = w["s"] - 0.02 <= t < w["e"] + 0.1
                col = "#ffd34d" if cur else ("#ffffff" if on else "#c9ced8")
                text(c, ww, x, y, size, col, align="left", a=1.0 if on else 0.75)
                x += wd + gapw
            break


def render_frame(c, t):
    c.clear(C("#000000"))
    for start, end, fn in SCENES:
        if start <= t < end:
            c.save()
            fn(c, t)
            c.restoreToCount(1)
            break
    vignette(c, 0.42)
    grain(c, t, 0.045)
    dip = 0.0
    for ct in CUTS:
        d = abs(t - ct)
        if d < 0.14:
            dip = max(dip, 1 - d / 0.14)
    if t < 0.3:
        dip = max(dip, 1 - t / 0.3)
    if t > 448.6:
        dip = max(dip, clamp((t - 448.6) / 1.0))
    if dip > 0:
        c.drawRect(skia.Rect(0, 0, W, H), P("#000000", a=dip * 0.92))
    draw_captions(c, t)
