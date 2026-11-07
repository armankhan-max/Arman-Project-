"""Timeline part A: hook, intro and items 1-5. Times are absolute seconds in the voiceover."""
import math
import random

import skia

from pgfx import *  # noqa: F401,F403

FLOOR = 800


def FY(s=1.0, floor=FLOOR):
    """Hip height so that a figure of scale s stands on `floor`."""
    return floor - 170 * s


# ---------------------------------------------------------------- camera
def cam(c, zoom=1.0, cx=W / 2, cy=H / 2, t=0.0, shake=0.0, drift=1.0):
    dx = drift * (5 * math.sin(t * 0.37) + 3 * math.sin(t * 0.91)) + shake * (math.sin(t * 53) * 8)
    dy = drift * (4 * math.sin(t * 0.29 + 1) + 2 * math.sin(t * 1.13)) + shake * (math.cos(t * 47) * 8)
    c.translate(W / 2 + dx, H / 2 + dy)
    c.scale(zoom, zoom)
    c.translate(-cx, -cy)


def push(t, a, b, z0, z1):
    return lerp(z0, z1, smooth((t - a) / max(0.01, b - a)))


def pin(t, start, dur=0.45):
    """(scale, alpha) for a pop-in."""
    return back_out(at(t, start, dur)), clamp(at(t, start, dur * 0.6))


def slide(t, start, dur=0.5, dist=80):
    k = ease_out(at(t, start, dur))
    return (1 - k) * dist, k


def counter(t, start, dur, a, b):
    return lerp(a, b, ease_out(at(t, start, dur)))


def tagpop(c, t, start, x, y, s, color=ACC, fg="#0b1018", size=40, end=None):
    k, a = pin(t, start, 0.4)
    if end is not None:
        a *= clamp((end - t) / 0.25)
    if a > 0:
        tag(c, x, y, s, color, size, a=a, sc=k, fg=fg)


def calendar(c, x, y, w, h, t, title="THIS MONTH", marks=(), mark_col=GRN, days=30, cols=7, mark_kind="check",
             start_day=0):
    """Paper wall-calendar. marks = [(day_index, start_time)]."""
    with xf(c, x, y):
        c.drawRect(skia.Rect(-w / 2 + 14, -h / 2 + 22, w / 2 + 14, h / 2 + 22), blur_paint("#000000", 18, 0.4))
        c.drawRect(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), P("#fbfaf6"))
        c.drawRect(skia.Rect(-w / 2, -h / 2, w / 2, -h / 2 + 90), P("#d64933"))
        text(c, title, 0, -h / 2 + 60, 40, "#ffffff", "Black")
        rows = math.ceil((days + start_day) / cols)
        cw, ch = w / cols, (h - 110) / rows
        for d in range(days):
            i = d + start_day
            cx = -w / 2 + (i % cols + 0.5) * cw
            cy = -h / 2 + 100 + (i // cols + 0.5) * ch
            text(c, str(d + 1), cx - cw * 0.3, cy - ch * 0.15, 22, "#8a8f98", "SemiBold", align="left")
            c.drawRect(skia.Rect(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2), P("#e2dfd8", 1.5))
        for day, st in marks:
            k = at(t, st, 0.35)
            if k <= 0:
                continue
            i = day + start_day
            cx = -w / 2 + (i % cols + 0.5) * cw
            cy = -h / 2 + 100 + (i // cols + 0.5) * ch
            if mark_kind == "check":
                check_mark(c, cx + 6, cy + 8, min(cw, ch) * 0.6, mark_col, 1, k)
            elif mark_kind == "cross":
                cross_mark(c, cx, cy + 6, min(cw, ch) * 0.5 * back_out(k), mark_col)
            elif mark_kind == "cup":
                with xf(c, cx, cy + 10, s=back_out(k) * min(cw, ch) / 110):
                    icon_tile(c, 0, 0, 80, "#8b5a2b", "cup")


def sandwich(c, x, y, s=1.0):
    with xf(c, x, y, s):
        soft_shadow(c, 0, 10, 420, 40, 0.5, 14)
        for k, (col, dy) in enumerate((("#e6c58c", 0), ("#4caf50", -40), ("#e8564a", -55), ("#f6d365", -70),
                                       ("#e6c58c", -90))):
            if k in (0, 4):
                p = poly([(-200, dy), (200, dy), (170, dy - 60), (-170, dy - 60)])
                c.drawPath(p, skia.Paint(AntiAlias=True, Shader=linear(0, dy - 60, 0, dy,
                           ["#f3dcae", "#c99a55"])))
                c.drawPath(p, P("#a87436", 6))
            else:
                c.drawPath(poly([(-205, dy), (205, dy), (195, dy - 18), (-195, dy - 18)]), P(col))
        spec(c, -50, -135, 200, 14, 0.3)


# ================================================================ HOOK
def s_hook(c, t):
    cam(c, push(t, 0, 5.7, 1.0, 1.12), 960, 560, t)
    bg(c, "home", 7)
    x, y = 960, FY(1.25, 860)
    figure(c, x, y, "sam", "tap", "neutral" if t < 3.6 else "worried", t, look=(0.3, 0.6), s=1.25,
           hold=lambda c, hx, hy: photo_phone(c, hx + 6, hy - 30, 0.17, rot=-8, shadow=False,
                                              screen=app_screen_home))
    # money quietly leaving the pocket
    for i in range(14):
        st = 2.5 + i * 0.22
        ph = (t - st) / 1.6
        if 0 < ph < 1:
            cx = x + 40 + 30 * math.sin(i * 1.7) + ph * (90 + i * 6)
            cy = y - 10 + ph * ph * 220
            photo_coin(c, cx, cy, 20, "#d4a838" if i % 3 else "#c9c9cf", a=1 - ph * 0.7)
    k = ease_out(at(t, 3.7, 0.5))
    if k:
        label(c, 960, 210, "STOPPED BEING WORTH IT", 46, ACC, a=k, sc=0.9 + 0.1 * k)


def s_not_lux(c, t):
    studio(c, t)
    cam(c, push(t, 5.6, 9.9, 1.0, 1.04), 960, 540, t, drift=0.5)
    # luxuries (crossed) then everyday things
    lk = 1 - ease_out(at(t, 6.6, 0.4))
    if lk > 0:
        with xf(c, 960, 640, alpha=lk):
            photo_car(c, 0, 0, 0.9, "#c9a227", t)
            if t > 5.8:
                cross_mark(c, 0, -170, 260 * back_out(at(t, 5.8, 0.3)), RED, 0.9)
        tagpop(c, t, 5.7, 960, 200, "NOT LUXURIES", "#0b1018", "#ffffff", 50, end=6.65)
    items = [(lambda c: photo_cup(c, 0, 0, 0.55, t, label="CAFE"), 360),
             (lambda c: photo_phone(c, 0, -170, 0.5, screen=app_screen_home), 700),
             (lambda c: photo_tshirt(c, 0, -150, 0.4, "#3d6ec9"), 1030),
             (lambda c: photo_card(c, 0, -90, 0.45, rot=-8), 1330),
             (lambda c: photo_burger(c, 0, 0, 0.55), 1620)]
    for i, (fn, x) in enumerate(items):
        st = 6.7 + i * 0.15
        k, a = pin(t, st, 0.45)
        if a > 0:
            with xf(c, x, 720, k, alpha=a):
                fn(c)
    tagpop(c, t, 7.24, 960, 200, "EVERYDAY PURCHASES", ACC, size=50)


def list_board(c, t, start, unlock12=None, highlight12=None, chain=None):
    info_board(c, t)
    for i in range(12):
        col, row = i // 6, i % 6
        x = 330 + col * 680
        y = 210 + row * 130
        k, a = pin(t, start + i * 0.05, 0.4)
        if a <= 0:
            continue
        with xf(c, x, y, alpha=a):
            is12 = i == 11
            rrect(c, -20, -50, 600, 100, 18, "#16233a")
            rrect(c, -20, -50, 600, 100, 18, ACC if is12 else "#2b3d5c", stroke=3)
            text(c, f"{i + 1:02d}", 50, 20, 52, ACC if is12 else "#5bd6ff", "Black")
            if is12:
                op = 0.0 if unlock12 is None else ease_out(at(t, unlock12, 0.6))
                if op < 1:
                    with xf(c, 0, 0, alpha=1 - op):
                        icon_tile(c, 330, 0, 70, "#2b3d5c", "lock", s=1 + 0.06 * math.sin(t * 4))
                        text(c, "? ? ?", 470, 18, 44, "#ffffff", "Black", a=0.6)
                if op > 0:
                    with xf(c, 0, 0, alpha=op):
                        text(c, "FORGOTTEN SUBSCRIPTIONS", 120, 14, 30, "#ffffff", "Black", align="left")
                if highlight12 is not None:
                    hk = clamp((t - highlight12) / 0.3)
                    if hk > 0.01:
                        rrect(c, -26, -56, 612, 112, 22, ACC, stroke=6 * hk * (0.7 + 0.3 * math.sin(t * 6)))
            else:
                for k2 in range(3):
                    rrect(c, 120 + k2 * 140, -10, 120, 20, 10, "#2b3d5c")
    if chain is not None:
        k = ease_out(at(t, chain, 0.5))
        if k:
            # items 11 and 12 are linked
            for j in range(3):
                c.drawOval(skia.Rect(1250 - 22, 785 + j * 38 - 30, 1250 + 22, 785 + j * 38 + 8),
                           P(ACC, 8, k))


def s_list(c, t):
    cam(c, push(t, 9.8, 15.4, 1.0, 1.3), lerp(960, 1180, smooth((t - 10.2) / 2)),
        lerp(540, 690, smooth((t - 10.2) / 2)), t, drift=0.6)
    list_board(c, t, 9.88, highlight12=10.2)
    k = ease_out(at(t, 11.66, 0.5))
    if k:
        label(c, 1310, 960, "ALMOST NOBODY CHECKS", 40, "#0b1018", ACC, a=k)


def s_prices(c, t):
    info_board(c, t)
    cam(c, push(t, 15.4, 19.2, 1.0, 1.05), 960, 540, t, drift=0.5)
    x0, y0, x1, y1 = 260, 220, 1660, 880
    chart_frame(c, x0, y0, x1, y1)
    n = 10
    pr = [(lerp(x0, x1, i / n), y1 - 80 - 520 * (1.06 ** (i * 2) - 1) / (1.06 ** (n * 2) - 1)) for i in range(n + 1)]
    wg = [(lerp(x0, x1, i / n), y1 - 80 - 170 * i / n - 10 * math.sin(i)) for i in range(n + 1)]
    end = plot_line(c, pr, ease_out(at(t, 15.42, 1.6)), RED, 12)
    if end and t > 15.9:
        text(c, "PRICES", end[0] - 20, end[1] - 40, 52, RED, "Black", align="right")
    end2 = plot_line(c, wg, ease_out(at(t, 17.12, 1.4)), CYN, 12)
    if end2 and t > 17.6:
        text(c, "WAGES", end2[0] - 20, end2[1] + 80, 52, CYN, "Black", align="right")
    k = ease_out(at(t, 18.2, 0.4))
    if k:
        x = x1 - 40
        arrow(c, x, pr[-1][1] + 30, x, wg[-1][1] - 30, ACC, 8, k)
        arrow(c, x, wg[-1][1] - 30, x, pr[-1][1] + 30, ACC, 8, k)
        text(c, "THE GAP", x - 60, (pr[-1][1] + wg[-1][1]) / 2 + 16, 44, ACC, "Black", align="right", a=k)


def s_question(c, t):
    cam(c, push(t, 19.2, 24.5, 1.05, 1.18), 900, 520, t)
    bg(c, "home", 8, dim=0.15)
    figure(c, 760, FY(), "sam", "think", "neutral" if t < 22.2 else "smile", t, look=(0.6, -0.6))
    k, a = pin(t, 19.2, 0.4)
    swap = ease_out(at(t, 22.24, 0.45))
    if a:
        thought(c, 1240, 330, 780, 230, a=a, s=k, tail=(-1, 1))
        if swap < 1:
            with xf(c, 1240, 330, k, alpha=a * (1 - swap)):
                text(c, "CAN I AFFORD IT?", 0, 22, 64, "#1b1b2f", "Black")
                if t > 20.42:
                    pk = ease_out(at(t, 20.42, 0.4))
                    line(c, -300, 0, -300 + 600 * pk, 0, RED, 12)
        if swap > 0:
            with xf(c, 1240, 330, k * (0.8 + 0.2 * back_out(swap)), alpha=swap):
                text(c, "IS THIS STILL", 0, -14, 60, "#1b1b2f", "Black")
                text(c, "WORTH IT?", 0, 60, 70, "#d4920f", "Black")


def s_title(c, t):
    dark_studio(c, t, "#1d2a44")
    cam(c, push(t, 24.5, 27.1, 1.0, 1.06), 960, 540, t, drift=0.4)
    k, a = pin(t, 24.6, 0.5)
    with xf(c, 960, 420, k, alpha=a):
        text(c, "12", 0, 120, 360, ACC, "Black", shadow=True)
    dy, k2 = slide(t, 25.2, 0.5, 40)
    with xf(c, 960, 690 + dy, alpha=k2):
        text(c, "THINGS THAT FAIL THE TEST", 0, 0, 72, "#ffffff", "Black", shadow=True)
    dy, k3 = slide(t, 26.3, 0.5, 40)
    with xf(c, 960, 800 + dy, alpha=k3):
        tag(c, 0, 0, "IN 2027", RED, 52, fg="#ffffff")


def denim(c):
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, W, H, ["#2c4a78", "#1d3458", "#2a4776"]))
    r = random.Random(1)
    for i in range(0, W + H, 6):
        line(c, i, 0, i - H, H, "#ffffff", 1.5, 0.035)
    for _ in range(900):
        x, y = r.uniform(0, W), r.uniform(0, H)
        line(c, x, y, x + 6, y - 6, "#9fb8dc", 1.5, 0.12)


def s_pocket(c, t):
    cam(c, push(t, 27.1, 30.0, 1.0, 1.08), 960, 540, t, drift=0.4)
    denim(c)
    # pocket
    c.translate(0, 380)
    pocket = poly([(560, 120), (1360, 120), (1320, 900), (960, 1000), (600, 900)])
    rise = ease_out(at(t, 27.6, 1.2))
    photo_phone(c, 990, 520 - 430 * rise, 1.0, rot=-6, screen=app_screen_home, t=t)
    c.drawPath(pocket, P("#2a4876"))
    c.drawPath(pocket, skia.Paint(AntiAlias=True, Shader=linear(0, 120, 0, 1000, [("#000000", 0.25),
                                                                                    ("#000000", 0.0)])))
    c.drawPath(pocket, P("#e0a23c", 4, 0.8))
    p2 = poly([(590, 150), (1330, 150), (1292, 880), (960, 972), (628, 880)])
    for k in range(0, 60, 1):
        pass
    eff = skia.DashPathEffect.Make([18, 12], 0)
    pp = P("#e0a23c", 4, 0.8)
    pp.setPathEffect(eff)
    c.drawPath(p2, pp)
    c.drawRect(skia.Rect(520, 100, 1400, 130), P("#1d3458"))


# ================================================================ 1. FOOD DELIVERY
def card_scene(num, title, sub, prop, tone="#1d2a44"):
    def fn(c, t, _st=[None]):
        dark_studio(c, t, tone, light=(1450, 420))
        st = CARD_START[num]
        cam(c, push(t, st, st + 3.5, 1.0, 1.05), 960, 540, t, drift=0.5)
        k, a = pin(t, st + 0.1, 0.6)
        if a:
            with xf(c, 1580, 560, 0.75 + 0.13 * k, alpha=a):
                prop(c, t)
        number_card(c, t, st, num, title, sub)
    return fn


CARD_START = {1: 30.04, 2: 61.36, 3: 90.10, 4: 116.50, 5: 141.38, 6: 166.04, 7: 193.52, 8: 222.02, 9: 248.26,
              10: 279.82, 11: 303.52, 12: 328.18}


def _prop_delivery(c, t):
    photo_phone(c, 0, 0, 1.15, rot=8 + 2 * math.sin(t), screen=app_screen_delivery, t=t)


def s_receipt(c, t):
    studio(c, t, warm=0.2)
    cam(c, push(t, 33.3, 37.4, 1.0, 1.08), 960, 520, t, drift=0.4)
    photo_burger(c, 420, 760, 0.8)
    rows = [("Food", "$12.00", at(t, 33.4, 0.4), False),
            ("Delivery fee", "$2.99", at(t, 35.12, 0.35), t > 35.12),
            ("Service fee", "$2.01", at(t, 35.96, 0.35), t > 35.96),
            ("Tip", "$3.00", at(t, 36.72, 0.35), t > 36.72)]
    photo_receipt(c, 1250, 500, 1.15, rows, rot=-3)


def s_platform(c, t):
    info_board(c, t)
    cam(c, push(t, 37.4, 42.3, 1.0, 1.05), 960, 540, t, drift=0.5)
    figure(c, 420, FY(1.15, 940), "chef", "present" if t > 38.4 else "stand", "worried" if t > 39.9 else "neutral",
           t, s=1.15)
    # order split donut
    cx, cy, R = 1220, 500, 270
    k = ease_out(at(t, 37.6, 0.6))
    c.drawCircle(cx, cy, R * k, P("#2c4a86"))
    sweep = 360 * lerp(0.0, 0.15, ease_out(at(t, 39.96, 0.5)))
    sweep = 360 * lerp(sweep / 360, 0.30, ease_out(at(t, 40.62, 0.6)))
    if sweep > 0:
        pth = skia.Path()
        pth.moveTo(cx, cy)
        pth.arcTo(skia.Rect(cx - R, cy - R, cx + R, cy + R), -90, sweep, False)
        pth.close()
        c.drawPath(pth, P(RED))
    c.drawCircle(cx, cy, R * 0.55 * k, P("#0d1624"))
    if k:
        text(c, "ONE ORDER", cx, cy + 14, 44, "#ffffff", "Black", a=k)
    if t > 39.96:
        pct = "15%" if t < 40.62 else "15–30%"
        tagpop(c, t, 39.96, cx + 370, cy - 210, pct, RED, "#ffffff", 54)
        tagpop(c, t, 40.3, cx + 370, cy - 110, "TO THE APP", "#ffffff", "#0b1018", 34)
    tagpop(c, t, 38.48, 420, 270, "RESTAURANT", "#e9edf3", "#0b1018", 36)


def menu_card(c, x, y, s, title, price, col, a=1.0, up=0.0):
    with xf(c, x, y, s, alpha=a):
        c.drawRect(skia.Rect(-200, -260, 220, 290), blur_paint("#000000", 20, 0.4))
        c.drawRect(skia.Rect(-210, -270, 210, 270), P("#fbf6ea"))
        c.drawRect(skia.Rect(-210, -270, 210, -170), P(col))
        text(c, title, 0, -205, 36, "#ffffff", "Black")
        photo_burger(c, 0, 40, 0.5)
        text(c, "Classic burger", 0, 130, 32, "#333333", "Bold")
        text(c, price, 0, 220, 72, "#c0392b" if up else "#333333", "Black")
        if up:
            arrow(c, 150, 230, 150, 230 - 110 * up, RED, 12)


def s_menu(c, t):
    studio(c, t)
    cam(c, push(t, 42.3, 44.66, 1.0, 1.05), 960, 540, t, drift=0.4)
    menu_card(c, 620, 560, 1.1, "IN THE RESTAURANT", "$12", "#2c4a86")
    k, a = pin(t, 42.6, 0.45)
    menu_card(c, 1300, 560, 1.1 * k, "ON THE APP", "$14.50" if t > 43.02 else "$12", "#ff5a3c", a,
              up=ease_out(at(t, 43.02, 0.5)))


def s_door_price(c, t):
    studio(c, t, warm=0.15)
    cam(c, push(t, 44.6, 48.6, 1.0, 1.06), 960, 560, t, drift=0.4)
    photo_burger(c, 520, 760, 1.0)
    tagpop(c, t, 45.22, 520, 380, "$12", "#ffffff", "#0b1018", 90)
    tagpop(c, t, 45.6, 520, 470, "IN THE RESTAURANT", "#0b1018", "#ffffff", 30)
    k = ease_out(at(t, 46.3, 0.6))
    if k:
        arrow(c, 820, 560, 820 + 260 * k, 560, ACC, 16, k)
        with xf(c, 1420, 0, alpha=k):
            photo_door(c, 0, 900, 0.95, open_=0.6)
            photo_bag(c, 30, 900, 0.8)
    tagpop(c, t, 46.74, 1420, 380, "$20", RED, "#ffffff", 90)
    tagpop(c, t, 47.6, 1420, 470, "AT YOUR DOOR", "#0b1018", "#ffffff", 30)


def s_year_cost(c, t):
    info_board(c, t)
    cam(c, push(t, 48.6, 52.5, 1.0, 1.04), 960, 540, t, drift=0.4)
    # 52 weeks x 2 orders
    for wk in range(52):
        for j in range(2):
            idx = wk * 2 + j
            st = 48.8 + idx * 0.012
            k = at(t, st, 0.2)
            if k <= 0:
                continue
            x = 576 + (idx % 13) * 64
            y = 300 + (idx // 13) * 46
            icon_tile(c, x, y, 34, "#ff5a3c", "bag", a=k, s=back_out(k))
    text(c, "2 ORDERS × 52 WEEKS", 960, 230, 48, "#c9d3e3", "Black", a=clamp(at(t, 48.8, 0.4)))
    v = counter(t, 49.9, 1.2, 0, 832)
    if t > 49.9:
        big_number(c, 960, 700, f"+{money(v)}", 150, RED, sub="EXTRA PER YEAR")
    k = ease_out(at(t, 51.3, 0.4))
    if k:
        label(c, 960, 960, "TO SKIP A SHORT DRIVE", 40, "#ffffff", a=k)


def s_default(c, t):
    night = 1.0
    cam(c, push(t, 52.5, 59.5, 1.0, 1.1), 960, 560, t)
    bg(c, "home", 8, dim=0.25)
    # sam on the couch (tired) - couch seat ~ y 680
    figure(c, 760, 690, "sam", "slump", "bored", t, s=0.95, look=(0.2, 0.5),
           hold=lambda c, hx, hy: photo_phone(c, hx, hy - 20, 0.16, rot=-20, shadow=False,
                                              screen=app_screen_delivery))
    tagpop(c, t, 53.52, 760, 300, "TIRED DAYS", "#9aa3b3", "#0b1018", 38, end=54.1)
    # stacking bags = it became the default
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    for i, d in enumerate(days):
        st = 54.2 + i * 0.28
        k, a = pin(t, st, 0.35)
        if a <= 0:
            continue
        x = 1180 + (i % 4) * 170
        y = 640 + (i // 4) * 290
        with xf(c, x, y, 0.42 * k, alpha=a):
            photo_bag(c, 0, 0, 1.0)
        text(c, d, x, y + 50, 30, "#c9d3e3", "Black", a=a)
    k = ease_out(at(t, 56.96, 0.5))
    if k:
        label(c, 1430, 200, "THE DEFAULT", 52, RED, a=k, sc=0.9 + 0.1 * k)
    k = ease_out(at(t, 57.7, 0.5))
    if k:
        text(c, "= THE MOST EXPENSIVE HABIT", 1430, 300, 38, "#ffffff", "Black", a=k)


def s_teaser_car(c, t):
    dark_studio(c, t, "#0d1220")
    cam(c, push(t, 59.5, 61.4, 1.15, 1.0), 960, 600, t, drift=0.3)
    k = ease_out(at(t, 59.6, 1.2))
    with xf(c, 960, 800, alpha=0.25 + 0.75 * k):
        photo_car(c, 0, 0, 1.25, "#1d1f26", t, shine=k)
    glow(c, 960 + 560, 800 - 175, 260 * k, "#fff3c4", 0.35 * k)
    tagpop(c, t, 60.06, 960, 260, "COSTS FAR MORE", RED, "#ffffff", 50)


# ================================================================ 2. NEW CARS
def _prop_car(c, t):
    photo_car(c, 0, 220, 0.62, "#c4161c", t)


def value_chart(c, t, x0=260, y0=300, x1=1660, y1=860):
    chart_frame(c, x0, y0, x1, y1)
    for yr in range(6):
        text(c, f"YEAR {yr}", lerp(x0, x1, yr / 5), y1 + 50, 28, "#8796ad", "Bold")
    vals = [1.0, 0.8, 0.7, 0.62, 0.56, 0.5]
    pts = [(lerp(x0, x1, i / 5), lerp(y1, y0, v)) for i, v in enumerate(vals)]
    return pts


def s_depr(c, t):
    info_board(c, t)
    cam(c, push(t, 63.8, 68.5, 1.0, 1.05), 960, 540, t, drift=0.4)
    pts = value_chart(c, t)
    prog = 0.0
    if t > 64.1:
        prog = 0.2 * ease_out(at(t, 64.1, 1.7))
    if t > 66.3:
        prog = 0.2 + 0.8 * ease_out(at(t, 66.3, 1.4))
    end = plot_line(c, pts, prog, RED, 12)
    text(c, "CAR VALUE", 260, 230, 44, "#c9d3e3", "Black", align="left")
    tagpop(c, t, 64.88, pts[1][0] + 30, pts[1][1] - 90, "−20% IN YEAR 1", RED, "#ffffff", 40)
    tagpop(c, t, 67.22, pts[5][0] - 120, pts[5][1] - 100, "≈ −50% BY YEAR 5", RED, "#ffffff", 40)
    if end:
        with xf(c, end[0], end[1] - 120, 0.22):
            photo_car(c, 0, 0, 1.0, mixhex("#c4161c", "#6b6b6b", prog), t, shine=1 - prog * 0.7, shadow=False)


def s_loan(c, t):
    info_board(c, t)
    cam(c, push(t, 68.5, 71.9, 1.0, 1.05), 960, 540, t, drift=0.4)
    pts = value_chart(c, t)
    plot_line(c, pts, 1.0, RED, 10, dot=False)
    loan = [(lerp(260, 1660, i / 5), lerp(860, 300, v)) for i, v in enumerate((1.05, 0.92, 0.78, 0.62, 0.44, 0.25))]
    k = ease_out(at(t, 68.9, 1.2))
    end = plot_line(c, loan, k, ACC, 10)
    if k > 0.3:
        # shade the underwater gap (loan above value) years 0-3
        g = skia.Path()
        g.moveTo(*loan[0])
        for p in loan[1:4]:
            g.lineTo(*p)
        for p in reversed(pts[:4]):
            g.lineTo(*p)
        g.close()
        c.drawPath(g, P(RED, a=0.25 * clamp((k - 0.3) * 2)))
    text(c, "CAR VALUE", 1640, pts[-1][1] - 30, 34, RED, "Black", align="right")
    if end:
        text(c, "WHAT YOU OWE", 1640, loan[-1][1] + 60, 34, ACC, "Black", align="right", a=k)
    tagpop(c, t, 69.72, 960, 200, "YOU OWE MORE THAN IT'S WORTH", RED, "#ffffff", 40)


def s_used(c, t):
    info_board(c, t)
    cam(c, push(t, 71.9, 79.7, 1.0, 1.06), 960, 540, t, drift=0.4)
    pts = value_chart(c, t)
    plot_line(c, pts, 1.0, RED, 10, dot=False)
    # first-year loss shaded
    k = ease_out(at(t, 72.46, 0.6))
    if k:
        g = poly([pts[0], pts[1], (pts[1][0], 860), (pts[0][0], 860)])
        c.drawPath(g, P(RED, a=0.22 * k))
        text(c, "SOMEONE ELSE'S", (pts[0][0] + pts[1][0]) / 2, 600, 30, "#ffffff", "Black", a=k)
        text(c, "LOSS", (pts[0][0] + pts[1][0]) / 2, 640, 30, "#ffffff", "Black", a=k)
    k2 = ease_out(at(t, 74.36, 0.6))
    if k2:
        x, y = pts[3]
        g = poly([pts[3], pts[4], pts[5], (pts[5][0], 860), (pts[3][0], 860)])
        c.drawPath(g, P(GRN, a=0.18 * k2))
        c.drawCircle(x, y, 26 * back_out(k2), P(GRN))
        c.drawCircle(x, y, 11, P("#ffffff"))
        tagpop(c, t, 74.5, x, y - 200, "YOU BUY HERE", GRN, "#0b1018", 40)
        with xf(c, x, y - 90, 0.2 * back_out(k2)):
            photo_car(c, 0, 0, 1.0, "#2f6fb5", t, shadow=False)
    tagpop(c, t, 76.44, pts[1][0] + 150, pts[1][1] - 40, "STEEPEST DROP: DONE", "#ffffff", "#0b1018", 32)
    tagpop(c, t, 77.7, 1350, 920, "YEARS OF DRIVING LEFT", GRN, "#0b1018", 34)


def s_compare_cars(c, t):
    studio(c, t)
    cam(c, push(t, 79.7, 82.3, 1.0, 1.04), 960, 560, t, drift=0.4)
    photo_car(c, 500, 760, 0.85, "#c4161c", t)
    k, a = pin(t, 79.8, 0.5)
    with xf(c, 1420, 760, k, alpha=a):
        photo_car(c, 0, 0, 0.85, "#2f6fb5", t, old=True)
    tagpop(c, t, 79.9, 500, 330, "NEW", "#0b1018", "#ffffff", 44)
    tagpop(c, t, 80.0, 1420, 330, "3 YEARS OLD", GRN, "#0b1018", 44)
    # price bars
    tagpop(c, t, 80.0, 500, 900, "FULL PRICE", RED, "#ffffff", 40)
    tagpop(c, t, 80.9, 1420, 900, "A FRACTION OF THE COST", GRN, "#0b1018", 40)


def s_a_to_b(c, t):
    cam(c, push(t, 82.3, 86.6, 1.0, 1.05), 960, 560, t, drift=0.5)
    bg(c, "street", 6, dim=0.1)
    # pins
    for x, lbl in ((220, "A"), (1700, "B")):
        c.drawCircle(x, 640, 50, P(ACC))
        c.drawPath(poly([(x - 30, 670), (x + 30, 670), (x, 740)]), P(ACC))
        text(c, lbl, x, 662, 56, "#0b1018", "Black")
    p = ease_out(at(t, 84.0, 2.0))
    cx = lerp(380, 1500, p)
    with xf(c, cx, 905):
        photo_car(c, 0, 0, 0.42, "#c4161c", t, wheel_rot=p * 900)
    tagpop(c, t, 82.94, 960, 230, "NOT WRONG", GRN, "#0b1018", 48, end=84.0)
    tagpop(c, t, 84.38, 960, 230, "JUST EXPENSIVE", RED, "#ffffff", 48)


def notif(c, x, y, s, title, body, amount, a=1.0, icon=("#7d5cc8", "fit")):
    with xf(c, x, y, s, alpha=a):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-420 + 10, -90 + 18, 420 + 10, 90 + 18), 34, 34),
                    blur_paint("#000000", 20, 0.4))
        rrect(c, -420, -90, 840, 180, 34, "#f4f5f8")
        icon_tile(c, -330, 0, 100, *icon)
        text(c, title, -260, -22, 32, "#111111", "Black", align="left")
        text(c, body, -260, 30, 28, "#555a66", "SemiBold", align="left")
        text(c, amount, 390, 14, 44, "#c0392b", "Black", align="right")


def s_teaser_gym(c, t):
    studio(c, t, key="#d9dde3", rim="#9aa2ad")
    cam(c, push(t, 86.6, 90.1, 1.0, 1.06), 960, 540, t, drift=0.4)
    photo_dumbbell(c, 960, 760, 1.1, dust=ease_out(at(t, 87.9, 1.0)))
    for i in range(3):
        st = 87.5 + i * 0.4
        k, a = pin(t, st, 0.4)
        if a:
            notif(c, 960, 210 + i * 0 - i * 14, k * (1 - i * 0.04), "GYM MEMBERSHIP", "Monthly charge", "−$40.00",
                  a * (1 if i == 2 else 0.85))


# ================================================================ 3. GYM
def _prop_gym(c, t):
    photo_dumbbell(c, 0, 80, 0.95, rot=-6, dust=0.8)


def s_gym_year(c, t):
    info_board(c, t)
    cam(c, push(t, 92.8, 95.3, 1.0, 1.05), 960, 540, t, drift=0.4)
    big_number(c, 520, 470, "$40", 170, "#ffffff", a=clamp(at(t, 92.88, 0.3)), sub="A MONTH")
    k = ease_out(at(t, 93.5, 0.4))
    if k:
        text(c, "× 12", 960, 520, 90, "#8796ad", "Black", a=k)
    if t > 93.74:
        v = counter(t, 93.74, 0.9, 40, 480)
        big_number(c, 1420, 470, money(v), 170, ACC, sub="A YEAR")
    for i in range(12):
        k2 = at(t, 93.6 + i * 0.07, 0.25)
        if k2 > 0:
            photo_coin(c, 1150 + (i % 6) * 110, 860 + (i // 6) * 90 - 20 * (1 - k2), 38, a=k2)


def s_per_visit(c, t):
    studio(c, t, key="#e7e3dc")
    cam(c, push(t, 95.3, 100.8, 1.0, 1.04), 960, 540, t, drift=0.4)
    calendar(c, 620, 560, 760, 760, t, "THIS MONTH", marks=[(5, 95.66), (19, 95.9)], start_day=2)
    k = ease_out(at(t, 96.16, 0.4))
    if k:
        with xf(c, 1430, 400, alpha=k):
            text(c, "$40 ÷ 2 VISITS", 0, 0, 56, "#333333", "Black")
    if t > 97.0:
        k2, a2 = pin(t, 97.0, 0.45)
        with xf(c, 1430, 560, k2, alpha=a2):
            text(c, "$20", 0, 60, 190, "#c0392b", "Black")
            text(c, "PER VISIT", 0, 130, 44, "#333333", "Black")
    k3 = ease_out(at(t, 98.98, 0.4))
    if k3:
        with xf(c, 1430, 860, alpha=k3):
            rrect(c, -280, -60, 560, 120, 24, "#2ecc71")
            text(c, "PAY PER CLASS", -20, 18, 46, "#0b1018", "Black")
            check_mark(c, 220, 4, 60, "#ffffff", 1, at(t, 99.9, 0.4))


def s_gym_model(c, t):
    cam(c, push(t, 100.8, 105.1, 1.0, 1.05), 960, 560, t)
    bg(c, "gym", 7, dim=0.2)
    # a nearly empty gym
    figure(c, 1300, FY(0.8), "sam", "stand", "neutral", t, s=0.8, face=-1)
    # paying vs showing up bars
    k = ease_out(at(t, 102.9, 0.8))
    bar(c, 420, 880, 200, 520 * k, ACC, 0.95, None, "PAYING" if k > 0.5 else None)
    k2 = ease_out(at(t, 104.06, 0.6))
    bar(c, 700, 880, 200, 90 * k2, CYN, 0.95, None, "SHOWING UP" if k2 > 0.5 else None)
    for i in range(int(18 * k)):
        x, y = 330 + (i % 6) * 36, 760 - (i // 6) * 70
    tagpop(c, t, 101.16, 960, 180, "GYMS KNOW THIS", "#ffffff", "#0b1018", 44)


def s_free(c, t):
    cam(c, push(t, 105.1, 109.6, 1.0, 1.04), 960, 560, t)
    bg(c, "park", 6)
    p = (t - 105.1)
    figure(c, 500 + p * 60, FY(0.9, 860), "sam", walk(t), "happy", t, s=0.9)
    tags = [("WALKING", 105.14), ("BODYWEIGHT", 105.74), ("FREE VIDEOS", 106.82), ("LOCAL PARK", 107.62)]
    for i, (s, st) in enumerate(tags):
        tagpop(c, t, st, 1180 + (i % 2) * 400, 260 + (i // 2) * 120, s, "#ffffff", "#0b1018", 38)
    k, a = pin(t, 108.6, 0.5)
    if a:
        with xf(c, 1380, 560, k, alpha=a):
            text(c, "$0", 0, 60, 200, GRN, "Black", shadow=True)


def s_door(c, t):
    cam(c, push(t, 109.6, 112.6, 1.0, 1.1), 960, 600, t)
    bg(c, "street", 6, dim=0.15)
    with xf(c, 1240, 830, 0.85):
        photo_door(c, 0, 0, 1.0, open_=ease_out(at(t, 110.6, 0.8)))
        rrect(c, -130, -790, 260, 70, 10, "#0b1018")
        text(c, "GYM", 0, -740, 48, ACC, "Black")
    p = ease_out(at(t, 110.9, 1.4))
    figure(c, lerp(560, 1180, p), FY(0.95, 830), "sam", walk(t) if p < 0.98 else "stand", "focus", t, s=0.95,
           alpha=1 - clamp((p - 0.85) * 6))
    tagpop(c, t, 110.14, 600, 240, "ONLY WORTH IT IF YOU GO", GRN, "#0b1018", 40)


def s_teaser_warranty(c, t):
    dark_studio(c, t, "#1d2a44")
    cam(c, push(t, 112.6, 116.5, 1.0, 1.06), 960, 560, t, drift=0.4)
    photo_box(c, 900, 840, 1.1, label="NEW TV")
    k, a = pin(t, 114.2, 0.5)
    if a:
        with xf(c, 1260, 420, 1.6 * k, alpha=a):
            icon_tile(c, 0, 0, 160, "#2c8fd6", "shield")
    tagpop(c, t, 114.22, 960, 180, "PAYING FOR PEACE OF MIND", "#ffffff", "#0b1018", 42)


# ================================================================ 4. WARRANTIES
def _prop_warranty(c, t):
    photo_box(c, -40, 260, 0.95, label="NEW TV")
    with xf(c, 200, -170, 1.0):
        icon_tile(c, 0, 0, 150, "#2c8fd6", "shield")


def s_checkout(c, t):
    cam(c, push(t, 118.8, 123.3, 1.0, 1.06), 960, 560, t)
    bg(c, "store", 6, dim=0.35)
    figure(c, 1350, FY(), "clerk", "present" if t > 119.8 else "stand", "smile", t, face=-1,
           talk=1.0 if 119.8 < t < 121.6 else 0.0)
    rrect(c, 1040, 640, 800, 180, 12, "#3b4252")
    rrect(c, 1040, 640, 800, 22, 8, "#566078")
    photo_box(c, 1060, 640, 0.42, label="TV")
    figure(c, 560, FY(), "sam", "stand", "neutral" if t < 122.0 else "worried", t, look=(1, -0.3))
    if 119.8 < t:
        k, a = pin(t, 119.82, 0.4)
        with xf(c, 1160, 270, k, alpha=a):
            rrect(c, -360, -80, 720, 160, 70, "#ffffff")
            c.drawPath(poly([(60, 70), (150, 70), (170, 150)]), P("#ffffff"))
            text(c, "PROTECT YOUR PURCHASE?", 0, 16, 44, "#1b1b2f", "Black")
    tagpop(c, t, 122.12, 560, 230, "SOUNDS RESPONSIBLE", "#ffffff", "#0b1018", 36)


def s_profit(c, t):
    info_board(c, t)
    cam(c, push(t, 123.3, 128.7, 1.0, 1.04), 960, 540, t, drift=0.4)
    tagpop(c, t, 124.04, 960, 160, "ONE OF THE MOST PROFITABLE THINGS A STORE SELLS", ACC, "#0b1018", 38)
    broken = {13, 58, 81}
    for i in range(100):
        x = 560 + (i % 20) * 42
        y = 330 + (i // 20) * 90
        k = at(t, 125.9 + i * 0.008, 0.3)
        if k <= 0:
            continue
        col = RED if (i in broken and t > 127.1) else "#5f7aa5"
        icon_tile(c, x, y, 36, col, "box", a=k)
    k2 = ease_out(at(t, 127.1, 0.5))
    if k2:
        text(c, "MOST PRODUCTS NEVER BREAK", 960, 870, 52, "#ffffff", "Black", a=k2)
        text(c, "DURING THE WARRANTY PERIOD", 960, 930, 34, "#9fb0c8", "Bold", a=k2)


def warranty_paper(c, x, y, s, rot=0, a=1.0):
    with xf(c, x, y, s, rot, alpha=a):
        c.drawRect(skia.Rect(-250, -320, 270, 350), blur_paint("#000000", 20, 0.4))
        c.drawRect(skia.Rect(-260, -340, 260, 340), P("#fffdf6"))
        c.drawRect(skia.Rect(-240, -320, 240, 320), P("#c9a227", 4))
        text(c, "WARRANTY", 0, -220, 54, "#2b2b2b", "Black")
        text(c, "1 YEAR INCLUDED", 0, -150, 34, "#2c8fd6", "Black")
        for k in range(7):
            line(c, -190, -80 + k * 44, 190 - (k % 3) * 40, -80 + k * 44, "#b9b4a8", 6)
        c.drawCircle(150, 250, 56, P("#c9a227"))
        c.drawCircle(150, 250, 44, P("#e6c55a"))


def s_included(c, t):
    studio(c, t)
    cam(c, push(t, 128.7, 132.4, 1.0, 1.05), 960, 540, t, drift=0.4)
    k, a = pin(t, 128.9, 0.5)
    warranty_paper(c, 640, 540, 1.0 * k, -5, a)
    k2, a2 = pin(t, 130.9, 0.5)
    if a2:
        photo_card(c, 1340, 520, 1.0 * k2, rot=6, color=("#141414", "#3b3b3b"), name="CREDIT")
        tagpop(c, t, 131.5, 1340, 780, "+ EXTRA PROTECTION", GRN, "#0b1018", 40)


def s_fund(c, t):
    studio(c, t, warm=0.15)
    cam(c, push(t, 132.4, 141.3, 1.0, 1.06), 960, 560, t, drift=0.4)
    fill = 0.15 + 0.6 * ease_out(at(t, 133.4, 2.4))
    if t > 136.4:
        fill -= 0.18 * ease_out(at(t, 137.1, 0.6)) * (1 - ease_out(at(t, 138.0, 1.6)))
    photo_jar(c, 640, 900, 1.2, fill=fill, t=t)
    # something breaks -> covered
    k, a = pin(t, 136.2, 0.4)
    if a and t < 138.0:
        with xf(c, 1320, 520, k, alpha=a * clamp((138.0 - t) / 0.3)):
            photo_phone(c, 0, 0, 0.75, rot=10, screen=lambda c, w, h, tt: _cracked(c, w, h))
        tagpop(c, t, 137.16, 1320, 900, "YOU COVER IT", "#ffffff", "#0b1018", 40, end=138.0)
    if t > 137.9:
        tagpop(c, t, 138.66, 1320, 420, "NOTHING BREAKS?", "#ffffff", "#0b1018", 46)
        k3 = ease_out(at(t, 139.84, 0.5))
        if k3:
            with xf(c, 1320, 600, 0.8 + 0.2 * back_out(k3), alpha=k3):
                rrect(c, -300, -80, 600, 160, 30, GRN)
                text(c, "STILL YOURS", 0, 22, 66, "#0b1018", "Black")


def _cracked(c, w, h):
    c.drawRect(skia.Rect(0, 0, w, h), P("#0c0f16"))
    r = random.Random(3)
    cx, cy = w * 0.6, h * 0.35
    for _ in range(14):
        ang = r.uniform(0, math.tau)
        L = r.uniform(80, 400)
        p = skia.Path()
        p.moveTo(cx, cy)
        x, y = cx, cy
        for k in range(4):
            x += math.cos(ang + r.uniform(-0.4, 0.4)) * L / 4
            y += math.sin(ang + r.uniform(-0.4, 0.4)) * L / 4
            p.lineTo(x, y)
        c.drawPath(p, P("#dfe8f5", 2.5, 0.8))


# ================================================================ 5. FAST FASHION
def _prop_shirt(c, t):
    photo_tshirt(c, 0, 0, 0.9, "#d64933", tag="$15", rot=-4)


def s_sandwich(c, t):
    studio(c, t)
    cam(c, push(t, 144.8, 147.3, 1.0, 1.05), 960, 540, t, drift=0.4)
    photo_tshirt(c, 560, 520, 0.85, "#d64933", tag="$7")
    k = ease_out(at(t, 145.3, 0.4))
    if k:
        text(c, "=", 960, 560, 160, "#333333", "Black", a=k)
    k2, a2 = pin(t, 145.76, 0.45)
    if a2:
        with xf(c, 1400, 720, k2, alpha=a2):
            sandwich(c, 0, 0, 1.35)
    tagpop(c, t, 146.34, 960, 160, "FEELS LIKE A WIN", GRN, "#0b1018", 46)


def s_cpw(c, t):
    info_board(c, t)
    cam(c, push(t, 147.3, 150.2, 1.0, 1.05), 960, 540, t, drift=0.4)
    k = ease_out(at(t, 147.7, 0.5))
    with xf(c, 960, 400, alpha=k):
        text(c, "COST PER WEAR", 0, 0, 110, ACC, "Black", shadow=True)
    k2 = ease_out(at(t, 149.0, 0.5))
    if k2:
        with xf(c, 960, 640, alpha=k2):
            rrect(c, -520, -100, 1040, 200, 30, "#16233a")
            text(c, "PRICE  ÷  TIMES WORN", 0, 26, 76, "#ffffff", "Black")


def s_two_shirts(c, t):
    studio(c, t)
    cam(c, push(t, 150.2, 157.5, 1.0, 1.04), 960, 540, t, drift=0.4)
    wears1 = int(counter(t, 151.3, 0.8, 0, 5))
    worn1 = ease_out(at(t, 151.16, 1.2))
    photo_tshirt(c, 520, 460, 0.75, "#d64933", worn=worn1, tag="$15")
    text(c, f"WORN {wears1}×", 520, 820, 48, "#333333", "Black", a=clamp(at(t, 151.3, 0.3)))
    k = ease_out(at(t, 153.1, 0.4))
    if k:
        with xf(c, 520, 930, 0.8 + 0.2 * back_out(k), alpha=k):
            rrect(c, -230, -60, 460, 110, 24, RED)
            text(c, "$3 / WEAR", 0, 18, 56, "#ffffff", "Black")
    k2, a2 = pin(t, 154.4, 0.5)
    if a2:
        with xf(c, 1400, 460, k2, alpha=a2):
            photo_tshirt(c, 0, 0, 0.75, "#1f4e79", tag="$60")
        wears2 = int(counter(t, 155.4, 0.8, 0, 60))
        text(c, f"WORN {wears2}×", 1400, 820, 48, "#333333", "Black", a=a2)
    k3 = ease_out(at(t, 156.6, 0.4))
    if k3:
        with xf(c, 1400, 930, 0.8 + 0.2 * back_out(k3), alpha=k3):
            rrect(c, -230, -60, 460, 110, 24, GRN)
            text(c, "$1 / WEAR", 0, 18, 56, "#0b1018", "Black")


def hanger_shirt(c, x, y, s, col):
    with xf(c, x, y, s):
        pp = skia.Path()
        pp.moveTo(-150, -260)
        pp.lineTo(0, -320)
        pp.lineTo(150, -260)
        c.drawPath(pp, P("#8a8f98", 8))
        c.drawPath(poly([(0, -320), (-6, -350), (6, -350)]), P("#8a8f98"))
        photo_tshirt(c, 0, 0, 0.6, col)


def s_basics(c, t):
    studio(c, t, key="#ece8e1")
    cam(c, push(t, 157.5, 163.1, 1.0, 1.05), 960, 540, t, drift=0.4)
    if t < 159.9:
        photo_tshirt(c, 960, 520, 0.9, "#d64933", worn=1.0, tag="$15")
        stamp(c, 960, 520, 1.0, "THE EXPENSIVE ONE", RED, at(t, 158.4, 0.35))
    else:
        c.drawRect(skia.Rect(260, 300, 1660, 312), P("#8a8f98"))
        for i, col in enumerate(("#1f2a44", "#e9e4da", "#4a5a3a", "#7a8ca3")):
            k, a = pin(t, 160.1 + i * 0.15, 0.45)
            if a:
                with xf(c, 0, 0, alpha=a):
                    hanger_shirt(c, 450 + i * 340, 640, k, col)
        tagpop(c, t, 160.54, 960, 180, "FEWER, BETTER BASICS", GRN, "#0b1018", 48)
        tagpop(c, t, 161.6, 960, 960, "COST LESS OVER TIME", "#0b1018", "#ffffff", 40)


SCENES_A = [
    (0.0, 5.62, s_hook),
    (5.62, 9.85, s_not_lux),
    (9.85, 15.38, s_list),
    (15.38, 19.15, s_prices),
    (19.15, 24.5, s_question),
    (24.5, 27.08, s_title),
    (27.08, 30.0, s_pocket),
    (30.0, 33.28, card_scene(1, ["FOOD DELIVERY", "APPS"], "The cost arrives in small pieces", _prop_delivery)),
    (33.28, 37.38, s_receipt),
    (37.38, 42.26, s_platform),
    (42.26, 44.62, s_menu),
    (44.62, 48.56, s_door_price),
    (48.56, 52.5, s_year_cost),
    (52.5, 59.48, s_default),
    (59.48, 61.32, s_teaser_car),
    (61.32, 63.78, card_scene(2, ["BRAND-NEW", "CARS"], "The steepest loss comes first", _prop_car)),
    (63.78, 68.5, s_depr),
    (68.5, 71.86, s_loan),
    (71.86, 79.66, s_used),
    (79.66, 82.24, s_compare_cars),
    (82.24, 86.58, s_a_to_b),
    (86.58, 90.06, s_teaser_gym),
    (90.06, 92.82, card_scene(3, ["GYM MEMBERSHIPS", "YOU DON'T USE"], None, _prop_gym)),
    (92.82, 95.3, s_gym_year),
    (95.3, 100.8, s_per_visit),
    (100.8, 105.08, s_gym_model),
    (105.08, 109.58, s_free),
    (109.58, 112.58, s_door),
    (112.58, 116.46, s_teaser_warranty),
    (116.46, 118.8, card_scene(4, ["EXTENDED", "WARRANTIES"], "Paying for peace of mind", _prop_warranty)),
    (118.8, 123.3, s_checkout),
    (123.3, 128.7, s_profit),
    (128.7, 132.38, s_included),
    (132.38, 141.34, s_fund),
    (141.34, 144.8, card_scene(5, ["CHEAP", "FAST FASHION"], "Measure cost per wear", _prop_shirt)),
    (144.8, 147.26, s_sandwich),
    (147.26, 150.18, s_cpw),
    (150.18, 157.5, s_two_shirts),
    (157.5, 163.1, s_basics),
]
