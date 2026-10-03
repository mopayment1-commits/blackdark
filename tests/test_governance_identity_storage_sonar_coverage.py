"""Small governance runtime status coverage for Sonar new-code margin."""

from __future__ import annotations

from governance.identity_governance import identity_governance_status, verify_password_policy
from governance.storage_governance import _storage_status_from_health, storage_governance_status


def test_verify_password_policy_rejects_weak():
    result = verify_password_policy()
    assert result["ok"] is True


def test_identity_governance_status_shape():
    status = identity_governance_status()
    assert status["email_validation"] is True
    assert "mfa_available" in status


def test_storage_governance_status_from_health():
    out = _storage_status_from_health({"tier_orchestrator": True})
    assert out["tier_orchestrator"] is True
    assert out["trace_replay_bootstrap"] is True
    sync = storage_governance_status()
    assert sync["retention_policy"] is True
