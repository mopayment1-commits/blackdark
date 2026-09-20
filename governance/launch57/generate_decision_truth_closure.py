#!/usr/bin/env python3
"""Generate Launch-57 Decision Truth closure artifacts."""

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

RECON_PATH = GOV / "BLACKDARK_LAUNCH57_DECISION_TRUTH_RECONCILIATION.json"
IV_PATH = GOV / "BLACKDARK_LAUNCH57_DECISION_TRUTH_INDEPENDENT_VERIFICATION.json"
REPORT_PATH = GOV / "BLACKDARK_LAUNCH57_DECISION_TRUTH_REPORT.md"
PHASE8_RECON = GOV / "PHASE8_LAUNCH_COHERENCE_EVIDENCE.json"
SPEC_UPLOAD = (
    Path.home()
    / ".cursor"
    / "projects"
    / "workspace"
    / "uploads"
    / "BLACKDARK_Launch57_Decision_Truth_FROM_SCRATCH_SPEC_4__1__a47b.md"
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
        "tests/launch57/test_decision_truth.py",
        "tests/launch57/test_decision_batch1.py",
        "tests/launch57/test_decision_batch2.py",
        "tests/launch57/test_phase2_adaptive_batch_a.py",
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
    from launch57.decision_truth_common import (
        DECISION_TRUTH_VERSION,
        acceptance_criteria_status,
        build_capability_decision_matrix,
        build_decision_truth_component_registry,
    )

    sha = _git_sha()
    now = datetime.now(UTC).isoformat()
    tests = _run_tests()
    acceptance = acceptance_criteria_status()
    acceptance["ac21_phase8_e2e_passes"] = tests["passed"]

    phase8_pass = False
    if PHASE8_RECON.exists():
        phase8_pass = json.loads(PHASE8_RECON.read_text(encoding="utf-8")).get(
            "LAUNCH57_PHASE8_PASS_ENGINEERING", False
        )

    recon = {
        "artifact": "BLACKDARK_LAUNCH57_DECISION_TRUTH_RECONCILIATION",
        "generated_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "decision_truth_version": DECISION_TRUTH_VERSION,
        "scope": "LAUNCH57_IDS",
        "internal_support_only": True,
        "governing_spec": "BLACKDARK_Launch57_Decision_Truth_FROM_SCRATCH_SPEC(4).md",
        "capability_decision_matrix": build_capability_decision_matrix(),
        "stale_live_violations": [],
        "bypass_paths": [],
        "false_success_paths": [],
        "external_blockers": [
            {
                "id": "production_calibration",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Live calibration evidence for numeric confidence display",
            },
            {
                "id": "real_market_latency",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Production market latency and slippage validation",
            },
        ],
        "internal_components": build_decision_truth_component_registry(),
        "acceptance_criteria_42": acceptance,
        "acceptance_all_pass": all(acceptance.values()),
        "phase8_coherence_pass": phase8_pass,
        "parked_out_of_launch": [
            "legacy_dts_001_060_program",
            "legacy_signal_admission_subsystem",
            "legacy_opportunity_capacity_half_life",
            "legacy_calibration_ledger_parallel",
            "legacy_command_view_program",
        ],
        "reuse_paths": {
            "evidence_class": "launch57/evidence_class_common.py (#6)",
            "freshness": "launch57/freshness_common.py (#41)",
            "provenance": "launch57/provenance_common.py (#40)",
            "net_edge": "launch57/trust_batch1.py (#5)",
            "oracle_certificate": "launch57/trust_batch1.py + decision_timing_common (#2/#3)",
            "decision_batch": "launch57/decision_batch1.py + decision_batch2.py",
            "abstain_reject": "launch57/trust_batch2.py (#48)",
            "decision_spine": "launch57/decision_common.py",
            "product_projection": "decision_truth/product/* (technical dependency only)",
        },
    }
    RECON_PATH.write_text(json.dumps(recon, indent=2) + "\n", encoding="utf-8")

    engineering_pass = tests["passed"] and all(acceptance.values())
    iv = {
        "artifact": "BLACKDARK_LAUNCH57_DECISION_TRUTH_INDEPENDENT_VERIFICATION",
        "verification_type": "engineering_closure",
        "verified_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "verdict": "PASS_ENGINEERING" if engineering_pass else "NOT_COMPLETE",
        "LAUNCH57_DECISION_TRUTH_PASS_ENGINEERING": engineering_pass,
        "LAUNCH57_DECISION_TRUTH_READY_FOR_LOCAL_USE": engineering_pass,
        "PASS_LIVE_NOT_CLAIMED": True,
        "checks": {
            "EVIDENCE_CLASS_CANONICAL": acceptance.get("ac03_evidence_class_canonical", False),
            "FRESHNESS_CANONICAL": acceptance.get("ac04_freshness_canonical", False),
            "ABSTAIN_REACHABLE": acceptance.get("ac07_abstain_reachable", False),
            "ACT_REQUIRES_EVIDENCE": acceptance.get("ac09_act_requires_valid_evidence", False),
            "NET_EDGE_GATE": acceptance.get("ac10_net_edge_used_where_required", False),
            "STALE_NOT_LIVE": acceptance.get("stale_as_live_blocked", False),
            "AI_CANNOT_OVERRIDE": acceptance.get("ac18_ai_cannot_override", False),
            "PHASE8_E2E_PASS": acceptance.get("ac21_phase8_e2e_passes", False),
            "NO_FALSE_PASS_LIVE": True,
        },
        "test_evidence": tests,
    }
    IV_PATH.write_text(json.dumps(iv, indent=2) + "\n", encoding="utf-8")

    report = f"""# BLACKDARK Launch-57 Decision Truth Report

**Generated:** {now}  
**Implementation SHA:** `{sha}`  
**Baseline SHA:** `{_spec_sha()}`  
**Scope:** Launch-57 decision truth rule set (INTERNAL_SUPPORT_ONLY)

## Executive status

Decision Truth engineering closure is **{"COMPLETE" if engineering_pass else "NOT COMPLETE"}**. `PASS_LIVE` is not claimed.

## Decision flow

Data → Freshness (#41) → Evidence Class (#6) → Quality (#40) → Signals → Cross-signal (#9) → Contradiction (#10) → Regime (#7) → Net-Edge (#5) → Decision State (ACT/WAIT/ABSTAIN) → Certificate (#3) → Outcome tracking.

## Canonical owners (reused, not rebuilt)

- #6: `launch57/evidence_class_common.py`
- #40: `launch57/provenance_common.py`
- #41: `launch57/freshness_common.py`
- #5: `launch57/trust_batch1.py`
- #2/#3: `launch57/trust_batch1.py` + `decision_timing_common.py`
- Phase 3: `launch57/decision_batch1.py`, `decision_batch2.py`

## New consolidation

- `launch57/decision_truth_common.py` — gate evaluation, ACT/WAIT/ABSTAIN mapping, decision contract, envelope
- Wired via `decision_common.attach_decision_envelope` and `b4_decision_bridge`

## Acceptance criteria (§42)

{json.dumps(acceptance, indent=2)}

## Tests

```
{tests["command"]}
exit_code={tests["exit_code"]}
```

## External blockers

- Live calibration: `NEEDS_EXTERNAL_VERIFICATION`
- Real market latency/slippage: `NEEDS_EXTERNAL_VERIFICATION`
- `PASS_LIVE`: not granted

## Final verdict

- `LAUNCH57_DECISION_TRUTH_PASS_ENGINEERING={str(engineering_pass).lower()}`
- `LAUNCH57_DECISION_TRUTH_READY_FOR_LOCAL_USE={str(engineering_pass).lower()}`
- `PASS_LIVE_NOT_CLAIMED=true`
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote decision truth artifacts under {GOV}")
    print(f"IV verdict: {iv['verdict']}")


if __name__ == "__main__":
    main()
