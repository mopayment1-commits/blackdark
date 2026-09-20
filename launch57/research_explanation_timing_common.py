"""
Launch-57 canonical research/explanation timing owner for B9 (#34, #35, #36, #51).

Zero legacy/PARKED runtime dependencies on cap646 or decision_certificate.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from launch57.temporal_common import local_render_instant, parse_rfc3339, to_rfc3339, utc_now

METHODOLOGY_VERSION = "launch57-research-explanation-timing-common-1.0"
B9_LAUNCH_NUMBERS: frozenset[int] = frozenset({34, 35, 36, 51})
DEFAULT_VALIDITY_WINDOW_SEC = 3600.0
DEFAULT_STALE_THRESHOLD_MS = 300_000.0


@dataclass(frozen=True)
class ExplanationTimingContext:
    generation_time: str
    source_snapshot_time: str | None
    validity_window: dict[str, Any]
    stale_threshold_ms: float
    source_age_ms: float | None
    presented_as_current: bool
    expired_reason: str | None
    display_timezone: str
    local_render_generation_time: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "generation_time": self.generation_time,
            "source_snapshot_time": self.source_snapshot_time,
            "validity_window": self.validity_window,
            "stale_threshold_ms": self.stale_threshold_ms,
            "source_age_ms": self.source_age_ms,
            "presented_as_current": self.presented_as_current,
            "expired_reason": self.expired_reason,
            "display_timezone": self.display_timezone,
            "local_render_generation_time": self.local_render_generation_time,
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


def _source_age_ms(explanation: dict[str, Any]) -> float | None:
    for key in ("source_age_ms", "evidence_age_ms", "data_age_ms", "age_ms"):
        raw = explanation.get(key)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value >= 0:
            return value
    return None


def _stale_threshold_ms(payload: dict[str, Any], explanation: dict[str, Any]) -> float:
    governed = dict(payload.get("governed_payload") or {})
    for source in (governed, explanation, payload):
        raw_ms = source.get("stale_threshold_ms")
        if raw_ms is not None:
            return float(raw_ms)
        raw_sec = source.get("stale_threshold_sec")
        if raw_sec is not None:
            return float(raw_sec) * 1000.0
    return DEFAULT_STALE_THRESHOLD_MS


def _validity_window_sec(payload: dict[str, Any], explanation: dict[str, Any]) -> float:
    governed = dict(payload.get("governed_payload") or {})
    for source in (governed, explanation, payload):
        raw = source.get("validity_window_sec") or source.get("research_validity_window_sec")
        if raw is not None:
            return float(raw)
        window = source.get("validity_window")
        if isinstance(window, dict) and window.get("duration_seconds") is not None:
            return float(window["duration_seconds"])
    return DEFAULT_VALIDITY_WINDOW_SEC


def build_explanation_timing_context(
    payload: dict[str, Any],
    *,
    explanation: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> ExplanationTimingContext:
    """Assemble canonical explanation timing; mark expired explanations not current."""
    row = dict(explanation or payload.get("explanation") or {})
    governed = dict(payload.get("governed_payload") or {})
    zone = str(display_timezone or payload.get("display_timezone") or governed.get("display_timezone") or "UTC")
    spine_data = dict(spine or {})

    generation_time = _parse_instant(
        _first_present(governed, "generation_time")
        or _first_present(row, "generation_time", "explanation_time", "generated_at", "timestamp")
    )
    if generation_time is None:
        generation_time = to_rfc3339(utc_now())

    source_snapshot_time = _parse_instant(
        _first_present(governed, "source_snapshot_time")
        or _first_present(row, "source_snapshot_time", "evidence_snapshot_time", "snapshot_time")
        or _first_present(spine_data.get("data_spine") or {}, "timestamp")
        or spine_data.get("timestamp")
    )

    window_sec = _validity_window_sec(payload, row)
    window_start = generation_time
    window_end = _parse_instant(
        _first_present(governed, "validity_window_end")
        or _first_present(row, "validity_window_end", "expires_at")
    )
    if window_end is None:
        window_end = to_rfc3339(parse_rfc3339(generation_time) + timedelta(seconds=window_sec))

    governed_window = governed.get("validity_window")
    if isinstance(governed_window, dict):
        window_start = _parse_instant(governed_window.get("start")) or window_start
        window_end = _parse_instant(governed_window.get("end")) or window_end

    validity_window = {
        "start": window_start,
        "end": window_end,
        "duration_seconds": max(
            0,
            int((parse_rfc3339(window_end) - parse_rfc3339(window_start)).total_seconds()),
        ),
    }

    stale_threshold = _stale_threshold_ms(payload, row)
    source_age = _source_age_ms(row)
    now = utc_now()
    expired_reason: str | None = None
    if source_age is not None and source_age > stale_threshold:
        expired_reason = "explanation_source_stale"
    elif parse_rfc3339(window_end) < now:
        expired_reason = "validity_window_expired"

    presented_as_current = expired_reason is None

    return ExplanationTimingContext(
        generation_time=generation_time,
        source_snapshot_time=source_snapshot_time,
        validity_window=validity_window,
        stale_threshold_ms=stale_threshold,
        source_age_ms=source_age,
        presented_as_current=presented_as_current,
        expired_reason=expired_reason,
        display_timezone=zone,
        local_render_generation_time=local_render_instant(parse_rfc3339(generation_time), zone),
    )


def attach_explanation_temporal_envelope(body: dict[str, Any], timing: ExplanationTimingContext) -> dict[str, Any]:
    out = dict(body)
    out["explanation_timing"] = timing.as_dict()
    out["presented_as_current"] = timing.presented_as_current
    out["display"] = {
        "timezone": timing.display_timezone,
        "local_render_generation_time": timing.local_render_generation_time,
    }
    return out
