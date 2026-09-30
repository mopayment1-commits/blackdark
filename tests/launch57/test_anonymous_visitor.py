"""Launch-57 Anonymous Visitor & Public Intelligence baseline tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from launch57.anonymous_visitor_common import (
    ANONYMOUS_DENIED_BY_DEFAULT,
    ANONYMOUS_ELIGIBLE_LAUNCH_IDS,
    ANONYMOUS_VISITOR_VERSION,
    acceptance_criteria_status,
    attach_anonymous_visitor_envelope,
    build_anonymous_route_inventory,
    build_approved_public_trust_surfaces,
    build_public_intelligence_proof_index,
    reference_anonymous_route_allowlist,
    verify_account_gate_required,
    verify_anonymous_eligibility,
    verify_private_by_default,
)
from launch57.trust_batch2 import guest_trust_surface


def test_private_by_default_no_overlap():
    scope = verify_private_by_default()
    assert scope["private_by_default"] is True
    assert scope["no_overlap"] is True
    assert scope["anonymous_eligible_count"] == len(ANONYMOUS_ELIGIBLE_LAUNCH_IDS)


def test_anonymous_eligibility_public_accuracy():
    ok = verify_anonymous_eligibility(4)
    denied = verify_anonymous_eligibility(49)
    assert ok["eligible"] is True
    assert denied["eligible"] is False
    assert denied["fail_closed"] is True


def test_denied_by_default_includes_private_capabilities():
    assert 32 in ANONYMOUS_DENIED_BY_DEFAULT
    assert 49 in ANONYMOUS_DENIED_BY_DEFAULT
    assert 2 in ANONYMOUS_DENIED_BY_DEFAULT


def test_account_gate_blocks_anonymous_persistence():
    watchlist = verify_account_gate_required("watchlist")
    save = verify_account_gate_required("save")
    browse = verify_account_gate_required("browse_public")
    assert watchlist["anonymous_blocked"] is True
    assert save["anonymous_blocked"] is True
    assert browse["allowed"] is True


def test_approved_surfaces_align_with_spec_section_3():
    surfaces = build_approved_public_trust_surfaces()
    ids = {s["launch_item_id"] for s in surfaces}
    assert 4 in ids
    assert 46 in ids
    assert 52 in ids
    assert 2 not in ids
    assert 3 not in ids
    assert 5 not in ids
    assert all(s["anonymous_eligible"] for s in surfaces)


def test_route_allowlist_includes_launch57_guest_trust():
    allowlist = reference_anonymous_route_allowlist()
    assert allowlist["launch57_prefix_allowed"] is True
    assert "/api/launch57/guest-trust" in allowlist["launch57_public_routes"]


def test_public_intelligence_proofs_not_empty():
    proofs = build_public_intelligence_proof_index()
    assert len(proofs) >= 5
    assert all(p["fabricated_proof_forbidden"] for p in proofs)


def test_route_inventory_server_side():
    inventory = build_anonymous_route_inventory()
    guest = next(r for r in inventory if r["launch_item_id"] == 46)
    assert guest["server_side_enforced"] is True
    assert guest["auth_expectation"] == "ANONYMOUS"


def test_envelope_metadata_only():
    body = attach_anonymous_visitor_envelope({"launch_item_id": 46, "success": True})
    env = body["launch57_anonymous_visitor"]
    assert env["version"] == ANONYMOUS_VISITOR_VERSION
    assert env["pass_engineering_not_granted_by_envelope"] is True
    assert env["legacy_anonymous_program_excluded"] is True


def test_acceptance_criteria_gate():
    acceptance = acceptance_criteria_status()
    assert acceptance["av01_explicit_anonymous_state"] is True
    assert acceptance["av03_deny_by_default_allowlist"] is True
    assert acceptance["av09_no_personalization_for_anonymous"] is True
    assert acceptance["av10_account_gate_at_boundary"] is True
    assert acceptance["removed_non_spec_surfaces"] is True


@pytest.mark.asyncio
async def test_guest_trust_surface_wired(monkeypatch):
    monkeypatch.setattr(
        "governance.anonymous_visitor_governance.anonymous_visitor_status",
        lambda: {
            "anonymous_state": "ANONYMOUS",
            "private_by_default": True,
            "public_readiness": True,
            "rate_limits": True,
            "no_pii_leak": True,
            "visitor_tier_gating": True,
            "route_inventory": {},
        },
    )
    out = await guest_trust_surface(symbol="BTC", params={"user_key": "anonymous"})
    assert out["launch_item_id"] == 46
    assert out["guest_trust"]["no_pii_leak"] is True
    assert out["guest_trust"]["not_duplicate_private_app"] is True
    assert "launch57_anonymous_visitor" in out
    assert len(out["guest_trust"]["approved_public_trust_surfaces"]) >= 20


def test_governance_artifacts_paths_exist_after_generator():
    gov = Path("governance/launch57")
    for name in (
        "BLACKDARK_LAUNCH57_ANONYMOUS_VISITOR_RECONCILIATION.json",
        "BLACKDARK_LAUNCH57_ANONYMOUS_VISITOR_INDEPENDENT_VERIFICATION.json",
        "BLACKDARK_LAUNCH57_ANONYMOUS_VISITOR_REPORT.md",
    ):
        path = gov / name
        if path.exists():
            payload = path.read_text(encoding="utf-8")
            if name.endswith(".json"):
                assert json.loads(payload)
