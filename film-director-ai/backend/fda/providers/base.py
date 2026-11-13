"""Provider framework: every external (or local) capability is an adapter registered here.

An adapter declares its capabilities, the credential fields it needs, whether it costs money, and how to
validate its configuration. Agents ask the registry for "a provider that can do X" instead of naming vendors."""
import os
import time
from dataclasses import dataclass, field

import requests

from fda.auth.security import decrypt


class ProviderError(RuntimeError):
    """Provider failed. `retryable` tells the workflow whether another attempt makes sense."""

    def __init__(self, msg, retryable=True, code=None):
        super().__init__(msg)
        self.retryable, self.code = retryable, code


class NotConfigured(ProviderError):
    def __init__(self, msg):
        super().__init__(msg, retryable=False, code="not_configured")


CAPS = ("llm", "embeddings", "text_to_image", "text_to_video", "image_to_video", "stock_video", "stock_image", "archive_image",
        "tts", "stt", "avatar", "lipsync", "music", "sfx", "youtube_public", "youtube_oauth", "web_search")


@dataclass
class CredField:
    name: str
    label: str
    env: str = ""
    secret: bool = True
    required: bool = True


@dataclass
class Provider:
    name: str = ""
    label: str = ""
    caps: tuple = ()
    paid: bool = False
    fields: tuple = ()
    docs: str = ""
    notes: str = ""
    verified: bool = True          # False = written against public docs, not yet exercised with real credentials
    unit: str = ""                 # what usage is counted in (tokens, images, seconds, characters…)
    creds: dict = field(default_factory=dict)
    config: dict = field(default_factory=dict)
    enabled: bool = True

    # ---------------------------------------------------------- configuration
    def load(self, row):
        self.creds = {}
        for f in self.fields:
            v = os.environ.get(f.env) if f.env else None
            if v:
                self.creds[f.name] = v
        if row is not None:
            self.creds.update({k: v for k, v in decrypt(row.credentials_encrypted).items() if v})
            self.config = dict(row.config or {})
            self.enabled = row.enabled
        return self

    def configured(self) -> bool:
        return all(self.creds.get(f.name) for f in self.fields if f.required)

    def need(self):
        if not self.enabled:
            raise NotConfigured("%s is disabled in Settings → Providers." % self.label)
        if not self.configured():
            missing = [f.label for f in self.fields if f.required and not self.creds.get(f.name)]
            raise NotConfigured("%s needs: %s. Add it in Settings → Providers." % (self.label, ", ".join(missing)))

    def validate(self) -> tuple[bool, str]:
        """Make a cheap real request to prove the credentials work."""
        return (self.configured(), "No validation call for this provider" if self.configured() else "Missing credentials")

    def cost_per_unit(self):
        """Owner-configured USD estimate per unit, or None (estimate unavailable). Never invented."""
        v = (self.config or {}).get("usd_per_unit")
        try:
            return float(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def estimate(self, units: float):
        c = self.cost_per_unit()
        return None if c is None else round(c * units, 4)

    def describe(self):
        return {"name": self.name, "label": self.label, "caps": list(self.caps), "paid": self.paid, "docs": self.docs, "notes": self.notes,
                "verified_integration": self.verified, "unit": self.unit, "fields": [{"name": f.name, "label": f.label, "secret": f.secret, "required": f.required, "env": f.env} for f in self.fields]}


# ------------------------------------------------------------------ http helper
def http(method, url, retries=2, timeout=60, ok=(200, 201, 202), **kw):
    last = None
    for i in range(retries + 1):
        try:
            r = requests.request(method, url, timeout=timeout, **kw)
        except requests.RequestException as e:
            last = ProviderError("Network error contacting %s: %s" % (url.split("/")[2], e))
            time.sleep(1.5 * (i + 1))
            continue
        if r.status_code in ok:
            return r
        body = r.text[:400]
        if r.status_code in (401, 403):
            raise ProviderError("Credentials rejected (%s): %s" % (r.status_code, body), retryable=False, code="auth")
        if r.status_code in (400, 404, 413, 422):
            raise ProviderError("Request rejected (%s): %s" % (r.status_code, body), retryable=False, code="bad_request")
        if r.status_code == 402:
            raise ProviderError("Provider reports insufficient credit (402)", retryable=False, code="payment")
        last = ProviderError("HTTP %s from %s: %s" % (r.status_code, url.split("/")[2], body), retryable=True, code="http")
        time.sleep(min(20, 2 ** i * (3 if r.status_code == 429 else 1.5)))
    raise last


def download(url, dest, timeout=180, max_mb=500, headers=None):
    with requests.get(url, stream=True, timeout=timeout, headers=headers or {"User-Agent": "FilmDirectorAI/1.0"}) as r:
        if r.status_code != 200:
            raise ProviderError("Download failed: HTTP %s" % r.status_code)
        n = 0
        with open(dest + ".part", "wb") as f:
            for chunk in r.iter_content(1 << 16):
                n += len(chunk)
                if n > max_mb << 20:
                    raise ProviderError("Downloaded file exceeds %d MB" % max_mb, retryable=False)
                f.write(chunk)
    if n < 500:
        raise ProviderError("Downloaded file is empty")
    os.replace(dest + ".part", dest)
    return dest
