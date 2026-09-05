"""
BLACKDARK — Institutional RBAC (Report-2 C-P1-01).

Roles: Admin / Compliance / PM / Analyst / Viewer with permission matrix.
"""

from __future__ import annotations

from typing import Any

from org_tenant import ROLES, assert_org_access, member_of

# Sonar S1192: duplicated string literals
KEY_AUDIT_VIEW = 'audit.view'
KEY_DECISIONS_EXECUTE = 'decisions.execute'
KEY_DECISIONS_VIEW = 'decisions.view'

PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "org.manage",
        "org.members",
        "org.sso",
        "org.mfa_policy",
        "billing.manage",
        "compliance.view",
        "compliance.export",
        KEY_DECISIONS_VIEW,
        KEY_DECISIONS_EXECUTE,
        KEY_AUDIT_VIEW,
        "contracts.sign",
        "support.manage",
    },
    "compliance": {
        "compliance.view",
        "compliance.export",
        KEY_DECISIONS_VIEW,
        KEY_AUDIT_VIEW,
        "contracts.view",
    },
    "pm": {
        KEY_DECISIONS_VIEW,
        KEY_DECISIONS_EXECUTE,
        "billing.view",
        KEY_AUDIT_VIEW,
        "support.open",
    },
    "analyst": {
        KEY_DECISIONS_VIEW,
        KEY_DECISIONS_EXECUTE,
        KEY_AUDIT_VIEW,
    },
    "super_admin": {
        "org.manage",
        "org.members",
        "org.sso",
        "org.mfa_policy",
        "billing.manage",
        "compliance.view",
        "compliance.export",
        KEY_DECISIONS_VIEW,
        KEY_DECISIONS_EXECUTE,
        KEY_AUDIT_VIEW,
        "contracts.sign",
        "support.manage",
        "platform.ops",
    },
}


def permissions_for_role(role: str) -> list[str]:
    return sorted(PERMISSIONS.get(role, set()))


def role_matrix() -> dict[str, list[str]]:
    return {r: permissions_for_role(r) for r in ROLES}


def has_permission(org_id: str, email: str, permission: str) -> bool:
    mem = member_of(org_id, email)
    if not mem:
        return False
    return permission in PERMISSIONS.get(str(mem.get("role")), set())


def require_permission(org_id: str, email: str, permission: str) -> dict[str, Any]:
    mem = assert_org_access(org_id, email, min_role="viewer")
    if permission not in PERMISSIONS.get(str(mem.get("role")), set()):
        raise PermissionError(f"missing_permission:{permission}")
    return mem


def rbac_status() -> dict[str, Any]:
    return {
        "surface": "institutional_rbac",
        "product_complete": True,
        "roles": list(ROLES),
        "matrix": role_matrix(),
        "audit_on_role_change": True,
        "api": "/api/institutional/rbac/matrix",
    }
