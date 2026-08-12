"""Institutional Completion Program — behavioral gate evidence tests (honest)."""

from __future__ import annotations

import asyncio
import time

import pytest


def test_gate1_canonical_streaming_evidence_not_self_labeled_complete():
    from institutional_gate_cert import certify_gate1_data_truth

    out = certify_gate1_data_truth()
    assert out["passed"] is True
    assert out["stale_as_live"] == 0
    assert out["canonical"] != "VERIFIED_COMPLETE"
    assert out["canonical_adoption_pct"] > 0
    assert out["bypasses_unproven"] >= 0


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


def test_gate2_oms_reconcile_mismatch_records_safely():
    from institutional_gate_cert import certify_gate2_financial_execution

    out = certify_gate2_financial_execution()
    assert out["passed"] is True
    assert out["oms_reconcile_mismatch_ok"] is True
    assert out["jupiter_live_submit"] == "NOT_IMPLEMENTED"
    assert out["unknown_fee_as_zero"] == 0


@pytest.mark.asyncio
async def test_gate2_oms_submit_dry_run_pipeline():
    import oms

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


def test_gate3_risk_suite_no_domain_inflation():
    from institutional_gate_cert import certify_gate3_risk

    out = certify_gate3_risk()
    assert out["passed"] is True
    assert "venue" in out["domains_computed"]
    assert out["unsafe_execution_after_risk_failure"] == 0


def test_gate4_decision_brain_loop():
    from institutional_gate_cert import certify_gate4_decision_brain

    out = certify_gate4_decision_brain()
    assert out["passed"] is True
    assert out["loop_closed"] is True
    assert out["hallucinated_evidence"] == 0


def test_gate5_product_surfaces_partial_with_delivery():
    from institutional_gate_cert import certify_gate5_product

    out = certify_gate5_product()
    assert out["passed"] is True
    assert out["alert_delivered"] is True
    assert out["derivatives_computed"] is True
    assert out["super_terminal"] == "PARTIAL"


def test_gate6_stub_sweep_and_live_probe_recorded():
    from institutional_gate_cert import certify_gate6_hardening

    out = certify_gate6_hardening()
    assert out["passed"] is True
    assert out["production_stub_mock_fake"] == 0
    assert "live_public_probe" in out


def test_all_gates_bundle_no_hardcoded_verified_complete():
    from institutional_gate_cert import run_all_gates

    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    out = run_all_gates()
    assert out["passed"] is True
    assert out["hardcoded_verified_complete_present"] is False


def test_portfolio_dashboard_mapper():
    from portfolio_intelligence import holdings_from_dashboard_assets

    rows = holdings_from_dashboard_assets(
        [{"symbol": "BTC", "quantity": 1, "price": 50_000, "side": "long"}]
    )
    assert rows[0]["notional_usd"] == 50_000.0


@pytest.mark.asyncio
async def test_live_data_truth_probe_fail_closed_or_live():
    from live_data_truth_probe import probe_binance_public_book

    out = await probe_binance_public_book("BTCUSDT")
    assert "ok" in out
    if out["ok"]:
        assert out["live"] is True
        assert out["executable_quotes"] is True
        assert out["venue"] == "binance"
    else:
        assert out["live"] is False
        assert out["executable_quotes"] is False
