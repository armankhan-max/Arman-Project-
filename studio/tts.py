"""Voiceover: free neural voices (edge-tts) or the owner's own uploaded recording."""
import asyncio
import os
import subprocess
import wave

import numpy as np

SR = 48000
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or None

FALLBACK_VOICES = [
    {"id": "en-US-AndrewMultilingualNeural", "name": "Andrew (US, male, warm)", "lang": "en-US", "gender": "Male"},
    {"id": "en-US-AvaMultilingualNeural", "name": "Ava (US, female)", "lang": "en-US", "gender": "Female"},
    {"id": "en-US-GuyNeural", "name": "Guy (US, male)", "lang": "en-US", "gender": "Male"},
    {"id": "en-GB-RyanNeural", "name": "Ryan (UK, male)", "lang": "en-GB", "gender": "Male"},
    {"id": "en-IN-PrabhatNeural", "name": "Prabhat (India English, male)", "lang": "en-IN", "gender": "Male"},
    {"id": "hi-IN-MadhurNeural", "name": "Madhur (Hindi, male)", "lang": "hi-IN", "gender": "Male"},
    {"id": "hi-IN-SwaraNeural", "name": "Swara (Hindi, female)", "lang": "hi-IN", "gender": "Female"},
]
_voices = None


CHILD = {"en-US-AnaNeural", "en-GB-MaisieNeural"}
# Age tone presets for the free voices (pitch / speed shift). ElevenLabs voices carry their real age.
AGES = {
    "child": {"label": "Child / teen", "pitch": 28, "rate": 6},
    "young": {"label": "Young adult", "pitch": 8, "rate": 4},
    "middle": {"label": "Middle aged", "pitch": 0, "rate": 0},
    "old": {"label": "Old / elderly", "pitch": -14, "rate": -12},
}
EL_API = "https://api.elevenlabs.io/v1"
_el_cache = {}


def voices(cfg=None):
    """Free neural voices + the owner's ElevenLabs voices (if a key is set), with category labels."""
    global _voices
    if _voices is None:
        try:
            import edge_tts
            raw = asyncio.run(edge_tts.list_voices(proxy=PROXY))
            _voices = []
            for v in raw:
                tag = v.get("VoiceTag") or {}
                nm = v["ShortName"].split("-", 2)[2].replace("Neural", "").replace("Multilingual", " (multilingual)")
                _voices.append({"id": v["ShortName"], "lang": v["Locale"], "gender": v["Gender"], "provider": "free",
                                "age": "child" if v["ShortName"] in CHILD else "adult",
                                "style": ", ".join(tag.get("VoicePersonalities") or [])[:60],
                                "name": nm})
        except Exception:
            _voices = None
            out = [dict(v, provider="free", age="adult", style="") for v in FALLBACK_VOICES]
        else:
            out = list(_voices)
    else:
        out = list(_voices)
    key = (cfg or {}).get("elevenlabs_key")
    if key:
        out = elevenlabs_voices(key) + out
    return out


def elevenlabs_voices(key):
    if key in _el_cache:
        return _el_cache[key]
    import requests
    try:
        r = requests.get(EL_API + "/voices", headers={"xi-api-key": key}, timeout=30)
        r.raise_for_status()
        out = []
        for v in r.json().get("voices", []):
            lb = v.get("labels") or {}
            age = (lb.get("age") or "").lower()
            age = "old" if "old" in age else "middle" if "middle" in age else "young" if "young" in age else "child" if ("child" in age or "teen" in age) else "adult"
            out.append({"id": "el:" + v["voice_id"], "lang": "multi", "gender": (lb.get("gender") or "").title() or "Any",
                        "provider": "elevenlabs", "age": age, "preview": v.get("preview_url") or "",
                        "style": ", ".join(x for x in (lb.get("accent"), lb.get("description"), lb.get("use_case") or lb.get("use case")) if x)[:60],
                        "name": v.get("name", "voice")})
        _el_cache[key] = out
        return out
    except Exception:
        return []


def _el_synth(text, voice_id, out_mp3, key, speed=1.0):
    import base64
    import requests
    body = {"text": text, "model_id": "eleven_multilingual_v2"}
    if abs(speed - 1.0) > 0.01:
        body["voice_settings"] = {"stability": 0.5, "similarity_boost": 0.75, "speed": max(0.7, min(1.2, speed))}
    r = requests.post(f"{EL_API}/text-to-speech/{voice_id}/with-timestamps", headers={"xi-api-key": key},
                      json=body, timeout=300)
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs error {r.status_code}: {r.text[:200]}")
    j = r.json()
    with open(out_mp3, "wb") as f:
        f.write(base64.b64decode(j["audio_base64"]))
    al = j.get("alignment") or j.get("normalized_alignment") or {}
    chars, st, en = al.get("characters", []), al.get("character_start_times_seconds", []), al.get("character_end_times_seconds", [])
    words, cur, a, b = [], "", None, None
    for ch, s0, e0 in zip(chars, st, en):
        if ch.isspace():
            if cur:
                words.append([round(a, 3), round(b, 3), cur])
            cur, a = "", None
            continue
        if a is None:
            a = s0
        cur += ch
        b = e0
    if cur:
        words.append([round(a, 3), round(b, 3), cur])
    return words


def synth(text, voice, out_mp3, rate=0, pitch=0):
    """Speak text to out_mp3. Returns word timings [[start, end, word], ...] in seconds."""
    if voice.startswith("el:"):
        import store
        key = store.get_settings().get("elevenlabs_key")
        if not key:
            raise RuntimeError("This is an ElevenLabs voice: add your ElevenLabs key in the Owner panel.")
        last = None
        for _ in range(3):
            try:
                return _el_synth(text, voice[3:], out_mp3, key, 1 + int(rate) / 100)
            except Exception as e:
                last = e
        raise RuntimeError(f"Voice generation failed: {last}")
    import edge_tts

    async def run():
        words = []
        c = edge_tts.Communicate(text, voice, rate=f"{int(rate):+d}%", pitch=f"{int(pitch):+d}Hz", boundary="WordBoundary", proxy=PROXY)
        with open(out_mp3, "wb") as f:
            async for ch in c.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    s = ch["offset"] / 1e7
                    words.append([round(s, 3), round(s + ch["duration"] / 1e7, 3), ch["text"]])
        return words

    last = None
    for _ in range(3):
        try:
            w = asyncio.run(run())
            if os.path.getsize(out_mp3) > 0:
                return w
        except Exception as e:
            last = e
    raise RuntimeError(f"Voice generation failed: {last}")


def decode(path):
    """Any audio file -> mono float32 numpy array at 48 kHz."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def write_wav(path, mono):
    data = (np.clip(mono, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def spread_words(text, start, dur):
    """No real timings (uploaded voice): spread words over the scene by their length."""
    ws = text.split()
    total = sum(len(w) + 1 for w in ws) or 1
    out, t = [], start
    for w in ws:
        d = dur * (len(w) + 1) / total
        out.append([round(t, 3), round(t + d, 3), w.strip(".,!?;:\"'()।")])
        t += d
    return out


# ---------- background music, generated so nothing has to be licensed ----------
MOODS = {
    "cinematic": {"root": 55.0, "chords": [[0, 7, 15, 19], [-4, 3, 12, 15], [-2, 5, 14, 17], [-7, 0, 12, 15]], "bar": 8.0, "pluck": False},
    "calm": {"root": 65.41, "chords": [[0, 7, 16, 19], [5, 12, 21, 24], [-3, 4, 12, 16], [-5, 2, 11, 14]], "bar": 7.0, "pluck": False},
    "suspense": {"root": 49.0, "chords": [[0, 7, 12, 15], [1, 8, 13, 16], [0, 7, 12, 15], [-2, 5, 10, 13]], "bar": 6.0, "pluck": False, "pulse": True},
    "emotional": {"root": 58.27, "chords": [[0, 7, 16, 23], [-3, 4, 12, 19], [5, 12, 16, 21], [-5, 2, 11, 14]], "bar": 6.0, "pluck": True, "soft": True},
    "upbeat": {"root": 73.42, "chords": [[0, 7, 16, 19], [-3, 4, 12, 16], [5, 12, 21, 24], [7, 14, 19, 23]], "bar": 4.0, "pluck": True},
}


def make_music(mood, seconds, seed=None):
    m = dict(MOODS.get(mood, MOODS["cinematic"]))
    if seed is not None:  # every video gets its own key, tempo and chord order
        import random
        rnd = random.Random(seed)
        m["root"] = m["root"] * 2 ** (rnd.randint(-4, 4) / 12)
        m["bar"] = m["bar"] * rnd.uniform(0.85, 1.2)
        ch = list(m["chords"])
        first = ch[0]
        rest = ch[1:]
        rnd.shuffle(rest)
        m["chords"] = [first] + rest
        m["pluck"] = m.get("pluck") or rnd.random() < 0.3
        m["pulse"] = m.get("pulse") or (mood in ("suspense", "cinematic") and rnd.random() < 0.5)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, dtype=np.float32)
    bar = m["bar"]
    for b in range(int(seconds / bar) + 1):
        chord = m["chords"][b % len(m["chords"])]
        a, e = int(b * bar * SR), min(n, int((b + 1.25) * bar * SR))
        if a >= n:
            break
        tt = t[a:e] - b * bar
        env = np.clip(tt / (bar * 0.3), 0, 1) * np.clip((bar * 1.25 - tt) / (bar * 0.35), 0, 1)
        for k, semi in enumerate(chord):
            f = m["root"] * 2 * 2 ** (semi / 12)
            out[a:e] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt + k)
                         + 0.5 * np.sin(2 * np.pi * f * 1.003 * tt)) * env * 0.11
        out[a:e] += np.sin(2 * np.pi * m["root"] * 2 ** (chord[0] / 12) * tt) * env * 0.22
        if m.get("pulse"):  # low heartbeat pulse for tension
            for s in range(int(bar / 0.75)):
                pa = int((b * bar + s * 0.75) * SR)
                pe = min(n, pa + int(0.35 * SR))
                if pa >= n:
                    break
                pt = np.arange(pe - pa) / SR
                out[pa:pe] += np.sin(2 * np.pi * m["root"] * pt) * np.exp(-pt * 9) * 0.35
        if m["pluck"]:
            step = bar / 8
            for s in range(8):
                pa = int((b * bar + s * step) * SR)
                pe = min(n, pa + int(0.5 * SR))
                if pa >= n:
                    break
                pt = np.arange(pe - pa) / SR
                if m.get("soft") and s % 2:
                    continue
                f = m["root"] * 4 * 2 ** (chord[[0, 2, 1, 3, 2, 1, 3, 2][s]] / 12)
                out[pa:pe] += (np.sin(2 * np.pi * f * pt) + 0.25 * np.sin(4 * np.pi * f * pt)) * np.exp(-pt * (4 if m.get("soft") else 7)) * 0.16
    fade = int(min(3, seconds / 4) * SR)
    if fade:
        out[:fade] *= np.linspace(0, 1, fade)
        out[-fade:] *= np.linspace(1, 0, fade)
    return out / (np.abs(out).max() + 1e-6) * 0.8
