# Launch-57 — Post-merge operations (main branch)

Run after CISA remediation PR lands on `main`.

Machine-check manifest (engineering):

```bash
python scripts/verify_launch57_post_merge_ops_manifest.py
```

Institutional manifest: `governance/launch57/LAUNCH57_POST_MERGE_OPS_MANIFEST.json`

## 1. Railway

Apply `deploy/railway/LAUNCH57_CISA_ENV.md` and verify:

```bash
python scripts/verify_railway_launch57_env.py
```

## 2. Production surface

```bash
export LAUNCH57_PROD_URL=https://blackdark-production.up.railway.app
python scripts/verify_launch57_prod_surface.py
python scripts/verify_well_known_security_txt.py --url "$LAUNCH57_PROD_URL"
python scripts/record_launch57_security_txt_prod_verification.py
python scripts/verify_launch57_p7_wp5_production_smoke.py
python scripts/record_launch57_p7_wp5_prod_smoke.py
```

## 3. QA — §8.3 V-2 CI run URLs (after green `security.yml` + `launch57-cisa-assurance`)

```bash
python scripts/verify_launch57_cross_workflow_assurance.py
python scripts/verify_launch57_ci_reviewer_evidence_bundle.py
python scripts/record_launch57_qa_v2_ci_urls.py \
  --security-run-url 'https://github.com/<org>/<repo>/actions/runs/<id>' \
  --launch57-run-url 'https://github.com/<org>/<repo>/actions/runs/<id>' \
  --recorded-by '<QA id>'
python scripts/record_launch57_independent_verification_signoff.py --step V-2 --signer-role QA --reference '<CI run note>'
python scripts/preflight_launch57_iv_human_signoffs.py
```

Spec: `governance/launch57/LAUNCH57_QA_V2_CI_RECORDING.json`

## 4. Close findings (verified)

`docs/ops/LAUNCH57_OPS_FINDING_TRANSITION_RUNBOOK.md`

```bash
python scripts/preflight_launch57_open_finding_transitions.py
python scripts/transition_launch57_finding_status.py --finding FINDING-14 --prod-url "$LAUNCH57_PROD_URL"
```

## 5. Record ops attestation

```bash
./scripts/record_launch57_ops_attestation.sh --fail-on-blockers
# implements scripts/record_launch57_ops_attestation.py
```

## 6. Executive pledge (FINDING-01)

```bash
python scripts/record_pledge_submission.py --pledge-url "https://..." --apply
python scripts/record_launch57_finding01_pledge_readiness.py
```

Then `python scripts/transition_launch57_finding_status.py --finding FINDING-01 --pledge-url ... --apply`

## 7. Regenerate status

```bash
python scripts/generate_launch57_completion_status.py
python scripts/generate_launch57_engineering_closure.py
python scripts/verify_launch57_program_closure_81.py  # expect exit 2 until all findings CLOSED
```
