"""Tests — #604 #607 #619 #623 merged features batch."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import diligence_risk_scoring as drs
from bd_platform import portfolio_intelligence_engine as pie
from bd_platform import smart_money_flow_tracker as smft
from bd_platform import token_unlock_intelligence_engine as tui


@pytest.fixture
def drs_seed(tmp_path, monkeypatch):
    p = tmp_path / "diligence_risk_scoring_seed.json"
    p.write_text(Path("data/diligence_risk_scoring_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(drs, "_SEED_PATH", p)
    return p


@pytest.fixture
def unlock_seed(tmp_path, monkeypatch):
    p = tmp_path / "token_unlock_intelligence_seed.json"
    p.write_text(Path("data/token_unlock_intelligence_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(tui, "_SEED_PATH", p)
    return p


@pytest.fixture
def portfolio_seed(tmp_path, monkeypatch):
    p = tmp_path / "portfolio_intelligence_engine_seed.json"
    p.write_text(Path("data/portfolio_intelligence_engine_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(pie, "_SEED_PATH", p)
    return p


@pytest.fixture
def smft_seed(tmp_path, monkeypatch):
    p = tmp_path / "smart_money_flow_tracker_seed.json"
    p.write_text(Path("data/smart_money_flow_tracker_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(smft, "_SEED_PATH", p)
    return p


# --- #604 Token Risk Scoring ---


def test_604_composite_score(drs_seed):
    risk = drs.score_token_risk("UNI")
    assert risk["ok"] is True
    assert 0 <= risk["risk_score_0_100"] <= 100
    assert risk["risk_score_0_10"] == round(risk["risk_score_0_100"] / 10, 2)


def test_604_weights_documented(drs_seed):
    risk = drs.score_token_risk("UNI")
    assert risk["weights_documented"] is True
    assert risk["weights_version"] == "1.0.0"
    assert sum(risk["weights"].values()) == pytest.approx(1.0, abs=0.01)


def test_604_evidence_per_component(drs_seed):
    risk = drs.score_token_risk("UNI")
    for comp in risk["risk_breakdown"].values():
        assert len(comp["evidence"]) >= 3


def test_604_grade_and_color(drs_seed):
    risk = drs.score_token_risk("UNI")
    assert risk["risk_grade"] in ("A", "B", "C", "D", "F")
    assert risk["color_coding"] in ("green", "light_green", "yellow", "orange", "red", "gray")


def test_604_portfolio_integration(drs_seed):
    attached = drs.attach_token_risk_to_portfolio_assets()
    assert attached["ok"] is True
    assert attached["count"] >= 2


def test_604_panel_integration(drs_seed):
    panel = drs.build_risk_scoring_panel("UNI")
    assert panel.get("token_risk_604", {}).get("ok") is True


def test_604_reconciliation(drs_seed):
    result = drs.run_reconciliation_tests()
    ids = {c["id"] for c in result["checks"]}
    assert "token_risk_604" in ids
    assert "token_evidence_per_component" in ids


# --- #607 Token Unlock Forecaster ---


def test_607_severity_scoring(unlock_seed):
    low = tui.compute_unlock_severity(0.5)
    med = tui.compute_unlock_severity(2.5)
    high = tui.compute_unlock_severity(6.0)
    crit = tui.compute_unlock_severity(12.0)
    assert low["severity"] == "low"
    assert med["severity"] == "medium"
    assert high["severity"] == "high"
    assert crit["severity"] == "critical"


def test_607_provenance_and_revisions(unlock_seed):
    panel = tui.build_unlock_forecaster_panel()
    entry = panel["unlock_calendar"][0]
    assert entry["schedule_provenance"]["source_url"]
    assert entry["revisions_tracked"] is True
    assert entry["no_deterministic_price_prediction"] is True
    assert entry["display_label"] == "ضغط عرض محتمل"


def test_607_historical_context(unlock_seed):
    panel = tui.build_unlock_forecaster_panel()
    arb = next(e for e in panel["unlock_calendar"] if e["asset"] == "ARB")
    assert arb["historical_impact_context"]["data_driven_not_prediction"] is True


def test_607_capital_protection_alerts(unlock_seed):
    alerts = tui.build_capital_protection_unlock_alerts()
    assert alerts["ok"] is True
    assert any(a["asset"] == "SUI" for a in alerts["alerts"])


def test_607_alert_tests(unlock_seed):
    qa = tui.run_unlock_alert_tests()
    assert qa["all_passed"] is True


def test_607_market_radar_timeline(unlock_seed):
    timeline = tui.build_market_radar_unlock_timeline()
    assert timeline["surface"] == "market_radar"
    assert timeline["no_deterministic_price_prediction"] is True


# --- #619 Wallet PnL ---


def test_619_pnl_breakdown(portfolio_seed):
    pnl = pie.build_wallet_pnl_breakdown("demo_wallet")
    assert pnl["ok"] is True
    assert pnl["fifo_mandatory"] is True
    assert pnl["fees_included"] is True
    assert pnl["total_fees_usd"] > 0


def test_619_realized_unrealized_separated(portfolio_seed):
    pnl = pie.build_wallet_pnl_breakdown("demo_wallet")
    assert pnl["realized_vs_unrealized_separated"] is True
    assert pnl["realized_pnl_usd"] is not None
    assert pnl["unrealized_pnl_usd"] is not None


def test_619_breakeven_integration(portfolio_seed):
    pnl = pie.build_wallet_pnl_breakdown("demo_wallet")
    assert (pnl.get("breakeven_integration_404") or {}).get("shared_cost_basis_engine") is True


def test_619_integrated_panel(portfolio_seed):
    panel = pie.build_integrated_panel()
    assert panel.get("wallet_pnl_breakdown_619", {}).get("ok") is True
    assert panel.get("token_risk_scores_604", {}).get("ok") is True


def test_619_reconciliation(portfolio_seed):
    result = pie.run_reconciliation_tests()
    ids = {c["id"] for c in result["checks"]}
    assert "wallet_pnl_619" in ids
    assert "fees_included_619" in ids


# --- #623 Wallet Shadowing ---


def test_623_shadowing_alerts(smft_seed):
    shadow = smft.build_wallet_shadowing_alerts()
    assert shadow["ok"] is True
    assert shadow["alert_count"] >= 2


def test_623_label_confidence(smft_seed):
    shadow = smft.build_wallet_shadowing_alerts()
    low_conf = next(a for a in shadow["alerts"] if a["label_confidence_pct"] < 95)
    assert "محتمل" in low_conf["entity_label"]
    assert low_conf["no_identity_fabrication"] is True


def test_623_reorg_handling(smft_seed):
    shadow = smft.build_wallet_shadowing_alerts()
    assert shadow["reorg_confirmation_blocks"] == 6
    assert all(a.get("reorg_safe") for a in shadow["alerts"])


def test_623_dedupe(smft_seed):
    shadow = smft.build_wallet_shadowing_alerts()
    aggregated = [a for a in shadow["alerts"] if a.get("aggregated")]
    assert len(aggregated) >= 1
    assert aggregated[0]["transfer_count"] >= 2


def test_623_why_relevant(smft_seed):
    shadow = smft.build_wallet_shadowing_alerts()
    assert all(a.get("why_relevant") for a in shadow["alerts"])


def test_623_panel_integration(smft_seed):
    panel = smft.build_smart_money_flow_panel()
    assert panel.get("wallet_shadowing_623", {}).get("ok") is True


def test_623_reconciliation(smft_seed):
    result = smft.run_reconciliation_tests()
    ids = {c["id"] for c in result["checks"]}
    assert "wallet_shadowing_623" in ids
    assert "reorg_handling_623" in ids
