"""Tests — #338 Funding Arbitrage Simulator, #341 Fundraising Velocity, #343 Basis Curve."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import funding_arbitrage_simulator as fas
from bd_platform import market_data_engine as mde
from bd_platform import private_market_vc_flow as pmvc


@pytest.fixture
def fas_seed(tmp_path, monkeypatch):
    p = tmp_path / "funding_arbitrage_simulator_seed.json"
    p.write_text(json.dumps({
        "legal_review": {"complete": True, "date": "2026-08-20"},
        "backtest": {"paper_simulation_validated": True, "events_replayed": 10},
        "scenarios": [{
            "scenario_id": "s1", "asset": "BTC",
            "long_venue": "binance", "short_venue": "bybit",
            "funding_rate": 0.0005, "funding_interval_hours": 8,
            "fees_pct": 0.10, "borrow_cost_pct": 0.05,
            "slippage_pct": 0.03, "basis_risk_penalty_pct": 0.02,
            "liquidity_penalty_pct": 0.01,
            "point_in_time_utc": "2026-08-26T10:00:00+00:00",
            "confidence": "medium",
        }],
    }), encoding="utf-8")
    monkeypatch.setattr(fas, "_SEED_PATH", p)
    return p


@pytest.fixture
def fas_seed_blocked(tmp_path, monkeypatch):
    p = tmp_path / "funding_arbitrage_simulator_seed.json"
    p.write_text(json.dumps({
        "legal_review": {"complete": False},
        "scenarios": [],
    }), encoding="utf-8")
    monkeypatch.setattr(fas, "_SEED_PATH", p)
    return p


@pytest.fixture
def fvi_seed(tmp_path, monkeypatch):
    p = tmp_path / "private_market_vc_flow_seed.json"
    p.write_text(json.dumps({
        "fundraising_velocity": {
            "formula_version": "1.0",
            "backtest": {"events_tested": 10, "accuracy_pct": 70},
        },
        "projects": [{
            "project_id": "p1", "company": "TestCo", "sector": "defi",
            "stage": "Series A", "funding_velocity_usd_per_month": 1e7,
            "investor_breadth": 5, "investor_quality_tier": "tier_1",
            "valuation_usd": None, "valuation_disclosed": False,
            "rounds_last_90d": 1, "sector_trend": "stable",
        }],
        "rounds": [],
    }), encoding="utf-8")
    monkeypatch.setattr(pmvc, "_SEED_PATH", p)
    return p


@pytest.fixture
def basis_seed(tmp_path, monkeypatch):
    p = tmp_path / "market_data_engine_seed.json"
    p.write_text(json.dumps({
        "basis_curves": {
            "BTC": {
                "spot_price": 100,
                "timestamp_utc": "2026-08-26T10:00:00+00:00",
                "perp": {"venue": "binance", "perp_price": 101},
                "contracts": [{
                    "contract_id": "BTC-Q4",
                    "venue": "binance",
                    "futures_price": 102,
                    "expiry_utc": "2026-12-26T08:00:00+00:00",
                    "timestamp_utc": "2026-08-26T10:00:00+00:00",
                    "timestamp_sync": True,
                }],
            },
        },
        "venues": {},
        "provider_semantics": {},
        "weighting": {},
    }), encoding="utf-8")
    monkeypatch.setattr(mde, "_SEED_PATH", p)
    return p


def test_338_renamed_simulator_paper_only(fas_seed):
    panel = fas.build_simulation_panel()
    assert panel["renamed_from"] == "Funding_Arbitrage_Engine"
    assert panel["no_engine_in_name"] is True
    assert panel["paper_simulation_only"] is True
    assert panel["no_live_execution"] is True
    assert panel["tier"] == "pro/institution"
    assert panel["wave"] == 3


def test_338_hypothetical_net_spread_not_opportunity(fas_seed):
    panel = fas.build_simulation_panel()
    result = panel["simulation_results"][0]
    assert "hypothetical_net_spread_pct" in result
    assert result["no_opportunity_language"] is True
    assert result["all_costs_included"] is True
    assert result["no_guaranteed_profit"] is True
    assert "Ranked" in result["rank_display"]
    assert "hypothetical net spread" in result["rank_display"].lower()


def test_338_legal_review_gate_blocks(fas_seed_blocked):
    panel = fas.build_simulation_panel()
    assert panel["ok"] is False
    assert panel["error"] == "legal_review_pending"
    assert panel["release_blocked"] is True


def test_341_renamed_no_score(fvi_seed):
    panel = pmvc.build_fundraising_velocity_indicator()
    assert panel["renamed_from"] == "Fundraising Momentum Score"
    assert panel["no_score_in_name"] is True
    assert panel["no_score_in_output"] is True
    assert panel["no_ranking_list_by_score"] is True
    assert panel["title"] == "Fundraising Velocity Indicator"


def test_341_component_breakdown_not_score(fvi_seed):
    panel = pmvc.build_fundraising_velocity_indicator()
    bd = panel["activity_breakdowns"][0]
    assert bd["output_format"] == "fundraising_activity_breakdown"
    assert "velocity" in bd["components"]
    assert "breadth" in bd["components"]
    assert "stage" in bd["components"]
    assert bd["valuation"]["undisclosed_excluded"] is True
    assert bd["no_undisclosed_valuation_invention"] is True


def test_341_formula_documented(fvi_seed):
    panel = pmvc.build_fundraising_velocity_indicator()
    assert panel["formula"]["no_black_box"] is True
    assert panel["formula"]["formula_version"] == "1.0"


def test_343_basis_curve_absorbed(basis_seed):
    curve = mde.build_basis_curve_component("BTC")
    assert curve["sub_task"] == "#343"
    assert curve["title"] == "Basis Curve"
    assert curve["standalone_rejected"] is True
    assert curve["expiry_math_verified"] is True
    assert curve["venue_normalization"] is True
    assert curve["timestamp_sync"] is True
    assert curve["no_basis_trading_recommendation"] is True


def test_343_structure_mathematical_only(basis_seed):
    curve = mde.build_basis_curve_component("BTC")
    point = curve["term_structure"][0]
    assert point["structure_mathematical_only"] is True
    assert point["no_buy_signal"] is True
    assert point["no_implied_carry_claim"] is True
    assert point["days_to_expiry"] > 0


def test_api_routes(fas_seed, fvi_seed, basis_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/funding-arbitrage-simulator/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/funding-arbitrage-simulator").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/market-radar/fundraising-velocity").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/market-radar/basis-curve?asset=BTC").status_code == 200


def test_full_seeds_exist():
    fas_data = json.loads(Path("data/funding_arbitrage_simulator_seed.json").read_text())
    assert fas_data["renamed_from"] == "Funding_Arbitrage_Engine"
    pmvc_data = json.loads(Path("data/private_market_vc_flow_seed.json").read_text())
    assert "341" in pmvc_data.get("absorbed_tickets", {})
    mde_data = json.loads(Path("data/market_data_engine_seed.json").read_text())
    assert "343" in mde_data.get("absorbed_tickets", {})
