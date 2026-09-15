#!/usr/bin/env python3
"""FDS production / external assurance boundary verifier."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "FDS_PRODUCTION_EXTERNAL_ASSURANCE_BOUNDARY.json"
SPEC = ROOT / "docs" / "BLACKDARK_FINANCIAL_DATA_SECURITY_IMPLEMENTATION_SPEC_2026_FINAL.md"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "missing"


def _git_sha() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def _run_pytest() -> dict[str, Any]:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_fds_production_external_assurance_boundary.py",
            "-q",
            "-k",
            "not closure_script_produces_evidence",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": "python -m pytest tests/test_fds_production_external_assurance_boundary.py -q",
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "stdout_tail": proc.stdout[-2500:],
        "stderr_tail": proc.stderr[-1000:],
    }


def build_evidence() -> dict[str, Any]:
    from governance.fds_production_external_assurance_boundary import verify_fds_production_external_assurance_boundary

    tests = _run_pytest()
    evaluation = verify_fds_production_external_assurance_boundary()
    summary = evaluation.get("summary", {})
    regression_failures = int(summary.get("REGRESSION_FAILURES", 0)) + int(not tests.get("passed"))
    summary["REGRESSION_FAILURES"] = regression_failures

    boundary_ok = (
        evaluation.get("verdict") == "FDS_EXTERNAL_ASSURANCE_BOUNDARY_CLOSED"
        and regression_failures == 0
        and tests.get("passed")
    )
    if not boundary_ok and evaluation.get("verdict") == "FDS_EXTERNAL_ASSURANCE_BOUNDARY_CLOSED":
        evaluation["verdict"] = "FDS_EXTERNAL_ASSURANCE_BOUNDARY_NOT_CLOSED"

    return {
        "verdict": evaluation["verdict"],
        "generated_at": datetime.now(UTC).isoformat(),
        "governing_spec": {"path": str(SPEC.relative_to(ROOT)), "sha256": _sha256_file(SPEC)},
        "git": {"current_head_sha": _git_sha()},
        "pending_external_production_items": evaluation.get("items", []),
        "fds04_applicability": evaluation.get("fds04_applicability"),
        "safe_probes": evaluation.get("safe_probes"),
        "misclassification_checks": evaluation.get("misclassification_checks"),
        "previous_verifier_results": evaluation.get("previous_closure_verifiers"),
        "tests": tests,
        "summary": summary,
    }


def main() -> int:
    evidence = build_evidence()
    OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": evidence["verdict"], "artifact": OUT.name}, indent=2))
    return 0 if evidence["verdict"] == "FDS_EXTERNAL_ASSURANCE_BOUNDARY_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
