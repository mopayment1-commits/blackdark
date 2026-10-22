"""OWASP/NIST-aligned security controls (2026 hardening)."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("ENV", "development")
os.environ.setdefault("SESSION_TOKEN_PEPPER", "test-pepper-owasp-2026")
os.environ.setdefault("SECURITY_API_RATE_PER_MIN", "10000")
os.environ.setdefault("LOGIN_RATE_MAX_ATTEMPTS", "100")


def test_argon2id_hash_roundtrip():
    from password_kdf import hash_password, password_needs_rehash, verify_password

    stored = hash_password("Str0ng-Passw0rd!Example")
    assert stored.startswith("argon2id$")
    assert verify_password("Str0ng-Passw0rd!Example", stored)
    assert not verify_password("wrong", stored)
    assert not password_needs_rehash(stored)


def test_legacy_pbkdf2_still_verifies():
    import hashlib

    salt = "abc123"
    digest = hashlib.pbkdf2_hmac("sha256", b"legacy-pass", salt.encode(), 260_000).hex()
    stored = f"pbkdf2_sha256$260000${salt}${digest}"
    from password_kdf import password_needs_rehash, verify_password

    assert verify_password("legacy-pass", stored)
    assert password_needs_rehash(stored)


def test_csrf_token_validation():
    from security_csrf import mint_csrf_token, validate_csrf_token

    token = mint_csrf_token()
    assert validate_csrf_token(token)
    assert not validate_csrf_token("bad-token")


@pytest.mark.asyncio
async def test_password_history_blocks_reuse():
    from auth_service import hash_password
    from database import create_user, fetch_user_by_id, init_db
    from security_store import append_password_history, password_reused_recently

    await init_db()
    email = f"hist-{os.getpid()}@blackdark.test"
    h1 = hash_password("First-Password-99!")
    uid = await create_user(email, h1, "Hist")
    await append_password_history(uid, h1)
    assert await password_reused_recently(uid, "First-Password-99!")
    row = await fetch_user_by_id(uid)
    assert row is not None


def test_security_headers_include_hsts_and_csp():
    from starlette.requests import Request

    from security_middleware import security_headers_for

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("test", 443),
    }
    headers = security_headers_for(Request(scope))
    assert "Strict-Transport-Security" in headers
    hsts = headers["Strict-Transport-Security"]
    assert "max-age=31536000" in hsts
    assert "includeSubDomains" in hsts
    assert "preload" in hsts
    csp = headers["Content-Security-Policy"]
    assert "default-src 'none'" in csp
    assert "object-src 'none'" in csp
    assert headers.get("Cross-Origin-Embedder-Policy") == "credentialless"
    assert headers.get("X-XSS-Protection") == "0"
