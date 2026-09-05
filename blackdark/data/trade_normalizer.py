"""
Trade / tick normalization — Feature #96 (silent data layer).

Exchange-native timestamps → canonical UTC; taker side preserved.
Foundation for order flow (#85) and OHLCV aggregation.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

# Bounded in-memory trade stream (per symbol) for replay / order flow
_TRADE_STREAM: dict[str, list[dict[str, Any]]] = {}
_STREAM_MAX = 2000


def _canonical_ts(ts_ms: int) -> dict[str, Any]:
    return {
        "ts_ms": int(ts_ms),
        "ts_utc": datetime.fromtimestamp(int(ts_ms) / 1000, tz=UTC).isoformat(),
    }


def _parse_exchange_ts(raw: Any) -> int | None:
    if raw is None:
        return None
    try:
        v = int(raw)
        if v < 10_000_000_000:
            return v * 1000
        return v
    except (TypeError, ValueError):
        return None


def _infer_taker_side(*, is_buyer_maker: bool | None, side: str | None) -> str:
    if is_buyer_maker is not None:
        return "sell" if is_buyer_maker else "buy"
    s = (side or "").lower()
    if s in {"buy", "sell"}:
        return s
    return "unknown"


def normalize_trade(exchange: str, raw: dict[str, Any]) -> dict[str, Any] | None:
    """
    Normalize a trade tick from exchange-native payload.

    Supports Binance aggTrade/bookTicker trade fields and generic {price, qty, side}.
    """
    ex = exchange.strip().lower()
    price = float(raw.get("p") or raw.get("price") or 0)
    qty = float(raw.get("q") or raw.get("qty") or raw.get("quantity") or 0)
    if price <= 0 or qty <= 0:
        return None

    sym = str(raw.get("s") or raw.get("symbol") or "").upper()
    if sym and not sym.endswith("/USDT") and sym.endswith("USDT"):
        sym = f"{sym[:-4]}/USDT"

    exchange_ts = _parse_exchange_ts(raw.get("T") or raw.get("t") or raw.get("timestamp") or raw.get("ts_ms"))
    received_ts = int(time.time() * 1000)
    canonical_ts = exchange_ts or received_ts

    is_buyer_maker = raw.get("m")
    if is_buyer_maker is not None and not isinstance(is_buyer_maker, bool):
        is_buyer_maker = str(is_buyer_maker).lower() in {"true", "1", "yes"}

    taker_side = _infer_taker_side(
        is_buyer_maker=is_buyer_maker if isinstance(is_buyer_maker, bool) else None,
        side=raw.get("side"),
    )

    trade_id = str(raw.get("a") or raw.get("id") or raw.get("trade_id") or f"{ex}:{canonical_ts}:{price}")

    row = {
        "feature": "#96-silent",
        "exchange": ex,
        "symbol": sym,
        "trade_id": trade_id,
        "price": price,
        "qty": qty,
        "taker_side": taker_side,
        "is_buyer_maker": is_buyer_maker,
        "exchange_ts_ms": exchange_ts,
        "received_ts_ms": received_ts,
        **_canonical_ts(canonical_ts),
    }
    return row


def append_trade_stream(trade: dict[str, Any]) -> None:
    sym = str(trade.get("symbol") or "UNKNOWN")
    buf = _TRADE_STREAM.setdefault(sym, [])
    buf.append(trade)
    if len(buf) > _STREAM_MAX:
        _TRADE_STREAM[sym] = buf[-_STREAM_MAX:]


def get_trade_stream(symbol: str, *, limit: int = 100) -> list[dict[str, Any]]:
    sym = symbol.strip().upper()
    if not sym.endswith("/USDT") and sym.endswith("USDT"):
        sym = f"{sym[:-4]}/USDT"
    rows = _TRADE_STREAM.get(sym, [])
    return rows[-max(1, min(limit, 500)) :]


def trade_stream_stats() -> dict[str, Any]:
    return {
        "symbols": len(_TRADE_STREAM),
        "total_trades": sum(len(v) for v in _TRADE_STREAM.values()),
    }
