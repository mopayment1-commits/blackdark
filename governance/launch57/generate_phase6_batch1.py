#!/usr/bin/env python3
"""Launch-57 Phase 6 Explanation+AI Batch 1 — SSOT + register (builder PENDING only)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
REGISTER_PATH = ROOT / "governance/launch57/LAUNCH57_REGISTER.json"
EVIDENCE_PATH = ROOT / "governance/launch57/PHASE6_BATCH1_EVIDENCE.json"
REPORT_PATH = ROOT / "governance/launch57/PHASE6_BATCH1_REPORT.md"
LAYER_REPORT_PATH = ROOT / "governance/launch57/PHASE6_EXPLANATION_AI_LAYER_REPORT.md"

SOURCE_COMMIT = "e8dd65bf"
BUILD_ORDER = [34, 35, 36, 51]

CAP_ROWS: dict[int, dict] = {
    34: {
        "cap_ids": ["CAP-0025"],
        "numeric_ids": [25],
        "name": "Signal → Explanation workflow",
        "entrypoint": "signal_explanation_workflow",
        "ai_system_type": "RULE_BASED",
        "runtime_path": "cap646/institutional_official_production.py → launch57/explanation_ai_batch1.py",
        "consumer_paths": [
            "launch57/explanation_ai_batch1.py",
            "bd_platform/footprint_analytics.py",
            "heroes_quality.py",
        ],
        "semantic_oracle": "footprint + OQS why block on live spine; STALE blocks",
        "tests": ["tests/launch57/test_explanation_ai_batch1.py::test_signal_explanation_blocks_stale"],
    },
    35: {
        "cap_ids": ["CAP-0026"],
        "numeric_ids": [26],
        "name": "Price-move explanation",
        "entrypoint": "price_move_explanation",
        "ai_system_type": "RULE_BASED",
        "runtime_path": "cap646/institutional_official_production.py → launch57/explanation_ai_batch1.py",
        "consumer_paths": [
            "launch57/explanation_ai_batch1.py",
            "launch57/decision_common.py",
            "sentiment_engine.py",
        ],
        "semantic_oracle": "threshold rules on spine price + sentiment; no LIVE on STALE",
        "tests": ["tests/launch57/test_explanation_ai_batch1.py::test_price_move_explanation_rule_based_live"],
    },
    36: {
        "cap_ids": ["CAP-0024"],
        "numeric_ids": [24],
        "name": "AI Research Agent + Copilot (platform data only)",
        "entrypoint": "ai_research_agent_grounded",
        "ai_system_type": "STATISTICAL",
        "runtime_path": "cap646/institutional_official_production.py → launch57/explanation_ai_batch1.py",
        "consumer_paths": [
            "launch57/explanation_ai_batch1.py",
            "research_lab.py",
        ],
        "semantic_oracle": "platform-data-only aggregation; compliance footer visible; llm_used=false",
        "tests": ["tests/launch57/test_explanation_ai_batch1.py::test_ai_research_agent_platform_only_footer"],
    },
    51: {
        "cap_ids": ["CAP-0065", "CAP-0100"],
        "numeric_ids": [65, 100],
        "name": "Research portal / short briefs",
        "entrypoint": "research_intelligence_portal",
        "ai_system_type": "STATISTICAL",
        "runtime_path": "cap646/institutional_official_production.py → launch57/explanation_ai_batch1.py",
        "consumer_paths": [
            "launch57/explanation_ai_batch1.py",
            "oracle_track_record.py",
        ],
        "semantic_oracle": "short shareable briefs from oracle track record; limited launch scope",
        "tests": ["tests/launch57/test_explanation_ai_batch1.py::test_research_portal_short_brief"],
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
            "tests/launch57/test_explanation_ai_batch1.py",
            "tests/launch57/test_explanation_ai_institutional_wire.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": (
            "python3 -m pytest tests/launch57/test_explanation_ai_batch1.py "
            "tests/launch57/test_explanation_ai_institutional_wire.py -q"
        ),
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "passed": proc.returncode == 0,
    }


def _update_cap_row(cap: dict, launch_id: int, commit_sha: str, test_result: dict) -> None:
    meta = CAP_ROWS[launch_id]
    cap["canonical_implementation"] = "launch57.explanation_ai_batch1"
    cap["actual_consumer_paths"] = meta["consumer_paths"]
    cap["launch57_phase6_batch1"] = {
        "phase": "6_EXPLANATION_AI",
        "batch": 1,
        "launch_item_id": launch_id,
        "builder_status": "PENDING_VERIFICATION",
        "prior_pass_trusted_for_launch": "NO",
        "runtime_path": meta["runtime_path"],
        "consumer_paths": meta["consumer_paths"],
        "backend_module": "launch57.explanation_ai_batch1",
        "backend_entrypoint": meta["entrypoint"],
        "binding_source": "launch57_phase6_explanation_ai_batch1",
        "handler_module": "launch57.explanation_ai_batch1",
        "ai_system_type": meta["ai_system_type"],
        "semantic_oracle": meta["semantic_oracle"],
        "tests_run": meta["tests"],
        "tests_result": "PASS" if test_result["passed"] else "FAIL",
        "evidence_reference": "governance/launch57/PHASE6_BATCH1_EVIDENCE.json",
        "commit_sha": commit_sha,
        "known_gaps": [
            "independent_verification_pending",
            "legacy_bypass_if_LAUNCH57_EXPLANATION_AI_BATCH1_CAP_IDS_emptied",
        ],
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

    ssot["phase6_explanation_ai_batch1"] = {
        "phase": "6_EXPLANATION_AI",
        "batch": 1,
        "build_order_executed": BUILD_ORDER,
        "commit": commit_sha,
        "completed_at": now,
        "builder_status": "PENDING_VERIFICATION",
        "handler_module": "launch57.explanation_ai_batch1",
        "tests": test_result,
        "phase5_baseline": SOURCE_COMMIT,
        "open_debt": {
            "legacy_bypass": (
                "When LAUNCH57_EXPLANATION_AI_BATCH1_CAP_IDS emptied → "
                "cap646/batch01_dedicated.py (24,25,26) and cap646/batch02_dedicated.py (65,100)"
            ),
            "fix_mandatory": "NO unless explanation_ai path blocked",
        },
    }
    SSOT_PATH.write_text(json.dumps(ssot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    register["phase"] = "6_EXPLANATION_AI_BATCH1_BUILD"
    register["generated_at"] = now
    for item in register.get("launch57_register", []):
        ln = item.get("launch_number")
        if ln not in BUILD_ORDER:
            continue
        meta = CAP_ROWS[ln]
        item["phase6_batch1_build"] = {
            "builder_status": "PENDING_VERIFICATION",
            "runtime_path": meta["runtime_path"],
            "consumer_paths": meta["consumer_paths"],
            "binding_source": "launch57_phase6_explanation_ai_batch1",
            "handler_module": "launch57.explanation_ai_batch1",
            "ai_system_type": meta["ai_system_type"],
            "tests_found": meta["tests"],
            "evidence_found": ["governance/launch57/PHASE6_BATCH1_EVIDENCE.json"],
            "blocker": None,
            "prior_pass_trusted_for_launch": "NO",
            "commit_sha": commit_sha,
        }
        item["canonical_implementation"] = ["launch57.explanation_ai_batch1"]
        item["actual_consumer_paths"] = meta["consumer_paths"]
        item["current_engineering_status"] = "PENDING_VERIFICATION"
        item["pass_engineering_reconciliation"] = "PENDING_INDEPENDENT_VERIFICATION"

    register["phase6_batch1_verification"] = {
        "PHASE": "6_EXPLANATION_AI",
        "BATCH": 1,
        "BUILD_ORDER_EXECUTED": BUILD_ORDER,
        "MAX_BUILDER_STATUS": "PENDING_VERIFICATION",
    }
    REGISTER_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence = {
        "artifact": "PHASE6_BATCH1_EVIDENCE",
        "phase": "6_EXPLANATION_AI",
        "batch": 1,
        "source_commit": SOURCE_COMMIT,
        "final_commit": commit_sha,
        "generated_at": now,
        "build_order": BUILD_ORDER,
        "handler_module": "launch57.explanation_ai_batch1",
        "launch_items": {
            str(lid): {
                "ai_system_type": CAP_ROWS[lid]["ai_system_type"],
                "cap_ids": CAP_ROWS[lid]["cap_ids"],
                "builder_status": "PENDING_VERIFICATION",
            }
            for lid in BUILD_ORDER
        },
        "legacy_bypass_debt": (
            "LAUNCH57_EXPLANATION_AI_BATCH1_CAP_IDS empty → batch01_dedicated (24,25,26) "
            "+ batch02_dedicated (65,100)"
        ),
        "tests": test_result,
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        f"# Phase 6 Batch 1 — Explanation + AI\n\n"
        f"BUILD_ORDER: {BUILD_ORDER}\n"
        f"COMMIT: {commit_sha}\n"
        f"STATUS: PENDING_VERIFICATION\n"
        f"HANDLER: launch57.explanation_ai_batch1\n",
        encoding="utf-8",
    )
    LAYER_REPORT_PATH.write_text(
        "# Phase 6 Explanation + AI Layer\n\n"
        "Items 34→35→36→51 wired via launch57.explanation_ai_batch1.\n"
        "Builder status: PENDING_VERIFICATION only.\n",
        encoding="utf-8",
    )
    print(f"Updated SSOT/register phase6 batch1 @ {commit_sha}")


if __name__ == "__main__":
    main()
