"""Tests — #710 Yield Arbitrage + #711 Yields Screener (DeFi Yield Center)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from bd_platform import defi_yield_center as dyc


@pytest.fixture
def isolated_yield_center(tmp_path, monkeypatch):
    seed = tmp_path / "defi_yield_center_seed.json"
    store = tmp_path / "defi_yield_center.json"
    stale_date = (datetime.now(UTC) - timedelta(days=10)).isoformat()
    fresh_date = datetime.now(UTC).isoformat()
    seed.write_text(
        json.dumps({
            "apy_methodology": {
                "version": "v1.0",
                "formula": "APY = (fees_24h * 365 / TVL) * 100 + incentive_APY",
                "stale_threshold_days": 7,
            },
            "pools": [
                {
                    "id": "active-pool",
                    "protocol": "Aave",
                    "pool": "ETH Supply",
                    "chain": "ethereum",
                    "current_apy_pct": 12.0,
                    "tvl_usd": 50_000_000,
                    "risk_level": "medium",
                    "last_interaction_at_utc": fresh_date,
                },
                {
                    "id": "stale-pool",
                    "protocol": "AbandonedFarm",
                    "pool": "DEAD-USDC",
                    "chain": "ethereum",
                    "current_apy_pct": 25.0,
                    "tvl_usd": 500_000,
                    "risk_level": "high",
                    "last_interaction_at_utc": stale_date,
                },
            ],
            "arbitrage_opportunities": [
                {
                    "id": "arb-test",
                    "from_pool_id": "active-pool",
                    "to_pool_id": "active-pool",
                    "from_protocol": "Aave",
                    "to_protocol": "Uniswap",
                    "gross_yield_delta_pct": 8.8,
                    "gas_cost_usd": 45.0,
                    "bridge_cost_usd": 25.0,
                    "lockup_days": 3,
                    "slippage_bps": 15,
                    "position_usd": 100_000,
                    "protocol_risk_score": 3,
                    "simulation_6m_success_pct": 78,
                    "tier_required": "pro",
                },
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(dyc, "_SEED_PATH", seed)
    monkeypatch.setattr(dyc, "_STORE_PATH", store)
    return store


def test_stale_pools_excluded(isolated_yield_center):
    result = dyc.screen_yield_pools(exclude_stale=True)
    pool_ids = [p["id"] for p in result["pools"]]
    assert "active-pool" in pool_ids
    assert "stale-pool" not in pool_ids
    assert result["stale_pools_excluded"] is True


def test_screener_display_format(isolated_yield_center):
    pool = dyc.screen_yield_pools(exclude_stale=True)["pools"][0]
    assert "Pool ETH Supply:" in pool["screener_display"]
    assert "APY 12.0%" in pool["screener_display"]
    assert "TVL $50M" in pool["screener_display"]
    assert "Risk:" in pool["screener_display"]
    assert "Stale: ❌ No" in pool["screener_display"]


def test_apy_methodology_documented(isolated_yield_center):
    result = dyc.screen_yield_pools()
    assert "apy_methodology" in result
    assert "formula" in result["apy_methodology"]


def test_arbitrage_costs_included(isolated_yield_center):
    opp = dyc.list_yield_arbitrage()["opportunities"][0]
    assert opp["costs_included"] is True
    assert opp["gas_cost_usd"] == 45.0
    assert opp["bridge_cost_usd"] == 25.0
    assert opp["slippage_usd"] > 0
    assert opp["lockup_days"] == 3
    assert opp["total_switching_cost_usd"] > 0
    assert opp["net_yield_delta_pct"] < opp["gross_yield_delta_pct"]


def test_break_even_horizon(isolated_yield_center):
    opp = dyc.list_yield_arbitrage()["opportunities"][0]
    assert opp["break_even_days"] is not None
    assert "recover switching cost" in opp["break_even_display"].lower()


def test_no_guaranteed_yield(isolated_yield_center):
    screener = dyc.screen_yield_pools()
    arbitrage = dyc.list_yield_arbitrage()
    assert screener["no_guaranteed_yield"] is True
    assert arbitrage["no_guaranteed_yield"] is True
    assert "No guaranteed yield" in arbitrage["disclaimer"]


def test_simulation_only_no_auto_execute(isolated_yield_center):
    arbitrage = dyc.list_yield_arbitrage()
    assert arbitrage["auto_execute"] is False
    assert arbitrage["simulation_only"] is True
    assert arbitrage["execute_requires_mfa"] is True


def test_historical_simulation(isolated_yield_center):
    sim = dyc.run_arbitrage_simulation("arb-test")
    assert sim["ok"] is True
    assert sim["historical_simulation"] is True
    assert sim["success_rate_pct"] == 78
    assert "6-month" in sim["simulation_display"]


def test_optimization_surface(isolated_yield_center):
    result = dyc.optimize_yield_allocation(capital_usd=100_000, max_risk="high")
    assert result["ok"] is True
    assert result["feature"] == 198
    assert result["simulation_only"] is True
    assert len(result["allocation"]) >= 1


@pytest.mark.asyncio
async def test_unified_dashboard(isolated_yield_center, monkeypatch):
    def fake_list_yield_pools(**kwargs):
        return {"ok": True, "pools": [], "count": 0}

    monkeypatch.setattr(
        "bd_platform.yield_sustainability_score.list_yield_pools",
        fake_list_yield_pools,
    )
    dash = await dyc.get_yield_center_dashboard()
    assert dash["ok"] is True
    assert 711 in dash["integrated_features"]
    assert 709 in dash["integrated_features"]
    assert 710 in dash["integrated_features"]
    assert 198 in dash["integrated_features"]
    assert "screener" in dash["surfaces"]
    assert "arbitrage" in dash["surfaces"]


def test_status_flags(isolated_yield_center):
    status = dyc.defi_yield_center_status()
    assert status["costs_included"] is True
    assert status["historical_simulation_tests"] is True
    assert status["auto_execute"] is False
    assert status["execute_requires_mfa"] is True
    assert status["disclaimer_hideable"] is False


def test_full_seed_exists():
    seed = json.loads(Path("data/defi_yield_center_seed.json").read_text(encoding="utf-8"))
    assert len(seed["pools"]) >= 5
    assert len(seed["arbitrage_opportunities"]) >= 2
    assert "yield-stale-pool" in [p["id"] for p in seed["pools"]]


def test_api_routes(isolated_yield_center, monkeypatch):
    def fake_list_yield_pools(**kwargs):
        return {"ok": True, "pools": [], "count": 0}

    monkeypatch.setattr(
        "bd_platform.yield_sustainability_score.list_yield_pools",
        fake_list_yield_pools,
    )

    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)

    status = c.get("/api/platform/defi/yield-center/status")
    assert status.status_code == 200
    assert 710 in status.json()["feature_ids"]
    assert 711 in status.json()["feature_ids"]

    screener = c.get("/api/platform/defi/yield-center/screener")
    assert screener.status_code == 200
    assert screener.json()["feature"] == 711
    assert all(not p.get("stale") for p in screener.json()["pools"])

    arbitrage = c.get("/api/platform/defi/yield-center/arbitrage")
    assert arbitrage.status_code == 200
    assert arbitrage.json()["feature"] == 710
    assert arbitrage.json()["auto_execute"] is False

    sim = c.post("/api/platform/defi/yield-center/arbitrage/arb-test/simulate")
    assert sim.status_code == 200
    assert sim.json()["success_rate_pct"] == 78

    optimize = c.get("/api/platform/defi/yield-center/optimize?capital_usd=50000")
    assert optimize.status_code == 200
    assert optimize.json()["feature"] == 198

    dashboard = c.get("/api/platform/defi/yield-center/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["module"] == "DeFi Yield Center"
