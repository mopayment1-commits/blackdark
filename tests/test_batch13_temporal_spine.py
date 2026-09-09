"""Temporal spine local tests."""

from __future__ import annotations

import pytest

from evaluation_contamination_registry import contamination_registry_status, register_contamination_event
from reproducibility_manifest import build_reproducibility_manifest, verify_manifest
from temporal_leakage_firewall import TemporalLeakageError, assert_no_temporal_leakage, leakage_firewall_report


def test_leakage_firewall_blocks_lookahead() -> None:
    with pytest.raises(TemporalLeakageError):
        assert_no_temporal_leakage(event_time="2026-01-02T00:00:00Z", evaluation_cutoff="2026-01-01T00:00:00Z")


def test_reproducibility_manifest_roundtrip() -> None:
    manifest = build_reproducibility_manifest(dataset_id="ds-test", seed=42)
    assert verify_manifest(manifest) is True


def test_contamination_registry_append() -> None:
    row = register_contamination_event(
        evaluation_id="eval-test",
        dataset_id="ds-test",
        contamination_type="train_eval_overlap",
        severity="medium",
        detail="unit test event",
    )
    assert row["evaluation_id"] == "eval-test"
    status = contamination_registry_status()
    assert status["status"] == "ACTIVE_LOCAL"


def test_leakage_report_active() -> None:
    report = leakage_firewall_report(source="historical_seed")
    assert report["status"] == "ACTIVE_LOCAL"
