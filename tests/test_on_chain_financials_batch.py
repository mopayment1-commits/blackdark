"""Tests — #641 On-Chain Financials merged into #472."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import investment_thesis_scoring as its
from bd_platform import on_chain_financials as ocf
from bd_platform import onchain_metrics_library as oml


@pytest.fixture
def fin_seed(tmp_path, monkeypatch):
    p = tmp_path / "on_chain_financials_seed.json"
    p.write_text(Path("data/on_chain_financials_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ocf, "_SEED_PATH", p)
    return p


@pytest.fixture
def thesis_seed(tmp_path, monkeypatch):
    p = tmp_path / "investment_thesis_scoring_seed.json"
    p.write_text(Path("data/investment_thesis_scoring_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(its, "_SEED_PATH", p)
    return p


@pytest.fixture
def oml_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_library_seed.json"
    p.write_text(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(oml, "_SEED_PATH", p)
    return p


def test_641_panel_ok(fin_seed):
    panel = ocf.build_on_chain_financials("uniswap")
    assert panel["ok"] is True
    assert panel["legal_name"] == "On-Chain Financials"
    assert panel["standalone"] is False


def test_641_mandatory_metrics(fin_seed):
    panel = ocf.build_on_chain_financials("uniswap")
    assert len(panel["mandatory_metrics"]) == 5
    m = panel["metrics"]
    assert m["revenue_30d"] == 12_500_000
    assert m["profit_margin"] == pytest.approx(77.6, abs=0.5)
    assert m["ps_ratio"] == pytest.approx(30.0, abs=1.0)
    assert m["revenue_per_user"] is not None
    assert m["growth_rate_qoq"] is not None


def test_641_on_chain_not_estimate(fin_seed):
    panel = ocf.build_on_chain_financials("lido")
    assert panel["no_estimates"] is True
    assert panel["financials"]["fee_source_type"] == "on_chain_staking_fees"


def test_641_peer_comparison(fin_seed):
    panel = ocf.build_on_chain_financials("uniswap")
    peer = panel["peer_comparison"]
    assert peer is not None
    assert "Visa" in peer["display"]
    assert peer["not_equity_comparison"] is True


def test_641_query_latency(fin_seed):
    panel = ocf.build_on_chain_financials("aave")
    assert panel["data_pipeline"]["query_within_1s"] is True


def test_641_storage_retention(fin_seed):
    panel = ocf.build_on_chain_financials("aave")
    assert panel["data_pipeline"]["store"]["retention_met"] is True
    assert panel["data_pipeline"]["store"]["retention_years"] >= 2


def test_641_accuracy(fin_seed):
    panel = ocf.build_on_chain_financials("uniswap")
    assert panel["accuracy_pct"] >= 99.99


def test_641_asset_card_tab(fin_seed):
    tab = ocf.build_asset_financials_tab("UNI")
    assert tab["tab"] == "الأرقام المالية"
    assert tab["asset_card_integration"] is True


def test_641_market_radar_sector(fin_seed):
    sector = ocf.build_market_radar_revenue_sector()
    assert sector["ok"] is True
    assert sector["count"] >= 3
    assert sector["protocols"][0]["revenue_30d_usd"] >= sector["protocols"][-1]["revenue_30d_usd"]


def test_641_thesis_dimension_7(fin_seed):
    dim = ocf.score_on_chain_financials_dimension("UNI")
    assert dim["thesis_dimension_number"] == 7
    assert dim["dimension_score"] > 50


def test_641_metrics_library_577(fin_seed, oml_seed):
    lib = ocf.build_metrics_library_financials("uniswap")
    assert lib["ok"] is True
    assert "protocol_revenue" in lib["metrics"]
    assert "protocol_profit_margin" in lib["metrics"]
    assert "ps_ratio" in lib["metrics"]


def test_641_export(fin_seed):
    export = ocf.export_financials_report("uniswap")
    assert export["export_ready"] is True
    assert export["report"]["metrics"]["revenue_30d"] > 0


def test_641_thesis_integration(fin_seed, thesis_seed):
    thesis = its.score_investment_thesis("UNI")
    assert thesis["dimension_count"] == 7
    assert "on_chain_financials" in thesis["dimensions"]
    assert thesis["dimensions"]["on_chain_financials"]["evidence_source"] == "on_chain_fee_data"


def test_641_thesis_seven_dimensions(fin_seed, thesis_seed):
    result = its.run_reconciliation_tests()
    ids = {c["id"] for c in result["checks"] if c["passed"]}
    assert "seven_dimensions" in ids
    assert "on_chain_financials_641" in ids


def test_641_reconciliation(fin_seed):
    result = ocf.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["passed"] == result["total"]
