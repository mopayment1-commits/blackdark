# Liquidity Analytics — #259 (Sprint 2 Intelligence)

Analytics layer converting raw order book feeds (#256–258) into depth, spread,
and slippage metrics with block-level replay/QA. Complements #249 aggregation
and #228 DeFi AMM slippage.

Integrated into **Market Radar** as **Liquidity Analytics** — NOT standalone.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Replay/QA | Block-level recompute with actual vs replay variance |
| Depth | Per-venue + global (top 10 levels), method documented |
| Spread | Descriptive only — venue, asset, time — no buy signals |
| Slippage | Per-size ($10K, $100K, $1M) + per-venue via OB simulation |
| Integration #249 | Global Depth + Slippage Estimation = Complete Liquidity Picture |
| Integration #228 | AMM slippage for DeFi; order book N/A for DeFi assets |
| Integration #247+#130 | Total cost = slippage + gas + fees |
| Disclaimer | Non-hideable |
| Methodology v1.2 | Depth top 10, spread best bid/ask, slippage VWAP, replay block-level |
| No signal language | "Liquidity: Sufficient for $50K" — not "enter now!" |
| Update frequency | Enterprise per tick / Pro per 5s / Free per 30s |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/market-radar/liquidity-analytics` | Liquidity Analytics panel |
| `GET /api/platform/liquidity-analytics/status` | Module status |
| `GET /api/platform/market-radar/dashboard` | Includes `liquidity_analytics` block |

## Related

- `bd_platform/global_order_book.py` — aggregation layer (#249)
- `bd_platform/defi_slippage_mapper.py` — AMM slippage (#228)
- `bd_platform/gas_cost_engine.py` — gas cost (#247)
- `bd_platform/order_book_feed.py` — raw feeds (#256–258)
- `bd_platform/market_radar_dashboard.py` — Market Radar integration
