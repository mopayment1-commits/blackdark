# CI Critical Gate evidence policy (permanent)

**Effective:** 2026-08-31  
**Status:** ADOPTED — applies to all future PRs including batch merges and `main` promotions.

---

## Rule

Every pull request that changes application code, tests, CI workflows, or capability artifacts **must** include in its description (or linked completion report):

1. **URL** to the latest **CI Critical Gate Suite** GitHub Actions run for that PR branch, and  
2. **Conclusion** (`success` / `failure`) copied from GitHub or CI log, and  
3. If institutional gate step ran: excerpt showing `verdict: PASS` from `verify_institutional_closure.py --ci` or pytest institutional gate.

**No exceptions** for batch work, draft PRs, or merge chains (05→main, 06→main, etc.).

---

## Authoritative workflow

| Workflow file | Job name | Merge gate? |
|---------------|----------|-------------|
| `.github/workflows/ci.yml` | `critical` (CI Critical Gate Suite) | **YES** |
| `.github/workflows/sonarcloud.yml` | SonarCloud CI Scanner | No (parallel signal) |
| `.github/workflows/cap978-institutional-gate.yml` | institutional gate | Subset / scheduled |

---

## Evidence template (copy into PR body)

```markdown
## CI Critical Gate evidence

- **Run URL:** https://github.com/mopayment1-commits/blackdark/actions/runs/<RUN_ID>
- **Conclusion:** success
- **Branch:** cursor/<branch>-e85e
- **Institutional gate:** verdict PASS, checks_failed 0 (if applicable)
```

---

## Reference green run (batch 06 integrity session)

- **Run:** https://github.com/mopayment1-commits/blackdark/actions/runs/33341818925  
- **Conclusion:** success  
- **Commit:** `e98f5e3`  
- **Institutional gate excerpt:** `verdict: PASS`, `checks_passed: 23`, `checks_failed: 0`

---

## SonarCloud

SonarCloud failures are tracked separately in `docs/SONARCLOUD_FAILURE_REGISTER_*.md`.  
SonarCloud green is **not** required for this policy unless explicitly adopted as a merge gate in a future ADR.
