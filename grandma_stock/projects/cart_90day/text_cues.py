"""Text cues for the 90-day grocery cart video. Times = original voiceover seconds."""
# helpers (big, words, lower, item, count, panel, warn, subscribe, add, sfx) come from lib/vtext.py

# ============================== PART 1 ==============================
big(0.15, 1.85, "IMAGINE THE [POWER] GOES OUT", y=540)
words(2.55, 4.40, "NOT HOURS… [90 DAYS]", y=540, gap=0.5)
words(4.85, 6.95, "NO LIGHTS • NO STOVE • NO FRIDGE", y=880, gap=0.35, style="Big")
lower(7.05, 9.10, "Stores: [no deliveries]")
big(9.30, 10.85, "WOULD YOUR FAMILY EAT [TOMORROW]?", y=540)
count(11.0, 13.3, 90, prefix="DAY ", dur=1.2, y=520, label="Would they still be eating?")

lower(13.6, 16.2, "Hello, I'm [Kaja]")
lower(16.5, 19.9, "\"[Mummo]\" = Finnish for Grandmother")
words(20.3, 24.9, "STAY [WARM] • [FED] • [CALM]", y=900, gap=0.6)
subscribe(25.1, 30.9)

add(31.1, 35.4, "Tag", "{\\an7\\move(-500,110,110,110,0,250)\\fad(0,250)}TODAY'S PLAN", 5)
add(31.4, 35.4, "Item", "{\\an7\\pos(110,190)\\fad(200,250)}THE [90-DAY] GROCERY CART", 5)
add(33.5, 35.4, "Info", "{\\an7\\move(118,400,118,370,0,250)\\fad(200,250)}Family of [4] • No power", 5)
sfx += [(31.1, "whoosh", -12), (31.4, "hit", -13), (33.5, "pop", -17)]
lower(35.7, 37.9, "To get through [90 days] without power")
words(38.2, 42.4, "NOT FANCY • NOT A [$$$] BUCKET", y=540, gap=0.45)
lower(42.8, 46.9, "Ordinary groceries • amounts that [add up]")
panel(47.2, 51.8, 110, 560, 800, [(47.4, "✔ [WHAT] goes in"), (49.5, "✔ [HOW MUCH]"), (50.6, "✔ And [WHY]")], 0)

lower(52.1, 55.1, "Grew up with wood heat in [Lake Country]")
lower(55.4, 59.6, "Storms took the power down [almost every year]")
lower(59.9, 62.5, "Mother's pantry [never ran empty]")
big(62.8, 64.8, "SHE NEVER [PANICKED]", y=880)
words(65.0, 67.9, "PANIC = [NO PLAN]", y=540, gap=0.35)

add(68.2, 70.8, "Tag", "{\\an7\\move(-500,110,110,110,0,250)\\fad(0,250)}MUMMO'S RULES", 5)
sfx.append((68.2, "whoosh", -12))
panel(70.9, 88.0, 110, 220, 1150,
      [(71.0, "1. Keeps [without a fridge]"), (74.2, "2. [Cheap] & easy to find"),
       (76.4, "3. Food your family [already eats]"), (82.3, "4. Gives [enough calories]")], 0,
      title="SHOPPING RULES")

big(88.2, 89.75, "LET'S DO THE [MATH]", y=540)
lower(89.9, 94.0, "[2,000] calories × [4] people")
count(94.3, 97.1, 8000, suffix=" CAL/DAY", dur=1.0, y=540)
words(97.3, 99.2, "8,000 × [90 DAYS] =", y=380, gap=0.35)
count(99.3, 101.6, 720000, dur=1.2, y=560, label="CALORIES")
big(101.8, 104.0, "OUR [TARGET]", y=880)
sfx.append((101.8, "ding", -12))
lower(104.3, 108.7, "Teenagers eat [more] • little ones eat [less]")
lower(109.0, 115.3, "Special diets? [Ask your doctor]")

big(115.5, 117.8, "NOW… [THE CART]", y=540)
# ---- Item 1 rice
item(118.0, 126.2, 1, "WHITE [RICE]", "[100 LBS]")
lower(122.4, 126.2, "≈ [1,600] calories per pound")
count(126.5, 130.3, 160000, dur=1.2, y=850, style="Huge", label=None)
lower(130.5, 133.7, "More than [1/5] of the target — [one item]")
words(133.9, 135.6, "WHITE vs [BROWN]?", y=540, gap=0.35)
lower(135.8, 138.7, "Brown rice oils go [stale faster]")
lower(138.9, 142.7, "White rice, dry & sealed: [lasts years]")
panel(142.9, 148.7, 110, 560, 950, [(143.0, "✔ [Airtight] food-safe"), (144.9, "✔ [Tight lids]"), (146.0, "✔ Cool, dry, [off the floor]")], 0)
lower(148.9, 152.0, "Keeps out the [mice]")

# ---- Item 2 beans
item(152.2, 161.0, 2, "BEANS & [LENTILS]", "[60 LBS]")
words(157.0, 161.0, "PINTO • BLACK • [LENTILS]", y=920, gap=0.45)
lower(161.3, 164.7, "≈ [1,500] calories per pound")
count(164.9, 169.8, 90000, dur=1.2, y=520, label="+ PROTEIN & FIBER")
words(170.2, 177.9, "RICE + BEANS = [COMPLETE PROTEIN]", y=900, gap=0.35)
lower(178.4, 183.9, "Lentils: [no soaking] • cook faster • [less fuel]")
big(184.1, 186.9, "BUY [MORE LENTILS]", y=540)
lower(187.1, 192.1, "Eat your [oldest beans] first")
words(192.3, 196.9, "USE SOME • [REPLACE SOME]", y=540, gap=0.5)

# ---- Item 3 oats
item(197.1, 204.0, 3, "ROLLED [OATS]", "[40 LBS] • old fashioned")
lower(201.8, 204.6, "≈ [1,700] calories per pound")
count(204.9, 208.0, 68000, dur=1.1, y=560)
words(208.3, 212.7, "NOT JUST FOOD — [MORALE]", y=900, gap=0.4)
lower(212.9, 218.9, "Hot water + oats = [ready in minutes]")

big(219.1, 220.8, "LET'S [ADD IT UP]", y=200)
panel(220.9, 232.2, 110, 330, 1000,
      [(220.9, "Rice ........... [160,000]"), (222.9, "Beans/Lentils .. [90,000]"),
       (225.1, "Oats ............ [68,000]"), (226.7, "TOTAL ......... [318,000]")], 0)
lower(230.4, 232.2, "A little [under half] of the target")
count(232.5, 237.8, 400000, prefix="≈ ", dur=1.3, y=500, label="STILL TO GO")
words(238.0, 244.4, "FATS • PROTEIN • CANS • [SALT] • [FLAVOR]", y=900, gap=0.35)

lower(244.7, 251.5, "Rice, beans & oats need [water] + [a way to cook]")
big(251.8, 257.0, "COOKING WITH [NO STOVE]", y=880)
lower(257.2, 260.3, "Very little fuel — [safely]")
lower(260.5, 263.1, "Water gets [its own video]")
warn(263.4, 272.3, "⚠ NEVER INDOORS: CHARCOAL • CAMP STOVE • GENERATOR")
big(272.5, 275.5, "CARBON MONOXIDE HAS [NO SMELL]", y=880)
lower(276.2, 278.5, "Cook only with [plenty of fresh air]")
big(278.7, 282.6, "DON'T [PANIC-BUY]", y=540)
panel(283.3, 292.8, 110, 560, 1050, [(283.3, "1. Start with [2 weeks] of food"), (285.3, "2. Add [a little] every trip"), (287.5, "3. A full pantry in [a few months]")], 0)
words(293.0, 298.2, "[RICE] • [BEANS & LENTILS] • [OATS]", y=540, gap=0.6)

add(298.4, 309.5, "Tag", "{\\an7\\move(-500,110,110,110,0,250)\\fad(0,250)}COMING IN PART 2", 5)
sfx.append((298.4, "whoosh", -12))
panel(300.0, 309.5, 110, 220, 1100, [(300.5, "• Fats for [energy]"), (302.4, "• Protein to keep [strong]"),
                                    (304.5, "• Cheap [flavors]"), (307.3, "• Cooking [without a stove]")], 0)
big(309.7, 313.7, "STAY WITH ME", y=880)

# ============================== PART 2 ==============================
big(313.95, 316.2, "WELCOME BACK — [PART 2]", y=880, style="Big")
sfx.append((313.95, "hit", -10))
panel(316.4, 325.7, 110, 220, 1000, [(319.2, "✔ [100 LBS] white rice"), (321.1, "✔ [60 LBS] beans & lentils"), (323.4, "✔ [40 LBS] rolled oats")], 0,
      title="PART 1 RECAP")
count(325.9, 332.4, 318000, dur=1.2, y=520, label="A LITTLE UNDER HALF")
lower(332.6, 337.7, "Finish the cart + cook with [very little fuel]")

item(337.9, 346.3, 4, "COOKING [OIL]", "[3 GALLONS]")
lower(342.7, 346.3, "Most [concentrated energy] in your kitchen")
lower(346.6, 351.8, "≈ [30,000] calories per gallon")
count(351.9, 355.5, 92000, dur=1.1, y=520)
lower(355.7, 362.4, "Sealed • cool & dark • [oldest first]")

item(362.6, 371.3, 5, "PEANUT [BUTTER]", "[20 LBS] ≈ 53,000 cal")
lower(368.8, 376.1, "No cooking • keeps well • [a real treat]")
big(376.3, 380.9, "ALLERGY? → [SUNFLOWER SEED BUTTER]", y=880)

item(381.1, 387.0, 6, "[PASTA]", "[40 LBS] ≈ 64,000 cal")
big(387.2, 393.8, "DON'T POUR THE [PASTA WATER]", y=880)
lower(390.4, 393.8, "Drink it as broth or [reuse it]")
big(394.0, 396.2, "NOTHING IS [WASTED]", y=540)

item(396.4, 402.1, 7, "PLAIN [FLOUR]", "[25 LBS] ≈ 41,000 cal")
words(402.3, 410.2, "FLOUR + SALT + OIL = [FLATBREAD]", y=900, gap=0.35)

item(410.4, 419.3, 8, "PLAIN [CRACKERS]", "[20 LBS] ≈ 40,000 cal")
lower(415.1, 419.3, "No cooking • keep in [airtight tins]")

item(419.5, 426.2, 9, "[SUGAR]", "[20 LBS] ≈ 35,000 cal")
lower(423.7, 426.2, "+ a jar of [honey] for your tea")

item(426.4, 437.5, 10, "DRY MILK [POWDER]", "[20 LBS] ≈ 32,000 cal")
lower(431.6, 437.5, "[Calcium] + [protein] — no fridge needed")

item(437.7, 451.0, 11, "CANNED [PROTEIN]", "[60 CANS]")
words(439.8, 442.8, "TUNA • SALMON • [CHICKEN]", y=900, gap=0.45)
lower(442.9, 451.0, "≈ 8,000 cal — but [protein keeps you strong]")

item(451.2, 458.1, 12, "SOUP • VEG • [FRUIT]", "[100 CANS] ≈ 25,000 cal")
lower(458.3, 462.9, "Variety & comfort — [eat them cold] if you must")
panel(463.1, 468.0, 110, 600, 900, [(463.1, "✔ Check for [dents & rust]"), (465.8, "✔ Rotate • [oldest first]")], 0)

item(468.2, 480.2, 13, "SALT • SPICES • [TEA]", "[5 LBS] salt • keeps forever")
lower(474.2, 480.2, "A little spice turns it into [a real meal]")

big(480.4, 482.0, "THE [FINAL] TALLY", y=150)
tally = [(482.2, "Rice/Beans/Oats [318k]"), (486.0, "Oil [92k]"), (488.0, "Peanut butter [53k]"),
         (489.9, "Pasta [64k]"), (491.6, "Flour [41k]")]
tally2 = [(492.7, "Crackers [40k]"), (493.9, "Sugar [35k]"), (495.7, "Dry milk [32k]"),
          (497.3, "Canned meat/fish [8k]"), (498.9, "Soup/Veg/Fruit [25k]")]
panel(482.1, 502.2, 80, 260, 860, tally, 0)
panel(492.6, 502.2, 980, 260, 860, tally2, 0)
count(502.4, 507.6, 708000, dur=1.4, y=520, label="CALORIES")
big(507.7, 510.2, "TARGET: [720,000] ✔", y=880)
sfx.append((507.7, "ding", -11))

big(510.4, 511.5, "THAT'S [YOUR CART]", y=880)
lower(511.6, 517.8, "Prices change — [add up your own cart]")
lower(518.2, 524.7, "Compare vs a ready-made [emergency bucket]")
words(524.9, 527.0, "COOK IT ALL — [NO STOVE]", y=540, gap=0.4)
big(527.2, 531.9, "HEAT IT ONCE — LET THE [HEAT] DO THE WORK", y=880)

item(532.1, 545.7, "1", "THE [THERMOS]", "Method one", label="METHOD")
lower(533.1, 538.4, "Boil water [outdoors] → pour over oats/lentils")
lower(538.6, 545.7, "Close the lid & wait — [no more fuel]")
item(545.9, 559.4, "2", "RETAINED [HEAT POT]", "Method two", label="METHOD")
lower(548.3, 553.2, "Boil • cover • wrap in [blankets]")
lower(553.4, 559.4, "Or an [insulated cooler] for a few hours")
item(559.6, 568.9, "3", "[WOOD STOVE]", "Properly installed & maintained", label="METHOD")
warn(569.1, 576.2, "⚠ NEVER INDOORS: CHARCOAL • CAMP STOVE • GENERATOR")
lower(576.4, 581.3, "CO has [no smell] — cook with [fresh air]")
panel(581.5, 586.7, 110, 560, 1050, [(581.5, "✔ Working [CO alarm]"), (584.0, "✔ With [battery backup]")], 0)
count(586.9, 593.7, 1, prefix="", suffix=" GALLON", dur=0.4, y=520, label="PER PERSON • PER DAY")
lower(594.1, 596.5, "Water gets [its own video]")
big(596.7, 600.6, "DON'T BUY IT [ALL AT ONCE]", y=880)
panel(600.7, 607.3, 110, 560, 1150, [(600.7, "1. Start with [2 weeks]"), (602.4, "2. Add [a little] every trip"), (604.2, "3. [Eat what you store]")], 0)
subscribe(607.6, 613.0)
lower(613.3, 619.1, "NEXT: [When the water stops]")
big(619.3, 621.9, "STAY [WARM]", y=880)

# top-right part badge
add(31.0, 313.6, "Tag", "{\\an9\\pos(1810,60)\\fad(400,400)\\fs34}PART 1", 1)
add(316.4, 607.3, "Tag", "{\\an9\\pos(1810,60)\\fad(400,400)\\fs34}PART 2", 1)
