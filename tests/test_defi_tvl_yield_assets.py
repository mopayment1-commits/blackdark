"""Tests — #702 DeFi TVL, #705 Canonical Assets, #709 Yield Sustainability."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import canonical_asset_registry as car
from bd_platform import defi_tvl_engine as dte
from bd_platform import yield_sustainability_score as yss


# ── #702 DeFi TVL Engine ───────────────────────────────────────────────────────


@pytest.fixture
def isolated_tvl(tmp_path, monkeypatch):
    seed = tmp_path / "defi_tvl_seed.json"
    store = tmp_path / "defi_tvl_engine.json"
    seed.write_text(
        json.dumps({
            "methodology": {
                "version": "v2.1",
                "description": "staking tokens counted separately",
                "double_count_policy": "Exclude borrowed tokens",
                "source_primary": "DeFiLlama",
            },
            "protocols": [{
                "id": "aave", "name": "Aave", "chain": "ethereum", "category": "lending",
                "tvl_usd": 10000000000, "tvl_raw_usd": 12000000000,
                "double_count_excluded_usd": 2000000000,
                "double_count_display": "Aave TVL includes borrowed tokens — we exclude them",
                "source": "DeFiLlama", "source_url": "https://defillama.com/aave",
                "methodology_version": "v2.1",
            }],
            "chains": [{"chain": "ethereum", "tvl_usd": 50000000000, "protocol_count": 10, "source": "DeFiLlama"}],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(dte, "_SEED_PATH", seed)
    monkeypatch.setattr(dte, "_STORE_PATH", store)
    return store


def test_double_count_policy_display(isolated_tvl):
    dash = dte.build_tvl_dashboard()
    proto = dash["protocols"][0]
    assert "borrowed tokens" in proto["double_count_display"].lower()
    assert dash["double_count_policy"]


def test_methodology_versioned(isolated_tvl):
    meth = dte.get_methodology()
    assert meth["version"] == "v2.1"
    assert "v2.1" in meth["display"]


def test_source_metadata(isolated_tvl):
    proto = dte.get_protocol_tvl("aave")["protocol"]
    assert proto["source_metadata"]["primary"] == "DeFiLlama"
    assert "Source:" in proto["source_line"]


def test_market_radar_defi_layer(isolated_tvl):
    dash = dte.build_tvl_dashboard()
    assert dash["surface"] == "market_radar_defi_layer"
    assert dash["protocols"][0]["market_radar_layer"] == "defi"


# ── #705 Canonical Asset Registry (merged #194) ────────────────────────────────


@pytest.fixture
def isolated_assets(tmp_path, monkeypatch):
    seed = tmp_path / "canonical_assets_seed.json"
    store = tmp_path / "canonical_assets.json"
    seed.write_text(
        json.dumps([
            {"stable_id": "asset:eth:ethereum", "symbol": "ETH", "name": "Ethereum",
             "lifecycle": "active", "lifecycle_version": 1, "chain": "ethereum",
             "canonical": True, "aliases": ["ETH", "WETH"]},
            {"stable_id": "asset:eth-old:ethereum", "symbol": "ETH-OLD", "name": "Legacy ETH",
             "lifecycle": "deprecated", "lifecycle_version": 0, "chain": "ethereum",
             "canonical": False, "aliases": ["ETH-OLD"], "replaced_by": "asset:eth:ethereum"},
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(car, "_SEED_PATH", seed)
    monkeypatch.setattr(car, "_STORE_PATH", store)
    return store


def test_not_standalone_metadata_layer(isolated_assets):
    status = car.canonical_asset_registry_status()
    assert status["standalone"] is False
    assert status["parent_feature"] == 194


def test_stable_id_resolution(isolated_assets):
    result = car.resolve_asset("ETH")
    assert result["stable_id"] == "asset:eth:ethereum"
    assert result["lifecycle"] == "active"


def test_deprecated_lifecycle(isolated_assets):
    result = car.resolve_asset("ETH-OLD")
    assert result["is_deprecated"] is True
    assert result["lifecycle"] == "deprecated"


def test_lifecycle_versioning(isolated_assets):
    assets = car.list_canonical_assets()
    eth = next(a for a in assets["assets"] if a["symbol"] == "ETH")
    assert "Lifecycle:" in eth["lifecycle_display"]


# ── #709 Yield Sustainability Score ────────────────────────────────────────────


@pytest.fixture
def isolated_yield(tmp_path, monkeypatch):
    seed = tmp_path / "yield_history_seed.json"
    store = tmp_path / "yield_sustainability.json"
    seed.write_text(
        json.dumps([
            {
                "id": "stable-pool", "protocol": "Aave", "pool": "ETH", "chain": "ethereum",
                "current_apy_pct": 3.2, "apy_30d_avg_pct": 3.1, "apy_30d_std_pct": 0.15,
                "apy_history_30d": [3.0, 3.1, 3.2], "fee_share_pct": 75, "incentive_share_pct": 25,
                "tvl_usd": 1000000000, "outlier_flag": False, "source": "DeFiLlama Yields",
            },
            {
                "id": "volatile-pool", "protocol": "NewFarm", "pool": "USDC", "chain": "arbitrum",
                "current_apy_pct": 85.0, "apy_30d_avg_pct": 42.0, "apy_30d_std_pct": 28.5,
                "apy_history_30d": [12, 85, 90], "fee_share_pct": 20, "incentive_share_pct": 80,
                "tvl_usd": 10000000, "outlier_flag": True, "source": "DeFiLlama Yields",
            },
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(yss, "_SEED_PATH", seed)
    monkeypatch.setattr(yss, "_STORE_PATH", store)
    return store


def test_yield_display_format(isolated_yield):
    pool = yss.get_yield_pool("stable-pool")["pool"]
    assert "Current APY:" in pool["yield_display"]
    assert "30-day avg:" in pool["yield_display"]
    assert "fees" in pool["yield_display"]


def test_incentive_decomposition(isolated_yield):
    pool = yss.get_yield_pool("stable-pool")["pool"]
    decomp = pool["incentive_decomposition"]
    assert decomp["fee_share_pct"] == 75
    assert decomp["incentive_share_pct"] == 25


def test_outlier_flag(isolated_yield):
    pool = yss.get_yield_pool("volatile-pool")["pool"]
    assert pool["outlier_detected"] is True
    assert pool["sustainability"] in ("low", "critical")


def test_time_series_stability(isolated_yield):
    stable = yss.get_yield_pool("stable-pool")["pool"]
    volatile = yss.get_yield_pool("volatile-pool")["pool"]
    assert stable["time_series_stability"] == "stable"
    assert volatile["time_series_stability"] == "volatile"


def test_merged_features(isolated_yield):
    status = yss.yield_sustainability_status()
    assert 709 in status["merged_features"]
    assert 198 in status["merged_features"]
    assert 710 not in status["merged_features"]


def test_full_seeds_exist():
    tvl = json.loads(Path("data/defi_tvl_seed.json").read_text(encoding="utf-8"))
    assets = json.loads(Path("data/canonical_assets_seed.json").read_text(encoding="utf-8"))
    yields = json.loads(Path("data/yield_history_seed.json").read_text(encoding="utf-8"))
    assert len(tvl["protocols"]) >= 5
    assert len(assets) >= 8
    assert len(yields) >= 5


def test_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)

    tvl = c.get("/api/platform/market-radar/defi/tvl/status")
    assert tvl.status_code == 200
    assert tvl.json()["feature_id"] == 702

    assets = c.get("/api/platform/connectors/assets/status")
    assert assets.status_code == 200
    assert assets.json()["standalone"] is False

    yld = c.get("/api/platform/defi/yield-sustainability/status")
    assert yld.status_code == 200
    assert 709 in yld.json()["merged_features"]
