"""Scenes + shot list for:
  "Why Attackers Never Touch a Woman Who Does This (Yakuza Secret)"
Same contract as scenes.py:  fn(c, t, d, w, h, S, **kw)."""
import math
import skia
from kit import *  # noqa: F401,F403
from scenes import stage, title_card, quote, endcard  # noqa: F401


def street_lamp(c, x, ground, t, h=620, on=1.0):
    line(c, x, ground, x, ground - h, "#1c1c1f", 18)
    line(c, x, ground - h, x + 90, ground - h - 10, "#1c1c1f", 14)
    glow(c, x + 95, ground - h + 10, 220, "#ffd58a", 0.45 * on)
    p = poly([(x + 75, ground - h + 5), (x + 115, ground - h + 5), (x + 330, ground), (x - 140, ground)])
    soft_shape(c, p, "#ffd58a", 0.16 * on, 18)


def night_ground(c, w, h, t, sign="銀行", col="#ff4d4d"):
    bg_night_street(c, w, h, t, sign=sign, sign_col=col, rain=False)


# ============================================================ HOOK
def hook(c, t, d, w, h, S):
    night_ground(c, w, h, t)
    c.save(); stage(c, w, h)
    g = 960
    street_lamp(c, 700, g, t)
    wx = lerp(120, 560, clamp(t / max(d, 1)))
    woman(c, wx, g, 0.62, "walk", t, "#0b0b0d", rim="#ffd58a", cane=True, walk=t)
    for i in range(2):
        mx = wx - 330 - i * 120
        man(c, mx, g, 0.5, "stand", t, "#060607", rim=RED, big=1.1, run=t * 0.7)
    stamp(c, t, 0.4, 290, 150, "NAMBA, OSAKA · 1986", GOLD, 46, rot=-3)
    if S(2) > -50:
        reticle(c, wx, g - 0.62 * 800, 60, t, RED, t0=S(2))
        kicker(c, t, S(2), S(3) + 1.5, "\"HER.\"", 540, 330, 110)
    if S(4) > -50:
        kicker(c, t, S(4) + 1.2, d + 1, "SHE DID ONE THING", 540, 330, 76)
    c.restore()


def easy_target(c, t, d, w, h, S):
    night_ground(c, w, h, t)
    c.save(); stage(c, w, h)
    street_lamp(c, 420, 980, t)
    woman(c, 620, 980, 0.8, "stand", t, "#0b0b0d", rim="#ffd58a", cane=True)
    tags = [(7, "SMALL", 880, 300), (8, "OLD", 900, 430), (9, "A CANE", 880, 560)]
    for si, s, x, y in tags:
        k = pop(t, S(si))
        if k > 0:
            with xf(c, x, y, s=k, rot=-4): rrect(c, -130, -46, 260, 92, 16, "#ffffff"); text(c, s, 0, 18, 46, "#111111")
    if S(10) > -50:
        kicker(c, t, S(10), S(11) - 0.1, "EASIEST TARGET?", 540, 150, 80)
    if S(11) > -50:
        kicker(c, t, S(11), d + 1, "THEY WOULD NOT TOUCH HER", 540, 150, 64)
    c.restore()


def seven(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#17120f")
    c.save(); stage(c, w, h)
    icons = ["keys", "eye", "light", "alarm", "space", "voice", "mind"]
    for i, ic in enumerate(icons):
        t0 = 0.4 + i * 0.32
        k = pop(t, t0)
        if k <= 0: continue
        x = 140 + (i % 4) * 267 if i < 4 else 273 + (i - 4) * 267
        y = 330 if i < 4 else 560
        with xf(c, x, y, s=k):
            c.drawCircle(0, 0, 95, P("#221b15")); c.drawCircle(0, 0, 95, P(GOLD if i < 6 else RED, 5))
            icon(c, ic, 0, 0, 0.9, "#ffffff" if i < 6 else RED, t)
            text(c, str(7 - i), 70, -70, 44, GOLD)
    counter(c, t, 0.3, 540, 170, 7, 120, GOLD, dur=2.0, suffix=" THINGS")
    for i, (si, s, col) in enumerate([(14, "NO GUN", RED), (15, "NO STRENGTH", RED), (16, "COST: $0", GREEN)]):
        k = pop(t, S(si)) if S(si) > -50 else 0
        if k > 0:
            with xf(c, 200 + i * 340, 830, s=k): rrect(c, -150, -50, 300, 100, 50, col); text(c, s, 0, 16, 40, "#ffffff")
    if S(17) > -50:
        kicker(c, t, S(17), d + 1, "WAIT FOR NUMBER ONE", 540, 990, 60)
    c.restore()


def chooser(c, t, d, w, h, S):
    bg_night_street(c, w, h, t, sign="難波", sign_col="#ffb347", rain=False)
    c.save(); stage(c, w, h)
    r = rng(5)
    people = []
    for i in range(7):
        x = 90 + i * 150 + 40 * math.sin(t * 0.6 + i); s = r.uniform(0.33, 0.42)
        people.append((x, s))
    pick = int(t / 1.8) % 7
    for i, (x, s) in enumerate(people):
        if i % 2: woman(c, x, 1000, s, "walk", t, "#0a0a0b", rim="#5b4a3a", walk=t + i, bag=True)
        else: man(c, x, 1000, s * 0.9, "stand", t, "#0a0a0b", rim="#5b4a3a", big=1.0, run=t + i)
    px, ps = people[pick]
    reticle(c, px, 1000 - ps * 800, 50, t % 1.8 + 0.0, RED, t0=0.0)
    kicker(c, t, 0.3, d + 1, "MY JOB: CHOOSE", 540, 170, 76)
    c.restore()


def tne(c, t, d, w, h, S):
    fill_shader(c, skia.Rect(0, 0, w, h), radial(w / 2, h / 2, max(w, h) * 0.7, ["#1d1612", "#050403"]))
    c.save(); stage(c, w, h)
    if S(31) > -50 and t < S(33) - 0.2:
        kicker(c, t, S(30), S(33) - 0.2, "NOT BRAVE. LAZY.", 540, 520, 86)
    items = [(33, "time", "TIME"), (34, "noise", "NOISE"), (35, "eye", "EYES")]
    for i, (si, ic, s) in enumerate(items):
        if S(si) < -50: continue
        k = pop(t, S(si))
        if k <= 0: continue
        x = 200 + i * 340
        with xf(c, x, 450, s=k):
            c.drawCircle(0, 0, 130, P(RED, a=0.18)); c.drawCircle(0, 0, 130, P(RED, 6))
            icon(c, ic, 0, 0, 1.3, "#ffffff", t)
            text(c, s, 0, 230, 66, "#ffffff")
    if S(37) > -50:
        kicker(c, t, S(37), d + 1, "GIVE ONE → WE LEAVE", 540, 930, 70)
    c.restore()


# ============================================================ #7 KEYS
def key_claw(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#16120f")
    c.save(); stage(c, w, h)
    hit = S(44) + 1.0 if S(44) > -50 else 99
    fall = clamp((t - hit - 0.15) * 1.5)
    rrect(c, 760, 220, 220, 520, 60, "#3b2a1e"); rrect(c, 760, 220, 220, 520, 60, "#1c130c", stroke=6)
    fx = lerp(200, 560, ease_out(clamp((t - hit + 0.5) / 0.5))) if t < hit + 0.2 else 560 - 30 * fall
    with xf(c, fx, 470, s=1.15):
        fist_shape(c, 0, 0, 1, SKIN, rot=90)
        for i in range(3):
            ang = 0 if fall == 0 else 40 * fall * (i - 1)
            with xf(c, 70, -50 + i * 45, rot=ang):
                if fall < 0.4: line(c, 0, 0, 90, 0, "#c9cfd4", 14)
    if fall > 0:
        for i in range(3):
            kx = 650 + i * 30; ky = 470 + 420 * fall ** 2
            line(c, kx, ky, kx + 50, ky + 30, "#c9cfd4", 12)
        glow(c, fx + 60, 470, 120, RED, 0.5 * (1 - fall))
    impact(c, 740, 470, t, hit, "#ffffff", 140)
    if S(41) > -50: kicker(c, t, S(41), S(43) - 0.1, "NOT LIKE CLAWS", 540, 150, 76)
    if S(43) > -50: stamp(c, t, S(43), 270, 150, "DORIS, 78", RED, 52)
    if S(46) > -50: kicker(c, t, S(46), d + 1, "NO WEAPON. NO WAY HOME.", 540, 980, 58)
    c.restore()


def keys_ready(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#121519", light=(0.2, 0.1))
    c.save(); stage(c, w, h)
    g = 900
    rect(c, 0, g, 1080, 180, "#1e1f22")
    car_side(c, 800, g, 0.95, lights=(1.0 if (S(53) > -50 and t > S(53) + 0.5 and int(t * 4) % 2) else 0.0), t=t)
    wx = lerp(80, 470, clamp(t / max(6.0, S(50) + 0.5)))
    woman(c, wx, g, 0.55, "walk", t, "#0b0b0d", rim="#7f9bb3", walk=t)
    with xf(c, wx + 75, g - 0.55 * 300): icon(c, "keys", 0, 0, 0.5, GOLD, t)
    if S(48) > -50: kicker(c, t, S(48), S(51) - 0.1, "KEYS OUT BEFORE THE CAR", 540, 150, 62)
    if S(51) > -50: kicker(c, t, S(51), S(52) - 0.1, "DIGGING AT THE DOOR = TARGET", 540, 150, 56)
    if S(52) > -50 and t > S(52):
        k = pop(t, S(52))
        with xf(c, 540, 470, s=k):
            rrect(c, -90, -150, 180, 300, 70, "#22262b"); rrect(c, -90, -150, 180, 300, 70, "#cfd6dd", stroke=5)
            for i in range(2): c.drawCircle(0, -70 + i * 80, 30, P("#9aa4ad"))
            press = 1 if (t > S(54) and int(t * 3) % 2) else 0
            c.drawCircle(0, 90, 38 - 4 * press, P(RED)); glow(c, 0, 90, 90, RED, 0.6 * press)
        if S(54) > -50 and t > S(54):
            sound_rings(c, 800, g - 120, t, RED, a=0.6)
        if S(55) > -50: kicker(c, t, S(55), d + 1, "TIME + NOISE. FREE.", 540, 150, 70)
    c.restore()


# ============================================================ #6 EYES
def garage(c, t, d, w, h, S):
    fill_shader(c, skia.Rect(0, 0, w, h), linear(0, 0, 0, h, ["#14161a", "#0b0c0e"]))
    for i in range(0, int(w), 240):
        glow(c, i + 120, 60, 200, "#cfe3ff", 0.12)
    c.save(); stage(c, w, h)
    stamp(c, t, 0.3, 280, 110, "UMEDA, OSAKA · 2004", GOLD, 40, rot=-3)
    # top-down rows of cars
    cars = []
    for row, y in enumerate((300, 780)):
        for i in range(6):
            x = 120 + i * 170
            cars.append((x, y))
            rrect(c, x - 55, y - 100, 110, 200, 26, "#2b3038"); rrect(c, x - 40, y - 60, 80, 70, 12, "#56606c")
    line(c, 40, 540, 1040, 540, "#e8d36a", 4, 0.4)
    wx = lerp(80, 1000, clamp(t / max(d, 1)))
    look = math.sin(t * 2.4) * 0.9
    dirv = (0 if look == 0 else 1)
    ang = -math.pi / 2 if look > 0 else math.pi / 2
    cone = poly([(wx, 540), (wx + math.cos(ang - 0.4) * 260, 540 + math.sin(ang - 0.4) * 260), (wx + math.cos(ang + 0.4) * 260, 540 + math.sin(ang + 0.4) * 260)])
    soft_shape(c, cone, "#ffe9a8", 0.35, 6)
    c.drawCircle(wx, 540, 34, P("#d9c2a0")); c.drawCircle(wx, 540, 14, P("#555555"))
    for x, y in cars:
        if x < wx - 40:
            check_mark(c, x, y, 60, GREEN, prog=1)
    if S(63) > -50: kicker(c, t, S(63), d + 1, "\"SHE'S COUNTING US.\"", 540, 1000, 66)
    c.restore()


def choices(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#141414")
    c.save(); stage(c, w, h)
    ws = [("phone", "PHONE"), ("bag", "IN THE BAG"), ("headphones", "HEADPHONES"), (None, "HEAD UP")]
    for i, (ic, lab) in enumerate(ws):
        x = 150 + i * 260
        down = 1 if ic else 0
        woman(c, x, 900, 0.45, "phone" if ic == "phone" else "stand", t, "#0b0b0d", rim="#666666" if ic else GOLD, head_down=down, bag=(ic != "phone"))
        if ic: icon(c, ic, x, 300, 0.7, "#ffffff", t)
        else: icon(c, "eye", x, 300, 0.7, GOLD, t)
        text(c, lab, x, 990, 34, "#ffffff" if ic else GOLD)
        if ic: reticle(c, x, 900 - 0.45 * 560, 60, t, RED, t0=0.6 + i * 0.4)
        else:
            k = pop(t, 2.2)
            if k > 0:
                with xf(c, x, 160, s=k): rrect(c, -100, -40, 200, 80, 40, GREEN); text(c, "SKIPPED", 0, 14, 34, "#06140a")
    kicker(c, t, 0.2, d + 1, "CHOSEN IN 3 SECONDS", 540, 100, 56, bar=RED)
    c.restore()


def warning_signs(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#18110f")
    c.save(); stage(c, w, h)
    text(c, "WARNING SIGNS", 540, 140, 72, RED, a=clamp(t * 3), shadow=0.6)
    items = [(68, "SPEEDS UP TO CLOSE THE GAP"), (69, "MATCHES YOUR PACE"), (70, "STANDING FOR NO REASON"), (71, "\"GOT THE TIME?\" TOO CLOSE")]
    for i, (si, s) in enumerate(items):
        t0 = S(si) if S(si) > -50 else 0.5 + i
        k = ease_out(at(t, t0, 0.4))
        if k <= 0: continue
        y = 290 + i * 150
        with xf(c, 540 + (1 - k) * 80, y, alpha=k):
            rrect(c, -470, -58, 940, 116, 18, "#241a17"); rrect(c, -470, -58, 16, 116, 8, RED)
            text(c, "!", -400, 22, 64, RED)
            text(c, s, -340, 16, 42, "#ffffff", align="left")
    if S(72) > -50: kicker(c, t, S(72), S(74) - 0.1, "IT'S A TEST", 540, 950, 76)
    if S(74) > -50: kicker(c, t, S(74), d + 1, "STOMACH COLD? BELIEVE IT.", 540, 950, 62)
    c.restore()


# ============================================================ #5 LIGHT
def porch(c, t, d, w, h, S):
    fill_shader(c, skia.Rect(0, 0, w, h), linear(0, 0, 0, h, ["#04060c", "#0c1220", "#0a0a0a"]))
    r = rng(8)
    for i in range(70):
        c.drawCircle(r.uniform(0, w), r.uniform(0, h * 0.45), r.uniform(0.6, 1.8), P("#ffffff", a=r.uniform(0.2, 0.7)))
    c.drawPath(poly([(0, h * 0.62), (w * 0.3, h * 0.42), (w * 0.6, h * 0.55), (w, h * 0.4), (w, h), (0, h)]), P("#05070a"))
    c.save(); stage(c, w, h)
    stamp(c, t, 0.3, 300, 120, "ROKKO ROAD, KOBE · 2003", GOLD, 38, rot=-3)
    on = S(79) if S(79) > -50 else 99
    lit = clamp((t - on) * 8)
    # house
    c.drawPath(poly([(560, 520), (790, 380), (1020, 520)]), P("#0e0f12"))
    rect(c, 590, 520, 400, 300, "#121317")
    rect(c, 640, 600, 70, 90, "#ffd27a" if lit > 0.5 else "#1b1d22")
    glow(c, 860, 560, 260, "#ffd27a", 0.55 * lit)
    rect(c, 845, 540, 30, 20, "#fff1c4" if lit else "#333333")
    car_side(c, 300, 900, 0.85, lights=0.6, t=t)
    if S(80) > -50 and t > S(80):
        k = clamp((t - S(80)) * 2)
        woman(c, 850, 860, 0.38, "point_light", t, "#0b0b0d", rim="#ffd27a", a=k, bag=False)
        beam = poly([(850 + 140, 860 - 245), (60, 780), (60, 900)])
        soft_shape(c, beam, "#fff6d0", 0.35 * k, 10)
        if t > S(80) + 2.5:
            with xf(c, 760, 320, s=pop(t, S(80) + 2.5), rot=5):
                rrect(c, -80, -100, 160, 200, 8, "#f2ead6"); [line(c, -55, -60 + j * 32, 55, -60 + j * 32, "#6b6b6b", 3) for j in range(5)]
                text(c, "KB 3721", 0, -66, 26, "#222222")
    if S(82) > -50: kicker(c, t, S(82), d + 1, "A LIGHT + A PENCIL", 540, 1010, 64)
    c.restore()


def flashlight(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#0d0e12", light=(0.1, 0.5), a=0.4)
    c.save(); stage(c, w, h)
    # face of attacker (silhouette head) on right
    blink = S(87) if S(87) > -50 else 2
    hx, hy = 820, 470
    turn = ease_out(clamp((t - blink) * 3)) if t > blink else 0
    with xf(c, hx, hy, rot=-25 * turn):
        c.drawOval(skia.Rect(-120, -150, 120, 150), P("#16161a")); c.drawOval(skia.Rect(-120, -150, 120, 150), P("#3a3a44", 4))
        for ex in (-45, 45):
            if t > blink and int(t * 6) % 3 == 0: line(c, ex - 22, -20, ex + 22, -20, "#ffffff", 5)
            else: c.drawOval(skia.Rect(ex - 22, -32, ex + 22, -8), P("#ffffff"))
    # flashlight
    with xf(c, 170, 520, rot=-4):
        rrect(c, -120, -32, 220, 64, 18, "#2c2f35"); rect(c, 90, -46, 50, 92, "#3c4048")
    on = clamp((t - 0.6) * 5)
    soft_shape(c, poly([(140, 490), (140, 550), (980, 720), (980, 220)]), "#fff6d0", 0.5 * on, 14)
    glow(c, hx, hy, 240, "#fff6d0", 0.55 * on)
    if S(85) > -50:
        k = pop(t, S(85))
        if k > 0:
            with xf(c, 270, 230, s=k): rrect(c, -170, -55, 340, 110, 20, GOLD); text(c, "300+ LUMENS", 0, 16, 44, "#111111")
        k2 = pop(t, S(85) + 1.8)
        if k2 > 0:
            with xf(c, 270, 360, s=k2): text(c, "~$20", 0, 20, 70, "#ffffff")
    if S(88) > -50:
        counter(c, t, S(88), 540, 920, 2, 84, GOLD, dur=0.5, suffix=" SEC HEAD START")
    c.restore()


# ============================================================ #4 ALARM
def alarm_lot(c, t, d, w, h, S):
    fill_shader(c, skia.Rect(0, 0, w, h), linear(0, 0, 0, h, ["#93a7b8", "#cfd8df", "#6d747a"]))
    c.save(); stage(c, w, h)
    stamp(c, t, 0.3, 300, 110, "SEATTLE PARKING LOT", "#1b2a3a", 40, rot=-3)
    rect(c, -400, 640, 1880, 440, "#4f5459")
    for i in range(6):
        line(c, 60 + i * 190, 660, 20 + i * 190, 1080, "#e8e8e8", 6, 0.7)
    shriek = S(94) if S(94) > -50 else 99
    on = t > shriek
    woman(c, 540, 960, 0.5, "stand", t, "#16161a", rim="#ffffff", bag=True)
    if on:
        sound_rings(c, 455, 960 - 0.5 * 410, t, RED, n=5, rmax=520, a=0.8, speed=1.8)
    # heads that turn: little people around
    pos = [(140, 780), (300, 700), (790, 720), (940, 800), (200, 960), (900, 980)]
    for i, (x, y) in enumerate(pos):
        turn = ease_out(clamp((t - shriek - 0.4 - i * 0.12) * 3)) if on else 0
        woman(c, x, y, 0.22, "stand", t, "#24262a", rim=GOLD if turn > 0.5 else None, bag=False) if i % 2 else man(c, x, y, 0.2, "stand", t, "#24262a", rim=GOLD if turn > 0.5 else None)
        if turn > 0: arrow(c, x, y - 200, lerp(x, 540, 0.25), lerp(y - 200, 760, 0.25), GOLD, 6, prog=turn)
    if on: kicker(c, t, shriek, d + 1, "EVERY HEAD TURNED", 540, 240, 72)
    c.restore()


def alarm_spec(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#151012")
    c.save(); stage(c, w, h)
    with xf(c, 300, 480, s=1.0):
        rrect(c, -90, -140, 180, 260, 70, RED); c.drawCircle(0, -180, 40, P("#d0d0d0", 12))
        text(c, "dB", 0, 30, 60, "#ffffff")
    sound_rings(c, 300, 480, t, RED, n=5, rmax=420, a=0.6, speed=1.5)
    counter(c, t, 0.2, 760, 400, 120, 170, RED, dur=1.0, suffix="")
    text(c, "DECIBELS", 760, 470, 44, "#ffffff", a=clamp(t))
    items = [(100, "NOTHING TO AIM"), (101, "NO TRAINING"), (102, "NO STRENGTH")]
    for i, (si, s) in enumerate(items):
        t0 = S(si) if S(si) > -50 else 1 + i * 0.5
        k = ease_out(at(t, t0, 0.3))
        if k <= 0: continue
        with xf(c, 600, 590 + i * 80, alpha=k):
            check_mark(c, 0, -14, 44, GREEN, prog=k); text(c, s, 50, 0, 40, "#ffffff", align="left")
    if S(105) > -50:
        with xf(c, 760, 300, s=pop(t, S(105))): text(c, "$10–20", 0, 0, 60, GOLD)
    if S(106) > -50: kicker(c, t, S(106), d + 1, "A LOUD OLD WOMAN WINS", 540, 990, 62)
    c.restore()


# ============================================================ #3 SPACE
def chalk_line(c, t, d, w, h, S):
    bg_dojo(c, w, h, t)
    c.save(); stage(c, w, h)
    k = ease_out(clamp((t - 0.6) / 1.5))
    line(c, 540, 1000, 540, 1000 - 380 * k, "#f4f1e6", 12, 0.9)
    woman(c, 360, 1000, 0.42, "stand", t, "#100b07", rim="#ffcf87", bag=False)
    man(c, 760, 1000, 0.5, "stand", t, "#100b07", rim="#ffcf87", big=1.1)
    stamp(c, t, 0.3, 230, 120, "AGE 12", RED, 46)
    if S(112) > -50:
        k2 = pop(t, S(113) if S(113) > -50 else S(112) + 2)
        if k2 > 0:
            with xf(c, 540, 330, s=k2):
                text(c, "間合い", 0, 0, 150, "#f4f1e6", "jp")
                text(c, "MA-AI", 0, 90, 64, GOLD)
    elif S(110) > -50:
        pass
    if S(110) > -50 and t < (S(112) if S(112) > -50 else d):
        kicker(c, t, S(110), (S(112) if S(112) > -50 else d) - 0.1, "DISTANCE DECIDES", 540, 300, 76)
    c.restore()


def keep_space(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#121417")
    c.save(); stage(c, w, h)
    rect(c, 0, 0, 1080, 1080, "#2a2c30", 0.6)
    # parking space outline (top-down)
    line(c, 260, 200, 260, 760, "#f2f2f2", 6, 0.6); line(c, 560, 200, 560, 760, "#f2f2f2", 6, 0.6)
    text(c, "1 PARKING SPACE", 410, 180, 34, "#ffffff")
    mx = lerp(840, 700, clamp(t / 3))
    stepped = S(115) if S(115) > -50 else 2
    k = ease_out(clamp((t - stepped) / 0.8))
    wx, wy = lerp(180, 120, k), lerp(480, 640, k)
    c.drawCircle(mx, 480, 46, P("#141414")); c.drawCircle(mx, 480, 46, P(RED, 5))
    c.drawCircle(wx, wy, 40, P("#d9c2a0")); c.drawCircle(wx, wy, 40, P(GOLD, 5))
    arrow(c, 180, 480, 120, 640, GREEN, 10, prog=k)
    if S(116) > -50 and t > S(116):
        kk = pop(t, S(116))
        with xf(c, 420, 560, s=kk):
            rrect(c, -90, -55, 180, 110, 12, "#8a8f96"); line(c, -90, -20, 90, -20, "#5a5f66", 6); line(c, -90, 20, 90, 20, "#5a5f66", 6)
        text(c, "CART BETWEEN YOU", 420, 680, 36, GOLD, a=kk)
    kicker(c, t, 0.2, (S(115) if S(115) > -50 else d) - 0.1, "HE'S FASTER THAN YOUR PURSE", 540, 950, 54)
    if S(115) > -50: kicker(c, t, S(115), d + 1, "STEP BACK + TO THE SIDE", 540, 950, 62, bar=GREEN, color="#06140a")
    c.restore()


# ============================================================ #2 VOICE
def market(c, t, d, w, h, S):
    fill_shader(c, skia.Rect(0, 0, w, h), linear(0, 0, 0, h, ["#2a1a10", "#120a06"]))
    for i in range(int(w / 140) + 1):
        lantern(c, 70 + i * 140, 90 + (i % 2) * 24, 0.65, t, "#ffb347" if i % 2 else "#ff5a3c", "")
    c.save(); stage(c, w, h)
    stamp(c, t, 0.3, 300, 220, "TSURUHASHI MARKET · 1978", GOLD, 38, rot=-3)
    rect(c, 140, 720, 800, 40, "#6b4524"); rect(c, 140, 760, 800, 240, "#3b2414")
    for i in range(7):
        c.drawOval(skia.Rect(180 + i * 105, 690, 260 + i * 105, 730), P(["#b8c44a", "#d9a441", "#8fb04a"][i % 3]))
    roar = S(127) if S(127) > -50 else 99
    pose = "hands_up" if t > roar else "stand"
    woman(c, 320, 1000, 0.6, pose, t, "#0e0907", rim="#ffb347", bag=False)
    lean = 0 if t < roar + 0.6 else ease_out(clamp((t - roar - 0.6) * 2))
    with xf(c, 760 + 120 * lean, 1000, rot=-12 * (1 - lean)):
        man(c, 0, 0, 0.6, "stand", t, "#080606", rim=RED, big=1.1)
    if t > roar:
        sound_rings(c, 320, 1000 - 0.6 * 820, t, "#ffffff", n=4, rmax=500, a=0.6, speed=1.6)
        kicker(c, t, roar, d + 1, "\"BACK UP!\"", 540, 420, 110)
    if S(128) > -50 and t > S(128):
        counter(c, t, S(128), 800, 620, 50, 80, GOLD, dur=0.8, suffix=" FACES")
    c.restore()


def hands_voice(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#141210", light=(0.5, 0.0))
    c.save(); stage(c, w, h)
    woman(c, 540, 1080, 0.95, "hands_up", t, "#0e0b09", rim="#ffcf87", bag=False)
    if S(132) > -50:
        label_line(c, t, S(132), 430, 1080 - 0.95 * 800, 120, 260, "PROTECTS FACE", GOLD, 38)
        label_line(c, t, S(132) + 1.5, 650, 1080 - 0.95 * 800, 760, 230, "LOOKS LIKE PEACE", GREEN, 38)
    if S(134) > -50 and t > S(134):
        sound_rings(c, 540, 1080 - 0.95 * 800, t, "#ffffff", n=4, rmax=520, a=0.5, speed=1.6)
        kicker(c, t, S(134), (S(135) if S(135) > -50 else d) + 0.6, "\"BACK UP!\"", 540, 560, 120)
    if S(136) > -50:
        for i, s in enumerate(["QUIET", "YOU ALONE"]):
            k = pop(t, S(136) + i * 0.4)
            if k > 0:
                with xf(c, 330 + i * 420, 900, s=k): rrect(c, -170, -50, 340, 100, 20, "#1f1a17"); text(c, s, 0, 16, 46, "#ffffff")
                x_over(c, 330 + i * 420, 900, 110, t, (S(137) if S(137) > -50 else S(136) + 1.5) + i * 0.2)
    c.restore()


def poll7(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#141a1f")
    c.save(); stage(c, w, h)
    text(c, "WHICH ONE WOULD YOU BET ON?", 540, 150, 56, "#ffffff", a=clamp(t * 3))
    opts = [("keys", "KEYS"), ("eye", "EYES"), ("light", "LIGHT"), ("alarm", "ALARM"), ("space", "SPACE"), ("voice", "VOICE")]
    for i, (ic, lab) in enumerate(opts):
        k = pop(t, 0.3 + i * 0.25)
        if k <= 0: continue
        x = 220 + (i % 3) * 320; y = 340 + (i // 3) * 250
        hi = int(t * 1.2) % 6 == i
        with xf(c, x, y, s=k * (1.06 if hi else 1)):
            rrect(c, -140, -100, 280, 200, 24, "#1f262d"); rrect(c, -140, -100, 280, 200, 24, GOLD if hi else "#3a4550", stroke=5)
            icon(c, ic, 0, -20, 0.8, GOLD if hi else "#ffffff", t)
            text(c, lab, 0, 75, 38, "#ffffff")
    if S(141) > -50 and t > S(141):
        msg = "The alarm, because..."
        n = int(clamp((t - S(141)) / 1.6) * len(msg))
        rrect(c, 120, 820, 840, 120, 20, "#ffffff"); c.drawCircle(190, 880, 36, P("#c9b48a"))
        text(c, msg[:n] + ("|" if int(t * 3) % 2 else ""), 250, 895, 42, "#222222", "semi", align="left")
    c.restore()


# ============================================================ #1 DECISION
def turn_around(c, t, d, w, h, S):
    night_ground(c, w, h, t)
    c.save(); stage(c, w, h)
    g = 980
    street_lamp(c, 360, g, t)
    tt = S(149) if S(149) > -50 else 2
    pose = "cane_up" if t > tt + 1.5 else "stand"
    woman(c, 500, g, 0.7, pose, t, "#0b0b0d", rim="#ffd58a", cane=(pose != "cane_up"), bag=False)
    leave = S(153) if S(153) > -50 else 99
    for i in range(2):
        k = ease_out(clamp((t - leave) / 1.5))
        x = 820 + i * 140 + 300 * k
        man(c, x, g, 0.55, "stand", t, "#060607", rim=RED, big=1.1, a=1 - k * 0.6, run=(t if k > 0 else 0))
    if S(147) > -50: kicker(c, t, S(147), S(149) - 0.1, "SHE DID NOT RUN", 540, 150, 72, bar=None)
    if S(149) > -50: kicker(c, t, S(149), S(150) - 0.1, "SQUARE. FEET SET.", 540, 150, 72)
    if S(150) > -50: kicker(c, t, S(150), S(152) - 0.1, "\"NOT TONIGHT, BOYS.\"", 540, 150, 76)
    if S(152) > -50: kicker(c, t, S(152), d + 1, "40 YEARS YOUNGER. 2x HER SIZE.", 540, 150, 52, bar=None)
    if S(153) > -50: kicker(c, t, S(153), d + 1, "THEY WALKED AWAY", 540, 270, 72)
    c.restore()


def rehearse(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#141016")
    c.save(); stage(c, w, h)
    if t < (S(161) if S(161) > -50 else 2) - 0.1:
        k = pop(t, S(159) if S(159) > -50 else 0.3)
        with xf(c, 540, 460, s=k):
            text(c, "FREEZING", 0, 0, 150, XRAY, shadow=0.6)
            for i in range(10):
                ang = i / 10 * math.tau
                line(c, math.cos(ang) * 280, math.sin(ang) * 120 - 50, math.cos(ang) * 340, math.sin(ang) * 150 - 50, XRAY, 6, 0.6)
        if S(160) > -50: kicker(c, t, S(160), d + 1, "DECIDE NOW", 540, 800, 80)
    else:
        steps = [(162, "HANDS UP"), (162, "STEP BACK"), (162, "\"BACK UP!\"")]
        for i, (si, s) in enumerate(steps):
            t0 = S(si) + i * 1.3 if S(si) > -50 else 1 + i
            k = pop(t, t0)
            if k <= 0: continue
            with xf(c, 200 + i * 340, 300, s=k):
                c.drawCircle(0, 0, 120, P("#221b15")); c.drawCircle(0, 0, 120, P(GOLD, 6))
                text(c, str(i + 1), 0, 40, 120, GOLD)
                text(c, s, 0, 190, 44, "#ffffff")
        if S(164) > -50:
            kicker(c, t, S(164), d + 1, "GOAL: HIS HANDS OPEN", 540, 700, 66)
        if S(165) > -50:
            kicker(c, t, S(165), d + 1, "1 STRIKE → PEOPLE + LIGHT", 540, 850, 62, bar=GREEN, color="#06140a")
    c.restore()


def law2(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#10131a")
    c.save(); stage(c, w, h)
    tilt = 8 * math.sin(t * 1.2)
    line(c, 200, 140, 200, 520, GOLD, 10); rect(c, 130, 520, 140, 16, GOLD)
    with xf(c, 200, 160, rot=tilt):
        line(c, -130, 0, 130, 0, GOLD, 8)
        for sx in (-1, 1):
            line(c, sx * 130, 0, sx * 100, 140, GOLD, 3); line(c, sx * 130, 0, sx * 160, 140, GOLD, 3)
            with xf(c, sx * 130, 140, rot=-tilt):
                c.drawPath(poly([(-60, 0), (60, 0), (40, 30), (-40, 30)]), P(GOLD))
    text(c, "NOT LEGAL ADVICE", 200, 620, 30, DIM)
    items = [(171, "READ YOUR STATE'S RULES"), (172, "FORCE FITS THE DANGER"), (173, "HE STOPS → YOU STOP"), (174, "GET FREE, NOT EVEN"), (175, "YOU CALL POLICE FIRST")]
    for i, (si, s) in enumerate(items):
        t0 = S(si) if S(si) > -50 else 0.5 + i
        k = ease_out(at(t, t0, 0.4))
        if k <= 0: continue
        y = 180 + i * 140
        with xf(c, 420 + (1 - k) * 80, y, alpha=k):
            rrect(c, 0, -52, 640, 96, 16, "#1c2230")
            check_mark(c, 55, -5, 48, GREEN, prog=k)
            text(c, s, 100, 12, 34, "#ffffff", align="left")
    c.restore()


def recap(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#131110")
    c.save(); stage(c, w, h)
    text(c, "TIME · NOISE · EYES", 540, 120, 64, GOLD, shadow=0.6, a=clamp(t * 3))
    rows = [(178, "keys", "KEYS OUT BEFORE THE CAR"), (179, "eye", "HEAD UP, EYES COUNTING"), (180, "light", "BRIGHT LIGHT AT NIGHT"),
            (181, "alarm", "ALARM ON YOUR KEYS"), (182, "space", "KEEP YOUR SPACE"), (183, "voice", "USE YOUR VOICE"), (184, "mind", "DECIDE TODAY")]
    for i, (si, ic, s) in enumerate(rows):
        t0 = S(si) if S(si) > -50 else 0.5 + i * 0.5
        k = ease_out(at(t, t0, 0.35))
        if k <= 0: continue
        y = 220 + i * 118
        col = RED if ic == "mind" else "#ffffff"
        with xf(c, 540 + (1 - k) * 60, y, alpha=k):
            rrect(c, -440, -48, 880, 96, 18, "#1d1a17")
            icon(c, ic, -380, 0, 0.42, GOLD, t)
            text(c, s, -320, 15, 40, col, align="left")
            text(c, str(7 - i), 400, 16, 44, GOLD)
    c.restore()


def homework2(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#1a1611", light=(0.3, 0.1))
    c.save(); stage(c, w, h)
    text(c, "THIS WEEK · 10 MINUTES", 540, 130, 60, GOLD, a=clamp(t * 3))
    items = [(192, "light", "FLASHLIGHT ON NIGHTSTAND"), (193, "keys", "ONE THING, ONE POCKET × 10"), (194, "voice", "SAY \"BACK UP!\" OUT LOUD")]
    for i, (si, ic, s) in enumerate(items):
        t0 = S(si) if S(si) > -50 else 0.5 + i
        k = pop(t, t0)
        if k <= 0: continue
        with xf(c, 540, 300 + i * 220, s=k):
            rrect(c, -460, -85, 920, 170, 24, "#221d17"); rrect(c, -460, -85, 920, 170, 24, GOLD, stroke=4)
            icon(c, ic, -370, 0, 0.6, GOLD, t)
            text(c, s, -280, 16, 44, "#ffffff", align="left")
    if S(196) > -50: kicker(c, t, S(196), d + 1, "LOUDER THAN FEELS POLITE", 540, 1000, 60)
    c.restore()


def end2(c, t, d, w, h, S):
    endcard(c, t, d, w, h, lambda i: S({220: 202, 222: 204, 223: 205}.get(i, i)), nxt=("YAKUZA SECRETS", "FOR WOMEN WHO LIVE ALONE"))


# ============================================================ SHOT LIST
T = title_card
SHOTS = [
    (0, "B", hook, {}),
    (6, "S", easy_target, {}),
    (12, "P", seven, {}),
    (19, "A", None, dict(lower=("REIKO KURODA", "35 YEARS · YAKUZA SPOTTER"), kick=[(22, "MY JOB WAS TO CHOOSE")])),
    (23, "S", chooser, {}),
    (26, "A", None, dict(kick=[(26, "NOW I TEACH YOU")])),
    (29, "B", tne, {}),
    (39, "B", T, dict(num="7", name="YOUR KEYS", jp="鍵", col=GOLD)),
    (41, "S", key_claw, {}),
    (47, "P", keys_ready, {}),
    (56, "B", T, dict(num="6", name="YOUR EYES", jp="目", col=XRAY)),
    (58, "P", garage, {}),
    (65, "S", choices, {}),
    (67, "S", warning_signs, {}),
    (75, "B", T, dict(num="5", name="A BRIGHT LIGHT", jp="光", col=GOLD)),
    (77, "P", porch, {}),
    (84, "S", flashlight, {}),
    (90, "B", T, dict(num="4", name="AN ALARM", jp="音", col=RED)),
    (92, "S", alarm_lot, {}),
    (97, "A", None, dict(kick=[(98, "WHAT WE FEARED")])),
    (99, "S", alarm_spec, {}),
    (107, "B", T, dict(num="3", name="YOUR SPACE", jp="間合", col=GREEN)),
    (109, "S", chalk_line, {}),
    (114, "P", keep_space, {}),
    (120, "A", None, dict(kick=[(121, "EVERY STEP = WITNESSES")])),
    (122, "B", T, dict(num="2", name="YOUR VOICE", jp="声", col=RED)),
    (124, "P", market, {}),
    (131, "S", hands_voice, {}),
    (138, "P", poll7, {}),
    (143, "B", T, dict(num="1", name="THE DECISION", jp="覚悟", col=RED)),
    (145, "A", None, dict(kick=[(145, "WHAT SHE DID")])),
    (147, "B", turn_around, {}),
    (154, "A", None, dict(kick=[(155, "SHE DECIDED EARLY")])),
    (156, "B", quote, dict(lines=("The tool never", "saves you.", "The decision does."), who="REIKO KURODA")),
    (158, "S", rehearse, {}),
    (166, "A", None, dict(kick=[(167, "THIS IS CONTROL")])),
    (169, "P", law2, {}),
    (176, "B", recap, {}),
    (185, "A", None, dict(kick=[(186, "MY ANSWER: THE DECISION"), (189, "SEEN FROM ACROSS THE STREET")])),
    (191, "S", homework2, {}),
    (197, "A", None, dict(kick=[(198, "WHAT'S IN YOUR PURSE?"), (200, "WHERE ARE YOU FROM?")])),
    (201, "P", end2, {}),
]
