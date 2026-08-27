"""Tests — Impermanent Loss Live Simulator."""

from __future__ import annotations

import math

import pytest

from lp_il_simulator import (
    compute_impermanent_loss_pct,
    hodl_value_ratio,
    il_vulnerability_score,
    lp_value_ratio,
    simulate_lp_position,
)


def test_il_zero_at_par():
    assert compute_impermanent_loss_pct(1.0) == 0.0


def test_il_symmetric():
    il_up = compute_impermanent_loss_pct(4.0)
    il_down = compute_impermanent_loss_pct(0.25)
    assert abs(il_up - il_down) < 1e-9
    assert abs(il_up + 0.2) < 0.001  # -20% at 4x or 0.25x


def test_il_known_2x():
    il = compute_impermanent_loss_pct(2.0)
    expected = 2 * math.sqrt(2) / 3 - 1
    assert abs(il - expected) < 1e-9


def test_lp_vs_hodl_ratios():
    r = 1.5
    assert lp_value_ratio(r) < hodl_value_ratio(r)  # LP underperforms HODL when r != 1


def test_simulate_lp_position_structure():
    out = simulate_lp_position(
        amount_usd=10_000,
        entry_price=3000,
        exit_price=3600,
        fee_apy_pct=10,
        horizon_days=30,
    )
    assert out["ok"] is True
    assert out["data_state"] == "LIVE"
    assert out["impermanent_loss_pct"] < 0
    assert out["fee_income_usd"] > 0
    assert len(out["il_curve"]) > 10


def test_simulate_invalid_inputs():
    out = simulate_lp_position(amount_usd=0, entry_price=1, exit_price=2)
    assert out["ok"] is False
    assert out["data_state"] == "MISSING"


def test_vulnerability_score_range():
    out = il_vulnerability_score(symbol="ETH-USDC", volatility_30d_pct=60, liquidity_usd=500_000)
    assert 0 <= out["il_vulnerability_score"] <= 100
    assert out["success"] is True


@pytest.mark.asyncio
async def test_fetch_live_pools_mock(monkeypatch):
    async def fake_json(url, *, params=None):
        return {
            "pairs": [
                {
                    "pairAddress": "0xabc",
                    "dexId": "uniswap",
                    "chainId": "ethereum",
                    "priceUsd": "3000",
                    "liquidity": {"usd": 5_000_000},
                    "volume": {"h24": 1_000_000},
                    "priceChange": {"h24": 5},
                    "baseToken": {"symbol": "WETH"},
                    "quoteToken": {"symbol": "USDC"},
                }
            ]
        }

    monkeypatch.setattr("lp_il_simulator._get_json", fake_json)
    from lp_il_simulator import fetch_live_pools

    out = await fetch_live_pools("ETH USDC")
    assert out["data_state"] == "LIVE"
    assert out["count"] == 1
    assert out["pools"][0]["liquidity_usd"] == 5_000_000


@pytest.mark.asyncio
async def test_simulate_lp_live_mock(monkeypatch):
    async def fake_pools(*a, **k):
        return {
            "pools": [
                {
                    "pair_address": "0x1",
                    "dex": "uniswap",
                    "chain": "ethereum",
                    "base_symbol": "ETH",
                    "quote_symbol": "USDC",
                    "price_usd": 3000,
                    "liquidity_usd": 10_000_000,
                    "price_change_24h_pct": 10,
                }
            ],
            "data_state": "LIVE",
        }

    async def fake_apy(*a, **k):
        return 12.5

    monkeypatch.setattr("lp_il_simulator.fetch_live_pools", fake_pools)
    monkeypatch.setattr("lp_il_simulator._match_defillama_apy", fake_apy)
    from lp_il_simulator import simulate_lp_live

    out = await simulate_lp_live(symbol="ETH-USDC", amount_usd=5000)
    assert out["ok"] is True
    assert out["sla_met"] is True
    assert out["simulation"]["fee_income_usd"] > 0


def test_il_api_live_endpoint(tmp_path, monkeypatch):
    import asyncio
    import config
    import database

    db_path = tmp_path / "il-api.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    asyncio.run(database.init_db())

    async def fake_live(**kwargs):
        return {
            "ok": True,
            "success": True,
            "headline": "IL -5.72%",
            "simulation": simulate_lp_position(
                amount_usd=10_000, entry_price=3000, exit_price=3300, fee_apy_pct=5
            ),
            "vulnerability": il_vulnerability_score(symbol="ETH-USDC"),
            "latency_ms": 120,
            "data_state": "LIVE",
        }

    monkeypatch.setattr("lp_il_simulator.simulate_lp_live", fake_live)
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    r = c.get("/api/platform/defi/il/live?token_a=ETH&token_b=USDC")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "simulation" in body


def test_il_simulator_page(tmp_path, monkeypatch):
    import asyncio
    import config
    import database

    db_path = tmp_path / "il-page.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    asyncio.run(database.init_db())

    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    r = c.get("/il-simulator")
    assert r.status_code == 200
    assert "Impermanent Loss Live Simulator" in r.text
    assert "/api/platform/defi/il/live" in r.text
