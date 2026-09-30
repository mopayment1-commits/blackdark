# Launch-57 — Open findings register (honest)

Generated from `CISA_REMEDIATION_EVIDENCE_INDEX.json`. **Not** a certification.

| ID | Status | Owner | Closure action |
|----|--------|-------|----------------|
| FINDING-01 | OPEN_EXECUTIVE | Executive / GRC | CISA portal pledge submission + URL recorded |
| FINDING-11 | CLOSED_PARTIAL | Security Lead + Release | LAUNCH57_SBOM_SEC_LEAD_APPROVAL_ID or container/Syft SBOM + transition_launch57_finding_status.py --finding FINDING-11 --apply |
| FINDING-14 | CLOSED_REPO | Ops | record_launch57_security_txt_prod_verification.py + transition_launch57_finding_status.py --finding FINDING-14 --apply |
| FINDING-18 | OPEN_OPS | Security / vendor | Signed pentest deposit + verify_pentest_attestation() |
| FINDING-19 | OPEN_OPS | Infra | CDN_WAF_ACTIVE=1 + verify_edge_waf_cdn exit 0 |

**Ops closure package (SSOT):** `governance/launch57/LAUNCH57_OPEN_OPS_CLOSURE_PACKAGE.json`

**Aggregate report:** `python scripts/launch57_closure_report.py`
**PR merge gates:** `python scripts/verify_launch57_pr_merge_checklist_gates.py`

Regenerate: `python scripts/generate_launch57_open_findings_register.py`
