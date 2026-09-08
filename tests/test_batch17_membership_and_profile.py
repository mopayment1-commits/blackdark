"""Batch17 membership and pre-build classification tests."""

from __future__ import annotations

from bd_platform.batch17_membership import BATCH17_IDS, CANONICAL_DUPLICATE_TARGETS, verify_membership
from bd_platform.batch17_prebuild_classification import verify_prebuild_classification


def test_batch17_scope_exact() -> None:
    assert len(BATCH17_IDS) == 26
    assert BATCH17_IDS[0] == 801
    assert BATCH17_IDS[-1] == 826


def test_prebuild_classification_exact_26() -> None:
    result = verify_prebuild_classification()
    assert result["ok"] is True
    assert result["count"] == 26
    assert result["unique"] == 26


def test_all_canonical_duplicate_targets_present() -> None:
    assert len(CANONICAL_DUPLICATE_TARGETS) == 26
    assert CANONICAL_DUPLICATE_TARGETS[801] == 534
    assert CANONICAL_DUPLICATE_TARGETS[813] == 546
    assert CANONICAL_DUPLICATE_TARGETS[826] == 559


def test_membership_ok() -> None:
    assert verify_membership()["ok"] is True
