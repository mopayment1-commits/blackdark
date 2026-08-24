# BLACKDARK Threat Model

**Feature #192 — Security-First Architecture (Sprint 0)**

> Security is not a feature — it is the foundation. This document answers: *who threatens us, how, and what mitigations exist?*

## Scope

- User accounts, sessions, and MFA
- API keys and exchange credentials (envelope-encrypted vault)
- Platform APIs and admin surfaces
- Market data ingestion and execution paths
- Audit logs and compliance evidence

## Trust Boundaries

| Boundary | Inside | Outside |
|----------|--------|---------|
| User browser | Session cookie, CSRF checks | Untrusted input |
| API gateway | Authenticated requests | Anonymous abuse |
| Secrets vault | Encrypted credentials | Plaintext env keys (blocked in prod) |
| Admin plane | X-Admin-Key + MFA | Public internet |

---

## Threat Actors

### Actor: External attacker (credential stuffing / brute force)

- **Motivation:** Account takeover, fund theft
- **Capability:** Automated bots, leaked password lists
- **Mitigation:** Login rate limits (10/5min), MFA/TOTP, suspicious-login pattern detection (#190), audit log

### Actor: Malicious API consumer

- **Motivation:** Data scraping, API abuse, key exfiltration
- **Capability:** Valid or stolen API tokens
- **Mitigation:** Scoped API keys (#165), per-user isolation, immediate revocation, viral capacity middleware

### Actor: Insider / compromised operator

- **Motivation:** Unauthorized data access, key theft
- **Capability:** Admin credentials, server access
- **Mitigation:** Least privilege, admin MFA, audit registry, no plaintext secrets in logs

### Actor: Supply-chain attacker

- **Motivation:** Inject vulnerable dependency
- **Capability:** PyPI/npm compromise
- **Mitigation:** pip-audit in CI, hash-locked requirements, Bandit SAST

### Actor: Exchange / counterparty failure

- **Motivation:** N/A (operational risk)
- **Capability:** Withdrawal suspension, insolvency
- **Mitigation:** Withdrawal stress detection (#190), exchange health monitor, user alerts

---

## Attack Vectors

### Vector: Credential theft via log injection

- **Entry:** Application logs, error messages
- **Impact:** API key exposure
- **Mitigation:** Log redaction (#165), mask_secret, no plaintext persistence

### Vector: Session hijacking

- **Entry:** XSS, network sniffing
- **Impact:** Account takeover
- **Mitigation:** HttpOnly cookies, CSP headers, Secure flag in prod, SESSION_TOKEN_PEPPER

### Vector: Platform instability cascade

- **Entry:** Upstream failures, bug-induced 5xx storm
- **Impact:** User harm, data corruption risk
- **Mitigation:** Circuit breaker at 50% error rate (#190), auto-shutdown, alert, investigate

### Vector: Privilege escalation

- **Entry:** Cross-user API key access, admin endpoint abuse
- **Impact:** Unauthorized trading/withdrawal
- **Mitigation:** Per-user vault isolation, admin gate, fail-closed auth

### Vector: Secret sprawl in environment

- **Entry:** .env files, CI secrets
- **Impact:** Full platform compromise
- **Mitigation:** Envelope encryption, KMS/HSM recommendation, rotation drills, block env keys in prod

---

## Mitigations (Control Matrix)

### Mitigation: Envelope encryption

- Master key in KMS/HSM (operator responsibility)
- Fernet AES-128-CBC at rest; AES-256-GCM upgrade path
- No plaintext in DB, logs, or API responses

### Mitigation: Least privilege

- API key scopes (read/trade)
- Service accounts with minimal env credentials
- Execution tier gating (whale tier for live)

### Mitigation: MFA / Step-up

- TOTP enrollment for users
- Step-up required for: API key change, large withdrawal, admin ops, secret rotation

### Mitigation: Fail-closed

- Auth service failure → deny all
- Unknown venue fees → fail closed
- Circuit breaker open → platform shutdown (health endpoints exempt)

### Mitigation: Secret rotation & revocation

- Immediate revocation (#165)
- Rotation drill with re-encryption
- Audit trail for every access

### Mitigation: Continuous monitoring

- 24/7 threat pattern scan (#190)
- Security events log
- CI security pipeline (pip-audit, Bandit, pytest-security)

---

## Incident Response Paths

| Incident | Detection | Response |
|----------|-----------|----------|
| Circuit breaker trip | 50% error rate / 60s | Auto-shutdown → alert → investigate → admin reset |
| Credential compromise | Suspicious login pattern | Revoke keys → MFA step-up → audit review |
| Data breach suspected | Anomalous access | Isolate → preserve logs → compliance notify |
| Exchange withdrawal stress | Withdrawal score < 50 | Alert users → exposure guidance |

See `docs/RUNBOOK.md` and `/api/platform/security/architecture/incident-paths`.

---

## Residual Risks

- Edge WAF/CDN activation is operator responsibility (`deploy/cloudflare`, `nginx/blackdark.conf`)
- Quarterly external penetration test recommended (template: `docs/templates/pentest_scope.md`)
- SOC2/ISO27001 are organizational certifications — not granted by codebase

---

## Review Cadence

- **Quarterly:** Threat model review + external pentest
- **Per release:** Dependency scan (CI), security pytest suite
- **Continuous:** Circuit breaker monitoring, security events tail

*Last updated: Sprint 0 — Features #190 + #192*
