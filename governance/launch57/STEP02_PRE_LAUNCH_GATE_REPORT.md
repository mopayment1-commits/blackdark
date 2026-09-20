# Launch-57 — Step ② Pre-Launch Gate Report (Internal)

**Generated:** 2026-09-19T09:51:29Z  
**Branch / commit:** `cursor/launch57-phase8-launch-coherence-358c` @ `cdf73650`  
**Scope:** LAUNCH57_IDS only — no spec rebuild, no LAUNCH57_IDS expansion  
**PASS_LIVE_CLAIMED:** `false` (no staging/production URL probed in this run)

---

## Executive summary

| Item | Status |
|------|--------|
| FILES 01–13 local closure | **13/13 CLOSED_LOCAL** (`SPECS_13_LOCAL_CLOSURE_LEDGER.json`) |
| Regression smoke (Section A) | **ALL GREEN** (6/6 suites, exit 0) |
| Engineering degrade honesty | **PASS** — `#33` Telegram `BLOCKED_EXTERNAL`, `#38` MVRV `licensed_mvrv_feed: false` when proxy missing |
| Staging/prod live probe | **NOT RUN** — no HTTPS URL evidenced |
| Paid checkout live | **NOT READY** — Stripe/Lemon env not configured; Egypt merchant constraint documented by owner |
| **Gate verdict** | **NO-GO** (see Section E) |

---

## A) Regression smoke

Executed on this VM with `python3 -m pytest`. All suites **exit 0**.

| # | Suite | Files | Tests | Exit |
|---|-------|-------|------:|-----:|
| 1 | Isolation + support plane + phase1/2/3 batches | `test_b1/b2/b3_isolation_closure`, `test_support_plane_phase1_isolation`, `test_data_batch1/2`, `test_trust_batch1/2` | 50 | **0** |
| 2 | Anonymous matrix (Spec 02) | `test_spec02_anonymous_visitor_public_intelligence` | 14 | **0** |
| 3 | Entitlement (Spec 03) | `test_spec03_billing_subscription_entitlement` | 16 | **0** |
| 4 | Financial secret hygiene (Spec 10) | `test_spec10_financial_data_secret_security` | 15 | **0** |
| 5 | Temporal (Spec 11 + batch 11) | `test_spec11_global_time_temporal_consistency`, `test_temporal_batch11` | 26 | **0** |
| 6 | Phase 8 E2E acceptance | `test_phase8_e2e_acceptance` | 6 | **0** |
| | **Total** | | **127** | **0** |

**Key anonymous matrix assertions (Spec 02 / Spec 10 / Spec 12):**

- `GET /api/launch57/guest-trust` → **200** (anonymous allowed)
- `GET /api/launch57/command-home` → **401** (anonymous denied)
- `GET /api/launch57/decision-history` → **401** (anonymous denied)
- `enforce_launch57_entitlement(launch_item_id=49, tier=pro, user_key=anonymous)` → denied (free cannot spoof pro)

**Phase 8 E2E:** 6/6 journeys PASS in `test_phase8_e2e_acceptance.py` (local TestClient; not a deployed URL).

---

## B) Live-blocker register

| Blocker ID | Domain | Blocks paid launch? | Blocks free invite launch? | Owner action | Deferred OK? |
|------------|--------|:-------------------:|:----------------------------:|--------------|:------------:|
| HOST-DEPLOY-01 | Hosting / HTTPS / domain | Yes | **Yes (P0)** | Deploy Launch-57 build to public HTTPS staging or prod; set `APP_BASE_URL`; probe `/health/live`, `/api/launch57/guest-trust`, `/api/launch57/command-home` (401 anon) | No |
| SECRETS-PROD-01 | Production env secrets | Yes | **Yes (P0)** | Inject secrets via host/Vault — never commit. Required min: `SECRETS_MASTER_KEY`, `SESSION_TOKEN_PEPPER`, `ADMIN_API_KEY` (per `.env.production.example`) | No |
| PAY-STRIPE-01 | Stripe / global card checkout | **Yes (P0)** | No (free tier) | Register Stripe (or Lemon Squeezy MoR) under **non–Egypt-constrained** merchant entity; set `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_*` | Yes for free-only invite |
| PAY-WEBHOOK-01 | Payment webhook reachability | **Yes (P0)** | No | Expose `APP_BASE_URL/webhook` (+ Lemon path) with valid TLS; verify HMAC signatures live | Yes for free-only |
| PAY-TAX-01 | Tax / MoR configuration | Yes | No | Production tax settings with PSP; documented as `NEEDS_EXTERNAL_VERIFICATION` in billing reconciliation | Yes |
| EMAIL-DELIVERY-01 | Email (verify / reset) | Partial (paid signup friction) | Partial | Configure SMTP or transactional provider; identity reconciliation lists `real_email_delivery` as external | **Yes** for anonymous-first free invite |
| DATA-PAID-API-01 | Paid market-data APIs | No (enhancement) | No | Optional keys: `COINGLASS_API_KEY`, `DEBANK_API_KEY`, `LUNARCRUSH_API_KEY`, `ARKHAM_API_KEY`, explorer keys — all have free/public fallbacks in code | **Yes** |
| DATA-TELEGRAM-01 | Telegram alert delivery | No (in-app alerts work) | No | `#33`: set `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` or accept `delivery_status: BLOCKED_EXTERNAL` | **Yes** |
| DATA-MVRV-01 | Licensed on-chain MVRV | No | No | `#38`: `licensed_mvrv_feed: false`; local CoinGecko proxy or `BLOCKED_EXTERNAL` — must not claim full licensed feed | **Yes** |
| NTP-CLOCK-01 | NTP / host clock | Partial (freshness SLO) | Partial | Spec 11: `PASS_LIVE` requires production NTP evidence; engineering monotonic/wall-clock separation passes locally | Yes short-term |
| MONITOR-MIN-01 | Monitoring / alerts minimum | Yes (ops) | Partial | `MONITORING_SETUP_REPORT.json`: set `MONITORING_BASE_URL`, optional `SENTRY_DSN`, external uptime on `/health/live`, `TELEGRAM_BOT_TOKEN` for ops | Yes for soft launch |
| LEGAL-PAGES-01 | Terms / privacy / risk | Yes (compliance) | Partial | Routes wired: `/terms`, `/privacy`, `/disclaimer`, `/refund` (`legal_content.py`, `dashboard.py`) — **content present in repo**; counsel review + live URL check still owner | Partial — deploy then verify |
| OAUTH-PROD-01 | Google/GitHub OIDC | Partial | No | `OAUTH_*` env for sign-in; anonymous surfaces work without | **Yes** |
| B2B-KEY-01 | B2B feed API key | Yes (Hero 6) | No | `BLACKDARK_B2B_API_KEY` for `/api/b2b/feed` — not in Launch-57 handler path | Yes |

Machine-readable subset: `governance/launch57/STEP02_LIVE_BLOCKERS.json`.

---

## C) Free vs paid data degrade map

From Launch-57 code paths and `.env.example` (providers not invented).

| Launch ID / feature | External dependency | Works on free/public tier? | User-visible behavior if key missing |
|---------------------|--------------------|:--------------------------:|--------------------------------------|
| **#21–24, #42** spot/OHLCV/prices | Binance public REST (+ Kraken/OKX/Bybit/Coinbase fallback) | **Yes** | Connector failover; degraded/stale → abstain paths in `data_batch1` / failure recovery |
| **#25–29** derivatives | Binance futures public + Deribit public; optional CoinGlass | **Yes** (core) | `coinglass.available: false`; Binance snapshot still returned (`derivatives_hub.py`) |
| **#27** liquidation radar | Binance free metrics; optional CoinGlass | **Yes** | Fewer alerts; `coinglass_supplement: false` |
| **#30–31** order book / screener | Internal + Binance-derived | **Yes** | Reduced depth disclaimers (`derivatives_common.py`) |
| **#33** smart alerts | Telegram API (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) | In-app eval **yes**; push **no** without creds | `delivery_status: BLOCKED_EXTERNAL`, `blocked_channels: ["telegram_push"]` — **not presented as LIVE push** |
| **#38** MVRV / Z-score | CoinGecko public (`compute_mvrv_realignment`); LookIntoBitcoin reference URLs | Partial proxy | `licensed_mvrv_feed: false`, `blocker: BLOCKED_EXTERNAL` when no z-score; `presented_as_live: false` |
| **#43** arbitrage scanner | Public CEX feeds via `arbitrage_service` / `market_context` | **Yes** | Scan works; Telegram instant alerts optional (`TELEGRAM_*`) |
| **#13–20, #53–54** smart money / wallet DD | Tracely + eth-labels + socialtickers (free); optional DeBank/Zerion/Bubblemaps/Scopescan/Arkham | **Yes** (baseline) | Wallet: Tracely fallback chain; `arkham_entity: null` without `ARKHAM_API_KEY`; insufficient DD → qualified verdict, not zero-risk (`trust_adaptive_common`) |
| **#2** single-sentence oracle | Governed payload / rules (`trust_batch1`) — no LLM in Launch-57 handler | **Yes** | WAIT/ABSTAIN on stale/missing spine (`oracle_stale_abstain`) |
| **#34–36, #51** explanations | Rule/statistical (`explanation_ai_common`: `llm_used: false`) | **Yes** | Platform-data-only footer; AI failure preserves evidence (`#36`) |
| **#49–50** private history / discipline | Auth + entitlement (not a data API) | Free tier limited | Anonymous → 401 / entitlement denied; unverified `tier=pro` cannot spoof paid |
| **#4–6, #44–48** trust / share | Internal evidence class | **Yes** | `assess_user_evidence_class` — SIM/DELAYED labeled, not masked as LIVE |

**SIM / missing-as-LIVE check:** Phase 8 pre-live checklist documents `#33` and `#38` as `PASS_ENGINEERING_WITH_BLOCKED_EXTERNAL`. Code sets `presented_as_live: false` when proxy/license missing (`edge_ui_batch1.py`). Net-edge rejects demo opportunities (`trust_batch1`). **No path found in Launch-57 handlers that marks missing external data as full LIVE success.**

---

## D) Payments path decision (document only)

**Recommended path for owner:** **(1) Free-only global invite until Stripe entity ready**, with **(3) Stripe after non–Egypt-constrained merchant entity** as the documented paid follow-on.

Rationale from repo:

- `billing/ops_readiness.py`: `launch_ready` requires Stripe **or** Lemon webhook + SKU env — none set in dev VM.
- `BLACKDARK_LAUNCH57_BILLING_ENTITLEMENT_RECONCILIATION.json`: `production_stripe_eligibility` = `BLOCKED_EXTERNAL`.
- `payments_usd.py`: self-serve via **Lemon Squeezy or Stripe** hosted checkout (USD); institutional = wire (`INSTITUTIONAL_WIRE`), not self-serve card.
- Owner context: Egypt-constrained payout bank blocks Stripe live for global customers until entity moves to supported country.

**Not recommended now:** **(2) Manual bank transfer entitlement** — high ops/fraud risk; only `INSTITUTIONAL_WIRE` is codified for sales-led tier, not retail PRO/ELITE spoofing.

**(4) Non-Stripe global MoR:** Lemon Squeezy is already referenced as launch-default MoR in `payments_usd.py` (`provider_preference`). Paddle/other PSPs — **evaluate outside repo** (not implemented).

---

## E) GO / NO-GO

```
VERDICT: NO-GO
PASS_LIVE_CLAIMED: false
NEXT_STEP_FOR_OWNER: Deploy to HTTPS staging, run live probes (/health/live, guest-trust 200, command-home 401 anon), then re-run Step ② live slice; keep free-only until non-EG Stripe/Lemon merchant is live.
```

### Why not GO_LIMITED_FREE_INVITE (yet)

Regression smoke is **fully green** and FILES 01–13 remain **CLOSED_LOCAL**, but Step ② explicitly requires staging/prod URL evidence for a free-invite GO. **This run performed no HTTPS deployment probe.** `PASS_LIVE` remains false on all 13 specs.

### P0 blockers (must clear before invite)

1. **HOST-DEPLOY-01** — No public HTTPS staging/prod URL probed in this run  
2. **SECRETS-PROD-01** — Production secret injection on target host (not git)

### Deferred OK for free-only soft launch (after P0 cleared)

- PAY-STRIPE-01, PAY-WEBHOOK-01, PAY-TAX-01 (paid path)  
- DATA-PAID-API-01, DATA-TELEGRAM-01, DATA-MVRV-01  
- EMAIL-DELIVERY-01 (if anonymous-first invite)  
- NTP-CLOCK-01, MONITOR-MIN-01 (harden before scale)

### Why not GO_LIMITED_WITH_PAYMENTS

No live Stripe/Lemon checkout, webhook, or merchant eligibility evidenced. Owner Egypt merchant constraint applies.

---

## Appendix — Specs ledger snapshot

| FILES | Status | PASS_LIVE |
|-------|--------|-----------|
| 01–13 | CLOSED_LOCAL | false (all) |
| Ledger | `all_files_closed_local: true` | `PASS_LIVE_CLAIMED: false` |

## Appendix — Smoke command log

```bash
# A — isolation + phase1/2/3 (exit 0, 50 tests)
python3 -m pytest tests/launch57/test_b1_isolation_closure.py \
  tests/launch57/test_b2_isolation_closure.py \
  tests/launch57/test_b3_isolation_closure.py \
  tests/launch57/test_support_plane_phase1_isolation.py \
  tests/launch57/test_data_batch1.py tests/launch57/test_data_batch2.py \
  tests/launch57/test_trust_batch1.py tests/launch57/test_trust_batch2.py -q

# B — spec02 (exit 0, 14 tests)
python3 -m pytest tests/launch57/test_spec02_anonymous_visitor_public_intelligence.py -q

# C — spec03 (exit 0, 16 tests)
python3 -m pytest tests/launch57/test_spec03_billing_subscription_entitlement.py -q

# D — spec10 (exit 0, 15 tests)
python3 -m pytest tests/launch57/test_spec10_financial_data_secret_security.py -q

# E — spec11 + temporal batch11 (exit 0, 26 tests)
python3 -m pytest tests/launch57/test_spec11_global_time_temporal_consistency.py \
  tests/launch57/test_temporal_batch11.py -q

# F — phase8 e2e (exit 0, 6 tests)
python3 -m pytest tests/launch57/test_phase8_e2e_acceptance.py -q
```

---

*End of Step ② report. No deployment automation started.*
