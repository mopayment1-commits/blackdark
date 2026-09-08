"""Independent reference helpers for Batch15 canonical-reuse oracle tests."""

from __future__ import annotations

CANONICAL_OFFSET = 267


def expected_canonical_owner(cap_id: int) -> int:
    if cap_id == 725:
        return 458
    return cap_id - CANONICAL_OFFSET
