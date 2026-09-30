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
