#!/usr/bin/env python3
"""P5 Decision Product Experience closure verification."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
OUT = ROOT / "DECISION_TRUTH_P5_PRODUCT_EXPERIENCE_CLOSURE_EVIDENCE.json"
SPEC = ROOT / "docs" / "BLACKDARK_DECISION_TRUTH_SYSTEM_INSTITUTIONAL_FINAL_v1.md"

P5_DTS = [
    "DTS-007",
    "DTS-019",
    "DTS-020",
    "DTS-025",
    "DTS-026",
    "DTS-031",
    "DTS-032",
    "DTS-033",
    "DTS-034",
    "DTS-035",
    "DTS-036",
    "DTS-044",
    "DTS-046",
    "DTS-047",
    "DTS-048",
]

CANONICAL_OWNERS = {
    "governance_entry": "decision_truth/govern.py",
    "product_orchestrator": "decision_truth/product/__init__.py",
    "rejection_engine": "decision_truth/product/rejection_engine.py",
    "why_not_engine": "decision_truth/product/why_not.py",
    "six_heroes": "decision_truth/product/six_heroes.py",
    "command_view": "decision_truth/product/command_view.py",
    "smart_money_context": "decision_truth/product/smart_money.py",
    "causality_guard": "decision_truth/product/causality.py",
    "daily_evidence_autopsy": "decision_truth/product/daily_brief.py",
    "evidence_backed_sentences": "decision_truth/product/grounding.py",
    "user_local_delivery": "decision_truth/product/delivery.py",
    "reject_bad_opportunity": "decision_truth/product/reject_proof.py",
    "no_decision_surface": "decision_truth/product/no_decision.py",
    "full_evidence_trail": "decision_truth/product/evidence_trail.py",
    "thirty_second_truth": "decision_truth/product/thirty_second.py",
    "calm_default": "decision_truth/product/calm_default.py",
    "decision_surface": "data_governance/decision_surface.py",
    "compliance_guards": "decision_truth/compliance.py",
    "timezone_authority": "governance/timezone_governance.py",
}


def _spec_hash() -> str:
    if SPEC.is_file():
        return hashlib.sha256(SPEC.read_bytes()).hexdigest()
    return "missing"


def _git_sha() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def _read(path: str) -> str:
    p = ROOT / path
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def _scan_gaps() -> dict[str, list[str]]:
    govern = _read("decision_truth/govern.py")
    product_init = _read("decision_truth/product/__init__.py")
    rejection = _read("decision_truth/product/rejection_engine.py")
    why_not = _read("decision_truth/product/why_not.py")
    heroes = _read("decision_truth/product/six_heroes.py")
    command = _read("decision_truth/product/command_view.py")
    smart = _read("decision_truth/product/smart_money.py")
    causality = _read("decision_truth/product/causality.py")
    daily = _read("decision_truth/product/daily_brief.py")
    grounding = _read("decision_truth/product/grounding.py")
    delivery = _read("decision_truth/product/delivery.py")
    reject_proof = _read("decision_truth/product/reject_proof.py")
    no_decision = _read("decision_truth/product/no_decision.py")
    trail = _read("decision_truth/product/evidence_trail.py")
    thirty = _read("decision_truth/product/thirty_second.py")
    surface = _read("data_governance/decision_surface.py")
    compliance = _read("decision_truth/compliance.py")

    gaps: dict[str, list[str]] = {
        "REJECTION_ENGINE_PIPELINE_GAPS": [],
        "WHY_NOT_CONTEXT_GAPS": [],
        "HERO_DECISION_TRUTH_GAPS": [],
        "COMMAND_VIEW_PARALLEL_LOGIC_PATHS": [],
        "SMART_MONEY_CONTEXT_GAPS": [],
        "ATTRIBUTION_WITHOUT_CONFIDENCE_PATHS": [],
        "UNSUPPORTED_CAUSALITY_PATHS": [],
        "UNGROUNDED_DAILY_BRIEF_CLAIMS": [],
        "MATERIAL_CLAIMS_WITHOUT_EVIDENCE": [],
        "HARDCODED_GLOBAL_DELIVERY_TIME_PATHS": [],
        "FABRICATED_REJECTION_PROOF_PATHS": [],
        "NO_DECISION_HIDDEN_AS_ERROR_PATHS": [],
        "FULL_EVIDENCE_TRAIL_GAPS": [],
        "THIRTY_SECOND_TRUTH_GAPS": [],
    }

    if "project_decision_product" not in govern:
        gaps["REJECTION_ENGINE_PIPELINE_GAPS"].append("govern_missing_product_projection")
    if "build_rejection_engine" not in product_init or "govern_stats" not in rejection:
        gaps["REJECTION_ENGINE_PIPELINE_GAPS"].append("rejection_engine_not_canonical")
    if '"fabricated_metrics": False' not in rejection:
        gaps["REJECTION_ENGINE_PIPELINE_GAPS"].append("rejection_fabrication_flag_missing")

    if "build_why_not_engine" not in product_init or "machine_readable" not in why_not:
        gaps["WHY_NOT_CONTEXT_GAPS"].append("why_not_engine_incomplete")

    if "no_ui_recomputation" not in heroes or "build_six_heroes" not in product_init:
        gaps["HERO_DECISION_TRUTH_GAPS"].append("six_heroes_not_bound")

    if "build_command_view" not in product_init:
        gaps["COMMAND_VIEW_PARALLEL_LOGIC_PATHS"].append("command_view_missing")
    elif '"parallel_logic": True' in command or "'parallel_logic': True" in command:
        gaps["COMMAND_VIEW_PARALLEL_LOGIC_PATHS"].append("command_view_parallel_logic_true")
    elif "parallel_logic" not in command:
        gaps["COMMAND_VIEW_PARALLEL_LOGIC_PATHS"].append("command_view_parallel_logic_flag_missing")

    if "context_only" not in smart or "not_standalone_decision_driver" not in smart:
        gaps["SMART_MONEY_CONTEXT_GAPS"].append("smart_money_not_contextualized")
    if "ATTRIBUTION_UNCERTAIN" not in smart:
        gaps["ATTRIBUTION_WITHOUT_CONFIDENCE_PATHS"].append("uncertain_attribution_state_missing")

    if "contains_unsupported_causality" not in causality or "sanitize_causal_language" not in compliance:
        gaps["UNSUPPORTED_CAUSALITY_PATHS"].append("causality_guard_not_wired")

    if "WHAT_CHANGED" not in daily or "grounded" not in daily:
        gaps["UNGROUNDED_DAILY_BRIEF_CLAIMS"].append("daily_brief_structure_missing")
    if "validate_material_claims" not in product_init:
        gaps["MATERIAL_CLAIMS_WITHOUT_EVIDENCE"].append("material_claims_validator_missing")

    if "hardcoded_global_08_00" not in delivery:
        gaps["HARDCODED_GLOBAL_DELIVERY_TIME_PATHS"].append("delivery_hardcode_guard_missing")
    if re.search(r'08:00.*UTC|UTC.*08:00', delivery):
        gaps["HARDCODED_GLOBAL_DELIVERY_TIME_PATHS"].append("global_08_00_utc_hardcoded")

    if "fabricated" not in reject_proof or '"fabricated": True' in reject_proof:
        gaps["FABRICATED_REJECTION_PROOF_PATHS"].append("reject_proof_fabrication_risk")
    if "derived_from" not in reject_proof:
        gaps["FABRICATED_REJECTION_PROOF_PATHS"].append("reject_proof_not_canonical")

    if "hidden_as_error" not in no_decision or "first_class_state" not in no_decision:
        gaps["NO_DECISION_HIDDEN_AS_ERROR_PATHS"].append("no_decision_not_first_class")

    from decision_truth.product.evidence_trail import TRAIL_FIELDS

    for field in TRAIL_FIELDS:
        if field not in trail:
            gaps["FULL_EVIDENCE_TRAIL_GAPS"].append(f"missing_trail_field:{field}")
    if "ui_store_duplication" not in trail:
        gaps["FULL_EVIDENCE_TRAIL_GAPS"].append("trail_duplication_guard_missing")

    if "independent_summary" not in thirty or "build_thirty_second_truth" not in product_init:
        gaps["THIRTY_SECOND_TRUTH_GAPS"].append("thirty_second_truth_incomplete")

    if '== "ADMITTED"' in surface and "AVAILABLE" not in surface:
        gaps["HERO_DECISION_TRUTH_GAPS"].append("decision_surface_admitted_only")

    return gaps


def _run_tests() -> tuple[int, str]:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_decision_truth_p5_product_experience.py",
        "tests/test_decision_truth_p4_evidence_lifecycle.py",
        "tests/test_decision_truth_p3_portfolio_preimpact.py",
        "tests/test_decision_truth_p2_economic_execution.py",
        "tests/test_decision_truth_p1_anti_bypass.py",
        "tests/test_decision_truth_pipeline.py",
        "tests/test_data_governance_p0_test_matrix.py",
        "tests/test_arb_truth_gate.py",
        "-q",
        "--tb=no",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return int(proc.returncode != 0), proc.stdout + proc.stderr


def main() -> int:
    gaps = _scan_gaps()
    regression_failures, test_output = _run_tests()
    gap_counts = {k: len(v) for k, v in gaps.items()}
    locally_buildable_remaining = sum(gap_counts.values()) + regression_failures

    closed = locally_buildable_remaining == 0 and regression_failures == 0
    verdict = "DECISION_PRODUCT_EXPERIENCE_NOT_CLOSED"
    if closed:
        verdict = "DECISION_PRODUCT_EXPERIENCE_CLOSED"

    payload = {
        "phase": "P5_DECISION_PRODUCT_EXPERIENCE",
        "verified_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "governing_spec_sha256": _spec_hash(),
        "base_sha": _git_sha(),
        "implementation_sha": _git_sha(),
        "dts_ids_covered": P5_DTS,
        "canonical_owners": CANONICAL_OWNERS,
        "product_surfaces_affected": [
            "six_heroes",
            "command_view",
            "decision_surface",
            "rejection_engine",
            "why_not",
            "daily_brief",
            "smart_money",
            "evidence_trail",
            "thirty_second_truth",
            "no_decision",
            "reject_proof",
        ],
        "pipeline_bindings": {
            "govern_hook": "project_decision_product",
            "projection_flow": "Canonical Decision Truth → Product Projection → User Explanation",
        },
        "rejection_evidence": "decision_truth/product/rejection_engine.py + govern_stats",
        "why_not_evidence": "decision_truth/product/why_not.py",
        "smart_money_attribution_evidence": "decision_truth/product/smart_money.py",
        "causal_language_controls": "decision_truth/product/causality.py",
        "daily_evidence_evidence": "decision_truth/product/daily_brief.py",
        "full_evidence_trail_evidence": "decision_truth/product/evidence_trail.py",
        "thirty_second_truth_evidence": "decision_truth/product/thirty_second.py",
        "remaining_gaps": gaps,
        "summary": {
            "DTS_REQUIREMENTS_IN_SCOPE": len(P5_DTS),
            "FULLY_IMPLEMENTED_VERIFIED_LOCAL": len(P5_DTS) if closed else 0,
            "PARTIAL_LOCAL": 0 if closed else len(P5_DTS),
            "NOT_IMPLEMENTED_LOCAL": 0,
            "LOCALLY_BUILDABLE_REMAINING": locally_buildable_remaining,
            **gap_counts,
            "REGRESSION_FAILURES": regression_failures,
        },
        "verdict": verdict,
        "test_commands": [
            "python3 -m pytest tests/test_decision_truth_p5_product_experience.py tests/test_decision_truth_p4_evidence_lifecycle.py tests/test_decision_truth_p3_portfolio_preimpact.py tests/test_decision_truth_p2_economic_execution.py tests/test_decision_truth_p1_anti_bypass.py tests/test_decision_truth_pipeline.py tests/test_data_governance_p0_test_matrix.py tests/test_arb_truth_gate.py -q",
            "python3 scripts/p5_decision_product_experience_closure_verify.py",
        ],
        "test_output_tail": test_output[-4000:],
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(f"VERDICT={verdict}")
    return 0 if closed else 1


if __name__ == "__main__":
    raise SystemExit(main())
