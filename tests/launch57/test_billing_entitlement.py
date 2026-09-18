"""Launch-57 Billing, Subscription & Entitlement baseline tests."""

from __future__ import annotations

import json
from pathlib import Path

from launch57.billing_entitlement_common import (
    INTERNAL_BILLING_COMPONENTS,
    BillingState,
    EntitlementState,
    acceptance_criteria_status,
    attach_billing_entitlement_envelope,
    build_billing_touchpoint_matrix,
    record_billing_entitlement_signal,
    resolve_billing_context,
    verify_billing_entitlement_separation,
    verify_capability_entitlement,
    verify_financial_arithmetic,
    verify_launch57_capability_scope,
    verify_no_unverified_paid_grant,
)


def test_internal_components_registry():
    from launch57.billing_entitlement_common import build_billing_component_registry

    registry = build_billing_component_registry()
    assert len(registry) == len(INTERNAL_BILLING_COMPONENTS)
    for row in registry:
        assert row["launch_scope"] == "LAUNCH57"


def test_billing_entitlement_separation():
    sep = verify_billing_entitlement_separation(
        billing_state=BillingState.ACTIVE.value,
        entitlement_state=EntitlementState.PAID_ACTIVE.value,
    )
    assert sep["direct_webhook_to_tier_forbidden"] is True
    assert sep["redirect_grant_forbidden"] is True


def test_unverified_redirect_blocked():
    check = verify_no_unverified_paid_grant(
        grant_source="checkout_redirect",
        verified=False,
    )
    assert check["allowed"] is False
    assert check["fail_closed"] is True


def test_unsigned_webhook_blocked():
    check = verify_no_unverified_paid_grant(
        grant_source="unsigned_webhook",
        verified=False,
    )
    assert check["fail_closed"] is True


def test_launch57_scope_only():
    in_scope = verify_launch57_capability_scope(49)
    out_scope = verify_launch57_capability_scope(999)
    assert in_scope["in_launch57_scope"] is True
    assert out_scope["parked_capabilities_sellable"] is False


def test_capability_entitlement_server_side():
    result = verify_capability_entitlement(
        launch_item_id=49,
        requested_tier="free",
        effective_tier="free",
    )
    assert result["server_side_enforced"] is True
    assert result["client_only_gating"] is False
    assert result["allowed"] is True


def test_financial_arithmetic_uses_minor_units():
    result = verify_financial_arithmetic(1999)
    assert result["integer_minor_units"] is True
    assert result["float_used_for_money"] is False
    assert result["amount_cents"] == 1999


def test_attach_envelope_free_tier():
    body = {
        "launch_item_id": 49,
        "success": True,
        "personal_decision_history": {"count": 0},
    }
    out = attach_billing_entitlement_envelope(
        body,
        launch_item_id=49,
        params={"tier": "free"},
    )
    assert out["success"] is True
    envelope = out["launch57_billing_entitlement"]
    assert envelope["billing_context"]["tier"] == "free"
    assert envelope["capability_entitlement"]["allowed"] is True
    assert envelope["pass_live_not_claimed"] is True


def test_attach_envelope_reports_unverified_paid_tier_param():
    body = {"launch_item_id": 33, "success": True}
    out = attach_billing_entitlement_envelope(
        body,
        launch_item_id=33,
        params={"tier": "pro"},
    )
    envelope = out["launch57_billing_entitlement"]
    assert envelope["unverified_grant_check"]["verified"] is False
    assert envelope["billing_context"]["tier"] == "free"
    assert envelope["entitlement_resolution"]["unverified_paid_claim"] is True


def test_touchpoint_matrix():
    matrix = build_billing_touchpoint_matrix()
    by_id = {row["launch_item_id"]: row for row in matrix}
    assert by_id[32]["wired"] is True
    assert by_id[49]["tier_variables"] is not None


def test_record_billing_signal(tmp_path, monkeypatch):
    store = tmp_path / "signals.jsonl"
    monkeypatch.setattr(
        "launch57.billing_entitlement_common._SIGNAL_STORE",
        store,
    )
    row = record_billing_entitlement_signal(
        signal_type="entitlement_evaluated",
        launch_item_id=33,
        detail="tier=pro",
    )
    assert row["signal_type"] == "entitlement_evaluated"
    lines = store.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["launch_item_id"] == 33


def test_resolve_effective_tier_caps_client_pro():
    from launch57.billing_entitlement_common import resolve_effective_entitlement_tier

    row = resolve_effective_entitlement_tier({"tier": "pro"})
    assert row["effective_tier"] == "free"
    assert row["unverified_paid_claim"] is True


def test_enforce_launch57_entitlement_smart_alerts():
    from launch57.billing_entitlement_common import enforce_launch57_entitlement

    gate = enforce_launch57_entitlement(launch_item_id=33, params={"tier": "pro"})
    assert gate["allowed"] is False
    assert gate["server_side_enforced"] is True


def test_acceptance_criteria_engineering_gate():
    acceptance = acceptance_criteria_status()
    assert acceptance["ac03_billing_separate_from_entitlement"] is True
    assert acceptance["ac04_redirect_cannot_grant"] is True
    assert acceptance["ac10_launch57_capabilities_only"] is True
    assert acceptance["ac20_no_false_pass_live"] is True
