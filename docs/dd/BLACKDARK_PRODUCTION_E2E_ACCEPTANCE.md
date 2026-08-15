# BLACKDARK Production E2E Acceptance Matrix

**Rule:** `PASS` = exercised on published Production and succeeded. `FAIL` = anything else.

**Origin proved:** `https://blackdark-production.up.railway.app`  
**Not used:** `https://blackdark.up.railway.app` (HTTP 404)

**When:** 2026-08-15T00:37Z–00:43Z  
**Production build:** `git_commit=5927056e45656985929ae7f3d5c58f665ca1767e` · `release=2026-07-27-launch-phase-v8` · `branch=main`  
**This matrix judges the published Railway site, not the unreleased recert branch.**

## Verdict

| Track | Result |
|---|---|
| PUBLIC-DEMO-READY | **false** |
| LIVE-PRODUCTION-READY | **false** |
| LIVE-MONEY-READY | **false** |
| Unconditional GO | **NO-GO** |

| Metric | Result |
|---|---|
| Capabilities scored | **94** |
| **PASS** | **0** |
| **FAIL** | **94** |
| HTTP surfaces probed | 170 |
| 2xx / 4xx / 5xx | 43 / 113 / 14 |
| HTML catalog 404 | 46 pages |
| Console/Network silent-fail | Oracle stub 50005 vs live 63015; market assets=[] |

Agent-env proofs (Telegram on-call, Stripe TEST, Google IdP) are **not** Production PASS.

## Infra (production HTTP)

| Check | Observed | Verdict |
|---|---|---|
| Process live/ready | `/health` `/health/live` `/health/ready` HTTP 200 | not a feature PASS |
| PostgreSQL | `database_engine=postgresql`, pool `active=true` | **FAIL** — `/api/database/health` 500; duplicate register 500 |
| Redis | `redis_configured=false`, `redis_connected=false` | **FAIL** |
| Web workers | `service_mode=web`, `tasks=[]`, `flags={}`, `scale_ready=false` | **FAIL** |
| Market pipeline | `ticks_total=0`, stream+hub `running=false` | **FAIL** |
| Billing | `billing_configured=false`, `provider=none` | **FAIL** |
| Telegram | `configured=false`, `bot_token_set=false` | **FAIL** |
| OAuth | routes 404 on this SHA | **FAIL** |
| Sentry | `sentry_configured=false`; `errors_total` rising | **FAIL** |

## Journeys actually run

1. **Register** — `POST /api/auth/register` HTTP 200, `user.id` assigned, token in JSON, **no `Set-Cookie`**.
2. **Login** — same credentials → HTTP **401** `Invalid email or password`.
3. **Session** — Bearer / `bd_token` cookie / `X-Session-Token` → `/api/auth/me` `authenticated=false`.
4. **Duplicate register** — HTTP **500** Internal Server Error (not a clean 409).
5. **Logout** — HTTP 200 `success=true` with no session (not fail-closed).
6. **OAuth** — `/api/auth/oauth/google/start` **404**.
7. **Checkout** — `/create-checkout-session?tier=pro` **503** `Billing not configured`.
8. **Telegram test (unauth)** — HTTP **200** `success=false` (must be **401**).
9. **B2B WebSocket** — `wss://…/ws/b2b/feed?api_key=` opened; `connected` + `snapshot(record_count=0)` + `heartbeat` + `ping/pong`; **no** `arbitrage_opportunity` / `oracle_signal` in 20s.
10. **Oracle quick** — `price=50005.0`, `change_24h=0` (stub). Diagnostic `/api/diagnostics/price/BTC` resolved **63015.28** (live). Product surface shows the stub.
11. **Market overview** — claims `Binance Live API` / `tracked_count=25` / `assets=[]`.
12. **Options overview** — Deribit JSON 200 (BTC 818 / ETH 694 instruments). Paper OMS not run → capability still FAIL.
13. **On-chain overview** — numeric flows returned; sentiment/macro stub/null → `MKT-SENT` FAIL.
14. **Dashboard HTML** — title `Intelligence Dashboard`; JS calls `/api/auth/me`, `/api/market/overview`, `/api/arbitrage/*`, `/api/billing/checkout`, `/api/alerts/telegram/*`. Those APIs are 401/403/empty/unconfigured — the page is a shell, not a working product.
15. **Landing CTAs** — `/create-checkout-session?tier=pro|whale` are live links and return 503. Telegram links are `t.me/share` only (no production bot). Login HTML has **no** OAuth start control (only Google Fonts).
16. **`/register`** — HTTP 404 (current repo aliases this to `/login`; production SHA does not).

## Feature-by-Feature Production Acceptance Matrix

PASS = 0. Every row below is **FAIL**.

| ID | Feature | Production evidence | Verdict |
|---|---|---|---|
| ID-REG | Register / login / logout / session | Register 200, login 401, no cookie, bearer dead, dup 500 | FAIL |
| ID-MFA | TOTP MFA | `/profile` 404; no authenticated MFA journey | FAIL |
| ID-OAUTH | OAuth start/callback | OAuth routes 404 | FAIL |
| ID-EMAIL | Email verify / reset | `/verify-email` `/reset-password` `/api/auth/forgot-password` 404 | FAIL |
| ID-TIER | Tier gates | Only anonymous free `/api/auth/me`; cannot prove pro/whale | FAIL |
| ID-PROMO | Promo redeem | `/api/promo/redeem` 405; no session | FAIL |
| BIL-STATUS | Billing status + pricing | Status honest unconfigured; `/api/pricing` 404 | FAIL |
| BIL-CHECKOUT | Self-serve checkout | 503 Billing not configured | FAIL |
| BIL-INST | Institutional inquiry | Not proved | FAIL |
| OR-SENTENCE | Oracle sentence | `/oracle/BTCUSDT` 500; `/quick` stub 50005 vs live 63015 | FAIL |
| OR-CERT | Decision certificate | `/api/locked-predictions` 404 | FAIL |
| OR-TRUTH | Net-edge / half-life | Not proved | FAIL |
| OR-LEDGER | Accuracy ledger | Page 200; public accuracy API 500; chain empty | FAIL |
| OR-IDK | I DON'T KNOW token | Primary oracle 500 | FAIL |
| OR-MIND | Changed-mind | Page+API 404 | FAIL |
| OR-PERSONA | Persona clarity | APIs 404 | FAIL |
| OR-E2E | Decision e2e | Not proved | FAIL |
| OR-GRAPH | Decision graph | Not proved | FAIL |
| OR-PROV | Provenance score | 404 | FAIL |
| MKT-INGEST | Catalog-100 health | `/api/universe/status` 500; ticks=0 | FAIL |
| MKT-L2 | Venue L2 | `/api/product/l2-remainder` 404 | FAIL |
| MKT-MESH | CORE L2 mesh | Not proved on this SHA | FAIL |
| MKT-RADAR | Market radar | Overview empty arrays; sectors 500 | FAIL |
| MKT-SENT | Sentiment / onchain / macro | Sentiment all 50/Neutral; macro all null | FAIL |
| MKT-OPT | Options + paper OMS | Deribit chain 200; paper OMS not run | FAIL |
| MKT-TA | TA snapshot | Not proved | FAIL |
| MKT-FEED | Feed guards / engine | Engine idle, ticks=0 | FAIL |
| ARB-SCAN | Arb scans | opportunities 403; scan 405 | FAIL |
| ARB-CAT | Arb catalog | Taxonomy 200 only; scan not proved | FAIL |
| ARB-CEXDEX | CEX↔DEX | Not proved | FAIL |
| EX-SIM | Simulator | history 403 | FAIL |
| EX-OMS | OMS lifecycle | Not proved | FAIL |
| EX-KEYS | Key vault | Not proved | FAIL |
| EX-LIVE | Live venue FILL | Unauth 401; no live fill | FAIL |
| EX-JUP | Jupiter | Not proved on this SHA | FAIL |
| EX-PANIC | Panic freeze | Not proved | FAIL |
| EX-AUTO | Auto execution | `/api/execution/status` 401 | FAIL |
| RSK-ARCH | Risk architecture | `/api/risk/status` 401 | FAIL |
| RSK-WHALE | Whale band | Not proved | FAIL |
| AL-INBOX | In-app inbox | `/api/alerts/inbox` 404 | FAIL |
| AL-SUB | Alert subscribe | Not proved | FAIL |
| AL-TG | Live Telegram | Unconfigured; unauth test 200 not 401 | FAIL |
| AL-PASS | Alert passport | `/alert-passport` 404 | FAIL |
| AL-GEN | Generosity | Not proved | FAIL |
| JR-CRUD | Journal | `/api/journal` 401; no session | FAIL |
| RP-WEEK | Weekly/daily reports | 403 | FAIL |
| RP-SUB | Subscriber digest | Not proved | FAIL |
| RS-LAB | Research lab | 403 | FAIL |
| RS-CHAT | AI chat | 405 | FAIL |
| RS-PORT | Portfolio AI | Not proved | FAIL |
| WH-RADAR | Whale radar | scan 405 | FAIL |
| WH-VOICE | Voice | 405 | FAIL |
| WH-MEV | MEV report | 404 | FAIL |
| UX-LENS | Trust OS lenses | `/api/lenses` `/capabilities` `/api/trust-os` 404 | FAIL |
| UX-AUD | Audience routing | 404 | FAIL |
| UX-INT | Intent / 60s | 404 | FAIL |
| UX-DISC | Discipline mirror | 404 | FAIL |
| WOW-CORE | WOW eight | All HTML 404 | FAIL |
| WOW-F1F10 | F1–F10 | All HTML+API 404 | FAIL |
| WOW-COV | Coverage honesty | All 404 | FAIL |
| WOW-GLASS | Glass-box | Not proved | FAIL |
| WOW-PULSE | Trust pulse | 404 | FAIL |
| ML-TRAIN | ML train/predict | Not proved | FAIL |
| ML-EXPLAIN | ML explain | Not proved | FAIL |
| PLAT-GRID | Grid/rules/marketplace | Hub HTML only | FAIL |
| PLAT-DERIV | Derivatives hub | Not proved | FAIL |
| PLAT-TV | TradingView | Not proved | FAIL |
| B2B-FEED | B2B JSON/WS | WS opens; snapshot 0; demo feed 0; `/api/b2b/feed` 422 | FAIL |
| B2B-WL | White-label | Not proved | FAIL |
| B2B-WL-HOST | Hosted custom domain | Absent | FAIL |
| B2B-ORG | Org RBAC | Not proved | FAIL |
| B2B-SSO | OIDC/SAML | Not proved | FAIL |
| B2B-SCIM | SCIM | Not proved | FAIL |
| B2B-SUPER | Super terminal | Not proved | FAIL |
| FUND-TERM | Fund terminal | `/b2b` 200; `/model-card` 404 | FAIL |
| FUND-HA | Cloud multi-AZ | `scale_ready=false` | FAIL |
| FUND-PG | Postgres HA | Pool up; health API 500; dup register 500 | FAIL |
| FUND-IR | IR / restore | Not proved; db health 500 | FAIL |
| FUND-OBS | Observability | JSON 200; Sentry off; errors rising | FAIL |
| FUND-HEALTH | Health + status pages | live/ready 200; `/api/status` `/status` `/health/viral` 404 | FAIL |
| DD-PACK | DD pack | `/data-room` 404 | FAIL |
| DD-FOUR | Four-blockers API | inventory 404 | FAIL |
| DD-LAUNCH | Launch / GTM | launch+gtm 500 | FAIL |
| DD-PLAN | Plan/roadmap | 404 | FAIL |
| PRV-DSR | GDPR DSR | Status metadata only; DSR not run | FAIL |
| PRV-REG | Regulatory page | API 200; `/compliance` 404 | FAIL |
| SITE-LEGAL | Legal/FAQ/contact | 3 pages 200; 10+ 404 | FAIL |
| SITE-I18N | i18n | 404 | FAIL |
| SITE-PWA | PWA/SEO | manifest+sw 200; robots/sitemap/favicon 404 | FAIL |
| SITE-DOCS | Docs/OpenAPI | `/docs` 200; public docs 404 | FAIL |
| SITE-GQL | GraphQL | 422 | FAIL |
| SEC-KEYS | Security keys | Static status only | FAIL |
| INV-FULL | Capability inventory API | 404 | FAIL |
| SITE-PUBLIC | Public readiness probe | 404 | FAIL |

## What is true (not PASS)

These happened on Production and must not be inflated into feature PASS:

- Site process is up: `/` `/login` `/dashboard` `/docs` `/b2b` `/platform` `/oracle-accuracy` `/terms` `/privacy` `/disclaimer` HTML 200.
- Postgres pool is attached (`/health/ready`).
- Price **diagnostic** can resolve BTC/ETH from Binance Vision / Coinbase / Kraken / OKX.
- Deribit options JSON returns a large instrument list.
- B2B WebSocket **transport** accepts a demo key and heartbeats.
- Checkout **fail-closes** with 503 when billing is unconfigured.
- `/admin/launch` fail-closes 403.

None of those are a complete user journey with correct live product data.

## Blockers to flip this matrix

1. Deploy current SHA (OAuth, public-readiness, register alias, B2B `start()` async, honesty APIs).
2. Fix production session: cookie + login after register + no 500 on duplicate email.
3. Wire Oracle/radar to the live diagnostic price (stop serving 50005 stub / empty assets).
4. Run ingestion workers; Redis must be configured and connected.
5. Configure production Telegram, Stripe (required mode), Google OAuth on the Railway origin.
6. Re-run this matrix; PASS only after each journey succeeds on the published host.
