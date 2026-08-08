"""Security module tests."""


from secrets_vault import decrypt_secret, encrypt_secret, mask_secret
from security_auth import (
    hash_session_token,
    is_admin_user,
    verify_admin_key,
)


def test_encrypt_decrypt_roundtrip(monkeypatch):
    monkeypatch.setenv("SECRETS_MASTER_KEY", "test-master-key-for-unit-tests-only")
    plain = "sk-live-binance-secret-key-12345"
    enc = encrypt_secret(plain)
    assert enc != plain
    assert decrypt_secret(enc) == plain


def test_mask_secret():
    assert mask_secret("abcdefghijklmnop") == "abcd...mnop"


def test_session_token_hash_deterministic():
    h1 = hash_session_token("abc123")
    h2 = hash_session_token("abc123")
    assert h1 == h2
    assert len(h1) == 64


def test_admin_key_verify(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "super-secret-admin")
    assert verify_admin_key("super-secret-admin") is True
    assert verify_admin_key("wrong") is False


def test_is_admin_user():
    assert is_admin_user({"email": "x@y.com"}) is False
