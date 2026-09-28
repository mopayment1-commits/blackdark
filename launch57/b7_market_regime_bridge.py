"""
B7 → #7/#11–#20/#25–#30/#37 targeted reconciliation bridge.

Binds cross-signal surfaces to launch57.market_regime_timing_common.
"""

from __future__ import annotations

from typing import Any

from launch57.batch7_isolation import finalize_b7_response
from launch57.b6_net_edge_bridge import apply_b6_trust_envelope
from launch57.market_regime_timing_common import (
    B7_LAUNCH_NUMBERS,
    CrossSignalTimingAssessment,
    SignalTemporalInput,
    assess_cross_signal_timing,
    collect_signals_from_context,
)

B7_MARKET_REGIME_TIMING_ACTIVATED: bool = True


def b7_market_regime_timing_state() -> dict[str, Any]:
    return {
        "contract": "B7_MARKET_REGIME_TIMING_RECONCILIATION",
        "activated": B7_MARKET_REGIME_TIMING_ACTIVATED,
        "affected_launch_items": sorted(B7_LAUNCH_NUMBERS),
        "status": "PENDING_VERIFICATION" if B7_MARKET_REGIME_TIMING_ACTIVATED else "PREPARED_NOT_ACTIVATED",
        "owner_module": "launch57/market_regime_timing_common.py",
        "reopen_reason": "NONE",
    }


def apply_b7_trust_envelope(body: dict[str, Any], *, display_timezone: str | None = None) -> dict[str, Any]:
    out = apply_b6_trust_envelope(body, display_timezone=display_timezone)
    out["b7_market_regime_timing"] = b7_market_regime_timing_state()
    return finalize_b7_response(out)


def finalize_b7_cross_signal_surface(
    body: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
    signals: list[SignalTemporalInput] | None = None,
    display_timezone: str | None = None,
    fail_closed_on_mismatch: bool = True,
) -> dict[str, Any]:
    """Attach SPEC §16 cross-signal timing; fail closed on temporal mismatch when enabled."""
    launch_id = int(body.get("launch_item_id") or 0)
    p = dict(payload or {})
    if launch_id not in B7_LAUNCH_NUMBERS:
        return body

    if not B7_MARKET_REGIME_TIMING_ACTIVATED:
        return apply_b7_trust_envelope(body, display_timezone=display_timezone)

    signal_inputs = list(signals or collect_signals_from_context(p, spine=spine, body=body))
    assessment = assess_cross_signal_timing(p, signal_inputs)
    out = apply_b7_trust_envelope(body, display_timezone=display_timezone)
    out["cross_signal_timing"] = assessment.as_dict()
    out["recommended_action"] = assessment.recommended_action

    if fail_closed_on_mismatch and assessment.temporal_mismatch and body.get("success") is not False:
        out["success"] = False
        out["error"] = "temporal_mismatch"
        out["temporal_mismatch"] = True
        out["confidence_reduced"] = assessment.recommended_action == "WAIT"
        out["presented_as_live"] = False

    out["b7_market_regime_timing"] = b7_market_regime_timing_state()
    return finalize_b7_response(out)


def assessment_for_payload(
    payload: dict[str, Any],
    *,
    spine: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> CrossSignalTimingAssessment:
    signals = collect_signals_from_context(payload, spine=spine, body=body)
    return assess_cross_signal_timing(payload, signals)
