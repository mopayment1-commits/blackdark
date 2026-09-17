"""
B8 → Launch #33 targeted reconciliation bridge.

Binds smart-alerts surfaces to launch57.alert_timing_common.
"""

from __future__ import annotations

from typing import Any

from launch57.alert_timing_common import (
    B8_LAUNCH_NUMBERS,
    attach_alert_temporal_envelope,
    build_alert_timing_context,
    enrich_alert_evaluations,
)
from launch57.batch8_isolation import finalize_b8_response
from launch57.b7_market_regime_bridge import apply_b7_trust_envelope

B8_ALERT_TIMING_ACTIVATED: bool = True


def b8_alert_timing_state() -> dict[str, Any]:
    return {
        "contract": "B8_ALERT_TIMING_RECONCILIATION",
        "activated": B8_ALERT_TIMING_ACTIVATED,
        "affected_launch_items": sorted(B8_LAUNCH_NUMBERS),
        "status": "PENDING_VERIFICATION" if B8_ALERT_TIMING_ACTIVATED else "PREPARED_NOT_ACTIVATED",
        "owner_module": "launch57/alert_timing_common.py",
        "reopen_reason": "NONE",
    }


def apply_b8_trust_envelope(body: dict[str, Any], *, display_timezone: str | None = None) -> dict[str, Any]:
    out = apply_b7_trust_envelope(body, display_timezone=display_timezone)
    out["b8_alert_timing"] = b8_alert_timing_state()
    return finalize_b8_response(out)


def finalize_b8_alert_surface(
    body: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> dict[str, Any]:
    """Attach SPEC §17 alert timing to Launch #33; never present expired alerts as current."""
    launch_id = int(body.get("launch_item_id") or 0)
    if launch_id not in B8_LAUNCH_NUMBERS:
        return body

    if not B8_ALERT_TIMING_ACTIVATED:
        return apply_b8_trust_envelope(body, display_timezone=display_timezone)

    p = dict(payload or {})
    zone = display_timezone or p.get("display_timezone")
    timing = build_alert_timing_context(p, spine=spine, display_timezone=zone)
    out = apply_b8_trust_envelope(body, display_timezone=zone)
    out = attach_alert_temporal_envelope(out, timing)

    smart_alerts = dict(out.get("smart_alerts") or {})
    evaluations = dict(smart_alerts.get("evaluations") or {})
    fired = list(smart_alerts.get("fired_channels") or [])
    if evaluations:
        enriched, current_fired, all_fired = enrich_alert_evaluations(
            evaluations,
            fired,
            payload=p,
            spine=spine,
            display_timezone=zone,
        )
        smart_alerts["evaluations"] = enriched
        smart_alerts["fired_channels"] = current_fired
        smart_alerts["fired_channels_all"] = all_fired
        smart_alerts["expired_filtered"] = len(all_fired) - len(current_fired)
        smart_alerts["presented_as_current_only"] = True
        out["smart_alerts"] = smart_alerts
        out["presented_as_current"] = bool(current_fired) or not all_fired
        if all_fired and not current_fired:
            out["success"] = False
            out["error"] = out.get("error") or timing.expired_reason or "alert_expired"
            out["presented_as_current"] = False

    if not timing.presented_as_current and out.get("success") is not False:
        out["success"] = False
        out["error"] = timing.expired_reason or "alert_expired"
        out["presented_as_current"] = False

    external = dict(out.get("external_delivery") or {})
    if external.get("delivery_status") == "BLOCKED_EXTERNAL":
        out["blocked_external"] = True
        out["external_push_live"] = False

    out["b8_alert_timing"] = b8_alert_timing_state()
    return finalize_b8_response(out)
