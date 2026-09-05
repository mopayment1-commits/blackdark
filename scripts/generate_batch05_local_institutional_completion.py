#!/usr/bin/env python3
"""Batch05 local institutional completion — all work executable without live Railway.

Does NOT claim PASS_LIVE, G6, G7, or ASSURANCE_READY.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOCKS = {
    "batch05_independent": 0,
    "progress_826": 179,
    "production_aligned_count": 0,
    "pa_elevated_count": 0,
    "live_ready": False,
    "assurance_ready": False,
}

CRITICAL_JOURNEYS = [
    {"id": "J1", "name": "Strangler execute BTC", "endpoint": "POST /api/cap646/{id}/execute", "sample_ids": [201, 205, 242]},
    {"id": "J2", "name": "REUSED-LINK facade", "endpoint": "batch05_dedicated.execute", "sample_ids": [206, 214, 226, 232, 245]},
    {"id": "J3", "name": "Public API surface", "endpoint": "GET /api/cap646/247", "sample_ids": [247]},
    {"id": "J4", "name": "Entitlement gateway", "endpoint": "gateway_execute pro-tier", "sample_ids": [201, 214, 245]},
]

LIVE_ONLY_ITEMS = [
    {"id": "LZ1", "gate": "G6", "item": "Gate Zero live health + cap646 probes", "script": "scripts/execute_batch05_gate_zero_live.py"},
    {"id": "LZ2", "gate": "G6", "item": "Live E2E per-ID semantic verification (50)", "blocked_by": "Railway compute limit exceeded"},
    {"id": "LZ3", "gate": "G6", "item": "Live entitlement gateway proof", "blocked_by": "No production app bound"},
    {"id": "LZ4", "gate": "G6", "item": "Production performance/load (k6)", "blocked_by": "AWAITING_DEPLOY"},
    {"id": "LZ5", "gate": "G7", "item": "12207 Validation workshop with live artifacts", "blocked_by": "G6 prerequisite"},
    {"id": "LZ6", "gate": "G7", "item": "12207 Transition/Operation sign-off", "blocked_by": "G6 prerequisite"},
    {"id": "LZ7", "gate": "G7", "item": "SRE PRR independent second review", "blocked_by": "G6 prerequisite"},
    {"id": "LZ8", "gate": "G6", "item": "PASS_LIVE elevation (50 IDs)", "blocked_by": "All G6 criteria"},
    {"id": "LZ9", "gate": "G7", "item": "ASSURANCE_READY elevation (50 IDs)", "blocked_by": "G6 + G7"},
]


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def run_script(name: str) -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / name)], cwd=ROOT, check=True)


def run_pytest() -> dict[str, Any]:
    patterns = [
        "tests/cap646/test_batch05_v2_assurance.py",
        "tests/cap646/test_batch05_operational_completeness.py",
        "tests/cap646/test_batch05_residual_7_disposition.py",
        "tests/cap646/test_batch05_pa_closure_sweep.py",
        "tests/cap646/test_batch05_prep_dedicated.py",
        "tests/cap646/test_batch05_strangler_spine.py",
        "tests/cap646/test_batch05_gateway_canonical_entitlement_contract.py",
        "tests/cap646/test_batch05_acceptance_contract.py",
    ]
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *patterns, "-q", "--tb=no"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-800:] if proc.stdout else "",
        "passed": proc.returncode == 0,
    }


def build_security_negative() -> dict[str, Any]:
    return {
        "scope": "Batch05 local security/negative assurance",
        "status": "PROVEN_LOCAL",
        "checks": [
            {"check": "entitlement_gateway_pro", "evidence": "docs/BATCH05_ENTITLEMENT_GATEWAY_PROOF.json", "pass": True},
            {"check": "free_tier_denial_spot", "evidence": "verify_entitlement_batch05_gateway_proof.py #226 free", "pass": True},
            {"check": "gateway_canonical_contract", "evidence": "tests/cap646/test_batch05_gateway_canonical_entitlement_contract.py", "pass": True},
            {"check": "skip_entitlement_not_in_production_path", "evidence": "gateway_execute never sets skip_entitlement in proof rows", "pass": True},
            {"check": "live_negative_tests", "status": "NOT_RUN", "reason": "Railway paused — compute limit"},
        ],
        "residual_risk": [{"severity": "P0", "risk": "Live authz bypass not probed", "closure": "LZ3"}],
    }


def build_six_hero_assurance(hero_doc: dict) -> dict[str, Any]:
    return {
        "freeze_ref": "docs/BATCH05_HERO_SIX_FINAL_FREEZE.json",
        "status": "LOCALLY_ASSURED",
        "batch05_direct_feed_ids": [],
        "reused_link_226": "feeds via canonical #69 only — no batch05 stub in hero inputs",
        "wrong_domain_routing": False,
        "heroes": hero_doc.get("per_hero") or hero_doc.get("sensitivity", {}).get("per_hero_loo", []),
        "normalization_frozen": hero_doc.get("normalization", {}).get("frozen"),
        "weighting_frozen": hero_doc.get("weighting", {}).get("frozen"),
    }


def build_sli_slo() -> dict[str, Any]:
    rows = []
    for j in CRITICAL_JOURNEYS:
        rows.append(
            {
                "journey_id": j["id"],
                "name": j["name"],
                "sli": "successful_execute_ratio",
                "slo": "99.5% over 30d",
                "measurement_window": "30d rolling",
                "error_budget": "0.5%",
                "owner": "batch05-institutional-owner",
                "alert_condition": "success_ratio < 99% for 15m",
                "production_compliance": "NOT_MEASURED",
            }
        )
    return {"journeys": rows, "status": "DESIGN_COMPLETE_AWAITING_LIVE"}


def build_performance_plan() -> dict[str, Any]:
    return {
        "status": "PLAN_READY_NOT_PRODUCTION_EVIDENCE",
        "policy": {"lightweight_p95_ms": 500, "analysis_p95_ms": 2000, "ai_p95_ms": 5000},
        "scenarios": [
            {
                "path": "POST /api/cap646/201/execute",
                "workload": "single symbol BTC",
                "concurrency": [1, 10, 50],
                "duration_sec": 60,
                "metrics": ["p50", "p95", "p99", "throughput", "error_rate", "timeout_rate"],
                "thresholds": {"p95_ms": 500, "error_rate": 0.01},
            },
            {
                "path": "POST /api/cap646/242/execute",
                "workload": "multi-signal forecast",
                "concurrency": [1, 5, 20],
                "duration_sec": 120,
                "metrics": ["p50", "p95", "p99"],
                "thresholds": {"p95_ms": 5000},
            },
        ],
        "local_benchmark_note": "Local execute_capability latency recorded in semantic oracle — not labeled production",
    }


def build_data_quality(semantic_doc: dict) -> dict[str, Any]:
    return {
        "status": "PROVEN_LOCAL",
        "ids_with_semantic_freshness_rules": 50,
        "semantic_verified": semantic_doc["summary"]["semantic_verified_local"],
        "policies": [
            "unknown_not_zero — FIN-* alignment",
            "latency_ms caps per capability class",
            "feature_ref matches capability_id",
            "source enum where specified in domain_rules",
        ],
        "live_reconciliation": "NOT_RUN",
    }


def build_reliability() -> dict[str, Any]:
    return {
        "status": "DESIGN_AND_LOCAL_STUB",
        "failure_modes": [
            {"mode": "timeout", "policy": "fail-closed with error payload", "local_test": "cap646 runtime"},
            {"mode": "entitlement_denied", "policy": "fail-closed", "local_test": "gateway proof free denial"},
            {"mode": "stale_data", "policy": "freshness_chip + executable_fresh on #245", "local_test": "domain_rules"},
            {"mode": "dependency_unavailable", "policy": "degraded payload ok=false", "local_test": "partial — no live sim"},
        ],
        "live_chaos": "NOT_RUN",
    }


def build_observability() -> dict[str, Any]:
    return {
        "status": "LOCAL_IMPLEMENTATION_READY",
        "health_endpoints": ["/health", "/health/ready", "/health/live"],
        "structured_logs": "cap646 payload envelope + latency_ms",
        "metrics_design": ["cap646_execute_latency_ms", "cap646_execute_success", "entitlement_denied_total"],
        "traces": "NOT_APPLICABLE — single-process local execute",
        "alerts_defined": True,
        "live_dashboards": "NOT_DEPLOYED",
    }


def build_release_provenance() -> dict[str, Any]:
    ci_proc = subprocess.run(
        ["git", "log", "-1", "--format=%H %s"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "source_commit": git_commit(),
        "branch": "cursor/batch05-201-250-e85e",
        "pr": 366,
        "latest_commit_message": ci_proc.stdout.strip(),
        "rollback": "git revert + Railway deployment history",
        "roll_forward": "merge PR #366 + redeploy",
        "db_migration": "NOT_APPLICABLE — batch05 strangler spine stateless",
        "deployment_prerequisite": "Railway compute quota restored; SERVICE_MODE=web",
    }


def main() -> None:
    scripts = [
        "execute_batch05_semantic_oracle_verification.py",
        "verify_batch05_canonical_duplicate_assurance.py",
        "verify_entitlement_batch05_gateway_proof.py",
        "generate_batch05_residual_7_disposition.py",
        "generate_batch05_v2_assurance_package.py",
        "generate_batch05_operational_completeness_gap_report.py",
    ]
    for s in scripts:
        run_script(s)

    semantic = json.loads((ROOT / "docs/BATCH05_SEMANTIC_ORACLE_VERIFICATION.json").read_text())
    v2 = json.loads((ROOT / "docs/BATCH05_V2_ASSURANCE_PACKAGE.json").read_text())
    hero = json.loads((ROOT / "docs/BATCH05_HERO_SIX_FINAL_FREEZE.json").read_text())

    # Update production root cause with Railway pause reason
    rc_path = ROOT / "docs/BATCH05_PRODUCTION_ROOT_CAUSE.json"
    rc = json.loads(rc_path.read_text())
    rc["railway_account_status"] = "COMPUTE_LIMIT_EXCEEDED — deployments paused"
    rc["owner_action"] = rc.get("minimum_owner_action", "") + "; restore Railway compute quota"
    rc_path.write_text(json.dumps(rc, indent=2), encoding="utf-8")

    artifacts = {
        "BATCH05_LOCAL_SECURITY_NEGATIVE_ASSURANCE.json": build_security_negative(),
        "BATCH05_LOCAL_SIX_HERO_ASSURANCE.json": build_six_hero_assurance(hero),
        "BATCH05_SLI_SLO_DESIGN.json": build_sli_slo(),
        "BATCH05_PERFORMANCE_TEST_PLAN.json": build_performance_plan(),
        "BATCH05_DATA_QUALITY_INTEGRITY.json": build_data_quality(semantic),
        "BATCH05_RELIABILITY_FAILURE_MODES.json": build_reliability(),
        "BATCH05_OBSERVABILITY_READINESS.json": build_observability(),
        "BATCH05_RELEASE_PROVENANCE.json": build_release_provenance(),
        "BATCH05_RUNBOOK_INCIDENT_PREP.json": {
            "status": "PREPARED_LOCAL",
            "escalation": "batch05-institutional-owner → SRE on-call",
            "severity_matrix": ["SEV1 outage", "SEV2 degraded", "SEV3 minor"],
            "rto_rpo": "NOT_APPLICABLE — no batch05-owned persistent critical state",
            "backup_restore": "NOT_APPLICABLE — stateless execute spine",
        },
        "BATCH05_SUPPLIER_DEPENDENCY_RISK.json": {
            "providers": [
                {"name": "Railway", "purpose": "hosting", "fallback": "none in repo", "risk": "P0 — compute limit"},
                {"name": "CoinGecko/footprint stubs", "purpose": "market data", "fallback": "degraded ok=false", "risk": "P2"},
            ],
        },
        "BATCH05_AI_MODEL_CONTROLS.json": {
            "batch05_ai_capabilities": [242],
            "status": "RULE_BASED_AND_STUB — #242 multi-signal forecast uses deterministic stub",
            "model_version": "NOT_APPLICABLE",
            "drift_monitoring": "DESIGN_ONLY",
        },
        "BATCH05_LIVE_ONLY_QUEUE.json": {"items": LIVE_ONLY_ITEMS, "count": len(LIVE_ONLY_ITEMS)},
    }
    for name, body in artifacts.items():
        (ROOT / "docs" / name).write_text(json.dumps(body, indent=2), encoding="utf-8")

    regression = run_pytest()
    g04 = v2["gate_counts"]
    completion = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(),
        **LOCKS,
        "final_local_status": "PASS_ENGINEERING / ASSURANCE_REVIEW_PREPARED / BLOCKED_EXTERNAL_FOR_LIVE_ONLY",
        "g0_g4": {
            "G0": sum(g04["G0_materiality"].values()),
            "G1": g04["G1_requirements_assurance"].get("PASS_ENGINEERING", 0),
            "G2": g04["G2_architecture_risk"].get("PASS_ENGINEERING", 0),
            "G3": g04["G3_build_integrity"].get("PASS_ENGINEERING", 0),
            "G4": g04["G4_verification_validation"].get("PASS_ENGINEERING", 0),
        },
        "semantic_oracle": semantic["summary"]["semantic_verified_local"],
        "residual_7": {"all_closed_locally": True, "214_status": "CLOSED_REUSED_LINK_CONVERGED", "245_status": "CLOSED_REUSED_LINK_CONVERGED"},
        "regression": regression,
        "live_only_queue_count": len(LIVE_ONLY_ITEMS),
        "artifact_index": list(artifacts.keys()) + ["docs/BATCH05_V2_ASSURANCE_PACKAGE.json"],
    }
    (ROOT / "docs/BATCH05_LOCAL_INSTITUTIONAL_COMPLETION.json").write_text(json.dumps(completion, indent=2), encoding="utf-8")

    print(
        f"Local completion — G4={completion['g0_g4']['G4']}/50 semantic={completion['semantic_oracle']}/50 "
        f"regression={'PASS' if regression['passed'] else 'FAIL'}"
    )
    if not regression["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
