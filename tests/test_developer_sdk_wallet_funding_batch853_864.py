"""Tests — #853 Developer SDK + #854 Wallet Risk + #861 Funding Rates + #862 Uptime Shield + #864 PIT Integrity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import api_gateway_developer_sdk as sdk
from bd_platform import data_engine_quality_pipeline as qpipe
from bd_platform import infrastructure_observability_stack as ios
from bd_platform import intelligence_ledger_wallet_risk_monitor as wrm
from bd_platform import market_radar_funding_rates as fri


@pytest.fixture
def gw_seed() -> dict:
    return json.loads(Path("data/api_gateway_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def wrm_seed() -> dict:
    return json.loads(Path("data/wallet_risk_monitor_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def fri_seed() -> dict:
    return json.loads(Path("data/funding_rate_intelligence_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def ios_seed() -> dict:
    return json.loads(Path("data/infrastructure_observability_stack_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def qpipe_seed() -> dict:
    return json.loads(Path("data/data_engine_quality_pipeline_seed.json").read_text(encoding="utf-8"))


# --- #853 ---


def test_853_status(gw_seed):
    status = sdk.developer_sdk_status_853(seed=gw_seed)
    assert status["standalone_rejected"] is True
    assert status["api_gateway_ref"] == 876
    assert status["no_hidden_endpoints"] is True
    assert status["languages"]["typescript"]["priority"] == 1


def test_853_openapi_registry(gw_seed):
    reg = sdk.get_openapi_endpoint_registry_853(seed=gw_seed)
    assert reg["no_hidden_endpoints"] is True
    assert reg["openapi_coverage_pct"] == 100.0
    assert all(not ep.get("hidden") for ep in reg["endpoints"])


def test_853_contract_tests(gw_seed):
    contracts = sdk.run_contract_tests_853(seed=gw_seed)
    assert contracts["all_passed"] is True
    assert contracts["tolerance_pct"] == 0


def test_853_runnable_examples(gw_seed):
    examples = sdk.validate_runnable_examples_853(seed=gw_seed)
    assert examples["all_passed"] is True
    assert examples["no_broken_examples"] is True


def test_853_e2e(gw_seed):
    e2e = sdk.run_developer_sdk_e2e_853(seed=gw_seed)
    assert e2e["all_passed"] is True


# --- #854 ---


def test_854_status(wrm_seed):
    status = wrm.wallet_risk_monitor_status_854(seed=wrm_seed)
    assert status["standalone_rejected"] is True
    assert status["manual_review_required"] is True
    assert "Rug Pull" in status["banned_labels"]
    assert status["ml_rejected"] is True


def test_854_material_transfer(wrm_seed):
    transfers = wrm_seed["transfers"]["ARB"]
    material = wrm.evaluate_transfer_854(transfers[0], seed=wrm_seed)
    assert material["material"] is True
    assert material["label"] == "Transfer to Exchange"
    assert material["no_accusation"] is True
    assert material["auto_publish"] is False


def test_854_internal_move(wrm_seed):
    transfers = wrm_seed["transfers"]["ARB"]
    internal = wrm.evaluate_transfer_854(transfers[1], seed=wrm_seed)
    assert internal["material"] is True
    assert internal["label"] == "Internal Move"


def test_854_below_threshold(wrm_seed):
    transfers = wrm_seed["transfers"]["ARB"]
    small = wrm.evaluate_transfer_854(transfers[2], seed=wrm_seed)
    assert small["material"] is False


def test_854_unlock_context(wrm_seed):
    transfers = wrm_seed["transfers"]["ARB"]
    ev = wrm.evaluate_transfer_854(transfers[0], seed=wrm_seed)
    assert ev["unlock_context"]["post_unlock_movement"] is True
    assert ev["unlock_context"]["context_flag"] == "Post-Unlock Movement"


def test_854_panel(wrm_seed):
    panel = wrm.build_wallet_risk_panel_854("ARB", seed=wrm_seed)
    assert panel["ok"] is True
    assert panel["panel_title_ar"] == "مراقبة المحافظ"
    assert panel["badge_color"] in ("yellow", "red")


def test_854_e2e(wrm_seed):
    e2e = wrm.run_wallet_risk_e2e_854(seed=wrm_seed)
    assert e2e["all_passed"] is True


# --- #861 ---


def test_861_status(fri_seed):
    status = fri.funding_rate_intelligence_status_861(seed=fri_seed)
    assert status["standalone_rejected"] is True
    assert status["venues"] == ["Binance", "Bybit", "OKX", "dYdX"]
    assert status["null_not_zero"] is True


def test_861_apr_normalization():
    apr = fri.normalize_funding_apr_861(0.0001, 8)
    assert apr is not None
    assert apr > 0


def test_861_panel(fri_seed):
    panel = fri.build_funding_rates_panel_861("BTC", seed=fri_seed)
    assert panel["ok"] is True
    assert "OI-Weighted" in panel["formatted_output"]
    assert panel["settlement_intervals_verified"] is True


def test_861_null_not_zero(fri_seed):
    panel = fri.build_funding_rates_panel_861("BTC", seed=fri_seed)
    for v in panel["venues"]:
        if v.get("excluded"):
            assert v["apr_pct"] == "N/A"


def test_861_divergence():
    div = fri.detect_divergence_861([10.0, 70.0])
    assert div["high_divergence"] is True
    assert div["divergence_level"] == "High Divergence"


def test_861_e2e(fri_seed):
    e2e = fri.run_funding_rates_e2e_861(seed=fri_seed)
    assert e2e["all_passed"] is True


# --- #862 ---


def test_862_uptime_shield(ios_seed):
    shield = ios.build_uptime_slo_shield_862(seed=ios_seed)
    assert shield["standalone_rejected"] is True
    assert shield["slos"]["availability_target_pct"] == 99.9
    assert shield["synthetic_checks"]["interval_sec"] == 60


def test_862_slo_tests(ios_seed):
    tests = ios.run_uptime_slo_tests_862(seed=ios_seed)
    assert tests["all_passed"] is True


def test_862_integrated_stack(ios_seed):
    stack = ios.build_sre_observability_with_quality_monitor_789(seed=ios_seed)
    assert "uptime_shield_862" in stack
    assert stack.get("uptime_slo_compliant") is True


def test_862_e2e(ios_seed):
    e2e = ios.run_uptime_shield_e2e_862(seed=ios_seed)
    assert e2e["all_passed"] is True


# --- #864 ---


def test_864_status(qpipe_seed):
    status = qpipe.pit_integrity_status_864(seed=qpipe_seed)
    assert status["backtesting_branding_rejected"] is True
    assert status["component"] == "pit_integrity"
    assert status["timezone"] == "UTC"


def test_864_future_leakage_blocked():
    result = qpipe.check_no_future_leakage_864(
        "2026-08-28T00:00:00+00:00",
        "2026-08-27T00:00:00+00:00",
    )
    assert result["future_leakage"] is True
    assert result["action"] == "blocked"


def test_864_availability_timestamp(qpipe_seed):
    metric = qpipe_seed["pit_integrity_864"]["sample_metrics"][0]
    ts = qpipe_seed["pit_integrity_864"]["default_query_timestamp"]
    result = qpipe.check_availability_timestamp_864(metric, ts)
    assert result["ok"] is True


def test_864_deterministic_replay(qpipe_seed):
    replay = qpipe.run_deterministic_replay_test_864("btc-ohlcv-daily", seed=qpipe_seed)
    assert replay["deterministic"] is True


def test_864_panel(qpipe_seed):
    panel = qpipe.build_pit_integrity_panel_864(seed=qpipe_seed)
    assert panel["ok"] is True
    assert panel["backtesting_branding_rejected"] is True


def test_864_e2e(qpipe_seed):
    e2e = qpipe.run_pit_integrity_e2e_864(seed=qpipe_seed)
    assert e2e["all_passed"] is True
