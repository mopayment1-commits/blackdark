"""Runnable financial incident drill harness — synthetic data only (SDG-16)."""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fds_retention_incident.incident_playbook import (
    LIFECYCLE_ORDER,
    IncidentType,
    advance_incident,
    route_incident,
)

DRILL_VERSION = "fds-incident-drill-v1"

_REQUIRED_STEPS = frozenset(
    {
        "DETECT",
        "CONTAIN",
        "PRESERVE_EVIDENCE",
        "REVOKE_ROTATE",
        "SCOPE",
        "ESCALATE_NOTIFY",
        "POST_INCIDENT_REVIEW",
    }
)

_DRILL_SCENARIOS: dict[str, dict[str, Any]] = {
    "pan_in_log_fixture": {
        "incident_type": "pan_discovered_in_storage",
        "fixture": "synthetic_log_line_with_masked_pan_reference_only",
        "detection_source": "dlp_scan_fixture",
        "synthetic_indicator": "PAN_REF_SYNTHETIC_411111",
    },
    "webhook_secret_exposed": {
        "incident_type": "exposed_webhook_signing_secret",
        "fixture": "synthetic_webhook_secret_exposure_indicator",
        "detection_source": "secret_scan_fixture",
        "synthetic_indicator": "WEBHOOK_SECRET_EXPOSURE_SYNTHETIC",
    },
    "exchange_api_secret_leaked": {
        "incident_type": "leaked_financial_api_secret",
        "fixture": "synthetic_exchange_credential_leak_indicator",
        "detection_source": "credential_monitor_fixture",
        "synthetic_indicator": "EXCHANGE_SECRET_LEAK_SYNTHETIC",
    },
    "unauthorized_bulk_financial_export": {
        "incident_type": "unauthorized_financial_export",
        "fixture": "synthetic_bulk_export_attempt",
        "detection_source": "privileged_access_audit_fixture",
        "synthetic_indicator": "BULK_EXPORT_SYNTHETIC",
    },
    "financial_data_ai_boundary": {
        "incident_type": "financial_data_in_logs_analytics_ai",
        "fixture": "synthetic_ai_boundary_violation",
        "detection_source": "ai_boundary_fixture",
        "synthetic_indicator": "AI_BOUNDARY_LEAK_SYNTHETIC",
    },
    "privileged_misuse": {
        "incident_type": "privileged_unauthorized_financial_access",
        "fixture": "synthetic_privileged_misuse",
        "detection_source": "break_glass_audit_fixture",
        "synthetic_indicator": "PRIVILEGED_MISUSE_SYNTHETIC",
    },
}


def _evidence_path() -> Path:
    base = Path(os.getenv("DATA_DIR", "data"))
    return base / "financial_incident_drill_evidence.jsonl"


def _append_evidence(record: dict[str, Any]) -> None:
    path = _evidence_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def drill_scenarios() -> list[str]:
    return list(_DRILL_SCENARIOS.keys())


def run_drill_scenario(scenario_key: str) -> dict[str, Any]:
    """Execute synthetic drill; PASS only when required lifecycle steps complete."""
    if scenario_key not in _DRILL_SCENARIOS:
        return {"scenario": scenario_key, "passed": False, "error": "unknown_scenario"}

    spec = _DRILL_SCENARIOS[scenario_key]
    incident_type: IncidentType = spec["incident_type"]
    drill_id = str(uuid.uuid4())
    started = datetime.now(UTC)

    incident = route_incident(incident_type, detection_source=spec["detection_source"])
    incident_id = incident["incident_id"]
    steps_completed: list[str] = ["DETECT"]
    decisions: list[dict[str, Any]] = []

    for step in LIFECYCLE_ORDER:
        if step == "DETECT":
            continue
        notes = f"synthetic_drill:{scenario_key}:{spec['synthetic_indicator']}"
        result = advance_incident(incident_id, step, outcome="completed", notes=notes)
        steps_completed.append(step)
        decisions.append(
            {
                "step": step,
                "timestamp": result["timestamp"],
                "outcome": result["outcome"],
            }
        )
        if step == "REVOKE_ROTATE":
            decisions[-1]["revoke_rotate_triggered"] = True
        if step == "PRESERVE_EVIDENCE":
            decisions[-1]["evidence_preserved"] = True
        if step == "ESCALATE_NOTIFY":
            decisions[-1]["notification_decision"] = "escalate_per_playbook"

    missing = sorted(_REQUIRED_STEPS - set(steps_completed))
    passed = len(missing) == 0
    unresolved: list[str] = []
    if missing:
        unresolved.append(f"missing_lifecycle_steps:{','.join(missing)}")

    record = {
        "event": "incident_drill_completed",
        "drill_id": drill_id,
        "drill_version": DRILL_VERSION,
        "scenario": scenario_key,
        "incident_type": incident_type,
        "incident_id": incident_id,
        "synthetic_only": True,
        "controls_invoked": incident["required_actions"],
        "started_at": started.isoformat(),
        "completed_at": datetime.now(UTC).isoformat(),
        "lifecycle_steps_completed": steps_completed,
        "decisions": decisions,
        "outcome": "PASS" if passed else "FAIL",
        "unresolved_gaps": unresolved,
        "policy_version": incident.get("playbook_version"),
        "post_incident_review_required": True,
        "post_incident_review_completed": "POST_INCIDENT_REVIEW" in steps_completed,
    }
    _append_evidence(record)
    return record


def run_all_drills() -> dict[str, Any]:
    results = {key: run_drill_scenario(key) for key in drill_scenarios()}
    all_passed = all(r.get("outcome") == "PASS" for r in results.values())
    summary = {
        "drill_version": DRILL_VERSION,
        "scenario_count": len(results),
        "passed": sum(1 for r in results.values() if r.get("outcome") == "PASS"),
        "failed": sum(1 for r in results.values() if r.get("outcome") != "PASS"),
        "all_passed": all_passed,
        "scenarios": results,
    }
    _append_evidence({"event": "incident_drill_suite", **summary, "timestamp": time.time()})
    return summary
