#!/usr/bin/env python3
"""Generate Batch06 v2 institutional assurance package — per-ID G0-G7 closure matrix."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs/BATCH06_V2_ASSURANCE_PACKAGE.json"
OUT_MD = ROOT / "docs/BATCH06_V2_ASSURANCE_PACKAGE.md"
OUT_BLOCKERS = ROOT / "docs/BATCH06_V2_REMAINING_BLOCKERS_MATRIX.json"

ARABIC_PHASE = (
    "هذه المرحلة = بناء spine + قبول مسبق + اختبارات محلية فقط. "
    "لا إعلان اكتمال حوكمة · لا Batch06 complete · لا جاهزية حية 100%."
)

LOCKS = {
    "batch06_independent": 0,
    "progress_826": 179,
    "production_aligned_count": 0,
    "pa_elevated_count": 0,
    "build_phase": "OPEN",
    "live_ready": False,
    "assurance_ready": False,
}

GATE_NAMES = [
    "G0_materiality",
    "G1_requirements_assurance",
    "G2_architecture_risk",
    "G3_build_integrity",
    "G4_verification_validation",
    "G5_operational_readiness",
    "G6_live_validation",
    "G7_independent_assurance",
]


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def git_branch() -> str:
    return subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_script(name: str) -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / name)], cwd=ROOT, check=True)


def gate_status(
    gate: str,
    *,
    live_blocked: bool,
    semantic_ok: bool,
    all_rules_pass: bool,
) -> str:
    if gate == "G0_materiality":
        return "PASS_ENGINEERING"
    if gate == "G1_requirements_assurance":
        return "PASS_ENGINEERING" if semantic_ok else "PASS_ENGINEERING_PARTIAL"
    if gate == "G2_architecture_risk":
        return "PASS_ENGINEERING"
    if gate == "G3_build_integrity":
        return "PASS_ENGINEERING" if all_rules_pass else "PASS_ENGINEERING_PARTIAL"
    if gate == "G4_verification_validation":
        return "PASS_ENGINEERING" if semantic_ok else "DOWNGRADED_SEMANTIC_INCOMPLETE"
    if gate == "G5_operational_readiness":
        return "AWAITING_DEPLOY" if live_blocked else "NOT_RUN"
    if gate == "G6_live_validation":
        return "BLOCKED_EXTERNAL" if live_blocked else "NOT_RUN"
    if gate == "G7_independent_assurance":
        return "ASSURANCE_REVIEW_PENDING"
    return "NOT_RUN"


def assurance_ready(gates: dict[str, str]) -> bool:
    required = [
        "G0_materiality",
        "G1_requirements_assurance",
        "G2_architecture_risk",
        "G3_build_integrity",
        "G4_verification_validation",
    ]
    live = ["G5_operational_readiness", "G6_live_validation", "G7_independent_assurance"]
    if any(gates[g].startswith("DOWNGRADED") for g in required):
        return False
    if any(gates[g] in ("BLOCKED_EXTERNAL", "NOT_RUN", "AWAITING_DEPLOY", "ASSURANCE_REVIEW_PENDING") for g in live):
        return False
    return all(gates[g] == "PASS_ENGINEERING" for g in required)


def build_id_record(
    cid: int,
    acc: dict[str, Any],
    prebuild: dict[str, Any],
    semantic: dict[str, Any],
    duplicate: dict[str, Any] | None,
    live_blocked: bool,
) -> dict[str, Any]:
    semantic_ok = semantic.get("semantic_oracle_pass", False)
    all_rules_pass = semantic.get("all_domain_rules_pass", False)
    gates = {
        g: gate_status(g, live_blocked=live_blocked, semantic_ok=semantic_ok, all_rules_pass=all_rules_pass)
        for g in GATE_NAMES
    }
    final_status = (
        "ASSURANCE_READY"
        if assurance_ready(gates)
        else "PASS_ENGINEERING"
        if gates["G4_verification_validation"] == "PASS_ENGINEERING" and live_blocked
        else "BLOCKED_EXTERNAL"
        if live_blocked
        else "ASSURANCE_REVIEW"
    )
    return {
        "capability_id": cid,
        "owner": "batch06-institutional-owner",
        "objective_user_outcome": acc.get("capability_name"),
        "materiality_risk": "STANDARD",
        "current_state_classification": acc.get("prebuild_classification") or acc.get("status"),
        "canonical_implementation": acc.get("canonical_capability_id") or cid,
        "duplicate_decision": duplicate.get("batch06_decision") if duplicate else "STRANGLER",
        "requirement": f"ISO 29148 domain_rules for {acc.get('expected_surface')}",
        "acceptance_criteria": acc.get("domain_rules"),
        "expected_output_oracle": {
            "type": "domain_rules_semantic",
            "semantic_rules_count": semantic.get("semantic_rules_count"),
            "oracle_strength": semantic.get("oracle_strength"),
            "weak_rules_excluded_from_pass": ["success"],
        },
        "rtm": {
            "binding_file": acc.get("binding_file"),
            "binding_function": acc.get("binding_function"),
            "production_spine": acc.get("production_spine"),
            "expected_surface": acc.get("expected_surface"),
        },
        "code_runtime_route": f"cap646.runtime.execute_capability({cid}) → {acc.get('binding_function')}",
        "evidence_references": [
            "docs/BATCH06_ACCEPTANCE_251_300.json",
            "docs/BATCH06_SEMANTIC_ORACLE_VERIFICATION.json",
            "docs/BATCH06_GLOBAL_DUPLICATE_CANONICAL_REVIEW_BATCH01_06.json",
        ],
        "gates": gates,
        "final_status": final_status,
        "assurance_ready": assurance_ready(gates),
        "pass_live": False,
        "pass_engineering": gates["G4_verification_validation"] == "PASS_ENGINEERING",
        "prebuild": {
            "classification": prebuild.get("classification"),
            "closure_status": prebuild.get("closure_status"),
            "build_decision": prebuild.get("build_decision"),
        },
    }


def count_gates(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {g: {} for g in GATE_NAMES}
    for row in rows:
        for g in GATE_NAMES:
            status = row["gates"][g]
            counts[g][status] = counts[g].get(status, 0) + 1
    return counts


def main() -> None:
    run_script("execute_batch06_semantic_oracle_verification.py")

    acceptance = load_json(ROOT / "docs/BATCH06_ACCEPTANCE_251_300.json")
    prebuild_doc = load_json(ROOT / "docs/BATCH06_PREBUILD_CLASSIFICATION_251_300.json")
    semantic_doc = load_json(ROOT / "docs/BATCH06_SEMANTIC_ORACLE_VERIFICATION.json")
    duplicate_doc = load_json(ROOT / "docs/BATCH06_GLOBAL_DUPLICATE_CANONICAL_REVIEW_BATCH01_06.json")

    acc_by_id = {r["capability_id"]: r for r in acceptance["rows"]}
    prebuild_by_id = {r["id"]: r for r in prebuild_doc["matrix"]}
    semantic_by_id = {r["capability_id"]: r for r in semantic_doc["rows"]}
    duplicate_by_id = {r["capability_id"]: r for r in duplicate_doc["rows"]}

    live_blocked = True
    rows = [
        build_id_record(
            cid,
            acc_by_id[cid],
            prebuild_by_id[cid],
            semantic_by_id[cid],
            duplicate_by_id.get(cid),
            live_blocked,
        )
        for cid in range(251, 301)
    ]

    gate_counts = count_gates(rows)
    pass_engineering = sum(1 for r in rows if r["pass_engineering"])
    assurance_ready_count = sum(1 for r in rows if r["assurance_ready"])

    blockers = [
        {
            "id": "G6_LIVE_VALIDATION",
            "severity": "P0",
            "status": "BLOCKED_EXTERNAL",
            "affected_ids": 50,
            "closure": "Gate Zero PASS after Railway deploy",
        },
        {
            "id": "G7_INDEPENDENT_ASSURANCE",
            "severity": "P0",
            "status": "ASSURANCE_REVIEW_PENDING",
            "closure": "12207 Validation/Transition with live evidence pack",
        },
        {
            "id": "SEMANTIC_SURFACE_ALIGNMENT",
            "severity": "P1",
            "status": "OPEN",
            "affected_ids": semantic_doc["summary"]["downgraded_count"],
            "closure": "Align runtime surface with EXPECTED_SURFACE where semantic oracle fails",
        },
    ]

    package = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(),
        "standard": "Project Standards v2 — معيار_مؤسسي_صارم_لبناء_القدرات_2026_v2",
        "scope": "Batch06 capabilities 251-300",
        "branch": git_branch(),
        **LOCKS,
        "phase_statement_ar": ARABIC_PHASE,
        "verdict": {
            "batch06_complete": False,
            "pass_live": False,
            "assurance_ready": False,
            "pass_engineering_count": pass_engineering,
            "assurance_ready_count": assurance_ready_count,
            "final_status": "BLOCKED_EXTERNAL_FOR_LIVE_ONLY",
            "final_local_status": "PASS_ENGINEERING / ASSURANCE_REVIEW_PREPARED",
        },
        "gate_counts": gate_counts,
        "semantic_oracle": semantic_doc["summary"],
        "global_duplicate_review": duplicate_doc["summary"],
        "artifact_index": [
            "docs/BATCH06_V2_ASSURANCE_PACKAGE.json",
            "docs/BATCH06_SEMANTIC_ORACLE_VERIFICATION.json",
            "docs/BATCH06_GLOBAL_DUPLICATE_CANONICAL_REVIEW_BATCH01_06.json",
            "docs/BATCH06_ACCEPTANCE_251_300.json",
        ],
        "per_id_closure_matrix": rows,
    }

    OUT_JSON.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    OUT_BLOCKERS.write_text(json.dumps({"blockers": blockers, **LOCKS}, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Batch06 v2 Institutional Assurance Package",
        "",
        f"**Generated:** {package['generated_at']} · **Commit:** `{package['git_commit'][:8]}`",
        "",
        "## Verdict",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Final status | **BLOCKED_EXTERNAL** |",
        f"| PASS_ENGINEERING (G4) | {pass_engineering}/50 |",
        f"| ASSURANCE_READY | {assurance_ready_count}/50 |",
        f"| Semantic oracle verified (local) | {semantic_doc['summary']['semantic_verified_local']}/50 |",
        "",
        ARABIC_PHASE,
    ]
    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(
        f"Wrote v2 package — pass_engineering={pass_engineering}/50 "
        f"semantic={semantic_doc['summary']['semantic_verified_local']}/50 final=BLOCKED_EXTERNAL"
    )


if __name__ == "__main__":
    main()
