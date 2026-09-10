"""Honest AV satisfaction status — separates traceability from engineering PASS."""

from __future__ import annotations

from typing import Any


def satisfaction_status_for_av(control_id: str, *, ev: dict[str, Any], rec: dict[str, Any]) -> str | None:
    """Return PARTIAL/PASS/NEEDS_EXTERNAL for governed controls; None = use default PASS."""
    audit = ev.get("audit_findings") or {}
    a11y = ev.get("accessibility") or {}
    if control_id == "AV-08":
        temporal = ev.get("public_accuracy_temporal") or {}
        if temporal.get("TEMPORALLY_PROVABLE_PREDICTIONS", 0) == 0:
            return "PARTIAL"
        return "PASS"
    if control_id == "AV-11":
        if audit.get("PUBLIC_SURFACES_WITH_UNVERIFIED_UPSTREAM_LICENSE") or audit.get(
            "PUBLIC_PRODUCTION_SURFACES_FAILING_LICENSE_GATE"
        ):
            return "PARTIAL"
        return "PASS"
    if control_id == "AV-13":
        if audit.get("PUBLIC_SURFACES_WITHOUT_EFFECTIVE_RATE_LIMIT"):
            return "PARTIAL"
        return "PASS"
    if control_id == "AV-14":
        return "PARTIAL" if ev.get("unproven_av14_controls") else "PASS"
    if control_id == "AV-15":
        return "PARTIAL" if ev.get("unproven_stream_controls") else "PASS"
    if control_id == "AV-20":
        if a11y.get("local_buildable_remaining", 0) > 0 or a11y.get("LOCAL_ACCESSIBILITY_FAILURES"):
            return "PARTIAL"
        return "PASS"
    if control_id == "AV-25":
        return "PARTIAL" if ev.get("unproven_av25_controls") else "PASS"
    if control_id == "AV-26":
        if ev.get("unproven_stream_controls") and not ev.get("av26_http_abuse_proven"):
            return "PARTIAL"
        return "PASS"
    if control_id == "AV-30":
        if not rec.get("RECONCILIATION_SHA_SEMANTICS_VALID"):
            return "PARTIAL"
        return "PASS"
    return None
