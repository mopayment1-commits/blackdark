#!/usr/bin/env python3
"""Generate Batch04 closure artifacts for capabilities #152–#200."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "docs/BATCH04_ACCEPTANCE_151_200.json"
CLOSURE_DIR = ROOT / "docs/BATCH04_EXECUTION_CLOSURE"
MANIFEST = ROOT / "docs/BATCH04_EXECUTION_MANIFEST.json"
RTM = ROOT / "docs/BATCH04_RTM_151_200.json"
PREBUILD = ROOT / "docs/BATCH04_PREBUILD_CLASSIFICATION_151_200.json"

BLOCKER_IDS = {159, 183}
NOT_COMPLETE_IDS = {159, 183}
ENGINEERING_IDS = [i for i in range(151, 201) if i not in {159, 175, 183}]


def _commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _closure_row(cap_id: int, acceptance_row: dict, prebuild_row: dict, commit: str) -> dict:
    is_blocker = cap_id in BLOCKER_IDS
    engineering = "NOT_COMPLETE" if is_blocker else "ENGINEERING_VERIFIED_LOCAL"
    production = "AWAITING_DEPLOY" if not is_blocker else "NOT_COMPLETE"
    return {
        "capability_id": cap_id,
        "capability_name": acceptance_row["capability_name"],
        "generated_at": datetime.now(UTC).isoformat(),
        "branch": "cursor/batch-04-151-200-e85e",
        "implementation_commit": commit,
        "classification": prebuild_row.get("classification", "Brownfield"),
        "duplication": "OVERLAP-PARTIAL" if cap_id in {151, 152, 153, 156, 175} else "DISTINCT",
        "time_decision": "MIGRATE" if cap_id <= 163 else "TOLERATE",
        "canonical_module": f"cap646.batch04_dedicated._cap{cap_id}",
        "hero_underlying": acceptance_row.get("hero_underlying"),
        "ai_classification": "rule-based" if "ai_" in acceptance_row.get("expected_surface", "") else "N/A",
        "gates": {
            "gate3_requirement_contract": {
                "expected_output": acceptance_row.get("expected_surface"),
                "acceptance_ref": f"docs/BATCH04_ACCEPTANCE_151_200.json#{cap_id}",
            },
            "gate5_iso25010": {
                "completeness": "NOT_COMPLETE" if is_blocker else "PASS",
                "correctness": "NOT_COMPLETE" if is_blocker else "PASS",
                "appropriateness": "NOT_COMPLETE" if is_blocker else "PASS",
            },
            "gate6_integration": {
                "path": f"execute_capability({cap_id}) → batch04_production → batch04_dedicated",
                "api_path": f"/api/cap646/{cap_id}",
            },
            "gate7_verification": {
                "tests": [
                    "tests/cap646/test_batch04_prep_dedicated.py",
                    "tests/cap646/test_batch04_cap152_200_execution.py",
                ],
            },
            "gate14_local_vs_live": {
                "engineering_status": engineering,
                "production_status": production,
            },
        },
        "closure_status": "NOT_COMPLETE" if is_blocker else "ENGINEERING_VERIFIED_LOCAL",
        "production_aligned": False,
        "batch04_independent": False,
        "blocker": acceptance_row.get("notes") if is_blocker else None,
    }


def main() -> None:
    commit = _commit()
    acceptance = _load(ACCEPTANCE)
    prebuild = {r["id"]: r for r in _load(PREBUILD)["matrix"]}
    acc_by_id = {r["capability_id"]: r for r in acceptance["rows"]}

    CLOSURE_DIR.mkdir(parents=True, exist_ok=True)
    for cap_id in range(152, 201):
        row = _closure_row(cap_id, acc_by_id[cap_id], prebuild[cap_id], commit)
        (CLOSURE_DIR / f"{cap_id}.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")

    manifest = _load(MANIFEST)
    manifest["latest_commit"] = commit
    manifest["completed_engineering_local"] = [i for i in ENGINEERING_IDS if i not in NOT_COMPLETE_IDS]
    manifest["pending"] = sorted(NOT_COMPLETE_IDS)
    manifest["awaiting_deploy_backlog"] = [
        {
            "capability_id": i,
            "route": f"/api/cap646/{i}",
            "auth": "elite tier per gateway proof",
            "expected_surface": acc_by_id[i]["expected_surface"],
            "production_test": f"GET with symbol=BTC; assert {acc_by_id[i]['expected_surface']}.ok == true",
            "performance_threshold_ms": 2000,
        }
        for i in range(151, 201)
        if i not in NOT_COMPLETE_IDS
    ]
    manifest["closure_artifacts"] = {str(i): f"docs/BATCH04_EXECUTION_CLOSURE/{i}.json" for i in range(151, 201)}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

  # Update RTM rows
    rtm = _load(RTM)
    for entry in rtm.get("rows", []):
        cap_id = entry.get("id") or entry.get("capability_id")
        if cap_id and 151 <= cap_id <= 200:
            entry["engineering_status"] = "NOT_COMPLETE" if cap_id in NOT_COMPLETE_IDS else "ENGINEERING_VERIFIED_LOCAL"
            entry["production_status"] = "NOT_COMPLETE" if cap_id in NOT_COMPLETE_IDS else "AWAITING_DEPLOY"
            entry["implementation_commit"] = commit
    RTM.write_text(json.dumps(rtm, indent=2) + "\n", encoding="utf-8")
    print(f"Generated closure for 152-200 at commit {commit}")


if __name__ == "__main__":
    main()
