#!/usr/bin/env python3
"""Verify CISA remediation evidence paths referenced in the evidence index exist in repo."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance" / "launch57" / "CISA_REMEDIATION_EVIDENCE_INDEX.json"
SKIP_PREFIXES = ("GET ", "POST ")


def _paths_from_finding(finding: dict) -> list[str]:
    out: list[str] = []
    for item in finding.get("evidence", []):
        if not isinstance(item, str) or item.startswith(SKIP_PREFIXES):
            continue
        out.append(item)
    extra = finding.get("ops_runbook") or finding.get("package")
    if isinstance(extra, str) and not extra.startswith("http"):
        out.append(extra)
    return out


def main() -> int:
    if not INDEX.is_file():
        print(f"MISSING index: {INDEX}", file=sys.stderr)
        return 1
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    missing: list[str] = []
    checked = 0
    for fid, finding in data.get("findings", {}).items():
        for rel in _paths_from_finding(finding):
            path = ROOT / rel
            checked += 1
            if not path.is_file():
                missing.append(f"{fid}: {rel}")
    meta_keys = (
        "ops_closure_gate",
        "ci_workflow",
        "repo_evidence_gate",
        "ops_playbook",
        "railway_env_gate",
        "prod_surface_gate",
        "railway_env_spec",
        "open_findings_register",
        "closure_report_script",
        "ops_attestation_recorder",
        "release_evidence_publisher",
        "completion_status_md",
        "completion_status_json",
        "completion_status_generator",
        "pr_merge_checklist",
        "pr_template",
        "finding_inventory_lock",
        "finding_inventory_gate",
        "engineering_closure_declaration_md",
        "engineering_closure_json",
        "engineering_closure_generator",
        "ops_finding_transition",
        "ops_finding_transition_runbook",
        "generated_artifacts_freshness_gate",
        "merge_readiness_gate",
        "merge_readiness_doc",
        "post_merge_ops_doc",
        "pledge_submission_recorder",
        "normative_traceability",
        "normative_traceability_gate",
        "executive_summary_ar",
        "independent_verification_ar",
        "independent_verification_gate",
        "independent_verification_register",
        "release_attestation_82",
        "release_attestation_82_gate",
        "release_attestation_ar",
        "evidence_class_register",
        "evidence_class_register_gate",
        "program_closure_81_gate",
        "ntia_sbom_gap_analysis",
        "sbom_ntia_scope_gate",
        "security_lead_inventory_rerun_gate",
        "finding14_prod_run_recorder",
        "round_16_ops_evidence_ar",
        "p7_wp5_production_smoke",
        "p7_wp5_prod_smoke_recorder",
        "qa_ci_bundle_gate",
        "ops_v3_bundle_gate",
        "round_17_p7_wp5_ar",
        "open_ops_closure_package",
        "open_ops_closure_package_gate",
        "legal_v4_bundle_gate",
        "legal_review_signoff_recorder",
        "round_18_open_ops_ar",
        "program_authority",
    )
    for rel in [data.get(k, "") for k in meta_keys]:
        if not rel or rel.startswith("GET "):
            continue
        path = ROOT / rel if "/" in rel else None
        if path and path.is_file():
            checked += 1
        elif path:
            missing.append(f"meta: {rel}")
    if missing:
        print("MISSING evidence paths:", file=sys.stderr)
        for line in missing:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print(f"PASS: {checked} evidence paths present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
