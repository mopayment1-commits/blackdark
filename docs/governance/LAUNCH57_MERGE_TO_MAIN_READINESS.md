# Launch-57 CISA remediation — merge to `main` readiness

## Engineering merge (this PR)

Institutional manifest: `governance/launch57/LAUNCH57_MERGE_TO_MAIN_READINESS_MANIFEST.json`

```bash
python scripts/verify_launch57_merge_to_main_readiness_manifest.py
```

Safe to merge when:

```bash
python scripts/verify_launch57_merge_readiness.py
python scripts/verify_launch57_program_integrity_report.py
python scripts/run_launch57_engineering_verification_suite.py
python scripts/verify_launch57_pr_merge_checklist_gates.py
```

Expect:

- `safe_to_merge_engineering: true`
- `program_complete: false`
- Open ops findings **01 / 18 / 19** (and 14 repo-until-prod-verify) documented

## Before merge (reviewer)

1. [ ] PR template `launch57_cisa_remediation` completed
2. [ ] `LAUNCH57_PR_MERGE_CHECKLIST.md`
3. [ ] CI: `.github/workflows/launch57-cisa-assurance.yml` + `.github/workflows/security.yml` green
4. [ ] No marketing/API text claiming CISA certification or signed pledge

## After merge to `main`

Follow `docs/ops/LAUNCH57_POST_MERGE_OPS.md` and `governance/launch57/LAUNCH57_POST_MERGE_OPS_MANIFEST.json`.

## Baseline

Inventory baseline SHA: `e73f398d4048723bd10670beab14a0d18ceb19ef` (PR #493 Launch-57 line).
