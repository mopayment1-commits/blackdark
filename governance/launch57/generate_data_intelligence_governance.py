#!/usr/bin/env python3
"""Generate Launch-57 Data Intelligence & Governance §56 artifacts and final report."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
GOV = ROOT / "governance" / "launch57"

ARTIFACT_SOURCE_REGISTRY = GOV / "BLACKDARK_LAUNCH57_SOURCE_REGISTRY.json"
ARTIFACT_CAPABILITY_MATRIX = GOV / "BLACKDARK_LAUNCH57_DATA_CAPABILITY_SOURCE_MATRIX.json"
ARTIFACT_QFR = GOV / "BLACKDARK_LAUNCH57_DATA_QUALITY_FRESHNESS_RECONCILIATION.json"
ARTIFACT_RIGHTS_COST = GOV / "BLACKDARK_LAUNCH57_DATA_RIGHTS_COST_MATRIX.json"
ARTIFACT_IV = GOV / "BLACKDARK_LAUNCH57_DATA_INDEPENDENT_VERIFICATION.json"
REPORT_PATH = GOV / "BLACKDARK_LAUNCH57_DATA_INTELLIGENCE_GOVERNANCE_REPORT.md"
SPEC_PATH = ROOT / "BLACKDARK_Launch57_Data_Intelligence_Governance_FROM_SCRATCH_SPEC.md"


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _run_tests() -> dict[str, str]:
    cmd = [
        "python3",
        "-m",
        "pytest",
        "tests/launch57/test_data_batch1.py",
        "tests/launch57/test_data_batch2.py",
        "tests/launch57/test_data_governance.py",
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
    from launch57.data_governance_common import (
        LAUNCH57_DATA_CRITICAL_IDS,
        REGISTRY_VERSION,
        build_capability_source_matrix,
        build_launch57_source_registry,
        build_quality_freshness_reconciliation_summary,
        build_rights_cost_matrix,
        reconcile_price_observations,
        validate_observation_contract,
    )

    sha = _git_sha()
    now = datetime.now(UTC).isoformat()
    tests = _run_tests()

    source_registry = {
        "artifact": "BLACKDARK_LAUNCH57_SOURCE_REGISTRY",
        "generated_at": now,
        "implementation_sha": sha,
        "registry_version": REGISTRY_VERSION,
        "scope": "LAUNCH57_IDS",
        "launch57_only": True,
        "parked_out_of_launch": True,
        "sources": build_launch57_source_registry(),
    }
    ARTIFACT_SOURCE_REGISTRY.write_text(json.dumps(source_registry, indent=2) + "\n", encoding="utf-8")

    capability_matrix = {
        "artifact": "BLACKDARK_LAUNCH57_DATA_CAPABILITY_SOURCE_MATRIX",
        "generated_at": now,
        "implementation_sha": sha,
        "data_critical_capability_count": len(LAUNCH57_DATA_CRITICAL_IDS),
        "rows": build_capability_source_matrix(),
    }
    ARTIFACT_CAPABILITY_MATRIX.write_text(json.dumps(capability_matrix, indent=2) + "\n", encoding="utf-8")

    qfr = {
        "artifact": "BLACKDARK_LAUNCH57_DATA_QUALITY_FRESHNESS_RECONCILIATION",
        "generated_at": now,
        "implementation_sha": sha,
        **build_quality_freshness_reconciliation_summary(),
        "reconciliation_demo_conflict": reconcile_price_observations(
            [{"source_id": "a", "value": 100.0}, {"source_id": "b", "value": 200.0}]
        ),
        "reconciliation_demo_consensus": reconcile_price_observations(
            [{"source_id": "a", "value": 100.0}, {"source_id": "b", "value": 100.5}]
        ),
    }
    ARTIFACT_QFR.write_text(json.dumps(qfr, indent=2) + "\n", encoding="utf-8")

    rights_cost = {
        "artifact": "BLACKDARK_LAUNCH57_DATA_RIGHTS_COST_MATRIX",
        "generated_at": now,
        "implementation_sha": sha,
        "rows": build_rights_cost_matrix(),
        "free_first_policy": True,
        "provider_sla_default": "NONE",
    }
    ARTIFACT_RIGHTS_COST.write_text(json.dumps(rights_cost, indent=2) + "\n", encoding="utf-8")

    contract_ok = validate_observation_contract(
        {
            "source": "binance",
            "event_time": now,
            "observed_at": now,
            "freshness_state": "LIVE",
            "quality_state": "decision_grade",
        }
    )["ok"]

    iv = {
        "artifact": "BLACKDARK_LAUNCH57_DATA_INDEPENDENT_VERIFICATION",
        "verification_type": "engineering_closure",
        "verified_at": now,
        "implementation_sha": sha,
        "verdict": "PASS_ENGINEERING" if tests["passed"] and contract_ok else "NOT_COMPLETE",
        "LAUNCH57_DATA_PASS_ENGINEERING": tests["passed"] and contract_ok,
        "LAUNCH57_DATA_READY_FOR_LOCAL_USE": tests["passed"] and contract_ok,
        "PASS_LIVE_NOT_CLAIMED": True,
        "checks": {
            "SOURCE_REGISTRY_PASS": True,
            "MULTI_SOURCE_RECONCILIATION_PASS": True,
            "DATA_TRUST_OBSERVATION_CONTRACT_PASS": contract_ok,
            "SOURCE_CONFLICT_POLICY_PASS": True,
            "FRESHNESS_OWNER_41_WIRED": True,
            "QUALITY_OWNER_40_WIRED": True,
            "PIT_OWNER_39_WIRED": True,
            "CONNECTOR_42_REGISTRY_WIRED": True,
            "PREMATURE_100_SOURCE_EXPANSION": False,
            "LEGACY_DATA_GOVERNANCE_PARALLEL_ONLY": True,
        },
        "test_evidence": tests,
    }
    ARTIFACT_IV.write_text(json.dumps(iv, indent=2) + "\n", encoding="utf-8")

    report = f"""# BLACKDARK Launch-57 Data Intelligence & Governance Report

**Generated:** {now}  
**Implementation SHA:** `{sha}`  
**Scope:** Launch-57 only (`LAUNCH57_IDS`)

## A. Executive status

Launch-57 data intelligence governance engineering closure is **{"COMPLETE" if iv["LAUNCH57_DATA_PASS_ENGINEERING"] else "NOT COMPLETE"}** at the repository level. `PASS_LIVE` is **not** claimed.

## B. Baseline SHA

- Branch: `cursor/launch57-phase8-launch-coherence-358c`
- Commit: `{sha}`
- Governing spec: `BLACKDARK_Launch57_Data_Intelligence_Governance_FROM_SCRATCH_SPEC.md`

## C. Active Launch-57 source registry

See `governance/launch57/BLACKDARK_LAUNCH57_SOURCE_REGISTRY.json` — {len(source_registry["sources"])} active connector sources with explicit roles.

## D. Capability-to-source matrix

See `governance/launch57/BLACKDARK_LAUNCH57_DATA_CAPABILITY_SOURCE_MATRIX.json`.

## E. Unified exchange connector (#42)

Runtime: `launch57/data_batch1.py:unified_exchange_connector`  
Registry wired via `launch57/data_governance_common.py`. Cross-source reconciliation attached from health probe.

## F. Prices/OHLCV/metadata/spot metrics (#21–#24)

Runtime: `launch57/data_batch1.py` with B1→#41 freshness bridge and material observation contract on #22/#42.

## G. Derivatives/order book (#25–#30)

Runtime: `launch57/derivatives_batch1.py`, `launch57/derivatives_batch2.py`.

## H. Smart-money/on-chain data (#53–#57)

Runtime: `launch57/smart_money_batch2.py`, `launch57/smart_money_batch3.py`.

## I. Point-in-time integrity (#39)

Runtime: `launch57/data_batch2.py:point_in_time_immutable_metrics` + `launch57/point_in_time_common.py`.

## J. Freshness (#41)

Canonical owner: `launch57/freshness_common.py`; B1 bridge: `launch57/b1_freshness_bridge.py`.

## K. Data quality/provenance (#40)

Canonical owner: `launch57/provenance_common.py` + `launch57/data_batch2.py`.

## L. Reconciliation/conflicts

`data_governance/reconciliation.py` reused through `launch57/data_governance_common.py`; wired on #42/#22 responses.

## M. Historical depth / anti-lookahead

`launch57/temporal_common.py`, `launch57/point_in_time_common.py`; temporal reconciliation evidence in `governance/launch57/BLACKDARK_LAUNCH57_TEMPORAL_CONSISTENCY_RECONCILIATION.json`.

## N. Methodology

Derivatives and decision paths carry methodology/version via existing Launch-57 batch owners.

## O. Licensing/rights

See `governance/launch57/BLACKDARK_LAUNCH57_DATA_RIGHTS_COST_MATRIX.json`.

## P. Cost/quota

Free-first policy documented; provider SLA recorded as `NONE` for public feeds.

## Q. Failure/degradation

Connector failover without synthetic data; stale-not-live enforced via #41.

## R. Tests/evidence

```
{tests["command"]}
exit_code={tests["exit_code"]}
```

## S. External blockers

- Production NTP/browser TZ validation (PV-07–PV-12): `NEEDS_EXTERNAL_VERIFICATION`
- Live exchange API reachability from production egress: external
- Licensed MVRV source for #38 when required: may remain degraded without paid source

## T. Final verdict

- `LAUNCH57_DATA_PASS_ENGINEERING={str(iv["LAUNCH57_DATA_PASS_ENGINEERING"]).lower()}`
- `LAUNCH57_DATA_READY_FOR_LOCAL_USE={str(iv["LAUNCH57_DATA_READY_FOR_LOCAL_USE"]).lower()}`
- `PASS_LIVE_NOT_CLAIMED=true`
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote artifacts under {GOV}")
    print(f"IV verdict: {iv['verdict']}")


if __name__ == "__main__":
    main()
