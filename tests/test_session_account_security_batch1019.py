"""Tests — Session / Account Security 2FA Policy (#1019)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import session_account_security_1019 as sas


@pytest.fixture
def sas_seed() -> dict:
    return json.loads(Path("data/session_account_security_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset():
    sas.reset_session_security_state()
    audit = Path("data/mfa_audit.jsonl")
    if audit.is_file():
        audit.unlink()
    yield
    sas.reset_session_security_state()


def test_1019_status_no_standalone(sas_seed):
    status = sas.session_security_status_1019(seed=sas_seed)
    assert status["standalone_rejected"] is True
    assert status["policy"]["totp_only"] is True
    assert status["policy"]["sms_forbidden"] is True
    assert status["policy"]["backup_codes_count"] == 10


def test_tier_policy(sas_seed):
    assert sas.tier_mfa_requirement("free", seed=sas_seed) == "optional"
    assert sas.tier_mfa_requirement("pro", seed=sas_seed) == "strongly_recommended"
    assert sas.tier_mfa_requirement("institutional", seed=sas_seed) == "mandatory"


def test_institutional_login_blocked_without_mfa(sas_seed):
    with pytest.raises(ValueError, match="mandatory"):
        sas.assert_tier_mfa_at_login(
            tier="institutional", mfa_enabled=False, email="i@example.com", seed=sas_seed
        )


def test_free_login_allowed_without_mfa(sas_seed):
    result = sas.assert_tier_mfa_at_login(
        tier="free", mfa_enabled=False, email="f@example.com", seed=sas_seed
    )
    assert result["mfa_requirement"] == "optional"


def test_mfa_audit_append_only(sas_seed):
    sas.log_mfa_event("enable", user_id=42, actor="u@example.com", seed=sas_seed)
    sas.log_mfa_event("verify", user_id=42, seed=sas_seed)
    trail = sas.get_mfa_audit_trail(limit=10)
    assert trail["events_count"] >= 2
    assert trail["append_only"] is True
    assert Path("data/mfa_audit.jsonl").is_file()


def test_skip_admin_mfa_logs_bypass(monkeypatch, sas_seed):
    monkeypatch.setenv("SKIP_ADMIN_MFA", "true")
    sas.assert_no_skip_admin_mfa(seed=sas_seed)
    trail = sas.get_mfa_audit_trail()
    assert any(e.get("event_type") == "bypass_attempt" for e in trail["events"])


def test_rbac_elevation_requires_mfa(sas_seed):
    with pytest.raises(PermissionError):
        sas.assert_role_elevation_mfa(
            from_role="viewer", to_role="admin", mfa_verified=False, seed=sas_seed
        )
    sas.assert_role_elevation_mfa(
        from_role="viewer", to_role="admin", mfa_verified=True, seed=sas_seed
    )


def test_backup_codes_count(sas_seed):
    assert sas.backup_codes_count(seed=sas_seed) == 10


def test_recovery_codes_generate_10(monkeypatch):
    monkeypatch.setenv("SECRETS_MASTER_KEY", "unit-test-mfa-key-not-for-prod-32b!")
    from mfa_service import generate_recovery_codes

    codes = generate_recovery_codes()
    assert len(codes) == 10


def test_production_gate(sas_seed):
    gate = sas.check_production_gate_1019(seed=sas_seed)
    assert "admin_2fa_configured" in gate
    assert gate["checks"]["backup_codes_10"] is True


def test_e2e_1019(sas_seed):
    result = sas.run_session_security_e2e_1019(seed=sas_seed)
    assert result["all_passed"] is True
    assert result["ok"] is True
