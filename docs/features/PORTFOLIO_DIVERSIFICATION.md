# Portfolio Diversification Health Score — #717 + #109 + #199 (Sprint 2)

Merged with Risk Management (#109) and PnL Drift (#199).

**UI label:** `Diversification Score: 65/100` — NOT "Entropy".

## Components

| Component | Source | Description |
|-----------|--------|-------------|
| Asset entropy | #717 (internal) | Shannon entropy across holdings |
| Correlation risk | #109 | Do assets move together? |
| Sector concentration | #717 | e.g. 60% in DeFi = risk |
| PnL / ROI | #199 | Real-time PnL ±0.1% accuracy |

## Example UI Copy

> Smart Diversification: Portfolio looks diversified (10 assets) but 70% risk in L1 → Diversification Score: 42/100

## Heatmap

Sector, chain, and market cap tier concentration.

## Acceptance

- Real-time update
- PnL accuracy ±0.1%
- ≥ 1000 assets supported
- PDF/CSV export available

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/intelligence-ledger/portfolio-health/status` | Module status |
| `GET /api/platform/intelligence-ledger/portfolio-health` | Diversification panel |
