"""Tests — #839 CoinGecko Terminal + #843 Coverage Registry + #849 Data Health + #850 Quality Pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import coverage_metadata_registry as cmr
from bd_platform import data_engine_quality_pipeline as qpipe
from bd_platform import data_health_monitor as dhm
from bd_platform import infrastructure_observability_stack as ios
from bd_platform import oracle_coingecko_terminal_source as cg


@pytest.fixture
def cg_seed() -> dict:
    return json.loads(Path("data/oracle_coingecko_terminal_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def cmr_seed() -> dict:
    return json.loads(Path("data/coverage_metadata_registry_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def dhm_seed() -> dict:
    return json.loads(Path("data/data_health_monitor_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def qpipe_seed() -> dict:
    return json.loads(Path("data/data_engine_quality_pipeline_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def ios_seed() -> dict:
    return json.loads(Path("data/infrastructure_observability_stack_seed.json").read_text(encoding="utf-8"))


# --- #839 ---


def test_839_status(cg_seed):
    status = cg.coingecko_terminal_status_839(seed=cg_seed)
    assert status["standalone_rejected"] is True
    assert status["component"] == "coingecko_terminal_source"
    assert status["data_categories"] == ["dex_volume", "liquidity", "pool_data"]


def test_839_three_categories(cg_seed):
    cg._CACHE.clear()
    for cat in ("dex_volume", "liquidity", "pool_data"):
        result = cg.fetch_coingecko_terminal_data_839(cat, "ETH", seed=cg_seed)
        assert result["ok"] is True
        assert result["within_response_target"] is True


def test_839_cache_and_fallback(cg_seed):
    cg._CACHE.clear()
    first = cg.fetch_coingecko_terminal_data_839("dex_volume", "ETH", seed=cg_seed)
    second = cg.fetch_coingecko_terminal_data_839("dex_volume", "ETH", seed=cg_seed)
    assert second["cache_hit"] is True
    fb = cg.fetch_coingecko_terminal_data_839("liquidity", "ETH", seed=cg_seed, force_primary_fail=True)
    assert fb["fallback_used"] is True


def test_839_market_radar(cg_seed):
    feed = cg.build_market_radar_dex_feed_839("ETH", seed=cg_seed)
    assert feed["ok"] is True
    assert feed["surface"] == "market_radar"


def test_839_e2e(cg_seed):
    cg._CACHE.clear()
    e2e = cg.run_coingecko_terminal_e2e_839(seed=cg_seed)
    assert e2e["all_passed"] is True


# --- #843 ---


def test_843_status(cmr_seed):
    status = cmr.coverage_metadata_status_843(seed=cmr_seed)
    assert status["standalone_rejected"] is True
    assert status["machine_readable"] is True
    assert status["admin_panel_ar"] == "التغطية"


def test_843_registry(cmr_seed):
    registry = cmr.build_coverage_registry_843(seed=cmr_seed)
    assert registry["generated_from_production"] is True
    assert registry["counts"]["apis"] >= 1
    assert registry["counts"]["ui_routes"] >= 1
    assert len(registry["slas"]) >= 1


def test_843_parity_tests(cmr_seed):
    parity = cmr.run_coverage_parity_tests_843(seed=cmr_seed)
    assert parity["parity_tolerance_pct"] == 0
    assert parity["all_passed"] is True


def test_843_admin_view(cmr_seed):
    admin = cmr.build_admin_coverage_view_843(seed=cmr_seed)
    assert admin["panel_name_ar"] == "التغطية"


def test_843_e2e(cmr_seed):
    e2e = cmr.run_coverage_registry_e2e_843(seed=cmr_seed)
    assert e2e["all_passed"] is True


# --- #849 ---


def test_849_status(dhm_seed):
    status = dhm.data_health_monitor_status_849(seed=dhm_seed)
    assert status["standalone_rejected"] is True
    assert status["per_venue_slos_ms"]["oracle_api"] == 500
    assert status["per_venue_slos_ms"]["market_radar"] == 1000
    assert status["per_venue_slos_ms"]["on_chain"] == 3000


def test_849_venue_slos(dhm_seed):
    for venue in ("oracle_api", "market_radar", "on_chain"):
        ev = dhm.evaluate_venue_slo_849(venue, seed=dhm_seed)
        assert ev["within_slo"] is True


def test_849_infra_feed(dhm_seed):
    feed = dhm.build_infra_observability_health_feed_849(seed=dhm_seed)
    assert feed["feeds"] == "#789 Infrastructure Observability"


def test_849_stack_integration(ios_seed):
    stack = ios.build_sre_observability_with_quality_monitor_789(seed=ios_seed)
    assert "data_health_feed_849" in stack


def test_849_e2e(dhm_seed):
    e2e = dhm.run_data_health_e2e_849(seed=dhm_seed)
    assert e2e["all_passed"] is True


# --- #850 ---


def test_850_status(qpipe_seed):
    status = qpipe.quality_pipeline_status_850(seed=qpipe_seed)
    assert status["standalone_rejected"] is True
    assert status["component"] == "quality_pipeline"
    assert status["mandatory_tests"] == ["gap_detection", "outlier_detection", "reconciliation"]
    assert status["quality_monitor_ref"] == 824


def test_850_batch_qa(qpipe_seed):
    qa = qpipe.run_pipeline_batch_qa_850("batch-20260827", seed=qpipe_seed)
    assert qa["qa_status"] in ("Pass", "Warning")
    assert qa["tests_run"] == 3


def test_850_pipeline_stages(qpipe_seed):
    panel = qpipe.build_quality_pipeline_panel_850(seed=qpipe_seed)
    assert panel["pipeline_documented"] is True
    assert panel["no_hidden_steps"] is True
    assert "read" in panel["pipeline_stages"]


def test_850_e2e(qpipe_seed):
    e2e = qpipe.run_quality_pipeline_e2e_850(seed=qpipe_seed)
    assert e2e["all_passed"] is True


def test_batch_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/coverage/registry").status_code == 200
    assert c.get("/api/platform/coverage/registry/e2e").json()["all_passed"] is True

    assert c.get("/api/platform/intelligence-ledger/oracle/coingecko-terminal/status").status_code == 200
    e2e839 = c.get("/api/platform/intelligence-ledger/oracle/coingecko-terminal/e2e")
    assert e2e839.status_code == 200
    assert e2e839.json()["all_passed"] is True
