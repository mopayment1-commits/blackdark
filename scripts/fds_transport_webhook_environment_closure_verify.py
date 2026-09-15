#!/usr/bin/env python3
"""FDS-09/14/19 + SDG-11/13 closure verifier."""

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

OUT = ROOT / "FDS_TRANSPORT_WEBHOOK_ENVIRONMENT_CLOSURE_EVIDENCE.json"
SPEC = ROOT / "docs" / "BLACKDARK_FINANCIAL_DATA_SECURITY_IMPLEMENTATION_SPEC_2026_FINAL.md"
PREV = [
    ROOT / "scripts" / "fds_secrets_crypto_audit_identity_closure_verify.py",
    ROOT / "scripts" / "fds_privileged_identity_authorization_closure_verify.py",
    ROOT / "scripts" / "fds_security_governance_data_boundary_closure_verify.py",
]

SCOPE_FDS = ("FDS-09", "FDS-14", "FDS-19")
SCOPE_SDG = ("SDG-11", "SDG-13")

CANONICAL_OWNERS = {
    "transport": "transport_webhook_env/transport.py",
    "environment": "transport_webhook_env/environment.py",
    "webhook_lifecycle": "transport_webhook_env/webhook_lifecycle.py",
    "access_audit": "transport_webhook_env/access_audit.py",
    "security_middleware": "security_middleware.py",
    "billing_webhooks": "api/routers/billing.py",
    "stripe_webhook": "dashboard.py",
    "production_guard": "production_guard.py",
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
            "tests/test_fds_transport_webhook_environment.py",
            "-q",
            "-k",
            "not closure_script_produces_evidence",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": "python -m pytest tests/test_fds_transport_webhook_environment.py -q",
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "stdout_tail": proc.stdout[-2500:],
        "stderr_tail": proc.stderr[-1000:],
    }


def _run_prev(script: Path) -> dict[str, Any]:
    if not script.is_file():
        return {"passed": False, "error": "missing"}
    proc = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    return {"command": f"python {script.name}", "exit_code": proc.returncode, "passed": proc.returncode == 0}


def build_evidence() -> dict[str, Any]:
    from governance.fds_transport_webhook_environment import verify_fds_transport_webhook_environment_scope

    tests = _run_pytest()
    prev_results = {p.name: _run_prev(p) for p in PREV}
    evaluation = verify_fds_transport_webhook_environment_scope()
    gaps = evaluation.get("gaps", {})
    gap_total = sum(int(v) for v in gaps.values() if isinstance(v, int))
    controls = evaluation.get("controls", {})
    fully = sum(1 for c in SCOPE_FDS if controls.get(c, {}).get("verified"))
    partial = sum(1 for c in SCOPE_FDS if controls.get(c) and not controls[c].get("verified"))
    not_impl = len(SCOPE_FDS) - fully - partial
    locally_buildable = gap_total if not evaluation.get("scope_verified") else 0
    prev_failures = sum(int(not r.get("passed")) for r in prev_results.values())
    regression_failures = prev_failures + int(not tests.get("passed"))
    prod_pending = len(evaluation.get("production_validation_pending") or [])
    all_ok = (
        tests.get("passed")
        and prev_failures == 0
        and evaluation.get("scope_verified")
        and gap_total == 0
        and fully == len(SCOPE_FDS)
        and locally_buildable == 0
        and regression_failures == 0
    )
    if all_ok and prod_pending > 0:
        verdict = "FDS_TRANSPORT_WEBHOOK_ENVIRONMENT_CLOSED_WITH_PRODUCTION_VALIDATION_PENDING"
    elif all_ok:
        verdict = "FDS_TRANSPORT_WEBHOOK_ENVIRONMENT_CLOSED"
    else:
        verdict = "FDS_TRANSPORT_WEBHOOK_ENVIRONMENT_NOT_CLOSED"
    return {
        "verdict": verdict,
        "generated_at": datetime.now(UTC).isoformat(),
        "governing_spec": {"path": str(SPEC.relative_to(ROOT)), "sha256": _sha256_file(SPEC)},
        "git": {"base_sha": _git_sha(), "implementation_sha": _git_sha()},
        "scope": {"fds_controls": list(SCOPE_FDS), "sdg_controls": list(SCOPE_SDG)},
        "canonical_owners": CANONICAL_OWNERS,
        "tests": tests,
        "previous_phase_regressions": prev_results,
        "evaluation": evaluation,
        "local_gaps": [] if gap_total == 0 else [{"counter": k, "value": v} for k, v in gaps.items() if v],
        "production_validation_pending": evaluation.get("production_validation_pending", []),
        "summary": {
            "fds_controls_in_scope": len(SCOPE_FDS),
            "fully_implemented_verified_local": fully,
            "partial_local": partial,
            "not_implemented_local": not_impl,
            "locally_buildable_remaining": locally_buildable,
            "production_validation_pending": prod_pending,
            "previous_fds_phase_regression_failures": prev_failures,
            "regression_failures": regression_failures,
            **gaps,
        },
    }


def main() -> int:
    evidence = build_evidence()
    OUT.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": evidence["verdict"], "artifact": OUT.name}, indent=2))
    closed = evidence["verdict"].startswith("FDS_TRANSPORT_WEBHOOK_ENVIRONMENT_CLOSED")
    return 0 if closed else 1


if __name__ == "__main__":
    raise SystemExit(main())
