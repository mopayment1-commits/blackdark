"""Tests — #56 Execution Optimizer + #57 Flash-Crash Protection."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from bd_platform.execution_optimizer import (
    DEX_VENUES,
    CEX_VENUES,
    capacity_score,
    compute_true_cost,
    mev_risk_score,
    optimize_execution,
    predict_slippage_bps,
)
from bd_platform.flash_crash_protection import (
    _circuit_level,
    _classify_event,
    _cross_exchange_divergence,
    circuit_breaker_status,
    evaluate_flash_protection,
)


def test_capacity_score_deep_liquidity():
    out = capacity_score(amount_usd=10_000, liquidity_usd=50_000_000)
    assert out["score"] >= 90
    assert out["label"] == "deep"


def test_true_cost_formula():
    tc = compute_true_cost(
        price_impact_bps=10,
        slippage_bps=15,
        fee_bps=10,
        gas_bps=5,
        bridge_bps=0,
        mev_risk_bps=3,
    )
    assert tc["true_cost_bps"] == 43


def test_mev_protected_low_risk():
    mev = mev_risk_score(amount_usd=50_000, venue="cowswap", mev_protected=True, chain="ethereum")
    assert mev["score"] <= 10


def test_slippage_prediction_interval():
    slip = predict_slippage_bps(
        amount_usd=50_000,
        liquidity_usd=5_000_000,
        volatility_pct=3.0,
        venue_fee_bps=30,
        is_cex=False,
    )
    assert slip["confidence_low_bps"] <= slip["predicted_bps"] <= slip["confidence_high_bps"]


def test_circuit_levels():
    assert _circuit_level(1.0) == "green"
    assert _circuit_level(2.5) == "yellow"
    assert _circuit_level(3.5) == "orange"
    assert _circuit_level(6.0) == "red"


def test_classify_flash_crash():
    ev = _classify_event(velocity_pct=-4.2, divergence_pct=0.5, direction="down")
    assert ev["event_type"] == "flash_crash"
    assert ev["action"] == "halt_buy_signals"


def test_cross_exchange_divergence():
    div = _cross_exchange_divergence({"binance": 100.0, "okx": 102.0})
    assert div is not None
    assert div >= 1.9


@pytest.mark.asyncio
async def test_optimize_execution_mocked():
    fake_ctx = {
        "canonical_symbol": "ETH",
        "volatility_24h_pct": 2.0,
        "liquidity_usd": 20_000_000,
        "price_usd": 3000,
        "source": "test",
    }
    with patch(
        "bd_platform.execution_optimizer._market_liquidity",
        new=AsyncMock(return_value=fake_ctx),
    ), patch(
        "bd_platform.execution_optimizer._gas_bps_for_chain",
        new=AsyncMock(return_value=8.0),
    ):
        out = await optimize_execution(asset="ETH", amount_usd=10_000)
    assert out["ok"] is True
    assert out["feature"] == "#56"
    assert len(out["routes"]) >= len(DEX_VENUES) // 2
    assert out["dex_venue_count"] >= 20
    assert out["cex_venue_count"] == len(CEX_VENUES)
    assert out["sla_met"] is True
    assert out["ai_recommendation_badge"]


@pytest.mark.asyncio
async def test_flash_crash_evaluate_mocked():
    with patch(
        "bd_platform.flash_crash_protection._fetch_multi_exchange_prices",
        new=AsyncMock(return_value={"binance": 100.0, "okx": 99.5, "bybit": 99.8}),
    ), patch(
        "bd_platform.flash_crash_protection._price_velocity",
        return_value=-4.5,
    ):
        out = await evaluate_flash_protection("BTC")
    assert out["ok"] is True
    assert out["feature"] == "#57"
    assert out["circuit_breaker"]["level"] in {"orange", "red"}
    assert out["decision_engine_signal"]["action"] in {"pause", "delay", "resume"}
    assert out["classification"]["event_type"] == "flash_crash"


def test_circuit_breaker_status():
    st = circuit_breaker_status()
    assert st["ok"] is True
    assert "global_level" in st
