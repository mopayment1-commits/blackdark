"""Tests — Entity Layer #542 Entity-Adjusted Metrics, #543 Entity-Aware Wallet Intelligence."""

from __future__ import annotations

import json

import pytest

from bd_platform import entity_layer as el
from bd_platform import entity_resolution_engine as ere


@pytest.fixture
def entity_resolution_seed(tmp_path, monkeypatch):
    p = tmp_path / "entity_resolution_engine_seed.json"
    p.write_text(json.dumps({
        "entities": {
            "entity_binance_hot": {
                "entity_type": "exchange",
                "attribution": {
                    "label": "Binance Hot Wallet Cluster",
                    "confidence": "verified",
                    "source": "verified_labels_registry",
                    "version": "1.0",
                },
            },
            "entity_whale_alpha": {
                "entity_type": "whale",
                "attribution": {
                    "label": "Whale Alpha",
                    "confidence": "high",
                    "source": "onchain_graph_clustering",
                    "version": "1.0",
                },
            },
        },
        "clusters": {
            "cluster_binance_001": {
                "cluster_id": "cluster_binance_001",
                "entity_id": "entity_binance_hot",
                "version": "1.0",
                "addresses": ["0xbinance_hot", "0xbinance_cold"],
            },
            "cluster_whale_001": {
                "cluster_id": "cluster_whale_001",
                "entity_id": "entity_whale_alpha",
                "version": "1.0",
                "addresses": ["0xwhale_a", "0xwhale_b"],
            },
        },
        "address_index": {
            "0xbinance_hot": {"cluster_id": "cluster_binance_001"},
            "0xbinance_cold": {"cluster_id": "cluster_binance_001"},
            "0xwhale_a": {"cluster_id": "cluster_whale_001"},
            "0xwhale_b": {"cluster_id": "cluster_whale_001"},
        },
    }), encoding="utf-8")
    monkeypatch.setattr(ere, "_SEED_PATH", p)
    return p


@pytest.fixture
def entity_layer_seed(tmp_path, monkeypatch, entity_resolution_seed):
    p = tmp_path / "entity_layer_seed.json"
    p.write_text(json.dumps({
        "entity_profiles": {
            "entity_binance_hot": {"entity_type": "exchange", "name": "Binance Hot"},
            "entity_whale_alpha": {"entity_type": "whale", "name": "Whale Alpha"},
        },
        "transfers": [
            {
                "transfer_id": "t1",
                "asset": "ETH",
                "direction": "inflow",
                "value_usd": 1000000.0,
                "from_address": "0xexternal",
                "to_address": "0xbinance_hot",
            },
            {
                "transfer_id": "t2",
                "asset": "ETH",
                "direction": "inflow",
                "value_usd": 500000.0,
                "from_address": "0xbinance_hot",
                "to_address": "0xbinance_cold",
            },
            {
                "transfer_id": "t3",
                "asset": "ETH",
                "direction": "outflow",
                "value_usd": 300000.0,
                "from_address": "0xbinance_hot",
                "to_address": "0xexternal2",
            },
            {
                "transfer_id": "t4",
                "asset": "USDC",
                "direction": "inflow",
                "value_usd": 200000.0,
                "from_address": "0xunknown_a",
                "to_address": "0xunknown_b",
            },
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(el, "_SEED_PATH", p)
    return p


def test_layer_status_not_standalone(entity_layer_seed):
    status = el.entity_layer_status()
    assert status["standalone_rejected"] is True
    assert status["tasks_not_tickets"] is True
    assert set(status["feature_ids"]) == {542, 543}
    assert status["dependencies"]["entity_resolution_feature_id"] == 541


def test_542_raw_and_adjusted_both_visible(entity_layer_seed):
    seed = json.loads(entity_layer_seed.read_text(encoding="utf-8"))
    metrics = el.compute_entity_adjusted_metrics(seed["transfers"], view="both")

    assert metrics["raw_vs_adjusted_toggle"] is True
    assert metrics["adjusted_only_forbidden"] is True
    assert "raw" in metrics
    assert "adjusted" in metrics
    assert metrics["raw"]["metrics"]["transfer_count"] == 4
    assert metrics["adjusted"]["metrics"]["transfer_count"] == 3
    assert metrics["raw"]["metrics"]["internal_count"] == 1


def test_542_internal_flow_classification(entity_layer_seed):
    seed = json.loads(entity_layer_seed.read_text(encoding="utf-8"))
    classified = [el.classify_transfer_entity(t) for t in seed["transfers"]]

    internal = [t for t in classified if t["is_internal"]]
    assert len(internal) == 1
    assert internal[0]["transfer_id"] == "t2"
    assert internal[0]["no_silent_attribution"] is True
    assert internal[0]["from_cluster_source"] == "verified_labels_registry"


def test_542_methodology_visible(entity_layer_seed):
    methodology = el.build_methodology_block()
    assert methodology["methodology_visible"] is True
    assert methodology["unknown_entities_preserved"] is True
    assert methodology["no_silent_attribution"] is True


def test_542_unknown_entities_preserved(entity_layer_seed):
    seed = json.loads(entity_layer_seed.read_text(encoding="utf-8"))
    unknown_transfer = seed["transfers"][3]
    classified = el.classify_transfer_entity(unknown_transfer)

    assert classified["is_internal"] is False
    assert classified["unknown_entities_preserved"] is True
    assert classified["from_entity"]["unknown_remains_unknown"] is True


def test_543_wallet_unknown_remains_unknown(entity_layer_seed):
    wallet = el.build_wallet_intelligence("0xunknown999")
    assert wallet["unknown_remains_unknown"] is True
    assert wallet["entity_name"] is None
    assert wallet["no_likely_guessing"] is True
    assert wallet["identity_without_confidence_forbidden"] is True


def test_543_wallet_with_confidence_and_source(entity_layer_seed):
    wallet = el.build_wallet_intelligence("0xbinance_hot")
    assert wallet["entity_name"] == "Binance Hot Wallet Cluster"
    assert wallet["entity_type"] == "exchange"
    assert wallet["confidence"] == "verified"
    assert wallet["source"] == "verified_labels_registry"
    assert wallet["confidence_source_mandatory"] is True


def test_epic_panel_all_sub_modules(entity_layer_seed):
    panel = el.build_entity_layer_panel(
        address="0xbinance_hot",
        view="both",
    )
    assert panel["ok"] is True
    assert "542_entity_adjusted_metrics" in panel["sub_modules"]
    assert "543_entity_aware_wallet_intelligence" in panel["sub_modules"]
    assert panel["acceptance_criteria"]["methodology_visible"] is True


def test_reconciliation_tests(entity_layer_seed):
    tests = el.run_reconciliation_tests()
    assert tests["all_passed"] is True
    test_names = [t["test"] for t in tests["reconciliation_tests"]]
    assert "raw_and_adjusted_both_visible" in test_names
    assert "methodology_visible" in test_names
    assert "wallet_unknown_remains_unknown" in test_names


def test_api_routes(entity_layer_seed, entity_resolution_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/entity-layer/status").status_code == 200
    assert c.get(
        "/api/platform/intelligence-ledger/entity-layer?address=0x28c6c06298d514db089934071355e5743bf21d60"
    ).status_code == 200
    assert c.get(
        "/api/platform/intelligence-ledger/entity-layer/wallet-intelligence?address=0x28c6c06298d514db089934071355e5743bf21d60"
    ).status_code == 200
    assert c.get(
        "/api/platform/intelligence-ledger/entity-layer/reconciliation-tests"
    ).status_code == 200
