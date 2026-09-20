"""Wave 5 — decision certificate (#3) + public ledger (#4) live-surface truth."""

from __future__ import annotations

import pytest

from launch57.decision_timing_common import (
    CERTIFICATE_HASH_VERSION,
    build_decision_timing_context,
    build_launch57_decision_certificate,
    snapshot_decision_time_evidence_state,
)
from launch57.public_accuracy_common import enrich_public_track_record


def _governed():
    return {
        "decision_time": "2026-09-17T10:00:00.000Z",
        "timing": {
            "decision_time": "2026-09-17T10:00:00.000Z",
            "review_time": "2026-09-17T11:00:00.000Z",
        },
    }


def test_certificate_hash_stable_for_same_input():
    timing = build_decision_timing_context(
        {"governed_payload": _governed()},
        require_authoritative_decision_time=True,
    )
    assert timing is not None
    evidence = snapshot_decision_time_evidence_state({"source": "synthetic"})
    payload = {
        "symbol": "BTC",
        "decision_action": "WAIT",
        "decision_sentence": "BTC: WAIT",
        "prediction_id": "pred-wave5",
    }
    a = build_launch57_decision_certificate(payload, timing=timing, evidence=evidence)
    b = build_launch57_decision_certificate(payload, timing=timing, evidence=evidence)
    assert a["certificate_hash"] == b["certificate_hash"]
    assert a["certificate_hash_version"] == CERTIFICATE_HASH_VERSION


def test_decision_without_trusted_time_fails_closed():
    out = build_decision_timing_context(
        {"governed_payload": {}},
        require_authoritative_decision_time=True,
    )
    assert out is None


def test_public_ledger_marks_sim_not_live_eligible():
    enriched = enrich_public_track_record(
        {
            "recent": [
                {
                    "prediction_id": 1,
                    "event": "prediction_created",
                    "decision_time": "2026-09-17T10:00:00.000Z",
                    "evidence_class": "SIMULATED",
                    "synthetic": True,
                    "source": "demo_sim",
                }
            ]
        },
        display_timezone="UTC",
    )
    entries = enriched.get("recent_all") or []
    assert entries
    row = entries[0]
    assert row.get("live_only_eligible") is False
    assert row.get("user_facing_evidence_label") == "SIM"
    assert enriched.get("live_only_primary") is True
    assert len(enriched.get("recent") or []) == 0
