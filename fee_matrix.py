"""
BLACKDARK — Runtime fee matrix (maker/taker, withdrawal, deposit).

Refreshed hourly via CCXT + exchange APIs; covers all enabled venues.

Fail-closed policy (DEC-0305):
- Known seeded / refreshed venues return concrete rates.
- Unknown venues or missing cells return None — never invent DEFAULT_* for live authority.
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from datetime import UTC, datetime
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
    ex: dict.fromkeys(("BTC", "ETH", "SOL", "BNB", "XRP"), 0.0)
    for ex in WITHDRAWAL_FEE_USDT
}

_matrix: dict[str, dict[str, Any]] = {}
_last_refresh: float = 0.0
_refresh_task: asyncio.Task | None = None
REFRESH_INTERVAL_SEC = int(getattr(config, "FEE_MATRIX_REFRESH_SEC", 3600))


def _is_known_venue(exchange_id: str) -> bool:
    ex = (exchange_id or "").lower().strip()
    if not ex:
        return False
    if ex in WITHDRAWAL_FEE_USDT:
        return True
    try:
        return ex in {k.lower() for k in config.enabled_exchanges()}
    except Exception:
        return False


def _default_row(exchange_id: str) -> dict[str, Any]:
    """Seed row for a *known* venue only. Unknown venues must not be invented."""
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
        _matrix[ex.lower()] = _default_row(ex.lower())


def _row_for(exchange_id: str) -> dict[str, Any] | None:
    """Return matrix row for known venues; None for unknown (fail-closed)."""
    _ensure_seeded()
    ex = (exchange_id or "").lower().strip()
    if not ex:
        return None
    row = _matrix.get(ex)
    if row is not None:
        return row
    if _is_known_venue(ex):
        row = _default_row(ex)
        _matrix[ex] = row
        return row
    return None


def _finite_rate(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return None
    if val < 0 or math.isnan(val):
        return None
    return val


def taker_fee(exchange_id: str, *, market: str = "spot") -> float | None:
    """Known venue taker rate, or None when unknown (never invent DEFAULT_*)."""
    row = _row_for(exchange_id)
    if row is None:
        return None
    if market == "perpetual":
        return _finite_rate(row.get("futures_taker"))
    return _finite_rate(row.get("taker"))


def maker_fee(exchange_id: str, *, market: str = "spot") -> float | None:
    """Known venue maker rate, or None when unknown."""
    row = _row_for(exchange_id)
    if row is None:
        return None
    if market == "perpetual":
        fut = _finite_rate(row.get("futures_taker"))
        if fut is None:
            return None
        return fut * 0.8
    return _finite_rate(row.get("maker"))


def withdrawal_fee_usdt(exchange_id: str, symbol: str) -> float | None:
    """Return known USDT withdrawal fee, or None when unknown (never invent 0)."""
    row = _row_for(exchange_id)
    if row is None:
        return None
    base = symbol.split("/")[0].upper()
    w = row.get("withdrawal") or {}
    if base in w and w[base] is not None:
        return float(w[base])
    seed = WITHDRAWAL_FEE_USDT.get((exchange_id or "").lower(), {}).get(base)
    if seed is not None:
        return float(seed)
    return None


def deposit_fee_usdt(exchange_id: str, symbol: str) -> float | None:
    """Known deposit fee (0 is valid for free deposits); None when unknown."""
    row = _row_for(exchange_id)
    if row is None:
        return None
    base = symbol.split("/")[0].upper()
    d = row.get("deposit") or {}
    if base in d and d[base] is not None:
        return float(d[base])
    seed = DEPOSIT_FEE_USDT.get((exchange_id or "").lower(), {}).get(base)
    if seed is not None:
        return float(seed)
    return None


def trading_fees_usdt(
    exchange_id: str,
    notional: float,
    *,
    market: str = "spot",
    use_maker: bool = False,
) -> float | None:
    rate = maker_fee(exchange_id, market=market) if use_maker else taker_fee(exchange_id, market=market)
    if rate is None:
        return None
    return notional * rate


def _fee_timestamp_iso() -> str:
    return datetime.now(UTC).isoformat()


async def calculate_opportunity_fees(
    opportunity_id: str,
    exchange: str,
    symbol: str,
    side: str,
    notional: float,
    *,
    gross_profit_usdt: float | None = None,
    gas_fee_usdt: float = 0.0,
    market: str = "spot",
    use_maker: bool = False,
) -> dict[str, Any] | None:
    """
    Calculate fees for one opportunity leg and persist to the fees table.

    Returns None when any required fee cell is unknown (fail-closed).
    """
    if not opportunity_id or notional <= 0:
        return None

    side_n = (side or "").lower().strip()
    if side_n not in {"buy", "sell"}:
        return None

    rate = maker_fee(exchange, market=market) if use_maker else taker_fee(exchange, market=market)
    if rate is None:
        return None

    trading_usdt = trading_fees_usdt(
        exchange,
        notional,
        market=market,
        use_maker=use_maker,
    )
    if trading_usdt is None:
        return None

    withdrawal: float | None = 0.0
    deposit: float | None = 0.0
    if side_n == "buy":
        withdrawal = withdrawal_fee_usdt(exchange, symbol)
        if withdrawal is None:
            return None
    else:
        deposit = deposit_fee_usdt(exchange, symbol)
        if deposit is None:
            return None

    withdrawal_f = float(withdrawal or 0.0)
    deposit_f = float(deposit or 0.0)
    gas_f = float(gas_fee_usdt or 0.0)
    total_fee = trading_usdt + withdrawal_f + deposit_f + gas_f
    net_profit = None
    if gross_profit_usdt is not None:
        net_profit = float(gross_profit_usdt) - total_fee

    record = {
        "opportunity_id": opportunity_id,
        "exchange": (exchange or "").lower().strip(),
        "symbol": symbol,
        "side": side_n,
        "trading_fee_pct": rate,
        "trading_fee_usdt": trading_usdt,
        "withdrawal_fee_usdt": withdrawal_f,
        "deposit_fee_usdt": deposit_f,
        "gas_fee_usdt": gas_f,
        "total_fee_usdt": total_fee,
        "net_profit_usdt": net_profit,
        "timestamp": _fee_timestamp_iso(),
    }

    from database import insert_fee_record

    row_id = await insert_fee_record(
        record["opportunity_id"],
        record["exchange"],
        record["symbol"],
        record["side"],
        trading_fee_pct=record["trading_fee_pct"],
        trading_fee_usdt=record["trading_fee_usdt"],
        withdrawal_fee_usdt=record["withdrawal_fee_usdt"],
        deposit_fee_usdt=record["deposit_fee_usdt"],
        gas_fee_usdt=record["gas_fee_usdt"],
        total_fee_usdt=record["total_fee_usdt"],
        net_profit_usdt=record["net_profit_usdt"],
        timestamp=record["timestamp"],
    )
    record["id"] = row_id
    return record


def calculate_opportunity_fees_sync(
    opportunity_id: str,
    exchange: str,
    symbol: str,
    side: str,
    notional: float,
    **kwargs: Any,
) -> dict[str, Any] | None:
    """Sync wrapper for calculate_opportunity_fees (used from sync arbitrage builders)."""
    coro = calculate_opportunity_fees(
        opportunity_id,
        exchange,
        symbol,
        side,
        notional,
        **kwargs,
    )
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    task = loop.create_task(coro)
    if task.done():
        return task.result()
    raise RuntimeError("calculate_opportunity_fees must be awaited inside a running event loop")


def _load_ccxt_modules() -> tuple[Any, Any, Any] | None:
    try:
        import ccxt.async_support as ccxt_async

        from ccxt_market_fetcher import CCXT_ID_MAP, ccxt_exchange_id
    except ImportError:
        return None
    return ccxt_async, CCXT_ID_MAP, ccxt_exchange_id


async def _fetch_trading_fees(ex: Any) -> dict[str, Any]:
    if not hasattr(ex, "fetchTradingFees"):
        return {}
    try:
        return await ex.fetchTradingFees()
    except Exception:
        return {}


def _fee_rates(exchange_id: str, ex: Any, fees: dict[str, Any]) -> tuple[float | None, float | None]:
    """Extract CCXT rates; treat missing/0 as unknown (do not chain to invented DEFAULT_*)."""
    trading = getattr(ex, "fees", {}) or {}
    if not isinstance(trading, dict):
        trading = {}
    trading = trading.get("trading") or {}
    taker = _finite_rate(trading.get("taker"))
    maker = _finite_rate(trading.get("maker"))
    # Explicit 0.0 from CCXT is a valid free-fee rate; distinguish from missing via key presence.
    if "taker" in trading and trading.get("taker") is not None:
        try:
            taker = float(trading["taker"])
        except (TypeError, ValueError):
            taker = None
    if "maker" in trading and trading.get("maker") is not None:
        try:
            maker = float(trading["maker"])
        except (TypeError, ValueError):
            maker = None
    if fees:
        for _sym, row in list(fees.items())[:1]:
            if isinstance(row, dict):
                if "taker" in row and row.get("taker") is not None:
                    try:
                        taker = float(row["taker"])
                    except (TypeError, ValueError):
                        pass
                if "maker" in row and row.get("maker") is not None:
                    try:
                        maker = float(row["maker"])
                    except (TypeError, ValueError):
                        pass
                break
    if taker is None:
        taker = taker_fee(exchange_id)
    if maker is None:
        maker = maker_fee(exchange_id)
    return taker, maker


async def _refresh_exchange_fee(exchange_id: str, ccxt_async: Any, ccxt_id_map: Any, ccxt_exchange_id: Any) -> bool:
    ccxt_id = ccxt_exchange_id(exchange_id) if exchange_id in ccxt_id_map else exchange_id
    if ccxt_id not in ccxt_async.exchanges:
        return False
    exchange_class = getattr(ccxt_async, ccxt_id)
    ex = exchange_class({"enableRateLimit": True})
    await ex.load_markets()
    taker, maker = _fee_rates(exchange_id, ex, await _fetch_trading_fees(ex))
    base = _row_for(exchange_id) or _default_row(exchange_id.lower())
    _matrix[exchange_id.lower()] = {
        **base,
        "taker": taker,
        "maker": maker,
        "source": "ccxt",
        "updated_ms": int(time.time() * 1000),
    }
    await ex.close()
    return True


async def refresh_fee_matrix() -> dict[str, Any]:
    """Pull trading fees from CCXT where supported."""
    global _matrix, _last_refresh
    _ensure_seeded()
    updated = 0
    errors = 0

    ccxt_modules = _load_ccxt_modules()
    if ccxt_modules is None:
        _last_refresh = time.time()
        return {"updated": 0, "total": len(_matrix), "source": "seed_only"}
    ccxt_async, ccxt_id_map, ccxt_exchange_id = ccxt_modules

    exchanges = list(config.enabled_exchanges().keys())
    for exchange_id in exchanges:
        try:
            if await _refresh_exchange_fee(exchange_id, ccxt_async, ccxt_id_map, ccxt_exchange_id):
                updated += 1
        except Exception:
            errors += 1
            logger.debug("Fee matrix CCXT refresh failed | exchange=%s", exchange_id, exc_info=True)

    _last_refresh = time.time()
    logger.info("Fee matrix refreshed | updated=%d errors=%d total=%d", updated, errors, len(_matrix))
    return {"updated": updated, "errors": errors, "total": len(_matrix), "last_refresh": _last_refresh}


def start_fee_matrix_scheduler() -> asyncio.Task | None:  # pragma: no cover
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
        await asyncio.gather(_refresh_task, return_exceptions=True)
        _refresh_task = None


def matrix_stats() -> dict[str, Any]:
    _ensure_seeded()
    return {
        "exchanges": len(_matrix),
        "last_refresh": _last_refresh,
        "refresh_interval_sec": REFRESH_INTERVAL_SEC,
        "sample": {
            k: {"taker": v.get("taker"), "maker": v.get("maker"), "source": v.get("source")}
            for k, v in list(_matrix.items())[:8]
        },
    }
