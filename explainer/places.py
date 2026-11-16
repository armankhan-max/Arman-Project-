"""Real-world sets (street, shop, bank, kitchen, restaurant, library, park, office) and a crowd of extra people."""
import math
import random

import skia

import gfx
from gfx import W, H, P, rrect, poly, line, text, linear, radial, fill_shader, draw_char, walk_pose

# extra adults for crowds
gfx.CHARS.update({
    "p1": dict(skin="#e0b089", hair="#5a3a22", shirt="#e4572e", pants="#2f3e5c", shoe="#222222", cap=None,
               head=48, torso=112, arm=(58, 54), leg=(68, 66), width=40),
    "p2": dict(skin="#7a4a2e", hair="#111111", shirt="#6c5ce7", pants="#3a3a46", shoe="#eeeeee", cap=None,
               head=50, torso=120, arm=(60, 56), leg=(72, 68), width=42),
    "p3": dict(skin="#f1c7a0", hair="#c98a3a", shirt="#ffc93c", pants="#1f6f8b", shoe="#7a3e1d", cap=None,
               head=47, torso=108, arm=(56, 52), leg=(66, 64), width=38),
    "p4": dict(skin="#a86b48", hair="#2a1b14", shirt="#2ecc71", pants="#4a3a2a", shoe="#333333", cap="#3aa0ff",
               head=49, torso=116, arm=(58, 54), leg=(70, 66), width=41),
    "p5": dict(skin="#c48c64", hair="#7a7a7a", shirt="#ff7aa8", pants="#54426e", shoe="#222222", cap=None,
               head=48, torso=110, arm=(58, 54), leg=(66, 64), width=40),
})
CROWD = ["p1", "p2", "p3", "p4", "p5", "ines", "gran"]

SW = W + 240  # sets are wider than the frame so the camera can pan
FLOOR = 900


def _sky(c, top, bot):
    fill_shader(c, skia.Rect(0, 0, SW, H), linear(0, 0, 0, H, [top, bot]))


def _building(c, x, w, h, col, win="#ffe9a8", rnd=None):
    rrect(c, x, FLOOR - 120 - h, w, h + 120, 6, col)
    for yy in range(int(FLOOR - 120 - h + 30), FLOOR - 160, 70):
        for xx in range(int(x + 20), int(x + w - 40), 60):
            on = rnd.random() < 0.6 if rnd else True
            rrect(c, xx, yy, 34, 44, 4, win if on else "#2b3550", 0.9)


def _shopfront(c, x, w, col, sign, awning):
    rrect(c, x, FLOOR - 330, w, 330, 6, col)
    for i in range(int(w // 60)):
        c.drawRect(skia.Rect(x + i * 60, FLOOR - 300, x + i * 60 + 30, FLOOR - 250), P(awning))
        c.drawRect(skia.Rect(x + i * 60 + 30, FLOOR - 300, x + i * 60 + 60, FLOOR - 250), P("#ffffff"))
    rrect(c, x + 20, FLOOR - 390, w - 40, 70, 10, "#1b1b2f")
    text(c, sign, x + w / 2, FLOOR - 340, 44, "#ffe08a")
    rrect(c, x + 30, FLOOR - 230, w * 0.55, 160, 6, "#bfe6ff")
    rrect(c, x + 30, FLOOR - 230, w * 0.55, 160, 6, "#ffffff", 0.0)
    for i in range(4):
        rrect(c, x + 45 + i * (w * 0.55 - 30) / 4, FLOOR - 120, (w * 0.55 - 60) / 4, 40, 6,
              ["#ff7a59", "#2ecc71", "#ffc93c", "#3aa0ff"][i])
    rrect(c, x + w * 0.66, FLOOR - 240, w * 0.26, 240, 6, "#5a3c28")


def _floor_outdoor(c):
    c.drawRect(skia.Rect(0, FLOOR - 20, SW, FLOOR + 40), P("#b9b2a5"))
    c.drawRect(skia.Rect(0, FLOOR + 40, SW, H), P("#3d4250"))
    for x in range(0, SW, 220):
        rrect(c, x + 40, FLOOR + 120, 110, 14, 7, "#f2f2f2", 0.8)
    for x in range(0, SW, 140):
        line(c, x, FLOOR - 20, x, FLOOR + 40, "#9a9386", 3)


def street(c):
    _sky(c, "#7cc6ff", "#d9f0ff")
    rnd = random.Random(2)
    for i, (x, w, h, col) in enumerate([(0, 300, 420, "#c9a98a"), (280, 260, 520, "#9fb4c9"),
                                         (1500, 280, 480, "#b48a7a"), (1760, 400, 380, "#8fa38a")]):
        _building(c, x, w, h, col, rnd=rnd)
    _shopfront(c, 560, 420, "#e8d4b0", "MARKET", "#e4572e")
    _shopfront(c, 1000, 480, "#d4e2f0", "CAFE", "#2ecc71")
    for x in (530, 1490):
        line(c, x, FLOOR - 20, x, FLOOR - 330, "#2b2e3d", 10)
        c.drawCircle(x, FLOOR - 340, 18, P("#ffe08a"))
    _floor_outdoor(c)


def shop(c):
    c.drawRect(skia.Rect(0, 0, SW, H), P("#f4efe6"))
    c.drawRect(skia.Rect(0, 0, SW, 140), P("#e4572e"))
    text(c, "SUPER  MART", SW / 2, 100, 70, "#ffffff")
    for sx in (60, 560, 1460, 1860):
        rrect(c, sx, 220, 360, 620, 10, "#c9b79c")
        for k in range(5):
            y = 260 + k * 115
            c.drawRect(skia.Rect(sx + 10, y + 80, sx + 350, y + 92), P("#8a6e4e"))
            r = random.Random(sx + k)
            for j in range(7):
                col = r.choice(["#ff7a59", "#2ecc71", "#ffc93c", "#3aa0ff", "#a66cff", "#ff4f86"])
                hh = r.uniform(40, 75)
                rrect(c, sx + 18 + j * 47, y + 80 - hh, 38, hh, 6, col)
    rrect(c, 960, 640, 440, 200, 12, "#3a3d52")
    rrect(c, 1010, 560, 120, 80, 8, "#1b1b2f")
    text(c, "$ 0.00", 1070, 612, 26, "#2ecc71")
    c.drawRect(skia.Rect(0, FLOOR - 20, SW, H), P("#d8cbb6"))
    for x in range(0, SW, 120):
        line(c, x, FLOOR - 20, x - 80, H, "#c4b59c", 3)


def bank(c):
    _sky(c, "#8fd0ff", "#e6f4ff")
    _building(c, 0, 260, 380, "#a7b3c4", rnd=random.Random(4))
    _building(c, 1880, 300, 420, "#b9a28a", rnd=random.Random(5))
    x0, x1 = 420, 1720
    c.drawPath(poly([(x0 - 40, 300), ((x0 + x1) / 2, 140), (x1 + 40, 300)]), P("#e9e3d6"))
    rrect(c, x0 - 40, 300, x1 - x0 + 80, 50, 4, "#d8d0bf")
    text(c, "CITY  BANK", (x0 + x1) / 2, 290, 64, "#2b3550")
    for i in range(7):
        x = x0 + 40 + i * (x1 - x0 - 80) / 6
        rrect(c, x - 32, 350, 64, 480, 6, "#f4efe6")
        line(c, x - 12, 360, x - 12, 820, "#d8d0bf", 4)
        line(c, x + 12, 360, x + 12, 820, "#d8d0bf", 4)
    rrect(c, (x0 + x1) / 2 - 90, 600, 180, 230, 8, "#5a3c28")
    rrect(c, (x0 + x1) / 2 - 200, 470, 400, 100, 12, "#2b3550")
    text(c, "CITY BANK", (x0 + x1) / 2, 540, 60, "#ffe08a")
    for k in range(4):
        rrect(c, x0 - 80 + k * 20, 830 + k * 16, x1 - x0 + 160 - k * 40, 18, 2, "#cfc7b6")
    _floor_outdoor(c)


def kitchen(c):
    c.drawRect(skia.Rect(0, 0, SW, H), P("#fdf3e3"))
    for x in range(0, SW, 60):
        for y in range(380, 640, 60):
            rrect(c, x + 2, y + 2, 56, 56, 4, "#e8f4f0")
    for x in (80, 420, 1500, 1840):
        rrect(c, x, 100, 300, 220, 10, "#c97b4a")
        line(c, x + 150, 110, x + 150, 310, "#a85f34", 4)
    rrect(c, 0, 640, SW, 60, 6, "#7c8296")
    rrect(c, 0, 700, SW, 200, 0, "#c97b4a")
    rrect(c, 900, 560, 340, 80, 8, "#2b2e3d")
    for x in (960, 1180):
        c.drawCircle(x, 600, 26, P("#ff7a59", a=0.5))
    rrect(c, 1700, 380, 240, 160, 10, "#bfe6ff")
    c.drawRect(skia.Rect(0, FLOOR - 20, SW, H), P("#d9b98c"))


def restaurant(c):
    c.drawRect(skia.Rect(0, 0, SW, H), P("#3b2430"))
    for x in range(0, SW, 160):
        c.drawRect(skia.Rect(x, 0, x + 80, 640), P("#432a37"))
    for x in (300, 900, 1500, 2000):
        line(c, x, 0, x, 160, "#1b1b2f", 4)
        c.drawPath(poly([(x - 50, 200), (x + 50, 200), (x + 25, 160), (x - 25, 160)]), P("#ffc93c"))
        fill_shader(c, skia.Rect(x - 260, 160, x + 260, 700), radial(x, 220, 400, [("#ffc93c", 0.28),
                                                                                    ("#ffc93c", 0)]))
    for x in (380, 1100, 1800):
        rrect(c, x - 200, 700, 400, 30, 8, "#f4efe6")
        rrect(c, x - 20, 730, 40, 170, 4, "#2b2e3d")
        for k in (-120, 0, 120):
            c.drawCircle(x + k, 690, 30, P("#ffffff"))
            c.drawCircle(x + k, 690, 18, P("#ff7a59"))
    c.drawRect(skia.Rect(0, FLOOR - 20, SW, H), P("#5a3a2a"))


def library(c):
    c.drawRect(skia.Rect(0, 0, SW, H), P("#efe2c8"))
    for sx in range(0, SW, 440):
        rrect(c, sx + 20, 80, 400, 800, 8, "#7a4e2c")
        for k in range(6):
            y = 100 + k * 128
            r = random.Random(sx * 7 + k)
            x = sx + 34
            while x < sx + 400:
                w = r.uniform(18, 34)
                h = r.uniform(80, 112)
                rrect(c, x, y + 118 - h, w, h, 3, r.choice(["#e4572e", "#3aa0ff", "#2ecc71", "#ffc93c", "#a66cff",
                                                            "#1f6f8b", "#ff7aa8"]))
                x += w + 3
            c.drawRect(skia.Rect(sx + 20, y + 118, sx + 420, y + 128), P("#5a3a20"))
    rrect(c, 760, 30, 560, 70, 10, "#2b3550")
    text(c, "PUBLIC LIBRARY", 1040, 80, 44, "#ffe08a")
    c.drawRect(skia.Rect(0, FLOOR - 20, SW, H), P("#a8744a"))


def park(c):
    _sky(c, "#6ec3ff", "#d8f3ff")
    c.drawCircle(1700, 180, 80, P("#ffe08a"))
    for x, h in ((0, 260), (500, 200), (1100, 280), (1600, 220)):
        c.drawPath(poly([(x - 200, FLOOR), (x + 300, FLOOR - h - 200), (x + 800, FLOOR)]), P("#7fbf8a"))
    c.drawRect(skia.Rect(0, FLOOR - 140, SW, H), P("#6fbf5a"))
    for x in (120, 520, 1580, 2000):
        rrect(c, x - 18, FLOOR - 320, 36, 220, 8, "#7a4e2c")
        c.drawCircle(x, FLOOR - 360, 110, P("#3f9a4a"))
        c.drawCircle(x - 60, FLOOR - 310, 70, P("#4fae58"))
        c.drawCircle(x + 60, FLOOR - 310, 70, P("#4fae58"))
    rrect(c, 1060, FLOOR - 360, 16, 360, 4, "#e4e4e4")
    rrect(c, 980, FLOOR - 400, 170, 110, 6, "#ffffff")
    c.drawCircle(1065, FLOOR - 330, 34, P("#e4572e", 6))
    c.drawPath(poly([(0, FLOOR + 30), (SW, FLOOR - 10), (SW, FLOOR + 60), (0, FLOOR + 90)]), P("#d9c39a"))


def office(c):
    c.drawRect(skia.Rect(0, 0, SW, H), P("#e8edf3"))
    for x in range(100, SW, 520):
        rrect(c, x, 90, 400, 380, 8, "#9fd3ff")
        for k in range(4):
            rrect(c, x + 30 + k * 90, 260 - k * 30, 60, 210 + k * 30, 2, "#7aa8d0")
        line(c, x + 200, 90, x + 200, 470, "#ffffff", 8)
    for x in (300, 1000, 1700):
        rrect(c, x - 220, 690, 440, 30, 6, "#c9b79c")
        rrect(c, x - 200, 720, 20, 180, 4, "#8a6e4e")
        rrect(c, x + 180, 720, 20, 180, 4, "#8a6e4e")
        rrect(c, x - 100, 560, 200, 130, 8, "#2b2e3d")
        rrect(c, x - 88, 572, 176, 100, 4, "#3aa0ff")
    c.drawRect(skia.Rect(0, FLOOR - 20, SW, H), P("#9aa6b8"))


SETS = dict(street=street, shop=shop, bank=bank, kitchen=kitchen, restaurant=restaurant, library=library, park=park,
            office=office)
OUTDOOR = ("street", "park", "bank")
LABEL = dict(street="DOWNTOWN", shop="THE STORE", bank="THE BANK", kitchen="MY KITCHEN", restaurant="DINNER",
             library="THE LIBRARY", park="THE PARK", office="THE OFFICE")

PLACE_KEYS = [
    (("library", "books", "book"), "library"),
    (("dinner", "ate out", "delivery", "cocktails", "entree", "appetizers", "dish", "table", "birthday", "restaurant"),
     "restaurant"),
    (("cook", "cooked", "rice", "beans", "chili", "chicken", "meal", "meals", "coffee", "pot", "kitchen", "stove",
      "vegetables", "protein"), "kitchen"),
    (("grocer", "store", "shopping", "secondhand", "marketplace", "purchase", "bought", "buy", "sale", "vending",
      "gas station", "cash only", "target", "goodwill", "cart", "amazon", "retail", "shop"), "shop"),
    (("bank", "account", "savings", "high yield", "401k", "roth", "ira", "brokerage", "balance", "invest",
      "fund", "index", "emergency", "debt", "loan", "checking", "windfall", "budget"), "bank"),
    (("job", "career", "company", "employer", "salary", "raise", "coworker", "negotiat", "bill", "work", "boss",
      "insurance", "match", "paycheck"), "office"),
    (("hike", "hiked", "basketball", "gym", "park", "free entertainment", "mountains", "trip", "outside", "walk",
      "run", "fun"), "park"),
    (("car", "civic", "honda", "mechanic", "drive", "tires", "oil", "miles", "neighborhood", "studio", "rent",
      "apartment", "friends", "people", "everyone", "nobody"), "street"),
]


def pick_place(txt):
    low = txt.lower()
    for keys, name in PLACE_KEYS:
        for k in keys:
            if k in low:
                return name
    return None


_cache = {}


def draw_set(c, name, t, pan):
    if name not in _cache:
        s = skia.Surface(SW, H)
        SETS[name](s.getCanvas())
        _cache[name] = s.makeImageSnapshot()
    c.drawImage(_cache[name], -120 - pan, 0)
    if name in OUTDOOR:
        r = random.Random(9)
        for i in range(3):  # drifting clouds
            x = (r.uniform(0, W) + t * r.uniform(10, 25)) % (W + 400) - 200
            y = r.uniform(60, 220)
            for k, dx in enumerate((-60, 0, 60)):
                c.drawCircle(x + dx, y + (10 if k != 1 else -10), 50 if k == 1 else 38, P("#ffffff", a=0.85))


def crowd(c, t, side, n, seed, expr_mode="listen"):
    """n people standing on the opposite side of the main character, listening/reacting."""
    r = random.Random(seed)
    names = r.sample(CROWD, n)
    base = W - 420 if side == 1 else 420
    for i, who in enumerate(names):
        x = base + (i - (n - 1) / 2) * 190 * (1 if side == 1 else -1)
        y = FLOOR + 10 + (i % 2) * 18
        expr = ["happy", "neutral", "shock", "happy", "laugh"][(i + seed) % 5]
        pose = ["stand", "hold", "stand", "give_l", "stand"][(i + seed) % 5]
        nod = 3 * math.sin(t * 2.5 + i)
        draw_char(c, x, y - 130, who, pose, expr, t + i, s=1.15, bob=nod, flip=(side == 1),
                  look=(-side * 0.7, 0))


def walker(c, t, x, y, who, s, flip, expr="happy", t0=0.0):
    pose = walk_pose(t - t0, 7.0, 26)
    bob = -6 * abs(math.sin((t - t0) * 7.0))
    draw_char(c, x, y, who, pose, expr, t, s=s, bob=bob, flip=flip)
