# 03 — COMPLETE SYSTEM UNIVERSE

**Audit ID:** `IDA-2026-BLACKDARK-001`  
**Wave:** 1 — Complete System Discovery (§18–§19)  
**Generated:** 2026-09-10T23:47:21Z  
**HEAD SHA:** `14bbf492c69b51e2008d6dc9baefe3d578ae0696`  
**Evidence Level:** L0 (repository enumeration)  
**Policy:** Full discovery — no sampling. Discovery ≠ audit.

---

## 1. Discovery Denominators (§19)

| Denominator | Count | Discovery Method | Audited |
|---|---:|---|---|
| Source files (tracked) | **1,435** | `git ls-files` | NO |
| Python source files | **834** | extension filter | NO |
| Top-level modules/packages | **24** | path prefix | NO |
| FastAPI services | **2** | `dashboard:app`, `worker_app:app` | NO |
| HTTP route decorators | **657** | regex scan all `.py` | NO |
| HTML page paths | **68** | `dashboard.py` route enumeration | NO |
| Jinja templates | **50** | `templates/` inventory | NO |
| Interactive UI controls | **NOT VERIFIED** | template parse deferred Wave 10 | NO |
| SQLAlchemy ORM models | **3** | `blackdark/data/models.py` | NO |
| DB tables (CREATE TABLE universe) | **76** | repo-wide DDL scan | NO |
| SQL migrations (Wave 01) | **17** | `blackdark/data/migrations/` | NO |
| Alembic revisions | **1** | `alembic/versions/` | NO |
| Algorithm/model candidate files | **403** | keyword + path heuristic | NO |
| Capability artifact files | **24** | docs/cap646 JSON | NO |
| Direct Python dependencies | **65** | `requirements*.txt` | NO |
| Test files | **200** | `tests/test_*.py` | NO |
| Test functions | **1,054** | AST parse | NO |
| CLI entry points (`__main__`) | **147** | AST/grep | NO |
| Background scheduler/worker files | **5** | filename heuristic | NO |
| Infrastructure manifest files | **14** | docker/nginx/railway | NO |
| User journeys | **NOT VERIFIED** | deferred Wave 11 | NO |

Machine-readable: `WAVE_01_DISCOVERY_DENOMINATORS.json`, `WAVE_01_ROUTE_INVENTORY.json`

---

## 2. Repository Structure

### 2.1 Source Roots & Apps

| Root | Files | Role |
|---|---:|---|
| `docs/` | 329 | Status registers, batch artifacts, evidence JSON (claims — not truth) |
| `tests/` | 202 | Automated test suites |
| `scripts/` | 171 | Operational/audit CLI scripts |
| `bd_platform/` | 74 | Platform intelligence layers |
| `templates/` | 50 | Jinja2 UI |
| `cap646/` | 48 | Capability runtime/catalog |
| `blackdark/` | 47 | Data engine, canonical store |
| `api/` | 26 | FastAPI routers |
| `data/` | 38 | Data artifacts, evidence jsonl |
| `ml/` | 16 | ML training artifacts |
| `microservices/` | 4+ | Worker FastAPI app |
| `billing/` | 11 | Billing subsystem |
| `cap978/` | 12 | CAP978 catalog |
| `browser_extension/` | 13 | MV3 Chrome extension |
| `static/` | 14 | CSS/JS/PWA assets |
| `locales/` | 25 | i18n catalogs |

### 2.2 Monolith vs Microservices

| Component | Entry | Port (default) |
|---|---|---|
| **Primary web+API** | `dashboard.py` → `uvicorn dashboard:app` | 8080 |
| **Worker services** | `microservices/worker_app.py` via `run_service.py` | 8091–8093 |
| **Launcher** | `run_service.py` modes: all/web/aggregator/arbitrage/ingestion | — |

---

## 3. Runtime Discovery (§18)

### 3.1 Entry Points

- **147** Python files with `if __name__ == "__main__"`
- **37** argparse CLI scripts
- **1** module CLI: `python -m blackdark.data`
- **0** Celery workers (comment-only reference)
- **0** Flask apps

### 3.2 Processes & Background Work

| File | Inferred Role |
|---|---|
| `ingestion_scheduler.py` | Async ingestion scheduling |
| `microservices/worker_app.py` | Worker health + background loops |
| `aggregator.py` | Data aggregation (CLI) |
| `arbitrage_engine.py` | Arbitrage engine (CLI) |
| `whale_tracker.py` | Whale tracking (CLI) |

**Queues:** Redis service bus (`service_bus.py`) — pub/sub pattern discovered; depth NOT VERIFIED.

---

## 4. Network Discovery (§18)

### 4.1 API Surface

| Layer | Routes |
|---|---:|
| `@app.*` in `dashboard.py` | 225 |
| `@app.*` in `worker_app.py` | 4 |
| Router modules (all `.py`) | 421 |
| GraphQL | 1 (`/graphql`) |
| WebSocket | 1 (`/ws/b2b/feed`) |
| Static mount | `/static` |
| **Total route decorators** | **657** |

### 4.2 Router Modules (`api/routers/`)

| Module | Routes | Prefix |
|---|---:|---|
| heroes.py | 74 | — |
| institutional.py | 49 | `/api/institutional` |
| oracle.py | 28 | — |
| compounding.py | 28 | — |
| cap646.py | 26 | `/api/cap646` |
| auth.py | 24 | `/api/auth` |
| observability.py | 13 | — |
| arbitrage.py | 13 | `/api/arbitrage` |
| billing.py | 11 | `/api/billing` |
| (+ 11 more) | 42 | various |

Additional routers: `platform_api.py` (86), `blackdark/data/api.py` (11), `blackdark/data/systems_api.py` (16)

### 4.3 Webhooks

- `/api/webhooks` — Didit KYC (`didit_webhook.py`)
- `/api/telegram` — Telegram webhook
- Billing webhooks — Stripe (in billing routers + `database.py` tables)

---

## 5. UI Discovery (§18)

| Category | Count |
|---|---:|
| HTML page URL paths | 68 |
| Jinja templates | 50 (47 pages + 3 partials) |
| Orphan template | `templates/index.html` (not routed) |
| Static JS files | 7 (+ `sw.js`) |
| Browser extension pages | 2 |
| PWA manifest | 1 |

**Rendering surface:** exclusively `dashboard.py` (FastAPI + Jinja2).  
**CSP architecture:** `security_middleware.py` injects `csp_events.js`.

---

## 6. Data Discovery (§18)

### 6.1 Database Architecture

| Path | Role |
|---|---|
| `database.py` | Primary runtime schema authority (40 baseline + migrations) |
| `database_ddl.py` | SSOT DDL for 9 spine tables |
| `postgres_backend.py` | Postgres adapter, SQLite→PG translation |
| `blackdark/data/db.py` | Wave 01 async SQLAlchemy engine (Postgres-only) |
| `blackdark/data/migrations/*.sql` | 17 numbered SQL migrations |
| `alembic/versions/` | 1 revision — **documented non-authoritative** |

### 6.2 ORM vs Raw SQL

| ORM models | 3 (`DataSource`, `IngestionRun`, `OhlcvData`) |
| Tables total | 76 unique production table names |
| Gap | ~73 tables without SQLAlchemy models |

### 6.3 Cache & Hot Storage

| Component | Technology |
|---|---|
| Price cache | Redis (`redis_price_cache.py`) |
| Service bus | Redis pub/sub |
| Hot tier | NDJSON / ClickHouse / TimescaleDB options |
| Canonical store | `blackdark/canonical/store.py` |
| Default DB | SQLite `data/blackdark.db` if `DATABASE_URL` empty |

---

## 7. Models / Intelligence Discovery (§18)

**403 files** match model/intelligence heuristics (predict, forecast, score, oracle, signal, regime, etc.)

### 7.1 Named Subsystems (sample — full list in `WAVE_01_MODEL_CANDIDATES.json`)

| Subsystem | Key Paths |
|---|---|
| AI Oracle | `ai_oracle.py`, `api/routers/oracle.py` |
| Arbitrage | `arbitrage_engine.py`, `arbitrage_service.py`, `api/routers/arbitrage.py` |
| Sentiment | `sentiment_engine.py` |
| Regime ML | `ml/train_regime_models.py`, `ml/*.joblib` |
| Alpha/Risk layers | `bd_platform/alpha_engine.py`, `bd_platform/advanced_ta_risk_layer.py` |
| RVM | `rvm/`, `api/routers/rvm.py` |
| Compounding/Knowledge graph | `api/routers/compounding.py`, KG tables in schema |
| Platform intelligence | 20+ `bd_platform/*_layer.py` modules |

**Validation status for all:** NOT VERIFIED (discovery only)

---

## 8. Integrations Discovery (§18)

| Provider | Files touching (heuristic) |
|---|---:|
| Binance/CCXT | 160+ |
| Telegram | 83 |
| Postgres | 76 |
| Redis | 57 |
| Stripe | 54 |
| Webhooks (generic) | 54 |
| Coinbase | 28 |
| OAuth | 22 |
| Didit KYC | 10 |
| OpenAI | 5 |
| ClickHouse | 5 |
| TimescaleDB | 6 |

---

## 9. Security Discovery (§18)

| Component | Paths |
|---|---|
| Auth service | `auth_service.py`, `api/routers/auth.py` |
| Security middleware | `security_middleware.py` |
| MFA | `admin_mfa.py`, auth router |
| Session/tokens | `database.py` users/sessions tables |
| Rate limiting | `security_auth.py` (Redis) |
| Security models | `security_models.py` |
| Anonymous visitor | `anonymous_visitor/` package (20 modules) |

**29** Python files match auth/security path patterns.

---

## 10. Infrastructure Discovery (§18)

| Asset | Path |
|---|---|
| Docker Compose | `docker-compose.yml`, `docker-compose.ha.yml` |
| Nginx | `nginx/blackdark.conf` |
| Railway | `railway.toml` |
| CI workflows | `.github/workflows/ci.yml`, `security.yml`, `sonarcloud.yml`, `cap978-institutional-gate.yml` |
| SBOM | `docs/data-room/sbom/cyclonedx-python.json` |
| License inventory | `docs/data-room/licenses/` |

---

## 11. Capability / Status Register Discovery

Prior project artifacts (CLAIM REQUIRING REVALIDATION):
- `docs/BATCH07_*` — batch 301–350 closure packages
- `docs/BATCH05_*` — batch 401–500
- `cap646/` runtime catalog
- `cap978/` institutional gate catalog
- Capability spine references in docs

**826-capability PDF registry** referenced in scripts/docs — count NOT VERIFIED as unique semantic capabilities (prior audits found heterogeneous namespaces).

---

## 12. GIPS Applicability Gate (§15) — Initial Screen

User-facing surfaces discovered that **may** trigger GIPS review:
- `oracle_accuracy.html` — oracle/track record presentation
- `platform.html`, `coin.html` — market data display
- Hero surfaces with performance/confidence semantics
- Backtest scripts: `scripts/backfill_track_record.py`, `tests/test_oracle_track_record.py`

**GIPS status:** APPLICABILITY NOT VERIFIED — Wave 3/5/6 must classify actual vs simulated vs backtested presentation.

---

## 13. Discovery Integrity

| Check | Result |
|---|---|
| Full repo enumeration (no sampling) | YES — all 1,435 tracked files in universe |
| Discovery denominators computed | YES |
| Discovery treated as audit | **NO** — all items NOT AUDITED |
| Prior claims accepted | **NO** — zero-trust |

---

## 14. Wave 1 Asset ID Seeds

Asset IDs assigned in SSOT for discovered material components (sample):

- `SVC-001` dashboard:app
- `SVC-002 worker_app:app
- `API-001..657` route handlers (bulk register Wave 9)
- `UI-001..068` page paths
- `DB-001..076` tables
- `MDL-001..403` model candidates (to be classified Wave 3)
- `DEP-001..065` direct dependencies

Full asset register expansion: Wave 2–22.

---

## Wave 1 Status

**DISCOVERY COMPLETE:** YES  
**AUDIT COMPLETE:** NO  
**Next:** Wave 2 — Architecture & Reachability
