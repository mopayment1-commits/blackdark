"""Progressive Disclosure safety floor — never hide material decision-changing facts."""

from __future__ import annotations

from typing import Any

_SAFETY_FLOOR_KEYS = frozenset(
    {
        "disclaimer",
        "analysis_only",
        "no_execution",
        "evidence_class",
        "blocker_type",
        "classification",
        "reason",
        "uncertainty_band",
        "abstain",
    }
)


def apply_progressive_disclosure(
    payload: dict[str, Any],
    *,
    level: str = "summary",
) -> dict[str, Any]:
    """Return payload with safety-floor fields always visible."""
    if level == "full":
        return payload
    floor = {k: payload[k] for k in _SAFETY_FLOOR_KEYS if k in payload}
    detail = {k: v for k, v in payload.items() if k not in _SAFETY_FLOOR_KEYS}
    if level == "summary":
        return {**floor, "summary": {k: detail[k] for k in list(detail)[:5]}}
    return {**floor, "detail": detail, "disclosure_level": level}
