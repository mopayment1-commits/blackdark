# WebAuthn / Passkeys (Phishing-Resistant Authentication)

**Status:** Launch-57 Phase 3 — TOTP default enrollment enforced via `USER_MFA_ENROLL_REQUIRED`; WebAuthn **planned**.

## Current phishing-resistant controls

1. **TOTP** (RFC 6238) — required enrollment when `USER_MFA_ENROLL_REQUIRED=true` (production default)
2. **Enterprise OIDC SSO** — customers may enforce phishing-resistant MFA at IdP (Auth0/Okta passkeys)

## WebAuthn delivery plan

| Milestone | Deliverable |
|-----------|-------------|
| L57-WA-1 | Add `webauthn` optional dependency + `webauthn_service.py` register/authenticate |
| L57-WA-2 | API `/api/auth/webauthn/*` + tests |
| L57-WA-3 | Prefer WebAuthn over TOTP when credential present |

Until L57-WA-2 ships, `security_posture` reports `phishing_resistant: idp_or_totp_enroll_required`.
