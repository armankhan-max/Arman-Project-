"""Timeline for 'Why You'd Never Want To Meet A Giant Pacific Octopus'.

Each shot is a function registered with @shot(start_time). A shot runs until the next shot
starts. All times come from the word-level transcript, so visuals land on the spoken word.
"""
import json
import math
import os
import random
import re

import skia

from ofx import *  # noqa: F401,F403
from ofx import (W, H, C, P, xf, rrect, poly, line, text, linear, radial, fill_shader, glow, sparkle, check_mark,
                 cross_mark, mixhex, clamp, lerp, smooth, ease_out, back_out, at, window)

from gfx import cross_mark as _cross, check_mark as _check  # noqa: E402


def cross_mark(c, x, y, s, color=RED, a=1.0):
    _cross(c, x, y, s * 150, color, a)


def check_mark(c, x, y, s, color="#4fd18b", a=1.0, prog=1.0):
    _check(c, x, y, s * 100, color, a, prog)


HERE = os.path.dirname(os.path.abspath(__file__))
TR = json.load(open(os.path.join(HERE, "transcript.json")))


def S(i):
    return TR[i]["start"]


def E(i):
    return TR[i]["end"]


def WT(i, word, nth=0, end=False):
    """Time of `word` (prefix match, case/punctuation-insensitive) inside sentence i."""
    k = 0
    for w in TR[i]["words"]:
        clean = re.sub(r"[^a-z0-9']", "", w["w"].lower())
        if clean.startswith(word.lower()):
            if k == nth:
                return w["e"] if end else w["s"]
            k += 1
    return TR[i]["start"]


SHOTS = []


def shot(start, push=0.035, dip=0.0, drift=1.0):
    def deco(fn):
        SHOTS.append((start, fn, push, dip, drift))
        return fn
    return deco


def fade(t, a, d=0.3):
    return clamp((t - a) / d)


def headline(c, t, start, s, y=150, size=58, color=WHITE, end=None, sp=0.05):
    pop_text(c, t, start, s, W / 2, y, size, color, end=end, sp=sp)


def dark_sea(c, t, k=1.0, rays=0.4, green=False):
    top = mixhex(SEA_TOP, GREEN_TOP if green else DARK_TOP, k)
    bot = mixhex(SEA_BOT, GREEN_BOT if green else DARK_BOT, k)
    ocean(c, t, top, bot, rays=rays * (1 - k * 0.7), snow=0.8)


def blueprint(c, t):
    blit(c, cached("bp", lambda cc: (fill_shader(cc, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#0d2a3a", "#06141c"])),
                                     [line(cc, x, 0, x, H, "#7fd8ea", 1, 0.08) for x in range(0, W, 60)],
                                     [line(cc, 0, y, W, y, "#7fd8ea", 1, 0.08) for y in range(0, H, 60)])))
    marine_snow(c, t, 0.4)


def bone_icon(c, x, y, s=1.0, a=1.0, col="#e9e2cf"):
    with xf(c, x, y, s=s, rot=-30, alpha=a):
        rrect(c, -70, -14, 140, 28, 12, col)
        for sx in (-1, 1):
            for sy in (-1, 1):
                c.drawCircle(sx * 72, sy * 16, 22, P(col))


def fin_icon(c, x, y, s=1.0, a=1.0, col="#9fb7c0"):
    with xf(c, x, y, s=s, alpha=a):
        p = skia.Path()
        p.moveTo(-70, 60)
        p.quadTo(-20, -40, 40, -80)
        p.quadTo(20, 0, 70, 60)
        p.close()
        c.drawPath(p, P(col))


def brain_icon(c, x, y, r, col="#f39bb2", a=1.0):
    with xf(c, x, y, alpha=a):
        for dx, dy, rr in ((-0.45, -0.1, 0.62), (0.4, -0.15, 0.64), (0, -0.45, 0.6), (-0.2, 0.3, 0.55), (0.3, 0.3, 0.55)):
            c.drawCircle(dx * r, dy * r, rr * r, P(col))
        p = skia.Path()
        p.moveTo(0, -r * 0.9)
        p.quadTo(r * 0.15, 0, 0, r * 0.7)
        c.drawPath(p, P(mixhex(col, "#000000", 0.3), max(2, r * 0.08)))


def suction_cup(c, x, y, s=1.0, a=1.0):
    with xf(c, x, y, s=s, alpha=a):
        rrect(c, -16, -160, 32, 140, 12, "#8a6a4a")
        p = skia.Path()
        p.moveTo(-100, 40)
        p.quadTo(-90, -40, 0, -30)
        p.quadTo(90, -40, 100, 40)
        p.close()
        c.drawPath(p, P("#d84a3a"))


def map_card(c, t, x, y, w, h, title, pins, prog=1.0, a=1.0, sub=None):
    """Stylised Pacific-Northwest coastline card with pins [(fx, fy, label, start)]."""
    with xf(c, x, y, alpha=a):
        rrect(c, -w / 2, -h / 2, w, h, 16, "#0d2b3a")
        c.save()
        c.clipRRect(skia.RRect.MakeRectXY(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), 16, 16), True)
        land = "#2f5d55"
        # mainland (right) and island (left), a sound in between
        p = skia.Path()
        p.moveTo(w * 0.05, -h / 2)
        p.cubicTo(-w * 0.05, -h * 0.2, w * 0.12, -h * 0.05, -w * 0.02, h * 0.12)
        p.cubicTo(-w * 0.1, h * 0.25, w * 0.05, h * 0.35, 0, h / 2)
        p.lineTo(w / 2, h / 2)
        p.lineTo(w / 2, -h / 2)
        p.close()
        c.drawPath(p, P(land))
        c.drawPath(blob_path(-w * 0.3, -h * 0.25, w * 0.45, h * 0.32, 5, rough=0.3), P(land))
        c.drawPath(blob_path(-w * 0.12, h * 0.05, w * 0.12, h * 0.1, 9, rough=0.3), P(land))
        c.drawPath(blob_path(w * 0.04, h * 0.2, w * 0.06, h * 0.22, 3, rough=0.3), P("#0d2b3a"))
        for i in range(7):
            line(c, -w / 2, -h / 2 + i * h / 6, w / 2, -h / 2 + i * h / 6, WHITE, 1, 0.06)
        c.restore()
        rrect(c, -w / 2, -h / 2, w, h, 16, "#7fd8ea", a=0.5, stroke=3)
        spaced(c, title, -w / 2 + 30, -h / 2 + 50, 28, WHITE, "ExtraBold", "left", 1, 0.08)
        if sub:
            spaced(c, sub, -w / 2 + 30, -h / 2 + 84, 20, MUTED, "Bold", "left", 1, 0.1)
        for fx, fy, lab, st in pins:
            k = back_out(at(t, st, 0.4))
            if k <= 0:
                continue
            px, py = fx * w / 2, fy * h / 2
            with xf(c, px, py, s=k):
                c.drawCircle(0, -26, 16, P(RED))
                c.drawPath(poly([(-12, -18), (12, -18), (0, 4)]), P(RED))
                c.drawCircle(0, -26, 6, P(WHITE))
            if lab:
                spaced(c, lab, px + 24, py - 18, 20, WHITE, "ExtraBold", "left", clamp((t - st) / 0.3), 0.06)


def options_list(c, t, x, y, items, active=-1, struck=(), size=44, a=1.0, appear=None, strike_t=None):
    """'YOUR OPTIONS' list: struck items get a red line, the active item gets a red box."""
    spaced(c, "YOUR OPTIONS", x, y, 40, WHITE, "Black", "left", a, 0.08)
    for i, s in enumerate(items):
        if appear and t < appear[i]:
            continue
        ka = clamp((t - appear[i]) / 0.25) if appear else 1
        yy = y + 80 + i * 74
        lab = f"{i + 1}. {s}"
        wd = spaced_w(lab, size, "ExtraBold", 0.05)
        col = WHITE if i not in struck else "#c7a3a0"
        if i == active:
            rrect(c, x - 16, yy - size * 0.95, wd + 32, size * 1.4, 6, RED, a=a * ka, stroke=4)
        spaced(c, lab, x, yy, size, col, "ExtraBold", "left", a * ka * (0.6 if i in struck else 1), 0.05)
        if i in struck:
            st = strike_t.get(i, 0) if strike_t else 0
            strike(c, x - 8, yy - size * 0.32, x + wd + 8, (t - st) / 0.4, RED, 6, a)


def stamp(c, t, start, s, x, y, size=80, col=RED, rot=-8):
    if t < start:
        return
    k = at(t, start, 0.25)
    sc = lerp(1.8, 1.0, ease_out(k))
    with xf(c, x, y, s=sc, rot=rot, alpha=k):
        wd = spaced_w(s, size, "Black", 0.06)
        rrect(c, -wd / 2 - 24, -size * 0.95, wd + 48, size * 1.3, 8, col, stroke=8)
        spaced(c, s, 0, 0, size, col, "Black", "center", 1, 0.06, shadow=False)


def counter(c, t, start, dur, v0, v1, x, y, size, fmt="{:,}", col=AMBER, suffix="", a=1.0, align="center"):
    if t < start:
        return
    k = ease_out(at(t, start, dur))
    v = int(round(lerp(v0, v1, k)))
    spaced(c, fmt.format(v) + suffix, x, y, size, col, "Black", align, a * clamp((t - start) / 0.15), 0.03)


def shake(t, start, dur=0.4, amp=14):
    if start <= t < start + dur:
        k = 1 - (t - start) / dur
        return math.sin(t * 90) * amp * k, math.cos(t * 77) * amp * k
    return 0, 0


# =================================================================== HOOK
@shot(0.0, push=0.05)
def s_reef_intro(c, t, a, b):
    ocean(c, t)
    reef(c, t, seed=1)
    x = lerp(300, 1100, (t - a) / (b - a))
    diver(c, x, 430 + math.sin(t * 0.7) * 14, 0.75, t, beam=0.6)
    fish(c, (1500 - t * 40) % 2200 - 100, 260, 0.6, t, -1)
    fish(c, (1600 - t * 40) % 2200 - 60, 300, 0.45, t, -1)
    pop_text(c, t, WT(0, "rocky"), "ROCKY REEF  ·  COLD PACIFIC", W / 2, 140, 34, WHITE, end=S(1) + 0.2, sp=0.12)
    # research checklist
    if t > S(1) - 0.1:
        k = ease_out(at(t, S(1) - 0.1, 0.5))
        px = lerp(-560, 120, k)
        rrect(c, px, 210, 560, 360, 18, "#071822", a=0.82)
        rrect(c, px, 210, 560, 360, 18, CYAN, a=0.4, stroke=3)
        spaced(c, "YOUR RESEARCH", px + 36, 268, 30, AMBER, "Black", "left", 1, 0.1)
        rows = [(WT(2, "sharks"), "SHARKS: RARE"), (WT(3, "seals"), "SEALS: IGNORE DIVERS"),
                (WT(4, "nothing"), "NOTHING HUNTS YOU")]
        for i, (st, s) in enumerate(rows):
            if t < st:
                continue
            yy = 350 + i * 76
            check_mark(c, px + 60, yy - 12, 0.5, "#4fd18b", 1, clamp((t - st) / 0.3))
            spaced(c, s, px + 100, yy, 32, WHITE, "ExtraBold", "left", clamp((t - st) / 0.2), 0.05)
    stamp(c, t, S(5) + 0.15, "THE RULE", 680, 600, 54, AMBER, -6)


@shot(S(6) - 0.15, push=0.10)
def s_feel_it(c, t, a, b):
    dark_sea(c, t, 0.55)
    reef(c, t, seed=1, a=0.9)
    dx, dy = shake(t, WT(6, "feel"), 0.5, 8)
    diver(c, 960 + dx, 470 + dy, 1.25, t, kick=0.15, beam=0.6)
    tint(c, "#000000", 0.2 * fade(t, a, 1.0))


@shot(S(7), push=0.06)
def s_ankle(c, t, a, b):
    dark_sea(c, t, 0.6)
    blit(c, cached(("reefblur", 1), lambda cc: reef(cc, 0, seed=2), blur=8, clear=None), 0, 60)
    # close on the diver's legs (diver body off-screen right)
    pull = 0
    diver(c, 1700 + pull, 330, 2.6, t, kick=0.25 * (1 - fade(t, WT(7, "slides"), 0.6)), beam=0.0,
          bubbles_on=False)
    ank_x, ank_y = 1120, 380
    prog = smooth((t - WT(7, "something")) / (WT(7, "ankle", end=True) - WT(7, "something") + 0.4))
    reach_arm(c, 200, 1120, ank_x, ank_y, t, w0=70, prog=prog, under=-1, curl_tip=2.0 + 1.6 * prog, ph=0.4)
    pop_text(c, t, WT(7, "soft"), "SOFT.", 300, 220, 64, WHITE, end=WT(7, "slides"))
    pop_text(c, t, WT(7, "cold"), "COLD.", 520, 220, 64, CYAN, end=WT(7, "slides"))
    pop_text(c, t, WT(7, "kelp") - 0.15, "NOT KELP.", 420, 220, 84, RED)


@shot(S(8), push=0.08)
def s_pull(c, t, a, b):
    dark_sea(c, t, 0.65)
    blit(c, cached(("reefblur", 1), lambda cc: reef(cc, 0, seed=2), blur=8, clear=None), 0, 60)
    tug = 0
    for st in (WT(8, "pulls"), WT(8, "testing")):
        if t > st:
            tug += -40 * math.sin(clamp((t - st) / 0.6) * math.pi)
    diver(c, 1700 + tug, 330 + tug * 0.2, 2.6, t, kick=0.0, beam=0.0, bubbles_on=False)
    reach_arm(c, 200, 1120, 1120 + tug, 380 + tug * 0.2, t, w0=70, prog=1, under=-1, curl_tip=3.8, ph=0.4)
    reach_arm(c, -120, 900, 1020 + tug, 400, t, w0=55, prog=smooth((t - WT(8, "testing")) / 1.2), under=-1,
              curl_tip=3.2, ph=1.4)
    pop_text(c, t, WT(8, "testing"), "TESTING THE GRIP", 520, 200, 56, WHITE)


@shot(S(9), push=0.06, dip=0.25)
def s_reveal(c, t, a, b):
    dark_sea(c, t, 0.45)
    reef(c, t, seed=3)
    k = smooth((t - a) / 2.2)
    rock(c, 1500, 640, 760, 520, 77, ROCK2, "#1b4352")
    octopus(c, 1300, 600, 1.0, t, face=-1, camo=1 - k, blink=clamp(1 - (t - WT(9, "giant")) / 0.3),
            look=(-1, 0.2), eye_glow=0.6 * fade(t, WT(9, "knows"), 0.6))
    diver(c, 330, 330, 0.5, t, beam=0.7)
    tl = WT(9, "giant")
    if t > tl:
        kk = ease_out(at(t, tl, 0.5))
        line(c, 120, 820, 120 + 680 * kk, 820, AMBER, 4)
        spaced(c, "GIANT PACIFIC OCTOPUS", 120, 800, 56, WHITE, "Black", "left", kk, 0.05)
        spaced(c, "ENTEROCTOPUS DOFLEINI", 122, 870, 26, MUTED, "Bold", "left", fade(t, tl + 0.4), 0.14)
    pop_text(c, t, WT(9, "knows"), "IT ALREADY KNOWS YOU'RE HERE", W / 2, 140, 44, AMBER)


@shot(S(10), push=0.04)
def s_dangerous(c, t, a, b):
    ocean(c, t)
    headline(c, t, WT(10, "dangerous"), "DANGEROUS SEA CREATURE?", 150, 56)
    k1 = ease_out(at(t, WT(10, "great"), 0.8))
    shark(c, lerp(-400, 560, k1), 560, 1.05, t, 1)
    if k1 > 0:
        spaced(c, "GREAT WHITE", 560, 820, 34, WHITE, "ExtraBold", "center", k1, 0.08)
    k2 = ease_out(at(t, WT(10, "orca"), 0.8))
    orca(c, lerp(2300, 1380, k2), 560, 1.0, t, -1)
    if k2 > 0:
        spaced(c, "ORCA", 1380, 820, 34, WHITE, "ExtraBold", "center", k2, 0.08)


@shot(S(11), push=0.04)
def s_category(c, t, a, b):
    ocean(c, t)
    k = ease_out(at(t, a, 0.9))
    shark(c, 560 - k * 900, 560, 1.05, t, 1, a=1 - k)
    orca(c, 1380 + k * 900, 560, 1.0, t, -1, a=1 - k)
    ko = ease_out(at(t, a + 0.3, 1.0))
    octopus(c, 960, lerp(1300, 560, ko), 0.95, t, face=1)
    headline(c, t, WT(11, "different"), "A DIFFERENT CATEGORY", 150, 60, AMBER)


@shot(S(12), push=0.03)
def s_no_bones(c, t, a, b):
    blueprint(c, t)
    items = [(WT(12, "bones"), "BONES", bone_icon), (WT(12, "shell"), "SHELL", None), (WT(12, "fins"), "FINS", fin_icon)]
    for i, (st, lab, fn) in enumerate(items):
        x = 480 + i * 480
        k = back_out(at(t, st - 0.15, 0.4))
        if k <= 0:
            continue
        with xf(c, x, 520, s=k):
            c.drawCircle(0, 0, 160, P("#0b2230"))
            c.drawCircle(0, 0, 160, P(CYAN, 3, 0.5))
            if fn:
                fn(c, 0, 0, 1.0)
            else:
                snail(c, 0, 0, 2.0)
        if t > st + 0.25:
            cross_mark(c, x, 520, 1.2 * ease_out(at(t, st + 0.25, 0.25)), RED)
        spaced(c, "NO " + lab, x, 770, 46, WHITE, "Black", "center", clamp((t - st) / 0.2), 0.08)


@shot(S(13), push=0.05)
def s_yet(c, t, a, b):
    t1, t2, t3 = a, WT(13, "hunts"), WT(13, "disappear")
    if t < t2:
        ocean(c, t)
        reef(c, t, seed=4)
        octopus(c, 960, 560, 1.15, t)
        stamp(c, t, WT(13, "largest"), "LARGEST OCTOPUS ON EARTH", W / 2, 160, 54, AMBER, -3)
    elif t < t3:
        ocean(c, t)
        k = ease_out(at(t, t2, 0.5))
        shark(c, lerp(-300, 640, k), 520, 0.9, t, 1, kind="dogfish", col="#6f8590")
        octopus(c, 1380, 560, 0.9, t, face=-1)
        pop_text(c, t, t2, "IT HUNTS SHARKS", W / 2, 160, 70, RED)
    else:
        ocean(c, t)
        reef(c, t, seed=4)
        rock(c, 960, 680, 900, 420, 51, ROCK, ROCK_HI)
        k = smooth((t - t3) / 1.4)
        octopus(c, 960, 560, 1.15, t, camo=k, camo_col="#1d4656", a=1 - 0.85 * k, eye_glow=0)
        pop_text(c, t, t3 + 0.2, "...AND VANISHES IN PLAIN SIGHT", W / 2, 160, 52, WHITE)


@shot(S(14), push=0.06, dip=0.3)
def s_title(c, t, a, b):
    dark_sea(c, t, 0.85, rays=0.2)
    bl = 1.0 if WT(14, "never") < t < WT(14, "never") + 0.18 else 0.0
    eye_closeup(c, 1450, 560, 230, t, blink=bl, look=(-1, 0))
    diver(c, 560, 760, 0.35, t, beam=0.8)
    k = ease_out(at(t, a + 0.2, 0.6))
    spaced(c, "WHY YOU'D NEVER", 120, 300, 70, WHITE, "Black", "left", k, 0.04)
    spaced(c, "WANT TO MEET", 120, 384, 70, WHITE, "Black", "left", k, 0.04)
    spaced(c, "ONE UNDERWATER", 120, 468, 70, RED, "Black", "left", k, 0.04)


# =================================================================== 1. SIZE
@shot(S(15), push=0.03, dip=0.2)
def s_ch_size(c, t, a, b):
    dark_sea(c, t, 0.4)
    octopus_spread(c, 1300, 520, 0.85, t, a=0.35)
    chapter(c, t, a, 1, 5, "SIZE", "HARD TO IMAGINE")


@shot(S(16), push=0.02)
def s_size(c, t, a, b):
    blueprint(c, t)
    big = smooth((t - S(17)) / 1.0) if t > S(17) else 0
    sc = 0.9 * (1 + 0.18 * big)
    octopus_spread(c, 960, 520, sc, t, amp=0.05)
    kw = back_out(at(t, WT(16, "weigh"), 0.4))
    if kw > 0:
        with xf(c, 330, 210, s=kw):
            rrect(c, -190, -70, 380, 130, 14, "#071822", a=0.85)
            spaced(c, "WEIGHT", 0, -22, 24, MUTED, "Bold", "center", 1, 0.12)
            spaced(c, "15 - 30 KG", 0, 36, 56, AMBER, "Black", "center", 1, 0.04)
    st = WT(16, "arms")
    if t > st:
        k = ease_out(at(t, st, 1.4))
        span = 0.9 * 430 * 2 * (1 + 0.18 * big) * 0.98
        x0, x1 = 960 - span / 2 * k, 960 + span / 2 * k
        line(c, x0, 960, x1, 960, WHITE, 4)
        line(c, x0, 940, x0, 980, WHITE, 4)
        line(c, x1, 940, x1, 980, WHITE, 4)
        lab = "3+ METRES TIP TO TIP" if big < 0.5 else "EVEN LARGER"
        spaced(c, lab, 960, 1035, 36, WHITE if big < 0.5 else AMBER, "Black", "center", k, 0.08)


@shot(S(18), push=0.03)
def s_dog(c, t, a, b):
    ocean(c, t, rays=0.6)
    reef(c, t, seed=5, a=0.6)
    k1 = back_out(at(t, WT(18, "dog"), 0.45))
    octopus(c, 520, 520, 0.75, t)
    spaced(c, "=", 920, 560, 120, WHITE, "Black", "center", fade(t, WT(18, "heavy")), 0)
    if k1 > 0:
        with xf(c, 1240, 600, s=k1):
            dog_icon(c, 0, 0, 1.4, "#e9dfcf")
        spaced(c, "AS HEAVY AS A BIG DOG", 1240, 300, 40, WHITE, "Black", "center", k1, 0.06)
    st = WT(18, "eight")
    if t > st:
        k = ease_out(at(t, st, 0.4))
        blueprint(c, t) if k >= 1 else tint(c, "#071822", k)
        person_icon(c, 700, 860, 1.6, "#e9dfcf", k)
        line(c, 600, 900, 600, 900 - 560 * k, WHITE, 3, k)
        spaced(c, "~1.8 M", 590, 900 - 560 * k - 20, 30, WHITE, "ExtraBold", "right", k, 0.05)
        ka = ease_out(at(t, st + 0.3, 0.9))
        draw_arm(c, 1150, 940, -math.pi / 2, 900 * ka, 0.0, 1.6, t, 0, 0.05, 0.2, 46, OCTO, 1, True)
        spaced(c, "ONE ARM: 1.5+ M", 1260, 260, 36, AMBER, "Black", "left", ka, 0.05)
        spaced(c, "8 ARMS LONGER THAN A MAN IS TALL", W / 2, 120, 44, WHITE, "Black", "center", ka, 0.05)


@shot(S(19), push=0.05)
def s_muscle(c, t, a, b):
    ocean(c, t)
    sq = 1 + 0.08 * math.sin(t * 7) * clamp(1 - (t - a) / 2.5)
    octopus(c, 960, 520, 1.05, t, squash=sq)
    pop_text(c, t, WT(19, "soft"), "100% SOFT MUSCLE", W / 2, 150, 66, WHITE)


@shot(S(20), push=0.04)
def s_xray(c, t, a, b):
    blueprint(c, t)
    with xf(c, 0, 0, alpha=0.45):
        octopus(c, 960, 520, 1.1, t, col="#4aa9c0", suckers=False, amp=0.05)
    sy = lerp(80, 1000, ((t - a) / 2.0) % 1.0)
    fill_shader(c, skia.Rect(0, sy - 60, W, sy + 4), linear(0, sy - 60, 0, sy, [(CYAN, 0), (CYAN, 0.35)]))
    line(c, 0, sy, W, sy, CYAN, 3, 0.9)
    spaced(c, "X-RAY", 120, 120, 30, CYAN, "Black", "left", 1, 0.2)
    pop_text(c, t, WT(20, "single"), "BONES FOUND: 0", W / 2, 960, 60, RED)


@shot(S(21), push=0.10)
def s_beak_zoom(c, t, a, b):
    blueprint(c, t)
    z = 1 + 0.9 * smooth((t - a) / 2.2)
    with xf(c, 960, 540, s=z):
        with xf(c, -960, -560, alpha=0.4):
            octopus(c, 960, 520, 1.1, t, col="#4aa9c0", suckers=False, amp=0.05)
        glow(c, 0, 20, 120, AMBER, 0.6 * fade(t, a + 0.6))
        beak(c, 0, 20, 0.8, fade(t, a + 0.6), col="#f2a93b")
    headline(c, t, WT(21, "changes"), "ONE FACT CHANGES EVERYTHING", 150, 54)


@shot(S(22), push=0.03)
def s_beak(c, t, a, b):
    blueprint(c, t)
    k = back_out(at(t, a, 0.5))
    with xf(c, 560, 540, s=k * 2.6):
        beak(c, 0, 0, 1.0, col="#2a211a")
    leader(c, 700, 470, 980, 330, "BEAK", at(t, WT(22, "beak"), 0.6), AMBER, 40)
    leader(c, 700, 620, 980, 700, "THE ONLY HARD PART", at(t, WT(22, "only"), 0.6), WHITE, 36)
    pop_text(c, t, WT(22, "squeeze"), "ANY GAP BIGGER THAN THIS = A WAY THROUGH", W / 2, 150, 42, WHITE)


@shot(S(23), push=0.05)
def s_coin(c, t, a, b):
    ocean(c, t)
    rock(c, 960, 560, 1400, 820, 12, ROCK, ROCK_HI)
    c.drawCircle(1180, 560, 64, P("#02080b"))
    c.drawCircle(1180, 560, 64, P("#000000", 6, 0.4))
    k = back_out(at(t, WT(23, "coin"), 0.45))
    if k > 0:
        coin(c, 700, 560, 64 * k)
        spaced(c, "=", 940, 590, 90, WHITE, "Black", "center", k, 0)
    pop_text(c, t, WT(23, "enough"), "A COIN-SIZED GAP IS ENOUGH", W / 2, 150, 54, AMBER)


@shot(S(24), push=0.03)
def s_squeeze(c, t, a, b):
    ocean(c, t)
    k = smooth((t - (a + 0.6)) / 4.5)
    cx = lerp(380, 1560, k)
    near = math.exp(-((cx - 960) / 260) ** 2)
    with xf(c, cx, 560, sx=1 - 0.75 * near, sy=1 + 0.25 * near):
        octopus(c, 0, 0, 0.7, t)
    # rock wall with crack drawn over the animal; animal visible only through the crack
    c.save()
    crack = skia.Path()
    crack.addRect(skia.Rect(940, 0, 980, H))
    c.clipPath(crack, skia.ClipOp.kDifference, True)
    rock(c, 960, 540, 640, 1500, 31, ROCK, ROCK_HI)
    c.restore()
    rrect(c, 944, -10, 32, H + 20, 0, "#03090c", a=0.55)
    pop_text(c, t, WT(24, "pour"), "IT POURS ITSELF THROUGH", W / 2, 150, 54, WHITE)
    pop_text(c, t, WT(24, "never"), "AND YOU'D NEVER SEE IT GO", W / 2, 230, 40, MUTED)


# =================================================================== 2. DIET
@shot(S(25), push=0.03, dip=0.2)
def s_ch_diet(c, t, a, b):
    dark_sea(c, t, 0.4)
    crab(c, 1400, 520, 1.6, t)
    shell_pile(c, 1350, 800, 14, 1.2)
    chapter(c, t, a, 2, 5, "WHAT IT EATS", "THIS IS WHERE IT GETS UNCOMFORTABLE")


@shot(S(26), push=0.025)
def s_menu(c, t, a, b):
    ocean(c, t, rays=0.6)
    spaced(c, "DAILY MENU", W / 2, 150, 60, WHITE, "Black", "center", fade(t, a), 0.1)
    items = [(WT(26, "crabs"), "CRABS", lambda x, y, k: crab(c, x, y, 1.1 * k, t)),
             (WT(26, "clams"), "CLAMS", lambda x, y, k: clam(c, x, y + 20, 1.5 * k, open_=0.3)),
             (WT(26, "snails"), "SNAILS", lambda x, y, k: snail(c, x, y, 1.4 * k)),
             (WT(26, "lobsters"), "LOBSTERS", lambda x, y, k: lobster(c, x + 40, y, 0.8 * k, t=t)),
             (WT(27, "fish"), "FISH", lambda x, y, k: fish(c, x, y, 1.4 * k, t))]
    for i, (st, lab, fn) in enumerate(items):
        if t < st - 0.1:
            continue
        k = back_out(at(t, st - 0.1, 0.4))
        x = 260 + i * 350
        c.drawCircle(x, 520, 140, P("#0a2633", a=0.9))
        fn(x, 520, k)
        spaced(c, lab, x, 730, 36, WHITE, "Black", "center", clamp((t - st) / 0.2), 0.08)


@shot(S(28), push=0.08)
def s_sharks(c, t, a, b):
    dx, dy = shake(t, WT(28, "sharks"), 0.5, 18)
    with xf(c, dx, dy):
        dark_sea(c, t, 0.7)
        tint(c, "#3a0606", 0.5 * fade(t, WT(28, "sharks")))
        shark(c, 960, 600, 1.4, t, 1, kind="dogfish", col="#6f8590")
        pop_text(c, t, WT(28, "sharks") - 0.05, "SHARKS.", W / 2, 260, 150, RED, dur=0.25)


@shot(S(29), push=0.03)
def s_aquarium(c, t, a, b):
    ocean(c, t, "#24617a", "#0c2a38", rays=0.7)
    rrect(c, 0, 940, W, 140, 0, "#c9b994")
    rock(c, 1350, 900, 700, 300, 61, "#3b4f57", "#56707a")
    tc, tw, tp = WT(29, "catching"), WT(29, "wrapping"), WT(29, "pulling")
    ox, oy = 1300, 700
    # shark path
    if t < tc:
        sx, sy, rot = lerp(-300, 760, ease_out((t - a) / (tc - a + 0.5))), 520, 0
    else:
        k = smooth((t - tp) / 1.6) if t > tp else 0
        sx, sy, rot = lerp(760, 1060, k), lerp(520, 620, k) + math.sin(t * 9) * 8 * (1 - k * 0.5), 10 * k
    with xf(c, sx, sy, rot=rot):
        shark(c, 0, 0, 0.75, t * (2.5 if t > tc else 1), 1, kind="dogfish", col="#6f8590")
    octopus(c, ox, oy, 0.85, t, face=-1, look=(-1, -0.3))
    if t > tc:
        reach_arm(c, ox - 60, oy + 40, sx + 60, sy, t, w0=34, prog=clamp((t - tc) / 0.5), under=-1, ph=0.3)
    if t > tw:
        for j, (dxx, dyy) in enumerate(((-90, 10), (-20, 50), (90, 30))):
            reach_arm(c, ox - 40 + j * 20, oy + 50, sx + dxx, sy + dyy, t, w0=30, prog=clamp((t - tw - j * 0.2) / 0.5),
                      under=1 if j % 2 else -1, curl_tip=3.5, ph=j)
    # glass reflections + REC
    for i in range(3):
        c.drawPath(poly([(200 + i * 500, 0), (300 + i * 500, 0), (100 + i * 500, H), (0 + i * 500, H)]),
                   P(WHITE, a=0.04))
    rec_overlay(c, t, "SEATTLE AQUARIUM")
    pop_text(c, t, WT(29, "dogfish"), "OCTOPUS vs DOGFISH SHARK", W / 2, 170, 44, WHITE)


@shot(S(30), push=0.03)
def s_puget(c, t, a, b):
    ocean(c, t, rays=0.3)
    pins = [(0.0, -0.05, "DEN", WT(30, "octopus")), (0.08, 0.25, "SHARK REMAINS", WT(30, "shark")),
            (-0.1, 0.05, "", WT(30, "remains")), (0.12, -0.3, "", WT(30, "dens"))]
    map_card(c, t, W / 2, 560, 1300, 760, "PUGET SOUND", pins, sub="WASHINGTON, USA", a=fade(t, a))


@shot(S(31), push=0.05)
def s_den(c, t, a, b):
    dark_sea(c, t, 0.4)
    reef(c, t, seed=6)
    rock(c, 1080, 640, 1100, 640, 21, ROCK, ROCK_HI)
    c.drawOval(skia.Rect(900, 600, 1240, 860), P("#02070a"))
    bl = 1.0 if (t % 3.0) < 0.15 else 0.0
    for ex in (1030, 1110):
        c.drawCircle(ex, 700, 16, P("#efd9a0", a=0.9))
        rrect(c, ex - 10, 697, 20, 6, 3, "#08090b")
        if bl:
            c.drawCircle(ex, 700, 17, P("#02070a"))
    pop_text(c, t, WT(31, "hunter"), "EVERY GOOD HUNTER", W / 2, 150, 54, WHITE)
    pop_text(c, t, WT(31, "record"), "KEEPS A RECORD", W / 2, 230, 54, AMBER)


@shot(S(32), push=0.04)
def s_midden(c, t, a, b):
    dark_sea(c, t, 0.4)
    reef(c, t, seed=6)
    rock(c, 760, 600, 1000, 600, 21, ROCK, ROCK_HI)
    c.drawOval(skia.Rect(600, 560, 920, 800), P("#02070a"))
    for ex in (720, 800):
        c.drawCircle(ex, 650, 14, P("#efd9a0", a=0.9))
        rrect(c, ex - 9, 647, 18, 5, 2.5, "#08090b")
    n = int(26 * clamp((t - WT(32, "pile")) / 3.0))
    shell_pile(c, 760, 960, n, 1.0)
    if n:
        leader(c, 900, 900, 1080, 860, "EMPTY SHELLS + CLAWS", at(t, WT(32, "shells"), 0.6), WHITE, 28)
    rows = [("CRAB", "x14"), ("CLAM", "x31"), ("SNAIL", "x9"), ("SHARK", "x1")]
    receipt(c, 1520, 140, rows, at(t, WT(32, "receipt"), 1.6), t)


@shot(S(33), push=0.04)
def s_no_receipt(c, t, a, b):
    ocean(c, t, "#24394a", "#0b1520", rays=0.2)
    person_icon(c, 700, 640, 2.4, "#e9dfcf")
    for i in range(3):
        k = back_out(at(t, a + 0.4 + i * 0.25, 0.3))
        if k > 0:
            text(c, "?", 860 + i * 70, 420 - i * 40, 90 * k, AMBER, "Black")
    k = back_out(at(t, WT(33, "receipt"), 0.4))
    if k > 0:
        with xf(c, 1320, 560, s=k):
            rrect(c, -260, -110, 520, 220, 14, "#071822")
            rrect(c, -260, -110, 520, 220, 14, RED, stroke=4)
            cross_mark(c, -170, 0, 0.8, RED)
            spaced(c, "RECEIPT", -100, -10, 44, WHITE, "Black", "left", 1, 0.05)
            spaced(c, "NOT FOUND", -100, 46, 44, RED, "Black", "left", 1, 0.05)


# =================================================================== 3. SENSES
@shot(S(34), push=0.04, dip=0.2)
def s_ch_senses(c, t, a, b):
    dark_sea(c, t, 0.9, rays=0.0)
    octopus(c, 1350, 520, 0.8, t, a=0.35, col="#4a2a26")
    chapter(c, t, a, 3, 5, "SENSES", "HUNTING IN DARK, COLD WATER")


@shot(S(36), push=0.04)
def s_not_sound(c, t, a, b):
    dark_sea(c, t, 0.85, rays=0.0)
    for i in range(6):
        r = ((t - a) * 160 + i * 90) % 540
        c.drawCircle(760, 540, r, P(CYAN, 4, 0.6 * (1 - r / 540)))
    octopus(c, 760, 540, 0.6, t)
    k = ease_out(at(t, WT(36, "sound"), 0.3))
    if k > 0:
        cross_mark(c, 760, 540, 2.6 * k, RED)
    pop_text(c, t, WT(36, "not"), "NOT WITH SOUND", 1400, 560, 70, WHITE)


@shot(S(37), push=0.03)
def s_suckers(c, t, a, b):
    dark_sea(c, t, 0.5)
    k = ease_out(at(t, a, 1.2))
    draw_arm(c, -100, 700, -0.12, 2300 * k, 0.15, 0.4, t, 0, 0.05, 0.15, 120, OCTO, 1, True)
    counter(c, t, WT(37, "2"), 1.6, 0, 2000, W / 2, 300, 150, "{:,}", AMBER, "+")
    if t > WT(37, "2"):
        spaced(c, "SUCKERS", W / 2, 380, 46, WHITE, "Black", "center", fade(t, WT(37, "2")), 0.2)
    pop_text(c, t, WT(37, "covered"), "EVERY ARM IS COVERED", W / 2, 140, 44, MUTED, end=WT(37, "2"))


@shot(S(38), push=0.04)
def s_not_cups(c, t, a, b):
    dark_sea(c, t, 0.5)
    k = back_out(at(t, a, 0.4))
    with xf(c, 960, 600, s=k * 1.6):
        suction_cup(c, 0, 0)
    if t > WT(38, "plain"):
        cross_mark(c, 960, 560, 2.0 * ease_out(at(t, WT(38, "plain"), 0.3)), RED)
    pop_text(c, t, WT(38, "plain"), "NOT PLAIN SUCTION CUPS", W / 2, 180, 60, WHITE)


@shot(S(39), push=0.05)
def s_sucker_close(c, t, a, b):
    dark_sea(c, t, 0.5)
    x, y = 960, 560
    c.drawCircle(x, y, 330, P(OCTO))
    c.drawCircle(x, y, 300, P(SUCKER))
    c.drawCircle(x, y, 210, P(mixhex(SUCKER, OCTO, 0.25)))
    c.drawCircle(x, y, 120, P(mixhex(SUCKER, OCTO, 0.6)))
    rnd = random.Random(4)
    for i in range(90):
        ang, d = rnd.uniform(0, 6.28), rnd.uniform(130, 290)
        px, py = x + math.cos(ang) * d, y + math.sin(ang) * d
        on = 0.5 + 0.5 * math.sin(t * 6 + i)
        lit = fade(t, WT(39, "taste"))
        c.drawCircle(px, py, 5, P(mixhex("#d79a7a", "#fff2a8", lit * on)))
        if lit * on > 0.6:
            glow(c, px, py, 18, "#fff2a8", 0.4)
    leader(c, 1180, 380, 1460, 260, "TASTE", at(t, WT(39, "taste"), 0.5), AMBER, 48)
    leader(c, 760, 760, 480, 880, "TOUCH", at(t, WT(39, "feel"), 0.5), CYAN, 48)
    pop_text(c, t, a + 0.2, "ONE SUCKER", W / 2, 140, 44, WHITE)


@shot(S(40), push=0.03)
def s_arm_reads(c, t, a, b):
    dark_sea(c, t, 0.5)
    rock(c, 960, 900, 2200, 500, 8, ROCK, ROCK_HI)
    k = smooth((t - a) / 4.0)
    pts = draw_arm(c, -200 + 900 * k, 640, 0.05, 1100, 0.2, 1.0, t, 0, 0.08, 0.3, 80, OCTO, 1, True)
    tx, ty, _ = pts[-8]
    for i in range(3):
        r = ((t * 120 + i * 50) % 150)
        c.drawCircle(tx, 700, r, P(AMBER, 3, 0.7 * (1 - r / 150)))
    pop_text(c, t, WT(41, "reading"), "READING THE ROCK", W / 2, 150, 54, WHITE)
    pop_text(c, t, WT(41, "fingertips"), "FINGERTIPS THAT CAN TASTE", W / 2, 230, 44, AMBER)


@shot(S(42), push=0.04)
def s_crab_crack(c, t, a, b):
    dark_sea(c, t, 0.75, rays=0.0)
    rock(c, 960, 620, 1500, 900, 44, ROCK, ROCK_HI)
    crack = poly([(1060, 300), (1120, 300), (1080, 560), (1140, 860), (1060, 860), (1020, 560)])
    c.drawPath(crack, P("#02070a"))
    found = WT(42, "long")
    c.save()
    c.clipPath(crack, doAntiAlias=True)
    crab(c, 1085, 640, 0.6, t, wiggle=0.3)
    reach_arm(c, 600, 300, 1090, 600, t, w0=26, prog=smooth((t - a) / 2.0), under=1, curl_tip=1.2)
    c.restore()
    reach_arm(c, 300, 200, 1050, 360, t, w0=30, prog=smooth((t - a) / 1.6), under=1, curl_tip=0.4, amp=0.04)
    if t > found:
        for i in range(2):
            r = ((t - found) * 200 + i * 80) % 200
            c.drawCircle(1085, 640, r, P(AMBER, 4, 1 - r / 200))
        label_box(c, 1085, 940, "FOUND BY TASTE", 30, bg=AMBER)
    # its eyes are far away and closed
    eye_closeup(c, 240, 860, 70, t, blink=0.85)
    spaced(c, "EYES: NOT NEEDED", 240, 1010, 22, MUTED, "Bold", "center", fade(t, found), 0.1)


# =================================================================== 4. VANISHING
@shot(S(43), push=0.04, dip=0.2)
def s_ch_vanish(c, t, a, b):
    dark_sea(c, t, 0.4)
    reef(c, t, seed=7)
    octopus(c, 1350, 600, 0.85, t, camo=0.5 + 0.5 * math.sin(t * 1.3), camo_col="#2b5462")
    chapter(c, t, a, 4, 5, "VANISHING", "THE TRULY UNSETTLING PART")


@shot(S(44), push=0.05)
def s_disappear(c, t, a, b):
    ocean(c, t)
    reef(c, t, seed=7)
    rock(c, 960, 700, 1000, 480, 81, ROCK, ROCK_HI)
    k = smooth((t - WT(44, "disappear")) / 1.2)
    octopus(c, 960, 600, 1.0, t, camo=k, camo_col="#1d4656", a=1 - 0.9 * k)
    pop_text(c, t, WT(44, "disappear"), "IT CAN DISAPPEAR", W / 2, 150, 60, WHITE)


@shot(S(45), push=0.05)
def s_chromato(c, t, a, b):
    c.drawRect(skia.Rect(0, 0, W, H), P("#f0d6bb"))
    rnd = random.Random(9)
    ctl = WT(45, "controls")
    for i in range(380):
        x, y = rnd.uniform(-20, W + 20), rnd.uniform(-20, H + 20)
        col = rnd.choice(("#8b2a1d", "#c4492f", "#d98b2b", "#5a2a1a"))
        base = rnd.uniform(10, 26)
        wave = 0.5 + 0.5 * math.sin(t * 2 + x * 0.006 - y * 0.004 + (3 * (t - ctl) if t > ctl else 0))
        r = base * (0.35 + 0.75 * wave)
        c.drawCircle(x, y, r, P(col, a=0.9))
    tint(c, "#000000", 0.25)
    if t > WT(45, "millions"):
        rrect(c, 0, 430, W, 220, 0, "#000000", a=0.55 * fade(t, WT(45, "millions")))
    pop_text(c, t, WT(45, "millions"), "MILLIONS OF COLOUR CELLS", W / 2, 520, 70, WHITE)
    pop_text(c, t, ctl, "EACH ONE UNDER CONTROL", W / 2, 610, 44, AMBER)


@shot(S(46), push=0.03)
def s_match(c, t, a, b):
    ts, tw, tst, tb = WT(46, "sand"), WT(46, "seaweed"), WT(46, "stone"), WT(46, "bumps")
    if t < tw:
        bg, cc, lab = "#c9b48a", "#bfa77a", "SAND"
    elif t < tst:
        bg, cc, lab = "#2f5a3a", "#3d6b42", "SEAWEED"
    else:
        bg, cc, lab = "#5d6669", "#6c7578", "ROUGH STONE"
    c.drawRect(skia.Rect(0, 0, W, H), P(bg))
    rnd = random.Random(len(lab))
    for _ in range(300):
        c.drawCircle(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(2, 14), P(mixhex(bg, "#000000", 0.25), a=0.5))
    if lab == "SEAWEED":
        for i in range(12):
            kelp(c, i * 170 + 40, H + 40, 900, t, seed=i, col="#24472d")
    tsw = max(ts, tw if t >= tw else ts, tst if t >= tst else ts)
    k = smooth((t - tsw) / 0.5) if t > ts else 0
    octopus(c, 960, 560, 1.0, t, camo=0.88 * k, camo_col=cc)
    if t > tb:
        rnd = random.Random(2)
        kb = back_out(at(t, tb, 0.4))
        for _ in range(40):
            px, py = 960 + rnd.uniform(-200, 120), 560 + rnd.uniform(-230, 40)
            c.drawCircle(px, py, 7 * kb, P(mixhex(cc, "#ffffff", 0.25)))
        label_box(c, 960, 960, "+ TEXTURE BUMPS", 34, bg=AMBER)
    stopwatch(c, 1700, 200, 80, clamp((t - a) / 1.0), AMBER, label="< 1 SEC")
    if t > ts:
        label_box(c, 260, 130, lab, 36)


@shot(S(47), push=0.08)
def s_strange(c, t, a, b):
    dark_sea(c, t, 0.85, rays=0.0)
    eye_closeup(c, 960, 600, 280, t, look=(0.3 * math.sin(t), 0))
    headline(c, t, a + 0.2, "HERE'S THE STRANGE PART", 140, 54, AMBER)


@shot(S(48), push=0.03)
def s_colorblind(c, t, a, b):
    def scene(cc):
        ocean(cc, t, rays=0.5)
        reef(cc, t, seed=8)
        rock(cc, 960, 760, 1300, 420, 18, "#5b6f5a", "#7e9278")
        octopus(cc, 960, 620, 0.9, t, camo=0.85, camo_col="#6f8468")
    split = 960
    c.save()
    c.clipRect(skia.Rect(0, 0, split, H))
    gm = skia.ColorFilters.Matrix([0.33, 0.59, 0.11, 0, 0, 0.33, 0.59, 0.11, 0, 0, 0.33, 0.59, 0.11, 0, 0, 0, 0, 0, 1, 0])
    c.saveLayer(None, skia.Paint(ColorFilter=gm))
    scene(c)
    c.restore()
    c.restore()
    c.save()
    c.clipRect(skia.Rect(split, 0, W, H))
    scene(c)
    c.restore()
    line(c, split, 0, split, H, WHITE, 6)
    spaced(c, "WHAT IT SEES", 480, 120, 40, WHITE, "Black", "center", 1, 0.08)
    spaced(c, "WHAT WE SEE", 1440, 120, 40, WHITE, "Black", "center", 1, 0.08)
    pop_text(c, t, WT(48, "color"), "NO COLOUR VISION", 480, 190, 32, RED)
    pop_text(c, t, WT(48, "perfectly"), "PERFECT MATCH", 1440, 190, 32, "#4fd18b")


@shot(S(49), push=0.04)
def s_rock_field(c, t, a, b):
    dark_sea(c, t, 0.3)
    rnd = random.Random(12)
    spots = [(rnd.uniform(120, 1800), rnd.uniform(380, 1000), rnd.uniform(150, 280), i) for i in range(16)]
    for x, y, r, i in spots:
        rock(c, x, y, r * 1.5, r, 300 + i, ROCK, ROCK_HI)
    bl = WT(50, "blinking")
    x, y = 1290, 720
    rock(c, x, y, 330, 220, 999, ROCK, ROCK_HI)
    if t > bl - 0.3:
        op = smooth((t - (bl - 0.3)) / 0.3)
        blink = 1.0 if bl + 0.6 < t < bl + 0.75 else 1 - op
        for ex in (x - 30, x + 40):
            c.drawCircle(ex, y - 40, 15, P("#efd9a0"))
            rrect(c, ex - 10, y - 43, 20, 6, 3, "#08090b")
            if blink > 0:
                c.drawRect(skia.Rect(ex - 17, y - 57, ex + 17, y - 57 + 34 * blink), P(ROCK_HI))
    pop_text(c, t, WT(49, "searching"), "YOU'RE NOT SEARCHING FOR AN ANIMAL", W / 2, 150, 46, WHITE, end=S(50))
    pop_text(c, t, S(50), "YOU'RE SEARCHING FOR A ROCK...", W / 2, 150, 50, WHITE)
    pop_text(c, t, bl, "...THAT BLINKS BACK", W / 2, 230, 50, RED)


@shot(S(51), push=0.04)
def s_not_only(c, t, a, b):
    dark_sea(c, t, 0.5)
    octopus(c, 960, 620, 0.9, t, camo=0.8 * clamp(1 - (t - a) / 1.5), camo_col="#2b5462")
    headline(c, t, a + 0.2, "BUT IT'S NOT ONLY CAMOUFLAGE", 150, 54)


# =================================================================== 5. BRAINS
@shot(S(52), push=0.04, dip=0.2)
def s_ch_brain(c, t, a, b):
    dark_sea(c, t, 0.6)
    brain_icon(c, 1380, 480, 150, a=0.85)
    chapter(c, t, a, 5, 5, "BRAINS", "IT IS ALSO SMART")


def _neuron_octo(c, t, active_arms=None, flick=False):
    with xf(c, 0, 0, alpha=0.45):
        octopus_spread(c, 960, 560, 0.95, t, col="#3f8fa3", amp=0.04)
    glow(c, 960, 490, 110, "#f39bb2", 0.6)
    brain_icon(c, 960, 490, 46)
    rnd = random.Random(1)
    for i in range(8):
        ang = math.radians(-90 + 22.5 + i * 45)
        on = 1.0
        if flick:
            on = 1.0 if math.sin(t * (3 + i * 0.7) + i * 2) > 0.3 else 0.25
        for k in range(14):
            d = 110 + k * 26 * 0.95
            px = 960 + math.cos(ang) * d * 0.95 + rnd.uniform(-8, 8)
            py = 560 + math.sin(ang) * d * 0.95 + rnd.uniform(-8, 8)
            if active_arms is not None and k / 14 > active_arms:
                continue
            c.drawCircle(px, py, 6, P("#fff2a8", a=0.9 * on))
            glow(c, px, py, 18, "#fff2a8", 0.35 * on)


@shot(S(53), push=0.03)
def s_neurons(c, t, a, b):
    blueprint(c, t)
    _neuron_octo(c, t, active_arms=clamp((t - WT(53, "neurons")) / 2.0))
    leader(c, 990, 470, 1300, 260, "CENTRAL BRAIN", at(t, WT(53, "central"), 0.5), "#f39bb2", 32)
    pop_text(c, t, WT(53, "most"), "MOST NEURONS LIVE IN THE ARMS", W / 2, 1000, 44, WHITE)
    pop_text(c, t, WT(53, "hundreds"), "HUNDREDS OF MILLIONS", 420, 160, 40, AMBER)


@shot(S(54), push=0.03)
def s_arm_decide(c, t, a, b):
    blueprint(c, t)
    _neuron_octo(c, t, flick=True)
    pop_text(c, t, WT(54, "react"), "EACH ARM REACTS ON ITS OWN", W / 2, 140, 50, WHITE)
    pop_text(c, t, WT(54, "permission"), "NO PERMISSION NEEDED", W / 2, 1000, 40, AMBER)


@shot(S(55), push=0.05)
def s_nine(c, t, a, b):
    dark_sea(c, t, 0.5)
    diver(c, 1350, 420, 1.3, t, kick=0.2, beam=0.5)
    reach_arm(c, -60, 900, 1035, 560, t, w0=50, prog=smooth((t - WT(55, "touches") + 0.4) / 0.8), under=-1,
              curl_tip=3.0)
    if t < S(56):
        pop_text(c, t, WT(55, "one"), "NOT ONE MIND...", 520, 200, 56, WHITE)
    else:
        tint(c, "#071822", 0.6 * fade(t, S(56)))
        kb = back_out(at(t, S(56), 0.4))
        brain_icon(c, 960, 420, 80 * kb)
        for i in range(8):
            ki = back_out(at(t, WT(56, "nine") + i * 0.06, 0.3))
            brain_icon(c, 600 + i * 103, 640, 34 * ki)
        pop_text(c, t, WT(56, "nine"), "NINE.", W / 2, 860, 110, RED)


@shot(S(57), push=0.03)
def s_hearts(c, t, a, b):
    ocean(c, t, rays=0.4)
    th = WT(57, "three")
    for i in range(3):
        k = back_out(at(t, th + i * 0.12, 0.35))
        beat = 1 + 0.12 * max(0, math.sin(t * 7 + i))
        if k > 0:
            heart(c, 400 + i * 230, 420, 70 * k * beat, "#3a7bff")
    if t > th:
        spaced(c, "3 HEARTS", 630, 600, 50, WHITE, "Black", "center", fade(t, th), 0.06)
    tb = WT(57, "blue")
    if t > tb:
        k = back_out(at(t, tb, 0.4))
        from gfx import drop
        drop(c, 1350, 430, 90 * k, "#3a7bff")
        spaced(c, "BLUE BLOOD", 1350, 600, 50, CYAN, "Black", "center", fade(t, tb), 0.06)
    for i, (sym, name, st, x, bad) in enumerate(((("Cu", "COPPER", WT(57, "copper"), 760, False)),
                                                  ("Fe", "IRON", WT(57, "iron"), 1160, True))):
        if t < st:
            continue
        k = back_out(at(t, st, 0.35))
        with xf(c, x, 820, s=k):
            rrect(c, -90, -90, 180, 180, 14, "#c46f3c" if not bad else "#6b7378")
            text(c, sym, 0, 30, 90, WHITE, "Black")
            spaced(c, name, 0, 140, 30, WHITE, "ExtraBold", "center", 1, 0.08)
        if bad:
            cross_mark(c, x, 820, 1.1 * ease_out(at(t, st + 0.25, 0.25)), RED)
        else:
            check_mark(c, x + 100, 740, 0.6, "#4fd18b", 1, clamp((t - st - 0.2) / 0.3))


@shot(S(58), push=0.04)
def s_cold(c, t, a, b):
    ocean(c, t, "#1f5a74", "#06202c", rays=0.3)
    thermometer(c, 560, 820, 520, 0.12 + 0.02 * math.sin(t * 2))
    spaced(c, "0-10°C", 560, 940, 40, CYAN, "Black", "center", 1, 0.05)
    octopus(c, 1250, 560, 0.75, t)
    rows = [(WT(58, "freezing"), "FREEZING WATER"), (WT(58, "low"), "LOW OXYGEN")]
    for i, (st, s) in enumerate(rows):
        if t > st:
            check_mark(c, 760, 300 + i * 90, 0.5, "#4fd18b", 1, clamp((t - st) / 0.3))
            spaced(c, s, 810, 316 + i * 90, 40, WHITE, "Black", "left", fade(t, st), 0.05)
    pop_text(c, t, WT(58, "works"), "BUILT FOR IT", 1250, 150, 50, AMBER)


@shot(S(59), push=0.04)
def s_problems(c, t, a, b):
    dark_sea(c, t, 0.4)
    octopus(c, 960, 640, 0.85, t, look=(0, -1))
    for i in range(5):
        sparkle(c, 960 + math.cos(t + i * 1.3) * 300, 300 + math.sin(t * 1.3 + i) * 80, 18, AMBER, 0.8, t * 40)
    headline(c, t, WT(59, "solve"), "THEY SOLVE PROBLEMS", 160, 66, WHITE)


@shot(S(60), push=0.03)
def s_jar(c, t, a, b):
    ocean(c, t, rays=0.5)
    tp = WT(60, "tell")
    if t < tp:
        k = smooth((t - WT(60, "open")) / 1.6)
        with xf(c, 960, 600):
            with xf(c, 0, 20, alpha=0.95):
                octopus(c, 0, 0, 0.42, t, L=260)
            jar(c, 0, 0, 1.3, lid_rot=25 * k, lid_off=90 * k)
        pop_text(c, t, WT(60, "inside"), "FROM THE INSIDE", W / 2, 150, 60, WHITE)
    else:
        cols = ["#e9dfcf", "#e9dfcf", "#e9dfcf"]
        for i in range(3):
            k = back_out(at(t, tp + i * 0.12, 0.35))
            person_icon(c, 560 + i * 400, 640, 1.8 * k, cols[i])
        if t > WT(60, "individual"):
            rrect(c, 960 - 140, 420, 280, 320, 20, AMBER, stroke=6, a=fade(t, WT(60, "individual")))
            label_box(c, 960, 840, "THAT ONE", 30, bg=AMBER, a=fade(t, WT(60, "individual")))
        pop_text(c, t, tp, "IT CAN TELL PEOPLE APART", W / 2, 180, 56, WHITE)


@shot(S(61), push=0.03, dip=0.2)
def s_otto(c, t, a, b):
    tsq, tsh, tbl = WT(61, "squirting"), WT(61, "short"), WT(61, "lights")
    out = clamp((t - tbl) / 0.15)
    c.drawRect(skia.Rect(0, 0, W, H), P("#2a2420"))
    rrect(c, 260, 360, 1400, 640, 10, "#1d4c5f")
    rrect(c, 260, 360, 1400, 120, 0, "#2a6276", a=0.6)
    lamp(c, 1300, 260, 1.0, on=0 if t > tsh + 0.4 else (1 if t < tsh or int(t * 20) % 2 else 0.2), t=t)
    octopus(c, 760, 800, 0.6, t, face=1, look=(1, -1))
    spaced(c, "OTTO", 560, 990, 34, AMBER, "Black", "center", 1, 0.15)
    if tsq < t < tsh + 0.4:
        for i in range(10):
            ph = ((t - tsq) * 1.5 + i / 10) % 1
            x = lerp(820, 1300, ph)
            y = 760 - math.sin(ph * math.pi) * 520 + ph * (260 - 260)
            y = lerp(760, 300, ph) - math.sin(ph * math.pi) * 160
            c.drawCircle(x, y, 9, P("#bfeaf5", a=0.9))
    if tsh < t < tsh + 0.6:
        for i in range(8):
            sparkle(c, 1300 + math.cos(i) * 60 * (t - tsh) * 4, 270 + math.sin(i * 1.7) * 60 * (t - tsh) * 4, 20,
                    "#fff3a0", 1, i * 20)
    card_frame(c, 300, 140, 420, 120, -4)
    with xf(c, 300, 140, rot=-4):
        spaced(c, "GERMANY · 1950s", 0, 14, 34, "#2a211a", "Black", "center", 1, 0.06, shadow=False)
    tint(c, "#000000", 0.92 * out)
    if t > tbl:
        pop_text(c, t, tbl + 0.1, "*CLICK*", W / 2, 560, 44, MUTED)


@shot(S(62), push=0.03)
def s_not_accident(c, t, a, b):
    c.drawRect(skia.Rect(0, 0, W, H), P("#030608"))
    headline(c, t, WT(62, "not"), "NOT AN ACCIDENT.", 560, 80, WHITE)


@shot(S(63), push=0.08)
def s_plan(c, t, a, b):
    c.drawRect(skia.Rect(0, 0, W, H), P("#030608"))
    eye_closeup(c, 1450, 560, 200, t, look=(-1, 0), a=fade(t, a, 0.8))
    pop_text(c, t, WT(63, "plan"), "A PLAN.", 560, 600, 130, RED)


# =================================================================== PART 2: LEGENDS
@shot(S(64), push=0.04, dip=0.35)
def s_question(c, t, a, b):
    ocean(c, t)
    reef(c, t, seed=9)
    diver(c, 520, 420, 0.75, t, beam=0.6)
    octopus(c, 1420, 620, 0.9, t, face=-1, look=(-1, -0.4))
    headline(c, t, WT(64, "obvious"), "THE OBVIOUS QUESTION", 140, 44, MUTED, end=S(65))
    pop_text(c, t, S(65) + 0.2, "HAS IT EVER TURNED ON HUMANS?", W / 2, 150, 58, WHITE)


@shot(S(66), push=0.04)
def s_not_legend(c, t, a, b):
    ocean(c, t)
    reef(c, t, seed=9)
    diver(c, 520, 420, 0.75, t, beam=0.6)
    octopus(c, 1420, 620, 0.9, t, face=-1)
    k = fade(t, WT(66, "legends") - 0.2, 0.6)
    c.drawRect(skia.Rect(0, 0, W, H), P("#e8d9b5", a=0.85 * k))
    pop_text(c, t, WT(66, "not"), "NOT LIKE THE LEGENDS", W / 2, 540, 70, "#3b2a1c" if k > 0.5 else WHITE)


def parchment(c):
    blit(c, cached("parch", lambda cc: (fill_shader(cc, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, W * 0.7,
                                                                                       ["#efe2bf", "#d8c08e", "#a9864f"],
                                                                                       [0, 0.7, 1])),
                                        [line(cc, 0, y, W, y + 20 * math.sin(y), "#8a6a3e", 1, 0.12)
                                         for y in range(0, H, 9)])))


@shot(S(67), push=0.04)
def s_kraken(c, t, a, b):
    parchment(c)
    INK = "#4a3523"
    for i in range(6):
        yy = 640 + i * 50
        p = skia.Path()
        p.moveTo(0, yy)
        for x in range(0, W + 60, 60):
            p.quadTo(x + 30, yy - 14, x + 60, yy)
        c.drawPath(p, P(INK, 3, 0.6))
    drag = smooth((t - WT(67, "dragging")) / 2.5)
    ship(c, 960, 560 + drag * 170, 0.9, rot=-12 * drag, col=INK)
    for i, (bx, ang, ph) in enumerate(((650, -1.2, 0), (820, -1.5, 1), (1120, -1.7, 2), (1280, -1.9, 3))):
        k = smooth((t - WT(67, "tentacled") - i * 0.2) / 1.2)
        if k > 0:
            draw_arm(c, bx, 900, ang, 520 * k, 0.4 if i % 2 else -0.4, 3.0 * (1 if i % 2 else -1), t, ph, 0.12, 0.2,
                     34, "#6b4a30", 1 if i % 2 else -1, True, scol="#e2cfa3")
    spaced(c, "HERE BE MONSTERS", W / 2, 160, 64, INK, "Black", "center", fade(t, a + 0.3), 0.08, shadow=False)
    spaced(c, "SAILORS' TALES", W / 2, 220, 28, "#6b5038", "Bold", "center", fade(t, WT(67, "sailors")), 0.2,
           shadow=False)


@shot(S(68), push=0.04)
def s_squid(c, t, a, b):
    dark_sea(c, t, 0.7, rays=0.2)
    k = ease_out(at(t, WT(68, "giant"), 1.0))
    squid(c, lerp(2200, 1100, k), 560, 0.9, t)
    if t > WT(68, "giant"):
        label_box(c, 1100, 860, "GIANT SQUID?", 36, a=fade(t, WT(68, "giant")))
    ti = WT(68, "imagination")
    if t > ti:
        kk = back_out(at(t, ti, 0.4))
        with xf(c, 440, 480, s=kk):
            for dx, dy, r in ((0, 0, 150), (-120, 30, 100), (120, 30, 100), (-60, -80, 100), (70, -80, 100)):
                c.drawCircle(dx, dy, r, P(WHITE, a=0.95))
            c.drawCircle(-120, 220, 30, P(WHITE))
            c.drawCircle(-160, 290, 18, P(WHITE))
            spaced(c, "IMAGINATION", 0, 14, 44, "#123b50", "Black", "center", 1, 0.06, shadow=False)
    headline(c, t, WT(68, "historians"), "WHAT HISTORIANS THINK", 140, 40, MUTED)


@shot(S(69), push=0.04)
def s_monster_story(c, t, a, b):
    dark_sea(c, t, 0.6)
    k = back_out(at(t, a, 0.5))
    with xf(c, 640, 560, s=k, rot=-3):
        rrect(c, -230, -320, 460, 640, 10, "#5a2e22")
        rrect(c, -205, -295, 410, 590, 6, "#e2c27a", stroke=4)
        spaced(c, "THE KRAKEN", 0, -200, 54, "#f1d9a0", "Black", "center", 1, 0.06, shadow=False)
        with xf(c, 0, 100, s=0.42):
            octopus(c, 0, 0, 1.0, t, col="#e2c27a")
    rows = [(WT(69, "hide"), "HIDES IN PLAIN SIGHT"), (WT(69, "grip"), "GRIPS WITH 8 ARMS")]
    for i, (st, s) in enumerate(rows):
        if t > st:
            check_mark(c, 1050, 420 + i * 100, 0.55, "#4fd18b", 1, clamp((t - st) / 0.3))
            spaced(c, s, 1110, 440 + i * 100, 40, WHITE, "Black", "left", fade(t, st), 0.05)
    pop_text(c, t, WT(69, "perfect"), "THE PERFECT MONSTER STORY", 1380, 760, 40, AMBER)


# =================================================================== ESCAPE OPTIONS
OPTS = ["SWIM AWAY", "DIVE DEEPER", "STAY PERFECTLY STILL", "PULL FREE"]


@shot(S(70), push=0.06, dip=0.3)
def s_worst(c, t, a, b):
    dark_sea(c, t, 0.85, rays=0.0)
    tint(c, "#3a0606", 0.35)
    narrow = 1 - 0.55 * smooth((t - WT(71, "problem")) / 0.6) if t > S(71) else 1
    eye_closeup(c, 1350, 560, 260, t, pupil=narrow, look=(-1, 0))
    diver(c, 420, 760, 0.35, t, beam=0.5)
    headline(c, t, WT(70, "worst"), "WORST CASE", 150, 50, RED, end=S(71))
    pop_text(c, t, WT(71, "problem"), "YOU = A PROBLEM", 600, 300, 64, WHITE)


@shot(S(72), push=0.03)
def s_options(c, t, a, b):
    dark_sea(c, t, 0.7, rays=0.1)
    ap = [WT(73, "down") + 0.2 + i * 0.3 for i in range(4)]
    headline(c, t, a + 0.1, "WHAT WOULD YOU ACTUALLY DO?", 150, 50, WHITE)
    options_list(c, t, 620, 380, OPTS, appear=ap)


def mini_opts(c, t, active, struck=(), strike_t=None):
    with xf(c, 60, 60, s=0.45, alpha=0.95):
        rrect(c, -30, -70, 860, 420, 16, "#04121a", a=0.75)
        options_list(c, t, 0, 0, OPTS, active=active, struck=struck, size=44, strike_t=strike_t)


@shot(S(74), push=0.03)
def s_opt_swim(c, t, a, b):
    ocean(c, t)
    reef(c, t, seed=10, a=0.7)
    tj = WT(75, "jet")
    if t < S(76):
        diver(c, lerp(1100, 700, smooth((t - a) / 6)), 440, 0.8, t, face=-1, kick=1.4, beam=0.0)
        if t > tj:
            k = ease_out(at(t, tj, 1.4))
            ox = lerp(1500, 600, k)
            for i in range(12):
                yy = 640 + (i - 6) * 16
                line(c, ox + 160, yy, ox + 160 + 600 * (1 - k * 0.5), yy, WHITE, 3, 0.35 * (1 - k * 0.3))
            octopus(c, ox, 640, 0.6, t, face=1, arms=[(-10 + i * 3, 1.15, 0, 0.15, 1 if i % 2 else -1, i) for i in range(8)],
                    amp=0.06, mtilt=-8)
            pop_text(c, t, tj, "JET PROPULSION", W / 2 + 160, 160, 60, AMBER)
    else:
        diver(c, 900, 520, 1.1, t, face=-1, kick=0.6, tired=1.0, beam=0.0)
        rows = [(WT(76, "heavy"), "HEAVY TANK", 840, 330), (WT(76, "flippers"), "FLIPPERS", 1500, 600),
                (WT(76, "tired"), "TIRED", 700, 800), (WT(76, "cold"), "COLD", 1100, 820)]
        for st, s, x, y in rows:
            if t > st:
                label_box(c, x, y, s, 34, bg=WHITE, a=fade(t, st, 0.2))
        pop_text(c, t, WT(77, "outrun"), "OUTRUN SOMETHING WITH NO LEGS?", W / 2 + 160, 150, 50, WHITE)
    mini_opts(c, t, 0, struck=(0,) if t > E(77) - 0.6 else (), strike_t={0: E(77) - 0.6})


@shot(S(78), push=0.03)
def s_opt_deep(c, t, a, b):
    k = clamp((t - a) / (S(80) - a))
    blit(c, cached("depth", lambda cc: fill_shader(cc, skia.Rect(0, 0, W, H),
                                                     linear(0, 0, 0, H, ["#2a7390", "#0b3446", "#020a0f"]))))
    marine_snow(c, t)
    x0 = 1500
    line(c, x0, 140, x0, 980, WHITE, 3, 0.7)
    for i, d in enumerate((0, 100, 200, 300)):
        y = 140 + i * 280
        line(c, x0 - 16, y, x0 + 16, y, WHITE, 3)
        spaced(c, f"{d} M", x0 + 36, y + 10, 26, WHITE, "ExtraBold", "left", 0.9, 0.06)
    tl = WT(79, "live")
    if t > tl:
        kk = ease_out(at(t, tl, 1.6))
        rrect(c, x0 - 70, 140, 26, 840 * kk, 13, OCTO, a=0.9)
        spaced(c, "OCTOPUS RANGE", x0 - 90, 120 + 840 * kk, 24, OCTO_LT, "Black", "right", kk, 0.08)
    dy = lerp(240, 900, smooth(k))
    diver(c, 760, dy, 0.6, t, rot=40, beam=0.3)
    line(c, x0 - 30, dy, x0, dy, AMBER, 4)
    if t > S(80):
        octopus(c, 1100, 900, 0.7, t, face=-1, look=(-1, -0.5), a=fade(t, S(80), 0.8))
    pop_text(c, t, S(80) + 0.2, "GOING DEEPER IS NOT HIDING", 860, 330, 50, WHITE, end=S(81))
    pop_text(c, t, WT(81, "kitchen") - 0.1, "IT'S WALKING INTO ITS KITCHEN", 860, 330, 50, RED)
    mini_opts(c, t, 1, struck=(0,) + ((1,) if t > E(81) - 0.5 else ()), strike_t={0: 0, 1: E(81) - 0.5})


@shot(S(82), push=0.03)
def s_opt_still(c, t, a, b):
    dark_sea(c, t, 0.5)
    reef(c, t, seed=11, a=0.7)
    dxx, dyy = 760, 460
    diver(c, dxx, dyy, 0.85, t, kick=0.0, beam=0.3, face=1)
    octopus(c, 1450, 700, 0.75, t, face=-1)
    tf = WT(84, "feel")
    if t > tf:
        for i in range(4):
            r = ((t - tf) * 220 + i * 90) % 360
            c.drawCircle(dxx + 40, dyy, r, P(CYAN, 3, 0.7 * (1 - r / 360)))
    if t > WT(84, "taste"):
        reach_arm(c, 1360, 760, dxx + 120, dyy + 30, t, w0=26, prog=smooth((t - WT(84, "taste")) / 0.8), under=-1)
    pop_text(c, t, WT(83, "need"), "IT DOESN'T NEED YOU TO MOVE", W / 2, 160, 50, WHITE, end=tf)
    pop_text(c, t, tf, "IT FEELS THE WATER MOVE", W / 2, 160, 50, CYAN)
    pop_text(c, t, WT(84, "taste"), "...AND TASTES YOU", W / 2, 240, 46, AMBER)
    mini_opts(c, t, 2, struck=(0, 1) + ((2,) if t > E(84) - 0.4 else ()), strike_t={2: E(84) - 0.4})


@shot(S(85), push=0.04)
def s_opt_pull(c, t, a, b):
    dark_sea(c, t, 0.55)
    tp = WT(85, "pull")
    pull = 60 * math.sin(max(0, t - tp) * 5) * (t > tp)
    diver(c, 760 + pull, 420, 1.0, t, face=-1, kick=1.6, beam=0.0)
    times = [a + 0.1, WT(86, "more", 0), WT(86, "more", 1), WT(86, "arms"), WT(86, "join"), WT(86, "in")]
    n = 0
    for i, st in enumerate(times):
        if t < st:
            continue
        n += 1
        reach_arm(c, 1900, 650 + i * 70, 1000 + pull + (i % 3) * 30, 470 + (i % 2) * 40, t, w0=34,
                  prog=clamp((t - st) / 0.4), under=1 if i % 2 else -1, curl_tip=3.2, ph=i)
    spaced(c, f"ARMS HOLDING YOU: {n}", W / 2, 1000, 44, RED if n > 2 else WHITE, "Black", "center", 1, 0.05)
    pop_text(c, t, WT(86, "more"), "THE MORE YOU PULL...", W / 2, 160, 50, WHITE)
    mini_opts(c, t, 3, struck=(0, 1, 2) + ((3,) if t > E(86) - 0.4 else ()), strike_t={3: E(86) - 0.4})


@shot(S(87), push=0.04)
def s_ink(c, t, a, b):
    dark_sea(c, t, 0.5)
    ti = WT(87, "cloud")
    octopus(c, 1350 + 400 * smooth((t - ti) / 1.5), 560, 0.8, t, face=-1, a=1 - 0.6 * fade(t, ti + 0.6))
    diver(c, 520, 460, 0.8, t, beam=0.6)
    if t > ti - 0.3:
        k = ease_out(at(t, ti - 0.3, 2.0))
        ink_cloud(c, 1150, 560, 200 + 900 * k, t, a=min(1, k * 1.5))
    pop_text(c, t, WT(87, "scare"), "SCARE IT...", W / 2, 160, 50, WHITE, end=ti + 0.5)
    pop_text(c, t, ti + 0.5, "BLACK INK", W / 2, 160, 64, WHITE)
    if t > S(88):
        tint(c, "#040608", 0.7 * fade(t, S(88)))
        pop_text(c, t, WT(88, "more"), "IT DOES MORE THAN HIDE IT", W / 2, 420, 50, WHITE)
        tsm = WT(89, "smell")
        if t > tsm:
            spaced(c, "YOUR SENSE OF SMELL", W / 2, 560, 36, MUTED, "Black", "center", fade(t, tsm), 0.1)
            lvl = 1 - 0.85 * ease_out(at(t, tsm + 0.3, 1.2))
            rrect(c, 660, 600, 600, 50, 25, "#203039")
            rrect(c, 660, 600, 600 * lvl, 50, 25, RED if lvl < 0.4 else AMBER)
            pop_text(c, t, tsm + 1.2, "DULLED", W / 2, 760, 60, RED)


@shot(S(90), push=0.06)
def s_alone(c, t, a, b):
    c.drawRect(skia.Rect(0, 0, W, H), P("#020507"))
    diver(c, 620, 560, 0.9, t, beam=0.5, kick=0.4)
    for i, (x, y) in enumerate(((1400, 380), (1650, 760), (1200, 860))):
        on = window(t, a + 1 + i * 1.2, a + 2 + i * 1.2, 0.2)
        for ex in (x, x + 34):
            c.drawCircle(ex, y, 8, P("#efd9a0", a=0.8 * on))
    pop_text(c, t, WT(90, "alone"), "ALONE IN THE DARK", W / 2, 160, 56, WHITE)
    pop_text(c, t, WT(90, "knows"), "IT KNOWS THIS PLACE. YOU DON'T.", W / 2, 960, 40, AMBER)


@shot(S(91), push=0.03)
def s_verdict(c, t, a, b):
    dark_sea(c, t, 0.7, rays=0.1)
    options_list(c, t, 620, 330, OPTS, struck=(0, 1, 2, 3), strike_t={0: 0, 1: 0, 2: 0, 3: 0})
    headline(c, t, WT(91, "verdict"), "THE HONEST VERDICT", 150, 50, AMBER)
    stamp(c, t, WT(93, "not"), "NOT MUCH YOU COULD DO", W / 2, 860, 62, RED, -4)


@shot(S(94), push=0.05, dip=0.25)
def s_but(c, t, a, b):
    k = fade(t, S(95), 1.0)
    ocean(c, t, mixhex(DARK_TOP, SEA_TOP, k), mixhex(DARK_BOT, SEA_BOT, k), rays=k)
    headline(c, t, WT(94, "surprising"), "BUT HERE'S THE SURPRISE", 420, 52, MUTED, end=S(95))
    pop_text(c, t, WT(95, "never"), "IT ALMOST NEVER DOES.", W / 2, 560, 90, WHITE)


@shot(S(96), push=0.03)
def s_no_pattern(c, t, a, b):
    blueprint(c, t)
    x0, y0, w, h = 300, 820, 1320, 500
    line(c, x0, y0, x0 + w, y0, WHITE, 3)
    line(c, x0, y0, x0, y0 - h, WHITE, 3)
    k = ease_out(at(t, a + 0.3, 2.0))
    line(c, x0, y0 - 6, x0 + w * k, y0 - 6, "#4fd18b", 8)
    spaced(c, "OCTOPUSES HUNTING PEOPLE", x0, y0 - h - 30, 30, MUTED, "Bold", "left", 1, 0.08)
    spaced(c, "TIME", x0 + w, y0 + 50, 26, MUTED, "Bold", "right", 1, 0.1)
    pop_text(c, t, WT(96, "pattern"), "NO PATTERN. AT ALL.", W / 2, 500, 70, WHITE)


@shot(S(97), push=0.03)
def s_divers_map(c, t, a, b):
    ocean(c, t, rays=0.3)
    pins = [(-0.3, -0.35, "BRITISH COLUMBIA", WT(97, "british")), (0.02, 0.1, "PUGET SOUND", WT(97, "puget"))]
    rnd = random.Random(5)
    for i in range(14):
        pins.append((rnd.uniform(-0.45, 0.1), rnd.uniform(-0.5, 0.6), "", WT(97, "meet") + i * 0.1))
    map_card(c, t, W / 2, 560, 1300, 760, "DIVERS MEET THEM ALL THE TIME", pins, a=fade(t, a))


@shot(S(98), push=0.04)
def s_backs_off(c, t, a, b):
    ocean(c, t)
    reef(c, t, seed=12)
    rock(c, 1350, 640, 1000, 620, 21, ROCK, ROCK_HI)
    c.drawOval(skia.Rect(1180, 600, 1520, 860), P("#02070a"))
    tc, tb = WT(98, "changes"), WT(98, "backs")
    flash = math.sin(clamp((t - tc) / 1.2) * math.pi) if t > tc else 0
    k = smooth((t - tb) / 1.5)
    octopus(c, lerp(900, 1350, k), lerp(600, 730, k), lerp(0.75, 0.35, k), t,
            col=mixhex(OCTO, "#f2e0d0", flash * 0.8), face=1, a=1 - 0.3 * k)
    diver(c, 360, 380, 0.55, t, beam=0.5)
    pop_text(c, t, tc, "CHANGES COLOUR", 620, 160, 44, WHITE, end=tb + 0.2)
    pop_text(c, t, tb, "BACKS INTO ITS DEN", 620, 160, 44, WHITE, end=WT(98, "watches"))
    pop_text(c, t, WT(98, "watches"), "...AND WATCHES", 620, 160, 50, AMBER)


@shot(S(99), push=0.05)
def s_glove(c, t, a, b):
    dark_sea(c, t, 0.4)
    with xf(c, 1300, 520, s=3.0):
        line(c, 200, -40, 40, 0, "#16191d", 26)
        rrect(c, -10, -20, 60, 40, 18, "#2a2f35")
        for i in range(4):
            rrect(c, -40, -18 + i * 10, 40, 9, 4.5, "#2a2f35")
    reach_arm(c, -40, 820, 1170, 530, t, w0=46, prog=smooth((t - a) / 2.0) * 0.98, under=-1, curl_tip=1.4, amp=0.04)
    pop_text(c, t, WT(99, "gently"), "GENTLY.", 520, 220, 70, WHITE)
    pop_text(c, t, WT(99, "glove"), "JUST CURIOUS", 520, 300, 40, AMBER)


@shot(S(100), push=0.03)
def s_rare(c, t, a, b):
    blueprint(c, t)
    spaced(c, "HOW OFTEN?", W / 2, 300, 40, MUTED, "Black", "center", 1, 0.1)
    x0, w = 460, 1000
    rrect(c, x0, 480, w, 70, 35, "#203039")
    k = ease_out(at(t, WT(100, "rare"), 0.8))
    rrect(c, x0, 480, max(70, w * 0.04 * k + 70 * (k > 0)), 70, 35, "#4fd18b")
    spaced(c, "NEVER", x0, 620, 28, MUTED, "Bold", "left", 1, 0.1)
    spaced(c, "ALWAYS", x0 + w, 620, 28, MUTED, "Bold", "right", 1, 0.1)
    pop_text(c, t, WT(100, "happen"), "IT CAN HAPPEN", W / 2, 820, 50, WHITE)
    pop_text(c, t, WT(100, "rare"), "BUT IT'S RARE", W / 2, 900, 60, "#4fd18b")


@shot(S(101), push=0.04)
def s_pov(c, t, a, b):
    ocean(c, t)
    reef(c, t, seed=13, a=0.8)
    diver(c, 960, 520, 1.4, t, face=-1, beam=0.0, kick=0.6)
    bubbles(c, 820, 500, t, n=12, spread=40, rise=420, size=14)
    # fisheye octopus-POV mask
    c.save()
    hole = skia.Path()
    hole.addOval(skia.Rect(160, 20, W - 160, H - 20))
    c.clipPath(hole, skia.ClipOp.kDifference, True)
    c.drawRect(skia.Rect(0, 0, W, H), P("#02070a"))
    c.restore()
    spaced(c, "OCTOPUS POV", 220, 90, 26, AMBER, "Black", "left", 1, 0.15)
    pop_text(c, t, WT(101, "strange"), "A STRANGE, BUBBLING VISITOR", W / 2, 980, 48, WHITE)


@shot(S(102), push=0.04)
def s_fly(c, t, a, b):
    ocean(c, t, rays=0.4)
    octopus(c, 760, 600, 0.9, t, look=(1, -1))
    fx = 1350 + math.sin(t * 3.1) * 200
    fy = 400 + math.sin(t * 4.3) * 120
    fly(c, fx, fy, 2.2, t)
    spaced(c, "YOU", fx, fy + 100, 30, WHITE, "Black", "center", 1, 0.1)
    pop_text(c, t, WT(102, "fly"), "YOU ARE THE FLY", W / 2, 150, 58, AMBER)


@shot(S(103), push=0.03)
def s_flip(c, t, a, b):
    dark_sea(c, t, 0.6)
    octopus(c, 1400, 600, 0.75, t, face=-1)
    person_icon(c, 450, 640, 1.8, "#e9dfcf")
    k = smooth((t - WT(103, "other")) / 0.6)
    y = 600
    x1, x2 = lerp(1150, 650, k), lerp(650, 1150, k)
    line(c, x1, y, x2, y, RED, 14)
    ang = 0 if x2 > x1 else math.pi
    c.drawPath(poly([(x2, y - 34), (x2, y + 34), (x2 + 50 * math.cos(ang), y)]), P(RED))
    spaced(c, "DANGER", 900, y - 50, 40, RED, "Black", "center", 1, 0.12)
    pop_text(c, t, WT(103, "real"), "THE REAL DANGER", W / 2, 160, 56, WHITE)


@shot(S(104), push=0.03, dip=0.2)
def s_lifespan(c, t, a, b):
    blueprint(c, t)
    x0, w = 360, 1200
    line(c, x0, 600, x0 + w, 600, WHITE, 3)
    for y in range(6):
        x = x0 + y * w / 5
        line(c, x, 585, x, 615, WHITE, 3)
        spaced(c, f"{y}", x, 660, 30, WHITE, "ExtraBold", "center", 1, 0)
    spaced(c, "YEARS", x0 + w, 720, 24, MUTED, "Bold", "right", 1, 0.1)
    k = ease_out(at(t, WT(104, "lives"), 1.2))
    rrect(c, x0, 500, w * 0.6 * k, 60, 30, OCTO)
    if t > WT(104, "3"):
        rrect(c, x0 + w * 0.6, 500, w * 0.4 * ease_out(at(t, WT(104, "5"), 0.6)), 60, 30, OCTO, a=0.45)
    pop_text(c, t, WT(104, "only"), "A WHOLE LIFE: 3-5 YEARS", W / 2, 300, 60, WHITE)


@shot(S(105), push=0.04)
def s_male(c, t, a, b):
    dark_sea(c, t, 0.6)
    k = smooth((t - WT(105, "weakens")) / 2.5)
    octopus(c, 960, 520 + 220 * k, 0.85, t * (1 - k * 0.8), col=mixhex(OCTO, "#7a7a7a", k), a=1 - 0.6 * k,
            blink=k * 0.8, amp=0.16 * (1 - k))
    pop_text(c, t, WT(105, "male"), "THE MALE", W / 2, 160, 50, WHITE, end=WT(105, "weakens"))
    pop_text(c, t, WT(105, "weakens"), "WEAKENS... AND DIES", W / 2, 160, 50, MUTED)


def den_scene(c, t, mother_a=1.0, hatch=0.0, grey=0.0, blow=0.0):
    dark_sea(c, t, 0.75, rays=0.0)
    blit(c, cached("den_bg", lambda cc: (rock(cc, 960, 120, 2400, 600, 5, ROCK2, ROCK),
                                         rock(cc, 960, 1060, 2400, 400, 6, ROCK2, ROCK)), clear=None))
    egg_strands(c, 1150, 260, n=12, L=240, t=t, hatch=hatch)
    octopus(c, 620, 640, 0.85, t, col=mixhex(OCTO, "#8a8a8a", grey), a=mother_a, look=(1, -0.6), amp=0.08)
    if blow > 0:
        for i in range(30):
            ph = (t * 0.7 + i / 30) % 1
            x = lerp(760, 1700, ph)
            y = 380 + (i % 6) * 40 + math.sin(ph * 6 + i) * 20
            c.drawCircle(x, y, 4, P("#bfeaf5", a=0.6 * blow * (1 - ph)))


@shot(S(106), push=0.03)
def s_female(c, t, a, b):
    den_scene(c, t)
    pop_text(c, t, WT(106, "female"), "THE FEMALE", W / 2, 120, 44, MUTED)
    counter(c, t, WT(106, "tens"), 1.4, 0, 10000, 1150, 650, 70, "{:,}", AMBER, "+")
    if t > WT(106, "eggs"):
        spaced(c, "EGGS", 1150, 710, 28, WHITE, "Black", "center", fade(t, WT(106, "eggs")), 0.08)
    pop_text(c, t, WT(106, "months"), "GUARDED FOR MONTHS", W / 2, 960, 50, WHITE)


@shot(S(107), push=0.04)
def s_vigil(c, t, a, b):
    den_scene(c, t, blow=fade(t, WT(109, "blows")))
    pop_text(c, t, WT(107, "leave"), "SHE DOES NOT LEAVE.", 560, 230, 46, WHITE, end=S(109))
    pop_text(c, t, WT(108, "eat"), "SHE DOES NOT EAT.", 560, 310, 46, WHITE, end=S(109))
    pop_text(c, t, WT(109, "cleans"), "CLEANS THEM", 560, 230, 46, WHITE)
    pop_text(c, t, WT(109, "fresh"), "BLOWS FRESH WATER OVER THEM", 500, 310, 38, CYAN)
    if t > S(107):
        days = int(lerp(1, 180, clamp((t - S(107)) / (S(110) - S(107)))))
        spaced(c, f"DAY {days}", 1700, 960, 40, AMBER, "Black", "right", 1, 0.08)


@shot(S(110), push=0.03)
def s_hatch(c, t, a, b):
    th = WT(110, "hatch")
    hk = clamp((t - th) / 1.5)
    gk = smooth((t - WT(110, "dies")) / 2.5)
    den_scene(c, t, mother_a=1 - 0.75 * gk, hatch=hk, grey=gk)
    rnd = random.Random(3)
    for i in range(int(40 * hk)):
        bx = 1150 + rnd.uniform(-220, 220)
        by = 400 + rnd.uniform(0, 200) - (t - th) * rnd.uniform(60, 140)
        paralarva(c, bx + math.sin(t * 2 + i) * 20, by, 0.9, t + i)
    pop_text(c, t, th, "THE EGGS HATCH", W / 2, 120, 48, WHITE, end=WT(110, "dies"))
    pop_text(c, t, WT(110, "dies"), "...AND SHE DIES TOO", W / 2, 120, 48, MUTED)


@shot(S(111), push=0.05)
def s_never_meets(c, t, a, b):
    ocean(c, t, rays=1.2)
    rnd = random.Random(8)
    for i in range(40):
        x = rnd.uniform(200, 1700)
        y = rnd.uniform(300, 1100) - (t - a) * rnd.uniform(40, 90)
        paralarva(c, x + math.sin(t + i) * 30, y, rnd.uniform(0.8, 1.4), t + i)
    pop_text(c, t, WT(111, "never"), "SHE NEVER MEETS HER CHILDREN", W / 2, 540, 60, WHITE)


@shot(S(112), push=0.02, dip=0.2)
def s_threats(c, t, a, b):
    dark_sea(c, t, 0.6, rays=0.1)
    headline(c, t, WT(112, "threats"), "AND THE THREATS ARE GROWING", 130, 50, RED)
    panels = [(WT(113, "fishing"), "FISHING GEAR"), (WT(113, "crab"), "CRAB TRAPS"), (WT(113, "heat"), "OCEAN HEAT WAVES")]
    for i, (st, lab) in enumerate(panels):
        if t < st - 0.1:
            continue
        k = ease_out(at(t, st - 0.1, 0.4))
        x = 340 + i * 620
        with xf(c, x, 580 + (1 - k) * 60, alpha=k):
            rrect(c, -270, -330, 540, 620, 12, "#0e2f3e")
            c.save()
            c.clipRect(skia.Rect(-270, -330, 270, 290))
            if i == 0:
                net(c, -270, -330, 540, 620)
                octopus(c, 0, 40, 0.4, t)
                net(c, -200, -200, 400, 400, 0.9)
            elif i == 1:
                with xf(c, 0, 60):
                    trap(c, 0, 0, 1.4)
                    octopus(c, 0, 20, 0.28, t)
            else:
                fill_shader(c, skia.Rect(-270, -330, 270, 290), linear(0, -330, 0, 290, [("#e2552f", 0.75), ("#0e2f3e", 0.2)]))
                thermometer(c, 0, 180, 380, 0.85, RED)
            c.restore()
            spaced(c, lab, 0, 250, 30, WHITE, "Black", "center", 1, 0.08)


@shot(S(114), push=0.04)
def s_monster(c, t, a, b):
    ocean(c, t)
    reef(c, t, seed=14)
    octopus(c, 960, 600, 1.0, t)
    stamp(c, t, WT(114, "monster"), "MONSTER?", W / 2, 250, 80, RED, 0)
    if t > WT(114, "this"):
        strike(c, 660, 222, 1260, (t - WT(114, "this")) / 0.4, WHITE, 12)
    pop_text(c, t, WT(114, "holds"), "IT HOLDS ITS PART OF THE OCEAN TOGETHER", W / 2, 1000, 40, AMBER)


@shot(S(115), push=0.02)
def s_food_web(c, t, a, b):
    ocean(c, t, rays=0.5)
    cx, cy = 960, 560
    c.drawCircle(cx, cy, 150, P("#0a2633"))
    c.drawCircle(cx, cy, 150, P(OCTO_LT, 4))
    octopus(c, cx, cy - 10, 0.36, t, L=330)
    nodes = [(WT(115, "crabs"), "CRABS", 520, 900, lambda x, y: crab(c, x, y, 0.8, t), True),
             (WT(115, "shrimp"), "SHRIMP", 960, 950, lambda x, y: shrimp(c, x + 20, y, 1.4), True),
             (WT(115, "otters"), "SEA OTTERS", 420, 220, lambda x, y: otter(c, x, y, 0.7), False),
             (WT(115, "seals"), "SEALS", 960, 170, lambda x, y: seal(c, x, y, 0.6, t=t), False),
             (WT(115, "sharks"), "SHARKS", 1500, 220, lambda x, y: shark(c, x, y, 0.4, t, kind="dogfish"), False),
             (WT(115, "crabs") + 0.3, "CLAMS", 1400, 900, lambda x, y: clam(c, x, y + 10, 1.0), True)]
    for st, lab, x, y, fn, prey in nodes:
        if t < st - 0.1:
            continue
        k = ease_out(at(t, st - 0.1, 0.5))
        # arrow points from food to eater
        if prey:
            fx, fy, tx, ty = x, y - 60, lerp(x, cx, 0.68), lerp(y - 60, cy + 150, 0.9)
        else:
            fx, fy, tx, ty = cx + (x - cx) * 0.25, cy - 150, lerp(cx, x, 0.85), y + 70
        ex, ey = lerp(fx, tx, k), lerp(fy, ty, k)
        line(c, fx, fy, ex, ey, WHITE, 4, 0.7)
        ang = math.atan2(ey - fy, ex - fx)
        c.drawPath(poly([(ex + math.cos(ang) * 16, ey + math.sin(ang) * 16),
                         (ex + math.cos(ang + 2.4) * 16, ey + math.sin(ang + 2.4) * 16),
                         (ex + math.cos(ang - 2.4) * 16, ey + math.sin(ang - 2.4) * 16)]), P(WHITE, a=0.7))
        with xf(c, 0, 0, alpha=k):
            fn(x, y)
        spaced(c, lab, x, y + (80 if prey else -90), 26, WHITE, "Black", "center", k, 0.08)
    if t > S(116):
        kk = ease_out(at(t, S(116), 0.5))
        c.drawCircle(cx, cy, 150 + 30 * kk, P(AMBER, 5, kk))
        label_box(c, cx + 480, cy + 10, "THE MIDDLE OF THE FOOD WEB", 30, bg=AMBER, a=kk)


# =================================================================== OUTRO
@shot(S(117), push=0.05, dip=0.35)
def s_callback(c, t, a, b):
    ocean(c, t)
    reef(c, t, seed=1)
    diver(c, lerp(500, 1000, (t - a) / (b - a)), 430, 0.75, t, beam=0.6)
    headline(c, t, WT(117, "nothing"), "\"NOTHING IN THE SEA IS LOOKING FOR US\"", 150, 44, WHITE)
    pop_text(c, t, WT(118, "mostly"), "MOSTLY TRUE.", W / 2, 240, 50, AMBER)


@shot(S(119), push=0.07)
def s_somewhere(c, t, a, b):
    ocean(c, t, GREEN_TOP, GREEN_BOT, rays=0.2)
    rnd = random.Random(21)
    for i in range(12):
        rock(c, rnd.uniform(0, W), rnd.uniform(640, 1080), rnd.uniform(300, 500), rnd.uniform(200, 320), 500 + i,
             "#0d2a24", "#173d33")
    lv = S(121) + 0.5
    k_leave = smooth((t - lv) / 2.0)
    x, y = 1300 + 500 * k_leave, 720
    if t < lv:
        rock(c, x, y, 360, 230, 777, "#0d2a24", "#173d33")
        op = smooth((t - (S(120) + 0.4)) / 0.4)
        for ex in (x - 30, x + 40):
            c.drawCircle(ex, y - 40, 15 * op, P("#efd9a0"))
            if op > 0.2:
                rrect(c, ex - 10, y - 43, 20, 6, 3, "#08090b")
    else:
        octopus(c, x, y - 40, 0.6, t, face=1, camo=1 - k_leave, camo_col="#173d33")
    stats = [(WT(120, "nine"), "9 BRAINS"), (WT(120, "three"), "3 HEARTS"), (WT(120, "two"), "2,000 TASTING FINGERS")]
    for i, (st, s) in enumerate(stats):
        if t > st:
            spaced(c, s, 140, 260 + i * 80, 48, AMBER if i == 2 else WHITE, "Black", "left", fade(t, st), 0.05)
    pop_text(c, t, WT(120, "watching"), "IS WATCHING.", 140 + spaced_w("IS WATCHING.", 64) / 2, 560, 64, RED)
    pop_text(c, t, WT(121, "better"), "IT JUST HAS BETTER THINGS TO DO", W / 2, 960, 44, WHITE)


@shot(S(122), push=0.03, dip=0.3)
def s_thanks(c, t, a, b):
    ocean(c, t)
    reef(c, t, seed=15, a=0.7)
    octopus(c, 1500, 640, 0.7, t, face=-1)
    pop_text(c, t, a + 0.1, "THANKS FOR WATCHING", W / 2 - 200, 300, 70, WHITE)
    if t > WT(123, "sea"):
        comment_box(c, W / 2 - 200, 520, 900, "Which sea creature should be next?", (t - WT(123, "sea")) / 1.8)
    pop_text(c, t, WT(124, "read"), "I DO READ THEM.", W / 2 - 200, 760, 50, AMBER)


SHOTS.sort(key=lambda s: s[0])


def render_frame(c, t):
    idx = 0
    for i, s in enumerate(SHOTS):
        if s[0] <= t:
            idx = i
    a, fn, push, dip, drift = SHOTS[idx]
    b = SHOTS[idx + 1][0] if idx + 1 < len(SHOTS) else 10_000
    if b > 9999:
        b = a + 12
    c.clear(C("#000000"))
    k = clamp((t - a) / max(0.1, b - a))
    sc = 1 + push * smooth(k)
    dx = math.sin(t * 0.7) * 5 * drift
    dy = math.cos(t * 0.53) * 4 * drift
    c.save()
    c.translate(W / 2 + dx, H / 2 + dy)
    c.scale(sc * 1.012, sc * 1.012)
    c.translate(-W / 2, -H / 2)
    fn(c, t, a, b)
    c.restore()
    vignette(c, 0.5)
    grain(c, t, 0.045)
    # dip from black at the start of flagged shots; quick 4-frame soften on hard cuts
    if dip > 0 and t - a < dip:
        tint(c, "#000000", 1 - (t - a) / dip)
    # fade out at the very end
    end = TR[-1]["end"] + 1.2
    if t > end - 1.0:
        tint(c, "#000000", clamp((t - (end - 1.0)) / 1.0))
