"""AI/LLM financial data boundary — scrub restricted data before external models."""

from __future__ import annotations

import re
from typing import Any

from financial_data_security.classification import FORBIDDEN_STORAGE_FIELDS
from financial_data_security.scanner import find_pan_candidates, scan_text_for_restricted_data

_BLOCKED_KEY_RE = re.compile(
    r"(?i)(pan|cvv|cvc|pin|secret|token|api[_-]?key|password|refresh_token|private[_-]?key|"
    r"stripe_customer|payment_method|webhook|authorization|bearer)"
)


def scrub_for_llm(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            if str(k).lower() in FORBIDDEN_STORAGE_FIELDS or _BLOCKED_KEY_RE.search(str(k)):
                continue
            out[k] = scrub_for_llm(v)
        return out
    if isinstance(value, list):
        return [scrub_for_llm(v) for v in value]
    if isinstance(value, str):
        if scan_text_for_restricted_data(value)["blocked"]:
            return "[redacted_financial]"
        if "@" in value and len(value) < 120:
            return "[redacted_email]"
        return value
    return value


def prepare_llm_context(context: dict[str, Any]) -> dict[str, Any]:
    return scrub_for_llm(dict(context))


def ai_boundary_status() -> dict[str, Any]:
    sample = prepare_llm_context(
        {
            "email": "user@example.com",
            "stripe_customer_id": "cus_123",
            "cvv": "123",
            "pan": "redacted_sample",
            "oracle": {"verdict": "WAIT"},
        }
    )
    return {
        "scrub_enabled": True,
        "sample_output_keys": sorted(sample.keys()),
        "restricted_removed": "cvv" not in sample and "pan" not in sample and "stripe_customer_id" not in sample,
    }
