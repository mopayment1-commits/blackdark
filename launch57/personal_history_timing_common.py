"""
Launch-57 canonical personal-history timing owner for B11 (#49, #50).

Zero legacy/PARKED runtime dependencies on cap646 or decision_certificate.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from launch57.temporal_common import local_render_instant, parse_rfc3339, to_rfc3339, utc_now

METHODOLOGY_VERSION = "launch57-personal-history-timing-common-1.0"
B11_LAUNCH_NUMBERS: frozenset[int] = frozenset({49, 50})
DEFAULT_HISTORY_VALIDITY_WINDOW_SEC = 604_800.0
DEFAULT_STALE_THRESHOLD_MS = 900_000.0


@dataclass(frozen=True)
class PersonalHistoryTimingContext:
    record_time: str
    event_snapshot_time: str | None
    history_validity_window: dict[str, Any]
    stale_threshold_ms: float
    record_age_ms: float | None
    presented_as_current: bool
    expired_reason: str | None
    display_timezone: str
    local_render_record_time: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "record_time": self.record_time,
            "event_snapshot_time": self.event_snapshot_time,
            "history_validity_window": self.history_validity_window,
            "stale_threshold_ms": self.stale_threshold_ms,
            "record_age_ms": self.record_age_ms,
            "presented_as_current": self.presented_as_current,
            "expired_reason": self.expired_reason,
            "display_timezone": self.display_timezone,
            "local_render_record_time": self.local_render_record_time,
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


def _record_age_ms(history: dict[str, Any]) -> float | None:
    for key in ("record_age_ms", "history_age_ms", "event_age_ms", "age_ms"):
        raw = history.get(key)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value >= 0:
            return value
    return None


def _stale_threshold_ms(payload: dict[str, Any], history: dict[str, Any]) -> float:
    governed = dict(payload.get("governed_payload") or {})
    for source in (governed, history, payload):
        raw_ms = source.get("stale_threshold_ms")
        if raw_ms is not None:
            return float(raw_ms)
        raw_sec = source.get("stale_threshold_sec")
        if raw_sec is not None:
            return float(raw_sec) * 1000.0
    return DEFAULT_STALE_THRESHOLD_MS


def _history_validity_window_sec(payload: dict[str, Any], history: dict[str, Any]) -> float:
    governed = dict(payload.get("governed_payload") or {})
    for source in (governed, history, payload):
        raw = source.get("history_validity_window_sec") or source.get("retention_window_sec")
        if raw is not None:
            return float(raw)
        window = source.get("history_validity_window")
        if isinstance(window, dict) and window.get("duration_seconds") is not None:
            return float(window["duration_seconds"])
    return DEFAULT_HISTORY_VALIDITY_WINDOW_SEC


def build_personal_history_timing_context(
    payload: dict[str, Any],
    *,
    history: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> PersonalHistoryTimingContext:
    """Assemble canonical personal-history timing; mark expired records not current."""
    row = dict(history or payload.get("history") or {})
    governed = dict(payload.get("governed_payload") or {})
    zone = str(display_timezone or payload.get("display_timezone") or governed.get("display_timezone") or "UTC")
    spine_data = dict(spine or {})

    record_time = _parse_instant(
        _first_present(governed, "record_time")
        or _first_present(row, "record_time", "recorded_at", "timestamp", "decision_time")
    )
    if record_time is None:
        record_time = to_rfc3339(utc_now())

    event_snapshot_time = _parse_instant(
        _first_present(governed, "event_snapshot_time")
        or _first_present(row, "event_snapshot_time", "event_time", "decision_time", "occurred_at")
        or _first_present(spine_data.get("data_spine") or {}, "timestamp")
        or spine_data.get("timestamp")
    )

    window_sec = _history_validity_window_sec(payload, row)
    window_start = record_time
    window_end = _parse_instant(
        _first_present(governed, "history_validity_window_end")
        or _first_present(row, "history_validity_window_end", "expires_at", "retention_until")
    )
    if window_end is None:
        window_end = to_rfc3339(parse_rfc3339(record_time) + timedelta(seconds=window_sec))

    governed_window = governed.get("history_validity_window")
    if isinstance(governed_window, dict):
        window_start = _parse_instant(governed_window.get("start")) or window_start
        window_end = _parse_instant(governed_window.get("end")) or window_end

    history_validity_window = {
        "start": window_start,
        "end": window_end,
        "duration_seconds": max(
            0,
            int((parse_rfc3339(window_end) - parse_rfc3339(window_start)).total_seconds()),
        ),
    }

    stale_threshold = _stale_threshold_ms(payload, row)
    record_age = _record_age_ms(row)
    now = utc_now()
    expired_reason: str | None = None
    if record_age is not None and record_age > stale_threshold:
        expired_reason = "history_record_stale"
    elif parse_rfc3339(window_end) < now:
        expired_reason = "history_validity_expired"

    presented_as_current = expired_reason is None

    return PersonalHistoryTimingContext(
        record_time=record_time,
        event_snapshot_time=event_snapshot_time,
        history_validity_window=history_validity_window,
        stale_threshold_ms=stale_threshold,
        record_age_ms=record_age,
        presented_as_current=presented_as_current,
        expired_reason=expired_reason,
        display_timezone=zone,
        local_render_record_time=local_render_instant(parse_rfc3339(record_time), zone),
    )


def attach_personal_history_temporal_envelope(
    body: dict[str, Any],
    timing: PersonalHistoryTimingContext,
) -> dict[str, Any]:
    out = dict(body)
    out["personal_history_timing"] = timing.as_dict()
    out["presented_as_current"] = timing.presented_as_current
    out["display"] = {
        "timezone": timing.display_timezone,
        "local_render_record_time": timing.local_render_record_time,
    }
    return out


def enrich_history_rows(
    rows: list[dict[str, Any]],
    *,
    payload: dict[str, Any],
    spine: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (current_only, all_with_timing) for personal history rows."""
    current_rows: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for row in rows:
        timing = build_personal_history_timing_context(
            payload,
            history=row,
            spine=spine,
            display_timezone=display_timezone,
        )
        enriched = dict(row)
        enriched["history_timing"] = timing.as_dict()
        enriched["presented_as_current"] = timing.presented_as_current
        all_rows.append(enriched)
        if timing.presented_as_current:
            current_rows.append(enriched)
    return current_rows, all_rows
