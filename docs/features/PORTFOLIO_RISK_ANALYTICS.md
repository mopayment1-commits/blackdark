# Portfolio Risk Analytics Suite — #723 + #724 + #746 (merged)

**NOT standalone** — integrated into Portfolio AI → Risk Scenario Engine (Sprint 2).

| Feature | Layer | Surface |
|---------|-------|---------|
| #723 | Input | Correlation Matrix |
| #724 | Context | Cross-Asset Return Breadth |
| #746 | Simulation | Risk Scenario Simulator |

> "Monte Carlo" is internal only — UI shows **Risk Scenario Simulator**.

## #746 — Risk Scenario Simulator

| Rule | Implementation |
|------|----------------|
| Modeling only | Statistical simulation of potential outcomes — NOT prediction |
| Output | Probability distribution + VaR (95%, 99%) + confidence intervals |
| Performance | ≤2s for 10,000 iterations |
| Historical backtest | Simulation accuracy vs historical VaR breach rate |
| Tier | Pro+ only (`risk_scenario_simulator` feature gate) |
| Disclaimer | Mandatory, non-hideable |

## APIs

| Endpoint | Tier | Description |
|----------|------|-------------|
| `GET /api/platform/portfolio/risk-analytics/status` | All | Module status |
| `GET /api/platform/portfolio/risk-analytics/correlation` | All | #723 correlation matrix |
| `GET /api/platform/portfolio/risk-analytics/breadth` | All | #724 return breadth |
| `POST /api/platform/portfolio/risk-analytics/simulate` | Pro+ | #746 risk scenario simulation |
| `POST /api/platform/portfolio/risk-analytics` | Pro+ | Unified dashboard |

## Related

- `dashboard._analyze_portfolio_holdings` — Portfolio AI base layer
- `bd_platform/onchain_advanced._monte_carlo` — internal simulation engine (not exposed in UI)
