"""Tests — Protocol Valuation Layer epic #570 #571."""

from __future__ import annotations

import json

import pytest

from bd_platform import protocol_valuation_layer as pvl


@pytest.fixture
def valuation_seed(tmp_path, monkeypatch):
    p = tmp_path / "protocol_valuation_layer_seed.json"
    p.write_text(json.dumps({
        "formula": {
            "expression": "nvt = network_value / transfer_volume",
            "variants": {
                "nvt_entity_adjusted": {"window_days": 30, "transfer_type": "entity_adjusted"},
                "nvt_90d": {"window_days": 90, "transfer_type": "entity_adjusted"},
            },
        },
        "assets": {
            "bitcoin": {
                "name": "Bitcoin",
                "network_value_usd": 1000000000,
                "entity_adjusted_transfers": {"volume_30d_usd": 100000000},
                "raw_transfers": {"volume_30d_usd": 120000000},
                "entity_adjusted_transfers_90d": {"volume_90d_usd": 300000000},
                "historical_nvt": [5, 8, 10, 12, 15, 18, 20, 7, 9, 11],
                "historical_nvt_90d": [6, 9, 12, 15, 18, 8, 10],
            },
        },
        "backtest": {"periods_tested": 24, "percentile_accuracy_pct": 92},
    }), encoding="utf-8")
    monkeypatch.setattr(pvl, "_SEED_PATH", p)
    return p


def test_epic_status_merged(valuation_seed):
    status = pvl.protocol_valuation_layer_status()
    assert status["standalone_rejected"] is True
    assert set(status["feature_ids"]) == {570, 571}
    assert status["dependencies"]["entity_adjusted_feature_id"] == 542


def test_570_nvt_ratio_not_fair_value(valuation_seed):
    ctx = pvl.build_nvt_ratio_context("bitcoin")
    assert ctx["ok"] is True
    assert ctx["current_nvt"] == 10.0
    assert ctx["no_fair_value_claim"] is True
    assert ctx["no_price_guarantee"] is True
    assert "Current NVT:" in ctx["display"]
    assert "Historical percentile:" in ctx["display"]
    assert "fair value" not in ctx["display"].lower()


def test_entity_adjusted_preferred(valuation_seed):
    ctx = pvl.build_nvt_ratio_context("bitcoin", entity_adjusted=True)
    assert ctx["entity_adjusted"] is True
    assert ctx["entity_adjusted_preferred"] is True


def test_571_nvt_variants(valuation_seed):
    variants = pvl.build_nvt_variants("bitcoin")
    assert variants["ok"] is True
    assert variants["variant_count"] >= 2
    assert variants["formula_documented"] is True
    assert variants["no_arbitrary_valuation_claim"] is True


def test_main_panel(valuation_seed):
    panel = pvl.build_protocol_valuation_panel("bitcoin")
    assert panel["ok"] is True
    assert "570_nvt_ratio_historical_context" in panel["sub_modules"]
    assert "571_nvt_variants" in panel["sub_modules"]
    assert panel["renamed_from"]["570"] == "NVT Fair-Value Model"


def test_reconciliation_tests(valuation_seed):
    result = pvl.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["all_passed"] is True


def test_api_routes(valuation_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/data-layer/protocol-valuation/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/data-layer/protocol-valuation?asset_id=bitcoin").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/data-layer/protocol-valuation/reconciliation-tests").status_code == 200
