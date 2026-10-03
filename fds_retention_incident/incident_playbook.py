"""Financial security incident playbook (FDS-21)."""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

PLAYBOOK_VERSION = "fds-financial-incident-v1"

IncidentType = Literal[
    "pan_discovered_in_storage",
    "sad_discovered",
    "leaked_financial_api_secret",
    "exposed_webhook_signing_secret",
    "unauthorized_financial_export",
    "bank_credential_exposure",
    "privileged_unauthorized_financial_access",
    "financial_data_in_logs_analytics_ai",
    "compromised_payment_integration",
]

LifecycleStep = Literal[
    "DETECT",
    "CONTAIN",
    "PRESERVE_EVIDENCE",
    "REVOKE_ROTATE",
    "SCOPE",
    "ERADICATE",
    "RECOVER",
    "ESCALATE_NOTIFY",
    "POST_INCIDENT_REVIEW",
    "CONTROL_IMPROVEMENT",
]

LIFECYCLE_ORDER: tuple[LifecycleStep, ...] = (
    "DETECT",
    "CONTAIN",
    "PRESERVE_EVIDENCE",
    "REVOKE_ROTATE",
    "SCOPE",
    "ERADICATE",
    "RECOVER",
    "ESCALATE_NOTIFY",
    "POST_INCIDENT_REVIEW",
    "CONTROL_IMPROVEMENT",
)

_SECRET_PATTERN = re.compile(
    r"(sk_live_[A-Za-z0-9]+|sk_test_[A-Za-z0-9]+|whsec_[A-Za-z0-9]+|"
    r"api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9]{8,}|"
    r"password\s*[:=]\s*['\"]?[^\s'\"]{4,}|"
    r"\b\d{13,19}\b)",
    re.IGNORECASE,
)

_INCIDENT_PLAYBOOK: dict[IncidentType, dict[str, Any]] = {
    "pan_discovered_in_storage": {
        "severity_default": "SEV-1",
        "affected_data_class": "FDS-C2",
        "owner": "security_oncall",
        "required_actions": ["isolate_storage", "purge_pan", "notify_dpo", "post_incident_review"],
        "revoke_rotate": ["disable_affected_export_paths"],
        "escalation": "immediate_page",
    },
    "sad_discovered": {
        "severity_default": "SEV-1",
        "affected_data_class": "FDS-C1",
        "owner": "security_oncall",
        "required_actions": ["purge_sad", "verify_psp_boundary", "post_incident_review"],
        "revoke_rotate": [],
        "escalation": "immediate_page",
    },
    "leaked_financial_api_secret": {
        "severity_default": "SEV-1",
        "affected_data_class": "FDS-C4",
        "owner": "security_oncall",
        "required_actions": ["revoke_exchange_credentials", "rotate_secrets", "scope_access_logs"],
        "revoke_rotate": ["exchange_api_keys", "service_credentials"],
        "escalation": "immediate_page",
    },
    "exposed_webhook_signing_secret": {
        "severity_default": "SEV-1",
        "affected_data_class": "FDS-C4",
        "owner": "billing_oncall",
        "required_actions": ["rotate_webhook_secret", "replay_window_review", "provider_notification"],
        "revoke_rotate": ["stripe_webhook_secret", "lemon_webhook_secret"],
        "escalation": "immediate_page",
    },
    "unauthorized_financial_export": {
        "severity_default": "SEV-1",
        "affected_data_class": "FDS-C5",
        "owner": "privacy_oncall",
        "required_actions": ["revoke_sessions", "audit_export_path", "notify_privacy_lead"],
        "revoke_rotate": ["user_sessions", "export_tokens"],
        "escalation": "privacy_escalation",
    },
    "bank_credential_exposure": {
        "severity_default": "SEV-1",
        "affected_data_class": "FDS-C3",
        "owner": "security_oncall",
        "required_actions": ["revoke_bank_tokens", "provider_notification", "scope_tenant"],
        "revoke_rotate": ["banking_tokens"],
        "escalation": "immediate_page",
    },
    "privileged_unauthorized_financial_access": {
        "severity_default": "SEV-1",
        "affected_data_class": "FDS-C5",
        "owner": "security_oncall",
        "required_actions": ["revoke_privileged_session", "access_review", "break_glass_audit"],
        "revoke_rotate": ["privileged_sessions", "break_glass_grants"],
        "escalation": "immediate_page",
    },
    "financial_data_in_logs_analytics_ai": {
        "severity_default": "SEV-1",
        "affected_data_class": "FDS-C5",
        "owner": "security_oncall",
        "required_actions": ["purge_logs", "block_ai_boundary", "dlp_review"],
        "revoke_rotate": ["ai_export_tokens"],
        "escalation": "immediate_page",
    },
    "compromised_payment_integration": {
        "severity_default": "SEV-1",
        "affected_data_class": "FDS-C6",
        "owner": "billing_oncall",
        "required_actions": ["disable_checkout", "rotate_psp_keys", "reconcile_billing_events"],
        "revoke_rotate": ["stripe_keys", "lemon_keys", "webhook_secrets"],
        "escalation": "immediate_page",
    },
}


def _evidence_path() -> Path:
    base = Path(os.getenv("DATA_DIR", "data"))
    return base / "financial_incident_evidence.jsonl"


def _append_evidence(record: dict[str, Any]) -> None:
    path = _evidence_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def _sanitize_value(value: Any) -> None:
    if isinstance(value, str) and _SECRET_PATTERN.search(value):
        raise ValueError("incident_record_contains_restricted_pattern")
    if isinstance(value, list):
        for item in value:
            _sanitize_value(item)
    if isinstance(value, dict):
        for item in value.values():
            _sanitize_value(item)


def _sanitize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Ensure no secret values appear in user-supplied incident fields."""
    for key in ("detection_source", "notes", "affected_tenant"):
        if key in record:
            _sanitize_value(record[key])
    for ref in record.get("evidence_references", []):
        _sanitize_value(ref)
    return record


def playbook_for(incident_type: IncidentType) -> dict[str, Any]:
    base = _INCIDENT_PLAYBOOK[incident_type]
    return {"incident_type": incident_type, "playbook_version": PLAYBOOK_VERSION, **base}


def all_incident_types() -> list[str]:
    return list(_INCIDENT_PLAYBOOK.keys())


def create_incident(
    incident_type: IncidentType,
    *,
    severity: str | None = None,
    affected_tenant: str = "",
    affected_users: list[str] | None = None,
    detection_source: str = "",
    credentials_affected: list[str] | None = None,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Create incident record without storing secret values."""
    spec = playbook_for(incident_type)
    now = datetime.now(UTC)
    record: dict[str, Any] = {
        "incident_id": str(uuid.uuid4()),
        "incident_type": incident_type,
        "playbook_version": PLAYBOOK_VERSION,
        "severity": severity or spec["severity_default"],
        "affected_data_class": spec["affected_data_class"],
        "affected_tenant": affected_tenant,
        "affected_users": affected_users or [],
        "detection_timestamp": now.isoformat(),
        "detection_source": detection_source,
        "containment_timestamp": None,
        "credentials_tokens_affected": credentials_affected or spec.get("revoke_rotate", []),
        "owner": spec["owner"],
        "status": "open",
        "evidence_references": evidence_refs or [],
        "required_actions": spec["required_actions"],
        "notification_escalation_state": "pending",
        "lifecycle_steps_completed": ["DETECT"],
        "post_incident_review_required": True,
        "post_incident_review_completed": False,
        "unresolved_gaps": [],
    }
    _sanitize_record(record)
    _append_evidence({"event": "incident_created", **record})
    return record


def advance_incident(
    incident_id: str,
    step: LifecycleStep,
    *,
    outcome: str = "completed",
    notes: str = "",
) -> dict[str, Any]:
    """Advance incident through lifecycle; never store secrets in notes."""
    if _SECRET_PATTERN.search(notes):
        raise ValueError("incident_notes_contain_restricted_pattern")
    update = {
        "event": "incident_lifecycle_step",
        "incident_id": incident_id,
        "step": step,
        "timestamp": datetime.now(UTC).isoformat(),
        "outcome": outcome,
        "notes": notes,
        "playbook_version": PLAYBOOK_VERSION,
    }
    if step == "CONTAIN":
        update["containment_timestamp"] = update["timestamp"]
    if step == "POST_INCIDENT_REVIEW":
        update["post_incident_review_completed"] = outcome == "completed"
    _append_evidence(update)
    return update


def route_incident(incident_type: IncidentType, *, detection_source: str = "") -> dict[str, Any]:
    """Create and route incident with required lifecycle plan."""
    incident = create_incident(incident_type, detection_source=detection_source)
    plan = {
        "incident_id": incident["incident_id"],
        "incident_type": incident_type,
        "lifecycle_plan": list(LIFECYCLE_ORDER),
        "required_actions": incident["required_actions"],
        "escalation": playbook_for(incident_type).get("escalation"),
        "revoke_rotate_targets": incident["credentials_tokens_affected"],
    }
    _append_evidence({"event": "incident_routed", **plan})
    return {**incident, "routing": plan}


def incident_playbook_status() -> dict[str, Any]:
    return {
        "playbook_version": PLAYBOOK_VERSION,
        "incident_types": all_incident_types(),
        "lifecycle_steps": list(LIFECYCLE_ORDER),
        "evidence_path": str(_evidence_path()),
    }
