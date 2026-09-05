"""
BLACKDARK — User exchange API key management (Credential Vault Layer / #907).
"""

from __future__ import annotations

from typing import Any


async def store_user_exchange_keys(
    user_id: int,
    exchange: str,
    api_key: str,
    api_secret: str,
    *,
    label: str = "",
) -> dict[str, Any]:
    from credential_vault_layer import store_sync_credential

    return await store_sync_credential(
        user_id, exchange, api_key, api_secret, label=label, actor="user"
    )


async def list_user_exchange_keys(user_id: int) -> list[dict[str, Any]]:
    from database import fetch_user_api_keys

    rows = await fetch_user_api_keys(user_id)
    return [
        {
            "id": r["id"],
            "exchange": r["exchange"],
            "label": r.get("label"),
            "api_key_masked": "****",
            "read_only_sync": True,
            "created_at": r.get("created_at"),
            "updated_at": r.get("updated_at"),
        }
        for r in rows
    ]


async def get_user_exchange_credentials(
    user_id: int,
    exchange: str,
    *,
    caller: str | None = None,
) -> tuple[str, str] | None:
    """
    Backend-only retrieval — blocked for API/UI paths.
    Use caller='multi_account_sync' from sync jobs only.
    """
    from credential_vault_layer import retrieve_for_sync

    allowed: tuple[str, ...] = (
        "multi_account_sync",
        "sync_connector",
        "credential_vault_self_test",
    )
    if caller not in allowed:
        from credential_vault_layer import record_vault_audit

        record_vault_audit(
            user_id=user_id,
            exchange=exchange,
            action="retrieve",
            allowed=False,
            reason="client_exposure_blocked",
            actor=caller or "unknown",
        )
        return None
    return await retrieve_for_sync(user_id, exchange, caller=caller)  # type: ignore[arg-type]


async def remove_user_exchange_keys(user_id: int, exchange: str) -> dict[str, Any]:
    from credential_vault_layer import delete_sync_credential

    return await delete_sync_credential(user_id, exchange, actor="user")
