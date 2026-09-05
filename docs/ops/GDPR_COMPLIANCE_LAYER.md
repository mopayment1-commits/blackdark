# GDPR Compliance Layer — Sprint 0 (cross-cutting on #949)

Legal/compliance foundation merged into Sprint-0 Infrastructure — **not** a standalone module.

## Scope

| Mechanism | Implementation |
|-----------|----------------|
| Right to be Forgotten | `POST /api/user/delete-account` — soft delete 30-day grace → hard delete |
| Data Residency | Documented region per dataset — EU users = EU storage (Art. 44) |
| Explicit Consent | Logged, timestamped, immutable — no pre-ticked boxes |
| Data Minimization | email + preferences + public wallet addresses only |
| Data Portability | JSON/CSV export via #924 |
| Breach Notification | 72h playbook via #1017 |
| DPO Contact | Visible in Privacy Policy (#1018) |

## Retention alignment (#949)

| Data type | Retention |
|-----------|-----------|
| Personal data | Account lifetime + 30 days |
| Logs | 2 years |
| Audit | 5 years |

## API

```
GET  /api/privacy/gdpr/status
GET  /api/privacy/gdpr/residency
GET  /api/privacy/gdpr/retention
GET  /api/privacy/gdpr/dpo
GET  /api/privacy/gdpr/breach-playbook
POST /api/privacy/gdpr/consent
POST /api/privacy/gdpr/portability
POST /api/user/delete-account
GET  /api/privacy/gdpr/production-gate
GET  /api/privacy/gdpr/e2e          (admin)
```

## Production gate

**Blocks production launch** if GDPR compliance incomplete.

## Fee DB

Ops cost per deletion/portability request logged — no user-facing fee.
