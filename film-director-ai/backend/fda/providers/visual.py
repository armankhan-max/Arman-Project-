"""Image generation, video generation and licensed stock/archive search adapters."""
import base64
import re
import time
import urllib.parse

from .base import CredField, Provider, ProviderError, download, http

from .base import UA_DEFAULT
UA = {"User-Agent": UA_DEFAULT}


# ------------------------------------------------------------------ image generation
class ImageProvider(Provider):
    def generate(self, prompt, dest, width=1280, height=720, seed=1, negative="") -> dict:
        raise NotImplementedError


class PollinationsImage(ImageProvider):
    def __init__(self):
        super().__init__(name="pollinations_image", label="Pollinations (free images)", caps=("text_to_image",), paid=False, unit="images",
                         docs="https://pollinations.ai", notes="Free keyless image model (FLUX). Outputs are AI-generated stills, not video.")

    def generate(self, prompt, dest, width=1280, height=720, seed=1, negative=""):
        full = prompt.strip() + (". Avoid: " + negative if negative else "")
        url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(full[:900], safe="")
        pad = 72  # the free service may stamp its name in the bottom corner; generate taller and cut that strip off
        q = "?width=%d&height=%d&seed=%d&nologo=true&model=%s" % (width, height + pad, seed % 999983, (self.config or {}).get("model", "flux"))
        last = None
        for i in range(4):
            try:
                download(url + q, dest, timeout=180, max_mb=30)
                from PIL import Image
                with Image.open(dest) as im:
                    im = im.convert("RGB")
                    cut = int(round(im.height * pad / float(height + pad)))
                    im.crop((0, 0, im.width, im.height - cut)).save(dest, "PNG")
                return {"model": (self.config or {}).get("model", "flux"), "seed": seed}
            except ProviderError as e:
                last = e
                time.sleep(3 + 4 * i)
        raise last

    def validate(self):
        try:
            http("GET", "https://image.pollinations.ai/prompt/ping?width=64&height=64&nologo=true", retries=0, timeout=60)
            return True, "Reachable"
        except ProviderError as e:
            return False, str(e)


class OpenAIImage(ImageProvider):
    def __init__(self):
        super().__init__(name="openai_image", label="OpenAI Images", caps=("text_to_image",), paid=True, unit="images",
                         fields=(CredField("api_key", "API key", "OPENAI_API_KEY"),), docs="https://platform.openai.com/docs/guides/images")

    def generate(self, prompt, dest, width=1280, height=720, seed=1, negative=""):
        self.need()
        size = "1536x1024" if width > height else "1024x1536" if height > width else "1024x1024"
        j = http("POST", "https://api.openai.com/v1/images/generations", timeout=300, headers={"authorization": "Bearer " + self.creds["api_key"]},
                 json={"model": (self.config or {}).get("model", "gpt-image-1"), "prompt": prompt + ((". Avoid: " + negative) if negative else ""), "size": size}).json()
        with open(dest, "wb") as f:
            f.write(base64.b64decode(j["data"][0]["b64_json"]))
        return {"model": (self.config or {}).get("model", "gpt-image-1"), "size": size}

    def validate(self):
        if not self.configured():
            return False, "Missing API key"
        try:
            http("GET", "https://api.openai.com/v1/models", headers={"authorization": "Bearer " + self.creds["api_key"]}, retries=0)
            return True, "Key accepted"
        except ProviderError as e:
            return False, str(e)


# ------------------------------------------------------------------ video generation (async jobs)
class VideoProvider(Provider):
    """submit() returns a job id; poll() returns {'status': 'running'|'succeeded'|'failed', 'url'?, 'error'?}."""

    def submit(self, prompt, image_url=None, duration=5, ratio="16:9", seed=None) -> str:
        raise NotImplementedError

    def poll(self, job_id) -> dict:
        raise NotImplementedError

    def wait(self, job_id, dest, timeout=900, every=8):
        t0 = time.time()
        while time.time() - t0 < timeout:
            st = self.poll(job_id)
            if st["status"] == "succeeded":
                return download(st["url"], dest, timeout=300)
            if st["status"] == "failed":
                raise ProviderError("Video generation failed: %s" % st.get("error", "unknown"), retryable=False)
            time.sleep(every)
        raise ProviderError("Video generation timed out after %ds" % timeout, retryable=True, code="timeout")


class RunwayVideo(VideoProvider):
    API = "https://api.dev.runwayml.com/v1"

    def __init__(self):
        super().__init__(name="runway", label="Runway (image/text to video)", caps=("image_to_video", "text_to_video"), paid=True, unit="seconds",
                         fields=(CredField("api_key", "API secret", "RUNWAYML_API_SECRET"),), docs="https://docs.dev.runwayml.com", verified=False,
                         notes="Written against Runway's public API docs; awaiting credentials for a live test.")

    def _h(self):
        return {"authorization": "Bearer " + self.creds["api_key"], "X-Runway-Version": "2024-11-06", "content-type": "application/json"}

    def submit(self, prompt, image_url=None, duration=5, ratio="16:9", seed=None):
        self.need()
        r = {"16:9": "1280:720", "9:16": "720:1280", "1:1": "960:960"}.get(ratio, "1280:720")
        body = {"model": (self.config or {}).get("model", "gen4_turbo"), "promptText": prompt[:1000], "ratio": r, "duration": 10 if duration > 7 else 5}
        if not image_url:
            raise ProviderError("Runway image_to_video needs a first-frame image", retryable=False)
        body["promptImage"] = image_url
        if seed is not None:
            body["seed"] = int(seed) % 4294967295
        return http("POST", self.API + "/image_to_video", headers=self._h(), json=body).json()["id"]

    def poll(self, job_id):
        j = http("GET", self.API + "/tasks/" + job_id, headers=self._h()).json()
        s = j.get("status")
        if s == "SUCCEEDED":
            return {"status": "succeeded", "url": (j.get("output") or [None])[0]}
        if s in ("FAILED", "CANCELLED"):
            return {"status": "failed", "error": j.get("failure") or s}
        return {"status": "running"}

    def validate(self):
        if not self.configured():
            return False, "Missing API secret"
        try:
            http("GET", self.API + "/organization", headers=self._h(), retries=0)
            return True, "Key accepted"
        except ProviderError as e:
            return False, str(e)


class LumaVideo(VideoProvider):
    API = "https://api.lumalabs.ai/dream-machine/v1"

    def __init__(self):
        super().__init__(name="luma", label="Luma Dream Machine", caps=("text_to_video", "image_to_video"), paid=True, unit="seconds",
                         fields=(CredField("api_key", "API key", "LUMAAI_API_KEY"),), docs="https://docs.lumalabs.ai", verified=False,
                         notes="Written against Luma's public API docs; awaiting credentials for a live test.")

    def _h(self):
        return {"authorization": "Bearer " + self.creds["api_key"], "content-type": "application/json"}

    def submit(self, prompt, image_url=None, duration=5, ratio="16:9", seed=None):
        self.need()
        body = {"prompt": prompt[:2000], "model": (self.config or {}).get("model", "ray-2"), "aspect_ratio": ratio, "duration": "9s" if duration > 7 else "5s"}
        if image_url:
            body["keyframes"] = {"frame0": {"type": "image", "url": image_url}}
        return http("POST", self.API + "/generations", headers=self._h(), json=body).json()["id"]

    def poll(self, job_id):
        j = http("GET", self.API + "/generations/" + job_id, headers=self._h()).json()
        if j.get("state") == "completed":
            return {"status": "succeeded", "url": (j.get("assets") or {}).get("video")}
        if j.get("state") == "failed":
            return {"status": "failed", "error": j.get("failure_reason")}
        return {"status": "running"}

    def validate(self):
        if not self.configured():
            return False, "Missing API key"
        try:
            http("GET", self.API + "/generations?limit=1", headers=self._h(), retries=0)
            return True, "Key accepted"
        except ProviderError as e:
            return False, str(e)


# ------------------------------------------------------------------ stock & archive
def _cand(kind, url, thumb, provider, license, attribution, source_page, w=0, h=0, dur=0, title="", cid="", commercial="yes", terms=None):
    return {"kind": kind, "url": url, "thumb": thumb or url, "provider": provider, "license": license, "attribution": attribution, "source_page": source_page,
            "width": w, "height": h, "duration": dur, "title": title, "id": cid, "commercial_use": commercial, "terms_url": terms}


class Pexels(Provider):
    def __init__(self):
        super().__init__(name="pexels", label="Pexels (stock video & photos)", caps=("stock_video", "stock_image"), paid=False, unit="requests",
                         fields=(CredField("api_key", "API key", "PEXELS_API_KEY"),), docs="https://www.pexels.com/api/",
                         notes="Free. Pexels licence allows commercial use without attribution (attribution is still recorded).")

    def _h(self):
        return {"Authorization": self.creds["api_key"]}

    def search(self, q, kind="video", n=8, portrait=False):
        self.need()
        orient = "portrait" if portrait else "landscape"
        if kind == "video":
            j = http("GET", "https://api.pexels.com/videos/search", headers=self._h(), params={"query": q, "per_page": n, "orientation": orient}).json()
            out = []
            for v in j.get("videos", []):
                fs = sorted([f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4" and f.get("width")], key=lambda f: abs((f.get("height") or 0) - 1080))
                if fs:
                    out.append(_cand("video", fs[0]["link"], v.get("image"), "pexels", "Pexels License", "Video by %s on Pexels" % (v.get("user") or {}).get("name", ""),
                                     v.get("url"), fs[0]["width"], fs[0]["height"], v.get("duration", 0), q, "pexels-v-%s" % v["id"], terms="https://www.pexels.com/license/"))
            return out
        j = http("GET", "https://api.pexels.com/v1/search", headers=self._h(), params={"query": q, "per_page": n, "orientation": orient}).json()
        return [_cand("image", p["src"]["large2x"], p["src"]["medium"], "pexels", "Pexels License", "Photo by %s on Pexels" % p.get("photographer", ""), p.get("url"),
                      p.get("width", 0), p.get("height", 0), 0, p.get("alt") or q, "pexels-p-%s" % p["id"], terms="https://www.pexels.com/license/") for p in j.get("photos", [])]

    def validate(self):
        if not self.configured():
            return False, "Missing API key"
        try:
            http("GET", "https://api.pexels.com/v1/search", headers=self._h(), params={"query": "sky", "per_page": 1}, retries=0)
            return True, "Key accepted"
        except ProviderError as e:
            return False, str(e)


class Pixabay(Provider):
    def __init__(self):
        super().__init__(name="pixabay", label="Pixabay (stock video & photos)", caps=("stock_video", "stock_image"), paid=False, unit="requests",
                         fields=(CredField("api_key", "API key", "PIXABAY_API_KEY"),), docs="https://pixabay.com/api/docs/",
                         notes="Free. Pixabay Content License allows commercial use.")

    def search(self, q, kind="video", n=8, portrait=False):
        self.need()
        if kind == "video":
            j = http("GET", "https://pixabay.com/api/videos/", params={"key": self.creds["api_key"], "q": q[:95], "per_page": max(3, n), "safesearch": "true"}).json()
            out = []
            for v in j.get("hits", []):
                vs = v.get("videos") or {}
                f = vs.get("large") if (vs.get("large") or {}).get("url") else vs.get("medium") or {}
                if f.get("url"):
                    out.append(_cand("video", f["url"], f.get("thumbnail"), "pixabay", "Pixabay Content License", "Video by %s on Pixabay" % v.get("user", ""), v.get("pageURL"),
                                     f.get("width", 0), f.get("height", 0), v.get("duration", 0), v.get("tags", q), "pixabay-v-%s" % v["id"], terms="https://pixabay.com/service/license-summary/"))
            return out
        j = http("GET", "https://pixabay.com/api/", params={"key": self.creds["api_key"], "q": q[:95], "per_page": max(3, n), "image_type": "photo", "safesearch": "true",
                                                         "orientation": "vertical" if portrait else "horizontal"}).json()
        return [_cand("image", p["largeImageURL"], p.get("webformatURL"), "pixabay", "Pixabay Content License", "Image by %s on Pixabay" % p.get("user", ""), p.get("pageURL"),
                      p.get("imageWidth", 0), p.get("imageHeight", 0), 0, p.get("tags", q), "pixabay-p-%s" % p["id"], terms="https://pixabay.com/service/license-summary/") for p in j.get("hits", [])]

    def validate(self):
        if not self.configured():
            return False, "Missing API key"
        try:
            http("GET", "https://pixabay.com/api/", params={"key": self.creds["api_key"], "q": "sky", "per_page": 3}, retries=0)
            return True, "Key accepted"
        except ProviderError as e:
            return False, str(e)


FREE_LICENSES = re.compile(r"^(cc0|public domain|pd|cc by( |-)?(sa )?\d|cc-by(-sa)?-\d|cc by-sa|attribution)", re.I)
BAD_TITLE = re.compile(r"logo|icon|flag of|coat of arms|\.svg|\.pdf|\.djvu|signature|seal of", re.I)


class WikimediaCommons(Provider):
    def __init__(self):
        super().__init__(name="wikimedia", label="Wikimedia Commons (archive photos & video)", caps=("archive_image", "stock_video"), paid=False, unit="requests",
                         docs="https://commons.wikimedia.org/wiki/Commons:API", notes="No key. Only files whose licence is public domain or Creative Commons are returned; attribution is stored.")

    def search(self, q, kind="image", n=8, portrait=False):
        video = kind == "video"
        params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": min(40, n * 4),
                  "gsrsearch": "%s filetype:%s" % (q, "video" if video else "bitmap"), "prop": "videoinfo" if video else "imageinfo",
                  ("viprop" if video else "iiprop"): "url|size|mime|extmetadata" + ("|derivatives" if video else ""), ("viurlwidth" if video else "iiurlwidth"): 1920}
        j = http("GET", "https://commons.wikimedia.org/w/api.php", params=params, headers=UA, timeout=30).json()
        out = []
        for p in sorted(((j.get("query") or {}).get("pages") or {}).values(), key=lambda p: p.get("index", 99)):
            title = p.get("title", "")
            ii = (p.get("videoinfo") or p.get("imageinfo") or [{}])[0]
            w, h = ii.get("width", 0), ii.get("height", 0)
            md = ii.get("extmetadata") or {}
            lic = (md.get("LicenseShortName") or {}).get("value", "")
            if not ii.get("url") or BAD_TITLE.search(title) or w < 640 or not h or not FREE_LICENSES.search(lic or ""):
                continue
            artist = re.sub(r"<[^>]+>", "", (md.get("Artist") or {}).get("value", "")).strip()[:80] or "Unknown"
            commercial = "yes"
            if video:
                dur = float(ii.get("duration") or 0)
                if dur < 3 or w / h < 1.2 or ii.get("size", 0) > 200e6:
                    continue
                url = ii["url"]
                for d in ii.get("derivatives") or []:
                    if d.get("type", "").startswith("video/webm") and str(d.get("transcodekey", "")).startswith(("720p", "1080p")):
                        url = d["src"]
                out.append(_cand("video", url, ii.get("thumburl"), "wikimedia", lic, "%s, %s, via Wikimedia Commons" % (artist, lic), ii.get("descriptionurl"),
                                 w, h, dur, title[5:], "commons-%s" % p["pageid"], commercial, (md.get("LicenseUrl") or {}).get("value")))
            else:
                if not (0.5 < w / h < 2.8) or ii.get("mime") not in ("image/jpeg", "image/png", "image/tiff", "image/webp"):
                    continue
                out.append(_cand("image", ii.get("thumburl") or ii["url"], ii.get("thumburl"), "wikimedia", lic, "%s, %s, via Wikimedia Commons" % (artist, lic),
                                 ii.get("descriptionurl"), w, h, 0, title[5:], "commons-%s" % p["pageid"], commercial, (md.get("LicenseUrl") or {}).get("value")))
            if len(out) >= n:
                break
        return out

    def validate(self):
        try:
            self.search("moon", "image", 1)
            return True, "Reachable"
        except ProviderError as e:
            return False, str(e)


class NASAImages(Provider):
    def __init__(self):
        super().__init__(name="nasa", label="NASA Image and Video Library", caps=("archive_image",), paid=False, unit="requests",
                         docs="https://images.nasa.gov", notes="No key. NASA media is generally not copyrighted; logos and identifiable people have restrictions.")

    def search(self, q, kind="image", n=8, portrait=False):
        j = http("GET", "https://images-api.nasa.gov/search", params={"q": q, "media_type": "image"}, timeout=30, retries=1).json()
        out = []
        for it in (j.get("collection") or {}).get("items", [])[:n]:
            d = (it.get("data") or [{}])[0]
            link = (it.get("links") or [{}])[0].get("href")
            if link:
                out.append(_cand("image", link.replace("~thumb", "~large"), link, "nasa", "NASA media usage guidelines", "Image: NASA (%s)" % d.get("nasa_id", ""),
                                 "https://images.nasa.gov/details/%s" % d.get("nasa_id", ""), 0, 0, 0, d.get("title", q), "nasa-%s" % d.get("nasa_id", ""),
                                 "yes", "https://www.nasa.gov/nasa-brand-center/images-and-media/"))
        return out

    def validate(self):
        try:
            self.search("moon", n=1)
            return True, "Reachable"
        except ProviderError as e:
            return False, str(e)


# ------------------------------------------------------------------ more keyless internet sources
OPENVERSE_OK = {"cc0", "pdm", "by", "by-sa"}


class Openverse(Provider):
    def __init__(self):
        super().__init__(name="openverse", label="Openverse (CC & public-domain images)", caps=("stock_image", "archive_image"), paid=False, unit="requests",
                         docs="https://api.openverse.org/v1/", notes="No key. Searches hundreds of millions of openly licensed images; only licences that allow commercial use are kept.")

    def search(self, q, kind="image", n=8, portrait=False):
        j = http("GET", "https://api.openverse.org/v1/images/", headers=UA, timeout=30, retries=1,
                 params={"q": q[:200], "page_size": min(20, n * 2), "license": ",".join(sorted(OPENVERSE_OK)), "aspect_ratio": "tall" if portrait else "wide",
                         "size": "large", "mature": "false"}).json()
        out = []
        for r in j.get("results", []):
            if (r.get("license") or "").lower() not in OPENVERSE_OK or not r.get("url"):
                continue
            lic = "CC %s %s" % (r.get("license", "").upper(), r.get("license_version") or "") if r.get("license") not in ("cc0", "pdm") else r.get("license", "").upper()
            out.append(_cand("image", r["url"], r.get("thumbnail"), "openverse", lic.strip(), r.get("attribution") or "%s via Openverse" % (r.get("creator") or "unknown"),
                             r.get("foreign_landing_url"), r.get("width") or 0, r.get("height") or 0, 0, " ".join([r.get("title") or ""] + [t.get("name", "") for t in (r.get("tags") or [])[:8]]),
                             "openverse-%s" % r["id"], "yes", r.get("license_url")))
            if len(out) >= n:
                break
        return out

    def validate(self):
        try:
            self.search("mountain", n=1)
            return True, "Reachable"
        except ProviderError as e:
            return False, str(e)


class NASAVideo(Provider):
    def __init__(self):
        super().__init__(name="nasa_video", label="NASA video library", caps=("stock_video",), paid=False, unit="requests", docs="https://images.nasa.gov",
                         notes="No key. Real space, Earth-science and mission footage; NASA media is generally not copyrighted.")

    def search(self, q, kind="video", n=6, portrait=False):
        if kind != "video":
            return []
        j = http("GET", "https://images-api.nasa.gov/search", params={"q": q, "media_type": "video"}, timeout=30, retries=1).json()
        out = []
        for it in (j.get("collection") or {}).get("items", [])[:n * 2]:
            d = (it.get("data") or [{}])[0]
            nid = d.get("nasa_id")
            if not nid:
                continue
            try:
                files = http("GET", it["href"], timeout=20, retries=0).json()
            except (ProviderError, ValueError, KeyError):
                continue
            mp4 = [f for f in files if f.endswith(".mp4")]
            pick = next((f for f in mp4 if "~medium" in f), None) or next((f for f in mp4 if "~orig" in f), None) or next(iter(mp4), None)
            if not pick:
                continue
            thumb = next((f for f in files if f.endswith((".jpg", ".png"))), None)
            out.append(_cand("video", pick.replace("http://", "https://"), thumb, "nasa_video", "NASA media usage guidelines", "Video: NASA (%s)" % nid,
                             "https://images.nasa.gov/details/%s" % nid, 1280, 720, 0, "%s %s" % (d.get("title", ""), " ".join(d.get("keywords") or [])),
                             "nasa-v-%s" % nid, "yes", "https://www.nasa.gov/nasa-brand-center/images-and-media/"))
            if len(out) >= n:
                break
        return out

    def validate(self):
        try:
            http("GET", "https://images-api.nasa.gov/search", params={"q": "moon", "media_type": "video"}, timeout=20, retries=0)
            return True, "Reachable"
        except ProviderError as e:
            return False, str(e)


class InternetArchive(Provider):
    def __init__(self):
        super().__init__(name="internet_archive", label="Internet Archive (public-domain film & newsreels)", caps=("stock_video",), paid=False, unit="requests",
                         docs="https://archive.org/advancedsearch.php",
                         notes="No key. Public-domain material only: Prelinger Archives, Universal Newsreels, FedFlix and items marked public domain.")

    def search(self, q, kind="video", n=6, portrait=False):
        if kind != "video":
            return []
        query = '(%s) AND mediatype:movies AND (collection:prelinger OR collection:universal_newsreels OR collection:FedFlix OR licenseurl:*publicdomain*)' % q.replace('"', "")
        j = http("GET", "https://archive.org/advancedsearch.php", headers=UA, timeout=30, retries=1,
                 params={"q": query, "fl[]": ["identifier", "title", "licenseurl", "subject", "year"], "rows": n * 2, "sort[]": "downloads desc", "output": "json"}).json()
        out = []
        for d in (j.get("response") or {}).get("docs", []):
            ident = d.get("identifier")
            lic = d.get("licenseurl") or ""
            if not ident or (lic and "publicdomain" not in lic):
                continue  # only public domain (licence URL, or the public-domain Prelinger / Universal Newsreels / FedFlix collections)
            try:
                meta = http("GET", "https://archive.org/metadata/%s" % ident, headers=UA, timeout=20, retries=0).json()
            except (ProviderError, ValueError):
                continue
            vids = [f for f in meta.get("files", []) if (f.get("name", "").lower().endswith(".mp4")) and int(f.get("size") or 0) < 220 * (1 << 20)]
            if not vids:
                continue
            f = sorted(vids, key=lambda f: -int(f.get("size") or 0))[0]
            subj = d.get("subject") or []
            out.append(_cand("video", "https://archive.org/download/%s/%s" % (ident, f["name"]), "https://archive.org/services/img/%s" % ident, "internet_archive",
                             "Public domain",
                             "%s, Internet Archive" % (d.get("title") or ident), "https://archive.org/details/%s" % ident, int(f.get("width") or 0), int(f.get("height") or 0),
                             float(f.get("length") or 0) if str(f.get("length") or "").replace(".", "").isdigit() else 0,
                             "%s %s" % (d.get("title") or "", " ".join(subj) if isinstance(subj, list) else subj), "ia-%s" % ident, "yes", lic))
            if len(out) >= n:
                break
        return out

    def validate(self):
        try:
            http("GET", "https://archive.org/advancedsearch.php", params={"q": "moon", "rows": 1, "output": "json"}, timeout=20, retries=0)
            return True, "Reachable"
        except ProviderError as e:
            return False, str(e)
