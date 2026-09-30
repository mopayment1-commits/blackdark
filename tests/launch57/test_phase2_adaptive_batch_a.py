"""Launch-57 Phase 2 Adaptive Batch A — builder verification tests (#6→#5→#4→#3→#2)."""

from __future__ import annotations

import pytest

from launch57.evidence_class_common import assess_user_evidence_class
from launch57.trust_batch1 import (
    decision_certificate_export,
    net_edge_truth_score,
    public_accuracy_ledger,
    single_sentence_oracle,
    user_evidence_display,
)


def test_capability_6_evidence_display_unchanged_owner():
    out = user_evidence_display({"source": "production"})
    assert out["owner"] == "launch57.evidence_class_common"
    assert out["user_facing_label"] == "LIVE"


@pytest.mark.asyncio
async def test_capability_5_net_edge_adaptive_safety_floor():
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
    assert out["net_edge_safety_floor"]["gross_edge_not_actionable_without_cost_treatment"] is True
    assert out["adaptive_disclosure"]["level_1"]["launch_item_id"] == 5
    assert out["safety_floor_visible"] is True


@pytest.mark.asyncio
async def test_capability_4_ledger_interpretation_context(monkeypatch):
    fake_ledger = {
        "cumulative": {"metrics_scope": "live_only", "hit_rate_percent": 70.0},
        "synthetic_demo_data": {"excluded_from_primary_metrics": True},
        "immutable_chain": {"valid": True},
        "recent": [],
    }
    monkeypatch.setattr("oracle_track_record.public_track_record", lambda: fake_ledger)
    out = await public_accuracy_ledger(symbol="BTC", params={})
    assert out["ledger_interpretation_context"]["public_scope"] == "live_primary_outcomes_only"
    assert out["adaptive_disclosure"]["level_1"]["launch_item_id"] == 4
    assert out["safety_floor_visible"] is True


@pytest.mark.asyncio
async def test_capability_3_certificate_adaptive_fields_and_disclosure():
    out = await decision_certificate_export(
        symbol="ETH",
        params={
            "governed_payload": {
                "decision_time": "2026-09-17T12:00:00.000Z",
                "issued_at": "2026-09-17T12:00:01.000Z",
                "key_drivers": [{"name": "momentum", "direction": "up"}],
                "contradictions": [{"summary": "funding diverges"}],
                "limitations": [{"summary": "thin liquidity"}],
            },
            "decision_action": "WAIT",
            "decision_sentence": "ETH: wait for clarity",
        },
    )
    cert = out["certificate"]
    assert cert["key_drivers"]
    assert cert["contradictions"]
    assert cert["limitations"]
    assert out["adaptive_disclosure"]["level_1"]["launch_item_id"] == 3
    assert out["safety_floor_visible"] is True


@pytest.mark.asyncio
async def test_capability_2_oracle_level1_backing_fields():
    out = await single_sentence_oracle(
        symbol="BTC",
        params={
            "decision_action": "ABSTAIN",
            "decision_sentence": "BTC: abstain — insufficient agreement",
            "abstention_reason": "conflicting signals",
            "contradictions": [{"summary": "price up, sentiment down"}],
            "limitations": [{"summary": "stale funding feed"}],
            "deeper_evidence_link": "/ledger/BTC",
            "source": "oracle",
        },
    )
    level1 = out["adaptive_disclosure"]["level_1"]
    assert level1["launch_item_id"] == 2
    assert level1["answer_state"] == "ABSTAIN"
    assert level1["abstention_reason"] == "conflicting signals"
    assert level1["critical_contradiction"]["summary"] == "price up, sentiment down"
    assert level1["critical_limitation"]["summary"] == "stale funding feed"
    assert level1["deeper_evidence_link"] == "/ledger/BTC"
    assert out["evidence_display"]["visible"] is True
    assert assess_user_evidence_class({"source": "oracle"}).user_facing_label
