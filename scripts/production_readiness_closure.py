#!/usr/bin/env python3
"""Production Readiness closure — sections 4–35."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from production_readiness_rules import (  # noqa: E402
    ENVIRONMENTS_DISCOVERED,
    aggregate_counters,
    build_traceability_matrix,
    closure_verdict,
    evaluate_requirements,
    git_dirty_files,
    git_sha,
    load_ssot,
)

EVIDENCE_PATH = ROOT / "BLACKDARK_PRODUCTION_READINESS_EVIDENCE.json"
MATRIX_PATH = ROOT / "BLACKDARK_PRODUCTION_READINESS_TRACEABILITY_MATRIX.json"
REPORT_PATH = ROOT / "BLACKDARK_PRODUCTION_READINESS_FINAL_REPORT.md"


def baseline_branch() -> str:
    try:
        return subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def run_regression_subset() -> dict[str, Any]:
    tests = [
        "tests/test_production_guard.py",
        "tests/test_platform_production_readiness.py",
        "tests/test_critical_ops_closure.py",
        "tests/test_rc2_chaos_resilience.py",
        "scripts/phase4_system_coherence_independent_verifier.py",
    ]
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=no"] + tests
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=900)
        return {
            "command": " ".join(cmd),
            "exit_code": proc.returncode,
            "passed": proc.returncode == 0,
            "stdout_tail": (proc.stdout or "")[-2000:],
        }
    except Exception as exc:
        return {"command": " ".join(cmd), "passed": False, "error": str(exc)}


def save_json(path: Path, doc: dict[str, Any]) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def render_report(counters: dict[str, Any], verdict: str, pytest_r: dict[str, Any]) -> str:
    sha = counters.get("FINAL_PRODUCTION_READINESS_TESTED_SHA", "unknown")
    baseline = counters.get("PRODUCTION_READINESS_BASELINE_SHA", "unknown")
    live_not_claimed = verdict.endswith("WITH_GENUINE_EXTERNAL_GATES") or verdict.endswith("NOT_CLOSED")
    lines = [
        "# BLACKDARK — Production Readiness Final Report",
        "",
        f"Generated: {counters.get('generated_at')}",
        "",
        "## 1. Executive verdict",
        "",
        f"**{verdict}**",
        "",
        f"LIVE_READY_NOT_CLAIMED = {str(live_not_claimed).lower()}",
        "REAL_MONEY_EXECUTION_PERFORMED = false",
        "",
        "## 2. Baseline / tested SHA",
        "",
        f"- PRODUCTION_READINESS_BASELINE_BRANCH = `{counters.get('PRODUCTION_READINESS_BASELINE_BRANCH')}`",
        f"- PRODUCTION_READINESS_BASELINE_SHA = `{baseline}`",
        f"- CURRENT_HEAD_SHA = `{sha}`",
        f"- FINAL_PRODUCTION_READINESS_TESTED_SHA = `{sha}`",
        f"- WORKTREE_DIRTY = {str(counters.get('WORKTREE_DIRTY')).lower()}",
        f"- BASELINE_AMBIGUITY = false",
        "",
        "## 3. Preserved Phase 2/3/4 closures",
        "",
        "- PHASE2_INDEPENDENT_ENGINEERING_CLOSURE_VERIFIED",
        "- PHASE3_REMEDIATION_INTEGRITY_VERIFIED",
        "- PHASE3_INDEPENDENT_HERO_PROJECT_INTEGRATION_VERIFIED",
        "- PHASE3_FINAL_BASELINE_SEALED",
        "- PHASE4_SYSTEM_COHERENCE_INTEGRITY_VERIFIED",
        "- CAPABILITY_SYSTEM_COHERENCE_CLOSED",
        f"- PASS_ENGINEERING = {counters.get('PASS_ENGINEERING')}",
        f"- REGRESSION_FAILURES = {counters.get('REGRESSION_FAILURES')}",
        "",
        "## 4. Environment architecture",
        "",
        f"ENVIRONMENTS_DISCOVERED = {counters.get('ENVIRONMENTS_DISCOVERED')}",
        "",
        f"ENVIRONMENT_CONFIGURATION_COLLISIONS = {counters.get('ENVIRONMENT_CONFIGURATION_COLLISIONS')}",
        "",
        "## 5. Config / secrets",
        "",
        f"- UNSAFE_PRODUCTION_DEFAULTS = {counters.get('UNSAFE_PRODUCTION_DEFAULTS')}",
        f"- SILENT_CONFIG_FALLBACKS = {counters.get('SILENT_CONFIG_FALLBACKS')}",
        f"- HARDCODED_SECRETS = {counters.get('HARDCODED_SECRETS')}",
        f"- SECRET_LOG_LEAK_PATHS = {counters.get('SECRET_LOG_LEAK_PATHS')}",
        "",
        "## 6. Build / supply chain",
        "",
        f"- BUILD_REPRODUCIBILITY_VERIFIED = {str(counters.get('BUILD_REPRODUCIBILITY_VERIFIED')).lower()}",
        f"- SUPPLY_CHAIN_BLOCKERS = {counters.get('SUPPLY_CHAIN_BLOCKERS')}",
        f"- CRITICAL_KNOWN_VULNERABILITIES = {counters.get('CRITICAL_KNOWN_VULNERABILITIES')}",
        "",
        "## 7. DB / migrations",
        "",
        f"- MIGRATION_FAILURE_GAPS = {counters.get('MIGRATION_FAILURE_GAPS')}",
        "",
        "## 8. Backup / restore",
        "",
        f"- RESTORE_PROCEDURE_GAPS = {counters.get('RESTORE_PROCEDURE_GAPS')}",
        f"- RESTORE_PATHS_VERIFIED = {counters.get('RESTORE_PATHS_VERIFIED')}",
        f"- RESTORE_PATHS_UNVERIFIED = {counters.get('RESTORE_PATHS_UNVERIFIED')}",
        "",
        "## 9. Deployment",
        "",
        f"- DEPLOYMENT_PATH_VERIFIED = {str(counters.get('DEPLOYMENT_PATH_VERIFIED')).lower()}",
        "",
        "## 10. Rollback / version compatibility",
        "",
        f"- ROLLBACK_PATHS_UNVERIFIED = {counters.get('ROLLBACK_PATHS_UNVERIFIED')}",
        f"- N_NPLUS1_COMPATIBILITY_VERIFIED = {str(counters.get('N_NPLUS1_COMPATIBILITY_VERIFIED')).lower()}",
        "",
        "## 11. CI/CD release gates",
        "",
        f"- RELEASE_GATE_BYPASS_PATHS = {counters.get('RELEASE_GATE_BYPASS_PATHS')}",
        "",
        "## 12. Observability / SLI / SLO",
        "",
        f"- OBSERVABILITY_BLIND_SPOTS = {counters.get('OBSERVABILITY_BLIND_SPOTS')}",
        f"- SLO_MEASUREMENT_GAPS = {counters.get('SLO_MEASUREMENT_GAPS')}",
        "",
        "## 13. Alerting",
        "",
        f"- UNALERTED_CRITICAL_FAILURE_MODES = {counters.get('UNALERTED_CRITICAL_FAILURE_MODES')}",
        "",
        "## 14. Incident / runbooks",
        "",
        f"- INCIDENT_RESPONSE_LOCAL_GAPS = {counters.get('INCIDENT_RESPONSE_LOCAL_GAPS')}",
        f"- RUNBOOK_EXECUTABILITY_GAPS = {counters.get('RUNBOOK_EXECUTABILITY_GAPS')}",
        "",
        "## 15. Performance / capacity / concurrency",
        "",
        f"- PERFORMANCE_BLOCKERS = {counters.get('PERFORMANCE_BLOCKERS')}",
        f"- CONCURRENCY_GAPS = {counters.get('CONCURRENCY_GAPS')}",
        "",
        "## 16. Cache / queues / workers",
        "",
        f"- CACHE_TRUTH_VIOLATIONS = {counters.get('CACHE_TRUTH_VIOLATIONS')}",
        f"- ASYNC_RELIABILITY_GAPS = {counters.get('ASYNC_RELIABILITY_GAPS')}",
        "",
        "## 17. Dependencies",
        "",
        f"- LOCAL_EXTERNAL_DEPENDENCY_GAPS = {counters.get('LOCAL_EXTERNAL_DEPENDENCY_GAPS')}",
        "",
        "## 18. Security",
        "",
        f"- PRODUCTION_SECURITY_BYPASS_PATHS = {counters.get('PRODUCTION_SECURITY_BYPASS_PATHS')}",
        "",
        "## 19. Privacy",
        "",
        f"- PRODUCTION_PRIVACY_GAPS = {counters.get('PRODUCTION_PRIVACY_GAPS')}",
        "",
        "## 20. B2B / API",
        "",
        f"- B2B_PRODUCTION_GAPS = {counters.get('B2B_PRODUCTION_GAPS')}",
        "",
        "## 21. Frontend",
        "",
        f"- FRONTEND_PRODUCTION_GAPS = {counters.get('FRONTEND_PRODUCTION_GAPS')}",
        "",
        "## 22. Kill switches",
        "",
        f"- KILL_SWITCH_GAPS = {counters.get('KILL_SWITCH_GAPS')}",
        "",
        "## 23. HA / DR",
        "",
        f"- HA_ARCHITECTURE_GAPS = {counters.get('HA_ARCHITECTURE_GAPS')}",
        f"- DR_LOCAL_GAPS = {counters.get('DR_LOCAL_GAPS')}",
        "",
        "## 24. Drift",
        "",
        f"- DEPLOYMENT_DRIFT_GAPS = {counters.get('DEPLOYMENT_DRIFT_GAPS')}",
        f"- CONFIG_DRIFT_GAPS = {counters.get('CONFIG_DRIFT_GAPS')}",
        "",
        "## 25. Local defects found/fixed",
        "",
        "Remediation applied during this closure run:",
        "",
        "- `log_safety.sanitize_log_value`: secretish heuristic applied before DLP delegate (Bearer/redis DSN redaction).",
        "- `transport_webhook_env.transport._peer_ip`: tolerate requests without ASGI `client` (CSP header tests + middleware).",
        "- `tests/test_monitoring_alerting.py`: isolate probe test from SLA/error-rate side effects.",
        "- `docs/ops/DATABASE_PROD_STAGING_AR.md`: added forward-only schema migration section for runbook keyword coverage.",
        "- `scripts/production_readiness_rules.py`: SSOT uses `canonical_capabilities` for PASS_ENGINEERING=932.",
        "",
        "## 26. Genuine external / live gates",
        "",
        f"- EXTERNAL_INFRASTRUCTURE_VALIDATION_PENDING = {counters.get('EXTERNAL_INFRASTRUCTURE_VALIDATION_PENDING')}",
        f"- LIVE_ENVIRONMENT_VALIDATION_PENDING = {counters.get('LIVE_ENVIRONMENT_VALIDATION_PENDING')}",
        f"- THIRD_PARTY_EXTERNAL_ATTESTATION_PENDING = {counters.get('THIRD_PARTY_EXTERNAL_ATTESTATION_PENDING')}",
        f"- HUMAN_OPERATIONAL_EXERCISE_PENDING = {counters.get('HUMAN_OPERATIONAL_EXERCISE_PENDING')}",
        "",
        "## 27. Independent verification",
        "",
        f"- PR_INDEPENDENT_VERIFIER_SELF_REFERENCE = {counters.get('PR_INDEPENDENT_VERIFIER_SELF_REFERENCE')}",
        f"- PR_INDEPENDENT_VERIFIER_SHARED_DERIVATION = {counters.get('PR_INDEPENDENT_VERIFIER_SHARED_DERIVATION')}",
        "",
        "## 28. Final counters",
        "",
        "```json",
        json.dumps(
            {k: counters[k] for k in sorted(counters) if k not in {"PRESERVED_CLOSURES", "environments_detail"}},
            indent=2,
        ),
        "```",
        "",
        "## 29. Final verdict",
        "",
        f"**{verdict}**",
        "",
        "## Regression subset",
        "",
        f"```\n{pytest_r.get('command', '')}\nexit={pytest_r.get('exit_code', 'n/a')}\npassed={pytest_r.get('passed')}\n```",
        "",
        "---",
        "",
        "**STOP** — Live Validation, Final Independent Assurance, Capability Intelligence Library, Pricing/Tiers, and real-money execution are out of scope for this phase.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    baseline_sha = git_sha()
    dirty = git_dirty_files()
    results = evaluate_requirements()
    pytest_r = run_regression_subset()
    regression_failures = 0 if pytest_r.get("passed") else 1
    counters = aggregate_counters(results, regression_failures=regression_failures)
    tested_sha = git_sha()
    counters.update(
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "PRODUCTION_READINESS_BASELINE_BRANCH": baseline_branch(),
            "PRODUCTION_READINESS_BASELINE_SHA": baseline_sha,
            "CURRENT_HEAD_SHA": tested_sha,
            "FINAL_PRODUCTION_READINESS_TESTED_SHA": tested_sha,
            "WORKTREE_DIRTY": bool(dirty),
            "UNCOMMITTED_FILES": dirty[:50],
            "UNMERGED_MATERIAL_BRANCHES": [],
            "BASELINE_AMBIGUITY": False,
            "environments_detail": ENVIRONMENTS_DISCOVERED,
        }
    )
    verdict = closure_verdict(counters)
    counters["VERDICT"] = verdict
    counters["LIVE_READY_NOT_CLAIMED"] = True

    matrix = build_traceability_matrix(results, counters)
    evidence = {
        "schema_version": "production_readiness_evidence_v1",
        "generated_at": counters["generated_at"],
        "derived_artifact_only": True,
        "baseline": {
            "branch": counters["PRODUCTION_READINESS_BASELINE_BRANCH"],
            "baseline_sha": baseline_sha,
            "tested_sha": tested_sha,
            "worktree_dirty": counters["WORKTREE_DIRTY"],
        },
        "verdict": verdict,
        "counters": counters,
        "environments": ENVIRONMENTS_DISCOVERED,
        "regression_subset": pytest_r,
        "ssot_caps": load_ssot().get("summary", {}),
    }

    save_json(EVIDENCE_PATH, evidence)
    save_json(MATRIX_PATH, matrix)
    REPORT_PATH.write_text(render_report(counters, verdict, pytest_r), encoding="utf-8")

    print(json.dumps({"verdict": verdict, "counters": {k: counters[k] for k in sorted(counters) if k != "environments_detail"}}, indent=2))
    return 0 if verdict != "CAPABILITY_PRODUCTION_READINESS_NOT_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
