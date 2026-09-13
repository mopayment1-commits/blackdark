"""Decision expiry / half-life integration (DIG-037)."""

from __future__ import annotations

from typing import Any


def compute_half_life(payload: dict[str, Any], *, default_seconds: int = 45) -> dict[str, Any]:
    seconds = int(payload.get("half_life_seconds") or default_seconds)
    return {
        "expected_half_life_seconds": seconds,
        "kill_after_seconds": seconds * 3,
        "source": "decision_truth.half_life",
    }
