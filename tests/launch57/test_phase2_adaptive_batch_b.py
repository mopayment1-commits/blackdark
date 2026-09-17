"""Launch-57 Phase 2 Adaptive Batch B — builder verification tests (#47→#48→#44→#45→#46)."""

from __future__ import annotations

import pytest

from launch57.trust_batch2 import (
    abstain_reject_reasons_visible,
    guest_trust_surface,
    one_click_risk_disclosure,
    shareable_accuracy_page,
    shareable_decision_card,
)


@pytest.mark.asyncio
async def test_capability_47_material_risk_direct_access():
    out = await one_click_risk_disclosure(
        symbol="BTC",
        params={
            "decision_truth_state": "REJECTED",
            "decision_truth": {
                "contract": {
                    "decision_state": "REJECTED",
                    "net_edge": {"expected_net_edge_bps": -5},
                    "grade": "F",
                    "evidence_class": "SHADOW_LIVE_FORWARD",
                }
            },
        },
    )
    assert out["launch_item_id"] == 47
    assert out["material_risk"]["direct_access"] is True
    assert out["risk_disclosure"]["material_risk"]["direct_access"] is True
    assert out["adaptive_disclosure"]["level_1"]["launch_item_id"] == 47
    assert out["safety_floor_visible"] is True


@pytest.mark.asyncio
async def test_capability_48_abstention_first_class_not_hidden():
    out = await abstain_reject_reasons_visible(
        symbol="BTC",
        params={
            "decision_truth_state": "ABSTAINED",
            "decision_action": "NO_DECISION",
            "abstention_reason": "conflicting signals",
        },
    )
    assert out["launch_item_id"] == 48
    assert out["first_class_abstain"] is True
    assert out["hidden_as_error"] is False
    assert out["abstention_reject_disclosure"]["first_class_state"] is True
    assert out["abstention_reject_disclosure"]["hidden_as_error"] is False
    level1 = out["adaptive_disclosure"]["level_1"]
    assert level1["launch_item_id"] == 48
    assert level1["uncertainty"] == "insufficient_evidence"


@pytest.mark.asyncio
async def test_capability_44_shareable_truth_preserves_evidence_and_blocks_unsupported_live():
    out = await shareable_decision_card(
        symbol="BTC",
        params={
            "decision_action": "WAIT",
            "decision_sentence": "BTC: wait",
            "source": "market_replay_v1",
            "decision_time": "2026-09-17T12:00:00.000Z",
        },
    )
    assert out["launch_item_id"] == 44
    truth = out["shareable_truth_context"]
    assert truth["decision_time"] == "2026-09-17T12:00:00.000Z"
    assert truth["user_facing_evidence_label"] == "DELAYED"
    assert truth["unsupported_live_claim_blocked"] is True
    assert out["unsupported_live_claim_blocked"] is True
    assert out["evidence_display"]["owner"] == "launch57.evidence_class_common"
    assert out["adaptive_disclosure"]["level_1"]["launch_item_id"] == 44


@pytest.mark.asyncio
async def test_capability_45_ledger_interpretation_live_only(monkeypatch):
    fake = {
        "cumulative": {"metrics_scope": "live_only", "hit_rate_percent": 68.0, "resolved_predictions": 40},
        "synthetic_demo_data": {"excluded_from_primary_metrics": True},
        "recent": [],
    }
    monkeypatch.setattr("oracle_track_record.public_track_record", lambda: fake)
    out = await shareable_accuracy_page(symbol="BTC", params={})
    assert out["launch_item_id"] == 45
    assert out["ledger_interpretation_context"]["public_scope"] == "live_primary_outcomes_only"
    assert out["live_only_primary"] is True
    assert out["adaptive_disclosure"]["level_1"]["launch_item_id"] == 45
    assert out["safety_floor_visible"] is True


@pytest.mark.asyncio
async def test_capability_46_approved_public_trust_surfaces_only(monkeypatch):
    monkeypatch.setattr(
        "governance.anonymous_visitor_governance.anonymous_visitor_status",
        lambda: {
            "anonymous_state": "anonymous",
            "private_by_default": True,
            "public_readiness": True,
            "rate_limits": True,
            "no_pii_leak": True,
            "visitor_tier_gating": True,
            "route_inventory": {},
        },
    )
    out = await guest_trust_surface(symbol="BTC", params={})
    approved = out["approved_public_trust_surfaces"]
    assert out["launch_item_id"] == 46
    assert len(approved) >= 8
    assert all(row["module"].startswith("launch57.trust_batch") for row in approved)
    assert {row["launch_item_id"] for row in approved} >= {44, 45, 46, 47, 48}
    assert out["adaptive_disclosure"]["level_1"]["launch_item_id"] == 46
