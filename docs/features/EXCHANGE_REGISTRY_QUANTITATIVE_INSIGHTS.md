# Exchange Registry & Quantitative Insights — #401

## Decision

**NOT a standalone AI engine.** Integrated into Oracle API + Data Engine + Market Radar + Intelligence Ledger.

| Component | Role |
|-----------|------|
| Exchange Registry | 100 venues — metadata + logo + API endpoints (seed only) |
| Quantitative Insights Layer | Rule-based scoring v1 over `intelligence_signals` seed |
| Data Engine | Funding Rates + Social Sentiment as existing sources |
| UI Surfaces | Market Radar + Portfolio AI **only** |

## Rejected

- Standalone "AI engine" naming
- Separate signals database/API
- Sharpe ≥1.5 / Win Rate ≥55% / Max DD ≤15% (replaced)
- ML in v1 (deferred 90 days)

## Acceptance Thresholds (v1)

| Metric | Threshold |
|--------|-----------|
| Sharpe | ≥ 0.8 |
| Win Rate | ≥ 52% |
| Max Drawdown | ≤ 20% |
| Latency | ≤ 5 minutes |
| Backtest | ≥ 2 years |
| Walk-Forward | 6 months |
| Fee Deduction | Mandatory (exchange + slippage + network) |

## Output Labels (mandatory)

- Quantitative Insight
- Risk-Adjusted Signal
- Data-Driven Alert

**Banned:** "AI predicts", "guaranteed profit", "buy now", "exploit"

## API

```
GET /api/platform/intelligence-ledger/data-layer/exchange-registry
GET /api/platform/intelligence-ledger/data-layer/exchange-registry/lookup?exchange_id=binance
GET /api/platform/intelligence-ledger/market-radar/quantitative-insights?asset=BTC
GET /api/platform/intelligence-ledger/portfolio-ai/quantitative-insights?asset=BTC
GET /api/platform/intelligence-ledger/intelligence-layer/quantitative-insights
```

## 100 Exchanges

CEX (1–50), DEX (51–70), Perp DEX (71–80), Regional (81–100) — see `data/exchange_registry_seed.json`.
