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


async def _fetch_ticker(pair: str, *, exchange: str = "binance") -> dict | None:
    from live_book_hub import get_best_price

    symbol = pair.replace("USDT", "") + "/USDT" if pair.endswith("USDT") else pair
    live = get_best_price(exchange, symbol)
    if live:
        return {"price": live["mid"], "bid": live["bid"], "ask": live["ask"], "source": "websocket_live"}

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
    dry_run = os.getenv("AUTO_EXECUTION_DRY_RUN", "true").lower() in {"1", "true", "yes"}
    live_flag = _live_enabled()
    has_keys = bool(os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_API_SECRET"))
    return {
        "panic_active": bool(state.get("panic_active")),
        "auto_execution_enabled": bool(state.get("auto_execution_enabled")),
        "live_mode_available": live_flag and has_keys and not dry_run,
        "auto_execution_live": bool(state.get("auto_execution_enabled")) and live_flag and has_keys and not dry_run,
        "dry_run_mode": dry_run or not live_flag,
        "has_api_keys": has_keys,
        "auto_execution_loop": os.getenv("AUTO_EXECUTION_LOOP", "true").lower() in {"1", "true", "yes"},
        "updated_at": state.get("updated_at"),
        "disclaimer": "Dry-run is default. Live requires keys + AUTO_EXECUTION_ENABLED=true + DRY_RUN=false.",
        "keys_file": "keys/exchange_keys.env",
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

    dry_run = os.getenv("AUTO_EXECUTION_DRY_RUN", "true").lower() in {"1", "true", "yes"}
    if enabled and not dry_run and not _live_enabled():
        return {
            "success": False,
            "message": "Set AUTO_EXECUTION_ENABLED=true, AUTO_EXECUTION_DRY_RUN=false, and Binance API keys.",
        }
    if enabled and not dry_run:
        if not (os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_API_SECRET")):
            return {
                "success": False,
                "message": "BINANCE_API_KEY and BINANCE_API_SECRET required for live auto-execution.",
            }
    await set_execution_state(auto_execution_enabled=enabled, panic_active=False)
    mode = "live" if enabled and _live_enabled() and not dry_run else "dry_run"
    return {"success": True, "auto_execution_enabled": enabled, "mode": mode if enabled else "off"}


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

    from risk_manager import evaluate_execution_risk, is_trading_frozen, register_stop_loss

    if is_trading_frozen():
        return {
            "success": False,
            "blocked": True,
            "reason": "trading_frozen",
            "message": "Risk manager has frozen trading (data poisoning or manual freeze).",
        }

    risk = evaluate_execution_risk({"asset": asset, "slippage_bps": 0})
    if not risk.allowed:
        return {
            "success": False,
            "blocked": True,
            "reason": risk.reason,
            "message": f"Risk gate blocked: {risk.reason}",
        }

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

    if payload.get("executed") or not live:
        register_stop_loss(asset, price, side)

    return payload


async def try_execute_from_opportunity(opportunity: dict[str, Any]) -> dict[str, Any]:
    """Fast path: execute (or dry-run) immediately on a hot arbitrage signal."""
    from database import fetch_execution_state
    from risk_manager import is_trading_frozen

    if is_trading_frozen():
        return {"skipped": True, "reason": "trading_frozen"}

    state = await fetch_execution_state()
    if state.get("panic_active"):
        return {"skipped": True, "reason": "panic_active"}

    live = _live_enabled()
    dry_run_default = os.getenv("AUTO_EXECUTION_DRY_RUN", "true").lower() in {"1", "true", "yes"}
    if not state.get("auto_execution_enabled"):
        if live or not dry_run_default:
            return {"skipped": True, "reason": "auto_execution_disabled"}

    min_usdt = float(os.getenv("AUTO_EXECUTION_MIN_PROFIT_USDT", "0.25"))
    profit = float(opportunity.get("net_profit_usdt") or 0)
    if profit < min_usdt:
        return {"skipped": True, "reason": "below_min_profit", "profit_usdt": profit}

    from risk_manager import evaluate_execution_risk

    risk = evaluate_execution_risk(opportunity)
    if not risk.allowed:
        return {"skipped": True, "reason": risk.reason, "risk_blocked": True}

    kind = str(opportunity.get("kind") or "")
    if kind == "triangular" and float(opportunity.get("data_age_sec") or 0) > 1.0:
        return {"skipped": True, "reason": "triangular_stale_for_execution"}

    asset = str(opportunity.get("asset") or "BTC")
    side: Side = "buy"
    amount = float(os.getenv("AUTO_EXECUTION_QUOTE_USD", "100"))
    result = await execute_order(asset, side, amount, dry_run=not live)
    return {
        "executed": True,
        "fast_path": True,
        "opportunity": opportunity,
        "order": result,
        "mode": "live" if live else "dry_run",
    }


async def run_auto_execution_cycle() -> dict[str, Any]:
    """Scan profitable arb and execute top signal if auto-execution is enabled."""
    import os

    if os.getenv("CEX_DEX_AUTO_EXEC", "false").lower() in {"1", "true", "yes"}:
        try:
            from bd_platform.cex_dex_executor import run_cex_dex_cycle

            cex_dex = await run_cex_dex_cycle(
                quote_usd=float(os.getenv("CEX_DEX_QUOTE_USD", "500")),
            )
            if cex_dex.get("executed") and not cex_dex.get("skipped"):
                return {"executed": True, "mode": "cex_dex", **cex_dex}
        except Exception:
            logger.exception("CEX↔DEX auto cycle failed")

    from scan_coordinator import get_shared_scan

    min_usdt = float(os.getenv("AUTO_EXECUTION_MIN_PROFIT_USDT", "0.25"))
    scan = await get_shared_scan(profitable_only=True, prefer_live=False)
    top = scan.get("top_opportunity")
    if not top or float(top.get("net_profit_usdt") or 0) < min_usdt:
        return {"skipped": True, "reason": "no_profitable_signal", "scanned": scan.get("profitable_count", 0)}

    top_exec = dict(top)
    top_exec["data_age_sec"] = scan.get("data_age_sec")
    return await try_execute_from_opportunity(top_exec)


async def start_auto_execution_loop() -> Any:
    global _auto_task
    enabled = os.getenv("AUTO_EXECUTION_LOOP", "true").lower() in {"1", "true", "yes"}
    if not enabled:
        logger.info("Auto-execution loop disabled (AUTO_EXECUTION_LOOP=false).")
        return None
    if _auto_task is not None and not _auto_task.done():
        return _auto_task

    interval = max(1, int(os.getenv("AUTO_EXECUTION_INTERVAL_SEC", str(getattr(config, "AUTO_EXECUTION_INTERVAL_SEC", 1)))))

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
