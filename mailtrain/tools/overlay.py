"""Archival-style overlays: pinned paper tag and depth chart. Returns RGBA float arrays (H,W,4)."""
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1920, 1080
FD = "fonts/"
INK = (92, 22, 18)
DARK = (40, 32, 26)

def _font(name, size, var=None):
    f = ImageFont.truetype(FD + name, size)
    if var:
        try: f.set_variation_by_name(var)
        except Exception: pass
    return f

def _paper(w, h, seed=0):
    r = np.random.default_rng(seed)
    base = np.array([226, 211, 178], np.float32)
    n = cv2.GaussianBlur(r.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 18) * 9 + r.normal(0, 3, (h, w))
    img = np.clip(base[None, None, :] + n[..., None], 0, 255)
    # darker edges
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    e = np.minimum(np.minimum(xx, w - xx), np.minimum(yy, h - yy))
    img *= (0.8 + 0.2 * np.clip(e / 40, 0, 1))[..., None]
    return Image.fromarray(img.astype(np.uint8), "RGB").convert("RGBA")

def _shadowed(card, angle, pos, canvas):
    card = card.rotate(angle, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    a = card.split()[3].point(lambda v: int(v * 0.55))
    sh.putalpha(a)
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    canvas.alpha_composite(sh, (pos[0] + 10, pos[1] + 14))
    canvas.alpha_composite(card, pos)

def tag(line1, line2, seed=0):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    f1 = _font("Playfair.ttf", 46, "Bold"); f2 = _font("Playfair.ttf", 92, "Bold")
    d0 = ImageDraw.Draw(canvas)
    w = int(max(d0.textlength(line1, font=f1), d0.textlength(line2, font=f2))) + 90
    hgt = 190
    card = _paper(w, hgt, seed)
    d = ImageDraw.Draw(card)
    d.text((44, 22), line1, font=f1, fill=DARK)
    d.text((40, 70), line2, font=f2, fill=INK)
    # pin
    d.ellipse((w - 52, 14, w - 26, 40), fill=(150, 40, 30)); d.ellipse((w - 46, 18, w - 38, 26), fill=(230, 170, 150))
    x = W - w - 150; y = H - hgt - 170
    _shadowed(card, 2.0, (x, y), canvas)
    return np.asarray(canvas).astype(np.float32) / 255

def depth(n, label="Depth", seed=1):
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    maxd = 80 if n <= 75 else 160
    pw, ph = 620, 1000
    card = _paper(pw, ph, seed)
    card.putalpha(232)
    d = ImageDraw.Draw(card)
    fh = _font("Caveat.ttf", 54, "Bold"); fn = _font("Playfair.ttf", 34)
    d.text((70, 36), "Wheat field", font=fh, fill=DARK)
    top, bot, x0 = 120, ph - 60, 230
    d.line((x0, top, x0, bot), fill=DARK, width=3)
    step = 10 if maxd == 80 else 20
    for v in range(0, maxd + 1, step // 2):
        y = top + (bot - top) * v / maxd
        if v % step == 0:
            d.line((x0 - 26, y, x0, y), fill=DARK, width=3)
            if v: d.text((x0 - 50, y), str(v), font=fn, fill=DARK, anchor="rm")
        else:
            d.line((x0 - 13, y, x0, y), fill=DARK, width=2)
    for k in range(-ph, pw, 22):  # hatching = ground
        d.line((x0 + 10 + k, top, x0 + 10 + k + (bot - top), bot), fill=(150, 130, 105), width=1)
    yv = top + (bot - top) * n / maxd
    d.line((x0 + 120, top, x0 + 120, yv), fill=INK, width=4)
    d.line((x0 - 30, yv, pw, yv), fill=INK, width=4)
    d.ellipse((x0 + 104, yv - 18, x0 + 136, yv + 18), fill=(40, 30, 28))
    _shadowed(card, -1.0, (160, 40), canvas)
    # label card
    t = tag(label, f"{n} feet", seed + 5)
    out = np.asarray(canvas).astype(np.float32) / 255
    lab = np.zeros_like(t);
    # move label next to the line
    ys = int(40 + yv - 120); xs = 160 + pw - 30
    tc = (t[..., 3] > 0.01)
    yy, xx = np.where(tc)
    cy0, cy1, cx0, cx1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
    piece = t[cy0:cy1, cx0:cx1]
    ys = max(0, min(H - piece.shape[0], ys)); xs = max(0, min(W - piece.shape[1], xs))
    lab[ys:ys + piece.shape[0], xs:xs + piece.shape[1]] = piece
    a = lab[..., 3:4]
    rgb = out[..., :3] * out[..., 3:4] * (1 - a) + lab[..., :3] * a
    al = out[..., 3:4] * (1 - a) + a
    rgb = np.where(al > 0, rgb / np.maximum(al, 1e-6), 0)
    return np.concatenate([rgb, al], -1)

if __name__ == "__main__":
    for name, ov in [("tag", tag("Railway mail car", "2,311 letters")), ("depth", depth(61, "Boxcar red"))]:
        bg = np.full((H, W, 3), 0.55, np.float32)
        o = bg * (1 - ov[..., 3:]) + ov[..., :3] * ov[..., 3:]
        cv2.imwrite(f"/tmp/claude-0/-home-user-Arman-Project-/c04745c3-b3a2-535c-9969-7c96192d22b1/scratchpad/ov_{name}.jpg", (o[..., ::-1] * 255).astype(np.uint8))
