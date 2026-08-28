"""Tests — #885 Sandbox + #889 Risk Rules + #892 Streaming + #894 Twitter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import api_gateway_developer_sandbox as sandbox
from bd_platform import api_gateway_streaming as streaming
from bd_platform import intelligence_ledger_risk_rules as risk
from blackdark.ingestion import twitter_connector as twitter


@pytest.fixture
def gw_seed() -> dict:
    return json.loads(Path("data/api_gateway_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def risk_seed() -> dict:
    return json.loads(Path("data/intelligence_ledger_risk_rules_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def twitter_seed() -> dict:
    return json.loads(Path("data/twitter_connector_seed.json").read_text(encoding="utf-8"))


# --- #885 ---


def test_885_status(gw_seed):
    status = sandbox.developer_sandbox_status_885(seed=gw_seed)
    assert status["standalone_rejected"] is True
    assert status["api_gateway_ref"] == 876
    assert status["isolated"] is True
    assert status["fixture_count"] == 50


def test_885_isolation(gw_seed):
    proof = sandbox.prove_isolation_885(seed=gw_seed)
    assert proof["isolation_proven"] is True
    assert proof["no_production_side_effects"] is True


def test_885_deterministic_fixtures(gw_seed):
    r1 = sandbox.simulate_sandbox_request_885("scenario-001", seed=gw_seed)
    sandbox.reset_sandbox_state_885(seed=gw_seed)
    r2 = sandbox.simulate_sandbox_request_885("scenario-001", seed=gw_seed)
    assert r1["body"]["data"]["price"] == r2["body"]["data"]["price"]
    assert r1["production_side_effects"] is False


def test_885_error_scenarios(gw_seed):
    errors = sandbox.run_rate_limit_error_scenarios_885(seed=gw_seed)
    assert errors["all_passed"] is True


def test_885_reset(gw_seed):
    sandbox.simulate_sandbox_request_885("scenario-002", seed=gw_seed)
    reset = sandbox.reset_sandbox_state_885(seed=gw_seed)
    assert reset["state_wiped"] is True


def test_885_e2e(gw_seed):
    e2e = sandbox.run_developer_sandbox_e2e_885(seed=gw_seed)
    assert e2e["all_passed"] is True


# --- #889 ---


def test_889_status(risk_seed):
    status = risk.risk_rules_status_889(seed=risk_seed)
    assert status["standalone_rejected"] is True
    assert status["no_enforcement"] is True
    assert status["rule_count"] <= 10
    assert status["approval_workflow_required"] is True


def test_889_rules_evaluation(risk_seed):
    btc = risk.evaluate_risk_rules_889("BTC", seed=risk_seed)
    assert btc["scoring_only"] is True
    assert "Overvalued" in btc["triggered_labels"]

    eth = risk.evaluate_risk_rules_889("ETH", seed=risk_seed)
    assert "Extreme" in eth["triggered_labels"]
    assert "Risk" in eth["triggered_labels"]


def test_889_approval_queue(risk_seed):
    queue = risk.get_approval_queue_889(seed=risk_seed)
    assert queue["manual_approval_required"] is True
    assert queue["no_auto_deploy"] is True
    assert queue["count"] >= 1


def test_889_versioning(risk_seed):
    ver = risk.get_version_migration_889(seed=risk_seed)
    assert ver["current_version"] == "1.0"
    assert ver["breaking_changes"] is False


def test_889_e2e(risk_seed):
    e2e = risk.run_risk_rules_e2e_889(seed=risk_seed)
    assert e2e["all_passed"] is True


# --- #892 ---


def test_892_status(gw_seed):
    status = streaming.streaming_infrastructure_status_892(seed=gw_seed)
    assert status["standalone_rejected"] is True
    assert status["api_gateway_ref"] == 876
    assert status["market_data_ref"] == 879


def test_892_api_streaming(gw_seed):
    api = streaming.build_api_streaming_config_892(seed=gw_seed)
    assert api["transport"] == "websocket"
    assert api["sandbox_isolated"] is True


def test_892_market_data_streaming(gw_seed):
    md = streaming.build_market_data_streaming_config_892("BTC", seed=gw_seed)
    assert md["transport"] == "websocket"
    assert md["within_response_target"] is True


def test_892_slo(gw_seed):
    panel = streaming.build_streaming_panel_892("BTC", seed=gw_seed)
    slo = panel["slo_evidence"]
    assert slo["response_within_2s"] is True
    assert slo["accuracy_above_95"] is True
    assert slo["uptime_above_99"] is True


def test_892_e2e(gw_seed):
    e2e = streaming.run_streaming_e2e_892(seed=gw_seed)
    assert e2e["all_passed"] is True


# --- #894 ---


def test_894_status(twitter_seed):
    status = twitter.twitter_connector_status_894(seed=twitter_seed)
    assert status["standalone_rejected"] is True
    assert status["sentiment_ref"] == 783
    assert status["free_tier_monthly_limit"] == 1500


def test_894_fetch_and_cache(twitter_seed):
    twitter._CACHE.clear()
    first = twitter.fetch_twitter_mentions_894("BTC", seed=twitter_seed)
    second = twitter.fetch_twitter_mentions_894("BTC", seed=twitter_seed)
    assert first["ok"] is True
    assert second["cache_hit"] is True


def test_894_fallback(twitter_seed):
    fb = twitter.fetch_twitter_mentions_894("BTC", seed=twitter_seed, force_primary_fail=True)
    assert fb["fallback_used"] is True
    assert fb["no_absolute_dependency"] is True


def test_894_sentiment_feed(twitter_seed):
    feed = twitter.build_sentiment_feed_894("BTC", seed=twitter_seed)
    assert feed["ok"] is True
    assert "783" in feed["feeds"]


def test_894_e2e(twitter_seed):
    e2e = twitter.run_twitter_connector_e2e_894(seed=twitter_seed)
    assert e2e["all_passed"] is True
