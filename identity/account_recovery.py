"""Full account recovery orchestration — ID-024."""

from __future__ import annotations

from typing import Any


async def recovery_options(user_id: int) -> dict[str, Any]:
    from database import count_user_auth_methods, fetch_user_mfa_row, list_passkey_credentials

    methods = await count_user_auth_methods(user_id)
    mfa = await fetch_user_mfa_row(user_id)
    passkeys = await list_passkey_credentials(user_id)
    return {
        "password": methods.get("password", False),
        "passkeys": len(passkeys),
        "totp": bool(mfa and mfa.get("mfa_enabled")),
        "recovery_codes_remaining": int((mfa or {}).get("mfa_recovery_remaining") or 0),
        "oauth_providers": methods.get("providers", []),
        "phone_verified": methods.get("phone_verified", False),
    }


async def initiate_recovery(user_id: int, *, channel: str, actor_email: str) -> dict[str, Any]:
    from identity.identity_audit import record_identity_event

    await record_identity_event(
        event_type="account.recovery.initiated",
        user_id=user_id,
        detail={"channel": channel, "actor_email": actor_email[:3] + "…"},
    )
    return {"status": "initiated", "channel": channel, "note": "Follow verified channel instructions"}
