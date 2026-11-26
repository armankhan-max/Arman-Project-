"""Adult characters with realistic proportions (like the grown-up characters in the reference video).

Childhood stays chibi; adults get ~7-head proportions, almond eyes, lips, cel shading and thinner outlines.
Same pose vocabulary as the chibi kit (angles: 0 = down, + = outward, 180 = up).
"""
import math

import skia

from gfx import P, xf, clamp, lerp, mixhex, linear, fill_shader, line

AO = "#1f140e"   # outline
AW = 3.2         # outline width


def shp(c, path, fill, ow=AW, a=1.0):
    c.drawPath(path, P(fill, a=a))
    if ow:
        c.drawPath(path, P(AO, ow, a))


def ov(c, x, y, rx, ry, fill, ow=AW):
    p = skia.Path()
    p.addOval(skia.Rect(x - rx, y - ry, x + rx, y + ry))
    shp(c, p, fill, ow)
    return p


def rr(c, x, y, w, h, r, fill, ow=AW):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r))
    shp(c, p, fill, ow)
    return p


def shade_clip(c, path, col, dx=0.0, a=0.28, side=1):
    """Cel shading: darken the far side of a shape."""
    c.save()
    c.clipPath(path, skia.ClipOp.kIntersect, True)
    b = path.getBounds()
    w = b.width()
    if side > 0:
        c.drawRect(skia.Rect(b.left() + w * (0.62 + dx), b.top() - 5, b.right() + 5, b.bottom() + 5), P(col, a=a))
    else:
        c.drawRect(skia.Rect(b.left() - 5, b.top() - 5, b.left() + w * (0.3 - dx), b.bottom() + 5), P(col, a=a))
    c.restore()


def face_path(rx=30, ry=38):
    p = skia.Path()
    p.moveTo(0, -ry)
    p.cubicTo(rx * 0.95, -ry, rx * 1.05, -ry * 0.35, rx * 0.98, ry * 0.05)
    p.cubicTo(rx * 0.92, ry * 0.55, rx * 0.45, ry * 1.0, 0, ry * 1.02)
    p.cubicTo(-rx * 0.45, ry * 1.0, -rx * 0.92, ry * 0.55, -rx * 0.98, ry * 0.05)
    p.cubicTo(-rx * 1.05, -ry * 0.35, -rx * 0.95, -ry, 0, -ry)
    p.close()
    return p


def a_hair_back(c, style, hc, t, fem):
    if style == "pony":
        sw = math.sin(t * 1.8) * 3
        p = skia.Path()
        p.moveTo(-30, -18)
        p.cubicTo(-38, -60, 38, -60, 32, -18)
        p.lineTo(34, 10)
        p.cubicTo(44, 40, 40 + sw, 90, 30 + sw, 130)
        p.cubicTo(22 + sw, 95, 24, 50, 18, 20)
        p.close()
        shp(c, p, hc)
        for k in range(5):
            y = 30 + k * 20
            c.drawLine(26 + sw * k / 5, y, 38 + sw * k / 5, y + 10, P(mixhex(hc, "#000000", 0.5), 2))
    elif style in ("long", "braids"):
        p = skia.Path()
        p.moveTo(-31, -20)
        p.cubicTo(-38, -64, 38, -64, 31, -20)
        p.cubicTo(40, 20, 42, 45, 36, 58)
        p.lineTo(-36, 58)
        p.cubicTo(-42, 45, -40, 20, -31, -20)
        p.close()
        shp(c, p, hc)
    elif style == "curly":
        for i in range(16):
            a = i / 16 * math.tau
            ov(c, math.cos(a) * 38, math.sin(a) * 40 - 6, 15, 15, hc, ow=2.4)
        ov(c, 0, -6, 40, 42, hc, ow=0)


def a_hair_front(c, style, hc, t):
    dk = mixhex(hc, "#000000", 0.35)
    if style in ("pony", "long", "braids"):
        p = skia.Path()
        p.moveTo(-31, 2)
        p.cubicTo(-36, -52, 36, -52, 31, 2)
        p.cubicTo(28, -18, 14, -30, 0, -30)
        p.cubicTo(-14, -30, -28, -18, -31, 2)
        p.close()
        shp(c, p, hc)
        c.drawLine(0, -40, 0, -30, P(dk, 2))
        c.drawLine(-18, -36, -26, -14, P(dk, 1.6))
        c.drawLine(18, -36, 26, -14, P(dk, 1.6))
    elif style == "curly":
        for i in range(8):
            a = math.pi + 0.15 + i / 7 * (math.pi - 0.3)
            ov(c, math.cos(a) * 28, math.sin(a) * 30 - 8, 11, 10, hc, ow=0)
    elif style in ("short", "jason", "slick", "gray", "cal"):
        p = skia.Path()
        p.moveTo(-31, -6)
        p.cubicTo(-34, -50, 30, -56, 31, -8)
        if style == "jason":
            p.cubicTo(26, -24, 12, -26, 2, -30)
            p.cubicTo(-10, -24, -24, -26, -31, -6)
        elif style == "slick":
            p.cubicTo(24, -32, -10, -34, -31, -6)
        else:
            p.cubicTo(22, -28, -14, -30, -31, -6)
        p.close()
        shp(c, p, hc)
        if style == "jason":
            for k in range(4):
                c.drawLine(-14 + k * 8, -42, -8 + k * 8, -30, P(dk, 1.6))
        if style == "slick":
            c.drawLine(-12, -40, 18, -38, P("#ffffff", 2, 0.35))
    elif style == "buzz":
        p = skia.Path()
        p.moveTo(-30, -10)
        p.cubicTo(-32, -50, 32, -50, 30, -10)
        p.cubicTo(22, -30, -22, -30, -30, -10)
        p.close()
        shp(c, p, hc, ow=2)
    elif style == "cap":
        p = skia.Path()
        p.moveTo(-33, -16)
        p.cubicTo(-34, -58, 34, -58, 33, -16)
        p.close()
        shp(c, p, hc)
        rr(c, -36, -22, 72, 10, 4, mixhex(hc, "#000000", 0.4))
        ov(c, 0, -36, 7, 8, "#e8c25a", ow=2)
    elif style == "mask":
        p = skia.Path()
        p.addPath(face_path(32, 40))
        hole = skia.Path()
        hole.addRRect(skia.RRect.MakeRectXY(skia.Rect(-22, -16, 22, 2), 8, 8))
        m = skia.Op(p, hole, skia.PathOp.kDifference_PathOp)
        shp(c, m, hc)
    elif style == "bald":
        c.drawLine(-14, -30, -4, -35, P("#ffffff", 2.5, 0.3))


def a_face(c, L, skin, expr, t, look, talk, blink, fem):
    lx, ly = look[0] * 1.6, look[1] * 1.2
    dk = mixhex(skin, "#000000", 0.38)
    if L.get("shades"):
        for sx in (-1, 1):
            rr(c, sx * 13 - 11, -12, 22, 13, 4, "#101014", ow=2)
        c.drawLine(-2, -7, 2, -7, P("#101014", 3))
    else:
        for sx in (-1, 1):
            x = sx * 13
            if blink or expr in ("laugh",):
                p = skia.Path()
                p.moveTo(x - 7, -5)
                p.quadTo(x, -9 if expr == "laugh" else -4, x + 7, -5)
                c.drawPath(p, P(AO, 2.6))
                continue
            p = skia.Path()
            op = 6.5 if expr in ("shock", "scared") else 5.0
            p.moveTo(x - 8, -5)
            p.quadTo(x, -5 - op * 1.3, x + 8, -5)
            p.quadTo(x, -5 + op * 0.8, x - 8, -5)
            p.close()
            c.drawPath(p, P("#f8f4ec"))
            c.save()
            c.clipPath(p, skia.ClipOp.kIntersect, True)
            c.drawCircle(x + lx, -5.5 + ly, 4.2, P("#3a2416"))
            c.drawCircle(x + lx, -5.5 + ly, 2.2, P("#0e0806"))
            c.drawCircle(x + lx - 1.4, -7 + ly, 1.1, P("#ffffff"))
            c.restore()
            lid = skia.Path()
            lid.moveTo(x - 8.5, -4.5)
            lid.quadTo(x, -5 - op * 1.35, x + 8.5, -5.5)
            c.drawPath(lid, P(AO, 2.8 if fem else 2.2))
            if fem:
                c.drawLine(x + sx * 8, -5.5, x + sx * 11, -8, P(AO, 2))
            if expr == "cry":
                k = (t * 1.3 + (0.5 if sx > 0 else 0)) % 1
                c.drawOval(skia.Rect.MakeXYWH(x - 2, 0 + k * 22, 4, 6), P("#7fc8ff", a=1 - k))
        if L.get("glasses"):
            for sx in (-1, 1):
                c.drawRoundRect(skia.Rect(sx * 13 - 11, -14, sx * 13 + 11, 2), 4, 4, P(AO, 2))
            c.drawLine(-2, -8, 2, -8, P(AO, 2))
    # brows
    for sx in (-1, 1):
        x = sx * 13
        by = -16
        if expr in ("angry", "determined"):
            pts = (x - sx * 9, by - 2, x + sx * 6, by + 3)
        elif expr in ("sad", "cry", "worried", "scared"):
            pts = (x - sx * 9, by + 3, x + sx * 6, by - 2)
        elif expr == "shock":
            pts = (x - 8, by - 4, x + 8, by - 5)
        elif expr == "smirk":
            yy = by - (3 if sx > 0 else 0)
            pts = (x - 8, yy, x + 8, yy - 1)
        else:
            pts = (x - 8, by, x + 8, by - 1.5)
        c.drawLine(pts[0], pts[1], pts[2], pts[3], P(L["hc"] if L["hc"] not in ("#151518",) else AO, 3.4))
    # nose
    p = skia.Path()
    p.moveTo(-1, -2)
    p.lineTo(-3, 11)
    p.quadTo(0, 14, 4, 11)
    c.drawPath(p, P(dk, 2))
    # mouth
    my = 22
    lipc = "#a8524a" if fem else mixhex(skin, "#7a2a2a", 0.45)
    op = 0.0
    if talk > 0:
        op = (0.5 + 0.5 * math.sin(t * 19)) * (0.6 + 0.4 * math.sin(t * 7.3)) * talk
    if expr in ("shock", "scared"):
        ov(c, 0, my + 1, 5, 6 + op * 2, "#4a1616", ow=2)
    elif expr in ("happy", "laugh") or op > 0.15:
        o = max(op, 0.7 if expr == "laugh" else 0.45 if expr == "happy" else 0)
        p = skia.Path()
        p.moveTo(-10, my - 1)
        p.quadTo(0, my + 2 + 12 * o, 10, my - 1)
        p.close()
        shp(c, p, "#4a1616", ow=2)
        c.save()
        c.clipPath(p, skia.ClipOp.kIntersect, True)
        c.drawRect(skia.Rect(-10, my - 2, 10, my + 2), P("#ffffff"))
        c.restore()
    else:
        p = skia.Path()
        if expr in ("smile",):
            p.moveTo(-9, my - 1)
            p.quadTo(0, my + 5, 9, my - 1)
        elif expr in ("sad", "cry", "worried"):
            p.moveTo(-8, my + 2)
            p.quadTo(0, my - 3, 8, my + 2)
        elif expr == "smirk":
            p.moveTo(-8, my + 1)
            p.quadTo(4, my + 2, 10, my - 3)
        elif expr in ("angry", "determined"):
            p.moveTo(-8, my + 1)
            p.lineTo(8, my)
        else:
            p.moveTo(-7, my)
            p.quadTo(0, my + 2, 7, my)
        if fem:
            c.drawPath(p, P(lipc, 5))
        c.drawPath(p, P(AO, 2.2))
    if L.get("mustache"):
        p = skia.Path()
        p.moveTo(-12, my - 3)
        p.quadTo(0, my - 11, 12, my - 3)
        p.quadTo(0, my - 6, -12, my - 3)
        shp(c, p, L["hc"], ow=1.6)
    if L.get("stubble"):
        p = skia.Path()
        p.moveTo(-28, 4)
        p.cubicTo(-26, 30, -12, 40, 0, 40)
        p.cubicTo(12, 40, 26, 30, 28, 4)
        p.cubicTo(18, 26, -18, 26, -28, 4)
        c.drawPath(p, P("#4a2e1c", a=0.28))


def a_head(c, who, lk, L, skin, expr, t, look=(0, 0), talk=0.0, blink_ok=True, scale=1.0):
    from g6fx import hsh
    fem = L.get("fem", False)
    with xf(c, s=scale):
        hs = L["hair"]
        a_hair_back(c, hs, L["hc"], t, fem)
        for sx in (-1, 1):
            ov(c, sx * 29, 2, 6, 9, skin, ow=2.4)
            if L.get("ear") == "hoop":
                c.drawCircle(sx * 30, 18, 7, P("#e8b93a", 2.4))
            elif L.get("ear") == "stud":
                c.drawCircle(sx * 30, 12, 2, P("#e8e8e8"))
        fp = face_path(30, 38 if not fem else 37)
        shp(c, fp, skin)
        shade_clip(c, fp, mixhex(skin, "#3a1a0a", 0.6), a=0.22)
        c.drawCircle(-17, 10, 6, P("#e0705a", a=0.15))
        c.drawCircle(17, 10, 6, P("#e0705a", a=0.15))
        blink = blink_ok and ((t + (hsh(who) % 37) * 0.13) % 3.9) < 0.11
        a_face(c, L, skin, expr, t, look, talk, blink, fem)
        a_hair_front(c, hs, L["hc"], t)


def _arm(c, sx, sy, a1, a2, side, L1, L2, w, col, skin, wraps=False, sleeve=0.55):
    def d(a):
        r = math.radians(a)
        return math.sin(r) * side, math.cos(r)
    dx, dy = d(a1)
    ex, ey = sx + dx * L1, sy + dy * L1
    dx2, dy2 = d(a2)
    hx, hy = ex + dx2 * L2, ey + dy2 * L2
    p = skia.Path()
    p.moveTo(sx, sy)
    p.lineTo(ex, ey)
    p.lineTo(hx, hy)
    c.drawPath(p, P(AO, w + AW * 2))
    c.drawPath(p, P(skin, w))
    if sleeve > 0:
        mx, my = sx + dx * L1 * sleeve, sy + dy * L1 * sleeve
        if sleeve > 1.0:
            mx, my = ex + dx2 * L2 * (sleeve - 1), ey + dy2 * L2 * (sleeve - 1)
            sl = skia.Path()
            sl.moveTo(sx, sy)
            sl.lineTo(ex, ey)
            sl.lineTo(mx, my)
        else:
            sl = skia.Path()
            sl.moveTo(sx, sy)
            sl.lineTo(mx, my)
        c.drawPath(sl, P(col, w + 2))
    ov(c, hx, hy, w * 0.55, w * 0.62, "#ececec" if wraps else skin, ow=2.4)
    return hx, hy


HEAD_Y = -418


def person_adult(c, x, y, who, lk, L, skin, ps, pose, expr, t, s, look, talk, walk, flip, bob, a, prop):
    fem = L.get("fem", False)
    sit = ps.get("sit")
    top, bot = L["top"], L["bottom"]
    sh_w = 40 if fem else 47
    with xf(c, x, y, s=s, alpha=a, sx=-s if flip else None, sy=s if flip else None):
        breathe = math.sin(t * 2.2 + len(who)) * 1.6 if bob else 0
        wk = math.sin(walk * 8.0) if walk else 0
        c.drawOval(skia.Rect(-70, -9, 70, 9), P("#000000", a=0.2))
        if sit:
            c.translate(0, 95)
        # legs
        if sit:
            for sx in (-1, 1):
                rr(c, sx * 20 - 14, -235, 28, 70, 10, bot)
                rr(c, sx * 22 - 13, -175, 26, 150, 10, bot)
                ov(c, sx * 24, -22, 18, 9, L["shoes"], ow=2.4)
        else:
            for sx in (-1, 1):
                sw = wk * 22 * sx
                hip = (sx * 19, -232)
                knee = (sx * 20 + sw * 0.5, -122)
                ank = (sx * 19 + sw, -16)
                p = skia.Path()
                p.moveTo(*hip)
                p.lineTo(*knee)
                p.lineTo(*ank)
                c.drawPath(p, P(AO, 28 + AW * 2))
                c.drawPath(p, P(bot, 28))
                c.drawLine(hip[0] + sx * 6, hip[1] + 20, ank[0] + sx * 6, ank[1] - 10,
                           P(mixhex(bot, "#000000", 0.18), 2))
                shoe = skia.Path()
                shoe.addRRect(skia.RRect.MakeRectXY(skia.Rect(ank[0] - 15 + sx * 3, ank[1] - 6,
                                                              ank[0] + 17 + sx * 3, ank[1] + 12), 7, 7))
                shp(c, shoe, L["shoes"])
        sh_y = -364 + breathe
        L1, L2, aw = 80, 74, 19
        sleeve = 0.0 if L.get("tank") else (1.85 if L.get("long") else 0.5)
        if ps.get("behind"):
            for side in (-1, 1):
                _arm(c, side * (sh_w - 4), sh_y + 8, ps["r"][0], ps["r"][1], side, L1, L2, aw, top, skin,
                     sleeve=sleeve)
        # torso
        p = skia.Path()
        if L.get("dress"):
            p.moveTo(-sh_w + 2, sh_y)
            p.lineTo(sh_w - 2, sh_y)
            p.cubicTo(sh_w - 6, -300, sh_w - 14, -280, sh_w - 4, -250)
            p.lineTo(sh_w + 24, -120)
            p.quadTo(0, -110, -sh_w - 24, -120)
            p.lineTo(-sh_w + 4, -250)
            p.cubicTo(-sh_w + 14, -280, -sh_w + 6, -300, -sh_w + 2, sh_y)
        else:
            waist = 30 if fem else 36
            p.moveTo(-sh_w + 2, sh_y)
            p.lineTo(sh_w - 2, sh_y)
            p.cubicTo(sh_w, -320, waist + 2, -300, waist, -276)
            p.lineTo(waist + 6, -236)
            p.lineTo(-waist - 6, -236)
            p.lineTo(-waist, -276)
            p.cubicTo(-waist - 2, -300, -sh_w, -320, -sh_w + 2, sh_y)
        p.close()
        shp(c, p, top)
        if L.get("hawaii"):
            c.save()
            c.clipPath(p, skia.ClipOp.kIntersect, True)
            for yy in range(-370, -230, 34):
                for xx in range(-60, 70, 34):
                    ox = 17 if (yy // 34) % 2 else 0
                    fx, fy = xx + ox, yy
                    for k in range(5):
                        a_ = k * math.tau / 5
                        c.drawCircle(fx + math.cos(a_) * 5, fy + math.sin(a_) * 5, 4.2, P("#fbe7a8", a=0.9))
                    c.drawCircle(fx, fy, 3, P("#e8735a"))
            c.restore()
            c.drawPath(p, P(AO, AW))
        shade_clip(c, p, "#000000", a=0.12)
        if not L.get("dress") and not L.get("jump"):
            hips = skia.Path()
            hips.addRRect(skia.RRect.MakeRectXY(skia.Rect(-38, -246, 38, -222), 6, 6))
            shp(c, hips, bot)
            c.drawRect(skia.Rect(-38, -248, 38, -240), P(mixhex(bot, "#000000", 0.45)))
            c.drawRect(skia.Rect(-6, -249, 6, -239), P("#c9a24a"))
        if L.get("jump"):
            c.drawLine(0, sh_y + 20, 0, -236, P(mixhex(top, "#000000", 0.3), 2))
            rr(c, 10, -340, 20, 14, 3, mixhex(top, "#ffffff", 0.3), ow=2)
        if L.get("suit"):
            lap = skia.Path()
            lap.moveTo(-12, sh_y)
            lap.lineTo(0, -300)
            lap.lineTo(12, sh_y)
            lap.close()
            shp(c, lap, "#f2f2f2", ow=2)
            tie = skia.Path()
            tie.moveTo(-3, sh_y + 6)
            tie.lineTo(3, sh_y + 6)
            tie.lineTo(5, -290)
            tie.lineTo(0, -282)
            tie.lineTo(-5, -290)
            tie.close()
            shp(c, tie, "#a8282c" if lk != "dealer" else "#e3b13b", ow=1.5)
            c.drawLine(-14, sh_y + 2, -20, -250, P(mixhex(top, "#000000", 0.4), 2))
            c.drawLine(14, sh_y + 2, 20, -250, P(mixhex(top, "#000000", 0.4), 2))
        if L.get("badge"):
            c.drawCircle(-22, -330, 7, P("#e8c25a"))
            c.drawCircle(-22, -330, 7, P(AO, 1.6))
        if L.get("chain"):
            ch = skia.Path()
            ch.moveTo(-16, sh_y)
            ch.quadTo(0, -318, 16, sh_y)
            c.drawPath(ch, P("#e8c25a", 3))
        # neck + collar
        nk = skia.Path()
        nk.addRect(skia.Rect(-9, -386 + breathe, 9, sh_y + 4))
        shp(c, nk, skin, ow=2.4)
        col = skia.Path()
        col.moveTo(-14, sh_y)
        col.quadTo(0, sh_y + (22 if fem else 14), 14, sh_y)
        c.drawPath(col, P(skin))
        c.drawPath(col, P(AO, 2))
        if prop:
            with xf(c, 0, 0, s=0.75):
                c.translate(0, -270)
                prop(c)
        if not ps.get("behind"):
            for side, key in ((1, "r"), (-1, "l")):
                a1, a2 = ps[key]
                if pose == "walk":
                    a1 += wk * 20 * side
                    a2 += wk * 20 * side
                if pose == "wave" and key == "r":
                    a2 += math.sin(t * 10) * 18
                if pose in ("punch", "punchl") and key == ("r" if pose == "punch" else "l"):
                    k = abs(math.sin(t * 5.5))
                    a1 = lerp(30, 92, k)
                    a2 = lerp(200, 92, k)
                _arm(c, side * (sh_w - 4), sh_y + 8, a1, a2, side, L1, L2, aw, top, skin, wraps=L.get("wraps"),
                     sleeve=sleeve)
        with xf(c, 0, HEAD_Y + breathe):
            a_head(c, who, lk, L, skin, expr, t, look, talk, scale=1.08)
