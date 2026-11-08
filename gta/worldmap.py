"""Top-down city map (original coastal city with a bay and a barrier island), GPS routes, pins, blips.

World coordinates: MW x MH. A view is (cx, cy, zoom): world point (cx, cy) is drawn at screen center.
Streets sit on a 120-unit grid (offset 60), so routes built from grid points always follow roads.
"""
import math
import random

import skia

from gfx import W, H, C, P, xf, rrect, poly, line, linear, radial, fill_shader, clamp, lerp, smooth, ease_out, \
    back_out, at, mixhex
import sgfx
from ggfx import glow, blurp, ftext, tw, PINK, HOT, GOLD, TEAL, CYAN, GREEN, RED, PURPLE, ORANGE
from vice import draw_line_anim

MW, MH = 3000, 2000
G = 120  # street grid
WATER = "#1b5a8c"
WATER2 = "#2a6ea3"
LAND = "#2b303c"
BLOCK = "#383f4e"
ROAD = "#545e74"
AVE = "#7a86a3"
HWY = "#e0ab45"
PARK = "#2f6a42"
SAND = "#dcc28a"


def gx(i):
    return 60 + i * G


def mainland():
    p = skia.Path()
    p.moveTo(-10, -10)
    p.lineTo(1990, -10)
    p.cubicTo(2010, 400, 1940, 700, 1990, 1000)
    p.cubicTo(2030, 1300, 1950, 1650, 2010, MH + 10)
    p.lineTo(-10, MH + 10)
    p.close()
    return p


def island():
    p = skia.Path()
    p.moveTo(2330, 80)
    p.cubicTo(2420, 500, 2400, 1200, 2470, 1940)
    p.lineTo(2620, 1940)
    p.cubicTo(2560, 1200, 2570, 500, 2470, 80)
    p.close()
    return p


def _draw_map(c):
    c.clear(C(WATER))
    # water texture
    rnd = random.Random(4)
    for _ in range(300):
        x, y = rnd.uniform(0, MW), rnd.uniform(0, MH)
        line(c, x, y, x + rnd.uniform(20, 60), y, WATER2, 3, 0.8)
    ml = mainland()
    c.drawPath(ml, P(SAND, 22))
    c.drawPath(ml, P(LAND))
    isl = island()
    c.drawPath(isl, P(SAND, 30))
    c.drawPath(isl, P(LAND))
    c.save()
    c.clipPath(isl, skia.ClipOp.kIntersect, True)
    for j in range(0, 40):
        c.drawRect(skia.Rect(2300, 60 + j * 50, 2700, 60 + j * 50 + 34), P(BLOCK))
    c.restore()
    # small bay islands
    for (x, y, r) in ((2150, 520, 60), (2180, 1180, 80), (2120, 1600, 45)):
        c.drawCircle(x, y, r + 10, P(SAND))
        c.drawCircle(x, y, r, P(PARK))
        c.drawCircle(x - r * 0.3, y - r * 0.2, r * 0.35, P(BLOCK))
    # blocks + parks inside mainland
    c.save()
    c.clipPath(ml, skia.ClipOp.kIntersect, True)
    for i in range(0, 17):
        for j in range(0, 17):
            x0, y0 = gx(i) + 12, gx(j) + 12
            col = BLOCK
            if rnd.random() < 0.08:
                col = PARK
            c.drawRect(skia.Rect(x0, y0, x0 + G - 24, y0 + G - 24), P(col))
            if col == BLOCK and rnd.random() < 0.7:
                for _ in range(2):
                    bx, by = x0 + rnd.uniform(6, 60), y0 + rnd.uniform(6, 60)
                    c.drawRect(skia.Rect(bx, by, bx + rnd.uniform(16, 34), by + rnd.uniform(16, 34)),
                               P(mixhex(BLOCK, "#ffffff", 0.07)))
    # river / canal
    rv = skia.Path()
    rv.moveTo(-20, 1260)
    rv.cubicTo(500, 1180, 900, 1420, 1300, 1330)
    rv.cubicTo(1600, 1260, 1800, 1300, 2000, 1260)
    c.drawPath(rv, P(WATER, 46))
    # streets
    for i in range(0, 18):
        w = 16 if i % 4 else 26
        col = ROAD if i % 4 else AVE
        line(c, gx(i), -20, gx(i), MH + 20, col, w)
        line(c, -20, gx(i), MW, gx(i), col, w)
    c.restore()
    # island strip road (the beach boulevard)
    c.save()
    c.clipPath(isl, skia.ClipOp.kIntersect, True)
    for j in range(0, 17):
        line(c, 2300, gx(j), 2700, gx(j), ROAD, 12)
    bl = skia.Path()
    bl.moveTo(2420, 60)
    bl.cubicTo(2490, 600, 2470, 1300, 2540, 1960)
    c.drawPath(bl, P(AVE, 20))
    c.restore()
    # causeways
    for y in (gx(4), gx(9), gx(14)):
        line(c, 1960, y, 2460, y, HWY, 18)
    # highway ring
    hw = skia.Path()
    hw.moveTo(-20, gx(2))
    hw.lineTo(gx(14), gx(2))
    hw.quadTo(gx(15) + 60, gx(2), gx(15) + 60, gx(4))
    hw.lineTo(gx(15) + 60, MH + 20)
    c.drawPath(hw, P("#000000", 30, 0.4))
    c.drawPath(hw, P(HWY, 20))
    hw2 = skia.Path()
    hw2.moveTo(-20, gx(12))
    hw2.lineTo(gx(15) + 60, gx(12))
    c.drawPath(hw2, P(HWY, 20))
    # beach umbrellas dots on the island beach
    for k in range(40):
        y = 120 + k * 45
        x = 2560 + 40 * math.sin(k)
        c.drawCircle(x, y, 6, P(rnd.choice((PINK, GOLD, TEAL)), a=0.9))


def map_image():
    key = ("worldmap",)
    if key not in sgfx._cache:
        s = skia.Surface(MW, MH)
        _draw_map(s.getCanvas())
        sgfx._cache[key] = s.makeImageSnapshot()
    return sgfx._cache[key]


class View:
    def __init__(self, cx, cy, zoom, rot=0.0):
        self.cx, self.cy, self.zoom, self.rot = cx, cy, zoom, rot

    def apply(self, c):
        c.translate(W / 2, H / 2)
        if self.rot:
            c.rotate(self.rot)
        c.scale(self.zoom, self.zoom)
        c.translate(-self.cx, -self.cy)

    def to_screen(self, x, y):
        dx, dy = (x - self.cx) * self.zoom, (y - self.cy) * self.zoom
        r = math.radians(self.rot)
        return W / 2 + dx * math.cos(r) - dy * math.sin(r), H / 2 + dx * math.sin(r) + dy * math.cos(r)


def lerp_view(v1, v2, k):
    k = smooth(k)
    return View(lerp(v1[0], v2[0], k), lerp(v1[1], v2[1], k), v1[2] * (v2[2] / v1[2]) ** k,
                lerp(v1[3] if len(v1) > 3 else 0, v2[3] if len(v2) > 3 else 0, k))


def draw_map(c, view, tilt=0.0, dim=0.0):
    c.drawRect(skia.Rect(0, 0, W, H), P(WATER))
    c.save()
    view.apply(c)
    c.drawImage(map_image(), 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
    c.restore()
    if dim:
        c.drawRect(skia.Rect(0, 0, W, H), P("#000000", a=dim))


def route_pts(cells):
    """Grid cells (i, j) → world points on street intersections."""
    return [(gx(i), gx(j)) for i, j in cells]


def route(c, view, cells, k, color=GOLD, w=10, t=0.0, car_icon=True, pts=None):
    pts = pts or route_pts(cells)
    sp = [view.to_screen(*p) for p in pts]
    head = draw_line_anim(c, sp, k, color, w, glow_on=True, dash=True, t=t)
    if car_icon and k > 0:
        # car arrow at the head of the route
        if len(sp) > 1:
            c.drawCircle(head[0], head[1], 20, P("#000000", a=0.5))
            c.drawCircle(head[0], head[1], 15, P("#ffffff"))
            c.drawCircle(head[0], head[1], 9, P(color))
    return head


def pin(c, x, y, color=HOT, icon="bag", s=1.0, a=1.0, t=0.0, pulse=True):
    """Map marker (screen coords), tip at (x, y)."""
    with xf(c, x, y, s, alpha=a):
        if pulse:
            ph = (t * 1.2) % 1.0
            c.drawOval(skia.Rect(-40 - 60 * ph, -12 - 18 * ph, 40 + 60 * ph, 12 + 18 * ph), P(color, 4, 0.8 * (1 - ph)))
        c.drawOval(skia.Rect(-26, -8, 26, 8), P("#000000", a=0.4))
        pth = skia.Path()
        pth.moveTo(0, 0)
        pth.cubicTo(-30, -40, -46, -60, -46, -86)
        pth.cubicTo(-46, -112, -24, -132, 0, -132)
        pth.cubicTo(24, -132, 46, -112, 46, -86)
        pth.cubicTo(46, -60, 30, -40, 0, 0)
        c.drawPath(pth, P("#000000", 8, 0.6))
        c.drawPath(pth, P(color))
        c.drawCircle(0, -88, 30, P("#ffffff"))
        with xf(c, 0, -88, 0.9):
            if icon == "bag":
                rrect(c, -16, -10, 32, 28, 4, color)
                pth2 = skia.Path()
                pth2.addArc(skia.Rect(-9, -22, 9, -2), 180, 180)
                c.drawPath(pth2, P(color, 4))
            elif icon == "home":
                c.drawPath(poly([(-20, 0), (0, -20), (20, 0)]), P(color))
                rrect(c, -14, -2, 28, 20, 2, color)
            elif icon == "pad":
                rrect(c, -20, -10, 40, 22, 10, color)
            elif icon == "q":
                ftext(c, "?", 0, 14, 40, color)
            elif icon == "star":
                pts = []
                for i in range(10):
                    r = 20 if i % 2 == 0 else 9
                    a = -math.pi / 2 + i * math.pi / 5
                    pts.append((math.cos(a) * r, math.sin(a) * r))
                c.drawPath(poly(pts), P(color))


def blip(c, x, y, color=CYAN, r=10, a=1.0):
    c.drawCircle(x, y, r + 3, P("#000000", a=0.5 * a))
    c.drawCircle(x, y, r, P(color, a=a))


def map_hud_frame(c, t, title=None):
    """Thin game-map frame with compass and scale bar."""
    c.drawRect(skia.Rect(0, 0, W, H), P("#000000", 22, 0.6))
    with xf(c, W - 110, 120):
        c.drawCircle(0, 0, 52, P("#000000", a=0.6))
        c.drawCircle(0, 0, 52, P("#ffffff", 3, 0.7))
        c.drawPath(poly([(0, -40), (12, 0), (0, -8), (-12, 0)]), P(RED))
        c.drawPath(poly([(0, 40), (12, 0), (0, 8), (-12, 0)]), P("#ffffff"))
    line(c, 80, H - 70, 280, H - 70, "#ffffff", 5, 0.8)
    line(c, 80, H - 82, 80, H - 58, "#ffffff", 5, 0.8)
    line(c, 280, H - 82, 280, H - 58, "#ffffff", 5, 0.8)
    if title:
        ftext(c, title, 80, 120, 54, "#ffffff", stroke="#000000", sw=8, align="left")
