"""Download CC0 HDRIs and PBR textures from Poly Haven into assets/ (first valid candidate per slot)."""
import json
import os
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
HDRIS = {
    "day": ["kloofendal_48d_partly_cloudy_puresky", "kloofendal_43d_clear_puresky"],
    "sunset": ["belfast_sunset_puresky", "the_sky_is_on_fire", "kloppenheim_06_puresky"],
    "night": ["satara_night", "dikhololo_night", "moonlit_golf", "rogland_clear_night"],
}
TEX = {
    "grass": ["leafy_grass", "sparse_grass", "grass_path_2", "forrest_ground_01", "aerial_grass_rock"],
    "soil": ["brown_mud_02", "brown_mud_leaves_01", "dirt", "red_dirt_mud_01", "mud_forest"],
    "stone": ["rock_wall_08", "castle_wall_slates", "rock_face", "rock_06", "aerial_rocks_02"],
    "marble": ["marble_01", "white_plaster_02", "concrete_wall_008", "beige_wall_001"],
    "wood": ["wood_planks_dirt", "old_wood_floor", "brown_planks_03", "weathered_brown_planks", "dark_wood"],
    "paving": ["cobblestone_floor_08", "stone_tiles_02", "floor_tiles_06", "cobblestone_05", "paving_stones_01"],
    "rock": ["rock_boulder_dry", "rock_face_03", "cliff_side", "rock_05", "mossy_rock"],
    "fabric": ["fabric_pattern_07", "denim_fabric", "cotton_jersey", "hessian_230"],
}


def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return
    req = urllib.request.Request(url, headers={"User-Agent": "asset-fetch"})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())


def files(name):
    try:
        req = urllib.request.Request("https://api.polyhaven.com/files/" + name, headers={"User-Agent": "asset-fetch"})
        d = json.load(urllib.request.urlopen(req, timeout=60))
        return d if isinstance(d, dict) and ("hdri" in d or "Diffuse" in d) else None
    except Exception:
        return None


os.makedirs(os.path.join(ROOT, "hdri"), exist_ok=True)
os.makedirs(os.path.join(ROOT, "tex"), exist_ok=True)
for slot, cands in HDRIS.items():
    for c in cands:
        d = files(c)
        if d and "hdri" in d:
            get(d["hdri"]["2k"]["hdr"]["url"], os.path.join(ROOT, "hdri", slot + ".hdr"))
            print("HDRI", slot, c)
            break
    else:
        print("HDRI_MISSING", slot)
for slot, cands in TEX.items():
    for c in cands:
        d = files(c)
        if d and "Diffuse" in d and "nor_gl" in d:
            get(d["Diffuse"]["1k"]["jpg"]["url"], os.path.join(ROOT, "tex", slot + "_diff.jpg"))
            get(d["nor_gl"]["1k"]["jpg"]["url"], os.path.join(ROOT, "tex", slot + "_nor.jpg"))
            rk = "Rough" if "Rough" in d else None
            if rk:
                get(d[rk]["1k"]["jpg"]["url"], os.path.join(ROOT, "tex", slot + "_rough.jpg"))
            print("TEX", slot, c)
            break
    else:
        print("TEX_MISSING", slot)
