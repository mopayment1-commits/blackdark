"""Tests — #587/#597 Screener, #588/#595/#596 Sentiment, #589 Alerts, #590/#593/#598 Smart Money."""

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


# --- #595 / #596 ---


def test_595_entity_tagged_feed(ssl_seed):
    feed = ssl.build_entity_tagged_sentiment_feed("BTC")
    assert feed["ok"] is True
    assert feed["legal_name"] == "Entity-Tagged Sentiment Feed"
    assert feed["not_alignment_engine"] is True


def test_595_no_alignment_language(ssl_seed):
    feed = ssl.build_entity_tagged_sentiment_feed("BTC")
    assert feed["no_alignment_language"] is True
    assert feed["not_alignment_engine"] is True
    for event in feed.get("entity_tagged_events") or []:
        assert event.get("alignment_computed_in_524") is True


def test_595_nlp_and_sources(ssl_seed):
    feed = ssl.build_entity_tagged_sentiment_feed("BTC")
    assert feed["nlp_analysis"]["accuracy_threshold_met"] is True
    assert feed["source_coverage"]["coverage_met"] is True
    assert feed["source_coverage"]["source_count"] >= 5


def test_595_refresh_and_archive(ssl_seed):
    feed = ssl.build_entity_tagged_sentiment_feed("BTC")
    assert feed["refresh_policy"]["interval_minutes"] == 15
    assert feed["archive"]["archive_met"] is True


def test_596_duplicate_merged(ssl_seed):
    panel = ssl.build_social_sentiment_panel("BTC")
    assert 595 in panel["feature_ids"]
    assert 596 in panel["feature_ids"]
    sub = panel["sub_modules"]["595_596_entity_tagged_sentiment_feed"]
    assert sub["ok"] is True


# --- #597 ---


def test_597_user_controlled_filters(cmds_seed):
    result = cmds.run_smart_money_token_screener({"smart_money_inflow_min": {"min": 5_000_000}})
    assert result["ok"] is True
    assert result["no_recommended_tokens"] is True
    assert result["user_controlled_filters_only"] is True


def test_597_explain_each_match(cmds_seed):
    result = cmds.run_smart_money_token_screener({"smart_money_inflow_min": {"min": 5_000_000}})
    assert result["explain_each_match"] is True
    for item in result.get("results") or []:
        explanation = item.get("match_explanation") or {}
        assert explanation.get("display")


def test_597_save_and_alert(cmds_seed):
    result = cmds.run_smart_money_token_screener()
    assert result["save_and_alert_supported"] is True


# --- #598 ---


def test_598_tracking_feed(smft_seed):
    feed = smft.build_smart_money_tracking_feed()
    assert feed["ok"] is True
    assert feed["task_id"] == "598"
    assert feed["event_count"] >= 1


def test_598_latency_visible(smft_seed):
    feed = smft.build_smart_money_tracking_feed()
    assert feed["latency"]["latency_visible"] is True
    assert feed["latency"]["measured_ms"] >= 0


def test_598_duplicate_prevention(smft_seed):
    feed = smft.build_smart_money_tracking_feed()
    assert feed["duplicate_prevention"]["enabled"] is True
    assert feed["duplicate_prevention"]["duplicates_prevented"] >= 1


def test_598_missed_event_handling(smft_seed):
    feed = smft.build_smart_money_tracking_feed()
    assert feed["missed_event_handling"]["missed_visible"] is True
    assert feed["missed_event_handling"]["missed_events"] >= 1
