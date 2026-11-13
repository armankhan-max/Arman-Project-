"""Drawing kit on top of Skia: colors, fonts (with complex-script shaping), text layout, shapes, images."""
import math
import os
from collections import OrderedDict

import numpy as np
import skia
from PIL import Image

from . import core
from .core import clamp

_tf = {}
_img = OrderedDict()
_fc = [None]
AA = dict(AntiAlias=True)
LIN = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
CUBIC = skia.SamplingOptions(skia.CubicResampler.Mitchell())
EMBOLDEN = {"PlayfairDisplay", "Montserrat", "Cinzel", "Oswald", "Caveat", "NotoSansDevanagari"}


def C(hx, a=1.0):
    r, g, b = core.hex_rgb(hx)
    return skia.Color(r, g, b, int(clamp(a) * 255))


def typeface(name):
    if name not in _tf:
        tf = None
        for ext in (".ttf", ".otf"):
            p = os.path.join(core.FONTS, name + ext)
            if os.path.exists(p):
                tf = skia.Typeface.MakeFromFile(p)
                break
        _tf[name] = tf or skia.Typeface.MakeDefault() if hasattr(skia.Typeface, "MakeDefault") else tf
        if _tf[name] is None:
            _tf[name] = skia.FontMgr().matchFamilyStyle("DejaVu Sans", skia.FontStyle.Bold())
    return _tf[name]


def font(name, size):
    f = skia.Font(typeface(name), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    if name in EMBOLDEN:
        f.setEmbolden(True)
    return f


def is_complex(s):
    return any(ord(ch) > 0x24F and not (0x2000 <= ord(ch) <= 0x22FF) for ch in s)


def _collection():
    if _fc[0] is None:
        tl = skia.textlayout
        fc = tl.FontCollection()
        prov = tl.TypefaceFontProvider()
        prov.registerTypeface(typeface("NotoSansDevanagari"), "Deva")
        fc.setAssetFontManager(prov)
        fc.setDefaultFontManager(skia.FontMgr())
        _fc[0] = fc
    return _fc[0]


def _para(s, size, color, maxw, align="left"):
    tl = skia.textlayout
    ps = tl.ParagraphStyle()
    ps.setTextAlign({"left": tl.TextAlign.kLeft, "center": tl.TextAlign.kCenter, "right": tl.TextAlign.kRight}[align])
    ts = tl.TextStyle()
    ts.setFontFamilies(["Deva", "Noto Sans", "DejaVu Sans", "FreeSans"])
    ts.setFontSize(size)
    ts.setColor(color)
    ts.setFontStyle(skia.FontStyle.Bold())
    ps.setTextStyle(ts)
    b = tl.ParagraphBuilder.make(ps, _collection(), skia.Unicode())
    b.pushStyle(ts)
    b.addText(s)
    p = b.Build()
    p.layout(maxw)
    return p


def text_w(s, name, size, tracking=0.0):
    if not s:
        return 0.0
    if is_complex(s):
        try:
            return _para(s, size, 0xFFFFFFFF, 100000).LongestLine
        except Exception:
            pass
    return font(name, size).measureText(s) + tracking * max(0, len(s) - 1)


def text(c, s, x, y, size, color, name="Inter-Bold", align="left", a=1.0, tracking=0.0, stroke=None, stroke_w=0.0, shadow=0.0):
    """Baseline text. align: left|center|right. Optional outline and soft shadow."""
    if not s or a <= 0.003:
        return 0.0
    col = C(color, a) if isinstance(color, str) else color
    if is_complex(s):
        try:
            p = _para(s, size, col, 100000)
            w = p.LongestLine
            ox = x - (w / 2 if align == "center" else w if align == "right" else 0)
            if shadow:
                p2 = _para(s, size, C("#000000", a * 0.6), 100000)
                p2.paint(c, ox + shadow, y - size * 0.95 + shadow)
            p.paint(c, ox, y - size * 0.95)
            return w
        except Exception:
            pass
    f = font(name, size)
    w = f.measureText(s) + tracking * max(0, len(s) - 1)
    ox = x - (w / 2 if align == "center" else w if align == "right" else 0)

    def run(paint, dx=0.0, dy=0.0):
        if tracking:
            cx = ox
            for ch in s:
                c.drawString(ch, cx + dx, y + dy, f, paint)
                cx += f.measureText(ch) + tracking
        else:
            c.drawString(s, ox + dx, y + dy, f, paint)
    if shadow:
        run(skia.Paint(Color=C("#000000", a * 0.55), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, shadow), **AA), 0, shadow * 0.6)
    if stroke and stroke_w:
        run(skia.Paint(Color=C(stroke, a), Style=skia.Paint.kStroke_Style, StrokeWidth=stroke_w, StrokeJoin=skia.Paint.kRound_Join, **AA))
    run(skia.Paint(Color=col, **AA))
    return w


def wrap(s, name, size, maxw):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if cur and text_w(t, name, size) > maxw:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def fit_size(s, name, maxw, size, min_size=18):
    while size > min_size and text_w(s, name, size) > maxw:
        size *= 0.94
    return size


def text_block(c, s, x, y, size, color, name, maxw, align="left", a=1.0, lh=1.22, max_lines=6, **kw):
    """Wrapped text; y is the first baseline. Returns the height used."""
    lines = wrap(s, name, size, maxw)[:max_lines]
    for i, ln in enumerate(lines):
        text(c, ln, x, y + i * size * lh, size, color, name, align, a, **kw)
    return len(lines) * size * lh


def rect(c, x, y, w, h, color, a=1.0, r=0.0, stroke=0.0):
    p = skia.Paint(Color=C(color, a) if isinstance(color, str) else color, **AA)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
    if r:
        c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), r, r, p)
    else:
        c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), p)


def line(c, x1, y1, x2, y2, color, w=3.0, a=1.0, dash=None, cap=True):
    p = skia.Paint(Color=C(color, a), StrokeWidth=w, Style=skia.Paint.kStroke_Style, **AA)
    if cap:
        p.setStrokeCap(skia.Paint.kRound_Cap)
    if dash:
        p.setPathEffect(skia.DashPathEffect.Make(list(dash), 0))
    c.drawLine(x1, y1, x2, y2, p)


def circle(c, x, y, r, color, a=1.0, stroke=0.0):
    p = skia.Paint(Color=C(color, a), **AA)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
    c.drawCircle(x, y, max(0.01, r), p)


def arc(c, x, y, r, start, sweep, color, w=8.0, a=1.0):
    p = skia.Paint(Color=C(color, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap, **AA)
    c.drawArc(skia.Rect.MakeLTRB(x - r, y - r, x + r, y + r), start, sweep, False, p)


def poly(c, pts, color, a=1.0, stroke=0.0, close=True):
    path = skia.Path()
    path.moveTo(*pts[0])
    for q in pts[1:]:
        path.lineTo(*q)
    if close:
        path.close()
    p = skia.Paint(Color=C(color, a), **AA)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeJoin(skia.Paint.kRound_Join)
        p.setStrokeCap(skia.Paint.kRound_Cap)
    c.drawPath(path, p)


def arrow(c, x1, y1, x2, y2, color, w=10.0, a=1.0, prog=1.0, curve=0.0):
    """Arrow that draws itself on as prog goes 0→1. curve bends it sideways."""
    prog = clamp(prog)
    if prog <= 0:
        return
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1
    cx, cy = mx - dy / L * curve, my + dx / L * curve
    pts = []
    n = 24
    for i in range(int(n * prog) + 1):
        u = i / n
        pts.append(((1 - u) ** 2 * x1 + 2 * (1 - u) * u * cx + u * u * x2, (1 - u) ** 2 * y1 + 2 * (1 - u) * u * cy + u * u * y2))
    if len(pts) < 2:
        return
    poly(c, pts, color, a, stroke=w, close=False)
    (ax, ay), (bx, by) = pts[-2], pts[-1]
    ang = math.atan2(by - ay, bx - ax)
    hs = w * 2.6
    poly(c, [(bx + math.cos(ang) * hs * 0.6, by + math.sin(ang) * hs * 0.6),
             (bx + math.cos(ang + 2.5) * hs, by + math.sin(ang + 2.5) * hs),
             (bx + math.cos(ang - 2.5) * hs, by + math.sin(ang - 2.5) * hs)], color, a)


def linear(x1, y1, x2, y2, colors, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(x1, y1), skia.Point(x2, y2)], colors, pos)


def radial(x, y, r, colors, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(x, y), r, colors, pos)


def fill(c, shader, x, y, w, h, a=1.0):
    p = skia.Paint(Shader=shader, **AA)
    p.setAlphaf(clamp(a))
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), p)


def glow(c, x, y, r, color, a=0.5):
    fill(c, radial(x, y, r, [C(color, a), C(color, 0)]), x - r, y - r, 2 * r, 2 * r)


# ------------------------------------------------------------------ images
def to_skia(arr):
    """HxWx4 uint8 RGBA numpy → skia.Image (copied)."""
    return skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType, copy=True)


def load_image(path, max_side=2200, cache=10):
    key = (path, max_side)
    if key in _img:
        _img.move_to_end(key)
        return _img[key]
    try:
        with Image.open(path) as im:
            im = im.convert("RGBA")
            if max(im.size) > max_side:
                im.thumbnail((max_side, max_side), Image.LANCZOS)
            img = to_skia(np.asarray(im))
    except Exception:
        img = None
    _img[key] = img
    while len(_img) > cache:
        _img.popitem(last=False)
    return img


def blurred(img, sigma, scale=0.25, key=None):
    """Cheap big blur: downscale, blur, and let the caller upscale."""
    k = ("blur", key or id(img), sigma)
    if k in _img:
        return _img[k]
    w, h = max(8, int(img.width() * scale)), max(8, int(img.height() * scale))
    s = skia.Surface(w, h)
    p = skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma * scale, sigma * scale, skia.TileMode.kClamp))
    cc = s.getCanvas()
    cc.drawImageRect(img, skia.Rect.MakeWH(w, h), LIN, p)
    out = s.makeImageSnapshot()
    _img[k] = out
    return out


def cover(iw, ih, w, h):
    """Source-size scale so an iw×ih image covers w×h."""
    return max(w / float(iw), h / float(ih))


def draw_cover(c, img, x, y, w, h, zoom=1.0, fx=0.5, fy=0.5, a=1.0, paint=None, sampling=None):
    """Draw img filling the rect, zoomed around the focus point (fx, fy in 0..1 of the image)."""
    iw, ih = img.width(), img.height()
    s = cover(iw, ih, w, h) * zoom
    sw, sh = w / s, h / s
    sx = clamp(fx * iw - sw / 2, 0, max(0, iw - sw))
    sy = clamp(fy * ih - sh / 2, 0, max(0, ih - sh))
    p = paint or skia.Paint(**AA)
    if a < 1:
        p.setAlphaf(clamp(a))
    c.drawImageRect(img, skia.Rect.MakeXYWH(sx, sy, sw, sh), skia.Rect.MakeXYWH(x, y, w, h), sampling or CUBIC, p)


def grade_filter(sat=1.0, contrast=1.0, gain=(1, 1, 1), lift=0.0):
    """Color matrix: saturation → per-channel gain → contrast around mid grey → lift."""
    lr, lg, lb = 0.2126, 0.7152, 0.0722
    s = sat
    m = np.array([[lr * (1 - s) + s, lg * (1 - s), lb * (1 - s)],
                  [lr * (1 - s), lg * (1 - s) + s, lb * (1 - s)],
                  [lr * (1 - s), lg * (1 - s), lb * (1 - s) + s]])
    m = (m.T * np.array(gain)).T * contrast
    off = 0.5 * (1 - contrast) + lift
    mat = [m[0][0], m[0][1], m[0][2], 0, off, m[1][0], m[1][1], m[1][2], 0, off, m[2][0], m[2][1], m[2][2], 0, off, 0, 0, 0, 1, 0]
    return skia.ColorFilters.Matrix([float(v) for v in mat])


FILTER_GRADES = {
    "none": None, "cinematic": (0.9, 1.14, (1.04, 1.0, 0.94), -0.01), "bw": (0.0, 1.15, (1, 1, 1), 0.0), "sepia": (0.25, 1.05, (1.12, 1.0, 0.8), 0.02),
    "cold": (0.9, 1.08, (0.92, 1.0, 1.12), 0.0), "warm": (1.08, 1.04, (1.1, 1.0, 0.88), 0.0), "vivid": (1.35, 1.1, (1, 1, 1), 0.0),
    "faded": (0.7, 0.88, (1.0, 1.0, 1.02), 0.05), "noir": (0.0, 1.4, (1, 1, 1), -0.03), "dream": (1.1, 0.92, (1.05, 1.0, 1.08), 0.04),
}
