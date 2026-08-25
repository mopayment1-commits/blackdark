# Positioning Intelligence — #221 (Sprint 2, merged into Sentiment Panel)

Top Trader Positioning — **NOT** copy-trade recommendations.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Provider semantics visible | `Source: Binance Top Traders \| Definition: Top 10% by volume \| Updated: hourly` |
| Not copy-trade | `Top Trader Long Ratio: X%` — never "Copy Trade: Long" |
| Disclaimer | Mandatory, non-hideable |
| Divergence alerts | `Top Traders: 70% Long \| Retail: 30% Long \| Divergence: High` |
| Cross-venue | `Aggregated across 5 exchanges \| Weighted by volume` |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/market-radar/sentiment/positioning/status` | Module status |
| `GET /api/platform/market-radar/sentiment/positioning` | Positioning panel |
| `GET /api/platform/market-radar/sentiment/positioning/divergence` | Divergence alert |
| `GET /api/platform/market-radar/sentiment` | Sentiment + positioning integrated |

## Related

- `bd_platform/sentiment_intelligence.py` — parent Sentiment Panel (#139)
