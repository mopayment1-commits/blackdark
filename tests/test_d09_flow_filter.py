"""D-09 — Exchange Internal Flow Filter."""

from __future__ import annotations

from exchange_internal_flow_filter import (
    EXCHANGE_HOT_WALLETS,
    FlowClassification,
    classify_flow,
)


def test_internal_confirmed_same_exchange_cluster():
    wallets = list(EXCHANGE_HOT_WALLETS["binance"])
    result = classify_flow(from_address=wallets[0], to_address=wallets[1])
    assert result["classification"] == FlowClassification.INTERNAL_CONFIRMED.value
    assert result["confidence"] >= 0.9


def test_economic_flow_deposit():
    result = classify_flow(
        from_address="1externalwalletaddress",
        to_address="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        is_deposit=True,
        amount_usd=1000.0,
    )
    assert result["classification"] == FlowClassification.ECONOMIC_FLOW.value


def test_unknown_when_unlabeled():
    result = classify_flow(
        from_address="addr_a_unknown",
        to_address="addr_b_unknown",
    )
    assert result["classification"] == FlowClassification.UNKNOWN.value


def test_all_four_classifications_exist():
    values = {c.value for c in FlowClassification}
    assert values == {
        "INTERNAL_CONFIRMED",
        "INTERNAL_LIKELY",
        "ECONOMIC_FLOW",
        "UNKNOWN",
    }
