"""Flat 2D icon library. Each icon is drawn centred on (0,0) inside roughly a 240px box."""
import math

import skia

from gfx import P, rrect, poly, line, text, xf, drop, sparkle, check_mark, cross_mark, glow, lightbulb, thumbs_up, bell

GREEN = "#2ecc71"
GOLD = "#ffc93c"
RED = "#ff4d5e"
BLUE = "#4cc3ff"
WHITE = "#f4f1ea"
INKC = "#1b1b2f"


def coin(c, t, x=0, y=0, r=90, spin=True):
    k = abs(math.cos(t * 2.2)) if spin else 1.0
    k = max(0.25, k)
    with xf(c, x, y, sx=k, sy=1.0):
        c.drawCircle(0, 6, r, P("#c9961e"))
        c.drawCircle(0, 0, r, P(GOLD))
        c.drawCircle(0, 0, r * 0.78, P("#ffdb6e"))
        text(c, "$", 0, r * 0.38, r * 1.05, "#c9961e")


def cash(c, t):
    for i in range(4):
        with xf(c, -10 + i * 8, 40 - i * 22, rot=-6 + i * 4):
            rrect(c, -130, -60, 260, 120, 14, "#1f8f4e")
            rrect(c, -118, -48, 236, 96, 10, "#2fbf6a")
            c.drawCircle(0, 0, 32, P("#1f8f4e"))
            text(c, "$", 0, 16, 46, "#bff5d3")


def phone(c, t, label=None):
    rrect(c, -95, -170, 190, 340, 30, "#222433")
    rrect(c, -82, -150, 164, 300, 18, "#0e1a2b")
    rrect(c, -30, -162, 60, 8, 4, "#3a3d52")
    # tiny chart on screen
    pts = [(-62, 80), (-35, 55), (-10, 66), (15, 20), (40, 30), (62, -20)]
    pth = skia.Path()
    pth.moveTo(*pts[0])
    for p in pts[1:]:
        pth.lineTo(*p)
    c.drawPath(pth, P(GREEN, 7))
    rrect(c, -62, -120, 124, 18, 9, "#ffffff", 0.25)
    rrect(c, -62, -90, 80, 30, 10, GREEN, 0.9)
    rrect(c, -62, 110, 124, 26, 13, BLUE)


def notebook(c, t):
    rrect(c, -110, -140, 220, 280, 16, "#e6b35a")
    rrect(c, -95, -128, 200, 256, 10, "#fffaf0")
    for i in range(7):
        line(c, -80, -90 + i * 32, 92, -90 + i * 32, "#9fc3e6", 3)
    line(c, -40, -120, -40, 120, "#ff8a8a", 3)
    for i in range(6):
        c.drawCircle(-110, -110 + i * 44, 9, P("#555b70"))
    with xf(c, 70, 60, rot=35):
        rrect(c, -12, -110, 24, 170, 6, GOLD)
        c.drawPath(poly([(-12, 60), (12, 60), (0, 92)]), P("#f1d3a8"))


def pot(c, t):
    for i in range(3):
        ph = t * 1.5 + i
        a = 0.5 * (0.5 + 0.5 * math.sin(ph * 2))
        pth = skia.Path()
        x0 = -50 + i * 50
        pth.moveTo(x0, -70)
        pth.cubicTo(x0 - 20, -100, x0 + 20, -120, x0, -150)
        c.drawPath(pth, P("#ffffff", 8, a))
    rrect(c, -150, -55, 300, 20, 10, "#5b6178")
    c.drawPath(poly([(-130, -40), (130, -40), (115, 95), (-115, 95)]), P("#7c8296"))
    rrect(c, -175, -30, 50, 22, 10, "#5b6178")
    rrect(c, 125, -30, 50, 22, 10, "#5b6178")
    c.drawOval(skia.Rect(-115, -52, 115, -28), P("#d9a066"))
    for i in range(9):
        c.drawCircle(-90 + i * 22, -42 + (i % 2) * 6, 7, P("#3a2a20" if i % 3 else "#fff4dc"))


def house(c, t):
    c.drawPath(poly([(-150, -10), (0, -140), (150, -10)]), P("#e4572e"))
    rrect(c, -115, -20, 230, 150, 6, "#f2e6d0")
    rrect(c, -30, 40, 60, 90, 6, "#8a5a3c")
    rrect(c, -95, 10, 50, 45, 4, BLUE)
    rrect(c, 45, 10, 50, 45, 4, BLUE)
    rrect(c, 70, -120, 30, 60, 3, "#a3402a")


def car(c, t):
    b = 3 * math.sin(t * 12)
    with xf(c, 0, b):
        c.drawPath(poly([(-150, 20), (-120, -30), (-60, -80), (60, -80), (110, -30), (160, -10), (160, 40),
                         (-150, 40)]), P("#3d7dd8"))
        c.drawPath(poly([(-50, -68), (0, -68), (0, -30), (-90, -30)]), P("#bfe6ff"))
        c.drawPath(poly([(12, -68), (55, -68), (92, -30), (12, -30)]), P("#bfe6ff"))
        rrect(c, 140, 0, 22, 14, 5, GOLD)
    for wx in (-90, 95):
        c.drawCircle(wx, 45, 36, P("#20222e"))
        c.drawCircle(wx, 45, 15, P("#aab0c0"))


def chart(c, t, prog=1.0):
    rrect(c, -150, -130, 300, 260, 20, "#0f2236")
    for i in range(4):
        line(c, -120, 90 - i * 55, 120, 90 - i * 55, "#ffffff", 2, 0.12)
    for i in range(5):
        h = (30 + i * 35) * min(1, prog * 1.4)
        rrect(c, -110 + i * 46, 100 - h, 30, h, 6, GREEN if i == 4 else "#3aa0ff")
    pth = skia.Path()
    pth.moveTo(-110, 60)
    pth.lineTo(-40, 10)
    pth.lineTo(10, 30)
    pth.lineTo(110, -90)
    c.drawPath(pth, P(GOLD, 8))
    c.drawPath(poly([(110, -90), (80, -88), (106, -62)]), P(GOLD))


def piggy(c, t):
    c.drawOval(skia.Rect(-140, -90, 130, 100), P("#ff9fb8"))
    c.drawCircle(120, 0, 42, P("#ff9fb8"))
    c.drawOval(skia.Rect(130, -16, 175, 22), P("#ff7aa0"))
    c.drawCircle(145, 2, 5, P("#b04064"))
    c.drawCircle(160, 2, 5, P("#b04064"))
    c.drawCircle(90, -25, 8, P(INKC))
    c.drawPath(poly([(40, -80), (70, -130), (90, -70)]), P("#ff7aa0"))
    for lx in (-100, -50, 30, 80):
        rrect(c, lx, 80, 30, 45, 8, "#ff7aa0")
    rrect(c, -40, -96, 70, 12, 6, "#b04064")
    y = -170 + ((t * 120) % 80)
    coin(c, t, -5, y, 34, spin=False)


def calendar(c, t):
    rrect(c, -130, -120, 260, 250, 20, WHITE)
    rrect(c, -130, -120, 260, 70, 20, RED)
    c.drawRect(skia.Rect(-130, -70, 130, -50), P(RED))
    for i in range(3):
        for j in range(4):
            col = GREEN if (i * 4 + j) in (2, 9) else "#d6d2c8"
            rrect(c, -105 + j * 55, -25 + i * 50, 40, 36, 8, col)
    for x in (-70, 70):
        rrect(c, x - 9, -140, 18, 45, 9, "#555b70")


def card_icon(c, t):
    with xf(c, 0, 0, rot=-8):
        rrect(c, -160, -100, 320, 200, 22, "#6c5ce7")
        rrect(c, -160, -60, 320, 36, 0, "#2d2a4a")
        rrect(c, -125, 5, 60, 44, 8, GOLD)
        for i in range(4):
            rrect(c, -40 + i * 45, 60, 36, 12, 6, "#ffffff", 0.6)


def cart(c, t):
    line(c, -160, -110, -120, -110, "#dfe6f0", 14)
    c.drawPath(poly([(-120, -110), (150, -80), (125, 40), (-95, 40)]), P("#dfe6f0", 14))
    for i, col in enumerate(["#ff7a59", GREEN, GOLD]):
        rrect(c, -80 + i * 65, -95 + (i % 2) * 20, 55, 90 - (i % 2) * 20, 10, col)
    c.drawCircle(-80, 85, 22, P("#dfe6f0"))
    c.drawCircle(100, 85, 22, P("#dfe6f0"))


def tv(c, t):
    rrect(c, -170, -115, 340, 210, 16, "#2b2e3d")
    rrect(c, -152, -98, 304, 176, 8, "#3aa0ff")
    fl = 0.15 + 0.1 * math.sin(t * 9)
    rrect(c, -152, -98, 304, 176, 8, "#ffffff", fl)
    line(c, -40, 95, -70, 140, "#2b2e3d", 12)
    line(c, 40, 95, 70, 140, "#2b2e3d", 12)


def couch(c, t):
    rrect(c, -170, -90, 340, 120, 30, "#8a5aa8")
    rrect(c, -200, -30, 60, 120, 24, "#74468f")
    rrect(c, 140, -30, 60, 120, 24, "#74468f")
    rrect(c, -150, 10, 145, 70, 14, "#9d6dbb")
    rrect(c, 5, 10, 145, 70, 14, "#9d6dbb")
    c.drawPath(poly([(-110, 25), (-85, 50), (-100, 55), (-70, 75)], close=False), P("#3a1f4c", 5))
    rrect(c, -180, 90, 20, 30, 4, "#4a2d5c")
    rrect(c, 160, 90, 20, 30, 4, "#4a2d5c")


def cup(c, t):
    for i in range(2):
        a = 0.5 + 0.3 * math.sin(t * 3 + i)
        pth = skia.Path()
        pth.moveTo(-25 + i * 45, -70)
        pth.cubicTo(-45 + i * 45, -100, -5 + i * 45, -110, -25 + i * 45, -140)
        c.drawPath(pth, P("#ffffff", 8, a))
    c.drawPath(poly([(-90, -50), (90, -50), (70, 110), (-70, 110)]), P(WHITE))
    c.drawCircle(105, 20, 40, P(WHITE, 16))
    rrect(c, -90, -10, 180, 40, 0, "#c0703a")


def gas(c, t):
    rrect(c, -90, -130, 160, 260, 18, RED)
    rrect(c, -65, -100, 110, 80, 10, "#ffe2e2")
    rrect(c, -110, 120, 200, 22, 8, "#555b70")
    pth = skia.Path()
    pth.moveTo(70, -60)
    pth.cubicTo(140, -60, 130, 40, 110, 70)
    c.drawPath(pth, P("#2b2e3d", 12))
    drop(c, 40, 50, 22, "#ffb02e")


def wrench(c, t):
    with xf(c, 0, 0, rot=-40 + 10 * math.sin(t * 4)):
        rrect(c, -22, -40, 44, 200, 20, "#aab0c0")
        c.drawCircle(0, -70, 60, P("#aab0c0"))
        rrect(c, -22, -140, 44, 70, 6, "#00000000")
        c.drawPath(poly([(-20, -135), (20, -135), (20, -80), (-20, -80)]), P("#16243a"))


def gradcap(c, t):
    c.drawPath(poly([(-180, -20), (0, -100), (180, -20), (0, 60)]), P("#2b2e3d"))
    c.drawPath(poly([(-110, 10), (110, 10), (100, 90), (-100, 90)]), P("#22252f"))
    line(c, 150, -20, 150, 70, GOLD, 6)
    c.drawCircle(150, 78, 12, P(GOLD))


def briefcase(c, t):
    rrect(c, -50, -125, 100, 50, 14, "#5a3c28", stroke=14)
    rrect(c, -160, -90, 320, 200, 22, "#8a5a3c")
    rrect(c, -160, -20, 320, 14, 0, "#6e4630")
    rrect(c, -22, -35, 44, 40, 6, GOLD)


def clock(c, t):
    c.drawCircle(0, 0, 130, P(WHITE))
    c.drawCircle(0, 0, 130, P("#2b2e3d", 14))
    for i in range(12):
        a = i / 12 * math.tau
        line(c, math.sin(a) * 100, -math.cos(a) * 100, math.sin(a) * 115, -math.cos(a) * 115, "#2b2e3d", 6)
    a1 = t * 2
    a2 = t * 0.3
    line(c, 0, 0, math.sin(a1) * 95, -math.cos(a1) * 95, RED, 7)
    line(c, 0, 0, math.sin(a2) * 65, -math.cos(a2) * 65, "#2b2e3d", 12)
    c.drawCircle(0, 0, 12, P("#2b2e3d"))


def lock(c, t):
    rrect(c, -70, -150, 140, 160, 70, "#aab0c0", stroke=26)
    rrect(c, -120, -60, 240, 190, 24, GOLD)
    c.drawCircle(0, 20, 22, P("#8a6512"))
    rrect(c, -9, 25, 18, 50, 6, "#8a6512")


def shield(c, t):
    c.drawPath(poly([(0, -150), (130, -100), (115, 40), (0, 150), (-115, 40), (-130, -100)]), P("#3aa0ff"))
    c.drawPath(poly([(0, -120), (100, -82), (88, 30), (0, 118), (-88, 30), (-100, -82)]), P("#1e6fd0"))
    check_mark(c, 0, 0, 120, "#ffffff")


def target(c, t):
    for i, col in enumerate([RED, WHITE, RED, WHITE, RED]):
        c.drawCircle(0, 0, 140 - i * 28, P(col))
    k = min(1.0, (t % 3.0) * 2)
    with xf(c, 160 - 160 * k, -160 + 160 * k, rot=45):
        line(c, 0, 0, 0, 150, "#2b2e3d", 10)
        c.drawPath(poly([(-14, 150), (14, 150), (0, 175)]), P("#2b2e3d"))


def gift(c, t):
    rrect(c, -130, -40, 260, 170, 12, RED)
    rrect(c, -145, -80, 290, 55, 12, "#ff6b7a")
    rrect(c, -20, -80, 40, 210, 0, GOLD)
    c.drawOval(skia.Rect(-80, -140, -5, -80), P(GOLD, 14))
    c.drawOval(skia.Rect(5, -140, 80, -80), P(GOLD, 14))


def people(c, t):
    for i, (x, col) in enumerate([(-100, "#ff7a59"), (0, "#3aa0ff"), (100, GREEN)]):
        y = 3 * math.sin(t * 3 + i)
        c.drawCircle(x, -60 + y, 42, P("#e0b089"))
        rrect(c, x - 55, -10 + y, 110, 130, 50, col)


def plane(c, t):
    with xf(c, 0, 0, rot=-20):
        rrect(c, -160, -22, 320, 44, 22, WHITE)
        c.drawPath(poly([(-20, -10), (60, -10), (-60, -130), (-90, -130)]), P("#dfe6f0"))
        c.drawPath(poly([(-20, 10), (60, 10), (-60, 130), (-90, 130)]), P("#dfe6f0"))
        c.drawPath(poly([(-150, -10), (-110, -10), (-140, -70), (-165, -70)]), P(RED))


def scissors(c, t):
    o = 12 * math.sin(t * 8)
    with xf(c, 0, 0, rot=-o):
        rrect(c, -10, -150, 22, 170, 10, "#aab0c0")
        c.drawCircle(0, 70, 40, P(RED, 16))
    with xf(c, 0, 0, rot=o):
        rrect(c, -12, -150, 22, 170, 10, "#c9ced9")
        c.drawCircle(0, 70, 40, P(RED, 16))


def mountain(c, t):
    c.drawPath(poly([(-180, 120), (-60, -90), (40, 50), (100, -20), (190, 120)]), P("#4f8a6b"))
    c.drawPath(poly([(-60, -90), (-30, -40), (-90, -40)]), P(WHITE))
    c.drawCircle(120, -100, 34, P(GOLD))


def basket(c, t):
    b = abs(math.sin(t * 4)) * 60
    c.drawCircle(0, -40 - b, 70, P("#ff8c2e"))
    line(c, -70, -40 - b, 70, -40 - b, "#8a3c10", 5)
    line(c, 0, -110 - b, 0, 30 - b, "#8a3c10", 5)


def warning(c, t):
    c.drawPath(poly([(0, -150), (160, 120), (-160, 120)]), P(GOLD))
    rrect(c, -14, -70, 28, 110, 12, INKC)
    c.drawCircle(0, 80, 16, P(INKC))


def bolt(c, t):
    c.drawPath(poly([(30, -160), (-90, 20), (-10, 20), (-40, 160), (90, -30), (10, -30)]), P(GOLD))


def heart(c, t):
    k = 1 + 0.06 * abs(math.sin(t * 5))
    with xf(c, 0, 0, s=k):
        pth = skia.Path()
        pth.moveTo(0, 120)
        pth.cubicTo(-200, -20, -90, -170, 0, -60)
        pth.cubicTo(90, -170, 200, -20, 0, 120)
        c.drawPath(pth, P(RED))


def book(c, t):
    c.drawPath(poly([(-170, -100), (-10, -80), (-10, 120), (-170, 100)]), P("#3aa0ff"))
    c.drawPath(poly([(170, -100), (10, -80), (10, 120), (170, 100)]), P("#1e6fd0"))
    for i in range(4):
        line(c, -150, -60 + i * 35, -30, -45 + i * 35, "#ffffff", 4, 0.6)


def debt(c, t):
    rrect(c, -120, -150, 240, 300, 14, WHITE)
    text(c, "DEBT", 0, -80, 54, RED)
    for i in range(4):
        line(c, -90, -30 + i * 40, 90, -30 + i * 40, "#c8c3b8", 6)
    with xf(c, 70, 100, rot=-15):
        rrect(c, -80, -32, 160, 64, 10, RED, stroke=8)
        text(c, "OWED", 0, 16, 40, RED)


def bulb(c, t):
    lightbulb(c, 0, 0, 1.6, on=1.0, t=t)


def thumbs(c, t):
    thumbs_up(c, 0, 0, 1.8)


def bellicon(c, t):
    bell(c, 0, 0, 1.6)


def checkicon(c, t):
    c.drawCircle(0, 0, 130, P(GREEN))
    check_mark(c, 0, 0, 150, "#ffffff", prog=min(1, (t % 4) * 2))


def crossicon(c, t):
    c.drawCircle(0, 0, 130, P(RED))
    cross_mark(c, 0, 0, 120, "#ffffff")


ICONS = dict(coin=coin, cash=cash, phone=phone, notebook=notebook, pot=pot, house=house, car=car, chart=chart,
             piggy=piggy, calendar=calendar, card=card_icon, cart=cart, tv=tv, couch=couch, cup=cup, gas=gas,
             wrench=wrench, gradcap=gradcap, briefcase=briefcase, clock=clock, lock=lock, shield=shield,
             target=target, gift=gift, people=people, plane=plane, scissors=scissors, mountain=mountain,
             basket=basket, warning=warning, bolt=bolt, heart=heart, book=book, debt=debt, bulb=bulb,
             thumbs=thumbs, bell=bellicon, check=checkicon, cross=crossicon)

# keyword → icon. First match in a sentence wins (ordered by specificity).
KEYWORDS = [
    (("couch", "cushion", "blanket", "sofa"), "couch"),
    (("tv", "television", "netflix", "streaming"), "tv"),
    (("windshield", "car", "civic", "honda", "mechanic", "tires", "oil", "miles", "drive"), "car"),
    (("rice", "beans", "chili", "chicken", "cook", "meal", "groceries", "grocery", "pot", "food", "dinner", "lunch",
      "vegetables", "protein", "eat"), "pot"),
    (("brokerage", "app", "phone", "balance"), "phone"),
    (("notebook", "track", "tracked", "columns", "paper", "wrote", "write"), "notebook"),
    (("rent", "studio", "apartment", "house", "home", "neighborhood", "roommate", "landlord", "lease"), "house"),
    (("compound", "compounding", "index", "fund", "invest", "invested", "investing", "market", "stock", "401k",
      "roth", "ira", "portfolio", "%", "percent", "growth", "returns"), "chart"),
    (("save", "saved", "saving", "savings", "emergency", "high yield", "account"), "piggy"),
    (("month", "monthly", "week", "sunday", "day", "every", "30th", "15th", "calendar", "year", "years"), "calendar"),
    (("credit", "card", "score", "interest", "apr"), "card"),
    (("subscription", "subscriptions", "cancel", "cut", "cancelled"), "scissors"),
    (("vending", "sparkling", "coffee", "water", "drink", "starbucks"), "cup"),
    (("gas", "fuel"), "gas"),
    (("college", "tuition", "graduation", "student", "school", "degree"), "gradcap"),
    (("job", "career", "salary", "raise", "boss", "company", "employer", "work", "promotion", "negotiate"),
     "briefcase"),
    (("debt", "loan", "owed", "owe", "broke"), "debt"),
    (("time", "hours", "minutes", "night", "clock", "automat", "automated", "automation"), "clock"),
    (("insurance", "protect", "safe", "risk", "emergency"), "shield"),
    (("goal", "goals", "target", "plan"), "target"),
    (("gift", "birthday", "christmas", "holiday"), "gift"),
    (("friends", "parents", "people", "family", "everyone", "nobody", "coworkers"), "people"),
    (("trip", "travel", "vacation", "flight", "road"), "plane"),
    (("mountains", "hiked", "hike", "outdoors"), "mountain"),
    (("basketball", "gym", "sport", "exercise"), "basket"),
    (("mistake", "lose", "problem", "problems", "wrong", "trap", "never"), "warning"),
    (("free", "match", "bonus"), "gift"),
    (("book", "books", "library", "learn", "read"), "book"),
    (("shopping", "buy", "bought", "purchase", "cart", "amazon", "store"), "cart"),
    (("lock", "locked", "door", "security"), "lock"),
    (("idea", "think", "thinking", "realize", "learned", "lesson", "secret"), "bulb"),
    (("love", "happy", "grateful", "life", "full", "enjoy"), "heart"),
    (("money", "dollar", "dollars", "cash", "pay", "paid", "cost", "spend", "spending", "price", "$"), "cash"),
]


def pick_icon(sentence):
    low = " " + sentence.lower().replace(",", " ").replace(".", " ") + " "
    for keys, name in KEYWORDS:
        for k in keys:
            if (" " + k + " ") in low or (k in ("%", "$", "automat") and k in low):
                return name
    return None
