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


def voices():
    global _voices
    if _voices is None:
        try:
            import edge_tts
            raw = asyncio.run(edge_tts.list_voices(proxy=PROXY))
            _voices = [{"id": v["ShortName"], "lang": v["Locale"], "gender": v["Gender"],
                        "name": v["ShortName"].split("-", 2)[2].replace("Neural", "").replace("Multilingual", " (multilingual)")
                        + f" · {v['Locale']} · {v['Gender']}"} for v in raw]
        except Exception:
            return FALLBACK_VOICES
    return _voices


def synth(text, voice, out_mp3, rate=0):
    """Speak text to out_mp3. Returns word timings [[start, end, word], ...] in seconds."""
    import edge_tts

    async def run():
        words = []
        c = edge_tts.Communicate(text, voice, rate=f"{int(rate):+d}%", boundary="WordBoundary", proxy=PROXY)
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


def make_music(mood, seconds):
    m = MOODS.get(mood, MOODS["cinematic"])
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
