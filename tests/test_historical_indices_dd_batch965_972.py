"""Tests — Batch 33: #965-968 Historical Layer, #970 Indices, #971 Token DD, #972 Wallet DD."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import data_engine_historical_layer as hist
from bd_platform import intelligence_ledger_token_due_diligence as token_dd
from bd_platform import market_radar_indices as indices
from bd_platform import onchain_intelligence_extension as onchain


@pytest.fixture
def hist_seed() -> dict:
    return json.loads(Path("data/data_engine_historical_layer_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def indices_seed() -> dict:
    return json.loads(Path("data/market_radar_indices_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def token_dd_seed() -> dict:
    return json.loads(Path("data/intelligence_ledger_token_due_diligence_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def onchain_seed() -> dict:
    return json.loads(Path("data/onchain_intelligence_extension_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_state():
    hist.reset_historical_layer_state()
    yield
    hist.reset_historical_layer_state()


# --- #967 Historical Layer ---


def test_967_status_master(hist_seed):
    status = hist.historical_layer_status_967(seed=hist_seed)
    assert status["standalone_rejected"] is True
    assert 965 in status["merged_refs"].values()
    assert 966 in status["merged_refs"].values()
    assert 968 in status["merged_refs"].values()
    assert status["immutable_storage"] is True
    assert status["reproducible_queries"] is True


def test_965_archive_checksum(hist_seed):
    snap = hist.get_archive_snapshot_965("snap_btc_ticks_20260827", seed=hist_seed)
    assert snap["checksum_valid"] is True
    assert snap["immutable"] is True
    assert snap["reproducible"] is True


def test_965_archive_list(hist_seed):
    listing = hist.list_archive_snapshots_965(seed=hist_seed)
    assert listing["count"] >= 3
    assert listing["checksums_reproducibility"] is True


def test_966_derivatives_reproducible(hist_seed):
    q1 = hist.query_derivatives_history_966("BTC", "funding_rate", seed=hist_seed)
    q2 = hist.query_derivatives_history_966("BTC", "funding_rate", version=q1["version"], seed=hist_seed)
    assert q1["query_checksum"] == q2["query_checksum"]
    assert q1["no_silent_revisions"] is True


def test_966_derivatives_four_metrics(hist_seed):
    for metric in ("open_interest", "funding_rate", "liquidations", "options"):
        result = hist.query_derivatives_history_966("BTC", metric, seed=hist_seed)
        assert result["ok"] is True


def test_968_research_export(hist_seed):
    export = hist.export_research_dataset_968("btc_market_research", fmt="json", seed=hist_seed)
    assert export["reproducible"] is True
    assert export["row_count"] >= 3


def test_967_metric_reproducible(hist_seed):
    m1 = hist.query_historical_metric_967("btc_price_daily", seed=hist_seed)
    m2 = hist.query_historical_metric_967("btc_price_daily", version=m1["version"], seed=hist_seed)
    assert m1["query_checksum"] == m2["query_checksum"]
    assert m1["no_silent_historical_mutation"] is True


def test_967_revision_explicit(hist_seed):
    rev = hist.log_historical_revision_967("btc_price_daily", old_version="v1.0.0", new_version="v1.0.1", seed=hist_seed)
    assert rev["revisions_explicit"] is True
    assert rev["revision"]["original_immutable"] is True


def test_967_e2e(hist_seed):
    e2e = hist.run_historical_layer_e2e_967(seed=hist_seed)
    assert e2e["all_passed"] is True


# --- #970 Indices ---


def test_970_status(indices_seed):
    status = indices.indices_status_970(seed=indices_seed)
    assert status["standalone_rejected"] is True
    assert status["methodology_versioned"] is True
    assert status["rebalance_audit"] is True


def test_970_constituents(indices_seed):
    const = indices.get_index_constituents_970("bd_large_cap", seed=indices_seed)
    assert const["constituents_auditable"] is True
    assert abs(const["weights_sum_pct"] - 100) < 1


def test_970_rebalance_audit(indices_seed):
    rebal = indices.get_rebalance_history_970("bd_large_cap", seed=indices_seed)
    assert rebal["rebalance_audit"] is True
    assert rebal["rebalance_count"] >= 1


def test_970_backtest(indices_seed):
    bt = indices.run_index_backtest_970("bd_large_cap", seed=indices_seed)
    assert bt["no_hindsight_optimization"] is True
    assert bt["backtest_available"] is True


def test_970_e2e(indices_seed):
    e2e = indices.run_indices_e2e_970(seed=indices_seed)
    assert e2e["all_passed"] is True


# --- #971 Token DD ---


def test_971_status(token_dd_seed):
    status = token_dd.token_dd_status_971(seed=token_dd_seed)
    assert status["standalone_rejected"] is True
    assert len(status["sections"]) == 6
    assert status["no_zero_disguise"] is True


def test_971_full_report(token_dd_seed):
    report = token_dd.build_token_dd_report_971("aave", seed=token_dd_seed)
    assert report["ok"] is True
    assert report["risk_score_required"] is True
    assert report["freshness_per_section"] is True
    assert len(report["sections"]) == 6


def test_971_na_not_zero(token_dd_seed):
    report = token_dd.build_token_dd_report_971("new_token", seed=token_dd_seed)
    assert report["sections"]["liquidity"]["display"] == "N/A"
    assert report["sections"]["smart_money"]["display"] == "N/A"
    assert report["no_zero_disguise"] is True


def test_971_e2e(token_dd_seed):
    e2e = token_dd.run_token_dd_e2e_971(seed=token_dd_seed)
    assert e2e["all_passed"] is True


# --- #972 Wallet DD ---


def test_972_wallet_report(onchain_seed):
    report = onchain.build_wallet_dd_report_972("0x742d35cc6634c0532925a3b844bc9e7595f0bbe0", seed=onchain_seed)
    assert report["ok"] is True
    assert report["dimension_count"] == 5
    assert report["evidence_links_required"] is True
    assert report["non_custodial"] is True
    assert report["export_available"] is True


def test_972_red_flags(onchain_seed):
    report = onchain.build_wallet_dd_report_972("0x742d35cc6634c0532925a3b844bc9e7595f0bbe0", seed=onchain_seed)
    assert report["red_flag_count"] >= 1
    assert all(v in ("high", "medium", "low", "none") for v in report["confidence_levels"].values())


# --- Regression ---


def test_onchain_e2e_includes_972(onchain_seed):
    e2e = onchain.run_onchain_extension_e2e(seed=onchain_seed)
    assert e2e["all_passed"] is True
    assert 972 in e2e["feature_refs"]
