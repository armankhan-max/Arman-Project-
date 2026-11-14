"""Thumbnail compositor: AI picture(s) + perfectly spelled bold text, optional host face, arrow or circle."""
import random

import skia

from .engine import core, gfx
from .engine.gfx import C, AA, text, text_w, rect, draw_cover, fill, linear, wrap, fit_size

W, H = 1280, 720


def _text_stack(c, s, x, y, maxw, size, accent_word, accent, align="left", box=None):
    words = s.split()
    lines = wrap(s, "Anton-Regular", size, maxw)
    while len(lines) > 3 and size > 60:
        size *= 0.9
        lines = wrap(s, "Anton-Regular", size, maxw)
    yy = y
    for ln in lines:
        lw = text_w(ln, "Anton-Regular", size)
        ox = x - (lw / 2 if align == "center" else lw if align == "right" else 0)
        if box:
            rect(c, ox - 18, yy - size * 0.92, lw + 36, size * 1.12, box)
        cx = ox
        for w in ln.split():
            col = accent if accent_word and w.strip(".,!?").upper() == accent_word.upper() else "#ffffff"
            if box and col == "#ffffff":
                col = "#ffffff"
            text(c, w, cx, yy, size, col, "Anton-Regular", stroke=None if box else "#000000", stroke_w=size * 0.16, shadow=0 if box else 14)
            cx += text_w(w + " ", "Anton-Regular", size) + size * 0.06
        yy += size * 1.1
    return yy


def compose(out, concept, bg_a, bg_b=None, face=None, accent="#ffd400", style=None):
    s = skia.Surface(W, H)
    c = s.getCanvas()
    c.clear(C("#000000"))
    pop = skia.Paint(ColorFilter=gfx.grade_filter(1.22, 1.12, (1.02, 1.0, 0.98), 0.0), AntiAlias=True)
    layout = concept.get("layout", "hero")
    A = gfx.load_image(bg_a, 1600) if bg_a else None
    txt = concept.get("text", "")
    aw = concept.get("accent_word", "")
    rnd = random.Random(core.seed_of(txt, out))
    if layout == "split" and bg_b and A is not None:
        B = gfx.load_image(bg_b, 1600)
        draw_cover(c, A, 0, 0, W / 2, H, 1.0, 0.5, 0.5, paint=skia.Paint(ColorFilter=gfx.grade_filter(0.55, 1.05, (1, 1, 1), -0.02), AntiAlias=True))
        if B is not None:
            draw_cover(c, B, W / 2, 0, W / 2, H, 1.0, 0.5, 0.5, paint=pop)
        rect(c, W / 2 - 5, 0, 10, H, "#ffffff")
        for lab, cx, col in ((concept.get("label_a") or "BEFORE", W * 0.25, "#e5383b"), (concept.get("label_b") or "AFTER", W * 0.75, "#2dc653")):
            lw = text_w(lab.upper(), "Anton-Regular", 64) + 50
            rect(c, cx - lw / 2, 28, lw, 86, col, r=8)
            text(c, lab.upper(), cx, 94, 64, "#ffffff", "Anton-Regular", "center")
        fill(c, linear(0, H * 0.55, 0, H, [C("#000000", 0), C("#000000", 0.85)]), 0, H * 0.55, W, H * 0.45)
        size = fit_size(txt, "Anton-Regular", W * 0.9, 150, 70)
        _text_stack(c, txt, W / 2, H - 50 - (len(wrap(txt, "Anton-Regular", size, W * 0.9)) - 1) * size * 1.1, W * 0.9, size, aw, accent, "center")
    else:
        if A is not None:
            draw_cover(c, A, 0, 0, W, H, 1.04, 0.5, 0.45, paint=pop)
        side_left = True
        if layout == "face" and face:
            F = gfx.load_image(face, 1600)
            if F is not None:
                fw = W * 0.44
                c.saveLayer(skia.Rect.MakeXYWH(W - fw, 0, fw, H), None)
                draw_cover(c, F, W - fw, 0, fw, H, 1.25, 0.5, 0.35, paint=pop)
                c.drawRect(skia.Rect.MakeXYWH(W - fw, 0, fw * 0.3, H), skia.Paint(Shader=linear(W - fw, 0, W - fw * 0.7, 0, [C("#000000", 1), C("#000000", 0)]),
                                                                              BlendMode=skia.BlendMode.kDstOut))
                c.restore()
        fill(c, linear(0, 0, W * 0.62, 0, [C("#000000", 0.82), C("#000000", 0.0)]), 0, 0, W * 0.62, H)
        fill(c, linear(0, H * 0.7, 0, H, [C("#000000", 0), C("#000000", 0.55)]), 0, H * 0.7, W, H * 0.3)
        box = accent if (style or {}).get("boxed") or rnd.random() < 0.3 else None
        size = 170
        lines = wrap(txt, "Anton-Regular", size, W * 0.52)
        while (len(lines) > 3 or any(text_w(l, "Anton-Regular", size) > W * 0.54 for l in lines)) and size > 70:
            size *= 0.92
            lines = wrap(txt, "Anton-Regular", size, W * 0.52)
        y0 = H / 2 - (len(lines) - 1) * size * 0.55 + size * 0.36
        yy = _text_stack(c, txt, 56, y0, W * 0.54, size, aw, "#ffffff" if box else accent, "left", box)
        hook = concept.get("hook", "none")
        if hook == "arrow":
            gfx.arrow(c, W * 0.34, min(H - 60, yy + 10), W * 0.66, H * 0.56, "#000000", 34, 1, 1, curve=90)
            gfx.arrow(c, W * 0.34, min(H - 60, yy + 10), W * 0.66, H * 0.56, "#e5383b", 22, 1, 1, curve=90)
        elif hook == "circle":
            gfx.arc(c, W * 0.74, H * 0.5, H * 0.24, -100, 372, "#000000", 22)
            gfx.arc(c, W * 0.74, H * 0.5, H * 0.24, -100, 372, "#e5383b", 13)
    fill(c, gfx.radial(W / 2, H / 2, W * 0.75, [C("#000000", 0), C("#000000", 0.35)]), 0, 0, W, H)
    s.makeImageSnapshot().save(out, skia.kPNG)
    return out


# ------------------------------------------------------------------ channel-style presets
STYLES = {
    "banner": "Red top banner with white headline over a real-looking scene; host on the left. Avatar and confession channels.",
    "clean": "One object on a plain cream backdrop with a huge black headline cropped at the top. Product, history and collector channels.",
    "boxed": "Bold cartoon illustration on white, black headline with one word in a red box, red arrow. Animal, baby and explainer channels.",
    "hero": "Dramatic full-frame photo with white outlined headline. Documentary and science channels.",
}
PROMPT_STYLE = {
    "banner": "Photorealistic scene, bright even lighting, saturated natural colors, the main object large on the right half, top quarter of the frame calm.",
    "clean": "Studio product photograph of the single object, three-quarter view, centred low in the frame on a seamless plain warm cream backdrop with a soft shadow, top third empty. Photorealistic.",
    "boxed": "Bold flat cartoon illustration with thick black outlines and bright flat colors on a pure white background, the subject on the right half, left half empty white. No shading gradients.",
    "hero": "Dramatic cinematic photograph, high contrast, the subject on the right, dark calm space on the left.",
}


def _arrow(c, x1, y1, x2, y2, curve=70, w=20):
    gfx.arrow(c, x1, y1, x2, y2, "#000000", w + 10, 1, 1, curve=curve)
    gfx.arrow(c, x1, y1, x2, y2, "#e3202a", w, 1, 1, curve=curve)


def compose_style(out, concept, img, face=None, style="hero", accent="#ffd400"):
    if style not in ("banner", "clean", "boxed"):
        return compose(out, dict(concept, layout="face" if face else "hero"), img, None, face, accent)
    s = skia.Surface(W, H)
    c = s.getCanvas()
    txt = "".join(ch if ord(ch) < 127 else ("-" if ch in "\u2010\u2011\u2012\u2013\u2014" else "'" if ch in "\u2018\u2019" else "") for ch in (concept.get("text") or "")).upper()
    aw = (concept.get("accent_word") or "").upper().strip(".,!?")
    pop = skia.Paint(ColorFilter=gfx.grade_filter(1.18, 1.08, (1.02, 1.0, 0.98), 0.0), AntiAlias=True)
    A = gfx.load_image(img, 1600)
    F = gfx.load_image(face, 1600) if face else None
    hook = concept.get("hook", "arrow")
    if style == "banner":
        c.clear(C("#000000"))
        if A is not None:
            draw_cover(c, A, 0, 0, W, H, 1.02, 0.5, 0.5, paint=pop)
        if F is not None:
            fw = W * 0.46
            c.saveLayer(skia.Rect.MakeXYWH(0, 0, fw, H), None)
            draw_cover(c, F, 0, 0, fw, H, 1.0, 0.5, 0.4, paint=pop)
            c.drawRect(skia.Rect.MakeXYWH(fw * 0.72, 0, fw * 0.28, H), skia.Paint(Shader=linear(fw * 0.72, 0, fw, 0, [C("#000000", 0), C("#000000", 1)]), BlendMode=skia.BlendMode.kDstOut))
            c.restore()
        bh = H * 0.2
        rect(c, 0, 0, W, bh, "#e3202a")
        size = fit_size(txt, "Anton-Regular", W - 60, bh * 0.82, 40)
        text(c, txt, W / 2, bh / 2 + size * 0.36, size, "#ffffff", "Anton-Regular", "center", stroke="#000000", stroke_w=size * 0.07)
        side = (concept.get("side_text") or "").upper()
        if side:
            lines = wrap(side, "Anton-Regular", 92, W * 0.3)[:4]
            for i, ln in enumerate(lines):
                text(c, ln, W - 40, bh + 130 + i * 98, 92, accent, "Anton-Regular", "right", stroke="#000000", stroke_w=14)
        if hook == "circle":
            gfx.arc(c, W * 0.7, H * 0.66, H * 0.16, -100, 372, "#e3202a", 14)
        if hook in ("arrow", "circle"):
            _arrow(c, W * 0.5, H * 0.34, W * 0.63, H * 0.56, curve=70)
    elif style == "clean":
        c.clear(C("#efe9dd"))
        if A is not None:
            draw_cover(c, A, 0, 0, W, H, 1.0, 0.5, 0.5, paint=pop)
        size = fit_size(txt, "Anton-Regular", W * 0.96, 330, 120)
        text(c, txt, W / 2, size * 0.74, size, "#111111", "Anton-Regular", "center")  # headline deliberately cropped by the top edge
        badge = (concept.get("side_text") or "").upper()
        if badge:
            text(c, badge, W - 40, H * 0.42, 84, "#7a1016", "Anton-Regular", "right")
    else:  # boxed
        c.clear(C("#ffffff"))
        if A is not None:
            draw_cover(c, A, 0, 0, W, H, 1.0, 0.5, 0.5)
        fill(c, linear(0, 0, W * 0.5, 0, [C("#ffffff", 0.96), C("#ffffff", 0)]), 0, 0, W * 0.5, H)
        words = txt.split()
        size = 150
        lines = wrap(txt, "Anton-Regular", size, W * 0.44)
        while (len(lines) > 3 or any(text_w(l, "Anton-Regular", size) > W * 0.46 for l in lines)) and size > 70:
            size *= 0.93
            lines = wrap(txt, "Anton-Regular", size, W * 0.44)
        y = H / 2 - (len(lines) - 1) * size * 0.58 + size * 0.36
        for ln in lines:
            has = aw and aw in [w.strip(".,!?") for w in ln.split()]
            lw = text_w(ln, "Anton-Regular", size)
            if has:
                rect(c, 44, y - size * 0.93, lw + 36, size * 1.12, "#e3202a")
                text(c, ln, 62, y, size, "#ffffff", "Anton-Regular")
            else:
                text(c, ln, 56, y, size, "#111111", "Anton-Regular")
            y += size * 1.16
        if hook != "none":
            _arrow(c, W * 0.44, 90, W * 0.62, H * 0.3, curve=-60, w=18)
        _ = words
    s.makeImageSnapshot().save(out, skia.kPNG)
    return out
