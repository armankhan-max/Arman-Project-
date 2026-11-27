import glob as _g
F = "stock/fsa_c/"
FM = "stock/films/"
PL = FM + "0884_Plow_that_Broke_the_Plains_The_16_30_36_10.mp4"
ML = FM + "6108_Mail_A_Story_of_the_United_States_Postal_Service_The_01_17_13_00.mp4"
RR = FM + "6136_One_Hundred_Years_of_Railroad_Development_01_33_49_15.mp4"
WF = FM + "0234_Wheat_Farmer_The_05_58_43_00.mp4"
RRC = [0.0, 0.25, 1.0, 1.0]  # crop grandstands

def I(p, crop=None, move=None):
    d = {"img": p}
    if crop: d["crop"] = crop
    if move: d["move"] = move
    return d
def V(f, t0, t1, crop=None):
    d = {"vid": f, "t": t0, "t1": t1}
    if crop: d["crop"] = crop
    return d
def A(*pats):
    out = []
    for pat in pats:
        out += [I(p) for p in sorted(_g.glob("ai/" + pat + "_*.png")) + sorted(_g.glob("comp/" + pat + "_*.png"))]
    return out
def FS(*names):
    return [I(F + n + ".jpg") for n in names]
P = {}
def add(name, *items):
    lst = P.setdefault(name, [])
    for it in items: lst.extend(it if isinstance(it, list) else [it])

add("plains_dawn", A("plains_dawn"), FS("plains_00", "plains_01", "plains_03", "plains_06", "plains_09"), V(PL, 212, 226), V(PL, 228, 250))
add("plains", FS("plains_00", "plains_01", "plains_02", "plains_03", "plains_05", "plains_06", "plains_07", "plains_08", "plains_09", "plains_10", "plains_11", "dust_22", "dust_23", "dust_25"), V(PL, 168, 200), V(PL, 212, 250))
add("wheat", FS("wheat2_00", "wheat2_01", "wheat2_02", "wheat2_05", "wheat2_06", "wheat2_07", "wheat2_08", "wheat2_09", "wheat2_10", "wheat2_11", "combine_14", "combine_15", "combine_16", "wheat3_00", "wheat3_08", "wheat3_11"), V(WF, 244, 258), V(WF, 420, 440), V(WF, 444, 470), V(PL, 860, 900), A("wheat_green"))
add("wheat_dry", FS("plains_05", "plains_12", "dust_21", "dust_22", "dust_23", "dust_24"), V(PL, 1060, 1100), V(PL, 1364, 1378), V(PL, 1484, 1500))
add("dust_storm", FS("dust_00", "dust_01", "dust_02", "dust_03", "dust_04", "dust_05", "dust_06", "dust_07", "dust_08", "dust_09", "dust_11", "dust_13", "dust_14", "dust_15", "dust_16", "dust_17", "dust_19", "dust_20", "dust_26", "dust_27"), V(PL, 1156, 1236), A("duststorm"))
add("farmhouse", FS("farmhouse_00", "farmhouse_01", "farmwife_17", "dust_21", "dust_26"), V(PL, 1276, 1296), V(PL, 1310, 1330), A("farmhouse"))
add("farm_family", FS("farmer2_13", "farmwife_05", "farmwife_04"), V(PL, 1300, 1306))
add("farmwife", A("clara", "clara_field"), FS("farmwife_02", "farmwife_03", "farmwife_09", "farmwife_16", "farmwife_18", "farmwife_28"), V(PL, 572, 578), V(PL, 588, 594))
add("kitchen_lamp", A("kitchen_lamp"), FS("farmwife_07", "farmwife_14", "farmwife_20"), V(WF, 196, 202))
add("windmill", FS("windmill_02", "windmill_03", "windmill_04", "windmill_06", "windmill_09", "windmill_11", "windmill_12", "windmill_13", "windmill_14", "windmill_15", "windmill_22", "windmill_23", "windmill_25", "windmill_28"))
add("well_rig", A("rig", "rig2"), FS("well_23", "well_26", "well_24"))
add("drillers", A("rig", "nephew", "rig_bit"), FS("well_27", "well_25"))
add("driller_portrait", A("driller"), FS("farmer2_09", "farmer2_14", "farmer2_19", "farmer_01", "farmer_14"))
add("drillbit", A("rig_bit"))
add("splinters", A("splinters"))
add("boxcar_red", A("splinters"), FS("boxcar_05", "boxcar_06", "freight_16", "freight_18"))
add("depth_chart", A("rig", "rig2", "shaft_top"))
add("logbook", A("tripbook"), FS("letters_14", "letters_22"))
add("logbook_close", A("tripbook2"))
add("ledger", A("ledger_old"), FS("letters_12"))
add("ledger_old", A("ledger_old"))
add("ledger_hand", A("ledger_hand"))
add("old_map", A("old_map"))
add("railroad_1880s", A("locomotive1889", "crew"), FS("locomotive_09", "locomotive_10", "locomotive_11", "locomotive_18", "locomotive_19", "railroad_08"), V(RR, 362, 384, RRC), V(RR, 410, 418, RRC))
add("locomotive", A("locomotive1889", "night_train"), FS("locomotive_09", "locomotive_10", "locomotive_18", "railroad_08"), V(RR, 362, 384, RRC))
add("crew", A("crew"))
add("trestle", A("trestle"), FS("trestle_01", "trestle_02", "trestle_08", "trestle_12", "trestle_19"))
add("trestle_wreck", A("trestle_gone"))
add("flood", A("flood", "trestle_flood"), FS("flood_01", "flood_02", "flood_03", "flood_04", "flood_05", "flood_14", "flood_15", "flood_16", "flood_17", "flood_18", "flood_25"))
add("river", FS("river_01", "river_02", "river_03", "river_04", "river_05", "river_06", "river_07", "river_13", "river_26", "river_27", "river_28"))
add("storm_night", A("station_night", "night_train"))
add("telegraph", A("telegraph"), V(WF, 284, 296))
add("rpo_clerk", A("rpo_work"), FS("mailcar_00", "mailcar_01", "mailcar_02", "mailcar_03", "mailcar_04", "mailcar_05", "mailcar_07", "mailcar_13", "mailcar_14"), V(ML, 320, 338), V(ML, 404, 418))
add("rpo_interior", A("car_interior", "rpo_work"), FS("mailcar_02", "mailcar_03", "mailcar_04"))
add("clerk_portrait", A("clerk"))
add("newspaper", A("newspaper_office", "editor"), FS("newspaper_11", "newspaper_12", "newspaper_22", "newspaper_23", "newspaper_24", "newspaper_26"))
add("crowd", A("crowd_hats", "shaft_top"), FS("crowd_09", "crowd_10", "crowd_11", "crowd_12", "crowd_13", "crowd_16", "crowd_17", "crowd_25", "crowd_26"))
add("cemetery", A("funeral"), FS("church_00", "church_01", "church_02"))
add("church", A("funeral"), FS("church_00", "church_01", "church_02"))
add("postoffice", A("postoffice"), FS("postoffice_07", "postoffice_08", "postoffice_11", "postoffice_19", "postoffice_20", "postoffice_22", "postoffice_24", "postmaster_07", "postmaster_26", "postoffice_21", "postoffice_15"), V(ML, 296, 316))
add("postmaster", A("postmaster"), FS("postmaster_06", "postmaster_07", "postmaster_26"))
add("inspector", A("inspector"), FS("courthouse_00", "courthouse_08"))
add("geologist", A("geologist"))
add("gypsum_cave", A("gypsum_cave"))
add("sinkhole", A("sinkhole"))
add("smalltown", FS("mainstreet_00", "mainstreet_01", "mainstreet_02", "smalltown_00", "smalltown_05", "smalltown_07", "smalltown_09", "smalltown_19", "smalltown_20", "smalltown_24", "smalltown_25", "smalltown_27", "grainelevator_06", "grainelevator_13", "grainelevator_16", "courthouse_16"))
add("excavation", A("shaft_top", "digging"), FS("excavation_00", "excavation_01", "excavation_02", "excavation_03", "excavation_04", "excavation_05", "excavation_06", "excavation_07", "excavation_09"))
add("digging", A("digging", "steamshovel"), FS("steamshovel_01", "steamshovel_02", "steamshovel_06", "steamshovel_07", "steamshovel_11", "steamshovel_13", "steamshovel_17", "steamshovel_18", "steamshovel_19", "shovel_01", "shovel_02", "shovel_05", "wheat2_13", "wheat2_14", "wheat2_17", "wheat2_21"), V(WF, 388, 404))
add("pump", A("pump"))
add("shaft", A("shaft"))
add("mailcar_buried", A("mailcar_buried"))
add("mailcar_door", A("mailcar_door"))
add("seal", A("seal"))
add("car_interior", A("car_interior", "car_interior2"))
add("mail_sacks", A("mail_sacks"), FS("mailcar_05", "mailcar_06", "mailcar_14"), V(ML, 296, 316), V(ML, 404, 418))
add("letters_stack", A("letters_stack", "envelope"), V(ML, 340, 346))
add("letters_table", A("letters_table", "letters_stack"))
add("envelope_old", A("envelope"))
add("letter_reading", A("clara_letter", "ada"), FS("letters_09", "letters_11", "letters_17", "letters_23", "letters_29"))
add("tripbook", A("tripbook"))
add("tripbook_close", A("tripbook2", "tripbook"))
add("lantern", A("car_interior2"))
add("locomotive_buried", A("locomotive_buried"))
add("oldwoman", A("rose", "ada"), FS("postmaster_06", "farmwife_03"))
add("oldman", A("otto"), FS("postmaster_03", "postmaster_04", "postmaster_11", "postmaster_05"))
add("farmer", A("otto"), FS("farmer2_00", "farmer2_08", "farmer2_15", "farmer2_18", "farmer2_20", "farmer_00", "farmer_07", "farmer_11", "wheat2_03"), V(PL, 440, 462), V(WF, 276, 282))
add("children", FS("children_00", "children_02", "children_10", "children_23"), V(PL, 1300, 1306))
add("seeds", A("seeds"), V(WF, 260, 274))
add("sprouts", A("sprouts"))
add("black", [{"color": 0.0}])
P["mailcar_buried"] = A("thumb", "thumb2", "mailcar_buried")
P["locomotive_buried"] = A("thumb2", "shaft")
P["excavation"] = P["excavation"] + A("thumb")
