import json, sys, time, urllib.parse, urllib.request, os, re
UA = {"User-Agent": "DocumentaryResearchBot/1.0 (educational video editing)"}
def get(url):
    for k in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
        except Exception as e:
            time.sleep(3 * (k + 1))
    return {}
OKL = re.compile(r"public domain|pd|cc0|no restrictions", re.I)
out = json.load(open("commons_hits.json")) if os.path.exists("commons_hits.json") else {}
for tag, q, n in [l.split("|") for l in open(sys.argv[1]).read().strip().split("\n")]:
    if tag in out: continue
    url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6&gsrlimit=30&gsrsearch="
           + urllib.parse.quote(q + " filetype:bitmap") + "&prop=imageinfo&iiprop=url|extmetadata|size&iiurlwidth=1600")
    d = get(url); res = []
    for p in sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99)):
        ii = p.get("imageinfo", [{}])[0]; md = ii.get("extmetadata", {})
        lic = md.get("LicenseShortName", {}).get("value", "")
        if not OKL.search(lic): continue
        if ii.get("width", 0) < 900: continue
        res.append({"title": p["title"], "url": ii.get("thumburl") or ii.get("url"), "lic": lic})
        if len(res) >= int(n): break
    out[tag] = res; print(tag, len(res), flush=True)
    json.dump(out, open("commons_hits.json", "w"), indent=0); time.sleep(1)
