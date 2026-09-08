"""Batch14 membership and semantic profile tests."""

from __future__ import annotations

from bd_platform.batch14_membership import BATCH14_IDS, verify_membership
from bd_platform.batch14_prebuild_classification import verify_prebuild_classification
from bd_platform.batch14_semantic_engine import semantic_profile, shared_core_ids


def test_batch14_scope_exact() -> None:
    assert len(BATCH14_IDS) == 50
    assert BATCH14_IDS[0] == 651
    assert BATCH14_IDS[-1] == 700


def test_prebuild_classification_exact_50() -> None:
    result = verify_prebuild_classification()
    assert result["ok"] is True
    assert result["missing_ids"] == []
    assert result["extra_ids"] == []


def test_shared_core_profiles() -> None:
    for cid in shared_core_ids()[:5]:
        profile = semantic_profile(cid)
        assert profile["capability_id"] == cid
        assert profile["semantic_rule"]


def test_membership_ok() -> None:
    assert verify_membership()["ok"] is True
