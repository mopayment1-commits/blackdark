"""B4 temporal batch — Launch #2/#3 decision timing (SPEC §13)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from launch57.decision_timing_common import (
    CERTIFICATE_HASH_VERSION,
    build_decision_timing_context,
    build_launch57_decision_certificate,
    snapshot_decision_time_evidence_state,
)
from launch57.evidence_class_common import assess_user_evidence_class
from launch57.temporal_common import parse_rfc3339
from launch57.trust_batch1 import decision_certificate_export, single_sentence_oracle

FIXED_DECISION_TIME = "2026-09-17T12:00:00.000Z"
FIXED_ISSUED_AT = "2026-09-17T12:00:01.000Z"


def _governed(**extra):
    base = {
        "decision_time": FIXED_DECISION_TIME,
        "issued_at": FIXED_ISSUED_AT,
        "certificate_timestamp": FIXED_ISSUED_AT,
    }
    base.update(extra)
    return base


def test_trust_batch1_no_cap646_evidence_class_import():
    root = Path(__file__).resolve().parents[2]
    source = (root / "launch57" / "trust_batch1.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "cap646" in node.module:
            imports.append(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "cap646" in alias.name:
                    imports.append(alias.name)
    assert imports == []


def test_decision_timing_context_rejects_review_before_decision():
    with pytest.raises(ValueError, match="review_time_before_decision_time"):
        build_decision_timing_context(
            {
                "governed_payload": {
                    "decision_time": FIXED_DECISION_TIME,
                    "review_time": "2026-09-17T11:00:00.000Z",
                }
            },
            require_authoritative_decision_time=True,
        )


def test_certificate_hash_deterministic_for_canonical_input():
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
        "prediction_id": "pred-1",
    }
    cert_a = build_launch57_decision_certificate(payload, timing=timing, evidence=evidence)
    cert_b = build_launch57_decision_certificate(payload, timing=timing, evidence=evidence)
    assert cert_a["certificate_hash"] == cert_b["certificate_hash"]
    assert cert_a["certificate_hash_version"] == CERTIFICATE_HASH_VERSION


def test_tz_display_does_not_mutate_canonical_decision_time():
    timing_utc = build_decision_timing_context(
        {"governed_payload": _governed(), "display_timezone": "UTC"},
        display_timezone="UTC",
        require_authoritative_decision_time=True,
    )
    timing_cairo = build_decision_timing_context(
        {"governed_payload": _governed(), "display_timezone": "Africa/Cairo"},
        display_timezone="Africa/Cairo",
        require_authoritative_decision_time=True,
    )
    assert timing_utc is not None and timing_cairo is not None
    assert timing_utc.decision_time == timing_cairo.decision_time
    assert timing_cairo.display_timezone == "Africa/Cairo"
    assert timing_utc.display_timezone == "UTC"
    if timing_cairo.local_render_decision_time != timing_utc.local_render_decision_time:
        assert "T12:00:00" not in timing_cairo.local_render_decision_time or "+03:00" in timing_cairo.local_render_decision_time


@pytest.mark.asyncio
async def test_oracle_includes_canonical_decision_and_issued_times():
    out = await single_sentence_oracle(
        symbol="BTC",
        params={"decision_action": "WAIT", "decision_sentence": "BTC: WAIT"},
    )
    assert out["launch_item_id"] == 2
    timing = out["decision_timing"]
    assert timing["decision_time"]
    assert timing["issued_at"]
    parse_rfc3339(timing["decision_time"])
    parse_rfc3339(timing["issued_at"])
    assert out["temporal"]["decision_time"] == timing["decision_time"]


@pytest.mark.asyncio
async def test_oracle_caller_evidence_escalation_blocked():
    out = await single_sentence_oracle(
        symbol="BTC",
        params={
            "source": "synthetic",
            "evidence_class": "PRODUCTION_VERIFIED",
            "decision_action": "ACT",
        },
    )
    state = out["decision_time_evidence_state"]
    assert state["canonical_evidence_class"] == "SIMULATED"
    assert state["user_facing_label"] == "SIM"


@pytest.mark.asyncio
async def test_certificate_fail_closed_without_decision_time():
    out = await decision_certificate_export(symbol="ETH", params={"decision_action": "WAIT"})
    assert out["success"] is False
    assert out["error"] == "decision_time_required"
    assert out.get("certificate_hash") is None


@pytest.mark.asyncio
async def test_certificate_rejects_caller_only_decision_time():
    """UNTRUSTED_DECISION_TIME_ASSERTION remediation — no governed_payload."""
    out = await decision_certificate_export(
        symbol="ETH",
        params={
            "decision_time": "2020-01-01T00:00:00.000Z",
            "decision_action": "WAIT",
            "decision_sentence": "ETH: backdated caller attempt",
        },
    )
    assert out["success"] is False
    assert out["error"] == "decision_time_required"
    assert out.get("certificate_hash") is None
    assert out.get("certificate") is None


@pytest.mark.asyncio
async def test_certificate_includes_timestamp_and_hash_with_governed_time():
    out = await decision_certificate_export(
        symbol="ETH",
        params={
            "governed_payload": _governed(),
            "decision_action": "WAIT",
            "decision_sentence": "ETH: wait",
            "source": "synthetic",
        },
    )
    assert out["success"] is True
    cert = out["certificate"]
    assert cert["certificate_timestamp"] == FIXED_ISSUED_AT
    assert cert["decision_time"] == FIXED_DECISION_TIME
    assert out["certificate_hash"]
    assert out["decision_timing"]["certificate_timestamp"] == FIXED_ISSUED_AT


@pytest.mark.asyncio
async def test_certificate_invalidation_append_only_fields():
    out = await decision_certificate_export(
        symbol="ETH",
        params={
            "governed_payload": _governed(
                invalidation={
                    "invalidation_time": "2026-09-17T13:00:00.000Z",
                    "invalidation_event": "stale_evidence",
                }
            ),
            "decision_action": "WAIT",
            "decision_sentence": "ETH: wait",
        },
    )
    cert = out["certificate"]
    assert cert["decision_time"] == FIXED_DECISION_TIME
    assert cert["invalidation_time"] == "2026-09-17T13:00:00.000Z"
    assert cert["invalidation_event"] == "stale_evidence"


def test_assess_user_evidence_synthetic_caller_production_verified():
    out = assess_user_evidence_class({"source": "synthetic", "evidence_class": "PRODUCTION_VERIFIED"})
    assert out.canonical_evidence_class == "SIMULATED"
    assert out.user_facing_label == "SIM"
