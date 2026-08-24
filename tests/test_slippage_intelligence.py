"""Tests — Slippage Intelligence Module (#5 + #17 unified)."""

from __future__ import annotations

import pytest

from bd_platform.slippage_tolerance_optimizer import (
    _amm_directional_slippage,
    _directional_bias,
    _volatility_adjustment,
    compute_asymmetric_slippage_cost,
    optimize_slippage_tolerance,
)


def test_directional_bias_balanced():
    assert _directional_bias(50, 52) == "balanced"
    assert _directional_bias(60, 40) == "buy_heavy"
    assert _directional_bias(30, 50) == "sell_heavy"


def test_amm_directional_asymmetry():
    buy = _amm_directional_slippage(amount_usd=10_000, liquidity_usd=5_000_000, price=3000, side="buy")
    sell = _amm_directional_slippage(amount_usd=10_000, liquidity_usd=5_000_000, price=3000, side="sell")
    assert buy != sell


@pytest.mark.asyncio
async def test_asymmetric_slippage_mock(monkeypatch):
    async def fake_ctx(asset):
        return {
            "canonical_symbol": "ETH",
            "volatility_24h_pct": 2.0,
            "liquidity_usd": 10_000_000,
            "price_usd": 3000,
            "source": "test",
        }

    async def fake_book(symbol):
        return {
            "asks": [[3000, 100], [3001, 50], [3002, 50]],
            "bids": [[2999, 100], [2998, 50], [2997, 50]],
        }

    async def fake_gas(chain, quote_usd, *, hops=1):
        return 10.0

    monkeypatch.setattr("bd_platform.slippage_tolerance_optimizer._market_context", fake_ctx)
    monkeypatch.setattr("bd_platform.slippage_tolerance_optimizer._fetch_cex_order_book", fake_book)
    monkeypatch.setattr("bd_platform.slippage_tolerance_optimizer.gas_cost_bps", fake_gas)

    out = await compute_asymmetric_slippage_cost("ETH", amount_usd=10_000)
    assert out["ok"] is True
    assert out["surface"] == "asymmetric_slippage_cost"
    assert out["module"] == "slippage_intelligence"
    assert out["buy_slippage_bps"] >= 0
    assert out["sell_slippage_bps"] >= 0
    assert "asymmetry_spread_bps" in out
    assert out["directional_bias"] in {"buy_heavy", "sell_heavy", "balanced"}
    assert out["sla_met"] is True


@pytest.mark.asyncio
async def test_slippage_intelligence_includes_asymmetric(monkeypatch):
    async def fake_asym(symbol, *, amount_usd=10_000, chain="ethereum"):
        return {
            "ok": True,
            "buy_slippage_bps": 25.0,
            "sell_slippage_bps": 15.0,
            "asymmetry_spread_bps": 10.0,
            "directional_bias": "buy_heavy",
            "side_tolerance_adjustment_bps": 4.0,
            "alerts": [],
            "sla_met": True,
        }

    async def fake_ctx(asset):
        return {
            "canonical_symbol": "ETH",
            "volatility_24h_pct": 2.0,
            "liquidity_usd": 5_000_000,
            "price_usd": 3000,
            "source": "test",
        }

    async def fake_gas(chain, quote_usd, *, hops=1):
        return 8.0

    monkeypatch.setattr(
        "bd_platform.slippage_tolerance_optimizer.compute_asymmetric_slippage_cost", fake_asym
    )
    monkeypatch.setattr("bd_platform.slippage_tolerance_optimizer._market_context", fake_ctx)
    monkeypatch.setattr("bd_platform.slippage_tolerance_optimizer.gas_cost_bps", fake_gas)

    out = await optimize_slippage_tolerance("ETH", amount_usd=10_000)
    assert out["surface"] == "slippage_intelligence_module"
    assert "#17_asymmetric_slippage_cost" in out["features"]
    assert out["asymmetric_slippage"]["buy_slippage_bps"] == 25.0
    assert out["sla_met"] is True
