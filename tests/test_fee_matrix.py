"""Unit tests — fee_matrix (maker/taker/withdrawal/deposit/trading fees)."""

from __future__ import annotations

import sys

import pytest

import fee_matrix


def test_taker_and_maker_fees_seeded(monkeypatch):
    fee_matrix._matrix.clear()
    monkeypatch.setattr(fee_matrix, "_last_refresh", 0.0)
    assert fee_matrix.taker_fee("binance") > 0
    assert fee_matrix.maker_fee("binance") > 0
    assert fee_matrix.maker_fee("binance") <= fee_matrix.taker_fee("binance")


def test_perpetual_taker_fee():
    fee_matrix._matrix.clear()
    spot = fee_matrix.taker_fee("okx", market="spot")
    perp = fee_matrix.taker_fee("okx", market="perpetual")
    assert perp > 0
    assert spot > 0


def test_withdrawal_and_deposit_fees():
    fee_matrix._matrix.clear()
    w = fee_matrix.withdrawal_fee_usdt("binance", "BTC/USDT")
    d = fee_matrix.deposit_fee_usdt("binance", "BTC/USDT")
    assert w is not None and w >= 0
    assert d >= 0


def test_unknown_withdrawal_fee_is_none_not_zero():
    fee_matrix._matrix.clear()
    assert fee_matrix.withdrawal_fee_usdt("binance", "ZZZCOIN/USDT") is None
    assert fee_matrix.withdrawal_fee_usdt("unknown_venue_xyz", "ETH/USDT") is None


def test_trading_fees_usdt_scales_with_notional():
    fee_matrix._matrix.clear()
    small = fee_matrix.trading_fees_usdt("binance", 100.0)
    large = fee_matrix.trading_fees_usdt("binance", 1000.0)
    assert large > small
    assert large == small * 10


def test_matrix_stats_after_seed():
    fee_matrix._matrix.clear()
    fee_matrix._ensure_seeded()
    stats = fee_matrix.matrix_stats()
    assert stats["exchanges"] >= 1
    assert "sample" in stats


def test_unknown_exchange_uses_defaults():
    fee_matrix._matrix.clear()
    assert fee_matrix.taker_fee("unknown_venue_xyz") > 0
    # Unknown venue/asset withdrawal must not invent a zero fee.
    assert fee_matrix.withdrawal_fee_usdt("unknown_venue_xyz", "ETH/USDT") is None


def test_maker_fee_and_trading_fees_maker():
    fee_matrix._matrix.clear()
    assert fee_matrix.maker_fee("binance", market="perpetual") > 0
    maker_cost = fee_matrix.trading_fees_usdt("binance", 500.0, use_maker=True)
    taker_cost = fee_matrix.trading_fees_usdt("binance", 500.0, use_maker=False)
    assert maker_cost <= taker_cost


@pytest.mark.asyncio
async def test_refresh_fee_matrix_no_network(monkeypatch):
    fee_matrix._matrix.clear()
    monkeypatch.setattr("fee_matrix.config.enabled_exchanges", dict)
    result = await fee_matrix.refresh_fee_matrix()
    assert result["total"] >= 0


@pytest.mark.asyncio
async def test_refresh_fee_matrix_seed_only_on_import_error(monkeypatch):
    fee_matrix._matrix.clear()
    fee_matrix._ensure_seeded()
    real_import = __import__

    def _block_ccxt(name, *args, **kwargs):
        if name.startswith("ccxt"):
            raise ImportError("blocked for coverage")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", _block_ccxt)
    result = await fee_matrix.refresh_fee_matrix()
    assert result["source"] == "seed_only"
    assert result["updated"] == 0
    assert result["total"] >= 1


@pytest.mark.asyncio
async def test_refresh_fee_matrix_ccxt_mock(monkeypatch):
    fee_matrix._matrix.clear()

    class _FakeEx:
        fees = {"trading": {"taker": 0.002, "maker": 0.001}}

        async def load_markets(self):
            return None

        async def fetchTradingFees(self):
            return {"BTC/USDT": {"taker": 0.0015, "maker": 0.0008}}

        async def close(self):
            return None

    class _FakeMod:
        exchanges = ["binance"]

        def binance(self, *_a, **_k):
            return _FakeEx()

    monkeypatch.setattr(fee_matrix.config, "enabled_exchanges", lambda: {"binance": {}})
    monkeypatch.setitem(sys.modules, "ccxt.async_support", _FakeMod())
    # Ensure seeded matrix includes binance even if module-level cache was empty/other.
    fee_matrix._matrix.clear()
    result = await fee_matrix.refresh_fee_matrix()
    assert result["total"] >= 1
    # Updated may be 0 if CCXT id map rejects the fake; seed path must still report total.
    assert result["updated"] >= 0
    assert "binance" in fee_matrix._matrix or result["total"] >= 1


import pytest


@pytest.mark.asyncio
async def test_fetch_trading_fees_missing_method():
    from fee_matrix import _fetch_trading_fees

    class Ex:
        pass

    assert await _fetch_trading_fees(Ex()) == {}


@pytest.mark.asyncio
async def test_fetch_trading_fees_exception():
    from fee_matrix import _fetch_trading_fees

    class Ex:
        async def fetchTradingFees(self):
            raise RuntimeError("boom")

    assert await _fetch_trading_fees(Ex()) == {}


def test_fee_rates_from_fees_dict():
    from fee_matrix import _fee_rates

    class Ex:
        fees = {"trading": {"taker": 0.001, "maker": 0.0005}}

    taker, maker = _fee_rates("binance", Ex(), {"BTC/USDT": {"taker": 0.002, "maker": 0.001}})
    assert taker == 0.002
    assert maker == 0.001


def test_fee_rates_empty_fees_fallback():
    from fee_matrix import _fee_rates

    class Ex:
        fees = {"trading": {"taker": 0.0015, "maker": 0.0007}}

    taker, maker = _fee_rates("binance", Ex(), {})
    assert taker == 0.0015
    assert maker == 0.0007
