"""Tests — #467 Stablecoin Health + #472 Investment Thesis + #474 Daily Market Brief."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import capital_protection_controls as cpc
from bd_platform import daily_market_brief as dmb
from bd_platform import investment_thesis_scoring as its
from bd_platform import net_edge_truth_layer as netl
from bd_platform import stablecoin_health_monitor as shm
from bd_platform import unified_arbitrage_engine as uae


@pytest.fixture
def shm_seed(tmp_path, monkeypatch):
    main = Path("data/stablecoin_health_monitor_seed.json")
    p = tmp_path / "stablecoin_health_monitor_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(shm, "_SEED_PATH", p)
    return p


@pytest.fixture
def its_seed(tmp_path, monkeypatch):
    main = Path("data/investment_thesis_scoring_seed.json")
    p = tmp_path / "investment_thesis_scoring_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(its, "_SEED_PATH", p)
    return p


@pytest.fixture
def dmb_seed(tmp_path, monkeypatch):
    main = Path("data/daily_market_brief_seed.json")
    p = tmp_path / "daily_market_brief_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(dmb, "_SEED_PATH", p)
    return p


# --- #467 Stablecoin Health Monitor ---


def test_467_status(shm_seed):
    status = shm.stablecoin_health_monitor_status()
    assert status["feature_id"] == 467
    assert status["legal_name"] == "Stablecoin Health Monitor"
    assert "De-Pegging" not in status["legal_name"]
    assert status["standalone"] is False


def test_467_stablecoin_grade(shm_seed):
    usdt = shm.analyze_stablecoin("USDT")
    assert usdt["ok"] is True
    assert usdt["stablecoin_grade"] in ("AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D")
    assert 0 <= usdt["depeg_probability"] <= 1
    assert len(usdt["indicators"]) >= 5


def test_467_portfolio_exposure_alert(shm_seed):
    alerts = shm.build_portfolio_stablecoin_alerts()
    assert alerts["exposure_threshold_pct"] == 30
    assert alerts["alerts_only"] is True


def test_467_arbitrage_cancel_gate(shm_seed):
    cancel = shm.should_cancel_stablecoin_arbitrage(
        {"opportunity_type": "stablecoin_depeg", "pair": "USDT/USDC"}
    )
    assert "cancel" in cancel
    assert cancel["feature_ref"] == 467


def test_467_capital_protection_integration(shm_seed):
    panel = cpc.build_capital_awareness_panel()
    sc = panel.get("stablecoin_health_467") or {}
    assert sc.get("feature_ref") == 467
    assert (sc.get("panel") or {}).get("ok") is True


def test_467_reconciliation(shm_seed):
    result = shm.run_reconciliation_tests()
    assert result["ok"] is True


# --- #472 Investment Thesis Scoring ---


def test_472_status(its_seed):
    status = its.investment_thesis_scoring_status()
    assert status["feature_id"] == 472
    assert status["not_price_probability"] is True
    assert len(status["mandatory_dimensions"]) == 6


def test_472_six_dimensions(its_seed):
    btc = its.score_investment_thesis("BTC")
    assert btc["ok"] is True
    assert btc["dimension_count"] == 6
    assert btc["thesis_grade"] in ("A", "B", "C", "D", "F")
    assert btc["rubric_version"] == "1.0.0"
    assert btc["not_price_probability"] is True


def test_472_net_edge_confidence(its_seed):
    adj = its.apply_thesis_to_confidence(
        {"asset": "BTC"},
        truth_result={"truth_score": 70},
    )
    assert adj["ok"] is True
    assert adj["not_price_probability"] is True
    assert 0 <= adj["adjusted_confidence"] <= 1


def test_472_market_radar_card(its_seed):
    card = its.build_market_radar_thesis_card("ETH")
    assert card["thesis_grade"] is not None
    assert card["not_price_probability"] is True


def test_472_net_edge_layer_integration(its_seed):
    result = netl.evaluate_arbitrage_opportunity({"asset": "BTC", "opportunity_type": "cross_venue"})
    thesis = result.get("thesis_confidence_472") or {}
    assert thesis.get("not_price_probability") is True


def test_472_reconciliation(its_seed):
    result = its.run_reconciliation_tests()
    assert result["ok"] is True


# --- #474 Daily Market Brief ---


def test_474_status(dmb_seed):
    status = dmb.daily_market_brief_status()
    assert status["feature_id"] == 474
    assert status["legal_name"] == "Daily Market Brief"
    assert status["template_based_v1"] is True
    assert status["no_generic_ai_prose"] is True


def test_474_three_sections(dmb_seed):
    brief = dmb.generate_daily_brief()
    assert brief["section_count"] == 3
    assert len(brief["what_changed"]) >= 1
    assert len(brief["why"]) >= 1
    assert len(brief["risks"]) >= 1


def test_474_evidence_links(dmb_seed):
    brief = dmb.generate_daily_brief()
    all_items = brief["what_changed"] + brief["why"] + brief["risks"]
    assert all(i.get("evidence_link") for i in all_items)
    assert brief["contributors_match_calculations"] is True


def test_474_event_context_443(dmb_seed):
    brief = dmb.generate_daily_brief()
    assert len(brief.get("event_context_443") or []) >= 1


def test_474_market_radar_first(dmb_seed):
    radar = dmb.build_market_radar_brief_first()
    assert radar["dashboard_position"] == "first"
    assert (radar.get("daily_brief_474") or {}).get("ok") is True


def test_474_unified_arbitrage_radar(dmb_seed, its_seed, shm_seed):
    radar = uae.build_market_radar_integration()
    assert radar["dashboard_position_first"] == "daily_brief_474"
    assert (radar.get("daily_brief_474") or {}).get("ok") is True
    assert radar["thesis_cards_472"]["BTC"]["thesis_grade"] is not None


def test_474_reconciliation(dmb_seed):
    result = dmb.run_reconciliation_tests()
    assert result["ok"] is True


def test_batch_reconciliation(shm_seed, its_seed, dmb_seed):
    uae_result = uae.run_reconciliation_tests()
    assert uae_result["ok"] is True
