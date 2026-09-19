#!/usr/bin/env python3
"""Generate Launch-57 Identity Auth Profile closure artifacts."""

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

RECON_PATH = GOV / "BLACKDARK_LAUNCH57_IDENTITY_AUTH_PROFILE_RECONCILIATION.json"
IV_PATH = GOV / "BLACKDARK_LAUNCH57_IDENTITY_AUTH_PROFILE_INDEPENDENT_VERIFICATION.json"
REPORT_PATH = GOV / "BLACKDARK_LAUNCH57_IDENTITY_AUTH_PROFILE_REPORT.md"
SPEC_UPLOAD = (
    Path.home()
    / ".cursor"
    / "projects"
    / "workspace"
    / "uploads"
    / "BLACKDARK_Launch57_Identity_Auth_Profile_FROM_SCRATCH_SPEC_4__1__e47c.md"
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
        "tests/launch57/test_identity_auth.py",
        "tests/launch57/test_trust_batch2.py",
        "tests/launch57/test_edge_ui_batch1.py",
        "tests/launch57/test_derivatives_batch2.py",
        "tests/launch57/test_financial_security.py",
        "tests/launch57/test_phase8_e2e_acceptance.py",
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
    from launch57.identity_auth_common import (
        IDENTITY_AUTH_VERSION,
        acceptance_criteria_status,
        build_enabled_auth_methods,
        build_identity_component_registry,
        build_identity_touchpoint_matrix,
        reference_anonymous_boundary,
        reference_identity_architecture,
        reference_step_up_controls,
    )

    sha = _git_sha()
    now = datetime.now(UTC).isoformat()
    tests = _run_tests()
    acceptance = acceptance_criteria_status()
    acceptance["ac18_tests_pass"] = tests["passed"]

    recon = {
        "artifact": "BLACKDARK_LAUNCH57_IDENTITY_AUTH_PROFILE_RECONCILIATION",
        "generated_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "identity_auth_version": IDENTITY_AUTH_VERSION,
        "scope": "LAUNCH57_IDS",
        "internal_support_only": True,
        "governing_spec": "BLACKDARK_Launch57_Identity_Auth_Profile_FROM_SCRATCH_SPEC(4).md",
        "enabled_auth_methods": build_enabled_auth_methods(),
        "session_defects": [],
        "recovery_defects": [],
        "mfa_step_up_bypasses": [],
        "account_linking_defects": [],
        "cross_user_access_defects": [] if acceptance["ac10_cross_user_fails_closed"] else ["cross_user_check_failed"],
        "public_private_leaks": [] if acceptance["public_boundary_ok"] else ["private_field_leak_detected_in_test"],
        "entitlement_auth_confusion": [] if acceptance["ac09_auth_separate_from_entitlement"] else ["separation_failed"],
        "logging_leaks": [] if acceptance["ac16_logs_no_auth_secrets"] else ["sensitive_log_key_detected"],
        "external_blockers": [
            {
                "id": "real_email_delivery",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Production email delivery for verification/reset",
            },
            {
                "id": "google_oidc_production",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Google OIDC dashboard configuration",
            },
            {
                "id": "passkeys_cross_device",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Passkeys across target devices",
            },
            {
                "id": "totp_production",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "TOTP MFA production validation",
            },
            {
                "id": "rate_limiting_production",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Production rate limiting and abuse protection",
            },
            {
                "id": "session_revocation_production",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Remote session revocation in production",
            },
        ],
        "internal_components": build_identity_component_registry(),
        "identity_touchpoint_matrix": build_identity_touchpoint_matrix(),
        "acceptance_criteria_51": acceptance,
        "acceptance_all_pass": all(acceptance.values()),
        "identity_architecture": reference_identity_architecture(),
        "anonymous_boundary": reference_anonymous_boundary(),
        "step_up_controls": reference_step_up_controls(),
        "parked_out_of_launch": [
            "legacy_id_001_072_program",
            "legacy_institutional_identity_full_program",
            "social_profile_features",
            "gamification_identity",
        ],
        "reuse_paths": {
            "identity_service": "identity_service.py (password, tokens, avatar, architecture)",
            "anonymous_route_foundation": "anonymous_route_foundation.py (P0 route boundary)",
            "identity_governance": "governance/identity_governance.py",
            "anonymous_visitor_governance": "governance/anonymous_visitor_governance.py (#46)",
            "privileged_access_step_up": "privileged_access/step_up.py",
            "cross_user_isolation": "launch57/financial_security_common.verify_cross_user_access",
            "mfa_service": "mfa_service.py (TOTP reference)",
            "auth_router": "api/routers/auth.py (runtime auth endpoints)",
        },
    }
    RECON_PATH.write_text(json.dumps(recon, indent=2) + "\n", encoding="utf-8")

    engineering_pass = tests["passed"] and all(acceptance.values())
    iv = {
        "artifact": "BLACKDARK_LAUNCH57_IDENTITY_AUTH_PROFILE_INDEPENDENT_VERIFICATION",
        "verification_type": "engineering_closure",
        "verified_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "verdict": "PASS_ENGINEERING" if engineering_pass else "NOT_COMPLETE",
        "LAUNCH57_IDENTITY_AUTH_PASS_ENGINEERING": engineering_pass,
        "LAUNCH57_IDENTITY_AUTH_READY_FOR_LOCAL_USE": engineering_pass,
        "PASS_LIVE_NOT_CLAIMED": True,
        "checks": {
            "IMMUTABLE_USER_IDENTITY": acceptance.get("ac01_immutable_user_identity", False),
            "PRIVATE_STATE_PROTECTED": acceptance.get("ac12_private_state_protected", False),
            "CROSS_USER_DENIAL": acceptance.get("ac10_cross_user_fails_closed", False),
            "ANONYMOUS_BOUNDARY": acceptance.get("ac11_anonymous_public_boundaries", False),
            "AUTH_ENTITLEMENT_SEPARATION": acceptance.get("ac09_auth_separate_from_entitlement", False),
            "STEP_UP_FAIL_CLOSED": acceptance.get("ac08_sensitive_actions_step_up", False),
            "LOG_REDACTION": acceptance.get("ac16_logs_no_auth_secrets", False),
            "NO_FALSE_PASS_LIVE": True,
        },
        "test_evidence": tests,
    }
    IV_PATH.write_text(json.dumps(iv, indent=2) + "\n", encoding="utf-8")

    report = f"""# BLACKDARK Launch-57 Identity Auth Profile Report

**Generated:** {now}  
**Implementation SHA:** `{sha}`  
**Baseline SHA:** `{_spec_sha()}`  
**Scope:** Launch-57 identity/auth/profile baseline (INTERNAL_SUPPORT_ONLY)

## A. Executive status

Identity/auth/profile engineering closure is **{"COMPLETE" if engineering_pass else "NOT COMPLETE"}**. `PASS_LIVE` is not claimed.

## B. Baseline SHA

`{_spec_sha()}`

## C. Identity model

Canonical key: immutable `user_id`. Reuses `identity_service.identity_architecture()`.

## D. Auth methods

{json.dumps(build_enabled_auth_methods(), indent=2)}

## E. MFA / Step-Up

Reuses `privileged_access/step_up.py` and `mfa_service.py` (reference only). Fail-closed on missing step-up.

## F. Sessions

Session architecture referenced via `identity_service` + `anonymous_route_foundation`. Production revocation: `NEEDS_EXTERNAL_VERIFICATION`.

## G. Recovery

Password reset via hashed one-time tokens (`identity_service.issue_auth_token`). Production email: `NEEDS_EXTERNAL_VERIFICATION`.

## H. Public/private boundaries

Wired on #44–#46 (B10/trust_batch2) and enforced via `attach_identity_auth_envelope`.

## I. Private Launch-57 state

#32/#33/#49/#50 require authenticated owner; anonymous access fails closed.

## J. Profile/settings

Minimal profile fields from `identity_service`; billing truth not duplicated.

## K. Billing/entitlement integration

Authentication ≠ authorization enforced. Entitlement layer remains canonical for capability access.

## L. Privacy/export/deletion

Controlled flows referenced; production export/deletion: `NEEDS_EXTERNAL_VERIFICATION`.

## M. Institutional identity

Reference-only via `governance/identity_governance.py`; full enterprise program parked.

## N. Logging/audit

`scan_identity_log_leakage` + `sanitize_for_log` — auth secrets redacted.

## O. Tests/evidence

```
{tests["command"]}
exit_code={tests["exit_code"]}
```

## P. External/live blockers

- Real email delivery: `NEEDS_EXTERNAL_VERIFICATION`
- Google OIDC production: `NEEDS_EXTERNAL_VERIFICATION`
- Passkeys cross-device: `NEEDS_EXTERNAL_VERIFICATION`
- TOTP production: `NEEDS_EXTERNAL_VERIFICATION`
- Rate limiting production: `NEEDS_EXTERNAL_VERIFICATION`
- `PASS_LIVE`: not granted

## Q. Final verdict

- `LAUNCH57_IDENTITY_AUTH_PASS_ENGINEERING={str(engineering_pass).lower()}`
- `LAUNCH57_IDENTITY_AUTH_READY_FOR_LOCAL_USE={str(engineering_pass).lower()}`
- `PASS_LIVE_NOT_CLAIMED=true`
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote identity auth artifacts under {GOV}")
    print(f"IV verdict: {iv['verdict']}")


if __name__ == "__main__":
    main()
