"""Speech-to-text, text-to-speech, avatars and research/search adapters."""
import asyncio
import base64
import os

from .base import CredField, Provider, ProviderError, http


# ------------------------------------------------------------------ speech to text
class STTProvider(Provider):
    def transcribe(self, path, language=None) -> dict:
        """→ {'language', 'text', 'words': [{w,s,e,p}], 'word_level': bool, 'model'}"""
        raise NotImplementedError


class LocalWhisper(STTProvider):
    def __init__(self):
        super().__init__(name="whisper_local", label="Whisper (local, faster-whisper)", caps=("stt",), paid=False, unit="audio minutes",
                         docs="https://github.com/SYSTRAN/faster-whisper",
                         notes="Runs on this machine. The model is downloaded on first use (or set FDA_WHISPER_MODEL to a local model folder).")

    def _model(self):
        from fda.config import get_settings
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ProviderError("faster-whisper is not installed (pip install faster-whisper)", retryable=False, code="not_configured")
        try:
            return WhisperModel(get_settings().whisper_model, device="cpu", compute_type="int8")
        except Exception as e:
            raise ProviderError("Whisper model '%s' is not available on this machine (%s). Download it once with network access, "
                                "point FDA_WHISPER_MODEL to a local folder, or configure OpenAI transcription." % (get_settings().whisper_model, str(e)[:160]),
                                retryable=False, code="not_configured")

    def transcribe(self, path, language=None):
        model = self._model()
        segs, info = model.transcribe(path, word_timestamps=True, vad_filter=True, language=None if language in (None, "", "hinglish", "auto") else language[:2])
        words = []
        for sg in segs:
            for w in sg.words or []:
                words.append({"w": w.word.strip(), "s": round(float(w.start), 3), "e": round(float(w.end), 3), "p": round(float(w.probability or 0), 3)})
        return {"language": info.language, "text": " ".join(w["w"] for w in words), "words": words, "word_level": True, "model": "faster-whisper"}

    def validate(self):
        try:
            self._model()
            return True, "Model loaded"
        except ProviderError as e:
            return False, str(e)


class OpenAIWhisper(STTProvider):
    def __init__(self):
        super().__init__(name="openai_stt", label="OpenAI transcription (Whisper API)", caps=("stt",), paid=True, unit="audio minutes",
                         fields=(CredField("api_key", "API key", "OPENAI_API_KEY"),), docs="https://platform.openai.com/docs/guides/speech-to-text")

    def transcribe(self, path, language=None):
        self.need()
        if os.path.getsize(path) > 25 << 20:
            raise ProviderError("OpenAI transcription accepts files up to 25 MB; the processed copy is larger", retryable=False)
        data = {"model": "whisper-1", "response_format": "verbose_json", "timestamp_granularities[]": "word"}
        if language and language not in ("hinglish", "auto"):
            data["language"] = language[:2]
        with open(path, "rb") as f:
            j = http("POST", "https://api.openai.com/v1/audio/transcriptions", timeout=600, headers={"authorization": "Bearer " + self.creds["api_key"]},
                     data=data, files={"file": (os.path.basename(path), f)}).json()
        words = [{"w": w["word"].strip(), "s": round(w["start"], 3), "e": round(w["end"], 3), "p": 1.0} for w in j.get("words", [])]
        return {"language": j.get("language"), "text": j.get("text", ""), "words": words, "word_level": bool(words), "model": "whisper-1"}


# ------------------------------------------------------------------ text to speech
class TTSProvider(Provider):
    def voices(self) -> list:
        return []

    def speak(self, text, voice, dest, rate=0, pitch=0) -> dict:
        """→ {'words': [{w,s,e}] or [], 'duration'}"""
        raise NotImplementedError


class EdgeNeural(TTSProvider):
    def __init__(self):
        super().__init__(name="edge_tts", label="Microsoft Edge neural voices (free)", caps=("tts",), paid=False, unit="characters",
                         docs="https://github.com/rany2/edge-tts",
                         notes="Free online neural voices through the edge-tts client (unofficial endpoint, intended for personal use). Returns word timings.")

    def _proxy(self):
        return os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or None

    def voices(self):
        import edge_tts
        try:
            vs = asyncio.run(edge_tts.list_voices(proxy=self._proxy()))
        except Exception as e:
            raise ProviderError("Could not list voices: %s" % e)
        return [{"id": v["ShortName"], "name": v["ShortName"].split("-")[-1].replace("Neural", "").replace("Multilingual", " (multilingual)"),
                 "locale": v["Locale"], "gender": v.get("Gender", "").lower(), "tags": (v.get("VoiceTag") or {}).get("VoicePersonalities", [])} for v in vs]

    def speak(self, text, voice, dest, rate=0, pitch=0):
        import edge_tts
        _ca = os.environ.get("SSL_CERT_FILE")
        if _ca:
            import certifi
            certifi.where = lambda: _ca

        async def go():
            kw = dict(rate="%+d%%" % rate, pitch="%+dHz" % pitch, proxy=self._proxy())
            try:
                com = edge_tts.Communicate(text, voice, boundary="WordBoundary", **kw)
            except TypeError:
                com = edge_tts.Communicate(text, voice, **kw)
            marks = []
            with open(dest, "wb") as f:
                async for ch in com.stream():
                    if ch["type"] == "audio":
                        f.write(ch["data"])
                    elif ch["type"] == "WordBoundary":
                        marks.append({"w": ch.get("text", ""), "s": ch["offset"] / 1e7, "e": (ch["offset"] + ch["duration"]) / 1e7})
            return marks
        last = None
        for i in range(3):
            try:
                words = asyncio.run(go())
                if os.path.getsize(dest) > 600:
                    return {"words": words}
            except Exception as e:
                last = e
        raise ProviderError("Neural TTS failed: %s" % last)

    def validate(self):
        try:
            return True, "%d voices available" % len(self.voices())
        except ProviderError as e:
            return False, str(e)


class ElevenLabs(TTSProvider):
    def __init__(self):
        super().__init__(name="elevenlabs", label="ElevenLabs", caps=("tts",), paid=True, unit="characters",
                         fields=(CredField("api_key", "API key", "ELEVENLABS_API_KEY"),), docs="https://elevenlabs.io/docs/api-reference")

    def voices(self):
        self.need()
        j = http("GET", "https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": self.creds["api_key"]}).json()
        return [{"id": v["voice_id"], "name": v.get("name"), "locale": (v.get("labels") or {}).get("accent", ""), "gender": (v.get("labels") or {}).get("gender", ""),
                 "tags": [(v.get("labels") or {}).get("age", ""), (v.get("labels") or {}).get("use_case", "")]} for v in j.get("voices", [])]

    def speak(self, text, voice, dest, rate=0, pitch=0):
        self.need()
        j = http("POST", "https://api.elevenlabs.io/v1/text-to-speech/%s/with-timestamps" % voice, timeout=300,
                 headers={"xi-api-key": self.creds["api_key"], "content-type": "application/json"},
                 json={"text": text, "model_id": (self.config or {}).get("model", "eleven_multilingual_v2"),
                       "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.3}}).json()
        with open(dest, "wb") as f:
            f.write(base64.b64decode(j["audio_base64"]))
        al = j.get("alignment") or {}
        words, cur = [], None
        for c, a, b in zip(al.get("characters") or [], al.get("character_start_times_seconds") or [], al.get("character_end_times_seconds") or []):
            if c.strip():
                cur = cur or {"w": "", "s": a, "e": b}
                cur["w"] += c
                cur["e"] = b
            elif cur:
                words.append(cur)
                cur = None
        if cur:
            words.append(cur)
        return {"words": words}

    def validate(self):
        if not self.configured():
            return False, "Missing API key"
        try:
            return True, "%d voices" % len(self.voices())
        except ProviderError as e:
            return False, str(e)


# ------------------------------------------------------------------ avatars
class AvatarProvider(Provider):
    def submit(self, image_url, audio_url) -> str:
        raise NotImplementedError

    def poll(self, job_id) -> dict:
        raise NotImplementedError

    def wait(self, job_id, dest, timeout=3600, every=15):
        import time
        from .base import download
        t0 = time.time()
        while time.time() - t0 < timeout:
            st = self.poll(job_id)
            if st["status"] == "succeeded":
                return download(st["url"], dest, timeout=600, max_mb=2000)
            if st["status"] == "failed":
                raise ProviderError("Avatar video failed: %s" % st.get("error", "unknown"), retryable=False)
            time.sleep(every)
        raise ProviderError("Avatar video timed out after %ds" % timeout, retryable=True, code="timeout")


class DID(AvatarProvider):
    def __init__(self):
        super().__init__(name="d_id", label="D-ID talking avatars", caps=("avatar", "lipsync"), paid=True, unit="seconds",
                         fields=(CredField("api_key", "API key (user:secret)", "DID_API_KEY"),), docs="https://docs.d-id.com", verified=False,
                         notes="Written against D-ID's public docs; awaiting credentials. Only use faces and voices you have permission to use.")

    def _h(self):
        return {"authorization": "Basic " + base64.b64encode(self.creds["api_key"].encode()).decode() if ":" in self.creds["api_key"] else "Basic " + self.creds["api_key"],
                "content-type": "application/json"}

    def submit(self, image_url, audio_url):
        self.need()
        return http("POST", "https://api.d-id.com/talks", headers=self._h(), json={"source_url": image_url, "script": {"type": "audio", "audio_url": audio_url}}).json()["id"]

    def poll(self, job_id):
        j = http("GET", "https://api.d-id.com/talks/" + job_id, headers=self._h()).json()
        if j.get("status") == "done":
            return {"status": "succeeded", "url": j.get("result_url")}
        if j.get("status") in ("error", "rejected"):
            return {"status": "failed", "error": str(j.get("error"))}
        return {"status": "running"}


class HeyGen(AvatarProvider):
    """Photo + narration audio → lip-synced talking-head video."""

    def __init__(self):
        super().__init__(name="heygen", label="HeyGen (lip-synced avatar video)", caps=("avatar", "lipsync"), paid=True, unit="seconds",
                         fields=(CredField("api_key", "API key", "HEYGEN_API_KEY"),), docs="https://docs.heygen.com", verified=False,
                         notes="Written against HeyGen's public API docs; awaiting credentials for a live test. Uploads the saved character photo and the narration, returns a lip-synced video.")

    def _h(self, ct="application/json"):
        return {"X-Api-Key": self.creds["api_key"], "content-type": ct}

    def upload_photo(self, path):
        self.need()
        ct = "image/png" if path.lower().endswith(".png") else "image/jpeg"
        with open(path, "rb") as f:
            j = http("POST", "https://upload.heygen.com/v1/talking_photo", headers=self._h(ct), data=f.read(), timeout=180).json()
        return (j.get("data") or {}).get("talking_photo_id")

    def upload_audio(self, path):
        self.need()
        with open(path, "rb") as f:
            j = http("POST", "https://upload.heygen.com/v1/asset", headers=self._h("audio/mpeg"), data=f.read(), timeout=600).json()
        return (j.get("data") or {}).get("id")

    def submit_talk(self, talking_photo_id, audio_asset_id, width=1280, height=720):
        self.need()
        j = http("POST", "https://api.heygen.com/v2/video/generate", headers=self._h(), timeout=120,
                 json={"video_inputs": [{"character": {"type": "talking_photo", "talking_photo_id": talking_photo_id},
                                         "voice": {"type": "audio", "audio_asset_id": audio_asset_id}}],
                       "dimension": {"width": width, "height": height}}).json()
        vid = (j.get("data") or {}).get("video_id")
        if not vid:
            raise ProviderError("HeyGen did not return a video id: %s" % str(j)[:200], retryable=False)
        return vid

    def poll(self, job_id):
        j = http("GET", "https://api.heygen.com/v1/video_status.get", headers=self._h(), params={"video_id": job_id}).json()
        d = j.get("data") or {}
        if d.get("status") == "completed":
            return {"status": "succeeded", "url": d.get("video_url")}
        if d.get("status") == "failed":
            return {"status": "failed", "error": str(d.get("error"))}
        return {"status": "running"}

    def validate(self):
        if not self.configured():
            return False, "Missing API key"
        try:
            http("GET", "https://api.heygen.com/v2/avatars", headers=self._h(), retries=0, timeout=30)
            return True, "Key accepted"
        except ProviderError as e:
            return False, str(e)


class LocalTalkingPhoto(Provider):
    def __init__(self):
        super().__init__(name="talking_photo", label="Talking photo (local)", caps=("avatar",), paid=False, unit="seconds",
                         notes="Built in. Animates a still portrait (mouth movement from voice loudness, blinks, hand-held camera). "
                               "It is an approximation, not true lip sync; connect an avatar provider for studio-grade results.")

    def validate(self):
        return True, "Built in"


# ------------------------------------------------------------------ research
class Wikipedia(Provider):
    def __init__(self):
        super().__init__(name="wikipedia", label="Wikipedia API", caps=("web_search",), paid=False, unit="requests", docs="https://www.mediawiki.org/wiki/API:Main_page",
                         notes="No key. Encyclopedia summaries with links; treated as a secondary source.")

    def search(self, q, n=5):
        j = http("GET", "https://en.wikipedia.org/w/api.php", timeout=20, retries=1, headers={"User-Agent": "FilmDirectorAI/1.0"},
                 params={"action": "query", "format": "json", "generator": "search", "gsrsearch": q, "gsrlimit": n, "prop": "extracts|info|revisions",
                         "inprop": "url", "rvprop": "timestamp", "exintro": 1, "explaintext": 1, "exchars": 2500}).json()
        out = []
        for p in sorted(((j.get("query") or {}).get("pages") or {}).values(), key=lambda p: p.get("index", 99)):
            out.append({"title": p.get("title"), "url": p.get("fullurl"), "publisher": "Wikipedia", "published_at": ((p.get("revisions") or [{}])[0]).get("timestamp", "")[:10],
                        "content": p.get("extract", "")})
        return out

    def validate(self):
        try:
            self.search("moon", 1)
            return True, "Reachable"
        except ProviderError as e:
            return False, str(e)


class Tavily(Provider):
    def __init__(self):
        super().__init__(name="tavily", label="Tavily web search", caps=("web_search",), paid=True, unit="searches",
                         fields=(CredField("api_key", "API key", "TAVILY_API_KEY"),), docs="https://docs.tavily.com")

    def search(self, q, n=6):
        self.need()
        j = http("POST", "https://api.tavily.com/search", timeout=60, json={"api_key": self.creds["api_key"], "query": q, "max_results": n, "search_depth": "advanced"}).json()
        return [{"title": r.get("title"), "url": r.get("url"), "publisher": r.get("url", "").split("/")[2] if r.get("url") else "", "published_at": r.get("published_date") or "",
                 "content": r.get("content", "")} for r in j.get("results", [])]

    def validate(self):
        if not self.configured():
            return False, "Missing API key"
        try:
            self.search("test", 1)
            return True, "Key accepted"
        except ProviderError as e:
            return False, str(e)
