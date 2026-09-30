# Launch-57 — Final CISA closure playbook (ops + executive)

**Honest rule:** Repository engineering can close FINDING-02…17 (repo). FINDING-01, 14 (prod), 18, 19 require operator/executive steps.

## 1. Railway production env

Apply `deploy/railway/LAUNCH57_CISA_ENV.md` on the web service.

## 2. Automated repo gate (CI / pre-merge)

```bash
python scripts/verify_launch57_repo_evidence.py
python -m pytest tests/test_cisa_launch57_remediation.py -q
```

## 3. Post-deploy ops matrix

```bash
export LAUNCH57_PROD_URL=https://blackdark-production.up.railway.app
export CDN_WAF_ACTIVE=1   # after Cloudflare proxy + WAF rules applied
python scripts/launch57_ops_closure_gate.py
```

Expected blockers until complete:

| Blocker | Finding | Remediation |
|---------|---------|-------------|
| `security_txt_prod` | 14 | Serve `/.well-known/security.txt` on prod URL |
| `waf_cdn` | 19 | `CDN_WAF_ACTIVE=1` + `deploy/cloudflare/waf-rules.json` deployed |
| `pentest_attestation` | 18 | Independent test + `POST /api/institutional/pentest/deposit` |

## 4. Pentest (FINDING-18)

1. Use `docs/templates/pentest_scope_LAUNCH57.md` and `docs/ops/PENTEST_ENGAGEMENT_RUNBOOK.md`
2. Deposit signed attestation per `docs/evidence/pentest_attestation.template.json`
3. Verify: `python scripts/verify_launch57_external_assurance.py` (still OPEN until WAF + pledge if applicable)

## 5. Executive pledge (FINDING-01)

Follow `docs/governance/SECURE_BY_DESIGN_PLEDGE_EXECUTION_CHECKLIST.md`

## 6. Evidence update

After each ops closure, bump `remediation_sha` in `governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json` and attach CI run URL under `governance/launch57/evidence/`.
