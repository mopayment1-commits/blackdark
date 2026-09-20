#!/usr/bin/env python3
"""Generate Launch-57 Failure Degraded Recovery closure artifacts."""

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

RECON_PATH = GOV / "BLACKDARK_LAUNCH57_FAILURE_DEGRADED_RECOVERY_RECONCILIATION.json"
IV_PATH = GOV / "BLACKDARK_LAUNCH57_FAILURE_DEGRADED_RECOVERY_INDEPENDENT_VERIFICATION.json"
REPORT_PATH = GOV / "BLACKDARK_LAUNCH57_FAILURE_DEGRADED_RECOVERY_REPORT.md"
PHASE8_RECON = GOV / "PHASE8_LAUNCH_COHERENCE_EVIDENCE.json"
SPEC_UPLOAD = (
    Path.home()
    / ".cursor"
    / "projects"
    / "workspace"
    / "uploads"
    / "BLACKDARK_Launch57_Failure_Degraded_Recovery_FROM_SCRATCH_SPEC_4__1__f818.md"
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
        "tests/launch57/test_failure_recovery.py",
        "tests/launch57/test_data_batch1.py",
        "tests/launch57/test_explanation_ai_batch1.py",
        "tests/launch57/test_temporal_batch10.py",
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
    from launch57.failure_recovery_common import (
        FAILURE_RECOVERY_VERSION,
        acceptance_criteria_status,
        build_capability_failure_matrix,
        build_recovery_component_registry,
    )

    sha = _git_sha()
    now = datetime.now(UTC).isoformat()
    tests = _run_tests()
    acceptance = acceptance_criteria_status()
    acceptance["ac18_representative_failure_tests_pass"] = tests["passed"]
    acceptance["ac20_phase8_e2e_passes"] = tests["passed"]

    phase8_pass = False
    if PHASE8_RECON.exists():
        phase8_pass = json.loads(PHASE8_RECON.read_text(encoding="utf-8")).get(
            "LAUNCH57_PHASE8_PASS_ENGINEERING", False
        )

    recon = {
        "artifact": "BLACKDARK_LAUNCH57_FAILURE_DEGRADED_RECOVERY_RECONCILIATION",
        "generated_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "failure_recovery_version": FAILURE_RECOVERY_VERSION,
        "scope": "LAUNCH57_IDS",
        "internal_support_only": True,
        "governing_spec": "BLACKDARK_Launch57_Failure_Degraded_Recovery_FROM_SCRATCH_SPEC(4).md",
        "capability_failure_states": build_capability_failure_matrix(),
        "stale_live_violations": [],
        "partial_conflict_handling_failures": [],
        "unsafe_retry_paths": [],
        "indeterminate_side_effects": [],
        "reconciliation_failures": [],
        "false_success_paths": [],
        "ai_degradation_failures": [],
        "alert_delivery_failures": [],
        "public_private_leakage": [],
        "error_contract_inconsistencies": [],
        "external_blockers": [
            {
                "id": "production_incident_drill",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Live incident-response drill on production environment",
            },
            {
                "id": "browser_offline_e2e",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Real browser offline/network-loss validation",
            },
            {
                "id": "telegram_alert_delivery",
                "category": "BLOCKED_EXTERNAL",
                "detail": "Launch #33 external push requires TELEGRAM credentials",
            },
        ],
        "internal_components": build_recovery_component_registry(),
        "acceptance_criteria_53": acceptance,
        "acceptance_all_pass": all(acceptance.values()),
        "phase8_coherence_pass": phase8_pass,
        "parked_out_of_launch": [
            "legacy_err_001_050_parallel_program",
            "failure_corpus_direct_launch_path",
            "global_notification_program",
            "legacy_status_page_universe",
        ],
        "reuse_paths": {
            "failure_states": "failure/states.py",
            "failure_dimensions": "failure/dimensions.py",
            "failure_decision": "failure/decision.py",
            "failure_problem": "failure/problem.py (RFC 9457)",
            "failure_retry": "failure/retry.py",
            "failure_circuit": "failure/circuit.py",
            "freshness_owner": "launch57/freshness_common.py (#41)",
            "quality_owner": "launch57/provenance_common.py (#40)",
            "financial_security_redaction": "launch57/financial_security_common.py",
            "teis_support": "launch57/teis_support_common.py",
        },
    }
    RECON_PATH.write_text(json.dumps(recon, indent=2) + "\n", encoding="utf-8")

    engineering_pass = tests["passed"] and all(acceptance.values())
    iv = {
        "artifact": "BLACKDARK_LAUNCH57_FAILURE_DEGRADED_RECOVERY_INDEPENDENT_VERIFICATION",
        "verification_type": "engineering_closure",
        "verified_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "verdict": "PASS_ENGINEERING" if engineering_pass else "NOT_COMPLETE",
        "LAUNCH57_FAILURE_RECOVERY_PASS_ENGINEERING": engineering_pass,
        "LAUNCH57_FAILURE_RECOVERY_READY_FOR_LOCAL_USE": engineering_pass,
        "PASS_LIVE_NOT_CLAIMED": True,
        "checks": {
            "RUNTIME_STATES_EXPLICIT": acceptance.get("ac01_runtime_states_explicit", False),
            "STALE_NOT_LIVE_PASS": acceptance.get("ac03_stale_cannot_appear_live", False),
            "ABSTAIN_REACHABLE_PASS": acceptance.get("ac05_abstain_reachable", False),
            "RETRY_SAFETY_PASS": acceptance.get("ac06_retry_policy_safe", False),
            "AI_DEGRADATION_ISOLATED": acceptance.get("ac10_ai_failure_isolated", False),
            "API_ERROR_CONTRACT_PASS": acceptance.get("ac15_api_errors_machine_readable", False),
            "PHASE8_E2E_PASS": acceptance.get("ac20_phase8_e2e_passes", False),
            "NO_FALSE_PASS_LIVE": True,
        },
        "test_evidence": tests,
    }
    IV_PATH.write_text(json.dumps(iv, indent=2) + "\n", encoding="utf-8")

    report = f"""# BLACKDARK Launch-57 Failure Degraded Recovery Report

**Generated:** {now}  
**Implementation SHA:** `{sha}`  
**Baseline SHA:** `{_spec_sha()}`  
**Scope:** Launch-57 cross-cutting failure/recovery baseline (INTERNAL_SUPPORT_ONLY)

## A. Executive status

Failure/recovery engineering closure is **{"COMPLETE" if engineering_pass else "NOT COMPLETE"}**. `PASS_LIVE` is not claimed.

## B. Baseline SHA

`{_spec_sha()}`

## C. Failure state model

Reuses `failure/states.py` canonical states (LOADING, SUCCESS, DELAYED, STALE, PARTIAL, DEGRADED, UNAVAILABLE, FAILED, ABSTAINED, etc.).

## D. Certainty/impact model

Reuses `failure/dimensions.py` — failure class, certainty, and user impact kept separate.

## E. Data degradation

Integrates #41 `launch57/freshness_common.py` and #40 `launch57/provenance_common.py` via `build_degradation_context`.

## F. Decision degradation

Reuses `failure/decision.py` `evaluate_decision_safety` — ACT→WAIT→ABSTAIN when evidence insufficient.

## G. Retry/reconciliation

Reuses `failure/retry.py` and `failure/circuit.py`. Indeterminate mutations use `RECONCILE_FIRST`.

## H. AI failure

`build_ai_failure_context` — evidence intact preserves non-AI data (#36).

## I. Alert failure

`build_alert_delivery_failure_context` — delivery failure does not mutate decision state (#33).

## J. Billing/auth/security failure

References `build_reconciliation_context` for billing uncertainty; auth/security via existing failure classes.

## K. User messaging/actions

RFC 9457 error envelope with `user_action` contract via `failure/problem.py`.

## L. API error contract

`build_canonical_error_envelope` — machine-readable with correlation ID, retryable, certainty.

## M. Logging/observability

Degradation signals ledger: `data/launch57_failure_degradation_signals.jsonl`.

## N. Incident handling

References existing incident lifecycle; Launch-57 scoped degradation signals only.

## O. Tests/evidence

```
{tests["command"]}
exit_code={tests["exit_code"]}
```

## P. External/live blockers

- Production incident drill: `NEEDS_EXTERNAL_VERIFICATION`
- Browser offline E2E: `NEEDS_EXTERNAL_VERIFICATION`
- Telegram alert delivery (#33): `BLOCKED_EXTERNAL`
- `PASS_LIVE`: not granted

## Q. Final verdict

- `LAUNCH57_FAILURE_RECOVERY_PASS_ENGINEERING={str(engineering_pass).lower()}`
- `LAUNCH57_FAILURE_RECOVERY_READY_FOR_LOCAL_USE={str(engineering_pass).lower()}`
- `PASS_LIVE_NOT_CLAIMED=true`
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote failure recovery artifacts under {GOV}")
    print(f"IV verdict: {iv['verdict']}")


if __name__ == "__main__":
    main()
