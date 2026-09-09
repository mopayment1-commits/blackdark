"""Account deletion orchestration — ID-047."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

DELETION_GRACE_DAYS = 14


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def request_account_deletion(user_id: int, *, actor: dict[str, Any]) -> dict[str, Any]:
    from database import insert_deletion_request
    from identity.account_states import transition_account_state
    from identity.identity_audit import record_identity_event
    from identity.security_notifications import notify_security_event
    from identity.session_service import revoke_all_sessions
    from identity.step_up import require_step_up

    await require_step_up(actor, action="account.delete")
    pending_until = (datetime.now(UTC) + timedelta(days=DELETION_GRACE_DAYS)).isoformat()
    req_id = await insert_deletion_request(user_id, pending_until=pending_until)
    from database import set_user_account_state

    await set_user_account_state(user_id, transition_account_state(str(actor.get("account_state") or "ACTIVE"), "DELETION_PENDING"))
    await revoke_all_sessions(user_id)
    await record_identity_event(event_type="account.deletion.requested", user_id=user_id, detail={"request_id": req_id})
    await notify_security_event(user_id, "security.deletion_requested", actor=actor)
    return {"request_id": req_id, "pending_until": pending_until, "status": "DELETION_PENDING"}


async def cancel_account_deletion(user_id: int) -> dict[str, Any]:
    from database import cancel_deletion_request, set_user_account_state
    from identity.account_states import AccountState
    from identity.identity_audit import record_identity_event

    await cancel_deletion_request(user_id)
    await set_user_account_state(user_id, AccountState.ACTIVE.value)
    await record_identity_event(event_type="account.deletion.cancelled", user_id=user_id)
    return {"status": AccountState.ACTIVE.value}


async def finalize_account_deletion(user_id: int) -> dict[str, Any]:
    from database import finalize_user_deletion
    from identity.identity_audit import record_identity_event

    result = await finalize_user_deletion(user_id)
    await record_identity_event(event_type="account.deletion.finalized", user_id=user_id, detail=result)
    return result
