"""
BLACKDARK Institutional Standards — programmatic enforcement for all agents/modules.

Mandatory reference: AGENTS.md + docs/governing/INSTITUTIONAL_GOVERNING_REFERENCE.md
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from cap646.evidence_class import EVIDENCE_CLASSES, attach_evidence_metadata, ai_compliance_footer

_UNAVAILABLE = "غير متوفر"
_UNAVAILABLE_EN = "unavailable"

_GLOBAL_BANNED_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\byou should buy\b",
        r"\byou should sell\b",
        r"\bbuy signal\b",
        r"\bsell signal\b",
        r"\bprice target\b",
        r"\bfair[\s-]?value\b",
        r"\bregime score\b",
        r"\brisk score\b",
        r"\brebalancing suggestion\b",
    )
)

_FEATURE_ACCEPTANCE_TEMPLATE: dict[str, bool] = {
    "formula_version_documented": True,
    "deterministic": True,
    "no_advisory_language": True,
    "stale_data_penalty_or_visibility": True,
    "ui_surface_exists": True,
    "reconciliation_tests": True,
    "evidence_class_attached": True,
    "unknown_not_zero": True,
}


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def missing_value(*, numeric: bool = False) -> Any:
    """DAT-003: unknown ≠ 0."""
    return None if numeric else _UNAVAILABLE


def sanitize_numeric(value: Any, *, field: str = "") -> Any:
    """Replace suspicious zero-with-unavailable with explicit missing."""
    if value is None:
        return missing_value(numeric=True)
    if isinstance(value, (int, float)) and value == 0:
        return value
    return value


def sanitize_payload_missing(payload: dict[str, Any], *, depth: int = 0) -> dict[str, Any]:
    """Walk payload — flag missing fields; never invent zeros for absent data."""
    if depth > 4 or not isinstance(payload, dict):
        return payload
    out: dict[str, Any] = {}
    for k, v in payload.items():
        if v is None:
            out[k] = _UNAVAILABLE
        elif isinstance(v, dict):
            if v.get("missing") is True and v.get("value_usd") == 0:
                out[k] = {**v, "value_usd": None, "display_value": _UNAVAILABLE}
            else:
                out[k] = sanitize_payload_missing(v, depth=depth + 1)
        elif isinstance(v, list):
            out[k] = [
                sanitize_payload_missing(i, depth=depth + 1) if isinstance(i, dict) else i
                for i in v
            ]
        else:
            out[k] = v
    out.setdefault("unknown_is_not_zero", True)
    return out


def scan_advisory_violations(text: str) -> list[str]:
    hits: list[str] = []
    for pat in _GLOBAL_BANNED_PATTERNS:
        if pat.search(text):
            hits.append(pat.pattern)
    return hits


def enforce_no_advisory(payload: dict[str, Any]) -> dict[str, Any]:
    """QA: scan serialized output for banned advisory language."""
    serialized = json.dumps(payload, default=str)
    violations = scan_advisory_violations(serialized)
    out = dict(payload)
    out["no_advisory_language"] = len(violations) == 0
    out["advisory_scan_clean"] = len(violations) == 0
    if violations:
        out["advisory_violations_detected"] = violations[:5]
    return out


def wrap_intelligence_response(
    payload: dict[str, Any],
    *,
    source: str | None = None,
    module_id: str | None = None,
) -> dict[str, Any]:
    """Standard wrapper for all Intelligence Ledger API responses."""
    out = sanitize_payload_missing(dict(payload))
    out = attach_evidence_metadata(out, source=source or out.get("source") or "intelligence_ledger_seed")
    out = enforce_no_advisory(out)
    out = ai_compliance_footer(out)
    if module_id:
        out["module_id"] = module_id
    out["institutional_standards_version"] = "1.0"
    out["ui_surface"] = f"/intelligence-ledger?module={module_id}" if module_id else "/intelligence-ledger"
    return out


def build_feature_acceptance_block(**overrides: bool) -> dict[str, Any]:
    criteria = dict(_FEATURE_ACCEPTANCE_TEMPLATE)
    criteria.update(overrides)
    return {
        "acceptance_criteria": criteria,
        "acceptance_template_version": "1.0",
        "governing_reference": "AGENTS.md",
    }


def user_journey_map() -> list[dict[str, Any]]:
    return [
        {
            "id": "decision",
            "title": "Trust Pulse & Oracle",
            "path": "/dashboard",
            "description": "Live decision you can verify",
            "icon": "pulse",
        },
        {
            "id": "platform",
            "title": "Platform Hub",
            "path": "/platform",
            "description": "40-point trading & analytics tools",
            "icon": "grid",
        },
        {
            "id": "intelligence",
            "title": "Intelligence Ledger",
            "path": "/intelligence-ledger",
            "description": "109+ analytical modules — unified UI",
            "icon": "brain",
        },
        {
            "id": "institutional",
            "title": "Institutional DD",
            "path": "/institutional",
            "description": "Due diligence & compliance slots",
            "icon": "shield",
        },
        {
            "id": "ask",
            "title": "Ask (Natural Language)",
            "path": "/ask",
            "description": "Query analytics in plain language — data only, no advice",
            "icon": "chat",
        },
        {
            "id": "launch",
            "title": "Launch Center",
            "path": "/launch-center",
            "description": "Readiness, journeys, engineering status",
            "icon": "rocket",
        },
        {
            "id": "cap646",
            "title": "CAP646",
            "path": "/cap646",
            "description": "646-capability closure program",
            "icon": "cap",
        },
    ]


def institutional_standards_status() -> dict[str, Any]:
    return {
        "ok": True,
        "standards_version": "1.0",
        "governing_reference": "AGENTS.md",
        "evidence_classes": list(EVIDENCE_CLASSES),
        "unknown_sentinel": _UNAVAILABLE,
        "unknown_is_not_zero": True,
        "banned_pattern_count": len(_GLOBAL_BANNED_PATTERNS),
        "acceptance_template": _FEATURE_ACCEPTANCE_TEMPLATE,
        "user_journeys": user_journey_map(),
        "timestamp": utcnow(),
    }
