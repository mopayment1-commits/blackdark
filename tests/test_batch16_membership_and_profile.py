"""Batch16 membership and pre-build classification tests."""

from __future__ import annotations

from bd_platform.batch16_membership import BATCH16_IDS, CANONICAL_DUPLICATE_TARGETS, verify_membership
from bd_platform.batch16_prebuild_classification import verify_prebuild_classification


def test_batch16_scope_exact() -> None:
    assert len(BATCH16_IDS) == 50
    assert BATCH16_IDS[0] == 751
    assert BATCH16_IDS[-1] == 800


def test_prebuild_classification_exact_50() -> None:
    result = verify_prebuild_classification()
    assert result["ok"] is True
    assert result["count"] == 50
    assert result["unique"] == 50


def test_all_canonical_duplicate_targets_present() -> None:
    assert len(CANONICAL_DUPLICATE_TARGETS) == 50
    assert CANONICAL_DUPLICATE_TARGETS[751] == 484
    assert CANONICAL_DUPLICATE_TARGETS[775] == 508
    assert CANONICAL_DUPLICATE_TARGETS[800] == 533


def test_membership_ok() -> None:
    assert verify_membership()["ok"] is True
