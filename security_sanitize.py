"""
BLACKDARK — Response sanitization for public-facing security.
"""

from __future__ import annotations

from typing import Any


_SENSITIVE_ORACLE_KEYS = frozenset({
    "modal_breakdown",
    "dimension_weights",
    "stored_weights",
    "core_weights",
    "breakdown",
    "institutional_context",
    "ml",
    "base_score",
})


def sanitize_oracle_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip proprietary scoring internals and apply regulatory compliance."""
    from regulatory_compliance_guard import apply_regulatory_compliance

    cleaned = dict(payload)
    for key in _SENSITIVE_ORACLE_KEYS:
        cleaned.pop(key, None)
    if cleaned.get("market_regime"):
        cleaned["weights_protected"] = True
    cleaned.pop("oracle_internal_verdict", None)
    return apply_regulatory_compliance(cleaned)


def sanitize_explanation_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(payload)
    cleaned.pop("modal_breakdown", None)
    cleaned.pop("institutional_context", None)
    return cleaned
