"""Tests — #482 Oracle Risk, #483 ROI & ATH, #484/#485 Risk Layer, #488 SOPR."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import capital_protection_controls as cpc
from bd_platform import defi_opportunity_scanner as dos
from bd_platform import portfolio_intelligence_engine as pie
from bd_platform import smart_money_flow_tracker as smft
from bd_platform import stablecoin_health_monitor as shm


@pytest.fixture
def dos_seed(tmp_path, monkeypatch):
    main = Path("data/defi_opportunity_scanner_seed.json")
    p = tmp_path / "defi_opportunity_scanner_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(dos, "_SEED_PATH", p)
    return p


@pytest.fixture
def pie_seed(tmp_path, monkeypatch):
    main = Path("data/portfolio_intelligence_engine_seed.json")
    p = tmp_path / "portfolio_intelligence_engine_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(pie, "_SEED_PATH", p)
    return p


@pytest.fixture
def cpc_seed(tmp_path, monkeypatch):
    main = Path("data/capital_protection_controls_seed.json")
    p = tmp_path / "capital_protection_controls_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(cpc, "_SEED_PATH", p)
    return p


@pytest.fixture
def smft_seed(tmp_path, monkeypatch):
    main = Path("data/smart_money_flow_tracker_seed.json")
    p = tmp_path / "smart_money_flow_tracker_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(smft, "_SEED_PATH", p)
    return p


# --- #482 Oracle Risk ---


def test_482_oracle_risk_view(dos_seed):
    view = dos.build_oracle_risk_view()
    assert view["feature_ref"] == 482
    assert view["count"] >= 1
    assert view["source_config_version"] == "1.0"


def test_482_protocol_oracle_indicators(dos_seed):
    aave = dos.analyze_protocol_oracle_risk("aave")
    assert aave["ok"] is True
    assert aave["oracle_count"] >= 1
    assert "heartbeat_freshness" in aave
    assert "deviation_history_bps" in aave
    assert aave["source_config"]["documented"] is True


def test_482_single_oracle_alerts(dos_seed):
    alerts = dos.build_portfolio_single_oracle_alerts()
    assert alerts["backend_enforced"] is True
    assert alerts["feature_ref"] == 482


def test_482_stablecoin_oracle_flag(dos_seed):
    flag = dos.get_stablecoin_oracle_risk_flag("USDT")
    assert flag["ok"] is True
    assert "oracle_risk_flagged" in flag


def test_482_stablecoin_health_integration(dos_seed):
    usdt = shm.analyze_stablecoin("USDT")
    assert "oracle_risk_482" in usdt
    assert "oracle_risk_flagged" in usdt


def test_482_defi_panel(dos_seed):
    panel = dos.build_defi_panel()
    assert (panel.get("oracle_risk_482") or {}).get("ok") is True


# --- #483 ROI & ATH ---


def test_483_roi_seven_windows(pie_seed):
    roi = pie.compute_roi_matrix("BTC")
    assert roi["ok"] is True
    assert set(roi["roi_windows"].keys()) == set(pie._MANDATORY_ROI_WINDOWS)


def test_483_ath_drawdown(pie_seed):
    ath = pie.compute_ath_statistics("BTC")
    assert ath["ok"] is True
    assert ath["ath_drawdown_pct"] is not None
    assert ath["ath_price"] > 0


def test_483_deterministic(pie_seed):
    a = {k: v for k, v in pie.compute_roi_matrix("BTC").items() if k != "timestamp"}
    b = {k: v for k, v in pie.compute_roi_matrix("BTC").items() if k != "timestamp"}
    assert a == b


def test_483_breakeven_integration(pie_seed):
    roi = pie.compute_roi_matrix("BTC")
    be = roi.get("breakeven_roi_404")
    assert be is not None
    assert be["source"] == "live_breakeven_404"


def test_483_asset_card(pie_seed):
    card = pie.build_roi_ath_asset_card("BTC")
    assert card["ok"] is True
    assert card["roi_matrix"]["deterministic"] is True


def test_483_portfolio_panel(pie_seed):
    panel = pie.build_integrated_panel()
    roi = panel.get("roi_ath_intelligence_483") or {}
    assert roi.get("ok") is True
    assert roi.get("count", 0) >= 1


# --- #484 Real-Time Risk Alerts ---


def test_484_backend_enforced(cpc_seed):
    alerts = cpc.build_real_time_risk_alerts()
    assert alerts["backend_enforced"] is True
    assert alerts["client_side_calculation"] is False
    assert len(alerts["mandatory_thresholds"]) >= 4


def test_484_four_threshold_rules(cpc_seed):
    alerts = cpc.build_real_time_risk_alerts()
    thresholds = alerts["mandatory_thresholds"]
    assert "drawdown_pct" in thresholds
    assert "concentration_pct" in thresholds
    assert "correlation_spike" in thresholds
    assert "exchange_health_drop" in thresholds


def test_484_capital_panel_integration(cpc_seed):
    panel = cpc.build_capital_awareness_panel()
    rt = panel.get("real_time_risk_alerts_484") or {}
    assert rt.get("backend_enforced") is True


# --- #485 Risk Analytics ---


def test_485_var_95_99(cpc_seed):
    var_block = cpc.compute_portfolio_var()
    assert var_block["var_95_pct"] is not None
    assert var_block["var_99_pct"] is not None
    assert var_block["var_99_pct"] > var_block["var_95_pct"]


def test_485_liquidity_exit_risk(cpc_seed):
    liq = cpc.compute_liquidity_exit_risk()
    assert liq["max_slippage_pct"] == 2.0
    assert liq["portfolio_bottleneck_exit_usd"] >= 0


def test_485_risk_analytics_block(cpc_seed):
    block = cpc.build_risk_analytics_block()
    assert block["stress_scenario_count"] == 5
    assert block["model_validation"]["assumptions_documented"] is True


def test_485_capital_panel(cpc_seed):
    panel = cpc.build_capital_awareness_panel()
    ra = panel.get("risk_analytics_485") or {}
    assert ra.get("var", {}).get("var_95_pct") is not None


# --- #488 SOPR ---


def test_488_sopr_output(smft_seed):
    sopr = smft.compute_sopr("BTC")
    assert sopr["ok"] is True
    assert sopr["sopr_7d_avg"] is not None
    assert sopr["profit_loss_regime"] in ("profit_zone", "loss_zone")
    assert sopr["trend_direction"] in ("improving", "declining", "flat")


def test_488_transfer_filtering(smft_seed):
    edge = smft.build_sopr_edge_case_tests()
    assert edge["all_passed"] is True
    assert len(edge["edge_cases"]) == 3


def test_488_loss_regime_alert(smft_seed):
    alert = smft.build_sopr_loss_regime_alert()
    assert alert["ok"] is True
    assert alert["alert_count"] >= 1


def test_488_market_radar_context(smft_seed):
    ctx = smft.build_market_radar_sopr_context("BTC")
    assert ctx["surface"] == "market_radar"
    assert ctx["sopr"]["ok"] is True


def test_488_smart_money_panel(smft_seed):
    panel = smft.build_smart_money_flow_panel("BTC")
    sopr_block = panel.get("sopr_intelligence_488") or {}
    assert sopr_block.get("count", 0) >= 1


# --- Reconciliation ---


def test_reconciliation_all_modules(dos_seed, pie_seed, cpc_seed, smft_seed):
    assert dos.run_reconciliation_tests()["ok"] is True
    assert pie.run_reconciliation_tests()["ok"] is True
    assert cpc.run_reconciliation_tests()["ok"] is True
    assert smft.run_reconciliation_tests()["ok"] is True
