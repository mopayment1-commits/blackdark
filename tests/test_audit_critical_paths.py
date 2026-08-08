"""Regression tests for critical architecture audit fixes."""

from __future__ import annotations

import asyncio

from live_book_hub import get_quote_age_ms, is_quote_fresh, update_top_of_book
from ml.labeling_pipeline import score_verdict_accuracy
from weight_aggregator import (
    apply_modal_adjustments_with_regime,
    detect_market_regime,
    get_regime_dimension_weights,
)


def test_oracle_unified_imports():
    import oracle_unified

    assert hasattr(oracle_unified, "compute_unified_oracle")


def test_public_weights_summary_exists():
    from model_weights_guard import public_weights_summary

    summary = public_weights_summary("risk_off")
    assert summary["market_regime"] == "risk_off"
    assert "dimension_weights" in summary
    assert abs(sum(summary["dimension_weights"].values()) - 1.0) < 1e-6


def test_verdict_labeling_public_taxonomy():
    outcome, _score, direction = score_verdict_accuracy("BULLISH_ANALYTICS", 100.0, 103.0)
    assert direction == "up"
    assert outcome == "correct"

    outcome2, _, _ = score_verdict_accuracy("NEUTRAL_OBSERVE", 100.0, 100.5)
    assert outcome2 == "correct"

    outcome3, _, direction3 = score_verdict_accuracy("ELEVATED_RISK", 100.0, 97.0)
    assert direction3 == "down"
    assert outcome3 == "correct"


def test_live_book_quote_age_helpers():
    update_top_of_book("binance", "BTC/USDT", bid=100.0, bid_qty=1.0, ask=100.1, ask_qty=1.0)
    age = get_quote_age_ms("binance", "BTC/USDT")
    assert age is not None
    assert age >= 0
    assert is_quote_fresh("binance", "BTC/USDT", max_age_ms=5000)


def test_regime_and_conflicts_in_breakdown():
    regime = detect_market_regime({"macro_regime": "Risk-Off"}, change_24h=-4.0)
    assert regime in {"risk_off", "panic"}
    weights = get_regime_dimension_weights(regime)
    assert set(weights) >= {"technical", "onchain", "sentiment", "macro", "whale"}

    adjusted, breakdown = apply_modal_adjustments_with_regime(
        60.0,
        "BTC",
        {
            "obi_by_asset": {"BTC": {"average_obi": 0.8}},
            "sentiment_compound_index": {"BTC": -0.9},
            "macro_regime": "Risk-Off",
            "macro_score_weight": 0.92,
        },
        change_24h=-5.0,
    )
    assert 0.0 <= adjusted <= 100.0
    assert "conflicts" in breakdown
    assert "market_regime" in breakdown


def test_pg_result_supports_fetch():
    from postgres_backend import _PgResult

    async def _run():
        result = _PgResult([{"id": 1, "asset": "BTC"}], rowcount=1)
        rows = await result.fetchall()
        one = await result.fetchone()
        assert rows[0]["asset"] == "BTC"
        assert one["id"] == 1

    asyncio.run(_run())
