"""Visual sourcing. Every provider returns the same candidate shape so the editor can swap freely.

Free, watermark-free sources:
  stock video  : Pexels, Pixabay (free API keys), Wikimedia Commons video (no key)
  real photos  : Pexels, Pixabay, Wikimedia Commons, NASA, Openverse (public domain / CC0)
  AI images    : Pollinations (no key) or OpenAI images (key)
"""
import os
import re
import threading
import time
import urllib.parse

from PIL import Image

from . import core

_ai_gate = threading.Semaphore(2)
BAD_TITLE = re.compile(r"logo|icon|flag of|coat of arms|diagram|map of|\.svg|\.pdf|\.djvu|signature|stamp|banner|chart|seal of", re.I)


def cand(kind, url, thumb, src, credit, w=0, h=0, dur=0, title="", cid=None):
    return {"kind": kind, "url": url, "thumb": thumb or url, "src": src, "credit": credit, "w": w, "h": h, "dur": dur,
            "title": title, "id": cid or core.h(url, 12)}


# ------------------------------------------------------------------ providers
def pexels_videos(q, n=8, portrait=False):
    key = core.get_settings().get("pexels_key")
    if not key:
        return []
    j = core.fetch("https://api.pexels.com/videos/search", headers={"Authorization": key}, timeout=20,
                   params={"query": q, "per_page": n, "orientation": "portrait" if portrait else "landscape"}).json()
    out = []
    for v in j.get("videos", []):
        files = sorted([f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4" and f.get("width")],
                       key=lambda f: abs((f.get("height") if not portrait else f.get("width")) - 1080))
        if files:
            f = files[0]
            out.append(cand("video", f["link"], v.get("image"), "pexels", "Video: %s / Pexels" % (v.get("user") or {}).get("name", "Pexels"),
                            f["width"], f["height"], v.get("duration", 0), q, "pxv%s" % v["id"]))
    return out


def pexels_photos(q, n=8, portrait=False):
    key = core.get_settings().get("pexels_key")
    if not key:
        return []
    j = core.fetch("https://api.pexels.com/v1/search", headers={"Authorization": key}, timeout=20,
                   params={"query": q, "per_page": n, "orientation": "portrait" if portrait else "landscape"}).json()
    return [cand("image", p["src"]["large2x"], p["src"]["medium"], "pexels", "Photo: %s / Pexels" % p.get("photographer", "Pexels"),
                 p.get("width", 0), p.get("height", 0), 0, p.get("alt") or q, "pxp%s" % p["id"]) for p in j.get("photos", [])]


def pixabay_videos(q, n=8, portrait=False):
    key = core.get_settings().get("pixabay_key")
    if not key:
        return []
    j = core.fetch("https://pixabay.com/api/videos/", timeout=20, params={"key": key, "q": q[:95], "per_page": max(3, n), "safesearch": "true"}).json()
    out = []
    for v in j.get("hits", []):
        vs = v.get("videos") or {}
        f = vs.get("large") or vs.get("medium") or vs.get("small") or {}
        if f.get("height", 0) > 1200:
            f = vs.get("medium") or f
        if f.get("url"):
            out.append(cand("video", f["url"], f.get("thumbnail") or (vs.get("tiny") or {}).get("thumbnail"), "pixabay",
                            "Video: %s / Pixabay" % v.get("user", "Pixabay"), f.get("width", 0), f.get("height", 0), v.get("duration", 0), v.get("tags", q), "pbv%s" % v["id"]))
    return out


def pixabay_photos(q, n=8, portrait=False):
    key = core.get_settings().get("pixabay_key")
    if not key:
        return []
    j = core.fetch("https://pixabay.com/api/", timeout=20, params={"key": key, "q": q[:95], "per_page": max(3, n), "image_type": "photo", "safesearch": "true",
                                                                 "orientation": "vertical" if portrait else "horizontal"}).json()
    return [cand("image", p["largeImageURL"], p.get("webformatURL"), "pixabay", "Photo: %s / Pixabay" % p.get("user", "Pixabay"),
                 p.get("imageWidth", 0), p.get("imageHeight", 0), 0, p.get("tags", q), "pbp%s" % p["id"]) for p in j.get("hits", [])]


def _commons(q, n, video=False):
    params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": min(30, n * 3),
              "gsrsearch": "%s filetype:%s" % (q, "video" if video else "bitmap"),
              "prop": "imageinfo" if not video else "videoinfo", ("iiprop" if not video else "viprop"): "url|size|mime|extmetadata" + ("|derivatives" if video else ""),
              ("iiurlwidth" if not video else "viurlwidth"): 1920}
    j = core.fetch("https://commons.wikimedia.org/w/api.php", params=params, timeout=20).json()
    pages = sorted(((j.get("query") or {}).get("pages") or {}).values(), key=lambda p: p.get("index", 99))
    out = []
    for p in pages:
        title = p.get("title", "")
        ii = (p.get("videoinfo") or p.get("imageinfo") or [{}])[0]
        w, hh = ii.get("width", 0), ii.get("height", 0)
        if not ii.get("url") or BAD_TITLE.search(title) or w < 640 or not hh:
            continue
        ar = w / float(hh)
        md = ii.get("extmetadata") or {}
        artist = re.sub(r"<[^>]+>", "", (md.get("Artist") or {}).get("value", "")).strip()[:60] or "Wikimedia Commons"
        lic = (md.get("LicenseShortName") or {}).get("value", "")
        credit = "%s: %s (%s) / Wikimedia Commons" % ("Video" if video else "Photo", artist, lic or "free licence")
        if video:
            dur = float(ii.get("duration") or 0)
            if dur < 3 or ar < 1.2 or ii.get("size", 0) > 150e6:
                continue
            url = ii["url"]
            for d in ii.get("derivatives") or []:  # prefer a 720p/1080p transcode over a giant original
                if d.get("type", "").startswith("video/webm") and str(d.get("transcodekey", "")).startswith(("720p", "1080p")):
                    url = d["src"]
            out.append(cand("video", url, ii.get("thumburl"), "commons", credit, w, hh, dur, title[5:], "cmv%s" % p["pageid"]))
        else:
            if not (0.55 < ar < 2.7) or ii.get("mime") not in ("image/jpeg", "image/png", "image/tiff", "image/webp"):
                continue
            c = cand("image", ii.get("thumburl") or ii["url"], ii.get("thumburl") or ii["url"], "commons", credit, w, hh, 0, title[5:], "cmp%s" % p["pageid"])
            c["alt_url"] = ii["url"]
            out.append(c)
        if len(out) >= n:
            break
    return out


def commons_photos(q, n=8, portrait=False):
    return _commons(q, n, False)


def commons_videos(q, n=6, portrait=False):
    return _commons(q, n, True)


def nasa_photos(q, n=6, portrait=False):
    j = core.fetch("https://images-api.nasa.gov/search", params={"q": q, "media_type": "image"}, timeout=15, retries=0).json()
    out = []
    for it in (j.get("collection") or {}).get("items", [])[:n]:
        d = (it.get("data") or [{}])[0]
        l = (it.get("links") or [{}])[0].get("href")
        if l:
            out.append(cand("image", l.replace("~thumb", "~large"), l, "nasa", "Image: NASA", 0, 0, 0, d.get("title", q), "nasa" + d.get("nasa_id", core.h(l))))
    return out


def openverse_photos(q, n=6, portrait=False):
    j = core.fetch("https://api.openverse.org/v1/images/", params={"q": q, "page_size": n, "license": "cc0,pdm", "aspect_ratio": "tall" if portrait else "wide"},
                   timeout=15, retries=0).json()
    return [cand("image", r["url"], r.get("thumbnail") or r["url"], "openverse", "Image: %s (%s) / Openverse" % (r.get("creator") or "unknown", r.get("license", "pd")),
                 r.get("width", 0), r.get("height", 0), 0, r.get("title", q), "ov" + r["id"][:10]) for r in j.get("results", [])]


PROVIDERS = {
    "stock_video": [pexels_videos, pixabay_videos, commons_videos],
    "stock_photo": [pexels_photos, pixabay_photos],
    "archive": [commons_photos, nasa_photos, openverse_photos],
}
_search_cache = {}


def search(q, group, n=8, portrait=False):
    """group: stock_video | stock_photo | archive. Never raises."""
    key = (q.lower(), group, portrait)
    if key in _search_cache:
        return _search_cache[key]
    out = []
    for fn in PROVIDERS.get(group, []):
        try:
            out += fn(q, n, portrait)
        except Exception:
            continue
        if len(out) >= n:
            break
    _search_cache[key] = out
    return out


# ------------------------------------------------------------------ AI images
AI_STYLES = {
    "photo": "cinematic documentary photograph, photorealistic, natural light, 35mm lens, shallow depth of field, rich detail, looks like premium stock photography",
    "archive": "authentic vintage press photograph, period-accurate, film grain, slightly faded, documentary realism",
    "home": "candid smartphone photo in a real lived-in home, soft window daylight, natural colors, slightly imperfect framing, photorealistic, looks like a frame from a phone video",
    "flat2d": "flat 2D vector illustration background, simple bold shapes, dark navy palette with warm rim light, cinematic, empty scene with no people and no characters",
    "kids": "bright friendly children's picture-book illustration, soft shapes, warm colors, simple background",
    "dark": "moody low-key cinematic still, deep shadows, cold desaturated color, fog, unsettling atmosphere, photorealistic",
    "tech": "sleek futuristic photograph, dark studio, neon cyan and magenta rim light, glossy reflections, photorealistic, premium product look",
    "paper": "real photograph, neutral daylight, documentary evidence photo, sharp detail",
    "nature": "National-Geographic style wildlife and landscape photograph, golden hour light, telephoto lens, photorealistic, breathtaking detail",
}
FORMAT_AI = {"avatar": "home", "anim2d": "flat2d", "kids": "kids", "mystery": "dark", "tech": "tech", "news": "photo", "history": "archive",
             "biography": "archive", "nature": "nature", "casestudy": "paper", "whatif": "flat2d"}


def ai_image(prompt, dest, w=1280, h=720, seed=1, style="photo", block=""):
    s = core.get_settings()
    full = "%s. %s. No text, no captions, no watermark, no logo%s." % (prompt.strip().rstrip("."), AI_STYLES.get(style, style),
                                                                     (", no " + block) if block else "")
    if s.get("image_provider") == "openai" and s.get("openai_key"):
        r = core.http().post("https://api.openai.com/v1/images/generations", timeout=180,
                             headers={"authorization": "Bearer " + s["openai_key"]},
                             json={"model": "gpt-image-1", "prompt": full, "size": "1536x1024" if w >= h else "1024x1536", "quality": "medium"})
        if r.status_code == 200:
            import base64
            with open(dest, "wb") as f:
                f.write(base64.b64decode(r.json()["data"][0]["b64_json"]))
            return dest
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(full[:900], safe="")
    params = "?width=%d&height=%d&seed=%d&nologo=true&model=%s" % (w, h, seed % 999983, s.get("image_model") or "flux")
    last = None
    with _ai_gate:
        for i in range(5):
            try:
                core.download(url + params, dest, timeout=150)
                with Image.open(dest) as im:
                    im.verify()
                return dest
            except Exception as e:
                last = e
                time.sleep(3 + 4 * i)
    raise RuntimeError("AI image failed: %s" % last)


# ------------------------------------------------------------------ obtain
def obtain(c, folder):
    """Download a candidate and normalise it. Returns asset dict or raises."""
    os.makedirs(folder, exist_ok=True)
    if c["kind"] == "video":
        ext = ".webm" if ".webm" in c["url"] else ".mp4"
        dest = os.path.join(folder, c["id"] + ext)
        if not os.path.exists(dest):
            core.download(c["url"], dest, timeout=180, max_mb=160)
        d = core.media_duration(dest)
        if d < 2:
            os.remove(dest)
            raise RuntimeError("bad video")
        return {"kind": "video", "path": dest, "src": c["src"], "credit": c["credit"], "thumb": c.get("thumb"), "dur": d, "id": c["id"], "title": c.get("title", "")}
    dest = os.path.join(folder, c["id"] + ".jpg")
    if not os.path.exists(dest):
        raw = dest + ".raw"
        urls = [c["url"]] + ([c["alt_url"]] if c.get("alt_url") else [])
        if "thumb.wikimedia.org" in c["url"]:
            urls.insert(1, c["url"].split("?")[0].replace("thumb.wikimedia.org", "upload.wikimedia.org"))
        err = None
        for u in urls:
            try:
                core.download(u, raw, timeout=90, max_mb=60)
                err = None
                break
            except Exception as e:
                err = e
        if err:
            raise err
        normalise_image(raw, dest)
        os.remove(raw)
    return {"kind": "image", "path": dest, "src": c["src"], "credit": c["credit"], "thumb": c.get("thumb"), "id": c["id"], "title": c.get("title", "")}


def normalise_image(src, dest, max_side=2560):
    Image.MAX_IMAGE_PIXELS = 300_000_000
    with Image.open(src) as im:
        im = im.convert("RGB")
        if max(im.size) > max_side:
            im.thumbnail((max_side, max_side), Image.LANCZOS)
        if min(im.size) < 360:
            raise RuntimeError("image too small")
        im.save(dest, "JPEG", quality=92)
    return dest


def pick(plan, variant, st, used, folder, seed, portrait=False):
    """Choose and fetch the visual for one shot. `used` is the set of asset ids already in the video
    (no picture is ever repeated). Falls back down the chain until something works; returns None only
    if every source failed, in which case the renderer draws a designed backdrop."""
    src = st.get("sources") or {}
    fmt = st["format"]
    style = st.get("ai_style") or FORMAT_AI.get(fmt, "photo")
    q = plan["query"] if variant == 0 else (plan.get("query2") or plan["query"])
    order = {"stock": ["stock_video", "stock_photo", "archive", "ai"], "archive": ["archive", "stock_photo", "ai", "stock_video"],
             "ai": ["ai", "stock_video", "stock_photo", "archive"], "mg": ["ai", "stock_photo", "archive"]}[plan.get("kind", "ai")]
    if fmt in ("anim2d", "kids"):
        order = ["ai"]
    if variant % 2 == 1 and plan.get("kind") == "stock":
        order = ["stock_photo", "stock_video", "archive", "ai"]
    blocked = [b.strip().lower() for b in (st.get("blocklist") or "").split(",") if b.strip()]
    for group in order:
        if not src.get(group, True):
            continue
        if group == "ai":
            pid = "ai" + core.h("%s|%s|%s|%s" % (plan["prompt"], variant, seed, style), 12)
            dest = os.path.join(folder, pid + ".jpg")
            try:
                if not os.path.exists(dest):
                    angle = ["", " Wide establishing shot.", " Close-up detail shot.", " Low angle, dramatic.", " Over-the-shoulder view."][variant % 5]
                    w, h = (720, 1280) if portrait else (1280, 720)
                    ai_image(plan["prompt"] + angle, dest, w, h, seed + variant * 31, "archive" if plan.get("kind") == "archive" and style == "photo" else style, ", ".join(blocked))
                    normalise_image(dest, dest)
                used.add(pid)
                return {"kind": "image", "path": dest, "src": "ai", "credit": "", "id": pid, "prompt": plan["prompt"], "query": q, "title": "AI image"}
            except Exception:
                continue
        try:
            cands = search(q, group, 8, portrait)
        except Exception:
            cands = []
        for c in cands:
            if c["id"] in used or any(b in (c.get("title") or "").lower() for b in blocked):
                continue
            try:
                used.add(c["id"])
                a = obtain(c, folder)
                a.update(query=q, prompt=plan["prompt"])
                return a
            except Exception:
                continue
    return None


def alternatives(q, prompt, portrait=False):
    """Candidates for the editor's 'replace visual' panel."""
    out = []
    for g in ("stock_video", "stock_photo", "archive"):
        out += search(q, g, 8, portrait)
    return out
