# BLACKDARK Institutional Acquisition DD Assessment

**Canonical tip:** `e00971a034043046f4eefd3df1807c7b59101859` (origin/main, post-merge PR #69)  
**Audit date:** 2026-08-12  
**Mode:** Evidence-only (repo, `docs/dd/*`, CI, tests, code). No marketing language.

---

## Executive verdict

**NOT READY** for unconditional institutional acquisition or commercial launch claim.

**Committee posture:** **PROCEED WITH CONDITIONS** as a *software asset with strong fail-closed financial/security engineering* — **not** as a turnkey operated business. Tip CI proves Critical Gate + Security Scan + CodeQL Analyze green; **SonarCloud main Quality Gate is FAILED** on this exact SHA. Material EXTERNAL packs (PSP, counsel, Code Scanning UI, branch protection, DR drill, account ownership) remain empty or unverifiable.

Do **not** treat RC2’s “93/100” self-score as buyer-grade PASS. This audit re-scores from tip evidence.

---

## Domain scorecard

| # | Domain | Score | Evidence (1–2 sentences) |
|---|--------|-------|--------------------------|
| 1 | Financial truth / fail-closed economics | **PASS** | `fee_matrix.py` returns `None` for unknown venues/fees/withdrawals (never invents defaults); `net_edge_truth.py` hard-rejects missing net/slippage/fees/withdrawal; `arbitrage_engine` / `execution_engine` fail closed on unknown fees; critical CI runs `tests/test_rc2_financial_truth.py` + fee suite with `--cov-fail-under=85`. |
| 2 | Auth / session / secrets / production guards | **CONDITIONAL** | Fernet-sealed session cookies, CSRF reject path, production ENV OR fail-closed, vault key required in prod tests (`test_p1_session_hardening`), `require_admin` + `X-Admin-TOTP`, `production_guard` refuses strict prod without secrets/pepper/MFA/demo-key-off. Residual: Soft Launch still bypasses Postgres/billing gates; prod CSP/secrets attestation forms unfilled; founder-held secrets. |
| 3 | XSS / CSP / DOM safety | **CONDITIONAL** | Default `CSP_NONCE_MODE=true` with nonce + `strict-dynamic` (no default `script-src 'unsafe-inline'`); regression suites `test_xss_sink_hardening.py` / CodeQL XSS closure tests on tip. Residual: `style-src 'unsafe-inline'` accepted; break-glass `CSP_NONCE_MODE=false` reopens unsafe-inline; `docs/ops/CSP_PRODUCTION_ATTESTATION.md` unsigned for live URL. |
| 4 | CodeQL / Bandit / security scan posture | **CONDITIONAL** | Tip run CodeQL Analyze **SUCCESS** (python/js/actions); Security Scan **SUCCESS** (pip-audit + pytest-security); local Bandit `@ .bandit` = **HIGH=0 MEDIUM=0 LOW=111**. Code Scanning open-alert API **403** (counts EXTERNAL); Bandit LOW≠0 and PR #50 (claim LOW=0) still open/CONFLICTING — posture is strong-but-incomplete, not “cleared.” |
| 5 | SonarCloud main QG / coverage / AA | **FAIL** | Tip SonarCloud Analysis run `31604386000` @ `e00971a`: **QUALITY GATE STATUS: FAILED** (dashboard main). Workflow correctly keeps Automatic Analysis **DISABLED** and imports curated `coverage.xml` (`--cov-fail-under=0`); `#69` only established `sonar.projectVersion=2026.08.12` baseline — **main QG still red**. |
| 6 | Payments / PSP live readiness | **EXTERNAL** | Hosted Lemon/Stripe checkout code + webhook auth + SKUs ($29/$49) exist (`billing_service.py`, `docs/PAYMENTS_USD_SECURITY.md`); `docs/DEFERRED_HUMAN_STEPS.md` H1 still requires live PSP + **one test purchase**. Soft Launch can boot without billing — no live purchase evidence on tip. |
| 7 | DR / backup / restore | **EXTERNAL** | Scripts + runbook present (`scripts/backup_postgres.py`, `restore_postgres.py`, `docs/ops/BACKUP_RESTORE.md`); drill API records exist in code. Doc itself: **“Live restore drill evidence in buyer cloud remains EXTERNAL.”** No attached restore artifact for tip. |
| 8 | Branch protection / supply chain | **CONDITIONAL** | Hash-locked installs (`requirements.hashes.txt` + `--require-hashes`), Actions SHA-pinned in `ci.yml` / `security.yml` / `sonarcloud.yml`, SBOM + license inventory gated in Critical CI. Branch protection API **403** — required checks / admin enforcement **unverifiable** from this token. |
| 9 | Legal / counsel / IP / regulatory | **EXTERNAL** | Engineering IP pack exists (`docs/IP_CLEANLINESS.md`, NOTICE, license inventory CI artifact) claiming no GPL/AGPL in direct stack. **No counsel letter** for IP assignment / dependency opinion / advice-marketing boundaries (`F-EXT-05`, `F-EXT-06`); docs alone ≠ legal clearance. |
| 10 | Scale / viral capacity | **CONDITIONAL** | Signed HA row exists for soft multi-worker (`docs/LOAD_TEST_RUN_LOG.md` @ `9bae7c4`, `WEB_CONCURRENCY=2`, Soft Launch off) with controlled 429 — honest that **1k–10k / multi-replica is UNPROVEN**. PR #65 viral surge certification tip `770f150` is **not** ancestor of main (`e00971a`). |
| 11 | SSO / RBAC / enterprise claims vs code | **FAIL** | `enterprise_sso.py` advertises `product_complete: True`, `scim_ready: True`, SAML via stub `BD_SAML_AUTHN_*`, and treats empty/`demo_sso_ok` code as demo with `ENTERPRISE_SSO_DEMO` defaulting **true**. Org RBAC roles exist (`org_tenant.ROLES`) but IdP path is demo-grade — enterprise claim language on main is not buyer-defensible. |
| 12 | Test suite honesty | **CONDITIONAL** | Critical Gate is explicitly **not** the full tree and is green on tip; fee coverage gate ≥85% is real. Sonar `coverage.xml` is a **curated** broad-green list with `--cov-fail-under=0` (import theater risk if misread as full coverage). CI footer still warns of ~20 non-gate failures (may be stale vs RC2 “628 passed” claim — either way, tip does not prove full-suite green on main CI). Skips are minimal (`skipif` Postgres / optional pool). |
| 13 | Open stale security PRs (#40,#41,#50,#51,#54,#65) | **FAIL** | Six named PRs still open: #40/#41/#65 **DRAFT+CONFLICTING**; #50 Bandit LOW=0 **CONFLICTING** (100 files); #51 Ruff MERGEABLE; #54 softlaunch taint MERGEABLE but largely superseded on main (in-process bootstrap already present; founder email default remains). Unmerged/conflicting security closure work is a governance red flag, not closed risk. |
| 14 | Commercial launch readiness | **FAIL** | RC2 cert on merged lineage still says **LAUNCH: NOT READY**; Soft Launch is the operational escape hatch; PSP test purchase EXTERNAL; ownership schedule blank; Sonar main QG FAIL. Pricing tables exist on paper ($29/$49 + institutional inquiry) — that is SKU design, not launch proof. |

---

## TOP 10 HARD BLOCKERS (acquisition committee)

These block an unconditional close / READY claim. They are not nitpicks.

1. **SonarCloud main Quality Gate FAILED** on certified tip `e00971a` (run `31604386000`) — institutional static-analysis gate red after deliberate baseline PR #69.
2. **No counsel IP / license opinion** — KG-08 remains EXTERNAL; engineering `IP_CLEANLINESS.md` is not a legal opinion or assignment package.
3. **No live PSP configuration + test purchase evidence** (or signed Soft-Launch-only non-sale disclosure) — monetization path unproven (`F-EXT-01` / H1).
4. **Code Scanning open Critical/High/Medium counts unverifiable** (API 403) — Analyze job green ≠ open-alert inventory cleared (`F-EXT-02`).
5. **Account / secrets control plane empty** — `docs/ops/ACCOUNT_OWNERSHIP_SCHEDULE.md` has blank rows for GitHub, Sonar, cloud, DNS, PSP, CDN (`F-EXT-07`). Buyer cannot operate or transfer.
6. **Enterprise SSO honesty failure on main** — `product_complete` / `scim_ready` True with demo-default callback and stub SAML; institutional enterprise claim is false-complete.
7. **Branch protection unverifiable** — cannot confirm required checks / review rules actually enforce Critical+Security+CodeQL+Sonar (`F-EXT-04`).
8. **No live Postgres backup/restore drill artifact** — scripts/docs only; RPO/RTO declared, not proven (`F-EXT-03`).
9. **Open conflicting security closure PRs** (#50 Bandit LOW, #41 catastrophe P0, #65 integrity/viral, #40 quality honesty) — unfinished or superseded security work still hanging; diligence signal of incomplete closure discipline.
10. **Commercial / strict-production launch path not closed** — Soft Launch bypasses billing/Postgres; RC2/own certs say NOT READY; no production CSP attestation signed for target URL.

---

## TOP 10 CONDITIONAL / EXTERNAL items

1. **Pentest / WAF / CDN evidence** absent or deferred (`F-EXT-09`, `CDN_WAF_CHECKLIST.md`).
2. **Regulatory counsel memo** on advice/marketing / financial-adjacent positioning (`F-EXT-06`).
3. **CSP production attestation** form fill for live URL (`F-SEC-01`).
4. **Bandit LOW backlog (~111)** — H/M clean; LOW triage incomplete; PR #50 not mergeable onto tip.
5. **style-src 'unsafe-inline'** residual (accepted risk if HTML injection absent).
6. **Capacity beyond signed 2-worker HA** — 1k–10k / multi-replica / global UNPROVEN; PR #65 surge pack not on main.
7. **Founder 60s walkthrough / Glass Box operator ritual** deferred human steps.
8. **Dual oracle paths** (`oracle_unified` vs `ai_oracle`) — documented debt, post-close integration friction.
9. **Dashboard monolith / observability depth** — post-close maintainability (RC2 `F-CQ-01`, `F-OPS-02`).
10. **Sonar New Code admin confirmation** that Previous-version baseline is actually active in SonarCloud UI (repo set `projectVersion`; QG still failing — admin/settings EXTERNAL).

---

## What is actually strong and defensible

- **Fail-closed fee / withdrawal / net-edge economics** with independent RC2 tests in the merge-critical path — this is real product integrity, not slideware.
- **Security engineering baseline:** CSP nonce default, Fernet session sealing, admin MFA hook, production guard fail-closed OR across ENV tokens, hash-locked deps, SHA-pinned Actions, SBOM+license inventory CI gates.
- **Honest certification culture in current DD docs:** RC2 and two-track certs say **NOT READY / NOT COMPLETE / PROCEED WITH CONDITIONS** rather than fabricating READY (older marketing docs exist elsewhere — discount them).
- **Critical CI + Security Scan + CodeQL Analyze green on tip** — reproducible engineering signal.
- **Hosted-checkout PCI boundary** (no PAN storage) is correctly designed for SAQ A *if* live PSP is configured.
- **Postgres migration integrity tests** and Soft Launch vs strict Postgres honesty in `production_guard`.
- **Measured (limited) HA rehearsal** documented with explicit non-claims on viral 1k–10k.

---

## Tip CI snapshot (`e00971a`)

| Check | Result | Run |
|------|--------|-----|
| CI Critical Gate Suite | SUCCESS | `31604385904` |
| Security Scan | SUCCESS | `31604385899` |
| CodeQL (Analyze python/js/actions) | SUCCESS | `31604385834` |
| SonarCloud Analysis | **FAILURE (QG)** | `31604386000` |

---

## Stale PR register (as of audit)

| PR | Title | State | Mergeability | DD read |
|----|-------|-------|--------------|---------|
| #40 | Quality Honesty Soft Launch | DRAFT | CONFLICTING | Unfinished honesty packaging vs main |
| #41 | Security catastrophe P0 | DRAFT | CONFLICTING | Claims operator gates / MFA wiring; conflicts with tip — verify delta before discard |
| #50 | Bandit full closure LOW=0 | OPEN | CONFLICTING | Large divergent security rewrite; tip still LOW≈111 |
| #51 | Ruff report closure | OPEN | MERGEABLE | Style hygiene; not a kill gate |
| #54 | Sonar High softlaunch shell taint | OPEN | MERGEABLE | Core taint fix largely on main already; residual founder email default |
| #65 | Final integrity + viral capacity | DRAFT | CONFLICTING | Contains SSO honesty + surge evidence **not** on main |

---

## Final acquisition language (allowed)

| Claim | Allowed? |
|-------|----------|
| READY / CERTIFIED COMPLETE / acquisition-ready turnkey | **NO** |
| PROCEED WITH CONDITIONS (software asset) | **YES** — with blockers above as conditions precedent |
| Financial fail-closed core is institutional-grade engineering | **YES** — with test evidence |
| Live operated SaaS / enterprise SSO / viral 10k / Sonar main QG | **NO** on tip evidence |

---

*Audit bound to tip `e00971a`. Inaccessible systems (Code Scanning UI counts, branch protection, Sonar admin UI, live PSP, counsel) marked EXTERNAL — never PASS.*
