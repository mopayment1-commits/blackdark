"""Tests — #247 Gas Cost Engine (Core Infrastructure for Fee DB #130)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import gas_cost_engine as gce


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "gas_cost_engine_seed.json"
    seed.write_text(
        json.dumps({
            "methodology_version": "2.1",
            "last_updated": "2026-08-25",
            "chain_models": {
                "ethereum": {
                    "model_type": "EIP-1559 base fee + priority fee model",
                    "display": "Ethereum: EIP-1559 base fee + priority fee model",
                },
                "bsc": {
                    "model_type": "Fixed priority model",
                    "display": "BSC: Fixed priority model",
                },
            },
            "chains": {
                "ethereum": {
                    "median_cost_usd": 12.50,
                    "calibration": {"actual_vs_predicted_error_pct": 8.2, "last_calibrated_block": 21234500},
                    "spike": {"detected": False, "volatility_sigma": 1.8},
                    "fallback": {
                        "primary_failed": False,
                        "source": "Last 10 blocks median",
                        "median_usd": 12.50,
                        "range_low_usd": 8.20,
                        "range_high_usd": 18.40,
                        "confidence": "Medium",
                    },
                    "percentile_bands": {
                        "expected_usd": 12.50,
                        "p25_usd": 9.80,
                        "p75_usd": 15.20,
                        "p95_usd": 22.50,
                        "confidence": "Medium",
                    },
                    "tx_costs": {
                        "swap": 12.50,
                        "bridge": 28.00,
                        "nft_mint": 45.00,
                        "contract_deploy": 120.00,
                    },
                    "monitoring": {
                        "predicted_usd": 12.50,
                        "actual_usd": 13.52,
                        "variance_pct": 8.2,
                        "drift": "None",
                    },
                    "opportunity_context": {
                        "gross_yield_pct": 8.5,
                        "gas_entry_usd": 12.50,
                        "gas_exit_usd": 12.50,
                        "slippage_usd": 30.00,
                        "notional_usd": 10000,
                    },
                },
                "polygon": {
                    "median_cost_usd": 0.02,
                    "calibration": {"actual_vs_predicted_error_pct": 6.8},
                    "spike": {"detected": True, "volatility_sigma": 3.5},
                    "fallback": {
                        "primary_failed": True,
                        "median_usd": 0.02,
                        "range_low_usd": 0.01,
                        "range_high_usd": 0.08,
                        "confidence": "Low",
                    },
                    "percentile_bands": {"expected_usd": 0.02, "p25_usd": 0.015, "p75_usd": 0.035, "p95_usd": 0.06},
                    "tx_costs": {"swap": 0.02},
                    "monitoring": {"predicted_usd": 0.02, "actual_usd": 0.025, "variance_pct": 25.0, "drift": "Elevated"},
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(gce, "_SEED_PATH", seed)
    return seed


def test_chain_specific_model(isolated_seed):
    eth = gce.get_chain_model("ethereum")
    bsc = gce.get_chain_model("bsc")
    assert "EIP-1559" in eth["display"]
    assert "Fixed priority" in bsc["display"]
    assert eth["chain_specific"] is True


def test_calibration(isolated_seed):
    chain = json.loads(isolated_seed.read_text())["chains"]["ethereum"]
    cal = gce.build_calibration(chain)
    assert "calibrated every 100 blocks" in cal["display"]
    assert cal["within_threshold"] is True


def test_spike_handling(isolated_seed):
    chain = json.loads(isolated_seed.read_text())["chains"]["polygon"]
    spike = gce.detect_gas_spike(chain)
    assert spike["spike_detected"] is True
    assert spike["current_estimate_usd"] is None
    assert "Historical median" in spike["display"]


def test_fallback(isolated_seed):
    chain = json.loads(isolated_seed.read_text())["chains"]["ethereum"]
    fb = gce.build_fallback_estimate(chain)
    assert "Fallback:" in fb["display"]
    assert fb["no_single_number_without_fallback"] is True


def test_percentile_bands(isolated_seed):
    chain = json.loads(isolated_seed.read_text())["chains"]["ethereum"]
    bands = gce.build_percentile_bands(chain["percentile_bands"])
    assert "Expected:" in bands["display"]
    assert "p25:" in bands["display"]
    assert "p95:" in bands["display"]
    assert bands["shows_uncertainty_range"] is True


def test_tx_specific_costs(isolated_seed):
    chain = json.loads(isolated_seed.read_text())["chains"]["ethereum"]
    tx = gce.build_tx_specific_costs(chain["tx_costs"])
    assert "Swap (Uniswap v3):" in tx["display"]
    assert "Bridge:" in tx["display"]
    assert "Contract Deploy:" in tx["display"]


def test_actual_vs_predicted_monitoring(isolated_seed):
    chain = json.loads(isolated_seed.read_text())["chains"]["ethereum"]
    mon = gce.build_actual_vs_predicted(chain["monitoring"])
    assert "Predicted:" in mon["display"]
    assert "Actual:" in mon["display"]
    assert "Variance:" in mon["display"]
    assert mon["weekly_review"] is True


def test_fee_db_net_opportunity(isolated_seed):
    net = gce.build_net_opportunity_impact(
        gross_yield_pct=8.5,
        gas_entry_usd=12.50,
        gas_exit_usd=12.50,
        slippage_usd=30.00,
    )
    assert "Gross Yield:" in net["display"]
    assert "Gas (entry):" in net["display"]
    assert "Net after fees:" in net["display"]
    assert net["fee_db"]["fee_db_feature_id"] == 130
    assert net["no_opportunity_without_gas_impact"] is True


def test_no_guaranteed_profit_language(isolated_seed):
    result = gce.predict_gas_cost("ethereum", tier="pro")
    assert result["ok"] is True
    assert result["no_guaranteed_profit_language"] is True
    assert "مربحة" not in str(result)
    assert "guaranteed" not in str(result).lower() or "no_guaranteed" in str(result)


def test_disclaimer_non_hideable(isolated_seed):
    result = gce.predict_gas_cost("ethereum")
    assert "block builder" in result["disclaimer"]
    assert result["disclaimer_hideable"] is False


def test_pro_tier_gating(isolated_seed):
    free = gce.predict_gas_cost("ethereum", tier="free")
    pro = gce.predict_gas_cost("ethereum", tier="pro")
    assert free["percentile_bands"] is None
    assert pro["percentile_bands"] is not None
    assert pro["tx_specific"] is not None


def test_spike_nulls_estimate_pro(isolated_seed):
    result = gce.predict_gas_cost("polygon", tier="pro")
    assert result["spike"]["spike_detected"] is True
    assert result["estimate_usd"] is None


def test_methodology_versioned(isolated_seed):
    meth = gce.build_methodology_block(json.loads(isolated_seed.read_text()))
    assert "Gas Cost Model v2.1" in meth["display"]
    assert "Fallback: Enabled" in meth["display"]


def test_calibration_monitoring_dashboard(isolated_seed):
    dash = gce.get_calibration_monitoring()
    assert dash["ok"] is True
    assert dash["internal"] is True
    assert len(dash["chains"]) >= 2


def test_status(isolated_seed):
    status = gce.gas_cost_engine_status()
    assert status["feature_id"] == 247
    assert status["core_infrastructure_for"] == 130
    assert status["acceptance_criteria"]["chain_specific_model"] is True
    assert status["cost_calculator_not_profit_calculator"] is True


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/gas-cost/status").status_code == 200
    assert c.get("/api/platform/gas-cost/predict?chain=ethereum&tier=pro").status_code == 200
    assert c.get("/api/platform/gas-cost/monitoring").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/gas_cost_engine_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 247
    assert len(seed["chains"]) >= 4
    assert len(seed["chain_models"]) >= 8
