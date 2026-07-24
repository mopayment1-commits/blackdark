# BLACKDARK — Project Context Seed

**Institutional crypto arbitrage intelligence platform.** Async Python stack: live REST ingestion → SQLite + hot spool → multi-strategy arbitrage engine → AI oracle scoring → FastAPI dashboard. Modular pipeline designed to scale toward Top 50–100 exchanges/assets via a human-reviewed operational manifest.

---

## Runtime Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+, asyncio |
| Database | SQLite (`aiosqlite`, WAL mode) at `data/blackdark.db` |
| HTTP | `aiohttp`, FastAPI + Uvicorn (port **8080**) |
| Validation | Pydantic |
| NLP | VADER, TextBlob, optional OpenAI LLM fallback |
| Analytics | `pandas`, `pyarrow` (Snappy Parquet) |
| Cold storage | NDJSON spool → Parquet → optional S3 (`aioboto3`) |
| Config | Central `config.py` (env-var overrides) |

---

## Module Map

| File | Role |
|---|---|
| `config.py` | All tunables, whitelists, sector map, feature flags |
| `database.py` | Schema, migrations, CRUD, telemetry, archival purge helpers |
| `liquidity_discovery.py` | Hybrid filtering, CCXT/CoinGecko/CMC discovery, manifest I/O |
| `aggregator.py` | Live REST polling (Binance, OKX, Bybit) |
| `hot_storage.py` | In-memory buffer → NDJSON / ClickHouse / TimescaleDB |
| `arbitrage_engine.py` | Four arbitrage strategies + multi-modal enrichment loop |
| `ai_oracle.py` | 0–100 opportunity score, verdict, single-sentence oracle |
| `whale_tracker.py` | CVVD manipulation detection + SII sector rotation |
| `sentiment_engine.py` | Multi-source news NLP + rolling compound sentiment |
| `macro_correlations.py` | DXY/SPX/BTC-Gold macro regime + dynamic slippage/score weights |
| `obi_predictor.py` | Order book imbalance + flash-crash warnings |
| `onchain_tracker.py` | Exchange inflow/outflow matrix (simulated or API) |
| `parquet_compactor.py` | Cold/warm compaction: SQLite archival + NDJSON → Parquet |
| `cloud_syncer.py` | S3 upload with post-verify local retention |
| `dashboard.py` | Web UI, telemetry API, tier-gated opportunities, B2B feed |

---

## Database Tables

| Table | Purpose | Key Fields |
|---|---|---|
| `pricing_logs` | Spot/cross/perp tickers | `exchange`, `symbol`, `price`, `volume`, `market_type` |
| `order_books` | Depth snapshots | `bids`, `asks` (JSON), `market_type` |
| `funding_rates` | Perp funding | `funding_rate`, `next_funding_time` |
| `evaluated_opportunities` | Oracle-scored signals | `kind`, `asset`, `opportunity_score`, `oracle_verdict`, `payload_json` |
| `institutional_flows` | Whale/CVVD/SII events | `flow_type`, `asset`, `sector`, `notional_usd`, `metadata_json` |
| `market_sentiment_logs` | NLP news radar | `asset`, `source`, `raw_text`, `sentiment_score`, `compound_momentum` |
| `macro_market_logs` | Macro regime snapshots | `dxy_score`, `spx_score`, `macro_regime`, `volatility_buffer` |
| `cloud_sync_logs` | Parquet S3 sync audit | `local_path`, `s3_key`, `status`, `etag` |

**Dashboard telemetry:** `institutional` KPI = `COUNT(institutional_flows) + COUNT(market_sentiment_logs)`.

**Compaction targets (SQLite, >24h):** `pricing_logs`, `order_books`, `market_sentiment_logs` → purged after verified Parquet write.

---

## Aggregator Pipeline (`aggregator.py`)

1. **`_initialize_operational_inventory()`** — Runs **before** any ingestion. Builds/saves `data/operational_manifest.json`, prints summary, **pauses for human ENTER** (or `MANIFEST_AUTO_APPROVE=true`).
2. **`start_hot_pipeline()`** — Enables async hot-data flush workers.
3. **Polling loop** (default **5s**) — Concurrent REST fetch per exchange for manifest-approved symbols:
   - Spot + cross pairs (triangular legs)
   - Linear perpetual tickers + depth
   - Funding rates (perp symbols)
4. **Persistence** — Non-blocking enqueue to hot pipeline; optional SQLite mirror.

**Ingestion-ready exchanges:** `binance`, `okx`, `bybit` only (REST fetchers implemented). Manifest may list more tier-1 venues for future expansion.

---

## Dynamic Liquidity Manifest (`liquidity_discovery.py`)

**Safe hybrid filtering** for scaling to 50–100 exchanges/assets:

| Guard | Immutable Baseline |
|---|---|
| Exchanges | Binance, OKX, Bybit, Coinbase, Kraken, KuCoin, Gate.io |
| Assets | BTC, ETH, SOL, BNB, XRP |

**Discovery flow:**
1. CoinGecko — exchange trust score ≥ 7, asset 24h volume ≥ $5M
2. CoinMarketCap (optional, `COINMARKETCAP_API_KEY`) — cross-validates volume
3. CCXT — parallel registry probe for active USDT/USDC spot pairs
4. **`apply_whitelist_guards()`** — merges candidates; whitelist entries can never be removed
5. Output → `data/operational_manifest.json` (`status: pending_review` → `approved`)

Env: `MANIFEST_REQUIRE_REVIEW`, `MANIFEST_AUTO_APPROVE`, `LIQUIDITY_MAX_DYNAMIC_*`.

---

## Hot Data Pipeline (`hot_storage.py`)

In-memory deque buffer → batched async flush to `data/hot_spool/` (NDJSON). Backends: `local` (default), ClickHouse HTTP, TimescaleDB. Optional SQLite mirror via `HOT_STORAGE_MIRROR_SQLITE`.

---

## Cold/Warm Storage Compaction (`parquet_compactor.py`)

### SQLite historical compaction — `compact_historical_data()`
- Targets **`pricing_logs`**, **`order_books`**, **`market_sentiment_logs`** older than **24 hours** (`COMPACTION_MIN_AGE_HOURS`)
- Writes Snappy Parquet to **`data/history/{dataset}/year=YYYY/month=MM/day=DD/{dataset}.parquet`**
- Verifies row count via PyArrow metadata before **purging archived SQLite rows**
- Non-blocking trigger: **`trigger_historical_compaction_background()`** (1h cooldown) from arbitrage engine loop

### Hot-spool compaction — `run_compaction_once()`
- Prior-day NDJSON from `data/hot_spool/` → `data/historical_parquet/{type}/{year}/{month}/`
- Midnight UTC scheduler (00:05) also runs full `compact_historical_data()`

Optional **cloud_syncer** uploads Parquet to S3 after compaction.

---

## Arbitrage Engine (`arbitrage_engine.py`)

Reads latest `order_books` + `funding_rates` from SQLite each **5s** cycle. Four strategies with depth-walking, fees, **macro-adjusted slippage buffers**, withdrawal costs:

| Strategy | Function | Logic |
|---|---|---|
| Cross-exchange | `calculate_cross_exchange_arbitrage` | Buy low / sell high across venues |
| Triangular | `calculate_triangular_arbitrage` | 3-leg loops (e.g. USDT→BTC→ETH→USDT) |
| Spot–futures basis | `calculate_spot_futures_premium` | Spot vs perp premium on same asset |
| Funding | `calculate_funding_arbitrage` | Long/short perp pair by funding spread |

**Enrichment per cycle (merged into `market_context`):**
- **Whale tracker** → CVVD alerts + SII sector flows
- **OBI predictor** → order book imbalance, flash-crash warnings
- **On-chain tracker** → distribution/accumulation signals
- **Sentiment engine** → 5-minute compound indices via `get_rolling_compound_sentiment_index()` per asset
- **Macro correlations** → Risk-On / Risk-Off / Neutral regime; dynamic slippage + score weights

Funding opportunities receive SII convergence adjustments and CVVD risk buffers via `calculate_funding_arbitrage_with_institutional_context`.

Positive opportunities → **`ai_oracle.evaluate_and_store()`** → `evaluated_opportunities`.

---

## AI Oracle (`ai_oracle.py`)

Deterministic **0–100 score** (profit 40%, liquidity 35%, stability 25%) plus contextual adjustments:

| Source | Effect |
|---|---|
| Whale tracker | Score boost (CVVD/SII) |
| OBI predictor | ± adjustment |
| On-chain tracker | ± adjustment |
| Sentiment (normal) | ±4 max from compound index |
| **Sentiment panic** | Compound < **−0.6** → **−25 points** + institutional risk warning in `explanation_json` |
| Macro regime | Final score × weight (Risk-On **1.08**, Risk-Off **0.92**) |
| Funding SII | Convergence delta |

Outputs: `oracle_verdict`, structured `explanation_json`, single-sentence oracle (rules / OpenAI / Ollama).

---

## CVVD / SII Whale Tracking (`whale_tracker.py`)

### CVVD — Cross-Venue Volume Discrepancy
Detects manipulation from public trades + order books (Binance/OKX/Bybit):

| Pattern | Trigger |
|---|---|
| `cross_venue_manipulation` | Volume spike ≥ 2.2× + liquidity drop |
| `liquidity_spoof` | Depth collapse after spike |
| `iceberg_cluster` | ≥ 8 similar-size trades, low size CV |

### SII — Sector Inflow Index
60s trade buckets by sector (`SECTOR_MAP`: Layer 1, DeFi, L2). Velocity + acceleration → **±100 SII score**. Feeds funding convergence and oracle scoring.

**B2B export:** `InstitutionalDataExporter` → `/api/b2b/institutional-feed` (`BLACKDARK_B2B_API_KEY`).

---

## Sentiment Engine (`sentiment_engine.py`)

| Source | Config |
|---|---|
| RSS (CoinDesk, Cointelegraph, Decrypt) | `SENTIMENT_RSS_FEEDS` |
| CryptoCompare News API | `SENTIMENT_CRYPTOCOMPARE_API_KEY` |
| Mock X/Twitter + Telegram | `SENTIMENT_*_MOCK_ENABLED` |

**`analyze_sentiment_score(text)`** → **−1.0 to +1.0** (VADER → TextBlob → rules → optional LLM).

**`load_active_sentiment_indices_for_valuation()`** pulls per-asset 5-minute compound index before opportunity scoring.

**Defensive filter:** compound < `SENTIMENT_EXTREME_NEGATIVE_THRESHOLD` (−0.6) → −25 score penalty + oracle risk alert.

---

## Macro Correlations (`macro_correlations.py`)

| Indicator | Source |
|---|---|
| DXY (US Dollar Index) | Yahoo Finance / mock |
| SPX (S&P 500) | Yahoo Finance / mock |
| BTC/Gold ratio | Yahoo BTC-USD ÷ GC=F |

**`compute_macro_regime()`** classifies:

| Regime | Condition | Slippage buffer | Score weight |
|---|---|---|---|
| **Risk-On** | DXY falling, SPX rising | 3 bps (×0.85 multiplier) | ×1.08 |
| **Risk-Off** | DXY spiking, SPX crashing | 12 bps (×1.35 multiplier) | ×0.92 |
| **Neutral** | Otherwise | 5 bps (×1.0) | ×1.0 |

Persisted to `macro_market_logs`. Engine applies via `_slippage_buffer_usdt(..., market_context)` and `apply_macro_score_weight()` in oracle.

Env: `MACRO_DATA_SOURCE` (`mixed`, `mock`, `yahoo`), `MACRO_POLL_INTERVAL_SECONDS` (300).

---

## Dashboard (`dashboard.py`)

- **UI:** `http://localhost:8080` — Jinja2 terminal-style template
- **Tiers:** `free` (score < 50), `pro` (15s delay), `whale` (zero latency)
- **APIs:** `/api/opportunities`, `/api/telemetry`, `/api/b2b/institutional-feed`
- **Telemetry KPIs:** evaluated, pricing, orderbook, funding, institutional (flows + sentiment)

---

## Startup Commands

```bash
pip install -r requirements.txt
pip install pandas pyarrow vaderSentiment textblob

python aggregator.py          # Manifest review pause → live ingestion
python arbitrage_engine.py    # Strategy loop + enrichment + background compaction
python dashboard.py           # http://localhost:8080
```

**Typical env flags:**

| Variable | Purpose |
|---|---|
| `MANIFEST_AUTO_APPROVE=true` | Skip manifest ENTER prompt |
| `COINMARKETCAP_API_KEY` | CMC liquidity validation |
| `SENTIMENT_DATA_SOURCE=mixed` | RSS + mock social streams |
| `MACRO_DATA_SOURCE=mixed` | Yahoo + mock macro fallback |
| `SQLITE_HISTORICAL_COMPACTION_ENABLED=true` | SQLite → Parquet purge |
| `CLOUD_SYNC_ENABLED=true` | S3 cold storage |

---

## Data Flow (End-to-End)

```
Exchanges (REST)
    → aggregator.py (+ manifest gate)
    → hot_storage (NDJSON spool) ⇄ SQLite mirrors
    → arbitrage_engine.py (5s loop)
        ├── whale_tracker (CVVD/SII)
        ├── obi_predictor
        ├── onchain_tracker
        ├── sentiment_engine (NLP + panic filter)
        └── macro_correlations (regime + slippage)
    → ai_oracle.py (score × macro weight + verdict)
    → evaluated_opportunities
    → dashboard.py (UI + telemetry)

Background: compact_historical_data()
    → data/history/year=/month=/day=/*.parquet
    → SQLite purge (pricing, order_books, sentiment >24h)
Midnight: hot_spool → historical_parquet → cloud_syncer (S3)
```

---

## Key Paths

| Path | Contents |
|---|---|
| `data/blackdark.db` | Primary SQLite store (kept lean via compaction purge) |
| `data/operational_manifest.json` | Human-reviewed exchange/asset inventory |
| `data/hot_spool/` | Live NDJSON buffer |
| `data/history/` | SQLite-archived Parquet (Hive partitions) |
| `data/historical_parquet/` | Hot-spool Parquet archives |

---

*Last updated: 2026-07-20. Use this file as the canonical context seed for new chat sessions.*
---

## Session Update — 2026-07-21

**Live engines verified running together for the first time:** `dashboard.py` + `aggregator.py` (manifest approved) + `arbitrage_engine.py`, each in a separate terminal tab. Confirmed `age_seconds` on fresh opportunities dropped to ~1 minute (from ~21 hours stale).

**Critical bug fixed:** `database.py` — `delete_pricing_logs_by_ids`, `delete_order_books_by_ids`, `delete_sentiment_logs_by_ids` were passing unbounded row-id lists into a single SQL `IN (...)` clause, throwing `sqlite3.OperationalError: too many SQL variables`. Fixed by batching deletes in chunks of 500. Confirmed `cycle_status` returned to `ONLINE` after the fix and engine restart.

**Frontend gap closed:** `templates/index.html` previously only exposed Oracle + Market Radar. Added two new sections wired to existing backend endpoints (no backend changes needed):
- **Whale Tracker** section → calls `/api/whale-activity`, renders alert cards (asset, exchange, pattern, notional, timestamp)
- **Portfolio AI** section → calls `/portfolio/analyze` (POST), lets user add symbol+amount
*Last updated: 2026-07-20. Use this file as 
the canonical context seed for new chat sessions.*
