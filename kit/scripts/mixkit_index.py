"""Build a catalog of free Mixkit stock clips (Mixkit License) for a list of keywords."""
import os as _os
KIT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json, re, sys, time, urllib.request, os

UA = {"User-Agent": "Mozilla/5.0"}
CAT = f"{KIT}/data/catalog.json"
cat = json.load(open(CAT)) if os.path.exists(CAT) else {}

def fetch(url):
    err = None
    for i in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30)
            return r.read().decode("utf8", "ignore")
        except Exception as e:
            err = e; time.sleep(2)
    print("fail", url, err); return ""

def videos(html):
    out = {}
    for slug, vid in re.findall(r'href="/free-stock-video/([a-z0-9-]+)-(\d+)/"', html):
        out[int(vid)] = slug.replace("-", " ")
    return out

for kw in sys.argv[1:]:
    if kw in cat: continue
    slug = kw.strip().lower().replace(" ", "-")
    res = {}
    for page in (1, 2, 3):
        url = f"https://mixkit.co/free-stock-video/{slug}/" + (f"?page={page}" if page > 1 else "")
        v = videos(fetch(url))
        if not v or set(v) <= set(res): break
        res.update(v)
    cat[kw] = [{"id": k, "name": n} for k, n in res.items()]
    print(kw, len(cat[kw]), flush=True)
    json.dump(cat, open(CAT, "w"), indent=0)
allc = {x["id"]: x["name"] for v in cat.values() for x in v}
json.dump(allc, open(f"{KIT}/data/all_clips.json", "w"))
