"""B-roll finder: free stock video/photos, AI images, and a built-in generated fallback."""
import hashlib
import os
import random
import threading
import time
import re
import urllib.parse

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFilter

UA = {"User-Agent": "AIVideoStudio/1.1 (self-hosted video maker; python-requests)"}
_locks = {"commons": threading.Lock(), "ai": threading.Lock()}
_last = {"commons": 0.0, "ai": 0.0}


def _throttle(name, gap):
    """Free services allow few requests per second; space them out politely."""
    with _locks[name]:
        wait = _last[name] + gap - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[name] = time.time()
_cache = {}


def _get(url, **kw):
    r = requests.get(url, timeout=kw.pop("timeout", 40), headers={**UA, **kw.pop("headers", {})}, **kw)
    r.raise_for_status()
    return r


def _download(url, path, max_mb=80):
    with requests.get(url, timeout=90, headers=UA, stream=True) as r:
        r.raise_for_status()
        size = 0
        with open(path, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                size += len(chunk)
                if size > max_mb << 20:
                    raise RuntimeError("file too large")
                f.write(chunk)
    if os.path.getsize(path) < 2000:
        raise RuntimeError("empty download")
    return path


_cool = {}


def _search(kind, query, cfg, portrait):
    """Returns a list of {url, credit} for one provider + query (cached)."""
    key = (kind, query, portrait)
    if key in _cache:
        return _cache[key]
    if _cool.get(kind, 0) > time.time():
        return []
    try:
        return _search_inner(kind, query, cfg, portrait, key)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            _cool[kind] = time.time() + 90  # back off instead of hammering a free service
        raise


def _search_inner(kind, query, cfg, portrait, key):
    orient = "portrait" if portrait else "landscape"
    out = []
    if kind == "pexels_video" and cfg.get("pexels_key"):
        j = _get("https://api.pexels.com/videos/search", headers={"Authorization": cfg["pexels_key"]},
                 params={"query": query, "per_page": 15, "orientation": orient}).json()
        for v in j.get("videos", []):
            files = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4" and f.get("width")]
            if files and 4 <= v.get("duration", 0) <= 60:
                best = min(files, key=lambda f: abs(max(f["width"], f["height"]) - 1920))
                out.append({"url": best["link"], "credit": "Pexels / " + (v.get("user") or {}).get("name", "")})
    elif kind == "pexels_photo" and cfg.get("pexels_key"):
        j = _get("https://api.pexels.com/v1/search", headers={"Authorization": cfg["pexels_key"]},
                 params={"query": query, "per_page": 15, "orientation": orient}).json()
        out = [{"url": p["src"]["large2x"], "credit": "Pexels / " + p.get("photographer", "")} for p in j.get("photos", [])]
    elif kind == "pixabay_video" and cfg.get("pixabay_key"):
        j = _get("https://pixabay.com/api/videos/", params={"key": cfg["pixabay_key"], "q": query, "per_page": 15}).json()
        for h in j.get("hits", []):
            v = h.get("videos", {})
            f = v.get("large") if (v.get("large") or {}).get("url") and v["large"].get("width", 9999) <= 1920 else v.get("medium")
            if f and f.get("url") and 4 <= h.get("duration", 0) <= 60:
                out.append({"url": f["url"], "credit": "Pixabay / " + h.get("user", "")})
    elif kind == "pixabay_photo" and cfg.get("pixabay_key"):
        j = _get("https://pixabay.com/api/", params={"key": cfg["pixabay_key"], "q": query, "per_page": 15,
                                                      "image_type": "photo", "orientation": "vertical" if portrait else "horizontal"}).json()
        out = [{"url": h["largeImageURL"], "credit": "Pixabay / " + h.get("user", "")} for h in j.get("hits", [])]
    elif kind == "commons" and cfg.get("use_openverse", True):
        _throttle("commons", 1.2)
        # Wikimedia Commons: historical photographs, maps, satellite images (free licences)
        j = _get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query", "format": "json", "generator": "search", "gsrsearch": f"filetype:bitmap {query}",
            "gsrnamespace": 6, "gsrlimit": 15, "prop": "imageinfo", "iiprop": "url|extmetadata|size",
            "iiurlwidth": 1920}).json()
        for pg in sorted((j.get("query") or {}).get("pages", {}).values(), key=lambda x: x.get("index", 0)):
            ii = (pg.get("imageinfo") or [{}])[0]
            if ii.get("thumburl") and ii.get("width", 0) >= 800:
                meta = ii.get("extmetadata") or {}
                lic = (meta.get("LicenseShortName") or {}).get("value", "")
                art = re.sub(r"<[^>]+>", "", (meta.get("Artist") or {}).get("value", ""))[:60]
                out.append({"url": ii["thumburl"], "credit": f"{art or 'Wikimedia Commons'} ({lic}) via Wikimedia Commons"})
    elif kind == "openverse" and cfg.get("use_openverse", True):
        j = _get("https://api.openverse.org/v1/images/", params={
            "q": query, "license_type": "commercial", "page_size": 15, "aspect_ratio": "tall" if portrait else "wide",
            "size": "large,medium"}).json()
        out = [{"url": h["url"], "credit": f"{h.get('creator') or 'unknown'} ({(h.get('license') or '').upper()}) via Openverse"}
               for h in j.get("results", []) if h.get("url")]
    _cache[key] = out
    return out


def procedural(path, w, h, seed, accent="#FFD400"):
    """A soft abstract backdrop, used when no stock or AI image is reachable."""
    rnd = random.Random(seed)
    palettes = [((12, 18, 38), (40, 70, 120)), ((30, 14, 40), (110, 50, 90)), ((8, 30, 32), (30, 110, 100)),
                ((38, 22, 12), (140, 80, 40)), ((16, 16, 22), (70, 70, 90))]
    c1, c2 = rnd.choice(palettes)
    sw, sh = w // 4, h // 4
    yy = np.linspace(0, 1, sh)[:, None, None]
    xx = np.linspace(0, 1, sw)[None, :, None]
    g = yy * 0.7 + xx * 0.3
    arr = (np.array(c1) * (1 - g) + np.array(c2) * g).astype(np.uint8)
    img = Image.fromarray(arr, "RGB").convert("RGBA")
    ar = tuple(int(accent.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    layer = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(7):
        r = rnd.randint(sh // 8, sh // 2)
        x, y = rnd.randint(0, sw), rnd.randint(0, sh)
        col = ar if i % 3 == 0 else tuple(min(255, c + 60) for c in c2)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (rnd.randint(35, 80),))
    img = Image.alpha_composite(img, layer.filter(ImageFilter.GaussianBlur(sh // 9)))
    img = img.convert("RGB").resize((w, h), Image.LANCZOS)
    noise = np.random.default_rng(seed).integers(-6, 7, (h, w, 1), dtype=np.int16)
    Image.fromarray(np.clip(np.asarray(img).astype(np.int16) + noise, 0, 255).astype(np.uint8)).save(path, quality=92)
    return path


def ai_image(prompt, path, w, h, seed):
    last = None
    for attempt in range(4):  # the free tier allows one image at a time
        _throttle("ai", 3)
        try:
            return _ai_image(prompt, path, w, h, seed)
        except requests.HTTPError as e:
            last = e
            if e.response is None or e.response.status_code not in (402, 429, 500, 502, 503):
                raise
            time.sleep(4 + attempt * 4)
    raise last


def _ai_image(prompt, path, w, h, seed):
    url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt[:900], safe="")
           + f"?width={w}&height={int(h * 1.1)}&nologo=true&seed={seed}&model=flux")
    _download(url, path)
    im = Image.open(path).convert("RGB")
    # the free tier stamps a small logo in the bottom corner: crop that strip off (the camera move hides the size change)
    im.crop((0, 0, im.width, int(im.height * 0.91))).save(path, quality=93)
    return path


def fetch(scene, n, cfg, style, outdir, w, h, used, source, log=lambda m: None, seed0=0):
    """Find n visuals for one scene. Returns [{path, type, source, credit}]."""
    portrait = h > w
    queries = [q for q in scene.get("queries", []) if q] or ["nature"]
    orders = {
        "stock_video": ["pexels_video", "pixabay_video", "pexels_photo", "pixabay_photo", "commons", "openverse", "ai"],
        "stock_photo": ["pexels_photo", "pixabay_photo", "commons", "openverse", "pexels_video", "ai"],
        "archive": ["commons", "openverse", "pexels_photo", "ai"],
        "ai_image": ["ai", "pexels_photo", "pixabay_photo", "openverse"],
    }
    assets = []
    for k in range(n):
        if source == "mix":
            order = orders[["stock_video", "ai_image", "archive", "stock_photo"][(seed0 + k) % 4]]
        else:
            order = orders.get(source, orders["stock_video"])
        q = queries[k % len(queries)]
        seed = int(hashlib.md5(f"{scene.get('narration', '')}{k}{seed0}".encode()).hexdigest()[:7], 16)
        base = os.path.join(outdir, f"v{seed0:03d}_{k}")
        got = None
        for kind in order:
            try:
                if kind == "ai":
                    if not cfg.get("use_pollinations", True):
                        continue
                    p = ai_image(scene.get("image_prompt", q) + ", " + style.get("image_suffix", ""), base + ".jpg", w, h, seed)
                    got = {"path": p, "type": "image", "source": "AI image", "credit": "AI generated (Pollinations)"}
                else:
                    hits = [x for x in _search(kind, q, cfg, portrait) if x["url"] not in used]
                    if not hits:
                        continue
                    hit = hits[seed % min(len(hits), 5)]
                    is_video = kind.endswith("video")
                    p = _download(hit["url"], base + (".mp4" if is_video else ".jpg"))
                    if not is_video:
                        Image.open(p).convert("RGB").save(p, quality=92)
                    used.add(hit["url"])
                    got = {"path": p, "type": "video" if is_video else "image", "source": kind, "credit": hit["credit"]}
                break
            except Exception as e:
                log(f"  {kind} failed for '{q}': {str(e)[:120]}")
        if not got:
            got = {"path": procedural(base + ".jpg", w, h, seed, style.get("accent", "#FFD400")), "type": "image",
                   "source": "generated backdrop", "credit": ""}
        got["path"] = os.path.relpath(got["path"], os.path.dirname(outdir))
        assets.append(got)
    return assets
