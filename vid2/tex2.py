"""Textures for the Hell Bank Notes short."""
import math
import random
import skia
from engine3d import col, INK
from tex import cached, font, P, text_c, text_fit, rrect
from chars import draw_char

RULER = dict(body=(150, 30, 40), suit=True, tie=(240, 200, 60), hat='emperor', hat_col=(200, 160, 40),
             stache='walrus', stache_col=(40, 30, 30), beard=True, beard_col=(40, 30, 30))


def ornate_border(c, w, h, a, b):
    c.drawRect(skia.Rect(0, 0, w, h), P(a))
    c.drawRect(skia.Rect(14, 14, w - 14, h - 14), P(b, stroke=10))
    for x in range(30, w - 20, 26):
        c.drawCircle(x, 26, 6, P(b))
        c.drawCircle(x, h - 26, 6, P(b))
    for y in range(52, h - 40, 26):
        c.drawCircle(26, y, 6, P(b))
        c.drawCircle(w - 26, y, 6, P(b))


def _note(c, value, look_side=0, tint=0):
    w, h = 1000, 480
    pal = [((236, 214, 160), (176, 60, 40)), ((200, 226, 190), (40, 110, 70)), ((214, 200, 236), (90, 60, 150))][tint % 3]
    ornate_border(c, w, h, pal[0], pal[1])
    # header
    text_c(c, 'HELL BANK NOTE', w / 2, 92, font('black', 56), pal[1])
    text_c(c, '天地銀行', w / 2, 152, font('cjk', 44), (30, 30, 30))
    # portrait oval
    oval = skia.Rect(w / 2 - 120, 170, w / 2 + 120, 440)
    c.save()
    path = skia.Path()
    path.addOval(oval)
    c.clipPath(path, doAntiAlias=True)
    c.drawPaint(P((250, 238, 200)))
    c.translate(w / 2, 590)
    c.scale(3.6, 3.6)
    draw_char(c, RULER, dict(eyes='squint' if look_side == 0 else 'dot', brows='angry', mouth='frown', px=look_side * 2.2))
    c.restore()
    c.drawOval(oval, P(pal[1], stroke=8))
    # values
    f = font('black', 64 if len(value) < 10 else 40)
    text_c(c, value, 200, 300, f, (30, 30, 30))
    text_c(c, value, 800, 300, f, (30, 30, 30))
    text_c(c, 'BANK OF HELL', 210, 380, font('black', 40), pal[1])
    text_c(c, '冥通銀行', 790, 380, font('cjk', 44), pal[1])


_note_cache = {}


def note(value='1,000,000,000', look_side=0, tint=0):
    key = (value, look_side, tint)
    if key not in _note_cache:
        from engine3d import picture
        pic = picture(1000, 480, lambda c: _note(c, value, look_side, tint))
        _note_cache[key] = lambda canvas: canvas.drawPicture(pic)
    return _note_cache[key]


@cached(860, 540)
def gift_card(c):
    rrect(c, 6, 6, 854, 534, 46, (220, 40, 60), INK, 10)
    c.drawRect(skia.Rect(560, 6, 620, 534), P((250, 210, 70)))
    c.drawRect(skia.Rect(6, 300, 854, 360), P((250, 210, 70)))
    text_c(c, 'GIFT CARD', 290, 160, font('black', 92), (255, 255, 255))
    text_c(c, 'To: Grandpa', 290, 250, font('bold', 52), (255, 235, 200))
    text_c(c, '♥', 590, 345, font('black', 90), (220, 40, 60))


@cached(700, 260)
def mailbox_label(c):
    rrect(c, 6, 6, 694, 254, 22, (250, 246, 230), INK, 8)
    text_c(c, 'MAIL TO:', 350, 100, font('black', 64), (30, 30, 40))
    text_c(c, 'NEXT WORLD', 350, 200, font('black', 80), (200, 40, 40))


@cached(1200, 300)
def qingming_banner(c):
    rrect(c, 6, 6, 1194, 294, 30, (190, 30, 36), (250, 200, 70), 12)
    text_c(c, '清明节', 330, 205, font('cjk', 150), (250, 210, 80))
    text_c(c, 'QINGMING', 860, 175, font('black', 84), (255, 240, 210))
    text_c(c, 'FESTIVAL', 860, 255, font('bold', 56), (250, 210, 80))


@cached(500, 800)
def tomb_face(c):
    c.drawRect(skia.Rect(0, 0, 500, 800), P((150, 150, 158)))
    rrect(c, 40, 40, 460, 760, 20, (170, 170, 178), (110, 110, 118), 8)
    for i, ch in enumerate('先祖之墓'):
        text_c(c, ch, 250, 190 + i * 150, font('cjk', 120), (180, 40, 40))


@cached(900, 360)
def shop_sign(c):
    rrect(c, 6, 6, 894, 354, 26, (170, 30, 36), (250, 200, 70), 12)
    text_c(c, '紙紮', 180, 230, font('cjk', 140), (250, 210, 80))
    text_c(c, 'PAPER', 600, 160, font('black', 96), (255, 240, 210))
    text_c(c, 'OFFERINGS', 600, 270, font('black', 84), (255, 240, 210))


@cached(400, 240)
def price_tag(c, txt='¥0.10'):
    tag = skia.Path()
    tag.moveTo(60, 10)
    tag.lineTo(390, 10)
    tag.lineTo(390, 230)
    tag.lineTo(60, 230)
    tag.lineTo(10, 120)
    tag.close()
    c.drawPath(tag, P((255, 236, 140)))
    c.drawPath(tag, P(INK, stroke=8))
    c.drawCircle(48, 120, 12, P(INK, stroke=5))
    text_fit(c, txt, 230, 150, 300, 'black', 90, (30, 30, 40))


@cached(500, 900)
def phone_screen(c, stage=0):
    rrect(c, 0, 0, 500, 900, 60, (20, 20, 26))
    rrect(c, 24, 60, 476, 840, 30, (60, 140, 230) if stage else (240, 240, 245))
    if stage == 0:
        for i in range(9):
            x, y = 70 + (i % 3) * 140, 140 + (i // 3) * 150
            rrect(c, x, y, x + 100, y + 100, 24, [(230, 80, 80), (80, 200, 120), (250, 190, 60)][i % 3])
    else:
        text_c(c, '✓', 250, 420, font('black', 220), (255, 255, 255))
        text_c(c, 'UPGRADE', 250, 560, font('black', 70), (255, 255, 255))
        text_c(c, 'COMPLETE', 250, 640, font('black', 70), (255, 255, 255))


@cached(700, 460)
def year_card(c, year=2024):
    rrect(c, 10, 10, 690, 450, 26, (255, 255, 255), INK, 10)
    c.drawRect(skia.Rect(14, 14, 686, 130), P((200, 40, 40)))
    text_c(c, 'YEAR', 350, 100, font('black', 80), (255, 255, 255))
    text_c(c, str(year), 350, 380, font('black', 210), (30, 30, 40))


@cached(256, 256)
def stone_tiles(c):
    c.drawRect(skia.Rect(0, 0, 256, 256), P((170, 160, 150)))
    for y in range(0, 256, 64):
        for x in range(0, 256, 64):
            rrect(c, x + 3, y + 3, x + 61, y + 61, 6, (184, 174, 162))


@cached(256, 256)
def cloud_floor(c):
    c.drawRect(skia.Rect(0, 0, 256, 256), P((222, 214, 238)))
    rnd = random.Random(3)
    for _ in range(14):
        x, y = rnd.uniform(0, 256), rnd.uniform(0, 256)
        c.drawCircle(x, y, rnd.uniform(18, 40), P((234, 228, 246)))


@cached(256, 256)
def gold_wall(c):
    c.drawRect(skia.Rect(0, 0, 256, 256), P((200, 150, 60)))
    for x in range(0, 256, 64):
        c.drawRect(skia.Rect(x, 0, x + 6, 256), P((240, 200, 100)))
    for x in range(32, 256, 64):
        for y in range(32, 256, 64):
            c.drawCircle(x, y, 10, P((240, 200, 100)))


@cached(256, 256)
def red_wall(c):
    c.drawRect(skia.Rect(0, 0, 256, 256), P((170, 40, 40)))
    for y in range(0, 256, 32):
        c.drawRect(skia.Rect(0, y, 256, y + 3), P((140, 30, 30)))


@cached(256, 256)
def shack_wall(c):
    c.drawRect(skia.Rect(0, 0, 256, 256), P((120, 96, 70)))
    for x in range(0, 256, 42):
        c.drawRect(skia.Rect(x, 0, x + 3, 256), P((80, 60, 40)))
    c.drawRect(skia.Rect(140, 60, 200, 110), P((150, 120, 90)))


@cached(600, 420)
def paper_house_face(c):
    c.drawRect(skia.Rect(0, 0, 600, 420), P((250, 236, 210)))
    c.drawRect(skia.Rect(240, 200, 360, 420), P((190, 40, 40)))
    for x in (60, 420):
        c.drawRect(skia.Rect(x, 150, x + 120, 260), P((120, 180, 230)))
        c.drawRect(skia.Rect(x, 150, x + 120, 260), P((190, 40, 40), stroke=10))
    text_c(c, '福', 300, 130, font('cjk', 100), (200, 40, 40))
    c.drawRect(skia.Rect(0, 0, 600, 420), P((200, 160, 60), stroke=14))
