# AuthZ Layer — RBAC Core + SSO (Sprint 1/2 Infrastructure)

Authorization layer merged into Sprint-1 Infrastructure on top of AuthN (#1019). **Not** a standalone module.

## Canonical roles (4)

| Role | Capabilities |
|------|-------------|
| **Viewer** | Read-only |
| **Analyst** | Export reports + saved queries (#924, #978) |
| **Admin** | Billing + users + API keys (#908, #952) |
| **Super Admin** | Platform operations |

## Tenant isolation

- Role assignment = `user_id` + `tenant_id`
- Every query scoped to tenant membership
- Cross-tenant access denied at backend

## Backend enforcement

Every protected endpoint calls `authorize_request()` — no client-side-only validation.

## Audit

Every authZ decision logged: user, role, action, resource, tenant, timestamp, result.

- Append-only
- 2-year retention policy

## SSO (Sprint 2 — Pro/Institution)

- SAML 2.0 / OIDC
- IdP: Okta · Azure AD · Google Workspace
- JIT provisioning with default role **Viewer**

## API

```
GET  /api/institutional/authz/status
GET  /api/institutional/authz/matrix
GET  /api/institutional/authz/sso-status
GET  /api/institutional/authz/audit-trail
POST /api/institutional/authz/authorize
POST /api/institutional/authz/revoke-compromised
GET  /api/institutional/authz/e2e
```

## Integrations

| Ref | Behavior |
|-----|----------|
| #1019 AuthN | Authentication layer below AuthZ |
| #908 Billing | Role → tier capabilities + rate limits |
| #924 Data Export | Analyst+ only |
| #978 SQL Workspace | Analyst+ only |
| #952 Decision Certificate | Admin required |
| #1017 Incident Response | Compromised account revoke playbook |
| #1018 Privacy | Role-based access in privacy policy |

## Fee DB

Each authZ check logs cost + permission + tier.
