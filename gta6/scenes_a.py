"""Part 1 of the timeline: birth -> prison -> Jason -> the setup -> road to Vice City (0:00-4:43)."""
from common import *  # noqa: F401,F403
from common import shot, wt, marker_circle
import math


# ======================================================================= HOOK
@shot(0.0, 5.1, "GTA VI · LEONIDA")
def s_hook(c, t, lt, d):
    p = wt("punch", 3.3)
    with xf(c):
        cam(c, lt, d, 1.0, 1.08, cx=900, t=t, shake=0.35 * window(t, p, p + 0.3, 0.05))
        draw_bg(c, "vice_sunset")
        car(c, 420, 930, 0.9, "#d8262e", t, kind="conv")
        pose = "punch" if t > p - 0.1 else "stand"
        person(c, 1180, 1560, "lucia", "lucia", pose, "determined" if t > p else "neutral", t, s=2.95,
               look=(-2, 0))
        if t > p:
            burst(c, 1700, 610, 110 * pop(t, p, 0.25), "#ffd23f", t * 0.5)
            T(c, "POW!", 1700, 635, 70 * pop(t, p, 0.25), "#d8262e", BANG, outline="#141414", ow=8)
    tag(c, 700, 200, "LUCIA CAMINOS", 46, a=fade(t, 0.8), s=pop(t, 0.8))
    r = wt("read", 4.5)
    if t > r - 0.2:
        with xf(c, 520, 700 + (t - r) * 900, rot=(t - r) * 200):
            box(c, -90, -60, 180, 120, "#3a7ad8", r=8)
            T(c, "ABC", 0, 18, 50, "#ffffff", LUCKY)


@shot(5.1, 10.3)
def s_prison_love(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.05, 1.0, t=t)
        draw_bg(c, "cell")
        person(c, 960, 1000, "lucia", "lucia_p", "cross", "sad", t, s=1.6)
        k = ease_out(at(t, 5.2, 0.6))
        with xf(c, 0, -H * (1 - k)):
            bars(c, 300, 1620, -40, H + 40, n=10, col="#6c7784")
    trust = wt("trust", 8.0)
    k = pop(t, trust - 0.1, 0.45)
    if k > 0:
        mug(c, 1560, 430, "jason", label="JASON?", expr="smirk", rot=6, s=k * 1.05, t=t)
    caption_serif(c, "for the people you love", 960, 1010, 46, a=window(t, 5.8, 7.6))


@shot(10.3, 13.4)
def s_fork(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.08, t=t)
        draw_bg(c, "road_night")
        pth = poly([(860, 640), (1060, 640), (1500, H), (420, H)])
        c.drawPath(pth, P("#2a2a34"))
        for k in range(8):
            y = 660 + k * 60 + (t * 160) % 60
            rect(c, 955, y, 10, 30 + k * 4, "#f2e6b8")
        # sign post
        line(c, 1500, 900, 1500, 380, OUT, 16)
        line(c, 1500, 900, 1500, 380, "#8a8a8a", 9)
        for i, (lab, col, yy, sx) in enumerate((("WAY OUT", "#2e8b57", 420, 1), ("END OF THE ROAD", "#c0392b", 540, -1))):
            tm = wt("way", 11.5) if i == 0 else wt("end", 12.4)
            k = pop(t, tm - 0.1, 0.35)
            if k <= 0:
                continue
            with xf(c, 1500, yy, s=k):
                w = tw(lab, 40, LUCKY) + 80
                pts = [(0, -40), (sx * w, -40), (sx * (w + 40), 0), (sx * w, 40), (0, 40)]
                shape(c, poly(pts), col, ow=6)
                T(c, lab, sx * (w / 2 + 10), 15, 40, "#ffffff", LUCKY)
        car(c, 960, 1020, 0.55, "#d8262e", t, moving=0.4, kind="conv", lights=1.0,
            people=[(-40, "jason", "jason", "neutral"), (60, "lucia", "lucia", "worried")])


@shot(13.4, 18.6, "GTA VI · LEONIDA")
def s_baby_map(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.12, cx=980, cy=560, t=t)
        draw_bg(c, "map")

        def inner(cc, iw, ih):
            blit_scaled_set(cc, "living", iw, ih)
            person(cc, iw * 0.35, ih * 0.98, "mom", "mom", "hold", "happy", t, s=0.55,
                   prop=lambda c2: baby_bundle(c2, 0, -150, 1.1, t))
            person(cc, iw * 0.68, ih * 0.98, "dad", "dad", "stand", "smile", t, s=0.55)

        k = ease_out(at(t, 13.5, 0.6))
        polaroid(c, 960, 560 - (1 - k) * 700, 700, 640, inner, "THE CAMINOS", rot=-3, a=1)
    b = wt("baby", 14.9)
    tag(c, 760, 330, "YOU", 36, a=fade(t, b), s=pop(t, b))
    k = pop(t, wt("wants", 16.0), 0.4)
    if k > 0:
        with xf(c, 1480, 300, s=k):
            thought(c, 0, 0, 300, 220)
            T(c, "$ $ $", 0, 20, 70, "#2e8b57", LUCKY)


def blit_scaled_set(c, name, w, h):
    img = bg(name)
    c.drawImageRect(img, skia.Rect(0, 0, w, h), skia.SamplingOptions(skia.FilterMode.kLinear))


import skia  # noqa: E402


@shot(18.6, 24.4)
def s_mom_liberty(c, t, lt, d):
    lib = wt("liberty", 19.7)
    if t < 21.0:
        with xf(c):
            cam(c, lt, 2.4, 1.0, 1.06, t=t)
            draw_bg(c, "dark")
            grad_rect(c, 120, 200, 1680, 640, ["#8b9bb0", "#c9d2dc"])
            skyline(c, 840, "#5b6678", seed=5, hmin=140, hmax=520, wmin=40, wmax=110)
            c.drawRect(skia.Rect(120, 200, 1800, 840), P(OUT, 8))
            arrow(c, 200, 920, 1500, 920, "#e8282e", 10, prog=ease_out(at(t, 18.8, 1.0)), dashed=True)
            marker_text(c, "LIBERTY CITY", 960, 170, 90, a=fade(t, lib - 0.1))
            caption_serif(c, "where your mother comes from", 960, 1010, 42, a=fade(t, 19.3))
    else:
        with xf(c):
            cam(c, t - 21.0, 3.4, 1.0, 1.08, cx=900, t=t)
            draw_bg(c, "living")
            person(c, 760, 1010, "mom", "mom", "hold", "smile", t, s=1.35,
                   prop=lambda c2: baby_bundle(c2, 0, -150, 1.1, t))
            tag(c, 760, 400, "MOM", 34, a=fade(t, 21.1))
        dr = wt("dream", 22.0)
        k = pop(t, dr - 0.1, 0.45)
        if k > 0:
            with xf(c, 1300, 330, s=k):
                thought(c, 0, 0, 420, 300)
                dream_house(c, 0, 90, 0.55, t)


skyline = __import__("sets").skyline


@shot(24.4, 30.8)
def s_good_life(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "street")
        rect(c, 0, 0, W, H, "#fff3d8", 0.25)
        lock = at(t, wt("locks", 29.9) - 0.2, 0.6)
        dream_house(c, 1320, 820, 1.7, t, lock=lock)
    big_title(c, "THE GOOD LIFE", 960, 170, 110, t, 24.5, "#ffd23f")
    checklist(c, 140, 420, ["MONEY", "SAFETY", "A DOOR THAT LOCKS"], t,
              [wt("money", 26.7), wt("safety", 27.5), wt("door", 28.9)], size=58)


@shot(30.8, 34.7)
def s_keep_dream(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.02, 1.12, t=t)
        draw_bg(c, "cork")

        def inner(cc, iw, ih):
            grad_rect(cc, 0, 0, iw, ih, ["#7cc7ec", "#fff3d8"])
            dream_house(cc, iw / 2, ih - 20, 0.9, t)

        polaroid(c, 960, 500, 560, 600, inner, "THE GOOD LIFE", rot=-4)
    marker_text(c, "KEEP THIS IN MIND", 960, 920, 70, a=fade(t, 31.0), rot=-3)
    k = fade(t, wt("decides", 32.5))
    if k > 0:
        stamp(c, 1450, 300, "IT DECIDES EVERYTHING", 46, a=k, s=lerp(1.4, 1, k), rot=12)


# ======================================================================= FATHER
@shot(34.7, 40.6, "GTA VI · LEONIDA")
def s_father(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.08, t=t)
        draw_bg(c, "yard")
        tch = wt("teaches", 39.0)
        person(c, 1150, 1000, "dad", "dad", "guard" if t > tch - 0.3 else "stand", "determined" if t > tch else "smile",
               t, s=1.5)
        wk = wt("walk", 38.1)
        if t < tch:
            x = lerp(500, 720, smooth(at(t, 37.2, 1.5)))
            person(c, x, 1000, "lucia", "lucia_kid", "walk" if t > 37.2 else "stand", "happy", t, s=1.1,
                   walk=t if 37.2 < t < 38.7 else 0)
        else:
            person(c, 720, 1000, "lucia", "lucia_kid", "guard", "determined", t, s=1.1)
    tag(c, 1150, 380, "DAD", 34, a=fade(t, 35.3))
    k = pop(t, wt("gift", 36.4), 0.4)
    if k > 0 and t < 38.0:
        with xf(c, 520, 340, s=k):
            box(c, -90, -70, 180, 140, "#d8262e", r=8)
            rect(c, -15, -70, 30, 140, "#ffd23f")
            T(c, "?", 0, 22, 70, "#ffffff", LUCKY)


@shot(40.6, 46.8)
def s_fists(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.12, 1.0, cx=900, cy=600, t=t)
        draw_bg(c, "yard", blur=6)
        hit = wt("hit", 42.2)
        person(c, 860, 1100, "lucia", "lucia_kid", "punch" if t > hit - 0.1 else "guard", "determined", t, s=1.9)
    for i, (lab, tm, col) in enumerate((("FISTS UP", wt("fists", 40.7), "#ffd23f"),
                                        ("CHIN DOWN", wt("chin", 41.4), "#ffd23f"),
                                        ("HIT FIRST", wt("hit", 42.2), "#ff4a4a"))):
        k = pop(t, tm - 0.05, 0.3)
        if k > 0:
            with xf(c, 1450, 300 + i * 170, s=k, rot=-3):
                T(c, lab, 0, 30, 96, col, LUCKY, outline="#141414", ow=12)
    lv = wt("love", 46.3)
    k = pop(t, lv - 0.15, 0.4)
    if k > 0:
        heart(c, 560, 380, 2.4 * k)
    caption_serif(c, "It's not cruelty.", 960, 1010, 46, a=window(t, 43.8, 45.3))


@shot(46.8, 53.7)
def s_rigged(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "dark")
        # scale of justice tilted
        tilt = math.radians(lerp(0, 16, smooth(at(t, 49.5, 1.0))))
        with xf(c, 960, 620):
            line(c, 0, -360, 0, 260, "#c9a24a", 20)
            box(c, -160, 250, 320, 40, "#c9a24a", r=8)
            oval(c, 0, -370, 30, 30, "#e8c25a")
            ex, ey = math.cos(tilt) * 420, math.sin(tilt) * 420
            line(c, -ex, -ey - 340, ex, ey - 340, "#e8c25a", 16)
            for sx, lab, col in ((-1, "PEOPLE LIKE YOU", "#9fd3ef"), (1, "$$$", "#7dff8a")):
                px, py = sx * ex, sx * ey - 340
                line(c, px, py, px - 110, py + 220, "#c9a24a", 4)
                line(c, px, py, px + 110, py + 220, "#c9a24a", 4)
                pth = skia.Path()
                pth.moveTo(px - 140, py + 220)
                pth.quadTo(px, py + 300, px + 140, py + 220)
                pth.close()
                shape(c, pth, "#e8c25a")
                T(c, lab, px, py + 200, 40 if sx < 0 else 70, col, LUCKY, outline="#141414", ow=8)
    k = fade(t, wt("rigged", 50.0) - 0.1)
    if k > 0:
        stamp(c, 960, 170, "THE GAME IS RIGGED", 74, a=k, s=lerp(1.5, 1, ease_out(k)), rot=-4)
    caption_serif(c, "and nobody is coming to fix it", 960, 1010, 46, a=fade(t, wt("nobody", 51.7)))


@shot(53.7, 57.2)
def s_years(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.04, t=t)
        draw_bg(c, "living", blur=8)
        tint_c(c, "#1a0f0a", 0.35)
        n = int(clamp((t - 53.8) / 2.6) * 18)
        year = 1990 + n
        with xf(c, 960, 520):
            box(c, -230, -260, 460, 520, "#f7f3ea", r=12, ow=7)
            box(c, -230, -260, 460, 120, "#d8262e", r=12, ow=7)
            T(c, "YEAR", 0, -180, 50, "#ffffff", LUCKY)
            T(c, str(year), 0, 90, 170, "#141414", LUCKY)
            for k in range(-2, 3):
                oval(c, k * 80, -260, 14, 14, "#9a9a9a", ow=3)
    k = fade(t, wt("cute", 55.2))
    if k > 0:
        mug(c, 420, 520, "lucia", "lucia_baby", "CUTE BABY", "happy", rot=-8, t=t, xmark=at(t, wt("gone", 55.9), 0.5))


def tint_c(c, col, a):
    c.drawRect(skia.Rect(0, 0, W, H), P(col, a=a))


@shot(57.2, 62.0, "GTA VI · LEONIDA")
def s_teen(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.08, t=t)
        draw_bg(c, "street")
        person(c, 960, 1020, "lucia", "lucia_teen", "cross", "smirk", t, s=1.55)
    for i, (lab, tm, x, y) in enumerate((("SHARP", wt("sharp", 57.6), 520, 380),
                                         ("STUBBORN", wt("stubborn", 58.1), 1420, 330),
                                         ("LOYAL", wt("loyal", 58.6), 1420, 560))):
        tag(c, x, y, lab, 54, a=fade(t, tm - 0.05, 0.15), s=pop(t, tm - 0.05), rot=(-4 if i % 2 else 4))
    k = pop(t, wt("swinging", 60.8), 0.3)
    if k > 0:
        with xf(c, 450 + (1 - k) * -400, 650, rot=-20):
            oval(c, 0, 0, 70, 60, "#d8262e")
            T(c, "LIFE", 0, 12, 34, "#ffffff", LUCKY)


@shot(62.0, 64.6)
def s_swing_back(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.1, 1.0, shake=0.3 * window(t, 62.2, 62.8, 0.1), t=t)
        draw_bg(c, "gym")
        person(c, 860, 1000, "lucia", "lucia_box", "punch", "angry", t, s=1.6)
        sw = math.sin(t * 5.5)
        with xf(c, 1240, 0, rot=sw * 6):
            line(c, 0, 0, 0, 300, OUT, 6)
            box(c, -70, 300, 140, 360, "#a8282c", r=55)
            T(c, "LIFE", 0, 500, 50, "#ffffff", LUCKY, rot=90)
    big_title(c, "HARDER.", 1400, 880, 110, t, wt("harder", 62.3), "#ffd23f")


@shot(64.6, 69.7)
def s_mother(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.1, cx=880, t=t)
        draw_bg(c, "living")
        person(c, 860, 1020, "lucia", "lucia", "hold", "happy", t, s=1.5,
               prop=lambda c2: baby_bundle(c2, 0, -150, 1.1, t, "tommy", "tommy", "#8fc6ef"))
    tm = wt("tommy", 65.6)
    tag(c, 860, 400, "TOMMY", 40, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1))
    k = pop(t, wt("first", 66.7), 0.4)
    for i in range(3):
        if k > 0:
            hy = 300 - ((t - 66.7) * 60 + i * 50) % 160
            heart(c, 1180 + i * 60, hy, 0.9 * k, a=0.9)
    caption_serif(c, "not just fighting for yourself", 960, 1010, 46, a=fade(t, wt("not", 67.7)))


@shot(69.7, 72.5)
def s_worst_day(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.15, t=t)
        draw_bg(c, "living_night")
        person(c, 860, 1020, "lucia", "lucia", "hold", "worried", t, s=1.5,
               prop=lambda c2: baby_bundle(c2, 0, -150, 1.1, t, "tommy", "tommy", "#8fc6ef", "neutral"))
    tint_c(c, "#000000", 0.4 * smooth(at(t, 70.5, 1.5)))
    big_title(c, "THE WORST DAY", 960, 540, 120, t, wt("worst", 70.7), "#ff4a4a")


# ======================================================================= ROBBERY
@shot(72.5, 77.4, "PAYDAY LOANS · LEONIDA")
def s_robbery(c, t, lt, d):
    al = wt("alarms", 75.4)
    with xf(c):
        cam(c, lt, d, 1.0, 1.08, shake=0.25 if t > al else 0, t=t)
        draw_bg(c, "store")
        run = smooth(at(t, 73.0, 2.5))
        person(c, lerp(960, 1500, run), 1000, "lucia", "lucia", "bag", "scared" if t > al else "determined", t,
               s=1.3, walk=t if 73.0 < t < 75.5 else 0, prop=lambda c2: money_bag(c2, 90, -60, 0.9))
        if t > al:
            if int(t * 4) % 2 == 0:
                tint_c(c, "#ff1a2a", 0.28)
            for k, x in enumerate((300, 1620)):
                glow(c, x, 120, 140, "#ff2a3a", 0.6 * (0.5 + 0.5 * math.sin(t * 16 + k)))
                oval(c, x, 120, 34, 34, "#ff2a3a")
    k = fade(t, wt("wrong", 74.5) - 0.1)
    if k > 0:
        stamp(c, 600, 300, "GONE WRONG", 80, a=k, s=lerp(1.6, 1, ease_out(k)), rot=-10)
    for i, (lab, tm) in enumerate((("ALARMS!", al), ("SIRENS!", wt("sirens", 76.3)))):
        k = pop(t, tm, 0.3)
        if k > 0:
            T(c, lab, 380 + i * 1150, 820 - i * 60, 90 * k, "#ffd23f", BANG, outline="#141414", ow=10, rot=-6 + i * 10)


@shot(77.4, 79.1)
def s_chase(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.04, shake=0.15, t=t)
        draw_bg(c, "vice_night")
        rect(c, 0, 830, W, 250, "#1c1a2a")
        for k in range(10):
            x = (k * 240 - t * 1600) % (W + 240) - 120
            rect(c, x, 960, 120, 12, "#f2e6b8")
        car(c, 1250, 1000, 0.8, "#2a2a34", t, moving=1.0, kind="sedan")
        car(c, 520, 1010, 0.8, "#16161c", t, moving=1.0, kind="cop")
    speedlines(c, t, 0.25)
    big_title(c, "CHASE!", 960, 200, 120, t, wt("chase", 77.6), "#ffffff")


@shot(79.1, 84.3)
def s_coffee(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "cafe")
        # baby carrier on table
        with xf(c, 1300, 790):
            box(c, -80, -70, 160, 70, "#5a8ac8", r=30)
            pth = skia.Path()
            pth.moveTo(-70, -60)
            pth.quadTo(0, -170, 70, -60)
            c.drawPath(pth, P(OUT, 12))
            c.drawPath(pth, P("#5a8ac8", 6))
            with xf(c, 0, -80):
                head(c, "tommy", "tommy", 36, "worried", t)
        tag(c, 1300, 600, "TOMMY", 32, a=fade(t, 79.5))
        marker_circle(c, 1300, 730, 150, 110, at(t, 79.6, 0.7))
        run = wt("run", 82.4)
        if t > run - 0.3:
            x = lerp(-200, 700, smooth(at(t, run - 0.3, 1.5)))
            person(c, x, 1010, "lucia", "lucia", "walk", "scared", t, s=1.3, walk=t)
    # clock
    with xf(c, 360, 260, s=pop(t, wt("every", 81.1), 0.3)):
        oval(c, 0, 0, 110, 110, "#f7f3ea", ow=8)
        a = t * 4
        line(c, 0, 0, math.sin(a) * 80, -math.cos(a) * 80, "#d8262e", 7)
        line(c, 0, 0, 0, -55, OUT, 9)
        T(c, "TICK", 0, 170, 40, "#ffffff", LUCKY, outline="#141414", ow=8)


@shot(84.3, 89.4)
def s_cops_door(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.08, t=t)
        draw_bg(c, "cafe")
        tint_c(c, "#1a2a6a", 0.15)
        for k, x in enumerate((260, 1700)):
            glow(c, x, 500, 300, "#ff2a3a" if (int(t * 6) + k) % 2 else "#2a6aff", 0.35)
        person(c, 780, 1000, "cop", "cop", "point", "angry", t, s=1.3)
        person(c, 1120, 1000, "cop2", "cop", "stand", "angry", t, s=1.3, label="POLICE", label_a=fade(t, wt("police", 87.7)))
    k = fade(t, wt("reported", 85.5))
    if k > 0:
        phone_screen(c, 1580, 520, 0.8 * k, lambda cc: (grad_rect(cc, -150, -300, 300, 600, ["#1c2a4a", "#0e1628"]),
                                                       T(cc, "911", 0, -120, 80, "#ff4a4a", LUCKY),
                                                       T(cc, "BABY LEFT", 0, 20, 40, "#ffffff", "inter"),
                                                       T(cc, "ALONE", 0, 70, 40, "#ffffff", "inter")), rot=8)


@shot(89.4, 94.3)
def s_custody(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "cafe", blur=5)
        tint_c(c, "#1a2a6a", 0.2)
        person(c, 650, 1000, "cop", "cop", "stand", "neutral", t, s=1.3)
        person(c, 900, 1000, "lucia", "lucia", "cuffed", "cry", t, s=1.3)
        tk = wt("taken", 91.3)
        x = lerp(1350, 1900, smooth(at(t, tk, 2.5)))
        person(c, x, 1000, "counselor", "counselor", "hold", "neutral", t, s=1.3, walk=t if t > tk else 0,
               prop=lambda c2: baby_bundle(c2, 0, -150, 1.1, t, "tommy", "tommy", "#8fc6ef", "cry"))
    k = pop(t, wt("handcuffs", 89.4), 0.35)
    if k > 0:
        with xf(c, 400, 300, s=k, rot=-12):
            for sx in (-1, 1):
                c.drawCircle(sx * 60, 0, 50, P("#c9c9c9", 14))
                c.drawCircle(sx * 60, 0, 50, P(OUT, 4))
            line(c, -10, 0, 10, 0, "#c9c9c9", 10)
    tag(c, 1500, 330, "CHILD WELFARE", 38, a=fade(t, wt("child", 91.9)))


# ======================================================================= PRISON
@shot(94.3, 101.8, "LEONIDA PENITENTIARY")
def s_cell(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.12, cx=760, cy=600, t=t)
        draw_bg(c, "cell")
        person(c, 470, 745, "lucia", "lucia_p", "sit", "sad", t, s=1.25, look=(4, -1))
    k = fade(t, wt("orange", 95.4))
    if k > 0:
        tag(c, 600, 380, "ORANGE JUMPSUIT", 34, a=k, s=pop(t, wt("orange", 95.4)))
    caption_serif(c, "staring at a concrete wall", 960, 1010, 46, a=fade(t, wt("staring", 98.7)))


@shot(101.8, 105.4)
def s_two_things(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "cell", blur=4)
        tint_c(c, "#000000", 0.25)
        with xf(c, 960, 500):
            box(c, -560, -320, 1120, 640, "#8d9298", ow=0)
    T(c, "ONLY TWO THINGS", 960, 260, 70, "#f2f2f2", MARKER, rot=-2)
    marker_text(c, "1. GET OUT", 700, 520, 110, "#ffffff", a=fade(t, wt("get", 103.8) - 0.1), rot=-3, align="left")
    marker_text(c, "2. GET TOMMY BACK", 700, 720, 110, "#ffd23f", a=fade(t, wt("get", 104.3) - 0.1), rot=-2,
                align="left")
    


@shot(105.4, 117.0)
def s_counselor(c, t, lt, d):
    nm = wt("name", 114.4)
    z1 = 1.3 if t > nm - 0.5 else 1.05
    with xf(c):
        cam(c, lt, d, 1.0, 1.1, cx=960, cy=560, t=t)
        if t > nm - 0.5:
            k = smooth(at(t, nm - 0.5, 1.2))
            c.translate(W / 2, H / 2)
            c.scale(1 + k * 0.25, 1 + k * 0.25)
            c.translate(-W / 2, -H / 2 - 80 * k)
        draw_bg(c, "office")
        person(c, 600, 760, "lucia", "lucia_p", "stand", "neutral", t, s=1.1, talk=0.6 * window(t, 110.0, 112.3))
        person(c, 1320, 760, "counselor", "counselor", "stand", "neutral", t, s=1.1,
               talk=0.7 * (window(t, 105.5, 109.4) + window(t, 113.2, 114.8)))
        box(c, 300, 760, 1320, 60, "#8a6a4a", r=6)
    tag(c, 1320, 280, "PRISON COUNSELOR", 32, a=fade(t, wt("counselor", 105.9)) * (1 - fade(t, 112.5)))
    speech(c, 1260, 200, ["EARLY RELEASE?"], 40, a=window(t, wt("early", 108.8) - 0.1, 110.8),
           s=pop(t, wt("early", 108.8) - 0.1), tail=(40, 90))
    caption_serif(c, "calm... like someone who has run out of tears", 960, 1010, 42, a=window(t, 110.2, 113.0))
    k = fade(t, nm - 0.1)
    if k > 0:
        speech(c, 1250, 230, ["...JASON DUVAL."], 46, a=k, s=pop(t, nm - 0.1), tail=(40, 90))


@shot(117.0, 122.3)
def s_jason_reveal(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "cork")
        k = pop(t, 117.0, 0.4)
        mug(c, 960, 520, "jason", label="JASON DUVAL", expr="smirk", rot=-3, s=1.35 * k, t=t, bgcol="#cfe3e8")
    tag(c, 1460, 300, "WHO IS HE?", 40, a=fade(t, wt("who", 117.9)), rot=6)
    tag(c, 460, 760, "PARTNER?", 44, a=fade(t, wt("partner", 119.0)), rot=-6, bg="#ffd23f")
    if t > wt("while", 119.9):
        with xf(c, 420, 330, s=pop(t, wt("while", 119.9))):
            box(c, -150, -110, 300, 220, "#8d9298", ow=6)
            bars(c, -140, 140, -100, 100, n=4)
            T(c, "YOU", 0, 150, 34, "#ffffff", LUCKY, outline="#141414", ow=6)


@shot(122.3, 129.4, "LEONIDA KEYS")
def s_keys(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.08, cx=1100, t=t)
        draw_bg(c, "keys_night")
        bob = math.sin(t * 1.6) * 6
        with xf(c, 0, bob):
            person(c, 1250, 690, "jason", "jason", "hold", "neutral", t, s=0.9,
                   prop=lambda c2: box(c2, -60, -170, 120, 90, "#b98a58", r=4, ow=4))
        person(c, 380, 770, "brian", "brian", "point", "smirk", t, s=1.0)
    tag(c, 1250, 300, "JASON", 34, a=fade(t, 122.5))
    marker_circle(c, 1250, 560, 120, 200, at(t, 122.6, 0.8))
    tag(c, 380, 340, "BRIAN HEDER", 34, a=fade(t, wt("brian", 125.1)))
    tag(c, 960, 140, "SMUGGLING JOBS", 46, a=fade(t, wt("smuggling", 123.5)), bg="#ffd23f")
    for i, (lab, tm) in enumerate((("NOT RICH", wt("rich", 127.0)), ("NOT SAFE", wt("safe", 128.4)))):
        k = fade(t, tm - 0.1)
        if k > 0:
            stamp(c, 760 + i * 520, 470, lab, 60, a=k, s=lerp(1.5, 1, ease_out(k)), rot=-8 + i * 12)


@shot(129.4, 136.4)
def s_better_life(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "cork")
        mug(c, 560, 520, "jason", label="JASON", expr="smile", rot=-5, t=t, bgcol="#cfe3e8")
        mug(c, 1360, 520, "lucia", "lucia_p", "LUCIA", "smile", rot=5, t=t, bgcol="#f2d6c0")
        red_string(c, [(560, 335), (960, 420), (1360, 335)], ease_out(at(t, 129.8, 1.5)))
        k = pop(t, wt("possible", 131.9) - 0.3, 0.4)
        heart(c, 960, 430, 1.5 * k)
    caption_serif(c, "the one person who makes a better life feel possible", 960, 1010, 42, a=fade(t, 130.0))
    k = fade(t, wt("too", 134.6))
    if k > 0:
        T(c, "...and you're that person for him too", 960, 900, 40, "#ffd23f", SERIF, a=k)


@shot(136.4, 143.0, "LEONIDA PENITENTIARY")
def s_released(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "gate")
        from sets import set_gate_open
        set_gate_open(c, smooth(at(t, wt("released", 139.5), 1.5)))
        rel = wt("released", 139.5)
        if t > rel:
            x = lerp(960, 760, smooth(at(t, rel + 0.3, 1.5)))
            person(c, x, 960, "lucia", "lucia", "walk" if t < rel + 1.8 else "wave", "happy", t, s=1.25,
                   walk=t if t < rel + 1.8 else 0)
        car(c, 1460, 1000, 0.75, "#d8262e", t, kind="conv")
        person(c, 1250, 960, "jason", "jason", "wave" if t > wt("waiting", 141.6) else "stand", "smile", t, s=1.25)
    k = pop(t, wt("luck", 138.0), 0.4)
    if k > 0 and t < 140:
        with xf(c, 360, 250, s=k):
            for i in range(4):
                ang = i * math.pi / 2
                oval(c, math.cos(ang) * 45, math.sin(ang) * 45, 45, 45, "#3ccf6a")
            line(c, 0, 40, 20, 140, "#2e8b57", 10)
    if t > wt("released", 139.5):
        k = fade(t, wt("released", 139.5))
        stamp(c, 960, 200, "RELEASED EARLY", 74, a=k, s=lerp(1.5, 1, ease_out(k)), color="#2e8b57", rot=-6)


@shot(143.0, 147.4, "THE RUSTY ANCHOR")
def s_bar(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.07, t=t)
        draw_bg(c, "bar")
        person(c, 760, 900, "lucia", "lucia", "raise" if 143.6 < t < 145.2 else "stand", "laugh", t, s=1.2)
        person(c, 1160, 900, "jason", "jason", "raise" if 143.6 < t < 145.2 else "stand", "happy", t, s=1.2)
        box(c, 0, 680, W, 70, "#8a5a3a", r=10, ow=6)
        for x in (720, 1200):
            box(c, x - 22, 600, 44, 80, "#e8b23a", r=6, ow=4)
            rect(c, x - 18, 604, 36, 16, "#ffffff", 0.9)
    k = pop(t, 143.4, 0.3)
    if k > 0 and t < 145.5:
        T(c, "CHEERS!", 960, 470, 70 * k, "#ffd23f", BANG, outline="#141414", ow=8)


@shot(147.4, 152.4)
def s_one_night(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.08, t=t)
        draw_bg(c, "house_night")
        for i in range(6):
            x = (i * 330 + t * 20) % W
            sparkle(c, x, 120 + (i * 70) % 260, 10 + 4 * math.sin(t * 3 + i), "#ffffff", a=0.8)
    caption_serif(c, "For one night, nobody is chasing you.", 960, 1010, 48, a=fade(t, 147.5))


@shot(152.4, 158.1, "SUBSCRIBE")
def s_subscribe(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.04, t=t)
        draw_bg(c, "dark")
        with xf(c, 960, 520, rot=-1.5):
            box(c, -620, -380, 1240, 760, "#efe2c4", r=8)
            line(c, 0, -380, 0, 380, "#c9b89a", 6)
            T(c, "QUICK PAUSE", -310, -260, 56, "#2a1a12", LUCKY)
            T(c, "Who should be", -310, -150, 50, "#2a1a12", SERIF)
            T(c, "born next?", -310, -90, 50, "#2a1a12", SERIF)
            for i, nm_ in enumerate(("Jason Duval", "Brian Heder", "Raul", "Boobie")):
                k = fade(t, 153.3 + i * 0.5)
                box(c, -540, 0 + i * 80, 460, 62, "#ffffff", r=10, a=k, ow=3)
                T(c, nm_, -520, 42 + i * 80, 32, "#2a1a12", "interb", align="left", a=k)
                T(c, f"♥ {(4 - i) * 3}.{i + 1}k", -110, 42 + i * 80, 26, "#d8262e", "interb", align="right", a=k)
            # subscribe button
            sb = wt("subscribe", 152.8)
            pressed = 1 if t > sb + 0.8 else 0
            k = pop(t, sb - 0.1, 0.4)
            with xf(c, 310, -60, s=k):
                box(c, -220, -60, 440, 120, "#8a8a8a" if pressed else "#d8262e", r=60, ow=6)
                T(c, "SUBSCRIBED" if pressed else "SUBSCRIBE", 0, 18, 50, "#ffffff", LUCKY)
            if t > sb + 0.4:
                hx = lerp(560, 360, smooth(at(t, sb + 0.2, 0.6)))
                with xf(c, hx, 20):
                    oval(c, 0, 0, 34, 34, "#f2c9a0")
            with xf(c, 310, 170, s=pop(t, wt("comments", 155.0), 0.4)):
                box(c, -230, -50, 460, 100, "#ffffff", r=18, ow=4)
                T(c, "Add a comment...", -200, 12, 32, "#8a8a8a", "interb", align="left")
            with xf(c, 310, 300, s=pop(t, wt("born", 157.3), 0.4)):
                T(c, "MOST LIKED = NEXT LIFE", 0, 0, 34, "#d8262e", LUCKY)


# ======================================================================= MONEY + SETUP
@shot(158.1, 167.4, "LEONIDA KEYS")
def s_clock(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "house_night" if t < 158.4 else "keys")
        tint_c(c, "#000000", 0.25)
        with xf(c, 620, 520, s=pop(t, 158.2, 0.4)):
            oval(c, 0, 0, 240, 240, "#f7f3ea", ow=10)
            for k in range(12):
                a = k * math.pi / 6
                line(c, math.sin(a) * 200, -math.cos(a) * 200, math.sin(a) * 225, -math.cos(a) * 225, OUT, 8)
            a = (t - 158) * 3
            line(c, 0, 0, math.sin(a) * 180, -math.cos(a) * 180, "#d8262e", 8)
            line(c, 0, 0, math.sin(a / 12) * 120, -math.cos(a / 12) * 120, OUT, 12)
            oval(c, 0, 0, 14, 14, OUT, ow=0)
        mon = wt("money", 160.6)
        k = pop(t, mon - 0.1, 0.4)
        if k > 0:
            with xf(c, 1340, 440, s=k):
                money_bag(c, 0, 0, 2.6)
        cs = wt("costs", 163.6)
        k = pop(t, cs - 0.1, 0.4)
        if k > 0:
            mug(c, 1340, 560, "tommy", "tommy_kid", "TOMMY", "sad", rot=4, s=k, t=t)
            with xf(c, 1520, 380, s=k, rot=-20):
                pth = poly([(-120, -50), (90, -50), (130, 0), (90, 50), (-120, 50)])
                shape(c, pth, "#ffd23f")
                T(c, "$$$$$", -10, 16, 44, "#141414", LUCKY)
    caption_serif(c, "getting a son back costs more than courage", 960, 1010, 44, a=fade(t, cs - 0.1))


@shot(167.4, 174.4, "OVERSEAS HIGHWAY")
def s_runs(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "bridge")
        for k in range(12):
            x = (k * 180 - t * 900) % (W + 180) - 90
            rect(c, x, 630, 90, 8, "#f2e6b8")
        car(c, 960, 640, 0.75, "#d8262e", t, moving=1.0, kind="conv", lights=1.0,
            people=[(-40, "jason", "jason", "neutral"), (60, "lucia", "lucia", "smirk")])
        for i in range(3):
            box(c, 1040 + i * 50 - 30, 470, 46, 40, "#b98a58", r=4, ow=3)
    for i, (lab, tm) in enumerate((("LATE NIGHT DRIVES", wt("late", 169.0)), ("HIDDEN CARGO", wt("hidden", 170.3)),
                                   ("RISKY DEALS", wt("risky", 171.3)))):
        tag(c, 360 + i * 600, 860, lab, 40, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1), rot=(-3 + i * 3))
    big_title(c, "A NATURAL.", 960, 220, 110, t, wt("natural", 172.9), "#ffd23f")


@shot(174.4, 185.0, "LEONIDA KEYS")
def s_mattia(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "keys")
        mt = wt("mattia", 175.6)
        x = lerp(2100, 1450, smooth(at(t, mt - 0.5, 1.4)))
        person(c, x, 990, "mattia", "mattia", "point" if t > mt + 1.2 else "walk", "smirk", t, s=1.3,
               walk=t if t < mt + 0.9 else 0)
        person(c, 520, 990, "jason", "jason", "cross" if t > wt("trap", 179.9) - 0.5 else "stand",
               "angry" if t > wt("trap", 179.9) - 0.5 else "neutral", t, s=1.3)
        person(c, 860, 990, "lucia", "lucia", "hips", "smirk", t, s=1.3)
    tag(c, x, 360, "MATTIA", 34, a=fade(t, mt))
    k = pop(t, wt("pays", 177.9) - 0.1, 0.4)
    if k > 0:
        with xf(c, 1450, 220, s=k, rot=6):
            box(c, -170, -90, 340, 180, "#f2e2c4", r=6)
            pth = poly([(-170, -90), (0, 10), (170, -90)], close=False)
            c.drawPath(pth, P(OUT, 5))
            T(c, "$$$$", 0, 70, 50, "#2e8b57", LUCKY)
            T(c, "WAY TOO WELL", 0, 150, 34, "#ffd23f", LUCKY, outline="#141414", ow=6)
    speech(c, 520, 280, ["SMELLS LIKE", "A TRAP."], 38, a=window(t, wt("trap", 179.9) - 0.3, 184.8),
           s=pop(t, wt("trap", 179.9) - 0.3), tail=(10, 90))


@shot(185.0, 191.6)
def s_say_yes(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.05, 1.18, cx=900, cy=520, t=t)
        draw_bg(c, "keys", blur=6)
        person(c, 900, 1060, "lucia", "lucia", "fist" if t > wt("yes", 189.0) else "cross", "determined", t, s=1.7)
    for i, (lab, tm) in enumerate((("POOR", wt("poor", 185.9)), ("LOCKED UP", wt("locked", 186.8)),
                                   ("DONE WAITING", wt("done", 188.0)))):
        tag(c, 360, 300 + i * 120, lab, 40, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1), rot=-4)
    k = fade(t, wt("yes", 189.0) - 0.05)
    speech(c, 1330, 300, ["I'M IN."], 64, a=k, s=pop(t, wt("yes", 189.0) - 0.05), tail=(-60, 90))
    # first domino
    dm = wt("domino", 190.7)
    if t > wt("remember", 189.9) - 0.2:
        for i in range(6):
            fall = smooth(at(t, dm + i * 0.12, 0.3))
            with xf(c, 1260 + i * 95, 1000, rot=fall * 70, s=0.8):
                box(c, -24, -150, 48, 150, "#141414", r=6, ow=4, oc="#f2f2f2")
                oval(c, 0, -110, 7, 7, "#f2f2f2", ow=0)
                oval(c, 0, -40, 7, 7, "#f2f2f2", ow=0)


@shot(191.6, 197.0, "IT'S A SETUP")
def s_setup(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, shake=0.2, t=t)
        draw_bg(c, "keys_night")
        for k in range(4):
            glow(c, 200 + k * 500, 600, 300, "#ff2a3a" if (int(t * 6) + k) % 2 else "#2a6aff", 0.35)
        car(c, 1550, 1010, 0.7, "#16161c", t, kind="cop", lights=1)
        car(c, 380, 1010, 0.7, "#16161c", t, kind="cop", lights=1, flip=True)
        person(c, 820, 990, "lucia", "lucia", "cuffed", "angry", t, s=1.2)
        person(c, 1080, 990, "jason", "jason", "cuffed", "cry" if t > wt("wounded", 195.6) else "angry", t, s=1.2)
    k = fade(t, 191.7)
    stamp(c, 960, 180, "IT'S A SETUP", 90, a=k, s=lerp(1.6, 1, ease_out(k)), rot=-5)
    tag(c, 1080, 520, "BADLY WOUNDED", 32, a=fade(t, wt("wounded", 195.6)), bg="#ff8a8a")


@shot(197.0, 203.1)
def s_burn(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, shake=0.12, t=t)
        draw_bg(c, "house_night")
        bn = wt("burn", 200.2)
        k = smooth(at(t, bn - 0.3, 1.5))
        if k > 0:
            draw_fire(c, 960, 640, 560, 420 * k, t)
            tint_c(c, "#ff6a1a", 0.15 * k)
        if t < bn:
            for i, x in enumerate((300, 1620)):
                person(c, x, 1010, "masked", "masked", "point", "angry", t, s=1.1, flip=(i == 1))
    tag(c, 960, 160, "MASKED MEN + DIRTY COPS", 40, a=window(t, 197.1, bn + 0.3))
    caption_serif(c, "everything you just started building... gone in one night", 960, 1010, 42,
                  a=fade(t, wt("everything", 203.1) - 1.0))


def draw_fire(c, x, y, w, h, t):
    import random as _r
    for layer, col in enumerate(("#ff4a1a", "#ff8a1a", "#ffd23f")):
        for i in range(14):
            rnd = _r.Random(i * 7 + layer)
            fx = x - w / 2 + (i + 0.5) * w / 14 + math.sin(t * 5 + i) * 10
            fh = h * (1 - layer * 0.3) * (0.6 + 0.4 * abs(math.sin(t * (3 + rnd.random() * 3) + i)))
            pth = skia.Path()
            pth.moveTo(fx - w / 18, y)
            pth.quadTo(fx - w / 30, y - fh * 0.6, fx + math.sin(t * 6 + i) * 20, y - fh)
            pth.quadTo(fx + w / 30, y - fh * 0.6, fx + w / 18, y)
            pth.close()
            c.drawPath(pth, P(col, a=0.9))
    glow(c, x, y - h * 0.4, w * 0.8, "#ff8a1a", 0.35)


@shot(203.1, 212.4)
def s_run_map(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.05, 1.18, cx=900, cy=480, t=t)
        draw_bg(c, "map")
        pts = [(1050, 900), (900, 600), (700, 420), (420, 340)]
        red_string(c, [(p[0], p[1]) for p in pts], ease_out(at(t, 204.5, 4.0)), "#e8282e", 9)
        marker_text(c, "KELLY COUNTY", 600, 300, 50, a=fade(t, wt("kelly", 208.0)), rot=-6)
    k = pop(t, 203.3, 0.4)
    if k > 0:
        with xf(c, 1450, 760, s=k * 0.9):
            person(c, 0, 0, "lucia", "lucia", "hug", "determined", t, s=1.0)
            person(c, 130, 0, "jason", "jason", "cry", "cry", t, s=1.0)
    tag(c, 1500, 330, "BLEEDING + WANTED", 36, a=fade(t, wt("bleeding", 206.0)), bg="#ff8a8a")


@shot(212.4, 218.4, "PORT GELLHORN")
def s_gellhorn(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "motel")
        person(c, 560, 1010, "lucia", "lucia", "hug", "worried", t, s=1.2)
        person(c, 720, 1010, "jason", "jason", "cry", "sad", t, s=1.2)
    checklist(c, 1100, 520, ["NO MONEY", "NO FRIENDS", "NO PLAN"], t,
              [wt("money", 213.9), wt("friends", 214.6), wt("plan", 215.4)], size=54, cross=True)
    big_title(c, "PORT GELLHORN", 960, 160, 90, t, 212.5, "#ffd23f")


@shot(218.4, 229.8)
def s_holds(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "motel_night")
        person(c, 960, 1010, "lucia", "lucia", "hips", "determined", t, s=1.45)
    items = [("SUPPLIES", wt("supplies", 222.0), "#9fd3ef"), ("PAINKILLERS", wt("painkillers", 223.4), "#ff8a8a"),
             ("LOCAL CONTACTS", wt("local", 224.4), "#ffd23f")]
    for i, (lab, tm, col) in enumerate(items):
        tag(c, 380 + (i % 2) * 1160, 320 + i * 170, lab, 42, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1), bg=col)
    k = fade(t, wt("kidnapping", 228.5) - 0.1)
    if k > 0:
        stamp(c, 960, 160, "KIDNAPPING", 80, a=k, s=lerp(1.5, 1, ease_out(k)), rot=-6)
    caption_serif(c, "deals you'd never have made before", 960, 1010, 44, a=window(t, wt("deals", 226.0) - 0.3, 228.4))


@shot(229.8, 240.2)
def s_worth_it(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.08, t=t)
        draw_bg(c, "motel_night")
        tint_c(c, "#000000", 0.35)
        # bed with Jason
        box(c, 1080, 760, 640, 120, "#e8e2d4", r=20)
        box(c, 1080, 860, 640, 40, "#7a5a3a", ow=4)
        with xf(c, 1180, 740):
            head(c, "jason", "jason", 70, "sad", t)
        box(c, 540, 760, 200, 30, "#6a4a32", r=6)
        box(c, 550, 790, 20, 220, "#4a3222", ow=4)
        box(c, 710, 790, 20, 220, "#4a3222", ow=4)
        box(c, 700, 560, 30, 220, "#6a4a32", r=6)
        person(c, 640, 900, "lucia", "lucia", "sit", "worried", t, s=1.2, look=(3, 0))
    k = fade(t, wt("dead", 231.6) - 0.1)
    if k > 0 and t < 233.5:
        stamp(c, 960, 200, "SOMEONE DEAD", 70, a=k, rot=-4, color="#ff4a4a")
    tag(c, 1400, 600, "JASON LIVES", 36, a=fade(t, wt("lives", 233.0)), bg="#7dff8a")
    k = pop(t, wt("worth", 235.0), 0.4)
    if k > 0:
        T(c, "WORTH IT?", 960, 230, 110 * k, "#ffffff", LUCKY, outline="#141414", ow=12)
    k = pop(t, wt("was", 236.6), 0.4)
    if k > 0:
        T(c, "?", 1450, 260, 160 * k, "#ffd23f", LUCKY, outline="#141414", ow=12)


@shot(240.2, 246.2, "ROBBERY SPREE")
def s_rob(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.08, cx=880, cy=520, t=t)
        draw_bg(c, "map")
        spots = [(700, 420), (560, 360), (880, 560), (1000, 700), (1120, 820)]
        for i, (x, y) in enumerate(spots):
            k = pop(t, wt("small", 240.6) + i * 0.7, 0.3)
            if k > 0:
                s = 0.6 + i * 0.15
                with xf(c, x, y, s=k * s):
                    box(c, -50, -50, 100, 100, "#ffffff", r=10, ow=5)
                    pth = skia.Path()
                    pth.moveTo(-28, 0)
                    pth.lineTo(-8, 22)
                    pth.lineTo(30, -26)
                    c.drawPath(pth, P("#2e8b57", 12))
    big_title(c, "YOU ROB.", 960, 200, 110, t, wt("rob", 240.6), "#ffffff")
    k = pop(t, wt("scarily", 244.5), 0.4)
    if k > 0:
        tag(c, 1450, 900, "SCARILY GOOD", 50, s=k, rot=-5, bg="#ffd23f")


@shot(246.2, 252.9)
def s_huge_score(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "dark")
        # small piggy vs big price
        with xf(c, 520, 620, s=pop(t, 246.3, 0.4)):
            oval(c, 0, 0, 160, 120, "#f4a7c0")
            oval(c, 140, -10, 40, 34, "#f4a7c0")
            for x in (-90, 80):
                box(c, x - 20, 90, 40, 60, "#f4a7c0", r=10, ow=4)
            box(c, -30, -126, 60, 14, OUT, r=6, ow=0)
            T(c, "$", 0, 30, 90, "#d86a90", LUCKY)
            T(c, "SMALL ROBBERIES", 0, 250, 40, "#f2f2f2", LUCKY)
        k = pop(t, wt("tommy", 250.5) - 0.8, 0.4)
        if k > 0:
            mug(c, 1360, 520, "tommy", "tommy_kid", "TOMMY", "sad", rot=5, s=k * 1.1, t=t)
    big_title(c, "ONE HUGE SCORE", 960, 160, 100, t, wt("huge", 251.6), "#ffd23f")


@shot(252.9, 258.4, "VICE CITY")
def s_vice_reveal(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.12, 1.0, cy=480, t=t)
        draw_bg(c, "vice_night")
    vc = wt("vice", 257.0)
    k = fade(t, vc - 0.4, 0.5)
    if k > 0:
        from sets import neon
        neon(c, "Vice City", 960, 460, 230, "#ff5fa2", SCRIPT, a=k, flick=0.85 + 0.15 * math.sin(t * 30))
    caption_serif(c, "the biggest city in Leonida is waiting", 960, 1010, 46, a=window(t, 253.0, 257.6))


@shot(258.4, 265.0)
def s_hunters(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, shake=0.1, t=t)
        draw_bg(c, "motel_night")
        tint_c(c, "#000000", 0.3)
        for i, x in enumerate((1500, 1700)):
            person(c, x, 1010, "masked", "masked", "point", "angry", t, s=1.2, flip=True, a=0.95)
        x = lerp(760, 300, smooth(at(t, wt("drag", 259.4), 3.5)))
        person(c, x, 1010, "lucia", "lucia", "walk", "scared", t, s=1.2, walk=t)
        person(c, x + 150, 1010, "jason", "jason", "cry", "cry", t, s=1.2, walk=t * 0.6)
    tag(c, 1600, 330, "HUNTERS", 40, a=fade(t, wt("hunters", 258.4)), bg="#ff8a8a")
    for i, (lab, tm) in enumerate((("WOUNDED", wt("wounded", 262.9)), ("HUNTED", wt("hunted", 263.6)))):
        tag(c, 560 + i * 400, 220, lab, 44, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1), rot=-4 + i * 6)


@shot(265.0, 270.4)
def s_bag(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.12, t=t)
        draw_bg(c, "dark")
        fill_shader(c, skia.Rect(560, 0, 1360, H), linear(960, 0, 960, H, [("#fff2c0", 0.25), ("#fff2c0", 0.05)]))
        with xf(c, 960, 640, s=pop(t, wt("bag", 267.6) - 0.2, 0.5) * 1.4):
            box(c, -220, -120, 440, 240, "#2a2a30", r=40)
            pth = skia.Path()
            pth.moveTo(-100, -120)
            pth.quadTo(0, -230, 100, -120)
            c.drawPath(pth, P(OUT, 22))
            c.drawPath(pth, P("#3a3a42", 14))
            line(c, -200, -40, 200, -40, "#55555f", 5)
            oval(c, 0, -40, 14, 10, "#e8c25a", ow=3)
    marker_circle(c, 960, 620, 420, 260, at(t, wt("bag", 267.6), 0.8))
    marker_text(c, "THE BAG", 1380, 330, 80, a=at(t, wt("bag", 267.6) + 0.3, 0.6), rot=-6)
    k = pop(t, wt("don't", 268.5), 0.4)
    if k > 0:
        T(c, "?", 960, 300, 200 * k, "#ffd23f", LUCKY, outline="#141414", ow=14)
    caption_serif(c, "the one thing powerful people want back", 960, 1010, 44, a=window(t, 265.1, 267.9))


@shot(270.4, 276.6)
def s_skyline_drive(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "vice_night")
        rect(c, 0, 900, W, 180, "#1c1a2a")
        for k in range(10):
            x = (k * 240 - t * 900) % (W + 240) - 120
            rect(c, x, 980, 120, 10, "#f2e6b8")
        car(c, 960, 1040, 0.7, "#d8262e", t, moving=1.0, kind="conv", lights=1,
            people=[(-40, "jason", "jason", "sad"), (60, "lucia", "lucia", "determined")])
    k = fade(t, wt("close", 273.5) - 0.2)
    if k > 0:
        stamp(c, 960, 220, "NOT EVEN CLOSE", 80, a=k, s=lerp(1.5, 1, ease_out(k)), rot=-5)


@shot(276.6, 283.3, "PART 2")
def s_part2(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "dark")
    if t < wt("in", 279.5) - 0.2:
        caption_serif(c, "the people who built your trap are still out there", 960, 540, 50, a=fade(t, 276.7))
        return
    p = wt("part", 280.0)
    k = pop(t, p - 0.2, 0.5)
    T(c, "PART 2", 960, 330, 70 * k, "#f3e3c3", SERIF)
    from sets import neon
    neon(c, "Vice City", 960, 560, 200, "#ff5fa2", SCRIPT, a=fade(t, p))
    for i, (lab, tm) in enumerate((("A BANK", wt("bank", 281.2)), ("A BETRAYAL", wt("betrayal", 281.8)),
                                   ("A BRIDGE", wt("bridge", 282.7)))):
        tag(c, 560 + i * 400, 800, lab, 46, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1))
