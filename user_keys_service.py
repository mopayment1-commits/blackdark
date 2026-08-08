"""
BLACKDARK — User exchange API key management (encrypted vault).

App-layer Fernet encryption always. When Postgres is active, Fernet ciphertext
is additionally wrapped with pgcrypto (pgp_sym_encrypt) for DB at-rest defense.
"""

from __future__ import annotations

import logging
from typing import Any

from secrets_vault import decrypt_secret, encrypt_secret, mask_secret

logger = logging.getLogger("BLACKDARK.UserKeys")

_PGCRYPTO_PREFIX = "pgc1:"


async def _seal_for_storage(plaintext: str) -> tuple[str, str]:
    """Return (ciphertext, engine) — Fernet, optionally double-wrapped with pgcrypto."""
    fernet_ct = encrypt_secret(plaintext)
    try:
        from postgres_backend import pgp_sym_encrypt, use_postgres

        if use_postgres():
            wrapped = await pgp_sym_encrypt(fernet_ct)
            if wrapped:
                return f"{_PGCRYPTO_PREFIX}{wrapped}", "fernet+pgcrypto"
    except Exception:
        logger.debug("pgcrypto wrap skipped — Fernet-only storage", exc_info=True)
    return fernet_ct, "fernet"


async def _unseal_from_storage(ciphertext: str) -> str:
    raw = str(ciphertext or "")
    if raw.startswith(_PGCRYPTO_PREFIX):
        try:
            from postgres_backend import pgp_sym_decrypt

            inner = await pgp_sym_decrypt(raw[len(_PGCRYPTO_PREFIX) :])
            if inner:
                return decrypt_secret(inner)
        except Exception:
            logger.exception("pgcrypto unwrap failed")
            raise
    return decrypt_secret(raw)


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

    sealed_key, engine = await _seal_for_storage(api_key.strip())
    sealed_secret, _ = await _seal_for_storage(api_secret.strip())
    await upsert_user_api_key(
        user_id,
        exchange,
        sealed_key,
        sealed_secret,
        label=label,
    )
    return {
        "success": True,
        "exchange": exchange.lower(),
        "api_key_masked": mask_secret(api_key),
        "message": "API keys encrypted and stored securely.",
        "validation": validation.reason,
        "crypto_engine": engine,
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
        await _unseal_from_storage(str(row["api_key_encrypted"])),
        await _unseal_from_storage(str(row["api_secret_encrypted"])),
    )


async def remove_user_exchange_keys(user_id: int, exchange: str) -> dict[str, Any]:
    from database import delete_user_api_key

    deleted = await delete_user_api_key(user_id, exchange)
    return {"success": deleted, "exchange": exchange.lower()}
