"""Provider registry: one place that knows every adapter, its stored configuration and its health."""
import hashlib
import math
import re
from datetime import datetime, timezone

from fda.auth.security import decrypt, encrypt, mask
from fda.database import models as m

from . import audio, llm, visual
from .base import CredField, NotConfigured, Provider, ProviderError, http

EMBED_DIM = m.EMBED_DIM


class HashEmbeddings(Provider):
    """Deterministic local embeddings (feature hashing of words, word pairs and character trigrams).
    Lexical rather than semantic, but free, offline and good enough for retrieval over project data."""

    def __init__(self):
        super().__init__(name="hash_embeddings", label="Local lexical embeddings", caps=("embeddings",), paid=False, unit="chunks",
                         notes="Offline fallback. Configure OpenAI embeddings for true semantic search.")

    model_name = "hash-v1-384"

    def embed(self, texts):
        out = []
        for t in texts:
            v = [0.0] * EMBED_DIM
            toks = re.findall(r"\w+", (t or "").lower())
            feats = toks + [a + "_" + b for a, b in zip(toks, toks[1:])]
            for w in toks:
                feats += ["#" + w[i:i + 3] for i in range(max(1, len(w) - 2))]
            for f in feats:
                hv = int(hashlib.md5(f.encode()).hexdigest()[:8], 16)
                v[hv % EMBED_DIM] += 1.0 if (hv >> 9) & 1 else -1.0
            n = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / n for x in v])
        return out

    def validate(self):
        return True, "Built in"


class OpenAIEmbeddings(Provider):
    model_name = "text-embedding-3-small@384"

    def __init__(self):
        super().__init__(name="openai_embeddings", label="OpenAI embeddings", caps=("embeddings",), paid=True, unit="1k tokens",
                         fields=(CredField("api_key", "API key", "OPENAI_API_KEY"),))

    def embed(self, texts):
        self.need()
        j = http("POST", "https://api.openai.com/v1/embeddings", headers={"authorization": "Bearer " + self.creds["api_key"]},
                 json={"model": "text-embedding-3-small", "input": texts, "dimensions": EMBED_DIM}).json()
        return [d["embedding"] for d in j["data"]]


class YouTubeData(Provider):
    def __init__(self):
        super().__init__(name="youtube_data", label="YouTube Data API v3 (public data)", caps=("youtube_public",), paid=False, unit="quota units",
                         fields=(CredField("api_key", "API key", "YOUTUBE_API_KEY"),), docs="https://developers.google.com/youtube/v3",
                         notes="Free with a daily quota (search costs 100 units, list calls 1 unit).")

    def validate(self):
        if not self.configured():
            return False, "Missing API key"
        try:
            http("GET", "https://www.googleapis.com/youtube/v3/videos", params={"part": "id", "id": "dQw4w9WgXcQ", "key": self.creds["api_key"]}, retries=0)
            return True, "Key accepted"
        except ProviderError as e:
            return False, str(e)


class GoogleOAuth(Provider):
    def __init__(self):
        super().__init__(name="google_oauth", label="Google OAuth (your YouTube channel)", caps=("youtube_oauth",), paid=False,
                         fields=(CredField("client_id", "OAuth client ID", "FDA_GOOGLE_CLIENT_ID", secret=False), CredField("client_secret", "OAuth client secret", "FDA_GOOGLE_CLIENT_SECRET")),
                         docs="https://developers.google.com/youtube/reporting/guides/authorization",
                         notes="Read-only scopes: youtube.readonly and yt-analytics.readonly.")


class ProceduralAudio(Provider):
    def __init__(self):
        super().__init__(name="procedural_audio", label="Original music & SFX (built in)", caps=("music", "sfx"), paid=False,
                         notes="Music beds and sound effects synthesised in code, so they are original and royalty-free.")

    def validate(self):
        return True, "Built in"


FACTORIES = [llm.Anthropic, llm.OpenAI, llm.Groq, llm.Pollinations, visual.PollinationsImage, visual.OpenAIImage, visual.RunwayVideo, visual.LumaVideo,
             visual.Pexels, visual.Pixabay, visual.WikimediaCommons, visual.NASAImages, audio.LocalWhisper, audio.OpenAIWhisper, audio.EdgeNeural,
             audio.ElevenLabs, audio.DID, audio.LocalTalkingPhoto, audio.Wikipedia, audio.Tavily, HashEmbeddings, OpenAIEmbeddings, YouTubeData,
             GoogleOAuth, ProceduralAudio]
# preference order when several providers can do the same job
PREFERENCE = {"llm": ["anthropic", "openai", "groq", "pollinations_text"], "text_to_image": ["openai_image", "pollinations_image"],
              "image_to_video": ["runway", "luma"], "text_to_video": ["luma", "runway"], "stock_video": ["pexels", "pixabay", "wikimedia"],
              "stock_image": ["pexels", "pixabay"], "archive_image": ["wikimedia", "nasa"], "stt": ["whisper_local", "openai_stt"],
              "tts": ["elevenlabs", "edge_tts"], "avatar": ["d_id", "talking_photo"], "web_search": ["tavily", "wikipedia"],
              "embeddings": ["openai_embeddings", "hash_embeddings"]}


def all_names():
    return [f().name for f in FACTORIES]


def get(db, name) -> Provider:
    for f in FACTORIES:
        p = f()
        if p.name == name:
            row = db.query(m.ModelProvider).filter_by(name=name).one_or_none() if db is not None else None
            return p.load(row)
    raise KeyError("Unknown provider %s" % name)


def for_cap(db, cap, usable_only=True, allow_paid=True) -> list[Provider]:
    """Providers able to do `cap`, best first. With usable_only, only enabled + configured ones."""
    names = PREFERENCE.get(cap) or [f().name for f in FACTORIES if cap in f().caps]
    out = []
    for n in names:
        p = get(db, n)
        if cap not in p.caps:
            continue
        if usable_only and (not p.enabled or not p.configured()):
            continue
        if not allow_paid and p.paid:
            continue
        out.append(p)
    return out


def first(db, cap, **kw) -> Provider:
    ps = for_cap(db, cap, **kw)
    if not ps:
        raise NotConfigured("No configured provider can do '%s'. Configure one in Settings → Providers." % cap)
    return ps[0]


def save(db, name, credentials=None, config=None, enabled=None):
    get(db, name)  # validates the name
    row = db.query(m.ModelProvider).filter_by(name=name).one_or_none()
    if row is None:
        row = m.ModelProvider(name=name)
        db.add(row)
    if credentials is not None:
        cur = decrypt(row.credentials_encrypted)
        for k, v in credentials.items():
            if v is None or (isinstance(v, str) and v.startswith("••••")):
                continue
            if v == "":
                cur.pop(k, None)
            else:
                cur[k] = v.strip()
        row.credentials_encrypted = encrypt(cur)
    if config is not None:
        row.config = {**(row.config or {}), **config}
    if enabled is not None:
        row.enabled = bool(enabled)
    row.status = "unchecked"
    db.flush()
    return row


def check(db, name):
    p = get(db, name)
    row = db.query(m.ModelProvider).filter_by(name=name).one_or_none()
    if row is None:
        row = m.ModelProvider(name=name)
        db.add(row)
    try:
        ok, detail = p.validate()
    except Exception as e:  # validation must never crash the settings page
        ok, detail = False, str(e)[:300]
    row.status = "ok" if ok else ("unconfigured" if not p.configured() else "invalid")
    row.status_detail = detail
    row.checked_at = datetime.now(timezone.utc)
    db.flush()
    return row


def public_view(db):
    rows = {r.name: r for r in db.query(m.ModelProvider).all()}
    out = []
    for f in FACTORIES:
        p = f()
        r = rows.get(p.name)
        p.load(r)
        d = p.describe()
        d.update(enabled=p.enabled, configured=p.configured(), status=(r.status if r else ("unchecked" if p.configured() else "unconfigured")),
                 status_detail=r.status_detail if r else None, checked_at=r.checked_at.isoformat() if r and r.checked_at else None,
                 config=p.config, credentials={f.name: (mask(p.creds.get(f.name, "")) if f.secret else p.creds.get(f.name, "")) for f in p.fields},
                 usd_per_unit=p.cost_per_unit())
        out.append(d)
    return out
