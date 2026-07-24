"""
BLACKDARK — Auto-Execution Engine (Priority 5).

Dry-run by default; live mode requires AUTO_EXECUTION_ENABLED + Binance API keys.
Optional background loop executes top profitable arb signals when enabled.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
import asyncio
from datetime import datetime, timezone
from typing import Any, Literal
from urllib.parse import urlencode

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.ExecutionEngine")

Side = Literal["buy", "sell"]

_auto_task: Any = None


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


def _binance_base_url() -> str:
    testnet = os.getenv("BINANCE_TESTNET", "false").lower() in {"1", "true", "yes"}
    return "https://testnet.binance.vision" if testnet else "https://api.binance.com"


async def _place_binance_market_order(pair: str, side: Side, quantity: float) -> dict[str, Any]:
    """Signed Binance spot market order (testnet or live)."""
    api_key = os.getenv("BINANCE_API_KEY", "")
    secret = os.getenv("BINANCE_API_SECRET", "")
    if not api_key or not secret:
        raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET required for live orders")

    params = {
        "symbol": pair,
        "side": side.upper(),
        "type": "MARKET",
        "quantity": f"{quantity:.8f}".rstrip("0").rstrip("."),
        "timestamp": int(time.time() * 1000),
    }
    query = urlencode(params)
    signature = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    params["signature"] = signature

    url = f"{_binance_base_url()}/api/v3/order"
    headers = {"X-MBX-APIKEY": api_key}
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, params=params, headers=headers) as resp:
            data = await resp.json()
            if resp.status >= 400:
                raise RuntimeError(str(data.get("msg") or data))
            return data


async def get_execution_status() -> dict[str, Any]:
    from database import fetch_execution_state

    state = await fetch_execution_state()
    return {
        "panic_active": bool(state.get("panic_active")),
        "auto_execution_enabled": bool(state.get("auto_execution_enabled")),
        "live_mode_available": _live_enabled(),
        "auto_execution_live": bool(state.get("auto_execution_enabled")) and _live_enabled(),
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
        try:
            order = await _place_binance_market_order(pair, side, quantity)
            payload["executed"] = True
            payload["exchange_order"] = {
                "orderId": order.get("orderId"),
                "status": order.get("status"),
                "executedQty": order.get("executedQty"),
            }
            payload["message"] = f"Live {side} {asset} submitted to Binance."
            logger.info("Live order placed | %s %s $%.2f order_id=%s", side, asset, amount_usd, order.get("orderId"))
        except Exception as exc:
            payload["executed"] = False
            payload["message"] = f"Live order failed: {exc}"
            logger.exception("Live order failed | %s %s", side, asset)
    else:
        payload["message"] = f"Dry-run: would {side} {quantity:.6f} {asset} @ ${price:,.2f}"
        payload["executed"] = False

    await insert_execution_log(side, asset, json.dumps(payload), live=live)
    return payload


async def run_auto_execution_cycle() -> dict[str, Any]:
    """Scan profitable arb and execute top signal if auto-execution is enabled."""
    from arbitrage_service import scan_arbitrage_opportunities
    from database import fetch_execution_state

    state = await fetch_execution_state()
    if state.get("panic_active"):
        return {"skipped": True, "reason": "panic_active"}
    if not state.get("auto_execution_enabled"):
        return {"skipped": True, "reason": "auto_execution_disabled"}

    min_usdt = float(os.getenv("AUTO_EXECUTION_MIN_PROFIT_USDT", "0.25"))
    scan = await scan_arbitrage_opportunities(prefer_live=True, profitable_only=True)
    top = scan.get("top_opportunity")
    if not top or float(top.get("net_profit_usdt") or 0) < min_usdt:
        return {"skipped": True, "reason": "no_profitable_signal", "scanned": scan.get("profitable_count", 0)}

    asset = str(top.get("asset") or "BTC")
    side: Side = "buy" if top.get("kind") != "funding" else "buy"
    amount = float(os.getenv("AUTO_EXECUTION_QUOTE_USD", "100"))
    live = _live_enabled()
    result = await execute_order(asset, side, amount, dry_run=not live)
    return {
        "executed": True,
        "opportunity": top,
        "order": result,
        "mode": "live" if live else "dry_run",
    }


async def start_auto_execution_loop() -> Any:
    global _auto_task
    enabled = os.getenv("AUTO_EXECUTION_LOOP", "false").lower() in {"1", "true", "yes"}
    if not enabled:
        logger.info("Auto-execution loop disabled (AUTO_EXECUTION_LOOP=false).")
        return None
    if _auto_task is not None and not _auto_task.done():
        return _auto_task

    interval = max(60, int(os.getenv("AUTO_EXECUTION_INTERVAL_SEC", "120")))

    async def _loop() -> None:
        while True:
            try:
                outcome = await run_auto_execution_cycle()
                if outcome.get("executed"):
                    logger.info("Auto-execution cycle | mode=%s asset=%s", outcome.get("mode"), outcome.get("order", {}).get("symbol"))
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Auto-execution cycle failed")
            await asyncio.sleep(interval)

    _auto_task = asyncio.create_task(_loop(), name="auto-execution-loop")
    logger.info("Auto-execution loop started | interval=%ss", interval)
    return _auto_task


async def stop_auto_execution_loop() -> None:
    global _auto_task
    if _auto_task is not None:
        _auto_task.cancel()
        try:
            await _auto_task
        except asyncio.CancelledError:
            pass
        _auto_task = None
