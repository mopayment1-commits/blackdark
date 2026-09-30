# Customer Security Log Policy

**Normative:** CISA Secure by Demand (August 2024) — SaaS security logs  
**Launch-57 default retention:** 180 days (`SECURITY_LOG_RETENTION_DAYS`)

## Categories (CISA-aligned)

| Category | Event kinds (examples) |
|----------|----------------------|
| Configuration change | `config_change`, `admin_policy_update`, `sso_configure` |
| Identity / token | `login_success`, `login_failure`, `logout`, `mfa_enroll`, `sso_login`, `session_revoke` |
| Business data access | `audit_export`, `decision_create`, `data_export` (tenant-scoped) |

## Customer access

- Authenticated users: `GET /api/security/customer-logs/export` (JSON/CSV)
- Organization admins: same endpoint with org scope when `org_id` present
- **No separate security-log surcharge** for baseline export (see `COMMERCIAL_SECURITY_FEATURES.md`)

## Retention

- Minimum **180 days** durable storage (JSONL + optional Postgres mirror)
- Prune job: `security_events.prune_expired_events()` (scheduled via ops or CI smoke)

## Not in scope

- Raw SIEM/SOC2 certification
- Unlimited forensic retention without contract
