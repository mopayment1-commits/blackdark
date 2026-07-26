"""Tests for CEX↔DEX scanner helpers."""

from __future__ import annotations

from bd_platform.cex_dex_arbitrage import _best_cex, _execution_feasibility


def test_best_cex_buy_sell():
    prices = {"binance": 100.0, "okx": 100.5}
    assert _best_cex(prices, side="buy")[0] == "binance"
    assert _best_cex(prices, side="sell")[0] == "okx"


def test_execution_feasibility():
    assert _execution_feasibility(30, 50_000, 1000) == "high"
    assert _execution_feasibility(5, 50_000, 1000) == "below_threshold"
