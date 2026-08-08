"""
BLACKDARK — API key security guard (regulatory / custody isolation).

Protects user exchange keys from misuse after server compromise:
- Trade-only validation (reject withdraw-enabled keys)
- Per-user vault required for live execution in production
- Block plaintext env operator keys in production
- Key access audit trail
- Wash-trade guard integration hook
"""

from __future__ import annotations

import logging
import os
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC
from pathlib import Path
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.ApiKeySecurityGuard")

_audit_log: deque[dict[str, Any]] = deque(maxlen=500)


def _enabled() -> bool:
    return getattr(config, "API_KEY_SECURITY_GUARD_ENABLED", True)


def _is_production() -> bool:
    """ENV=production is never overridden by LOCAL_DEV."""
    env = os.getenv("ENV", os.getenv("RAILWAY_ENVIRONMENT", "")).strip().lower()
    return env in {"production", "prod"}


def block_withdraw_enabled_keys() -> bool:
    return getattr(config, "API_KEY_BLOCK_WITHDRAW_ENABLED", True)


def require_user_vault_for_live() -> bool:
    return getattr(config, "API_KEY_REQUIRE_USER_VAULT_LIVE", True)


def block_env_keys_in_production() -> bool:
    return getattr(config, "API_KEY_BLOCK_ENV_KEYS_IN_PRODUCTION", True)


@dataclass
class KeyValidationResult:
    exchange: str
    allowed: bool
    valid: bool = False
    can_trade: bool = False
    can_withdraw: bool = False
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)


def record_key_access(
    *,
    user_id: int | None,
    exchange: str,
    action: str,
    allowed: bool,
    reason: str = "",
) -> None:
    entry = {
        "timestamp": time.time(),
        "user_id": user_id,
        "exchange": exchange.lower(),
        "action": action,
        "allowed": allowed,
        "reason": reason,
    }
    _audit_log.append(entry)
    try:
        audit_path = Path(__file__).resolve().parent / "data" / "api_key_access_audit.jsonl"
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        from datetime import datetime

        row = {**entry, "ts": datetime.now(UTC).isoformat()}
        with audit_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        logger.debug("API key audit persist failed", exc_info=True)
    logger.info(
        "Key access audit | user_id=%s exchange=%s action=%s allowed=%s reason=%s",
        user_id,
        exchange,
        action,
        allowed,
        reason or "ok",
    )


async def validate_exchange_api_key(
    exchange: str,
    api_key: str,
    api_secret: str,
) -> KeyValidationResult:
    """Verify keys are valid and safe (trade-only, no withdraw)."""
    ex = exchange.strip().lower()
    result = KeyValidationResult(exchange=ex, allowed=False)

    if not _enabled():
        result.allowed = True
        result.reason = "guard_disabled"
        return result

    if not api_key.strip() or not api_secret.strip():
        result.reason = "missing_credentials"
        return result

    if ex == "binance":
        from execution_keys import verify_binance_keys

        verify = await verify_binance_keys(api_key.strip(), api_secret.strip())
        result.valid = bool(verify.get("valid"))
        result.can_trade = bool(verify.get("can_trade"))
        result.can_withdraw = bool(verify.get("can_withdraw"))
        result.details = verify

        if not result.valid:
            result.reason = str(verify.get("reason") or verify.get("message") or "invalid_keys")
            return result
        if not result.can_trade:
            result.reason = "trade_disabled"
            return result
        if block_withdraw_enabled_keys() and result.can_withdraw:
            result.reason = "withdraw_enabled_rejected"
            logger.warning(
                "API key rejected — withdraw enabled | exchange=%s (trade-only required)",
                ex,
            )
            return result
        result.allowed = True
        result.reason = "ok"
        return result

    result.reason = "unsupported_exchange_validation"
    result.allowed = False
    return result


def live_execution_allowed(*, user_id: int | None, using_env_keys: bool) -> tuple[bool, str]:
    """Hard gate before any live order uses decrypted credentials."""
    if not _enabled():
        return True, "guard_disabled"

    if _is_production() and block_env_keys_in_production() and using_env_keys:
        return False, "env_keys_blocked_in_production"

    if _live_mode_requested() and require_user_vault_for_live() and user_id is None:
        return False, "user_vault_required_for_live"

    return True, "ok"


def _live_mode_requested() -> bool:
    dry_run = os.getenv("AUTO_EXECUTION_DRY_RUN", "true").lower() in {"1", "true", "yes"}
    live = os.getenv("AUTO_EXECUTION_ENABLED", "false").lower() in {"1", "true", "yes"}
    return live and not dry_run


def resolve_credential_source(user_id: int | None, has_user_creds: bool) -> str:
    if has_user_creds:
        return "user_vault"
    if os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_API_SECRET"):
        return "env_operator"
    return "none"


def api_key_security_status() -> dict[str, Any]:
    recent_denied = sum(1 for e in _audit_log if not e.get("allowed"))
    return {
        "enabled": _enabled(),
        "production_mode": _is_production(),
        "block_withdraw_enabled_keys": block_withdraw_enabled_keys(),
        "require_user_vault_for_live": require_user_vault_for_live(),
        "block_env_keys_in_production": block_env_keys_in_production(),
        "encryption": "fernet_aes128_cbc",
        "vault_master_key_required_in_production": True,
        "hashicorp_vault_available": bool(os.getenv("VAULT_ADDR")),
        "live_mode": _live_mode_requested(),
        "audit_events_buffered": len(_audit_log),
        "audit_denied_total": recent_denied,
        "recent_audit": list(_audit_log)[-10:],
        "policy": (
            "User keys encrypted at rest (Fernet). Live execution requires per-user vault "
            "in production. Withdraw-enabled API keys rejected. Env plaintext keys blocked "
            "in production. Full HSM/KMS recommended for acquisition-grade custody."
        ),
        "compliance_notes": [
            "Store trade-only keys with exchange-side IP whitelist",
            "Never commit keys/exchange_keys.env to git",
            "Use SECRETS_MASTER_KEY from KMS in production",
            "Rotate keys on any suspected breach",
        ],
    }
