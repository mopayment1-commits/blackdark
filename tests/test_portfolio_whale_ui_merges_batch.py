"""Tests — #614 #620 #626 #628 merged features batch."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import portfolio_intelligence_engine as pie
from bd_platform import smart_money_flow_tracker as smft
from bd_platform import wallet_profiler as wp


@pytest.fixture
def portfolio_seed(tmp_path, monkeypatch):
    p = tmp_path / "portfolio_intelligence_engine_seed.json"
    p.write_text(Path("data/portfolio_intelligence_engine_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(pie, "_SEED_PATH", p)
    return p


@pytest.fixture
def smft_seed(tmp_path, monkeypatch):
    p = tmp_path / "smart_money_flow_tracker_seed.json"
    p.write_text(Path("data/smart_money_flow_tracker_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(smft, "_SEED_PATH", p)
    return p


@pytest.fixture
def wp_seed(tmp_path, monkeypatch):
    p = tmp_path / "wallet_profiler_seed.json"
    p.write_text(Path("data/wallet_profiler_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(wp, "_SEED_PATH", p)
    return p


# --- #614 Unified Portfolio Dashboard ---


def test_614_dashboard_ok(portfolio_seed):
    dash = pie.build_unified_portfolio_dashboard()
    assert dash["ok"] is True
    assert dash["feature_id"] == 614
    assert dash["standalone"] is False


def test_614_daily_brief_first(portfolio_seed):
    dash = pie.build_unified_portfolio_dashboard()
    assert dash["dashboard_position_first"] == "daily_brief_474"


def test_614_nav_and_allocation(portfolio_seed):
    dash = pie.build_unified_portfolio_dashboard()
    assert dash["nav_usd"] > 0
    assert sum(dash["allocation"].values()) == pytest.approx(100.0, abs=0.5)


def test_614_cross_source_reconciliation(portfolio_seed):
    dash = pie.build_unified_portfolio_dashboard()
    recon = dash["cross_source_reconciliation"]
    assert recon["cross_source_reconciliation"] is True
    eth = next((h for h in dash["holdings_reconciled"] if h["asset"] == "ETH"), None)
    assert eth is not None
    assert eth["cross_source_reconciled"] is True
    assert eth["source_count"] >= 2


def test_614_missing_data_flags(portfolio_seed):
    dash = pie.build_unified_portfolio_dashboard()
    flagged = [h for h in dash["holdings_reconciled"] if h.get("missing_data_flag")]
    assert len(flagged) >= 1
    assert "مصدر واحد" in flagged[0]["missing_data_flag"]


def test_614_notification_center(portfolio_seed, smft_seed):
    dash = pie.build_unified_portfolio_dashboard()
    nc = dash["notification_center"]
    assert nc["enabled"] is True
    assert nc["count"] >= 1


def test_614_strategy_simulator_cta(portfolio_seed):
    dash = pie.build_unified_portfolio_dashboard()
    cta = dash["strategy_simulator_421"]
    assert cta["integration"] == "strategy_simulator_421"


def test_614_e2e_journey_steps(portfolio_seed):
    dash = pie.build_unified_portfolio_dashboard()
    assert len(dash["e2e_journey_steps"]) == 5


def test_614_mobile_first(portfolio_seed):
    dash = pie.build_unified_portfolio_dashboard()
    assert dash["responsive_ux"]["mobile_first"] is True


def test_614_reconciliation_tests(portfolio_seed, smft_seed):
    result = pie.run_reconciliation_tests()
    ids = {c["id"] for c in result["checks"] if c["passed"]}
    assert "unified_dashboard_614" in ids
    assert "cross_source_recon_614" in ids


# --- #620 Wallet Profiler ---


def test_620_six_tabs(wp_seed, smft_seed, portfolio_seed):
    profile = wp.build_wallet_profile("0xwhale_binance_hot")
    assert profile["ok"] is True
    assert len(profile["mandatory_tabs"]) == 6
    assert len(profile["tabs_rendered"]) == 6


def test_620_data_interlinked(wp_seed, smft_seed, portfolio_seed):
    profile = wp.build_wallet_profile("0xwhale_binance_hot")
    assert profile["data_interlinked"] is True
    assert profile["navigation"]["tx_to_counterparty"] is True


def test_620_freshness_visible(wp_seed, smft_seed, portfolio_seed):
    profile = wp.build_wallet_profile("0xwhale_binance_hot")
    assert profile["tabs"]["holdings"]["freshness"]["display"]


def test_620_empty_wallet(wp_seed):
    empty = wp.build_wallet_profile("0xempty")
    assert empty["empty_wallet"] is True
    assert empty["tabs_available"] is False


def test_620_new_wallet_notice(wp_seed, smft_seed, portfolio_seed):
    profile = wp.build_wallet_profile("0xnew_wallet")
    assert profile["new_wallet"] is True
    assert profile["tabs"]["holdings"]["new_wallet_notice"] is not None


def test_620_e2e_latency(wp_seed, smft_seed, portfolio_seed):
    profile = wp.build_wallet_profile("0xwhale_binance_hot")
    assert profile["latency_ms"] < 10000


def test_620_whale_label(wp_seed, smft_seed, portfolio_seed):
    profile = wp.build_wallet_profile("0xwhale_binance_hot")
    sm_tab = profile["tabs"]["smart_money_signals"]
    assert sm_tab["classification_408"]["label"] == "whale"


def test_620_reconciliation_tests(wp_seed, smft_seed, portfolio_seed):
    result = wp.run_reconciliation_tests()
    assert result["ok"] is True


# --- #626 Whale Accumulation/Distribution ---


def test_626_whale_state(smft_seed):
    intel = smft.detect_whale_accumulation_distribution_intelligence("BTC")
    assert intel["ok"] is True
    assert intel["state"] in ("accumulating", "neutral", "distributing")


def test_626_persistence_rule(smft_seed):
    intel = smft.detect_whale_accumulation_distribution_intelligence("BTC")
    assert intel["persistence_rule"]["single_transfer_ignored"] is True
    assert intel["persistence_rule"]["days_min"] == 3


def test_626_thresholds_documented(smft_seed):
    intel = smft.detect_whale_accumulation_distribution_intelligence("BTC")
    th = intel["whale_thresholds"]
    assert th["documented"] is True
    assert th["version"] == "1.0"
    assert th["holdings_usd_min"] == 1_000_000


def test_626_exchange_exclusion(smft_seed):
    intel = smft.detect_whale_accumulation_distribution_intelligence("BTC")
    assert intel["exchange_entity_exclusion"] is True
    assert intel["exchange_wallets_excluded"] >= 1


def test_626_evidence(smft_seed):
    intel = smft.detect_whale_accumulation_distribution_intelligence("BTC")
    assert intel["evidence"]["text"]
    assert len(intel["evidence"]["tx_hashes"]) >= 1


def test_626_market_radar_overlay(smft_seed):
    overlay = smft.build_market_radar_whale_flow_overlay("BTC")
    assert overlay["ok"] is True
    assert overlay["overlay"]["enabled"] is True


def test_626_eth_distributing(smft_seed):
    intel = smft.detect_whale_accumulation_distribution_intelligence("ETH")
    assert intel["state"] == "distributing"


# --- #628 Whale Movement Alerts ---


def test_628_alerts_generated(smft_seed):
    alerts = smft.build_whale_movement_alerts()
    assert alerts["ok"] is True
    assert alerts["alert_count"] >= 2


def test_628_user_threshold(smft_seed):
    low = smft.build_whale_movement_alerts(threshold_usd=100_000)
    high = smft.build_whale_movement_alerts(threshold_usd=10_000_000)
    assert low["alert_count"] >= high["alert_count"]


def test_628_false_positive_review(smft_seed):
    alerts = smft.build_whale_movement_alerts()
    assert alerts["false_positive_review_enabled"] is True
    first = alerts["alerts"][0]
    assert first["false_positive_review"]["options"] == ["thumbs_up", "thumbs_down"]


def test_628_source_evidence(smft_seed):
    alerts = smft.build_whale_movement_alerts()
    first = alerts["alerts"][0]
    ev = first["source_evidence"]
    assert ev["tx_hash"]
    assert ev["block_explorer_url"]


def test_628_exchange_excluded(smft_seed):
    alerts = smft.build_whale_movement_alerts()
    addrs = [a["source_evidence"]["tx_hash"] for a in alerts["alerts"]]
    assert "0xwhale628002" not in addrs


def test_628_dashboard_integration(smft_seed):
    alerts = smft.build_whale_movement_alerts()
    assert alerts["integration_dashboard_614"] is True


def test_628_reconciliation_tests(smft_seed):
    result = smft.run_reconciliation_tests()
    ids = {c["id"] for c in result["checks"] if c["passed"]}
    assert "whale_intel_626" in ids
    assert "whale_alerts_628" in ids
