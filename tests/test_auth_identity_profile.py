"""Identity: password policy, reset tokens, username, avatar, architecture."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest


def test_identity_architecture():
    from identity_service import identity_architecture, validate_password, validate_username

    arch = identity_architecture()
    assert arch["primary_authenticator"] == "email"
    assert arch["phone_auth"] is False
    assert arch["email_verification"] is True
    assert arch["password_reset"] is True
    validate_username("alex_trade")
    with pytest.raises(ValueError):
        validate_password("12345678")
    validate_password("correct-horse-battery-99", email="user@example.com")


def test_avatar_svg_and_initials():
    from identity_service import avatar_initials, default_avatar_svg

    assert avatar_initials("Ada Lovelace", "a@b.c") == "AL"
    svg = default_avatar_svg("Ada Lovelace", "ada@example.com")
    assert "AL" in svg
    assert "svg" in svg


def test_password_reset_flow(tmp_path, monkeypatch):
    import database
    from auth_service import hash_password, verify_password
    from identity_service import consume_auth_token, issue_auth_token, validate_password

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "id.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _run():
        await database.init_db()
        uid = await database.create_user(
            "resetme@example.com", hash_password("old-password-99"), "Reset Me"
        )
        raw = await issue_auth_token(uid, "password_reset")
        user_id = await consume_auth_token(raw, "password_reset")
        assert user_id == uid
        with pytest.raises(ValueError):
            await consume_auth_token(raw, "password_reset")
        validate_password("new-secure-pass-42", email="resetme@example.com")
        await database.update_user_profile_fields(
            uid, {"password_hash": hash_password("new-secure-pass-42"), "password_is_set": 1}
        )
        row = await database.fetch_user_by_id(uid)
        assert verify_password("new-secure-pass-42", row["password_hash"])

    asyncio.run(_run())


def test_register_requires_terms_and_sets_username(tmp_path, monkeypatch):
    import database
    from auth_service import register_user

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "reg.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _run():
        await database.init_db()
        with pytest.raises(ValueError, match="Terms"):
            await register_user("a@b.co", "strong-pass-12345", "A", accepted_terms=False)
        result = await register_user(
            "trader@example.com",
            "strong-pass-12345",
            "Trader One",
            username="trader_one",
            accepted_terms=True,
            plan="free",
        )
        assert result["user"]["username"] == "trader_one"
        assert result["selected_plan"] == "free"
        assert result["trial"] is None
        assert result["next"]["start_pro_trial"] is False
        assert result["email_verification"]["required"] is True
        assert result["token"]
        prof = await database.fetch_user_profile("trader@example.com")
        assert prof["username"] == "trader_one"

        pro = await register_user(
            "prouser@example.com",
            "strong-pass-12345",
            "Pro User",
            accepted_terms=True,
            plan="pro",
        )
        assert pro["selected_plan"] == "pro"
        assert pro["trial"]
        assert pro["trial"]["active"] is True
        assert pro["user"]["tier"] == "pro"

    asyncio.run(_run())


def test_login_template_has_mfa_and_oauth_and_forgot():
    html = Path("templates/login.html").read_text(encoding="utf-8")
    assert "mfaForm" in html
    assert ("Continue with Google" in html) or ("auth.google" in html)
    assert ("Forgot password" in html) or ("auth.forgot_pass" in html)
    assert "accepted_terms" in html or "regTerms" in html
    assert 'name="regPlan"' in html
    assert 'data-plan="pro"' in html
    assert 'data-plan="institutional"' in html
    assert Path("templates/profile.html").is_file()
    assert Path("templates/reset_password.html").is_file()
    assert Path("docs/AUTH_IDENTITY_PROFILE.md").is_file()


def test_oauth_state_roundtrip(tmp_path, monkeypatch):
    import database
    from identity_service import store_oauth_state_async, validate_oauth_state_async

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "oauth.db"))

    async def _run():
        await database.init_db()
        await store_oauth_state_async("google", "state123abc")
        await validate_oauth_state_async("google", "state123abc")
        with pytest.raises(ValueError):
            await validate_oauth_state_async("google", "state123abc")

    asyncio.run(_run())
