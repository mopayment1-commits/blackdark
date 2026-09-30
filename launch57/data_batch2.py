"""
Launch-57 Phase 1 — Data Batch 2 canonical runtime spine (B2 isolated).

Build order: #40 CAP-0063/0500 → #41 CAP-0630 → #39 CAP-0061
"""

from __future__ import annotations

from typing import Any

from launch57.batch2_isolation import finalize_b2_response
from launch57.freshness_common import assess_freshness
from launch57.point_in_time_common import build_immutable_snapshot, retrieve_point_in_time
from launch57.provenance_common import (
    attach_provenance_payload,
    build_provenance_record,
    normalization_report_from_provenance,
)
from launch57.temporal_common import to_rfc3339, utc_now

LAUNCH57_BATCH2_CAP_IDS: frozenset[int] = frozenset({61, 63, 500, 630})

LAUNCH_ITEM_BY_CAP: dict[int, int] = {
    63: 40,
    500: 40,
    630: 41,
    61: 39,
}


def _stamp_batch2(body: dict[str, Any], *, capability_id: int, entrypoint: str) -> dict[str, Any]:
    out = dict(body)
    out.setdefault("backend_module", "launch57.data_batch2")
    out.setdefault("backend_entrypoint", entrypoint)
    out.setdefault("binding_source", "launch57_phase1_batch2")
    out["launch_item_id"] = LAUNCH_ITEM_BY_CAP.get(capability_id)
    out["builder_status"] = "PENDING_VERIFICATION"
    return out


async def data_quality_provenance_layer(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #40 / CAP-0063 — internal provenance layer."""
    params = dict(params or {})
    asset = str(params.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")
    try:
        record, envelope = build_provenance_record(symbol=asset, params=params)
    except ValueError as exc:
        body = _stamp_batch2(
            {
                "capability_id": 63,
                "surface": "data_quality_provenance_layer",
                "symbol": asset,
                "success": False,
                "error": str(exc),
                "user_visible": True,
                "unknown_is_not_zero": True,
            },
            capability_id=63,
            entrypoint="data_quality_provenance_layer",
        )
        return finalize_b2_response(body)

    body = _stamp_batch2(
        {
            "capability_id": 63,
            "surface": "data_quality_provenance_layer",
            "symbol": asset,
            "user_visible": True,
            "unknown_is_not_zero": True,
            "success": record.quality_state.value not in {"insufficient", "unknown"},
        },
        capability_id=63,
        entrypoint="data_quality_provenance_layer",
    )
    if not body["success"]:
        body["error"] = "insufficient_provenance_band"
    return finalize_b2_response(attach_provenance_payload(body, record, envelope))


async def data_quality_normalization(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #40 / CAP-0500 — user-visible normalization (distinct from CAP-0063)."""
    params = dict(params or {})
    asset = str(params.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")
    try:
        record, envelope = build_provenance_record(symbol=asset, params=params)
    except ValueError as exc:
        body = _stamp_batch2(
            {
                "capability_id": 500,
                "surface": "data_quality_normalization",
                "symbol": asset,
                "success": False,
                "error": str(exc),
                "user_visible": True,
                "unknown_is_not_zero": True,
            },
            capability_id=500,
            entrypoint="data_quality_normalization",
        )
        return finalize_b2_response(body)

    base = normalization_report_from_provenance(record, envelope)
    body = _stamp_batch2(
        {
            **base,
            "capability_id": 500,
            "surface": "data_quality_normalization",
            "symbol": asset,
            "user_visible": True,
            "unknown_is_not_zero": True,
            "success": bool(base.get("success")),
        },
        capability_id=500,
        entrypoint="data_quality_normalization",
    )
    return finalize_b2_response(body)


async def freshness_update_assurance(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #41 / CAP-0630 — canonical Launch-57 freshness assurance."""
    params = dict(params or {})
    asset = str(params.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")

    age_ms = params.get("quote_age_ms")
    age_sec = params.get("age_sec")
    if age_sec is None and age_ms is not None:
        age_sec = float(age_ms) / 1000.0
    if age_sec is not None:
        age_sec = float(age_sec)

    assessment = assess_freshness(
        age_sec=age_sec,
        source_time=params.get("source_time"),
        observed_at=params.get("observed_at"),
        ingested_at=params.get("ingested_at"),
        available_at=params.get("available_at"),
        availability_state=params.get("availability_state"),
        quote_fresh=params.get("quote_fresh"),
    )

    body = _stamp_batch2(
        {
            "capability_id": 630,
            "surface": "real_time_data_freshness_update_assurance",
            "symbol": asset,
            "data_age_sec": age_sec,
            **assessment.to_payload(),
            "executable_fresh": assessment.presented_as_live,
        },
        capability_id=630,
        entrypoint="freshness_update_assurance",
    )
    return finalize_b2_response(body)


async def point_in_time_immutable_metrics(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #39 / CAP-0061 — immutable point-in-time metrics snapshot."""
    params = dict(params or {})
    asset = str(params.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")
    as_of = params.get("as_of") or to_rfc3339(utc_now())

    if params.get("retrieve_only"):
        rows = retrieve_point_in_time(asset, as_of=as_of, metric_key=params.get("metric_key"))
        body = _stamp_batch2(
            {
                "capability_id": 61,
                "surface": "point_in_time_immutable_metrics",
                "symbol": asset,
                "as_of": as_of,
                "observations": rows,
                "point_in_time": True,
                "immutable": bool(rows),
                "success": bool(rows),
                "unknown_is_not_zero": True,
            },
            capability_id=61,
            entrypoint="point_in_time_immutable_metrics",
        )
        if not rows:
            body["error"] = "no_point_in_time_observations"
        return finalize_b2_response(body)

    provenance_params = params.get("provenance") or {}
    freshness_params = params.get("freshness") or {}
    metrics = dict(params.get("metrics") or {"price": params.get("price"), "symbol": asset})
    metrics = {k: v for k, v in metrics.items() if v is not None}

    prov_record = None
    prov_dict = None
    if provenance_params or params.get("source_authority") or params.get("source"):
        prov_record, _env = build_provenance_record(symbol=asset, params={**provenance_params, **params})
        prov_dict = prov_record.as_dict()

    fresh_dict = None
    if freshness_params or params.get("age_sec") is not None or params.get("quote_age_ms") is not None:
        age_ms = params.get("quote_age_ms")
        age_sec = params.get("age_sec")
        if age_sec is None and age_ms is not None:
            age_sec = float(age_ms) / 1000.0
        fresh = assess_freshness(
            age_sec=float(age_sec) if age_sec is not None else None,
            source_time=params.get("source_time"),
            observed_at=params.get("observed_at"),
            available_at=params.get("available_at"),
            availability_state=params.get("availability_state"),
        )
        fresh_dict = fresh.to_payload()

    snapshot = build_immutable_snapshot(symbol=asset, metrics=metrics, provenance=prov_dict, freshness=fresh_dict)
    body = _stamp_batch2(
        {
            "capability_id": 61,
            "surface": "point_in_time_immutable_metrics",
            **snapshot,
        },
        capability_id=61,
        entrypoint="point_in_time_immutable_metrics",
    )
    if not body["success"]:
        body["error"] = "immutable_chain_invalid"
    return finalize_b2_response(body)


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
