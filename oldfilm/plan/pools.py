"""Pool -> candidate visual sources. Every entry was picked by eye from contact sheets.
I(path, crop, move)  still image (crop = fractions x0,y0,x1,y1)
V(film, t0, t1, crop) archive film clip (public domain)
A(glob)              AI-generated (local SDXL-Turbo) / composites
"""
import glob as _g
F = "stock/fsa_c/"
ZZ = "stock/films/201297_Beside_The_Zuider_Zee.mp4"
OS = "stock/films/200325_The_Open_Sea.mp4"
VS = "stock/films/0600_Vista_Stock_Shots_Ocean-Oriented_Footage.mp4"
SS = "stock/films/0993_Safety_at_Sea_01_28_18_08.mp4"
NE = "stock/films/0315_New_England_Yesterday_and_Today_16_00_54_25.mp4"
SAL = "stock/films/fc-fc-490.mp4"
GL = "stock/films/098725.mp4"
FV = "stock/films/0351_Fishing_Vagabonds_05_17_31_00.mp4"
SALC = [0.0, 0.05, 1.0, 0.80]  # keep burned-in timecode out of frame

def I(p, crop=None, move=None, **kw):
    d = {"img": p}
    if crop: d["crop"] = crop
    if move: d["move"] = move
    d.update(kw); return d
def V(f, t0, t1, crop=None):
    d = {"vid": f, "t": t0, "t1": t1}
    if crop: d["crop"] = crop
    return d
def A(pat, **kw):
    return [dict(img=p, **kw) for p in sorted(_g.glob(pat))]
def FS(*names, crop=None, **kw):
    return [I(F + n + ".jpg", crop, **kw) for n in names]
PORT = [0.0, 0.0, 1.0, 0.62]   # top part of a vertical portrait
PORT2 = [0.0, 0.08, 1.0, 0.70]

P = {}
def add(name, *items):
    lst = P.setdefault(name, [])
    for it in items:
        lst.extend(it if isinstance(it, list) else [it])

# ---------------- sea / weather
add("sea_dawn", A("ai/g12_*.png"), FS("gloucester_boats_25", "nets_13", "gloucester_boats_26"), V(VS, 1160, 1170))
add("sea_flat", FS("gloucester_boats_26", "gloucester_boats_27", "nets_04"), A("ai/g12_2.png"), V(VS, 1795, 1812), V(FV, 408, 414))
add("sea_calm", P["sea_flat"])
add("sea_empty", FS("gloucester_boats_27", "nets_13"), V(VS, 1795, 1812))
add("sea_swell", V(VS, 315, 324), V(VS, 1675, 1688), V(FV, 252, 262), A("ai/g12_1.png"))
add("sea_deep", V(FV, 456, 462), V(VS, 1675, 1688), FS("gloucester_boats_26"))
add("sea_close", V(FV, 276, 282), V(FV, 456, 462), A("ai/g11_*.png"))
add("sea_dark", V(FV, 456, 462), V(FV, 408, 414), V(SS, 1022, 1038), A("ai/g17_0.png"), V(VS, 1798, 1812))
add("sea_bright", FS("fishermen_04", "nets_13"), V(VS, 1160, 1170))
add("dawn", A("ai/g12_*.png"), FS("gloucester_boats_25", "nets_13"), V(VS, 1160, 1170))
add("dawn_pink", P["dawn"])
add("tide", A("ai/g45_*.png"), V(VS, 1795, 1812))
add("storm", V(SS, 552, 560), V(SS, 602, 612), V(SS, 1022, 1040), V(OS, 24, 36), V(OS, 338, 348), V(VS, 326, 340))
add("storm_coming", V(SS, 552, 560), V(VS, 1125, 1140))
add("storm_night", V(SS, 1022, 1040), A("ai/stormnight_*.png"))
add("trawler_storm", V(SS, 620, 632), V(SS, 1010, 1020))
add("small_boat_storm", V(SS, 620, 632), FS("fishermen_boat_14", "gloucester_27", "fishermen_boat_13"))
add("waves_rocks", V(OS, 24, 36), V(OS, 338, 348), V(VS, 596, 618), V(VS, 1176, 1190))
add("reef", A("ai/g45_*.png"), V(OS, 338, 348), V(VS, 596, 618), V(VS, 736, 750), V(VS, 1126, 1140), V(VS, 1176, 1190))
add("reef_empty", A("ai/g45_*.png"), V(VS, 736, 750))
add("rocks_point", V(VS, 270, 290), V(VS, 1176, 1190), V(OS, 24, 36))
add("cliff_night", V(SS, 1040, 1047), A("ai/bg_cliff_night_*.png"), A("ai/g17_2.png"))
add("capecoast", FS("village_03", "village_09"), V(VS, 270, 290), V(VS, 1795, 1812))
add("clear_water", A("ai/clearwater_*.png"))
add("whale", A("ai/whale_*.png"))

# ---------------- boats
add("boats_sea", A("ai/g12_*.png"), FS("nets_08", "nets_14", "fishermen_boat_16", "fishermen_boat_25", "gloucester_boats_23", "seine_11"))
add("boats_dawn", A("ai/g12_*.png"), A("ai/g01_*.png"), FS("nets_13", "fishermen_04"))
add("boats_still", A("ai/g12_*.png"), FS("fishermen_boat_18", "nets_09"))
add("boats_swell", A("ai/g12_*.png"), V(SAL, 96, 104, SALC), FS("fishermen_boat_18"))
add("boats_home", FS("nets_09", "seine_08", "gloucester_13", "fishermen_boat_16"), V(ZZ, 366, 380))
add("boats_return", V(ZZ, 366, 380), FS("harbor_00", "wharf_06"))
add("boats_night", FS("gloucester_boats_24", "nets_20", "nets_11", "nets_12"))
add("boats_dark", FS("nets_11", "nets_12", "gloucester_boats_24"))
add("boats_moored", FS("harbor_00", "harbor_01", "harbor_17", "harbor_18", "wharf_06", "wharf_07", "wharf_09", "wharf_23", "wharf_24", "gloucester_boats_00", "gloucester_boats_01"), V(NE, 225, 246))
add("boat_out", FS("fishermen_04", "nets_14", "fishermen_boat_25"), V(SAL, 96, 104, SALC))
add("boat_lead", FS("gloucester_boats_22", "fishermen_boat_19"), A("ai/bg_fromboat_*.png"))
add("boat_bow", FS("gloucester_boats_22", "gloucester_boats_25"), A("ai/bg_fromboat_*.png"))
add("boat_engine", FS("fishermen_boat_19", "fishermen_boat_20", "gloucester_boats_22"))
add("empty_boat", FS("fishermen_boat_18", "fishermen_boat_03", "wharf_08"))
add("trawler", FS("gloucester_boats_21", "nets_23", "seine_10", "seine_13", "gloucester_boats_23"), A("ai/trawler_*.png"))
add("trawler_dawn", A("ai/trawler_*.png"), FS("gloucester_boats_23"))
add("trawler_still", A("ai/g30_*.png"), A("ai/trawler_*.png"))
add("trawler_men", A("ai/trawlermen_*.png"), A("ai/g30_*.png"), FS("gloucester_boats_06"))
add("trawler_home", FS("gloucester_boats_23", "gloucester_boats_21"), V(ZZ, 366, 380))
add("coaster", FS("harbor_17", "wharf_18"), V(NE, 225, 246))
add("rowing", A("ai/rowing2_*.png"), A("ai/g36_*.png"), V(NE, 1037, 1043), FS("fishermen_04"))
add("skiff_dusk", A("ai/g25_*.png"), FS("fishermen_04"))
add("upturned", A("ai/g26_*.png"))
add("dusk_sea", V(VS, 1798, 1812), FS("nets_13"), A("ai/g25_*.png"))

# ---------------- fishermen
add("fishermen_work", FS("fishermen_boat_10", "fishermen_boat_11", "fishermen_boat_12", "fishermen_boat_13", "fishermen_boat_15", "fishermen_boat_17", "fishermen_16", "nets_17", "nets_18", "seine_01", "seine_03", "seine_05", "seine_06", "gloucester_02", "gloucester_24"), V(SAL, 104, 128, SALC), V(ZZ, 349, 360))
add("fishermen_faces", FS("fishermen_01", "fishermen_05", "fishermen_boat_22", "gloucester_boats_19", "gloucester_boats_16", "gloucester_boats_18"), A("ai/g09_*.png"))
add("fishermen_old", FS("fisherman_portrait_05", "fisherman_portrait_01", "fishermen_19", "dory_14", "fisherman_portrait_04"), V(NE, 323, 336), V(ZZ, 475, 480))
add("fishermen_still", FS("gloucester_boats_06", "gloucester_boats_14", "gloucester_boats_15", "fishermen_boat_01", "fishermen_boat_23"), A("ai/g03_*.png"))
add("fisherman_young", FS("fisherman_portrait_06", "fisherman_portrait_09", "fishermen_18"), A("ai/boy17_*.png"))
add("boy_pointing", A("ai/g04_0.png"), A("ai/g04_1.png"))
add("young_fisherman", FS("fisherman_portrait_09", "gloucester_boats_13", "fisherman_portrait_06"))
add("young_man", A("ai/willem_*.png"), FS("fisherman_portrait_09", "gloucester_boats_13"))
add("first_mate", FS("gloucester_boats_07", "fisherman_portrait_15"))
add("skipper_portrait", FS("fisherman_portrait_12", "fisherman_portrait_13", "fisherman_portrait_25", "gloucester_boats_05", "gloucester_boats_07", "gloucester_boats_17", "fisherman_portrait_10", "fisherman_portrait_16"), A("ai/skipper_*.png"))
add("skipper_old", FS("fisherman_portrait_05", "fisherman_portrait_01", "fisherman_portrait_02"), A("ai/skipper_old_*.png"), V(NE, 329, 336))
add("skippers_group", FS("fishermen_boat_08", "gloucester_00", "gloucester_20", "fishermen_21", "fishermen_19", "wharf_14", "dory_14"))
add("kous", A("ai/kous_*.png"), FS("fisherman_portrait_25", "fisherman_portrait_13", "gloucester_boats_17"))
add("caps_off", A("ai/capsoff2_*.png"), A("ai/g09_*.png"))
add("caps_hands", A("ai/capsoff2_*.png"), FS("fishermen_boat_08"))
add("fish_catch", FS("nets_05", "nets_10"), V(GL, 343, 362), V(ZZ, 324, 336))
add("fishcount", A("ai/fishcount_*.png"), FS("nets_05"), V(ZZ, 324, 336))
add("nets", FS("nets_01", "nets_03", "nets_15", "nets_16", "nets_24", "fisherman_portrait_07", "fisherman_portrait_24", "nets_26"), V(SAL, 136, 144, SALC), V(GL, 287, 300))
add("nets_cut", FS("nets_15", "nets_25", "nets_01"))
add("fisherwife", FS("dory_08"), A("ai/fisherwife_*.png"))

# ---------------- village / harbour
add("village", A("ai/village_sa_*.png"), A("ai/g47_*.png"), FS("village_03", "village_09", "village_25", "village_12", "village_13"), V(ZZ, 384, 392))
add("village_people", FS("dory_14", "fishermen_19", "village_22", "dory_06", "fishermen_11"))
add("village_old", FS("village_03", "village_09"), A("ai/village_sa_*.png"))
add("village_night", A("ai/bg_reef_night_*.png"))
add("cottages", A("ai/village_sa_*.png"), V(ZZ, 384, 392), FS("village_25"))
add("cottage_interior", A("ai/g23_*.png"))
add("harbour", FS("harbor_00", "harbor_03", "harbor_05", "harbor_06", "wharf_00", "wharf_06", "wharf_12", "wharf_13", "gloucester_boats_00", "gloucester_boats_03", "village_01", "village_21"), A("ai/harbourwall_*.png"), A("ai/g48_*.png"), V(ZZ, 300, 312))
add("harbour_wall", A("ai/harbourwall_*.png"), A("ai/g48_*.png"), FS("wharf_12", "wharf_13"))
add("quay", FS("fishermen_11", "fishermen_21", "wharf_14", "gloucester_04"), V(ZZ, 306, 312), V(ZZ, 337, 342))
add("dusk_harbour", A("ai/stonehouse_*.png"), FS("wharf_00"))
add("stone_house", A("ai/stonehouse_*.png"))
add("stone_wall", A("ai/doorstep2_*.png"), A("ai/stonehouse_*.png"))
add("window_night", A("ai/stonehouse_*.png"), A("ai/g23_*.png"))
add("smokehouse", A("ai/smokehouse_*.png"))
add("dogs", A("ai/dogs_*.png"))
add("doorstep", A("ai/g22_*.png"), A("ai/doorstep2_*.png"))
add("doorstep_stone", A("ai/g22_*.png"), A("ai/doorstep2_*.png"))
add("officer_doors", A("ai/officer_*.png"), A("ai/g22_*.png"))

# ---------------- people of the story
add("harbourmaster", FS("dory_00", "dory_20", "fisherman_portrait_00"), A("ai/harbourmaster_*.png"), A("ai/g40_*.png"), V(ZZ, 343, 348))
add("keeper_woman", FS("dory_08"), A("ai/keeper_*.png"), A("ai/g41_*.png"), A("ai/g16_*.png"))
add("officer", A("ai/officer_*.png"), A("ai/g42_*.png"))
add("priest", A("ai/priest_*.png"), A("ai/g43_*.png"))
add("priest_pray", A("ai/priest_*.png"), FS("church_04", "church_12"))
add("priest_stone", A("ai/g43_*.png"))
add("brothers_argue", A("ai/g24_*.png"))
add("old_man_wall", A("ai/g44_*.png"), A("ai/oldwall2_*.png"))
add("old_couple", A("ai/g36_*.png"), A("ai/vigil_*.png"))
add("old_couple_boat", A("ai/vigil_*.png"), A("ai/g36_*.png"))
add("children", A("ai/children_*.png"))
add("children_sleep", A("ai/children_*.png"))

# ---------------- records
add("logbook", A("ai/g39_*.png"), A("ai/logbook2_*.png"))
add("logbook_close", A("ai/logbook2_*.png"), A("ai/g39_*.png"))
add("ledger", A("ai/ledger2_*.png"), A("ai/g40_*.png"))
add("ledger_page", A("ai/ledger2_*.png"))
add("keeper_log", A("ai/g41_*.png"), A("ai/ledger2_*.png"))
add("officer_notebook", A("ai/g42_*.png"), A("ai/officer_*.png"), A("ai/logbook2_*.png"))
add("papers", A("ai/ledger2_*.png"), A("ai/logbook2_*.png"), A("ai/sea_chest_*.png"))
add("register", A("ai/ledger2_*.png"), I("stock/reg/reg_b_00.jpg", [0.0, 0.07, 1.0, 0.5]), I("stock/reg/reg_b_00.jpg", [0.0, 0.3, 0.8, 0.75]), I("stock/reg/reg_c_00.jpg", [0.05, 0.12, 0.95, 0.6]))
add("register_marks", [I("comp/register_real_marks.png", c) for c in ([0.45, 0.15, 1.0, 0.55], [0.35, 0.2, 0.95, 0.6], [0.5, 0.35, 1.0, 0.75])])
add("calendar", A("ai/logbook2_*.png"))
add("sea_chest", A("ai/sea_chest_*.png"))
add("tin_trunk", A("ai/g38_*.png"))
add("house_clearance", A("ai/g38_*.png"), A("ai/sea_chest_*.png"))
add("city_office", A("ai/city_office_*.png"))
add("typewriter", A("ai/city_office_*.png"))
add("office_door", A("ai/city_office_*.png"), A("ai/harbourmaster_*.png"))
add("magistrate", A("ai/magistrate_*.png"))
add("bank", A("ai/city_office_*.png"))
add("watch", A("ai/watch_*.png"))

# ---------------- chapel
add("chapel", A("ai/chapel_sa_*.png"), FS("church_ext_00", "church_ext_09", "church_19", "church_ext_19"))
add("chapel_ext", A("ai/chapel_sa_*.png"), FS("church_ext_00", "church_ext_01", "church_ext_07", "church_ext_09", "church_ext_20", "church_19"))
add("chapel_walk", FS("church_ext_19", "church_ext_25"), A("ai/chapel_sa_*.png"))
add("chapel_int", FS("church_02", "church_03", "church_05", "church_09", "church_13", "church_15"), A("ai/chapel_int_*.png"))
add("vestry", FS("church_04", "church_12", "church_01"), A("ai/stonesrow_*.png"))
add("altar", FS("church_04", "church_12", "church_11"))
add("chapel_floor", FS("church_13", "church_09"))
add("chapel_door", A("ai/g13_*.png"), FS("church_ext_07", "church_ext_09"))
add("chapel_step", A("ai/g13_*.png"))
add("chapel_gear", A("ai/g13_*.png"))
add("congregation", FS("church_ext_15", "church_ext_16", "church_ext_14"), A("ai/g27_*.png"), A("ai/confess_*.png"))
add("chapel_confess", A("ai/confess_*.png"), A("ai/g27_*.png"))
add("hand_shoulder", A("ai/handshoulder_*.png"), A("ai/g28_*.png"))
add("stones_table", A("ai/stonesrow_*.png"), A("ai/g29_*.png"))
add("gravestones", FS("cemetery_07", "cemetery_06", "cemetery_22", "cemetery_27", "cemetery_11"))
add("graveyard_rows", FS("cemetery_17", "cemetery_18", "cemetery_08", "cemetery_09", "cemetery_10", "cemetery_12"))

# ---------------- objects
add("anchor", A("ai/g07_*.png"), A("ai/g06_*.png"))
add("anchor_rock", A("ai/g07_*.png"))
add("chain", A("ai/g07_*.png"), A("ai/g06_*.png"))
add("lobster", FS("fisherman_portrait_11", "fisherman_portrait_14"), A("ai/gearrow2_*.png"))
add("rope", FS("dory_24", "nets_03"), A("ai/g08_*.png"))
add("oar", A("ai/g08_*.png"))
add("bell", V(SS, 82, 96), A("ai/g13_*.png"))
add("gaff", A("ai/g08_*.png"))
add("gear_row", A("ai/gearrow2_*.png"), A("ai/g08_*.png"))
add("tools_field", A("ai/g06_*.png"))
add("yard", A("ai/gearrow2_*.png"))
add("farm_gate", A("ai/farm_gate_*.png"))
add("binoculars", V(SS, 342, 350), A("ai/telescope_*.png"))
add("lantern", A("ai/lanternfloat2_*.png"), A("ai/g34_*.png"))
add("lamp_table", A("ai/g23_*.png"))
add("stone_sill", A("ai/stonehouse_*.png"))
add("stone_mark", A("comp/stone_mark_*.png"))
add("bundle", A("ai/bundle2_*.png"))
add("canvas", A("ai/bundle2_*.png"), A("ai/g20_1.png"))
add("relics", A("ai/seaboot_*.png"), A("ai/ring_*.png"), A("ai/knife_*.png"), A("ai/g21_*.png"))
add("point_walk", A("ai/pointwalk_*.png"))
add("point_night", A("ai/g17_*.png"), V(NE, 441, 462))

# ---------------- lighthouse / night
add("lighthouse", FS("lighthouse_00", "lighthouse_01", "lighthouse_03"), V(SS, 42, 50), V(SS, 62, 78), V(SS, 542, 550), A("ai/g16_*.png"))
add("lighthouse_lens", V(SS, 51, 61))
add("lighthouse_night", V(NE, 441, 462), A("ai/g16_*.png"), A("ai/g17_2.png"))
add("lighthouse_stairs", A("ai/g16_*.png"), V(NE, 441, 462))
add("lantern_far", A("ai/g17_*.png"), A("ai/bg_reef_night_*.png"))
add("giant_lantern", A("ai/g18_*.png"))
add("lantern_rock", A("ai/g34_*.png"))
add("lantern_float", A("ai/lanternfloat2_*.png"), A("ai/g37_*.png"), A("ai/vigil_*.png"))

# ---------------- seabed
add("seabed_graves", A("ai/g31_*.png"))
add("seabed_old", A("ai/g31_*.png"))
add("seabed_grave_empty", A("ai/g32_*.png"))
add("seabed_filled", A("ai/gravefilled_*.png"), A("ai/g35_*.png"))

# ---------------- the giant (composites + AI)
add("giant_far", A("comp/giant_far_*.png"), A("comp/giant_wade_*.png"))
add("giant_close", A("comp/giant_close_*.png"), A("comp/giant_chest_2.png"))
add("giant_chest", A("comp/giant_chest_*.png"))
add("giant_wading", A("comp/giant_wade_*.png"), A("comp/giant_far_*.png"))
add("giant_shoulders", A("comp/giant_shoulders_*.png"), A("comp/giant_chest_1.png"))
add("giant_head", A("comp/giant_close_*.png"))
add("giant_looks", A("comp/giant_chest_2.png"), A("comp/giant_chest_3.png"), A("comp/giant_looks_*.png"), A("comp/giant_close_*.png"))
add("giant_bend", A("comp/giant_bend_*.png"))
add("giant_hand", A("comp/giant_bend_*.png"))
add("giant_hand_anchor", A("ai/g06_*.png"))
add("giant_palm", A("comp/giant_palm_*.png"), A("ai/g10_2.png"))
add("giant_away", A("comp/giant_away_*.png"), A("ai/g11_*.png"))
add("giant_cliff", A("comp/giant_cliff_*.png"), A("ai/g19_*.png"))
add("giant_sitting", A("comp/giant_sit_*.png"), A("ai/g33_*.png"))

add("black", [{"color": 0.0}])

L = "stock/loc_c/"
def LC(*names): return [I(L + n + ".jpg") for n in names]
add("gulls_flying", LC("gulls_22", "gulls_19", "gulls_20"), V(OS, 216, 222))
add("gulls_sitting", A("ai/gulls_sit_*.png"), A("ai/g46_*.png"), V(OS, 216, 222), LC("gulls_22"))
add("waves_rocks", LC("waves_01", "waves_02", "waves_07", "waves_11", "waves_12"))
add("storm", LC("waves_02", "waves_07"))
add("boats_dawn", LC("dawnsea_11", "dawnsea_22"))
add("fishermen_still", LC("gulls_23"))

# --- FSA people/chapel additions
add("keeper_woman", FS("oldwoman_03", "widow_13", "widow_15"))
add("congregation", FS("congregation_13", "congregation_00", "congregation_09"))
add("chapel_confess", FS("congregation_02"))
add("chapel_ext", FS("congregation_06", "congregation_07", "congregation_19", "minister_20", "minister_21", "minister_23"))
add("chapel", FS("congregation_06", "minister_21"))
add("priest", FS("minister_15", "minister_16", "minister_08"))
add("priest_pray", FS("minister_15"))
add("village_people", FS("congregation_14", "congregation_16"))
add("skipper_old", FS("oldman_03", "oldman_05", "oldman_19"))
add("fishermen_old", FS("oldman_03", "oldman_13"))
add("officer", FS("minister_00", "minister_24"))
add("officer_notebook", FS("minister_17"))
add("city_office", FS("minister_05", "minister_06", "minister_17"))
add("office_door", FS("minister_06"))
add("ledger", FS("ledger_01", "clerk_03", "clerk_12", "clerk_19"))
add("ledger_page", FS("ledger_01"))
add("harbourmaster", FS("clerk_19", "desk_06", "desk_22"))
add("city_office", FS("desk_13", "clerk_20", "desk_07", "typewriter_21", "clerk_09"))
add("typewriter", FS("typewriter_08", "typewriter_14", "typewriter_24"))
add("officer_notebook", FS("writing_16", "writing_13"))
add("lantern", FS("lantern_04", "lantern_03"))
add("office_door", FS("clerk_02", "clerk_13"))
add("anchor", FS("anchor_00"))
add("fishermen_work", FS("anchor_26"))
add("rope", FS("rope_01"))
add("chapel_door", FS("door_14", "door_06"))
add("window_night", FS("window_27"))
add("capecoast", FS("coast_00", "coast_01", "coast_04", "coast_05"))
add("rocks_point", FS("coast_00", "coast_03", "coast_06", "sea_17"))
add("reef", FS("sea_12", "sea_18", "coast_02"))
add("waves_rocks", FS("sea_01", "sea_02", "sea_17", "sea_18"))
add("smokehouse", FS("smokehouse_00", "smokehouse_01", "smokehouse_02"))
add("gulls_flying", FS("sea_15", "sea_16"))
add("boats_still", FS("captain_18", "captain_26", "captain_27"))
add("boats_sea", FS("captain_18", "captain_26", "cove_10"))
add("fishermen_still", FS("captain_22", "captain_23", "captain_24", "captain_25"))
add("trawler", FS("dragger_01", "dragger_02", "dragger_04", "dragger_08", "dragger_14", "trawler_00", "trawler_01", "trawler_02", "trawler_10"))
add("trawler_still", FS("dragger_01", "trawler_00", "trawler_20"))
add("trawler_dawn", FS("trawler_21", "trawler_22", "dragger_05"))
add("trawler_home", FS("trawler_13", "trawler_16"))
add("children_sleep", FS("children_10", "children_23"))
add("children", FS("children_10", "children_08"))
add("fisherwife", FS("wife_01", "wife_21"))
add("dusk_harbour", FS("trawler_13", "trawler_16"))
add("sea_flat", FS("cove_06", "cove_07", "cove_08"))
add("seabed_graves", A("ai/seabed3_*.png"), A("ai/seabed4_*.png"))
add("seabed_old", A("ai/seabed5_*.png"), A("ai/seabed3_*.png"))
add("graveyard_rows", A("ai/seabed4_*.png"))
add("keeper_log", A("ai/keeper_log2_*.png"))
add("logbook", A("ai/logbook3_*.png"))
add("ledger", A("ai/ledger3_*.png"))
add("harbourmaster", A("ai/ledger3_*.png"))
add("officer", A("ai/officer2_*.png"))
add("officer_notebook", A("ai/officer2_*.png"))
add("lantern_far", A("ai/lantern_sea_*.png"))
add("sea_dark", A("ai/lantern_sea_*.png"))
add("relics", A("ai/g21_*.png"))
add("bundle", A("ai/g20_1.png"), A("ai/g20_2.png"))
add("giant_cliff", A("ai/g19_0.png"), A("ai/g19_1.png"))
add("giant_lantern", A("comp/giant_lantern_*.png"))

add("binoculars", A("ai/telescope_*.png"))
add("keeper_woman", A("ai/telescope_*.png"))

# ---- final overrides
SM = "comp/stone_mark_b.png"
P["stone_mark"] = [I(SM, move="in"), I(SM, [0.25, 0.15, 0.75, 0.85], move="in"), I(SM, [0.3, 0.25, 0.68, 0.75], move="out"), I("comp/stone_mark_a.png", [0.3, 0.2, 0.85, 0.8], move="in")]
P["priest_stone"] = A("ai/g43_*.png") + [I(SM, [0.25, 0.15, 0.75, 0.85])]
P["relics"] = A("ai/seaboot_*.png") + A("ai/ring_*.png") + A("ai/g21_*.png")
P["lantern_far"] = A("ai/g17_*.png") + A("ai/bg_reef_night_*.png")
P["sea_dark"] = [x for x in P["sea_dark"] if "lantern_sea" not in x.get("img", "")]
P["chapel_confess"] = A("ai/g27_*.png") + FS("congregation_02")
P["congregation"] = [x for x in P["congregation"] if "confess" not in x.get("img", "")]
P["seabed_grave_empty"] = A("ai/g32_*.png") + A("ai/gravefilled_0.png")
P["seabed_filled"] = A("ai/g35_*.png") + A("ai/gravefilled_*.png")
P["lantern_float"] = A("ai/g37_*.png") + A("ai/lanternfloat2_*.png") + A("ai/vigil_*.png")
P["old_couple_boat"] = A("ai/vigil_*.png") + A("ai/g36_*.png")
P["old_couple"] = A("ai/g36_*.png")
P["old_man_wall"] = A("ai/oldwall2_*.png") + A("ai/g44_*.png")
P["stones_table"] = A("ai/g29_*.png") + A("ai/stonesrow_*.png")
P["hand_shoulder"] = A("ai/handshoulder_*.png") + A("ai/g28_*.png")
P["yard"] = A("ai/gearrow2_*.png")
P["tin_trunk"] = A("ai/g38_*.png")
P["lantern_rock"] = A("ai/g34_*.png")
P["clear_water"] = A("ai/clearwater_*.png")
P["doorstep_stone"] = A("ai/doorstep2_*.png") + A("ai/g22_*.png")
P["gulls_sitting"] = A("ai/gulls_sit_*.png") + A("ai/g46_*.png")
