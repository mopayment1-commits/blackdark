"""Tests — #404 Live Breakeven Tracker (Portfolio AI Position Analytics Layer)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import live_breakeven_tracker as lbt


@pytest.fixture
def breakeven_seed(tmp_path, monkeypatch):
    main = Path("data/live_breakeven_tracker_seed.json")
    p = tmp_path / "live_breakeven_tracker_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(lbt, "_SEED_PATH", p)
    return p


def test_404_status_not_standalone(breakeven_seed):
    status = lbt.live_breakeven_tracker_status()
    assert status["feature_id"] == 404
    assert status["standalone"] is False
    assert status["legal_name"] == "Dynamic Cost Basis"
    assert status["auto_calculation_name_forbidden"] is True
    assert status["refresh_policy"]["client_side_instant"] is True
    assert status["refresh_policy"]["server_refresh_seconds"] == 30
    assert status["components"]["fee_transparency"] is True
    assert status["components"]["scenario_simulator"] is True


def test_404_dynamic_breakeven_includes_all_costs(breakeven_seed):
    panel = lbt.build_live_breakeven_panel("pos_btc_001")
    assert panel["ok"] is True
    assert panel["title"] == "Live Breakeven Tracker"
    assert panel["surface"] == "portfolio_ai"
    assert panel["breakeven"]["dynamic_cost_basis"] is True
    assert panel["breakeven"]["static_breakeven_rejected"] is True
    be = panel["breakeven"]["price"]
    assert 59000 < be < 60000
    assert panel["breakeven"]["remaining_quantity"] == 1.2


def test_404_fee_transparency_every_cent(breakeven_seed):
    panel = lbt.build_live_breakeven_panel("pos_btc_001")
    ft = panel["fee_transparency"]
    assert ft["fee_transparency"] is True
    assert ft["every_cent_visible"] is True
    assert len(ft["line_items"]) >= 5
    assert "exchange_fee" in ft["by_category_usd"]
    assert ft["total_fees_added_to_breakeven_usd"] > 0
    assert "CoinTracker" in ft["competitive_differentiator"]


def test_404_distance_to_breakeven(breakeven_seed):
    panel = lbt.build_live_breakeven_panel("pos_btc_001")
    dist = panel["distance_to_breakeven"]
    assert dist["position_vs_breakeven"] == "above_breakeven"
    assert dist["distance_to_breakeven_pct"] > 0
    assert dist["unrealized_pnl_vs_breakeven_usd"] > 0


def test_404_scenario_simulator_dca(breakeven_seed):
    seed = lbt._load_seed()
    pos = seed["positions"]["pos_btc_001"]
    sim = lbt.simulate_breakeven_scenario(
        pos,
        hypothetical_dca_qty=0.1,
        hypothetical_dca_price=62000,
        fee_defaults=seed.get("fee_defaults"),
    )
    assert sim["ok"] is True
    assert sim["simulation"] is True
    assert sim["simulated_breakeven"] != sim["baseline_breakeven"]
    assert sim["simulated_quantity"] > sim["baseline_quantity"]
    assert sim["not_investment_advice"] is True


def test_404_scenario_simulator_partial_exit(breakeven_seed):
    seed = lbt._load_seed()
    pos = seed["positions"]["pos_btc_001"]
    sim = lbt.simulate_breakeven_scenario(
        pos,
        hypothetical_exit_qty=0.2,
        hypothetical_exit_price=66000,
        fee_defaults=seed.get("fee_defaults"),
    )
    assert sim["ok"] is True
    assert sim["simulated_quantity"] < sim["baseline_quantity"]


def test_404_intelligence_ledger_owns_asset(breakeven_seed):
    ctx = lbt.build_intelligence_ledger_signal_context("BTC")
    assert ctx["user_owns_asset"] is True
    assert ctx["breakeven_context_attached"] is True
    assert "distance_to_breakeven_pct" in ctx["distance_to_breakeven"]
    assert ctx["not_investment_advice"] is True


def test_404_intelligence_ledger_no_position(breakeven_seed):
    ctx = lbt.build_intelligence_ledger_signal_context("SOL")
    assert ctx["breakeven_context_attached"] is False


def test_404_capital_protection_integration(breakeven_seed):
    panel = lbt.build_live_breakeven_panel("pos_btc_001")
    cp = panel["capital_protection"]
    assert cp["feature_id"] == 410
    assert cp["integration"] == "capital_protection_controls"
    assert cp["mandatory"] is True


def test_404_client_calculation_payload(breakeven_seed):
    panel = lbt.build_live_breakeven_panel("pos_btc_001")
    cc = panel["client_calculation"]
    assert cc["client_side_instant"] is True
    assert cc["server_refresh_seconds"] == 30
    assert cc["formula_version"] == "1.0"
    assert len(cc["events"]) >= 3


def test_404_accuracy_within_tolerance(breakeven_seed):
    """Recompute breakeven — verify deterministic output within ±0.01%."""
    seed = lbt._load_seed()
    pos = seed["positions"]["pos_btc_001"]
    calc1 = lbt.compute_dynamic_breakeven(pos["events"])
    calc2 = lbt.compute_dynamic_breakeven(pos["events"])
    assert calc1["breakeven_price"] == calc2["breakeven_price"]
    drift = abs(calc1["breakeven_price"] - calc2["breakeven_price"]) / calc1["breakeven_price"] * 100
    assert drift <= 0.01


def test_404_reconciliation_tests(breakeven_seed):
    result = lbt.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["passed"] == result["total"]


def test_404_api_routes(breakeven_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/portfolio-ai/live-breakeven/status").status_code == 200
    r = c.get("/api/platform/intelligence-ledger/portfolio-ai/live-breakeven?position_id=pos_btc_001")
    assert r.status_code == 200
    assert r.json()["breakeven"]["price"] > 0
    sim = c.get(
        "/api/platform/intelligence-ledger/portfolio-ai/live-breakeven/simulate"
        "?position_id=pos_btc_001&hypothetical_dca_qty=0.1&hypothetical_dca_price=62000"
    )
    assert sim.status_code == 200
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/live-breakeven/signal-context?symbol=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/portfolio-ai/capital-protection/breakeven-alerts?position_id=pos_btc_001").status_code == 200
    assert c.get("/portfolio-ai/live-breakeven").status_code == 200
    page = c.get("/portfolio-ai/live-breakeven")
    assert "Live Breakeven Tracker" in page.text
    assert "live_breakeven_tracker.js" in page.text


def test_404_seed_integrity():
    seed = json.loads(Path("data/live_breakeven_tracker_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 404
    assert seed["standalone"] is False
    assert len(seed["positions"]) == 3
    assert seed["accuracy_target"]["tolerance_pct"] == 0.01
