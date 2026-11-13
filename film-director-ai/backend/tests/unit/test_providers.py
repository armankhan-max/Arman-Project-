from unittest import mock

import pytest
import requests

from fda.agents.blender import clean_params
from fda.providers import registry
from fda.providers.base import NotConfigured, ProviderError, http
from fda.youtube.intelligence import iso_dur


def test_missing_key_is_not_configured(db):
    p = registry.get(db, "pexels")
    assert not p.configured()
    with pytest.raises(NotConfigured):
        p.search("ocean")
    ok, detail = p.validate()
    assert not ok and "Missing" in detail


def test_invalid_key_is_not_retried():
    resp = mock.Mock(status_code=401, text="bad key")
    with mock.patch("requests.request", return_value=resp) as rq:
        with pytest.raises(ProviderError) as e:
            http("GET", "https://api.example.com/x")
    assert e.value.code == "auth" and not e.value.retryable and rq.call_count == 1


def test_timeout_is_retryable():
    with mock.patch("requests.request", side_effect=requests.Timeout("slow")), mock.patch("time.sleep"):
        with pytest.raises(ProviderError) as e:
            http("GET", "https://api.example.com/x", retries=1)
    assert e.value.retryable


def test_credentials_saved_encrypted_and_masked(db):
    registry.save(db, "pexels", credentials={"api_key": "abcdef123456"})
    db.flush()
    p = registry.get(db, "pexels")
    assert p.configured() and p.creds["api_key"] == "abcdef123456"
    view = [x for x in registry.public_view(db) if x["name"] == "pexels"][0]
    assert view["credentials"]["api_key"].endswith("3456") and "abcdef" not in view["credentials"]["api_key"]
    registry.save(db, "pexels", credentials={"api_key": view["credentials"]["api_key"]})  # masked echo keeps the secret
    assert registry.get(db, "pexels").creds["api_key"] == "abcdef123456"


def test_no_silent_capability_substitution(db):
    assert all("image_to_video" in p.caps for p in registry.for_cap(db, "image_to_video", usable_only=False))
    assert registry.for_cap(db, "image_to_video") == []  # nothing configured → nothing usable


def test_blender_params_are_sanitised():
    out = clean_params("planet", {"color": "#ff0000", "bands": 9999, "rings": 1, "evil": "__import__('os')", "move": "orbit"})
    assert out == {"color": "#ff0000", "bands": 40, "rings": True, "move": "orbit"}
    with pytest.raises(ProviderError):
        clean_params("not_a_template", {})


def test_iso_duration():
    assert iso_dur("PT1H2M3S") == 3723 and iso_dur("PT45S") == 45 and iso_dur("P1DT1S") == 86401
