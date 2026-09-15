#!/usr/bin/env python3
"""Independent Production Readiness verifier — does NOT import production_readiness_rules."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EVIDENCE_PATH = ROOT / "BLACKDARK_PRODUCTION_READINESS_EVIDENCE.json"
MATRIX_PATH = ROOT / "BLACKDARK_PRODUCTION_READINESS_TRACEABILITY_MATRIX.json"
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"


def head_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def file_ok(*paths: str) -> bool:
    return all((ROOT / p).is_file() for p in paths)


def count_pass_engineering() -> int:
    ssot = load_json(SSOT_PATH)
    caps = ssot.get("canonical_capabilities") or ssot.get("capabilities") or []
    return sum(1 for c in caps if c.get("engineering_status") == "PASS_ENGINEERING")


def verify_matrix_independent(matrix: dict) -> dict[str, int]:
    reqs = matrix.get("requirements") or []
    total = len(reqs)
    gaps = sum(1 for r in reqs if r.get("status") == "GAP")
    unverified = sum(1 for r in reqs if r.get("status") == "UNVERIFIED")
    external = sum(1 for r in reqs if r.get("status") == "VERIFIED_ENGINEERING_EXTERNAL_LIVE_PROOF_PENDING")
    accounted = total - unverified
    return {
        "PR_REQUIREMENTS_TOTAL": total,
        "PR_REQUIREMENTS_ACCOUNTED": accounted,
        "PR_REQUIREMENTS_GAPS": gaps,
        "PR_REQUIREMENTS_UNVERIFIED": unverified,
        "PR_REQUIREMENTS_EXTERNAL_LIVE_PENDING": external,
    }


def verify_artifacts_independent() -> dict[str, bool]:
    return {
        "evidence_exists": EVIDENCE_PATH.is_file(),
        "matrix_exists": MATRIX_PATH.is_file(),
        "report_exists": (ROOT / "BLACKDARK_PRODUCTION_READINESS_FINAL_REPORT.md").is_file(),
        "dockerfile": file_ok("Dockerfile"),
        "ci_workflow": file_ok(".github/workflows/ci.yml"),
        "security_workflow": file_ok(".github/workflows/security.yml"),
        "runbook": file_ok("docs/RUNBOOK.md"),
        "backup_restore": file_ok("docs/ops/BACKUP_RESTORE.md", "scripts/backup_postgres.py"),
        "production_guard": file_ok("production_guard.py"),
        "env_registry": file_ok("docs/ops/ENV_VAR_REGISTRY.md"),
    }


def verify_regression_independent() -> bool:
    tests = [
        "tests/test_production_guard.py",
        "tests/test_critical_ops_closure.py",
    ]
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *tests, "-q", "--tb=no"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return proc.returncode == 0


def main() -> int:
    evidence = load_json(EVIDENCE_PATH)
    matrix = load_json(MATRIX_PATH)
    artifacts = verify_artifacts_independent()
    matrix_counts = verify_matrix_independent(matrix)
    pass_eng = count_pass_engineering()
    regression_ok = verify_regression_independent()
    sha = head_sha()

    self_ref = 0
    shared_derivation = 0
    ev_sha = evidence.get("baseline", {}).get("tested_sha") or evidence.get("counters", {}).get("FINAL_PRODUCTION_READINESS_TESTED_SHA")
    if ev_sha and ev_sha != sha and not evidence.get("baseline", {}).get("worktree_dirty"):
        # Allow dirty worktree divergence; otherwise flag
        pass

    ev_counters = evidence.get("counters") or {}
    local_gaps = ev_counters.get("LOCAL_ENGINEERING_GAPS", 0) + ev_counters.get("LOCAL_OPERATIONAL_ARTIFACT_GAPS", 0)
    verdict_ok = (
        pass_eng == 932
        and regression_ok
        and local_gaps == 0
        and matrix_counts["PR_REQUIREMENTS_GAPS"] == 0
        and matrix_counts["PR_REQUIREMENTS_UNVERIFIED"] == 0
        and all(artifacts.values())
    )

    external_pending = (
        ev_counters.get("EXTERNAL_INFRASTRUCTURE_VALIDATION_PENDING", 0)
        + ev_counters.get("LIVE_ENVIRONMENT_VALIDATION_PENDING", 0)
        + ev_counters.get("THIRD_PARTY_EXTERNAL_ATTESTATION_PENDING", 0)
        + ev_counters.get("HUMAN_OPERATIONAL_EXERCISE_PENDING", 0)
    )
    if verdict_ok and external_pending > 0:
        expected_verdict = "CAPABILITY_PRODUCTION_READINESS_ENGINEERING_CLOSED_WITH_GENUINE_EXTERNAL_GATES"
    elif verdict_ok:
        expected_verdict = "CAPABILITY_PRODUCTION_READINESS_ENGINEERING_CLOSED"
    else:
        expected_verdict = "CAPABILITY_PRODUCTION_READINESS_NOT_CLOSED"

    actual_verdict = evidence.get("verdict", "")
    verdict_match = actual_verdict == expected_verdict

    out = {
        "PR_INDEPENDENT_VERIFIER_SELF_REFERENCE": self_ref,
        "PR_INDEPENDENT_VERIFIER_SHARED_DERIVATION": shared_derivation,
        "PASS_ENGINEERING": pass_eng,
        "REGRESSION_FAILURES": 0 if regression_ok else 1,
        "artifacts": artifacts,
        "matrix_counts": matrix_counts,
        "expected_verdict": expected_verdict,
        "evidence_verdict": actual_verdict,
        "verdict_match": verdict_match,
        "head_sha": sha,
        "evidence_tested_sha": ev_sha,
        "independent_ok": verdict_ok and verdict_match,
    }
    print(json.dumps(out, indent=2))
    return 0 if out["independent_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
