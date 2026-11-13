"""The AI writer: outline → narration → visual plan, plus titles, upload pack and persona."""
import random
import re
from concurrent.futures import ThreadPoolExecutor

from . import catalog, core, llm

BANNED = ("delve, tapestry, testament, realm, unlock, unleash, elevate, embark, harness, leverage, robust, seamless, crucial, "
          "pivotal, game-changer, in today's fast-paced world, let's dive in, buckle up, without further ado, picture this, "
          "here's the kicker, it's worth noting, in conclusion, at the end of the day, moreover, furthermore, plethora, myriad, "
          "nestled, boasts, vibrant, meticulous, mind-blowing, you won't believe")

BASE_RULES = """You write narration for YouTube videos. It will be read aloud by a voice, so write for the ear.
Rules:
- Output ONLY the words that are spoken. No headings, labels, stage directions, brackets, emojis, lists or markdown.
- Flowing spoken sentences of mixed length. Never strings of tiny fragments like "Simple. Cheap. Fast."
- No em dashes, no semicolons, no parentheses. Write symbols as words ("percent", "dollars", "degrees").
- Concrete details over vague claims. Never invent quotes, statistics, studies or dates. If you are not sure of a number, describe it without one.
- Never use these words or phrases: """ + BANNED + """.
- No brand names. No medical, legal or investment advice."""

FORMAT_RULES = {
    "documentary": "Style: cinematic documentary. Calm, precise third person, present or past tense. Open inside the most dramatic moment with an exact time or place, then rewind. Build curiosity with open questions and answer each one later. Use exact times, dates, distances.",
    "history": "Style: history documentary. Measured, respectful, vivid sensory detail of the period. Anchor every section with a year or date and a place. Explain why each event mattered.",
    "truecrime": "Style: true crime. Careful, factual, respectful to victims. Build a timeline, raise questions investigators faced, reveal answers in order. Never sensationalise gore.",
    "last24": "Style: 'the final 24 hours'. Reconstruct one day minute by minute using clock times. Each section starts by stating the time. Slow, inevitable tension, respectful tone.",
    "explainer": "Style: explainer. Friendly, direct second person ('you'). One question drives the video. Use everyday analogies, step by step, each step answering 'why'.",
    "avatar": "Style: a warm older host talking straight to camera across a kitchen table, first person. Open inside a scene of the viewer's own frustration, absolve them ('it was never your fault'), promise the old way that works, tease the best secret for the end. Teach the WHY behind every trick in plain words. Dry, gentle, personal humor, short family stories. Every method must be correct and safe for a normal home, with the real safety warning where it applies. One mid-video ask phrased as a small favor. End with one small homework and a question for the comments.",
    "anim2d": "Style: animated story told in second person ('you') with one or two named characters. Simple, visual, emotional beats. Each sentence should describe something a stick-figure character can act out.",
    "listicle": "Style: countdown list. Number every item, count down to number one, tease number one early, one surprising fact per item, quick bridges between items.",
    "science": "Style: science documentary. Wonder first, then mechanism. Use scale comparisons a viewer can feel. Be exact about what is known and what is uncertain.",
    "whatif": "Style: 'what if' scenario in second person. Escalate hour by hour or day by day. Each step follows logically from the last with the real science behind it.",
    "biography": "Style: biography. Start with the defining moment, then tell the life in order. Specific years, places, turning points. Human, not worshipful.",
    "finance": "Style: business story. Stakes in money and people. Explain every number in plain words. No investment advice.",
    "tech": "Style: tech explainer. Crisp, confident, slightly wry. What it is, how it works, why it matters, what could go wrong.",
    "mystery": "Style: slow-burn mystery. Quiet dread, precise details, long pauses implied by short paragraphs. Separate what is documented from what is rumor.",
    "nature": "Style: nature and travel film. Patient, observational, sensory. Let places and animals be the characters.",
    "motivation": "Style: motivational speech. Second person, rhythm and repetition used sparingly, one story as the spine, a clear call to act today.",
    "news": "Style: news report. Who, what, when, where first. Neutral, sourced phrasing ('according to'). Short paragraphs.",
    "casestudy": "Style: case study. Pose the puzzle, walk through the evidence like notes in a notebook, land on the lesson.",
    "kids": "Style: children's story. Very simple words, short warm sentences, a small hero, a gentle lesson, a little repetition.",
    "sports": "Style: sports story. The moment, the stakes, the career behind it. Exact scores and years only when certain.",
    "typography": "Style: punchy essay. Short strong statements that work as on-screen text, one idea per sentence.",
    "shorts": "Style: vertical short. Hook in the first five words. One idea. No intro, no outro, end on the payoff.",
}


def wpm(fmt):
    return 140 if fmt == "avatar" else 150


def lang_line(lang):
    if lang == "hinglish":
        return "Write in Hinglish: conversational Hindi written in Latin letters with natural English words mixed in."
    return "Write in %s." % catalog.LANG_NAME.get(lang, "English")


def research(topic):
    """Best-effort background facts. Quietly returns '' when the source is unreachable."""
    try:
        r = core.fetch("https://en.wikipedia.org/w/api.php", timeout=10, retries=0, params={
            "action": "query", "format": "json", "generator": "search", "gsrsearch": topic, "gsrlimit": 2,
            "prop": "extracts", "exintro": 1, "explaintext": 1, "exchars": 1500})
        pages = (r.json().get("query") or {}).get("pages") or {}
        return "\n\n".join("%s: %s" % (p.get("title"), p.get("extract", "")) for p in pages.values())[:3200]
    except Exception:
        return ""


def outline(brief, fmt, lang, minutes, style_note=""):
    total = int(minutes * wpm(fmt))
    n = max(1, min(40, round(minutes / 1.4)))
    if minutes <= 1.5:
        n = 1
    facts = research(brief[:120])
    sys = ("You plan YouTube videos that hold attention to the end. " + FORMAT_RULES.get(fmt, FORMAT_RULES["documentary"]))
    user = """Plan a video.
BRIEF: %s
%s%s
Total narration: about %d words, in %d chapters. %s
Return JSON: {"title": "final video title under 70 characters", "logline": "one sentence promise of the video",
"big_loop": "the question opened in the first 20 seconds and answered at the end",
"chapters": [{"title": "2-5 word chapter title", "summary": "what this chapter covers, 2 sentences, with its concrete facts", "words": 200}]}
Chapter 1 is the cold open and hook. The last chapter pays off the big loop and ends cleanly. Chapter word counts must add up to about %d.""" % (
        brief[:6000], ("BACKGROUND FACTS (use only if relevant):\n" + facts + "\n") if facts else "",
        ("SCRIPT STYLE TO FOLLOW: " + style_note + "\n") if style_note else "", total, n, lang_line(lang), total)
    try:
        o = llm.chat_json(sys, user, max_tokens=3500)
        ch = [c for c in (o.get("chapters") or []) if isinstance(c, dict) and c.get("title")]
        if not ch:
            raise ValueError("no chapters")
    except Exception:
        o = {"title": brief[:68], "logline": brief[:140], "big_loop": "", "chapters": []}
        ch = [{"title": "Part %d" % (i + 1), "summary": brief[:300], "words": total // n} for i in range(n)]
    s = sum(max(40, int(c.get("words") or 0)) for c in ch) or 1
    for c in ch:
        c["words"] = max(45, int(max(40, int(c.get("words") or 0)) * total / s))
    o["chapters"] = ch
    o["title"] = (o.get("title") or brief)[:100]
    o["facts"] = facts
    return o


def clean_narration(t):
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"^\s*(#+|\*\*|chapter\s+\d+[:.]?|narrator:|voiceover:|\[.*?\]).*$", lambda m: "" if len(m.group(0)) < 60 else m.group(0), t, flags=re.I | re.M)
    t = re.sub(r"\[[^\]]{0,80}\]|\([^)]{0,80}\)", " ", t)
    t = t.replace("\u2011", "-").replace("\u2010", "-").replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    t = t.replace("—", ", ").replace("–", ", ").replace(";", ",").replace("*", "").replace("#", "")
    t = re.sub(r"\s+", " ", t).strip().strip('"')
    return t


def write_chapter(o, i, fmt, lang, style_note, persona, prev_tail=""):
    ch = o["chapters"][i]
    n = len(o["chapters"])
    pos = "This is the OPENING chapter: start inside the scene, no greeting, hook in the first two sentences, open the big question." if i == 0 else (
        "This is the FINAL chapter: answer the big question, give a short human closing thought and a clean last line." if i == n - 1 else
        "This is a middle chapter: continue straight on, no recap, no greeting, end with a line that pulls into the next chapter.")
    sys = BASE_RULES + "\n" + FORMAT_RULES.get(fmt, FORMAT_RULES["documentary"]) + "\n" + lang_line(lang)
    if persona:
        sys += "\nHOST PERSONA (stay in this voice, first person): " + persona[:2500]
    if style_note:
        sys += "\nSCRIPT STYLE TO FOLLOW: " + style_note[:800]
    user = """VIDEO: %s
PROMISE: %s
BIG QUESTION: %s
ALL CHAPTERS: %s
%s
Write chapter %d of %d: "%s".
It covers: %s
%s
Length: about %d words. Output only the spoken narration.""" % (
        o["title"], o.get("logline", ""), o.get("big_loop", ""), " | ".join(c["title"] for c in o["chapters"]),
        ("FACTS: " + o["facts"][:1800]) if o.get("facts") else "", i + 1, n, ch["title"], ch.get("summary", ""), pos, ch["words"])
    if prev_tail:
        user += "\nThe previous chapter ended with: \"%s\"" % prev_tail
    txt = clean_narration(llm.chat(sys, user, max_tokens=int(ch["words"] * 2.4) + 500, temperature=0.85))
    words = core.words_of(txt)
    if len(words) > ch["words"] * 1.35:  # trim runaway chapters at a sentence end
        keep, count = [], 0
        for s in core.sentences(txt):
            count += len(core.words_of(s))
            keep.append(s)
            if count >= ch["words"] * 1.15:
                break
        txt = " ".join(keep)
    return txt


MG_DOC = """Motion graphic types and the data each needs (use ONLY facts stated in the narration):
title {"text","sub"} · stat {"value":number,"prefix","suffix","label"} · timeline {"events":[{"t":"6:30","label"}]} (2-5 events)
bar_chart {"title","unit","items":[{"label","value":number}]} · compare {"a":{"label","value"},"b":{"label","value"},"unit"}
line_chart {"title","unit","points":[{"x":"1990","y":number}]} · ring {"value":0-100,"label"}
world_map {"place","lat":number,"lon":number,"label"} · route_map {"label","points":[{"name","lat","lon"}]} (2-4 points)
quote {"text","by"} · list {"title","items":["..."]} (2-5) · clock {"time":"9:06 AM","date","place"}
keywords {"words":["..."]} (2-4 strong words) · icon_grid {"items":["..."]} (3-6) · character_card {"name","role","facts":["..."]}
document {"title","lines":["..."],"stamp":"CLASSIFIED"} · counter {"value","label"} · diagram {"center","parts":["..."]} (3-6)
callout {"label"} (a circle and arrow drawn over the picture)"""


def plan_visuals(o, i, text, fmt, allowed_mg, look_hint, seed, sents=None):
    """Per-sentence visual plan. Always returns one dict per sentence (heuristic fallback)."""
    sents = sents or core.sentences(text)
    numbered = "\n".join("%d. %s" % (k + 1, s) for k, s in enumerate(sents))
    sys = "You are a film editor choosing the picture for every line of narration. Different lines must get clearly different pictures."
    anim = fmt in ("anim2d", "kids", "whatif")
    extra = ""
    if anim:
        extra = ('\nAlso give "cast": 1-2 stick-figure characters acting the line, each {"pose": one of stand|walk|run|point|think|shock|sit|cheer|sad|talk|fall|carry|look_up, '
                 '"expr": one of neutral|happy|shock|sad|angry|fear|think}, and "bubble": optional 1-3 word thought or speech.')
    user = """VIDEO: %s (%s look)
NARRATION LINES:
%s

For EVERY line return an item: {"n": line number, "kind": "stock" | "archive" | "ai" | "mg",
"query": "2-4 plain words to search stock footage, concrete nouns only",
"query2": "a different 2-4 word search for a second shot",
"prompt": "one detailed sentence describing a photorealistic image for this line: subject, action, setting, light, camera framing. No text in the image.",
"emotion": "calm|tense|sad|excited|warm|mystery", "sfx": "none|whoosh|hit|riser|tick|click|pop|rumble|shutter|typing|heartbeat|water|wind",
"key": "1-3 word on-screen keyword or empty", "mg": null or {"type": ..., ...data}}%s
Use "archive" for real historical people, events and places; "stock" for generic real-world footage; "ai" when no real footage could exist; "mg" when a number, date, place, comparison, list or quote is the point.
About one line in %d should be "mg". Allowed mg types: %s.
%s
Return JSON: {"items": [...]}""" % (
        o["title"], look_hint, numbered, extra, 5 if fmt != "typography" else 2, ", ".join(allowed_mg) or "title, keywords", MG_DOC)
    items = {}
    try:
        j = llm.chat_json(sys, user, max_tokens=min(7000, 400 + 260 * len(sents)), temperature=0.6, tries=2)
        arr = j.get("items") if isinstance(j, dict) else j
        for it in arr or []:
            if isinstance(it, dict) and str(it.get("n", "")).isdigit():
                items[int(it["n"]) - 1] = it
    except Exception:
        pass
    rnd = random.Random(seed + i * 977)
    out = []
    for k, s in enumerate(sents):
        it = items.get(k) or {}
        kw = keywords(s)
        q = (it.get("query") or " ".join(kw[:3]) or o["title"])[:60]
        plan = {
            "text": s, "kind": it.get("kind") if it.get("kind") in ("stock", "archive", "ai", "mg") else rnd.choice(["stock", "ai", "ai", "archive"]),
            "query": q, "query2": (it.get("query2") or " ".join(kw[1:4]) or q)[:60],
            "prompt": (it.get("prompt") or s)[:420], "emotion": it.get("emotion") or "calm",
            "sfx": it.get("sfx") or "none", "key": (it.get("key") or "")[:28],
            "mg": it.get("mg") if isinstance(it.get("mg"), dict) and it["mg"].get("type") else None,
            "cast": it.get("cast") if isinstance(it.get("cast"), list) else None, "bubble": (it.get("bubble") or "")[:24],
        }
        if plan["mg"] and allowed_mg and plan["mg"]["type"] not in allowed_mg:
            plan["mg"] = None
        if plan["kind"] == "mg" and not plan["mg"]:
            plan["kind"] = "ai"
        out.append(plan)
    return out


STOP = set("the a an and or but so because of to in on at for with from by as is are was were be been it its this that these those you your he she they them his her their we our i my me not no yes do does did have has had will would can could should than then there here what when where why how who which into over under about after before again just very more most much many some any each every all also only even still".split())


def keywords(s):
    ws = [w.strip(".,!?\"'()[]:;").lower() for w in s.split()]
    ws = [w for w in ws if len(w) > 3 and w not in STOP and w.isascii()]
    return sorted(set(ws), key=lambda w: -len(w))[:5]


def write_script(p, progress=lambda f, m: None):
    """Fills p['outline'] and p['beats'] (list of per-sentence plans with chapter index)."""
    st = p["settings"]
    fmt, lang, minutes = st["format"], st["language"], float(st["duration_min"])
    style_note = (p.get("brand") or {}).get("script_style", "")
    persona = (p.get("persona") or {}).get("bible", "") if fmt == "avatar" else ""
    seed = p["seed"]
    if p.get("own_script"):
        txt = clean_narration(p["own_script"])
        sents = core.sentences(txt)
        per = max(6, min(14, len(sents) // max(1, round(len(core.words_of(txt)) / 220)) or 8))
        groups = [sents[k:k + per] for k in range(0, len(sents), per)]
        o = {"title": p["title"], "logline": "", "big_loop": "", "facts": "",
             "chapters": [{"title": "Part %d" % (k + 1), "summary": "", "words": len(core.words_of(" ".join(g)))} for k, g in enumerate(groups)]}
        texts = [" ".join(g) for g in groups]
    else:
        progress(0.02, "Planning the story")
        o = outline(p["prompt"] or p["title"], fmt, lang, minutes, style_note)
        if p.get("title_locked"):
            o["title"] = p["title"]
        n = len(o["chapters"])
        texts = [None] * n
        texts[0] = write_chapter(o, 0, fmt, lang, style_note, persona)
        progress(0.1, "Writing chapter 1 of %d" % n)
        done = [1]

        def job(i):
            texts[i] = write_chapter(o, i, fmt, lang, style_note, persona)
            done[0] += 1
            progress(0.1 + 0.4 * done[0] / n, "Writing chapter %d of %d" % (done[0], n))
        with ThreadPoolExecutor(3) as ex:
            list(ex.map(job, range(1, n)))
    p["outline"] = {k: o.get(k) for k in ("title", "logline", "big_loop", "chapters")}
    theme = catalog.THEMES[st["theme"]]["name"]
    allowed = st.get("motion_graphics") or []
    beats = [None] * len(texts)
    done = [0]

    def vjob(i):
        beats[i] = plan_visuals(o, i, texts[i], fmt, allowed, theme, seed)
        done[0] += 1
        progress(0.5 + 0.5 * done[0] / len(texts), "Storyboarding chapter %d of %d" % (done[0], len(texts)))
    with ThreadPoolExecutor(3) as ex:
        list(ex.map(vjob, range(len(texts))))
    flat = []
    for i, bs in enumerate(beats):
        for b in bs:
            b["chapter"] = i
            flat.append(b)
    p["beats"] = flat
    if not p.get("title_locked"):
        p["title"] = o["title"]
    return p


# ------------------------------------------------------------------ titles / pack / persona / style
TITLE_FORMULAS = [
    "Most People Are [Doing X] Wrong. Try This [Angle] Trick Instead", "Stop [Doing] [X]! Do This Instead",
    "What Actually Happens When You [Common Action]", "The $[Small Price] [Thing] That [Big Result]",
    "[Number] Things [Group] Never [Do] (And Why)", "Why Your [Thing] [Problem] — Do This Instead",
    "The Untold Timeline of [Person]'s Last Day", "They Found [Thing] in [Place] — And No One Went Back",
    "What [Organization] Found on [Object] [Time Before Event]", "What If [Impossible Scenario]?",
    "[Time] : The Minute Everything Changed", "How [Small Thing] Destroyed [Big Thing]",
]


def gen_titles(topic, fmt="documentary", lang="en", n=10, reference=""):
    sys = "You are a YouTube packaging specialist. You write titles with one strong curiosity gap that the video can honestly deliver."
    user = """Topic: %s
Format: %s. %s
%s
Proven formulas for inspiration (adapt, never copy an existing video's exact title): %s
Write %d title options. Each under 70 characters, at most one ALL-CAPS word, no emojis, no clickbait the video cannot deliver.
Return JSON: {"titles": [{"title": "...", "angle": "which emotion or curiosity gap it uses, 6 words", "score": 1-100 click potential}]}""" % (
        topic[:1500], catalog.FORMATS.get(fmt, {}).get("name", fmt), lang_line(lang),
        ("Reference video title to learn the style from: " + reference) if reference else "", " | ".join(TITLE_FORMULAS), n)
    j = llm.chat_json(sys, user, max_tokens=1800, temperature=0.95)
    arr = j.get("titles") if isinstance(j, dict) else j
    out = []
    for t in arr or []:
        if isinstance(t, str):
            t = {"title": t}
        if isinstance(t, dict) and t.get("title"):
            out.append({"title": str(t["title"])[:100], "angle": str(t.get("angle", "")), "score": int(t.get("score") or 70) if str(t.get("score", "")).isdigit() else 70})
    return sorted(out, key=lambda x: -x["score"])


def gen_pack(p):
    """Titles, description with real chapter timestamps, tags, hashtags and pinned comment."""
    chapters = []
    for c in p.get("chapters_time", []):
        chapters.append("%s %s" % (core.fmt_time(c["t"]), c["title"]))
    if chapters and not chapters[0].startswith("0:00"):
        chapters.insert(0, "0:00 Intro")
    script = " ".join(b["text"] for b in p.get("beats", []))[:5000]
    sys = "You are a YouTube packaging specialist. Honest, searchable, human."
    user = """Video title: %s
Format: %s. %s
Script excerpt: %s
Return JSON: {"titles": [6 alternative titles under 70 characters],
"description_intro": "two punchy lines restating the problem and payoff with the main search phrase, then one warm paragraph of what the viewer learns",
"tags": [20-30 search tags, most important first, no brands],
"hashtags": [8 hashtags without spaces, most important first],
"pinned_comment": "2-4 sentences: a thank-you, one bonus detail not in the video, one easy question",
"thumbnail_texts": [4 options of 2-4 words that ADD to the title]}""" % (p["title"], p["settings"]["format"], lang_line(p["settings"]["language"]), script)
    try:
        j = llm.chat_json(sys, user, max_tokens=2200)
    except Exception:
        j = {}
    tags = [str(t) for t in (j.get("tags") or [])]
    line, total = [], 0
    for t in tags:
        if total + len(t) + 2 > 495:
            break
        line.append(t)
        total += len(t) + 2
    hashtags = ["#" + re.sub(r"[^\w]", "", str(x)) for x in (j.get("hashtags") or [])][:8]
    desc = (j.get("description_intro") or p.get("outline", {}).get("logline") or p["title"]).strip()
    if len(chapters) >= 3:
        desc += "\n\nCHAPTERS\n" + "\n".join(chapters)
    credits = sorted({s["asset"].get("credit") for s in p.get("shots", []) if s.get("asset") and s["asset"].get("credit")})
    if credits:
        desc += "\n\nVISUAL CREDITS\n" + "\n".join(credits[:40])
    if p["settings"]["format"] == "avatar":
        desc += "\n\nThe host of this video is an AI-generated character."
    desc += "\n\n" + " ".join(hashtags[:3])
    return {"titles": [str(t)[:100] for t in (j.get("titles") or [p["title"]])][:6], "description": desc, "tags": ", ".join(line),
            "hashtags": " ".join(hashtags), "pinned_comment": j.get("pinned_comment", ""),
            "thumbnail_texts": [str(t)[:30] for t in (j.get("thumbnail_texts") or [])][:4], "chapters": chapters}


def make_persona(topic, bible=""):
    sys = "You design original fictional on-camera hosts for YouTube. Never base them on a real person."
    user = """%s
Create the host for a video about: %s
Return JSON: {"name": "first and last name", "age": number, "gender": "female|male", "heritage": "culture or background, no real town names",
"one_liner": "who they are in one sentence",
"look": "face, hair, glasses, jewelry and clothing only, with one signature clothing color, 30-45 words",
"set": "the room they film in, 15-25 words", "sign_off": "their closing line", "voice_age": "old|middle|young"}""" % (
        ("PERSONA BIBLE (extract from this, do not invent a different person):\n" + bible[:5000]) if bible else
        "The host has built-in authority from age and background (a grandmother, grandfather, farmer, craftsman, retired engineer, sailor...).", topic[:600])
    try:
        j = llm.chat_json(sys, user, max_tokens=900)
    except Exception:
        j = {}
    j.setdefault("name", "Ruth Calloway")
    j.setdefault("age", 68)
    j.setdefault("gender", "female")
    j.setdefault("look", "silver hair in a loose bun, round wire glasses, soft lined face, kind eyes, small pearl earrings, a teal cardigan over a cream blouse")
    j.setdefault("set", "a lived-in farmhouse kitchen with open shelves, a kettle, herbs on the windowsill and soft window daylight")
    j.setdefault("sign_off", "Take care of your home, and it will take care of you.")
    j["bible"] = bible or "%s, %s, %s. %s Signature sign-off: %s" % (j["name"], j["age"], j.get("heritage", ""), j.get("one_liner", ""), j["sign_off"])
    return j


def analyze_reference(url):
    """Learn a script/editing style from a reference video's public metadata."""
    info = {"url": url}
    try:
        r = core.fetch("https://www.youtube.com/oembed", params={"url": url, "format": "json"}, timeout=15)
        j = r.json()
        info.update(title=j.get("title"), channel=j.get("author_name"), thumb=j.get("thumbnail_url"))
    except Exception:
        pass
    if not info.get("title"):
        info["error"] = "Could not read that link. Paste a YouTube video URL."
        return info
    sys = "You are a YouTube strategist who reverse-engineers how successful videos are written and edited."
    user = """Reference video: "%s" by %s.
Infer the likely style of this video from its title, niche and channel. Return JSON:
{"summary": "2 sentences on the format", "mood": "3 words", "voice_and_tone": "how the narrator speaks", "structure": "how the video is ordered",
"hook_pattern": "how it likely opens", "title_formula": "the title rewritten as a reusable [bracket] formula",
"editing": "pace, visuals, graphics an editor would use", "suggested_format": one of %s}""" % (info["title"], info.get("channel", ""), list(catalog.FORMATS))
    try:
        info["style"] = llm.chat_json(sys, user, max_tokens=900)
        s = info["style"]
        info["script_style"] = "%s Tone: %s Structure: %s Hook: %s" % (s.get("summary", ""), s.get("voice_and_tone", ""), s.get("structure", ""), s.get("hook_pattern", ""))
    except Exception as e:
        info["error"] = str(e)
    return info
