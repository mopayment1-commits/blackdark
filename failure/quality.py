"""Failure corpus quality scoring (DIG-021)."""

from __future__ import annotations

from typing import Any


def score_failure_quality(payload: dict[str, Any]) -> dict[str, Any]:
    has_type = bool(payload.get("failure_type") or payload.get("type"))
    has_source = bool(payload.get("source") or payload.get("source_id"))
    score = 50.0 + (25.0 if has_type else 0.0) + (25.0 if has_source else 0.0)
    return {"score": score, "passed": score >= 50.0}
