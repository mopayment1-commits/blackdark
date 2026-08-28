"""
Institutional RBAC Hardening — #1022.

Merged into RBAC Layer / Sprint 1 Infrastructure — NOT standalone.
Least-privilege roles, tenant isolation, authZ audit, team management.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.InstitutionalRBAC")

_FEATURE_REF = 1022
_SUB_FEATURE = "institutional_team_rbac"
_SEED_PATH = Path("data/rbac_institutional_seed.json")
_AUDIT_PATH = Path("data/authz_audit.jsonl")

_SESSION_REF = 1019
_STRIPE_REF = 908
_DATA_EXPORT_REF = 924
_SQL_WORKSPACE_REF = 978
_DECISION_CERT_REF = 952
_TOS_REF = 1018

InstitutionalRole = Literal["viewer", "analyst", "admin", "super_admin"]

_LOCK = threading.Lock()


def reset_rbac_state() -> None:
    pass


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("institutional_rbac_1022") or {}


def institutional_roles(*, seed: dict[str, Any] | None = None) -> tuple[str, ...]:
    roles = (_cfg(seed).get("institutional_roles") or {}).keys()
    return tuple(str(r) for r in roles) or ("viewer", "analyst", "admin", "super_admin")


def canonical_role(role: str, *, seed: dict[str, Any] | None = None) -> str:
    seed = seed or _load_seed()
    aliases = (_cfg(seed).get("legacy_role_aliases") or {})
    mapped = aliases.get(role.strip().lower(), role.strip().lower())
    if mapped in institutional_roles(seed=seed):
        return mapped
    return "viewer"


def permissions_for_institutional_role(role: str, *, seed: dict[str, Any] | None = None) -> set[str]:
    seed = seed or _load_seed()
    canonical = canonical_role(role, seed=seed)
    role_cfg = (_cfg(seed).get("institutional_roles") or {}).get(canonical) or {}
    return set(role_cfg.get("permissions") or [])


def build_permission_matrix(*, seed: dict[str, Any] | None = None) -> dict[str, list[str]]:
    seed = seed or _load_seed()
    roles_cfg = (_cfg(seed).get("institutional_roles") or {})
    return {
        role: sorted((cfg.get("permissions") or []))
        for role, cfg in roles_cfg.items()
    }


def institutional_rbac_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "sub_feature": _SUB_FEATURE,
        "standalone_rejected": True,
        "merged_into": "#1022 RBAC Layer / Sprint 1 Infrastructure",
        "policy": {
            "backend_enforced": policy.get("backend_enforced", True),
            "client_side_forbidden": policy.get("client_side_forbidden", True),
            "tenant_isolation": policy.get("tenant_isolation", True),
            "least_privilege": policy.get("least_privilege", True),
            "separation_of_duties": policy.get("separation_of_duties", True),
            "audit_retention_days": policy.get("audit_retention_days", 730),
            "blocks_production_sprint1": policy.get("blocks_production_sprint1", True),
        },
        "institutional_roles": list(institutional_roles(seed=seed)),
        "matrix": build_permission_matrix(seed=seed),
        "team_management": cfg.get("team_management") or {},
        "integrations": cfg.get("integrations") or {
            "session_ref": _SESSION_REF,
            "stripe_ref": _STRIPE_REF,
            "data_export_ref": _DATA_EXPORT_REF,
            "sql_workspace_ref": _SQL_WORKSPACE_REF,
            "decision_certificate_ref": _DECISION_CERT_REF,
            "tos_ref": _TOS_REF,
        },
        "timestamp": _utcnow(),
    }


def log_authz_decision(
    *,
    user_id: int | None = None,
    email: str | None = None,
    tenant_id: str | None = None,
    role: str | None = None,
    action: str,
    resource: str,
    result: str = "allowed",
    detail: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    event = {
        "event_id": f"authz_{uuid.uuid4().hex[:12]}",
        "feature_ref": _FEATURE_REF,
        "user_id": user_id,
        "email": email,
        "tenant_id": tenant_id,
        "role": role,
        "action": action,
        "resource": resource,
        "result": result,
        "detail": detail or {},
        "append_only": True,
        "retention_days": (_cfg(seed).get("policy") or {}).get("audit_retention_days", 730),
        "timestamp": _utcnow(),
        "ts": time.time(),
    }
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        try:
            with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError:
            logger.debug("authz audit persist failed", exc_info=True)
    try:
        from security_events import record_security_event

        record_security_event(
            f"authz_{action}",
            severity="warning" if result == "denied" else "info",
            actor=email or (str(user_id) if user_id else None),
            detail={"event_id": event["event_id"], "resource": resource, "result": result},
        )
    except ImportError:
        pass
    return event


def get_authz_audit_trail(*, limit: int = 50) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    if _AUDIT_PATH.is_file():
        try:
            lines = _AUDIT_PATH.read_text(encoding="utf-8").splitlines()
            rows = [json.loads(x) for x in lines[-limit:] if x.strip()]
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "ok": True,
        "events_count": len(rows),
        "events": rows,
        "append_only": True,
        "retention_days": 730,
        "path": str(_AUDIT_PATH),
        "timestamp": _utcnow(),
    }


def enforce_tenant_membership(
    org_id: str,
    email: str,
    *,
    action: str = "access",
    resource: str = "org",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """RLS-style tenant gate — user must be active member of org_id (tenant)."""
    from org_tenant import member_of

    mem = member_of(org_id, email)
    if not mem:
        log_authz_decision(
            email=email,
            tenant_id=org_id,
            action=action,
            resource=resource,
            result="denied",
            detail={"reason": "cross_tenant_denied"},
            seed=seed,
        )
        raise PermissionError("cross_tenant_denied")
    return mem


def enforce_permission(
    org_id: str,
    email: str,
    permission: str,
    *,
    action: str | None = None,
    resource: str | None = None,
    user_id: int | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Backend-enforced RBAC check with audit."""
    seed = seed or _load_seed()
    mem = enforce_tenant_membership(
        org_id,
        email,
        action=action or "permission_check",
        resource=resource or permission,
        seed=seed,
    )
    role = str(mem.get("role") or "viewer")
    perms = permissions_for_institutional_role(role, seed=seed)
    # Legacy roles may have extra permissions from org_rbac.PERMISSIONS
    try:
        from org_rbac import PERMISSIONS as LEGACY_PERMS

        perms = perms | LEGACY_PERMS.get(role, set())
    except ImportError:
        pass
    if permission not in perms:
        log_authz_decision(
            user_id=user_id,
            email=email,
            tenant_id=org_id,
            role=role,
            action=action or "permission_check",
            resource=resource or permission,
            result="denied",
            detail={"permission": permission},
            seed=seed,
        )
        raise PermissionError(f"missing_permission:{permission}")
    log_authz_decision(
        user_id=user_id,
        email=email,
        tenant_id=org_id,
        role=role,
        action=action or "permission_check",
        resource=resource or permission,
        result="allowed",
        detail={"permission": permission},
        seed=seed,
    )
    return mem


def has_institutional_permission(org_id: str, email: str, permission: str, *, seed: dict[str, Any] | None = None) -> bool:
    try:
        enforce_permission(org_id, email, permission, seed=seed)
        return True
    except PermissionError:
        return False


def assert_data_export_allowed(org_id: str, email: str, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#924 — Analyst/Admin export enabled; Viewer blocked."""
    return enforce_permission(
        org_id,
        email,
        "data.export",
        action="data_export",
        resource="data.export",
        seed=seed,
    )


def assert_sql_workspace_allowed(org_id: str, email: str, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#978 — Analyst/Admin query access; Viewer blocked."""
    return enforce_permission(
        org_id,
        email,
        "sql.workspace.query",
        action="sql_query",
        resource="sql.workspace",
        seed=seed,
    )


def assert_institutional_certificate_allowed(
    org_id: str,
    email: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#952 — institutional certificate generation requires Admin."""
    return enforce_permission(
        org_id,
        email,
        "certificate.institutional.generate",
        action="certificate_generate",
        resource="decision_certificate",
        seed=seed,
    )


def manage_team_member(
    org_id: str,
    *,
    actor_email: str,
    action: Literal["create", "update", "delete"],
    target_email: str,
    role: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Sprint 2 team management — Admin only, backend-enforced."""
    seed = seed or _load_seed()
    enforce_permission(
        org_id,
        actor_email,
        "org.members.manage",
        action=f"team_{action}",
        resource=f"member:{target_email}",
        seed=seed,
    )
    from org_tenant import add_member, remove_member, set_member_role

    target_email = target_email.strip().lower()
    if action == "create":
        if not role:
            raise ValueError("role_required")
        result = add_member(org_id, target_email, role)
    elif action == "update":
        if not role:
            raise ValueError("role_required")
        result = set_member_role(org_id, target_email, role, actor_email=actor_email)
    else:
        result = remove_member(org_id, target_email, actor_email=actor_email)
    log_authz_decision(
        email=actor_email,
        tenant_id=org_id,
        action=f"team_{action}",
        resource=f"member:{target_email}",
        result="allowed",
        detail={"target_role": role, "target": target_email},
        seed=seed,
    )
    return {"ok": True, "action": action, "member": result}


def check_rbac_production_gate(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = institutional_rbac_status(seed=seed)
    policy = status["policy"]
    checks = {
        "backend_enforced": policy["backend_enforced"] is True,
        "tenant_isolation": policy["tenant_isolation"] is True,
        "four_roles": len(status["institutional_roles"]) == 4,
        "viewer_readonly": "data.export" not in (status["matrix"].get("viewer") or []),
        "analyst_export": "data.export" in (status["matrix"].get("analyst") or []),
        "admin_users": "org.members.manage" in (status["matrix"].get("admin") or []),
        "super_admin_ops": "platform.ops" in (status["matrix"].get("super_admin") or []),
        "audit_2y": policy["audit_retention_days"] == 730,
    }
    return {
        "ok": all(checks.values()),
        "feature_ref": _FEATURE_REF,
        "blocks_production": policy.get("blocks_production_sprint1", True),
        "checks": checks,
        "timestamp": _utcnow(),
    }


def run_institutional_rbac_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    from org_tenant import add_member, create_org

    status = institutional_rbac_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "four_roles", "passed": len(status["institutional_roles"]) == 4})
    checks.append({"id": "viewer_no_export", "passed": "data.export" not in status["matrix"]["viewer"]})
    checks.append({"id": "analyst_export", "passed": "data.export" in status["matrix"]["analyst"]})
    checks.append({"id": "admin_cert", "passed": "certificate.institutional.generate" in status["matrix"]["admin"]})

    org = create_org(name="RBAC Test Org", owner_email="owner@rbac.test")
    add_member(org["org_id"], "viewer@rbac.test", "viewer")
    add_member(org["org_id"], "analyst@rbac.test", "analyst")

    try:
        assert_data_export_allowed(org["org_id"], "viewer@rbac.test", seed=seed)
        checks.append({"id": "viewer_export_blocked", "passed": False})
    except PermissionError:
        checks.append({"id": "viewer_export_blocked", "passed": True})

    try:
        assert_data_export_allowed(org["org_id"], "analyst@rbac.test", seed=seed)
        checks.append({"id": "analyst_export_ok", "passed": True})
    except PermissionError:
        checks.append({"id": "analyst_export_ok", "passed": False})

    try:
        assert_sql_workspace_allowed(org["org_id"], "viewer@rbac.test", seed=seed)
        checks.append({"id": "viewer_sql_blocked", "passed": False})
    except PermissionError:
        checks.append({"id": "viewer_sql_blocked", "passed": True})

    try:
        manage_team_member(
            org["org_id"],
            actor_email="viewer@rbac.test",
            action="create",
            target_email="new@rbac.test",
            role="analyst",
            seed=seed,
        )
        checks.append({"id": "viewer_team_blocked", "passed": False})
    except PermissionError:
        checks.append({"id": "viewer_team_blocked", "passed": True})

    gate = check_rbac_production_gate(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})

    audit = get_authz_audit_trail(limit=20)
    checks.append({"id": "audit_logged", "passed": audit["events_count"] >= 1})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
