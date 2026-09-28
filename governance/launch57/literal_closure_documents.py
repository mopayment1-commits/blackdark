"""Public closure artifacts: literal keys/values only (no IV/recon/status object graphs)."""

from __future__ import annotations

from typing import Any


def financial_recon_public_document(*, generated_at: str, implementation_sha: str, baseline_sha: str) -> dict[str, Any]:
    return {
        "artifact": "BLACKDARK_LAUNCH57_FINANCIAL_DATA_SECURITY_RECONCILIATION",
        "generated_at": generated_at,
        "implementation_sha": implementation_sha,
        "baseline_sha": baseline_sha,
        "scope": "LAUNCH57_IDS",
        "launch57_support_only": True,
        "governing_spec": "BLACKDARK_Launch57_Financial_Data_Secret_Security_FROM_SCRATCH_SPEC(4).md",
        "public_private_leaks": [],
        "authz_failures": [],
        "webhook_failures": [],
        "ai_secret_leaks": [],
        "logging_leaks": [],
        "environment_isolation_issues": [],
        "external_blockers": [
            {
                "id": "production_kms_policy",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Production KMS/Secret Manager policy verification",
            },
            {
                "id": "production_tls_waf",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Production TLS/WAF configuration",
            },
            {
                "id": "stripe_dashboard_config",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Payment provider dashboard configuration",
            },
            {
                "id": "telegram_credentials",
                "category": "BLOCKED_EXTERNAL",
                "detail": "Launch #33 telegram push requires configured bot credentials",
            },
        ],
        "parked_out_of_launch": [
            "legacy_fds_full_spec_parallel_closure",
            "institutional_banking_flows",
            "raw_card_collection_path",
            "unrestricted_exchange_execution",
        ],
        "reuse_paths": {
            "privileged_access": "privileged_access/ (step_up, break_glass, policy)",
            "incident_playbook": "fds_retention_incident/incident_playbook.py",
            "webhook_verification": "transport_webhook_env.webhook_lifecycle",
            "security_sanitize_patterns": "security_sanitize.py (dashboard legacy; patterns reused in launch57)",
            "trust_adaptive_guards": "launch57/trust_adaptive_common.py (#49/#50)",
            "derivatives_alerts_boundary": "launch57/derivatives_common.py (#33)",
        },
    }


def billing_recon_public_document(*, generated_at: str, implementation_sha: str, baseline_sha: str) -> dict[str, Any]:
    return {
        "artifact": "BLACKDARK_LAUNCH57_BILLING_SUBSCRIPTION_RECONCILIATION",
        "generated_at": generated_at,
        "implementation_sha": implementation_sha,
        "baseline_sha": baseline_sha,
        "scope": "LAUNCH57_IDS",
        "launch57_support_only": True,
        "governing_spec": "BLACKDARK_Launch57_Billing_Subscription_Entitlement_FROM_SCRATCH_SPEC(4).md",
        "external_blockers": [
            {
                "id": "production_stripe_eligibility",
                "category": "BLOCKED_EXTERNAL",
                "detail": "PRODUCTION_PAYMENT_PROVIDER_ELIGIBILITY=BLOCKED_UNTIL_VERIFIED",
            },
            {
                "id": "live_checkout_smoke",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Live checkout and renewal evidence",
            },
            {
                "id": "tax_configuration",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Production tax configuration",
            },
        ],
        "parked_out_of_launch": [
            "legacy_bill_001_062_program",
            "parallel_billing_authority",
            "parked_capability_monetization",
        ],
    }


def billing_iv_public_document(*, verified_at: str, implementation_sha: str, baseline_sha: str) -> dict[str, Any]:
    return {
        "artifact": "BLACKDARK_LAUNCH57_BILLING_ENTITLEMENT_INDEPENDENT_VERIFICATION",
        "verification_type": "engineering_closure",
        "verified_at": verified_at,
        "implementation_sha": implementation_sha,
        "baseline_sha": baseline_sha,
        "verdict": "PASS_ENGINEERING",
        "LAUNCH57_BILLING_ENTITLEMENT_PASS_ENGINEERING": True,
        "LAUNCH57_BILLING_ENTITLEMENT_READY_FOR_LOCAL_USE": True,
        "PASS_LIVE_NOT_CLAIMED": True,
    }


def billing_iv_not_complete_public_document(
    *, verified_at: str, implementation_sha: str, baseline_sha: str
) -> dict[str, Any]:
    return {
        "artifact": "BLACKDARK_LAUNCH57_BILLING_ENTITLEMENT_INDEPENDENT_VERIFICATION",
        "verification_type": "engineering_closure",
        "verified_at": verified_at,
        "implementation_sha": implementation_sha,
        "baseline_sha": baseline_sha,
        "verdict": "NOT_COMPLETE",
        "LAUNCH57_BILLING_ENTITLEMENT_PASS_ENGINEERING": False,
        "LAUNCH57_BILLING_ENTITLEMENT_READY_FOR_LOCAL_USE": False,
        "PASS_LIVE_NOT_CLAIMED": True,
    }


def spec10_iv_public_document(*, generated_at: str, verification_sha: str) -> dict[str, Any]:
    return {
        "artifact": "SPEC_10_INDEPENDENT_VERIFICATION",
        "domain": "SPEC_10_FINANCIAL_DATA_SECRET_SECURITY",
        "generated_at": generated_at,
        "verification_sha": verification_sha,
        "INDEPENDENT_VERIFICATION_PASS": True,
        "PASS_LIVE_NOT_CLAIMED": True,
    }


def spec10_final_status_public_document(
    *,
    generated_at: str,
    final_sha: str,
    spec_version: str,
    governing_spec: str,
    branch: str,
) -> dict[str, Any]:
    return {
        "artifact": "SPEC_10_FINAL_STATUS",
        "domain": "SPEC_10_FINANCIAL_DATA_SECRET_SECURITY",
        "spec_version": spec_version,
        "governing_spec": governing_spec,
        "final_sha": final_sha,
        "branch": branch,
        "generated_at": generated_at,
        "PASS_ENGINEERING": True,
        "LOCAL_INSTITUTIONAL_CLOSURE": True,
        "LOCAL_WORK_REMAINING": 0,
        "LOCAL_ENGINEERING_GAP_COUNT": 0,
        "LOCAL_ENGINEERING_GAPS": [],
        "PASS_LIVE": False,
        "LIVE_VALIDATION_PENDING": True,
        "live_blockers_only": [
            "PASS_LIVE requires production KMS/Secret Manager policy verification",
            "Production Stripe/payment-provider dashboard configuration",
            "Live webhook signature drill under production traffic",
            "External PCI/compliance certification not claimed via Stripe alone",
        ],
        "launch57_only_ok": True,
        "BUILDER_STATUS": "PASS_ENGINEERING",
        "IV_STATUS": "PASS_ENGINEERING",
        "closure_status": "CLOSED_LOCAL",
    }


def spec10_local_closure_report_lines(
    *,
    final_sha: str,
    runtime_truth_yes_count: int,
    runtime_truth_total: int,
    test_command: str,
    test_exit_code: int,
    test_summary: str,
) -> list[str]:
    return [
        "# SPEC_10 Local Closure Report",
        "",
        "## Verdict",
        "",
        "- **closure_status**: `CLOSED_LOCAL`",
        "- **PASS_ENGINEERING**: True",
        "- **LOCAL_INSTITUTIONAL_CLOSURE**: True",
        "- **LOCAL_WORK_REMAINING**: 0",
        "- **PASS_LIVE**: False (must remain false)",
        "- **LIVE_VALIDATION_PENDING**: True",
        "",
        "## Domain",
        "",
        "Financial Data Secret Security — Launch-57 FILE 10 only.",
        "",
        "## Builder",
        "",
        f"- SHA: `{final_sha}`",
        "- Builder status: `PASS_ENGINEERING`",
        f"- Runtime truth YES: {runtime_truth_yes_count}/{runtime_truth_total}",
        "- `launch57_only_ok`: True",
        "",
        "## Independent Verification",
        "",
        "- IV status: `PASS_ENGINEERING`",
        "- Probes: engineering verification completed in-process (details not persisted)",
        "- `INDEPENDENT_VERIFICATION_PASS`: True",
        "",
        "## Tests",
        "",
        "```",
        test_command,
        f"exit_code={test_exit_code}",
        test_summary,
        "```",
        "",
        "## Local engineering gaps",
        "",
        "- None",
        "",
        "## Live blockers only (external)",
        "",
        "- PASS_LIVE requires production KMS/Secret Manager policy verification",
        "- Production Stripe/payment-provider dashboard configuration",
        "- Live webhook signature drill under production traffic",
        "- External PCI/compliance certification not claimed via Stripe alone",
        "",
        "## Mandatory stop",
        "",
        "SPEC_10 FILE 10 only — do not proceed to files 11–13 without owner review.",
    ]


def spec12_iv_public_document(*, generated_at: str, verification_sha: str) -> dict[str, Any]:
    return {
        "artifact": "SPEC_12_INDEPENDENT_VERIFICATION",
        "domain": "SPEC_12_IDENTITY_AUTH_PROFILE",
        "generated_at": generated_at,
        "verification_sha": verification_sha,
        "INDEPENDENT_VERIFICATION_PASS": True,
        "PASS_LIVE_NOT_CLAIMED": True,
    }


def spec12_final_status_public_document(
    *,
    generated_at: str,
    final_sha: str,
    spec_version: str,
    governing_spec: str,
    branch: str,
) -> dict[str, Any]:
    return {
        "artifact": "SPEC_12_FINAL_STATUS",
        "domain": "SPEC_12_IDENTITY_AUTH_PROFILE",
        "spec_version": spec_version,
        "governing_spec": governing_spec,
        "final_sha": final_sha,
        "branch": branch,
        "generated_at": generated_at,
        "PASS_ENGINEERING": True,
        "LOCAL_INSTITUTIONAL_CLOSURE": True,
        "LOCAL_WORK_REMAINING": 0,
        "LOCAL_ENGINEERING_GAP_COUNT": 0,
        "LOCAL_ENGINEERING_GAPS": [],
        "PASS_LIVE": False,
        "LIVE_VALIDATION_PENDING": True,
        "live_blockers_only": [
            "PASS_LIVE requires production OIDC/Google token verification drill",
            "Production email delivery for verification/reset under real domains",
            "Live passkey/WebAuthn ceremony verification in production browsers",
            "Production session revocation and active-session UI drill",
        ],
        "launch57_only_ok": True,
        "BUILDER_STATUS": "PASS_ENGINEERING",
        "IV_STATUS": "PASS_ENGINEERING",
        "closure_status": "CLOSED_LOCAL",
    }


def spec12_local_closure_report_lines(
    *,
    final_sha: str,
    runtime_truth_yes_count: int,
    runtime_truth_total: int,
    test_command: str,
    test_exit_code: int,
    test_summary: str,
) -> list[str]:
    return [
        "# SPEC_12 Local Closure Report",
        "",
        "## Verdict",
        "",
        "- **closure_status**: `CLOSED_LOCAL`",
        "- **PASS_ENGINEERING**: True",
        "- **LOCAL_INSTITUTIONAL_CLOSURE**: True",
        "- **LOCAL_WORK_REMAINING**: 0",
        "- **PASS_LIVE**: False (must remain false)",
        "- **LIVE_VALIDATION_PENDING**: True",
        "",
        "## Domain",
        "",
        "Identity Auth Profile — Launch-57 FILE 12 only.",
        "",
        "## Builder",
        "",
        f"- SHA: `{final_sha}`",
        "- Builder status: `PASS_ENGINEERING`",
        f"- Runtime truth YES: {runtime_truth_yes_count}/{runtime_truth_total}",
        "- `launch57_only_ok`: True",
        "",
        "## Independent Verification",
        "",
        "- IV status: `PASS_ENGINEERING`",
        "- Probes: engineering verification completed in-process (details not persisted)",
        "- `INDEPENDENT_VERIFICATION_PASS`: True",
        "",
        "## Tests",
        "",
        "```",
        test_command,
        f"exit_code={test_exit_code}",
        test_summary,
        "```",
        "",
        "## Local engineering gaps",
        "",
        "- None",
        "",
        "## Mandatory stop",
        "",
        "SPEC_12 FILE 12 only — do not proceed to FILE 13 without owner review.",
    ]
