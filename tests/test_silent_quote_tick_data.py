"""Silent tests — Feature #90 Quote Data + Feature #96 Tick Trade Data."""

from __future__ import annotations

import time

import pytest


# --- #90 Quote Data ---


def test_bid_ask_sanity_valid():
    from blackdark.data.quote_normalizer import validate_bid_ask_sanity

    ok, reason = validate_bid_ask_sanity(bid=100.0, ask=100.1)
    assert ok is True
    assert reason == "ok"


def test_bid_ask_sanity_inverted_rejected():
    from blackdark.data.quote_normalizer import validate_bid_ask_sanity

    ok, reason = validate_bid_ask_sanity(bid=101.0, ask=100.0)
    assert ok is False
    assert reason == "bid_not_lt_ask"


def test_quote_stale_flag():
    from blackdark.data.quote_normalizer import quote_stale_flag

    old = int(time.time() * 1000) - 60_000
    stale, age, reason = quote_stale_flag(received_ts_ms=old)
    assert stale is True
    assert "stale" in reason


def test_normalize_quote_metadata():
    from blackdark.data.quote_normalizer import normalize_quote

    q = normalize_quote(
        exchange="binance",
        symbol="BTC/USDT",
        bid=50_000,
        ask=50_010,
        bid_qty=1,
        ask_qty=2,
    )
    assert q["sane"] is True
    assert q["stale"] is False
    assert q["executable"] is True
    assert q["feature"] == "#90-silent"
    assert "ts_utc" in q


@pytest.mark.asyncio
async def test_ingest_quote_rejects_inverted():
    from market_data_pipeline import ingest_quote, pipeline_stats

    before = pipeline_stats()["quotes_rejected_sanity"]
    out = await ingest_quote("binance", "BTC/USDT", bid=100, ask=99)
    assert out["ingested"] is False
    assert out["sanity_reason"] == "bid_not_lt_ask"
    assert pipeline_stats()["quotes_rejected_sanity"] == before + 1


@pytest.mark.asyncio
async def test_ingest_quote_accepts_valid():
    from market_data_pipeline import ingest_quote

    out = await ingest_quote("binance", "ETH/USDT", bid=3000, ask=3001, bid_qty=1, ask_qty=1)
    assert out["ingested"] is True
    assert out["executable"] is True


# --- #96 Tick Trade Data ---


def test_normalize_binance_agg_trade():
    from blackdark.data.trade_normalizer import normalize_trade

    raw = {
        "s": "BTCUSDT",
        "p": "50000.5",
        "q": "0.01",
        "T": 1_700_000_000_000,
        "m": True,
        "a": 12345,
    }
    t = normalize_trade("binance", raw)
    assert t is not None
    assert t["exchange"] == "binance"
    assert t["symbol"] == "BTC/USDT"
    assert t["taker_side"] == "sell"
    assert t["trade_id"] == "12345"
    assert t["exchange_ts_ms"] == 1_700_000_000_000
    assert "ts_utc" in t
    assert t["feature"] == "#96-silent"


def test_normalize_trade_canonical_timestamp_seconds():
    from blackdark.data.trade_normalizer import normalize_trade

    t = normalize_trade("kraken", {"price": 100, "qty": 1, "timestamp": 1_700_000_000})
    assert t is not None
    assert t["exchange_ts_ms"] == 1_700_000_000_000


@pytest.mark.asyncio
async def test_ingest_trade_stream():
    from blackdark.data.trade_normalizer import get_trade_stream
    from market_data_pipeline import ingest_trade

    await ingest_trade(
        "binance",
        {"s": "ETHUSDT", "p": "2500", "q": "0.5", "T": int(time.time() * 1000), "m": False, "a": 99},
    )
    stream = get_trade_stream("ETH/USDT", limit=5)
    assert len(stream) >= 1
    assert stream[-1]["taker_side"] == "buy"


def test_get_executable_quote_after_ingest():
    from live_book_hub import get_top_of_book
    from market_data_pipeline import get_executable_quote

    from live_book_hub import update_top_of_book

    update_top_of_book("binance", "SOL/USDT", bid=100, bid_qty=1, ask=101, ask_qty=1)
    q = get_executable_quote("binance", "SOL/USDT")
    assert q is not None
    assert q["quote_meta"]["executable"] is True
    assert get_top_of_book("binance", "SOL/USDT") is not None
