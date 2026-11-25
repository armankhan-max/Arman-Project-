"""Search Wikimedia Commons for freely-licensed images and download them.
usage: python -I commons.py search "<query>" N   -> prints candidates json
       python -I commons.py get <outdir> <tag> "<query>" N
Only keeps Public Domain / CC0 / CC-BY / CC-BY-SA files."""
import json, sys, os, re, urllib.request, urllib.parse, time
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "OldFilmEditor/1.0 (educational video project)"}
OK = re.compile(r"^(public domain|pd|cc0|cc[- ]by(-sa)?[- ]?\d|cc by(-sa)? \d|no restrictions)", re.I)

def api(**p):
    p.update(format="json")
    url = API + "?" + urllib.parse.urlencode(p)
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.load(r)
        except Exception as e:
            time.sleep(2 + 3 * i)
    return {}

def search(q, n=20):
    d = api(action="query", generator="search", gsrsearch=q + " filetype:bitmap", gsrnamespace=6,
            gsrlimit=n, prop="imageinfo", iiprop="url|extmetadata|size|mime", iiurlwidth=1280)
    out = []
    for pg in (d.get("query", {}).get("pages", {}) or {}).values():
        ii = (pg.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        lic = md.get("LicenseShortName", {}).get("value", "")
        if not OK.search(lic.strip()):
            continue
        if ii.get("width", 0) < 900:
            continue
        artist = re.sub("<[^>]+>", "", md.get("Artist", {}).get("value", ""))[:120]
        out.append(dict(title=pg["title"], idx=pg.get("index", 0), lic=lic, artist=artist.strip(),
                        url=ii.get("thumburl") or ii["url"], page=ii.get("descriptionurl"),
                        w=ii.get("width"), h=ii.get("height"),
                        date=re.sub("<[^>]+>", "", md.get("DateTimeOriginal", {}).get("value", ""))[:40]))
    out.sort(key=lambda x: x["idx"])
    return out

def download(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 20000:
        return True
    for i in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                open(path, "wb").write(r.read())
            time.sleep(1.2)
            return True
        except Exception as e:
            time.sleep(10 * (i + 1))
    return False

if __name__ == "__main__":
    if sys.argv[1] == "search":
        for c in search(sys.argv[2], int(sys.argv[3])):
            print(json.dumps(c))
    elif sys.argv[1] == "get":
        outdir, tag, q, n = sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
        os.makedirs(outdir, exist_ok=True)
        res = search(q, n)
        meta = []
        for k, c in enumerate(res):
            ext = os.path.splitext(c["url"].split("?")[0])[1].lower() or ".jpg"
            if ext not in (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"):
                ext = ".jpg"
            p = os.path.join(outdir, f"{tag}_{k:02d}{ext}")
            if download(c["url"], p):
                c["file"] = p; meta.append(c)
            time.sleep(0.3)
        with open(os.path.join(outdir, f"{tag}.json"), "w") as f:
            json.dump(meta, f, indent=1)
        print(tag, len(meta))
