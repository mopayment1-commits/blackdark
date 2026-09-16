"""Launch-57 Phase 2 Trust Batch 1 — runtime and semantic contract tests."""

from __future__ import annotations

import pytest

from launch57.trust_batch1 import (
    LAUNCH57_TRUST_BATCH1_CAP_IDS,
    attach_trust_envelope,
    decision_certificate_export,
    execute_launch57_trust_batch1,
    net_edge_truth_score,
    public_accuracy_ledger,
    single_sentence_oracle,
    user_evidence_display,
)
from net_edge_truth import FIN_004_DEMO_OPPORTUNITY


def test_user_evidence_display_maps_live_delayed_sim():
    live = user_evidence_display({"evidence_class": "PRODUCTION_VERIFIED"})
    assert live["user_facing_label"] == "LIVE"
    assert live["visible"] is True

    delayed = user_evidence_display({"source": "market_replay_v1"})
    assert delayed["user_facing_label"] == "DELAYED"

    sim = user_evidence_display({"source": "synthetic"})
    assert sim["user_facing_label"] == "SIM"


def test_attach_trust_envelope_includes_evidence_display():
    out = attach_trust_envelope({"symbol": "BTC", "success": True})
    assert out["evidence_class_visible"] is True
    assert out["evidence_display"]["launch_item_id"] == 6
    assert out["compliance_footer"]["evidence_class"]


@pytest.mark.asyncio
async def test_net_edge_rejects_missing_opportunity_no_demo():
    out = await net_edge_truth_score(symbol="BTC", params={})
    assert out["success"] is False
    assert out["error"] == "opportunity_required"
    assert out["demo_path_blocked"] is True
    assert out["cost_claim_allowed"] is False


@pytest.mark.asyncio
async def test_net_edge_rejects_demo_opportunity():
    out = await net_edge_truth_score(
        symbol="BTC",
        params={"opportunity": dict(FIN_004_DEMO_OPPORTUNITY)},
    )
    assert out["success"] is False
    assert out["error"] == "demo_opportunity_rejected"
    assert out["cost_claim_allowed"] is False


@pytest.mark.asyncio
async def test_net_edge_scores_real_opportunity():
    out = await net_edge_truth_score(
        symbol="BTC",
        params={
            "opportunity": {
                "net_profit_usdt": 5.0,
                "quote_amount": 1000.0,
                "total_slippage_bps": 2,
                "withdrawal_fee_usdt": 0.1,
                "trading_fees_usdt": 0.2,
                "quote_age_ms": 100,
                "estimated_recipients": 1,
            }
        },
    )
    assert out["success"] is True
    assert out["net_edge_before_cost_claim"] is True
    assert out["net_edge_truth_score"]["truth_score"] is not None


@pytest.mark.asyncio
async def test_public_accuracy_ledger_live_only_primary(monkeypatch):
    fake_ledger = {
        "cumulative": {"metrics_scope": "live_only", "hit_rate_percent": 70.0},
        "synthetic_demo_data": {"excluded_from_primary_metrics": True},
        "immutable_chain": {"valid": True},
    }
    monkeypatch.setattr("oracle_track_record.public_track_record", lambda: fake_ledger)
    out = await public_accuracy_ledger(symbol="BTC", params={})
    assert out["capability_id"] == 640
    assert out["live_only_primary"] is True
    assert out["metrics_scope"] == "live_only"
    assert out["synthetic_excluded_from_primary"] is True


@pytest.mark.asyncio
async def test_decision_certificate_includes_hash():
    out = await decision_certificate_export(
        symbol="ETH",
        params={"decision_action": "WAIT", "decision_sentence": "ETH: wait for clarity"},
    )
    assert out["capability_id"] == 641
    assert out["certificate_hash"]
    assert out["certificate"]["certificate_hash"] == out["certificate_hash"]


@pytest.mark.asyncio
async def test_single_sentence_oracle_act_wait_abstain():
    out = await single_sentence_oracle(
        symbol="BTC",
        params={"decision_action": "ACT", "decision_sentence": "BTC: momentum supports ACT"},
    )
    assert out["launch_item_id"] == 2
    assert out["decision_action"] == "ACT"
    assert "ACT" in out["decision_sentence"]
    assert out["evidence_display"]["visible"] is True


@pytest.mark.asyncio
async def test_execute_dispatch_caps():
    for cap_id in LAUNCH57_TRUST_BATCH1_CAP_IDS:
        out = await execute_launch57_trust_batch1(cap_id, params={"symbol": "BTC"})
        assert out["binding_source"] == "launch57_phase2_trust_batch1"
