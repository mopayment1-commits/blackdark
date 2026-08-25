"""Tests — #246 Futures Volume Intelligence merged into #705 Asset Metadata."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import canonical_asset_registry as car
from bd_platform import futures_volume_intelligence as fvi


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "futures_volume_intelligence_seed.json"
    seed.write_text(
        json.dumps({
            "methodology_version": "1.2",
            "venue_count": 15,
            "last_updated": "2026-08-25",
            "last_updated_utc": "2026-08-25T20:15:00+00:00",
            "global_excluded_venues": ["Deribit (options-only)"],
            "assets": {
                "BTC": {
                    "volume_24h_usd": 42500000000,
                    "spot_volume_usd": 18200000000,
                    "price_usd": 108500,
                    "contracts_count": 392000,
                    "trend": "up",
                    "contracts": [
                        {
                            "symbol": "BTC-USDT-Perp",
                            "venue": "Binance",
                            "contract_size": 1,
                            "unit": "USDT-margined",
                            "notional_usd": 14875000000,
                            "mapping_validated": True,
                        },
                    ],
                    "venues": {
                        "Binance Futures": 12750000000,
                        "Bybit": 10625000000,
                        "OKX": 8500000000,
                        "CME": 6375000000,
                        "BitMEX": 4250000000,
                    },
                    "excluded_venues": ["Deribit (options-only)"],
                    "contract_types": {
                        "Perpetual": 36125000000,
                        "Quarterly": 5100000000,
                        "Monthly": 1275000000,
                    },
                    "oi_context": {
                        "volume_24h_usd": 42500000000,
                        "open_interest_usd": 28500000000,
                        "oi_change_pct": 3.2,
                        "funding_rate_pct": -0.0085,
                    },
                    "historical": {
                        "7d_usd": 289000000000,
                        "30d_usd": 1240000000000,
                        "trend_pct": 12.0,
                        "venue_leader": "Binance",
                        "venue_leader_pct": 35,
                    },
                    "basis_context": {
                        "funding_rate_pct": -0.01,
                        "net_after_funding_7d_pct": 0.42,
                    },
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(fvi, "_SEED_PATH", seed)
    return seed


def test_contract_mapping_validated(isolated_seed):
    asset = json.loads(isolated_seed.read_text())["assets"]["BTC"]
    mapping = fvi.build_contract_mapping(asset["contracts"])
    assert mapping["all_validated"] is True
    assert mapping["no_volume_without_mapping"] is True
    assert "Mapping Validated: Yes" in mapping["entries"][0]["display"]
    assert "USDT-margined" in mapping["entries"][0]["display"]


def test_venue_coverage_disclosed(isolated_seed):
    asset = json.loads(isolated_seed.read_text())["assets"]["BTC"]
    venues = fvi.build_venue_coverage(asset["venues"], excluded=asset["excluded_venues"])
    assert venues["venue_coverage_disclosed"] is True
    assert "Binance Futures" in venues["display"]
    assert "Excluded: Deribit" in venues["display"]
    assert "Total:" in venues["display"]


def test_notional_mapping(isolated_seed):
    notional = fvi.build_notional_mapping(392000, 108500, 42500000000)
    assert "Notional:" in notional["display"]
    assert "contracts" in notional["display"]
    assert notional["notional_not_contracts_only"] is True


def test_spot_futures_separation(isolated_seed):
    sep = fvi.build_spot_futures_separation(42500000000, 18200000000)
    assert "Futures Volume:" in sep["display"]
    assert "Spot Volume:" in sep["display"]
    assert "Futures/Spot Ratio:" in sep["display"]
    assert sep["spot_futures_separated"] is True


def test_oi_context(isolated_seed):
    asset = json.loads(isolated_seed.read_text())["assets"]["BTC"]
    oi = fvi.build_oi_context(asset["oi_context"])
    assert "Volume:" in oi["display"]
    assert "OI:" in oi["display"]
    assert "OI Change:" in oi["display"]
    assert "Funding:" in oi["display"]


def test_contract_type_separation(isolated_seed):
    asset = json.loads(isolated_seed.read_text())["assets"]["BTC"]
    types = fvi.build_contract_type_breakdown(asset["contract_types"])
    assert "Perpetual:" in types["display"]
    assert "Quarterly:" in types["display"]
    assert "Monthly:" in types["display"]
    assert types["contract_types_separated"] is True


def test_historical_trend_dashboard(isolated_seed):
    asset = json.loads(isolated_seed.read_text())["assets"]["BTC"]
    trend = fvi.build_historical_trend(asset["historical"])
    assert "7D Volume:" in trend["display"]
    assert "30D:" in trend["display"]
    assert "Venue Leader:" in trend["display"]
    assert trend["dashboard_not_snapshot_only"] is True


def test_methodology_versioned(isolated_seed):
    meth = fvi.build_methodology_block(json.loads(isolated_seed.read_text()))
    assert "Futures Volume Methodology v1.2" in meth["display"]
    assert "Venues: 15" in meth["display"]


def test_update_schedule(isolated_seed):
    sched = fvi.build_update_schedule(json.loads(isolated_seed.read_text()))
    assert "Every 5 minutes" in sched["display"]
    assert "Exchange APIs" in sched["display"]
    assert sched["no_instant_claim"] is True


def test_no_opportunity_language(isolated_seed):
    block = fvi.get_futures_volume_for_asset("BTC")
    assert block is not None
    assert "Futures Volume (24H):" in block["volume_display"]
    assert block["no_opportunity_language"] is True
    assert "enter long" not in block["volume_display"].lower()


def test_disclaimer_non_hideable(isolated_seed):
    block = fvi.get_futures_volume_for_asset("BTC")
    assert block is not None
    assert "exchange-reported data" in block["disclaimer"]
    assert block["disclaimer_hideable"] is False


def test_fee_db_for_basis(isolated_seed):
    block = fvi.get_futures_volume_for_asset("BTC")
    assert block is not None
    assert block["basis_fee_context"] is not None
    assert "Funding:" in block["basis_fee_context"]["display"]
    assert block["basis_fee_context"]["fee_db"]["fee_db_feature_id"] == 130


def test_dashboard(isolated_seed):
    dash = fvi.get_futures_volume_dashboard()
    assert dash["ok"] is True
    assert dash["surface"] == "futures_volume_dashboard"
    assert dash["asset_count"] >= 1
    assert "venue_coverage" in dash


def test_asset_metadata_integration(isolated_seed, tmp_path, monkeypatch):
    assets_seed = tmp_path / "canonical_assets_seed.json"
    assets_seed.write_text(
        json.dumps([{
            "stable_id": "asset:btc:bitcoin",
            "symbol": "BTC",
            "name": "Bitcoin",
            "lifecycle": "active",
            "lifecycle_version": 1,
            "chain": "bitcoin",
            "canonical": True,
            "aliases": ["BTC"],
        }]),
        encoding="utf-8",
    )
    monkeypatch.setattr(car, "_SEED_PATH", assets_seed)
    monkeypatch.setattr(car, "_STORE_PATH", tmp_path / "canonical_assets.json")

    result = car.get_canonical_asset("asset:btc:bitcoin")
    assert result["ok"] is True
    assert "futures_volume" in result["asset"]
    assert "#246" in result["asset"]["integrated_features"]


def test_status(isolated_seed):
    status = fvi.futures_volume_intelligence_status()
    assert status["feature_id"] == 246
    assert status["replaces"] == 245
    assert status["standalone"] is False
    assert status["acceptance_criteria"]["contract_unit_mapping_validated"] is True


def test_api_routes(isolated_seed, tmp_path, monkeypatch):
    assets_seed = tmp_path / "canonical_assets_seed.json"
    monkeypatch.setattr(car, "_SEED_PATH", assets_seed)
    monkeypatch.setattr(car, "_STORE_PATH", tmp_path / "canonical_assets.json")
    assets_seed.write_text("[]", encoding="utf-8")

    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/futures-volume/status").status_code == 200
    assert c.get("/api/platform/futures-volume/dashboard").status_code == 200
    resp = c.get("/api/platform/connectors/assets/BTC/futures-volume")
    assert resp.status_code == 200
    assert resp.json()["symbol"] == "BTC"


def test_full_seed_exists():
    seed = json.loads(Path("data/futures_volume_intelligence_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 246
    assert seed["replaces"] == 245
    assert len(seed["assets"]) >= 3
