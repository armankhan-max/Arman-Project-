"""Timeline for the GTA 6 buying-guide video. Each scene uses absolute times taken from the
word timestamps in transcript.json, so every visual beat and SFX lands on its word.

SFX cues are registered next to the visuals (sx(...)) and read by audio_gta.py.
"""
import json
import math
import os
import random

import skia

from ggfx import *  # noqa: F401,F403
from ggfx import (W, H, C, P, xf, rrect, poly, line, linear, radial, fill_shader, clamp, lerp, smooth, ease_out,
                  back_out, at, window, mixhex, blit, grain, tint, figure, head_only, arrow)
import sgfx

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE_END = 301.25          # narration ends here (the rest of the recording is production notes)
END = VOICE_END + 3.6       # short music outro

# ------------------------------------------------------------------ word timing
_WORDS = []
for seg in json.load(open(os.path.join(HERE, "transcript.json"))):
    for w in seg["words"]:
        _WORDS.append((w["w"].strip().lower().strip(".,?!"), w["s"], w["e"]))


def T(word, near):
    """Start time of `word` closest to `near` seconds."""
    word = word.lower()
    best = min((abs(s - near), s) for ww, s, e in _WORDS if ww == word)
    assert best[0] < 4.0, (word, near, best)
    return best[1]


SFX = []


def sx(t, name, gain=1.0, pan=0.0, **kw):
    SFX.append((t, name, gain, pan, kw))


# ------------------------------------------------------------------ helpers
def push(c, t, a, b, z0=1.0, z1=1.06, cx=W / 2, cy=H / 2, dx=0.0):
    k = smooth((t - a) / max(0.01, b - a))
    z = lerp(z0, z1, k)
    c.translate(cx + dx * k, cy)
    c.scale(z, z)
    c.translate(-cx, -cy)


def drift(c, t, amp=4):
    c.translate(math.sin(t * 0.7) * amp, math.cos(t * 0.53) * amp * 0.7)


def xmark(c, x, y, s=1.0, a=1.0, color=RED):
    with xf(c, x, y, s, alpha=a):
        line(c, -60, -60, 60, 60, "#000000", 40)
        line(c, -60, 60, 60, -60, "#000000", 40)
        line(c, -60, -60, 60, 60, color, 26)
        line(c, -60, 60, 60, -60, color, 26)


def check(c, x, y, s=1.0, a=1.0, color=GREEN):
    with xf(c, x, y, s, alpha=a):
        pth = poly([(-60, 0), (-18, 44), (66, -50)], close=False)
        c.drawPath(pth, P("#000000", 40))
        c.drawPath(pth, P(color, 26))


def bubble(c, x, y, s, label, a=1.0, bg="#ffffff", fg="#0b0614", size=56, tail=-1):
    w = tw(label, size) + 70
    with xf(c, x, y, s, alpha=a):
        c.drawPath(poly([(tail * 20, 40), (tail * 70, 100), (tail * 60, 30)]), P(bg))
        rrect(c, -w / 2, -60, w, 110, 40, bg)
        ftext(c, label, 0, 18, size, fg)


def rays(c, x, y, t, color=GOLD, a=0.25, n=14, r=1400):
    with xf(c, x, y, rot=t * 12):
        for i in range(n):
            ang = 2 * math.pi * i / n
            ang2 = ang + math.pi / n * 0.6
            c.drawPath(poly([(0, 0), (math.cos(ang) * r, math.sin(ang) * r), (math.cos(ang2) * r, math.sin(ang2) * r)]),
                       P(color, a=a))


def pedestal(c, x, y, w=300, col=PINK, a=1.0):
    with xf(c, x, y, alpha=a):
        c.drawOval(skia.Rect(-w / 2 - 40, -30, w / 2 + 40, 30), blurp(col, 20, 0.6))
        rrect(c, -w / 2, 0, w, 200, 12, "#1a1030")
        c.drawOval(skia.Rect(-w / 2, -24, w / 2, 24), P("#2b1a4a"))
        c.drawOval(skia.Rect(-w / 2, -24, w / 2, 24), P(col, 4, 0.9))


def spotlight(c, x, y_floor, a=0.18, w=360):
    c.drawPath(poly([(x - 70, -20), (x + 70, -20), (x + w, y_floor), (x - w, y_floor)]), P("#fff3c4", a=a))
    c.drawOval(skia.Rect(x - w, y_floor - 40, x + w, y_floor + 40), P("#fff3c4", a=a * 0.8))


def walk_pose(t, speed=7.0):
    return "run" if (t * speed) % 2 < 1 else "run2"


def crowd_walk(c, t, x0, y, n, spacing, s, face=1, speed=7.0, expr="wide", whos=("buyer", "buyer2", "buyer3"),
               rim=None):
    for i in range(n):
        bob = abs(math.sin(t * speed * 1.5 + i)) * 10
        figure(c, x0 + i * spacing * face * -1, y - bob, whos[i % len(whos)], walk_pose(t + i * 0.13, speed), expr,
               t + i, s=s, face=face, rim=rim or sgfx.RIM)


def ticker(c, t, start, v0, v1, dur, x=W - 70, y=110, size=72, color=CASH, prefix=""):
    k = smooth(at(t, start, dur))
    money_hud(c, lerp(v0, v1, k), t, color=color, x=x, y=y, size=size)


def card_panel(c, x, y, w, h, t, start, num, draw, col=PINK, end=None):
    if t < start:
        return
    k = back_out(at(t, start, 0.4))
    out = 1.0 if end is None else clamp((end - t) / 0.3)
    with xf(c, x, y, k, alpha=min(1, k) * out):
        rrect(c, -w / 2 + 16, -h / 2 + 20, w, h, 30, "#000000", 0.5)
        rrect(c, -w / 2, -h / 2, w, h, 30, "#140a2a")
        rrect(c, -w / 2, -h / 2, w, h, 30, col, stroke=6)
        c.drawCircle(-w / 2 + 10, -h / 2 + 10, 46, P(col))
        ftext(c, str(num), -w / 2 + 10, -h / 2 + 30, 60, "#0b0614")
        c.save()
        c.scale(1.6, 1.6)
        draw(c)
        c.restore()


def char_wheel(c, t, start, whos, sel_t=None, sel=1, x=W / 2, y=H / 2 + 20, r=300):
    """Original character-switch wheel: 3 portrait slots around a ring."""
    k = ease_out(at(t, start, 0.35))
    with xf(c, x, y, lerp(0.6, 1.0, k), alpha=k):
        c.drawCircle(0, 0, r + 70, P("#000000", a=0.55))
        c.drawCircle(0, 0, r + 70, P("#ffffff", 4, 0.4))
        angs = [-150, -90, -30][:len(whos)] if len(whos) == 3 else [-90 + i * 360 / len(whos) for i in range(len(whos))]
        active = None
        if sel_t is not None and t >= sel_t:
            active = sel
        elif sel_t is not None:
            # cycling highlight before the selection lands
            active = int((t - start) * 6) % len(whos)
        for i, (who, expr) in enumerate(whos):
            a = math.radians(angs[i])
            px, py = math.cos(a) * r * 0.78, math.sin(a) * r * 0.78 + 80
            on = active == i
            c.drawCircle(px, py, 120, P(GOLD if on else "#2a2140"))
            c.drawCircle(px, py, 120, P("#ffffff" if on else "#5a4f7a", 6))
            c.save()
            pth = skia.Path()
            pth.addCircle(px, py, 112)
            c.clipPath(pth, skia.ClipOp.kIntersect, True)
            head_only(c, px, py + 30, who, expr, t, r=70, rim=CYAN if on else "#4a4466")
            c.restore()
        c.drawCircle(0, 80, 40, P("#ffffff", a=0.15))


# ================================================================== SCENES
# --- A. Hook: "In 12 days, millions of people will make the same mistake."
def s_hook(c, t):
    a, b = 0.0, T("they'll", 3.8)
    c.save()
    push(c, t, a, b, 1.12, 1.0)
    scene_coast(c, t, "night", cam=t * 30, sun=False, car_x=-300 + t * 700)
    c.restore()
    # crowd specks flooding the street (millions)
    m = T("millions", 1.2)
    if t > m:
        rnd = random.Random(4)
        k = ease_out(at(t, m, 1.5))
        for i in range(160):
            x = rnd.uniform(0, W)
            y = rnd.uniform(930, 1070)
            if rnd.random() < k:
                c.drawCircle(x + math.sin(t * 9 + i) * 3, y, rnd.uniform(5, 9), P(rnd.choice((PINK, CYAN, GOLD, "#ffffff")),
                                                                                   a=0.8))
    letterbox(c, 1.0)
    slam_title(c, t, T("12", 0.3), "12 DAYS", W / 2, 420, 210, end=b + 0.1)
    mk = T("mistake", 2.7)
    if t > mk:
        tint(c, RED, 0.25 * clamp(1 - (t - mk) / 0.8))
    flash(c, t, T("12", 0.3), 0.2)


sx(0.0, "boom", 0.9)
sx(0.0, "riser_rev", 0.4)
sx(T("12", 0.3) - 0.02, "slam", 1.0)
sx(T("millions", 1.2), "crowd", 0.5, dur=2.4)
sx(T("mistake", 2.7), "hit_low", 0.8)
sx(0.4, "car_pass", 0.35, pan=0.6)


# --- B. Rush to the store, hand over hundreds of dollars
def s_rush(c, t):
    a, b = T("they'll", 3.8), T("and", 8.3)
    c.save()
    push(c, t, a, b, 1.0, 1.08, dx=-60)
    scene_street(c, t, "night", cam=(t - a) * 40)
    storefront(c, 1250, 905, 0.85, t)
    lt = t - a
    x0 = -200 + lt * 230
    crowd_walk(c, t, x0, 1000, 6, 140, 0.5, face=1, speed=8)
    h = T("hand", 5.4)
    if t > h:
        rnd = random.Random(8)
        for i in range(14):
            st = h + i * 0.12
            if t > st:
                k = (t - st) / 1.3
                bx = lerp(x0 - rnd.uniform(0, 600), 1250 + rnd.uniform(-200, 200), clamp(k))
                by = 820 - math.sin(clamp(k) * math.pi) * rnd.uniform(200, 380)
                if k < 1:
                    bill(c, bx, by, 0.6, rot=k * 600 + i * 30)
    cn = T("console", 7.3)
    if t > cn:
        k = pop_in(t, cn)
        console_tall(c, 1110, 860, 0.38 * k, glow_c=CYAN)
        console_box(c, 1400, 860, 0.38 * k, glow_c=GREEN)
    c.restore()
    # HUD money draining
    hd = T("hundreds", 5.9)
    money_hud(c, 1250 - 900 * smooth(at(t, hd, 1.6)), t, color=CASH if t < hd else "#ff6b6b")
    if t > hd:
        k = at(t, hd, 0.3)
        ftext(c, "-$900", W - 70, 190 + (1 - k) * 20, 54, "#ff5050", "InterDisplay-Black", align="right",
              stroke="#000000", sw=8, a=window(t, hd, b, 0.2))
    minimap(c, t, heading=t * 8)


sx(T("rush", 4.0), "whoosh", 0.6)
sx(T("rush", 4.0), "footsteps", 0.45, dur=3.8)
sx(T("hand", 5.4), "cash_flutter", 0.6)
sx(T("hundreds", 5.9), "register", 0.7)
for i in range(5):
    sx(T("hundreds", 5.9) + 0.15 + i * 0.28, "coin_out", 0.25)
sx(T("console", 7.3), "pop", 0.5)


# --- C. Wrong thing / right thing for the wrong reason
def s_wrong(c, t):
    a, b = T("and", 8.3), T("by", 13.4)
    room_bg(c, t)
    c.save()
    push(c, t, a, b, 1.0, 1.05)
    tv(c, 1480, 560, 0.75, t=t)
    wr = T("wrong", 10.0)
    ri = T("right", 11.4)
    split = t >= ri - 0.2
    if not split:
        figure(c, W / 2 - 80, 900, "buyer", "hold", "happy" if t < wr else "sad", t, s=1.0, rim=PINK,
               hold=lambda cc, hx, hy: console_old(cc, hx + 40, hy + 60, 0.9, crack=1 if t > wr else 0, kind=1))
        if t > wr:
            xmark(c, W / 2 + 330, 420, back_out(at(t, wr, 0.25)) * 1.6)
    else:
        k = ease_out(at(t, ri - 0.2, 0.4))
        # left: wrong thing (old console) — right: right thing, wrong reason (burning wallet)
        c.save()
        sgfx.clip_half(c, 0, seed=2)
        tint(c, "#200818", 0.6)
        figure(c, 480, 900, "buyer", "stand", "sad", t, s=0.85, rim=PINK)
        console_old(c, 480, 990, 0.6, crack=1, kind=1)
        xmark(c, 480, 300, 1.1)
        c.restore()
        c.save()
        sgfx.clip_half(c, 1, seed=2)
        tint(c, "#082018", 0.5)
        figure(c, 1430, 900, "buyer2", "cheer", "laugh", t, s=0.85, rim=GOLD)
        console_tall(c, 1700, 1000, 0.45, glow_c=CYAN)
        rw = T("reason", 12.5)
        if t > T("wrong", 12.3):
            wallet(c, 1150, 520, 0.6, burn=clamp((t - T("wrong", 12.3)) * 2), t=t)
        check(c, 1400, 260, 1.1 * back_out(at(t, ri, 0.3)))
        if t > rw:
            qmark(c, 1600, 250, 200, ORANGE, t=t)
        c.restore()
        sgfx.jagged_split(c, seed=2, color="#000000", w=14 * k)
    c.restore()


sx(T("bought", 9.6), "box_drop", 0.4)
sx(T("wrong", 10.0), "buzzer", 0.5)
sx(T("wrong", 10.0), "glass_crack", 0.4)
sx(T("right", 11.4) - 0.2, "whoosh", 0.5)
sx(T("right", 11.4), "ding", 0.4)
sx(T("wrong", 12.3), "fire", 0.4, dur=1.2)


# --- D. Which one are you? character wheel
def s_which(c, t):
    a, b = T("by", 13.4), T("and", 17.1)
    grid_board(c, t)
    c.save()
    push(c, t, a, b, 1.0, 1.06)
    char_wheel(c, t, a, [("buyer", "sad"), ("gamer", "worried"), ("buyer2", "happy")], sel_t=T("are", 16.4), sel=1,
               y=H / 2 + 120)
    c.restore()
    if t > T("are", 16.4):
        k = back_out(at(t, T("are", 16.4), 0.3))
        qmark(c, W / 2, 150, 180 * k, GOLD, t=t)


for i in range(14):
    sx(T("by", 13.4) + 0.25 + i * 0.2, "tick_ui", 0.35)
sx(T("are", 16.4), "select", 0.6)


# --- E. One detail nobody's talking about — mystery box
def s_mystery(c, t):
    a, b = T("and", 17.1), T("on", 23.6)
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#07040f", "#120a26"]))
    c.save()
    push(c, t, a, b, 1.0, 1.15, cy=H * 0.55)
    on = T("detail", 17.8)
    sp = ease_out(at(t, on, 0.2))
    rattle = window(t, T("itself", 19.3), T("we'll", 22.3) - 0.2, 0.2)
    lid = 0.0
    if t > T("nobody", 20.3):
        lid = 0.25 * smooth(at(t, T("nobody", 20.3), 1.0))
    sh = T("it", 22.9)
    if t > sh:
        lid = lid * clamp(1 - (t - sh) / 0.12)
    game_box_pedestal(c, W / 2, 760, t, lid=lid, spot=sp, rattle=rattle * 0.6,
                      inside=lambda cc: glow(cc, 0, 0, 260, GOLD, 0.7 * lid * 4))
    if t > sh:
        k = back_out(at(t, sh, 0.3))
        padlock(c, W / 2 + 150, 560, 0.8 * k)
    c.restore()
    ox, oy = shake(t, sh, 0.35, 16)
    c.translate(ox, oy)
    if t < on:
        tint(c, "#000000", 0.6)


sx(T("detail", 17.8), "spotlight", 0.8)
sx(T("detail", 17.8), "drone", 0.45, dur=5.0)
sx(T("itself", 19.3), "rattle", 0.4, dur=2.4)
sx(T("nobody", 20.3), "shimmer", 0.35)
sx(T("it", 22.9), "slam", 0.9)
sx(T("it", 22.9) + 0.05, "lock", 0.7)


# --- F. Launch date: Nov 19, 2026 — establishing shot + BGM drop
def s_launch(c, t):
    a, b = T("on", 23.6), T("take", 28.9)
    c.save()
    push(c, t, a, b, 1.0, 1.1, cy=H * 0.6)
    la = T("launches", 27.8)
    cx = -400 + (t - a) * 380 if t < la else -400 + (la - a) * 380 + (t - la) ** 1.6 * 1800
    scene_coast(c, t, "dusk", cam=(t - a) * 20, car_x=cx)
    c.restore()
    letterbox(c, 1.0)
    slam_title(c, t, T("19th", 23.9), "NOV 19", W / 2, 300, 200, end=b + 0.1, sub=None)
    if t > T("2026", 24.9):
        k = back_out(at(t, T("2026", 24.9), 0.3))
        chip(c, W / 2 + 40, 470, "2026", GOLD, size=60, sc=k)
    if t > T("grand", 26.5):
        k = ease_out(at(t, T("grand", 26.5), 0.4))
        ftext(c, "GTA 6", W / 2, 640 + (1 - k) * 40, 96, "#ffffff", a=k, stroke="#000000", sw=12, glow_c=PINK,
              glow_r=30)
    flash(c, t, la, 0.3, "#ffffff", 0.9)
    flash(c, t, T("19th", 23.9), 0.2, "#ffffff", 0.5)


sx(T("november", 23.7) - 0.6, "riser", 0.6, dur=0.6)
sx(T("19th", 23.9), "slam", 1.0)
sx(T("2026", 24.9), "pop_big", 0.7)
sx(T("grand", 26.5) - 0.9, "riser", 0.5, dur=1.2)
sx(T("launches", 27.8), "boom", 1.0)
sx(T("launches", 27.8), "car_pass", 0.8, pan=0.4)


# --- G. CEO: no more delays; people calling in sick
def s_ceo(c, t):
    a, b = T("take", 28.9), T("the", 33.0)
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#140a2e", "#05030c"]))
    c.save()
    push(c, t, a, b, 1.0, 1.08)
    for x in (560, 1360):
        spotlight(c, x, 980, 0.1, 300)
    # backdrop screen
    rrect(c, 360, 120, 1200, 520, 20, "#1e1240")
    fill_shader(c, skia.Rect(380, 140, 1540, 620), linear(0, 140, 0, 620, ["#2a0c45", "#b8306c", "#ff8a3c"]))
    c.save()
    c.clipRect(skia.Rect(380, 140, 1540, 620))
    retro_sun(c, 960, 560, 160)
    palms_row(c, t, 640, "#12061f", xs=(470, 1450), scale=0.6)
    c.restore()
    figure(c, W / 2, 830, "ceo", "point" if t > T("plainly", 30.8) else "stand", "smile", t, s=1.3, rim=GOLD,
           talk=0.6 if t < b else 0)
    # podium
    c.drawPath(poly([(W / 2 - 170, 760), (W / 2 + 170, 760), (W / 2 + 140, 1000), (W / 2 - 140, 1000)]), P("#2a1f48"))
    c.drawPath(poly([(W / 2 - 170, 760), (W / 2 + 170, 760), (W / 2 + 140, 1000), (W / 2 - 140, 1000)]),
               P(PINK, 4, 0.8))
    line(c, W / 2, 760, W / 2 + 30, 690, "#888888", 6)
    c.restore()
    # press camera flashes
    rnd = random.Random(int(t * 7))
    if rnd.random() < 0.35:
        glow(c, rnd.uniform(100, W - 100), rnd.uniform(850, 1050), 160, "#ffffff", 0.7)
    stamp(c, t, T("no", 31.7), "NO DELAYS", W / 2, 260, GREEN, 110, end=b + 0.2)


for k in range(10):
    sx(T("take", 28.9) + 0.3 + k * 0.37 + (k % 3) * 0.05, "camera", 0.3, pan=(-0.6 + (k % 5) * 0.3))
sx(T("no", 31.7), "stamp", 1.0)


def s_sick(c, t):
    a, b = T("the", 33.0), T("but", 39.7)
    room_bg(c, t, window_kind="day")
    c.save()
    push(c, t, a, b, 1.0, 1.08)
    couch(c, 760, 960, 1.0)
    tv(c, 1500, 640, 0.75, t=t)
    figure(c, 700, 870, "gamer", "phone" if t < T("honestly", 37.9) else "game", "worried" if t < T("honestly", 37.9)
           else "happy", t, s=0.9, rim=CYAN, talk=0.5 if t < T("day", 36.8) else 0,
           hold=(lambda cc, hx, hy: sgfx.phone(cc, hx, hy - 30, 1.2, rot=-10, glow_a=0.6)) if t < T("honestly", 37.9)
           else (lambda cc, hx, hy: controller(cc, hx, hy, 0.35)))
    # thermometer
    line(c, 735, 615, 800, 640, "#e9eef7", 9)
    c.drawCircle(800, 640, 8, P(RED))
    sk = T("sick", 36.4)
    if t > T("calling", 35.8):
        k = back_out(at(t, T("calling", 35.8), 0.3))
        bubble(c, 980, 330, k, "*cough*", tail=-1)
    if t > sk:
        k = back_out(at(t, sk, 0.3))
        calendar(c, 260, 330, 0.7 * k, "NOV", 19, circle=at(t, sk + 0.2, 0.6))
    c.restore()
    ri = T("right", 39.0)
    if t > T("honestly", 37.9):
        # tiny wink: TV shows the game sunset
        pass
    if t > ri:
        stamp(c, t, ri, "LOL", 1500, 260, GOLD, 80)


sx(T("the", 33.0), "phone_ring", 0.4)
sx(T("calling", 35.8), "cough", 0.7)
sx(T("sick", 36.4) + 0.25, "cough", 0.5)
sx(T("sick", 36.4), "pop", 0.5)
sx(T("honestly", 37.9), "game_start", 0.5)
sx(T("right", 39.0), "rimshot", 0.5)


# --- H. The problem: excitement is expensive; slow down, adults with a budget
def s_hype(c, t):
    a, b = T("but", 39.7), T("so", 47.5)
    grid_board(c, t, col=HOT)
    c.save()
    push(c, t, a, b, 1.0, 1.07)
    ex = T("excitement", 43.2)
    hype = smooth(at(t, T("when", 41.2), 3.5))
    shk = hype * 6
    c.translate(math.sin(t * 50) * shk, math.cos(t * 43) * shk)
    figure(c, 760, 920, "buyer", "cheer" if hype > 0.4 else "stand", "laugh" if hype > 0.4 else "neutral", t, s=1.1,
           rim=PINK)
    # hype meter
    with xf(c, 1320, 560):
        rrect(c, -70, -380, 140, 760, 40, "#000000", 0.7)
        rrect(c, -70, -380, 140, 760, 40, "#ffffff", stroke=5)
        hh = 720 * hype
        fill_shader(c, skia.Rect(-50, 360 - hh, 50, 360), linear(0, 360, 0, -360, [GREEN, GOLD, HOT]))
        ftext(c, "HYPE", 0, 450, 64, "#ffffff", stroke="#000000", sw=8)
    if t > T("expensive", 46.5) - 0.3:
        k = back_out(at(t, T("expensive", 46.5) - 0.3, 0.35))
        wallet(c, 1660, 760, 0.8 * k, burn=1, t=t)
    c.restore()
    if t > T("problem", 40.2) and t < T("when", 41.2):
        tint(c, "#000000", 0.35)
    if t > ex:
        tint(c, HOT, 0.15 * hype * (0.5 + 0.5 * math.sin(t * 10)))


sx(T("problem", 40.2) - 0.15, "scratch", 0.7)
sx(T("when", 41.2), "riser", 0.4, dur=3.5)
sx(T("excitement", 43.2), "heartbeat_fast", 0.6, dur=2.0)
sx(T("expensive", 46.5) - 0.3, "register", 0.6)
sx(T("expensive", 46.5), "fire", 0.5, dur=1.0)


def s_slow(c, t):
    a, b = T("so", 47.5), T("first", 51.5)
    room_bg(c, t, window_kind="dusk", lamp=True)
    c.save()
    push(c, t, a, b, 1.08, 1.0)
    sl = T("slow", 48.0)
    figure(c, 860, 900, "gamer", "think", "neutral", t, s=1.0, rim=CYAN)
    hourglass(c, 1350, 560, 0.9, frac=smooth(at(t, sl, 3.0)), rot=0)
    if t > T("budget", 50.7) - 0.4:
        k = back_out(at(t, T("budget", 50.7) - 0.4, 0.35))
        wallet(c, 420, 520, 0.7 * k, t=t)
        check(c, 420, 330, 0.9 * k)
    c.restore()
    if t < sl + 0.8:
        tint(c, "#000000", 0.4 * clamp(1 - (t - sl) / 0.8))


sx(T("slow", 48.0), "tape_slow", 0.6)
sx(T("budget", 50.7) - 0.4, "ding", 0.5)


# --- I. Platforms
def s_platforms(c, t):
    a, b = T("first", 51.5), T("if", 65.4)
    grid_board(c, t, col=CYAN)
    c.save()
    push(c, t, a, b, 1.0, 1.06)
    chip(c, W / 2, 140, "FACT #1", GOLD, size=56, sc=back_out(at(t, T("fact", 52.5) - 0.3, 0.3)))
    ps = T("playstation", 55.3)
    xb = T("xbox", 56.6)
    pc = T("pc", 60.2)
    p4 = T("4", 62.8)
    x1 = T("one", 64.5)
    # current gen pair
    for i, (st, x, fn, lab, gc) in enumerate(((ps, 520, console_tall, "PS5", CYAN),
                                               (xb, 940, console_box, "XBOX SERIES X|S", GREEN))):
        if st - 0.25 < t < p4 - 0.45:
            k = back_out(at(t, st - 0.25, 0.45))
            pedestal(c, x, 830, 300, gc)
            fn(c, x, 830 + (1 - k) * 300, 0.95 * k, glow_c=gc)
            chip(c, x, 930, lab, "#ffffff", size=36, a=clamp(k))
            if t > T("it", 59.3):
                check(c, x + 130, 380, 0.8 * back_out(at(t, T("it", 59.3) + i * 0.12, 0.3)))
    # no PC
    if pc - 0.2 < t < p4 - 0.45:
        k = back_out(at(t, pc - 0.2, 0.4))
        with xf(c, 1480, 780, 0.75 * k):
            pc_tower(c, 0, 0, 1.0, a=0.85)
        xmark(c, 1500, 500, 1.2 * back_out(at(t, pc + 0.2, 0.3)), a=clamp(k))
    c.restore()
    # last gen falls in front and cracks
    if t > p4 - 0.5:
        tint(c, "#000000", 0.35 * clamp((t - p4 + 0.5) / 0.3))
        for st, x, kind in ((p4 - 0.4, 640, 0), (x1 - 0.4, 1280, 1)):
            if t > st:
                k = clamp((t - st) / 0.35)
                y = lerp(-200, 760, k ** 2)
                console_old(c, x, lerp(-200, 840, k ** 2) if False else y + 60, 1.7, crack=clamp((t - st - 0.4) * 2), kind=kind)
                if t > st + 0.45:
                    xmark(c, x, 520, 1.0 * back_out(at(t, st + 0.45, 0.25)))
        if t < p4 + 0.6:
            c.translate(*shake(t, p4, 0.3, 14))


sx(T("fact", 52.5) - 0.3, "pop_big", 0.5)
sx(T("playstation", 55.3) - 0.25, "power_on", 0.7, pan=-0.4)
sx(T("xbox", 56.6) - 0.25, "power_on", 0.7, pan=0.0)
sx(T("it", 59.3), "ding", 0.4)
sx(T("it", 59.3) + 0.12, "ding", 0.35)
sx(T("pc", 60.2) - 0.2, "whoosh", 0.4, pan=0.5)
sx(T("pc", 60.2) + 0.2, "buzzer", 0.5, pan=0.5)
sx(T("4", 62.8) - 0.05, "thud_crack", 0.8, pan=-0.3)
sx(T("one", 64.5) - 0.05, "thud_crack", 0.8, pan=0.3)


def s_lastgen(c, t):
    a, b = T("if", 65.4), T("so", 70.4)
    room_bg(c, t)
    c.save()
    push(c, t, a, b, 1.0, 1.1, cx=900)
    nt = T("not", 69.2)
    tv(c, 1180, 560, 1.0, t=t, screen=(lambda cc: (fill_shader(cc, skia.Rect(-312, -192, 312, 152),
                                                                linear(0, -192, 0, 152, ["#121018", "#202030"])),
                                                    xmark(cc, 0, -20, 1.4 * back_out(at(t, nt, 0.3)),
                                                          a=1.0 if t > nt else 0.0),
                                                    progress_bar(cc, 0, 90, 420, smooth(at(t, a + 1.0, 3.0)) * 0.12,
                                                                 RED, a=1.0 if t < nt else 0.3))))
    console_old(c, 1180, 860, 0.8, crack=0, kind=0)
    figure(c, 520, 920, "buyer", "point" if t < nt else "headhold", "wide" if t < nt else "scared", t, s=1.0,
           rim=PINK, face=1)
    c.restore()


sx(T("generation", 67.1), "hum_old", 0.4, dur=2.0)
sx(T("not", 69.2), "error", 0.7)


# --- J. First question: do you own one?  YES → relax.  NO → iceberg
def s_question(c, t):
    a, b = T("so", 70.4), T("if", 76.3)
    grid_board(c, t, col=GOLD)
    c.save()
    push(c, t, a, b, 1.0, 1.06)
    # fork road on a map
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, [("#000000", 0), ("#000000", 0.4)]))
    pth = skia.Path()
    pth.moveTo(W / 2, H + 40)
    pth.lineTo(W / 2, 640)
    pth.quadTo(W / 2, 480, 520, 360)
    p2 = skia.Path()
    p2.moveTo(W / 2, 640)
    p2.quadTo(W / 2, 480, 1400, 360)
    k = smooth(at(t, a + 0.2, 1.2))
    for pp, col in ((pth, GREEN), (p2, HOT)):
        c.drawPath(pp, P("#000000", 120, 0.6))
        c.drawPath(pp, P(col, 90 * k, 0.9))
        c.drawPath(pp, P("#ffffff", 6, 0.6 * k))
    if t > T("own", 73.1):
        kk = back_out(at(t, T("own", 73.1), 0.35))
        console_tall(c, 760, 420, 0.65 * kk, glow_c=CYAN)
        console_box(c, 1160, 420, 0.7 * kk, glow_c=GREEN)
        qmark(c, 960, 200, 170 * kk, GOLD, t=t)
    c.restore()
    figure(c, W / 2, 1040, "hero", "think", "neutral", t, s=0.75, rim=GOLD)
    minimap(c, t, heading=0, blip=(-60, -60, GOLD))


sx(T("first", 70.7), "map_open", 0.6)
sx(T("own", 73.1), "pop_big", 0.5)


def s_relax(c, t):
    a, b = T("if", 76.3), T("but", 84.1)
    room_bg(c, t, window_kind="dusk")
    c.save()
    push(c, t, a, b, 1.0, 1.06)
    tv(c, 1400, 620, 0.8, t=t, screen=lambda cc: (scene_mini(cc, t)))
    console_tall(c, 1730, 830, 0.35, glow_c=CYAN)
    couch(c, 620, 970, 1.0, "#2f5a6a")
    figure(c, 600, 880, "hero", "game" if t > T("relax", 76.9) else "sit", "happy", t, s=0.9, rim=TEAL,
           hold=lambda cc, hx, hy: controller(cc, hx, hy, 0.32))
    c.restore()
    if t > T("yes", 76.6):
        stamp(c, t, T("yes", 76.6), "YES", 1400, 210, GREEN, 100, end=T("close", 80.6))
    # fake video player close button
    cl = T("close", 80.6)
    if t > cl - 0.3:
        k = ease_out(at(t, cl - 0.3, 0.3))
        with xf(c, W - 140, 300, k):
            c.drawCircle(0, 0, 60, P("#000000", a=0.7))
            c.drawCircle(0, 0, 60, P("#ffffff", 5))
            line(c, -22, -22, 22, 22, "#ffffff", 9)
            line(c, -22, 22, 22, -22, "#ffffff", 9)
        # cursor glide
        cx = lerp(W - 600, W - 130, smooth(at(t, cl - 0.3, 0.5)))
        cy = lerp(650, 310, smooth(at(t, cl - 0.3, 0.5)))
        c.drawPath(poly([(cx, cy), (cx, cy + 60), (cx + 16, cy + 46), (cx + 28, cy + 72), (cx + 38, cy + 66),
                         (cx + 26, cy + 42), (cx + 46, cy + 42)]), P("#ffffff"))
    kp = T("keep", 82.2)
    if t > kp:
        ticker(c, t, kp, 1250, 1250, 0.1)
        k = back_out(at(t, kp, 0.3))
        wallet(c, 1500, 900, 0.6 * k, t=t)
        check(c, 1640, 760, 0.7 * k)


def scene_mini(cc, t):
    with xf(cc, -312, -192, sx=624 / W, sy=344 / H):
        scene_coast(cc, t, "dusk", cam=t * 50, car_x=(t * 400) % 2400 - 300)


sx(T("yes", 76.6), "stamp", 0.8)
sx(T("relax", 76.9), "sigh_pad", 0.5)
sx(T("close", 80.6) + 0.1, "click", 0.7)
sx(T("keep", 82.2), "coin_in", 0.6)


def s_iceberg(c, t):
    a, b = T("but", 84.1), T("let's", 90.1)
    fill_shader(c, skia.Rect(0, 0, W, 520), linear(0, 0, 0, 520, ["#1a0b3b", "#ff6b4a"]))
    fill_shader(c, skia.Rect(0, 520, W, H), linear(0, 520, 0, H, ["#123a6a", "#020814"]))
    c.save()
    rv = T("real", 88.9)
    cam_y = -260 * smooth(at(t, rv - 0.4, 1.2))
    c.translate(0, cam_y)
    push(c, t, a, b, 1.15, 1.0, cy=520)
    iceberg(c, W / 2, 520, 1.3, t, reveal=smooth(at(t, T("not", 88.4), 0.8)))
    price_tag(c, W / 2 + 40, 300, 0.8 * back_out(at(t, T("console", 87.7), 0.3)), "CONSOLE", GOLD, rot=-6)
    if t > rv:
        rnd = random.Random(3)
        icons = ["$", "$$", "$$$", "+", "$", "$$"]
        for i, s in enumerate(icons):
            k = back_out(at(t, rv + i * 0.12, 0.3))
            x = W / 2 + rnd.uniform(-330, 330)
            y = 720 + rnd.uniform(0, 380)
            ftext(c, s, x, y, 90 * k, GOLD, stroke="#000000", sw=8)
    c.restore()
    if t > T("interesting", 86.1) - 0.3 and t < T("because", 87.3):
        tint(c, "#000000", 0.25)


sx(T("but", 84.1), "whoosh", 0.6)
sx(T("interesting", 86.1), "dun", 0.7)
sx(T("console", 87.7), "pop", 0.5)
sx(T("real", 88.9) - 0.4, "underwater", 0.7)
for i in range(6):
    sx(T("real", 88.9) + i * 0.12, "pop", 0.25)


# --- K. Game price $80, +$10, gamers not happy
def s_price(c, t):
    a, b = T("let's", 90.1), T("and", 100.0)
    grid_board(c, t, col=GOLD)
    c.save()
    push(c, t, a, b, 1.0, 1.08)
    rays(c, 700, 540, t, GOLD, 0.06)
    spin = (1 - ease_out(at(t, a, 1.0))) * 2.5
    with xf(c, 700, 540, 1.0, sx=max(0.05, abs(math.cos(spin * math.pi))), sy=1.0):
        game_case(c, 0, 0, 1.25, t=t)
    e = T("$80", 95.2)
    if t > e - 0.1:
        price_tag(c, 1250, 420, 1.3 * back_out(at(t, e - 0.1, 0.3)), "$80", GOLD)
    if t > T("$10", 97.2):
        k = back_out(at(t, T("$10", 97.2), 0.3))
        price_tag(c, 1300, 700, 0.8 * k, "$70", "#9aa0b5", rot=4)
        line(c, 1140, 700, 1460, 690, RED, 14, clamp(k))
        chip(c, 1560, 560, "+$10", HOT, "#ffffff", 64, sc=k)
    c.restore()


sx(T("let's", 90.1), "spin", 0.6)
sx(T("$80", 95.2) - 0.1, "slam", 0.9)
sx(T("$80", 95.2), "register", 0.5)
sx(T("$10", 97.2), "pop_big", 0.6)


def s_angry(c, t):
    a, b = T("and", 100.0), T("now", 102.3)
    scene_street(c, t, "night")
    c.save()
    push(c, t, a, b, 1.05, 1.0)
    rnd = random.Random(5)
    for i in range(9):
        x = 160 + i * 200
        jump = abs(math.sin(t * 6 + i)) * 30
        figure(c, x, 1000 - jump, ("buyer", "buyer2", "buyer3", "gamer")[i % 4], "cheer" if i % 2 else "stop", "angry",
               t + i, s=0.55, face=1 if i < 4 else -1, rim=HOT)
    for i in range(6):
        st = a + 0.15 + i * 0.22
        if t > st:
            k = back_out(at(t, st, 0.25))
            bubble(c, 200 + i * 300 + rnd.uniform(-40, 40), 330 + rnd.uniform(-80, 80), k * 0.9,
                   ("!!", "$80?!", "!!!", ">:(", "NO", "?!")[i], bg=("#ffffff", GOLD)[i % 2], tail=1 if i % 2 else -1)
    c.restore()


sx(T("gamers", 100.2), "crowd_angry", 0.6, dur=2.2)
for i in range(6):
    sx(T("and", 100.0) + 0.15 + i * 0.22, "pop", 0.3, pan=-0.6 + i * 0.24)


# --- L. Add the console: prices change, bundles, check price, few hundred before the game loads
def s_console_cost(c, t):
    a, b = T("now", 102.3), T("and", 114.7)
    grid_board(c, t, col=PINK)
    c.save()
    push(c, t, a, b, 1.0, 1.06)
    ad = T("add", 102.5)
    k = clamp((t - ad) / 0.5)
    pedestal(c, 520, 800, 280, CYAN)
    console_tall(c, 520, lerp(-200, 800, k ** 2), 0.75, glow_c=CYAN)
    pr = T("prices", 103.9)
    if t > pr:
        rnd = random.Random(int(t * 8) if t < T("bundles", 106.0) else 3)
        val = rnd.choice(("$449", "$499", "$549", "$399", "$599", "$479"))
        price_tag(c, 1020, 380, 1.0 * back_out(at(t, pr, 0.3)), val, GOLD, rot=-6)
    bd = T("bundles", 106.0)
    if t > bd:
        kk = back_out(at(t, bd, 0.35))
        gift(c, 1500, 800, 0.9 * kk, color=PURPLE)
        chip(c, 1500, 880, "BUNDLE", GOLD, size=40, sc=kk)
    ch = T("check", 107.0)
    if t > ch:
        kk = back_out(at(t, ch, 0.3))
        sgfx.phone(c, 1050, 700, 2.2 * kk, rot=8, glow_a=0.8)
        check(c, 1090, 650, 0.6 * kk)
    c.restore()
    bs = T("basic", 110.3)
    if t > bs - 0.3:
        tint(c, "#000000", 0.6 * clamp((t - bs + 0.3) / 0.3))
        receipt(c, W / 2 - 260, 140, [("Console", "$$$"), ("Game", "$80")], k=smooth(at(t, bs - 0.3, 0.8)),
                total="$$$+" if t > T("hundred", 112.2) else None)
        ld = T("loads", 113.8)
        progress_bar(c, W / 2 + 470, 520, 520, 0.03 * smooth(at(t, T("game", 113.3), 1.0)), TEAL,
                     a=clamp((t - T("before", 112.8)) * 3), label="LOADING...")


sx(T("add", 102.5), "drop_whoosh", 0.6)
sx(T("add", 102.5) + 0.5, "thud", 0.7)
for i in range(14):
    sx(T("prices", 103.9) + i * 0.125, "tick_ui", 0.3)
sx(T("bundles", 106.0), "pop_big", 0.6)
sx(T("check", 107.0), "notify", 0.5)
sx(T("basic", 110.3) - 0.3, "printer", 0.5, dur=1.0)
sx(T("hundred", 112.2), "register", 0.6)


# --- M. Extras: controller, storage, subscription, monthly → many hundred
def s_extras(c, t):
    a, b = T("and", 114.7), T("if", 129.5)
    grid_board(c, t, col=TEAL)
    c.save()
    push(c, t, a, b, 1.0, 1.05)
    co = T("controller", 117.4)
    st = T("storage", 120.4)
    on = T("online", 124.9)
    sub = T("subscription", 128.2)
    items = [(co, 380, lambda cc, x, y, k: controller(cc, x, y, 0.85 * k), "+ CONTROLLER"),
             (st, 960, lambda cc, x, y, k: ssd(cc, x, y, 1.0 * k), "+ STORAGE"),
             (on, 1540, lambda cc, x, y, k: (wifi(cc, x, y + 60, 1.0 * k, 3, color=CYAN),
                                              calendar(cc, x + 170, y - 120, 0.45 * k, "MONTH", "$", t=t)),
              "+ ONLINE")]
    for st_t, x, fn, lab in items:
        if t > st_t - 0.2:
            k = back_out(at(t, st_t - 0.2, 0.4))
            pedestal(c, x, 760, 340, TEAL)
            fn(c, x, 560, k)
            chip(c, x, 880, lab, GOLD, size=38, sc=k)
    # family playing together
    fam = T("family", 118.4)
    if fam < t < st - 0.2:
        figure(c, 150, 1060, "parent", "cheer", "happy", t, s=0.62, rim=CYAN)
        figure(c, 620, 1060, "teen", "cheer", "laugh", t, s=0.62, rim=CYAN, face=-1)
    hd = T("huge", 123.1)
    if hd < t < on - 0.2:
        progress_bar(c, 960, 260, 700, 0.06 * smooth(at(t, hd, 1.5)), TEAL, label="DOWNLOAD 0%")
    c.restore()
    ticker(c, t, co, 80, 80, 0.1)
    vals = [(co, 80, 150), (st, 150, 400), (sub, 400, 480)]
    v = 80
    for s0, v0, v1 in vals:
        if t > s0:
            v = lerp(v0, v1, smooth(at(t, s0, 0.8)))
    money_hud(c, v, t, color="#ff6b6b")


sx(T("then", 114.9), "whoosh", 0.5)
sx(T("controller", 117.4) - 0.2, "pop_big", 0.6)
sx(T("controller", 117.4), "register", 0.4)
sx(T("family", 118.4), "kids_yay", 0.4)
sx(T("storage", 120.4) - 0.2, "pop_big", 0.6)
sx(T("storage", 120.4), "register", 0.4)
sx(T("huge", 123.1), "download_blips", 0.4, dur=1.4)
sx(T("online", 124.9) - 0.2, "pop_big", 0.6)
sx(T("subscription", 128.2), "register", 0.5)


def s_monthly(c, t):
    a, b = T("if", 129.5), T("and", 142.8)
    sky(c, "night", H, t)
    c.save()
    push(c, t, a, b, 1.0, 1.08)
    # globe with connected friends
    gx, gy, gr = W / 2, 600, 300
    glow(c, gx, gy, gr * 1.6, CYAN, 0.25)
    c.drawCircle(gx, gy, gr, P("#10304f"))
    for i in range(-3, 4):
        c.drawOval(skia.Rect(gx - gr * abs(math.cos(t * 0.5 + i * 0.45)), gy - gr, gx + gr * abs(math.cos(t * 0.5 + i * 0.45)),
                             gy + gr), P(CYAN, 2, 0.35))
        line(c, gx - gr * math.cos(i * 0.4), gy + i * 80, gx + gr * math.cos(i * 0.4), gy + i * 80, CYAN, 2, 0.35)
    c.drawCircle(gx, gy, gr, P(CYAN, 5, 0.8))
    pos = [(-560, -250), (560, -250), (-640, 150), (640, 150), (0, -440)]
    fr = T("friends", 136.8)
    for i, (dx, dy) in enumerate(pos):
        st = T("online", 131.0) + i * 0.25
        if t > st:
            k = back_out(at(t, st, 0.35))
            line(c, gx, gy, gx + dx, gy + dy, PINK, 4, 0.6 * clamp(k))
            c.drawCircle(gx + dx, gy + dy, 90 * k, P("#1c1236"))
            c.drawCircle(gx + dx, gy + dy, 90 * k, P(PINK, 5))
            head_only(c, gx + dx, gy + dy + 10, ("buyer", "buyer2", "buyer3", "gamer", "hero")[i], "happy", t,
                      r=50 * k, rim=PINK)
    # monthly coins draining
    mo = T("monthly", 135.4)
    if t > mo - 0.6:
        for i in range(8):
            ph = ((t - mo + 0.6) * 1.2 + i / 8) % 1.0
            coin(c, W - 260 + math.sin(i) * 40, lerp(300, 1000, ph), 34, a=1 - ph, spin=t * 6 + i)
        calendar(c, W - 260, 220, 0.5, "MONTHLY", "$", t=t, color=PURPLE)
    c.restore()
    big = T("$80", 138.1)
    if t > big - 0.1:
        tint(c, "#000000", 0.7 * clamp((t - big + 0.1) / 0.3))
        k = smooth(at(t, T("become", 140.3), 1.6))
        if k <= 0:
            slam_title(c, t, big - 0.1, "$80", W / 2, H / 2, 260, color=GOLD)
        else:
            s = "$80" if k < 0.05 else "$" + "$" * int(1 + k * 3)
            sc = 1 + 0.25 * k
            with xf(c, W / 2, H / 2, sc):
                ftext(c, s if k < 1 else "$$$$", 0, 90, 260, mixhex(GOLD, HOT, k), stroke="#000000", sw=24)
            receipt(c, 260, 120 + (1 - k) * 500, [("Game", "$80"), ("Console", "$$$"), ("Controller", "$"),
                                                   ("Storage", "$$"), ("Online", "$/mo")], k=k, a=k)


sx(T("online", 131.0), "connect", 0.4)
for i in range(5):
    sx(T("online", 131.0) + i * 0.25, "pop", 0.3, pan=-0.6 + i * 0.3)
for i in range(4):
    sx(T("monthly", 135.4) - 0.4 + i * 0.3, "coin_out", 0.35)
sx(T("$80", 138.1) - 0.1, "slam", 0.8)
sx(T("become", 140.3), "riser", 0.5, dur=1.5)
sx(T("purchase", 141.8), "register", 0.8)


# --- N. The detail: no disc in the box — just a download code
def s_detail(c, t):
    a, b = T("and", 142.8), T("so", 153.6)
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#07040f", "#120a26"]))
    c.save()
    push(c, t, a, b, 1.0, 1.12, cy=H * 0.55)
    unl = T("promised", 144.2)
    nd = T("no", 148.7)
    lid = 0.0
    if t > T("physical", 147.3):
        lid = smooth(at(t, T("physical", 147.3), 0.9))
    cd = T("code", 152.8)
    dl = T("download", 152.5)

    def inside(cc):
        if t > nd:
            # empty tray with a faint disc outline
            cc.drawCircle(0, 0, 120, P("#ffffff", 4, 0.25))
            cc.drawCircle(0, 0, 36, P("#ffffff", 3, 0.2))
        if t > dl - 0.6:
            k = smooth(at(t, dl - 0.6, 0.6))
            code_card(cc, 0, 40 - 60 * k, 0.75, reveal=at(t, dl, 0.8))
        else:
            glow(cc, 0, 0, 220, GOLD, 0.5 * lid)

    game_box_pedestal(c, W / 2, 760, t, lid=lid, spot=1.0, rattle=0.0, inside=inside)
    if t < T("physical", 147.3) + 0.4:
        pk = clamp((t - unl) / 0.4)
        padlock(c, W / 2 + 150, 560 - pk * 40, 0.8, a=1 - clamp((t - unl - 0.6) / 0.4), closed=1 - pk)
    c.restore()
    if t > nd:
        k = back_out(at(t, nd, 0.3))
        with xf(c, 360, 420, k):
            disc(c, 0, 0, 150, rot=t * 90)
            xmark(c, 0, 0, 1.4)
    if t > cd:
        k = back_out(at(t, cd, 0.3))
        chip(c, 1500, 360, "CODE ONLY", GOLD, size=60, sc=k)


sx(T("detail", 143.6), "drone", 0.45, dur=4.0)
sx(T("promised", 144.2) + 0.1, "unlock", 0.8)
sx(T("physical", 147.3), "creak", 0.6)
sx(T("no", 148.7), "hit_low", 0.9)
sx(T("no", 148.7) + 0.05, "buzzer", 0.4)
sx(T("download", 152.5) - 0.6, "slide", 0.5)
for i in range(8):
    sx(T("download", 152.5) + i * 0.1, "type", 0.35)
sx(T("code", 152.8), "pop_big", 0.6)


def s_nodisc(c, t):
    a, b = T("so", 153.6), T("that", 161.0)
    grid_board(c, t, col=PURPLE)
    c.save()
    push(c, t, a, b, 1.0, 1.05)
    wt = T("waiting", 159.1)
    if t < wt - 0.4:
        disc(c, W / 2, 380, 170, rot=t * 60)
        acts = [(T("keep", 155.2), 460, "KEEP"), (T("trade", 155.4) + 0.25, 960, "TRADE"),
                (T("lend", 156.1), 1460, "LEND")]
        for st, x, lab in acts:
            if t > st:
                k = back_out(at(t, st, 0.3))
                chip(c, x, 820, lab, "#ffffff", size=64, sc=k)
                xmark(c, x, 650, 0.8 * back_out(at(t, st + 0.15, 0.25)))
        if t > T("code", 158.2) - 0.4:
            k = back_out(at(t, T("code", 158.2) - 0.4, 0.3))
            code_card(c, W / 2, 380, 1.2 * k, rot=-4)
    else:
        # waiting for a massive download
        room_bg(c, t)
        couch(c, 560, 990, 0.9)
        tv(c, 1300, 560, 0.95, t=t, screen=lambda cc: (fill_shader(cc, skia.Rect(-312, -192, 312, 152),
                                                                     linear(0, -192, 0, 152, ["#10121c", "#1c2033"])),
                                                         progress_bar(cc, 0, -10, 460,
                                                                      0.01 + 0.03 * at(t, wt, 3.0), TEAL)))
        figure(c, 520, 920, "gamer", "sit", "sad", t, s=0.9, rim=CYAN)
        hourglass(c, 520, 380, 0.6, frac=at(t, wt, 2.5), rot=0)
    c.restore()


sx(T("keep", 155.2), "buzzer_short", 0.4, pan=-0.5)
sx(T("trade", 155.4) + 0.25, "buzzer_short", 0.4)
sx(T("lend", 156.1), "buzzer_short", 0.4, pan=0.5)
sx(T("code", 158.2) - 0.4, "pop_big", 0.5)
sx(T("waiting", 159.1) - 0.4, "whoosh", 0.5)
sx(T("massive", 159.8), "clock_slow", 0.5, dur=1.2)


# --- O. That changes things: internet, storage, no reselling
def s_changes(c, t):
    a, b = T("that", 161.0), T("second", 172.2)
    grid_board(c, t, col=CYAN)
    c.save()
    push(c, t, a, b, 1.0, 1.05)
    it = T("internet", 163.3)
    sl = T("slow", 165.6)
    dc = T("data", 166.7)
    if t > it - 0.3:
        k = back_out(at(t, it - 0.3, 0.35))
        bars = 3 if t < sl else 1
        wifi(c, 560, 640, 1.8 * k, bars, color=GREEN if t < sl else RED)
        chip(c, 560, 820, "INTERNET", "#ffffff", size=50, sc=k)
        if t > sl:
            ftext(c, "0.4 MB/s", 560, 300, 60, RED, "InterDisplay-Black", stroke="#000000", sw=8,
                  a=clamp((t - sl) * 3))
    if t > dc:
        k = back_out(at(t, dc, 0.35))
        # data-cap meter
        with xf(c, 1360, 560, k):
            fill = smooth(at(t, T("hours", 169.5) - 0.5, 2.0))
            rrect(c, -340, -60, 680, 120, 60, "#000000", 0.7)
            rrect(c, -340, -60, 680, 120, 60, "#ffffff", stroke=6)
            c.save()
            c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-330, -50, 660, 100), 50, 50),
                        skia.ClipOp.kIntersect, True)
            fill_shader(c, skia.Rect(-330, -50, -330 + 660 * fill, 50), linear(-330, 0, 330, 0, [GREEN, GOLD, RED]))
            c.restore()
            ftext(c, "DATA CAP", 0, -100, 52, "#ffffff", stroke="#000000", sw=8)
            if fill > 0.95:
                stamp(c, t, T("limit", 171.2) - 0.1, "FULL", 0, 200, RED, 70)
        # clock spinning (hours)
        hs = T("hours", 169.5)
        if t > hs:
            with xf(c, 1360, 300, back_out(at(t, hs, 0.3)) * 0.8):
                c.drawCircle(0, 0, 90, P("#ffffff"))
                c.drawCircle(0, 0, 90, P("#000000", 8))
                ang = (t - hs) * 12
                line(c, 0, 0, math.sin(ang) * 70, -math.cos(ang) * 70, "#000000", 8)
                line(c, 0, 0, math.sin(ang / 12) * 45, -math.cos(ang / 12) * 45, RED, 10)
    c.restore()
    if a <= t < it - 0.3:
        for i in range(3):
            card_panel(c, 460 + i * 500, 540, 380, 380, t, a + 0.15 * i, i + 1,
                       lambda cc, i=i: [wifi(cc, 0, 60, 1.0, 3, color=CYAN) if i == 0 else
                                        ssd(cc, 0, 30, 0.5) if i == 1 else disc(cc, 0, 30, 110)])


sx(T("that", 161.0), "cards", 0.6)
sx(T("internet", 163.3) - 0.3, "pop_big", 0.5)
sx(T("slow", 165.6), "power_down", 0.5)
sx(T("data", 166.7), "pop_big", 0.5)
sx(T("hours", 169.5), "clock_fast", 0.4, dur=1.6)
sx(T("limit", 171.2) - 0.1, "stamp", 0.8)


def s_storage(c, t):
    a, b = T("second", 172.2), T("the", 184.5)
    grid_board(c, t, col=PINK)
    c.save()
    push(c, t, a, b, 1.0, 1.05)
    th = T("third", 180.0)
    if t < th - 0.3:
        fu = T("full", 175.7)
        dl = T("delete", 177.0)
        by = T("buy", 178.2)
        # storage bar
        fill = 0.4 + 0.58 * smooth(at(t, T("console", 174.8), 1.0))
        if t > dl:
            fill -= 0.3 * smooth(at(t, dl, 0.8))
        progress_bar(c, W / 2, 260, 1100, fill, RED if fill > 0.9 else TEAL, h=80, label="STORAGE")
        if t > fu:
            stamp(c, t, fu, "FULL", W / 2 + 620, 200, RED, 70, end=dl)
        # games being deleted into a bin
        rnd = random.Random(2)
        for i in range(4):
            st = dl + i * 0.2
            x = 420 + i * 220
            if t < st:
                game_case(c, x, 620, 0.5, t=t)
            elif t < st + 0.8:
                k = (t - st) / 0.8
                game_case(c, lerp(x, 1250, k), 620 + k * 220 - math.sin(k * math.pi) * 200, 0.5 * (1 - k * 0.5),
                          rot=k * 180, t=t)
        if t > dl - 0.3:
            with xf(c, 1250, 820, back_out(at(t, dl - 0.3, 0.3))):
                c.drawPath(poly([(-110, -120), (110, -120), (90, 120), (-90, 120)]), P("#3a3f4c"))
                rrect(c, -130, -150, 260, 36, 10, "#555b6a")
        if t > by:
            k = back_out(at(t, by, 0.35))
            ssd(c, 1620, 640, 0.9 * k, rot=-8)
            chip(c, 1620, 760, "+ $$", GOLD, size=46, sc=k)
    else:
        # no reselling
        storefront(c, W / 2, 1020, 0.85, t, sign="TRADE-IN")
        disc(c, W / 2, 280, 130, rot=t * 80)
        if t > T("no", 181.0):
            xmark(c, W / 2, 280, 1.5 * back_out(at(t, T("no", 181.0), 0.3)))
        figure(c, 300, 1020, "gamer", "shrug", "sad", t, s=0.75, rim=CYAN)
    c.restore()


sx(T("second", 172.2), "whoosh", 0.4)
sx(T("full", 175.7), "error", 0.6)
for i in range(4):
    sx(T("delete", 177.0) + i * 0.2 + 0.6, "trash", 0.45)
sx(T("buy", 178.2), "register", 0.5)
sx(T("third", 180.0) - 0.3, "whoosh", 0.5)
sx(T("no", 181.0), "buzzer", 0.5)


# --- P. Preload Nov 12 — the smart move
def s_preload(c, t):
    a, b = T("and", 197.3), T("so", 202.1)
    a0 = T("the", 184.5)
    if t < a:
        grid_board(c, t, col=GREEN)
        c.save()
        push(c, t, a0, a, 1.0, 1.06)
        wk = T("week", 186.3)
        nv = T("november", 188.2)
        # calendar flips 19 → 12
        day = 19
        if t > wk:
            day = max(12, 19 - int((t - wk) * 7))
        calendar(c, 520, 520, 1.3 * back_out(at(t, a0, 0.35)), "NOV", day, circle=at(t, nv + 0.2, 0.6), color=GREEN)
        dl = T("download", 191.4)
        if t > T("digitally", 189.9) - 0.2:
            k = smooth(at(t, dl, 2.2))
            progress_bar(c, 1300, 420, 760, k, GREEN, h=70, label=f"PRELOAD {int(k * 100)}%")
            console_box(c, 1300, 880, 0.7, glow_c=GREEN)
        un = T("unlocks", 193.5)
        if t > un - 0.2:
            pk = clamp((t - un + 0.2) / 0.4)
            padlock(c, 1300, 650, 0.7, closed=1 - pk, color=GREEN)
        if t > un + 0.2:
            rays(c, 1300, 600, t, GREEN, 0.08 * clamp((t - un) * 2))
        c.restore()
        banner(c, t, T("smart", 195.0) - 0.1, "SMART MOVE", None, GREEN, end=T("do", 196.3), y=880)
        if t > T("do", 196.3):
            stamp(c, t, T("do", 196.3), "DO IT", W / 2, 880, GOLD, 100, rot=-6)
    else:
        # split: others stuck on a progress bar | you, already playing
        c.save()
        sgfx.clip_half(c, 0, seed=5)
        room_bg(c, t, window_kind="night")
        tint(c, "#000000", 0.4)
        tv(c, 560, 520, 0.8, t=t, screen=lambda cc: (fill_shader(cc, skia.Rect(-312, -192, 312, 152),
                                                                   linear(0, -192, 0, 152, ["#10121c", "#1c2033"])),
                                                       progress_bar(cc, 0, -10, 420, 0.07, RED)))
        figure(c, 340, 980, "buyer", "headhold", "sad", t, s=0.7, rim=PINK)
        figure(c, 700, 990, "buyer3", "stand", "worried", t, s=0.62, rim=PINK)
        c.restore()
        c.save()
        sgfx.clip_half(c, 1, seed=5)
        room_bg(c, t, window_kind="night")
        tv(c, 1440, 520, 0.8, t=t, screen=lambda cc: scene_mini(cc, t))
        figure(c, 1450, 990, "hero", "game", "laugh", t, s=0.7, rim=TEAL, hold=lambda cc, hx, hy:
               controller(cc, hx, hy, 0.3))
        c.restore()
        sgfx.jagged_split(c, seed=5, color="#000000", w=14)


sx(T("the", 184.5), "pop_big", 0.5)
for i in range(7):
    sx(T("week", 186.3) + i / 7, "page_flip", 0.35)
sx(T("november", 188.2) + 0.2, "marker", 0.5)
sx(T("download", 191.4), "download_blips", 0.45, dur=2.2)
sx(T("unlocks", 193.5) - 0.2, "unlock", 0.8)
sx(T("unlocks", 193.5), "success", 0.8)
sx(T("smart", 195.0) - 0.1, "banner", 0.8)
sx(T("do", 196.3), "stamp", 0.8)
sx(T("and", 197.3), "whoosh", 0.5)
sx(T("playing", 201.2) - 0.8, "game_start", 0.5, pan=0.5)


# --- Q. Who should buy? parent / veteran / curious
def s_who(c, t):
    a, b = T("so", 202.1), T("if", 204.8)
    grid_board(c, t, col=GOLD)
    char_wheel(c, t, a, [("parent", "neutral"), ("gamer", "neutral"), ("buyer2", "neutral")], sel_t=None)
    qmark(c, W / 2, 300, 180, GOLD, t=t)


sx(T("so", 202.1), "wheel", 0.6)


def s_parent(c, t):
    a, b = T("if", 204.8), T("if", 219.3)
    room_bg(c, t, window_kind="day")
    c.save()
    push(c, t, a, b, 1.0, 1.06)
    pa = T("pause", 208.4)
    tt_ = t if t < pa else pa + (t - pa) * (0.0 if t < T("this", 209.5) else 1.0)
    figure(c, 620, 920, "parent", "hold", "happy", tt_, s=1.0, rim=GOLD,
           hold=lambda cc, hx, hy: gift(cc, hx + 40, hy + 120, 0.6, lid=0.0))
    if t > T("teenager", 207.5) - 0.3:
        figure(c, 1150, 940, "teen", "cheer", "laugh", tt_, s=0.95, rim=GOLD, face=-1)
    ra = T("rated", 210.1)
    if t > ra:
        shield_badge(c, 1550, 420, 1.1 * back_out(at(t, ra, 0.35)), "18+", RED)
    fr = T("family", 213.3)
    if t > fr:
        k = back_out(at(t, fr, 0.35))
        with xf(c, 330, 380, k):
            rrect(c, -170, -180, 340, 360, 20, "#fbf6ee")
            rrect(c, -170, -180, 340, 70, 20, PURPLE)
            ftext(c, "RULES", 0, -125, 46, "#ffffff")
            for i in range(3):
                check(c, -110, -40 + i * 80, 0.35 * clamp((t - fr - 0.3 - i * 0.25) * 4))
                rrect(c, -60, -52 + i * 80, 190, 18, 9, "#c9c2b5")
    pc_ = T("parental", 216.4)
    if t > pc_:
        padlock(c, 1550, 820, 0.75 * back_out(at(t, pc_, 0.35)), closed=smooth(at(t, pc_ + 0.4, 0.3)), color=GOLD)
    c.restore()
    if pa <= t < T("this", 209.5):
        tint(c, "#000000", 0.45)
        with xf(c, W / 2, H / 2, back_out(at(t, pa, 0.25))):
            rrect(c, -110, -140, 80, 280, 18, "#ffffff")
            rrect(c, 30, -140, 80, 280, 18, "#ffffff")


sx(T("parent", 205.3), "pop", 0.4)
sx(T("teenager", 207.5) - 0.3, "kids_yay", 0.4)
sx(T("pause", 208.4), "pause", 0.8)
sx(T("rated", 210.1), "stamp", 0.7)
for i in range(3):
    sx(T("family", 213.3) + 0.3 + i * 0.25, "tick_check", 0.4)
sx(T("parental", 216.4), "pop_big", 0.5)
sx(T("parental", 216.4) + 0.4, "lock", 0.7)


def s_veteran(c, t):
    a, b = T("and", 231.9), T("now", 242.8)
    a0 = T("if", 219.3)
    if t < T("prices", 226.6) - 0.2:
        room_bg(c, t, window_kind="dusk")
        c.save()
        push(c, t, a0, a, 1.0, 1.08)
        console_old(c, 1300, 860, 1.0, kind=0)
        # cobwebs / dust
        for i in range(5):
            line(c, 1150 + i * 70, 760, 1180 + i * 60, 700, "#d9d9e6", 2, 0.4)
        figure(c, 640, 920, "gamer", "think", "neutral", t, s=1.0, rim=CYAN)
        if t > T("5", 221.8):
            chip(c, 1300, 640, "2013", "#9aa0b5", size=56, sc=back_out(at(t, T("5", 221.8), 0.3)))
        if t > T("consider", 225.0) - 0.2:
            hourglass(c, 980, 420, 0.6 * back_out(at(t, T("consider", 225.0) - 0.2, 0.3)), frac=at(t, 225.0, 1.5))
        c.restore()
    elif t < T("and", 231.9):
        grid_board(c, t, col=GREEN)
        c.save()
        push(c, t, T("prices", 226.6) - 0.2, a, 1.0, 1.06)
        # price chart dropping
        k = smooth(at(t, T("prices", 226.6), 1.2))
        pts = [(260, 300), (560, 360), (860, 470), (1160, 560), (1460, 720), (1660, 760)]
        n = max(2, int(len(pts) * k + 0.999))
        pth = poly(pts[:n], close=False)
        c.drawPath(pth, P("#000000", 34, 0.5))
        c.drawPath(pth, P(GREEN, 18))
        px, py = pts[n - 1]
        price_tag(c, px, py - 120, 0.7, "$$", GOLD, rot=8)
        bu = T("bundles", 228.0)
        if t > bu:
            gift(c, 1500, 380, 0.7 * back_out(at(t, bu, 0.35)), color=PURPLE)
        eb = T("early", 229.4)
        if t > eb:
            kk = back_out(at(t, eb, 0.3))
            wallet(c, 420, 760, 0.7 * kk, empty=True, burn=1, t=t)
            chip(c, 420, 900, "DAY 1 = MOST $", HOT, "#ffffff", 40, sc=kk)
        c.restore()
    else:
        grid_board(c, t, col=CYAN)
        c.save()
        push(c, t, a, b, 1.0, 1.06)
        figure(c, 420, 940, "buyer2", "think", "neutral", t, s=0.9, rim=CYAN)
        pa = T("patched", 235.6)
        fi = T("fixed", 236.3)
        im = T("improved", 236.8)
        for st, x, kind in ((pa, 900, 0), (fi, 1240, 1), (im, 1580, 2)):
            if t > st:
                k = back_out(at(t, st, 0.35))
                with xf(c, x, 460, k):
                    if kind == 0:
                        gear(c, 0, 0, 90, t * 60, "#c9ccd6")
                    elif kind == 1:
                        # squashed bug
                        c.drawOval(skia.Rect(-70, -45, 70, 45), P("#6a3a2a"))
                        for j in range(3):
                            line(c, -40 + j * 40, -40, -60 + j * 50, -80, "#6a3a2a", 8)
                            line(c, -40 + j * 40, 40, -60 + j * 50, 80, "#6a3a2a", 8)
                        xmark(c, 0, 0, 0.8)
                    else:
                        arrow(c, -80, 80, 80, -80, GREEN, 26)
        mo = T("months", 239.0)
        if t > mo - 0.3:
            k = back_out(at(t, mo - 0.3, 0.3))
            calendar(c, 1240, 820 - 0, 0.55 * k, "+3 MO", "", color=PURPLE)
        ch = T("cheaper", 241.6)
        if t > ch:
            price_tag(c, 1600, 800, 0.7 * back_out(at(t, ch, 0.3)), "-$$", GREEN)
        c.restore()


sx(T("since", 221.2), "dust", 0.5)
sx(T("5", 221.8), "pop", 0.5)
sx(T("consider", 225.0) - 0.2, "tick_slow", 0.4, dur=1.4)
sx(T("prices", 226.6), "slide_down", 0.6)
sx(T("bundles", 228.0), "pop_big", 0.5)
sx(T("early", 229.4), "fire", 0.4, dur=1.0)
sx(T("patched", 235.6), "wrench", 0.5)
sx(T("fixed", 236.3), "squish", 0.6)
sx(T("improved", 236.8), "up", 0.5)
sx(T("months", 239.0) - 0.3, "page_flip", 0.4)
sx(T("cheaper", 241.6), "coin_in", 0.5)


# --- R. Already have a console → checklist. Buying just for this → 3 questions
def s_checklist(c, t):
    a, b = T("now", 242.8), T("but", 250.1)
    room_bg(c, t, window_kind="dusk")
    c.save()
    push(c, t, a, b, 1.0, 1.05)
    figure(c, 460, 940, "hero", "point", "smile", t, s=1.0, rim=TEAL)
    items = [(T("buy", 244.8), "GAME", lambda cc: game_case(cc, -260, 0, 0.22, t=t)),
             (T("check", 246.0), "STORAGE", lambda cc: ssd(cc, -260, 0, 0.3)),
             (T("preload", 247.6), "PRELOAD", lambda cc: progress_bar(cc, -260, 0, 120, 1.0, GREEN, h=30))]
    for i, (st, lab, ic) in enumerate(items):
        if t > st - 0.2:
            k = ease_out(at(t, st - 0.2, 0.3))
            with xf(c, 1240 + (1 - k) * 200, 300 + i * 190, alpha=k):
                rrect(c, -360, -75, 720, 150, 24, "#000000", 0.6)
                rrect(c, -360, -75, 720, 150, 24, "#ffffff", stroke=4)
                ic(c)
                ftext(c, lab, -120, 22, 64, "#ffffff", align="left")
                check(c, 290, 0, 0.6 * back_out(at(t, st + 0.1, 0.25)))
    c.restore()
    banner(c, t, T("set", 249.2) - 0.1, "ALL SET", None, GREEN, end=b, y=900)


for st in (244.8, 246.0, 247.6):
    sx(T({244.8: "buy", 246.0: "check", 247.6: "preload"}[st], st) + 0.1, "tick_check", 0.6)
sx(T("set", 249.2) - 0.1, "success", 0.8)


def s_three(c, t):
    a, b = T("but", 250.1), T("you're", 267.5)
    grid_board(c, t, col=PINK)
    c.save()
    push(c, t, a, b, 1.0, 1.04)
    q3 = T("three", 253.2)
    if t < q3 - 0.2:
        figure(c, W / 2 - 200, 960, "buyer", "think", "worried", t, s=1.0, rim=PINK)
        console_tall(c, W / 2 + 280, 960, 0.8, glow_c=CYAN)
        qmark(c, W / 2 - 200, 300, 160, GOLD, t=t)
    else:
        qs = [(T("can", 254.8), lambda cc: (wallet(cc, 0, -20, 0.6, t=t),
                                             price_tag(cc, 60, 120, 0.45, "FULL COST", GOLD))),
              (T("do", 258.2), lambda cc: (wifi(cc, -70, 30, 0.7, 3, color=CYAN), ssd(cc, 70, 100, 0.45))),
              (T("will", 261.8), lambda cc: calendar(cc, 0, 30, 0.6, "6 MO", "?", color=PURPLE))]
        for i, (st, draw) in enumerate(qs):
            card_panel(c, 420 + i * 540, 560, 460, 520, t, min(st, q3 + i * 0.15) - 0.1, i + 1, draw, col=PINK)
            ys = T("yes", 265.9)
            if t > ys - 0.5 + i * 0.25:
                check(c, 420 + i * 540 + 170, 360, 0.8 * back_out(at(t, ys - 0.5 + i * 0.25, 0.25)))
    c.restore()
    go = T("go", 266.4)
    if t > go:
        stamp(c, t, go, "GO FOR IT", W / 2, 950, GREEN, 90, rot=-4)


sx(T("three", 253.2) - 0.2, "cards", 0.6)
sx(T("can", 254.8), "pop", 0.4)
sx(T("do", 258.2), "pop", 0.4)
sx(T("will", 261.8), "pop", 0.4)
for i in range(3):
    sx(T("yes", 265.9) - 0.5 + i * 0.25, "tick_check", 0.6)
sx(T("go", 266.4), "stamp", 0.9)


def s_choice(c, t):
    a, b = T("you're", 267.5), T("one", 274.9)
    sp = T("and", 270.7)
    if t < sp:
        c.save()
        push(c, t, a, sp, 1.0, 1.1, cy=H * 0.65)
        scene_coast(c, t, "dusk", cam=(t - a) * 30, car_x=lerp(300, 1500, smooth(at(t, a, 3.2))), car_c=TEAL)
        c.restore()
        letterbox(c, 1.0)
        ch = T("choice", 269.9)
        if t > ch:
            slam_title(c, t, ch, "CHOICE", W / 2, 360, 190, color=GOLD, end=sp + 0.1)
        elif t > T("mistake", 268.2):
            slam_title(c, t, T("mistake", 268.2), "MISTAKE", W / 2, 360, 150, color="#ffffff", end=ch)
            if t > T("mistake", 268.2) + 0.25:
                line(c, W / 2 - 380, 360, W / 2 + 380, 330, RED, 22)
    else:
        c.save()
        sgfx.clip_half(c, 0, seed=8)
        grid_board(c, t, col=HOT)
        figure(c, 480, 960, "buyer", "cheer", "laugh", t, s=0.85, rim=PINK)
        rnd = random.Random(1)
        for i in range(12):
            ph = ((t - sp) * 0.9 + i / 12) % 1.0
            bill(c, 480 + rnd.uniform(-300, 300), lerp(600, -80, ph), 0.6, rot=ph * 400 + i * 30)
        c.restore()
        c.save()
        sgfx.clip_half(c, 1, seed=8)
        grid_board(c, t, col=GREEN)
        figure(c, 1420, 960, "hero", "hold", "smile", t, s=0.85, rim=TEAL,
               hold=lambda cc, hx, hy: console_tall(cc, hx + 20, hy + 150, 0.4, glow_c=CYAN))
        if t > T("well", 274.2) - 0.2:
            wallet(c, 1720, 500, 0.6 * back_out(at(t, T("well", 274.2) - 0.2, 0.3)), t=t)
            check(c, 1720, 330, 0.8 * back_out(at(t, T("well", 274.2), 0.25)))
        c.restore()
        sgfx.jagged_split(c, seed=8, color="#000000", w=14)


sx(T("you're", 267.5), "car_pass", 0.6, pan=0.3)
sx(T("mistake", 268.2), "slam", 0.6)
sx(T("mistake", 268.2) + 0.25, "scratch_line", 0.6)
sx(T("choice", 269.9), "slam", 1.0)
sx(T("and", 270.7), "whoosh", 0.5)
sx(T("money", 272.6), "cash_flutter", 0.5, pan=-0.5)
sx(T("well", 274.2), "ding", 0.6, pan=0.5)


# --- S. One last thing: the PC question → ending
def s_last(c, t):
    a, b = T("one", 274.9), T("either", 294.7)
    sh = T("shown", 281.9)
    if t < T("if", 286.2):
        fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#05030f", "#140a2e"]))
        c.save()
        push(c, t, a, T("if", 286.2), 1.0, 1.12)
        if t < T("remember", 276.3):
            chip(c, W / 2, H / 2, "ONE LAST THING", GOLD, size=80, sc=back_out(at(t, a, 0.35)))
        else:
            # PC silhouette under a sheet, a big question hanging above
            k = smooth(at(t, T("remember", 276.3), 0.6))
            spotlight(c, W / 2, 980, 0.14 * k, 420)
            with xf(c, W / 2 + 40, 950, 1.1, alpha=k):
                pc_tower(c, 0, 0, 1.0)
            # sheet covering it
            cov = 1.0 - (0.0 if t < T("pc", 284.4) else 0.25 * smooth(at(t, T("pc", 284.4), 0.6)))
            with xf(c, W / 2 + 40, 950, 1.1, alpha=k * cov):
                pth = skia.Path()
                pth.moveTo(-330, 10)
                pth.cubicTo(-320, -300, -280, -460, -60, -470)
                pth.cubicTo(200, -470, 330, -420, 330, 10)
                pth.close()
                c.drawPath(pth, P("#4a3f6e"))
                for i in range(5):
                    line(c, -250 + i * 120, -380 + abs(i - 2) * 30, -270 + i * 130, 0, "#3a3058", 8, 0.8)
            qmark(c, W / 2, 210, 220 * back_out(at(t, T("question", 278.2), 0.35)), GOLD, t=t)
            if t > T("pc", 284.4):
                chip(c, W / 2 + 520, 520, "PC?", "#ffffff", size=80, sc=back_out(at(t, T("pc", 284.4), 0.3)))
            if t > T("when", 285.4):
                chip(c, W / 2 - 520, 520, "WHEN?", "#ffffff", size=70, sc=back_out(at(t, T("when", 285.4), 0.3)))
        c.restore()
    elif t < T("so", 291.7):
        # overnight change: day ↔ night flip over the city
        ov = T("overnight", 290.4)
        k = smooth(at(t, ov - 0.4, 1.0))
        scene_street(c, t, "day" if k < 0.5 else "night", cam=(t - a) * 10)
        tint(c, "#000000", 0.0)
        with xf(c, W / 2, 0, alpha=1.0):
            pass
        console_tall(c, 620, 900, 0.6, glow_c=CYAN)
        pc_tower(c, 1350, 900, 0.75, a=smooth(at(t, T("happens", 286.7), 0.5)))
        if t > T("console", 289.3):
            price_tag(c, 620, 320, 0.7, "?", GOLD, rot=math.sin(t * 6) * 12)
        if 0.05 < k < 0.95:
            tint(c, "#ffffff", 0.5 * (1 - abs(k - 0.5) * 2))
    else:
        fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#05030f", "#1a0b3b"]))
        hw = T("long", 292.5)
        flip = clamp((t - hw) / 0.6)
        hourglass(c, W / 2, H / 2, 1.5, frac=at(t, hw + 0.6, 2.0), rot=180 * smooth(flip) - 180)


sx(T("one", 274.9), "pop_big", 0.6)
sx(T("remember", 276.3), "drone", 0.4, dur=7.0)
sx(T("question", 278.2), "pop_big", 0.6)
sx(T("rockstar", 280.7), "shimmer", 0.35)
sx(T("pc", 284.4), "pop", 0.5)
sx(T("when", 285.4), "pop", 0.5)
sx(T("if", 286.2), "whoosh", 0.5)
sx(T("happens", 286.7), "power_on", 0.6, pan=0.4)
sx(T("overnight", 290.4) - 0.4, "swoosh_big", 0.7)
sx(T("long", 292.5), "hourglass_flip", 0.6)
sx(T("long", 292.5) + 0.6, "sand", 0.35, dur=2.0)


def s_end(c, t):
    a = T("either", 294.7)
    if t < VOICE_END:
        c.save()
        push(c, t, a, VOICE_END, 1.0, 1.04)
        scene_street(c, t, "night", cam=(t - a) * 30)
        storefront(c, 1350, 905, 0.85, t, sign="GAMES")
        # long queue to the store on launch night
        for i in range(10):
            x = 1000 - i * 95
            figure(c, x, 1000 + (i % 2) * 6, ("buyer", "buyer2", "buyer3", "gamer")[i % 4], "stand",
                   ("neutral", "worried", "neutral", "sad")[i % 4], t + i, s=0.45, face=1, rim=PINK)
        # you: calm, walking the other way
        hx = 1000 - (t - a) * 90
        figure(c, 1560 - (t - a) * 70, 1010, "hero", walk_pose(t, 3), "smile", t, s=0.55, face=-1, rim=TEAL)
        c.restore()
        calendar(c, 200, 230, 0.6 * back_out(at(t, T("november", 300.0) - 0.3, 0.35)), "NOV", 19, color=HOT) if t > T(
            "november", 300.0) - 0.3 else None
        minimap(c, t, heading=t * 4, blip=(40, -20, TEAL))
    else:
        # outro: coast at dusk, car drives off, fade
        lt = t - VOICE_END
        c.save()
        push(c, t, VOICE_END, END, 1.0, 1.08, cy=H * 0.6)
        scene_coast(c, t, "dusk", cam=lt * 30, car_x=700 + lt ** 1.5 * 600, car_c=TEAL)
        c.restore()
        letterbox(c, 1.0)
        tint(c, "#000000", clamp((lt - 2.2) / 1.2))
        flash(c, t, VOICE_END, 0.3)


sx(T("either", 294.7), "whoosh", 0.4)
sx(T("standing", 298.0), "crowd", 0.35, dur=3.0)
sx(T("november", 300.0) - 0.3, "pop_big", 0.5)
sx(VOICE_END, "boom", 0.8)
sx(VOICE_END + 0.1, "car_pass", 0.7, pan=0.5)


# ------------------------------------------------------------------ assembly
SCENES = [
    (0.0, T("they'll", 3.8), s_hook),
    (T("they'll", 3.8), T("and", 8.3), s_rush),
    (T("and", 8.3), T("by", 13.4), s_wrong),
    (T("by", 13.4), T("and", 17.1), s_which),
    (T("and", 17.1), T("on", 23.6), s_mystery),
    (T("on", 23.6), T("take", 28.9), s_launch),
    (T("take", 28.9), T("the", 33.0), s_ceo),
    (T("the", 33.0), T("but", 39.7), s_sick),
    (T("but", 39.7), T("so", 47.5), s_hype),
    (T("so", 47.5), T("first", 51.5), s_slow),
    (T("first", 51.5), T("if", 65.4), s_platforms),
    (T("if", 65.4), T("so", 70.4), s_lastgen),
    (T("so", 70.4), T("if", 76.3), s_question),
    (T("if", 76.3), T("but", 84.1), s_relax),
    (T("but", 84.1), T("let's", 90.1), s_iceberg),
    (T("let's", 90.1), T("and", 100.0), s_price),
    (T("and", 100.0), T("now", 102.3), s_angry),
    (T("now", 102.3), T("and", 114.7), s_console_cost),
    (T("and", 114.7), T("if", 129.5), s_extras),
    (T("if", 129.5), T("and", 142.8), s_monthly),
    (T("and", 142.8), T("so", 153.6), s_detail),
    (T("so", 153.6), T("that", 161.0), s_nodisc),
    (T("that", 161.0), T("second", 172.2), s_changes),
    (T("second", 172.2), T("the", 184.5), s_storage),
    (T("the", 184.5), T("so", 202.1), s_preload),
    (T("so", 202.1), T("if", 204.8), s_who),
    (T("if", 204.8), T("if", 219.3), s_parent),
    (T("if", 219.3), T("now", 242.8), s_veteran),
    (T("now", 242.8), T("but", 250.1), s_checklist),
    (T("but", 250.1), T("you're", 267.5), s_three),
    (T("you're", 267.5), T("one", 274.9), s_choice),
    (T("one", 274.9), T("either", 294.7), s_last),
    (T("either", 294.7), END + 1, s_end),
]
CUTS = [s for s, e, f in SCENES[1:]]
# sub-cuts inside scenes (also get a whoosh)
SUBCUTS = [T("right", 11.4) - 0.2, T("waiting", 159.1) - 0.4, T("third", 180.0) - 0.3, T("and", 197.3),
           T("prices", 226.6) - 0.2, T("and", 231.9), T("three", 253.2) - 0.2, T("and", 270.7), T("if", 286.2),
           T("so", 291.7), VOICE_END]
BIG = {T("on", 23.6), T("and", 142.8), T("you're", 267.5)}


def render_frame(c, t):
    c.clear(C("#000000"))
    for start, end, fn in SCENES:
        if start <= t < end:
            c.save()
            drift(c, t, 3)
            fn(c, t)
            c.restoreToCount(1)
            break
    light_leak(c, t, 0.08)
    vignette(c, 0.5)
    grain(c, t, 0.045)
    # cut transitions: fast dip + whip streak
    for ct in CUTS + SUBCUTS:
        d = t - ct
        if -0.08 < d < 0.12:
            k = 1 - abs(d) / (0.08 if d < 0 else 0.12)
            tint(c, "#000000", 0.55 * k)
            for i in range(10):
                y = (i * 113 + int(ct * 100)) % H
                c.drawRect(skia.Rect(0, y, W, y + 6 + (i % 3) * 8), P("#ffffff", a=0.10 * k))
    if t < 0.4:
        tint(c, "#000000", 1 - t / 0.4)
