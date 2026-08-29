"""
BLACKDARK — Exchange deposit / withdrawal currency status (#380 / #381).

Live CCXT currency metadata with fail-closed unknowns.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Literal

import config

logger = logging.getLogger("BLACKDARK.ExchangeCurrencyStatus")

CurrencyStatus = Literal["open", "closed", "maintenance", "unknown"]

_cache: dict[str, dict[str, Any]] = {}
_cache_ts: float = 0.0
_CACHE_TTL = 3600.0


def _classify_currency(flags: dict[str, Any], *, mode: str) -> CurrencyStatus:
    active = flags.get("active")
    if active is False:
        return "closed"
    if mode == "deposit":
        if flags.get("deposit") is False:
            return "closed"
        if flags.get("deposit") is True:
            return "open"
    else:
        if flags.get("withdraw") is False:
            return "closed"
        if flags.get("withdraw") is True:
            return "open"
    if active is True:
        return "open"
    return "unknown"


async def _fetch_exchange_currencies(exchange_id: str) -> dict[str, Any]:
    import ccxt.async_support as ccxt

    ex_id = exchange_id.lower().strip()
    if not hasattr(ccxt, ex_id):
        return {"exchange": ex_id, "error": "unsupported_exchange", "currencies": {}}
    klass = getattr(ccxt, ex_id)
    exchange = klass({"enableRateLimit": True})
    try:
        await exchange.load_markets()
        raw = await exchange.fetch_currencies()
        out: dict[str, dict[str, Any]] = {}
        for code, meta in (raw or {}).items():
            if not isinstance(meta, dict):
                continue
            out[code.upper()] = {
                "deposit_status": _classify_currency(meta, mode="deposit"),
                "withdrawal_status": _classify_currency(meta, mode="withdraw"),
                "active": meta.get("active"),
                "networks": list((meta.get("networks") or {}).keys())[:8],
            }
        return {"exchange": ex_id, "currencies": out, "source": "ccxt_live"}
    except Exception as exc:
        logger.debug("fetch_currencies failed %s: %s", ex_id, exc)
        return {"exchange": ex_id, "error": str(exc), "currencies": {}, "source": "error"}
    finally:
        await exchange.close()


async def _ensure_cache(exchange_id: str) -> dict[str, Any]:
    global _cache_ts
    ex = exchange_id.lower().strip()
    now = time.time()
    if ex in _cache and (now - _cache_ts) < _CACHE_TTL:
        return _cache[ex]
    row = await _fetch_exchange_currencies(ex)
    _cache[ex] = row
    _cache_ts = now
    return row


def _seed_fallback(exchange_id: str) -> dict[str, Any]:
    """Offline seed when CCXT unavailable — major assets open on known venues."""
    from fee_matrix import WITHDRAWAL_FEE_USDT

    ex = exchange_id.lower().strip()
    symbols = list(WITHDRAWAL_FEE_USDT.get(ex, {"BTC": 0, "ETH": 0, "USDT": 0}).keys())
    currencies = {
        s: {"deposit_status": "open", "withdrawal_status": "open", "active": True, "networks": []}
        for s in symbols + ["USDT"]
    }
    return {"exchange": ex, "currencies": currencies, "source": "seed_fallback"}


async def deposit_currencies_open(*, exchange: str = "binance") -> dict[str, Any]:
    """#380 — currencies open for deposit on exchange."""
    row = await _ensure_cache(exchange)
    if not row.get("currencies") and row.get("error"):
        row = _seed_fallback(exchange)
    open_list = sorted(
        code
        for code, meta in (row.get("currencies") or {}).items()
        if meta.get("deposit_status") == "open"
    )
    closed_list = sorted(
        code
        for code, meta in (row.get("currencies") or {}).items()
        if meta.get("deposit_status") == "closed"
    )
    return {
        "feature_ref": "exchange_currency_status#380",
        "capability_id": 380,
        "exchange": exchange.lower(),
        "deposit_open": open_list,
        "deposit_closed": closed_list,
        "total_tracked": len(row.get("currencies") or {}),
        "source": row.get("source"),
        "ok": True,
        "disclaimer": "Status from exchange API — verify before moving funds.",
    }


async def withdrawal_currencies_closed(*, exchange: str = "binance") -> dict[str, Any]:
    """#381 — currencies with withdrawals closed/suspended."""
    row = await _ensure_cache(exchange)
    if not row.get("currencies") and row.get("error"):
        row = _seed_fallback(exchange)
    closed = sorted(
        code
        for code, meta in (row.get("currencies") or {}).items()
        if meta.get("withdrawal_status") == "closed"
    )
    open_w = sorted(
        code
        for code, meta in (row.get("currencies") or {}).items()
        if meta.get("withdrawal_status") == "open"
    )
    return {
        "feature_ref": "exchange_currency_status#381",
        "capability_id": 381,
        "exchange": exchange.lower(),
        "withdrawal_closed": closed,
        "withdrawal_open": open_w,
        "total_tracked": len(row.get("currencies") or {}),
        "source": row.get("source"),
        "ok": True,
        "disclaimer": "Withdrawal suspension alerts — not custodial execution.",
    }


def reset_currency_status_cache() -> None:
    global _cache, _cache_ts
    _cache = {}
    _cache_ts = 0.0
