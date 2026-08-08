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
    cleaned.pop("oracle_internal_verdict", None)
    out = apply_regulatory_compliance(cleaned)
    out.pop("oracle_internal_verdict", None)
    if out.get("market_regime"):
        out["weights_protected"] = True
    return out


def sanitize_explanation_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(payload)
    cleaned.pop("modal_breakdown", None)
    cleaned.pop("institutional_context", None)
    return cleaned
