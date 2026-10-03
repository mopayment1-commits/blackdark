# Security Workflow Closure Status

**Generated:** 2026-09-12

## Critical workflows — live verification

| ID | Title | Status | Live test |
|----|-------|--------|-----------|
| WF-001 | Admin API key brute-force protection | **REMEDIATED** | `tests/test_d13_auth_abuse.py::test_admin_key_rejects_empty` |
| WF-002 | Session token hashing | **REMEDIATED** | `tests/test_d13_auth_abuse.py::test_session_token_not_reversible` |
| WF-003 | Production secrets vault fail-closed | **REMEDIATED** | `secrets_vault.get_vault_key` production guard |
| WF-004 | Stripe/credential cleartext logging | **REMEDIATED** | `tests/test_codeql_cleartext_logging_closure.py` |
| WF-005 | Cross-tenant org data leakage | **REMEDIATED** | `test_wf005_cross_tenant_org_access` |
| WF-015 | Identity impersonation (owner/actor email) | **REMEDIATED** | `test_wf015_identity_impersonation` |
| WF-016 | Unauthenticated org member enumeration | **REMEDIATED** | `test_wf016_org_members_requires_membership` |
| WF-017 | Unauthorized org member injection | **REMEDIATED** | `test_wf017_org_add_member_requires_admin` |
| WF-018 | Hardcoded secrets in source | **REMEDIATED** | `scripts/secrets_hygiene_scan.py` → 0 findings |
| WF-019 | Production SQLite default | OPEN_PRE_DEPLOY | Requires `postgresql://` in prod |
| WF-020 | Signed billing webhook verification | OPEN_PRE_DEPLOY | Requires webhook secrets in prod |

## WF-015 fix (identity impersonation)

`api/routers/institutional.py` derives `owner` and `actor` from the authenticated principal (`user["email"]`), never from request body alone. Spoofed `owner_email` / `actor_email` in the body are ignored.

## Secrets management (WF-018)

- All API keys and credentials read from `os.getenv()` / `secrets_vault`
- `.env` excluded from git (`.gitignore` lines 1–7)
- Template: `.env.example` — no real secrets committed
- Scan: `python3 scripts/secrets_hygiene_scan.py` → `SECRETS_HYGIENE_REPORT.json`

## Pre-deploy blockers (not code defects)

WF-019 and WF-020 require production environment configuration before live deploy. Code paths exist; secrets must be set in staging/prod `.env`.
