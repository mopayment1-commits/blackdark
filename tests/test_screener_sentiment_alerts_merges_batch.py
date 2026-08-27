"""Tests — #587 Screener, #588 Sentiment, #589 Alerts, #590/#593 Smart Money."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import custom_alerts as ca
from bd_platform import custom_market_data_screener as cmds
from bd_platform import smart_money_flow_tracker as smft
from bd_platform import social_sentiment_layer as ssl


@pytest.fixture
def cmds_seed(tmp_path, monkeypatch):
    main = Path("data/custom_market_data_screener_seed.json")
    p = tmp_path / "custom_market_data_screener_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(cmds, "_SEED_PATH", p)
    return p


@pytest.fixture
def ssl_seed(tmp_path, monkeypatch):
    main = Path("data/social_sentiment_layer_seed.json")
    p = tmp_path / "social_sentiment_layer_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ssl, "_SEED_PATH", p)
    return p


@pytest.fixture
def ca_seed(tmp_path, monkeypatch):
    main = Path("data/custom_alerts_seed.json")
    p = tmp_path / "custom_alerts_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ca, "_SEED_PATH", p)
    return p


@pytest.fixture
def smft_seed(tmp_path, monkeypatch):
    main = Path("data/smart_money_flow_tracker_seed.json")
    p = tmp_path / "smart_money_flow_tracker_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(smft, "_SEED_PATH", p)
    return p


# --- #587 ---


def test_587_no_default_ranking(cmds_seed):
    result = cmds.run_screener({"risk_score_max": {"max": 50}})
    assert result["no_default_ranking"] is True


def test_587_pagination(cmds_seed):
    result = cmds.run_screener({"risk_score_max": {"max": 100}}, page=1, page_size=2)
    assert result["pagination"]["page_size"] == 2
    assert result["pagination"]["total_count"] >= 2


def test_587_user_sort(cmds_seed):
    result = cmds.run_screener({"risk_score_max": {"max": 100}}, sort_by="risk_score")
    assert result["sort_by"] == "risk_score"


def test_587_missing_explicit(cmds_seed):
    result = cmds.run_screener({"risk_score_max": {"max": 100}})
    assert result["missing_values_explicit"] is True


def test_587_reconciliation(cmds_seed):
    assert cmds.run_reconciliation_tests()["ok"] is True


# --- #588 ---


def test_588_sentiment_panel(ssl_seed):
    panel = ssl.build_social_sentiment_panel("BTC")
    assert panel["ok"] is True
    assert 588 in panel["feature_ids"]


def test_588_duplicate_suppression(ssl_seed):
    panel = ssl.build_social_sentiment_panel("BTC")
    assert panel["duplicate_suppression"] is True
    assert panel["duplicates_suppressed"] >= 1


def test_588_no_causality(ssl_seed):
    panel = ssl.build_social_sentiment_panel("BTC")
    assert panel["no_unsupported_causality"] is True


def test_588_tos_compliant(ssl_seed):
    panel = ssl.build_social_sentiment_panel("BTC")
    assert panel["tos_compliant"] is True


def test_588_reconciliation(ssl_seed):
    assert ssl.run_reconciliation_tests()["ok"] is True


# --- #589 ---


def test_589_smart_alerts(ca_seed):
    panel = ca.build_custom_alerts_panel()
    assert panel["smart_alert_count"] >= 1


def test_589_backend_enforcement(ca_seed):
    panel = ca.build_custom_alerts_panel()
    assert panel["backend_enforcement"] is True


def test_589_cooldown_dedupe(ca_seed):
    panel = ca.build_custom_alerts_panel()
    assert panel["cooldown_dedupe"] is True


def test_589_reconciliation(ca_seed):
    assert ca.run_reconciliation_tests()["ok"] is True


# --- #590 ---


def test_590_accumulation_state(smft_seed):
    result = smft.detect_accumulation_distribution_state("BTC")
    assert result["accumulation_distribution_state"] == "accumulating"
    assert result["thresholds_visible"] is True


def test_590_persistence_indicator(smft_seed):
    result = smft.detect_accumulation_distribution_state("BTC")
    indicator = result["net_flow_persistence_indicator"]
    assert indicator["persistence_not_rating"] is True
    assert indicator["not_investment_score"] is True


def test_590_no_advisory(smft_seed):
    result = smft.detect_accumulation_distribution_state("BTC")
    assert result["no_advisory_language"] is True
    assert "bullish" not in result["display"].lower()


# --- #593 ---


def test_593_historical_trend(smft_seed):
    trend = smft.build_historical_trend_analysis("BTC")
    assert trend["ok"] is True
    assert trend["classification_version_awareness"] is True


def test_593_statistical_regime(smft_seed):
    trend = smft.build_historical_trend_analysis("BTC")
    assert trend["regimes_statistical_only"] is True
    assert "bullish" not in trend["statistical_regime"]


def test_593_missing_not_zero(smft_seed):
    trend = smft.build_historical_trend_analysis("BTC")
    assert trend["missing_history_handling"]["missing_not_zero"] is True


def test_593_smart_money_reconciliation(smft_seed):
    result = smft.run_reconciliation_tests()
    assert result["ok"] is True
