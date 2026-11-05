"""2D stick-figure characters (big round head, bean body, line limbs).

Local space: feet at y=0, head top near y=-100. Draw with draw_char(canvas, look, pose).
"""
import math
import skia
from engine3d import INK, col, rgb, clamp

WHITE = skia.Color(250, 250, 248)


def P(**kw):
    return dict(**kw)


def _paint(c, stroke=None, aa=True):
    p = skia.Paint(AntiAlias=aa, Color=c if isinstance(c, int) else col(c))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


LW = 3.0  # outline width in local units


def _line(c, pts, w=2.4, color=INK):
    path = skia.Path()
    path.moveTo(*pts[0])
    if len(pts) == 3:
        path.quadTo(*pts[1], *pts[2])
    else:
        for p in pts[1:]:
            path.lineTo(*p)
    c.drawPath(path, _paint(color, stroke=w))


def limb(c, a, b, bend=0.0, w=2.4, color=INK):
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    _line(c, [a, (mx + nx * bend, my + ny * bend), b], w=w, color=color)


def arm_end(sh, ang, length):
    r = math.radians(ang)
    return (sh[0] + math.sin(r) * length, sh[1] + math.cos(r) * length)


SKIN_HI = (255, 255, 255)
SKIN_LO = (196, 198, 210)
OUT = skia.Color(40, 38, 52)
OLW = 1.1  # soft outline


def _shade(base, _x, k):
    return tuple(max(0, min(255, int(v * k))) for v in base[:3])


def _lin(p0, p1, c0, c1):
    return skia.GradientShader.MakeLinear([p0, p1], [col(c0), col(c1)])


def _sphere(c, x, y, r, base=SKIN_HI, lo=SKIN_LO, outline=True):
    sh = skia.GradientShader.MakeRadial((x - r * 0.35, y - r * 0.4), r * 1.45, [col(base), col(lo)])
    c.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Shader=sh))
    if outline:
        c.drawCircle(x, y, r, _paint(OUT, stroke=OLW))


def _tube(c, a, b, w, c0=SKIN_HI, c1=SKIN_LO, outline=True):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    p = skia.Path()
    p.moveTo(a[0] + nx, a[1] + ny)
    p.lineTo(b[0] + nx, b[1] + ny)
    p.lineTo(b[0] - nx, b[1] - ny)
    p.lineTo(a[0] - nx, a[1] - ny)
    p.close()
    sh = _lin((a[0] - nx, a[1] - ny), (a[0] + nx, a[1] + ny), c0, c1)
    if outline:
        c.drawPath(p, _paint(OUT, stroke=OLW * 2))
        c.drawCircle(a[0], a[1], w / 2 + OLW / 2, _paint(OUT))
        c.drawCircle(b[0], b[1], w / 2 + OLW / 2, _paint(OUT))
    pa = skia.Paint(AntiAlias=True, Shader=sh)
    c.drawPath(p, pa)
    c.drawCircle(a[0], a[1], w / 2, pa)
    c.drawCircle(b[0], b[1], w / 2, pa)


def arm_end(sh, ang, length):
    r = math.radians(ang)
    return (sh[0] + math.sin(r) * length, sh[1] + math.cos(r) * length)


def _arm(c, sh, ang, cloth, alen=24, side=1):
    """sleeve (cloth colour) for the upper part, white forearm, ball hand. returns hand pos."""
    bias = 22 * side  # so (20, -20) hangs naturally at the sides
    if isinstance(ang, tuple):
        ang = (ang[0] + bias, ang[1] + bias)
    else:
        ang = ang + bias
    if isinstance(ang, tuple):
        e = arm_end(sh, ang[0], alen * 0.5)
        h = arm_end(e, ang[1], alen * 0.52)
        _tube(c, sh, e, 8.5, _shade(cloth, 1, 1.12), _shade(cloth, 1, 0.78))
        mid = ((e[0] + h[0]) / 2, (e[1] + h[1]) / 2)
        _tube(c, e, h, 7.0)
        _tube(c, e, mid, 8.0, _shade(cloth, 1, 1.05), _shade(cloth, 1, 0.75), outline=False)
    else:
        e = arm_end(sh, ang, alen * 0.6)
        h = arm_end(sh, ang, alen)
        _tube(c, e, h, 7.0)
        _tube(c, sh, e, 8.5, _shade(cloth, 1, 1.12), _shade(cloth, 1, 0.78))
    _sphere(c, h[0], h[1], 5.6)
    return h


def draw_char(c, look, pose=None):
    """look: dict(body, hat, hair, hair_col, stache, glasses, tie, bowtie, belly, suit, ...)
    pose: dict(eyes, brows, mouth, arms=(l,r), walk, sit, tilt, sq, blush, sweat, red, px, py, hold, hold_l)"""
    pose = pose or {}
    belly = look.get('belly', 1.0)
    sq = max(0.05, pose.get('sq', 1.0))
    c.save()
    c.scale(1 / math.sqrt(sq), sq)
    sit = pose.get('sit', False)
    walk = pose.get('walk', None)
    hop = abs(math.sin(walk * math.pi)) * 2.0 if walk is not None else 0.0
    c.translate(0, -hop)
    cloth = look.get('body', (60, 70, 110))
    pants = look.get('pants')

    hip_y = -33 if not sit else -30
    # ---------- legs: white tubes with ball feet
    if sit:
        legs = [((-6, hip_y), (-10, -4)), ((6, hip_y), (10, -4))]
    else:
        if walk is not None:
            s_ = math.sin(walk * math.pi * 2)
            fl, fr = (-5 + s_ * 6, -4 - max(0, s_) * 3), (5 - s_ * 6, -4 - max(0, -s_) * 3)
        else:
            sp = pose.get('spread', 0)
            fl, fr = (-6.2 - sp, -4), (6.2 + sp, -4)
        legs = [((-6, hip_y), fl), ((6, hip_y), fr)]
    for (a, b) in legs:
        if pants:
            _tube(c, a, b, 11.0, _shade(pants, 1, 1.1), _shade(pants, 1, 0.75))
        else:
            _tube(c, a, b, 10.5)
    for (a, b) in legs:
        x, y = b
        r = skia.Rect(x - 7.0, y - 4.2, x + 7.0, y + 4.6)
        sh = skia.GradientShader.MakeRadial((x - 1.5, y - 1.5), 8, [col(look.get('shoe_hi', SKIN_HI)), col(look.get('shoe_lo', SKIN_LO))])
        c.drawOval(r, skia.Paint(AntiAlias=True, Shader=sh))
        c.drawOval(r, _paint(OUT, stroke=OLW))

    # ---------- torso (hoodie / jacket) with soft shading
    bw = 13.5 * belly
    top, bot = -58, hip_y + 3
    body = skia.Path()
    body.moveTo(-bw + 3, top)
    body.lineTo(bw - 3, top)
    body.quadTo(bw + 1, top + 1, bw + 0.5, top + 8)
    body.lineTo(bw * (1.02 if belly > 1 else 0.96), bot - 3)
    body.quadTo(bw * 0.95, bot + 0.5, bw * 0.7, bot)
    body.lineTo(-bw * 0.7, bot)
    body.quadTo(-bw * 0.95, bot + 0.5, -bw * (1.02 if belly > 1 else 0.96), bot - 3)
    body.lineTo(-bw - 0.5, top + 8)
    body.quadTo(-bw - 1, top + 1, -bw + 3, top)
    body.close()
    # arms behind? draw shoulder-down arms after torso so they read in front
    c.drawPath(body, _paint(OUT, stroke=OLW * 2))
    c.drawPath(body, skia.Paint(AntiAlias=True, Shader=_lin((-bw, top), (bw, bot), _shade(cloth, 1, 1.15), _shade(cloth, 1, 0.72))))
    c.save()
    c.clipPath(body, doAntiAlias=True)
    dark = skia.Color(0, 0, 0, 55)
    if look.get('suit'):
        shirt = look.get('shirt', (245, 245, 240))
        tri = skia.Path()
        tri.moveTo(-5.5, top)
        tri.lineTo(5.5, top)
        tri.lineTo(0, top + 13)
        tri.close()
        c.drawPath(tri, _paint(shirt))
        _line(c, [(-5.5, top), (0, top + 14)], w=1.2, color=dark)
        _line(c, [(5.5, top), (0, top + 14)], w=1.2, color=dark)
        _line(c, [(0, top + 14), (0, bot)], w=0.9, color=dark)
        for yy in (top + 18, top + 23):
            c.drawCircle(0, yy, 0.9, _paint((30, 30, 30, 160)))
    else:
        # hoodie: drawstrings + kangaroo pocket
        for x in (-3, 3):
            _line(c, [(x, top + 2), (x, top + 9)], w=1.4, color=skia.Color(255, 255, 255, 230))
        pk = skia.Rect(-bw * 0.45, bot - 10, bw * 0.45, bot - 4)
        c.drawRRect(skia.RRect.MakeRectXY(pk, 1.5, 1.5), _paint(_shade(cloth, 1, 0.78)))
        c.drawRRect(skia.RRect.MakeRectXY(pk, 1.5, 1.5), _paint(dark, stroke=0.8))
    if look.get('belt'):
        c.drawRect(skia.Rect(-bw - 2, bot - 6, bw + 2, bot - 3), _paint(look['belt']))
    if look.get('stripes'):
        for yy in range(int(top) + 4, int(bot), 6):
            c.drawRect(skia.Rect(-bw - 2, yy, bw + 2, yy + 2.5), _paint(look['stripes']))
    if look.get('badge'):
        star = skia.Path()
        for i in range(10):
            rr = 3.0 if i % 2 == 0 else 1.3
            a = -math.pi / 2 + i * math.pi / 5
            (star.moveTo if i == 0 else star.lineTo)(6 + rr * math.cos(a), top + 12 + rr * math.sin(a))
        star.close()
        c.drawPath(star, _paint((245, 200, 60)))
    c.restore()
    if look.get('tie'):
        tie = skia.Path()
        tie.moveTo(-1.6, top + 1)
        tie.lineTo(1.6, top + 1)
        tie.lineTo(2.4, top + 13)
        tie.lineTo(0, top + 16)
        tie.lineTo(-2.4, top + 13)
        tie.close()
        c.drawPath(tie, _paint(look['tie']))
        c.drawPath(tie, _paint(OUT, stroke=0.8))
    if look.get('bowtie'):
        bt = skia.Path()
        bt.moveTo(0, top + 2)
        bt.lineTo(-5, top - 1)
        bt.lineTo(-5, top + 5)
        bt.close()
        bt.moveTo(0, top + 2)
        bt.lineTo(5, top - 1)
        bt.lineTo(5, top + 5)
        bt.close()
        c.drawPath(bt, _paint(look['bowtie']))
        c.drawPath(bt, _paint(OUT, stroke=0.8))

    # ---------- arms
    arms = pose.get('arms', (20, -20))
    sh_l, sh_r = (-bw + 2.5, top + 5), (bw - 2.5, top + 5)
    hands = [_arm(c, sh_l, arms[0], cloth, side=-1), _arm(c, sh_r, arms[1], cloth, side=1)]
    if pose.get('hold'):
        c.save()
        c.translate(*hands[1])
        pose['hold'](c)
        c.restore()
    if pose.get('hold_l'):
        c.save()
        c.translate(*hands[0])
        pose['hold_l'](c)
        c.restore()

    # ---------- neck + head
    _tube(c, (0, top + 1), (0, top - 6), 5.5)
    tilt = pose.get('tilt', 0) + pose.get('nod', 0)
    hx, hy, R = 0, -79, 20
    c.save()
    c.translate(hx, hy)
    c.rotate(tilt)
    hair = look.get('hair')
    hc = look.get('hair_col', (70, 45, 30))
    if hair == 'curly':
        for i in range(9):
            a = math.pi + i * math.pi / 8
            _sphere(c, R * 0.95 * math.cos(a), R * 0.82 * math.sin(a) - 2, 6.3, _shade(hc, 1, 1.25), _shade(hc, 1, 0.8))
    _sphere(c, 0, 0, R, look.get('skin', SKIN_HI), SKIN_LO)
    if pose.get('blush'):
        for s in (-1, 1):
            c.drawOval(skia.Rect(s * 12 - 4, 4, s * 12 + 4, 8), _paint((255, 120, 130, int(150 * pose['blush']))))
    if pose.get('red'):
        c.drawCircle(0, 0, R, _paint((235, 60, 60, int(150 * pose['red']))))
    if hair == 'bun':
        _sphere(c, 0, -R * 1.05, 7.5, _shade(hc, 1, 1.4), _shade(hc, 1, 0.8))
    if hair in ('side', 'slick', 'bowl', 'bun'):
        hp = skia.Path()
        hp.moveTo(-R - 0.5, 1)
        hp.cubicTo(-R - 1, -R * 1.3, R + 1, -R * 1.3, R + 0.5, 1)
        hp.cubicTo(R - 3, -6, 4, -10, 0, -9)
        hp.cubicTo(-4, -10, -R + 3, -6, -R - 0.5, 1)
        hp.close()
        c.drawPath(hp, skia.Paint(AntiAlias=True, Shader=_lin((-R, -R), (R, 0), _shade(hc, 1, 1.3), _shade(hc, 1, 0.8))))
        c.drawPath(hp, _paint(OUT, stroke=OLW))
        _line(c, [(0, -9), (0, -R + 1)], w=2.2, color=skia.Color(255, 255, 255, 200))
    if hair == 'combover':
        for k in range(3):
            _line(c, [(-12, -12 - k * 2.5), (0, -18 - k * 1.5), (12, -13 - k * 2)], w=1.4, color=col(hc))
        for s in (-1, 1):
            c.drawOval(skia.Rect(s * R - 4, -6, s * R + 4, 6), _paint(hc))

    _face(c, look, pose, R)
    if look.get('beard'):
        bp = skia.Path()
        bp.moveTo(-6, 13)
        bp.quadTo(0, 30, 6, 13)
        bp.close()
        c.drawPath(bp, _paint(look.get('beard_col', (245, 245, 245))))
        c.drawPath(bp, _paint(OUT, stroke=0.8))

    hat = look.get('hat')
    hatc = look.get('hat_col', (35, 35, 45))
    hpaint = skia.Paint(AntiAlias=True, Shader=_lin((-R, -R * 1.4), (R, -R * 0.5), _shade(hatc, 1, 1.35), _shade(hatc, 1, 0.8)))
    ol = _paint(OUT, stroke=OLW)
    if hat == 'fedora':
        crown = skia.Path()
        crown.moveTo(-R * 0.78, -R * 0.55)
        crown.lineTo(-R * 0.7, -R * 1.25)
        crown.quadTo(0, -R * 1.05, R * 0.7, -R * 1.25)
        crown.lineTo(R * 0.78, -R * 0.55)
        crown.close()
        c.drawPath(crown, hpaint)
        c.drawPath(crown, ol)
        c.drawRect(skia.Rect(-R * 0.78, -R * 0.75, R * 0.78, -R * 0.6), _paint(look.get('band', (150, 30, 40))))
        brim = skia.RRect.MakeRectXY(skia.Rect(-R - 7, -R * 0.62, R + 7, -R * 0.62 + 5), 2.5, 2.5)
        c.drawRRect(brim, hpaint)
        c.drawRRect(brim, ol)
    elif hat == 'cap':
        cap = skia.Path()
        cap.addArc(skia.Rect(-R * 0.98, -R * 1.1, R * 0.98, R * 0.5), 180, 180)
        c.drawPath(cap, hpaint)
        c.drawPath(cap, ol)
        vz = skia.RRect.MakeRectXY(skia.Rect(-R - 2, -R * 0.35, R * 0.4, -R * 0.2), 2, 2)
        c.drawRRect(vz, hpaint)
        c.drawRRect(vz, ol)
    elif hat == 'kepi':
        k = skia.Path()
        k.moveTo(-R * 0.8, -R * 0.5)
        k.lineTo(-R * 0.68, -R * 1.25)
        k.lineTo(R * 0.68, -R * 1.25)
        k.lineTo(R * 0.8, -R * 0.5)
        k.close()
        c.drawPath(k, hpaint)
        c.drawRect(skia.Rect(-R * 0.8, -R * 0.72, R * 0.8, -R * 0.6), _paint((230, 40, 50)))
        c.drawPath(k, ol)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-R * 0.85, -R * 0.55, R * 0.85, -R * 0.4), 3, 3), _paint((30, 30, 40)))
        c.drawCircle(0, -R * 0.95, 2.6, _paint((245, 200, 60)))
    elif hat == 'tophat':
        r1 = skia.Rect(-R * 0.6, -R * 1.7, R * 0.6, -R * 0.6)
        c.drawRect(r1, hpaint)
        c.drawRect(skia.Rect(-R * 0.6, -R * 0.85, R * 0.6, -R * 0.68), _paint((150, 30, 40)))
        c.drawRect(r1, ol)
        brim = skia.RRect.MakeRectXY(skia.Rect(-R - 3, -R * 0.68, R + 3, -R * 0.52), 2, 2)
        c.drawRRect(brim, hpaint)
        c.drawRRect(brim, ol)
    elif hat == 'emperor':
        c.drawRect(skia.Rect(-R * 0.55, -R * 1.25, R * 0.55, -R * 0.75), hpaint)
        c.drawRect(skia.Rect(-R * 0.55, -R * 1.25, R * 0.55, -R * 0.75), ol)
        board = skia.Rect(-R * 1.15, -R * 1.42, R * 1.15, -R * 1.25)
        c.drawRect(board, _paint((30, 30, 36)))
        for k in range(-4, 5):
            x = k * R * 0.26
            for j in range(3):
                c.drawCircle(x, -R * 1.2 + j * 4, 1.4, _paint((230, 60, 50) if j % 2 else (250, 210, 80)))
    elif hat == 'beret':
        b = skia.Path()
        b.addOval(skia.Rect(-R * 0.95, -R * 1.15, R * 1.05, -R * 0.5))
        c.drawPath(b, hpaint)
        c.drawPath(b, ol)
        _line(c, [(2, -R * 1.12), (4, -R * 1.3)], w=2.2)
    c.restore()

    if pose.get('sweat'):
        sp = skia.Path()
        sx, sy = R * 0.85, hy - R * 0.5
        sp.moveTo(sx, sy - 5)
        sp.quadTo(sx + 4, sy + 1, sx, sy + 3)
        sp.quadTo(sx - 4, sy + 1, sx, sy - 5)
        c.drawPath(sp, _paint((120, 200, 255)))
        c.drawPath(sp, _paint(OUT, stroke=1.0))
    c.restore()


def _face(c, look, pose, R):
    eyes = pose.get('eyes', 'dot')
    px, py = pose.get('px', 0), pose.get('py', 0)
    ex, ey = 7.5, -3
    glasses = look.get('glasses')
    for s in (-1, 1):
        x = s * ex
        if eyes == 'dot':
            c.drawOval(skia.Rect(x - 2.1 + px, ey - 3 + py, x + 2.1 + px, ey + 3 + py), _paint(INK))
        elif eyes == 'wide':
            c.drawCircle(x, ey, 5.6, _paint(WHITE))
            c.drawCircle(x, ey, 5.6, _paint(INK, stroke=1.6))
            c.drawCircle(x + px, ey + py, 2.0, _paint(INK))
        elif eyes == 'half':  # smug / half-lidded
            c.drawOval(skia.Rect(x - 2.3 + px, ey - 1.5, x + 2.3 + px, ey + 2.8), _paint(INK))
            _line(c, [(x - 4.5, ey - 1.6), (x + 4.5, ey - 1.6)], w=1.9)
        elif eyes == 'closed':  # happy arcs
            _line(c, [(x - 4, ey + 1), (x, ey - 3.5), (x + 4, ey + 1)], w=2.0)
        elif eyes == 'shut':
            _line(c, [(x - 4, ey), (x + 4, ey)], w=2.0)
        elif eyes == 'squint':
            _line(c, [(x - 4, ey - 1 + s * 0.0), (x + 4, ey + 0.5)], w=2.2)
        elif eyes == 'money':
            f = skia.Font(None, 11)
            f.setEmbolden(True)
            c.drawString('$', x - 3.3, ey + 4, f, _paint((40, 160, 70)))
        elif eyes == 'wink':
            if s < 0:
                _line(c, [(x - 4, ey + 1), (x, ey - 3.5), (x + 4, ey + 1)], w=2.0)
            else:
                c.drawOval(skia.Rect(x - 2.1 + px, ey - 3 + py, x + 2.1 + px, ey + 3 + py), _paint(INK))
        elif eyes == 'roll':
            c.drawCircle(x, ey, 5.0, _paint(WHITE))
            c.drawCircle(x, ey, 5.0, _paint(INK, stroke=1.4))
            c.drawCircle(x + 1.5, ey - 2.8, 1.8, _paint(INK))
        elif eyes == 'stars':
            c.drawCircle(x, ey, 3, _paint((250, 200, 40)))
    br = pose.get('brows')
    for s in (-1, 1):
        x = s * ex
        if br == 'up':
            _line(c, [(x - 4, ey - 8), (x, ey - 10), (x + 4, ey - 8)], w=1.8)
        elif br == 'angry':
            if s < 0:
                _line(c, [(x - 4, ey - 10), (x + 4, ey - 6.5)], w=2.2)
            else:
                _line(c, [(x - 4, ey - 6.5), (x + 4, ey - 10)], w=2.2)
        elif br == 'worried':
            if s < 0:
                _line(c, [(x - 4, ey - 7), (x + 4, ey - 10.5)], w=1.8)
            else:
                _line(c, [(x - 4, ey - 10.5), (x + 4, ey - 7)], w=1.8)
        elif br == 'flat':
            _line(c, [(x - 4, ey - 8), (x + 4, ey - 8)], w=1.8)
        elif br == 'one' and s == 1:
            _line(c, [(x - 4, ey - 9), (x, ey - 12), (x + 4, ey - 10)], w=1.9)
        elif br == 'one' and s == -1:
            _line(c, [(x - 4, ey - 7), (x + 4, ey - 7)], w=1.9)
        elif br == 'sly':
            _line(c, [(x - 4, ey - 7 - (s < 0) * 2), (x + 4, ey - 7 - (s > 0) * 2)], w=1.9)
    if look.get('shades') or pose.get('shades'):
        for s in (-1, 1):
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(s * ex - 6, ey - 4, s * ex + 6, ey + 4), 3, 3), _paint(INK))
        _line(c, [(-ex + 6, ey - 2), (ex - 6, ey - 2)], w=1.6)
    if glasses:
        for s in (-1, 1):
            c.drawCircle(s * ex, ey, 6, _paint(INK, stroke=1.6))
        _line(c, [(-ex + 6, ey), (ex - 6, ey)], w=1.4)
    stache = look.get('stache')
    my = 10 if stache else 8
    vis = pose.get('viseme')
    if vis:
        _viseme(c, vis, pose.get('open', 0.0), look.get('stache'))
        m = None
    else:
        m = pose.get('mouth', 'smile')
    if m == 'smile':
        _line(c, [(-5, my - 1), (0, my + 3), (5, my - 1)], w=1.9)
    elif m == 'flat':
        _line(c, [(-4, my + 1), (4, my + 1)], w=1.9)
    elif m == 'frown':
        _line(c, [(-5, my + 3), (0, my - 1), (5, my + 3)], w=1.9)
    elif m == 'smirk':
        _line(c, [(-5, my + 1), (2, my + 1.5), (6, my - 2)], w=1.9)
    elif m in ('open', 'o', 'grin', 'teeth', 'shout'):
        if m == 'o':
            r = skia.Rect(-3, my - 2, 3, my + 5)
            c.drawOval(r, _paint(INK))
        elif m == 'open':
            p = skia.Path()
            p.moveTo(-6, my - 1)
            p.quadTo(0, my + 9, 6, my - 1)
            p.close()
            c.drawPath(p, _paint(INK))
            c.drawOval(skia.Rect(-3, my + 2, 3, my + 5), _paint((230, 90, 100)))
        elif m == 'shout':
            c.drawOval(skia.Rect(-5, my - 3, 5, my + 8), _paint(INK))
        else:  # grin / teeth: rounded rect with tooth grid
            r = skia.Rect(-7, my - 2.5, 7, my + 5)
            c.drawRRect(skia.RRect.MakeRectXY(r, 2.5, 2.5), _paint(WHITE))
            for xx in (-3.5, 0, 3.5):
                _line(c, [(xx, my - 2.5), (xx, my + 5)], w=0.9)
            _line(c, [(-7, my + 1.2), (7, my + 1.2)], w=0.9)
            c.drawRRect(skia.RRect.MakeRectXY(r, 2.5, 2.5), _paint(INK, stroke=1.6))
    if stache == 'curl':
        p = skia.Path()
        p.moveTo(0, my - 3.5)
        p.cubicTo(-4, my - 6, -9, my - 4, -11, my - 7)
        p.cubicTo(-9, my - 1, -3, my - 2, 0, my - 2)
        p.cubicTo(3, my - 2, 9, my - 1, 11, my - 7)
        p.cubicTo(9, my - 4, 4, my - 6, 0, my - 3.5)
        c.drawPath(p, _paint(look.get('stache_col', INK)))
    elif stache == 'thin':
        _line(c, [(-7, my - 3), (0, my - 4.5), (7, my - 3)], w=2.2, color=col(look.get('stache_col', (30, 25, 25))))
    elif stache == 'walrus':
        p = skia.Path()
        p.addRRect(skia.RRect.MakeRectXY(skia.Rect(-8, my - 6, 8, my - 1), 3, 3))
        c.drawPath(p, _paint(look.get('stache_col', (90, 60, 40))))


def _viseme(c, v, op, stache):
    """mouth shape for lip sync (face-local units)."""
    my = 10 if stache else 8
    ink = skia.Color(30, 24, 30)
    inside = skia.Color(70, 20, 30)
    if v in ('rest', 'MBP'):
        w = 4.5 if v == 'rest' else 5.0
        _line(c, [(-w, my + 1), (w, my + 1)], w=2.3 if v == 'MBP' else 1.9)
        return
    if v == 'FV':
        c.drawRect(skia.Rect(-4.5, my - 0.5, 4.5, my + 2.2), _paint((250, 250, 248)))
        _line(c, [(-5, my + 2.4), (0, my + 3.4), (5, my + 2.4)], w=1.8)
        return
    if v == 'AA':
        w, h = 6.5, 2.5 + 7.5 * op
    elif v == 'EE':
        w, h = 7.5, 1.5 + 3.5 * op
    elif v == 'OO':
        w, h = 3.6 + 0.8 * op, 3.0 + 4.0 * op
    elif v == 'L':
        w, h = 5.5, 2.0 + 4.5 * op
    else:  # S: teeth together
        w, h = 6.0, 2.2 + 1.5 * op
    r = skia.Rect(-w, my - h * 0.35, w, my + h * 0.65)
    c.drawOval(r, _paint(inside))
    c.save()
    pth = skia.Path()
    pth.addOval(r)
    c.clipPath(pth, doAntiAlias=True)
    if v in ('AA', 'EE', 'S', 'L'):
        c.drawRect(skia.Rect(-w, r.top(), w, r.top() + min(2.2, h * 0.35)), _paint((250, 250, 248)))
    if v == 'S':
        c.drawRect(skia.Rect(-w, r.bottom() - min(2.0, h * 0.35), w, r.bottom()), _paint((250, 250, 248)))
    if v in ('AA', 'L'):
        c.drawOval(skia.Rect(-w * 0.6, r.bottom() - h * 0.45 - (h * 0.25 if v == 'L' else 0), w * 0.6,
                             r.bottom() + h * 0.2), _paint((225, 95, 110)))
    c.restore()
    c.drawOval(r, _paint(ink, stroke=1.5))
