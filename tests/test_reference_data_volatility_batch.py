"""Tests — #394 Reference Data Registry, #395 Normalization, #501 Volatility Regime."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import cross_asset_volatility_regime as cavr
from bd_platform import market_data_engine as mde
from bd_platform import reference_data_registry as rdr


@pytest.fixture
def rdr_seed(tmp_path, monkeypatch):
    p = tmp_path / "reference_data_registry_seed.json"
    p.write_text(json.dumps({
        "assets": {
            "asset_btc": {
                "canonical_id": "asset_btc", "symbol": "BTC", "version": "1.0",
                "lifecycle_status": "active", "mappings": [],
            },
        },
        "exchanges": {
            "exchange_binance": {
                "canonical_id": "exchange_binance", "name": "Binance",
                "version": "1.0", "lifecycle_status": "active", "mappings": [],
            },
        },
        "mappings": [{
            "mapping_id": "m1", "canonical_id": "asset_btc", "source_id": "BTC",
            "source": "binance", "mapping_version": "1.0", "entity_type": "asset",
        }],
    }), encoding="utf-8")
    monkeypatch.setattr(rdr, "_SEED_PATH", p)
    return p


@pytest.fixture
def mde_seed(tmp_path, monkeypatch):
    p = tmp_path / "market_data_engine_seed.json"
    p.write_text(json.dumps({
        "normalization": {
            "BTC": {
                "spot": {"canonical_id": "asset_btc", "venue": "binance", "symbol": "BTCUSDT"},
                "derivatives": [{
                    "canonical_id": "inst1", "venue": "binance", "contract_type": "perp",
                    "symbol": "BTCUSDT", "contract_specs_validated": True, "asset_mismatch": False,
                }],
            },
        },
        "venues": {}, "provider_semantics": {}, "weighting": {},
    }), encoding="utf-8")
    monkeypatch.setattr(mde, "_SEED_PATH", p)
    return p


@pytest.fixture
def vol_seed(tmp_path, monkeypatch):
    p = tmp_path / "cross_asset_volatility_regime_seed.json"
    p.write_text(json.dumps({
        "legal_review": {"complete": True},
        "formula": {"thresholds": {"low_regime_percentile": 33, "high_regime_percentile": 67}},
        "backtest": {"events_tested": 10, "regime_accuracy_pct": 70},
        "assets": {
            "BTC": {
                "historical_volatility_percentile": 42,
                "realized_volatility": 0.045, "realized_vol_annualized_pct": 45,
                "atr": 100, "return_30d_pct": 5, "volume_24h_usd": 1e10,
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(cavr, "_SEED_PATH", p)
    return p


def test_394_internal_registry(rdr_seed):
    status = rdr.reference_data_registry_status()
    assert status["internal_only"] is True
    assert status["user_facing"] is False
    assert status["no_external_api_product"] is True
    assert status["wave"] == 0
    assert status["priority"] == "highest"
    assert status["acceptance_criteria"]["stable_ids_mandatory"] is True


def test_394_stable_ids_and_mappings(rdr_seed):
    entry = rdr.build_asset_entry("asset_btc")
    assert entry["stable_id"]["stable_id"] is True
    assert entry["lifecycle"]["corporate_token_lifecycle_handling"] is True
    lookup = rdr.lookup_canonical_id(source="binance", source_id="BTC")
    assert lookup["ok"] is True
    assert lookup["canonical_id"] == "asset_btc"
    assert lookup["mapping"]["versioned_mappings"] is True


def test_395_normalization_absorbed(mde_seed):
    layer = mde.build_market_data_normalization_layer("BTC")
    assert layer["sub_task"] == "#395"
    assert layer["title"] == "Market Data Normalization Layer"
    assert layer["standalone_rejected"] is True
    assert layer["contract_specs_validated"] is True
    assert layer["no_asset_mismatch"] is True
    assert layer["no_coverage_as_product"] is True


def test_501_renamed_no_scoring(vol_seed):
    panel = cavr.build_cross_asset_volatility_panel("BTC")
    assert panel["renamed_from"] == "Volatility_Scoring_System"
    assert panel["no_scoring_in_name"] is True
    assert panel["no_scoring_in_output"] is True
    analysis = panel["analysis"]
    assert analysis["no_risk_score_output"] is True
    assert "Historical Volatility Percentile" in analysis["percentile_display"]
    assert analysis["regime_classification"]["historical_regime_only"] is True
    assert analysis["regime_classification"]["no_advisory_language"] is True


def test_501_formula_and_legal_review(vol_seed):
    panel = cavr.build_cross_asset_volatility_panel("BTC")
    assert panel["formula"]["no_scoring_terminology"] is True
    assert panel["formula"]["cross_asset_normalization"] is True
    assert panel["legal_review_gate"]["legal_review_mandatory"] is True
    assert panel["rule_based_only"] is True
    assert panel["ml_deferred"] is True


def test_api_routes(rdr_seed, mde_seed, vol_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/internal/reference-data-registry/status").status_code == 200
    assert c.get("/api/platform/internal/reference-data-registry/lookup?source=binance&source_id=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/market-radar/market-data-normalization?asset=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/data-layer/volatility-regime/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/data-layer/volatility-regime?asset=BTC").status_code == 200


def test_full_seeds_exist():
    rdr_data = json.loads(Path("data/reference_data_registry_seed.json").read_text())
    assert rdr_data["wave"] == 0
    assert rdr_data["internal_only"] is True
    mde_data = json.loads(Path("data/market_data_engine_seed.json").read_text())
    assert "395" in mde_data.get("absorbed_tickets", {})
    vol_data = json.loads(Path("data/cross_asset_volatility_regime_seed.json").read_text())
    assert vol_data["renamed_from"] == "Volatility_Scoring_System"
