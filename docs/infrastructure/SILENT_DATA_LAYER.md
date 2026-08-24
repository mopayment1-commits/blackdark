# Silent Data Layer — Exchange Flows, The Block, Solana RPC (#97, #95, #93)

**Not user-facing features.** Internal metrics and context for Decision Engine (#48) and Alpha Engine (#13).

## Connectors

| Feature | Module | Role |
|---------|--------|------|
| #97 Token Exchange Flows | `exchange_flow_metric.py` | In/out/net flows with internal transfer filter |
| #54 Exchange Netflow Intelligence | `exchange_netflow_intelligence.py` | Rolling normalization, percentile, regime |
| #59 Futures CVD / Taker Flow | `futures_cvd_metric.py` | CVD + trade-side classification QA |
| #66 Historical Flat Files | `historical_flat_archive.py` | Partitioned archive + checksum manifests |
| #95 The Block Articles | `theblock_connector.py` | Research RSS → AI context lines |
| #68 Investing.com RSS | `investing_com_connector.py` | News RSS + high-impact scoring |
| #93 Solana RPC | `solana_rpc_connector.py` | Public RPC (upgrade via `SOLANA_RPC_URL`) |
| #21 Binance API | `binance_connector.py` | Spot/futures market data source |
| #25+#26 Lending Markets | `lending_markets_connector.py` | Borrows outstanding + borrow APR |
| #85 Order Flow Intelligence | `order_flow_intelligence.py` | Aggressive flow + trade-side QA |
| #86 Polygon.io API | `polygon_io_connector.py` | Macro/equities context (SPY proxy) |
| #87 Polygonscan API | `polygonscan_connector.py` | Polygon on-chain health |
| #60 Gate.io API | `gateio_connector.py` | Early altcoin listing vs Binance |
| #69 KuCoin API | `kucoin_connector.py` | KuCoin-before-Binance listing intel |
| #75 MarketWatch RSS | `marketwatch_connector.py` | Macro high-impact event flags |

## #60 Gate.io (silent listing intel)

- Spot tickers + Gate-only USDT pairs vs Binance `exchangeInfo`
- `exchange_listing_tracker.py` for honest first-seen timestamps
- User headline: *"First platform to surface {SYMBOL} before Binance listing"*

## #69 KuCoin (silent listing intel)

- KuCoin-only pairs vs Binance with measured lead-time when both sighted
- User headline: *"KuCoin-listed token detected — not yet on Binance"* (or hours if proven)

## #75 MarketWatch RSS (silent macro)

- RSS + macro keyword impact scoring, Dow Jones fallback
- User headline: *"AI flagged 2 macro events from MarketWatch as high-impact on your portfolio"*

## #85 Order Flow Intelligence

- Aggressive buy/sell from Binance aggTrades, bucketed by size
- Trade-side QA: kline taker validation + aggTrades cross-check
- Feeds `decision_engine_inputs.order_flow_intelligence`
- User headline example: *"Order Flow: Aggressive buyers exhausted on ETH — 72% probability of reversal within 4 hours"*

## #86 Polygon.io (silent macro)

- `POLYGON_API_KEY` / `POLYGON_IO_API_KEY`, TTL cache, circuit breaker
- SPY snapshot → macro risk context for crypto decisions
- Fallback: stale cache → Investing.com RSS
- User headline example: *"AI detected S&P 500 down 1.2% — macro risk context elevated for crypto"*

## #87 Polygonscan (silent on-chain)

- `POLYGONSCAN_API_KEY`, block + gas via Polygonscan API
- Fallback: Polygon public RPC → stale cache
- User note: *"Polygon on-chain data included in analysis"* — no API branding

## #32 Circuit Breakers (resilience pattern)

- Shared per-source breaker: `blackdark/data/circuit_breaker.py`
- Wired into `connector_cache.http_get` / `http_get_json` via `source_slug`
- Fail-closed: circuit OPEN → stale cache only, never invented live data
- See `docs/infrastructure/RESILIENCE_PATTERNS.md`

## Release engineering SOPs (#30, #31)

- Capacity evidence: `docs/sop/RELEASE_CAPACITY_EVIDENCE_SOP.md` + `scripts/release_capacity_evidence.py`
- Chaos resilience: `docs/sop/RELEASE_CHAOS_RESILIENCE_SOP.md` + `scripts/release_chaos_gate.py`
- Combined gate: `scripts/release_engineering_gate.py` (run every release)

## #21 Binance API

- Spot 24h ticker + futures funding via `binance_connector`
- Optional `BINANCE_API_KEY`, TTL cache, 429 backoff
- Fallback: stale cache → CoinGecko
- Wired into `ingestion_fetchers` (`binance_spot`, `binance_futures`)

## #23 Block Search (On-Chain Intelligence)

- `search_block()` in `address_intelligence.py`
- Etherscan proxy + public RPC fallback
- Reorg/finality disclosure on every block response
- API: `GET /api/platform/address-intelligence/block?block_number=`

## #25 + #26 Lending (merged)

- `lending_markets_connector.py` — DeFiLlama yields
- Aggregate borrow outstanding + normalized borrow APR
- Market mapping reconciliation per pool
- Feeds `decision_engine_inputs.lending_markets`

## #54 Exchange netflow

- **Fixed formula:** `netflow = inflow - outflow`
- Inflow/outflow reconciliation on every response
- **Missing ≠ zero:** `null` + `data_state: MISSING` when unavailable
- Rolling percentile + regime (`high_inflow`, `high_outflow`, `neutral`)

## #59 Futures CVD

- Binance futures klines → taker buy/sell split
- CVD cumulative delta + taker imbalance
- **Trade-side QA:** bars with invalid taker classification excluded

## #66 Historical flat archive

- Partitions: `data/archive/{dataset}/{symbol}/{interval}/{date}.jsonl`
- `manifest.json` with SHA-256 checksums per file
- `verify_manifest()` for integrity checks
- User sees: *"Backtest 2+ years"* via `backtest_coverage_years()`

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/decision/inputs?asset=` | Decision Engine feeder (#48) |
| `GET /api/platform/ingestion/data-layer/status` | Connector health |

## Wired consumers

- `decision_engine_inputs.py` — aggregates all silent metrics
- `alpha_engine.py` — risk delta + headlines
- `alpha_backtest.py` — archive years metadata
- `onchain_tracker.py` — exchange flow enrichment
- `ingestion_fetchers.py` — `theblock_rss`, `investing_com_rss`

## #97 Exchange flows

- Uses `exchange_internal_flow_filter.classify_flow()` to exclude `INTERNAL_CONFIRMED` / `INTERNAL_LIKELY`
- Economic inflow/outflow only in metrics
- Feeds `decision_engine_inputs.gather_decision_inputs()` and `onchain_tracker.build_onchain_context()`
- User headline example: *"Large SHIB inflow to Binance detected — AI adjusts risk score"*

## #95 The Block

- RSS: `https://www.theblock.co/rss.xml`
- Theme tagging (ETF, Ethereum, regulation, DeFi, macro)
- User sees: *"AI analyzed research on Ethereum ETF flows..."* — not branded news UI

## #93 Solana RPC

- Default: public mainnet endpoints with fallback chain
- Production: `SOLANA_RPC_URL` (Helius / QuickNode / Alchemy)
- User sees: *"Solana on-chain data included"*

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/decision/inputs?asset=` | Internal decision metrics (#48 feeder) |
| `GET /api/platform/ingestion/data-layer/status` | Connector health |

## Wired consumers

- `bd_platform/alpha_engine.py` — risk delta + research headlines
- `onchain_tracker.py` — token exchange flow enrichment
- `bd_platform/address_intelligence.py` — Solana balance via RPC
- `ingestion_fetchers.py` — `theblock_rss` handler
