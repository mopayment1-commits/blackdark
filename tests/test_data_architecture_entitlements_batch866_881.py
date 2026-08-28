"""Tests — #866 RBAC Entitlements + #878 Data Architecture + #879 Market Data + #881 Storage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import api_gateway_rbac_entitlements as rbac
from bd_platform import data_engine_architecture as arch
from bd_platform import data_engine_market_data_ingestion as mdi


@pytest.fixture
def gw_seed() -> dict:
    return json.loads(Path("data/api_gateway_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def arch_seed() -> dict:
    return json.loads(Path("data/data_engine_architecture_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def mdi_seed() -> dict:
    return json.loads(Path("data/market_data_ingestion_seed.json").read_text(encoding="utf-8"))


# --- #866 ---


def test_866_status(gw_seed):
    status = rbac.rbac_entitlements_status_866(seed=gw_seed)
    assert status["standalone_rejected"] is True
    assert status["api_gateway_ref"] == 876
    assert status["roles"] == ["free", "pro", "institution"]
    assert status["least_privilege"] is True
    assert status["audit_trail_required"] is True
    assert status["quota_enforcement_backend"] is True


def test_866_least_privilege(gw_seed):
    free = rbac.get_role_dataset_entitlements_866("free", seed=gw_seed)
    inst = rbac.get_role_dataset_entitlements_866("institution", seed=gw_seed)
    assert len(inst["premium_datasets"]) > len(free["premium_datasets"])
    assert rbac.check_dataset_access_866("free", "premium_derivatives", seed=gw_seed)["allowed"] is False
    assert rbac.check_dataset_access_866("institution", "premium_derivatives", seed=gw_seed)["allowed"] is True


def test_866_audit_trail(gw_seed):
    audit = rbac.get_audit_trail_866(seed=gw_seed)
    assert audit["ok"] is True
    assert audit["audit_trail_required"] is True
    assert all("user_id" in e and "endpoint" in e for e in audit["entries"])


def test_866_quota_backend(gw_seed):
    from bd_platform.api_gateway import reset_quota_for_tests

    reset_quota_for_tests()
    result = rbac.enforce_quota_backend_866("user_free_001", "free", seed=gw_seed)
    assert result["enforced_backend"] is True
    assert result["no_client_side"] is True


def test_866_security_tests(gw_seed):
    from bd_platform.api_gateway import reset_quota_for_tests

    reset_quota_for_tests()
    security = rbac.run_security_tests_866(seed=gw_seed)
    assert security["all_passed"] is True


def test_866_dashboard(gw_seed):
    from bd_platform.api_gateway import reset_quota_for_tests

    reset_quota_for_tests()
    dashboard = rbac.build_enterprise_access_dashboard_866(seed=gw_seed)
    assert dashboard["least_privilege"] is True
    assert dashboard["quota_enforcement_backend"] is True


def test_866_e2e(gw_seed):
    from bd_platform.api_gateway import reset_quota_for_tests

    reset_quota_for_tests()
    e2e = rbac.run_rbac_entitlements_e2e_866(seed=gw_seed)
    assert e2e["all_passed"] is True


# --- #878 + #881 ---


def test_878_status(arch_seed):
    status = arch.data_architecture_status_878(seed=arch_seed)
    assert status["standalone_rejected"] is True
    assert status["no_institutional_branding"] is True
    assert status["missing_not_zero"] is True


def test_878_null_handling():
    null = arch.handle_null_value_878(None)
    assert null["display"] == "N/A"
    assert null["implicit_zero_rejected"] is True


def test_878_deduplication():
    seen: set[str] = set()
    first = arch.check_deduplication_878("msg-abc", seen_ids=seen)
    second = arch.check_deduplication_878("msg-abc", seen_ids=seen)
    assert first["ok"] is True
    assert second["duplicate"] is True


def test_878_lineage(arch_seed):
    rec = arch.build_lineage_record_878("dp-1", source="binance", transformation="normalize", storage="timescaledb", seed=arch_seed)
    assert rec["provenance_tracked"] is True
    assert rec["evidence_layer_ref"] == 777


def test_881_storage_tiers(arch_seed):
    storage = arch.multi_tier_storage_status_881(seed=arch_seed)
    assert storage["tiers"]["hot"]["engine"] == "TimescaleDB"
    assert storage["tiers"]["warm"]["engine"] == "ClickHouse"
    assert storage["tiers"]["cold"]["retention_years_min"] >= 2


def test_881_query_routing(arch_seed):
    hot = arch.route_query_to_tier_881(10, seed=arch_seed)
    warm = arch.route_query_to_tier_881(100, seed=arch_seed)
    cold = arch.route_query_to_tier_881(500, seed=arch_seed)
    assert hot["tier"] == "hot"
    assert warm["tier"] == "warm"
    assert cold["tier"] == "cold"


def test_878_backup_restore(arch_seed):
    backup = arch.run_backup_restore_test_878(seed=arch_seed)
    assert backup["ok"] is True
    assert backup["daily_backup"] is True


def test_878_capacity(arch_seed):
    capacity = arch.run_capacity_evidence_test_878(seed=arch_seed)
    assert capacity["ok"] is True
    assert capacity["peak_multiplier"] == 10


def test_878_replay(arch_seed):
    replay = arch.run_replay_idempotency_test_878(seed=arch_seed)
    assert replay["deterministic"] is True


def test_878_e2e(arch_seed):
    e2e = arch.run_data_architecture_e2e_878(seed=arch_seed)
    assert e2e["all_passed"] is True


# --- #879 ---


def test_879_status(mdi_seed):
    status = mdi.market_data_ingestion_status_879(seed=mdi_seed)
    assert status["standalone_rejected"] is True
    assert status["venue_count"] == 10
    assert status["spot_first"] is True
    assert status["transport"] == "rest_polling"


def test_879_normalize():
    tick = mdi.normalize_tick_879({"symbol": "btc", "price": 64800, "volume": 100}, "Binance")
    assert tick["symbol"] == "BTC"
    assert tick["source"] == "Binance"
    assert tick["normalized"] is True


def test_879_fetch_tick(mdi_seed):
    tick = mdi.fetch_venue_tick_879("Binance", "BTC", seed=mdi_seed)
    assert tick["ok"] is True
    assert "price" in tick["tick"]


def test_879_latency_gap_qa(mdi_seed):
    qa = mdi.run_latency_gap_qa_879("BTC", seed=mdi_seed)
    assert qa["ok"] is True
    assert qa["gap_threshold_sec"] == 30


def test_879_feed_panel(mdi_seed):
    panel = mdi.build_market_data_feed_panel_879("BTC", seed=mdi_seed)
    assert panel["ok"] is True
    assert panel["venue_count"] == 10


def test_879_e2e(mdi_seed):
    e2e = mdi.run_market_data_ingestion_e2e_879(seed=mdi_seed)
    assert e2e["all_passed"] is True
