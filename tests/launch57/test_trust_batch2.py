"""Launch-57 Phase 2 Trust Batch 2 — product surface tests."""

from __future__ import annotations

import pytest

from launch57.trust_batch2 import (
    LAUNCH57_TRUST_BATCH2_ITEM_IDS,
    abstain_reject_reasons_visible,
    execute_launch57_trust_batch2,
    guest_trust_surface,
    one_click_risk_disclosure,
    shareable_accuracy_page,
    shareable_decision_card,
)


@pytest.mark.asyncio
async def test_one_click_risk_disclosure():
    out = await one_click_risk_disclosure(
        symbol="BTC",
        params={
            "decision_truth_state": "REJECTED",
            "decision_truth": {"contract": {"decision_state": "REJECTED", "net_edge": {"expected_net_edge_bps": -5}}},
        },
    )
    assert out["launch_item_id"] == 47
    assert out["risk_disclosure"]["one_click"] is True
    assert out["risk_disclosure"]["compliance_footer"]["surface"] == "one_click_risk_disclosure"


@pytest.mark.asyncio
async def test_abstain_reject_reasons_first_class():
    out = await abstain_reject_reasons_visible(
        symbol="BTC",
        params={"decision_truth_state": "ABSTAINED", "decision_action": "NO_DECISION"},
    )
    assert out["launch_item_id"] == 48
    assert out["first_class_abstain"] is True
    assert out["hidden_as_error"] is False
    assert out["no_decision"]["first_class_state"] is True


@pytest.mark.asyncio
async def test_shareable_decision_card_og_metadata():
    out = await shareable_decision_card(
        symbol="BTC",
        params={"decision_action": "WAIT", "decision_sentence": "BTC: wait"},
    )
    assert out["launch_item_id"] == 44
    assert out["og_metadata"]["title"]
    assert out["share_urls"]
    assert out["alias_of"] == "CAP-0641"


@pytest.mark.asyncio
async def test_shareable_accuracy_page_live_only(monkeypatch):
    fake = {
        "cumulative": {"metrics_scope": "live_only", "hit_rate_percent": 68.0, "resolved_predictions": 40},
        "synthetic_demo_data": {"excluded_from_primary_metrics": True},
    }
    monkeypatch.setattr("oracle_track_record.public_track_record", lambda: fake)
    out = await shareable_accuracy_page(symbol="BTC", params={})
    assert out["launch_item_id"] == 45
    assert out["live_only_primary"] is True
    assert out["alias_of"] == "CAP-0640"
    assert out["accuracy_page"]["metrics_scope"] == "live_only"


@pytest.mark.asyncio
async def test_guest_trust_surface(monkeypatch):
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
    assert out["launch_item_id"] == 46
    assert out["guest_trust"]["no_pii_leak"] is True
    assert out["guest_trust"]["visitor_tier_gating"] is True


@pytest.mark.asyncio
async def test_execute_dispatch_launch_items():
    for item_id in LAUNCH57_TRUST_BATCH2_ITEM_IDS:
        out = await execute_launch57_trust_batch2(item_id, params={"symbol": "BTC"})
        assert out["launch_item_id"] == item_id
        assert out["binding_source"] == "launch57_phase2_trust_batch2"
