"""Tests — #757 Token Circulation, #759 Alerts, #760 Technical Chart."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import alert_engine as ae
from bd_platform import market_radar_indicators as mri
from bd_platform import onchain_metrics_library as oml


@pytest.fixture
def oml_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_library_seed.json"
    p.write_text(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(oml, "_SEED_PATH", p)
    return p


@pytest.fixture
def ae_seed(tmp_path, monkeypatch):
    p = tmp_path / "alert_engine_seed.json"
    p.write_text(Path("data/alert_engine_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ae, "_SEED_PATH", p)
    return p


@pytest.fixture
def mri_seed(tmp_path, monkeypatch):
    p = tmp_path / "market_radar_indicators_seed.json"
    p.write_text(Path("data/market_radar_indicators_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(mri, "_SEED_PATH", p)
    return p


# --- #757 ---


def test_757_btc_utxo_no_double_count(oml_seed):
    suite = oml.build_token_circulation_suite_757("BTC")
    assert suite["ok"] is True
    assert suite["chain_model"] == "utxo"
    assert suite["no_double_counting"] is True
    assert suite["mandatory_metrics"]["unique_units_moved"]["value"] == 3


def test_757_eth_account_semantics(oml_seed):
    suite = oml.build_token_circulation_suite_757("ETH")
    assert suite["chain_model"] == "account"
    assert suite["mandatory_metrics"]["circulation_velocity"]["value"] is not None


def test_757_hbar_dag_model(oml_seed):
    suite = oml.build_token_circulation_suite_757("HBAR")
    assert suite["chain_model"] == "dag"


def test_757_qa_tests(oml_seed):
    dc = oml.run_token_circulation_no_double_count_tests_757()
    assert dc["all_passed"] is True
    backfill = oml.run_token_circulation_backfill_qa_757("BTC")
    assert backfill["within_tolerance"] is True


def test_757_market_radar_widget(oml_seed):
    widget = oml.build_market_radar_token_circulation_widget_757("BTC")
    assert widget["widget_label_ar"] == "حركة التوكن"


def test_757_asset_card(oml_seed):
    card = oml.build_asset_card_circulation_context_757("BTC")
    assert card["tab"] == "Circulation"
    assert len(card["sparkline"]) >= 3


def test_757_risk_flag(oml_seed):
    flag = oml.build_circulation_velocity_risk_flag_ledger("BTC")
    assert flag["ok"] is True


def test_757_metrics_panel(oml_seed):
    panel = oml.build_metrics_library_panel("BTC")
    assert panel["sub_modules"]["757_token_circulation"]["ok"] is True


# --- #759 ---


def test_759_layer_config(ae_seed):
    layer = ae.build_multi_channel_alerts_layer_759()
    assert layer["no_whatsapp"] is True
    assert layer["rule_based_only"] is True
    assert layer["log_retention_days"] == 30


def test_759_portfolio_alerts(ae_seed):
    panel = ae.build_portfolio_alerts_panel_759()
    assert panel["route"] == "/portfolio/alerts"
    assert panel["panel_name_ar"] == "تنبيهاتي"
    assert panel["triggered_count"] >= 1


def test_759_market_radar_alerts(ae_seed):
    panel = ae.build_market_radar_alerts_panel_759()
    assert panel["route"] == "/radar/alerts"
    assert "Not financial advice" in panel["disclaimer"]


def test_759_qa(ae_seed):
    qa = ae.run_alerts_qa_tests_759()
    assert qa["all_passed"] is True


# --- #760 ---


def test_760_no_prediction(mri_seed):
    chart = mri.build_technical_chart_overlay_760("BTC")
    assert chart["ok"] is True
    assert chart["no_prediction"] is True
    assert chart["no_strong_buy_sell"] is True
    assert "does not predict" in chart["disclaimer"].lower()


def test_760_asset_card(mri_seed):
    panel = mri.build_asset_card_technical_indicators_760("BTC")
    assert panel["panel_name_ar"] == "مؤشرات فنية"
    assert panel["no_prediction"] is True


def test_760_market_radar_panel(mri_seed, oml_seed, ae_seed):
    panel = mri.build_market_radar_panel("BTC")
    assert panel["technical_chart_760"]["ok"] is True
    assert panel["token_circulation_757"]["ok"] is True
    assert panel["market_alerts_759"]["ok"] is True


def test_api_routes(oml_seed, ae_seed, mri_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    client = TestClient(app)
    assert client.get("/api/platform/intelligence-ledger/onchain-layer/metrics-library/token-circulation?asset=BTC").status_code == 200
    assert client.get("/api/platform/intelligence-ledger/market-radar/technical-chart?asset=BTC").status_code == 200
    assert client.get("/api/platform/intelligence-ledger/portfolio-ai/alerts").status_code == 200
    assert client.get("/api/platform/intelligence-ledger/market-radar/alerts").status_code == 200
