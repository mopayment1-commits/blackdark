# BLACKDARK — SEC / MiCA Compliance Pack (Engineering Posture)

> **Status:** Product & engineering control pack — **not a legal opinion**  
> **Counsel required:** External SEC (US) and MiCA (EU) counsel must review before any LOI marketing claim of “compliant.”  
> **Last updated:** 2026-03-28

---

## 1) Product classification (internal posture)

| Claim | Posture |
|-------|---------|
| Investment adviser / broker-dealer | **Not claimed.** Product is decision intelligence / analytics. |
| Trade execution custody | Optional user-held exchange API keys only; withdraw-blocked by default. |
| AI output | Informational; Anti-Hype / regulatory disclaimer on primary surfaces. |
| Public accuracy | `/oracle-accuracy` publishes hits and misses. |

---

## 2) Control map (implemented in code)

| Control | Location |
|---------|----------|
| Regulatory disclaimer engine | `regulatory_compliance_guard.py` |
| Public risk pages | `/disclaimer`, `/terms`, `/privacy` (`legal_content.py`) |
| GDPR DSR export/erase | `/api/privacy/dsr/*` (`gdpr_service.py`) |
| Password hashing | PBKDF2-SHA256 (`auth_service.py`) |
| Admin MFA (TOTP) | `admin_mfa.py` + `X-Admin-TOTP` |
| OAuth2 social login | `oauth_service.py` (Google/GitHub) |
| Secrets at rest (app) | Fernet vault (`secrets_vault.py`) |
| Secrets at rest (DB) | `pgcrypto` via `postgres_backend.ensure_pgcrypto` |
| Production fail-closed | `production_guard.py` (Postgres + Redis + admin MFA) |
| Auth failure audit | `data/auth_audit.jsonl` |

---

## 3) MiCA / SEC checklist (owner = Legal + Founder)

- [ ] Confirm entity jurisdiction and whether any token / CASP authorization is required.
- [ ] Confirm marketing copy never implies guaranteed returns or “AI-managed funds.”
- [ ] Confirm US distribution does not trigger investment-adviser registration for the chosen packaging.
- [ ] Publish privacy contacts + DPO path if targeting EU residents at scale.
- [ ] Retain counsel sign-off letter in data room before acquisition diligence.

---

## 4) Buyer-facing statement (allowed)

> “BLACKDARK ships engineering controls aligned with an analytics / decision-intelligence posture (disclaimers, accuracy ledger, GDPR DSR APIs, production security gates). Formal SEC/MiCA authorization status depends on entity packaging and is subject to external counsel review.”

**Disallowed:** “SEC-compliant” / “MiCA-licensed” without counsel letter.
