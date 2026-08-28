"""
#907 Multi-Account Sync — uses Credential Vault Layer for read-only key retrieval.

Insight-only · Non-custodial — sync balances/positions, never trade.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("BLACKDARK.MultiAccountSync")

_FEATURE = "multi_account_sync"


async def sync_user_exchange_account(user_id: int, exchange: str) -> dict[str, Any]:
    """
    Sync a single exchange account for a user.
    Retrieves credentials from vault (backend-only) and fetches account snapshot.
    """
    from credential_vault_layer import retrieve_for_sync

    ex = exchange.strip().lower()
    creds = await retrieve_for_sync(user_id, ex, caller="multi_account_sync")
    if not creds:
        return {
            "ok": False,
            "user_id": user_id,
            "exchange": ex,
            "reason": "credentials_unavailable",
        }

    api_key, api_secret = creds
    if ex == "binance":
        snapshot = await _binance_account_snapshot(api_key, api_secret)
        return {
            "ok": snapshot.get("valid", False),
            "user_id": user_id,
            "exchange": ex,
            "snapshot": snapshot,
            "credentials_exposed": False,
        }

    return {
        "ok": False,
        "user_id": user_id,
        "exchange": ex,
        "reason": "unsupported_exchange",
    }


async def sync_all_user_accounts(user_id: int) -> dict[str, Any]:
    """Sync all linked exchange accounts for a user."""
    from database import fetch_user_api_keys

    rows = await fetch_user_api_keys(user_id)
    results: list[dict[str, Any]] = []
    for row in rows:
        ex = str(row.get("exchange") or "")
        if ex:
            results.append(await sync_user_exchange_account(user_id, ex))
    return {
        "ok": all(r.get("ok") for r in results) if results else True,
        "user_id": user_id,
        "accounts": results,
        "feature": _FEATURE,
    }


async def _binance_account_snapshot(api_key: str, api_secret: str) -> dict[str, Any]:
    import time

    import aiohttp

    from execution_keys import _binance_base_url, _sign_params

    params = _sign_params(api_secret, {"timestamp": int(time.time() * 1000)})
    url = f"{_binance_base_url()}/api/v3/account"
    headers = {"X-MBX-APIKEY": api_key}
    timeout = aiohttp.ClientTimeout(total=15)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params, headers=headers) as resp:
                data = await resp.json()
                if resp.status == 200:
                    balances = [
                        {"asset": b["asset"], "free": b["free"], "locked": b["locked"]}
                        for b in (data.get("balances") or [])
                        if float(b.get("free", 0)) > 0 or float(b.get("locked", 0)) > 0
                    ]
                    return {
                        "valid": True,
                        "can_trade": bool(data.get("canTrade")),
                        "can_withdraw": bool(data.get("canWithdraw")),
                        "balances": balances[:50],
                        "balance_count": len(balances),
                    }
                return {"valid": False, "reason": data.get("msg", "api_error")}
    except Exception as exc:
        logger.debug("Binance sync snapshot failed", exc_info=True)
        return {"valid": False, "reason": str(exc)}


def multi_account_sync_status() -> dict[str, Any]:
    from credential_vault_layer import credential_vault_status

    vault = credential_vault_status()
    return {
        "ok": True,
        "feature": _FEATURE,
        "credential_vault": vault,
        "non_custodial": True,
        "read_only_sync": True,
        "trade_execution": False,
    }
