# CISA Secure by Design — Progress Report (Engineering)

**Period:** Launch-57 remediation (2026)  
**Pledge signed:** Not yet — see `SECURE_BY_DESIGN_PLEDGE_SUBMISSION_PACKAGE.md`  
**This document:** Honest engineering progress toward pledge principles (not a CISA filing).

## Principles addressed in product

| Principle | Evidence |
|-----------|----------|
| Secure defaults | `PRIVATE_BY_DEFAULT`, admin MFA, `USER_MFA_ENROLL_REQUIRED` |
| Transparency | VDP (`/api/security/vdp`), security.txt, public `/api/security/status` |
| Vulnerability reduction | XSS roadmap, SQL safety tests, dependency scanning |
| Supply chain | CycloneDX SBOM + git SHA binding |
| Customer logging | 180-day policy + export API |

## Engineering round 25 (post-merge ops manifest + §8.3 human preflight)

- `LAUNCH57_POST_MERGE_OPS_MANIFEST.json` + `verify_launch57_post_merge_ops_manifest.py`
- `preflight_launch57_iv_human_signoffs.py` — PENDING/RECORDED report only
- `LAUNCH57_POST_MERGE_OPS.md` §8.3 V-2 QA CI section
- `LAUNCH57_ROUND_25_POST_MERGE_OPS_AR.md`

## Engineering round 24 (§8.3 V-2 CI URL recording spec + reviewer bundle gate)

- `LAUNCH57_QA_V2_CI_RECORDING.json` + `record_launch57_qa_v2_ci_urls.py` (gitignored `evidence/V-2/`)
- `verify_launch57_ci_reviewer_evidence_bundle.py` — structure parity with evidence index / cross-workflow
- IV register `repo_automation` + IV repo bundle entries for V-2
- `LAUNCH57_ROUND_24_QA_V2_RECORDING_AR.md`

## Engineering round 23 (§8.3 V-2 cross-workflow CI + reviewer evidence bundle)

- `LAUNCH57_CROSS_WORKFLOW_ASSURANCE.json` + `verify_launch57_cross_workflow_assurance.py` (`security.yml` + `launch57-cisa-assurance.yml`)
- `generate_launch57_ci_reviewer_evidence_bundle.py` → `LAUNCH57_CI_REVIEWER_EVIDENCE_BUNDLE.json` (URLs for QA only)
- `LAUNCH57_ROUND_23_CROSS_WORKFLOW_AR.md`

## Engineering round 22 (§9 index schema + PR checklist gates + engineering handoff)

- `LAUNCH57_EVIDENCE_INDEX_SCHEMA.json` + `verify_launch57_evidence_index_schema.py`
- `verify_launch57_pr_merge_checklist_gates.py` + `generate_launch57_open_findings_register.py`
- `LAUNCH57_ENGINEERING_HANDOFF.json` + `verify_launch57_engineering_handoff.py`
- `LAUNCH57_ROUND_22_HANDOFF_AR.md`

## Engineering round 21 (CI E-TEST manifest + engineering verification suite)

- `LAUNCH57_CI_ASSURANCE_MANIFEST.json` + `verify_launch57_ci_assurance_manifest.py` (§3.2 / workflow parity)
- `run_launch57_engineering_verification_suite.py` — local reviewer entry
- Gate index / completion `phase` sync in `verify_launch57_generated_artifacts_fresh.py`
- `LAUNCH57_ROUND_21_CI_MANIFEST_AR.md`

## Engineering round 20 (remediation gate index + transition preflight)

- `LAUNCH57_REMEDIATION_GATE_INDEX.json` + `generate_launch57_gate_index.py` / `verify_launch57_gate_index.py`
- `preflight_launch57_open_finding_transitions.py` — dry-run only
- API/docs navigation: `gate_index` in `launch57-closure-status` inventory attachment
- `LAUNCH57_ROUND_20_GATE_INDEX_AR.md`

## Engineering round 19 (§8.3 IV repo bundle + program integrity report)

- `LAUNCH57_INDEPENDENT_VERIFICATION_REPO_BUNDLE.json` + `verify_launch57_iv_repo_bundle.py`
- `verify_launch57_program_integrity_report.py` (§8.1 honest incomplete + governance JSON flags)
- `run_launch57_ops_playbook_dry_run.py` — no `transition --apply`
- `LAUNCH57_ROUND_19_IV_BUNDLE_AR.md`

## Engineering round 18 (open ops closure package + §8.3 V-4 + FINDING 01/18/19 recorders)

- `LAUNCH57_OPEN_OPS_CLOSURE_PACKAGE.json` + `verify_launch57_open_ops_closure_package.py`
- `verify_launch57_legal_v4_bundle.py` + `record_launch57_legal_review_signoff.py`
- E-OPS/E-LEGAL recorders for FINDING-01/18/19 (gitignored evidence; no auto-close)
- Ops gate matrix includes `p7_wp5_production_smoke`

## Engineering round 17 (L57-P7-WP5 production smoke + §8.3 V-2/V-3 bundles)

- `verify_launch57_p7_wp5_production_smoke.py` + `record_launch57_p7_wp5_prod_smoke.py` (Phase 7 WP5)
- `verify_launch57_qa_ci_bundle.py` (§8.3 V-2 repo), `verify_launch57_ops_v3_bundle.py` (§8.3 V-3)
- `LAUNCH57_ROUND_17_P7_WP5_AR.md`

## Engineering round 16 (FINDING-11 NTIA gap + FINDING-14 E-RUN + §8.3 V-1 bundle)

- `LAUNCH57_NTIA_SBOM_GAP_ANALYSIS.json` + `verify_launch57_sbom_ntia_scope.py` (program §6 FINDING-11 / NTIA-MIN)
- `record_launch57_security_txt_prod_verification.py` (RFC-9116 E-RUN; no auto-close)
- `verify_launch57_security_lead_inventory_rerun.py` (§8.3 V-1 repo gate bundle)
- `LAUNCH57_ROUND_16_OPS_EVIDENCE_AR.md`; transition rules updated for FINDING-11

## Engineering round 15 (§8.2 attestation lock + §3.2 evidence classes + §8.1 gate)

- `LAUNCH57_RELEASE_ATTESTATION_82.json` + `verify_launch57_release_attestation_82.py` (wording locked to program §8.2; forbidden claim scan)
- `LAUNCH57_EVIDENCE_CLASS_REGISTER.json` + `verify_launch57_evidence_class_register.py` (§6 verification → E-ART/E-TEST/…)
- `verify_launch57_program_closure_81.py` — exit 2 until all findings `CLOSED` exactly
- `record_launch57_independent_verification_signoff.py` — gitignored §8.3 human records
- `LAUNCH57_RELEASE_ATTESTATION_AR.md`

## Engineering round 14 (program §8.3 independent verification register)

- `LAUNCH57_INDEPENDENT_VERIFICATION_REGISTER.json` + `verify_launch57_independent_verification.py` (V-1..V-4; human sign-off honest)
- `LAUNCH57_INDEPENDENT_VERIFICATION_AR.md` — Arabic institutional summary tied to program §8.3 only
- Merge readiness + `launch57-cisa-assurance` CI include §8.3 repo gates

## Engineering round 13 (normative traceability + AR executive summary)

- `LAUNCH57_NORMATIVE_TRACEABILITY.json` + `verify_launch57_normative_traceability.py` (program §2/§7 only)
- `LAUNCH57_REMEDIATION_EXECUTIVE_SUMMARY_AR.md` — facts from evidence index + program §8.2 wording

## Engineering round 12 (merge readiness + post-merge ops)

- `verify_launch57_merge_readiness.py` — single pre-merge engineering gate
- `LAUNCH57_MERGE_TO_MAIN_READINESS.md`, `LAUNCH57_POST_MERGE_OPS.md`
- `record_pledge_submission.py` for FINDING-01 URL (executive)

## Engineering round 11 (ops transition tool + artifact freshness)

- `transition_launch57_finding_status.py` — verified CLOSED transitions only (no fake pentest)
- `verify_launch57_generated_artifacts_fresh.py` — remediation_sha sync in CI
- `LAUNCH57_OPS_FINDING_TRANSITION_RUNBOOK.md`

## Engineering round 10 (engineering closure declaration + inventory lock)

- `FINDING_INVENTORY_LOCK.json` + `verify_launch57_finding_inventory_lock.py` (CI gate)
- `LAUNCH57_ENGINEERING_CLOSURE_DECLARATION.md` — formal repo closure; ops/executive still open

## Engineering round 9 (API inventory + PR checklist)

- `launch57_completion_status.py` embedded in `GET /api/security/launch57-closure-status`
- `LAUNCH57_PR_MERGE_CHECKLIST.md` + GitHub PR template `launch57_cisa_remediation.md`

## Engineering round 8 (completion status rollup + CI evidence bundle)

- `generate_launch57_completion_status.py` → MD + JSON for all FINDING-01…19
- CI artifact `launch57-release-evidence-bundle` (manifest, SBOM, completion status)

## Engineering round 7 (ops attestation log + release SBOM manifest)

- `record_launch57_ops_attestation.py` / `.sh` — honest ops gate records (gitignored JSON)
- `publish_launch57_release_evidence.py` + `LAUNCH57_RELEASE_MANIFEST.json` + release notes template
- Ops gate: `LAUNCH57_SKIP_ENGINEERING_BASELINE` for faster operator reruns

## Engineering round 6 (pentest deposit path + closure report + prod CI)

- `docs/evidence/PENTEST_DEPOSIT_LAUNCH57.md` + `prepare_pentest_deposit_launch57.py`
- `launch57_closure_report.py` + `LAUNCH57_OPEN_FINDINGS_REGISTER.md`
- CI: `validate_syft_sbom_artifact.py`; optional prod surface via `LAUNCH57_PROD_URL` secret

## Engineering round 5 (Railway + prod surface + Syft CI)

- `governance/launch57/RAILWAY_CISA_ENV_EXPECTATIONS.json` + `verify_railway_launch57_env.py`
- `verify_launch57_prod_surface.py` — prod HTTP smoke (security.txt, VDP, status)
- `generate_syft_lockfile_sbom.sh` — CI job `syft-prod-lock-sbom` (FINDING-11 supplement)
- Ops gate matrix: `railway_env`, `prod_security_surface`

## Engineering round 4 (supply chain + closure playbook)

- `webauthn` pinned in `requirements.lock.txt` / `requirements.hashes.txt` and prod requirements
- `scripts/verify_launch57_repo_evidence.py` — evidence index path gate
- `docs/ops/LAUNCH57_FINAL_CLOSURE_PLAYBOOK.md` — FINDING-01/14/18/19 ops steps
- `docs/governance/SECURE_BY_DESIGN_PLEDGE_EXECUTION_CHECKLIST.md` — FINDING-01 executive
- Ops gate uses `LAUNCH57_PROD_URL` only for live security.txt

## Engineering round 3 (ops gates)

- `scripts/collect_engineering_security_baseline.py` → CI artifact (not a pentest)
- `scripts/launch57_ops_closure_gate.py` → post-deploy matrix (WAF, security.txt prod, attestation)
- `deploy/railway/LAUNCH57_CISA_ENV.md` → production env checklist
- Workflow: `.github/workflows/launch57-cisa-assurance.yml`

## Next executive action

Submit pledge on CISA portal and link URL in `SECURE_BY_DESIGN_PLEDGE_STATUS.md`.
