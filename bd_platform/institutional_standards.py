"""Institutional standards helpers — missing≠0 and intelligence response wrapping."""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import attach_evidence_metadata, ai_compliance_footer

_UNAVAILABLE = "unavailable"


def missing_value(*, numeric: bool = False) -> Any:
    """DAT-003: unknown ≠ 0."""
    return None if numeric else _UNAVAILABLE


def wrap_intelligence_response(
    payload: dict[str, Any],
    *,
    source: str | None = None,
    module_id: str | None = None,
) -> dict[str, Any]:
    out = dict(payload)
    out = attach_evidence_metadata(out, source=source or out.get("source") or "intelligence_ledger_seed")
    out = ai_compliance_footer(out)
    if module_id:
        out["module_id"] = module_id
    out["institutional_standards_version"] = "1.0"
    return out
