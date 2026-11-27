import urllib.parse
import json, sys, urllib.request, os
ident = sys.argv[1]
d = json.load(urllib.request.urlopen(f"https://archive.org/metadata/{ident}", timeout=60))
m = d.get("metadata", {})
files = [f for f in d["files"] if f["name"].lower().endswith((".mp4", ".mpeg4", ".m4v", ".ogv"))]
def score(f):
    n = f["name"].lower(); s = int(f.get("size", 0) or 0)
    pref = 0 if n.endswith(".mp4") and "512kb" not in n else (1 if n.endswith(".mp4") else 2)
    return (pref, s if s < 900e6 else 9e12)
files.sort(key=score)
if not files: print("NOFILE", ident); sys.exit()
f = files[0]
print(ident, "|", m.get("title"), "|", m.get("licenseurl"), "|", m.get("collection"), "|", f["name"], f.get("size"))
url = f"https://archive.org/download/{ident}/{urllib.parse.quote(f['name'])}"
os.system(f"curl -sL --retry 4 -m 1800 -o '{ident}.mp4' '{url}'")
json.dump({"id": ident, "title": m.get("title"), "license": m.get("licenseurl"), "collection": m.get("collection"), "url": f"https://archive.org/details/{ident}"}, open(ident + ".json", "w"))
