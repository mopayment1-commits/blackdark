"""Account compromise response — ID-025."""

from __future__ import annotations

from typing import Any


async def secure_my_account(user_id: int, *, actor: dict[str, Any]) -> dict[str, Any]:
    from database import invalidate_user_reset_tokens, revoke_all_identity_sessions
    from identity.identity_audit import record_identity_event
    from identity.security_notifications import notify_security_event
    from identity.step_up import mark_step_up, require_step_up

    await require_step_up(actor, action="account.compromise")
    sessions = await revoke_all_identity_sessions(user_id)
    tokens = await invalidate_user_reset_tokens(user_id)
    await mark_step_up(user_id)
    await record_identity_event(
        event_type="account.compromise_response",
        user_id=user_id,
        detail={"sessions_revoked": sessions, "reset_tokens_invalidated": tokens},
    )
    await notify_security_event(user_id, "security.compromise_response", actor=actor)
    return {
        "status": "secured",
        "sessions_revoked": sessions,
        "reset_tokens_invalidated": tokens,
        "requires_reauthentication": True,
    }
