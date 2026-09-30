"""FDS-10/11/12/17/22/23 + SDG-06/07/09/14/18 behavior verification."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _user(user_id: int = 1, email: str = "alice@example.com") -> dict:
    return {"id": user_id, "email": email, "tier": "pro"}


def _mfa_setup(monkeypatch: pytest.MonkeyPatch) -> tuple[str, object]:
    import pyotp

    secret = pyotp.random_base32()
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "true")
    monkeypatch.setenv("ADMIN_TOTP_SECRET", secret)
    return secret, pyotp.TOTP(secret)


def _issue_step_up(subject: str, operation: str) -> str:
    from privileged_access.step_up import issue_step_up_grant

    return issue_step_up_grant(subject_id=subject, operation=operation)["step_up_token"]


@pytest.mark.asyncio
async def test_privileged_financial_operation_denied_without_mfa(monkeypatch: pytest.MonkeyPatch):
    from privileged_access.operations import ProtectedOperation
    from privileged_access.policy import AuthorizationContext, AuthorizationDenied, authorize_financial_operation

    _mfa_setup(monkeypatch)
    ctx = AuthorizationContext(
        subject_id="1",
        subject_email="alice@example.com",
        operation=ProtectedOperation.PRIVACY_DSR_EXPORT,
        resource_owner_id="1",
    )
    with pytest.raises(AuthorizationDenied, match="mfa_required"):
        await authorize_financial_operation(ctx, user=_user())


@pytest.mark.asyncio
async def test_valid_mfa_allows_only_authorized_resource(monkeypatch: pytest.MonkeyPatch):
    from privileged_access.operations import ProtectedOperation
    from privileged_access.policy import AuthorizationContext, AuthorizationDenied, authorize_financial_operation

    secret, totp = _mfa_setup(monkeypatch)
    token = _issue_step_up("1", ProtectedOperation.PRIVACY_DSR_EXPORT.value)
    ctx = AuthorizationContext(
        subject_id="1",
        subject_email="alice@example.com",
        operation=ProtectedOperation.PRIVACY_DSR_EXPORT,
        resource_owner_id="1",
    )
    result = await authorize_financial_operation(
        ctx,
        user=_user(),
        x_mfa_code=totp.now(),
        x_step_up_token=token,
    )
    assert result["authorized"] is True

    ctx_bad = AuthorizationContext(
        subject_id="2",
        subject_email="bob@example.com",
        operation=ProtectedOperation.PRIVACY_DSR_EXPORT,
        resource_owner_id="1",
    )
    with pytest.raises(AuthorizationDenied, match="resource_owner_mismatch"):
        await authorize_financial_operation(
            ctx_bad,
            user=_user(2, "bob@example.com"),
            x_mfa_code=totp.now(),
            x_step_up_token=_issue_step_up("2", ProtectedOperation.PRIVACY_DSR_EXPORT.value),
        )


@pytest.mark.asyncio
async def test_cross_tenant_financial_resource_access_denied(monkeypatch: pytest.MonkeyPatch):
    from privileged_access.operations import ProtectedOperation
    from privileged_access.policy import AuthorizationContext, AuthorizationDenied, authorize_financial_operation

    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    ctx = AuthorizationContext(
        subject_id="9",
        subject_email="outsider@example.com",
        operation=ProtectedOperation.PRIVACY_DSR_EXPORT,
        resource_owner_id="1",
        tenant_id="org-a",
    )
    token = _issue_step_up("9", ProtectedOperation.PRIVACY_DSR_EXPORT.value)
    with pytest.raises(AuthorizationDenied, match="resource_owner_mismatch"):
        await authorize_financial_operation(
            ctx,
            user=_user(9, "outsider@example.com"),
            x_step_up_token=token,
        )


@pytest.mark.asyncio
async def test_same_tenant_unauthorized_role_denied(monkeypatch: pytest.MonkeyPatch):
    from privileged_access.operations import ProtectedOperation
    from privileged_access.policy import AuthorizationContext, AuthorizationDenied, authorize_financial_operation

    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    monkeypatch.setattr("org_rbac.has_permission", lambda *_a, **_k: False)
    ctx = AuthorizationContext(
        subject_id="1",
        subject_email="alice@example.com",
        operation=ProtectedOperation.BILLING_ADMIN_METRICS,
        org_id="org-1",
        is_admin=False,
    )
    token = _issue_step_up("1", ProtectedOperation.BILLING_ADMIN_METRICS.value)
    with pytest.raises(AuthorizationDenied, match="missing_org_permission"):
        await authorize_financial_operation(
            ctx,
            user=_user(),
            x_step_up_token=token,
        )


@pytest.mark.asyncio
async def test_legitimate_authorized_access_succeeds(monkeypatch: pytest.MonkeyPatch):
    from privileged_access.operations import ProtectedOperation
    from privileged_access.policy import AuthorizationContext, authorize_financial_operation

    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    monkeypatch.setattr("org_rbac.has_permission", lambda *_a, **_k: True)
    token = _issue_step_up("1", ProtectedOperation.BILLING_ADMIN_METRICS.value)
    ctx = AuthorizationContext(
        subject_id="1",
        subject_email="alice@example.com",
        operation=ProtectedOperation.BILLING_ADMIN_METRICS,
        org_id="org-1",
        is_admin=False,
    )
    result = await authorize_financial_operation(ctx, user=_user(), x_step_up_token=token)
    assert result["authorized"] is True


@pytest.mark.asyncio
async def test_step_up_required_for_high_risk_action(monkeypatch: pytest.MonkeyPatch):
    from privileged_access.operations import ProtectedOperation
    from privileged_access.policy import AuthorizationContext, AuthorizationDenied, authorize_financial_operation

    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    ctx = AuthorizationContext(
        subject_id="1",
        subject_email="alice@example.com",
        operation=ProtectedOperation.BILLING_CANCEL,
        resource_owner_id="1",
    )
    with pytest.raises(AuthorizationDenied, match="step_up_required"):
        await authorize_financial_operation(ctx, user=_user())


def test_ordinary_login_does_not_satisfy_step_up():
    from privileged_access.step_up import verify_step_up_grant

    assert verify_step_up_grant(token=None, subject_id="1", operation="billing.cancel") is False


def test_expired_step_up_denied(monkeypatch: pytest.MonkeyPatch):
    from privileged_access import step_up as step_up_mod

    monkeypatch.setattr(step_up_mod, "_STEP_UP_TTL_SEC", 1)
    grant = step_up_mod.issue_step_up_grant(subject_id="1", operation="billing.cancel")
    time.sleep(1.1)
    assert step_up_mod.verify_step_up_grant(token=grant["step_up_token"], subject_id="1", operation="billing.cancel") is False


def test_step_up_cannot_be_blindly_replayed():
    from privileged_access.step_up import issue_step_up_grant, verify_step_up_grant

    grant = issue_step_up_grant(subject_id="1", operation="billing.cancel")
    token = grant["step_up_token"]
    assert verify_step_up_grant(token=token, subject_id="1", operation="billing.cancel") is True
    assert verify_step_up_grant(token=token, subject_id="1", operation="billing.cancel") is False


def test_step_up_audit_record_exists(tmp_path, monkeypatch: pytest.MonkeyPatch):
    from privileged_access import step_up as step_up_mod

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    step_up_mod.issue_step_up_grant(subject_id="audit-user", operation="billing.cancel")
    ledger = tmp_path / "step_up_grants.jsonl"
    assert ledger.is_file()
    rows = [json.loads(line) for line in ledger.read_text().splitlines()]
    assert any(row.get("event") == "step_up_issued" for row in rows)


def test_shared_human_admin_credential_cannot_bypass_attribution(monkeypatch: pytest.MonkeyPatch):
    from privileged_access.policy import AuthorizationDenied, _shared_admin_key_requires_attribution

    monkeypatch.setenv("ENV", "production")
    with pytest.raises(AuthorizationDenied, match="shared_admin_key_requires_x_actor_email"):
        _shared_admin_key_requires_attribution(admin_key_used=True, user=None, x_actor_email=None)


def test_bulk_financial_export_triggers_detector(monkeypatch: pytest.MonkeyPatch):
    from privileged_access.detectors import detect_bulk_financial_export
    from security_events import recent_security_events

    monkeypatch.setenv("BULK_FINANCIAL_EXPORT_THRESHOLD", "2")
    detect_bulk_financial_export(actor="bulk@example.com", resource_class="financial_export")
    result = detect_bulk_financial_export(actor="bulk@example.com", resource_class="financial_export")
    assert result is not None
    assert result["detector"] == "bulk_financial_export"
    kinds = {e.get("kind") for e in recent_security_events(limit=20)}
    assert "bulk_financial_export" in kinds


def test_unusual_access_triggers_security_event(monkeypatch: pytest.MonkeyPatch):
    from privileged_access.detectors import detect_repeated_denied_financial_access
    from security_events import recent_security_events

    monkeypatch.setenv("FINANCIAL_DENIED_THRESHOLD", "2")
    detect_repeated_denied_financial_access(actor="deny@example.com", operation="privacy.dsr.export")
    result = detect_repeated_denied_financial_access(actor="deny@example.com", operation="privacy.dsr.export")
    assert result is not None
    kinds = {e.get("kind") for e in recent_security_events(limit=20)}
    assert "unusual_financial_access" in kinds


def test_denied_bypass_attempts_observable():
    from privileged_access.detectors import detect_audit_bypass_attempt
    from security_events import recent_security_events

    detect_audit_bypass_attempt(actor="probe@example.com", flag="AUDIT_BYPASS")
    events = recent_security_events(limit=20, kind="audit_bypass_attempt")
    assert events


def test_audit_bypass_attempt_detected(monkeypatch: pytest.MonkeyPatch):
    from privileged_access.detectors import check_audit_bypass_env

    monkeypatch.setenv("SKIP_AUDIT", "true")
    findings = check_audit_bypass_env()
    assert findings
    assert any(f.get("detected") for f in findings)


def test_break_glass_disabled_by_default(monkeypatch: pytest.MonkeyPatch):
    from privileged_access.break_glass import activate_break_glass, break_glass_enabled

    monkeypatch.delenv("BREAK_GLASS_ENABLED", raising=False)
    assert break_glass_enabled() is False
    with pytest.raises(PermissionError, match="break_glass_disabled"):
        activate_break_glass(
            actor_id="1",
            actor_email="admin@example.com",
            reason="emergency maintenance window",
        )


@pytest.mark.asyncio
async def test_break_glass_requires_strong_auth_and_reason(monkeypatch: pytest.MonkeyPatch):
    from privileged_access.break_glass import activate_break_glass, break_glass_enabled
    from privileged_access.operations import ProtectedOperation
    from privileged_access.policy import AuthorizationContext, AuthorizationDenied, authorize_financial_operation

    monkeypatch.setenv("BREAK_GLASS_ENABLED", "true")
    assert break_glass_enabled() is True
    ctx = AuthorizationContext(
        subject_id="admin@example.com",
        subject_email="admin@example.com",
        operation=ProtectedOperation.BREAK_GLASS_ACTIVATE,
        is_admin=True,
    )
    with pytest.raises(AuthorizationDenied):
        await authorize_financial_operation(ctx, user={"email": "admin@example.com", "is_admin": True})
    with pytest.raises(ValueError, match="break_glass_reason_required"):
        activate_break_glass(actor_id="1", actor_email="admin@example.com", reason="short")


def test_break_glass_expires_automatically(monkeypatch: pytest.MonkeyPatch):
    from privileged_access import break_glass as bg_mod
    from privileged_access.break_glass import active_break_glass_for_actor, expire_break_glass_grants

    monkeypatch.setenv("BREAK_GLASS_ENABLED", "true")
    monkeypatch.setattr(bg_mod, "_DEFAULT_TTL_SEC", 1)
    rec = bg_mod.activate_break_glass(
        actor_id="admin-1",
        actor_email="admin@example.com",
        reason="incident response drill window",
    )
    assert active_break_glass_for_actor("admin-1") is not None
    time.sleep(1.1)
    expire_break_glass_grants()
    assert active_break_glass_for_actor("admin-1") is None
    assert rec.get("post_use_review_required") is True


def test_break_glass_creates_post_use_review_requirement(monkeypatch: pytest.MonkeyPatch):
    from privileged_access.break_glass import activate_break_glass, break_glass_status

    monkeypatch.setenv("BREAK_GLASS_ENABLED", "true")
    activate_break_glass(
        actor_id="admin-2",
        actor_email="admin@example.com",
        reason="mandatory post-use review drill",
    )
    status = break_glass_status()
    assert status["pending_post_use_review"] >= 1


def test_access_review_keep_revoke_modify(tmp_path, monkeypatch: pytest.MonkeyPatch):
    from privileged_access.access_review import list_access_reviews, record_access_review

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    for decision in ("KEEP", "REVOKE", "MODIFY"):
        rec = record_access_review(
            reviewer="reviewer@example.com",
            subject=f"{decision.lower()}@example.com",
            grant_type="human_admin_email",
            decision=decision,
            reason=f"decision {decision}",
        )
        assert rec["decision"] == decision
    rows = list_access_reviews()
    assert {r["decision"] for r in rows} == {"KEEP", "REVOKE", "MODIFY"}


def test_overdue_recertification_detectable(tmp_path, monkeypatch: pytest.MonkeyPatch):
    from privileged_access.access_review import overdue_reviews, record_access_review

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    record_access_review(
        reviewer="reviewer@example.com",
        subject="stale@example.com",
        grant_type="human_admin_email",
        decision="KEEP",
        reason="old review",
        next_review_days=0,
    )
    overdue = overdue_reviews(now=time.time() + 1)
    assert any(item["subject"] == "stale@example.com" for item in overdue)


def test_review_evidence_retained(tmp_path, monkeypatch: pytest.MonkeyPatch):
    from privileged_access.access_review import access_review_status, record_access_review

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    record_access_review(
        reviewer="reviewer@example.com",
        subject="retained@example.com",
        grant_type="human_admin_email",
        decision="KEEP",
        reason="retention check",
    )
    status = access_review_status()
    assert Path(status["evidence_path"]).is_file()


def test_previous_fds_security_governance_closure_remains_green():
    from governance.fds_data_boundary import verify_fds_data_boundary_scope

    result = verify_fds_data_boundary_scope()
    assert result["scope_verified"] is True


def test_fds_01_03_payment_architecture_remains_green():
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_payments_usd_security.py", "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_privileged_identity_scope_verifier_green():
    from governance.fds_privileged_identity import verify_fds_privileged_identity_scope

    result = verify_fds_privileged_identity_scope()
    assert result["scope_verified"] is True
    assert sum(result["gaps"].values()) == 0


def test_closure_script_produces_evidence():
    proc = subprocess.run(
        [sys.executable, "scripts/fds_privileged_identity_authorization_closure_verify.py"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    evidence = json.loads((ROOT / "FDS_PRIVILEGED_IDENTITY_AUTHORIZATION_CLOSURE_EVIDENCE.json").read_text())
    assert evidence["verdict"] == "FDS_PRIVILEGED_IDENTITY_AUTHORIZATION_CLOSED"
    assert evidence["summary"]["fds_controls_in_scope"] == 6
    for key in (
        "PRIVILEGED_FINANCIAL_MFA_BYPASS_PATHS",
        "RESOURCE_AUTHORIZATION_BYPASS_PATHS",
        "TENANT_ISOLATION_AUTHZ_GAPS",
        "STEP_UP_BYPASS_PATHS",
        "STALE_PRIVILEGED_SESSION_PATHS",
        "SHARED_HUMAN_ADMIN_CREDENTIAL_PATHS",
        "UNMONITORED_BULK_EXPORT_PATHS",
        "UNUSUAL_ACCESS_ALERT_GAPS",
        "AUDIT_BYPASS_ALERT_GAPS",
        "BREAK_GLASS_CONTROL_GAPS",
        "BREAK_GLASS_EXPIRY_GAPS",
        "ACCESS_RECERTIFICATION_GAPS",
        "ACCESS_REVIEW_EVIDENCE_GAPS",
    ):
        assert evidence["summary"][key] == 0
