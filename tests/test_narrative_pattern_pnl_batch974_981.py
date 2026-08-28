"""Tests — Batch 34: #974 Narratives, #978 SQL Workspace, #979 Patterns, #980 PIT, #981 PnL."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import data_engine_historical_layer as hist
from bd_platform import data_engine_native_sql_workspace as sql_ws
from bd_platform import market_radar_narrative_sector as narratives
from bd_platform import portfolio_ai_profitability_analyzer as pnl
from bd_platform import signal_engine_pattern_recognition as patterns


@pytest.fixture
def narrative_seed() -> dict:
    return json.loads(Path("data/market_radar_narrative_sector_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def pattern_seed() -> dict:
    return json.loads(Path("data/signal_engine_pattern_recognition_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def pnl_seed() -> dict:
    return json.loads(Path("data/portfolio_ai_profitability_analyzer_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def hist_seed() -> dict:
    return json.loads(Path("data/data_engine_historical_layer_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def sql_seed() -> dict:
    return json.loads(Path("data/data_engine_native_sql_workspace_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_sql_state():
    sql_ws.reset_native_sql_workspace_state()
    yield
    sql_ws.reset_native_sql_workspace_state()


# --- #974 Narrative & Sector Intelligence ---


def test_974_status(narrative_seed):
    status = narratives.narrative_sector_status_974(seed=narrative_seed)
    assert status["standalone_rejected"] is True
    assert status["taxonomy_versioned"] is True
    assert status["no_hindsight_relabeling"] is True
    assert status["min_sources_for_narrative"] == 3


def test_974_leaderboard_rejects_insufficient_evidence(narrative_seed):
    board = narratives.build_narrative_leaderboard_974(seed=narrative_seed)
    assert board["count"] >= 2
    assert board["rejected_insufficient_evidence"] >= 1
    assert board["constituent_transparency"] is True
    for item in board["leaderboard"]:
        assert item["source_count"] >= 3
        assert len(item["constituents"]) >= 1


def test_974_sector_heatmap(narrative_seed):
    heatmap = narratives.build_sector_heatmap_974(seed=narrative_seed)
    assert heatmap["sector_count"] >= 2
    assert all(s.get("no_double_counting") for s in heatmap["heatmap"])


def test_974_narrative_details(narrative_seed):
    details = narratives.get_narrative_details_974("ai_agents", seed=narrative_seed)
    assert details["evidence_sufficient"] is True
    assert details["no_hindsight_relabeling"] is True
    assert len(details["constituents"]) >= 1


def test_974_backtest_90d(narrative_seed):
    bt = narratives.run_narrative_backtest_974(seed=narrative_seed)
    assert bt["backtest_days"] == 90
    assert bt["ok"] is True


def test_974_e2e(narrative_seed):
    e2e = narratives.run_narrative_sector_e2e_974(seed=narrative_seed)
    assert e2e["all_passed"] is True


# --- #978 Native SQL Workspace ---


def test_978_status(sql_seed):
    status = sql_ws.native_sql_workspace_status_978(seed=sql_seed)
    assert status["standalone_rejected"] is True
    assert status["sandbox_read_only"] is True
    assert status["audit_retention_days"] == 90


def test_978_injection_test(sql_seed):
    result = sql_ws.run_sql_injection_test_978(seed=sql_seed)
    assert result["ok"] is True
    assert result["parameterized_only"] is True


def test_978_data_leak_test(sql_seed):
    result = sql_ws.run_data_leak_test_978(seed=sql_seed)
    assert result["data_leak_prevented"] is True


def test_978_free_tier_denied(sql_seed):
    denied = sql_ws.execute_workspace_query(
        user_id="user_free",
        tenant_id="tenant_alpha",
        tier="free",
        formula="volume_usd > 0",
        seed=sql_seed,
    )
    assert denied.get("error") == "free_tier_no_sql_access"


def test_978_e2e(sql_seed):
    e2e = sql_ws.run_native_sql_workspace_e2e(seed=sql_seed)
    assert e2e["all_passed"] is True


# --- #979 Pattern Recognition ---


def test_979_status(pattern_seed):
    status = patterns.pattern_recognition_status_979(seed=pattern_seed)
    assert status["standalone_rejected"] is True
    assert status["rule_based_only"] is True
    assert status["invalidation_required"] is True


def test_979_pattern_detection(pattern_seed):
    detected = patterns.detect_patterns_979("BTC", seed=pattern_seed)
    assert detected["pattern_count"] >= 1
    assert all(p["no_intra_candle"] for p in detected["patterns"])
    assert all(p["supplementary_evidence_only"] for p in detected["patterns"])


def test_979_precision_report(pattern_seed):
    report = patterns.get_pattern_precision_report_979("rsi_divergence", seed=pattern_seed)
    assert report["precision_reported"] is True
    assert report["out_of_sample"]["included_in_training"] is False


def test_979_e2e(pattern_seed):
    e2e = patterns.run_pattern_recognition_e2e_979(seed=pattern_seed)
    assert e2e["all_passed"] is True


# --- #980 Point-in-Time Immutable Metrics ---


def test_980_pit_query(hist_seed):
    pit1 = hist.query_pit_metric_980("btc_price_daily", seed=hist_seed)
    pit2 = hist.query_pit_metric_980("btc_price_daily", pit_version=pit1["pit_version"], seed=hist_seed)
    assert pit1["immutable"] is True
    assert pit1["checksum_valid"] is True
    assert pit1["no_retroactive_mutation"] is True
    assert pit1["query_checksum"] == pit2["query_checksum"]


def test_980_pit_snapshots(hist_seed):
    listing = hist.list_pit_snapshots_980("btc_price_daily", seed=hist_seed)
    assert listing["count"] >= 1
    assert listing["checksum_version_audit"] is True


def test_980_pit_in_historical_e2e(hist_seed):
    e2e = hist.run_historical_layer_e2e_967(seed=hist_seed)
    assert e2e["all_passed"] is True
    assert 980 in e2e["feature_refs"]


# --- #981 Profitability Analyzer ---


def test_981_status(pnl_seed):
    status = pnl.profitability_analyzer_status_981(seed=pnl_seed)
    assert status["standalone_rejected"] is True
    assert status["decimal_precision"] == 8
    assert status["methodology_versioned"] is True


def test_981_pnl_dashboard(pnl_seed):
    dash = pnl.build_pnl_dashboard_981("demo_portfolio", seed=pnl_seed)
    assert dash["fee_completeness"] is True
    assert dash["decimal_precision"] == 8
    assert dash["reconciliation"]["passed"] is True


def test_981_export(pnl_seed):
    export = pnl.export_pnl_report_981("demo_portfolio", seed=pnl_seed)
    assert export["downloadable"] is True
    assert export["methodology_versioned"] is True


def test_981_e2e(pnl_seed):
    e2e = pnl.run_profitability_analyzer_e2e_981(seed=pnl_seed)
    assert e2e["all_passed"] is True


# --- Regression batch 33 ---


def test_batch33_historical_e2e_regression(hist_seed):
    e2e = hist.run_historical_layer_e2e_967(seed=hist_seed)
    assert e2e["all_passed"] is True
