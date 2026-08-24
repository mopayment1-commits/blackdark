"""
BLACKDARK — User exchange API key management (encrypted vault).
"""

from __future__ import annotations

from typing import Any

from secrets_vault import decrypt_secret, encrypt_secret, mask_secret


async def store_user_exchange_keys(
    user_id: int,
    exchange: str,
    api_key: str,
    api_secret: str,
    *,
    label: str = "",
) -> dict[str, Any]:
    from api_key_security_guard import record_key_access, validate_exchange_api_key
    from database import upsert_user_api_key

    validation = await validate_exchange_api_key(exchange, api_key, api_secret)
    record_key_access(
        user_id=user_id,
        exchange=exchange,
        action="store_keys",
        allowed=validation.allowed,
        reason=validation.reason,
    )
    if not validation.allowed:
        return {
            "success": False,
            "exchange": exchange.lower(),
            "reason": validation.reason,
            "message": f"API key rejected: {validation.reason}",
        }

    await upsert_user_api_key(
        user_id,
        exchange,
        encrypt_secret(api_key.strip()),
        encrypt_secret(api_secret.strip()),
        label=label,
    )

    try:
        from bd_platform.secrets_key_vault import create_secret

        vault_key = create_secret(
            tenant_id="default",
            user_id=user_id,
            name=f"{exchange.lower()}_api",
            value=f"{api_key.strip()}:{api_secret.strip()}",
            permission="trading",
            secret_type="exchange_api",
            actor=f"user:{user_id}",
        )
        vault_secret_id = vault_key.get("secret_id")
    except Exception:
        vault_secret_id = None

    return {
        "success": True,
        "exchange": exchange.lower(),
        "api_key_masked": mask_secret(api_key),
        "message": "API keys encrypted and stored securely.",
        "validation": validation.reason,
        "vault_secret_id": vault_secret_id,
    }


async def list_user_exchange_keys(user_id: int) -> list[dict[str, Any]]:
    from database import fetch_user_api_keys

    rows = await fetch_user_api_keys(user_id)
    return [
        {
            "id": r["id"],
            "exchange": r["exchange"],
            "label": r.get("label"),
            "api_key_masked": "****",
            "created_at": r.get("created_at"),
            "updated_at": r.get("updated_at"),
        }
        for r in rows
    ]


async def get_user_exchange_credentials(user_id: int, exchange: str) -> tuple[str, str] | None:
    from database import fetch_user_api_key_secrets

    row = await fetch_user_api_key_secrets(user_id, exchange)
    if not row:
        return None
    return (
        decrypt_secret(str(row["api_key_encrypted"])),
        decrypt_secret(str(row["api_secret_encrypted"])),
    )


async def remove_user_exchange_keys(user_id: int, exchange: str) -> dict[str, Any]:
    from database import delete_user_api_key

    deleted = await delete_user_api_key(user_id, exchange)
    return {"success": deleted, "exchange": exchange.lower()}
