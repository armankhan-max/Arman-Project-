"""Timeline part B (3:03 - end)."""
import math
import random

import skia

from pgfx import *  # noqa: F401,F403
from psets import *  # noqa: F401,F403
from pscenes_a import cam, push, head_cu, walker_person, gesture, host_shot, tag2, loc_tag  # noqa: F401


def s_jobseeker(c, t):
    a = 183.5
    cam(c, push(t, a, 189.7, 1.0, 1.06), 960, 560, t)
    bg(c, "living", 8)
    # shoes waiting by the door
    for i in range(2):
        with xf(c, 1560 + i * 70, 870):
            rrect(c, -30, -16, 70, 30, 12, "#3a2c22")
    rrect(c, 500, 640, 760, 160, 50, "#4a5170")
    rrect(c, 520, 520, 720, 160, 50, "#3e4562")
    # tries to get up, flops back
    up = max(0.0, math.sin(clamp((t - 187.6) / 1.4) * math.pi))
    person(c, 860, 700 - up * 70, "job", mix_pose("sitslump", "reach", up * 0.7), "dreamy" if t < 187.4 else "tired",
           t, 1.15, face=1, look=(0.8, -0.2), tilt=5, chair=False)
    thought_bubbles(c, 960, 380, 1060, 260, t, window(t, a, 187.4, 0.4))
    with xf(c, 1180, 190, alpha=window(t, a, 187.4, 0.4)):
        soft(c, 0, 0, 130, GOLD, 0.3, 40)
        c.drawCircle(0, 0, 110, P("#fff2d6"))
        dtext(c, "HIRED!", 0, 20, 70, "#2e7d5a", "bebas", track=0.06)
    battery(c, 360, 480, 0.5, 0.12, t)
    lower(c, t, 184.0, "THE JOB SEEKER", "Energy to pound the pavement: low", GOLD, dur=5.2)


def s_lovesick(c, t):
    a = 189.6
    cam(c, push(t, a, 194.0, 1.0, 1.05), 960, 560, t)
    bg(c, "cafe", 8)
    rrect(c, 260, 700, 480, 30, 8, "#5a3a26")
    rise = max(0.0, math.sin(clamp((t - 191.6) / 1.2) * math.pi))
    person(c, 440, 700 - rise * 60, "leo", mix_pose("sitthink", "reach", rise * 0.6), "dreamy" if t < 191.5 else "worried",
           t, 1.1, face=1, look=(1, -0.2))
    rrect(c, 1180, 700, 480, 30, 8, "#5a3a26")
    person(c, 1450, 700, "maya", "sitphone", "neutral", t, 1.1, face=-1, look=(-0.5, 0.5))
    thought_bubbles(c, 540, 380, 640, 260, t)
    with xf(c, 760, 180):
        soft(c, 0, 0, 120, "#ff7a8a", 0.3, 40)
        c.drawCircle(0, 0, 100, P("#fff2d6"))
        heart(c, 0, 0, 50, "#ff6a8a")
    lower(c, t, 189.9, "THE LOVESICK", "Energy to approach: low", "#ff7a8a", dur=4.0)


def s_mindmoves(c, t):
    a = 193.9
    cam(c, push(t, a, 199.7, 1.0, 1.04), 960, 560, t)
    # a road to a finish line; the mind (golden ghost) runs ahead, the body stays at the start
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#1a2236", "#0b0f18"]))
    c.drawPath(poly([(860, 420), (1060, 420), (1700, H), (220, H)]), P("#2b3245"))
    for i in range(8):
        y0 = 440 + (i * 90 + ((t * 0) % 90))
        k = (y0 - 420) / 660
        w_ = 6 + 20 * k
        rrect(c, 960 - w_ / 2, y0, w_, 30 * (0.3 + k), 4, "#e8e2d6", 0.6)
    # finish line + banner
    rrect(c, 820, 330, 280, 70, 8, GOLD)
    dtext(c, "FINISH", 960, 382, 54, "#2a1d16", "bebas", track=0.2)
    line(c, 830, 400, 830, 440, "#e8e2d6", 6)
    line(c, 1090, 400, 1090, 440, "#e8e2d6", 6)
    for i in range(10):
        c.drawRect(skia.Rect(860 + i * 20, 420, 870 + i * 20, 430), P("#ffffff" if i % 2 else "#000000"))
    # body at the start line
    person(c, 960, 830, "leo", "stand", "dreamy", t, 1.0, face=1, look=(0, -1))
    # the mind leaves early and celebrates
    k = ease_out(at(t, 196.3, 1.6))
    if t > 196.0:
        gx, gy, gs = 960, lerp(830, 420, k), lerp(1.0, 0.25, k)
        if k < 0.98:
            walker_person(c, gx, gy, "leo", t, gs, run=True, freq=1.5, expr="bliss", rim=GOLD, alpha=0.55,
                          tint_col=GOLD, tint_a=0.6)
        else:
            person(c, gx, gy - 10 * abs(math.sin(t * 6)), "leo", "cheer", "bliss", t, gs, rim=GOLD, alpha=0.6,
                   tint_col=GOLD, tint_a=0.6)
            for i in range(6):
                sparkle(c, 960 + math.cos(i + t * 2) * 90, 350 + math.sin(i + t * 2) * 40, 12, GOLD)
    kword(c, t, 196.34, "THE MIND MOVES IN EARLY", 960, 170, 70, GOLD, style="rise", track=0.08)


def s_relax(c, t):
    a = 199.6
    cam(c, push(t, a, 205.7, 1.0, 1.06), 960, 560, t)
    bg(c, "living", 9)
    rrect(c, 560, 620, 800, 200, 80, "#6a5aa0")
    person(c, 960, 680, "leo", "sitslump", "bliss", t, 1.15, face=0.6, tilt=-8, chair=False)
    for i in range(3):
        k = ((t - a) * 0.5 + i / 3) % 1.0
        p = skia.Path()
        p.addArc(skia.Rect(960 - 200 - k * 300, 420 - 120 - k * 200, 960 + 200 + k * 300, 420 + 120 + k * 200),
                 200, 140)
        c.drawPath(p, P(GOLD, 6, (1 - k) * 0.6))
    for i, (lab, v, col, st) in enumerate((("RELIEF", 1.0, GOLD, 200.0), ("WORK DONE", 0.0, COOL, 203.7))):
        y = 260 + i * 120
        k = ease_out(at(t, st, 0.8))
        with xf(c, 1330, y, alpha=clamp(k * 3)):
            dtext(c, lab, -230, 14, 46, col, "bebas", "left", track=0.1)
            rrect(c, -20, -16, 400, 32, 16, "#2a2f3a")
            if v * k > 0.01:
                rrect(c, -20, -16, 400 * v * k, 32, 16, col)
            dtext(c, f"{int(v * k * 100)}%", 420, 14, 46, col, "bebas", "left")
    kword(c, t, 202.6, "BEFORE ANY WORK", 960, 980, 70, "#f2ead6", style="rise", track=0.12)


def s_salary(c, t):
    a = 205.6
    cam(c, push(t, a, 217.1, 1.0, 1.05), 960, 560, t)
    bg(c, "bedroom", 9)
    person(c, 760, 700, "leo", "sitthink" if t < 213 else "hold", "dreamy" if t < 213 else "bliss", t, 1.15,
           face=1, look=(0.6, -1))
    kword(c, t, 205.9, "“THE HARD PART IS OVER”", 960, 150, 64, GOLD, "bebas", style="type", track=0.08,
          end=209.0)
    thought_bubbles(c, 860, 380, 1000, 300, t, clamp((t - 209.0) * 2))
    items = [(210.56, "BUSINESS"), (211.62, "BOOK"), (212.7, "BODY")]
    for i, (st, lab) in enumerate(items):
        k = back_out(at(t, st - 0.2, 0.4))
        if k <= 0:
            continue
        x = 1100 + i * 260
        y = 260 + (i % 2) * 60
        with xf(c, x, y, k * (1 - 0.3 * at(t, 213.0, 0.5))):
            soft(c, 0, 0, 120, GOLD, 0.3, 40)
            c.drawCircle(0, 0, 100, P("#fff2d6"))
            if i == 0:
                rrect(c, -60, -30, 120, 80, 6, "#c9785c")
                c.drawPath(poly([(-70, -30), (70, -30), (55, -60), (-55, -60)]), P("#d14a3a"))
            elif i == 1:
                rrect(c, -45, -60, 90, 120, 6, "#3d6f9a")
                dtext(c, "BOOK", 0, 12, 34, "#ffffff", "bebas")
            else:
                c.drawCircle(0, -40, 18, P(INK))
                c.drawPath(poly([(-50, -15), (50, -15), (30, 55), (-30, 55)]), P(INK))
                c.drawCircle(-55, -10, 18, P(INK))
                c.drawCircle(55, -10, 18, P(INK))
            dtext(c, "FINISHED " + lab, 0, 150, 34, "#f2ead6", "bebas", track=0.1)
    if t > 213.0:
        k = ease_out(at(t, 213.0, 0.9))
        payslip(c, lerp(1500, 980, k), lerp(-150, 520, k), 1.0, lerp(-30, -6, k))
        for i in range(10):
            ct = (t - 213.6 - i * 0.18)
            if ct > 0:
                cy = 200 + ct * 700
                if cy < 760:
                    coin(c, 860 + (i * 47) % 200, cy, 26)
        kword(c, t, 214.18, "A SALARY OF SATISFACTION", 960, 160, 70, GOLD, style="rise", track=0.08)
        kword(c, t, 215.52, "IN ADVANCE", 960, 960, 80, "#f2ead6", style="slam", track=0.12)


def s_salreal(c, t):
    a = 217.0
    for side in (0, 1):
        c.save()
        clip_half(c, side, seed=12)
        bg(c, "bedroom", 10)
        x = 480 if side == 0 else 1440
        if side == 0:
            payslip(c, x, 480, 1.2)
            for i in range(6):
                coin(c, x - 150 + i * 60, 700 + (i % 2) * 20, 30)
            if t > 218.0:
                check_mark(c, x, 860, 1.0, GREEN, prog=clamp((t - 218.0) * 3))
        else:
            with xf(c, x, 560, alpha=0.55):
                eff = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6,
                                 PathEffect=skia.DashPathEffect.Make([24, 16], (t * 40) % 40))
                eff.setColor(C("#9aa3ad"))
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-230, -300, 460, 320), 14, 14), eff)
                c.drawPath(poly([(-260, 40), (260, 40), (290, 70), (-290, 70)]), eff)
            if t > 219.8:
                cross_mark(c, x, 860, 1.0 * back_out(at(t, 219.82, 0.3)), RED)
        c.restore()
    jagged_split(c, seed=12)
    kword(c, t, 217.42, "THE SALARY IS REAL", 480, 150, 64, GOLD, style="rise", track=0.06)
    kword(c, t, 218.98, "THE WORK IS NOT", 1440, 150, 64, "#f2ead6", style="rise", track=0.06)


def s_pleasant(c, t):
    a = 222.4
    cam(c, push(t, a, 228.7, 1.0, 1.05), 960, 540, t)
    fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, W * 0.7, ["#1e150d", "#070504"]))
    kword(c, t, 223.5, "PLEASANT", 960, 300, 150, GOLD, style="pop", track=0.06)
    kword(c, t, 224.34, "& EXPENSIVE", 960, 450, 120, RED, style="pop", track=0.06)
    if t > 225.4:
        # two pay slots: fantasy filled, the second one a mystery
        for i in range(2):
            k = back_out(at(t, 225.54 + i * 1.0, 0.4))
            x = 700 + i * 520
            with xf(c, x, 760, max(0.001, k)):
                rrect(c, -200, -130, 400, 260, 26, "#16120e")
                rrect(c, -200, -130, 400, 260, 26, GOLD if i == 0 else "#9aa3ad", stroke=5)
                if i == 0:
                    with xf(c, 0, -10, 0.6):
                        soft(c, 0, 0, 120, GOLD, 0.3, 40)
                        c.drawCircle(0, 0, 100, P("#fff2d6"))
                        sparkle(c, 0, 0, 40, GOLD)
                    dtext(c, "WAY #1: FANTASY", 0, 110, 40, GOLD, "bebas", track=0.08)
                else:
                    dtext(c, "?", 0, 50, 180, "#9aa3ad", "bebas")
                    dtext(c, "WAY #2", 0, 110, 40, "#9aa3ad", "bebas", track=0.08)
        kword(c, t, 226.62, "GETTING PAID EARLY", 960, 580, 50, "#f2ead6", style="rise", track=0.14)


def s_host3(c, t):
    host_shot(c, t, 228.6, ("sittalk", "point", "sittalk"), period=0.8, zoom=1.06, side=-1)
    kword(c, t, 229.34, "A SECOND WAY", 1350, 420, 110, GOLD, style="pop", track=0.06)
    kword(c, t, 230.52, "YOU DID IT TODAY", 1350, 540, 70, "#f2ead6", style="rise", track=0.08)


def s_ch2(c, t):
    chapter(c, t, 230.95, "TWO", "THE ANNOUNCEMENT", 232.55)


# ================================================================= CHAPTER 2: ANNOUNCING
def s_gol(c, t):
    a = 232.5
    cam(c, push(t, a, 243.5, 1.0, 1.05), 960, 540, t)
    if t < 239.7:
        bg(c, "labroom", 8)
        person(c, 1250, 560, "gol", gesture(t, a, ["explain", "present", "stand"], 1.7), "focus", t, 1.15, face=-1,
               look=(-0.5, 0))
        year_badge(c, t, 233.08, "2009", 520, 330, GOLD, 120)
        lower(c, t, 233.64, "PETER GOLLWITZER", "Psychologist  ·  & colleagues", GOLD, dur=4.6)
        if t > 236.1:
            for i in range(4):
                k = back_out(at(t, 236.16 + i * 0.12, 0.35))
                with xf(c, 330 + i * 130, 520, max(0.001, k)):
                    rrect(c, -50, -60, 100, 120, 10, "#f2efe6")
                    for j in range(4):
                        line(c, -32, -36 + j * 22, 30, -36 + j * 22, "#9aa3ad", 4)
        kword(c, t, 238.28, "AN AWKWARD QUESTION", 520, 720, 54, GOLD, style="type", track=0.12)
    else:
        fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, W * 0.7, ["#1e150d", "#070504"]))
        megaphone(c, 960, 280, 1.2, -12, t, 1.0)
        quote(c, t, 239.8, 242.6, 960, 640, 1500, 84, "#f6efe2", GOLD, "playb")


def s_lawyer(c, t):
    a = 243.4
    cam(c, push(t, a, 251.5, 1.0, 1.05), 960, 560, t)
    bg(c, "bedroom", 9)
    person(c, 640, 680, "leo", "stand" if t < 246.2 else "proud" and "point_up", "focus" if t < 246.2 else "proud",
           t, 1.1, face=1, look=(0.6, -0.6))
    k = at(t, 246.2, 0.6)
    if k > 0:
        # the identity: his future self as a lawyer, glowing
        person(c, 1140, 640, "boss", "present", "proud", t, 1.1, face=-1, alpha=0.5 * ease_out(k), rim=GOLD,
               tint_col=GOLD, tint_a=0.35)
        kword(c, t, 246.36, "IDENTITY: LAWYER", 1140, 170, 64, GOLD, style="pop", track=0.1)
    if t > 249.0:
        for i in range(4):
            kk = back_out(at(t, 249.22 + i * 0.15, 0.35))
            law_book(c, 330 + i * 140, 980 - i * 0, 0.6 * max(0.001, kk), -5 + i * 3,
                     ["#7a2a2a", "#2a4a7a", "#2a6a4a", "#6a4a2a"][i])
        kword(c, t, 249.44, "BEHAVIOUR: READ LAW JOURNALS", 1300, 960, 50, "#f2ead6", style="rise", track=0.08)
    loc_tag(c, t, 243.6, "PARTICIPANTS HELD IDENTITY GOALS", 247.5, y=90)


def s_noticed(c, t):
    a = 251.4
    if t < 254.0:
        cam(c, push(t, a, 254.0, 1.0, 1.06), 960, 560, t)
        bg(c, "cafe", 8)
        rrect(c, 560, 700, 800, 30, 8, "#5a3a26")
        tk = (0.35 + 0.35 * abs(math.sin(t * 11)), 0.4) if t < 253.0 else None
        person(c, 700, 700, "leo", gesture(t, a, ["sittalk", "explain"], 0.7, sit=True), "talk" if tk else "proud", t, 1.05,
               face=1, talk=tk)
        clap = abs(math.sin(t * 9)) if t > 252.3 else 0
        ps = mix_pose("sit", "cheer", clap * 0.6)
        ps["fl"], ps["bl"] = (85, -85), (80, -80)
        pz = mix_pose("sittalk", "shake", clap if t > 252.2 else 0)
        pz["fl"], pz["bl"] = (85, -85), (80, -80)
        pz["_name"] = "sit_shake"
        person(c, 1150, 700, "sam", ps, "happy", t, 1.05, face=-1)
        person(c, 1420, 700, "zed", pz, "smile", t, 1.0, face=-1)
        if t > 252.26:
            for i in range(6):
                kk = ((t - 252.26) * 0.9 + i * 0.17) % 1.0
                heart(c, 1100 + i * 70, 520 - kk * 300, 22 * (1 - kk * 0.4), "#ff6a8a", a=1 - kk)
            tag2(c, t, 252.26, "NOTICED", 1280, 220, "#ff6a8a", 50)
    else:
        for side in (0, 1):
            c.save()
            clip_half(c, side, seed=14)
            bg(c, "bedroom", 9)
            x = 480 if side == 0 else 1440
            rrect(c, x - 280, 720, 560, 30, 8, "#3a2c40")
            if side == 0:
                person(c, x - 60, 720, "leo", "sitphone", "proud", t, 1.0, face=1, look=(0.4, 0.4))
                law_book(c, x + 140, 670, 0.6, -80, "#7a2a2a")
                for i in range(3):
                    kk = ((t * 0.7 + i * 0.33) % 1.0)
                    heart(c, x + 20 + i * 40, 420 - kk * 120, 16, "#ff6a8a", a=1 - kk)
                bar = 0.3
            else:
                person(c, x - 60, 720, "leo", "sitdesk", "focus", t, 1.0, face=1, look=(0.5, 0.6))
                with xf(c, x + 120, 690, 0.6):
                    rrect(c, -110, -70, 220, 140, 6, "#f2efe6")
                    line(c, 0, -70, 0, 70, "#cdbf9f", 4)
                bar = 0.85
            k = ease_out(at(t, 255.16, 1.0))
            with xf(c, x, 220):
                dtext(c, "EFFORT", 0, -40, 40, "#d8cfbf", "bebas", track=0.14)
                rrect(c, -220, -10, 440, 30, 15, "#2a2f3a")
                rrect(c, -220, -10, 440 * bar * k, 30, 15, RED if side == 0 else GREEN)
            c.restore()
        jagged_split(c, seed=14)
        tag2(c, t, 254.1, "NOTICED", 480, 90, "#ff6a8a", 40)
        tag2(c, t, 256.56, "NOBODY NOTICED", 1440, 90, COOL, 40)


def s_week(c, t):
    a = 257.6
    cam(c, push(t, a, 265.1, 1.0, 1.04), 960, 540, t)
    info_board(c, t, "#0f1117", "#06070a")
    if t < 261.7:
        kword(c, t, 258.16, "REAL LIFE: ONE WEEK", 960, 170, 70, "#f2ead6", style="rise", track=0.12)
        days = "MTWTFSS"
        for row, (lab, pat, col) in enumerate((("NOTICED", [1, 0, 0, 1, 0, 0, 0], "#ff6a8a"),
                                                ("NOT NOTICED", [1, 1, 0, 1, 1, 1, 0], COOL))):
            y = 450 + row * 260
            dtext(c, lab, 420, y + 20, 50, col, "bebas", "right", track=0.08)
            for i in range(7):
                x = 520 + i * 160
                rrect(c, x, y - 60, 130, 130, 16, "#1a1e28")
                dtext(c, days[i], x + 65, y - 72, 30, "#8a8f9a", "SemiBold")
                if pat[i] and t > 258.6 + i * 0.25:
                    check_mark(c, x + 65, y + 5, 0.7, col, prog=clamp((t - 258.6 - i * 0.25) * 4))
    else:
        kword(c, t, 261.9, "IN THE LAB", 960, 170, 70, "#f2ead6", style="rise", track=0.12)
        kword(c, t, 263.1, "FEWER CHANCES TAKEN", 960, 960, 64, RED, style="rise", track=0.08)
        # chances float by; Leo catches only one
        for i in range(7):
            x = ((t - 261.8) * 380 + i * 300) % (W + 300) - 150
            y = 500 + math.sin(i * 2 + t) * 60
            grabbed = i == 2
            col = GREEN if grabbed else "#9aa3ad"
            with xf(c, x, y):
                rrect(c, -50, -70, 100, 140, 10, col, 0.25 if not grabbed else 0.8)
                rrect(c, -50, -70, 100, 140, 10, col, stroke=4)
                c.drawCircle(30, 0, 8, P(col))
        person(c, 960, 640, "leo", "phone", "bored", t, 0.9, face=1, look=(-0.6, -0.4))


def s_commit(c, t):
    a = 265.0
    cam(c, push(t, a, 269.7, 1.0, 1.04), 960, 540, t)
    info_board(c, t, "#0f1117", "#06070a")
    for i, (lab, v, eff, col, st) in enumerate((("STRONGLY COMMITTED", 0.9, True, GOLD, 266.18),
                                                 ("WEAKLY COMMITTED", 0.25, False, "#9aa3ad", 268.42))):
        y = 380 + i * 330
        k = ease_out(at(t, st, 0.8))
        if k <= 0:
            continue
        dtext(c, lab, 300, y, 64, col, "bebas", "left", a=clamp(k * 2), track=0.06)
        rrect(c, 300, y + 40, 800, 40, 20, "#2a2f3a")
        rrect(c, 300, y + 40, 800 * v * k, 40, 20, col)
        x = 1450
        if eff:
            tag2(c, t, st + 0.6, "EFFECT FOUND", x, y + 40, RED, 48)
        else:
            tag2(c, t, st + 0.4, "NO EFFECT", x, y + 40, "#9aa3ad", 48)


def s_premature(c, t):
    a = 269.6
    cam(c, push(t, a, 276.7, 1.0, 1.08), 960, 560, t)
    bg(c, "bedroom", 10)
    tint(c, "#000000", 0.3)
    # mirror: the reflection is already the lawyer
    rrect(c, 1020, 160, 560, 760, 280, "#c9b48a", stroke=24)
    c.save()
    c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(1032, 172, 536, 736), 268, 268), skia.ClipOp.kIntersect,
                True)
    fill_shader(c, skia.Rect(1032, 172, 1568, 908), linear(0, 172, 0, 908, ["#3a3050", "#1a1428"]))
    k = ease_out(at(t, 272.4, 1.2))
    person(c, 1300, 600, "leo", "stand", "neutral", t, 1.05, face=-1, alpha=1 - k)
    person(c, 1300, 600, "boss", "proud" and "present", "proud", t, 1.05, face=-1, alpha=k, rim=GOLD)
    if k > 0.3:
        for i in range(6):
            kk = ((t * 0.5 + i / 6) % 1.0)
            heart(c, 1150 + i * 60, 700 - kk * 400, 20, "#ff6a8a", a=(1 - kk) * k)
    soft(c, 1300, 300, 200, GOLD, 0.15 * k, 60)
    c.restore()
    person(c, 640, 640, "leo", "stand", "proud" if t > 272.5 else "neutral", t, 1.1, face=1, look=(1, -0.3))
    kword(c, t, 272.96, "PREMATURE", 640, 160, 90, GOLD, style="slam", track=0.1)
    kword(c, t, 273.92, "“I'M ALREADY THAT PERSON”", 640, 260, 46, "#f2ead6", "play", style="type")


def s_gap(c, t):
    a = 276.6
    cam(c, push(t, a, 281.0, 1.0, 1.06), 960, 560, t)
    info_board(c, t, "#0f1117", "#06070a")
    # a gap labelled EFFORT; hearts/likes pour in and fill it - but they're not effort
    c.drawRect(skia.Rect(260, 640, 760, 760), P("#3a3f4a"))
    c.drawRect(skia.Rect(1160, 640, 1660, 760), P("#3a3f4a"))
    eff = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6,
                     PathEffect=skia.DashPathEffect.Make([24, 16], 0))
    eff.setColor(C(GREEN))
    c.drawRect(skia.Rect(760, 640, 1160, 900), eff)
    dtext(c, "EFFORT-SHAPED GAP", 960, 960, 44, GREEN, "bebas", track=0.12)
    fill = ease_out(at(t, 277.2, 2.0))
    rnd = random.Random(3)
    for i in range(int(60 * fill)):
        x = 790 + rnd.uniform(0, 340)
        y = 880 - rnd.uniform(0, 240 * fill)
        heart(c, x, y, 18, "#ff6a8a", 0.85)
    for i in range(8):
        ct = (t - 277.2 - i * 0.2)
        if 0 < ct < 1.0:
            heart(c, 960 + math.sin(i * 3) * 120, 200 + ct * 500, 26, "#ff6a8a")
    kword(c, t, 276.8, "ATTENTION FILLED THE GAP", 960, 200, 70, "#ff8a9a", style="rise", track=0.08)
    kword(c, t, 278.54, "ONLY EFFORT SHOULD FILL", 960, 300, 60, GREEN, style="rise", track=0.08)
    person(c, 400, 470, "leo", "shrug", "worried", t, 0.75)


def s_host4(c, t):
    host_shot(c, t, 280.9, ("sittalk", "explain", "sittalk", "open"), period=1.3)
    k = back_out(at(t, 282.6, 0.4))
    if k > 0:
        with xf(c, 470, 400, k):
            c.drawPath(poly([(0, -140), (150, 120), (-150, 120)]), P(GOLD))
            c.drawPath(poly([(0, -100), (115, 95), (-115, 95)]), P("#2a1d16"))
            dtext(c, "!", 0, 80, 150, GOLD, "bebas")
    kword(c, t, 283.5, "A RISK", 470, 680, 100, GOLD, style="pop", track=0.06)
    kword(c, t, 283.8, "NOT A RULE", 470, 790, 70, "#f2ead6", style="rise", track=0.1)


def s_friend(c, t):
    a = 285.3
    cam(c, push(t, a, 289.9, 1.0, 1.05), 960, 560, t)
    bg(c, "cafe", 8)
    rrect(c, 560, 700, 800, 30, 8, "#5a3a26")
    talking = t < 288.4
    tk = (0.35 + 0.4 * abs(math.sin(t * 12)), 0.3) if talking else None
    tired = clamp((t - 288.4) / 0.6)
    person(c, 760, 700, "leo", gesture(t, a, ["sittalk", "explain", "open"], 0.6, sit=True) if talking else "sitslump",
           "talk" if talking else "tired", t, 1.05, face=1, talk=tk, tilt=8 * tired)
    person(c, 1220, 700, "sam", "sitthink", "smile", t, 1.05, face=-1)
    if talking:
        for i in range(3):
            kk = ((t * 1.2 + i / 3) % 1.0)
            with xf(c, 900 + kk * 100, 380 - kk * 120, alpha=1 - kk):
                sparkle(c, 0, 0, 22, GOLD)
    if tired > 0:
        for i in range(3):
            c.drawCircle(700 + i * 20, 300 + ((t * 80 + i * 30) % 80), 7, P("#9fd0ff", a=0.8))
        battery(c, 1550, 420, 0.45, 0.15, t)
    # clock races to evening
    hrs = 12 + 7 * ease_out(clamp((t - a) / 4.0))
    clock_face(c, 300, 260, 0.6, hrs, (hrs % 1) * 60)
    kword(c, t, 288.9, "A FULL DAY'S WORK", 960, 980, 70, "#f2ead6", style="slam", track=0.1)


def s_ch3(c, t):
    chapter(c, t, 289.75, "THREE", "THE FEAR", 291.25, "#ff6a5a")


# ================================================================= CHAPTER 3: FEAR
def s_fear(c, t):
    a = 291.2
    cam(c, push(t, a, 303.0, 1.0, 1.08), 960, 560, t, shake=0.15 if t > 298.3 else 0)
    bg(c, "void", 0)
    # big dream -> big tasks -> fear
    dk = back_out(at(t, 294.72, 0.6))
    if dk > 0 and t < 299.1:
        with xf(c, 560, 330, dk):
            soft(c, 0, 0, 190, GOLD, 0.35, 60)
            c.drawCircle(0, 0, 160, P("#fff2d6"))
            trophy(c, 0, 60, 0.7)
        kword(c, t, 294.72, "BIG DREAMS", 560, 600, 70, GOLD, style="rise", track=0.1, end=299.0)
    tk = at(t, 296.2, 0.8)
    if tk > 0 and t < 299.1:
        line(c, 720, 330, 1180, 330 + 0 * tk, "#d8cfbf", 6, tk)
        for i in range(10):
            kk = back_out(at(t, 296.22 + i * 0.07, 0.3))
            col_ = i % 3
            row = i // 3
            with xf(c, 1240 + col_ * 150 - row * 0, 520 - row * 120, max(0.001, kk)):
                rrect(c, -65, -55, 130, 110, 8, "#8a6a4a")
                line(c, -65, -10, 65, -10, "#6a4a2a", 6)
        kword(c, t, 296.42, "BIG TASKS", 1390, 650, 70, "#d8cfbf", style="rise", track=0.1, end=299.0)
    mk = ease_out(at(t, 297.6, 1.2))
    if mk > 0:
        shadow_monster(c, 960, 640 - 80 * mk, 0.6 + 0.5 * mk, t, a=mk, eyes=clamp((t - 298.2) * 2))
        person(c, 960, 760, "leo", "headhold" if t > 299.1 else "stand", "scared", t, 0.85, rim="#ff6a5a",
               look=(0, -1))
        kword(c, t, 298.34, "FEAR", 960, 200, 160, "#ff5a4f", style="slam", track=0.12, end=299.1)
    kword(c, t, 299.18, "FEAR OF FAILING", 960, 200, 90, "#ff8a7a", style="slam", track=0.1, end=300.3)
    if t > 300.4:
        kword(c, t, 300.44, "FEAR OF BEING", 960, 170, 74, "#ff8a7a", style="rise", track=0.1)
        kword(c, t, 301.76, "ORDINARY", 960, 290, 130, "#f2ead6", style="slam", track=0.14)
        # a crowd of identical grey figures closes in
        k = ease_out(at(t, 301.0, 1.4))
        for i in range(6):
            sd = -1 if i < 3 else 1
            x = 960 + sd * (300 + (i % 3) * 170) * (1.4 - 0.4 * k)
            person(c, x, 820, "zed", "stand", "deadpan", t, 0.6, rim="#5a5a5a", tint_col="#6a6a6a", tint_a=0.9,
                   alpha=k, face=-sd)
    grade(c, "fear", 0.4)


def s_sirois(c, t):
    a = 302.9
    cam(c, push(t, a, 312.7, 1.0, 1.04), 960, 540, t)
    bg(c, "labroom", 9)
    tint(c, "#000000", 0.35)
    lower(c, t, 303.3, "FUSCHIA SIROIS & TIM PYCHYL", "Procrastination researchers", GOLD, dur=4.6)
    if t < 308.3:
        person(c, 760, 600, "sir", gesture(t, a, ["explain", "stand"], 1.6), "focus", t, 1.1, face=1)
        person(c, 1160, 600, "pyc", gesture(t, a, ["stand", "present"], 1.8), "smile", t, 1.1, face=-1)
    # TIME vs MOOD
    k1 = back_out(at(t, 308.44, 0.5))
    k2 = back_out(at(t, 309.6, 0.5))
    if k1 > 0:
        clock_face(c, 620, 470, 0.9 * k1, (t * 2) % 12, (t * 120) % 60)
        dtext(c, "MANAGING TIME", 620, 720, 54, "#d8cfbf", "bebas", a=clamp(k1), track=0.1)
        if t > 309.4:
            cross_mark(c, 620, 470, 1.6 * back_out(at(t, 309.34, 0.3)), RED)
    if k2 > 0:
        with xf(c, 1300, 470, k2):
            c.drawCircle(0, 0, 150, P(GOLD))
            c.drawCircle(-50, -30, 18, P("#2a1d16"))
            c.drawCircle(50, -30, 18, P("#2a1d16"))
            m = 40 * math.sin(t * 2)
            p = skia.Path()
            p.moveTo(-60, 50)
            p.quadTo(0, 50 + m, 60, 50)
            c.drawPath(p, P("#2a1d16", 12))
        dtext(c, "MANAGING MOOD", 1300, 720, 54, GOLD, "bebas", a=clamp(k2), track=0.1)
        if t > 310.2:
            check_mark(c, 1300, 860, 1.0, GREEN, prog=clamp((t - 310.2) * 3))


def s_quote2(c, t):
    a = 312.6
    cam(c, push(t, a, 318.0, 1.0, 1.05), 960, 540, t, drift=0.4)
    fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, W * 0.75, ["#1e150d", "#070504"]))
    bokeh(c, t, GOLD, 18, seed=13, a=0.1, speed=8)
    quote(c, t, 312.9, 317.0, 960, 470, 1450, 84, "#f6efe2", GOLD, "play", lead="“")
    kword(c, t, 316.5, "— TIM PYCHYL", 960, 820, 44, GOLD, "SemiBold", style="rise", track=0.3)


def s_seesaw(c, t):
    a = 317.9
    cam(c, push(t, a, 325.0, 1.0, 1.04), 960, 540, t)
    info_board(c, t, "#0f1117", "#06070a")
    year_badge(c, t, 318.54, "2013", 960, 180, GOLD, 100, end=321.0)
    tilt = -14 * ease_out(at(t, 321.6, 1.2)) + 2 * math.sin(t * 2)
    with xf(c, 960, 700):
        c.drawPath(poly([(0, -10), (-70, 120), (70, 120)]), P("#d8cfbf"))
        with xf(c, 0, -10, rot=tilt):
            rrect(c, -600, -16, 1200, 32, 12, "#d8cfbf")
            with xf(c, -460, -16, rot=-tilt):
                k = back_out(at(t, 321.62, 0.4))
                with xf(c, 0, -110, max(0.001, k)):
                    rrect(c, -170, -100, 340, 200, 24, GOLD)
                    dtext(c, "SHORT-TERM", 0, -14, 52, "#2a1d16", "bebas", track=0.06)
                    dtext(c, "MOOD REPAIR", 0, 50, 52, "#2a1d16", "bebas", track=0.06)
            with xf(c, 460, -16, rot=-tilt):
                k = back_out(at(t, 323.5, 0.4))
                with xf(c, 0, -90, max(0.001, k * 0.8)):
                    rrect(c, -170, -100, 340, 200, 24, COOL)
                    dtext(c, "LONG-TERM", 0, -14, 52, "#0b1018", "bebas", track=0.06)
                    dtext(c, "GOALS", 0, 50, 52, "#0b1018", "bebas", track=0.06)
    kword(c, t, 323.08, "AHEAD OF", 960, 330, 64, "#f2ead6", style="rise", track=0.12)


def s_anxious(c, t):
    a = 324.9
    cam(c, push(t, a, 334.6, 1.0, 1.06), 960, 560, t)
    bg(c, "bedroom", 8)
    rrect(c, 300, 720, 1320, 40, 10, "#3a2c40")
    anx = clamp((t - 326.0) / 0.5)
    phone_t = t > 327.1
    person(c, 760, 720, "leo", "sitphone" if phone_t else "sitdesk", "worried" if t < 329.4 else "bored", t, 1.05,
           face=1, look=(0.5, 0.4) if not phone_t else (0.2, 0.3), hold=(lambda cc, hx, hy: phone(cc, hx + 10, hy - 30,
                                                                                                  0.8, -10, "#9fd0ff", 0.4))
           if phone_t else None)
    laptop(c, 1240, 720, 0.85, t, blank=True)
    if anx > 0 and t < 329.4:
        # anxiety scribble above his head
        pth = skia.Path()
        rnd = random.Random(int(t * 12))
        pth.moveTo(700, 220)
        for i in range(14):
            pth.lineTo(640 + rnd.uniform(0, 160), 170 + rnd.uniform(0, 90))
        c.drawPath(pth, P("#ff6a5a", 5, anx))
        tag2(c, t, 326.1, "ANXIOUS", 760, 120, RED, 44, end=329.3)
    # the three escapes
    if t > 329.4:
        k = back_out(at(t, 329.54, 0.4))
        with xf(c, 360, 420, max(0.001, k)):
            phone_feed(c, 0, 0, 0.9, t, (t - 329.5) * 600)
        tag2(c, t, 329.54, "SCROLLING", 360, 690, "#9fd0ff", 40)
    if t > 330.4:
        for i in range(5):
            k = back_out(at(t, 330.44 + i * 0.12, 0.3))
            with xf(c, 1100 + i * 40, 230 + i * 40, max(0.001, k)):
                rrect(c, -150, -90, 300, 180, 12, "#e8ecf2")
                rrect(c, -150, -90, 300, 30, 12, "#b8c2d2")
                for j in range(3):
                    rrect(c, -120, -40 + j * 34, 200 - j * 30, 12, 6, "#a0a8b8")
        tag2(c, t, 330.44, "RESEARCHING", 1260, 520, "#e8ecf2", 40, end=331.5)
    if t > 331.5:
        v = 1 + int(4 * clamp((t - 331.6) / 1.6))
        with xf(c, 1260, 380, back_out(at(t, 331.58, 0.3))):
            notebook(c, 0, 0, 0.55, t, ((t - 331.6) * 2.5) % 1.0 if t < 333.2 else 0, ["PLAN"])
        tag2(c, t, 331.58, f"PLAN  v{v}", 1260, 560, GOLD, 44)


def s_sitdream(c, t):
    a = 334.5
    if t < 338.5:
        cam(c, push(t, a, 338.5, 1.0, 1.06), 960, 560, t)
        bg(c, "bedroom", 9)
        person(c, 760, 720, "leo", "sitslump", "bliss", t, 1.1, face=1, tilt=-8)
        thought_bubbles(c, 860, 380, 1000, 300, t)

        def inner(cc):
            cc.save()
            cc.translate(-960, -540)
            set_dream(cc, t)
            person(cc, 960, 600, "leo", "cheer", "bliss", t, 1.2, rim="#fff2c4")
            trophy(cc, 960, 200, 0.7, ghost=True)
            cc.restore()
        with xf(c, 1340, 300, 0.55):
            dream_frame(c, 0, 0, 520, 300, t, inner, at(t, 335.3, 0.7))
        kword(c, t, 336.42, "THE DREAM THAT ALREADY WORKED", 960, 980, 54, GOLD, style="rise", track=0.08)
    else:
        for side in (0, 1):
            c.save()
            clip_half(c, side, seed=16)
            x = 480 if side == 0 else 1440
            if side == 0:
                set_dream(c, t)
                with xf(c, x, 540):
                    soft(c, 0, 0, 260, GOLD, 0.4, 70)
                    rrect(c, -150, -200, 300, 400, 14, "#3d6f9a")
                    dtext(c, "MY BOOK", 0, -60, 64, "#ffffff", "bebas", track=0.1)
                    dtext(c, "BESTSELLER", 0, 20, 40, GOLD, "bebas", track=0.2)
                    for i in range(5):
                        sparkle(c, -120 + i * 60, 150, 14, GOLD)
                grade(c, "dream", 0.6)
            else:
                bg(c, "bedroom", 10)
                tint(c, "#000000", 0.3)
                laptop(c, x, 700, 1.2, t, blank=True)
            c.restore()
        jagged_split(c, seed=16)
        tag2(c, t, 338.66, "IN YOUR HEAD", 480, 120, GOLD, 44)
        tag2(c, t, 341.96, "IN FRONT OF YOU", 1440, 120, "#e8ecf2", 44)
        if t > 343.9:
            k = ease_out(at(t, 343.96, 0.5))
            soft(c, 960, 540, 500 * k, GOLD, 0.25 * (1 - at(t, 345.0, 0.8)), 120)
            kword(c, t, 343.96, "RELIEF. NOW.", 960, 980, 100, "#fff2d6", style="slam", track=0.12)


def s_bill(c, t):
    a = 345.9
    if t < 347.9:
        cam(c, push(t, a, 348.0, 1.0, 1.08), 960, 560, t)
        bg(c, "living", 9)
        tint(c, "#000000", 0.25)
        # future self, greyer and tired, receives the bill
        person(c, 1060, 640, "leo", "hold", "tired", t, 1.15, face=-1, tint_col="#7a7f8a", tint_a=0.25,
               rim="#9aa3ad")
        k = ease_out(at(t, 346.12, 0.8))
        invoice(c, lerp(400, 880, k), lerp(-200, 470, k), 0.8, lerp(-40, -8, k))
        tag2(c, t, 346.82, "YOUR FUTURE SELF", 1060, 140, "#9aa3ad", 50)
    else:
        cam(c, push(t, 347.9, 356.1, 1.0, 1.04), 960, 540, t)
        info_board(c, t, "#0f1117", "#06070a")
        kword(c, t, 348.1, "META-ANALYSIS", 960, 160, 64, "#f2ead6", "bebas", style="type", track=0.2)
        # a timeline: PRESENT <-> FUTURE; procrastinator leans toward the present
        line(c, 260, 760, 1660, 760, "#d8cfbf", 6)
        dtext(c, "PRESENT", 420, 830, 60, GOLD, "bebas", track=0.1)
        dtext(c, "FUTURE", 1500, 830, 60, COOL, "bebas", track=0.1)
        lean = 14 * ease_out(at(t, 350.36, 0.8))
        person(c, 960, 590, "leo", "reach" if t > 351.2 else "stand", "neutral" if t < 354.6 else "sad", t, 1.0,
               face=-1, lean=lean, look=(-1, 0))
        if t > 354.6:
            # a raincloud of negative mood
            with xf(c, 900, 260, back_out(at(t, 354.68, 0.4))):
                for (dx, dy, r) in ((-60, 0, 60), (0, -30, 75), (70, 0, 60)):
                    c.drawCircle(dx, dy, r, P("#5a6070"))
                rain_drops(c, t, (-90, 40, 90, 200), 0.8, 10, seed=4)
            tag2(c, t, 354.98, "NEGATIVE MOOD", 1300, 300, "#9aa3ad", 40)


def s_loop(c, t):
    a = 356.0
    cam(c, push(t, a, 365.2, 1.0, 1.05), 960, 540, t)
    info_board(c, t, "#13101a", "#07060a")
    kword(c, t, 356.5, "THE LOOP CLOSES", 960, 130, 70, "#f2ead6", style="rise", track=0.12)
    nodes = [("DREAM", 358.6, GOLD, True, (960, 330)), ("TELL", 360.28, "#ff8a9a", True, (1340, 700)),
             ("START", 362.2, COOL, False, (580, 700))]
    # loop arrows between the two good nodes (spinning)
    if t > 360.6:
        ang = (t - 360.6) * 2.4
        for i in range(10):
            u = (ang + i / 10 * 6.283) % 6.283
            x = 1150 + math.cos(u) * 260
            y = 515 + math.sin(u) * 230
            c.drawCircle(x, y, 9, P(GOLD, a=0.7))
    for lab, st, col, good, (x, y) in nodes:
        k = back_out(at(t, st, 0.45))
        if k <= 0:
            continue
        with xf(c, x, y, k):
            soft(c, 0, 0, 150, col, 0.2, 50)
            c.drawCircle(0, 0, 120, P("#10141a"))
            c.drawCircle(0, 0, 120, P(col, 7))
            dtext(c, lab, 0, -20, 58, col, "bebas", track=0.1)
            dtext(c, "FEELS GOOD" if good else "FEELS BAD", 0, 40, 34, "#d8cfbf", "bebas", track=0.1)
    if t > 364.2:
        k = back_out(at(t, 364.28, 0.4))
        with xf(c, 960, 960, k):
            dtext(c, "THE BRAIN PICKS THE FEELING", 0, 0, 64, "#f2ead6", "bebas", track=0.08)
        line(c, 580, 700, 580, 700, COOL, 1)
        if t > 364.5:
            cross_mark(c, 580, 700, 0.9, RED)


def s_ch4(c, t):
    chapter(c, t, 365.1, "FOUR", "THE FIX", 367.0, GREEN)


# ================================================================= CHAPTER 4: THE FIX
def s_host5(c, t):
    host_shot(c, t, 367.0, ("sittalk", "open", "point"), period=1.2, zoom=1.06)
    kword(c, t, 367.6, "DREAM LESS", 480, 400, 110, "#f2ead6", style="rise", track=0.08)
    strike(c, t, 368.1, 480, 360, 520, RED, 16)
    kword(c, t, 370.26, "DREAM SECOND", 480, 580, 120, GREEN, style="slam", track=0.08)


def s_contrast(c, t):
    a = 371.4
    gold_side = t < 376.6
    cam(c, push(t, a, 381.2, 1.0, 1.06), 960, 560, t, shake=0.4 if 376.5 < t < 376.9 else 0)
    if gold_side:
        set_dream(c, t)
        person(c, 960, 640, "leo", "cheer" if t > 375.3 else "stand", "bliss", t, 1.15, rim="#fff2c4")
        bokeh(c, t, "#ffffff", 18, seed=3, a=0.25)
        grade(c, "dream", 0.6)
        kword(c, t, 372.18, "MENTAL CONTRASTING", 960, 150, 90, "#ffffff", style="rise", track=0.1, end=374.2)
        kword(c, t, 374.34, "1 · PICTURE THE WISH", 960, 150, 80, "#ffffff", style="pop", track=0.08)
    else:
        bg(c, "bedroom", 8)
        rrect(c, 300, 720, 1320, 40, 10, "#3a2c40")
        person(c, 860, 720, "leo", "sitthink", "focus", t, 1.05, face=1, look=(0.6, 0.2))
        phone(c, 1200, 700, 0.8, 80, "#2b3a55")
        laptop(c, 1450, 720, 0.6, t, blank=True)
        grade(c, "cold", 0.5)
        flash(c, t, 376.6, "#cfe8ff", 0.35, 0.8)
        kword(c, t, 376.76, "2 · TURN TO REALITY", 960, 150, 80, COOL, style="slam", track=0.08)
        kword(c, t, 378.04, "NAME WHAT BLOCKS IT", 960, 990, 64, "#f2ead6", style="rise", track=0.1)


def s_obstacles(c, t):
    a = 380.9
    cam(c, push(t, a, 385.9, 1.0, 1.04), 960, 540, t)
    info_board(c, t, "#0f1117", "#06070a")
    obs = [("THE TIREDNESS", 381.26), ("THE DREAD", 383.18), ("THE PHONE ON THE DESK", 384.7)]
    for i, (lab, st) in enumerate(obs):
        k = back_out(at(t, st, 0.4))
        if k <= 0:
            continue
        x = 400 + i * 560
        with xf(c, x, 520, k):
            rrect(c, -230, -260, 460, 520, 30, "#161a22")
            rrect(c, -230, -260, 460, 520, 30, "#e8b04a", stroke=5)
            if i == 0:
                head_cu(c, 0, -40, "leo", "tired", t, 1.4)
                for j in range(3):
                    dtext(c, "z", 90 + j * 30, -130 - j * 40 - ((t * 30) % 20), 40 + j * 10, "#9fd0ff", "bebas")
            elif i == 1:
                for (dx, dy, r) in ((-60, -40, 60), (0, -70, 75), (70, -40, 60)):
                    c.drawCircle(dx, dy, r, P("#4a4f60"))
                rain_drops(c, t, (-90, 0, 90, 140), 0.8, 10, seed=6)
            else:
                phone(c, 0, -40, 1.4, 0, "#9fd0ff", 0.4)
                for j in range(3):
                    p = skia.Path()
                    p.addArc(skia.Rect(-80 - j * 25, -130 - j * 25, 80 + j * 25, 50 + j * 25), -60, 120)
                    c.drawPath(p, P("#9fd0ff", 4, 0.5 * (0.5 + 0.5 * math.sin(t * 8 - j))))
            dtext(c, lab, 0, 200, 40, "#e8b04a", "bebas", track=0.08)
    kword(c, t, 381.0, "OBSTACLES  (INSIDE YOU)", 960, 150, 60, "#e8b04a", style="rise", track=0.14)


def s_ifthen(c, t):
    a = 385.8
    cam(c, push(t, a, 394.5, 1.0, 1.04), 960, 560, t)
    if t < 389.5:
        bg(c, "labroom", 9)
        tint(c, "#000000", 0.35)
        person(c, 1250, 560, "gol", "present", "smile", t, 1.1, face=-1)
        lower(c, t, 386.0, "PETER GOLLWITZER", "Implementation intentions", GOLD, dur=3.4)
        kword(c, t, 388.02, "IF", 500, 450, 220, GOLD, style="slam")
        kword(c, t, 388.4, "THEN", 760, 450, 220, GREEN, style="slam")
        kword(c, t, 388.74, "PLAN", 630, 620, 110, "#f2ead6", style="rise", track=0.2)
    else:
        bg(c, "bedroom", 8)
        rrect(c, 300, 720, 1320, 40, 10, "#3a2c40")
        mins = 50 + 10 * ease_out(at(t, 389.8, 0.8))
        clock_face(c, 330, 330, 0.75, 6 + mins / 60.0, mins % 60, glow_a=0.4 if mins >= 59.9 else 0.0)
        typing = t > 391.7
        person(c, 860, 720, "leo", "sitdesk" if typing else "sit", "focus", t, 1.05, face=1, look=(0.6, 0.3))
        laptop(c, 1250, 720, 0.85, t, typing=typing, words=clamp((t - 392.4) / 2.0))
        if typing and int(t * 8) % 2 == 0:
            pass
        kword(c, t, 389.6, "IF  7 PM  ON A WEEKDAY", 960, 140, 66, GOLD, style="type", track=0.08)
        kword(c, t, 391.14, "THEN  OPEN THE DOC  +  WRITE 20 MIN", 960, 990, 58, GREEN, style="type", track=0.06)
        if t > 393.0:
            rem = max(0, 20 * 60 - int((t - 393.1) * 60))
            with xf(c, 1600, 330, back_out(at(t, 393.1, 0.4))):
                rrect(c, -150, -70, 300, 140, 20, "#10141a")
                rrect(c, -150, -70, 300, 140, 20, GREEN, stroke=5)
                dtext(c, f"{rem // 60:02d}:{rem % 60:02d}", 0, 30, 90, GREEN, "bebas", track=0.05)


def s_advance(c, t):
    a = 394.4
    cam(c, push(t, a, 400.0, 1.0, 1.04), 960, 560, t)
    info_board(c, t, "#0f1117", "#06070a")
    # a lever thrown in advance, a rail that carries the action
    kword(c, t, 394.56, "DECIDED IN ADVANCE", 960, 160, 80, GOLD, style="rise", track=0.1)
    line(c, 200, 700, 1720, 700, "#d8cfbf", 8)
    for i in range(16):
        line(c, 230 + i * 95, 690, 230 + i * 95, 720, "#8a8f9a", 6)
    lk = ease_out(at(t, 395.0, 0.4))
    with xf(c, 300, 690, rot=lerp(-40, 40, lk)):
        line(c, 0, 0, 0, -150, "#d8cfbf", 14)
        c.drawCircle(0, -150, 24, P(RED))
    k = ease_out(at(t, 396.0, 3.0))
    pose, bob, lean, sp = walk(t, 0.9)
    person(c, lerp(500, 1500, k), 530 + bob, "leo", pose, "focus", t, 0.95, lean=lean)
    with xf(c, 420, 330):
        dtext(c, "MOTIVATION", 0, -40, 40, "#d8cfbf", "bebas", track=0.14)
        rrect(c, -200, -10, 400, 30, 15, "#2a2f3a")
        rrect(c, -200, -10, 400 * 0.18, 30, 15, RED)
    kword(c, t, 397.04, "NO MOTIVATION NEEDED", 960, 960, 64, "#f2ead6", style="rise", track=0.1)


def s_truly(c, t):
    a = 399.9
    cam(c, push(t, a, 404.4, 1.0, 1.05), 960, 540, t)
    info_board(c, t, "#0f1117", "#06070a")
    for i, (lab, col, sc, st) in enumerate((("A GOAL YOU TRULY WANT", GOLD, 1.0, 402.12),
                                            ("A WEAK ONE", "#6a6f7a", 0.55, 403.42))):
        x = 600 + i * 720
        k = back_out(at(t, st - 0.6, 0.5))
        if k <= 0:
            continue
        with xf(c, x, 500, k * sc):
            soft(c, 0, 0, 220, col, 0.3 if i == 0 else 0.05, 60)
            heart(c, 0, 0, 140, col)
        dtext(c, lab, x, 820, 54, col, "bebas", a=clamp(k), track=0.08)
        if i == 0 and t > 402.6:
            check_mark(c, x, 960, 0.8, GREEN, prog=clamp((t - 402.6) * 3))
    kword(c, t, 400.04, "WORKS BEST WHEN", 960, 150, 64, "#f2ead6", style="rise", track=0.14)


def s_woop(c, t):
    a = 404.3
    cam(c, push(t, a, 410.1, 1.0, 1.05), 960, 540, t)
    fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, W * 0.75, ["#16201a", "#050806"]))
    bokeh(c, t, GREEN, 14, seed=21, a=0.1)
    kword(c, t, 405.92, "W O O P", 960, 330, 200, "#ffffff", style="slam", track=0.1, end=406.95)
    words = [("W", "WISH", 407.14, GOLD), ("O", "OUTCOME", 407.52, "#ffd98a"), ("O", "OBSTACLE", 408.3, "#e8b04a"),
             ("P", "PLAN", 408.98, GREEN)]
    for i, (L, wd, st, col) in enumerate(words):
        x = 330 + i * 420
        k = back_out(at(t, min(st, 406.9 + i * 0.12) if t < st else st, 0.4))
        if t < 406.9:
            continue
        on = t >= st
        with xf(c, x, 560, max(0.001, k)):
            rrect(c, -170, -210, 340, 420, 30, "#10141a")
            rrect(c, -170, -210, 340, 420, 30, col if on else "#3a3f4a", stroke=6)
            dtext(c, L, 0, 60, 260, col if on else "#3a3f4a", "bebas")
            if on:
                soft(c, 0, 0, 200, col, 0.12, 60)
                kk = ease_out(at(t, st, 0.4))
                dtext(c, wd, 0, 160, 50, col, "bebas", a=kk, track=0.1)
    kword(c, t, 404.3, "COMBINED", 960, 150, 54, "#d8cfbf", "SemiBold", style="rise", track=0.3, end=406.9)


def s_evidence(c, t):
    a = 410.0
    cam(c, push(t, a, 431.6, 1.0, 1.04), 960, 540, t)
    info_board(c, t, "#0f1117", "#06070a")
    kword(c, t, 410.1, "HOW STRONG IS THE EVIDENCE?", 960, 140, 70, "#f2ead6", style="type", track=0.08, end=412.0)
    studies = [("2006 REVIEW", "94 TESTS", "IF-THEN PLANS", "MEDIUM-LARGE", 0.78, GREEN, 412.26, 416.4),
               ("2024 ANALYSIS", "BIAS-CORRECTED", "IF-THEN PLANS", "SMALLER", 0.45, "#a8d36a", 418.78, 422.86),
               ("META-ANALYSIS", "21 STUDIES", "WOOP-STYLE", "SMALL-MODERATE", 0.35, GOLD, 424.08, 429.52)]
    for i, (yr, n, what, eff, v, col, st, st2) in enumerate(studies):
        x = 400 + i * 560
        k = ease_out(at(t, st, 0.6))
        if k <= 0:
            continue
        with xf(c, x, 0, alpha=clamp(k * 2)):
            dtext(c, yr, 0, 260, 60, col, "bebas", track=0.08)
            dtext(c, n, 0, 310, 36, "#d8cfbf", "bebas", track=0.14)
            dtext(c, what, 0, 352, 30, "#8a8f9a", "SemiBold", track=0.14)
            kk = ease_out(at(t, st2 - 0.6, 1.0))
            hh = 420 * v * kk
            if i == 1 and t > 420.5:
                # shrink from the previous height: publication-bias correction
                hh = 420 * lerp(0.78, v, ease_out(at(t, 420.5, 1.6)))
            rrect(c, -110, 840 - hh, 220, hh, 14, col)
            if kk > 0.5:
                dtext(c, eff, 0, 900, 40, col, "bebas", a=clamp((kk - 0.5) * 2), track=0.06)
    line(c, 160, 840, 1760, 840, "#d8cfbf", 4, 0.5)
    if t > 420.4:
        tag2(c, t, 420.52, "CORRECTED FOR PUBLICATION BIAS", 960, 980, "#a8d36a", 34, end=423.6)


def s_modest(c, t):
    a = 431.5
    cam(c, push(t, a, 437.0, 1.0, 1.06), 960, 540, t)
    info_board(c, t, "#0f1117", "#06070a")
    kword(c, t, 432.04, "MODEST", 600, 360, 150, "#d8cfbf", style="pop", track=0.08)
    kword(c, t, 433.58, "BUT CHEAP", 1300, 360, 150, GREEN, style="pop", track=0.08)
    k = ease_out(at(t, 434.5, 0.8))
    if k > 0:
        # an arrow flies into the gap between dream and action
        line(c, 500, 760, 860, 760, GOLD, 10)
        line(c, 1060, 760, 1420, 760, COOL, 10)
        dtext(c, "DREAM", 680, 840, 50, GOLD, "bebas", track=0.1)
        dtext(c, "ACTION", 1240, 760 + 80, 50, COOL, "bebas", track=0.1)
        ax = lerp(300, 960, k)
        arrow(c, ax - 220, 640, ax, 740, GREEN, 14)
        if k >= 1:
            for i in range(8):
                ang = i / 8 * 6.283
                line(c, 960 + math.cos(ang) * 50, 750 + math.sin(ang) * 50, 960 + math.cos(ang) * 90,
                     750 + math.sin(ang) * 90, GREEN, 6, clamp(1 - (t - 435.3) * 2))
        kword(c, t, 435.32, "THIS GAP", 960, 980, 70, GREEN, style="rise", track=0.14)


# ================================================================= RETURN TO THE PATIENT
def s_backhosp(c, t):
    a = 436.9
    cam(c, push(t, a, 447.7, 1.12, 1.0), 900, 560, t)
    bg(c, "hospital", 8)
    # warmer this time: morning light through the blinds
    p = skia.Paint(BlendMode=skia.BlendMode.kScreen)
    p.setShader(radial(1400, 300, 900, [("#ffcf8a", 0.25), ("#000000", 0)]))
    c.drawRect(skia.Rect(0, 0, W, H), p)
    monitor(c, 1500, 420, 0.9, t)
    hosp_bed(c, 860, 700, 1.0)
    person(c, 760, 655, "hari", "lie", "dreamy" if t < 443.7 else "smile", t, 1.15, rot=-90, face=1,
           look=(0.6, 0), shadow=False)
    hosp_bed(c, 860, 700, 1.0, front=True)
    kword(c, t, 440.36, "AS HUMAN AS WISHES GET", 960, 160, 66, "#fff2d6", style="rise", track=0.1, end=443.5)
    kword(c, t, 444.84, "HIS MIND WASN'T WEAK", 960, 160, 66, "#fff2d6", style="rise", track=0.1)


def s_finishline(c, t):
    a = 447.6
    cam(c, push(t, a, 454.0, 1.0, 1.06), 960, 560, t)
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#3a4a6a", "#1a2030"]))
    c.drawPath(poly([(880, 420), (1040, 420), (1700, H), (220, H)]), P("#2b3245"))
    for i in range(8):
        y0 = 440 + i * 85
        kk = (y0 - 420) / 660
        w_ = 6 + 20 * kk
        rrect(c, 960 - w_ / 2, y0, w_, 30 * (0.3 + kk), 4, "#e8e2d6", 0.6)
    # a beautiful framed picture of the finish line stands in for the road... then is lifted away
    lift = ease_out(at(t, 451.8, 1.2))
    with xf(c, 960, 520 - lift * 700, 1.0, rot=lift * -8):
        rrect(c, -340, -230, 680, 460, 12, "#c9a35a")
        c.save()
        c.clipRect(skia.Rect(-320, -210, 320, 210))
        fill_shader(c, skia.Rect(-320, -210, 320, 210), linear(0, -210, 0, 210, ["#ffd99a", "#ff9f7a"]))
        rrect(c, -200, -80, 400, 80, 8, GOLD)
        dtext(c, "FINISH", 0, -22, 60, "#2a1d16", "bebas", track=0.2)
        for i in range(6):
            sparkle(c, -250 + i * 100, 120, 18, "#ffffff")
        c.restore()
        soft(c, 0, 0, 380, GOLD, 0.25 * (1 - lift), 80)
    if t > 452.4:
        # the road appears; he takes the first step with the walker
        k = clamp((t - 452.6) / 1.4)
        walker_frame(c, 1126, 681, 0.85, 247)
        pose = mix_pose("walker", dict(fa=(55, 15), ba=(50, 15), fl=(14, -10), bl=(-14, -5)), k)
        person(c, 980, 740, "hari", pose, "focus", t, 0.85, lean=6, rim="#ffcf99")
    kword(c, t, 449.16, "A BEAUTIFUL PICTURE", 960, 140, 66, GOLD, style="rise", track=0.1, end=451.8)
    kword(c, t, 452.0, "…STANDING IN FOR THE ROAD", 960, 140, 64, "#f2ead6", style="rise", track=0.08)


def s_oneminute(c, t):
    a = 453.9
    cam(c, push(t, a, 459.7, 1.0, 1.06), 960, 560, t)
    bg(c, "bedroom", 8)
    lit = t > 455.26
    person(c, 760, 700, "leo", "point_up" if lit else "sitthink", "happy" if lit else "dreamy", t, 1.1, face=1,
           look=(0.3, -1))
    if lit:
        k = back_out(at(t, 455.26, 0.4))
        with xf(c, 760, 220, k):
            glow(c, 0, 0, 200, GOLD, 0.5)
            c.drawCircle(0, 0, 70, P("#fff2c4"))
            rrect(c, -30, 60, 60, 40, 8, "#9aa3ad")
    if t > 456.5:
        rem = max(0.0, 60 - (t - 456.6) * 8)
        with xf(c, 1350, 420, back_out(at(t, 456.58, 0.4))):
            c.drawCircle(0, 0, 200, P("#10141a"))
            arc = skia.Path()
            arc.addArc(skia.Rect(-170, -170, 170, 170), -90, 360 * rem / 60)
            c.drawPath(arc, P(GREEN, 22))
            dtext(c, f"0:{int(rem):02d}" if rem < 60 else "1:00", 0, 34, 110, "#ffffff", "bebas", track=0.05)
        kword(c, t, 456.58, "ONE MINUTE", 1350, 720, 70, GREEN, style="rise", track=0.12)
    kword(c, t, 458.44, "THREE QUESTIONS", 960, 990, 70, "#f2ead6", style="slam", track=0.12)


def s_questions(c, t):
    a = 459.6
    cam(c, push(t, a, 464.7, 1.0, 1.04), 960, 540, t)
    fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, W * 0.75, ["#16201a", "#050806"]))
    qs = [("1", "What is in my way?", 459.72), ("2", "What is my first move?", 461.2),
          ("3", "When exactly do I make it?", 462.74)]
    for i, (n, q, st) in enumerate(qs):
        k = ease_out(at(t, st, 0.5))
        if k <= 0:
            continue
        y = 330 + i * 220
        active = st <= t < (qs[i + 1][2] if i < 2 else 999)
        with xf(c, (1 - k) * -60, 0, alpha=clamp(k * 2) * (1.0 if active else 0.55)):
            c.drawCircle(330, y - 24, 70, P(GREEN if active else "#3a4a40"))
            dtext(c, n, 330, y + 16, 90, "#0b120d", "bebas")
            dtext(c, q, 450, y, 78, "#f6efe2", "playb", "left")
            if active:
                underline(c, t, st + 0.2, 450 + dwidth(q, 78, "playb") / 2, y + 26, dwidth(q, 78, "playb"), GREEN, 6)


def s_end(c, t):
    a = 464.6
    if t < 467.6:
        cam(c, push(t, a, 467.6, 1.0, 1.1), 960, 600, t)
        bg(c, "bedroom", 8)
        rrect(c, 300, 720, 1320, 40, 10, "#3a2c40")
        person(c, 760, 720, "leo", "sitdesk", "focus", t, 1.05, face=1, look=(0.6, 0.5))
        ck = [clamp((t - 465.4 - i * 0.6) * 3) for i in range(3)]
        notebook(c, 1250, 640, 0.75, t, 0, ["IN MY WAY", "FIRST MOVE", "WHEN"], ck)
        rem = max(0.0, 12 - (t - 464.6) * 3)
        with xf(c, 330, 300):
            dtext(c, f"0:{int(rem):02d}", 0, 30, 110, GREEN, "bebas", track=0.05)
        kword(c, t, 464.6, "WRITE IT DOWN", 960, 990, 70, "#f2ead6", style="rise", track=0.14)
    else:
        fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, W * 0.7, ["#1a130c", "#050403"]))
        bokeh(c, t, GOLD, 24, seed=9, a=0.12, speed=10)
        k = ease_out(at(t, 467.7, 0.9))
        out = clamp((472.4 - t) / 0.8)
        with xf(c, 0, 0, alpha=out):
            dtext(c, "DREAM FIRST.", W / 2, 470 + (1 - k) * 20, 120, GOLD, "bebas", a=clamp(k * 2), track=0.12)
            k2 = ease_out(at(t, 468.5, 0.9))
            dtext(c, "THEN PLAN THE ROAD.", W / 2, 620 + (1 - k2) * 20, 120, "#f6efe2", "bebas", a=clamp(k2 * 2),
                  track=0.12)
            k3 = ease_out(at(t, 469.6, 0.8))
            rrect(c, W / 2 - 260 * k3, 680, 520 * k3, 3, 1.5, GOLD)
            dtext(c, "THE DREAM TAX", W / 2, 760, 40, "#bfae90", "SemiBold", a=k3, track=0.4)
