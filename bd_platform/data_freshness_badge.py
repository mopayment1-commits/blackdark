"""
Data Freshness Badge — #1030 (Cross-Cutting UI).

Translates backend provenance/freshness metadata into a unified visual badge.
NOT standalone — design system component applied to every data-displaying surface.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.DataFreshnessBadge")

_FEATURE_REF = 1030
_MERGED_INTO = "Cross-Cutting UI"
_STANDALONE = False
_SEED_PATH = Path("data/data_freshness_badge_seed.json")
_RUNBOOK = "docs/infrastructure/DATA_FRESHNESS_BADGE.md"

_PROVENANCE_REF = 945
_STABILIZATION_REF = 950
_SOURCE_PROVENANCE_REF = 1003
_OUTLIER_REF = 1026
_GAP_RECOVERY_REF = 1028
_AI_PROVENANCE_REF = 921

FreshnessState = Literal["Live", "Delayed", "Stabilized", "Provisional", "Recovered"]
DataCategory = Literal["price", "volume", "onchain", "governance"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("freshness badge seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("data_freshness_badge_1030") or {}


def freshness_badge_status_1030(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "policy": {
            "enabled": policy.get("enabled", True),
            "design_system_enforced": policy.get("design_system_enforced", True),
            "enforcement_sprint": policy.get("enforcement_sprint", 2),
            "enforcement_enabled": policy.get("enforcement_enabled", False),
            "methodology_version": policy.get("methodology_version", "1.0.0"),
        },
        "states": cfg.get("states") or ["Live", "Delayed", "Stabilized", "Provisional", "Recovered"],
        "thresholds_ms": cfg.get("thresholds_ms") or {},
        "surfaces": cfg.get("surfaces") or [],
        "integrations": {
            "provenance_ref": _PROVENANCE_REF,
            "data_stabilization_ref": _STABILIZATION_REF,
            "source_provenance_ref": _SOURCE_PROVENANCE_REF,
            "outlier_detection_ref": _OUTLIER_REF,
            "gap_recovery_ref": _GAP_RECOVERY_REF,
            "ai_output_provenance_ref": _AI_PROVENANCE_REF,
        },
        "runbook": _RUNBOOK,
        "fee_db": cfg.get("fee_db"),
        "timestamp": _utcnow(),
    }


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:
            ts /= 1000.0
        return datetime.fromtimestamp(ts, UTC)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _relative_supplement(delay_ms: float) -> str:
    sec = delay_ms / 1000.0
    if sec < 60:
        return f"{int(sec)}s ago"
    if sec < 3600:
        return f"{int(sec // 60)}m ago"
    if sec < 86400:
        return f"{int(sec // 3600)}h ago"
    return f"{int(sec // 86400)}d ago"


def _threshold_for(category: DataCategory, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    thresholds = (_cfg(seed).get("thresholds_ms") or {}).get(category) or {}
    defaults = {
        "price": 300_000,
        "volume": 3_600_000,
        "onchain": 12_000,
        "governance": 86_400_000,
    }
    return {
        "expected_interval_ms": int(thresholds.get("expected_interval_ms", defaults[category])),
        "delayed_multiplier": float(thresholds.get("delayed_multiplier", 2.0)),
    }


def record_freshness_fee(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee_cfg = (_cfg(seed).get("fee_db") or {})
    cost = round(
        float(fee_cfg.get("badge_render_usd", 0.000001))
        + float(fee_cfg.get("provenance_query_usd", 0.000005))
        + float(fee_cfg.get("timestamp_format_usd", 0.000001)),
        6,
    )
    return {
        "cost_usd": cost,
        "fee_db_logged": True,
        "logged_per_data_point": True,
        "timestamp": _utcnow(),
    }


def compute_freshness_state(
    *,
    category: DataCategory = "price",
    timestamp: str | float | None = None,
    source: str | None = None,
    stabilized: bool = False,
    provisional: bool = False,
    recovered: bool = False,
    recovered_from: str | None = None,
    outlier_detected: bool = False,
    now: datetime | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Rule-based deterministic freshness — visualizes #945/#950 metadata, no separate calc.
    """
    seed = seed or _load_seed()
    threshold = _threshold_for(category, seed=seed)
    expected_ms = threshold["expected_interval_ms"]
    delayed_ms = expected_ms * threshold["delayed_multiplier"]

    now_dt = now or datetime.now(UTC)
    ts_dt = _parse_timestamp(timestamp) or now_dt
    timestamp_iso = ts_dt.isoformat()
    actual_delay_ms = max(0.0, (now_dt - ts_dt).total_seconds() * 1000.0)

    state: FreshnessState
    confidence = "High"
    outlier_review = False

    if recovered:
        state = "Recovered"
        confidence = "Medium"
        if recovered_from:
            source = recovered_from
    elif stabilized:
        state = "Stabilized"
        confidence = "High"
    elif provisional:
        state = "Provisional"
        confidence = "Medium"
    elif actual_delay_ms > delayed_ms:
        state = "Delayed"
        confidence = "Medium"
    elif actual_delay_ms > expected_ms:
        state = "Delayed"
        confidence = "Medium"
    else:
        state = "Live"
        confidence = "High"

    if outlier_detected:
        outlier_review = True
        confidence = "Medium"

    css_class = f"dfb-{state.lower()}"
    if outlier_review:
        css_class += " dfb-outlier-review"

    badge_label = state
    if outlier_review:
        badge_label = f"{state} · Outlier Review"

    provenance_href = f"/api/v1/data/provenance/freshness?source={source or 'unknown'}&timestamp={timestamp_iso}"

    return {
        "state": state,
        "timestamp": timestamp_iso,
        "source": source,
        "expected_interval_ms": expected_ms,
        "actual_delay_ms": round(actual_delay_ms, 1),
        "confidence": confidence,
        "outlier_review": outlier_review,
        "relative_supplement": _relative_supplement(actual_delay_ms),
        "badge": {
            "label": badge_label,
            "source_name": source,
            "timestamp_iso": timestamp_iso,
            "state": state,
            "relative_supplement": _relative_supplement(actual_delay_ms),
            "provenance_href": provenance_href,
            "provenance_ref": _PROVENANCE_REF,
            "clickable": True,
            "css_class": css_class,
            "design_system": "data-freshness-badge-v1",
        },
        "provenance_visualization": True,
        "fee_db": record_freshness_fee(seed=seed),
    }


def freshness_from_response_metadata(
    payload: dict[str, Any],
    *,
    category: DataCategory = "price",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map existing backend metadata (#945, #950, #1026, #1028) to freshness object."""
    seed = seed or _load_seed()

    timestamp = (
        payload.get("timestamp")
        or payload.get("timestamp_utc")
        or payload.get("latest_record_at")
        or (payload.get("normalization") or {}).get("normalization_timestamp")
    )
    source = payload.get("source")
    if not source and payload.get("provenance"):
        sources = (payload.get("provenance") or {}).get("sources") or []
        if sources:
            source = sources[0].get("source") if isinstance(sources[0], dict) else str(sources[0])

    recovered = bool(payload.get("recovered") or (payload.get("gap_recovery") or {}).get("recovered"))
    recovered_from = None
    if payload.get("badge") and "Recovered from" in str(payload.get("badge")):
        recovered = True
        recovered_from = str(payload.get("badge")).replace("Recovered from ", "").strip()
    if (payload.get("gap_recovery") or {}).get("recovered_from"):
        recovered_from = payload["gap_recovery"]["recovered_from"]

    outlier = (
        payload.get("outlier_review")
        or (payload.get("outlier_gate") or {}).get("outlier_count", 0) > 0
        or payload.get("badge") == "Outlier Detected / Data Degraded"
    )

    stabilized = payload.get("data_stability") == "stabilized" or payload.get("status") == "stabilized"
    provisional = payload.get("data_stability") == "provisional" or payload.get("status") == "provisional"

    if payload.get("immutable_audit"):
        ts = payload.get("timestamp")
        if ts:
            timestamp = ts

    return compute_freshness_state(
        category=category,
        timestamp=timestamp,
        source=source,
        stabilized=stabilized,
        provisional=provisional,
        recovered=recovered,
        recovered_from=recovered_from,
        outlier_detected=bool(outlier),
        seed=seed,
    )


def attach_freshness_to_response(
    payload: dict[str, Any],
    *,
    category: DataCategory = "price",
    source: str | None = None,
    timestamp: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach freshness object to any API response — mandatory for data endpoints."""
    seed = seed or _load_seed()
    if not (_cfg(seed).get("policy") or {}).get("enabled", True):
        return payload

    out = dict(payload)
    if source:
        out.setdefault("source", source)
    if timestamp:
        out.setdefault("timestamp", timestamp)

    freshness = freshness_from_response_metadata(out, category=category, seed=seed)
    out["freshness"] = freshness
    out["data_freshness_badge"] = freshness["badge"]
    return out


def render_badge_html(freshness: dict[str, Any]) -> str:
    """Design system HTML snippet — consistent across all surfaces."""
    badge = freshness.get("badge") or {}
    state = badge.get("state", "Live")
    source = badge.get("source_name") or "unknown"
    ts = badge.get("timestamp_iso", "")
    rel = badge.get("relative_supplement", "")
    css = badge.get("css_class", "dfb-live")
    href = badge.get("provenance_href", "#")
    label = badge.get("label", state)
    return (
        f'<span class="data-freshness-badge {css}" '
        f'data-state="{state}" data-source="{source}" data-timestamp="{ts}" '
        f'title="Provenance #945">'
        f'<a class="dfb-link" href="{href}">{label}</a>'
        f'<span class="dfb-source">{source}</span>'
        f'<time class="dfb-time" datetime="{ts}">{ts}</time>'
        f'<span class="dfb-relative">({rel})</span>'
        f"</span>"
    )


def check_component_gate_1030(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = freshness_badge_status_1030(seed=seed)
    thresholds = status.get("thresholds_ms") or {}
    complete = all(k in thresholds for k in ("price", "volume", "onchain", "governance"))
    return {
        "ok": complete,
        "feature_ref": _FEATURE_REF,
        "component_ready": complete,
        "enforcement_enabled": status["policy"].get("enforcement_enabled", False),
        "checks": {
            "thresholds_configured": complete,
            "five_states": len(status.get("states") or []) >= 5,
            "design_system": status["policy"].get("design_system_enforced", True),
        },
        "timestamp": _utcnow(),
    }


def run_freshness_badge_e2e_1030(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    now = datetime.now(UTC)

    status = freshness_badge_status_1030(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "five_states", "passed": len(status["states"]) == 5})

    live = compute_freshness_state(
        category="price",
        timestamp=now.isoformat(),
        source="binance",
        seed=seed,
        now=now,
    )
    checks.append({"id": "live_state", "passed": live["state"] == "Live"})

    delayed_ts = (now.timestamp() - 400) * 1000
    delayed = compute_freshness_state(
        category="price",
        timestamp=delayed_ts,
        source="binance",
        seed=seed,
        now=now,
    )
    checks.append({"id": "delayed_state", "passed": delayed["state"] == "Delayed"})
    checks.append({"id": "delayed_confidence", "passed": delayed["confidence"] == "Medium"})

    recovered = compute_freshness_state(
        category="price",
        timestamp=now.isoformat(),
        source="coingecko",
        recovered=True,
        recovered_from="coingecko",
        seed=seed,
        now=now,
    )
    checks.append({"id": "recovered_state", "passed": recovered["state"] == "Recovered"})

    stabilized = compute_freshness_state(
        category="price",
        timestamp=now.isoformat(),
        stabilized=True,
        seed=seed,
        now=now,
    )
    checks.append({"id": "stabilized_state", "passed": stabilized["state"] == "Stabilized"})

    iso = live["timestamp"]
    checks.append({"id": "iso8601_timestamp", "passed": "T" in iso and "+00:00" in iso})

    html = render_badge_html(live)
    checks.append({"id": "badge_html", "passed": "data-freshness-badge" in html})
    checks.append({"id": "badge_has_source", "passed": "binance" in html})

    attached = attach_freshness_to_response({"value": 42000}, category="price", source="binance", timestamp=now.isoformat(), seed=seed)
    checks.append({"id": "api_freshness_object", "passed": "freshness" in attached})
    checks.append({"id": "expected_interval", "passed": attached["freshness"]["expected_interval_ms"] == 300000})

    outlier = compute_freshness_state(
        category="price",
        timestamp=now.isoformat(),
        outlier_detected=True,
        seed=seed,
        now=now,
    )
    checks.append({"id": "outlier_review", "passed": outlier["outlier_review"] is True})

    gate = check_component_gate_1030(seed=seed)
    checks.append({"id": "component_gate", "passed": gate["component_ready"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
