"""B3 #6 trust-boundary regression — UNTRUSTED_EVIDENCE_CLASS_ESCALATION remediation."""

from __future__ import annotations

import pytest

from launch57.evidence_class_common import (
    assess_user_evidence_class,
    attach_evidence_class_metadata,
    infer_canonical_evidence_class,
)


def test_synthetic_explicit_production_verified_not_live():
    out = assess_user_evidence_class({"source": "synthetic", "evidence_class": "PRODUCTION_VERIFIED"})
    assert out.canonical_evidence_class == "SIMULATED"
    assert out.user_facing_label == "SIM"


def test_synthetic_canonical_explicit_production_verified_not_live():
    out = assess_user_evidence_class(
        {"source": "synthetic", "canonical_evidence_class": "PRODUCTION_VERIFIED"}
    )
    assert out.canonical_evidence_class == "SIMULATED"
    assert out.user_facing_label == "SIM"


def test_synthetic_stale_explicit_production_no_internal_contradiction():
    out = assess_user_evidence_class(
        {
            "source": "synthetic",
            "evidence_class": "PRODUCTION_VERIFIED",
            "freshness_state": "STALE",
        },
        freshness_state="STALE",
    )
    assert out.canonical_evidence_class == "SIMULATED"
    assert out.user_facing_label == "SIM"
    assert out.freshness_downgrade_applied is False


def test_replay_explicit_production_verified_not_live():
    out = assess_user_evidence_class(
        {"source": "market_replay_v1", "evidence_class": "PRODUCTION_VERIFIED"}
    )
    assert out.canonical_evidence_class == "BACKTESTED"
    assert out.user_facing_label == "DELAYED"


def test_unknown_source_explicit_production_verified_no_escalation():
    out = assess_user_evidence_class(
        {"source": "binance:api", "evidence_class": "PRODUCTION_VERIFIED"}
    )
    assert out.canonical_evidence_class == "SHADOW_LIVE_FORWARD"
    assert out.canonical_evidence_class != "PRODUCTION_VERIFIED"


def test_contradictory_explicit_sim_source_governs():
    out = assess_user_evidence_class({"source": "paper_trading", "evidence_class": "PRODUCTION_VERIFIED"})
    assert out.canonical_evidence_class == "SIMULATED"
    assert out.user_facing_label == "SIM"


def test_valid_production_source_remains_production_verified():
    out = assess_user_evidence_class({"source": "production_feed", "evidence_class": "PRODUCTION_VERIFIED"})
    assert out.canonical_evidence_class == "PRODUCTION_VERIFIED"
    assert out.user_facing_label == "LIVE"


def test_valid_production_stale_downgrades_user_label_only():
    out = assess_user_evidence_class(
        {"source": "production_feed", "evidence_class": "PRODUCTION_VERIFIED", "freshness_state": "STALE"},
        freshness_state="STALE",
    )
    assert out.canonical_evidence_class == "PRODUCTION_VERIFIED"
    assert out.user_facing_label == "DELAYED"
    assert out.freshness_downgrade_applied is True


def test_synthetic_without_override_remains_sim():
    out = assess_user_evidence_class({"source": "synthetic"})
    assert out.user_facing_label == "SIM"


def test_timezone_invariance_under_trust_gate():
    payload = {"source": "binance", "evidence_class": "PRODUCTION_VERIFIED"}
    labels = {
        assess_user_evidence_class(payload, display_timezone=tz).user_facing_label
        for tz in (None, "UTC", "Africa/Cairo", "America/New_York")
    }
    assert len(labels) == 1


def test_deterministic_under_trust_gate():
    payload = {"source": "synthetic", "evidence_class": "PRODUCTION_VERIFIED"}
    a = assess_user_evidence_class(payload)
    b = assess_user_evidence_class(payload)
    assert a.canonical_evidence_class == b.canonical_evidence_class
    assert a.user_facing_label == b.user_facing_label


def test_attach_metadata_cannot_bypass_trust_gate():
    body = attach_evidence_class_metadata(
        {"source": "synthetic", "evidence_class": "PRODUCTION_VERIFIED", "success": True}
    )
    assert body["evidence_class"] == "SIMULATED"
    assert body["evidence_display"]["user_facing_label"] == "SIM"


def test_infer_canonical_blocks_explicit_escalation():
    assert (
        infer_canonical_evidence_class(source="synthetic", explicit="PRODUCTION_VERIFIED")
        == "SIMULATED"
    )
    assert (
        infer_canonical_evidence_class(source="market_replay_v1", explicit="PRODUCTION_VERIFIED")
        == "BACKTESTED"
    )
