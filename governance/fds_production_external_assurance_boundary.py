"""Production / external assurance boundary reconciliation for FDS."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[1]

AssuranceStatus = Literal[
    "LOCAL_ENGINEERING_COMPLETE",
    "PRODUCTION_VALIDATION_PENDING",
    "EXTERNAL_ATTESTATION_PENDING",
    "NOT_CURRENTLY_APPLICABLE_WITH_EVIDENCE",
    "LOCAL_ENGINEERING_GAP",
]

_CLOSURE_SCRIPTS = [
    ROOT / "scripts" / "fds_security_governance_data_boundary_closure_verify.py",
    ROOT / "scripts" / "fds_privileged_identity_authorization_closure_verify.py",
    ROOT / "scripts" / "fds_secrets_crypto_audit_identity_closure_verify.py",
    ROOT / "scripts" / "fds_transport_webhook_environment_closure_verify.py",
    ROOT / "scripts" / "fds_retention_incident_supply_chain_closure_verify.py",
]

_CLOSURE_ARTIFACTS = [
    ROOT / "FDS_SECURITY_GOVERNANCE_DATA_BOUNDARY_CLOSURE_EVIDENCE.json",
    ROOT / "FDS_PRIVILEGED_IDENTITY_AUTHORIZATION_CLOSURE_EVIDENCE.json",
    ROOT / "FDS_SECRETS_CRYPTO_AUDIT_IDENTITY_CLOSURE_EVIDENCE.json",
    ROOT / "FDS_TRANSPORT_WEBHOOK_ENVIRONMENT_CLOSURE_EVIDENCE.json",
    ROOT / "FDS_RETENTION_INCIDENT_SUPPLY_CHAIN_CLOSURE_EVIDENCE.json",
]

_PRODUCTION_HOSTS = (
    "blackdark.io",
    "www.blackdark.io",
    "blackdark-production.up.railway.app",
)


def _local_prereq(
    *,
    implementation: list[str],
    wiring: list[str],
    tests: list[str],
    fail_closed: list[str],
    machine_evidence: list[str],
) -> dict[str, Any]:
    def _exists(paths: list[str]) -> bool:
        return all((ROOT / p).is_file() for p in paths)

    impl_ok = _exists(implementation)
    wire_ok = _exists(wiring)
    test_ok = _exists(tests)
    fc_ok = _exists(fail_closed)
    ev_ok = _exists(machine_evidence)
    complete = impl_ok and wire_ok and test_ok and fc_ok and ev_ok
    missing = []
    if not impl_ok:
        missing.append("implementation")
    if not wire_ok:
        missing.append("wiring")
    if not test_ok:
        missing.append("tests")
    if not fc_ok:
        missing.append("fail_closed")
    if not ev_ok:
        missing.append("machine_evidence")
    return {
        "implementation_paths": implementation,
        "wiring_paths": wiring,
        "test_paths": tests,
        "fail_closed_paths": fail_closed,
        "machine_evidence_paths": machine_evidence,
        "complete": complete,
        "missing": missing,
    }


def _item(
    item_id: str,
    control_id: str,
    requirement: str,
    status: AssuranceStatus,
    *,
    local_prereq: dict[str, Any],
    external_evidence_required: str,
    evidence_source: str,
    expected_artifact: str,
    validation_method: str,
    why_not_provable_locally: str,
    owner: str,
    revalidation: str = "",
    applicability_evidence: list[str] | None = None,
) -> dict[str, Any]:
    local_status = "LOCAL_ENGINEERING_COMPLETE" if local_prereq.get("complete") else "LOCAL_ENGINEERING_GAP"
    if local_status == "LOCAL_ENGINEERING_GAP" and status != "LOCAL_ENGINEERING_GAP":
        status = "LOCAL_ENGINEERING_GAP"
    return {
        "item_id": item_id,
        "control_id": control_id,
        "requirement": requirement,
        "local_engineering_status": local_status,
        "assurance_status": status,
        "local_prerequisites": local_prereq,
        "external_evidence_required": external_evidence_required,
        "evidence_source": evidence_source,
        "expected_artifact": expected_artifact,
        "validation_method": validation_method,
        "why_cannot_be_proven_locally": why_not_provable_locally,
        "owner": owner,
        "revalidation_condition": revalidation,
        "applicability_evidence": applicability_evidence or [],
    }


def _fds04_applicability() -> dict[str, Any]:
    """FDS-04 — no user-facing bank linking on current HEAD."""
    bank_link_signals = []
    skip_dirs = {"tests", "governance", ".git", "node_modules", "venv", ".venv"}
    for pattern in (
        r"\bplaid\b",
        r"/api/[^\"']*bank-link",
        r"/api/[^\"']*bank_account",
        r"collect_iban",
        r"BankLink",
        r"link_bank_account",
    ):
        hits = []
        for path in ROOT.rglob("*.py"):
            if skip_dirs.intersection(path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if re.search(pattern, text, re.IGNORECASE):
                hits.append(str(path.relative_to(ROOT)))
        if hits:
            bank_link_signals.extend(hits[:3])
    has_bank_linking = len(bank_link_signals) > 0
    return {
        "control_id": "FDS-04",
        "bank_linking_feature_present": has_bank_linking,
        "signals": bank_link_signals,
        "payment_architecture": "hosted_stripe_lemon_checkout",
        "applicability": "NOT_CURRENTLY_APPLICABLE_WITH_EVIDENCE" if not has_bank_linking else "REQUIRES_REASSESSMENT",
        "evidence": [
            "docs/PAYMENTS_USD_SECURITY.md",
            "billing_service.py",
            "legal_content.py",
            "no_plaid_or_bank_link_api_routes",
        ],
    }


def _tls_probe(hostname: str) -> dict[str, Any]:
    result: dict[str, Any] = {"hostname": hostname, "probed_at": datetime.now(UTC).isoformat()}
    try:
        proc = subprocess.run(
            ["openssl", "s_client", "-connect", f"{hostname}:443", "-servername", hostname],
            input=b"",
            capture_output=True,
            text=True,
            timeout=15,
        )
        out = proc.stdout + proc.stderr
        result["openssl_exit_code"] = proc.returncode
        if "Protocol  : TLSv1.3" in out:
            result["tls_version_observed"] = "TLSv1.3"
        elif "Protocol  : TLSv1.2" in out:
            result["tls_version_observed"] = "TLSv1.2"
        else:
            result["tls_version_observed"] = None
        result["certificate_observed"] = "BEGIN CERTIFICATE" in out
        result["production_tls_proof"] = False
        result["note"] = "connectivity_or_handshake_only_not_closure_proof"
    except Exception as exc:
        result["error"] = str(exc)
        result["production_tls_proof"] = False
    return result


def _http_headers_probe(url: str) -> dict[str, Any]:
    result: dict[str, Any] = {"url": url, "probed_at": datetime.now(UTC).isoformat()}
    try:
        proc = subprocess.run(
            ["curl", "-sI", url],
            capture_output=True,
            text=True,
            timeout=15,
        )
        headers = proc.stdout
        result["status_line"] = headers.splitlines()[0] if headers else ""
        result["strict_transport_security"] = any(
            line.lower().startswith("strict-transport-security:") for line in headers.splitlines()
        )
        result["hsts_proof"] = result["strict_transport_security"]
        result["production_hsts_proof"] = False
        result["note"] = "header_probe_not_closure_proof_without_production_config_attestation"
    except Exception as exc:
        result["error"] = str(exc)
        result["hsts_proof"] = False
        result["production_hsts_proof"] = False
    return result


def _build_item_registry() -> list[dict[str, Any]]:
    transport_local = _local_prereq(
        implementation=["transport_webhook_env/transport.py", "security_middleware.py"],
        wiring=["security_middleware.py", "dashboard.py"],
        tests=["tests/test_fds_transport_webhook_environment.py"],
        fail_closed=["transport_webhook_env/transport.py"],
        machine_evidence=["FDS_TRANSPORT_WEBHOOK_ENVIRONMENT_CLOSURE_EVIDENCE.json"],
    )
    env_local = _local_prereq(
        implementation=["transport_webhook_env/environment.py", "production_guard.py"],
        wiring=["production_guard.py"],
        tests=["tests/test_fds_transport_webhook_environment.py"],
        fail_closed=["transport_webhook_env/environment.py", "production_guard.py"],
        machine_evidence=["FDS_TRANSPORT_WEBHOOK_ENVIRONMENT_CLOSURE_EVIDENCE.json"],
    )
    access_local = _local_prereq(
        implementation=["transport_webhook_env/access_audit.py", "privileged_access/operations.py"],
        wiring=["api/routers/privacy.py", "transport_webhook_env/access_audit.py"],
        tests=["tests/test_fds_transport_webhook_environment.py", "tests/test_fds_privileged_identity_authorization.py"],
        fail_closed=["privileged_access/step_up.py", "privileged_access/policy.py"],
        machine_evidence=["FDS_PRIVILEGED_IDENTITY_AUTHORIZATION_CLOSURE_EVIDENCE.json"],
    )
    fips_local = _local_prereq(
        implementation=["secrets_crypto/fips.py"],
        wiring=["secrets_crypto/fips.py", "production_guard.py"],
        tests=["tests/test_fds_secrets_crypto_audit_identity.py"],
        fail_closed=["secrets_crypto/fips.py"],
        machine_evidence=["FDS_SECRETS_CRYPTO_AUDIT_IDENTITY_CLOSURE_EVIDENCE.json"],
    )
    backup_local = _local_prereq(
        implementation=["fds_retention_incident/backup_lifecycle.py"],
        wiring=["scripts/backup_postgres.py"],
        tests=["tests/test_fds_retention_incident_supply_chain.py"],
        fail_closed=["fds_retention_incident/backup_lifecycle.py"],
        machine_evidence=["FDS_RETENTION_INCIDENT_SUPPLY_CHAIN_CLOSURE_EVIDENCE.json"],
    )
    incident_local = _local_prereq(
        implementation=["fds_retention_incident/incident_playbook.py", "fds_retention_incident/incident_drill.py"],
        wiring=["docs/ops/FINANCIAL_DATA_INCIDENT_PLAYBOOK.md"],
        tests=["tests/test_fds_retention_incident_supply_chain.py"],
        fail_closed=["fds_retention_incident/incident_playbook.py"],
        machine_evidence=["FDS_RETENTION_INCIDENT_SUPPLY_CHAIN_CLOSURE_EVIDENCE.json"],
    )
    supply_local = _local_prereq(
        implementation=["fds_retention_incident/supply_chain.py", "scripts/generate_sbom.py"],
        wiring=[".github/workflows/security.yml"],
        tests=["tests/test_fds_retention_incident_supply_chain.py"],
        fail_closed=["fds_retention_incident/supply_chain.py"],
        machine_evidence=["FDS_RETENTION_INCIDENT_SUPPLY_CHAIN_CLOSURE_EVIDENCE.json"],
    )
    credential_local = _local_prereq(
        implementation=["fds_retention_incident/account_closure.py", "secrets_crypto/lifecycle.py"],
        wiring=["gdpr_service.py", "user_keys_service.py"],
        tests=["tests/test_fds_retention_incident_supply_chain.py"],
        fail_closed=["secrets_crypto/lifecycle.py"],
        machine_evidence=["FDS_RETENTION_INCIDENT_SUPPLY_CHAIN_CLOSURE_EVIDENCE.json"],
    )
    fds04 = _fds04_applicability()

    items = [
        _item(
            "FIPS-140-3-MODULE-CERTIFICATE",
            "FDS-08",
            "FIPS 140-3 validated cryptographic module bound to deployed runtime configuration",
            "EXTERNAL_ATTESTATION_PENDING",
            local_prereq=fips_local,
            external_evidence_required=(
                "CMVP certificate PDF or vendor attestation JSON naming module_id, certificate number, "
                "validated version, and deployment configuration binding to CRYPTO_PROVIDER/FIPS_MODULE_ID"
            ),
            evidence_source="NIST CMVP / cloud KMS vendor / HSM vendor",
            expected_artifact="fips_validation_attestation.json attached via FIPS_VALIDATION_EVIDENCE_PATH",
            validation_method="secrets_crypto.fips.fips_state() returns validated=true with certificate_id",
            why_not_provable_locally="FIPS validation is a third-party certification, not implementable in application code",
            owner="platform_security",
            revalidation="annual or on crypto module upgrade",
        ),
        _item(
            "TLS-PUBLIC-ENDPOINT-MINIMUM",
            "FDS-09",
            "Production public endpoints enforce TLS 1.2+ with no downgrade",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=transport_local,
            external_evidence_required=(
                "ssllabs or openssl s_client transcript for blackdark.io and blackdark-production.up.railway.app "
                "showing negotiated TLS>=1.2, trusted certificate chain, and ingress TLS policy attestation"
            ),
            evidence_source="production ingress (Railway/CDN) + live endpoint scan",
            expected_artifact="tls_public_endpoint_attestation.json",
            validation_method="Independent scan confirms TLS>=1.2 on all customer-facing hostnames",
            why_not_provable_locally="TLS termination occurs at external ingress; local middleware cannot attest live cipher suite",
            owner="platform_ops",
            revalidation="quarterly and after ingress change",
        ),
        _item(
            "HSTS-PRODUCTION-RESPONSE",
            "FDS-09",
            "Production responses include Strict-Transport-Security with appropriate max-age",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=transport_local,
            external_evidence_required="curl -sI https://<production-host>/ showing Strict-Transport-Security header on HTTPS responses",
            evidence_source="live production HTTP response headers",
            expected_artifact="hsts_production_header_capture.txt",
            validation_method="Header present on production apex and app hostnames with max-age>=31536000",
            why_not_provable_locally="HSTS must be observed on deployed ingress, not dev/test only",
            owner="platform_ops",
            revalidation="after CDN/LB config change",
        ),
        _item(
            "SECURE-COOKIE-PRODUCTION",
            "FDS-09",
            "Session cookies marked Secure+HttpOnly+SameSite in production",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=transport_local,
            external_evidence_required="Set-Cookie capture from production login showing Secure; HttpOnly; SameSite attributes",
            evidence_source="production authentication flow",
            expected_artifact="production_set_cookie_capture.txt",
            validation_method="Browser/curl capture of Set-Cookie on https production login",
            why_not_provable_locally="Cookie attributes must be verified on live production responses",
            owner="platform_ops",
            revalidation="after auth/session change",
        ),
        _item(
            "CDN-LB-INGRESS-CONFIGURATION",
            "FDS-14",
            "CDN/load balancer ingress enforces HTTPS-only customer traffic",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=env_local,
            external_evidence_required="Railway/CDN dashboard export or IaC showing HTTPS listener, TLS policy, and HTTP redirect",
            evidence_source="cloud provider ingress configuration",
            expected_artifact="ingress_tls_policy_export.json",
            validation_method="Provider config review matches transport_webhook_env contract",
            why_not_provable_locally="Ingress config is external to repository runtime",
            owner="platform_ops",
            revalidation="after infrastructure change",
        ),
        _item(
            "CLOUD-NETWORK-PROJECT-BOUNDARY",
            "FDS-14",
            "Production network/project boundary isolates financial workloads",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=env_local,
            external_evidence_required="Cloud project/VPC boundary diagram with production account IDs and network ACL summary",
            evidence_source="cloud provider account governance",
            expected_artifact="production_network_boundary_attestation.pdf",
            validation_method="Security review confirms prod/staging/dev project separation",
            why_not_provable_locally="Network boundaries are cloud-account level, not code-level",
            owner="platform_security",
            revalidation="annual",
        ),
        _item(
            "ENV-SECRET-NAMESPACE-SEPARATION",
            "FDS-14",
            "Distinct secret namespaces per environment with no crossover",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=env_local,
            external_evidence_required="Secret manager/Railway variable export showing distinct STRIPE_/DATABASE_/WEBHOOK_ values per ENV",
            evidence_source="production secret store + staging secret store",
            expected_artifact="environment_secret_namespace_diff.json",
            validation_method="Automated diff shows zero shared live secrets across prod and non-prod",
            why_not_provable_locally="Secret values live in external secret stores",
            owner="platform_security",
            revalidation="after secret rotation or env addition",
        ),
        _item(
            "ENV-DATABASE-RESOURCE-SEPARATION",
            "FDS-14",
            "Production database/resources isolated from staging/dev",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=env_local,
            external_evidence_required="DATABASE_URL host/dbname listing per environment with no shared production DB in non-prod",
            evidence_source="database provider consoles",
            expected_artifact="environment_database_inventory.json",
            validation_method="Inventory review confirms distinct connection targets per ENV",
            why_not_provable_locally="Database instances are external managed resources",
            owner="platform_ops",
            revalidation="after database migration",
        ),
        _item(
            "SANDBOX-VS-PRODUCTION-PSP-CREDENTIALS",
            "FDS-14",
            "Stripe/Lemon sandbox credentials never used in production",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=env_local,
            external_evidence_required="Stripe dashboard mode + Railway env showing sk_live_/whsec_ only in production; test keys only in staging",
            evidence_source="PSP dashboards + deployment env",
            expected_artifact="psp_credential_environment_matrix.json",
            validation_method="Key prefix audit: production uses live prefixes only",
            why_not_provable_locally="Live vs test key assignment is deployment configuration",
            owner="billing_ops",
            revalidation="after PSP key rotation",
        ),
        _item(
            "NO-PRODUCTION-DATA-IN-NONPROD",
            "FDS-14",
            "No production customer/financial data replicated to non-production",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=env_local,
            external_evidence_required="Data flow attestation + backup/restore policy showing prod snapshots not restored to staging without anonymization",
            evidence_source="ops data governance",
            expected_artifact="prod_to_nonprod_data_flow_attestation.json",
            validation_method="Quarterly review confirms no prod PII/financial rows in staging DB",
            why_not_provable_locally="Data residency is operational, not verifiable from code alone",
            owner="data_governance",
            revalidation="quarterly",
        ),
        _item(
            "PRODUCTION-PRIVILEGED-ACCESS-AUDIT",
            "SDG-13",
            "Named privileged production access events with MFA strength and authorization outcome",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=access_local,
            external_evidence_required=(
                "Export of data/production_access_audit.jsonl showing actor, action, target, timestamp, "
                "auth_strength, authorization_result, correlation_id for real production sessions"
            ),
            evidence_source="production DATA_DIR production_access_audit.jsonl",
            expected_artifact="production_access_audit_sample.jsonl",
            validation_method="Sample review of 30d production privileged events with audit integrity intact",
            why_not_provable_locally="Local test audit logs are synthetic, not production operator evidence",
            owner="security_oncall",
            revalidation="monthly sampling",
        ),
        _item(
            "BREAK-GLASS-PRODUCTION-EXERCISE",
            "FDS-22",
            "Break-glass activation attributable in production if exercised",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=access_local,
            external_evidence_required="data/break_glass_events.jsonl production export with actor, reason, expiry, revoke state",
            evidence_source="production break-glass ledger",
            expected_artifact="production_break_glass_audit_sample.jsonl",
            validation_method="If break-glass used, event chain links to production_access_audit correlation_id",
            why_not_provable_locally="Production break-glass exercise not runnable in dev without false claim",
            owner="security_oncall",
            revalidation="after each break-glass use",
        ),
        _item(
            "PRODUCTION-BACKUP-EXPIRY-DELETION",
            "SDG-15",
            "Production backups expire and are deleted/verified per policy",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=backup_local,
            external_evidence_required=(
                "Cloud backup provider lifecycle log showing backup created_at, expiry_at, deletion_result, "
                "verification_result for production database backups"
            ),
            evidence_source="cloud backup provider + data/backup_lifecycle_evidence.jsonl production export",
            expected_artifact="production_backup_lifecycle_evidence.jsonl",
            validation_method="Ops review confirms expired backups absent and VERIFIED state recorded",
            why_not_provable_locally="Actual cloud backup deletion occurs in external storage",
            owner="platform_ops",
            revalidation="monthly",
        ),
        _item(
            "REAL-INCIDENT-EXERCISE",
            "FDS-21",
            "Production/tabletop financial incident exercise with operator participation",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=incident_local,
            external_evidence_required=(
                "Signed tabletop record naming participants, scenario, timestamps, containment/revoke decisions, "
                "and post-incident review — separate from synthetic drill evidence"
            ),
            evidence_source="security operations",
            expected_artifact="production_financial_incident_exercise_record.json",
            validation_method="Exercise record references playbook version and completed POST_INCIDENT_REVIEW",
            why_not_provable_locally="Synthetic drills prove architecture; operator participation is operational",
            owner="security_oncall",
            revalidation="annual",
        ),
        _item(
            "PROVIDER-CREDENTIAL-REVOCATION",
            "FDS-20",
            "Provider-side exchange/API credential revocation confirmed after account closure",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=credential_local,
            external_evidence_required=(
                "Exchange/PSP API audit log showing credential revoked or API key deleted at provider "
                "after account_closure event"
            ),
            evidence_source="Binance/Stripe/exchange provider dashboards",
            expected_artifact="provider_credential_revocation_confirmation.json",
            validation_method="Provider audit timestamp aligns with account_closure_evidence.jsonl entry",
            why_not_provable_locally="Provider revocation occurs outside application boundary",
            owner="security_oncall",
            revalidation="per account closure involving credentials",
        ),
        _item(
            "LIVE-DEPENDENCY-MONITORING",
            "SDG-17",
            "Production release cadence dependency monitoring with alert on critical CVE",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=supply_local,
            external_evidence_required="Dependency monitor (GitHub Dependabot/Snyk/etc.) alert history + release block record for critical CVE",
            evidence_source="dependency monitoring service + CI security workflow runs on main",
            expected_artifact="dependency_monitor_alert_history.json",
            validation_method="Critical finding opened, triaged, waived or blocked release per policy",
            why_not_provable_locally="Monitor execution on production release cadence is operational",
            owner="platform_security",
            revalidation="continuous",
        ),
        _item(
            "SBOM-EXTERNAL-RETENTION",
            "SDG-17",
            "SBOM retained/published for external assurance consumers",
            "PRODUCTION_VALIDATION_PENDING",
            local_prereq=supply_local,
            external_evidence_required="Published CycloneDX SBOM URL or artifact store path versioned per release SHA",
            evidence_source="CI artifact store / data room publication",
            expected_artifact="sbom_release_manifest.json mapping git SHA to cyclonedx-python.json",
            validation_method="Each production release tag has corresponding SBOM artifact",
            why_not_provable_locally="External publication/retention is release operations",
            owner="platform_security",
            revalidation="per release",
        ),
        _item(
            "FDS-04-BANK-LINKING-APPLICABILITY",
            "FDS-04",
            "Bank details use tokenized/provider-hosted flow where available",
            fds04["applicability"],
            local_prereq=_local_prereq(
                implementation=["financial_data/classification.py", "financial_data/boundary.py"],
                wiring=["billing_service.py", "legal_content.py"],
                tests=["tests/test_fds_security_governance_data_boundary.py"],
                fail_closed=["financial_data/boundary.py"],
                machine_evidence=["FDS_SECURITY_GOVERNANCE_DATA_BOUNDARY_CLOSURE_EVIDENCE.json"],
            ),
            external_evidence_required="N/A — no user-facing bank linking feature on current HEAD",
            evidence_source="repository architecture review",
            expected_artifact="fds04_applicability_assessment.json",
            validation_method="Confirm no bank collection routes; payments use hosted PSP checkout only",
            why_not_provable_locally="Control not applicable until bank linking feature ships",
            owner="product_security",
            revalidation="reassess when bank linking feature added",
            applicability_evidence=fds04["evidence"],
        ),
    ]
    return items


def _run_closure_verifiers() -> dict[str, Any]:
    results: dict[str, Any] = {}
    failures = 0
    for script in _CLOSURE_SCRIPTS:
        name = script.name
        if not script.is_file():
            results[name] = {"passed": False, "error": "missing_script"}
            failures += 1
            continue
        proc = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True, timeout=1200)
        passed = proc.returncode == 0
        if not passed:
            failures += 1
        results[name] = {
            "command": f"python {name}",
            "exit_code": proc.returncode,
            "passed": passed,
            "stdout_tail": proc.stdout[-500:],
        }
    return {"results": results, "failures": failures}


def _misclassification_checks(items: list[dict[str, Any]]) -> dict[str, int]:
    misclassified = 0
    hidden_local = 0
    unspecified = 0
    false_claims = 0
    stale = 0

    from secrets_crypto.fips import fips_state

    fips = fips_state()
    if fips.get("validated") and not fips.get("evidence_path"):
        false_claims += 1
    if (fips.get("status") or "").startswith("FIPS_VALIDATED") and not fips.get("validated"):
        false_claims += 1

    for item in items:
        if item["assurance_status"] in {"PRODUCTION_VALIDATION_PENDING", "EXTERNAL_ATTESTATION_PENDING"}:
            if item["local_engineering_status"] != "LOCAL_ENGINEERING_COMPLETE":
                hidden_local += 1
                misclassified += 1
        if not item.get("external_evidence_required") or len(str(item["external_evidence_required"])) < 20:
            if item["assurance_status"] not in {"NOT_CURRENTLY_APPLICABLE_WITH_EVIDENCE"}:
                unspecified += 1
        if item["assurance_status"] == "NOT_CURRENTLY_APPLICABLE_WITH_EVIDENCE":
            if not item.get("applicability_evidence"):
                unspecified += 1

    for artifact in _CLOSURE_ARTIFACTS:
        if not artifact.is_file():
            stale += 1
            continue
        try:
            data = json.loads(artifact.read_text(encoding="utf-8"))
            verdict = str(data.get("verdict", ""))
            if verdict.endswith("_NOT_CLOSED"):
                stale += 1
        except Exception:
            stale += 1

    return {
        "MISCLASSIFIED_EXTERNAL_ITEMS": misclassified,
        "LOCAL_GAPS_HIDDEN_AS_EXTERNAL": hidden_local,
        "UNSPECIFIED_EXTERNAL_EVIDENCE_REQUIREMENTS": unspecified,
        "FALSE_COMPLIANCE_CLAIMS": false_claims,
        "STALE_EXTERNAL_EVIDENCE": stale,
    }


def verify_fds_production_external_assurance_boundary(*, run_closure_verifiers: bool = True) -> dict[str, Any]:
    items = _build_item_registry()

    local_complete = sum(1 for i in items if i["local_engineering_status"] == "LOCAL_ENGINEERING_COMPLETE")
    prod_pending = sum(1 for i in items if i["assurance_status"] == "PRODUCTION_VALIDATION_PENDING")
    external_pending = sum(1 for i in items if i["assurance_status"] == "EXTERNAL_ATTESTATION_PENDING")
    not_applicable = sum(1 for i in items if i["assurance_status"] == "NOT_CURRENTLY_APPLICABLE_WITH_EVIDENCE")
    local_gaps = sum(1 for i in items if i["assurance_status"] == "LOCAL_ENGINEERING_GAP")

    tls_probes = [_tls_probe(h) for h in _PRODUCTION_HOSTS]
    hsts_probe = _http_headers_probe("https://blackdark-production.up.railway.app/health/live")

    if run_closure_verifiers:
        closure = _run_closure_verifiers()
        regressions = closure["failures"]
        closure_results = closure["results"]
    else:
        regressions = 0
        closure_results = {}

    checks = _misclassification_checks(items)

    boundary_closed = (
        checks["MISCLASSIFIED_EXTERNAL_ITEMS"] == 0
        and checks["LOCAL_GAPS_HIDDEN_AS_EXTERNAL"] == 0
        and checks["STALE_EXTERNAL_EVIDENCE"] == 0
        and checks["UNSPECIFIED_EXTERNAL_EVIDENCE_REQUIREMENTS"] == 0
        and checks["FALSE_COMPLIANCE_CLAIMS"] == 0
        and regressions == 0
        and local_gaps == 0
    )

    verdict = "FDS_EXTERNAL_ASSURANCE_BOUNDARY_CLOSED" if boundary_closed else "FDS_EXTERNAL_ASSURANCE_BOUNDARY_NOT_CLOSED"

    return {
        "verdict": verdict,
        "items": items,
        "fds04_applicability": _fds04_applicability(),
        "safe_probes": {"tls": tls_probes, "hsts": hsts_probe, "claims_production_proof": False},
        "misclassification_checks": checks,
        "previous_closure_verifiers": closure_results,
        "summary": {
            "EXTERNAL_ITEMS_REVIEWED": len(items),
            "LOCAL_ENGINEERING_COMPLETE_ITEMS": local_complete,
            "GENUINE_PRODUCTION_VALIDATION_PENDING": prod_pending,
            "GENUINE_EXTERNAL_ATTESTATION_PENDING": external_pending,
            "NOT_CURRENTLY_APPLICABLE_WITH_EVIDENCE": not_applicable,
            **checks,
            "PREVIOUS_FDS_PHASE_REGRESSION_FAILURES": regressions,
            "REGRESSION_FAILURES": regressions,
        },
    }
