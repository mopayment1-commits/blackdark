"""
B10 → #44/#45/#46 targeted reconciliation bridge.

Binds shareable/public trust surfaces to launch57.shareable_public_timing_common.
"""

from __future__ import annotations

from typing import Any

from launch57.batch10_isolation import finalize_b10_response
from launch57.b9_research_explanation_bridge import apply_b9_trust_envelope
from launch57.financial_security_common import attach_financial_security_envelope
from launch57.shareable_public_timing_common import (
    B10_LAUNCH_NUMBERS,
    attach_shareable_public_temporal_envelope,
    build_shareable_public_timing_context,
)

B10_SHAREABLE_PUBLIC_TIMING_ACTIVATED: bool = True


def b10_shareable_public_timing_state() -> dict[str, Any]:
    return {
        "contract": "B10_SHAREABLE_PUBLIC_TIMING_RECONCILIATION",
        "activated": B10_SHAREABLE_PUBLIC_TIMING_ACTIVATED,
        "affected_launch_items": sorted(B10_LAUNCH_NUMBERS),
        "status": "PENDING_VERIFICATION" if B10_SHAREABLE_PUBLIC_TIMING_ACTIVATED else "PREPARED_NOT_ACTIVATED",
        "owner_module": "launch57/shareable_public_timing_common.py",
        "reopen_reason": "NONE",
    }


def apply_b10_trust_envelope(body: dict[str, Any], *, display_timezone: str | None = None) -> dict[str, Any]:
    out = apply_b9_trust_envelope(body, display_timezone=display_timezone)
    out["b10_shareable_public_timing"] = b10_shareable_public_timing_state()
    return finalize_b10_response(out)


def finalize_b10_shareable_surface(
    body: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> dict[str, Any]:
    """Attach SPEC §19 shareable/public timing; fail closed on expired/stale shares."""
    launch_id = int(body.get("launch_item_id") or 0)
    if launch_id not in B10_LAUNCH_NUMBERS:
        return body

    if not B10_SHAREABLE_PUBLIC_TIMING_ACTIVATED:
        return apply_b10_trust_envelope(body, display_timezone=display_timezone)

    p = dict(payload or {})
    zone = display_timezone or p.get("display_timezone")
    content_row = _extract_shareable_content(body)
    timing = build_shareable_public_timing_context(
        p,
        content=content_row,
        spine=spine,
        display_timezone=zone,
    )
    out = apply_b10_trust_envelope(body, display_timezone=zone)
    out = attach_shareable_public_temporal_envelope(out, timing)

    if not timing.presented_as_current and out.get("success") is not False:
        out["success"] = False
        out["error"] = timing.expired_reason or "share_expired"
        out["presented_as_current"] = False

    out["b10_shareable_public_timing"] = b10_shareable_public_timing_state()
    from launch57.failure_recovery_common import attach_failure_recovery_envelope

    out = attach_financial_security_envelope(
        out,
        surface_type="public",
        launch_item_id=launch_id,
    )
    out = attach_failure_recovery_envelope(
        out,
        surface_type="public",
        launch_item_id=launch_id,
    )
    from launch57.billing_entitlement_common import attach_billing_entitlement_envelope
    from launch57.identity_auth_common import attach_identity_auth_envelope

    out = attach_identity_auth_envelope(
        out,
        launch_item_id=launch_id,
        surface_type="public",
        params=p,
    )
    out = attach_billing_entitlement_envelope(out, launch_item_id=launch_id, params=p)
    return finalize_b10_response(out)


def _extract_shareable_content(body: dict[str, Any]) -> dict[str, Any]:
    for key in ("certificate", "accuracy_page", "ledger", "guest_trust", "og_metadata"):
        block = body.get(key)
        if isinstance(block, dict):
            return block
    return {}
