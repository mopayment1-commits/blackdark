# BLACKDARK Institutional Identity, Authentication, Registration, Recovery & Profile Specification

**Version:** Final Consolidated & Reconciled v1.0  
**Status:** Governing SSOT for implementation  
**Scope:** Identity + Authentication + Registration + Recovery + MFA + Sessions + Profile + Username + Avatar + Privacy + Accessibility + Enterprise Identity Readiness

## Governing References
- NIST SP 800-63-4 / SP 800-63B-4
- OWASP ASVS 5.0.0
- OWASP Authentication / Session / Forgot Password / MFA / Password Storage guidance
- FIDO2 / WebAuthn / Passkeys
- Google Identity Services / OpenID Connect
- Unicode UTS #39
- WCAG 2.2 AA
- GDPR / CCPA-CPRA where applicable
- Existing BLACKDARK Security / Entitlement / Billing / I18N architecture

## Governance Rules
- هذا الملف هو Source of Truth الحاكم.
- الـLedger للتتبع والإثبات فقط؛ عند التعارض تفوز المواصفة.
- قبل البناء: `KEEP / REUSE / IMPROVE / REPLACE / BUILD`.
- IDs ثابتة من `ID-001` إلى `ID-072`.
- لا `PASS_ENGINEERING_IDENTITY` إلا بعد `ID-071`.
- لا `PASS_LIVE` إلا بأدلة `ID-072`.
- لا ادعاء Live readiness أو external compliance بدون evidence فعلي.
- إعادة استخدام أنظمة BLACKDARK الحالية وعدم إنشاء سلطات موازية.

---

## ID-001 — الهوية الداخلية الحاكمة

`user_id` هو immutable internal identifier (يفضل UUID/UUIDv7 أو ما يعادله).
البريد: `normalized_email UNIQUE` + `email_verified`، لكنه ليس Primary Key.
نفصل بين `user_id`, `email`, `username`, `display_name`.

---


## ID-002 — وسائل الدخول P0

Email + Password، Google Identity Services، Passkeys / WebAuthn.
الهاتف SECONDARY / RECOVERY / FALLBACK فقط، وليس primary-only authentication.

---


## ID-003 — Password Policy

إذا كانت كلمة المرور العامل الوحيد: minimum=15.
إذا كانت جزءًا من MFA: minimum>=8.
BLACKDARK يمكن أن يعتمد 15 دائمًا.
max_length>=64، Unicode/spaces/paste/password managers/autofill مسموحة، composition rules=none، periodic forced rotation=none إلا عند compromise evidence.

---


## ID-004 — Unicode Passwords

عند قبول Unicode يطبق NFC normalization before hashing مع الحفاظ على semantics المتوقعة.

---


## ID-005 — Breached Password Protection

فحص breached/common/context-specific passwords عند signup/change/reset.
إذا استخدم HIBP فلا تُرسل كلمة السر نفسها؛ يستخدم privacy-preserving lookup أو equivalent.

---


## ID-006 — Password Storage

Argon2id + unique random salt + versioned parameters + rehash-on-login عند ترقية policy.
يحظر MD5/SHA-1/plain SHA-256/plain SHA-512 لتخزين كلمات المرور.

---


## ID-007 — Google Identity Services

GIS/OIDC مع openid email profile فقط.
التحقق server-side من signature, iss, aud, exp, nonce where applicable, email_verified, sub.
المعرف الثابت لمزود Google هو `sub`.

---


## ID-008 — Google Account Linking

مرفوض الربط الأعمى لمجرد تطابق البريد.
verified token → verified provider identity → detect existing account → recent auth/controlled verification → explicit secure link → audit.
فك الربط فقط مع وسيلة دخول بديلة صالحة.

---


## ID-009 — Passkeys / WebAuthn

P0: register, authenticate, list, rename, multiple passkeys, remove, revoke, last_used_at, metadata, recovery path.

---


## ID-010 — MFA Hierarchy

1) Passkeys/WebAuthn
2) TOTP
3) Recovery Codes
4) SMS fallback

---


## ID-011 — TOTP

enroll, confirm, verify, disable, replace, recovery. أي تغيير يتطلب Step-Up.

---


## ID-012 — Recovery Codes

high entropy, single-use, hashed server-side, generated as set, display/download once, regeneration invalidates old set, audited when used.

---


## ID-013 — SMS / Phone

verified_phone, OTP, recovery, fallback MFA مع expiration, attempt/send throttling, anti-flooding, SIM-swap/risk awareness. Provider pluggable.

---


## ID-014 — Progressive Registration

Stage 1: Email+Password أو Google أو Passkey + Terms acceptance + Privacy acknowledgment + separate marketing consent.
Stage 2: Email verification حيث يلزم.
Stage 3: display name, username, avatar, phone optional, language, timezone, preferences.

---


## ID-015 — Email Verification

نفصل بين account_exists, email_verified, account_status, authentication_state, entitlement_state.
Email verification لا تساوي Paid Entitlement.

---


## ID-016 — Email Validation

reasonable syntax validation → normalization → uniqueness → real email verification. لا giant RFC5322 regex.

---


## ID-017 — Username Model

display_name non-unique، username unique public handle، user_id immutable identity.

---


## ID-018 — Username Similarity / Impersonation

case folding, canonical form, reserved names, Unicode script policy, confusable skeleton, homoglyph protection, impersonation checks, rename throttling/history.
تحجز أسماء admin/support/blackdark/official/moderator.

---


## ID-019 — Username Length

Default 3–30 visible characters، Unicode-aware. يمكن أن تكون handle policy أكثر تقييدًا من Display Name.

---


## ID-020 — Account Lifecycle

PENDING_VERIFICATION, ACTIVE, LOCKED, SUSPENDED, COMPROMISED, DELETION_PENDING, DELETED, ANONYMIZED.
لا تختلط مع Subscription states.

---


## ID-021 — Forgot Password

البريد فقط، رد generic لمنع enumeration، ونفس response timing قدر الإمكان.

---


## ID-022 — Password Reset Token

random opaque token, high entropy, hash stored server-side, purpose-bound, account-bound, single-use, short expiry.

---


## ID-023 — Reset Completion

password updated, token invalidated, audit event, security notification. لا automatic login بعد reset.

---


## ID-024 — Full Account Recovery

مسارات lost password/passkey/TOTP/recovery codes/phone/email/Google/compromised account. Recovery لا يكون أضعف بكثير من auth الأصلي.

---


## ID-025 — Account Compromise Mode

SECURE_MY_ACCOUNT: revoke sessions, invalidate reset tokens, revoke refresh credentials, require reauth, review providers/MFA/passkeys, notify, preserve audit.

---


## ID-026 — Step-Up Authentication

إلزامي قبل password/email/phone change, MFA/passkey changes, linked identity changes, billing-sensitive actions, API keys, data export, account deletion, institutional admin actions.

---


## ID-027 — Session Architecture

للويب: opaque server-managed session.
Cookie: Secure, HttpOnly, SameSite, `__Host-` حيث عملي.
JWT فقط إذا احتاجت architecture token-based APIs.

---


## ID-028 — Session Lifetime

idle_timeout, absolute_timeout, remember_me_timeout, risk_adjusted_timeout, privileged_session_timeout — كلها configurable.

---


## ID-029 — Session Rotation

تجديد session ID after authentication, privilege elevation, password change, security-factor change, sensitive recovery.

---


## ID-030 — Active Sessions

يعرض device, browser, approximate location, created_at, last_seen, auth method مع revoke one/others/all.

---


## ID-031 — Risk-Based Authentication

new device/country, ASN change, impossible travel, credential stuffing, rapid IP change, proxy/Tor, suspicious recovery, sensitive action.
Device fingerprint = risk signal فقط.

---


## ID-032 — Login Abuse Protection

account/IP throttling, device/network context, progressive delay, exponential backoff, credential stuffing detection, bot challenge on risk.
5/15 مجرد configuration ابتدائي.

---


## ID-033 — CAPTCHA / Bot Protection

Provider pluggable مثل Turnstile/reCAPTCHA/equivalent، وRisk-based.

---


## ID-034 — Profile: Public Surface

avatar, display_name, username, bio optional, public links optional. لا بريد/هاتف public افتراضيًا.

---


## ID-035 — Profile: Private Identity

verified email/phone, linked providers, user ID reference, display name, username, avatar.

---


## ID-036 — Profile: Security

passkeys, MFA, recovery codes, active sessions, devices, login history, password, linked identities, recent security events.

---


## ID-037 — Profile: Subscription

tier, subscription state, paid-through, renewal date, billing portal. يعيد استخدام Billing SSOT الحالي.

---


## ID-038 — Profile: Preferences

selected language, timezone, theme, notification preferences, market preferences, display formatting.
Launch billing currency = USD_ONLY.

---


## ID-039 — I18N Integration

كل Auth/Profile/Recovery UI ورسائل الأمان والإيميلات تتبع locale المستخدم وتعيد استخدام نظام الـ38 Locale الحالي.

---


## ID-040 — Avatar Sources

upload, initials avatar, optional provider image. Gravatar optional وليس automatic lookup.

---


## ID-041 — Avatar Upload Security

allowlisted formats, real MIME detection, size/dimension/pixel limits, safe decode, server-side re-encode, EXIF strip, malware scan, UUID object key, controlled object storage, CDN, deletion lifecycle. SVG ممنوع أو sanitized بقوة.

---


## ID-042 — Avatar Moderation

AI moderation ليست إلزامية لكل upload؛ تستخدم حسب threat/community model مع توثيق الخصوصية والتكلفة. File security إلزامي.

---


## ID-043 — Audit Trail

يشمل signup, email verification, login success/failure, logout, password change/reset, email/phone change, MFA/passkey/provider changes, session creation/revoke, recovery, compromise mode, export/deletion requests.

---


## ID-044 — Security Notifications

Localized notifications عند new device, password/email/MFA/passkey/provider changes, suspicious recovery, deletion requested.

---


## ID-045 — Data Privacy

data minimization, purpose limitation, lawful basis, retention schedule, access controls, auditable consent.

---


## ID-046 — GDPR Data Export

Self-service export حيث ينطبق، machine-readable مثل JSON/CSV where appropriate.

---


## ID-047 — Account Deletion

deletion request → recent auth/step-up → deletion pending → subscription handling → session revoke → provider unlink → API credential revoke → avatar/content cleanup → personalization/history cleanup per policy → justified retention → delete/anonymize.

---


## ID-048 — Retention

Retention Registry: data category, purpose, lawful basis, retention, deletion/anonymization behavior.
30 يوم operational target لا قاعدة قانونية مطلقة.

---


## ID-049 — CCPA / CPRA

عند الانطباق: access, delete, correct, opt-out of sale/share, limit sensitive-data use where applicable.

---


## ID-050 — Cookie / Tracking Consent

يعتمد على jurisdiction, cookie purpose, analytics, advertising, necessary/non-necessary.

---


## ID-051 — Accessibility

WCAG 2.2 AA: keyboard, visible focus, focus not obscured, accessible authentication, labels, screen readers, contrast, target sizes, error association.

---


## ID-052 — Native HTML Before ARIA

native semantic HTML first, proper label, ARIA only where needed, aria-describedby, aria-invalid, live regions عند الحاجة.

---


## ID-053 — Accessible Password UX

password managers, autofill, paste, show/hide password, accessible errors, no unnecessary cognitive challenge, Passkey-compatible UX.

---


## ID-054 — UX Validation

clear labels, actionable errors, appropriate validation timing, correct mobile keyboard, logical tab order, visible focus, preserve entered values on recoverable errors.

---


## ID-055 — Enterprise Identity Readiness

Architecture-ready لـ SAML 2.0, Enterprise OIDC, SCIM, domain verification, org identity, role mapping, mandatory enterprise MFA, session policies, provisioning/deprovisioning. Full implementation P1 عند demand.

---


## ID-056 — Organization Security Policy

يمكن فرض MFA/passkey, session duration, allowed provider, SSO-only, domain restriction, admin recovery policy.

---


## ID-057 — Fail-Closed

عند uncertainty في identity verification/step-up/MFA/authorization/account ownership لا تمنح صلاحية حساسة جديدة. لا يعني حذف الحساب أو revoke شامل بلا دليل.

---


## ID-058 — Authorization Separation

Authentication ≠ Authorization. كل privileged capability تعتمد على existing BLACKDARK authorization/entitlement layer.

---


## ID-059 — Security Headers / Web Controls

إعادة استخدام canonical CSP, CSRF, Secure cookies, input/output handling, parameterized queries, rate limiting, TLS. لا implementation موازي.

---


## ID-060 — Logging Privacy

ممنوع logs تحتوي password, OTP, recovery code, passkey private key/secret, session secret, full reset token, OAuth secrets.

---


## ID-061 — Recovery Anti-Abuse

request throttling, email/OTP flood protection, generic responses, single-use tokens, short expiry, replay detection, risk alerts.

---


## ID-062 — Username Recovery

لا Forgot Username كمسار primary لأن login بالبريد/Google/Passkey. username يظهر بعد login.

---


## ID-063 — Sensitive Action Recent Authentication

delete account, change email, disable MFA, remove last passkey, billing-sensitive change, export data تتطلب auth_age threshold أو Step-Up جديد.

---


## ID-064 — Prevent Lockout

ممنوع حذف آخر طريقة دخول صالحة بدون alternative authenticator verified.

---


## ID-065 — Provider Registry

provider_identity_id, user_id, provider, provider_subject, verified_at, linked_at, last_used_at, status.

---


## ID-066 — Authenticator Registry

authenticator_id, user_id, type, created_at, verified_at, last_used_at, status, metadata، مع تقليل secrets.

---


## ID-067 — Login History

User-visible: time, device, browser, approximate location, method, status، بدون كشف fraud internals الحساسة.

---


## ID-068 — Admin Identity Operations

admin-assisted recovery: strong admin auth, authorization, reason, ticket/reference, audit, dual control for high-risk takeover recovery.

---


## ID-069 — Account Enumeration Resistance

يطبق على login حيث مناسب, signup, forgot password, email verification resend, MFA recovery, provider linking، مع رسائل وزمن لا يكشفان الحساب بسهولة.

---


## ID-070 — Testing & Evidence

تغطية happy/negative/abuse/race: session fixation, credential stuffing, enumeration, reset replay/expiry, MFA bypass, lost factor, provider-link attack, username homoglyph, password blocklist, Passkey lifecycle, session revoke, step-up bypass, deletion, export, i18n, accessibility.

---


## ID-071 — P0 Acceptance Gate

لا `PASS_ENGINEERING_IDENTITY=true` إلا إذا:
EMAIL_PASSWORD_AUTH_PASS=true
GOOGLE_OIDC_PASS=true
PASSKEY_AUTH_PASS=true
IMMUTABLE_USER_ID_PASS=true
PASSWORD_POLICY_NIST_800_63B_4_PASS=true
PASSWORD_UNICODE_NFC_PASS=true
BREACHED_PASSWORD_BLOCKLIST_PASS=true
ARGON2ID_PASS=true
USERNAME_UNIQUENESS_PASS=true
USERNAME_CONFUSABLE_PROTECTION_PASS=true
ACCOUNT_LINKING_SECURITY_PASS=true
EMAIL_VERIFICATION_PASS=true
PASSWORD_RECOVERY_PASS=true
ACCOUNT_RECOVERY_PASS=true
PASSKEY_LIFECYCLE_PASS=true
TOTP_PASS=true
RECOVERY_CODES_PASS=true
SESSION_SECURITY_PASS=true
SESSION_ROTATION_PASS=true
REMOTE_REVOCATION_PASS=true
STEP_UP_AUTH_PASS=true
LAST_AUTH_METHOD_PROTECTION_PASS=true
USER_ENUMERATION_RESISTANCE_PASS=true
RATE_LIMITING_PASS=true
CREDENTIAL_STUFFING_DEFENSE_PASS=true
RECOVERY_ABUSE_PROTECTION_PASS=true
PROFILE_PRIVACY_PASS=true
AVATAR_UPLOAD_SECURITY_PASS=true
AUDIT_TRAIL_PASS=true
SECURITY_NOTIFICATION_PASS=true
GDPR_WORKFLOWS_PASS=true
CCPA_CPRA_ARCHITECTURE_PASS=true
WCAG_2_2_AA_PASS=true
I18N_IDENTITY_SURFACES_PASS=true
KNOWN_LOCAL_IDENTITY_GAPS=[]
LOCAL_BUILDABLE_IDENTITY_REQUIREMENTS_REMAINING=0

---


## ID-072 — Live Gate

LIVE_GOOGLE_OIDC_VERIFIED
LIVE_EMAIL_DELIVERY_VERIFIED
LIVE_EMAIL_VERIFICATION_VERIFIED
LIVE_PASSWORD_RESET_VERIFIED
LIVE_PASSKEY_DESKTOP_VERIFIED
LIVE_PASSKEY_MOBILE_VERIFIED
LIVE_PASSKEY_CROSS_DEVICE_VERIFIED
LIVE_TOTP_VERIFIED
LIVE_RECOVERY_CODES_VERIFIED
LIVE_RATE_LIMITING_VERIFIED
LIVE_SESSION_REVOCATION_VERIFIED
LIVE_NEW_DEVICE_ALERT_VERIFIED
LIVE_DATA_EXPORT_VERIFIED
LIVE_ACCOUNT_DELETION_VERIFIED

حتى يتم ذلك: `PASS_LIVE_NOT_CLAIMED=true`.

---
