"""
B6 → #5/#43 targeted reconciliation bridge.

Binds net-edge and arbitrage surfaces to launch57.net_edge_timing_common.
"""

from __future__ import annotations

from typing import Any

from launch57.batch6_isolation import finalize_b6_response
from launch57.b4_decision_bridge import apply_b4_trust_envelope
from launch57.net_edge_timing_common import (
    attach_opportunity_temporal_envelope,
    build_opportunity_timing_context,
    enrich_opportunity_rows,
)

B6_NET_EDGE_TIMING_ACTIVATED: bool = True


def b6_net_edge_timing_state() -> dict[str, Any]:
    return {
        "contract": "B6_NET_EDGE_TIMING_RECONCILIATION",
        "activated": B6_NET_EDGE_TIMING_ACTIVATED,
        "affected_launch_items": [5, 43],
        "status": "PENDING_VERIFICATION" if B6_NET_EDGE_TIMING_ACTIVATED else "PREPARED_NOT_ACTIVATED",
        "owner_module": "launch57/net_edge_timing_common.py",
        "reopen_reason": "NONE",
    }


def apply_b6_trust_envelope(body: dict[str, Any], *, display_timezone: str | None = None) -> dict[str, Any]:
    out = apply_b4_trust_envelope(body, display_timezone=display_timezone)
    out["b6_net_edge_timing"] = b6_net_edge_timing_state()
    return finalize_b6_response(out)


def finalize_b6_net_edge_surface(
    body: dict[str, Any],
    *,
    payload: dict[str, Any],
    opportunity: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> dict[str, Any]:
    """Attach SPEC §15 timing to Launch #5 net-edge surface; fail closed when expired."""
    if not B6_NET_EDGE_TIMING_ACTIVATED:
        return apply_b6_trust_envelope(body, display_timezone=display_timezone)

    timing = build_opportunity_timing_context(
        payload,
        opportunity=opportunity,
        display_timezone=display_timezone,
    )
    if timing is None:
        out = apply_b6_trust_envelope(body, display_timezone=display_timezone)
        out["success"] = False
        out["error"] = out.get("error") or "opportunity_timing_required"
        out["presented_as_current"] = False
        return finalize_b6_response(out)

    if not timing.presented_as_current:
        out = apply_b6_trust_envelope(body, display_timezone=display_timezone)
        out["success"] = False
        out["error"] = timing.expired_reason or "opportunity_expired"
        out["presented_as_current"] = False
        out = attach_opportunity_temporal_envelope(out, timing)
        out["b6_net_edge_timing"] = b6_net_edge_timing_state()
        return finalize_b6_response(out)

    out = apply_b6_trust_envelope(body, display_timezone=display_timezone)
    out = attach_opportunity_temporal_envelope(out, timing)
    out["b6_net_edge_timing"] = b6_net_edge_timing_state()
    return finalize_b6_response(out)


def enrich_arbitrage_opportunities_block(
    block: dict[str, Any],
    *,
    payload: dict[str, Any],
    scan_meta: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> dict[str, Any]:
    meta = dict(scan_meta or block.get("scan_meta") or {})
    current_rows, all_rows = enrich_opportunity_rows(
        list(block.get("opportunities") or []),
        payload=payload,
        scan_timestamp=meta.get("timestamp"),
        display_timezone=display_timezone,
    )
    out = dict(block)
    out["opportunities"] = current_rows
    out["opportunities_all"] = all_rows
    out["arbitrage_timing"] = {
        "scan_timestamp": meta.get("timestamp"),
        "data_age_sec": meta.get("data_age_sec"),
        "current_count": len(current_rows),
        "total_count": len(all_rows),
        "expired_filtered": len(all_rows) - len(current_rows),
        "presented_as_current_only": True,
    }
    return out


def finalize_b6_arbitrage_surface(
    body: dict[str, Any],
    *,
    payload: dict[str, Any],
    opportunities: list[dict[str, Any]],
    scan_meta: dict[str, Any] | None = None,
    display_timezone: str | None = None,
    opportunities_key: str = "opportunities",
) -> dict[str, Any]:
    """Filter expired rows from current presentation for Launch #43 arbitrage scans."""
    if not B6_NET_EDGE_TIMING_ACTIVATED:
        return apply_b6_trust_envelope(body, display_timezone=display_timezone)

    meta = dict(scan_meta or {})
    scan_ts = meta.get("timestamp")
    current_rows, all_rows = enrich_opportunity_rows(
        opportunities,
        payload=payload,
        scan_timestamp=scan_ts,
        display_timezone=display_timezone,
    )
    out = apply_b6_trust_envelope(body, display_timezone=display_timezone)
    out[opportunities_key] = current_rows
    out[f"{opportunities_key}_all"] = all_rows
    out["arbitrage_timing"] = {
        "scan_timestamp": scan_ts,
        "data_age_sec": meta.get("data_age_sec"),
        "current_count": len(current_rows),
        "total_count": len(all_rows),
        "expired_filtered": len(all_rows) - len(current_rows),
        "presented_as_current_only": True,
    }
    out["presented_as_current"] = bool(current_rows) or not all_rows
    out["b6_net_edge_timing"] = b6_net_edge_timing_state()
    return finalize_b6_response(out)
