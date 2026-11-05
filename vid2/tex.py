"""2D textures (drawn once as skia Pictures) that get mapped onto 3D planes."""
import math
import random
import functools
import skia
from engine3d import picture, col, rgb, INK

FONT_DIR = '/usr/share/fonts/'
_tf = {}


def tf(name):
    paths = {
        'black': 'opentype/inter/Inter-ExtraBold.otf',
        'bold': 'opentype/inter/Inter-Bold.otf',
        'semi': 'opentype/inter/Inter-SemiBold.otf',
        'serif': 'truetype/dejavu/DejaVuSerif-Bold.ttf',
        'serifr': 'truetype/dejavu/DejaVuSerif.ttf',
        'mono': 'truetype/jetbrains-mono/JetBrainsMono-Bold.ttf',
        'cjk': 'truetype/wqy/wqy-zenhei.ttc',
    }
    if name not in _tf:
        _tf[name] = skia.Typeface.MakeFromFile(FONT_DIR + paths[name])
    return _tf[name]


def font(name, size):
    f = skia.Font(tf(name), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def P(c, stroke=None):
    p = skia.Paint(AntiAlias=True, Color=col(c) if isinstance(c, tuple) else c)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def text_c(c, s, x, y, f, color, stroke=None, stroke_col=INK):
    w = f.measureText(s)
    if stroke:
        c.drawString(s, x - w / 2, y, f, P(stroke_col, stroke=stroke))
    c.drawString(s, x - w / 2, y, f, P(color))


def text_fit(c, s, x, y, maxw, fname, size, color, stroke=None):
    f = font(fname, size)
    w = f.measureText(s)
    if w > maxw:
        f = font(fname, size * maxw / w)
    text_c(c, s, x, y, f, color, stroke)


def rrect(c, x0, y0, x1, y1, r, fill, stroke=None, sw=4):
    rr = skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), r, r)
    if fill is not None:
        c.drawRRect(rr, P(fill))
    if stroke is not None:
        c.drawRRect(rr, P(stroke, stroke=sw))


def cached(w, h):
    def deco(fn):
        @functools.lru_cache(maxsize=None)
        def make(*args):
            pic = picture(w, h, lambda c: fn(c, *args))
            return lambda canvas: canvas.drawPicture(pic)
        make.w, make.h = w, h
        return make
    return deco


# ---------------------------------------------------------------- Eiffel lattice
IRON = (128, 84, 60)
IRON_D = (88, 56, 42)


@cached(256, 256)
def lattice(c, dense=6, rust=0.0):
    c.drawRect(skia.Rect(0, 0, 256, 256), P((0, 0, 0, 0)))
    edge = P(IRON_D, stroke=14)
    c.drawLine(4, 0, 4, 256, edge)
    c.drawLine(252, 0, 252, 256, edge)
    thin = P(IRON, stroke=5)
    n = dense
    for i in range(n):
        y0, y1 = 256 * i / n, 256 * (i + 1) / n
        c.drawLine(4, y0, 252, y1, thin)
        c.drawLine(252, y0, 4, y1, thin)
        c.drawLine(4, y0, 252, y0, P(IRON_D, stroke=6))
    if rust > 0:
        rnd = random.Random(3)
        for _ in range(int(70 * rust)):
            x, y = rnd.choice([4, 252, rnd.uniform(0, 256)]), rnd.uniform(0, 256)
            c.drawCircle(x, y, rnd.uniform(3, 9), P((205, 105, 45, 200)))


@cached(512, 256)
def arch_face(c, rust=0.0):
    # lattice face with the big decorative arch cut out
    lat = lattice(6, rust)
    c.save()
    path = skia.Path()
    path.addRect(skia.Rect(0, 0, 512, 256))
    arch = skia.Path()
    arch.moveTo(40, 256)
    arch.cubicTo(60, 40, 452, 40, 472, 256)
    arch.close()
    path = skia.Op(path, arch, skia.PathOp.kDifference_PathOp)
    c.clipPath(path, doAntiAlias=True)
    c.save()
    c.scale(2, 1)
    lat(c)
    c.restore()
    c.restore()
    c.drawPath(arch, P(IRON_D, stroke=14))


# ---------------------------------------------------------------- Paris buildings
@cached(512, 640)
def haussmann(c, hue=0, lit=False):
    wall = [(236, 222, 196), (228, 214, 186), (240, 228, 204)][hue % 3]
    c.drawRect(skia.Rect(0, 0, 512, 640), P(wall))
    # mansard roof
    roof = skia.Path()
    roof.moveTo(0, 130)
    roof.lineTo(30, 0)
    roof.lineTo(482, 0)
    roof.lineTo(512, 130)
    roof.close()
    c.drawPath(roof, P((92, 108, 128)))
    for x in range(60, 480, 110):
        rrect(c, x, 40, x + 46, 110, 20, (60, 70, 90))
    c.drawRect(skia.Rect(0, 128, 512, 140), P((200, 186, 160)))
    for row in range(4):
        y = 170 + row * 112
        for x in range(36, 480, 110):
            wc = (255, 214, 120) if lit and (x * 7 + row * 3) % 5 < 2 else (70, 98, 130)
            rrect(c, x, y, x + 52, y + 80, 6, wc)
            c.drawLine(x + 26, y, x + 26, y + 80, P(wall, stroke=3))
            if row in (0, 2):
                c.drawRect(skia.Rect(x - 8, y + 78, x + 60, y + 86), P(INK))
                for k in range(8):
                    c.drawLine(x - 6 + k * 9, y + 70, x - 6 + k * 9, y + 80, P(INK, stroke=2))
    c.drawRect(skia.Rect(0, 600, 512, 640), P((180, 160, 130)))
    c.drawRect(skia.Rect(0, 0, 512, 640), P(INK, stroke=6))


@cached(256, 128)
def cobble(c):
    c.drawRect(skia.Rect(0, 0, 256, 128), P((176, 164, 150)))
    rnd = random.Random(5)
    for y in range(0, 128, 16):
        off = (y // 16) % 2 * 16
        for x in range(-16, 256, 32):
            s = rnd.randint(-10, 10)
            rrect(c, x + off + 2, y + 2, x + off + 30, y + 14, 4, (168 + s, 156 + s, 142 + s))


@cached(256, 256)
def grass(c):
    c.drawRect(skia.Rect(0, 0, 256, 256), P((120, 180, 90)))
    rnd = random.Random(8)
    for _ in range(90):
        x, y = rnd.uniform(0, 256), rnd.uniform(0, 256)
        c.drawLine(x, y, x + rnd.uniform(-3, 3), y - 8, P((96, 156, 70), stroke=3))


# ---------------------------------------------------------------- signs & paper
@cached(600, 360)
def sold_sign(c, again=False):
    rrect(c, 8, 8, 592, 352, 26, (250, 246, 236), INK, 10)
    if not again:
        rrect(c, 40, 40, 560, 320, 18, None, (210, 40, 50), 14)
        text_c(c, 'SOLD!', 300, 230, font('black', 170), (210, 40, 50))
    else:
        text_c(c, 'SOLD', 300, 200, font('black', 150), (210, 40, 50))
        text_c(c, 'AGAIN!', 300, 310, font('black', 96), (30, 30, 40))


@cached(700, 360)
def stamp_again(c):
    c.save()
    c.rotate(-12, 350, 180)
    rrect(c, 30, 70, 670, 300, 22, (255, 250, 235), (210, 40, 50), 16)
    text_c(c, 'SOLD AGAIN!', 350, 225, font('black', 110), (210, 40, 50))
    c.restore()


@cached(420, 260)
def temp_tag(c):
    tag = skia.Path()
    tag.moveTo(70, 10)
    tag.lineTo(410, 10)
    tag.lineTo(410, 250)
    tag.lineTo(70, 250)
    tag.lineTo(10, 130)
    tag.close()
    c.drawPath(tag, P((252, 226, 140)))
    c.drawPath(tag, P(INK, stroke=8))
    c.drawCircle(52, 130, 14, P(INK, stroke=6))
    text_c(c, 'TEMPORARY', 245, 115, font('black', 62), (40, 30, 30))
    text_c(c, 'only 20 years', 245, 190, font('bold', 44), (160, 60, 40))


@cached(520, 720)
def morris_poster(c):
    c.drawRect(skia.Rect(0, 0, 520, 720), P((246, 222, 170)))
    c.drawRect(skia.Rect(20, 20, 500, 700), P((200, 70, 50), stroke=10))
    text_c(c, 'PARIS', 260, 170, font('serif', 120), (40, 40, 70))
    text_c(c, '1925', 260, 420, font('black', 220), (200, 70, 50))
    text_c(c, 'Exposition', 260, 560, font('serifr', 60), (40, 40, 70))


@cached(1000, 1300)
def newspaper(c, kind=0):
    c.drawRect(skia.Rect(0, 0, 1000, 1300), P((240, 234, 218)))
    text_c(c, 'LE MATIN', 500, 140, font('serif', 140), (25, 25, 30))
    c.drawRect(skia.Rect(40, 170, 960, 178), P(INK))
    text_c(c, 'PARIS  ·  1925  ·  15 CENTIMES', 500, 220, font('serifr', 36), (60, 60, 60))
    c.drawRect(skia.Rect(40, 240, 960, 244), P(INK))
    if kind == 0:
        text_fit(c, 'TEAR IT', 500, 400, 900, 'black', 170, (25, 25, 30))
        text_fit(c, 'DOWN?', 500, 570, 900, 'black', 170, (200, 40, 40))
        # tower sketch
        c.save()
        c.translate(260, 640)
        t = skia.Path()
        t.moveTo(0, 560)
        t.quadTo(110, 300, 120, 0)
        t.lineTo(140, 0)
        t.quadTo(150, 300, 260, 560)
        t.close()
        c.drawRect(skia.Rect(-20, -10, 300, 600), P((205, 196, 176)))
        c.drawPath(t, P((70, 60, 55)))
        c.drawLine(40, 300, 220, 300, P((70, 60, 55), stroke=14))
        c.restore()
        for i in range(12):
            y = 680 + i * 46
            c.drawRect(skia.Rect(600, y, 950 - (i % 3) * 40, y + 16), P((150, 146, 136)))
        text_c(c, '"Too rusty, too costly"', 780, 660, font('serifr', 30), (60, 60, 60))
    else:
        heads = ['CAT ELECTED', 'MAYOR', 'WEATHER:', 'MOSTLY FINE', 'MAN FINDS', 'HIS HAT', 'BAKERY OUT', 'OF BREAD']
        a, b = heads[(kind - 1) * 2 % 8], heads[((kind - 1) * 2 + 1) % 8]
        text_fit(c, a, 500, 420, 900, 'black', 150, (25, 25, 30))
        text_fit(c, b, 500, 590, 900, 'black', 150, (25, 25, 30))
        for i in range(14):
            y = 680 + i * 40
            c.drawRect(skia.Rect(60, y, 940 - (i % 4) * 60, y + 14), P((150, 146, 136)))


@cached(700, 900)
def letterhead(c, stamped=True):
    c.drawRect(skia.Rect(0, 0, 700, 900), P((252, 250, 244)))
    c.drawCircle(350, 110, 60, P((40, 60, 120)))
    text_c(c, 'RF', 350, 132, font('serif', 64), (250, 250, 250))
    text_c(c, 'MINISTÈRE DES POSTES', 350, 240, font('serif', 40), (40, 60, 120))
    text_c(c, 'ET TÉLÉGRAPHES', 350, 290, font('serif', 40), (40, 60, 120))
    c.drawRect(skia.Rect(60, 315, 640, 320), P((40, 60, 120)))
    for i in range(9):
        y = 380 + i * 42
        c.drawRect(skia.Rect(70, y, 630 - (i % 3) * 70, y + 12), P((170, 170, 180)))
    if stamped:
        c.save()
        c.rotate(-14, 470, 740)
        c.drawCircle(470, 740, 110, P((200, 40, 50), stroke=12))
        text_c(c, 'OFFICIAL', 470, 760, font('black', 52), (200, 40, 50))
        c.restore()


@cached(1100, 260)
def hotel_sign(c):
    rrect(c, 0, 0, 1100, 260, 30, (30, 40, 70), (210, 175, 90), 14)
    text_fit(c, 'HÔTEL DE CRILLON', 550, 150, 1000, 'serif', 104, (240, 205, 120))
    text_c(c, '★ ★ ★ ★ ★', 550, 222, font('serifr', 46), (240, 205, 120))


@cached(800, 1000)
def easel(c, stage=0):
    """stage 0: tower drawing, 1: red X, 2: 7,000 TONS, 3: HIGHEST BID WINS"""
    c.drawRect(skia.Rect(0, 0, 800, 1000), P((250, 250, 245)))
    if stage <= 1:
        text_c(c, 'TOP SECRET', 400, 110, font('black', 84), (200, 40, 50))
        t = skia.Path()
        t.moveTo(220, 900)
        t.quadTo(370, 520, 385, 180)
        t.lineTo(415, 180)
        t.quadTo(430, 520, 580, 900)
        t.close()
        c.drawPath(t, P((60, 50, 50), stroke=10))
        c.drawLine(280, 620, 520, 620, P((60, 50, 50), stroke=10))
        c.drawLine(330, 420, 470, 420, P((60, 50, 50), stroke=10))
        if stage == 1:
            c.drawLine(140, 220, 660, 920, P((220, 30, 40), stroke=40))
            c.drawLine(660, 220, 140, 920, P((220, 30, 40), stroke=40))
    elif stage == 2:
        text_c(c, '7,000', 400, 380, font('black', 230), (40, 40, 50))
        text_c(c, 'TONS', 400, 560, font('black', 150), (40, 40, 50))
        text_c(c, 'OF IRON', 400, 700, font('black', 110), (160, 90, 50))
        for i in range(5):
            rrect(c, 180 + i * 90, 820 - (i % 2) * 20, 260 + i * 90, 880, 8, (128, 84, 60), INK, 6)
    else:
        text_c(c, 'HIGHEST', 400, 330, font('black', 160), (40, 40, 50))
        text_c(c, 'BID', 400, 520, font('black', 200), (210, 40, 50))
        text_c(c, 'WINS', 400, 710, font('black', 160), (40, 40, 50))
        text_c(c, '₣ ₣ ₣', 400, 870, font('black', 110), (40, 150, 70))


@cached(900, 300)
def name_card(c, name, sub, accent=(210, 40, 50)):
    rrect(c, 10, 10, 890, 290, 30, (255, 255, 255), INK, 10)
    c.drawRect(skia.Rect(10, 10, 60, 290), P(accent))
    text_fit(c, name, 475, 150, 760, 'black', 110, (25, 25, 35))
    text_fit(c, sub, 475, 240, 760, 'bold', 64, accent)


@cached(800, 1000)
def certificate(c):
    c.drawRect(skia.Rect(0, 0, 800, 1000), P((250, 240, 210)))
    c.drawRect(skia.Rect(30, 30, 770, 970), P((170, 130, 60), stroke=14))
    text_c(c, 'CERTIFICATE', 400, 170, font('serif', 80), (90, 60, 30))
    text_c(c, 'OF OWNERSHIP', 400, 250, font('serif', 54), (90, 60, 30))
    t = skia.Path()
    t.moveTo(300, 760)
    t.quadTo(390, 520, 395, 330)
    t.lineTo(405, 330)
    t.quadTo(410, 520, 500, 760)
    t.close()
    c.drawPath(t, P((90, 60, 30)))
    text_c(c, 'OWNER: A. POISSON', 400, 850, font('bold', 52), (60, 40, 20))
    c.drawCircle(640, 860, 60, P((200, 40, 50)))


@cached(700, 500)
def calendar(c, day=0):
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    rrect(c, 10, 10, 690, 490, 24, (255, 255, 255), INK, 10)
    c.drawRect(skia.Rect(14, 14, 686, 150), P((210, 40, 50)))
    text_c(c, days[day % 7], 350, 115, font('black', 96), (255, 255, 255))
    text_c(c, str(12 + day), 350, 400, font('black', 230), (30, 30, 40))


@cached(600, 400)
def police_sign(c):
    rrect(c, 10, 10, 590, 390, 24, (30, 50, 120), (255, 255, 255), 12)
    text_c(c, 'POLICE', 300, 200, font('black', 140), (255, 255, 255))
    text_c(c, 'PRÉFECTURE · PARIS', 300, 300, font('bold', 44), (250, 210, 90))


@cached(800, 500)
def au_revoir(c):
    c.drawRect(skia.Rect(0, 0, 800, 500), P((252, 250, 240)))
    text_c(c, 'Au revoir!', 400, 220, font('serif', 120), (40, 40, 60))
    text_c(c, '— V.L.  ♥', 520, 380, font('serifr', 70), (200, 40, 50))


@cached(400, 300)
def bill(c):
    rrect(c, 4, 4, 396, 296, 14, (150, 200, 140), (60, 110, 60), 8)
    c.drawCircle(200, 150, 80, P((110, 170, 100)))
    text_c(c, '₣', 200, 190, font('black', 120), (40, 90, 40))
    text_c(c, '1000', 80, 70, font('black', 40), (40, 90, 40))


@cached(256, 256)
def wallpaper(c, a=(122, 30, 42), b=(140, 40, 52)):
    c.drawRect(skia.Rect(0, 0, 256, 256), P(a))
    for x in range(0, 256, 64):
        c.drawRect(skia.Rect(x, 0, x + 28, 256), P(b))
    for x in range(14, 256, 64):
        for y in range(16, 256, 64):
            c.drawCircle(x, y, 6, P((200, 160, 90, 90)))


@cached(256, 256)
def planks(c, a=(150, 96, 60)):
    c.drawRect(skia.Rect(0, 0, 256, 256), P(a))
    for i, y in enumerate(range(0, 256, 32)):
        c.drawRect(skia.Rect(0, y, 256, y + 2), P((90, 56, 34)))
        off = (i * 83) % 256
        c.drawRect(skia.Rect(off, y, off + 2, y + 32), P((90, 56, 34)))


@cached(256, 256)
def carpet(c):
    c.drawRect(skia.Rect(0, 0, 256, 256), P((120, 30, 40)))
    c.drawRect(skia.Rect(18, 18, 238, 238), P((210, 170, 90), stroke=8))
    c.drawRect(skia.Rect(40, 40, 216, 216), P((150, 46, 56)))
    c.drawCircle(128, 128, 44, P((210, 170, 90), stroke=6))


@cached(400, 600)
def window_tex(c, night=False, rain=False):
    sky = (40, 50, 100) if night else (160, 205, 240)
    c.drawRect(skia.Rect(0, 0, 400, 600), P(sky))
    if night:
        c.drawCircle(300, 120, 40, P((250, 240, 200)))
    if rain:
        rnd = random.Random(2)
        for _ in range(60):
            x, y = rnd.uniform(0, 400), rnd.uniform(0, 600)
            c.drawLine(x, y, x - 6, y + 24, P((160, 180, 230, 160), stroke=3))
    c.drawRect(skia.Rect(0, 0, 400, 600), P((240, 236, 226), stroke=30))
    c.drawLine(200, 0, 200, 600, P((240, 236, 226), stroke=18))
    c.drawLine(0, 300, 400, 300, P((240, 236, 226), stroke=18))


@cached(512, 256)
def ship_hull(c):
    c.drawRect(skia.Rect(0, 0, 512, 256), P((30, 30, 40)))
    c.drawRect(skia.Rect(0, 190, 512, 256), P((180, 40, 40)))
    c.drawRect(skia.Rect(0, 0, 512, 30), P((240, 240, 240)))
    for x in range(30, 500, 46):
        c.drawCircle(x, 90, 11, P((250, 220, 140)))
    text_c(c, 'S.S. AMERICA', 256, 160, font('black', 40), (240, 240, 240))
