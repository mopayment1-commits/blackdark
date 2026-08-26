"""Tests — #402 Asset Registry (105-coin Data Engine seed + scoring layer)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import asset_registry as ar
from bd_platform import market_data_engine as mde


@pytest.fixture
def registry_seed(tmp_path, monkeypatch):
    main = Path("data/asset_registry_seed.json")
    p = tmp_path / "asset_registry_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ar, "_SEED_PATH", p)
    return p


def test_402_status_105_assets(registry_seed):
    status = ar.asset_registry_status()
    assert status["feature_id"] == 402
    assert status["standalone"] is False
    assert status["asset_count"] == 105
    assert status["expected_count"] == 105
    assert status["non_custodial"] is True
    assert status["account_data_excluded"] is True
    assert status["oracle_api_delegated"] is True
    assert status["metadata_enrichment"]["sector"] is True
    assert status["scoring_layer"]["risk_score"] is True
    assert status["integrations"]["market_radar"] is True


def test_402_btc_metadata_enrichment(registry_seed):
    panel = ar.build_asset_registry_panel(symbol="BTC")
    assert panel["ok"] is True
    meta = panel["asset"]["metadata"]
    assert meta["sector"] == "Layer 1"
    assert meta["chain"] == "bitcoin"
    assert meta["market_cap_tier"] == "mega"
    assert meta["risk_classification"] == "conservative"
    assert meta["volatility_profile"] == "medium"
    assert panel["asset"]["non_custodial"] is True


def test_402_scoring_layer(registry_seed):
    panel = ar.build_asset_registry_panel(symbol="ETH")
    scoring = panel["asset"]["scoring"]
    assert 0 <= scoring["risk_score"] <= 100
    assert 0 <= scoring["liquidity_score"] <= 100
    assert 0 <= scoring["onchain_health_score"] <= 100
    assert scoring["analytics_only"] is True
    assert scoring["no_investment_advice"] is True


def test_402_pol_matic_alias(registry_seed):
    assert ar.resolve_entity_id("MATIC") == "asset_pol"
    assert ar.resolve_entity_id("POL") == "asset_pol"


def test_402_mkr_sky_alias(registry_seed):
    assert ar.resolve_entity_id("SKY") == "asset_mkr"


def test_402_mana_manta_distinct(registry_seed):
    assert ar.resolve_entity_id("MANA") == "asset_mana"
    assert ar.resolve_entity_id("MANTA") == "asset_manta"


def test_402_universe_panel(registry_seed):
    universe = ar.build_universe_panel()
    assert universe["asset_count"] == 105
    assert universe["assets"][0]["rank"] == 101
    assert universe["assets"][-1]["rank"] == 205
    symbols = {a["symbol"] for a in universe["assets"]}
    assert "BTC" in symbols and "GAL" in symbols


def test_402_market_radar_integration(registry_seed):
    block = ar.build_market_radar_integration()
    assert block["integration"] == "market_radar"
    assert block["universe_size"] == 105
    assert block["screener_ready"] is True


def test_402_portfolio_ai_integration(registry_seed):
    block = ar.build_portfolio_ai_integration("SOL")
    assert block["ok"] is True
    assert block["integration"] == "portfolio_ai"
    assert block["exposure_context"]["sector"] == "Layer 1"
    assert block["non_custodial"] is True


def test_402_intelligence_ledger_integration(registry_seed):
    block = ar.build_intelligence_ledger_integration()
    assert block["entity_count"] == 105
    assert block["entity_id_map"]["BTC"] == "asset_btc"
    assert block["signal_registry_compatible"] is True


def test_402_reconciliation_tests(registry_seed):
    result = ar.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["passed"] == result["total"]
    assert all(c["passed"] for c in result["checks"])


def test_402_market_data_engine_hook(registry_seed):
    status = mde.market_data_engine_status()
    block = status.get("asset_registry") or {}
    assert block.get("feature_id") == 402
    assert block.get("asset_count") == 105


def test_402_api_routes(registry_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/data-layer/asset-registry/status").status_code == 200
    r = c.get("/api/platform/intelligence-ledger/data-layer/asset-registry?symbol=BTC")
    assert r.status_code == 200
    assert r.json()["asset"]["symbol"] == "BTC"
    assert c.get("/api/platform/intelligence-ledger/data-layer/asset-registry/universe").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/market-radar/asset-registry").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/portfolio-ai/asset-registry?symbol=ETH").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/asset-registry").status_code == 200
    tests = c.get("/api/platform/intelligence-ledger/data-layer/asset-registry/reconciliation-tests")
    assert tests.status_code == 200
    assert tests.json()["ok"] is True


def test_402_seed_file_integrity():
    seed = json.loads(Path("data/asset_registry_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 402
    assert seed["asset_count"] == 105
    assert seed["non_custodial"] is True
    assert seed["account_data_excluded"] is True
