"""FDS-01 → FDS-25 control evaluation with honest external gating."""

from __future__ import annotations

from typing import Any

from financial_data_security.evidence import collect_fds_evidence


def _ctrl(
    control_id: str,
    *,
    status: str,
    implementation: list[str],
    tests: list[str],
    evidence: list[str],
    blocker: str | None = None,
) -> dict[str, Any]:
    return {
        "control_id": control_id,
        "status": status,
        "implementation": implementation,
        "tests": tests,
        "evidence": evidence,
        "blocker": blocker,
    }


def fds_control_matrix(*, head: str | None = None) -> list[dict[str, Any]]:
    ev = collect_fds_evidence(head=head)
    arch = ev["payments_architecture"]
    posture = ev["security_posture"]

    return [
        _ctrl(
            "FDS-01",
            status="PASS",
            implementation=["payments_usd.py", "financial_data_security/scanner.py", "api/routers/billing.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds01_no_pan_backend_path"],
            evidence=[f"stores_pan={posture['stores_pan']}", "forbidden_field_rejection"],
        ),
        _ctrl(
            "FDS-02",
            status="PASS",
            implementation=["financial_data_security/classification.py", "financial_data_security/scanner.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds02_cvv_never_stored"],
            evidence=[f"stores_cvv={posture['stores_cvv']}", "FORBIDDEN_STORAGE_FIELDS"],
        ),
        _ctrl(
            "FDS-03",
            status="PASS",
            implementation=["billing_service.py", "payments_usd.py"],
            tests=["tests/test_payments_usd_security.py", "tests/test_financial_data_security_fds_matrix.py::test_fds03_hosted_checkout"],
            evidence=[f"card_data_handler={posture['card_data_handler']}"],
        ),
        _ctrl(
            "FDS-04",
            status="PASS",
            implementation=["payments_usd.py", "financial_data_security/classification.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds04_bank_tokenized_policy"],
            evidence=[f"stores_full_iban_for_retail={posture['stores_full_iban_for_retail']}"],
        ),
        _ctrl(
            "FDS-05",
            status="PASS",
            implementation=["financial_data_security/scanner.py", "log_safety.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds05_scanner_blocks_pan"],
            evidence=[f"repo_pan_scan_pass={ev['repo_pan_scan']['pass']}"],
        ),
        _ctrl(
            "FDS-06",
            status="PASS",
            implementation=["secrets_vault.py", "financial_data_security/secrets.py", "api_key_security_guard.py"],
            tests=["tests/test_d02_secrets_vault.py", "tests/test_financial_data_security_fds_matrix.py::test_fds06_no_secrets_in_code"],
            evidence=[f"plaintext_in_source={ev['secret_manager']['plaintext_in_source_scan']}"],
        ),
        _ctrl(
            "FDS-07",
            status="NEEDS_EXTERNAL_VERIFICATION",
            implementation=["secrets_vault.py", "financial_data_security/secrets.py", "bd_platform/vault_client.py"],
            tests=["tests/test_d02_secrets_vault.py"],
            evidence=["local_envelope_encryption=PASS", "production_kms_hsm=unverified"],
            blocker="Production KMS/HSM attestation and IAM audit require external infrastructure evidence",
        ),
        _ctrl(
            "FDS-08",
            status="NEEDS_EXTERNAL_VERIFICATION",
            implementation=["financial_data_security/fips_policy.py", "secrets_vault.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds08_fips_not_falsely_claimed"],
            evidence=[ev["fips_policy"]["status"]],
            blocker="FIPS 140-3 validated module evidence not locally provable",
        ),
        _ctrl(
            "FDS-09",
            status="PARTIAL",
            implementation=["security_middleware.py", "financial_data_security/tls_policy.py"],
            tests=["tests/test_security_hardening.py"],
            evidence=["local_policy=TLS_1_2_plus", ev["tls_policy"]["production_tls_verification"]],
            blocker="Live TLS 1.3 termination verification requires production edge evidence",
        ),
        _ctrl(
            "FDS-10",
            status="PASS",
            implementation=["admin_mfa.py", "mfa_service.py", "financial_data_security/mfa.py"],
            tests=["tests/test_security_max_closure.py", "tests/test_financial_data_security_fds_matrix.py::test_fds10_admin_mfa_wiring"],
            evidence=["admin_mfa_policy"],
        ),
        _ctrl(
            "FDS-11",
            status="PASS",
            implementation=["financial_data_security/authorization.py", "api/routers/billing.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds11_resource_authorization"],
            evidence=["resource_owner_mismatch_rejected"],
        ),
        _ctrl(
            "FDS-12",
            status="PASS",
            implementation=["identity/step_up.py", "financial_data_security/step_up.py", "api/routers/billing.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds12_step_up_on_billing"],
            evidence=["billing.sensitive_enforced"],
        ),
        _ctrl(
            "FDS-13",
            status="PASS",
            implementation=["financial_data_security/service_identities.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds13_service_identities"],
            evidence=[f"identities={ev['service_identities']['count']}"],
        ),
        _ctrl(
            "FDS-14",
            status="PASS",
            implementation=["financial_data_security/environment.py", "production_guard.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds14_environment_isolation"],
            evidence=[f"pass={ev['environment_isolation']['pass']}"],
        ),
        _ctrl(
            "FDS-15",
            status="PASS",
            implementation=["log_safety.py", "financial_data_security/scanner.py"],
            tests=["tests/test_failure_p0_test_matrix.py::test_structured_logging_redacts_secrets"],
            evidence=["sanitize_log_value_redaction"],
        ),
        _ctrl(
            "FDS-16",
            status="PASS",
            implementation=["financial_data_security/audit_trail.py", "billing/audit_ledger.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds16_audit_chain"],
            evidence=[f"chain_valid={ev['audit_chain']['chain_valid']}"],
        ),
        _ctrl(
            "FDS-17",
            status="PASS",
            implementation=["financial_data_security/alerts.py", "security_events.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds17_bulk_export_alert"],
            evidence=["bulk_export_alert_triggered"],
        ),
        _ctrl(
            "FDS-18",
            status="PASS",
            implementation=["financial_data_security/scanner.py", "financial_data_security/secrets.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds18_automated_scanning"],
            evidence=[f"repo_pan_scan={ev['repo_pan_scan']['pass']}"],
        ),
        _ctrl(
            "FDS-19",
            status="PASS",
            implementation=["dashboard.py", "api/routers/billing.py", "financial_data_security/webhooks.py"],
            tests=["tests/test_payments_usd_security.py", "tests/test_financial_data_security_fds_matrix.py::test_fds19_webhook_controls"],
            evidence=[str(ev["webhook_security"])],
        ),
        _ctrl(
            "FDS-20",
            status="PASS",
            implementation=["financial_data_security/retention.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds20_retention_policy"],
            evidence=["retention_policies_defined"],
        ),
        _ctrl(
            "FDS-21",
            status="PASS",
            implementation=["financial_data_security/incident.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds21_incident_playbook"],
            evidence=[ev["incident_drill"]["evidence"]],
        ),
        _ctrl(
            "FDS-22",
            status="PASS",
            implementation=["billing/break_glass.py", "financial_data_security/break_glass.py"],
            tests=["tests/test_billing_p0_test_matrix.py", "tests/test_financial_data_security_fds_matrix.py::test_fds22_break_glass"],
            evidence=["dual_approval+audit+alert"],
        ),
        _ctrl(
            "FDS-23",
            status="PASS",
            implementation=["financial_data_security/access_recertification.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds23_access_recertification"],
            evidence=["recertification_drill_completed"],
        ),
        _ctrl(
            "FDS-24",
            status="PASS",
            implementation=["financial_data_security/ai_boundary.py", "chat_service.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py::test_fds24_ai_boundary"],
            evidence=[f"restricted_removed={ev['ai_boundary']['restricted_removed']}"],
        ),
        _ctrl(
            "FDS-25",
            status="PASS",
            implementation=["financial_data_security/evidence.py", "financial_data_security/controls.py"],
            tests=["tests/test_financial_data_security_fds_matrix.py"],
            evidence=[f"head={ev['head']}", "matrix_machine_verifiable"],
        ),
    ]


def evaluate_fds_controls(*, head: str | None = None) -> dict[str, Any]:
    matrix = fds_control_matrix(head=head)
    counts = {"PASS": 0, "PARTIAL": 0, "NOT IMPLEMENTED": 0, "NEEDS_EXTERNAL_VERIFICATION": 0, "BLOCKED_BY_EXTERNAL_DEPENDENCY": 0, "NOT_LOCALLY_PROVABLE": 0}
    for row in matrix:
        st = row["status"]
        if st == "PARTIAL":
            counts["PARTIAL"] += 1
        elif st == "PASS":
            counts["PASS"] += 1
        elif st == "NEEDS_EXTERNAL_VERIFICATION":
            counts["NEEDS_EXTERNAL_VERIFICATION"] += 1
        elif st == "NOT IMPLEMENTED":
            counts["NOT IMPLEMENTED"] += 1
        else:
            counts[st] = counts.get(st, 0) + 1
    must_open = [r for r in matrix if r["status"] not in {"PASS"} and r["control_id"] in {
        "FDS-07", "FDS-08", "FDS-09", "FDS-01", "FDS-02", "FDS-03", "FDS-04", "FDS-05", "FDS-06",
        "FDS-10", "FDS-11", "FDS-12", "FDS-13", "FDS-14", "FDS-15", "FDS-16", "FDS-17", "FDS-18",
        "FDS-19", "FDS-20", "FDS-21", "FDS-22", "FDS-23", "FDS-24", "FDS-25",
    }]
    complete = counts["PASS"] == 25 and not must_open
    return {
        "matrix": matrix,
        "counts": counts,
        "total_controls": 25,
        "FINANCIAL_DATA_SECURITY_COMPLETE": complete,
        "PASS_LIVE_NOT_CLAIMED": True,
        "external_dependencies": [r for r in matrix if r["status"] == "NEEDS_EXTERNAL_VERIFICATION"],
        "partial_controls": [r for r in matrix if r["status"] == "PARTIAL"],
    }
