"""Tests — On-Chain Metrics Library #577 epic + #574 API sub-task."""

from __future__ import annotations

import json

import pytest

from bd_platform import onchain_metrics_library as oml


@pytest.fixture
def metrics_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_library_seed.json"
    p.write_text(json.dumps({
        "metric_definitions": {
            "active_addresses": {
                "name": "Active Addresses",
                "formula": "count(distinct addresses)",
                "formula_version": "1.0",
                "source": "indexer",
                "unit": "addresses",
            },
            "hash_rate": {
                "name": "Hash Rate",
                "formula": "mean(hash_rate)",
                "formula_version": "1.0",
                "source": "miner_layer",
                "unit": "EH/s",
            },
        },
        "assets": {
            "BTC": {
                "metrics": {
                    "active_addresses": {"value": 100, "available": True, "as_of": "2026-08-26T00:00:00Z"},
                    "hash_rate": {"value": 500, "available": True, "as_of": "2026-08-26T00:00:00Z"},
                },
            },
            "ETH": {
                "metrics": {
                    "active_addresses": {"value": 50, "available": True, "as_of": "2026-08-26T00:00:00Z"},
                    "hash_rate": {"value": None, "available": False, "as_of": None},
                },
            },
        },
        "historical_qa": {"periods_tested": 12},
    }), encoding="utf-8")
    monkeypatch.setattr(oml, "_SEED_PATH", p)
    return p


def test_status_epic_577_not_standalone(metrics_seed):
    status = oml.onchain_metrics_library_status()
    assert status["epic_feature_id"] == 577
    assert status["standalone_rejected"] is True
    assert "574" in status["absorbed_tickets"]


def test_canonical_metric_definitions(metrics_seed):
    defs = oml.build_metric_definitions()
    assert defs["canonical_definitions"] is True
    assert defs["metric_count"] == 2
    assert all(m["unknown_is_not_zero"] for m in defs["metrics"])


def test_network_data_pro_api_574(metrics_seed):
    api = oml.build_network_data_pro_api("BTC")
    assert api["task_id"] == "574"
    assert api["standalone_rejected"] is True
    assert api["institutional_api"] is True
    assert len(api["network_metrics"]) == 2


def test_missing_not_zero_eth_hash_rate(metrics_seed):
    api = oml.build_network_data_pro_api("ETH")
    hash_metric = next(m for m in api["network_metrics"] if m["metric_id"] == "hash_rate")
    assert hash_metric["missing"] is True
    assert hash_metric["available"] is False
    assert hash_metric["value"] != 0


def test_metrics_library_panel_includes_submodules(metrics_seed):
    panel = oml.build_metrics_library_panel("BTC")
    assert panel["canonical_metric_definitions"] is True
    assert "574_network_data_pro_api" in panel["sub_modules"]
    assert panel["sub_modules"]["tasks_not_tickets"] is True


def test_historical_qa_tests(metrics_seed):
    qa = oml.run_historical_qa_tests()
    assert qa["all_passed"] is True
    assert qa["test_count"] >= 6


def test_build_panel_wraps_evidence(metrics_seed):
    panel = oml.build_onchain_metrics_library_panel("BTC")
    assert panel.get("evidence_metadata") or panel.get("institutional_evidence")


def test_api_routes(metrics_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library?asset=BTC").status_code == 200
    api = c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/network-api?asset=BTC")
    assert api.status_code == 200
    assert api.json().get("task_id") == "574"
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/historical-qa").status_code == 200
