# Auth, Identity & Profile (Binding)

**Login identity:** email (primary).  
**Optional public handle:** `@username` for Proof Card sharing — not used to log in.  
**Phone/SMS auth:** not in v1.  
**Currency note:** billing remains USD via hosted PSP (see `docs/PAYMENTS_USD_SECURITY.md`).

## Login methods

| Method | Status |
|--------|--------|
| Email + password | Yes |
| Google OAuth | Yes when `OAUTH_GOOGLE_CLIENT_ID/SECRET` set |
| GitHub OAuth | Yes when configured |
| MFA TOTP | Optional; challenge completed in Login UI |
| Phone | No (deferred) |

## Recovery

- `POST /api/auth/forgot-password` → one-time link → `/reset-password`
- `POST /api/auth/forgot-username` → email reminder (login is email; optional @username)
- Tokens hashed at rest (`auth_tokens`); short TTL; single-use
- Email via SMTP or durable `email_outbox` queue

## Registration

- Display name + optional username + email + password (min 10, blocked commons)
- Required acceptance of Terms / Privacy / Risk Disclaimer
- Email verification link issued on signup
- 7-day Decision Pro trial unchanged

## Profile (`/profile`)

- Display name, @username, avatar (initials SVG default or upload)
- UI language, UX mode, timezone, Telegram chat id
- Plan / billing links (USD)
- MFA enroll/confirm/disable
- Change password / set password (OAuth users)
- Logout all sessions
- Resend verification

## Security standards

- NIST SP 800-63B-inspired password policy
- OAuth `state` CSRF stored and consumed
- Session cookie HttpOnly path (existing middleware)
- No PAN/CVV (payments separate)
- GDPR export/erase via existing privacy routes

## Env

```
OAUTH_GOOGLE_CLIENT_ID=
OAUTH_GOOGLE_CLIENT_SECRET=
OAUTH_GITHUB_CLIENT_ID=
OAUTH_GITHUB_CLIENT_SECRET=
SMTP_HOST= SMTP_PORT= SMTP_USER= SMTP_PASSWORD= SMTP_FROM=
IDENTITY_DEBUG_TOKENS=true   # dev only — returns reset/verify links in API JSON
IDENTITY_AVATAR_DIR=data/avatars
APP_BASE_URL=https://your.domain
```

## APIs

- `GET /api/auth/identity`
- `POST /api/auth/register|login|logout|logout-all`
- `POST /api/auth/forgot-password|reset-password|change-password|forgot-username`
- `GET /api/auth/verify-email` · `POST /api/auth/resend-verification`
- `PATCH /api/auth/profile` · `POST|DELETE /api/auth/avatar` · `GET /api/auth/avatar/{file}`
- MFA + OAuth routes (existing)
