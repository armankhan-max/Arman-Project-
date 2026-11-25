"""Frame engine: Ken Burns images, stock video clips, crossfades, text animation, grade.

A timeline is a list of shots:
    {"s": start, "e": end, "src": "img:name" | "vid:path", "mv": motion, "ov": [overlays]}
Overlays are dicts with a "k" (kind) and "s"/"e" times (absolute seconds).
"""
import os, subprocess, math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
FONTS = os.path.join(HERE, "fonts")
XFADE = 0.5

GOLD = (226, 184, 92)
CREAM = (250, 242, 225)


def font(name, size):
    return _font(name, size)


@functools.lru_cache(maxsize=64)
def _font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def back_out(x):
    x = min(max(x, 0.0), 1.0)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


# ---------------------------------------------------------------- sources
@functools.lru_cache(maxsize=12)
def load_img(name):
    im = Image.open(os.path.join(IMG, name + ".jpg")).convert("RGB")
    # cover 16:9 at 1.25x so we can zoom/pan without losing resolution
    tw, th = int(W * 1.25), int(H * 1.25)
    r = max(tw / im.width, th / im.height)
    im = im.resize((math.ceil(im.width * r), math.ceil(im.height * r)), Image.LANCZOS)
    l = (im.width - tw) // 2
    t = (im.height - th) // 2
    return im.crop((l, t, l + tw, t + th))


MOVES = {
    #        zoom0  zoom1  cx0   cy0   cx1   cy1  (centre in 0..1 of source)
    "in":    (1.00, 1.14, .50, .50, .50, .47),
    "out":   (1.16, 1.00, .50, .46, .50, .50),
    "inL":   (1.02, 1.15, .44, .50, .38, .45),
    "inR":   (1.02, 1.15, .56, .50, .62, .45),
    "left":  (1.12, 1.12, .58, .50, .42, .50),
    "right": (1.12, 1.12, .42, .50, .58, .50),
    "up":    (1.12, 1.14, .50, .58, .50, .42),
    "down":  (1.12, 1.14, .50, .42, .50, .58),
    "face":  (1.05, 1.22, .50, .42, .50, .34),   # push into a face (upper centre)
    "faceL": (1.05, 1.20, .45, .42, .40, .36),
    "faceR": (1.05, 1.20, .55, .42, .60, .36),
}


def render_img(name, mv, u, dur):
    src = load_img(name)
    z0, z1, x0, y0, x1, y1 = MOVES.get(mv, MOVES["in"])
    k = ease(u) * 0.7 + u * 0.3
    z = z0 + (z1 - z0) * k
    cx = (x0 + (x1 - x0) * k) * src.width
    cy = (y0 + (y1 - y0) * k) * src.height
    # tiny handheld drift so nothing feels like a still slide
    t = u * dur
    cx += math.sin(t * 0.7) * 3.0
    cy += math.cos(t * 0.53) * 2.0
    scale = (src.width / 1.25) / W / z   # source px per output px
    vw, vh = W * scale, H * scale
    l = min(max(cx - vw / 2, 0), src.width - vw)
    tp = min(max(cy - vh / 2, 0), src.height - vh)
    out = src.transform((W, H), Image.AFFINE, (scale, 0, l, 0, scale, tp), resample=Image.BICUBIC)
    return np.asarray(out, dtype=np.uint8)


class VidReader:
    """Sequential raw-frame reader for one stock clip, stretched to cover a shot."""

    def __init__(self, path, dur, start_local, mv):
        info = probe(path)
        speed = 1.0
        avail = info - 0.1
        if avail < dur:
            speed = avail / dur          # slow motion to cover the shot
        self.speed = speed
        self.n = 0
        self.last = None
        ss = max(0.0, start_local * speed)
        zoom = {"in": "1.0+0.06*t/%f" % max(dur, 0.1), "out": "1.06-0.06*t/%f" % max(dur, 0.1)}.get(mv)
        vf = f"setpts=PTS/{speed},fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
        vf += ",eq=saturation=0.92:contrast=1.03,colorbalance=rs=.05:gs=.01:bs=-.06:rm=.04:bm=-.04"
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{ss:.3f}", "-i", path, "-an", "-vf", vf,
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=W * H * 3 * 2)
        self.zoom = mv

    def frame(self, want):
        while self.n <= want:
            buf = self.p.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            self.last = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            self.n += 1
        if self.last is None:
            return np.zeros((H, W, 3), np.uint8)
        return self.last

    def close(self):
        try:
            self.p.stdout.close()
            self.p.kill()
        except Exception:
            pass


@functools.lru_cache(maxsize=256)
def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout
    return float(out.strip() or 0)


def vid_zoom(fr, mv, u):
    """Gentle extra push on stock video for continuity of motion."""
    z = 1.0 + 0.06 * ease(u) if mv != "out" else 1.06 - 0.06 * ease(u)
    if z <= 1.001:
        return fr
    im = Image.fromarray(fr)
    s = 1 / z
    vw, vh = W * s, H * s
    out = im.transform((W, H), Image.AFFINE, (s, 0, (W - vw) / 2, 0, s, (H - vh) / 2), resample=Image.BILINEAR)
    return np.asarray(out)


# ---------------------------------------------------------------- finishing
@functools.lru_cache(maxsize=1)
def vignette():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    v = 1 - 0.38 * np.clip(d - 0.45, 0, 1) ** 1.6
    return v[..., None]


@functools.lru_cache(maxsize=1)
def grain_tiles():
    rng = np.random.default_rng(7)
    return [rng.normal(0, 4.0, (H // 2, W // 2, 1)).astype(np.float32) for _ in range(6)]


def finish(fr, fi):
    f = fr.astype(np.float32) * vignette()
    g = grain_tiles()[fi % 6]
    f[0::2, 0::2] += g
    f[1::2, 1::2] += g
    return np.clip(f, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- text helpers
def text_size(fnt, s, spacing=0):
    b = fnt.getbbox(s)
    return b[2] - b[0] + spacing * max(len(s) - 1, 0), b[3] - b[1], b


def draw_spaced(d, xy, s, fnt, fill, spacing=0):
    x, y = xy
    if spacing == 0:
        d.text((x, y), s, font=fnt, fill=fill)
        return
    for ch in s:
        d.text((x, y), ch, font=fnt, fill=fill)
        x += fnt.getlength(ch) + spacing


def wrap(fnt, s, maxw):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if fnt.getlength(t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def shadowed(layer, radius=10, alpha=170, offset=(0, 4)):
    """Return layer with a soft dark shadow composited beneath it."""
    a = layer.split()[3]
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    blk = Image.new("RGBA", layer.size, (0, 0, 0, alpha))
    sh.paste(blk, offset, a)
    sh = sh.filter(ImageFilter.GaussianBlur(radius))
    sh.alpha_composite(layer)
    return sh


def paste(base, layer, x, y, opacity=1.0):
    """Alpha-blend an RGBA PIL layer onto float32 HxWx3 base in place."""
    if opacity <= 0.003:
        return
    lw, lh = layer.size
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + lw, W), min(y + lh, H)
    if x1 <= x0 or y1 <= y0:
        return
    arr = np.asarray(layer, dtype=np.float32)[y0 - y:y1 - y, x0 - x:x1 - x]
    a = arr[..., 3:4] / 255.0 * opacity
    region = base[y0:y1, x0:x1]
    region *= (1 - a)
    region += arr[..., :3] * a


def dim(base, amount, region=None):
    if region is None:
        base *= (1 - amount)
    else:
        x0, y0, x1, y1 = region
        base[y0:y1, x0:x1] *= (1 - amount)


@functools.lru_cache(maxsize=1)
def bottom_grad():
    g = np.clip((np.arange(H, dtype=np.float32) - H * 0.55) / (H * 0.45), 0, 1) ** 1.4
    return (1 - 0.62 * g)[:, None, None]


@functools.lru_cache(maxsize=1)
def left_grad():
    g = np.clip(1 - np.arange(W, dtype=np.float32) / (W * 0.62), 0, 1) ** 1.2
    return (1 - 0.72 * g)[None, :, None]
