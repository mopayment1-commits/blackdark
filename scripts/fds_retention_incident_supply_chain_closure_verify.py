#!/usr/bin/env python3
"""FDS-20/21 + SDG-15/16/17 closure verifier."""

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

OUT = ROOT / "FDS_RETENTION_INCIDENT_SUPPLY_CHAIN_CLOSURE_EVIDENCE.json"
SPEC = ROOT / "docs" / "BLACKDARK_FINANCIAL_DATA_SECURITY_IMPLEMENTATION_SPEC_2026_FINAL.md"
PREV = [
    ROOT / "scripts" / "fds_transport_webhook_environment_closure_verify.py",
    ROOT / "scripts" / "fds_secrets_crypto_audit_identity_closure_verify.py",
    ROOT / "scripts" / "fds_privileged_identity_authorization_closure_verify.py",
    ROOT / "scripts" / "fds_security_governance_data_boundary_closure_verify.py",
]

SCOPE_FDS = ("FDS-20", "FDS-21")
SCOPE_SDG = ("SDG-15", "SDG-16", "SDG-17")

CANONICAL_OWNERS = {
    "retention_policy": "fds_retention_incident/retention_policy.py",
    "account_closure": "fds_retention_incident/account_closure.py",
    "backup_lifecycle": "fds_retention_incident/backup_lifecycle.py",
    "incident_playbook": "fds_retention_incident/incident_playbook.py",
    "incident_drill": "fds_retention_incident/incident_drill.py",
    "supply_chain": "fds_retention_incident/supply_chain.py",
    "payment_script_inventory": "fds_retention_incident/payment_script_inventory.py",
    "gdpr_service": "gdpr_service.py",
    "backup_script": "scripts/backup_postgres.py",
    "market_retention": "data_governance/retention.py",
    "incident_runbook": "docs/ops/INCIDENT_RESPONSE.md",
    "financial_playbook": "docs/ops/FINANCIAL_DATA_INCIDENT_PLAYBOOK.md",
    "sca_ci": ".github/workflows/security.yml",
    "sbom_generator": "scripts/generate_sbom.py",
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
            "tests/test_fds_retention_incident_supply_chain.py",
            "-q",
            "-k",
            "not closure_script_produces_evidence",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": "python -m pytest tests/test_fds_retention_incident_supply_chain.py -q",
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
    from fds_retention_incident.payment_script_inventory import payment_script_inventory
    from fds_retention_incident.retention_policy import financial_retention_matrix
    from fds_retention_incident.supply_chain import sca_status, sbom_status
    from governance.fds_retention_incident_supply_chain import verify_fds_retention_incident_supply_chain_scope

    tests = _run_pytest()
    prev_results = {p.name: _run_prev(p) for p in PREV}
    evaluation = verify_fds_retention_incident_supply_chain_scope()
    gaps = evaluation.get("gaps", {})
    gap_total = sum(int(v) for v in gaps.values() if isinstance(v, int))
    controls = evaluation.get("controls", {})
    sdg = evaluation.get("sdg", {})
    fully = sum(1 for c in SCOPE_FDS if controls.get(c, {}).get("verified"))
    partial = sum(1 for c in SCOPE_FDS if controls.get(c) and not controls[c].get("verified"))
    not_impl = len(SCOPE_FDS) - fully - partial
    sdg_verified = sum(1 for s in SCOPE_SDG if sdg.get(s, {}).get("verified"))
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
        and sdg_verified == len(SCOPE_SDG)
        and locally_buildable == 0
        and regression_failures == 0
    )
    if all_ok and prod_pending > 0:
        verdict = "FDS_RETENTION_INCIDENT_SUPPLY_CHAIN_CLOSED_WITH_PRODUCTION_VALIDATION_PENDING"
    elif all_ok:
        verdict = "FDS_RETENTION_INCIDENT_SUPPLY_CHAIN_CLOSED"
    else:
        verdict = "FDS_RETENTION_INCIDENT_SUPPLY_CHAIN_NOT_CLOSED"

    from fds_retention_incident.incident_drill import run_all_drills

    drill = run_all_drills()
    sca = sca_status()
    sbom = sbom_status()

    return {
        "verdict": verdict,
        "generated_at": datetime.now(UTC).isoformat(),
        "governing_spec": {"path": str(SPEC.relative_to(ROOT)), "sha256": _sha256_file(SPEC)},
        "git": {"base_sha": _git_sha(), "implementation_sha": _git_sha()},
        "scope": {"fds_controls": list(SCOPE_FDS), "sdg_controls": list(SCOPE_SDG)},
        "canonical_owners": CANONICAL_OWNERS,
        "retention_matrix": financial_retention_matrix(),
        "deletion_revocation_paths": {
            "account_closure": "fds_retention_incident/account_closure.py",
            "credential_revoke": "secrets_crypto/lifecycle.py + account_closure.revoke_financial_credentials",
            "backup_expiry": "fds_retention_incident/backup_lifecycle.py",
        },
        "backup_lifecycle_evidence": evaluation.get("backup_lifecycle"),
        "incident_playbook_version": evaluation.get("incident_playbook", {}).get("playbook_version"),
        "drill_scenarios_results": drill,
        "supply_chain_controls": evaluation.get("supply_chain"),
        "sca_results": {"finding_count": sca.get("finding_count"), "tool": sca.get("tool")},
        "sbom_results": sbom,
        "payment_script_inventory": payment_script_inventory(),
        "machine_counters": gaps,
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
    closed = evidence["verdict"].startswith("FDS_RETENTION_INCIDENT_SUPPLY_CHAIN_CLOSED")
    return 0 if closed else 1


if __name__ == "__main__":
    raise SystemExit(main())
