"""Tests — #259 Liquidity Analytics merged into Market Radar."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import liquidity_analytics as la


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "liquidity_analytics_seed.json"
    seed.write_text(
        json.dumps({
            "methodology_version": "1.2",
            "last_updated": "2026-08-25",
            "assets": {
                "BTC": {
                    "primary_venue": "Binance",
                    "liquidity_sufficient_for_usd": 50000,
                    "is_defi": False,
                    "replay_qa": {
                        "block_start": 18500000,
                        "block_end": 18500100,
                        "block_x": 18500050,
                        "order_size_usd": 10000,
                        "actual_slippage_pct": 0.28,
                        "replay_slippage_pct": 0.3,
                        "variance_threshold_pct": 0.05,
                    },
                    "depth": {
                        "levels": 10,
                        "method": "Sum of top 10 levels per venue",
                        "venues": {
                            "Binance": 530000000,
                            "Coinbase": 370000000,
                        },
                    },
                    "spread": {
                        "spread_bps": 2.1,
                        "venue": "Binance",
                        "pair": "BTC/USDT",
                        "time_display": "2026-08-25 20:58 UTC",
                    },
                    "slippage": {
                        "method": "Order book simulation",
                        "by_size": {
                            "$10K": 0.12,
                            "$100K": 0.8,
                            "$1M": 3.5,
                        },
                    },
                    "total_cost": {
                        "slippage_pct": 0.3,
                        "gas_usd": 0,
                        "notional_usd": 10000,
                        "gross_opportunity_pct": 1.2,
                    },
                },
                "UNI": {
                    "primary_venue": "Uniswap V3",
                    "liquidity_sufficient_for_usd": 10000,
                    "is_defi": True,
                    "amm_slippage_pct": 0.5,
                    "replay_qa": {
                        "block_start": 18500000,
                        "block_end": 18500040,
                        "block_x": 18500020,
                        "order_size_usd": 10000,
                        "actual_slippage_pct": 0.48,
                        "replay_slippage_pct": 0.5,
                        "variance_threshold_pct": 0.05,
                    },
                    "depth": {"levels": 10, "venues": {"Uniswap V3": 12000000}},
                    "spread": {
                        "spread_bps": 0,
                        "venue": "Uniswap V3",
                        "pair": "UNI/USDC",
                        "time_display": "2026-08-25 20:58 UTC",
                    },
                    "slippage": {
                        "method": "AMM curve simulation",
                        "by_size": {"$10K": 0.5, "$100K": 2.1, "$1M": 8.5},
                    },
                    "total_cost": {
                        "slippage_pct": 0.5,
                        "gas_usd": 12.5,
                        "notional_usd": 10000,
                        "gross_opportunity_pct": 1.8,
                    },
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(la, "_SEED_PATH", seed)
    return seed


def test_replay_qa_passed(isolated_seed):
    replay = la.build_replay_qa({
        "block_start": 18500000,
        "block_end": 18500100,
        "block_x": 18500050,
        "order_size_usd": 10000,
        "actual_slippage_pct": 0.28,
        "replay_slippage_pct": 0.3,
        "variance_threshold_pct": 0.05,
    })
    assert replay["qa_passed"] is True
    assert "Replay: Block 18500000 to Block 18500100" in replay["display"]
    assert "Actual vs Replay: 0.28%" in replay["display"]
    assert "Variance: 0.02%" in replay["display"]
    assert "QA: Passed" in replay["display"]
    assert replay["replay_qa_required"] is True


def test_depth_per_venue_and_global(isolated_seed):
    depth = la.build_depth_metrics({
        "levels": 10,
        "method": "Sum of top 10 levels per venue",
        "venues": {"Binance": 530000000, "Coinbase": 370000000},
    })
    assert "Binance Depth (top 10):" in depth["display"]
    assert "Coinbase Depth (top 10):" in depth["display"]
    assert "Global:" in depth["display"]
    assert depth["no_ambiguous_depth"] is True
    assert depth["global_usd"] == 900000000


def test_spread_descriptive_only(isolated_seed):
    spread = la.build_spread_metric({
        "spread_bps": 2.1,
        "venue": "Binance",
        "pair": "BTC/USDT",
        "time_display": "2026-08-25 20:58 UTC",
    })
    assert spread["display"] == (
        "Spread: 2.1 bps | Venue: Binance | Asset: BTC/USDT | Time: 2026-08-25 20:58 UTC"
    )
    assert spread["descriptive_only"] is True
    assert spread["no_buy_signal"] is True


def test_slippage_per_size_per_venue(isolated_seed):
    slip = la.build_slippage_by_size(
        {
            "method": "Order book simulation",
            "by_size": {"$10K": 0.12, "$100K": 0.8, "$1M": 3.5},
        },
        venue="Binance",
    )
    assert "Slippage (Binance," in slip["display"]
    assert "($10K): 0.12%" in slip["display"]
    assert "($100K): 0.8%" in slip["display"]
    assert "($1M): 3.5%" in slip["display"]
    assert "Order book simulation" in slip["display"]
    assert slip["per_size_per_venue"] is True


def test_total_cost_gas_fee_db(isolated_seed):
    cost = la.build_total_cost_block({
        "slippage_pct": 0.3,
        "gas_usd": 12.5,
        "notional_usd": 10000,
        "gross_opportunity_pct": 1.2,
    })
    assert "Slippage: 0.3%" in cost["display"]
    assert "Gas: $12" in cost["display"]
    assert "Total Cost:" in cost["display"]
    assert "Net Opportunity:" in cost["display"]
    assert cost["fee_db_mandatory"] is True
    assert cost["gas_cost_engine_247"] is True


def test_defi_integration_separation(isolated_seed):
    cex = la.build_defi_integration({"is_defi": False}, "BTC")
    assert "Order Book Slippage (#259): active" in cex["display"]
    assert "AMM Slippage (#228): N/A (CEX asset)" in cex["display"]
    assert cex["no_cex_defi_mixing"] is True

    defi = la.build_defi_integration({"is_defi": True, "amm_slippage_pct": 0.5}, "UNI")
    assert "AMM Slippage (#228): 0.5%" in defi["display"]
    assert "Order Book Slippage (#259): N/A (DeFi has no order book)" in defi["display"]


def test_update_frequency_by_tier(isolated_seed):
    free = la._update_frequency("free")
    pro = la._update_frequency("pro")
    ent = la._update_frequency("institutional")
    assert "per 30s" in free["display"]
    assert "per 5s" in pro["display"]
    assert "per tick" in ent["display"]
    assert free["no_instant_claim"] is True


def test_methodology_versioned(isolated_seed):
    meth = la.build_methodology_block(json.loads(isolated_seed.read_text()))
    assert "Liquidity Analytics v1.2" in meth["display"]
    assert "Depth: Top 10 levels" in meth["display"]
    assert "Replay: Block-level" in meth["display"]


def test_no_signal_language(isolated_seed):
    panel = la.build_liquidity_analytics_panel("BTC", tier="pro")
    assert panel["ok"] is True
    assert panel["no_signal_language"] is True
    assert panel["no_opportunity_language"] is True
    assert "Liquidity: Sufficient for" in panel["liquidity_display"]
    assert "enter now" not in panel["liquidity_display"].lower()


def test_disclaimer_non_hideable(isolated_seed):
    panel = la.build_liquidity_analytics_panel("BTC")
    assert panel["disclaimer_hideable"] is False
    assert "not guarantees of execution price" in panel["disclaimer"].lower()


def test_panel_integrations(isolated_seed):
    panel = la.build_liquidity_analytics_panel("BTC", tier="pro")
    assert panel["feature_id"] == 259
    assert panel["standalone"] is False
    assert panel["merged_into"] == "market_radar"
    assert panel["replay_qa"]["qa_passed"] is True
    assert panel["global_order_book_249"] is not None
    assert "Complete Liquidity Picture" in panel["global_order_book_249"]["display"]


def test_defi_panel(isolated_seed):
    panel = la.build_liquidity_analytics_panel("UNI", tier="pro")
    assert panel["ok"] is True
    assert "AMM Slippage (#228)" in panel["defi_integration"]["display"]


def test_status(isolated_seed):
    status = la.liquidity_analytics_status()
    assert status["feature_id"] == 259
    assert status["sprint"] == 2
    assert status["acceptance_criteria"]["replay_qa"] is True
    assert 249 in status["complements"]


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/liquidity-analytics/status").status_code == 200
    resp = c.get("/api/platform/market-radar/liquidity-analytics?asset=BTC&tier=pro")
    assert resp.status_code == 200
    body = resp.json()
    assert body["feature_id"] == 259
    assert body["replay_qa"]["qa_passed"] is True


def test_full_seed_exists():
    seed = json.loads(Path("data/liquidity_analytics_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 259
    assert seed["methodology_version"] == "1.2"
    assert len(seed["assets"]) >= 3
