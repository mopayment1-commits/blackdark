"""DTS-054 — Timezone presentation projection for Decision Truth surfaces."""

from __future__ import annotations

from typing import Any

from governance.timezone_governance import format_user_facing_timestamp, parse_canonical_timestamp, resolve_user_timezone

_TIMESTAMP_FIELDS = (
    "detected_at",
    "source_timestamp",
    "ingestion_time",
    "decision_issue_time",
    "review_time",
    "invalidation_time",
    "outcome_time",
    "timestamp",
    "as_of",
    "resolved_at_utc",
    "next_delivery_utc",
    "next_delivery_local",
)


def project_dts_timestamps(payload: dict[str, Any], *, user_timezone: str | None, lang: str | None) -> dict[str, Any]:
    """Attach user-facing timestamp projections without mutating canonical evidence."""
    out = dict(payload)
    resolved = resolve_user_timezone(user_timezone or out.get("user_timezone"))
    tz = resolved["timezone"]
    lang = lang or out.get("lang") or "en"

    canonical_fields: dict[str, Any] = {}
    user_fields: dict[str, Any] = {}

    for field in _TIMESTAMP_FIELDS:
        if field in out and out[field] is not None:
            canonical_fields[field] = _canonical_value(out[field])
            user_fields[field] = format_user_facing_timestamp(out[field], tz, lang=lang)

    contract = ((out.get("decision_truth") or {}).get("contract") or {})
    fresh = contract.get("freshness") or {}
    if fresh.get("as_of"):
        canonical_fields["freshness.as_of"] = _canonical_value(fresh["as_of"])
        user_fields["freshness.as_of"] = format_user_facing_timestamp(fresh["as_of"], tz, lang=lang)

    lifecycle = ((out.get("decision_truth") or {}).get("evidence_lifecycle") or {})
    for key in ("calibration", "simulation", "pre_registration", "history_event"):
        block = lifecycle.get(key) or {}
        for ts_key in ("window_start", "window_end", "period_start", "period_end", "timestamp", "registered_at"):
            if block.get(ts_key):
                path = f"{key}.{ts_key}"
                canonical_fields[path] = _canonical_value(block[ts_key])
                user_fields[path] = format_user_facing_timestamp(block[ts_key], tz, lang=lang)

    product = dict(out.get("product_experience") or {})
    delivery = dict(product.get("user_local_delivery") or {})
    if delivery:
        for key in ("next_delivery_utc", "next_delivery_local", "resolved_at_utc"):
            if delivery.get(key):
                canonical_fields[f"delivery.{key}"] = _canonical_value(delivery[key])
                user_fields[f"delivery.{key}"] = format_user_facing_timestamp(delivery[key], tz, lang=lang)

    trail = dict(product.get("full_evidence_trail") or {}).get("trail") or {}
    ts_block = trail.get("timestamp") or {}
    if isinstance(ts_block, dict) and ts_block.get("value"):
        canonical_fields["trail.timestamp"] = _canonical_value(ts_block["value"])
        user_fields["trail.timestamp"] = format_user_facing_timestamp(ts_block["value"], tz, lang=lang)

    out["dts_timezone"] = {
        "canonical_authority": resolved["authority"],
        "canonical_storage": "UTC",
        "user_timezone": tz,
        "fallback_used": resolved.get("fallback_used"),
        "fallback_reason": resolved.get("fallback_reason"),
        "canonical_timestamps": canonical_fields,
        "user_facing_timestamps": user_fields,
        "naive_canonical_paths": [k for k, v in canonical_fields.items() if v is None],
        "duplicate_authority": False,
        "methodology_version": "dts-p6-timezone-1.0",
    }
    return out


def _canonical_value(value: Any) -> str | None:
    parsed = parse_canonical_timestamp(value)
    return parsed.isoformat() if parsed else None
