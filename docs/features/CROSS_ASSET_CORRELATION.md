# Feature #42 — Cross-Asset Correlation

Rolling Pearson correlation between crypto and TradFi returns for Portfolio AI / Risk Dashboard.

## Scope

- **Not** Alpha Vantage quote display (#12)
- Computes **relationship** (correlation) with window + significance metadata
- Default window: 30 days (configurable 7–90)

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/correlation/matrix` | Full matrix (crypto × tradfi) |
| `GET /api/platform/correlation/view?asset=BTC` | Single-asset correlation view |

## Response fields (acceptance)

- `window_days` — rolling window size
- `significance` — strength label, sample count, `significant` flag, approximate t-stat

## Integration

- `POST /portfolio/analyze` — adds `correlation_analysis` block with weighted SPX correlation

## Data sources

- Crypto: Binance daily klines
- TradFi: Yahoo Finance daily chart (SPX, DXY, GOLD, NDX, VIX)
