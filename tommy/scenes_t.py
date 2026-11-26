"""Timeline for 'If you were born as Tommy Vercetti' (6:34)."""
import math
import random

import skia

from common import *  # noqa: F401,F403
from common import shot, wt, marker_circle, screen_space
from sets import neon
import sets_t  # noqa: F401  (registers extra sets)

TV = "tommy_v"


def tint_c(c, col, a):
    c.drawRect(skia.Rect(0, 0, W, H), P(col, a=a))


def tommy(c, x, y, lk=TV, pose="stand", expr="neutral", t=0.0, s=1.3, **kw):
    person(c, x, y, "tommy_v", lk, pose, expr, t, s=s, **kw)


def newspaper(c, x, y, s, t, rot=-6, head="HARWOOD BUTCHER"):
    with xf(c, x, y, s=s, rot=rot):
        box(c, -330, -230, 660, 460, "#efe8d6", r=4)
        T(c, "LIBERTY TREE", 0, -170, 44, "#1d1d1d", SERIF)
        line(c, -300, -150, 300, -150, "#1d1d1d", 3)
        T(c, "1971", -270, -120, 22, "#1d1d1d", "interb", align="left")
        T(c, head, 0, -60, 58, "#1d1d1d", LUCKY)
        T(c, "11 DEAD IN HARWOOD", 0, -10, 30, "#a3261e", "inter")
        box(c, -300, 20, 260, 180, "#c9c2b0", r=2, ow=3)
        with xf(c, -170, 150):
            head_ = None
        for j in range(7):
            rect(c, -10, 30 + j * 24, 300 if j % 3 else 240, 8, "#9a9488")


def briefcase(c, x, y, s=1.0, open_=0.0):
    poi(c, x, y, 90 * s, "ui")
    with xf(c, x, y, s=s):
        box(c, -110, -60, 220, 130, "#3a2a1e", r=10)
        box(c, -40, -82, 80, 26, "#2a1a12", r=8)
        line(c, -110, 0, 110, 0, "#5a4a3a", 4)
        oval(c, -60, -10, 8, 8, "#c9a24a", ow=2)
        oval(c, 60, -10, 8, 8, "#c9a24a", ow=2)
        if open_ > 0:
            for i in range(5):
                cash(c, -70 + i * 35, -60 - open_ * 40 - (i % 2) * 10, 0.8, rot=-10 + i * 5)


def gunfire(c, x, y, t, a=1.0, n=3):
    if int(t * 14) % 2:
        for k in range(n):
            burst(c, x + k * 40, y - k * 25, 28, "#ffd23f", t, a)


# ======================================================================= HOOK
@shot(0.0, 6.0, "GTA VICE CITY · 1986")
def t_hook(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "cell")
        tommy(c, 760, 1520, "tommy_p", "cross", "angry", t, s=2.6, look=(2, 0))
        with xf(c, 0, -H * (1 - ease_out(at(t, 0.1, 0.7)))):
            bars(c, 260, 1660, -40, H + 40, n=10, col="#6c7784")
    tag(c, 1280, 260, "TOMMY VERCETTI", 46, a=fade(t, 0.6), s=pop(t, 0.6))
    k = pop(t, wt("15", 2.4), 0.35)
    if k > 0:
        with screen_space(c):
            with xf(c, 1450, 560, s=k):
                box(c, -180, -110, 360, 220, "#f7f3ea", r=12, ow=6)
                T(c, "15", 0, 40, 120, "#d8262e", LUCKY)
                T(c, "YEARS", 0, 95, 34, "#141414", LUCKY)
    marker_text(c, "never visited", 1450, 820, 54, a=at(t, wt("visited", 5.0), 0.5), rot=-4)


@shot(6.0, 9.5)
def t_paradise(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "vice_sunset")
        tommy(c, 960, 1060, TV, "hips", "smirk", t, s=1.5)
        if t > wt("rob", 8.2) - 0.1:
            for i, x in enumerate((420, 1500)):
                person(c, x, 1060, "masked", "masked", "point", "angry", t, s=1.3, flip=(i == 1))
    tag(c, 960, 200, "PARADISE", 50, a=fade(t, wt("paradise", 6.8)), bg="#ffd23f")


@shot(9.5, 15.3)
def t_empire(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "mansion")
        tommy(c, 960, 1040, TV, "cross", "determined", t, s=1.45)
        if t < wt("build", 11.4):
            tint_c(c, "#000000", 0.55)
            draw_rubble(c, t)
    marker_text(c, "THE EMPIRE", 960, 220, 90, "#f4f0e6", a=at(t, wt("empire", 12.0), 0.5), rot=-3)
    tag(c, 960, 330, "BRICK BY BLOODY BRICK", 36, a=fade(t, wt("brick", 13.7)), bg="#ff8a8a")


def draw_rubble(c, t):
    rnd = random.Random(3)
    for _ in range(26):
        x, y = rnd.uniform(200, 1700), rnd.uniform(820, 1040)
        box(c, x, y, rnd.uniform(40, 90), rnd.uniform(20, 40), "#9a8a7a", r=4, ow=3)


# ======================================================================= LIBERTY CITY CHILDHOOD
@shot(15.3, 22.3, "LIBERTY CITY · 1950s")
def t_kid(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "liberty_street")
        x = lerp(300, 820, smooth(at(t, 15.6, 3.0)))
        person(c, x, 1010, "tommy_v", "tommy_kid", "walk" if t < 18.6 else "stand", "neutral", t, s=1.3,
               walk=t if t < 18.6 else 0)
        for k in range(30):
            rnd = random.Random(k)
            sx = (rnd.uniform(0, W) + t * 30) % W
            sy = (rnd.uniform(0, H) + t * 80) % H
            c.drawCircle(sx, sy, rnd.uniform(2, 4), P("#ffffff", a=0.8))
    tag(c, 820, 460, "YOU", 34, a=fade(t, 16.0))
    for i, (lab, tm) in enumerate((("COLD WINTERS", wt("cold", 19.9)), ("LOUD NEIGHBORS", wt("loud", 20.9)))):
        tag(c, 1400, 300 + i * 100, lab, 36, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1), rot=-3 + i * 5)


@shot(22.3, 29.5)
def t_suits(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "liberty_street")
        car(c, 1500, 1020, 0.85, "#1a1a20", t, kind="sedan")
        person(c, 1180, 1010, "goon", "goon", "cross", "smirk", t, s=1.25)
        person(c, 1360, 1010, "goon2", "goon2", "stand", "neutral", t, s=1.25)
        person(c, 520, 1010, "tommy_v", "tommy_kid", "stand", "shock" if t > 26.4 else "neutral", t, s=1.3,
               look=(4, 0))
        k = pop(t, wt("money", 25.0), 0.3)
        if k > 0:
            for i in range(4):
                cash(c, 1260 + (i - 2) * 50, 560 - i * 30 - (t - 25) * 30, 1.0 * k, rot=-15 + i * 10)
    tag(c, 1270, 330, "NEVER WORK. ALWAYS PAID.", 32, a=fade(t, wt("never", 23.0)))
    k = fade(t, wt("notice", 26.6))
    if k > 0:
        marker_circle(c, 1270, 720, 260, 360, at(t, wt("notice", 26.6), 0.7))
        marker_text(c, "you notice", 520, 430, 60, "#f4f0e6", a=k, rot=-5)


@shot(29.5, 39.8, "LIBERTY CITY · 1960s")
def t_errands(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "liberty_night")
        tommy(c, 760, 1010, "tommy_teen", "hold", "determined", t, s=1.3,
              prop=lambda c2: box(c2, -60, -170, 120, 90, "#b98a58", r=4, ow=4))
        person(c, 1250, 1010, "goon", "goon", "point", "smirk", t, s=1.3)
    tag(c, 1250, 360, "THE FORELLI FAMILY", 36, a=fade(t, wt("family", 32.4)))
    items = ["DELIVER A PACKAGE", "WATCH A DOOR", "KEEP YOUR MOUTH SHUT"]
    times = [wt("deliver", 34.0), wt("watch", 35.0), wt("keep", 36.0)]
    checklist(c, 1380, 520, items, t, times, size=40)
    k = fade(t, wt("too", 38.9))
    if k > 0:
        stamp(c, 560, 240, "TOO GOOD", 70, a=k, s=lerp(1.5, 1, ease_out(k)), rot=-8, color="#2e8b57")


@shot(39.8, 46.3)
def t_reliable(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "liberty_night")
        tommy(c, 960, 1040, "tommy_70", "cross", "neutral", t, s=1.5)
        for i, x in enumerate((420, 1500)):
            person(c, x, 1040, "goon" if i else "goon2", None, "stand", "smirk", t, s=1.3, talk=0.5)
    k = pop(t, wt("reliable", 40.6), 0.4)
    if k > 0:
        tag(c, 960, 260, "RELIABLE", 60, s=k, bg="#ffd23f")
    k = fade(t, wt("dangerous", 44.3))
    if k > 0:
        marker_text(c, "the most dangerous word", 960, 900, 60, a=k, rot=-3)


@shot(46.3, 55.0)
def t_sonny(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "lawyer")
        person(c, 1180, 1010, "sonny", "sonny", "hug" if t > wt("brother", 52.4) else "hips", "smile", t, s=1.4,
               talk=0.5 * window(t, 51.6, 53.0))
        tommy(c, 720, 1010, "tommy_70", "stand", "neutral", t, s=1.35)
    tag(c, 1180, 330, "SONNY FORELLI", 42, a=fade(t, wt("sonny", 47.8)), s=pop(t, wt("sonny", 47.8)))
    for i, (lab, tm) in enumerate((("SHARP SUIT", wt("sharp", 49.2)), ("BIG SMILE", wt("big", 49.9)),
                                   ("COLD EYES", wt("cold", 50.5)))):
        tag(c, 1560, 520 + i * 90, lab, 32, a=fade(t, tm - 0.05), s=pop(t, tm - 0.05), rot=-3,
            bg="#ff8a8a" if i == 2 else "#ffffff")
    k = fade(t, wt("least", 53.4))
    if k > 0:
        marker_text(c, "...that's what he says", 760, 330, 56, a=k, rot=-4)


# ======================================================================= HARWOOD 1971
@shot(55.0, 60.2, "HARWOOD · 1971")
def t_1971(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "harwood")
        x = lerp(200, 760, smooth(at(t, 57.4, 2.2)))
        tommy(c, x, 1020, "tommy_70", "walk" if 57.4 < t < 59.6 else "stand", "determined", t, s=1.3,
              walk=t if 57.4 < t < 59.6 else 0)
    big_title(c, "1971", 960, 400, 200, t, wt("1971", 55.9), "#f4f0e6")
    tag(c, 1400, 300, "ONE MAN. ONE JOB.", 36, a=fade(t, wt("one", 59.4)))


@shot(60.2, 66.7)
def t_trap(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, shake=0.2 * window(t, 65.3, 66.2, 0.1))
        draw_bg(c, "harwood")
        tommy(c, 960, 1040, "tommy_70", "stand", "shock" if t > 64 else "determined", t, s=1.3)
        n = 0 if t < wt("11", 65.3) else 11
        if t > wt("isn't", 63.2) and n == 0:
            n = 1
        rnd = random.Random(4)
        pos = [(260, 1000), (1660, 1000), (420, 980), (1500, 980), (140, 960), (1780, 960), (600, 960),
               (1330, 960), (330, 940), (1600, 940), (760, 940)]
        for k in range(n):
            x, y = pos[k]
            person(c, x, y, "goon" if k % 2 else "goon2", None, "point", "angry", t, s=1.0, flip=(x > 960))
    k = fade(t, wt("trap", 61.8) - 0.1)
    if k > 0:
        stamp(c, 960, 330, "IT'S A TRAP", 80, a=k, s=lerp(1.5, 1, ease_out(k)), rot=-6)
    big_title(c, "11.", 960, 360, 160, t, wt("11", 65.3), "#ff4a4a")


@shot(66.7, 70.9)
def t_alone(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "harwood")
        tint_c(c, "#2a0005", 0.3)
        x = lerp(960, 1300, smooth(at(t, 66.8, 1.8)))
        tommy(c, x, 1040, "tommy_70", "walk" if t < 68.6 else "stand", "angry", t, s=1.3, walk=t if t < 68.6 else 0)
    caption_serif(c, "You walk out alone.", 960, 1010, 56, a=fade(t, 66.8))


@shot(70.9, 74.9)
def t_butcher(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "dark")
        k = ease_out(at(t, 70.9, 0.6))
        newspaper(c, 960, 520, 1.25 * (0.6 + 0.4 * k), t, rot=-6 + (1 - k) * 360)
        if t > wt("handcuffs", 73.2):
            with xf(c, 1520, 820, s=pop(t, wt("handcuffs", 73.2), 0.35), rot=-12):
                for sx in (-1, 1):
                    c.drawCircle(sx * 60, 0, 50, P("#c9c9c9", 14))
                    c.drawCircle(sx * 60, 0, 50, P(OUT, 4))
                line(c, -10, 0, 10, 0, "#c9c9c9", 10)


@shot(74.9, 77.3, "LIBERTY CITY COURT")
def t_judge(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "court")
        person(c, 960, 760, "judge", "judge", "gavel", "angry", t, s=1.3, talk=0.5)
        box(c, 560, 600, 800, 80, "#5a3820", r=6, ow=6)
        tommy(c, 600, 1080, "tommy_70", "cuffed", "angry", t, s=1.3)
    k = pop(t, wt("15", 75.7), 0.35)
    if k > 0:
        stamp(c, 1400, 420, "15 YEARS", 90, s=k, rot=-8)


# ======================================================================= PRISON
@shot(77.3, 84.6, "LIBERTY CITY PENITENTIARY")
def t_talk(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "cell")
        for i, x in enumerate((360, 1560)):
            person(c, x, 1000, "inmate", "inmate", "point" if i == 0 else "pointl", "smirk", t, s=1.2, talk=0.7)
        tommy(c, 960, 1000, "tommy_p", "cross", "neutral", t, s=1.3)
    for i, (lab, tm, x) in enumerate((("EVERYONE TALKS", wt("talks", 79.6), 400), ("CUTS A DEAL", wt("deal", 80.9), 1520),
                                      ("GIVES UP A NAME", wt("name", 82.6), 960))):
        speech(c, x, 330 if i < 2 else 220, [lab], 34, a=fade(t, tm - 0.15), s=pop(t, tm - 0.15),
               tail=(40 if i == 0 else -40, 90))


@shot(84.6, 93.4)
def t_silence(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "cell")
        tommy(c, 760, 1520, "tommy_p", "cross", "determined", t, s=2.6, look=(2, 0))
    big_title(c, "YOU DON'T.", 1380, 300, 110, t, wt("don't", 84.8), "#f4f0e6")
    n = int(clamp((t - 86) / 6.5) * 15)
    with screen_space(c):
        for i in range(n):
            gx = 1180 + (i % 5) * 70
            gy = 520 + (i // 5) * 110
            if i % 5 == 4:
                line(c, gx - 260, gy + 70, gx + 10, gy + 10, "#f4f0e6", 8)
            else:
                line(c, gx, gy, gx, gy + 80, "#f4f0e6", 8)
        if n:
            T(c, f"{min(15, n)} YEARS", 1380, 900, 50, "#ffd23f", LUCKY, outline="#141414", ow=8)
    k = fade(t, wt("sonny", 87.6))
    if k > 0:
        marker_text(c, "NEVER SAYS: SONNY", 520, 220, 58, a=k, rot=-4)


@shot(93.4, 101.4, "SUBSCRIBE")
def t_subscribe(c, t, lt, d):
    with xf(c):
        draw_bg(c, "dark")
        with xf(c, 960, 520, rot=-1.5):
            box(c, -620, -380, 1240, 760, "#efe2c4", r=8)
            line(c, 0, -380, 0, 380, "#c9b89a", 6)
            T(c, "QUICK PAUSE", -310, -260, 56, "#2a1a12", LUCKY)
            T(c, "Who should be", -310, -150, 50, "#2a1a12", SERIF)
            T(c, "born next?", -310, -90, 50, "#2a1a12", SERIF)
            for i, nm_ in enumerate(("CJ", "Niko Bellic", "Claude", "Arthur Morgan")):
                k = fade(t, 95.0 + i * 0.5)
                box(c, -540, 0 + i * 80, 460, 62, "#ffffff", r=10, a=k, ow=3)
                T(c, nm_, -520, 42 + i * 80, 32, "#2a1a12", "interb", align="left", a=k)
                T(c, f"{(4 - i) * 3}.{i + 2}k", -110, 42 + i * 80, 26, "#d8262e", "interb", align="right", a=k)
            sb = wt("subscribe", 96.2)
            pressed = t > sb + 0.8
            k = pop(t, sb - 0.1, 0.4)
            with xf(c, 310, -60, s=k):
                box(c, -220, -60, 440, 120, "#8a8a8a" if pressed else "#d8262e", r=60, ow=6)
                T(c, "SUBSCRIBED" if pressed else "SUBSCRIBE", 0, 18, 50, "#ffffff", LUCKY)
            with xf(c, 310, 170, s=pop(t, wt("comments", 97.3), 0.4)):
                box(c, -230, -50, 460, 100, "#ffffff", r=18, ow=4)
                T(c, "Add a comment...", -200, 12, 32, "#8a8a8a", "interb", align="left")
            with xf(c, 310, 300, s=pop(t, wt("wins", 100.2), 0.4)):
                T(c, "MOST LIKED = NEXT LIFE", 0, 0, 34, "#d8262e", LUCKY)


# ======================================================================= 1986 RELEASE
@shot(101.4, 108.0, "1986")
def t_release(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "gate")
        from sets import set_gate_open
        set_gate_open(c, smooth(at(t, wt("gates", 102.6), 1.4)))
        if t > 102.8:
            x = lerp(960, 700, smooth(at(t, 103.0, 1.8)))
            tommy(c, x, 960, "tommy_70", "walk" if t < 104.8 else "stand", "neutral", t, s=1.25,
                  walk=t if t < 104.8 else 0)
    big_title(c, "1986", 960, 230, 140, t, 101.5, "#f4f0e6")
    tag(c, 700, 380, "AGE 35", 38, a=fade(t, wt("35", 104.5)))
    k = fade(t, wt("moved", 106.0))
    if k > 0:
        marker_text(c, "the world moved on", 1360, 520, 56, a=k, rot=-5)


@shot(108.0, 117.9)
def t_nervous(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "lawyer")
        person(c, 1200, 1010, "sonny", "sonny", "hug", "smile", t, s=1.4, talk=0.6 * window(t, 108.1, 117.4))
        tommy(c, 720, 1010, "tommy_70", "stand", "neutral", t, s=1.35)
        if t > wt("nervous", 114.8) - 0.4:
            for i, x in enumerate((240, 1650)):
                person(c, x, 1010, "goon2" if i else "goon", None, "cross", "worried", t, s=1.2)
    k = fade(t, wt("too", 110.4))
    if k > 0:
        marker_text(c, "a little TOO happy", 1200, 320, 54, a=k, rot=-4)
    tag(c, 960, 200, "CERTAIN PEOPLE: NERVOUS", 36, a=fade(t, wt("nervous", 114.8)), bg="#ff8a8a")
    k = pop(t, wt("idea", 116.8), 0.35)
    if k > 0:
        with xf(c, 1450, 520, s=k):
            lightbulb_(c, 0, 0)


def lightbulb_(c, x, y):
    glow(c, x, y, 120, "#ffe36b", 0.5)
    oval(c, x, y, 50, 56, "#ffe36b")
    box(c, x - 24, y + 50, 48, 36, "#9a9a9a", r=6, ow=4)


@shot(117.9, 128.2, "VICE CITY · 1986")
def t_vice(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "vice_sunset")
        if t > 119.3:
            tommy(c, 960, 1060, TV, "hips", "smirk", t, s=1.45)
    k = fade(t, 118.0, 0.4)
    if t < 120.0:
        neon(c, "Vice City", 960, 520, 220, "#ff5fa2", SCRIPT, a=k)
    for i, (lab, tm) in enumerate((("SUNSHINE", wt("sunshine", 119.5)), ("PALM TREES", wt("palm", 120.2)),
                                   ("NEON", wt("neon", 121.0)))):
        tag(c, 360 + i * 600, 220, lab, 40, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1), rot=-4 + i * 4)
    k = fade(t, wt("piece", 125.0))
    if k > 0:
        tag(c, 960, 360, "THE FORELLIS WANT A PIECE", 36, a=k, bg="#ffd23f")


@shot(128.2, 133.4)
def t_plan(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "map")
        steps = [("FLY DOWN", wt("fly", 130.0)), ("MEET THE DEALERS", wt("meet", 130.6)),
                 ("BUY THE PRODUCT", wt("product", 131.6)), ("SEND IT HOME", wt("send", 132.3))]
        arrow(c, 600, 120, 1150, 640, "#e8282e", 9, prog=ease_out(at(t, 129.0, 1.2)), dashed=True)
    checklist(c, 180, 560, [s_[0] for s_ in steps], t, [s_[1] for s_ in steps], size=46)
    big_title(c, "SIMPLE.", 1450, 240, 90, t, wt("simple", 128.9), "#f4f0e6")


@shot(133.4, 141.2, "VICE CITY")
def t_ken(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "airport")
        person(c, 1180, 1010, "ken", "ken", "shrug", "scared", t, s=1.35, talk=0.8 * window(t, 136.9, 140.6))
        tommy(c, 720, 1010, TV, "cross", "neutral", t, s=1.35)
        if t > wt("sweats", 137.6):
            for i in range(4):
                k = (t * 1.5 + i * 0.25) % 1
                drop(c, 1140 + i * 30, 540 + k * 80, 9, "#9fd3ef", a=1 - k)
    tag(c, 1180, 360, "KEN ROSENBERG · LAWYER", 34, a=fade(t, wt("ken", 135.6)))
    for i, (lab, tm) in enumerate((("TALKS FAST", wt("talks", 137.0)), ("SWEATS A LOT", wt("sweats", 137.6)),
                                   ("SCARED OF EVERYTHING", wt("scared", 139.0)))):
        tag(c, 1580, 520 + i * 90, lab, 30, a=fade(t, tm - 0.05), s=pop(t, tm - 0.05), rot=-3)


from gfx import drop  # noqa: E402


# ======================================================================= THE DEAL
@shot(141.2, 150.6, "VICE CITY DOCKS")
def t_deal(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "keys_night")
        box(c, 760, 840, 400, 30, "#6a4a32", r=6)
        box(c, 790, 870, 20, 140, "#4a3222", ow=4)
        box(c, 1110, 870, 20, 140, "#4a3222", ow=4)
        if t > wt("briefcase", 148.0):
            briefcase(c, 960, 780, 0.9, open_=at(t, wt("table", 149.4), 0.5))
        person(c, 360, 1040, "ken", "ken", "stand", "scared", t, s=1.2)
        tommy(c, 600, 1040, TV, "hug" if 146.4 < t < 147.6 else "stand", "neutral", t, s=1.25)
        person(c, 1320, 1040, "victor", "victor", "hug" if 146.4 < t < 147.6 else "stand", "smile", t, s=1.25)
        person(c, 1560, 1040, "lance", "lance", "hips", "smirk", t, s=1.25)
    tag(c, 1320, 400, "VICTOR VANCE", 30, a=fade(t, wt("victor", 145.0)))
    tag(c, 1560, 470, "LANCE VANCE", 30, a=fade(t, wt("lance", 145.4)))
    tag(c, 360, 470, "KEN", 30, a=fade(t, 143.0))


@shot(150.6, 157.4)
def t_ambush(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, shake=0.15)
        draw_bg(c, "keys_night")
        for k in range(4):
            glow(c, 200 + k * 500, 600, 260, "#ffd23f", 0.15 * (int(t * 12 + k) % 2))
        for i, x in enumerate((180, 1740, 400)):
            if t > wt("masked", 152.6) + i * 0.2 - 0.3:
                person(c, x, 1040, "masked", "masked", "point", "angry", t, s=1.15, flip=(x > 960))
                gunfire(c, x + (120 if x < 960 else -120), 650, t + i, n=1)
        dead = t > wt("killed", 155.0)
        if not dead:
            person(c, 1320, 1040, "victor", "victor", "raise", "scared", t, s=1.25)
        else:
            with xf(c, 1320, 1040, rot=80):
                person(c, 0, 0, "victor", "victor", "stand", "sad", t, s=1.25, bob=False)
        lx = lerp(1560, 2200, smooth(at(t, wt("escapes", 156.3), 1.0)))
        person(c, lx, 1040, "lance", "lance", "walk", "scared", t, s=1.25, walk=t)
        tommy(c, 760, 1040, TV, "guard", "angry", t, s=1.25)
    k = pop(t, wt("shooting", 151.0), 0.3)
    if k > 0 and t < 153:
        T(c, "AMBUSH!", 960, 260, 120 * k, "#ffd23f", BANG, outline="#141414", ow=12, rot=-6)
    tag(c, 1320, 420, "VICTOR", 32, a=fade(t, wt("killed", 155.0)), bg="#ff8a8a")


@shot(157.4, 165.9)
def t_gone(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "keys_night")
        if t < wt("smoke", 160.0):
            x = lerp(760, -300, smooth(at(t, 157.5, 1.8)))
            tommy(c, x, 1040, TV, "walk", "scared", t, s=1.25, walk=t)
            person(c, x - 240, 1040, "ken", "ken", "walk", "scared", t, s=1.2, walk=t)
        for k in range(5):
            rnd = random.Random(k)
            a = clamp(1 - (t - 159.5) / 3)
            oval(c, 400 + k * 280, 700 - (t - 157) * 20 - k * 30, 160, 80, "#8a8a94", ow=0)
        box(c, 760, 840, 400, 30, "#6a4a32", r=6)
        marker_circle(c, 960, 800, 260, 120, at(t, wt("money", 161.0), 0.6))
    for i, (lab, tm) in enumerate((("MONEY: GONE", wt("money", 161.0)), ("DRUGS: GONE", wt("drugs", 162.4)))):
        tag(c, 700 + i * 520, 300, lab, 42, a=fade(t, tm - 0.05), s=pop(t, tm - 0.05), bg="#ff8a8a", rot=-4 + i * 6)
    k = pop(t, wt("phone", 164.8), 0.35)
    if k > 0:
        phone_screen(c, 1580, 560, 0.7 * k, lambda cc: (grad_rect(cc, -150, -300, 300, 600, ["#1c2a4a", "#0e1628"]),
                                                       T(cc, "SONNY", 0, -160, 44, "#ffffff", LUCKY),
                                                       T(cc, "calling...", 0, -110, 26, "#9fd3ef", "interb")), rot=6)


@shot(165.9, 173.6)
def t_owe(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "liberty_night")
        person(c, 1200, 1040, "sonny", "sonny", "phone", "angry", t, s=1.45, talk=0.7 * window(t, 166.5, 169.0))
        tommy(c, 560, 1040, TV, "phone", "worried", t, s=1.4)
        line(c, 960, 0, 860, H, "#141414", 14)
    speech(c, 1200, 230, ["I WANT MY MONEY BACK.", "ALL OF IT."], 36, a=fade(t, wt("money", 167.2) - 0.3),
           s=pop(t, wt("money", 167.2) - 0.3), tail=(20, 90))
    k = fade(t, wt("fortune", 172.6))
    if k > 0:
        stamp(c, 560, 260, "DAY 1: IN DEBT", 60, a=k, s=lerp(1.5, 1, ease_out(k)), rot=-6)


# ======================================================================= CORTEZ / LANCE
@shot(173.6, 180.0)
def t_work(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "keys")
        tommy(c, 760, 1040, TV, "hips", "determined", t, s=1.35)
        person(c, 380, 1040, "ken", "ken", "point", "smile", t, s=1.25, talk=0.7 * window(t, 177.5, 180))
    caption_serif(c, "So you start where every survivor starts.", 960, 1010, 50, a=window(t, 173.8, 176.2))
    big_title(c, "YOU FIND WORK.", 1350, 260, 90, t, wt("work", 176.4), "#f4f0e6")


@shot(180.0, 188.8, "VICE CITY")
def t_cortez(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "keys")
        person(c, 1200, 1040, "cortez", "cortez", "point", "smirk", t, s=1.35, talk=0.5 * window(t, 184.5, 188))
        tommy(c, 720, 1040, TV, "stand", "neutral", t, s=1.35)
    tag(c, 1200, 360, "COLONEL CORTEZ", 38, a=fade(t, wt("colonel", 180.6)), s=pop(t, wt("colonel", 180.6)))
    for i, (lab, tm) in enumerate((("KNOWS EVERYBODY", wt("knows", 182.0)), ("TRUSTS NOBODY", wt("trusts", 183.0)))):
        tag(c, 1600, 560 + i * 100, lab, 30, a=fade(t, tm - 0.05), s=pop(t, tm - 0.05), rot=-4,
            bg="#ff8a8a" if i else "#ffffff")
    checklist(c, 140, 300, ["DO JOBS", "MAKE CONTACTS", "LEARN THE CITY"], t,
              [wt("jobs", 185.0), wt("contacts", 186.2), wt("learn", 187.4)], size=40)


@shot(188.8, 197.8)
def t_lance(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "vice_night")
        person(c, 1180, 1040, "lance", "lance", "point", "angry", t, s=1.4, talk=0.6 * window(t, 190.6, 193.5))
        tommy(c, 720, 1040, TV, "cross", "determined", t, s=1.4)
    tag(c, 1180, 340, "LANCE VANCE", 40, a=fade(t, wt("lance", 189.6)))
    for i, (lab, tm) in enumerate((("ANGRY", wt("angry", 190.8)), ("RECKLESS", wt("reckless", 191.4)))):
        tag(c, 1560, 520 + i * 90, lab, 32, a=fade(t, tm - 0.05), s=pop(t, tm - 0.05), bg="#ff8a8a")
    k = pop(t, wt("name", 195.9) - 0.2, 0.4)
    if k > 0:
        with xf(c, 960, 260, s=k):
            box(c, -160, -60, 320, 120, "#f7f3ea", r=6, ow=5)
            T(c, "???", 0, 20, 70, "#d8262e", LUCKY)


@shot(197.8, 210.0, "VICE CITY")
def t_diaz(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "cork")
        mug(c, 960, 500, "diaz", label="RICARDO DIAZ", expr="angry", rot=-3, s=1.35 * pop(t, wt("diaz", 199.4) - 0.2),
            t=t, bgcol="#e8c0a0")
        red_string(c, [(500, 900), (720, 700), (960, 360)], ease_out(at(t, 198.2, 1.2)))
    tag(c, 1450, 300, "BIGGEST DRUG LORD", 34, a=fade(t, wt("biggest", 201.4)), rot=5)
    for i, (lab, tm) in enumerate((("PARANOID", wt("paranoid", 203.6)), ("LOUD", wt("loud", 204.2)),
                                   ("DANGEROUS", wt("dangerous", 204.6)))):
        tag(c, 440, 300 + i * 90, lab, 34, a=fade(t, tm - 0.05), s=pop(t, tm - 0.05), rot=-4,
            bg="#ff8a8a" if i == 2 else "#ffffff")
    k = fade(t, wt("working", 208.2))
    if k > 0:
        marker_text(c, "now working for him", 1450, 880, 56, a=k, rot=-4)


@shot(210.0, 217.0)
def t_smile(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "penthouse")
        person(c, 1200, 1040, "diaz", "diaz", "point", "laugh", t, s=1.4, talk=0.6)
        tommy(c, 720, 1040, TV, "stand", "smile" if 213.0 < t < 215.0 else "neutral", t, s=1.4)
    for i, (lab, tm) in enumerate((("YOU SMILE", wt("smile", 213.4)), ("RUN HIS ERRANDS", wt("errands", 214.8)),
                                   ("AND YOU WAIT", wt("wait", 215.8)))):
        tag(c, 360, 300 + i * 100, lab, 36, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1), rot=-3)


@shot(217.0, 224.0, "JUNKYARD")
def t_junk(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, shake=0.12 * (t > 221))
        draw_bg(c, "junkyard")
        person(c, 1300, 1040, "lance", "lance", "cuffed", "scared", t, s=1.3)
        if t > wt("drag", 221.4) - 0.3:
            tommy(c, 1060, 1040, TV, "hug", "angry", t, s=1.3)
        for i, x in enumerate((260, 1700)):
            person(c, x, 1040, "diaz" if i == 0 else "goon", None, "point", "angry", t, s=1.15, flip=(x > 960))
            if t > 221:
                gunfire(c, x + (120 if x < 960 else -120), 680, t + i, n=1)
    tag(c, 1300, 400, "CAUGHT", 40, a=fade(t, wt("caught", 220.3)), bg="#ff8a8a")
    marker_text(c, "Lance can't wait", 700, 260, 60, a=at(t, 217.2, 0.6), rot=-4)


@shot(224.0, 233.6, "DIAZ MANSION")
def t_storm(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, shake=0.1 * (t > 226))
        draw_bg(c, "mansion")
        adv = smooth(at(t, wt("storm", 226.6), 2.5))
        tommy(c, lerp(300, 760, adv), 1040, TV, "point", "angry", t, s=1.3, walk=t if adv < 1 else 0)
        person(c, lerp(100, 560, adv), 1040, "lance", "lance", "point", "angry", t, s=1.3, walk=t if adv < 1 else 0)
        if t > 226.5:
            gunfire(c, lerp(500, 960, adv), 690, t, n=2)
    big_title(c, "THEN IT'S TIME.", 960, 200, 90, t, wt("time", 224.6), "#f4f0e6")
    for i, (lab, tm) in enumerate((("ROOM BY ROOM", wt("room", 228.0)), ("FLOOR BY FLOOR", wt("floor", 229.2)))):
        tag(c, 1450, 300 + i * 100, lab, 38, a=fade(t, tm - 0.05), s=pop(t, tm - 0.05), rot=-3 + i * 5)


@shot(233.6, 243.8)
def t_mansion_yours(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "mansion")
        tommy(c, 960, 1040, TV, "raise" if t > wt("yours", 236.4) else "hips", "smirk", t, s=1.5)
    mug(c, 380, 380, "diaz", label="DIAZ", expr="scared", rot=-8, t=t, s=0.8, xmark=at(t, wt("gone", 234.9), 0.6))
    k = fade(t, wt("yours", 236.4) - 0.1)
    if k > 0:
        stamp(c, 1450, 280, "MANSION: YOURS", 60, a=k, s=lerp(1.5, 1, ease_out(k)), rot=-6, color="#2e8b57")
    caption_serif(c, "from a man with nothing... to the most dangerous house in Vice City", 960, 1010, 42,
                  a=fade(t, wt("overnight", 237.8)))


# ======================================================================= THE EMPIRE
BIZ = [("STRIP CLUB", "strip", 246.0), ("CAB COMPANY", "cab", 247.4), ("CAR SHOWROOM", "car", 248.8),
       ("FILM STUDIO", "film", 250.0), ("PRINT WORKS", "print", 251.3), ("ICE CREAM FACTORY", "ice", 254.7)]


def biz_icon(c, kind, t):
    if kind == "strip":
        neon(c, "Pole", 0, 10, 70, "#ff5fa2", SCRIPT)
    elif kind == "cab":
        car(c, 0, 70, 0.55, "#f2c12e", t, kind="sedan")
    elif kind == "car":
        car(c, 0, 70, 0.55, "#d8262e", t, kind="conv")
        sparkle(c, 120, -60, 20, "#ffffff")
    elif kind == "film":
        oval(c, -50, -20, 45, 45, "#2a2a30")
        oval(c, 50, -20, 45, 45, "#2a2a30")
        box(c, -90, 20, 180, 70, "#2a2a30", r=8)
    elif kind == "print":
        for i in range(3):
            cash(c, -40 + i * 40, -20 + i * 15, 1.3, rot=-10 + i * 8)
    elif kind == "ice":
        pth = poly([(-40, -10), (40, -10), (0, 90)])
        shape(c, pth, "#e0a050")
        oval(c, 0, -30, 50, 40, "#f4a7c0")


@shot(243.8, 258.8, "THE VERCETTI EMPIRE")
def t_biz(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "cork")
    for i, (lab, kind, near) in enumerate(BIZ):
        tm = wt(lab.split()[0].lower() if kind != "strip" else "strip", near) - 0.2
        k = pop(t, max(tm, 244.0), 0.4)
        if k <= 0:
            continue
        x = 380 + (i % 3) * 580
        y = 340 if i < 3 else 760
        with xf(c, x, y, s=k, rot=(-5 + i * 3)):
            box(c, -230, -170, 460, 340, "#f7f3ea", r=6)
            biz_icon(c, kind, t)
            T(c, lab, 0, 140, 34, "#141414", LUCKY)
            oval(c, 0, -165, 14, 14, "#d8262e", ow=3)
    big_title(c, "YOU DON'T STOP THERE.", 960, 560, 80, t, 243.9, "#f4f0e6") if t < 245.6 else None
    k = fade(t, wt("fake", 252.6))
    if k > 0 and t < 254.5:
        stamp(c, 960, 560, "FAKE MONEY", 80, a=k, rot=-6)


@shot(258.8, 263.0)
def t_power(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "office_m")
        tommy(c, 960, 700, TV, "hips", "smirk", t, s=1.0)
        box(c, 560, 700, 800, 70, "#6a4428", r=6)
        box(c, 600, 770, 720, 300, "#5a3a22", ow=5)
        n = int(clamp((t - 258.9) / 3) * 12)
        for i in range(n):
            cash(c, 700 + (i % 6) * 100, 690 - (i // 6) * 30, 1.2)
    with screen_space(c):
        box(c, 1450, 300, 360, 200, "#141418", r=16, ow=5, oc="#f2f2f2")
        v = clamp((t - 258.9) / 3.5)
        pth = skia.Path()
        pth.moveTo(1480, 470)
        for i in range(1, 11):
            x = 1480 + i * 30
            y = 470 - (i / 10) ** 1.6 * 140 * v - (i % 2) * 10
            pth.lineTo(x, y)
        c.drawPath(pth, P("#7dff8a", 6))
        T(c, "POWER", 1630, 340, 30, "#7dff8a", LUCKY)


@shot(263.0, 267.6, "MALIBU CLUB")
def t_malibu(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "club_malibu")
        tommy(c, 960, 1020, TV, "point", "smirk", t, s=1.3, talk=0.5)
        for i, (w_, lk) in enumerate((("goon", None), ("lance", "lance"), ("ken", "ken"), ("goon2", None))):
            person(c, (260, 560, 1360, 1660)[i], 1020, w_, lk, "cross", "neutral", t, s=1.15)
    with screen_space(c):
        k = pop(t, wt("bank", 264.0), 0.4)
        if k > 0:
            with xf(c, 1500, 260, s=k, rot=5):
                box(c, -200, -140, 400, 280, "#2a4a8a", r=6)
                for g in range(6):
                    line(c, -200 + g * 66, -140, -200 + g * 66, 140, "#5a7aba", 2)
                    line(c, -200, -140 + g * 46, 200, -140 + g * 46, "#5a7aba", 2)
                arrow(c, -150, 90, 60, -50, "#ffffff", 6)
                T(c, "THE BIG ONE", 0, 120, 34, "#ffffff", LUCKY)


@shot(267.6, 272.4, "EL BANCO CORRUPTO GRANDE")
def t_bank(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, shake=0.1 * (t > 268.5 and t < 270))
        draw_bg(c, "bank_vc")
        out = smooth(at(t, wt("walk", 270.6), 1.2))
        tommy(c, lerp(960, 1200, out), 1020, TV, "bag" if out > 0 else "point", "smirk", t, s=1.3,
              prop=lambda c2: money_bag(c2, 90, -60, 0.9) if out > 0 else None, walk=t if 0 < out < 1 else 0)
        if t > 268.4 and t < 270.2:
            gunfire(c, 1180, 690, t, n=1)
    tag(c, 960, 160, "BROAD DAYLIGHT", 40, a=fade(t, wt("broad", 269.4)), bg="#ffd23f")
    k = fade(t, wt("rich", 271.2))
    if k > 0:
        stamp(c, 600, 300, "RICH", 100, a=k, s=lerp(1.5, 1, ease_out(k)), rot=-8, color="#2e8b57")


@shot(272.4, 279.0, "VICE CITY")
def t_mister(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "street_sunset")
        tommy(c, 960, 1020, TV, "hips", "smirk", t, s=1.45)
        for i, (w_, lk, pose, x) in enumerate((("cop", "cop", "cross", 380), ("goon", "masked", "raise", 1560))):
            if t > (wt("cops", 275.0) if i == 0 else wt("gangs", 276.4)) - 0.2:
                person(c, x, 1020, w_, lk, pose, "worried", t, s=1.2, look=(-3 if x > 960 else 3, 0))
    marker_text(c, "VERCETTI", 960, 240, 110, "#f4f0e6", a=at(t, 272.6, 0.8), rot=-3)
    speech(c, 1480, 360, ["GOOD EVENING,", "MISTER VERCETTI."], 32, a=fade(t, wt("mister", 278.0) - 0.2),
           s=pop(t, wt("mister", 278.0) - 0.2), tail=(-60, 90))


# ======================================================================= SONNY WANTS HIS CUT
@shot(279.0, 289.3, "LIBERTY CITY")
def t_watching(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "liberty_night")
        person(c, 960, 1040, "sonny", "sonny", "phone" if t > wt("calls", 282.8) else "cross", "angry", t, s=1.5,
               talk=0.7 * window(t, 283.5, 288.8))
    with screen_space(c):
        if t > wt("calls", 282.8):
            phone_screen(c, 1540, 540, 0.7, lambda cc: (grad_rect(cc, -150, -300, 300, 600, ["#1c2a4a", "#0e1628"]),
                                                       T(cc, "SONNY", 0, -160, 44, "#ffffff", LUCKY),
                                                       T(cc, "calling...", 0, -110, 26, "#9fd3ef", "interb")), rot=6)
    for i, (lab, tm) in enumerate((("MY CUT.", wt("cut", 284.4)), ("I SENT YOU THERE.", wt("sent", 285.7)),
                                   ("15 YEARS, TOMMY.", wt("15", 287.5)))):
        speech(c, 520, 250 + i * 150, [lab], 34, a=fade(t, tm - 0.2), s=pop(t, tm - 0.2), tail=(60, 60))


@shot(289.3, 292.3)
def t_no(c, t, lt, d):
    no = wt("no", 291.2)
    with xf(c):
        cam(c, lt, d, shake=0.25 * window(t, no, no + 0.35, 0.05))
        draw_bg(c, "penthouse")
        tommy(c, 760, 1520, TV, "phone", "angry", t, s=2.6, look=(2, 0))
    big_title(c, "NO.", 1400, 360, 200, t, no, "#ff4a4a")


@shot(292.3, 303.6)
def t_used(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "cork")
        mug(c, 960, 480, "sonny", label="SONNY", expr="smirk", rot=-3, t=t, s=1.2, bgcol="#c8c8d0",
            xmark=at(t, wt("used", 296.2), 0.6) * 0 + 0)
    items = [("NEVER NEEDED YOU", wt("needed", 295.0)), ("USED YOU", wt("used", 296.2)),
             ("LET YOU ROT", wt("rot", 297.8)), ("SENT YOU TO A BAD DEAL", wt("deal", 299.4)),
             ("NOW WANTS IT ALL", wt("take", 302.8))]
    for i, (lab, tm) in enumerate(items):
        x = 300 if i % 2 == 0 else 1620
        y = 260 + i * 150
        k = pop(t, tm - 0.2, 0.35)
        if k > 0:
            tag(c, x, y, lab, 32, s=k, rot=-4 if i % 2 == 0 else 4, bg="#ff8a8a" if i in (1, 4) else "#ffffff")
            red_string(c, [(x, y), (960, 480)], at(t, tm - 0.1, 0.4))


@shot(303.6, 309.6, "SONNY COMES TO VICE CITY")
def t_army(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "mansion")
        tint_c(c, "#1a0a2a", 0.35)
        n = int(clamp((t - 304.0) / 2.0) * 8)
        for i in range(n):
            x = 220 + i * 210
            person(c, x, 1050, "goon" if i % 2 else "goon2", None, "cross", "angry", t, s=1.1)
        person(c, 960, 1060, "sonny", "sonny", "hips", "smirk", t, s=1.3)
    tag(c, 960, 360, "WITH AN ARMY", 44, a=fade(t, wt("army", 306.0)), bg="#ff8a8a")
    caption_serif(c, "And here's the part that hurts the most.", 960, 1010, 50, a=fade(t, wt("part", 308.0)))


@shot(309.6, 321.3)
def t_lance_betrays(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "liberty_night")
        person(c, 760, 1040, "lance", "lance", "phone", "smirk", t, s=1.45, talk=0.6 * window(t, 314.3, 320.6))
        if t > wt("talking", 314.8) - 0.2:
            person(c, 1260, 1040, "sonny", "sonny", "phone", "smile", t, s=1.45)
            line(c, 1010, 0, 920, H, "#141414", 14)
    tag(c, 760, 380, "LANCE VANCE", 40, a=fade(t, 310.3))
    for i, (lab, tm) in enumerate((("YOU SAVED HIS LIFE", wt("saved", 312.0)), ("TRUSTED LIKE A BROTHER", wt("trusted", 313.3)))):
        tag(c, 400, 560 + i * 90, lab, 30, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1), rot=-3)
    k = fade(t, wt("underappreciated", 317.8))
    if k > 0:
        marker_text(c, "\"underappreciated\"", 760, 260, 56, a=k, rot=-4)
    k = fade(t, wt("his", 320.3))
    if k > 0:
        stamp(c, 1300, 260, "TRAITOR", 80, a=k, s=lerp(1.5, 1, ease_out(k)), rot=-8)


@shot(321.3, 325.0)
def t_door(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "mansion")
        tint_c(c, "#0a0530", 0.45)
        k = smooth(at(t, wt("opens", 321.9), 0.8))
        box(c, 840, 520, 240, 240, "#fff2c0", ow=6)
        box(c, 840, 520, 240 * (1 - k * 0.85), 240, "#8a5a3a", ow=6)
        person(c, 700, 1040, "lance", "lance", "point", "smirk", t, s=1.25)
        if t > wt("walks", 323.0) - 0.2:
            x = lerp(1700, 1150, smooth(at(t, wt("walks", 323.0) - 0.2, 1.4)))
            person(c, x, 1040, "sonny", "sonny", "walk", "smirk", t, s=1.3, walk=t)


# ======================================================================= THE FINAL NIGHT
@shot(325.0, 332.0, "THE FINAL NIGHT")
def t_chaos(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, shake=0.18)
        draw_bg(c, "office_m")
        tint_c(c, "#2a0010", 0.25)
        tommy(c, 960, 1040, TV, "point", "angry", t, s=1.35)
        gunfire(c, 1140, 690, t, n=2)
        for i, x in enumerate((240, 1680, 420, 1500)):
            person(c, x, 1040 - (i // 2) * 40, "goon" if i % 2 else "goon2", None, "point", "angry", t, s=1.05,
                   flip=(x > 960))
            gunfire(c, x + (110 if x < 960 else -110), 690 - (i // 2) * 30, t + i, n=1)
        if t > wt("money", 330.7) - 0.3:
            for i in range(16):
                y = ((t - 330) * 400 + i * 90) % 1200 - 100
                cash(c, (i * 211) % W, y, 1.1, rot=(t * 90 + i * 30))
    big_title(c, "PURE CHAOS", 960, 180, 100, t, wt("chaos", 325.8), "#ff4a4a")


@shot(332.0, 338.2, "THE ROOF")
def t_roof(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, shake=0.1 * (t > 336.6))
        draw_bg(c, "roof")
        down = t > wt("ends", 337.1)
        if not down:
            person(c, 1300, 1000, "lance", "lance", "point", "angry", t, s=1.3, flip=True)
        else:
            with xf(c, 1300, 1000, rot=80):
                person(c, 0, 0, "lance", "lance", "stand", "sad", t, s=1.3, bob=False)
        tommy(c, 640, 1000, TV, "point", "angry", t, s=1.35)
        if 336.0 < t < 337.3:
            gunfire(c, 820, 650, t, n=1)
    mug(c, 1560, 300, "lance", label="FRIEND", expr="smile", rot=6, t=t, s=0.75,
        xmark=at(t, wt("traitor", 335.4), 0.6))
    tag(c, 1300, 420, "TRAITOR", 36, a=fade(t, wt("traitor", 335.4)) * (0 if down else 1), bg="#ff8a8a")


@shot(338.2, 345.6)
def t_office(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "office_m")
        person(c, 1200, 1040, "sonny", "sonny", "bag", "smirk", t, s=1.4,
               prop=lambda c2: money_bag(c2, 90, -60, 0.9), talk=0.5 * window(t, 345.0, 347))
        tommy(c, 700, 1040, TV, "point", "angry", t, s=1.4)
    k = pop(t, wt("1971", 343.8), 0.4)
    if k > 0:
        mug(c, 1560, 300, "sonny", label="1971", expr="smile", rot=6, t=t, s=0.7 * k, bgcol="#d8c8a0")
    marker_circle(c, 1290, 740, 140, 120, at(t, wt("money", 341.0), 0.6))


@shot(345.6, 352.9)
def t_paid(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "office_m")
        if t < wt("never", 351.0):
            person(c, 1200, 1040, "sonny", "sonny", "point", "smirk", t, s=1.4, talk=0.6 * window(t, 345.7, 346.8))
        tommy(c, 700, 1040, TV, "point", "determined", t, s=1.4, talk=0.6 * window(t, 347.2, 349.3))
    speech(c, 1300, 250, ["YOU OWE ME, TOMMY."], 36, a=window(t, 345.8, 347.3), s=pop(t, 345.8), tail=(-30, 90))
    speech(c, 700, 250, ["I PAID.", "FIFTEEN YEARS."], 40, a=fade(t, wt("paid", 347.6) - 0.2),
           s=pop(t, wt("paid", 347.6) - 0.2), tail=(30, 90))
    flash(c, t, wt("never", 351.0), 0.3)
    if t > wt("never", 351.0):
        caption_serif(c, "Sonny Forelli never leaves Vice City.", 960, 1010, 50, a=fade(t, wt("never", 351.0) + 0.2))


# ======================================================================= ENDING
@shot(352.9, 360.8, "SUNRISE")
def t_balcony(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "balcony")
        tommy(c, 860, 1080, TV, "hips", "smirk", t, s=1.5)
        person(c, 1180, 1080, "ken", "ken", "shrug", "worried", t, s=1.4)
    tag(c, 1180, 380, "KEN · STILL SHAKING", 32, a=fade(t, wt("shaking", 359.4)))
    caption_serif(c, "looking out over the city you own", 960, 1010, 48, a=fade(t, wt("looking", 356.3)))


@shot(360.8, 368.6)
def t_king(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "vice_sunset")
        tommy(c, 760, 1520, TV, "hips", "smirk", t, s=2.6, look=(2, 0))
    mug(c, 1450, 340, "tommy_v", "tommy_kid", "LIBERTY CITY BOY", "neutral", rot=6, t=t, s=0.7,
        xmark=at(t, wt("gone", 362.5), 0.5))
    k = fade(t, wt("butcher", 363.9))
    if k > 0:
        stamp(c, 1450, 700, "HARWOOD BUTCHER", 50, a=k, rot=-6)
        line(c, 1200, 700, 1200 + 500 * at(t, wt("gone", 364.2), 0.4), 700, "#d8262e", 10)
    big_title(c, "THE KING OF VICE CITY", 960, 160, 80, t, wt("king", 367.3), "#ffd23f")


@shot(368.6, 382.4)
def t_recap(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "cork")
    items = [("tommy_v", "tommy_kid", "WATCHING THE SUITS", "neutral", wt("kid", 370.6), 360, 330),
             ("tommy_v", "tommy_p", "15 YEARS OF SILENCE", "determined", wt("silence", 373.8), 860, 330),
             ("sonny", "sonny", "NEVER DESERVED IT", "smirk", wt("deserved", 375.2), 1360, 330)]
    for i, (who, lk, lab, ex, tm, x, y) in enumerate(items):
        k = pop(t, tm - 0.2, 0.4)
        if k > 0:
            mug(c, x, y, who, lk, lab, ex, rot=(-5 + i * 4), t=t, s=k * 0.9)
    k = pop(t, wt("briefcase", 377.6) - 0.2, 0.4)
    if k > 0:
        briefcase(c, 560, 780, 1.1 * k)
    k = fade(t, wt("errand", 380.6))
    if k > 0:
        marker_text(c, "nobody's errand boy again", 1250, 800, 60, a=k, rot=-4)


@shot(382.4, 386.9)
def t_loyalty(c, t, lt, d):
    with xf(c):
        cam(c, lt, d)
        draw_bg(c, "liberty_night", blur=6)
        tint_c(c, "#000000", 0.35)
    k = fade(t, 382.5)
    T(c, "LOYAL YOUR WHOLE LIFE", 960, 440, 76, "#ffffff", LUCKY, a=k, outline="#141414", ow=10)
    k = fade(t, wt("loyalty", 384.6))
    if k > 0:
        T(c, "LOYALTY ALMOST KILLED YOU", 960, 560, 76, "#ff4a4a", LUCKY, a=k, outline="#141414", ow=10)


@shot(386.9, 400.0, "WHAT WOULD YOU DO?")
def t_final(c, t, lt, d):
    with xf(c):
        draw_bg(c, "vice_night")
        tint_c(c, "#000000", 0.35)
    doors(c, t, 387.0, ["STAY LOYAL TO SONNY", "TAKE THE CITY"], cols=("#5a6a8a", "#ff5fa2"))
    big_title(c, "IF YOU WERE TOMMY...", 960, 160, 70, t, 387.2, "#ffd23f")
    k = fade(t, 391.5)
    if k > 0:
        with xf(c, 960, 1000, alpha=k):
            box(c, -360, -46, 720, 92, "#ffffff", r=20, ow=5, oc="#141414")
            T(c, "Tell me in the comments!", 0, 14, 38, "#141414", "interb")
