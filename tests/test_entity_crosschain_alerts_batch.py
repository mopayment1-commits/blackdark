"""Tests — #541 Entity Resolution, #522 Cross-Chain Liquidity, #532 Custom Alerts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import cross_chain_liquidity_flow as cclf
from bd_platform import custom_alerts as ca
from bd_platform import entity_resolution_engine as ere


@pytest.fixture
def entity_seed(tmp_path, monkeypatch):
    p = tmp_path / "entity_resolution_engine_seed.json"
    p.write_text(json.dumps({
        "entities": {
            "entity_whale": {
                "entity_type": "whale",
                "attribution": {
                    "label": "Whale Alpha", "confidence": "high",
                    "source": "onchain_graph", "version": "1.0",
                },
            },
        },
        "clusters": {
            "cluster_001": {
                "cluster_id": "cluster_001", "entity_id": "entity_whale",
                "version": "1.0", "addresses": ["0xabc123"],
            },
        },
        "address_index": {
            "0xabc123": {"cluster_id": "cluster_001"},
        },
    }), encoding="utf-8")
    monkeypatch.setattr(ere, "_SEED_PATH", p)
    return p


@pytest.fixture
def liquidity_seed(tmp_path, monkeypatch):
    p = tmp_path / "cross_chain_liquidity_flow_seed.json"
    p.write_text(json.dumps({
        "reconciliation": {"reorg_handling": True, "reorg_confirmation_blocks": 12},
        "flows": [
            {
                "source_chain": "ethereum", "dest_chain": "arbitrum",
                "token_symbol": "USDC", "bridge_tx_hash": "0xdup",
                "amount_usd": 1000000, "bridge_identity_verified": True,
                "token_identity_verified": True, "reorg_confirmed": True,
                "freshness_seconds": 300, "direction": "inflow",
            },
            {
                "source_chain": "ethereum", "dest_chain": "arbitrum",
                "token_symbol": "USDC", "bridge_tx_hash": "0xdup",
                "amount_usd": 1000000, "bridge_identity_verified": True,
                "token_identity_verified": True, "reorg_confirmed": True,
                "freshness_seconds": 300, "direction": "inflow",
            },
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(cclf, "_SEED_PATH", p)
    return p


@pytest.fixture
def alerts_seed(tmp_path, monkeypatch, entity_seed):
    p = tmp_path / "custom_alerts_seed.json"
    p.write_text(json.dumps({
        "rules": [{
            "rule_id": "r1", "active": True, "entity_id": "entity_whale",
            "min_value_usd": 100000, "channels": ["webhook"],
        }],
        "pending_events": [{
            "entity_id": "entity_whale",
            "address": "0xabc123",
            "token": "ETH", "chain": "ethereum",
            "value_usd": 500000,
            "tx_hash": "0xtx001",
        }],
        "delivery_log": [],
    }), encoding="utf-8")
    monkeypatch.setattr(ca, "_SEED_PATH", p)
    return p


def test_541_critical_foundation_entity_resolution(entity_seed):
    status = ere.entity_resolution_engine_status()
    assert status["priority"] == "critical"
    assert status["critical_infrastructure"] is True
    assert status["sprint"] == 0
    assert status["acceptance_criteria"]["unknown_remains_unknown"] is True


def test_541_unknown_remains_unknown(entity_seed):
    result = ere.resolve_address("0xunknown999")
    assert result["unknown_remains_unknown"] is True
    assert result["attribution"]["entity_label"] == "Unknown"
    assert result["attribution"]["confidence"] == "unknown"


def test_541_cluster_versioning(entity_seed):
    panel = ere.build_entity_resolution_panel(address="0xabc123")
    resolution = panel["resolution"]
    assert resolution["resolved"] is True
    assert resolution["cluster"]["versioned"] is True
    assert resolution["attribution"]["source_mandatory"] is True


def test_522_cross_chain_liquidity_integrated(liquidity_seed):
    panel = cclf.build_cross_chain_liquidity_panel()
    assert panel["standalone_rejected"] is True
    assert panel["duplicates_removed"] == 1
    assert panel["reconciliation"]["double_counting_prevented"] is True
    assert panel["reconciliation"]["bridge_identity_verified"] is True


def test_522_reconciliation_tests(liquidity_seed):
    tests = cclf.run_reconciliation_tests()
    assert tests["all_passed"] is True
    assert tests["test_count"] >= 4
    test_names = [t["test"] for t in tests["reconciliation_tests"]]
    assert "double_count_prevention" in test_names
    assert "bridge_identity_verified" in test_names


def test_532_custom_alerts_no_buy_sell(alerts_seed, entity_seed):
    panel = ca.build_custom_alerts_panel()
    assert panel["no_buy_sell_alerts"] is True
    assert panel["backend_enforcement"] is True
    assert panel["direct_tx_evidence_required"] is True
    if panel["triggered_alerts"]:
        alert = panel["triggered_alerts"][0]
        assert alert["not_buy_sell_signal"] is True
        assert alert["tx_hash"] is not None
        assert alert["direct_tx_evidence"] is True


def test_532_rate_limits(alerts_seed):
    rate = ca.check_rate_limit("user1", delivery_log=[], limit_per_hour=5)
    assert rate["allowed"] is True
    assert rate["rate_limit_enforced"] is True


def test_532_depends_on_541_516(alerts_seed):
    deps = ca.build_dependencies_block()
    assert deps["entity_resolution_feature_id"] == 541
    assert deps["asset_profiles_feature_id"] == 516


def test_api_routes(entity_seed, liquidity_seed, alerts_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/foundation/entity-resolution/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/foundation/entity-resolution?address=0xabc123").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/cross-chain-liquidity/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/cross-chain-liquidity/reconciliation-tests").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/infrastructure/custom-alerts/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/infrastructure/custom-alerts").status_code == 200


def test_full_seeds_exist():
    ere_data = json.loads(Path("data/entity_resolution_engine_seed.json").read_text())
    assert ere_data["priority"] == "critical"
    assert ere_data["feature_id"] == 541

    cclf_data = json.loads(Path("data/cross_chain_liquidity_flow_seed.json").read_text())
    assert cclf_data["standalone_rejected"] is True

    ca_data = json.loads(Path("data/custom_alerts_seed.json").read_text())
    assert ca_data["feature_id"] == 532
