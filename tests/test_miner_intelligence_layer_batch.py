"""Tests — Miner Intelligence Layer epic #566 #567 #568."""

from __future__ import annotations

import json

import pytest

from bd_platform import miner_intelligence_layer as mil


@pytest.fixture
def miner_seed(tmp_path, monkeypatch):
    p = tmp_path / "miner_intelligence_layer_seed.json"
    p.write_text(json.dumps({
        "mpi_baseline": {
            "version": "1.0",
            "window_days": 365,
            "outlier_handling": "iqr_trim",
            "iqr_multiplier": 1.5,
        },
        "miner_clusters": {
            "miner_test_pool": {
                "addresses": ["0xminer_hot_001", "0xminer_cold_001"],
            },
        },
        "exchange_clusters": {
            "binance": {
                "addresses": ["0x28c6c06298d514db089934071355e5743bf21d60"],
            },
        },
        "miners": {
            "miner_test_pool": {
                "miner_id": "miner_test_pool",
                "entity_id": "entity_miner_test",
                "name": "Test Pool",
                "pool": "Test Pool",
                "asset": "BTC",
                "labels": {
                    "label": "Test Miner Pool",
                    "confidence": "high",
                    "source": "test_labels_registry",
                    "version": "1.0",
                    "freshness_seconds": 300,
                },
                "pool_reclassification": {
                    "previous_pool": "Old Pool Name",
                    "current_pool": "Test Pool",
                    "date": "2025-01-01",
                    "historical_continuity_preserved": True,
                },
                "balances": {"total_btc": 500.0, "previous_total_btc": 520.0},
                "flow_baseline": {"mean_outflow_usd": 5000000.0, "std_outflow_usd": 1000000.0},
                "market_context": {"price_usd": 95000.0, "issuance_btc_daily": 450.0},
                "provenance": {
                    "source": "test_indexer",
                    "as_of": "2026-08-26T13:00:00Z",
                    "freshness_seconds": 300,
                },
                "historical_outflows": [
                    {"date": "2026-01-01", "outflow_btc": 50.0},
                    {"date": "2026-02-01", "outflow_btc": 55.0},
                    {"date": "2026-03-01", "outflow_btc": 60.0},
                    {"date": "2026-04-01", "outflow_btc": 52.0},
                    {"date": "2026-05-01", "outflow_btc": 58.0},
                    {"date": "2026-06-01", "outflow_btc": 200.0},
                    {"date": "2026-07-01", "outflow_btc": 54.0},
                    {"date": "2026-08-01", "outflow_btc": 56.0},
                    {"date": "2026-08-25", "outflow_btc": 120.0},
                ],
            },
        },
        "transfers": [
            {
                "transfer_id": "t-001",
                "miner_id": "miner_test_pool",
                "asset": "BTC",
                "direction": "outflow",
                "quantity": 30.0,
                "value_usd": 2850000.0,
                "from_address": "0xminer_hot_001",
                "to_address": "0x28c6c06298d514db089934071355e5743bf21d60",
            },
            {
                "transfer_id": "t-002",
                "miner_id": "miner_test_pool",
                "asset": "BTC",
                "direction": "internal",
                "quantity": 10.0,
                "value_usd": 950000.0,
                "from_address": "0xminer_hot_001",
                "to_address": "0xminer_cold_001",
            },
            {
                "transfer_id": "t-003",
                "miner_id": "miner_test_pool",
                "asset": "BTC",
                "direction": "inflow",
                "quantity": 50.0,
                "value_usd": 4750000.0,
                "from_address": "0xexternal_reward",
                "to_address": "0xminer_hot_001",
            },
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(mil, "_SEED_PATH", p)
    return p


def test_epic_status_merged_not_standalone(miner_seed):
    status = mil.miner_intelligence_layer_status()
    assert status["standalone_rejected"] is True
    assert status["tasks_not_tickets"] is True
    assert set(status["feature_ids"]) == {566, 567, 568}
    assert status["dependencies"]["entity_resolution_feature_id"] == 541


def test_miner_labels_confidence(miner_seed):
    flow = mil.build_miner_flow_intelligence("miner_test_pool")
    assert flow["ok"] is True
    assert flow["label"]["confidence"] == "high"
    assert flow["label"]["miner_labels_confidence"] is True


def test_pool_reclassification_handling(miner_seed):
    flow = mil.build_miner_flow_intelligence("miner_test_pool")
    reclass = flow["pool_reclassification"]
    assert reclass["pool_reclassification_handling"] is True
    assert reclass["previous_pool"] == "Old Pool Name"


def test_miner_to_exchange_flow_observed_not_selling_pressure(miner_seed):
    flow = mil.build_miner_flow_intelligence("miner_test_pool")
    mte = flow["miner_to_exchange_flow_observed"]
    assert mte["indicator_name"] == "Miner-to-Exchange Flow Observed"
    assert mte["not_selling_pressure"] is True
    assert mte["no_direct_sell_claim"] is True
    assert mte["flow_usd"] == 2850000.0


def test_internal_transfer_filtering(miner_seed):
    flow = mil.build_miner_flow_intelligence("miner_test_pool")
    assert flow["transfer_filter"]["internal_filtered_count"] == 1
    assert flow["transfer_filter"]["internal_transfer_filtering"] is True


def test_miner_flow_monitor_baseline_deviation(miner_seed):
    monitor = mil.build_miner_flow_monitor("miner_test_pool")
    assert monitor["ok"] is True
    assert monitor["baseline_deviation"]["historical_validation"] is True
    assert monitor["label_provenance"]["provenance_documented"] is True


def test_mpi_percentile_descriptive_only(miner_seed):
    mpi_panel = mil.build_miners_position_index("miner_test_pool")
    assert mpi_panel["ok"] is True
    mpi = mpi_panel["mpi"]
    assert mpi["not_a_sell_signal"] is True
    assert mpi["no_anomaly_equals_sell"] is True
    assert 0 <= mpi["percentile"] <= 100
    assert "percentile" in mpi["display"]


def test_mpi_baseline_documented(miner_seed):
    config = mil.build_mpi_baseline_config()
    assert config["baseline_window_documented"] is True
    assert config["robust_to_outliers"] is True
    assert config["window_days"] == 365


def test_mpi_outlier_robustness(miner_seed):
    historical = [50.0, 55.0, 60.0, 52.0, 58.0, 200.0, 54.0, 56.0]
    mpi = mil.compute_mpi(120.0, historical)
    assert mpi["outliers_trimmed"] >= 0
    assert mpi["descriptive_only"] is True


def test_mpi_historical_replay(miner_seed):
    mpi_panel = mil.build_miners_position_index("miner_test_pool")
    assert len(mpi_panel["historical_replay"]) > 0
    for entry in mpi_panel["historical_replay"]:
        assert "percentile" in entry
        assert "state" in entry


def test_main_panel(miner_seed):
    panel = mil.build_miner_intelligence_panel(miner_id="miner_test_pool")
    assert panel["ok"] is True
    assert panel["epic_feature_id"] == 566
    assert "566_miner_flow_intelligence" in panel["sub_modules"]
    assert "567_miner_flow_monitor" in panel["sub_modules"]
    assert "568_miners_position_index" in panel["sub_modules"]
    assert "selling pressure" in panel["banned_output_terms"]


def test_reconciliation_tests(miner_seed):
    result = mil.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["all_passed"] is True
    assert result["test_count"] >= 10


def test_classify_internal_transfer(miner_seed):
    transfer = {
        "from_address": "0xminer_hot_001",
        "to_address": "0xminer_cold_001",
        "direction": "internal",
        "value_usd": 950000.0,
    }
    classified = mil.classify_miner_transfer(
        transfer,
        miner_clusters={"miner_test_pool": {"addresses": ["0xminer_hot_001", "0xminer_cold_001"]}},
        exchange_clusters={},
    )
    assert classified["is_internal"] is True
    assert classified["included_in_adjusted"] is False


def test_classify_miner_to_exchange(miner_seed):
    transfer = {
        "from_address": "0xminer_hot_001",
        "to_address": "0x28c6c06298d514db089934071355e5743bf21d60",
        "direction": "outflow",
        "value_usd": 2850000.0,
    }
    classified = mil.classify_miner_transfer(
        transfer,
        miner_clusters={"miner_test_pool": {"addresses": ["0xminer_hot_001"]}},
        exchange_clusters={"binance": {"addresses": ["0x28c6c06298d514db089934071355e5743bf21d60"]}},
    )
    assert classified["is_miner_to_exchange"] is True
    assert classified["no_direct_sell_claim"] is True
