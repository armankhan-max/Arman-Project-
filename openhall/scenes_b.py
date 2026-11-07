"""Timeline part B: items 6-12, the wrap-up and the end screen. Times are absolute seconds."""
import math
import random

import skia

from pgfx import *  # noqa: F401,F403
from scenes_a import (FY, cam, push, pin, slide, counter, tagpop, calendar, card_scene, list_board, notif,
                      _cracked)


# ================================================================ 6. PHONE UPGRADES
def s_holding(c, t):
    cam(c, push(t, 163.1, 166.0, 1.0, 1.08), 960, 540, t, drift=0.5)
    dark_studio(c, t, "#1b2740", light=(960, 360))
    # a stickman hand holding a real-looking phone, close up
    sway = 2 * math.sin(t * 1.3)
    with xf(c, 960, 560, rot=sway):
        photo_phone(c, 0, 0, 1.15, rot=-4, screen=app_screen_home, t=t)
        for i in range(4):
            c.drawCircle(175, -120 + i * 90, 46, P("#14141c"))
            c.drawCircle(175, -120 + i * 90, 42, P(INK))
        c.drawCircle(-170, 120, 56, P("#14141c"))
        c.drawCircle(-170, 120, 52, P(INK))
        rrect(c, -40, 300, 260, 400, 80, "#14141c")
        rrect(c, -36, 304, 252, 392, 76, OUTFITS["sam"]["suit"])
    tagpop(c, t, 164.06, 960, 160, "ALMOST EVERYONE IS HOLDING ONE", "#ffffff", "#0b1018", 40)


def _prop_phone(c, t):
    photo_phone(c, -90, 10, 0.95, rot=-10, screen=app_screen_home, t=t, color="#2b2d33")
    photo_phone(c, 110, 40, 0.95, rot=8, screen=app_screen_home, t=t, color="#d9d4cc")


def s_leaps(c, t):
    info_board(c, t)
    cam(c, push(t, 168.3, 175.3, 1.0, 1.04), 960, 540, t, drift=0.4)
    base = 860
    gains = [260, 220, 180, 60, 40, 30, 22]
    for i, g in enumerate(gains):
        st = 168.5 + i * 0.25 if i < 3 else 171.2 + (i - 3) * 0.3
        k = ease_out(at(t, st, 0.5))
        x = 360 + i * 200
        bar(c, x, base, 120, g * 2 * k, CYN if i < 3 else "#5f7aa5", 0.95)
        text(c, f"GEN {i + 1}", x, base + 50, 28, "#8796ad", "Bold", a=clamp(k * 2))
    text(c, "HOW MUCH BETTER EACH NEW PHONE GOT", 960, 200, 40, "#c9d3e3", "Black", a=clamp(at(t, 168.4, 0.4)))
    tagpop(c, t, 169.84, 560, 260, "HUGE LEAPS", CYN, "#0b1018", 44)
    tagpop(c, t, 173.22, 1260, 600, "SMALL STEPS", "#ffffff", "#0b1018", 44)
    k = ease_out(at(t, 174.3, 0.5))
    if k:
        line(c, 260, 330, 1660, 330, RED, 8, k)
        text(c, "THE PRICE: STILL HIGH", 1660, 300, 46, RED, "Black", align="right", a=k)


def s_tradein(c, t):
    studio(c, t)
    cam(c, push(t, 175.3, 182.5, 1.0, 1.05), 960, 540, t, drift=0.4)
    photo_phone(c, 480, 520, 0.95, rot=-6, screen=app_screen_home, t=t)
    tagpop(c, t, 175.5, 480, 900, "YOU PAID $1,000", "#0b1018", "#ffffff", 44)
    k = ease_out(at(t, 177.04, 0.5))
    if k:
        arrow(c, 760, 520, 760 + 280 * k, 520, ACC, 16, k)
        for i in range(4):
            photo_bill(c, 1300 + i * 26, 470 + i * 18, 0.7, rot=-6 + i * 4, amount="100", a=k)
        tagpop(c, t, 177.44, 1360, 280, "YOU GET BACK $400", GRN, "#0b1018", 44)
    k2 = ease_out(at(t, 179.44, 0.5))
    if k2:
        with xf(c, 1360, 840, 0.8 + 0.2 * back_out(k2), alpha=k2):
            rrect(c, -330, -70, 660, 140, 28, RED)
            text(c, "−$600 EVERY UPGRADE", 0, 20, 52, "#ffffff", "Black")
    # repeating losses
    for i in range(3):
        k3 = at(t, 180.8 + i * 0.35, 0.3)
        if k3 > 0:
            with xf(c, 1060 + i * 150, 990, back_out(k3), alpha=k3):
                rrect(c, -64, -30, 128, 60, 14, RED, 0.85)
                text(c, "−$600", 0, 14, 32, "#ffffff", "Black")


def s_honest(c, t):
    cam(c, push(t, 182.5, 189.7, 1.0, 1.1), 960, 560, t)
    bg(c, "home", 8, dim=0.2)
    pose = "hold2" if t < 187.3 else "shrug"
    figure(c, 960, FY(1.1, 860), "sam", pose, "focus" if t < 187.3 else "smile", t, s=1.1, look=(0, 0.5))
    if t < 187.3:
        for i, (dx, col) in enumerate(((-330, "#2b2d33"), (330, "#d9d4cc"))):
            k, a = pin(t, 183.0 + i * 0.3, 0.4)
            if a:
                with xf(c, 960 + dx, 520, k, alpha=a):
                    photo_phone(c, 0, 0, 0.5, rot=-6 if i == 0 else 6, screen=app_screen_home, t=t, color=col)
                    text(c, ("MINE", "NEW")[i], 0, 220, 40, "#ffffff", "Black")
        k = ease_out(at(t, 184.5, 0.4))
        if k:
            text(c, "?", 960, 340, 180, ACC, "Black", a=k)
        tagpop(c, t, 183.84, 960, 150, "WHAT CAN IT DO THAT MINE CAN'T?", "#ffffff", "#0b1018", 40)
    else:
        tagpop(c, t, 188.68, 960, 200, "YOU HAVE YOUR ANSWER", GRN, "#0b1018", 48)


# ================================================================ 7. NAME BRANDS
def s_kitchen(c, t):
    studio(c, t, warm=0.25)
    cam(c, push(t, 189.7, 193.5, 1.0, 1.06), 960, 560, t, drift=0.4)
    photo_pack(c, 780, 880, 1.2, "#d64933", "CRUNCH")
    k, a = pin(t, 190.8, 0.45)
    if a:
        with xf(c, 1180, 420, k, alpha=a):
            rrect(c, -170, -80, 340, 160, 26, ACC)
            text(c, "+ $ NAME", 0, 26, 64, "#0b1018", "Black")
    tagpop(c, t, 192.22, 960, 160, "IN YOUR KITCHEN", "#ffffff", "#0b1018", 42)


def _prop_brands(c, t):
    photo_pack(c, -110, 300, 1.0, "#d64933", "CRUNCH")
    photo_pack(c, 150, 300, 1.0, "#e8e3d8", "CORN FLAKES", plain=True)


def price_tag(c, x, y, s, price, col="#ffd23f", fg="#111111", a=1.0, strike=None):
    with xf(c, x, y, s, alpha=a):
        c.drawRect(skia.Rect(-110, -50, 130, 70), blur_paint("#000000", 10, 0.35))
        c.drawRect(skia.Rect(-120, -60, 120, 60), P(col))
        text(c, price, 0, 22, 62, fg, "Black")
        if strike:
            line(c, -100, 0, 100, 0, RED, 8)


def s_aisle(c, t):
    cam(c, push(t, 196.6, 203.1, 1.0, 1.08), 960, 600, t)
    bg(c, "store", 5, dim=0.08)
    c.drawRect(skia.Rect(300, 880, 1620, 920), P("#8a96a3"))
    c.drawRect(skia.Rect(300, 920, 1620, 1000), P("#6b7682"))
    k1, a1 = pin(t, 198.13, 0.45)
    k2, a2 = pin(t, 198.5, 0.45)
    if a1:
        with xf(c, 700, 880, k1, alpha=a1):
            photo_pack(c, 0, 0, 1.15, "#d64933", "CRUNCH")
        price_tag(c, 700, 960, 0.8, "$5.49", a=a1)
    if a2:
        with xf(c, 1220, 880, k2, alpha=a2):
            photo_pack(c, 0, 0, 1.15, "#e8e3d8", "CORN FLAKES", plain=True)
        price_tag(c, 1220, 960, 0.8, "$3.79", a=a2)
    tagpop(c, t, 200.68, 700, 330, "FAMOUS NAME", "#ffffff", "#0b1018", 40)
    tagpop(c, t, 201.9, 1220, 330, "PLAINER & CHEAPER", GRN, "#0b1018", 40)


def s_pills(c, t):
    studio(c, t, key="#e7ecef", rim="#a8b2bb")
    cam(c, push(t, 203.1, 208.2, 1.0, 1.05), 960, 560, t, drift=0.4)
    photo_bottle(c, 620, 860, 1.25, name="FAMOUS", sub="IBUPROFEN", label_col="#c0392b")
    photo_bottle(c, 1300, 860, 1.25, name="STORE", sub="IBUPROFEN", plain=True, label_col="#2c8fd6")
    k = ease_out(at(t, 204.62, 0.5))
    if k:
        text(c, "=", 960, 600, 180, "#333333", "Black", a=k)
    tagpop(c, t, 204.9, 960, 170, "SAME ACTIVE INGREDIENT", GRN, "#0b1018", 46)
    tagpop(c, t, 206.32, 960, 270, "SAME STRENGTH: 200 mg", GRN, "#0b1018", 46)
    price_tag(c, 620, 980, 0.75, "$8.99", a=clamp(at(t, 203.4, 0.3)))
    price_tag(c, 1300, 980, 0.75, "$3.49", a=clamp(at(t, 203.6, 0.3)))


def s_cheaper(c, t):
    studio(c, t)
    cam(c, push(t, 208.2, 214.0, 1.0, 1.05), 960, 560, t, drift=0.4)
    items = [("box", "#d64933", "CRUNCH", False, 420), ("box", "#e8e3d8", "CORN FLAKES", True, 720),
             ("jug", "#2c6fd6", "SPARKLE", False, 1200), ("jug", "#e8e3d8", "DETERGENT", True, 1500)]
    for i, (kind, col, nm, plain, x) in enumerate(items):
        k, a = pin(t, 208.3 + i * 0.15, 0.4)
        if a:
            with xf(c, x, 820, k * 0.95, alpha=a):
                photo_pack(c, 0, 0, 1.0, col, nm, plain=plain, kind=kind)
    tagpop(c, t, 210.68, 960, 170, "OFTEN CLOSE TO IDENTICAL", "#ffffff", "#0b1018", 44)
    for x in (720, 1500):
        tagpop(c, t, 212.16, x, 930, "−20 to 30%", GRN, "#0b1018", 44)


def s_ads(c, t):
    info_board(c, t)
    cam(c, push(t, 214.0, 216.1, 1.0, 1.05), 960, 540, t, drift=0.4)
    # price stack: product + advertising
    k = ease_out(at(t, 214.1, 0.4))
    bar(c, 760, 880, 260, 300 * k, "#5f7aa5", 1.0)
    k2 = ease_out(at(t, 214.6, 0.5))
    if k2:
        rrect(c, 630, 880 - 300 - 180 * k2, 260, 180 * k2, 14, ACC)
        text(c, "EXTRA", 760, 880 - 300 - 90 * k2 + 14, 40, "#0b1018", "Black", a=k2)
    text(c, "THE PRODUCT", 760, 760, 34, "#ffffff", "Black", a=k)
    k3 = ease_out(at(t, 215.3, 0.4))
    if k3:
        arrow(c, 920, 510, 1130, 510, ACC, 14, k3)
        with xf(c, 1420, 500, 0.8 + 0.2 * back_out(k3), alpha=k3):
            rrect(c, -260, -150, 520, 300, 20, "#16233a")
            rrect(c, -260, -150, 520, 300, 20, ACC, stroke=6)
            text(c, "ADVERTISING", 0, 18, 58, ACC, "Black")
            c.drawRect(skia.Rect(-20, 150, 20, 330), P("#2b3d5c"))


def s_try5(c, t):
    studio(c, t, warm=0.15)
    cam(c, push(t, 216.1, 222.0, 1.0, 1.05), 960, 560, t, drift=0.4)
    names = ["CEREAL", "RICE", "SOAP", "PASTA", "PAPER"]
    for i, nm in enumerate(names):
        x = 360 + i * 300
        k, a = pin(t, 217.06 + i * 0.12, 0.4)
        if a:
            with xf(c, x, 700, k * 0.75, alpha=a):
                photo_pack(c, 0, 0, 1.0, "#e8e3d8", nm, plain=True, kind="box" if i % 2 == 0 else "jug")
            check_mark(c, x + 80, 330, 70, GRN, 1, at(t, 218.0 + i * 0.12, 0.35))
    tagpop(c, t, 216.44, 960, 160, "TRY 5 STORE-BRAND ITEMS THIS MONTH", "#ffffff", "#0b1018", 40)
    k = ease_out(at(t, 219.98, 0.5))
    if k:
        with xf(c, 960, 900, 0.85 + 0.15 * back_out(k), alpha=k):
            rrect(c, -380, -70, 760, 140, 30, GRN)
            text(c, "MONEY YOU NEVER NEEDED", 0, 20, 50, "#0b1018", "Black")


# ================================================================ 8. COFFEE
def _prop_coffee(c, t):
    photo_cup(c, 0, 330, 1.15, t, label="CAFE")


def s_cafe(c, t):
    cam(c, push(t, 225.6, 230.0, 1.0, 1.08), 960, 560, t)
    bg(c, "cafe", 7)
    rrect(c, 640, 650, 640, 26, 10, "#6b4a33")
    c.drawRect(skia.Rect(940, 676, 980, 860), P("#4a3324"))
    figure(c, 760, 690, "sam", "sit", "happy", t, s=0.95, face=1)
    photo_cup(c, 1080, 650, 0.32, t, label="")
    for i, (s, st) in enumerate((("A BREAK", 226.38), ("A RITUAL", 226.66), ("A PLACE TO SIT", 227.6))):
        tagpop(c, t, st, 1500, 260 + i * 110, s, "#f4e9d8", "#2a1d16", 40)
    k = ease_out(at(t, 228.76, 0.4))
    if k:
        with xf(c, 1500, 640, alpha=k):
            rrect(c, -230, -60, 460, 120, 26, GRN)
            text(c, "REAL VALUE", -20, 20, 50, "#0b1018", "Black")
            check_mark(c, 180, 4, 54, "#ffffff", 1, at(t, 229.0, 0.4))


def s_coffee_year(c, t):
    info_board(c, t)
    cam(c, push(t, 230.0, 236.8, 1.0, 1.04), 960, 540, t, drift=0.4)
    if t < 233.9:
        big_number(c, 360, 470, "$5", 180, "#ffffff", a=clamp(at(t, 230.32, 0.3)), sub="EVERY WORKDAY")
        k = ease_out(at(t, 231.38, 0.4))
        if k:
            text(c, "× 260 workdays", 800, 520, 52, "#8796ad", "Black", a=k)
        if t > 232.34:
            v = counter(t, 232.34, 1.0, 0, 1300)
            big_number(c, 1440, 470, "≈" + money(v), 140, ACC, sub="A YEAR")
    else:
        k = ease_out(at(t, 233.9, 0.5))
        x0 = 640
        with xf(c, 0, 0, alpha=k):
            bar(c, x0, 880, 260, 560, ACC, 1.0)
            text(c, "$1,300", x0, 290, 64, ACC, "Black")
            text(c, "COFFEE SHOP", x0, 940, 36, "#c9d3e3", "Black")
            photo_cup(c, x0, 860, 0.6, t, label="CAFE", steam=False)
        k2 = ease_out(at(t, 234.24, 0.6))
        if k2:
            bar(c, 1280, 880, 260, 90 * k2, GRN, 1.0)
            text(c, "AT HOME", 1280, 940, 36, "#c9d3e3", "Black", a=k2)
            photo_mug(c, 1280, 780, 0.6, t)
            tagpop(c, t, 235.38, 1280, 560, "A SMALL FRACTION", GRN, "#0b1018", 40)


def s_twice(c, t):
    studio(c, t, warm=0.2)
    cam(c, push(t, 236.8, 240.7, 1.0, 1.05), 960, 540, t, drift=0.4)
    days = ["MON", "TUE", "WED", "THU", "FRI"]
    picks = {1: 238.48, 4: 238.62}
    for i, d in enumerate(days):
        x = 360 + i * 300
        rrect(c, x - 120, 360, 240, 380, 24, "#ffffff", 0.9)
        rrect(c, x - 120, 360, 240, 70, 24, "#d64933")
        text(c, d, x, 410, 40, "#ffffff", "Black")
        if i in picks:
            k, a = pin(t, picks[i], 0.4)
            if a:
                with xf(c, x, 700, k * 0.55, alpha=a):
                    photo_cup(c, 0, 0, 1.0, t, label="CAFE")
        else:
            k = ease_out(at(t, 238.8, 0.4))
            if k:
                with xf(c, x, 680, 0.55, alpha=k):
                    photo_mug(c, 0, 0, 1.0, t)
    tagpop(c, t, 237.36, 960, 200, "YOU DON'T HAVE TO GIVE IT UP", "#ffffff", "#0b1018", 42, end=238.4)
    tagpop(c, t, 238.5, 960, 200, "TWICE A WEEK: A TREAT", GRN, "#0b1018", 46)


def wallet(c, x, y, s=1.0, leak=0.0, t=0.0):
    with xf(c, x, y, s):
        soft_shadow(c, 0, 170, 520, 40, 0.5, 14)
        rrect(c, -240, -150, 480, 300, 36, "#5a3a24")
        fill_shader(c, skia.Rect(-240, -150, 240, 150), linear(0, -150, 0, 150, [("#ffffff", 0.15),
                                                                                 ("#000000", 0.25)]))
        rrect(c, -240, -150, 480, 120, 36, "#6e4a30")
        eff = skia.DashPathEffect.Make([14, 10], 0)
        pp = P("#d9b48a", 4, 0.7)
        pp.setPathEffect(eff)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-224, -134, 224, 134), 28, 28), pp)
        rrect(c, 150, -40, 110, 80, 20, "#4a2f1c")
        c.drawCircle(200, 0, 14, P("#d8b45a"))
        if leak > 0:
            for i in range(int(4 + 10 * leak)):
                ph = ((t * (0.8 + 0.6 * leak)) + i * 0.137) % 1
                photo_coin(c, -60 + (i % 5) * 30, 150 + ph * 420, 22, a=1 - ph)


def s_leak(c, t):
    studio(c, t)
    cam(c, push(t, 240.7, 248.2, 1.0, 1.06), 960, 540, t, drift=0.4)
    if t < 242.5:
        with xf(c, 960, 560):
            photo_cup(c, 0, 260, 1.0, t, label="CAFE")
        k = ease_out(at(t, 241.28, 0.4))
        if k:
            tagpop(c, t, 241.28, 960, 160, "A HABIT YOU CHOSE = A PLEASURE", GRN, "#0b1018", 46)
    else:
        leak = 0.3 + 0.7 * ease_out(at(t, 245.6, 1.4))
        wallet(c, 960, 420, 1.0, leak, t)
        tagpop(c, t, 242.7, 960, 120, "A HABIT YOU NEVER QUESTIONED = A LEAK", RED, "#ffffff", 42)
        tagpop(c, t, 245.78, 960, 950, "AND ONE THING MAKES LEAKS WORSE", "#ffffff", "#0b1018", 40)


# ================================================================ 9. BUY NOW PAY LATER
def _prop_bnpl(c, t):
    photo_card(c, -60, -40, 0.9, rot=-10)
    with xf(c, 140, 150):
        icon_tile(c, 0, 0, 170, "#7d5cc8", "split")


def s_split(c, t):
    studio(c, t)
    cam(c, push(t, 250.5, 253.8, 1.0, 1.05), 960, 540, t, drift=0.4)
    photo_box(c, 520, 820, 1.0, color="#2b2d33", label="HEADPHONES", printcol="#ffffff")
    sp = ease_out(at(t, 250.98, 0.8))
    if sp < 1:
        with xf(c, 1300, 520, alpha=1 - sp):
            rrect(c, -260, -100, 520, 200, 30, "#0b1018")
            text(c, "$200", 0, 36, 110, "#ffffff", "Black")
    if sp > 0:
        for i in range(4):
            x = 1300 + (i - 1.5) * 170 * sp
            y = 520 + (i % 2) * 0
            with xf(c, x, y, alpha=sp):
                rrect(c, -75, -75, 150, 150, 24, "#7d5cc8")
                text(c, "$50", 0, 20, 56, "#ffffff", "Black")
                text(c, f"{i + 1}/4", 0, 60, 22, "#e0d6ff", "Bold")
    tagpop(c, t, 251.24, 1300, 780, "4 EASY PAYMENTS", "#7d5cc8", "#ffffff", 44)


def s_brain(c, t):
    info_board(c, t)
    cam(c, push(t, 253.8, 259.5, 1.0, 1.04), 960, 540, t, drift=0.4)
    if t < 256.2:
        figure(c, 520, FY(1.0, 900), "sam", "think", "smile", t, look=(1, -0.4))
        k = ease_out(at(t, 254.6, 0.4))
        with xf(c, 1240, 460, alpha=k):
            text(c, "$200", -140, 30, 110, "#5f7aa5", "Black")
            arrow(c, 20, 0, 160, 0, ACC, 12)
            text(c, "$50", 300, 40, 160, GRN, "Black")
        tagpop(c, t, 255.02, 1240, 690, "FEELS CHEAPER", GRN, "#0b1018", 44)
    else:
        tagpop(c, t, 256.22, 960, 180, "MANY PEOPLE SPEND MORE WHEN THEY CAN SPLIT", "#ffffff", "#0b1018", 38)
        k1 = ease_out(at(t, 256.6, 0.5))
        k2 = ease_out(at(t, 257.44, 0.6))
        bar(c, 760, 860, 240, 300 * k1, "#5f7aa5", 1.0, "PAY IN FULL")
        bar(c, 1160, 860, 240, 470 * k2, "#7d5cc8", 1.0, "SPLIT IT")


def s_missed(c, t):
    studio(c, t, key="#e7e3dc")
    cam(c, push(t, 259.5, 263.0, 1.0, 1.05), 960, 540, t, drift=0.4)
    calendar(c, 620, 560, 760, 760, t, "PAYMENTS", marks=[(3, 259.7), (17, 260.0)], start_day=1)
    k, a = pin(t, 260.54, 0.4)
    if a:
        with xf(c, 1400, 420, k, alpha=a):
            rrect(c, -260, -90, 520, 180, 30, RED)
            text(c, "MISSED", 0, 0, 58, "#ffffff", "Black")
            text(c, "PAYMENT", 0, 60, 40, "#ffffff", "Black")
    tagpop(c, t, 261.68, 1400, 640, "+ LATE FEE", "#0b1018", "#ffffff", 50)
    tagpop(c, t, 261.96, 1400, 760, "+ STRESS", "#0b1018", "#ffffff", 50)


def s_paycheck(c, t):
    info_board(c, t)
    cam(c, push(t, 263.0, 267.5, 1.0, 1.04), 960, 540, t, drift=0.4)
    text(c, "YOUR PAYCHECK", 960, 260, 48, "#c9d3e3", "Black")
    x0, x1, y = 260, 1660, 420
    rrect(c, x0, y, x1 - x0, 160, 20, GRN)
    plans = ["SHOES", "PHONE", "SOFA", "TV", "TRIP", "GAME", "JACKET", "BLENDER"]
    used = 0.0
    for i, p in enumerate(plans):
        k = ease_out(at(t, 263.4 + i * 0.32, 0.35))
        if k <= 0:
            continue
        w = (x1 - x0) * 0.115 * k
        rrect(c, x0 + used, y, w, 160, 14, "#7d5cc8" if i % 2 == 0 else "#9b7de0")
        if k > 0.6:
            with xf(c, x0 + used + w / 2, y + 90, rot=-90):
                text(c, p, 0, 10, 26, "#ffffff", "Black")
        used += w
    tagpop(c, t, 264.74, 960, 720, "ALREADY PROMISED", RED, "#ffffff", 50)
    tagpop(c, t, 265.82, 960, 830, "TO THINGS YOU FORGOT", "#ffffff", "#0b1018", 40)


def s_rule(c, t):
    cam(c, push(t, 267.5, 277.1, 1.0, 1.06), 960, 560, t)
    bg(c, "home", 8, dim=0.2)
    tagpop(c, t, 267.6, 960, 120, "A SIMPLE RULE", ACC, "#0b1018", 48)
    if t < 271.4:
        figure(c, 560, FY(), "sam", "think", "focus", t, look=(1, -0.5))
        k, a = pin(t, 268.82, 0.4)
        if a:
            thought(c, 1180, 400, 760, 220, a=a, s=k)
            with xf(c, 1180, 400, k, alpha=a):
                text(c, "CAN'T AFFORD IT TODAY?", 0, -20, 46, "#1b1b2f", "Black")
                if t > 270.0:
                    text(c, "ASK WHY YOU WANT IT", 0, 50, 46, "#d4920f", "Black", a=clamp(at(t, 270.0, 0.3)))
    elif t < 273.9:
        figure(c, 560, FY(), "sam", "stand", "smile", t)
        for i in range(3):
            k, a = pin(t, 271.86 + i * 0.25, 0.35)
            if a:
                with xf(c, 1000 + i * 220, 420, k, alpha=a):
                    rrect(c, -90, -90, 180, 180, 24, "#ffffff")
                    text(c, f"WEEK {i + 1}", 0, 12, 34, "#1b1b2f", "Black")
        k = ease_out(at(t, 272.98, 0.4))
        if k:
            photo_jar(c, 1220, 920, 0.6, fill=0.2 + 0.4 * ease_out(at(t, 273.0, 0.8)), t=t, label="SAVE IT")
    else:
        figure(c, 560, FY(), "sam", "shrug", "happy", t)
        fade = 1 - ease_out(at(t, 274.12, 1.0))
        thought(c, 1180, 400, 520, 240, a=0.9 * (0.15 + 0.85 * fade))
        with xf(c, 1180, 420, alpha=fade):
            photo_box(c, 0, 90, 0.42, color="#2b2d33", label="", printcol="#ffffff")
        k = ease_out(at(t, 275.44, 0.5))
        if k:
            with xf(c, 1180, 820, 0.85 + 0.15 * back_out(k), alpha=k):
                rrect(c, -360, -66, 720, 132, 30, GRN)
                text(c, "MONEY KEPT. ZERO EFFORT.", 0, 18, 46, "#0b1018", "Black")


def s_bleed(c, t):
    cam(c, push(t, 277.1, 279.8, 1.0, 1.08), 960, 560, t)
    bg(c, "bank", 6, dim=0.15)
    for i in range(8):
        ph = ((t - 277.0) * 0.7 + i * 0.125) % 1
        photo_coin(c, 960 + (i % 3 - 1) * 60, 300 + ph * 600, 24, a=(1 - ph) * clamp(at(t, 277.7, 0.5)))
    tagpop(c, t, 278.12, 960, 200, "SLOWLY. AND LEGALLY.", RED, "#ffffff", 48)


# ================================================================ 10. BANK FEES
def _prop_bank(c, t):
    photo_card(c, 0, 0, 1.0, rot=-8)


def s_fees(c, t):
    studio(c, t, key="#e3e6ea", rim="#9aa2ad")
    cam(c, push(t, 280.7, 292.1, 1.0, 1.05), 960, 540, t, drift=0.4)
    merge = ease_out(at(t, 288.86, 1.0))
    fees = [("MONTHLY FEE", "$12", 281.54, (520, 300)), ("OVERDRAFT FEE", "$35", 282.82, (1400, 300)),
            ("ATM FEE", "$3", 283.64, (520, 780)), ("BELOW MINIMUM", "$10", 285.02, (1400, 780))]
    photo_card(c, 960, 540, 0.8 * (1 - merge * 0.4), rot=-6)
    for i, (nm, amt, st, (x, y)) in enumerate(fees):
        k, a = pin(t, st, 0.4)
        if a <= 0:
            continue
        x2, y2 = lerp(x, 960, merge), lerp(y, 540, merge)
        with xf(c, x2, y2, k * (1 - 0.6 * merge), alpha=a * (1 - merge * 0.9)):
            rrect(c, -230, -90, 460, 180, 26, "#ffffff")
            rrect(c, -230, -90, 460, 180, 26, RED, stroke=5)
            text(c, nm, 0, -14, 34, "#333333", "Black")
            text(c, amt, 0, 58, 64, RED, "Black")
    tagpop(c, t, 287.98, 960, 150, "EACH ONE IS SMALL", "#ffffff", "#0b1018", 44, end=288.9)
    if merge > 0.5:
        k2 = ease_out(at(t, 289.6, 0.5))
        with xf(c, 960, 540, 0.8 + 0.2 * back_out(k2), alpha=k2):
            rrect(c, -360, -110, 720, 220, 36, RED)
            text(c, "IT ADDS UP", 0, 34, 96, "#ffffff", "Black")
        tagpop(c, t, 291.18, 960, 860, "AND BUYS YOU NOTHING", "#0b1018", "#ffffff", 46)


def s_switch(c, t):
    cam(c, push(t, 292.1, 296.3, 1.0, 1.06), 960, 560, t)
    bg(c, "bank", 6, dim=0.1)
    figure(c, 1440, FY(), "banker", "stand", "neutral" if t < 294.4 else "smile", t, face=-1)
    figure(c, 640, FY(), "sam", "point" if 293.6 < t < 295.2 else "stand", "focus", t, talk=0.0)
    tagpop(c, t, 292.34, 960, 160, "FEE-FREE ACCOUNTS EXIST", GRN, "#0b1018", 48)
    if t > 293.78:
        k, a = pin(t, 293.78, 0.35)
        with xf(c, 900, 360, k, alpha=a * clamp((295.3 - t) / 0.2)):
            rrect(c, -230, -64, 460, 128, 60, "#ffffff")
            text(c, "REMOVE THIS FEE?", 0, 16, 40, "#1b1b2f", "Black")
    if t > 295.22:
        k = ease_out(at(t, 295.3, 0.5))
        arrow(c, 760, 380, 760 + 380 * k, 380, ACC, 16, k)
        with xf(c, 1300, 380, 0.6 + 0.4 * back_out(k), alpha=k):
            icon_tile(c, 0, 0, 150, "#2ecc71", "bank")
        text(c, "OR SWITCH", 900, 320, 44, ACC, "Black", a=k)


STMT = [("03/02", "Coffee Corner", "-5.40"), ("03/04", "Monthly account fee", "-12.00"),
        ("03/07", "Grocery Mart", "-64.18"), ("03/09", "ATM withdrawal fee", "-3.00"),
        ("03/12", "Salary", "2,450.00"), ("03/15", "Streaming plus", "-12.99")]


def s_statements(c, t):
    studio(c, t)
    cam(c, push(t, 296.3, 301.3, 1.0, 1.06), 960, 540, t, drift=0.4)
    for i in range(3):
        k, a = pin(t, 296.68 + i * 0.22, 0.45)
        if a <= 0:
            continue
        rot = (-8, -2, 5)[i]
        x = 820 + i * 140
        mark = {}
        if i == 2:
            mark = {1: (ease_out(at(t, 298.34, 0.5)), "#ffe14d"), 3: (ease_out(at(t, 298.6, 0.5)), "#ffe14d")}
        with xf(c, x, 540 + i * 10, k * 0.92, alpha=a):
            photo_statement(c, 0, 0, 1.0, STMT, rot=rot, title=("JANUARY", "FEBRUARY", "MARCH")[i], mark=mark)
    tagpop(c, t, 296.96, 300, 160, "LAST 3 STATEMENTS", "#0b1018", "#ffffff", 40)
    k = ease_out(at(t, 299.52, 0.5))
    if k:
        with xf(c, 960, 960, 0.85 + 0.15 * back_out(k), alpha=k):
            rrect(c, -380, -64, 760, 128, 30, GRN)
            text(c, "THE EASIEST MONEY TO SAVE", 0, 18, 46, "#0b1018", "Black")


# ================================================================ 11. STREAMING
def s_two_left(c, t):
    cam(c, push(t, 301.3, 303.5, 1.0, 1.15), 1100, 620, t, drift=0.5)
    list_board(c, t, 299.0, chain=301.8)
    for i in range(10):
        col, row = i // 6, i % 6
        x, y = 330 + col * 680, 210 + row * 130
        check_mark(c, x + 540, y, 50, GRN, 1, 1.0)
    tagpop(c, t, 302.36, 1300, 990, "CONNECTED", ACC, "#0b1018", 40)


SERVICES = [("#e50914", "play", "STREAMFLIX"), ("#1db954", "music", "TUNEBOX"), ("#7d5cc8", "tv", "PRIMEVIEW"),
            ("#00a8e1", "star", "CINEMAX+"), ("#ff9900", "game", "PLAYZONE")]


def tv_screen(t, n=1, lit=None, cancel=None):
    def scr(c, w, h, tt):
        fill_shader(c, skia.Rect(0, 0, w, h), linear(0, 0, 0, h, ["#0d1324", "#05070b"]))
        for i in range(n):
            col, g, nm = SERVICES[i]
            x = 110 + (i % 4) * 225
            y = 160 + (i // 4) * 200
            k = clamp(at(t, 0, 1)) if False else 1.0
            dim = 1.0 if (lit is None or i in lit) else 0.25
            with xf(c, x, y, alpha=dim):
                icon_tile(c, 0, 0, 150, col, g)
                text(c, nm, 0, 115, 24, "#ffffff", "Bold")
            if cancel and i in cancel:
                cross_mark(c, x, y, 120, RED, 0.9)
    return scr


def s_more_services(c, t):
    dark_studio(c, t, "#151c2c")
    cam(c, push(t, 306.3, 312.4, 1.0, 1.05), 960, 520, t, drift=0.4)
    n = 1 if t < 308.6 else min(4, 1 + int((t - 308.6) / 0.35) + 1)
    photo_tv(c, 960, 470, 1.15, screen=tv_screen(t, n), t=t)
    tagpop(c, t, 307.54, 960, 100, "STARTED AS A WAY TO SAVE", GRN, "#0b1018", 44, end=308.4)
    tagpop(c, t, 308.6, 960, 100, "THEN CAME MORE SERVICES", "#ffffff", "#0b1018", 44)
    tagpop(c, t, 310.18, 520, 960, "EXCLUSIVE SHOWS", "#7d5cc8", "#ffffff", 40)
    tagpop(c, t, 311.16, 1400, 960, "RISING PRICES ↑", RED, "#ffffff", 40)


def s_stream_cost(c, t):
    dark_studio(c, t, "#151c2c")
    cam(c, push(t, 312.3, 318.1, 1.0, 1.04), 960, 540, t, drift=0.4)
    lit = None if t < 315.9 else {0, 2}
    photo_tv(c, 620, 420, 0.75, screen=tv_screen(t, 4, lit=lit), t=t)
    k = ease_out(at(t, 312.54, 0.4))
    if k:
        text(c, "4 × $12 / MONTH", 1440, 330, 60, "#ffffff", "Black", a=k)
    if t > 314.38:
        v = counter(t, 314.38, 1.0, 0, 576)
        big_number(c, 1440, 520, "≈" + money(v), 150, ACC, sub="A YEAR")
    tagpop(c, t, 316.62, 620, 900, "ACTIVELY WATCHED: 1 OR 2", RED, "#ffffff", 42)


def s_rotate(c, t):
    dark_studio(c, t, "#151c2c")
    cam(c, push(t, 318.1, 325.2, 1.0, 1.04), 960, 540, t, drift=0.4)
    tagpop(c, t, 318.26, 960, 140, "TRY ROTATING", ACC, "#0b1018", 52)
    steps = [("SUBSCRIBE", 318.96, GRN), ("WATCH", 320.14, CYN), ("CANCEL", 320.98, RED), ("NEXT", 321.74, ACC)]
    cx, cy, R = 960, 560, 270
    for i, (s, st, col) in enumerate(steps):
        ang = -math.pi / 2 + i * math.pi / 2
        x, y = cx + math.cos(ang) * R * 1.35, cy + math.sin(ang) * R
        k, a = pin(t, st, 0.4)
        if a:
            tag(c, x, y, s, col, 44, a=a, sc=k)
    k = ease_out(at(t, 318.96, 0.6))
    if k:
        rot = (t - 318.96) * 40
        with xf(c, cx, cy, rot=rot, alpha=k):
            for j in range(4):
                with xf(c, 0, 0, rot=j * 90):
                    pp = skia.Path()
                    pp.addArc(skia.Rect(-150, -150, 150, 150), 10, 60)
                    c.drawPath(pp, P("#ffffff", 10, 0.5))
        active = 0 if t < 321.74 else 1
        col, g, nm = SERVICES[active]
        icon_tile(c, cx, cy, 170, col, g, a=k)
    if t > 322.74:
        tagpop(c, t, 322.74, 960, 960, "SHOWS DON'T DISAPPEAR. THEY WAIT.", "#ffffff", "#0b1018", 42)


# ================================================================ 12. FORGOTTEN SUBSCRIPTIONS
def s_promise(c, t):
    cam(c, push(t, 325.2, 328.1, 1.0, 1.3), lerp(960, 1180, smooth((t - 325.4) / 1.5)),
        lerp(540, 690, smooth((t - 325.4) / 1.5)), t, drift=0.5)
    list_board(c, t, 323.0, unlock12=326.6, highlight12=325.6)
    for i in range(11):
        col, row = i // 6, i % 6
        x, y = 330 + col * 680, 210 + row * 130
        check_mark(c, x + 540, y, 50, GRN, 1, 1.0)


def _prop_subs(c, t):
    icons = ["#e50914", "#1db954", "#7d5cc8", "#00a8e1", "#ff9900", "#e74c3c", "#3498db", "#f1c40f",
             "#9b59b6", "#1abc9c", "#e67e22", "#34495e", "#ff7aa8", "#16a085", "#c0392b", "#2ecc71"]
    photo_phone(c, 0, 0, 1.05, rot=6, screen=lambda c, w, h, tt: app_screen_home(c, w, h, tt, icons), t=t)


def s_how_many(c, t):
    cam(c, push(t, 331.0, 334.4, 1.0, 1.08), 960, 560, t)
    bg(c, "home", 8, dim=0.2)
    figure(c, 960, FY(1.1, 860), "sam", "think", "worried", t, s=1.1, look=(0.3, -0.8))
    glyphs = [("#e50914", "play"), ("#1db954", "music"), ("#3498db", "cloud"), ("#e67e22", "box"),
              ("#7d5cc8", "news"), ("#ff9900", "game"), ("#2ecc71", "fit"), ("#c0392b", "star")]
    for i, (col, g) in enumerate(glyphs):
        ang = i / len(glyphs) * math.tau + t * 0.35
        k = ease_out(at(t, 332.2 + i * 0.12, 0.4))
        if k:
            icon_tile(c, 960 + math.cos(ang) * 560, 500 + math.sin(ang) * 230, 100, col, g, a=k)
    k = ease_out(at(t, 332.32, 0.4))
    if k:
        text(c, "HOW MANY?", 960, 140, 80, ACC, "Black", a=k, shadow=True)


def s_kinds(c, t):
    dark_studio(c, t, "#1b2740")
    cam(c, push(t, 334.4, 338.7, 1.0, 1.04), 960, 540, t, drift=0.4)
    kinds = [("APPS", "#3498db", "phone", 334.42), ("BOXES", "#e67e22", "box", 334.92),
             ("STORAGE", "#16a085", "cloud", 335.44), ("TRIAL PLANS", "#7d5cc8", "star", 336.18)]
    for i, (nm, col, g, st) in enumerate(kinds):
        k, a = pin(t, st, 0.4)
        if a <= 0:
            continue
        x = 330 + i * 420
        with xf(c, x, 470, k, alpha=a):
            icon_tile(c, 0, 0, 200, col, g)
            text(c, nm, 0, 170, 42, "#ffffff", "Black")
    if t > 336.6:
        flip = ease_out(at(t, 337.42, 0.5))
        x = 330 + 3 * 420
        with xf(c, x, 820):
            if flip < 1:
                with xf(c, 0, 0, sy=1 - flip, sx=1):
                    tag(c, 0, 0, "FREE TRIAL", GRN, 36)
            else:
                tag(c, 0, 0, "$9.99 / MONTH", RED, 36, fg="#ffffff")
        tagpop(c, t, 337.12, 960, 160, "QUIETLY TURNED INTO PAID", RED, "#ffffff", 44)


def s_underestimate(c, t):
    info_board(c, t)
    cam(c, push(t, 338.7, 343.5, 1.0, 1.04), 960, 540, t, drift=0.4)
    tagpop(c, t, 338.74, 960, 160, "SURVEYS OFTEN FIND", "#ffffff", "#0b1018", 40)
    k1 = ease_out(at(t, 339.76, 0.6))
    k2 = ease_out(at(t, 340.72, 0.7))
    bar(c, 720, 880, 280, 260 * k1, "#5f7aa5", 1.0, "WHAT PEOPLE GUESS")
    bar(c, 1200, 880, 280, 520 * k2, RED, 1.0, "WHAT THEY PAY")
    if k1 > 0.5:
        text(c, "?", 720, 880 - 260 * k1 - 30, 70, "#ffffff", "Black")
    k3 = ease_out(at(t, 342.02, 0.5))
    if k3:
        with xf(c, 1200, 880 - 520 * k2 + 120, alpha=k3):
            rrect(c, -130, -40, 260, 80, 16, "#000000", 0.35)
            text(c, "FORGOTTEN", 0, 14, 34, "#ffffff", "Black")


def s_easy_hard(c, t):
    studio(c, t, key="#e4e8ee", rim="#a1aab5")
    cam(c, push(t, 343.5, 349.1, 1.0, 1.04), 960, 540, t, drift=0.4)
    tagpop(c, t, 343.9, 960, 140, "NO ACCIDENT", RED, "#ffffff", 48)
    k, a = pin(t, 345.24, 0.4)
    if a:
        with xf(c, 520, 520, k, alpha=a):
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-250, -80, 270, 110), 60, 60),
                        blur_paint("#000000", 18, 0.35))
            rrect(c, -260, -90, 520, 180, 60, GRN)
            text(c, "SIGN UP", 0, 28, 80, "#ffffff", "Black")
        tagpop(c, t, 345.7, 520, 720, "ONE TAP", GRN, "#0b1018", 40)
    k2 = ease_out(at(t, 346.18, 0.6))
    if k2:
        with xf(c, 1360, 520, alpha=k2):
            rr = random.Random(5)
            pth = skia.Path()
            pth.moveTo(-300, -260)
            x, y = -300, -260
            for i in range(14):
                if i % 2 == 0:
                    x = -x * 0.85
                else:
                    y += 40
                pth.lineTo(x, y)
            c.drawPath(pth, P("#5f6b7a", 14, 0.8))
            rrect(c, -160, 220, 320, 70, 14, "#ffffff")
            text(c, "cancel", 0, 268, 30, "#9aa3b3", "SemiBold")
        tagpop(c, t, 346.64, 1360, 800, "TO CANCEL: A MAZE", RED, "#ffffff", 40)
    k3 = ease_out(at(t, 347.24, 0.4))
    if k3:
        tagpop(c, t, 347.24, 960, 960, "THEY COUNT ON YOU NEVER LOOKING", "#0b1018", "#ffffff", 40)


SUBS = [("01/03", "Music Plus", "-10.99"), ("01/05", "Cloud Storage 200GB", "-2.99"),
        ("01/09", "Meal Box Weekly", "-59.99"), ("01/12", "Grocery Mart", "-48.20"),
        ("01/14", "Photo Editor Pro", "-7.99"), ("01/18", "Streamflix", "-15.49"),
        ("01/22", "Fitness App", "-12.99")]


def s_mark(c, t):
    studio(c, t)
    cam(c, push(t, 349.1, 353.6, 1.0, 1.06), 960, 540, t, drift=0.4)
    for i in range(3):
        k, a = pin(t, 350.8 + i * 0.2, 0.4)
        if a <= 0:
            continue
        x = 1500 + i * 0
        with xf(c, 1620, 300 + i * 120, k * 0.8, alpha=a):
            rrect(c, -150, -45, 300, 90, 18, ("#2c4a86", "#2c4a86", "#d64933")[i])
            text(c, ("MONTH 1", "MONTH 2", "MONTH 3")[i], 0, 14, 36, "#ffffff", "Black")
    mark = {}
    for j, row in enumerate((0, 1, 2, 4, 5, 6)):
        mark[row] = (ease_out(at(t, 351.82 + j * 0.18, 0.35)), "#ffe14d")
    k, a = pin(t, 349.9, 0.45)
    with xf(c, 760, 560, k, alpha=a):
        photo_statement(c, 0, 0, 1.15, SUBS, rot=-2, title="YOUR STATEMENT", mark=mark)
    tagpop(c, t, 352.36, 1560, 760, "MARK EVERY", ACC, "#0b1018", 36)
    tagpop(c, t, 352.5, 1560, 840, "REPEATING CHARGE", ACC, "#0b1018", 36)


def s_three_q(c, t):
    info_board(c, t)
    cam(c, push(t, 353.6, 361.4, 1.0, 1.04), 960, 540, t, drift=0.4)
    qs = [("DID I USE THIS LAST MONTH?", 355.66), ("WOULD I BUY IT AGAIN TODAY?", 357.26),
          ("COULD I LIVE WITHOUT IT?", 358.66)]
    tagpop(c, t, 354.44, 960, 150, "ASK 3 QUESTIONS", ACC, "#0b1018", 48)
    cancel = ease_out(at(t, 360.7, 0.4))
    for i, (q, st) in enumerate(qs):
        dx, k = slide(t, st, 0.5, 120)
        if k <= 0:
            continue
        with xf(c, 960 + dx, 330 + i * 170, alpha=k * (1 - 0.6 * cancel)):
            rrect(c, -620, -66, 1240, 132, 26, "#16233a")
            rrect(c, -620, -66, 1240, 132, 26, "#2b3d5c", stroke=3)
            text(c, f"{i + 1}", -560, 22, 60, ACC, "Black")
            text(c, q, -500, 20, 52, "#ffffff", "Black", align="left")
    if t > 359.76:
        tagpop(c, t, 359.9, 640, 870, "ANY ANSWER IS NO?", "#ffffff", "#0b1018", 44)
        stamp(c, 1360, 870, 1.0, "CANCEL IT", RED, at(t, 360.7, 0.35))


def s_invest(c, t):
    info_board(c, t)
    cam(c, push(t, 361.4, 369.8, 1.0, 1.05), 960, 540, t, drift=0.4)
    x0, y0, x1, y1 = 300, 300, 1640, 880
    chart_frame(c, x0, y0, x1, y1)
    big_number(c, 520, 200, "$100 / MONTH", 70, "#ffffff", a=clamp(at(t, 361.58, 0.4)))
    for yr in (0, 5, 10, 15, 20):
        text(c, f"{yr} YRS", lerp(x0, x1, yr / 20), y1 + 50, 28, "#8796ad", "Bold",
             a=clamp(at(t, 362.52, 0.4)))
    pts = []
    for i in range(21):
        months = i * 12
        r = 0.07 / 12
        fv = 100 * ((1 + r) ** months - 1) / r if months else 0
        pts.append((lerp(x0, x1, i / 20), lerp(y1, y0, fv / 55000)))
    contrib = [(lerp(x0, x1, i / 20), lerp(y1, y0, 1200 * i / 55000)) for i in range(21)]
    prog = ease_out(at(t, 362.52, 2.6))
    plot_line(c, contrib, prog, "#5f7aa5", 6, dot=False)
    end = plot_line(c, pts, prog, GRN, 12)
    if t > 365.4:
        v = counter(t, 365.36, 1.0, 0, 50000)
        big_number(c, 1300, 240, "≈" + money(v), 110, GRN)
    k = ease_out(at(t, 363.1, 0.5))
    if k:
        text(c, "YOU PUT IN $24,000", 1640, contrib[-1][1] - 20, 30, "#9fb0c8", "Black", align="right", a=k)
    tagpop(c, t, 367.02, 1300, 380, "NOT GUARANTEED", "#ffffff", "#0b1018", 34)
    k2 = ease_out(at(t, 368.6, 0.4))
    if k2:
        text(c, "THAT'S HOW TIME WORKS", 960, 1010, 40, ACC, "Black", a=k2)


# ================================================================ WRAP-UP
ALL12 = [("#ff5a3c", "bag"), ("#c4161c", "car"), ("#7d5cc8", "fit"), ("#2c8fd6", "shield"), ("#d64933", "shirt"),
         ("#34495e", "phone"), ("#e67e22", "pill"), ("#8b5a2b", "cup"), ("#9b59b6", "split"), ("#2c4a86", "bank"),
         ("#e50914", "tv"), ("#16a085", "cloud")]


def s_share(c, t):
    info_board(c, t)
    cam(c, push(t, 369.8, 378.2, 1.0, 1.04), 960, 540, t, drift=0.4)
    dim = ease_out(at(t, 376.9, 0.8))
    for i, (col, g) in enumerate(ALL12):
        k, a = pin(t, 369.9 + i * 0.07, 0.35)
        if a:
            x = 330 + (i % 6) * 252
            y = 290 + (i // 6) * 200
            icon_tile(c, x, y, 140, mixhex(col, "#2b3d5c", dim * 0.8), g, a=a, s=k)
    words = [("CONVENIENCE", 371.88), ("COMFORT", 372.48), ("STATUS", 372.92), ("FOMO", 373.44)]
    for i, (w, st) in enumerate(words):
        k, a = pin(t, st, 0.4)
        if a:
            tag(c, 330 + i * 420, 760, w, ACC, 44, a=a, sc=k)
    k = ease_out(at(t, 374.84, 0.4))
    if k:
        text(c, "SPENDING FEELS NORMAL… EVEN SMART", 960, 900, 46, "#ffffff", "Black", a=k * (1 - dim))
    if dim:
        tagpop(c, t, 377.0, 960, 900, "…UNTIL YOU DO THE MATH", RED, "#ffffff", 50)


def s_joy(c, t):
    cam(c, push(t, 378.2, 382.9, 1.0, 1.08), 960, 560, t)
    bg(c, "cafe", 7)
    rrect(c, 640, 650, 640, 26, 10, "#6b4a33")
    c.drawRect(skia.Rect(940, 676, 980, 860), P("#4a3324"))
    figure(c, 760, 690, "sam", "sit", "happy", t, s=0.95)
    photo_cup(c, 1080, 650, 0.32, t, label="")
    tagpop(c, t, 378.56, 960, 160, "YOU DON'T NEED TO CUT THEM ALL", "#ffffff", "#0b1018", 44)
    k, a = pin(t, 380.86, 0.5)
    if a:
        with xf(c, 1450, 430, k, alpha=a):
            hp = skia.Path()
            hp.moveTo(0, 60)
            hp.cubicTo(-140, -30, -70, -140, 0, -70)
            hp.cubicTo(70, -140, 140, -30, 0, 60)
            c.drawPath(hp, P("#ff5c7a"))
            text(c, "JOY", 0, -10, 40, "#ffffff", "Black")
    tagpop(c, t, 381.68, 1450, 620, "A GOOD REASON TO SPEND", GRN, "#0b1018", 38)


def s_choice(c, t):
    dark_studio(c, t, "#1b2740")
    cam(c, push(t, 382.9, 387.5, 1.0, 1.04), 960, 540, t, drift=0.4)
    tagpop(c, t, 383.06, 960, 140, "THE GOAL IS SIMPLE", ACC, "#0b1018", 46)
    k, a = pin(t, 385.14, 0.45)
    if a:
        with xf(c, 560, 560, k, alpha=a):
            rrect(c, -330, -250, 660, 500, 40, "#16233a")
            rrect(c, -330, -250, 660, 500, 40, GRN, stroke=6)
            check_mark(c, 0, -40, 220, GRN, 1, at(t, 385.3, 0.5))
            text(c, "A CHOICE YOU MADE", 0, 190, 46, "#ffffff", "Black")
    k2, a2 = pin(t, 386.36, 0.45)
    if a2:
        with xf(c, 1360, 560, k2, alpha=a2):
            rrect(c, -330, -250, 660, 500, 40, "#16233a")
            rrect(c, -330, -250, 660, 500, 40, RED, stroke=6)
            with xf(c, 0, -40, rot=(t - 386.36) * 120):
                pp = skia.Path()
                pp.addArc(skia.Rect(-100, -100, 100, 100), 20, 290)
                c.drawPath(pp, P(RED, 22))
                c.drawPath(poly([(96, -20), (130, 50), (60, 40)]), P(RED))
            text(c, "NOT A HABIT", 0, 170, 46, "#ffffff", "Black")
            text(c, "THAT MADE YOU", 0, 220, 36, "#c9d3e3", "Black")


def eye(c, x, y, s, t, open_=1.0):
    with xf(c, x, y, s):
        h = 160 * open_
        p = skia.Path()
        p.moveTo(-300, 0)
        p.quadTo(0, -h * 1.6, 300, 0)
        p.quadTo(0, h * 1.6, -300, 0)
        c.drawPath(p, P("#f2ead6"))
        c.save()
        c.clipPath(p, skia.ClipOp.kIntersect, True)
        c.drawCircle(20 * math.sin(t), 0, 120, P("#2c8fd6"))
        c.drawCircle(20 * math.sin(t), 0, 60, P("#0a0a10"))
        c.drawCircle(20 * math.sin(t) + 30, -36, 22, P("#ffffff"))
        c.restore()
        c.drawPath(p, P("#0a0a10", 12))


def s_noticing(c, t):
    dark_studio(c, t, "#1b2740")
    cam(c, push(t, 387.5, 395.8, 1.0, 1.08), 960, 540, t, drift=0.4)
    if t < 392.9:
        k = ease_out(at(t, 387.6, 0.5))
        text(c, "IN 2027", 960, 200, 70, ACC, "Black", a=k)
        for i, (w, st) in enumerate((("EARNING MORE", 390.04), ("SPENDING LESS", 390.92))):
            kk, a = pin(t, st, 0.35)
            if a:
                x = 560 + i * 800
                with xf(c, x, 360, kk, alpha=a * (1 - 0.6 * clamp(at(t, 391.84, 0.4)))):
                    rrect(c, -280, -60, 560, 120, 24, "#16233a")
                    text(c, w, 0, 20, 50, "#9fb0c8", "Black")
                if t > 391.4:
                    line(c, x - 260, 360, x - 260 + 520 * ease_out(at(t, 391.4, 0.3)), 360, RED, 10)
        ko = ease_out(at(t, 392.06, 0.6))
        if ko:
            eye(c, 960, 680, 0.9, t, open_=ko)
            text(c, "NOTICING", 960, 950, 90, "#ffffff", "Black", a=ko, shadow=True)
    else:
        eye(c, 960, 380, 0.55, t)
        k = ease_out(at(t, 393.1, 0.5))
        text(c, "ONE QUESTION, EVERY TIME", 960, 620, 48, "#c9d3e3", "Black", a=k)
        k2, a2 = pin(t, 394.84, 0.5)
        if a2:
            with xf(c, 960, 790, k2, alpha=a2):
                text(c, "IS THIS STILL WORTH IT?", 0, 30, 110, ACC, "Black", shadow=True)


def s_disclaimer(c, t):
    dark_studio(c, t, "#141b2a")
    k = ease_out(at(t, 395.9, 0.6))
    with xf(c, 960, 540, alpha=k):
        rrect(c, -620, -150, 1240, 300, 30, "#0f1624")
        rrect(c, -620, -150, 1240, 300, 30, "#2b3d5c", stroke=3)
        icon_tile(c, -500, 0, 120, "#2c8fd6", "news")
        text(c, "For education and general information.", -400, -18, 44, "#ffffff", "Bold", align="left")
        text(c, "Not personal financial advice.", -400, 52, 44, ACC, "Black", align="left")


def s_pick_one(c, t):
    info_board(c, t)
    cam(c, push(t, 402.0, 405.5, 1.0, 1.05), 960, 540, t, drift=0.4)
    pick = 7
    chosen = ease_out(at(t, 403.44, 0.5))
    for i, (col, g) in enumerate(ALL12):
        x = 330 + (i % 6) * 252
        y = 360 + (i // 6) * 220
        if i == pick:
            s = 1 + 0.25 * chosen
            icon_tile(c, x, y - 30 * chosen, 140, col, g, s=s)
            if chosen > 0:
                rrect(c, x - 100, y - 30 * chosen - 100, 200, 200, 40, ACC, stroke=8 * chosen)
        else:
            icon_tile(c, x, y, 140, mixhex(col, "#2b3d5c", chosen * 0.8), g, a=1 - 0.4 * chosen)
    tagpop(c, t, 402.06, 960, 150, "PICK ONE THING", ACC, "#0b1018", 50)
    tagpop(c, t, 404.08, 960, 900, "THIS WEEK. JUST ONE.", "#ffffff", "#0b1018", 48)


def s_next(c, t):
    dark_studio(c, t, "#1d2a44")
    cam(c, push(t, 405.5, 415.0, 1.0, 1.06), 960, 540, t, drift=0.4)
    k = ease_out(at(t, 407.4, 0.6))
    tagpop(c, t, 407.4, 960, 150, "WATCH NEXT", ACC, "#0b1018", 52)
    with xf(c, 960, 560, 0.85 + 0.15 * k, alpha=k):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-520 + 14, -292 + 24, 520 + 14, 292 + 24), 30, 30),
                    blur_paint("#000000", 24, 0.5))
        r = skia.RRect.MakeRectXY(skia.Rect(-520, -292, 520, 292), 28, 28)
        c.save()
        c.clipRRect(r, skia.ClipOp.kIntersect, True)
        c.translate(-520, -292)
        c.scale(1040 / W, 584 / H)
        bg(c, "home", 10, dim=0.4)
        figure(c, 700, FY(1.3, 900), "sam", "headhold", "worried", t, s=1.3)
        text(c, "THE ONE", 1420, 380, 120, "#ffffff", "Black", shadow=True)
        text(c, "TRAP", 1420, 510, 150, ACC, "Black", shadow=True)
        c.restore()
        c.drawRRect(r, P("#ffffff", 4, 0.3))
        c.drawCircle(0, 200, 56, P("#000000", a=0.55))
        c.drawPath(poly([(-17, 172), (32, 200), (-17, 228)]), P("#ffffff"))
    k2 = ease_out(at(t, 411.94, 0.5))
    if k2:
        with xf(c, 960, 960, alpha=k2):
            icon_tile(c, -420, 0, 90, "#5f7aa5", "bag")
            cross_mark(c, -420, 0, 90, RED)
            text(c, "NOTHING TO DO WITH SHOPPING", 40, 16, 44, "#ffffff", "Black")


SCENES_B = [
    (163.1, 166.0, s_holding),
    (166.0, 168.28, card_scene(6, ["UPGRADING YOUR", "PHONE EVERY YEAR"], None, _prop_phone)),
    (168.28, 175.3, s_leaps),
    (175.3, 182.46, s_tradein),
    (182.46, 189.7, s_honest),
    (189.7, 193.48, s_kitchen),
    (193.48, 196.4, card_scene(7, ["NAME BRANDS FOR", "EVERYDAY BASICS"], "Paying extra for a name", _prop_brands)),
    (196.4, 203.12, s_aisle),
    (203.12, 208.18, s_pills),
    (208.18, 214.0, s_cheaper),
    (214.0, 216.08, s_ads),
    (216.08, 221.98, s_try5),
    (221.98, 225.58, card_scene(8, ["THE DAILY", "COFFEE SHOP DRINK"], "Let's be fair", _prop_coffee)),
    (225.58, 230.0, s_cafe),
    (230.0, 236.8, s_coffee_year),
    (236.8, 240.74, s_twice),
    (240.74, 248.2, s_leak),
    (248.2, 250.48, card_scene(9, ["BUY NOW,", "PAY LATER"], None, _prop_bnpl)),
    (250.48, 253.76, s_split),
    (253.76, 259.48, s_brain),
    (259.48, 262.98, s_missed),
    (262.98, 267.5, s_paycheck),
    (267.5, 277.14, s_rule),
    (277.14, 279.78, s_bleed),
    (279.78, 281.3, card_scene(10, ["BANK", "FEES"], "Small, quiet, and everywhere", _prop_bank)),
    (281.3, 292.1, s_fees),
    (292.1, 296.26, s_switch),
    (296.26, 301.3, s_statements),
    (301.3, 303.48, s_two_left),
    (303.48, 306.32, card_scene(11, ["STACKING", "STREAMING SERVICES"], None,
                                lambda c, t: photo_tv(c, 0, 0, 0.55, screen=tv_screen(t, 4), t=t))),
    (306.32, 312.26, s_more_services),
    (312.26, 318.06, s_stream_cost),
    (318.06, 325.16, s_rotate),
    (325.16, 328.14, s_promise),
    (328.14, 330.98, card_scene(12, ["SUBSCRIPTIONS", "YOU FORGOT YOU HAD"], "The one almost nobody checks",
                                _prop_subs)),
    (330.98, 334.38, s_how_many),
    (334.38, 338.7, s_kinds),
    (338.7, 343.54, s_underestimate),
    (343.54, 349.1, s_easy_hard),
    (349.1, 353.56, s_mark),
    (353.56, 361.44, s_three_q),
    (361.44, 369.84, s_invest),
    (369.84, 378.2, s_share),
    (378.2, 382.92, s_joy),
    (382.92, 387.5, s_choice),
    (387.5, 395.78, s_noticing),
    (395.78, 402.0, s_disclaimer),
    (402.0, 405.5, s_pick_one),
    (405.5, 999.0, s_next),
]
