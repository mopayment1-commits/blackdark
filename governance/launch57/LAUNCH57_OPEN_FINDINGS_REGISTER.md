# Launch-57 — Open findings register (honest)

Engineering inventory status from `CISA_REMEDIATION_EVIDENCE_INDEX.json`. **Not** a certification.

| ID | Status | Owner | Closure action |
|----|--------|-------|----------------|
| FINDING-01 | OPEN_EXECUTIVE | GRC / executive | CISA pledge + update `SECURE_BY_DESIGN_PLEDGE_STATUS.md` |
| FINDING-11 | CLOSED_PARTIAL | Engineering + release | `LAUNCH57_RELEASE_MANIFEST.json` + CI `launch57-syft-prod-lock-sbom`; optional container Syft on image |
| FINDING-14 | CLOSED_REPO | Ops | `verify_well_known_security_txt.py --url <prod>` |
| FINDING-18 | OPEN_OPS | Security / vendor | Pentest + `docs/evidence/PENTEST_DEPOSIT_LAUNCH57.md` |
| FINDING-19 | OPEN_OPS | Infra | `CDN_WAF_ACTIVE=1` + edge runbook |

**Aggregate report:** `python scripts/launch57_closure_report.py`  
**Full 19-finding rollup:** `governance/launch57/LAUNCH57_REMEDIATION_COMPLETION_STATUS.md` (regenerate via `generate_launch57_completion_status.py`)  
**Engineering closure (repo):** `docs/governance/LAUNCH57_ENGINEERING_CLOSURE_DECLARATION.md`
