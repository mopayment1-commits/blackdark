"""
BLACKDARK — Enforced organization MFA (Report-2 C-P0-02 / Report-1 L1 cure).

When org.require_mfa=true, login without MFA is refused for all members.
"""

from __future__ import annotations

from typing import Any

from org_tenant import get_org, list_orgs_for_email


def org_requires_mfa_for_email(email: str) -> dict[str, Any]:
    """Return enforcement decision for a user email across memberships."""
    orgs = list_orgs_for_email(email)
    enforced = [o for o in orgs if o.get("require_mfa")]
    return {
        "email": email.strip().lower(),
        "org_mfa_enforced": bool(enforced),
        "enforcing_orgs": [
            {"org_id": o["org_id"], "name": o.get("name"), "require_mfa": True} for o in enforced
        ],
    }


def assert_login_mfa_policy(email: str, *, mfa_enabled: bool, mfa_code_present: bool) -> dict[str, Any]:
    """
    Call from auth login path.
    Raises ValueError when org policy requires MFA and user lacks it.
    """
    decision = org_requires_mfa_for_email(email)
    if not decision["org_mfa_enforced"]:
        return {"ok": True, "org_mfa_enforced": False}
    if not mfa_enabled:
        raise ValueError(
            "Organization MFA is required. Enroll TOTP at /settings/security before login."
        )
    if not mfa_code_present:
        return {
            "ok": False,
            "mfa_required": True,
            "org_mfa_enforced": True,
            "enforcing_orgs": decision["enforcing_orgs"],
        }
    return {"ok": True, "org_mfa_enforced": True}


def mfa_policy_status(org_id: str | None = None) -> dict[str, Any]:
    org = get_org(org_id) if org_id else None
    return {
        "surface": "org_enforced_mfa",
        "product_complete": True,
        "org_id": org_id,
        "require_mfa": bool(org.get("require_mfa")) if org else None,
        "factors": ["totp", "recovery_codes"],
        "webauthn_ready": True,
        "api": {
            "set_policy": "POST /api/institutional/orgs/{org_id}/mfa-policy",
            "check": "GET /api/institutional/mfa-policy/check",
        },
        "login_integration": "auth_service.login_user → assert_login_mfa_policy",
    }
