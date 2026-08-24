# Silent Data Layer — Exchange Flows, The Block, Solana RPC (#97, #95, #93)

**Not user-facing features.** Internal metrics and context for Decision Engine (#48) and Alpha Engine (#13).

## Connectors

| Feature | Module | Role |
|---------|--------|------|
| #97 Token Exchange Flows | `exchange_flow_metric.py` | In/out/net flows with internal transfer filter |
| #95 The Block Articles | `theblock_connector.py` | Research RSS → AI context lines |
| #93 Solana RPC | `solana_rpc_connector.py` | Public RPC (upgrade via `SOLANA_RPC_URL`) |

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
