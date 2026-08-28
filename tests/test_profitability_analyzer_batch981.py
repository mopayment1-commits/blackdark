"""Tests — Profitability Analyzer / Net Profit Engine (#981)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import profitability_analyzer as pa


@pytest.fixture
def pa_seed() -> dict:
    return json.loads(Path("data/profitability_analyzer_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _reset():
    pa.reset_profitability_analyzer_state()
    yield
    pa.reset_profitability_analyzer_state()


def test_981_status_no_standalone(pa_seed):
    status = pa.profitability_analyzer_status_981(seed=pa_seed)
    assert status["standalone_rejected"] is True
    assert len(status["fee_categories"]) == 4
    assert status["policy"]["net_profit_default_display"] is True


def test_fee_attribution_four_categories(pa_seed):
    attr = pa.attribute_fees(
        trading_usdt=0.5,
        withdrawal_usdt=4.5,
        deposit_usdt=0.0,
        network_gas_usdt=1.2,
        platform_fee_usdt=0.1,
        trade_id="t1",
        reference_price=42000.0,
        seed=pa_seed,
    )
    assert len(attr["items"]) == 4
    assert attr["platform_fee"]["separate_from_market_fees"] is True
    assert attr["total_market_fees_usdt"] == pytest.approx(6.2)


def test_net_profit_deducts_all_fees(pa_seed):
    pnl = pa.compute_net_profit_engine(
        proceeds_usdt=110.0,
        cost_usdt=100.0,
        trading_fees_usdt=0.5,
        withdrawal_fees_usdt=4.5,
        deposit_fees_usdt=0.0,
        network_gas_usdt=1.2,
        slippage_buffer_usdt=0.3,
        seed=pa_seed,
    )
    assert pnl is not None
    assert pnl["net_profit_usdt"] == pytest.approx(3.5, abs=0.01)
    assert pnl["display"]["default"] == "net"
    assert pnl["gross_profit"]["hidden_by_default"] is True
    assert pnl["fee_completeness"]["network_gas"] is True


def test_gross_hidden_net_default(pa_seed):
    pnl = pa.compute_net_profit_engine(
        proceeds_usdt=110.0,
        cost_usdt=100.0,
        trading_fees_usdt=0.5,
        withdrawal_fees_usdt=4.5,
        deposit_fees_usdt=0.0,
        network_gas_usdt=1.2,
        seed=pa_seed,
    )
    assert pnl is not None
    assert pnl["display"]["gross_hidden"] is True
    assert pnl["display"]["net_profit_usdt"] < pnl["display"]["gross_profit_usdt"]


def test_disclaimer_present(pa_seed):
    pnl = pa.compute_net_profit_engine(
        proceeds_usdt=110.0,
        cost_usdt=100.0,
        trading_fees_usdt=0.5,
        withdrawal_fees_usdt=4.5,
        deposit_fees_usdt=0.0,
        network_gas_usdt=1.2,
        seed=pa_seed,
    )
    assert pnl is not None
    assert "تقدير" in pnl["disclaimer"]


def test_user_gas_override(pa_seed):
    gas = pa.resolve_network_gas_usdt(user_override_usdt=2.5, seed=pa_seed)
    assert gas is not None
    assert gas["source"] == "user_override"
    assert gas["amount_usdt"] == 2.5


def test_cross_exchange_full_pipeline(pa_seed):
    buy = {"bids": [[99.0, 100.0]], "asks": [[100.0, 100.0]]}
    sell = {"bids": [[102.0, 100.0]], "asks": [[103.0, 100.0]]}
    result = pa.compute_cross_exchange_net_profit(
        buy,
        sell,
        buy_exchange="binance",
        sell_exchange="okx",
        symbol="BTC/USDT",
        notional=100.0,
        network_gas_usdt=1.5,
        reference_price=42000.0,
        seed=pa_seed,
    )
    assert result is not None
    assert "fee_attribution" in result
    assert result["network_gas_usdt"] == 1.5
    assert result["net_profit_usdt"] < result["gross_profit_usdt"]
    assert result["profitability_analyzer_ref"] == 981


def test_cross_account_aggregation(pa_seed):
    agg = pa.aggregate_cross_account_fees(
        [
            {"account_id": "ex1", "trading_fees_usdt": 1.0, "network_gas_usdt": 0.5},
            {"account_id": "ex2", "withdrawal_fees_usdt": 4.0, "network_gas_usdt": 1.0},
        ],
        seed=pa_seed,
    )
    assert agg["accounts_count"] == 2
    assert agg["multi_account_sync_ref"] == 907
    assert agg["totals"]["trading_fees_usdt"] == 1.0


def test_production_gate(pa_seed):
    gate = pa.check_production_gate_981(seed=pa_seed)
    assert gate["fee_completeness"] is True
    assert gate["checks"]["four_fee_categories"] is True


def test_e2e_981(pa_seed):
    result = pa.run_profitability_analyzer_e2e_981(seed=pa_seed)
    assert result["all_passed"] is True
    assert result["ok"] is True


def test_fail_closed_without_gas(pa_seed):
    pnl = pa.compute_net_profit_engine(
        proceeds_usdt=110.0,
        cost_usdt=100.0,
        trading_fees_usdt=0.5,
        withdrawal_fees_usdt=4.5,
        deposit_fees_usdt=0.0,
        seed=pa_seed,
    )
    assert pnl is None
