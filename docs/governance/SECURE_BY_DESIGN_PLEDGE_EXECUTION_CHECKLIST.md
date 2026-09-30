# FINDING-01 — Secure by Design Pledge execution checklist

**Owner:** Executive / GRC  
**Engineering package:** `SECURE_BY_DESIGN_PLEDGE_SUBMISSION_PACKAGE.md`

## Pre-submission (engineering — done in repo)

- [x] Secure defaults documented and enforced in code
- [x] VDP + `GET /api/security/vdp` + RFC 9116 `security.txt`
- [x] Customer security logs (≥180d) + export API
- [x] SBOM with release/git binding
- [x] Progress report template `SECURE_BY_DESIGN_PROGRESS_2026.md`

## Submission (executive — required to close FINDING-01)

- [ ] Legal/comms review of public pledge language
- [ ] Submit on CISA Secure by Design pledge portal
- [ ] Record **submission URL** and **date** via `python scripts/record_pledge_submission.py --pledge-url https://... --apply`
- [ ] Update `governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json` FINDING-01 → `CLOSED`

## Prohibited until checklist complete

- Marketing copy stating “signed CISA pledge”
- Setting `cisa_certification_claimed` or equivalent in any API response
