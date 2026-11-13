"""Shared plumbing: paths, owner settings, HTTP, small helpers."""
import hashlib
import json
import math
import os
import random
import re
import threading
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
FONTS = os.path.join(ASSETS, "fonts")
DATA = os.environ.get("STUDIO_DATA", os.path.join(ROOT, "data"))
PROJECTS = os.path.join(DATA, "projects")
CACHE = os.path.join(DATA, "cache")
UPLOADS = os.path.join(DATA, "uploads")
for _d in (DATA, PROJECTS, CACHE, UPLOADS):
    os.makedirs(_d, exist_ok=True)

UA = "FrameForgeStudio/1.0 (self-hosted video tool)"
_lock = threading.RLock()

DEFAULT_SETTINGS = {
    "owner_password": "",
    "llm_provider": "auto",          # auto | anthropic | openai | gemini | groq | pollinations
    "anthropic_key": "", "openai_key": "", "gemini_key": "", "groq_key": "",
    "llm_model": "",
    "elevenlabs_key": "",
    "pexels_key": "", "pixabay_key": "", "youtube_key": "",
    "image_provider": "pollinations",  # pollinations | openai
    "image_model": "flux",
    "max_minutes": 60,
    "credits_enabled": False,
    "render_jobs": max(1, (os.cpu_count() or 2)),
    "default_resolution": 1080,
    "brand_name": "FrameForge",
}


def _settings_path():
    return os.path.join(DATA, "settings.json")


def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, obj):
    tmp = path + ".tmp%d" % threading.get_ident()
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def get_settings():
    s = dict(DEFAULT_SETTINGS)
    s.update(load_json(_settings_path(), {}) or {})
    # environment variables win, so keys can live outside the data folder
    for k in list(s):
        v = os.environ.get("STUDIO_" + k.upper()) or (os.environ.get(k.upper()) if k.endswith("_key") else None)
        if v:
            s[k] = v
    return s


def update_settings(patch):
    with _lock:
        s = load_json(_settings_path(), {}) or {}
        for k, v in patch.items():
            if k in DEFAULT_SETTINGS:
                s[k] = v
        save_json(_settings_path(), s)
    return get_settings()


# ------------------------------------------------------------------ http
_session = None


def http():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers["User-Agent"] = UA
    return _session


def fetch(url, timeout=40, headers=None, params=None, retries=2):
    last = None
    for i in range(retries + 1):
        try:
            r = http().get(url, timeout=timeout, headers=headers, params=params)
            if r.status_code == 200:
                return r
            last = RuntimeError("HTTP %s for %s" % (r.status_code, url[:90]))
            if r.status_code in (400, 401, 403, 404):
                break
        except Exception as e:  # network
            last = e
        time.sleep(0.8 * (i + 1))
    raise last


def download(url, dest, timeout=90, headers=None, max_mb=120):
    """Stream a URL to dest. Returns dest or raises."""
    tmp = dest + ".part"
    with http().get(url, timeout=timeout, headers=headers, stream=True) as r:
        if r.status_code != 200:
            raise RuntimeError("HTTP %s" % r.status_code)
        n = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
                n += len(chunk)
                if n > max_mb * (1 << 20):
                    raise RuntimeError("file too large")
    if os.path.getsize(tmp) < 800:
        os.remove(tmp)
        raise RuntimeError("empty download")
    os.replace(tmp, dest)
    return dest


# ------------------------------------------------------------------ helpers
def uid(n=10):
    return hashlib.sha1(("%s%s" % (time.time(), random.random())).encode()).hexdigest()[:n]


def h(s, n=16):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:n]


def seed_of(*parts):
    return int(hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:8], 16)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t, p=3):
    t = clamp(t)
    return 1 - (1 - t) ** p


def ease_in(t, p=3):
    return clamp(t) ** p


def ease_io(t):
    t = clamp(t)
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def back_out(t, s=1.6):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def ramp(t, a, b):
    """0→1 as t goes a→b."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def words_of(text):
    return re.findall(r"[^\s]+", text or "")


def slugify(s, n=60):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s or "").strip("-").lower()
    return s[:n] or "video"


def sentences(text):
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?।…])\s+(?=[^\s])", text)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if out and len(p) < 12:
            out[-1] += " " + p
        else:
            out.append(p)
    return out


def fmt_time(t):
    t = max(0, int(t))
    return "%d:%02d" % (t // 60, t % 60)


def run(cmd, timeout=None):
    import subprocess
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError("command failed: %s\n%s" % (" ".join(cmd[:6]), p.stderr.decode("utf-8", "ignore")[-900:]))
    return p


def media_duration(path):
    try:
        p = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], timeout=30)
        return float(p.stdout.decode().strip())
    except Exception:
        return 0.0


def hex_rgb(hx):
    hx = hx.lstrip("#")
    return tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4))


def mix_hex(a, b, t):
    A, B = hex_rgb(a), hex_rgb(b)
    return "#%02x%02x%02x" % tuple(int(round(lerp(A[i], B[i], t))) for i in range(3))


def hue_shift(hx, deg, sat=1.0, val=1.0):
    import colorsys
    r, g, b = [c / 255 for c in hex_rgb(hx)]
    hh, s, v = colorsys.rgb_to_hsv(r, g, b)
    hh = (hh + deg / 360.0) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hh, clamp(s * sat), clamp(v * val))
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def tau():
    return math.tau
