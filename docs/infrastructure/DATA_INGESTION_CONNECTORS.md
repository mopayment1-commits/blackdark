# Silent Data Connectors — DeBank, DexScreener, Etherscan (#46, #49, #50)

**Not user-facing features.** These are Sprint 2 Data Ingestion Layer sources integrated silently. Users see portfolio depth, liquidity drain signals, and whale flow headlines — not vendor branding.

## Connectors

| Feature | Module | Role |
|---------|--------|------|
| #46 DeBank | `blackdark/ingestion/debank_connector.py` | Multi-chain wallet/portfolio balance |
| #49 DexScreener | `blackdark/ingestion/dexscreener_connector.py` | DEX pair liquidity + drain heuristics |
| #50 Etherscan | `blackdark/ingestion/etherscan_connector.py` | On-chain balance, txs, whale sell-flow signal |

Shared cache/rate-limit utilities: `blackdark/ingestion/connector_cache.py`

## Capabilities

| Capability | Implementation |
|------------|----------------|
| Auth | `DEBANK_API_KEY`, `ETHERSCAN_API_KEY` (DexScreener is public) |
| Cache | `*_CACHE_TTL_SEC` env vars (default 3600s, max 86400s) |
| Rate limits | HTTP 429 → backoff + stale cache serve |
| Timeout | 3s per request (`sla_met` on responses) |
| Fallback | DeBank → Zerion → Tracely; DexScreener → GeckoTerminal; Etherscan → stale cache |

## Fallback chains

```
DeBank API → stale cache → Zerion → Tracely
DexScreener API → stale cache → GeckoTerminal
Etherscan API → stale cache
```

## Wired consumers

- `bd_platform/free_integrations.wallet_balance()` — DeBank connector first
- `bd_platform/onchain_hub.dexscreener_pairs()` — DexScreener connector
- `bd_platform/address_intelligence.search_address()` — Etherscan whale flow signal (ETH)
- `ingestion_fetchers.py` — `debank`, `dexscreener`, `etherscan` handlers

## Infrastructure API

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/ingestion/connectors/status` | Combined connector health |

## Acceptance

| Criterion | Target |
|-----------|--------|
| API latency | ≤3s (`sla_met`) |
| Cache | 1–24 hours |
| Rate limit | 429 backoff + stale serve |
| Fallback | Multi-layer per connector |
| Uptime | Stale cache + alternate sources |
