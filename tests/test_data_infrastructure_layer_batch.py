"""Tests — Data Infrastructure Layer #564 Market + Network Join."""

from __future__ import annotations

import json

import pytest

from bd_platform import data_infrastructure_layer as dil


@pytest.fixture
def data_infra_seed(tmp_path, monkeypatch):
    p = tmp_path / "data_infrastructure_layer_seed.json"
    p.write_text(json.dumps({
        "default_as_of": "2026-08-26T14:00:00Z",
        "join_rules": {
            "version": "1.0",
            "max_forward_tolerance_seconds": 0,
        },
        "network_data": [
            {
                "record_id": "n1",
                "asset": "BTC",
                "timestamp": "2026-08-26T13:00:00Z",
                "metric": "active_addresses",
                "value": 100,
            },
            {
                "record_id": "n2",
                "asset": "BTC",
                "timestamp": "2026-08-26T14:30:00Z",
                "metric": "hash_rate",
                "value": 200,
            },
        ],
        "market_data": [
            {
                "record_id": "m1",
                "asset": "BTC",
                "timestamp": "2026-08-26T12:00:00Z",
                "price_usd": 94000.0,
                "source": "ohlcv",
            },
            {
                "record_id": "m2",
                "asset": "BTC",
                "timestamp": "2026-08-26T13:00:00Z",
                "price_usd": 94500.0,
                "source": "ohlcv",
            },
            {
                "record_id": "m3",
                "asset": "BTC",
                "timestamp": "2026-08-26T15:00:00Z",
                "price_usd": 96000.0,
                "source": "ohlcv",
            },
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(dil, "_SEED_PATH", p)
    return p


def test_status_sprint_0(data_infra_seed):
    status = dil.data_infrastructure_layer_status()
    assert status["sprint"] == 0
    assert status["standalone_rejected"] is True
    assert status["feature_ids"] == [564]


def test_no_look_ahead(data_infra_seed):
    join = dil.build_market_network_join()
    assert join["no_look_ahead"] is True
    assert join["look_ahead_violations"] == 0


def test_join_rules_documented(data_infra_seed):
    rules = dil.build_join_rules()
    assert rules["no_look_ahead"] is True
    assert rules["no_look_ahead_documented"] is True


def test_time_aligned_join(data_infra_seed):
    join = dil.build_market_network_join(asset="BTC")
    aligned = [j for j in join["joined_records"] if j.get("join_status") == "aligned"]
    assert len(aligned) >= 1
    for record in aligned:
        assert record["no_look_ahead"] is True
        assert record.get("look_ahead_violation") is False


def test_future_network_excluded(data_infra_seed):
    join = dil.build_market_network_join()
    record_ids = [j.get("record_id") for j in join["joined_records"]]
    assert "n2" not in record_ids


def test_main_panel(data_infra_seed):
    panel = dil.build_data_infrastructure_panel()
    assert panel["ok"] is True
    assert "564_market_network_join" in panel["sub_modules"]
    assert panel["foundation_feature"] is True


def test_reconciliation_tests(data_infra_seed):
    result = dil.run_reconciliation_tests()
    assert result["all_passed"] is True
