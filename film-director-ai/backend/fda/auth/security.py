"""Password hashing (scrypt), signed session tokens and encryption of stored credentials."""
import base64
import hashlib
import hmac
import json
import os
import time

from cryptography.fernet import Fernet, InvalidToken
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner

from fda.config import get_settings

SESSION_COOKIE = "fda_session"
CSRF_HEADER = "x-fda-request"


def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(pw.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)
    return "scrypt$%s$%s" % (base64.b64encode(salt).decode(), base64.b64encode(dk).decode())


def verify_password(pw: str, stored: str) -> bool:
    try:
        _, s, d = stored.split("$")
        dk = hashlib.scrypt(pw.encode(), salt=base64.b64decode(s), n=2 ** 14, r=8, p=1, dklen=32)
        return hmac.compare_digest(dk, base64.b64decode(d))
    except Exception:
        return False


def _signer():
    return TimestampSigner(get_settings().secret_key, salt="fda-session")


def make_session(user_id: str) -> str:
    return _signer().sign(user_id).decode()


def read_session(token: str | None) -> str | None:
    if not token:
        return None
    try:
        return _signer().unsign(token, max_age=get_settings().session_hours * 3600).decode()
    except (BadSignature, SignatureExpired):
        return None


def _fernet():
    key = hashlib.sha256(("fda-credentials|" + get_settings().secret_key).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt(obj: dict) -> bytes:
    return _fernet().encrypt(json.dumps(obj).encode())


def decrypt(blob: bytes | None) -> dict:
    if not blob:
        return {}
    try:
        return json.loads(_fernet().decrypt(bytes(blob)).decode())
    except (InvalidToken, ValueError):
        return {}


def mask(value: str) -> str:
    if not value:
        return ""
    return "••••" + value[-4:] if len(value) > 8 else "••••"


class RateLimiter:
    """Small in-process sliding window limiter (per key)."""

    def __init__(self, limit: int, window_s: float):
        self.limit, self.window, self.hits = limit, window_s, {}

    def allow(self, key: str) -> bool:
        t = time.time()
        q = [x for x in self.hits.get(key, []) if t - x < self.window]
        if len(q) >= self.limit:
            self.hits[key] = q
            return False
        q.append(t)
        self.hits[key] = q
        return True
