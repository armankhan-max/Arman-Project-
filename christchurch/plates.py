"""B-roll plate definitions for the Christchurch documentary.

Each plate builds one Blender scene and returns a list of camera shots; every shot is rendered to
build/plates/<plate>_<shot>.png (RGBA: sky is transparent so the compositor can add real cloudy skies).

Usage: python3 plates.py NAME [NAME ...] [--samples N] [--preview] [--skip-existing]
       python3 plates.py --all
"""
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bl_kit as K  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "plates")
FONT = os.path.join(HERE, "assets", "fonts", "Oswald.ttf")
PLATES = {}
pi = math.pi


def plate(fn):
    PLATES[fn.__name__] = fn
    return fn


def S(name, loc, look, lens=35, dof=None, fstop=5.6, sky=True, samples=None):
    return dict(name=name, loc=loc, look=look, lens=lens, dof=dof, fstop=fstop, sky=sky, samples=samples)


# ------------------------------------------------------------------ shared sets
SHOPS = ["CAFE", "BOOKS", "PHARMACY", "BAKERY", "JEWELLERS", "SHOES", "BANK", "FLORIST", "OPTOMETRIST", "TAKEAWAYS",
         "CLOTHING", "MUSIC", "LIQUOR", "BARBER", "DAIRY", "SPORTS", "ANTIQUES", "TRAVEL", "NEWSAGENT", "GIFTS"]


def shop_row(y_front, x0, x1, mats, seed=0, facing=-1, floors=(2, 3), lit_frac=0.0, lit_glass=None, signs=True,
             collapse=None):
    """Row of heritage shopfronts. facing=-1: fronts face -Y (row on +Y side of street); facing=+1 mirrored.
    collapse(x)->bool: building facade replaced by rubble spill."""
    rr = random.Random(seed)
    K.R.seed(seed)
    walls = [mats["brick"], mats["brick_light"], mats["plaster_cream"], mats["plaster_white"], mats["stone"],
             mats["plaster_blue"], mats["plaster_red"], mats["plaster_green"], mats["brick"]]
    x = x0
    root = K.bpy.data.objects.new("row", None)
    K.link(root)
    spill = []
    sign_mats = [K.mat("sgn1", (0.05, 0.08, 0.2), bump=0), K.mat("sgn2", (0.5, 0.05, 0.04), bump=0),
                 K.mat("sgn3", (0.08, 0.2, 0.1), bump=0), K.mat("sgn4", (0.06, 0.06, 0.06), bump=0)]
    sign_fg = K.mat("sgnfg", (0.85, 0.82, 0.7), bump=0)
    while x < x1:
        w = rr.choice([7.0, 8.5, 10.0, 12.0, 6.5])
        fl = rr.randint(*floors)
        h = fl * 4.0
        wall = rr.choice(walls)
        col = bool(collapse and collapse(x + w / 2))
        if col:
            # building with front facade gone: dark interior + floor edges + rubble spill on footpath/road
            objs = [K.box((x + w / 2, 7.5, h * 0.4), (w - 0.1, 14, h * 0.8), wall),
                    K.box((x + w / 2, 0.6, h * 0.35), (w - 0.6, 0.3, h * 0.7), K._reveal_mat())]
            for f in range(1, fl):
                objs.append(K.box((x + w / 2, 1.0 + rr.uniform(0, 1), f * 4.0 - rr.uniform(0, 1.2)), (w - 0.3, 2.0, 0.3),
                                  mats["concrete_dark"], rot=(rr.uniform(-0.25, 0.25), rr.uniform(-0.1, 0.1), 0)))
            for k in range(5):
                objs.append(K.box((x + rr.uniform(0.5, w - 0.5), 0.3, h * 0.8 + rr.uniform(-1, 0.6)),
                                  (rr.uniform(0.8, 2.5), 0.4, rr.uniform(0.8, 2.0)), wall, rot=(0, rr.uniform(-.4, .4), 0)))
            spill.append((x + w / 2, w))
        else:
            objs = K.heritage_building(x, 0, w - 0.05, h, fl, wall=wall, mats=mats, lit_frac=lit_frac,
                                       lit_glass=lit_glass, shop=True, d=14)
            if signs:
                objs.append(K.sign(rr.choice(SHOPS), (x + w / 2, -0.2, 4.0 * 0.92), min(w * 0.7, 6), 0.7,
                                   rr.choice(sign_mats), sign_fg, font=FONT))
        for o in objs:
            if o.parent is None:
                o.parent = root
        x += w
    for (sx, sw) in spill:
        for o in K.rubble_pile(sx, -3.5, sw * 0.6, 4.5, 2.2, n=160, mats=mats, bricks=260, seed=int(sx * 10) % 1000,
                               brick_mat=mats["brick"]):
            if o.parent is None:
                o.parent = root
    if facing == -1:
        root.location = (0, y_front, 0)
    else:
        root.rotation_euler = (0, 0, pi)
        root.location = (x0 + x1, y_front, 0)
    return root


def colombo(mats, lit=False, lit_frac=0.0, cars=10, trees=True, wet=False, seed=4, collapse=None, dusty_cars=0.0,
            people=0, length=260):
    K.street(length, 12, 4.0, mats, wet=wet)
    lg = K.mat_glass(lit=4.0) if lit else None
    shop_row(8.1, -length / 2, length / 2, mats, seed=seed, facing=-1, lit_frac=lit_frac, lit_glass=lg, collapse=collapse)
    shop_row(-8.1, -length / 2, length / 2, mats, seed=seed + 7, facing=1, lit_frac=lit_frac, lit_glass=lg,
             collapse=collapse)
    K.ground(3000, mats["asphalt"], z=-0.3)
    rr = random.Random(seed)
    for i in range(-6, 7):
        K.lamp_post(i * 22 + 5, 7.3, arm_dir=-1, mats=mats, lit=40 if lit else 0)
    for i in range(cars):
        K.car(rr.uniform(-length / 2 + 10, length / 2 - 10), rr.choice([-3.2, 3.2]), rot=rr.choice([0, pi]), mats=mats,
              dusty=dusty_cars)
    if trees:
        for i in range(-5, 6):
            K.tree(i * 25 + 12, -7.6, h=6.5, r=2.4, mats=mats, seed=i)
    tops = [mats["cloth_dark"], mats["cloth_blue"], mats["plaster_red"], mats["plaster_white"], mats["weatherboard_yellow"]]
    for i in range(people):
        y = rr.choice([-9.2, -8.6, 8.6, 9.2])
        K.person(rr.uniform(-60, 80), y, rot=rr.choice([0, pi]) + rr.uniform(-.3, .3), top=rr.choice(tops), mats=mats)


def suburb(mats, seed=0, n=8, silt=0.0, water=0.0, tilt=0.0, sink=0.0, cars=3, street_len=160, fences=True,
           sunk_cars=0, trees=True):
    """NZ suburban street (weatherboard bungalows). silt>0 adds liquefaction ejecta; water floods street."""
    rr = random.Random(seed)
    K.ground(4000, mats["grass"], z=-0.11)
    K.street(street_len, 9, 2.0, mats, lines=False)
    walls = [mats["weatherboard_white"], mats["weatherboard_yellow"], mats["weatherboard_blue"],
             mats["weatherboard_green"], mats["brick"], mats["weatherboard_white"]]
    roofs = [mats["roof_iron"], mats["roof_red"], mats["roof_tile"]]
    for side in (-1, 1):
        for i in range(n):
            x = -street_len / 2 + 12 + i * (street_len - 20) / n + rr.uniform(-2, 2)
            y = side * rr.uniform(17, 20)
            t = (rr.uniform(-tilt, tilt), rr.uniform(-tilt, tilt)) if tilt else (0, 0)
            K.house(x, y, w=rr.uniform(8, 11), d=rr.uniform(9, 12), wall=rr.choice(walls), roof=rr.choice(roofs),
                    rot=(0 if side < 0 else pi), tilt=t, sink=rr.uniform(0, sink), mats=mats)
            if fences:
                for k in range(8):
                    K.box((x - 5 + k * 1.4, side * 8.0, 0.55), (1.2, 0.08, 1.0), mats["wood"])
            if trees and rr.random() < 0.6:
                K.tree(x + rr.uniform(4, 7), side * rr.uniform(11, 14), h=rr.uniform(5, 9), r=rr.uniform(2, 3.5),
                       mats=mats, seed=rr.randrange(999))
    for i in range(cars):
        K.car(rr.uniform(-60, 60), rr.choice([-3.4, 3.4]), rot=rr.choice([0, pi]), mats=mats,
              sink=0.35 * silt if silt else 0.0, dusty=0.5 * silt)
    for i in range(sunk_cars):
        K.car(rr.uniform(-25, 25), rr.choice([-2.5, 2.5]), rot=rr.uniform(-0.4, 0.4) + rr.choice([0, pi]), mats=mats,
              sink=0.75, tilt=(rr.uniform(-0.1, 0.1), rr.uniform(-0.12, 0.12)), dusty=0.7)
    if silt > 0:
        # ejecta mounds + sand boils across road and lawns
        def hf(x, y):
            n = K.noise2(x, y, seed + 3, 4, 0.08)
            return max(0.0, n * 0.9 + 0.05) * silt * 0.9 - 0.05

        K.grid_terrain("silt", street_len, 40, 260, 80, hf, mats["silt"])
        for i in range(int(40 * silt)):
            x, y = rr.uniform(-60, 60), rr.uniform(-14, 14)
            K.sphere((x, y, -0.25), 1.0, mats["silt"], subdiv=3, scale=(rr.uniform(0.8, 2.2), rr.uniform(0.8, 2.2), 0.45))
    if water > 0:
        K.box((0, 0, water), (street_len, 26, 0.02), mats["silt_wet"])


def cracks(cx, cy, length, mats, seed=0, along_x=True, width=0.25, depth=0.6, offset=0.0, n=30):
    """Jagged open crack (dark trench pieces) in a surface."""
    rr = random.Random(seed)
    dark = K._reveal_mat()
    o = []
    x, y = (cx - length / 2, cy) if along_x else (cx, cy - length / 2)
    for i in range(n):
        seg = length / n
        if along_x:
            nx_, ny_ = x + seg, y + rr.uniform(-0.6, 0.6)
        else:
            nx_, ny_ = x + rr.uniform(-0.6, 0.6), y + seg
        L = math.hypot(nx_ - x, ny_ - y)
        o.append(K.box(((x + nx_) / 2, (y + ny_) / 2, -depth / 2 + 0.03), (L + 0.2, width * rr.uniform(0.6, 1.4), depth),
                       dark, rot=(0, 0, math.atan2(ny_ - y, nx_ - x))))
        x, y = nx_, ny_
    return o


# ================================================================== PLATES
@plate
def colombo_day():
    K.reset(4)
    mats = K.M()
    K.sky(elev=50, rot=160, sun=4.5)
    colombo(mats, people=40)
    K.bus(-12, -3.2, rot=0, mats=mats)
    K.bus(30, 3.2, rot=pi, color=(0.85, 0.85, 0.82), mats=mats)
    return [S("street", (-58, -1.5, 1.8), (40, 1.5, 6), lens=40, dof=40, fstop=8),
            S("high", (-40, -9, 14), (30, 5, 0), lens=30),
            S("foot", (-20, -6.6, 1.5), (20, -7.5, 3), lens=50, dof=18, fstop=4)]


@plate
def colombo_collapse():
    K.reset(5)
    mats = K.M()
    K.sky(elev=50, rot=160, sun=3.5, haze=4)
    colombo(mats, collapse=lambda x: (int(x * 7.3) % 3) == 0, dusty_cars=0.7, cars=8, people=0)
    b = K.bus(-6, -3.4, rot=0.05, mats=mats, color=(0.6, 0.55, 0.3))
    K.rubble_pile(-6, -5.0, 9, 3.5, 3.4, n=200, mats=mats, bricks=500, seed=7, brick_mat=mats["brick"])
    K.dust((0, 0, 15), (260, 60, 30), density=0.035, scale=0.05, falloff=1.0)
    rr = random.Random(2)
    for i in range(14):
        K.person(rr.uniform(10, 50), rr.uniform(-6, 6), rot=rr.uniform(0, 6.3), mats=mats,
                 top=mats["rubble_dust"], legs=mats["cloth_dark"])
    return [S("wide", (-48, 0.5, 2.2), (30, -1, 4), lens=35, dof=42, fstop=8),
            S("bus", (-22, 4.5, 2.5), (-6, -4, 1.5), lens=45, dof=17, fstop=5.6),
            S("high", (-30, -6, 16), (20, 2, 0), lens=28)]


@plate
def dust_street():
    K.reset(6)
    mats = K.M()
    K.sky(elev=40, rot=200, sun=6, haze=6, sun_color=(1, 0.85, 0.65))
    colombo(mats, collapse=lambda x: (int(x * 3.1) % 4) == 0, dusty_cars=0.9, cars=6, trees=False)
    K.dust((0, 0, 12), (260, 40, 24), density=0.12, scale=0.06, falloff=1.0, color=(0.75, 0.68, 0.58))
    rr = random.Random(3)
    for i in range(10):
        K.person(rr.uniform(-10, 30), rr.uniform(-5, 5), rot=rr.uniform(-.5, .5) + pi / 2, mats=mats,
                 top=mats["rubble_dust"], legs=mats["rubble_dust"])
    return [S("silhouettes", (-30, 0, 1.6), (20, 0, 3), lens=50, dof=35, fstop=4),
            S("sunbeams", (-40, 5, 3), (10, -10, 9), lens=30)]


@plate
def night_street():
    K.reset(7)
    mats = K.M()
    K.flat_world((0.004, 0.006, 0.014), 1.0)
    colombo(mats, lit=True, lit_frac=0.06, cars=3, trees=True, wet=True)
    K.light_point((0, 0, 60), energy=0, radius=1)
    return [S("empty", (-58, -1.0, 1.7), (40, 1.0, 5), lens=40, dof=40, fstop=4, sky=False),
            S("corner", (-25, -6.6, 2.0), (15, 2, 4), lens=35, sky=False)]


@plate
def city_aerial():
    K.reset(8)
    mats = K.M()
    K.sky(elev=38, rot=220, sun=4.0, haze=2)
    K.ground(12000, K.mat("plains", (0.18, 0.2, 0.1), rough=0.95, var=0.5, scale=0.02, bump=0.1))
    K.box((0, 0, -0.08), (1400, 1400, 0.1), mats["asphalt"])
    sq = lambda x, y: abs(x) < 50 and abs(y) < 40  # noqa: E731 cathedral square
    park = lambda x, y: x < -420  # noqa: E731 Hagley park
    K.city_grid(0, 0, 1300, 1300, block=80, seed=8, hmin=7, hmax=24, tall=0.05,
                skip=lambda x, y: sq(x, y) or park(x, y))
    K.city_trees(-650, 0, 400, 1300, 600, mats, seed=2)
    K.box((-650, 0, -0.05), (420, 1300, 0.1), mats["grass"])
    K.cathedral(0, -20, rot=0, mats=mats)
    # Port Hills behind (south-east)
    hill = K.mat("hills", (0.22, 0.2, 0.1), rough=0.95, var=0.45, scale=0.01, bump=0.3, bump_scale=0.1, grime=0.3)
    K.grid_terrain("ph", 9000, 2500, 220, 70,
                   lambda x, y: max(0.0, (1 - abs(y - 2600) / 1250)) ** 1.3 * 480 * (0.7 + 0.5 * K.noise2(x, y, 4, 4, 0.0015)) - 5,
                   hill)
    K.atmosphere(size=(16000, 16000, 1200), center=(0, 0, 600), density=0.00025)
    return [S("oblique", (-700, -900, 380), (60, 300, 0), lens=40),
            S("cathedral", (-160, -260, 140), (0, 10, 20), lens=55),
            S("hills", (-200, -1400, 220), (100, 1500, 100), lens=50)]


@plate
def city_night_aerial():
    K.reset(9)
    mats = K.M()
    K.flat_world((0.003, 0.005, 0.012), 1.0)
    K.ground(12000, K.mat("nplains", (0.02, 0.02, 0.02), rough=0.9))
    K.city_grid(0, 0, 1300, 1300, block=80, seed=8, hmin=7, hmax=24, tall=0.05, lit=3.0)
    lamp = K.mat("slamp", (1, 0.6, 0.25), emit=(1, 0.55, 0.2), emit_str=80, bump=0)
    for i in range(-8, 9):
        for k in range(-40, 41):
            K.sphere((i * 80 + 40, k * 16, 7), 0.5, lamp, subdiv=1)
            K.sphere((k * 16, i * 80 + 40, 7), 0.5, lamp, subdiv=1)
    K.atmosphere(size=(16000, 16000, 1200), center=(0, 0, 600), density=0.0004, color=(0.4, 0.45, 0.6))
    return [S("sleep", (-700, -900, 380), (60, 300, 0), lens=40, sky=False)]


@plate
def cathedral_day():
    K.reset(10)
    mats = K.M()
    K.sky(elev=45, rot=210, sun=4.5)
    K.ground(3000, mats["footpath"])
    K.box((0, 0, 0.01), (120, 120, 0.02), K.mat("paving", (0.3, 0.29, 0.27), rough=0.8, var=0.2, bump=0.2, bump_scale=8))
    K.cathedral(0, 10, mats=mats)
    for i, x in enumerate((-60, -40, 40, 60)):
        K.facade_box(x - 10, 75, 20, 20, 18, K.mat_facade((0.55, 0.53, 0.5)), 5)
    rr = random.Random(5)
    for i in range(30):
        K.person(rr.uniform(-25, 25), rr.uniform(-25, 0), rot=rr.uniform(0, 6.3), mats=mats,
                 top=rr.choice([mats["cloth_dark"], mats["plaster_red"], mats["cloth_blue"], mats["plaster_white"]]))
    for x in (-30, 30):
        K.tree(x, -10, h=10, r=4, mats=mats, seed=x)
    return [S("front", (-14, -55, 1.7), (0, 12, 22), lens=28, dof=55, fstop=11),
            S("spire", (8, -30, 1.6), (0, 6.5, 50), lens=24),
            S("square", (-50, -45, 6), (0, 10, 15), lens=35)]


@plate
def cathedral_collapsed():
    K.reset(11)
    mats = K.M()
    K.sky(elev=45, rot=210, sun=3.8, haze=5)
    K.ground(3000, mats["footpath"])
    K.box((0, 0, 0.01), (120, 120, 0.02), K.mat("paving", (0.3, 0.29, 0.27), rough=0.8, var=0.2, bump=0.2, bump_scale=8))
    K.cathedral(0, 10, mats=mats, broken=1.0)
    for x in (-30, 30):
        K.tree(x, -10, h=10, r=4, mats=mats, seed=x)
    K.dust((0, 0, 20), (160, 160, 40), density=0.03, scale=0.05)
    mesh = K.mesh_fence(-35, -32, 35, -32, mats=mats)  # noqa: F841
    return [S("front", (-14, -55, 1.7), (0, 12, 14), lens=28, dof=55, fstop=11),
            S("rubble", (14, -26, 2.5), (0, 4, 3), lens=35, dof=20, fstop=5.6),
            S("high", (-40, -60, 30), (0, 10, 5), lens=35)]


@plate
def ctv_day():
    K.reset(12)
    mats = K.M()
    K.sky(elev=50, rot=150, sun=4.5)
    K.ground(3000, mats["asphalt"], z=-0.3)
    K.street(200, 12, 4, mats, center=(0, -10))
    K.office_building(-12, 0, 24, 22, 6, mats=mats, band=K.mat("ctvband", (0.72, 0.7, 0.66), rough=0.8, var=0.08, bump=0.05))
    K.box((-12 + 24 + 3.5, 6, 11), (6, 6, 22), mats["concrete"])  # stair core on the side (north wall)
    K.facade_box(16, 0, 18, 18, 9, mats["plaster_cream"], 2, glass=mats["glass"])
    K.facade_box(-40, 0, 24, 18, 12, K.mat_facade((0.5, 0.48, 0.46)), 3)
    K.text_obj("CTV", (-6, -0.1, 3.4), 1.4, K.mat("ctvsign", (0.85, 0.1, 0.08), bump=0), font=FONT)
    rr = random.Random(4)
    for i in range(6):
        K.car(rr.uniform(-60, 60), -10 + rr.choice([-3.2, 3.2]), rot=rr.choice([0, pi]), mats=mats)
    for x in (-20, 26):
        K.tree(x, -4, h=7, r=2.6, mats=mats, seed=x)
    return [S("corner", (-45, -40, 1.8), (2, 8, 10), lens=30),
            S("up", (-4, -18, 1.5), (0, 5, 16), lens=22)]


@plate
def ctv_collapsed():
    K.reset(13)
    mats = K.M()
    K.sky(elev=48, rot=150, sun=3.6, haze=4)
    K.ground(3000, mats["asphalt"], z=-0.3)
    K.street(200, 12, 4, mats, center=(0, -10))
    K.rubble_pile(0, 11, 15, 13, 6, n=900, mats=mats, slabs=26, rebar=60, seed=3)
    K.box((15.5, 6, 11), (6, 6, 22), mats["concrete"])  # surviving stair/lift tower
    for k in range(6):
        K.box((12.5, 6 + K.rnd(-2.5, 2.5), 3.4 * (k + 1)), (0.3, 0.6, 0.3), mats["rust"])
    K.facade_box(19, 0, 18, 18, 9, mats["plaster_cream"], 2, glass=mats["glass"])
    K.facade_box(-42, 0, 24, 18, 12, K.mat_facade((0.5, 0.48, 0.46)), 3)
    K.dust((0, 5, 18), (120, 80, 36), density=0.03, scale=0.05)
    rr = random.Random(9)
    for i in range(12):
        K.person(rr.uniform(-10, 12), rr.uniform(1, 18), rot=rr.uniform(0, 6.3), mats=mats, hivis=rr.random() < 0.4,
                 helmet=rr.random() < 0.5).location.z = 3.5 + rr.uniform(0, 1.5)
    return [S("wide", (-40, -38, 3), (2, 10, 4), lens=30),
            S("tower", (-8, -20, 1.7), (14, 7, 10), lens=28),
            S("pile", (-12, -6, 6), (2, 12, 3), lens=40, dof=16, fstop=5.6)]


@plate
def ctv_smoke():
    K.reset(14)
    mats = K.M()
    K.sky(elev=30, rot=250, sun=3.2, haze=5, sun_color=(1, 0.82, 0.62))
    K.ground(3000, mats["asphalt"], z=-0.3)
    K.street(200, 12, 4, mats, center=(0, -10))
    K.rubble_pile(0, 11, 15, 13, 6, n=900, mats=mats, slabs=26, rebar=60, seed=3)
    K.box((15.5, 6, 11), (6, 6, 22), mats["concrete"])
    K.facade_box(19, 0, 18, 18, 9, mats["plaster_cream"], 2, glass=mats["glass"])
    K.smoke((0, 12, 34), (26, 22, 60), density=0.35, color=(0.12, 0.12, 0.12), scale=0.12)
    K.fire((-2, 10, 4.5), (6, 4, 3), strength=25)
    K.fire((4, 14, 5.0), (4, 3, 2.5), strength=20)
    rr = random.Random(9)
    for i in range(10):
        K.person(rr.uniform(-12, 12), rr.uniform(-4, 0), rot=rr.uniform(0, 6.3), mats=mats, hivis=True,
                 helmet=True)
    return [S("smoke", (-45, -45, 3), (0, 10, 18), lens=28),
            S("fire", (-14, -12, 2), (0, 10, 5), lens=45, dof=24, fstop=4)]


@plate
def ctv_fire_night():
    K.reset(15)
    mats = K.M()
    K.flat_world((0.006, 0.008, 0.016), 1.0)
    K.ground(3000, mats["asphalt_wet"], z=-0.3)
    K.street(200, 12, 4, mats, center=(0, -10), wet=True)
    K.rubble_pile(0, 11, 15, 13, 6, n=900, mats=mats, slabs=26, rebar=60, seed=3)
    K.box((15.5, 6, 11), (6, 6, 22), mats["concrete"])
    K.smoke((0, 12, 34), (30, 26, 60), density=0.25, color=(0.25, 0.22, 0.2), scale=0.12)
    K.fire((-2, 10, 4.5), (7, 5, 4), strength=40)
    K.fire((4, 14, 5.0), (5, 4, 3), strength=35)
    K.light_point((0, 11, 6), energy=60000, color=(1, 0.45, 0.12), radius=4)
    K.floodlight(-20, -6, 9, (0, 10, 3), mats=mats)
    K.floodlight(22, -6, 9, (0, 10, 3), mats=mats)
    rr = random.Random(11)
    for i in range(16):
        K.person(rr.uniform(-14, 14), rr.uniform(-6, 2), rot=rr.uniform(0, 6.3), mats=mats, hivis=True, helmet=True,
                 pose=rr.choice(["stand", "dig"]))
    # fire truck-ish
    K.bus(-24, -10, rot=0.2, color=(0.6, 0.03, 0.02), mats=mats)
    return [S("night", (-42, -40, 2.5), (0, 10, 9), lens=30, sky=False),
            S("rescuers", (-10, -16, 1.6), (2, 4, 4), lens=50, dof=18, fstop=2.8, sky=False)]


@plate
def pgc_day():
    K.reset(16)
    mats = K.M()
    K.sky(elev=50, rot=120, sun=4.5)
    K.ground(3000, mats["asphalt"], z=-0.3)
    K.street(200, 12, 4, mats, center=(0, -10))
    K.office_building(-14, 0, 28, 20, 5, fh=3.6, mats=mats, band=K.mat("pgcband", (0.45, 0.43, 0.4), rough=0.8))
    K.facade_box(18, 0, 20, 18, 12, mats["brick"], 3, glass=mats["glass"])
    K.facade_box(-42, 0, 24, 18, 9, mats["plaster_white"], 2, glass=mats["glass"])
    for x in (-25, 25, 0):
        K.tree(x, -4.5, h=7, r=2.6, mats=mats, seed=x + 3)
    return [S("front", (-34, -40, 1.8), (0, 8, 9), lens=32)]


@plate
def pgc_collapsed():
    K.reset(17)
    mats = K.M()
    K.sky(elev=45, rot=120, sun=3.8, haze=4)
    K.ground(3000, mats["asphalt"], z=-0.3)
    K.street(200, 12, 4, mats, center=(0, -10))
    K.pancake(-14, 0, 28, 20, floors_crushed=3, floors_intact=2, fh=3.6, mats=mats)
    K.facade_box(18, 0, 20, 18, 12, mats["brick"], 3, glass=mats["glass"])
    K.dust((0, 5, 15), (100, 70, 30), density=0.025, scale=0.05)
    rr = random.Random(2)
    for i in range(8):
        p = K.person(rr.uniform(-12, 12), rr.uniform(2, 16), rot=rr.uniform(0, 6.3), mats=mats, hivis=True, helmet=True)
        p.location.z = 3.0 + 7.2
    return [S("front", (-36, -36, 1.8), (0, 8, 5), lens=32),
            S("slabs", (-10, -12, 1.4), (0, 2, 2.5), lens=40, dof=13, fstop=4)]


@plate
def pgc_rescue_night():
    K.reset(18)
    mats = K.M()
    K.flat_world((0.005, 0.007, 0.015), 1.0)
    K.ground(3000, mats["asphalt_wet"], z=-0.3)
    K.street(200, 12, 4, mats, center=(0, -10), wet=True)
    K.pancake(-14, 0, 28, 20, floors_crushed=3, floors_intact=2, fh=3.6, mats=mats)
    K.floodlight(-26, -8, 10, (0, 6, 5), mats=mats, energy=60000)
    K.floodlight(20, -8, 10, (0, 6, 5), mats=mats, energy=60000)
    rr = random.Random(5)
    for i in range(10):
        p = K.person(rr.uniform(-12, 12), rr.uniform(-1, 10), rot=rr.uniform(0, 6.3), mats=mats, hivis=True,
                     helmet=True, pose="dig")
        p.location.z = 10.2
    for i in range(8):
        K.person(rr.uniform(-15, 15), rr.uniform(-6, -2), rot=rr.uniform(0, 6.3), mats=mats, hivis=True, helmet=True)
    # crane boom
    K.box((30, -14, 1.5), (10, 3, 2.5), K.mat("crn", (0.75, 0.55, 0.05), rough=0.5))
    b = K.box((20, -6, 14), (1.2, 1.2, 30), K.mat("crn", (0.75, 0.55, 0.05), rough=0.5))
    b.rotation_euler = (0.25, -0.45, 0)
    return [S("night", (-40, -38, 3), (0, 8, 7), lens=30, sky=False),
            S("close", (-14, -14, 4), (0, 4, 9), lens=45, dof=20, fstop=4, sky=False)]


@plate
def office_interior():
    K.reset(19)
    mats = K.M()
    K.sky(elev=55, rot=140, sun=5.0)
    room = K.mat("wallpaint", (0.75, 0.74, 0.7), rough=0.85, var=0.05, bump=0.02)
    carpet = K.mat("carpet", (0.12, 0.13, 0.16), rough=1.0, var=0.2, bump=0.3, bump_scale=200)
    K.box((0, 0, -0.05), (16, 12, 0.1), carpet)
    K.box((0, 0, 2.85), (16, 12, 0.1), K.mat("ceil", (0.8, 0.8, 0.78), rough=0.9, var=0.03))
    K.box((0, 6, 1.4), (16, 0.2, 2.8), room)
    K.box((-8, 0, 1.4), (0.2, 12, 2.8), room)
    K.box((8, 0, 1.4), (0.2, 12, 2.8), room)
    # window wall (-Y) with spandrel + glazing
    K.box((0, -6, 0.45), (16, 0.3, 0.9), room)
    K.box((0, -6, 2.7), (16, 0.3, 0.3), room)
    for i in range(9):
        K.box((-8 + i * 2, -6, 1.7), (0.08, 0.2, 1.7), mats["metal_dark"])
    for i in range(10):
        K.light_area((-6 + (i % 5) * 3, -2 + (i // 5) * 4, 2.78), (-6 + (i % 5) * 3, -2 + (i // 5) * 4, 0), energy=60,
                     size=1.2, color=(1, 0.97, 0.92))
    desk = K.mat("desk", (0.6, 0.55, 0.45), rough=0.5, var=0.1, bump=0.02)
    scr = K.mat("screen", (0.2, 0.3, 0.4), emit=(0.6, 0.75, 0.9), emit_str=3, rough=0.2, bump=0)
    rr = random.Random(3)
    for r_ in range(2):
        for c in range(3):
            x, y = -4.5 + c * 4.5, -2.5 + r_ * 4
            K.box((x, y, 0.74), (3.2, 1.5, 0.04), desk)
            for s_ in (-1, 1):
                K.box((x + s_ * 1.5, y, 0.37), (0.05, 1.4, 0.72), mats["metal_dark"])
            K.box((x - 0.6, y + 0.35, 1.05), (0.55, 0.04, 0.38), mats["metal_dark"])
            K.box((x - 0.6, y + 0.33, 1.05), (0.5, 0.01, 0.32), scr)
            K.box((x - 0.6, y + 0.4, 0.82), (0.25, 0.2, 0.12), mats["metal_dark"])
            K.box((x + 0.6, y + 0.1, 0.78), (0.32, 0.24, 0.03), K.mat("paper", (0.85, 0.85, 0.82), bump=0))
            K.cylinder((x + 0.9, y - 0.3, 0.8), 0.04, 0.1, K.mat("mug", (0.6, 0.1, 0.05), rough=0.3, bump=0))
            K.box((x - 0.5, y - 0.9, 0.48), (0.5, 0.5, 0.08), mats["cloth_dark"])
            K.box((x - 0.5, y - 1.12, 0.8), (0.5, 0.06, 0.6), mats["cloth_dark"])
            K.cylinder((x - 0.5, y - 0.9, 0.24), 0.03, 0.45, mats["metal"])
    # city outside
    K.facade_box(-30, -40, 60, 20, 30, K.mat_facade((0.55, 0.53, 0.5)), 8)
    K.ground(2000, mats["asphalt"], z=-12)
    return [S("desk", (5.5, 4.5, 1.25), (-3, -4, 0.9), lens=26, dof=4, fstop=4, sky=False, samples=20)]


@plate
def classroom():
    K.reset(20)
    mats = K.M()
    K.sky(elev=50, rot=200, sun=5.0)
    room = K.mat("wallpaint2", (0.78, 0.76, 0.7), rough=0.85, var=0.05, bump=0.02)
    K.box((0, 0, -0.05), (12, 10, 0.1), K.mat("vinyl", (0.35, 0.33, 0.3), rough=0.4, var=0.15, bump=0.05))
    K.box((0, 0, 2.85), (12, 10, 0.1), K.mat("ceil", (0.8, 0.8, 0.78), rough=0.9, var=0.03))
    K.box((0, 5, 1.4), (12, 0.2, 2.8), room)
    K.box((6, 0, 1.4), (0.2, 10, 2.8), room)
    K.box((0, -5, 0.45), (12, 0.3, 0.9), room)
    K.box((0, -5, 2.7), (12, 0.3, 0.3), room)
    K.box((-6, 0, 1.4), (0.2, 10, 2.8), room)
    wb = K.mat("whiteboard", (0.9, 0.9, 0.9), rough=0.15, var=0.02, bump=0)
    K.box((5.88, 0, 1.6), (0.05, 4, 1.3), wb)
    ink = K.mat("ink", (0.05, 0.1, 0.4), rough=0.5, bump=0)
    K.text_obj("Present Perfect", (5.84, 0.0, 2.0), 0.28, ink, rot=(pi / 2, 0, -pi / 2), font=FONT)
    K.text_obj("I have lived here for ...", (5.84, 0.0, 1.55), 0.17, ink, rot=(pi / 2, 0, -pi / 2), font=FONT)
    for i in range(6):
        K.light_area((-4 + (i % 3) * 4, -2 + (i // 3) * 4, 2.78), (-4 + (i % 3) * 4, -2 + (i // 3) * 4, 0), energy=60,
                     size=1.2)
    dk = K.mat("sdesk", (0.62, 0.5, 0.35), rough=0.5, var=0.1, bump=0.02)
    for r_ in range(4):
        for c in range(4):
            x, y = -3.5 + r_ * 1.9, -3.2 + c * 1.9
            K.box((x, y, 0.72), (0.65, 1.1, 0.04), dk)
            K.box((x, y, 0.36), (0.04, 1.0, 0.7), mats["metal_dark"])
            K.box((x - 0.55, y, 0.45), (0.42, 0.42, 0.04), mats["plaster_blue"])
            K.box((x - 0.75, y, 0.75), (0.04, 0.42, 0.5), mats["plaster_blue"])
            if (r_ + c) % 2 == 0:
                K.box((x, y + 0.15, 0.75), (0.3, 0.22, 0.02), K.mat("book", (0.75, 0.2, 0.15), bump=0))
    K.ground(2000, mats["asphalt"], z=-15)
    K.facade_box(-30, -45, 60, 20, 35, K.mat_facade((0.6, 0.58, 0.55)), 9)
    return [S("room", (-5.3, 4.2, 1.6), (4, -1.5, 1.1), lens=24, sky=False, samples=20)]


@plate
def farmland_night():
    """Darfield, 4:35 am: the plains in blue pre-dawn light, fence lines."""
    K.reset(21)
    mats = K.M()
    K.sky(elev=-2, rot=90, sun=0.0, strength=0.5)
    K.flat_world((0.02, 0.03, 0.065), 1.0)
    fields(mats, seed=1)
    K.mountains(dist=9000, width=40000, height=2200, depth=6000, z0=-50)
    K.fence(-200, -2, 200, -2, mats=mats)
    K.light_point((-300, 800, 600), energy=0, radius=1)
    K.atmosphere(size=(40000, 40000, 2000), center=(0, 0, 1000), density=0.0003, color=(0.4, 0.5, 0.8))
    m = K.bpy.data.lights.new("moon", "SUN")
    m.energy = 0.6
    m.color = (0.6, 0.7, 1.0)
    mo = K.bpy.data.objects.new("moon", m)
    K.link(mo)
    mo.rotation_euler = (0.9, 0.2, 2.2)
    return [S("plains", (-30, -20, 1.7), (60, 300, 6), lens=30, sky=False)]


def fields(mats, seed=0, size=6000, dry=False):
    rr = random.Random(seed)
    K.ground(60000, mats["grass_dry"] if dry else mats["grass"])
    cols = [(0.13, 0.2, 0.06), (0.2, 0.24, 0.08), (0.3, 0.27, 0.12), (0.1, 0.16, 0.05), (0.25, 0.2, 0.1)]
    for i in range(-6, 7):
        for j in range(-1, 12):
            c = rr.choice(cols)
            K.box((i * 400 + 200, j * 400 + 200, -0.08), (396, 396, 0.06),
                  K.mat(f"fld{c}", c, rough=0.95, var=0.35, scale=0.3, bump=0.3, bump_scale=200))
    # shelterbelts (pine hedgerows typical of Canterbury)
    hedge = K.mat("hedge", (0.03, 0.06, 0.025), rough=0.9, var=0.4, scale=2, bump=0.8, bump_scale=10)
    for j in range(1, 12):
        h = K.box((0, j * 400 + 150, 6), (5200, 4, 12), hedge)
        dm = h.modifiers.new("s", "SUBSURF")
        dm.levels = 2
        dm.render_levels = 2


@plate
def fault_rupture():
    """Greendale fault: farmland torn, fences offset several metres (right-lateral)."""
    K.reset(22)
    mats = K.M()
    K.sky(elev=30, rot=60, sun=4.0, haze=1.5)
    fields(mats, seed=2)
    K.mountains(dist=9000, width=40000, height=2200, depth=6000, z0=-50)

    def off(t):
        return 4.0 / (1 + math.exp(-(t - 0.5) * 60)) - 2.0

    K.fence(-1, -80, -1, 80, mats=mats, offset_fn=off, n=60)
    K.fence(-30, -80, -30, 80, mats=mats, offset_fn=off, n=60, wire=False)
    # rupture zone: en-echelon cracks and a pushed-up mole track across the field
    for k in range(18):
        x = -60 + k * 7
        K.box((x, 0 + K.rnd(-1, 1), -0.2), (6, 0.6, 0.6), K._reveal_mat(), rot=(0, 0, 0.5))
        K.box((x + 1, 1.2, 0.15), (6.5, 1.8, 0.5), mats["dirt"], rot=(0.1, 0, 0.5), bevel=0.3)
    K.rubble_pile(0, 0, 60, 2.5, 0.35, n=250, mats=mats, dusty=False, seed=5)
    K.atmosphere(size=(40000, 40000, 2000), center=(0, 0, 1000), density=0.0002)
    return [S("fence", (-5, -35, 1.6), (1, 10, 0.5), lens=35, dof=30, fstop=8),
            S("aerial", (-40, -60, 30), (0, 5, 0), lens=35)]


@plate
def road_crack():
    K.reset(23)
    mats = K.M()
    K.sky(elev=28, rot=80, sun=4.0)
    fields(mats, seed=3)
    K.mountains(dist=9000, width=40000, height=2200, depth=6000, z0=-50)
    # road split and offset across a crack
    K.box((0, -60, -0.05), (8, 120, 0.1), mats["asphalt"])
    K.box((1.6, 60, -0.05 - 0.25), (8, 120, 0.1), mats["asphalt"], rot=(0.004, 0, 0))
    paint = K.mat("rp", (0.85, 0.8, 0.3), rough=0.6, var=0.1, bump=0.05)
    for i in range(12):
        K.box((0, -6 - i * 9, 0.002), (0.15, 3, 0.01), paint)
        K.box((1.6, 6 + i * 9, 0.002 - 0.25), (0.15, 3, 0.01), paint)
    cracks(0, 0, 14, mats, seed=1, width=0.5, depth=1.2)
    K.rubble_pile(0, 0, 7, 1.2, 0.3, n=60, mats=mats, dusty=False)
    return [S("road", (-1, -22, 1.5), (1, 20, 0.2), lens=35, dof=20, fstop=8)]


@plate
def rail_buckled():
    K.reset(24)
    mats = K.M()
    K.sky(elev=32, rot=100, sun=4.0)
    fields(mats, seed=4, dry=True)
    K.mountains(dist=9000, width=40000, height=2200, depth=6000, z0=-50)
    ball = K.mat("ballast", (0.35, 0.33, 0.3), rough=0.95, var=0.3, bump=0.8, bump_scale=60)
    K.box((0, 0, 0.1), (5, 400, 0.4), ball, bevel=0.2)
    steel = K.mat("rail", (0.35, 0.3, 0.27), rough=0.4, metal=1, var=0.3)

    def lat(y):
        return 2.8 * math.exp(-((y - 8) / 9) ** 2) * math.sin((y - 8) / 4.5)

    for s_ in (-0.72, 0.72):
        pts = [(lat(y) + s_, y) for y in [i * 0.5 - 100 for i in range(400)]]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            L = math.hypot(bx - ax, by - ay)
            K.box(((ax + bx) / 2, (ay + by) / 2, 0.42), (0.08, L + 0.02, 0.16), steel, rot=(0, 0, -math.atan2(bx - ax, by - ay)))
    for i in range(300):
        y = i * 0.65 - 100
        K.box((lat(y), y, 0.3), (2.6, 0.25, 0.15), mats["wood"], rot=(0, 0, -0.3 * lat(y) / 2.8))
    return [S("rail", (0.5, -18, 1.4), (0, 14, 0.4), lens=40, dof=22, fstop=8)]


@plate
def shopfront_dawn():
    """Sept 2010 aftermath: brick facade spilled on footpath, chimney through a roof, dawn light."""
    K.reset(25)
    mats = K.M()
    K.sky(elev=6, rot=95, sun=5.0, sun_color=(1, 0.7, 0.45), haze=2)
    colombo(mats, collapse=lambda x: (int(x * 2.3) % 5) == 0, cars=2, trees=True, length=200)
    K.mesh_fence(-60, -5.5, 20, -5.5, mats=mats)
    return [S("dawn", (-50, 2, 1.7), (30, -6, 4), lens=40, dof=30, fstop=8),
            S("bricks", (-20, -3, 1.2), (0, -9, 1.5), lens=35, dof=10, fstop=4)]


@plate
def liquefaction_2010():
    K.reset(26)
    mats = K.M()
    K.sky(elev=10, rot=100, sun=4.5, sun_color=(1, 0.8, 0.6), haze=2)
    suburb(mats, seed=3, silt=0.7, water=0.05, cars=3, sunk_cars=1)
    return [S("street", (-55, 1, 1.7), (20, -1, 1.5), lens=35, dof=25, fstop=8)]


@plate
def liquefaction_2011():
    K.reset(27)
    mats = K.M()
    K.sky(elev=35, rot=200, sun=3.5, haze=3)
    suburb(mats, seed=5, silt=1.0, water=0.32, cars=2, sunk_cars=3, tilt=0.04, sink=0.4)
    return [S("flood", (-40, 0.5, 1.5), (20, -1, 0.8), lens=35, dof=22, fstop=8),
            S("car", (-18, 5, 1.3), (-6, 0, 0.6), lens=45, dof=12, fstop=4),
            S("high", (-45, -20, 12), (10, 3, 0), lens=30)]


@plate
def tilted_house():
    K.reset(28)
    mats = K.M()
    K.sky(elev=40, rot=230, sun=4.0, haze=2)
    K.ground(4000, mats["grass"])

    def hf(x, y):
        return max(0.0, K.noise2(x, y, 6, 4, 0.12) * 0.7 + 0.1) * 0.8 - 0.1

    K.grid_terrain("silt", 80, 60, 160, 120, hf, mats["silt"])
    K.house(0, 8, w=10, d=11, tilt=(0.07, -0.09), sink=0.8, mats=mats, wall=mats["weatherboard_yellow"])
    K.house(-22, 10, w=9, d=10, tilt=(-0.03, 0.05), sink=0.4, mats=mats)
    K.box((0, -6, 0.15), (70, 6, 0.02), mats["silt_wet"])
    cracks(0, -2, 40, mats, seed=4, width=0.3, depth=0.6)
    K.car(9, -2, rot=0.4, sink=0.5, tilt=(0.08, 0.05), mats=mats, dusty=0.6)
    return [S("house", (-10, -22, 1.6), (0, 8, 2.5), lens=32, dof=26, fstop=8)]


@plate
def sand_boils():
    K.reset(29)
    mats = K.M()
    K.sky(elev=35, rot=200, sun=4.0, haze=2)
    K.ground(4000, mats["grass"])
    rr = random.Random(3)
    for i in range(16):
        x, y = rr.uniform(-12, 12), rr.uniform(-2, 25)
        r = rr.uniform(0.6, 2.2)
        K.sphere((x, y, -0.05), r, mats["silt"], subdiv=4, scale=(r, r * rr.uniform(0.8, 1.2), r * 0.22))
        K.cylinder((x, y, r * 0.2), r * 0.12, 0.1, K._reveal_mat())
    K.box((0, 8, 0.03), (40, 40, 0.02), mats["silt_wet"])
    return [S("boils", (-1, -8, 1.3), (0, 8, 0), lens=30, dof=10, fstop=8)]


@plate
def canterbury_plains():
    K.reset(30)
    mats = K.M()
    K.sky(elev=22, rot=80, sun=4.0, haze=1.5)
    fields(mats, seed=6)
    K.mountains(dist=12000, width=50000, height=2600, depth=8000, z0=-50)
    # braided river: gravel bed + channels
    grav = K.mat("gravel", (0.5, 0.48, 0.44), rough=0.9, var=0.3, bump=0.5, bump_scale=40)
    for k in range(40):
        y = k * 140
        K.box((-600 + math.sin(k * 0.3) * 120, y, -0.02), (700, 150, 0.05), grav)
        for c in range(4):
            K.box((-600 + math.sin(k * 0.3 + c) * 280, y, 0.04), (rnd_(20, 60), 150, 0.02), mats["water"],
                  rot=(0, 0, rnd_(-0.3, 0.3)))
    K.atmosphere(size=(60000, 60000, 3000), center=(0, 0, 1500), density=0.00012)
    return [S("alps", (-300, -500, 180), (-200, 4000, 200), lens=35),
            S("river", (-500, -300, 60), (-600, 1500, 0), lens=30)]


def rnd_(a, b):
    return K.R.uniform(a, b)


@plate
def port_hills():
    K.reset(31)
    mats = K.M()
    K.sky(elev=14, rot=290, sun=5.0, sun_color=(1, 0.78, 0.55), haze=1.5)
    hill = K.mat("hills2", (0.25, 0.22, 0.1), rough=0.95, var=0.5, scale=0.03, bump=0.4, bump_scale=0.3, grime=0.35)

    def hf(x, y):
        ridge = max(0.0, 1 - abs(y - 1500) / 900) ** 1.2
        return ridge * 450 * (0.65 + 0.6 * K.noise2(x, y, 7, 5, 0.002)) + 3 * K.noise2(x, y, 2, 3, 0.03) - 2

    K.grid_terrain("ph", 8000, 2600, 260, 110, hf, hill)
    rr = random.Random(7)
    roofs = [mats["roof_iron"], mats["roof_red"], mats["roof_tile"]]
    for i in range(500):
        x, y = rr.uniform(-1200, 1200), rr.uniform(-200, 600)
        K.box((x, y, 2), (rr.uniform(8, 12), rr.uniform(9, 12), 4), rr.choice([mats["weatherboard_white"], mats["brick"],
                                                                                 mats["weatherboard_yellow"]]))
        K.box((x, y, 4.3), (rr.uniform(9, 13), rr.uniform(10, 13), 0.6), rr.choice(roofs))
    K.city_trees(0, 200, 2400, 800, 700, mats, seed=3)
    K.atmosphere(size=(20000, 20000, 1500), center=(0, 0, 750), density=0.00025)
    return [S("ridge", (-300, -700, 60), (100, 1400, 250), lens=45),
            S("wide", (-900, -900, 90), (0, 1500, 150), lens=30)]


@plate
def lyttelton():
    K.reset(32)
    mats = K.M()
    K.sky(elev=30, rot=60, sun=4.0, haze=1.5)
    hill = K.mat("hills3", (0.24, 0.22, 0.11), rough=0.95, var=0.5, scale=0.03, bump=0.4, bump_scale=0.3, grime=0.35)

    def hf(x, y):
        r = math.hypot(x / 1.6, y)
        rim = max(0.0, 1 - abs(r - 1900) / 1500)
        return rim * 420 * (0.6 + 0.6 * K.noise2(x, y, 9, 5, 0.0015)) - 25 + 0.012 * max(0, r - 1100)

    K.grid_terrain("crater", 9000, 7000, 240, 190, hf, hill)
    K.box((0, 0, 0), (9000, 7000, 0.1), K.mat("sea", (0.02, 0.05, 0.06), rough=0.08, var=0.1, bump=0.05,
                                                bump_scale=1, coat=1.0))
    rr = random.Random(2)
    for i in range(220):
        a = rr.uniform(1.0, 2.1)
        r = rr.uniform(1150, 1400)
        x, y = math.cos(a) * r * 1.6, math.sin(a) * r
        z = hf(x, y)
        if z < 2:
            continue
        K.box((x, y, z + 2), (9, 10, 4.5), rr.choice([mats["weatherboard_white"], mats["brick"], mats["stone"]]))
        K.box((x, y, z + 4.6), (10, 11, 0.5), rr.choice([mats["roof_iron"], mats["roof_red"]]))
    K.atmosphere(size=(20000, 20000, 1500), center=(0, 0, 750), density=0.0002)
    return [S("harbour", (300, 1900, 330), (-200, -300, 0), lens=30)]


@plate
def timeball():
    """Lyttelton Timeball Station (castle-like stone tower with time-ball mast) above the harbour."""
    K.reset(33)
    mats = K.M()
    K.sky(elev=35, rot=40, sun=4.0, haze=1.5)
    hill = K.mat("hills4", (0.24, 0.22, 0.11), rough=0.95, var=0.5, scale=0.3, bump=0.4, bump_scale=4)
    K.grid_terrain("slope", 600, 600, 120, 120, lambda x, y: (0.15 * y if y < -10 else -1.5 + 0.04 * y) + 1.5 * K.noise2(x, y, 3, 3, 0.05) * min(1, abs(y) / 15), hill)
    K.box((0, -500, -40), (4000, 400, 0.1), K.mat("sea", (0.02, 0.05, 0.06), rough=0.08, var=0.1, bump=0.05, coat=1.0))
    st = mats["stone_dark"]
    K.box((0, 0, 5), (14, 10, 10), st)
    K.box((-4, 2, 9), (6, 6, 18), st)
    for k in range(6):
        K.box((-6.6 + k * 1.1, -1, 18.4), (0.6, 0.6, 0.9), st)
    K.cylinder((-4, 2, 25), 0.15, 14, mats["metal_dark"], verts=8)
    K.sphere((-4, 2, 29), 1.0, K.mat("tball", (0.06, 0.06, 0.06), rough=0.5))
    for s_ in (-1, 1):
        for k in range(3):
            K.box((s_ * 7.02, -2 + k * 2.5, 6), (0.1, 1.0, 1.8), mats["glass"])
    rr = random.Random(4)
    for i in range(30):
        K.rock((rr.uniform(-8, 8), rr.uniform(-9, -5), 0.3), rr.uniform(0.3, 0.8), mats["stone_dark"])
    return [S("station", (-26, -26, 3), (-2, 0, 9), lens=32)]


@plate
def sumner_cliffs():
    K.reset(34)
    mats = K.M()
    K.sky(elev=40, rot=330, sun=4.0, haze=2)
    cliffm = K.mat("cliff", (0.32, 0.27, 0.22), rough=0.95, var=0.45, scale=0.4, bump=0.9, bump_scale=3, grime=0.4)

    def hf(x, y):
        base = 0 if y < 20 else min(70, (y - 20) * 3.5) + 15 * max(0, y - 40) / 40
        return base + 5 * K.noise2(x, y, 5, 5, 0.06) * min(1, max(0, y - 18) / 6)

    K.grid_terrain("cliff", 400, 160, 400, 200, hf, cliffm, origin=(0, 60, 0))
    K.ground(4000, mats["footpath"])
    K.rubble_pile(-10, 26, 30, 9, 6, n=500, mats=mats, dusty=False, seed=8)
    K.box((0, -60, -0.3), (600, 80, 0.1), K.mat("sea", (0.02, 0.05, 0.06), rough=0.06, coat=1.0))
    rr = random.Random(5)
    for i, x in enumerate((-70, -45, 25, 50, 75)):
        K.house(x, 10, w=10, d=9, mats=mats, rot=0, wall=rr.choice([mats["weatherboard_white"], mats["weatherboard_blue"]]))
    K.street(400, 8, 2, mats, center=(0, -6), lines=False)
    for i in range(30):
        K.rock((rr.uniform(-40, 30), rr.uniform(14, 22), rr.uniform(0.5, 1.5)), rr.uniform(0.8, 2.5), mats["rock"])
    K.dust((0, 30, 20), (120, 40, 40), density=0.02, scale=0.08)
    return [S("cliff", (-70, -30, 4), (0, 40, 22), lens=30)]


@plate
def boulder_house():
    K.reset(35)
    mats = K.M()
    K.sky(elev=45, rot=300, sun=4.2, haze=1.5)
    hill = K.mat("hills5", (0.22, 0.2, 0.1), rough=0.95, var=0.5, scale=0.3, bump=0.5, bump_scale=4)
    K.grid_terrain("slope", 300, 300, 120, 120, lambda x, y: max(0, y) * 0.45 + 2 * K.noise2(x, y, 3, 3, 0.05), hill)
    h = K.house(0, -2, w=10, d=10, mats=mats, wall=mats["weatherboard_white"], chimney=False)
    K.box((1.0, 3.0, 2.4), (3.4, 4.0, 3.2), K._reveal_mat())  # hole torn through the back wall/roof
    K.rock((1.5, 4.0, 2.2), (2.6, 2.3, 2.1), mats["rock"], seed=3)
    for i in range(40):
        K.box((K.rnd(-2, 5), K.rnd(-8, 8), 0.15), (K.rnd(0.3, 1.5), K.rnd(0.1, 0.3), 0.06), mats["weatherboard_white"],
              rot=(K.rnd(-1, 1), K.rnd(-1, 1), K.rnd(0, 6)))
    for i in range(12):
        K.rock((K.rnd(-10, 14), K.rnd(10, 60), 3 + K.rnd(0, 10)), K.rnd(0.5, 1.6), mats["rock"])
    return [S("boulder", (-14, -24, 2.2), (1, 1, 2.4), lens=35, dof=26, fstop=8),
            S("track", (-6, 30, 16), (0, -2, 2), lens=30)]


@plate
def grand_chancellor():
    K.reset(36)
    mats = K.M()
    K.sky(elev=40, rot=160, sun=4.0, haze=3)
    K.ground(3000, mats["asphalt"], z=-0.3)
    K.street(300, 12, 4, mats)
    root = K.bpy.data.objects.new("gc", None)
    K.link(root)
    fac = K.mat_facade((0.62, 0.6, 0.56), bay=2.6, floor=3.2, frac=0.3)
    for o in [K.box((0, 0, 42), (24, 20, 84), fac), K.box((0, 0, 84.5), (24.5, 20.5, 1.0), mats["concrete"]),
              K.box((14, 0, 20), (6, 16, 40), mats["concrete"])]:
        o.parent = root
    root.location = (0, 25, 0)
    root.rotation_euler = (0.0, -0.03, 0)
    rr = random.Random(5)
    for x in (-60, -36, 30, 55):
        K.facade_box(x - 10, 14, 20, 20, rr.uniform(10, 24), K.mat_facade((0.5, 0.49, 0.47)), 4)
    K.tape(-30, -7, 30, -7, mats=mats)
    for x in (-30, 30):
        K.cylinder((x, -7, 0.55), 0.05, 1.1, mats["metal"])
    K.dust((0, 0, 30), (300, 200, 60), density=0.008, scale=0.03)
    return [S("lean", (-45, -50, 1.7), (0, 25, 40), lens=28)]


@plate
def search_rescue():
    K.reset(37)
    mats = K.M()
    K.sky(elev=30, rot=230, sun=3.5, haze=3)
    K.ground(3000, mats["asphalt"], z=-0.3)
    K.rubble_pile(0, 10, 18, 12, 5, n=900, mats=mats, slabs=20, rebar=40, bricks=400, seed=12)
    K.facade_box(-40, 0, 20, 16, 12, mats["brick"], 3, glass=mats["glass"])
    K.facade_box(22, 0, 20, 16, 8, mats["plaster_cream"], 2, glass=mats["glass"])
    rr = random.Random(8)
    for i in range(12):
        p = K.person(rr.uniform(-12, 12), rr.uniform(2, 18), rot=rr.uniform(0, 6.3), mats=mats, hivis=True,
                     helmet=True, pose=rr.choice(["stand", "dig"]))
        p.location.z = 2.5 + rr.uniform(0, 2)
    K.dust((0, 5, 15), (100, 60, 30), density=0.015, scale=0.05)
    return [S("team", (-24, -24, 2), (0, 10, 3), lens=40, dof=34, fstop=5.6)]


@plate
def student_army():
    K.reset(38)
    mats = K.M()
    K.sky(elev=45, rot=200, sun=4.3)
    suburb(mats, seed=9, silt=0.5, water=0.0, cars=1)
    rr = random.Random(4)
    wb = K.mat("wbarrow", (0.1, 0.25, 0.5), rough=0.4)
    for i in range(24):
        x, y = rr.uniform(-40, 30), rr.choice([-6.5, 6.5]) + rr.uniform(-1, 1)
        K.sphere((x, y, -0.1), 1, mats["silt"], scale=(rr.uniform(1.0, 1.8), rr.uniform(0.8, 1.4), 0.9))
    for i in range(30):
        x, y = rr.uniform(-40, 30), rr.uniform(-8, 8)
        K.person(x, y, rot=rr.uniform(0, 6.3), mats=mats, pose=rr.choice(["dig", "dig", "stand"]),
                 top=rr.choice([mats["hivis"], mats["cloth_dark"], mats["plaster_red"], mats["cloth_blue"], mats["hivis_y"]]))
        if rr.random() < 0.6:
            K.cylinder((x + 0.4, y - 0.5, 0.7), 0.02, 1.3, mats["wood"], verts=6, rot=(0.6, 0.2, 0))
    for i in range(5):
        x = rr.uniform(-30, 20)
        K.box((x, 3, 0.6), (1.2, 0.7, 0.4), wb, bevel=0.2)
    return [S("street", (-55, -2, 2.2), (10, 1, 0.5), lens=40, dof=40, fstop=8),
            S("high", (-45, -18, 12), (0, 2, 0), lens=30)]


@plate
def red_zone_cordon():
    K.reset(39)
    mats = K.M()
    K.sky(elev=25, rot=170, sun=3.0, haze=3)
    colombo(mats, collapse=lambda x: (int(x * 5.1) % 3) == 0, cars=0, trees=False, length=200)
    K.mesh_fence(-8, -10, -8, 10, mats=mats)
    red = K.mat("rzred", (0.65, 0.03, 0.02), bump=0)
    wht = K.mat("rzwht", (0.9, 0.9, 0.88), bump=0)
    K.sign("RED ZONE", (-8.3, -2, 1.7), 2.6, 0.7, red, wht, rot_z=-pi / 2, font=FONT)
    K.sign("NO ENTRY", (-8.3, 3, 1.7), 2.6, 0.7, wht, red, rot_z=-pi / 2, font=FONT)
    K.person(-11, 5, rot=pi / 2, mats=mats, top=K.mat("camo", (0.15, 0.17, 0.1), rough=0.9), helmet=True)
    return [S("cordon", (-30, 0.5, 1.7), (10, 1, 2.5), lens=35, dof=21, fstop=5.6)]


@plate
def demolition():
    K.reset(40)
    mats = K.M()
    K.sky(elev=30, rot=200, sun=3.5, haze=2.5)
    K.ground(3000, mats["asphalt"], z=-0.3)
    grav = K.mat("lot", (0.42, 0.4, 0.36), rough=0.95, var=0.3, bump=0.5, bump_scale=30)
    K.box((0, 30, -0.02), (200, 50, 0.05), grav)
    K.street(300, 12, 4, mats)
    K.excavator(-4, 20, rot=0.6, mats=mats)
    K.rubble_pile(6, 24, 9, 6, 3.5, n=300, mats=mats, slabs=8, rebar=30, seed=4)
    # half-demolished building: exposed floors
    for f in range(4):
        K.box((24, 30, f * 3.6 + 0.2), (14, 14, 0.4), mats["concrete"])
    for c in range(4):
        K.box((17.5 + c * 4.3, 23.5, 7.2), (0.5, 0.5, 14.4), mats["concrete"])
    K.facade_box(40, 23, 18, 14, 14, K.mat_facade((0.55, 0.53, 0.5)), 4)
    K.mesh_fence(-40, 6, 50, 6, mats=mats)
    return [S("lot", (-30, -14, 2), (8, 24, 4), lens=32)]


@plate
def residential_red_zone():
    K.reset(41)
    mats = K.M()
    K.sky(elev=30, rot=250, sun=4.0, haze=2, sun_color=(1, 0.88, 0.7))
    K.ground(4000, K.mat("overgrown", (0.2, 0.24, 0.08), rough=0.95, var=0.55, scale=0.5, bump=0.7, bump_scale=120))
    K.street(200, 9, 2, mats, lines=False)
    cracks(0, 0, 80, mats, seed=6, width=0.12, depth=0.3)
    rr = random.Random(6)
    for side in (-1, 1):
        for i in range(9):
            x = -90 + i * 20
            K.box((x, side * 11, 0.0), (3, 7, 0.05), mats["concrete"])  # orphaned driveways
            if rr.random() < 0.5:
                K.tree(x + rr.uniform(-6, 6), side * rr.uniform(14, 24), h=rr.uniform(5, 10), r=rr.uniform(2.5, 4),
                       mats=mats, seed=rr.randrange(999))
            if rr.random() < 0.3:
                for k in range(4):
                    K.box((x - 3 + k * 1.4, side * 8.0, 0.5), (1.2, 0.08, 0.9), mats["wood"],
                          rot=(0, rr.uniform(-0.2, 0.2), 0))
    for i in range(8):
        K.lamp_post(-80 + i * 22, -6, arm_dir=1, mats=mats)
    return [S("empty", (-60, 1.0, 1.7), (20, 0, 1.6), lens=35, dof=30, fstop=8),
            S("high", (-55, -25, 14), (0, 4, 0), lens=30)]


@plate
def container_mall():
    K.reset(42)
    mats = K.M()
    K.sky(elev=45, rot=210, sun=4.5)
    K.ground(3000, K.mat("plaza", (0.3, 0.29, 0.27), rough=0.8, var=0.2, bump=0.2, bump_scale=8))
    cols = [(0.75, 0.2, 0.1), (0.1, 0.35, 0.6), (0.85, 0.65, 0.1), (0.2, 0.5, 0.3), (0.9, 0.9, 0.88), (0.5, 0.1, 0.4),
            (0.95, 0.45, 0.1), (0.1, 0.55, 0.6)]
    rr = random.Random(3)
    for i in range(8):
        K.container(-28 + i * 7, 6, color=cols[i % 8], open_side=True, mats=mats)
        if rr.random() < 0.6:
            K.container(-28 + i * 7, 6, color=cols[(i + 3) % 8], z=2.59, mats=mats)
    for i in range(6):
        K.container(-18 + i * 7, -14, rot=pi, color=cols[(i + 5) % 8], open_side=True, mats=mats)
    for i in range(30):
        K.person(rr.uniform(-25, 25), rr.uniform(-9, 2), rot=rr.uniform(0, 6.3), mats=mats,
                 top=rr.choice([mats["cloth_dark"], mats["plaster_red"], mats["cloth_blue"], mats["plaster_white"]]))
    for x in (-20, 0, 20):
        K.tree(x, -4, h=5, r=2, mats=mats, seed=x)
    return [S("mall", (-34, -16, 2.0), (0, 4, 2.5), lens=30, dof=30, fstop=8)]


@plate
def cardboard_cathedral():
    K.reset(43)
    mats = K.M()
    K.sky(elev=12, rot=260, sun=4.5, sun_color=(1, 0.8, 0.6))
    K.ground(3000, mats["footpath"])
    K.box((0, 0, 0.0), (80, 80, 0.05), K.mat("lawn", (0.15, 0.22, 0.07), rough=0.9, var=0.4, bump=0.3, bump_scale=200))
    tube = K.mat("tube", (0.62, 0.5, 0.33), rough=0.75, var=0.08, scale=6, bump=0.15, bump_scale=200)
    H, Wd, L = 21, 27, 30
    ang = math.atan2(H, Wd / 2)
    n = 16
    for i in range(n):
        y = 4 + i * (L / n)
        for s_ in (-1, 1):
            ln = math.hypot(H, Wd / 2) * (1 - i * 0.012)
            c = K.cylinder((s_ * Wd / 4, y, H / 2 * (1 - i * 0.012)), 0.45, ln, tube, verts=20)
            c.rotation_euler = (0, s_ * -(pi / 2 - ang), 0)
    roofm = K.mat("polyc", (0.85, 0.85, 0.8), rough=0.2, transmission=0.6, bump=0)
    for s_ in (-1, 1):
        K.box((s_ * Wd / 4, 4 + L / 2, H / 2), (0.1, L, math.hypot(H, Wd / 2)), roofm, rot=(0, s_ * -(pi / 2 - ang), 0))
    # triangular coloured glass front
    cols = [(0.7, 0.2, 0.1), (0.1, 0.3, 0.6), (0.8, 0.6, 0.1), (0.2, 0.5, 0.3), (0.5, 0.1, 0.4)]
    for k in range(10):
        z0 = k * H / 10
        w = Wd * (1 - (z0 + H / 20) / H)
        for j in range(max(1, int(w / 2.4))):
            c = cols[(k + j) % 5]
            K.box((-w / 2 + (j + 0.5) * w / max(1, int(w / 2.4)), 3.6, z0 + H / 20), (w / max(1, int(w / 2.4)) - 0.08, 0.06, H / 10 - 0.08),
                  K.mat(f"sg{c}", c, rough=0.1, emit=c, emit_str=0.6, bump=0))
    for s_ in (-1, 1):
        K.box((s_ * 6, 3.0, 1.8), (4, 3, 3.6), mats["metal_dark"])
    return [S("front", (-10, -38, 1.6), (0, 4, 9), lens=30)]


@plate
def avon_park():
    K.reset(44)
    mats = K.M()
    K.sky(elev=25, rot=240, sun=4.5, sun_color=(1, 0.85, 0.65), haze=1.5)

    def hf(x, y):
        d = abs(y - 8 * math.sin(x / 30))
        return -1.5 if d < 9 else min(0.0, -1.5 + (d - 9) * 0.5)

    K.grid_terrain("banks", 400, 200, 400, 200, hf, mats["grass"])
    K.box((0, 0, -0.9), (400, 200, 0.02), mats["water"])
    rr = random.Random(5)
    for i in range(30):
        x = rr.uniform(-150, 150)
        side = rr.choice([-1, 1])
        y = 8 * math.sin(x / 30) + side * rr.uniform(14, 50)
        K.tree(x, y, h=rr.uniform(8, 16), r=rr.uniform(3, 5.5), mats=mats, seed=rr.randrange(999))
    # willow-ish drooping trees at the edge
    for i in range(8):
        x = rr.uniform(-100, 100)
        y = 8 * math.sin(x / 30) + rr.choice([-12, 12])
        K.tree(x, y, h=9, r=5, mats=mats, seed=rr.randrange(999),
               leaves=K.mat("willow", (0.15, 0.22, 0.05), rough=0.8, var=0.4, bump=0.6, bump_scale=60))
    return [S("river", (-70, -16, 2.5), (40, 5, 0), lens=30)]


@plate
def memorial_wall():
    K.reset(45)
    mats = K.M()
    K.sky(elev=18, rot=250, sun=4.5, sun_color=(1, 0.8, 0.6), haze=1.5)
    K.ground(3000, mats["grass"])
    K.box((0, 30, -0.9), (400, 30, 0.02), mats["water"])
    marble = K.mat("marble", (0.82, 0.81, 0.78), rough=0.25, var=0.06, scale=1, bump=0.03, coat=0.4)
    names = K.mat_facade((0.82, 0.81, 0.78), glass=(0.25, 0.25, 0.25), bay=1.2, floor=0.09, frac=0.55, name="names", rough=0.3)
    R0 = 40
    for i in range(36):
        a = math.radians(-35 + i * 2)
        x, y = math.sin(a) * R0, -math.cos(a) * R0 + 40
        K.box((x, y, 1.4), (2.4, 0.5, 2.8), marble, rot=(0, 0, a))
        K.box((x - math.sin(a) * 0.0, y - math.cos(a) * 0.26 + 0.0, 1.5), (2.2, 0.02, 1.6), names, rot=(0, 0, a))
    K.box((0, -1.5, 0.02), (60, 3.0, 0.04), K.mat("path", (0.5, 0.48, 0.44), rough=0.8, bump=0.2))
    rr = random.Random(2)
    for i in range(10):
        K.tree(rr.uniform(-60, 60), rr.uniform(20, 50), h=rr.uniform(8, 13), r=rr.uniform(3, 5), mats=mats,
               seed=rr.randrange(99))
    return [S("wall", (-22, -12, 1.6), (6, 2, 1.4), lens=35, dof=18, fstop=4),
            S("names", (-3, -3.2, 1.6), (3, 1.0, 1.4), lens=50, dof=3.5, fstop=2.8)]


@plate
def modern_city():
    K.reset(46)
    mats = K.M()
    K.sky(elev=8, rot=280, sun=5.5, sun_color=(1, 0.7, 0.45), haze=2)
    K.ground(12000, mats["asphalt"])
    K.street(400, 14, 5, mats)
    rr = random.Random(3)
    x = -150
    while x < 150:
        w = rr.uniform(16, 30)
        for side in (-1, 1):
            h = rr.uniform(10, 26)
            g = K.mat_facade((0.25, 0.27, 0.3), glass=(0.05, 0.08, 0.1), bay=1.6, floor=3.6, frac=0.12, rough=0.3)
            K.box((x + w / 2, side * (12 + 10), h / 2), (w - 1, 20, h), g)
        x += w
    for i in range(-6, 7):
        K.tree(i * 22, -10, h=7, r=2.5, mats=mats, seed=i + 50)
    K.atmosphere(size=(8000, 8000, 600), center=(0, 0, 300), density=0.0006, color=(1, 0.85, 0.7))
    return [S("sunset", (-90, -2, 1.7), (40, 1, 8), lens=35, dof=50, fstop=8)]


@plate
def city_sunset_aerial():
    K.reset(47)
    mats = K.M()
    K.sky(elev=4, rot=290, sun=5.0, sun_color=(1, 0.6, 0.35), haze=2.5)
    K.ground(12000, K.mat("plains2", (0.15, 0.17, 0.08), rough=0.95, var=0.5, scale=0.02, bump=0.1))
    K.box((0, 0, -0.08), (1400, 1400, 0.1), mats["asphalt"])
    K.city_grid(0, 0, 1300, 1300, block=80, seed=18, hmin=6, hmax=18, tall=0.03, lit=1.5)
    K.city_trees(0, 0, 1400, 1400, 500, mats, seed=7)
    hill = K.mat("hills", (0.22, 0.2, 0.1), rough=0.95, var=0.45, scale=0.01, bump=0.3, bump_scale=0.1, grime=0.3)
    K.grid_terrain("ph", 9000, 2500, 220, 70,
                   lambda x, y: max(0.0, (1 - abs(y - 2600) / 1250)) ** 1.3 * 480 * (0.7 + 0.5 * K.noise2(x, y, 4, 4, 0.0015)) - 5,
                   hill)
    K.atmosphere(size=(16000, 16000, 1200), center=(0, 0, 600), density=0.0003, color=(1, 0.8, 0.65))
    return [S("dusk", (-800, -1100, 300), (100, 600, 0), lens=35)]


@plate
def suburb_day():
    K.reset(48)
    mats = K.M()
    K.sky(elev=30, rot=250, sun=4.0, sun_color=(1, 0.85, 0.7))
    suburb(mats, seed=11, cars=4)
    return [S("street", (-55, 1.5, 1.7), (20, -1, 2.0), lens=35, dof=30, fstop=8)]


# ------------------------------------------------------------------ runner
def run(name, samples=None, preview=False, skip=False):
    t = time.time()
    os.makedirs(OUT, exist_ok=True)
    shots = PLATES[name]()
    sc = K.bpy.context.scene
    for s in shots:
        path = os.path.join(OUT, f"{name}_{s['name']}" + ("_prev" if preview else "") + ".png")
        if skip and os.path.exists(path) and not preview:
            continue
        for ob in [o for o in K.bpy.data.objects if o.type == "CAMERA"]:
            K.bpy.data.objects.remove(ob)
        K.camera(s["loc"], s["look"], lens=s["lens"], dof=s["dof"], fstop=s["fstop"])
        sc.render.film_transparent = s["sky"]
        sc.render.image_settings.file_format = "PNG"
        sc.render.image_settings.color_mode = "RGBA"
        sc.render.image_settings.compression = 30
        if preview:
            K.render(path, samples=12, res=(704, 396))
        else:
            K.render(path, samples=samples or s["samples"] or 12, res=(1600, 900))
        print(f"[plate] {name}_{s['name']} {time.time() - t:.1f}s", flush=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    samples = None
    if "--samples" in args:
        i = args.index("--samples")
        samples = int(args[i + 1])
        del args[i:i + 2]
    preview = "--preview" in args
    skip = "--skip-existing" in args
    args = [a for a in args if not a.startswith("--") or a == "--all"]
    if args == ["--all"]:
        args = list(PLATES)
    for n in args:
        try:
            run(n, samples, preview, skip)
        except Exception as e:  # keep going; report
            import traceback
            traceback.print_exc()
            print(f"[plate-error] {n}: {e}", flush=True)
