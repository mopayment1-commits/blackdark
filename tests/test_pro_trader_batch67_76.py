"""Tests — Pro Trader & Portfolio UX (#67–#76)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import pro_trader_layer as pro


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset(seed):
    pro.reset_pro_trader_state()
    yield
    pro.reset_pro_trader_state()


def test_67_health_score_widget(seed):
    result = pro.compute_health_score_67(concentration_pct=85, seed=seed)
    assert 0 <= result["widget"]["score"] <= 100
    assert result["widget"]["color"] in ("green", "yellow", "red")
    assert result["widget"]["no_tables_default"] is True


def test_67_from_holdings(seed):
    holdings = [{"value_usd": 8000, "btc_beta": 0.9}, {"value_usd": 2000, "btc_beta": 0.5}]
    result = pro.health_score_from_holdings_67(holdings, seed=seed)
    assert result["widget"]["score"] < 70


def test_68_share_card(seed):
    card = pro.build_share_card_68(card_type="health", title="Health 72", summary="Test", seed=seed)
    assert card["card"]["one_click"] is True
    assert card["card"]["disclaimer"]
    assert "utm" in card["share"]["url"]


def test_69_ttv_under_60s(seed):
    result = pro.evaluate_ttv_flow_69(elapsed_seconds=42)
    assert result["target_met"] is True


def test_70_filter_pro(seed):
    result = pro.apply_opportunity_filter_70(filters={"max_risk_score": 8}, user_tier="pro", seed=seed)
    assert result["ok"] is True
    assert result["transparency"]["exclusion_reasons_shown"] is True


def test_70_free_blocked(seed):
    result = pro.apply_opportunity_filter_70(user_tier="free", seed=seed)
    assert result.get("error") == "custom_filter_pro_only"


def test_71_whale_narrative(seed):
    n = pro.build_whale_narrative_71(amount_eth=12000, direction="to_exchange", seed=seed)
    assert "sell pressure" in n["narrative"]["en"].lower() or "exchange" in n["narrative"]["en"].lower()


def test_72_noise_filter(seed):
    noise = pro.classify_onchain_signal_72(is_exchange_internal=True, seed=seed)
    assert noise["classification"] == "noise"
    signal = pro.classify_onchain_signal_72(seed=seed)
    assert signal["signal_probability"] >= 70


def test_73_multi_dim(seed):
    m = pro.build_multi_dim_analysis_73(technical=7, on_chain=6, sentiment=5, macro=4, seed=seed)
    assert m["composite_score"] > 0
    assert len(m["dimensions"]) == 4


def test_74_backtest(seed):
    bt = pro.run_backtest_74(days=90, seed=seed)
    assert bt["no_execution"] is True
    assert bt["performance"]["trade_count"] >= 1


def test_75_alert_policy(seed):
    free = pro.get_alert_policy_75(user_tier="free", seed=seed)
    pro_tier = pro.get_alert_policy_75(user_tier="pro", seed=seed)
    assert free["daily_limit"] == 3
    assert pro_tier["unlimited"] is True


def test_76_journal(seed):
    entry = pro.add_journal_entry_76(asset="ETH", price=3000, prediction="up", reason="test", seed=seed)
    updated = pro.update_journal_actual_76(entry_id=entry["entry"]["entry_id"], actual_price=3200)
    assert updated["entry"]["outcome"] == "matched"


def test_76_journal_tab(seed):
    pro.add_journal_entry_76(asset="BTC", price=1, prediction="up", reason="x", seed=seed)
    tab = pro.build_journal_tab_76(seed=seed)
    assert tab["extends_discipline_ref"] == 66


def test_portfolio_attach(seed):
    out = pro.attach_portfolio_pro_layers_67_76(
        {"holdings": [{"value_usd": 5000, "btc_beta": 0.7}], "risk_score": 6},
        seed=seed,
    )
    assert "health_score_widget" in out
    assert "share_card" in out
    assert "journal_tab" in out


def test_pro_trader_e2e(seed):
    assert pro.run_pro_trader_e2e_67_76(seed=seed)["all_passed"] is True
