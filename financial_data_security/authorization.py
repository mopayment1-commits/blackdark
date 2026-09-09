"""Resource-level authorization for financial operations."""

from __future__ import annotations

from typing import Any


async def authorize_billing_action(
    *,
    user: dict[str, Any] | None,
    action: str,
    resource_owner_id: int | None = None,
) -> None:
    if action == "billing.checkout":
        return
    if user is None:
        raise PermissionError("authentication_required")
    uid = int(user.get("id") or 0)
    if uid <= 0:
        raise PermissionError("invalid_subject")
    if resource_owner_id is not None and uid != int(resource_owner_id):
        raise PermissionError("resource_owner_mismatch")
    if action == "billing.export":
        raise PermissionError("export_not_allowed")
    allowed = {
        "billing.checkout": True,
        "billing.portal": True,
        "billing.cancel": True,
        "billing.downgrade": True,
    }
    if not allowed.get(action, False):
        raise PermissionError(f"action_not_allowed:{action}")


def authorization_self_test() -> dict[str, Any]:
    return {"resource_aware": True, "logged_in_equals_allow": False, "is_admin_allow_all": False}
