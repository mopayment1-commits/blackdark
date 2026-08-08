"""
BLACKDARK — Auto-Execution Engine (Priority 5).

Dry-run by default; live mode requires AUTO_EXECUTION_ENABLED + credentials
that pass api_key_security_guard (user vault preferred; env keys blocked in prod).
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any, Literal
from urllib.parse import urlencode

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.ExecutionEngine")

Side = Literal["buy", "sell"]

_auto_task: Any = None


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


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


def _dry_run_default() -> bool:
    return os.getenv("AUTO_EXECUTION_DRY_RUN", "true").lower() in {"1", "true", "yes"}


def _binance_base_url() -> str:
    testnet = os.getenv("BINANCE_TESTNET", "false").lower() in {"1", "true", "yes"}
    return "https://testnet.binance.vision" if testnet else "https://api.binance.com"


async def resolve_binance_credentials(
    user_id: int | None = None,
) -> tuple[str, str, str]:
    """
    Resolve credentials with vault preference.
    Returns (api_key, api_secret, source) where source is user_vault|env_operator.
    """
    if user_id is not None:
        try:
            from user_keys_service import get_user_exchange_credentials

            creds = await get_user_exchange_credentials(int(user_id), "binance")
            if creds and creds[0] and creds[1]:
                return creds[0], creds[1], "user_vault"
        except Exception:
            logger.debug("User vault credential lookup failed", exc_info=True)

    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    secret = os.getenv("BINANCE_API_SECRET", "").strip()
    if api_key and secret:
        return api_key, secret, "env_operator"
    raise ValueError("No Binance credentials available (user vault or env keys)")


async def _place_binance_market_order(
    pair: str,
    side: Side,
    quantity: float,
    *,
    user_id: int | None = None,
) -> dict[str, Any]:
    """Signed Binance spot market order (testnet or live) with security gate."""
    from api_key_security_guard import live_execution_allowed, record_key_access

    api_key, secret, source = await resolve_binance_credentials(user_id)
    using_env = source == "env_operator"
    allowed, reason = live_execution_allowed(user_id=user_id, using_env_keys=using_env)
    record_key_access(
        user_id=user_id,
        exchange="binance",
        action="live_order",
        allowed=allowed,
        reason=reason,
    )
    if not allowed:
        raise RuntimeError(f"Live execution blocked by API key security guard: {reason}")

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
    from api_key_security_guard import api_key_security_status, live_execution_allowed
    from database import fetch_execution_state

    state = await fetch_execution_state()
    dry_run = _dry_run_default()
    live_flag = _live_enabled()
    has_env_keys = bool(os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_API_SECRET"))
    env_allowed, env_reason = live_execution_allowed(user_id=None, using_env_keys=True)
    return {
        "panic_active": bool(state.get("panic_active")),
        "auto_execution_enabled": bool(state.get("auto_execution_enabled")),
        "live_mode_available": live_flag and has_env_keys and not dry_run and env_allowed,
        "auto_execution_live": bool(state.get("auto_execution_enabled"))
        and live_flag
        and has_env_keys
        and not dry_run
        and env_allowed,
        "dry_run_mode": dry_run or not live_flag,
        "has_api_keys": has_env_keys,
        "env_keys_live_allowed": env_allowed,
        "env_keys_block_reason": env_reason if not env_allowed else "",
        "auto_execution_loop": os.getenv("AUTO_EXECUTION_LOOP", "false").lower()
        in {"1", "true", "yes"},
        "updated_at": state.get("updated_at"),
        "api_key_security": api_key_security_status(),
        "disclaimer": (
            "Dry-run is default. Live requires credentials that pass "
            "api_key_security_guard + AUTO_EXECUTION_ENABLED=true + DRY_RUN=false."
        ),
        "keys_file": "keys/exchange_keys.env",
    }


async def trigger_panic(*, user_id: int | None = None) -> dict[str, Any]:
    """Halt all auto-execution. Optional user_id is for audit only."""
    from database import set_execution_state

    await set_execution_state(panic_active=True)
    logger.warning("PANIC BUTTON activated — all execution halted | user_id=%s", user_id)
    return {
        "panic_active": True,
        "message": "All auto-execution halted immediately.",
        "triggered_by": user_id,
    }


async def resume_execution() -> dict[str, Any]:
    from database import set_execution_state

    await set_execution_state(panic_active=False)
    return {"panic_active": False, "message": "Execution resumed (still dry-run unless live mode enabled)."}


async def set_auto_execution(enabled: bool) -> dict[str, Any]:
    from api_key_security_guard import live_execution_allowed
    from database import set_execution_state

    dry_run = _dry_run_default()
    if enabled and not dry_run and not _live_enabled():
        return {
            "success": False,
            "message": "Set AUTO_EXECUTION_ENABLED=true, AUTO_EXECUTION_DRY_RUN=false, and valid credentials.",
        }
    if enabled and not dry_run:
        allowed, reason = live_execution_allowed(user_id=None, using_env_keys=True)
        has_keys = bool(os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_API_SECRET"))
        if not has_keys:
            return {
                "success": False,
                "message": "BINANCE_API_KEY/SECRET or user vault credentials required for live auto-execution.",
            }
        if not allowed:
            return {
                "success": False,
                "message": f"Live execution blocked: {reason}",
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
    user_id: int | None = None,
) -> dict[str, Any]:
    """Execute or simulate a spot order with security + risk gates."""
    from api_key_security_guard import live_execution_allowed
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

    use_dry_run = _dry_run_default() if dry_run is None else dry_run
    live_requested = _live_enabled() and not use_dry_run and state.get("auto_execution_enabled")

    credential_source = "none"
    if live_requested:
        try:
            _key, _secret, credential_source = await resolve_binance_credentials(user_id)
        except ValueError as exc:
            return {
                "success": False,
                "blocked": True,
                "reason": "missing_credentials",
                "message": str(exc),
            }
        allowed, reason = live_execution_allowed(
            user_id=user_id,
            using_env_keys=(credential_source == "env_operator"),
        )
        if not allowed:
            return {
                "success": False,
                "blocked": True,
                "reason": reason,
                "message": f"API key security guard blocked live order: {reason}",
            }

    live = bool(live_requested)

    payload = {
        "symbol": asset,
        "pair": pair,
        "side": side,
        "amount_usd": round(amount_usd, 2),
        "price": price,
        "quantity": round(quantity, 8),
        "fee_usd": round(fee, 4),
        "mode": "dry_run" if not live else "live",
        "credential_source": credential_source,
        "user_id": user_id,
        "timestamp": _utcnow_iso(),
    }

    if live:
        try:
            order = await _place_binance_market_order(
                pair, side, quantity, user_id=user_id
            )
            payload["executed"] = True
            payload["exchange_order"] = {
                "orderId": order.get("orderId"),
                "status": order.get("status"),
                "executedQty": order.get("executedQty"),
            }
            payload["message"] = f"Live {side} {asset} submitted to Binance."
            logger.info(
                "Live order placed | %s %s $%.2f order_id=%s source=%s",
                side,
                asset,
                amount_usd,
                order.get("orderId"),
                credential_source,
            )
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


def _infer_execution_side(opportunity: dict[str, Any]) -> Side:
    """Infer first-leg side from opportunity structure (not always buy)."""
    explicit = str(opportunity.get("side") or opportunity.get("action") or "").lower()
    if explicit in {"buy", "sell"}:
        return explicit  # type: ignore[return-value]
    if opportunity.get("sell_first") or opportunity.get("short_first"):
        return "sell"
    kind = str(opportunity.get("kind") or "").lower()
    if kind == "funding":
        # Negative funding often favors shorting the high-funding leg first.
        funding = float(opportunity.get("funding_spread_bps") or opportunity.get("funding_rate") or 0)
        if funding > 0:
            return "sell"
    buy_price = float(opportunity.get("buy_price") or 0)
    sell_price = float(opportunity.get("sell_price") or 0)
    if buy_price > 0 and sell_price > 0 and sell_price < buy_price:
        return "sell"
    return "buy"


async def try_execute_from_opportunity(
    opportunity: dict[str, Any],
    *,
    user_id: int | None = None,
) -> dict[str, Any]:
    """Fast path: execute (or dry-run) immediately on a hot arbitrage signal."""
    from database import fetch_execution_state
    from risk_manager import is_trading_frozen

    if is_trading_frozen():
        return {"skipped": True, "reason": "trading_frozen"}

    state = await fetch_execution_state()
    if state.get("panic_active"):
        return {"skipped": True, "reason": "panic_active"}

    live = _live_enabled()
    dry_run_default = _dry_run_default()
    if not state.get("auto_execution_enabled") and (live or not dry_run_default):
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

    # Constitution fail-closed: recompute missing Truth / Half-Life / Veto before exec.
    try:
        from constitution_gates import ensure_execution_gates

        opportunity = ensure_execution_gates(opportunity)
    except Exception:
        logger.debug("execution gate recompute failed", exc_info=True)

    if opportunity.get("gates_missing"):
        return {"skipped": True, "reason": "constitution_gates_missing", "opportunity": {
            "net_edge_truth": opportunity.get("net_edge_truth"),
            "opportunity_half_life": opportunity.get("opportunity_half_life"),
        }}

    conflict = opportunity.get("dimension_conflict") or {}
    if conflict.get("veto") or conflict.get("abstain"):
        return {"skipped": True, "reason": "dimension_conflict", "conflict": conflict}
    truth = opportunity.get("net_edge_truth") or {}
    if truth.get("reject"):
        return {"skipped": True, "reason": "net_edge_truth_reject", "net_edge_truth": truth}
    if opportunity.get("half_life_killed"):
        return {
            "skipped": True,
            "reason": "opportunity_half_life_expired",
            "opportunity_half_life": opportunity.get("opportunity_half_life"),
        }
    half = opportunity.get("opportunity_half_life") or {}
    try:
        remain = float(half.get("remaining_seconds"))
        p_gone = float(half.get("disappearance_probability") or 0)
    except (TypeError, ValueError):
        remain, p_gone = None, 0.0
    if remain is None:
        return {"skipped": True, "reason": "opportunity_half_life_unavailable", "opportunity_half_life": half}
    if remain <= 2.0 or p_gone >= 0.92:
        return {
            "skipped": True,
            "reason": "opportunity_half_life_expired",
            "opportunity_half_life": half,
        }

    asset = str(opportunity.get("asset") or "BTC")
    side = _infer_execution_side(opportunity)
    amount = float(os.getenv("AUTO_EXECUTION_QUOTE_USD", "100"))
    # Never escalate to live from opportunity auto-path unless flags + guard allow.
    result = await execute_order(
        asset,
        side,
        amount,
        dry_run=bool(dry_run_default or not live),
        user_id=user_id,
    )
    return {
        "executed": bool(result.get("executed")),
        "fast_path": True,
        "opportunity": opportunity,
        "order": result,
        "side": side,
        "mode": result.get("mode"),
    }


async def run_auto_execution_cycle() -> dict[str, Any]:
    """Scan profitable arb and execute top signal if auto-execution is enabled."""
    # Built-in stop-loss monitor — flatten/halt when registered stops hit
    try:
        from risk_manager import active_stop_loss_symbols, check_stop_losses, freeze_trading

        prices: dict[str, float] = {}
        for sym in active_stop_loss_symbols():
            try:
                market = await _fetch_ticker(f"{sym}USDT")
                if market and market.get("price") is not None:
                    prices[sym] = float(market["price"])
            except Exception:
                continue
        if prices:
            triggered = check_stop_losses(prices)
            if triggered:
                freeze_trading(
                    f"stop_loss_triggered:{','.join(t.get('symbol','?') for t in triggered[:5])}",
                    duration_sec=int(os.getenv("RISK_STOP_LOSS_FREEZE_SEC", "120")),
                )
                flatten_results = []
                for hit in triggered:
                    try:
                        side = "sell" if hit.get("side") == "buy" else "buy"
                        amt = float(os.getenv("AUTO_EXECUTION_QUOTE_USD", "100"))
                        result = await execute_order(
                            hit["symbol"],
                            side,  # type: ignore[arg-type]
                            amt,
                            dry_run=None,
                        )
                        flatten_results.append(
                            {
                                "symbol": hit["symbol"],
                                "flatten_side": side,
                                "mode": result.get("mode"),
                                "executed": result.get("executed"),
                            }
                        )
                    except Exception as exc:
                        flatten_results.append(
                            {"symbol": hit.get("symbol"), "error": str(exc)[:120]}
                        )
                return {
                    "executed": bool(flatten_results),
                    "mode": "stop_loss_flatten",
                    "triggered": triggered,
                    "flatten": flatten_results,
                }
    except Exception:
        logger.debug("stop-loss monitor skipped", exc_info=True)

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
        return {
            "skipped": True,
            "reason": "no_profitable_signal",
            "scanned": scan.get("profitable_count", 0),
        }

    top_exec = dict(top)
    top_exec["data_age_sec"] = scan.get("data_age_sec")
    return await try_execute_from_opportunity(top_exec)


async def start_auto_execution_loop() -> Any:
    global _auto_task
    # Safer default: loop off unless explicitly enabled.
    enabled = os.getenv("AUTO_EXECUTION_LOOP", "false").lower() in {"1", "true", "yes"}
    if not enabled:
        logger.info("Auto-execution loop disabled (AUTO_EXECUTION_LOOP!=true).")
        return None
    if _auto_task is not None and not _auto_task.done():
        return _auto_task

    interval = max(
        1,
        int(
            os.getenv(
                "AUTO_EXECUTION_INTERVAL_SEC",
                str(getattr(config, "AUTO_EXECUTION_INTERVAL_SEC", 1)),
            )
        ),
    )

    async def _loop() -> None:
        while True:
            try:
                outcome = await run_auto_execution_cycle()
                if outcome.get("executed"):
                    logger.info(
                        "Auto-execution cycle | mode=%s asset=%s",
                        outcome.get("mode"),
                        outcome.get("order", {}).get("symbol"),
                    )
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
