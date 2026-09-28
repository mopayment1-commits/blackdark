#!/usr/bin/env python3
"""Generate Launch-57 Billing Entitlement closure artifacts."""

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

from governance.launch57.gov_io import write_artifact_lines
GOV = ROOT / "governance" / "launch57"

RECON_PATH = GOV / "BLACKDARK_LAUNCH57_BILLING_ENTITLEMENT_RECONCILIATION.json"
IV_PATH = GOV / "BLACKDARK_LAUNCH57_BILLING_ENTITLEMENT_INDEPENDENT_VERIFICATION.json"
REPORT_PATH = GOV / "BLACKDARK_LAUNCH57_BILLING_ENTITLEMENT_REPORT.md"
SPEC_UPLOAD = (
    Path.home()
    / ".cursor"
    / "projects"
    / "workspace"
    / "uploads"
    / "BLACKDARK_Launch57_Billing_Subscription_Entitlement_FROM_SCRATCH_SPEC_4__1__8540.md"
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
        "tests/launch57/test_billing_entitlement.py",
        "tests/launch57/test_identity_auth.py",
        "tests/launch57/test_edge_ui_batch1.py",
        "tests/launch57/test_derivatives_batch2.py",
        "tests/launch57/test_trust_batch2.py",
        "tests/launch57/test_financial_security.py",
        "tests/launch57/test_failure_recovery.py",
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
    from launch57.billing_entitlement_common import (
        BILLING_ENTITLEMENT_VERSION,
        acceptance_criteria_status,
        build_billing_component_registry,
        build_billing_touchpoint_matrix,
        reference_billing_governance,
        reference_plan_registry,
        reference_subscription_engine,
        reference_webhook_pipeline,
    )

    sha = _git_sha()
    now = datetime.now(UTC).isoformat()
    tests = _run_tests()
    acceptance = acceptance_criteria_status()
    acceptance["ac18_tests_pass"] = tests["passed"]

    # Internal-only engineering checks (results are not written to public artifacts).
    _ = BILLING_ENTITLEMENT_VERSION
    _ = reference_plan_registry()
    _ = build_billing_component_registry()
    _ = build_billing_touchpoint_matrix()
    _ = reference_subscription_engine()
    _ = reference_webhook_pipeline()
    _ = reference_billing_governance()

    baseline_sha = _spec_sha()
    engineering_pass = tests["passed"] and all(acceptance.values())
    if engineering_pass:
        subprocess.run(
            [sys.executable, "-m", "governance.launch57.emit_billing_public_artifacts", "pass"],
            cwd=ROOT,
            check=True,
        )
    else:
        subprocess.run(
            [sys.executable, "-m", "governance.launch57.emit_billing_public_artifacts", "fail"],
            cwd=ROOT,
            check=True,
        )
    iv_verdict = "PASS_ENGINEERING" if engineering_pass else "NOT_COMPLETE"

    report = f"""# BLACKDARK Launch-57 Billing Entitlement Report

**Generated:** {now}  
**Implementation SHA:** `{sha}`  
**Baseline SHA:** `{_spec_sha()}`  
**Scope:** Launch-57 billing/subscription/entitlement baseline (INTERNAL_SUPPORT_ONLY)

## A. Executive status

Billing/entitlement engineering closure is **{"COMPLETE" if engineering_pass else "NOT COMPLETE"}**. `PASS_LIVE` is not claimed.

## B. Baseline SHA

`{_spec_sha()}`

## C. Current tier registry

Reuses `billing/plan_registry.py` — FREE, PRO, ELITE, QUANT, INSTITUTIONAL.

## D. Billing state model

Referenced via `billing/subscription_engine.py`; separate from entitlement state.

## E. Entitlement state model

`effective_plan` + `entitlement_allowed` — no webhook→tier shortcut.

## F. Checkout/payment proof

`billing_service.create_checkout_session` — hosted provider only; redirect cannot grant access.

## G. Renewal/recovery

Subscription engine lifecycle + grace policy; production renewal: `NEEDS_EXTERNAL_VERIFICATION`.

## H. Upgrade/downgrade/cancel

Handled by `billing/subscription_engine.py`; idempotent webhook processing.

## I. Refund/dispute

Engine tracks `REVOKED_PAYMENT_STATUSES`; entitlement revoked on financial reversal.

## J. Reconciliation

`failure_recovery_common.build_reconciliation_context` — no grant from uncertain state.

## K. Tier variables

Separate from capability identity per touchpoint (#32–#33, #46, #49–#52).

## L. Capability enforcement

`verify_capability_entitlement` — server-side, Launch-57 scope only.

## M. Institutional billing

Reference: `billing/institutional_activation.py`; full B2B program parked unless contracted.

## N. Security

Webhook signature via `transport_webhook_env`; payment security via `financial_security_common`.

## O. Observability

Billing audit ledger + signal store `launch57_billing_entitlement_signals.jsonl`.

## P. Tests

```
{tests["command"]}
exit_code={tests["exit_code"]}
```

## Q. External/live blockers

- Production provider eligibility: `BLOCKED_EXTERNAL`
- Live webhook/checkout: `NEEDS_EXTERNAL_VERIFICATION`
- `PASS_LIVE`: not granted

## R. Final verdict

- `LAUNCH57_BILLING_ENTITLEMENT_PASS_ENGINEERING={str(engineering_pass).lower()}`
- `LAUNCH57_BILLING_ENTITLEMENT_READY_FOR_LOCAL_USE={str(engineering_pass).lower()}`
- `PASS_LIVE_NOT_CLAIMED=true`
"""
    write_artifact_lines(REPORT_PATH, report.splitlines())
    print(f"Wrote billing entitlement artifacts under {GOV}")
    print(f"IV verdict: {iv_verdict}")


if __name__ == "__main__":
    main()
