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


_cities = None


def find_city(name):
    global _cities
    if _cities is None:
        with open(os.path.join(store.BASE, "assets", "cities.json"), encoding="utf-8") as f:
            _cities = json.load(f)
    q = name.strip().lower()
    return next((c for c in _cities if c[0].lower() == q), None) or next((c for c in _cities if q in c[0].lower()), None)


TYPES = {
    "map": "map: Egypt (a country) or map: Giza, 29.98, 31.13",
    "city": "city: Paris (a city, zooms in close)",
    "conflict": "conflict: Russia vs Ukraine (two countries facing each other)",
    "bars": "bars: Honey=3000, Milk=7 (days)",
    "compare": "compare: Honey vs Sugar; Lasts=3000 years|2 years; Water=17%|0.1%",
    "timeline": "timeline: 1922=Tomb opened; 2026=Still edible",
    "icons": "icons: Fast; Cheap; Safe (3 to 5 short key points in circles)",
    "card": "card: Cleopatra; Last pharaoh of Egypt; 69 BC to 30 BC (a person profile card)",
    "stat": "stat: 3,000 years; Age of the oldest honey ever found (one big number)",
}


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
        if kind == "city":
            parts = [x.strip() for x in body.split(",")]
            if len(parts) >= 3:
                lat, lon = float(parts[1]), float(parts[2])
            else:
                c = find_city(parts[0])
                if not c:
                    return None
                lat, lon = c[1], c[2]
            cc = next((x for x in countries() if any(_inside(lon, lat, r) for r in x["r"])), None)
            return {"type": "map", "label": parts[0], "lat": lat, "lon": lon, "country": cc["n"] if cc else None, "zoom": "city"}
        if kind == "conflict":
            names = [x.strip() for x in re.split(r"\bvs\.?\b|\bversus\b|,", body) if x.strip()]
            cs = [find_country(n) for n in names[:2]]
            if len(cs) < 2 or not all(cs):
                return None
            return {"type": "conflict", "a": cs[0], "b": cs[1], "la": names[0], "lb": names[1]}
        if kind == "compare":
            parts = [x.strip() for x in body.split(";") if x.strip()]
            heads = [x.strip() for x in re.split(r"\bvs\.?\b|\|", parts[0]) if x.strip()][:2]
            rows = []
            for r_ in parts[1:6]:
                if "=" in r_:
                    k, v = r_.split("=", 1)
                    vals = [x.strip() for x in v.split("|")]
                    rows.append((k.strip(), vals[0], vals[1] if len(vals) > 1 else ""))
            return {"type": "compare", "heads": heads, "rows": rows} if len(heads) == 2 and rows else None
        if kind == "icons":
            items = [x.strip() for x in re.split(r"[;,]", body) if x.strip()][:5]
            return {"type": "icons", "items": items} if items else None
        if kind == "card":
            parts = [x.strip() for x in body.split(";")]
            return {"type": "card", "name": parts[0], "role": parts[1] if len(parts) > 1 else "",
                    "years": parts[2] if len(parts) > 2 else ""} if parts[0] else None
        if kind == "stat":
            parts = [x.strip() for x in body.split(";")]
            return {"type": "stat", "value": parts[0], "label": parts[1] if len(parts) > 1 else ""}
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
    start_w, end_w = MW * 0.75, MW * (0.045 if g.get("zoom") == "city" else 0.075)  # view width in canvas pixels
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
            d.text(((w - uw) / 2, h * (0.15 if title else 0.08)), unit.upper(), font=f_lab, fill=(170, 180, 200))
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


def _world_multi(hl, accent):
    """World canvas with several countries tinted: hl = {name: rgb}."""
    key = ("multi", tuple(sorted(hl.items())))
    if key in _maps:
        return _maps[key]
    img = _world(None, accent).copy()
    d = ImageDraw.Draw(img)
    for c in countries():
        if c["n"] in hl:
            for ring in c["r"]:
                pts = [_xy(x, y) for x, y in ring]
                if len(pts) > 2:
                    d.polygon(pts, fill=hl[c["n"]], outline=(255, 255, 255))
    _maps[key] = img
    return img


def render_conflict(g, path, dur, w, h, accent):
    ca, cb = g["a"], g["b"]
    red, blue = (214, 48, 49), (41, 128, 255)
    world = _world_multi({ca["n"]: red, cb["n"]: blue}, accent)
    ax, ay = _xy(ca["lon"], ca["lat"])
    bx, by = _xy(cb["lon"], cb["lat"])
    mx, my = (ax + bx) / 2, (ay + by) / 2
    span = max(abs(ax - bx) * 2.2, abs(ay - by) * 2.2 * w / h, MW * 0.05)
    n = max(2, round(dur * FPS))
    f_lab = _font(int(h * 0.05))
    zoom_t = min(2.2, dur * 0.5)

    def frame(t):
        e = _ease(t / zoom_t)
        vw = MW * 0.7 * (span / (MW * 0.7)) ** e
        vh = vw * h / w
        cx, cy = MW / 2 + (mx - MW / 2) * e, MH * 0.45 + (my - MH * 0.45) * e
        box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
        im = world.transform((w, h), Image.EXTENT, box, Image.BILINEAR)
        d = ImageDraw.Draw(im, "RGBA")
        P = lambda x, y: ((x - box[0]) / vw * w, (y - box[1]) / vh * h)
        pa, pb = P(ax, ay), P(bx, by)
        ta = t - zoom_t * 0.8
        if ta > 0:
            p = _ease(ta / 0.8)  # arrows grow from each side toward the middle
            for (sx, sy), (ex, ey), col in ((pa, pb, red), (pb, pa, blue)):
                mxp, myp = sx + (ex - sx) * 0.42 * p, sy + (ey - sy) * 0.42 * p
                d.line([(sx, sy), (mxp, myp)], fill=col + (255,), width=max(6, int(h * 0.012)))
                ang = math.atan2(myp - sy, mxp - sx)
                L = h * 0.03
                d.polygon([(mxp + math.cos(ang) * L, myp + math.sin(ang) * L),
                           (mxp + math.cos(ang + 2.5) * L, myp + math.sin(ang + 2.5) * L),
                           (mxp + math.cos(ang - 2.5) * L, myp + math.sin(ang - 2.5) * L)], fill=col + (255,))
            la = int(255 * min(1, ta / 0.4))
            for (x, y), lab, col in ((pa, g["la"], red), (pb, g["lb"], blue)):
                tw = d.textlength(lab.upper(), font=f_lab)
                x0 = min(max(x - tw / 2 - 14, 10), w - tw - 40)
                y0 = y - h * 0.11
                d.rectangle([x0, y0, x0 + tw + 28, y0 + h * 0.07], fill=col + (la,))
                d.text((x0 + 14, y0 + h * 0.008), lab.upper(), font=f_lab, fill=(255, 255, 255, la))
        return im.convert("RGB")

    _pipe(path, w, h, n, frame)


def render_compare(g, path, dur, w, h, accent, title=""):
    base = _background(w, h)
    acc = _rgb(accent)
    n = max(2, round(dur * FPS))
    rows = g["rows"]
    f_h, f_r, f_v = _font(int(h * 0.06)), _font(int(h * 0.036)), _font(int(h * 0.05))
    colx = [w * 0.24, w * 0.55, w * 0.8]
    top = h * 0.2
    rh = min(h * 0.13, h * 0.62 / max(1, len(rows)))

    def frame(t):
        im = base.copy()
        d = ImageDraw.Draw(im, "RGBA")
        a = _ease(t / 0.4)
        for j, (hd, col) in enumerate(zip(g["heads"], (acc, (110, 190, 255)))):
            tw = d.textlength(hd.upper(), font=f_h)
            d.text((colx[j + 1] - tw / 2, top - (1 - a) * 30), hd.upper(), font=f_h, fill=col + (int(255 * a),))
        for i, (lab, va, vb) in enumerate(rows):
            ti = t - 0.4 - i * 0.45
            if ti <= 0:
                continue
            s = _ease(ti / 0.35)
            y = top + h * 0.1 + i * rh
            d.rounded_rectangle([w * 0.08, y, w * 0.92, y + rh * 0.8], radius=rh * 0.2, fill=(26, 36, 56, int(220 * s)))
            d.text((w * 0.11, y + rh * 0.22), lab, font=f_r, fill=(220, 226, 238, int(255 * s)))
            for j, v in enumerate((va, vb)):
                tw = d.textlength(v, font=f_v)
                d.text((colx[j + 1] - tw / 2, y + rh * 0.14), v, font=f_v, fill=(255, 255, 255, int(255 * s)))
        return im

    _pipe(path, w, h, n, frame)


def render_icons(g, path, dur, w, h, accent, title=""):
    base = _background(w, h)
    acc = _rgb(accent)
    n = max(2, round(dur * FPS))
    items = g["items"]
    k = len(items)
    f_l, f_n = _font(int(h * 0.04)), _font(int(h * 0.075))
    f_t = _font(int(h * 0.06), title)
    gap = w * 0.8 / k
    r = min(h * 0.11, gap * 0.36)

    def frame(t):
        im = base.copy()
        d = ImageDraw.Draw(im, "RGBA")
        if title:
            tw = d.textlength(title, font=f_t)
            d.text(((w - tw) / 2, h * 0.14), title, font=f_t, fill=(255, 255, 255, int(255 * min(1, t / 0.3))))
        for i, it in enumerate(items):
            ti = t - 0.2 - i * 0.35
            if ti <= 0:
                continue
            s = _back(ti / 0.4)
            cx, cy = w * 0.1 + gap * (i + 0.5), h * 0.5
            rr = r * s
            d.ellipse([cx - rr * 1.12, cy - rr * 1.12, cx + rr * 1.12, cy + rr * 1.12], outline=acc + (255,), width=max(3, int(h * 0.005)))
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(28, 40, 64))
            num = str(i + 1)
            tw = d.textlength(num, font=f_n)
            if s > 0.6:
                d.text((cx - tw / 2, cy - h * 0.048), num, font=f_n, fill=acc)
                lines = _wrap(d, it, f_l, gap * 0.92)
                for j, ln in enumerate(lines):
                    lw = d.textlength(ln, font=f_l)
                    d.text((cx - lw / 2, cy + r * 1.35 + j * h * 0.05), ln, font=f_l, fill=(235, 240, 248, int(255 * min(1, (s - 0.6) / 0.4))))
        return im

    _pipe(path, w, h, n, frame)


def render_card(g, path, dur, w, h, accent, portrait=None):
    base = _background(w, h)
    acc = _rgb(accent)
    n = max(2, round(dur * FPS))
    f_n, f_r, f_y = _font(int(h * 0.075), g["name"]), _font(int(h * 0.04), g["role"]), _font(int(h * 0.04))
    ph = int(h * 0.5)
    pic = None
    if portrait and os.path.exists(portrait):
        from PIL import ImageOps
        pic = ImageOps.fit(Image.open(portrait).convert("RGB"), (int(ph * 0.8), ph), Image.LANCZOS)

    def frame(t):
        im = base.copy()
        d = ImageDraw.Draw(im, "RGBA")
        s = _ease(t / 0.5)
        cw, chh = w * 0.7, h * 0.62
        x0, y0 = (w - cw) / 2 + (1 - s) * 60, (h - chh) / 2
        d.rounded_rectangle([x0, y0, x0 + cw, y0 + chh], radius=h * 0.03, fill=(22, 30, 48, int(240 * s)))
        d.rounded_rectangle([x0, y0, x0 + h * 0.012, y0 + chh], radius=4, fill=acc + (int(255 * s),))
        tx = x0 + h * 0.06
        if pic is not None:
            im.paste(pic, (int(x0 + h * 0.06), int(y0 + (chh - ph) / 2)))
            d.rectangle([x0 + h * 0.06, y0 + (chh - ph) / 2, x0 + h * 0.06 + pic.width, y0 + (chh - ph) / 2 + ph], outline=acc, width=4)
            tx = x0 + h * 0.06 + pic.width + h * 0.06
        a = int(255 * _ease((t - 0.3) / 0.4))
        d.text((tx, y0 + chh * 0.28), g["name"].upper(), font=f_n, fill=(255, 255, 255, a))
        for j, ln in enumerate(_wrap(d, g["role"], f_r, x0 + cw - tx - h * 0.04)):
            d.text((tx, y0 + chh * 0.46 + j * h * 0.05), ln, font=f_r, fill=(205, 212, 226, a))
        if g["years"]:
            d.rectangle([tx, y0 + chh * 0.72, tx + d.textlength(g["years"], font=f_y) + 30, y0 + chh * 0.72 + h * 0.06], fill=acc + (a,))
            d.text((tx + 15, y0 + chh * 0.72 + h * 0.008), g["years"], font=f_y, fill=(15, 15, 20, a))
        return im

    _pipe(path, w, h, n, frame)


def render_stat(g, path, dur, w, h, accent):
    base = _background(w, h)
    acc = _rgb(accent)
    n = max(2, round(dur * FPS))
    m = re.search(r"\d[\d,]*(?:\.\d+)?", g["value"])
    f_v, f_l = _font(int(h * 0.2)), _font(int(h * 0.045), g["label"])

    def frame(t):
        im = base.copy()
        d = ImageDraw.Draw(im, "RGBA")
        e = 1 - (1 - min(1, t / 1.3)) ** 3
        txt = g["value"]
        if m:
            val = float(m.group(0).replace(",", ""))
            dec = len(m.group(0).split(".")[1]) if "." in m.group(0) else 0
            cur = f"{val * e:,.{dec}f}" if "," in m.group(0) or val >= 10000 else f"{val * e:.{dec}f}"
            txt = txt[:m.start()] + cur + txt[m.end():]
        tw = d.textlength(txt, font=f_v)
        d.text(((w - tw) / 2, h * 0.3), txt, font=f_v, fill=acc)
        bw = w * 0.3 * _ease((t - 0.4) / 0.6)
        d.rectangle([(w - bw) / 2, h * 0.58, (w + bw) / 2, h * 0.595], fill=(255, 255, 255, 200))
        a = int(255 * _ease((t - 0.7) / 0.4))
        for j, ln in enumerate(_wrap(d, g["label"], f_l, w * 0.7)):
            lw = d.textlength(ln, font=f_l)
            d.text(((w - lw) / 2, h * 0.63 + j * h * 0.06), ln, font=f_l, fill=(225, 230, 240, a))
        return im

    _pipe(path, w, h, n, frame)


def render(spec, path, dur, w, h, accent="#FFD400", title="", portrait=None):
    g = parse(spec) if isinstance(spec, str) else spec
    if not g:
        raise ValueError("not a graphic")
    if g["type"] == "map":
        render_map(g, path, dur, w, h, accent)
    elif g["type"] == "conflict":
        render_conflict(g, path, dur, w, h, accent)
    elif g["type"] == "compare":
        render_compare(g, path, dur, w, h, accent, title)
    elif g["type"] == "icons":
        render_icons(g, path, dur, w, h, accent, title)
    elif g["type"] == "card":
        render_card(g, path, dur, w, h, accent, portrait)
    elif g["type"] == "stat":
        render_stat(g, path, dur, w, h, accent)
    elif g["type"] == "bars":
        render_bars(g, path, dur, w, h, accent, title)
    else:
        render_timeline(g, path, dur, w, h, accent, title)
    return path
