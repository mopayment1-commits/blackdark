"""Tests — #413 Oracle VWAP + #414 System Performance Monitor + #415 Fill Feasibility."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import fill_feasibility_simulator as ffs
from bd_platform import oracle_vwap_layer as ovl
from bd_platform import system_performance_monitor as spm


@pytest.fixture
def vwap_seed(tmp_path, monkeypatch):
    main = Path("data/oracle_vwap_seed.json")
    p = tmp_path / "oracle_vwap_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ovl, "_SEED_PATH", p)
    return p


@pytest.fixture
def spm_seed(tmp_path, monkeypatch):
    main = Path("data/system_performance_monitor_seed.json")
    p = tmp_path / "system_performance_monitor_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(spm, "_SEED_PATH", p)
    return p


@pytest.fixture
def ffs_seed(tmp_path, monkeypatch):
    main = Path("data/fill_feasibility_seed.json")
    p = tmp_path / "fill_feasibility_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ffs, "_SEED_PATH", p)
    return p


# --- #413 ---


def test_413_status_oracle_layer(vwap_seed):
    status = ovl.oracle_vwap_status()
    assert status["feature_id"] == 413
    assert status["standalone"] is False
    assert status["oracle_api_layer"] is True
    assert status["constituent_source_metadata"] is True


def test_413_fair_value_index(vwap_seed):
    fvi = ovl.build_fair_value_index("BTC")
    assert fvi["ok"] is True
    assert fvi["fair_value_index"] > 0
    assert fvi["each_price_has_source"] is True
    assert len(fvi["vwap"]["constituents"]) == 12


def test_413_constituent_source_metadata(vwap_seed):
    fvi = ovl.build_fair_value_index("ETH")
    for c in fvi["vwap"]["constituents"]:
        assert c.get("source")
        assert c.get("venue")
        assert "deviation_pct" in c


def test_413_market_radar_integration(vwap_seed):
    ctx = ovl.build_market_radar_vwap_context("BTC")
    assert ctx["ok"] is True
    assert len(ctx["venue_deviations"]) >= 10


def test_413_arbitrage_vwap_benchmark(vwap_seed):
    bench = ovl.build_arbitrage_vwap_benchmark("BTC")
    assert bench["benchmark_type"] == "vwap_fair_value"
    assert bench["not_best_bid_ask"] is True


def test_413_breakeven_integration(vwap_seed):
    ref = ovl.build_breakeven_vwap_price("BTC")
    assert ref["use_for_breakeven"] is True
    assert ref["vwap_reference_price"] > 0


def test_413_reconciliation(vwap_seed):
    result = ovl.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["passed"] == result["total"]


# --- #414 ---


def test_414_status_internal_admin(spm_seed):
    status = spm.system_performance_monitor_status()
    assert status["feature_id"] == 414
    assert status["standalone"] is False
    assert status["internal_admin_only"] is True
    assert status["not_user_facing"] is True
    assert status["renamed_from"] == "Execution_Latency_Monitor"


def test_414_percentiles(spm_seed):
    panel = spm.build_performance_panel()
    latency = panel["systems"]["oracle_api"]["latency"]
    assert "p50_ms" in latency
    assert "p95_ms" in latency
    assert "p99_ms" in latency


def test_414_stage_attribution(spm_seed):
    panel = spm.build_performance_panel()
    attr = panel["systems"]["oracle_api"]["stage_attribution"]
    assert attr.get("bottleneck_stage") is not None


def test_414_trace_ids_clock_sync(spm_seed):
    panel = spm.build_performance_panel()
    assert panel["principles"]["clock_sync"] is True
    assert panel["principles"]["trace_ids"] is True
    assert panel["principles"]["no_averaged_away_tail_latency"] is True


def test_414_load_evidence(spm_seed):
    panel = spm.build_performance_panel()
    assert panel["load_evidence"]["passed"] is True


def test_414_reconciliation(spm_seed):
    result = spm.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["passed"] == result["total"]


# --- #415 ---


def test_415_status_simulation_only(ffs_seed):
    status = ffs.fill_feasibility_simulator_status()
    assert status["feature_id"] == 415
    assert status["standalone"] is False
    assert status["simulation_only"] is True
    assert status["legal_name"] == "Liquidity Depth Analyzer"


def test_415_deterministic_book_replay(ffs_seed):
    sim = ffs.simulate_fill(symbol="BTC/USDT", venue="binance", side="buy", size=5.0)
    assert sim["ok"] is True
    assert sim["weighted_fill_price"] > 0
    assert sim["verdict"] == "full_fill"


def test_415_stale_depth_rejected(ffs_seed):
    sim = ffs.simulate_fill(symbol="BTC/USDT", venue="okx", side="buy", size=1.0)
    assert sim["reason"] == "stale_depth_rejected"
    assert sim["verdict"] == "not_fillable"


def test_415_missing_depth_never_executable(ffs_seed):
    sim = ffs.simulate_fill(symbol="BTC/USDT", venue="nonexistent", side="buy", size=1.0)
    assert sim["reason"] == "missing_depth_never_executable"


def test_415_partial_fill(ffs_seed):
    sim = ffs.simulate_fill(symbol="BTC/USDT", venue="binance", side="buy", size=1000.0)
    assert sim["verdict"] in {"partial_fill", "not_fillable"}
    assert sim["residual_size"] > 0


def test_415_liquidity_score(ffs_seed):
    score = ffs.liquidity_score_for_venue("BTC/USDT", "binance")
    assert 0 <= score["liquidity_score"] <= 100


def test_415_arbitrage_volume_feasibility(ffs_seed):
    panel = ffs.build_arbitrage_feasibility_panel("BTC/USDT", size=1.0)
    assert panel["count"] >= 1
    assert "volume_feasibility" in panel["opportunities"][0]


def test_415_market_radar_heatmap(ffs_seed):
    panel = ffs.build_market_radar_panel("BTC/USDT")
    assert panel["ok"] is True
    assert len(panel["liquidity_heatmap"]["venues"]) >= 2


def test_415_reconciliation(ffs_seed):
    result = ffs.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["passed"] == result["total"]
