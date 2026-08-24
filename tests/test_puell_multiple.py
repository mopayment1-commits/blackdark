"""Tests — #89 Puell Multiple miner profitability."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from bd_platform.puell_multiple import (
    _block_reward_btc,
    _compute_puell_series,
    _capitulation_confirmed,
    _hash_ribbon_buy,
    _cycle_comparison,
    classify_zone,
    compute_puell_multiple,
    puell_for_decision_engine,
    puell_multiple_status,
)


def test_block_reward_halving_schedule():
    assert _block_reward_btc(datetime(2015, 1, 1, tzinfo=UTC)) == 25.0
    assert _block_reward_btc(datetime(2021, 1, 1, tzinfo=UTC)) == 6.25
    assert _block_reward_btc(datetime(2025, 1, 1, tzinfo=UTC)) == 3.125


def test_zone_classification():
    assert classify_zone(0.3)["zone"] == "deep_capitulation"
    assert classify_zone(0.5)["ai_signal"] == "buy"
    assert classify_zone(1.2)["zone"] == "healthy"
    assert classify_zone(2.5)["zone"] == "euphoria"
    assert classify_zone(5.0)["zone"] == "deep_euphoria"


def test_puell_series_formula():
    rows = [{"date": f"2024-01-{i:02d}", "revenue_usd": 100.0 + i} for i in range(1, 31)]
    series = _compute_puell_series(rows)
    assert not series  # need 365 days for MA
    rows365 = [{"date": f"2023-{1 + (i // 28):02d}-{1 + (i % 28):02d}", "revenue_usd": 100.0} for i in range(400)]
    series = _compute_puell_series(rows365)
    assert series
    assert abs(series[-1]["puell"] - 1.0) < 0.01


def test_capitulation_confirmed():
    assert _capitulation_confirmed(0.42, -6.0) is True
    assert _capitulation_confirmed(0.42, -2.0) is False


def test_hash_ribbon_buy_signal():
    series = [{"puell": v} for v in [0.4, 0.35, 0.32, 0.33, 0.36, 0.38, 0.42, 0.45, 0.48, 0.5, 0.52, 0.55, 0.58, 0.6]]
    assert _hash_ribbon_buy(series, 2.0) is True


def test_cycle_comparison_halving():
    comp = _cycle_comparison(0.5, 120)
    assert comp["cycle_phase"] == "early_post_halving"
    assert comp["halving_cycles_supported"] >= 3


@pytest.mark.asyncio
async def test_compute_puell_mocked():
    revenue = [{"date": f"2020-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}", "revenue_usd": 1_000_000 + i * 1000} for i in range(500)]
    puell_hist = [{"date": r["date"], "puell": 0.5 + (i % 10) * 0.05} for i, r in enumerate(revenue)]
    with patch(
        "bd_platform.puell_multiple.build_daily_revenue_series",
        new=AsyncMock(return_value=revenue),
    ), patch(
        "bd_platform.puell_multiple._glassnode_puell_series",
        new=AsyncMock(return_value=None),
    ), patch(
        "bd_platform.puell_multiple._fetch_hashrate_series",
        new=AsyncMock(return_value=[{"avgHashrate": 1e20}, {"avgHashrate": 9e19}]),
    ), patch(
        "bd_platform.puell_multiple._miner_outflow_stress",
        new=AsyncMock(return_value={"available": False}),
    ), patch(
        "bd_platform.puell_multiple._compute_puell_series",
        return_value=puell_hist,
    ):
        out = await compute_puell_multiple()
    assert out["ok"] is True
    assert out["feature"] == "#89"
    assert out["decision_weight"] == 0.12
    assert "zone" in out


@pytest.mark.asyncio
async def test_puell_decision_engine_payload():
    with patch(
        "bd_platform.puell_multiple.compute_puell_multiple",
        new=AsyncMock(
            return_value={
                "ok": True,
                "puell_multiple": 0.42,
                "zone": {"zone": "capitulation"},
                "ai_signal": "buy",
                "ai_confidence": 0.8,
                "capitulation_confirmed": True,
                "hash_ribbon_buy": False,
                "headline": "Puell Capitulation",
                "latency_ms": 100,
            }
        ),
    ):
        out = await puell_for_decision_engine("BTC")
    assert out["ok"] is True
    assert out["decision_weight"] == 0.12
    assert out["risk_score_delta"] < 0


def test_puell_status():
    status = puell_multiple_status()
    assert status["feature"] == "#89"
    assert status["decision_weight"] == 0.12
