"""DTS-033 — No unsupported causality in user-facing paths."""

from __future__ import annotations

import re
from typing import Any

_UNSUPPORTED_CAUSAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bwhale\s+caused\b", re.IGNORECASE),
    re.compile(r"\bcaused\s+(?:the\s+)?price\b", re.IGNORECASE),
    re.compile(r"\bthis\s+wallet\s+moved\s+(?:the\s+)?market\b", re.IGNORECASE),
    re.compile(r"\bimpact\s*[+]?\s*\d+(?:\.\d+)?%\b", re.IGNORECASE),
    re.compile(r"\bdrove\s+(?:the\s+)?price\b", re.IGNORECASE),
    re.compile(r"\bmarket\s+moved\s+by\s+\d", re.IGNORECASE),
)

_ASSOCIATION_REPLACEMENTS = {
    "caused": "was temporally associated with",
    "drove": "coincided with",
    "impact +": "association context (not causal): ",
}


def contains_unsupported_causality(text: str) -> bool:
    return any(p.search(text) for p in _UNSUPPORTED_CAUSAL_PATTERNS)


def sanitize_causal_language(payload: dict[str, Any]) -> dict[str, Any]:
    """Rewrite or flag unsupported causal claims in product-visible text."""
    out = dict(payload)
    for key in ("narrative", "analysis", "smart_money_summary", "daily_brief_text"):
        val = out.get(key)
        if isinstance(val, str) and contains_unsupported_causality(val):
            out[key] = _to_association_language(val)
            out.setdefault("causality_guard", {})["sanitized_fields"] = list(
                set((out.get("causality_guard") or {}).get("sanitized_fields", []) + [key])
            )

    product = (out.get("product_experience") or (out.get("decision_truth") or {}).get("product_experience") or {})
    if product:
        sm = product.get("smart_money_context") or {}
        for attr in sm.get("attributions") or []:
            label = str(attr.get("label") or "")
            if contains_unsupported_causality(label):
                attr["label"] = _to_association_language(label)
                attr["causality_guard"] = "association_only"
    return out


def _to_association_language(text: str) -> str:
    cleaned = text
    for pattern in _UNSUPPORTED_CAUSAL_PATTERNS:
        cleaned = pattern.sub("[association only — causal methodology not established]", cleaned)
    for old, new in _ASSOCIATION_REPLACEMENTS.items():
        cleaned = cleaned.replace(old, new)
    return cleaned
