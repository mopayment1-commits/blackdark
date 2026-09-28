#!/usr/bin/env python3
"""FDS-05/15/18/24/25 + SDG-01/08/10/12 closure verifier (evidence-derived)."""

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

OUT = ROOT / "FDS_SECURITY_GOVERNANCE_DATA_BOUNDARY_CLOSURE_EVIDENCE.json"
SPEC = ROOT / "docs" / "BLACKDARK_FINANCIAL_DATA_SECURITY_IMPLEMENTATION_SPEC_2026_FINAL.md"
BASE_SHA_FILE = ROOT / ".fds_closure_base_sha"

SCOPE_CONTROLS = ("FDS-05", "FDS-15", "FDS-18", "FDS-24", "FDS-25")
SCOPE_SDG = ("SDG-01", "SDG-08", "SDG-10", "SDG-12")

CANONICAL_OWNERS = {
    "classification": "financial_data/classification.py",
    "sink_policy": "financial_data/sink_policy.py",
    "dlp": "financial_data/dlp.py",
    "boundary": "financial_data/boundary.py",
    "scanner": "financial_data/scanner.py",
    "test_data_policy": "financial_data/test_data_policy.py",
    "log_safety": "log_safety.py",
    "secrets_scan": "scripts/secrets_hygiene_scan.py",
    "financial_scan": "scripts/financial_data_security_scan.py",
    "llm_wiring": "oracle_data_hub.py",
    "ai_oracle_wiring": "ai_oracle.py",
    "support_export": "gdpr_service.py",
    "analytics_export": "bigquery_export.py",
    "fds_catalog": "governance/fds_requirements.py",
}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "missing"


def _git_sha() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def _base_sha() -> str:
    if BASE_SHA_FILE.is_file():
        return BASE_SHA_FILE.read_text(encoding="utf-8").strip()
    return _git_sha()


def _run_pytest() -> dict[str, Any]:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_fds_security_governance_data_boundary.py",
            "-q",
            "-k",
            "not closure_script_produces_evidence",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    passed = proc.returncode == 0
    return {
        "command": "python -m pytest tests/test_fds_security_governance_data_boundary.py -q",
        "exit_code": proc.returncode,
        "passed": passed,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-1000:],
    }


def _run_payment_regression() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_payments_usd_security.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": "python -m pytest tests/test_payments_usd_security.py -q",
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
    }


def _run_scanner() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "scripts/financial_data_security_scan.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    report_path = ROOT / "FDS_FINANCIAL_DATA_SCAN_REPORT.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
    return {
        "command": "python scripts/financial_data_security_scan.py",
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "report": {
            "clean": report.get("clean"),
            "files_scanned": report.get("files_scanned"),
            "pan_finding_count": report.get("pan_finding_count"),
            "secret_finding_count": report.get("secret_finding_count"),
        },
    }


def _evaluate_controls(
    *,
    tests: dict[str, Any],
    scanner: dict[str, Any],
    payment: dict[str, Any],
) -> dict[str, Any]:
    from financial_data.classification import CLASS_POLICY_VERSION, FDSClass, class_definition
    from financial_data.sink_policy import policy_matrix
    from financial_data.test_data_policy import test_data_policy_status
    from governance.fds_data_boundary import verify_fds_data_boundary_scope

    runtime = verify_fds_data_boundary_scope()
    controls: dict[str, Any] = {}
    all_ok = True
    for cid in SCOPE_CONTROLS:
        ok = bool(runtime.get("controls", {}).get(cid, {}).get("verified"))
        controls[cid] = runtime.get("controls", {}).get(cid, {})
        if not ok:
            all_ok = False
    for sid in SCOPE_SDG:
        ok = bool(runtime.get("sdg", {}).get(sid, {}).get("verified"))
        controls[sid] = runtime.get("sdg", {}).get(sid, {})
        if not ok:
            all_ok = False
    if not tests.get("passed"):
        all_ok = False
    if not scanner.get("passed"):
        all_ok = False
    if not payment.get("passed"):
        all_ok = False
    gaps = runtime.get("gaps", {})
    gap_total = sum(int(v) for v in gaps.values() if isinstance(v, int))
    if gap_total > 0:
        all_ok = False
    return {
        "controls": controls,
        "all_scope_verified": all_ok,
        "classification_model_version": CLASS_POLICY_VERSION,
        "sink_policy_matrix": policy_matrix(),
        "class_definitions": {c.value: class_definition(c).reason for c in FDSClass if c != FDSClass.UNKNOWN},
        "test_data_policy": test_data_policy_status(),
        "gaps": gaps,
    }


def build_evidence() -> dict[str, Any]:
    base_sha = _base_sha()
    impl_sha = _git_sha()
    tests = _run_pytest()
    scanner = _run_scanner()
    payment = _run_payment_regression()
    evaluation = _evaluate_controls(tests=tests, scanner=scanner, payment=payment)
    verdict = "FDS_SECURITY_GOVERNANCE_DATA_BOUNDARY_CLOSED" if evaluation["all_scope_verified"] else "FDS_SECURITY_GOVERNANCE_DATA_BOUNDARY_NOT_CLOSED"
    return {
        "verdict": verdict,
        "generated_at": datetime.now(UTC).isoformat(),
        "governing_spec": {
            "path": str(SPEC.relative_to(ROOT)),
            "sha256": _sha256_file(SPEC),
        },
        "git": {"base_sha": base_sha, "implementation_sha": impl_sha},
        "scope": {"fds_controls": list(SCOPE_CONTROLS), "sdg_controls": list(SCOPE_SDG)},
        "canonical_owners": CANONICAL_OWNERS,
        "tests": tests,
        "scanner": scanner,
        "payment_regression": payment,
        "evaluation": evaluation,
        "summary": {
            "fds_controls_in_scope": len(SCOPE_CONTROLS),
            "fully_implemented_verified_local": sum(
                1 for c in SCOPE_CONTROLS if evaluation["controls"].get(c, {}).get("verified")
            ),
            "regression_failures": int(not tests.get("passed")) + int(not scanner.get("passed")) + int(not payment.get("passed")),
            **evaluation.get("gaps", {}),
        },
    }


def main() -> int:
    evidence = build_evidence()
    OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": evidence["verdict"], "artifact": str(OUT.name)}, indent=2))
    return 0 if evidence["verdict"].endswith("CLOSED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
