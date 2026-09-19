"""
Launch-57 canonical chart display timing owner for B13 (SPEC §22, cross-cutting).

Zero legacy/PARKED runtime dependencies on cap646 or decision_certificate.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from launch57.temporal_common import local_render_instant, parse_rfc3339, to_rfc3339

METHODOLOGY_VERSION = "launch57-chart-display-timing-common-1.0"
CHART_COMPONENT_NAMES: tuple[str, ...] = (
    "candles",
    "axes",
    "crosshair",
    "annotations",
    "events",
    "tooltips",
)
CHART_SURFACE_NAMES: frozenset[str] = frozenset({"ohlcv"})
CHART_BODY_KEYS: frozenset[str] = frozenset({"chart_view", "bars", "candles"})
DEFAULT_CANONICAL_STORAGE_TIMEZONE = "UTC"


@dataclass(frozen=True)
class ChartDisplayTimingContext:
    display_timezone: str
    canonical_storage_timezone: str
    components_bound: tuple[str, ...]
    timezone_mixing_detected: bool
    mixing_violations: tuple[str, ...]
    chart_temporally_consistent: bool
    expired_reason: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "display_timezone": self.display_timezone,
            "canonical_storage_timezone": self.canonical_storage_timezone,
            "components_bound": list(self.components_bound),
            "timezone_mixing_detected": self.timezone_mixing_detected,
            "mixing_violations": list(self.mixing_violations),
            "chart_temporally_consistent": self.chart_temporally_consistent,
            "expired_reason": self.expired_reason,
            "methodology_version": METHODOLOGY_VERSION,
        }


def is_chart_bearing_body(body: dict[str, Any]) -> bool:
    if str(body.get("surface") or "") in CHART_SURFACE_NAMES:
        return True
    if body.get("chart_view") is not None:
        return True
    return any(key in body for key in CHART_BODY_KEYS)


def _normalize_zone(value: Any, fallback: str) -> str:
    zone = str(value or "").strip()
    return zone if zone else fallback


def _ms_to_canonical_rfc3339(open_time_ms: Any) -> str | None:
    if open_time_ms is None:
        return None
    try:
        ms = int(open_time_ms)
    except (TypeError, ValueError):
        return None
    return to_rfc3339(datetime.fromtimestamp(ms / 1000.0, tz=UTC))


def _component_timezones(chart_view: dict[str, Any]) -> dict[str, str | None]:
    zones: dict[str, str | None] = {}
    view_zone = chart_view.get("display_timezone")
    for name in CHART_COMPONENT_NAMES:
        block = chart_view.get(name)
        if name == "axes" and isinstance(block, dict):
            for axis_key, axis_val in block.items():
                if isinstance(axis_val, dict) and axis_val.get("display_timezone"):
                    zones[f"axes.{axis_key}"] = str(axis_val["display_timezone"])
            continue
        if isinstance(block, dict) and block.get("display_timezone"):
            zones[name] = str(block["display_timezone"])
        elif isinstance(block, list) and block:
            for idx, item in enumerate(block):
                if isinstance(item, dict) and item.get("display_timezone"):
                    zones[f"{name}[{idx}]"] = str(item["display_timezone"])
        elif block is not None and view_zone:
            zones[name] = str(view_zone)
    return zones


def build_chart_display_timing_context(
    payload: dict[str, Any],
    *,
    chart_view: dict[str, Any] | None = None,
    display_timezone: str | None = None,
) -> ChartDisplayTimingContext:
    """Bind one explicit display timezone per chart view; fail closed on silent mixing."""
    governed = dict(payload.get("governed_payload") or {})
    view = dict(chart_view or payload.get("chart_view") or {})
    zone = _normalize_zone(
        display_timezone or payload.get("display_timezone") or governed.get("display_timezone") or view.get("display_timezone"),
        "UTC",
    )
    canonical_zone = _normalize_zone(
        governed.get("canonical_storage_timezone") or view.get("canonical_storage_timezone"),
        DEFAULT_CANONICAL_STORAGE_TIMEZONE,
    )

    mixing: list[str] = []
    for component, component_zone in _component_timezones(view).items():
        if component_zone is not None and component_zone != zone:
            mixing.append(f"{component}_timezone_mismatch:{component_zone}!={zone}")

    explicit_conflicts = list(view.get("timezone_mixing_violations") or [])
    mixing.extend(str(v) for v in explicit_conflicts)

    expired_reason = "chart_timezone_mixing" if mixing else None
    components_bound = tuple(CHART_COMPONENT_NAMES) if view else tuple()

    return ChartDisplayTimingContext(
        display_timezone=zone,
        canonical_storage_timezone=canonical_zone,
        components_bound=components_bound,
        timezone_mixing_detected=bool(mixing),
        mixing_violations=tuple(mixing),
        chart_temporally_consistent=expired_reason is None,
        expired_reason=expired_reason,
    )


def bind_chart_components(
    body: dict[str, Any],
    *,
    display_timezone: str,
    canonical_storage_timezone: str = DEFAULT_CANONICAL_STORAGE_TIMEZONE,
) -> dict[str, Any]:
    """Materialize chart_view with unified display timezone across candles/axes/crosshair/etc."""
    out = dict(body)
    zone = _normalize_zone(display_timezone, "UTC")
    bars = list(out.get("bars") or out.get("candles") or [])
    candles: list[dict[str, Any]] = []
    for bar in bars:
        row = dict(bar)
        canonical_open = _ms_to_canonical_rfc3339(row.get("open_time_ms"))
        if canonical_open is not None:
            row["canonical_open_time"] = canonical_open
            row["local_render_open_time"] = local_render_instant(parse_rfc3339(canonical_open), zone)
        row["display_timezone"] = zone
        candles.append(row)

    annotations = list((out.get("chart_view") or {}).get("annotations") or out.get("annotations") or [])
    events = list((out.get("chart_view") or {}).get("events") or out.get("events") or [])

    chart_view = {
        "display_timezone": zone,
        "canonical_storage_timezone": canonical_storage_timezone,
        "candles": candles,
        "axes": {"x": {"display_timezone": zone}, "y": {"display_timezone": zone}},
        "crosshair": {"display_timezone": zone},
        "annotations": [{**dict(a), "display_timezone": zone} if isinstance(a, dict) else a for a in annotations],
        "events": [{**dict(e), "display_timezone": zone} if isinstance(e, dict) else e for e in events],
        "tooltips": {"display_timezone": zone},
    }
    out["chart_view"] = chart_view
    if candles:
        out["candles"] = candles
    return out


def attach_chart_display_temporal_envelope(
    body: dict[str, Any],
    timing: ChartDisplayTimingContext,
) -> dict[str, Any]:
    out = dict(body)
    out["chart_display_timing"] = timing.as_dict()
    out["chart_temporally_consistent"] = timing.chart_temporally_consistent
    out["display"] = {
        "timezone": timing.display_timezone,
        "canonical_storage_timezone": timing.canonical_storage_timezone,
    }
    return out
