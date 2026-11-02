"""Edit decision list: narration paragraph -> shots, graphics, on-screen text, shakes and sound cues.

Cut points are anchored to words in the narration (timeline.json), so every cut, text pop and hit
lands on the word it belongs to.

shot kinds
  pl(plate, move, grade, ...)   a rendered B-roll plate with Ken Burns move + grade
  gx(name, **params)            an animated 2D graphic (map, seismograph, diagram, counter ...)
text kinds
  lower(title, sub)   location lower-third (serif, line wipe)       date(text)  red typewriter stamp
  pop(text)           big keyword slam                              chapter(n, title)
  title(text, sub)    main title card                                callout(text, x, y)  label + leader line
quake(word, dur, amp)  camera shake event (applied to whatever is on screen)
"""

E = {}


def pl(name, move="in", grade="day", at=None, **kw):
    return dict(kind="plate", name=name, move=move, grade=grade, at=at, **kw)


def gx(name, at=None, **kw):
    return dict(kind="gfx", name=name, at=at, **kw)


def lower(title, sub="", at=None, dur=4.5):
    return dict(kind="lower", text=title, sub=sub, at=at, dur=dur)


def date(text, at=None, dur=3.5, sub=""):
    return dict(kind="date", text=text, sub=sub, at=at, dur=dur)


def pop(text, at=None, dur=2.2, color="red", size=150):
    return dict(kind="pop", text=text, at=at, dur=dur, color=color, size=size)


def chapter(n, text, at=None, dur=4.0):
    return dict(kind="chapter", text=text, n=n, at=at, dur=dur)


def title(text, sub, at=None, dur=6.0):
    return dict(kind="title", text=text, sub=sub, at=at, dur=dur)


def callout(text, x, y, at=None, dur=3.5, tx=None, ty=None):
    return dict(kind="callout", text=text, x=x, y=y, tx=tx, ty=ty, at=at, dur=dur)


def quake(at, dur=3.0, amp=1.0, decay=1.5, p=None):
    return dict(kind="quake", at=at, dur=dur, amp=amp, decay=decay, p=p)


def sfx(name, at=None, gain=1.0, off=0.0):
    return dict(kind="sfx", name=name, at=at, gain=gain, off=off)


def P(i, shots, extra=()):
    E[i] = dict(shots=shots, extra=list(extra))


# ------------------------------------------------------------------ HOOK
P(0, [pl("colombo_day_street", "in", "day"), pl("office_interior_desk", "left", "day", at="ordinary"),
      pl("city_aerial_cathedral", "in", "day", at="ground"), pl("colombo_collapse_wide", "out", "disaster", at="moved", flash=True)],
  [date("12:51 PM", at="At", sub="TUESDAY"), pop("UPWARD", at="upward"), quake("moved", 4.5, 1.2, 0.8),
   sfx("riser", at="ground", gain=0.6), sfx("boom", at="moved")])
P(1, [pl("dust_street_silhouettes", "in", "disaster"), pl("colombo_collapse_bus", "right", "disaster", at="Cars"),
      gx("gforce", at="In")],
  [quake("People", 3.0, 0.8, 1.0), quake("Cars", 2.5, 0.9, 1.0), sfx("debris", at="People"), sfx("glass", at="Cars")])
P(2, [pl("cathedral_collapsed_front", "in", "disaster"), pl("colombo_collapse_high", "out", "disaster", at="But")],
  [sfx("sub", at="never")])
P(3, [gx("map", at=None, seq="nz_to_chch"), pl("city_aerial_oblique", "in", "dark", at="The", dim=0.55),
      gx("compare", at="strangest", mode="tease")],
  [title("THE DAY THE GROUND\nCAME BACK", "CHRISTCHURCH, NEW ZEALAND", at="The", dur=6.5), pop("IT WASN'T EVEN CLOSE", at="It", size=96)])
# ------------------------------------------------------------------ SEPTEMBER 2010
P(4, [gx("timeline", mode="rewind"), pl("city_night_aerial_sleep", "in", "night", at="night")],
  [sfx("rewind", at="back"), chapter(1, "THE MIRACLE", at="night")])
P(5, [pl("night_street_empty", "in", "night")], [date("4 SEPTEMBER 2010", at="It's", dur=4.4, sub="04:35 AM")])
P(6, [pl("city_night_aerial_sleep", "out", "night"), pl("night_street_corner", "left", "night", at="streets"),
      pl("night_street_empty", "out", "night", at="buses")], [sfx("crickets", at="Most")])
P(7, [gx("map", seq="darfield"), pl("farmland_night_plains", "in", "night", at="tears", flash=True)],
  [lower("DARFIELD", "40 km west of Christchurch", at="Darfield", dur=3.0), quake("tears", 4.5, 1.1, 0.7), sfx("boom", at="tears")])
P(8, [pl("fault_rupture_aerial", "in", "memory"), pl("fault_rupture_fence", "right", "memory", at="Fences"),
      pl("road_crack_road", "in", "memory", at="Roads"), pl("rail_buckled_rail", "in", "memory", at="Railway")],
  [quake("A", 2.0, 0.5, 1.0), lower("GREENDALE FAULT", "Unknown before 4 September 2010", at="fault", dur=3.5),
   callout("OFFSET: UP TO 5 M", 0.52, 0.55, at="shifted", tx=0.62, ty=0.3), sfx("crack", at="Roads"), sfx("metal", at="Railway")])
P(9, [gx("seismo", mag="7.1", label="4 SEPT 2010 · 04:35"), pl("city_night_aerial_sleep", "in", "night", at="That's")],
  [sfx("boom", at="measures", gain=0.7)])
P(10, [pl("shopfront_dawn_dawn", "in", "memory"), pl("shopfront_dawn_bricks", "right", "memory", at="Old"),
       pl("liquefaction_2010_street", "in", "memory", at="Water")],
   [sfx("debris", at="chimneys"), sfx("bricks", at="crumble"), sfx("water", at="Water")])
P(11, [pl("city_aerial_oblique", "in", "dawn")], [sfx("birds", at="sun")])
P(12, [pl("liquefaction_2010_street", "in", "dark", dim=0.4)], [pop("NO ONE KILLED DIRECTLY\nBY THE SHAKING", at="No", dur=2.9, color="white", size=84)])
P(13, [pl("cathedral_day_square", "in", "dawn"), gx("clock", at="timing", time="4:35", sub="AM"),
       pl("shopfront_dawn_bricks", "left", "memory", at="nobody"), pl("night_street_corner", "in", "night", at="Nobody")],
   [pop("A MIRACLE", at="miracle", color="white", size=130)])
P(14, [pl("port_hills_ridge", "in", "dark")], [sfx("sub", at="hidden")])
P(15, [pl("colombo_day_street", "in", "day")])
P(16, [gx("map", seq="aftershocks"), pl("suburb_day_street", "right", "day", at="Others")],
   [quake("trembling", 1.2, 0.35, 1.5), quake("Others", 1.5, 0.5, 1.5), sfx("rumble_s", at="trembling"), sfx("rumble_s", at="Others")])
P(17, [pl("shopfront_dawn_dawn", "in", "day"), pl("colombo_day_foot", "left", "day", at="Cracks"),
       pl("colombo_day_high", "out", "day", at="Life")], [pop("ALL-CLEAR", at="all-clear", color="green", size=120)])
P(18, [pl("city_aerial_oblique", "in", "day")], [sfx("drone_swell", at="worst")])
P(19, [gx("black")], [pop("IT WASN'T.", at="It", color="red", size=170, dur=1.6), sfx("boom", at="It")])
# ------------------------------------------------------------------ THE GROUND
P(20, [gx("soil", stage=0)], [chapter(2, "THE GROUND", at="To")])
P(21, [pl("canterbury_plains_alps", "in", "day"), pl("canterbury_plains_river", "right", "day", at="Long")],
   [lower("CANTERBURY PLAINS", "Between the Southern Alps and the Pacific", at="The", dur=4.0)])
P(22, [gx("soil", stage=1)])
P(23, [gx("soil", stage=2)], [sfx("rumble_s", at="shaken")])
P(24, [pl("sand_boils_boils", "in", "day")], [pop("LIQUEFACTION", at="liquefaction", color="white", size=140)])
P(25, [pl("tilted_house_house", "in", "day"), pl("liquefaction_2011_car", "left", "day", at="Cars"),
       pl("sand_boils_boils", "out", "day", at="Roads")], [sfx("creak", at="Houses"), sfx("water", at="slurry")])
P(26, [pl("liquefaction_2010_street", "in", "memory"), pl("liquefaction_2011_high", "out", "day", at="But")])
P(27, [gx("map", seq="porthills")])
P(28, [pl("port_hills_wide", "in", "day"), pl("port_hills_ridge", "right", "day", at="remains"),
       pl("lyttelton_harbour", "in", "day", at="On")],
   [lower("PORT HILLS", "Remains of an extinct volcano", at="Port", dur=4.0), lower("LYTTELTON", "Harbour town", at="Lyttelton", dur=3.0)])
P(29, [pl("lyttelton_harbour", "out", "day"), pl("port_hills_ridge", "in", "day", at="Peaceful."),
       pl("timeball_station", "in", "day", at="Solid.")], [sfx("hit_soft", at="Peaceful."), sfx("hit_soft", at="Solid.")])
P(30, [pl("port_hills_wide", "in", "dark", dim=0.7)], [sfx("drone_swell", at="Or")])
P(31, [gx("map", seq="hidden_fault")], [sfx("sub", at="another")])
P(32, [gx("clock", time="12:50", sub="PM", tick=True)])
# ------------------------------------------------------------------ 22 FEBRUARY 2011
P(33, [pl("city_aerial_cathedral", "in", "day")], [date("22 FEBRUARY 2011", at="Tuesday,", dur=3.4, sub="TUESDAY"),
                                                   chapter(3, "12:51", at="2011.", dur=3.0)])
P(34, [pl("colombo_day_high", "in", "day"), pl("cathedral_day_square", "right", "day", at="The")], [sfx("city", at="It's")])
P(35, [pl("colombo_day_foot", "in", "day"), pl("colombo_day_street", "in", "day", at="Shoppers"),
       pl("colombo_day_high", "left", "day", at="Buses"), pl("cathedral_day_spire", "up", "day", at="Tourists")],
   [lower("COLOMBO STREET", "Central Christchurch", at="Shoppers", dur=3.5),
    lower("CHRISTCHURCH CATHEDRAL", "The heart of the city", at="Tourists", dur=4.5)])
P(36, [pl("ctv_day_corner", "in", "day"), pl("ctv_day_up", "up", "day", at="It's")],
   [lower("CTV BUILDING", "Madras Street", at="CTV", dur=4.0), callout("6 FLOORS", 0.5, 0.42, at="six-story", tx=0.72, ty=0.25)])
P(37, [pl("classroom_room", "in", "day"), pl("city_aerial_cathedral", "out", "day", at="Many")],
   [pop("JAPAN · CHINA · PHILIPPINES", at="Japan,", color="white", size=70, dur=3.0)])
P(38, [pl("classroom_room", "left", "day"), pl("colombo_day_foot", "right", "day", at="on")])
P(39, [pl("pgc_day_front", "in", "day"), pl("office_interior_desk", "in", "day", at="Five")],
   [lower("PGC BUILDING", "Pyne Gould Corporation · Cambridge Terrace", at="Pyne", dur=4.0)])
P(40, [gx("clock", time="12:50", sub="PM", tick=True, fast=True)])
P(41, [gx("black")], [date("12:51 PM", at="12:51", dur=1.8, sub="22 FEBRUARY 2011"), sfx("heartbeat", at="12:51")])
P(42, [gx("map", seq="feb_epicentre"), pl("port_hills_ridge", "in", "disaster", at="gives", flash=True)],
   [quake("gives", 5.0, 1.4, 0.6), sfx("boom", at="gives"), sfx("rumble_l", at="gives")])
P(43, [gx("compare", mode="mag")])
P(44, [gx("compare", mode="mag", hold=True)])
P(45, [pl("colombo_day_street", "in", "dark", dim=0.8)], [sfx("drone_swell", at="But")])
P(46, [gx("depth"), gx("map", seq="feb_distance", at="It's"), pl("colombo_day_high", "in", "day", at="strikes")],
   [pop("SHALLOW", at="shallow,", size=120), pop("CLOSE", at="close,", size=120), pop("12:51 PM", at="middle", size=120)])
P(47, [gx("sway", stage=0)])
P(48, [gx("sway", stage=1)])
P(49, [gx("sway", stage=2)], [sfx("boom", at="upward."), pop("UPWARD", at="upward.", size=150)])
P(50, [gx("seismo", mag="2.2 g", label="VERTICAL ACCELERATION · 22 FEB 2011", vertical=True),
       gx("gforce", at="moment", big=True)], [sfx("boom", at="stronger", gain=0.6)])
P(51, [pl("office_interior_desk", "in", "day")],
   [quake("slam", 2.0, 1.2, 1.0), quake("hammer", 2.5, 1.5, 0.8), pop("A HAMMER BLOW\nFROM BELOW", at="hammer", size=100),
    sfx("boom", at="slam"), sfx("boom", at="hammer"), sfx("glass", at="hammer")])
P(52, [pl("city_aerial_cathedral", "in", "disaster")], [quake("That", 1.6, 1.3, 0.8), sfx("rumble_l", at="That")])
P(53, [pl("dust_street_sunbeams", "in", "disaster"), pl("colombo_collapse_high", "right", "disaster", at="then")],
   [quake("deep", 4.0, 0.9, 0.6), sfx("rumble_l", at="deep"), sfx("crack", at="crack"), sfx("glass", at="shattering"),
    sfx("debris", at="thunder")])
P(54, [pl("shopfront_dawn_bricks", "in", "disaster")], [quake("old", 3.0, 0.8, 0.8), sfx("bricks", at="apart.")])
P(55, [pl("colombo_collapse_wide", "in", "disaster"), pl("colombo_collapse_bus", "left", "disaster", at="Two"),
       pl("dust_street_silhouettes", "in", "disaster", at="People")],
   [lower("COLOMBO STREET", "22 February 2011", at="Colombo", dur=3.5), sfx("debris", at="crash"), sfx("bricks", at="masonry.")])
P(56, [pl("cathedral_day_spire", "up", "disaster"), pl("cathedral_collapsed_front", "in", "disaster", at="collapses", flash=True),
       pl("cathedral_collapsed_rubble", "right", "disaster", at="The")],
   [quake("breaks", 2.0, 1.0, 1.0), sfx("stone", at="breaks"), sfx("boom", at="collapses")])
P(57, [pl("dust_street_sunbeams", "in", "disaster"), pl("colombo_collapse_wide", "out", "disaster", at="Car"),
       pl("dust_street_silhouettes", "left", "disaster", at="People")], [sfx("alarms", at="Car")])
P(58, [gx("map", seq="two_buildings")])
P(59, [pl("pgc_day_front", "in", "disaster"), pl("pgc_collapsed_front", "in", "disaster", at="Its", flash=True),
       pl("pgc_collapsed_slabs", "right", "dark", at="People")], [quake("collapses.", 2.0, 1.0, 1.0), sfx("collapse", at="collapses.")])
P(60, [pl("ctv_day_up", "up", "disaster")], [quake("crack.", 1.5, 0.6, 1.2), sfx("crack", at="crack.")])
P(61, [pl("ctv_collapsed_wide", "in", "disaster", flash=True)], [quake("falls.", 3.5, 1.5, 0.8), sfx("collapse", at="falls."),
                                                                  pop("IT FALLS.", at="falls.", size=160, dur=1.8)])
P(62, [pl("ctv_collapsed_wide", "out", "disaster"), pl("ctv_collapsed_pile", "in", "disaster", at="Almost"),
       pl("ctv_collapsed_tower", "up", "disaster", at="Only")], [callout("STAIRWELL TOWER", 0.55, 0.38, at="stairwell", tx=0.75, ty=0.2)])
P(63, [pl("ctv_collapsed_pile", "in", "dark", dim=0.75)])
P(64, [pl("ctv_collapsed_tower", "in", "dark", dim=0.75)], [sfx("heartbeat", at="voices")])
P(65, [pl("search_rescue_team", "in", "disaster"), pl("ctv_collapsed_wide", "right", "disaster", at="Off-duty")],
   [sfx("sirens", at="Off-duty")])
P(66, [pl("ctv_collapsed_pile", "in", "dark", dim=0.8)], [sfx("drone_swell", at="notice")])
P(67, [pl("ctv_smoke_smoke", "in", "disaster")], [pop("SMOKE.", at="Smoke.", size=170, dur=1.6), sfx("boom", at="Smoke.", gain=0.7)])
# ------------------------------------------------------------------ THE RESCUE
P(68, [pl("ctv_smoke_fire", "in", "disaster")], [chapter(4, "THE RESCUE", at="The"), sfx("fire", at="fire")])
P(69, [pl("ctv_smoke_smoke", "up", "disaster")])
P(70, [pl("search_rescue_team", "in", "disaster"), pl("ctv_collapsed_pile", "left", "disaster", at="A"),
       pl("pgc_collapsed_slabs", "in", "dark", at="Some")], [sfx("sirens", at="Rescuers")])
P(71, [pl("ctv_smoke_fire", "in", "disaster"), pl("ctv_fire_night_night", "in", "night", at="Teams"),
       pl("ctv_fire_night_rescuers", "left", "night", at="Heat")], [sfx("fire", at="fire")])
P(72, [pl("ctv_smoke_smoke", "out", "dark", dim=0.7)])
P(73, [gx("counter", value=115, label="LIVES LOST AT THE CTV BUILDING"), pl("classroom_room", "in", "mourn", at="Many")])
P(74, [gx("world", seq="families")])
P(75, [pl("city_aerial_hills", "in", "disaster")])
P(76, [pl("pgc_rescue_night_night", "in", "night")], [lower("PGC BUILDING", "Night of 22 February 2011", at="PGC", dur=3.5)])
P(77, [pl("pgc_collapsed_slabs", "in", "dark", dim=0.8), pl("pgc_rescue_night_close", "in", "night", at="Trapped")],
   [sfx("tap", at="tap")])
P(78, [pl("pgc_rescue_night_close", "right", "night"), pl("pgc_rescue_night_night", "out", "night", at="Over")],
   [sfx("saw", at="cut")])
P(79, [gx("counter", value=18, label="LIVES LOST AT THE PGC BUILDING"), pl("pgc_rescue_night_night", "in", "night", at="But")])
P(80, [pl("city_aerial_oblique", "in", "disaster")])
P(81, [gx("map", seq="east")], [lower("AVON RIVER", "Eastern suburbs", at="Avon", dur=3.0)])
P(82, [pl("liquefaction_2011_flood", "in", "day"), pl("liquefaction_2011_high", "out", "day", at="It"),
       pl("liquefaction_2011_car", "in", "day", at="Cars"), pl("tilted_house_house", "left", "day", at="Footpaths")],
   [sfx("water", at="burst"), sfx("creak", at="Houses")])
P(83, [pl("liquefaction_2011_flood", "in", "dark", dim=0.9)])
P(84, [pl("liquefaction_2011_high", "in", "dark"), pl("city_night_aerial_sleep", "in", "night", at="Power", blackout=True)],
   [sfx("power_down", at="Power")])
P(85, [pl("tilted_house_house", "in", "day"), pl("sand_boils_boils", "in", "dark", at="In")])
P(86, [pl("port_hills_ridge", "in", "disaster")], [quake("shed", 2.0, 0.8, 1.0), sfx("rockfall", at="shed")])
P(87, [pl("sumner_cliffs_cliff", "in", "disaster"), pl("boulder_house_track", "in", "day", at="Huge"),
       pl("boulder_house_boulder", "in", "day", at="A")],
   [lower("SUMNER", "Seaside suburb below the Port Hills", at="Sumner", dur=3.5), sfx("rockfall", at="cliffs"), sfx("boom", at="smashed", gain=0.6)])
P(88, [pl("lyttelton_harbour", "in", "disaster"), pl("timeball_station", "in", "day", at="The")],
   [lower("LYTTELTON", "Closest town to the epicentre", at="Lyttelton,", dur=3.5),
    lower("TIMEBALL STATION", "Watching over the harbour since 1876", at="Timeball", dur=4.5)])
P(89, [pl("grand_chancellor_lean", "in", "dark", dim=0.8)])
P(90, [pl("grand_chancellor_lean", "up", "disaster")],
   [lower("HOTEL GRAND CHANCELLOR", "One of the tallest buildings in the city", at="Hotel", dur=4.5),
    callout("LEANING", 0.5, 0.3, at="leaning.", tx=0.7, ty=0.18), sfx("creak", at="leaning.")])
P(91, [pl("grand_chancellor_lean", "left", "dark"), pl("search_rescue_team", "in", "disaster", at="Rescuers")])
P(92, [gx("map", seq="aftershocks2")], [quake("aftershocks", 1.5, 0.6, 1.2), sfx("rumble_s", at="aftershocks")])
P(93, [pl("city_aerial_hills", "in", "disaster")])
P(94, [pl("city_aerial_cathedral", "in", "dark", dim=0.45)],
   [date("23 FEBRUARY 2011", at="On", dur=3.0), pop("STATE OF\nNATIONAL EMERGENCY", at="declared", color="white", size=110, dur=4.0),
    pop("A FIRST IN NEW ZEALAND'S HISTORY", at="It", color="red", size=64, dur=3.5)])
P(95, [gx("quote", text="“This may be New Zealand's\ndarkest day.”", who="PRIME MINISTER JOHN KEY · 22 FEBRUARY 2011")])
P(96, [gx("world", seq="help"), pl("search_rescue_team", "in", "disaster", at="Specialists")])
P(97, [pl("cathedral_collapsed_high", "in", "disaster"), pl("cathedral_collapsed_rubble", "left", "disaster", at="For"),
       pl("cathedral_collapsed_front", "in", "dawn", at="When")])
P(98, [pl("liquefaction_2011_high", "in", "hope")])
P(99, [pl("student_army_street", "in", "hope")])
P(100, [pl("student_army_high", "in", "hope"), pl("student_army_street", "right", "hope", at="They")],
    [lower("STUDENT VOLUNTEER ARMY", "Thousands of volunteers", at="Student", dur=4.5), sfx("shovels", at="digging")])
P(101, [pl("demolition_lot", "in", "hope"), pl("student_army_high", "out", "hope", at="Neighbors")])
P(102, [pl("cathedral_collapsed_front", "in", "dawn")], [pop("BUT ITS PEOPLE\nWERE NOT.", at="But", color="white", size=100, dur=2.4)])
P(103, [gx("counter", value=185, label="LIVES LOST · 22 FEBRUARY 2011")])
# ------------------------------------------------------------------ WHY
P(104, [gx("compare", mode="question")])
P(105, [gx("compare", mode="mag")])
P(106, [gx("reasons", stage=0)])
P(107, [gx("reasons", stage=1)])
P(108, [gx("reasons", stage=2)])
P(109, [gx("reasons", stage=3)])
P(110, [gx("reasons", stage=4), pl("shopfront_dawn_bricks", "in", "memory", at="Some")])
P(111, [pl("cathedral_collapsed_front", "out", "disaster")], [pop("WRONG PLACE.\nWRONG TIME.", at="In", size=110, dur=3.2)])
P(112, [pl("ctv_collapsed_wide", "in", "dark", dim=0.7)])
# ------------------------------------------------------------------ AFTERMATH
P(113, [pl("city_aerial_hills", "in", "dark", dim=0.8)], [chapter(5, "THE CITY THAT CAME BACK", at="And", dur=4.5)])
P(114, [pl("red_zone_cordon_cordon", "in", "disaster"), gx("map", seq="redzone_cbd", at="The")],
    [pop("RED ZONE", at="red", size=150, dur=2.0)])
P(115, [pl("demolition_lot", "in", "disaster"), pl("colombo_collapse_high", "out", "dark", at="Most"),
        pl("red_zone_cordon_cordon", "left", "dark", at="Whole")], [sfx("demolish", at="taken")])
P(116, [pl("grand_chancellor_lean", "out", "dark"), pl("demolition_lot", "in", "disaster", at="brought")])
P(117, [pl("residential_red_zone_empty", "in", "day"), gx("map", seq="redzone_east", at="Around"),
        pl("tilted_house_house", "in", "day", at="Families"), pl("residential_red_zone_high", "in", "day", at="Entire")],
    [pop("≈ 8,000 HOMES", at="eight", size=120, dur=2.6)])
P(118, [gx("counter", value=40, label="ESTIMATED COST OF REBUILDING", prefix="NZ$", suffix=" BILLION")])
P(119, [gx("doc", stage=0)])
P(120, [gx("doc", stage=1), pl("ctv_collapsed_tower", "in", "dark", at="It"), gx("doc", stage=2, at="Those")])
P(121, [pl("avon_park_river", "in", "hope")])
P(122, [pl("container_mall_mall", "in", "hope")], [lower("RE:START CONTAINER MALL", "Opened October 2011", at="temporary", dur=4.5)])
P(123, [pl("cardboard_cathedral_front", "in", "hope")], [lower("THE CARDBOARD CATHEDRAL", "Designed by Shigeru Ban · 2013", at="cardboard", dur=5.0)])
P(124, [pl("residential_red_zone_high", "in", "hope"), pl("avon_park_river", "right", "hope", at="The")])
P(125, [pl("memorial_wall_wall", "in", "hope"), pl("memorial_wall_names", "left", "mourn", at="It")],
    [lower("CANTERBURY EARTHQUAKE NATIONAL MEMORIAL", "Unveiled 22 February 2017", at="memorial", dur=5.0)])
P(126, [pl("modern_city_sunset", "in", "hope")])
P(127, [pl("sand_boils_boils", "in", "dark", dim=0.8)])
P(128, [pl("sand_boils_boils", "out", "dusk"), pl("port_hills_ridge", "in", "dusk", at="The"), gx("map", seq="hidden_fault", at="And")])
P(129, [pl("city_sunset_aerial_dusk", "in", "dusk")])
P(130, [gx("timeline", mode="twice")], [sfx("boom", at="twice.", gain=0.7)])
P(131, [pl("city_sunset_aerial_dusk", "out", "dusk", fade_out=True)], [sfx("final", at="remind")])
