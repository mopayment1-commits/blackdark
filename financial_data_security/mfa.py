"""MFA policy for privileged financial access."""

from __future__ import annotations

from typing import Any


def mfa_coverage_status() -> dict[str, Any]:
    from admin_mfa import mfa_status

    admin = mfa_status()
    user_mfa = {"module": "mfa_service.py", "available": True}
    return {
        "admin_mfa_policy": admin,
        "user_mfa_module": user_mfa,
        "privileged_financial_routes_require_mfa": admin.get("policy_enabled"),
    }


async def assert_admin_financial_mfa(*, x_admin_totp: str | None = None, user: dict | None = None) -> None:
    from admin_mfa import assert_admin_mfa

    await assert_admin_mfa(x_admin_totp=x_admin_totp, user=user)
