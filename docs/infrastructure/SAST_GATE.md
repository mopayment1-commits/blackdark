# SAST Gate — CI/CD Static Application Security Testing

**Not a standalone product.** Security gate merged into Sprint 0 CI/CD infrastructure.

## Purpose

Detect code-level vulnerabilities (SQL injection, XSS, hardcoded secrets, weak crypto) **before production** on every PR and main merge.

## Tooling

| Tool | Role |
|------|------|
| **Bandit** | Python SAST (OWASP/CWE mapped) |
| **secrets_scan** | Hardcoded API keys, passwords, PEM private keys |
| **encryption_policy_scan** | Weak crypto / TLS verify disabled (#1039) |
| **decimal_enforcement** | float() in financial modules (#1031) |
| **rbac_scan** | Missing auth Depends on API routes (#1022) |

Open-source first. Semgrep/CodeQL compatible — Bandit + custom rules documented.

## Severity Policy

| Severity | Action |
|----------|--------|
| Critical | **Block merge/deployment** |
| High | **Block merge/deployment** |
| Medium | Warning — resolve within Sprint |
| Low | Tracked only |

## CI/CD Integration

```yaml
# .github/workflows/security.yml → job: sast-gate
python scripts/run_sast_gate.py
```

- Every pull request
- Every merge to `main`
- Timeout: 10 minutes
- Parallel with pip-audit / pytest-security

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/sast/status` | Policy status |
| `GET /api/platform/sast/gate` | Production gate |
| `GET /api/platform/sast/e2e` | Self-test |
| `POST /api/platform/sast/scan` | Admin on-demand scan |

## Suppressions

File: `data/sast_suppressions.json`

- Requires `approved_by_security_lead: true`
- Documented `reason` + audit trail
- No developer self-suppress without approval

## Audit

Append-only: `data/sast_scan_audit.jsonl` — 2-year retention.

Each entry: scan_id, actor, duration, finding counts, pass/fail.

## Integrations

| Ref | Integration |
|-----|-------------|
| #1017 | Critical/high in production candidate → incident playbook |
| #1039 | Static encryption/crypto rule checks |
| #1040 | Plaintext API key pattern detection |
| #1022 | RBAC Depends() heuristic on routers |
| #1038 | Scan events in audit trail |
| #1020 | Parallel CI gate (runtime load testing separate) |

## Local Development

```bash
pip install bandit==1.8.3
python scripts/run_sast_gate.py
python scripts/run_sast_gate.py --no-bandit  # fast secrets-only
```

## Production Gate

`check_sast_production_gate()` blocks production without:
- SAST enabled on every PR
- Critical/high blocking policy
- Secrets + decimal + RBAC rulesets
- Suppression approval policy
- Audit retention ≥ 2 years
