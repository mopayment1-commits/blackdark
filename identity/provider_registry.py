"""Provider registry — ID-065, ID-008."""

from __future__ import annotations

from typing import Any


async def link_provider(
    user_id: int,
    *,
    provider: str,
    provider_subject: str,
    verified_at: str | None = None,
    require_step_up: bool = True,
    actor_user: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from database import fetch_provider_link, insert_provider_link
    from identity.identity_audit import record_identity_event
    from identity.step_up import require_step_up

    if require_step_up and actor_user:
        await require_step_up(actor_user, action="provider.link")
    existing = await fetch_provider_link(provider, provider_subject)
    if existing and int(existing["user_id"]) != user_id:
        raise ValueError("Provider identity already linked to another account")
    row = await insert_provider_link(
        user_id,
        provider=provider,
        provider_subject=provider_subject,
        verified_at=verified_at,
    )
    await record_identity_event(
        event_type="provider.link",
        user_id=user_id,
        detail={"provider": provider, "provider_subject": provider_subject[:8] + "…"},
    )
    return row


async def unlink_provider(
    user_id: int,
    *,
    provider: str,
    actor_user: dict[str, Any],
) -> dict[str, Any]:
    from database import count_user_auth_methods, delete_provider_link
    from identity.identity_audit import record_identity_event
    from identity.step_up import require_step_up

    await require_step_up(actor_user, action="provider.unlink")
    methods = await count_user_auth_methods(user_id)
    if methods.get("total", 0) <= 1:
        raise ValueError("Cannot remove last login method")
    ok = await delete_provider_link(user_id, provider)
    if not ok:
        raise ValueError("Provider link not found")
    await record_identity_event(event_type="provider.unlink", user_id=user_id, detail={"provider": provider})
    return {"unlinked": provider}


async def find_user_by_provider(provider: str, provider_subject: str) -> dict[str, Any] | None:
    from database import fetch_provider_link

    row = await fetch_provider_link(provider, provider_subject)
    if not row:
        return None
    from database import fetch_user_by_id

    return await fetch_user_by_id(int(row["user_id"]))
