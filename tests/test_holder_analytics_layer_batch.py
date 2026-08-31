"""Tests — Holder Analytics Layer epic #559 #560."""

from __future__ import annotations

import json

import pytest

from bd_platform import holder_analytics_layer as hal


@pytest.fixture
def holder_seed(tmp_path, monkeypatch):
    p = tmp_path / "holder_analytics_layer_seed.json"
    p.write_text(json.dumps({
        "cohort_thresholds": {
            "version": "1.0",
            "sth_max_days": 155,
            "lth_min_days": 155,
            "effective_from": "2026-01-01T00:00:00Z",
        },
        "excluded_wallets": {
            "BTC": {
                "exchange": [{"address": "0xexchange001"}],
                "contract": [{"address": "0xcontract001"}],
                "bridge": [],
            },
        },
        "assets": {
            "BTC": {
                "as_of": "2026-08-26T10:00:00Z",
                "current_price": 95000.0,
                "provenance": {
                    "source": "onchain_indexer",
                    "label_source": "entity_resolution_v1",
                    "freshness_seconds": 600,
                },
                "holders": [
                    {
                        "address": "0xholder001",
                        "balance": 100.0,
                        "holding_duration_days": 30,
                        "acquisition_price": 60000.0,
                        "entity_type": "individual",
                    },
                    {
                        "address": "0xholder002",
                        "balance": 500.0,
                        "holding_duration_days": 200,
                        "acquisition_price": 30000.0,
                        "entity_type": "individual",
                    },
                    {
                        "address": "0xexchange001",
                        "balance": 5000.0,
                        "holding_duration_days": 10,
                        "acquisition_price": 90000.0,
                        "entity_type": "exchange",
                    },
                    {
                        "address": "0xcontract001",
                        "balance": 2000.0,
                        "holding_duration_days": 365,
                        "acquisition_price": 50000.0,
                        "entity_type": "contract",
                    },
                ],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(hal, "_SEED_PATH", p)
    return p


def test_epic_status_merged_not_standalone(holder_seed):
    status = hal.holder_analytics_layer_status()
    assert status["standalone_rejected"] is True
    assert status["tasks_not_tickets"] is True
    assert set(status["feature_ids"]) == {559, 560}
    assert status["dependencies"]["entity_resolution_feature_id"] == 541


def test_cohort_thresholds_versioned(holder_seed):
    thresholds = hal.build_cohort_thresholds()
    assert thresholds["versioned"] is True
    assert thresholds["cohort_threshold_version"] == "1.0"
    assert thresholds["sth_max_days"] == 155
    assert thresholds["no_reclassification_leakage"] is True


def test_exchange_contract_wallets_excluded(holder_seed):
    seed = json.loads(holder_seed.read_text(encoding="utf-8"))
    holders = seed["assets"]["BTC"]["holders"]
    filtered, exclusion = hal.filter_holders(holders, seed=seed, asset="BTC")
    assert exclusion["exchange_contract_excluded"] is True
    assert exclusion["excluded_count"] == 2
    assert len(filtered) == 2


def test_sth_lth_classification(holder_seed):
    seed = json.loads(holder_seed.read_text(encoding="utf-8"))
    thresholds = hal.build_cohort_thresholds(seed)
    holders, _ = hal.filter_holders(seed["assets"]["BTC"]["holders"], seed=seed, asset="BTC")

    classified = [
        hal.classify_holder_cohort(h, thresholds=thresholds, as_of="2026-08-26T10:00:00Z")
        for h in holders
    ]
    sth = [h for h in classified if h["cohort"] == "sth"]
    lth = [h for h in classified if h["cohort"] == "lth"]
    assert len(sth) == 1
    assert len(lth) == 1
    assert all(h["point_in_time"] for h in classified)
    assert all(h["no_reclassification_leakage"] for h in classified)


def test_559_cohort_intelligence(holder_seed):
    seed = json.loads(holder_seed.read_text(encoding="utf-8"))
    cohort = hal.build_cohort_intelligence("BTC", seed=seed, as_of="2026-08-26T10:00:00Z")
    assert cohort["no_reclassification_leakage"] is True
    assert cohort["sth"]["holder_count"] == 1
    assert cohort["lth"]["holder_count"] == 1
    assert cohort["wallet_exclusion"]["excluded_count"] == 2


def test_560_distribution_intelligence(holder_seed):
    seed = json.loads(holder_seed.read_text(encoding="utf-8"))
    dist = hal.build_distribution_intelligence("BTC", seed=seed, as_of="2026-08-26T10:00:00Z")
    assert dist["provenance"]["provenance_clear"] is True
    assert len(dist["distribution_bands"]) >= 1
    assert dist["concentration"]["concentration_documented"] is True
    assert dist["wallet_exclusion"]["exchange_contract_excluded"] is True


def test_epic_panel_all_sub_modules(holder_seed):
    panel = hal.build_holder_analytics_panel(asset="BTC")
    assert panel["ok"] is True
    assert "559_holder_cohort_intelligence" in panel["sub_modules"]
    assert "560_holder_distribution_intelligence" in panel["sub_modules"]
    assert panel["no_reclassification_leakage"] is True
    assert panel["point_in_time_reproducibility"] is True


def test_reconciliation_tests(holder_seed):
    tests = hal.run_reconciliation_tests()
    assert tests["all_passed"] is True
    test_names = [t["test"] for t in tests["reconciliation_tests"]]
    assert "cohort_thresholds_versioned" in test_names
    assert "exchange_contract_excluded_btc" in test_names
    assert "provenance_clear" in test_names


def test_api_routes(holder_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get(
        "/api/platform/intelligence-ledger/onchain-layer/holder-analytics/status"
    ).status_code == 200
    assert c.get(
        "/api/platform/intelligence-ledger/onchain-layer/holder-analytics?asset=BTC"
    ).status_code == 200
    assert c.get(
        "/api/platform/intelligence-ledger/onchain-layer/holder-analytics/reconciliation-tests"
    ).status_code == 200
