"""Tests — #490 Sharpe, #491 Smart Contract Risk, #492 Strategy Vetting."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import daily_market_brief as dmb
from bd_platform import defi_opportunity_scanner as dos
from bd_platform import portfolio_intelligence_engine as pie
from bd_platform import strategy_simulator as ss
from bd_platform import strategy_vetting as sv
from bd_platform import unified_arbitrage_engine as uae


@pytest.fixture
def pie_seed(tmp_path, monkeypatch):
    main = Path("data/portfolio_intelligence_engine_seed.json")
    p = tmp_path / "portfolio_intelligence_engine_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(pie, "_SEED_PATH", p)
    return p


@pytest.fixture
def dos_seed(tmp_path, monkeypatch):
    main = Path("data/defi_opportunity_scanner_seed.json")
    p = tmp_path / "defi_opportunity_scanner_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(dos, "_SEED_PATH", p)
    return p


@pytest.fixture
def sv_seed(tmp_path, monkeypatch):
    main = Path("data/strategy_vetting_seed.json")
    p = tmp_path / "strategy_vetting_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(sv, "_SEED_PATH", p)
    return p


# --- #490 Sharpe ---


def test_490_sharpe_three_windows(pie_seed):
    sharpe = pie.build_sharpe_intelligence_panel()
    assert sharpe["ok"] is True
    assert set(sharpe["rolling_sharpe"].keys()) == {"30d", "90d", "1y"}


def test_490_risk_free_policy(pie_seed):
    sharpe = pie.build_sharpe_intelligence_panel()
    policy = sharpe.get("risk_free_policy") or {}
    assert policy.get("version") is not None
    assert policy.get("explicit") is True


def test_490_no_cross_window_comparison(pie_seed):
    sharpe = pie.compute_rolling_sharpe()
    assert sharpe["no_cross_window_comparison"] is True
    for w in sharpe["rolling_sharpe"].values():
        assert w.get("comparable_within_window_only") is True


def test_490_explanation(pie_seed):
    sharpe = pie.build_sharpe_intelligence_panel()
    assert "unit of" in (sharpe.get("explanation") or "")


def test_490_daily_brief_integration():
    brief = dmb.generate_daily_brief()
    items = (brief.get("why") or []) + (brief.get("what_changed") or [])
    assert any(i.get("feature_ref_490") == 490 for i in items)


# --- #491 Smart Contract Risk ---


def test_491_protocol_risk_indicators(dos_seed):
    aave = dos.analyze_protocol_smart_contract_risk("aave")
    assert aave["ok"] is True
    assert len(aave["indicators"]) >= 5
    assert "defillama" in aave.get("data_sources", [])


def test_491_contract_risk_view(dos_seed):
    view = dos.build_smart_contract_risk_view()
    assert view["count"] >= 1
    assert view["feature_ref"] == 491


def test_491_opportunity_score_adjustment(dos_seed):
    opp = {"asset": "ETH", "protocol_id": "aave", "net_edge_bps": 20}
    adj = dos.apply_protocol_risk_to_opportunity_score(opp)
    assert adj.get("adjusted") is True
    assert adj.get("adjusted_opportunity_bps") is not None


def test_491_defi_panel(dos_seed):
    panel = dos.build_defi_panel()
    assert (panel.get("smart_contract_risk_491") or {}).get("ok") is True


# --- #492 Strategy Vetting ---


def test_492_eligible_strategy(sv_seed):
    vet = sv.vet_strategy("momentum_cross_venue")
    assert vet["eligible"] is True
    assert vet["strategy_grade"] in ("A", "B")
    assert len(vet["factors"]) == 6


def test_492_reject_guaranteed_claim(sv_seed):
    vet = sv.vet_strategy("guaranteed_alpha")
    assert vet["auto_rejected"] is True
    assert vet["eligible"] is False


def test_492_small_sample_penalty(sv_seed):
    vet = sv.vet_strategy("low_sample_scalper")
    assert vet["small_sample_penalty"] is True
    assert vet["eligible"] is False


def test_492_overfit_penalty(sv_seed):
    vet = sv.vet_strategy("overfit_momentum")
    assert vet.get("overfit_penalty", 0) > 0


def test_492_thresholds_versioned(sv_seed):
    status = sv.strategy_vetting_status()
    assert status["thresholds_version"] is not None


def test_492_arbitrage_filter(sv_seed):
    feed = uae.build_unified_feed()
    assert feed.get("strategy_quality_gate_492") is not None


def test_492_simulator_integration(sv_seed):
    panel = ss.build_strategy_simulator_panel()
    approved = panel.get("approved_strategies_492") or {}
    assert approved.get("count", 0) >= 1


# --- Reconciliation ---


def test_reconciliation_all(pie_seed, dos_seed, sv_seed):
    assert pie.run_reconciliation_tests()["ok"] is True
    assert dos.run_reconciliation_tests()["ok"] is True
    assert sv.run_reconciliation_tests()["ok"] is True
    assert dmb.run_reconciliation_tests()["ok"] is True
