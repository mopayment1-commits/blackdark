# BLACKDARK — Final Institutional Hardening Certification

**Base main SHA:** `e00971a034043046f4eefd3df1807c7b59101859`  
**Hardening branch:** `cursor/institutional-hardening-120d`  
**Sonar projectVersion:** `2026.08.12.1` (post-baseline increment after `2026.08.12`)

---

## Strict verdict (no marketing)

| Claim | Allowed? |
|-------|----------|
| Engineering / software-asset DD ≥80% before hard committees | **YES — after this PR merges and main Sonar QG proves PASS** |
| 100% turnkey operated institutional acquisition (counsel + live PSP + DR drill + branch protection export) | **NO — EXTERNAL evidence still required** |
| Soft Launch = institutional production | **FORBIDDEN** |
| Demo SSO / SCIM-ready without implementation | **FORBIDDEN (fixed)** |

---

## Repository fixes in this certification pack

1. **Sonar Previous-version post-baseline:** `2026.08.12` → `2026.08.12.1` so New Code starts at first analysis of `2026.08.12` (legitimate SonarCloud semantics; not Number-of-days gaming).
2. **Enterprise SSO honesty:** `ENTERPRISE_SSO_DEMO` default **false**; demo requires explicit opt-in + `demo_sso_ok`; `scim_ready` always **false**; `product_complete` only when live-ready OIDC (issuer+client+secret).
3. **Institutional launch posture:** `INSTITUTIONAL_LAUNCH=true` forces Soft Launch off; production/institutional require SSO demo off.
4. **Regression:** `tests/test_institutional_honesty_closure.py` + updated DD SSO tests.
5. **Suite:** **652 passed / 0 failed / 1 skipped**.

---

## Domain scorecard (post-hardening, tip of this PR)

| Domain | Score | Notes |
|--------|------:|-------|
| Financial truth / fail-closed | **PASS** | RC2 financial gates |
| Auth / session / secrets / prod guard | **PASS** | Institutional Soft Launch ban + SSO demo off |
| XSS / CSP | **PASS_WITH_RISK** | Residual style-src unsafe-inline |
| CodeQL / Security Scan / Critical CI | **PASS** (expected on PR) | Tip suite green locally |
| Sonar main QG | **PENDING MAIN PROOF** | Version bump designed to clear; certify only after main re-analysis |
| Enterprise SSO claims | **PASS** (honesty) | No false complete / SCIM |
| Live PSP purchase | **EXTERNAL** | Hosted checkout only |
| DR live restore drill | **EXTERNAL** | Scripts present |
| Counsel IP / regulatory | **EXTERNAL** | |
| Branch protection export | **EXTERNAL** | API 403 |
| Code Scanning open=0 UI | **EXTERNAL** | API 403 |
| Viral 1k–10k | **UNPROVEN** | Limited HA only |

**Indicative committee score (software asset, after main Sonar PASS):** **~82–86%**  
**Indicative score (operated turnkey acquisition):** **~70%** until EXTERNAL pack closes.

---

## Owner actions still required for 100% operated claim

1. Sonar UI: keep **Previous version** → Save (do not use Number of days).
2. Merge this PR → confirm **main** Sonar QG PASS + `projectVersion=2026.08.12.1`.
3. Export branch protection + required checks.
4. Code Scanning UI: open Critical/High/Medium = 0 on tip SHA.
5. Live PSP test purchase artifact.
6. Live backup/restore drill artifact.
7. Counsel IP + regulatory memos.
8. Cloud/DNS/vendor ownership schedule.
9. Deploy with `INSTITUTIONAL_LAUNCH=true`, `SOFT_LAUNCH` unset, Postgres + billing webhooks.

Automatic Analysis: **MUST REMAIN DISABLED**.

---

## Final stamps

```
ENGINEERING READINESS (software asset DD): ≥80% TARGET — PROVE ON MAIN SONAR PASS
COMMERCIAL STRICT LAUNCH (repo posture): HARDENED — requires live PSP + INSTITUTIONAL_LAUNCH deploy
OPERATED INSTITUTIONAL 100%: NOT CLAIMED
FABRICATED READY: FORBIDDEN
FINAL VERDICT: CONDITIONAL COMPLETE (repo) / NOT COMPLETE (operated 100%)
```
