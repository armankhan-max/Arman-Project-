"""Code-made motion graphics: animated maps with location pins, bar charts and timelines.
Scene syntax (editable in the scene editor):
    map: Egypt                      map: Giza, 29.98, 31.13
    bars: Honey=3000, Milk=7, Bread=5 (days)
    timeline: 1922=Tomb opened; 1950=Honey tested; 2026=Still edible
"""
import json
import math
import os
import re
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import store

FPS = 30
_countries = None
_maps = {}


def countries():
    global _countries
    if _countries is None:
        with open(os.path.join(store.BASE, "assets", "countries.json"), encoding="utf-8") as f:
            _countries = json.load(f)
    return _countries


def find_country(name):
    q = name.strip().lower()
    for c in countries():
        if q == (c["n"] or "").lower() or q in (a.lower() for a in c["alt"]):
            return c
    for c in countries():
        if any(q in a.lower() or a.lower() in q for a in c["alt"] if len(a) > 3):
            return c
    return None


def parse(spec):
    """'map: Egypt' -> dict, or None if the text is not a valid graphic."""
    if not spec or ":" not in spec:
        return None
    kind, body = spec.split(":", 1)
    kind, body = kind.strip().lower(), body.strip()
    try:
        if kind == "map":
            parts = [x.strip() for x in body.split(",")]
            g = {"type": "map", "label": parts[0]}
            if len(parts) >= 3:
                g["lat"], g["lon"] = float(parts[1]), float(parts[2])
                c = None
                for cc in countries():  # highlight the country that contains the point, if any
                    if any(_inside(g["lon"], g["lat"], r) for r in cc["r"]):
                        c = cc
                        break
            else:
                c = find_country(parts[0])
                if not c:
                    return None
                g["lat"], g["lon"] = c["lat"], c["lon"]
            g["country"] = c["n"] if c else None
            return g
        if kind == "bars":
            unit = ""
            m = re.search(r"\(([^)]*)\)\s*$", body)
            if m:
                unit, body = m.group(1), body[:m.start()]
            items = []
            for part in body.split(","):
                if "=" in part:
                    k, v = part.rsplit("=", 1)
                    items.append((k.strip(), float(re.sub(r"[^\d.\-]", "", v) or 0)))
            return {"type": "bars", "items": items[:6], "unit": unit} if items else None
        if kind == "timeline":
            ev = []
            for part in body.split(";"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    ev.append((k.strip(), v.strip()))
            return {"type": "timeline", "events": ev[:6]} if ev else None
    except Exception:
        return None
    return None


def _inside(x, y, ring):
    c = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            c = not c
        j = i
    return c


def _font(size, text=""):
    deva = any("ऀ" <= ch <= "ॿ" for ch in text)
    for n in (["FreeSansBold.ttf"] if deva else []) + ["Inter-ExtraBold.otf", "FreeSansBold.ttf"]:
        try:
            return ImageFont.truetype(os.path.join(store.FONTS, n), size)
        except Exception:
            pass
    return ImageFont.load_default()


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _back(t):  # overshoot ease for pops
    t = max(0.0, min(1.0, t))
    s = 1.70158
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def _background(w, h):
    bg = Image.new("RGB", (w, h), (10, 14, 22))
    top = Image.new("RGB", (w, h), (24, 32, 50))
    mask = Image.linear_gradient("L").resize((w, h)).point(lambda v: 255 - v)
    return Image.composite(top, bg, mask)


def _pipe(path, w, h, n, frame_fn):
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", path],
                         stdin=subprocess.PIPE)
    try:
        for i in range(n):
            p.stdin.write(frame_fn(i / FPS).tobytes())
    finally:
        p.stdin.close()
        p.wait()
    if p.returncode != 0:
        raise RuntimeError("graphic encode failed")


# ---------------- map ----------------
MW = 6144  # equirectangular world canvas width (lon -180..180); height covers lat 84..-60
LAT_T, LAT_B = 84.0, -60.0
MH = int(MW * (LAT_T - LAT_B) / 360)


def _xy(lon, lat):
    return (lon + 180) / 360 * MW, (LAT_T - lat) / (LAT_T - LAT_B) * MH


def _world(highlight, accent):
    key = (highlight, accent)
    if key in _maps:
        return _maps[key]
    img = Image.new("RGB", (MW, MH), (9, 22, 38))
    d = ImageDraw.Draw(img)
    for lon in range(-180, 181, 15):  # graticule
        x, _ = _xy(lon, 0)
        d.line([(x, 0), (x, MH)], fill=(17, 34, 54), width=3)
    for lat in range(-60, 85, 15):
        _, y = _xy(0, lat)
        d.line([(0, y), (MW, y)], fill=(17, 34, 54), width=3)
    acc = _rgb(accent)
    for c in countries():
        hl = c["n"] == highlight
        for ring in c["r"]:
            pts = [_xy(x, y) for x, y in ring]
            if len(pts) > 2:
                d.polygon(pts, fill=tuple(int(v * 0.85) for v in acc) if hl else (38, 54, 72), outline=(84, 108, 134))
    _maps.clear()
    _maps[key] = img
    return img


def render_map(g, path, dur, w, h, accent):
    world = _world(g.get("country"), accent)
    tx, ty = _xy(g["lon"], g["lat"])
    n = max(2, round(dur * FPS))
    zoom_t = min(2.6, dur * 0.55)
    start_w, end_w = MW * 0.75, MW * 0.075  # view width in canvas pixels (world -> ~27 degrees)
    cx0, cy0 = MW * 0.5 + (tx - MW * 0.5) * 0.3, MH * 0.48
    f_lab = _font(int(h * 0.055), g["label"])
    acc = _rgb(accent)

    def frame(t):
        e = _ease(t / zoom_t)
        vw = start_w * (end_w / start_w) ** e * (1 - 0.04 * max(0, t - zoom_t) / max(1, dur))  # keep drifting in
        vh = vw * h / w
        cx = cx0 + (tx - cx0) * e
        cy = cy0 + (ty - cy0) * e
        box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
        im = world.transform((w, h), Image.EXTENT, box, Image.BILINEAR)
        d = ImageDraw.Draw(im, "RGBA")
        px, py = (tx - box[0]) / vw * w, (ty - box[1]) / vh * h
        tp = t - zoom_t * 0.8
        if tp > 0:
            s = _back(tp / 0.45)
            for k in range(2):  # pulse rings
                ph = ((tp + k * 0.7) % 1.4) / 1.4
                r = h * 0.02 + h * 0.08 * ph
                d.ellipse([px - r, py - r, px + r, py + r], outline=acc + (int(255 * (1 - ph)),), width=max(2, int(h * 0.004)))
            r = h * 0.018 * s
            d.ellipse([px - r, py - r, px + r, py + r], fill=acc + (255,), outline=(0, 0, 0, 255), width=3)
            # pin label
            la = min(1, max(0, (tp - 0.2) / 0.3))
            if la > 0:
                tw = d.textlength(g["label"], font=f_lab)
                bx = px + h * 0.05
                bx = min(bx, w - tw - h * 0.08)
                by = py - h * 0.09
                d.line([(px, py), (bx, by + h * 0.035)], fill=(255, 255, 255, int(220 * la)), width=3)
                d.rectangle([bx, by, bx + tw + h * 0.04, by + h * 0.075], fill=(10, 10, 14, int(220 * la)))
                d.rectangle([bx, by, bx + h * 0.008, by + h * 0.075], fill=acc + (int(255 * la),))
                d.text((bx + h * 0.025, by + h * 0.008), g["label"], font=f_lab, fill=(255, 255, 255, int(255 * la)))
        return im.convert("RGB")

    _pipe(path, w, h, n, frame)


# ---------------- bars ----------------
def _fmt(v, final):
    if abs(final) >= 100 or float(final).is_integer():
        return f"{v:,.0f}"
    return f"{v:,.1f}"


def render_bars(g, path, dur, w, h, accent, title=""):
    items, unit = g["items"], g.get("unit", "")
    n = max(2, round(dur * FPS))
    base = _background(w, h)
    acc = _rgb(accent)
    vmax = max(v for _, v in items) or 1
    k = len(items)
    land = w > h
    left, right = w * (0.12 if land else 0.1), w * (0.88 if land else 0.9)
    top, bottom = h * 0.24, h * (0.78 if land else 0.72)
    slot = (right - left) / k
    bw = slot * 0.58
    f_val, f_lab = _font(int(h * 0.05)), _font(int(h * 0.036), " ".join(i[0] for i in items))
    f_t = _font(int(h * 0.06), title)

    def frame(t):
        im = base.copy()
        d = ImageDraw.Draw(im, "RGBA")
        if title:
            tw = d.textlength(title, font=f_t)
            d.text(((w - tw) / 2, h * 0.07), title, font=f_t, fill=(255, 255, 255, int(255 * min(1, t / 0.3))))
        d.line([(left - 10, bottom), (right + 10, bottom)], fill=(120, 130, 150), width=3)
        for i, (lab, v) in enumerate(items):
            e = _ease((t - 0.2 - i * 0.18) / 1.1)
            x = left + slot * i + (slot - bw) / 2
            bh = max(h * 0.012, (bottom - top) * (v / vmax)) * e
            col = acc if v == vmax else (200, 208, 222)
            d.rectangle([x, bottom - bh, x + bw, bottom], fill=col + (255,))
            if e > 0:
                val = _fmt(v * e, v)
                tw = d.textlength(val, font=f_val)
                d.text((x + bw / 2 - tw / 2, bottom - bh - h * 0.065), val, font=f_val, fill=(255, 255, 255))
            lw = d.textlength(lab, font=f_lab)
            d.text((x + bw / 2 - lw / 2, bottom + h * 0.02), lab, font=f_lab, fill=(220, 225, 235, int(255 * min(1, max(0, t - i * 0.18) / 0.3))))
        if unit:
            uw = d.textlength(unit, font=f_lab)
            d.text(((w - uw) / 2, h * 0.9), unit.upper(), font=f_lab, fill=(150, 160, 180))
        return im

    _pipe(path, w, h, n, frame)


# ---------------- timeline ----------------
def _wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines[:3]


def render_timeline(g, path, dur, w, h, accent, title=""):
    ev = g["events"]
    n = max(2, round(dur * FPS))
    base = _background(w, h)
    acc = _rgb(accent)
    k = len(ev)
    left, right, y = w * 0.16, w * 0.84, h * 0.52
    step = (right - left) / max(1, k - 1) if k > 1 else 0
    f_year, f_lab = _font(int(h * 0.06)), _font(int(h * 0.032), " ".join(e[1] for e in ev))
    f_t = _font(int(h * 0.06), title)
    per = min(1.0, max(0.5, (dur - 1.2) / max(1, k)))
    draw_t = per * k

    def frame(t):
        im = base.copy()
        d = ImageDraw.Draw(im, "RGBA")
        if title:
            tw = d.textlength(title, font=f_t)
            d.text(((w - tw) / 2, h * 0.08), title, font=f_t, fill=(255, 255, 255, int(255 * min(1, t / 0.3))))
        p = _ease(t / draw_t) if k > 1 else 1
        d.line([(left, y), (left + (right - left) * p, y)], fill=(150, 160, 180), width=5)
        for i, (yr, lab) in enumerate(ev):
            x = left + step * i if k > 1 else w / 2
            ti = t - (i * per if k > 1 else 0)
            if ti <= 0:
                continue
            s = _back(ti / 0.35)
            r = h * 0.018 * s
            last = i == k - 1
            d.ellipse([x - r, y - r, x + r, y + r], fill=(acc if last else (235, 240, 248)) + (255,), outline=(0, 0, 0), width=3)
            a = int(255 * min(1, ti / 0.3))
            yw = d.textlength(yr, font=f_year)
            up = i % 2 == 0
            d.text((x - yw / 2, y - h * (0.13 if up else -0.04)), yr, font=f_year, fill=(acc if last else (255, 255, 255)) + (a,))
            lines = _wrap(d, lab, f_lab, max(step * 0.9, w * 0.14))
            ly = y + h * 0.05 if up else y - h * 0.08 - len(lines) * h * 0.04
            for j, ln in enumerate(lines):
                lw = d.textlength(ln, font=f_lab)
                d.text((min(max(x - lw / 2, w * 0.02), w * 0.98 - lw), ly + j * h * 0.04), ln, font=f_lab, fill=(210, 216, 228, a))
        return im

    _pipe(path, w, h, n, frame)


def render(spec, path, dur, w, h, accent="#FFD400", title=""):
    g = parse(spec) if isinstance(spec, str) else spec
    if not g:
        raise ValueError("not a graphic")
    if g["type"] == "map":
        render_map(g, path, dur, w, h, accent)
    elif g["type"] == "bars":
        render_bars(g, path, dur, w, h, accent, title)
    else:
        render_timeline(g, path, dur, w, h, accent, title)
    return path
