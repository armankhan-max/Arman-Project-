"""Download CC0 Poly Haven 3D models (glTF, 1k textures) into assets/models/<name>/."""
import json
import os
import sys
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "models")
MODELS = sys.argv[1:] or [
    "fir_tree_01", "pine_tree_01", "island_tree_02", "jacaranda_tree", "grass_medium_01", "grass_medium_02",
    "boulder_01", "rock_07", "namaqualand_boulder_02", "stone_fire_pit", "treasure_chest", "wooden_lantern_01",
    "Lantern_01", "marble_bust_01", "tree_stump_01", "fern_02", "dead_tree_trunk", "flower_gazania", "dandelion_01",
    "ship_pinnace", "moss_01", "brass_vase_01", "gothic_statue",
]


def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "asset-fetch"})
    with urllib.request.urlopen(req, timeout=300) as r, open(path, "wb") as f:
        f.write(r.read())


for m in MODELS:
    try:
        req = urllib.request.Request("https://api.polyhaven.com/files/" + m, headers={"User-Agent": "asset-fetch"})
        d = json.load(urllib.request.urlopen(req, timeout=60))
        g = d["gltf"]["1k"]["gltf"]
        base = os.path.join(ROOT, m)
        get(g["url"], os.path.join(base, m + ".gltf"))
        size = g.get("size", 0)
        for rel, inc in g.get("include", {}).items():
            get(inc["url"], os.path.join(base, rel))
            size += inc.get("size", 0)
        print("MODEL", m, round(size / 1e6, 1), "MB")
    except Exception as e:
        print("MODEL_FAIL", m, e)
