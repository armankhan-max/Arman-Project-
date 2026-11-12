"""Thumbnail generator: background + optional host/subject picture + big bold text + arrow."""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

import store


def _font(size, text=""):
    devanagari = any("ऀ" <= ch <= "ॿ" for ch in text)
    names = (["FreeSansBold.ttf"] if devanagari else []) + ["Inter-ExtraBold.otf", "FreeSansBold.ttf"]
    for n in names:
        try:
            return ImageFont.truetype(os.path.join(store.FONTS, n), size)
        except Exception:
            pass
    return ImageFont.load_default()


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _wrap(text, max_lines=3):
    words = text.split()
    if len(words) <= 2:
        return words or [""]
    lines = min(max_lines, max(2, round(len(words) / 2)))
    per = -(-len(words) // lines)
    return [" ".join(words[i:i + per]) for i in range(0, len(words), per)]


def make(out, text, bg=None, subject=None, layout="left", accent="#FFD400", arrow=True, size=(1280, 720), badge="", serif=False):
    if layout == "bottom":
        return make_cinematic(out, text, bg, accent, badge, serif, size)
    W, H = size
    if bg and os.path.exists(bg):
        img = ImageOps.fit(Image.open(bg).convert("RGB"), size, Image.LANCZOS)
    else:
        import media
        tmp = out + ".bg.jpg"
        img = Image.open(media.procedural(tmp, W, H, abs(hash(text)) % 9999, accent)).convert("RGB")
        os.remove(tmp)
    img = img.filter(ImageFilter.GaussianBlur(2 if subject else 0))
    img = Image.eval(img, lambda v: int(v * 0.82))
    text_left = layout != "right"
    centered = layout == "center" or not subject
    # darken the text side so words pop
    if not centered:
        grad = Image.linear_gradient("L").rotate(90 if text_left else -90, expand=True).resize(size)
        shade = Image.new("RGB", size, (0, 0, 0))
        img = Image.composite(img, shade, grad.point(lambda v: int(90 + v * 0.65)))
    else:
        img = Image.eval(img, lambda v: int(v * 0.75))
    img = img.convert("RGBA")

    if subject and os.path.exists(subject):
        sub = Image.open(subject).convert("RGBA")
        sw = int(W * 0.46)
        if sub.getextrema()[3][0] < 250:  # real cut-out with transparency
            sub = ImageOps.contain(sub, (sw, int(H * 0.98)), Image.LANCZOS)
            pos = (W - sub.width - int(W * 0.02) if text_left else int(W * 0.02), H - sub.height)
            glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
            glow.paste((255, 255, 255, 255), pos, sub.split()[3])
            glow = glow.filter(ImageFilter.MaxFilter(13))
            img = Image.alpha_composite(img, glow)
            img.alpha_composite(sub, pos)
        else:  # normal photo: a clean framed panel
            sub = ImageOps.fit(sub.convert("RGB"), (sw, int(H * 0.86)), Image.LANCZOS, centering=(0.5, 0.3))
            framed = ImageOps.expand(sub, border=8, fill="white")
            pos = (W - framed.width - int(W * 0.035) if text_left else int(W * 0.035), (H - framed.height) // 2)
            sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(sh).rectangle([pos[0] + 14, pos[1] + 16, pos[0] + framed.width + 14, pos[1] + framed.height + 16], fill=(0, 0, 0, 150))
            img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(14)))
            img.paste(framed, pos)

    d = ImageDraw.Draw(img)
    lines = _wrap(text.upper())
    box_w = int(W * (0.88 if centered else 0.47))
    box_h = int(H * (0.8 if centered else 0.7))
    fs = 300
    while fs > 40:
        f = _font(fs, text)
        if max(d.textlength(l, font=f) for l in lines) <= box_w and fs * 1.08 * len(lines) <= box_h:
            break
        fs -= 6
    f = _font(fs, text)
    lh = int(fs * 1.08)
    y = (H - lh * len(lines)) // 2 - int(fs * 0.08)
    x0 = int(W * 0.045) if text_left else int(W * 0.5)
    for i, l in enumerate(lines):
        tw = d.textlength(l, font=f)
        x = (W - tw) // 2 if centered else x0
        col = _rgb(accent) if i == len(lines) - 1 and len(lines) > 1 else (255, 255, 255)
        d.text((x, y + i * lh), l, font=f, fill=col, stroke_width=max(6, fs // 11), stroke_fill=(0, 0, 0))
    if arrow and subject and not centered:
        ay = min(H - 70, y + lh * len(lines) + 55)
        a0, a1 = (int(W * 0.12), int(W * 0.47)) if text_left else (int(W * 0.88), int(W * 0.53))
        s = 1 if text_left else -1
        for wdt, col in ((34, (0, 0, 0)), (20, (230, 30, 40))):
            hd = 30 + wdt
            d.line([a0, ay, a1 - s * hd // 2, ay], fill=col, width=wdt)
            d.polygon([(a1 + s * (wdt // 4), ay), (a1 - s * hd, ay - hd * 0.8), (a1 - s * hd, ay + hd * 0.8)], fill=col)
    img.convert("RGB").save(out, quality=93)
    return out


def make_cinematic(out, text, bg, accent="#FFD400", badge="", serif=False, size=(1280, 720)):
    """Documentary look: full-bleed picture, dark fade at the bottom, small badge, huge title bottom-left."""
    W, H = size
    if bg and os.path.exists(bg):
        img = ImageOps.fit(Image.open(bg).convert("RGB"), size, Image.LANCZOS)
    else:
        import media
        tmp = out + ".bg.jpg"
        img = Image.open(media.procedural(tmp, W, H, abs(hash(text)) % 9999, accent)).convert("RGB")
        os.remove(tmp)
    grad = Image.linear_gradient("L").resize(size).point(lambda v: int(max(0, v - 90) * 1.5))
    img = Image.composite(Image.new("RGB", size, (0, 0, 0)), img, grad).convert("RGBA")
    d = ImageDraw.Draw(img)
    fname = "DejaVuSerif-Bold.ttf" if serif else None
    lines = _wrap(text.upper(), 2)
    fs = 260
    while fs > 40:
        f = ImageFont.truetype(os.path.join(store.FONTS, fname), fs) if fname else _font(fs, text)
        if max(d.textlength(l, font=f) for l in lines) <= W * 0.9 and fs * 1.05 * len(lines) <= H * 0.42:
            break
        fs -= 6
    lh = int(fs * 1.08)
    y = H - int(H * 0.1) - lh * len(lines)
    x = int(W * 0.045)
    if badge:
        fb = _font(int(H * 0.05))
        bw = d.textlength(badge.upper(), font=fb)
        by = y - int(H * 0.085)
        d.rectangle([x, by, x + bw + 26, by + int(H * 0.068)], fill=_rgb(accent))
        d.text((x + 13, by + int(H * 0.006)), badge.upper(), font=fb, fill=(10, 10, 10))
    for i, l in enumerate(lines):
        d.text((x, y + i * lh), l, font=f, fill=(255, 255, 255), stroke_width=max(2, fs // 40), stroke_fill=(0, 0, 0))
    img.convert("RGB").save(out, quality=93)
    return out
