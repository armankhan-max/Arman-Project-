import json, math, sys, subprocess, random, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1280, 720, 24
DUR = 2093.1
D = os.path.dirname(os.path.abspath(__file__))
F_BEBAS = D + "/fonts/7fb78b.ttf"; F_OSW = D + "/fonts/092e85.ttf"
F_PLAY = D + "/fonts/b8a6dc.ttf"; F_TYPE = D + "/fonts/c33104.ttf"
GOLD = (212, 170, 92); CREAM = (236, 230, 216)
TR = json.load(open(D + "/transcript.json"))
SEGSTARTS = [s["s"] for s in TR]

_imgs = {}
def IMG(k):
    if k not in _imgs:
        _imgs[k] = Image.open(f"{D}/img/{k}.jpg").convert("RGB")
    return _imgs[k]
_fonts = {}
def FONT(p, s):
    if (p, s) not in _fonts: _fonts[(p, s)] = ImageFont.truetype(p, s)
    return _fonts[(p, s)]

def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)

# ------------------------------------------------------------ story ranges
R = [  # start, pool, steam
 (0,    ["e115b136","0904ebe5","54d411da","f597a17f","04b91edb"], 0),
 (25,   ["dae0d14e","35a2aeac","fc1069f6","0904ebe5"], 1),
 (39.8, ["10b2ffd8","e9cf60b1","834f097e","ea2e6c8b"], 0),
 (54,   ["5c22916c","ebc885b7","53159461","037a1aa1"], 0),
 (73,   ["02f8d8fa","e86ea8bd","dae0d14e","65a9ab2a","56393b8b"], 1),
 (88,   ["56393b8b","02f8d8fa","c079b40a","037a1aa1"], 1),
 (110,  ["53159461","5c22916c","2dde5428","dfbc66d6"], 0),
 (128,  ["d8ac389c","2dde5428"], 0),
 (143,  ["e9cf60b1","10b2ffd8"], 0),
 (159,  ["f597a17f","e115b136"], 0),
 (172,  ["fd11570c","436811a2","ea2e6c8b"], 1),
 (183,  ["10b2ffd8","e9cf60b1"], 0),
 (198,  ["e86ea8bd","65a9ab2a","c079b40a"], 1),
 (226,  ["5e4f424e","e86ea8bd","02f8d8fa"], 1),
 (245,  ["dfbc66d6","65a9ab2a","e9cf60b1"], 1),
 (261,  ["7fb7353c","2dde5428","dfbc66d6"], 0),
 (284,  ["0904ebe5","54d411da","fc1069f6","7fb7353c"], 0),
 (343,  ["e115b136","f597a17f","04b91edb","35a2aeac"], 0),
 (412,  ["04b91edb","f597a17f","0904ebe5"], 0),
 (437,  ["31dcc152","4252c9d9"], 0),
 (463,  ["35a2aeac","dae0d14e","fc1069f6"], 1),
 (498,  ["fc1069f6","c8dd9e68","4097dda3"], 1),
 (511,  ["4097dda3","057c1571","c8dd9e68"], 0),
 (531,  ["27b006cb","bc816ed9","4252c9d9"], 0),
 (570,  ["4252c9d9","f597a17f","35a2aeac"], 0),
 (616,  ["614e8345","0904ebe5","037a1aa1"], 0),
 (657,  ["5c22916c","10b2ffd8","614e8345","53159461"], 0),
 (674,  ["614e8345","4252c9d9","e115b136","31dcc152"], 0),
 (702,  ["037a1aa1","ee043a31","e9cf60b1"], 0),
 (724,  ["834f097e","f597a17f","ea2e6c8b"], 0),
 (737,  ["fd11570c","436811a2","ea2e6c8b","5e4f424e"], 1),
 (769,  ["834f097e","ea2e6c8b","fd11570c"], 0),
 (783,  ["ee043a31","037a1aa1","614e8345"], 0),
 (807,  ["4497f331","436811a2","5e4f424e","f5ba18ec"], 1),
 (838,  ["ea2e6c8b","834f097e","4497f331"], 0),
 (848,  ["436811a2","f5ba18ec","5e4f424e","4497f331"], 1),
 (872,  ["ea2e6c8b","5e4f424e","4497f331"], 1),
 (891,  ["c8dd9e68","4097dda3","5e4f424e","fc1069f6"], 1),
 (926,  ["27b006cb","ee043a31","0904ebe5"], 0),
 (933,  ["d8ac389c","2dde5428","7fb7353c"], 0),
 (967,  ["2dde5428","ee043a31","568091e2"], 0),
 (993,  ["568091e2","7fb7353c","0904ebe5"], 1),
 (1006, ["394b9374","27b006cb","2fabc34f"], 0),
 (1026, ["f5ba18ec","2fabc34f","fc1069f6"], 1),
 (1039, ["8cb01cb3","c8dd9e68","394b9374"], 1),
 (1063, ["2fabc34f","bc816ed9","568091e2"], 0),
 (1077, ["53159461","feaeb64f"], 0),
 (1082, ["feaeb64f"], 0),
 (1094, ["5c22916c","ebc885b7","feaeb64f"], 0),
 (1110, ["ec1dd03d","5c22916c"], 1),
 (1143, ["53159461","5e4f424e","fd11570c","c8dd9e68"], 1),
 (1167, ["834f097e","ea2e6c8b","ec1dd03d"], 0),
 (1198, ["ebc885b7","5c22916c","037a1aa1","53159461"], 0),
 (1233, ["e9cf60b1","dfbc66d6","10b2ffd8"], 0),
 (1258, ["037a1aa1","e86ea8bd","dfbc66d6"], 0),
 (1295, ["dfbc66d6","65a9ab2a","7fb7353c"], 1),
 (1320, ["65a9ab2a","c8dd9e68","fc1069f6"], 1),
 (1365, ["0904ebe5","54d411da","04b91edb"], 0),
 (1393, ["0904ebe5","394b9374","ee043a31","614e8345"], 0),
 (1439, ["2fabc34f","dfbc66d6","568091e2"], 1),
 (1478, ["04b91edb","2fabc34f","35a2aeac"], 0),
 (1507, ["27b006cb","bc816ed9","2fabc34f"], 0),
 (1538, ["bc816ed9","27b006cb","e9cf60b1"], 0),
 (1557, ["e9cf60b1","037a1aa1","c079b40a","53159461"], 0),
 (1578, ["dfbc66d6","c079b40a","e86ea8bd"], 1),
 (1592, ["10b2ffd8","834f097e"], 0),
 (1604, ["5c22916c","bc816ed9","834f097e"], 0),
 (1636, ["d8ac389c","e9cf60b1","f597a17f","fd11570c","e86ea8bd","10b2ffd8"], 0),
 (1675, ["04b91edb","31dcc152","27b006cb","35a2aeac","4097dda3","4252c9d9"], 0),
 (1706, ["614e8345","037a1aa1","834f097e","e9cf60b1","ea2e6c8b","436811a2"], 0),
 (1762, ["dfbc66d6","65a9ab2a","0904ebe5","2fabc34f"], 0),
 (1796, ["e115b136","4097dda3","f5ba18ec","5e4f424e","27b006cb","bc816ed9"], 0),
 (1842, ["394b9374","2fabc34f","8cb01cb3","f5ba18ec","feaeb64f"], 0),
 (1889, ["0904ebe5","27b006cb","54d411da","bc816ed9"], 0),
 (1933, ["31dcc152","04b91edb","0904ebe5"], 0),
 (1963, ["5c22916c","ebc885b7","53159461"], 0),
 (1977, ["ee043a31","dfbc66d6","568091e2"], 0),
 (2029, ["2fabc34f","0904ebe5","27b006cb","54d411da","7fb7353c"], 0),
 (2057, ["10b2ffd8","834f097e","e9cf60b1","ea2e6c8b","dfbc66d6"], 0),
]

# full-frame graphics: (start, end, kind, data)
GFX = [
 (30.0, 39.6, "thermo", {}),
 (51.6, 58.1, "title", {"t": "THE CARSON RIDGE STAIR", "s": "A CASE BUILT FROM LEDGERS, TIME BOOKS & LETTERS"}),
 (122.0, 128.6, "grid", {"names": [("d8ac389c","DECLAN VOSS","Miner"),("e9cf60b1","A. LINDQVIST","Night Foreman"),("f597a17f","EDMUND HALE","Surveyor"),("fd11570c","SILAS PENHALE","Pump Engineer")]}),
 (376.5, 404.0, "stats", {}),
 (466.5, 481.0, "thermo", {}),
 (577.0, 616.0, "formula", {}),
 (813.5, 838.0, "sump", {}),
 (1636.3, 1648.0, "grid", {"names": [("d8ac389c","1876","Voss · the landing"),("f597a17f","1876","Hale · the notebook"),("fd11570c","1876","Penhale · the letters"),("dfbc66d6","1881","Hartman · the daybook")]}),
 (2066.0, 2093.1, "end", {}),
]
# overlays: (start, end, kind, data)
OV = [
 (0.3, 5.0, "type", {"t": "1,400 FEET BELOW CARSON RIDGE", "pos": "bl"}),
 (17.0, 25.0, "big", {"t": "30 FEET TALL"}),
 (58.3, 65.0, "loc", {"a": "CARSON RIDGE, NEVADA", "b": "1876"}),
 (73.3, 79.5, "chapter", {"n": "CHAPTER ONE", "t": "THE HOT GROUND"}),
 (83.0, 88.0, "type", {"t": "ROCK: 110°F", "pos": "bl"}),
 (91.7, 97.3, "type", {"t": "3 GALLONS OF ICE WATER · PER MAN · PER SHIFT", "pos": "bl"}),
 (110.6, 118.0, "loc", {"a": "THE ALDER QUEEN MINE", "b": "1,400 FT LEVEL · SUMMER 1876"}),
 (129.0, 137.0, "lower", {"a": "DECLAN VOSS", "b": "Miner · County Mayo · age 28"}),
 (143.6, 151.0, "lower", {"a": "ANDERS LINDQVIST", "b": "Night Foreman · keeper of the time book"}),
 (159.6, 167.0, "lower", {"a": "EDMUND HALE", "b": "Company Surveyor · trained in Germany"}),
 (172.8, 180.0, "lower", {"a": "SILAS PENHALE", "b": "Pump Engineer · Cornwall"}),
 (183.8, 190.0, "chapter", {"n": "CHAPTER TWO", "t": "THE FACE BREAKS"}),
 (191.0, 198.0, "type", {"t": "AUG. 9, 1876 - 10 HRS. EAST DRIFT. HOT WATER. FACE CUT.", "pos": "bl"}),
 (218.2, 225.0, "lower", {"a": "OWEN PRICE", "b": "Miner · Wales"}),
 (250.6, 254.4, "type", {"t": "WATER GONE. FACE OPEN. AIR COMING OUT OF IT.", "pos": "c"}),
 (254.5, 261.5, "cold", {"t": "COLD."}),
 (297.6, 305.0, "type", {"t": "EVERY STEP - HIP HIGH", "pos": "bl"}),
 (343.3, 350.5, "chapter", {"n": "CHAPTER THREE", "t": "THE SURVEYOR"}),
 (437.2, 444.0, "type", {"t": "A POLISHED GROOVE · 16 FEET ABOVE THE TREADS", "pos": "bl"}),
 (447.5, 453.6, "big", {"t": "A HANDRAIL"}),
 (491.3, 498.0, "type", {"t": "THE CANDLE FLAME LEANED - LIKE A BREATH", "pos": "bl"}),
 (513.1, 521.0, "type", {"t": "300 FT OF LINE · NO BOTTOM", "pos": "bl"}),
 (538.2, 547.5, "type", {"t": "TOP LANDING · 8 NICHES · SOOT-BLACKENED", "pos": "bl"}),
 (569.3, 573.5, "cold", {"t": "LIGHTS."}),
 (616.2, 623.0, "lower", {"a": "HORACE TEAGUE", "b": "Superintendent · Alder Queen Mine"}),
 (634.7, 645.0, "type", {"t": "OFFICIAL REPORT: 'AN OLD HOT WATER COURSE ... RECOMMEND A BULKHEAD AT ONCE.'", "pos": "bl"}),
 (690.5, 694.5, "quote", {"t": "Steps do not form.\nSteps are cut.", "b": "Stufen entstehen nicht. Stufen werden gehauen."}),
 (699.6, 702.4, "quote", {"t": "A handrail is for a hand.\nWhose?", "b": ""}),
 (702.4, 710.5, "type", {"t": "AUGUST 21, 1876 - THE BULKHEAD GOES UP", "pos": "bl"}),
 (730.5, 736.5, "type", {"t": "THE ORIGINAL NOTEBOOK - MAILED TO GERMANY", "pos": "bl"}),
 (737.0, 744.0, "chapter", {"n": "CHAPTER FOUR", "t": "THE WATER THAT BREATHED"}),
 (744.8, 752.0, "lower", {"a": "SILAS PENHALE", "b": "Pump Engineer · 30 years in wet mines"}),
 (780.8, 786.0, "type", {"t": "LETTER No. 10 - OCTOBER 2nd, 1876", "pos": "bl"}),
 (842.8, 848.2, "quote", {"t": "\"Water does not breathe.\nThis breathed.\"", "b": "- Silas Penhale, letter to his brother"}),
 (853.5, 860.0, "type", {"t": "AGAIN ON THE 4th. AGAIN ON THE 7th.", "pos": "bl"}),
 (878.4, 891.0, "quote", {"t": "\"Something below is taking a big breath\nand letting it out.\"", "b": "- letter No. 11"}),
 (962.2, 970.0, "chapter", {"n": "CHAPTER FIVE", "t": "THE ROPE"}),
 (967.5, 974.0, "type", {"t": "OCTOBER 25th, 1876 · NIGHT", "pos": "bl"}),
 (1021.0, 1026.0, "quote", {"t": "\"I wanted to know\nif someone was waiting.\"", "b": "- Declan Voss"}),
 (1027.9, 1034.0, "type", {"t": "2:00 A.M.", "pos": "c"}),
 (1082.0, 1093.0, "type", {"t": "SHIFT BOOK: 'CAME UP WITH WHITE IN HIS HAIR AT BOTH TEMPLES.'", "pos": "bl"}),
 (1110.0, 1117.0, "chapter", {"n": "CHAPTER SIX", "t": "THE FIRE"}),
 (1128.8, 1135.0, "type", {"t": "31 BLOCKS GONE", "pos": "bl"}),
 (1189.0, 1198.0, "quote", {"t": "\"The water went up before the fire went out.\nIt did not rise. It was lifted.\"", "b": "- Silas Penhale"}),
 (1198.8, 1206.0, "chapter", {"n": "CHAPTER SEVEN", "t": "FROM BELOW"}),
 (1224.4, 1232.0, "lower", {"a": "GUS HARTMAN", "b": "Tunnel Foreman · German-born · age 44"}),
 (1264.0, 1270.0, "type", {"t": "MARCH 14th, 1881", "pos": "bl"}),
 (1272.2, 1279.5, "type", {"t": "BROKE TO OPEN SPACE AT FACE. AIR COLD. NO WATER. FLOOR LEVEL. DRESSED STONE.", "pos": "c"}),
 (1365.4, 1371.0, "type", {"t": "MARCH 16th · 200 PACES ACROSS THE BASIN", "pos": "bl"}),
 (1388.0, 1393.0, "cold", {"t": "52."}),
 (1436.3, 1439.2, "big", {"t": "52 STEPS"}),
 (1443.8, 1452.0, "type", {"t": "MARCH 17th - A DOOR IN THE SOUTH WALL. TALLER THAN MY LAMP.", "pos": "bl"}),
 (1459.3, 1465.0, "cold", {"t": "NOT OURS."}),
 (1557.3, 1563.0, "type", {"t": "MARCH 18th - CREW REFUSED THE SHIFT.", "pos": "bl"}),
 (1597.0, 1604.0, "quote", {"t": "\"I have closed the tunnel face with timber.\nI will not write why.\"", "b": "- Gus Hartman"}),
 (1628.0, 1636.0, "quote", {"t": "\"Tell them the lamp in the sixth niche\nwas still warm.\"", "b": "- Gus Hartman, letter to his daughter"}),
 (1675.3, 1683.0, "type", {"t": "52 STEPS · RISER 36 IN · TREAD 60 IN", "pos": "bl"}),
 (1687.3, 1693.0, "type", {"t": "AIR 58°F · ROCK 118°F", "pos": "bl"}),
 (1703.0, 1706.0, "big", {"t": "30 FEET TALL"}),
 (1883.0, 1889.0, "quote", {"t": "\"...the lamp in the sixth niche\nwas still warm.\"", "b": ""}),
 (1899.3, 1904.0, "quote", {"t": "Why would anyone light\nthe top of a stair?", "b": ""}),
 (1911.3, 1917.0, "type", {"t": "YOU LIGHT IT FOR THE ONE WHO IS COMING UP", "pos": "c"}),
 (1958.3, 1963.0, "quote", {"t": "You do not wear polish into stone by visiting.\nYou wear it by living there.", "b": ""}),
 (1977.3, 1987.0, "type", {"t": "1952 - STATE GEOLOGIST: IRON GATE, PADLOCKED FROM OUTSIDE", "pos": "bl"}),
 (1995.3, 2002.0, "type", {"t": "1998 - GATE FOUND OPEN. SHACKLE CUT CLEAN.", "pos": "bl"}),
 (2008.3, 2014.0, "type", {"t": "11 DAYS LATER - WELD CRACKED FROM THE INSIDE", "pos": "bl"}),
 (2023.3, 2029.0, "cold", {"t": "NOBODY HAS OPENED IT SINCE."}),
 (2050.3, 2057.0, "quote", {"t": "For somebody who was not us.\nAnd who has not come home yet.", "b": ""}),
]

# ------------------------------------------------------------ shot list
def build_shots():
    rng = random.Random(7)
    bounds = [r[0] for r in R] + [DUR]
    shots = []; use = {}
    for i, (s, pool, steam) in enumerate(R):
        e = bounds[i + 1]
        cuts = [s]
        t = s
        while e - t > 9.5:
            cands = [x for x in SEGSTARTS if t + 5.0 <= x <= t + 9.0 and x < e - 3]
            nt = min(cands, key=lambda x: abs(x - (t + 7))) if cands else t + 7.5
            cuts.append(nt); t = nt
        cuts.append(e)
        for j in range(len(cuts) - 1):
            k = pool[j % len(pool)]
            n = use.get(k, 0); use[k] = n + 1
            mv = rng.choice(["in", "out", "pl", "pr", "in", "out"])
            if n == 0: z0, fx, fy = 1.0, 0.5, 0.5
            else: z0 = 1.12 + min(n, 5) * 0.05; fx, fy = rng.uniform(.3, .7), rng.uniform(.3, .65)
            shots.append(dict(s=cuts[j], e=cuts[j + 1], k=k, mv=mv, z=z0, fx=fx, fy=fy, steam=steam))
    return shots
SHOTS = build_shots()

def crop_rect(sh, t):
    d = sh["e"] - sh["s"]; p = (t - sh["s"]) / max(d, .01); p = min(max(p, 0), 1.2)
    z = sh["z"]; mv = sh["mv"]
    if mv == "in": zz = z * (1 + 0.14 * p); cx, cy = sh["fx"], sh["fy"]
    elif mv == "out": zz = z * (1.14 - 0.14 * p); cx, cy = sh["fx"], sh["fy"]
    else:
        zz = z * 1.12; a = 0.5 - 0.08 + 0.16 * p if mv == "pr" else 0.5 + 0.08 - 0.16 * p
        cx, cy = a + (sh["fx"] - .5), sh["fy"]
    cw, ch = 1600 / zz, 900 / zz
    x0 = min(max(cx * 1600 - cw / 2, 0), 1600 - cw); y0 = min(max(cy * 900 - ch / 2, 0), 900 - ch)
    return x0, y0, cw, ch

def render_img(k, rect, jx=0, jy=0):
    x0, y0, cw, ch = rect
    sx, sy = cw / W, ch / H
    im = IMG(k).transform((W, H), Image.AFFINE, (sx, 0, x0 + jx, 0, sy, y0 + jy), resample=Image.BILINEAR)
    return np.asarray(im).astype(np.float32)

# ------------------------------------------------------------ textures
rs = np.random.default_rng(1)
GRAIN = []
for i in range(24):
    g = rs.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    g = np.asarray(Image.fromarray((g * 30 + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32) - 128
    GRAIN.append(g * 0.55)
def make_smoke():
    acc = np.zeros((H * 2, W), np.float32)
    for sc, wt in [(8, 1.0), (16, .6), (32, .35), (64, .2)]:
        n = rs.random((H * 2 // (256 // sc) + 2, W // (256 // sc) + 2)).astype(np.float32)
        im = Image.fromarray((n * 255).astype(np.uint8)).resize((W, H * 2), Image.BICUBIC)
        acc += np.asarray(im).astype(np.float32) / 255 * wt
    acc = acc / acc.max(); acc = np.clip((acc - 0.45) * 2.2, 0, 1)
    return np.asarray(Image.fromarray((acc * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18))).astype(np.float32) / 255
SMOKE = make_smoke()
yy, xx = np.mgrid[0:H, 0:W]
VIG = 1.12 * (1 - 0.26 * (((xx / W - .5) ** 2) * 1.2 + ((yy / H - .5) ** 2) * 1.8) * 2.2).clip(0.5, 1).astype(np.float32)[..., None]

_th = {}
def _thumb(k, w, h):
    if (k, w) not in _th: _th[(k, w)] = np.asarray(IMG(k).resize((w, h), Image.BILINEAR)).astype(np.float32)
    return _th[(k, w)]

def dark_bg(k, t, dim=0.35, blur=True):
    if blur and k + "_b" not in _imgs: _imgs[k + "_b"] = IMG(k).filter(ImageFilter.GaussianBlur(4))
    a = render_img(k + "_b" if blur else k, (100 + 30 * math.sin(t * .05), 60, 1400, 787.5))
    return a * dim

# ------------------------------------------------------------ text helpers
def tlayer(size=(W, H)): return Image.new("RGBA", size, (0, 0, 0, 0))
def comp(base, layer, alpha=1.0):
    bb = layer.getbbox()
    if not bb or alpha <= 0: return base
    x0, y0, x1, y1 = bb
    a = np.asarray(layer.crop(bb)).astype(np.float32)
    al = a[..., 3:4] * (alpha / 255)
    reg = base[y0:y1, x0:x1]
    base[y0:y1, x0:x1] = reg + (a[..., :3] - reg) * al
    return base
def shadow_text(d, xy, txt, font, fill, anchor="la", sh=3):
    d.text((xy[0] + sh, xy[1] + sh), txt, font=font, fill=(0, 0, 0, 170), anchor=anchor)
    d.text(xy, txt, font=font, fill=fill, anchor=anchor)

_g = np.linspace(0, 1, H)[:, None, None].astype(np.float32)
GR1 = np.clip((_g - 0.62) * 2.6, 0, 1); GR2 = np.clip((_g - 0.55) * 2.2, 0, 1); GR3 = np.clip((_g - 0.7) * 3, 0, 1)
_cache = {}
def ov_layer(o):
    key = id(o)
    if key in _cache: return _cache[key]
    s, e, kind, dat = o
    L = tlayer(); d = ImageDraw.Draw(L); extra = {}
    if kind == "lower":
        fa = FONT(F_OSW, 44); fb = FONT(F_PLAY, 30)
        d.rectangle((90, 560, 118, 565), fill=GOLD + (255,))
        shadow_text(d, (134, 538), dat["a"], fa, CREAM + (255,))
        shadow_text(d, (136, 600), dat["b"], fb, (236, 228, 210, 255), sh=2)
        extra["w"] = 160 + max(fa.getlength(dat["a"]), fb.getlength(dat["b"]))
    elif kind == "chapter":
        fn = FONT(F_OSW, 24); ft = FONT(F_BEBAS, 96)
        shadow_text(d, (W / 2, 300), "·  " + dat["n"] + "  ·", fn, GOLD + (255,), "mm", 2)
        shadow_text(d, (W / 2, 372), dat["t"], ft, CREAM + (255,), "mm", 4)
        extra["uw"] = ft.getlength(dat["t"])
    elif kind == "loc":
        fa = FONT(F_BEBAS, 64); fb = FONT(F_OSW, 26)
        shadow_text(d, (90, 520), dat["a"], fa, CREAM + (255,))
        shadow_text(d, (92, 600), dat["b"], fb, GOLD + (255,), sh=2)
        extra["w"] = fa.getlength(dat["a"]) + 20
    elif kind == "big":
        ft = FONT(F_BEBAS, 120)
        shadow_text(d, (W / 2, H / 2), dat["t"], ft, CREAM + (255,), "mm", 5)
        extra["uw"] = ft.getlength(dat["t"])
    elif kind == "cold":
        ft = FONT(F_BEBAS, 150 if len(dat["t"]) < 10 else 96)
        shadow_text(d, (W / 2, H / 2), dat["t"], ft, CREAM + (255,), "mm", 5)
        extra["uw"] = ft.getlength(dat["t"])
    elif kind == "quote":
        fq = FONT(F_PLAY, 46); fb = FONT(F_OSW, 22)
        lines = dat["t"].split("\n"); y = H / 2 - (len(lines) - 1) * 32 - (14 if dat["b"] else 0)
        for ln in lines:
            shadow_text(d, (W / 2, y), ln, fq, CREAM + (255,), "mm", 3); y += 64
        if dat["b"]:
            d.rectangle((W / 2 - 20, y - 8, W / 2 + 20, y - 5), fill=GOLD + (255,))
            shadow_text(d, (W / 2, y + 22), dat["b"], fb, GOLD + (255,), "mm", 2)
    elif kind == "type":
        txt = dat["t"]; sz = 34 if len(txt) < 40 else 26
        f = FONT(F_TYPE, sz); extra["f"] = f
        if dat["pos"] == "c":
            # wrap
            words = txt.split(); lines = [""]
            for wd in words:
                if f.getlength(lines[-1] + " " + wd) > 980: lines.append(wd)
                else: lines[-1] = (lines[-1] + " " + wd).strip()
            extra["lines"] = lines
        else: extra["lines"] = [txt]
    _cache[key] = (L, extra)
    return _cache[key]

def apply_overlay(fr, o, t):
    s, e, kind, dat = o
    L, ex = ov_layer(o)
    p = t - s; rem = e - t
    fade = min(1, p / 0.5, rem / 0.5)
    if kind == "lower":
        a = ease(p / 0.7) * min(1, rem / 0.6)
        wv = int(ex["w"] * ease(p / 0.9)) + 90
        M = np.zeros((1, W, 1), np.float32); M[:, :min(W, wv)] = 1
        dx = int((1 - ease(p / 0.7)) * -30)
        Ls = L if dx == 0 else L.transform(L.size, Image.AFFINE, (1, 0, -dx, 0, 1, 0))
        arr = np.asarray(Ls).astype(np.float32); al = arr[..., 3:4] / 255 * a * M
        # dark gradient behind
        fr[440:] *= (1 - GR1[440:] * 0.55 * a)
        return fr * (1 - al) + arr[..., :3] * al
    if kind in ("chapter", "big", "cold"):
        dim = 0.55 if kind == "chapter" else 0.4
        fr = fr * (1 - dim * fade)
        sc = 1.0 + 0.03 * (p / (e - s))
        Ls = L.resize((int(W * sc), int(H * sc)), Image.BILINEAR).crop((int(W * (sc - 1) / 2), int(H * (sc - 1) / 2), int(W * (sc - 1) / 2) + W, int(H * (sc - 1) / 2) + H)) if kind != "chapter" else L
        fr = comp(fr, Ls, fade)
        uw = ex["uw"] * ease((p - 0.3) / 0.9)
        if uw > 2:
            y = 430 if kind == "chapter" else H // 2 + (95 if kind == "cold" and ex["uw"] < 700 else 70)
            x0 = int(W / 2 - ex["uw"] / 2)
            fr[y:y + 4, x0:x0 + int(uw)] = fr[y:y + 4, x0:x0 + int(uw)] * (1 - fade) + np.array(GOLD, np.float32) * fade
        return fr
    if kind == "loc":
        a = fade
        wv = int(ex["w"] * ease(p / 1.0)) + 90
        M = np.zeros((1, W, 1), np.float32); M[:, :wv] = 1
        arr = np.asarray(L).astype(np.float32); al = arr[..., 3:4] / 255 * a * M
        fr[390:] *= (1 - GR2[390:] * 0.6 * a)
        uw = int(ex["w"] * ease((p - .4) / 1.0))
        if uw > 2: fr[592:595, 90:90 + uw] = fr[592:595, 90:90 + uw] * (1 - a) + np.array(GOLD, np.float32) * a
        return fr * (1 - al) + arr[..., :3] * al
    if kind == "quote":
        fr = fr * (1 - 0.6 * fade)
        return comp(fr, L, fade)
    if kind == "type":
        f = ex["f"]; lines = ex["lines"]
        n = int(p * 24)  # chars revealed
        Lt = tlayer(); d = ImageDraw.Draw(Lt)
        if dat["pos"] == "bl":
            fr[500:] *= (1 - GR3[500:] * 0.5 * fade)
            txt = lines[0][:n]
            shadow_text(d, (90, 630), txt, f, (232, 226, 210, 255), sh=2)
            if n < len(lines[0]) and int(t * 3) % 2 == 0:
                x = 90 + f.getlength(txt); d.rectangle((x + 3, 606, x + 15, 640), fill=GOLD + (255,))
        else:
            fr = fr * (1 - 0.5 * fade)
            y = H / 2 - (len(lines) - 1) * 26; c = n
            for ln in lines:
                shadow_text(d, (W / 2 - f.getlength(ln) / 2, y), ln[:max(0, c)], f, (232, 226, 210, 255), "lm", 2)
                c -= len(ln); y += 52
        return comp(fr, Lt, fade)
    return fr

# ------------------------------------------------------------ graphics scenes
def gfx_frame(g, t):
    s, e, kind, dat = g
    p = t - s
    if kind == "thermo":
        fr = dark_bg("dae0d14e", t, 0.3)
        L = tlayer(); d = ImageDraw.Draw(L)
        for i, (lab, val, x) in enumerate([("THE ROCK", 118, 420), ("THE AIR ON THE STAIR", 58, 860)]):
            d.rounded_rectangle((x - 22, 140, x + 22, 560), 22, outline=CREAM + (220,), width=3)
            d.ellipse((x - 38, 540, x + 38, 616), outline=CREAM + (220,), width=3)
            col = (165, 85, 62, 255) if i == 0 else (105, 135, 160, 255)
            d.ellipse((x - 30, 548, x + 30, 608), fill=col)
            prog = ease((p - 0.4 - i * 1.6) / 2.2); v = val * prog
            top = 548 - (v / 130) * 400
            d.rectangle((x - 10, top, x + 10, 560), fill=col)
            for tk in range(0, 131, 10):
                yy_ = 548 - tk / 130 * 400; d.line((x + 26, yy_, x + 40, yy_), fill=CREAM + (160,), width=2)
            shadow_text(d, (x, 100), lab, FONT(F_OSW, 28), GOLD + (255,), "mm", 2)
            shadow_text(d, (x + 70, top), f"{int(round(v))}°F", FONT(F_BEBAS, 72), CREAM + (255,), "lm", 3)
        if p > 5.5:
            a = min(1, (p - 5.5) / .6)
            shadow_text(d, (W / 2, 670), "THE HOTTEST MINE ON THE RIDGE · THE ONLY COLD STAIR", FONT(F_OSW, 26), (236, 230, 216, int(255 * a)), "mm", 2)
        return comp(fr, L)
    if kind == "title":
        fr = dark_bg("0904ebe5", t, 0.42, blur=False)
        L = tlayer(); d = ImageDraw.Draw(L)
        sc = 1 + 0.02 * p
        ft = FONT(F_BEBAS, int(118 * sc))
        a = ease(p / 1.2)
        shadow_text(d, (W / 2, H / 2 - 20), dat["t"], ft, (236, 230, 216, int(255 * a)), "mm", 5)
        shadow_text(d, (W / 2, H / 2 + 80), dat["s"], FONT(F_OSW, 24), GOLD + (int(255 * ease((p - 1.2) / 1)),), "mm", 2)
        fr = comp(fr, L)
        uw = int(ft.getlength(dat["t"]) * ease((p - 0.6) / 1.2)); x0 = int(W / 2 - ft.getlength(dat["t"]) / 2)
        if uw > 2: fr[H // 2 + 42:H // 2 + 46, x0:x0 + uw] = GOLD
        return fr
    if kind == "grid":
        fr = np.full((H, W, 3), 14, np.float32)
        for gx in range(0, W, 125): fr[:, gx:gx + 1] = 70
        for gy in range(0, H, 125): fr[gy:gy + 1, :] = 70
        names = dat["names"]; n = len(names)
        pw, ph = 330, 186; gap = 40
        total = n * pw + (n - 1) * gap
        off = 80 - p * 18
        for i, (k, a, b) in enumerate(names):
            ap = ease((p - i * 0.6) / 0.8)
            if ap <= 0: continue
            x = int(W / 2 - total / 2 + i * (pw + gap) + off * 0.5 * (i - 1.5) / 1.5)
            y = int(250 + (1 - ap) * 40)
            im = _thumb(k, pw, ph)
            reg = fr[y - 6:y + ph + 6, x - 6:x + pw + 6]
            if reg.shape[0] != ph + 12 or reg.shape[1] != pw + 12: continue
            gold = np.array([190, 140, 80], np.float32)
            reg[:] = reg * (1 - ap) + gold * ap
            reg[6:6 + ph, 6:6 + pw] = reg[6:6 + ph, 6:6 + pw] * (1 - ap) + im * ap
            L = tlayer(); d = ImageDraw.Draw(L)
            shadow_text(d, (x + pw / 2, y + ph + 40), a, FONT(F_BEBAS, 40), CREAM + (int(255 * ap),), "mm", 2)
            shadow_text(d, (x + pw / 2, y + ph + 74), b, FONT(F_PLAY, 22), GOLD + (int(255 * ap),), "mm", 2)
            fr = comp(fr, L)
        return fr
    if kind == "stats":
        fr = dark_bg("04b91edb", t, 0.32)
        L = tlayer(); d = ImageDraw.Draw(L)
        items = [(0, "52", "STEPS · COUNTED TWICE"), (3.5, "156 FT", "STRAIGHT DOWN · NO TURNS"), (18.0, "36 IN", "EVERY RISER"), (20.7, "60 IN", "EVERY TREAD"), (25.0, "0.5 IN", "MAX ERROR · NINE STEPS MEASURED")]
        y = 110
        for (ts, big, small) in items:
            a = ease((p - ts) / 0.8)
            if a > 0:
                shadow_text(d, (330 - (1 - a) * 30, y), big, FONT(F_BEBAS, 84), CREAM + (int(255 * a),), "ra", 4)
                shadow_text(d, (370, y + 30), small, FONT(F_OSW, 30), GOLD + (int(255 * a),), "la", 2)
            y += 112
        return comp(fr, L)
    if kind == "formula":
        fr = dark_bg("4252c9d9", t, 0.28)
        L = tlayer(); d = ImageDraw.Draw(L)
        rows = [(0, F_PLAY, 34, "A rule for stairs - written down 200 years ago", GOLD),
                (7.2, F_BEBAS, 76, "2 × RISER  +  TREAD  =  STRIDE", CREAM),
                (10.0, F_OSW, 30, "an ordinary man  =  about 25 inches", (210, 204, 190)),
                (14.7, F_BEBAS, 76, "2 × 36  +  60  =  132 IN", CREAM),
                (19.9, F_BEBAS, 76, "A STRIDE OF 11 FEET", CREAM),
                (23.6, F_BEBAS, 120, "= 30 FEET TALL", (240, 205, 140))]
        y = 95
        for ts, fp, sz, txt, col in rows:
            a = ease((p - ts) / 0.9)
            if a > 0:
                shadow_text(d, (W / 2, y + (1 - a) * 15), txt, FONT(fp, sz), col + (int(255 * a),), "mm", 3)
            y += 92 if sz < 100 else 0
        fr = comp(fr, L)
        if p > 31.6:  # box around it
            a = ease((p - 31.6) / 0.8); bw = FONT(F_BEBAS, 120).getlength("= 30 FEET TALL") / 2 + 30
            x0, x1, y0, y1 = int(W / 2 - bw), int(W / 2 + bw), 600, 720 - 6
            yc = 555 + 92 * 0
            y0, y1 = 95 + 92 * 5 - 70, 95 + 92 * 5 + 70
            g = np.array(GOLD, np.float32)
            fr[y0:y0 + 3, x0:x1] = fr[y0:y0 + 3, x0:x1] * (1 - a) + g * a; fr[y1:y1 + 3, x0:x1] = fr[y1:y1 + 3, x0:x1] * (1 - a) + g * a
            fr[y0:y1, x0:x0 + 3] = fr[y0:y1, x0:x0 + 3] * (1 - a) + g * a; fr[y0:y1, x1:x1 + 3] = fr[y0:y1, x1:x1 + 3] * (1 - a) + g * a
        return fr
    if kind == "sump":
        fr = dark_bg("5e4f424e", t, 0.4)
        L = tlayer(); d = ImageDraw.Draw(L)
        x0, x1, ytop, ybot = 470, 810, 120, 620
        d.rectangle((x0, ytop, x1, ybot), outline=CREAM + (200,), width=3)
        for ft in range(0, 41, 5):
            yv = ybot - ft / 40 * (ybot - ytop); d.line((x1, yv, x1 + 18, yv), fill=CREAM + (180,), width=2)
            d.text((x1 + 26, yv), f"{ft} FT", font=FONT(F_OSW, 20), fill=CREAM + (200,), anchor="lm")
        # level: start 34, drop 19 over seconds 3..8, recover 18..24
        lv = 34 - 19 * ease((p - 3) / 5) + 19 * ease((p - 18.5) / 6)
        yv = ybot - lv / 40 * (ybot - ytop)
        d.rectangle((x0 + 3, yv, x1 - 3, ybot - 3), fill=(80, 95, 110, 210))
        d.line((x0 + 3, yv, x1 - 3, yv), fill=(200, 220, 235, 255), width=3)
        shadow_text(d, (x0 - 30, 160), "LOWEST SUMP", FONT(F_OSW, 28), GOLD + (255,), "ra", 2)
        shadow_text(d, (x0 - 30, 200), "~2:00 A.M.", FONT(F_BEBAS, 56), CREAM + (255,), "ra", 3)
        shadow_text(d, (x0 - 30, 260), "ENGINES OFF", FONT(F_OSW, 24), (210, 204, 190, 255), "ra", 2)
        dropped = 34 - lv
        if p > 3: shadow_text(d, (x0 - 30, 420), f"-{dropped:0.0f} FT", FONT(F_BEBAS, 96), (240, 205, 140, 255), "ra", 4)
        if p > 8.5: shadow_text(d, (x0 - 30, 490), "IN ABOUT ONE HOUR", FONT(F_OSW, 24), CREAM + (255,), "ra", 2)
        return comp(fr, L)
    if kind == "end":
        fr = dark_bg("27b006cb", t, 0.3, blur=False)
        L = tlayer(); d = ImageDraw.Draw(L)
        a = ease((p - 6) / 1.5)
        shadow_text(d, (W / 2, 300), "THE GIANT LEDGER", FONT(F_BEBAS, 110), CREAM + (int(255 * a),), "mm", 5)
        shadow_text(d, (W / 2, 385), "stories built from ledgers, time books & letters", FONT(F_PLAY, 32), GOLD + (int(255 * a),), "mm", 2)
        b = ease((p - 8) / 1)
        if b > 0:
            d.rounded_rectangle((W / 2 - 150, 450, W / 2 + 150, 510), 8, fill=(170, 40, 30, int(230 * b)))
            d.text((W / 2, 480), "SUBSCRIBE", font=FONT(F_OSW, 32), fill=(255, 255, 255, int(255 * b)), anchor="mm")
        fr = comp(fr, L)
        uw = int(560 * ease((p - 6.6) / 1.2))
        if uw > 2: fr[352:355, W // 2 - 280:W // 2 - 280 + uw] = GOLD
        if rem := (e - t) < 1.5: fr = fr * max(0, (e - t) / 1.5)
        return fr
    return np.zeros((H, W, 3), np.float32)

# ------------------------------------------------------------ frame
XF = 0.6  # crossfade
def shot_at(t):
    for i, sh in enumerate(SHOTS):
        if sh["s"] <= t < sh["e"]: return i
    return len(SHOTS) - 1

def frame(fi):
    t = fi / FPS
    rng = np.random.default_rng(fi)
    jx, jy = rng.normal(0, 0.35), rng.normal(0, 0.35)  # gate weave
    g = next((g for g in GFX if g[0] <= t < g[1]), None)
    if g is not None:
        fr = gfx_frame(g, t)
        p = t - g[0]
        if p < 0.4:  # fade from shot
            i = shot_at(g[0] - 0.01); sh = SHOTS[i]
            prev = render_img(sh["k"], crop_rect(sh, g[0]), jx, jy)
            fr = prev * (1 - p / 0.4) + fr * (p / 0.4)
    else:
        i = shot_at(t); sh = SHOTS[i]
        fr = render_img(sh["k"], crop_rect(sh, t), jx, jy)
        if i > 0 and t - sh["s"] < XF:
            pv = SHOTS[i - 1]
            pg = next((g for g in GFX if g[0] <= sh["s"] - 0.01 < g[1]), None)
            prev = gfx_frame(pg, sh["s"] - 0.01) if pg else render_img(pv["k"], crop_rect(pv, t), jx, jy)
            a = (t - sh["s"]) / XF; a = a * a * (3 - 2 * a)
            fr = prev * (1 - a) + fr * a
        if sh["steam"]:
            off = int((t * 22) % H)
            sm = SMOKE[off:off + H, :, None]
            fr = fr + sm * 70 * (0.8 + 0.2 * math.sin(t * 0.7))
    for o in OV:
        if o[0] <= t < o[1]: fr = apply_overlay(fr, o, t)
    # opening fade
    if t < 1.2: fr = fr * (t / 1.2)
    # flicker + vignette + grain
    fl = 1 + 0.035 * math.sin(fi * 1.7) * rng.random() + rng.normal(0, 0.012)
    fr = fr * fl * VIG + GRAIN[(fi * 7) % 24][..., None]
    if rng.random() < 0.04:  # occasional scratch
        x = rng.integers(0, W); fr[:, x:x + 1] += rng.uniform(-25, 30)
    if rng.random() < 0.15:
        for _ in range(rng.integers(1, 4)):
            x, y = rng.integers(10, W - 10), rng.integers(10, H - 10); r = rng.integers(1, 4)
            fr[y - r:y + r, x - r:x + r] = rng.choice([15, 220])
    return np.clip(fr, 0, 255).astype(np.uint8)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        for ts in sys.argv[2:]:
            Image.fromarray(frame(int(float(ts) * FPS))).save(f"{D}/still_{ts}.jpg", quality=88)
    else:
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for fi in range(a, b):
            p.stdin.write(frame(fi).tobytes())
            if fi % 1200 == 0: print(out, fi, flush=True)
        p.stdin.close(); p.wait()
