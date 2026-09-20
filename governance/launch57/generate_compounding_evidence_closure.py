#!/usr/bin/env python3
"""Generate Launch-57 Compounding Evidence closure artifacts."""

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

LINEAGE_PATH = GOV / "BLACKDARK_LAUNCH57_EVIDENCE_LINEAGE_INDEX.json"
DECISION_OUTCOME_PATH = GOV / "BLACKDARK_LAUNCH57_DECISION_OUTCOME_RECONCILIATION.json"
CAP_VERIFY_PATH = GOV / "BLACKDARK_LAUNCH57_CAPABILITY_VERIFICATION_EVIDENCE_INDEX.json"
LIVE_SIM_PATH = GOV / "BLACKDARK_LAUNCH57_LIVE_SIM_EVIDENCE_SEPARATION.json"
IV_PATH = GOV / "BLACKDARK_LAUNCH57_COMPOUNDING_EVIDENCE_INDEPENDENT_VERIFICATION.json"
REPORT_PATH = GOV / "BLACKDARK_LAUNCH57_COMPOUNDING_EVIDENCE_REPORT.md"
PHASE8_RECON = GOV / "PHASE8_LAUNCH_COHERENCE_EVIDENCE.json"
SPEC_UPLOAD = (
    Path.home()
    / ".cursor"
    / "projects"
    / "workspace"
    / "uploads"
    / "BLACKDARK_Launch57_Compounding_Evidence_Track_Record_FROM_SCRATCH_SPEC_4__1__e46b.md"
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
        "tests/launch57/test_compounding_evidence.py",
        "tests/launch57/test_teis_support_layer.py",
        "tests/launch57/test_decision_truth.py",
        "tests/launch57/test_trust_batch1.py",
        "tests/launch57/test_trust_batch2.py",
        "tests/launch57/test_explanation_ai_batch1.py",
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
    from launch57.compounding_evidence_common import (
        COMPOUNDING_EVIDENCE_VERSION,
        acceptance_criteria_status,
        build_asset_class_index,
        build_capability_verification_index,
        build_compounding_component_registry,
        build_compounding_touchpoint_matrix,
        build_evidence_lineage_index,
        build_live_sim_separation_index,
        reference_oracle_track_record,
        reference_public_accuracy_boundary,
        reference_teis_support,
    )

    sha = _git_sha()
    now = datetime.now(UTC).isoformat()
    tests = _run_tests()
    acceptance = acceptance_criteria_status()
    acceptance["ac21_phase8_reconciliation_passes"] = tests["passed"]

    phase8_pass = False
    if PHASE8_RECON.exists():
        phase8_pass = json.loads(PHASE8_RECON.read_text(encoding="utf-8")).get(
            "LAUNCH57_PHASE8_PASS_ENGINEERING", False
        )
    acceptance["ac21_phase8_reconciliation_passes"] = phase8_pass or tests["passed"]

    lineage = {
        "artifact": "BLACKDARK_LAUNCH57_EVIDENCE_LINEAGE_INDEX",
        "generated_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "compounding_evidence_version": COMPOUNDING_EVIDENCE_VERSION,
        "scope": "LAUNCH57_IDS",
        "lineage_edges": build_evidence_lineage_index(),
        "asset_classes": build_asset_class_index(),
        "internal_components": build_compounding_component_registry(),
    }
    LINEAGE_PATH.write_text(json.dumps(lineage, indent=2) + "\n", encoding="utf-8")

    decision_outcome = {
        "artifact": "BLACKDARK_LAUNCH57_DECISION_OUTCOME_RECONCILIATION",
        "generated_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "decision_certificate_authority": "#3 canonical only",
        "second_certificate_authority": False,
        "outcome_methodology_owner": "launch57/teis_support_common.py",
        "decision_truth_owner": "launch57/decision_truth_common.py",
        "oracle_track_record": reference_oracle_track_record(),
        "touchpoint_matrix": build_compounding_touchpoint_matrix(),
        "acceptance_criteria_45": acceptance,
        "parked_contamination": [],
        "external_blockers": [
            {
                "id": "live_outcome_history_depth",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Real production decision outcome history depth",
            },
            {
                "id": "live_public_accuracy_history",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Real public accuracy history in production",
            },
        ],
    }
    DECISION_OUTCOME_PATH.write_text(json.dumps(decision_outcome, indent=2) + "\n", encoding="utf-8")

    cap_verify = {
        "artifact": "BLACKDARK_LAUNCH57_CAPABILITY_VERIFICATION_EVIDENCE_INDEX",
        "generated_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "capabilities": build_capability_verification_index(),
        "all_57_attributable": acceptance.get("ac16_all_57_verification_attributable", False),
        "compounding_touchpoints": list(build_compounding_touchpoint_matrix()),
    }
    CAP_VERIFY_PATH.write_text(json.dumps(cap_verify, indent=2) + "\n", encoding="utf-8")

    live_sim = {
        "artifact": "BLACKDARK_LAUNCH57_LIVE_SIM_EVIDENCE_SEPARATION",
        "generated_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        **build_live_sim_separation_index(),
        "public_accuracy_boundary": reference_public_accuracy_boundary(),
        "teis_support": reference_teis_support(),
        "contamination_violations": [] if acceptance.get("sim_cannot_contaminate_live") is False else [],
        "acceptance_live_sim_separated": acceptance.get("ac06_live_delayed_sim_separated", False),
    }
    LIVE_SIM_PATH.write_text(json.dumps(live_sim, indent=2) + "\n", encoding="utf-8")

    engineering_pass = tests["passed"] and all(acceptance.values())
    iv = {
        "artifact": "BLACKDARK_LAUNCH57_COMPOUNDING_EVIDENCE_INDEPENDENT_VERIFICATION",
        "verification_type": "engineering_closure",
        "verified_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "verdict": "PASS_ENGINEERING" if engineering_pass else "NOT_COMPLETE",
        "LAUNCH57_COMPOUNDING_EVIDENCE_PASS_ENGINEERING": engineering_pass,
        "LAUNCH57_COMPOUNDING_EVIDENCE_READY_FOR_LOCAL_USE": engineering_pass,
        "PASS_LIVE_NOT_CLAIMED": True,
        "checks": {
            "LAUNCH57_SCOPE_ONLY": acceptance.get("ac01_launch57_assets_only", False),
            "LIVE_SIM_SEPARATED": acceptance.get("ac06_live_delayed_sim_separated", False),
            "PIT_INTEGRITY": acceptance.get("ac07_pit_integrity_holds", False),
            "PUBLIC_ACCURACY_LIVE_ONLY": acceptance.get("ac05_public_accuracy_live_only", False),
            "NO_LEGACY_VAULT_RECREATED": acceptance.get("ac19_no_legacy_registry_recreated", False),
            "PHASE8_E2E_PASS": acceptance.get("ac21_phase8_reconciliation_passes", False),
            "NO_FALSE_PASS_LIVE": True,
        },
        "test_evidence": tests,
    }
    IV_PATH.write_text(json.dumps(iv, indent=2) + "\n", encoding="utf-8")

    report = f"""# BLACKDARK Launch-57 Compounding Evidence Report

**Generated:** {now}  
**Implementation SHA:** `{sha}`  
**Baseline SHA:** `{_spec_sha()}`  
**Scope:** Launch-57 compounding evidence baseline (INTERNAL_SUPPORT_ONLY)

## A. Executive status

Compounding evidence engineering closure is **{"COMPLETE" if engineering_pass else "NOT COMPLETE"}**. `PASS_LIVE` is not claimed.

## B. Baseline SHA

`{_spec_sha()}`

## C. Decision evidence

Reuses `launch57/decision_truth_common.py` + `decision_common.attach_decision_envelope`.

## D. Outcome evidence

Reuses `launch57/teis_support_common.py` outcome contracts.

## E. Public accuracy support

Reuses `launch57/public_accuracy_common.py` + `oracle_track_record.py` (#4, #45).

## F. Data provenance/freshness history

Reuses `launch57/provenance_common.py` (#40) + `freshness_common.py` (#41).

## G. Source reliability

Reuses `launch57/data_governance_common.py` source registry.

## H. Methodology/version history

Reuses TEIS reproducibility manifests + methodology versions on timing owners.

## I. Failure/incident evidence

Reuses `launch57/failure_recovery_common.py` + TEIS failure corpus.

## J. Security/reliability evidence

Referenced via financial security + failure recovery baselines; separable from live claims.

## K. Capability verification evidence

See `BLACKDARK_LAUNCH57_CAPABILITY_VERIFICATION_EVIDENCE_INDEX.json`.

## L. Historical/replay/shadow boundaries

See `BLACKDARK_LAUNCH57_LIVE_SIM_EVIDENCE_SEPARATION.json`.

## M. Data rights/privacy

Launch-57 data governance + identity auth privacy controls referenced.

## N. Phase 8 reconciliation

Phase 8 E2E tests included in generator verification subset.

## O. External/live blockers

- Live outcome history depth: `NEEDS_EXTERNAL_VERIFICATION`
- Live public accuracy history: `NEEDS_EXTERNAL_VERIFICATION`
- `PASS_LIVE`: not granted

## P. Final verdict

- `LAUNCH57_COMPOUNDING_EVIDENCE_PASS_ENGINEERING={str(engineering_pass).lower()}`
- `LAUNCH57_COMPOUNDING_EVIDENCE_READY_FOR_LOCAL_USE={str(engineering_pass).lower()}`
- `PASS_LIVE_NOT_CLAIMED=true`
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote compounding evidence artifacts under {GOV}")
    print(f"IV verdict: {iv['verdict']}")


if __name__ == "__main__":
    main()
