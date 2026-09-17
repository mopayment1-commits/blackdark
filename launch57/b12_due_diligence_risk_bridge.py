"""
B12 → #53–#57 targeted reconciliation bridge.

Binds due-diligence / risk surfaces to launch57.due_diligence_risk_timing_common.
"""

from __future__ import annotations

from typing import Any

from launch57.batch12_isolation import finalize_b12_response
from launch57.b11_personal_history_bridge import apply_b11_trust_envelope
from launch57.due_diligence_risk_timing_common import (
    B12_LAUNCH_NUMBERS,
    attach_due_diligence_risk_temporal_envelope,
    build_due_diligence_risk_timing_context,
    enrich_risk_incident_rows,
)

B12_DUE_DILIGENCE_RISK_TIMING_ACTIVATED: bool = True

_INCIDENT_LIST_KEYS: tuple[tuple[str, str], ...] = (
    ("pump_dump_detection", "whale_manipulation_alerts"),
    ("due_diligence", "risk_incidents"),
    ("token_due_diligence", "risk_incidents"),
)


def b12_due_diligence_risk_timing_state() -> dict[str, Any]:
    return {
        "contract": "B12_DUE_DILIGENCE_RISK_TIMING_RECONCILIATION",
        "activated": B12_DUE_DILIGENCE_RISK_TIMING_ACTIVATED,
        "affected_launch_items": sorted(B12_LAUNCH_NUMBERS),
        "status": "PENDING_VERIFICATION" if B12_DUE_DILIGENCE_RISK_TIMING_ACTIVATED else "PREPARED_NOT_ACTIVATED",
        "owner_module": "launch57/due_diligence_risk_timing_common.py",
        "reopen_reason": "NONE",
    }


def apply_b12_trust_envelope(body: dict[str, Any], *, display_timezone: str | None = None) -> dict[str, Any]:
    out = apply_b11_trust_envelope(body, display_timezone=display_timezone)
    out["b12_due_diligence_risk_timing"] = b12_due_diligence_risk_timing_state()
    return finalize_b12_response(out)


def finalize_b12_due_diligence_risk_surface(
    body: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> dict[str, Any]:
    """Attach SPEC §21 due-diligence/risk timing; fail closed on stale/expired risk."""
    launch_id = int(body.get("launch_item_id") or 0)
    if launch_id not in B12_LAUNCH_NUMBERS:
        return body

    if not B12_DUE_DILIGENCE_RISK_TIMING_ACTIVATED:
        return apply_b12_trust_envelope(body, display_timezone=display_timezone)

    p = dict(payload or {})
    zone = display_timezone or p.get("display_timezone")
    risk_row = _extract_risk_content(body)
    timing = build_due_diligence_risk_timing_context(
        p,
        risk=risk_row,
        spine=spine,
        display_timezone=zone,
    )
    out = apply_b12_trust_envelope(body, display_timezone=zone)
    out = attach_due_diligence_risk_temporal_envelope(out, timing)

    for block_key, list_key in _INCIDENT_LIST_KEYS:
        block = dict(out.get(block_key) or {})
        rows = list(block.get(list_key) or [])
        if rows:
            current_rows, all_rows = enrich_risk_incident_rows(rows, payload=p, spine=spine, display_timezone=zone)
            block[list_key] = current_rows
            block[f"{list_key}_all"] = all_rows
            block["expired_filtered"] = len(all_rows) - len(current_rows)
            block["presented_as_current_only"] = True
            out[block_key] = block
            out["presented_as_current"] = bool(current_rows) or not all_rows
            if all_rows and not current_rows:
                out["success"] = False
                out["error"] = out.get("error") or timing.expired_reason or "risk_expired"
                out["presented_as_current"] = False

    flags = list(out.get("suspicious_activity_flags") or [])
    if flags and all(isinstance(row, dict) for row in flags):
        current_rows, all_rows = enrich_risk_incident_rows(flags, payload=p, spine=spine, display_timezone=zone)
        out["suspicious_activity_flags"] = current_rows
        out["suspicious_activity_flags_all"] = all_rows
        out["expired_filtered"] = len(all_rows) - len(current_rows)
        out["presented_as_current_only"] = True
        out["presented_as_current"] = bool(current_rows) or not all_rows
        if all_rows and not current_rows:
            out["success"] = False
            out["error"] = out.get("error") or timing.expired_reason or "risk_expired"
            out["presented_as_current"] = False

    if not timing.presented_as_current and out.get("success") is not False:
        out["success"] = False
        out["error"] = timing.expired_reason or "risk_expired"
        out["presented_as_current"] = False

    out["b12_due_diligence_risk_timing"] = b12_due_diligence_risk_timing_state()
    return finalize_b12_response(out)


def _extract_risk_content(body: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "due_diligence",
        "token_due_diligence",
        "pump_dump_detection",
        "exchange_risk_indicators",
        "suspicious_activity_flags",
    ):
        block = body.get(key)
        if isinstance(block, dict):
            return block
        if key == "suspicious_activity_flags" and isinstance(block, list) and block:
            first = block[0]
            if isinstance(first, dict):
                return first
    return {}
