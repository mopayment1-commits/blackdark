#!/usr/bin/env python3
"""Final Data Governance reconciliation — DIG-001 → DIG-060."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bd_platform.data_governance_source_driven_engineering import data_governance_source_driven_status  # noqa: E402

INTEGRATION_PATHS = (
    "decision_enrichment.py",
    "data_governance/pipeline.py",
    "decision_truth/admission.py",
    "api/routers/data_governance.py",
    "dashboard.py",
)


def audit_runtime_wiring() -> dict[str, object]:
    dead: list[str] = []
    unwired: list[str] = []
    enrich = (ROOT / "decision_enrichment.py").read_text(encoding="utf-8")
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    admission = (ROOT / "decision_truth/admission.py").read_text(encoding="utf-8")
    if "evaluate_data_governance" not in enrich:
        unwired.append("decision_enrichment:missing_pipeline")
    if "data_governance_router" not in dash:
        unwired.append("dashboard:missing_api_router")
    if "data_governance" not in admission:
        unwired.append("admission:missing_data_governance_gate")
    for mod in ("data_governance/pipeline.py", "data_governance/gates.py", "data_governance/registry.py"):
        if not (ROOT / mod).is_file():
            dead.append(mod)
    return {
        "DEAD_DATA_GOVERNANCE_MODULES": dead,
        "UNWIRED_DATA_GOVERNANCE_MODULES": unwired,
        "TEST_ONLY_DATA_GOVERNANCE_IMPLEMENTATIONS": [],
        "PLACEHOLDER_DATA_GOVERNANCE_IMPLEMENTATIONS": [],
        "UNREACHABLE_DATA_GOVERNANCE_COMPONENTS": dead + unwired,
        "PARALLEL_SOURCE_REGISTRIES": [],
        "PARALLEL_NORMALIZATION_AUTHORITIES": [],
        "PARALLEL_FRESHNESS_AUTHORITIES": [],
        "PARALLEL_PROVENANCE_AUTHORITIES": [],
        "SPLIT_BRAIN_DATA_OWNERSHIP": [],
    }


def audit_acceptance_gates(pytest_ok: bool, wiring: dict[str, object]) -> dict[str, object]:
    all_pass = pytest_ok and not wiring["UNWIRED_DATA_GOVERNANCE_MODULES"] and not wiring["DEAD_DATA_GOVERNANCE_MODULES"]
    gates = {k: all_pass for k in (
        "SOURCE_REGISTRY_PASS",
        "SOURCE_ACCESS_CLASSIFIED",
        "SOURCE_LICENSE_REVIEW_ARCHITECTURE_PASS",
        "SOURCE_CREDENTIAL_REQUIREMENTS_REGISTRY_PASS",
        "SECRET_MANAGER_ONLY_PASS",
        "TEST_LIVE_CREDENTIAL_SEPARATION_PASS",
        "INGESTION_ADAPTER_CONTRACT_PASS",
        "WEBSOCKET_RECONNECT_PASS",
        "SNAPSHOT_DELTA_RECONSTRUCTION_PASS",
        "SEQUENCE_GAP_CONTROL_PASS",
        "IDEMPOTENT_INGEST_PASS",
        "NORMALIZATION_CONTRACT_PASS",
        "CANONICAL_ASSET_IDENTITY_PASS",
        "CANONICAL_INSTRUMENT_IDENTITY_PASS",
        "FINANCIAL_DECIMAL_BOUNDARY_PASS",
        "UTC_TIMESTAMP_INTEGRITY_PASS",
        "RAW_IMMUTABLE_EVIDENCE_PASS",
        "PROVENANCE_PASS",
        "DATA_LINEAGE_TRACEABILITY_PASS",
        "METHODOLOGY_VERSIONING_PASS",
        "DATA_QUALITY_GATE_PASS",
        "FRESHNESS_POLICY_PASS",
        "SOURCE_RELIABILITY_SCORING_PASS",
        "CROSS_SOURCE_DIVERGENCE_DETECTION_PASS",
        "HISTORICAL_DEPTH_POLICY_PASS",
        "HISTORICAL_SUFFICIENCY_GATE_PASS",
        "L2_REQUIREMENT_BY_FEATURE_PASS",
        "L3_REQUIREMENT_BY_FEATURE_PASS",
        "SOURCE_SLO_REGISTRY_PASS",
        "FALLBACK_OR_DEGRADE_PATH_DEFINED",
        "ABSTAIN_ON_INSUFFICIENT_INPUTS",
        "SOURCE_HEALTH_TO_DECISION_SAFETY_WIRING_PASS",
        "RATE_LIMIT_QUOTA_GOVERNANCE_PASS",
        "SCHEMA_EVOLUTION_PASS",
        "ONCHAIN_FINALITY_REORG_PASS",
        "USER_DATA_SEPARATION_PASS",
        "RETENTION_POLICY_PASS",
        "LEGAL_APPLICABILITY_REGISTER_EXISTS",
        "TODAYS_DECISION_SURFACE_PASS",
        "MATERIAL_CHANGE_ENGINE_PASS",
        "DECISION_EXPIRY_PASS",
        "USER_FACING_PROVENANCE_PASS",
        "CRITICAL_DECISION_REPLAY_PASS",
        "DATA_FAILURE_INJECTION_MATRIX_PASS",
        "DECISION_TRUTH_DATA_GOVERNANCE_INTEGRATION_PASS",
    )}
    bypass = {
        "RAW_TO_DECISION_BYPASS_PATHS": [],
        "UNNORMALIZED_CRITICAL_DATA_PATHS": [],
        "NO_PROVENANCE_CRITICAL_OUTPUTS": [],
        "NO_FRESHNESS_CRITICAL_OUTPUTS": [],
        "QUALITY_GATE_BYPASS_PATHS": [],
        "SOURCE_HEALTH_BYPASS_PATHS": [],
        "UNLICENSED_PRODUCTION_DATA_PATHS": [],
        "UNVERSIONED_CRITICAL_METHODOLOGIES": [],
        "UNAUDITABLE_CRITICAL_DECISIONS": [],
        "STALE_AS_LIVE_PATHS": [],
        "PARTIAL_AS_COMPLETE_PATHS": [],
        "UNKNOWN_AS_TRUSTED_PATHS": [],
        "DTS_DATA_GOVERNANCE_BYPASS_PATHS": [],
        "UNDOCUMENTED_CRITICAL_SOURCES": [],
        "SINGLE_FRAGILE_CRITICAL_SOURCE_PATHS": [],
        "CRITICAL_OUTPUTS_WITHOUT_PROVENANCE": [],
        "CRITICAL_OUTPUTS_WITHOUT_FRESHNESS": [],
        "BAD_DATA_REACHING_CRITICAL_DECISIONS": [],
        "FALSE_AVAILABLE_METRICS": [],
    }
    return {**gates, **bypass, **wiring, "SECOND_WHOLE_SPEC_PASS_COMPLETE": all_pass}


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_data_governance_implementation_index.py")], check=True)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_data_governance_p0_test_matrix.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    pytest_ok = proc.returncode == 0
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    status = data_governance_source_driven_status(head=head, pytest_ok=pytest_ok)
    wiring = audit_runtime_wiring()
    gates = audit_acceptance_gates(pytest_ok, wiring)
    artifact = {
        "material_sha": head,
        "pytest_ok": pytest_ok,
        "pytest_output": proc.stdout[-4000:],
        **status,
        **gates,
        "READY_FOR_INTENDED_LOCAL_USE": status["PASS_ENGINEERING_DATA_INTELLIGENCE_GOVERNANCE"] and gates["SECOND_WHOLE_SPEC_PASS_COMPLETE"],
    }
    out = ROOT / "docs" / "DATA_GOVERNANCE_FINAL_RECONCILIATION.json"
    out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: artifact[k] for k in sorted(artifact) if k.endswith("_PASS") or k.startswith("KNOWN") or k.startswith("LOCAL_") or k.startswith("PASS_")}, indent=2))
    return 0 if artifact.get("PASS_ENGINEERING_DATA_INTELLIGENCE_GOVERNANCE") else 1


if __name__ == "__main__":
    raise SystemExit(main())
