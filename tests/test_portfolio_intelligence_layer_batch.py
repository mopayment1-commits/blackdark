"""Tests — Portfolio Intelligence Layer epic #515 #557 #558."""

from __future__ import annotations

import json

import pytest

from bd_platform import portfolio_intelligence_layer as pil


@pytest.fixture
def portfolio_seed(tmp_path, monkeypatch):
    p = tmp_path / "portfolio_intelligence_layer_seed.json"
    p.write_text(json.dumps({
        "symbol_normalization": {"WBTC": "BTC"},
        "chain_coverage": {
            "ethereum": {"supported": True, "coverage_pct": 99.5, "display": "Ethereum"},
        },
        "portfolios": {
            "test_portfolio": {
                "name": "Test Portfolio",
                "latest_snapshot_timestamp": "2026-08-01T00:00:00Z",
                "available_snapshots": ["2026-08-01T00:00:00Z"],
            },
        },
        "snapshots": {
            "test_portfolio:2026-08-01T00:00:00Z": {
                "holdings": [
                    {"asset": "BTC", "amount": 1.0, "price_usd": 65000, "value_usd": 65000},
                ],
                "prices_as_of": "2026-08-01T00:00:00Z",
                "no_current_label_leakage": True,
            },
        },
        "global_assets": {
            "test_portfolio": {
                "as_of": "2026-08-26T14:00:00Z",
                "fx_applied": True,
                "holdings": [
                    {
                        "source_id": "binance",
                        "source_type": "exchange",
                        "asset": "BTC",
                        "network": "bitcoin",
                        "amount": 1.0,
                        "value_usd": 95000.0,
                        "freshness_seconds": 120,
                        "stale": False,
                        "missing": False,
                    },
                    {
                        "source_id": "binance",
                        "source_type": "exchange",
                        "asset": "BTC",
                        "network": "bitcoin",
                        "amount": 1.0,
                        "value_usd": 95000.0,
                        "freshness_seconds": 120,
                        "stale": False,
                        "missing": False,
                    },
                    {
                        "source_id": "wallet1",
                        "source_type": "wallet",
                        "asset": "ETH",
                        "network": "ethereum",
                        "amount": 5.0,
                        "value_usd": 21000.0,
                        "freshness_seconds": 3600,
                        "stale": True,
                        "missing": False,
                    },
                    {
                        "source_id": "defi1",
                        "source_type": "defi",
                        "asset": "USDC",
                        "network": "ethereum",
                        "amount": 0,
                        "value_usd": 0,
                        "stale": False,
                        "missing": True,
                    },
                ],
            },
        },
        "wallets": {
            "ethereum:0xtest123": {
                "chain": "ethereum",
                "historical_balances": {
                    "2026-08-01T00:00:00Z": {
                        "exact_timestamp_semantics": "block_timestamp",
                        "balances": [{"asset": "ETH", "amount": 10.0, "value_usd": 35000.0}],
                        "total_value_usd": 35000.0,
                        "valuation_available": True,
                        "reorg_handling": {
                            "reorg_handled": True,
                            "revision_id": "rev-001",
                            "canonical_block": 18500000,
                            "reorg_depth": 0,
                        },
                    },
                },
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(pil, "_SEED_PATH", p)
    return p


def test_epic_status_merged_not_standalone(portfolio_seed):
    status = pil.portfolio_intelligence_layer_status()
    assert status["standalone_rejected"] is True
    assert status["tasks_not_tickets"] is True
    assert set(status["feature_ids"]) == {515, 557, 558}
    assert status["dependencies"]["entity_resolution_feature_id"] == 541
    assert status["dependencies"]["asset_profiles_feature_id"] == 516


def test_515_historical_snapshot(portfolio_seed):
    snap = pil.build_historical_snapshot(
        "test_portfolio", snapshot_timestamp="2026-08-01T00:00:00Z",
    )
    assert snap["ok"] is True
    assert snap["total_value_usd"] == 65000.0
    assert snap["point_in_time_reconstruction"] is True


def test_557_global_asset_tracker(portfolio_seed):
    tracker = pil.build_global_asset_tracker("test_portfolio")
    assert tracker["ok"] is True
    assert tracker["no_advisory_language"] is True
    assert tracker["display"] == "Total Assets: $116,000.00"
    assert tracker["deduplication"]["duplicates_removed"] == 1
    assert tracker["stale_missing_visibility"]["stale_count"] == 1
    assert tracker["stale_missing_visibility"]["missing_count"] == 1


def test_557_duplicate_prevention(portfolio_seed):
    tracker = pil.build_global_asset_tracker("test_portfolio")
    assert tracker["deduplication"]["duplicate_prevention"] is True
    assert tracker["deduplication"]["deduped_count"] == 3


def test_557_breakdown_by_source(portfolio_seed):
    tracker = pil.build_global_asset_tracker("test_portfolio")
    assert "exchange" in tracker["breakdown"]["by_source"]
    assert "wallet" in tracker["breakdown"]["by_source"]


def test_558_historical_wallet_balance(portfolio_seed):
    bal = pil.build_historical_wallet_balance(
        "0xtest123", chain="ethereum", timestamp="2026-08-01T00:00:00Z",
    )
    assert bal["ok"] is True
    assert bal["total_value_usd"] == 35000.0
    assert bal["chain_coverage"]["coverage_explicit"] is True
    assert bal["reorg_revision_handling"]["reorg_revision_handling"] is True
    assert bal["exact_timestamp_semantics"] == "block_timestamp"


def test_main_panel_all_sub_modules(portfolio_seed):
    panel = pil.build_portfolio_intelligence_panel(portfolio_id="test_portfolio")
    assert panel["ok"] is True
    assert "515_historical_portfolio_snapshot" in panel["sub_modules"]
    assert "557_global_asset_tracker" in panel["sub_modules"]
    assert "558_historical_wallet_balance" in panel["sub_modules"]


def test_reconciliation_tests(portfolio_seed):
    result = pil.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["all_passed"] is True
    assert result["test_count"] >= 6


def test_no_advisory_banned_terms(portfolio_seed):
    panel = pil.build_portfolio_intelligence_panel(portfolio_id="test_portfolio")
    assert "you should buy" in panel["banned_output_terms"]
