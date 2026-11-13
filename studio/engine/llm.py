"""One LLM entry point with several providers. 'auto' uses the first configured key and
falls back to the free keyless endpoint so the site works out of the box."""
import json
import re
import time

from . import core

DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-5-5",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
    "groq": "llama-3.3-70b-versatile",
    "pollinations": "openai",
}


def provider():
    s = core.get_settings()
    p = s.get("llm_provider") or "auto"
    if p != "auto":
        return p
    for name in ("anthropic", "openai", "gemini", "groq"):
        if s.get(name + "_key"):
            return name
    return "pollinations"


def _post(url, headers, body, timeout=180):
    r = core.http().post(url, headers=headers, json=body, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError("LLM HTTP %s: %s" % (r.status_code, r.text[:300]))
    return r.json()


def _call(p, system, user, max_tokens, temperature, want_json):
    s = core.get_settings()
    model = s.get("llm_model") or DEFAULT_MODELS[p]
    if p == "anthropic":
        j = _post("https://api.anthropic.com/v1/messages",
                  {"x-api-key": s["anthropic_key"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
                  {"model": model, "max_tokens": max_tokens, "system": system,
                   "messages": [{"role": "user", "content": user}]})
        return "".join(b.get("text", "") for b in j.get("content", []))
    if p == "gemini":
        j = _post("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s" % (model, s["gemini_key"]),
                  {"content-type": "application/json"},
                  {"systemInstruction": {"parts": [{"text": system}]},
                   "contents": [{"role": "user", "parts": [{"text": user}]}],
                   "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens,
                                        **({"responseMimeType": "application/json"} if want_json else {})}})
        return "".join(pt.get("text", "") for pt in j["candidates"][0]["content"]["parts"])
    url, key = {
        "openai": ("https://api.openai.com/v1/chat/completions", s.get("openai_key")),
        "groq": ("https://api.groq.com/openai/v1/chat/completions", s.get("groq_key")),
        "pollinations": ("https://text.pollinations.ai/openai", ""),
    }[p]
    body = {"model": model if p != "pollinations" else "openai",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temperature, "max_tokens": max_tokens}
    if p == "pollinations":  # free reasoning model: thinking counts against the limit, so give it room
        body["max_tokens"] = max(6000, max_tokens * 3)
        body["reasoning_effort"] = "low"
    if want_json:
        body["response_format"] = {"type": "json_object"}
    headers = {"content-type": "application/json"}
    if key:
        headers["authorization"] = "Bearer " + key
    j = _post(url, headers, body)
    return j["choices"][0]["message"].get("content") or ""


def chat(system, user, max_tokens=3000, temperature=0.8, want_json=False, retries=3):
    p = provider()
    order = [p] + (["pollinations"] if p != "pollinations" else [])
    last = None
    for prov in order:
        for i in range(retries):
            try:
                out = _call(prov, system, user, max_tokens, temperature, want_json)
                if out and out.strip():
                    return out.strip()
                last = RuntimeError("empty LLM reply")
            except Exception as e:
                last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError("AI writer unavailable: %s" % last)


def extract_json(text):
    """Pull the first JSON object/array out of a model reply, tolerant of code fences and trailing junk."""
    if text is None:
        raise ValueError("no text")
    t = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(t)
    except Exception:
        pass
    start = min([i for i in (t.find("{"), t.find("[")) if i >= 0], default=-1)
    if start < 0:
        raise ValueError("no JSON in reply")
    opener = t[start]
    closer = "}" if opener == "{" else "]"
    depth, in_str, esc = 0, False, False
    for i in range(start, len(t)):
        ch = t[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return json.loads(t[start:i + 1])
    # truncated reply: try to close it
    frag = t[start:]
    frag = re.sub(r",\s*$", "", frag)
    for tail in ("}", "]}", "}]}", "\"}]}", "]", "}]"):
        try:
            return json.loads(frag + tail)
        except Exception:
            continue
    raise ValueError("unparseable JSON")


def chat_json(system, user, max_tokens=3000, temperature=0.7, tries=3):
    last = None
    for i in range(tries):
        try:
            return extract_json(chat(system, user + "\n\nReply with valid JSON only.", max_tokens, temperature, want_json=True))
        except Exception as e:
            last = e
    raise RuntimeError("AI returned unusable data: %s" % last)
