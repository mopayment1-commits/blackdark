"""Tests — #786/#788 Alert Layer, #789 Infra Observability, #794 Supply Dynamics."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import alert_engine as ae
from bd_platform import infrastructure_observability_stack as ios
from bd_platform import market_radar_indicators as mri
from bd_platform import onchain_metrics_library as oml


@pytest.fixture
def alert_seed():
    return json.loads(Path("data/alert_engine_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def oml_seed():
    return json.loads(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def mri_seed():
    return json.loads(Path("data/market_radar_indicators_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def ios_seed():
    return json.loads(Path("data/infrastructure_observability_stack_seed.json").read_text(encoding="utf-8"))


# --- #786 ---


def test_786_orchestration_backend(alert_seed):
    backend = ae.build_alert_backend_orchestration_786(seed=alert_seed)
    assert backend["no_workflow_engine"] is True
    assert backend["dedupe_cooldown_sec"] == 900
    assert backend["throttle_max_per_hour"] == 10
    assert backend["max_retries"] == 3


def test_786_no_user_surface(alert_seed):
    backend = ae.build_alert_backend_orchestration_786(seed=alert_seed)
    assert backend["no_user_visible_surface"] is True
    assert backend["backend_enforcement"] is True


# --- #788 ---


def test_788_custom_metric_trigger(alert_seed):
    panel = ae.build_custom_metric_alerts_panel_788("default", seed=alert_seed)
    assert panel["ok"] is True
    assert panel["no_smart_alerts"] is True
    triggered = [r for r in panel["rules"] if r.get("triggered")]
    assert len(triggered) >= 1


def test_788_allowed_metrics(alert_seed):
    status = ae.custom_metric_alerts_status_788()
    assert "rsi" in status["allowed_metrics"]
    assert "nvt" in status["allowed_metrics"]
    assert status["cooldown_sec"] == 900


def test_788_dedupe_cooldown(alert_seed):
    rule = {
        "rule_id": "dedupe-test",
        "metric": "rsi",
        "condition": {"field": "rsi_14", "operator": ">=", "threshold": 70},
        "current_value": 72,
        "last_fired_at": _utcnow_recent(),
        "channels": ["in_app"],
    }
    result = ae.evaluate_custom_metric_alert_788(rule, seed=alert_seed)
    assert result.get("dedupe_suppressed") is True


def _utcnow_recent() -> str:
    from datetime import UTC, datetime, timedelta

    return (datetime.now(UTC) - timedelta(minutes=5)).isoformat()


def test_788_delivery_logs(alert_seed):
    logs = ae.list_custom_alert_delivery_logs_788(seed=alert_seed)
    assert logs["delivery_logs_visible"] is True
    assert logs["count"] >= 1


def test_788_manage_pause(alert_seed):
    result = ae.manage_custom_alert_rule_788("cm-001", "pause", seed=alert_seed)
    assert result["ok"] is True
    assert result["action"] == "pause"


def test_788_e2e_suite(alert_seed):
    e2e = ae.run_custom_metric_alerts_e2e_788(seed=alert_seed)
    assert e2e["all_passed"] is True


def test_788_evidence_attached(alert_seed):
    result = ae.evaluate_custom_metric_alert_788(
        alert_seed["custom_metric_alerts_788"]["user_rules"][0],
        seed=alert_seed,
    )
    assert result.get("triggered") is True
    assert "evidence_confidence_777" in result


def test_788_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/alert-engine/custom-metrics/status").status_code == 200
    resp = c.get("/api/platform/intelligence-ledger/alert-engine/custom-metrics?user_id=default")
    assert resp.status_code == 200
    assert resp.json()["no_smart_alerts"] is True


# --- #789 ---


def test_789_not_user_alerts(ios_seed):
    stack = ios.build_sre_observability_stack_789(seed=ios_seed)
    assert stack["not_user_alert_system"] is True
    assert stack["no_market_data"] is True
    assert stack["user_alerts_built_in_788"] is True


def test_789_sre_components(ios_seed):
    stack = ios.build_sre_observability_stack_789(seed=ios_seed)
    components = stack["components"]
    assert "prometheus" in components
    assert "grafana" in components
    assert "loki" in components
    assert "jaeger" in components


def test_789_slos(ios_seed):
    stack = ios.build_sre_observability_stack_789(seed=ios_seed)
    slos = stack["slos"]
    assert slos["uptime_target_pct"] == 99.9
    assert slos["latency_p99_max_ms"] == 500
    assert slos["error_rate_max_pct"] == 0.1


def test_789_slo_tests(ios_seed):
    qa = ios.run_infra_observability_slo_tests_789(seed=ios_seed)
    assert qa["all_passed"] is True


# --- #794 ---


def test_794_five_metrics(oml_seed):
    suite = oml.build_supply_dynamics_suite_794("BTC", seed=oml_seed)
    assert suite["ok"] is True
    assert len(suite["mandatory_metrics"]) == 5
    assert "Active: 18.0%" in suite["display"]


def test_794_chain_semantics(oml_seed):
    suite = oml.build_supply_dynamics_suite_794("BTC", seed=oml_seed)
    assert suite["chain_model"] == "utxo"
    assert suite["chain_semantics_documented"] is True


def test_794_methodology_documented(oml_seed):
    suite = oml.build_supply_dynamics_suite_794("BTC", seed=oml_seed)
    assert suite["methodology"]["documented"] is True
    assert suite["no_ml_prediction"] is True


def test_794_supply_reconciliation(oml_seed):
    qa = oml.run_supply_reconciliation_qa_794("BTC", seed=oml_seed)
    assert qa["within_tolerance"] is True
    assert qa["tolerance_pct"] == 0.1


def test_794_reorg_handling(oml_seed):
    suite = oml.build_supply_dynamics_suite_794("BTC", seed=oml_seed)
    assert suite["reorg_handling"]["recalculate_cancelled_blocks"] is True


def test_794_market_radar_widget(oml_seed):
    widget = oml.build_market_radar_supply_dynamics_widget_794("BTC", seed=oml_seed)
    assert widget["widget_label_ar"] == "ديناميكيات العرض"


def test_794_asset_card(oml_seed):
    card = oml.build_asset_card_supply_structure_794("BTC", seed=oml_seed)
    assert card["tab_ar"] == "هيكل العرض"
    assert len(card["pie_chart_data"]) == 4


def test_794_risk_flag(oml_seed):
    flag = oml.build_revived_supply_risk_flag_ledger_794("BTC", seed=oml_seed)
    assert flag["ok"] is True
    assert flag["no_automatic_alert"] is True


def test_794_market_radar_integration(mri_seed):
    panel = mri.build_market_radar_panel("binance", "BTC", seed=mri_seed)
    assert panel["supply_dynamics_794"]["ok"] is True


def test_794_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    resp = c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/supply-dynamics?asset=BTC")
    assert resp.status_code == 200
    assert resp.json()["feature_ref"] == 794
