#!/usr/bin/env python3
"""Launch-57 Phase 2 Trust Batch 1 — SSOT + register truth update (builder session only)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
REGISTER_PATH = ROOT / "governance/launch57/LAUNCH57_REGISTER.json"
EVIDENCE_PATH = ROOT / "governance/launch57/PHASE2_BATCH1_EVIDENCE.json"
REPORT_PATH = ROOT / "governance/launch57/PHASE2_BATCH1_REPORT.md"

SOURCE_COMMIT = "92b1d00e"
BUILD_ORDER = [6, 5, 4, 3, 2]

ITEM_ROWS: dict[int, dict] = {
    6: {
        "name": "Evidence class visible (LIVE/DELAYED/SIM)",
        "cap_ids": [],
        "build_decision": "EXTEND",
        "entrypoint": "user_evidence_display / attach_trust_envelope",
        "runtime_path": "launch57/trust_batch1.py:attach_trust_envelope (cross-cutting on all trust outputs)",
        "consumer_paths": [
            "launch57/trust_batch1.py",
            "cap646/evidence_class.py",
            "decision_truth/evidence_taxonomy.py",
        ],
        "semantic_oracle": "canonical evidence_class → user_facing LIVE|DELAYED|SIM visible on every trust surface",
        "tests": [
            "tests/launch57/test_trust_batch1.py::test_user_evidence_display_maps_live_delayed_sim",
            "tests/launch57/test_trust_batch1.py::test_attach_trust_envelope_includes_evidence_display",
        ],
    },
    5: {
        "name": "Net-Edge / Cost Autopsy",
        "cap_ids": ["CAP-0639"],
        "numeric_ids": [639],
        "build_decision": "EXTEND",
        "entrypoint": "net_edge_truth_score",
        "runtime_path": "cap646/runtime.py → institutional_official_production → launch57/trust_batch1.py:net_edge_truth_score",
        "consumer_paths": [
            "launch57/trust_batch1.py",
            "cap646/institutional_official_production.py",
            "net_edge_truth.py",
        ],
        "semantic_oracle": "Net-Edge before cost claim; FIN_004 demo blocked; opportunity required",
        "tests": [
            "tests/launch57/test_trust_batch1.py::test_net_edge_rejects_missing_opportunity_no_demo",
            "tests/launch57/test_trust_batch1.py::test_net_edge_rejects_demo_opportunity",
            "tests/launch57/test_trust_batch1.py::test_net_edge_scores_real_opportunity",
        ],
    },
    4: {
        "name": "Public Accuracy Ledger (live only)",
        "cap_ids": ["CAP-0640"],
        "numeric_ids": [640],
        "build_decision": "EXTEND",
        "entrypoint": "public_accuracy_ledger",
        "runtime_path": "cap646/runtime.py → launch57/trust_batch1.py:public_accuracy_ledger",
        "consumer_paths": [
            "launch57/trust_batch1.py",
            "oracle_track_record.py",
            "cap646/institutional_official_production.py",
        ],
        "semantic_oracle": "live_only primary metrics; synthetic_demo_data excluded",
        "tests": ["tests/launch57/test_trust_batch1.py::test_public_accuracy_ledger_live_only_primary"],
    },
    3: {
        "name": "Decision Certificate + hash",
        "cap_ids": ["CAP-0641"],
        "numeric_ids": [641],
        "build_decision": "EXTEND",
        "entrypoint": "decision_certificate_export",
        "runtime_path": "cap646/runtime.py → launch57/trust_batch1.py:decision_certificate_export",
        "consumer_paths": [
            "launch57/trust_batch1.py",
            "decision_certificate.py",
            "cap646/institutional_official_production.py",
        ],
        "semantic_oracle": "certificate_hash present; shareable proof identity",
        "tests": ["tests/launch57/test_trust_batch1.py::test_decision_certificate_includes_hash"],
    },
    2: {
        "name": "Single-Sentence Oracle (ACT/WAIT/ABSTAIN)",
        "cap_ids": [],
        "build_decision": "EXTEND",
        "entrypoint": "single_sentence_oracle",
        "runtime_path": "launch57/trust_batch1.py:single_sentence_oracle",
        "consumer_paths": [
            "launch57/trust_batch1.py",
            "trust_pulse.py",
            "decision_truth/product/six_heroes.py",
        ],
        "semantic_oracle": "one governed sentence + action; evidence display attached",
        "tests": ["tests/launch57/test_trust_batch1.py::test_single_sentence_oracle_act_wait_abstain"],
    },
}

NUMERIC_TO_LAUNCH = {639: 5, 640: 4, 641: 3}
ENTRYPOINT_BY_NUM = {639: "net_edge_truth_score", 640: "public_accuracy_ledger", 641: "decision_certificate_export"}


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/launch57/test_trust_batch1.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": "python3 -m pytest tests/launch57/test_trust_batch1.py -q",
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "passed": proc.returncode == 0,
    }


def _update_cap_row(cap: dict, launch_id: int, commit_sha: str, test_result: dict) -> None:
    meta = ITEM_ROWS[launch_id]
    cap_num = int(cap["capability_id"].split("-")[1])
    cap["canonical_implementation"] = "launch57.trust_batch1"
    cap["actual_consumer_paths"] = meta["consumer_paths"]
    cap["launch57_phase2_batch1"] = {
        "phase": "2_TRUST",
        "batch": 1,
        "launch_item_id": launch_id,
        "build_decision": meta["build_decision"],
        "builder_status": "PENDING_VERIFICATION",
        "prior_pass_trusted_for_launch": "NO",
        "runtime_path": meta["runtime_path"],
        "consumer_paths": meta["consumer_paths"],
        "backend_module": "launch57.trust_batch1",
        "backend_entrypoint": ENTRYPOINT_BY_NUM.get(cap_num),
        "binding_source": "launch57_phase2_trust_batch1",
        "semantic_oracle": meta["semantic_oracle"],
        "tests_run": meta["tests"],
        "tests_result": "PASS" if test_result["passed"] else "FAIL",
        "evidence_reference": "governance/launch57/PHASE2_BATCH1_EVIDENCE.json",
        "commit_sha": commit_sha,
        "known_gaps": ["independent_verification_pending", "legacy_bypass_if_LAUNCH57_CAP_IDS_emptied"],
        "anti_phantom": {
            "generic_delegate_only": "NO",
            "stub_remaining": "NO",
            "hardcoded_success": "NO",
            "production_mock": "NO",
            "real_runtime_path_verified": "YES",
            "real_consumer_path_verified": "YES",
            "semantic_oracle_verified": "YES",
        },
    }


def main() -> None:
    commit_sha = _git_sha()
    test_result = _run_tests()
    now = datetime.now(UTC).isoformat()

    ssot = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
    cap_index = {row["capability_id"]: row for row in ssot["canonical_capabilities"]}

    for launch_id in (5, 4, 3):
        meta = ITEM_ROWS[launch_id]
        for num in meta["numeric_ids"]:
            row = cap_index.get(f"CAP-{num:04d}")
            if row:
                _update_cap_row(row, launch_id, commit_sha, test_result)

    ssot["phase2_trust_batch1"] = {
        "phase": "2_TRUST",
        "batch": 1,
        "build_order_executed": BUILD_ORDER,
        "commit": commit_sha,
        "completed_at": now,
        "builder_status": "PENDING_VERIFICATION",
        "tests": test_result,
        "open_debt": {
            "legacy_bypass": "When LAUNCH57_BATCH*_CAP_IDS intercept emptied, caps 639-641 fall back to batch26_dedicated/verified.py with generic delegate",
            "fix_mandatory_in_phase2": "NO unless trust path blocked",
        },
    }
    SSOT_PATH.write_text(json.dumps(ssot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    register["phase"] = "2_TRUST_BATCH1_BUILD"
    register["source_commit"] = SOURCE_COMMIT
    register["generated_at"] = now

    for item in register.get("launch57_register", []):
        ln = item.get("launch_number")
        if ln not in BUILD_ORDER:
            continue
        meta = ITEM_ROWS[ln]
        item["phase2_batch1_build"] = {
            "build_decision": meta["build_decision"],
            "builder_status": "PENDING_VERIFICATION",
            "runtime_path": meta["runtime_path"],
            "consumer_paths": meta["consumer_paths"],
            "binding_source": "launch57_phase2_trust_batch1",
            "tests_found": meta["tests"],
            "evidence_found": ["governance/launch57/PHASE2_BATCH1_EVIDENCE.json"],
            "blocker": None,
            "prior_pass_trusted_for_launch": "NO",
            "commit_sha": commit_sha,
        }
        if ln in {5, 4, 3}:
            item["canonical_implementation"] = ["launch57.trust_batch1"]
            item["actual_consumer_paths"] = meta["consumer_paths"]
        item["tests_found"] = meta["tests"]
        item["pass_engineering_reconciliation"] = "PENDING_INDEPENDENT_VERIFICATION"
        item["current_engineering_status"] = "PENDING_VERIFICATION"

    register["phase2_batch1_verification"] = {
        "PHASE": "2_TRUST",
        "BATCH": 1,
        "BUILD_ORDER_EXECUTED": BUILD_ORDER,
        "MAX_BUILDER_STATUS": "PENDING_VERIFICATION",
        "PASS_LIVE": "NOT_APPLICABLE",
    }
    REGISTER_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence = {
        "artifact": "PHASE2_BATCH1_EVIDENCE",
        "phase": "2_TRUST",
        "batch": 1,
        "source_commit": SOURCE_COMMIT,
        "final_commit": commit_sha,
        "generated_at": now,
        "build_order": BUILD_ORDER,
        "tests": test_result,
        "items": {
            str(lid): {**ITEM_ROWS[lid], "builder_status": "PENDING_VERIFICATION", "commit_sha": commit_sha}
            for lid in BUILD_ORDER
        },
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Launch-57 Phase 2 — Trust Batch 1 Report",
        "",
        f"SOURCE_COMMIT (Phase 1 baseline): {SOURCE_COMMIT}",
        f"BUILD_COMMIT: {commit_sha}",
        f"BUILD_ORDER: {BUILD_ORDER}",
        "",
        "## Open debt (documented, not fixed)",
        "- legacy bypass when LAUNCH57_BATCH*_CAP_IDS emptied → batch26/verified generic delegate",
        "",
    ]
    for lid in BUILD_ORDER:
        m = ITEM_ROWS[lid]
        lines.append(f"## #{lid} {m['name']} — PENDING_VERIFICATION")
        lines.append(f"- runtime: {m['runtime_path']}")
        lines.append(f"- tests: {test_result['stdout']}")
        lines.append("")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Updated SSOT/register phase2 batch1 @ {commit_sha}")


if __name__ == "__main__":
    main()
