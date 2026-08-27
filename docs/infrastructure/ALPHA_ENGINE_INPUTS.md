# Alpha Engine — Input Sources (#13 + #14 + #15)

**Not separate user features.** Alternative.me and Arkham are **data inputs** to the unified Alpha Engine.

## Alpha Engine (#13)

`bd_platform/alpha_engine.py`

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/alpha/signal?asset=` | Unified alpha score for one asset |
| `GET /api/platform/alpha/ranking?limit=` | Ranked universe |

### Factor weights

| Factor | Weight | Source |
|--------|--------|--------|
| Momentum | 30% | CoinGecko 24h change |
| Sentiment F&G | 25% | Alternative.me (#14) |
| Entity flow | 25% | Arkham (#15) |
| Liquidity | 20% | CoinGecko price quality |

## Alternative.me (#14) — sentiment input

`blackdark/ingestion/alternative_me_connector.py`

- Fear & Greed Index → `alpha_score` (contrarian mapping)
- Cache: `ALTERNATIVE_ME_CACHE_TTL_SEC` (1–24h)
- Fallback: stale cache → neutral synthetic (50)
- Ingest: `run_alternative_me_ingest()` on bootstrap

## Arkham (#15) — entity flow input

`blackdark/ingestion/arkham_connector.py`

- Live: `ARKHAM_API_KEY` → `api.arkm.com` entity search
- Fallback: whale/institutional flow proxy from platform DB
- **No separate ML engine** — feeds `entity_flow` factor only

## Bootstrap order

1. CoinGecko primary
2. Alternative.me F&G
3. Other category sources

## Acceptance

| Source | Latency | Fallback |
|--------|---------|----------|
| Alternative.me | ≤3s | stale cache / neutral |
| Arkham | ≤3s | whale flow proxy |
| Alpha signal | ≤3s | partial inputs degrade gracefully |
