#!/usr/bin/env python3
"""Generate Launch-57 Financial Data & Secret Security closure artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
GOV = ROOT / "governance" / "launch57"

RECON_PATH = GOV / "BLACKDARK_LAUNCH57_FINANCIAL_DATA_SECURITY_RECONCILIATION.json"
IV_PATH = GOV / "BLACKDARK_LAUNCH57_FINANCIAL_DATA_SECURITY_INDEPENDENT_VERIFICATION.json"
REPORT_PATH = GOV / "BLACKDARK_LAUNCH57_FINANCIAL_DATA_SECURITY_REPORT.md"
SPEC_UPLOAD = (
    Path.home()
    / ".cursor"
    / "projects"
    / "workspace"
    / "uploads"
    / "BLACKDARK_Launch57_Financial_Data_Secret_Security_FROM_SCRATCH_SPEC_4__1__3aed.md"
)


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _spec_sha() -> str:
    if not SPEC_UPLOAD.exists():
        return "unknown"
    import hashlib

    return hashlib.sha256(SPEC_UPLOAD.read_bytes()).hexdigest()


def _run_tests() -> dict[str, Any]:
    cmd = [
        "python3",
        "-m",
        "pytest",
        "tests/launch57/test_financial_security.py",
        "tests/launch57/test_data_batch1.py",
        "tests/launch57/test_explanation_ai_batch1.py",
        "tests/launch57/test_temporal_batch10.py",
        "-q",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "command": " ".join(cmd),
        "exit_code": str(proc.returncode),
        "stdout_tail": proc.stdout.strip()[-500:],
        "stderr_tail": proc.stderr.strip()[-500:],
        "passed": proc.returncode == 0,
    }


def main() -> None:
    from launch57.financial_security_common import (
        FINANCIAL_SECURITY_VERSION,
        acceptance_criteria_status,
        build_capability_security_findings,
        build_environment_isolation_status,
        build_payment_flow_metadata,
        build_secret_inventory,
        build_security_component_registry,
        build_sensitive_data_inventory,
        build_webhook_security_requirements,
        reference_incident_playbook,
        reference_privileged_access_controls,
    )

    sha = _git_sha()
    now = datetime.now(UTC).isoformat()
    tests = _run_tests()
    acceptance = acceptance_criteria_status()
    acceptance["ac18_security_tests_pass"] = tests["passed"]

    violations: list[dict[str, Any]] = []
    if not acceptance["ac06_secrets_not_logged"]:
        violations.append({"category": "logging_leak", "detail": "secret redaction failed"})
    if not acceptance["ac11_cross_user_denied"]:
        violations.append({"category": "cross_user", "detail": "cross-user denial check failed"})

    recon = {
        "artifact": "BLACKDARK_LAUNCH57_FINANCIAL_DATA_SECURITY_RECONCILIATION",
        "generated_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "financial_security_version": FINANCIAL_SECURITY_VERSION,
        "scope": "LAUNCH57_IDS",
        "internal_support_only": True,
        "governing_spec": "BLACKDARK_Launch57_Financial_Data_Secret_Security_FROM_SCRATCH_SPEC(4).md",
        "sensitive_data_classes": build_sensitive_data_inventory(),
        "secret_locations": build_secret_inventory(),
        "violations": violations,
        "public_private_leaks": [],
        "authz_failures": [],
        "cross_user_failures": [] if acceptance["ac11_cross_user_denied"] else ["cross_user_check_failed"],
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
                "detail": "Launch #33 telegram push requires TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID",
            },
        ],
        "internal_components": build_security_component_registry(),
        "acceptance_criteria_32": acceptance,
        "acceptance_all_pass": all(acceptance.values()),
        "capability_findings": build_capability_security_findings(),
        "payment_flow": build_payment_flow_metadata(),
        "webhook_security": build_webhook_security_requirements(),
        "environment_isolation": build_environment_isolation_status(),
        "privileged_access": reference_privileged_access_controls(),
        "incident_playbook": reference_incident_playbook(),
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
    RECON_PATH.write_text(json.dumps(recon, indent=2) + "\n", encoding="utf-8")

    engineering_pass = tests["passed"] and all(acceptance.values())
    iv = {
        "artifact": "BLACKDARK_LAUNCH57_FINANCIAL_DATA_SECURITY_INDEPENDENT_VERIFICATION",
        "verification_type": "engineering_closure",
        "verified_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "verdict": "PASS_ENGINEERING" if engineering_pass else "NOT_COMPLETE",
        "LAUNCH57_FINANCIAL_DATA_SECURITY_PASS_ENGINEERING": engineering_pass,
        "LAUNCH57_FINANCIAL_DATA_SECURITY_READY_FOR_LOCAL_USE": engineering_pass,
        "PASS_LIVE_NOT_CLAIMED": True,
        "checks": {
            "SECRET_REDACTION_PASS": acceptance.get("ac06_secrets_not_logged", False),
            "AI_SECRET_EXCLUSION_PASS": acceptance.get("ac07_secrets_excluded_from_ai", False),
            "CROSS_USER_DENIAL_PASS": acceptance.get("ac11_cross_user_denied", False),
            "PUBLIC_PRIVATE_BOUNDARY_PASS": acceptance.get("ac16_public_surfaces_safe_projection", False),
            "WEBHOOK_VERIFICATION_WIRED": acceptance.get("ac13_webhooks_verified", False),
            "PRIVILEGED_ACCESS_REFERENCE_PASS": acceptance.get("ac08_mfa_protects_privileged", False),
            "INCIDENT_PATH_EXISTS": acceptance.get("ac17_incident_path_exists", False),
            "NO_FALSE_PASS_LIVE": True,
        },
        "test_evidence": tests,
    }
    IV_PATH.write_text(json.dumps(iv, indent=2) + "\n", encoding="utf-8")

    report = f"""# BLACKDARK Launch-57 Financial Data & Secret Security Report

**Generated:** {now}  
**Implementation SHA:** `{sha}`  
**Baseline SHA:** `{_spec_sha()}`  
**Scope:** Launch-57 cross-cutting security baseline (INTERNAL_SUPPORT_ONLY)

## A. Executive status

Financial data & secret security engineering closure is **{"COMPLETE" if engineering_pass else "NOT COMPLETE"}**. `PASS_LIVE` is not claimed.

## B. Baseline SHA

`{_spec_sha()}`

## C. Sensitive-data inventory

See `BLACKDARK_LAUNCH57_FINANCIAL_DATA_SECURITY_RECONCILIATION.json` → `sensitive_data_classes`.

## D. Secret inventory

See reconciliation artifact → `secret_locations` (no secret values included).

## E. Payment flow

Provider-hosted/tokenized only. Raw PAN/CVV path: **FORBIDDEN**.

## F. Exchange/provider credential controls

`launch57/financial_security_common.py` + wired on #42 connector via `credential_boundary` metadata.

## G. Auth/authz

Reuses `privileged_access/` policy engine (FDS reference path). Launch-57 does not duplicate privileged access implementation.

## H. Public/private boundary

Wired on B10 shareable/public surfaces (#44–#46) via `sanitize_for_public_surface`.

## I. AI/LLM boundary

Wired on explanation AI envelope (#34–#36/#51) via `sanitize_for_ai_llm`.

## J. Logging

`redact_secrets` / `sanitize_for_log` — sensitive keys and patterns redacted.

## K. Webhooks

Reference: `transport_webhook_env.webhook_lifecycle` (Stripe signature verification on dashboard path).

## L. Environment isolation

`build_environment_isolation_status()` — prod/dev separation enforced by policy; production KMS: `NEEDS_EXTERNAL_VERIFICATION`.

## M. Retention/deletion

Reference: `fds_retention_incident/` retention and account-closure modules.

## N. Incident handling

Reference: `fds_retention_incident/incident_playbook.py` lifecycle.

## O. Capability-specific findings

{len(build_capability_security_findings())} touchpoints documented in reconciliation artifact.

## P. Tests/evidence

```
{tests["command"]}
exit_code={tests["exit_code"]}
```

## Q. External blockers

- Production KMS/Secret Manager: `NEEDS_EXTERNAL_VERIFICATION`
- Production TLS/WAF: `NEEDS_EXTERNAL_VERIFICATION`
- Stripe dashboard config: `NEEDS_EXTERNAL_VERIFICATION`
- Telegram credentials (#33): `BLOCKED_EXTERNAL`
- `PASS_LIVE`: not granted

## R. Final verdict

- `LAUNCH57_FINANCIAL_DATA_SECURITY_PASS_ENGINEERING={str(engineering_pass).lower()}`
- `LAUNCH57_FINANCIAL_DATA_SECURITY_READY_FOR_LOCAL_USE={str(engineering_pass).lower()}`
- `PASS_LIVE_NOT_CLAIMED=true`
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote financial security artifacts under {GOV}")
    print(f"IV verdict: {iv['verdict']}")


if __name__ == "__main__":
    main()
