"""Tests — Canonical Data Layer + Asset Metadata (#16 + #29)."""

from __future__ import annotations

import asyncio

import pytest

from blackdark.canonical.layer import CanonicalDataLayer
from blackdark.canonical.registry import all_canonical_assets, registry_stats
from blackdark.canonical.resolver import resolve_asset, resolve_symbol
from blackdark.canonical.schema import make_canonical_id


def test_stable_canonical_id_format():
    assert make_canonical_id("btc") == "bd:BTC"


def test_resolve_symbol_direct():
    assert resolve_symbol("ETH") == "ETH"


def test_resolve_alias_matic_to_pol():
    result = resolve_asset("MATIC")
    assert result.found is True
    assert result.symbol == "POL"
    assert result.canonical_id == "bd:POL"
    assert result.matched_via == "alias"


def test_resolve_trading_pair():
    result = resolve_asset("BTCUSDT")
    assert result.found is True
    assert result.symbol == "BTC"
    assert result.matched_via in {"trading_pair", "pair_base"}


def test_resolve_coingecko_slug():
    result = resolve_asset("ethereum")
    assert result.found is True
    assert result.symbol == "ETH"


def test_resolve_kraken_xbt():
    result = resolve_asset("XBT")
    assert result.found is True
    assert result.symbol == "BTC"


def test_registry_loads_universe():
    assets = all_canonical_assets()
    stats = registry_stats()
    assert len(assets) >= 100
    assert stats["asset_count"] == len(assets)
    symbols = {a.symbol for a in assets}
    assert "BTC" in symbols
    assert "ETH" in symbols


def test_platform_universe_delegates():
    from platform_universe import resolve_asset_symbol

    assert resolve_asset_symbol("MATIC") == "POL"
    assert resolve_asset_symbol("btc") == "BTC"


def test_normalize_oracle_symbol_uses_canonical():
    from market_context import normalize_oracle_symbol

    asset, pair = normalize_oracle_symbol("MATIC/USDT")
    assert asset == "POL"
    assert pair == "MATICUSDT" or pair.endswith("USDT")


@pytest.mark.asyncio
async def test_canonical_layer_ingest_and_query(tmp_path, monkeypatch):
    import config
    import database

    db_path = tmp_path / "canonical.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    await database.init_db()

    layer = CanonicalDataLayer()
    await layer.bootstrap(persist=True)
    ingested = await layer.ingest(
        source="test",
        dataset="reference",
        raw={"symbol": "ETH", "price": 3000},
    )
    assert ingested["canonical_id"] == "bd:ETH"
    assert ingested["resolve_found"] is True

    q = await layer.query(input="ETH", dataset="reference")
    assert q["count"] >= 1
    assert q["canonical_id"] == "bd:ETH"
    assert q["sla_met"] is True


def test_canonical_api(tmp_path, monkeypatch):
    import config
    import database

    db_path = tmp_path / "canonical_api.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    asyncio.run(database.init_db())

    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    r = c.get("/api/platform/canonical/resolve?input=MATIC")
    assert r.status_code == 200
    body = r.json()
    assert body["found"] is True
    assert body["symbol"] == "POL"

    r2 = c.get("/api/platform/canonical/assets?limit=5")
    assert r2.status_code == 200
    assert r2.json()["count"] == 5

    r3 = c.get("/api/platform/canonical/layer/status")
    assert r3.status_code == 200
    assert r3.json()["assets_loaded"] >= 100
