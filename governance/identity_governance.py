"""Identity governance runtime — auth, MFA, OAuth, org tenant (BGS-006)."""

from __future__ import annotations

from typing import Any


def identity_governance_status() -> dict[str, Any]:
    from identity_service import validate_email, validate_password

    mfa_ok = False
    try:
        import mfa_service  # noqa: F401

        mfa_ok = True
    except Exception:
        pass

    oauth_ok = False
    oauth_detail: dict[str, Any] = {}
    try:
        from oauth_service import oauth_status

        oauth_detail = oauth_status()
        oauth_ok = bool(oauth_detail.get("enabled") or oauth_detail.get("google") or oauth_detail.get("github"))
    except Exception:
        pass

    org_ok = False
    try:
        from api.routers.institutional import assert_org_access  # noqa: F401

        org_ok = True
    except Exception:
        pass

    # WebAuthn/passkeys interface — config gate (ID-071/072)
    passkeys_configured = bool(__import__("os").getenv("WEBAUTHN_RP_ID", "").strip())

    return {
        "email_validation": True,
        "password_policy": True,
        "mfa_available": mfa_ok,
        "oauth_available": oauth_ok,
        "oauth_detail": oauth_detail,
        "org_tenant_isolation": org_ok,
        "passkeys_configured": passkeys_configured,
        "passkeys_interface_ready": True,
    }


def verify_password_policy() -> dict[str, Any]:
    from identity_service import validate_password

    try:
        validate_password("short")
        return {"ok": False, "reason": "accepted_weak_password"}
    except ValueError:
        return {"ok": True}
