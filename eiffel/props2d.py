"""Small 2D props held in a character's hand (local char units, hand at 0,0)."""
import math
import skia
from engine3d import INK, col
import tex as T


def _p(c, stroke=None):
    p = skia.Paint(AntiAlias=True, Color=col(c) if isinstance(c, tuple) else c)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
    return p


def suitcase(c, open_=0.0):
    r = skia.RRect.MakeRectXY(skia.Rect(-14, 2, 14, 22), 3, 3)
    c.drawRRect(r, _p((120, 72, 40)))
    c.drawRRect(r, _p(INK, 2.2))
    c.drawLine(-14, 11, 14, 11, _p(INK, 1.4))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-5, -2, 5, 3), 2, 2), _p(INK, 2.2))
    if open_ > 0:
        for i in range(5):
            a = -math.pi / 2 + (i - 2) * 0.45
            d = 10 + 22 * open_
            x, y = math.cos(a) * d, 2 + math.sin(a) * d
            c.save()
            c.translate(x, y)
            c.rotate(i * 37 + open_ * 200)
            c.drawRect(skia.Rect(-6, -4, 6, 4), _p((150, 200, 140)))
            c.drawRect(skia.Rect(-6, -4, 6, 4), _p((60, 110, 60), 1.0))
            c.restore()


def money_bag(c, label='₣'):
    path = skia.Path()
    path.moveTo(-4, -2)
    path.lineTo(4, -2)
    path.cubicTo(18, 6, 16, 26, 0, 26)
    path.cubicTo(-16, 26, -18, 6, -4, -2)
    c.drawPath(path, _p((200, 170, 110)))
    c.drawPath(path, _p(INK, 2.2))
    c.drawLine(-5, 0, 5, 0, _p(INK, 2.5))
    f = T.font('black', 15)
    T.text_c(c, label, 0, 20, f, (40, 110, 50))


def gavel(c, ang=0):
    c.save()
    c.rotate(ang)
    c.drawLine(0, 0, 0, -22, _p((110, 70, 40), 3.5))
    r = skia.RRect.MakeRectXY(skia.Rect(-10, -30, 10, -20), 2, 2)
    c.drawRRect(r, _p((120, 70, 40)))
    c.drawRRect(r, _p(INK, 1.8))
    c.restore()


def watch(c):
    c.drawCircle(0, -6, 7, _p((240, 205, 90)))
    c.drawCircle(0, -6, 7, _p(INK, 1.8))
    c.drawCircle(0, -6, 5, _p((255, 255, 245)))
    c.drawLine(0, -6, 0, -10, _p(INK, 1.2))
    c.drawLine(0, -6, 3, -6, _p(INK, 1.2))


def torch(c, t=0.0):
    c.drawLine(0, 6, 0, -22, _p((110, 70, 40), 3))
    fl = skia.Path()
    w = 1 + 0.15 * math.sin(t * 30)
    fl.moveTo(0, -42 * w)
    fl.cubicTo(8, -30, 7, -22, 0, -21)
    fl.cubicTo(-7, -22, -8, -30, 0, -42 * w)
    c.drawPath(fl, _p((255, 150, 40)))
    c.drawCircle(0, -27, 3.5, _p((255, 230, 120)))


def pitchfork(c):
    c.drawLine(0, 10, 0, -30, _p((110, 70, 40), 3))
    for x in (-5, 0, 5):
        c.drawLine(x, -30, x, -42, _p((90, 90, 100), 2.4))
    c.drawLine(-5, -30, 5, -30, _p((90, 90, 100), 2.4))


def brush(c):
    c.drawLine(0, 0, 6, -12, _p((140, 90, 50), 2.5))
    c.drawRect(skia.Rect(4, -20, 10, -12), _p((200, 120, 60)))


def bucket(c):
    p = skia.Path()
    p.moveTo(-7, 0)
    p.lineTo(7, 0)
    p.lineTo(6, 14)
    p.lineTo(-6, 14)
    p.close()
    c.drawPath(p, _p((150, 150, 160)))
    c.drawPath(p, _p(INK, 1.8))
    c.drawRect(skia.Rect(-7, 0, 7, 3), _p((120, 80, 60)))


def whistle(c):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-2, -6, 10, 0), 2, 2), _p((220, 220, 230)))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-2, -6, 10, 0), 2, 2), _p(INK, 1.4))


def hat(c, col_=(35, 35, 45)):
    c.drawRect(skia.Rect(-9, -16, 9, -4), _p(col_))
    c.drawRect(skia.Rect(-9, -16, 9, -4), _p(INK, 1.8))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-14, -5, 14, -1), 2, 2), _p(col_))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-14, -5, 14, -1), 2, 2), _p(INK, 1.8))


def paper(c, w=16, h=20, color=(250, 248, 240)):
    c.drawRect(skia.Rect(-w / 2, -h, w / 2, 0), _p(color))
    c.drawRect(skia.Rect(-w / 2, -h, w / 2, 0), _p(INK, 1.4))
    for i in range(4):
        c.drawLine(-w / 2 + 3, -h + 5 + i * 4, w / 2 - 3, -h + 5 + i * 4, _p((150, 150, 160), 1.0))


def contract_hook(c):
    c.drawLine(0, -400, 0, -4, _p((60, 60, 60), 0.8))
    hook = skia.Path()
    hook.moveTo(0, -4)
    hook.lineTo(0, 4)
    hook.quadTo(0, 10, -5, 8)
    c.drawPath(hook, _p((120, 120, 130), 1.8))
    paper(c, 14, 16)
