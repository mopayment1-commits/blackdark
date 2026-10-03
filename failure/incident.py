"""Incident aggregation, status components, maintenance messaging (ERR-016, ERR-024–026, ERR-045)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from failure.states import ComponentStatus, IncidentLifecycle
from timezone.canonical import format_api_timestamp, utc_now

_HISTORY = Path(__file__).resolve().parents[1] / "data" / "failure_incidents.jsonl"

CANONICAL_COMPONENTS = (
    {"id": "authentication", "label": "Authentication"},
    {"id": "market_data", "label": "Market Data"},
    {"id": "analytics", "label": "Analytics"},
    {"id": "ai_intelligence", "label": "AI Intelligence"},
    {"id": "billing", "label": "Billing"},
    {"id": "notifications", "label": "Notifications"},
    {"id": "reports_exports", "label": "Reports / Exports"},
    {"id": "api", "label": "API"},
)


def append_incident_event(
    *,
    incident_id: str,
    lifecycle: IncidentLifecycle,
    affected_components: list[str],
    summary_key: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rec = {
        "incident_id": incident_id,
        "lifecycle": lifecycle.value,
        "affected_components": affected_components,
        "summary_key": summary_key,
        "recorded_at": format_api_timestamp(utc_now()),
        "metadata": metadata or {},
    }
    _HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with _HISTORY.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def aggregate_dependency_failures(failures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse duplicate alerts that share a dependency root."""
    by_dep: dict[str, dict[str, Any]] = {}
    for item in failures:
        dep = str(item.get("dependency") or item.get("affected_component") or "unknown")
        bucket = by_dep.setdefault(
            dep,
            {
                "dependency": dep,
                "summary_key": item.get("summary_key") or "error.incident.aggregated",
                "affected_components": [],
                "count": 0,
            },
        )
        bucket["count"] += 1
        comp = item.get("component")
        if comp and comp not in bucket["affected_components"]:
            bucket["affected_components"].append(comp)
    return list(by_dep.values())


def component_status_report() -> dict[str, Any]:
    from failure.circuit import snapshot as circuit_snapshot

    circuits = circuit_snapshot()
    components: list[dict[str, Any]] = []
    for comp in CANONICAL_COMPONENTS:
        status = ComponentStatus.OPERATIONAL
        if any(v.get("canonical_state") == "OPEN" for v in circuits.values()):
            status = ComponentStatus.DEGRADED_PERFORMANCE
        components.append({"id": comp["id"], "label": comp["label"], "status": status.value})
    return {
        "updated_at": format_api_timestamp(utc_now()),
        "components": components,
        "incidents": load_open_incidents(),
    }


def load_open_incidents() -> list[dict[str, Any]]:
    if not _HISTORY.is_file():
        return []
    open_map: dict[str, dict[str, Any]] = {}
    for line in _HISTORY.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        iid = rec.get("incident_id")
        if not iid:
            continue
        open_map[iid] = rec
        if rec.get("lifecycle") == IncidentLifecycle.RESOLVED.value:
            open_map.pop(iid, None)
    return list(open_map.values())


def global_banner_payload(*, lang: str | None = None) -> dict[str, Any] | None:
    incidents = load_open_incidents()
    if not incidents:
        return None
    primary = incidents[0]
    try:
        from i18n_service import t

        message = t(primary.get("summary_key") or "error.incident.banner", lang)
    except Exception:
        message = "Some platform components are currently affected."
    return {
        "message_key": primary.get("summary_key") or "error.incident.banner",
        "message": message,
        "user_action": "VIEW_STATUS",
        "incident_id": primary.get("incident_id"),
        "affected_components": primary.get("affected_components") or [],
    }


def maintenance_message(
    *,
    start_utc: str,
    affected_services: list[str],
    expected_behavior: str,
    end_utc: str | None = None,
    lang: str | None = None,
) -> dict[str, Any]:
    from timezone.format import format_user_datetime

    payload = {
        "start": format_user_datetime(start_utc, tz_name="UTC", lang=lang),
        "affected_services": affected_services,
        "expected_behavior": expected_behavior,
        "end": format_user_datetime(end_utc, tz_name="UTC", lang=lang) if end_utc else None,
        "message_key": "error.maintenance",
    }
    return payload
