"""Tests — #235 DEX Volume Feed merged into #705 Asset Metadata."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import canonical_asset_registry as car
from bd_platform import dex_volume_feed as dvf


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "dex_volume_feed_seed.json"
    seed.write_text(
        json.dumps({
            "methodology_version": "2.1",
            "wash_policy_version": "1.3",
            "last_updated": "2026-08-25",
            "last_updated_utc": "2026-08-25T19:45:00+00:00",
            "last_block": 21234567,
            "wash_noise_policy": {
                "minimum_trade_usd": 500,
                "bot_filtered": True,
                "method": "Heuristic + address clustering v1.2",
            },
            "normalization": {
                "fx_rate_method": "hourly VWAP",
                "stablecoin_peg_adjustment": True,
            },
            "assets": {
                "ETH": {
                    "volume_24h_usd": 2840000000,
                    "trend": "up",
                    "protocols": {
                        "Uniswap v3": 1420000000,
                        "Curve": 568000000,
                        "Balancer": 284000000,
                        "PancakeSwap": 568000000,
                    },
                    "chains": {
                        "Ethereum": 1988000000,
                        "Arbitrum": 426000000,
                        "Polygon": 284000000,
                        "BSC": 142000000,
                    },
                    "historical": {
                        "7d_usd": 18200000000,
                        "30d_usd": 78000000000,
                        "90d_usd": 228000000000,
                        "yoy_pct": 12.4,
                    },
                },
                "UNI": {
                    "volume_24h_usd": 89000000,
                    "trend": "up",
                    "protocols": {
                        "Uniswap v3": 71200000,
                        "Curve": 8900000,
                        "Balancer": 4450000,
                        "PancakeSwap": 4450000,
                    },
                    "chains": {
                        "Ethereum": 62300000,
                        "Arbitrum": 13350000,
                        "Polygon": 8900000,
                        "BSC": 4450000,
                    },
                    "historical": {
                        "7d_usd": 580000000,
                        "30d_usd": 2450000000,
                        "90d_usd": 7200000000,
                        "yoy_pct": 8.7,
                    },
                    "yield_context": {
                        "fees_generated_usd": 267000,
                        "lp_share_usd": 1335,
                        "farming_related": True,
                    },
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(dvf, "_SEED_PATH", seed)
    return seed


def test_wash_noise_policy(isolated_seed):
    policy = dvf.build_wash_noise_policy(json.loads(isolated_seed.read_text()))
    assert policy["wash_trades_excluded"] is True
    assert policy["minimum_trade_usd"] == 500
    assert "Heuristic + address clustering" in policy["display"]
    assert policy["no_volume_without_policy"] is True


def test_normalization(isolated_seed):
    norm = dvf.build_normalization(json.loads(isolated_seed.read_text()))
    assert norm["currency"] == "USD"
    assert "hourly VWAP" in norm["display"]
    assert norm["stablecoin_peg_adjustment"] is True


def test_protocol_breakdown(isolated_seed):
    asset = json.loads(isolated_seed.read_text())["assets"]["ETH"]
    breakdown = dvf.build_protocol_breakdown(asset["protocols"])
    assert "Uniswap v3" in breakdown["display"]
    assert "Total:" in breakdown["display"]
    assert breakdown["no_total_without_breakdown"] is True
    assert len(breakdown["entries"]) == 4


def test_chain_separation(isolated_seed):
    asset = json.loads(isolated_seed.read_text())["assets"]["ETH"]
    chains = dvf.build_chain_breakdown(asset["chains"])
    assert chains["chain_separated"] is True
    assert chains["no_hidden_aggregation"] is True
    assert "Ethereum:" in chains["display"]
    assert "BSC:" in chains["display"]
    assert len(chains["entries"]) == 4


def test_historical_trend(isolated_seed):
    asset = json.loads(isolated_seed.read_text())["assets"]["ETH"]
    trend = dvf.build_historical_trend(asset["historical"])
    assert "7D:" in trend["display"]
    assert "30D:" in trend["display"]
    assert "90D:" in trend["display"]
    assert "YoY:" in trend["display"]
    assert trend["trend_not_snapshot_only"] is True


def test_methodology_versioned(isolated_seed):
    meth = dvf.build_methodology_block(json.loads(isolated_seed.read_text()))
    assert "DEX Volume Methodology v2.1" in meth["display"]
    assert "Wash Policy: v1.3" in meth["display"]
    assert "USD VWAP" in meth["display"]


def test_update_schedule(isolated_seed):
    sched = dvf.build_update_schedule(json.loads(isolated_seed.read_text()))
    assert "Every 15 minutes" in sched["display"]
    assert "On-chain events" in sched["display"]
    assert "Last Block:" in sched["display"]
    assert sched["no_instant_claim"] is True


def test_no_opportunity_language(isolated_seed):
    block = dvf.get_dex_volume_for_asset("ETH")
    assert block is not None
    assert "DEX Volume (24H):" in block["volume_display"]
    assert "Trend:" in block["volume_display"]
    assert block["no_opportunity_language"] is True
    assert "exploding" not in block["volume_display"].lower()
    assert "trade now" not in block["volume_display"].lower()


def test_disclaimer_non_hideable(isolated_seed):
    block = dvf.get_dex_volume_for_asset("ETH")
    assert block is not None
    assert "wash trades" in block["disclaimer"].lower()
    assert "Not investment advice" in block["disclaimer"]
    assert block["disclaimer_hideable"] is False


def test_fee_db_for_yield(isolated_seed):
    block = dvf.get_dex_volume_for_asset("UNI")
    assert block is not None
    assert block["yield_fee_context"] is not None
    assert "Fees generated:" in block["yield_fee_context"]["display"]
    assert block["yield_fee_context"]["fee_db"]["fee_db_feature_id"] == 130


def test_no_fee_db_without_yield(isolated_seed):
    block = dvf.get_dex_volume_for_asset("ETH")
    assert block is not None
    assert block["yield_fee_context"] is None


def test_asset_metadata_integration(isolated_seed, tmp_path, monkeypatch):
    assets_seed = tmp_path / "canonical_assets_seed.json"
    assets_seed.write_text(
        json.dumps([{
            "stable_id": "asset:eth:ethereum",
            "symbol": "ETH",
            "name": "Ethereum",
            "lifecycle": "active",
            "lifecycle_version": 1,
            "chain": "ethereum",
            "canonical": True,
            "aliases": ["ETH"],
        }]),
        encoding="utf-8",
    )
    monkeypatch.setattr(car, "_SEED_PATH", assets_seed)
    monkeypatch.setattr(car, "_STORE_PATH", tmp_path / "canonical_assets.json")

    result = car.get_canonical_asset("asset:eth:ethereum")
    assert result["ok"] is True
    assert "dex_volume" in result["asset"]
    assert "#235" in result["asset"]["integrated_features"]


def test_status(isolated_seed):
    status = dvf.dex_volume_feed_status()
    assert status["feature_id"] == 235
    assert status["standalone"] is False
    assert status["merged_into"] == "705_asset_metadata"
    assert status["acceptance_criteria"]["wash_noise_policy"] is True


def test_api_routes(isolated_seed, tmp_path, monkeypatch):
    assets_seed = tmp_path / "canonical_assets_seed.json"
    monkeypatch.setattr(car, "_SEED_PATH", assets_seed)
    monkeypatch.setattr(car, "_STORE_PATH", tmp_path / "canonical_assets.json")
    assets_seed.write_text("[]", encoding="utf-8")

    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/dex-volume/status").status_code == 200
    resp = c.get("/api/platform/connectors/assets/ETH/dex-volume")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "ETH"
    assert "wash_noise_policy" in data


def test_full_seed_exists():
    seed = json.loads(Path("data/dex_volume_feed_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 235
    assert seed["standalone"] is False
    assert len(seed["assets"]) >= 4
