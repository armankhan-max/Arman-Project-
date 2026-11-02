"""Animated 2D documentary graphics: dark satellite-style maps with red markers (ref style),
seismograph, g-force bars, magnitude comparison, soil/liquefaction cross-section, building sway,
clock, counters, world map arcs, quote card, report document, four-reasons board, timeline."""
import json
import math
import os
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "assets", "fonts")
W, H = 1920, 1080
RED = (214, 40, 40)
WHITE = (238, 233, 222)
GREY = (150, 150, 145)
BLUE = (70, 140, 210)
BG = (12, 13, 15)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


@lru_cache(maxsize=64)
def F(name, size, var=None):
    path = {"oswald": "Oswald.ttf", "playfair": "Playfair.ttf", "type": "SpecialElite.ttf", "courier": "CourierPrimeBold.ttf"}[name]
    f = ImageFont.truetype(os.path.join(FONTS, path), size)
    if var:
        try:
            f.set_variation_by_name(var)
        except Exception:
            pass
    return f


def ctext(d, xy, text, fnt, fill, anchor="mm"):
    d.text(xy, text, font=fnt, fill=fill, anchor=anchor)


def fbm(h, w, seed, octaves=6, base=4, persistence=0.55):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = base * 2 ** o
        small = rng.random((max(2, int(n * h / w)) + 1, n + 1)).astype(np.float32)
        out += cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC) * amp
        tot += amp
        amp *= persistence
    return out / tot


@lru_cache(maxsize=1)
def bg_texture():
    n = fbm(H, W, 21, 6, 3)
    base = np.array(BG, np.float32)[None, None] * (0.7 + 0.6 * n[..., None])
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
    base *= np.clip(1.25 - r * 1.2, 0.4, 1.2)[..., None]
    # faint grid
    g = ((xx % 80 == 0) | (yy % 80 == 0)).astype(np.float32) * 6
    base += g[..., None]
    return np.clip(base, 0, 255).astype(np.uint8)


def canvas():
    return Image.fromarray(bg_texture().copy())


def to_np(im):
    return np.asarray(im.convert("RGB"))


# ================================================================== geography
GEO = json.load(open(os.path.join(HERE, "assets", "geo", "nz.json")))
LAT0 = -43.0
COS0 = math.cos(math.radians(LAT0))
PLACES = {
    "chch": (172.636, -43.532), "darfield": (172.11, -43.49), "sept": (172.18, -43.55), "feb": (172.68, -43.583),
    "lyttelton": (172.72, -43.603), "sumner": (172.765, -43.568), "wellington": (174.78, -41.29),
    "auckland": (174.76, -36.85), "ctv": (172.6425, -43.5279), "pgc": (172.6335, -43.5285),
    "cathedral": (172.637, -43.531),
}
ALPS = [(-40.9, 172.6), (-41.8, 172.3), (-42.5, 171.9), (-43.0, 171.4), (-43.5, 170.6), (-44.0, 169.9), (-44.6, 168.6),
        (-45.3, 167.6)]
NI_RANGES = [(-39.3, 175.6), (-40.0, 176.0), (-40.6, 175.6), (-41.2, 175.2), (-38.4, 177.0), (-37.9, 177.6)]
AVON = [(172.565, -43.525), (172.59, -43.527), (172.615, -43.530), (172.632, -43.528), (172.645, -43.527),
        (172.66, -43.521), (172.68, -43.514), (172.70, -43.517), (172.712, -43.527), (172.725, -43.538)]
PORT_HILLS = [(172.55, -43.585), (172.6, -43.592), (172.65, -43.592), (172.70, -43.588), (172.74, -43.583),
              (172.79, -43.575)]
HIDDEN_FAULT = [(172.60, -43.578), (172.64, -43.581), (172.68, -43.585), (172.72, -43.592)]
GREENDALE = [(171.98, -43.585), (172.08, -43.565), (172.18, -43.552), (172.30, -43.548)]


class Base:
    def __init__(self, lon0, lon1, lat0, lat1, K, detail):
        self.lon0, self.lon1, self.lat0, self.lat1, self.K = lon0, lon1, lat0, lat1, K
        self.w = int((lon1 - lon0) * COS0 * K)
        self.h = int((lat0 - lat1) * K)
        self.detail = detail
        self.img = self.build()

    def xy(self, lon, lat):
        return ((lon - self.lon0) * COS0 * self.K, (self.lat0 - lat) * self.K)

    def build(self):
        w, h = self.w, self.h
        ss = 1
        mask = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(mask)

        def polys(geom):
            if geom["type"] == "Polygon":
                yield geom["coordinates"]
            elif geom["type"] == "MultiPolygon":
                yield from geom["coordinates"]

        for f in GEO["land"]:
            for poly in polys(f["geom"]):
                d.polygon([self.xy(x, y) for x, y in poly[0]], fill=255)
                for hole in poly[1:]:
                    d.polygon([self.xy(x, y) for x, y in hole], fill=0)
        for f in GEO["lakes"]:
            for poly in polys(f["geom"]):
                d.polygon([self.xy(x, y) for x, y in poly[0]], fill=0)
        if self.detail:  # Avon-Heathcote estuary
            ex, ey = self.xy(172.735, -43.548)
            d.ellipse([ex - 0.012 * COS0 * self.K, ey - 0.008 * self.K, ex + 0.01 * COS0 * self.K, ey + 0.008 * self.K], fill=0)
        land = np.asarray(mask).astype(np.float32) / 255
        land = cv2.GaussianBlur(land, (0, 0), 1.0)
        # height field
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        lon = self.lon0 + xx / (COS0 * self.K)
        lat = self.lat0 - yy / self.K
        hgt = np.zeros((h, w), np.float32)
        for chain, amp, width in ((ALPS, 1.0, 0.55), (NI_RANGES, 0.6, 0.35)):
            dmin = np.full((h, w), 9.0, np.float32)
            for (a, b) in zip(chain, chain[1:]):
                ax, ay = a[1] * COS0, a[0]
                bx, by = b[1] * COS0, b[0]
                px, py = lon * COS0, lat
                vx, vy = bx - ax, by - ay
                tt = np.clip(((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy), 0, 1)
                dd = np.hypot(px - (ax + tt * vx), py - (ay + tt * vy))
                dmin = np.minimum(dmin, dd)
            hgt += amp * np.exp(-(dmin / width) ** 2)
        hgt = np.maximum(0, hgt - 0.12) * 1.15  # flat Canterbury plains
        bp = np.hypot((lon - 172.85) * COS0, lat + 43.74)
        hgt += 0.3 * np.exp(-(bp / 0.2) ** 2)
        # Port Hills ridge (north rim of the Lyttelton volcano)
        dmin = np.full((h, w), 9.0, np.float32)
        for (a, b) in zip(PORT_HILLS, PORT_HILLS[1:]):
            ax, ay, bx, by = a[0] * COS0, a[1], b[0] * COS0, b[1]
            px, py = lon * COS0, lat
            vx, vy = bx - ax, by - ay
            tt = np.clip(((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy), 0, 1)
            dmin = np.minimum(dmin, np.hypot(px - (ax + tt * vx), py - (ay + tt * vy)))
        south = np.clip((-43.578 - lat) / 0.02, 0, 1).astype(np.float32)
        hgt += 0.35 * np.exp(-(dmin / (0.012 + 0.03 * south)) ** 2)
        n1 = fbm(h, w, 3, 8, max(4, w // 400))
        n2 = fbm(h, w, 7, 6, max(8, w // 120))
        hgt = hgt * (0.6 + 0.8 * n1) + 0.03 * n2 * np.clip(hgt * 4, 0, 1)
        hgt *= land
        # hillshade
        gx = cv2.Sobel(hgt, cv2.CV_32F, 1, 0, ksize=3) * (120.0 if self.detail else 60.0)
        gy = cv2.Sobel(hgt, cv2.CV_32F, 0, 1, ksize=3) * (120.0 if self.detail else 60.0)
        nx, ny, nz = -gx, -gy, np.ones_like(gx)
        nl = np.sqrt(nx * nx + ny * ny + nz * nz)
        lx, ly, lz = -0.6, -0.6, 0.55
        ll = math.sqrt(lx * lx + ly * ly + lz * lz)
        shade = np.clip((nx * lx + ny * ly + nz * lz) / (nl * ll), 0, 1)
        # land colours: patchwork plains, brown hills, grey rock, snow
        fields = fbm(h, w, 11, 3, max(30, w // 40))
        fq = np.floor(fields * 7) / 7
        low = np.stack([0.30 + 0.12 * fq, 0.34 + 0.1 * fq, 0.22 + 0.04 * fq], -1)
        hill = np.array([0.36, 0.33, 0.26], np.float32)
        rock = np.array([0.42, 0.41, 0.4], np.float32)
        snow = np.array([0.88, 0.89, 0.92], np.float32)
        k1 = np.clip((hgt - 0.15) / 0.2, 0, 1)[..., None]
        k2 = np.clip((hgt - 0.6) / 0.25, 0, 1)[..., None]
        k3 = np.clip((hgt - 0.95) / 0.15, 0, 1)[..., None]
        col = low * (1 - k1) + hill * k1
        col = col * (1 - k2) + rock * k2
        col = col * (1 - k3) + snow * k3
        col = col * (0.35 + 0.85 * shade[..., None])
        # sea: dark, slightly lighter near coast
        dist = cv2.distanceTransform((land < 0.5).astype(np.uint8), cv2.DIST_L2, 5)
        shelf = np.exp(-dist / (60 if not self.detail else 200))[..., None]
        sea = np.array([0.04, 0.07, 0.1], np.float32) + shelf * np.array([0.05, 0.08, 0.09], np.float32)
        sea = sea + 0.015 * n2[..., None]
        img = sea * (1 - land[..., None]) + col * land[..., None]
        if self.detail:
            img = self.city(img, lon, lat, land)
        # rivers
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        for f in GEO["rivers"]:
            g = f["geom"]
            lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
            for ln in lines:
                d.line([self.xy(x, y) for x, y in ln], fill=(40, 60, 72), width=max(1, int(self.K / 900)))
        if self.detail:
            d.line([self.xy(x, y) for x, y in AVON], fill=(35, 55, 66), width=max(2, int(self.K / 900)))
        arr = np.asarray(im).astype(np.float32) / 255
        # ref-style satellite grade: desaturated, dark
        lum = arr.mean(-1, keepdims=True)
        arr = lum + (arr - lum) * 0.55
        arr = arr * 0.85
        return (np.clip(arr, 0, 1) * 255).astype(np.uint8)

    def city(self, img, lon, lat, land):
        cx, cy = PLACES["chch"]
        r = np.hypot((lon - cx - 0.01) * COS0 / 0.085, (lat - cy + 0.004) / 0.06)
        n = fbm(self.h, self.w, 33, 5, 40)
        m = np.clip((1.0 - r + (n - 0.5) * 0.8) * 2.5, 0, 1) * np.clip((lat + 43.586) / 0.012, 0, 1) * 0.85
        m *= land
        hy, hx = np.mgrid[0:self.h, 0:self.w]
        step = max(4, int(self.K * 0.0016))
        grid = (((hx % step) == 0) | ((hy % step) == 0)).astype(np.float32)
        tex = 0.36 + 0.1 * fbm(self.h, self.w, 44, 4, 300) - 0.035 * grid
        urban = np.stack([tex, tex * 0.98, tex * 0.95], -1)
        # Hagley Park
        park = np.hypot((lon - 172.62) * COS0 / 0.008, (lat + 43.531) / 0.009) < 1
        urban[park] = (0.22, 0.3, 0.18)
        return img * (1 - m[..., None]) + urban * m[..., None]


@lru_cache(maxsize=1)
def base_nz():
    return Base(165.5, 179.0, -33.8, -47.6, 330, False)


@lru_cache(maxsize=1)
def base_cant():
    return Base(171.3, 173.25, -43.15, -43.95, 3600, True)


def map_view(lon, lat, span):
    """span = degrees of longitude visible across the frame."""
    b = base_cant() if span < 1.7 else base_nz()
    s_px = W / (span * COS0 * b.K)  # output px per base px
    cx, cy = b.xy(lon, lat)
    M = np.float32([[s_px, 0, W / 2 - s_px * cx], [0, s_px, H / 2 - s_px * cy]])
    img = cv2.warpAffine(b.img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(10, 18, 26))
    if 1.5 < span < 1.9:  # crossfade between bases
        b2 = base_nz() if b is base_cant() else base_cant()
        s2 = W / (span * COS0 * b2.K)
        cx2, cy2 = b2.xy(lon, lat)
        M2 = np.float32([[s2, 0, W / 2 - s2 * cx2], [0, s2, H / 2 - s2 * cy2]])
        img2 = cv2.warpAffine(b2.img, M2, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                              borderValue=(10, 18, 26))
        k = (span - 1.5) / 0.4
        if b is base_cant():
            img = cv2.addWeighted(img, 1 - k, img2, k, 0)
        else:
            img = cv2.addWeighted(img2, 1 - k, img, k, 0)

    def proj(lo, la):
        return (W / 2 + (lo - lon) * COS0 / (span * COS0) * W, H / 2 + (lat - la) / (span * COS0) * W)
    return img, proj


MAPSEQ = {
    "nz_to_chch": dict(cam=[(0, 173.2, -41.3, 13.0), (0.15, 173.2, -41.3, 12.0), (0.75, 172.64, -43.53, 1.0), (1, 172.64, -43.53, 0.75)],
                       labels=[("NEW ZEALAND", 174.8, -39.0, 0.0, 0.4), ("SOUTH ISLAND", 170.6, -44.2, 0.1, 0.5)],
                       markers=[("CHRISTCHURCH", "chch", 0.45)]),
    "darfield": dict(cam=[(0, 172.38, -43.52, 0.95), (1, 172.38, -43.53, 0.8)],
                     markers=[("CHRISTCHURCH", "chch", 0.0), ("DARFIELD", "darfield", 0.15)],
                     lines=[("darfield", "chch", "40 KM", 0.3)], rings=[("sept", 0.82)],
                     paths=[("GREENDALE FAULT", GREENDALE, 0.85, False)]),
    "aftershocks": dict(cam=[(0, 172.4, -43.55, 1.0), (1, 172.42, -43.55, 0.9)], markers=[("CHRISTCHURCH", "chch", 0.0)],
                        dots=("sept", 0.05, 0.95), months=True),
    "aftershocks2": dict(cam=[(0, 172.66, -43.56, 0.45), (1, 172.66, -43.56, 0.4)], markers=[("CHRISTCHURCH", "chch", 0.0)],
                         dots=("feb", 0.0, 1.0), label_top="AFTERSHOCKS"),
    "porthills": dict(cam=[(0, 172.64, -43.55, 0.5), (1, 172.68, -43.575, 0.38)], markers=[("CHRISTCHURCH", "chch", 0.0),
                                                                                        ("LYTTELTON", "lyttelton", 0.5)],
                      paths=[("PORT HILLS", PORT_HILLS, 0.15, False)]),
    "hidden_fault": dict(cam=[(0, 172.66, -43.565, 0.42), (1, 172.66, -43.575, 0.3)],
                         markers=[("CHRISTCHURCH", "chch", 0.0)], paths=[("UNMAPPED FAULT", HIDDEN_FAULT, 0.2, True)]),
    "feb_epicentre": dict(cam=[(0, 172.66, -43.56, 0.32), (1, 172.66, -43.565, 0.28)], markers=[("CITY CENTRE", "chch", 0.0)],
                          rings=[("feb", 0.15)], epis=[("EPICENTRE · 12:51 PM", "feb", 0.15)], lines=[("feb", "chch", "10 KM", 0.35)]),
    "feb_distance": dict(cam=[(0, 172.6, -43.55, 0.5), (1, 172.42, -43.55, 0.95)], markers=[("CHRISTCHURCH", "chch", 0.0)],
                         epis=[("SEPT 2010", "sept", 0.25), ("FEB 2011", "feb", 0.0)],
                         lines=[("feb", "chch", "10 KM", 0.05), ("sept", "chch", "40 KM", 0.4)]),
    "two_buildings": dict(cam=[(0, 172.638, -43.53, 0.08), (1, 172.638, -43.53, 0.06)],
                          markers=[("PGC BUILDING", "pgc", 0.05), ("CTV BUILDING", "ctv", 0.35)]),
    "east": dict(cam=[(0, 172.66, -43.53, 0.22), (1, 172.68, -43.525, 0.17)], markers=[("CITY CENTRE", "chch", 0.0)],
                 zone=("avon", 0.2, "LIQUEFACTION")),
    "redzone_cbd": dict(cam=[(0, 172.637, -43.532, 0.1), (1, 172.637, -43.532, 0.08)], zone=("cbd", 0.05, "CBD RED ZONE")),
    "redzone_east": dict(cam=[(0, 172.68, -43.524, 0.18), (1, 172.69, -43.522, 0.15)], markers=[("CITY CENTRE", "chch", 0.0)],
                         zone=("avon", 0.1, "RESIDENTIAL RED ZONE")),
}


def interp_cam(cam, k):
    for (a, b) in zip(cam, cam[1:]):
        if a[0] <= k <= b[0]:
            u = ease((k - a[0]) / max(1e-6, b[0] - a[0]))
            lo = a[1] + (b[1] - a[1]) * u
            la = a[2] + (b[2] - a[2]) * u
            sp = math.exp(math.log(a[3]) + (math.log(b[3]) - math.log(a[3])) * u)
            return lo, la, sp
    return cam[-1][1:]


def g_map(spec, u, d, t):
    seq = MAPSEQ[spec["seq"]]
    k = u / d
    lo, la, sp = interp_cam(seq["cam"], k)
    img, P = map_view(lo, la, sp)
    im = Image.fromarray(img).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    fl = F("oswald", 30, "Medium")
    fs = F("oswald", 24, "Regular")
    for (txt, lo_, la_, a0, a1) in seq.get("labels", []):
        a = ease((k - a0) / 0.1) * (1 - ease((k - a1) / 0.1))
        if a > 0:
            x, y = P(lo_, la_)
            dr.text((x, y), txt, font=F("oswald", 46, "Light"), fill=WHITE + (int(220 * a),), anchor="mm")
    zone = seq.get("zone")
    if zone:
        kind, a0, lab = zone
        a = ease((k - a0) / 0.2)
        if kind == "cbd":
            pts = [(172.623, -43.522), (172.652, -43.522), (172.652, -43.540), (172.623, -43.540)]
        else:
            pts = [(x, y + 0.006) for x, y in AVON[4:]] + [(x, y - 0.007) for x, y in AVON[4:]][::-1]
        poly = [P(x, y) for x, y in pts]
        dr.polygon(poly, fill=RED + (int(90 * a),), outline=RED + (int(255 * a),))
        if lab:
            cx = sum(p[0] for p in poly) / len(poly)
            cy = min(p[1] for p in poly) - 40
            dr.text((cx, cy), lab, font=F("oswald", 40, "Bold"), fill=WHITE + (int(255 * a),), anchor="mm")
    for (lab, pts, a0, glow) in seq.get("paths", []):
        p = ease_out((k - a0) / 0.35)
        if p <= 0:
            continue
        sc = [P(x, y) for x, y in pts]
        n = max(2, int(len(sc) * p + 0.999))
        seg = sc[:n]
        if n <= len(sc):
            # partial last segment
            fx = len(sc) * p - (n - 1)
            if n >= 2 and fx < 1:
                (ax, ay), (bx, by) = sc[n - 2], sc[n - 1]
                seg = sc[:n - 1] + [(ax + (bx - ax) * max(0, fx), ay + (by - ay) * max(0, fx))]
        col = RED if glow else (230, 200, 120)
        if glow:
            pulse = 0.6 + 0.4 * math.sin(t * 4)
            gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(gl).line(seg, fill=RED + (int(200 * pulse),), width=16)
            ov.alpha_composite(gl.filter(ImageFilter.GaussianBlur(10)))
        for i in range(len(seg) - 1):
            dr.line([seg[i], seg[i + 1]], fill=col + (255,), width=5)
        if p > 0.7:
            mx, my = sc[len(sc) // 2]
            dr.text((mx, my + 34), lab, font=F("oswald", 34, "Bold"), fill=col + (int(255 * ease((p - 0.7) / 0.3)),), anchor="mm")
    for (a, b, lab, a0) in seq.get("lines", []):
        p = ease_out((k - a0) / 0.25)
        if p <= 0:
            continue
        (ax, ay), (bx, by) = P(*PLACES[a]), P(*PLACES[b])
        ex, ey = ax + (bx - ax) * p, ay + (by - ay) * p
        n = int(math.hypot(ex - ax, ey - ay) / 18)
        for i in range(n):
            if i % 2 == 0:
                f0, f1 = i / max(n, 1), (i + 1) / max(n, 1)
                dr.line([(ax + (ex - ax) * f0, ay + (ey - ay) * f0), (ax + (ex - ax) * f1, ay + (ey - ay) * f1)], fill=WHITE + (230,), width=3)
        if p > 0.8:
            mx, my = (ax + bx) / 2, (ay + by) / 2
            tw = dr.textlength(lab, font=F("oswald", 40, "Bold"))
            dr.rectangle([mx - tw / 2 - 14, my - 58, mx + tw / 2 + 14, my - 10], fill=(10, 10, 10, 210))
            dr.text((mx, my - 34), lab, font=F("oswald", 40, "Bold"), fill=WHITE + (255,), anchor="mm")
    for (key, a0) in seq.get("rings", []):
        if k < a0:
            continue
        x, y = P(*PLACES[key])
        for j in range(4):
            ph = ((u - a0 * d) * 0.8 + j / 4) % 1
            r = 10 + ph * 260
            dr.ellipse([x - r, y - r, x + r, y + r], outline=RED + (int(255 * (1 - ph)),), width=4)
    for (lab, key, a0) in seq.get("epis", []):
        a = ease((k - a0) / 0.08)
        if a <= 0:
            continue
        x, y = P(*PLACES[key])
        r = 20
        dr.line([x - r, y - r, x + r, y + r], fill=RED + (int(255 * a),), width=7)
        dr.line([x - r, y + r, x + r, y - r], fill=RED + (int(255 * a),), width=7)
        dr.text((x, y + 48), lab, font=F("oswald", 34, "Bold"), fill=RED + (int(255 * a),), anchor="mm")
    for (lab, key, a0) in seq.get("markers", []):
        a = ease((k - a0) / 0.08)
        if a <= 0:
            continue
        x, y = P(*PLACES[key])
        pr = 14 + 5 * math.sin(t * 5)
        dr.ellipse([x - pr, y - pr, x + pr, y + pr], outline=RED + (int(255 * a),), width=4)
        dr.ellipse([x - 5, y - 5, x + 5, y + 5], fill=RED + (int(255 * a),))
        tw = dr.textlength(lab, font=fl)
        lx, ly = x + 34, y - 46
        dr.line([x + 10, y - 10, lx, ly + 20], fill=WHITE + (int(200 * a),), width=2)
        dr.rectangle([lx, ly, lx + tw + 22, ly + 40], fill=(12, 12, 12, int(200 * a)))
        dr.rectangle([lx, ly, lx + 5, ly + 40], fill=RED + (int(255 * a),))
        dr.text((lx + 14, ly + 20), lab, font=fl, fill=WHITE + (int(255 * a),), anchor="lm")
    dots = seq.get("dots")
    if dots:
        key, a0, a1 = dots
        rng = np.random.default_rng(4)
        N = 900
        cx, cy = PLACES[key]
        if key == "sept":
            tt = rng.random(N)
            pts_lon = 171.98 + tt * 0.6 + rng.normal(0, 0.05, N)
            pts_lat = -43.57 + rng.normal(0, 0.035, N) + tt * 0.01
        else:
            pts_lon = cx + rng.normal(0, 0.05, N)
            pts_lat = cy + rng.normal(0, 0.02, N)
        times = np.sort(rng.random(N) ** 1.8)
        frac = (k - a0) / (a1 - a0)
        shown = int(np.searchsorted(times, frac))
        for i in range(shown):
            x, y = P(pts_lon[i], pts_lat[i])
            age = frac - times[i]
            r = 4 + 10 * max(0, 1 - age * 30)
            al = int(255 * (0.55 + 0.45 * max(0, 1 - age * 20)))
            dr.ellipse([x - r, y - r, x + r, y + r], outline=(255, 120, 40, al), width=2)
        if seq.get("months"):
            months = ["SEP 2010", "OCT 2010", "NOV 2010", "DEC 2010", "JAN 2011", "FEB 2011"]
            m = months[min(5, int(max(0, frac) * 6))]
            dr.text((110, 110), m, font=F("type", 64), fill=RED + (255,))
            dr.text((110, 190), "THOUSANDS OF AFTERSHOCKS", font=F("oswald", 34, "Regular"), fill=WHITE + (230,))
        if seq.get("label_top"):
            dr.text((110, 110), seq["label_top"], font=F("type", 64), fill=RED + (255,))
    im.alpha_composite(ov)
    out = np.asarray(im.convert("RGB")).copy()
    # scan-line / radar tint like the reference
    out = (out.astype(np.float32) * np.array([0.97, 1.0, 1.02])).clip(0, 255).astype(np.uint8)
    return out


# ================================================================== other graphics
def g_black(spec, u, d, t):
    return np.zeros((H, W, 3), np.uint8)


def trace(n, t, spike_at, amp_big, seed=0, vertical=False):
    rng = np.random.default_rng(seed)
    base = rng.normal(0, 1, n * 4).astype(np.float32)
    base = np.convolve(base, np.ones(3) / 3, "same")
    return base


def g_seismo(spec, u, d, t):
    im = canvas()
    dr = ImageDraw.Draw(im)
    x0, x1, yc = 140, W - 140, 600
    for i in range(9):
        y = 300 + i * 75
        dr.line([x0, y, x1, y], fill=(40, 42, 44), width=1)
    for i in range(0, 31):
        x = x0 + (x1 - x0) * i / 30
        dr.line([x, 300, x, 900], fill=(32, 34, 36), width=1)
    spike_t = d * 0.3
    pts = []
    N = 900
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 1, 20000)
    speed = 1.0
    for i in range(N):
        tt = u - (N - i) / N * 4.0  # 4 seconds visible window
        if tt < 0:
            v = 0.0
        else:
            j = int(tt * 2000) % 20000
            v = noise[j] * 4
            if tt > spike_t:
                e = (tt - spike_t)
                v += noise[(j * 7) % 20000] * 280 * math.exp(-e * 0.9) * min(1, e * 6) * (math.sin(tt * 40) * 0.5 + 0.7)
        pts.append((x0 + (x1 - x0) * i / N, yc + max(-290, min(290, v))))
    if len(pts) > 1:
        dr.line(pts, fill=(235, 70, 60), width=3)
    if spec.get("vertical"):
        a = ease((u - spike_t - 0.3) / 0.5)
        for s_ in (-1, 1):
            y = yc + s_ * 130
            dr.line([x0, y, x1, y], fill=(90, 160, 230, 255), width=3)
        dr.text((x1 - 10, yc - 150), "1 g  (GRAVITY)", font=F("oswald", 30, "Regular"), fill=(90, 160, 230), anchor="rs")
    dr.text((x0, 200), spec.get("label", ""), font=F("oswald", 34, "Regular"), fill=GREY)
    a = ease((u - spike_t - 0.4) / 0.4)
    if a > 0:
        sc = 1 + 0.3 * (1 - ease_out((u - spike_t - 0.4) / 0.3))
        f = F("oswald", int(170 * sc), "Bold")
        lab = ("M " if not spec.get("vertical") else "") + spec["mag"]
        dr.text((x1, 140), lab, font=f, fill=(225, 40, 40), anchor="ra")
    return to_np(im)


def g_gforce(spec, u, d, t):
    im = canvas()
    dr = ImageDraw.Draw(im)
    base_y = 900
    bars = [("GRAVITY", 1.0, (110, 160, 220)), ("GROUND (VERTICAL)", 2.2, (225, 40, 40))]
    unit = 250
    for i, (lab, val, col) in enumerate(bars):
        x = 640 + i * 520
        p = ease_out((u - 0.3 - i * 0.6) / 1.2)
        hgt = unit * val * p
        dr.rectangle([x - 110, base_y - hgt, x + 110, base_y], fill=col)
        dr.text((x, base_y + 50), lab, font=F("oswald", 38, "Medium"), fill=WHITE, anchor="mm")
        if p > 0.05:
            v = val * p
            dr.text((x, base_y - hgt - 60), f"{v:.1f} g", font=F("oswald", 76, "Bold"), fill=col, anchor="mm")
    dr.line([380, base_y, 1540, base_y], fill=WHITE, width=3)
    dr.line([380, base_y - unit, 1540, base_y - unit], fill=(110, 160, 220), width=2)
    a = ease((u - 2.4) / 0.5)
    if a > 0:
        dr.text((W / 2, 140), "MORE THAN TWICE THE FORCE OF GRAVITY", font=F("oswald", 56, "Bold"),
                fill=WHITE + (int(255 * a),), anchor="mm")
        dr.text((W / 2, 205), "Peak vertical ground acceleration recorded near the epicentre",
                font=F("playfair", 30, "Italic"), fill=GREY, anchor="mm")
    return to_np(im)


def g_compare(spec, u, d, t):
    im = canvas()
    dr = ImageDraw.Draw(im)
    mode = spec.get("mode", "mag")
    cols = [(W * 0.3, "4 SEPTEMBER 2010", "7.1", (150, 160, 170)), (W * 0.7, "22 FEBRUARY 2011", "6.2", (225, 40, 40))]
    for i, (x, dt, m, col) in enumerate(cols):
        a = ease((u - 0.2 - i * 0.5) / 0.5) if not spec.get("hold") else 1
        dr.text((x, 230), dt, font=F("oswald", 40, "Regular"), fill=WHITE + (int(255 * a),), anchor="mm")
        dr.text((x, 400), "M " + m, font=F("oswald", 190, "Bold"), fill=col + (int(255 * a),), anchor="mm")
        # energy circle (area ~ energy)
        if mode in ("mag", "question"):
            r = 190 if i == 0 else 190 / math.sqrt(22.4)
            r *= ease_out((u - 0.6 - i * 0.5) / 0.8) if not spec.get("hold") else 1
            dr.ellipse([x - r, 720 - r, x + r, 720 + r], outline=col + (255,), width=4)
    if mode == "mag" and u > 1.8:
        a = ease((u - 1.8) / 0.5) if not spec.get("hold") else 1
        dr.text((W / 2, 960), "THE 2011 QUAKE RELEASED ROUGHLY 20× LESS ENERGY", font=F("oswald", 44, "Medium"),
                fill=WHITE + (int(255 * a),), anchor="mm")
    if mode == "tease":
        for i, (x, dt, m, col) in enumerate(cols):
            a = ease((u - 1.5 - i * 0.6) / 0.5)
            dr.text((x, 640), "DEATHS CAUSED", font=F("oswald", 36, "Regular"), fill=GREY + (int(255 * a),), anchor="mm")
            dr.text((x, 760), "0 direct" if i == 0 else "185", font=F("oswald", 120, "Bold"), fill=col + (int(255 * a),), anchor="mm")
    if mode == "question":
        a = ease((u - 0.8) / 0.4)
        dr.text((W / 2, 400), "?", font=F("playfair", 260, "Black"), fill=WHITE + (int(255 * a),), anchor="mm")
    return to_np(im)


def g_timeline(spec, u, d, t):
    im = canvas()
    dr = ImageDraw.Draw(im)
    y = 560
    xa, xb = 420, 1500
    dr.line([200, y, W - 200, y], fill=(90, 90, 90), width=3)
    months = ["SEP", "OCT", "NOV", "DEC", "JAN", "FEB"]
    for i, m in enumerate(months):
        x = xa + (xb - xa) * i / 5
        dr.line([x, y - 12, x, y + 12], fill=(120, 120, 120), width=2)
        dr.text((x, y + 44), m, font=F("oswald", 30, "Regular"), fill=GREY, anchor="mm")
    mode = spec.get("mode")
    for x, lab, m in ((xa, "4 SEPT 2010", "7.1"), (xb, "22 FEB 2011", "6.2")):
        flash = mode == "twice" and ((x == xa and 0.15 < u < 1.0) or (x == xb and u > 1.0))
        col = RED if (flash or mode == "rewind") else WHITE
        dr.ellipse([x - 16, y - 16, x + 16, y + 16], fill=col)
        dr.text((x, y - 70), lab, font=F("oswald", 40, "Medium"), fill=col, anchor="mm")
        if mode == "twice":
            dr.text((x, y - 160), "M " + m, font=F("oswald", 90, "Bold"), fill=col, anchor="mm")
    if mode == "rewind":
        p = ease((u - 0.3) / 2.0)
        x = xb + (xa - xb) * p
        dr.line([x, y - 120, x, y + 120], fill=RED, width=4)
        dr.text((x, y - 150), "◀◀ REWIND", font=F("oswald", 40, "Bold"), fill=RED, anchor="mm")
        a = ease((u - 2.0) / 0.5)
        dr.text((W / 2, y + 170), "FIVE MONTHS EARLIER", font=F("type", 60), fill=WHITE + (int(255 * a),), anchor="mm")
    arr = to_np(im)
    if mode == "rewind" and 0.3 < u < 2.3:
        arr = cv2.blur(arr, (int(4 + 20 * math.sin((u - 0.3) / 2 * math.pi)), 1))
    return arr


def g_clock(spec, u, d, t):
    im = canvas()
    dr = ImageDraw.Draw(im)
    cx, cy, R = W / 2, 470, 300
    dr.ellipse([cx - R, cy - R, cx + R, cy + R], outline=WHITE, width=6, fill=(18, 18, 20))
    for i in range(60):
        a = i / 60 * 2 * math.pi
        r0 = R - (40 if i % 5 == 0 else 18)
        dr.line([cx + math.sin(a) * r0, cy - math.cos(a) * r0, cx + math.sin(a) * (R - 8), cy - math.cos(a) * (R - 8)],
                fill=WHITE, width=5 if i % 5 == 0 else 2)
    hh, mm = map(int, spec["time"].split(":"))
    if spec.get("tick"):
        sec = 59 * (u / d) ** (0.6 if spec.get("fast") else 1.0) if spec.get("fast") else 20 + u
        sec = int(sec)
    else:
        sec = int(u) % 60
    mm_f = mm + sec / 60
    for ang, ln, wd, col in (((hh % 12 + mm_f / 60) / 12, R * 0.5, 12, WHITE), (mm_f / 60, R * 0.78, 8, WHITE),
                             (sec / 60, R * 0.86, 3, RED)):
        a = ang * 2 * math.pi
        dr.line([cx, cy, cx + math.sin(a) * ln, cy - math.cos(a) * ln], fill=col, width=wd)
    dr.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=RED)
    dr.text((cx, 880), f"{hh:02d}:{mm:02d}:{sec:02d} {spec.get('sub', '')}", font=F("type", 80), fill=RED, anchor="mm")
    return to_np(im)


def g_counter(spec, u, d, t):
    im = canvas()
    dr = ImageDraw.Draw(im)
    v = spec["value"]
    money = "prefix" in spec
    if money:
        shown = int(round(v * ease_out(u / 2.0)))
    else:
        shown = v
    a = ease(u / 1.0)
    txt = f"{spec.get('prefix', '')}{shown}{spec.get('suffix', '')}"
    col = WHITE if not money else (225, 40, 40)
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gl)
    gd.text((W / 2, 470), txt, font=F("oswald", 260 if not money else 200, "Bold"), fill=col + (int(255 * a),), anchor="mm")
    im = im.convert("RGBA")
    im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(18)))
    im.alpha_composite(gl)
    dr = ImageDraw.Draw(im)
    la = ease((u - 0.8) / 0.8)
    dr.text((W / 2, 680), spec["label"], font=F("oswald", 44, "Regular"), fill=(200, 195, 185, int(255 * la)), anchor="mm")
    dr.rectangle([W / 2 - 260 * la, 730, W / 2 + 260 * la, 732], fill=RED + (int(255 * la),))
    return to_np(im)


@lru_cache(maxsize=1)
def world_base():
    g = json.load(open(os.path.join(HERE, "assets", "geo", "ne_110m_land.geojson")))
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    def P(lon, lat):
        lon2 = (lon - 150 + 180) % 360 - 180
        return (W / 2 + lon2 / 360 * W * 1.0, H / 2 - lat / 180 * W * 1.0 * 0.5 * 1.1 + 60)

    for f in g["features"]:
        geom = f["geometry"]
        polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        for poly in polys:
            ring = poly[0]
            # split at dateline jumps
            seg = []
            prev = None
            for lon, lat in ring:
                p = P(lon, lat)
                if prev and abs(p[0] - prev[0]) > W / 2:
                    if len(seg) > 2:
                        d.polygon(seg, fill=(48, 52, 56))
                    seg = []
                seg.append(p)
                prev = p
            if len(seg) > 2:
                d.polygon(seg, fill=(48, 52, 56))
    arr = np.asarray(im).astype(np.float32)
    arr += (fbm(H, W, 5, 5, 8)[..., None] - 0.5) * 18
    return np.clip(arr, 0, 255).astype(np.uint8), P


COUNTRIES = {"JAPAN": (139.7, 35.7), "CHINA": (116.4, 39.9), "PHILIPPINES": (121.0, 14.6), "SOUTH KOREA": (127.0, 37.5),
             "THAILAND": (100.5, 13.7), "TAIWAN": (121.5, 25.0), "AUSTRALIA": (149.1, -35.3), "UNITED STATES": (-77.0, 38.9),
             "UNITED KINGDOM": (-0.1, 51.5), "SINGAPORE": (103.8, 1.35), "ISRAEL": (35.2, 31.8), "SERBIA": (20.5, 44.8),
             "CANADA": (-75.7, 45.4), "IRELAND": (-6.3, 53.3), "TURKEY": (32.9, 39.9)}


def g_world(spec, u, d, t):
    base, P = world_base()
    im = Image.fromarray(base).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    nz = P(172.6, -43.5)
    if spec["seq"] == "families":
        names = ["JAPAN", "CHINA", "PHILIPPINES", "SOUTH KOREA", "THAILAND", "TAIWAN", "ISRAEL", "IRELAND"]
        outward = True
        title = "FAMILIES WAITING FOR NEWS, ACROSS THE WORLD"
    else:
        names = ["AUSTRALIA", "JAPAN", "UNITED STATES", "UNITED KINGDOM", "TAIWAN", "SINGAPORE", "CHINA"]
        outward = False
        title = "INTERNATIONAL SEARCH & RESCUE TEAMS"
    for i, nm in enumerate(names):
        a0 = 0.6 + i * (d * 0.6) / len(names)
        p = ease_out((u - a0) / 1.2)
        if p <= 0:
            continue
        cx, cy = P(*COUNTRIES[nm])
        (sx, sy), (ex, ey) = ((nz, (cx, cy)) if outward else ((cx, cy), nz))
        mx, my = (sx + ex) / 2, (sy + ey) / 2 - math.hypot(ex - sx, ey - sy) * 0.25
        pts = []
        for j in range(41):
            s = j / 40 * p
            pts.append(((1 - s) ** 2 * sx + 2 * (1 - s) * s * mx + s * s * ex, (1 - s) ** 2 * sy + 2 * (1 - s) * s * my + s * s * ey))
        dr.line(pts, fill=(230, 70, 60, 220), width=3)
        dr.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=WHITE + (255,))
        dr.text((cx + 12, cy - 4), nm, font=F("oswald", 24, "Regular"), fill=WHITE + (int(230 * min(1, p * 2)),), anchor="ls")
    pr = 12 + 6 * math.sin(t * 5)
    dr.ellipse([nz[0] - pr, nz[1] - pr, nz[0] + pr, nz[1] + pr], outline=RED + (255,), width=4)
    dr.text((nz[0] - 20, nz[1] + 34), "CHRISTCHURCH", font=F("oswald", 28, "Bold"), fill=RED + (255,), anchor="rm")
    a = ease(u / 0.8)
    dr.text((W / 2, 70), title, font=F("oswald", 48, "Medium"), fill=WHITE + (int(255 * a),), anchor="mm")
    im.alpha_composite(ov)
    return np.asarray(im.convert("RGB"))


def g_quote(spec, u, d, t):
    im = canvas()
    dr = ImageDraw.Draw(im)
    lines = spec["text"].split("\n")
    a = ease(u / 1.0)
    for i, ln in enumerate(lines):
        aa = ease((u - 0.2 - i * 0.6) / 0.8)
        dr.text((W / 2, 420 + i * 120), ln, font=F("playfair", 96, "Italic"), fill=WHITE + (int(255 * aa),), anchor="mm")
    sa = ease((u - 1.4) / 0.6)
    dr.rectangle([W / 2 - 60, 680, W / 2 + 60, 683], fill=RED)
    dr.text((W / 2, 740), spec["who"], font=F("oswald", 34, "Regular"), fill=(190, 185, 175, int(255 * sa)), anchor="mm")
    return to_np(im)


def g_doc(spec, u, d, t):
    im = canvas()
    st = spec.get("stage", 0)
    paper = Image.new("RGB", (900, 1180), (226, 220, 205))
    pd = ImageDraw.Draw(paper)
    pn = (fbm(1180, 900, 77, 5, 6) * 30).astype(np.uint8)
    paper = Image.fromarray(np.clip(np.asarray(paper).astype(np.int16) - pn[..., None], 0, 255).astype(np.uint8))
    pd = ImageDraw.Draw(paper)
    pd.text((450, 110), "ROYAL COMMISSION OF INQUIRY", font=F("playfair", 40, "Bold"), fill=(30, 30, 30), anchor="mm")
    pd.text((450, 165), "Canterbury Earthquakes", font=F("playfair", 34, "Italic"), fill=(40, 40, 40), anchor="mm")
    pd.line([120, 210, 780, 210], fill=(60, 60, 60), width=2)
    pd.text((120, 250), "Building failure: CTV Building", font=F("playfair", 30, "Bold"), fill=(30, 30, 30))
    rng = np.random.default_rng(3)
    y = 310
    hl_rows = [5, 6, 7] if st >= 1 else []
    for r in range(22):
        ln = rng.uniform(420, 660)
        if r in hl_rows:
            p = ease_out((u - 0.8 - (r - 5) * 0.5) / 0.6) if st == 1 else 1
            pd.rectangle([116, y - 4, 116 + (ln + 8) * p, y + 22], fill=(240, 200, 60))
        pd.rectangle([120, y, 120 + ln, y + 16], fill=(90, 90, 90))
        y += 38
        if r == 10:
            y += 20
    rot = paper.rotate(-3 + 1.0 * math.sin(u * 0.3), resample=Image.BICUBIC, expand=True, fillcolor=(0, 0, 0))
    sc = 0.78 + 0.04 * u / max(d, 1)
    rot = rot.resize((int(rot.width * sc), int(rot.height * sc)), Image.BICUBIC)
    mask = Image.fromarray((np.asarray(rot.convert("L")) > 5).astype(np.uint8) * 255)
    sh = Image.new("RGBA", rot.size, (0, 0, 0, 160))
    imr = im.convert("RGBA")
    imr.paste(sh, (W // 2 - rot.width // 2 + 20, H // 2 - rot.height // 2 + 30), mask.filter(ImageFilter.GaussianBlur(12)))
    imr.paste(rot, (W // 2 - rot.width // 2, H // 2 - rot.height // 2), mask)
    dr = ImageDraw.Draw(imr)
    if st == 1 and u > 2.5:
        a = ease((u - 2.5) / 0.6)
        dr.rectangle([1260, 440, 1840, 600], fill=(12, 12, 12, int(220 * a)))
        dr.rectangle([1260, 440, 1268, 600], fill=RED + (int(255 * a),))
        dr.text((1290, 470), "FINDINGS", font=F("oswald", 30, "Regular"), fill=RED + (int(255 * a),))
        dr.text((1290, 510), "Serious problems in design\nand approval", font=F("oswald", 36, "Medium"),
                fill=WHITE + (int(255 * a),))
    if st == 2:
        a = ease((u - 0.3) / 0.6)
        dr.rectangle([1260, 440, 1840, 640], fill=(12, 12, 12, int(220 * a)))
        dr.rectangle([1260, 440, 1268, 640], fill=(60, 200, 110, int(255 * a)))
        dr.text((1290, 470), "RESULT", font=F("oswald", 30, "Regular"), fill=(60, 200, 110, int(255 * a)))
        dr.text((1290, 510), "Major changes to how NZ\ndeals with earthquake-\nprone buildings", font=F("oswald", 36, "Medium"),
                fill=WHITE + (int(255 * a),))
    dr.text((40, H - 50), "Illustrative reconstruction", font=F("oswald", 22, "Light"), fill=(120, 120, 120))
    return np.asarray(imr.convert("RGB"))


def g_reasons(spec, u, d, t):
    im = canvas()
    dr = ImageDraw.Draw(im)
    st = spec["stage"]
    items = [("DISTANCE", "40 km away", "~10 km away"), ("DEPTH", "~10 km deep", "~5 km deep"),
             ("TIMING", "04:35 AM · streets empty", "12:51 PM · streets full"),
             ("DAMAGE ALREADY THERE", "Buildings intact", "Weakened by thousands\nof aftershocks")]
    dr.text((W / 2, 110), "WHY 6.2 WAS DEADLIER THAN 7.1", font=F("oswald", 54, "Bold"), fill=WHITE, anchor="mm")
    for i, (ttl, a_, b_) in enumerate(items):
        x = 120 + i * 435
        active = (i + 1) == st
        done = (i + 1) < st
        app = ease((u - i * 0.25) / 0.4) if st == 0 else 1
        col = RED if active else ((200, 195, 185) if done else (90, 90, 90))
        al = int(255 * app)
        dr.rectangle([x, 220, x + 400, 900], outline=col + (al,), width=4 if active else 2)
        dr.text((x + 30, 250), f"{i + 1}", font=F("oswald", 110, "Bold"), fill=col + (al,))
        dr.text((x + 30, 400), ttl, font=F("oswald", 40, "Bold"), fill=col + (al,))
        if active or done:
            k = ease((u - 0.3) / 0.6) if active else 1
            dr.text((x + 30, 500), "SEPT 2010", font=F("oswald", 26, "Regular"), fill=(140, 140, 140, int(255 * k)))
            dr.multiline_text((x + 30, 535), a_, font=F("oswald", 34, "Medium"), fill=(200, 200, 200, int(255 * k)))
            k2 = ease((u - 0.9) / 0.6) if active else 1
            dr.text((x + 30, 680), "FEB 2011", font=F("oswald", 26, "Regular"), fill=(225, 80, 70, int(255 * k2)))
            dr.multiline_text((x + 30, 715), b_, font=F("oswald", 34, "Medium"), fill=WHITE + (int(255 * k2),))
    return to_np(im)


def g_soil(spec, u, d, t):
    im = canvas()
    dr = ImageDraw.Draw(im)
    st = spec["stage"]
    if st == 0:
        layers = [(380, 520, (120, 105, 80), "SAND & SILT"), (520, 680, (95, 90, 80), "SILT · CLAY"),
                  (680, 840, (110, 108, 100), "GRAVEL"), (840, 1000, (70, 68, 64), "OLD RIVER & SWAMP DEPOSITS")]
        for i, (y0, y1, col, lab) in enumerate(layers):
            a = ease((u - 0.3 * i) / 0.6)
            dr.rectangle([140, y0, W - 140, y1], fill=tuple(int(c * a + 12 * (1 - a)) for c in col))
            dr.text((W - 170, (y0 + y1) / 2), lab, font=F("oswald", 34, "Medium"), fill=WHITE, anchor="rm")
        wa = ease((u - 1.8) / 0.6)
        dr.line([140, 470, W - 140, 470], fill=(80, 160, 230, int(255 * wa)), width=4)
        dr.text((170, 440), "WATER TABLE", font=F("oswald", 30, "Regular"), fill=(80, 160, 230, int(255 * wa)), anchor="ls")
        for x in range(260, W - 200, 230):
            dr.rectangle([x, 300, x + 120, 380], fill=(170, 165, 155))
            dr.polygon([(x - 10, 300), (x + 60, 250), (x + 130, 300)], fill=(120, 60, 50))
        dr.text((W / 2, 140), "THE GROUND BENEATH CHRISTCHURCH", font=F("oswald", 56, "Bold"), fill=WHITE, anchor="mm")
        return to_np(im)
    # grain-scale view
    rng = np.random.default_rng(2)
    n = 150
    gx = rng.uniform(260, W - 260, n)
    gy = rng.uniform(380, 980, n)
    gr = rng.uniform(26, 46, n)
    dr.rectangle([200, 340, W - 200, 1020], fill=(30, 70, 110))  # water fills the gaps
    k = 0.0
    if st == 2:
        k = ease((u - 2.0) / (d * 0.5))
    shake = 0.0 if st == 1 else (min(1.0, u / 1.5) * 18 * (1 - 0.3 * k))
    for i in range(n):
        dx = shake * math.sin(t * 40 + i)
        dy = shake * math.cos(t * 33 + i * 1.7) - k * 60 * ((i * 37) % 11 / 11)
        x = gx[i] + dx + k * (gx[i] - W / 2) * 0.08
        y = gy[i] + dy + k * (gy[i] - 680) * 0.18
        r = gr[i] * (1 - 0.15 * k)
        col = (176 - (i % 5) * 9, 152 - (i % 5) * 8, 112 - (i % 5) * 6)
        dr.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=(80, 70, 55), width=2)
    # building on top sinking
    sink = 140 * k
    tilt = 8 * k
    bx, by = W / 2, 340 + sink
    pts = [(-160, 0), (160, 0), (160, -260), (-160, -260)]
    ca, sa = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    poly = [(bx + px * ca - py * sa, by + px * sa + py * ca) for px, py in pts]
    dr.polygon(poly, fill=(160, 158, 150), outline=(220, 220, 220))
    dr.text((W / 2, 110), "GRAINS & WATER" if st == 1 else "LIQUEFACTION", font=F("oswald", 56, "Bold"), fill=WHITE, anchor="mm")
    labs = ["WATER FILLS THE SPACES BETWEEN GRAINS"] if st == 1 else ["SHAKING RAISES WATER PRESSURE",
                                                                       "GRAINS LOSE THEIR GRIP",
                                                                       "SOLID GROUND BEHAVES LIKE A LIQUID"]
    for i, lb in enumerate(labs):
        a = ease((u - 0.5 - i * (d / 3.2)) / 0.5)
        if a > 0:
            dr.rectangle([140, 170 + i * 0, 140, 170], fill=RED)
    if st == 1:
        dr.text((W / 2, 180), labs[0], font=F("oswald", 40, "Regular"), fill=(150, 200, 240), anchor="mm")
    else:
        idx = min(2, int(u / (d / 3)))
        a = ease((u - idx * d / 3) / 0.4)
        dr.text((W / 2, 180), labs[idx], font=F("oswald", 40, "Regular"), fill=(240, 120, 100, int(255 * a)), anchor="mm")
        if idx >= 0:
            for i in range(5):
                ax = 400 + i * 280
                ay = 900 - ((u * 120 + i * 50) % 300)
                dr.line([ax, ay + 60, ax, ay], fill=(120, 190, 255), width=5)
                dr.polygon([(ax - 14, ay), (ax + 14, ay), (ax, ay - 22)], fill=(120, 190, 255))
    return to_np(im)


def g_depth(spec, u, d, t):
    im = canvas()
    dr = ImageDraw.Draw(im)
    gy = 330
    dr.rectangle([0, gy, W, H], fill=(38, 34, 30))
    dr.line([0, gy, W, gy], fill=WHITE, width=3)
    for km in (5, 10):
        y = gy + km * 60
        dr.line([90, y, W - 90, y], fill=(70, 66, 60), width=1)
        dr.text((80, y), f"{km} KM", font=F("oswald", 28, "Regular"), fill=GREY, anchor="rm")
    for (x, km, lab, col, a0) in ((560, 10, "SEPT 2010", (150, 160, 170), 0.3), (1360, 5, "FEB 2011", RED, 1.0)):
        a = ease((u - a0) / 0.5)
        y = gy + km * 60
        for j in range(3):
            ph = ((u - a0) * 0.7 + j / 3) % 1
            r = 20 + ph * 300
            if a > 0:
                dr.ellipse([x - r, y - r, x + r, y + r], outline=col + (int(200 * (1 - ph) * a),), width=3)
        dr.ellipse([x - 14, y - 14, x + 14, y + 14], fill=col + (int(255 * a),))
        dr.text((x, gy - 60), lab, font=F("oswald", 44, "Bold"), fill=col + (int(255 * a),), anchor="mm")
        dr.text((x + 30, y + 40), f"~{km} km deep", font=F("oswald", 34, "Medium"), fill=WHITE + (int(255 * a),), anchor="lm")
    dr.text((W / 2, 110), "A SHALLOW RUPTURE", font=F("oswald", 60, "Bold"), fill=WHITE, anchor="mm")
    return to_np(im.convert("RGB"))


def g_sway(spec, u, d, t):
    im = canvas()
    dr = ImageDraw.Draw(im)
    st = spec["stage"]
    gy = 860
    dx = dy = 0.0
    if st == 1:
        dx = 50 * math.sin(u * 4.0)
    if st == 2:
        dy = -110 * abs(math.sin(u * 9)) * math.exp(-((u % 1.6)) * 1.5) if u > 0.4 else 0
    dr.rectangle([300, gy + max(0, -dy) * 0 + dy * 0.6, W - 300, gy + 30 + dy * 0.6], fill=(80, 74, 66))
    bx = W / 2 + dx
    floors = 6
    for f in range(floors):
        lean = dx * (f / floors) * 0.6
        y0 = gy + dy - f * 95
        dr.rectangle([bx - 170 + lean, y0 - 95, bx + 170 + lean, y0], outline=WHITE, width=4, fill=(30, 32, 36))
        for k in range(4):
            wx = bx - 140 + k * 80 + lean
            dr.rectangle([wx, y0 - 70, wx + 50, y0 - 25], fill=(70, 90, 110))
    if st == 1:
        for s_ in (-1, 1):
            x = W / 2 + s_ * 420
            dr.line([x - 80, 520, x + 80, 520], fill=(110, 160, 220), width=8)
            dr.polygon([(x + s_ * 80, 500), (x + s_ * 80, 540), (x + s_ * 115, 520)], fill=(110, 160, 220))
        dr.text((W / 2, 150), "DESIGNED FOR SIDEWAYS SHAKING", font=F("oswald", 56, "Bold"), fill=(110, 160, 220), anchor="mm")
    elif st == 2:
        dr.line([W / 2 + 420, 760, W / 2 + 420, 460], fill=RED, width=12)
        dr.polygon([(W / 2 + 390, 470), (W / 2 + 450, 470), (W / 2 + 420, 410)], fill=RED)
        dr.text((W / 2, 150), "22 FEBRUARY 2011: THE GROUND PUNCHED UP", font=F("oswald", 56, "Bold"), fill=RED, anchor="mm")
    else:
        dr.text((W / 2, 150), "THE DIRECTION OF THE SHAKING", font=F("oswald", 56, "Bold"), fill=WHITE, anchor="mm")
    return to_np(im)


RENDER = {"map": g_map, "black": g_black, "seismo": g_seismo, "gforce": g_gforce, "compare": g_compare,
          "timeline": g_timeline, "clock": g_clock, "counter": g_counter, "world": g_world, "quote": g_quote,
          "doc": g_doc, "reasons": g_reasons, "soil": g_soil, "depth": g_depth, "sway": g_sway}


def render(spec, u, d, t):
    out = RENDER[spec["name"]](spec, u, d, t)
    if out.shape[:2] != (H, W):
        out = cv2.resize(out, (W, H))
    return np.ascontiguousarray(out[..., :3])
