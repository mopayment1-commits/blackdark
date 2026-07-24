"""
BLACKDARK — Trade Simulator (Wave 4A).

Paper-trade oracle signals and arbitrage paths with fee-aware P&L scenarios.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Literal

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.TradeSimulator")

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
                return {
                    "price": float(data["lastPrice"]),
                    "change_24h": float(data["priceChangePercent"]),
                }
    except (aiohttp.ClientError, KeyError, TypeError, ValueError):
        return None


def _fee_usd(notional: float) -> float:
    return notional * config.DEFAULT_TAKER_FEE


async def simulate_spot_trade(
    symbol: str,
    side: Side,
    amount_usd: float,
    *,
    hold_hours: int = 24,
) -> dict[str, Any]:
    """
    Simulate a spot trade using live price + oracle levels.

    Returns entry, fees, and bull/base/bear exit scenarios.
    """
    if amount_usd <= 0:
        raise ValueError("amount_usd must be positive")

    asset, pair = _normalize_symbol(symbol)
    market = await _fetch_ticker(pair)
    if market is None:
        raise ValueError(f"Symbol {asset} not found")

    price = float(market["price"])
    change = float(market["change_24h"])
    hourly_drift = change / 24.0 if hold_hours else change

    entry_fee = _fee_usd(amount_usd)
    net_notional = amount_usd - entry_fee if side == "buy" else amount_usd
    quantity = net_notional / price if side == "buy" else amount_usd / price

    support = round(price * 0.97, 6)
    resistance = round(price * 1.03, 6)
    flat_exit = price * (1 + (hourly_drift * hold_hours) / 100.0)

    def _exit_pnl(exit_price: float) -> dict[str, float]:
        if side == "buy":
            gross = quantity * exit_price
            exit_fee = _fee_usd(gross)
            pnl = gross - exit_fee - amount_usd
        else:
            gross = quantity * price
            buy_back = quantity * exit_price
            exit_fee = _fee_usd(buy_back)
            pnl = gross - entry_fee - buy_back - exit_fee
        return {
            "exit_price": round(exit_price, 6),
            "pnl_usd": round(pnl, 4),
            "pnl_percent": round((pnl / amount_usd) * 100, 4),
        }

    scenarios = {
        "bullish": _exit_pnl(resistance),
        "base_case": _exit_pnl(flat_exit),
        "bearish": _exit_pnl(support),
    }

    payload = {
        "mode": "spot_simulation",
        "symbol": asset,
        "side": side,
        "amount_usd": round(amount_usd, 2),
        "entry_price": price,
        "quantity": round(quantity, 8),
        "entry_fee_usd": round(entry_fee, 4),
        "hold_hours": hold_hours,
        "support": support,
        "resistance": resistance,
        "scenarios": scenarios,
        "verdict_hint": scenarios["base_case"]["pnl_usd"],
        "disclaimer": "Paper simulation — not financial advice. Slippage not included.",
        "timestamp": _utcnow_iso(),
    }

    from database import insert_simulation_log

    await insert_simulation_log("spot", asset, json.dumps(payload), scenarios["base_case"]["pnl_usd"])
    return payload


async def simulate_arbitrage_trade(
    kind: str,
    quote_amount: float,
    *,
    symbol: str | None = None,
    buy_exchange: str | None = None,
    sell_exchange: str | None = None,
    exchange: str | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    """Simulate executing a specific arbitrage opportunity."""
    from arbitrage_service import scan_arbitrage_opportunities

    scan = await scan_arbitrage_opportunities(quote_amount=quote_amount, prefer_live=True)
    opportunities = scan.get("opportunities") or []

    match: dict[str, Any] | None = None
    for opp in opportunities:
        if opp.get("kind") != kind:
            continue
        if symbol and opp.get("symbol") != symbol and opp.get("asset") != symbol.replace("/USDT", ""):
            continue
        if buy_exchange and opp.get("buy_exchange") != buy_exchange:
            continue
        if sell_exchange and opp.get("sell_exchange") != sell_exchange:
            continue
        if exchange and opp.get("exchange") != exchange:
            continue
        if path and opp.get("path") != path:
            continue
        match = opp
        break

    if match is None and opportunities:
        match = next((o for o in opportunities if o.get("kind") == kind), opportunities[0])

    if match is None:
        return {
            "mode": "arbitrage_simulation",
            "kind": kind,
            "quote_amount": quote_amount,
            "executed": False,
            "message": "No matching arbitrage opportunity found for simulation.",
            "timestamp": _utcnow_iso(),
        }

    net = float(match.get("net_profit_usdt") or 0)
    payload = {
        "mode": "arbitrage_simulation",
        "executed": True,
        "kind": kind,
        "quote_amount": quote_amount,
        "opportunity": match,
        "projected_profit_usd": round(net, 4),
        "projected_profit_percent": round(float(match.get("net_profit_percent") or 0), 4),
        "execution_feasibility": match.get("execution_feasibility"),
        "estimated_duration": match.get("estimated_duration"),
        "fees_usd": round(float(match.get("fees_usdt") or 0), 4),
        "disclaimer": "Paper simulation — assumes full fill at depth-walk prices.",
        "timestamp": _utcnow_iso(),
    }

    from database import insert_simulation_log

    asset = str(match.get("asset") or match.get("symbol") or "MULTI")
    await insert_simulation_log(kind, asset, json.dumps(payload), net)
    return payload
