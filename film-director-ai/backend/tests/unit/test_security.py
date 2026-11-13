from fda.auth.security import decrypt, encrypt, hash_password, make_session, mask, read_session, verify_password


def test_password_hash_roundtrip():
    h = hash_password("correct horse")
    assert h.startswith("scrypt$") and "correct horse" not in h
    assert verify_password("correct horse", h)
    assert not verify_password("wrong", h)


def test_session_signing():
    tok = make_session("abc")
    assert read_session(tok) == "abc"
    assert read_session(tok + "x") is None
    assert read_session(None) is None


def test_credential_encryption():
    blob = encrypt({"api_key": "sk-secret"})
    assert b"sk-secret" not in blob
    assert decrypt(blob) == {"api_key": "sk-secret"}
    assert decrypt(b"garbage") == {}
    assert mask("abcdefghijk").endswith("hijk") and "abc" not in mask("abcdefghijk")
