"""
BLACKDARK — Auto-Execution Engine (Wave 4C) with Panic Button.

Dry-run by default; live mode requires explicit env flag + API keys.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Literal

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.ExecutionEngine")

Side = Literal["buy", "sell"]


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_symbol(symbol: str) -> tuple[str, str]:
    cleaned = symbol.upper().strip().replace("/", "").replace("-", "")
    if cleaned.endswith("USDT"):
        return cleaned[:-4], cleaned
    return cleaned, f"{cleaned}USDT"


async def _fetch_ticker(pair: str) -> dict | None:
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return {"price": float(data["lastPrice"])}
    except (aiohttp.ClientError, KeyError, TypeError, ValueError):
        return None


def _live_enabled() -> bool:
    return os.getenv("AUTO_EXECUTION_ENABLED", "false").lower() in {"1", "true", "yes"}


async def get_execution_status() -> dict[str, Any]:
    from database import fetch_execution_state

    state = await fetch_execution_state()
    return {
        "panic_active": bool(state.get("panic_active")),
        "auto_execution_enabled": bool(state.get("auto_execution_enabled")) and _live_enabled(),
        "live_mode_available": _live_enabled(),
        "has_api_keys": bool(os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_API_SECRET")),
        "updated_at": state.get("updated_at"),
        "disclaimer": "Dry-run is default. Live execution requires AUTO_EXECUTION_ENABLED=true.",
    }


async def trigger_panic() -> dict[str, Any]:
    from database import set_execution_state

    await set_execution_state(panic_active=True)
    logger.warning("PANIC BUTTON activated — all execution halted")
    return {"panic_active": True, "message": "All auto-execution halted immediately."}


async def resume_execution() -> dict[str, Any]:
    from database import set_execution_state

    await set_execution_state(panic_active=False)
    return {"panic_active": False, "message": "Execution resumed (still dry-run unless live mode enabled)."}


async def set_auto_execution(enabled: bool) -> dict[str, Any]:
    from database import set_execution_state

    if enabled and not _live_enabled():
        return {
            "success": False,
            "message": "Set AUTO_EXECUTION_ENABLED=true and API keys in .env first.",
        }
    await set_execution_state(auto_execution_enabled=enabled, panic_active=False)
    return {"success": True, "auto_execution_enabled": enabled}


async def execute_order(
    symbol: str,
    side: Side,
    amount_usd: float,
    *,
    dry_run: bool | None = None,
) -> dict[str, Any]:
    """Execute or simulate a spot order."""
    from database import fetch_execution_state, insert_execution_log

    state = await fetch_execution_state()
    if state.get("panic_active"):
        return {
            "success": False,
            "blocked": True,
            "reason": "panic_active",
            "message": "Panic button is active — no orders allowed.",
        }

    asset, pair = _normalize_symbol(symbol)
    market = await _fetch_ticker(pair)
    if market is None:
        raise ValueError(f"Symbol {asset} not found")

    price = float(market["price"])
    fee = amount_usd * config.DEFAULT_TAKER_FEE
    quantity = (amount_usd - fee) / price if side == "buy" else amount_usd / price

    use_dry_run = True if dry_run is None else dry_run
    live = _live_enabled() and not use_dry_run and state.get("auto_execution_enabled")

    payload = {
        "symbol": asset,
        "pair": pair,
        "side": side,
        "amount_usd": round(amount_usd, 2),
        "price": price,
        "quantity": round(quantity, 8),
        "fee_usd": round(fee, 4),
        "mode": "dry_run" if not live else "live",
        "timestamp": _utcnow_iso(),
    }

    if live:
        payload["message"] = "Live execution placeholder — wire exchange API keys in production."
        payload["executed"] = False
        logger.info("Live order requested | %s %s $%.2f", side, asset, amount_usd)
    else:
        payload["message"] = f"Dry-run: would {side} {quantity:.6f} {asset} @ ${price:,.2f}"
        payload["executed"] = False

    await insert_execution_log(side, asset, json.dumps(payload), live=live)
    return payload
