"""Tests — Exchange Intelligence Layer epic #544 #546 #547 #548 #549 #550 #551 #552 #553."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import exchange_intelligence_layer as eil


@pytest.fixture
def exchange_seed(tmp_path, monkeypatch):
    p = tmp_path / "exchange_intelligence_layer_seed.json"
    p.write_text(json.dumps({
        "exchanges": {
            "binance": {
                "exchange_id": "binance",
                "entity_id": "binance",
                "name": "Binance",
                "labels": {
                    "label": "Binance",
                    "confidence": "high",
                    "source": "entity_resolution_v1",
                    "version": "1.0",
                    "freshness_seconds": 300,
                },
            },
        },
        "exchange_clusters": {
            "binance": {
                "exchange_id": "binance",
                "addresses": ["0xbinance_hot", "0xbinance_cold"],
                "cluster_confidence": "high",
                "cluster_source": "entity_resolution_v1",
            },
        },
        "transfers": [
            {
                "transfer_id": "t1",
                "exchange_id": "binance",
                "asset": "BTC",
                "direction": "inflow",
                "value_usd": 1000000.0,
                "from_address": "0xexternal",
                "to_address": "0xbinance_hot",
            },
            {
                "transfer_id": "t2",
                "exchange_id": "binance",
                "asset": "BTC",
                "direction": "inflow",
                "value_usd": 500000.0,
                "from_address": "0xbinance_hot",
                "to_address": "0xbinance_cold",
            },
            {
                "transfer_id": "t3",
                "exchange_id": "binance",
                "asset": "BTC",
                "direction": "outflow",
                "value_usd": 300000.0,
                "from_address": "0xbinance_hot",
                "to_address": "0xexternal2",
            },
        ],
        "balances": {
            "binance": {
                "total_usd": 5000000000.0,
                "change_24h_pct": 0.1,
                "change_7d_pct": -0.5,
                "trend": "stable",
                "anomalies": [],
                "historical_revisions_controlled": True,
            },
        },
        "reserves": {
            "binance": {
                "total_usd": 5000000000.0,
                "change_24h_pct": 0.1,
                "change_7d_pct": -0.5,
                "trend": "stable",
                "by_asset": {"BTC": 5000000000.0},
                "anomaly_detected": False,
                "freshness_seconds": 300,
                "historical_replay_supported": True,
            },
        },
        "revisions": [
            {
                "revision_id": "rev-001",
                "effective_at": "2026-08-25T00:00:00Z",
                "reason": "cluster_relabel",
                "affected_exchanges": ["binance"],
            },
        ],
        "supply_balances": {
            "binance": {
                "total_balance_usd": 5000000000.0,
                "as_of": "2026-08-26T10:00:00Z",
                "snapshot_id": "snap-test-001",
                "methodology_version": "1.0",
                "historical_reproducibility": True,
                "by_asset": {
                    "BTC": {
                        "balance": 100000.0,
                        "total_supply": 20000000.0,
                        "cluster_version": "1.0",
                    },
                },
            },
        },
        "large_inflow_metric": {
            "version": "1.0",
            "top_n": 3,
            "rolling_window_days": 7,
            "historical_windows": [
                {
                    "window_start": "2026-08-19",
                    "window_end": "2026-08-25",
                    "inflows": [
                        {"direction": "inflow", "value_usd": 500000.0, "is_internal": False},
                        {"direction": "inflow", "value_usd": 300000.0, "is_internal": False},
                        {"direction": "inflow", "value_usd": 200000.0, "is_internal": False},
                    ],
                },
                {
                    "window_start": "2026-08-12",
                    "window_end": "2026-08-18",
                    "inflows": [
                        {"direction": "inflow", "value_usd": 400000.0, "is_internal": False},
                        {"direction": "inflow", "value_usd": 250000.0, "is_internal": False},
                    ],
                },
            ],
        },
    }), encoding="utf-8")
    monkeypatch.setattr(eil, "_SEED_PATH", p)
    return p


def test_epic_status_merged_not_standalone(exchange_seed):
    status = eil.exchange_intelligence_layer_status()
    assert status["standalone_rejected"] is True
    assert status["tasks_not_tickets"] is True
    assert set(status["feature_ids"]) == {544, 546, 547, 548, 549, 550, 551, 552, 553}
    assert status["dependencies"]["entity_resolution_feature_id"] == 541


def test_549_internal_flow_filter_no_silent_filtering(exchange_seed):
    seed = json.loads(exchange_seed.read_text(encoding="utf-8"))
    clusters = seed["exchange_clusters"]
    transfers = seed["transfers"]

    adjusted, meta = eil.filter_transfers(transfers, exchange_clusters=clusters, adjusted=True)
    raw, raw_meta = eil.filter_transfers(transfers, exchange_clusters=clusters, adjusted=False)

    assert meta["internal_filtered_count"] == 1
    assert meta["no_silent_filtering"] is True
    assert len(adjusted) == 2
    assert len(raw) == 3
    assert raw_meta["view"] == "raw"
    assert all(t.get("no_silent_filtering") for t in raw)


def test_547_netflow_formula_fixed(exchange_seed):
    seed = json.loads(exchange_seed.read_text(encoding="utf-8"))
    clusters = seed["exchange_clusters"]
    transfers, _ = eil.filter_transfers(
        seed["transfers"], exchange_clusters=clusters, adjusted=True,
    )

    netflow = eil.compute_netflow(transfers, exchange_id="binance")
    assert netflow["formula_fixed"] is True
    assert netflow["inflow_usd"] == 1000000.0
    assert netflow["outflow_usd"] == 300000.0
    assert netflow["netflow_usd"] == 700000.0
    assert "inflow" in netflow["formula"].lower()


def test_548_inflow_intelligence(exchange_seed):
    seed = json.loads(exchange_seed.read_text(encoding="utf-8"))
    clusters = seed["exchange_clusters"]
    transfers, _ = eil.filter_transfers(
        seed["transfers"], exchange_clusters=clusters, adjusted=True,
    )

    inflow = eil.build_inflow_intelligence(transfers, exchange_id="binance")
    assert inflow["internal_flows_filtered"] is True
    assert inflow["total_inflow_usd"] == 1000000.0
    assert inflow["by_asset"]["BTC"] == 1000000.0


def test_546_flow_intelligence(exchange_seed):
    seed = json.loads(exchange_seed.read_text(encoding="utf-8"))
    clusters = seed["exchange_clusters"]
    transfers, _ = eil.filter_transfers(
        seed["transfers"], exchange_clusters=clusters, adjusted=True,
    )

    flow = eil.build_flow_intelligence(transfers, exchange_id="binance")
    assert flow["labels_documented"] is True
    assert flow["internal_transfers_filtered"] is True
    assert flow["netflow"]["netflow_usd"] == 700000.0


def test_544_balance_netflow(exchange_seed):
    seed = json.loads(exchange_seed.read_text(encoding="utf-8"))
    clusters = seed["exchange_clusters"]
    transfers, _ = eil.filter_transfers(
        seed["transfers"], exchange_clusters=clusters, adjusted=True,
    )

    balance = eil.build_balance_netflow("binance", seed=seed, transfers=transfers)
    assert balance["balance_usd"] == 5000000000.0
    assert balance["historical_revisions_controlled"] is True
    assert balance["labels"]["entity_labels_documented"] is True


def test_550_reserve_intelligence(exchange_seed):
    seed = json.loads(exchange_seed.read_text(encoding="utf-8"))
    reserve = eil.build_reserve_intelligence("binance", seed=seed)

    assert reserve["total_reserve_usd"] == 5000000000.0
    assert reserve["freshness_visible"] is True
    assert reserve["internal_transfers_handled"] is True
    assert reserve["reconciliation_supported"] is True


def test_551_supply_balance_intelligence(exchange_seed):
    seed = json.loads(exchange_seed.read_text(encoding="utf-8"))
    supply = eil.build_supply_balance_intelligence("binance", seed=seed)

    assert supply["entity_adjusted"] is True
    assert supply["cluster_revisions_tracked"] is True
    assert supply["historical_reproducibility"] is True
    assert supply["extends_feature_id"] == 550
    assert supply["by_asset"]["BTC"]["share_of_supply_pct"] == 0.5
    assert supply["revision_count"] >= 1


def test_epic_panel_all_sub_modules(exchange_seed):
    panel = eil.build_exchange_intelligence_panel(exchange_id="binance")
    assert panel["ok"] is True
    assert panel["no_standalone_features"] is True
    assert "549_internal_flow_filter" in panel["sub_modules"]
    assert "547_netflow_formula" in panel["sub_modules"]
    assert "548_inflow_intelligence" in panel["sub_modules"]
    assert "546_flow_intelligence" in panel["sub_modules"]
    assert "544_balance_netflow" in panel["sub_modules"]
    assert "550_reserve_intelligence" in panel["sub_modules"]
    assert "551_supply_balance_intelligence" in panel["sub_modules"]
    assert "552_large_inflow_concentration_metric" in panel["sub_modules"]
    assert "553_exchange_to_exchange_flow" in panel["sub_modules"]
    assert panel["filter"]["no_silent_filtering"] is True
    assert "whale ratio" in panel["banned_output_terms"]


def test_552_large_inflow_concentration_metric(exchange_seed):
    seed = json.loads(exchange_seed.read_text(encoding="utf-8"))
    clusters = seed["exchange_clusters"]
    transfers, _ = eil.filter_transfers(
        seed["transfers"], exchange_clusters=clusters, adjusted=True,
    )
    licm = eil.build_large_inflow_concentration_metric(
        "binance", seed=seed, transfers=transfers,
    )
    assert licm["metric"]["metric_name"] == "Large-Inflow Concentration Metric"
    assert licm["metric"]["no_whale_in_ui"] is True
    assert licm["top_n_config"]["top_n_definition_documented"] is True
    assert licm["statistical_anomaly"]["not_a_sell_signal"] is True
    assert licm["historical_metric_validation"]["not_trading_backtest"] is True
    assert licm["metric"]["concentration_ratio"] == 1.0


def test_552_low_volume_edge_case(exchange_seed):
    metric = eil.compute_large_inflow_concentration(
        [{"direction": "inflow", "value_usd": 50000.0, "is_internal": False}],
        top_n=3,
        low_volume_threshold=100000.0,
    )
    assert metric["low_volume_edge_case"] is True
    assert metric["concentration_ratio"] is None


def test_553_exchange_to_exchange_flow(exchange_seed):
    seed = json.loads(exchange_seed.read_text(encoding="utf-8"))
    seed["exchange_clusters"]["okx"] = {
        "exchange_id": "okx",
        "addresses": ["0xokx_hot"],
        "cluster_confidence": "medium",
        "cluster_source": "entity_resolution_v1",
    }
    seed["transfers"].append({
        "transfer_id": "t4",
        "exchange_id": "binance",
        "asset": "BTC",
        "direction": "outflow",
        "value_usd": 600000.0,
        "from_address": "0xbinance_hot",
        "to_address": "0xokx_hot",
    })
    e2e = eil.build_exchange_to_exchange_flow_intelligence(
        seed=seed, transfers=seed["transfers"],
    )
    assert e2e["flow_matrix"]["same_exchange_internal_excluded"] is True
    assert e2e["flow_matrix"]["inter_exchange_count"] == 1
    assert e2e["entity_confidence"]["binance"]["confidence"] == "high"
    assert e2e["historical_revision_handling"]["historical_revision_handling"] is True
    assert len(e2e["net_bilateral_flows"]) >= 1


def test_553_same_exchange_internal_excluded(exchange_seed):
    seed = json.loads(exchange_seed.read_text(encoding="utf-8"))
    clusters = seed["exchange_clusters"]
    classified = eil.classify_inter_exchange_transfer(
        seed["transfers"][1], clusters,
    )
    assert classified["same_exchange_internal_excluded"] is True
    assert classified["is_inter_exchange"] is False


def test_reconciliation_tests(exchange_seed):
    tests = eil.run_reconciliation_tests()
    assert tests["all_passed"] is True
    test_names = [t["test"] for t in tests["reconciliation_tests"]]
    assert "internal_flow_classification" in test_names
    assert "no_silent_filtering" in test_names
    assert "netflow_formula_fixed" in test_names
    assert "supply_balance_entity_adjusted" in test_names
    assert "top_n_definition_documented" in test_names
    assert "same_exchange_internal_excluded" in test_names
    assert "historical_metric_validation_not_backtest" in test_names


def test_api_routes(exchange_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get(
        "/api/platform/intelligence-ledger/onchain-layer/exchange-intelligence/status"
    ).status_code == 200
    assert c.get(
        "/api/platform/intelligence-ledger/onchain-layer/exchange-intelligence?exchange_id=binance"
    ).status_code == 200
    assert c.get(
        "/api/platform/intelligence-ledger/onchain-layer/exchange-intelligence/reconciliation-tests"
    ).status_code == 200
