# Security Verification Evidence — Feature #191

**Sprint 0/1 — Security Gate (non-negotiable).** Integrates with #192.

## Capabilities

| Capability | Implementation |
|------------|----------------|
| SAST | Bandit in CI + optional local run |
| DAST | `scripts/wave_00_passive_security_scan.py` |
| Dependency scan | pip-audit in `.github/workflows/security.yml` |
| Secrets scan | Pattern scanner (AWS keys, private keys, hardcoded secrets) |
| Authz regression | pytest suite inventory (6 modules) |
| Severity classification | critical / high / medium / low / info |
| Signed suppression | HMAC-signed rationale required |
| Evidence retention | 3 years minimum |
| Release gate | PASS only when no critical unresolved findings |

## API

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/platform/security/verification/status` | Public | Gate status + headline |
| `GET /api/platform/security/verification/evidence-pack` | Public | Full evidence pack |
| `GET /api/platform/security/verification/release-gate` | Public | PASS/BLOCKED |
| `POST /api/platform/security/verification/run-gates` | Admin | Run security gates |
| `POST /api/platform/security/verification/suppress` | Admin | Signed suppression |
| `POST /api/platform/security/verification/remediate` | Admin | Remediation proof |

## Release Gate Headline Example

```
Open findings: 2 (medium) | Remediated: 15 | Gate: ✅ Pass
```

## Acceptance Criteria

| Criterion | Target |
|-----------|--------|
| No critical unresolved | Enforced at release gate |
| Scans reproducible | CI tool versions tracked |
| Suppression | Signed rationale required |
| Authz regression | 6 test modules present |
| Evidence retained | 3+ years |
