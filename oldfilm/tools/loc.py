"""Library of Congress photo search+download (public-domain / no known restrictions items).
usage: python -I loc.py get <outdir> <tag> "<query>" N"""
import json, sys, os, re, time, urllib.request, urllib.parse
UA = {"User-Agent": "OldFilmEditor/1.0 (educational video project)"}
def fetch(url, binary=False, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=150) as r:
                b = r.read()
                return b if binary else json.loads(b)
        except Exception as e:
            time.sleep(4 * (i + 1))
    return None
def search(q, n):
    base = os.environ.get("LOCBASE", "https://www.loc.gov/collections/fsa-owi-black-and-white-negatives/")
    url = base + "?" + urllib.parse.urlencode({"q": q, "fo": "json", "c": n})
    d = fetch(url) or {}
    out = []
    for r in d.get("results", []):
        if r.get("access_restricted"): continue
        imgs = [u.split("#")[0] for u in r.get("image_url", [])]
        if not imgs: continue
        big = imgs[-1]
        # prefer the large 'v' derivative for pnp images
        m = re.match(r"(.*/service/pnp/.+/)(\w+?)(_\d+px|[a-z])?\.(jpg|gif)$", big)
        cands = []
        if m: cands.append(f"{m.group(1)}{m.group(2)}v.jpg")
        cands.append(big)
        out.append(dict(title=r.get("title"), date=r.get("date"), page=r.get("url"), cands=cands,
                        partof=[p for p in (r.get("partof") or []) if isinstance(p, str)][:4]))
    return out
if __name__ == "__main__":
    outdir, tag, q, n = sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
    os.makedirs(outdir, exist_ok=True); meta = []
    for k, c in enumerate(search(q, n)):
        p = os.path.join(outdir, f"{tag}_{k:02d}.jpg")
        if not (os.path.exists(p) and os.path.getsize(p) > 15000):
            for u in c["cands"]:
                b = fetch(u, binary=True, tries=2)
                if b and len(b) > 15000 and b[:2] == b"\xff\xd8":
                    open(p, "wb").write(b); c["img"] = u; break
        if os.path.exists(p):
            c["file"] = p; meta.append(c)
    json.dump(meta, open(os.path.join(outdir, f"{tag}.json"), "w"), indent=1)
    print(tag, len(meta), flush=True)
