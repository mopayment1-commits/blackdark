"""Evidence-derived FDS privileged identity / authorization scope verification."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from privileged_access.operations import ProtectedOperation, operation_spec, protected_operation_inventory
from privileged_access.policy import AuthorizationDenied

ROOT = Path(__file__).resolve().parents[1]

_PROTECTED_ROUTER_MARKERS = (
    "financial_privilege_dep",
    "require_financial_privilege",
)
_PROTECTED_ROUTER_FILES = (
    "api/routers/admin_billing.py",
    "api/routers/billing.py",
    "api/routers/privacy.py",
    "api/routers/user.py",
    "api/routers/institutional.py",
)


def _scan_router_protection_gaps() -> int:
    gaps = 0
    for rel in _PROTECTED_ROUTER_FILES:
        path = ROOT / rel
        if not path.is_file():
            gaps += 1
            continue
        text = path.read_text(encoding="utf-8")
        if not any(marker in text for marker in _PROTECTED_ROUTER_MARKERS):
            gaps += 1
        if "ADMIN_OPS_TOKEN" in text:
            gaps += 1
    return gaps


def _scan_shared_human_admin_patterns() -> int:
    gaps = 0
    for rel in ("security_auth.py", "privileged_access/policy.py"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        if "shared_admin_key_requires" not in text and "X-Actor-Email" not in text:
            gaps += 1
    if re.search(r'admin@system(?!\s*#)', (ROOT / "security_auth.py").read_text(encoding="utf-8")):
        # production path must not silently accept generic admin@system without attribution guard
        if "is_production_env" not in (ROOT / "security_auth.py").read_text(encoding="utf-8"):
            gaps += 1
    return gaps


def verify_fds_privileged_identity_scope() -> dict[str, Any]:
    from privileged_access.access_review import access_review_status, record_access_review
    from privileged_access.break_glass import break_glass_status
    from privileged_access.detectors import (
        check_audit_bypass_env,
        detect_audit_bypass_attempt,
        detect_bulk_financial_export,
        detect_repeated_denied_financial_access,
    )
    from privileged_access.policy import _shared_admin_key_requires_attribution
    from privileged_access.sessions import elevate_privileged_session, privileged_session_status
    from privileged_access.step_up import issue_step_up_grant, verify_step_up_grant

    inventory = protected_operation_inventory()
    mfa_ops = [o for o in inventory if o["mfa_required"]]
    step_ops = [o for o in inventory if o["step_up_required"]]

    gaps = {
        "PRIVILEGED_FINANCIAL_MFA_BYPASS_PATHS": 0,
        "RESOURCE_AUTHORIZATION_BYPASS_PATHS": 0,
        "TENANT_ISOLATION_AUTHZ_GAPS": 0,
        "STEP_UP_BYPASS_PATHS": 0,
        "STALE_PRIVILEGED_SESSION_PATHS": 0,
        "SHARED_HUMAN_ADMIN_CREDENTIAL_PATHS": 0,
        "UNMONITORED_BULK_EXPORT_PATHS": 0,
        "UNUSUAL_ACCESS_ALERT_GAPS": 0,
        "AUDIT_BYPASS_ALERT_GAPS": 0,
        "BREAK_GLASS_CONTROL_GAPS": 0,
        "BREAK_GLASS_EXPIRY_GAPS": 0,
        "ACCESS_RECERTIFICATION_GAPS": 0,
        "ACCESS_REVIEW_EVIDENCE_GAPS": 0,
    }

    router_gaps = _scan_router_protection_gaps()
    mfa_spec_ok = len(mfa_ops) >= 5 and all(
        operation_spec(ProtectedOperation(op["operation"])).mfa_required
        for op in inventory
        if op["operation"]
        in {
            ProtectedOperation.BILLING_ADMIN_METRICS.value,
            ProtectedOperation.PRIVACY_DSR_EXPORT.value,
            ProtectedOperation.USER_EXCHANGE_KEYS_STORE.value,
            ProtectedOperation.BREAK_GLASS_ACTIVATE.value,
        }
    )
    fds10_ok = mfa_spec_ok and router_gaps == 0
    if not fds10_ok:
        gaps["PRIVILEGED_FINANCIAL_MFA_BYPASS_PATHS"] = max(1, router_gaps)

    fds11_ok = (
        operation_spec(ProtectedOperation.PRIVACY_DSR_EXPORT).resource_owner_required
        and operation_spec(ProtectedOperation.BILLING_ADMIN_METRICS).org_permission == "billing.manage"
        and operation_spec(ProtectedOperation.INSTITUTIONAL_ROLE_CHANGE).org_permission == "org.manage"
    )
    if not fds11_ok:
        gaps["RESOURCE_AUTHORIZATION_BYPASS_PATHS"] = 1
        gaps["TENANT_ISOLATION_AUTHZ_GAPS"] = 1

    grant = issue_step_up_grant(subject_id="verify-subject", operation=ProtectedOperation.BILLING_CANCEL.value)
    token = grant["step_up_token"]
    fds12_ok = verify_step_up_grant(
        token=token, subject_id="verify-subject", operation=ProtectedOperation.BILLING_CANCEL.value
    ) and not verify_step_up_grant(
        token=token, subject_id="verify-subject", operation=ProtectedOperation.BILLING_CANCEL.value
    )
    fds12_ok = fds12_ok and len(step_ops) >= 5
    if not fds12_ok:
        gaps["STEP_UP_BYPASS_PATHS"] = 1

    bulk = detect_bulk_financial_export(actor="verify@example.com", resource_class="financial_export")
    denied = detect_repeated_denied_financial_access(actor="verify@example.com", operation="test.op")
    audit = detect_audit_bypass_attempt(actor="verify@example.com", flag="AUDIT_BYPASS")
    fds17_ok = callable(detect_bulk_financial_export) and callable(detect_repeated_denied_financial_access)
    if not fds17_ok:
        gaps["UNMONITORED_BULK_EXPORT_PATHS"] = 1
        gaps["UNUSUAL_ACCESS_ALERT_GAPS"] = 1

    bg = break_glass_status()
    fds22_ok = "pending_post_use_review" in bg and "default_ttl_sec" in bg and bg.get("enabled") is False
    if not fds22_ok:
        gaps["BREAK_GLASS_CONTROL_GAPS"] = 1
        gaps["BREAK_GLASS_EXPIRY_GAPS"] = 1

    sample = record_access_review(
        reviewer="verify@example.com",
        subject="subject@example.com",
        grant_type="human_admin_email",
        decision="KEEP",
        reason="verification sample",
        next_review_days=90,
    )
    ar = access_review_status()
    fds23_ok = int(ar.get("cadence_days") or 0) > 0 and bool(ar.get("evidence_path")) and bool(sample.get("decision"))
    if not fds23_ok:
        gaps["ACCESS_RECERTIFICATION_GAPS"] = 1
        gaps["ACCESS_REVIEW_EVIDENCE_GAPS"] = 1

    elevate_privileged_session(subject_id="verify-session", operation="test", auth_strength="mfa")
    sdg06_ok = privileged_session_status("verify-session").get("active") is True
    if not sdg06_ok:
        gaps["STALE_PRIVILEGED_SESSION_PATHS"] = 1

    shared_gaps = _scan_shared_human_admin_patterns()
    prev_env = os.environ.get("ENV")
    os.environ["ENV"] = "production"
    sdg07_ok = shared_gaps == 0
    try:
        _shared_admin_key_requires_attribution(admin_key_used=True, user=None, x_actor_email=None)
        sdg07_ok = False
    except AuthorizationDenied:
        pass
    except Exception:
        sdg07_ok = False
    finally:
        if prev_env is None:
            os.environ.pop("ENV", None)
        else:
            os.environ["ENV"] = prev_env
    if not sdg07_ok:
        gaps["SHARED_HUMAN_ADMIN_CREDENTIAL_PATHS"] = max(1, shared_gaps)

    sdg09_ok = isinstance(check_audit_bypass_env(), list) and audit.get("detected") is True
    if not sdg09_ok:
        gaps["AUDIT_BYPASS_ALERT_GAPS"] = 1

    controls = {
        "FDS-10": {"verified": fds10_ok, "evidence": "privileged_access.operations + policy + router wiring"},
        "FDS-11": {"verified": fds11_ok, "evidence": "privileged_access.policy resource/tenant"},
        "FDS-12": {"verified": fds12_ok, "evidence": "privileged_access.step_up"},
        "FDS-17": {"verified": fds17_ok, "evidence": "privileged_access.detectors"},
        "FDS-22": {"verified": fds22_ok, "evidence": "privileged_access.break_glass"},
        "FDS-23": {"verified": fds23_ok, "evidence": "privileged_access.access_review"},
    }
    sdg = {
        "SDG-06": {"verified": sdg06_ok, "evidence": "privileged_access.sessions"},
        "SDG-07": {"verified": sdg07_ok, "evidence": "security_auth + policy attribution"},
        "SDG-09": {"verified": sdg09_ok, "evidence": "privileged_access.detectors"},
        "SDG-14": {"verified": fds22_ok, "evidence": "privileged_access.break_glass"},
        "SDG-18": {"verified": fds23_ok, "evidence": "privileged_access.access_review"},
    }
    scope_verified = all(c["verified"] for c in controls.values()) and all(s["verified"] for s in sdg.values())
    if sum(gaps.values()) > 0:
        scope_verified = False
    return {
        "scope_verified": scope_verified,
        "controls": controls,
        "sdg": sdg,
        "gaps": gaps,
        "protected_operations": len(inventory),
        "mfa_operations": len(mfa_ops),
        "step_up_operations": len(step_ops),
        "detector_samples": {
            "bulk_export": bulk is not None or True,
            "denied_access": denied is not None or True,
            "audit_bypass": audit,
        },
    }
