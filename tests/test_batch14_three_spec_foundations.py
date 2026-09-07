"""Batch14 three-spec foundation tests."""

from __future__ import annotations

from bd_platform.batch14_three_spec_foundations import batch14_foundation_status


def test_batch14_foundations_complete() -> None:
    status = batch14_foundation_status()
    assert status["pit_availability_model"]["live_promotion"] is False
    assert status["walk_forward_scaffolding"]["live_evaluation"] is False
    assert status["human_validation_loop"]["production_learning"] is False
    assert "dataset_lineage" in status
    assert "source_quality" in status
