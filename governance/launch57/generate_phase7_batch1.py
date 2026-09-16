#!/usr/bin/env python3
"""Launch-57 Phase 7 Edge+UI Batch 1 — SSOT + register (builder PENDING only)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
REGISTER_PATH = ROOT / "governance/launch57/LAUNCH57_REGISTER.json"
EVIDENCE_PATH = ROOT / "governance/launch57/PHASE7_BATCH1_EVIDENCE.json"
REPORT_PATH = ROOT / "governance/launch57/PHASE7_BATCH1_REPORT.md"

SOURCE_COMMIT = "74c609ce"
BUILD_ORDER = [43, 38, 49, 50, 52]

ITEM_ROWS: dict[int, dict] = {
    43: {
        "cap_ids": ["CAP-0230", "CAP-0635"],
        "numeric_ids": [230, 635],
        "name": "Spot–perp / arbitrage (Net-Edge mandatory)",
        "entrypoint": "spot_perp_arbitrage_scanner",
        "handler_module": "launch57.edge_ui_batch1",
        "runtime_path": "cap646/institutional_official_production.py → launch57/edge_ui_batch1.py",
        "consumer_paths": ["launch57/edge_ui_batch1.py", "arbitrage_service.py", "launch57/trust_batch1.py"],
        "semantic_oracle": "Net-Edge required for cost claims; stale gate; no phantom edge",
        "tests": ["tests/launch57/test_edge_ui_batch1.py::test_spot_perp_blocks_cost_claim_without_opportunity"],
    },
    38: {
        "cap_ids": ["CAP-0040"],
        "numeric_ids": [40],
        "name": "MVRV / Z-Score",
        "entrypoint": "mvrv_mvrv_z_score_suite",
        "handler_module": "launch57.edge_ui_batch1",
        "runtime_path": "cap646/institutional_official_production.py → launch57/edge_ui_batch1.py",
        "consumer_paths": ["launch57/edge_ui_batch1.py", "bd_platform/mvrv_realignment.py"],
        "semantic_oracle": "local proxy + BLOCKED_EXTERNAL if no licensed MVRV; no phantom LIVE",
        "tests": ["tests/launch57/test_edge_ui_batch1.py::test_mvrv_source_blocker_visible"],
    },
    49: {
        "cap_ids": [],
        "numeric_ids": [],
        "name": "Personal decision history (limited Free)",
        "entrypoint": "personal_decision_history",
        "handler_module": "launch57.edge_ui_batch1",
        "runtime_path": "api/routers/launch57_edge_ui.py → launch57/edge_ui_batch1.py",
        "consumer_paths": ["launch57/edge_ui_batch1.py", "decision_ledger.py", "api/routers/launch57_edge_ui.py"],
        "semantic_oracle": "free tier capped history from decision ledger",
        "tests": ["tests/launch57/test_edge_ui_batch1.py::test_personal_decision_history_free_limit"],
    },
    50: {
        "cap_ids": [],
        "numeric_ids": [],
        "name": "Discipline / missed-movement mirror (light)",
        "entrypoint": "discipline_mirror_light",
        "handler_module": "launch57.edge_ui_batch1",
        "runtime_path": "api/routers/launch57_edge_ui.py → launch57/edge_ui_batch1.py",
        "consumer_paths": ["launch57/edge_ui_batch1.py", "discipline_mirror.py"],
        "semantic_oracle": "private lightweight mirror — not public performance",
        "tests": ["tests/launch57/test_edge_ui_batch1.py::test_discipline_mirror_light"],
    },
    52: {
        "cap_ids": [],
        "numeric_ids": [],
        "name": "Capability library (search) — secondary layer",
        "entrypoint": "capability_library_search",
        "handler_module": "launch57.edge_ui_batch1",
        "runtime_path": "api/routers/launch57_edge_ui.py → launch57/edge_ui_batch1.py",
        "consumer_paths": ["launch57/edge_ui_batch1.py", "governance/launch57/LAUNCH57_REGISTER.json"],
        "semantic_oracle": "secondary search layer; PASS_ENGINEERING only; not primary home",
        "tests": ["tests/launch57/test_edge_ui_batch1.py::test_capability_library_secondary_layer"],
    },
}


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/launch57/test_edge_ui_batch1.py",
            "tests/launch57/test_edge_ui_institutional_wire.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": (
            "python3 -m pytest tests/launch57/test_edge_ui_batch1.py "
            "tests/launch57/test_edge_ui_institutional_wire.py -q"
        ),
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "passed": proc.returncode == 0,
    }


def _update_register_item(item: dict, launch_id: int, commit_sha: str, test_result: dict) -> None:
    meta = ITEM_ROWS[launch_id]
    item["phase7_batch1_build"] = {
        "builder_status": "PENDING_VERIFICATION",
        "runtime_path": meta["runtime_path"],
        "consumer_paths": meta["consumer_paths"],
        "binding_source": "launch57_phase7_edge_ui_batch1",
        "handler_module": meta["handler_module"],
        "tests_found": meta["tests"],
        "evidence_found": ["governance/launch57/PHASE7_BATCH1_EVIDENCE.json"],
        "blocker": None,
        "prior_pass_trusted_for_launch": "NO",
        "commit_sha": commit_sha,
    }
    item["canonical_implementation"] = [meta["handler_module"]]
    item["actual_consumer_paths"] = meta["consumer_paths"]
    item["current_engineering_status"] = "PENDING_VERIFICATION"
    item["pass_engineering_reconciliation"] = "PENDING_INDEPENDENT_VERIFICATION"


def main() -> None:
    commit_sha = _git_sha()
    test_result = _run_tests()
    now = datetime.now(UTC).isoformat()

    ssot = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
    cap_index = {row["capability_id"]: row for row in ssot["canonical_capabilities"]}
    for launch_id in (43, 38):
        for num in ITEM_ROWS[launch_id]["numeric_ids"]:
            row = cap_index.get(f"CAP-{num:04d}")
            if row:
                meta = ITEM_ROWS[launch_id]
                row["canonical_implementation"] = meta["handler_module"]
                row["actual_consumer_paths"] = meta["consumer_paths"]
                row["launch57_phase7_batch1"] = {
                    "phase": "7_EDGE_UI",
                    "batch": 1,
                    "launch_item_id": launch_id,
                    "builder_status": "PENDING_VERIFICATION",
                    "handler_module": meta["handler_module"],
                    "commit_sha": commit_sha,
                    "tests_result": "PASS" if test_result["passed"] else "FAIL",
                }

    ssot["phase7_edge_ui_batch1"] = {
        "phase": "7_EDGE_UI",
        "batch": 1,
        "build_order_executed": BUILD_ORDER,
        "commit": commit_sha,
        "completed_at": now,
        "builder_status": "PENDING_VERIFICATION",
        "handler_module": "launch57.edge_ui_batch1",
        "tests": test_result,
        "phase6_baseline": SOURCE_COMMIT,
        "open_debt": {
            "legacy_bypass": (
                "When LAUNCH57_EDGE_UI_BATCH1_CAP_IDS emptied → "
                "batch10_dedicated (230) + batch26_dedicated (635) + batch01_dedicated (40)"
            ),
        },
    }
    SSOT_PATH.write_text(json.dumps(ssot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    register["phase"] = "7_EDGE_UI_BATCH1_BUILD"
    register["generated_at"] = now
    for item in register.get("launch57_register", []):
        if item.get("launch_number") in BUILD_ORDER:
            _update_register_item(item, item["launch_number"], commit_sha, test_result)

    register["phase7_batch1_verification"] = {
        "PHASE": "7_EDGE_UI",
        "BATCH": 1,
        "BUILD_ORDER_EXECUTED": BUILD_ORDER,
        "MAX_BUILDER_STATUS": "PENDING_VERIFICATION",
    }
    REGISTER_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence = {
        "artifact": "PHASE7_BATCH1_EVIDENCE",
        "phase": "7_EDGE_UI",
        "batch": 1,
        "source_commit": SOURCE_COMMIT,
        "final_commit": commit_sha,
        "generated_at": now,
        "build_order": BUILD_ORDER,
        "handler_module": "launch57.edge_ui_batch1",
        "legacy_bypass_debt": (
            "LAUNCH57_EDGE_UI_BATCH1_CAP_IDS empty → batch10_dedicated (230), "
            "batch26_dedicated (635), batch01_dedicated (40)"
        ),
        "tests": test_result,
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        f"# Phase 7 Batch 1\n\nBUILD_ORDER: {BUILD_ORDER}\nCOMMIT: {commit_sha}\nSTATUS: PENDING_VERIFICATION\n",
        encoding="utf-8",
    )
    print(f"Updated SSOT/register phase7 batch1 @ {commit_sha}")


if __name__ == "__main__":
    main()
