"""Final FDS reconciliation — artifact-driven only."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_all_closure_artifacts_present():
    required = [
        "FDS_SECURITY_GOVERNANCE_DATA_BOUNDARY_CLOSURE_EVIDENCE.json",
        "FDS_PRIVILEGED_IDENTITY_AUTHORIZATION_CLOSURE_EVIDENCE.json",
        "FDS_SECRETS_CRYPTO_AUDIT_IDENTITY_CLOSURE_EVIDENCE.json",
        "FDS_TRANSPORT_WEBHOOK_ENVIRONMENT_CLOSURE_EVIDENCE.json",
        "FDS_RETENTION_INCIDENT_SUPPLY_CHAIN_CLOSURE_EVIDENCE.json",
        "FDS_PRODUCTION_EXTERNAL_ASSURANCE_BOUNDARY.json",
    ]
    for name in required:
        assert (ROOT / name).is_file(), name


def test_fds01_to_25_accounted():
    from governance.fds_full_spec_final_reconciliation import reconcile_fds_full_spec

    result = reconcile_fds_full_spec()
    assert result["summary"]["TOTAL_FDS_ACCEPTANCE_CONTROLS"] == 25
    assert result["summary"]["ACCOUNTED_FOR"] == 25
    assert len(result["fds_controls"]) == 25


def test_no_local_gaps_or_contradictions():
    from governance.fds_full_spec_final_reconciliation import reconcile_fds_full_spec

    s = reconcile_fds_full_spec()["summary"]
    assert s["PARTIALLY_IMPLEMENTED_LOCAL"] == 0
    assert s["UNIMPLEMENTED_LOCAL"] == 0
    assert s["UNVERIFIED_LOCAL"] == 0
    assert s["LOCALLY_BUILDABLE_REMAINING"] == 0
    assert s["SPEC_DETAIL_LOCAL_GAPS"] == 0
    assert s["UNACCOUNTED_SPEC_DETAIL_REQUIREMENTS"] == 0
    assert s["STALE_EVIDENCE"] == 0
    assert s["MISSING_IMPLEMENTATION_FROM_CURRENT_HEAD"] == 0
    assert s["EVIDENCE_CONTRADICTIONS"] == 0
    assert s["LOCAL_GAPS_HIDDEN_AS_EXTERNAL"] == 0


def test_fds04_not_applicable():
    from governance.fds_full_spec_final_reconciliation import reconcile_fds_full_spec

    controls = {c["control_id"]: c for c in reconcile_fds_full_spec()["fds_controls"]}
    assert controls["FDS-04"]["status"] == "NOT_CURRENTLY_APPLICABLE_WITH_EVIDENCE"


def test_sdg_details_accounted():
    from governance.fds_full_spec_final_reconciliation import reconcile_fds_full_spec

    sdg = reconcile_fds_full_spec()["sdg_detail_accounting"]
    assert sdg["unaccounted"] == []


def test_final_verdict_pending_external_only():
    from governance.fds_full_spec_final_reconciliation import reconcile_fds_full_spec

    result = reconcile_fds_full_spec()
    assert result["verdict"] == "FDS_FULL_SPEC_ENGINEERING_CLOSED_WITH_PRODUCTION_EXTERNAL_VALIDATION_PENDING"
    assert result["summary"]["PASS_FDS_ENGINEERING"] is True
    assert result["summary"]["PASS_PRODUCTION_NOT_CLAIMED"] is True


def test_reconciliation_script_produces_artifact():
    proc = subprocess.run(
        [sys.executable, "scripts/fds_full_spec_final_reconciliation_verify.py"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    evidence = json.loads((ROOT / "FDS_FULL_SPEC_FINAL_RECONCILIATION.json").read_text())
    assert evidence["verdict"].startswith("FDS_FULL_SPEC_ENGINEERING_CLOSED")
