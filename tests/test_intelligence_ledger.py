"""Tests — Intelligence Ledger Sprint 2 (features #5–#6)."""

from __future__ import annotations

import asyncio

import pytest

from bd_platform.intelligence_ledger import _effective_cost_bps, build_execution_intelligence
from bd_platform.slippage_tolerance_optimizer import (
    _depth_adjustment,
    _gas_adjustment,
    _volatility_adjustment,
    optimize_slippage_tolerance,
)


def test_volatility_adjustment_scales_with_vol():
    assert _volatility_adjustment(0) == 0
    assert _volatility_adjustment(5) == 40
    assert _volatility_adjustment(20) == 120  # capped


def test_depth_adjustment_thin_pool_widens():
    assert _depth_adjustment(amount_usd=50_000, liquidity_usd=100_000) > 0
    assert _depth_adjustment(amount_usd=1_000, liquidity_usd=10_000_000) < 0


def test_gas_adjustment_defaults_when_missing():
    assert _gas_adjustment(None) == 5.0
    assert _gas_adjustment(50) == 30.0


def test_effective_cost_bps_penalizes_price_deviation():
    cost = _effective_cost_bps(
        venue="1inch",
        price=3100,
        reference_price=3000,
        slippage_bps=50,
        gas_bps=10,
    )
    assert cost > 50 + 10


@pytest.mark.asyncio
async def test_slippage_optimizer_mock(monkeypatch):
    async def fake_ctx(asset):
        return {
            "volatility_24h_pct": 3.0,
            "liquidity_usd": 5_000_000,
            "price_usd": 3000,
            "source": "test",
        }

    async def fake_gas(chain, quote_usd, *, hops=1):
        return 12.0

    monkeypatch.setattr(
        "bd_platform.slippage_tolerance_optimizer._market_context", fake_ctx
    )
    monkeypatch.setattr("bd_platform.slippage_tolerance_optimizer.gas_cost_bps", fake_gas)

    out = await optimize_slippage_tolerance("ETH", amount_usd=10_000)
    assert out["ok"] is True
    assert 10 <= out["optimal_slippage_bps"] <= 300
    assert out["sla_met"] is True
    assert "volatility_adj_bps" in out["optimization"]


@pytest.mark.asyncio
async def test_execution_intelligence_mock(monkeypatch):
    async def fake_slippage(symbol, *, amount_usd=10_000, chain="ethereum", user_tolerance_bps=None):
        return {
            "ok": True,
            "optimal_slippage_bps": 55,
            "optimization": {
                "inputs": {
                    "price_usd": 3000,
                    "gas_cost_bps": 15,
                    "amm_impact_bps_estimate": 22,
                }
            },
            "alerts": [],
        }

    async def fake_oneinch(**kwargs):
        return {
            "ok": True,
            "price_usd": 2995,
            "quote": {
                "source": "dexscreener_1inch_fallback",
                "price_usd": 2995,
                "liquidity_usd": 2_000_000,
                "fallback": True,
            },
        }

    monkeypatch.setattr(
        "bd_platform.intelligence_ledger.optimize_slippage_tolerance", fake_slippage
    )
    monkeypatch.setattr("bd_platform.intelligence_ledger.fetch_oneinch_quote", fake_oneinch)

    out = await build_execution_intelligence(asset="ETH", amount_usd=10_000)
    assert out["ok"] is True
    assert out["sprint"] == 2
    assert out["recommended_route"]["venue"] in {"1inch", "amm_pool", "cex_spot"}
    assert len(out["routes"]) >= 2
    assert out["oneinch_data_source"]["ok"] is True
    assert out["sla_met"] is True


def test_intelligence_ledger_api(tmp_path, monkeypatch):
    import config
    import database

    db_path = tmp_path / "il.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    asyncio.run(database.init_db())

    async def fake_exec(**kwargs):
        return {
            "ok": True,
            "headline": "Use 1inch with 55bps",
            "routes": [{"venue": "1inch", "effective_cost_bps": 60}],
            "recommended_route": {"venue": "1inch", "effective_cost_bps": 60},
            "sla_met": True,
            "latency_ms": 120,
            "data_sources": ["1inch"],
        }

    async def fake_slip(symbol, **kwargs):
        return {
            "ok": True,
            "optimal_slippage_bps": 55,
            "headline": "Optimal slippage 55bps",
            "optimization": {"formula": "test"},
            "sla_met": True,
            "latency_ms": 80,
        }

    monkeypatch.setattr(
        "bd_platform.intelligence_ledger.build_execution_intelligence", fake_exec
    )
    monkeypatch.setattr(
        "bd_platform.slippage_tolerance_optimizer.optimize_slippage_tolerance", fake_slip
    )

    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/execution").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/slippage-optimize").status_code == 200
    r = c.get("/intelligence-ledger")
    assert r.status_code == 200
    assert "Intelligence Ledger" in r.text
