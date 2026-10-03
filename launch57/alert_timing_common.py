"""
Launch-57 canonical alert timing owner for B8 (Launch #33).

Zero legacy/PARKED runtime dependencies on cap646 or decision_certificate.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from launch57.temporal_common import local_render_instant, parse_rfc3339, to_rfc3339, utc_now

METHODOLOGY_VERSION = "launch57-alert-timing-common-1.0"
B8_LAUNCH_NUMBERS: frozenset[int] = frozenset({33})
DEFAULT_DELIVERY_WINDOW_SEC = 600.0
DEFAULT_STALE_THRESHOLD_MS = 60_000.0


@dataclass(frozen=True)
class AlertTimingContext:
    trigger_time: str
    delivery_window: dict[str, Any]
    stale_threshold_ms: float
    trigger_age_ms: float | None
    presented_as_current: bool
    expired_reason: str | None
    display_timezone: str
    local_render_trigger_time: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "trigger_time": self.trigger_time,
            "delivery_window": self.delivery_window,
            "stale_threshold_ms": self.stale_threshold_ms,
            "trigger_age_ms": self.trigger_age_ms,
            "presented_as_current": self.presented_as_current,
            "expired_reason": self.expired_reason,
            "display_timezone": self.display_timezone,
            "local_render_trigger_time": self.local_render_trigger_time,
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


def _trigger_age_ms(alert: dict[str, Any]) -> float | None:
    for key in ("trigger_age_ms", "alert_age_ms", "age_ms"):
        raw = alert.get(key)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value >= 0:
            return value
    return None


def _stale_threshold_ms(payload: dict[str, Any], alert: dict[str, Any]) -> float:
    governed = dict(payload.get("governed_payload") or {})
    for source in (governed, alert, payload):
        raw_ms = source.get("stale_threshold_ms")
        if raw_ms is not None:
            return float(raw_ms)
        raw_sec = source.get("stale_threshold_sec")
        if raw_sec is not None:
            return float(raw_sec) * 1000.0
    return DEFAULT_STALE_THRESHOLD_MS


def _delivery_window_sec(payload: dict[str, Any], alert: dict[str, Any]) -> float:
    governed = dict(payload.get("governed_payload") or {})
    for source in (governed, alert, payload):
        raw = source.get("delivery_window_sec") or source.get("alert_delivery_window_sec")
        if raw is not None:
            return float(raw)
        window = source.get("delivery_window")
        if isinstance(window, dict) and window.get("duration_seconds") is not None:
            return float(window["duration_seconds"])
    return DEFAULT_DELIVERY_WINDOW_SEC


def build_alert_timing_context(
    payload: dict[str, Any],
    *,
    alert: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> AlertTimingContext:
    """Assemble canonical alert timing; mark expired alerts not current."""
    row = dict(alert or payload.get("alert") or {})
    governed = dict(payload.get("governed_payload") or {})
    zone = str(display_timezone or payload.get("display_timezone") or governed.get("display_timezone") or "UTC")
    spine_data = dict(spine or {})

    trigger_time = _parse_instant(
        _first_present(governed, "trigger_time")
        or _first_present(row, "trigger_time", "fired_at", "alert_time", "timestamp")
        or _first_present(spine_data.get("data_spine") or {}, "timestamp")
        or spine_data.get("timestamp")
    )
    if trigger_time is None:
        trigger_time = to_rfc3339(utc_now())

    window_sec = _delivery_window_sec(payload, row)
    window_start = trigger_time
    window_end = _parse_instant(
        _first_present(governed, "delivery_window_end")
        or _first_present(row, "delivery_window_end", "expires_at")
    )
    if window_end is None:
        window_end = to_rfc3339(parse_rfc3339(trigger_time) + timedelta(seconds=window_sec))

    governed_window = governed.get("delivery_window")
    if isinstance(governed_window, dict):
        window_start = _parse_instant(governed_window.get("start")) or window_start
        window_end = _parse_instant(governed_window.get("end")) or window_end

    delivery_window = {
        "start": window_start,
        "end": window_end,
        "duration_seconds": max(
            0,
            int((parse_rfc3339(window_end) - parse_rfc3339(window_start)).total_seconds()),
        ),
    }

    stale_threshold = _stale_threshold_ms(payload, row)
    trigger_age = _trigger_age_ms(row)
    now = utc_now()
    expired_reason: str | None = None
    if trigger_age is not None and trigger_age > stale_threshold:
        expired_reason = "alert_stale"
    elif parse_rfc3339(window_end) < now:
        expired_reason = "delivery_window_expired"

    presented_as_current = expired_reason is None

    return AlertTimingContext(
        trigger_time=trigger_time,
        delivery_window=delivery_window,
        stale_threshold_ms=stale_threshold,
        trigger_age_ms=trigger_age,
        presented_as_current=presented_as_current,
        expired_reason=expired_reason,
        display_timezone=zone,
        local_render_trigger_time=local_render_instant(parse_rfc3339(trigger_time), zone),
    )


def attach_alert_temporal_envelope(body: dict[str, Any], timing: AlertTimingContext) -> dict[str, Any]:
    out = dict(body)
    out["alert_timing"] = timing.as_dict()
    out["presented_as_current"] = timing.presented_as_current
    out["display"] = {
        "timezone": timing.display_timezone,
        "local_render_trigger_time": timing.local_render_trigger_time,
    }
    return out


def enrich_alert_evaluations(
    evaluations: dict[str, Any],
    fired_channels: list[str],
    *,
    payload: dict[str, Any],
    spine: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> tuple[dict[str, Any], list[str], list[str]]:
    """Return enriched evaluations, current fired channels, and all fired channels."""
    enriched: dict[str, Any] = {}
    current_fired: list[str] = []
    all_fired = list(fired_channels)
    for channel, evaluation in evaluations.items():
        row = dict(evaluation) if isinstance(evaluation, dict) else {"value": evaluation}
        timing = build_alert_timing_context(
            payload,
            alert=row,
            spine=spine,
            display_timezone=display_timezone,
        )
        row["alert_timing"] = timing.as_dict()
        row["presented_as_current"] = timing.presented_as_current
        enriched[channel] = row
        if channel in fired_channels and timing.presented_as_current:
            current_fired.append(channel)
    return enriched, current_fired, all_fired
