"""Voiceover: free neural voices (with per-line emotion shaping), ElevenLabs, or the user's own recording."""
import asyncio
import base64
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

from . import catalog, core

# honour a corporate / sandbox CA bundle for the websocket TTS client
try:
    import certifi
    _ca = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    if _ca and os.path.exists(_ca):
        certifi.where = lambda: _ca
except Exception:
    pass

EMOTION = {  # (rate %, pitch Hz) nudges that make a neural voice act the line
    "calm": (0, 0), "tense": (-5, -4), "sad": (-9, -6), "excited": (6, 6), "warm": (-3, 2), "mystery": (-8, -5),
}
SAMPLE = {
    "en": "At nine oh six that morning, nobody on the dock knew what was coming. By noon, everything had changed.",
    "hi": "उस सुबह किसी को अंदाज़ा नहीं था कि आगे क्या होने वाला है। दोपहर तक, सब कुछ बदल चुका था।",
    "es": "Aquella mañana nadie en el muelle sabía lo que venía. Al mediodía, todo había cambiado.",
}
_el_cache = {"t": 0, "voices": []}
_edge_names = {"t": 0, "names": None}


def _proxy():
    return os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or None


def edge_names():
    if _edge_names["names"] is None or time.time() - _edge_names["t"] > 86400:
        try:
            import edge_tts
            vs = asyncio.run(edge_tts.list_voices(proxy=_proxy()))
            _edge_names["names"] = {v["ShortName"]: v for v in vs}
            _edge_names["t"] = time.time()
        except Exception:
            _edge_names["names"] = _edge_names["names"] or {}
    return _edge_names["names"]


def elevenlabs_voices():
    if time.time() - _el_cache["t"] < 3600 and _el_cache["voices"]:
        return _el_cache["voices"]
    key = core.get_settings().get("elevenlabs_key")
    try:
        r = core.fetch("https://api.elevenlabs.io/v1/voices", timeout=20, headers={"xi-api-key": key} if key else None)
        out = []
        for v in r.json().get("voices", []):
            lb = v.get("labels") or {}
            age = (lb.get("age") or "middle").replace("middle_aged", "middle").replace("middle aged", "middle").replace("-", "_")
            out.append({"id": "el:" + v["voice_id"], "name": v.get("name", "Voice"), "provider": "elevenlabs",
                        "gender": lb.get("gender", ""), "age": "middle" if "middle" in age else age, "accent": (lb.get("accent") or "").title(),
                        "style": lb.get("use_case") or lb.get("description") or "", "desc": (v.get("description") or lb.get("description") or "").strip()[:140],
                        "preview": v.get("preview_url"), "locked": not key})
        _el_cache.update(t=time.time(), voices=out)
    except Exception:
        pass
    return _el_cache["voices"]


def list_all(lang=None):
    names = edge_names()
    out = []
    for v in catalog.voice_list():
        if names and v["base"] not in names:
            continue
        v["locale"] = v["base"][:5]
        v["multilingual"] = v["base"] in catalog.MULTILINGUAL
        out.append(v)
    out += elevenlabs_voices()
    return out


def more_neural(locale_prefix):
    """Every raw neural voice for a language, for niche languages the curated list does not cover."""
    out = []
    for n, v in sorted(edge_names().items()):
        if n.lower().startswith(locale_prefix.lower()):
            out.append({"id": "edge:" + n, "name": n.split("-")[-1].replace("Neural", "").replace("Multilingual", " (multi)"),
                        "provider": "neural", "gender": v.get("Gender", "").lower(), "age": "middle", "accent": v.get("LocaleName", n[:5]),
                        "style": ", ".join((v.get("VoiceTag") or {}).get("VoicePersonalities", [])), "desc": v.get("FriendlyName", ""), "locale": n[:5]})
    return out


def resolve(voice_id, lang="en"):
    """→ dict(provider, base, rate, pitch)"""
    if voice_id and voice_id.startswith("el:"):
        return {"provider": "elevenlabs", "base": voice_id[3:], "rate": 0, "pitch": 0}
    if voice_id and voice_id.startswith("edge:"):
        return {"provider": "neural", "base": voice_id[5:], "rate": 0, "pitch": 0}
    v = catalog.voice_by_id(voice_id) or catalog.voice_by_id("andrew_doc")
    base = v["base"]
    want = catalog.LANG_LOCALE.get(lang, "en-US")[:2]
    if base[:2] != want and base not in catalog.MULTILINGUAL:  # voice cannot speak this language → nearest native voice
        native = [n for n, x in edge_names().items() if n.startswith(want) and x.get("Gender", "").lower() == v["gender"]]
        if native:
            base = native[0]
    return {"provider": "neural", "base": base, "rate": v["rate"], "pitch": v["pitch"]}


def _spread_words(text, dur, t0=0.06):
    ws = core.words_of(text)
    if not ws:
        return []
    weights = [len(w) + 2 + (4 if w[-1] in ".,!?" else 0) for w in ws]
    tot = float(sum(weights))
    out, t = [], t0
    span = max(0.2, dur - t0 - 0.08)
    for w, wt in zip(ws, weights):
        d = span * wt / tot
        out.append({"w": w, "s": round(t, 3), "e": round(t + d * 0.92, 3)})
        t += d
    return out


def _merge_words(text, marks):
    """Map TTS word boundaries (which drop punctuation) back onto the script's words."""
    ws = core.words_of(text)
    if not marks:
        return []
    if len(marks) == len(ws):
        return [{"w": w, "s": m["s"], "e": m["e"]} for w, m in zip(ws, marks)]
    out, j = [], 0
    for i, w in enumerate(ws):
        k = min(len(marks) - 1, int(round(i * (len(marks) - 1) / max(1, len(ws) - 1))))
        j = max(j, k)
        out.append({"w": w, "s": marks[j]["s"], "e": marks[j]["e"]})
    for i in range(1, len(out)):
        if out[i]["s"] <= out[i - 1]["s"]:
            out[i]["s"] = out[i - 1]["s"] + 0.04
            out[i]["e"] = max(out[i]["e"], out[i]["s"] + 0.05)
    return out


async def _edge(text, base, rate, pitch, out):
    import edge_tts
    kw = dict(rate="%+d%%" % rate, pitch="%+dHz" % pitch, proxy=_proxy())
    try:
        com = edge_tts.Communicate(text, base, boundary="WordBoundary", **kw)
    except TypeError:
        com = edge_tts.Communicate(text, base, **kw)
    marks = []
    with open(out, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                marks.append({"s": ch["offset"] / 1e7, "e": (ch["offset"] + ch["duration"]) / 1e7})
    return marks


def _eleven(text, voice_id, out):
    s = core.get_settings()
    if not s.get("elevenlabs_key"):
        raise RuntimeError("Add your ElevenLabs API key in Owner Settings to use this voice.")
    r = core.http().post("https://api.elevenlabs.io/v1/text-to-speech/%s/with-timestamps" % voice_id,
                         headers={"xi-api-key": s["elevenlabs_key"], "content-type": "application/json"},
                         json={"text": text, "model_id": "eleven_multilingual_v2",
                               "voice_settings": {"stability": 0.42, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": True}}, timeout=180)
    if r.status_code != 200:
        raise RuntimeError("ElevenLabs error %s: %s" % (r.status_code, r.text[:200]))
    j = r.json()
    with open(out, "wb") as f:
        f.write(base64.b64decode(j["audio_base64"]))
    al = j.get("alignment") or {}
    chars, st, en = al.get("characters") or [], al.get("character_start_times_seconds") or [], al.get("character_end_times_seconds") or []
    marks, cur = [], None
    for c, a, b in zip(chars, st, en):
        if c.strip():
            if cur is None:
                cur = {"s": a, "e": b}
            cur["e"] = b
        elif cur:
            marks.append(cur)
            cur = None
    if cur:
        marks.append(cur)
    return marks


def speakable(text, lang):
    t = text.replace("&", " and ").replace("%", " percent").replace("…", "...")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def synth(text, voice_id, out_mp3, emotion="calm", lang="en", humanize=True):
    """Synthesise one line. Returns (duration_seconds, words[])"""
    v = resolve(voice_id, lang)
    text_s = speakable(text, lang)
    last = None
    for attempt in range(4):
        try:
            if v["provider"] == "elevenlabs":
                marks = _eleven(text_s, v["base"], out_mp3)
            else:
                dr, dp = EMOTION.get(emotion, (0, 0)) if humanize else (0, 0)
                jitter = ((core.seed_of(text) % 5) - 2) if humanize else 0  # tiny per-line variation, like a real read
                marks = asyncio.run(_edge(text_s, v["base"], v["rate"] + dr + jitter, v["pitch"] + dp, out_mp3))
            if os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 600:
                break
            last = RuntimeError("no audio returned")
        except Exception as e:
            last = e
            if "API key" in str(e):
                raise
        time.sleep(1.2 * (attempt + 1))
    else:
        raise RuntimeError("Voice generation failed: %s" % last)
    dur = core.media_duration(out_mp3)
    words = _merge_words(text, marks) or _spread_words(text, dur)
    end = min(dur, (words[-1]["e"] if words else dur) + 0.18)
    return end, words


def synth_beats(beats, voice_id, lang, folder, progress=lambda f, m: None, humanize=True):
    os.makedirs(folder, exist_ok=True)
    done = [0]

    def job(i):
        b = beats[i]
        path = os.path.join(folder, "b%04d_%s.mp3" % (i, core.h(b["text"] + voice_id, 8)))
        if not (os.path.exists(path) and b.get("words") and b.get("audio") == path):
            d, words = synth(b["text"], voice_id, path, b.get("emotion", "calm"), lang, humanize)
            b.update(audio=path, vdur=d, words=words)
        done[0] += 1
        progress(done[0] / len(beats), "Recording voiceover %d/%d" % (done[0], len(beats)))
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(job, range(len(beats))))


def preview(voice_id, lang="en"):
    path = os.path.join(core.CACHE, "voice_%s_%s.mp3" % (re.sub(r"\W", "_", voice_id), lang))
    if not os.path.exists(path):
        synth(SAMPLE.get(lang[:2], SAMPLE["en"]), voice_id, path, "calm", lang)
    return path


def transcribe(path, lang=None):
    """Word-level transcript of an uploaded voiceover (needs the optional faster-whisper package)."""
    try:
        from faster_whisper import WhisperModel
    except Exception:
        raise RuntimeError("Uploaded voiceovers need the 'faster-whisper' package (pip install faster-whisper).")
    try:
        model = WhisperModel(os.environ.get("STUDIO_WHISPER", "small"), device="cpu", compute_type="int8")
        segs, _ = model.transcribe(path, word_timestamps=True, language=None if not lang or lang == "hinglish" else lang[:2])
        words = []
        for sg in segs:
            for w in sg.words or []:
                words.append({"w": w.word.strip(), "s": float(w.start), "e": float(w.end)})
    except Exception as e:
        raise RuntimeError("Could not transcribe the voiceover (speech model unavailable on this server): %s" % str(e)[:160])
    if not words:
        raise RuntimeError("No speech found in the uploaded voiceover.")
    return words


def beats_from_words(words):
    """Group transcript words into sentence beats with absolute timings."""
    beats, cur = [], []
    for w in words:
        cur.append(w)
        long_gap = False
        if w["w"][-1:] in ".!?।" or len(cur) >= 28 or long_gap:
            beats.append(cur)
            cur = []
    if cur:
        beats.append(cur)
    out = []
    for g in beats:
        t0 = g[0]["s"]
        out.append({"text": " ".join(x["w"] for x in g), "abs_start": t0, "vdur": g[-1]["e"] - t0 + 0.1,
                    "words": [{"w": x["w"], "s": x["s"] - t0, "e": x["e"] - t0} for x in g]})
    return out
