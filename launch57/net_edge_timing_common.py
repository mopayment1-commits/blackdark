"""
Launch-57 canonical net-edge / arbitrage timing owner for B6 (#5, #43).

Zero legacy/PARKED runtime dependencies on cap646 or decision_certificate.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from launch57.temporal_common import local_render_instant, parse_rfc3339, to_rfc3339, utc_now

METHODOLOGY_VERSION = "launch57-net-edge-timing-common-1.0"
DEFAULT_STALE_THRESHOLD_MS = 2500.0
DEFAULT_EXECUTION_WINDOW_SEC = 30.0


@dataclass(frozen=True)
class OpportunityTimingContext:
    quote_time: str
    order_book_snapshot_time: str | None
    funding_timestamp: str | None
    transfer_estimate_time: str | None
    detection_time: str
    expected_execution_window: dict[str, Any]
    stale_threshold_ms: float
    quote_age_ms: float | None
    presented_as_current: bool
    expired_reason: str | None
    display_timezone: str
    local_render_quote_time: str | None = None
    local_render_detection_time: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "quote_time": self.quote_time,
            "order_book_snapshot_time": self.order_book_snapshot_time,
            "funding_timestamp": self.funding_timestamp,
            "transfer_estimate_time": self.transfer_estimate_time,
            "detection_time": self.detection_time,
            "expected_execution_window": self.expected_execution_window,
            "stale_threshold_ms": self.stale_threshold_ms,
            "quote_age_ms": self.quote_age_ms,
            "presented_as_current": self.presented_as_current,
            "expired_reason": self.expired_reason,
            "display_timezone": self.display_timezone,
            "local_render_quote_time": self.local_render_quote_time,
            "local_render_detection_time": self.local_render_detection_time,
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


def _quote_age_ms(opportunity: dict[str, Any]) -> float | None:
    for key in ("quote_age_ms", "rewalk_age_ms", "book_age_ms", "age_ms"):
        raw = opportunity.get(key)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value >= 0:
            return value
    data_age_sec = opportunity.get("data_age_sec")
    if data_age_sec is not None:
        try:
            return float(data_age_sec) * 1000.0
        except (TypeError, ValueError):
            return None
    return None


def _stale_threshold_ms(payload: dict[str, Any], opportunity: dict[str, Any]) -> float:
    governed = dict(payload.get("governed_payload") or {})
    for source in (governed, opportunity, payload):
        raw_ms = source.get("stale_threshold_ms")
        if raw_ms is not None:
            return float(raw_ms)
        raw_sec = source.get("stale_threshold_sec")
        if raw_sec is not None:
            return float(raw_sec) * 1000.0
    return DEFAULT_STALE_THRESHOLD_MS


def _execution_window_sec(payload: dict[str, Any], opportunity: dict[str, Any]) -> float:
    governed = dict(payload.get("governed_payload") or {})
    for source in (governed, opportunity, payload):
        raw = source.get("expected_execution_window_sec") or source.get("execution_window_sec")
        if raw is not None:
            return float(raw)
        window = source.get("expected_execution_window")
        if isinstance(window, dict) and window.get("duration_seconds") is not None:
            return float(window["duration_seconds"])
    return DEFAULT_EXECUTION_WINDOW_SEC


def build_opportunity_timing_context(
    payload: dict[str, Any],
    *,
    opportunity: dict[str, Any] | None = None,
    display_timezone: str | None = None,
    scan_timestamp: str | None = None,
) -> OpportunityTimingContext | None:
    """Assemble canonical opportunity timing; mark expired opportunities not current."""
    opp = dict(opportunity or payload.get("opportunity") or {})
    governed = dict(payload.get("governed_payload") or {})
    zone = str(display_timezone or payload.get("display_timezone") or governed.get("display_timezone") or "UTC")

    quote_time = _parse_instant(
        _first_present(governed, "quote_time")
        or _first_present(opp, "quote_time", "quote_timestamp", "timestamp")
        or scan_timestamp
    )
    detection_time = _parse_instant(
        _first_present(governed, "detection_time")
        or _first_present(opp, "detection_time", "detected_at", "observed_time")
        or quote_time
    )
    if detection_time is None:
        detection_time = to_rfc3339(utc_now())
    if quote_time is None:
        quote_time = detection_time

    order_book_snapshot_time = _parse_instant(
        _first_present(governed, "order_book_snapshot_time")
        or _first_present(opp, "order_book_snapshot_time", "book_snapshot_time", "book_timestamp")
    )
    funding_timestamp = _parse_instant(
        _first_present(governed, "funding_timestamp") or _first_present(opp, "funding_timestamp", "funding_time")
    )
    transfer_estimate_time = _parse_instant(
        _first_present(governed, "transfer_estimate_time")
        or _first_present(opp, "transfer_estimate_time", "transfer_time", "transfer_estimate")
    )

    window_sec = _execution_window_sec(payload, opp)
    window_start = detection_time
    window_end = _parse_instant(
        _first_present(governed, "expected_execution_window_end")
        or _first_present(opp, "expected_execution_window_end", "execution_window_end")
    )
    if window_end is None:
        window_end = to_rfc3339(parse_rfc3339(detection_time) + timedelta(seconds=window_sec))

    governed_window = governed.get("expected_execution_window")
    if isinstance(governed_window, dict):
        window_start = _parse_instant(governed_window.get("start")) or window_start
        window_end = _parse_instant(governed_window.get("end")) or window_end

    expected_execution_window = {
        "start": window_start,
        "end": window_end,
        "duration_seconds": max(0, int((parse_rfc3339(window_end) - parse_rfc3339(window_start)).total_seconds())),
    }

    stale_threshold = _stale_threshold_ms(payload, opp)
    quote_age = _quote_age_ms(opp)
    now = utc_now()
    expired_reason: str | None = None
    if quote_age is not None and quote_age > stale_threshold:
        expired_reason = "quote_stale"
    elif parse_rfc3339(window_end) < now:
        expired_reason = "execution_window_expired"

    presented_as_current = expired_reason is None

    return OpportunityTimingContext(
        quote_time=quote_time,
        order_book_snapshot_time=order_book_snapshot_time,
        funding_timestamp=funding_timestamp,
        transfer_estimate_time=transfer_estimate_time,
        detection_time=detection_time,
        expected_execution_window=expected_execution_window,
        stale_threshold_ms=stale_threshold,
        quote_age_ms=quote_age,
        presented_as_current=presented_as_current,
        expired_reason=expired_reason,
        display_timezone=zone,
        local_render_quote_time=local_render_instant(parse_rfc3339(quote_time), zone),
        local_render_detection_time=local_render_instant(parse_rfc3339(detection_time), zone),
    )


def attach_opportunity_temporal_envelope(body: dict[str, Any], timing: OpportunityTimingContext) -> dict[str, Any]:
    out = dict(body)
    out["opportunity_timing"] = timing.as_dict()
    out["presented_as_current"] = timing.presented_as_current
    out["display"] = {
        "timezone": timing.display_timezone,
        "local_render_quote_time": timing.local_render_quote_time,
        "local_render_detection_time": timing.local_render_detection_time,
    }
    return out


def enrich_opportunity_rows(
    opportunities: list[dict[str, Any]],
    *,
    payload: dict[str, Any],
    scan_timestamp: str | None = None,
    display_timezone: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (current_only, all_with_timing) for arbitrage scan rows."""
    current_rows: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    for row in opportunities:
        timing = build_opportunity_timing_context(
            payload,
            opportunity=row,
            display_timezone=display_timezone,
            scan_timestamp=scan_timestamp,
        )
        if timing is None:
            continue
        enriched = dict(row)
        enriched["opportunity_timing"] = timing.as_dict()
        enriched["presented_as_current"] = timing.presented_as_current
        all_rows.append(enriched)
        if timing.presented_as_current:
            current_rows.append(enriched)
    return current_rows, all_rows
