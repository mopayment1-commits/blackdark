"""
Data Health / SLA Monitor — Feature #849 (Sprint-0 Infrastructure).

Merged into #789 Observability Stack. Per-venue SLOs for data connectors.
Internal Grafana dashboard — alerts for team only.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.DataHealthMonitor")

_FEATURE_REF = 849
_STANDALONE = False
_MERGED_INTO = "Sprint-0 Infrastructure / Observability Stack"
_COMPONENT = "data_health_monitor"
_INFRA_OBS_REF = 789
_SEED_PATH = Path("data/data_health_monitor_seed.json")

_VENUE_SLOS_MS = {
    "oracle_api": 500,
    "market_radar": 1000,
    "on_chain": 3000,
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("data health monitor seed load failed: %s", exc)
        return {}


def evaluate_venue_slo_849(
    venue: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Per-venue SLO evaluation — latency/gaps/errors."""
    seed = seed or _load_seed()
    venues = seed.get("venues") or {}
    venue_data = venues.get(venue)
    if not venue_data:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "venue_not_found", "venue": venue}

    slo_ms = int(venue_data.get("slo_latency_ms", _VENUE_SLOS_MS.get(venue, 1000)))
    latency_p99 = float(venue_data.get("latency_p99_ms", 0))
    gap_count = int(venue_data.get("gap_count", 0))
    error_rate = float(venue_data.get("error_rate_pct", 0))

    latency_ok = latency_p99 <= slo_ms
    gaps_ok = gap_count == 0
    errors_ok = error_rate <= float(venue_data.get("error_rate_max_pct", 0.1))

    return {
        "ok": latency_ok and gaps_ok and errors_ok,
        "feature_ref": _FEATURE_REF,
        "venue": venue,
        "slo_latency_ms": slo_ms,
        "latency_p99_ms": latency_p99,
        "within_slo": latency_ok,
        "gap_count": gap_count,
        "gaps_ok": gaps_ok,
        "error_rate_pct": error_rate,
        "errors_ok": errors_ok,
        "timestamp": _utcnow(),
    }


def build_data_health_panel_849(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Health aggregation for ops Grafana dashboard."""
    seed = seed or _load_seed()
    cfg = seed.get("data_health_monitor_849") or {}
    venues = list((seed.get("venues") or {}).keys())
    evaluations = [evaluate_venue_slo_849(v, seed=seed) for v in venues]

    return {
        "ok": all(e.get("ok") for e in evaluations),
        "feature_ref": _FEATURE_REF,
        "merged_into": _MERGED_INTO,
        "component": _COMPONENT,
        "standalone_rejected": True,
        "no_user_surface": True,
        "internal_dashboard": "Grafana (team only)",
        "infra_observability_ref": _INFRA_OBS_REF,
        "per_venue_slos": dict(_VENUE_SLOS_MS),
        "venue_evaluations": evaluations,
        "alerts_enabled": cfg.get("alerts_enabled", True),
        "alert_channel": cfg.get("alert_channel", "pagerduty_devops"),
        "timestamp": _utcnow(),
    }


def build_infra_observability_health_feed_849(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#849 → #789 Infrastructure Observability feed."""
    panel = build_data_health_panel_849(seed=seed)
    return {
        "ok": panel.get("ok", False),
        "feature_ref": _FEATURE_REF,
        "feeds": f"#{_INFRA_OBS_REF} Infrastructure Observability",
        "all_venues_within_slo": panel.get("ok"),
        "venue_count": len(panel.get("venue_evaluations") or []),
        "grafana_dashboard": "blackdark-data-health-internal",
        "timestamp": _utcnow(),
    }


def data_health_monitor_status_849(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "component": _COMPONENT,
        "sprint": 0,
        "no_user_surface": True,
        "infra_observability_ref": _INFRA_OBS_REF,
        "per_venue_slos_ms": dict(_VENUE_SLOS_MS),
        "metrics": ["latency", "gaps", "errors"],
        "internal_dashboard": "Grafana",
        "timestamp": _utcnow(),
    }


def run_data_health_e2e_849(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    status = data_health_monitor_status_849(seed=seed)
    tests.append({"test": "standalone_rejected", "passed": status.get("standalone_rejected") is True})
    tests.append({"test": "oracle_slo_500ms", "passed": status.get("per_venue_slos_ms", {}).get("oracle_api") == 500})
    tests.append({"test": "market_radar_slo_1s", "passed": status.get("per_venue_slos_ms", {}).get("market_radar") == 1000})
    tests.append({"test": "onchain_slo_3s", "passed": status.get("per_venue_slos_ms", {}).get("on_chain") == 3000})

    for venue in ("oracle_api", "market_radar", "on_chain"):
        ev = evaluate_venue_slo_849(venue, seed=seed)
        tests.append({"test": f"{venue}_within_slo", "passed": ev.get("within_slo") is True})

    feed = build_infra_observability_health_feed_849(seed=seed)
    tests.append({"test": "feeds_infra_obs_789", "passed": feed.get("feeds") == "#789 Infrastructure Observability"})

    panel = build_data_health_panel_849(seed=seed)
    tests.append({"test": "all_venues_healthy", "passed": panel.get("ok") is True})

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "e2e_tests": tests,
        "all_passed": all_passed,
        "timestamp": _utcnow(),
    }
