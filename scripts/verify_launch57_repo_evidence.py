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
        "iv_repo_bundle",
        "iv_repo_bundle_gate",
        "program_integrity_report_gate",
        "ops_playbook_dry_run",
        "round_19_iv_bundle_ar",
        "remediation_gate_index",
        "remediation_gate_index_generator",
        "remediation_gate_index_gate",
        "preflight_open_finding_transitions",
        "round_20_gate_index_ar",
        "ci_assurance_manifest",
        "ci_assurance_manifest_gate",
        "engineering_verification_suite",
        "round_21_ci_manifest_ar",
        "evidence_index_schema",
        "evidence_index_schema_gate",
        "pr_merge_checklist_gates",
        "open_findings_register_generator",
        "engineering_handoff",
        "engineering_handoff_gate",
        "round_22_handoff_ar",
        "cross_workflow_assurance",
        "cross_workflow_assurance_gate",
        "ci_reviewer_evidence_bundle",
        "ci_reviewer_evidence_bundle_generator",
        "round_23_cross_workflow_ar",
        "qa_v2_ci_recording",
        "ci_reviewer_evidence_bundle_gate",
        "qa_v2_ci_urls_recorder",
        "round_24_qa_v2_recording_ar",
        "post_merge_ops_manifest",
        "post_merge_ops_manifest_gate",
        "iv_human_signoff_preflight",
        "round_25_post_merge_ops_ar",
        "merge_to_main_readiness_manifest",
        "merge_to_main_readiness_manifest_gate",
        "round_26_merge_readiness_ar",
        "final_closure_playbook_manifest",
        "final_closure_playbook_manifest_gate",
        "round_27_final_closure_ar",
        "remediation_lifecycle_index",
        "remediation_lifecycle_index_gate",
        "open_findings_closure_readiness",
        "round_28_lifecycle_index_ar",
        "finding_11_sbom_closure_lane",
        "finding_11_sbom_closure_lane_gate",
        "finding_11_sec_lead_approval_recorder",
        "finding_11_transition_preflight",
        "round_29_finding11_sbom_ar",
        "finding_14_security_txt_closure_lane",
        "finding_14_security_txt_closure_lane_gate",
        "finding_14_transition_preflight",
        "round_30_finding14_security_txt_ar",
        "finding_18_pentest_closure_lane",
        "finding_18_pentest_closure_lane_gate",
        "finding_18_transition_preflight",
        "finding_19_waf_closure_lane",
        "finding_19_waf_closure_lane_gate",
        "finding_19_transition_preflight",
        "round_31_finding18_19_ar",
        "finding_01_pledge_closure_lane",
        "finding_01_pledge_closure_lane_gate",
        "finding_01_transition_preflight",
        "round_32_finding01_pledge_ar",
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
