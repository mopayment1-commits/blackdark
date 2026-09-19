"""B5 temporal batch — Launch #4 public accuracy ledger (SPEC §14)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from launch57.public_accuracy_common import (
    enrich_ledger_records,
    enrich_public_track_record,
    sort_canonical_ledger_order,
)
from launch57.trust_batch1 import public_accuracy_ledger

FIXED_DECISION = "2026-09-17T10:00:00.000Z"
FIXED_OUTCOME = "2026-09-18T10:00:00.000Z"
FIXED_DECISION_B = "2026-09-17T11:00:00.000Z"


def _chain_records():
    return [
        {
            "seq": 2,
            "timestamp": FIXED_OUTCOME,
            "event": "prediction_resolved",
            "prediction_id": 1,
            "asset": "BTC",
            "source": "oracle",
            "resolved": True,
            "label": "correct",
        },
        {
            "seq": 1,
            "timestamp": FIXED_DECISION,
            "event": "prediction_created",
            "prediction_id": 1,
            "asset": "BTC",
            "source": "oracle",
            "resolved": False,
        },
        {
            "seq": 4,
            "timestamp": "2026-09-18T11:00:00.000Z",
            "event": "prediction_resolved",
            "prediction_id": 2,
            "asset": "ETH",
            "source": "synthetic",
            "resolved": True,
            "label": "correct",
        },
        {
            "seq": 3,
            "timestamp": FIXED_DECISION_B,
            "event": "prediction_created",
            "prediction_id": 2,
            "asset": "ETH",
            "source": "synthetic",
            "resolved": False,
        },
    ]


def test_trust_batch1_public_accuracy_uses_b5_bridge_import():
    root = Path(__file__).resolve().parents[2]
    source = (root / "launch57" / "trust_batch1.py").read_text(encoding="utf-8")
    assert "finalize_b5_ledger_surface" in source
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "cap646" in node.module:
            imports.append(node.module)
    assert imports == []


def test_enrich_ledger_preserves_decision_outcome_evaluation_window():
    rows = enrich_ledger_records(_chain_records(), display_timezone="UTC")
    live_rows = [r for r in rows if r["prediction_id"] == 1]
    assert len(live_rows) == 1
    row = live_rows[0]
    assert row["decision_time"] == FIXED_DECISION
    assert row["outcome_time"] == FIXED_OUTCOME
    assert row["evaluation_window"]["start"] == FIXED_DECISION
    assert row["evaluation_window"]["end"] == FIXED_OUTCOME
    assert row["evaluation_window"]["status"] == "closed"
    assert row["live_only_eligible"] is True
    assert row["canonical_evidence_class"] in {"SHADOW_LIVE_FORWARD", "PRODUCTION_VERIFIED"}


def test_synthetic_excluded_from_live_primary_enrichment():
    rows = enrich_ledger_records(_chain_records(), display_timezone="UTC", live_primary_only=True)
    assert {r["prediction_id"] for r in rows} == {1}
    all_rows = enrich_ledger_records(_chain_records(), display_timezone="UTC", live_primary_only=False)
    assert {r["prediction_id"] for r in all_rows} == {1, 2}
    synth = next(r for r in all_rows if r["prediction_id"] == 2)
    assert synth["live_only_eligible"] is False
    assert synth["user_facing_evidence_label"] == "SIM"


def test_canonical_ledger_order_invariant_under_display_timezone():
    records = _chain_records()
    utc_rows = enrich_ledger_records(records, display_timezone="UTC")
    cairo_rows = enrich_ledger_records(records, display_timezone="Africa/Cairo")
    utc_order = [r["prediction_id"] for r in sort_canonical_ledger_order(utc_rows)]
    cairo_order = [r["prediction_id"] for r in sort_canonical_ledger_order(cairo_rows)]
    assert utc_order == cairo_order == [1, 2]
    utc_live = next(r for r in utc_rows if r["prediction_id"] == 1)
    cairo_live = next(r for r in cairo_rows if r["prediction_id"] == 1)
    assert utc_live["decision_time"] == cairo_live["decision_time"]
    assert utc_live["canonical_order_key"] == cairo_live["canonical_order_key"]
    assert utc_live["ledger_timing"]["display_timezone"] == "UTC"
    assert cairo_live["ledger_timing"]["display_timezone"] == "Africa/Cairo"
    assert utc_live["decision_time"] == cairo_live["decision_time"]


def test_enrich_public_track_record_attaches_ledger_timing_block():
    ledger = {
        "cumulative": {"metrics_scope": "live_only"},
        "synthetic_demo_data": {"excluded_from_primary_metrics": True},
        "recent": _chain_records(),
    }
    out = enrich_public_track_record(ledger, display_timezone="UTC")
    assert out["ledger_timing"]["canonical_order_invariant"] is True
    assert out["live_only_primary"] is True
    assert len(out["recent"]) == 1
    assert out["recent"][0]["decision_time"] == FIXED_DECISION


@pytest.mark.asyncio
async def test_public_accuracy_ledger_surface_includes_b5_temporal_fields(monkeypatch):
    fake_ledger = {
        "cumulative": {"metrics_scope": "live_only", "hit_rate_percent": 70.0},
        "synthetic_demo_data": {"excluded_from_primary_metrics": True},
        "immutable_chain": {"valid": True},
        "recent": _chain_records(),
    }
    monkeypatch.setattr("oracle_track_record.public_track_record", lambda: fake_ledger)
    out = await public_accuracy_ledger(symbol="BTC", params={"display_timezone": "UTC"})
    assert out["capability_id"] == 640
    assert out["b5_public_accuracy"]["activated"] is True
    assert out["b5_isolation_leakage"] == 0
    assert out["live_only_primary"] is True
    recent = out["ledger"]["recent"]
    assert recent
    assert recent[0]["decision_time"] == FIXED_DECISION
    assert recent[0]["outcome_time"] == FIXED_OUTCOME
    assert recent[0]["evaluation_window"]["start"] == FIXED_DECISION
    assert out["ledger_evidence_state"]["visible"] is True
