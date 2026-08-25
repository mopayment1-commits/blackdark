"""Tests — #274+#275+#276 Options Intelligence Module merged (Wave 3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import options_intelligence as oi


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "options_intelligence_seed.json"
    seed.write_text(
        json.dumps({
            "dependency_gate": {
                "spot_data_stable": True,
                "perp_data_stable": True,
                "sprint1_stable": True,
                "stability_days_required": 30,
                "stability_days_met": 30,
            },
            "current_phase": 1,
            "mapping_audit": {"total_instruments": 100, "mapped_correctly": 99},
            "iv_surface": {
                "model": "black_scholes_merton",
                "model_documented": True,
                "risk_free_rate": 0.05,
                "spot_price": 95000,
            },
            "instruments": {
                "BTC-26DEC25-100000-C": {
                    "mark_iv": 0.52,
                    "open_interest": 1250.5,
                    "exchange_oi": 1250.5,
                    "volume_24h": 89.2,
                    "time_to_expiry_years": 0.35,
                    "greeks": {
                        "delta": 0.45,
                        "gamma": 0.000012,
                        "theta": -12.5,
                        "vega": 85.2,
                        "source": "exchange",
                    },
                },
                "BTC-26DEC25-100000-P": {
                    "mark_iv": 0.54,
                    "open_interest": 980.3,
                    "exchange_oi": 980.3,
                    "volume_24h": 62.1,
                    "time_to_expiry_years": 0.35,
                    "greeks": {"source": "calculated"},
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(oi, "_SEED_PATH", seed)
    return seed


def test_parse_deribit_instrument():
    parsed = oi.parse_deribit_instrument("BTC-26DEC25-100000-C")
    assert parsed is not None
    assert parsed["currency"] == "BTC"
    assert parsed["expiry"] == "2025-12-26"
    assert parsed["strike"] == 100000.0
    assert parsed["option_type"] == "call"


def test_dependency_gate(isolated_seed):
    gate = oi.check_dependency_gate()
    assert gate["gate_passed"] is True
    assert gate["spot_data_stable"] is True
    assert gate["perp_data_stable"] is True
    assert "Wave 3" in gate["display"]


def test_dependency_gate_blocked(isolated_seed):
    seed = json.loads(isolated_seed.read_text(encoding="utf-8"))
    seed["dependency_gate"]["spot_data_stable"] = False
    isolated_seed.write_text(json.dumps(seed), encoding="utf-8")
    gate = oi.check_dependency_gate()
    assert gate["gate_passed"] is False
    assert gate["blocked_if_not_met"] is True


def test_scope_lock_deribit_only(isolated_seed):
    scope = oi.build_scope_lock()
    assert scope["current_phase"] == 1
    assert scope["phase_1_exchange"] == "deribit"
    assert scope["no_tradfi_equity_options"] is True
    assert "Deribit" in scope["display"]


def test_expiry_strike_mapping_accuracy(isolated_seed):
    seed = json.loads(isolated_seed.read_text(encoding="utf-8"))
    mapping = oi.build_expiry_strike_mapping(
        seed["instruments"],
        audit=seed["mapping_audit"],
    )
    assert mapping["mapping_accuracy_pct"] == 99.0
    assert mapping["meets_accuracy_threshold"] is True
    assert mapping["mapped_count"] == 2
    assert "2025-12-26" in mapping["by_expiry"]


def test_iv_surface_documented(isolated_seed):
    surface = oi.build_iv_surface()
    assert surface["model"] == "black_scholes_merton"
    assert surface["model_documented"] is True
    assert surface["surface_points"] == 2
    assert "Black-Scholes" in surface["model_formula"]


def test_oi_verification(isolated_seed):
    oi_check = oi.build_oi_verification()
    assert oi_check["verified_count"] == 2
    assert oi_check["exchange_verified"] is True


def test_greeks_exchange_and_calculated(isolated_seed):
    seed = json.loads(isolated_seed.read_text(encoding="utf-8"))
    surface_cfg = seed["iv_surface"]
    call_data = seed["instruments"]["BTC-26DEC25-100000-C"]
    parsed = oi.parse_deribit_instrument("BTC-26DEC25-100000-C")
    exchange_greeks = oi.build_greeks_block(call_data, parsed=parsed, surface_cfg=surface_cfg)
    assert exchange_greeks["source"] == "exchange"
    assert exchange_greeks["formula_documented"] is True

    put_data = seed["instruments"]["BTC-26DEC25-100000-P"]
    parsed_put = oi.parse_deribit_instrument("BTC-26DEC25-100000-P")
    calc_greeks = oi.build_greeks_block(put_data, parsed=parsed_put, surface_cfg=surface_cfg)
    assert calc_greeks["source"] == "calculated"
    assert calc_greeks["formula"] == "black_scholes_merton"


def test_data_layer_275(isolated_seed):
    layer = oi.build_data_layer()
    assert layer["sub_task"] == "#275"
    assert layer["provider"] == "deribit"
    assert "expiry_strike_mapping" in layer
    assert "iv_surface" in layer
    assert "oi_verification" in layer


def test_volume_layer_276(isolated_seed):
    layer = oi.build_volume_layer()
    assert layer["sub_task"] == "#276"
    assert layer["total_volume_24h"] == pytest.approx(151.3)
    assert "2025-12-26" in layer["by_expiry"]


def test_panel_ok(isolated_seed):
    result = oi.build_options_intelligence_panel("BTC")
    assert result["ok"] is True
    assert result["feature_ids"] == [274, 275, 276]
    assert result["standalone"] is False
    assert result["wave"] == 3
    assert result["data_layer"]["sub_task"] == "#275"
    assert result["volume_layer"]["sub_task"] == "#276"
    assert result["dashboard_deferred"] is True


def test_panel_blocked_when_gate_fails(isolated_seed):
    seed = json.loads(isolated_seed.read_text(encoding="utf-8"))
    seed["dependency_gate"]["perp_data_stable"] = False
    isolated_seed.write_text(json.dumps(seed), encoding="utf-8")
    result = oi.build_options_intelligence_panel("BTC")
    assert result["ok"] is False
    assert result["error"] == "dependency_gate_not_met"


def test_not_standalone(isolated_seed):
    status = oi.options_intelligence_status()
    assert status["feature_ids"] == [274, 275, 276]
    assert status["standalone"] is False
    assert status["wave"] == 3
    assert status["cluster"]["275"] == "data normalization layer"
    assert status["acceptance_criteria"]["scope_lock_deribit_phase1"] is True


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/options/status").status_code == 200
    resp = c.get("/api/platform/intelligence-ledger/options?currency=BTC")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["expiry_strike_mapping"]["meets_accuracy_threshold"] is True


def test_full_seed_exists():
    seed = json.loads(Path("data/options_intelligence_seed.json").read_text(encoding="utf-8"))
    assert 274 in seed["feature_ids"]
    assert seed["dependency_gate"]["spot_data_stable"] is True
    assert seed["mapping_audit"]["mapped_correctly"] / seed["mapping_audit"]["total_instruments"] >= 0.99
