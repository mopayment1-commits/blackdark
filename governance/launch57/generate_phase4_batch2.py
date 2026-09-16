#!/usr/bin/env python3
"""Launch-57 Phase 4 Smart Money Batch 2 — SSOT + register (builder PENDING only)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
REGISTER_PATH = ROOT / "governance/launch57/LAUNCH57_REGISTER.json"
EVIDENCE_PATH = ROOT / "governance/launch57/PHASE4_BATCH2_EVIDENCE.json"
REPORT_PATH = ROOT / "governance/launch57/PHASE4_BATCH2_REPORT.md"

SOURCE_COMMIT = "9adef8c0"
BUILD_ORDER = [15, 18, 19, 53, 54]

CAP_ROWS: dict[int, dict] = {
    15: {
        "cap_ids": ["CAP-0014"],
        "numeric_ids": [14],
        "name": "Entity-Aware Wallet Intelligence",
        "entrypoint": "entity_aware_wallet_intelligence",
        "runtime_path": "cap646/institutional_official_production.py → launch57/smart_money_batch2.py",
        "consumer_paths": ["launch57/smart_money_batch2.py", "bd_platform/address_intelligence.py"],
        "semantic_oracle": "entity labels from address intel on live spine",
        "tests": ["tests/launch57/test_smart_money_batch2.py"],
    },
    18: {
        "cap_ids": ["CAP-0081", "CAP-0098"],
        "numeric_ids": [81, 98],
        "name": "Whale Accumulation / Movement Alerts",
        "entrypoint": "whale_accumulation_distribution_intelligence",
        "runtime_path": "cap646/institutional_official_production.py → launch57/smart_money_batch2.py",
        "consumer_paths": ["launch57/smart_money_batch2.py", "whale_tracker.py"],
        "semantic_oracle": "whale alerts filtered on live spine",
        "tests": ["tests/launch57/test_smart_money_batch2.py::test_dispatch_all_batch2_caps"],
    },
    19: {
        "cap_ids": ["CAP-0091"],
        "numeric_ids": [91],
        "name": "Inter-Entity Flow (limited launch)",
        "entrypoint": "inter_entity_flow_intelligence",
        "runtime_path": "cap646/institutional_official_production.py → launch57/smart_money_batch2.py",
        "consumer_paths": ["launch57/smart_money_batch2.py", "onchain_tracker.py"],
        "semantic_oracle": "limited scope — no full paid leaderboard",
        "tests": ["tests/launch57/test_smart_money_batch2.py::test_inter_entity_limited_scope"],
    },
    53: {
        "cap_ids": ["CAP-0022"],
        "numeric_ids": [22],
        "name": "Instant Wallet Due Diligence",
        "entrypoint": "instant_wallet_due_diligence",
        "runtime_path": "cap646/institutional_official_production.py → launch57/smart_money_batch2.py",
        "consumer_paths": ["launch57/smart_money_batch2.py", "bd_platform/whales_institutional_layer.py"],
        "semantic_oracle": "wallet DD with surveillance flags on live spine",
        "tests": ["tests/launch57/test_smart_money_batch2.py::test_dispatch_all_batch2_caps"],
    },
    54: {
        "cap_ids": ["CAP-0023"],
        "numeric_ids": [23],
        "name": "Instant Token Due Diligence",
        "entrypoint": "instant_token_due_diligence",
        "runtime_path": "cap646/institutional_official_production.py → launch57/smart_money_batch2.py",
        "consumer_paths": ["launch57/smart_money_batch2.py", "research_lab.py"],
        "semantic_oracle": "token DD checklist on live spine; STALE blocks",
        "tests": ["tests/launch57/test_smart_money_batch2.py::test_instant_token_dd_blocks_stale"],
    },
}


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        ["python3", "-m", "pytest", "tests/launch57/test_smart_money_batch2.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": "python3 -m pytest tests/launch57/test_smart_money_batch2.py -q",
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "passed": proc.returncode == 0,
    }


def _update_cap_row(cap: dict, launch_id: int, commit_sha: str, test_result: dict) -> None:
    meta = CAP_ROWS[launch_id]
    cap["canonical_implementation"] = "launch57.smart_money_batch2"
    cap["actual_consumer_paths"] = meta["consumer_paths"]
    cap["launch57_phase4_batch2"] = {
        "phase": "4_SMART_MONEY_INSTANT",
        "batch": 2,
        "launch_item_id": launch_id,
        "builder_status": "PENDING_VERIFICATION",
        "prior_pass_trusted_for_launch": "NO",
        "runtime_path": meta["runtime_path"],
        "consumer_paths": meta["consumer_paths"],
        "backend_module": "launch57.smart_money_batch2",
        "backend_entrypoint": meta["entrypoint"],
        "binding_source": "launch57_phase4_smart_money_batch2",
        "semantic_oracle": meta["semantic_oracle"],
        "tests_run": meta["tests"],
        "tests_result": "PASS" if test_result["passed"] else "FAIL",
        "evidence_reference": "governance/launch57/PHASE4_BATCH2_EVIDENCE.json",
        "commit_sha": commit_sha,
        "known_gaps": ["independent_verification_pending", "legacy_bypass_if_LAUNCH57_SMART_MONEY_BATCH2_CAP_IDS_emptied"],
    }


def main() -> None:
    commit_sha = _git_sha()
    test_result = _run_tests()
    now = datetime.now(UTC).isoformat()

    ssot = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
    cap_index = {row["capability_id"]: row for row in ssot["canonical_capabilities"]}
    for launch_id in BUILD_ORDER:
        for num in CAP_ROWS[launch_id]["numeric_ids"]:
            row = cap_index.get(f"CAP-{num:04d}")
            if row:
                _update_cap_row(row, launch_id, commit_sha, test_result)

    ssot["phase4_smart_money_batch2"] = {
        "phase": "4_SMART_MONEY_INSTANT",
        "batch": 2,
        "build_order_executed": BUILD_ORDER,
        "commit": commit_sha,
        "completed_at": now,
        "builder_status": "PENDING_VERIFICATION",
        "tests": test_result,
        "phase3_baseline": SOURCE_COMMIT,
        "open_debt": {
            "legacy_bypass": "When LAUNCH57_SMART_MONEY_BATCH2_CAP_IDS emptied → batch01/batch02_dedicated",
            "fix_mandatory": "NO unless smart-money path blocked",
        },
    }
    SSOT_PATH.write_text(json.dumps(ssot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    register["phase"] = "4_SMART_MONEY_BATCH2_BUILD"
    register["generated_at"] = now
    for item in register.get("launch57_register", []):
        ln = item.get("launch_number")
        if ln not in BUILD_ORDER:
            continue
        meta = CAP_ROWS[ln]
        item["phase4_batch2_build"] = {
            "builder_status": "PENDING_VERIFICATION",
            "runtime_path": meta["runtime_path"],
            "consumer_paths": meta["consumer_paths"],
            "binding_source": "launch57_phase4_smart_money_batch2",
            "handler_module": "launch57.smart_money_batch2",
            "tests_found": meta["tests"],
            "evidence_found": ["governance/launch57/PHASE4_BATCH2_EVIDENCE.json"],
            "blocker": None,
            "prior_pass_trusted_for_launch": "NO",
            "commit_sha": commit_sha,
        }
        item["canonical_implementation"] = ["launch57.smart_money_batch2"]
        item["actual_consumer_paths"] = meta["consumer_paths"]
        item["current_engineering_status"] = "PENDING_VERIFICATION"
        item["pass_engineering_reconciliation"] = "PENDING_INDEPENDENT_VERIFICATION"

    register["phase4_batch2_verification"] = {
        "PHASE": "4_SMART_MONEY_INSTANT",
        "BATCH": 2,
        "BUILD_ORDER_EXECUTED": BUILD_ORDER,
        "MAX_BUILDER_STATUS": "PENDING_VERIFICATION",
    }
    REGISTER_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence = {
        "artifact": "PHASE4_BATCH2_EVIDENCE",
        "phase": "4_SMART_MONEY_INSTANT",
        "batch": 2,
        "source_commit": SOURCE_COMMIT,
        "final_commit": commit_sha,
        "generated_at": now,
        "build_order": BUILD_ORDER,
        "handler_module": "launch57.smart_money_batch2",
        "tests": test_result,
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        f"# Phase 4 Batch 2\n\nBUILD_ORDER: {BUILD_ORDER}\nCOMMIT: {commit_sha}\nSTATUS: PENDING_VERIFICATION\n",
        encoding="utf-8",
    )
    print(f"Updated SSOT/register phase4 batch2 @ {commit_sha}")


if __name__ == "__main__":
    main()
