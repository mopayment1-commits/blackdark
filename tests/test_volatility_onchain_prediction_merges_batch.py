"""Tests — #498 Volatility, #578 Usage, #579 Wallet Tracker, #580 Prediction Trends."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import capital_protection_controls as cpc
from bd_platform import market_radar_indicators as mri
from bd_platform import onchain_metrics_library as oml
from bd_platform import portfolio_intelligence_layer as pil
from bd_platform import prediction_trend_analyzer as pta

DEMO_ETH_ADDRESS = "0x0000000000000000000000000000000000000001"


@pytest.fixture
def mri_seed(tmp_path, monkeypatch):
    main = Path("data/market_radar_indicators_seed.json")
    p = tmp_path / "market_radar_indicators_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(mri, "_SEED_PATH", p)
    return p


@pytest.fixture
def oml_seed(tmp_path, monkeypatch):
    main = Path("data/onchain_metrics_library_seed.json")
    p = tmp_path / "onchain_metrics_library_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(oml, "_SEED_PATH", p)
    return p


@pytest.fixture
def pil_seed(tmp_path, monkeypatch):
    main = Path("data/portfolio_intelligence_layer_seed.json")
    p = tmp_path / "portfolio_intelligence_layer_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(pil, "_SEED_PATH", p)
    return p


@pytest.fixture
def pta_seed(tmp_path, monkeypatch):
    main = Path("data/prediction_trend_analyzer_seed.json")
    p = tmp_path / "prediction_trend_analyzer_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(pta, "_SEED_PATH", p)
    return p


# --- #498 Volatility Analytics ---


def test_498_three_mandatory_windows(mri_seed):
    vol = mri.compute_realized_volatility("BTC")
    assert vol["ok"] is True
    assert set(vol["realized_vol_windows"].keys()) == {"7d", "30d", "90d"}


def test_498_window_version_documented(mri_seed):
    dash = mri.build_volatility_analytics_dashboard("BTC")
    assert dash["window_version_documented"] is True
    for w in dash["realized_volatility"]["realized_vol_windows"].values():
        assert w.get("methodology_version") is not None
        assert w.get("window_documented") is True


def test_458_compression_signal(mri_seed):
    compression = mri.build_volatility_compression_signal("BTC")
    assert compression["ok"] is True
    assert compression.get("compression_signal") is not None
    assert compression.get("integration") == "volatility_analytics_498"


def test_410_vol_regime_for_risk(mri_seed):
    regime = mri.build_volatility_regime_for_risk("BTC")
    assert regime["ok"] is True
    assert regime["volatility_regime"] in ("low", "medium", "high")
    assert regime.get("risk_score_adjustment") is not None


def test_498_market_radar_panel(mri_seed):
    panel = mri.build_market_radar_panel("binance", "BTC")
    assert panel["ok"] is True
    assert panel["volatility_analytics_498"]["ok"] is True


def test_498_capital_protection_integration():
    panel = cpc.build_capital_awareness_panel()
    assert panel["ok"] is True
    regime = panel.get("volatility_regime_498") or {}
    assert regime.get("volatility_regime") in ("low", "medium", "high")
    sample = next(iter(panel["position_risk_scores"].values()))
    assert (sample.get("volatility_regime_498") or {}).get("risk_score_adjustment") is not None


def test_498_reconciliation(mri_seed):
    result = mri.run_reconciliation_tests()
    assert result["ok"] is True


# --- #578 Usage Intelligence ---


def test_578_usage_dashboard(oml_seed):
    usage = oml.build_usage_intelligence_dashboard("BTC")
    assert usage["ok"] is True
    assert usage["missing_not_zero"] is True
    assert (usage.get("spam_bot_policy") or {}).get("exclude_bots") is True


def test_578_normalized_by_chain_app(oml_seed):
    usage = oml.build_usage_intelligence_dashboard("BTC")
    norm = usage.get("normalization") or {}
    assert norm.get("normalized_by_chain_app") is True
    assert usage["daily_active_addresses"]["normalized"] <= usage["daily_active_addresses"]["raw"]


def test_578_in_metrics_library_panel(oml_seed):
    panel = oml.build_metrics_library_panel("BTC", prefer_live=False)
    usage = panel["sub_modules"]["578_usage_intelligence"]
    assert usage["ok"] is True


def test_578_historical_qa(oml_seed):
    qa = oml.run_historical_qa_tests()
    usage_tests = [t for t in qa["reconciliation_tests"] if "578" in t["test"]]
    assert usage_tests
    assert all(t["passed"] for t in usage_tests)


# --- #579 Wallet Balance Tracker ---


def test_579_wallet_tracker(pil_seed):
    tracker = pil.build_non_custodial_wallet_balance_tracker(
        DEMO_ETH_ADDRESS,
        chain="ethereum",
    )
    assert tracker["ok"] is True
    assert tracker["legal_name"] == "Non-Custodial Wallet Balance Tracker"
    assert tracker["no_risk_output"] is True
    assert tracker["no_risk_alerts"] is True


def test_579_spam_filtering(pil_seed):
    tracker = pil.build_non_custodial_wallet_balance_tracker(
        DEMO_ETH_ADDRESS,
        chain="ethereum",
    )
    symbols = {t["symbol"] for t in tracker["holdings"]}
    assert "SCAM" not in symbols
    assert tracker["spam_filtering_applied"] is True
    assert any(a["alert_type"] == "spam_token_detected" for a in tracker["data_alerts"])


def test_579_price_provenance(pil_seed):
    tracker = pil.build_non_custodial_wallet_balance_tracker(
        DEMO_ETH_ADDRESS,
        chain="ethereum",
    )
    assert tracker.get("price_provenance")
    assert tracker.get("price_source_per_asset") is True


def test_579_statistical_anomaly_only(pil_seed):
    tracker = pil.build_non_custodial_wallet_balance_tracker(
        DEMO_ETH_ADDRESS,
        chain="ethereum",
    )
    anomaly = tracker.get("statistical_anomaly")
    assert anomaly is not None
    assert anomaly.get("statistical_only") is True
    assert anomaly.get("no_suspicious_activity_language") is True


def test_579_in_portfolio_panel(pil_seed):
    panel = pil.build_portfolio_intelligence_panel("demo_portfolio")
    tracker = panel["sub_modules"]["579_non_custodial_wallet_balance_tracker"]
    assert tracker["ok"] is True


def test_579_reconciliation(pil_seed):
    result = pil.run_reconciliation_tests()
    wallet_tests = [t for t in result["reconciliation_tests"] if "579" in t["test"] or "wallet_tracker" in t["test"]]
    assert wallet_tests
    assert all(t["passed"] for t in wallet_tests)


# --- #580 Prediction Trend Analyzer ---


def test_580_source_attribution(pta_seed):
    event = pta.analyze_prediction_event("btc_etf_approval")
    assert event["eligible"] is True
    attr = event["source_attribution"]
    assert attr["not_blackdark_prediction"] is True
    assert "Polymarket" in attr["display"]


def test_580_liquidity_threshold(pta_seed):
    low = pta.analyze_prediction_event("low_liquidity_event")
    assert low["eligible"] is False
    assert low["reason"] == "below_liquidity_threshold"


def test_580_correlation_not_causation(pta_seed):
    event = pta.analyze_prediction_event("btc_etf_approval")
    ctx = event["market_correlation_context"]
    assert ctx["correlation_not_causation"] is True
    assert ctx["no_price_forecast"] is True


def test_580_panel(pta_seed):
    panel = pta.build_prediction_trend_panel()
    assert panel["ok"] is True
    assert panel["eligible_count"] >= 1
    assert panel["source_attribution_required"] is True


def test_580_reconciliation(pta_seed):
    result = pta.run_reconciliation_tests()
    assert result["ok"] is True
