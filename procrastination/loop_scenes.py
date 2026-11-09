"""Timeline for "The Loop". Every time is read from timing.json (the female voiceover), so the edit
stays locked to the narration: cuts land on sentence starts, text hits land on the exact word."""
import json
import math
import os
import random

import skia

from kit import (W, H, C, P, xf, rrect, poly, line, linear, radial, fill_shader, clamp, lerp, smooth, ease_out,
                 back_out, at, window, mixhex, txt, tw, cached, blit, grain, vignette, tint, add_glow, light_cone,
                 shake, woman, big_head, walk_pose, mix_pose, POSES, phone, mug, book, laptop, alarm_clock, pan_egg,
                 calendar_page, lamp, thought_bubble, arrow_curve, draw_set, desk_front, chair, INK, EYE)

HERE = os.path.dirname(os.path.abspath(__file__))
SEGS = json.load(open(os.path.join(HERE, "timing.json")))
END = SEGS[-1]["end"] + 5.5


def T(i):
    return SEGS[i]["start"]


def E(i):
    return SEGS[i]["end"]


def wt(i, word, nth=0):
    """Start time of a word inside sentence i."""
    k = 0
    for w in SEGS[i]["words"]:
        if w["w"].lower().strip(".,?!:'").startswith(word.lower()):
            if k == nth:
                return w["s"]
            k += 1
    return T(i)


LAMP = (1250, 600, "#ffb36b")
BLUE = "#6fb6ff"
RED = "#e8343a"
GOLD = "#ffc46b"


# ------------------------------------------------------------------ text animation presets
def t_slam(c, t, t0, s, x, y, size, color="#ffffff", fam="bebas", out=None, track=0.02, glow_col=None):
    if t < t0 or (out and t > out + 0.25):
        return
    k = ease_out(at(t, t0, 0.22))
    sc = lerp(1.7, 1.0, k)
    a = clamp((t - t0) / 0.08) * (1 - clamp((t - out) / 0.25) if out else 1)
    with xf(c, x, y, sc):
        txt(c, s, 0, 0, size, fam, color, a=a, track=track, shadow=0.6, glow_col=glow_col, glow_a=0.7)


def t_rise(c, t, t0, s, x, y, size, fam="serif", color="#f3ece0", out=None, align="center", track=0.0, dur=0.6):
    if t < t0 or (out and t > out + 0.4):
        return
    k = ease_out(at(t, t0, dur))
    a = k * (1 - clamp((t - out) / 0.4) if out else 1)
    txt(c, s, x, y + 26 * (1 - k), size, fam, color, align=align, a=a, track=track, blur=8 * (1 - k), shadow=0.5)


def t_track(c, t, t0, s, x, y, size, fam="serif", color="#f3ece0", out=None, t1=0.25, t2=0.06, dur=2.2):
    if t < t0 or (out and t > out + 0.5):
        return
    k = ease_out(at(t, t0, dur))
    a = clamp((t - t0) / 0.6) * (1 - clamp((t - out) / 0.5) if out else 1)
    txt(c, s, x, y, size, fam, color, a=a, track=lerp(t1, t2, k), blur=10 * (1 - clamp((t - t0) / 0.7)), shadow=0.5)


def flash(c, t, t0, dur=0.25, col="#ffffff", a=0.8):
    if t0 <= t < t0 + dur:
        tint(c, col, a * (1 - (t - t0) / dur))


def dip(c, t, t0, t1, dur=0.35):
    """black dip around scene boundaries t0 (in) and t1 (out)."""
    a = max(1 - clamp((t - t0) / dur), clamp((t - (t1 - dur)) / dur))
    tint(c, "#000000", a)


def cam(c, t, t0, t1, z0=1.0, z1=1.08, cx=W / 2, cy=H / 2, drift=6.0, sh=0.0):
    u = smooth((t - t0) / max(0.01, t1 - t0))
    z = lerp(z0, z1, u)
    dx = drift * math.sin(t * 0.7) + shake(t, sh)[0]
    dy = drift * 0.6 * math.cos(t * 0.53) + shake(t, sh)[1]
    c.translate(cx + dx, cy + dy)
    c.scale(z, z)
    c.translate(-cx, -cy)


def floor_ring(c, cx, cy, rx, ry, t, col="#ff9a3c", a=1.0, prog=1.0, crack=0.0, w=10):
    if a <= 0:
        return
    p = skia.Path()
    n = 120
    for i in range(int(n * prog) + 1):
        th = i / n * 2 * math.pi
        x, y = cx + rx * math.cos(th), cy + ry * math.sin(th)
        (p.moveTo if i == 0 else p.lineTo)(x, y)
    gp = P(col, w * 3, 0.35 * a)
    gp.setImageFilter(skia.ImageFilters.Blur(18, 18))
    c.drawPath(p, gp)
    pe = P(col, w, a)
    if crack > 0:
        pe.setPathEffect(skia.DashPathEffect.Make([lerp(400, 30, crack), lerp(0, 60, crack)], t * 30))
    c.drawPath(p, pe)
    c.drawPath(p, P("#fff2dc", w * 0.3, a * 0.8 * (1 - crack)))


def floor_glow(c, cx, cy, rx, ry, col, a):
    fill_shader(c, skia.Rect(cx - rx * 1.6, cy - ry * 2, cx + rx * 1.6, cy + ry * 2),
                radial(cx, cy, rx * 1.4, [(col, a), (col, 0)]))


# ------------------------------------------------------------------ scenes
def sc_hook(c, t):
    """0 -> T2: dark open, phone-lit silhouette + kinetic serif (like the original's type stack)."""
    t0, t1 = 0.0, T(2)
    c.clear(C("#030304"))
    c.save()
    cam(c, t, t0, t1, 1.12, 1.0, 1300, 560)
    # her, hunched over phone in the dark, lit only by the screen
    fill_shader(c, skia.Rect(0, 0, W, H), radial(1340, 560, 700, [("#0d1a2c", 0.9), ("#000000", 0)]))
    hp = woman(c, 1300, 700, 2.0, "phone", "tired", t, look=(0.4, 0.8), rim=BLUE, light=(1500, 500, BLUE),
               shade=0.75)
    phone(c, hp[0] + 8, hp[1] - 38, 1.9, -18, 1.0, t)
    c.restore()
    # kinetic type stack (left)
    x = 150
    t_rise(c, t, wt(0, "if"), "If I had", x, 190, 70, "serifi", align="left", out=T(1) - 0.3)
    # timer 3:32
    if wt(0, "three") <= t < T(1) - 0.1:
        k = back_out(at(t, wt(0, "three"), 0.35))
        rem = 212 - int(max(0, t - wt(0, "three")) * 1)
        s = f"{rem // 60}:{rem % 60:02d}"
        with xf(c, x + 170, 420, k):
            txt(c, s, 0, 0, 190, "bebas", "#ffffff", align="center", a=clamp(k), shadow=0.6)
        txt(c, "MINUTES  ·  SECONDS", x + 170, 462, 22, "sans", "#9aa4b5", a=clamp(k) * 0.9, track=0.18)
    t_rise(c, t, wt(0, "to"), "to show", x, 560, 64, "serif", align="left", out=T(1) - 0.3)
    if wt(0, "you") <= t < T(1) - 0.1:
        t_slam(c, t, wt(0, "you"), "YOU", x + 330, 570, 110, "#ffffff", "serifb", out=T(1) - 0.35)
    t_rise(c, t, wt(0, "how"), "how to", x, 660, 64, "serifi", align="left", out=T(1) - 0.3)
    if t >= wt(0, "never"):
        k = ease_out(at(t, wt(0, "never"), 0.2))
        a = 1 - clamp((t - (T(1) - 0.35)) / 0.25)
        with xf(c, x + 330 + 40, 790, lerp(1.6, 1, k)):
            txt(c, "NEVER", -40, 0, 170, "bebas", RED, a=a * clamp(k * 3), track=0.03, glow_col=RED, glow_a=0.8)
        flash(c, t, wt(0, "never"), 0.18, RED, 0.25)
    t_rise(c, t, wt(0, "procrastinate"), "procrastinate again.", x, 880, 56, "serifi", align="left",
           out=T(1) - 0.3, color="#c9c1b4")
    # "all I'd say is..." : everything gone, a single line in the dark
    t_track(c, t, T(1) + 0.05, "all I'd say is…", W / 2, 560, 64, "serifi", out=T(2) - 0.3, t1=0.15, t2=0.04,
            dur=1.2)


def lemniscate(u, cx, cy, a, persp=0.42):
    s, co = math.sin(u), math.cos(u)
    d = 1 + s * s
    return cx + a * co / d, cy + a * s * co / d * 2 * persp


def sc_loop(c, t):
    """T2 -> T3: she walks an endless ∞ track; INFINITE LOOP; then the title card."""
    t0, t1 = T(2), T(3)
    ttl = E(2) + 0.25
    c.clear(C("#050407"))
    c.save()
    cam(c, t, t0, ttl, 1.25, 1.0, 960, 600)
    fill_shader(c, skia.Rect(0, 0, W, H), radial(960, 640, 1100, [("#1a1015", 1), ("#050407", 1)]))
    cx, cy, A = 960, 650, 720
    # track
    p = skia.Path()
    for i in range(241):
        x, y = lemniscate(i / 240 * 2 * math.pi, cx, cy, A)
        (p.moveTo if i == 0 else p.lineTo)(x, y)
    gp = P("#ff8a3c", 40, 0.25); gp.setImageFilter(skia.ImageFilters.Blur(22, 22)); c.drawPath(p, gp)
    c.drawPath(p, P("#ff9a4a", 9, 0.95))
    c.drawPath(p, P("#fff0d8", 3, 0.8))
    # flowing light pulses along the loop
    for k in range(6):
        u = (t * 0.6 + k / 6) * 2 * math.pi
        x, y = lemniscate(u, cx, cy, A)
        add_glow(c, x, y, 60, "#ffd3a0", 0.6)
    # her walking the loop
    u = (t - t0) * 0.42 + 2.2
    x, y = lemniscate(u, cx, cy, A)
    x2, _ = lemniscate(u + 0.01, cx, cy, A)
    face = 1 if x2 > x else -1
    woman(c, x, y - 150 * 0.62, 0.62, walk_pose(t, 1.5), "tired", t, face=face, rim="#ffb36b",
          light=(x, y + 200, "#ff9a3c"), shade=0.5)
    c.restore()
    t_slam(c, t, wt(2, "infinite"), "INFINITE", W / 2, 300, 170, "#ffffff", out=ttl - 0.1, track=0.06)
    t_slam(c, t, wt(2, "loop"), "LOOP", W / 2, 460, 170, "#ff9a4a", out=ttl - 0.1, track=0.06, glow_col="#ff7a2a")
    t_rise(c, t, wt(2, "trapped"), "trapped in", W / 2, 120, 50, "serifi", out=ttl - 0.2)
    flash(c, t, wt(2, "loop"), 0.2, "#ffb36b", 0.35)
    # ---- title card
    if t >= ttl:
        tint(c, "#000000", clamp((t - ttl) / 0.25))
        k = t - ttl
        # light sweep
        sx = lerp(-300, W + 300, clamp(k / 2.2))
        a = clamp(k / 0.5) * (1 - clamp((t - (t1 - 0.5)) / 0.5))
        c.save()
        txt(c, "THE  LOOP", W / 2, 600, 230, "bebas", "#1d1a1e", a=a, track=lerp(0.35, 0.12, ease_out(clamp(k / 3))))
        sp = skia.Paint(Shader=linear(sx - 260, 0, sx + 260, 0, [("#ffffff", 0), ("#ffe0b8", 1), ("#ffffff", 0)]))
        c.saveLayer(None, None)
        txt(c, "THE  LOOP", W / 2, 600, 230, "bebas", "#ffffff", a=a, track=lerp(0.35, 0.12, ease_out(clamp(k / 3))))
        sp.setBlendMode(skia.BlendMode.kSrcIn)
        c.drawRect(skia.Rect(0, 0, W, H), sp)
        c.restore()
        txt(c, "THE  LOOP", W / 2, 600, 230, "bebas", "#e8e1d4", a=a * clamp((k - 1.2) / 1.0),
            track=lerp(0.35, 0.12, ease_out(clamp(k / 3))))
        c.restore()
        line(c, W / 2 - 260 * ease_out(clamp((k - 0.6) / 1.2)), 650, W / 2 + 260 * ease_out(clamp((k - 0.6) / 1.2)),
             650, RED, 4, a)
        txt(c, "WHY YOU KEEP PUTTING IT OFF", W / 2, 710, 30, "sans", "#a59c90", a=a * clamp((k - 1.0) / 0.8),
            track=0.3)


def sc_night(c, t):
    """T3 -> T5: lying in bed, making promises to herself; TOMORROW."""
    t0, t1 = T(3), T(5)
    c.save()
    cam(c, t, t0, t1, 1.0, 1.12, 700, 560)
    draw_set(c, "bedroom", 7)
    add_glow(c, 1310, 520, 560, "#ff9a2e", 0.35)
    lamp(c, 1310, 650, 0.9, 1.0)
    woman(c, 650, 560, 1.25, "lie", "soft" if t < wt(3, "forgotten") else "sad", t, rot=-90, look=(0.3, -1),
          rim="#ffb36b", light=(1310, 500, "#ffb36b"), shadow=False)
    # blanket over legs
    bp = skia.Path()
    bp.moveTo(560, 500); bp.cubicTo(700, 470, 1000, 480, 1160, 520); bp.lineTo(1160, 660); bp.lineTo(540, 660)
    bp.close()
    c.drawPath(bp, P("#6d5f5f"))
    fill_shader(c, skia.Rect(540, 470, 1160, 660), linear(1160, 480, 540, 660, [("#ffb36b", 0.25), ("#000000", 0.5)]))
    c.restore()
    # promises: thought bubble list
    tb0 = wt(3, "promises")
    if t >= tb0 - 0.2:
        k = back_out(at(t, tb0 - 0.2, 0.5))
        fade = 1.0
        forg = wt(3, "forgotten")
        thought_bubble(c, 560, 230, 760, 300, a=clamp(k) * 0.95, s=k, tail=(1, 1))
        items = ["Read 20 pages", "Start the project", "No phone after 11"]
        for i, it in enumerate(items):
            ti = tb0 + 0.25 + i * 0.45
            ki = ease_out(at(t, ti, 0.35))
            # promises crumble on "tomorrow comes" (handled by the next scene); here they wobble
            y = 160 + i * 78
            rrect(c, 290, y - 38, 42, 42, 7, "#1d1a1e", a=ki * fade, stroke=5)
            txt(c, it, 355, y, 54, "serifb", "#1d1a1e", align="left", a=ki * fade)
            if t > E(4) - 0.6:
                pass
    # "tomorrow" calendar page drops in
    tm = wt(4, "tomorrow")
    if t >= tm - 0.1:
        k = ease_out(at(t, tm - 0.1, 0.4))
        calendar_page(c, 1560, lerp(-300, 620, k), 0.9, lerp(-20, 6, k), "TOMORROW", "?", RED)
        if t > tm + 0.3:
            # stamp
            ks = back_out(at(t, tm + 0.3, 0.25))
            with xf(c, 1560, 640, lerp(2.0, 1.0, ks), rot=-14, alpha=clamp(ks * 2)):
                rrect(c, -170, -50, 340, 100, 10, RED, stroke=8)
                txt(c, "I PROMISE", 0, 30, 76, "bebas", RED, track=0.06)
    t_rise(c, t, wt(4, "swore"), "“I swear I'll finally do it…”", 520, 980, 50, "serifi", out=t1 - 0.3)


def sc_morning(c, t):
    """T5 -> T8: tomorrow comes (alarm), nothing's changed, same old comfortable routine (looping montage)."""
    t0, t1 = T(5), T(8)
    tc = wt(5, "comes")
    if t < T(6):
        # alarm close-up, morning light, promises falling apart as text dust
        c.clear(C("#0d0a08"))
        c.save()
        cam(c, t, t0, T(6), 1.0, 1.15, 960, 560)
        fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, W, H, ["#3a2a1c", "#120c08"]))
        light_cone(c, 1700, -100, 40, 18, 1600, "#ffd59a", 0.35)
        c.drawRect(skia.Rect(0, 760, W, H), P("#1a120c"))
        alarm_clock(c, 960, 600, 1.9, t, ring=1.0 if t > tc - 0.1 else 0.0, hhmm=(7, 0))
        c.restore()
        t_slam(c, t, tc - 0.05, "7:00 AM", W / 2, 190, 120, "#ffffff", out=T(6) - 0.15)
        flash(c, t, tc - 0.05, 0.2, "#fff2d0", 0.5)
        return
    # routine montage: hard cuts that repeat (deja vu). Day label increments while nothing changes.
    shots = ["egg", "coffee", "desk"]
    local = t - T(6)
    seg = 0.95
    i = int(local / seg)
    kind = shots[i % 3]
    day = 1 + i // 3
    lt = (local % seg) / seg
    c.save()
    cam(c, lt, 0, 1, 1.0, 1.06, 960, 540)
    if kind == "egg":
        c.clear(C("#120d0a"))
        fill_shader(c, skia.Rect(0, 0, W, H), radial(960, 540, 900, ["#3d2a1d", "#0f0a07"]))
        pan_egg(c, 900, 560, 1.6, t)
    elif kind == "coffee":
        draw_set(c, "room", 10)
        tint(c, "#000000", 0.35)
        desk_front(c, 820, 0, W)
        mug(c, 960, 820, 2.4, t)
        # pour stream
        pth = skia.Path(); pth.moveTo(1040, 0); pth.cubicTo(1010, 300, 975, 450, 965, 690)
        c.drawPath(pth, P("#3a2416", 12, 0.95))
    else:
        draw_set(c, "room", 7)
        lamp(c, 1300, 770, 0.8)
        chair(c, 860, 640, 1.3)
        hp = woman(c, 880, 630, 1.25, "sitphone", "bored", t, look=(0.4, 0.8), light=(1300, 600, "#ffb36b"))
        phone(c, hp[0], hp[1] - 25, 1.2, -20, 1.0, t)
        desk_front(c, 780, 980, 1700)
        mug(c, 1150, 780, 1.0, t)
    c.restore()
    # repetition label
    txt(c, f"DAY {day}", 110, 140, 64, "bebas", "#ffffff", align="left", a=0.9, track=0.08, shadow=0.6)
    line(c, 110, 160, 110 + 130, 160, RED, 4, 0.9)
    t_rise(c, t, T(6), "Nothing's changed.", W / 2, 960, 60, "serifi", out=T(7) - 0.2)
    t_track(c, t, wt(7, "same"), "SAME  OLD  ROUTINE", W / 2, 960, 64, "bebas", "#ffffff", out=t1 - 0.2,
            t1=0.4, t2=0.12, dur=1.5)
    if (local % seg) < 0.05:
        tint(c, "#ffffff", 0.08)


def sc_droste(c, t):
    """T8 -> T9: the room contains the room contains the room... psychological loop."""
    t0, t1 = T(8), T(9)
    K = 3.2
    u = ((t - t0) * 0.32) % 1.0
    zoom = K ** u
    fx, fy, fw, fh = 1040, 300, 300, 180  # inset frame (a picture on the wall)
    c.clear(C("#000000"))

    def content(cc, depth):
        draw_set(cc, "room", 7)
        lamp(cc, 1500, 770, 0.8)
        chair(cc, 680, 640, 1.3)
        hp = woman(cc, 700, 630, 1.25, "sitphone", "tired", t + depth * 0.37, look=(0.4, 0.8),
                   light=(1500, 600, "#ffb36b"))
        phone(cc, hp[0], hp[1] - 25, 1.2, -20, 1.0, t)
        desk_front(cc, 780, 300, 1750)
        rrect(cc, fx - 14, fy - 14, fw + 28, fh + 28, 4, "#120a08")

    # simpler, exact construction: compose recursively from the inside out
    def draw_level(cc, n):
        content(cc, n)
        if n < 4:
            cc.save()
            cc.clipRect(skia.Rect(fx, fy, fx + fw, fy + fh))
            cc.translate(fx, fy)
            cc.scale(fw / W, fh / H)
            draw_level(cc, n + 1)
            cc.restore()
        else:
            cc.drawRect(skia.Rect(fx, fy, fx + fw, fy + fh), P("#000000"))

    # fixed point of mapping p -> f + p*(fw/W): p* = f / (1 - fw/W)
    rx, ry = fw / W, fh / H
    px, py = fx / (1 - rx), fy / (1 - ry)
    c.save()
    c.translate(px, py)
    c.scale((1 / rx) ** u, (1 / ry) ** u)
    c.translate(-px, -py)
    draw_level(c, 0)
    c.restore()
    tint(c, "#1a0606", 0.15)
    t_slam(c, t, wt(8, "trap"), "TRAPPED", W / 2, 200, 130, "#ffffff", out=t1 - 0.2, track=0.08)
    t_track(c, t, wt(8, "psychological"), "AN INFINITE PSYCHOLOGICAL LOOP", W / 2, 960, 54, "bebas", "#ffb36b",
            out=t1 - 0.2, t1=0.3, t2=0.1, dur=1.6)


# ---- cycle diagram on the cutting mat
NODES = [((960, 240), "DIFFICULT TASK", "1"), ((1420, 540), "DISCOMFORT", "2"), ((960, 850), "AVOID", "3"),
         ((500, 540), "RELIEF", "4")]


def card(c, x, y, label, num, t, t0, rot=0.0, hi=0.0):
    if t < t0:
        return
    k = ease_out(at(t, t0, 0.45))
    lift = 1 - k
    sh = P("#000000", a=0.45)
    sh.setImageFilter(skia.ImageFilters.Blur(6 + 30 * lift, 6 + 30 * lift))
    s = 1 + 0.35 * lift
    with xf(c, x + 14 + 50 * lift, y + 18 + 60 * lift, s, rot + 8 * lift):
        c.drawRect(skia.Rect(-tw(label, 72) / 2 - 70, -60, tw(label, 72) / 2 + 40, 60), sh)
    with xf(c, x, y - 40 * lift, s, rot + 8 * lift, alpha=clamp(k * 3)):
        w = tw(label, 72) / 2 + 40
        rrect(c, -w - 40, -58, 2 * w + 40, 116, 6, "#f4efe4")
        fill_shader(c, skia.Rect(-w - 40, -58, w, 58), linear(0, -58, 0, 58, [("#ffffff", 0.0), ("#000000", 0.08)]))
        txt(c, num + ".", -w - 6, 28, 72, "bebas", "#c0392b")
        txt(c, label, 22 - 10, 28, 72, "bebas", "#1d1a1e")
        if hi > 0:
            rrect(c, -w - 50, -68, 2 * w + 60, 136, 10, "#ffcf3a", a=hi, stroke=8)


def mat_arrows(c, t, starts, col="#ffcf3a"):
    pts = [n[0] for n in NODES]
    for i, st in enumerate(starts):
        if st is None or t < st:
            continue
        a, b = pts[i], pts[(i + 1) % 4]
        k = ease_out(at(t, st, 0.5))
        # shorten
        def sh(p, q, d):
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            return p[0] + (q[0] - p[0]) * d / L, p[1] + (q[1] - p[1]) * d / L
        p1 = sh(a, b, 190)
        p2 = sh(b, a, 190)
        arrow_curve(c, p1[0], p1[1], p2[0], p2[1], -90, col, 10, 1.0, k)


def mat_base(c, t, t0, t1, z0=1.0, z1=1.06, cx=960, cy=540):
    c.save()
    cam(c, t, t0, t1, z0, z1, cx, cy, drift=3)
    draw_set(c, "mat", 0)
    add_glow(c, 1700, 100, 900, "#ffb36b", 0.25)


def sc_cycle1(c, t):
    """T9 -> T12: card 1 DIFFICULT TASK + book & project."""
    t0, t1 = T(9), T(12)
    mat_base(c, t, t0, t1, 1.25, 1.12, 960, 300)
    card(c, 960, 240, "DIFFICULT TASK", "1", t, wt(9, "difficult") - 0.1, -2)
    if t >= wt(10, "book"):
        k = ease_out(at(t, wt(10, "book") - 0.15, 0.4))
        book(c, lerp(400, 640, k), lerp(900, 520, k), 1.0, lerp(-40, -8, k))
    if t >= wt(11, "project"):
        k = ease_out(at(t, wt(11, "project") - 0.15, 0.4))
        with xf(c, lerp(1600, 1280, k), lerp(900, 600, k), 1.0, lerp(30, 6, k)):
            rrect(c, -150, -110, 300, 220, 8, "#e9e4d8")
            for r_ in range(5):
                line(c, -120, -70 + r_ * 34, 100 - (r_ * 47) % 90, -70 + r_ * 34, "#8e8676", 6)
            txt(c, "PROJECT", 0, -80, 34, "bebas", "#c0392b") if False else None
            rrect(c, -150, -110, 300, 46, 8, "#3a5f8a")
            txt(c, "NEW PROJECT", 0, -76, 34, "bebas", "#ffffff", track=0.05)
    c.restore()


def sc_discomfort(c, t):
    """T12 -> T14: card 2, then emotional close-up: boredom / frustration / fear."""
    t0, t1 = T(12), T(14)
    if t < T(13):
        mat_base(c, t, t0, T(13), 1.0, 1.04)
        book(c, 640, 520, 1.0, -8)
        card(c, 960, 240, "DIFFICULT TASK", "1", t, t0 - 5, -2)
        mat_arrows(c, t, [t0 + 0.1, None, None, None])
        card(c, 1420, 540, "DISCOMFORT", "2", t, wt(12, "discomfort") - 0.1, 3)
        c.restore()
        return
    # close-up of her face; words hit as emotions change
    c.save()
    cam(c, t, T(13), t1, 1.0, 1.1, 960, 480)
    draw_set(c, "room", 14)
    tint(c, "#000000", 0.35)
    wb, wf, wfe = wt(13, "boredom"), wt(13, "frustration"), wt(13, "fear")
    expr = "yawn" if t < wf else ("frustrated" if t < wfe else "worried")
    big_head(c, 960, 470, 165, expr, t, look=(0, 0.3), light=LAMP, tilt=-6 if t < wf else 0)
    c.restore()
    if t >= wfe:
        tint(c, "#000000", 0.35 * clamp((t - wfe) / 0.6))
        vignette(c, 0.6 * clamp((t - wfe) / 0.6))
    t_slam(c, t, wb, "BOREDOM", 360, 300, 110, "#d7d0c4", out=wf - 0.1)
    t_slam(c, t, wf, "FRUSTRATION", 1560, 300, 110, "#ff7a4a", out=wfe - 0.1)
    if t >= wfe:
        t_rise(c, t, wfe, "the fear of not knowing", W / 2, 900, 58, "serifi", out=t1 - 0.2)
        t_rise(c, t, wt(13, "where"), "where to begin.", W / 2, 970, 58, "serifi", out=t1 - 0.2, color="#ff9a7a")
        flash(c, t, wfe, 0.15, "#000000", 0.6)


def sc_avoid(c, t):
    """T14 -> T16: avoid (picks up phone), relief (warm exhale)."""
    t0, t1 = T(14), T(16)
    wp = wt(14, "picking")
    c.save()
    cam(c, t, t0, t1, 1.0, 1.14, 900, 470)
    draw_set(c, "room", 8)
    lamp(c, 1320, 770, 0.8)
    chair(c, 860, 640, 1.3)
    pk = smooth(at(t, wp - 0.1, 0.6))
    pose = mix_pose("sit", "sitphone", pk)
    relief = clamp((t - wt(15, "relief")) / 0.6)
    expr = "worried" if t < wp else ("neutral" if t < T(15) else ("smile_closed" if relief > 0.3 else "neutral"))
    glow_on = pk
    hp = woman(c, 880, 630, 1.25, pose, expr, t, look=(0.4, 0.8), light=(1320, 600, "#ffb36b"))
    if pk > 0.05:
        phone(c, hp[0], hp[1] - 25, 1.2, -20 * pk, glow_on, t)
    else:
        phone(c, 1060, 770, 1.0, 80, 0.0, t, feed=False)
    desk_front(c, 780, 980, 1700)
    book(c, 1200, 760, 0.6, 80)
    c.restore()
    if relief > 0:
        add_glow(c, 900, 420, 600, "#ffcf8a", 0.28 * relief)
        # exhale breath wisps
        for k in range(3):
            ph = clamp((t - wt(15, "relief") - k * 0.25) / 1.4)
            if 0 < ph < 1:
                with xf(c, 990 + ph * 120, 395 - ph * 40, 1 + ph):
                    c.drawCircle(0, 0, 20, P("#ffffff", a=0.18 * (1 - ph)))
    card_small = lambda s, n, x, y, t0_: card(c, x, y, s, n, t, t0_, 0)
    with xf(c, 0, 0, 1):
        if t >= wt(14, "avoid"):
            with xf(c, 1530, 200, 0.62):
                card(c, 0, 0, "AVOID", "3", t, wt(14, "avoid") - 0.05, -3)
        if t >= wt(15, "relief") - 0.1:
            with xf(c, 1530, 340, 0.62):
                card(c, 0, 0, "RELIEF", "4", t, wt(15, "relief") - 0.1, 2)


def sc_cycle_full(c, t):
    """T16 -> T18: relief teaches the brain -> arrow back to 1 -> spins, DAY AFTER DAY."""
    t0, t1 = T(16), T(18)
    spin_t = wt(17, "trapping")
    mat_base(c, t, t0, t1, 1.0, 1.0)
    # spin the whole diagram, accelerating
    sp = max(0.0, t - spin_t)
    ang = 22 * sp * sp + 40 * sp
    c.save()
    c.translate(960, 545); c.rotate(-ang); c.translate(-960, -545)
    book(c, 640, 360, 0.6, -8)
    for (p, lab, n), r in zip(NODES, (-2, 3, -3, 2)):
        card(c, p[0], p[1], lab, n, t, -10, r)
    mat_arrows(c, t, [-5, -5, -5, wt(16, "teaches") - 0.2])
    # brain in the centre
    if t > wt(16, "brain") - 0.1:
        k = back_out(at(t, wt(16, "brain") - 0.1, 0.45))
        with xf(c, 960, 545, k):
            c.drawCircle(0, 0, 120, P("#f4efe4"))
            for i in range(7):
                a = i * 0.9
                c.drawCircle(math.cos(a) * 45, math.sin(a) * 38, 46, P("#f2a3a8"))
            for i in range(7):
                a = i * 0.9 + 0.4
                p = skia.Path(); p.moveTo(math.cos(a) * 20, math.sin(a) * 18)
                p.quadTo(math.cos(a) * 70, math.sin(a) * 30, math.cos(a + 0.5) * 70, math.sin(a + 0.5) * 60)
                c.drawPath(p, P("#c9737a", 5))
    c.restore()
    # motion blur feel when fast: ghost frames
    if sp > 0.8:
        tint(c, "#000000", clamp((sp - 0.8) / 3) * 0.3)
    c.restore()
    # day counter
    if t >= wt(17, "day") - 0.2:
        n = int(1 + max(0, t - (wt(17, "day") - 0.2)) ** 2.4 * 40)
        txt(c, f"DAY {n}", W / 2, 140, 96, "bebas", "#ffffff", track=0.08, shadow=0.7)
    t_track(c, t, wt(17, "cycle"), "DAY  AFTER  DAY", W / 2, 980, 70, "bebas", "#ffcf3a", out=t1 - 0.2, t1=0.4,
            t2=0.14, dur=2.0)


def sc_breakfree(c, t):
    """T18 -> T22: alone on the glowing ring; ANOTHER DAY / MONTH / YEAR."""
    t0, t1 = T(18), T(22)
    c.clear(C("#040405"))
    c.save()
    cam(c, t, t0, t1, 1.0, 1.22, 960, 600)
    draw_set(c, "studio", 0)
    light_cone(c, 960, -200, 0, 13, 1300, "#ffe6c4", 0.22)
    floor_glow(c, 960, 800, 520, 150, "#ff8a3c", 0.25)
    floor_ring(c, 960, 800, 520, 150, t)
    # she walks the ring
    th = (t - t0) * 0.55 + 1.2
    x, y = 960 + 520 * math.cos(th), 800 + 150 * math.sin(th)
    depth = 0.86 + 0.12 * math.sin(th)
    face = -1 if math.sin(th) > 0 else 1
    woman(c, x, y - 190 * depth, depth, walk_pose(t, 1.3), "tired", t, face=face, rim="#ffb36b",
          light=(960, 800, "#ff9a3c"), shade=0.5)
    c.restore()
    if t > T(19):
        rnd = random.Random(4)
        for k in range(26):
            st = T(19) + rnd.uniform(0, t1 - T(19) - 0.5)
            ph = (t - st) / 1.6
            if 0 < ph < 1:
                x = rnd.uniform(0, W) + ph * rnd.uniform(-300, 300)
                y = -200 + ph * (H + 400)
                calendar_page(c, x, y, 0.35, rnd.uniform(-60, 60) + ph * rnd.uniform(-180, 180), "DAY",
                              str(rnd.randint(1, 31)), RED, a=0.85)
    t_rise(c, t, wt(18, "break"), "How do you break free?", W / 2, 150, 72, "serifi", out=T(19) - 0.1)
    # calendar pages flying + slams
    hits = [(T(19), "ANOTHER DAY", 1.0), (T(20), "ANOTHER MONTH", 1.15), (T(21), "ANOTHER YEAR", 1.35)]
    for i, (th_, s, sc) in enumerate(hits):
        nxt = hits[i + 1][0] if i < 2 else t1 - 0.3
        if th_ <= t < nxt + 0.05:
            t_slam(c, t, th_, s, W / 2, 230, 130 * sc, "#ffffff" if i < 2 else RED, out=nxt - 0.05, track=0.05)
            flash(c, t, th_, 0.15, "#ffffff", 0.25 + 0.15 * i)


def sc_slowdown(c, t):
    """T22 -> T23: everything slows; she stops and looks at the pattern of her own footprints."""
    t0, t1 = T(22), T(23)
    tf = wt(22, "slow")
    slow = clamp((t - tf) / 1.2)
    c.clear(C("#040405"))
    c.save()
    cam(c, t, t0, t1, 1.22, 1.0, 960, 640)
    draw_set(c, "studio", 0)
    light_cone(c, 960, -200, 0, 13, 1300, "#ffe6c4", 0.22)
    floor_glow(c, 960, 800, 520, 150, "#ff8a3c", 0.22)
    floor_ring(c, 960, 800, 520, 150, t, col=mixhex("#ff8a3c", "#9fc6ff", slow))
    # footprints worn into the ring
    for k in range(40):
        th = k / 40 * 2 * math.pi
        x, y = 960 + 520 * math.cos(th), 800 + 150 * math.sin(th)
        c.drawOval(skia.Rect(x - 9, y - 4, x + 9, y + 4), P("#000000", a=0.55 * clamp((t - wt(22, "pattern")) / 0.8)))
    # she decelerates to a stop (time is ~ integral of speed)
    tt_ = t0 + (min(t, tf) - t0) + (1 - math.exp(-max(0, t - tf) * 1.8)) / 1.8
    th = (tt_ - T(18)) * 0.55 + 1.2
    x, y = 960 + 520 * math.cos(th), 800 + 150 * math.sin(th)
    depth = 0.86 + 0.12 * math.sin(th)
    face = -1 if math.sin(th) > 0 else 1
    pose = mix_pose(walk_pose(tt_, 1.3), "stand", slow)
    look = (0.2, lerp(0, 1, clamp((t - wt(22, "recognize")) / 0.6)))
    woman(c, x, y - 190 * depth, depth, pose, "focus" if slow > 0.5 else "tired", t, face=face, look=look,
          rim=mixhex("#ffb36b", "#9fc6ff", slow), light=(960, 800, mixhex("#ff9a3c", "#9fc6ff", slow)), shade=0.5)
    # dust motes slowing/freezing
    rnd = random.Random(8)
    for k in range(60):
        x0, y0 = rnd.uniform(0, W), rnd.uniform(0, H)
        v = rnd.uniform(20, 60) * (1 - slow * 0.97)
        c.drawCircle(x0, (y0 + tt_ * v) % H, rnd.uniform(1, 3), P("#ffe6c4", a=0.4))
    c.restore()
    if slow > 0:
        tint(c, "#0a1630", 0.25 * slow, skia.BlendMode.kColor)
    t_track(c, t, tf, "SLOW  DOWN", W / 2, 200, 120, "bebas", "#ffffff", out=t1 - 0.2, t1=0.6, t2=0.25, dur=2.5)
    t_rise(c, t, wt(22, "recognize"), "recognize the pattern you're stuck in.", W / 2, 1000, 50, "serifi",
           out=t1 - 0.2)


def sc_meta(c, t):
    """T23 -> T25: METACOGNITION title, then thinking about your thinking (recursive heads)."""
    t0, t1 = T(23), T(25)
    c.clear(C("#060608"))
    fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, 1000, ["#141826", "#050507"]))
    tm = wt(23, "metacognition")
    if t < T(24) + 0.2:
        k = t - tm
        a = clamp(k / 0.4) * (1 - clamp((t - T(24) - 0.0) / 0.25))
        word = "METACOGNITION"
        n = int(clamp(k / 1.0) * len(word) + 0.999)
        full_w = tw(word, 190, "serif", 0.06)
        x = W / 2 - full_w / 2
        f = 0
        for i, ch in enumerate(word):
            ki = ease_out(clamp((k - i * 0.06) / 0.5))
            txt(c, ch, x, 600 - 30 * (1 - ki), 190, "serif", "#f3ece0", align="left", a=a * ki, blur=6 * (1 - ki))
            x += tw(ch, 190, "serif") + 0.06 * 190
        line(c, W / 2 - 400 * ease_out(clamp((k - 0.6) / 0.8)), 650, W / 2 + 400 * ease_out(clamp((k - 0.6) / 0.8)),
             650, "#9fc6ff", 3, a)
        txt(c, "meta · cog · ni · tion   (noun)", W / 2, 720, 38, "serifi", "#8a93a6", a=a * clamp((k - 0.8) / 0.6))
        return
    # thinking about your thinking: a thought bubble that contains her thinking, that contains... (seamless zoom)
    k = t - T(24)
    u = (k * 0.38) % 1.0
    bx, by, bw, bh = 1060, 150, 640, 360          # bubble window rect (16:9)
    r = bw / W

    def lvl(cc, n):
        fill_shader(cc, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, 1000, ["#141826", "#050507"]))
        big_head(cc, 640, 600, 150, "focus", t + n * 0.37, look=(0.7, -0.7), rim="#9fc6ff",
                 light=(1400, 200, "#9fc6ff"))
        for j, rr in enumerate((22, 14, 9)):
            cc.drawCircle(980 - j * 44, 560 - j * 46 + 40, rr, P("#cfe4ff", 4, 0.9))
        rr_ = skia.RRect.MakeRectXY(skia.Rect(bx, by, bx + bw, by + bh), 60, 60)
        if n < 3:
            cc.save()
            cc.clipRRect(rr_, doAntiAlias=True)
            cc.translate(bx, by); cc.scale(r, r)
            lvl(cc, n + 1)
            cc.restore()
        gp = P("#cfe4ff", 18, 0.25); gp.setImageFilter(skia.ImageFilters.Blur(14, 14))
        cc.drawRRect(rr_, gp)
        cc.drawRRect(rr_, P("#cfe4ff", 5, 0.95))

    px, py = bx / (1 - r), by / (1 - r)
    c.save()
    c.translate(px, py); c.scale((1 / r) ** u, (1 / r) ** u); c.translate(-px, -py)
    lvl(c, 0)
    c.restore()
    t_rise(c, t, wt(24, "thinking"), "thinking about", W / 2, 920, 66, "serifi", out=t1 - 0.2)
    t_slam(c, t, wt(24, "your", 1), "YOUR THINKING", W / 2, 1010, 76, "#9fc6ff", out=t1 - 0.2, track=0.08)


def sc_examine(c, t):
    """T25 -> T27: magnifying glass over her excuses."""
    t0, t1 = T(25), T(27)
    c.save()
    cam(c, t, t0, t1, 1.0, 1.1, 760, 520)
    draw_set(c, "room", 9)
    tint(c, "#000000", 0.3)
    lamp(c, 1500, 770, 0.8)
    chair(c, 560, 640, 1.3)
    hp = woman(c, 580, 630, 1.25, "sitphone", "neutral", t, look=(0.4, 0.8), light=(1500, 600, "#ffb36b"))
    phone(c, hp[0], hp[1] - 25, 1.2, -20, 1.0, t)
    desk_front(c, 780, 700, 1800)
    c.restore()
    thoughts = ["“I'll do it later.”", "“Just five minutes.”", "“I'm not in the mood.”"]
    tx = wt(26, "examine")
    kb = back_out(at(t, T(26) - 0.2, 0.5))
    if t > T(26) - 0.2:
        thought_bubble(c, 1250, 330, 760, 330, a=clamp(kb), s=kb, tail=(-1, 1))
        for i, th in enumerate(thoughts):
            ki = ease_out(at(t, T(26) + 0.1 + i * 0.5, 0.4))
            txt(c, th, 1250, 250 + i * 80, 52, "serifi", "#1d1a1e", a=ki)
    if t > tx - 0.3:
        km = ease_out(at(t, tx - 0.3, 0.7))
        mx = lerp(1900, 1250 + 120 * math.sin((t - tx) * 1.3), km)
        my = lerp(900, 320 + 60 * math.cos((t - tx) * 1.1), km)
        # lens magnifies (draw scaled text again inside a circle)
        c.save()
        pth = skia.Path(); pth.addCircle(mx, my, 120)
        c.clipPath(pth, doAntiAlias=True)
        c.drawCircle(mx, my, 120, P("#fbf6ea"))
        c.translate(mx, my); c.scale(1.6, 1.6); c.translate(-mx, -my)
        for i, th in enumerate(thoughts):
            txt(c, th, 1250, 250 + i * 80, 52, "serifi", "#1d1a1e")
        c.restore()
        c.drawCircle(mx, my, 120, P("#2a2526", 16))
        c.drawCircle(mx, my, 120, P("#d9d2c4", 4))
        line(c, mx + 88, my + 88, mx + 210, my + 210, "#2a2526", 30)
        c.drawCircle(mx - 50, my - 55, 22, P("#ffffff", a=0.35))
    t_rise(c, t, wt(25, "already"), "You already know when you're procrastinating.", W / 2, 990, 46, "serifi",
           out=T(26) - 0.1)


DECISION_ICONS = ["mug", "egg", "shirt", "phone", "book", "clock", "laptop", "bed", "door", "food"]


def mini_icon(c, kind, x, y, s, t):
    with xf(c, x, y, s):
        c.drawCircle(0, 0, 46, P("#f4efe4"))
        col = "#1d1a1e"
        if kind == "mug":
            rrect(c, -18, -18, 30, 36, 6, col); c.drawCircle(16, 0, 9, P(col, 5))
        elif kind == "egg":
            c.drawCircle(0, 0, 26, P("#ffffff")); c.drawCircle(0, 0, 26, P(col, 3)); c.drawCircle(4, -3, 11, P("#f0a51c"))
        elif kind == "shirt":
            c.drawPath(poly([(-26, -18), (-10, -26), (10, -26), (26, -18), (20, -4), (12, -8), (12, 26), (-12, 26),
                             (-12, -8), (-20, -4)]), P(col))
        elif kind == "phone":
            rrect(c, -13, -24, 26, 48, 5, col); rrect(c, -9, -19, 18, 34, 3, BLUE)
        elif kind == "book":
            rrect(c, -20, -24, 40, 48, 4, "#7a2f2a")
        elif kind == "clock":
            c.drawCircle(0, 0, 24, P(col, 5)); line(c, 0, 0, 0, -15, col, 4); line(c, 0, 0, 11, 4, col, 4)
        elif kind == "laptop":
            rrect(c, -22, -18, 44, 28, 3, col); rrect(c, -28, 10, 56, 6, 2, col)
        elif kind == "bed":
            rrect(c, -26, -4, 52, 18, 4, col); rrect(c, -26, -16, 16, 14, 4, col)
        elif kind == "door":
            rrect(c, -16, -26, 32, 52, 3, col); c.drawCircle(8, 2, 3, P("#f4efe4"))
        else:
            c.drawOval(skia.Rect(-26, -6, 26, 20), P(col)); c.drawCircle(-6, -12, 8, P("#c0392b"))


def sc_decisions(c, t):
    """T27 -> T29: hundreds of automatic decisions (breakfast, sit down for work)."""
    t0, t1 = T(27), T(29)
    c.clear(C("#0b0a0d"))
    fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, 1100, ["#1d1714", "#070607"]))
    rnd = random.Random(21)
    tw0 = wt(27, "hundreds")
    cnt = 0
    for i in range(160):
        x, y = 120 + (i % 16) * 112 + rnd.uniform(-10, 10), 270 + (i // 16) * 82 + rnd.uniform(-8, 8)
        st = tw0 + i * 0.022 + rnd.uniform(0, 0.15)
        if t >= st:
            cnt += 1
            k = back_out(at(t, st, 0.3))
            fade = 0.75 if t > T(28) else 1.0
            mini_icon(c, DECISION_ICONS[i % len(DECISION_ICONS)], x, y, 0.62 * k, t)
            if t > T(28):
                tint(c, "#000000", 0)
    if t >= T(28):
        tint(c, "#000000", 0.78 * clamp((t - T(28)) / 0.4))
        # spotlight two decisions: breakfast + sitting down for work
        kb = back_out(at(t, wt(28, "breakfast") - 0.1, 0.4))
        kw = back_out(at(t, wt(28, "work") - 0.25, 0.4))
        with xf(c, 620, 600, kb):
            pan_egg(c, 0, 0, 0.9, t)
        txt(c, "BREAKFAST", 620, 880, 60, "bebas", "#ffffff", a=clamp(kb), track=0.1)
        if t >= wt(28, "work") - 0.25:
            with xf(c, 1300, 640, kw):
                laptop(c, 0, 60, 1.6)
            txt(c, "WORK", 1300, 880, 60, "bebas", "#ffffff", a=clamp(kw), track=0.1)
    n = int(min(247, cnt * 1.55))
    txt(c, f"{n}", W / 2, 130, 110, "bebas", "#ffcf3a", shadow=0.7)
    txt(c, "DECISIONS TODAY", W / 2, 190, 30, "sans", "#cfc6b8", track=0.3, a=0.9)
    t_rise(c, t, wt(27, "without"), "…without even thinking.", W / 2, 1010, 50, "serifi", out=T(28) - 0.1)


def sc_autopilot(c, t):
    """T29 -> T31: procrastination becomes automatic: her hand drifts to the phone on its own."""
    t0, t1 = T(29), T(31)
    c.save()
    cam(c, t, t0, t1, 1.0, 1.12, 860, 480)
    draw_set(c, "room", 8)
    lamp(c, 1320, 770, 0.8)
    laptop(c, 1130, 785, 0.9, 0.7)
    chair(c, 760, 640, 1.3)
    cyc = ((t - t0) % 2.6) / 2.6
    k = smooth(clamp(cyc * 2.2)) * (1 - smooth(clamp((cyc - 0.8) / 0.2)))
    pose = mix_pose("sit", "sitphone", k)
    hp = woman(c, 780, 630, 1.25, pose, "bored", t, look=(0.6 * (1 - k) + 0.4 * k, 0.3 + 0.5 * k),
               light=(1320, 600, "#ffb36b"))
    if k > 0.05:
        phone(c, hp[0], hp[1] - 25, 1.2, -20 * k, k, t)
    desk_front(c, 780, 900, 1700)
    c.restore()
    # autopilot HUD
    a = clamp((t - wt(29, "automatic")) / 0.3)
    if a > 0:
        rrect(c, 110, 110, 420, 90, 8, "#ff4747", a=a * (0.7 + 0.3 * math.sin(t * 6)), stroke=4)
        c.drawCircle(150, 155, 12, P("#ff4747", a=a * (0.5 + 0.5 * math.sin(t * 6))))
        txt(c, "AUTOPILOT: ON", 340, 172, 56, "bebas", "#ff4747", a=a, track=0.08)
    if t > T(30) - 0.1:
        items = ["Wake up", "Coffee", "Sit down", "Scroll"]
        for i, it in enumerate(items):
            ki = ease_out(at(t, T(30) + i * 0.25, 0.3))
            y = 330 + i * 70
            txt(c, it, 1560, y, 50, "serifb", "#f3ece0", align="left", a=ki)
            rrect(c, 1500, y - 36, 38, 38, 6, "#f3ece0", a=ki, stroke=4)
            if ki > 0.6:
                line(c, 1506, y - 18, 1516, y - 6, "#ffcf3a" if i < 3 else "#ff4747", 6)
                line(c, 1516, y - 6, 1536, y - 32, "#ffcf3a" if i < 3 else "#ff4747", 6)
    t_rise(c, t, wt(30, "routine"), "just another part of your routine.", W / 2, 1010, 50, "serifi", out=t1 - 0.1)


def sc_splitsecond(c, t):
    """T31 -> T33: attention. The hand freezes mid-reach. The split second."""
    t0, t1 = T(31), T(33)
    tf = wt(32, "split")
    frozen = clamp((t - (tf - 0.2)) / 0.4)
    if t < T(32):
        # close-up: eyes open into awareness
        c.save()
        cam(c, t, t0, T(32), 1.0, 1.15, 960, 470)
        draw_set(c, "room", 16)
        tint(c, "#000000", 0.45)
        k = clamp((t - wt(31, "attention")) / 0.5)
        big_head(c, 960, 470, 180, "tired" if k < 0.5 else "focus", t, look=(0.1, 0), light=(1400, 200, "#cfe4ff"),
                 rim="#cfe4ff")
        c.restore()
        add_glow(c, 960, 400, 700, "#9fc6ff", 0.15 * k)
        t_rise(c, t, wt(31, "pay"), "pay attention to your own thoughts.", W / 2, 1000, 52, "serifi", out=T(32) - 0.1)
        return
    # macro: hand reaching for the phone, freezes
    c.clear(C("#0b0908"))
    c.save()
    cam(c, t, T(32), t1, 1.0, 1.12, 1000, 600)
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#2a1a12", "#140c08"]))
    c.drawRect(skia.Rect(0, 650, W, H), P("#3b2618"))
    fill_shader(c, skia.Rect(0, 650, W, H), linear(0, 650, 0, H, [("#5a3a22", 0.8), ("#1a0f08", 1)]))
    add_glow(c, 1500, 400, 900, "#ff9a2e", 0.3)
    # phone on desk (perspective quad)
    ph = [(1230, 700), (1400, 690), (1450, 790), (1260, 805)]
    c.drawPath(poly([(x + 6, y + 10) for x, y in ph]), P("#000000", a=0.5))
    c.drawPath(poly(ph), P("#0c0c10"))
    ins = [(1240, 706), (1392, 697), (1438, 785), (1268, 797)]
    c.drawPath(poly(ins), P("#3b78b8"))
    add_glow(c, 1340, 720, 300, BLUE, 0.45)
    # arm: from bottom-left (foreshortened), reaching; progress freezes in the split second
    tt_ = min(t, tf - 0.2) + (1 - math.exp(-max(0, t - (tf - 0.2)) * 6)) / 6 * 0.15
    reach = clamp((tt_ - T(32)) / 2.4)
    e = ease_out(reach)
    hx = lerp(380, 1120, e)
    hy = lerp(900, 700, e)
    sl = skia.Path(); sl.moveTo(-60, H + 120); sl.cubicTo(150, 980, hx - 380, hy + 120, hx - 120, hy + 10)
    c.drawPath(sl, P("#111016", 196)); c.drawPath(sl, P("#c9b28f", 180))
    c.drawPath(sl, P("#9d8462", 40, 0.35))
    c.drawCircle(hx - 110, hy + 10, 70, P("#111016")); c.drawCircle(hx - 110, hy + 10, 64, P("#9d8462"))
    for kk in range(5):
        line(c, hx - 150 + kk * 14, hy - 40, hx - 160 + kk * 14, hy + 58, "#857052", 3, 0.6)
    with xf(c, hx - 30, hy + 4, 1.25, rot=-14):
        c.drawOval(skia.Rect(-60, -46, 60, 46), P(INK))
        for kk in range(4):
            ln = [62, 74, 70, 56][kk]
            with xf(c, 40, -36 + kk * 22, rot=(kk - 1.5) * 6 + 18 * (1 - e)):
                rrect(c, 0, -10, ln, 21, 10.5, INK)
        with xf(c, -10, -46, rot=-40):
            rrect(c, 0, -11, 58, 22, 11, INK)
        c.drawOval(skia.Rect(-40, -36, 10, -14), P("#ffffff", a=0.08))
    c.restore()
    if frozen > 0:
        tint(c, "#0a1630", 0.6 * frozen, skia.BlendMode.kColor)
        # time ripple rings
        for k in range(3):
            ph = ((t - tf) * 0.7 + k / 3) % 1
            c.drawCircle(1100, 640, 100 + ph * 900, P("#cfe4ff", 3, 0.35 * (1 - ph) * frozen))
        # stopwatch
        with xf(c, 1640, 230, 0.9, alpha=frozen):
            c.drawCircle(0, 0, 100, P("#f3ece0", 8))
            rrect(c, -18, -136, 36, 28, 6, "#f3ece0")
            a = 2 * math.pi * 0.87
            line(c, 0, 0, math.sin(a) * 80, -math.cos(a) * 80, RED, 6)
            c.drawCircle(0, 0, 8, P("#f3ece0"))
        txt(c, "0.5 s", 1640, 390, 44, "bebas", "#cfe4ff", a=frozen, track=0.1)
    flash(c, t, tf - 0.2, 0.3, "#ffffff", 0.6)
    t_track(c, t, tf - 0.1, "THE  SPLIT  SECOND", W / 2, 180, 110, "bebas", "#ffffff", out=t1 - 0.15, t1=0.5,
            t2=0.18, dur=1.6)
    t_rise(c, t, wt(32, "before"), "before you slip into the same old habits.", W / 2, 1000, 50, "serifi",
           out=t1 - 0.15)


def jagged(x, amp=14, seed=3):
    rnd = random.Random(seed)
    pts = []
    y = -20
    while y < H + 40:
        pts.append((x + rnd.uniform(-amp, amp), y))
        y += 60
    return pts


def sc_choice(c, t):
    """T33 -> T35: THE CHOICE. Left: the same day forever (grey). Right: a door of warm light."""
    t0, t1 = T(33), T(35)
    split = ease_out(at(t, wt(33, "choice") - 0.1, 0.6))
    # full shot first, then split
    c.clear(C("#000000"))
    xs = lerp(W + 40, W / 2, split)
    pts = jagged(xs)
    # left half: grey loop
    c.save()
    lp = poly([(-10, -10)] + pts + [(-10, H + 10)])
    c.clipPath(lp, doAntiAlias=True)
    c.save()
    c.translate(-240 * split, 0)
    draw_set(c, "studio", 0)
    floor_ring(c, 960, 800, 420, 120, t, col="#8a8a8a")
    th = (t - t0) * 0.7
    x, y = 960 + 420 * math.cos(th), 800 + 120 * math.sin(th)
    woman(c, x, y - 190 * 0.85, 0.85, walk_pose(t, 1.3), "tired", t, face=-1 if math.sin(th) > 0 else 1,
          rim="#9a9a9a", light=(960, 800, "#bbbbbb"))
    c.restore()
    tint(c, "#808080", 0.9, skia.BlendMode.kSaturation)
    tint(c, "#000000", 0.25)
    c.restore()
    # right half: open door with warm light
    if split > 0:
        c.save()
        rp = poly(pts + [(W + 10, H + 10), (W + 10, -10)])
        c.clipPath(rp, doAntiAlias=True)
        c.translate(240 * (1 - split), 0)
        fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, ["#2a1a10", "#0a0605"]))
        dx = 1440
        light_cone(c, dx, 560, 0, 40, 900, "#ffd59a", 0.4)
        rrect(c, dx - 150, 260, 300, 520, 6, "#1a100a")
        fill_shader(c, skia.Rect(dx - 130, 280, dx + 130, 780), linear(0, 280, 0, 780, ["#fff3d6", "#ffc46b"]))
        add_glow(c, dx, 520, 520, "#ffcf8a", 0.55)
        # door leaf swung open
        c.drawPath(poly([(dx + 130, 280), (dx + 230, 240), (dx + 230, 820), (dx + 130, 780)]), P("#3a2416"))
        c.drawRect(skia.Rect(0, 780, W, H), P("#140c08", a=0.8))
        fill_shader(c, skia.Rect(dx - 300, 780, dx + 300, H), radial(dx, 790, 380, [("#ffc46b", 0.5), ("#ffc46b", 0)]))
        c.restore()
        for side in (0, 1):
            c.drawPath(skia.Path() if False else poly(pts, close=False), P("#000000", 10))
    t_track(c, t, wt(33, "choice"), "THE  CHOICE", W / 2, 150, 110, "bebas", "#ffffff", out=t1 - 0.2, t1=0.5, t2=0.18,
            dur=1.6)
    t_rise(c, t, wt(34, "same"), "the same day,", 480, 960, 60, "serifi", out=t1 - 0.2, color="#bdbdbd")
    t_rise(c, t, wt(34, "over"), "over and over again.", 480, 1030, 46, "serifi", out=t1 - 0.2, color="#9a9a9a")


def sc_step(c, t):
    """T35 -> END: one small step forward. The ring breaks. Warm light."""
    t0 = T(35)
    ts = wt(35, "step")
    tb = wt(36, "breaking")
    c.clear(C("#040405"))
    c.save()
    cam(c, t, t0, END, 1.15, 1.0, 960, 640)
    draw_set(c, "studio", 0)
    warm = clamp((t - tb) / 1.5)
    fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, [("#ffb867", 0.0 + 0.35 * warm), ("#000000", 0)]))
    light_cone(c, 1100, -200, -10, 14, 1400, "#ffe6c4", 0.22 + 0.25 * warm)
    crack = clamp((t - tb) / 0.8)
    floor_ring(c, 860, 800, 420, 120, t, col=mixhex("#ff8a3c", "#ffd59a", warm), a=1 - 0.7 * crack, crack=crack)
    # shards flying away
    if crack > 0:
        rnd = random.Random(9)
        for k in range(30):
            th = rnd.uniform(0, 2 * math.pi)
            ph = clamp((t - tb) / 2.2)
            x = 860 + 420 * math.cos(th) * (1 + ph * rnd.uniform(0.2, 0.8))
            y = 800 + 120 * math.sin(th) * (1 + ph * rnd.uniform(0.2, 0.8)) - ph * rnd.uniform(40, 220)
            c.drawCircle(x, y, rnd.uniform(3, 7), P("#ffd59a", a=(1 - ph) * 0.9))
    # her: standing at the ring's edge, then one step out
    st = smooth(clamp((t - ts) / 0.9))
    x = lerp(1180, 1330, st)
    pose = mix_pose("stand", "stepf", math.sin(st * math.pi)) if st < 1 else POSES["stand"]
    expr = "focus" if t < tb else "soft"
    woman(c, x, 800 - 190 * 0.95, 0.95, pose, expr, t, face=1, look=(0.6, -0.1), rim=mixhex("#ffb36b", "#ffe6c4", warm),
          light=(1700, 400, "#ffd59a"), shade=0.45)
    c.restore()
    flash(c, t, tb, 0.35, "#fff2d0", 0.6)
    t_rise(c, t, wt(35, "one"), "one small step forward.", W / 2, 200, 70, "serifi", out=E(36) + 0.4)
    # end title
    te = E(36) + 0.6
    if t >= te:
        k = t - te
        tint(c, "#000000", clamp(k / 0.6) * 0.85)
        txt(c, "BREAK THE LOOP.", W / 2, 580, 170, "bebas", "#f3ece0", a=clamp((k - 0.3) / 0.6),
            track=lerp(0.3, 0.1, ease_out(clamp(k / 2.5))), glow_col="#ffc46b", glow_a=0.35)
        line(c, W / 2 - 220 * ease_out(clamp((k - 0.8) / 1)), 630, W / 2 + 220 * ease_out(clamp((k - 0.8) / 1)), 630,
             RED, 4, clamp((k - 0.8) / 0.5))
        txt(c, "start with one small step.", W / 2, 700, 46, "serifi", "#bfb6a8", a=clamp((k - 1.3) / 0.7))
        tint(c, "#000000", clamp((t - (END - 1.2)) / 1.2))


SCENES = [
    (0.0, T(2), sc_hook),
    (T(2), T(3) - 0.25, sc_loop),
    (T(3) - 0.25, T(5), sc_night),
    (T(5), T(8) - 0.2, sc_morning),
    (T(8) - 0.2, T(9), sc_droste),
    (T(9), T(12), sc_cycle1),
    (T(12), T(14), sc_discomfort),
    (T(14), T(16), sc_avoid),
    (T(16), T(18), sc_cycle_full),
    (T(18), T(22), sc_breakfree),
    (T(22), T(23), sc_slowdown),
    (T(23), T(25), sc_meta),
    (T(25), T(27), sc_examine),
    (T(27), T(29), sc_decisions),
    (T(29), T(31), sc_autopilot),
    (T(31), T(33), sc_splitsecond),
    (T(33), T(35), sc_choice),
    (T(35), END + 1, sc_step),
]
# where a short dip-to-black sits at a scene boundary (section changes)
DIPS = {T(3) - 0.25, T(9), T(18), T(23), T(33), T(35)}


def render_frame(c, t):
    c.clear(C("#000000"))
    for i, (a, b, fn) in enumerate(SCENES):
        if a <= t < b:
            c.save()
            fn(c, t)
            c.restore()
            if a in DIPS:
                tint(c, "#000000", 1 - clamp((t - a) / 0.35))
            if b in DIPS:
                tint(c, "#000000", clamp((t - (b - 0.3)) / 0.3))
            break
    # global grade: lift blacks slightly toward warm, vignette, grain
    tint(c, "#1a0f08", 0.06, skia.BlendMode.kScreen)
    vignette(c, 0.55)
    grain(c, t, 0.06)
    if t < 0.4:
        tint(c, "#000000", 1 - t / 0.4)
