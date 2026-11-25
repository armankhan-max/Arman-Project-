"""Shot list, text animations and captions, timed to audio/voice_clean.wav (transcript.json)."""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
STOCK = os.path.join(HERE, "stock")
TX = json.load(open(os.path.join(HERE, "transcript.json")))
WORDS = [w for s in TX for w in s["words"]]
END = 956.53 + 1.2

# ------------------------------------------------------------------ shots
# (cut time, source, move).  "i:" = still image (Ken Burns), "v:" = stock video.
CUTS = [
    (0.00, "i:av_main", "face"),
    (3.40, "i:majlis_circle", "in"),
    (5.90, "v:coffee_pour_cup", "in"),
    (8.10, "i:av_talk_guest", "faceR"),
    (11.40, "v:counting_bills", "in"),
    (14.00, "v:empty_wallet", "in"),
    (15.90, "i:av_explain", "face"),
    (18.30, "v:dubai_downtown", "in"),
    (21.60, "i:books_desk", "in"),
    (25.40, "v:suit_street", "in"),
    (28.50, "i:av_gesture", "face"),
    (32.00, "v:hourglass_black", "in"),
    (35.20, "i:av_hands", "faceR"),
    (40.30, "v:burj_night", "out"),
    (43.50, "i:majlis_wall", "in"),
    (47.80, "v:bazaar_timelapse", "in"),
    (52.40, "v:gold_coins_table", "in"),
    (53.90, "v:depressed_man", "in"),
    (55.00, "i:av_reading", "face"),
    (59.00, "v:hand_writing", "in"),
    (62.70, "v:worried_bills", "in"),
    (67.20, "i:camel_village", "in"),
    (73.90, "i:av_explain", "faceL"),
    (75.80, "i:souk_spices", "right"),
    (79.00, "i:souk_guide", "in"),
    (82.00, "i:perfume_seller", "left"),
    (85.80, "i:av_main", "out"),
    (88.20, "v:clock_bills", "in"),
    (97.90, "v:blueprints", "in"),
    (100.50, "v:dubai_port", "in"),
    (103.60, "v:palms_wind", "in"),
    (105.80, "v:man_thinking", "in"),
    (110.20, "v:old_man_coins", "in"),
    (114.20, "i:av_gesture", "face"),
    (116.40, "v:carpenter_chisel", "in"),
    (118.30, "v:carpenter_table", "in"),
    (122.60, "v:construction_aerial", "in"),
    (125.80, "v:carpenter_sanding", "in"),
    (127.50, "v:handshake", "in"),
    (130.90, "v:work_meeting", "in"),
    (134.10, "v:watch_hands", "in"),
    (137.60, "v:hourglass_desert", "in"),
    (142.40, "i:av_coffee", "face"),
    (145.40, "v:burj_timelapse", "in"),
    (148.50, "i:av_hands", "faceL"),
    (152.90, "v:library_shelf", "in"),
    (157.40, "i:av_reading", "face"),
    (160.30, "v:old_book_pages", "in"),
    (163.90, "v:old_books", "in"),
    (166.90, "v:caravan", "in"),
    (170.00, "v:father_son_reading", "in"),
    (172.30, "i:av_main", "faceR"),
    (175.20, "v:coin_jar", "in"),
    (179.00, "v:piggy_coins", "in"),
    (182.30, "i:av_explain", "faceR"),
    (186.50, "i:books_desk", "out"),
    (191.10, "v:brown_notebook", "in"),
    (193.30, "v:stock_profit", "in"),
    (195.40, "v:signing_contract", "in"),
    (197.50, "i:av_gesture", "faceL"),
    (199.60, "v:suit_street", "out"),
    (203.80, "v:man_thinking", "out"),
    (207.00, "i:av_main", "faceR"),
    (211.90, "v:hourglass_black", "out"),
    (216.10, "i:lantern_village", "in"),
    (220.90, "i:av_explain", "faceL"),
    (223.80, "v:shepherd_camels", "in"),
    (227.10, "i:camel_village", "in"),
    (230.90, "v:desert_stars", "in"),
    (234.20, "v:lantern_flame", "in"),
    (236.70, "i:lantern_village", "faceL"),
    (239.80, "v:dunes", "in"),
    (245.50, "i:camel_village", "right"),
    (250.30, "i:av_hands", "face"),
    (252.60, "v:arab_walk_desert", "in"),
    (256.90, "v:depressed_man", "out"),
    (259.30, "v:worried_bills", "out"),
    (266.90, "v:crane_sunset", "in"),
    (270.00, "i:av_explain", "in"),
    (276.30, "i:souk_guide", "faceR"),
    (280.90, "v:suit_window", "in"),
    (284.50, "v:elderly_window", "in"),
    (288.60, "i:majlis_circle", "in"),
    (292.90, "i:majlis_wall", "inR"),
    (296.70, "v:palm_jumeirah", "in"),
    (299.80, "i:av_talk_guest", "in"),
    (302.90, "i:av_main", "out"),
    (304.70, "v:work_meeting", "out"),
    (308.60, "v:blueprints", "out"),
    (312.00, "v:rainy_window", "in"),
    (316.90, "i:coffee_pour", "in"),
    (318.60, "i:av_coffee", "faceL"),
    (323.40, "i:majlis_circle", "out"),
    (326.70, "i:av_hands", "in"),
    (330.70, "v:carpenter_grandson", "in"),
    (334.20, "v:depressed_man", "in"),
    (341.30, "i:av_explain", "faceR"),
    (343.60, "v:watch_hands", "out"),
    (347.20, "i:majlis_wall", "left"),
    (351.40, "i:av_main", "face"),
    (353.40, "v:spices_market", "in"),
    (357.10, "v:coins_falling", "in"),
    (359.60, "i:av_gesture", "in"),
    (361.80, "i:perfume_bottle", "in"),
    (366.00, "i:av_talk_guest", "faceL"),
    (370.40, "i:av_explain", "in"),
    (377.00, "i:perfume_seller", "inL"),
    (381.80, "i:souk_spices", "left"),
    (383.10, "i:perfume_bottle", "out"),
    (387.80, "i:perfume_seller", "inR"),
    (394.50, "v:bazaar_timelapse", "out"),
    (396.80, "i:souk_guide", "in"),
    (400.00, "v:perfume_shop", "in"),
    (404.80, "i:souk_guide", "faceR"),
    (407.90, "v:cash_table", "in"),
    (411.10, "i:perfume_seller", "out"),
    (413.50, "i:av_main", "faceL"),
    (416.00, "v:gold_coins_table", "out"),
    (419.00, "v:suit_street", "in"),
    (422.20, "v:brown_notebook", "out"),
    (425.30, "i:av_gesture", "faceR"),
    (427.90, "v:handshake", "out"),
    (431.60, "v:work_meeting", "in"),
    (437.80, "i:av_explain", "in"),
    (442.30, "i:av_hands", "faceL"),
    (451.20, "v:clock_bills", "out"),
    (453.40, "v:empty_wallet", "out"),
    (455.60, "v:elderly_window", "out"),
    (460.80, "v:desert_timelapse", "in"),
    (465.40, "i:av_talk_guest", "in"),
    (469.60, "i:leaking_room", "in"),
    (471.20, "v:worried_bills", "in"),
    (475.10, "i:av_talk_guest", "faceL"),
    (478.00, "i:av_explain", "faceR"),
    (483.40, "v:thinking_beard", "in"),
    (488.80, "v:blueprints", "in"),
    (492.00, "v:construction_aerial", "out"),
    (496.40, "v:suit_window", "out"),
    (500.40, "i:leaking_room", "out"),
    (504.50, "i:av_main", "faceR"),
    (507.10, "i:av_gesture", "in"),
    (508.50, "v:desert_timelapse", "out"),
    (513.10, "v:dubai_downtown", "out"),
    (518.30, "v:rainy_window", "out"),
    (521.30, "v:burj_timelapse", "out"),
    (525.40, "v:palm_jumeirah", "out"),
    (528.00, "i:av_hands", "out"),
    (531.80, "i:majlis_wall", "in"),
    (535.40, "i:suit_watch", "in"),
    (540.40, "v:suit_street", "in"),
    (544.00, "i:av_talk_guest", "in"),
    (546.50, "i:suit_watch", "faceR"),
    (549.80, "v:counting_bills", "out"),
    (555.80, "i:av_main", "face"),
    (559.00, "i:av_hands", "in"),
    (561.90, "i:suit_watch", "out"),
    (566.30, "v:hourglass_black", "in"),
    (569.90, "v:suit_window", "in"),
    (575.80, "i:av_explain", "faceL"),
    (578.00, "i:av_gesture", "in"),
    (583.10, "v:gold_coins_table", "in"),
    (595.80, "v:piggy_coins", "out"),
    (599.60, "v:counting_bills", "in"),
    (603.00, "v:empty_wallet", "in"),
    (607.30, "i:av_explain", "in"),
    (614.10, "i:av_hands", "faceR"),
    (617.20, "v:coin_jar", "out"),
    (620.40, "i:lantern_village", "in"),
    (623.40, "i:av_gesture", "faceL"),
    (628.10, "v:thinking_beard", "out"),
    (632.80, "i:av_main", "in"),
    (636.30, "v:burj_night", "in"),
    (640.90, "i:well_palms", "in"),
    (646.20, "i:av_explain", "inL"),
    (648.20, "i:suit_watch", "in"),
    (650.80, "i:porsche_house2", "in"),
    (654.00, "i:porsche_house", "left"),
    (656.80, "v:suit_street", "out"),
    (659.00, "i:old_shop_car", "in"),
    (663.50, "v:signing_contract", "in"),
    (669.50, "i:old_shop_car", "right"),
    (672.90, "v:hourglass_desert", "in"),
    (674.40, "i:av_main", "faceL"),
    (677.20, "v:clock_bills", "in"),
    (681.20, "i:porsche_house2", "out"),
    (684.00, "i:old_shop_car", "out"),
    (687.40, "i:av_writing", "in"),
    (688.70, "i:well_palms", "out"),
    (692.50, "v:river_aerial", "in"),
    (696.00, "v:rain_roof", "in"),
    (699.20, "i:well_palms", "inR"),
    (701.40, "v:family_sunset", "in"),
    (707.20, "i:av_writing2", "in"),
    (711.60, "v:brown_notebook", "in"),
    (715.30, "i:av_writing", "faceL"),
    (718.70, "i:books_desk", "in"),
    (724.70, "v:gold_coins_table", "in"),
    (729.00, "v:stock_profit", "out"),
    (733.20, "v:man_thinking", "in"),
    (740.20, "i:av_coffee", "faceR"),
    (742.30, "i:av_main", "in"),
    (747.70, "i:av_gesture", "faceL"),
    (754.40, "i:av_hands", "in"),
    (759.40, "v:old_books", "out"),
    (765.40, "i:av_explain", "faceR"),
    (767.80, "v:counting_bills", "in"),
    (773.50, "v:cash_table", "out"),
    (778.20, "i:av_writing", "in"),
    (784.00, "v:coin_jar", "in"),
    (796.10, "v:empty_wallet", "in"),
    (802.40, "v:old_man_coins", "out"),
    (804.10, "i:av_explain", "in"),
    (811.30, "i:av_main", "faceL"),
    (813.90, "v:gold_coins_table", "out"),
    (819.20, "v:palm_sun", "in"),
    (824.80, "i:coffee_pour", "in"),
    (827.70, "i:majlis_circle", "in"),
    (833.50, "i:majlis_wall", "faceR"),
    (836.60, "v:handshake", "in"),
    (842.90, "v:palms_wind", "in"),
    (850.10, "i:av_main", "face"),
    (851.80, "v:watering_pot", "in"),
    (855.40, "i:sapling_pouch", "in"),
    (860.40, "v:sun_palms", "in"),
    (869.70, "v:rainy_window", "in"),
    (873.50, "v:carpenter_grandson", "out"),
    (880.80, "v:old_book_pages", "out"),
    (891.70, "v:burj_timelapse", "in"),
    (896.20, "i:majlis_circle", "out"),
    (898.80, "i:av_hands", "faceL"),
    (900.90, "v:family_sunset", "out"),
    (905.50, "v:father_son_reading", "out"),
    (911.60, "i:av_main", "in"),
    (914.00, "i:majlis_wall", "in"),
    (926.90, "i:well_palms", "in"),
    (940.30, "i:av_explain", "in"),
    (943.20, "v:sun_palms", "out"),
    (946.00, "i:av_gesture", "faceR"),
    (952.40, "i:av_coffee", "in"),
]

SHOTS = []
for k, (t, src, mv) in enumerate(CUTS):
    e = CUTS[k + 1][0] if k + 1 < len(CUTS) else END
    # the dissolve straddles the cut: start the outgoing shot's fade 0.25 s before, end 0.25 s after
    kind, ref = src.split(":", 1)
    path = "img:" + ref if kind == "i" else "vid:" + os.path.join(STOCK, ref + ".mp4")
    SHOTS.append({"s": t, "e": e + (0.25 if k + 1 < len(CUTS) else 0), "src": path, "mv": mv})
for k in range(1, len(SHOTS)):
    SHOTS[k]["s"] = SHOTS[k - 1]["e"]


# ------------------------------------------------------------------ helpers
def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def wt(phrase, after=0.0):
    """Start time of the first occurrence of `phrase` after `after` seconds."""
    p = [norm(x) for x in phrase.split()]
    for i, w in enumerate(WORDS):
        if w["s"] < after:
            continue
        if all(i + j < len(WORDS) and norm(WORDS[i + j]["w"]) == p[j] for j in range(len(p))):
            return w["s"]
    raise KeyError(phrase)


def habit(n, text, s, e):
    return {"k": "title", "s": s, "e": e, "top": f"HABIT {n} OF 10", "text": text}


def kw(text, s, e, pos="top", size=64, col=None):
    o = {"k": "kw", "text": text, "s": s, "e": e, "pos": pos, "size": size}
    if col:
        o["col"] = col
    return o


CREAMC = (250, 242, 225)

OVERLAYS = [
    kw("10 SMALL HABITS", 22.0, 25.3),
    kw("HABIT #7", 29.6, 33.8, size=58),
    {"k": "lower", "name": "SHEIKH UMAR", "role": "Dubai  •  40+ years in the majlis", "s": 40.9, "e": 47.2},
    kw("RICH ONES", 52.6, 53.95, size=56, col=CREAMC),
    kw("RUINED ONES", 54.0, 55.1, size=56, col=CREAMC),
    habit(1, "Paid for Value, Not Hours", 67.39, 73.8),
    {"k": "quote", "text": "“Who is better off because of what you did?”", "s": 82.2, "e": 85.8},
    kw("TIME = THE COST", 92.38, 95.1),
    kw("RESULT = THE PRODUCT", 95.16, 97.9),
    kw("1 TABLE  vs  100 HOMES", 123.2, 127.4, col=CREAMC),
    kw("WHERE CAN I CREATE THE MOST VALUE?", 145.55, 148.4, size=54),
    habit(2, "Read & Sit With Those Older Than You", 153.08, 157.3),
    kw("2–3 HOURS EVERY MORNING", 160.43, 163.8, size=56),
    kw("KNOWLEDGE = A DEPOSIT", 175.41, 178.9),
    kw("20 MINUTES A DAY", 212.09, 216.0, pos="mid", size=80),
    habit(3, "Find the Opportunity Inside the Problem", 216.28, 220.8),
    {"k": "quote", "text": "“Nobody owns a lantern? Then every house in this village is a customer.”", "s": 239.92, "e": 245.4},
    kw("ONE SAW A WALL", 252.74, 254.6, size=60, col=CREAMC),
    kw("ONE SAW A DOOR", 254.65, 256.8, size=60),
    kw("“IT IS TOO HARD”", 262.01, 263.5, size=54, col=CREAMC),
    kw("“TOO MUCH COMPETITION”", 263.55, 265.85, size=54, col=CREAMC),
    kw("“THE MARKET IS CLOSED”", 265.89, 266.9, size=54, col=CREAMC),
    kw("WHAT IS MISSING HERE?", 272.47, 276.2),
    habit(4, "Guard Who Sits in Your Circle", 288.76, 292.85),
    kw("YOU BECOME YOUR CIRCLE", 323.6, 326.6),
    kw("NONE OF THEM COST A SINGLE DIRHAM", 357.25, 359.6, size=50),
    habit(5, "Speak About Your Value Out Loud", 377.21, 381.7),
    {"k": "quote", "text": "“A diamond in your pocket feeds nobody.”", "s": 416.13, "e": 419.0},
    kw("SAY WHAT YOU DO", 444.79, 446.1, size=58),
    kw("SAY WHO IT HELPS", 446.15, 448.1, size=58),
    kw("SAY YOUR PRICE — CALMLY", 448.13, 451.2, size=58),
    habit(6, "Make Your Goals Bigger Than Your Problems", 461.01, 465.3),
    kw("WHAT DO YOU WANT TO BUILD IN 10 YEARS?", 481.57, 485.0, size=50),
    kw("40 EMPLOYEES • A WHOLE REGION", 492.15, 496.3, size=54),
    kw("SMALL GOAL → PROBLEMS LOOK LIKE MOUNTAINS", 508.63, 513.0, size=46, col=CREAMC),
    kw("BIG GOAL → PROBLEMS SHRINK", 514.91, 518.2, size=54),
    habit(7, "Hold Both Ideas, Not One", 531.95, 535.3),
    kw("EARN MORE — OR SPEND LESS?", 552.11, 555.8, size=58, col=CREAMC),
    kw("BOTH.", 556.9, 559.0, pos="upper", size=110),
    kw("POOR THINKING: EITHER / OR", 578.2, 580.7, size=56, col=CREAMC),
    kw("RICH THINKING: BOTH / AND", 580.76, 583.1, size=56),
    {"k": "list", "s": 583.28, "e": 595.7, "items": ["Earn more & spend wisely", "Save carefully & invest boldly",
                                                    "Be generous & stay strong", "Be patient & move fast"],
     "at": [583.28, 585.62, 588.18, 591.10]},
    kw("WHAT WOULD IT LOOK LIKE IF I DID BOTH?", 632.94, 636.3, size=50),
    habit(8, "Count What You Own, Not What You Earn", 641.11, 646.1),
    kw("BIG SALARY • NEW CAR • BIG LOAN", 650.99, 656.8, size=54, col=CREAMC),
    kw("SMALL INCOME • OWNS ASSETS", 663.69, 669.4, size=54),
    kw("10 YEARS LATER…", 673.09, 674.5, size=60),
    kw("HOW LONG COULD YOU LAST?", 677.41, 681.3),
    kw("3 MONTHS", 681.41, 684.1, pos="mid", size=90, col=CREAMC),
    kw("FOREVER", 684.21, 687.4, pos="mid", size=90),
    {"k": "quote", "text": "“Do not be proud of the river. Dig the well.”", "s": 688.84, "e": 692.5},
    kw("RIVER = INCOME", 692.6, 696.0),
    kw("WELL = WHAT YOU OWN", 699.34, 703.0),
    kw("WHAT I OWN  −  WHAT I OWE", 711.9, 718.6),
    kw("IT GROWS = WINNING", 724.84, 728.9, size=58),
    kw("IT SHRINKS = LOSING", 729.10, 733.1, size=58, col=CREAMC),
    habit(9, "Give Your Money Its Orders First", 768.01, 773.4),
    {"k": "list", "s": 784.19, "e": 796.0, "items": ["Savings", "What I own — the wells", "Giving", "Only then: living"],
     "at": [784.19, 786.55, 790.51, 793.15]},
    {"k": "quote", "text": "“The first coin belongs to your future, the second to your community, the third to your table.”",
     "s": 814.05, "e": 819.2},
    habit(10, "Do It All for a Very Long Time", 843.14, 850.0),
    {"k": "quote", "text": "“I am not planting for this season. I am planting for the family that will sit under it.”",
     "s": 860.54, "e": 869.6},
    kw("30 YEARS", 873.68, 880.7, size=70),
    {"k": "list", "s": 880.96, "e": 891.6, "items": ["Reading every morning", "Counting what he owns", "Dividing money first",
                                                    "Choosing his circle"],
     "at": [wt("reading every", 880), wt("counting what", 880), wt("dividing the money", 880), wt("choosing his", 880)]},
    {"k": "list", "s": 914.13, "e": 926.9,
     "items": ["Paid for value, not hours", "Read & sit with those who know", "Find the door in the problem",
               "Guard your circle", "Speak clearly about your value"],
     "at": [914.13, 916.99, 920.23, 923.01, 924.49]},
    {"k": "list", "s": 927.03, "e": 940.2,
     "items": ["Goals bigger than troubles", "Hold both ideas, not one", "Count what you own",
               "Give money its orders first", "Do it patiently for years"],
     "at": [927.03, 929.57, 932.77, 934.67, wt("patiently", 934)]},
    {"k": "title", "s": 953.0, "e": END - 0.2, "top": "SHEIKH UMAR", "text": "See you in the next Majlis"},
]
# number lists 6-10 correctly
for o in OVERLAYS:
    if o["k"] == "list" and o["items"][0].startswith("Goals bigger"):
        o["offset"] = 5

# ------------------------------------------------------------------ captions
FIX = [
    (r"\bA chic\b", "A Sheikh"), (r"\bChic\b", "Sheikh"), (r"\bchic\b", "Sheikh"), (r"\bAshik\b", "A Sheikh"),
    (r"\b[Mm]ajolise?\b", "majlis"), (r"\bMajlis\b", "majlis"), (r"\bsoup\b", "souk"), (r"\bood\b", "oud"),
    (r"\bDurham\b", "dirham"), (r"\bnot ours\b", "not hours"), (r"\bit's orders\b", "its orders"),
    (r"^To remain\b", "Two remain"),
]


def fix_text(s):
    for a, b in FIX:
        s = re.sub(a, b, s)
    return s


CHUNKS = []   # (words, [(s,e)], start, end)
for seg in TX:
    ws = seg["words"]
    cur = []
    for i, w in enumerate(ws):
        cur.append(w)
        txt = w["w"].strip()
        brk = len(cur) >= 7 or (txt[-1:] in ",.?!;" and len(cur) >= 3) or i == len(ws) - 1
        if brk:
            text = fix_text(" ".join(x["w"].strip() for x in cur))
            text = text[:1].upper() + text[1:]
            words = text.split()
            times = [(x["s"], x["e"]) for x in cur]
            if len(words) != len(times):      # a fix merged/split words: fall back to even timing
                s0, e0 = cur[0]["s"], cur[-1]["e"]
                times = [(s0 + (e0 - s0) * k / len(words), 0) for k in range(len(words))]
            CHUNKS.append((words, times, cur[0]["s"], cur[-1]["e"]))
            cur = []
# hold each chunk until the next one starts (max 0.9 s of tail)
CAP = []
for k, (words, times, s, e) in enumerate(CHUNKS):
    nxt = CHUNKS[k + 1][2] if k + 1 < len(CHUNKS) else e + 1
    CAP.append((words, times, s - 0.05, min(nxt - 0.05, e + 0.9)))


def caption_at(t):
    lo, hi = 0, len(CAP) - 1
    while lo <= hi:
        m = (lo + hi) // 2
        if CAP[m][2] > t:
            hi = m - 1
        else:
            lo = m + 1
    if hi >= 0 and CAP[hi][2] <= t <= CAP[hi][3]:
        return CAP[hi]
    return None
