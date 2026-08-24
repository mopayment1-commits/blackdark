"""Tests — Execution Quality Score (#153)."""

from __future__ import annotations

import pytest

from bd_platform.execution_quality_score import (
    _format_headline,
    _slippage_to_score,
    compute_execution_quality_score,
    enrich_net_profit_with_slippage,
    execution_quality_status,
)


def test_slippage_to_score_mapping():
    assert _slippage_to_score(0) == 100.0
    assert _slippage_to_score(50) == 80.0
    assert _slippage_to_score(500) == 0.0


def test_format_headline_with_alternative():
    primary = {"venue_label": "Uniswap", "slippage_pct": 2.3}
    alt = {"venue_label": "Binance", "slippage_pct": 0.1}
    en, ar = _format_headline(asset="ETH", amount_usd=5000, side="buy", primary=primary, alternative=alt)
    assert "Uniswap" in en
    assert "Binance" in en
    assert "2.3%" in en
    assert "0.1%" in en
    assert "Uniswap" in ar


def test_enrich_net_profit_with_slippage():
    row = {"net_profit_usd": 100.0, "notional_usd": 10_000}
    out = enrich_net_profit_with_slippage(row, slippage_bps=50, venue_label="Binance")
    assert out["execution_quality_153"]["slippage_cost_usd"] == 50.0
    assert out["execution_quality_153"]["net_profit_after_slippage_usd"] == 50.0


def test_execution_quality_status():
    status = execution_quality_status()
    assert status["ok"] is True
    assert status["feature_id"] == 153
    assert "#113" in status["integrated_features"]


@pytest.mark.asyncio
async def test_compute_execution_quality_score_mocked(monkeypatch, tmp_path):
    async def fake_ctx(asset):
        return {
            "canonical_symbol": "ETH",
            "volatility_24h_pct": 2.0,
            "liquidity_usd": 50_000_000,
            "price_usd": 3000,
            "source": "test",
        }

    async def fake_book(symbol):
        return {
            "asks": [[3000, 100], [3001, 50]],
            "bids": [[2999, 100], [2998, 50]],
        }

    async def fake_okx(symbol):
        return {
            "asks": [[3000, 80], [3001, 40]],
            "bids": [[2999, 80], [2998, 40]],
        }

    monkeypatch.setattr("bd_platform.execution_quality_score._market_context", fake_ctx)
    monkeypatch.setattr("bd_platform.execution_quality_score._fetch_cex_order_book", fake_book)
    monkeypatch.setattr("bd_platform.execution_quality_score._fetch_okx_order_book", fake_okx)
    monkeypatch.setattr(
        "bd_platform.execution_quality_score._SNAPSHOT_PATH",
        tmp_path / "execution_quality_snapshots.jsonl",
    )

    out = await compute_execution_quality_score("ETH", amount_usd=5000, side="buy")
    assert out["ok"] is True
    assert out["feature_id"] == 153
    assert out["best_venue"]["venue_id"]
    assert len(out["venue_rankings"]) == 3
    assert "Alternative:" in out["headline"]
    assert out["sla_met"] is True
