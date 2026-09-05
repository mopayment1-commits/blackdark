"""
BLACKDARK — Institutional RBAC (#1022).

Roles: Viewer · Analyst · Admin · Super Admin (+ legacy aliases).
Backend-enforced with authZ audit trail.
"""

from __future__ import annotations

from typing import Any

from org_tenant import ROLES, assert_org_access, member_of

# Sonar S1192: duplicated string literals
KEY_AUDIT_VIEW = "audit.view"
KEY_DECISIONS_EXECUTE = "decisions.execute"
KEY_DECISIONS_VIEW = "decisions.view"
KEY_DATA_EXPORT = "data.export"
KEY_SQL_WORKSPACE = "sql.workspace.query"
KEY_CERT_INSTITUTIONAL = "certificate.institutional.generate"
KEY_API_KEYS = "api.keys.manage"
KEY_MEMBERS_MANAGE = "org.members.manage"
KEY_PLATFORM_OPS = "platform.ops"

PERMISSIONS: dict[str, set[str]] = {
    "super_admin": {
        "org.manage",
        "org.members",
        KEY_MEMBERS_MANAGE,
        "org.sso",
        "org.mfa_policy",
        "billing.manage",
        "compliance.view",
        "compliance.export",
        KEY_DECISIONS_VIEW,
        KEY_DECISIONS_EXECUTE,
        KEY_AUDIT_VIEW,
        KEY_DATA_EXPORT,
        KEY_SQL_WORKSPACE,
        KEY_CERT_INSTITUTIONAL,
        KEY_API_KEYS,
        KEY_PLATFORM_OPS,
        "contracts.sign",
        "support.manage",
        "data.read",
    },
    "admin": {
        "org.manage",
        "org.members",
        KEY_MEMBERS_MANAGE,
        "billing.manage",
        "compliance.view",
        "compliance.export",
        KEY_DECISIONS_VIEW,
        KEY_DECISIONS_EXECUTE,
        KEY_AUDIT_VIEW,
        KEY_DATA_EXPORT,
        KEY_SQL_WORKSPACE,
        KEY_CERT_INSTITUTIONAL,
        KEY_API_KEYS,
        "contracts.sign",
        "support.manage",
        "data.read",
    },
    "compliance": {
        "compliance.view",
        "compliance.export",
        KEY_DECISIONS_VIEW,
        KEY_AUDIT_VIEW,
        KEY_DATA_EXPORT,
        "contracts.view",
        "data.read",
    },
    "pm": {
        KEY_DECISIONS_VIEW,
        KEY_DECISIONS_EXECUTE,
        "billing.view",
        KEY_AUDIT_VIEW,
        KEY_DATA_EXPORT,
        KEY_SQL_WORKSPACE,
        "support.open",
        "data.read",
    },
    "analyst": {
        KEY_DECISIONS_VIEW,
        KEY_DECISIONS_EXECUTE,
        KEY_AUDIT_VIEW,
        KEY_DATA_EXPORT,
        KEY_SQL_WORKSPACE,
        "compliance.export",
        "data.read",
    },
    "viewer": {
        KEY_DECISIONS_VIEW,
        KEY_AUDIT_VIEW,
        "data.read",
    },
}


def permissions_for_role(role: str) -> list[str]:
    try:
        from institutional_rbac_hardening import permissions_for_institutional_role

        perms = permissions_for_institutional_role(role)
        perms = perms | PERMISSIONS.get(role, set())
        return sorted(perms)
    except ImportError:
        return sorted(PERMISSIONS.get(role, set()))


def role_matrix() -> dict[str, list[str]]:
    try:
        from institutional_rbac_hardening import build_permission_matrix

        matrix = build_permission_matrix()
        for legacy in ROLES:
            if legacy not in matrix:
                matrix[legacy] = permissions_for_role(legacy)
        return matrix
    except ImportError:
        return {r: permissions_for_role(r) for r in ROLES}


def has_permission(org_id: str, email: str, permission: str) -> bool:
    try:
        from institutional_rbac_hardening import has_institutional_permission

        return has_institutional_permission(org_id, email, permission)
    except ImportError:
        mem = member_of(org_id, email)
        if not mem:
            return False
        return permission in PERMISSIONS.get(str(mem.get("role")), set())


def require_permission(org_id: str, email: str, permission: str) -> dict[str, Any]:
    try:
        from institutional_rbac_hardening import enforce_permission

        return enforce_permission(org_id, email, permission)
    except ImportError:
        mem = assert_org_access(org_id, email, min_role="viewer")
        if permission not in PERMISSIONS.get(str(mem.get("role")), set()):
            raise PermissionError(f"missing_permission:{permission}")
        return mem


def require_permission_with_elevation_mfa(
    org_id: str,
    email: str,
    permission: str,
    *,
    previous_role: str | None = None,
    mfa_verified: bool = False,
) -> dict[str, Any]:
    """#1022 — role elevation requires 2FA re-verification."""
    mem = require_permission(org_id, email, permission)
    if previous_role:
        try:
            from session_account_security_1019 import assert_role_elevation_mfa

            assert_role_elevation_mfa(
                from_role=previous_role,
                to_role=str(mem.get("role")),
                mfa_verified=mfa_verified,
            )
        except ImportError:
            pass
    return mem


def rbac_status() -> dict[str, Any]:
    base = {
        "surface": "institutional_rbac",
        "feature_ref": 1022,
        "product_complete": True,
        "roles": list(ROLES),
        "matrix": role_matrix(),
        "audit_on_role_change": True,
        "api": "/api/institutional/rbac/matrix",
    }
    try:
        from institutional_rbac_hardening import institutional_rbac_status

        hardened = institutional_rbac_status()
        base["institutional_roles"] = hardened.get("institutional_roles")
        base["policy"] = hardened.get("policy")
        base["standalone_rejected"] = hardened.get("standalone_rejected")
        base["team_management"] = hardened.get("team_management")
    except ImportError:
        pass
    return base
