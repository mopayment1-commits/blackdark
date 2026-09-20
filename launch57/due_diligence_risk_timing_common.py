"""
Launch-57 canonical due-diligence / risk timing owner for B12 (#53–#57).

Zero legacy/PARKED runtime dependencies on cap646 or decision_certificate.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from launch57.temporal_common import local_render_instant, parse_rfc3339, to_rfc3339, utc_now

METHODOLOGY_VERSION = "launch57-due-diligence-risk-timing-common-1.0"
B12_LAUNCH_NUMBERS: frozenset[int] = frozenset({53, 54, 55, 56, 57})
DEFAULT_RISK_VALIDITY_WINDOW_SEC = 86_400.0
DEFAULT_STALE_THRESHOLD_MS = 900_000.0


@dataclass(frozen=True)
class DueDiligenceRiskTimingContext:
    last_update_time: str | None
    source_snapshot_time: str | None
    source_age_ms: float | None
    risk_validity_window: dict[str, Any]
    stale_threshold_ms: float
    presented_as_current: bool
    expired_reason: str | None
    display_timezone: str
    local_render_last_update_time: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "last_update_time": self.last_update_time,
            "source_snapshot_time": self.source_snapshot_time,
            "source_age_ms": self.source_age_ms,
            "risk_validity_window": self.risk_validity_window,
            "stale_threshold_ms": self.stale_threshold_ms,
            "presented_as_current": self.presented_as_current,
            "expired_reason": self.expired_reason,
            "display_timezone": self.display_timezone,
            "local_render_last_update_time": self.local_render_last_update_time,
            "methodology_version": METHODOLOGY_VERSION,
        }


def _parse_instant(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return to_rfc3339(parse_rfc3339(str(value)))


def _first_present(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None and value != "":
            return value
    return None


def _source_age_ms(risk: dict[str, Any]) -> float | None:
    for key in ("source_age_ms", "data_age_ms", "snapshot_age_ms", "age_ms", "record_age_ms"):
        raw = risk.get(key)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value >= 0:
            return value
    return None


def _stale_threshold_ms(payload: dict[str, Any], risk: dict[str, Any]) -> float:
    governed = dict(payload.get("governed_payload") or {})
    for source in (governed, risk, payload):
        raw_ms = source.get("stale_threshold_ms")
        if raw_ms is not None:
            return float(raw_ms)
        raw_sec = source.get("stale_threshold_sec")
        if raw_sec is not None:
            return float(raw_sec) * 1000.0
    return DEFAULT_STALE_THRESHOLD_MS


def _risk_validity_window_sec(payload: dict[str, Any], risk: dict[str, Any]) -> float:
    governed = dict(payload.get("governed_payload") or {})
    for source in (governed, risk, payload):
        raw = source.get("risk_validity_window_sec") or source.get("validity_window_sec")
        if raw is not None:
            return float(raw)
        window = source.get("risk_validity_window")
        if isinstance(window, dict) and window.get("duration_seconds") is not None:
            return float(window["duration_seconds"])
    return DEFAULT_RISK_VALIDITY_WINDOW_SEC


def build_due_diligence_risk_timing_context(
    payload: dict[str, Any],
    *,
    risk: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> DueDiligenceRiskTimingContext:
    """Assemble canonical due-diligence/risk timing; mark stale/expired risk not current."""
    row = dict(risk or payload.get("risk") or {})
    governed = dict(payload.get("governed_payload") or {})
    zone = str(display_timezone or payload.get("display_timezone") or governed.get("display_timezone") or "UTC")
    spine_data = dict(spine or {})

    last_update_time = _parse_instant(
        _first_present(governed, "last_update_time")
        or _first_present(row, "last_update_time", "last_updated_at", "updated_at", "timestamp", "record_time")
    )

    source_snapshot_time = _parse_instant(
        _first_present(governed, "source_snapshot_time")
        or _first_present(row, "source_snapshot_time", "snapshot_time", "event_time", "incident_time", "occurred_at")
        or _first_present(spine_data.get("data_spine") or {}, "timestamp")
        or spine_data.get("timestamp")
    )

    window_sec = _risk_validity_window_sec(payload, row)
    window_start = last_update_time
    window_end = _parse_instant(
        _first_present(governed, "risk_validity_window_end")
        or _first_present(row, "risk_validity_window_end", "expires_at", "valid_until")
    )
    if window_end is None and last_update_time is not None:
        window_end = to_rfc3339(parse_rfc3339(last_update_time) + timedelta(seconds=window_sec))

    governed_window = governed.get("risk_validity_window")
    if isinstance(governed_window, dict):
        window_start = _parse_instant(governed_window.get("start")) or window_start
        window_end = _parse_instant(governed_window.get("end")) or window_end

    duration_seconds = 0
    if window_start is not None and window_end is not None:
        duration_seconds = max(
            0,
            int((parse_rfc3339(window_end) - parse_rfc3339(window_start)).total_seconds()),
        )

    risk_validity_window = {
        "start": window_start,
        "end": window_end,
        "duration_seconds": duration_seconds,
    }

    stale_threshold = _stale_threshold_ms(payload, row)
    source_age = _source_age_ms(row)
    now = utc_now()
    expired_reason: str | None = None
    if row.get("incident_without_timestamp_context"):
        expired_reason = "incident_without_timestamp_context"
    elif source_age is not None and source_age > stale_threshold:
        expired_reason = "risk_source_stale"
    elif last_update_time is None:
        expired_reason = "risk_timestamp_unknown"
    elif window_end is not None and parse_rfc3339(window_end) < now:
        expired_reason = "risk_validity_expired"

    presented_as_current = expired_reason is None
    local_render_last_update = (
        local_render_instant(parse_rfc3339(last_update_time), zone) if last_update_time is not None else None
    )

    return DueDiligenceRiskTimingContext(
        last_update_time=last_update_time,
        source_snapshot_time=source_snapshot_time,
        source_age_ms=source_age,
        risk_validity_window=risk_validity_window,
        stale_threshold_ms=stale_threshold,
        presented_as_current=presented_as_current,
        expired_reason=expired_reason,
        display_timezone=zone,
        local_render_last_update_time=local_render_last_update,
    )


def attach_due_diligence_risk_temporal_envelope(
    body: dict[str, Any],
    timing: DueDiligenceRiskTimingContext,
) -> dict[str, Any]:
    out = dict(body)
    out["due_diligence_risk_timing"] = timing.as_dict()
    out["presented_as_current"] = timing.presented_as_current
    out["display"] = {
        "timezone": timing.display_timezone,
        "local_render_last_update_time": timing.local_render_last_update_time,
    }
    return out


def enrich_risk_incident_rows(
    rows: list[dict[str, Any]],
    *,
    payload: dict[str, Any],
    spine: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (current_only, all_with_timing) for risk incident rows."""
    current_rows: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for row in rows:
        timing = build_due_diligence_risk_timing_context(
            payload,
            risk=row,
            spine=spine,
            display_timezone=display_timezone,
        )
        enriched = dict(row)
        enriched["risk_timing"] = timing.as_dict()
        enriched["presented_as_current"] = timing.presented_as_current
        all_rows.append(enriched)
        if timing.presented_as_current:
            current_rows.append(enriched)
    return current_rows, all_rows
