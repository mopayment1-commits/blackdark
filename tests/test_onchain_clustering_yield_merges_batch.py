"""Tests — #634 #637 #639 merged features batch."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import defi_opportunity_scanner as dos
from bd_platform import onchain_metrics_library as oml
from bd_platform import whale_clustering_engine as wce


@pytest.fixture
def oml_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_library_seed.json"
    p.write_text(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(oml, "_SEED_PATH", p)
    return p


@pytest.fixture
def wce_seed(tmp_path, monkeypatch):
    p = tmp_path / "whale_clustering_engine_seed.json"
    p.write_text(Path("data/whale_clustering_engine_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(wce, "_SEED_PATH", p)
    return p


@pytest.fixture
def dos_seed(tmp_path, monkeypatch):
    p = tmp_path / "defi_opportunity_scanner_seed.json"
    p.write_text(Path("data/defi_opportunity_scanner_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(dos, "_SEED_PATH", p)
    return p


# --- #634 Whale vs Retail Flow ---


def test_634_panel_ok(oml_seed):
    panel = oml.build_whale_vs_retail_flow_panel("BTC")
    assert panel["ok"] is True
    assert panel["feature_ref"] == 634


def test_634_cohort_thresholds_versioned(oml_seed):
    panel = oml.build_whale_vs_retail_flow_panel("BTC")
    th = panel["cohort_thresholds"]
    assert th["documented"] is True
    assert th["version"] == "1.0"
    assert th["same_as_625"] is True
    assert len(th["buckets"]) == 6


def test_634_buy_sell_flow_by_cohort(oml_seed):
    panel = oml.build_whale_vs_retail_flow_panel("BTC")
    shrimp = next(c for c in panel["cohort_flows"] if c["cohort_id"] == "shrimp")
    assert shrimp["selling_pressure"] is True
    assert "selling pressure" in shrimp["flow_interpretation"]


def test_634_whale_retail_divergence(oml_seed):
    panel = oml.build_whale_vs_retail_flow_panel("BTC")
    assert panel["whale_vs_retail_divergence"] is True
    assert panel["divergence_signal"]["integration_408"] is True


def test_634_market_radar_integration(oml_seed):
    panel = oml.build_whale_vs_retail_flow_panel("BTC")
    assert panel["market_radar_sentiment"]["section"] == "market_sentiment"


def test_634_daily_brief_hook(oml_seed):
    panel = oml.build_whale_vs_retail_flow_panel("BTC")
    assert panel["daily_brief_443_474"]["integration_474"] is True


def test_634_in_metrics_library_panel(oml_seed):
    panel = oml.build_metrics_library_panel("BTC", prefer_live=False)
    wr = panel["sub_modules"]["634_whale_vs_retail_flow"]
    assert wr["ok"] is True


# --- #637 Whale Clustering Engine ---


def test_637_cluster_view(wce_seed):
    view = wce.build_cluster_view("0xwhale_alpha")
    assert view["ok"] is True
    assert view["feature_id"] == 637


def test_637_explainable_links(wce_seed):
    view = wce.build_cluster_view("0xwhale_alpha")
    assert view["explainable_links"] is True
    assert all(l.get("why") for l in view["supporting_relationships"])


def test_637_uncertain_cluster(wce_seed):
    view = wce.build_cluster_view("0xprobable_link")
    assert view["uncertain_cluster"] is True
    assert view["confidence_label"] == "محتمل"


def test_637_confirmed_cluster(wce_seed):
    view = wce.build_cluster_view("0xbinance_hot")
    assert view["confidence_label"] == "مؤكد"
    assert view["confidence_pct"] >= 70


def test_637_no_doxxing(wce_seed):
    view = wce.build_cluster_view("0xwhale_alpha")
    assert view["no_doxxing_claims"] is True
    assert view["no_real_identity_disclosure"] is True


def test_637_precision_benchmark(wce_seed):
    bench = wce.run_precision_benchmark()
    assert bench["mandatory_benchmark"] is True
    assert bench["overall_f1"] > 0
    assert bench["entities_tested"] >= 2


def test_637_false_link_control(wce_seed):
    panel = wce.build_whale_cluster_panel()
    suppressed = [
        l for c in panel["clusters"]
        for l in c.get("supporting_relationships", [])
        if "SUPPRESSED" in l.get("why", "")
    ]
    assert len(suppressed) == 0
    seed = wce._load_seed()
    has_suppressed = any(
        l.get("suppressed")
        for c in (seed.get("clusters") or {}).values()
        for l in (c.get("supporting_links") or [])
    )
    assert has_suppressed is True


def test_637_sybil_filter(wce_seed):
    view = wce.build_cluster_view("0xwhale_alpha")
    assert view["sybil_filtered_input_494"] is True


def test_637_affiliation_hook(wce_seed):
    aff = wce.get_cluster_affiliation_for_address("0xwhale_alpha")
    assert aff["cluster_id"] == "cluster_whale_alpha"


def test_637_reconciliation_tests(wce_seed):
    result = wce.run_reconciliation_tests()
    assert result["ok"] is True


# --- #639 Yield Delta Listener ---


def test_639_yield_delta_ok(dos_seed):
    result = dos.build_yield_delta_listener()
    assert result["ok"] is True
    assert result["feature_ref"] == 639


def test_639_base_incentive_separated(dos_seed):
    result = dos.build_yield_delta_listener()
    valid = [s for s in result["spreads"] if not s.get("rejected")]
    aave = next(s for s in valid if s["protocol_identity"] == "Aave v3")
    assert aave["base_apy_pct"] == 3.2
    assert aave["incentive_apy_pct"] == 2.5
    assert aave["total_apy_pct"] == pytest.approx(5.7, abs=0.01)
    assert "base APY" in aave["apy_display"]


def test_639_stale_feeds_rejected(dos_seed):
    result = dos.build_yield_delta_listener()
    assert result["stale_feeds_rejected"] >= 1
    stale = next(s for s in result["spreads"] if s.get("stale"))
    assert stale["rejected"] is True
    assert "قديمة" in stale["stale_display"]


def test_639_protocol_identity(dos_seed):
    result = dos.build_yield_delta_listener()
    valid = [s for s in result["spreads"] if not s.get("rejected")]
    assert all(s.get("protocol_identity") for s in valid)


def test_639_risk_adjusted_ranking(dos_seed):
    result = dos.build_yield_delta_listener()
    ranked = result["ranked_by_risk_adjusted_yield"]
    assert result["no_apy_only_ranking"] is True
    assert ranked[0]["ranking_metric"] == "risk_adjusted_yield"
    yields = [s["risk_adjusted_yield"] for s in ranked]
    assert yields == sorted(yields, reverse=True)


def test_639_sustainability_context(dos_seed):
    result = dos.build_yield_delta_listener()
    top = result["ranked_by_risk_adjusted_yield"][0]
    assert top.get("sustainability_context")
    assert "ينتهي" in top["sustainability_context"]


def test_639_yield_alerts(dos_seed):
    result = dos.build_yield_delta_listener()
    assert result["alert_count"] >= 1


def test_639_in_defi_panel(dos_seed):
    panel = dos.build_defi_panel()
    yd = panel["yield_delta_listener_639"]
    assert yd["ok"] is True


def test_639_reconciliation_tests(dos_seed):
    result = dos.run_reconciliation_tests()
    ids = {c["id"] for c in result["checks"] if c["passed"]}
    assert "yield_delta_639" in ids
    assert "stale_feeds_rejected_639" in ids
