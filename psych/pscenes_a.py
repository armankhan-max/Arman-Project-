"""Timeline part A (0:00 - 3:03). Times are absolute seconds in the voiceover."""
import math
import random

import skia

from pgfx import *  # noqa: F401,F403
from psets import *  # noqa: F401,F403


# ---------------------------------------------------------------- camera + shared helpers
def cam(c, zoom=1.0, cx=W / 2, cy=H / 2, t=0.0, shake=0.0, drift=1.0):
    dx = drift * (6 * math.sin(t * 0.37) + 3 * math.sin(t * 0.91)) + shake * (math.sin(t * 53) * 9 + math.sin(t * 31) * 6)
    dy = drift * (4 * math.sin(t * 0.29 + 1) + 2 * math.sin(t * 1.13)) + shake * (math.cos(t * 47) * 9)
    c.translate(W / 2 + dx, H / 2 + dy)
    c.scale(zoom, zoom)
    c.translate(-cx, -cy)


def push(t, a, b, z0, z1):
    return lerp(z0, z1, smooth((t - a) / max(0.01, b - a)))


def head_cu(c, x, y, who, expr, t, s=1.0, look=(0, 0), face=1.0, talk=None, rim=RIM, tilt=0.0):
    bounds = skia.Rect(x - 300 * s, y - 300 * s, x + 300 * s, y + 300 * s)
    if rim:
        rp = skia.Paint(ColorFilter=skia.ColorFilters.Blend(C(rim), skia.BlendMode.kSrcIn))
        c.saveLayer(bounds, rp)
        with xf(c, x + 6 * s, y - 6 * s, s, tilt):
            draw_head(c, who, 62, expr, t, look, face, talk)
        c.restore()
    with xf(c, x, y, s, tilt):
        draw_head(c, who, 62, expr, t, look, face, talk)


def walker_person(c, x, y, who, t, s=1.0, face=1, run=False, freq=0.9, expr="smile", hold=None, look=(0, 0),
                  rim=RIM, alpha=1.0, tint_col=None, tint_a=0.0):
    pose, bob, lean, speed = walk(t, freq, run)
    person(c, x, y + bob * s, who, pose, expr, t, s, look=look, face=face, lean=lean, hold=hold, rim=rim,
           alpha=alpha, tint_col=tint_col, tint_a=tint_a)
    return speed * s


def gesture(t, a, poses, period=1.5, blend=0.35, sit=False):
    """Cycle through gestures every `period` seconds with smooth blends."""
    u = max(0.0, t - a) / period
    i = int(u)
    k = clamp((u - i) * period / blend)
    p1 = poses[(i - 1) % len(poses)] if i > 0 else poses[0]
    p2 = poses[i % len(poses)]
    out = mix_pose(p1, p2, k)
    if sit:
        out["fl"], out["bl"] = (85, -85), (80, -80)
        if not out["_name"].startswith("sit"):
            out["_name"] = "sit_" + out["_name"]
    return out


def armchair(c, x, y, s=1.0, col="#6b2f2a"):
    with xf(c, x, y, s):
        rrect(c, -170, -330, 340, 380, 60, mixhex(col, "#000000", 0.35))
        rrect(c, -150, -310, 300, 340, 50, col)
        rrect(c, -210, -80, 90, 200, 36, mixhex(col, "#000000", 0.15))
        rrect(c, 120, -80, 90, 200, 36, mixhex(col, "#000000", 0.15))
        rrect(c, -170, 20, 340, 110, 30, mixhex(col, "#000000", 0.25))


def host_shot(c, t, a, poses=("sittalk", "sit", "sittalk", "sitthink"), side=1, zoom=1.0, period=1.6,
              expr_over=None):
    """Talking-head interview shot. Mouth is driven by the real voiceover (lip(t))."""
    cam(c, push(t, a, a + 6, zoom, zoom * 1.05), W / 2, H / 2, t, drift=0.6)
    bg(c, "study", 9)
    bokeh(c, t, GOLD, 14, seed=4, a=0.12, speed=6, rmin=20, rmax=50)
    x = 1180 if side > 0 else 740
    face = -0.55 if side > 0 else 0.55
    armchair(c, x, 790, 1.5)
    op, rnd = lip(t)
    talking = op > 0.04
    expr = expr_over or ("talk" if talking else "neutral")
    pose = gesture(t, a, list(poses), period, sit=True)
    nod = 2.5 * math.sin(t * 2.1) + 3 * op
    person(c, x, 760, "host", pose, expr, t, s=1.55, face=face, talk=(op, rnd), look=(-0.5 * side, 0),
           tilt=nod, rim="#ffcf99", rim_off=(-6 if side > 0 else 6, -5), chair=False)
    grade(c, "dream", 0.25)


def tag2(c, t, start, s, x, y, color=GOLD, size=40, end=None, fg="#14100c"):
    k = back_out(at(t, start, 0.35))
    out = 1.0 if end is None else clamp((end - t) / 0.25)
    if k <= 0 or out <= 0:
        return
    w = dwidth(s, size, "bebas", 0.06) + 46
    with xf(c, x, y, max(0.01, k), alpha=clamp(k) * out):
        rrect(c, -w / 2, -size * 0.75, w, size * 1.45, 10, color)
        dtext(c, s, 0, size * 0.33, size, fg, "bebas", track=0.06)


def loc_tag(c, t, start, s, end=None, x=110, y=990):
    """Documentary location/context slug: thin rule + tracked caps, bottom-left."""
    k = ease_out(at(t, start, 0.6))
    out = 1.0 if end is None else clamp((end - t) / 0.4)
    if k <= 0 or out <= 0:
        return
    rrect(c, x, y - 34, 4, 44, 2, GOLD, k * out)
    c.save()
    c.clipRect(skia.Rect(x, y - 60, x + 30 + 900 * k, y + 20))
    dtext(c, s, x + 22, y, 30, "#f2ead6", "SemiBold", "left", a=out, track=0.22, shadow=0.6)
    c.restore()


# ================================================================= HOOK
def s_hosp(c, t):
    cam(c, push(t, 0, 4.0, 1.0, 1.12), 900, 560, t)
    bg(c, "hospital", 8)
    monitor(c, 1500, 420, 0.9, t)
    hosp_bed(c, 860, 700, 1.0)
    person(c, 760, 655, "hari", "lie", "neutral" if t < 2.0 else "tired", t, s=1.15, rot=-90, face=1,
           look=(0, 0), shadow=False)
    hosp_bed(c, 860, 700, 1.0, front=True)
    grade(c, "cold", 0.6)
    loc_tag(c, t, 0.4, "PRE-OP  ·  HIP REPLACEMENT", 3.7)


def s_mind(c, t):
    # move in on his face: eyes close, the dream window opens above him
    cam(c, push(t, 3.9, 6.9, 1.7, 1.85), 560, 560, t)
    bg(c, "hospital", 8)
    monitor(c, 1500, 420, 0.9, t)
    hosp_bed(c, 860, 700, 1.0)
    ex = "dreamy" if t > 4.6 else "neutral"
    person(c, 760, 655, "hari", "lie", "closed" if t > 5.6 else ex, t, 1.15, rot=-90, face=1, look=(0.3, -1),
           shadow=False)
    hosp_bed(c, 860, 700, 1.0, front=True)
    grade(c, "cold", 0.5)
    k = at(t, 4.6, 0.8)
    if k > 0:
        thought_bubbles(c, 600, 500, 680, 420, t, clamp(k * 2))

        def inner(cc):
            cc.save()
            cc.translate(-960, -540)
            dream_park(cc, t, (t - 4.6) * 120)
            soft_rect(cc, 1150, 300, 220, 420, "#fff6dc", 0.8, 40, 20)
            rrect(cc, 1150, 300, 220, 420, 12, "#fffaf0")
            cc.restore()
        with xf(c, 760, 300, 0.42):
            dream_frame(c, 0, 0, 520, 300, t, inner, at(t, 5.0, 0.9))
    bokeh(c, t, GOLD, 12, seed=2, a=0.15 * k)


def s_dreamwalk(c, t):
    t0 = 6.9
    cam(c, 1.0, 960, 540, t, drift=0.5)
    speed = walk(t, 0.85)[3] * 1.1
    scroll = (t - t0) * speed
    dream_park(c, t, scroll)
    # the hospital front door scrolls away behind him
    dx = 520 - scroll
    if dx > -500:
        rrect(c, dx - 160, 260, 360, 600, 14, "#fff2d6")
        soft_rect(c, dx - 140, 280, 320, 560, "#ffffff", 0.9, 30, 14)
        rrect(c, dx - 160, 260, 360, 600, 14, "#c98a5a", stroke=22)
        dtext(c, "EXIT", dx + 20, 240, 50, "#c98a5a", "bebas", track=0.2)
    walker_person(c, 960, 860 - 170 * 1.1, "hari", t, 1.1, freq=0.85, expr="bliss", rim="#fff2c4")
    bokeh(c, t, "#ffffff", 20, seed=5, a=0.25)
    grade(c, "dream", 0.8)
    flash(c, t, 6.9, "#fff4dc", 0.6, 0.8)


def s_nocane(c, t):
    t0 = 10.7
    run = t > 11.66
    freq = 1.4 if run else 0.85
    cam(c, push(t, t0, 14.3, 1.0, 1.06), 960, 540, t, drift=0.5)
    sp = walk(t, freq, run)[3] * 1.1
    scroll = 380 + (min(t, 11.66) - t0) * walk(t, 0.85)[3] * 1.1 + max(0.0, t - 11.66) * sp
    dream_park(c, t, scroll)
    # cane: held until "No cane", then tossed spinning away
    toss = t - 10.85
    if toss < 0:
        hold = lambda cc, hx, hy: cane(cc, hx, hy - 10, 0.9, 10)  # noqa: E731
    else:
        hold = None
        cx = 1040 + toss * 520
        cy = 520 - toss * 900 + 900 * toss * toss
        cane(c, cx, cy, 1.1, toss * 720)
    if t > 12.86:
        person(c, 960, 860 - 187 - 40 * abs(math.sin((t - 12.86) * 4)), "hari", "cheer", "bliss", t, 1.1,
               rim="#fff2c4")
        for i in range(8):
            ang = i / 8 * 6.283 + t
            r = 260 + 30 * math.sin(t * 3 + i)
            sparkle(c, 960 + math.cos(ang) * r, 420 + math.sin(ang) * r * 0.6, 22, "#ffffff",
                    a=clamp((t - 12.86) * 3))
    else:
        walker_person(c, 960, 860 - 187, "hari", t, 1.1, freq=freq, run=run, expr="bliss" if run else "happy",
                      hold=hold, rim="#fff2c4")
    bokeh(c, t, "#ffffff", 20, seed=5, a=0.25)
    grade(c, "dream", 0.8)
    kword(c, t, 10.82, "NO CANE.", 560, 300, 130, "#ffffff", style="slam", end=12.7)
    kword(c, t, 11.66, "NO PAIN.", 1360, 300, 130, "#ffffff", style="slam", end=12.7)


def s_reality(c, t):
    cam(c, push(t, 14.3, 22.3, 1.0, 1.1), 960, 560, t)
    bg(c, "physio", 8)
    # Hari shuffles slowly with the walker
    ph = (t - 14.3) * 0.45
    pose = mix_pose("walker", dict(fa=(55, 15), ba=(50, 15), fl=(8, -10), bl=(-14, -5)),
                    0.5 + 0.5 * math.sin(ph * 6.28))
    hx = 760 + (t - 14.3) * 12
    walker_frame(c, hx + 183, 486, 1.0, 292)
    person(c, hx, 600, "hari", pose, "worried", t, 1.05, look=(0.4, 0.5), lean=0)
    # therapist with clipboard
    marks = clamp((t - 20.0) / 1.2)
    person(c, 1400, 595, "nina", "clip", "focus", t, 1.05, face=-1, look=(-0.6, 0.2),
           hold=lambda cc, hx_, hy_: clipboard(cc, hx_ - 10, hy_ - 30, 0.9, -8, marks))
    grade(c, "cold", 0.8)
    flash(c, t, 14.3, "#ffffff", 0.35, 0.9)
    loc_tag(c, t, 14.9, "A WELL-KNOWN STUDY", 18.5)
    # the bright picture in his head
    k = window(t, 16.5, 19.8, 0.35)
    if k > 0:
        thought_bubbles(c, hx + 40, 330, hx + 120, 200, t, k)

        def inner(cc):
            dream_park(cc, t, t * 300)
            walker_person(cc, 960, 860 - 187, "hari", t, 1.1, freq=1.4, run=True, expr="bliss", rim="#fff2c4")
        with xf(c, hx + 300, 160, 0.38):
            dream_frame(c, 0, 0, 520, 300, t, lambda cc: (cc.save(), cc.translate(-960, -540), inner(cc),
                                                            cc.restore()), k)
        kword(c, t, 16.6, "BRIGHTEST PICTURE", hx + 300, 330, 46, DREAM, end=19.7, style="pop")
    if t > 21.4:
        tag2(c, t, 21.5, "RECOVERING WORSE", 1400, 230, RED, 48)
        arrow(c, 1640, 160, 1640, 300, RED, 16, a=clamp((t - 21.6) * 3))


def s_twoweeks(c, t):
    info_board(c, t, "#14100c", "#070504")
    cam(c, push(t, 22.2, 24.1, 1.0, 1.08), 960, 540, t)
    days = int(lerp(1, 14, ease_out(at(t, 22.3, 1.0))))
    flip = (t * 6) % 1.0 if t < 23.3 else 0.0
    calendar(c, 960, 520, 1.3, str(days), "DAY", flip)
    kword(c, t, 22.4, "TWO WEEKS LATER", 960, 900, 70, "#f2ead6", "bebas", style="type", track=0.18)


def s_notebook(c, t):
    t0 = 24.0
    if t < 27.1:
        cam(c, push(t, t0, 27.1, 1.0, 1.08), 960, 600, t)
        bg(c, "bedroom", 8)
        flip = ((t - 24.9) * 1.6) % 1.0 if 24.9 < t < 26.8 else 0.0
        items = ["GYM", "WRITE BOOK", "GUITAR", "SIDE BUSINESS", "SPANISH", "YOUTUBE"]
        page = int(max(0, t - 24.9) * 1.6) % 3
        its = [items[(i + page * 2) % 6] for i in range(6)]
        notebook(c, 960, 520, 1.25, t, flip, its, dust=clamp((t - 25.9) * 2))
        if t > 25.9:
            for i in range(6):
                col = i // 3
                xx = 960 + (-290 if col == 0 else 30) * 1.25 + 22
                yy = 520 + (-130 + (i % 3) * 110) * 1.25 - 15
                kk = at(t, 26.1 + i * 0.07, 0.25)
                if kk:
                    cross_mark(c, xx, yy, 0.35 * back_out(kk), RED)
        kword(c, t, 24.86, "A NOTEBOOK FULL OF PLANS", 960, 160, 70, "#f2ead6", style="rise", track=0.06)
        kword(c, t, 26.14, "NEVER STARTED", 960, 980, 80, RED, style="slam")
    else:
        cam(c, push(t, 27.1, 29.2, 1.05, 1.2), 960, 520, t)
        bg(c, "bedroom", 6)
        person(c, 960, 700, "leo", "sitthink", "worried", t, 1.3, face=0.4, look=(0.2, -0.2))
        rrect(c, 300, 760, 1320, 50, 10, "#3a2c40")
        notebook(c, 1180, 670, 0.3, t, 0, [], dust=1.0, rot=-4)


def s_lazy(c, t):
    if t < 30.15:
        cam(c, push(t, 29.1, 30.2, 1.0, 1.06), 960, 540, t)
        bg(c, "bedroom", 9)
        person(c, 960, 640, "leo", "slump", "bored", t, 1.3, face=0.3, tilt=8)
        stamp(c, t, 29.42, "LAZY?", 960, 300, RED, 150, -8)
    else:
        host_shot(c, t, 30.15, ("sittalk", "open"), period=0.6)
        if t > 30.18:
            k = at(t, 30.18, 0.3)
            with xf(c, 520, 320, alpha=clamp(k * 3)):
                dtext(c, "LAZY", 0, 50, 170, "#f2ead6", "bebas", track=0.08, shadow=0.5)
            strike(c, t, 30.4, 520, 0, 380, RED, 18)


def s_title(c, t):
    a = 31.0
    fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, W * 0.7, ["#1a130c", "#050403"]))
    bokeh(c, t, GOLD, 24, seed=9, a=0.12, speed=10)
    k = at(t, a + 0.1, 0.9)
    out = clamp((33.6 - t) / 0.4)
    e = ease_out(k)
    # a thought bubble that turns into a coin: "the dream tax"
    with xf(c, W / 2, 330, 0.9 + 0.1 * e, alpha=out * clamp(k * 2)):
        soft(c, 0, 0, 120, GOLD, 0.35, 50)
        c.drawCircle(0, 0, 90, P("#fff2d6"))
        c.drawCircle(-120, 120, 24, P("#fff2d6"))
        c.drawCircle(-160, 170, 14, P("#fff2d6"))
        coin(c, 0, 0, 70 * e, a=e)
    with xf(c, W / 2, 0, alpha=out):
        dtext(c, "THE DREAM TAX", 0, 640 + (1 - e) * 30, 200, "#f6efe2", "bebas", a=clamp(k * 2), track=0.1,
              shadow=0.6)
        kk = ease_out(at(t, a + 0.7, 0.8))
        rrect(c, -300 * kk, 690, 600 * kk, 3, 1.5, GOLD)
        dtext(c, "why picturing success can quietly stop you", 0, 760, 44, "#d9cbb0", "play",
              a=clamp((t - a - 0.9) * 2))


# ================================================================= CHAPTER 1: FANTASY vs EXPECTATION
def s_oet(c, t):
    cam(c, push(t, 33.6, 38.5, 1.0, 1.08), 960, 540, t)
    bg(c, "labroom", 8)
    rrect(c, 380, 650, 900, 40, 10, "#2a3a4c")
    for i in range(3):
        with xf(c, 560 + i * 80, 630, rot=-6 + i * 5):
            rrect(c, -60, -10, 120, 16, 3, "#f2efe6")
    person(c, 1000, 560, "oet", gesture(t, 33.6, ["explain", "present", "point"], 1.6), "focus", t, 1.15, face=-1,
           look=(-0.5, 0))
    lower(c, t, 33.9, "GABRIELE OETTINGEN", "Psychologist", GOLD, dur=4.4)
    tag2(c, t, 35.5, "NEW YORK UNIVERSITY", 1450, 300, "#8e6bd6", 40, fg="#ffffff")
    tag2(c, t, 36.7, "UNIVERSITY OF HAMBURG", 1450, 390, "#d9534f", 40, fg="#ffffff")


def s_split(c, t):
    a = 38.5
    cam(c, push(t, a, 46.7, 1.0, 1.06), 960, 540, t)
    info_board(c, t, "#0f1117", "#06070a")
    year_badge(c, t, 39.2, "2002", 960, 170, GOLD, 120, end=43.6)
    lower(c, t, 40.6, "WITH DORIS MAYER", "Co-author", GOLD, dur=3.0)
    # one orb that splits into two
    sp = ease_out(at(t, 41.6, 1.2))
    for sd, col in ((-1, COOL), (1, GOLD)):
        x = 960 + sd * 420 * sp
        r = 150 - 30 * sp
        soft(c, x, 540, r * 1.4, col if sp > 0.05 else "#e8e2d6", 0.3, 50)
        c.drawCircle(x, 540, r, P(mixhex("#e8e2d6", col, sp)))
        c.drawCircle(x, 540, r * 0.82, P("#0f1117", a=0.9))
    if sp < 0.5:
        dtext(c, "ONE THING?", 960, 555, 40, "#e8e2d6", "bebas", a=1 - sp * 2, track=0.08)
    if t > 42.2:
        # icons inside the orbs: scale (judgment) and film (scene)
        k1 = back_out(at(t, 44.32, 0.4))
        k2 = back_out(at(t, 45.28, 0.4))
        with xf(c, 540, 540, 0.3 * k1 if k1 > 0 else 0.001):
            scale_balance(c, 0, 40, 1.0, 6 * math.sin(t * 1.5), t)
        with xf(c, 1380, 540, max(0.001, 0.5 * k2)):
            film_frame(c, 0, 0, 260, 160, t, lambda cc: (fill_shader(cc, skia.Rect(-130, -80, 130, 80),
                                                                     linear(0, -80, 0, 80, ["#ffd99a", "#ff9f7a"])),
                                                          sparkle(cc, 0, 0, 40, "#ffffff")))
        kword(c, t, 44.32, "EXPECTATION", 540, 820, 90, COOL, style="rise", track=0.06)
        kword(c, t, 45.28, "FANTASY", 1380, 820, 90, GOLD, style="rise", track=0.06)


def s_expect(c, t):
    a = 46.6
    cam(c, push(t, a, 53.9, 1.0, 1.05), 960, 540, t)
    info_board(c, t, "#0d1520", "#05080c")
    tilt = 0
    loads = [(51.4, "HISTORY", "#8fb3d9"), (52.16, "SKILLS", "#7fd3ff"), (53.0, "ODDS", "#b0c4de")]
    nl = sum(1 for (tt_, _, _) in loads if t > tt_)
    tilt = -4 * nl + 3 * math.sin(t * 2) * (1 if nl else 0)

    def left(cc, x, y):
        for i, (tt_, lab, col) in enumerate(loads):
            k = at(t, tt_, 0.35)
            if k > 0:
                yy = y - 30 - i * 56 - (1 - ease_out(k)) * 300
                rrect(cc, x - 80, yy - 26, 160, 50, 8, col)
                dtext(cc, lab, x, yy + 12, 34, "#0b1018", "bebas", track=0.06)

    def right(cc, x, y):
        sparkle(cc, x, y - 40, 30, "#7fd3ff", a=0.7)
    person(c, 430, 640, "leo", "think", "focus", t, 1.15, face=1, look=(0.6, -0.3), rim=COOL)
    scale_balance(c, 1200, 560, 1.0, tilt, t, left, right)
    kword(c, t, 48.0, "A JUDGMENT", 960, 150, 96, COOL, style="rise", track=0.08)
    quote(c, t, 49.0, 50.4, 960, 260, 1400, 54, "#e8e2d6", COOL, "play")
    grade(c, "cold", 0.4)


def s_fantasy(c, t):
    cam(c, push(t, 53.8, 55.5, 1.0, 1.1), 960, 540, t)
    fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, W * 0.7, ["#2a1a0c", "#080503"]))

    def scene(cc):
        cc.save()
        cc.translate(-960, -540)
        set_dream(cc, t)
        person(cc, 960, 600, "leo", "cheer", "bliss", t, 1.2, rim="#fff2c4")
        trophy(cc, 960, 200, 0.8, ghost=True)
        bokeh(cc, t, "#ffffff", 20, seed=3, a=0.3)
        cc.restore()
    with xf(c, 960, 500, 0.62):
        film_frame(c, 0, 0, 1300, 760, t, scene)
    kword(c, t, 54.56, "A SCENE.", 960, 1000, 90, GOLD, style="slam", track=0.1)


def s_drift(c, t):
    a = 55.4
    cam(c, push(t, a, 62.8, 1.0, 1.04), 960, 540, t)
    fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H * 0.4, W * 0.8, ["#2a1d2e", "#0a0710"]))
    # drifting golden thought-bubbles carrying wishes
    icons = ["trophy", "heart", "coin", "env", "trophy", "heart"]
    for i in range(6):
        rnd = random.Random(i * 13)
        x = (rnd.uniform(0, W) + (t - a) * rnd.uniform(40, 90)) % (W + 400) - 200
        y = rnd.uniform(160, 900) + math.sin(t * 0.7 + i) * 30
        r = rnd.uniform(70, 110)
        soft(c, x, y, r * 1.3, GOLD, 0.2, 40)
        c.drawCircle(x, y, r, P("#fff2d6", a=0.18))
        c.drawCircle(x, y, r, P("#fff2d6", 3, 0.5))
        ic = icons[i]
        if ic == "trophy":
            trophy(c, x, y + 30, 0.35)
        elif ic == "heart":
            heart(c, x, y, 40, "#ff7a8a")
        elif ic == "coin":
            coin(c, x, y, 40)
        else:
            envelope(c, x, y, 0.4)
    c.drawRect(skia.Rect(0, 0, W, H), P("#000000", a=0.35))
    lower(c, t, 55.5, "GABRIELE OETTINGEN", "On fantasies", GOLD, y=120, dur=2.8)
    quote(c, t, 56.2, 62.0, 960, 560, 1450, 74, "#f6efe2", GOLD, "play", lead="“")
    kword(c, t, 61.6, "UNINVITED", 960, 860, 70, GOLD, style="wipe", track=0.25)


def s_shower(c, t):
    cam(c, push(t, 62.7, 63.9, 1.05, 1.12), 960, 560, t)
    bg(c, "shower", 6)
    rain_drops(c, t, (700, 150, 1700, 1080), 0.55, 50, speed=1400)
    with xf(c, 980, 830, 2.8):
        sh = skia.RRect.MakeRectXY(skia.Rect(-80, -10, 80, 200), 50, 50)
        c.drawRRect(sh, P(OL))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-76, -6, 76, 200), 46, 46), P(CAST["leo"]["skin"]))
        rrect(c, -14, -40, 28, 40, 4, shade(CAST["leo"]["skin"], 0.15))
    head_cu(c, 980, 560, "leo", "dreamy", t, 2.8, face=0.4, look=(0.5, -1), tilt=-6)
    steam(c, t, 0.6, 8)
    thought_bubbles(c, 1180, 380, 1400, 220, t, 1.0)
    loc_tag(c, t, 62.9, "IN THE SHOWER")


def s_commute(c, t):
    cam(c, push(t, 63.8, 65.0, 1.0, 1.06), 960, 540, t)
    city_scroll(c, t, (0, 120, W, 760), 520)
    bg_img = cached(("bus_frame",), lambda cc: (cc.clear(skia.ColorTRANSPARENT), set_bus(cc, 0)), 0)
    c.save()
    c.clipPath(poly([(0, 0), (W, 0), (W, 120), (0, 120)]), skia.ClipOp.kIntersect, True)
    blit(c, bg_img)
    c.restore()
    c.drawRect(skia.Rect(0, 740, W, H), P("#1b1f27"))
    for x in (0, 900):
        rrect(c, x + 60, 640, 600, 300, 30, "#3a4a6a")
    person(c, 1180, 760, "leo", "sit", "dreamy", t, 1.2, face=-0.7, look=(-1, -0.5), tilt=-5, chair=False)
    person(c, 600, 760, "job", "sitphone", "bored", t, 1.1, face=1, rim="#9fb7d9", chair=False)
    loc_tag(c, t, 64.0, "ON THE COMMUTE")


def s_ceiling(c, t):
    cam(c, push(t, 64.9, 67.5, 1.15, 1.0), 960, 540, t, drift=0.3)
    bg(c, "ceiling", 4)
    rrect(c, 360, 260, 1200, 600, 30, "#3a3560")
    rrect(c, 380, 300, 280, 520, 40, "#e8e2f0")
    person(c, 1000, 560, "leo", "lie", "dreamy", t, 1.35, rot=-90, face=1, look=(1, 0), shadow=False)
    c.drawPath(poly([(780, 300), (1540, 300), (1540, 820), (760, 820)]), P("#5a6aa0", a=0.0))
    rrect(c, 760, 450, 780, 370, 30, "#6a7ab0")
    # fan shadow sweeping
    with xf(c, 960, 540, alpha=0.18):
        ceiling_fan(c, 0, 0, 2.6, t)
    loc_tag(c, t, 65.1, "STARING AT THE CEILING")
    thought_bubbles(c, 520, 420, 420, 200, t, clamp((t - 65.5) * 2))


def s_interview(c, t):
    a = 67.4
    cam(c, push(t, a, 71.6, 1.0, 1.08), 960, 560, t, drift=0.5)
    bg(c, "office", 7)
    shake_k = window(t, 68.2, 69.4, 0.15)
    pose_l = mix_pose("stand", "shake", clamp((t - 67.9) / 0.3))
    pose_b = mix_pose("stand", "shake", clamp((t - 67.9) / 0.3))
    pump = 6 * math.sin(t * 16) * shake_k
    person(c, 780, 600 + pump * 0.2, "leo", pose_l, "happy", t, 1.15, face=1, rim="#fff2c4")
    person(c, 1160, 600, "boss", pose_b, "smile" if t < 69.3 else "happy", t, 1.15, face=-1, rim="#fff2c4")
    if t > 70.2:
        k = ease_out(at(t, 70.2, 0.8))
        envelope(c, lerp(1700, 970, k), lerp(150, 300, k) - 40 * math.sin(k * 3.14), 0.9, lerp(30, 0, k),
                 open_=clamp((t - 70.9) * 2), glow_a=0.5)
        if t > 70.9:
            kword(c, t, 70.9, "YOU'RE HIRED", 970, 170, 80, "#ffffff", style="pop")
    bokeh(c, t, "#ffffff", 16, seed=8, a=0.25)
    grade(c, "dream", 1.0)
    flash(c, t, a, "#fff4dc", 0.5, 0.8)
    kword(c, t, 68.2, "PERFECTLY.", 400, 980, 70, "#fff6e6", style="rise", end=71.4, track=0.1)


def s_noeffort(c, t):
    a = 71.5
    cam(c, push(t, a, 73.5, 1.0, 1.05), 960, 540, t, drift=0.5)
    set_dream(c, t)
    person(c, 720, 640, "leo", "cross", "bliss", t, 1.15, rim="#fff2c4", tilt=-5)
    with xf(c, 1300, 520):
        rrect(c, -200, -80, 400, 160, 30, "#ffffff", 0.85)
        dtext(c, "EFFORT", 0, -20, 46, "#7a5a3a", "bebas", track=0.2)
        rrect(c, -160, 20, 320, 34, 17, "#e8d8c0")
        v = 0.25 * (1 - ease_out(at(t, 72.3, 0.6)))
        if v > 0.01:
            rrect(c, -160, 20, 320 * v, 34, 17, RED)
        dtext(c, f"{int(v * 100)}%", 0, 140, 90, "#ffffff", "bebas")
    bokeh(c, t, "#ffffff", 16, seed=8, a=0.25)
    grade(c, "dream", 0.8)


def s_tracked(c, t):
    a = 73.4
    cam(c, push(t, a, 76.1, 1.0, 1.04), 960, 540, t)
    info_board(c, t, "#0f1117", "#06070a")
    for i, (lab, col, y) in enumerate((("EXPECTATIONS", COOL, 420), ("FANTASIES", GOLD, 660))):
        k = ease_out(at(t, 74.3 + i * 0.2, 1.2))
        icon_circle(c, 330, y, 70, col)
        dtext(c, "?" if i == 0 else "✨", 330, y + 24, 70, col, "bebas")
        line(c, 430, y, 430 + 1200 * k, y, col, 8)
        for j in range(5):
            if k * 1200 > j * 240 + 60:
                c.drawCircle(490 + j * 240, y, 14, P(col))
        dtext(c, lab, 440, y - 40, 50, col, "bebas", "left", a=k, track=0.1)
    kword(c, t, 74.32, "TRACKED BOTH", 960, 200, 100, "#f2ead6", style="type", track=0.1)


def s_graph(c, t):
    a = 76.0
    cam(c, push(t, a, 83.3, 1.0, 1.04), 960, 540, t)
    info_board(c, t, "#0f1117", "#06070a")
    # two panels: expectations (blue, up) vs fantasies (gold, down)
    for i, (lab, col, st, up) in enumerate((("POSITIVE EXPECTATIONS", COOL, 76.24, True),
                                            ("POSITIVE FANTASIES", GOLD, 80.42, False))):
        x0 = 220 + i * 820
        k = at(t, st, 0.5)
        if k <= 0:
            continue
        rrect(c, x0 - 40, 180, 720, 760, 24, "#ffffff", 0.03)
        dtext(c, lab, x0 + 320, 260, 54, col, "bebas", a=k, track=0.06)
        vals = [0.75, 0.85] if up else [0.3, 0.25]
        labs = ["EFFORT", "RESULTS"]
        for j in range(2):
            kk = ease_out(at(t, st + 1.6 + j * 0.6, 0.8))
            bx = x0 + 70 + j * 330
            hh = 480 * vals[j] * kk
            rrect(c, bx, 860 - hh, 200, hh, 12, col)
            dtext(c, labs[j], bx + 100, 910, 40, "#d8cfbf", "bebas", a=k, track=0.08)
            if kk > 0.6:
                ax = bx + 100
                if up:
                    arrow(c, ax, 860 - hh - 20, ax, 860 - hh - 120, GREEN, 16, a=clamp((kk - 0.6) * 3))
                else:
                    arrow(c, ax, 860 - hh - 120, ax, 860 - hh - 20, RED, 16, a=clamp((kk - 0.6) * 3))
    kword(c, t, 82.04, "THE REVERSE", 1460, 140, 80, RED, style="slam", track=0.06)


def s_quote1(c, t):
    a = 83.2
    cam(c, push(t, a, 91.0, 1.0, 1.05), 960, 540, t, drift=0.4)
    fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, W * 0.75, ["#1e150d", "#070504"]))
    bokeh(c, t, GOLD, 18, seed=11, a=0.1, speed=8)
    kword(c, t, 83.3, "OETTINGEN'S SUMMARY", 960, 170, 46, GOLD, "SemiBold", style="rise", track=0.3)
    quote(c, t, 85.5, 89.8, 960, 480, 1400, 84, "#f6efe2", GOLD, "play", lead="“")
    # battery drains on "drain your energy"
    k = at(t, 88.9, 0.3)
    if k > 0:
        lvl = 1 - 0.85 * ease_out(at(t, 89.1, 1.4))
        battery(c, 960, 840, 0.55 * back_out(k), lvl, t)


def s_pattern(c, t):
    a = 90.9
    cam(c, push(t, a, 94.3, 1.0, 1.05), 960, 540, t)
    info_board(c, t, "#13101a", "#07060a")
    kword(c, t, 91.3, "THE PATTERN REPEATED", 960, 200, 90, "#f2ead6", style="rise", track=0.08)
    items = [("LOVE", "#ff7a8a"), ("EXAMS", COOL), ("CAREERS", GOLD)]
    for i, (lab, col) in enumerate(items):
        k = back_out(at(t, 92.2 + i * 0.3, 0.45))
        if k <= 0:
            continue
        x = 480 + i * 480
        with xf(c, x, 580, k):
            rrect(c, -180, -200, 360, 400, 30, "#161320")
            rrect(c, -180, -200, 360, 400, 30, col, stroke=5)
            if i == 0:
                heart(c, 0, -30, 80, col)
            elif i == 1:
                rrect(c, -70, -120, 140, 180, 8, "#f2efe6")
                dtext(c, "A+", 0, 10, 90, RED, "bebas")
            else:
                rrect(c, -90, -80, 180, 120, 14, "#7a5634")
                rrect(c, -40, -110, 80, 40, 10, "#7a5634", stroke=10)
            dtext(c, lab, 0, 150, 60, col, "bebas", track=0.1)


def s_crush(c, t):
    a = 94.2
    cam(c, push(t, a, 100.4, 1.0, 1.06), 960, 560, t)
    bg(c, "cafe", 8)
    # Leo daydreams at his table; Maya walks past and leaves
    rrect(c, 300, 700, 520, 30, 8, "#5a3a26")
    line(c, 560, 730, 560, 900, "#3a2618", 14)
    person(c, 420, 700, "leo", "sitthink", "dreamy", t, 1.1, face=1, look=(0.6, -1))
    k = window(t, 95.2, 99.6, 0.4)
    if k > 0:
        thought_bubbles(c, 520, 380, 640, 250, t, k)

        def inner(cc):
            cc.save()
            cc.translate(-960, -540)
            set_dream(cc, t)
            person(cc, 840, 600, "leo", "hold", "bliss", t, 1.2, rim="#fff2c4")
            person(cc, 1080, 600, "maya", "hold", "happy", t, 1.2, face=-1, rim="#fff2c4")
            heart(cc, 960, 220, 70, "#ff6a8a")
            cc.restore()
        with xf(c, 900, 240, 0.42):
            dream_frame(c, 0, 0, 520, 300, t, inner, k)
    # Maya walks across the room and out
    if t > 97.4:
        mt = t - 97.4
        walker_person(c, 1350 + mt * walk(t, 0.9)[3] * 1.1, 560, "maya", t, 1.1, face=1, freq=0.9, expr="sad")
    else:
        person(c, 1350, 560, "maya", "stand", "neutral", t, 1.1, face=-1)
    if t > 98.0:
        kword(c, t, 98.0, "LESS LIKELY", 1300, 180, 80, RED, style="slam")


def s_exam(c, t):
    a = 100.3
    for side in (0, 1):
        c.save()
        clip_half(c, side, seed=5)
        bg(c, "exam", 8)
        x = 480 if side == 0 else 1440
        rrect(c, x - 300, 700, 600, 30, 6, "#4a3a2a")
        who = "leo" if side == 0 else "stud"
        if side == 0:
            expr = "dreamy" if t < 103.3 else "sad"
            person(c, x - 40, 700, who, "sitthink" if t < 103.3 else "sithead", expr, t, 1.05, look=(0.3, -1))
            if t < 103.3:
                thought_bubbles(c, x + 60, 380, x + 160, 250, t)
                with xf(c, x + 160, 170):
                    soft(c, 0, 0, 110, GOLD, 0.35, 30)
                    c.drawCircle(0, 0, 90, P("#fff2d6"))
                    dtext(c, "A+", 0, 30, 90, "#d14a3a", "bebas")
        else:
            person(c, x - 40, 700, who, "sitdesk", "focus", t, 1.05, face=1, look=(0.5, 0.6))
            if t > 105.8:
                tag2(c, t, 106.42, "“I'LL PROBABLY PASS”", x, 220, COOL, 40)
        # paper on desk with grade
        with xf(c, x + 150, 690, rot=-6):
            rrect(c, -70, -90, 140, 100, 6, "#f2efe6")
            for k in range(3):
                line(c, -50, -70 + k * 22, 40, -70 + k * 22, "#9aa3ad", 4)
        if side == 0 and t > 103.6:
            stamp(c, t, 103.76, "C-", x + 150, 560, RED, 120, -10)
        if side == 1 and t > 108.2:
            stamp(c, t, 108.32, "B+", x + 150, 560, GREEN, 120, -6)
        grade(c, "cold" if side == 1 else "dream", 0.4)
        c.restore()
    jagged_split(c, seed=5)
    tag2(c, t, 100.6, "PICTURED IT GOING BEAUTIFULLY", 480, 90, GOLD, 34)
    tag2(c, t, 105.1, "SIMPLY JUDGED THE ODDS", 1440, 90, COOL, 34)


def s_grads(c, t):
    a = 108.9
    if t < 113.6:
        cam(c, push(t, a, 113.7, 1.0, 1.08), 960, 560, t)
        set_dream(c, t)
        cap_y = 600 - 300 - 30 * math.sin(clamp((t - a) / 1.0) * 3.14) * 3
        person(c, 760, 600, "leo", "cheer", "bliss", t, 1.15, rim="#fff2c4")
        # grad cap tossed
        k = clamp((t - 109.4) / 1.4)
        cx, cy = 760 + 160 * k, 260 - 420 * k + 420 * k * k
        with xf(c, cx, cy, rot=k * 540):
            c.drawPath(poly([(-70, 0), (0, -30), (70, 0), (0, 30)]), P("#1a1a22"))
            line(c, 0, 0, 40, 40, GOLD, 4)
        # rosy career vision
        kk = at(t, 110.3, 0.8)
        if kk:
            thought_bubbles(c, 860, 300, 1060, 200, t, kk)

            def inner(cc):
                cc.save()
                cc.translate(-960, -540)
                set_office(cc, t)
                person(cc, 960, 600, "leo", "point_up", "proud", t, 1.2, rim="#fff2c4")
                for i in range(5):
                    coin(cc, 600 + i * 180, 200 + math.sin(t * 3 + i) * 20, 40)
                cc.restore()
            with xf(c, 1380, 260, 0.5):
                dream_frame(c, 0, 0, 520, 300, t, inner, kk)
        bokeh(c, t, "#ffffff", 16, seed=8, a=0.25)
        grade(c, "dream", 0.8)
        kword(c, t, 110.32, "ROSIEST VISIONS", 760, 960, 80, "#fff6e6", style="rise", track=0.08)
    else:
        cam(c, push(t, 113.6, 118.0, 1.0, 1.05), 960, 540, t)
        info_board(c, t, "#0f1117", "#06070a")
        calendar(c, 360, 380, 0.8, "2", "YEARS", 0)
        kword(c, t, 113.72, "TWO YEARS LATER", 360, 620, 54, "#f2ead6", style="type", track=0.12)
        bar_chart(c, 1200, 820, [("ROSY DREAMERS", 0.5, GOLD), ("THE REST", 0.8, COOL)], t, 115.4, 520, 260, 140,
                  vals=["$", "$$"])
        kword(c, t, 115.94, "LOWER SALARIES", 1200, 170, 80, RED, style="slam", track=0.06)
        person(c, 360, 860, "leo", "slump", "tired", t, 0.75, tilt=6)
        grade(c, "cold", 0.5)


# ================================================================= DREAMING ISN'T BAD
def s_host1(c, t):
    host_shot(c, t, 118.0, ("sittalk", "open", "sittalk", "present"))
    kword(c, t, 119.3, "DREAMING", 470, 380, 120, "#f2ead6", style="rise", track=0.08, end=121.0)
    kword(c, t, 120.0, "ISN'T BAD", 470, 500, 120, GOLD, style="pop", track=0.08, end=121.0)
    lower(c, t, 121.2, "REAL NEEDS", "Fantasies grow out of them", GOLD, x=150, y=420, dur=3.0)


def s_needs(c, t):
    a = 124.3
    cam(c, push(t, a, 131.5, 1.0, 1.05), 960, 540, t)
    bg(c, "living", 8)
    hungry = t > 127.2
    achieve = t > 128.2
    person(c, 960, 640, "leo", "sitthink" if t < 127.2 else "sitslump", "dreamy" if t < 126 else "tired", t, 1.15, chair=False)
    rrect(c, 650, 760, 620, 140, 40, "#3a3f5a")
    if hungry:
        for i in range(3):
            p = skia.Path()
            r = 30 + i * 22 + ((t * 40) % 22)
            p.addArc(skia.Rect(960 - r, 560 - r, 960 + r, 560 + r), -30, 60)
            c.drawPath(p, P("#f2ead6", 5, 0.5))
        tag2(c, t, 127.28, "HUNGER", 620, 400, "#ff9f5a", 50)
    if achieve:
        tag2(c, t, 128.24, "URGE TO ACHIEVE", 1300, 400, GOLD, 50)
    # number of fantasy bubbles grows with the need
    n = 2 + int(6 * clamp((t - 127.0) / 3.0))
    for i in range(n):
        rnd = random.Random(i * 5)
        ang = -2.6 + i * 0.32
        x = 960 + math.cos(ang) * (380 + rnd.uniform(-40, 40))
        y = 380 + math.sin(ang) * 260 + math.sin(t * 2 + i) * 10
        k = back_out(at(t, a + 0.5 + max(0, i - 2) * 0.35 + (2.7 if i >= 2 else 0), 0.4))
        if k <= 0:
            continue
        with xf(c, x, y, k):
            soft(c, 0, 0, 80, GOLD, 0.3, 30)
            c.drawCircle(0, 0, 62, P("#fff2d6"))
            if i % 2 == 0:
                burger(c, 0, 4, 0.36)
            else:
                trophy(c, 0, 30, 0.32)
    kword(c, t, 129.02, "MORE FANTASIES", 960, 1000, 70, GOLD, style="rise", track=0.1)


def s_burger(c, t):
    a = 131.4
    cam(c, push(t, a, 136.4, 1.0, 1.1), 960, 520, t)
    bg(c, "living", 9)
    bite = clamp((t - 132.6) / 0.5)
    person(c, 820, 640, "leo", mix_pose("hold", "phone", bite), "bliss" if t > 134.9 else "focus", t, 1.25,
           face=1)
    burger(c, lerp(1080, 960, bite), lerp(430, 380, bite), 0.9, a=0.55 + 0.2 * math.sin(t * 4), ghost=True)
    # hunger meter stays empty
    with xf(c, 1450, 560):
        rrect(c, -150, -230, 300, 460, 30, "#0b0d12", 0.7)
        dtext(c, "NEED MET", 0, -170, 50, "#f2ead6", "bebas", track=0.1)
        rrect(c, -40, -130, 80, 300, 20, "#f2ead6", stroke=6)
        fake = 0.9 * ease_out(at(t, 134.9, 0.6)) * (1 - at(t, 135.9, 0.4))
        if fake > 0.01:
            rrect(c, -30, 160 - 280 * fake, 60, 280 * fake, 14, GOLD, 0.6)
        dtext(c, "0%", 0, 225, 54, RED, "bebas")
    if t > 132.9:
        kword(c, t, 133.12, "DOES NOT MEET THE NEED", 820, 170, 70, RED, style="slam", end=134.8)
    kword(c, t, 135.08, "IT ONLY FEELS LIKE IT DID", 820, 170, 64, GOLD, style="type", track=0.06)


def s_host2(c, t):
    host_shot(c, t, 136.3, ("sittalk", "present"), period=1.0, zoom=1.08)
    k = back_out(at(t, 137.2, 0.5))
    if k > 0:
        sw = 8 * math.sin((t - 137.2) * 5) * math.exp(-(t - 137.2) * 1.5)
        with xf(c, 480, 380, k, sw):
            c.drawPath(poly([(-150, -70), (130, -70), (190, 0), (130, 70), (-150, 70)]), P(GOLD))
            c.drawCircle(120, 0, 14, P("#2a1d16"))
            dtext(c, "COST?", -20, 26, 80, "#2a1d16", "bebas", track=0.06)


# ================================================================= THE BLOOD-PRESSURE STUDIES
def s_kappes(c, t):
    a = 138.3
    cam(c, push(t, a, 148.7, 1.0, 1.06), 960, 560, t)
    bg(c, "labroom", 8)
    rrect(c, 300, 690, 1300, 40, 10, "#2a3a4c")
    person(c, 700, 690, "leo", "sitdesk", "neutral", t, 1.05, face=1, look=(0.6, 0.2))
    # cuff on his back arm area
    if t > 140.3:
        bp_cuff(c, 700, 560, 0.7, t, pump=math.sin(t * 6) * 0.5 + 0.5)
    person(c, 1200, 560, "kap", "clip", "focus", t, 1.05, face=-1, look=(-0.6, 0.3),
           hold=lambda cc, hx, hy: clipboard(cc, hx - 10, hy - 30, 0.9, -8))
    lower(c, t, 138.5, "HEATHER BARRY KAPPES", "& Gabriele Oettingen", GOLD, dur=4.0)
    if t > 140.4:
        gauge(c, 1600, 330, 0.65 * back_out(at(t, 140.44, 0.5)), 0.55 + 0.05 * math.sin(t), t, COOL)
    year_badge(c, t, 142.78, "2011", 960, 190, GOLD, 110)
    if t > 143.9:
        for i in range(4):
            k = back_out(at(t, 143.98 + i * 0.15, 0.35))
            with xf(c, 660 + i * 200, 330, max(0.001, k)):
                rrect(c, -70, -60, 140, 120, 14, "#f2efe6")
                dtext(c, str(i + 1), 0, 30, 90, "#1a2230", "bebas")
        kword(c, t, 144.3, "FOUR EXPERIMENTS", 960, 470, 50, "#f2ead6", style="rise", track=0.12, end=147.0)


def s_assigned(c, t):
    a = 148.6
    cam(c, push(t, a, 157.6, 1.0, 1.04), 960, 540, t)
    info_board(c, t, "#0f1117", "#06070a")
    kword(c, t, 148.84, "THEY ASSIGNED THEM", 960, 170, 90, "#f2ead6", style="slam", track=0.08)
    groups = [("GLOWING", GOLD, 153.1, "bliss"), ("CRITICAL", COOL, 155.42, "focus"),
              ("NEGATIVE", "#c86a6a", 156.14, "sad"), ("NEUTRAL", "#9aa3ad", 156.68, "neutral")]
    whos = ["leo", "maya", "sam", "zed"]
    for i, (lab, col, st, ex) in enumerate(groups):
        x = 300 + i * 440
        k = at(t, st - 0.3, 0.4)
        on = k > 0
        head_cu(c, x, 680, whos[i], ex if on else "neutral", t, 1.3, face=0.2, look=(0, -0.6), rim=col if on else RIM)
        with xf(c, x, 540, 0.0):
            pass
        if on:
            e = back_out(k)
            with xf(c, x, 420, e):
                soft(c, 0, 0, 120, col, 0.25, 40)
                c.drawCircle(0, 0, 96, P(col, a=0.25))
                c.drawCircle(0, 0, 96, P(col, 5))
                if i == 0:
                    sparkle(c, 0, 0, 50, "#ffffff")
                elif i == 1:
                    dtext(c, "?", 0, 34, 100, col, "bebas")
                elif i == 2:
                    cross_mark(c, 0, 0, 0.5, col)
                else:
                    line(c, -40, 0, 40, 0, col, 12)
            dtext(c, lab, x, 900, 60, col, "bebas", a=clamp(k * 2), track=0.1)
    kword(c, t, 150.46, "IMAGINE YOUR DESIRED FUTURE…", 960, 290, 46, "#d9cbb0", "play", style="type",
          end=153.0)


def s_energy(c, t):
    a = 157.5
    cam(c, push(t, a, 160.2, 1.0, 1.08), 960, 540, t)
    info_board(c, t, "#0f1117", "#06070a")
    v = 0.15 + 0.7 * ease_out(at(t, 158.2, 1.2))
    gauge(c, 960, 500, 1.4, v, t, GREEN)
    kword(c, t, 158.48, "MEASURED ENERGY", 960, 920, 90, GREEN, style="rise", track=0.12)


def s_heels(c, t):
    a = 160.1
    for side in (0, 1):
        c.save()
        clip_half(c, side, seed=8)
        x = 480 if side == 0 else 1440
        if side == 0:
            set_dream(c, t)
            person(c, x - 80, 600, "ana", "stand", "bliss", t, 1.05, face=1, rim="#fff2c4")
            thought_bubbles(c, x, 320, x + 120, 220, t)
            with xf(c, x + 170, 150):
                soft(c, 0, 0, 120, GOLD, 0.3, 40)
                c.drawCircle(0, 0, 100, P("#fff2d6"))
                high_heel(c, 0, 0, 0.8)
                sparkle(c, 60, -50, 18, GOLD)
            gauge(c, x + 190, 760, 0.6 * back_out(at(t, 165.0, 0.5)), 0.32 + 0.02 * math.sin(t), t, GOLD,
                  "BLOOD PRESSURE ↓" if t > 165.5 else None)
            grade(c, "dream", 0.6)
        else:
            bg(c, "labroom", 9)
            person(c, x - 80, 600, "ana", "think", "focus", t, 1.05, face=1, rim=COOL)
            with xf(c, x + 170, 150):
                c.drawCircle(0, 0, 100, P("#1b2733"))
                c.drawCircle(0, 0, 100, P(COOL, 5))
                high_heel(c, 0, 0, 0.8, "#9aa3ad")
                dtext(c, "?", 60, -20, 70, COOL, "bebas")
            gauge(c, x + 190, 760, 0.6 * back_out(at(t, 166.6, 0.5)), 0.68 + 0.02 * math.sin(t), t, COOL,
                  "HIGHER" if t > 167.2 else None)
            grade(c, "cold", 0.5)
        c.restore()
    jagged_split(c, seed=8)
    tag2(c, t, 161.96, "IMAGINED LOOKING GREAT", 480, 90, GOLD, 36)
    tag2(c, t, 166.86, "THOUGHT CRITICALLY", 1440, 90, COOL, 36)


def s_bars(c, t):
    a = 169.5
    cam(c, push(t, a, 179.7, 1.0, 1.04), 960, 540, t)
    info_board(c, t, "#0f1117", "#06070a")
    if t < 176.2:
        kword(c, t, 169.7, "ENERGY AFTER IMAGINING", 960, 150, 60, "#f2ead6", style="rise", track=0.14)
        bar_chart(c, 960, 820, [("GLOWING", 0.32, GOLD), ("CRITICAL", 0.72, COOL), ("NEGATIVE", 0.68, "#c86a6a"),
                                ("NEUTRAL", 0.7, "#9aa3ad")], t, 170.4, 480, 220, 90)
        if t > 172.6:
            tag2(c, t, 172.6, "LESS ENERGY", 465, 470, RED, 44)
            arrow(c, 465, 520, 465, 600, RED, 12, a=clamp((t - 172.7) * 3))
    else:
        kword(c, t, 176.34, "THE DRAIN GROWS", 960, 150, 80, "#f2ead6", style="rise", track=0.1)
        need = ease_out(at(t, 177.2, 1.4))
        # slider
        line(c, 460, 360, 1460, 360, "#3a3f4a", 16)
        line(c, 460, 360, 460 + 1000 * need, 360, RED, 16)
        c.drawCircle(460 + 1000 * need, 360, 30, P("#f2ead6"))
        dtext(c, "HOW BADLY YOU NEED IT", 960, 300, 40, "#a9a092", "bebas", track=0.14)
        # energy drain drips
        battery(c, 960, 700, 0.9, 1 - 0.85 * need, t)
        for i in range(int(2 + 8 * need)):
            ky = ((t * (1 + need) + i * 0.17) % 1.0)
            c.drawCircle(960 + math.sin(i * 7) * 50, 870 + ky * 200, 10, P(GREEN, a=1 - ky))


def s_morewant(c, t):
    a = 179.6
    cam(c, push(t, a, 183.6, 1.0, 1.08), 960, 560, t)
    bg(c, "bedroom", 9)
    g = ease_out(at(t, 180.1, 2.0))
    person(c, 760, 680, "leo", "sitthink", "dreamy" if g < 0.8 else "tired", t, 1.15, face=1, look=(0.5, -1))
    r = 120 + 230 * g
    with xf(c, 1260, 330):
        soft(c, 0, 0, r * 1.2, GOLD, 0.3, 50)
        c.drawCircle(0, 0, r, P("#fff2d6", a=0.85))
        trophy(c, 0, 40 * (r / 200), r / 260)
    thought_bubbles(c, 860, 380, 1060, 300, t)
    battery(c, 360, 520, 0.6, 1 - 0.9 * g, t)
    kword(c, t, 179.8, "THE MORE YOU WANT IT", 960, 960, 64, "#f2ead6", style="rise", track=0.08, end=181.2)
    kword(c, t, 181.3, "THE MORE IT COSTS", 960, 960, 74, RED, style="slam", track=0.08)
