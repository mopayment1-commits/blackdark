"""Batch15 membership and pre-build classification tests."""

from __future__ import annotations

from bd_platform.batch15_membership import BATCH15_IDS, CANONICAL_DUPLICATE_TARGETS, verify_membership
from bd_platform.batch15_prebuild_classification import verify_prebuild_classification


def test_batch15_scope_exact() -> None:
    assert len(BATCH15_IDS) == 50
    assert BATCH15_IDS[0] == 701
    assert BATCH15_IDS[-1] == 750


def test_prebuild_classification_exact_50() -> None:
    result = verify_prebuild_classification()
    assert result["ok"] is True
    assert result["count"] == 50
    assert result["unique"] == 50


def test_all_canonical_duplicate_targets_present() -> None:
    assert len(CANONICAL_DUPLICATE_TARGETS) == 50
    assert CANONICAL_DUPLICATE_TARGETS[701] == 434
    assert CANONICAL_DUPLICATE_TARGETS[725] == 458
    assert CANONICAL_DUPLICATE_TARGETS[750] == 483


def test_membership_ok() -> None:
    assert verify_membership()["ok"] is True
