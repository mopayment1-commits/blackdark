#!/usr/bin/env python3
"""Build IDENTITY_IMPLEMENTATION_INDEX.json from spec bindings."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BINDINGS: dict[str, dict] = {
    "ID-001": {"reuse": "IMPROVE", "module_paths": ["database.py", "identity/account_states.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Immutable internal identity"},
    "ID-002": {"reuse": "IMPROVE", "module_paths": ["auth_service.py", "oauth_service.py", "identity/webauthn_service.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "P0 login methods"},
    "ID-003": {"reuse": "IMPROVE", "module_paths": ["identity/password_policy.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Password policy"},
    "ID-004": {"reuse": "BUILD", "module_paths": ["identity/password_policy.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Unicode passwords NFC"},
    "ID-005": {"reuse": "BUILD", "module_paths": ["identity/breached_passwords.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Breached password protection"},
    "ID-006": {"reuse": "REPLACE", "module_paths": ["identity/password_storage.py", "auth_service.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Argon2id storage"},
    "ID-007": {"reuse": "IMPROVE", "module_paths": ["oauth_service.py", "identity/account_linking.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Google OIDC"},
    "ID-008": {"reuse": "BUILD", "module_paths": ["identity/account_linking.py", "identity/provider_registry.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Secure account linking"},
    "ID-009": {"reuse": "BUILD", "module_paths": ["identity/webauthn_service.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Passkeys/WebAuthn"},
    "ID-010": {"reuse": "REUSE", "module_paths": ["mfa_service.py", "identity/webauthn_service.py"], "test_paths": ["tests/test_spine_database_auth.py"], "title": "MFA hierarchy"},
    "ID-011": {"reuse": "REUSE", "module_paths": ["mfa_service.py"], "test_paths": ["tests/test_spine_database_auth.py"], "title": "TOTP lifecycle"},
    "ID-012": {"reuse": "REUSE", "module_paths": ["mfa_service.py"], "test_paths": ["tests/test_spine_database_auth.py"], "title": "Recovery codes"},
    "ID-013": {"reuse": "BUILD", "module_paths": ["identity/phone_otp.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "SMS/phone fallback"},
    "ID-014": {"reuse": "IMPROVE", "module_paths": ["auth_service.py", "identity_service.py"], "test_paths": ["tests/test_auth_identity_profile.py"], "title": "Progressive registration"},
    "ID-015": {"reuse": "REUSE", "module_paths": ["identity_service.py", "database.py"], "test_paths": ["tests/test_auth_identity_profile.py"], "title": "Email verification"},
    "ID-016": {"reuse": "REUSE", "module_paths": ["identity_service.py"], "test_paths": ["tests/test_auth_identity_profile.py"], "title": "Email validation"},
    "ID-017": {"reuse": "IMPROVE", "module_paths": ["identity/username_policy.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Username model"},
    "ID-018": {"reuse": "BUILD", "module_paths": ["identity/username_policy.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Username confusables"},
    "ID-019": {"reuse": "IMPROVE", "module_paths": ["identity/username_policy.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Username length"},
    "ID-020": {"reuse": "BUILD", "module_paths": ["identity/account_states.py", "database.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Account lifecycle"},
    "ID-021": {"reuse": "REUSE", "module_paths": ["identity_service.py", "identity/login_abuse.py"], "test_paths": ["tests/test_auth_identity_profile.py"], "title": "Forgot password"},
    "ID-022": {"reuse": "REUSE", "module_paths": ["identity_service.py", "database.py"], "test_paths": ["tests/test_auth_identity_profile.py"], "title": "Password reset token"},
    "ID-023": {"reuse": "IMPROVE", "module_paths": ["api/routers/auth.py", "identity/security_notifications.py"], "test_paths": ["tests/test_auth_identity_profile.py"], "title": "Reset completion"},
    "ID-024": {"reuse": "BUILD", "module_paths": ["identity/account_recovery.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Full account recovery"},
    "ID-025": {"reuse": "BUILD", "module_paths": ["identity/secure_account.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Account compromise mode"},
    "ID-026": {"reuse": "BUILD", "module_paths": ["identity/step_up.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Step-up authentication"},
    "ID-027": {"reuse": "REUSE", "module_paths": ["auth_service.py", "security_middleware.py"], "test_paths": ["tests/test_p1_session_hardening.py"], "title": "Session architecture"},
    "ID-028": {"reuse": "BUILD", "module_paths": ["identity/session_service.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Session lifetime"},
    "ID-029": {"reuse": "BUILD", "module_paths": ["identity/session_service.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Session rotation"},
    "ID-030": {"reuse": "BUILD", "module_paths": ["identity/session_service.py", "api/routers/auth.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Active sessions"},
    "ID-031": {"reuse": "BUILD", "module_paths": ["identity/risk_auth.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Risk-based authentication"},
    "ID-032": {"reuse": "IMPROVE", "module_paths": ["identity/login_abuse.py", "security_auth.py"], "test_paths": ["tests/test_d13_auth_abuse.py"], "title": "Login abuse protection"},
    "ID-033": {"reuse": "BUILD", "module_paths": ["identity/bot_protection.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "CAPTCHA/bot protection"},
    "ID-034": {"reuse": "REUSE", "module_paths": ["templates/profile.html", "api/routers/auth.py"], "test_paths": ["tests/test_visible_chrome_critical_surfaces.py"], "title": "Public profile"},
    "ID-035": {"reuse": "REUSE", "module_paths": ["api/routers/auth.py", "database.py"], "test_paths": ["tests/test_auth_identity_profile.py"], "title": "Private profile identity"},
    "ID-036": {"reuse": "IMPROVE", "module_paths": ["mfa_service.py", "identity/webauthn_service.py", "api/routers/auth.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Profile security"},
    "ID-037": {"reuse": "REUSE", "module_paths": ["billing/subscription_engine.py", "api/routers/auth.py"], "test_paths": ["tests/test_billing_subscription_engine.py"], "title": "Profile subscription"},
    "ID-038": {"reuse": "REUSE", "module_paths": ["database.py", "api/routers/auth.py"], "test_paths": ["tests/test_auth_identity_profile.py"], "title": "Profile preferences"},
    "ID-039": {"reuse": "REUSE", "module_paths": ["i18n_enforcement.py", "identity/security_notifications.py"], "test_paths": ["tests/test_i18n_38_locales.py"], "title": "I18N integration"},
    "ID-040": {"reuse": "REUSE", "module_paths": ["identity_service.py"], "test_paths": ["tests/test_auth_identity_profile.py"], "title": "Avatar sources"},
    "ID-041": {"reuse": "REUSE", "module_paths": ["identity_service.py"], "test_paths": ["tests/test_auth_identity_profile.py"], "title": "Avatar upload security"},
    "ID-042": {"reuse": "NOT_APPLICABLE_WITH_EVIDENCE", "module_paths": ["identity_service.py"], "test_paths": [], "title": "Avatar moderation", "notes": "AI moderation optional per spec"},
    "ID-043": {"reuse": "BUILD", "module_paths": ["identity/identity_audit.py", "database.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Audit trail"},
    "ID-044": {"reuse": "BUILD", "module_paths": ["identity/security_notifications.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Security notifications"},
    "ID-045": {"reuse": "REUSE", "module_paths": ["gdpr_service.py", "identity/retention_registry.py"], "test_paths": ["tests/test_technical_due_diligence.py"], "title": "Data privacy"},
    "ID-046": {"reuse": "REUSE", "module_paths": ["gdpr_service.py", "api/routers/privacy.py"], "test_paths": ["tests/test_technical_due_diligence.py"], "title": "GDPR export"},
    "ID-047": {"reuse": "BUILD", "module_paths": ["identity/account_deletion.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Account deletion"},
    "ID-048": {"reuse": "BUILD", "module_paths": ["identity/retention_registry.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Retention registry"},
    "ID-049": {"reuse": "REUSE", "module_paths": ["api/routers/privacy.py"], "test_paths": ["tests/test_technical_due_diligence.py"], "title": "CCPA/CPRA architecture"},
    "ID-050": {"reuse": "REUSE", "module_paths": ["templates/privacy.html"], "test_paths": [], "title": "Cookie consent architecture"},
    "ID-051": {"reuse": "REUSE", "module_paths": ["templates/login.html", "templates/profile.html"], "test_paths": ["tests/test_visible_chrome_critical_surfaces.py"], "title": "Accessibility WCAG"},
    "ID-052": {"reuse": "REUSE", "module_paths": ["templates/login.html"], "test_paths": ["tests/test_sonar_template_js_parse_hygiene.py"], "title": "Native HTML before ARIA"},
    "ID-053": {"reuse": "REUSE", "module_paths": ["templates/login.html"], "test_paths": ["tests/test_visible_chrome_critical_surfaces.py"], "title": "Accessible password UX"},
    "ID-054": {"reuse": "REUSE", "module_paths": ["templates/login.html", "security_models.py"], "test_paths": ["tests/test_auth_identity_profile.py"], "title": "UX validation"},
    "ID-055": {"reuse": "BUILD", "module_paths": ["identity/enterprise_readiness.py", "enterprise_sso.py"], "test_paths": ["tests/test_enterprise_sso_auth0.py"], "title": "Enterprise identity readiness"},
    "ID-056": {"reuse": "REUSE", "module_paths": ["org_mfa_policy.py"], "test_paths": ["tests/test_p0_authz_hardening.py"], "title": "Organization security policy"},
    "ID-057": {"reuse": "BUILD", "module_paths": ["identity/step_up.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Fail-closed"},
    "ID-058": {"reuse": "REUSE", "module_paths": ["auth_service.py", "billing/entitlement_state.py"], "test_paths": ["tests/test_billing_p0_test_matrix.py"], "title": "Authorization separation"},
    "ID-059": {"reuse": "REUSE", "module_paths": ["security_middleware.py", "security_auth.py"], "test_paths": ["tests/test_security_hardening.py"], "title": "Security headers"},
    "ID-060": {"reuse": "REUSE", "module_paths": ["identity/identity_audit.py", "email_outbox.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Logging privacy"},
    "ID-061": {"reuse": "IMPROVE", "module_paths": ["identity/login_abuse.py"], "test_paths": ["tests/test_d13_auth_abuse.py"], "title": "Recovery anti-abuse"},
    "ID-062": {"reuse": "NOT_APPLICABLE_WITH_EVIDENCE", "module_paths": ["identity_service.py"], "test_paths": [], "title": "Username recovery", "notes": "Login by email/Google/passkey per spec"},
    "ID-063": {"reuse": "BUILD", "module_paths": ["identity/step_up.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Sensitive action recent auth"},
    "ID-064": {"reuse": "BUILD", "module_paths": ["identity/webauthn_service.py", "identity/provider_registry.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Prevent lockout"},
    "ID-065": {"reuse": "BUILD", "module_paths": ["identity/provider_registry.py", "database.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Provider registry"},
    "ID-066": {"reuse": "BUILD", "module_paths": ["identity/webauthn_service.py", "mfa_service.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Authenticator registry"},
    "ID-067": {"reuse": "BUILD", "module_paths": ["database.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Login history"},
    "ID-068": {"reuse": "REUSE", "module_paths": ["admin_mfa.py", "identity/identity_audit.py"], "test_paths": ["tests/test_security_max_closure.py"], "title": "Admin identity operations"},
    "ID-069": {"reuse": "IMPROVE", "module_paths": ["identity/login_abuse.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Enumeration resistance"},
    "ID-070": {"reuse": "BUILD", "module_paths": ["tests/test_identity_p0_test_matrix.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "Testing evidence"},
    "ID-071": {"reuse": "BUILD", "module_paths": ["bd_platform/identity_source_driven_engineering.py"], "test_paths": ["tests/test_identity_p0_test_matrix.py"], "title": "P0 acceptance gate"},
    "ID-072": {"reuse": "LIVE_GATED", "module_paths": ["docs/BLACKDARK_INSTITUTIONAL_IDENTITY_AUTH_PROFILE_SPEC_v1.md"], "test_paths": [], "title": "Live gate"},
}


def main() -> None:
    out = {
        "schema_version": "1.0",
        "spec_file": "docs/BLACKDARK_INSTITUTIONAL_IDENTITY_AUTH_PROFILE_SPEC_v1.md",
        "bindings": BINDINGS,
    }
    path = ROOT / "docs" / "IDENTITY_IMPLEMENTATION_INDEX.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path} bindings={len(BINDINGS)}")


if __name__ == "__main__":
    main()
