"""Thumbnail studio: reference research (what is working for a topic), style analysis of any reference,
AI-written concepts, and a compositor that renders clean 1280x720 thumbnails with perfectly spelled text."""
import json
import os
import random
import re

import skia
from PIL import Image

from . import core, gfx, llm, media
from .gfx import C, AA, text, text_w, rect, draw_cover, fill, linear, wrap, fit_size

W, H = 1280, 720


# ------------------------------------------------------------------ references
def video_id(url):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|vi/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else None


def _views(s):
    m = re.search(r"([\d.,]+)\s*([KMB]?)", (s or "").replace(" ", " "))
    if not m:
        return 0
    try:
        return int(float(m.group(1).replace(",", "")) * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9}[m.group(2)])
    except Exception:
        return 0


def references(topic, n=12):
    """Videos currently ranking for a topic, biggest first, as thumbnail references."""
    key = core.get_settings().get("youtube_key")
    out = []
    try:
        if key:
            j = core.fetch("https://www.googleapis.com/youtube/v3/search", params={"part": "snippet", "q": topic, "type": "video", "maxResults": 25,
                                                                                  "order": "viewCount", "key": key}, timeout=15).json()
            ids = [i["id"]["videoId"] for i in j.get("items", [])]
            st = core.fetch("https://www.googleapis.com/youtube/v3/videos", params={"part": "statistics,snippet", "id": ",".join(ids), "key": key}, timeout=15).json()
            for v in st.get("items", []):
                out.append({"id": v["id"], "title": v["snippet"]["title"], "channel": v["snippet"]["channelTitle"], "views": int(v["statistics"].get("viewCount", 0))})
        else:
            r = core.fetch("https://www.youtube.com/results", params={"search_query": topic, "hl": "en", "gl": "US"}, timeout=20,
                           headers={"Accept-Language": "en-US,en;q=0.9", "Cookie": "CONSENT=YES+1", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"})
            m = re.search(r"var ytInitialData = (\{.*?\});</script>", r.text, re.S)
            data = json.loads(m.group(1)) if m else {}

            def walk(o):
                if isinstance(o, dict):
                    if "videoRenderer" in o:
                        v = o["videoRenderer"]
                        try:
                            out.append({"id": v["videoId"], "title": v["title"]["runs"][0]["text"], "channel": v.get("ownerText", {}).get("runs", [{}])[0].get("text", ""),
                                        "views": _views(v.get("viewCountText", {}).get("simpleText", "")), "length": v.get("lengthText", {}).get("simpleText", "")})
                        except Exception:
                            pass
                    for x in o.values():
                        walk(x)
                elif isinstance(o, list):
                    for x in o:
                        walk(x)
            walk(data)
    except Exception:
        pass
    seen, uniq = set(), []
    for v in sorted(out, key=lambda v: -v.get("views", 0)):
        if v["id"] not in seen:
            seen.add(v["id"])
            v["thumb"] = "https://img.youtube.com/vi/%s/hqdefault.jpg" % v["id"]
            v["url"] = "https://www.youtube.com/watch?v=" + v["id"]
            uniq.append(v)
    return uniq[:n]


def from_url(url):
    vid = video_id(url)
    if not vid:
        return {"error": "Paste a YouTube video link."}
    info = {"id": vid, "url": url, "thumb": "https://img.youtube.com/vi/%s/hqdefault.jpg" % vid}
    try:
        j = core.fetch("https://www.youtube.com/oembed", params={"url": "https://www.youtube.com/watch?v=" + vid, "format": "json"}, timeout=15).json()
        info.update(title=j.get("title"), channel=j.get("author_name"))
    except Exception:
        pass
    return info


def analyze(ref):
    """Palette + layout hints from a reference thumbnail (used as inspiration, never copied)."""
    out = {"palette": [], "bright": 0.5}
    try:
        path = os.path.join(core.CACHE, "ref_%s.jpg" % ref["id"])
        if not os.path.exists(path):
            try:
                core.download("https://img.youtube.com/vi/%s/maxresdefault.jpg" % ref["id"], path, timeout=20)
            except Exception:
                core.download(ref["thumb"], path, timeout=20)
        with Image.open(path) as im:
            im = im.convert("RGB").resize((160, 90))
            q = im.quantize(6, method=Image.MEDIANCUT)
            pal = q.getpalette()[:18]
            counts = sorted(q.getcolors(), reverse=True)
            cols = []
            for cnt, idx in counts:
                r, g, b = pal[idx * 3:idx * 3 + 3]
                cols.append({"hex": "#%02x%02x%02x" % (r, g, b), "share": round(cnt / (160.0 * 90), 3), "sat": (max(r, g, b) - min(r, g, b)) / 255.0,
                             "lum": (0.299 * r + 0.587 * g + 0.114 * b) / 255.0})
            out["palette"] = cols
            out["bright"] = round(sum(c["lum"] * c["share"] for c in cols), 3)
            vivid = sorted([c for c in cols if c["sat"] > 0.35 and c["lum"] > 0.3], key=lambda c: -c["sat"])
            out["accent"] = vivid[0]["hex"] if vivid else "#ffd400"
            out["path"] = path
    except Exception:
        pass
    return out


def concepts(title, fmt="documentary", ref_title="", persona=None, n=4):
    sys = ("You design YouTube thumbnails that look like a professional editor made them: one clear subject, one hero object, 2 to 4 bold words. "
           "Never copy a reference; borrow only what makes it work.")
    user = """Video title: %s
Format: %s
%s%s
Give %d clearly different thumbnail concepts. Return JSON: {"concepts": [{"idea": "one line: what we see and why it gets clicked",
"text": "2-4 words in capitals that ADD to the title, never repeat it", "accent_word": "the one word of the text to color",
"layout": "hero" | "split" | "face",
"prompt": "detailed image description for the background picture: subject, action, setting, lighting, camera. Photoreal. Leave the %s third of the frame calm for text. No text in the image.",
"prompt_b": "for split layout only: the 'after' or 'other side' image", "label_a": "split only, 1 word", "label_b": "split only, 1 word",
"hook": "arrow" | "circle" | "none"}]}
Layouts: hero = one dramatic full-frame image; split = before/after or A-vs-B; face = a person reacting on one side, object on the other.""" % (
        title, fmt, ("Reference that is working in this niche (inspiration only): \"%s\"\n" % ref_title) if ref_title else "",
        ("The host looks like: %s\n" % persona.get("look", "")) if persona else "", n, "left")
    try:
        j = llm.chat_json(sys, user, max_tokens=1800, temperature=0.9)
        arr = [c for c in (j.get("concepts") if isinstance(j, dict) else j) or [] if isinstance(c, dict) and c.get("prompt")]
    except Exception:
        arr = []
    if not arr:
        arr = [{"idea": "Dramatic hero image with a bold question", "text": "NOBODY NOTICED", "accent_word": "NOBODY", "layout": "hero",
                "prompt": "dramatic cinematic scene illustrating: %s. Subject on the right, dark calm space on the left" % title, "hook": "circle"}]
    for c in arr:
        c["text"] = str(c.get("text") or "")[:32].upper()
        c["layout"] = c.get("layout") if c.get("layout") in ("hero", "split", "face") else "hero"
    return arr[:n]


# ------------------------------------------------------------------ compositor
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


def generate(concept, folder, name, face=None, accent=None, seed=1, style="photo"):
    os.makedirs(folder, exist_ok=True)
    a = os.path.join(folder, name + "_a.jpg")
    media.ai_image(concept["prompt"] + " Bold, high-contrast, saturated, striking composition, sharp focus", a, 1280, 720, seed, style)
    b = None
    if concept.get("layout") == "split" and concept.get("prompt_b"):
        b = os.path.join(folder, name + "_b.jpg")
        try:
            media.ai_image(concept["prompt_b"] + " Bold, high-contrast, saturated, sharp focus", b, 1280, 720, seed + 1, style)
        except Exception:
            b = None
    out = os.path.join(folder, name + ".png")
    compose(out, concept, a, b, face, accent or "#ffd400")
    return out


def for_project(p):
    """Thumbnail for a finished project, following the reference/concept picked in the wizard."""
    tc = p.get("thumb_choice") or {}
    ref = tc.get("ref") or {}
    accent = None
    if ref.get("id"):
        accent = analyze(ref).get("accent")
    concept = tc.get("concept")
    if not concept:
        texts = (p.get("pack") or {}).get("thumbnail_texts") or []
        cs = concepts(p["title"], p["settings"]["format"], ref.get("title", ""), p.get("persona") if p["settings"]["format"] == "avatar" else None, 3)
        concept = cs[0]
        if tc.get("text"):
            concept["text"] = tc["text"].upper()
        elif texts and not concept.get("text"):
            concept["text"] = texts[0].upper()
        p["thumb_concepts"] = cs
    face = (p.get("avatar") or {}).get("image") if p["settings"]["format"] == "avatar" else None
    if face:
        concept["layout"] = "face"
    out = generate(concept, os.path.join(p["dir"], "thumbs"), "thumb_%s" % core.uid(5), face, accent, p["seed"],
                   media.FORMAT_AI.get(p["settings"]["format"], "photo") if p["settings"]["format"] != "anim2d" else "photo")
    p.setdefault("outputs", {})["thumbnail"] = out
    p["outputs"].setdefault("thumbnails", []).append(out)
    return out
