"""Tests — #323 merged into #289 + #327 Derivatives Market State Module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import alert_engine as ae
from bd_platform import derivatives_market_state as dms


@pytest.fixture
def alert_seed(tmp_path, monkeypatch):
    p = tmp_path / "alert_engine_seed.json"
    p.write_text(json.dumps({
        "current_phase": 1,
        "rules": [],
        "derivatives_rules": [
            {
                "rule_id": "d1",
                "name": "BTC funding",
                "asset": "BTC",
                "metric": "funding_rate",
                "condition": {"operator": ">=", "threshold": 0.0005},
                "current_value": 0.0008,
                "anomaly_input_enabled": True,
            },
        ],
        "delivery_log": [],
    }), encoding="utf-8")
    monkeypatch.setattr(ae, "_SEED_PATH", p)
    return p


@pytest.fixture
def dms_seed(tmp_path, monkeypatch):
    p = tmp_path / "derivatives_market_state_seed.json"
    p.write_text(json.dumps({
        "backtest": {
            "historical_events_tested": 10,
            "regime_accuracy_pct": 75,
            "false_positive_rate_pct": 25,
        },
        "assets": {
            "BTC": {
                "components": {
                    "funding_rate": 0.0005,
                    "funding_z": 2.5,
                    "oi_change_pct": 10,
                    "oi_z": 2.0,
                    "leverage_ratio": 1.5,
                    "leverage_ratio_source": "Binance API v3",
                    "liquidation_usd_24h": 50000000,
                    "liquidation_z": 2.8,
                    "price_change_24h_pct": 2.0,
                    "funding_rate_source": "Binance API v3",
                    "open_interest_usd": 1e10,
                    "exchange_reserve_usd": 8e9,
                    "reserve_qa": {"verified": True},
                    "elr_history_90d": [1.0, 1.1, 1.2],
                },
                "baselines": {
                    "funding_rate": {"mean": 0.0001, "std": 0.0002},
                    "oi_change_pct": {"mean": 2, "std": 4},
                    "leverage_ratio": {"mean": 1.2, "std": 0.2},
                    "liquidation_usd_24h": {"mean": 1e7, "std": 1e7},
                    "price_change_24h_pct": {"mean": 0, "std": 2},
                },
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(dms, "_SEED_PATH", p)
    return p


def test_323_merged_no_separate_engine(alert_seed):
    config = ae.build_derivatives_alert_rules()
    assert config["no_separate_engine"] is True
    assert config["absorbed_feature_id"] == 323
    assert "oi_change_pct" in config["metrics"]


def test_323_dedupe_and_anomaly(alert_seed):
    result = ae.evaluate_derivatives_rule(
        {
            "rule_id": "d1", "name": "t", "asset": "BTC", "metric": "funding_rate",
            "condition": {"operator": ">=", "threshold": 0.0005},
            "current_value": 0.0008,
            "anomaly_input_enabled": True,
        },
        market={"flow_anomaly_detected": True},
    )
    assert result["triggered"] is True
    assert result["anomaly_integration"]["flow_anomaly_feature_id"] == 282
    assert result["dedupe_key"] == "BTC:funding_rate:>=:0.0005"


def test_323_list_derivatives_rules(alert_seed):
    rules = ae.list_derivatives_alert_rules(asset="BTC")
    assert rules["absorbed_feature_id"] == 323
    assert rules["count"] == 1


def test_327_no_opaque_score(dms_seed):
    panel = dms.build_derivatives_market_state_panel("BTC")
    score = panel["market_state_score"]
    assert score["no_opaque_score"] is True
    assert score["formula"]["black_box"] is False
    assert len(score["contributors"]) == 5


def test_327_regime_detection(dms_seed):
    panel = dms.build_derivatives_market_state_panel("BTC")
    assert panel["regime"]["regime"] in ("crowded", "flush", "normal")
    assert panel["regime"]["rule_based"] is True
    assert panel["regime"]["sub_component"] == "Regime Classification Sub-component"


def test_327_leverage_absorbed(dms_seed):
    panel = dms.build_derivatives_market_state_panel("BTC")
    lev = panel["leverage_ratio"]
    assert lev["sub_task"] == "#329"
    assert lev["formula"] == "ELR = OI / Exchange Reserve"
    assert lev["standalone_rejected"] is True


def test_327_backtest_gate(dms_seed):
    gate = dms.build_backtest_gate()
    assert gate["false_positive_gate"] is True
    assert gate["gate_passed"] is True


def test_327_scope_perpetuals(dms_seed):
    scope = dms.build_scope_lock()
    assert scope["perpetuals_only"] is True
    assert scope["options"] == "Phase 3"


def test_api_routes(alert_seed, dms_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/alert-engine/derivatives-rules").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/derivatives-market-state/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/derivatives-market-state?asset=BTC").status_code == 200


def test_full_seeds_exist():
    alert = json.loads(Path("data/alert_engine_seed.json").read_text())
    assert "323" in alert.get("absorbed_tickets", {})
    dms_data = json.loads(Path("data/derivatives_market_state_seed.json").read_text())
    assert dms_data["feature_id"] == 327
