"""
BLACKDARK — Price reconciliation engine.

Periodic comparison of internal cached prices vs Binance reference spot.
Alerts when deviation exceeds configured threshold.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.Reconciliation")

DEFAULT_THRESHOLD_BPS = float(getattr(config, "RECONCILIATION_THRESHOLD_BPS", 50))
REFERENCE_EXCHANGE = "binance"


async def _fetch_binance_spot(symbol: str) -> float | None:
    pair = symbol if "/" in symbol else f"{symbol}/USDT"
    native = pair.replace("/", "")
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={native}"
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
        price = float(data.get("price") or 0)
        return price if price > 0 else None
    except Exception as exc:
        logger.warning("Binance reference fetch failed for %s: %s", symbol, exc)
        return None


async def _internal_price(symbol: str) -> float | None:
    try:
        from market_cache import get_cached_ticker

        row = await get_cached_ticker(symbol)
        if row and float(row.get("price") or 0) > 0:
            return float(row["price"])
    except Exception:
        pass
    try:
        from database import get_latest_pricing

        row = await get_latest_pricing(symbol=symbol, exchange=REFERENCE_EXCHANGE)
        if row and float(row.get("price") or 0) > 0:
            return float(row["price"])
    except Exception:
        pass
    return None


def _deviation_bps(internal: float, reference: float) -> float:
    if reference <= 0:
        return 0.0
    return abs((internal - reference) / reference) * 10_000


async def reconcile_symbol(symbol: str, *, threshold_bps: float | None = None) -> dict[str, Any]:
    threshold = threshold_bps if threshold_bps is not None else DEFAULT_THRESHOLD_BPS
    internal = await _internal_price(symbol)
    reference = await _fetch_binance_spot(symbol)
    if internal is None or reference is None:
        return {
            "symbol": symbol,
            "status": "insufficient_data",
            "internal_price": internal,
            "reference_price": reference,
            "reference_exchange": REFERENCE_EXCHANGE,
            "threshold_bps": threshold,
            "alert": False,
            "checked_at": time.time(),
        }
    bps = _deviation_bps(internal, reference)
    alert = bps > threshold
    result = {
        "symbol": symbol,
        "status": "alert" if alert else "ok",
        "internal_price": internal,
        "reference_price": reference,
        "reference_exchange": REFERENCE_EXCHANGE,
        "deviation_bps": round(bps, 2),
        "threshold_bps": threshold,
        "alert": alert,
        "checked_at": time.time(),
    }
    if alert:
        logger.warning(
            "Reconciliation ALERT | %s internal=%.6f ref=%.6f dev_bps=%.1f",
            symbol,
            internal,
            reference,
            bps,
        )
        try:
            from database import upsert_ingestion_health

            await upsert_ingestion_health(
                f"reconciliation:{symbol}",
                "reconciliation",
                ok=False,
                error=f"deviation_bps={bps:.2f}>{threshold}",
            )
        except Exception:
            pass
    return result


async def run_reconciliation_batch(symbols: list[str] | None = None) -> dict[str, Any]:
    symbols = symbols or ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    rows = [await reconcile_symbol(sym) for sym in symbols]
    alerts = [r for r in rows if r.get("alert")]
    return {
        "checked": len(rows),
        "alerts": len(alerts),
        "threshold_bps": DEFAULT_THRESHOLD_BPS,
        "reference_exchange": REFERENCE_EXCHANGE,
        "rows": rows,
    }
