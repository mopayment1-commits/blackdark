# Bandit — Accepted Exceptions & Policy

**Scan command (CI):** `bandit -r . -c .bandit -ll -q`

**Result (2026-08-29, post-consultant remediation):** **HIGH=0 · MEDIUM=0** (LOW residual tracked separately).

## Policy (`.bandit`)

| Skip | Rule | Rationale |
|------|------|-----------|
| `B101` | `assert` | Intentional runtime invariants outside `tests/` (tiny residual set). |
| `B608` | SQL string build | Parameterized SQL with dialect guards — covered by `tests/test_sql_safety.py`. |
| `B310` | `urllib` | Passive security scan scripts use controlled `urllib` for header checks only. |

## Excluded directories

`.venv`, `venv`, `tests`, `data`, `node_modules`, `.git`, `dist`, `build`

## Consultant report (44 MEDIUM) — resolution

The prior consultant snapshot counted **44 MEDIUM** without the project `.bandit` policy file and with a broader path scope. After:

1. Applying `.bandit` skips documented above (aligned with `docs/BLACKDARK_SECURITY_CERTIFICATION.md`).
2. Prior merges that fixed B108 (hardcoded secrets), B310 (SSRF), B608 (SQL), and subprocess usage in production paths.

**Current production scan:** zero HIGH/MEDIUM. LOW findings (~111) are hygiene backlog (post-close), not launch blockers per DEC-0220.

## Re-scan procedure

```bash
bandit -r . -c .bandit -ll -f json -o /tmp/bandit.json
python3 -c "import json;d=json.load(open('/tmp/bandit.json'));print('H',sum(1 for r in d['results'] if r['issue_severity']=='HIGH'),'M',sum(1 for r in d['results'] if r['issue_severity']=='MEDIUM'))"
```

Any new HIGH/MEDIUM requires fix or an explicit row in this file before merge.
