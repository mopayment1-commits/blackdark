# 27 — EXTERNAL BLOCKERS VERIFICATION REGISTER

**Updated:** 2026-09-11T01:07:25Z

| Blocker ID | Procedure IDs | Reason | Required Evidence | Required Access | Expected Verifier |
|---|---|---|---|---|---|
| BLK-001 | W13-CI-002 | CI workflow re-execution requires GitHub Actions trigger on current SHA | CI run logs, pass/fail per job | L2 GitHub Actions | Platform operator |
| BLK-002 | W15-RES-002 | Postgres backup/restore drill requires dedicated DB + backup tooling | Restore drill log, RTO/RPO measurement | L2 Postgres + backup env | DBA / SRE |
| BLK-003 | W18-LEGAL-001 | Legal license review requires external counsel | License matrix, copyleft obligations, data rights | L5 Legal | External counsel |
| BLK-004 | (multiple) | Production L3 read-only verification not available | Production config parity, live auth behavior, capacity | L3 Production read-only | Operator + auditor |
| BLK-005 | W18-GIPS-001 follow-up | GIPS applicable surfaces detected; performance presentation not independently verified | Track record methodology, disclosures | L5 + domain expert | Compliance / CFA specialist |

**Rule:** Blockers do not halt unrelated procedures. 40/43 procedures executed despite 3 primary blockers.
