"""Money Decimal policy unit tests."""

from __future__ import annotations

from decimal import Decimal

import money_decimal as md


def test_float_roundtrip_avoids_binary_expansion():
    assert md.d(0.1) + md.d(0.2) == Decimal("0.3")


def test_apply_fee_and_net():
    fee = md.apply_fee(1000, "0.001")
    assert fee == Decimal("1.0000")
    net = md.net_after_costs(100.0, costs=[1.0, "0.25", 0.1])
    assert float(net) == 98.65


def test_crypto_and_fiat_precision_policy():
    assert md.crypto_money("1.123456789") == Decimal("1.12345679")
    assert md.fiat_money("10.125") == Decimal("10.13")
    meta = md.financial_audit_metadata(asset_type="fiat")
    assert meta["precision"] == 2


def test_net_cross_uses_decimal_model():
    import profit_fee_algorithms as pfa

    buy = {"bids": [[99.0, 100.0]], "asks": [[100.0, 100.0]]}
    sell = {"bids": [[102.0, 100.0]], "asks": [[103.0, 100.0]]}
    row = pfa.net_cross_exchange_profit(
        buy,
        sell,
        buy_exchange="binance",
        sell_exchange="okx",
        symbol="BTC/USDT",
        notional=100.0,
    )
    assert row is not None
    assert row.get("money_model") == "decimal_half_even"
