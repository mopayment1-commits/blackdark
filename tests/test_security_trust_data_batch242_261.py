"""Tests — Security, Trust & Data Sources (#242–#261)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import security_trust_data_layer as std


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset():
    std.reset_security_trust_data_state()
    yield
    std.reset_security_trust_data_state()


def test_242_audit_trail(seed):
    audit = std.append_audit_event_242(actor="user", action="login", system="landing", seed=seed)
    assert audit["entry"]["immutable"] is True
    assert audit["entry"]["chain_hash"]
    export = std.export_audit_trail_242(seed=seed)
    assert export["admin_mfa_required"] is True


def test_242_audit_embed(seed):
    from bd_platform.data_sources_layer import explain_opportunity_151

    explain = explain_opportunity_151(seed=seed)
    assert "audit_log_id" in explain
    assert 242 in explain["merged_features"]


def test_243_bybit(seed):
    bybit = std.ingest_bybit_price_243(seed=seed)
    assert bybit["source"] == "bybit"
    assert bybit["normalized_oracle_format"] is True


def test_244_cointelegraph(seed):
    news = std.ingest_cointelegraph_rss_244(seed=seed)
    assert news["rule_based_filtering"] is True


def test_245_coinmarketcal_merged(seed):
    assert std.coinmarketcal_status_245(seed=seed)["activation_not_build"] is True


def test_246_etherscan_watch(seed):
    watch = std.add_etherscan_watch_246(address="0xabc", seed=seed)
    assert watch["watch"]["no_wallet_connection"] is True
    assert std.list_etherscan_watchlist_246(seed=seed)["watches"]


def test_247_weekly_digest(seed):
    digest = std.generate_weekly_digest_247(seed=seed)
    assert digest["ai_reports_rejected"] is True
    assert digest["summary_not_recommendation"] is True


def test_248_profit_rejected(seed):
    assert std.profit_analytics_rejected_status_248(seed=seed)["profit_analytics_rejected"] is True
    perf = std.manual_performance_tracker_248(seed=seed)
    assert perf["manual_entry_only"] is True


def test_249_250_rejected():
    assert std.trad_simulator_rejected_status_249()["trad_simulator_rejected"] is True
    assert std.execution_speed_rejected_status_250()["execution_speed_rejected"] is True


def test_251_token_velocity(seed):
    velocity = std.compute_token_velocity_251(seed=seed)
    assert velocity["formula"] == "circulating_supply / (trading_volume_30d / 30)"


def test_252_google_trends(seed):
    trends = std.ingest_google_trends_252(seed=seed)
    assert trends["merged_into"] == ["sentiment_layer", "market_radar", "signal_engine_11"]


def test_253_kill_rate(seed):
    kill = std.build_kill_rate_widget_253(seed=seed)
    assert kill["brag_about_refusal"] is True


def test_254_contradiction_replay(seed):
    replay = std.build_contradiction_replay_254(seed=seed)
    assert replay["shareable"] is True


def test_255_committee_pager(seed):
    pager = std.committee_one_pager_status_255(seed=seed)
    assert pager["pro_desk_tier_only"] is True


def test_256_half_life_clock(seed):
    clock = std.compute_half_life_clock_256(seed=seed)
    assert clock["remaining_vitality_pct"] >= 0


def test_257_proof_arena_lite(seed):
    assert std.proof_arena_lite_status_257(seed=seed)["mode"] == "lite"


def test_258_since_you_left(seed):
    widget = std.since_you_left_top3_258(seed=seed)
    assert len(widget["top_events"]) == 3


def test_259_anti_hype(seed):
    result = std.apply_anti_hype_mode_259("فرصة ذهبية", enabled=True)
    assert "محتملة" in result["sanitized"] or "فرصة" in result["sanitized"]


def test_260_corpus_passport(seed):
    passport = std.corpus_passport_status_260(seed=seed)
    assert passport["requires_audit_trail_242"] is True


def test_261_pricing(seed):
    pricing = std.pricing_model_status_261(seed=seed)
    assert pricing["no_lifetime_access"] is True
    assert pricing["tiers"]["pro"]["price_usd"] == 29


def test_261_subscription_embed(seed):
    from bd_platform.legal_commercial_layer import subscription_tier_status_60

    sub = subscription_tier_status_60(seed=seed)
    assert "pricing_model_261" in sub


def test_security_trust_data_e2e(seed):
    assert std.run_security_trust_data_e2e_242_261(seed=seed)["all_passed"] is True
