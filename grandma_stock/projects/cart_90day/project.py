"""Project config: 90-day grocery cart for a family of four (grandma / pantry style).

All times are ORIGINAL voiceover seconds (from tools/transcribe.py). make.py slows the
voice by SPD and rescales every time automatically.
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))

# ---- inputs (edit these for a new video)
VO = os.environ.get("VO", "/root/.claude/uploads/d98dc366-baed-563d-a5bd-609111141466/893d3802-Part1_Part2_merged_room.mp3")
IMG_DIR = os.environ.get("IMG_DIR", "/root/.claude/uploads/d98dc366-baed-563d-a5bd-609111141466")
IMG_PATTERN = "{id}-image.jpg"      # I:<id> -> IMG_DIR/<id>-image.jpg
VO_DURATION = 622.03                 # original voiceover length in seconds
SPD = 0.93                           # voice 7% slower (user preference)
OUT_NAME = "90_Day_Grocery_Cart"

# ---- shot list: (start_sec, source, motion)
# source: "I:<image id>" or "V:<mixkit clip id>@<offset sec>"
# motion: in | out | left | right  (images: 16% push, clips: 8% push)
SHOTS = [
    (0.00, "V:9681@0.5", "in"),
    (1.90, "I:a21ded54", "in"),
    (4.50, "I:39430412", "in"),
    (7.00, "I:cfe9e4fa", "out"),
    (9.20, "V:45977@0", "in"),
    (10.90, "V:6925@3", "in"),
    (13.40, "I:8f7b2b1b", "in"),
    (16.30, "I:a40f0558", "out"),
    (20.00, "I:c7a91c57", "in"),
    (25.00, "I:17f66f92", "left"),
    (31.00, "I:9dfd8b0b", "in"),
    (35.50, "V:6204@2", "in"),
    (38.00, "V:6102@0", "right"),
    (42.50, "V:14991@0", "in"),
    (47.00, "I:76377cb6", "out"),
    (51.90, "V:30252@0", "in"),
    (55.20, "V:3358@0", "in"),
    (59.70, "I:17f66f92", "in"),
    (62.60, "I:21f44e4f", "right"),
    (64.90, "I:2b55d385", "in"),
    (68.00, "V:22676@4", "in"),
    (70.90, "V:12579@2", "in"),
    (74.10, "V:31969@0", "in"),
    (76.30, "V:45977@0", "out"),
    (82.20, "I:6718445d", "in"),
    (88.00, "I:2b55d385", "out"),
    (89.80, "V:6472@2", "in"),
    (94.10, "I:2b55d385", "in"),
    (97.20, "V:28897@0", "in"),
    (101.70, "I:2b55d385", "left"),
    (104.10, "V:6472@10", "in"),
    (108.80, "V:4554@2", "in"),
    (115.40, "V:14991@3", "in"),
    (117.90, "I:a714c0f9", "in"),
    (122.30, "V:46354@2", "in"),
    (126.30, "I:d1f03eb4", "in"),
    (133.80, "V:3816@0", "in"),
    (138.80, "I:9b48b64a", "right"),
    (142.80, "I:6718445d", "out"),
    (148.80, "I:21f44e4f", "left"),
    (152.10, "I:65235008", "in"),
    (156.80, "I:6aa3e152", "in"),
    (161.20, "V:12581@0", "in"),
    (170.00, "I:79e2291a", "in"),
    (178.30, "V:32608@0", "in"),
    (187.00, "V:12580@2", "in"),
    (197.00, "I:1f563001", "in"),
    (201.70, "I:6718445d", "right"),
    (208.10, "I:ddf4d635", "in"),
    (212.80, "I:1f563001", "out"),
    (219.00, "I:9dfd8b0b", "in"),
    (232.30, "I:21f44e4f", "right"),
    (237.90, "I:76377cb6", "in"),
    (244.50, "I:39430412", "in"),
    (251.60, "I:b31a19db", "in"),
    (260.40, "I:5e1d8ad0", "left"),
    (263.20, "I:f0b79f2f", "in"),
    (272.40, "I:602407c9", "in"),
    (278.60, "V:6204@8", "in"),
    (283.20, "V:40174@0", "in"),
    (292.90, "I:9b48b64a", "left"),
    (298.30, "I:21f44e4f", "in"),
    (309.60, "I:c7a91c57", "out"),
    (313.90, "I:8f7b2b1b", "in"),
    (318.50, "I:9dfd8b0b", "out"),
    (325.80, "V:12579@10", "in"),
    (332.50, "I:e93348d7", "in"),
    (337.80, "V:13935@0", "in"),
    (346.40, "I:a23a36d7", "in"),
    (355.60, "V:47785@2", "in"),
    (362.50, "I:76377cb6", "right"),
    (368.60, "I:21f44e4f", "in"),
    (376.20, "I:17f66f92", "in"),
    (381.00, "I:43d18c1e", "in"),
    (387.10, "V:26344@0", "in"),
    (393.90, "V:47624@0", "in"),
    (396.30, "V:48053@2", "in"),
    (402.20, "I:c005a121", "in"),
    (410.30, "I:76377cb6", "left"),
    (419.40, "V:13198@2", "in"),
    (426.30, "I:d74ee14a", "in"),
    (437.60, "I:3ca5c2bc", "in"),
    (451.10, "V:22022@0", "in"),
    (458.20, "I:3ca5c2bc", "right"),
    (468.10, "I:f625b9ee", "in"),
    (480.30, "I:76377cb6", "in"),
    (495.70, "I:9dfd8b0b", "in"),
    (510.30, "I:cfe9e4fa", "in"),
    (524.80, "I:e93348d7", "out"),
    (532.00, "I:cff28011", "in"),
    (538.50, "I:87f850ba", "in"),
    (545.80, "I:5c616630", "in"),
    (559.50, "I:e93348d7", "in"),
    (569.00, "I:1b5685a0", "right"),
    (576.30, "I:f0b79f2f", "out"),
    (586.80, "I:cedab5ce", "in"),
    (596.60, "V:40176@0", "in"),
    (602.40, "V:40174@3", "in"),
    (607.40, "I:8f7b2b1b", "in"),
    (613.20, "I:5e1d8ad0", "in"),
    (619.20, "I:c7a91c57", "out"),
]
# cuts at hard intros where we want a white flash / no dissolve

# cuts that get a white-flash transition + louder whoosh (new section / new item)
FLASH_CUTS = {1.90, 13.40, 31.00, 117.90, 152.10, 197.00, 313.90, 337.80, 362.50, 381.00,
              396.30, 410.30, 419.40, 426.30, 437.60, 451.10, 468.10}

# ---- ambience beds: (sfx id, start, end, gain_db, file offset)
AMBIENCE = [
    ("1157", 0.0, 12.0, -30, 0), ("1157", 55.2, 59.7, -32, 0), ("1157", 309.6, 313.9, -32, 0),
    ("1157", 619.2, 622.0, -32, 0), ("1330", 51.9, 55.2, -30, 0), ("1330", 332.5, 337.8, -31, 5),
    ("1330", 524.8, 532.0, -31, 8), ("1330", 559.5, 569.0, -31, 12),
]

# ---- music: Mixkit track ids played back to back (crossfaded), ducked under voice
MUSIC = ["616", "584"]
