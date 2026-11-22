import json, urllib.request, urllib.parse, time, sys
UA = {"User-Agent": "DocumentaryResearchBot/1.0 (educational video editing)"}
out = {}
qs = [l.split("|") for l in open(sys.argv[1]).read().strip().split("\n")]
for tag, q, n in qs:
    url = "https://www.loc.gov/photos/?" + urllib.parse.urlencode({"q": q, "fo": "json", "c": 40, "fa": "online-format:image"})
    try: d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40))
    except Exception as e: print(tag, "ERR", e); continue
    res = []
    for r in (d.get("results") or d.get("content", {}).get("results", [])):
        if r.get("access_restricted"): continue
        imgs = r.get("image_url", [])
        if not imgs: continue
        u = imgs[-1].split("#")[0]
        if not any(c in u for c in ("/pnp/fsa/", "/pnp/det/", "/pnp/highsm/")): continue
        import re as _re
        best = _re.sub(r"_\d+px\.jpg$", "v.jpg", u)
        res.append({"title": r.get("title", ""), "url": best, "page": r.get("id")})
        if len(res) >= int(n): break
    out[tag] = res; print(tag, len(res), flush=True); time.sleep(1)
json.dump(out, open("loc_hits.json", "w"), indent=0)
