"""
BLACKDARK — Runtime fee matrix (maker/taker, withdrawal, deposit).

Refreshed hourly via CCXT + exchange APIs; covers all enabled venues.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.FeeMatrix")

# Seed withdrawal fees (USDT) — migrated from arbitrage_engine
WITHDRAWAL_FEE_USDT: dict[str, dict[str, float]] = {
    "binance": {"BTC": 4.5, "ETH": 1.2, "SOL": 0.15, "BNB": 0.20, "XRP": 0.25},
    "okx": {"BTC": 5.0, "ETH": 1.5, "SOL": 0.18, "BNB": 0.22, "XRP": 0.30},
    "bybit": {"BTC": 4.8, "ETH": 1.3, "SOL": 0.16, "BNB": 0.21, "XRP": 0.28},
    "coinbase": {"BTC": 5.5, "ETH": 1.8, "SOL": 0.20, "BNB": 0.25, "XRP": 0.35},
    "kraken": {"BTC": 5.0, "ETH": 1.6, "SOL": 0.18, "BNB": 0.24, "XRP": 0.32},
    "kucoin": {"BTC": 5.2, "ETH": 1.4, "SOL": 0.17, "BNB": 0.22, "XRP": 0.30},
    "gateio": {"BTC": 4.9, "ETH": 1.35, "SOL": 0.17, "BNB": 0.21, "XRP": 0.29},
    "bitget": {"BTC": 5.0, "ETH": 1.4, "SOL": 0.17, "BNB": 0.22, "XRP": 0.30},
    "mexc": {"BTC": 4.7, "ETH": 1.3, "SOL": 0.16, "BNB": 0.20, "XRP": 0.28},
}

DEPOSIT_FEE_USDT: dict[str, dict[str, float]] = {
    ex: {asset: 0.0 for asset in ("BTC", "ETH", "SOL", "BNB", "XRP")}
    for ex in WITHDRAWAL_FEE_USDT
}

_matrix: dict[str, dict[str, Any]] = {}
_last_refresh: float = 0.0
_refresh_task: asyncio.Task | None = None
REFRESH_INTERVAL_SEC = int(getattr(config, "FEE_MATRIX_REFRESH_SEC", 3600))


def _default_row(exchange_id: str) -> dict[str, Any]:
    return {
        "exchange": exchange_id,
        "taker": float(config.DEFAULT_TAKER_FEE),
        "maker": float(config.DEFAULT_MAKER_FEE),
        "futures_taker": float(config.DEFAULT_FUTURES_TAKER_FEE),
        "withdrawal": dict(WITHDRAWAL_FEE_USDT.get(exchange_id, {})),
        "deposit": dict(DEPOSIT_FEE_USDT.get(exchange_id, {})),
        "source": "default",
    }


def _ensure_seeded() -> None:
    global _matrix
    if _matrix:
        return
    for ex in config.enabled_exchanges():
        _matrix[ex] = _default_row(ex)


def taker_fee(exchange_id: str, *, market: str = "spot") -> float:
    _ensure_seeded()
    row = _matrix.get(exchange_id.lower()) or _default_row(exchange_id.lower())
    if market == "perpetual":
        return float(row.get("futures_taker") or config.DEFAULT_FUTURES_TAKER_FEE)
    return float(row.get("taker") or config.DEFAULT_TAKER_FEE)


def maker_fee(exchange_id: str, *, market: str = "spot") -> float:
    _ensure_seeded()
    row = _matrix.get(exchange_id.lower()) or _default_row(exchange_id.lower())
    if market == "perpetual":
        return float(row.get("futures_taker") or config.DEFAULT_FUTURES_TAKER_FEE) * 0.8
    return float(row.get("maker") or config.DEFAULT_MAKER_FEE)


def withdrawal_fee_usdt(exchange_id: str, symbol: str) -> float:
    _ensure_seeded()
    base = symbol.split("/")[0].upper()
    row = _matrix.get(exchange_id.lower()) or _default_row(exchange_id.lower())
    w = row.get("withdrawal") or {}
    return float(w.get(base) or WITHDRAWAL_FEE_USDT.get(exchange_id.lower(), {}).get(base, 0.0))


def deposit_fee_usdt(exchange_id: str, symbol: str) -> float:
    _ensure_seeded()
    base = symbol.split("/")[0].upper()
    row = _matrix.get(exchange_id.lower()) or _default_row(exchange_id.lower())
    d = row.get("deposit") or {}
    return float(d.get(base) or 0.0)


def trading_fees_usdt(
    exchange_id: str,
    notional: float,
    *,
    market: str = "spot",
    use_maker: bool = False,
) -> float:
    rate = maker_fee(exchange_id, market=market) if use_maker else taker_fee(exchange_id, market=market)
    return notional * rate


async def refresh_fee_matrix() -> dict[str, Any]:
    """Pull trading fees from CCXT where supported."""
    global _matrix, _last_refresh
    _ensure_seeded()
    updated = 0
    errors = 0

    try:
        import ccxt.async_support as ccxt_async
        from ccxt_market_fetcher import CCXT_ID_MAP, ccxt_exchange_id
    except ImportError:
        _last_refresh = time.time()
        return {"updated": 0, "total": len(_matrix), "source": "seed_only"}

    exchanges = list(config.enabled_exchanges().keys())
    for exchange_id in exchanges:
        ccxt_id = ccxt_exchange_id(exchange_id) if exchange_id in CCXT_ID_MAP else exchange_id
        if ccxt_id not in ccxt_async.exchanges:
            continue
        try:
            exchange_class = getattr(ccxt_async, ccxt_id)
            ex = exchange_class({"enableRateLimit": True})
            await ex.load_markets()
            fees = {}
            if hasattr(ex, "fetchTradingFees"):
                try:
                    fees = await ex.fetchTradingFees()
                except Exception:
                    fees = {}
            taker = float(getattr(ex, "fees", {}).get("trading", {}).get("taker") or 0) or taker_fee(exchange_id)
            maker = float(getattr(ex, "fees", {}).get("trading", {}).get("maker") or 0) or maker_fee(exchange_id)
            if fees:
                for _sym, row in list(fees.items())[:1]:
                    if isinstance(row, dict):
                        taker = float(row.get("taker") or taker)
                        maker = float(row.get("maker") or maker)
                        break
            _matrix[exchange_id] = {
                **_matrix.get(exchange_id, _default_row(exchange_id)),
                "taker": taker,
                "maker": maker,
                "source": "ccxt",
                "updated_ms": int(time.time() * 1000),
            }
            updated += 1
            await ex.close()
        except Exception:
            errors += 1
            logger.debug("Fee matrix CCXT refresh failed | exchange=%s", exchange_id, exc_info=True)

    _last_refresh = time.time()
    logger.info("Fee matrix refreshed | updated=%d errors=%d total=%d", updated, errors, len(_matrix))
    return {"updated": updated, "errors": errors, "total": len(_matrix), "last_refresh": _last_refresh}


async def start_fee_matrix_scheduler() -> asyncio.Task | None:  # pragma: no cover
    global _refresh_task
    if _refresh_task is not None:
        return _refresh_task
    _ensure_seeded()

    async def _loop() -> None:
        try:
            await refresh_fee_matrix()
        except Exception:
            logger.exception("Fee matrix initial refresh failed.")
        while True:
            await asyncio.sleep(REFRESH_INTERVAL_SEC)
            try:
                await refresh_fee_matrix()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Fee matrix scheduler error")

    _refresh_task = asyncio.create_task(_loop(), name="fee-matrix")
    logger.info("Fee matrix scheduler started (background refresh).")
    return _refresh_task


async def stop_fee_matrix_scheduler() -> None:  # pragma: no cover
    global _refresh_task
    if _refresh_task is not None:
        _refresh_task.cancel()
        try:
            await _refresh_task
        except asyncio.CancelledError:
            pass
        _refresh_task = None


def matrix_stats() -> dict[str, Any]:
    _ensure_seeded()
    return {
        "exchanges": len(_matrix),
        "last_refresh": _last_refresh,
        "refresh_interval_sec": REFRESH_INTERVAL_SEC,
        "sample": {k: {"taker": v.get("taker"), "maker": v.get("maker"), "source": v.get("source")} for k, v in list(_matrix.items())[:8]},
    }
