"""Build plan.json (b-roll scenes, avatar switches, chapter/title cards, pops) and captions.json
from words_fixed.json + video.json (per-video text: chapters, titles, pops, caption fixes, extra concepts)."""
import json, re, random, wave, os
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open("video.json")) if os.path.exists("video.json") else {}

random.seed(7)
WORDS = []
for w in json.load(open("words_fixed.json")):
    if WORDS and ((re.match(r"^[,.%]?\d|^%|^,\d|^\.\d", w["w"]) and re.search(r"[\d$]$", WORDS[-1]["w"]))
                  or re.match(r"^[-&']", w["w"])):
        WORDS[-1]["w"] += w["w"]; WORDS[-1]["e"] = w["e"]
    else:
        WORDS.append(dict(w))
CLIPS = {int(k): v for k, v in json.load(open(f"{KIT}/data/all_clips.json")).items() if int(k) < 100000}
import os
for _f in open(f"{KIT}/data/failed.txt").read().split(): CLIPS.pop(int(_f), None)
with wave.open("voice.wav") as w:
    DUR = w.getnframes() / w.getframerate()

FIX = CFG.get("caption_fixes", {})

# ---------------- sentences ----------------
sents, cur = [], []
for w in WORDS:
    cur.append(w)
    if re.search(r"[.?!]$", w["w"]) or (len(cur) > 28 and w["w"].endswith(",")):
        sents.append(cur); cur = []
if cur: sents.append(cur)

# ---------------- scenes (4-8 s) ----------------
scenes = []
buf = []
for s in sents:
    buf += s
    d = buf[-1]["e"] - buf[0]["s"]
    if d >= 4.0:
        # split long sentences into ~6s pieces
        while buf[-1]["e"] - buf[0]["s"] > 9.0:
            cut = 0
            for i, w in enumerate(buf):
                if w["e"] - buf[0]["s"] > 6.0: cut = i; break
            scenes.append(buf[:cut]); buf = buf[cut:]
        scenes.append(buf); buf = []
if buf: scenes[-1] += buf

# ---------------- concept -> search terms ----------------
CONCEPTS = [
    (r"crash|collaps|plung|panic|fear|disaster|crisis|downturn|decline|fall", "stock market falling crash panic storm"),
    (r"stock|market|share|investor|invest|trading|portfolio", "stock market trading chart graph"),
    (r"headline|news", "news newspaper"),
    (r"microsoft|software|enterprise|productivity|cybersecurity|office", "technology computer office laptop software"),
    (r"cloud|azure|aws|data cent|infrastructure|server", "data center server cloud network technology"),
    (r"artificial intelligence|\bai\b|copilot", "robot artificial technology network"),
    (r"amazon|e-commerce|online shopping|retail|shopping|seller|customer", "online shopping delivery package boxes"),
    (r"logistic|fulfillment|warehouse|delivery|transport", "warehouse delivery truck boxes conveyor"),
    (r"advertis|brand|visibility", "advertising billboard times square"),
    (r"alphabet|google|search|android|online", "smartphone search laptop typing"),
    (r"youtube|video|creator|audience|subscription", "video smartphone social media"),
    (r"regulat|government|central bank|policy", "government building flag"),
    (r"berkshire|buffett|conglomerate", "businessman office building corporate"),
    (r"insurance|premium", "documents signing insurance"),
    (r"rail|train", "train railway"),
    (r"energy|utility", "power plant energy wind turbine"),
    (r"manufactur|factory|industr|consumer product", "factory manufacturing"),
    (r"cash|dollar|money|saving|capital|\$|treasury", "money cash dollars bills"),
    (r"revenue|profit|earning|cash flow|income|valuation|price|worth|value", "money chart growth coins"),
    (r"debt|borrow|loan", "documents signing contract"),
    (r"emergenc", "umbrella rain"),
    (r"divers|concentration|sector", "chart portfolio puzzle"),
    (r"patien|disciplin|calm|wait|time|years|long-term|gradual", "hourglass clock calm"),
    (r"emotion|psycholog|pressure|stress|worr", "stress worried man thinking"),
    (r"research|study|examine|analy|evaluat|understand|compare|watch list", "magnifying glass analyzing documents laptop"),
    (r"strategy|plan|prepar|framework", "chess strategy"),
    (r"opportunit|bargain|discount|cheap|buy", "shopping money coins"),
    (r"global|world|billion|million", "earth globe network"),
    (r"retire|house|younger|older|family", "family house old couple"),
    (r"subscribe|share|channel|watching", "smartphone social media"),
]
CONCEPTS = [(rx, q) for rx, q in CFG.get("extra_concepts", [])] + CONCEPTS
STOP = set("a an the of in on at and with to for from by over under into is are man woman person market".split())

BAD = re.compile(r"green screen|screen|chroma|vertical|newlywed|wedding|bride|perfume|plumbing|euro|christmas|halloween|bikini|sexy|party|drunk|beer|wine|cigar|smok|gun|blood|police|zombie|santa|valentine|nightclub|dj|tattoo|fight|port|crane|badminton|pregnant|dna|sunglasses|password|code|programmer|developer|turbine|jet engine|chinese|praying|pool|escalator|pizza|ibiza|abandoned|dark|mustache|desert|judge|skull|hooded|autograph|celebrity|guitar|static|confused|mask|tokyo|hong kong|chicago|perfume|child patient|cancer|brain scan|x ray|sick|burn|betting|demanding|empty wallet|no longer|ham |poor|hungry|touching the skin|fruit|vegetable|tomato|melon|tangerine|farmers|vendor|antique|chimp|soldier|mosque|dancing|balloon|confetti|thief|lovers|ice cream|turtle|cows|istanbul|guangzhou|shanghai|hacker|heart|orange|pepper|trailer|swans|surfer|scooter|asleep|drowsy|falling asleep|vr glasses|paddle")
name_tokens = {k: set(re.findall(r"[a-z]+", v)) for k, v in CLIPS.items() if not BAD.search(v)}
used = {}
for _c in open(f"{KIT}/data/used_clips.txt").read().split(): used[int(_c)] = -2000.0  # clips used in earlier videos


def pick(text, t):
    tl = text.lower()
    terms = []
    for rx, q in CONCEPTS:
        n = len(re.findall(rx, tl))
        if n: terms.append((n, q))
    terms.sort(key=lambda x: -x[0])
    if not terms: terms = [(1, "stock market chart money")]
    best, bs = None, -1e9
    for k, toks in name_tokens.items():
        sc = 0
        for rank, (n, q) in enumerate(terms[:3]):
            qw = set(q.split()) - STOP
            hit = len(qw & toks)
            sc += hit * (3 - rank) * (1 + 0.3 * n)
        if sc <= 0: continue
        if "vertical" in toks or "portrait" in toks: sc -= 4
        if k in used: sc -= 4 + 30 / (1 + abs(t - used[k]) / 120)
        sc += random.random() * 0.8
        if sc > bs: bs, best = sc, k
    used[best] = t
    return best


CAT = json.load(open(f"{KIT}/data/catalog.json"))
def pool(keys, rx):
    ids = []
    for k in keys:
        for c in CAT.get(k, []):
            if c["id"] in name_tokens and c["id"] not in used and re.search(rx, c["name"]) and c["id"] not in ids: ids.append(c["id"])
    random.shuffle(ids); return ids
NATURE = pool(["forest", "waterfall", "ocean", "lake", "river", "clouds", "sunrise", "flowers", "mountains",
               "landscape", "waves", "green field", "tree", "sky", "nature", "sunset", "mountain"],
              r"forest|waterfall|ocean|lake|river|cloud|sunrise|sunset|flower|mountain|landscape|wave|field|tree|sky|valley|beach|sea|meadow")
BUSINESS = pool(["office building", "business district", "aerial city", "corporate", "skyscraper", "bank building",
                 "new york", "city", "night city"], r"building|skyscraper|city|downtown|tower|office|district|aerial")
print("nature", len(NATURE), "business", len(BUSINESS))

plan = {"duration": DUR, "scenes": [], "titles": [], "avatar": []}
for i, sc in enumerate(scenes):
    s = 0.0 if i == 0 else sc[0]["s"] - 0.15
    e = DUR if i == len(scenes) - 1 else scenes[i + 1][0]["s"] - 0.15
    text = " ".join(w["w"] for w in sc)
    if i % 4 == 3 and NATURE: clip = NATURE.pop()
    elif i % 6 == 1 and BUSINESS: clip = BUSINESS.pop()
    else: clip = pick(text, s)
    used[clip] = s
    plan["scenes"].append({"s": round(s, 3), "e": round(e, 3), "clip": clip, "text": text})

# ---------------- titles (text animation) ----------------
def find(phrase, after=0):
    toks = [x.strip(".,?!") for x in phrase.lower().split()]
    for i in range(len(WORDS)):
        if WORDS[i]["s"] < after: continue
        if all(WORDS[i + j]["w"].lower().strip(".,?!") == toks[j] for j in range(len(toks)) if i + j < len(WORDS)):
            return WORDS[i]["s"]
    raise SystemExit("not found: " + phrase)

TITLES = [tuple(x) for x in CFG.get("titles", [])]          # [phrase, TEXT, sub, seconds]
CHAPTERS = [tuple(x) for x in CFG.get("chapters", [])]      # [phrase, num, TEXT, sub, at_or_null, seconds]
plan["chapters"] = []
for phrase, num, text, sub, at, d in CHAPTERS:
    t = at if at is not None else find(phrase) - 0.1
    plan["chapters"].append({"s": round(max(t, 0), 3), "e": round(t + d, 3), "num": num, "text": text, "sub": sub})
last = 0
for phrase, text, sub, d in TITLES:
    try: t = find(phrase, last)
    except SystemExit as e: print("skip title", e); continue
    if any(c["s"] - 0.5 < t < c["e"] + 0.5 for c in plan["chapters"]): continue
    plan["titles"].append({"s": round(t - 0.1, 3), "e": round(t - 0.1 + d, 3), "text": text, "sub": sub})
    last = t

# number pops (hand-picked)
plan["pops"] = []
for phrase, txt in CFG.get("pops", []):
    try:
        t = find(phrase)
        plan["pops"].append({"s": round(t, 3), "e": round(t + 2.6, 3), "text": txt})
    except SystemExit as e: print("skip pop", e)

# avatar: switch photo every ~20 s at a sentence start (cycle 2 -> 1 -> 3)
starts = [s[0]["s"] for s in sents]
plan["avatar"] = []; cur_s = 0.0; idx = 0; order = [2, 1, 3]
for st in starts:
    if st - cur_s >= 19:
        plan["avatar"].append({"s": round(cur_s, 3), "e": round(st - 0.1, 3), "id": order[idx % 3]})
        cur_s = st - 0.1; idx += 1
plan["avatar"].append({"s": round(cur_s, 3), "e": DUR + 1, "id": order[idx % 3]})

json.dump(plan, open("plan.json", "w"), indent=1)

# ---------------- captions: 2-5 word groups ----------------
caps, g = [], []
for i, w in enumerate(WORDS):
    txt = w["w"]
    for a, b in FIX.items():
        if txt == a: txt = b
    g.append({"w": txt, "s": w["s"], "e": w["e"]})
    nxt = WORDS[i + 1] if i + 1 < len(WORDS) else None
    brk = (len(g) >= 4 or re.search(r"[.?!,;:]$", txt) or nxt is None or nxt["s"] - w["e"] > 0.45
           or sum(len(x["w"]) for x in g) > 22)
    if brk and (len(g) >= 2 or nxt is None or re.search(r"[.?!]$", txt) or nxt["s"] - w["e"] > 0.45):
        caps.append({"s": g[0]["s"], "e": g[-1]["e"], "words": g}); g = []
for i in range(len(caps) - 1):
    caps[i]["e"] = min(caps[i]["e"] + 0.25, caps[i + 1]["s"] - 0.02) if caps[i + 1]["s"] - caps[i]["e"] < 0.6 else caps[i]["e"] + 0.15
json.dump(caps, open("captions.json", "w"))
print("scenes", len(plan["scenes"]), "unique clips", len({s["clip"] for s in plan["scenes"]}), "captions", len(caps))
