# Feature #104 — Twelve Data Macro Enrichment

**Wave 1 — Macro Context Layer only.** Not a standalone Twelve Data product.

## Scope

Enriches Market Radar and Decision Engine (#48) with crypto-correlated tradfi:

- S&P 500 (`SPX`)
- US Dollar Index (`DXY`)
- Gold (`XAU/USD`)
- Nasdaq (`IXIC`)
- VIX (`VIX`)

## Configuration

```bash
TWELVEDATA_API_KEY=your_key
TWELVEDATA_CACHE_TTL_SEC=1200  # 15–30 min recommended
```

## Output example

> Bitcoin down 3% while DXY up 0.5% — strong negative correlation

## Fallback chain

1. Twelve Data `/quote` batch
2. Stale local cache
3. Polygon.io SPY proxy
4. Investing.com RSS macro tags

## APIs

- `GET /api/market/radar-narrative` — includes `macro_context` / `macro_enrichment`
- `GET /api/platform/decision/inputs?asset=ETH` — `twelvedata_macro` field
- `GET /api/platform/ingestion/data-layer/status` — `twelvedata` connector health
