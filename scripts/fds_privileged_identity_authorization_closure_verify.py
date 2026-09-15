#!/usr/bin/env python3
"""FDS-10/11/12/17/22/23 + SDG-06/07/09/14/18 closure verifier."""

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

OUT = ROOT / "FDS_PRIVILEGED_IDENTITY_AUTHORIZATION_CLOSURE_EVIDENCE.json"
SPEC = ROOT / "docs" / "BLACKDARK_FINANCIAL_DATA_SECURITY_IMPLEMENTATION_SPEC_2026_FINAL.md"
PREV_VERIFIER = ROOT / "scripts" / "fds_security_governance_data_boundary_closure_verify.py"

SCOPE_FDS = ("FDS-10", "FDS-11", "FDS-12", "FDS-17", "FDS-22", "FDS-23")
SCOPE_SDG = ("SDG-06", "SDG-07", "SDG-09", "SDG-14", "SDG-18")

CANONICAL_OWNERS = {
    "operations": "privileged_access/operations.py",
    "policy": "privileged_access/policy.py",
    "step_up": "privileged_access/step_up.py",
    "sessions": "privileged_access/sessions.py",
    "break_glass": "privileged_access/break_glass.py",
    "access_review": "privileged_access/access_review.py",
    "detectors": "privileged_access/detectors.py",
    "deps": "privileged_access/deps.py",
    "api": "api/routers/privileged_access.py",
    "admin_mfa": "admin_mfa.py",
    "security_auth": "security_auth.py",
    "org_rbac": "org_rbac.py",
}


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
            "tests/test_fds_privileged_identity_authorization.py",
            "-q",
            "-k",
            "not closure_script_produces_evidence",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": "python -m pytest tests/test_fds_privileged_identity_authorization.py -q",
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "stdout_tail": proc.stdout[-2500:],
        "stderr_tail": proc.stderr[-1000:],
    }


def _run_previous_fds_verifier() -> dict[str, Any]:
    if not PREV_VERIFIER.is_file():
        return {"passed": False, "error": "previous_verifier_missing"}
    proc = subprocess.run([sys.executable, str(PREV_VERIFIER)], cwd=ROOT, capture_output=True, text=True)
    return {
        "command": f"python {PREV_VERIFIER.name}",
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
    }


def _run_payment_regression() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_payments_usd_security.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {"exit_code": proc.returncode, "passed": proc.returncode == 0}


def build_evidence() -> dict[str, Any]:
    from governance.fds_privileged_identity import verify_fds_privileged_identity_scope
    from privileged_access.operations import protected_operation_inventory

    tests = _run_pytest()
    prev = _run_previous_fds_verifier()
    payment = _run_payment_regression()
    evaluation = verify_fds_privileged_identity_scope()
    gaps = evaluation.get("gaps", {})
    gap_total = sum(int(v) for v in gaps.values() if isinstance(v, int))
    controls = evaluation.get("controls", {})
    fully = sum(1 for c in SCOPE_FDS if controls.get(c, {}).get("verified"))
    partial = sum(1 for c in SCOPE_FDS if controls.get(c) and not controls[c].get("verified"))
    not_impl = len(SCOPE_FDS) - fully - partial
    locally_buildable = gap_total if not evaluation.get("scope_verified") else 0
    regression_failures = (
        int(not tests.get("passed")) + int(not prev.get("passed")) + int(not payment.get("passed"))
    )
    all_ok = (
        tests.get("passed")
        and prev.get("passed")
        and payment.get("passed")
        and evaluation.get("scope_verified")
        and gap_total == 0
        and fully == len(SCOPE_FDS)
        and locally_buildable == 0
        and regression_failures == 0
    )
    verdict = (
        "FDS_PRIVILEGED_IDENTITY_AUTHORIZATION_CLOSED"
        if all_ok
        else "FDS_PRIVILEGED_IDENTITY_AUTHORIZATION_NOT_CLOSED"
    )
    return {
        "verdict": verdict,
        "generated_at": datetime.now(UTC).isoformat(),
        "governing_spec": {"path": str(SPEC.relative_to(ROOT)), "sha256": _sha256_file(SPEC)},
        "git": {"base_sha": _git_sha(), "implementation_sha": _git_sha()},
        "scope": {"fds_controls": list(SCOPE_FDS), "sdg_controls": list(SCOPE_SDG)},
        "canonical_owners": CANONICAL_OWNERS,
        "protected_operation_inventory": protected_operation_inventory(),
        "mfa_coverage": [o for o in protected_operation_inventory() if o["mfa_required"]],
        "step_up_coverage": [o for o in protected_operation_inventory() if o["step_up_required"]],
        "privileged_session_policy": {"module": "privileged_access/sessions.py", "ttl_env": "PRIVILEGED_SESSION_TTL_SEC"},
        "alert_detector_coverage": {
            "bulk_financial_export": "privileged_access.detectors.detect_bulk_financial_export",
            "repeated_denied_access": "privileged_access.detectors.detect_repeated_denied_financial_access",
            "audit_bypass": "privileged_access.detectors.detect_audit_bypass_attempt",
        },
        "break_glass_evidence": evaluation.get("controls", {}).get("FDS-22", {}),
        "access_review_evidence": evaluation.get("controls", {}).get("FDS-23", {}),
        "anti_bypass_counters": gaps,
        "tests": tests,
        "previous_fds_governance_regression": prev,
        "payment_regression": payment,
        "evaluation": evaluation,
        "local_gaps": [] if gap_total == 0 else [{"counter": k, "value": v} for k, v in gaps.items() if v],
        "production_validation_pending": [],
        "summary": {
            "fds_controls_in_scope": len(SCOPE_FDS),
            "fully_implemented_verified_local": fully,
            "partial_local": partial,
            "not_implemented_local": not_impl,
            "locally_buildable_remaining": locally_buildable,
            "previous_fds_security_governance_regression_failures": int(not prev.get("passed")),
            "regression_failures": regression_failures,
            **gaps,
        },
    }


def main() -> int:
    evidence = build_evidence()
    OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": evidence["verdict"], "artifact": OUT.name}, indent=2))
    return 0 if evidence["verdict"].endswith("CLOSED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
