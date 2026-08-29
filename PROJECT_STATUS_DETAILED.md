# blackdark — Detailed Platform Status Report

> **Generated:** 2026-08-29 (UTC)  
> **Repository:** `mopayment1-commits/blackdark`  
> **Commit at generation:** `fb5d7c0a4d0463c7cafd110935bd5222b91c178b`  
> **Purpose:** Single source of truth for technical, functional, and operational state of the **blackdark** platform from absolute zero to current state.  
> **Method:** Direct codebase inspection. Prior audit outputs are referenced where noted — not re-derived.

---

## 1. PROJECT IDENTITY

### 1.1 Project name

| Source | Name used |
|--------|-----------|
| GitHub repository | `blackdark` |
| README title | `BLACKDARK` |
| Python package (`blackdark/__init__.py`) | `blackdark` (`__version__ = "1.0.0"`) |
| SDK (`sdk/blackdark/__init__.py`) | `blackdark` (`__version__ = "1.0.0"`) |
| Database file default | `data/blackdark.db` (`config.DB_PATH`) |
| Redis topic default | `blackdark.price.ticks` |
| Code comments / loggers | `BLACKDARK` (uppercase branding) |

**Naming consistency:** The canonical product name is **blackdark** (repository and package). Code and documentation frequently use **BLACKDARK** (uppercase) for branding, logging, and legal headers. No alternate product name (e.g. FalconAI) is used as the runtime identity; FalconAI references exist only in **rejection/denylist** documentation (`docs/CANONICAL_BINDING.md`, `trust_os.py`, `expert_execution.py`) as explicitly superseded marketing claims.

### 1.2 Version

| Component | Version |
|-----------|---------|
| Python SDK / package | `1.0.0` |
| Wave-01 Data Engine | `1.0.0` (`blackdark/data/api.py`) |
| Wave-01 Institutional | `1.2.0` (`blackdark/data/institutional.py`) |
| Wave-00 Hardening | `0.1.0` (`wave_00_hardening.py`) |
| B2B feed | `1.0.0` (`config.B2B_FEED_VERSION`) |
| Commercial MSA default | `1.0-FINAL` (`commercial_msa.py`) |

No single global application semver is published in `config.py`; version strings are module-scoped.

### 1.3 Repository structure (top level)

```
blackdark/
├── dashboard.py              # Primary FastAPI app (~5,584 lines, ~314 routes)
├── platform_api.py           # Secondary API surface (~2,703 lines, ~310 routes)
├── database.py               # Schema + migrations authority (~5,000 lines)
├── config.py                 # Central runtime configuration
├── run_service.py            # Microservice launcher (web/aggregator/arbitrage/ingestion/all)
├── bd_platform/              # 65 Python modules, 19 *_layer.py batch implementations
├── cap646/                   # Capability registry, UI surfaces, handlers
├── cap978/                   # Extended capability closure / institutional gate
├── blackdark/                # Wave-01 data engine package
├── api/routers/              # Modular API routers (auth, billing, institutional, oracle)
├── billing/                  # Subscription engine, plan registry, stores
├── microservices/            # Worker app for split deploy modes
├── ml/                       # Drift monitor, training, replay
├── templates/                # 50 Jinja2 HTML templates (server-rendered UI)
├── tests/                    # Pytest suite (1,177+ collected per prior audit)
├── scripts/                  # Ops, load test, audit, bootstrap tooling
├── deploy/k8s/               # Kubernetes manifests
├── docs/                     # Architecture, runbooks, DD, compliance
├── data/                     # SQLite DB, JSONL audit logs, ML models, seed artifacts
├── docker-compose.yml        # Local/staging multi-service stack
├── railway.toml              # Railway deploy config
├── requirements.txt          # Python dependencies
└── capabilities_checklist.xlsx  # 816-item PDF audit output + 10 repo extras
```

**Scale (measured):** ~691 Python files (excluding `.venv`), 50 HTML templates, 43 JSONL append-only logs under `data/`.

### 1.4 Main technology stack

| Layer | Technology | Evidence |
|-------|------------|----------|
| **Backend runtime** | Python 3.12 | `.github/workflows/ci.yml`, `requirements.txt` |
| **Web framework** | FastAPI + Starlette + Uvicorn | `dashboard.py`, `requirements.txt` |
| **Frontend** | **Server-rendered Jinja2 templates** (no React/Vue SPA; no `package.json` at root) | `dashboard.py` → `Jinja2Templates(directory="templates")` |
| **API patterns** | REST (primary), Strawberry GraphQL (partial), MCP references | `graphql_schema.py`, `public_api_docs.py` |
| **Primary database** | SQLite (soft launch / dev) **or** PostgreSQL (production strict) | `database.py`, `postgres_backend.py`, `ARCHITECTURE.md` |
| **Time-series data** | Relational tables (`pricing_logs`, `order_books`, `funding_rates`) — **no dedicated TSDB** (Influx/Timescale not present) | `database.py` SCHEMA |
| **Cache** | In-process TTL caches + optional **Redis** (`REDIS_URL`) | `config.py`, `hot_storage.py` |
| **Message queue / bus** | In-process bus (`SERVICE_BUS_LOCAL=true`) or **Redis pub/sub**; optional Kafka (`KAFKA_PRICE_STREAM_ENABLED`, default off) | `service_bus.py`, `config.py` |
| **ML** | scikit-learn, joblib | `ml/`, `data/models/` |
| **Exchange connectivity** | CCXT + custom adapters + WebSocket hubs | `aggregator.py`, `live_book_hub.py`, `exchange_adapters.py` |
| **Payments** | Stripe + Lemon Squeezy | `billing_service.py` |
| **Secrets** | Fernet encryption (`secrets_vault.py`, `SECRETS_MASTER_KEY`) | `ARCHITECTURE.md`, prior audit |
| **Deployment targets** | Railway (documented), Docker Compose, Kubernetes (`deploy/k8s/`) | `DEPLOY.md`, `railway.toml`, `docker-compose.yml` |
| **CI/CD** | GitHub Actions (`ci.yml`, `security.yml`, `sonarcloud.yml`, `cap978-institutional-gate.yml`) | `.github/workflows/` |

---

## 2. ARCHITECTURE OVERVIEW

### 2.1 High-level system diagram (text)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER / B2B CLIENT / TELEGRAM                        │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ HTTPS
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  SERVICE_MODE=web  →  dashboard.py (FastAPI)  +  platform_api.py routes     │
│  ├── Jinja2 pages: /dashboard, /oracle/{sym}, /b2b, /compliance, …          │
│  ├── REST /api/*  (~600+ combined route decorators)                         │
│  ├── Auth: sessions, MFA (TOTP), OAuth2 (when configured)                   │
│  └── Middleware: CORS, CSP nonce, production_guard, rate limits             │
└───────────────┬──────────────────────────────┬──────────────────────────────┘
                │                              │
                ▼                              ▼
┌───────────────────────────┐    ┌────────────────────────────────────────────┐
│  Decision / Oracle layer   │    │  Market / Execution edge                    │
│  oracle_unified.py         │    │  aggregator.py, arbitrage_engine.py         │
│  ai_oracle.py (arb labels) │    │  execution_engine.py (default: disabled)    │
│  dimension_conflict_guard  │    │  live_book_hub.py, fee_matrix.py            │
│  net_edge_truth.py         │    │  instant_alert_engine.py                    │
└───────────────┬───────────┘    └──────────────────┬─────────────────────────┘
                │                                    │
                ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  bd_platform/*_layer.py  (batch capability implementations, 19 layers)      │
│  cap646/handlers/*  ·  cap978/extension_registry  ·  signal_registry         │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
┌───────────────────┐  ┌────────────────────┐  ┌────────────────────────────┐
│ SQLite / Postgres  │  │ Redis (optional)    │  │ data/*.jsonl audit moat    │
│ database.py        │  │ service_bus, RL     │  │ oracle_audit_chain, etc.   │
└───────────────────┘  └────────────────────┘  └────────────────────────────┘
                ▲
                │ optional split workers
┌───────────────┴─────────────────────────────────────────────────────────────┐
│  SERVICE_MODE=aggregator|arbitrage|ingestion  →  microservices/worker_app   │
└─────────────────────────────────────────────────────────────────────────────┘
                ▲
                │ CEX REST/WS, on-chain adapters, news RSS
┌───────────────┴─────────────────────────────────────────────────────────────┐
│  External: Binance, OKX, Bybit, Coinbase, Kraken, KuCoin, Gate, Bitget,    │
│  MEXC, DefiLlama, CoinGecko, Telegram, Stripe, Didit KYC, etc.            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Frontend architecture

| Aspect | Implementation |
|--------|----------------|
| **Framework** | None (no SPA build chain). FastAPI serves HTML via Jinja2. |
| **Templates** | 50 files under `templates/` (e.g. `cap646_hub.html`, `anti_hype.html`, `intelligence_ledger.html`) |
| **Routing** | FastAPI `@app.get/post` in `dashboard.py` — ~313 route decorators; ~25+ non-API page routes including `/dashboard`, `/discipline-mirror`, `/oracle-accuracy`, `/b2b`, `/compliance`, `/cap646` |
| **State management** | Server-side session cookies + inline JSON bootstrapped into templates; no Redux/Vuex |
| **Primary navigation** | `/dashboard` (Six Heroes intent router), `/cap646` hub for capability waves A/B/C |
| **Charts** | TradingView bridge (`bd_platform/tradingview_bridge.py`) — embedded config, not a separate frontend app |
| **Accessibility** | Prior audit: **no WCAG automated testing**; limited `aria-label` only (`capabilities_checklist.xlsx` item classified missing) |

**USER_FACING capability surfaces (cap646):** 20 capability IDs mapped in `cap646/ui_pages.py` `USER_SURFACES`; remaining user-facing capabilities default to `/cap646` generic hub or `/dashboard` aggregation.

### 2.3 Backend architecture

| Aspect | Implementation |
|--------|----------------|
| **Pattern** | **Modular monolith** by default (`SERVICE_MODE=all` or `web`); optional **4-service split** (web, aggregator, arbitrage, ingestion) via `run_service.py` |
| **Entry point** | `dashboard:app` (Uvicorn) |
| **API layering** | `dashboard.py` (pages + core APIs) + `platform_api.py` (B2B/platform endpoints) + `api/routers/*` (auth, billing, institutional, oracle) |
| **Middleware / guards** | `production_guard.py`, `constitution_gates.py`, `regulatory_compliance_guard.py`, `security_auth.py`, `org_rbac.py`, `cap646/entitlements.py` |
| **Background work** | APScheduler jobs, asyncio tasks in aggregator/arbitrage workers, ML flywheel (`config.ML_FLYWHEEL_ENABLED`) |
| **Capability model** | `cap646/catalog.py` (IDs 1–646) + `cap978/catalog.py` (647+) with institutional gate tests |

### 2.4 Database architecture

| Store | Role |
|-------|------|
| **SQLite** (`data/blackdark.db`) | Default dev/soft-launch; WAL mode when `DB_WAL_MODE` |
| **PostgreSQL** | Required for strict production (`DATABASE_URL`); pool via `postgres_backend.py` (`PG_POOL_MAX` default 20) |
| **Redis** | Optional cache, distributed rate limits, service bus; required for `VIRAL_MODE` HA claims |
| **JSONL files** (`data/*.jsonl`, 43 files) | Append-only audit moat: `oracle_audit_chain.jsonl`, `decision_ledger.jsonl`, `in_app_alerts.jsonl`, etc. |
| **Parquet** | ML training (`data/training/labeled_oracle_dataset.parquet`) |
| **Joblib models** | `data/models/oracle_direction_*.joblib`, regime models |
| **S3 / cloud sync** | `cloud_sync_logs` table + optional sync; not the primary runtime store |
| **BigQuery / dbt** | `bigquery_export.py`, `dbt_connector.py` — requires external project setup |

**Fee data:** `fee_matrix.py` holds maker/taker/withdrawal fees **in memory** (refreshed from CCXT hourly). **No `fees` database table** — fees are not persisted as a relational ledger.

### 2.5 Infrastructure

| Component | Status |
|-----------|--------|
| **Hosting** | Railway documented (`DEPLOY.md`, `railway.toml`); K8s manifests in `deploy/k8s/`; no production URL committed in repo |
| **CDN** | Not configured in repository |
| **CI/CD** | GitHub Actions: critical gate suite on push/PR to `main`/`master`/`develop`; Docker build smoke; SonarCloud; security workflow |
| **Health probes** | `/health/live` (sidecar port+100), `/health/ready`, `/health/viral` |
| **Env management** | `docs/ops/ENV_VAR_REGISTRY.md`, `docs/ENV_CONFIG_MATRIX.md`, `.env.softlaunch.local` (gitignored, bootstrap script) |
| **Secrets files** | `keys/*.secrets.env` (mode 0600), Fernet vault |

---

## 3. DATABASE SCHEMA (Complete Inventory)

**Authority:** `database.SCHEMA` + `database._apply_migrations()` via `init_db()`. Alembic (`alembic/versions/`, 1 revision) is **not** runtime authority per `docs/DATABASE_MIGRATIONS.md`.

**Total tables:** 55 (confirmed by parsing `CREATE TABLE` statements in `database.py`).

### 3.1 Core market data tables

#### `pricing_logs`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| timestamp | TEXT NOT NULL | ISO UTC |
| exchange | TEXT NOT NULL | |
| symbol | TEXT NOT NULL | |
| price | REAL NOT NULL | |
| volume | REAL | |
| opportunity_score | REAL | |
| market_type | TEXT DEFAULT 'spot' | added by migration |

**Index:** `idx_pricing_exchange_symbol_ts (exchange, symbol, timestamp)`

#### `order_books`
| Column | Type |
|--------|------|
| id | INTEGER PK |
| timestamp | TEXT |
| exchange | TEXT |
| symbol | TEXT |
| bids | TEXT (JSON) |
| asks | TEXT (JSON) |
| market_type | TEXT DEFAULT 'spot' |

**Index:** `idx_orderbook_exchange_symbol_ts`

#### `funding_rates`
| Column | Type |
|--------|------|
| id | INTEGER PK |
| timestamp | TEXT |
| exchange | TEXT |
| symbol | TEXT |
| funding_rate | REAL |
| next_funding_time | TEXT |

**Index:** `idx_funding_exchange_symbol_ts`

### 3.2 Oracle / decisions / signals

#### `evaluated_opportunities`
id, timestamp, kind, asset, payload_json, opportunity_score, net_profit_usdt, oracle_verdict, oracle_sentence, explanation_json, confidence_percent — index on (asset, timestamp)

#### `oracle_predictions`
id, timestamp, asset, price_at_prediction, verdict, opportunity_score, confidence, resolved, price_after_24h/1h/4h, outcome, accuracy_score, label, direction_label, features_json, resolved_at, kind, source, market_regime — indexes on (asset, timestamp), (resolved, timestamp)

#### `decisions`
decision_id, context, prediction, confidence, timestamp, outcome, version, signature — UNIQUE(decision_id, version)

#### `market_signals`
signal_id, symbol, signal_type, value_json, confidence, source, timestamp, version, payload_hash, signature — UNIQUE(signal_id, version)

#### `learning_predictions` / `learning_outcomes` / `counterfactual_log`
ML flywheel chain with signature fields

#### `trust_evidence` / `proof_certificates`
Evidence and certificate storage with payload_hash + signature

### 3.3 User / auth / sessions

#### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| email | TEXT UNIQUE | |
| password_hash | TEXT | |
| name | TEXT | |
| created_at, last_login_at | TEXT | |
| stripe_customer_id | TEXT | migration |
| telegram_chat_id | TEXT | migration |
| mfa_enabled | INTEGER DEFAULT 0 | migration |
| mfa_secret_enc, mfa_pending_secret_enc | TEXT | Fernet-encrypted |
| mfa_recovery_hashes | TEXT | migration |
| oauth_provider, oauth_subject | TEXT | migration |
| username, email_verified_at, avatar_url | TEXT | migration |
| ui_lang | TEXT DEFAULT 'en' | migration |
| ux_mode_pref | TEXT DEFAULT 'beginner' | migration |
| timezone | TEXT DEFAULT 'UTC' | migration |
| password_is_set | INTEGER DEFAULT 1 | migration |

#### `user_sessions`
id, user_id → users(id) ON DELETE CASCADE, token UNIQUE, expires_at, created_at — index on token

#### `user_api_keys` (prior audit: API key storage)
| Column | Type |
|--------|------|
| id | INTEGER PK |
| user_id | INTEGER |
| exchange | TEXT |
| api_key_encrypted | TEXT (Fernet) |
| api_secret_encrypted | TEXT (Fernet) |
| label | TEXT |
| created_at, updated_at | TEXT |
| UNIQUE(user_id, exchange) | |

**Prior audit finding (referenced, not re-verified):** User exchange API keys are stored encrypted via `secrets_vault.py` Fernet in `user_api_keys`; not plaintext.

#### `auth_tokens` / `oauth_states`
Password reset and OAuth state tracking (migration DDL)

### 3.4 Billing / subscriptions

#### `subscriptions` (legacy)
email, tier, stripe_sub_id, status, created_at, trial_ends_at, past_due_at, access_bonus_until

#### `subscription_accounts` (SSOT for entitlements)
user_id UNIQUE, email, plan, subscription_status, payment_status, period dates, provider IDs, entitlements_version, grace_period_end, trial_ends_at, auto_renew fields

#### `billing_payment_events`
Provider events with idempotency_key UNIQUE

#### `billing_audit_ledger`
Plan/status change audit trail

#### `billing_webhook_events`
provider + event_id UNIQUE

#### `usage_meters`
user_id, capability_key, period_key, count, limit_value — UNIQUE(user_id, capability_key, period_key)

### 3.5 Alerts / execution / journal

- `alert_subscriptions` — email, telegram_chat_id, whatsapp_phone, alert toggles
- `alert_delivery_log` — delivery results JSON
- `arbitrage_alert_log` — kind, title, payload_json, delivered
- `execution_state` — singleton (id=1): panic_active, auto_execution_enabled
- `execution_logs` — side, asset, payload_json, live_mode
- `journal_entries` — user trading journal
- `oracle_usage_daily` — per-email daily oracle quota
- `simulation_logs` — paper/sim PnL

### 3.6 Analytics / behavior / audit

- `platform_analytics` — singleton counters (page_views, dashboard_views, etc.)
- `behavior_events` — event_type, user_email, tier, payload_json
- `analytics_events` — attribution_json, payload_json
- `audit_logs` — actor, action, payload_hash, signature, request_method/path
- `weekly_reports`, `maintenance_runs`, `forecast_logs`, `ml_model_runs`

### 3.7 Institutional / compliance / knowledge graph

- `institutional_flows`, `institutional_inquiries`, `corporate_dd_entries`
- `waitlist`, `retention_grants`, `telegram_free_subscribers`
- `kg_nodes`, `kg_edges` — knowledge graph with signatures
- `ip_registry` — asset IP documentation
- `ingestion_snapshots`, `ingestion_source_health`
- `risk_freeze_state` (singleton), `user_risk_settings`
- `cloud_sync_logs` — S3 sync metadata

### 3.8 Relationships (text)

```
users 1──* user_sessions
users 1──* user_api_keys
users 1──1 subscription_accounts
users 1──* journal_entries
users 1──* usage_meters
users 1──1 user_risk_settings
subscription_accounts ── billing_payment_events (via user_id)
subscription_accounts ── billing_audit_ledger (via user_id)
oracle_predictions ── learning_predictions (oracle_prediction_id, optional)
learning_predictions 1──* learning_outcomes
kg_nodes *──* kg_edges (source_node_id, target_node_id)
pricing_logs / order_books / funding_rates — standalone time-series (no FK to users)
```

### 3.9 Seed data status

| Artifact | Status |
|----------|--------|
| `scripts/bootstrap_free_human_ops.py` | Creates admin user, `.env.softlaunch.local`, keys files |
| `fee_matrix.py` | Seeded withdrawal/deposit fee tables in code |
| `data/` JSONL logs | Runtime-generated; not shipped as seed |
| ML models | `data/models/` contains trained joblib artifacts (runtime) |
| `DATA_MOAT_BLOCK_SYNTHETIC_SEED=true` | Blocks synthetic oracle seeding by default |
| Operational manifest | `liquidity_discovery.py` — exchange/symbol whitelist manifest |

### 3.10 Migration history

| Mechanism | Status |
|-----------|--------|
| `database._apply_migrations()` | **Runtime authority** — additive columns, billing tables, user profile columns, user_api_keys, risk tables |
| `alembic/versions/` | 1 baseline revision; **incomplete** vs live schema — documented as optional/historical only |
| Postgres translation | `postgres_backend._sqlite_schema_to_pg()` at DDL time |

---

## 4. ENVIRONMENT & DEPLOYMENT

### 4.1 Current deployment URL(s)

**None committed in repository.** `DEPLOY.md` instructs operator to generate a Railway domain (e.g. `blackdark-production.up.railway.app`). Load test log uses `[REDACTED]` placeholders. **No verified production URL in codebase.**

### 4.2 Hosting platform project status

| Platform | Config present | Deployed (in repo evidence) |
|----------|----------------|----------------------------|
| Railway | `railway.toml`, `DEPLOY.md`, `Dockerfile` | Documented; not confirmed live |
| Docker Compose | `docker-compose.yml`, `docker-compose.ha.yml` | Local/staging |
| Kubernetes | `deploy/k8s/web-deployment.yaml`, workers, HPA | Reference manifests only |

### 4.3 Environment variables (names only — secrets masked)

**Critical production** (from `docs/ops/ENV_VAR_REGISTRY.md`):

- `DATABASE_URL`
- `SOFT_LAUNCH`
- `SECRETS_MASTER_KEY` / `SECRETS_VAULT_KEY`
- `SESSION_TOKEN_PEPPER`
- `ADMIN_API_KEY` / `ADMIN_API_KEY_FILE`
- `ADMIN_EMAILS`
- `ADMIN_TOTP_SECRET`
- `ADMIN_MFA_REQUIRED`
- `APP_BASE_URL`
- `CORS_ALLOWED_ORIGINS`
- `CSP_NONCE_MODE`
- `REDIS_URL`
- `WEB_CONCURRENCY` / `WEB_REPLICAS`
- `VIRAL_MODE`
- `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` / `STRIPE_SUCCESS_URL` / `STRIPE_CANCEL_URL`
- `LEMON_SQUEEZY_*` (checkout + webhook)
- `TELEGRAM_SECRETS_FILE`
- `PORT`, `SERVICE_MODE`, `RUN_AGGREGATOR`, `INGESTION_ENABLED`
- `ENV` / `APP_ENV` / `ENVIRONMENT`
- `KAFKA_BROKERS`, `KAFKA_PRICE_STREAM_ENABLED`
- `OPENAI_API_KEY`, `COINMARKETCAP_API_KEY`
- `BLACKDARK_B2B_DEMO_KEY`, `BLACKDARK_B2B_API_KEY`
- `AUTO_EXECUTION_ENABLED`, `AUTO_EXECUTION_DRY_RUN`, `LIVE_EXECUTION_ALLOW_API`
- `ML_FLYWHEEL_ENABLED`, `ML_DRIFT_PSI_THRESHOLD`, `ML_OOD_FAIL_CLOSED`
- `PRO_TRIAL_DAYS` / `PAID_TRIAL_DAYS`
- `RAILWAY_ENVIRONMENT` (auto-detected)

Full matrix: `docs/ENV_CONFIG_MATRIX.md` (40+ variables documented).

### 4.4 Known blockers

| Blocker | Evidence |
|---------|----------|
| No signed HA load-test row | `docs/LOAD_TEST_RUN_LOG.md` — all runs marked **NOT signed HA** |
| Strict production guard may fail without Postgres + secrets | `production_guard.py`, `docs/RUNBOOK.md` pre-flight |
| Stripe/Lemon not configured → billing provider `"none"` | `billing_service.billing_provider()` |
| `verify_pentest_attestation()` → **False** | Prior consultant audit (not re-run) |
| 13 failing tests in full suite | Prior audit: 1162 passed, 13 failed, 2 skipped |
| Auto-execution disabled by default | `AUTO_EXECUTION_ENABLED=false`, `AUTO_EXECUTION_DRY_RUN=true` |
| WCAG / accessibility testing absent | Prior audit + capabilities checklist |
| M&A Intelligence (#113) not implemented | `capabilities_checklist.xlsx` |

### 4.5 Last deployment date and commit hash

| Field | Value |
|-------|-------|
| Last documented load test | 2026-08-12T00:07:00Z @ commit `73818e24635d2b6be8483127dcb2d37e0aadef6c` |
| Last git commit (this workspace) | `fb5d7c0a4d0463c7cafd110935bd5222b91c178b` — 2026-08-29 10:48:06 UTC |
| Production go-live marker | `scripts/mark_golive.py` exists; no `data/golive.json` committed with live URL |

---

## 5. DATA FLOW DOCUMENTATION

### 5.1 Example: "Get BTC analysis" (`GET /oracle/BTC`)

```
1. HTTP request
   └── dashboard.py route → oracle page handler / API

2. Market data fetch
   ├── live_book_hub.py / aggregator.py — WS or REST from Binance/OKX/Bybit/etc.
   ├── hot_storage.py — in-process + optional Redis cache (TTL: MARKET_CACHE_TTL_SEC=2s)
   └── database.pricing_logs — historical snapshots (if persisted)

3. Normalization
   ├── exchange_adapters.native_symbol() — symbol canonicalization
   ├── platform_universe.py — asset registry
   └── blackdark/canonical/schema.py — canonical schema (registry v1)

4. Feature assembly
   ├── oracle_data_hub.py — hub_score_adjustment
   ├── build_full_market_context() — weight_aggregator.py
   ├── sentiment_engine.py — fear/greed, panic penalties
   ├── bd_platform/derivatives_hub.py — funding/OI if available
   └── net_edge_truth.py — net edge after fees (fee_matrix.py)

5. AI / rule engine
   ├── oracle_unified.py — unified_multimodal_v1 pipeline
   │   ├── compute_base_technical_score()
   │   ├── apply_modal_adjustments_with_regime()
   │   ├── dimension_conflict_guard — abstain/veto on conflict
   │   └── optional ML model (data/models/oracle_direction_latest.joblib)
   ├── ai_oracle.py — used for arb evaluation labels (not second product oracle per ARCHITECTURE.md)
   └── ml/drift_monitor.py — OOD fail-closed if enabled

6. Compliance sanitization
   └── regulatory_compliance_guard.to_public_verdict() — public surface never exposes raw "Buy Now"
       (Prior audit: internal ai_oracle may use Buy Now; public API sanitized)

7. Persistence / audit
   ├── database.oracle_predictions — prediction row
   ├── oracle_audit_chain.jsonl — hash chain append
   ├── locked_predictions.jsonl — sealed predictions
   └── decision_certificate.py — exportable certificate payload

8. Response
   ├── JSON API: verdict, decision_sentence, net_edge_truth, signal_registry (pro mode)
   └── HTML: Jinja2 template with ux_mode=beginner|pro

9. Frontend render
   └── Server-rendered page at /oracle/BTC (no client-side router)
```

### 5.2 Bottlenecks / missing links

| Gap | Detail |
|-----|--------|
| **Stale quote guard** | `STALE_PRICE_GUARD_ENABLED` — fails closed on old quotes; WS coverage limited to binance/okx/bybit (`WS_PRICE_VENUES`) |
| **Fee authority** | Unknown venue → `fee_matrix` returns `None` (fail-closed); no DB fee history |
| **Reconciliation engine** | Prior audit: `market_context.py` multi-source failover only — **not** a full reconciliation engine |
| **On-chain depth** | On-chain modules exist (`bd_platform/onchain_hub.py`) but CEX path is primary for oracle |
| **GraphQL/MCP** | Partially wired; not the primary BTC analysis path |
| **Single-worker soft launch** | Load tests run 1×1 worker — not representative of HA |

---

## 6. MONETIZATION & COMMERCE

### 6.1 Payment gateway integration

| Provider | Code status | Webhooks |
|----------|-------------|----------|
| **Stripe** | `billing_service.py`, `stripe>=7.0.0` in requirements | `/webhook` — `checkout.session.completed` documented in `DEPLOY.md`; `billing_webhook_events` table |
| **Lemon Squeezy** | `LEMON_SQUEEZY_CHECKOUT_*` env keys, portal URL | `LEMON_SQUEEZY_WEBHOOK_SECRET` in env matrix |
| **Neither configured** | `billing_provider()` returns `"none"` | Checkout raises `RuntimeError("Stripe not configured")` |

**Products/prices in code** (`billing/plan_registry.py`):

| Plan | price_cents | Self-serve |
|------|-------------|------------|
| free | 0 | yes |
| pro | 1999 ($19.99/mo) | yes |
| elite | 4999 ($49.99/mo) | yes |
| quant | (see plan_registry) | yes |
| institutional | custom | no (sales-assisted) |

Legacy aliases: `whale` → `elite`, `decision_desk` → `elite`.  
`DEPLOY.md` also documents older tier names (Free $0, Pro $29, Decision Desk $49) — **pricing docs conflict**; code authority is `plan_registry.py`.

### 6.2 Subscription tiers (enforcement)

- **Registry:** `billing/plan_registry.py` `PLAN_DEFINITIONS`
- **Enforcement:** `cap646/entitlements.py` `EntitlementEngine` reads `subscription_accounts` SSOT
- **Feature matrix:** `auth_service.TIER_FEATURES`
- **Trial:** `PAID_TRIAL_DAYS` / `PRO_TRIAL_DAYS` default 7 days

### 6.3 Fee DB existence

**No relational fee table.** Fees are:

1. **Runtime matrix** — `fee_matrix.py` in-memory dict, refreshed via CCXT (`FEE_MATRIX_REFRESH_SEC` default 3600)
2. **Code seeds** — `WITHDRAWAL_FEE_USDT`, `DEPOSIT_FEE_USDT` per exchange
3. **Billing ledger** — `billing_payment_events.amount_cents` records **subscription payments**, not trading fees
4. **JSONL** — `data/credential_vault_fees.jsonl` exists (audit log style, not queryable fee engine)

**Answer:** Fees affect net-edge calculations but are **not** stored in a dedicated fee database schema.

### 6.4 Billing flow end-to-end test status

| Test / script | Status |
|---------------|--------|
| `tests/` billing tests | Present (`api/routers/billing.py`, subscription engine tests in CI subset) |
| CI critical gate | Does not claim full Stripe E2E against live PSP |
| `scripts/setup_stripe_production.py` | Setup helper exists |
| Soft launch closure | `cap978/soft_launch_closure.py` — shadow-forward mode |

**End-to-end live billing test:** **Not evidenced** in repository (no recorded successful live Stripe webhook integration test log).

---

## 7. CODE QUALITY & DEBT

### 7.1 Duplicate code blocks

| Area | Evidence |
|------|----------|
| Capability duplication | `cap978/catalog.is_duplicate()`, `bd_platform/data_sources_layer.py` marks #140 duplicate of #90 |
| Route surface duplication | `dashboard.py` + `platform_api.py` — overlapping API concerns (~600 routes combined) |
| Oracle paths | `ai_oracle.py` vs `oracle_unified.py` — documented as distinct roles (arb vs product) in `ARCHITECTURE.md` |
| Layer batch files | 19 `bd_platform/*_layer.py` files with similar check-list patterns |
| Sonar S1192 | Multiple files carry `# Sonar S1192: duplicated string literals` suppression comments |

### 7.2 Orphaned / hard-to-reach code

| Category | Examples |
|----------|----------|
| API-only capabilities | Hundreds of `bd_platform` functions reachable only via `/api/cap646/{id}` without dedicated UI |
| cap978 extensions | IDs 647+ with limited `USER_SURFACES` mapping |
| Microservice workers | `SERVICE_MODE=aggregator|arbitrage|ingestion` paths not used in default `all` monolith |
| Legacy `subscriptions` table | Superseded by `subscription_accounts` but both exist |
| `build_capabilities_checklist.py` | Old CAP978-based script; superseded by `scripts/audit_pdf_capabilities_checklist.py` |

### 7.3 Hardcoded values that should be configurable

| Value | Location |
|-------|----------|
| Exchange endpoints | `aggregator.EXCHANGE_ENDPOINTS` — hardcoded REST URLs |
| Withdrawal fee seeds | `fee_matrix.WITHDRAWAL_FEE_USDT` |
| Whitelist exchanges | `config.WHITELIST_EXCHANGES` frozenset |
| Promo codes | `DEPLOY.md`: `LAUNCHPRO`, `DARKSIDE`, `BLACKDARK` |
| Default quote amount | `config.DEFAULT_QUOTE_AMOUNT` (env-overridable) |
| B2B demo key example | `BLACKDARK_B2B_DEMO_KEY=bd_demo_launch_2026` in DEPLOY.md |

### 7.4 TODO / FIXME comments

| Scope | Count |
|-------|-------|
| `*.py` production code | **0** matches for `TODO` or `FIXME` (ripgrep) |
| Tests | 2 files reference `TODO` in test names/comments (`test_oracle_audit_chain.py`, `test_track_record_backfill.py`) |
| Documentation | 1 reference in `docs/dd/BLACKDARK_ACQUISITION_DD_CONTROL_MATRIX.md` |

---

## 8. DOCUMENTATION

### 8.1 README completeness

`README.md` covers: value layers, entry points, Six Heroes, canonical binding, install commands, load test references, classification disclaimer. **Substantive** — not a stub.

### 8.2 API documentation

| Surface | URL / file |
|---------|------------|
| Full OpenAPI | `/api/docs/openapi.json`, `/openapi.json` |
| Public filtered OpenAPI | `/api/docs/public-openapi.json` (`public_api_docs.py`) |
| HTML docs page | `/docs` |
| GraphQL | Strawberry schema in `graphql_schema.py` (not primary docs) |
| Architecture index | `ARCHITECTURE.md` |

### 8.3 Environment setup guide

| Doc | Path |
|-----|------|
| Install | `README.md` (venv, hashed requirements) |
| Env registry | `docs/ops/ENV_VAR_REGISTRY.md` |
| Env matrix | `docs/ENV_CONFIG_MATRIX.md` |
| Bootstrap | `scripts/bootstrap_free_human_ops.py` |
| Soft launch | `.env.softlaunch.local` via bootstrap |

### 8.4 Deployment runbook

| Doc | Path |
|-----|------|
| Deploy | `DEPLOY.md`, `LAUNCH_GUIDE.md` |
| Day-2 ops | `docs/RUNBOOK.md` |
| Go-live | `docs/GO_LIVE_AR.md`, `scripts/finalize_launch.py` |
| Glass Box | `docs/GLASS_BOX_OPERATOR_RUNBOOK.md` |
| Buyer handover | `docs/ops/BUYER_HANDOVER_PACK.md` |
| Load test log | `docs/LOAD_TEST_RUN_LOG.md` |

---

## 9. PERFORMANCE METRICS

### 9.1 API response times (key endpoints)

**No live measurements in this workspace.** Referenced from prior load test (`docs/LOAD_TEST_RUN_LOG.md`, 2026-08-12, commit `73818e2`, **NOT signed HA**, 1 worker):

| Endpoint class | p50 / p95 (ms) | Notes |
|----------------|----------------|-------|
| Live health | 51.8 / 57.6 | ok=1.0 |
| Readiness | 46.6 / 55.1 | |
| trust_os | 69.1 / 76.9 | |
| oracle_quick | 446 / 1448 | ok=0.75 |
| Other paths | 429 rate-limited | controlled degradation |

**Status:** Metrics are **outdated** (2026-08-12) and **not** valid for HA/production claims.

### 9.2 Database query performance

- No slow-query log configuration found in repository.
- SQLite WAL + busy timeout (`DB_BUSY_TIMEOUT_MS`) for dev.
- Postgres pool `PG_POOL_MAX=20`.
- Indexes documented per table in `database.py` SCHEMA.

### 9.3 Frontend bundle size

**Not applicable** — no JS bundler or `package.json`. Frontend is server-rendered HTML + inline scripts. No measured asset bundle.

### 9.4 Concurrent user capacity

**Prior load test (referenced):**

- Script: `scripts/load_test_concurrent.py --workers 40 --requests 80`
- Environment: local Soft Launch, 1 uvicorn worker, Postgres+Redis present
- Hard errors: 0
- Viral approval: **False** (single instance)
- Honest HA requires: Postgres + Redis + `WEB_CONCURRENCY`×`WEB_REPLICAS` ≥ 2 + signed log row — **not achieved**

`/api/viral/readiness` and `/api/scale/readiness` endpoints exist for self-assessment JSON.

---

## 10. DECISION LOG

| Decision | Rationale | Rejected alternative |
|----------|-----------|---------------------|
| Single product "Trust OS" with 4 layers + 6 Heroes | `docs/CANONICAL_BINDING.md` — reduces inflated "16 platforms" marketing | FalconAI 16-platform valuation shape |
| `oracle_unified.py` as canonical product oracle | One decision path for dashboard + certificates | Separate competing oracle engines |
| Fernet + 0600 secret files for secrets | Shipped path, no HSM dependency | HashiCorp Vault as production authority |
| SQLite allowed only for Soft Launch | Fast demo; explicit non-HA | Claiming SQLite as production HA |
| PostgreSQL required for strict production | `production_guard`, pool support | SQLite at scale |
| Auto-execution default **off** | Regulatory/safety posture | Live trading by default |
| Public oracle verdict sanitization | `regulatory_compliance_guard` | Exposing internal "Buy Now" verbatim |
| Runtime migrations in `database.py` | Single authority, SQLite+PG parity | Alembic as competing migration path |
| Modular monolith default | Simpler ops; split optional via SERVICE_MODE | Mandatory microservices from day one |
| Fail-closed fee authority | Unknown fee → None in `fee_matrix.py` | Default fee invention for unknown venues |
| CAP646/CAP978 capability catalogs | Institutional gate + entitlement IDs | Ad-hoc feature flags per endpoint |
| JSONL audit moat alongside SQL | Tamper-evident append-only evidence | SQL-only audit |
| CI critical gate ≠ full test suite | `.github/workflows/ci.yml` comment: ~20 pre-existing failures outside gate | Claiming full green suite |

---

## 11. PLATFORM COMPLETENESS ASSESSMENT

### 11.1 Stated goal

README: *"Decision intelligence / Trust OS — prove-it analytics, not signal spam."*  
Canonical binding: **one product**, four value layers, six heroes — not a loose script collection.

### 11.2 Integrated platform vs disconnected components

| Criterion | Assessment | Evidence |
|-----------|------------|----------|
| Single entry point | **Yes (partial)** | `dashboard.py` serves `/dashboard`, `/login`, `/oracle/{sym}`, `/b2b`, `/compliance` |
| Shared data layer | **Yes** | `database.py` + `data/*.jsonl` moat shared across modules |
| Consistent navigation | **Partial** | Six Heroes intent router on dashboard; 796/816 capabilities lack dedicated nav (cap646 hub generic) |
| Unified auth/billing | **Yes (when configured)** | `auth_service`, `subscription_accounts`, `EntitlementEngine` |
| Execution integration | **No (by design)** | Auto-execution disabled; advisory-only default |
| Microservices wiring | **Optional / often off** | Default `SERVICE_MODE=all` monolith |

### 11.3 Features in code but NOT reachable from main UI

**From `capabilities_checklist.xlsx` audit (816 PDF items — referenced, not re-audited):**

| Status | Count |
|--------|-------|
| مبني وشغال فعليًا | 154 |
| مبني جزئيًا | 589 |
| غير موجود إطلاقًا | 4 |
| غير مؤكَّد | 69 |

**Structural evidence of disconnect:**

- `cap646/ui_pages.py` maps only **20** `USER_FACING` capability IDs to explicit UI paths; others default to `/cap646` generic hub or API-only.
- **65** `bd_platform` modules vs **20** explicit UI surfaces.
- Examples of API-only or hidden surfaces: most `bd_platform/*_layer.py` batch endpoints (`/api/cap646/{id}/execute`), Wave-01 data engine (`blackdark/data/`), many exchange connector admin paths, MCP server tools, GraphQL schema, BigQuery/dbt export pipelines.
- **10 repo capabilities** not in PDF at all (rows 817–826 in checklist): e.g. CEX-DEX Arbitrage Scanner, Constitution Gates — some have pages (`/coverage-honesty`, `/anti-hype`) but many are API-first.

### 11.4 Verdict: Is this a complete platform today?

## **NO — partial platform (integrated core, incomplete surface coverage)**

**Evidence:**

1. **Capability coverage:** 589/816 checklist items are **مبني جزئيًا**; 69 **غير مؤكَّد**; 4 **غير موجود إطلاقًا** (`capabilities_checklist.xlsx`).
2. **UI wiring:** Only 20 capabilities have explicit UI surface maps; hundreds exist as backend layers without user navigation.
3. **Execution:** Not a complete trading platform — auto-execution off, paper/sim only for trading engines.
4. **HA/scale:** No signed multi-worker HA proof; soft-launch posture.
5. **Commerce:** Billing code exists but live PSP integration not evidenced end-to-end.
6. **Compliance certifications:** Explicitly not claimed (no SOC2/ISO/WCAG) per README and architecture docs.

**What IS integrated:** Oracle decision path, accuracy ledger, discipline mirror, dashboard heroes, auth/session layer, entitlement engine, and shared database/audit chain function as a **coherent core product** — not merely disconnected scripts.

---

## 12. CRITICAL GAPS & BLOCKERS

### 12.1 What prevents public launch today

| Blocker | Severity |
|---------|----------|
| No verified production deployment URL / go-live attestation in repo | High |
| `verify_pentest_attestation()` → **False** (prior audit) | High |
| Full test suite: **13 failures** (prior audit: 1162 passed) | High |
| No signed Postgres+Redis multi-worker HA load test | High |
| Billing not proven live (Stripe/Lemon webhooks) | Medium-High |
| 69 capabilities **غير مؤكَّد** in checklist | Medium |
| WCAG/accessibility absent (prior audit) | Medium (legal/UX) |
| Pricing doc conflict ($19.99 vs $29 in DEPLOY.md) | Medium (commercial) |

### 12.2 What would break under 100 concurrent users

| Risk | Mechanism |
|------|-----------|
| Single uvicorn worker | Default local deploy 1×1; oracle_quick p95 **1448ms** at 40 workers in prior test |
| SQLite lock contention | If `DATABASE_URL` not set to Postgres under load |
| Redis absent | `SERVICE_BUS_LOCAL=true` → no cross-instance bus; rate limits not shared |
| Exchange rate limits | `INGRESS_GUARD_ENABLED` may ban polls; 9 exchanges × many symbols |
| Oracle ML inference | Synchronous scikit-learn on hot path without batching evidence |
| No CDN/static edge | All HTML rendered server-side per request |

### 12.3 Highest legal risk (from prior consultant-report verification — referenced)

| Risk | Prior audit finding |
|------|---------------------|
| **Investment advice / "Buy Now" exposure** | Internal `ai_oracle.py` uses Buy Now semantics; **public** surface sanitized via `regulatory_compliance_guard.py` — misconfiguration risk if guard bypassed |
| **KYC/AML** | Partial implementation (`institutional_commerce.py`, `didit_kyc.py`, `legal_commercial_layer`) — **not** a complete licensed compliance program |
| **Unregistered securities / fund marketing** | Emerging Fund Terminal, B2B materials exist — require human legal review; README disclaims financial advice |
| **Data protection** | GDPR service exists (`gdpr_service.py`) but enterprise DPA/evidence not evidenced as signed |
| **WCAG** | No automated accessibility compliance — ADA/EAA exposure for public UI |

### 12.4 Highest technical debt risk

| Risk | Detail |
|------|--------|
| **Schema migration dual-path confusion** | Alembic incomplete vs `database._apply_migrations()` — operator error risk |
| **600+ routes across two files** | `dashboard.py` + `platform_api.py` maintenance burden |
| **589 partial capabilities** | Half-implemented features create false completeness impression |
| **In-memory fee matrix** | No historical fee audit trail; restarts lose unsaved CCXT refresh |
| **JSONL + SQL dual writes** | Consistency not always transactional |
| **Bandit MEDIUM=44** (prior audit) | Security hygiene debt |
| **13 failing tests** | Regression risk on non-critical paths |

---

## APPENDIX A — Prior audit cross-references (not re-derived)

### A.1 Consultant 13-point verification summary

| Claim area | Prior finding |
|------------|---------------|
| API key storage | Fernet-encrypted in `user_api_keys` via `secrets_vault.py` / `user_keys_service.py` |
| Buy Now oracle | Internal in `ai_oracle.py`; public sanitized |
| Encryption / 2FA / Auth | Fernet secrets; TOTP MFA (`admin_mfa.py`, user MFA columns); OAuth2 when configured |
| KYC/AML | Partial — `institutional_commerce.py`, `didit_kyc.py`, AML gate in legal layer |
| Reconciliation | Partial — multi-source failover in `market_context.py`, not full engine |
| MRM | Partial — `buyer_model_card.py` docs only, not formal MRM |
| Feature flags | Env toggles + `universe_rollout.py`, not canary deployment platform |
| Vendor monitoring | Partial institutional assurance artifacts |
| WCAG | **Not present** (aria-label only) |
| Data lineage | Partial — `data_provenance_score.py`, `blackdark/data/provenance.py` |
| Full pytest | **1162 passed, 13 failed, 2 skipped** |
| Load test | 2026-08-12, **NOT signed HA** |
| Pentest attestation | `verify_pentest_attestation()` → **False** |
| Bandit | HIGH=0, MEDIUM=44 |

### A.2 Capabilities checklist summary (`capabilities_checklist.xlsx`)

- **Source:** Attached PDF `capabilities_checklist_66b7.pdf` — 816 items
- **Output rows:** 826 (816 + 10 repo extras)
- **Distribution:** 154 working · 589 partial · 4 missing · 69 uncertain
- **Missing:** #113 M&A Intelligence, #380 deposit currency list, #381 withdrawal currency list, #627 comparison engine
- **Script:** `scripts/audit_pdf_capabilities_checklist.py`

---

## APPENDIX B — File references

| Artifact | Path |
|----------|------|
| This report | `PROJECT_STATUS_DETAILED.md` |
| Capabilities audit | `capabilities_checklist.xlsx` |
| Architecture | `ARCHITECTURE.md` |
| Canonical binding | `docs/CANONICAL_BINDING.md` |
| Database authority | `database.py`, `docs/DATABASE_MIGRATIONS.md` |
| Load test log | `docs/LOAD_TEST_RUN_LOG.md` |
| Env registry | `docs/ops/ENV_VAR_REGISTRY.md` |

---

*End of report. All claims trace to repository files at commit `fb5d7c0` unless explicitly marked as prior-audit reference.*
