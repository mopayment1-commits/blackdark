# Market Intelligence — Features #2–#4

## Features

| # | Feature | Module | API | UI Tab |
|---|---------|--------|-----|--------|
| 2 | MVRV Z-Score Dynamic Realignment | `bd_platform/mvrv_realignment.py` | `GET /api/platform/onchain/mvrv-realignment` | MVRV Realignment |
| 3 | Multi-Factor Alpha Ranking | `bd_platform/alpha_factor_ranking.py` | `GET /api/platform/alpha/ranking` | Alpha Ranking |
| 4 | Squeeze Trigger Coordinates | `bd_platform/squeeze_trigger_engine.py` | `GET /api/platform/squeeze/triggers` | Squeeze Triggers |

## UI

`/market-intelligence` — unified dark-theme hub with three tabs.

## Data sources

- **MVRV:** Binance daily klines (SMA200 realized proxy)
- **Alpha:** CoinGecko markets (fallback Binance)
- **Squeeze:** Binance Futures public (funding, OI, L/S ratio)

## Tests

```bash
pytest tests/test_market_intelligence.py -v
```

## CAP bindings

- MVRV: CAP646 IDs 40, 195
- Alpha: CAP646 ID 127
- Squeeze: CAP978 IDs 936, 942, 951, 974

## Limitations

- MVRV uses price-based proxy (not Glassnode on-chain series)
- Squeeze coordinates are leverage-tier estimates, not order-book liquidation heatmaps
- Alpha model uses free-tier factors only
