"""Batch13 membership verification."""

from __future__ import annotations

from bd_platform.batch13_membership import BATCH13_IDS, verify_membership


def test_batch13_exact_scope() -> None:
    assert BATCH13_IDS == list(range(601, 651))
    assert len(BATCH13_IDS) == 50


def test_membership_ok() -> None:
    assert verify_membership()["ok"] is True
