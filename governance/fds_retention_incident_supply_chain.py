"""Evidence-derived FDS retention/incident/supply-chain scope verification."""

from __future__ import annotations

from typing import Any


def verify_fds_retention_incident_supply_chain_scope() -> dict[str, Any]:
    from fds_retention_incident.account_closure import account_closure_status
    from fds_retention_incident.backup_lifecycle import backup_lifecycle_status, record_backup_creation
    from fds_retention_incident.incident_drill import run_all_drills
    from fds_retention_incident.incident_playbook import all_incident_types, incident_playbook_status, route_incident
    from fds_retention_incident.payment_script_inventory import verify_payment_path_minimization
    from fds_retention_incident.retention_policy import (
        all_fds_classes_have_policy,
        financial_retention_matrix,
        reject_indefinite_retention,
        retention_for_class,
    )
    from fds_retention_incident.supply_chain import evaluate_waivers, sbom_status, sca_status, supply_chain_status
    from financial_data.classification import FDSClass

    gaps: dict[str, int] = {
        "FINANCIAL_RETENTION_POLICY_GAPS": 0,
        "INDEFINITE_FINANCIAL_RETENTION_PATHS": 0,
        "ACCOUNT_CLOSURE_RETENTION_GAPS": 0,
        "FINANCIAL_CREDENTIAL_REVOCATION_GAPS": 0,
        "BACKUP_EXPIRY_POLICY_GAPS": 0,
        "BACKUP_DELETION_VERIFICATION_GAPS": 0,
        "FALSE_DELETION_CLAIM_PATHS": 0,
        "FINANCIAL_INCIDENT_PLAYBOOK_GAPS": 0,
        "FINANCIAL_INCIDENT_ROUTING_GAPS": 0,
        "INCIDENT_SECRET_LEAK_IN_RECORD_PATHS": 0,
        "INCIDENT_DRILL_GAPS": 0,
        "INCIDENT_POST_REVIEW_GAPS": 0,
        "SCA_COVERAGE_GAPS": 0,
        "SBOM_GAPS": 0,
        "CRITICAL_DEPENDENCY_RELEASE_POLICY_GAPS": 0,
        "UNCONTROLLED_SECURITY_DEPENDENCY_WAIVERS": 0,
        "PAYMENT_FLOW_THIRD_PARTY_SCRIPT_GAPS": 0,
    }

    matrix = financial_retention_matrix()
    if not matrix or not all_fds_classes_have_policy():
        gaps["FINANCIAL_RETENTION_POLICY_GAPS"] = 1
    for policy in matrix:
        if not reject_indefinite_retention(policy):
            gaps["INDEFINITE_FINANCIAL_RETENTION_PATHS"] += 1

    closure = account_closure_status()
    if not closure.get("closure_states"):
        gaps["ACCOUNT_CLOSURE_RETENTION_GAPS"] = 1
    if "pending_backup_expiry" not in closure.get("closure_states", []):
        gaps["FALSE_DELETION_CLAIM_PATHS"] = 1

    for cls in (FDSClass.C3_BANKING, FDSClass.C4_SECRET):
        pol = retention_for_class(cls)
        if pol.get("deletion_method") not in {"CRYPTO_ERASE", "REVOKE", "TOKEN_REVOKE"}:
            gaps["FINANCIAL_CREDENTIAL_REVOCATION_GAPS"] += 1

    backup = backup_lifecycle_status()
    if backup.get("retention_days", 0) <= 0:
        gaps["BACKUP_EXPIRY_POLICY_GAPS"] = 1
    sample = record_backup_creation(backup_path="verify_sample.sql.gz", policy_class="verify", sha256="verify")
    if not sample.get("expiry_at"):
        gaps["BACKUP_EXPIRY_POLICY_GAPS"] = 1
    from fds_retention_incident.backup_lifecycle import verify_backup_deletion

    verify = verify_backup_deletion("verify_sample.sql.gz")
    if verify.get("verified") is not True:
        gaps["BACKUP_DELETION_VERIFICATION_GAPS"] = 1

    required_incidents = {
        "pan_discovered_in_storage",
        "sad_discovered",
        "leaked_financial_api_secret",
        "exposed_webhook_signing_secret",
        "unauthorized_financial_export",
        "bank_credential_exposure",
        "privileged_unauthorized_financial_access",
        "financial_data_in_logs_analytics_ai",
        "compromised_payment_integration",
    }
    playbook_types = set(all_incident_types())
    if not required_incidents.issubset(playbook_types):
        gaps["FINANCIAL_INCIDENT_PLAYBOOK_GAPS"] = 1

    try:
        routed = route_incident("exposed_webhook_signing_secret", detection_source="scope_verify")
        if not routed.get("routing"):
            gaps["FINANCIAL_INCIDENT_ROUTING_GAPS"] = 1
        if routed.get("post_incident_review_required") is not True:
            gaps["INCIDENT_POST_REVIEW_GAPS"] = 1
    except Exception:
        gaps["FINANCIAL_INCIDENT_ROUTING_GAPS"] = 1

    try:
        from fds_retention_incident.incident_playbook import create_incident

        bad = create_incident("leaked_financial_api_secret", detection_source="whsec_test_secret_value_here")
        if "whsec" in str(bad):
            gaps["INCIDENT_SECRET_LEAK_IN_RECORD_PATHS"] = 1
    except ValueError:
        pass
    except Exception:
        gaps["INCIDENT_SECRET_LEAK_IN_RECORD_PATHS"] = 1

    drill = run_all_drills()
    if not drill.get("all_passed"):
        gaps["INCIDENT_DRILL_GAPS"] = int(drill.get("failed", 1))
    for _key, result in drill.get("scenarios", {}).items():
        if result.get("post_incident_review_completed") is not True:
            gaps["INCIDENT_POST_REVIEW_GAPS"] += 1

    sca = sca_status()
    if sca.get("tool") != "pip-audit":
        gaps["SCA_COVERAGE_GAPS"] = 1

    sbom = sbom_status()
    if not sbom.get("machine_readable") or not sbom.get("generated"):
        gaps["SBOM_GAPS"] = 1

    sc = supply_chain_status()
    if sc.get("release_policy", {}).get("policy") is None:
        gaps["CRITICAL_DEPENDENCY_RELEASE_POLICY_GAPS"] = 1

    waivers = evaluate_waivers()
    gaps["UNCONTROLLED_SECURITY_DEPENDENCY_WAIVERS"] = len(waivers.get("uncontrolled", []))

    payment = verify_payment_path_minimization()
    gaps["PAYMENT_FLOW_THIRD_PARTY_SCRIPT_GAPS"] = len(payment.get("gaps", []))

    fds20_ok = (
        gaps["FINANCIAL_RETENTION_POLICY_GAPS"] == 0
        and gaps["INDEFINITE_FINANCIAL_RETENTION_PATHS"] == 0
        and gaps["ACCOUNT_CLOSURE_RETENTION_GAPS"] == 0
        and gaps["FINANCIAL_CREDENTIAL_REVOCATION_GAPS"] == 0
        and gaps["FALSE_DELETION_CLAIM_PATHS"] == 0
    )
    sdg15_ok = gaps["BACKUP_EXPIRY_POLICY_GAPS"] == 0 and gaps["BACKUP_DELETION_VERIFICATION_GAPS"] == 0
    fds21_ok = (
        gaps["FINANCIAL_INCIDENT_PLAYBOOK_GAPS"] == 0
        and gaps["FINANCIAL_INCIDENT_ROUTING_GAPS"] == 0
        and gaps["INCIDENT_SECRET_LEAK_IN_RECORD_PATHS"] == 0
        and gaps["INCIDENT_DRILL_GAPS"] == 0
        and gaps["INCIDENT_POST_REVIEW_GAPS"] == 0
    )
    sdg17_ok = (
        gaps["SCA_COVERAGE_GAPS"] == 0
        and gaps["SBOM_GAPS"] == 0
        and gaps["CRITICAL_DEPENDENCY_RELEASE_POLICY_GAPS"] == 0
        and gaps["UNCONTROLLED_SECURITY_DEPENDENCY_WAIVERS"] == 0
        and gaps["PAYMENT_FLOW_THIRD_PARTY_SCRIPT_GAPS"] == 0
    )

    controls = {
        "FDS-20": {"verified": fds20_ok, "evidence": "fds_retention_incident.retention_policy + account_closure"},
        "FDS-21": {"verified": fds21_ok, "evidence": "fds_retention_incident.incident_playbook + incident_drill"},
    }
    sdg = {
        "SDG-15": {"verified": sdg15_ok, "evidence": "fds_retention_incident.backup_lifecycle"},
        "SDG-16": {"verified": drill.get("all_passed") is True, "evidence": "fds_retention_incident.incident_drill"},
        "SDG-17": {"verified": sdg17_ok, "evidence": "fds_retention_incident.supply_chain + payment_script_inventory"},
    }
    scope_verified = all(c["verified"] for c in controls.values()) and all(s["verified"] for s in sdg.values())
    if sum(gaps.values()) > 0:
        scope_verified = False

    return {
        "scope_verified": scope_verified,
        "controls": controls,
        "sdg": sdg,
        "gaps": gaps,
        "retention_matrix_version": matrix[0]["policy_version"] if matrix else "",
        "incident_playbook": incident_playbook_status(),
        "backup_lifecycle": backup,
        "drill_summary": {"all_passed": drill.get("all_passed"), "scenario_count": drill.get("scenario_count")},
        "supply_chain": sc,
        "production_validation_pending": [
            "actual_cloud_backup_expiry_deletion_proof",
            "real_incident_exercise_participation",
            "provider_side_credential_revocation_proof",
            "live_dependency_monitoring_service_behavior",
        ],
    }
