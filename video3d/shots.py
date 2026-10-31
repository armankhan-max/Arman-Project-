"""The 10 shots of the video. Each build_* function builds a scene in Blender and returns its frame count.

Timeline (30 fps, voice delayed 0.25 s), see timeline.json for the exact words.
"""
import math
import random

import bpy
from mathutils import Matrix, Vector

import lib3d as L

SHOTS = []  # (name, n_frames, builder)


def shot(name, n):
    def deco(fn):
        SHOTS.append((name, n, fn))
        return fn
    return deco


def handheld(cam, amount=0.004, speed=30):
    if not any(fc.data_path == "rotation_euler" for fc in L.fcurves_of(cam)):
        cam.keyframe_insert("rotation_euler", frame=0)
    L.add_noise(cam, "rotation_euler", amount, speed)


def wobble_from(obj, f_start, amount, speed=6.0, rot=0.25):
    """Noise wobble active only from f_start (so popped-in germs stay invisible before)."""
    if not any(fc.data_path == "scale" for fc in L.fcurves_of(obj)):
        obj.keyframe_insert("scale", frame=0)
    if not any(fc.data_path == "rotation_euler" for fc in L.fcurves_of(obj)):
        obj.keyframe_insert("rotation_euler", frame=0)
    for fc in L.fcurves_of(obj):
        if fc.data_path in ("scale", "rotation_euler"):
            m = fc.modifiers.new("NOISE")
            m.strength = amount if fc.data_path == "scale" else rot
            m.scale = speed if fc.data_path == "scale" else speed * 2
            m.phase = random.uniform(0, 100)
            if f_start > 0:
                m.use_restricted_range = True
                m.frame_start = f_start
                m.frame_end = 100000
                m.blend_in = 4


def screen_germs(parent, n, seed, size=(0.05, 0.1), region=(-0.3, 0.3, -0.66, 0.66), z=0.045, crawl=0.0,
                 n_frames=60, hair=False):
    rnd = random.Random(seed)
    gs = L.germ_cluster(None, 0, n, size=size, seed=seed, parent=parent, flat_z=z, region=region, hair=hair)
    for g in gs:
        s = g.scale[0]
        if crawl:
            p0 = g.location.copy()
            a = rnd.uniform(0, 6.28)
            d = Vector((math.cos(a), math.sin(a), 0)) * crawl * rnd.uniform(0.4, 1.0)
            L.key(g, 0, loc=p0)
            L.key(g, n_frames, loc=p0 + d)
            for fc in L.fcurves_of(g):
                if fc.data_path == "location":
                    for kp in fc.keyframe_points:
                        kp.interpolation = "LINEAR"
        wobble_from(g, 0, s * 0.12)
    return gs


# ------------------------------------------------------------------ sets
def bathroom_set():
    L.reset(world_color=(0.75, 0.8, 0.85), world_strength=0.5)
    floor_m = L.tile_mat("FloorTiles", (0.32, 0.34, 0.38), (0.15, 0.15, 0.17), scale=1.2, rough=0.15)
    wall_m = L.tile_mat("WallTiles", (0.82, 0.9, 0.92), (0.6, 0.64, 0.66), scale=1.6, rough=0.05)
    L.plane((14, 14), (0, 0, 0), mat=floor_m, name="Floor")
    L.plane((14, 8), (0, 1.15, 4), rot=(math.pi / 2, 0, 0), mat=wall_m, name="Wall")
    cer = L.bsdf_mat("Ceramic", (0.9, 0.91, 0.92), rough=0.1, coat=0.6)
    # pedestal + bowl via lathe, stretched front-to-back
    prof = [(0.0, 0.0), (0.36, 0.0), (0.38, 0.06), (0.3, 0.25), (0.28, 0.55), (0.42, 0.78), (0.58, 0.95),
            (0.63, 1.02), (0.6, 1.04), (0.5, 1.0), (0.38, 0.9), (0.25, 0.75), (0.0, 0.7)]
    bowl = L.lathe(prof, (0, -0.15, 0), (1, 1.3, 1), mat=cer, name="Bowl")
    water = L.bsdf_mat("Water", (0.6, 0.8, 0.9), rough=0.02, transmission=1.0, ior=1.33)
    w = L.cylinder(0.36, 0.01, (0, -0.15, 0.8), mat=water, name="WaterSurf")
    w.scale = (1, 1.28, 1)
    seat_m = L.bsdf_mat("Seat", (0.95, 0.95, 0.96), rough=0.18, coat=0.5)
    seat = L.torus(0.47, 0.13, (0, -0.17, 1.1), scale=(1.0, 1.32, 0.38), mat=seat_m, name="Seat")
    # lid leaning back
    lid = L.cylinder(0.6, 0.06, (0, 0.38, 1.68), rot=(math.radians(-80), 0, 0), mat=seat_m, name="Lid", bevel=0.025)
    lid.scale = (1, 1.3, 1)
    tank = L.box((1.25, 0.45, 0.95), (0, 0.78, 1.55), bevel=0.09, mat=cer, name="Tank")
    tank_lid = L.box((1.32, 0.52, 0.08), (0, 0.78, 2.06), bevel=0.035, mat=cer, name="TankLid")
    chrome = L.bsdf_mat("Chrome", (0.9, 0.9, 0.92), rough=0.06, metal=1.0)
    L.cylinder(0.07, 0.04, (0, 0.72, 2.11), mat=chrome, name="Flush")
    # a towel on the wall and a plant for set dressing
    towel_m = L.bsdf_mat("Towel", (0.25, 0.55, 0.65), rough=0.95)
    tw = L.box((0.7, 0.08, 1.2), (-1.7, 1.08, 2.0), bevel=0.04, mat=towel_m, name="Towel")
    L.cylinder(0.03, 1.0, (-1.7, 1.05, 2.62), rot=(0, math.pi / 2, 0), mat=chrome, name="Rail")
    return {"seat": seat, "chrome": chrome}


def table_set(dark=False):
    L.reset(world_color=(0.55, 0.5, 0.45), world_strength=0.35)
    L.plane((12, 12), (0, 0, 0), mat=L.wood_mat("Table", scale=0.7), name="Table")
    wall = L.bsdf_mat("Wall", (0.55, 0.62, 0.68) if not dark else (0.2, 0.22, 0.28), rough=0.8)
    L.plane((14, 8), (0, 4.0, 3), rot=(math.pi / 2, 0, 0), mat=wall, name="BackWall")
    # coffee mug in background
    mug_m = L.bsdf_mat("Mug", (0.85, 0.3, 0.2), rough=0.2, coat=0.7)
    L.lathe([(0.0, 0.0), (0.33, 0.0), (0.35, 0.05), (0.36, 0.8), (0.32, 0.8), (0.31, 0.06), (0.0, 0.06)],
            (1.5, 1.8, 0), mat=mug_m, name="Mug")
    L.torus(0.18, 0.045, (1.88, 1.8, 0.42), rot=(math.pi / 2, 0, 0), mat=mug_m, name="Handle")
    # crumbs
    rnd = random.Random(5)
    crumb_m = L.bsdf_mat("Crumb", (0.55, 0.35, 0.15), rough=0.8)
    for i in range(14):
        c = L.sphere(rnd.uniform(0.008, 0.02), (rnd.uniform(-1.0, 1.0), rnd.uniform(-1.2, 1.2), 0.008),
                     scale=(1, rnd.uniform(0.6, 1.4), 0.6), mat=crumb_m, name="Crumb", seg=8)
    L.area_light((-3, -2, 4), (0, 0, 0), 700, 3.5, (1.0, 0.9, 0.78))
    L.area_light((3, -1.5, 2), (0, 0, 0), 220, 4, (0.75, 0.85, 1.0))
    L.area_light((0.5, 4, 3), (0, 0, 0), 450, 2.5, (1.0, 0.95, 0.9))


# ------------------------------------------------------------------ shots
@shot("s01_phone_vs_toilet", 78)
def s01(n):
    bathroom_set()
    root, scr, sb = L.phone((-0.22, -0.42, 1.175), rot=(0.02, -0.03, 0.35))
    screen_germs(root, 30, seed=1, size=(0.03, 0.06), crawl=0.08, n_frames=n)
    # just a few on the seat
    for i, p in enumerate([(0.45, -0.5, 1.15), (0.3, -0.85, 1.14), (0.42, 0.12, 1.15)]):
        g = L.germ(p, 0.04, seed=900 + i)
        wobble_from(g, 0, 0.005)
    L.studio_lights((0, -0.3, 1.2), key=700, fill=220, rim=500, scale=0.8)
    tgt = L.empty((0.0, -0.4, 1.15), "CamTarget")
    cam = L.camera((-0.55, -1.85, 2.15), tgt.location, lens=38, dof_dist=root, fstop=2.2)
    L.cam_track(cam, tgt)
    L.key(cam, 0, loc=(-0.45, -1.7, 2.05))
    L.key(cam, n - 1, loc=(0.35, -3.0, 2.55))
    L.key(tgt, 0, loc=(-0.22, -0.42, 1.18))
    L.key(tgt, n - 1, loc=(0.0, -0.25, 1.15))
    handheld(cam)


@shot("s02_toilet_cleaned", 68)
def s02(n):
    s = bathroom_set()
    L.studio_lights((0, -0.3, 1.2), key=700, fill=220, rim=500, scale=0.8)
    tgt = L.empty((0.0, -0.3, 1.1), "CamTarget")
    cam = L.camera((0.9, -1.9, 2.0), tgt.location, lens=35, dof_dist=1.9, fstop=4)
    L.cam_track(cam, tgt)
    L.key(cam, 0, loc=(0.95, -1.95, 2.05))
    L.key(cam, n - 1, loc=(0.55, -1.75, 1.85))
    handheld(cam)
    # germs on seat that get wiped
    rnd = random.Random(2)
    seat_germs = []
    for i in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        p = Vector((0.47 * math.cos(a), -0.17 + 0.47 * 1.32 * math.sin(a), 1.17))
        g = L.germ(p, rnd.uniform(0.035, 0.06), seed=300 + i)
        wobble_from(g, 0, 0.005)
        seat_germs.append((g, a))
    # spray bottle
    blue = L.bsdf_mat("Bottle", (0.1, 0.45, 0.95), rough=0.15, transmission=0.6, coat=0.5)
    white = L.bsdf_mat("Trigger", (0.95, 0.95, 0.95), rough=0.3)
    bot = L.empty((1.1, -0.6, 1.9), "Bottle")
    body = L.lathe([(0, -0.6), (0.17, -0.6), (0.19, -0.55), (0.19, 0.1), (0.1, 0.25), (0.07, 0.3), (0, 0.3)],
                   (0, 0, 0), mat=blue, name="BottleBody")
    body.parent = bot
    head = L.box((0.14, 0.32, 0.18), (0, -0.08, 0.4), bevel=0.04, mat=white, name="Head")
    head.parent = bot
    trig = L.box((0.06, 0.06, 0.2), (0, -0.14, 0.25), bevel=0.02, mat=white, name="Trig")
    trig.parent = bot
    bot.rotation_euler = (0.5, 0, 0.6)
    L.key(bot, 0, loc=(2.6, -0.5, 3.2))
    L.key(bot, 6, loc=(0.85, -0.75, 1.75))
    L.key(bot, 22, loc=(0.85, -0.75, 1.75))
    L.key(bot, 30, loc=(2.6, -0.5, 3.2))
    for f in (8, 15):
        L.key(trig, f, loc=(0, -0.14, 0.25))
        L.key(trig, f + 2, loc=(0, -0.08, 0.25))
        L.key(trig, f + 5, loc=(0, -0.14, 0.25))
    # mist
    mist_m = L.bsdf_mat("Mist", (0.9, 0.95, 1.0), rough=0.1, transmission=0.9, ior=1.33)
    nozzle = Vector((0.66, -0.98, 1.95))
    for k in range(36):
        f0 = 9 + (k % 2) * 7 + rnd.randint(0, 3)
        d = Vector((rnd.uniform(-0.9, -0.4), rnd.uniform(0.2, 0.9), rnd.uniform(-1.0, -0.6)))
        drop = L.sphere(rnd.uniform(0.01, 0.025), nozzle, mat=mist_m, name="Drop", seg=12)
        L.key(drop, f0 - 1, loc=nozzle, scale=0)
        L.key(drop, f0, loc=nozzle, scale=1)
        L.key(drop, f0 + 9, loc=nozzle + d * rnd.uniform(0.7, 1.1), scale=0.6)
        L.key(drop, f0 + 11, scale=0)
    # sponge wiping around the seat (half circle front)
    sp_m = L.bsdf_mat("Sponge", (1.0, 0.8, 0.15), rough=0.9)
    scrub_m = L.bsdf_mat("Scrub", (0.1, 0.55, 0.2), rough=1.0)
    sp = L.empty((0, 0, 0), "Sponge")
    sb = L.box((0.42, 0.26, 0.14), (0, 0, 0.1), bevel=0.04, mat=sp_m, name="SpongeBody")
    sb.parent = sp
    sc_ = L.box((0.42, 0.26, 0.05), (0, 0, 0.005), bevel=0.02, mat=scrub_m, name="SpongeScrub")
    sc_.parent = sp
    f_start, f_end = 28, 60
    angs = []
    for i, f in enumerate(range(f_start, f_end + 1, 2)):
        t = i / ((f_end - f_start) / 2)
        a = math.radians(170) + t * math.radians(370)
        p = Vector((0.47 * math.cos(a), -0.17 + 0.47 * 1.32 * math.sin(a), 1.17))
        L.key(sp, f, loc=p, rot=(0, 0, a + math.pi / 2 + 0.25 * math.sin(f)))
        angs.append((f, a))
    L.key(sp, 0, loc=(-2.5, -0.6, 2.2), scale=1)
    L.key(sp, f_start - 6, loc=(-1.0, -0.5, 1.5), scale=1)
    L.key(sp, f_end + 6, loc=(-1.6, -0.3, 1.9))
    # germs vanish when sponge reaches them
    for g, a in seat_germs:
        aa = (a - math.radians(170)) % (2 * math.pi)
        t = aa / math.radians(370)
        f = int(f_start + min(t, 1) * (f_end - f_start)) + 1
        L.pop_out(g, f, g.scale[0], dur=4)
    pts = []
    for i in range(10):
        a = rnd.uniform(0, 2 * math.pi)
        pts.append((0.47 * math.cos(a), -0.17 + 0.47 * 1.32 * math.sin(a), 1.25 + rnd.uniform(0, 0.15)))
    L.sparkle_burst(cam, pts, 50, size=0.07, seed=2, hold=8)


@shot("s03_phone_never_cleaned", 52)
def s03(n):
    table_set()
    root, scr, sb = L.phone((0, 0, 0.04), rot=(0, 0, 0.35))
    screen_germs(root, 34, seed=3, size=(0.045, 0.095), crawl=0.12, n_frames=n)
    tgt = L.empty((0, 0, 0.05), "CamTarget")
    cam = L.camera((0.2, -2.3, 1.1), tgt.location, lens=45, dof_dist=root, fstop=1.8)
    L.cam_track(cam, tgt)
    L.key(cam, 0, loc=(0.6, -2.4, 1.15))
    L.key(cam, n - 1, loc=(0.05, -1.55, 0.75))
    handheld(cam)


@shot("s04_door_handle", 35)
def s04(n):
    L.reset(world_color=(0.6, 0.6, 0.6), world_strength=0.4)
    door_m, nt, N, Ln, b = L.node_mat("Door")
    b.inputs["Base Color"].default_value = (0.42, 0.58, 0.62, 1)
    b.inputs["Roughness"].default_value = 0.35
    L.plane((8, 10), (0, 0, 0), rot=(math.pi / 2, 0, 0), mat=door_m, name="Door")
    chrome = L.bsdf_mat("Brass", (0.95, 0.78, 0.45), rough=0.12, metal=1.0)
    L.cylinder(0.3, 0.06, (0, -0.03, 0), rot=(math.pi / 2, 0, 0), mat=chrome, name="Rosette", bevel=0.02)
    pivot = L.empty((0, -0.35, 0), "Pivot")
    neck = L.cylinder(0.1, 0.36, (0, 0.17, 0), rot=(math.pi / 2, 0, 0), mat=chrome, name="Neck")
    neck.parent = pivot
    lever = L.cylinder(0.11, 1.1, (0.55, 0, 0), rot=(0, math.pi / 2, 0), mat=chrome, name="Lever")
    lever.parent = pivot
    cap = L.sphere(0.12, (1.1, 0, 0), scale=(0.8, 1, 1), mat=chrome, name="Cap")
    cap.parent = pivot
    knob = L.sphere(0.13, (0, 0, 0), mat=chrome, name="Knob")
    knob.parent = pivot
    # germs on lever
    rnd = random.Random(4)
    for i in range(10):
        x = rnd.uniform(0.15, 1.1)
        a = rnd.uniform(-0.6, 3.6)
        p = (x, -0.12 * math.sin(a), 0.12 * math.cos(a))
        g = L.germ(p, rnd.uniform(0.04, 0.07), seed=400 + i, parent=pivot)
        wobble_from(g, 0, 0.006)
    # hand grabs lever and pushes down
    h = L.hand("Hand", curl=(0.72, 0.72, 0.75, 0.78), thumb=0.9, spread=0.03)
    h.parent = pivot
    grip = Vector((0.5, -0.95, 0.33))
    L.key(h, 0, loc=grip + Vector((0.5, -1.4, 0.9)), rot=(0.3, 0, -0.2))
    L.key(h, 11, loc=grip + Vector((0, -0.02, 0.03)), rot=(0, 0, 0))
    L.key(h, 13, loc=grip, rot=(0, 0, 0))
    L.key(pivot, 14, rot=(0, 0, 0))
    L.key(pivot, 24, rot=(0, 0.55, 0))
    L.key(pivot, n, rot=(0, 0.6, 0))
    # germs jump onto the hand
    tips = L.fingertip_points((0.72, 0.72, 0.75, 0.78), 0.03)
    for i in range(7):
        fi = i % 4
        seg = rnd.choice([1, 2])
        p = tips[fi][seg] + Vector((0, -0.05, 0.1))
        g = L.germ(p, rnd.uniform(0.045, 0.07), seed=450 + i, parent=h)
        L.pop_in(g, 14 + i * 2, g.scale[0])
        wobble_from(g, 22 + i * 2, 0.006)
    L.studio_lights((0.5, -0.4, 0), key=650, fill=200, rim=500, scale=0.8)
    tgt = L.empty((0.45, -0.4, 0.0), "CamTarget")
    cam = L.camera((1.9, -2.3, 1.4), tgt.location, lens=40, dof_dist=2.8, fstop=3.2)
    L.cam_track(cam, tgt)
    L.key(cam, 0, loc=(2.0, -2.4, 1.5))
    L.key(cam, n - 1, loc=(1.7, -2.0, 1.1))
    handheld(cam)


@shot("s05_dollar_bill", 37)
def s05(n):
    table_set()
    m, b, tex = L.image_mat("Bill", L.HERE + "/assets/bill.png", rough=0.7)
    bill = L.plane((1.56, 0.66), (0, 0.1, 0.01), mat=m, name="Bill")
    sub = bill.modifiers.new("Sub", "SUBSURF")
    sub.subdivision_type = "SIMPLE"
    sub.levels = sub.render_levels = 5
    tx = bpy.data.textures.new("Crease", "CLOUDS")
    tx.noise_scale = 0.35
    d = bill.modifiers.new("Disp", "DISPLACE")
    d.texture = tx
    d.strength = 0.05
    d.mid_level = 0.2
    bill.rotation_euler = (0, 0, -0.25)
    rnd = random.Random(5)
    for i in range(16):
        p = (rnd.uniform(-0.65, 0.65), rnd.uniform(-0.25, 0.25), 0.05)
        g = L.germ(p, rnd.uniform(0.04, 0.075), seed=500 + i, parent=bill)
        wobble_from(g, 0, 0.006)
    curl = (0.18, 0.15, 0.2, 0.25)
    h = L.hand("Hand", curl=curl, thumb=0.4, spread=0.06, scale=0.95)
    L.key(h, 0, loc=(0.6, -2.4, 0.9), rot=(-0.05, 0, 0.35))
    L.key(h, 14, loc=(0.35, -1.55, 0.25), rot=(-0.12, 0, 0.3))
    L.key(h, 17, loc=(0.35, -1.55, 0.2), rot=(-0.14, 0, 0.3))
    L.key(h, n, loc=(0.38, -1.62, 0.32), rot=(-0.1, 0, 0.3))
    tips = L.fingertip_points(curl, 0.06)
    for i in range(6):
        p = tips[i % 4][3 - (i // 4)] + Vector((0, -0.06, 0.1))
        g = L.germ(p, rnd.uniform(0.045, 0.07), seed=550 + i, parent=h)
        L.pop_in(g, 18 + i * 2, g.scale[0])
        wobble_from(g, 26 + i * 2, 0.006)
    tgt = L.empty((0.05, -0.1, 0.05), "CamTarget")
    cam = L.camera((-0.6, -2.2, 2.0), tgt.location, lens=40, dof_dist=2.7, fstop=3.5)
    L.cam_track(cam, tgt)
    L.key(cam, 0, loc=(-0.7, -2.2, 2.1))
    L.key(cam, n - 1, loc=(-0.35, -2.0, 1.7))
    handheld(cam)


def chip_mesh(seed):
    rnd = random.Random(seed)
    bpy.ops.mesh.primitive_circle_add(vertices=32, radius=0.22, fill_type="TRIFAN")
    o = bpy.context.object
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts=3)
    bpy.ops.object.mode_set(mode="OBJECT")
    k = rnd.uniform(2.5, 4.0)
    ph = rnd.uniform(0, 6)
    for v in o.data.vertices:
        x, y = v.co.x, v.co.y
        r = math.hypot(x, y)
        ang = math.atan2(y, x)
        rr = 1 + 0.08 * math.sin(ang * 5 + ph)
        v.co.x *= rr
        v.co.y *= rr
        v.co.z = k * (x * x - y * y) * 0.5
    so = o.modifiers.new("Solid", "SOLIDIFY")
    so.thickness = 0.012
    L.smooth(o, subsurf=1)
    return o


@shot("s06_snack", 26)
def s06(n):
    table_set()
    bowl_m = L.bsdf_mat("BowlM", (0.9, 0.9, 0.88), rough=0.15, coat=0.6)
    L.lathe([(0, 0), (0.45, 0), (0.5, 0.04), (0.85, 0.42), (0.88, 0.46), (0.84, 0.46), (0.46, 0.06), (0, 0.06)],
            (0, 0.2, 0), mat=bowl_m, name="Bowl")
    chip_m, nt, N, Ln, b = L.node_mat("Chip")
    b.inputs["Base Color"].default_value = (0.9, 0.45, 0.08, 1)
    b.inputs["Roughness"].default_value = 0.35
    b.inputs["Subsurface Weight"].default_value = 0.3
    b.inputs["Subsurface Radius"].default_value = (1, 0.6, 0.2)
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 30
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    Ln.new(nz.outputs["Fac"], bump.inputs["Height"])
    Ln.new(bump.outputs["Normal"], b.inputs["Normal"])
    rnd = random.Random(6)
    for i in range(34):
        c = chip_mesh(600 + i)
        r = rnd.uniform(0, 0.6)
        a = rnd.uniform(0, 6.28)
        c.location = (r * math.cos(a), 0.2 + r * math.sin(a), 0.12 + (0.6 - r) * 0.25 + rnd.uniform(0, 0.12))
        c.rotation_euler = (rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(0, 6.28))
        L.assign(c, chip_m)
    # picked chip follows the hand
    pick = chip_mesh(699)
    L.assign(pick, chip_m)
    curl = (0.45, 0.5, 0.6, 0.65)
    h = L.hand("Hand", curl=curl, thumb=0.95, spread=0.04, scale=0.9)
    top = Vector((0.1, -1.0, 1.3))
    low = Vector((0.05, -0.75, 0.55))
    L.key(h, 0, loc=top, rot=(-0.55, 0, 0.15))
    L.key(h, 9, loc=low, rot=(-0.6, 0, 0.15))
    L.key(h, 12, loc=low, rot=(-0.6, 0, 0.15))
    L.key(h, n, loc=top + Vector((0.1, -0.3, 0.2)), rot=(-0.45, 0, 0.2))
    bpy.context.view_layer.update()
    tip = L.fingertip_points(curl, 0.04)[0][3]
    # the picked chip rides on the fingertips once the hand closes over the bowl
    pick.parent = h
    pick.location = tip + Vector((-0.12, 0.05, -0.14))
    pick.rotation_euler = (0.9, 0.2, 0)
    L.key(pick, 10, scale=0)
    L.key(pick, 11, scale=1.0 / 0.9 * 0.9)
    # germs/grease on fingers
    tips = L.fingertip_points(curl, 0.04)
    for i in range(6):
        p = tips[i % 4][2 + (i // 4)] + Vector((0, -0.05, 0.1))
        g = L.germ(p, rnd.uniform(0.05, 0.075), seed=650 + i, parent=h)
        L.pop_in(g, 12 + i * 2, g.scale[0])
        wobble_from(g, 20 + i * 2, 0.006)
    tgt = L.empty((0.0, -0.1, 0.4), "CamTarget")
    cam = L.camera((1.6, -2.2, 1.7), tgt.location, lens=38, dof_dist=2.5, fstop=3.5)
    L.cam_track(cam, tgt)
    L.key(cam, 0, loc=(1.7, -2.3, 1.8))
    L.key(cam, n - 1, loc=(1.4, -2.1, 1.5))
    handheld(cam)


def finger_surface_points(curl, spread, finger, n, seed, radius=0.09, segs=(0, 1, 2), up=Vector((0, 0, 1))):
    rnd = random.Random(seed)
    pts = L.fingertip_points(curl, spread)[finger]
    out = []
    for i in range(n):
        s = rnd.choice(segs)
        a, b = pts[s], pts[s + 1]
        t = rnd.uniform(0.1, 0.95)
        c = a.lerp(b, t)
        axis = (b - a).normalized()
        v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1)))
        v = v - axis * v.dot(axis)
        if v.dot(up) < 0:
            v = -v
        v = (v.normalized() + up * 0.6).normalized()
        v = v - axis * v.dot(axis)
        out.append(c + v.normalized() * radius)
    return out


@shot("s07_bacteria_fingers", 51)
def s07(n):
    L.reset(world_color=(0.05, 0.06, 0.1), world_strength=0.3)
    back = L.bsdf_mat("Back", (0.04, 0.05, 0.09), rough=0.9)
    L.plane((20, 20), (0, 6, 0), rot=(math.pi / 2, 0, 0), mat=back, name="Back")
    curl = (0.04, 0.95, 1.0, 1.0)
    h = L.hand("Hand", curl=curl, thumb=0.9, spread=0.03)
    h.rotation_euler = (0.25, 0.0, 0.5)
    rnd = random.Random(7)
    pts = finger_surface_points(curl, 0.03, 0, 26, 7, radius=0.1)
    pts += finger_surface_points(curl, 0.03, 1, 6, 8, radius=0.1, segs=(0,))
    word_f = 2  # "bacteria" starts right as the shot begins
    for i, p in enumerate(pts):
        g = L.germ(p, rnd.uniform(0.035, 0.065), seed=700 + i, parent=h)
        f = word_f + int(i * 1.1)
        L.pop_in(g, f, g.scale[0])
        wobble_from(g, f + 8, 0.006)
    tip = L.fingertip_points(curl, 0.03)[0]
    bpy.context.view_layer.update()
    tip_w = h.matrix_world @ ((tip[2] + tip[3]) / 2)
    tgt = L.empty(tip_w, "CamTarget")
    cam = L.camera(tip_w + Vector((-0.9, -1.3, 0.8)), tgt.location, lens=60, dof_dist=tgt, fstop=2.0)
    L.cam_track(cam, tgt)
    L.key(cam, 0, loc=tip_w + Vector((-1.2, -1.5, 0.9)))
    L.key(cam, n - 1, loc=tip_w + Vector((0.2, -1.25, 0.75)))
    L.key(tgt, 0, loc=tip_w + Vector((-0.05, 0, 0)))
    L.key(tgt, n - 1, loc=h.matrix_world @ tip[2])
    handheld(cam, 0.003)
    # dramatic lights: warm key, colored rims
    L.area_light(tip_w + Vector((-2, -2, 3)), tip_w, 350, 2.5, (1.0, 0.92, 0.85))
    L.area_light(tip_w + Vector((2.5, 2, 1)), tip_w, 600, 2, (0.3, 1.0, 0.5))
    L.area_light(tip_w + Vector((-2.5, 2, 0.5)), tip_w, 500, 2, (0.6, 0.3, 1.0))


def pointing_hand_at(target, curl, rot, scale=0.95, lift=Vector((0, 0, 0))):
    """Return the hand origin that puts the index tip at target for the given rotation."""
    tip = L.fingertip_points(curl, 0.03)[0][3] + Vector((0, 0, -0.085))
    R = rot.to_matrix()
    return Vector(target) - (R @ tip) * scale + lift


@shot("s08_tap_screen", 52)
def s08(n):
    table_set()
    root, scr, sb = L.phone((0, 0, 0.04), rot=(0, 0, 0.0))
    from mathutils import Euler
    curl = (0.08, 0.95, 1.0, 1.0)
    rot = Euler((-0.65, 0.15, 0.45))
    h = L.hand("Hand", curl=curl, thumb=0.9, spread=0.03, scale=0.95)
    taps = [(14, Vector((0.05, -0.1, 0.085))), (31, Vector((-0.1, 0.3, 0.085)))]
    o_up0 = pointing_hand_at(taps[0][1], curl, rot, lift=Vector((0.3, -0.5, 0.6)))
    L.key(h, 0, loc=o_up0, rot=rot)
    for f, p in taps:
        down = pointing_hand_at(p, curl, rot)
        L.key(h, f - 6, loc=down + Vector((0, -0.05, 0.25)), rot=rot)
        L.key(h, f, loc=down, rot=rot)
        L.key(h, f + 2, loc=down, rot=rot)
        L.key(h, f + 9, loc=down + Vector((0, -0.05, 0.3)), rot=rot)
    L.key(h, n, loc=pointing_hand_at(taps[1][1], curl, rot, lift=Vector((0.2, -0.4, 0.55))), rot=rot)
    # germs on the finger
    rnd = random.Random(8)
    for i, p in enumerate(finger_surface_points(curl, 0.03, 0, 8, 81, radius=0.1, segs=(1, 2))):
        g = L.germ(p, rnd.uniform(0.035, 0.055), seed=800 + i, parent=h)
        wobble_from(g, 0, 0.005)
    ring_m = L.emission_mat("Ripple", (0.7, 0.9, 1.0), 4.0)
    for f, p in taps:
        ring = L.torus(0.1, 0.008, p + Vector((0, 0, -0.035)), mat=ring_m, name="Ripple")
        L.key(ring, f - 1, scale=0)
        L.key(ring, f, scale=0.3)
        L.key(ring, f + 10, scale=2.5)
        L.key(ring, f + 12, scale=0)
        # germs left on the screen
        for k in range(6):
            a = rnd.uniform(0, 6.28)
            r = rnd.uniform(0.03, 0.16)
            gp = Vector((p.x + r * math.cos(a), p.y + r * math.sin(a), 0.045 + 0.03))
            g = L.germ(gp, rnd.uniform(0.035, 0.06), seed=850 + f * 10 + k, parent=root)
            L.pop_in(g, f + 1 + k, g.scale[0])
            wobble_from(g, f + 8 + k, 0.005)
    tgt = L.empty((0, 0.05, 0.1), "CamTarget")
    cam = L.camera((-0.9, -1.9, 1.5), tgt.location, lens=42, dof_dist=2.4, fstop=2.8)
    L.cam_track(cam, tgt)
    L.key(cam, 0, loc=(-1.0, -2.0, 1.6))
    L.key(cam, n - 1, loc=(-0.6, -1.7, 1.3))
    handheld(cam)


def _bump(x, z, cx, cz, sx, sz):
    return math.exp(-(((x - cx) / sx) ** 2 + ((z - cz) / sz) ** 2))


def head(skin):
    """Procedurally sculpted head: a displaced sphere. Faces -Y, top is +Z, ~2.1 units tall."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=96, ring_count=64)
    o = bpy.context.object
    o.name = "Head"
    for v in o.data.vertices:
        d = v.co.normalized()
        x, y, z = d
        sx, sy, sz = 0.74, 0.88, 1.02
        if z < 0:
            k = 1 - 0.32 * (-z) ** 1.5
            sx *= k
            sy *= 1 - 0.12 * (-z) ** 2
        p = Vector((x * sx, y * sy, z * sz))
        front = max(0.0, -y) ** 2
        side = max(0.0, abs(x)) ** 2
        X, Z = p.x, p.z
        h = 0.0
        h += 0.36 * _bump(X, Z, 0, -0.12, 0.085, 0.22) * front          # nose bridge
        h += 0.2 * _bump(X, Z, 0, -0.29, 0.11, 0.09) * front          # nose tip
        h += 0.05 * _bump(X, Z, 0.12, -0.33, 0.06, 0.05) * front
        h += 0.05 * _bump(X, Z, -0.12, -0.33, 0.06, 0.05) * front      # nostrils
        h += 0.07 * _bump(abs(X), Z, 0.28, 0.33, 0.2, 0.06) * front     # brow ridge
        h -= 0.09 * _bump(abs(X), Z, 0.28, 0.14, 0.13, 0.1) * front     # eye sockets
        h += 0.07 * _bump(abs(X), Z, 0.42, -0.12, 0.14, 0.14) * front   # cheekbones
        h += 0.05 * _bump(X, Z, 0, -0.52, 0.17, 0.05) * front           # upper lip
        h += 0.045 * _bump(X, Z, 0, -0.62, 0.15, 0.045) * front         # lower lip
        h -= 0.02 * _bump(X, Z, 0, -0.57, 0.18, 0.012) * front          # mouth line
        h += 0.08 * _bump(X, Z, 0, -0.86, 0.14, 0.1) * front            # chin
        v.co = p + d * h
    L.smooth(o, subsurf=1)
    L.assign(o, skin)
    # ears
    for sxn in (-1, 1):
        e = L.sphere(0.2, (0.7 * sxn, 0.08, 0.02), scale=(0.28, 0.6, 1.0), mat=skin, name="Ear")
        e.rotation_euler = (0.15, 0, -0.25 * sxn)
        L.torus(0.13, 0.03, (0.74 * sxn, 0.08, 0.04), rot=(0, math.pi / 2, 0), scale=(1, 0.65, 1.0), mat=skin, name="EarRim")
    return o


def ray(origin, direction):
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, nrm, idx, ob, mtx = bpy.context.scene.ray_cast(dg, Vector(origin), Vector(direction).normalized())
    return (loc, nrm, ob) if hit else (None, None, None)


@shot("s09_phone_on_face", 63)
def s09(n):
    L.reset(world_color=(0.3, 0.32, 0.38), world_strength=0.5)
    back = L.bsdf_mat("Back", (0.3, 0.42, 0.52), rough=0.9)
    L.plane((20, 20), (0, 5, 0), rot=(math.pi / 2, 0, 0), mat=back, name="Back")
    skin = L.skin_mat(tone=(0.74, 0.5, 0.38))
    hd = head(skin)
    bpy.context.view_layer.update()
    white = L.bsdf_mat("EyeWhite", (0.92, 0.9, 0.88), rough=0.05, coat=1.0)
    iris = L.bsdf_mat("Iris", (0.22, 0.12, 0.05), rough=0.1, coat=1.0)
    pupil = L.bsdf_mat("Pupil", (0.0, 0.0, 0.0), rough=0.05, coat=1.0)
    brow_m = L.bsdf_mat("Brow", (0.07, 0.045, 0.03), rough=0.8)
    for sxn in (-1, 1):
        ex, ez = 0.27 * sxn, 0.14
        hit, _, _ = ray((ex, -3, ez), (0, 1, 0))
        ey = (hit.y if hit else -0.75) + 0.07
        L.sphere(0.1, (ex, ey, ez), mat=white, name="Eye")
        L.sphere(0.05, (ex, ey - 0.088, ez), scale=(1, 0.4, 1), mat=iris, name="Iris")
        L.sphere(0.025, (ex, ey - 0.1, ez), scale=(1, 0.3, 1), mat=pupil, name="Pupil")
        lid = L.sphere(0.104, (ex, ey + 0.012, ez + 0.055), scale=(1.08, 1.0, 0.5), mat=skin, name="Lid")
        hb, _, _ = ray((ex, -3, 0.33), (0, 1, 0))
        by = (hb.y if hb else -0.8) - 0.005
        br = L.cylinder(0.022, 0.24, (ex, by, 0.33), rot=(0, math.pi / 2, -0.12 * sxn), mat=brow_m, name="Brow")
        br.scale = (1, 1.4, 1)
    hair_m = L.bsdf_mat("Hair", (0.05, 0.033, 0.022), rough=0.5, coat=0.2)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=64, ring_count=32)
    hair = bpy.context.object
    hair.name = "Hair"
    for v in hair.data.vertices:
        d = v.co.normalized()
        k = 1.06 + 0.04 * math.sin(d.x * 9) * math.cos(d.y * 7)
        if d.z < 0.25 + 0.35 * max(0, -d.y) and not (d.y > 0.2 and d.z > -0.35):
            k = 0.9  # tucked inside the head (face area)
        v.co = Vector((d.x * 0.76 * k, d.y * 0.9 * k, d.z * 1.04 * k + 0.03))
    L.smooth(hair, subsurf=1)
    L.assign(hair, hair_m)
    L.cylinder(0.4, 1.2, (0, 0.1, -1.3), mat=skin, name="Neck")
    shirt = L.bsdf_mat("Shirt", (0.85, 0.3, 0.25), rough=0.8)
    L.sphere(1.0, (0, 0.2, -2.3), scale=(1.8, 0.95, 0.9), mat=shirt, name="Shoulders")
    bpy.context.view_layer.update()
    # phone comes to the left cheek (+X)
    root, scr, sb = L.phone((0, 0, 0), rot=(0, 0, 0))
    root.scale = (0.95, 0.95, 0.95)
    screen_germs(root, 18, seed=9, size=(0.05, 0.085), n_frames=n)
    zax = Vector((-1, 0, 0))
    yax = Vector((0, 0.45, 0.89)).normalized()
    xax = yax.cross(zax)
    R = Matrix((xax, yax, zax)).transposed()
    rot = R.to_euler()
    c_yz = Vector((0, -0.3, -0.12))
    xs = []
    for u in (-0.3, 0, 0.3):
        for v in (-0.6, -0.3, 0, 0.3, 0.6):
            p = c_yz + xax * u + yax * v
            hit, _, ob = ray((3, p.y, p.z), (-1, 0, 0))
            if hit is not None and ob is not None and ob.name.startswith(("Head", "Ear")):
                xs.append(hit.x)
    cx = (max(xs) if xs else 0.75) + 0.07
    contact = Vector((cx, c_yz.y, c_yz.z))
    away = contact + Vector((1.4, -0.9, -0.3))
    L.key(root, 0, loc=away, rot=rot)
    L.key(root, 20, loc=contact + Vector((0.12, 0, 0)), rot=rot)
    L.key(root, 25, loc=contact, rot=rot)
    L.key(root, 40, loc=contact, rot=rot)
    L.key(root, 54, loc=contact + Vector((0.9, -0.5, 0.1)), rot=rot)
    L.key(root, n, loc=contact + Vector((1.2, -0.6, 0.1)), rot=rot)
    rnd = random.Random(9)
    k = 0
    for i in range(60):
        if k >= 16:
            break
        p = c_yz + xax * rnd.uniform(-0.3, 0.3) + yax * rnd.uniform(-0.55, 0.45)
        hit, nrm, ob = ray((3, p.y, p.z), (-1, 0, 0))
        if hit is None or ob is None or not ob.name.startswith("Head"):
            continue
        s = rnd.uniform(0.035, 0.055)
        g = L.germ(hit + nrm * s * 0.5, s, seed=900 + k)
        f = 26 + k
        L.pop_in(g, f, s)
        wobble_from(g, f + 8, 0.005)
        k += 1
    tgt = L.empty((0.3, -0.4, -0.05), "CamTarget")
    cam = L.camera((-0.6, -3.6, 0.3), tgt.location, lens=32, dof_dist=4.0, fstop=4)
    L.cam_track(cam, tgt)
    L.key(cam, 0, loc=(-1.3, -4.3, 0.4))
    L.key(cam, 30, loc=(0.0, -4.0, 0.25))
    L.key(cam, n - 1, loc=(2.0, -2.0, 0.05))
    L.key(tgt, 0, loc=(0.15, -0.4, 0.0))
    L.key(tgt, n - 1, loc=(cx - 0.1, -0.35, -0.12))
    handheld(cam)
    L.area_light((-2.5, -3, 2.5), (0, -0.5, 0), 600, 3, (1.0, 0.92, 0.85))
    L.area_light((3, -2.5, 1), (0, -0.5, 0), 300, 3, (0.8, 0.9, 1.0))
    L.area_light((0.5, 3, 3), (0, 0, 0.3), 700, 2.5, (0.9, 0.95, 1.0))


@shot("s10_wipe_clean", 108)
def s10(n):
    table_set()
    root, scr, sb = L.phone((0, 0, 0.04), rot=(0, 0, 0.2))
    rnd = random.Random(10)
    gs = screen_germs(root, 30, seed=10, size=(0.045, 0.09), crawl=0.05, n_frames=n)
    # microfibre cloth with a hand on top, swiping along the phone (local Y)
    cloth_m, nt, N, Ln, b = L.node_mat("Cloth")
    b.inputs["Base Color"].default_value = (0.12, 0.38, 0.85, 1)
    b.inputs["Roughness"].default_value = 0.95
    if "Sheen Weight" in b.inputs:
        b.inputs["Sheen Weight"].default_value = 1.0
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 300
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.3
    Ln.new(nz.outputs["Fac"], bump.inputs["Height"])
    Ln.new(bump.outputs["Normal"], b.inputs["Normal"])
    cl_root = L.empty((0, 0, 0), "ClothRoot")
    cl_root.parent = root
    cloth = L.plane((1.1, 0.75), (0, 0, 0.0), mat=cloth_m, name="Cloth")
    cloth.parent = cl_root
    sub = cloth.modifiers.new("Sub", "SUBSURF")
    sub.subdivision_type = "SIMPLE"
    sub.levels = sub.render_levels = 5
    tx = bpy.data.textures.new("Folds", "CLOUDS")
    tx.noise_scale = 0.25
    dsp = cloth.modifiers.new("Disp", "DISPLACE")
    dsp.texture = tx
    dsp.strength = 0.08
    sol = cloth.modifiers.new("Solid", "SOLIDIFY")
    sol.thickness = 0.02
    L.smooth(cloth)
    h = L.hand("Hand", curl=(0.15, 0.12, 0.15, 0.2), thumb=0.3, spread=0.07, scale=0.75)
    h.parent = cl_root
    h.location = (0.0, -0.75, 0.2)
    h.rotation_euler = (-0.1, 0, 0)
    z0 = 0.075
    wipe = [(14, -1.9), (24, -0.9), (34, 0.0), (44, 0.95), (52, 1.6)]
    L.key(cl_root, 0, loc=(0.9, -2.6, 0.9), rot=(0, 0, 0.1))
    for f, y in wipe:
        L.key(cl_root, f, loc=(0.02 * math.sin(f), y, z0 if abs(y) < 1.0 else z0 + 0.12), rot=(0, 0, 0.1 * math.sin(f / 4)))
    L.key(cl_root, 64, loc=(1.2, 2.8, 1.0))
    # germs vanish as cloth passes: cloth front edge at y + 0.37
    def cloth_front_frame(y):
        ys = [w[1] for w in wipe]
        fs = [w[0] for w in wipe]
        for i in range(len(ys) - 1):
            if ys[i] + 0.3 <= y <= ys[i + 1] + 0.3:
                t = (y - ys[i] - 0.3) / (ys[i + 1] - ys[i])
                return int(fs[i] + t * (fs[i + 1] - fs[i]))
        return fs[1]
    for g in gs:
        f = cloth_front_frame(g.location.y)
        L.pop_out(g, f, g.scale[0], dur=3)
    # screen brightens once clean
    es = sb.inputs["Emission Strength"]
    L.key_value(es, 60, 1.6)
    L.key_value(es, 70, 3.2)
    L.key_value(es, 85, 1.9)
    tgt = L.empty((0, 0, 0.05), "CamTarget")
    cam = L.camera((0.8, -2.2, 1.6), tgt.location, lens=40, dof_dist=root, fstop=2.8)
    L.cam_track(cam, tgt)
    L.key(cam, 0, loc=(0.9, -2.3, 1.7))
    L.key(cam, 60, loc=(0.3, -2.0, 1.55))
    L.key(cam, n - 1, loc=(-0.5, -1.5, 1.2))
    handheld(cam, 0.003)
    pts = [(rnd.uniform(-0.45, 0.45), rnd.uniform(-0.8, 0.8), rnd.uniform(0.08, 0.3)) for _ in range(14)]
    L.sparkle_burst(cam, pts, 66, size=0.07, seed=10, hold=22)
    pts2 = [(rnd.uniform(-0.45, 0.45), rnd.uniform(-0.8, 0.8), rnd.uniform(0.08, 0.3)) for _ in range(10)]
    L.sparkle_burst(cam, pts2, 88, size=0.06, seed=11, hold=12)
