"""Collage compositions used by the modern documentary format: a photo pinned as a card on grid paper,
and two circular cut-outs over a split colour background."""
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageOps


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def grid_paper(w, h):
    im = Image.new("RGB", (w, h), (238, 238, 234))
    d = ImageDraw.Draw(im)
    step = max(12, w // 48)
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=(214, 216, 214), width=1)
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=(214, 216, 214), width=1)
    return im


def compose(kind, path, b_path, out, w, h, accent="#E23B3B", root=None, seed=0):
    if os.path.exists(out):
        return out
    rnd = random.Random(seed)
    if b_path and root and not os.path.isabs(b_path):
        b_path = os.path.join(root, b_path)
    src = Image.open(path).convert("RGB")
    W, H = int(w * 1.3), int(h * 1.3)  # extra room for the camera move
    if kind == "card":
        bg = grid_paper(W, H)
        cw, ch = int(W * 0.62), int(H * 0.62)
        card = ImageOps.fit(src, (cw, ch), Image.LANCZOS)
        mask = Image.new("L", (cw * 2, ch * 2), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, cw * 2, ch * 2], radius=cw // 14, fill=255)
        mask = mask.resize((cw, ch), Image.LANCZOS)
        layer = Image.new("RGBA", (cw + 40, ch + 40), (0, 0, 0, 0))
        sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([24, 30, cw + 24, ch + 30], radius=cw // 14, fill=(0, 0, 0, 120))
        layer = Image.alpha_composite(layer, sh.filter(ImageFilter.GaussianBlur(14)))
        layer.paste(card, (20, 20), mask)
        layer = layer.rotate(rnd.uniform(-2.5, 2.5), resample=Image.BICUBIC, expand=True)
        bg.paste(layer, ((W - layer.width) // 2, (H - layer.height) // 2), layer)
    else:
        bg = Image.new("RGB", (W, H), _rgb(accent))
        ImageDraw.Draw(bg).rectangle([W // 2, 0, W, H], fill=(48, 48, 50))
        pics = [src, Image.open(b_path).convert("RGB") if b_path and os.path.exists(b_path) else ImageOps.mirror(src)]
        r = int(min(W * 0.17, H * 0.27))
        for k, pic in enumerate(pics):
            disc = ImageOps.fit(pic, (r * 2, r * 2), Image.LANCZOS)
            m = Image.new("L", (r * 4, r * 4), 0)
            ImageDraw.Draw(m).ellipse([0, 0, r * 4, r * 4], fill=255)
            m = m.resize((r * 2, r * 2), Image.LANCZOS)
            cx, cy = (W // 4 if k == 0 else 3 * W // 4), H // 2
            ring = Image.new("RGBA", (r * 2 + 16, r * 2 + 16), (0, 0, 0, 0))
            ImageDraw.Draw(ring).ellipse([0, 0, r * 2 + 15, r * 2 + 15], fill=(240, 240, 236, 255))
            bg.paste(ring, (cx - r - 8, cy - r - 8), ring)
            bg.paste(disc, (cx - r, cy - r), m)
    bg.save(out, quality=93)
    return out
