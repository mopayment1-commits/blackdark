#!/usr/bin/env python3
"""v6 tri-state status model — BLACKDARK Institutional Capability Standard 2026 v6."""
from __future__ import annotations

from typing import Any, Literal

EngineeringStatus = Literal[
    "PASS_ENGINEERING",
    "PARTIAL",
    "FAIL",
    "NOT_APPLICABLE",
    "NOT_COMPLETE",
]
LiveStatus = Literal[
    "PASS_LIVE",
    "AWAITING_DEPLOY",
    "BLOCKED_EXTERNAL",
    "NOT_CLAIMED",
]
AssuranceStatus = Literal[
    "ASSURANCE_READY",
    "PENDING_INDEPENDENT_ASSURANCE",
    "NOT_APPLICABLE",
]

# Audit environment for this repository's Cloud Agent / local VM runs.
AUDIT_ENVIRONMENT = "local_dev_vm"
PRODUCTION_DEPLOYMENT_EVIDENCE = False


def batch_for_id(capability_id: int) -> str:
    if capability_id < 1:
        return "unknown"
    n = (capability_id - 1) // 50 + 1
    return f"batch{n:02d}"


def legacy_status_to_v6(
    legacy_status: str,
    *,
    batch_closed: bool,
    runtime_success: bool | None = None,
) -> dict[str, str]:
    """Map legacy single status → v6 tri-state. PASS_LIVE never granted without production."""
    eng: EngineeringStatus
    if legacy_status == "PRODUCTION-ALIGNED":
        eng = "PASS_ENGINEERING"
    elif legacy_status == "PERFORMANCE-UNVERIFIABLE":
        eng = "PASS_ENGINEERING" if runtime_success is not False else "PARTIAL"
    elif legacy_status in ("CONCEPTUALLY-UNSOUND", "SPLIT-BRAIN-UNVERIFIED", "FAIL"):
        eng = "FAIL"
    elif legacy_status == "NOT_COMPLETE":
        eng = "PARTIAL" if batch_closed and runtime_success is not False else "NOT_COMPLETE"
    else:
        eng = "PARTIAL"

    live: LiveStatus = "NOT_CLAIMED"
    if not PRODUCTION_DEPLOYMENT_EVIDENCE:
        live = "NOT_CLAIMED"
    assurance: AssuranceStatus = "PENDING_INDEPENDENT_ASSURANCE"

    return {
        "engineering_status": eng,
        "live_status": live,
        "assurance_status": assurance,
        "v6_audit_environment": AUDIT_ENVIRONMENT,
        "v6_production_deployed": "false",
    }


def evidence_pack_functions_check(batch: str, evidence: dict[str, Any]) -> dict[str, Any]:
    """§139.3 — twelve function coverage (presence of evidence, not fixed filenames)."""
    required = [
        "scope_inventory",
        "requirements_traceability",
        "semantic_correctness",
        "canonical_duplicate_reconciliation",
        "consumer_path_evidence",
        "security_entitlement",
        "data_provenance",
        "reliability_performance",
        "regression",
        "quality_security_gate",
        "build_provenance",
        "engineering_live_assurance_status",
    ]
    present = {k: bool(evidence.get(k)) for k in required}
    return {
        "batch": batch,
        "functions_required": len(required),
        "functions_covered": sum(present.values()),
        "coverage_met": all(present.values()),
        "per_function": present,
    }
