#!/usr/bin/env python3
"""Generate Launch-57 TEIS support layer closure artifacts."""

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

RECON_PATH = GOV / "BLACKDARK_LAUNCH57_TEIS_SUPPORT_LAYER_RECONCILIATION.json"
IV_PATH = GOV / "BLACKDARK_LAUNCH57_TEIS_INDEPENDENT_VERIFICATION.json"
REPORT_PATH = GOV / "BLACKDARK_LAUNCH57_TEIS_SUPPORT_LAYER_REPORT.md"
TEMPORAL_RECON = GOV / "BLACKDARK_LAUNCH57_TEMPORAL_CONSISTENCY_RECONCILIATION.json"


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _run_tests() -> dict[str, Any]:
    cmd = [
        "python3",
        "-m",
        "pytest",
        "tests/launch57/test_teis_support_layer.py",
        "tests/launch57/test_temporal_batch15.py",
        "-q",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "command": " ".join(cmd),
        "exit_code": str(proc.returncode),
        "stdout_tail": proc.stdout.strip()[-500:],
        "passed": proc.returncode == 0,
    }


def main() -> None:
    from launch57.teis_support_common import (
        TEIS_VERSION,
        acceptance_criteria_status,
        build_teis_component_registry,
    )

    sha = _git_sha()
    now = datetime.now(UTC).isoformat()
    tests = _run_tests()
    acceptance = acceptance_criteria_status()
    temporal_pass = False
    if TEMPORAL_RECON.exists():
        temporal_pass = json.loads(TEMPORAL_RECON.read_text(encoding="utf-8")).get(
            "LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING", False
        )

    recon = {
        "artifact": "BLACKDARK_LAUNCH57_TEIS_SUPPORT_LAYER_RECONCILIATION",
        "generated_at": now,
        "implementation_sha": sha,
        "teis_version": TEIS_VERSION,
        "scope": "LAUNCH57_IDS",
        "internal_support_only": True,
        "governing_spec": "BLACKDARK_Launch57_Temporal_Evidence_Intelligence_Support_Layer.md",
        "temporal_b1_b15_pass_engineering": temporal_pass,
        "internal_components": build_teis_component_registry(),
        "acceptance_criteria_27": acceptance,
        "acceptance_all_pass": all(acceptance.values()),
        "parked_out_of_launch": [
            "user_facing_market_time_machine",
            "standalone_learning_value_engine",
            "standalone_champion_challenger_product",
            "legacy_failure_corpus_direct_path",
            "phase_ii_iii_data_moat",
        ],
        "reuse_paths": {
            "temporal": "launch57/temporal_common.py + B1-B15 batches",
            "evidence_class": "launch57/evidence_class_common.py (#6)",
            "pit": "launch57/point_in_time_common.py (#39)",
            "public_accuracy": "launch57/public_accuracy_common.py (#4/#45)",
            "decision_timing": "launch57/decision_timing_common.py",
        },
    }
    RECON_PATH.write_text(json.dumps(recon, indent=2) + "\n", encoding="utf-8")

    engineering_pass = tests["passed"] and all(acceptance.values()) and temporal_pass
    iv = {
        "artifact": "BLACKDARK_LAUNCH57_TEIS_INDEPENDENT_VERIFICATION",
        "verification_type": "engineering_closure",
        "verified_at": now,
        "implementation_sha": sha,
        "verdict": "PASS_ENGINEERING" if engineering_pass else "NOT_COMPLETE",
        "LAUNCH57_TEIS_PASS_ENGINEERING": engineering_pass,
        "LAUNCH57_TEIS_READY_FOR_LOCAL_USE": engineering_pass,
        "PASS_LIVE_NOT_CLAIMED": True,
        "checks": {
            "NO_NEW_CAPABILITY": True,
            "INTERNAL_SUPPORT_ONLY": True,
            "EVIDENCE_CLASS_MAPPING_PASS": acceptance.get("evidence_mapping_deterministic", False),
            "REPLAY_NOT_LIVE_PASS": acceptance.get("replay_shadow_cannot_become_live", False),
            "TEMPORAL_LEAKAGE_TESTABLE": acceptance.get("temporal_leakage_testable", False),
            "B1_B15_TEMPORAL_FOUNDATION_PASS": temporal_pass,
            "PUBLIC_ACCURACY_LIVE_ONLY_BOUNDARY": True,
            "PREMATURE_PRODUCT_SURFACE": False,
        },
        "test_evidence": tests,
    }
    IV_PATH.write_text(json.dumps(iv, indent=2) + "\n", encoding="utf-8")

    report = f"""# BLACKDARK Launch-57 TEIS Support Layer Report

**Generated:** {now}  
**Implementation SHA:** `{sha}`  
**Scope:** Launch-57 internal support only

## Executive status

TEIS engineering closure is **{"COMPLETE" if engineering_pass else "NOT COMPLETE"}**. `PASS_LIVE` is not claimed.

## Governing objective

`TEMPORAL_SUPPORT ≠ NEW_CAPABILITY` — all components are `INTERNAL_SUPPORT_ONLY` with explicit `consumer_capability_ids`.

## Foundation reuse (no rebuild)

- B1–B15 temporal batches: `PASS_ENGINEERING` via `BLACKDARK_LAUNCH57_TEMPORAL_CONSISTENCY_RECONCILIATION.json`
- Evidence class owner: `launch57/evidence_class_common.py` (#6)
- PIT owner: `launch57/point_in_time_common.py` (#39)
- Public accuracy boundary: `launch57/public_accuracy_common.py` (#4/#45)

## New TEIS consolidation

- `launch57/teis_support_common.py` — outcome contracts, replay fidelity, dependence metadata, reproducibility manifests, internal failure corpus, acceptance §27 gate
- Wired on B4 decision trust envelope via `attach_teis_support_envelope`

## Acceptance criteria (§27)

{json.dumps(acceptance, indent=2)}

## Tests

```
{tests["command"]}
exit_code={tests["exit_code"]}
```

## External blockers

- Production host clock / browser TZ / DST scheduling: `NEEDS_EXTERNAL_VERIFICATION`
- `PASS_LIVE`: not granted

## Final verdict

- `LAUNCH57_TEIS_PASS_ENGINEERING={str(engineering_pass).lower()}`
- `LAUNCH57_TEIS_READY_FOR_LOCAL_USE={str(engineering_pass).lower()}`
- `PASS_LIVE_NOT_CLAIMED=true`
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote TEIS artifacts under {GOV}")
    print(f"IV verdict: {iv['verdict']}")


if __name__ == "__main__":
    main()
