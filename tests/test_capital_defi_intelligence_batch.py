"""Tests — #648 Capital Formation Radar, #650 Cross-Chain Fundamentals, #651 DeFi Decision Intelligence."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import capital_formation_radar as cfr
from bd_platform import daily_market_brief as dmb
from bd_platform import defi_decision_intelligence as ddi
from bd_platform import defi_opportunity_scanner as dos
from bd_platform import on_chain_financials as ocf
from bd_platform import unified_arbitrage_engine as uae


@pytest.fixture
def capital_seed(tmp_path, monkeypatch):
    p = tmp_path / "capital_formation_radar_seed.json"
    p.write_text(Path("data/capital_formation_radar_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(cfr, "_SEED_PATH", p)
    return p


@pytest.fixture
def defi_decision_seed(tmp_path, monkeypatch):
    p = tmp_path / "defi_decision_intelligence_seed.json"
    p.write_text(Path("data/defi_decision_intelligence_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ddi, "_SEED_PATH", p)
    return p


@pytest.fixture
def fin_seed(tmp_path, monkeypatch):
    p = tmp_path / "on_chain_financials_seed.json"
    p.write_text(Path("data/on_chain_financials_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ocf, "_SEED_PATH", p)
    return p


@pytest.fixture
def brief_seed(tmp_path, monkeypatch):
    p = tmp_path / "daily_market_brief_seed.json"
    p.write_text(Path("data/daily_market_brief_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(dmb, "_SEED_PATH", p)
    return p


def test_648_radar_ok(capital_seed):
    radar = cfr.build_capital_formation_radar()
    assert radar["ok"] is True
    assert radar["standalone"] is False
    assert radar["no_price_guarantee"] is True
    assert len(radar["capital_radar"]) >= 3


def test_648_four_components(capital_seed):
    radar = cfr.build_capital_formation_radar(sector_id="defi_lending")
    entry = radar["capital_radar"][0]
    assert len(entry["components"]) == 4
    assert (radar["formula"] or {}).get("documented") is True


def test_648_heatmap_and_formation_vs_price(capital_seed):
    radar = cfr.build_capital_formation_radar()
    entry = radar["capital_radar"][0]
    assert entry["heatmap_color"] in {"green", "yellow", "orange", "red"}
    assert "formation_vs_price" in entry


def test_648_chart_route(capital_seed):
    chart = cfr.build_capital_formation_chart()
    assert chart["chart_type"] == "radar"
    assert chart["route"] == "/capital-formation"


def test_648_sector_boost(capital_seed):
    boost = cfr.get_sector_formation_boost("layer2")
    assert boost == 0.15


def test_648_institutional_thesis_641(capital_seed, fin_seed):
    radar = cfr.build_capital_formation_radar()
    assert radar["institutional_thesis_641"] is not None


def test_650_cross_chain_dashboard(fin_seed):
    panel = ocf.build_cross_chain_comparables_dashboard()
    assert panel["ok"] is True
    assert panel["tab"] == "Cross-Chain Comparison"
    assert len(panel["metric_definitions"]) >= 6
    assert panel["count"] >= 3
    chain = panel["chains"][0]
    assert "daa" in chain["metrics"]
    assert chain["metrics"]["daa"]["source"] == "on_chain_indexer"


def test_650_normalization_documented(fin_seed):
    panel = ocf.build_cross_chain_comparables_dashboard()
    norm = panel["normalization_methodology"]
    assert norm["documented"] is True
    assert norm["baseline_chain"] == "ethereum"


def test_651_decision_score(defi_decision_seed):
    score = ddi.score_decision_relevance("aave_v3")
    assert score["ok"] is True
    assert score["yield_not_safety"] is True
    assert score["yield_display"]["side_by_side_mandatory"] is True
    assert score["evidence"]["evidence_links"]


def test_651_contradict_signal(defi_decision_seed):
    score = ddi.score_decision_relevance("high_yield_risky")
    assert score["signal"] == "contradict"
    assert "متناقضة" in (score.get("contradict_message") or "")


def test_651_rank_defi_opportunities(defi_decision_seed):
    opps = [{"asset": "ETH", "net_edge_bps": 10}, {"asset": "UNI", "net_edge_bps": 20}]
    ranked = ddi.rank_defi_opportunities_by_relevance(opps)
    assert ranked[0]["ranking_metric"] == "decision_relevance_not_apy_only"
    assert "decision_relevance_score" in ranked[0]


def test_651_defi_scanner_integration(defi_decision_seed):
    panel = dos.build_defi_panel()
    assert panel.get("ranked_by_decision_relevance_651") is True
    assert panel.get("defi_decision_intelligence_651", {}).get("ok") is True


def test_474_capital_radar_in_brief(capital_seed, brief_seed):
    brief = dmb.generate_daily_brief()
    assert brief.get("capital_formation_radar_648") is not None
    assert any(i.get("feature_ref_648") == 648 for i in brief.get("what_changed") or [])


def test_429_formation_ranking_boost(capital_seed):
    opps = [
        {"asset": "ARB", "net_edge_usdt": 100},
        {"asset": "IMX", "net_edge_usdt": 120},
    ]
    boosted = cfr.apply_formation_ranking_boost(opps)
    arb = next(o for o in boosted if o["asset"] == "ARB")
    assert arb.get("capital_formation_boost_648") == 0.15


def test_648_reconciliation(capital_seed, fin_seed):
    result = cfr.run_reconciliation_tests()
    assert result["ok"] is True


def test_650_reconciliation(fin_seed):
    result = ocf.run_reconciliation_tests()
    assert result["ok"] is True
    ids = {c["id"] for c in result["checks"] if c["passed"]}
    assert "cross_chain_650" in ids


def test_651_reconciliation(defi_decision_seed):
    result = ddi.run_reconciliation_tests()
    assert result["ok"] is True
