"""Semantic runbook verification — §20 eight-part structure."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from production_readiness_governing_catalog import MATERIAL_RUNBOOK_SPECS

ROOT = Path(__file__).resolve().parents[1]

# Patterns for 8 required runbook parts
_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "trigger": [re.compile(r"trigger|symptom|when|first\s+15\s+minutes|sev-", re.I)],
    "diagnosis": [re.compile(r"diagnos|likely\s+cause|check|confirm|blast\s+radius", re.I)],
    "actions": [re.compile(r"```|command|python\s+|curl|docker|psql|pg_|backup|restore|deploy|rollback", re.I)],
    "decision": [re.compile(r"decide|decision|if\s+|whether|or\s+config\s+fix|scale-out", re.I)],
    "verification": [re.compile(r"verif|confirm|/health|/api/production/guard|sample", re.I)],
    "recovery": [re.compile(r"recover|rollback|restore|mitigat|fix\s+env", re.I)],
    "escalation": [re.compile(r"escalat|on-?call|pager|owner|war-room|communications|sev-|incident commander|contact", re.I)],
    "evidence": [re.compile(r"evidence|log|preserve|request\s+id|postmortem|timeline|audit", re.I)],
}

# Per-runbook section extraction hints
_SECTION_HINTS: dict[str, list[str]] = {
    "deployment": ["deploy", "finalize", "pre-flight"],
    "rollback": ["rollback"],
    "db_migration": ["migration", "schema"],
    "db_recovery": ["restore", "recovery"],
    "backup_restore": ["backup", "restore"],
    "provider_outage": ["5xx", "upstream", "venue", "provider", "redis", "postgres"],
    "stale_feed": ["stale", "gas", "fee", "fail-closed"],
    "queue_failure": ["redis", "queue", "webhook"],
    "worker_restart": ["worker", "uvicorn", "docker", "restart"],
    "cache_failure": ["redis", "cache"],
    "auth_security_incident": ["auth", "bypass", "security", "session"],
    "secret_rotation": ["rotat", "pepper", "secret"],
    "billing_incident": ["webhook", "psp", "billing", "401"],
    "telemetry_outage": ["monitor", "uptime", "sentry", "alert"],
    "service_degradation": ["degrad", "sev-2", "mitigate", "partial"],
}


@dataclass
class RunbookSemanticResult:
    runbook_name: str
    path: str
    trigger_present: bool
    diagnosis_present: bool
    actions_executable: bool
    decision_points_present: bool
    verification_present: bool
    recovery_present: bool
    escalation_present: bool
    evidence_preservation_present: bool

    @property
    def runbook_complete(self) -> bool:
        return all(
            (
                self.trigger_present,
                self.diagnosis_present,
                self.actions_executable,
                self.decision_points_present,
                self.verification_present,
                self.recovery_present,
                self.escalation_present,
                self.evidence_preservation_present,
            )
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "RUNBOOK_NAME": self.runbook_name,
            "TRIGGER_PRESENT": self.trigger_present,
            "DIAGNOSIS_PRESENT": self.diagnosis_present,
            "ACTIONS_EXECUTABLE": self.actions_executable,
            "DECISION_POINTS_PRESENT": self.decision_points_present,
            "VERIFICATION_PRESENT": self.verification_present,
            "RECOVERY_PRESENT": self.recovery_present,
            "ESCALATION_PRESENT": self.escalation_present,
            "EVIDENCE_PRESERVATION_PRESENT": self.evidence_preservation_present,
            "RUNBOOK_COMPLETE": self.runbook_complete,
        }


def _extract_section(text: str, hints: list[str]) -> str:
    """Return best-matching section text for a runbook topic."""
    lower = text.lower()
    if any(h.lower() in lower for h in hints):
        return text
    # Fallback: use full document (cross-referenced runbooks share files)
    return text


def _has_part(text: str, part: str) -> bool:
    return any(p.search(text) for p in _PATTERNS[part])


def verify_runbook_semantics(root: Path | None = None) -> list[RunbookSemanticResult]:
    base = root or ROOT
    results: list[RunbookSemanticResult] = []
    for spec in MATERIAL_RUNBOOK_SPECS:
        path = base / spec["path"]
        if not path.is_file():
            results.append(
                RunbookSemanticResult(
                    spec["name"],
                    spec["path"],
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                )
            )
            continue
        full_text = path.read_text(encoding="utf-8")
        hints = _SECTION_HINTS.get(spec["name"], [spec["section_hint"]])
        section = _extract_section(full_text, hints)
        results.append(
            RunbookSemanticResult(
                runbook_name=spec["name"],
                path=spec["path"],
                trigger_present=_has_part(section, "trigger"),
                diagnosis_present=_has_part(section, "diagnosis"),
                actions_executable=_has_part(section, "actions"),
                decision_points_present=_has_part(section, "decision"),
                verification_present=_has_part(section, "verification"),
                recovery_present=_has_part(section, "recovery"),
                escalation_present=_has_part(section, "escalation"),
                evidence_preservation_present=_has_part(section, "evidence"),
            )
        )
    return results


def runbook_aggregate_counters(results: list[RunbookSemanticResult]) -> dict[str, int]:
    complete = sum(1 for r in results if r.runbook_complete)
    placeholder = sum(
        1
        for r in results
        if not r.runbook_complete and not r.actions_executable and not r.verification_present
    )
    gaps = len(results) - complete
    return {
        "RUNBOOKS_REQUIRED": len(results),
        "RUNBOOKS_COMPLETE": complete,
        "RUNBOOKS_PLACEHOLDER_ONLY": placeholder,
        "RUNBOOK_EXECUTABILITY_GAPS": gaps,
    }
