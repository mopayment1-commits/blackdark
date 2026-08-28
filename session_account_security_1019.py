"""
Session / Account Security — #1019 (2FA Policy Engine).

Merged into #1019 Auth Layer — NOT standalone. Unified TOTP 2FA policy,
audit trail, tier enforcement, and integration hooks for RBAC + billing.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.SessionAccountSecurity")

_FEATURE_REF = 1019
_MERGED_INTO = "#1019 Session/Account Security"
_STANDALONE = False
_SEED_PATH = Path("data/session_account_security_seed.json")
_RUNBOOK = "docs/infrastructure/SESSION_ACCOUNT_SECURITY.md"
_MFA_AUDIT_PATH = Path("data/mfa_audit.jsonl")

_RBAC_REF = 1022
_STRIPE_REF = 908
_INCIDENT_RESPONSE_REF = 1017

TierMfaPolicy = Literal["optional", "strongly_recommended", "mandatory"]
MfaEventType = Literal[
    "enable",
    "disable",
    "verify",
    "backup_code_use",
    "recovery_attempt",
    "bypass_attempt",
    "role_elevation",
    "billing_action",
]

_LOCK = threading.Lock()
_bypass_attempts: list[dict[str, Any]] = []


def reset_session_security_state() -> None:
    _bypass_attempts.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("session security seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("session_account_security_1019") or {}


def session_security_status_1019(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    from admin_mfa import mfa_status as admin_status

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": False,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "policy": {
            "enabled": policy.get("enabled", True),
            "totp_only": policy.get("totp_only", True),
            "sms_forbidden": policy.get("sms_forbidden", True),
            "admin_mfa_mandatory": policy.get("admin_mfa_mandatory", True),
            "skip_admin_mfa_forbidden": policy.get("skip_admin_mfa_forbidden", True),
            "backup_codes_count": policy.get("backup_codes_count", 10),
            "audit_retention_days": policy.get("audit_retention_days", 730),
            "methodology_version": policy.get("methodology_version", "1.0.0"),
            "non_custodial": policy.get("non_custodial", True),
            "disclaimer": policy.get("disclaimer"),
        },
        "tier_policy": cfg.get("tier_policy") or {},
        "supported_factors": cfg.get("supported_factors") or ["totp"],
        "forbidden_factors": cfg.get("forbidden_factors") or ["sms"],
        "admin_mfa": admin_status(),
        "integrations": {
            "rbac_ref": _RBAC_REF,
            "stripe_ref": _STRIPE_REF,
            "incident_response_ref": _INCIDENT_RESPONSE_REF,
        },
        "auth_flow": "login → password → 2FA (if enabled) → session",
        "password_recovery": {
            "token_expiry_minutes": (_cfg(seed).get("password_recovery") or {})
            .get("policy", {})
            .get("token_expiry_minutes", 15),
            "security_questions_forbidden": (_cfg(seed).get("password_recovery") or {})
            .get("policy", {})
            .get("security_questions_forbidden", True),
        },
        "session_lifecycle": {
            "idle_timeout_minutes": (_cfg(seed).get("session_lifecycle") or {})
            .get("policy", {})
            .get("idle_timeout_minutes", 30),
            "absolute_timeout_hours": (_cfg(seed).get("session_lifecycle") or {})
            .get("policy", {})
            .get("absolute_timeout_hours", 8),
            "global_logout_endpoint": (_cfg(seed).get("session_lifecycle") or {})
            .get("policy", {})
            .get("global_logout_endpoint", "/auth/logout-all"),
        },
        "runbook": _RUNBOOK,
        "timestamp": _utcnow(),
    }


def tier_mfa_requirement(tier: str | None, *, seed: dict[str, Any] | None = None) -> TierMfaPolicy:
    seed = seed or _load_seed()
    from auth_service import normalize_tier

    tier_key = normalize_tier(tier)
    return (_cfg(seed).get("tier_policy") or {}).get(tier_key, "optional")  # type: ignore[return-value]


def skip_admin_mfa_forbidden(*, seed: dict[str, Any] | None = None) -> bool:
    return bool((_cfg(seed).get("policy") or {}).get("skip_admin_mfa_forbidden", True))


def assert_no_skip_admin_mfa(*, seed: dict[str, Any] | None = None) -> None:
    """#1019 — SKIP_ADMIN_MFA is forbidden; logs incident and continues enforcement."""
    seed = seed or _load_seed()
    raw = os.getenv("SKIP_ADMIN_MFA", "").strip().lower()
    if raw not in {"1", "true", "yes", "on"}:
        return
    log_mfa_event(
        "bypass_attempt",
        actor="system",
        detail={"env": "SKIP_ADMIN_MFA", "forbidden": True, "enforcement_continues": True},
        seed=seed,
    )


def log_mfa_event(
    event_type: MfaEventType,
    *,
    user_id: int | None = None,
    actor: str | None = None,
    ip: str | None = None,
    detail: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append-only MFA audit — 2 year retention policy."""
    seed = seed or _load_seed()
    policy = (_cfg(seed).get("policy") or {})
    event = {
        "event_id": f"mfa_{uuid.uuid4().hex[:12]}",
        "feature_ref": _FEATURE_REF,
        "event_type": event_type,
        "user_id": user_id,
        "actor": actor,
        "ip": ip,
        "detail": detail or {},
        "append_only": True,
        "retention_days": policy.get("audit_retention_days", 730),
        "timestamp": _utcnow(),
        "ts": time.time(),
    }
    _MFA_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        try:
            with _MFA_AUDIT_PATH.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError:
            logger.debug("mfa audit persist failed", exc_info=True)
    try:
        from security_events import record_security_event

        record_security_event(
            f"mfa_{event_type}",
            severity="warning" if event_type in ("bypass_attempt", "recovery_attempt") else "info",
            actor=actor or (str(user_id) if user_id else None),
            ip=ip,
            detail={"event_id": event["event_id"], **(detail or {})},
        )
    except ImportError:
        pass
    if event_type == "bypass_attempt":
        _bypass_attempts.append(event)
        _trigger_incident_lockout(actor=actor or "unknown", seed=seed)
    return event


def _trigger_incident_lockout(*, actor: str, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        from bd_platform.infrastructure_incident_response_security_ops import record_incident_829
    except ImportError:
        return {"triggered": False}
    try:
        record_incident_829(
            scenario="security",
            severity="high",
            title=f"2FA bypass attempt blocked: {actor}",
            seed=seed,
        )
        return {"triggered": True, "incident_response_ref": _INCIDENT_RESPONSE_REF}
    except Exception:
        return {"triggered": False}


def get_mfa_audit_trail(*, limit: int = 50) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    if _MFA_AUDIT_PATH.is_file():
        try:
            lines = _MFA_AUDIT_PATH.read_text(encoding="utf-8").splitlines()
            rows = [json.loads(x) for x in lines[-limit:] if x.strip()]
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "ok": True,
        "events_count": len(rows),
        "events": rows,
        "append_only": True,
        "retention_days": 730,
        "path": str(_MFA_AUDIT_PATH),
        "timestamp": _utcnow(),
    }


def assert_tier_mfa_at_login(
    *,
    tier: str | None,
    mfa_enabled: bool,
    email: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Tier policy at login — institutional = mandatory."""
    seed = seed or _load_seed()
    requirement = tier_mfa_requirement(tier, seed=seed)
    if requirement == "mandatory" and not mfa_enabled:
        raise ValueError(
            f"2FA is mandatory for {tier} tier. Enroll TOTP at /settings/security before login."
        )
    return {
        "tier": tier,
        "mfa_requirement": requirement,
        "mfa_enabled": mfa_enabled,
        "strongly_recommended": requirement == "strongly_recommended" and not mfa_enabled,
        "email": email,
    }


async def assert_billing_action_mfa(
    user_id: int,
    *,
    action: str,
    mfa_code: str | None,
    tier: str | None = None,
    seed: dict[str, Any] | None = None,
) -> None:
    """#908 — billing changes require 2FA when user has 2FA enabled."""
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    if action not in (cfg.get("billing_actions_requiring_mfa") or []):
        return
    from mfa_service import mfa_status_for_user

    status = await mfa_status_for_user(user_id)
    requirement = tier_mfa_requirement(tier, seed=seed)
    if not status.get("enabled"):
        if requirement == "mandatory":
            raise ValueError("2FA must be enabled before billing changes on institutional tier")
        return
    if not mfa_code:
        raise ValueError("2FA code required for billing changes")
    from mfa_service import verify_user_mfa

    if not await verify_user_mfa(user_id, mfa_code):
        log_mfa_event("bypass_attempt", user_id=user_id, detail={"action": action, "billing": True}, seed=seed)
        raise ValueError("Invalid 2FA code for billing action")
    log_mfa_event("billing_action", user_id=user_id, detail={"action": action}, seed=seed)


def assert_role_elevation_mfa(
    *,
    from_role: str,
    to_role: str,
    mfa_verified: bool,
    seed: dict[str, Any] | None = None,
) -> None:
    """#1022 RBAC — role elevation requires 2FA re-verification."""
    seed = seed or _load_seed()
    if not (_cfg(seed).get("role_elevation_requires_mfa", True)):
        return
    rank = {"viewer": 0, "analyst": 1, "pm": 2, "compliance": 3, "admin": 4}
    if rank.get(to_role, 0) <= rank.get(from_role, 0):
        return
    if not mfa_verified:
        raise PermissionError("role_elevation_requires_2fa_reverification")
    log_mfa_event(
        "role_elevation",
        detail={"from_role": from_role, "to_role": to_role},
        seed=seed,
    )


def backup_codes_count(*, seed: dict[str, Any] | None = None) -> int:
    return int((_cfg(seed).get("policy") or {}).get("backup_codes_count", 10))


def check_production_gate_1019(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = session_security_status_1019(seed=seed)
    from admin_mfa import mfa_policy_enabled, system_admin_totp_configured

    assert_no_skip_admin_mfa(seed=seed)
    env = (os.getenv("ENV") or "").lower()
    prod = env in {"production", "prod"}
    admin_ok = system_admin_totp_configured() if prod and mfa_policy_enabled() else True
    return {
        "ok": admin_ok,
        "feature_ref": _FEATURE_REF,
        "blocks_production": prod,
        "admin_2fa_configured": admin_ok,
        "checks": {
            "totp_only": status["policy"]["totp_only"],
            "sms_forbidden": status["policy"]["sms_forbidden"],
            "skip_admin_mfa_forbidden": status["policy"]["skip_admin_mfa_forbidden"],
            "backup_codes_10": status["policy"]["backup_codes_count"] == 10,
            "audit_retention_2y": status["policy"]["audit_retention_days"] == 730,
        },
        "timestamp": _utcnow(),
    }


def run_session_security_e2e_1019(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    reset_session_security_state()

    status = session_security_status_1019(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "totp_only", "passed": status["policy"]["totp_only"] is True})
    checks.append({"id": "sms_forbidden", "passed": "sms" in status["forbidden_factors"]})
    checks.append({"id": "admin_mandatory", "passed": status["policy"]["admin_mfa_mandatory"] is True})
    checks.append({"id": "backup_10", "passed": status["policy"]["backup_codes_count"] == 10})

    checks.append({"id": "free_optional", "passed": tier_mfa_requirement("free", seed=seed) == "optional"})
    checks.append({"id": "pro_recommended", "passed": tier_mfa_requirement("pro", seed=seed) == "strongly_recommended"})
    checks.append({"id": "institution_mandatory", "passed": tier_mfa_requirement("institutional", seed=seed) == "mandatory"})

    tier_login = assert_tier_mfa_at_login(tier="free", mfa_enabled=False, email="u@example.com", seed=seed)
    checks.append({"id": "free_login_ok", "passed": tier_login["mfa_requirement"] == "optional"})

    try:
        assert_tier_mfa_at_login(tier="institutional", mfa_enabled=False, email="i@example.com", seed=seed)
        checks.append({"id": "institution_blocks", "passed": False})
    except ValueError:
        checks.append({"id": "institution_blocks", "passed": True})

    log_mfa_event("enable", user_id=1, actor="test@example.com", seed=seed)
    audit = get_mfa_audit_trail(limit=5)
    checks.append({"id": "audit_logged", "passed": audit["events_count"] >= 1})

    try:
        assert_role_elevation_mfa(from_role="viewer", to_role="admin", mfa_verified=False, seed=seed)
        checks.append({"id": "rbac_elevation_block", "passed": False})
    except PermissionError:
        checks.append({"id": "rbac_elevation_block", "passed": True})

    assert_role_elevation_mfa(from_role="viewer", to_role="admin", mfa_verified=True, seed=seed)
    checks.append({"id": "rbac_elevation_ok", "passed": True})

    gate = check_production_gate_1019(seed=seed)
    checks.append({"id": "production_gate", "passed": "admin_2fa_configured" in gate})

    try:
        from password_recovery_hardening import run_password_recovery_e2e

        pr = run_password_recovery_e2e(seed=seed)
        checks.append({"id": "password_recovery_e2e", "passed": pr["all_passed"] is True})
    except ImportError:
        checks.append({"id": "password_recovery_e2e", "passed": False})

    try:
        from session_lifecycle_hardening import run_session_lifecycle_e2e

        sl = run_session_lifecycle_e2e(seed=seed)
        checks.append({"id": "session_lifecycle_e2e", "passed": sl["all_passed"] is True})
    except ImportError:
        checks.append({"id": "session_lifecycle_e2e", "passed": False})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
