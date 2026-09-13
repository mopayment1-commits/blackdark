"""RESTORE-004/005 reconciliation tests."""

from __future__ import annotations

from data_governance.reconciliation import reconcile_observations


def test_reconcile_consensus():
    obs = [
        {"source_id": "a", "value": 100.0},
        {"source_id": "b", "value": 101.0},
    ]
    result = reconcile_observations(obs, max_relative_diff=0.05)
    assert result["state"] == "CONSENSUS"
    assert result["canonical_value"] is not None


def test_reconcile_conflict():
    obs = [
        {"source_id": "a", "value": 100.0},
        {"source_id": "b", "value": 200.0},
    ]
    result = reconcile_observations(obs, max_relative_diff=0.05)
    assert result["state"] == "CONFLICT"
    assert result["canonical_value"] is None


def test_reconcile_single_source_penalty():
    result = reconcile_observations([{"source_id": "only", "value": 50.0}])
    assert result["state"] == "SINGLE_SOURCE"
    assert result["confidence_penalty"] is True
