"""Part 2 of the timeline: Vice City -> Giorgio -> the bridge -> the endings -> outro (4:43-12:41)."""
from common import *  # noqa: F401,F403
from common import shot, wt
import math
import skia
from sets import neon
from scenes_a import tint_c, draw_fire


# ======================================================================= VICE CITY
@shot(283.3, 290.5, "VICE CITY")
def s_vice_slap(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, shake=0.25 * window(t, 283.4, 284.0, 0.1), t=t)
        draw_bg(c, "club")
        beat = abs(math.sin(t * math.pi * 2.0))
        tint_c(c, "#ff5fa2", 0.06 * beat)
        for i, x in enumerate((420, 700, 1220, 1500)):
            person(c, x, 1010 - beat * 10, ["woman", "man", "friend", "vinny"][i], None, "raise", "laugh", t + i, s=1.0)
        for i in range(8):
            x = (i * 260 + t * 120) % W
            note(c, x, 420 + math.sin(t * 3 + i) * 40, 1.0, ["#ffd36b", "#5fe3ff", "#ff5fa2"][i % 3], 0.9)
    k = pop(t, wt("slap", 283.6), 0.25)
    if k > 0 and t < 285.5:
        T(c, "SLAP!", 960, 560, 150 * k, "#ffd23f", BANG, outline="#141414", ow=14, rot=-8)
    for i, (lab, tm) in enumerate((("NEON LIGHTS", wt("neon", 284.2)), ("LOUD MUSIC", wt("loud", 285.2)),
                                   ("HOT NIGHTS", wt("hot", 286.3)))):
        tag(c, 400 + i * 560, 900, lab, 40, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1), rot=-3 + i * 3)
    k = fade(t, wt("money", 288.8) - 0.2)
    if k > 0:
        for i in range(14):
            y = ((t - 288.5) * 400 + i * 130) % 1200 - 100
            cash(c, (i * 173) % W, y, 1.0, rot=(t * 90 + i * 40))


@shot(290.5, 296.0)
def s_not_yours(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.08, t=t)
        draw_bg(c, "vice_night")
        person(c, 780, 1010, "lucia", "lucia", "shrug", "sad", t, s=1.4)
        person(c, 1140, 1010, "jason", "jason", "shrug", "sad", t, s=1.4)
    big_title(c, "$0", 960, 220, 160, t, wt("dollar", 291.5), "#ff4a4a")
    caption_serif(c, "and not a dollar of it is yours", 960, 1010, 46, a=fade(t, 290.6))
    k = fade(t, wt("bottom", 295.6) - 0.1)
    if k > 0:
        tag(c, 960, 400, "START AT THE BOTTOM", 44, a=k, s=pop(t, wt("bottom", 295.6) - 0.1))


@shot(296.0, 301.0, "VICE CITY")
def s_boobie_raul(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "cork")
        mug(c, 600, 520, "boobie", label="BOOBIE", expr="smirk", rot=-5, s=pop(t, wt("nightclub", 298.0) - 0.2), t=t,
            bgcol="#e8b0d0")
        mug(c, 1320, 520, "raul", label="RAUL", expr="smirk", rot=5, s=pop(t, wt("raul", 300.0) - 0.2), t=t,
            bgcol="#d0c0a0")
    tag(c, 600, 900, "NIGHTCLUB OWNER", 34, a=fade(t, wt("nightclub", 298.0)))
    tag(c, 1320, 900, "BANK ROBBER", 34, a=fade(t, wt("robber", 299.6)))


@shot(301.0, 308.9, "NATIONAL BANK")
def s_bank(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "bank")
        for i, (who, lk, x) in enumerate((("raul", "raul", 620), ("lucia", "lucia", 860), ("jason", "jason", 1100))):
            person(c, x, 1010, who, lk, "point" if (i == 0 and t > wt("plan", 304.5)) else "stand",
                   "smirk" if i == 0 else "determined", t, s=1.25)
    tag(c, 620, 450, "RAUL", 32, a=fade(t, 301.2))
    k = pop(t, wt("plan", 304.5) - 0.1, 0.4)
    if k > 0:
        with xf(c, 1520, 330, s=k, rot=5):
            box(c, -200, -150, 400, 300, "#2a4a8a", r=6)
            for g in range(6):
                line(c, -200 + g * 66, -150, -200 + g * 66, 150, "#5a7aba", 2)
                line(c, -200, -150 + g * 50, 200, -150 + g * 50, "#5a7aba", 2)
            box(c, -120, -80, 140, 120, "#ffffff", a=0.0, ow=4, oc="#ffffff")
            arrow(c, -150, 100, 30, -40, "#ffffff", 6)
            T(c, "THE PLAN", 0, 130, 34, "#ffffff", LUCKY)
    tag(c, 960, 150, "PULL OFF THE HEIST", 40, a=fade(t, wt("in", 307.0)))


@shot(308.9, 314.3)
def s_vault(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.08, t=t)
        draw_bg(c, "vault")
        person(c, 700, 1000, "lucia", "lucia", "raise", "laugh", t, s=1.3)
        person(c, 1000, 1000, "jason", "jason", "raise", "happy", t, s=1.3)
        for i in range(18):
            y = ((t - 309) * 300 + i * 90) % 1200 - 100
            cash(c, (i * 211) % W, y, 1.1, rot=(t * 80 + i * 30))
    big_title(c, "THEY PULL IT OFF", 960, 180, 100, t, wt("pulls", 310.8) - 0.2, "#7dff8a")


@shot(314.3, 324.6)
def s_almost(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "penthouse")
        person(c, 760, 1000, "lucia", "lucia", "hug", "happy", t, s=1.3)
        person(c, 1020, 1000, "jason", "jason", "hug", "happy", t, s=1.3)
    for i, (lab, tm) in enumerate((("RICH", wt("rich", 314.3)), ("FREE", wt("free", 315.3)))):
        tag(c, 560 + i * 800, 300, lab, 56, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1), bg="#7dff8a")
    md = wt("mother", 317.9)
    if t > md - 0.3:

        def inner(cc, iw, ih):
            grad_rect(cc, 0, 0, iw, ih, ["#7cc7ec", "#fff3d8"])
            dream_house(cc, iw / 2, ih - 20, 0.8, t)

        polaroid(c, 1540, 560, 420, 460, inner, "THE GOOD LIFE", rot=6, s=pop(t, md - 0.3, 0.4))
    k = fade(t, wt("almost", 321.0) - 0.05)
    if k > 0:
        stamp(c, 960, 540, "ALMOST.", 140, a=k, s=lerp(1.6, 1, ease_out(k)), rot=-8)


@shot(324.6, 330.9, "VICE CITY")
def s_abe(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "lawyer")
        person(c, 960, 860, "abe", "abe", "point", "smirk", t, s=1.1)
        box(c, 360, 760, 1200, 70, "#6a4428", r=6)
    tag(c, 960, 380, "ABE GONZALEZ · LAWYER", 36, a=fade(t, wt("lawyer", 325.0)))
    for i, (nm, x, rot) in enumerate((("NEW NAME #1", 520, -8), ("NEW NAME #2", 1400, 8))):
        k = pop(t, wt("fake", 328.0) + i * 0.4, 0.4)
        if k > 0:
            with xf(c, x, 640, s=k, rot=rot):
                box(c, -190, -120, 380, 240, "#e8f2f8", r=14)
                box(c, -190, -120, 380, 50, "#2f7ad8", r=14)
                T(c, "LEONIDA ID", 0, -84, 26, "#ffffff", "inter")
                box(c, -170, -50, 120, 150, "#c9d6e2", r=6, ow=3)
                with xf(c, -110, 40):
                    head(c, "lucia" if i == 0 else "jason", "lucia" if i == 0 else "jason", 48, "neutral", t)
                T(c, nm, 70, 20, 26, "#141414", "interb")
                rect(c, -20, 50, 180, 8, "#9aa8b8")
                rect(c, -20, 75, 140, 8, "#9aa8b8")
    k = pop(t, wt("cops", 322.5), 0.4)


@shot(330.9, 337.0)
def s_valentina_airport(c, t, lt, d):
    if t < wt("jason", 331.9) - 0.1:
        with xf(c):
            cam(c, lt, 1.5, 1.0, 1.05, t=t)
            draw_bg(c, "penthouse")
            person(c, 960, 1000, "valentina", "valentina", "hips", "smirk", t, s=1.4)
        tag(c, 960, 380, "VALENTINA", 40, a=fade(t, 331.0))
        return
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "airport")
        person(c, 600, 1010, "jason", "jason", "phone", "neutral", t, s=1.3, look=(4, 0))
    tag(c, 600, 400, "JASON @ THE AIRPORT", 36, a=fade(t, 332.0))
    k = fade(t, wt("collecting", 334.8) - 0.2)
    if k > 0:
        for i in range(3):
            with xf(c, 900 + i * 160, 360 - i * 40, alpha=k, rot=-6 + i * 6):
                box(c, -60, -80, 120, 160, "#f7f3ea", r=4)
                for j in range(5):
                    rect(c, -40, -55 + j * 25, 80, 6, "#9a9a9a")
        caption_serif(c, "quietly collecting information", 960, 1010, 46, a=k)


@shot(337.0, 344.3, "IRON GYM")
def s_gym_cordell(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "gym")
        cd = wt("cordell", 342.0)
        person(c, 1300, 1010, "cordell", "cordell", "cross", "smirk", t, s=1.4)
        ent = smooth(at(t, 337.3, 1.6))
        person(c, lerp(-200, 640, ent), 1010, "lucia", "lucia_box", "walk" if ent < 1 else "hips", "smirk", t,
               s=1.3, walk=t if ent < 1 else 0)
    tag(c, 1300, 400, "CORDELL GRANT", 38, a=fade(t, cd))
    k = pop(t, wt("smile", 343.7), 0.3)
    if k > 0:
        tag(c, 640, 380, "SMILE :)", 36, s=k)


@shot(344.3, 350.9)
def s_listening(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.1, cx=760, t=t)
        draw_bg(c, "gym")
        lift = abs(math.sin(t * 2.2)) if t > wt("lift", 344.6) else 0
        person(c, 760, 1010, "lucia", "lucia_box", "raise" if lift > 0.5 else "hold", "neutral", t, s=1.5,
               look=(5, 0))
        if t > wt("lift", 344.6):
            hy = lerp(-330, -560, lift) * 1.5
            line(c, 760 - 260, 1010 + hy * 0.95, 760 + 260, 1010 + hy * 0.95, "#5a5f66", 18)
            for sx in (-1, 1):
                oval(c, 760 + sx * 250, 1010 + hy * 0.95, 34, 80, "#202024")
        person(c, 1400, 1010, "cordell", "cordell", "point", "smirk", t, s=1.3, talk=0.8)
        person(c, 1650, 1010, "man", "man", "cross", "neutral", t, s=1.2, talk=0.4)
    for i, (lab, tm) in enumerate((("YOU SMILE", wt("smile", 343.7)), ("YOU LIFT", wt("lift", 344.6)),
                                   ("YOU LISTEN", wt("listen", 345.4)))):
        tag(c, 360, 260 + i * 110, lab, 40, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1), rot=-3)
    k = pop(t, wt("always", 346.6), 0.4)
    if k > 0:
        with xf(c, 1080, 300, s=k):
            for r_ in (60, 100, 140):
                pth = skia.Path()
                pth.addArc(skia.Rect(-r_, -r_, r_, r_), -40, 80)
                c.drawPath(pth, P("#ffd23f", 8, a=0.5 + 0.5 * math.sin(t * 6 - r_ / 30)))
            T(c, "ALWAYS LISTENING", 0, 200, 40, "#ffd23f", LUCKY, outline="#141414", ow=8)


@shot(350.9, 358.4, "AIRPORT HEIST")
def s_double_cross(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "cork")
        mug(c, 560, 500, "raul", label="RAUL", expr="smirk", rot=-5, t=t, bgcol="#d0c0a0")
        mug(c, 1360, 500, "cordell", label="CORDELL", expr="angry", rot=5, t=t, bgcol="#c0d8c0")
        arrow(c, 760, 450, 1150, 450, "#d8262e", 12, prog=ease_out(at(t, wt("double", 350.6), 0.8)))
    k = fade(t, wt("double", 350.6))
    if k > 0:
        stamp(c, 960, 330, "DOUBLE CROSS", 60, a=k, s=lerp(1.5, 1, ease_out(k)), rot=-6)
    for i, (lab, tm) in enumerate((("BOLD", wt("bold", 352.0)), ("DANGEROUS", wt("dangerous", 352.6)),
                                   ("NOT SMART ENOUGH", wt("smart", 354.6)))):
        tag(c, 560, 820 + i * 70 - 60, lab, 32, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1), bg="#ffd23f" if i < 2 else "#ff8a8a")


@shot(358.4, 365.0)
def s_mendes(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "cork")
        mug(c, 440, 500, "valentina", label="VALENTINA", expr="smirk", rot=-5, t=t, bgcol="#e0b8c0")
        mug(c, 960, 500, "raul", label="RAUL", expr="scared", rot=2, t=t, bgcol="#d0c0a0",
            xmark=at(t, wt("blood", 363.0), 0.6))
        mug(c, 1480, 500, "mendes", label="MENDES", expr="smirk", rot=6, t=t, bgcol="#b8c0d0",
            s=pop(t, wt("mendes", 360.4) - 0.2))
        red_string(c, [(440, 320), (960, 320), (1480, 320)], ease_out(at(t, wt("sells", 358.6), 1.5)))
    tag(c, 1480, 860, "DIRTY COP", 34, a=fade(t, wt("dirty", 359.8)), bg="#ff8a8a")
    k = pop(t, wt("sells", 358.6), 0.4)
    if k > 0:
        with xf(c, 700, 230, s=k, rot=-10):
            pth = poly([(-110, -40), (80, -40), (110, 0), (80, 40), (-110, 40)])
            shape(c, pth, "#ffd23f")
            T(c, "SOLD", -10, 14, 40, "#141414", LUCKY)


@shot(365.0, 372.3)
def s_loyalty(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.08, t=t)
        draw_bg(c, "vice_night", blur=5)
        tint_c(c, "#000000", 0.35)
    caption_serif(c, "one more friend gone. one more lesson.", 960, 300, 46, a=window(t, 365.1, 367.2))
    k = fade(t, wt("loyalty", 368.3) - 0.1)
    if k > 0:
        T(c, "LOYALTY LASTS EXACTLY", 960, 470, 70, "#ffffff", LUCKY, a=k, outline="#141414", ow=10)
        T(c, "UNTIL THE PRICE IS RIGHT", 960, 560, 70, "#ffd23f", LUCKY, a=k, outline="#141414", ow=10)
    k = pop(t, wt("price", 371.2) - 0.1, 0.4)
    if k > 0 and t > 370.8:
        mug(c, 960, 820, "lucia", "lucia", "", "worried", rot=-3, t=t, s=0.8 * k, w=280, h=300)
        with xf(c, 1160, 720, s=k, rot=-18):
            pth = poly([(-90, -36), (70, -36), (100, 0), (70, 36), (-90, 36)])
            shape(c, pth, "#ffd23f")
            T(c, "$$$", -10, 14, 36, "#141414", LUCKY)


@shot(372.3, 384.0)
def s_offer(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "lawyer")
        person(c, 1320, 860, "abe", "abe", "point", "smirk", t, s=1.1, talk=0.7 * window(t, 372.4, 378.0))
        person(c, 560, 860, "lucia", "lucia", "cross", "neutral", t, s=1.1)
        box(c, 360, 760, 1200, 70, "#6a4428", r=6)
    k = pop(t, wt("offer", 373.0), 0.4)
    if k > 0:
        with xf(c, 960, 520, s=k, rot=-3):
            box(c, -230, -300, 460, 600, "#fbf8f0", r=4)
            T(c, "PLEA OFFER", 0, -230, 44, "#141414", LUCKY)
            T(c, "GIVE UP JASON", 0, -150, 40, "#d8262e", MARKER)
            for j in range(6):
                rect(c, -180, -90 + j * 40, 360 if j % 3 else 280, 8, "#c9c2b0")
            line(c, -180, 220, 120, 220, "#141414", 3)
            T(c, "sign here", -180, 250, 22, "#8a8a8a", SERIF, align="left")
    for i, (lab, tm) in enumerate((("CLEAN PATH", wt("clean", 378.1)), ("YOUR SON", wt("son", 379.5)))):
        tag(c, 1500, 220 + i * 100, lab, 36, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1), bg="#7dff8a")
    caption_serif(c, "the easiest way out you've ever been given", 960, 1010, 44, a=fade(t, wt("easiest", 381.0)))


@shot(384.0, 390.8)
def s_no(c, t, lt, d):
    no = wt("no", 384.3)
    with xf(c):
        cam(c, lt, d, 1.12, 1.0, shake=0.25 * window(t, no, no + 0.4, 0.05), t=t)
        draw_bg(c, "lawyer", blur=5)
        person(c, 960, 1100, "lucia", "lucia", "cross", "angry", t, s=1.8)
        k = at(t, no, 0.5)
        for sx in (-1, 1):
            with xf(c, 960 + sx * (100 + k * 600), 420 + k * 300, rot=sx * k * 40, alpha=1 - k * 0.6):
                box(c, -110, -150, 220, 300, "#fbf8f0", r=4)
                T(c, "GIVE UP" if sx < 0 else "JASON", 0, 0, 34, "#d8262e", MARKER)
    big_title(c, "NO.", 960, 260, 220, t, no, "#ff4a4a")
    caption_serif(c, "No speech. No drama. Just no.", 960, 1010, 48, a=fade(t, 386.0))


@shot(390.8, 402.4)
def s_together(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.08, t=t)
        draw_bg(c, "living_night")
        sep = smooth(at(t, wt("stay", 393.7), 2.0))
        person(c, 600 - sep * 80, 1000, "lucia", "lucia", "sit", "sad", t, s=1.2, look=(3, 0))
        person(c, 1000 + sep * 80, 1000, "jason", "jason", "sit", "sad", t, s=1.2, look=(-3, 0))
    caption_serif(c, "Should you even stay together?", 960, 260, 56, a=fade(t, wt("should", 393.3)))
    k = fade(t, wt("loving", 395.6))
    if k > 0:
        heart(c, 800, 500, 1.6, a=k)
        if t > 398:
            line(c, 770, 450, 830, 560, "#141414", 7, k)
    caption_serif(c, "loving him might be exactly why you never get free", 960, 1010, 42, a=fade(t, 395.7))


@shot(402.4, 409.4)
def s_giorgio(c, t, lt, d):
    gg = wt("giorgio", 406.0)
    if t < gg - 0.4:
        with xf(c):
            cam(c, lt, 3.5, 1.0, 1.05, t=t)
            draw_bg(c, "dark")

            def scr(cc):
                grad_rect(cc, -150, -300, 300, 600, ["#1c2a4a", "#0e1628"])
                T(cc, "MATTIA", 0, -220, 32, "#ffffff", "inter")
                box(cc, -130, -150, 220, 110, "#2f7ad8", r=24, ow=0)
                T(cc, "Meet me.", -20, -90, 30, "#ffffff", "interb")
                box(cc, -130, -20, 240, 110, "#2f7ad8", r=24, ow=0)
                T(cc, "Bring the bag.", -10, 40, 28, "#ffffff", "interb")

            phone_screen(c, 960, 540, 1.2 * pop(t, 402.5, 0.4), scr, rot=-4)
        return
    with xf(c):
        cam(c, t - gg, d - (gg - 402.4), 1.0, 1.08, t=t)
        draw_bg(c, "penthouse")
        person(c, 960, 1010, "giorgio", "giorgio", "hips", "smirk", t, s=1.45)
    tag(c, 960, 360, "GIORGIO GALLO", 44, a=fade(t, gg))
    for i, (lab, tm) in enumerate((("CALM", wt("calm", 407.4)), ("POLITE", wt("polite", 407.8)),
                                   ("TERRIFYING", wt("terrifying", 408.2)))):
        tag(c, 360 + i * 600, 900, lab, 40, a=fade(t, tm - 0.1), s=pop(t, tm - 0.1),
            bg="#ffffff" if i < 2 else "#ff8a8a")


@shot(409.4, 415.3)
def s_drive_senator(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "dark")
        with xf(c, 620, 560, s=pop(t, 409.5, 0.4) * 1.4):
            box(c, -160, -100, 320, 200, "#2a2a30", r=20)
            box(c, -120, -60, 240, 120, "#3a3a44", r=10)
            oval(c, 0, 0, 40, 40, "#8a8a9a")
            box(c, 80, 30, 40, 18, "#7dff8a", r=4, ow=2)
            T(c, "HARD DRIVE", 0, 160, 32, "#ffffff", LUCKY)
        mug(c, 1360, 520, "camila", label="SEN. CAMILA FUENTES", expr="worried", rot=5, t=t, bgcol="#c8d0e8",
            s=pop(t, wt("senator", 413.0) - 0.2), w=360, h=420)
        arrow(c, 860, 540, 1150, 540, "#d8262e", 10, prog=ease_out(at(t, wt("blackmail", 412.4), 0.8)))
    k = fade(t, wt("blackmail", 412.4))
    if k > 0:
        stamp(c, 960, 200, "BLACKMAIL", 80, a=k, s=lerp(1.5, 1, ease_out(k)), rot=-6)


@shot(415.3, 421.4)
def s_hires(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "penthouse")
        person(c, 1300, 1010, "giorgio", "giorgio", "point", "smirk", t, s=1.3, talk=0.6 * window(t, 415.4, 419.0))
        person(c, 600, 1010, "lucia", "lucia", "stand", "shock", t, s=1.3)
        person(c, 840, 1010, "jason", "jason", "stand", "shock", t, s=1.3)
    caption_serif(c, "He doesn't punish you for taking it.", 960, 260, 50, a=window(t, 415.4, 417.6))
    big_title(c, "HE HIRES YOU.", 960, 260, 110, t, wt("hires", 418.3) - 0.1, "#ffd23f")


@shot(421.4, 427.4, "JOBS FOR GIORGIO")
def s_jobs(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.04, t=t)
        draw_bg(c, "cork")
    icons = [("SMUGGLING", wt("cocaine", 419.6), "boat"), ("WAR VS ALBANIAN MOB", wt("war", 420.8), "war"),
             ("STEAL A HELICOPTER", wt("helicopter", 423.3), "heli"), ("KIDNAP A SNIFFER DOG", wt("sniffer", 424.4), "dog"),
             ("BLOW UP A SHIPMENT", wt("blow", 425.4), "boom")]
    for i, (lab, tm, kind) in enumerate(icons):
        k = pop(t, max(tm - 0.2, 421.4), 0.4)
        if k <= 0:
            continue
        x = 360 + (i % 3) * 600
        y = 330 if i < 3 else 760
        if i >= 3:
            x += 300
        with xf(c, x, y, s=k, rot=(-4 + i * 3)):
            box(c, -230, -170, 460, 340, "#f7f3ea", r=6)
            draw_icon(c, kind, t)
            T(c, lab, 0, 140, 30, "#141414", LUCKY)
            oval(c, 0, -165, 14, 14, "#d8262e", ow=3)


def draw_icon(c, kind, t):
    if kind == "boat":
        rect(c, -210, 40, 420, 60, "#2fb3b8")
        pth = poly([(-150, 0), (150, 0), (110, 50), (-120, 50)])
        shape(c, pth, "#f2f2f2")
        box(c, -40, -60, 100, 60, "#e8e8e8", r=6)
        for k in range(3):
            box(c, 70 + k * 30 - 60, -30, 28, 28, "#b98a58", r=3, ow=3)
    elif kind == "war":
        for sx in (-1, 1):
            oval(c, sx * 70, -10, 60, 60, "#d8262e" if sx < 0 else "#1a1a1a")
        burst(c, 0, -10, 60, "#ffd23f", t)
    elif kind == "heli":
        box(c, -110, -50, 200, 100, "#2a4a8a", r=50)
        line(c, 80, 0, 200, -20, "#2a4a8a", 18)
        line(c, -180 + math.sin(t * 30) * 30, -80, 180 - math.sin(t * 30) * 30, -80, "#141414", 8)
        line(c, -10, -50, -10, -80, "#141414", 8)
        box(c, -80, -30, 70, 40, "#9fd3ef", r=10, ow=3)
    elif kind == "dog":
        oval(c, 0, 10, 100, 55, "#c9925a")
        oval(c, 100, -40, 50, 44, "#c9925a")
        oval(c, 130, -70, 16, 30, "#8a5a3a")
        for x in (-70, -30, 40, 80):
            box(c, x - 10, 40, 20, 50, "#c9925a", r=8, ow=3)
        oval(c, 115, -45, 6, 6, "#141414", ow=0)
        T(c, "K9", 0, 20, 30, "#ffffff", LUCKY)
    elif kind == "boom":
        burst(c, 0, -10, 110, "#ff8a1a", t * 0.6)
        burst(c, 0, -10, 70, "#ffd23f", -t * 0.6)
        T(c, "BOOM", 0, 5, 44, "#d8262e", BANG)


@shot(427.4, 431.8)
def s_vinny_liz(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "cork")
        mug(c, 660, 520, "vinny", label="VINNY", expr="smile", rot=-5, t=t, bgcol="#e8d8a0",
            xmark=at(t, wt("killed", 430.2), 0.5))
        mug(c, 1260, 520, "liz", label="LIZ", expr="smile", rot=5, t=t, bgcol="#a8e0d8",
            xmark=at(t, wt("killed", 430.2) + 0.3, 0.5))
    caption_serif(c, "and people don't make it out alive", 960, 1010, 46, a=fade(t, 427.5))


@shot(431.8, 437.8)
def s_leash(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "vice_night", blur=6)
        tint_c(c, "#000000", 0.3)
        person(c, 700, 1010, "lucia", "lucia", "stand", "sad", t, s=1.3)
        person(c, 960, 1010, "jason", "jason", "stand", "sad", t, s=1.3)
        # giant hand holding leashes from top-right
        hx, hy = 1500, 200
        for x in (700, 960):
            pth = skia.Path()
            pth.moveTo(x + 20, 772)
            pth.quadTo((x + hx) / 2, 560, hx, hy + 30)
            c.drawPath(pth, P("#d8262e", 7))
            c.drawOval(skia.Rect(x - 40, 755, x + 40, 785), P("#d8262e", 9))
        with xf(c, hx + 30, hy):
            for k in range(4):
                oval(c, -70 + k * 42, 60, 22, 34, "#e9c4a2", ow=4)
            oval(c, 0, 0, 100, 80, "#e9c4a2")
            oval(c, -100, 10, 26, 40, "#e9c4a2", ow=4)
        tag(c, hx + 30, hy + 120, "GIORGIO", 34)
    k = fade(t, wt("betrays", 436.6) - 0.1)
    if k > 0:
        stamp(c, 960, 200, "BETRAYED", 100, a=k, s=lerp(1.6, 1, ease_out(k)), rot=-6)
    caption_serif(c, "every job feels more like a leash", 960, 1010, 46, a=window(t, 432.0, 436.3))


@shot(437.8, 448.2, "VICE CITY PD")
def s_danica(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "interrog")
        person(c, 600, 1010, "lucia", "lucia", "cuffed", "angry", t, s=1.2)
        person(c, 860, 1010, "jason", "jason", "cuffed", "neutral", t, s=1.2)
        person(c, 1380, 1010, "danica", "danica", "point", "neutral", t, s=1.25, talk=0.7 * window(t, 442.5, 448.0))
        box(c, 360, 740, 800, 50, "#6a6e74", r=4)
    tag(c, 1380, 370, "PROSECUTOR DANICA HOWARD", 32, a=fade(t, wt("prosecutor", 439.0)))
    speech(c, 1300, 230, ["BRING ME THAT", "HARD DRIVE."], 38, a=fade(t, wt("only", 444.8)),
           s=pop(t, wt("only", 444.8)), tail=(40, 90))
    tag(c, 700, 380, "WALK FREE?", 40, a=fade(t, wt("walk", 443.5)), bg="#7dff8a")


@shot(448.2, 454.6)
def s_fight_out(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, shake=0.18, t=t)
        draw_bg(c, "store")
        person(c, 760, 1010, "lucia", "lucia", "punch", "angry", t, s=1.3)
        person(c, 1000, 1010, "jason", "jason", "punchl", "angry", t, s=1.3)
        for i in range(3):
            fall = clamp((t - 449.0 - i * 1.2) / 0.4)
            with xf(c, 1400 + i * 170, 1010, rot=fall * 80):
                person(c, 0, 0, "cop", "cop", "point", "shock" if fall > 0 else "angry", t, s=1.1)
        for i in range(3):
            tm = 449.0 + i * 1.2
            if tm < t < tm + 0.35:
                burst(c, 1300 + i * 170, 700, 90, "#ffd23f", t)
                T(c, "POW!", 1300 + i * 170, 720, 50, "#d8262e", BANG)
    tag(c, 960, 160, "DIRTY COPS, ONE AFTER ANOTHER", 40, a=fade(t, 449.5))


@shot(454.6, 459.4)
def s_penthouse_storm(c, t, lt, d):
    if t < wt("then", 456.4) - 0.1:
        with xf(c):
            cam(c, lt, 2.0, 1.1, 1.0, t=t)
            draw_bg(c, "vice_night", blur=4)
            person(c, 700, 1100, "lucia", "lucia", "guard", "angry", t, s=1.7)
            person(c, 1300, 1100, "mendes", "mendes", "guard", "angry", t, s=1.7, flip=True)
            T(c, "VS", 1000, 640, 140, "#ffd23f", BANG, outline="#141414", ow=14)
        tag(c, 1300, 300, "MENDES", 44, a=fade(t, 454.7))
        return
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, shake=0.1, t=t)
        draw_bg(c, "penthouse")
        person(c, 700, 1010, "lucia", "lucia", "raise", "determined", t, s=1.3,
               prop=lambda c2: None)
        person(c, 980, 1010, "jason", "jason", "fist", "determined", t, s=1.3)
        k = pop(t, wt("drive", 458.6) - 0.2, 0.4)
        if k > 0:
            with xf(c, 700, 450, s=k):
                box(c, -70, -45, 140, 90, "#2a2a30", r=12)
                box(c, 30, 15, 24, 12, "#7dff8a", r=3, ow=2)
                glow(c, 0, 0, 160, "#7dff8a", 0.35)
    tag(c, 1400, 300, "GIORGIO'S PENTHOUSE", 38, a=fade(t, 456.5))


# ======================================================================= THE BRIDGE
def bridge_scene(c, t, lt, d, car_=True, people=True, lights=1.0):
    draw_bg(c, "bridge")
    for k in range(6):
        x = 120 + k * 340
        col = "#ff2a3a" if (int(t * 6) + k) % 2 else "#2a6aff"
        glow(c, x, 600, 220, col, 0.4 * lights)
    for i, x in enumerate((160, 420, 1500, 1760)):
        car(c, x, 640, 0.45, "#16161c", t, kind="cop", lights=lights, flip=(x > 960))
    if car_:
        car(c, 960, 640, 0.5, "#d8262e", t, kind="conv",
            people=[(-40, "jason", "jason", "worried"), (60, "lucia", "lucia", "worried")] if people else None)


@shot(459.4, 465.3, "THE BRIDGE")
def s_bridge(c, t, lt, d):
    if t < wt("run", 460.6) - 0.1:
        with xf(c):
            cam(c, lt, 1.2, 1.0, 1.04, t=t)
            draw_bg(c, "penthouse", blur=3)
        big_title(c, "YOU DID IT.", 960, 540, 140, t, 459.5, "#7dff8a")
        return
    with xf(c):
        cam(c, lt, d, 1.15, 1.0, cy=560, t=t)
        bridge_scene(c, t, lt, d)
    caption_serif(c, "police lights in every direction", 960, 1010, 46, a=fade(t, wt("police", 463.0)))


@shot(465.3, 474.4)
def s_surrender(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "bridge", blur=6)
        for k in range(4):
            glow(c, 200 + k * 500, 600, 300, "#ff2a3a" if (int(t * 6) + k) % 2 else "#2a6aff", 0.3)
        person(c, 700, 1060, "lucia", "lucia", "stand", "cry", t, s=1.6)
        person(c, 1200, 1060, "jason", "jason", "hold", "sad", t, s=1.6, talk=0.6 * window(t, 465.5, 469.7),
               prop=lambda c2: box(c2, -50, -170, 100, 60, "#2a2a30", r=8))
    caption_serif(c, "No way out.", 960, 200, 60, a=window(t, 465.4, 466.8))
    speech(c, 1250, 230, ["I'LL SURRENDER.", "TAKE THE DRIVE.", "GO HOME TO TOMMY."], 34,
           a=window(t, wt("surrender", 467.2) - 0.3, 473.8), s=pop(t, wt("surrender", 467.2) - 0.3), tail=(-20, 90))


@shot(474.4, 479.6)
def s_refuse(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.1, 1.2, cx=760, cy=520, t=t)
        draw_bg(c, "bridge", blur=6)
        person(c, 760, 1100, "lucia", "lucia", "cross", "determined", t, s=1.9)
    big_title(c, "NO.", 1380, 380, 180, t, wt("refuse", 472.6) + 0.1, "#ff4a4a")
    caption_serif(c, "you've never once given up on him", 960, 1010, 46, a=fade(t, 475.0))


@shot(479.6, 485.8, "ENDING 1")
def s_jump(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "bridge")
        jp = wt("jump", 481.7)
        k = clamp((t - jp) / 3.2)
        y = 520 + k * k * 700
        for i, (who, x) in enumerate((("lucia", 900), ("jason", 1040))):
            person(c, x, y, who, who, "raise" if k > 0 else "stand", "scared" if k > 0 else "determined", t, s=0.75)
        line(c, 930, y - 150, 1010, y - 150, "#e9c4a2", 10)
    tag(c, 960, 150, "HAND IN HAND", 44, a=fade(t, wt("hand", 483.5)))
    k = pop(t, wt("slips", 484.6), 0.4)
    if k > 0:
        tag(c, 1460, 320, "HE SLIPS YOU THE DRIVE", 34, s=k, bg="#7dff8a")


@shot(485.8, 492.2)
def s_lets_go(c, t, lt, d):
    lg = wt("go", 487.5)
    with xf(c):
        cam(c, lt, d, 1.0, 1.04, t=t)
        if t < wt("water", 489.3):
            grad_rect(c, 0, 0, W, H, ["#05061a", "#141a40"])
            for i in range(30):
                y = ((i * 97 + t * 900) % (H + 200)) - 100
                line(c, (i * 131) % W, y, (i * 131) % W, y + 120, "#ffffff", 3, 0.3)
            sep = smooth(at(t, lg, 0.8)) * 220
            person(c, 860 - sep * 0.4, 760, "lucia", "lucia", "reach", "shock", t, s=1.2)
            person(c, 1060 + sep, 760 - sep * 0.6, "jason", "jason", "reach", "sad", t, s=1.2)
            if sep < 10:
                line(c, 900, 600, 1020, 600, "#e9c4a2", 10)
            big_title(c, "HE LETS GO", 960, 180, 100, t, lg, "#ffffff")
        else:
            draw_bg(c, "water")
            wk = t - wt("water", 489.3)
            for i in range(20):
                c.drawCircle(860 + (i * 47) % 260, 900 - ((wk * 300 + i * 70) % 900), 8 + i % 4,
                             P("#bfefff", 3, 0.6))
            person(c, 960, 900 - wk * 120, "lucia", "lucia", "raise", "determined", t, s=1.2)
            tag(c, 960, 160, "ESCAPE", 56, s=pop(t, wt("escape", 490.4)), bg="#7dff8a")
    flash(c, t, wt("water", 489.3), 0.3, "#e8f8ff")


@shot(492.2, 496.4)
def s_credits_son(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "home_happy")
        person(c, 960, 1010, "lucia", "lucia", "hold", "happy", t, s=1.4,
               prop=lambda c2: baby_bundle(c2, 0, -150, 1.1, t, "tommy", "tommy", "#8fc6ef", "happy"))
    tag(c, 960, 160, "DEAL TAKEN · TOMMY BACK", 40, a=fade(t, 492.3))
    for i in range(4):
        heart(c, 1260 + i * 40, 360 - ((t * 60 + i * 50) % 200), 0.7, a=0.85)


@shot(496.4, 501.9)
def s_visit(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "visit")
        person(c, 780, 900, "jason", "inmate", "phone", "smile", t, s=1.1)
        box(c, 0, 680, W, 50, "#8a8a80", ow=5)
        box(c, 0, 730, W, 300, "#6a6a62", ow=5)
        person(c, 1180, 1050, "lucia", "lucia", "stand", "smile", t, s=1.2)
        person(c, 1380, 1050, "tommy", "tommy_kid", "wave", "happy", t, s=1.2)
    tag(c, 960, 160, "YEARS LATER", 44, a=fade(t, wt("years", 496.0)))


@shot(501.9, 508.7, "ENDING 2")
def s_stand(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, shake=0.12 * (t > wt("fire", 507.6)), t=t)
        bridge_scene(c, t, lt, d, car_=False)
        person(c, 860, 1000, "lucia", "lucia", "point", "determined", t, s=1.25)
        person(c, 1080, 1000, "jason", "jason", "pointl", "determined", t, s=1.25)
        if t > wt("fire", 507.6):
            for sx, x in ((1, 1100), (-1, 840)):
                if int(t * 12) % 2:
                    burst(c, x + sx * 250, 690, 40, "#ffd23f", t)
    tag(c, 960, 150, "NEVER SURRENDER", 50, a=fade(t, 502.0), bg="#ff8a8a")


@shot(508.7, 514.4)
def s_bonnie(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "dark")

        def inner(cc, iw, ih):
            grad_rect(cc, 0, 0, iw, ih, ["#c8b89a", "#8a7a5a"])
            person(cc, iw * 0.35, ih * 1.05, "lucia", "lucia", "hug", "smirk", t, s=0.75)
            person(cc, iw * 0.65, ih * 1.05, "jason", "jason", "hug", "smirk", t, s=0.75)

        polaroid(c, 960, 500, 760, 640, inner, "BONNIE & CLYDE", rot=-3)
        k = smooth(at(t, wt("fall", 510.9), 1.5))
        tint_c(c, "#000000", 0.55 * k)
    caption_serif(c, "You fall together, still holding hands.", 960, 1010, 48, a=fade(t, wt("fall", 510.9)))


@shot(514.4, 521.5)
def s_frame_home(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "living")
        person(c, 700, 1000, "mom", "mom", "hug", "sad", t, s=1.3)
        person(c, 960, 1000, "tommy", "tommy_kid", "stand", "sad", t, s=1.3)
        with xf(c, 1400, 640, rot=3):
            box(c, -140, -170, 280, 340, "#6b4a33", r=6)
            box(c, -115, -145, 230, 290, "#c8b89a", r=2, ow=3)
            with xf(c, -50, 0):
                head(c, "lucia", "lucia", 50, "smile", t, blink_ok=False)
            with xf(c, 55, 0):
                head(c, "jason", "jason", 50, "smile", t, blink_ok=False)
    caption_serif(c, "And those are just two of the endings.", 960, 1010, 48, a=fade(t, wt("those", 518.5)))


# ======================================================================= RECAP + CHOICE SYSTEM
@shot(521.5, 533.2)
def s_recap1(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "cork")
        mug(c, 420, 420, "lucia", "lucia_kid", "FISTS UP", "determined", rot=-6, t=t, pose="guard",
            s=pop(t, 521.6, 0.4))
        items = [("FREEDOM", wt("freedom", 523.6), "cell"), ("HOME", wt("home", 524.3), "fire"),
                 ("NEARLY YOUR SON", wt("son", 525.6), "tommy")]
        for i, (lab, tm, kind) in enumerate(items):
            k = pop(t, tm - 0.1, 0.4)
            if k > 0:
                x = 860 + i * 380
                if kind == "tommy":
                    mug(c, x, 420, "tommy", "tommy_kid", lab, "sad", rot=4, t=t, s=k * 0.85)
                else:
                    def inner(cc, iw, ih, kind=kind):
                        if kind == "cell":
                            grad_rect(cc, 0, 0, iw, ih, ["#8d9298", "#5a5f66"])
                            bars(cc, 0, iw, -20, ih + 20, n=4)
                        else:
                            grad_rect(cc, 0, 0, iw, ih, ["#141a40", "#2a1f5a"])
                            draw_fire(cc, iw / 2, ih, iw, ih * 0.8, t)
                    polaroid(c, x, 420, 300, 380, inner, lab, rot=(-4 + i * 4), s=k * 0.85)
        k = fade(t, wt("turned", 527.7))
        if k > 0:
            tag(c, 640, 860, "TURNED DOWN THE EASY WAY OUT", 36, a=k, rot=-3)
        k = fade(t, wt("chose", 529.8))
        if k > 0:
            tag(c, 1300, 940, "CHOSE JASON EVERY TIME", 36, a=k, rot=3, bg="#ff8a8a")


@shot(533.2, 538.7, "THE BRIDGE")
def s_jump_or_fight(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "bridge", blur=3)
        tint_c(c, "#000000", 0.35)
    doors(c, t, 533.3, ["JUMP?", "STAND AND FIGHT?"])


@shot(538.7, 548.9)
def s_hundred(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "dark")
        n = 40
        for i in range(n):
            x = 120 + i * 43
            fall = smooth(at(t, wt("hundred", 543.3) + i * 0.06, 0.25))
            with xf(c, x, 700, rot=fall * 60):
                box(c, -14, -110, 28, 110, "#f2f2f2", r=4, ow=3)
    caption_serif(c, "There's something you need to know.", 960, 260, 52, a=window(t, 538.8, 541.0))
    k = fade(t, wt("never", 541.2))
    if k > 0 and t < 543.0:
        T(c, "THE ENDING WAS NEVER DECIDED THERE", 960, 300, 56, "#ffffff", LUCKY, a=k, outline="#141414", ow=8)
    k = fade(t, wt("hundred", 543.3))
    if k > 0:
        T(c, "100 SMALL MOMENTS AGO", 960, 300, 80, "#ffd23f", LUCKY, a=k, outline="#141414", ow=10)
    caption_serif(c, "and you barely noticed", 960, 1010, 46, a=fade(t, wt("barely", 546.8)))


@shot(548.9, 560.1, "HIDDEN STATS")
def s_bond(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.04, t=t)
        draw_bg(c, "cork")
        mug(c, 420, 480, "lucia", "lucia", "LUCIA", "smile", rot=-5, t=t)
        mug(c, 1500, 480, "jason", label="JASON", expr="smile", rot=5, t=t)
        n = int(clamp((t - wt("heart", 553.3)) / 3.5) * 10) if t > 550 else 0
        for i in range(10):
            filled = i < n
            heart(c, 640 + i * 70, 500, 0.7 if not filled else 0.7 + 0.1 * pop(t, wt("heart", 553.3) + i * 0.35, 0.3),
                  "#e8283a" if filled else "#8a6a4a", a=1 if filled else 0.5)
    tag(c, 960, 220, "BOND METER", 50, a=fade(t, 549.0))
    k = fade(t, wt("top", 554.3))
    if k > 0:
        tag(c, 960, 760, "MAX: THROUGH LIFE AND DEATH", 40, a=k, bg="#ff8a8a")


@shot(560.1, 572.4, "HIDDEN STATS")
def s_style(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.04, t=t)
        draw_bg(c, "dark")
        box(c, 360, 500, 1200, 60, "#2a2a30", r=30, ow=5, oc="#f2f2f2")
        grad_rect(c, 365, 505, 1190, 50, ["#3ccf6a", "#ffd23f", "#ff2a3a"], vertical=False)
        v = 0.5 + 0.42 * math.sin((t - 561) * 1.3)
        oval(c, 365 + v * 1190, 530, 44, 44, "#ffffff", ow=6)
        T(c, "CLEAN · CAREFUL", 360, 650, 46, "#3ccf6a", LUCKY, align="left", a=fade(t, wt("clean", 563.2)))
        T(c, "WILD · LOUD · OUT OF CONTROL", 1560, 650, 46, "#ff4a4a", LUCKY, align="right", a=fade(t, wt("wild", 564.4)))
    tag(c, 960, 260, "EVERY ROBBERY + SHOOTOUT COUNTS", 40, a=fade(t, 560.2))
    caption_serif(c, "The game decides who you are... and it remembers.", 960, 1010, 46,
                  a=fade(t, wt("decides", 567.0)))


@shot(572.4, 586.6, "BUG ME")
def s_bugme(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.04, t=t)
        draw_bg(c, "living_night", blur=6)
        tint_c(c, "#000000", 0.3)
    goals = [(5000, wt("$5", 579.0)), (15000, wt("$15", 580.7)), (100000, wt("$100", 582.3))]

    def scr(cc):
        grad_rect(cc, -150, -300, 300, 600, ["#1b2b1b", "#0e180e"])
        T(cc, "BUG ME", 0, -230, 46, "#7dff8a", LUCKY)
        T(cc, "SAVINGS", 0, -190, 22, "#c9f2c9", "interb")
        goal = 0
        for g, tm in goals:
            if t >= tm - 0.2:
                goal = g
        amt = goal * clamp((t - 576) / 10) if goal else 0
        T(cc, f"${int(amt):,}", 0, -80, 50, "#ffffff", "inter")
        T(cc, f"GOAL ${goal:,}" if goal else "GOAL: ---", 0, -30, 24, "#c9f2c9", "interb")
        box(cc, -120, 10, 240, 24, "#2a3a2a", r=12, ow=0)
        if goal:
            box(cc, -120, 10, 240 * clamp(amt / goal), 24, "#7dff8a", r=12, ow=0)
        for i, (g, tm) in enumerate(goals):
            a = fade(t, tm - 0.2)
            T(cc, f"${g:,}", 0, 110 + i * 55, 32, "#7dff8a", LUCKY, a=a)

    phone_screen(c, 960, 540, 1.3 * pop(t, 572.6, 0.5), scr)
    tag(c, 420, 300, "NOT THE THRILL OF CASH", 34, a=window(t, 572.5, 576.0), rot=-4)
    k = fade(t, wt("promise", 584.6))
    if k > 0:
        mug(c, 1520, 520, "tommy", "tommy_kid", "FOR TOMMY", "happy", rot=6, t=t, s=k)


@shot(586.6, 594.6)
def s_aunt(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "home_happy")
        person(c, 1250, 1010, "aunt", "aunt", "hug", "smile", t, s=1.3)
        person(c, 1500, 1010, "tommy", "tommy_kid", "wave", "happy", t, s=1.3)
        k = clamp((t - 587.5) / 2.0)
        for i in range(5):
            kk = clamp(k * 1.5 - i * 0.12)
            if 0 < kk < 1:
                cash(c, lerp(400, 1150, kk), 500 - math.sin(kk * math.pi) * 200, 1.0, rot=kk * 360)
    phone_screen(c, 380, 560, 0.7, lambda cc: (grad_rect(cc, -150, -300, 300, 600, ["#1b2b1b", "#0e180e"]),
                                               T(cc, "SEND $", 0, -60, 50, "#7dff8a", LUCKY),
                                               T(cc, "TO: AUNT", 0, 10, 34, "#ffffff", "interb")), rot=-6)
    tag(c, 1250, 380, "LUCIA'S AUNT", 34, a=fade(t, wt("aunt", 590.0)))
    tag(c, 960, 140, "SIDE QUEST", 46, a=fade(t, wt("side", 588.0)), bg="#ffd23f")


@shot(594.6, 600.4)
def s_doors_close(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "dark")
    for i in range(3):
        k = smooth(at(t, wt("close", 595.5) + i * 0.3, 0.4))
        with xf(c, 520 + i * 440, 860, s=pop(t, 594.7 + i * 0.15, 0.4)):
            box(c, -140, -440, 280, 440, "#2a2a30", r=6, ow=6)
            box(c, -130, -430, 260 * (1 - (1 - k) * 0.7) if False else 260 * lerp(0.3, 1, k), 430, "#6a4a32", r=4, ow=5)
            rect(c, -130 + 260 * lerp(0.3, 1, k), -430, 260 * (1 - lerp(0.3, 1, k)), 430, "#fff6d8", 0.8)
    tag(c, 960, 200, "SKIP IT = DOORS CLOSE FOR GOOD", 44, a=fade(t, 594.7))


@shot(600.4, 607.4)
def s_arnold(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "keys")
        person(c, 700, 1010, "jason", "jason", "stand", "neutral", t, s=1.3)
        person(c, 1200, 1010, "arnold", "arnold", "raise", "scared" if t < 603.5 else "happy", t, s=1.3)
    tag(c, 1200, 400, "ARNOLD", 38, a=fade(t, wt("arnold", 602.5)))
    k = fade(t, wt("spares", 601.5))
    if k > 0:
        stamp(c, 960, 200, "SPARED", 90, a=k, s=lerp(1.5, 1, ease_out(k)), color="#2e8b57", rot=-5)


@shot(607.4, 613.6)
def s_payback(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "keys")
        person(c, 700, 1010, "brian", "brian", "hug", "smile", t, s=1.3)
        person(c, 960, 1010, "arnold", "arnold", "hug", "smile", t, s=1.3)
    k = pop(t, 607.6, 0.4)
    if k > 0:
        with xf(c, 1450, 520, s=k):
            money_bag(c, 0, 0, 2.6)
            T(c, "+$10,000", 0, 200, 70, "#7dff8a", LUCKY, outline="#141414", ow=10)
    caption_serif(c, "one small kindness, paid back when you need it most", 960, 1010, 44, a=fade(t, 607.5))


@shot(613.6, 623.9, "THE BRIDGE")
def s_two_doors(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.05, 1.0, t=t)
        bridge_scene(c, t, lt, d)
        tint_c(c, "#000000", 0.35 * fade(t, 617.0))
    if t > wt("two", 617.6) - 0.2:
        doors(c, t, wt("two", 617.6) - 0.1, ["SWIM FOR IT", "NEVER SURRENDER"])
    caption_serif(c, "the game already knows exactly who you are", 960, 1010, 44, a=window(t, 613.8, 617.0))


def stats_card(c, t, start, love, record, savings, x=420, y=300):
    k = pop(t, start, 0.4)
    if k <= 0:
        return
    with xf(c, x, y, s=k):
        box(c, -300, -120, 600, 420, "#141418", r=18, ow=5, oc="#f2f2f2")
        for i, (lab, val, col) in enumerate((("LOVE", love, "#ff5f7a"), ("RECORD", record, "#5fe3ff"),
                                             ("SAVINGS", savings, "#7dff8a"))):
            yy = -40 + i * 120
            T(c, lab, -270, yy, 36, "#f2f2f2", LUCKY, align="left")
            box(c, -270, yy + 20, 540, 30, "#2a2a30", r=15, ow=0)
            box(c, -270, yy + 20, 540 * val * clamp((t - start - 0.3 - i * 0.3) / 0.6), 30, col, r=15, ow=0)


@shot(623.9, 635.7, "ENDING A")
def s_end_a(c, t, lt, d):
    if t < wt("points", 629.0) - 0.2:
        with xf(c):
            cam(c, lt, 5, 1.0, 1.04, t=t)
            draw_bg(c, "bridge", blur=6)
            tint_c(c, "#000000", 0.4)
        stats_card(c, t, 624.0, 0.95, 0.85, 0.35, x=960, y=420)
        tag(c, 960, 160, "CHOOSE TO JUMP", 50, a=fade(t, 624.0), bg="#5fb3ff")
        tag(c, 1400, 880, "SAVINGS FALL SHORT", 34, a=fade(t, wt("short", 628.8)), bg="#ff8a8a")
        return
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        bridge_scene(c, t, lt, d, car_=False)
        person(c, 860, 1000, "lucia", "lucia", "stand", "worried", t, s=1.25)
        person(c, 1080, 1000, "jason", "jason", "pointl", "determined", t, s=1.25, talk=0.6 * window(t, 630.2, 631.0))
    speech(c, 1160, 360, ["WE JUMP."], 48, a=fade(t, wt("we", 630.3)), s=pop(t, wt("we", 630.3)), tail=(-30, 90))
    tag(c, 500, 300, "→ SANDBANK", 40, a=fade(t, wt("sand", 629.5)))
    k = fade(t, wt("lets", 632.0))
    if k > 0:
        caption_serif(c, "In midair, he lets go of your hand, so you land free.", 960, 1010, 42, a=k)


@shot(635.7, 645.2)
def s_end_a2(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        if t < wt("raise", 643.0) - 0.4:
            draw_bg(c, "visit")
            person(c, 760, 900, "jason", "inmate", "phone", "sad", t, s=1.1)
            box(c, 0, 680, W, 50, "#8a8a80", ow=5)
            box(c, 0, 730, W, 300, "#6a6a62", ow=5)
            person(c, 1260, 1050, "tommy", "tommy_kid", "wave", "sad", t, s=1.2)
            tag(c, 760, 380, "JASON · LIFE IN PRISON", 34, a=fade(t, 635.8))
            tag(c, 1260, 460, "ONE LAST VISIT", 34, a=fade(t, wt("visit", 639.6)))
        else:
            draw_bg(c, "living")
            person(c, 860, 1000, "lucia", "lucia", "hug", "sad", t, s=1.3)
            person(c, 1100, 1000, "tommy", "tommy_kid", "stand", "smile", t, s=1.3)
            tag(c, 960, 160, "YOU RAISE TOMMY ALONE", 44, a=fade(t, wt("raise", 643.0) - 0.3))


@shot(645.2, 652.0, "ENDING B")
def s_end_b(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.04, t=t)
        draw_bg(c, "bridge", blur=6)
        tint_c(c, "#000000", 0.4)
    stats_card(c, t, 645.4, 0.95, 0.85, 1.0, x=960, y=420)
    tag(c, 960, 160, "SAME JUMP · SAME SACRIFICE", 46, a=fade(t, 645.3), bg="#5fb3ff")
    k = pop(t, wt("talks", 649.3), 0.4)
    if k > 0:
        T(c, "MONEY TALKS.", 960, 960, 100 * k, "#7dff8a", LUCKY, outline="#141414", ow=12)


@shot(652.0, 662.3)
def s_call_abe(c, t, lt, d):
    if t < wt("prison", 661.0) - 1.6:
        with xf(c):
            cam(c, lt, 7, 1.0, 1.05, t=t)
            draw_bg(c, "lawyer")
            person(c, 600, 1010, "lucia", "lucia", "phone", "determined", t, s=1.3, talk=0.5)
            person(c, 1320, 860, "abe", "abe", "phone", "smirk", t, s=1.1)
            box(c, 360, 760, 1200, 70, "#6a4428", r=6)
        tag(c, 1320, 380, "ABE", 40, a=fade(t, 652.1))
        caption_serif(c, "this time, you use him to bring Jason home", 960, 1010, 44, a=fade(t, wt("this", 655.0)))
        k = pop(t, wt("cash", 658.3), 0.4)
        if k > 0:
            with xf(c, 960, 300, s=k):
                for i in range(5):
                    cash(c, -160 + i * 80, 0, 1.2, rot=-10 + i * 5)
                T(c, "+ SHADY DEALS", 0, 110, 40, "#ffd23f", LUCKY, outline="#141414", ow=8)
        return
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "gate")
        from sets import set_gate_open
        k = smooth(at(t, wt("opens", 661.6) - 0.5, 1.4))
        set_gate_open(c, k)
        if k > 0.3:
            person(c, lerp(960, 1200, k), 960, "jason", "jason", "wave", "happy", t, s=1.2)
    stamp(c, 960, 200, "DOOR OPENS", 80, a=fade(t, wt("opens", 661.6) - 0.3), color="#2e8b57", rot=-5)


@shot(662.3, 666.9)
def s_happy(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "home_happy")
        person(c, 680, 1010, "jason", "jason", "hug", "happy", t, s=1.3)
        person(c, 960, 1010, "tommy", "tommy_kid", "raise", "laugh", t, s=1.3)
        person(c, 1240, 1010, "lucia", "lucia", "hug", "happy", t, s=1.3)
        for i in range(6):
            heart(c, 400 + i * 230, 300 - ((t * 50 + i * 40) % 140), 0.7, a=0.85)
    big_title(c, "THE HAPPIEST ENDING", 960, 170, 90, t, wt("happiest", 664.6) - 0.2, "#ffd23f")


@shot(666.9, 677.9, "ENDING C")
def s_end_c(c, t, lt, d):
    if t < wt("tommy", 677.0) - 0.2:
        with xf(c):
            cam(c, lt, d, 1.0, 1.06, shake=0.1 * (t > 670), t=t)
            bridge_scene(c, t, lt, d, car_=False)
            adv = smooth(at(t, wt("charge", 670.2), 2.0))
            person(c, 860 + adv * 120, 1000, "lucia", "lucia", "point", "angry", t, s=1.25, walk=t if adv < 1 else 0)
            person(c, 1080 + adv * 120, 1000, "jason", "jason", "point", "angry", t, s=1.25, walk=t if adv < 1 else 0)
            if t > 671.5 and int(t * 12) % 2:
                burst(c, 1400 + adv * 120, 690, 40, "#ffd23f", t)
        tag(c, 960, 160, "CHOOSE TO NEVER SURRENDER", 46, a=fade(t, 667.0), bg="#ff8a8a")
        k = smooth(at(t, wt("fall", 675.0), 1.0))
        tint_c(c, "#000000", 0.75 * k)
        if k > 0:
            caption_serif(c, "You fall together.", 960, 540, 64, a=k)
        return
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "living")
        person(c, 680, 1000, "aunt", "aunt", "hug", "sad", t, s=1.25)
        person(c, 960, 1000, "tommy", "tommy_kid", "stand", "sad", t, s=1.25)
        person(c, 1240, 1000, "mom", "mom", "hug", "sad", t, s=1.25)
    tag(c, 1240, 400, "MIA", 36, a=fade(t, wt("mia", 677.5)))
    tag(c, 680, 400, "AUNT", 36, a=fade(t, 677.3))


@shot(677.9, 682.9)
def s_explain(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.05, 1.15, cx=1100, t=t)
        draw_bg(c, "living_night")
        person(c, 960, 1000, "tommy", "tommy_kid", "stand", "cry", t, s=1.4)
        person(c, 1240, 1000, "mom", "mom", "hug", "sad", t, s=1.4, talk=0.4)
    caption_serif(c, "the one thing a child should never have to hear", 960, 1010, 44, a=fade(t, 678.6))


@shot(682.9, 691.6, "THE DARKEST DOOR")
def s_psycho(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.04, t=t)
        draw_bg(c, "dark")
        tint_c(c, "#2a0005", 0.5)
        box(c, 360, 520, 1200, 60, "#2a2a30", r=30, ow=5, oc="#f2f2f2")
        grad_rect(c, 365, 525, 1190, 50, ["#3ccf6a", "#ffd23f", "#ff2a3a"], vertical=False)
        v = lerp(0.5, 0.98, smooth(at(t, wt("wild", 686.6), 2.0)))
        oval(c, 365 + v * 1190, 550, 44, 44, "#ffffff", ow=6)
        if t > wt("psychopath", 689.8):
            glow(c, 1520, 550, 250, "#ff2a3a", 0.5 + 0.3 * math.sin(t * 10))
    big_title(c, "THE DARKEST DOOR", 960, 230, 90, t, 683.0, "#ff4a4a")
    k = fade(t, wt("psychopath", 689.8) - 0.1)
    if k > 0:
        stamp(c, 1300, 800, "PSYCHOPATH", 80, a=k, s=lerp(1.5, 1, ease_out(k)), rot=-6)


@shot(691.6, 697.0)
def s_kiss(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.05, 1.2, cy=480, t=t)
        draw_bg(c, "bridge", blur=6)
        tint_c(c, "#000000", 0.3)
        k = smooth(at(t, wt("kiss", 694.0) - 0.4, 0.6))
        with xf(c, 860 + k * 50, 520):
            head(c, "lucia", "lucia", 150, "happy" if k > 0.9 else "sad", t, look=(5, 0))
        with xf(c, 1080 - k * 50, 520):
            head(c, "jason", "jason", 150, "happy" if k > 0.9 else "sad", t, look=(-5, 0))
        if k > 0.9:
            heart(c, 970, 300, 1.2 * pop(t, wt("kiss", 694.0) + 0.2, 0.4))
    caption_serif(c, "Jason suggests it.", 960, 1010, 48, a=window(t, 691.7, 693.6))


@shot(697.0, 702.7)
def s_shoot_first(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        bridge_scene(c, t, lt, d, car_=True, people=False)
        person(c, 1150, 640, "jason", "jason", "raise", "sad", t, s=0.7)
    tag(c, 1150, 300, "HANDS UP", 40, a=fade(t, 697.2))
    sh = wt("shoot", 700.7)
    flash(c, t, sh, 0.3, "#ffffff")
    if t > sh + 0.2:
        tint_c(c, "#000000", smooth(at(t, sh + 0.2, 0.8)))
        caption_serif(c, "The police shoot first.", 960, 540, 60, a=fade(t, sh + 0.4))


@shot(702.7, 709.5)
def s_mia_tears(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "living")
        tint_c(c, "#1a1030", 0.2)
        person(c, 760, 1000, "aunt", "aunt", "hug", "sad", t, s=1.25)
        person(c, 1010, 1000, "tommy", "tommy_kid", "stand", "sad", t, s=1.25)
        person(c, 1300, 1000, "mom", "mom", "cry", "cry", t, s=1.25)
    tag(c, 1300, 400, "MIA", 36, a=fade(t, wt("mia", 703.2)))
    caption_serif(c, "Tommy grows up with his aunt.", 960, 1010, 46, a=window(t, 702.8, 706.0))


@shot(709.5, 717.7)
def s_four(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.04, t=t)
        draw_bg(c, "dark")
    cols = ("#5fb3ff", "#7dff8a", "#ff8a8a", "#8a2a3a")
    labs = ("JUMP", "JUMP + SAVED", "STAND", "PSYCHO")
    for i in range(4):
        k = pop(t, 709.7 + i * 0.25, 0.4)
        if k <= 0:
            continue
        with xf(c, 330 + i * 420, 860, s=k * 0.85):
            glow(c, 0, -230, 320, cols[i], 0.3)
            box(c, -140, -450, 280, 450, cols[i], r=8, ow=6)
            oval(c, 100, -220, 12, 12, "#e8c25a", ow=3)
            tag(c, 0, -500, labs[i], 34)
    big_title(c, "4 ENDINGS", 960, 170, 100, t, 709.6, "#ffffff")
    k = fade(t, wt("more", 709.2) if wt("more", 709.2) > 709.5 else 711.0)
    caption_serif(c, "None of them is bad. Only different.", 960, 1010, 48, a=fade(t, wt("none", 710.1)))


@shot(717.7, 728.2, "VICE CITY")
def s_not_yet(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "vice_night")
        rect(c, 0, 900, W, 180, "#1c1a2a")
        drv = t > wt("drive", 726.8) - 0.3
        for k in range(10):
            x = (k * 240 - t * (900 if drv else 0)) % (W + 240) - 120
            rect(c, x, 980, 120, 10, "#f2e6b8")
        cx = 960 + (smooth(at(t, wt("drive", 726.8), 1.5)) * 900 if drv else 0)
        car(c, cx, 1040, 0.7, "#d8262e", t, moving=1.0 if drv else 0, kind="conv", lights=1,
            people=[(-40, "jason", "jason", "smirk"), (60, "lucia", "lucia", "smirk")])
    k = fade(t, wt("finale", 718.8))
    if k > 0 and t < wt("asks", 721.0):
        with xf(c, 960, 380, alpha=k):
            box(c, -300, -150, 600, 300, "#efe2c4", r=10)
            T(c, "FINALE", 0, -60, 50, "#a3261e", LUCKY)
            oval(c, 0, 40, 40, 40, "#ffd23f")
            T(c, "!", 0, 58, 50, "#141414", LUCKY)
    speech(c, 960, 380, ["READY?"], 60, a=window(t, wt("ready", 722.3) - 0.3, 724.2), s=pop(t, wt("ready", 722.3) - 0.3))
    speech(c, 1100, 520, ["NOT YET."], 60, a=window(t, wt("yet", 724.4) - 0.1, 727.0), s=pop(t, wt("yet", 724.4) - 0.1),
           tail=(-40, 90))


@shot(728.2, 734.6)
def s_100(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.05, t=t)
        draw_bg(c, "map")
    checklist(c, 260, 400, ["FINISH THE MAP", "CHASE 100%", "TRY THE BRIDGE AGAIN"], t,
              [wt("finish", 728.8), wt("chase", 729.9), wt("return", 731.0)], size=58)


@shot(734.6, 744.9)
def s_recap2(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.06, t=t)
        draw_bg(c, "cork")
    items = [("lucia", "lucia_baby", "TAUGHT TO FIGHT", "determined", 735.0, 360, 330),
             ("mom", "mom", "A MOTHER'S DREAM", "smile", wt("mother", 740.0), 860, 330),
             ("lucia", "lucia_p", "A PRISON CELL", "sad", wt("prison", 741.7), 1360, 330),
             ("tommy", "tommy", "A SON TAKEN", "cry", wt("son", 743.0), 1600, 700)]
    for i, (who, lk, lab, ex, tm, x, y) in enumerate(items):
        k = pop(t, tm - 0.2, 0.4)
        if k > 0:
            mug(c, x, y, who, lk, lab, ex, rot=(-5 + i * 4), t=t, s=k * 0.9)
    k = pop(t, wt("robbery", 741.0) - 0.2, 0.4)
    if k > 0:
        with xf(c, 560, 760, s=k, rot=-6):
            stamp(c, 0, 0, "ROBBERY", 70, rot=0)


@shot(744.9, 756.0)
def s_recap3(c, t, lt, d):
    with xf(c):
        cam(c, lt, d, 1.0, 1.1, t=t)
        draw_bg(c, "vice_sunset")
        person(c, 760, 1050, "lucia", "lucia", "hug", "smile", t, s=1.5)
        person(c, 1080, 1050, "jason", "jason", "hug", "smile", t, s=1.5)
    tag(c, 960, 170, "TURNED DOWN THE EASY WAY OUT", 40, a=window(t, 745.0, 747.0))
    tag(c, 960, 170, "CHOSE JASON, EVEN WHEN IT HURT", 40, a=window(t, wt("chose", 747.0), 749.0))
    k = fade(t, wt("who", 751.0))
    if k > 0:
        T(c, "WHO YOU BECAME", 960, 220, 80, "#ffffff", LUCKY, a=k, outline="#141414", ow=10)
    k = fade(t, wt("saved", 753.6))
    if k > 0:
        T(c, "+ WHAT YOU SAVED", 960, 320, 70, "#7dff8a", LUCKY, a=k, outline="#141414", ow=10)


@shot(756.0, 770.0, "THE BRIDGE")
def s_final(c, t, lt, d):
    with xf(c):
        cam(c, lt, 5, 1.05, 1.0, t=t)
        bridge_scene(c, t, lt, d)
        tint_c(c, "#000000", 0.45)
    doors(c, t, 756.2, ["JUMP", "NEVER SURRENDER"])
    big_title(c, "WHICH DOOR WOULD YOU CHOOSE?", 960, 160, 72, t, wt("which", 758.6) - 0.2, "#ffd23f")
    k = fade(t, 759.5)
    if k > 0:
        with xf(c, 960, 1000, alpha=k):
            box(c, -360, -46, 720, 92, "#ffffff", r=20, ow=5, oc="#141414")
            T(c, "Tell me in the comments!", 0, 14, 38, "#141414", "interb")
