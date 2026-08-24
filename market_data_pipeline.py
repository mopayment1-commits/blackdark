"""
Market data pipeline — silent integration for #90 Quote Data + #96 Tick Trade Data.

Single ingress: normalize → sanity/stale gates → live_book + redis + OHLCV + trade stream.
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("BLACKDARK.MarketDataPipeline")

_quotes_rejected_sanity = 0
_quotes_rejected_stale = 0
_quotes_accepted = 0
_trades_ingested = 0


def pipeline_stats() -> dict[str, Any]:
    from blackdark.data.trade_normalizer import trade_stream_stats

    return {
        "quotes_accepted": _quotes_accepted,
        "quotes_rejected_sanity": _quotes_rejected_sanity,
        "quotes_rejected_stale": _quotes_rejected_stale,
        "trades_ingested": _trades_ingested,
        "trade_stream": trade_stream_stats(),
    }


async def ingest_quote(
    exchange: str,
    symbol: str,
    *,
    bid: float,
    ask: float,
    bid_qty: float = 0.0,
    ask_qty: float = 0.0,
    exchange_ts_ms: int | None = None,
    market_type: str = "spot",
    allow_stale: bool = False,
) -> dict[str, Any]:
    """
    Normalize and ingest a top-of-book quote (#90).
    Rejects bid>=ask; flags stale; only updates books when sane (+ fresh unless allow_stale).
    """
    global _quotes_rejected_sanity, _quotes_rejected_stale, _quotes_accepted

    from blackdark.data.quote_normalizer import normalize_quote

    received_ts_ms = int(time.time() * 1000)
    quote = normalize_quote(
        exchange=exchange,
        symbol=symbol,
        bid=bid,
        ask=ask,
        bid_qty=bid_qty,
        ask_qty=ask_qty,
        exchange_ts_ms=exchange_ts_ms,
        received_ts_ms=received_ts_ms,
        market_type=market_type,
    )

    if not quote["sane"]:
        _quotes_rejected_sanity += 1
        return {**quote, "ingested": False, "reject_reason": quote["sanity_reason"]}

    if quote["stale"] and not allow_stale:
        _quotes_rejected_stale += 1
        return {**quote, "ingested": False, "reject_reason": quote["stale_reason"]}

    from live_book_hub import update_top_of_book

    update_top_of_book(
        quote["exchange"],
        quote["symbol"],
        bid=bid,
        bid_qty=bid_qty,
        ask=ask,
        ask_qty=ask_qty,
        market_type=market_type,
    )

    if getattr(__import__("config"), "REDIS_PRICE_CACHE_ENABLED", True):
        try:
            from redis_price_cache import set_top_of_book

            await set_top_of_book(
                quote["exchange"],
                quote["symbol"],
                bid=bid,
                ask=ask,
                bid_qty=bid_qty,
                ask_qty=ask_qty,
            )
        except Exception:
            logger.debug("redis quote write skipped", exc_info=True)

    _quotes_accepted += 1
    return {**quote, "ingested": True}


async def ingest_trade(exchange: str, raw: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize and ingest a trade tick (#96)."""
    global _trades_ingested

    from blackdark.data.trade_normalizer import append_trade_stream, normalize_trade

    trade = normalize_trade(exchange, raw)
    if not trade:
        return None

    append_trade_stream(trade)
    asset = str(trade.get("symbol") or "").replace("/USDT", "")
    try:
        from blackdark.data.ohlcv_aggregator import buffer_trade

        buffer_trade(
            asset,
            price=float(trade["price"]),
            qty=float(trade["qty"]),
            ts_ms=int(trade["ts_ms"]),
        )
    except ImportError:
        pass

    try:
        from redis_price_cache import record_ohlc_tick

        await record_ohlc_tick(
            str(trade.get("symbol") or f"{asset}/USDT"),
            mid=float(trade["price"]),
            ts_ms=int(trade["ts_ms"]),
        )
    except Exception:
        logger.debug("trade ohlc hook skipped", exc_info=True)

    _trades_ingested += 1
    return trade


def get_executable_quote(exchange: str, symbol: str) -> dict[str, Any] | None:
    """Read live book with quote metadata for signal paths."""
    from blackdark.data.quote_normalizer import enrich_book_row
    from live_book_hub import get_top_of_book

    book = get_top_of_book(exchange, symbol)
    if not book:
        return None
    enriched = enrich_book_row(book, exchange=exchange, symbol=symbol)
    meta = enriched.get("quote_meta") or {}
    if not meta.get("executable"):
        return None
    return enriched
