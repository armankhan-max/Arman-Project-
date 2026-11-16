"""Build plan.json (b-roll scenes, avatar switches, titles) and captions.json from words_fixed.json."""
import json, re, random, wave

random.seed(7)
WORDS = []
for w in json.load(open("words_fixed.json")):
    if WORDS and ((re.match(r"^[,.%]?\d|^%|^,\d|^\.\d", w["w"]) and re.search(r"[\d$]$", WORDS[-1]["w"]))
                  or re.match(r"^[-&']", w["w"])):
        WORDS[-1]["w"] += w["w"]; WORDS[-1]["e"] = w["e"]
    else:
        WORDS.append(dict(w))
CLIPS = {int(k): v for k, v in json.load(open("all_clips.json")).items() if int(k) < 100000}
import os
for _f in (open("failed.txt").read().split() if os.path.exists("failed.txt") else []): CLIPS.pop(int(_f), None)
with wave.open("voice.wav") as w:
    DUR = w.getnframes() / w.getframerate()

FIX = {"Wire": "Why", "underline": "underlying", "review in": "reviewing", "organize in": "organizing"}

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
    (r"index fund|s&p|stock|market|compan|exchange|broker|fund", "stock market trading chart graph screen"),
    (r"technolog", "technology computer"),
    (r"consumer goods|shopping", "shopping supermarket"),
    (r"cash|dollar|money|savings|wealth|\$", "money cash dollars bills counting"),
    (r"compound|double|grow|rule of 72|return|percent|%", "coins money growing stack chart"),
    (r"inflation|cost of living|purchasing power|price", "supermarket groceries prices shopping"),
    (r"grocer", "groceries supermarket"),
    (r"electricity|utility|energy", "electricity light bulb power"),
    (r"transportation", "car traffic road"),
    (r"housing|home|house|property|properties|residential", "house home neighborhood"),
    (r"bond|treasury|government|tips", "treasury government documents flag capitol"),
    (r"tax", "tax documents calculator"),
    (r"gold|bars|coins", "gold coins gold bars"),
    (r"central bank|bank", "bank"),
    (r"rent|tenant|landlord", "keys apartment rent"),
    (r"mortgage|debt|loan|financ", "documents signing contract"),
    (r"repair|maintenance", "repair tools"),
    (r"apartment complex|shopping center|office|warehouse", "apartment building warehouse office"),
    (r"solar", "solar panels"),
    (r"insulation|window|heating|cooling|heat pump|thermostat|temperature", "heating windows home interior"),
    (r"install|quote|warrant", "construction worker installation"),
    (r"accessib|lighting|flooring|bathroom|entryway", "home interior living room"),
    (r"health|medical|hospital|treatment|checkup|screening|well-being", "doctor hospital medical patient"),
    (r"dental", "dentist"),
    (r"insurance|policy|policies|premium|coverage", "documents signing insurance"),
    (r"long-term care|assistance|care", "nurse elderly care"),
    (r"education|knowledge|learn|book|course|literacy|website", "reading books library laptop"),
    (r"scam|fraud", "hacker phone scam"),
    (r"professional|advice|advisor|guidance", "businessman meeting consultation"),
    (r"estate planning|will|beneficiar|inherit|legal|document", "lawyer signing documents"),
    (r"family", "family grandparents"),
    (r"retire|60s|older|age", "old couple senior elderly"),
    (r"risk|uncertain|downturn|lose|loss|fluctuat|instab|volatil", "storm stock market falling"),
    (r"time|years|decades|patien|consisten|long-term", "clock hourglass time"),
    (r"peace of mind|freedom|lifestyle|enjoy|independence|life", "old couple beach sunset walking happy"),
    (r"question|decid|decision|consider|think|imagine", "old man thinking"),
    (r"subscribe|share|channel|video", "phone smartphone"),
    (r"car|watch|luxur|possession", "luxury car watch"),
    (r"emergenc", "ambulance emergency"),
    (r"budget|expense|bill|cost|fee", "bills calculator budget"),
    (r"divers", "portfolio chart stocks"),
]
STOP = set("a an the of in on at and with to for from by over under into is are man woman person".split())

BAD = re.compile(r"green screen|screen|chroma|vertical|newlywed|wedding|bride|perfume|plumbing|euro|christmas|halloween|bikini|sexy|party|drunk|beer|wine|cigar|smok|gun|blood|police|zombie|santa|valentine|nightclub|dj|tattoo|fight|port|crane|badminton|pregnant|dna|sunglasses|password|code|programmer|developer|turbine|jet engine|chinese|praying|pool|escalator|pizza|ibiza|abandoned|dark|mustache|desert|judge|skull|hooded|autograph|celebrity|guitar|static|confused|mask|tokyo|hong kong|chicago|perfume|child patient|cancer|brain scan|x ray|sick|burn|betting|demanding|empty wallet|no longer|ham |poor|hungry|touching the skin")
name_tokens = {k: set(re.findall(r"[a-z]+", v)) for k, v in CLIPS.items() if not BAD.search(v)}
used = {}


def pick(text, t):
    tl = text.lower()
    terms = []
    for rx, q in CONCEPTS:
        n = len(re.findall(rx, tl))
        if n: terms.append((n, q))
    terms.sort(key=lambda x: -x[0])
    if not terms: terms = [(1, "old couple senior happy")]
    best, bs = None, -1e9
    for k, toks in name_tokens.items():
        sc = 0
        for rank, (n, q) in enumerate(terms[:3]):
            qw = set(q.split()) - STOP
            hit = len(qw & toks)
            sc += hit * (3 - rank) * (1 + 0.3 * n)
        if sc <= 0: continue
        if "vertical" in toks or "portrait" in toks: sc -= 4
        if k in used: sc -= 6 + 30 / (1 + (t - used[k]) / 120)
        sc += random.random() * 0.8
        if sc > bs: bs, best = sc, k
    used[best] = t
    return best


CAT = json.load(open("catalog.json"))
def pool(keys, rx):
    ids = []
    for k in keys:
        for c in CAT.get(k, []):
            if c["id"] in name_tokens and re.search(rx, c["name"]) and c["id"] not in ids: ids.append(c["id"])
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
    if i % 3 == 2 and NATURE: clip = NATURE.pop()
    elif i % 7 == 4 and BUSINESS: clip = BUSINESS.pop()
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

TITLES = [
    ("smartest wealth", "YOUR 60s", "The smartest wealth-building decade", 4.5),
    ("seven smart things", "7 SMART PURCHASES", "That could help double your wealth", 4.5),
    ("is not guaranteed", "NOT GUARANTEED", "No investment can promise it", 4.0),
    ("number one", "#1  LOW-COST INDEX FUNDS", "Track the whole market", 5.0),
    ("approximately 500", "S&P 500", "~500 leading American companies", 4.0),
    ("suppose you invest", "$100,000 @ 7.2%", "≈ $200,000 in 10 years", 5.0),
    ("rule of 72", "RULE OF 72", "72 ÷ return % = years to double", 5.0),
    ("annual expense ratio", "0.05%  vs  1%", "Fees quietly eat your returns", 5.0),
    ("number two", "#2  INFLATION-PROTECTED BONDS", "Protect your purchasing power", 5.0),
    ("$40,000", "$40,000 → $53,800", "3% inflation over 10 years", 5.0),
    ("commonly known as tips", "TIPS", "Treasury Inflation-Protected Securities", 4.5),
    ("phantom income", "PHANTOM INCOME", "Taxed before you receive it", 4.0),
    ("number three", "#3  PHYSICAL GOLD", "A store of value", 5.0),
    ("does not generate regular income", "NO DIVIDENDS. NO INTEREST.", "Gold pays no income", 4.0),
    ("diversification, not speculation", "DIVERSIFY, DON'T SPECULATE", "", 4.0),
    ("number four", "#4  INCOME REAL ESTATE", "Rental income + appreciation", 5.0),
    ("real estate investment trusts", "REITs", "Real Estate Investment Trusts", 4.5),
    ("number five", "#5  ENERGY-EFFICIENT HOME", "Cut your household costs", 5.0),
    ("solar panels", "SOLAR PANELS", "Check the payback period", 4.0),
    ("number six", "#6  HEALTH & LONG-TERM CARE", "Protect your savings", 5.0),
    ("preventive health care", "PREVENTIVE CARE", "Checkups • Screenings • Dental", 4.0),
    ("number seven", "#7  FINANCIAL EDUCATION", "Invest in knowledge", 5.0),
    ("financial scams", "BEWARE OF SCAMS", "Too good to be true? It is.", 4.0),
    ("estate planning", "ESTATE PLANNING", "Will • Beneficiaries • Documents", 4.0),
    ("let's bring all seven", "THE BIG PICTURE", "All 7 purchases together", 4.0),
    ("time and consistency", "TIME + CONSISTENCY", "Matter more than excitement", 4.5),
    ("ask yourself three questions", "ASK YOURSELF 3 QUESTIONS", "Before any major purchase", 4.5),
    ("never invest money you cannot", "NEVER INVEST WHAT YOU", "can't afford to lose", 4.5),
    ("subscribe to the channel", "SUBSCRIBE", "For more practical financial insights", 4.5),
]
last = 0
for phrase, text, sub, d in TITLES:
    t = find(phrase, last)
    plan["titles"].append({"s": round(t - 0.1, 3), "e": round(t - 0.1 + d, 3), "text": text, "sub": sub})
    last = t

# ---------------- avatar photo per section ----------------
bounds = [0] + [find(p) for p in ("number one", "number two", "number three", "number four", "number five",
                                  "number six", "number seven", "let's bring all seven")] + [DUR + 1]
for i in range(len(bounds) - 1):
    plan["avatar"].append({"s": bounds[i] - 0.1 if i else 0, "e": bounds[i + 1] - 0.1, "id": [2, 1, 3][i % 3]})

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
