"""
Unified OHLCV read spine — Feature #79 (silent).

Read chain: Redis OHLC → trade replay fill → Binance REST failover.
Charts and CAP646 consume this — no standalone OHLCV product surface.
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("BLACKDARK.OHLCVSpine")


async def fetch_ohlcv_candles(
    symbol: str,
    *,
    interval: str = "1h",
    limit: int = 100,
) -> dict[str, Any]:
    sym = symbol.strip().upper()
    if not sym.endswith("USDT"):
        sym = f"{sym}USDT"

    candles: list[dict[str, Any]] = []
    source = "none"
    gaps_filled = 0

    try:
        from redis_price_cache import get_ohlc_candles

        candles = await get_ohlc_candles(sym, interval=interval, limit=limit)
        if candles:
            source = "redis_ohlc"
    except Exception:
        logger.debug("redis ohlcv read failed", exc_info=True)

    if candles:
        from blackdark.data.ohlcv_aggregator import detect_gaps, get_trade_buffer, replay_fill_gaps

        gaps = detect_gaps(candles, interval=interval)
        if gaps:
            asset = sym.replace("USDT", "")
            merged, gaps_filled = replay_fill_gaps(candles, get_trade_buffer(asset), interval=interval)
            if gaps_filled:
                candles = merged
                source = f"{source}+replay"

    if not candles:
        from market_context import fetch_binance_klines, fetch_binance_ticker, normalize_oracle_symbol

        closes = await fetch_binance_klines(sym, interval=interval, limit=limit)
        src = "binance_klines"
        if not closes:
            asset, pair = normalize_oracle_symbol(sym.replace("USDT", ""))
            ticker = await fetch_binance_ticker(pair)
            price = float((ticker or {}).get("price") or 0)
            if price > 0:
                closes = [price] * min(limit, 20)
                src = "ticker_shadow_bar"
        if closes:
            now = int(time.time() * 1000)
            from blackdark.data.ohlcv_aggregator import bucket_ms

            step = bucket_ms(interval)
            candles = [
                {"t": now - (len(closes) - i) * step, "o": c, "h": c, "l": c, "c": c, "v": 0.0, "n": 0}
                for i, c in enumerate(closes)
            ]
            source = src

    return {
        "symbol": sym,
        "interval": interval,
        "candles": candles[-limit:],
        "count": len(candles[-limit:]),
        "source": source,
        "gaps_filled": gaps_filled,
    }


async def fetch_ohlcv_closes(
    symbol: str,
    *,
    interval: str = "1h",
    limit: int = 100,
) -> tuple[list[float], str]:
    """Unified close-price chain for RSI/MACD and CAP646."""
    sym = symbol.strip().upper()
    if not sym.endswith("USDT"):
        sym = f"{sym}USDT"

    pack = await fetch_ohlcv_candles(sym, interval=interval, limit=limit)
    if pack.get("candles"):
        closes = [float(c["c"]) for c in pack["candles"]]
        return closes, str(pack.get("source") or "ohlcv_spine")

    from market_context import fetch_binance_klines, fetch_binance_ticker, normalize_oracle_symbol

    closes = await fetch_binance_klines(sym, interval=interval, limit=limit)
    if closes:
        return closes, "binance_klines"

    from market_context import fetch_binance_ticker, normalize_oracle_symbol

    asset, pair = normalize_oracle_symbol(sym.replace("USDT", ""))
    ticker = await fetch_binance_ticker(pair)
    price = float((ticker or {}).get("price") or 0)
    if price > 0:
        return [price] * min(limit, 20), "ticker_shadow_bar"
    return [], "none"
