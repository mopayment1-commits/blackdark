# User Activity Audit Trail — Cross-Cutting Infrastructure

Full accountability log for every user action — merged into #1019 + #1022 + #945 + #1029.

## Policy

| Control | Value |
|---------|-------|
| Scope | All user actions — login, export, settings, RBAC, billing, queries |
| Storage | Append-only WORM `data/user_activity_audit.jsonl` |
| Dimensions | who · what · when · where · result (5D) |
| Retention | 2 years operational · 5 years institutional/legal hold |
| GDPR | Right to erasure = anonymize PII, retain hash for integrity |

## Visibility (RBAC #1022)

| Viewer | Scope |
|--------|-------|
| User | Own activity only |
| Admin | Team activity in tenant |
| Super Admin / Platform Admin | All (tenant-scoped when header set) |

## Integrations

| Ref | Behavior |
|-----|----------|
| #1019 Session Security | Auth events bridged via `bridge_auth_event()` |
| #1022 RBAC | AuthZ decisions via `bridge_authz_event()` |
| #945 Provenance | Activity cross-referenced via `data_snapshot_hash` |
| #1029 Immutable Audit | Insight actions mirrored to `data/immutable_recommendation_audit/` |
| #908 Stripe | Billing changes logged with financial audit trail |
| #1017 Incident | Suspicious patterns → auto-alert |
| #1023 GDPR | `anonymize_user_activity()` — no delete |

## API

```
GET /api/audit/user-activity
GET /api/audit/user-activity/status
GET /api/audit/user-activity/gate
GET /api/platform/user-activity/status
GET /api/platform/user-activity/gate
GET /api/platform/user-activity/audit
GET /api/platform/user-activity/e2e
```

Gateway: every `/api/` request logged in `dashboard.py` middleware before response.

## Sprint 0/1

Blocks production without audit trail enabled.
