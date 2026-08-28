"""Tests — Batch: #831 Account Security Layer (SEC-003 Sprint-0)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from bd_platform import infrastructure_account_security as sec


@pytest.fixture
def sec_seed() -> dict:
    return json.loads(Path("data/infrastructure_account_security_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    sec.reset_account_security_state()
    yield
    sec.reset_account_security_state()


def test_831_status(sec_seed):
    status = sec.account_security_status_831(seed=sec_seed)
    assert status["standalone_rejected"] is True
    assert status["control_ref"] == "SEC-003"
    assert status["policy"]["blocks_production_if_incomplete"] is True


def test_831_mfa_policy(sec_seed):
    mfa = sec.get_mfa_policy_831(seed=sec_seed)
    assert mfa["method"] == "totp"
    assert mfa["admin_mandatory"] is True
    assert mfa["no_sms"] is True
    assert mfa["backup_codes_encrypted"] is True


def test_831_no_skip_admin_mfa_in_production(sec_seed, monkeypatch):
    monkeypatch.setenv("SKIP_ADMIN_MFA", "true")
    monkeypatch.setenv("ENV", "production")
    result = sec.validate_admin_mfa_policy_831(seed=sec_seed)
    assert result["production_compliant"] is False


def test_831_session_policy(sec_seed):
    session = sec.get_session_policy_831(seed=sec_seed)
    assert session["idle_timeout_minutes"] == 30
    assert session["absolute_timeout_hours"] == 8
    assert session["backend_enforced"] is True


def test_831_concurrent_limits(sec_seed):
    assert sec.get_concurrent_session_limit_831("free", seed=sec_seed)["max_sessions"] == 1
    assert sec.get_concurrent_session_limit_831("pro", seed=sec_seed)["max_sessions"] == 3
    assert sec.get_concurrent_session_limit_831("institutional", seed=sec_seed)["max_sessions"] == 5


def test_831_password_reset_policy(sec_seed):
    reset = sec.get_password_reset_policy_831(seed=sec_seed)
    assert reset["expiry_minutes"] == 15
    assert reset["single_use"] is True
    assert reset["hashed_in_db"] is True


def test_831_password_reset_rate_limit(sec_seed):
    email = "rate@example.com"
    for _ in range(3):
        assert sec.check_password_reset_rate_limit_831(email, seed=sec_seed)["allowed"] is True
    assert sec.check_password_reset_rate_limit_831(email, seed=sec_seed)["allowed"] is False


def test_831_mfa_rate_limit(sec_seed):
    assert sec.check_mfa_rate_limit_831("user@example.com", seed=sec_seed)["max_per_5min"] == 5


def test_831_session_idle_check(sec_seed):
    from datetime import UTC, datetime, timedelta

    recent = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
    stale = (datetime.now(UTC) - timedelta(minutes=45)).isoformat()
    assert sec.check_session_idle_timeout_831(recent, seed=sec_seed)["idle_expired"] is False
    assert sec.check_session_idle_timeout_831(stale, seed=sec_seed)["idle_expired"] is True


def test_831_auth_audit(sec_seed):
    sec.record_auth_event_831("login", user_id=1, email="u@x.com", seed=sec_seed)
    trail = sec.get_auth_audit_trail_831(seed=sec_seed)
    assert trail["entry_count"] >= 2
    assert trail["audit_retention_years"] == 2


def test_831_non_custodial(sec_seed):
    nc = sec.account_security_status_831(seed=sec_seed)["policy"]["non_custodial"]
    assert nc["no_private_keys"] is True
    assert nc["password_reset_no_wallet_access"] is True


def test_831_identity_service_reset_ttl():
    from identity_service import TOKEN_TTL_MINUTES

    assert TOKEN_TTL_MINUTES["password_reset"] == 15


def test_831_e2e(sec_seed):
    e2e = sec.run_account_security_e2e_831(seed=sec_seed)
    assert e2e["all_passed"] is True
    assert len(e2e["checks"]) >= 20


@pytest.mark.asyncio
async def test_831_enforce_concurrent_sessions(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    from database import create_user, init_db, insert_user_session

    await init_db()
    user_id = await create_user("concurrent@example.com", "hash", "Test")
    from bd_platform.infrastructure_account_security import compute_session_expiry_831, enforce_concurrent_sessions_831

    exp = compute_session_expiry_831()
    for i in range(3):
        await insert_user_session(user_id, f"token_{i}", exp)
    result = await enforce_concurrent_sessions_831(user_id, "free")
    assert result["max_sessions"] == 1
