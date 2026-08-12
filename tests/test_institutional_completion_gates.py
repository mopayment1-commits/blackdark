"""Institutional Completion Program — behavioral gate certification tests."""

from __future__ import annotations

import asyncio

import pytest


def test_gate1_canonical_and_streaming_verified():
    from institutional_gate_cert import certify_gate1_data_truth

    out = certify_gate1_data_truth()
    assert out["passed"] is True
    assert out["canonical"] == "VERIFIED_COMPLETE"
    assert out["streaming"] == "VERIFIED_COMPLETE"
    assert out["bypasses"] == 0
    assert out["stale_as_live"] == 0


def test_gate1_adversarial_symbol_venue_collision():
    from canonical_adoption import adopt_symbol, adopt_venue
    from canonical_data_layer import reset_store_for_tests

    reset_store_for_tests()
    assert adopt_venue("BinanceUSDM") == adopt_venue("binance")
    assert adopt_symbol("btcusdt") == adopt_symbol("BTC-USDT") == "BTC/USDT"
    with pytest.raises(ValueError):
        adopt_symbol("")
    with pytest.raises(ValueError):
        adopt_venue("")


def test_gate2_oms_reconcile_and_jupiter_fail_closed():
    from institutional_gate_cert import certify_gate2_financial_execution

    out = certify_gate2_financial_execution()
    assert out["passed"] is True
    assert out["jupiter_stub_reachable"] is False
    assert out["unknown_fee_as_zero"] == 0


@pytest.mark.asyncio
async def test_gate2_oms_submit_dry_run_pipeline():
    import oms
    import time

    intent = oms.create_intent(
        org_id="t",
        venue="binance",
        symbol="ETH/USDT",
        side="buy",
        quantity=0.01,
        limit_price=2000.0,
        idempotency_key=f"gate2-oms-submit-{time.time_ns()}",
        actor="test",
    )
    result = await oms.submit_to_venue(intent["order_id"], actor="test", dry_run=True)
    assert result["blocked"] is False
    assert result["oms_state"] in {"ACK", "FILL", "RECONCILE", "SUBMISSION"}


def test_gate3_risk_suite_blocks_unsafe():
    from institutional_gate_cert import certify_gate3_risk

    out = certify_gate3_risk()
    assert out["passed"] is True
    assert out["unsafe_execution_after_risk_failure"] == 0


def test_gate4_decision_brain_unified():
    from institutional_gate_cert import certify_gate4_decision_brain

    out = certify_gate4_decision_brain()
    assert out["passed"] is True
    assert out["hallucinated_evidence"] == 0
    assert out["uncalibrated_probability_claims"] == 0


def test_gate5_super_terminal_whale_portfolio_b2b():
    from institutional_gate_cert import certify_gate5_product

    out = certify_gate5_product()
    assert out["passed"] is True
    assert out["super_terminal"] == "VERIFIED_COMPLETE"
    assert out["whale"] == "VERIFIED_COMPLETE"
    assert out["portfolio"] == "VERIFIED_COMPLETE"
    assert out["b2b"] == "VERIFIED_COMPLETE"


def test_gate6_stub_sweep_clean():
    from institutional_gate_cert import certify_gate6_hardening

    out = certify_gate6_hardening()
    assert out["passed"] is True
    assert out["production_stub_mock_fake"] == 0


def test_all_gates_bundle():
    from institutional_gate_cert import run_all_gates

    # Gate2 uses asyncio.get_event_loop().run_until_complete — ensure loop exists.
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    out = run_all_gates()
    assert out["passed"] is True


def test_portfolio_dashboard_mapper():
    from portfolio_intelligence import holdings_from_dashboard_assets

    rows = holdings_from_dashboard_assets(
        [{"symbol": "BTC", "quantity": 1, "price": 50_000, "side": "long"}]
    )
    assert rows[0]["notional_usd"] == 50_000.0
