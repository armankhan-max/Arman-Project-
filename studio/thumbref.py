"""Thumbnail references: find outlier videos on a topic (official YouTube Data API), or take any
custom URL, then design ORIGINAL thumbnails inspired by the reference's mood, colours and layout
(never a copy of the reference picture or its words)."""
import base64
import colorsys
import datetime as dt
import io
import json
import os
import re

import requests
from PIL import Image

import llm
import media
import thumb

YT = "https://www.googleapis.com/youtube/v3"


def video_id(url):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|/vi/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else None


def outliers(topic, key, n=12):
    """Videos on the topic from the last 12 months whose views beat their channel's subscribers."""
    if not key:
        raise RuntimeError("Add a free YouTube Data API key in the Owner panel to see outliers. Custom URL works without it.")
    after = (dt.datetime.utcnow() - dt.timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    s = requests.get(YT + "/search", timeout=30, params={"part": "snippet", "q": topic, "type": "video", "maxResults": 40,
                                                          "order": "viewCount", "publishedAfter": after, "key": key})
    s.raise_for_status()
    items = s.json().get("items", [])
    ids = [i["id"]["videoId"] for i in items]
    if not ids:
        return []
    v = requests.get(YT + "/videos", timeout=30, params={"part": "statistics,snippet", "id": ",".join(ids), "key": key}).json()
    chans = list({x["snippet"]["channelId"] for x in v.get("items", [])})
    subs = {}
    for k in range(0, len(chans), 50):
        c = requests.get(YT + "/channels", timeout=30, params={"part": "statistics", "id": ",".join(chans[k:k + 50]), "key": key}).json()
        for ch in c.get("items", []):
            subs[ch["id"]] = int(ch["statistics"].get("subscriberCount") or 0)
    out = []
    for x in v.get("items", []):
        views = int(x["statistics"].get("viewCount") or 0)
        sc = subs.get(x["snippet"]["channelId"], 0)
        th = x["snippet"]["thumbnails"]
        out.append({"id": x["id"], "title": x["snippet"]["title"], "channel": x["snippet"]["channelTitle"], "views": views,
                    "subs": sc, "score": round(views / max(sc, 1000), 1),
                    "thumb": (th.get("maxres") or th.get("high") or th.get("medium") or {}).get("url", "")})
    return sorted(out, key=lambda x: -x["score"])[:n]


def fetch_reference(url, path):
    vid = video_id(url)
    cands = [f"https://i.ytimg.com/vi/{vid}/{q}.jpg" for q in ("maxresdefault", "hqdefault")] if vid else [url]
    last = None
    for u in cands:
        try:
            r = requests.get(u, timeout=30, headers=media.UA)
            r.raise_for_status()
            im = Image.open(io.BytesIO(r.content)).convert("RGB")
            if im.width < 200:
                continue
            im.save(path, quality=92)
            return path
        except Exception as e:
            last = e
    raise RuntimeError(f"Could not load that reference ({last})")


def _color_word(rgb):
    r, g, b = [c / 255 for c in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if l < 0.15:
        return "near-black"
    if s < 0.18:
        return "grey" if l < 0.7 else "white"
    names = [(15, "red"), (40, "orange"), (65, "yellow"), (160, "green"), (195, "teal"), (250, "deep blue"), (290, "purple"), (335, "pink"), (360, "red")]
    hue = h * 360
    word = next(n for lim, n in names if hue <= lim)
    return ("dark " if l < 0.35 else "bright " if l > 0.65 else "") + word


def analyse(path, cfg=None):
    """Mood words, palette and an accent colour from the reference (Claude vision adds a richer brief if a key is set)."""
    im = Image.open(path).convert("RGB").resize((160, 90))
    pal = im.quantize(6).getpalette()[:18]
    counts = sorted(im.quantize(6).getcolors(), reverse=True)
    cols = [tuple(pal[i * 3:i * 3 + 3]) for _, i in counts]
    lum = sum(sum(c) for c in cols[:3]) / (3 * 765)
    sat = max(cols, key=lambda c: colorsys.rgb_to_hls(*[x / 255 for x in c])[2] * (0.3 < sum(c) / 765 < 0.95))
    hh, ll, ss = colorsys.rgb_to_hls(*[x / 255 for x in sat])
    sat = tuple(int(v * 255) for v in colorsys.hls_to_rgb(hh, max(ll, 0.55), max(ss, 0.65)))  # readable accent
    info = {"palette": ["#%02x%02x%02x" % c for c in cols], "accent": "#%02x%02x%02x" % sat,
            "mood": ("dark, moody, low-key" if lum < 0.3 else "bright, high-key" if lum > 0.6 else "balanced, cinematic"),
            "colors": ", ".join(dict.fromkeys(_color_word(c) for c in cols[:3])), "brief": ""}
    if cfg and cfg.get("anthropic_key"):
        try:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            r = requests.post("https://api.anthropic.com/v1/messages", timeout=120, headers={
                "x-api-key": cfg["anthropic_key"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": cfg.get("anthropic_model") or "claude-sonnet-5-5", "max_tokens": 400, "messages": [{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                    {"type": "text", "text": "Describe only the STYLE of this YouTube thumbnail in one short paragraph: composition, camera angle, "
                                             "lighting, colour grade, where the text sits and its font style. Do not describe its exact subject or "
                                             "repeat its words, because we will make an original thumbnail inspired by the style."}]}]})
            if r.status_code == 200:
                info["brief"] = "".join(b.get("text", "") for b in r.json().get("content", []))[:600]
        except Exception:
            pass
    return info


def make_variants(cfg, title, topic_text, ref_path, outdir, thumb_text=None, subject=None, style_suffix=""):
    """Three different original thumbnails inspired by the reference. Returns list of file paths."""
    info = analyse(ref_path, cfg) if ref_path else {"mood": "cinematic", "colors": "", "accent": "#FFD400", "brief": ""}
    text = (thumb_text or " ".join(title.split()[:3])).strip()
    base = f"{topic_text}, {info['mood']} lighting, {info['colors']} colour palette, " + (info["brief"] + ", " if info["brief"] else "")
    prompts = [
        base + "epic wide establishing shot, huge sense of scale, empty space at the bottom for a title, " + style_suffix,
        base + "dramatic close-up of the single most striking detail, shallow depth of field, " + style_suffix,
        base + "mysterious subject small in a vast environment, strong light source, " + style_suffix,
    ]
    layouts = [("bottom", True, "documentary"), ("center", False, ""), ("left" if subject else "bottom", False, "")]
    out = []
    for k, (pr, (lay, serif, badge)) in enumerate(zip(prompts, layouts)):
        bg = os.path.join(outdir, f"thumb_bg{k}.jpg")
        try:
            media.ai_image(pr + ", no text, no logo", bg, 1280, 720, 4242 + k)
        except Exception:
            bg = None
        o = os.path.join(outdir, f"thumb_{k + 1}.jpg")
        accent = info["accent"] if k != 1 else "#FFD400"
        thumb.make(o, text, bg, subject if lay == "left" else None, lay, accent, True, badge=badge, serif=serif)
        out.append(o)
    return out, info
