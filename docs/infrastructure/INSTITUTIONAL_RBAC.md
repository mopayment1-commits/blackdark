# Institutional RBAC — #1022

Cross-cutting authorization for institutional/team accounts — **NOT** standalone. Merged into **#1022 RBAC Layer / Sprint 1 Infrastructure**.

## Institutional roles (4)

| Role | Access |
|------|--------|
| **Viewer** | Read-only (`decisions.view`, `audit.view`, `data.read`) |
| **Analyst** | Viewer + export + SQL workspace queries |
| **Admin** | Analyst + billing + users + API keys + institutional certificates |
| **Super Admin** | Admin + SSO + MFA policy + platform ops |

Legacy aliases (`compliance`, `pm`) map to institutional equivalents.

## Enforcement

- **Backend-only** — every protected endpoint calls `enforce_permission()` / `require_permission()`
- **Tenant isolation** — `org_id` = tenant; cross-tenant access denied by default (RLS contract)
- **Team management** — Admin creates/updates/deletes members in same tenant (Sprint 2)

## Audit

Every authZ decision logged (user, role, action, resource, result):
- Append-only `data/authz_audit.jsonl`
- 2-year retention policy

## Integrations

| Ref | Behavior |
|-----|----------|
| #1019 Session Security | login → password/2FA → RBAC check → resource |
| #908 Stripe | Role determines tier capabilities + rate limits |
| #924 Data Export | Analyst/Admin only |
| #978 SQL Workspace | Analyst/Admin only |
| #952 Decision Certificate | Institutional cert = Admin role required |
| #1018 ToS/Privacy | RBAC cross-referenced in privacy policy |

## API

```
GET /api/institutional/rbac/matrix
GET /api/institutional/rbac/status
GET /api/institutional/rbac/gate
GET /api/institutional/rbac/audit
GET /api/institutional/rbac/e2e
GET /api/platform/rbac/status
GET /api/platform/rbac/gate
GET /api/platform/rbac/audit
GET /api/platform/rbac/e2e
```

Team management:
```
POST   /api/institutional/orgs/{org_id}/members
POST   /api/institutional/orgs/{org_id}/roles
DELETE /api/institutional/orgs/{org_id}/members/{email}
```

## Sprint

- **Sprint 1**: RBAC Core — blocks production if incomplete
- **Sprint 2**: Institutional team management (Pro/Institution tier)
