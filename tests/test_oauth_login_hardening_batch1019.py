"""Tests — OAuth Social Login Hardening (#1019)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import oauth_login_hardening as olh


@pytest.fixture
def olh_seed() -> dict:
    return json.loads(Path("data/session_account_security_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    monkeypatch.setenv("SECRETS_MASTER_KEY", "unit-test-oauth-key-not-for-prod-32b!")
    olh.reset_oauth_login_state()
    audit = Path("data/oauth_audit.jsonl")
    if audit.is_file():
        audit.unlink()
    yield
    olh.reset_oauth_login_state()


def test_oauth_status_no_standalone(olh_seed):
    status = olh.oauth_login_status(seed=olh_seed)
    assert status["standalone_rejected"] is True
    assert status["policy"]["optional_only"] is True
    assert status["policy"]["admin_oauth_forbidden"] is True
    assert set(status["providers"]["allowed"]) == {"google", "github", "twitter"}


def test_allowed_scopes_google(olh_seed):
    scope = olh.validate_requested_scopes("google", "openid email profile", seed=olh_seed)
    assert "openid" in scope


def test_forbidden_scope_rejected(olh_seed):
    with pytest.raises(ValueError, match="Forbidden|exceeds"):
        olh.validate_requested_scopes("github", "read:user user:email repo", seed=olh_seed)


def test_admin_oauth_forbidden(monkeypatch, olh_seed):
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")
    with pytest.raises(PermissionError):
        olh.assert_admin_oauth_forbidden("admin@example.com", seed=olh_seed)


def test_token_encryption_roundtrip():
    enc = olh.encrypt_oauth_token("oauth-access-secret")
    assert enc != "oauth-access-secret"
    assert olh.decrypt_oauth_token(enc) == "oauth-access-secret"


def test_oauth_audit_append_only(olh_seed):
    olh.log_oauth_event("start", provider="google", scope="openid email profile", seed=olh_seed)
    olh.log_oauth_event("login", user_id=1, email="u@example.com", provider="google", seed=olh_seed)
    trail = olh.get_oauth_audit_trail(limit=10)
    assert trail["events_count"] >= 2
    assert trail["append_only"] is True
    assert Path("data/oauth_audit.jsonl").is_file()


def test_provider_normalization(olh_seed):
    assert olh.assert_provider_allowed("x", seed=olh_seed) == "twitter"


@pytest.mark.asyncio
async def test_unlink_preserves_account(monkeypatch, olh_seed):
    removed = {"called": False}

    async def _delete(uid: int, provider: str, *, tenant_id: str = "platform") -> bool:
        removed["called"] = True
        return True

    async def _fetch(uid: int):
        return {"email": "u@example.com"}

    monkeypatch.setattr("database.delete_oauth_provider_link", _delete)
    monkeypatch.setattr("database.fetch_user_by_id", _fetch)
    result = await olh.unlink_oauth_provider(9, "google", seed=olh_seed)
    assert result["account_preserved"] is True
    assert result["unlinked"] is True
    assert removed["called"] is True


def test_production_gate(olh_seed):
    gate = olh.check_oauth_login_gate(seed=olh_seed)
    assert gate["ok"] is True
    assert gate["blocks_production"] is False
    assert gate["sprint"] == 1


def test_e2e(olh_seed):
    result = olh.run_oauth_login_e2e(seed=olh_seed)
    assert result["all_passed"] is True


def test_oauth_service_status_includes_policy(monkeypatch):
    monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_ID", raising=False)
    from oauth_service import oauth_status

    status = oauth_status()
    assert status["optional"] is True
    assert status.get("policy") is not None
