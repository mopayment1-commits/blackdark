"""Tests — #800 Chart Overlay, #801 Activity Metrics, #804 UX Modes, #810 Exchange Activity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import market_radar_indicators as mri
from bd_platform import onchain_metrics_library as oml
from ux_mode import (
    apply_widget_view_mode_804,
    beginner_professional_modes_status_804,
    build_asset_card_view_modes_804,
)


@pytest.fixture
def mri_seed() -> dict:
    return json.loads(Path("data/market_radar_indicators_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def oml_seed() -> dict:
    return json.loads(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"))


# --- #800 ---


def test_800_streamlit_rejected(mri_seed):
    chart = mri.build_interactive_chart_overlay_800("BTC", seed=mri_seed)
    assert chart["ok"] is True
    assert chart["streamlit_rejected"] is True
    assert chart["no_streamlit"] is True
    assert chart["route"] == "/radar/chart"
    assert chart["chart_library"] == "TradingView Lightweight Charts"


def test_800_four_indicators_only(mri_seed):
    chart = mri.build_interactive_chart_overlay_800("BTC", seed=mri_seed)
    assert chart["max_indicators_sprint_1"] == 4
    ind = chart["indicators"]
    assert "RSI" in ind
    assert "MACD" in ind
    assert "SMA" in ind
    assert "Volume" in ind


def test_800_zoom_pan_no_save_export(mri_seed):
    chart = mri.build_interactive_chart_overlay_800("BTC", seed=mri_seed)
    interaction = chart["interaction"]
    assert interaction["zoom"] is True
    assert interaction["pan"] is True
    assert interaction["save_settings"] is False
    assert interaction["export"] is False


def test_800_asset_card(mri_seed):
    card = mri.build_asset_card_technical_chart_800("BTC", seed=mri_seed)
    assert card["ok"] is True
    assert card["panel_name_ar"] == "مؤشرات فنية"


def test_800_market_radar_integration():
    panel = mri.build_market_radar_panel("BTC")
    chart = panel.get("interactive_chart_overlay_800") or {}
    assert chart.get("ok") is True


# --- #801 ---


def test_801_activity_suite(oml_seed):
    suite = oml.build_activity_metrics_suite_801("BTC", seed=oml_seed)
    assert suite["ok"] is True
    assert suite["metric_id"] == "activity_metrics"
    m = suite["metrics"]
    assert "daa" in m
    assert "tx_count" in m
    assert "tx_value_usd" in m
    assert "average_tx_size" in m


def test_801_spam_bot_policy(oml_seed):
    suite = oml.build_activity_metrics_suite_801("BTC", seed=oml_seed)
    policy = suite["spam_bot_policy"]
    assert policy["policy_applied"] is True
    assert policy["adjusted_daa"] < policy["raw_daa"]


def test_801_glassnode_qa(oml_seed):
    qa = oml.run_activity_metrics_qa_801("BTC", seed=oml_seed)
    assert qa["within_tolerance"] is True
    assert qa["tolerance_pct"] == 2.0


def test_801_market_radar_widget(oml_seed):
    widget = oml.build_market_radar_activity_metrics_widget_801("BTC", seed=oml_seed)
    assert widget["widget_label_ar"] == "نشاط الشبكة"


# --- #804 ---


def test_804_status():
    status = beginner_professional_modes_status_804()
    assert status["no_global_mode_switch"] is True
    assert status["per_widget_mode"] is True


def test_804_beginner_limits_metrics():
    widget = apply_widget_view_mode_804(
        {"metrics": [{"k": i} for i in range(8)]},
        view_mode="beginner",
        widget_id="test",
    )
    assert widget["view_mode"] == "beginner"
    assert len(widget["metrics_shown"]) == 4
    assert widget["explain_button_ar"] == "اشرح لي"
    assert widget["formulas_visible"] is False


def test_804_professional_shows_all():
    widget = apply_widget_view_mode_804(
        {"metrics": [{"k": i} for i in range(8)], "formulas": {"a": "f"}, "sources": {"b": "s"}},
        view_mode="professional",
        widget_id="test",
    )
    assert widget["view_mode"] == "professional"
    assert len(widget["metrics_shown"]) == 8
    assert widget["formulas_visible"] is True
    assert widget["raw_values_visible"] is True


def test_804_asset_card_toggle():
    card = build_asset_card_view_modes_804("BTC", view_mode="beginner")
    assert card["toggle_ar"] == "بسيط/متقدم"
    assert card["per_widget_mode"] is True


# --- #810 ---


def test_810_exchange_suite(oml_seed):
    suite = oml.build_exchange_activity_suite_810("BTC", seed=oml_seed)
    assert suite["ok"] is True
    m = suite["metrics"]
    assert "deposit_count" in m
    assert "withdrawal_count" in m
    assert "net_flow" in m
    assert "unique_addresses" in m


def test_810_coverage_disclosed(oml_seed):
    suite = oml.build_exchange_activity_suite_810("BTC", seed=oml_seed)
    assert suite["coverage_disclosed"] is True
    assert "Binance" in suite["coverage_exchanges"]
    assert suite["address_semantics"]["documented"] is True


def test_810_internal_filtered(oml_seed):
    suite = oml.build_exchange_activity_suite_810("BTC", seed=oml_seed)
    filt = suite["internal_activity_filtered"]
    assert filt["enabled"] is True
    assert filt["excluded_count"] > 0


def test_810_glassnode_qa(oml_seed):
    qa = oml.run_exchange_activity_qa_810("BTC", seed=oml_seed)
    assert qa["within_tolerance"] is True
    assert qa["tolerance_pct"] == 5.0


def test_810_market_radar_integration():
    panel = mri.build_market_radar_panel("BTC")
    assert (panel.get("exchange_activity_810") or {}).get("ok") is True
    assert (panel.get("activity_metrics_801") or {}).get("ok") is True


def test_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/market-radar/chart?asset=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/ux-layer/view-modes/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/activity-metrics?asset=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/exchange-activity?asset=BTC").status_code == 200
    chart = c.get("/api/platform/intelligence-ledger/market-radar/chart?asset=BTC").json()
    assert chart["streamlit_rejected"] is True
