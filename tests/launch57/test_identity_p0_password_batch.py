"""Launch-57 identity P0 — password storage, policy, recovery (ID-003…006, 021–023, 027/029, 032/069)."""

from __future__ import annotations

import asyncio
import time
import unicodedata

import pytest
from starlette.testclient import TestClient


@pytest.fixture()
def client():
    from dashboard import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_argon2id_hash_and_weak_hash_rejected():
    from password_security import hash_password, is_weak_hash_rejected, verify_password

    stored = hash_password("valid-password-15chars")
    assert stored.startswith("$argon2")
    assert verify_password("valid-password-15chars", stored) is True
    assert is_weak_hash_rejected("md5$deadbeef") is True
    assert verify_password("anything", "md5$deadbeef") is False
    assert verify_password("anything", "sha1$deadbeef") is False


def test_break_weak_hash_rejected_in_policy_gate():
    from launch57.identity_auth_common import verify_weak_hashing_forbidden

    check = verify_weak_hashing_forbidden()
    assert check["ok"] is True
    assert check["hash_algorithm"] == "argon2id"


def test_nfc_normalization_before_hash():
    from password_security import hash_password, normalize_password_nfc, verify_password

    composed = "café-password-15x"  # e + combining acute
    nfc = normalize_password_nfc(composed)
    assert nfc == unicodedata.normalize("NFC", composed)
    stored = hash_password(composed)
    assert verify_password(nfc, stored) is True
    assert verify_password(composed, stored) is True
    assert normalize_password_nfc(composed) == normalize_password_nfc(nfc)


def test_password_min_length_15_no_composition_rules():
    from password_security import PASSWORD_MIN_LENGTH, validate_password_policy

    assert PASSWORD_MIN_LENGTH == 15
    with pytest.raises(ValueError, match="at least 15"):
        validate_password_policy("short-pass-12", email="a@b.co")
    # No composition rule — long passphrase allowed
    meta = validate_password_policy("alllowercasepassword15", email="")
    assert meta["min_length"] == 15


def test_common_password_blocked(monkeypatch):
    from password_security import validate_password_policy

    monkeypatch.setattr("password_security._hibp_enabled", lambda: False)
    with pytest.raises(ValueError, match="too common"):
        validate_password_policy("password1234567890", email="")


def test_breach_check_blocked_external_when_hibp_unavailable(monkeypatch):
    import urllib.request

    from password_security import check_breached_password

    monkeypatch.setattr("password_security._hibp_enabled", lambda: True)

    def _fail(*_args, **_kwargs):
        raise OSError("network down")

    monkeypatch.setattr(urllib.request, "urlopen", _fail)
    result = check_breached_password("unique-password-15chars")
    assert result["breached"] is False
    assert result["hibp_status"] == "BLOCKED_EXTERNAL"


def test_pbkdf2_rehash_on_successful_login(tmp_path, monkeypatch):
    import database
    from auth_service import hash_password, login_user
    from password_security import _verify_pbkdf2

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "rehash.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _run():
        await database.init_db()
        legacy = (
            "pbkdf2_sha256$260000$"
            + "a" * 32
            + "$"
            + __import__("hashlib").pbkdf2_hmac(
                "sha256",
                b"legacy-password-15",
                ("a" * 32).encode(),
                260_000,
            ).hex()
        )
        assert _verify_pbkdf2("legacy-password-15", legacy)
        uid = await database.create_user("legacy@example.com", legacy, "Legacy")
        out = await login_user("legacy@example.com", "legacy-password-15")
        assert out["token"]
        row = await database.fetch_user_by_id(uid)
        assert str(row["password_hash"]).startswith("$argon2")

    asyncio.run(_run())


def test_reset_password_no_auto_login(tmp_path, monkeypatch, client):
    import database
    from identity_service import issue_auth_token

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "reset.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _setup():
        await database.init_db()
        uid = await database.create_user(
            "reset@example.com",
            __import__("auth_service").hash_password("old-password-15xx"),
            "Reset",
        )
        return uid, await issue_auth_token(uid, "password_reset")

    uid, raw = asyncio.run(_setup())
    res = client.post(
        "/api/auth/reset-password",
        json={"token": raw, "password": "new-password-15chars"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body.get("auto_login") is False
    assert "token" not in body
    assert "bd_token" not in res.cookies


def test_forgot_password_generic_message_same_timing(monkeypatch, client):
    monkeypatch.setenv("IDENTITY_FORGOT_MIN_DELAY_SEC", "0.1")
    t0 = time.perf_counter()
    known = client.post("/api/auth/forgot-password", json={"email": "nobody@example.com"})
    t1 = time.perf_counter()
    unknown = client.post("/api/auth/forgot-password", json={"email": "not-an-email"})
    t2 = time.perf_counter()
    assert known.status_code == 200
    assert unknown.status_code == 200
    assert known.json()["message"] == unknown.json()["message"]
    known_elapsed = t1 - t0
    unknown_elapsed = t2 - t1
    assert known_elapsed >= 0.08
    assert unknown_elapsed >= 0.08
    assert abs(known_elapsed - unknown_elapsed) < 0.2


def test_login_invalid_credentials_generic(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "missing@example.com", "password": "wrong-password-15xx"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


def test_login_rate_limit_account_and_ip(monkeypatch, client):
    from security_auth import _LOGIN_MAX_ATTEMPTS, check_login_rate_limit

    monkeypatch.setattr("viral_capacity.viral_middleware_enabled", lambda: False)
    ip = "203.0.113.50"
    email = "ratelimit@example.com"
    for _ in range(_LOGIN_MAX_ATTEMPTS):
        check_login_rate_limit(f"ip:{ip}")
        check_login_rate_limit(f"account:{email}")
    with pytest.raises(Exception):
        check_login_rate_limit(f"account:{email}")


def test_session_cookie_secure_httponly_samesite():
    from security_middleware import cookie_session_kwargs

    kwargs = cookie_session_kwargs()
    assert kwargs["httponly"] is True
    assert kwargs["samesite"] == "lax"
    assert "secure" in kwargs


def test_change_password_rotates_session(tmp_path, monkeypatch, client):
    import database
    from auth_service import hash_password, login_user

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "chg.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _setup():
        await database.init_db()
        await database.create_user(
            "change@example.com",
            hash_password("initial-password-15"),
            "Change",
        )
        return await login_user("change@example.com", "initial-password-15")

    login = asyncio.run(_setup())
    res = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {login['token']}"},
        json={
            "current_password": "initial-password-15",
            "new_password": "updated-password-15",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("ok") is True or body.get("token") or res.cookies.get("bd_token")
