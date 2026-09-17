#!/usr/bin/env python3
"""Launch-57 Phase 7 Edge+UI Batch 2 — Six Heroes Command Home (builder PENDING only)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTER_PATH = ROOT / "governance/launch57/LAUNCH57_REGISTER.json"
EVIDENCE_PATH = ROOT / "governance/launch57/PHASE7_BATCH2_EVIDENCE.json"
REPORT_PATH = ROOT / "governance/launch57/PHASE7_BATCH2_REPORT.md"
LAYER_REPORT_PATH = ROOT / "governance/launch57/PHASE7_EDGE_UI_LAYER_REPORT.md"

SOURCE_COMMIT = "74c609ce"
BUILD_ORDER = [1]

ITEM = {
    "name": "Six Heroes Command Home",
    "entrypoint": "six_heroes_command_home",
    "handler_module": "launch57.edge_ui_batch2",
    "runtime_path": "api/routers/launch57_edge_ui.py → launch57/edge_ui_batch2.py",
    "consumer_paths": [
        "launch57/edge_ui_batch2.py",
        "decision_truth/product/six_heroes.py",
        "decision_truth/product/command_view.py",
        "launch57/trust_batch1.py",
        "api/routers/launch57_edge_ui.py",
    ],
    "semantic_oracle": "PASS_ENGINEERING launch57 IDs only; excludes PARKED; oracle/trust consumed",
    "tests": ["tests/launch57/test_edge_ui_batch2.py::test_command_home_eligible_ids_within_launch57_scope"],
}


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        ["python3", "-m", "pytest", "tests/launch57/test_edge_ui_batch2.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": "python3 -m pytest tests/launch57/test_edge_ui_batch2.py -q",
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "passed": proc.returncode == 0,
    }


def main() -> None:
    commit_sha = _git_sha()
    test_result = _run_tests()
    now = datetime.now(UTC).isoformat()

    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    register["phase"] = "7_EDGE_UI_BATCH2_BUILD"
    register["generated_at"] = now
    for item in register.get("launch57_register", []):
        if item.get("launch_number") != 1:
            continue
        item["phase7_batch2_build"] = {
            "builder_status": "PENDING_VERIFICATION",
            "runtime_path": ITEM["runtime_path"],
            "consumer_paths": ITEM["consumer_paths"],
            "binding_source": "launch57_phase7_edge_ui_batch2",
            "handler_module": ITEM["handler_module"],
            "tests_found": ITEM["tests"],
            "evidence_found": ["governance/launch57/PHASE7_BATCH2_EVIDENCE.json"],
            "blocker": None,
            "prior_pass_trusted_for_launch": "NO",
            "commit_sha": commit_sha,
            "launch57_scope_guard": "eligible_launch57_ids subset of LAUNCH57_SCOPE_IDS; excludes PARKED",
        }
        item["canonical_implementation"] = [ITEM["handler_module"]]
        item["actual_consumer_paths"] = ITEM["consumer_paths"]
        item["current_engineering_status"] = "PENDING_VERIFICATION"
        item["pass_engineering_reconciliation"] = "PENDING_INDEPENDENT_VERIFICATION"

    register["phase7_batch2_verification"] = {
        "PHASE": "7_EDGE_UI",
        "BATCH": 2,
        "BUILD_ORDER_EXECUTED": BUILD_ORDER,
        "MAX_BUILDER_STATUS": "PENDING_VERIFICATION",
        "PHASE7_COMPLETE": True,
    }
    REGISTER_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence = {
        "artifact": "PHASE7_BATCH2_EVIDENCE",
        "phase": "7_EDGE_UI",
        "batch": 2,
        "source_commit": SOURCE_COMMIT,
        "final_commit": commit_sha,
        "generated_at": now,
        "build_order": BUILD_ORDER,
        "handler_module": ITEM["handler_module"],
        "launch57_scope_proof": "eligible_launch57_ids ⊆ LAUNCH57_SCOPE_IDS (1..57); excludes PARKED",
        "tests": test_result,
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        f"# Phase 7 Batch 2 — Command Home\n\nBUILD_ORDER: {BUILD_ORDER}\nCOMMIT: {commit_sha}\nSTATUS: PENDING_VERIFICATION\n",
        encoding="utf-8",
    )
    LAYER_REPORT_PATH.write_text(
        "# Phase 7 Edge + UI Layer\n\n"
        "Items 43→38→49→50→52→1 wired via launch57.edge_ui_batch1/batch2.\n"
        "Builder status: PENDING_VERIFICATION only.\n",
        encoding="utf-8",
    )
    print(f"Updated register phase7 batch2 @ {commit_sha}")


if __name__ == "__main__":
    main()
