# Session / Account Security — 2FA Policy (#1019)

Cross-cutting auth security — **NOT** standalone. Merged into **#1019 Session/Account Security** auth layer.

## 2FA Policy

| Factor | Status |
|--------|--------|
| TOTP (Google Authenticator, Authy) | Supported |
| Hardware keys (YubiKey) | Supported via TOTP |
| Recovery codes (10, single-use, encrypted) | Supported |
| SMS | **Forbidden** (SIM-swap risk) |

## Tier enforcement

| Tier | Policy |
|------|--------|
| Free | Optional |
| Pro / Elite / Quant | Strongly recommended |
| Institutional | **Mandatory** |

## Admin

- 2FA **mandatory** for all admin accounts
- `SKIP_ADMIN_MFA` **forbidden** — bypass attempts trigger #1017 incident alert
- No exceptions in production

## Auth flow

```
login → password → 2FA (if enabled) → session
```

Unified with existing `mfa_service.py` — no separate 2FA service.

## Recovery

- 10 backup codes, single-use, encrypted at-rest
- **No email recovery** for 2FA
- Lost 2FA → support ticket + identity verification

## Audit

Every 2FA event logged (enable · disable · verify · backup code · recovery · bypass):
- Append-only `data/mfa_audit.jsonl`
- 2-year retention policy
- Mirrored to `security_events.jsonl`

## Integrations

| Ref | Behavior |
|-----|----------|
| #1022 RBAC | Role elevation requires 2FA re-verification |
| #908 Stripe | Billing cancel/upgrade/downgrade requires 2FA if enabled |
| #1017 Incident | 2FA bypass attempt → auto-alert |

## API

```
GET /api/platform/session-security/status
GET /api/platform/session-security/production-gate
GET /api/platform/session-security/mfa-audit
GET /api/platform/session-security/e2e
```

Existing user MFA endpoints: `/api/auth/mfa/*`

## Sprint 0

Blocks production if admin 2FA not configured in production environment.
