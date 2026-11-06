"""Build captions_en.srt from transcript.json, fixing words the speech model misheard."""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = [
    (r"\bknew a fitness\b", "to a fitness"), (r"\bair lines?\b", "airlines"), (r"\bband it\b", "banned it"),
    (r"\bsam ?sung'?s\b", "Samsung's"), (r"\b(samson|samsong|sam sung)\b", "Samsung"), (r"\bteck\b", "tech"),
    (r"\btwenty, sixteenth\b", "2016"), (r"\btwenty sixteenth\b", "2016"), (r"\birish scanner\b", "iris scanner"),
    (r"\bviewers called\b", "reviewers called"), (r"\bbones were\b", "phones were"), (r"\blunch\b", "launch"),
    (r"\bwhirled wide\b", "worldwide"), (r"\bon line\b", "online"), (r"\bplain\b", "plane"),
    (r"\bairline's\b", "Airlines"), (r"\bu s government bandit\b", "the U.S. government banned it"),
    (r"\blitheamion\b", "lithium-ion"), (r"\blythium ion sell\b", "lithium-ion cell"), (r"\bthermal run away\b", "thermal runaway"),
    (r"\bwho different\b", "two different"), (r"\beyephone\b", "iPhone"), (r"\brighting\b", "riding"),
    (r"\bweb side\b", "website"), (r"\bu\. k\b", "U.K."), (r"\bbann them\b", "banned them"), (r"\bnsylvania\b", "Pennsylvania"),
    (r"\bhover boards\b", "hoverboards"), (r"\bhover board\b", "hoverboard"),
    (r"\bsays you well twenty seven two\b", "says UL 2272"), (r"\bdull lap top\b", "Dell laptop"),
    (r"\blap top\b", "laptop"), (r"\blinovo\b", "Lenovo"), (r"\bhe sat there\b", "they sat there"),
    (r"\bshored out\b", "short out"), (r"\bcenser\b", "sensor"), (r"\bfitbits\b", "Fitbit's"),
    (r"^bit announced", "Fitbit announced"), (r"\bbut told people\b", "Fitbit told people"),
    (r"\bp c fine googall\b", "CPSC fined Google"), (r"\bvitio\b", "video"), (r"\bor talking\b", "we're talking"),
    (r"\bbetting\b", "bedding"), (r"\b(pellaton|pelaton|pellan)\b", "Peloton"), (r"\bpelaton's\b", "Peloton's"),
    (r"\bse eux\b", "its CEO"), (r"^company reversed", "the company reversed"), (r"^called the warning", "it called the warning"),
    (r"\bas his bucky balls\b", "this is Buckyballs"), (r"\bkid saw\b", "kids saw"), (r"\btea majors\b", "teenagers"),
    (r"\bat seyo\b", "its CEO"), (r"\bsails\b", "sales"), (r"\bcord\b", "court"), (r"\bends upholding\b", "ends up holding"),
    (r"\bin the number\b", "and the number"), (r"\b(hustledan|asseldon)\b", "Heselden"), (r"\bjimmy\b", "Jimi"),
    (r"\b(saguay|sagua)\b", "Segway"), (r"^the company that made", "bought the company that made"),
    (r"\bschooner\b", "scooter"), (r"\bhouse cities were\b", "how cities work"), (r"\bhiped\b", "hyped"),
    (r"\bwriting a\b", "riding a"), (r"\banchor\b", "Anker"), (r"^and called over", "recalled over"),
    (r"^our banks", "power banks"), (r"\baeroplanes\b", "airplanes"), (r"\bintact\b", "in tech"), (r"\bcost it\b", "costs it"),
    (r"\bstarted adding a\b", "started adding up"), (r"\bdesigned problem\b", "design problem"),
    (r"\bfrom a phone\b", "From a phone"), (r"^this is (.*)$", r"This is \1"),
    (r"\bgps\b", "GPS"), (r"\bamazon\b", "Amazon"), (r"\bapple\b", "Apple"), (r"\bsony\b", "Sony"),
    (r"\bfitbit\b", "Fitbit"), (r"\bgoogle\b", "Google"), (r"\bflorida\b", "Florida"), (r"\bjeep\b", "Jeep"),
    (r"\bsouthwest\b", "Southwest"), (r"\blouisville\b", "Louisville"), (r"\bjapan\b", "Japan"), (r"\bchina\b", "China"),
    (r"\bharrisburg\b", "Harrisburg"), (r"\byorkshire\b", "Yorkshire"), (r"\bamerica\b", "America"),
    (r"\bbritish\b", "British"), (r"\bdell\b", "Dell"), (r"\bnote seven\b", "Note 7"), (r"\bgalaxy\b", "Galaxy"),
    (r"\bu s\b", "U.S."), (r"\bi'll\b", "I'll"), (r"\bi\b", "I"),
    (r"\b(august|september|october|december|march|july|april)\b", lambda m: m.group(1).capitalize()),
]


def fix(text):
    for pat, rep in FIX:
        text = re.sub(pat, rep, text, flags=re.I if not callable(rep) else re.I)
    return text


def ts(x):
    h, r = divmod(x, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}"


cues = []
for seg in json.load(open(os.path.join(HERE, "transcript.json"))):
    cur = []
    for w in seg["words"]:
        cur.append(w)
        txt = " ".join(x["w"] for x in cur)
        if len(txt) > 70 or (w["w"][-1:] in ".?!," and len(txt) > 38):
            cues.append(cur)
            cur = []
    if cur:
        if cues and len(" ".join(x["w"] for x in cur)) < 12 and cur[0]["s"] - cues[-1][-1]["e"] < 0.3:
            cues[-1] += cur
        else:
            cues.append(cur)

out = []
prev_end = "."
for i, cue in enumerate(cues, 1):
    text = fix(" ".join(x["w"] for x in cue)).strip()
    if prev_end in ".?!":
        text = text[0].upper() + text[1:]
    prev_end = text[-1]
    text = re.sub(r"([.?!] )([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
    if len(text) > 42:  # two lines
        words = text.split()
        best = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - len(text) / 2))
        text = " ".join(words[:best]) + "\n" + " ".join(words[best:])
    end = cue[-1]["e"]
    if i < len(cues):
        end = min(end + 0.3, cues[i][0]["s"] - 0.02)
    out.append(f"{i}\n{ts(cue[0]['s'])} --> {ts(end)}\n{text}\n")
open(os.path.join(HERE, "captions_en.srt"), "w").write("\n".join(out))
print(len(out), "cues")
