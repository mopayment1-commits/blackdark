"""Tests — #652 Cross-Protocol Contagion, #653 Custom Ratio Engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import cross_protocol_contagion as cpc
from bd_platform import custom_ratio_engine as cre
from bd_platform import defi_opportunity_scanner as dos
from bd_platform import investment_thesis_scoring as its
from bd_platform import market_radar_indicators as mri


@pytest.fixture
def contagion_seed(tmp_path, monkeypatch):
    p = tmp_path / "cross_protocol_contagion_seed.json"
    p.write_text(Path("data/cross_protocol_contagion_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(cpc, "_SEED_PATH", p)
    return p


@pytest.fixture
def ratio_seed(tmp_path, monkeypatch):
    p = tmp_path / "custom_ratio_engine_seed.json"
    p.write_text(Path("data/custom_ratio_engine_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(cre, "_SEED_PATH", p)
    return p


def test_652_monitor_ok(contagion_seed):
    monitor = cpc.build_contagion_monitor()
    assert monitor["ok"] is True
    assert monitor["standalone"] is False
    assert monitor["dependency_provenance"] is True


def test_652_contagion_vector(contagion_seed):
    vector = cpc.compute_contagion_vector("usdc_circle")
    assert vector["contagion_vector"] >= 80
    assert len(vector["affected_protocols"]) >= 3
    top = vector["affected_protocols"][0]
    assert top["protocol_id"] == "aave"
    assert top["exposure_pct"] == 85
    assert top["dependency_reasons"][0]["provenance_source"]


def test_652_usdc_display(contagion_seed):
    vector = cpc.compute_contagion_vector("usdc_circle")
    assert "Aave" in vector["cascade_scenario"]["display"]


def test_652_graph_visualization(contagion_seed):
    graph = cpc.build_contagion_graph_visualization()
    assert graph["ok"] is True
    assert graph["route"] == "/contagion"
    assert len(graph["graph"]["nodes"]) <= cpc._GRAPH_RENDER_LIMIT
    assert graph["graph"]["hover_shows_dependency_type"] is True


def test_652_portfolio_alert_410(contagion_seed):
    alert = cpc.build_portfolio_cluster_alert_410()
    assert alert["ok"] is True
    assert alert["cluster_threatened"] is True
    assert len(alert["alerts"]) >= 1


def test_652_defi_cancel_438(contagion_seed):
    opps = cpc.cancel_defi_opportunities_in_affected_cluster([{"protocol_id": "aave"}])
    assert opps[0]["contagion_cancelled_652"] is True
    assert opps[0]["signal_suppressed"] is True


def test_652_stablecoin_trigger_467(contagion_seed):
    triggers = cpc.get_contagion_triggers_from_stablecoin_467()
    assert triggers["ok"] is True


def test_652_defi_scanner_integration(contagion_seed):
    panel = dos.build_defi_panel()
    assert panel.get("cross_protocol_contagion_652", {}).get("ok") is True


def test_653_panel_ok(ratio_seed):
    panel = cre.build_ratio_builder_panel()
    assert panel["ok"] is True
    assert panel["route"] == "/ratio-builder"
    assert len(panel["presets"]) >= 3


def test_653_unit_validation(ratio_seed):
    valid = cre.validate_formula("fdv", "revenue_30d")
    assert valid["valid"] is True
    warned = cre.validate_formula("market_cap", "tx_count")
    assert warned["warning"] is not None


def test_653_ratio_compute(ratio_seed):
    ratio = cre.compute_ratio("uniswap", "ps_ratio")
    assert ratio["ok"] is True
    assert ratio["ratio_value"] == pytest.approx(30.0, rel=0.05)
    assert ratio["formula_version"] == "1.0"
    assert ratio["reproducible"] is True


def test_653_missing_not_zero(ratio_seed):
    ratio = cre.compute_ratio("uniswap", "revenue_per_user", as_of_date="2099-01")
    assert ratio["display"] == "N/A"
    assert ratio["ratio_value"] is None


def test_653_reproducible_history(ratio_seed):
    a = cre.compute_ratio("uniswap", "ps_ratio", as_of_date="2025-07")
    b = cre.compute_ratio("uniswap", "ps_ratio", as_of_date="2025-07")
    assert a["ratio_value"] == b["ratio_value"]
    assert a["reproducibility_key"] == b["reproducibility_key"]


def test_653_peer_percentile(ratio_seed):
    peers = cre.build_peer_comparison("uniswap", "ps_ratio")
    assert peers["ok"] is True
    assert peers["percentile"] is not None
    assert peers["peer_count"] >= 3


def test_653_ratio_chart(ratio_seed):
    chart = cre.build_ratio_chart("uniswap", "ps_ratio")
    assert chart["ok"] is True
    assert len(chart["points"]) >= 2
    assert chart["reproducible_history"] is True


def test_653_market_radar_integration(ratio_seed):
    panel = mri.build_market_radar_panel()
    assert panel.get("custom_ratio_engine_653", {}).get("ok") is True


def test_653_thesis_dimension_472(ratio_seed):
    thesis = its.score_investment_thesis("UNI")
    assert thesis.get("custom_ratio_dimension_653") is not None
    assert "custom_ratio_653" in thesis["dimensions"]


def test_652_reconciliation(contagion_seed):
    result = cpc.run_reconciliation_tests()
    assert result["ok"] is True


def test_653_reconciliation(ratio_seed):
    result = cre.run_reconciliation_tests()
    assert result["ok"] is True
