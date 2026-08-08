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

### Strict Disclaimer Architecture (`legal_shield.py`) — 4 layers

| Layer | Control | Location |
|-------|---------|----------|
| 1 | Mandatory disclaimer **prefix** on every Oracle narrative | `legal_shield.apply_legal_shield` via `sanitize_oracle_payload` |
| 2 | `SYSTEM_CLASSIFICATION=analytical_tool`, `IS_FINANCIAL_ADVISOR=False`, `REGULATORY_STATUS=not_regulated` | `config.py` + `/api/status` + `/system/info` + UI banner |
| 3 | Explicit consent modal + DB/cookie gate | `terms_consent.py` + `static/js/legal-shield.js` |
| 4 | Permanent footer on all pages | `static/js/legal-shield.js` + templates |

| Other controls | Location |
|----------------|----------|
| Public risk pages | `/terms`, `/privacy`, `/disclaimer` |
| GDPR deletion / issue forms | `/request-deletion` |
| GDPR DSR export/erase | `/api/privacy/dsr/*` |
| Admin MFA / OAuth / pgcrypto / prod guard | prior acquisition readiness work |

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
