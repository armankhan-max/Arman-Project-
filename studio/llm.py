"""Script writing, scene planning, titles and metadata. Works with Claude, any OpenAI-compatible
API, the free Pollinations text endpoint, or (for pasted scripts) with no AI at all."""
import json
import re
import threading
import time

import requests

STOP = set("""a an the and or but so because if then than that this these those is are was were be been being am do does did
have has had will would can could should may might must shall of in on at to for from by with about into over under after
before between out up down off again very just not no nor only own same too also it its it's you your yours he she they them
their we our us i me my mine him her his what which who whom when where why how all any both each few more most other some
such there here one two get got like really thing things much many every still even ever never always now going know make
made way want need said says say put take let lot back well right good people time little""".split())


class LLMError(Exception):
    pass


def provider(cfg):
    p = cfg.get("llm_provider", "auto")
    if p == "auto":
        if cfg.get("anthropic_key"):
            return "anthropic"
        if cfg.get("openai_key"):
            return "openai"
        return "pollinations"
    return p


def chat(cfg, system, user, max_tokens=4000):
    p = provider(cfg)
    try:
        if p == "anthropic":
            r = requests.post("https://api.anthropic.com/v1/messages", timeout=900, headers={
                "x-api-key": cfg["anthropic_key"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": cfg.get("anthropic_model") or "claude-sonnet-5-5", "max_tokens": max_tokens,
                      "system": system, "messages": [{"role": "user", "content": user}]})
            if r.status_code != 200:
                raise LLMError(f"Claude API error {r.status_code}: {r.text[:300]}")
            return "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text")
        if p in ("openai", "pollinations"):
            if p == "openai":
                url = cfg.get("openai_base", "").rstrip("/") + "/chat/completions"
                headers = {"Authorization": "Bearer " + cfg.get("openai_key", "")}
                model = cfg.get("openai_model") or "gpt-4o-mini"
            else:
                url, model = "https://text.pollinations.ai/openai", "openai"
                headers = {"Authorization": "Bearer " + cfg["pollinations_key"]} if cfg.get("pollinations_key") else {}
            body = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
            if p == "pollinations":
                body.update(reasoning_effort="low", max_tokens=max(4000, max_tokens * 2))
            for attempt in range(5):  # free endpoints fail or rate-limit now and then; wait and try again
                if p == "pollinations" and not cfg.get("pollinations_key"):
                    _free_wait()
                r = requests.post(url, timeout=900, headers=headers, json=body)
                if r.status_code == 402 and attempt < 4:
                    m = re.search(r"[Rr]etry after (\d+)", r.text)
                    time.sleep(int(m.group(1)) + 2 if m else 46)
                    continue
                if r.status_code == 200:
                    out = r.json()["choices"][0]["message"].get("content") or ""
                    if out.strip():
                        return out
                elif r.status_code not in (400, 429, 500, 502, 503, 504) or attempt == 4:
                    raise LLMError(f"AI text API error {r.status_code}: {r.text[:300]}")
                time.sleep(3 + attempt * 5)
            raise LLMError("The AI text service returned an empty answer. Try again, or add a Claude key in Settings.")
    except requests.RequestException as e:
        raise LLMError(f"Could not reach the AI text service ({p}): {e}")
    raise LLMError("No AI text provider is set. Add a key in Settings, or paste your own script.")


_free_lock = threading.Lock()
_free_last = [0.0]


def _free_wait():
    """The free Pollinations tier allows one reply every 45 seconds per IP."""
    with _free_lock:
        wait = _free_last[0] + 46 - time.time()
        if wait > 0:
            time.sleep(wait)
        _free_last[0] = time.time()


def _json(text):
    a, b = text.find("["), text.rfind("]")
    oa, ob = text.find("{"), text.rfind("}")
    if oa != -1 and (a == -1 or oa < a):
        a, b = oa, ob
    return json.loads(text[a:b + 1])


def clean_script(text):
    text = re.sub(r"```.*?\n|```", "", text)
    text = re.sub(r"\[[^\]]*\]|\([^)]*\)", "", text)       # stage directions
    text = re.sub(r"^\s*#+.*$", "", text, flags=re.M)        # headings
    text = re.sub(r"[*_`]", "", text).replace("—", ", ").replace("–", ", ")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def write_script(cfg, title, style, minutes, language, notes="", persona=""):
    words = int(minutes * cfg.get("words_per_minute", 150))
    st = cfg["styles"].get(style, {})
    system = ("You are an elite YouTube scriptwriter. " + cfg.get("script_rules", "") + "\n" + st.get("script_hint", ""))
    user = (f"Video title: {title}\nLanguage of the script: {language}\nLength: about {words} words (stay within 5 percent).\n"
            + (f"Host persona (write in this voice, use the name, sign-off and people from it):\n{persona}\n" if persona else "")
            + (f"Extra notes from the owner:\n{notes}\n" if notes else "")
            + "Write the full voiceover script now. Output only the spoken words.")
    if words <= 2200:
        return clean_script(chat(cfg, system, user, max_tokens=min(16000, int(words * 2.2) + 800)))
    # long videos (up to 60 minutes): outline first, then write each part with the story so far
    parts = max(2, round(words / 1500))
    outline = _json(chat(cfg, "You plan long YouTube scripts. Return ONLY a JSON array of strings.",
                         f"Video title: {title}\nLanguage: {language}\n{notes}\nPlan {parts} parts for a {minutes:g} minute video. "
                         "Each string: what this part covers, its open loop or tease, and how it hands over to the next part. "
                         "Part one opens with the hook, the last part pays off the big promise and ends the video.", 3000))
    outline = [str(x) for x in outline][:parts] or [title] * parts
    per = words // len(outline)
    out = []
    for k, part in enumerate(outline):
        tail = " ".join(" ".join(out).split()[-120:])
        u = (user.rsplit("Write the full", 1)[0]
             + f"\nFull plan:\n" + "\n".join(f"{j + 1}. {x}" for j, x in enumerate(outline))
             + f"\n\nNow write ONLY part {k + 1} of {len(outline)} ({part}), about {per} words."
             + (f" Continue naturally from where the script left off: ...{tail}" if tail else " Start with the hook.")
             + (" This is the final part: pay off the promise and end the video." if k == len(outline) - 1 else
                " Do not end the video and do not say goodbye.")
             + " Output only the spoken words.")
        out.append(clean_script(chat(cfg, system, u, max_tokens=min(16000, int(per * 2.2) + 800))))
    return "\n\n".join(out)


def split_scenes(script, target_words=32):
    """Group sentences into scenes of roughly target_words, respecting paragraphs."""
    scenes = []
    for para in re.split(r"\n\s*\n", script.strip()):
        sents = [s.strip() for s in re.split(r"(?<=[.!?।…])\s+", " ".join(para.split())) if s.strip()]
        cur = []
        for s in sents:
            cur.append(s)
            if sum(len(x.split()) for x in cur) >= target_words:
                scenes.append(" ".join(cur))
                cur = []
        if cur:
            if scenes and sum(len(x.split()) for x in cur) < 8 and len(sents) > len(cur):
                scenes[-1] += " " + " ".join(cur)
            else:
                scenes.append(" ".join(cur))
    return scenes


def keywords(text, n=3):
    ws = [w for w in re.findall(r"[^\W\d_]{3,}", text.lower()) if w not in STOP]
    seen, out = set(), []
    for w in sorted(ws, key=lambda w: -len(w)):
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out[:n]


def basic_annotation(narrations, title, style):
    scenes = []
    tk = " ".join(keywords(title, 2))
    for i, n in enumerate(narrations):
        kw = keywords(n)
        q = " ".join(kw[:2]) or tk or title
        scenes.append({"narration": n, "queries": [q, (kw[2] + " " + tk).strip() if len(kw) > 2 else tk or q],
                       "image_prompt": f"{title}. {n[:160]}", "text": "",
                       "kind": "aroll" if style.startswith("avatar") and (i % 3 == 0 or i == len(narrations) - 1) else "broll"})
    return scenes


def annotate(cfg, narrations, title, style, log=lambda m: None, allowed=None):
    """Ask the AI for B-roll search terms, image prompts and on-screen text for every scene."""
    import graphics
    style_cfg = cfg.get("styles", {}).get(style, {})
    scenes = basic_annotation(narrations, title, style)
    allowed = list(allowed if allowed is not None else graphics.TYPES)
    if provider(cfg) == "none":
        return scenes
    system = ("You are a video editor planning visuals. For each numbered narration scene return a JSON array of objects: "
              '{"i": scene number, "queries": [2 short ENGLISH stock-footage search phrases, 2-3 words each, concrete and filmable], '
              '"image_prompt": "one ENGLISH sentence describing a single clear image for this scene, no text in the image", '
              '"text": "0-4 word on-screen phrase in the narration language for key numbers, names or punchlines, empty string for most scenes", '
              '"kind": "aroll" or "broll"}. '
              + ('Mark as "aroll" the scenes where the host should be on camera: the hook, personal stories, asks and the ending '
                 "(about 40 percent of scenes); the rest are broll. " if style.startswith("avatar") else 'Always use "broll". ')
              + '"graphic": optional animated graphic, ONLY when the narration names a real place, person, numbers or dates. '
              'Use exactly one of these forms: ' + " | ".join(graphics.TYPES[k] for k in allowed if k in graphics.TYPES)
              + '. Every number, date and name must come from the narration and be true. Use a graphic in at most one scene in four, '
              'otherwise an empty string. '
              + "Give on-screen text to roughly one scene in three. " + (style_cfg.get("text_hint") or "") + " Output ONLY the JSON array.")
    for a in range(0, len(narrations), 12):
        chunk = narrations[a:a + 12]
        user = f"Video title: {title}\n\n" + "\n".join(f"{a + j}. {n}" for j, n in enumerate(chunk))
        try:
            try:
                items = _json(chat(cfg, system, user, max_tokens=6000))
            except Exception:
                items = _json(chat(cfg, system, user, max_tokens=6000))  # free models sometimes return junk once
            for o in items:
                i = int(o.get("i", -1))
                if 0 <= i < len(scenes):
                    q = [str(x) for x in (o.get("queries") or []) if x][:3]
                    scenes[i].update({"queries": q or scenes[i]["queries"],
                                      "image_prompt": str(o.get("image_prompt") or scenes[i]["image_prompt"]),
                                      "text": str(o.get("text") or "")[:40],
                                      "graphic": str(o.get("graphic") or "")[:200],
                                      "kind": "aroll" if o.get("kind") == "aroll" and style.startswith("avatar") else "broll"})
        except Exception as e:  # keep the keyword fallback for this batch
            log(f"AI scene planning failed for scenes {a}-{a + len(chunk)}, using keywords instead ({e})")
    return scenes


FORMULAS = [
    "Most People Get {T} Wrong. Do This Instead",
    "Stop Doing This With {T}! Try This Instead",
    "The Truth About {T} Nobody Told You",
    "{T}: 7 Things You Were Never Taught",
    "What Actually Happens With {T} (Not What You Think)",
    "Why {T} Keeps Going Wrong, and the Simple Fix",
    "I Tried {T} the Old Way. Here Is What Happened",
    "The Cheap Trick That Changes {T} Forever",
    "{T} Explained in a Way That Finally Makes Sense",
    "Before You Try {T}, Watch This",
]


def titles(cfg, topic, count=10, language="English", notes=""):
    if provider(cfg) != "none":
        try:
            out = _json(chat(cfg, "You are a YouTube packaging specialist. Return ONLY a JSON array of strings.",
                             f"Write {count} YouTube titles in {language} for a video about: {topic}\n{notes}\n"
                             "Each under 70 characters, one strong curiosity gap, at most one ALL CAPS word, no emojis, "
                             "no clickbait the video cannot deliver. Mix styles: you're doing it wrong, stop doing X, "
                             "number lists, the cheap trick, what actually happens when.", 1500))
            out = [str(t).strip() for t in out if str(t).strip()]
            if out:
                return out[:count], "ai"
        except Exception:
            pass
    t = topic.strip().rstrip(".!?")
    t = t[0].upper() + t[1:] if t else "This"
    return [f.format(T=t) for f in FORMULAS][:count], "template"


def metadata(cfg, title, script, language="English"):
    """Titles, description, tags, hashtags, pinned comment and a short thumbnail text."""
    kw = keywords(title + " " + script[:1500], 12)
    fallback = {"titles": titles({**cfg, "llm_provider": "none"}, title, 6)[0],
                "description": script[:300].rsplit(" ", 1)[0] + "...",
                "tags": ", ".join([title.lower()] + kw), "hashtags": " ".join("#" + k for k in kw[:5]),
                "pinned_comment": "Thank you for watching! Tell me in the comments what you think.",
                "thumb_text": " ".join(title.split()[:3]).upper()}
    if provider(cfg) == "none":
        return fallback
    try:
        o = _json(chat(cfg, "You are a YouTube packaging specialist. Return ONLY one JSON object.",
                       f"Language: {language}\nWorking title: {title}\nScript:\n{script[:6000]}\n\n"
                       'Return {"titles": [6 titles under 70 characters], "description": "1500-3000 characters, hook in the '
                       "first two lines, what the viewer learns, a subscribe line, one question, 3 hashtags on the last line, "
                       'no links", "tags": "20-35 comma separated tags under 500 characters, no brand names", '
                       '"hashtags": "8 hashtags on one line", "pinned_comment": "2-4 warm sentences with one bonus tip and '
                       'one question", "thumb_text": "2-4 words in capitals that add to the title"}', 4000))
        return {**fallback, **{k: v for k, v in o.items() if v}}
    except Exception:
        return fallback
