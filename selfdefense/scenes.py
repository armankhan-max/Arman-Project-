"""B-roll scenes (pure code motion graphics) + the shot list.

Every scene is   fn(c, t, d, w, h, S, **kw)
  t  local time in the shot (s), d shot length, (w, h) the box it fills
     (1920x1080 full screen, or 960x1080 for the split layout),
  S(i) = start of sentence i relative to this shot (so pops land on words).
Content is laid out in a 1080x1080 "stage" that is centred in the box."""
import math
import skia
from kit import *  # noqa: F401,F403
from kit import W, H


def stage(c, w, h):
    k = min(1.0, w / 1180.0)
    c.translate((w - 1080 * k) / 2, (h - 1080 * k) / 2); c.scale(k, k)


# ============================================================ HOOK / INTRO
def hook(c, t, d, w, h, S):
    bg_xray(c, w, h, t)
    c.save(); stage(c, w, h)
    hit = 2.2
    fx = lerp(-200, 520, ease_out(clamp(t / hit))) if t < hit else 520 - 20 * math.exp(-(t - hit) * 6) * math.sin((t - hit) * 40)
    skull_profile(c, 830, 470, 1.2, BONE, a=0.9, helmet=clamp((t - hit) * 2) * 0.8)
    if t < hit + 0.25:
        fist_shape(c, fx, 440, 1.1, SKIN, rot=90)
    else:
        hand_skeleton(c, fx - 40, 470, 1.15, t, BONE, crack=clamp((t - hit - 0.2) * 3), fist=0.0, a=1)
        glow(c, fx - 40, 470, 260, XRAY, 0.25)
    impact(c, 650, 440, t, hit, "#ffffff", 200)
    kicker(c, t, 0.4, hit + 0.1, "HIT HIS FACE?", 540, 900, 80)
    kicker(c, t, hit + 0.3, d + 1, "THE FIRST BONE TO BREAK...", 540, 860, 62, bar=None)
    kicker(c, t, hit + 1.6, d + 1, "...IS YOURS", 540, 975, 96, bar=RED)
    c.restore()


def clinic(c, t, d, w, h, S):
    bg_night_street(c, w, h, t)
    c.save(); stage(c, w, h)
    stamp(c, t, 0.6, 300, 220, "NADA, KOBE", RED, 58)
    label_line(c, t, S(2) - 0.2 if S(2) > 0 else 2.5, 380, 560, 520, 700, "BACK ROOM", GOLD, 44)
    if t > S(2) + 1.2:
        k = ease_out(at(t, S(2) + 1.2, 0.5))
        with xf(c, 540, 900, alpha=k):
            rrect(c, -360, -60, 720, 110, 16, "#000000", 0.6)
            text(c, "\"NEVER ASKED QUESTIONS\"", 0, 18, 48, "#ffffff", "serifi")
    c.restore()


def eleven(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#1a1018")
    c.save(); stage(c, w, h)
    text(c, "WINTER 1996", 540, 150, 56, GOLD, "black", spacing=8, a=clamp(t * 3))
    for i in range(11):
        t0 = 0.4 + i * 0.22
        k = pop(t, t0, 0.3)
        if k <= 0: continue
        x = 190 + (i % 4) * 233; y = 340 + (i // 4) * 220
        with xf(c, x, y, s=0.62 * k, rot=-10 + (i * 37) % 20):
            fist_shape(c, 0, 0, 1, SKIN)
            for b in range(4):
                line(c, -100, -50 + b * 38, 100, -30 + b * 38, "#f2f2ee", 22, 0.92)
    counter(c, t, 0.4, 540, 1000, 11, 150, RED, dur=2.4, suffix=" HANDS")
    c.restore()


def quote(c, t, d, w, h, S, lines=(), who="", color="#1c140c", size=74):
    bg_paper(c, w, h, t)
    c.save(); stage(c, w, h)
    y0 = 540 - (len(lines) - 1) * size * 0.65
    for i, ln in enumerate(lines):
        k = ease_out(at(t, 0.2 + i * 0.35, 0.5))
        text(c, ln, 540, y0 + i * size * 1.3 + (1 - k) * 30, size, color, "serif", a=k)
    text(c, "“", 140, y0 - 30, 260, RED, "serif", a=0.6)
    if who:
        k = at(t, 0.5 + len(lines) * 0.35, 0.5)
        brush_bar(c, 540 - 200, y0 + len(lines) * size * 1.3 + 10, 400, 70, RED, k)
        text(c, who, 540, y0 + len(lines) * size * 1.3 + 60, 40, "#ffffff", "black", a=k)
    c.restore()


def palm_vs_fist(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#151a1f")
    c.save(); stage(c, w, h)
    k1 = pop(t, 0.2); k2 = pop(t, S(2) if S(2) > 0 else 1.2)
    with xf(c, 290, 480, s=1.15 * k1): palm_shape(c, 0, 0, 1, SKIN, heel=1, t=t)
    text(c, "PALM", 290, 860, 70, GREEN, a=k1)
    tick(c, 290, 950, 90, t, 0.6)
    with xf(c, 790, 500, s=1.3 * k2): fist_shape(c, 0, 0, 1, SKIN)
    text(c, "FIST", 790, 860, 70, RED, a=k2)
    x_over(c, 790, 500, 300, t, (S(2) if S(2) > 0 else 1.2) + 0.4)
    line(c, 540, 200, 540, 900, "#ffffff", 3, 0.2)
    c.restore()


def head_question(c, t, d, w, h, S):
    bg_xray(c, w, h, t)
    c.save(); stage(c, w, h)
    skull_profile(c, 560, 470, 1.4, BONE, a=0.85)
    reticle(c, 740, 360, 70, t, RED, t0=0.4)
    kicker(c, t, 0.8, d + 1, "WHEN IT MAKES SENSE", 540, 860, 60, bar=GREEN)
    kicker(c, t, d * 0.55, d + 1, "WHEN IT'S FOOLISH", 540, 985, 60, bar=RED)
    c.restore()


def three_spots(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#1b1411")
    c.save(); stage(c, w, h)
    man(c, 540, 1050, 1.05, "stand", t, "#0d0b0a", rim="#5a4632", big=1.25)
    torso_anatomy(c, 540, 1050, 1.05, t, show=("ribs",), a=0.6)
    spots = [(540 - 70, 1050 - 1.05 * 505, "1"), (540, 1050 - 1.05 * 515, "2"), (540 + 120, 1050 - 1.05 * 260, "3")]
    pts = [(540 - 63, 1050 - 1.05 * 505), (540, 1050 - 1.05 * 515), (540 - 120, 1050 - 1.05 * 250)]
    for i, (x, y) in enumerate(pts):
        reticle(c, x, y, 46, t, [RED, GOLD, XRAY][i], t0=0.5 + i * 0.7)
    for i, s in enumerate(["NO GLOVES", "NO GREAT STRENGTH"]):
        k = pop(t, 2.8 + i * 0.6)
        if k > 0:
            with xf(c, 540, 120 + i * 90, s=k): text(c, s, 0, 20, 58, "#ffffff", shadow=0.7)
    counter(c, t, 0.4, 900, 520, 3, 220, GOLD, dur=2.0)
    text(c, "SPOTS", 900, 600, 54, GOLD, a=clamp(t - 0.6))
    c.restore()


def not_face(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#120e0e")
    c.save(); stage(c, w, h)
    man(c, 540, 1100, 1.1, "stand", t, "#0b0909", rim="#6d5236", big=1.2)
    # glowing question marks orbiting the body
    for i in range(3):
        ang = t * 1.2 + i * 2.1
        text(c, "?", 540 + math.cos(ang) * 330, 560 + math.sin(ang) * 120, 120, GOLD, a=0.5 + 0.5 * math.sin(t * 3 + i))
    x_over(c, 540, 1100 - 1.1 * 850, 170, t, S(13) + 0.1 if S(13) >= 0 else 0.6)
    kicker(c, t, S(13) if S(13) >= 0 else 0.5, d + 1, "IT'S NOT HIS FACE", 540, 160, 70)
    kicker(c, t, S(14) if S(14) >= 0 else 1.5, d + 1, "ALMOST NOBODY LOOKS", 540, 1010, 56, bar=None)
    c.restore()


# ============================================================ FIST PROBLEM
def forehead(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#191512")
    c.save(); stage(c, w, h)
    hit = max(0.5, S(27))
    dodge = ease_out(clamp((t - (S(26) + 1.5)) * 4)) if S(26) > -50 else 0
    skull_profile(c, 760 + dodge * 0, 520 - dodge * 40, 1.15, BONE, a=0.9, helmet=clamp((t - hit) * 2))
    fx = lerp(-150, 520, ease_out(clamp((t - hit + 0.6) / 0.6)))
    if t < hit + 0.1:
        fist_shape(c, fx, 360, 1.0, SKIN, rot=90)
    else:
        hand_skeleton(c, 480, 380, 0.95, t, BONE, crack=clamp((t - hit - 0.15) * 3))
    impact(c, 620, 370, t, hit, "#ffffff", 180)
    if t > S(26):
        text(c, "1 INCH", 900, 210, 54, GOLD, a=clamp((t - S(26) - 1.4) * 3))
    if S(28) > -50:
        kicker(c, t, S(28), d + 1, "SKULL = HELMET", 540, 960, 74)
    c.restore()


def hand27(c, t, d, w, h, S):
    bg_xray(c, w, h, t)
    c.save(); stage(c, w, h)
    hand_skeleton(c, 400, 640, 1.45, t, BONE, glowc=XRAY)
    glow(c, 400, 500, 330, XRAY, 0.18)
    counter(c, t, 0.3, 820, 470, 27, 230, XRAY, dur=1.5)
    text(c, "SMALL BONES", 820, 560, 54, "#ffffff", a=clamp(t - 0.8))
    kicker(c, t, 2.4, d + 1, "BUILT TO BUTTON A SHIRT", 540, 980, 58)
    c.restore()


def boxer(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#16120f", light=(0.5, 0.0))
    c.save(); stage(c, w, h)
    strip = clamp((t - (S(32) if S(32) > 0 else d * 0.6)) * 2.5)
    with xf(c, 540, 460, s=1.6):
        fist_shape(c, 0, 0, 1, SKIN)
        k = ease_out(clamp(t / 1.2)) * (1 - strip)
        for b in range(6):
            line(c, -100, -70 + b * 30, lerp(-100, 100, k), -60 + b * 30, "#f5f5f0", 20, 0.95 * (1 - strip))
        if t > 1.4:
            kk = ease_out(at(t, 1.4, 0.5)) * (1 - strip)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-125, -110, 250, 260), 110, 110), P(RED, 14, kk))
    text(c, "TAPE  +  GLOVES", 540, 860, 66, "#ffffff", a=clamp(t - 0.5) * (1 - strip))
    if strip > 0:
        kicker(c, t, S(32), d + 1, "YOU: NEITHER", 540, 900, 90)
    c.restore()


def bones_age(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#141418")
    c.save(); stage(c, w, h)
    for i, (x, lab, por) in enumerate([(300, "AGE 30", 0.0), (780, "60+", 1.0)]):
        k = pop(t, 0.3 + i * 0.8)
        if k <= 0: continue
        with xf(c, x, 470, s=k):
            c.drawCircle(0, 0, 190, P(BONE))
            c.drawCircle(0, 0, 80, P("#3a2a1e"))
            r = rng(7 + i)
            for j in range(int(120 * por)):
                ang = r.uniform(0, math.tau); rr = r.uniform(95, 180)
                c.drawCircle(math.cos(ang) * rr, math.sin(ang) * rr, r.uniform(5, 16), P("#3a2a1e"))
        text(c, lab, x, 740, 70, GREEN if i == 0 else RED, a=k)
    if S(34) > -50:
        kicker(c, t, S(34), d + 1, "BROKEN HAND = NO HANDS", 540, 960, 62)
    c.restore()


def curb_fall(c, t, d, w, h, S):
    bg_night_street(c, w, h, t, sign="駅", sign_col="#ff4d4d", rain=True)
    c.save(); stage(c, w, h)
    ground = 900
    rect(c, 100, ground, 880, 30, "#8a8a8a"); rect(c, 100, ground + 30, 880, 120, "#3a3a3a")
    th = S(37) + 0.2 if S(37) > -50 else 1.0
    k = ease_out(clamp((t - th) / 0.7))
    ang = -88 * k
    with xf(c, 420 + 160 * k, ground, rot=ang):
        man(c, 0, 0, 0.55, "stand", 0, "#0b0b0b", rim="#ffffff", big=1.0, a=1)
    impact(c, 420 + 160 * k + 470 if False else 900, ground - 10, t, th + 0.7, RED, 160)
    if t > th + 0.75:
        glow(c, 900, ground, 300, RED, 0.35 * (0.6 + 0.4 * math.sin(t * 8)))
    if S(38) > -50:
        kicker(c, t, S(38), d + 1, "NOT SELF-DEFENSE ANYMORE", 540, 170, 60)
    c.restore()


def sannomiya(c, t, d, w, h, S):
    bg_night_street(c, w, h, t, sign="三宮", sign_col="#ff4d4d", rain=True)
    c.save(); stage(c, w, h)
    stamp(c, t, 0.4, 540, 170, "SANNOMIYA STATION · 1999", GOLD, 46, rot=-3)
    for i, s in enumerate(["ONE PUNCH.", "ONE CURB."]):
        if S(40 + i) > -50:
            kicker(c, t, S(40 + i), d + 1, s, 540, 520 + i * 130, 92, bar=RED if i == 0 else None)
    if S(42) > -50 and t > S(42):
        k = ease_out(at(t, S(42), 0.6))
        for i in range(9):
            x = 90 + i * 113
            line(c, x, -20 + (1 - k) * -1100, x, 1100 * k, "#6d6d6d", 26)
            line(c, x - 8, -20, x - 8, 1100 * k, "#b0b0b0", 5, 0.6)
        counter(c, t, S(42) + 0.3, 540, 980, 6, 170, RED, dur=0.8, suffix=" YEARS")
    c.restore()


def walk_away(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#101418", light=(0.85, 0.2))
    c.save(); stage(c, w, h)
    for i in range(8):
        t0 = 0.3 + i * 0.35
        k = clamp((t - t0) * 3) * clamp(1 - (t - t0 - 3) * 0.5)
        x = 180 + i * 105; y = 700 + (40 if i % 2 else -40)
        with xf(c, x, y, rot=90, alpha=k):
            c.drawOval(skia.Rect(-26, -50, 26, 30), P(PAPER)); c.drawOval(skia.Rect(-20, 40, 20, 80), P(PAPER))
    arrow(c, 200, 880, 900, 880, GOLD, 16, prog=ease_out(clamp(t / 2)))
    kicker(c, t, 0.4, d + 1, "RULE #1", 540, 200, 70, bar=RED)
    kicker(c, t, 0.9, d + 1, "IF YOU CAN, WALK AWAY", 540, 330, 66, bar=None)
    c.restore()


# ============================================================ #3 LIVER
def title_card(c, t, d, w, h, S, num="3", name="THE LIVER", jp="肝臓", col=RED):
    fill_shader(c, skia.Rect(0, 0, w, h), radial(w / 2, h / 2, max(w, h) * 0.7, ["#1d1612", "#050403"]))
    koi_wave(c, w, h, t, 0.18, col)
    c.save(); stage(c, w, h)
    text(c, jp, 540, 640, 520, col, "jp", a=0.13 * clamp(t * 2))
    k = pop(t, 0.05, 0.4)
    with xf(c, 540, 470, s=0.6 + 0.4 * k, alpha=clamp(k)):
        text(c, "NUMBER", 0, -170, 54, GOLD, "black", spacing=14)
        text(c, num, 0, 120, 330, "#ffffff", "black", shadow=0.7)
    brush_bar(c, 540 - 330, 700, 660, 120, col, at(t, 0.5, 0.35), seed=4)
    text(c, name, 540, 790, 96, "#ffffff", "black", a=clamp((t - 0.6) * 4))
    c.restore()
    sakura(c, w, h, t, 14, 0.5)


def liver_check(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#1d1410")
    c.save(); stage(c, w, h)
    X, Y, s = 540, 1300, 1.25
    man(c, X, Y, s, "stand", t, "#100c0a", rim="#6a4c33", big=1.2)
    torso_anatomy(c, X, Y, s, t, show=("ribs",) + (("liver",) if t > max(0, S(58)) else ()), a=1)
    lx, ly = X - 60 * s, Y + (-760 + 255) * s
    if t > 0.8:  # pressing hand
        press = 8 * math.sin(max(0, t - S(55)) * 6) if S(55) <= t < S(56) + 1 else 0
        with xf(c, lx - 330 + press, ly + 40, rot=80): palm_shape(c, 0, 0, 0.5, SKIN, a=clamp(t - 0.8))
    label_line(c, t, max(0.4, S(54)), lx, ly - 140 * s / 1.25, 120, 230, "BELOW THE RIBS", GOLD, 40)
    if S(57) > -50:
        label_line(c, t, S(57) + 0.3, lx, ly, 160, 860, "NO MUSCLE OVER IT", RED, 44)
    if S(58) > -50:
        kicker(c, t, S(58) + 0.4, d + 1, "SAME PLACE ON EVERY MAN", 540, 1010, 54, bar=RED)
    c.restore()


def armor_gap(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#15171b")
    c.save(); stage(c, w, h)
    X, Y, s = 540, 1250, 1.2
    man(c, X, Y, s, "stand", t, "#0c0c0e", rim="#4f5966", big=1.35)
    plates = [(-150, -730, 300, 90), (-150, -630, 300, 90), (-60, -530, 210, 90), (-150, -430, 300, 70)]
    for i, (px, py, pw, ph) in enumerate(plates):
        k = pop(t, 0.3 + i * 0.25)
        if k <= 0: continue
        with xf(c, X + (px + pw / 2) * s, Y + (py + ph / 2) * s, s=k * s):
            rrect(c, -pw / 2, -ph / 2, pw, ph, 12, "#6f7c88"); rrect(c, -pw / 2, -ph / 2, pw, ph, 12, "#c7d3dc", stroke=4)
            for rv in (-pw / 2 + 16, pw / 2 - 16): c.drawCircle(rv, 0, 6, P("#2a3036"))
    if S(61) > -50 and t > S(61):
        gx, gy = X - 105 * s, Y - 485 * s
        glow(c, gx, gy, 140, RED, 0.6 * (0.6 + 0.4 * math.sin(t * 7)))
        reticle(c, gx, gy, 50, t, RED, t0=S(61))
        kicker(c, t, S(61) + 0.3, d + 1, "THE GAP", 540, 160, 90)
    if S(59) > -50:
        kicker(c, t, S(59), (S(61) if S(61) > -50 else d) - 0.1, "LIKE HITTING A BEAR", 540, 160, 70, bar=None)
    c.restore()


def sit_down(c, t, d, w, h, S):
    bg_dojo(c, w, h, t)
    c.save(); stage(c, w, h)
    hit = (S(62) + 1.6) if S(62) > -50 else 1.5
    k = ease_out(clamp((t - hit - 0.3) / 0.5))
    if t < hit + 0.3:
        man(c, 600, 1000, 0.9, "guard_high", t, "#0d0a08", rim="#ffcf87", big=1.25)
    else:
        with xf(c, 600, 1000 + 80 * k, sy=1 - 0.25 * k, sx=1):
            man(c, 0, 0, 0.9, "sit", t, "#0d0a08", rim="#ffcf87", big=1.25)
    with xf(c, 290, 690, rot=-10): palm_shape(c, 0, 0, 0.55 * clamp((t - hit + 0.6) * 3), SKIN)
    impact(c, 520, 600, t, hit, "#ffffff", 140)
    if S(64) > -50:
        kicker(c, t, S(64), d + 1, "THE BODY SITS DOWN", 540, 170, 70)
    c.restore()


def palm_elbow(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#1a1611")
    c.save(); stage(c, w, h)
    with xf(c, 330, 480, s=1.2 * pop(t, 0.2)): palm_shape(c, 0, 0, 1, SKIN, heel=1, t=t)
    text(c, "HEEL OF PALM", 330, 860, 42, GOLD, a=clamp(t * 2))
    k = pop(t, 1.3)
    if k > 0:
        with xf(c, 780, 500, s=k):
            line(c, -150, -160, 0, 60, SKIN, 90); line(c, 0, 60, 170, -40, SKIN, 82)
            c.drawCircle(0, 60, 60, P(SKIN))
            glow(c, 0, 80, 120, GOLD, 0.5 * (0.6 + 0.4 * math.sin(t * 8)))
        text(c, "UP CLOSE: ELBOW", 780, 860, 42, GOLD, a=k)
    kicker(c, t, 0.1, d + 1, "NO FIST NEEDED", 540, 170, 70, bar=RED)
    c.restore()


def hip_turn(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#13161a", light=(0.5, 0.0))
    c.save(); stage(c, w, h)
    ang = 35 * math.sin(t * 2.4)
    # top-down hips + shoulders
    with xf(c, 380, 520, rot=ang):
        c.drawOval(skia.Rect(-200, -70, 200, 70), P("#3b3026")); c.drawOval(skia.Rect(-200, -70, 200, 70), P(GOLD, 5))
        c.drawCircle(0, 0, 60, P("#6e5a46"))
        arrow(c, 0, 0, 260, 0, RED, 14)
    arc = skia.Path(); arc.addArc(skia.Rect(380 - 260, 520 - 260, 380 + 260, 520 + 260), -60, 120)
    c.drawPath(arc, P(GOLD, 6, 0.6))
    text(c, "HIPS", 380, 860, 60, GOLD)
    # car door closing
    da = 70 * (0.5 + 0.5 * math.sin(t * 2.4 - 1.2))
    with xf(c, 760, 360):
        rect(c, -20, -10, 300, 18, "#777777", 1)
        with xf(c, 0, 0, rot=da):
            rrect(c, 0, -8, 260, 30, 6, "#a8b3bd"); rect(c, 200, -2, 30, 18, "#333333")
        c.drawCircle(0, 0, 14, P("#222222"))
    text(c, "LIKE CLOSING A CAR DOOR", 840, 640, 40, "#ffffff", a=clamp(t - 0.5))
    if S(69) > -50:
        kicker(c, t, S(69), d + 1, "POWER = THE TURN", 540, 990, 72)
    c.restore()


def windup(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#1b1212")
    c.save(); stage(c, w, h)
    kicker(c, t, 0.1, d + 1, "MISTAKE #1: WIND-UP", 540, 160, 64, bar=RED)
    dip = 0.5 + 0.5 * math.sin(t * 3)
    with xf(c, 540, 1060, rot=-6 * dip):
        man(c, 0, 0, 0.95, "palm", t, "#0d0909", rim="#7a3a3a", big=1.15)
    if t > (S(72) if S(72) > -50 else 1):
        k = pop(t, S(72) if S(72) > -50 else 1)
        with xf(c, 760, 300, s=k):
            c.drawCircle(0, 0, 70, P(GOLD)); text(c, "!", 0, 38, 110, "#000000")
        text(c, "HE SEES IT COMING", 540, 1000, 56, "#ffffff", a=k, shadow=0.6)
    c.restore()


def through(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#191311")
    c.save(); stage(c, w, h)
    kicker(c, t, 0.1, d + 1, "MISTAKE #2: HITTING THE SKIN", 540, 140, 54, bar=RED)
    for i, (y, label, stop, col) in enumerate([(380, "SLAP", 0.42, RED), (720, "THROUGH", 0.86, GREEN)]):
        rect(c, 120, y - 120, 840, 240, "#3a2219", 0.6)
        rect(c, 440, y - 130, 18, 260, "#e0a98a")  # skin line
        c.drawCircle(780, y, 46, P("#8f2a22")); text(c, "TARGET", 780, y + 90, 30, DIM)
        t0 = (S(75) if i == 0 else S(76)) if S(75) > -50 else 0.6 + i * 1.5
        prog = ease_out(clamp((t - t0) / 0.5))
        arrow(c, 160, y, lerp(160, 160 + 840 * stop, 1), y, col, 22, prog=prog)
        if prog >= 1:
            text(c, label, 300, y - 140, 64, col, shadow=0.6)
            if i == 1: impact(c, 780, y, t, t0 + 0.5, GOLD, 120)
    c.restore()


def dojo_story(c, t, d, w, h, S):
    bg_dojo(c, w, h, t)
    c.save(); stage(c, w, h)
    stamp(c, t, 0.3, 220, 140, "AGE 14", RED, 50)
    tap = S(80) + 3.0 if S(80) > -50 else 99
    sit = S(81) if S(81) > -50 else 99
    if t < sit:
        man(c, 650, 980, 0.8, "stand", t, "#151009", rim="#ffcf87", big=1.6)
    else:
        k = ease_out(clamp((t - sit) / 0.5))
        with xf(c, 650, 980 + 50 * k, sy=1 - 0.2 * k, sx=1):
            man(c, 0, 0, 0.8, "sit", t, "#151009", rim="#ffcf87", big=1.6)
    ux = lerp(150, 380, ease_out(clamp((t - (S(80) if S(80) > -50 else 99)) / 1.5)))
    man(c, ux, 980, 0.7, "palm" if t > tap - 0.6 else "stand", t, "#0a0806", rim="#d9a35c", big=0.85)
    impact(c, 530, 640, t, tap, "#ffffff", 90)
    if t < sit:
        text(c, "KURIBAYASHI", 650, 160 + 60, 52, "#ffffff", shadow=0.6, a=clamp(t - 1))
    text(c, "UNCLE MORI", ux, 1040, 40, GOLD, a=clamp(t - (S(80) if S(80) > -50 else 99)))
    c.restore()


def coat_quote(c, t, d, w, h, S):
    quote(c, t, d, w, h, S, lines=("Muscle is a coat.", "Every coat has a gap", "under the arm."), who="UNCLE MORI")


# ============================================================ #2 SOLAR PLEXUS
def charge(c, t, d, w, h, S, label="WHAT IF HE CHARGES?"):
    fill_shader(c, skia.Rect(0, 0, w, h), linear(0, 0, 0, h, ["#0d0d10", "#26201a"]))
    speed_lines(c, w, h, t, w / 2, h * 0.45, 0.25)
    c.save(); stage(c, w, h)
    k = (t / max(d, 0.1))
    s = lerp(0.35, 1.25, k ** 1.6)
    man(c, 540, 1000 + 400 * k, s, "charge", t, "#090909", rim="#c8102e", big=1.3, run=t)
    kicker(c, t, 0.2, d + 1, label, 540, 170, 66)
    c.restore()


def plexus_find(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#17130f")
    c.save(); stage(c, w, h)
    X, Y, s = 540, 1330, 1.25
    man(c, X, Y, s, "stand", t, "#100c0a", rim="#6a4c33", big=1.2)
    torso_anatomy(c, X, Y, s, t, show=("ribs",) + (("plexus",) if t > max(0, S(95)) else ()))
    px, py = X, Y + (-760 + 215) * s
    label_line(c, t, max(0.3, S(92)), px, py, 720, 200, "RIBS MEET", BONE, 40)
    if S(93) > -50 and t > S(93):
        k = ease_out(at(t, S(93), 0.5))
        for i in range(2):
            rrect(c, px - 60, py + 8 + i * 22 * k, 120, 20, 10, SKIN, 0.9 * k)
        label_line(c, t, S(93) + 0.4, px, py + 40 * s, 700, 470, "2 FINGERS BELOW", GOLD, 40)
    if S(95) > -50:
        label_line(c, t, S(95) + 0.4, px, py + 40 * s, 120, 700, "NERVE BUNDLE", RED, 40, align="left")
    if S(96) > -50 and t > S(96) + 1:
        k = clamp((t - S(96) - 1) * 2)
        kicker(c, t, S(96) + 1, d + 1, "CAN'T BREATHE", 540, 1010, 76)
    c.restore()


def charge_palm(c, t, d, w, h, S):
    fill_shader(c, skia.Rect(0, 0, w, h), linear(0, 0, 0, h, ["#0d0d10", "#26201a"]))
    hit = (S(100) + 3.5) if S(100) > -50 else d * 0.5
    if t < hit: speed_lines(c, w, h, t, w / 2, h * 0.45, 0.25)
    c.save(); stage(c, w, h)
    k = clamp(t / hit)
    s = lerp(0.35, 1.05, k ** 1.5) if t < hit else 1.05 - 0.04 * math.exp(-(t - hit) * 5)
    man(c, 540, 1000 + 330 * min(1, k), s, "charge", t if t < hit else hit, "#090909", rim="#c8102e", big=1.3, run=t if t < hit else hit)
    py = 1000 + 330 * min(1, k) + (-760 + 245) * s
    with xf(c, 540, py + 150, rot=0): palm_shape(c, 0, 80, 0.85, SKIN, heel=clamp(t - hit + 1), t=t)
    impact(c, 540, py, t, hit, GOLD, 220)
    if t > hit:
        torso_anatomy(c, 540, 1330, 1.05, t, show=("plexus",), a=clamp((t - hit) * 3))
        kicker(c, t, hit + 0.2, d + 1, "HIS SPEED = YOUR POWER", 540, 160, 64)
    else:
        kicker(c, t, 0.2, hit, "DON'T BACK UP", 540, 160, 70)
    c.restore()


def precision(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#121214")
    c.save(); stage(c, w, h)
    X, Y, s = 540, 1600, 1.7
    torso_x = X
    man(c, X, Y, s, "stand", t, "#100c0a", rim="#4a3a2a", big=1.15, legs=False)
    torso_anatomy(c, X, Y, s, t, show=("ribs",))
    py = Y + (-760 + 245) * s
    kicker(c, t, 0.2, d + 1, "IT IS SMALL", 540, 120, 64)
    if S(105) > -50:
        label_line(c, t, S(105), torso_x, py - 110, 560, 250, "TOO HIGH: BREASTBONE", RED, 38)
        x_over(c, torso_x, py - 110, 70, t, S(105) + 0.3)
    if S(106) > -50:
        label_line(c, t, S(106), torso_x - 150, py + 20, 90, 640, "SIDE: RIBS", RED, 38)
        x_over(c, torso_x - 150, py + 20, 70, t, S(106) + 0.3)
    if S(108) > -50 and t > S(108) - 0.5:
        reticle(c, torso_x, py, 40, t, GREEN, t0=S(108) - 0.5)
        kicker(c, t, S(108), d + 1, "IT HAS TO BE THE SPOT", 540, 1010, 64, bar=GREEN, color="#06140a")
    c.restore()


def nurse(c, t, d, w, h, S):
    bg_paper(c, w, h, t)
    c.save(); stage(c, w, h)
    # ID card
    k = pop(t, 0.3)
    with xf(c, 540, 300, s=k, rot=-3):
        rrect(c, -330, -150, 660, 300, 22, "#ffffff"); rrect(c, -330, -150, 660, 70, 22, "#2f7dd1")
        rect(c, -330, -100, 660, 20, "#2f7dd1")
        c.drawCircle(-200, 50, 80, P("#d6dde4")); c.drawCircle(-200, 20, 34, P("#8b98a5")); c.drawOval(skia.Rect(-260, 60, -140, 130), P("#8b98a5"))
        text(c, "BERNICE, 74", 90, 20, 50, "#1d2733")
        text(c, "NURSE · 40 YEARS", 90, 80, 36, "#2f7dd1")
        text(c, "+", -280, -100, 60, "#ffffff")
    # CPR chart: torso outline with 'never press' zone
    if S(112) > -50 and t > S(112) - 0.3:
        kk = ease_out(at(t, S(112) - 0.3, 0.5))
        with xf(c, 540, 700, alpha=kk):
            rrect(c, -170, -150, 340, 330, 120, "#d9cdb5"); rrect(c, -170, -150, 340, 330, 120, "#5b4a33", stroke=5)
            line(c, 0, -120, 0, 40, "#5b4a33", 8)
            c.drawCircle(0, 80, 26, P(RED, 5)); x_over(c, 0, 80, 50, t, S(112) + 0.3)
            text(c, "CPR: NEVER PRESS HERE", 0, 230, 40, RED)
    if S(113) > -50:
        kicker(c, t, S(113), (S(115) if S(115) > -50 else d + 1), "FOUND IT IN 1 TRY", 540, 1010, 58)
    if S(117) > -50:
        kicker(c, t, S(117), d + 1, "THE TARGET WAS ALWAYS THERE", 540, 1010, 52)
    c.restore()


def poll(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#141a1f")
    c.save(); stage(c, w, h)
    text(c, "YOUR CHOICE?", 540, 170, 70, "#ffffff", a=clamp(t * 3))
    for i, (lab, col) in enumerate([("THE LIVER", RED), ("SOLAR PLEXUS", GOLD)]):
        k = pop(t, 0.3 + i * 0.3)
        if k <= 0: continue
        y = 330 + i * 180
        with xf(c, 540, y, s=k):
            rrect(c, -380, -65, 760, 130, 65, "#1f262d"); rrect(c, -380, -65, 760, 130, 65, col, stroke=5)
            fillw = 760 * (0.5 + 0.08 * math.sin(t * 1.3 + i * 3)) * ease_out(clamp(t - 1))
            c.save(); c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-380, -65, 760, 130), 65, 65), True)
            rect(c, -380, -65, fillw, 130, col, 0.25); c.restore()
            text(c, lab, 0, 22, 56, "#ffffff")
    # comment box typing
    if S(124) > -50 and t > S(124):
        msg = "Liver, because..."
        n = int(clamp((t - S(124)) / 1.6) * len(msg))
        rrect(c, 120, 720, 840, 130, 20, "#ffffff")
        c.drawCircle(190, 785, 38, P("#c9b48a"))
        text(c, msg[:n] + ("|" if int(t * 3) % 2 else ""), 250, 800, 44, "#222222", "semi", align="left")
        text(c, "COMMENT BELOW", 540, 960, 56, GOLD)
    c.restore()


# ============================================================ #1 LEG
def eyes_up(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#151310")
    c.save(); stage(c, w, h)
    X, Y, s = 540, 1080, 0.85
    man(c, X, Y, s, "guard_high", t, "#0d0b09", rim="#6a5032", big=1.25)
    hy = Y - 850 * s
    for sx in (-1, 1):
        arrow(c, X + sx * 30, hy - 20, X + sx * 130, hy - 220, GOLD, 10, prog=ease_out(at(t, 0.5, 0.6)))
    text(c, "EYES UP", X, hy - 250, 50, GOLD, a=clamp(t - 0.9))
    if S(131) > -50 and t > S(131):
        for sx in (-1, 1):
            glow(c, X + sx * 70, Y - 230, 170, XRAY, 0.4 * (0.6 + 0.4 * math.sin(t * 6)))
        kicker(c, t, S(131), d + 1, "NOBODY WATCHES THE LEGS", 540, 1010, 58)
    c.restore()


def movie_kick(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#1a1212")
    c.save(); stage(c, w, h)
    rect(c, 0, 920, 1080, 160, "#3a3a3a")
    fall = S(135) + 1.0 if S(135) > -50 else d * 0.6
    if t < fall:
        with xf(c, 540, 920): man(c, 0, 0, 0.85, "kick", t, "#0d0a0a", rim="#7a3a3a", big=1.0)
    else:
        k = ease_out(clamp((t - fall) / 0.5))
        with xf(c, 540 + 120 * k, 920, rot=80 * k): man(c, 0, 0, 0.85, "kick", t, "#0d0a0a", rim="#7a3a3a", big=1.0)
        impact(c, 900, 900, t, fall + 0.45, RED, 140)
    kicker(c, t, 0.2, d + 1, "NO MOVIE KICKS", 540, 160, 74)
    if S(134) > -50: x_over(c, 540, 400, 260, t, S(134))
    c.restore()


def low_kick(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#121417")
    c.save(); stage(c, w, h)
    ground = 960
    rect(c, 0, ground, 1080, 120, "#2c2c2c")
    curb = ground - 120
    line(c, 40, curb, 1040, curb, GOLD, 4, 0.8)
    text(c, "CURB HEIGHT", 160, curb - 16, 32, GOLD, align="left")
    # target leg (right): hip-knee
    hipx, hipy, kx, ky = 760, ground - 560, 780, ground - 280
    line(c, hipx, hipy, kx, ky, "#1b1b1b", 120); line(c, kx, ky, 790, ground, "#1b1b1b", 100)
    c.drawCircle(hipx, hipy - 40, 90, P("#1b1b1b"))
    mx, my = (hipx + kx) / 2 - 60, (hipy + ky) / 2
    reticle(c, mx, my, 40, t, RED, t0=0.6)
    label_line(c, t, 1.0, mx, my, 980, 220, "OUTSIDE THIGH", RED, 36, align="right") if False else None
    text(c, "HALFWAY: HIP ↔ KNEE", 540, 140, 54, "#ffffff", a=clamp(t - 0.8), shadow=0.6)
    # kicking shin swings
    cyc = (t * 0.8) % 1.0
    sw = math.sin(min(1, cyc / 0.35) * math.pi / 2) if cyc < 0.35 else max(0, 1 - (cyc - 0.35) / 0.25)
    with xf(c, 330, ground - 520):
        ang = lerp(25, -62, sw)
        with xf(c, 0, 0, rot=ang):
            line(c, 0, 0, 0, 260, "#5b4632", 100); line(c, 0, 260, 0, 500, "#7a5f45", 85)
            rrect(c, -50, 480, 130, 50, 20, "#222222")
    line(c, 260, ground - 520, 240, ground, "#4a3a2a", 95)
    if 0.33 < cyc < 0.42:
        impact(c, mx, my, t, t - (cyc - 0.33) / 0.8, "#ffffff", 120)
    kicker(c, t, 1.4, d + 1, "SHORT. HARD. FOOT BACK DOWN.", 540, 1050, 48, bar=RED)
    c.restore()


def dead_leg(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#141217")
    c.save(); stage(c, w, h)
    lx = 330
    line(c, lx, 200, lx + 20, 560, "#2a2622", 140); line(c, lx + 20, 560, lx + 30, 940, "#2a2622", 120)
    r = rng(int(t * 10))
    for i in range(7):
        y = r.uniform(250, 520); x = lx + r.uniform(-50, 60)
        p = poly([(x, y), (x + 20, y + 15), (x + 5, y + 25), (x + 30, y + 45)], close=False)
        c.drawPath(p, P(XRAY, 5, 0.9))
    glow(c, lx, 380, 180, XRAY, 0.35)
    text(c, "DEAD LEG", lx, 1020, 64, XRAY)
    items = [(143, "CAN'T CHASE YOU"), (144, "CAN'T PLANT HIS FEET"), (145, "BALANCE GONE")]
    for i, (si, s) in enumerate(items):
        t0 = S(si) if S(si) > -50 else 1 + i
        k = ease_out(at(t, t0, 0.4))
        if k <= 0: continue
        y = 330 + i * 170
        with xf(c, 470 + (1 - k) * 60, y, alpha=k):
            text(c, s, 90, 18, 40, "#ffffff", align="left")
            check_mark(c, 30, 0, 60, GREEN, prog=k)
    c.restore()


def fish_market(c, t, d, w, h, S):
    fill_shader(c, skia.Rect(0, 0, w, h), linear(0, 0, 0, h, ["#0b0d18", "#1b1220", "#150d0a"]))
    # tower silhouette
    tx = w * 0.78
    c.drawPath(poly([(tx - 50, h * 0.7), (tx - 20, h * 0.12), (tx + 20, h * 0.12), (tx + 50, h * 0.7)]), P("#06070c"))
    rect(c, tx - 70, h * 0.2, 140, 50, "#06070c"); glow(c, tx, h * 0.22, 120, "#ffd34d", 0.25)
    for i in range(int(w / 140) + 1):
        lantern(c, 70 + i * 140, 120 + (i % 2) * 30, 0.8, t, "#ff5a3c" if i % 3 else "#ffb347", "")
    rect(c, 0, h * 0.72, w, h * 0.28, "#140e0b")
    c.save(); stage(c, w, h)
    stamp(c, t, 0.3, 300, 300, "SHINSEKAI, OSAKA", RED, 44, rot=-4)
    stamp(c, t, 0.9, 740, 380, "SUMMER 1981", GOLD, 44, rot=3)
    # stall
    rect(c, 80, 760, 640, 40, "#5a3b22"); rect(c, 80, 800, 640, 200, "#3b2716")
    for i in range(5):
        with xf(c, 150 + i * 120, 745, rot=(i * 13) % 10 - 5):
            c.drawOval(skia.Rect(-50, -16, 50, 16), P("#b8c4cc")); c.drawPath(poly([(50, 0), (75, -18), (75, 18)]), P("#b8c4cc"))
    kick = (S(152) + 0.4) if S(152) > -50 else 99
    oldx = 420
    man(c, oldx, 1000, 0.5, "kick" if kick <= t < kick + 0.6 else "stand", t, "#0b0908", rim="#ffb347", big=0.9)
    rect(c, oldx - 50, 950, 40, 50, "#f2f2f2"); rect(c, oldx + 10, 950, 40, 50, "#f2f2f2")
    yx = 860 if t < kick + 0.3 else 860 + 20 * math.sin(t * 30) * math.exp(-(t - kick) * 3)
    man(c, yx, 1000, 0.6, "stand", t, "#151515", rim="#ff5a3c", big=1.15)
    impact(c, 760, 860, t, kick + 0.15, "#ffffff", 120)
    if S(156) > -50:
        kicker(c, t, S(156), d + 1, "HE WATCHES YOUR HANDS", 540, 140, 56, bar=None)
    if S(157) > -50:
        kicker(c, t, S(157), d + 1, "USE YOUR FEET", 540, 240, 80)
    c.restore()


def dinner(c, t, d, w, h, S):
    fill_shader(c, skia.Rect(0, 0, w, h), radial(w / 2, h / 2, max(w, h) * 0.6, ["#3a2414", "#070403"]))
    c.save(); stage(c, w, h)
    rrect(c, 200, 120, 680, 840, 30, "#4a2c18"); rrect(c, 200, 120, 680, 840, 30, "#1c0f07", stroke=10)
    r = rng(3)
    seats = [(200, 260), (200, 520), (200, 780), (880, 260), (880, 520), (880, 780)]
    for i, (x, y) in enumerate(seats):
        sx = -1 if x < 540 else 1
        c.drawCircle(x + sx * 90, y, 70, P("#0e0907"))
        # cups/plates
        c.drawCircle(x - sx * 110, y, 46, P("#e8e2d4")); c.drawCircle(x - sx * 110, y, 30, P("#cfc6b3"))
        # hands on table
        rrect(c, x - sx * 10 - 40, y - 60, 80, 40, 18, SKIN)
        rrect(c, x - sx * 10 - 40, y + 20, 80, 40, 18, SKIN)
    # end of table man with one hand hidden
    x, y = 540, 990
    c.drawCircle(x, y + 80, 80, P("#0e0907"))
    rrect(c, x - 110, y - 30, 80, 40, 18, SKIN)
    pul = 0.5 + 0.5 * math.sin(t * 5)
    if t > (S(166) if S(166) > -50 else 1.5):
        glow(c, x + 70, y + 10, 140, RED, 0.45 + 0.3 * pul)
        reticle(c, x + 70, y + 10, 34, t, RED, t0=S(166) if S(166) > -50 else 1.5)
    if S(164) > -50:
        kicker(c, t, S(164), d + 1, "FACES LIE.", 540, 470, 90, bar=None)
    if S(165) > -50:
        kicker(c, t, S(165), d + 1, "HANDS DON'T.", 540, 600, 90)
    c.restore()


def decide(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#121010")
    c.save(); stage(c, w, h)
    lowt = S(172) if S(172) > -50 else d * 0.5
    high = t < lowt
    man(c, 540, 1080, 1.0, "guard_high" if high else "stand", t, "#0d0b09", rim="#7a5a3a", big=1.25)
    if high:
        torso_anatomy(c, 540, 1080, 1.0, t, show=("liver", "plexus"))
        text(c, "HANDS HIGH", 540, 120, 70, GOLD, shadow=0.6)
        rect(c, 540 - 130, 1080 - 950, 260, 200, RED, 0.18)
        if S(170) > -50: kicker(c, t, S(170), lowt, "DON'T HIT THE WALL", 540, 240, 52)
        reticle(c, 540 - 120, 1080 - 250, 40, t, XRAY, t0=max(0, S(171) + 2))
    else:
        text(c, "HANDS LOW", 540, 120, 70, GOLD, shadow=0.6)
        jx, jy = 540 + 30, 1080 - 790
        reticle(c, jx, jy, 40, t, GREEN, t0=lowt + 0.5)
        if S(173) > -50: x_over(c, 540, 1080 - 880, 90, t, S(173) + 0.5)
        if S(175) > -50 and t > S(175):
            with xf(c, 860, 520, rot=-20): palm_shape(c, 0, 0, 0.6, SKIN, heel=1, t=t)
            label_line(c, t, S(175), jx, jy, 820, 380, "PALM → JAW", GREEN, 40, align="right")
        if S(177) > -50:
            kicker(c, t, S(177), d + 1, "TOO CLOSE? ELBOW", 540, 1010, 60)
    c.restore()


def musashi(c, t, d, w, h, S):
    bg_paper(c, w, h, t)
    c.save(); stage(c, w, h)
    # hanging scroll
    k = ease_out(clamp(t / 1.0))
    rect(c, 360, 60, 360, 30, "#3b2716")
    rect(c, 380, 90, 320, 760 * k, "#f4ecd8"); rect(c, 380, 90, 320, 760 * k, "#b59a6a", 0.0)
    c.drawRect(skia.Rect.MakeXYWH(380, 90, 320, 760 * k), P("#8a6f45", 4))
    if k > 0.5:
        text(c, "千日", 540, 330, 150, "#121212", "jp", a=clamp((t - 0.6) * 2))
        text(c, "万日", 540, 560, 150, RED, "jp", a=clamp((t - 1.3) * 2))
    rect(c, 360, 90 + 760 * k, 360, 30, "#3b2716")
    text(c, "MIYAMOTO MUSASHI", 540, 960, 46, "#3b2716", "serif", a=clamp(t - 0.5))
    if S(182) > -50:
        t1 = S(182) + 5.5
        k1 = pop(t, t1)
        if k1 > 0:
            with xf(c, 180, 380, s=k1): text(c, "1,000 DAYS", 0, 0, 52, "#121212"); text(c, "FORGE", 0, 60, 46, DIM)
        k2 = pop(t, t1 + 2.0)
        if k2 > 0:
            with xf(c, 900, 600, s=k2): text(c, "10,000", 0, 0, 56, RED); text(c, "POLISH", 0, 60, 46, DIM)
    if S(184) > -50:
        kicker(c, t, S(184), d + 1, "A FEW MINUTES A DAY", 540, 1040, 58)
    c.restore()


def law(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#10131a")
    c.save(); stage(c, w, h)
    # scales
    tilt = 8 * math.sin(t * 1.2)
    line(c, 200, 140, 200, 520, GOLD, 10); rect(c, 130, 520, 140, 16, GOLD)
    with xf(c, 200, 160, rot=tilt):
        line(c, -130, 0, 130, 0, GOLD, 8)
        for sx in (-1, 1):
            line(c, sx * 130, 0, sx * 100, 140, GOLD, 3); line(c, sx * 130, 0, sx * 160, 140, GOLD, 3)
            with xf(c, sx * 130, 140, rot=-tilt):
                c.drawPath(poly([(-60, 0), (60, 0), (40, 30), (-40, 30)]), P(GOLD))
    text(c, "NOT LEGAL ADVICE", 200, 620, 30, DIM)
    items = [(188, "FORCE FITS THE DANGER"), (189, "HE STOPS → YOU STOP"), (190, "GET FREE, NOT EVEN"), (191, "PEOPLE + LIGHT + CALL")]
    for i, (si, s) in enumerate(items):
        t0 = S(si) if S(si) > -50 else 0.5 + i
        k = ease_out(at(t, t0, 0.4))
        if k <= 0: continue
        y = 200 + i * 150
        with xf(c, 420 + (1 - k) * 80, y, alpha=k):
            rrect(c, 0, -55, 620, 100, 16, "#1c2230")
            check_mark(c, 55, -5, 50, GREEN, prog=k)
            text(c, s, 100, 12, 36, "#ffffff", align="left")
    if S(192) > -50:
        kicker(c, t, S(192), d + 1, "PRISON = KEPT GOING", 540, 900, 64)
    c.restore()


def cheat_sheet(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#131110")
    c.save(); stage(c, w, h)
    text(c, "HIS HANDS DECIDE", 540, 130, 72, GOLD, shadow=0.6, a=clamp(t * 3))
    rows = [(197, "HANDS HIGH", "PLEXUS · LIVER · LEG", XRAY), (198, "HANDS LOW", "PALM HEEL → JAW", GREEN),
            (199, "TOO CLOSE", "ELBOW", GOLD), (200, "NEVER", "BARE FIST TO HEAD", RED)]
    for i, (si, a_, b_, col) in enumerate(rows):
        t0 = S(si) if S(si) > -50 else 0.5 + i
        k = ease_out(at(t, t0, 0.4))
        if k <= 0: continue
        y = 300 + i * 170
        with xf(c, 540, y, s=0.9 + 0.1 * k, alpha=k):
            rrect(c, -480, -65, 960, 130, 20, "#1d1a17"); rrect(c, -480, -65, 18, 130, 9, col)
            text(c, a_, -430, 18, 46, col, align="left")
            text(c, b_, 440, 18, 44, "#ffffff", align="right")
    c.restore()


def homework(c, t, d, w, h, S):
    bg_dark(c, w, h, t, "#1a1611", light=(0.3, 0.1))
    c.save(); stage(c, w, h)
    # doorframe + cushion
    rect(c, 120, 120, 40, 900, "#6b4a2b"); rect(c, 480, 120, 40, 900, "#6b4a2b"); rect(c, 120, 100, 400, 40, "#6b4a2b")
    hit = (t * 1.3) % 1
    sq = 1 - 0.12 * math.exp(-hit * 8)
    with xf(c, 340, 560, sx=sq, sy=1):
        rrect(c, -110, -90, 220, 180, 40, "#b84a3a"); rrect(c, -110, -90, 220, 180, 40, "#6d2a20", stroke=5)
        line(c, -110, -50, 110, -50, "#d8d8d8", 16, 0.9); line(c, -110, 60, 110, 60, "#d8d8d8", 16, 0.9)
    text(c, "STOMACH HEIGHT", 340, 700, 30, GOLD)
    items = [(209, "10 PALM STRIKES", "turn your hips"), (210, "10 LOW KICKS", "no higher than a curb"), (212, "5 MIN / DAY", "for 1 week")]
    for i, (si, a_, b_) in enumerate(items):
        t0 = S(si) if S(si) > -50 else 0.5 + i
        k = pop(t, t0)
        if k <= 0: continue
        with xf(c, 800, 280 + i * 230, s=k):
            rrect(c, -230, -90, 460, 180, 22, "#221d17"); rrect(c, -230, -90, 460, 180, 22, GOLD, stroke=4)
            text(c, a_, 0, 0, 48, "#ffffff"); text(c, b_, 0, 55, 32, DIM, "semi")
    c.restore()


def endcard(c, t, d, w, h, S):
    fill_shader(c, skia.Rect(0, 0, w, h), radial(w / 2, h / 2, max(w, h) * 0.7, ["#1d1612", "#040302"]))
    koi_wave(c, w, h, t, 0.12, RED)
    c.save(); stage(c, w, h)
    k = pop(t, 0.3)
    with xf(c, 540, 240, s=k):
        rrect(c, -240, -60, 480, 120, 20, RED)
        text(c, "SUBSCRIBE", 0, 22, 60, "#ffffff")
    bell = 0.5 + 0.5 * math.sin(t * 12) if 0.8 < t % 4 < 1.6 else 0
    with xf(c, 830, 240, rot=12 * bell * math.sin(t * 30)):
        c.drawPath(poly([(-30, 25), (-24, -15), (0, -35), (24, -15), (30, 25)]), P(GOLD)); c.drawCircle(0, 33, 8, P(GOLD))
    tnext = S(220) if S(220) > -50 else 1.5
    k2 = pop(t, tnext)
    if k2 > 0:
        with xf(c, 540, 560, s=k2):
            rrect(c, -340, -170, 680, 340, 20, "#0e0c0b"); rrect(c, -340, -170, 680, 340, 20, GOLD, stroke=5)
            c.drawPath(poly([(-30, -40), (40, 0), (-30, 40)]), P("#ffffff", a=0.9))
            text(c, "WATCH NEXT", 0, -100, 34, GOLD)
            text(c, "THE NOODLE COOK", 0, 100, 44, "#ffffff")
            text(c, "VS MY BIGGEST ENFORCER", 0, 145, 32, DIM)
    if S(222) > -50:
        kicker(c, t, S(222), d + 1, "LOCK YOUR DOOR.", 540, 880, 64, bar=None)
    if S(223) > -50:
        kicker(c, t, S(223), d + 1, "LIVE LONG.", 540, 990, 80)
    c.restore()


# ============================================================ SHOT LIST
# (first sentence, layout, scene, kwargs)
#   A = avatar full, S = split (avatar | scene), P = scene + avatar PiP, B = scene only
SHOTS = [
    (0, "B", hook, {}),
    (1, "S", clinic, {}),
    (3, "P", eleven, {}),
    (6, "B", quote, dict(lines=("Your boys keep fighting", "with the smallest", "bones they own."), who="DR. ISHIKAWA")),
    (7, "S", palm_vs_fist, {}),
    (10, "S", head_question, {}),
    (11, "P", three_spots, {}),
    (12, "S", not_face, {}),
    (15, "A", None, dict(lower=("REIKO KURODA", "35 YEARS · YAKUZA"), kick=[(16, "35 YEARS"), (20, "NOW I TEACH YOU")])),
    (23, "S", forehead, {}),
    (30, "P", hand27, {}),
    (31, "S", boxer, {}),
    (33, "S", bones_age, {}),
    (35, "A", None, dict(kick=[(35, "THE WORST OUTCOME")])),
    (37, "B", curb_fall, {}),
    (39, "P", sannomiya, {}),
    (43, "S", walk_away, {}),
    (46, "A", None, dict(kick=[(49, "HANDS UP. CHIN DOWN."), (51, "AIM LOWER")])),
    (52, "B", title_card, dict(num="3", name="THE LIVER", jp="肝臓", col=RED)),
    (54, "S", liver_check, {}),
    (59, "P", armor_gap, {}),
    (62, "S", sit_down, {}),
    (65, "A", None, dict(kick=[(66, "YOU DON'T NEED A FIST")])),
    (67, "S", palm_elbow, {}),
    (68, "P", hip_turn, {}),
    (70, "S", windup, {}),
    (73, "P", through, {}),
    (77, "S", dojo_story, {}),
    (82, "B", coat_quote, {}),
    (84, "A", None, dict(kick=[(86, "FIND THE GAP")])),
    (87, "S", charge, {}),
    (90, "B", title_card, dict(num="2", name="SOLAR PLEXUS", jp="水月", col=GOLD)),
    (92, "S", plexus_find, {}),
    (98, "A", None, dict(kick=[(99, "DON'T BACK UP")])),
    (100, "P", charge_palm, {}),
    (104, "S", precision, {}),
    (109, "S", nurse, {}),
    (115, "B", quote, dict(lines=("I've been carrying", "a weapon for 40 years", "and nobody told me."), who="BERNICE, 74")),
    (116, "A", None, dict(kick=[(118, "SMALL HAND. BIG ANSWER.")])),
    (119, "S", charge, dict(label="THEY EXPECT YOU TO STEP BACK")),
    (121, "P", poll, {}),
    (126, "B", title_card, dict(num="1", name="THE LEG", jp="脚", col=XRAY)),
    (128, "S", eyes_up, {}),
    (132, "P", movie_kick, {}),
    (136, "S", low_kick, {}),
    (140, "S", dead_leg, {}),
    (147, "P", fish_market, {}),
    (158, "A", None, dict(kick=[(159, "IT IS HIS HANDS")])),
    (161, "S", dinner, {}),
    (168, "P", decide, {}),
    (179, "A", None, dict(kick=[(180, "YOU WILL NOT THINK")])),
    (182, "S", musashi, {}),
    (185, "P", law, {}),
    (195, "B", cheat_sheet, {}),
    (201, "A", None, dict(kick=[(202, "NEITHER."), (203, "I CHOOSE THE LEG")])),
    (207, "S", homework, {}),
    (213, "A", None, dict(kick=[(213, "COMMENT BELOW"), (216, "WHERE ARE YOU FROM?")])),
    (218, "P", endcard, {}),
]
