"""
Launch-57 Phase 1 — Data Batch 2 canonical runtime spine.

Build order: #40 CAP-0063/0500 → #41 CAP-0630 → #39 CAP-0061
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from cap646.evidence_class import ai_compliance_footer
from data_governance.freshness import attach_data_freshness
from failure.freshness import FreshnessState, classify_freshness

LAUNCH57_BATCH2_CAP_IDS: frozenset[int] = frozenset({61, 63, 500, 630})

LAUNCH_ITEM_BY_CAP: dict[int, int] = {
    63: 40,
    500: 40,
    630: 41,
    61: 39,
}

_LIVE_ELIGIBLE = frozenset(
    {
        FreshnessState.LIVE.value,
        FreshnessState.NEAR_LIVE.value,
        FreshnessState.DELAYED.value,
    }
)


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _content_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _stamp_batch2(body: dict[str, Any], *, capability_id: int, entrypoint: str) -> dict[str, Any]:
    out = dict(body)
    out.setdefault("backend_module", "launch57.data_batch2")
    out.setdefault("backend_entrypoint", entrypoint)
    out.setdefault("binding_source", "launch57_phase1_batch2")
    out["launch_item_id"] = LAUNCH_ITEM_BY_CAP.get(capability_id)
    return out


async def data_quality_provenance_layer(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #40 / CAP-0063 — internal provenance layer (distinct from user-visible normalization)."""
    from cap646.dedicated_common import provenance_hot_storage_payload

    params = dict(params or {})
    asset = str(params.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")
    core = provenance_hot_storage_payload(asset)
    prov = core.get("provenance") or {}

    user_disclosure = {
        "question": "من أين الرقم؟",
        "band": prov.get("band"),
        "posture": prov.get("posture"),
        "score": prov.get("score"),
        "components": prov.get("components"),
        "honesty": prov.get("honesty"),
        "disclaimer": prov.get("disclaimer"),
    }

    body = _stamp_batch2(
        {
            "capability_id": 63,
            "surface": "data_quality_provenance_layer",
            "symbol": asset,
            "provenance": prov,
            "data_provenance": prov,
            "hot_storage": core.get("hot_storage"),
            "user_disclosure": user_disclosure,
            "user_visible": True,
            "unknown_is_not_zero": True,
            "success": prov.get("band") not in {None, "insufficient"},
            "observed_at": _utcnow_iso(),
        },
        capability_id=63,
        entrypoint="data_quality_provenance_layer",
    )
    if not body["success"]:
        body["error"] = "insufficient_provenance_band"

    return ai_compliance_footer(attach_data_freshness(body, slo_class="T1"))


async def data_quality_normalization(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #40 / CAP-0500 — user-visible normalization with provenance (distinct from CAP-0063)."""
    from cap646.data_spine import normalization_report

    params = dict(params or {})
    asset = str(params.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")
    base = await normalization_report(symbol=asset)
    prov = base.get("provenance") or base.get("data_provenance") or {}

    body = _stamp_batch2(
        {
            **base,
            "capability_id": 500,
            "surface": "data_quality_normalization",
            "symbol": asset,
            "user_visible": True,
            "user_disclosure": {
                "question": "من أين الرقم؟",
                "schema_version": base.get("schema_version"),
                "provenance_band": prov.get("band"),
                "provenance_score": prov.get("score"),
                "source_lineage": "canonical_layer → probe_price_sources → provenance_score",
            },
            "unknown_is_not_zero": True,
            "success": bool(base.get("success")),
        },
        capability_id=500,
        entrypoint="data_quality_normalization",
    )
    return ai_compliance_footer(attach_data_freshness(body, slo_class="T1"))


async def freshness_update_assurance(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #41 / CAP-0630 — freshness assurance with explicit DELAYED/STALE labeling; no false live."""
    from cap646.data_spine import freshness_assurance_report

    params = dict(params or {})
    asset = str(params.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")
    base = await freshness_assurance_report(symbol=asset)

    age_ms = base.get("quote_age_ms")
    age_sec = float(age_ms) / 1000.0 if age_ms is not None else None
    fresh = classify_freshness(age_seconds=age_sec)
    freshness_state = fresh.state.value
    presented_as_live = freshness_state in _LIVE_ELIGIBLE

    delayed_disclosure = None
    if freshness_state == FreshnessState.DELAYED.value:
        delayed_disclosure = "DELAYED — within SLO tolerance; not presented as LIVE"
    elif freshness_state == FreshnessState.STALE.value:
        delayed_disclosure = "STALE — not presented as real-time"
    elif freshness_state == FreshnessState.UNKNOWN.value:
        delayed_disclosure = "UNKNOWN — freshness not asserted as LIVE"

    body = _stamp_batch2(
        {
            **base,
            "capability_id": 630,
            "surface": "real_time_data_freshness_update_assurance",
            "symbol": asset,
            "data_age_sec": age_sec,
            "freshness_state": freshness_state,
            "freshness_evidence": fresh.to_dict(),
            "presented_as_live": presented_as_live,
            "delayed_label": delayed_disclosure,
            "executable_fresh": presented_as_live and bool(base.get("quote_fresh")),
            "success": presented_as_live and bool(base.get("quote_fresh")),
            "policy": "stale_or_unknown_never_passes_as_live",
        },
        capability_id=630,
        entrypoint="freshness_update_assurance",
    )
    body["freshness_state"] = freshness_state
    if not presented_as_live:
        body["error"] = "freshness_not_live_eligible"

    return ai_compliance_footer(attach_data_freshness(body, slo_class="T0"))


async def point_in_time_immutable_metrics(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #39 / CAP-0061 — immutable point-in-time metrics snapshot with content hash."""
    from hot_storage import get_hot_storage_stats
    from oracle_track_record import public_track_record

    params = dict(params or {})
    asset = str(params.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")
    snapshot_at = _utcnow_iso()
    track = public_track_record()
    hot = get_hot_storage_stats()
    hot_payload = hot.__dict__ if hasattr(hot, "__dict__") else hot

    metrics_core = {
        "immutable_metrics": track,
        "hot_storage": hot_payload,
        "symbol": asset,
    }
    content_hash = _content_hash(metrics_core)
    chain = track.get("immutable_chain") or {}

    body = _stamp_batch2(
        {
            "capability_id": 61,
            "surface": "point_in_time_immutable_metrics",
            "symbol": asset,
            "snapshot_at": snapshot_at,
            "point_in_time": True,
            "immutable": bool(chain.get("valid")),
            "content_hash": content_hash,
            "immutable_metrics": track,
            "hot_storage": hot_payload,
            "chain_valid": chain.get("valid"),
            "chain_records": chain.get("total_records"),
            "metrics_scope": (track.get("cumulative") or {}).get("metrics_scope"),
            "unknown_is_not_zero": True,
            "success": chain.get("valid") is not False,
            "observed_at": snapshot_at,
        },
        capability_id=61,
        entrypoint="point_in_time_immutable_metrics",
    )
    if not body["success"]:
        body["error"] = "immutable_chain_invalid"

    return ai_compliance_footer(body)


_DISPATCH_ENTRYPOINTS: dict[int, str] = {
    63: "data_quality_provenance_layer",
    500: "data_quality_normalization",
    630: "freshness_update_assurance",
    61: "point_in_time_immutable_metrics",
}


async def execute_launch57_batch2(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in LAUNCH57_BATCH2_CAP_IDS:
        raise ValueError(f"capability {capability_id} not in Launch-57 data batch 2")
    entrypoint = _DISPATCH_ENTRYPOINTS[capability_id]
    fn = globals()[entrypoint]
    sym = str((params or {}).get("symbol") or "BTC")
    return await fn(symbol=sym, params=dict(params or {}))
