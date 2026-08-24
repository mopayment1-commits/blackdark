"""
OHLCV aggregation spine — Feature #79 (silent data layer).

Trades/ticks → interval candles with gap detection and replay fill.
No user-facing surface — consumed by charts and CAP646 enrichment.
"""

from __future__ import annotations

from typing import Any

INTERVAL_MS: dict[str, int] = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "6h": 21_600_000,
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
    "3d": 259_200_000,
    "1w": 604_800_000,
}


def bucket_ms(interval: str) -> int:
    return INTERVAL_MS.get(interval, INTERVAL_MS["1h"])


def aggregate_trades_to_candles(
    trades: list[dict[str, Any]],
    *,
    interval: str = "1h",
) -> list[dict[str, Any]]:
    """Aggregate trade ticks into OHLCV candles."""
    step = bucket_ms(interval)
    buckets: dict[int, dict[str, Any]] = {}
    for trade in sorted(trades, key=lambda t: int(t.get("ts_ms") or 0)):
        price = float(trade.get("price") or 0)
        qty = float(trade.get("qty") or trade.get("volume") or 0)
        ts = int(trade.get("ts_ms") or 0)
        if price <= 0 or ts <= 0:
            continue
        b = (ts // step) * step
        row = buckets.get(b)
        if row is None:
            buckets[b] = {
                "t": b,
                "o": price,
                "h": price,
                "l": price,
                "c": price,
                "v": qty,
                "n": 1,
            }
        else:
            row["h"] = max(row["h"], price)
            row["l"] = min(row["l"], price)
            row["c"] = price
            row["v"] += qty
            row["n"] += 1
    return [buckets[k] for k in sorted(buckets)]


def detect_gaps(
    candles: list[dict[str, Any]],
    *,
    interval: str,
) -> list[dict[str, Any]]:
    """Return missing bucket ranges between consecutive candles."""
    if len(candles) < 2:
        return []
    step = bucket_ms(interval)
    gaps: list[dict[str, Any]] = []
    ordered = sorted(candles, key=lambda c: int(c.get("t") or 0))
    for prev, cur in zip(ordered, ordered[1:]):
        p_t = int(prev.get("t") or 0)
        c_t = int(cur.get("t") or 0)
        expected = p_t + step
        if c_t > expected:
            gaps.append(
                {
                    "start_ms": expected,
                    "end_ms": c_t - step,
                    "missing_buckets": (c_t - expected) // step,
                }
            )
    return gaps


def replay_fill_gaps(
    candles: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    *,
    interval: str,
) -> tuple[list[dict[str, Any]], int]:
    """
    Replay trades into gap buckets; returns merged candles + gaps filled count.
    """
    gaps = detect_gaps(candles, interval=interval)
    if not gaps or not trades:
        return candles, 0
    filled = aggregate_trades_to_candles(trades, interval=interval)
    by_t = {int(c["t"]): c for c in candles}
    filled_count = 0
    gap_ranges = {(g["start_ms"], g["end_ms"]) for g in gaps}
    for candle in filled:
        t = int(candle["t"])
        for start, end in gap_ranges:
            if start <= t <= end:
                if t not in by_t:
                    by_t[t] = candle
                    filled_count += 1
                break
    merged = [by_t[k] for k in sorted(by_t)]
    return merged, filled_count


# In-process trade buffer for replay (per symbol+interval, bounded)
_trade_buffer: dict[str, list[dict[str, Any]]] = {}
_BUFFER_MAX = 5000


def buffer_trade(symbol: str, *, price: float, qty: float = 0.0, ts_ms: int) -> None:
    key = symbol.strip().upper()
    buf = _trade_buffer.setdefault(key, [])
    buf.append({"price": price, "qty": qty, "ts_ms": ts_ms})
    if len(buf) > _BUFFER_MAX:
        _trade_buffer[key] = buf[-_BUFFER_MAX:]


def get_trade_buffer(symbol: str) -> list[dict[str, Any]]:
    return list(_trade_buffer.get(symbol.strip().upper(), []))
