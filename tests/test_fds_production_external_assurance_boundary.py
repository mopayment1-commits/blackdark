"""Production / external assurance boundary reconciliation tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

_REQUIRED_FIELDS = frozenset(
    {
        "item_id",
        "control_id",
        "requirement",
        "local_engineering_status",
        "assurance_status",
        "external_evidence_required",
        "evidence_source",
        "expected_artifact",
        "validation_method",
        "why_cannot_be_proven_locally",
        "owner",
    }
)


def test_every_item_has_exact_external_contract():
    from governance.fds_production_external_assurance_boundary import _build_item_registry

    items = _build_item_registry()
    assert len(items) >= 15
    for item in items:
        assert _REQUIRED_FIELDS.issubset(item.keys())
        assert len(str(item["external_evidence_required"])) >= 20 or item["assurance_status"] == "NOT_CURRENTLY_APPLICABLE_WITH_EVIDENCE"
        assert item["validation_method"]
        assert item["expected_artifact"]


def test_fds04_not_currently_applicable():
    from governance.fds_production_external_assurance_boundary import _fds04_applicability, _build_item_registry

    fds04 = _fds04_applicability()
    assert fds04["bank_linking_feature_present"] is False
    assert fds04["applicability"] == "NOT_CURRENTLY_APPLICABLE_WITH_EVIDENCE"
    item = next(i for i in _build_item_registry() if i["control_id"] == "FDS-04")
    assert item["assurance_status"] == "NOT_CURRENTLY_APPLICABLE_WITH_EVIDENCE"
    assert item["applicability_evidence"]


def test_no_local_gap_hidden_as_external():
    from governance.fds_production_external_assurance_boundary import _build_item_registry, _misclassification_checks

    items = _build_item_registry()
    checks = _misclassification_checks(items)
    assert checks["LOCAL_GAPS_HIDDEN_AS_EXTERNAL"] == 0
    assert checks["MISCLASSIFIED_EXTERNAL_ITEMS"] == 0
    for item in items:
        if item["assurance_status"] in {"PRODUCTION_VALIDATION_PENDING", "EXTERNAL_ATTESTATION_PENDING"}:
            assert item["local_engineering_status"] == "LOCAL_ENGINEERING_COMPLETE"


def test_fips_no_false_validation_claim():
    from governance.fds_production_external_assurance_boundary import _misclassification_checks, _build_item_registry
    from secrets_crypto.fips import assert_no_false_fips_claim, fips_state

    state = fips_state()
    assert state.get("validated") is False
    assert state.get("external_validation_pending") is True
    assert_no_false_fips_claim()
    checks = _misclassification_checks(_build_item_registry())
    assert checks["FALSE_COMPLIANCE_CLAIMS"] == 0


def test_safe_probes_do_not_claim_production_proof():
    from governance.fds_production_external_assurance_boundary import verify_fds_production_external_assurance_boundary

    result = verify_fds_production_external_assurance_boundary(run_closure_verifiers=False)
    assert result["safe_probes"]["claims_production_proof"] is False
    for probe in result["safe_probes"]["tls"]:
        assert probe.get("production_tls_proof") is False


def test_summary_counter_consistency():
    from governance.fds_production_external_assurance_boundary import verify_fds_production_external_assurance_boundary

    result = verify_fds_production_external_assurance_boundary(run_closure_verifiers=False)
    s = result["summary"]
    items = result["items"]
    assert s["EXTERNAL_ITEMS_REVIEWED"] == len(items)
    assert s["GENUINE_PRODUCTION_VALIDATION_PENDING"] == sum(
        1 for i in items if i["assurance_status"] == "PRODUCTION_VALIDATION_PENDING"
    )
    assert s["GENUINE_EXTERNAL_ATTESTATION_PENDING"] == sum(
        1 for i in items if i["assurance_status"] == "EXTERNAL_ATTESTATION_PENDING"
    )
    assert s["NOT_CURRENTLY_APPLICABLE_WITH_EVIDENCE"] == sum(
        1 for i in items if i["assurance_status"] == "NOT_CURRENTLY_APPLICABLE_WITH_EVIDENCE"
    )


def test_previous_fds_phases_green_without_rerunning_closure_scripts():
    from governance.fds_data_boundary import verify_fds_data_boundary_scope
    from governance.fds_privileged_identity import verify_fds_privileged_identity_scope
    from governance.fds_retention_incident_supply_chain import verify_fds_retention_incident_supply_chain_scope
    from governance.fds_secrets_crypto_audit import verify_fds_secrets_crypto_audit_scope
    from governance.fds_transport_webhook_environment import verify_fds_transport_webhook_environment_scope

    assert verify_fds_data_boundary_scope()["scope_verified"] is True
    assert verify_fds_privileged_identity_scope()["scope_verified"] is True
    assert verify_fds_secrets_crypto_audit_scope()["scope_verified"] is True
    assert verify_fds_transport_webhook_environment_scope()["scope_verified"] is True
    assert verify_fds_retention_incident_supply_chain_scope()["scope_verified"] is True


def test_payment_regression_green():
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_payments_usd_security.py", "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_boundary_verifier_structure():
    from governance.fds_production_external_assurance_boundary import verify_fds_production_external_assurance_boundary

    result = verify_fds_production_external_assurance_boundary(run_closure_verifiers=False)
    assert "verdict" in result
    assert "misclassification_checks" in result
    assert result["misclassification_checks"]["UNSPECIFIED_EXTERNAL_EVIDENCE_REQUIREMENTS"] == 0


def test_closure_script_produces_evidence():
    proc = subprocess.run(
        [sys.executable, "scripts/fds_production_external_assurance_boundary_verify.py"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=3600,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    evidence = json.loads((ROOT / "FDS_PRODUCTION_EXTERNAL_ASSURANCE_BOUNDARY.json").read_text())
    assert evidence["verdict"] == "FDS_EXTERNAL_ASSURANCE_BOUNDARY_CLOSED"
    assert evidence["summary"]["MISCLASSIFIED_EXTERNAL_ITEMS"] == 0
    assert evidence["summary"]["REGRESSION_FAILURES"] == 0
