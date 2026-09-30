# Launch-57 — Post-merge operations (main branch)

Run after CISA remediation PR lands on `main`.

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
```

## 3. Close findings (verified)

`docs/ops/LAUNCH57_OPS_FINDING_TRANSITION_RUNBOOK.md`

## 4. Record ops attestation

```bash
./scripts/record_launch57_ops_attestation.sh --fail-on-blockers
```

## 5. Executive pledge (FINDING-01)

```bash
python scripts/record_pledge_submission.py --pledge-url "https://..." --apply
```

Then `transition_launch57_finding_status.py --finding FINDING-01 --pledge-url ... --apply`

## 6. Regenerate status

```bash
python scripts/generate_launch57_completion_status.py
python scripts/generate_launch57_engineering_closure.py
```
