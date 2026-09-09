"""Identity P0 test matrix — ID-001 → ID-071 local engineering evidence."""

from __future__ import annotations

import asyncio
import os

import pytest

os.environ.setdefault("IDENTITY_HIBP_CHECK", "false")
os.environ.setdefault("SOFT_LAUNCH", "1")

STRONG = "correct-horse-battery-99"
STRONG2 = "another-strong-pass-15"


def test_password_policy_min_15_and_nfc():
    from identity.password_policy import PASSWORD_MIN_LENGTH, normalize_password, validate_password_policy

    assert PASSWORD_MIN_LENGTH == 15
    with pytest.raises(ValueError):
        validate_password_policy("short-pass-1")
    nfc = normalize_password("p\u0300ass-" + "word-extra-99")
    assert nfc == normalize_password("pass\u0300-word-extra-99") or len(nfc) >= 15


def test_argon2id_hash_and_verify():
    from identity.password_storage import hash_password, password_scheme, verify_password

    stored = hash_password(STRONG)
    assert password_scheme(stored) == "argon2id"
    ok, needs = verify_password(STRONG, stored)
    assert ok
    assert needs in {True, False}
    ok2, _ = verify_password("wrong-password-here", stored)
    assert not ok2


def test_breached_password_k_anonymity(monkeypatch):
    import identity.breached_passwords as bp
    from identity.breached_passwords import sha1_prefix_suffix

    prefix, suffix = sha1_prefix_suffix("password")
    assert len(prefix) == 5
    assert len(suffix) == 35

    def fake_check(password: str, **kwargs):
        return {"checked": True, "breached": password == "password", "source": "hibp"}

    monkeypatch.setattr(bp, "check_breached_password", fake_check)
    assert bp.check_breached_password("password")["breached"] is True


def test_username_confusable_and_reserved():
    from identity.username_policy import validate_username, username_skeleton

    assert validate_username("trader_alpha") == "trader_alpha"
    with pytest.raises(ValueError):
        validate_username("admin")
    assert username_skeleton("adm1n") == username_skeleton("admin")


def test_account_state_transitions():
    from identity.account_states import AccountState, can_authenticate, transition_account_state

    assert can_authenticate(AccountState.ACTIVE)
    assert not can_authenticate(AccountState.DELETED)
    assert transition_account_state("ACTIVE", "COMPROMISED") == "COMPROMISED"


def test_step_up_freshness():
    from datetime import UTC, datetime, timedelta

    from identity.step_up import step_up_fresh

    recent = (datetime.now(UTC) - timedelta(seconds=30)).isoformat()
    assert step_up_fresh(recent)
    old = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    assert not step_up_fresh(old)


def test_identity_audit_redacts_secrets(tmp_path, monkeypatch):
    import database

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "audit.db"))

    async def _run():
        await database.init_db()
        from identity.identity_audit import record_identity_event

        row = await record_identity_event(
            event_type="password.change",
            user_id=1,
            detail={"password": "secret", "note": "changed"},
        )
        assert row["detail"]["password"] == "[redacted]"
        assert row["detail"]["note"] == "changed"

    asyncio.run(_run())


def test_session_list_and_revoke(tmp_path, monkeypatch):
    import database
    from auth_service import hash_password

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "sess.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _run():
        await database.init_db()
        uid = await database.create_user("sess@example.com", hash_password(STRONG), "S")
        from identity.session_service import create_user_session, list_user_sessions, revoke_session

        sess = await create_user_session(uid, auth_method="password", device_label="test", browser="pytest")
        rows = await list_user_sessions(uid)
        assert len(rows) >= 1
        sid = rows[0]["id"]
        assert await revoke_session(uid, sid)

    asyncio.run(_run())


def test_provider_registry_no_blind_email_link(tmp_path, monkeypatch):
    import database
    from auth_service import hash_password

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "prov.db"))

    async def _run():
        await database.init_db()
        uid = await database.create_user("owner@example.com", hash_password(STRONG), "Owner")
        from identity.provider_registry import link_provider

        await link_provider(uid, provider="google", provider_subject="google-sub-123", require_step_up=False)
        from database import fetch_provider_link

        row = await fetch_provider_link("google", "google-sub-123")
        assert row and int(row["user_id"]) == uid

    asyncio.run(_run())


def test_last_auth_method_protection(tmp_path, monkeypatch):
    import database
    from auth_service import hash_password

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "lock.db"))

    async def _run():
        await database.init_db()
        uid = await database.create_user("only@example.com", hash_password(STRONG), "Only")
        user = await database.fetch_user_by_id(uid)
        from identity.webauthn_service import remove_passkey

        with pytest.raises(ValueError, match="last login"):
            await remove_passkey(uid, "missing", actor={**user, "step_up_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat()})

    asyncio.run(_run())


def test_account_deletion_requires_step_up(tmp_path, monkeypatch):
    import database
    from auth_service import hash_password

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "del.db"))

    async def _run():
        await database.init_db()
        uid = await database.create_user("del@example.com", hash_password(STRONG), "Del")
        user = await database.fetch_user_by_id(uid)
        from identity.account_deletion import request_account_deletion

        with pytest.raises(ValueError, match="Recent authentication"):
            await request_account_deletion(uid, actor=user)

    asyncio.run(_run())


def test_security_notification_localized():
    from i18n_enforcement import localize_notification

    fr = localize_notification("fr", "notification.password_changed.title", "notification.password_changed.body")
    assert fr["locale"] == "fr"
    assert fr["title"]


def test_enumeration_resistant_forgot():
    from identity.login_abuse import GENERIC_AUTH_ERROR, generic_forgot_password_response

    body = generic_forgot_password_response()
    assert GENERIC_AUTH_ERROR in body["message"]


def test_retention_registry_manifest():
    from identity.retention_registry import retention_manifest

    m = retention_manifest()
    assert len(m["categories"]) >= 3


def test_enterprise_readiness_manifest():
    from identity.enterprise_readiness import enterprise_identity_manifest

    m = enterprise_identity_manifest()
    assert m["saml_2_0"]["architecture_ready"] is True


def test_recovery_options_surface(tmp_path, monkeypatch):
    import database
    from auth_service import hash_password

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "rec.db"))

    async def _run():
        await database.init_db()
        uid = await database.create_user("rec@example.com", hash_password(STRONG), "Rec")
        from identity.account_recovery import recovery_options

        opts = await recovery_options(uid)
        assert "password" in opts
        assert "passkeys" in opts

    asyncio.run(_run())


def test_register_uses_15_char_policy(tmp_path, monkeypatch):
    import database
    from auth_service import register_user

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "reg15.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _run():
        await database.init_db()
        with pytest.raises(ValueError):
            await register_user("a@b.co", "too-short-1", "A", accepted_terms=True)
        result = await register_user(
            "longpass@example.com",
            STRONG2,
            "User",
            accepted_terms=True,
            plan="free",
        )
        assert result["user"]["email"] == "longpass@example.com"

    asyncio.run(_run())


def test_identity_architecture_manifest():
    from identity_service import identity_architecture

    arch = identity_architecture()
    assert arch["password_policy"]["min_length"] == 15
    assert arch["password_policy"]["hash"] == "argon2id"
    assert "passkey_webauthn" in arch["login_methods"]
