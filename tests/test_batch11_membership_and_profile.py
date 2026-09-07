"""Batch11 membership and semantic profile smoke."""

from __future__ import annotations

from bd_platform.batch11_membership import verify_membership


def test_membership_unambiguous():
    report = verify_membership()
    assert report["shared_core_membership_unambiguous"] is True
    assert report["batch11_total_ids_exact"] == 50
    assert report["shared_core_count_exact"] == 47
    assert report["outside_shared_core_count_exact"] == 3


def test_525_hero_delegate_outside_shared_core():
    report = verify_membership()
    assert report["525_hero_delegate_outside_shared_core"] is True
