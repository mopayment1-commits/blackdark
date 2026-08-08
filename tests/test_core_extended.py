"""Extended tests to reach 80% on buyer-critical core modules."""

from unittest.mock import AsyncMock, patch

import pytest

import oracle_track_record as tr
from live_book_hub import get_live_books_if_fresh, update_top_of_book
from market_cache import cache_stats, get_cached_snapshots, set_cached_snapshots
from risk_manager import detect_data_poisoning, evaluate_execution_risk, unfreeze_trading
from sentiment_gate import sentiment_allows_execution, sentiment_execution_context


def test_live_book_freshness():
    update_top_of_book("binance", "BTC/USDT", bid=1, bid_qty=1, ask=2, ask_qty=1)
    update_top_of_book("okx", "BTC/USDT", bid=1, bid_qty=1, ask=2, ask_qty=1)
    result = get_live_books_if_fresh(max_age_ms=60000)
    assert result is not None


def test_market_cache_roundtrip():

    set_cached_snapshots({"binance": {}}, {}, source="test")
    cached = get_cached_snapshots(max_age_sec=60)
    assert cached is not None
    stats = cache_stats()
    assert stats["populated"] is True


def test_sentiment_gate_async():
    assert sentiment_allows_execution("BTC", compound_score=-0.9) is False
    assert sentiment_allows_execution("BTC", compound_score=0.5) is True


@pytest.mark.asyncio
async def test_sentiment_fetch_fallback():
    ctx = await sentiment_execution_context("BTC")
    assert "execution_allowed" in ctx


def test_risk_evaluate_with_opportunity():
    unfreeze_trading()
    v = evaluate_execution_risk({"asset": "BTC", "total_slippage_bps": 5, "buy_price": 50000})
    assert v.allowed is True


def test_risk_high_slippage_block():
    unfreeze_trading()
    v = evaluate_execution_risk({"asset": "BTC", "total_slippage_bps": 200})
    assert not v.allowed


def test_poison_unfreeze():
    unfreeze_trading()
    detect_data_poisoning({"BTC": 999999}, reference_prices={"BTC": 50000})
    unfreeze_trading()
    assert evaluate_execution_risk({"asset": "BTC", "total_slippage_bps": 1}).allowed


def test_track_record_public():
    stats = tr.public_track_record()
    assert "immutable_chain" in stats
    assert stats["auto_accumulation"] is True


@pytest.mark.asyncio
async def test_options_overview():
    from options_fetcher import fetch_options_overview
    with patch("options_fetcher.fetch_deribit_options_summary", new_callable=AsyncMock) as mock:
        mock.return_value = {"success": True, "count": 0, "instruments": []}
        result = await fetch_options_overview(["BTC"])
    assert "BTC" in result["assets"]


def test_infra_metrics_with_psutil():
    from infra_metrics import collect_infra_metrics
    m = collect_infra_metrics()
    assert m["cost_rating"] in {"excellent", "good", "moderate", "heavy", "unknown"}
