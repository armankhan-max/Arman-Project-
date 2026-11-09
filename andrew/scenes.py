"""Shot list for "Who can actually afford a $500,000 house?" (6:13).

Every time below is an absolute second in the voiceover, taken from the word timestamps in
transcript.json, so each pop / number / SFX lands on the word that says it.
SFX cues are declared next to the visuals they belong to (S(...)) and audio.py mixes them.
"""
import math
import random

import skia

from kit import *  # noqa: F401,F403
from kit import (W, H, C, P, xf, rrect, poly, line, text, text_width, linear, radial, fill_shader, glow,
                 sparkle, check_mark, cross_mark, mixhex, clamp, lerp, smooth, ease_out, back_out, at, window,
                 BOARD1, BOARD2, CREAM, AMBER, MINT, ROSE, MUTED, INK, HEAD, board, title, pop, tag, money,
                 callout, underline, strike, street, interior, house, tree, cloud, person, photo, bill, cash_stack,
                 price_tag, contract, pen, stamp, water_heater, calendar, shield, jar, car, ac_unit, credit_card,
                 bed_scene, clock, people_icon, house_icon, storm_icons, warning, donut, gauge, bike, briefcase,
                 vault, clipboard, zzz, money_rain, vignette, grain, blit, cached, blurpaint)

SCENES = []
SFX = []        # (time, name, gain)
AMB = []        # (t0, t1, name, gain)
LOWER = []


def S(t, name, g=1.0):
    SFX.append((t, name, g))


def scene(t0, t1, whoosh=True, amb=None):
    def deco(fn):
        SCENES.append((t0, t1, fn))
        if whoosh and t0 > 0.1:
            S(t0 - 0.12, "whoosh", 0.45)
        if amb:
            AMB.append((t0, t1, amb[0], amb[1]))
        return fn
    return deco


def fade_in(t, t0, d=0.35):
    return ease_out(at(t, t0, d))


def mini_icon(c, kind, x, y, s=1.0, col=CREAM):
    with xf(c, x, y, s=s):
        if kind == "car":
            rrect(c, -40, -10, 80, 26, 10, col)
            c.drawPath(poly([(-24, -10), (-14, -28), (16, -28), (26, -10)]), P(col))
            c.drawCircle(-22, 18, 9, P(BOARD2))
            c.drawCircle(22, 18, 9, P(BOARD2))
        elif kind == "shield":
            c.drawPath(poly([(0, -32), (28, -22), (24, 12), (0, 32), (-24, 12), (-28, -22)]), P(col))
        elif kind == "fuel":
            rrect(c, -22, -30, 34, 60, 6, col)
            line(c, 12, -16, 28, -6, col, 6)
            line(c, 28, -6, 28, 20, col, 6)
            rrect(c, -16, -22, 22, 16, 3, BOARD2)
        elif kind == "cap":
            c.drawPath(poly([(-40, -6), (0, -26), (40, -6), (0, 14)]), P(col))
            rrect(c, -22, 0, 44, 20, 6, col)
            line(c, 34, -4, 34, 22, col, 4)
        elif kind == "health":
            rrect(c, -10, -30, 20, 60, 4, col)
            rrect(c, -30, -10, 60, 20, 4, col)
        elif kind == "cart":
            c.drawPath(poly([(-34, -24), (-24, -24), (-14, 10), (26, 10), (32, -14), (-20, -14)], close=False),
                       P(col, 6))
            c.drawCircle(-10, 22, 6, P(col))
            c.drawCircle(22, 22, 6, P(col))
        elif kind == "phone":
            rrect(c, -18, -32, 36, 64, 8, col)
            rrect(c, -12, -24, 24, 42, 3, BOARD2)
        elif kind == "tax":
            rrect(c, -24, -32, 48, 64, 5, col)
            text(c, "%", 0, 14, 36, BOARD2)
        elif kind == "house":
            c.drawPath(poly([(-30, -4), (0, -32), (30, -4), (30, 30), (-30, 30)]), P(col))
        elif kind == "umbrella":
            pth = skia.Path()
            pth.addArc(skia.Rect(-34, -30, 34, 30), 180, 180)
            pth.close()
            c.drawPath(pth, P(col))
            line(c, 0, 0, 0, 28, col, 5)
        elif kind == "plane":
            c.drawPath(poly([(-36, 0), (30, -6), (40, 0), (30, 6)]), P(col))
            c.drawPath(poly([(-4, -2), (12, -30), (20, -30), (12, -2)]), P(col))
            c.drawPath(poly([(-4, 2), (12, 30), (20, 30), (12, 2)]), P(col))
        elif kind == "boat":
            c.drawPath(poly([(-40, 6), (40, 6), (28, 24), (-28, 24)]), P(col))
            c.drawPath(poly([(0, -34), (0, 2), (26, 2)]), P(col))
        elif kind == "gift":
            rrect(c, -28, -14, 56, 44, 4, col)
            rrect(c, -32, -24, 64, 14, 3, col)
            line(c, 0, -24, 0, 30, BOARD2, 6)
        elif kind == "debt":
            rrect(c, -36, -24, 72, 48, 6, col)
            rrect(c, -36, -12, 72, 10, 0, BOARD2)


# =====================================================================================================
# HOOK
# =====================================================================================================
@scene(0.0, 2.6, amb=("city", 0.22))
def s_hook_street(c, t):
    street(c, t)
    k = smooth(t / 2.6)
    house(c, 1180, 905, 1.05)
    # for-sale sign
    with xf(c, 1520, 905):
        line(c, 0, 0, 0, -170, "#6a4e3a", 10)
        rrect(c, -90, -230, 180, 90, 8, CREAM)
        text(c, "FOR SALE", 0, -175, 30, ROSE)
    tree(c, 520, 905, 1.1, "#7fa864", "#6a9354")
    tree(c, 1780, 905, 0.9)
    person(c, lerp(240, 760, k), 1000, "buyer", t=t, walk=t * 1.1, s=0.95, expr="smile")
    pk = pop(t, 1.75, 0.5)
    if pk > 0:
        price_tag(c, 1180, 300, "$500,000", s=pk)
    S(0.05, "steps", 0.5)
    S(1.75, "pop", 0.8)


@scene(2.6, 5.65, amb=("room", 0.3))
def s_hook_sign(c, t):
    interior(c, wall="#efe0c8", floor="#b98d64", window=True)
    rrect(c, 0, 760, W, 320, 0, "#7a573e")
    rrect(c, 0, 760, W, 22, 0, "#8d674b")
    sign = clamp((t - 3.4) / 1.6)
    with xf(c, 960, 560, s=0.95, rot=-4):
        tip = contract(c, 0, 0, sign=sign, t=t)
    if t > 3.3:
        # pen follows signature
        u = sign
        px = 960 + (-250 + u * 380) * 0.95
        py = 560 + (300 + math.sin(u * 22) * 16 * (1 - u * 0.3) - u * 10) * 0.95
        pen(c, px + 10, py - 4, 1.0, rot=30)
    else:
        pen(c, 1500, 820, 1.0, rot=70)
    # highlight the price
    k = ease_out(at(t, 4.0, 0.6))
    if k > 0:
        pth = skia.Path()
        pth.addOval(skia.Rect(640, 690, 1080, 800))
        meas = skia.PathMeasure(pth, False)
        seg = skia.Path()
        meas.getSegment(0, meas.getLength() * k, seg, True)
        c.drawPath(seg, P(ROSE, 8))
    S(2.75, "paper", 0.9)
    S(3.4, "pen", 1.0)
    S(4.2, "pop2", 0.6)


@scene(5.65, 7.0)
def s_bank_yes(c, t):
    street(c, t)
    with xf(c, 960, 905):
        rrect(c, -520, -520, 1040, 520, 6, "#efe6d6")
        c.drawPath(poly([(-580, -520), (580, -520), (0, -720)]), P("#d9cdb8"))
        rrect(c, -580, -540, 1160, 30, 4, "#cbbda6")
        text(c, "BANK", 0, -580, 64, "#6a5c48")
        for i in range(6):
            x = -430 + i * 172
            rrect(c, x - 30, -500, 60, 470, 6, "#ffffff")
        rrect(c, -110, -260, 220, 260, 10, "#5c4a3a")
        rrect(c, -580, -30, 1160, 30, 4, "#cbbda6")
    person(c, 1260, 1000, "banker", "thumbs", "grin", t=t, s=0.95)
    stamp(c, 820, 520, "APPROVED", at(t, 6.45, 0.25), col=MINT, size=110)
    S(6.45, "stamp", 1.0)
    S(6.6, "ding", 0.5)


@scene(7.0, 8.25)
def s_agent(c, t):
    board(c)
    photo(c, 700, 560, "agent", t, 7.0, s=1.05, rot=-3, label="SMILING", sub="REAL ESTATE AGENT")
    for i in range(3):
        sparkle(c, 980 + i * 60, 360 + math.sin(t * 3 + i) * 10, 16 * pop(t, 7.6 + i * 0.1), AMBER, rot=t * 40)
    S(7.05, "click", 0.7)


@scene(8.25, 9.95, amb=("city", 0.2))
def s_smart_move(c, t):
    street(c, t)
    house(c, 960, 905, 0.8)
    crew = [("crowd1", 250), ("crowd4", 470), ("crowd2", 1450), ("crowd3", 1670)]
    for i, (w, x) in enumerate(crew):
        person(c, x, 1010, w, "cheer" if i % 2 else "thumbs", "grin", t=t, s=0.85, seed=i, flip=x > 960)
    person(c, 960, 1040, "buyer", "wave", "grin", t=t, s=0.95)
    for i, (lbl, x, y, t0) in enumerate([("SMART MOVE!", 380, 330, 8.45), ("CONGRATS!", 1560, 300, 8.8),
                                         ("GREAT INVESTMENT!", 960, 190, 9.15)]):
        k = pop(t, t0)
        if k > 0:
            w = text_width(lbl, 44) + 70
            with xf(c, x, y, s=k):
                rrect(c, -w / 2, -45, w, 90, 45, CREAM)
                c.drawPath(poly([(-20, 40), (20, 40), (-30, 80)]), P(CREAM))
                text(c, lbl, 0, 16, 44, INK)
            S(t0, "pop", 0.7)
    S(8.3, "applause", 0.45)


@scene(9.95, 12.0)
def s_math_year(c, t):
    board(c)
    title(c, "THE MATH SAYS...", t, 10.2, y=150)
    months = ["JAN", "MAR", "MAY", "JUL", "SEP", "NOV", "JAN"]
    idx = int(clamp((t - 10.9) / 0.9) * (len(months) - 1))
    calendar(c, 960, 560, 1.4, months[idx], "+1" if idx == len(months) - 1 else str(idx * 2 + 1),
             "YEAR" if idx == len(months) - 1 else "MONTH", col=ROSE)
    for i in range(6):
        S(10.9 + i * 0.15, "paper", 0.25)
    tag(c, 960, 860, "WITHIN A YEAR", t, 11.5, bg=AMBER)


@scene(12.0, 14.9, amb=("room", 0.3))
def s_heater(c, t):
    interior(c, wall="#d9cbb6", floor="#9a8a78", window=False)
    burst = clamp((t - 13.35) / 0.3)
    water_heater(c, 1250, 860, 1.25, t, burst)
    if burst > 0:
        pd = clamp((t - 13.4) / 1.2)
        c.drawOval(skia.Rect(1250 - 520 * pd, 840, 1250 + 300 * pd, 900), P("#7fd3ff", a=0.55))
    person(c, 640, 1000, "buyer", "headhold" if t > 14.2 else ("stand" if burst <= 0 else "shrug"),
           "panic" if t > 13.6 else "smile", t=t, s=1.05, sweat=1.0 if t > 13.8 else 0, look=(1, 0))
    tag(c, 640, 330, "PANIC", t, 14.55, bg=ROSE, fg="#ffffff", size=46)
    tag(c, 1250, 210, "BROKEN WATER HEATER", t, 13.3, bg=CREAM, size=34)
    S(13.35, "burst", 1.0)
    S(13.4, "water", 0.8)
    S(14.0, "breath", 0.6)
    S(14.55, "sting_neg", 0.6)


# =====================================================================================================
# THE QUESTION
# =====================================================================================================
@scene(14.9, 20.05)
def s_question(c, t):
    board(c)
    title(c, "WHO CAN ACTUALLY AFFORD THIS HOUSE?", t, 15.1, y=170, size=58)
    house_icon(c, 960, 330, 0.9 * pop(t, 15.9), AMBER, 7)
    # left: approved
    k = fade_in(t, 17.0)
    if k > 0:
        with xf(c, 560, 640, alpha=k):
            rrect(c, -300, -140, 600, 280, 26, "#ffffff", 0.06)
            rrect(c, -300, -140, 600, 280, 26, MUTED, stroke=3)
            check_mark(c, -190, 0, 110, MINT, prog=at(t, 17.4, 0.4))
            text(c, "GETS", 40, -20, 54, CREAM)
            text(c, "APPROVED", 40, 50, 54, CREAM)
        strike(c, 560, 650, 560, t, 17.8, ROSE, 14)
        S(17.2, "pop2", 0.6)
        S(17.8, "error", 0.6)
    k = fade_in(t, 18.1)
    if k > 0:
        with xf(c, 1360, 640, s=0.9 + 0.1 * pop(t, 18.1), alpha=k):
            rrect(c, -300, -140, 600, 280, 26, MINT, 0.12)
            rrect(c, -300, -140, 600, 280, 26, MINT, stroke=5)
            text(c, "CAN AFFORD IT", 0, -20, 54, MINT)
            text(c, "+ SLEEP AT NIGHT", 0, 50, 44, CREAM, a=fade_in(t, 19.2))
        if t > 19.2:
            c.drawCircle(1640, 470, 46, P(CREAM))
            c.drawCircle(1622, 458, 42, P(BOARD1))
            zzz(c, 1680, 440, t)
        S(18.2, "ding", 0.6)
        S(19.3, "chime", 0.5)


@scene(20.05, 25.55)
def s_smaller_group(c, t):
    board(c)
    title(c, "MUCH SMALLER THAN YOU THINK", t, 20.4, y=130)
    rnd = random.Random(4)
    shrink = smooth((t - 21.2) / 1.0)
    cols, rows = 10, 5
    for i in range(cols * rows):
        x = 230 + (i % cols) * 88
        y = 330 + (i // cols) * 120
        keep = i in (12, 23, 25, 36, 41)
        col = mixhex(MUTED, "#38585c", shrink) if not keep else mixhex(MUTED, AMBER, shrink)
        sc = 0.9 + (0.25 * shrink if keep else -0.15 * shrink)
        people_icon(c, x, y + (rnd.uniform(-4, 4)), sc, col)
    if t > 21.2:
        S(21.2, "whoosh_s", 0.0)
    # the list
    lk = smooth((t - 22.7) / 0.6)
    if lk > 0:
        for j in range(3):
            kk = pop(t, 22.8 + j * 0.25)
            y = 380 + j * 170
            with xf(c, 1530 + (1 - lk) * 500, y, s=kk):
                bg = "#ffffff" if j < 2 else AMBER
                rrect(c, -230, -62, 460, 124, 20, bg, 0.08 if j < 2 else 0.95)
                rrect(c, -230, -62, 460, 124, 20, CREAM if j < 2 else AMBER, stroke=3)
                c.drawCircle(-160, 0, 38, P(CREAM if j < 2 else INK))
                text(c, str(j + 1), -160, 16, 44, INK if j < 2 else AMBER)
                if j < 2:
                    rrect(c, -100, -14, 260, 28, 14, CREAM, 0.25)
                else:
                    text(c, "???", 40, 18, 52, INK)
            S(22.8 + j * 0.25, "pop", 0.6)
        if t > 24.4:
            glow(c, 1530, 720, 260, AMBER, 0.25 + 0.1 * math.sin(t * 6))
            tag(c, 1530, 840, "NOBODY TALKS ABOUT", t, 24.5, bg=ROSE, fg="#ffffff", size=30)
            S(24.5, "sting_mystery", 0.6)


@scene(25.55, 32.35)
def s_truth(c, t):
    board(c)
    title(c, "A TRUTH MOST BUYERS NEVER HEAR", t, 26.9, y=150, size=54)
    underline(c, 960, 175, 860, t, 27.6, AMBER)
    k1 = pop(t, 28.9)
    if k1 > 0:
        with xf(c, 560, 560, s=k1):
            rrect(c, -330, -230, 660, 460, 30, "#ffffff", 0.06)
            # bank icon
            c.drawPath(poly([(-90, -110), (90, -110), (0, -170)]), P(CREAM))
            for i in range(4):
                rrect(c, -80 + i * 48, -100, 26, 100, 4, CREAM)
            rrect(c, -100, 6, 200, 18, 4, CREAM)
            check_mark(c, 110, -110, 70, MINT, prog=at(t, 29.4, 0.3))
            text(c, "BANK APPROVES", 0, 110, 48, CREAM)
            text(c, "YOU", 0, 168, 48, CREAM)
    k2 = pop(t, 30.1)
    if k2 > 0:
        with xf(c, 1360, 560, s=k2):
            rrect(c, -330, -230, 660, 460, 30, "#ffffff", 0.06)
            house_icon(c, -40, -80, 1.0, AMBER, 7)
            people_icon(c, 70, -50, 1.3, AMBER)
            text(c, "YOU CAN", 0, 110, 48, AMBER)
            text(c, "AFFORD IT", 0, 168, 48, AMBER)
    k3 = pop(t, 31.2)
    if k3 > 0:
        with xf(c, 960, 560, s=k3):
            c.drawCircle(0, 0, 70, P(ROSE))
            text(c, "≠", 0, 30, 90, "#ffffff")
        tag(c, 960, 930, "TWO DIFFERENT QUESTIONS", t, 31.4, bg=CREAM, size=40)
    S(28.9, "pop", 0.7)
    S(30.1, "pop", 0.7)
    S(31.2, "impact", 0.7)


@scene(32.35, 37.75)
def s_two_questions(c, t):
    board(c)
    line(c, 960, 80, 960, 1000, CREAM, 3, 0.4)
    photo(c, 480, 470, "lender", t, 32.4, s=0.82, rot=-2)
    k = pop(t, 33.4)
    if k > 0:
        with xf(c, 480, 900, s=k):
            rrect(c, -390, -70, 780, 140, 24, CREAM)
            text(c, "\"Will this loan get", 0, -8, 40, INK)
            text(c, "paid back?\"", 0, 42, 40, INK)
        tag(c, 480, 110, "THE BANK ASKS", t, 32.6, bg=MUTED, fg="#ffffff", size=30)
    # right: you in living room
    with xf(c, 1440, 0):
        c.save()
        c.clipRect(skia.Rect(-470, 0, 480, H))
        rrect(c, -470, 0, 950, H, 0, "#12434b")
        rrect(c, -380, 640, 760, 220, 40, "#c9705a")
        rrect(c, -340, 560, 680, 140, 40, "#d98a72")
        person(c, 0, 900, "buyer", "shrug" if t > 36.0 else "stand", "worried" if t > 36.2 else "neutral",
               t=t, s=0.9, look=(0, -1))
        c.restore()
    tag(c, 1440, 110, "YOU NEED TO ASK", t, 35.2, bg=AMBER, size=30)
    k = pop(t, 35.8)
    if k > 0:
        with xf(c, 1440, 330, s=k):
            rrect(c, -360, -90, 720, 180, 90, CREAM)
            for i, (dx, dy, r) in enumerate([(-40, 110, 22), (-70, 150, 14)]):
                c.drawCircle(dx, dy, r, P(CREAM))
            text(c, "\"Can I still have a", 0, -10, 40, INK)
            text(c, "LIFE while paying it?\"", 0, 44, 40, ROSE)
    S(33.4, "pop", 0.6)
    S(35.8, "pop", 0.6)
    S(36.9, "soft", 0.6)


@scene(37.75, 41.4)
def s_miles(c, t):
    board(c)
    k = smooth((t - 38.4) / 1.2)
    xa, xb = lerp(860, 300, k), lerp(1060, 1620, k)
    # road
    pth = skia.Path()
    pth.moveTo(xa, 620)
    pth.cubicTo(lerp(xa, xb, 0.3), 420, lerp(xa, xb, 0.7), 820, xb, 620)
    p = P(CREAM, 6, 0.6)
    p.setPathEffect(skia.DashPathEffect.Make([24, 18], -t * 60))
    c.drawPath(pth, p)
    for x, lbl, col in ((xa, "BANK'S ANSWER", MUTED), (xb, "YOUR ANSWER", AMBER)):
        with xf(c, x, 600):
            pin = skia.Path()
            pin.moveTo(0, 0)
            pin.cubicTo(-50, -60, -50, -120, 0, -120)
            pin.cubicTo(50, -120, 50, -60, 0, 0)
            c.drawPath(pin, P(col))
            c.drawCircle(0, -82, 18, P(BOARD2))
        text(c, lbl, x, 700, 34, col)
    if t > 39.1:
        tag(c, 960, 300, "MILES APART", t, 39.1, bg=ROSE, fg="#ffffff", size=54)
    S(38.4, "stretch", 0.6)
    S(39.1, "pop", 0.8)
    if t > 40.4:
        k2 = pop(t, 40.6)
        price_tag(c, 960, 900, "PRICE", s=k2 * 0.8, rot=-4)
    S(40.6, "pop2", 0.6)


# =====================================================================================================
# THE PRICE
# =====================================================================================================
@scene(41.4, 51.75)
def s_price(c, t):
    board(c)
    title(c, "THE PRICE", t, 41.5, y=120, accent="STEP 1:")
    # house + price
    house_icon(c, 420, 520, 2.2 * pop(t, 41.8), AMBER, 8, fillc="#123a40")
    money(c, 420, 790, 500000, 72, t, 42.2, 43.5, AMBER)
    # income bar vs 6 blocks
    base = 900
    k = pop(t, 45.3)
    if k > 0:
        with xf(c, 900, base):
            rrect(c, -60, -110 * k, 120, 110 * k, 8, MINT)
            text(c, "$85K", 0, -130 * k, 36, MINT)
        text(c, "YEARLY INCOME", 900, base + 50, 26, CREAM, "Bold", a=fade_in(t, 46.0))
    for i in range(6):
        t0 = 44.3 + i * 0.22 if t < 47.8 else 44.3 + i * 0.22
        kk = pop(t, t0, 0.3)
        if kk > 0:
            with xf(c, 1300, base - i * 112 - 56, s=kk):
                rrect(c, -90, -52, 180, 104, 8, AMBER if i % 2 == 0 else "#ffc76f")
                text(c, "$85K", 0, 14, 36, INK)
        if i < 6:
            S(44.3 + i * 0.22, "block", 0.5)
    text(c, "HOUSE PRICE", 1300, base + 50, 26, CREAM, "Bold", a=fade_in(t, 44.3))
    k6 = pop(t, 47.9, 0.5)
    if k6 > 0:
        with xf(c, 1600, 520, s=k6, rot=-6):
            c.drawCircle(0, 0, 130, P(ROSE))
            text(c, "6×", 0, 45, 130, "#ffffff")
        S(47.9, "impact", 0.8)
    if t > 48.9:
        tag(c, 1600, 740, "HOLD ON TO THIS", t, 48.9, bg=CREAM, size=30)
        S(48.9, "pop", 0.5)
    if t > 50.4:
        line(c, 1050, base + 6, 1500, base + 6, CREAM, 4, fade_in(t, 50.4))


@scene(51.75, 58.45)
def s_down_payment(c, t):
    board(c)
    title(c, "THE DOWN PAYMENT", t, 51.9, y=120, accent="STEP 2:")
    # bar of house price split 20/80
    x0, x1, y = 260, 1660, 380
    k = smooth((t - 52.6) / 0.6)
    rrect(c, x0, y - 50, (x1 - x0) * k, 100, 16, "#ffffff", 0.1)
    text(c, "$500,000 HOUSE", 960, y - 80, 34, CREAM, "Bold", a=k)
    k2 = ease_out(at(t, 54.8, 0.6))
    if k2 > 0:
        rrect(c, x0, y - 50, (x1 - x0) * 0.2 * k2, 100, 16, AMBER)
        text(c, "20%", x0 + (x1 - x0) * 0.1, y + 18, 50, INK, a=k2)
        S(54.8, "pop", 0.7)
    # cash pile grows
    kc = clamp((t - 56.9) / 1.2)
    if kc > 0:
        n = int(1 + kc * 9)
        for j in range(3):
            cash_stack(c, 760 + j * 200, 900, max(0, n - j * 2), 1.2)
        money(c, 960, 620, 100000, 84, t, 57.0, 58.0, MINT)
        tag(c, 1450, 840, "IN CASH", t, 58.0, bg=MINT, size=36)
        S(56.9, "counter", 0.8)
        S(58.0, "chaching", 0.7)


@scene(58.45, 69.25)
def s_saving(c, t):
    board(c)
    title(c, "HOW LONG TO SAVE IT?", t, 58.6, y=120)
    # left: salary -> 10%
    k = pop(t, 58.9)
    if k > 0:
        with xf(c, 470, 420, s=k):
            rrect(c, -260, -110, 520, 220, 26, "#ffffff", 0.07)
            text(c, "SAVE 10%", 0, -20, 58, AMBER)
            text(c, "of $85,000 income", 0, 44, 34, CREAM, "Bold")
    tag(c, 470, 610, "ALREADY A STRONG HABIT", t, 61.7, bg=MINT, size=28)
    k = pop(t, 63.3)
    if k > 0:
        with xf(c, 470, 800, s=k):
            text(c, "= $8,500", 0, 0, 90, CREAM)
            text(c, "PER YEAR", 0, 60, 34, MUTED)
    S(58.9, "pop", 0.6)
    S(61.7, "pop2", 0.5)
    S(63.4, "coin", 0.8)
    # right: jar filling through 12 years
    fill = clamp((t - 64.7) / 2.4)
    jar(c, 1380, 860, 1.6, fill, label=None)
    yrs = int(1 + fill * 11)
    if t > 64.7:
        calendar(c, 1730, 420, 0.8, "YEAR", str(yrs), col=ROSE)
        if fill < 1:
            if int((t - 64.7) * 10) % 2 == 0:
                pass
    for i in range(12):
        S(64.7 + i * 0.2, "coin_soft", 0.35)
    k12 = pop(t, 66.7)
    if k12 > 0:
        tag(c, 1380, 300, "≈ 12 YEARS", t, 66.7, bg=ROSE, fg="#ffffff", size=56)
        S(66.7, "impact", 0.7)
    if t > 67.8:
        k = fade_in(t, 67.8)
        with xf(c, 960, 990, alpha=k):
            text(c, "...and only if prices stand still", 0, 0, 36, CREAM, "Bold")
        S(68.4, "freeze", 0.5)


@scene(69.25, 78.0)
def s_less_down(c, t):
    board(c)
    # price climbing
    k = smooth((t - 69.4) / 1.1)
    val = 500000 + 60000 * k
    with xf(c, 480, 300):
        price_tag(c, 0, 0, f"${int(val):,}", s=0.9, rot=-6, col=AMBER if k < 0.5 else ROSE)
        if k > 0:
            c.drawPath(poly([(230, -40), (290, -110), (350, -40)]), P(ROSE, a=k))
            rrect(c, 270, -40, 40, 70 * k, 4, ROSE)
    S(69.4, "rise", 0.6)
    # less down
    title(c, "SO MOST BUYERS PUT DOWN LESS", t, 70.4, y=110, size=46)
    x0, x1, y = 200, 1240, 620
    rrect(c, x0, y - 45, x1 - x0, 90, 16, "#ffffff", 0.1)
    kd = ease_out(at(t, 72.3, 0.5))
    rrect(c, x0, y - 45, (x1 - x0) * lerp(0.2, 0.1, kd) if t > 72.3 else (x1 - x0) * 0.2, 90, 16, AMBER)
    if t > 72.3:
        text(c, "10%", x0 + 70, y + 16, 40, INK, a=kd)
        money(c, 760, y + 150, 50000, 70, t, 73.4, 74.0, AMBER)
    S(72.5, "pop", 0.6)
    if t > 74.6:
        person(c, 1530, 980, "buyer", "cheer" if t < 75.6 else "stand", "happy" if t < 76.1 else "shock", t=t,
               s=0.7)
        tag(c, 1530, 560, "RELIEF!", t, 74.9, bg=MINT, size=40)
        S(74.9, "sigh", 0.0)
        S(75.0, "chime", 0.5)
    if t > 76.1:
        kk = pop(t, 76.2)
        with xf(c, 1100, 860, s=kk):
            rrect(c, -230, -70, 460, 140, 20, "#000000", 0.35)
            rrect(c, -230, -70, 460, 140, 20, ROSE, stroke=4)
            if t < 76.9:
                text(c, "HIDDEN COST", 0, 18, 46, ROSE)
            else:
                text(c, "MORTGAGE", 0, -6, 40, "#ffffff")
                text(c, "INSURANCE", 0, 42, 40, "#ffffff")
        S(76.2, "sting_neg", 0.5)
        S(76.9, "pop2", 0.6)


@scene(78.0, 84.15)
def s_pmi(c, t):
    board(c)
    title(c, "MORTGAGE INSURANCE (PMI)", t, 78.1, y=120, size=50)
    tag(c, 960, 200, "A MONTHLY FEE", t, 78.4, bg=AMBER, size=32)
    photo(c, 600, 590, "lender", t, 79.0, s=0.68, rot=-3)
    ks = pop(t, 79.6)
    if ks > 0:
        with xf(c, 600, 590, alpha=0.9 * ks):
            c.drawCircle(0, 0, 300 * ks, P(MINT, 10))
            c.drawCircle(0, 0, 300 * ks, P(MINT, a=0.12))
        shield(c, 820, 360, 0.6 * ks, MINT)
        text(c, "PROTECTS THE LENDER", 600, 980, 40, MINT, a=fade_in(t, 79.8))
    S(79.6, "shield", 0.8)
    if t > 80.1:
        person(c, 1420, 960, "buyer", "shrug", "sad", t=t, s=0.8)
        k = pop(t, 80.2)
        with xf(c, 1420, 420, s=k):
            text(c, "NOT YOU", 0, 0, 72, ROSE)
        # rain over buyer
        for i in range(18):
            ph = (t * 1.6 + i / 18) % 1
            x = 1250 + (i * 37) % 340
            line(c, x, 480 + ph * 420, x - 6, 510 + ph * 420, "#7fb8ff", 4, 0.6)
        S(80.2, "error", 0.6)
    if t > 82.5:
        tag(c, 1420, 250, "+ A FEW HUNDRED / MONTH", t, 82.6, bg=ROSE, fg="#ffffff", size=34)
        S(82.6, "coin", 0.7)


@scene(84.15, 98.75)
def s_loan(c, t):
    board(c)
    title(c, "THE LOAN ITSELF", t, 84.3, y=110, accent="STEP 3:")
    with xf(c, 700, 580):
        k = pop(t, 84.4)
        with xf(c, 0, 0, s=k):
            rrect(c, -380 + 10, -380 + 14, 760, 760, 34, "#000000", 0.25)
            rrect(c, -380, -380, 760, 760, 34, "#fbf6ea")
            rrect(c, -380, -380, 760, 90, 34, "#2b3a40")
            c.drawRect(skia.Rect(-380, -320, 380, -290), P("#2b3a40"))
            text(c, "LOAN CALCULATOR", 0, -320, 34, CREAM)
            rows = [("Home price", "$500,000", 84.5), ("Down payment", "– $50,000", 85.6),
                    ("Loan amount", "$450,000", 87.0), ("Interest rate", "6.5%", 89.8), ("Term", "30 years", 91.2)]
            for i, (lbl, val, t0) in enumerate(rows):
                yy = -220 + i * 92
                a = fade_in(t, t0, 0.25)
                text(c, lbl, -320, yy, 34, "#6a645a", "Bold", "left", a=a)
                text(c, val, 320, yy, 40, INK if i != 2 else ROSE, "Black", "right", a=a)
                line(c, -320, yy + 30, 320, yy + 30, "#e3dccd", 3, a)
            # result
            rrect(c, -340, 250, 680, 110, 20, MINT, 0.18)
            text(c, "MONTHLY", -310, 320, 30, "#2b6b58", "Black", "left", a=fade_in(t, 93.6))
            money(c, 300, 330, 2850, 64, t, 93.7, 94.9, "#14614a", align="right")
    for t0 in (84.5, 85.6, 87.0, 89.8, 91.2):
        S(t0, "type", 0.6)
    S(93.7, "countup", 0.6)
    S(94.9, "ding", 0.6)
    if t > 95.8:
        tag(c, 1460, 520, "JUST THE LOAN", t, 95.9, bg=AMBER, size=44)
        S(95.9, "pop", 0.6)
    if t > 97.0:
        house_icon(c, 1460, 760, 1.4 * pop(t, 97.1), CREAM, 7)
        text(c, "...the house still has to be OWNED", 1460, 920, 30, CREAM, "Bold", a=fade_in(t, 97.3))
        S(97.1, "door", 0.6)


# --------------------------------------------------------------------------------- monthly stack
STACK = [("LOAN", 2850, "#5aa9c4", 98.8), ("PROPERTY TAX", 500, AMBER, 101.9), ("INSURANCE", 300, MINT, 104.4),
         ("PMI", 250, "#b48cf0", 109.0), ("MAINTENANCE", 417, ROSE, 120.1)]


def draw_stack(c, t, x=520, base=990, scale=0.18, labels=True):
    y = base
    for name, amt, col, t0 in STACK:
        k = ease_out(at(t, t0, 0.45))
        if k <= 0:
            continue
        h = amt * scale * k
        rrect(c, x - 150, y - h, 300, h - 4, 8, col)
        if labels and h > 30:
            text(c, f"{name}  ${amt:,}", x + 180, y - h / 2 + 10, 27, col, "Black", "left", a=k)
        y -= h
    return y


@scene(98.75, 110.25)
def s_stack1(c, t):
    board(c)
    title(c, "WHAT IT REALLY COSTS EACH MONTH", t, 98.8, y=110, size=48)
    draw_stack(c, t)
    for _, _, _, t0 in STACK[:4]:
        S(t0, "block", 0.7)
    # right side illustrations
    if 99.0 < t < 103.0:
        with xf(c, 1500, 520, s=pop(t, 99.1)):
            rrect(c, -170, -210, 340, 420, 14, "#fbf6ea")
            text(c, "PROPERTY TAX", 0, -140, 32, INK)
            for i in range(5):
                line(c, -120, -80 + i * 44, 120 - (i % 2) * 60, -80 + i * 44, "#cfc6b4", 8)
            stamp(c, 40, 140, "DUE", at(t, 102.0, 0.25), col=ROSE, size=56)
        S(102.0, "stamp", 0.6)
    elif 103.0 <= t < 107.6:
        with xf(c, 1480, 420, s=pop(t, 103.0)):
            mini_icon(c, "umbrella", 0, 0, 3.0, MINT)
        k = smooth((t - 105.0) / 0.6)
        if k > 0:
            c.drawPath(poly([(1700, 420 - 120 * k), (1660, 470 - 120 * k), (1740, 470 - 120 * k)]), P(ROSE))
            rrect(c, 1688, 470 - 120 * k, 24, 120 * k, 4, ROSE)
            text(c, "RISING", 1700, 580, 30, ROSE)
        storm_icons(c, 1480, 760, t, 106.0, gap=170)
        S(103.0, "pop", 0.5)
        S(105.1, "rise", 0.5)
        S(106.0, "water_short", 0.5)
        S(106.5, "fire", 0.5)
        S(107.1, "thunder", 0.6)
    elif t >= 107.6:
        with xf(c, 1480, 560, s=pop(t, 107.7)):
            shield(c, 0, 0, 1.2, "#b48cf0", check=False, label="PMI")
        S(107.7, "pop", 0.5)


@scene(110.25, 117.45, amb=("night", 0.35))
def s_pipe(c, t):
    interior(c, wall="#e7d8c2", floor="#a5876a", window=True, night=True)
    # pipe across wall
    line(c, 0, 380, 1200, 380, "#b07a3e", 34)
    line(c, 1200, 380, 1200, 900, "#b07a3e", 34)
    burst = clamp((t - 112.9) / 0.3)
    if burst > 0:
        for i in range(24):
            ph = (t * 1.5 + i / 24) % 1
            ang = -0.9 + (i % 7) * 0.3
            x = 700 + math.cos(ang) * ph * 500
            y = 380 + math.sin(ang) * ph * 260 + ph * ph * 520
            c.drawCircle(x, y, 12 * (1 - ph) + 4, P("#8fd8ff", a=0.9 * (1 - ph)))
        pd = clamp((t - 113.0) / 2.0)
        c.drawOval(skia.Rect(700 - 600 * pd, 900, 700 + 600 * pd, 980), P("#8fd8ff", a=0.5))
    person(c, 1500, 1010, "buyer", "headhold" if burst > 0 else "stand", "panic" if burst > 0 else "neutral", t=t,
           s=1.0, look=(-1, 0), sweat=burst)
    clock(c, 300, 200, 70, 2, 13)
    tag(c, 960, 140, "THE BILL EVERYONE FORGETS", t, 111.3, bg=ROSE, fg="#ffffff", size=38)
    # 1% rule card
    if t > 114.1:
        with xf(c, 960, 560, s=pop(t, 114.2)):
            rrect(c, -420, -180, 840, 360, 30, "#000000", 0.55)
            rrect(c, -420, -180, 840, 360, 30, AMBER, stroke=5)
            text(c, "THE 1% RULE", 0, -90, 46, AMBER)
            text(c, "1% of home value", 0, -10, 40, CREAM, "Bold")
            text(c, "set aside every year", 0, 50, 40, CREAM, "Bold")
            text(c, "= $5,000 / year", 0, 130, 48, MINT, a=fade_in(t, 116.0))
        S(114.2, "pop", 0.7)
    S(112.9, "burst", 1.0)
    S(113.0, "water", 0.8)
    S(112.4, "clock", 0.6)


@scene(117.45, 121.05)
def s_maint(c, t):
    board(c)
    title(c, "MAINTENANCE", t, 117.5, y=110, color=ROSE)
    money(c, 960, 380, 5000, 110, t, 118.0, 118.7, CREAM, suffix=" / YEAR")
    k = pop(t, 119.4)
    if k > 0:
        with xf(c, 960, 560, s=k):
            text(c, "÷ 12", 0, 0, 60, MUTED)
        money(c, 960, 760, 417, 130, t, 119.5, 120.4, ROSE, suffix=" / MONTH")
    S(118.0, "countup", 0.5)
    S(120.0, "ding", 0.6)


@scene(121.05, 131.45)
def s_total(c, t):
    board(c)
    title(c, "ADD IT ALL UP", t, 121.1, y=110)
    top = draw_stack(c, t, x=420, base=980, scale=0.17, labels=False)
    parts = [("$2,850", 122.1, "#5aa9c4"), ("+ $500", 123.2, AMBER), ("+ $300", 124.2, MINT),
             ("+ $250", 125.2, "#b48cf0"), ("+ $417", 126.2, ROSE)]
    x = 760
    for i, (lbl, t0, col) in enumerate(parts):
        k = pop(t, t0)
        if k > 0:
            with xf(c, x + i * 230, 360, s=k):
                text(c, lbl, 0, 0, 52, col)
            S(t0, "type", 0.6)
    if t > 127.3:
        k = pop(t, 127.4)
        with xf(c, 1220, 620, s=k):
            rrect(c, -480, -150, 960, 300, 36, "#ffffff", 0.08)
            rrect(c, -480, -150, 960, 300, 36, CREAM, stroke=4)
        money(c, 1220, 660, 4317, 120, t, 127.5, 128.7, CREAM, fmt=lambda v: f"≈ ${int(round(v / 100) * 100) if v > 4250 else int(v):,}")
        text(c, "PER MONTH", 1220, 735, 34, MUTED, a=fade_in(t, 128.7))
        S(127.5, "countup", 0.6)
        S(128.7, "impact", 0.8)
    if t > 130.3:
        tag(c, 1220, 900, "...with NOTHING broken yet", t, 130.4, bg=ROSE, fg="#ffffff", size=34)
        S(130.4, "pop2", 0.6)


# =====================================================================================================
# INCOME NEEDED
# =====================================================================================================
@scene(131.45, 142.0)
def s_28(c, t):
    board(c)
    title(c, "WHAT INCOME DOES THAT TAKE?", t, 131.6, y=110)
    k = clamp((t - 135.2) / 0.8)
    donut(c, 520, 560, 220, 0.28 * smooth(k), AMBER, wid=80, a=fade_in(t, 133.2))
    if t > 133.2:
        text(c, f"{int(28 * smooth(k))}%", 520, 590, 100, AMBER)
        text(c, "OF GROSS INCOME", 520, 880, 34, CREAM, a=fade_in(t, 136.2))
        tag(c, 520, 250, "THE 28% RULE", t, 133.4, bg=CREAM, size=34)
    S(133.4, "pop", 0.6)
    S(135.3, "countup", 0.4)
    if t > 137.0:
        with xf(c, 1360, 420, s=pop(t, 137.1)):
            text(c, "$4,300 / month", 0, 0, 54, CREAM)
            line(c, 0, 40, 0, 120, MUTED, 6)
            c.drawPath(poly([(-20, 110), (20, 110), (0, 140)]), P(MUTED))
        S(137.1, "pop", 0.5)
    if t > 140.0:
        money(c, 1360, 680, 185000, 120, t, 140.2, 141.5, MINT)
        text(c, "PER YEAR", 1360, 750, 34, MUTED, a=fade_in(t, 141.5))
        S(140.2, "countup", 0.6)
        S(141.6, "chaching", 0.6)


@scene(142.0, 149.85)
def s_lenders(c, t):
    board(c)
    photo(c, 470, 560, "lender", t, 142.0, s=0.85, rot=-3, label=None)
    tag(c, 470, 120, "LENDERS OFTEN ALLOW MORE", t, 142.4, bg=MUTED, fg="#ffffff", size=32)
    if t > 143.9:
        with xf(c, 1300, 300, s=pop(t, 144.0)):
            text(c, "THEIR LIMIT", 0, 0, 64, MUTED)
            text(c, "≠", 0, 90, 70, ROSE)
            text(c, "YOUR COMFORT", 0, 180, 64, MINT)
        S(144.0, "pop", 0.6)
        S(144.9, "pop2", 0.6)
    if t > 146.0:
        k = clamp((t - 146.2) / 0.9)
        donut(c, 1150, 780, 120, 0.28 + 0.07 * smooth(k), ROSE, wid=46)
        text(c, f"{28 + int(7 * smooth(k))}%", 1150, 800, 54, ROSE)
        text(c, "STRETCH", 1150, 950, 28, CREAM, "Black")
        S(146.2, "stretch", 0.5)
        if t > 148.3:
            money(c, 1540, 800, 150000, 86, t, 148.4, 149.4, AMBER)
            text(c, "STILL NEEDED", 1540, 860, 28, MUTED, a=fade_in(t, 149.0))
            S(148.4, "countup", 0.5)


@scene(149.85, 156.3)
def s_range(c, t):
    board(c)
    title(c, "REMEMBER THIS RANGE", t, 150.0, y=130)
    x0, x1, y = 200, 1720, 600
    line(c, x0, y, x1, y, CREAM, 6, 0.6)
    for i, v in enumerate(range(0, 251, 50)):
        x = lerp(x0, x1, v / 250)
        line(c, x, y - 14, x, y + 14, CREAM, 4, 0.6)
        text(c, f"${v}K", x, y + 60, 30, MUTED, "Bold")
    k = ease_out(at(t, 151.8, 1.6))
    if k > 0:
        xa, xb = lerp(x0, x1, 150 / 250), lerp(x0, x1, lerp(150, 185, k) / 250)
        rrect(c, xa, y - 60, xb - xa, 120, 14, AMBER, 0.85)
        text(c, "$150K", xa, y - 90, 44, AMBER)
        if k > 0.95:
            text(c, "$185K", xb, y - 90, 44, AMBER)
    S(151.8, "stretch", 0.4)
    S(154.0, "ding", 0.5)
    if t > 154.5:
        k = pop(t, 154.9)
        with xf(c, 960, 880, s=k):
            text(c, "HOW MANY HOUSEHOLDS EARN THAT?", 0, 0, 50, CREAM)
        S(154.9, "pop", 0.6)


@scene(156.3, 161.35)
def s_minority(c, t):
    board(c)
    title(c, "IT'S A MINORITY", t, 156.8, y=120, color=AMBER)
    hl = smooth((t - 156.9) / 0.6)
    for i in range(100):
        x = 560 + (i % 20) * 42
        y = 300 + (i // 20) * 110
        keep = (i % 20) >= 16
        col = mixhex(MUTED, AMBER if keep else "#2f5257", hl)
        people_icon(c, x, y, 0.62, col)
    S(156.9, "whoosh_s", 0.5)
    if t > 158.5:
        tag(c, 600, 930, "LARGE PART OF THE POPULATION", t, 158.6, bg=MUTED, fg="#ffffff", size=30)
        S(158.6, "pop2", 0.5)
    stamp(c, 1380, 900, "NOT A GOAL", at(t, 160.8, 0.25), col=ROSE, size=64)
    S(160.8, "stamp", 0.9)


@scene(161.35, 165.45)
def s_suit(c, t):
    street(c, t)
    k = smooth((t - 161.8) / 0.6)
    st = 1 + 0.35 * k + 0.04 * math.sin(t * 8) * k
    with xf(c, 960, 905, sx=st, sy=1 / st ** 0.5):
        house(c, 0, 0, 0.95, body="#3c6fb0", roof="#22314f")
    # tie + bow over the house
    kk = pop(t, 162.6)
    if kk > 0:
        with xf(c, 960, 560, s=kk):
            c.drawPath(poly([(-60, -40), (0, 0), (-60, 40)]), P(ROSE))
            c.drawPath(poly([(60, -40), (0, 0), (60, 40)]), P(ROSE))
            c.drawCircle(0, 0, 18, P(mixhex(ROSE, "#000000", 0.2)))
    tag(c, 960, 160, "A STRETCH IN A NICE SUIT", t, 162.0, bg=CREAM, size=44)
    S(161.9, "boing", 0.7)
    S(162.6, "pop", 0.6)
    if t > 163.6:
        tag(c, 960, 260, "BUT... PEOPLE EARNING WELL?", t, 163.8, bg=AMBER, size=34)
        S(163.8, "pop2", 0.5)


# =====================================================================================================
# THE COUPLE
# =====================================================================================================
@scene(165.45, 171.1, amb=("city", 0.18))
def s_couple(c, t):
    board(c, "#11414a")
    title(c, "MEET THE COUPLE", t, 166.5, y=120, accent="TEST:")
    photo(c, 600, 560, "husband", t, 166.5, s=0.78, rot=-4)
    photo(c, 1080, 580, "wife", t, 166.8, s=0.78, rot=3)
    k = pop(t, 167.6)
    if k > 0:
        with xf(c, 1560, 520, s=k):
            text(c, "COMBINED", 0, -60, 30, MUTED)
        money(c, 1560, 540, 160000, 90, t, 167.8, 169.3, MINT)
        text(c, "PER YEAR", 1560, 610, 30, MUTED, a=fade_in(t, 169.3))
    if t > 170.0:
        tag(c, 1560, 760, "SOUNDS COMFORTABLE", t, 170.3, bg=MINT, size=30)
    S(166.5, "click", 0.6)
    S(166.8, "click", 0.6)
    S(167.8, "countup", 0.5)
    S(170.3, "chime", 0.4)


@scene(171.1, 174.75)
def s_takehome(c, t):
    board(c)
    title(c, "AFTER TAXES & DEDUCTIONS", t, 171.2, y=130)
    with xf(c, 960, 560, s=pop(t, 171.3)):
        rrect(c, -460 + 10, -220 + 14, 920, 440, 26, "#000000", 0.25)
        rrect(c, -460, -220, 920, 440, 26, "#f3f6e9")
        rrect(c, -460, -220, 920, 80, 26, "#5fae7a")
        c.drawRect(skia.Rect(-460, -170, 460, -140), P("#5fae7a"))
        text(c, "PAYCHECK · TAKE-HOME", 0, -164, 32, "#ffffff")
        money(c, 0, 60, 9500, 130, t, 171.7, 174.4, "#1f5a3a")
        text(c, "PER MONTH", 0, 140, 34, "#5f7a66")
    S(171.3, "receipt", 0.7)
    S(173.4, "countup", 0.5)


BUDGET = [("car", "2 CAR PAYMENTS", 800, 180.6), ("shield", "CAR INSURANCE", 250, 182.3),
          ("fuel", "FUEL", 300, 183.4), ("cap", "STUDENT LOANS", 600, 184.9), ("health", "HEALTH", 400, 186.3),
          ("cart", "GROCERIES", 800, 187.5), ("phone", "UTILITIES & PHONES", 450, 189.3)]


@scene(174.75, 190.0)
def s_budget(c, t):
    board(c)
    # big bar: 9,500 -> housing -> leftover
    x0, x1, y = 160, 1760, 230
    full = x1 - x0
    rrect(c, x0, y - 50, full, 100, 14, "#5fae7a")
    text(c, "$9,500 TAKE-HOME", x0, y - 74, 30, CREAM, "Black", "left")
    kh = ease_out(at(t, 175.4, 0.5))
    hw = full * 4300 / 9500
    if kh > 0:
        rrect(c, x0, y - 50, hw * kh, 100, 14, ROSE)
        text(c, "HOUSING $4,300", x0 + 24, y + 14, 40, "#ffffff", "Black", "left", a=kh)
        S(175.4, "block", 0.8)
    spent = 0
    for _, _, amt, t0 in BUDGET:
        if t >= t0:
            spent += amt * ease_out(at(t, t0, 0.4))
    if spent > 0:
        sw = full * spent / 9500
        rrect(c, x0 + hw, y - 50, sw, 100, 0, AMBER)
    left = 5200 - spent
    if t > 176.8:
        money(c, x1 - 20, y + 120, max(0, left) if t > 179.5 else 5200, 54, t, 176.8, 177.6,
              CREAM if left > 2000 else ROSE, align="right", fmt=lambda v: f"LEFT: ${int(v):,}")
    S(177.3, "ding", 0.5)
    if t > 178.5:
        tag(c, 960, 420, "NOW ADD REAL LIFE", t, 178.6, bg=AMBER, size=34)
    for i, (ic, lbl, amt, t0) in enumerate(BUDGET):
        k = pop(t, t0)
        if k <= 0:
            continue
        col_x = 300 if i < 4 else 1080
        yy = 540 + (i % 4) * 130
        with xf(c, col_x, yy, s=k):
            rrect(c, -40, -50, 640, 100, 20, "#ffffff", 0.07)
            mini_icon(c, ic, 30, 0, 1.0, AMBER)
            text(c, lbl, 90, 12, 32, CREAM, "Black", "left")
            text(c, f"–${amt}", 580, 14, 38, ROSE, "Black", "right")
        S(t0, "coin", 0.45)


@scene(190.0, 199.7)
def s_remains(c, t):
    board(c)
    k = pop(t, 190.2)
    with xf(c, 520, 300, s=k):
        text(c, "REAL LIFE", 0, -40, 36, MUTED)
    money(c, 520, 360, 3600, 100, t, 190.4, 191.2, AMBER, prefix="–$")
    S(190.4, "countup", 0.5)
    k = pop(t, 192.7)
    if k > 0:
        with xf(c, 520, 700, s=k):
            rrect(c, -230, -120, 460, 240, 26, ROSE, 0.15)
            rrect(c, -230, -120, 460, 240, 26, ROSE, stroke=5)
            text(c, "$1,600", 0, 30, 96, "#ffffff")
            text(c, "WHAT REMAINS", 0, 90, 26, ROSE)
        S(192.7, "impact", 0.6)
    needs = [("CLOTHES", 194.1), ("KIDS", 194.7), ("MEDICAL BILLS", 195.2), ("REPAIRS", 195.9),
             ("HOLIDAYS", 196.4), ("RETIREMENT", 197.0), ("EMERGENCY SAVINGS", 197.5), ("FUN", 199.2)]
    for i, (lbl, t0) in enumerate(needs):
        k = pop(t, t0)
        if k <= 0:
            continue
        x = 1250 + (i % 2) * 340 + (60 if i // 2 % 2 else -40)
        y = 260 + (i // 2) * 170
        wob = math.sin(t * 4 + i) * 2
        tag(c, x, y + wob, lbl, t, t0, bg=CREAM if i < 7 else MINT, size=34, rot=(-4 + (i * 7) % 9))
        # arrows into the small box
        if k >= 1:
            line(c, x - 150, y + 10, 760, 700, CREAM, 2, 0.18)
        S(t0, "pop", 0.45)


@scene(199.7, 208.95, amb=("room", 0.25))
def s_half(c, t):
    if t < 203.3:
        board(c)
        k = clamp((t - 200.6) / 1.0)
        donut(c, 960, 560, 250, 0.45 * smooth(k), ROSE, wid=100)
        text(c, f"{int(45 * smooth(k))}%", 960, 590, 120, ROSE)
        text(c, "OF TAKE-HOME PAY", 960, 900, 40, CREAM, a=fade_in(t, 201.5))
        title(c, "HOUSING IS EATING NEARLY HALF", t, 199.8, y=120)
        S(200.6, "countup", 0.5)
        S(201.6, "impact", 0.6)
        return
    interior(c)
    rrect(c, 260, 640, 760, 220, 40, "#5a7fb8")
    rrect(c, 300, 560, 680, 140, 40, "#6e93cc")
    person(c, 520, 900, "buyer", "stand", "neutral", t=t, s=0.95)
    person(c, 780, 905, "partner", "stand", "smile", t=t, s=0.9, seed=1)
    tag(c, 650, 300, "NOT RECKLESS", t, 203.4, bg=MINT, size=44)
    for i, (ic, t0) in enumerate((("plane", 204.4), ("boat", 205.4))):
        k = pop(t, t0)
        if k > 0:
            with xf(c, 1300 + i * 280, 520, s=k):
                c.drawCircle(0, 0, 110, P(INK, a=0.15))
                mini_icon(c, ic, 0, 0, 2.2, "#4a5a6a")
                cross_mark(c, 0, 0, 160, ROSE)
            S(t0, "error", 0.5)
    tag(c, 1440, 820, "WHAT THE MARKET CALLS \"NORMAL\"", t, 207.4, bg=AMBER, size=30)
    S(207.4, "pop", 0.5)


# =====================================================================================================
# THE YEAR
# =====================================================================================================
def timeline(c, t, cur):
    x0, x1, y = 200, 1720, 120
    line(c, x0, y, x1, y, CREAM, 4, 0.4)
    for m in range(12):
        x = lerp(x0, x1, m / 11)
        hit = m + 1 in (4, 7, 9)
        col = ROSE if hit and cur >= m + 1 else CREAM
        c.drawCircle(x, y, 14 if hit else 9, P(col, a=1 if cur >= m + 1 else 0.35))
        text(c, f"M{m + 1}", x, y + 50, 22, col, "Bold", a=1 if cur >= m + 1 else 0.35)
    xc = lerp(x0, x1, (clamp(cur, 1, 12) - 1) / 11)
    c.drawPath(poly([(xc - 14, y - 40), (xc + 14, y - 40), (xc, y - 18)]), P(AMBER))


@scene(208.95, 227.6)
def s_year(c, t):
    board(c)
    cur = 1 + 11 * clamp((t - 209.2) / 13.6)
    if t < 211.3:
        cur = 1 + 2 * clamp((t - 209.4) / 1.9)
    elif t < 215.3:
        cur = 4
    elif t < 219.3:
        cur = 7
    elif t < 223.0:
        cur = 9
    else:
        cur = 9 + 3 * clamp((t - 223.0) / 1.5)
    timeline(c, t, cur)
    title(c, "WATCH THE YEAR UNFOLD", t, 209.0, y=270, size=40, color=MUTED)
    if 211.3 <= t < 215.2:
        calendar(c, 330, 560, 0.9, "MONTH", "4", col=ROSE)
        car(c, 950, 820, 1.2, "#d27b52", smoke=1.0, t=t)
        tag(c, 950, 460, "THE CAR BREAKS", t, 212.2, bg=ROSE, fg="#ffffff", size=36)
        if t > 213.0:
            credit_card(c, 1520, 620, 0.9 * pop(t, 213.1))
            text(c, "–$800", 1520, 820, 60, ROSE, a=fade_in(t, 213.4))
        S(211.8, "pop", 0.5)
        S(212.3, "car_fail", 0.8)
        S(213.3, "swipe", 0.7)
    elif 215.2 <= t < 219.2:
        calendar(c, 330, 560, 0.9, "MONTH", "7", col=ROSE)
        ac_unit(c, 950, 820, 1.3, t, dead=clamp((t - 216.0) / 0.4))
        tag(c, 950, 460, "THE AC DIES", t, 215.8, bg=ROSE, fg="#ffffff", size=36)
        if t > 216.8:
            with xf(c, 1520, 640, s=pop(t, 216.9)):
                text(c, "–$3,500", 0, 0, 70, ROSE)
                text(c, "FINANCED", 0, 60, 34, CREAM)
        S(215.3, "pop", 0.5)
        S(216.1, "ac_off", 0.9)
        S(216.9, "coin", 0.6)
    elif 219.2 <= t < 223.0:
        calendar(c, 330, 560, 0.9, "MONTH", "9", col=ROSE)
        person(c, 900, 960, "partner", "slump", "sad", t=t, s=0.95)
        if t > 220.6:
            with xf(c, 900, 480, s=pop(t, 220.7)):
                rrect(c, -170, -50, 340, 100, 50, CREAM)
                text(c, "HOURS: –30%", 0, 14, 36, ROSE)
        if t > 221.9:
            for i in range(4):
                k = pop(t, 221.9 + i * 0.18)
                with xf(c, 1360 + i * 110, 700, s=k):
                    rrect(c, -48, -60, 96, 120, 12, ROSE, 0.2)
                    text(c, "–", 0, 18, 60, ROSE)
                S(221.9 + i * 0.18, "tick", 0.5)
            text(c, "SHORT EVERY MONTH", 1525, 820, 34, ROSE, a=fade_in(t, 222.2))
        S(219.4, "pop", 0.5)
        S(220.8, "error", 0.5)
    elif t >= 223.0:
        jar(c, 960, 860, 1.7, 0.0)
        text(c, "$0", 960, 700, 90, ROSE, a=fade_in(t, 224.0))
        tag(c, 960, 420, "EMERGENCY FUND", t, 223.4, bg=AMBER, size=40)
        # a fly buzzing around the empty jar
        fx = 960 + math.sin(t * 3.1) * 120
        fy = 640 + math.sin(t * 4.7) * 50
        c.drawCircle(fx, fy, 6, P(INK))
        c.drawOval(skia.Rect(fx - 10, fy - 12, fx, fy - 2), P("#ffffff", a=0.6))
        S(224.0, "whomp", 0.6)
        S(225.0, "fly", 0.4)


@scene(227.6, 231.7)
def s_pressure(c, t):
    board(c)
    k = smooth((t - 229.9) / 1.2)
    with xf(c, 620, 720, sx=1 - 0.12 * k + 0.02 * math.sin(t * 30) * k, sy=1 - 0.18 * k):
        house_icon(c, 0, -100, 2.6, CREAM, 8, fillc=mixhex("#15555e", "#5a1f2c", k))
    if k < 0.5:
        shield(c, 900, 360, 0.7 * pop(t, 229.6), MINT)
        text(c, "SECURITY", 900, 520, 36, MINT, a=fade_in(t, 229.6) * (1 - k * 2))
    gauge(c, 1360, 640, 260, lerp(0.15, 0.95, k), a=fade_in(t, 228.0))
    text(c, "PRESSURE", 1360, 760, 54, mixhex(MINT, ROSE, k), a=fade_in(t, 230.4))
    S(229.6, "shield", 0.5)
    S(230.4, "pressure", 0.8)


# =====================================================================================================
# THE THREE GROUPS
# =====================================================================================================
GROUPS = [("1", "HIGH, STABLE EARNERS", "#22407a"), ("2", "BIG DOWN PAYMENT", "#b8976a"),
          ("3", "LOW-COST LIFERS", "#6f8c3f")]


@scene(231.7, 237.5)
def s_three(c, t):
    board(c)
    title(c, "WHO CAN ACTUALLY AFFORD IT?", t, 231.9, y=160, size=58)
    ka = fade_in(t, 232.3) * (1 - clamp((t - 235.6) / 0.3))
    if ka > 0:
        house_icon(c, 960, 560, 2.4 + 0.05 * math.sin(t * 4), AMBER, 8, a=ka)
        text(c, "?", 960, 640, 150, CREAM, a=ka)
    for i, (n, lbl, col) in enumerate(GROUPS):
        k = pop(t, 235.9 + i * 0.25)
        if k <= 0:
            continue
        with xf(c, 420 + i * 540, 600, s=k):
            rrect(c, -230 + 8, -230 + 12, 460, 460, 30, "#000000", 0.25)
            rrect(c, -230, -230, 460, 460, 30, col)
            c.drawCircle(0, -80, 80, P("#ffffff", a=0.15))
            text(c, n, 0, -48, 110, "#ffffff")
            text(c, lbl, 0, 140, 34, "#ffffff")
        S(235.9 + i * 0.25, "card", 0.7)


@scene(237.5, 248.4, amb=("city", 0.15))
def s_group1(c, t):
    board(c, "#123a5a")
    tag(c, 330, 90, "GROUP 1", t, 237.6, bg=AMBER, size=30)
    photo(c, 480, 560, "earner", t, 237.8, s=0.8, rot=-3)
    text(c, "HIGH, STABLE EARNERS", 480, 990, 40, CREAM, a=fade_in(t, 239.2))
    # income bar vs range
    x0, y0 = 980, 960
    k = ease_out(at(t, 240.9, 0.9))
    yr1, yr2 = y0 - 150 * 2.8, y0 - 185 * 2.8
    rrect(c, x0 - 40, yr2, 340, yr1 - yr2, 6, AMBER, 0.3)
    text(c, "NEEDED", x0 - 60, (yr1 + yr2) / 2 - 6, 30, AMBER, "Black", "right")
    text(c, "$150–185K", x0 - 60, (yr1 + yr2) / 2 + 30, 30, AMBER, "Black", "right")
    hb = 240 * 2.8 * k
    rrect(c, x0 + 60, y0 - hb, 160, hb, 10, MINT)
    if k > 0.9:
        text(c, "$240K", x0 + 140, y0 - hb - 20, 44, MINT)
    if t > 242.7:
        tag(c, x0 + 640, 260, "ROOM TO SPARE", t, 242.8, bg=MINT, size=34)
    S(240.9, "rise", 0.6)
    S(242.8, "ding", 0.6)
    if t > 243.9:
        shield(c, x0 + 640, 520, 0.8 * pop(t, 244.0), MINT)
        text(c, "JOB NOT FRAGILE", x0 + 640, 700, 32, CREAM, a=fade_in(t, 244.4))
        S(244.0, "shield", 0.6)
    if t > 246.5:
        # bad-year storm passes over the bar
        cx = lerp(x0 - 200, x0 + 400, clamp((t - 246.5) / 1.8))
        cloud(c, cx, 200, 0.9, col="#7f8f99")
        for i in range(10):
            ph = (t * 2 + i / 10) % 1
            line(c, cx - 70 + i * 16, 230 + ph * 200, cx - 76 + i * 16, 250 + ph * 200, "#9fc6ff", 3, 0.7)
        tag(c, x0 + 640, 860, "SURVIVES A BAD YEAR", t, 247.0, bg=CREAM, size=32)
        S(246.6, "thunder", 0.4)


@scene(248.4, 264.75)
def s_group2(c, t):
    board(c, "#3a3528")
    tag(c, 330, 90, "GROUP 2", t, 248.5, bg=AMBER, size=30)
    title(c, "BIG DOWN PAYMENT", t, 249.6, y=170, size=56)
    if t < 256.5:
        person(c, 330, 980, "saver", "hips", "happy", t=t, s=0.95)
        srcs = [("jar", "YEARS OF SAVING", 251.8), ("gift", "FAMILY HELP", 253.2), ("house", "SELLING A HOME", 254.5)]
        for i, (ic, lbl, t0) in enumerate(srcs):
            k = pop(t, t0)
            if k <= 0:
                continue
            with xf(c, 820 + i * 400, 560, s=k):
                c.drawCircle(0, 0, 140, P("#ffffff", a=0.08))
                if ic == "jar":
                    jar(c, 0, 90, 0.75, 0.75)
                elif ic == "gift":
                    mini_icon(c, "gift", 0, 10, 3.2, AMBER)
                else:
                    house_icon(c, 0, 0, 1.4, CREAM, 6)
                    if t > 255.6:
                        c.drawPath(poly([(70, -40), (110, -100), (150, -40)]), P(MINT))
                text(c, lbl, 0, 210, 32, CREAM)
            S(t0, "pop", 0.6)
        S(255.7, "rise", 0.5)
        return
    if t < 262.3:
        # shrinking bars
        k = smooth((t - 257.6) / 2.6)
        items = [("LOAN", 450, 300, 258.2), ("INTEREST", 360, 220, 258.7), ("PMI", 160, 0, 259.4)]
        for i, (lbl, a_, b_, t0) in enumerate(items):
            kk = smooth((t - t0) / 0.8)
            v = lerp(a_, b_, kk)
            y = 420 + i * 170
            text(c, lbl, 360, y + 16, 40, CREAM, "Black", "right")
            rrect(c, 400, y - 40, 2.6 * a_, 80, 12, "#ffffff", 0.08)
            rrect(c, 400, y - 40, max(4, 2.6 * v), 80, 12, [ROSE, AMBER, "#b48cf0"][i])
            if kk > 0:
                text(c, "SHRINKS", 400 + 2.6 * a_ + 30, y + 14, 30, MINT, "Black", "left", a=kk)
            S(t0, "shrink", 0.5)
        if t > 261.1:
            tag(c, 960, 960, "IT CHANGES THE ENTIRE MATH", t, 261.2, bg=MINT, size=36)
            S(261.2, "chime", 0.5)
        del k
        return
    # head start race
    for i, (who, lane, start) in enumerate((("saver", 0, 520), ("avg", 1, 140), ("crowd2", 2, 140))):
        y = 560 + lane * 170
        line(c, 100, y + 10, 1820, y + 10, CREAM, 3, 0.25)
        run = clamp((t - 262.6) / 2.0)
        person(c, start + run * 500, y + 40, who, t=t, walk=t * 1.6 + i * 0.3, s=0.55, expr="happy" if i == 0 else "worried",
               seed=i)
    line(c, 1700, 470, 1700, 960, AMBER, 6)
    tag(c, 700, 330, "ALREADY HAD A HEAD START", t, 263.6, bg=AMBER, size=36)
    S(262.6, "steps", 0.4)
    S(263.6, "pop", 0.5)


@scene(264.75, 274.35, amb=("birds", 0.3))
def s_group3_street(c, t):
    street(c, t)
    house(c, 1450, 905, 0.6, body="#c9a46a", roof="#6a4a3a")
    tree(c, 300, 905, 0.9)
    k = clamp((t - 265.0) / 3.0)
    x = lerp(-200, 760, ease_out(k))
    bike(c, x, 990, 1.0, wheel=t * 400, col=MINT)
    person(c, x - 10, 860, "lean", "hold", "happy", t=t, s=0.8, breathe=False)
    tag(c, 960, 140, "GROUP 3 · THE LOW-COST LIFERS", t, 265.4, bg=AMBER, size=40)
    S(265.4, "reveal", 0.7)
    S(266.0, "bike_bell", 0.6)
    items = [("debt", "ALMOST NO OTHER DEBT", 269.6), ("car", "ONE CAR OR NONE", 270.6),
             ("tax", "SMALL FIXED EXPENSES", 271.9), ("umbrella", "CALM LIFESTYLE", 273.4)]
    for i, (ic, lbl, t0) in enumerate(items):
        k = pop(t, t0)
        if k <= 0:
            continue
        with xf(c, 1420, 300 + i * 105, s=k):
            rrect(c, -330, -42, 660, 84, 42, "#ffffff", 0.85)
            mini_icon(c, ic, -280, 0, 0.8, "#6f8c3f")
            text(c, lbl, -230, 13, 32, INK, "Black", "left")
        S(t0, "pop", 0.5)


@scene(274.35, 286.75)
def s_group3_board(c, t):
    board(c, "#1f4030")
    tag(c, 330, 90, "GROUP 3", t, 274.4, bg=AMBER, size=30)
    rrect(c, 180, 300, 300, 100, 14, "#ffffff", 0.1)
    rrect(c, 180, 300, 300 * ease_out(at(t, 274.6, 0.6)), 100, 14, MUTED)
    text(c, "INCOME: AVERAGE", 330, 270, 30, CREAM)
    gauge(c, 330, 720, 200, 0.18, a=fade_in(t, 276.0))
    text(c, "PRESSURE: LOW", 330, 800, 34, MINT, a=fade_in(t, 276.6))
    S(276.4, "chime", 0.4)
    # house fits inside a lean life
    k = fade_in(t, 277.5)
    p = P(CREAM, 5, 0.6 * k)
    p.setPathEffect(skia.DashPathEffect.Make([20, 14], t * 30))
    c.drawRoundRect(skia.Rect(780, 280, 1300, 760), 40, 40, p)
    text(c, "A VERY LEAN LIFE", 1040, 250, 32, CREAM, a=k)
    hk = clamp((t - 277.8) / 0.6)
    house_icon(c, 1040, 560 - (1 - ease_out(hk)) * 300, 2.0, AMBER, 7, a=hk)
    S(277.9, "fit", 0.6)
    if t > 280.0:
        check_mark(c, 1440, 380, 110, MINT, prog=at(t, 280.1, 0.4))
        text(c, "POSSIBLE", 1440, 490, 40, MINT)
        S(280.1, "ding", 0.5)
    tag(c, 1500, 620, "A LIFESTYLE CHOICE", t, 281.7, bg=MINT, size=34)
    if t > 282.8:
        tag(c, 1500, 720, "NOT A CASUAL PURCHASE", t, 282.9, bg=CREAM, size=30)
        strike(c, 1500, 720, 0, t, 999)
    S(281.7, "pop", 0.5)
    S(282.9, "pop2", 0.5)
    if t > 284.6:
        sh = math.sin(t * 50) * 14 * clamp(1 - (t - 284.7) / 1.4)
        c.translate(sh, 0)
        tag(c, 1040, 900, "ONE BIG SURPRISE CAN SHAKE IT", t, 284.7, bg=ROSE, fg="#ffffff", size=36)
        S(284.7, "rumble", 0.8)


@scene(286.75, 294.95)
def s_missing(c, t):
    board(c)
    title(c, "NOTICE WHAT'S MISSING", t, 286.8, y=130)
    for i, (n, lbl, col) in enumerate(GROUPS):
        with xf(c, 290 + i * 400, 450, s=0.62):
            rrect(c, -230, -230, 460, 460, 30, col)
            text(c, n, 0, -48, 110, "#ffffff")
            text(c, lbl, 0, 140, 34, "#ffffff")
    p = P(ROSE, 6)
    p.setPathEffect(skia.DashPathEffect.Make([22, 14], 0))
    c.drawRoundRect(skia.Rect(1430, 307, 1715, 593), 22, 22, p)
    text(c, "?", 1572, 490, 120, ROSE, a=0.5 + 0.5 * math.sin(t * 5))
    if t > 288.4:
        x = lerp(2100, 1572, ease_out(clamp((t - 288.5) / 1.0)))
        person(c, x, 1000, "avg", "headhold" if t > 289.5 else "stand", "worried", t=t, s=0.85, sweat=1.0,
               walk=t * 1.4 if t < 289.5 else 0, flip=True)
        tag(c, 1000, 760, "THE AVERAGE HOUSEHOLD, STRETCHING", t, 288.6, bg=AMBER, size=34)
        S(288.5, "steps", 0.5)
    if t > 291.5:
        with xf(c, 720, 920, s=pop(t, 291.6)):
            rrect(c, -230, -50, 460, 100, 16, "#a8324a")
            text(c, "WELCOME!", 0, 16, 46, CREAM)
        S(291.6, "door_bell", 0.5)
    if t > 293.8:
        warning(c, 1260, 920, 0.7 * pop(t, 293.9))
        text(c, "MOST RISK", 1420, 940, 44, AMBER, "Black", "left", a=fade_in(t, 294.0))
        S(293.9, "alarm", 0.6)


# =====================================================================================================
# STRESS TEST
# =====================================================================================================
QS = [("1", "One income gone for 3 months?", "Could you still cover the full housing cost?", 299.2),
      ("2", "A $5,000 surprise tomorrow?", "Could you pay it without borrowing?", 304.6),
      ("3", "After all the bills...", "Can you still invest or save every month?", 310.0)]


@scene(294.95, 313.4)
def s_stress(c, t):
    board(c)
    if t < 298.6:
        k = fade_in(t, 295.0)
        house_icon(c, 700, 560, 2.2, ROSE, 7, a=k)
        hb = 1 + 0.08 * abs(math.sin(t * 6))
        with xf(c, 830, 380, s=hb * pop(t, 295.9)):
            pth = skia.Path()
            pth.moveTo(0, 30)
            pth.cubicTo(-70, -20, -40, -70, 0, -38)
            pth.cubicTo(40, -70, 70, -20, 0, 30)
            c.drawPath(pth, P(ROSE))
        tag(c, 1300, 460, "BEFORE YOU FALL IN LOVE...", t, 295.6, bg=CREAM, size=34)
        tag(c, 1300, 600, "RUN A STRESS TEST", t, 297.7, bg=AMBER, size=46)
        S(295.9, "heart", 0.6)
        S(297.8, "pop", 0.7)
        return
    clipboard(c, 960, 590, 1.25)
    text(c, "STRESS TEST", 960, 220, 48, INK)
    for i, (n, q1, q2, t0) in enumerate(QS):
        k = fade_in(t, t0)
        if k <= 0:
            continue
        y = 380 + i * 250
        with xf(c, 0, 0, alpha=k):
            rrect(c, 600, y - 40, 80, 80, 12, "#2b3a40", stroke=6)
            text(c, q1, 720, y - 6, 38, INK, "Black", "left")
            text(c, q2, 720, y + 46, 30, "#6a645a", "Bold", "left")
        S(t0, "pencil", 0.6)
        icons = ["phone", "health", "cart"]
        del icons
    # highlight current question
    cur = 0 if t < 304.6 else (1 if t < 310.0 else 2)
    y = 380 + cur * 250
    rrect(c, 580, y - 70, 760, 160, 18, AMBER, a=0.18)


@scene(313.4, 317.1)
def s_bigger(c, t):
    board(c, "#3a1f28")
    k = ease_out(clamp((t - 313.6) / 2.4))
    with xf(c, 1100, 980, s=1.0 + 1.3 * k):
        house(c, 0, 0, 0.9, body="#3c6fb0", roof="#22314f")
    person(c, 380, 1000, "avg", "shrug", "shock", t=t, s=0.6 + 0.0 * k, look=(1, -1))
    if t > 314.9:
        with xf(c, 520, 220, s=pop(t, 315.0)):
            rrect(c, -110, -70, 220, 140, 20, ROSE)
            text(c, "NO?", 0, 26, 74, "#ffffff")
        S(315.0, "error", 0.7)
    tag(c, 960, 110, "THE HOUSE IS BIGGER THAN YOUR LIFE", t, 316.0, bg=CREAM, size=40)
    S(313.6, "rumble_low", 0.5)
    S(316.0, "impact", 0.7)


@scene(317.1, 331.45)
def s_options(c, t):
    board(c)
    title(c, "NO SHAME. YOU HAVE OPTIONS.", t, 317.6, y=120, color=MINT)
    opts = [("tax", "LOOK AT A", "LOWER PRICE", 321.3), ("house", "KEEP RENTING &", "INVEST THE DIFFERENCE", 322.8),
            ("gift", "WAIT & BUILD A", "BIGGER DOWN PAYMENT", 324.8), ("car", "CHEAPER AREA OR", "SMALLER HOME", 327.4)]
    for i, (ic, a1, a2, t0) in enumerate(opts):
        k = pop(t, t0)
        if k <= 0:
            continue
        x = 300 + i * 440
        with xf(c, x, 520, s=k):
            rrect(c, -200 + 8, -220 + 12, 400, 440, 28, "#000000", 0.25)
            rrect(c, -200, -220, 400, 440, 28, "#163f47")
            rrect(c, -200, -220, 400, 440, 28, MINT, stroke=4)
            c.drawCircle(0, -100, 70, P(MINT, a=0.2))
            if i == 0:
                price_tag(c, 0, -100, "$", s=0.8, rot=-8, col=MINT)
            elif i == 1:
                mini_icon(c, "house", -20, -100, 1.6, MINT)
                c.drawPath(poly([(40, -80), (60, -130), (80, -80)]), P(AMBER))
            elif i == 2:
                jar(c, 0, -30, 0.5, 0.8)
            else:
                house_icon(c, 0, -100, 0.8, MINT, 6)
            text(c, a1, 0, 50, 30, CREAM)
            text(c, a2, 0, 100, 30 if len(a2) < 18 else 25, AMBER)
        S(t0, "card", 0.6)
    if t > 329.5:
        with xf(c, 960, 930, s=pop(t, 329.6)):
            text(c, "THE GOAL ISN'T THE BIGGEST HOUSE", 0, 0, 46, CREAM)
        strike(c, 1240, 920, 380, t, 330.6, ROSE, 8)
        S(329.6, "pop2", 0.5)


@scene(331.45, 337.1)
def s_room(c, t):
    board(c, "#123f36")
    k = fade_in(t, 331.6)
    p = P(MINT, 5, 0.7 * k)
    p.setPathEffect(skia.DashPathEffect.Make([20, 14], t * 30))
    c.drawRoundRect(skia.Rect(160, 260, 960, 940), 40, 40, p)
    house_icon(c, 420, 620, 1.6, CREAM, 7, a=k)
    person(c, 760, 900, "buyer", "cheer" if t > 333.3 else "stand", "happy", t=t, s=0.65)
    text(c, "ROOM FOR YOU", 560, 230, 40, MINT, a=fade_in(t, 333.4))
    S(333.4, "chime", 0.5)
    if t > 334.5:
        vault(c, 1440, 600, 0.9 * pop(t, 334.6), t)
        text(c, "EQUITY YOU CAN'T TOUCH", 1440, 860, 36, CREAM, a=fade_in(t, 335.4))
        if t > 335.3:
            cross_mark(c, 1440, 600, 260 * pop(t, 335.4), ROSE, 0.85)
        S(334.6, "vault", 0.6)
        S(335.4, "error", 0.5)


@scene(337.1, 341.8)
def s_margin(c, t):
    board(c)
    title(c, "REAL WEALTH IS", t, 337.2, y=160, size=50, color=CREAM)
    with xf(c, 960, 300, s=pop(t, 337.9)):
        text(c, "MARGIN", 0, 40, 130, MINT)
    S(337.9, "reveal", 0.7)
    if t > 339.2:
        with xf(c, 560, 780, s=0.6 * pop(t, 339.3)):
            house(c, 0, 200, 1.0)
        # hammer on the roof
        ang = -30 + 40 * abs(math.sin(t * 9))
        with xf(c, 640, 600, rot=ang):
            rrect(c, -8, 0, 16, 110, 6, "#7a5a44")
            rrect(c, -36, -16, 72, 30, 6, "#9aa4a8")
        text(c, "FIX THE ROOF", 560, 1000, 36, CREAM)
        for i in range(3):
            S(339.4 + i * 0.35, "hammer", 0.5)
    if t > 340.4:
        k = pop(t, 340.5)
        with xf(c, 1360, 760, s=k):
            jar(c, 0, 120, 0.9, 0.3 + 0.4 * clamp((t - 340.5) / 1.2))
            c.drawPath(poly([(140, 0), (180, -80), (220, 0)]), P(MINT))
        text(c, "...AND STILL INVEST", 1360, 1000, 36, MINT, a=fade_in(t, 340.6))
        S(340.6, "coin", 0.6)


@scene(341.8, 346.0, amb=("night", 0.4))
def s_sleep(c, t):
    interior(c, wall="#2a3350", floor="#3a3a50", window=True, night=True)
    bed_scene(c, 900, 900, 1.1, t, eyes_open=False)
    zzz(c, 700, 640, t)
    clock(c, 1500, 680, 80, 2, 0)
    # floating math that pops away
    for i, s_ in enumerate(["$4,300", "+$800", "–$3,500", "÷ 12"]):
        k = clamp((t - 342.0 - i * 0.2) / 0.3) * (1 - clamp((t - 343.0 - i * 0.12) / 0.25))
        if k > 0:
            text(c, s_, 450 + i * 240, 420 - i * 30, 46, ROSE, a=k)
        S(343.0 + i * 0.12, "pop2", 0.3)
    tag(c, 1500, 470, "2:00 AM", t, 343.8, bg=CREAM, size=34)
    S(343.8, "clock", 0.5)
    if t > 344.5:
        tag(c, 960, 140, "RUN YOUR OWN NUMBERS", t, 344.6, bg=AMBER, size=44)
        S(344.6, "pop", 0.6)


@scene(346.0, 352.6)
def s_rules(c, t):
    board(c)
    rows = [("✓", "INCLUDE EVERY COST", 346.3), ("✓", "BE HONEST ABOUT YOUR INCOME", 347.5)]
    for i, (_, lbl, t0) in enumerate(rows):
        k = fade_in(t, t0)
        if k <= 0:
            continue
        y = 260 + i * 140
        check_mark(c, 420, y - 14, 70, MINT, prog=at(t, t0, 0.4))
        text(c, lbl, 500, y + 6, 48, CREAM, "Black", "left", a=k)
        S(t0, "pencil", 0.5)
    if t > 349.7:
        gauge(c, 600, 820, 220, 0.85, a=fade_in(t, 349.8))
        text(c, "BANK'S RISK LIMIT", 600, 920, 34, MUTED, a=fade_in(t, 350.5))
        with xf(c, 960, 780, s=pop(t, 351.3)):
            c.drawCircle(0, 0, 60, P(ROSE))
            text(c, "≠", 0, 26, 80, "#ffffff")
        gauge(c, 1320, 820, 220, 0.35, a=fade_in(t, 351.6))
        text(c, "YOUR LIFE LIMIT", 1320, 920, 34, MINT, a=fade_in(t, 351.8))
        S(351.3, "impact", 0.6)


@scene(352.6, 361.8)
def s_disclaimer(c, t):
    board(c)
    with xf(c, 960, 480, s=pop(t, 352.8)):
        rrect(c, -620, -230, 1240, 460, 30, "#000000", 0.3)
        rrect(c, -620, -230, 1240, 460, 30, CREAM, stroke=4)
        text(c, "FOR EDUCATION & GENERAL", 0, -100, 52, CREAM)
        text(c, "INFORMATION ONLY", 0, -36, 52, CREAM)
        a = fade_in(t, 356.0)
        text(c, "Your numbers, rates and taxes will differ.", 0, 70, 38, AMBER, "Bold", a=a)
        text(c, "Not financial advice.", 0, 130, 32, MUTED, "Bold", a=a)
    S(352.8, "pop", 0.5)
    if t > 358.6:
        with xf(c, 960, 900, s=pop(t, 358.7)):
            rrect(c, -360, -60, 720, 120, 60, AMBER)
            text(c, "CALCULATE YOUR OWN SITUATION", 0, 14, 36, INK)
        S(358.7, "type", 0.5)


@scene(361.8, 373.1)
def s_next(c, t):
    board(c)
    title(c, "NEXT VIDEO", t, 362.0, y=130, color=AMBER)
    k = pop(t, 362.2)
    with xf(c, 760, 600, s=k):
        house(c, 0, 260, 0.9, body="#2f8f83", roof="#7a3b3b")
    # x-ray scan reveals the hidden cost
    if t > 366.4:
        sk = clamp((t - 366.5) / 1.0)
        sy = lerp(220, 860, sk)
        line(c, 460, sy, 1060, sy, MINT, 6, 0.9 * (1 - clamp((t - 367.6) / 0.4)))
        if t > 367.2:
            glow(c, 760, 600, 240, AMBER, 0.55 + 0.15 * math.sin(t * 6))
            with xf(c, 760, 620, s=pop(t, 367.3)):
                c.drawCircle(0, 0, 90, P(AMBER))
                text(c, "?", 0, 44, 130, INK)
        S(366.5, "scan", 0.6)
        S(367.3, "sting_mystery", 0.7)
    if t > 368.4:
        tag(c, 1420, 470, "HIDDEN IN EVERY PURCHASE", t, 368.5, bg=CREAM, size=34)
    if t > 371.5:
        with xf(c, 1420, 640, s=pop(t, 371.7)):
            text(c, "TENS OF", 0, 0, 80, ROSE)
            text(c, "THOUSANDS", 0, 90, 80, ROSE)
        S(371.7, "impact", 0.8)
        money_rain(c, t, 371.8, n=10)
    # subscribe button
    if t > 363.8:
        with xf(c, 1420, 900, s=pop(t, 363.9)):
            pressed = 364.6 < t < 364.9
            rrect(c, -190, -50, 380, 100, 50, ROSE if not pressed else "#c84a5e")
            text(c, "WATCH NEXT ▶" if t < 364.5 else "SUBSCRIBED ✓", 0, 16, 38, "#ffffff")
        S(363.9, "pop", 0.6)
        S(364.6, "click", 0.8)


# =====================================================================================================
SCENES.sort(key=lambda s: s[0])


def render_frame(c, t):
    c.clear(C(BOARD2))
    sc = SCENES[-1]
    for s_ in SCENES:
        if s_[0] <= t < s_[1]:
            sc = s_
            break
    t0, t1, fn = sc
    dur = max(0.5, t1 - t0)
    z = 1.0 + 0.03 * (t - t0) / dur + 0.04 * (1 - ease_out(at(t, t0, 0.45)))
    c.save()
    c.translate(W / 2, H / 2)
    c.scale(z, z)
    c.translate(-W / 2 + math.sin(t * 0.7) * 3, -H / 2 + math.cos(t * 0.5) * 2)
    fn(c, t)
    c.restore()
    vignette(c, 0.42)
    grain(c, t, 0.045)
    # quick dip at cuts
    d = min(t - t0, t1 - t)
    if d < 0.06:
        c.drawRect(skia.Rect(0, 0, W, H), P("#000000", a=0.35 * (1 - d / 0.06)))


def build_cues():
    """Run every scene over its time range once so all S() calls inside scene bodies are collected."""
    s = skia.Surface(64, 36)
    c = s.getCanvas()
    for t0, t1, fn in SCENES:
        t = t0
        while t < t1:
            c.save()
            fn(c, t)
            c.restore()
            t += 0.5
        c.save()
        fn(c, t1 - 0.01)
        c.restore()
    seen, out = set(), []
    for tt, n, g in SFX:
        key = (round(tt, 2), n)
        if key in seen or g <= 0:
            continue
        seen.add(key)
        out.append((tt, n, g))
    return sorted(out)
