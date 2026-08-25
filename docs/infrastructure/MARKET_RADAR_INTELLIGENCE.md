# Market Radar Intelligence — Features #155, #140, #186, #142, #139

Unified Market Radar surface — infrastructure + insights.

## Architecture

```
Market Radar
 ├── #155 Price Infrastructure (invisible) — multi-coin × multi-exchange
 ├── #140 Macro Events Calendar — impact forecasting
 ├── #186 Event Stream — categorized, deduplicated
 ├── #142 Liquidity Health Check — pre-purchase gate
 └── #139 Sentiment Intelligence — weighted multi-source NLP
```

## APIs

| Endpoint | Feature | Description |
|----------|---------|-------------|
| `GET /api/platform/market-radar/prices/matrix` | #155 | Cross-exchange price matrix |
| `GET /api/platform/market-radar/macro-events` | #140 | Macro calendar + impact |
| `GET /api/platform/market-radar/events/stream` | #186 | Industry event feed |
| `GET /api/platform/market-radar/liquidity-health` | #142 | Liquidity analysis |
| `GET /api/platform/market-radar/sentiment` | #139 | Weighted sentiment |

## Acceptance

| Feature | SLA | Accuracy |
|---------|-----|----------|
| #155 | ≤2s | Outlier-filtered |
| #140 | ≤2s | Impact forecast ≥95% heuristic |
| #186 | Dedup + evidence | Source mandatory |
| #142 | ≤2s | Slippage table $1K/$10K/$100K |
| #139 | 15min refresh | NLP ≥80% target, ≥5 sources |
