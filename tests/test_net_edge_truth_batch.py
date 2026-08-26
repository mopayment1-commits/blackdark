"""Tests — #417 Net-Edge Truth Score (Intelligence Ledger core)."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import net_edge_truth_layer as netl
from net_edge_truth import FORMULA_VERSION, compute_net_edge_truth


@pytest.fixture
def net_seed(tmp_path, monkeypatch):
    main = Path("data/net_edge_truth_seed.json")
    p = tmp_path / "net_edge_truth_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(netl, "_SEED_PATH", p)
    return p


def test_417_status(net_seed):
    status = netl.net_edge_truth_layer_status()
    assert status["feature_id"] == 417
    assert status["standalone"] is False
    assert status["formula_version"] == FORMULA_VERSION
    assert status["unknown_costs_never_zero"] is True
    assert status["fail_closed_stale_unfillable"] is True


def test_417_formula_version_documented(net_seed):
    assert FORMULA_VERSION == "2.0.0"
    result = compute_net_edge_truth(
        {
            "net_profit_usdt": 2.5,
            "quote_amount": 500,
            "total_slippage_bps": 3,
            "withdrawal_fee_usdt": 0.05,
            "trading_fees_usdt": 0.2,
            "quote_age_ms": 120,
        }
    )
    assert result["formula_version"] == "2.0.0"
    assert result["feature_ref"] == 417
    assert result["evidence"]["unknown_costs_never_zero"] is True


def test_417_missing_withdrawal_fail_closed(net_seed):
    result = compute_net_edge_truth(
        {
            "net_profit_usdt": 5.0,
            "quote_amount": 1000,
            "total_slippage_bps": 2,
            "trading_fees_usdt": 0.1,
            "quote_age_ms": 100,
        }
    )
    assert result["reject"] is True
    assert "missing_withdrawal_fee" in result["reasons"]


def test_417_worst_case_never_zero(net_seed):
    result = compute_net_edge_truth(
        {
            "net_profit_usdt": 3.0,
            "quote_amount": 1000,
            "total_slippage_bps": 5,
            "trading_fees_usdt": 0.2,
            "quote_age_ms": 200,
            "worst_case_costs": {"withdrawal_fee_usdt": 1.5},
        }
    )
    policies = result.get("cost_policies") or {}
    assert policies["withdrawal"]["source"] == "worst_case_estimate"
    assert result["economics"]["withdrawal_fee_usdt"] == 1.5


def test_417_stale_unfillable_fail_closed(net_seed):
    result = compute_net_edge_truth(
        {
            "net_profit_usdt": 1.5,
            "quote_amount": 1000,
            "total_slippage_bps": 8,
            "withdrawal_fee_usdt": 0.3,
            "trading_fees_usdt": 0.15,
            "quote_age_ms": 300,
            "volume_feasibility": {
                "max_executable_size": 0.0,
                "liquidity_score": 5,
                "signal_suppressed": True,
                "buy_leg": {"verdict": "not_fillable", "stale": True},
                "sell_leg": {"verdict": "not_fillable", "stale": True},
            },
        }
    )
    assert result["reject"] is True
    assert "insufficient_liquidity" in result["reasons"]
    assert "stale_depth_not_fillable" in result["reasons"]


def test_417_fresh_executable_passes(net_seed):
    result = compute_net_edge_truth(
        {
            "net_profit_usdt": 2.5,
            "quote_amount": 500,
            "total_slippage_bps": 3,
            "withdrawal_fee_usdt": 0.05,
            "trading_fees_usdt": 0.2,
            "quote_age_ms": 120,
            "flywheel_net_after_crowd_usd": 2.1,
            "volume_feasibility": {
                "max_executable_size": 1.0,
                "liquidity_score": 85,
                "buy_leg": {"verdict": "full_fill", "stale": False},
                "sell_leg": {"verdict": "full_fill", "stale": False},
            },
        }
    )
    assert result["pass"] is True
    assert result["truth_score"] >= 55
    assert result.get("executable_size") == 1.0
    assert result.get("net_return_pct") is not None


def test_417_arbitrage_integration(net_seed):
    opp = {
        "opportunity_id": "test_arb",
        "asset": "BTC",
        "buy_venue": "okx",
        "sell_venue": "binance",
        "net_edge_usdt": 1.2,
        "slippage_bps": 6,
        "trading_fees_usdt": 0.15,
        "withdrawal_fee_usdt": 0.35,
        "quote_age_ms": 400,
    }
    scored = netl.evaluate_arbitrage_opportunity(opp, enrich_feasibility=True)
    assert scored["ok"] is True
    assert scored["feature_ref"] == 417
    assert "net_edge_truth" in scored
    assert "rejection_reasons" in scored


def test_417_portfolio_scores(net_seed):
    panel = netl.build_portfolio_net_edge_scores("demo_portfolio")
    assert panel["ok"] is True
    assert len(panel["holdings"]) >= 3
    assert panel["truth_score_history"]["total_predictions"] >= 1


def test_417_truth_score_history(net_seed):
    history = netl.build_truth_score_history_panel()
    assert history["total_predictions"] >= 3
    assert history["outcomes_recorded"] >= 1
    assert history["accuracy_rate"] is not None


def test_417_deterministic_regression(net_seed):
    result = netl.run_regression_fixtures()
    assert result["ok"] is True
    assert result["passed"] == result["total"]
    assert result["total"] >= 5


def test_417_reconciliation(net_seed):
    result = netl.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["feature_id"] == 417


def test_417_panel(net_seed):
    panel = netl.build_truth_score_panel()
    assert panel["ok"] is True
    assert panel["formula_version"] == FORMULA_VERSION
