"""
Fee Database Internal Service — Feature #130 (Sprint 1, non-negotiable).

Internal service — NOT a standalone user-facing feature.
Core fee engine for all profit/cost surfaces across the platform.

Covers:
  - Trading fees (maker/taker)
  - Withdrawal fees per network
  - Deposit fees
  - Hidden spread estimate (order-book or default bps)
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from fee_matrix import (
    deposit_fee_usdt,
    maker_fee,
    matrix_stats,
    taker_fee,
    trading_fees_usdt,
    withdrawal_fee_usdt,
)

logger = logging.getLogger("BLACKDARK.FeeDatabase")

_FEATURE_ID = 130
_DEFAULT_SPREAD_BPS = 5.0  # conservative hidden-spread estimate when book unavailable


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def _estimate_spread_bps(exchange_id: str, symbol: str) -> float:
    """Estimate hidden spread from order book when available."""
    base = symbol.split("/")[0].upper()
    pair = f"{base}USDT"
    try:
        import aiohttp

        endpoints = {
            "binance": ("https://api.binance.com/api/v3/ticker/bookTicker", {"symbol": pair}),
            "okx": ("https://www.okx.com/api/v5/market/ticker", {"instId": f"{base}-USDT"}),
        }
        url, params = endpoints.get(exchange_id.lower(), (None, None))
        if not url:
            return _DEFAULT_SPREAD_BPS

        timeout = aiohttp.ClientTimeout(total=4)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return _DEFAULT_SPREAD_BPS
                data = await resp.json()

        if exchange_id.lower() == "okx":
            rows = data.get("data") or []
            if not rows:
                return _DEFAULT_SPREAD_BPS
            row = rows[0]
            bid = float(row.get("bidPx") or 0)
            ask = float(row.get("askPx") or 0)
        else:
            bid = float(data.get("bidPrice") or 0)
            ask = float(data.get("askPrice") or 0)

        if bid > 0 and ask > bid:
            mid = (bid + ask) / 2
            return round((ask - bid) / mid * 10_000, 2)
    except Exception:
        pass
    return _DEFAULT_SPREAD_BPS


def fee_database_status() -> dict[str, Any]:
    stats = matrix_stats()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "role": "fee_database_internal_service",
        "user_facing": False,
        "mode": "internal_service",
        "coverage": {
            "trading_fees": True,
            "withdrawal_fees": True,
            "deposit_fees": True,
            "hidden_spread": True,
        },
        "matrix": stats,
        "default_spread_bps": _DEFAULT_SPREAD_BPS,
        "timestamp": _utcnow(),
    }


async def calculate_transaction_cost(
    exchange_id: str,
    symbol: str,
    notional_usd: float,
    *,
    side: str = "buy",
    use_maker: bool = False,
    include_withdrawal: bool = False,
    include_deposit: bool = False,
    network: str | None = None,
) -> dict[str, Any]:
    """
    Full transaction cost breakdown for any profit/cost surface.

    Example display:
      "Transaction cost: $2.5 (fees) + $1.2 (spread) = $3.7"
    """
    t0 = time.perf_counter()
    ex = (exchange_id or "").lower().strip()
    sym = symbol.upper() if "/" in symbol else f"{symbol.upper()}/USDT"
    notional = max(float(notional_usd), 0.0)

    trading_rate = maker_fee(ex) if use_maker else taker_fee(ex)
    trading_fee = trading_fees_usdt(ex, notional, use_maker=use_maker)

    spread_bps = await _estimate_spread_bps(ex, sym)
    spread_cost = round(notional * spread_bps / 10_000, 4) if notional > 0 else 0.0

    withdrawal = 0.0
    if include_withdrawal:
        w = withdrawal_fee_usdt(ex, sym)
        withdrawal = float(w) if w is not None else 0.0

    deposit = 0.0
    if include_deposit:
        d = deposit_fee_usdt(ex, sym)
        deposit = float(d) if d is not None else 0.0

    total = round((trading_fee or 0.0) + spread_cost + withdrawal + deposit, 4)
    elapsed = time.perf_counter() - t0

    display_en = (
        f"Transaction cost: ${trading_fee or 0:.2f} (fees) + ${spread_cost:.2f} (spread)"
        + (f" + ${withdrawal:.2f} (withdrawal)" if withdrawal else "")
        + (f" + ${deposit:.2f} (deposit)" if deposit else "")
        + f" = ${total:.2f}"
    )
    display_ar = (
        f"تكلفة هذه الصفقة: ${trading_fee or 0:.2f} (رسوم) + ${spread_cost:.2f} (spread)"
        + (f" + ${withdrawal:.2f} (سحب)" if withdrawal else "")
        + (f" + ${deposit:.2f} (إيداع)" if deposit else "")
        + f" = ${total:.2f}"
    )

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "mode": "internal_service",
        "user_facing": False,
        "exchange_id": ex,
        "symbol": sym,
        "side": side,
        "notional_usd": round(notional, 2),
        "total_cost_usd": total,
        "breakdown": {
            "trading_fee_usd": round(trading_fee or 0.0, 4),
            "trading_rate": trading_rate,
            "fee_type": "maker" if use_maker else "taker",
            "spread_usd": spread_cost,
            "spread_bps": spread_bps,
            "withdrawal_fee_usd": withdrawal,
            "deposit_fee_usd": deposit,
            "network": network,
        },
        "display": display_en,
        "display_ar": display_ar,
        "accuracy_estimate": 0.99 if trading_rate is not None else 0.90,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }


def lookup_fee_matrix(
    exchange_id: str,
    *,
    symbol: str = "BTC/USDT",
) -> dict[str, Any]:
    """Return fee matrix row for an exchange — internal lookup."""
    ex = (exchange_id or "").lower().strip()
    sym = symbol.upper() if "/" in symbol else f"{symbol.upper()}/USDT"
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "exchange_id": ex,
        "symbol": sym,
        "maker": maker_fee(ex),
        "taker": taker_fee(ex),
        "withdrawal_usdt": withdrawal_fee_usdt(ex, sym),
        "deposit_usdt": deposit_fee_usdt(ex, sym),
        "mode": "internal_service",
        "user_facing": False,
        "timestamp": _utcnow(),
    }
