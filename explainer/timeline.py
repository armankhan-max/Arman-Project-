"""The whole video: beats keyed to the narration (absolute seconds).
Times come from transcript.json: numbers are sentence starts, tw("word", after)
finds the exact moment a word is spoken."""
from engine import *  # noqa: F401,F403
from engine import B, CH, G, I, K, LIST, N, S, SP, T, finalize, tw  # noqa: F811

TOTAL = 775.6


# ================================================================ diagrams
def battery_cell(start, sep=None, touch=None, heat=None, squeeze=None, specks=None, pierce=None,
                 labels=True):
    """Cross-section of a lithium-ion cell: two layers + a razor-thin separator."""
    def fn(c, x, y, t):
        a = ease_out(prog(t, start, 0.5))
        w, h = 900, 300
        x0, y0 = x - w / 2, y + 20
        sq = ease_io(prog(t, squeeze, 0.9)) if squeeze else 0
        # casing
        rr(c, x0, y0, w, h, 28, "#161A20", a)
        rr(c, x0, y0, w, h, 28, MUTED, a, stroke=6)
        # squeeze: casing corner pushing in (top-right)
        if squeeze:
            p = skia.Path()
            p.moveTo(x0 + w - 260, y0)
            p.lineTo(x0 + w, y0)
            p.lineTo(x0 + w, y0 + 120)
            p.close()
            c.drawPath(path([(x0 + w - 260, y0 - 2), (x0 + w + 2, y0 - 2), (x0 + w + 2, y0 + 30 + 110 * sq)]),
                       P(ACC, a=a * 0.85 * sq))
        mid = y0 + h / 2
        # touch point bulge
        tp = ease_out(prog(t, touch, 0.6)) if touch else 0
        tp = max(tp, sq * 0.95)
        bx = x0 + w - 150 if squeeze else x
        # top layer (A)
        top = skia.Path()
        top.moveTo(x0 + 40, y0 + 40)
        top.lineTo(x0 + w - 40, y0 + 40)
        top.lineTo(x0 + w - 40, mid - 14)
        for k in range(41):
            xx = x0 + w - 40 - k * (w - 80) / 40
            bump = tp * 12 * math.exp(-((xx - bx) / 70) ** 2)
            top.lineTo(xx, mid - 14 + bump)
        top.close()
        c.drawPath(top, P("#4C6B8A", a=a))
        bot = skia.Path()
        bot.moveTo(x0 + 40, y0 + h - 40)
        bot.lineTo(x0 + w - 40, y0 + h - 40)
        bot.lineTo(x0 + w - 40, mid + 14)
        for k in range(41):
            xx = x0 + w - 40 - k * (w - 80) / 40
            bump = tp * 12 * math.exp(-((xx - bx) / 70) ** 2)
            bot.lineTo(xx, mid + 14 - bump)
        bot.close()
        c.drawPath(bot, P("#8A6A4C", a=a))
        # separator
        sp = ease_out(prog(t, sep, 0.5)) if sep else 1
        glow = 0.5 + 0.5 * math.sin(t * 5) if sep and t < sep + 3 else 0
        sx0, sx1 = x0 + 40, x0 + 40 + (w - 80) * sp
        if tp < 0.99:
            line(c, sx0, mid, sx1, mid, mix(INK, COOL, glow * 0.6), 5, a)
        else:
            line(c, sx0, mid, bx - 40, mid, INK, 5, a)
            line(c, bx + 40, mid, sx1, mid, INK, 5, a)
        # specks (metal particles)
        if specks:
            ps = ease_out(prog(t, specks, 0.5))
            rnd = random.Random(7)
            for k in range(14):
                xx = x0 + 80 + rnd.random() * (w - 160)
                yy = y0 + 60 + rnd.random() * (h - 120)
                if abs(yy - mid) < 24:
                    yy += 40
                circ(c, xx, yy, 5, "#D7DCE3", a * ps)
            if pierce:
                pp = ease_io(prog(t, pierce, 1.6))
                xx = x + 120
                circ(c, xx, mid - 50 + 50 * pp, 9, AMB, a * ps)
                if pp > 0.95:
                    tp = 1
        # spark + heat
        if tp > 0.95 or (touch and t > touch + 0.5):
            sk = clamp((t - (touch or squeeze or pierce or 0)) * 2)
            px = bx if not specks else x + 120
            for k in range(8):
                ang = k * math.pi / 4 + t * 2
                r0, r1 = 18, 18 + 40 * sk
                line(c, px + r0 * math.cos(ang), mid + r0 * math.sin(ang), px + r1 * math.cos(ang),
                     mid + r1 * math.sin(ang), AMB, 5, a * sk)
            circ(c, px, mid, 14, "#FFF3C4", a * sk)
        if heat:
            hp = ease_out(prog(t, heat, 1.5))
            sh = skia.GradientShader.MakeRadial((bx, mid), 520 * hp + 1, [C(ACC, 0.55 * hp * a), C(ACC, 0)], [0, 1])
            c.drawRect(skia.Rect.MakeXYWH(x0, y0, w, h), skia.Paint(Shader=sh))
        if labels:
            draw_text(c, "LAYER", x0 - 30, y0 + 105, 30, MUTED, "Bold", a, "right")
            draw_text(c, "LAYER", x0 - 30, y0 + h - 75, 30, MUTED, "Bold", a, "right")
            la = a * (ease_out(prog(t, sep, 0.5)) if sep else 1)
            draw_text(c, "SEPARATOR", x0 + w + 30, mid + 11, 30, INK, "Bold", la)
            draw_text(c, "thin plastic", x0 + w + 30, mid + 48, 26, MUTED, "Medium", la)
    return G(fn, 360, start)


def runaway_cycle(times, center_t):
    labels = ["Short circuit", "Heat", "More unstable", "More heat"]
    cols = [AMB, ACC, AMB, ACC]

    def fn(c, x, y, t):
        cx, cy, R = x, y + 300, 230
        for i, (lab, tt) in enumerate(zip(labels, times)):
            ang = -math.pi / 2 + i * math.pi / 2
            px, py = cx + R * math.cos(ang) * 1.45, cy + R * math.sin(ang)
            p = ease_out(prog(t, tt, 0.5))
            if p <= 0:
                continue
            tw_ = text_w(lab, 46, "Bold") + 60
            rr(c, px - tw_ / 2, py - 40, tw_, 80, 40, "#1B2028", p)
            rr(c, px - tw_ / 2, py - 40, tw_, 80, 40, cols[i], p, stroke=4)
            draw_text(c, lab, px, py + 16, 46, INK, "Bold", p, "center")
            # arrow to next node (arc)
            nxt = tt + 0.4
            ap = ease_out(prog(t, nxt, 0.6))
            a0 = ang + 0.42
            a1 = ang + math.pi / 2 - 0.42
            arc = skia.Path()
            steps = 20
            for k in range(steps + 1):
                aa = a0 + (a1 - a0) * (k / steps) * ap
                q = (cx + R * math.cos(aa) * 1.45, cy + R * math.sin(aa))
                arc.moveTo(*q) if k == 0 else arc.lineTo(*q)
            c.drawPath(arc, P(MUTED, 6, p))
            if ap > 0.95:
                aa = a1
                hx, hy = cx + R * math.cos(aa) * 1.45, cy + R * math.sin(aa)
                dx, dy = -math.sin(aa) * 1.45, math.cos(aa)
                n = math.hypot(dx, dy)
                dx, dy = dx / n, dy / n
                c.drawPath(path([(hx + dx * 18, hy + dy * 18), (hx - dx * 6 - dy * 14, hy - dy * 6 + dx * 14),
                                 (hx - dx * 6 + dy * 14, hy - dy * 6 - dx * 14)]), P(MUTED, a=p))
        p = ease_out(prog(t, center_t, 0.6))
        if p > 0:
            draw_text(c, "THERMAL", cx, cy - 8, 64, ACC, "Black", p, "center")
            draw_text(c, "RUNAWAY", cx, cy + 58, 64, ACC, "Black", p, "center")
    return G(fn, 600, times[0])


def stat_row(items, size=150):
    """items = [(value, dec, suffix, label, t), ...] side by side."""
    def fn(c, x, y, t):
        n = len(items)
        colw = 520
        for i, (v, dec, suf, lab, tt) in enumerate(items):
            cx = x + (i - (n - 1) / 2) * colw
            p = ease_out(prog(t, tt, 0.4))
            if p <= 0:
                continue
            k = ease_out(prog(t, tt, 1.0))
            s = (f"{v * k:.{dec}f}" + suf) if v is not None else suf
            draw_text(c, s, cx, y + size * 0.85, size, ACC if v is not None else INK, "Black", p, "center")
            draw_text(c, lab, cx, y + size + 60, 50, MUTED, "Bold", p, "center")
    return G(fn, size + 90, items[0][4])


def intestine(start, one, two, clamp_t, holes):
    def fn(c, x, y, t):
        a = ease_out(prog(t, start, 0.5))
        w = 1000
        x0 = x - w / 2
        tubes = [y + 70, y + 290]
        for ty in tubes:
            rr(c, x0, ty - 70, w, 140, 70, "#3A2A2E", a)
            rr(c, x0, ty - 70, w, 140, 70, "#C9877F", a, stroke=6)
        # one magnet passing through
        p1 = prog(t, one, 2.4)
        if one <= t < two:
            circ(c, x0 + 60 + p1 * (w - 120), tubes[0], 22, "#D0D5DD", a)
            if p1 > 0.2:
                draw_text(c, "1 magnet: usually passes", x, y - 10, 40, MUTED, "Bold", a, "center")
        if t >= two:
            p2 = ease_out(prog(t, two, 0.5))
            pc = ease_io(prog(t, clamp_t, 0.8))
            mx = x + 40
            y1 = lerp(tubes[0], tubes[0] + 52, pc)
            y2 = lerp(tubes[1], tubes[1] - 52, pc)
            # attraction field lines
            if pc < 0.99:
                for k in range(3):
                    ph = (t * 1.5 + k / 3) % 1
                    yy = lerp(y1 + 30, y2 - 30, ph)
                    circ(c, mx, yy, 4, COOL, a * p2 * (1 - abs(ph - 0.5) * 2) * 0.8)
            for yy in (y1, y2):
                circ(c, mx, yy, 22 * p2, "#D0D5DD", a)
            draw_text(c, "2+ magnets attract", x, y - 10, 40, AMB, "Bold", a * p2, "center")
            if pc > 0.9:
                draw_text(c, "clamped through the walls", x + 280, y + 192, 36, INK, "Bold", a, "left")
        if holes and t >= holes:
            ph = ease_out(prog(t, holes, 0.5))
            for yy in (tubes[0] + 70, tubes[1] - 70):
                circ(c, x + 40, yy, 16 * ph, ACC, a)
                circ(c, x + 40, yy, 28 * ph, ACC, a * 0.6, stroke=4)
            draw_text(c, "HOLES = MEDICAL EMERGENCY", x, y + 430, 44, ACC, "Black", a * ph, "center")
    return G(fn, 470, start)


def hub(times, center_t):
    names = ["phone", "hoverboard", "laptop", "watch"]
    labels = ["Note 7", "Hoverboard", "Laptop", "Fitbit"]

    def fn(c, x, y, t):
        cx, cy = x, y + 290
        pc = ease_out(prog(t, center_t, 0.5))
        pos = [(-560, -120), (-560, 170), (560, -120), (560, 170)]
        for (dx, dy), nm, lab, tt in zip(pos, names, labels, times):
            p = ease_out(prog(t, tt, 0.5))
            if p <= 0:
                continue
            lp = ease_out(prog(t, tt + 0.2, 0.5))
            ex, ey = cx + dx * 0.55, cy + dy * 0.4
            line(c, cx + dx, cy + dy, lerp(cx + dx, ex, lp), lerp(cy + dy, ey, lp), DIM, 5, p)
            icon(c, nm, cx + dx, cy + dy, 170, t, tt)
            draw_text(c, lab, cx + dx + (165 if dx > 0 else -165), cy + dy + 14, 38, MUTED, "Bold", p,
                      "left" if dx > 0 else "right")
        if pc > 0:
            icon(c, "battery", cx, cy - 20, 300, t, center_t, fill=ACC)
            draw_text(c, "LITHIUM-ION CELL", cx, cy + 200, 44, ACC, "Black", pc, "center")
    return G(fn, 600, min(times + [center_t]))


def pair_icons(a, b, ta, tb, kwa=None, kwb=None, burn_a=None, size=240):
    def fn(c, x, y, t):
        icon(c, a, x - 220, y + size / 2 + 10, size, t, ta, **(kwa or {}))
        if burn_a:
            burn(c, x - 220, y + size / 2 + 30, size * 0.8, t, burn_a)
        icon(c, b, x + 220, y + size / 2 + 10, size, t, tb, **(kwb or {}))
    return G(fn, size + 40, min(ta, tb))


def strike_prices(t1, t2):
    def fn(c, x, y, t):
        p1 = ease_out(prog(t, t1, 0.4))
        draw_text(c, "$4,000", x - 330, y + 150, 160, MUTED, "Black", p1, "center")
        st = ease_out(prog(t, t2 - 0.2, 0.4))
        line(c, x - 560, y + 95, x - 560 + 460 * st, y + 95, ACC, 10, p1)
        p2 = ease_out(prog(t, t2, 0.5))
        draw_text(c, "~$30", x + 330, y + 150, 160 * lerp(0.8, 1, back_out(prog(t, t2, 0.5))), ACC, "Black", p2,
                  "center")
        draw_text(c, "treadmill", x - 330, y + 220, 44, MUTED, "Bold", p1, "center")
        draw_text(c, "tiny metal box", x + 330, y + 220, 44, MUTED, "Bold", p2, "center")
    return G(fn, 250, t1)


def end_card(t0, tclick):
    def fn(c, x, y, t):
        p = ease_out(prog(t, t0, 0.5))
        w, h = 760, 428
        rr(c, x - w / 2, y, w, h, 24, "#161A20", p)
        rr(c, x - w / 2, y, w, h, 24, DIM, p, stroke=4)
        icon(c, "warning", x, y + h / 2, 170, t, t0 + 0.2)
        pc = ease_out(prog(t, tclick, 0.4))
        if pc > 0:
            rr(c, x - w / 2 - 8, y - 8, w + 16, h + 16, 30, ACC, pc, stroke=6)
            # cursor
            cx, cy = x + 250, y + h - 60 + (1 - pc) * 60
            c.drawPath(path([(cx, cy), (cx, cy + 70), (cx + 18, cy + 54), (cx + 32, cy + 84), (cx + 44, cy + 78),
                             (cx + 30, cy + 49), (cx + 52, cy + 48)]), P(INK, a=pc))
    return G(fn, 440, t0)


# ================================================================ timeline
# ---------- cold open
B(0.0, I("phone", 0.05, 300, smoke=1.0), T("A phone so dangerous", 0.2),
  T("airlines *banned it by name*", tw("air", 1.5)))
B(3.40, I("watch", 3.45, 300), T("A fitness watch", 3.5),
  T("that *burned people* while they wore it", tw("burned", 3.5)))
B(6.50, K("Today", 6.55), T("The *deadliest gadgets*", 6.75, 130), T("ever sold", tw("ever", 7), 130))
B(9.06, T("But first:", 9.1), T("the *phone*", tw("phone", 9.5), 130),
  S("not just a bad product", tw("wasn", 10.5)))
B(13.35, S("a bad product one of the biggest tech companies on Earth", 13.4),
  T("had to *kill twice*", tw("twice", 15), 130))

# ---------- 01 Galaxy Note 7
CH(18.85, 1, "Samsung Galaxy Note 7", "Released August 2016")
B(23.30, S("On paper…", 23.35), T("it was *perfect*.", 24.36, 140))
B(26.25, T("“One of the *best phones* ever made”", 26.4), S("— reviewers", 27.3))
B(tw("curved", 28), I("phone", None, 360),
  LIST([("Curved screen", tw("curved", 28)), ("Stylus", tw("stylus", 29)),
        ("Iris scanner", tw("irish", 29)), ("Water resistant", tw("water", 30))]), layout="side")
B(tw("millions", 32), T("*Millions* lined up to buy it",
                                                                            tw("millions", 32), 100))
B(tw("within", 34), T("But within *days*…", tw("within", 34), 120))
B(36.84, I("phone", 36.9, 300), T("Strange reports online", 37.0), S("started showing up", 37.6))
B(39.37, I("phone", 39.4, 330, smoke=39.6), T("Getting *dangerously hot*", 39.5),
  S("while charging", tw("charging", 40)), layout="side")
B(41.96, I("phone", 42.0, 330, smoke=42.0, burn=tw("burst", 43)), T("Some *smoked*.", 42.05),
  T("Some *burst into flames*.", tw("burst", 43)), S("…while sitting on a table", tw("sitting", 44)),
  layout="side")
B(tw("florida", 45), I("car", None, 330, burn=tw("jeep", 46)), K("Florida", tw("florida", 45)),
  T("A Note 7 set an owner's", tw("said", 46), 80), T("*Jeep on fire*", tw("jeep", 46), 110), layout="side")
B(50.50, T("Less than", 50.55, 80), N(3, 50.7, suf=" weeks", size=200), S("after launch", tw("lunch", 51)),
  T("Samsung *stopped selling* it", tw("stopped", 52), 80))
B(54.50, K("September 2016", 54.55), N(2.5, tw("recalled", 55.7), dec=1, suf="M", size=220),
  S("phones recalled worldwide", tw("phones", 57)))
B(tw("but", 59), T("Samsung: replacements are *safe*", tw("but", 59), 90),
  S("that promise lasted about a month", tw("lasted", 60)))
B(63.72, I("plane", 63.8, 300), K("Early October 2016", 63.8),
  T("Southwest flight *evacuated*", 65.41, 92), S("Louisville, before takeoff", tw("take", 66)))
B(69.48, I("phone", 69.5, 330, smoke=tw("smoke", 70)), T("Pouring out *smoke*", tw("pour", 69.5)),
  T("…a *replacement* phone", tw("replacement", 71)), S("one Samsung said was fixed", 74.31), layout="side")
B(77.00, T("That was *the end*.", 77.05, 130))
B(78.57, K("October 11, 2016", 78.6), T("Note 7 *killed for good*", 80.07, 120))
B(82.21, I("plane", 82.3, 280), T("Banned from *every flight*", tw("bandit", 82.5), 100),
  S("by the U.S. government", 82.5))
B(tw("telling", 84), S("If you own this phone:", tw("telling", 84) + 0.2), T("Don't *turn it on*.", 88.52, 110),
  T("Don't *charge it*.", tw("charge", 89), 110))
B(91.27, T("The last time you'd ever hear", 91.3, 84), T("that about a *phone*", tw("phone", 92), 110))

# ---------- what went wrong
B(93.67, T("So what actually", 93.7, 110), T("*went wrong*?", tw("wrong", 94), 150))
B(tw("turns", 95), T("The replacement had a", tw("replacement", 96), 90),
  T("*different problem*", tw("different", 97), 130), S("than the original", tw("original", 98)))
B(tw("inside", 99), T("Inside a *lithium-ion* battery", tw("inside", 99), 84), SP(20),
  battery_cell(tw("inside", 99) + 0.2, sep=tw("razor", 104), touch=tw("touch", 107), heat=tw("short", 108.3)))
B(109.75, runaway_cycle([109.85, 110.31, 112.51, 113.8], 115.84),
  S("once it starts, there's no stopping it", 118.28))
B(120.74, K("Batch 1 · original", 120.8), T("Battery *too big* for its space", 122.21, 90), SP(10),
  battery_cell(121.0, squeeze=126.41, heat=127.6, labels=False))
B(129.35, K("Batch 2 · replacements", 129.4), T("A different supplier", 129.6, 80),
  LIST([("*Welding flaws*", tw("welding", 131)), ("Missing *protective tape*", tw("protect", 133))], 90))
B(136.20, T("Two different companies.", 136.25, 96), T("Two different mistakes.", 137.64, 96),
  T("*Same result.*", 139.21, 140))
B(141.51, S("the disaster cost Samsung about", 141.6), N(5, tw("five", 142), pre="$", suf=" billion", size=200),
  T("all to beat the *iPhone* to market", tw("rushed", 144), 72))

# ---------- 02 Hoverboard
B(149.13, T("A phone is something", 149.2, 100), T("you *pick for yourself*.", tw("pick", 150), 100))
B(152.45, I("tree", 152.5, 320), T("Under millions of", tw("millions", 153), 80),
  T("*Christmas trees*", tw("christmas", 154), 110), S("and it didn't even do what the name said",
                                                         tw("didn", 155)), layout="side")
CH(158.73, 2, "The Hoverboard", "The must-have gift of 2015")
B(160.58, I("hoverboard", 160.6, 300), T("It doesn't *hover*.", 160.7, 110),
  S("just two wheels and a pair of motors", tw("wheels", 162)))
B(tw("twenty", 164), K("2015", tw("twenty", 164)), T("The *must-have gift*", tw("must", 165), 130),
  S("of the year", tw("year", 166)))
B(167.43, LIST([("Celebrities riding them", 167.45), ("Kids begging for them", 169.22),
                ("Factories *pumping them out*", tw("factories", 170))], 84))
B(175.33, I("factory", 175.4, 300), T("Factories *cutting corners*", tw("cutting", 176), 96),
  S("on the one part that mattered most", tw("part", 177)))
B(179.17, I("battery", 179.2, 360, fill=ACC), T("The *battery*.", 179.2, 140), layout="side")
B(181.03, I("house", 181.1, 300, burn=tw("fire", 182)), K("December 2015", 181.1),
  T("*On fire* in people's homes", tw("fire", 182), 88),
  LIST([("often while *charging*", 184.97), ("often while the family *slept*", 186.89)], 60), layout="side")
B(tw("amazon", 189), LIST([("Amazon *pulled them* & refunded buyers", tw("amazon", 189)),
                           ("U.K. *seized thousands* at ports", tw("officials", 192))], 80))
B(tw("underwriters", 195), I("shield", None, 300), K("Underwriters Laboratories", tw("underwriters", 195)),
  S("the company that tests electronics for safety", 197.32),
  T("*None* of the boards met", 200.07, 88), T("the safety standard", 202.34, 88), layout="side")
B(tw("bann", 203), I("plane", None, 280), T("Airlines *banned them*", tw("bann", 203), 110),
  S("in the cabin and in the cargo hold", tw("cabin", 204)))
B(tw("house", 206), I("house", None, 280), K("2016 · Harrisburg, Pennsylvania", tw("house", 206)),
  T("A house fire killed", tw("killed", 209), 96), T("*two young girls*", tw("two", 209.5), 120),
  S("investigators linked it to a hoverboard", 211.53))
B(215.01, K("July 2016", 215.05), N(500000, tw("recall", 218), size=200), S("hoverboards recalled", 218.5),
  S("from 8 different companies", tw("eight", 219)))
B(223.33, N(99, tw("ninety", 224), size=230), T("*fires* in 24 states", tw("fires", 225), 90))
B(tw("why", 226.5), T("So why were they", tw("why", 226.5), 110), T("*burning*?", tw("burn", 227), 160))
B(228.77, LIST([("Cells packed *tightly* together", 228.8), ("Almost *no protection* circuits", 231.62),
                ("Charged overnight with a *cheap charger*", 233.83)], 76))
B(237.45, S("basically…", 237.5), T("A *bomb on wheels*", 238.47, 140), S("with a ribbon on top", tw("ribbon", 239)))
B(241.41, I("shield", 241.5, 280), T("A new *safety standard*", tw("safety", 243), 100),
  S("hoverboards must follow today", tw("follow", 244)), T("^UL 2272^", tw("twenty", 247.5), 110))
B(tw("rule", 250), T("A rule that came", tw("rule", 250), 100), T("*after* the damage", tw("after", 251), 130))
B(tw("industry", 253), T("How long did the industry", tw("industry", 253), 96),
  T("*know* about the problem?", tw("knew", 254), 96))
B(256.61, S("and it started with something", 256.65), T("much…", 258.0, 120), T("*much smaller*.", 258.66, 150))

# ---------- 03 Sony laptop batteries
CH(260.26, 3, "Exploding Laptop Batteries", "2006")
B(262.12, I("laptop", 262.2, 320, burn=tw("burst", 264)), K("A conference in Japan", 262.3),
  T("A Dell laptop", 262.6, 90), T("*bursts into flames*", tw("burst", 264), 100),
  S("and the photo goes around the world", 266.18), layout="side")
B(268.61, S("within weeks", 268.65), T("The *biggest electronics recall*", tw("biggest", 270), 96),
  S("in history at that time", tw("history", 271)))
B(273.19, stat_row([(4.1, 1, "M", "Dell", 273.3), (1.8, 1, "M", "Apple", tw("apple", 275)),
                    (None, 0, "+ more", "Lenovo & others", tw("linovo", 279))]), SP(40),
  S("laptop batteries recalled", 274.0))
B(280.5, T("All of them had", 280.55, 96), T("the same thing in *common*", tw("same", 281.4), 110))
B(282.79, T("Every battery was made by", 282.8, 90), T("*Sony*", tw("sony", 283.5), 220))
B(285.29, T("The cause was almost", 285.3, 96), T("*unbelievable*", tw("unbeliev", 286), 140))
B(288.04, T("Tiny *metal particles* got inside", tw("tiny", 289), 84), SP(10),
  battery_cell(288.3, specks=tw("tiny", 289), labels=False), S("specks you can barely see", tw("specks", 290)))
B(295.72, S("most of the time, they did nothing… but", 295.75),
  T("over time one could *poke through*", 300.13, 84), SP(10),
  battery_cell(295.8, specks=295.8, pierce=300.6, heat=303.4, labels=False),
  T("and *short out* the battery", 303.08, 84))
B(306.21, I("laptop", 306.3, 300), S("one that worked perfectly for months", 306.3),
  T("was carrying a *time bomb*", 308.17, 96), S("the size of a grain of dust", tw("size", 309)))
B(310.89, I("cash", 311.0, 260), S("in the end, Sony paid", 311.88), T("*hundreds of millions*", tw("hundreds", 312), 120),
  S("to fix it", tw("fix", 314)))
B(315.43, T("You'd think every company", 315.5, 90), T("would learn from that…", tw("learn", 316.5), 90))
B(317.73, T("*Nobody did.*", 317.75, 170))
B(319.69, K("11 years later", 319.7), S("one of the most trusted names in fitness", 321.25),
  T("put the same battery", tw("same", 323), 96), T("*on your wrist*", tw("wrist", 324), 140))

# ---------- 04 Fitbit Ionic
CH(326.73, 4, "Fitbit Ionic", "Released 2017")
B(330.66, I("watch", 330.7, 340), T("Fitbit's shot at the", 330.8, 84), T("*Apple Watch*", tw("apple", 331.5), 110),
  LIST([("GPS", 333.73), ("Heart-rate sensor", tw("heart", 334)), ("Bright screen", tw("bright", 335))], 60),
  layout="side")
B(337.64, I("watch", 337.7, 340, screen=lambda t: mix("#2B3340", ACC, prog(t, tw("overheating", 340), 1.5))),
  S("on sale for years… then reports", 337.7), T("Battery *overheating*", tw("overheating", 340), 100),
  T("*while people wore it*", tw("wearing", 342), 80), layout="side")
B(343.72, K("March 2022", 343.75), N(1.7, tw("recall", 346), dec=1, suf="M", size=220),
  S("watches recalled", tw("watches", 348)))
B(tw("hundred", 349), N(115, tw("hundred", 349), size=220), S("reports of overheating in the U.S. alone",
                                                                tw("overheating", 351)))
B(353.48, N(78, 353.5, size=230), T("people *burned*", tw("burned", 354.5), 100),
  S("2 with third-degree burns", 355.56))
B(358.89, T("“Stop using it.”", 358.9, 110), N(299, tw("two", 361), pre="$", suf=" refund", size=150, color=AMB))
B(364.29, T("The part that really", 364.3, 96), T("*bothered regulators*", tw("bothered", 365), 120))
B(366.79, T("Complaints *piling up*", 366.8, 100), S("long before the recall", tw("long", 368)),
  T("…and *not reported* in time", 369.83, 90))
B(372.45, I("gavel", 372.5, 260), K("Years later", 372.5), T("The CPSC fined *Google*", tw("fine", 373), 90),
  S("which now owned Fitbit", 375.33), N(12, tw("twelve", 377), pre="$", suf="M+", size=150, color=AMB),
  S("for waiting too long", tw("waiting", 378)), layout="side")

# ---------- bridge to washer
B(380.33, S("so far…", 380.35), T("everything has been a *battery*", 381.25, 100))
B(384.26, T("The next gadget", 384.3, 100), T("*didn't need one*.", tw("didn", 385), 130))
B(386.41, T("It didn't even need to be *on*", 386.45, 96), T("to put someone *in the hospital*", tw("put", 387.5), 90))
B(389.93, T("Same company that was", 389.95, 90), T("*still burning*", tw("still", 390.5), 130),
  S("from its phone disaster", tw("phone", 391)))
B(tw("busy", 392.5), S("while Samsung was losing billions on a phone…", tw("busy", 392.5)),
  T("it was selling something", 396.71, 96), T("*much bigger*", tw("bigger", 397.5), 140))
B(399.05, T("The part that was supposed to", 399.1, 90), T("*stay shut*…", tw("shut", 400), 120),
  T("*came off*.", tw("off", 401), 140))

# ---------- 05 Samsung washer
CH(403.24, 5, "Samsung Top-Loading Washer", "Recalled 2016")
B(406.31, K("October 2016", 406.35), S("just weeks after the Note 7 recall", 408.45),
  T("Samsung's *second* recall", tw("second", 411), 110))
B(413.64, I("washer", 413.7, 300), N(2.8, tw("two", 414.5), dec=1, suf="M", size=200), S("washers", tw("washers", 415)))
B(tw("reason", 416), I("washer", None, 380, anim="shake", spin=lambda t: t * 900,
                         lid=lambda t: ease_out(prog(t, tw("fly", 419), 0.9))),
  S("the reason sounds like a joke", tw("reason", 416)), T("During the *spin cycle*…", tw("spin", 418), 92),
  T("the top could *fly off*", tw("fly", 419), 100), layout="side")
B(422.12, I("washer", 422.2, 340, anim="shake", spin=lambda t: t * 1400), T("A heavy machine", 422.3, 90),
  T("spinning so fast it", tw("spinning", 423.5), 80), T("*shakes itself apart*", tw("shakes", 424.5), 100),
  layout="side")
B(427.46, T("*Hundreds* of reports", 427.5, 100), S("of the top coming off", tw("top", 428.5)),
  N(9, tw("nine", 431), size=200), S("people hurt — including a broken jaw", tw("hurt", 431.5)))
B(435.14, T("The part that made people", 435.2, 96), T("*so angry*", tw("angry", 436), 140))
B(437.64, S("Samsung's first advice wasn't “stop using it”", 437.7),
  T("“Wash *bulky loads*", tw("wash", 441), 110), T("on the *delicate* cycle”", tw("delicate", 442), 110))
B(tw("means", 444), T("It *knew* the machine", tw("knew", 445), 110), T("couldn't handle a heavy load", tw("handle", 445.5), 90),
  S("and still sold it as a washing machine", tw("still", 447)))
B(tw("after", 449.5), K("After the recall", tw("after", 449.5)),
  LIST([("Repairs", tw("repairs", 451)), ("Rebates", tw("rebates", 452)), ("Refunds", tw("refunds", 452.5))], 90))
B(tw("so", 453.5), T("No, the washer didn't", tw("no", 454), 90), T("set your house *on fire*…", tw("house", 455), 100))
B(456.36, K("In one year, Samsung recalled", 456.4),
  pair_icons("phone", "washer", tw("phone", 458), tw("washer", 459.5), burn_a=tw("burned", 459),
             kwb={"lid": lambda t: ease_out(prog(t, tw("attacked", 460), 0.8))}),
  T("a phone that *burned*", tw("phone", 458), 84), T("and a washer that *attacked*", tw("attacked", 460), 84))
B(462.05, T("At least with a washing machine", 462.1, 84), T("you *know* it's dangerous", 463.97, 110))
B(466.09, T("Nobody expected danger", 466.1, 100), T("from the *next one*", tw("next", 467), 110),
  S("it was supposed to make you healthier", 468.42))

# ---------- 06 Peloton Tread+
CH(472.49, 6, "Peloton Tread+", "Recalled 2021")
B(474.82, I("treadmill", 474.9, 290), S("a treadmill that cost over", 474.9),
  N(4000, tw("four", 475.5), pre="$", suf="+", size=170, color=AMB), S("giant touchscreen, huge following", 477.57),
  layout="side")
B(480.90, I("treadmill", 480.95, 300, gap=lambda t: t > tw("open", 485)), T("A *design problem*", tw("design", 481.5), 100),
  S("nobody thought about", tw("nobody", 482)),
  LIST([("Sat *higher* off the ground", tw("higher", 483.5)), ("*Open space* under the belt", tw("open", 485))], 60),
  layout="side")
B(488.49, pair_icons("child", "paw", tw("child", 489.5), tw("pet", 490.5), size=220),
  T("Just the right size for a", 488.5, 84), T("*child* or a *pet*", tw("child", 489.5), 120),
  S("or anything else that could get pulled in", 492.17))
B(495.49, K("Early 2021", 495.5), T("Reports started *adding up*", tw("report", 497), 100))
B(499.11, T("*One child died*", 499.15, 130), S("dozens of other incidents, including", tw("dozens", 500)),
  S("injuries to children and pets", tw("injuries", 502)))
B(tw("april", 503.5), K("April 2021", tw("april", 503.5)), T("Government: *stop using it*", 505.77, 100),
  S("especially with kids or animals at home", 508.55))
B(511.40, T("Peloton's response", 511.45, 100), T("was *shocking*", tw("shocking", 512.5), 130))
B(513.64, S("it called the warning", 513.7), T("“*inaccurate* and *misleading*”", tw("inaccurate", 514), 110),
  S("pushed back against its own regulators and kept selling", 516.36))
B(521.19, S("a few weeks later", 521.2), N(125000, tw("hundred", 524), size=180),
  S("treadmills recalled", tw("treadmills", 525)), T("CEO: fighting the warning *was a mistake*", tw("admitted", 528), 64))
B(530.53, I("gavel", 530.6, 260), S("later, Peloton agreed to pay", 531.4),
  N(19, tw("nineteen", 532.5), pre="$", suf="M", size=180, color=AMB), S("for how long it waited to report",
                                                                         534.82), layout="side")
B(538.47, T("Why do safety warnings", 538.5, 96), T("feel *so slow*?", tw("slow", 540), 120))
B(541.57, S("this is what it looks like from the inside", 541.6), T("A product that *hurts people*", tw("hurts", 543.5), 96),
  T("and a lot of *money* to protect", 546.05, 96))
B(548.42, strike_prices(tw("four", 548.6), tw("thirty", 552)), SP(20),
  S("even a $4,000 treadmill takes a back seat to…", 548.5))

# ---------- 07 Buckyballs
B(555.65, I("magnets", 555.7, 300), T("A little *desk toy*", 555.7, 110),
  S("millions bought it to relieve stress", 557.13))
CH(560.23, 7, "Buckyballs", "Tiny, powerful magnets")
B(562.09, I("magnets", 562.1, 340), T("Tiny, *powerful* magnets", 562.15, 96),
  S("hundreds of little silver spheres", tw("hundreds", 565)), S("shape them into anything", tw("shape", 567)),
  layout="side")
B(tw("marketed", 568.5), T("Marketed for *adults*", tw("marketed", 568.5), 110),
  S("office desks · fidgeting during a meeting", tw("office", 570)))
B(tw("problem", 572.5), I("candy", None, 280), T("Kids thought they were", tw("kid", 573.5), 90),
  T("*candy*", tw("candy", 575), 140), S("teens used them as fake tongue & lip piercings", tw("tea", 576)))
B(580.29, T("Some got *swallowed*.", 580.3, 130))
B(582.41, intestine(582.45, 582.6, tw("two", 586), tw("clamp", 590), tw("holes", 593.5)))
B(597.83, I("hospital", 597.9, 300), T("Kids needing", 597.9, 90), T("*emergency surgery*", tw("emergency", 599), 110),
  S("visits kept growing year after year", 601.96), layout="side")
B(606.37, K("2012", 606.4), T("The government went after", 607.85, 96), T("the *company*", tw("company", 609), 110),
  S("…and then the CEO, personally", 609.93))
B(tw("fought", 611.5), S("he fought back with a public campaign", tw("fought", 611.5)),
  T("“*Save* the product”", tw("save", 614), 120))
B(616.01, T("Sales *stopped*.", 616.05, 110), T("The company *shut down*.", tw("shut", 617), 110))
B(618.82, I("gavel", 618.9, 260), S("a few years later", 618.9), T("A court *overturned*", tw("overturned", 620), 110),
  T("the ban", tw("ban", 621), 110), layout="side")
B(622.02, S("safety rules caught up in the end", 622.05), K("2022", 624.2),
  T("New federal rules *limit* how strong", tw("limited", 627), 84), T("these magnets can be", tw("magnets", 628.5), 84))
B(630.76, S("and that's the thing about gadgets", 630.8), T("Sometimes the danger isn't in the *design*", 632.9, 80),
  T("it's in *who ends up holding it*", 635.3, 96))
B(637.45, T("A gadget that killed", tw("killed", 639), 100), T("*the one person who knew it best*", tw("one", 640), 90))

# ---------- 08 Segway
CH(643.08, 8, "Segway", "2010")
B(645.2, K("2009", 645.25), I("segway", 645.3, 280), S("British businessman Jimi Heselden", 645.4),
  T("*bought* the company that made the Segway", 647.08, 76))
B(649.64, I("segway", 649.7, 340), T("The two-wheeled scooter", 649.8, 84),
  S("“supposed to change how cities work”", tw("supposed", 651)),
  T("one of the most *hyped* inventions", 653.13, 76), layout="side")
B(tw("later", 656.5), K("2010 · Yorkshire, England", tw("later", 656.5)),
  T("Riding a Segway on his estate", 658.21, 88), T("he went *off a cliff*", tw("cliff", 662), 120),
  S("into a river below", tw("river", 663)))
B(tw("died", 664), T("He died at *62*.", tw("died", 664), 130),
  S("the owner of Segway, killed by his own Segway", 665.73))
B(669.38, T("A *tragic accident*", tw("tragic", 670), 130), S("no one blamed the machine", 672.26))
B(674.09, S("but if you want to understand", 674.1), T("how fast we *trust* new gadgets", tw("trust", 676), 100),
  S("that's the story", tw("story", 678)))
B(679.24, S("the final gadget on this list", 679.3), T("proves we're making", tw("proves", 681), 90),
  T("the *same mistake*", tw("same", 682), 130))

# ---------- 09 Power bank
B(683.85, T("You probably have one", 683.9, 100), T("in your *bag right now*", tw("bag", 685), 120))
CH(686.60, 9, "The Power Bank", "Probably in your bag")
B(688.33, I("powerbank", 688.4, 340), T("We all carry them", tw("all", 689), 96), T("They're *cheap*.", tw("cheap", 692), 110),
  S("nobody thinks twice about them", 693.32), layout="side")
B(tw("twenty", 695), K("2025", tw("twenty", 695)), S("Anker, one of the most trusted names in charging", tw("anchor", 696)),
  N(1, tw("million", 700.5), suf="M+", size=200), S("power banks recalled", tw("power", 701)),
  T("*fire* and *explosion* risk", tw("fire", 702), 84))
B(tw("first", 704.5), T("Not the first time", tw("first", 704.5), 100),
  LIST([("Fires in *bags*", tw("bags", 708.5)), ("in *cars*", tw("cars", 709)), ("even on *airplanes*", tw("aeroplanes", 710))], 76))
B(tw("air", 711.5), I("plane", None, 300), T("Airlines now *restrict*", tw("restrict", 712.5), 110),
  S("how you use them in the air", tw("use", 713)))
B(715.27, T("Remember what's inside?", 715.3, 110))
B(717.61, hub([tw("note", 718), tw("hover", 720.87), tw("lap", 722.28), tw("watch", 724)], 718.0))
B(tw("battery", 724.5), T("*Huge energy*, tiny space", tw("huge", 725.5), 100), SP(10),
  battery_cell(tw("battery", 724.5), sep=728.6, labels=True),
  T("a thin layer between *safe* and *disaster*", tw("thin", 729.5), 76))
B(733.70, T("What do *all* of these", 733.75, 100), T("have in *common*?", tw("common", 734.5), 120))
B(735.85, LIST([("Rushed to *market*", 735.9), ("Cheaper, smaller, *faster*", 737.48),
                ("Warning signs? Companies *waited*", tw("waited", 742))], 84))
B(tw("because", 744.5), T("In tech, being first", tw("being", 745), 100), T("*makes money*", tw("makes", 746), 140),
  T("Being careful *costs it*", 748.2, 100))
B(750.63, pair_icons("phone", "powerbank", 750.7, tw("power", 752.5), burn_a=None, size=240),
  T("Phone hot while *charging*?", tw("hot", 751.5), 90), T("Power bank *warm* in your bag?", tw("power", 752.5), 90))
B(755.59, LIST([("Don't *ignore* it", 755.6), ("*Unplug* it", tw("unplug", 757)),
                ("Move it away from anything that can *burn*", tw("move", 757.5))], 76))
B(tw("only", 760.5), S("it only takes", tw("only", 760.5)), T("one *tiny mistake*", tw("tiny", 761.5), 120),
  T("to turn a gadget into a *disaster*", tw("disaster", 763), 90))
B(764.10, S("if you want to see what else we've trusted at home", 764.2),
  end_card(tw("check", 767), tw("click", 771)),
  T("The deadliest *kitchen appliances* ever sold", tw("kitchen", 768), 72),
  S("one was in nearly every American home", tw("nearly", 770)))

finalize(TOTAL)
render_frame = render_frame  # noqa: F405
