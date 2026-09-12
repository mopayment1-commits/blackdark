#!/usr/bin/env python3
"""Deep honest audit — exposes superficial spines and generic capability routing.

v6 PASS_ENGINEERING requires per-requirement: code + test + evidence.
This script NEVER trusts catalog frozensets alone.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "HONEST_DEEP_INSTITUTIONAL_AUDIT.json"


def _rg_count(pattern: str, paths: list[str]) -> int:
    proc = subprocess.run(
        ["rg", "-l", pattern, *paths],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return len([l for l in proc.stdout.splitlines() if l.strip()])


def _capability_truth() -> dict:
    audit_path = ROOT / "ENGINEERING_AUDIT_826_REPORT.json"
    inv_path = ROOT / "docs" / "CAPABILITIES_826_INVENTORY.json"
    audit = json.loads(audit_path.read_text()) if audit_path.exists() else {}
    rows = audit.get("capabilities") or []

    binding_counts: dict[str, int] = {}
    for r in rows:
        src = r.get("binding_source") or "unknown"
        binding_counts[src] = binding_counts.get(src, 0) + 1

    generic_spine = binding_counts.get("batch_range_production_spine", 0)
    dedicated = binding_counts.get("explicit_option_a", 0)
    rescue = sum(1 for r in rows if r.get("rescue_tier") or r.get("gap_type") == "A_RESCUE")
    not_complete = sum(1 for r in rows if r.get("engineering_status") == "NOT_COMPLETE")

    inv = json.loads(inv_path.read_text()) if inv_path.exists() else {}
    per_id = inv.get("per_id") or {}
    aligned = sum(1 for r in per_id.values() if r.get("status") == "PRODUCTION-ALIGNED")
    inflated = sum(1 for r in per_id.values() if r.get("reconcile_source") == "engineering_audit_826")

    return {
        "total_capabilities": 826,
        "binding_breakdown": binding_counts,
        "generic_batch_range_spine": generic_spine,
        "dedicated_explicit_option_a": dedicated,
        "generic_spine_pct": round(generic_spine / 826 * 100, 1),
        "rescue_dependent": rescue,
        "engineering_not_complete": not_complete,
        "inventory_production_aligned": aligned,
        "inventory_inflated_by_reconcile_script": inflated,
        "honest_production_aligned_estimate": dedicated + 36,  # dedup covered
        "verdict": "FAIL" if generic_spine > 500 else "PARTIAL",
        "reason": (
            f"{generic_spine}/826 capabilities share one generic batch_range_production spine — "
            "NOT goal-specific per v6 §2.1 Functional Appropriateness"
        ),
    }


def _governing_spec_truth() -> dict:
    from decision_truth.requirements import dts_summary
    from data_governance.requirements import dat_summary
    from governance.billing_requirements import bill_summary
    from governance.identity_requirements import id_summary
    from governance.failure_requirements import err_summary

    domains = []
    for name, summary_fn, prefix in [
        ("DTS", dts_summary, "DTS"),
        ("DAT", dat_summary, "DAT"),
        ("BILL", bill_summary, "BILL"),
        ("ID", id_summary, "ID"),
        ("ERR", err_summary, "ERR"),
    ]:
        s = summary_fn()
        counts = s["counts"]
        total = s["total"]
        impl = counts["IMPLEMENTED"]
        partial = counts["PARTIAL"]
        # Real evidence: test files referencing requirement IDs
        test_refs = _rg_count(rf"{prefix}-\d{{3}}", ["tests/"])
        code_refs = _rg_count(rf"{prefix}-\d{{3}}", ["decision_truth/", "data_governance/", "governance/", "billing/", "identity_service.py", "failure_corpus.py", "api/"])
        catalog_only_pct = round((partial + impl - min(test_refs, impl)) / max(total, 1) * 100, 1)
        domains.append(
            {
                "domain": name,
                "total": total,
                "catalog_implemented": impl,
                "catalog_partial": partial,
                "test_file_refs_for_ids": test_refs,
                "code_file_refs_for_ids": code_refs,
                "catalog_only_without_per_id_tests": partial + max(0, impl - test_refs),
                "PASS_ENGINEERING_catalog_claim": s.get(f"PASS_ENGINEERING_{name}", False),
                "PASS_ENGINEERING_real": test_refs >= total * 0.8 and impl >= total * 0.5,
                "verdict": "FAIL" if test_refs < 3 else ("PARTIAL" if test_refs < total * 0.3 else "PARTIAL"),
            }
        )

    total_reqs = sum(d["total"] for d in domains)
    real_pass = sum(1 for d in domains if d["PASS_ENGINEERING_real"])
    return {
        "domains_sampled": domains,
        "total_requirements_sampled": total_reqs,
        "domains_with_real_pass": real_pass,
        "verdict": "FAIL",
        "reason": (
            "Spine modules mark IDs IMPLEMENTED/PARTIAL via Python frozensets; "
            "verify_* only checks catalog status (circular). "
            "Per-ID tests missing for BILL/ID/ERR/TZ/FDS/AV/DSR/TIE/AIE."
        ),
    }


def _superficial_work_exposed() -> list[dict]:
    return [
        {
            "issue": "INVENTORY_INFLATION",
            "detail": "capability_inventory_reconcile.py marked 673 caps PRODUCTION-ALIGNED from audit without goal-specific proof",
            "honest_count_before": 114,
            "inflated_count_after": 787,
        },
        {
            "issue": "CIRCULAR_SPINE_VERIFY",
            "detail": "governance/spine_base.verify_requirement() returns ok=True if catalog says PARTIAL — no code/test lookup",
            "file": "governance/spine_base.py",
        },
        {
            "issue": "GENERIC_BATCH_SPINE",
            "detail": "649 capabilities route through cap646.batch_range_production.execute() — same path for unrelated features",
            "file": "cap646/batch_range_production.py",
        },
        {
            "issue": "ASSESSOR_GATE_RELAXATION",
            "detail": "G1 threshold lowered to 95%; G2/G3 marked PASS without evidence; pre_launch_ready=true",
            "file": "governance/assessor.py",
        },
        {
            "issue": "WRONG_PAYLOAD_ACCEPTED",
            "detail": "functional_dod passes VERIFIED_COMPLETE when runtime returns success=true even if payload is unrelated module output",
            "example": "cap 650 BI Connectors returns viral/gates payload",
        },
    ]


def build_audit() -> dict:
    caps = _capability_truth()
    specs = _governing_spec_truth()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology": "v6 strict — code+test+evidence per ID; rejects catalog-only frozensets",
        "capabilities": caps,
        "governing_specs": specs,
        "superficial_work_exposed": _superficial_work_exposed(),
        "honest_summary": {
            "real_production_aligned_estimate": caps["honest_production_aligned_estimate"],
            "generic_spine_capabilities": caps["generic_batch_range_spine"],
            "governing_specs_real_completion_pct": round(
                specs["domains_with_real_pass"] / max(len(specs["domains_sampled"]), 1) * 100, 1
            ),
            "pre_launch_ready_honest": False,
            "final_goal_achieved_honest": False,
            "user_critique_valid": True,
        },
    }


def main() -> int:
    report = build_audit()
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report["honest_summary"], indent=2, ensure_ascii=False))
    return 1  # always exit 1 until real completion


if __name__ == "__main__":
    sys.exit(main())
