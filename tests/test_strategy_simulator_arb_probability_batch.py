"""Tests — #421 Strategy Simulator merge + #422 Arbitrage Probability Signal."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import arbitrage_probability_signal as aps
from bd_platform import strategy_simulator as ss
from bd_platform import unified_arbitrage_engine as uae


@pytest.fixture
def ss_seed(tmp_path, monkeypatch):
    main = Path("data/strategy_simulator_seed.json")
    p = tmp_path / "strategy_simulator_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ss, "_SEED_PATH", p)
    return p


@pytest.fixture
def aps_seed(tmp_path, monkeypatch):
    main = Path("data/arbitrage_probability_signal_seed.json")
    p = tmp_path / "arbitrage_probability_signal_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(aps, "_SEED_PATH", p)
    return p


@pytest.fixture
def uae_seed(tmp_path, monkeypatch):
    main = Path("data/unified_arbitrage_engine_seed.json")
    p = tmp_path / "unified_arbitrage_engine_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(uae, "_SEED_PATH", p)
    return p


# --- #421 merged into #411 ---


def test_421_merged_status(ss_seed):
    status = ss.strategy_simulator_status()
    assert status["feature_id"] == 411
    assert status["merged_feature_id"] == 421
    assert status["components"]["order_simulator_421"] is True
    assert status["components"]["realistic_fees_slippage"] is True


def test_421_simulate_order_fee_db(ss_seed):
    result = ss.simulate_paper_order(symbol="BTC", side="buy", quantity=0.01, price=65000, venue="binance")
    assert result["ok"] is True
    assert result["no_real_execution"] is True
    assert result["order"]["fees"]["fee_source"] == "fee_matrix_db"
    assert "no real execution" in result["display"].lower()


def test_421_unknown_venue_blocked(ss_seed):
    result = ss.simulate_paper_order(symbol="BTC", side="buy", quantity=0.01, price=65000, venue="unknown_venue_xyz")
    assert result["ok"] is False
    assert result["error"] == "unknown_venue_fee"


def test_421_paper_account_pnl(ss_seed):
    account = ss.build_paper_account()
    assert account["ok"] is True
    assert account["no_real_execution"] is True
    pnl = account["paper_account"]
    assert pnl["total_pnl_usd"] is not None
    assert pnl["return_pct"] is not None


def test_421_slippage_options(ss_seed):
    result = ss.simulate_paper_order(
        symbol="BTC", side="buy", quantity=0.5, price=65000, venue="binance", slippage_bps=12
    )
    assert result["order"]["slippage"]["slippage_bps"] == 12
    assert result["order"]["slippage"]["source"] == "user_specified"


def test_421_reconciliation(ss_seed):
    result = ss.run_reconciliation_tests()
    assert result["ok"] is True


# --- #422 Arbitrage Probability Signal ---


def test_422_status(aps_seed):
    status = aps.arbitrage_probability_signal_status()
    assert status["feature_id"] == 422
    assert status["standalone"] is False
    assert status["ml_disabled_v1"] is True
    assert "Predictive" not in status["legal_name"]


def test_422_probability_score(aps_seed):
    sig = aps.compute_probability_signal("BTC")
    assert 0 <= sig["probability_score_pct"] <= 100
    assert sig["confidence_level"] in ("high", "medium", "low", "very_low")
    assert sig["expected_formation_time"]["not_fixed_seconds"] is True
    assert len(sig["component_breakdown"]) == 4


def test_422_net_edge_integration(aps_seed):
    sig = aps.compute_probability_signal("BTC")
    enriched = aps.enrich_with_integrations(sig)
    assert enriched.get("net_edge_projection_417") is not None
    assert enriched["net_edge_projection_417"]["feature_ref"] == 417


def test_422_probability_backtest(aps_seed):
    bt = aps.build_probability_backtest()
    assert bt["meets_fpr_target"] is True
    assert bt["false_positive_rate"] <= bt["fpr_target"]
    assert bt["cancelled_sla"]["accuracy_95_pct"] is True


def test_422_scan_signals(aps_seed):
    signals = aps.scan_probability_signals()
    assert len(signals) >= 3
    assert signals[0]["probability_score_pct"] >= signals[-1]["probability_score_pct"]


def test_422_unified_arbitrage_integration(uae_seed, aps_seed):
    feed = uae.build_unified_feed()
    opps = feed.get("opportunities") or []
    assert len(opps) >= 1
    assert "arbitrage_probability_signal" in opps[0]


def test_422_reconciliation(aps_seed):
    result = aps.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["feature_id"] == 422
