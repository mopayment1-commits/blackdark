"""
Launch-57 canonical shareable/public timing owner for B10 (#44, #45, #46).

Zero legacy/PARKED runtime dependencies on cap646 or decision_certificate.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from launch57.temporal_common import local_render_instant, parse_rfc3339, to_rfc3339, utc_now

METHODOLOGY_VERSION = "launch57-shareable-public-timing-common-1.0"
B10_LAUNCH_NUMBERS: frozenset[int] = frozenset({44, 45, 46})
DEFAULT_PUBLIC_VALIDITY_WINDOW_SEC = 86_400.0
DEFAULT_STALE_THRESHOLD_MS = 600_000.0


@dataclass(frozen=True)
class ShareablePublicTimingContext:
    publication_time: str
    content_snapshot_time: str | None
    public_validity_window: dict[str, Any]
    stale_threshold_ms: float
    content_age_ms: float | None
    presented_as_current: bool
    expired_reason: str | None
    display_timezone: str
    local_render_publication_time: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "publication_time": self.publication_time,
            "content_snapshot_time": self.content_snapshot_time,
            "public_validity_window": self.public_validity_window,
            "stale_threshold_ms": self.stale_threshold_ms,
            "content_age_ms": self.content_age_ms,
            "presented_as_current": self.presented_as_current,
            "expired_reason": self.expired_reason,
            "display_timezone": self.display_timezone,
            "local_render_publication_time": self.local_render_publication_time,
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


def _content_age_ms(content: dict[str, Any]) -> float | None:
    for key in ("content_age_ms", "snapshot_age_ms", "data_age_ms", "age_ms"):
        raw = content.get(key)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value >= 0:
            return value
    return None


def _stale_threshold_ms(payload: dict[str, Any], content: dict[str, Any]) -> float:
    governed = dict(payload.get("governed_payload") or {})
    for source in (governed, content, payload):
        raw_ms = source.get("stale_threshold_ms")
        if raw_ms is not None:
            return float(raw_ms)
        raw_sec = source.get("stale_threshold_sec")
        if raw_sec is not None:
            return float(raw_sec) * 1000.0
    return DEFAULT_STALE_THRESHOLD_MS


def _public_validity_window_sec(payload: dict[str, Any], content: dict[str, Any]) -> float:
    governed = dict(payload.get("governed_payload") or {})
    for source in (governed, content, payload):
        raw = source.get("public_validity_window_sec") or source.get("share_validity_window_sec")
        if raw is not None:
            return float(raw)
        window = source.get("public_validity_window")
        if isinstance(window, dict) and window.get("duration_seconds") is not None:
            return float(window["duration_seconds"])
    return DEFAULT_PUBLIC_VALIDITY_WINDOW_SEC


def build_shareable_public_timing_context(
    payload: dict[str, Any],
    *,
    content: dict[str, Any] | None = None,
    spine: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> ShareablePublicTimingContext:
    """Assemble canonical shareable/public timing; mark expired shares not current."""
    row = dict(content or payload.get("shareable_content") or {})
    governed = dict(payload.get("governed_payload") or {})
    zone = str(display_timezone or payload.get("display_timezone") or governed.get("display_timezone") or "UTC")
    spine_data = dict(spine or {})

    publication_time = _parse_instant(
        _first_present(governed, "publication_time")
        or _first_present(row, "publication_time", "published_at", "share_time", "timestamp")
    )
    if publication_time is None:
        publication_time = to_rfc3339(utc_now())

    content_snapshot_time = _parse_instant(
        _first_present(governed, "content_snapshot_time")
        or _first_present(row, "content_snapshot_time", "snapshot_time", "issued_at", "decision_time")
        or _first_present(spine_data.get("data_spine") or {}, "timestamp")
        or spine_data.get("timestamp")
    )

    window_sec = _public_validity_window_sec(payload, row)
    window_start = publication_time
    window_end = _parse_instant(
        _first_present(governed, "public_validity_window_end")
        or _first_present(row, "public_validity_window_end", "expires_at", "share_expires_at")
    )
    if window_end is None:
        window_end = to_rfc3339(parse_rfc3339(publication_time) + timedelta(seconds=window_sec))

    governed_window = governed.get("public_validity_window")
    if isinstance(governed_window, dict):
        window_start = _parse_instant(governed_window.get("start")) or window_start
        window_end = _parse_instant(governed_window.get("end")) or window_end

    public_validity_window = {
        "start": window_start,
        "end": window_end,
        "duration_seconds": max(
            0,
            int((parse_rfc3339(window_end) - parse_rfc3339(window_start)).total_seconds()),
        ),
    }

    stale_threshold = _stale_threshold_ms(payload, row)
    content_age = _content_age_ms(row)
    now = utc_now()
    expired_reason: str | None = None
    if content_age is not None and content_age > stale_threshold:
        expired_reason = "share_content_stale"
    elif parse_rfc3339(window_end) < now:
        expired_reason = "public_validity_expired"

    presented_as_current = expired_reason is None

    return ShareablePublicTimingContext(
        publication_time=publication_time,
        content_snapshot_time=content_snapshot_time,
        public_validity_window=public_validity_window,
        stale_threshold_ms=stale_threshold,
        content_age_ms=content_age,
        presented_as_current=presented_as_current,
        expired_reason=expired_reason,
        display_timezone=zone,
        local_render_publication_time=local_render_instant(parse_rfc3339(publication_time), zone),
    )


def attach_shareable_public_temporal_envelope(
    body: dict[str, Any],
    timing: ShareablePublicTimingContext,
) -> dict[str, Any]:
    out = dict(body)
    out["shareable_public_timing"] = timing.as_dict()
    out["presented_as_current"] = timing.presented_as_current
    out["display"] = {
        "timezone": timing.display_timezone,
        "local_render_publication_time": timing.local_render_publication_time,
    }
    return out
