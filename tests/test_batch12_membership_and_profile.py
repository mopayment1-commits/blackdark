"""Batch12 membership and semantic profile smoke."""

from __future__ import annotations

from bd_platform.batch12_membership import verify_membership


def test_membership_unambiguous():
    report = verify_membership()
    assert report["shared_core_membership_unambiguous"] is True
    assert report["batch12_total_ids_exact"] == 50
    assert report["shared_core_count_exact"] == 47
    assert report["outside_shared_core_count_exact"] == 3
    assert report["551_canonical_duplicate_outside_shared_core"] is True


def test_outside_shared_core_ids():
    report = verify_membership()
    assert set(report["B_outside_shared_core_ids"]) == {551, 578, 584}
