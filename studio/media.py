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

UA = {"User-Agent": "AIVideoStudio/1.2 (self-hosted video maker; python-requests)"}
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


CONTACT = {"ua": ""}


def _get(url, **kw):
    ua = dict(UA)
    if CONTACT["ua"]:  # Wikimedia asks automated clients for a contact address; the owner can set one in Settings
        ua["User-Agent"] = UA["User-Agent"].replace(")", f"; {CONTACT['ua']})")
    for attempt in range(3):
        r = requests.get(url, timeout=kw.get("timeout", 40), headers={**ua, **kw.get("headers", {})},
                         **{k: v for k, v in kw.items() if k not in ("timeout", "headers")})
        if r.status_code not in (502, 503, 504) or attempt == 2:
            break
        time.sleep(2 + attempt * 3)
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
                out.append({"url": best["link"], "credit": "Pexels / " + (v.get("user") or {}).get("name", ""), "preview": v.get("image", ""),
                            "text": re.sub(r"[-/\\d]+", " ", (v.get("url") or "").split("/video/")[-1])})
    elif kind == "pexels_photo" and cfg.get("pexels_key"):
        j = _get("https://api.pexels.com/v1/search", headers={"Authorization": cfg["pexels_key"]},
                 params={"query": query, "per_page": 15, "orientation": orient}).json()
        out = [{"url": p["src"]["large2x"], "credit": "Pexels / " + p.get("photographer", ""), "preview": p["src"].get("medium", ""), "text": p.get("alt") or ""} for p in j.get("photos", [])]
    elif kind == "pixabay_video" and cfg.get("pixabay_key"):
        j = _get("https://pixabay.com/api/videos/", params={"key": cfg["pixabay_key"], "q": query, "per_page": 15}).json()
        for h in j.get("hits", []):
            v = h.get("videos", {})
            f = v.get("large") if (v.get("large") or {}).get("url") and v["large"].get("width", 9999) <= 1920 else v.get("medium")
            if f and f.get("url") and 4 <= h.get("duration", 0) <= 60:
                out.append({"url": f["url"], "credit": "Pixabay / " + h.get("user", ""), "preview": (v.get("tiny") or {}).get("thumbnail") or f.get("thumbnail", ""), "text": h.get("tags", "")})
    elif kind == "pixabay_photo" and cfg.get("pixabay_key"):
        j = _get("https://pixabay.com/api/", params={"key": cfg["pixabay_key"], "q": query, "per_page": 15,
                                                      "image_type": "photo", "orientation": "vertical" if portrait else "horizontal"}).json()
        out = [{"url": h["largeImageURL"], "credit": "Pixabay / " + h.get("user", ""), "preview": h.get("webformatURL", ""), "text": h.get("tags", "")} for h in j.get("hits", [])]
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
                out.append({"url": ii["thumburl"], "credit": f"{art or 'Wikimedia Commons'} ({lic}) via Wikimedia Commons", "preview": ii["thumburl"],
                            "text": re.sub(r"^File:|\\.\\w+$|[_\\-]", " ", pg.get("title", ""))})
    elif kind == "openverse" and cfg.get("use_openverse", True):
        j = _get("https://api.openverse.org/v1/images/", params={
            "q": query, "license_type": "commercial", "page_size": 15, "aspect_ratio": "tall" if portrait else "wide",
            "size": "large,medium"}).json()
        out = [{"url": h["url"], "credit": f"{h.get('creator') or 'unknown'} ({(h.get('license') or '').upper()}) via Openverse", "preview": h.get("thumbnail") or h["url"],
                "text": (h.get("title") or "") + " " + " ".join(t.get("name", "") for t in (h.get("tags") or [])[:12])}
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
    CONTACT["ua"] = cfg.get("contact_for_sources", "")
    """Find n visuals for one scene. Returns [{path, type, source, credit}]."""
    portrait = h > w
    queries = [q for q in scene.get("queries", []) if q] or ["nature"]
    orders = {
        "stock_video": ["pexels_video", "pixabay_video", "pexels_photo", "pixabay_photo", "commons", "openverse", "ai"],
        "stock_photo": ["pexels_photo", "pixabay_photo", "commons", "openverse", "pexels_video", "ai"],
        "archive": ["commons", "openverse", "pexels_photo", "ai"],
        "stock_video_ai": ["pexels_video", "pixabay_video", "ai", "pexels_photo", "pixabay_photo"],
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
        blocked = set(cfg.get("_blocked_sources") or [])
        groups = {"stock_video": ("pexels_video", "pixabay_video"), "stock_photo": ("pexels_photo", "pixabay_photo"),
                  "ai_image": ("ai",), "commons": ("commons", "openverse")}
        skip = {k for g in blocked for k in groups.get(g, ())}
        for kind in [k for k in order if k not in skip]:
            try:
                if kind == "ai":
                    if not cfg.get("use_pollinations", True):
                        continue
                    p = ai_image(scene.get("image_prompt", q) + ", " + style.get("image_suffix", ""), base + ".jpg", w, h, seed)
                    got = {"path": p, "type": "image", "source": "AI image", "credit": "AI generated (Pollinations)"}
                else:
                    bad_d, bad_w = cfg.get("_block_domains") or [], cfg.get("_block_words") or []
                    hits = [x for x in _search(kind, q, cfg, portrait) if x["url"] not in used
                            and not any(dm in x["url"].lower() for dm in bad_d)
                            and not any(bw in (x.get("credit", "") + x["url"]).lower() for bw in bad_w)]
                    if not hits:
                        continue
                    hit = best_hit(hits, scene, q, seed, cfg)
                    if hit is None:
                        continue  # nothing here really shows this scene: try the next source
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


SEARCH_KINDS = {"video": ["pexels_video", "pixabay_video"], "photo": ["pexels_photo", "pixabay_photo", "commons", "openverse"]}


def candidates(query, cfg, kind="all", portrait=False):
    """Search results for the editor's visual picker (nothing is downloaded yet)."""
    kinds = SEARCH_KINDS["video"] + SEARCH_KINDS["photo"] if kind == "all" else SEARCH_KINDS.get(kind, [])
    out, errors = [], []
    for k in kinds:
        try:
            for x in _search(k, query, cfg, portrait)[:8]:
                out.append({**x, "type": "video" if k.endswith("video") else "image", "kind": k})
        except Exception as e:
            errors.append(f"{k}: {str(e)[:80]}")
    return out, errors


def download_pick(url, typ, outdir):
    name = f"pick_{hashlib.md5(url.encode()).hexdigest()[:12]}" + (".mp4" if typ == "video" else ".jpg")
    path = os.path.join(outdir, name)
    if not os.path.exists(path):
        _download(url, path)
        if typ != "video":
            Image.open(path).convert("RGB").save(path, quality=92)
    return path


_WORD = re.compile(r"[a-z]{3,}")


def _stem(w):
    for suf in ("ing", "es", "s", "ed"):
        if w.endswith(suf) and len(w) > len(suf) + 3:
            return w[: -len(suf)]
    return w


def relevance(hit_text, want):
    have = {_stem(w) for w in _WORD.findall((hit_text or "").lower())}
    return sum(1 for w in want if w in have)


def best_hit(hits, scene, query, seed, cfg):
    """Pick the result that really shows the scene: rank by word overlap with the search words and narration,
    drop results with no overlap at all, and (with a Claude key) ask Claude to confirm the picture fits."""
    import llm
    q_words = {_stem(w) for w in _WORD.findall(query.lower())} - llm.STOP
    n_words = {_stem(w) for w in _WORD.findall((scene.get("narration", "") + " " + scene.get("image_prompt", "")).lower())} - llm.STOP
    scored = []
    for i, h in enumerate(hits[:15]):
        txt = h.get("text", "")
        s = 3 * relevance(txt, q_words) + relevance(txt, n_words)
        if not txt:
            s = 1  # provider gave no description: neutral
        scored.append((s, -i, h))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    good = [x for x in scored if x[0] > 0]
    if not good:
        return None
    top = [h for s, _, h in good if s >= good[0][0] - 1][:3]
    order = top[seed % len(top):] + top[: seed % len(top)]
    if cfg.get("anthropic_key"):
        for h in order:
            ok = vision_check(cfg, h.get("preview") or h["url"], scene.get("narration", ""))
            if ok is not False:
                return h
        return None
    return order[0]


def vision_check(cfg, image_url, narration):
    """True/False from Claude looking at the picture; None if it could not check."""
    try:
        r = requests.post("https://api.anthropic.com/v1/messages", timeout=60, headers={
            "x-api-key": cfg["anthropic_key"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": cfg.get("anthropic_model") or "claude-sonnet-5-5", "max_tokens": 5, "messages": [{"role": "user", "content": [
                {"type": "image", "source": {"type": "url", "url": image_url}},
                {"type": "text", "text": "A documentary narrator says: \"" + narration[:400] + "\"\nWould this picture be a fitting, accurate visual "
                                         "for that line (no unrelated subject, no visible watermark, no text-heavy graphic)? Answer only YES or NO."}]}]})
        if r.status_code != 200:
            return None
        ans = "".join(b.get("text", "") for b in r.json().get("content", [])).strip().upper()
        return ans.startswith("Y")
    except Exception:
        return None
