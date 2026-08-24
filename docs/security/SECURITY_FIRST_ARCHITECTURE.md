# Security-First Architecture — Feature #192

**Sprint 0 — Foundation (non-negotiable).** Security is architectural, not additive.

## Pillars

| Pillar | Implementation |
|--------|----------------|
| Threat model | `docs/security/THREAT_MODEL.md` |
| Envelope encryption | Fernet vault + AES-256-GCM upgrade path |
| Least privilege | Scoped API keys, tier gating, admin MFA |
| MFA / Step-up | TOTP + step-up for sensitive operations |
| Secret rotation | Immediate revocation + rotation drills (#165) |
| Fail-closed | Auth deny, unknown fees deny, circuit breaker (#190) |
| Security testing | pip-audit, Bandit, pytest-security in CI |
| Pentest evidence | `pentest_attestation` module + quarterly external |

## API

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/platform/security/architecture/status` | Public | Full architecture status (no secrets) |
| `GET /api/platform/security/threat-model` | Public | Threat model summary |
| `GET /api/platform/security/architecture/controls` | Public | Controls matrix |
| `GET /api/platform/security/architecture/incident-paths` | Public | Incident response paths |

## Acceptance Criteria

| Criterion | Target |
|-----------|--------|
| Threat model | Documented |
| Secrets | No plaintext storage/logging |
| Rotation/revocation | Tested (#165) |
| SAST/DAST/dependency | CI configured |
| Incident paths | Documented + API |
| Pentest evidence | Attestation module + template |

## Integration

- **#165** API Security Encryption — key vault, rotation, audit
- **#190** Circuit Breakers — platform auto-shutdown on error storm
- **security_posture.py** — engineering posture report
- **pentest_attestation.py** — external review evidence
