"""Tests — Data Validation Layer (#147) + Confidence Engine (#149 Phase 1)."""

from __future__ import annotations

import pytest

from bd_platform.confidence_engine import (
    compute_rule_based_confidence,
    confidence_engine_status,
)
from bd_platform.data_validation_layer import (
    validate_quotes,
    validation_layer_status,
)
from bd_platform.unified_connector_layer import CanonicalPriceQuote


def _q(cid: str, price: float, vol: float = 1_000_000) -> CanonicalPriceQuote:
    return CanonicalPriceQuote(
        connector_id=cid,
        exchange=cid,
        asset="BTC",
        pair="BTCUSDT",
        price_usd=price,
        volume_24h_usd=vol,
        source=f"{cid}:test",
        fetched_at="2026-08-24T00:00:00+00:00",
    )


def test_validation_layer_status():
    status = validation_layer_status()
    assert status["ok"] is True
    assert status["feature_id"] == 147
    assert status["user_facing"] is False
    assert status["user_surface"] == "price_verified_badge_only"
    assert status["outlier_threshold_pct"] == 5.0


def test_validate_quotes_flags_outlier_and_verifies():
    quotes = [
        _q("binance", 100_000),
        _q("okx", 100_100),
        _q("glitch_api", 110_000),  # >5% outlier
    ]
    result = validate_quotes(quotes, asset="BTC")
    assert result["ok"] is True
    assert result["flagged_count"] == 1
    assert result["price_verified"] is True
    assert result["user_badge"] == "✓ Price Verified"
    assert result["user_badge_ar"] == "✓ السعر موثّق"
    assert len(result["validated_quotes"]) == 2
    assert result["sla_met"] is True


def test_validate_quotes_all_clean():
    quotes = [_q("binance", 100_000), _q("okx", 100_050)]
    result = validate_quotes(quotes, asset="BTC")
    assert result["flagged_count"] == 0
    assert result["fallback_used"] is False
    assert result["user_badge"] == "✓ Price Verified"


def test_confidence_engine_status_phase_1():
    status = confidence_engine_status()
    assert status["ok"] is True
    assert status["feature_id"] == 149
    assert status["phase"] == 1
    assert status["phase_label"] == "Experimental"
    assert status["ml_enabled"] is False
    assert status["criteria_count"] == 13
    assert status["performance_disclosure"]["sharpe_current"] is None
    assert "Phase 1" in status["performance_disclosure"]["note"]


def test_compute_rule_based_confidence_score_range():
    block = compute_rule_based_confidence(
        asset="BTC",
        price_data={
            "source_metadata": {"connectors_ok": 8, "connectors_polled": 10, "sources_used": [{}] * 6},
            "outlier_count": 0,
            "quotes_clean": 8,
            "accuracy_estimate": 0.99,
            "vwap_usd": 95000,
            "latency_ms": 400,
            "validation": {"price_verified": True},
            "price_verified": True,
        },
        market_data={"change_24h": 2.0, "quote_volume": 2_000_000_000},
    )
    assert block["feature_id"] == 149
    assert block["phase_label"] == "Experimental"
    assert 0 <= block["confidence_score"] <= 100
    assert block["criteria_count"] == 13
    assert block["no_sharpe_promise"] is True
    assert "Experimental" in block["display"]


def test_confidence_low_when_unverified():
    block = compute_rule_based_confidence(
        asset="OBSCURE",
        price_data={
            "source_metadata": {"connectors_ok": 1, "connectors_polled": 5, "sources_used": []},
            "outlier_count": 3,
            "quotes_clean": 1,
            "accuracy_estimate": 0.7,
            "latency_ms": 1500,
            "validation": {"price_verified": False},
        },
        market_data={"change_24h": 25, "quote_volume": 0},
    )
    assert block["confidence_score"] < 60
    assert block["confidence_band"] in {"low", "moderate"}


@pytest.mark.asyncio
async def test_score_asset_confidence_sla(monkeypatch):
    async def fake_agg(asset, use_cache=True):
        return {
            "ok": True,
            "source_metadata": {"connectors_ok": 5, "connectors_polled": 6, "sources_used": [{}] * 4},
            "outlier_count": 0,
            "quotes_clean": 5,
            "accuracy_estimate": 0.98,
            "vwap_usd": 90000,
            "latency_ms": 300,
            "validation": {"price_verified": True, "user_badge": "✓ Price Verified"},
        }

    async def fake_ticker(sym):
        return {"change_pct": 1.5, "quote_volume": 1_500_000_000}

    monkeypatch.setattr("bd_platform.price_aggregation_engine.aggregate_prices", fake_agg)
    monkeypatch.setattr("market_context.fetch_binance_ticker", fake_ticker)
    monkeypatch.setattr("bd_platform.confidence_engine._SCORES_PATH", __import__("pathlib").Path("/tmp/conf_test.jsonl"))

    from bd_platform.confidence_engine import score_asset_confidence

    out = await score_asset_confidence("BTC")
    assert out["ok"] is True
    assert out["phase_label"] == "Experimental"
    assert out["sla_met"] is True
    assert out["price_verified_badge"] == "✓ Price Verified"
