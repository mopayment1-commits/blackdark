"""
B11 → #49/#50 targeted reconciliation bridge.

Binds personal-history surfaces to launch57.personal_history_timing_common.
"""

from __future__ import annotations

from typing import Any

from launch57.batch11_isolation import finalize_b11_response
from launch57.b10_shareable_public_bridge import apply_b10_trust_envelope
from launch57.personal_history_timing_common import (
    B11_LAUNCH_NUMBERS,
    attach_personal_history_temporal_envelope,
    build_personal_history_timing_context,
    enrich_history_rows,
)

B11_PERSONAL_HISTORY_TIMING_ACTIVATED: bool = True


def b11_personal_history_timing_state() -> dict[str, Any]:
    return {
        "contract": "B11_PERSONAL_HISTORY_TIMING_RECONCILIATION",
        "activated": B11_PERSONAL_HISTORY_TIMING_ACTIVATED,
        "affected_launch_items": sorted(B11_LAUNCH_NUMBERS),
        "status": "PENDING_VERIFICATION" if B11_PERSONAL_HISTORY_TIMING_ACTIVATED else "PREPARED_NOT_ACTIVATED",
        "owner_module": "launch57/personal_history_timing_common.py",
        "reopen_reason": "NONE",
    }


def apply_b11_trust_envelope(body: dict[str, Any], *, display_timezone: str | None = None) -> dict[str, Any]:
    out = apply_b10_trust_envelope(body, display_timezone=display_timezone)
    out["b11_personal_history_timing"] = b11_personal_history_timing_state()
    return finalize_b11_response(out)


def finalize_b11_personal_history_surface(
    body: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> dict[str, Any]:
    """Attach SPEC §20 personal-history timing; fail closed on expired/stale records."""
    launch_id = int(body.get("launch_item_id") or 0)
    if launch_id not in B11_LAUNCH_NUMBERS:
        return body

    if not B11_PERSONAL_HISTORY_TIMING_ACTIVATED:
        return apply_b11_trust_envelope(body, display_timezone=display_timezone)

    p = dict(payload or {})
    zone = display_timezone or p.get("display_timezone")
    history_row = _extract_history_row(body)
    timing = build_personal_history_timing_context(
        p,
        history=history_row,
        spine=spine,
        display_timezone=zone,
    )
    out = apply_b11_trust_envelope(body, display_timezone=zone)
    out = attach_personal_history_temporal_envelope(out, timing)

    pdh = dict(out.get("personal_decision_history") or {})
    decisions = list(pdh.get("decisions") or [])
    if decisions:
        current_rows, all_rows = enrich_history_rows(decisions, payload=p, spine=spine, display_timezone=zone)
        pdh["decisions"] = current_rows
        pdh["decisions_all"] = all_rows
        pdh["expired_filtered"] = len(all_rows) - len(current_rows)
        pdh["presented_as_current_only"] = True
        out["personal_decision_history"] = pdh
        out["presented_as_current"] = bool(current_rows) or not all_rows
        if all_rows and not current_rows:
            out["success"] = False
            out["error"] = out.get("error") or timing.expired_reason or "history_expired"
            out["presented_as_current"] = False

    mirror = dict(out.get("discipline_mirror") or {})
    entries = list(mirror.get("entries") or mirror.get("missed_movements") or [])
    if entries:
        current_rows, all_rows = enrich_history_rows(entries, payload=p, spine=spine, display_timezone=zone)
        key = "entries" if mirror.get("entries") is not None else "missed_movements"
        mirror[key] = current_rows
        mirror[f"{key}_all"] = all_rows
        mirror["expired_filtered"] = len(all_rows) - len(current_rows)
        mirror["presented_as_current_only"] = True
        out["discipline_mirror"] = mirror
        out["presented_as_current"] = bool(current_rows) or not all_rows
        if all_rows and not current_rows:
            out["success"] = False
            out["error"] = out.get("error") or timing.expired_reason or "history_expired"
            out["presented_as_current"] = False

    if not timing.presented_as_current and out.get("success") is not False:
        out["success"] = False
        out["error"] = timing.expired_reason or "history_expired"
        out["presented_as_current"] = False

    out["b11_personal_history_timing"] = b11_personal_history_timing_state()
    return finalize_b11_response(out)


def _extract_history_row(body: dict[str, Any]) -> dict[str, Any]:
    for key in ("personal_decision_history", "discipline_mirror"):
        block = body.get(key)
        if isinstance(block, dict):
            return block
    return {}
