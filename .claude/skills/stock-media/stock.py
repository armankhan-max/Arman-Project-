#!/usr/bin/env python3
"""stock.py <video|image> "<topic>" [--n 6] [--out DIR] [--min-height 720]
Downloads license-free stock media without watermarks and writes credits.txt."""
import argparse, json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

UA = "stock-media-skill/1.0 (personal video project)"
ap = argparse.ArgumentParser(); ap.add_argument("kind", choices=["video", "image"]); ap.add_argument("topic")
ap.add_argument("--n", type=int, default=6); ap.add_argument("--out"); ap.add_argument("--min-height", type=int, default=720)
a = ap.parse_args()
out = Path(a.out or "stock/" + re.sub(r"\W+", "-", a.topic.lower()).strip("-")); out.mkdir(parents=True, exist_ok=True)

def get(url, headers=None, binary=False, tries=2):
    for i in range(tries):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})}), timeout=60)
            d = r.read(); return d if binary else json.loads(d)
        except Exception as e:
            if i == tries - 1: print("  fail:", url[:80], str(e)[:60], file=sys.stderr); return None
            time.sleep(3 * (i + 1))

q = urllib.parse.quote(a.topic); found = []  # (url, ext, title, author, license, page)

def pexels():
    k = os.environ.get("PEXELS_API_KEY")
    if not k: return
    if a.kind == "video":
        d = get(f"https://api.pexels.com/videos/search?query={q}&per_page={a.n}&orientation=landscape", {"Authorization": k})
        for v in (d or {}).get("videos", []):
            fs = sorted([f for f in v["video_files"] if f["file_type"] == "video/mp4" and f["height"] >= a.min_height], key=lambda f: abs(f["height"] - 1080))
            if fs: found.append((fs[0]["link"], "mp4", f"Pexels video {v['id']}", v["user"]["name"], "Pexels License (free, no attribution needed)", v["url"]))
    else:
        d = get(f"https://api.pexels.com/v1/search?query={q}&per_page={a.n}&orientation=landscape", {"Authorization": k})
        for p in (d or {}).get("photos", []):
            found.append((p["src"]["large2x"], "jpg", f"Pexels photo {p['id']}", p["photographer"], "Pexels License (free, no attribution needed)", p["url"]))

def pixabay():
    k = os.environ.get("PIXABAY_API_KEY")
    if not k: return
    if a.kind == "video":
        d = get(f"https://pixabay.com/api/videos/?key={k}&q={q}&per_page={a.n}")
        for v in (d or {}).get("hits", []):
            for size in ("large", "medium"):
                u = v["videos"].get(size, {}).get("url")
                if u: found.append((u, "mp4", f"Pixabay video {v['id']}", v["user"], "Pixabay License (free, no attribution needed)", v["pageURL"])); break
    else:
        d = get(f"https://pixabay.com/api/?key={k}&q={q}&per_page={a.n}&image_type=photo&orientation=horizontal")
        for p in (d or {}).get("hits", []):
            found.append((p["largeImageURL"], "jpg", f"Pixabay photo {p['id']}", p["user"], "Pixabay License (free, no attribution needed)", p["pageURL"]))

def openverse():
    if a.kind != "image": return
    d = get(f"https://api.openverse.org/v1/images/?q={q}&license_type=commercial&page_size={a.n}&aspect_ratio=wide")
    for r in (d or {}).get("results", []):
        found.append((r["url"], (r.get("filetype") or "jpg").lower().replace("jpeg", "jpg"), r["title"] or "image", r.get("creator") or "unknown",
                      f"{r['license'].upper()} {r.get('license_version') or ''}".strip() + (" (credit the author)" if r["license"] not in ("cc0", "pdm") else ""), r["foreign_landing_url"]))

def commons():
    typ = "video" if a.kind == "video" else "bitmap"
    d = get(f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={q}+filetype:{typ}&gsrnamespace=6&gsrlimit={a.n * 2}"
            "&prop=imageinfo&iiprop=url|size|extmetadata&format=json")
    for p in (d or {}).get("query", {}).get("pages", {}).values():
        i = p["imageinfo"][0]; m = i.get("extmetadata", {})
        if a.kind == "video" and i.get("height", 0) < a.min_height: continue
        lic = m.get("LicenseShortName", {}).get("value", "")
        if "NC" in lic or "ND" in lic: continue
        au = re.sub("<[^>]+>", "", m.get("Artist", {}).get("value", "unknown"))
        found.append((i["url"], i["url"].rsplit(".", 1)[-1].lower(), p["title"], au, lic + " (Wikimedia Commons)", i["descriptionurl"]))

def archive():
    if a.kind != "video": return
    qq = urllib.parse.quote(f"{a.topic} AND mediatype:movies AND (licenseurl:*creativecommons* OR licenseurl:*publicdomain*)")
    d = get(f"https://archive.org/advancedsearch.php?q={qq}&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=creator&fl%5B%5D=licenseurl&rows={a.n * 3}&output=json")
    for r in (d or {}).get("response", {}).get("docs", []):
        md = get(f"https://archive.org/metadata/{r['identifier']}")
        fs = [f for f in (md or {}).get("files", []) if f["name"].lower().endswith(".mp4") and int(f.get("size", 0)) < 300e6 and int(f.get("height", 0) or 0) >= a.min_height]
        if fs:
            lic = r.get("licenseurl", ""); lic = lic[0] if isinstance(lic, list) else lic
            if "-nc" in lic or "-nd" in lic: continue
            found.append((f"https://archive.org/download/{r['identifier']}/{urllib.parse.quote(fs[0]['name'])}", "mp4", r["title"], str(r.get("creator", "unknown")), lic or "see page", f"https://archive.org/details/{r['identifier']}"))

for fn in (pexels, pixabay, openverse, commons, archive): fn()
got = 0; lines = []
for u, ext, title, author, lic, page in found:
    if got >= a.n: break
    if ext not in ("mp4", "webm", "mov", "jpg", "jpeg", "png", "webp", "gif"): continue
    name = out / (f"{got + 1:02d}-" + re.sub(r"\W+", "-", title.lower())[:40].strip("-") + "." + ext)
    data = get(u, binary=True)
    if not data or len(data) < 20000: continue
    name.write_bytes(data); got += 1
    lines.append(f"{name.name} | {title} | by {author} | {lic} | {page}")
    print("saved", name, f"{len(data) // 1024} KB |", lic)
(out / "credits.txt").write_text("\n".join(lines) + "\n")
print(f"{got} file(s) in {out}" + ("" if got else "  (nothing found: try other words, or set PEXELS_API_KEY / PIXABAY_API_KEY)"))
