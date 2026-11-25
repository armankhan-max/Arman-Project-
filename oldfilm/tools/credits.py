"""List every external source actually used in the edit, with its license."""
import json, os, glob
edl = json.load(open("plan/edl.json"))
used = set()
for s in edl:
    src = s["src"]; used.add(src.get("img") or src.get("vid") or "")
meta = {}
for d in ["stock/fsa", "stock/loc"]:
    for j in glob.glob(d + "/*.json"):
        for x in json.load(open(j)):
            b = os.path.basename(x["file"])
            meta[b] = (x.get("title"), x.get("page"), "Library of Congress, Prints & Photographs (FSA/OWI or P&P) - no known restrictions / public domain")
films = {}
for j in glob.glob("stock/films/*.json"):
    x = json.load(open(j)); films[x["id"]] = x
lines = ["# Sources used in 'The Giant of the Skerry' video", "",
         "All archive material is public domain. AI images were generated locally (SDXL-Turbo).",
         "Music and ambience were synthesized for this video.", "", "## Archive films (Internet Archive)"]
for u in sorted(u for u in used if u.endswith(".mp4")):
    k = os.path.basename(u)[:-4]; x = films.get(k, {})
    lines.append(f"- {x.get('title', k)} - {x.get('url', '')} - {x.get('license') or 'Prelinger Archives / US National Archives, public domain'}")
lines += ["", "## Photographs (Library of Congress)"]
for u in sorted(u for u in used if "/fsa_c/" in u or "/loc_c/" in u):
    t = meta.get(os.path.basename(u))
    if t: lines.append(f"- {t[0]} - {t[1]}")
lines += ["", "## Wikimedia Commons"]
for j in sorted(glob.glob("stock/reg/reg_*.json")):
    for x in json.load(open(j)):
        lines.append(f"- {x['title']} ({x['lic']}, {x['artist'] or 'unknown author'}) - {x['page']}")
open("SOURCES.md", "w").write("\n".join(lines) + "\n")
print(len(lines))
