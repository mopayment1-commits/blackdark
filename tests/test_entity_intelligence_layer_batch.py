"""Tests — Entity Intelligence Layer epic #539 #540."""

from __future__ import annotations

import json

import pytest

from bd_platform import entity_intelligence_layer as eil


@pytest.fixture
def entity_intel_seed(tmp_path, monkeypatch):
    p = tmp_path / "entity_intelligence_layer_seed.json"
    p.write_text(json.dumps({
        "cost_basis_rules": {
            "version": "1.0",
            "method": "fifo",
        },
        "entities": {
            "entity_whale_alpha": {
                "entity_type": "whale",
                "name": "Test Whale",
                "wallets": [
                    "0xabc1234567890def1234567890abc1234567890ab",
                    "0xdef9876543210abc9876543210def9876543210cd",
                ],
                "current_prices": {"BTC": 95000.0},
                "provenance": {
                    "source": "test_indexer",
                    "as_of": "2026-08-26T12:00:00Z",
                    "freshness_seconds": 300,
                    "stale_threshold_seconds": 3600,
                },
                "balances": {"total_usd": 5000000.0, "BTC": 50.0},
                "exchange_usage": [
                    {"exchange_id": "binance", "volume_usd": 1000000.0, "trade_count": 3},
                ],
                "events": [
                    {
                        "event_id": "t-001",
                        "timestamp": "2026-06-01T10:00:00Z",
                        "asset": "BTC",
                        "event_type": "buy",
                        "quantity": 50.0,
                        "execution_price": 60000.0,
                        "value_usd": 3000000.0,
                        "from_address": "0xexternal_001",
                        "to_address": "0xabc1234567890def1234567890abc1234567890ab",
                        "counterparty_id": "cex_binance",
                        "counterparty_label": "Binance",
                    },
                    {
                        "event_id": "t-002",
                        "timestamp": "2026-07-01T10:00:00Z",
                        "asset": "BTC",
                        "event_type": "internal_transfer",
                        "quantity": 10.0,
                        "value_usd": 700000.0,
                        "from_address": "0xabc1234567890def1234567890abc1234567890ab",
                        "to_address": "0xdef9876543210abc9876543210def9876543210cd",
                    },
                    {
                        "event_id": "t-003",
                        "timestamp": "2026-08-01T10:00:00Z",
                        "asset": "BTC",
                        "event_type": "sell",
                        "quantity": 5.0,
                        "execution_price": 90000.0,
                        "value_usd": 450000.0,
                        "from_address": "0xabc1234567890def1234567890abc1234567890ab",
                        "to_address": "0xexternal_002",
                        "counterparty_id": "cex_binance",
                        "counterparty_label": "Binance",
                    },
                    {
                        "event_id": "t-004",
                        "timestamp": "2026-08-10T10:00:00Z",
                        "asset": "BTC",
                        "event_type": "transfer_in",
                        "quantity": 5.0,
                        "cost_basis_unknown": True,
                        "value_usd": 475000.0,
                        "from_address": "0xunknown_sender",
                        "to_address": "0xdef9876543210abc9876543210def9876543210cd",
                        "counterparty_id": "unknown",
                        "counterparty_label": "Unknown",
                    },
                ],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(eil, "_SEED_PATH", p)
    return p


def test_epic_status_merged_not_standalone(entity_intel_seed):
    status = eil.entity_intelligence_layer_status()
    assert status["standalone_rejected"] is True
    assert status["tasks_not_tickets"] is True
    assert set(status["feature_ids"]) == {539, 540}
    assert status["dependencies"]["entity_resolution_feature_id"] == 541


def test_cost_basis_rules_versioned(entity_intel_seed):
    rules = eil.build_cost_basis_rules()
    assert rules["versioned"] is True
    assert rules["transfers_not_sales"] is True
    assert rules["unknown_basis_flagged"] is True


def test_transfers_not_sales(entity_intel_seed):
    pnl = eil.build_entity_pnl_tracker("entity_whale_alpha")
    assert pnl["ok"] is True
    assert pnl["pnl"]["transfers_not_sales"] is True
    assert pnl["pnl"]["internal_transfer_count"] == 1
    assert pnl["pnl"]["total_realized_pnl_usd"] == 150000.0


def test_unknown_basis_flagged(entity_intel_seed):
    pnl = eil.build_entity_pnl_tracker("entity_whale_alpha")
    assert pnl["pnl"]["unknown_basis_flagged"] is True
    assert pnl["pnl"]["unknown_basis_count"] == 1
    assert pnl["pnl"]["pnl_suppressed_due_to_unknown_basis"] is True


def test_realized_unrealized_pnl(entity_intel_seed):
    pnl = eil.build_entity_pnl_tracker("entity_whale_alpha")
    assert pnl["pnl"]["total_realized_pnl_usd"] == 150000.0
    assert pnl["pnl"]["total_unrealized_pnl_usd"] > 0
    assert pnl["pnl"]["total_pnl_usd"] == round(
        pnl["pnl"]["total_realized_pnl_usd"] + pnl["pnl"]["total_unrealized_pnl_usd"], 2
    )


def test_entity_profiles_freshness_visible(entity_intel_seed):
    profile = eil.build_entity_profiles_panel("entity_whale_alpha")
    assert profile["ok"] is True
    assert profile["freshness"]["freshness_visible"] is True
    assert profile["freshness"]["freshness_seconds"] == 300


def test_entity_wallet_reconciliation(entity_intel_seed):
    recon = eil.reconcile_entity_wallets("entity_whale_alpha")
    assert recon["entity_wallet_reconciliation"] is True
    assert recon["matched_count"] == 2
    assert recon["reconciled"] is True


def test_entity_profiles_aggregates(entity_intel_seed):
    profile = eil.build_entity_profiles_panel("entity_whale_alpha")
    assert profile["portfolio"]["total_usd"] == 5000000.0
    assert profile["history"]["event_count"] == 4
    assert len(profile["counterparties"]) >= 1
    assert profile["exchange_usage"][0]["exchange_id"] == "binance"


def test_main_panel(entity_intel_seed):
    panel = eil.build_entity_intelligence_panel(entity_id="entity_whale_alpha")
    assert panel["ok"] is True
    assert panel["epic_feature_id"] == 539
    assert "539_entity_pnl_tracker" in panel["sub_modules"]
    assert "540_entity_profiles" in panel["sub_modules"]
    assert panel["acceptance_criteria"]["unknown_basis_flagged"] is True


def test_reconciliation_tests(entity_intel_seed):
    result = eil.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["all_passed"] is True
    assert result["test_count"] >= 6


def test_classify_event_internal_not_sale(entity_intel_seed):
    event = {
        "event_type": "internal_transfer",
        "from_address": "0xabc1234567890def1234567890abc1234567890ab",
        "to_address": "0xdef9876543210abc9876543210def9876543210cd",
        "asset": "BTC",
        "quantity": 10.0,
    }
    classified = eil.classify_event(event, "entity_whale_alpha")
    assert classified["is_internal_transfer"] is True
    assert classified["treated_as_sale"] is False
    assert classified["transfers_not_sales"] is True


def test_classify_event_unknown_basis(entity_intel_seed):
    event = {
        "event_type": "transfer_in",
        "from_address": "0xunknown",
        "to_address": "0xabc1234567890def1234567890abc1234567890ab",
        "asset": "BTC",
        "quantity": 5.0,
        "cost_basis_unknown": True,
    }
    classified = eil.classify_event(event, "entity_whale_alpha")
    assert classified["unknown_basis_flagged"] is True
    assert classified["included_in_pnl"] is False
