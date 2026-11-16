"""Explainer timeline: beats from the transcript, habit chapter cards, stats, charts and kinetic text."""
import bisect
import json
import math
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
sys.path.insert(0, HERE)

import skia  # noqa: E402

from gfx import (W, H, P, xf, rrect, poly, line, text, text_width, linear, radial, fill_shader, glow,  # noqa: E402
                 sparkle, clamp, lerp, smooth, ease_out, back_out, draw_char, font)
import places as PL  # noqa: E402
from icons import ICONS, pick_icon, coin, GREEN, GOLD, RED, BLUE, WHITE  # noqa: E402

T = json.load(open(os.path.join(HERE, "transcript.json")))
DUR = T[-1]["end"] + 3.0

NUMW = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                    "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}

WORDS = []
for si, s in enumerate(T):
    for w in s["words"]:
        WORDS.append(dict(w=w["w"].strip(), s=w["s"], e=w["e"], seg=si))


def clean(w):
    return re.sub(r"[^\w$%]", "", w.lower())


# ---------------------------------------------------------------- chapters
CHAPTERS = [dict(n=0, start=0.0, title="MY STORY")]
for i, w in enumerate(WORDS[:-1]):
    if clean(w["w"]) == "habit":
        nx = clean(WORDS[i + 1]["w"])
        n = NUMW.get(nx) if not nx.isdigit() else int(nx)
        if n and n == CHAPTERS[-1]["n"] + 1:
            title = []
            for w2 in WORDS[i + 2:i + 14]:
                title.append(w2["w"])
                if w2["w"].endswith((".", "?", "!")):
                    break
            tt = " ".join(title).strip(" ,.")
            tt = re.sub(r"^I ", "", tt)
            tt = tt.split(",")[0]
            if len(tt.split()) < 3:
                tt = " ".join(x["w"] for x in WORDS[i + 2:i + 30]).split(".")[1].strip()
                tt = re.sub(r"^I ", "", tt)
            tt = " ".join(tt.split()[:7])
            CHAPTERS.append(dict(n=n, start=w["s"], title=tt.upper()))
# outro: after habit 20, find the "gap isn't about income" or last ~60s
last = CHAPTERS[-1]["start"]
for s in T:
    if s["start"] > last + 25 and ("behavior" in s["text"] or "income" in s["text"]):
        CHAPTERS.append(dict(n=99, start=s["start"] - 0.01, title="THE REAL LESSON"))
        break
CH_STARTS = [c["start"] for c in CHAPTERS]

THEMES = ["#e50914", "#2ecc71", "#3aa0ff", "#ffc93c", "#ff7a59", "#a66cff", "#1abc9c", "#ff4f86"]


def chapter_at(t):
    return CHAPTERS[max(0, bisect.bisect_right(CH_STARTS, t) - 1)]


def theme(ch):
    return "#e50914" if ch["n"] in (0, 99) else THEMES[ch["n"] % len(THEMES)]


# ---------------------------------------------------------------- beats
MONEY = re.compile(r"\$\s?[\d,]+(?:\.\d+)?(?:\s?(?:k|million|thousand))?|\b\d{1,3}(?:,\d{3})+\b|\b\d+(?:\.\d+)?%")


def parse_num(s):
    v = s.replace("$", "").replace(",", "").replace("%", "").strip()
    mult = 1
    if v.endswith("million"):
        mult, v = 1_000_000, v.replace("million", "")
    elif v.endswith("thousand"):
        mult, v = 1000, v.replace("thousand", "")
    elif v.endswith("k"):
        mult, v = 1000, v[:-1]
    try:
        return float(v.strip()) * mult
    except ValueError:
        return None


BEATS = []
for si, s in enumerate(T):
    txt = s["text"]
    b = dict(start=s["start"], end=s["end"], text=txt, words=s["words"], seg=si)
    m = list(MONEY.finditer(txt))
    if m:
        best = max(m, key=lambda mm: (("$" in mm.group()) * 2 + ("%" not in mm.group()), parse_num(mm.group()) or 0))
        raw = best.group().strip()
        b["kind"] = "stat"
        b["raw"] = raw
        b["val"] = parse_num(raw) or 0
        b["is_money"] = "$" in raw or (b["val"] >= 1000 and "%" not in raw)
        b["is_pct"] = "%" in raw
        # time the count-up on the word containing the digits
        digits = re.sub(r"\D", "", raw)[:3]
        b["hit"] = s["start"]
        for w in s["words"]:
            if digits and digits in re.sub(r"\D", "", w["w"]):
                b["hit"] = w["s"]
                break
        if re.search(r"\byears?\b", txt) and b["val"] >= 10000:
            b["kind"] = "chart"
    else:
        b["kind"] = "text"
    b["icon"] = pick_icon(txt)
    low = txt.lower()
    if any(k in low for k in ("no inheritance", "no lottery", "no stock picking", "no granite", "nobody")):
        b["kind"] = "nolist"
    BEATS.append(b)

# merge very short beats into previous for calmer pacing
merged = []
for b in BEATS:
    if merged and b["kind"] == "text" and merged[-1]["kind"] == "text" and (b["end"] - b["start"]) < 1.1 and \
            len(merged[-1]["words"]) < 9:
        merged[-1]["end"] = b["end"]
        merged[-1]["text"] += " " + b["text"]
        merged[-1]["words"] = merged[-1]["words"] + b["words"]
        merged[-1]["icon"] = merged[-1]["icon"] or b["icon"]
    else:
        merged.append(dict(b))
BEATS = merged
for i, b in enumerate(BEATS):
    b["i"] = i
    b["show0"] = b["start"] - 0.15 if i == 0 else (BEATS[i - 1]["end"] + b["start"]) / 2
for i, b in enumerate(BEATS):
    b["show1"] = BEATS[i + 1]["show0"] if i + 1 < len(BEATS) else DUR
B_STARTS = [b["show0"] for b in BEATS]
CUTS = [b["show0"] for b in BEATS]

# fallback icons rotate so no beat is empty
_fallback = ["bulb", "cash", "coin", "chart", "piggy", "target", "check"]
for b in BEATS:
    if not b["icon"]:
        b["icon"] = _fallback[b["i"] % len(_fallback)]
    b["side"] = 1 if (b["i"] // 2) % 2 == 0 else -1
    b["place"] = PL.pick_place(b["text"]) if b["kind"] == "text" else None
    if b["kind"] == "text" and not b["place"] and b["i"] % 3 == 0:
        b["place"] = "audience"

NEG = ("broke", "debt", "tear", "crack", "ignored", "lose", "lost", "problem", "struggling", "mistake", "trap",
       "okay?", "need money")
WOW = ("$61,412", "100,000", "million", "free money", "proof", "interesting")


def beat_at(t):
    return BEATS[max(0, bisect.bisect_right(B_STARTS, t) - 1)]


def active_word(t):
    # binary search over flat words
    lo, hi = 0, len(WORDS) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if WORDS[mid]["s"] <= t:
            lo = mid
        else:
            hi = mid - 1
    w = WORDS[lo]
    return w if w["s"] <= t <= w["e"] + 0.05 else None


# ---------------------------------------------------------------- formatting
def fmt_money(v, raw, is_pct):
    if is_pct:
        return (f"{v:.2f}".rstrip("0").rstrip(".")) + "%"
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M".replace(".0M", "M")
    s = f"{int(round(v)):,}"
    return ("$" if "$" in raw or v >= 1000 else "") + s


# ---------------------------------------------------------------- backgrounds
_bg_cache = {}


def background(c, t, col):
    key = col
    if key not in _bg_cache:
        s = skia.Surface(W, H)
        cc = s.getCanvas()
        fill_shader(cc, skia.Rect(0, 0, W, H), linear(0, 0, W, H, ["#0b0f1a", "#111a2e"]))
        fill_shader(cc, skia.Rect(0, 0, W, H), radial(W * 0.72, H * 0.42, 900, [(col, 0.22), (col, 0.0)]))
        fill_shader(cc, skia.Rect(0, 0, W, H), radial(W * 0.15, H * 0.95, 700, [("#3aa0ff", 0.10), ("#3aa0ff", 0)]))
        for gx in range(0, W + 1, 80):
            cc.drawLine(gx, 0, gx, H, P("#ffffff", 1, 0.035))
        for gy in range(0, H + 1, 80):
            cc.drawLine(0, gy, W, gy, P("#ffffff", 1, 0.035))
        _bg_cache[key] = s.makeImageSnapshot()
    c.drawImage(_bg_cache[key], 0, 0)
    r = random.Random(7)
    for i in range(26):
        x = (r.uniform(0, W) + t * r.uniform(6, 22)) % W
        y = (r.uniform(0, H) - t * r.uniform(10, 30)) % H
        rad = r.uniform(2, 5)
        c.drawCircle(x, y, rad, P(col if i % 3 == 0 else "#ffffff", a=0.12))


def floor(c, x, col):
    fill_shader(c, skia.Rect(x - 260, 940, x + 260, 1010), radial(x, 975, 260, [("#000000", 0.45), ("#000000", 0)]))


# ---------------------------------------------------------------- HUD
def hud(c, t, ch):
    col = theme(ch)
    # progress bar of 20 habits
    x0, y0 = 600, 46
    for k in range(20):
        done = ch["n"] == 99 or k < ch["n"]
        cur = k == ch["n"] - 1
        rrect(c, x0 + k * 37, y0, 31, 9, 4, col if (done or cur) else "#ffffff", 1.0 if done or cur else 0.15)
    if ch["n"] == 0:
        label = "MY STORY"
    elif ch["n"] == 99:
        label = "THE REAL LESSON"
    else:
        label = f"HABIT {ch['n']:02d}"
    w = text_width(label, 30, "Black") + 40
    rrect(c, 60, 32, w, 46, 10, col)
    text(c, label, 60 + w / 2, 66, 30, "#ffffff")


# ---------------------------------------------------------------- chapter card
def chapter_card(c, t, ch):
    k = t - ch["start"]
    if ch["n"] == 0 or k < 0 or k > 2.3:
        return
    col = theme(ch)
    inn = ease_out(k / 0.35)
    out = ease_out((k - 1.85) / 0.45)
    # diagonal wipe panels
    xoff = lerp(-W * 1.3, 0, inn) + lerp(0, W * 1.4, out)
    with xf(c, xoff, 0):
        c.drawPath(poly([(-200, 0), (W + 200, 0), (W - 100, H), (-500, H)]), P("#0b0f1a"))
        c.drawPath(poly([(W * 0.52, 0), (W + 200, 0), (W + 100, H), (W * 0.40, H)]), P(col))
    if inn < 0.6 or out > 0.6:
        return
    a = clamp((k - 0.25) / 0.2) * (1 - clamp((k - 1.8) / 0.2))
    with xf(c, 0, 0, alpha=a):
        num = "THE END" if ch["n"] == 99 else f"{ch['n']:02d}"
        ss = back_out(clamp((k - 0.25) / 0.5))
        if ch["n"] == 99:
            with xf(c, W * 0.70, H * 0.55, s=ss):
                text(c, "LESSON", 0, 60, 190, "#ffffff")
            text(c, "THE REAL", W * 0.25, H * 0.42, 70, col)
            text(c, "IT'S NOT INCOME", W * 0.25, H * 0.42 + 90, 52, "#ffffff")
        else:
            with xf(c, W * 0.74, H * 0.56, s=ss):
                text(c, num, 0, 150, 420, "#ffffff", shadow=True)
            text(c, "HABIT", W * 0.25, H * 0.33, 110, col)
            lines = wrap(ch["title"], 64, 860)
            for i, ln in enumerate(lines[:3]):
                kk = ease_out(clamp((k - 0.4 - i * 0.08) / 0.35))
                text(c, ln, W * 0.25 + (1 - kk) * -80, H * 0.48 + i * 80, 64, "#ffffff", a=kk)
            text(c, f"{ch['n']} / 20", W * 0.25, H * 0.80, 34, "#ffffff", "Bold", a=0.6)


def wrap(s, size, maxw, weight="Black"):
    words = s.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_width(trial, size, weight) > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- character
POSES_CYCLE = ["stand", "give", "wave", "hold", "give_l", "stand", "tug"]


def character(c, t, b, ch):
    side = b["side"]
    x = 360 if side == 1 else W - 360
    low = b["text"].lower()
    expr = "happy"
    if any(k in low for k in NEG):
        expr = "worried"
    if any(k.lower() in low for k in WOW) or b["kind"] in ("stat", "chart") and b.get("val", 0) >= 50000:
        expr = "shock" if t < b.get("hit", 0) + 1.2 and t > b.get("hit", 0) else "happy"
    pose = POSES_CYCLE[b["i"] % len(POSES_CYCLE)]
    if pose in ("wave",) and b["kind"] != "text":
        pose = "give"
    aw = active_word(t)
    talk = 0.5 + 0.5 * math.sin(t * 22) if aw else 0.0
    ent = ease_out((t - b["show0"]) / 0.35)
    bob = -6 * abs(math.sin(t * 2.2))
    floor(c, x, theme(ch))
    draw_char(c, x + (1 - ent) * -side * 60, 770, "you", pose, expr, t, s=1.55, talk=talk, bob=bob,
              flip=(side == -1), look=(side * 0.6, 0))


# ---------------------------------------------------------------- panels
def panel_box(c, t, b):
    side = b["side"]
    cx = W * 0.62 if side == 1 else W * 0.38
    k = ease_out((t - b["show0"]) / 0.4)
    ko = clamp((t - (b["show1"] - 0.2)) / 0.2)
    return cx, k, ko


def draw_icon(c, t, name, x, y, s):
    fn = ICONS.get(name)
    if fn:
        with xf(c, x, y, s=s):
            fn(c, t)


def text_panel(c, t, b, ch):
    cx, k, ko = panel_box(c, t, b)
    col = theme(ch)
    a = k * (1 - ko)
    with xf(c, cx, 0, alpha=a):
        # icon bubble
        ik = back_out(clamp((t - b["show0"]) / 0.5))
        fill_shader(c, skia.Rect(-260, 120, 260, 640), radial(0, 380, 260, [(col, 0.35), (col, 0)]))
        c.drawCircle(0, 380, 205 * ik, P("#ffffff", a=0.06))
        c.drawCircle(0, 380, 205 * ik, P(col, 4, 0.6))
        with xf(c, 0, 380 + 8 * math.sin(t * 2), s=ik * 0.95, rot=3 * math.sin(t * 1.3)):
            ICONS[b["icon"]](c, t)
        # kinetic sentence, words pop as spoken
        size = 58
        words = [w for w in b["words"]]
        lines, cur, curw = [], [], 0
        for w in words:
            ww = text_width(w["w"].strip() + " ", size)
            if curw + ww > 980 and cur:
                lines.append(cur)
                cur, curw = [], 0
            cur.append(w)
            curw += ww
        if cur:
            lines.append(cur)
        if len(lines) > 3:
            size = 46
            lines = []
            cur, curw = [], 0
            for w in words:
                ww = text_width(w["w"].strip() + " ", size)
                if curw + ww > 1040 and cur:
                    lines.append(cur)
                    cur, curw = [], 0
                cur.append(w)
                curw += ww
            if cur:
                lines.append(cur)
        y0 = 720
        for li, ln in enumerate(lines):
            lw = sum(text_width(w["w"].strip() + " ", size) for w in ln)
            x = -lw / 2
            for w in ln:
                s = w["w"].strip()
                ww = text_width(s + " ", size)
                p = clamp((t - w["s"] + 0.12) / 0.18)
                if p > 0:
                    key = bool(re.search(r"\d", s)) or len(re.sub(r"\W", "", s)) >= 7
                    speaking = w["s"] - 0.02 <= t <= w["e"] + 0.05
                    colw = GOLD if key else "#ffffff"
                    if speaking:
                        rrect(c, x - 8, y0 + li * size * 1.25 - size * 0.9, text_width(s, size) + 16, size * 1.15,
                              10, col, 0.85)
                        colw = "#ffffff"
                    sc = back_out(p)
                    with xf(c, x + text_width(s, size) / 2, y0 + li * size * 1.25 - size * 0.35, s=0.6 + 0.4 * sc):
                        text(c, s, 0, size * 0.35, size, colw, a=p, shadow=True)
                x += ww


def stat_panel(c, t, b, ch):
    cx, k, ko = panel_box(c, t, b)
    col = theme(ch)
    a = k * (1 - ko)
    hit = b["hit"]
    prog = ease_out(clamp((t - hit + 0.1) / 0.9))
    with xf(c, cx, 0, alpha=a):
        ik = back_out(clamp((t - b["show0"]) / 0.5))
        with xf(c, 0, 300 + 6 * math.sin(t * 2), s=ik * 0.75):
            ICONS[b["icon"]](c, t)
        v = b["val"] * prog
        label = fmt_money(v if not b["is_pct"] else b["val"] * prog, b["raw"], b["is_pct"])
        if b["is_pct"] and b["val"] < 1:
            label = b["raw"]
        size = 170 if len(label) <= 8 else 130
        pop = 1 + 0.12 * math.exp(-max(0, t - hit - 0.9) * 6) * (t > hit + 0.9)
        glow(c, 0, 600, 420, GREEN if b["is_money"] else col, 0.18 * prog)
        na = clamp((t - hit + 0.25) / 0.25)
        with xf(c, 0, 600, s=pop * (0.6 + 0.4 * back_out(na)), alpha=na):
            text(c, label, 0, size * 0.36, size, GREEN if b["is_money"] else GOLD, shadow=True)
        if prog > 0.98:
            for i in range(6):
                ang = i / 6 * math.tau + t
                rr = 330 + 20 * math.sin(t * 3 + i)
                sparkle(c, math.cos(ang) * rr, 600 + math.sin(ang) * rr * 0.4, 16, GOLD,
                        a=0.8 * clamp((t - hit - 0.9) / 0.3))
        # caption line under the number
        cap = b["text"]
        lines = wrap(cap, 40, 1000, "Bold")
        for i, ln in enumerate(lines[:3]):
            text(c, ln, 0, 790 + i * 54, 40, "#ffffff", "Bold", a=0.92)
        rrect(c, -60, 735, 120, 6, 3, col)


def chart_panel(c, t, b, ch):
    cx, k, ko = panel_box(c, t, b)
    col = theme(ch)
    a = k * (1 - ko)
    hit = b["hit"]
    prog = smooth(clamp((t - b["show0"] - 0.2) / max(1.0, (hit - b["show0"]) + 0.6)))
    with xf(c, cx, 0, alpha=a):
        gx, gy, gw, gh = -480, 220, 960, 440
        rrect(c, gx - 30, gy - 40, gw + 60, gh + 90, 26, "#0c1424", 0.85)
        rrect(c, gx - 30, gy - 40, gw + 60, gh + 90, 26, col, stroke=3)
        for i in range(5):
            line(c, gx, gy + gh - i * gh / 4, gx + gw, gy + gh - i * gh / 4, "#ffffff", 2, 0.08)
        text(c, "YEARS →", gx + gw - 70, gy + gh + 38, 26, "#ffffff", "Bold", a=0.5)
        n = 60
        pts = []
        for i in range(n + 1):
            f = i / n
            if f > prog:
                break
            yv = (math.pow(1.08, f * 30) - 1) / (math.pow(1.08, 30) - 1)
            pts.append((gx + f * gw, gy + gh - yv * gh * 0.95))
        if len(pts) > 1:
            area = skia.Path()
            area.moveTo(pts[0][0], gy + gh)
            for p in pts:
                area.lineTo(*p)
            area.lineTo(pts[-1][0], gy + gh)
            area.close()
            c.drawPath(area, skia.Paint(AntiAlias=True, Shader=linear(0, gy, 0, gy + gh, [(GREEN, 0.45),
                                                                                       (GREEN, 0.0)])))
            pth = skia.Path()
            pth.moveTo(*pts[0])
            for p in pts[1:]:
                pth.lineTo(*p)
            c.drawPath(pth, P(GREEN, 9))
            ex, ey = pts[-1]
            glow(c, ex, ey, 60, GREEN, 0.6)
            c.drawCircle(ex, ey, 13, P("#ffffff"))
            # bar compare: small "spent" coin stack vs growth
            coin(c, t, gx + 60, gy + gh - 60, 34)
        v = b["val"] * ease_out(clamp((t - hit + 0.1) / 0.9))
        label = fmt_money(v, b["raw"], False)
        with xf(c, gx + 40, gy + 30):
            text(c, label, 0, 50, 110, GREEN, align="left", shadow=True)
        lines = wrap(b["text"], 38, 1000, "Bold")
        for i, ln in enumerate(lines[:2]):
            text(c, ln, 0, 790 + i * 52, 38, "#ffffff", "Bold")


def nolist_panel(c, t, b, ch):
    cx, k, ko = panel_box(c, t, b)
    a = k * (1 - ko)
    parts = [p.strip(" .,") for p in re.split(r"[.,]", b["text"]) if p.strip(" .,")]
    with xf(c, cx, 0, alpha=a):
        n = len(parts)
        y0 = 540 - (n - 1) * 70
        for i, p in enumerate(parts):
            # timestamp of first word of this part
            first = p.split()[0].lower() if p.split() else ""
            ts = b["start"] + i * 0.6
            for w in b["words"]:
                if clean(w["w"]) == clean(first) and w["s"] >= ts - 0.8:
                    ts = w["s"]
                    break
            pk = back_out(clamp((t - ts + 0.1) / 0.35))
            if pk <= 0:
                continue
            y = y0 + i * 140
            with xf(c, 0, y, s=pk):
                w = text_width(p.upper(), 60) + 140
                rrect(c, -w / 2, -55, w, 110, 22, "#ffffff", 0.08)
                c.drawCircle(-w / 2 + 55, 0, 32, P(RED))
                line(c, -w / 2 + 40, -15, -w / 2 + 70, 15, "#ffffff", 8)
                line(c, -w / 2 + 70, -15, -w / 2 + 40, 15, "#ffffff", 8)
                text(c, p.upper(), 30, 22, 60, "#ffffff")
                sk = clamp((t - ts - 0.35) / 0.25)
                if sk > 0 and p.lower().startswith("no"):
                    line(c, -w / 2 + 100, 0, -w / 2 + 100 + (w - 130) * sk, 0, RED, 8)


# ---------------------------------------------------------------- captions (for stat/chart beats)
def captions(c, t, b):
    pass


# ---------------------------------------------------------------- intro / outro specials
def title_flash(c, t):
    """Big title on the '20 habits' line."""
    for s in T:
        if "20 habits" in s["text"].lower():
            k = t - s["start"]
            if 0 <= k <= (s["end"] - s["start"]) + 0.6:
                a = clamp(k / 0.2) * clamp((s["end"] + 0.6 - t) / 0.3)
                fill_shader(c, skia.Rect(0, 0, W, H), linear(0, 0, 0, H, [("#0b0f1a", a), ("#5a0208", a)]))
                with xf(c, W / 2, H / 2, s=back_out(clamp(k / 0.5)) * (1 + 0.03 * k), alpha=a):
                    text(c, "20", 0, 120, 380, "#e50914", shadow=True)
                    text(c, "BORING HABITS", 0, 230, 90, "#ffffff")
                    text(c, "THAT BUILT $100,000", 0, 320, 56, GOLD)
            break


def end_card(c, t):
    k = t - (T[-1]["end"] + 0.2)
    if k < 0:
        return
    a = clamp(k / 0.5)
    c.drawRect(skia.Rect(0, 0, W, H), P("#0b0f1a", a=a))
    with xf(c, W / 2, H / 2, alpha=a, s=0.9 + 0.1 * ease_out(k / 0.8)):
        text(c, "BUILT QUIETLY.", 0, -40, 120, "#ffffff")
        text(c, "THE BALANCE IS THE PROOF.", 0, 60, 60, GOLD)


# ---------------------------------------------------------------- real-world locations
def kinetic(c, t, words, cx, y0, size, maxw, col):
    lines, cur, curw = [], [], 0
    for w in words:
        ww = text_width(w["w"].strip() + " ", size)
        if curw + ww > maxw and cur:
            lines.append(cur)
            cur, curw = [], 0
        cur.append(w)
        curw += ww
    if cur:
        lines.append(cur)
    for li, ln in enumerate(lines[:3]):
        lw = sum(text_width(w["w"].strip() + " ", size) for w in ln)
        x = cx - lw / 2
        for w in ln:
            s = w["w"].strip()
            ww = text_width(s + " ", size)
            p = clamp((t - w["s"] + 0.12) / 0.18)
            if p > 0:
                key = bool(re.search(r"\d", s)) or len(re.sub(r"\W", "", s)) >= 7
                speaking = w["s"] - 0.02 <= t <= w["e"] + 0.05
                colw = GOLD if key else "#ffffff"
                yy = y0 + li * size * 1.3
                if speaking:
                    rrect(c, x - 7, yy - size * 0.9, text_width(s, size) + 14, size * 1.15, 9, col, 0.9)
                    colw = "#ffffff"
                with xf(c, x + text_width(s, size) / 2, yy - size * 0.35, s=0.6 + 0.4 * back_out(p)):
                    text(c, s, 0, size * 0.35, size, colw, a=p)
            x += ww
    return len(lines[:3])


def location_scene(c, t, b, ch):
    col = theme(ch)
    place = b["place"]
    side = b["side"]
    k = clamp((t - b["show0"]) / max(1.0, b["show1"] - b["show0"]))
    if place == "audience":
        background(c, t, col)
        fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, 200, 900, [("#ffffff", 0.10), ("#ffffff", 0)]))
        rrect(c, W / 2 - 330, 330, 660, 380, 18, "#0c1424")
        rrect(c, W / 2 - 330, 330, 660, 380, 18, col, stroke=5)
        with xf(c, W / 2, 520, s=0.9):
            ICONS[b["icon"]](c, t)
        c.drawRect(skia.Rect(0, PL.FLOOR - 20, W, H), P("#151d30"))
    else:
        PL.draw_set(c, place, t, pan=-60 + 120 * k * side)
    # crowd
    if place in ("restaurant", "office", "audience", "street", "park", "shop") or b["i"] % 2 == 0:
        n = 3 if place in ("audience", "restaurant", "office") else 2
        PL.crowd(c, t, side, n, b["i"])
    # main character walks in, then talks
    x1 = 420 if side == 1 else W - 420
    walk = clamp((t - b["show0"]) / 1.1)
    aw = active_word(t)
    talk = 0.5 + 0.5 * math.sin(t * 22) if aw else 0.0
    if walk < 1 and place in PL.OUTDOOR + ("shop", "audience"):
        x = x1 - side * 320 * (1 - ease_out(walk))
        PL.walker(c, t, x, PL.FLOOR - 130, "you", 1.4, side == -1, "happy", b["show0"])
    else:
        low = b["text"].lower()
        expr = "worried" if any(q in low for q in NEG) else "happy"
        pose = ["give", "wave", "give", "hold"][b["i"] % 4]
        draw_char(c, x1, PL.FLOOR - 130, "you", pose, expr, t, s=1.4, talk=talk,
                  bob=-5 * abs(math.sin(t * 2.2)), flip=(side == -1), look=(side * 0.6, 0))
    # place tag
    if place != "audience":
        lab = PL.LABEL[place]
        tw = text_width(lab, 28, "Black") + 70
        tx = W - 70 - tw if side == 1 else 70
        rrect(c, tx, 100, tw, 50, 25, "#0b0f1a", 0.75)
        c.drawCircle(tx + 28, 125, 9, P(col))
        text(c, lab, tx + 42 + (tw - 56) / 2, 135, 28, "#ffffff")
    # subtitle card with kinetic words
    a = clamp((t - b["show0"]) / 0.3)
    with xf(c, 0, 0, alpha=a):
        rrect(c, W / 2 - 640, 175, 1280, 190, 26, "#0b0f1a", 0.78)
        rrect(c, W / 2 - 640, 175, 10, 190, 5, col)
        with xf(c, W / 2 - 545, 270, s=0.38):
            ICONS[b["icon"]](c, t)
        kinetic(c, t, b["words"], W / 2 + 70, 250, 46, 1000, col)


# ---------------------------------------------------------------- master
def render_frame(c, t):
    ch = chapter_at(t)
    b = beat_at(t)
    col = theme(ch)
    # camera: slow push per beat + drift
    z = 1.0 + 0.035 * clamp((t - b["show0"]) / max(1.0, b["show1"] - b["show0"]))
    dx = 6 * math.sin(t * 0.5)
    dy = 4 * math.sin(t * 0.37)
    c.save()
    c.translate(W / 2 + dx, H / 2 + dy)
    c.scale(z, z)
    c.translate(-W / 2, -H / 2)
    if b["kind"] == "text" and b.get("place"):
        location_scene(c, t, b, ch)
        c.restore()
        _post(c, t, b, ch)
        return
    background(c, t, col)
    # giant watermark number
    wm = "★" if ch["n"] in (0, 99) else f"{ch['n']:02d}"
    if ch["n"] not in (0, 99):
        text(c, wm, W * 0.5 - b["side"] * 520, 980, 520, "#ffffff", a=0.035)
    character(c, t, b, ch)
    if b["kind"] == "stat":
        stat_panel(c, t, b, ch)
    elif b["kind"] == "chart":
        chart_panel(c, t, b, ch)
    elif b["kind"] == "nolist":
        nolist_panel(c, t, b, ch)
    else:
        text_panel(c, t, b, ch)
    c.restore()
    _post(c, t, b, ch)


def _post(c, t, b, ch):
    # flash on cut
    fk = t - b["show0"]
    if 0 <= fk < 0.12 and b["i"] > 0:
        c.drawRect(skia.Rect(0, 0, W, H), P("#ffffff", a=0.10 * (1 - fk / 0.12)))
    hud(c, t, ch)
    title_flash(c, t)
    for chh in CHAPTERS:
        chapter_card(c, t, chh)
    end_card(c, t)
    # letterbox-style vignette
    fill_shader(c, skia.Rect(0, 0, W, H), radial(W / 2, H / 2, W * 0.75, [("#000000", 0), ("#000000", 0),
                                                                          ("#000000", 0.5)], [0, 0.6, 1]))
    # fade in from black
    if t < 0.6:
        c.drawRect(skia.Rect(0, 0, W, H), P("#000000", a=1 - t / 0.6))


if __name__ == "__main__":
    for chh in CHAPTERS:
        print(f"{chh['start']:7.2f}  {chh['n']:2d}  {chh['title']}")
    print(len(BEATS), "beats", sum(b["kind"] == "stat" for b in BEATS), "stats",
          sum(b["kind"] == "chart" for b in BEATS), "charts")
