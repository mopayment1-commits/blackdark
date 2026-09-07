"""Batch10 membership and semantic profile coverage."""

from __future__ import annotations

import pytest

from bd_platform.batch10_membership import verify_membership
from bd_platform.batch10_semantic_engine import semantic_profile, shared_core_ids


def test_shared_core_ids_exact_49():
    assert shared_core_ids() == list(range(451, 458)) + list(range(459, 501))


def test_semantic_profile_sample():
    profile = semantic_profile(451)
    assert profile["capability_id"] == 451
    assert profile["semantic_rule"] == "protocol_dominance"
    assert "input_defaults" in profile


def test_membership_verification():
    report = verify_membership()
    assert report["batch10_total_ids_exact"] == 50
    assert report["shared_core_count_exact"] == 49
    assert report["shared_core_membership_unambiguous"] is True


def test_semantic_profile_invalid_id():
    with pytest.raises(KeyError):
        semantic_profile(458)
