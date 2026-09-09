"""Financial data security incident playbook — testable workflow."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from uuid import uuid4


class IncidentPhase(StrEnum):
    DETECT = "DETECT"
    CONTAIN = "CONTAIN"
    PRESERVE = "PRESERVE"
    REVOKE = "REVOKE"
    SCOPE = "SCOPE"
    ERADICATE = "ERADICATE"
    RECOVER = "RECOVER"
    ESCALATE = "ESCALATE"
    REVIEW = "REVIEW"


INCIDENT_TRIGGERS = frozenset(
    {
        "pan_in_storage",
        "cvv_discovered",
        "financial_api_secret_exposed",
        "unauthorized_financial_export",
        "webhook_secret_compromised",
        "financial_data_in_logs_or_ai",
    }
)


def run_incident_drill(*, trigger: str = "pan_in_storage") -> dict[str, Any]:
    if trigger not in INCIDENT_TRIGGERS:
        raise ValueError(f"Unknown trigger: {trigger}")
    incident_id = f"inc_{uuid4().hex[:12]}"
    phases = [p.value for p in IncidentPhase]
    return {
        "incident_id": incident_id,
        "trigger": trigger,
        "phases_executed": phases,
        "playbook_testable": True,
        "evidence": f"drill:{incident_id}",
    }


def incident_playbook_status() -> dict[str, Any]:
    return {"triggers": sorted(INCIDENT_TRIGGERS), "phases": [p.value for p in IncidentPhase]}
