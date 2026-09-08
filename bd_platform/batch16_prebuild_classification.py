"""Batch16 (751–800) pre-build classification — categories A–H only."""

from __future__ import annotations

from typing import Any

from bd_platform.batch16_membership import BATCH16_IDS, CANONICAL_DUPLICATE_TARGETS

_CLASS = "E. CANONICAL_DUPLICATE_REUSE"
PREBUILD_CLASSIFICATION: dict[int, str] = {cid: _CLASS for cid in BATCH16_IDS}
PREBUILD_EVIDENCE: dict[int, dict[str, Any]] = {
    cid: {
        "canonical_capability_id": CANONICAL_DUPLICATE_TARGETS[cid],
        "evidence": f"CAP978 extension #{cid} delegates to canonical #{CANONICAL_DUPLICATE_TARGETS[cid]}",
    }
    for cid in BATCH16_IDS
}


def verify_prebuild_classification() -> dict[str, Any]:
    ids = sorted(PREBUILD_CLASSIFICATION)
    return {"ok": len(ids) == 50 and len(set(ids)) == 50, "count": len(ids), "unique": len(set(ids))}
