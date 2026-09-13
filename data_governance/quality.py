"""Quality gate scoring (DIG-003, DIG-021)."""

from __future__ import annotations

from typing import Any


def score_quality(payload: dict[str, Any]) -> dict[str, Any]:
    score = 70.0
    if payload.get("symbol") or payload.get("asset"):
        score += 10.0
    if payload.get("source_id") or payload.get("source"):
        score += 10.0
    if payload.get("evidence_class"):
        score += 5.0
    if payload.get("provenance_chain") or payload.get("provenance"):
        score += 5.0
    score = min(100.0, score)
    return {"score": score, "floor": 40.0, "passed": score >= 40.0}
