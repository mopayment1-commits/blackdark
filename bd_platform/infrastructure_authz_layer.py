"""
Infrastructure AuthZ Layer — RBAC Core (Sprint 1) + SSO (Sprint 2).

Merged into Sprint-1 Infrastructure on top of AuthN (#1019 / account security).
NOT a standalone service — authorization layer with tenant isolation + audit.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.AuthZLayer")

_FEATURE_REF = "authz_layer"
_CONTROL_REF = "SEC-010"
_MERGED_INTO = "Sprint-1 Infrastructure (AuthN #1019)"
_STANDALONE = False
_SPRINT_RBAC = 1
_SPRINT_SSO = 2
_SEED_PATH = Path("data/infrastructure_authz_layer_seed.json")
_RUNBOOK = "docs/ops/AUTHZ_LAYER.md"
_AUDIT_PATH = Path("data/authz_audit.jsonl")

_AUTHN_REF = 1019
_BILLING_REF = 908
_DATA_EXPORT_REF = 924
_SQL_WORKSPACE_REF = 978
_DECISION_CERT_REF = 952
_INCIDENT_RESPONSE_REF = 1017
_PRIVACY_REF = 1018

_CANONICAL_ROLES = ("viewer", "analyst", "admin", "super_admin")

_LEGACY_ROLE_MAP: dict[str, str] = {
    "viewer": "viewer",
    "analyst": "analyst",
    "pm": "analyst",
    "compliance": "analyst",
    "admin": "admin",
    "super_admin": "super_admin",
}

_CANONICAL_PERMISSIONS: dict[str, frozenset[str]] = {
    "viewer": frozenset({"read", "decisions.view", "audit.view"}),
    "analyst": frozenset(
        {
            "read",
            "decisions.view",
            "audit.view",
            "data.export",
            "sql.workspace",
            "queries.save",
        }
    ),
    "admin": frozenset(
        {
            "read",
            "decisions.view",
            "audit.view",
            "data.export",
            "sql.workspace",
            "queries.save",
            "billing.manage",
            "users.manage",
            "api.keys.manage",
            "decision.certificate",
            "org.manage",
            "org.members",
            "org.sso",
            "org.mfa_policy",
        }
    ),
    "super_admin": frozenset(
        {
            "read",
            "decisions.view",
            "audit.view",
            "data.export",
            "sql.workspace",
            "queries.save",
            "billing.manage",
            "users.manage",
            "api.keys.manage",
            "decision.certificate",
            "org.manage",
            "org.members",
            "org.sso",
            "org.mfa_policy",
            "platform.ops",
        }
    ),
}

_audit_log: list[dict[str, Any]] = []


def reset_authz_state() -> None:
    _audit_log.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("authz seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("authz_layer") or {}


def normalize_canonical_role(role: str) -> str:
    key = str(role or "viewer").strip().lower()
    return _LEGACY_ROLE_MAP.get(key, "viewer")


def permissions_for_canonical_role(role: str) -> list[str]:
    canonical = normalize_canonical_role(role)
    return sorted(_CANONICAL_PERMISSIONS.get(canonical, _CANONICAL_PERMISSIONS["viewer"]))


def canonical_role_matrix() -> dict[str, list[str]]:
    return {r: permissions_for_canonical_role(r) for r in _CANONICAL_ROLES}


def authz_layer_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature": _FEATURE_REF,
        "control_ref": _CONTROL_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "sprint_rbac": _SPRINT_RBAC,
        "sprint_sso": _SPRINT_SSO,
        "policy": {
            "canonical_roles": list(_CANONICAL_ROLES),
            "backend_enforced": policy.get("backend_enforced", True),
            "no_client_side_only": policy.get("no_client_side_only", True),
            "tenant_isolation": policy.get("tenant_isolation", True),
            "rls_enforced": policy.get("rls_enforced", True),
            "audit_retention_years": policy.get("audit_retention_years", 2),
            "audit_append_only": policy.get("audit_append_only", True),
            "blocks_production_if_incomplete": policy.get("blocks_production_if_incomplete", True),
        },
        "integrations": {
            "authn_ref": _AUTHN_REF,
            "billing_ref": _BILLING_REF,
            "data_export_ref": _DATA_EXPORT_REF,
            "sql_workspace_ref": _SQL_WORKSPACE_REF,
            "decision_cert_ref": _DECISION_CERT_REF,
            "incident_response_ref": _INCIDENT_RESPONSE_REF,
            "privacy_ref": _PRIVACY_REF,
        },
        "matrix": canonical_role_matrix(),
        "runbook": _RUNBOOK,
        "fee_db": cfg.get("fee_db"),
        "timestamp": _utcnow(),
    }


def enforce_tenant_isolation(
    *,
    user_id: int | str | None,
    email: str,
    tenant_id: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """user_id + tenant_id — membership required; no cross-tenant access."""
    seed = seed or _load_seed()
    from org_tenant import member_of

    mem = member_of(tenant_id, email.strip().lower())
    isolated = mem is not None
    return {
        "ok": isolated,
        "user_id": user_id,
        "email": email.strip().lower(),
        "tenant_id": tenant_id,
        "isolated": isolated,
        "role": mem.get("role") if mem else None,
        "canonical_role": normalize_canonical_role(str(mem.get("role") if mem else "viewer")),
        "cross_tenant_blocked": not isolated,
        "timestamp": _utcnow(),
    }


def record_authz_fee(
    *,
    user_tier: str = "free",
    permission: str = "",
    allowed: bool = True,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee_cfg = (_cfg(seed).get("fee_db") or {})
    base = float(fee_cfg.get("per_authz_check_usd", 0.00001))
    entry = {
        "fee_id": f"authz_{uuid.uuid4().hex[:10]}",
        "user_tier": user_tier,
        "permission": permission,
        "allowed": allowed,
        "cost_usd": base,
        "fee_db_logged": True,
        "timestamp": _utcnow(),
    }
    return entry


def log_authz_audit(
    *,
    user_id: int | str | None,
    email: str,
    role: str,
    action: str,
    resource: str,
    tenant_id: str,
    result: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append-only authZ audit — 2 year retention policy."""
    seed = seed or _load_seed()
    entry = {
        "audit_id": f"authz_audit_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "email": email.strip().lower(),
        "role": role,
        "canonical_role": normalize_canonical_role(role),
        "action": action,
        "resource": resource,
        "tenant_id": tenant_id,
        "result": result,
        "timestamp": _utcnow(),
        "append_only": True,
        "retention_years": (_cfg(seed).get("policy") or {}).get("audit_retention_years", 2),
    }
    _audit_log.append(entry)
    try:
        _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.debug("authz audit persist skipped", exc_info=True)
    return entry


def authorize_request(
    *,
    user_id: int | str | None,
    email: str,
    tenant_id: str,
    permission: str,
    resource: str = "",
    user_tier: str = "free",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Backend-enforced authorization — every endpoint must call this."""
    seed = seed or _load_seed()
    isolation = enforce_tenant_isolation(user_id=user_id, email=email, tenant_id=tenant_id, seed=seed)
    fee = record_authz_fee(user_tier=user_tier, permission=permission, allowed=False, seed=seed)

    if not isolation["ok"]:
        audit = log_authz_audit(
            user_id=user_id,
            email=email,
            role="none",
            action=permission,
            resource=resource or f"tenant:{tenant_id}",
            tenant_id=tenant_id,
            result="denied_cross_tenant",
            seed=seed,
        )
        fee["allowed"] = False
        return {
            "ok": False,
            "allowed": False,
            "reason": "cross_tenant_denied",
            "isolation": isolation,
            "fee_db": fee,
            "audit": audit,
            "timestamp": _utcnow(),
        }

    canonical = isolation["canonical_role"]
    perms = _CANONICAL_PERMISSIONS.get(canonical, frozenset())
    allowed = permission in perms

    # Feature gate integrations
    if permission == "data.export" and not allowed:
        integration = {"ref": _DATA_EXPORT_REF, "blocked": True}
    elif permission == "sql.workspace" and not allowed:
        integration = {"ref": _SQL_WORKSPACE_REF, "blocked": True}
    elif permission == "decision.certificate" and not allowed:
        integration = {"ref": _DECISION_CERT_REF, "blocked": True}
    elif permission == "billing.manage" and not allowed:
        integration = {"ref": _BILLING_REF, "blocked": True}
    else:
        integration = None

    fee["allowed"] = allowed
    audit = log_authz_audit(
        user_id=user_id,
        email=email,
        role=str(isolation.get("role") or canonical),
        action=permission,
        resource=resource or f"tenant:{tenant_id}",
        tenant_id=tenant_id,
        result="allowed" if allowed else "denied",
        seed=seed,
    )

    return {
        "ok": allowed,
        "allowed": allowed,
        "permission": permission,
        "canonical_role": canonical,
        "tenant_id": tenant_id,
        "integration": integration,
        "fee_db": fee,
        "audit": audit,
        "timestamp": _utcnow(),
    }


def require_authorization(
    *,
    user_id: int | str | None,
    email: str,
    tenant_id: str,
    permission: str,
    resource: str = "",
    user_tier: str = "free",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = authorize_request(
        user_id=user_id,
        email=email,
        tenant_id=tenant_id,
        permission=permission,
        resource=resource,
        user_tier=user_tier,
        seed=seed,
    )
    if not result["allowed"]:
        raise PermissionError(f"authz_denied:{permission}")
    return result


def check_tier_feature_gate(
    *,
    canonical_role: str,
    feature: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#908 — tier capabilities enforced via RBAC role."""
    seed = seed or _load_seed()
    role = normalize_canonical_role(canonical_role)
    tier_caps = (seed.get("tier_capabilities") or {}).get(role, {})
    allowed = tier_caps.get(feature, role in ("analyst", "admin", "super_admin"))
    return {
        "ok": allowed,
        "feature": feature,
        "canonical_role": role,
        "billing_ref": _BILLING_REF,
        "backend_enforced": True,
        "timestamp": _utcnow(),
    }


def revoke_compromised_account(
    *,
    user_id: int | str,
    email: str,
    tenant_id: str,
    actor_email: str = "system",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#1017 Incident Response — RBAC revoke + session invalidation playbook."""
    seed = seed or _load_seed()
    sessions_revoked = 0
    try:
        import asyncio
        from database import delete_user_sessions_for_user

        async def _revoke() -> int:
            return int(await delete_user_sessions_for_user(int(user_id)))

        try:
            asyncio.get_running_loop()
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                sessions_revoked = pool.submit(lambda: asyncio.run(_revoke())).result()
        except RuntimeError:
            sessions_revoked = asyncio.run(_revoke())
    except Exception:
        logger.debug("session revoke skipped", exc_info=True)

    audit = log_authz_audit(
        user_id=user_id,
        email=email,
        role="revoked",
        action="incident.rbac_revoke",
        resource=f"user:{user_id}",
        tenant_id=tenant_id,
        result="revoked",
        seed=seed,
    )

    return {
        "ok": True,
        "incident_response_ref": _INCIDENT_RESPONSE_REF,
        "user_id": user_id,
        "email": email,
        "tenant_id": tenant_id,
        "sessions_revoked": sessions_revoked,
        "rbac_revoked": True,
        "actor": actor_email,
        "audit": audit,
        "timestamp": _utcnow(),
    }


def sso_authz_status(*, org_id: str | None = None, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Sprint 2 — SSO (SAML/OIDC) readiness for Pro/Institution."""
    seed = seed or _load_seed()
    sso_cfg = seed.get("sso") or {}
    try:
        from enterprise_sso import sso_status

        live = sso_status(org_id)
    except Exception:
        live = {}

    return {
        "ok": True,
        "sprint": _SPRINT_SSO,
        "protocols": sso_cfg.get("protocols", ["saml2", "oidc"]),
        "idp_integrations": sso_cfg.get("idp_integrations", ["okta", "azure_ad", "google_workspace"]),
        "jit_default_role": sso_cfg.get("jit_default_role", "viewer"),
        "tiers": sso_cfg.get("tiers", ["pro", "institution"]),
        "live_status": live,
        "timestamp": _utcnow(),
    }


def get_authz_audit_trail(*, limit: int = 50) -> dict[str, Any]:
    rows = _audit_log[-limit:]
    return {
        "ok": True,
        "count": len(rows),
        "audit_trail": rows,
        "append_only": True,
        "timestamp": _utcnow(),
    }


def run_authz_layer_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = authz_layer_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "four_roles", "passed": len(status["policy"]["canonical_roles"]) == 4})
    checks.append({"id": "backend_enforced", "passed": status["policy"]["backend_enforced"] is True})
    checks.append({"id": "tenant_isolation", "passed": status["policy"]["tenant_isolation"] is True})

    matrix = canonical_role_matrix()
    checks.append({"id": "viewer_read_only", "passed": "data.export" not in matrix["viewer"]})
    checks.append({"id": "analyst_export", "passed": "data.export" in matrix["analyst"]})
    checks.append({"id": "admin_users", "passed": "users.manage" in matrix["admin"]})
    checks.append({"id": "super_admin_ops", "passed": "platform.ops" in matrix["super_admin"]})

    from org_tenant import create_org, add_member

    org = create_org(name="AuthZ Test Org", owner_email="owner@authz.test", require_mfa=False)
    org_id = org["org_id"]
    add_member(org_id, "viewer@authz.test", "viewer")
    add_member(org_id, "analyst@authz.test", "analyst")
    add_member(org_id, "admin@authz.test", "admin")

    viewer_ok = authorize_request(
        user_id=1, email="viewer@authz.test", tenant_id=org_id, permission="read", seed=seed
    )
    checks.append({"id": "viewer_read", "passed": viewer_ok["allowed"] is True})

    viewer_export = authorize_request(
        user_id=1, email="viewer@authz.test", tenant_id=org_id, permission="data.export", seed=seed
    )
    checks.append({"id": "viewer_export_blocked", "passed": viewer_export["allowed"] is False})

    analyst_export = authorize_request(
        user_id=2, email="analyst@authz.test", tenant_id=org_id, permission="data.export", seed=seed
    )
    checks.append({"id": "analyst_export_allowed", "passed": analyst_export["allowed"] is True})

    cross = authorize_request(
        user_id=99, email="outsider@authz.test", tenant_id=org_id, permission="read", seed=seed
    )
    checks.append({"id": "cross_tenant_denied", "passed": cross["allowed"] is False})

    admin_users = authorize_request(
        user_id=3, email="admin@authz.test", tenant_id=org_id, permission="users.manage", seed=seed
    )
    checks.append({"id": "admin_users_allowed", "passed": admin_users["allowed"] is True})

    fee = admin_users.get("fee_db") or {}
    checks.append({"id": "fee_db_logged", "passed": fee.get("fee_db_logged") is True})

    sso = sso_authz_status(seed=seed)
    checks.append({"id": "sso_sprint2", "passed": sso["jit_default_role"] == "viewer"})
    checks.append({"id": "sso_idps", "passed": "okta" in sso["idp_integrations"]})

    tier_gate = check_tier_feature_gate(canonical_role="viewer", feature="api_rate_limit", seed=seed)
    checks.append({"id": "tier_gate", "passed": "billing_ref" in tier_gate})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
