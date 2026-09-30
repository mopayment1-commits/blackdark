# Launch-57 CISA remediation — PR merge checklist

Use before merging Launch-57 / CISA remediation work to `main`.

## Automated gates (CI)

- [ ] `launch57-cisa-assurance` workflow green (or documented waiver)
- [ ] `security.yml` includes `tests/test_cisa_launch57_remediation.py`
- [ ] `python scripts/verify_launch57_repo_evidence.py` passes locally

## Evidence hygiene

- [ ] `governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json` updated if findings changed
- [ ] `python scripts/generate_launch57_completion_status.py` run; MD/JSON committed when inventory changed
- [ ] `remediation_sha` in evidence index matches remediation commits
- [ ] No false claims: pledge, pentest, WAF, or CISA certification in marketing/API copy

## Ops / executive (cannot be faked in PR)

- [ ] FINDING-01: pledge status documented in `SECURE_BY_DESIGN_PLEDGE_STATUS.md`
- [ ] FINDING-14: prod `security.txt` verified when releasing to production
- [ ] FINDING-18: pentest deposit only with real vendor attestation
- [ ] FINDING-19: `CDN_WAF_ACTIVE` documented when edge is live

## Reviewer sign-off

- [ ] Reviewer confirmed `LAUNCH57_REMEDIATION_COMPLETION_STATUS.md` rollup is accurate
- [ ] Authenticated API `GET /api/security/launch57-closure-status` shows `program_complete: false` until ops closed
